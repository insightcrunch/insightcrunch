---
layout: post
title: "Fix Azure VM Boot Failure and No-Boot Issues"
page_title: "Fix Azure VM Boot Failure: Diagnose No-Boot with Boot Diagnostics, the Serial Console, and the Rescue VM Repair Workflow"
date: 2022-05-23
categories: ["Technology"]
tags: ["Azure", "Virtual Machines", "Boot Diagnostics", "Serial Console", "Troubleshooting"]
excerpt: "An Azure VM boot failure is almost always a guest OS fault you can read from boot diagnostics and then repair with a rescue VM, not a reason to redeploy."
image: "/assets/images/blog/blog-44.webp"
reading_time: 63
author: "thomas-reid"
last_updated: 2022-05-23
lang: en
---
An Azure VM boot failure is one of the few problems on the platform that feels genuinely frightening, because the machine has gone dark and the usual tools have nothing to connect to. There is no SSH session, no RDP window, no agent heartbeat, and no obvious place to look. The instinct that follows is almost always wrong: redeploy the machine, or restore last night's backup, and accept the lost state. That instinct throws away the work since the last snapshot to solve a problem that the serial console plus a rescue VM usually fixes in a few minutes, because the cause is sitting in the guest operating system rather than anywhere you cannot reach.

This guide treats a dead virtual machine the way a senior engineer does: as a five-symptom diagnosis with a confirming view, not a guessing game. You will learn to read the boot diagnostics screenshot and the serial log, identify which of the distinct no-boot causes is yours, and recover the instance with the repair commands rather than rebuilding it. Everything here assumes the instance reached the Azure fabric and was assigned to a host, then failed somewhere between power-on and a usable login. That is the territory where the guest, not the platform, owns the problem.

![Diagnosing an Azure VM boot failure with boot diagnostics and the serial console - Insight Crunch](/assets/images/blog/blog-44.webp)

## What an Azure VM boot failure actually is

A boot failure is not a single condition. It is the visible result of any one of several guest faults that stop the operating system from reaching a state where it can serve a login or a network listener. The fabric did its part: it allocated the machine, attached the managed OS disk, wired the network interface, and powered the instance on. From that moment forward, the boot is the guest's responsibility, and the failure lives inside the guest's filesystem, bootloader, kernel, or service manager.

The single most important reframing is this. A no-boot is almost never a host problem and almost never a quota or capacity problem. Those produce different signals, an allocation error or a SkuNotAvailable message at deployment, not a machine that powers on and then hangs. When a machine that booted yesterday refuses to boot today, something changed inside it: a package update, a configuration edit, a disk that filled, a kernel that no longer matches its initramfs. The mental model to hold is that the platform handed you a running engine and the engine seized after a change you or an automated process made. The repair is mechanical and reachable, and the path to it starts with looking rather than acting.

If you want the underlying compute and disk model that this article repeatedly leans on, the foundations live in the [complete engineering guide to Azure Virtual Machines](/2022/01/03/azure-virtual-machines-complete-guide/), which walks through how the OS disk, the data disks, the network interface, and the host fit together. The diagnosis below assumes that model and builds the recovery procedure on top of it.

## Confirming the instance reached the host first

Before treating a failure as a no-boot, rule out the two conditions that masquerade as one but live entirely outside the guest: an allocation failure and a deployment that never produced a running instance. These show different signals and need different fixes, and spending an hour reading boot diagnostics for a machine that never started is wasted effort. An allocation failure appears at start or deployment time as an explicit error, an allocation message or a SkuNotAvailable response, which means the fabric could not place the requested size in the chosen region or zone at that moment. That is a capacity or a quota condition, not a guest fault, and no amount of disk repair touches it. A deployment that failed before producing an instance similarly shows a provisioning error in the activity log rather than a powered-on instance that hangs.

The quick discrimination is to check the instance's power and provisioning state. An instance that is running yet unreachable, or running yet hanging at the console, is a true no-boot and belongs to this guide. An instance stuck in a starting or failed state with an allocation or quota message belongs to the capacity and quota class of problems instead, where the fix is to request more quota, choose a different size or zone, or wait for capacity:

```bash
# Read the power state and the provisioning state in one view
az vm get-instance-view \
  --resource-group myResourceGroup \
  --name myVm \
  --query "{power: instanceView.statuses[?starts_with(code, 'PowerState')].displayStatus | [0], provisioning: provisioningState}" \
  -o table
```

If that view shows the instance running, the failure is inside the guest and the boot diagnostics read is the next step. If it shows a failed allocation, you are in a different territory entirely, and treating it as a no-boot would only delay the real fix. Making this check first is cheap insurance against diagnosing the wrong layer.

## Reading the only window you have: boot diagnostics and the serial console

When a machine never reaches the network, you have exactly two ways to see inside it, and both are designed for precisely this situation. Boot diagnostics captures a screenshot of the console and the serial log to a storage location, so you can see the kernel panic, the GRUB prompt, the systemd emergency message, or the Windows stop code that the machine is showing to a monitor you cannot physically attach. The serial console gives you a live, interactive connection to that same console channel, so you can interrupt the bootloader, drop into single-user mode, edit a file, and continue the boot, all without any network path to the guest.

Neither tool works unless boot diagnostics is enabled, and that is the first thing to confirm. Managed boot diagnostics, which writes to an Azure-managed location rather than a storage account you provision, is the current default for many images, but you should verify it is on for the affected machine rather than assume it. You can enable it from the command line and then pull the boot log directly:

```bash
# Enable managed boot diagnostics (no storage account argument = managed)
az vm boot-diagnostics enable \
  --resource-group myResourceGroup \
  --name myVm

# Retrieve the serial boot log to your terminal
az vm boot-diagnostics get-boot-log \
  --resource-group myResourceGroup \
  --name myVm
```

Boot diagnostics captures two distinct artifacts, and knowing the difference helps you read them. The screenshot is a single image of whatever the console is displaying at the moment you look, which is ideal for a state that sits still, a kernel panic frozen mid-trace, a GRUB prompt, a Windows stop code, or a stalled servicing screen. The serial log is the accumulated text the console emitted during the boot, which is ideal for following a sequence, watching the systemd jobs run and seeing exactly which one failed and what it said. For a hang, the screenshot tells you where it stopped; for a failure that scrolled past, the serial log tells you what happened on the way. You typically read both, starting with the screenshot for the headline and turning to the log for the detail.

There are two ways the diagnostics data can be stored. Managed boot diagnostics keeps the screenshot and log in an Azure-managed location, which is the simpler choice because there is no storage account to provision, secure, or pay attention to, and it is the current default for many images. Custom boot diagnostics writes to a storage account you own, which some organizations prefer for retention or compliance reasons but which adds the responsibility of keeping that account reachable and correctly configured; a boot diagnostics setup that points at a deleted or firewalled storage account quietly stops capturing, which is the worst time to discover a gap. Whichever model you use, verify it is functioning on instances that matter before an incident, because the diagnostics you cannot read are no help at all.

In the portal, the same signals live under the machine's Help section: the Boot diagnostics blade shows the screenshot and the serial log, and the Serial console blade gives you the live channel. For a Linux guest, the serial console lands you at a getty login or, if you interrupt early, at the GRUB menu or a single-user shell. For a Windows guest, it lands you at the Special Administration Console, the text-mode channel from which you can launch a command shell. The serial console requires boot diagnostics to be enabled and the image to support the serial channel, which the standard Azure Marketplace images do. Custom images built without the serial console packages may not expose it, which is itself a reason to bake those packages into any image you intend to operate seriously.

### How do I see why my Azure VM will not boot?

Enable boot diagnostics, then open the Boot diagnostics blade to read the screenshot and serial log. The screenshot shows the exact console state: a kernel panic, a GRUB prompt, a systemd emergency shell, an fstab mount error, or a Windows stop code. That single image names the cause before you touch the disk.

The discipline this article advances has a name worth remembering. The serial-console-first rule for a dead machine says that the boot diagnostics screenshot and serial log identify the cause before any disk surgery, so the recovery sequence is always the same: read the screen, attach the OS disk to a rescue instance, fix the specific fault, then reattach the volume and start the original instance. Engineers who skip the first step and jump straight to a rebuild are not faster; they are slower, because they pay the full cost of lost state to avoid a five-minute read of a log that was already telling them the answer.

### How do I tell a kernel panic from an initramfs shell or emergency mode?

A kernel panic prints a stack trace and freezes, usually with text about being unable to mount root. An initramfs shell is an interactive prompt that appears before the real root is mounted, often naming a missing volume. Emergency mode is a systemd shell that appears after root mounted but a later job failed.

Those three Linux failure consoles look similar at a glance, yet each points at a different layer, and learning to tell them apart saves the wrong fix. A panic means the kernel itself could not proceed, almost always because it could not find or mount the root filesystem, so the trace ends in something like a message about an unmounted root or a missing init. The handoff between the bootloader and the kernel already happened, which rules out a bootloader problem and points at the initramfs, the root device, or the kernel image. An initramfs prompt, by contrast, is a tiny shell baked into the early boot image that is supposed to assemble and mount the real root before handing off; when it cannot, it drops you to a prompt that typically reads `(initramfs)` and lets you run a small set of commands to investigate, which is exactly where you scan and activate a logical volume that failed to appear. Emergency mode is later still: the real root mounted, systemd took over, and a unit, frequently a mount declared in `/etc/fstab`, failed in a way that systemd treats as fatal, so it stops and offers you a maintenance shell after asking for the root password.

Reading which of the three you are in tells you immediately whether to look at the initramfs and kernel, at the volume layout, or at the service and mount configuration, and it tells you whether a live serial console fix is even possible. A panic gives you nothing interactive, so you reboot the previous kernel or move to a rescue machine. An initramfs prompt is interactive but limited, good for activating a volume so the boot can continue once. Emergency mode gives you a near-full shell once you remount root read-write, which is where the in-place fstab fix below applies. The Windows equivalents are simpler to read because each is a labeled screen: a stop code on a blue background is the panic equivalent, a recovery environment is the maintenance equivalent, and a stalled servicing screen is its own category.

## The VM no-boot triage table

Before walking each cause individually, here is the artifact to bookmark. The InsightCrunch VM no-boot triage table maps each boot diagnostics symptom to its root cause and to the rescue sequence that fixes it, so the moment you read the screenshot you already know which branch you are on. The screenshot or serial log is the input; the rightmost column is the action.

| Boot diagnostics symptom | What you see on the console | Most likely root cause | Recovery path |
|---|---|---|---|
| Emergency mode, "Failed to mount", waiting for a device | systemd drops to an emergency shell or hangs on a device job | A bad `/etc/fstab` entry for a data disk with no `nofail` | Comment out or fix the line, add `nofail`, via serial console single-user or a rescue VM |
| Disk full messages, "No space left on device", services failing to start | Logs show write failures across services | OS disk filled to 100 percent | Attach to a rescue VM, reclaim space or grow the disk and filesystem |
| Kernel panic, "VFS: Unable to mount root fs", "No init found" | Panic immediately after the bootloader hands off | A kernel or initramfs update that produced a non-bootable image | Boot the previous kernel from GRUB, or chroot from a rescue VM and rebuild the initramfs and GRUB config |
| `grub rescue>` or `grub>` prompt | The bootloader cannot find its own configuration or the kernel | A broken or misconfigured bootloader | Chroot from a rescue VM and reinstall GRUB, regenerate the config |
| "Volume group not found", drops to an initramfs shell | The root logical volume is not activated | An LVM root volume that fails to mount | Activate the volume group from the rescue VM, repair the LVM metadata or fstab reference |
| systemd "Failed to start" cascade, security or permission errors | Core services refuse to start | Permissions or ownership changed on a system path | Restore correct ownership and mode on the affected path from a rescue VM |
| INACCESSIBLE_BOOT_DEVICE stop code | Windows blue screen on boot | A storage controller or boot-critical driver change, often after an update | Revert pending actions and repair the boot configuration from a rescue VM |
| "Getting Windows ready", "Undoing changes", a recovery loop | Windows stalls or loops on update screens | A failed or half-applied Windows update | Revert pending actions offline from a rescue VM |
| cloud-init or extension errors after a normal boot | The OS comes up but provisioning never completes | An OS provisioning or extension timeout, not a true no-boot | Inspect the agent and cloud-init logs; this is a separate class of problem |

The namable claim that organizes this entire table is the rule stated above: read the screen first. Every row begins with a symptom you can only see through boot diagnostics, and every recovery path begins by attaching the disk to a rescue machine rather than rebuilding the original. The table is the diagnosis; the sections below are the procedure for each row.

## The distinct root causes of an Azure VM boot failure

It helps to hold the full set in mind before drilling into any one. A Linux server that will not boot is almost always suffering from a filesystem or mount problem expressed through `/etc/fstab`, a disk that has filled completely, a kernel or initramfs that no longer agrees with itself after an update, a bootloader that cannot find or load its configuration, a logical volume that fails to activate, or a permissions change on a path that systemd depends on. A Windows server that will not boot is usually stuck on a boot-critical driver that changed, a stop code such as INACCESSIBLE_BOOT_DEVICE, or a half-applied update that left the machine looping through "Getting Windows ready" and "Undoing changes." A separate and often-confused class is the machine that boots fine but never finishes provisioning, where cloud-init or the guest agent times out; that is a provisioning fault, not a no-boot, and it shows the operating system reaching a login while the deployment still reports failure.

Each of these has a console signature you can read and a fix you can apply through the same recovery scaffold. What follows takes them one at a time, with the confirming signal and the tested command for each.

## A bad /etc/fstab entry that blocks boot

This is the most common self-inflicted no-boot on Linux, and it is entirely preventable. The scenario is familiar: you attach a data disk, format it, and add a mount line to `/etc/fstab` so it mounts automatically on reboot. The machine works fine until the next restart, at which point it hangs or drops into an emergency shell. The reason is that systemd, by default, treats every fstab entry as a hard requirement for boot. If the device named in the entry is not present, or the filesystem cannot be mounted, the mount job fails, and because the local filesystems target is a dependency of the rest of the boot, the whole sequence stalls. A device that detaches, a UUID that changes, or a simple typo in the entry is enough to take the machine down on the next reboot, days or weeks after the change was made.

### Can a bad fstab entry stop an Azure VM from booting?

Yes, and it is the single most common Linux no-boot. systemd treats each fstab line as a required mount, so a missing device, a wrong UUID, or a typo fails the mount job and stalls boot in an emergency shell. Adding the `nofail` option makes the mount optional and prevents the hang.

The console signature is unmistakable once you know it. The serial log shows a job timing out while waiting for a device, often the literal text about waiting for a device file under `/dev/disk/by-uuid`, followed by a drop into emergency mode that asks for the root password to continue. If you have the root credentials, the live fix from the serial console is fast. You log in at the emergency prompt, remount the root filesystem read-write, edit the offending line out of `/etc/fstab`, and continue:

```bash
# At the emergency shell on the serial console
mount -o remount,rw /
nano /etc/fstab          # comment out or correct the bad data-disk line
# add nofail to any optional data disk, e.g.:
# UUID=xxxx  /data  ext4  defaults,nofail  0  2
systemctl daemon-reload
mount -a                 # confirm everything in fstab mounts cleanly now
reboot
```

When you reach a shell but are not certain which line is at fault, systemd will tell you directly. Running `systemctl --failed` lists the units that did not start, and a failed mount appears as a `.mount` unit named after its mount point, so a failed mount at `/data` shows as `data.mount`. Following that with `journalctl -xb` shows the boot journal with the explanation lines that systemd appends, including the dependency that the failed mount blocked. Reading those two outputs turns a vague hang into a named line in `/etc/fstab`. The deeper cause is usually one of three things: the entry references a device by a path that changed, such as a kernel device name like `/dev/sdc1` that the system reassigned on the next boot; the UUID in the entry no longer matches the filesystem because the disk was reformatted; or the device is simply absent because the data disk was detached. The durable correction is to reference the filesystem by its UUID, which is stable across reattachment and reordering, and to add the options that make a missing mount survivable.

The safest data-disk entry combines `nofail` with a bounded device timeout so the boot neither hangs waiting for an absent device nor treats its absence as fatal. An entry such as `UUID=<uuid> /data ext4 defaults,nofail,x-systemd.device-timeout=10s 0 2` mounts the disk when present, waits only a short interval for it, and continues the boot cleanly when it is missing, logging the absence rather than stalling. The pair of options is the difference between a machine that comes up degraded and recoverable and one that locks you out entirely. Confirm the entry with `mount -a`, which attempts every fstab mount and reports any failure immediately, before you trust a reboot to validate it. Validating the entry while the system is running is far cheaper than discovering the mistake on the next restart, which is precisely when the original change has faded from memory.

If you do not have working credentials at the emergency prompt, or the machine never offers one, the offline path through a rescue machine is the answer, and it is covered in full below. The prevention is a one-word habit: every non-root, non-essential mount in `/etc/fstab` should carry the `nofail` option, and ideally `nofail` together with a sensible mount timeout, so that a missing data disk degrades to a missing mount rather than a dead machine. A machine that boots without its data disk and logs the missing mount is recoverable over SSH; a machine that hangs in an emergency shell is not, until you bring the heavier tools.

## A full OS disk that hangs the system

A disk that fills to one hundred percent does not announce itself politely. The operating system needs to write to the OS disk constantly during boot, for journals, for temporary files, for lock files, for the very logs that would tell you what is wrong. When there is no space left, those writes fail, services that depend on them fail in turn, and the machine either hangs partway through boot or comes up in a broken half-state where almost nothing works. The serial log shows a cascade of "No space left on device" errors and services that fail to start, and the pattern is broad rather than focused on a single component, which is the tell that distinguishes it from a single service crashing.

### Does a full OS disk cause an Azure VM boot failure?

Yes. When the OS disk reaches one hundred percent, the system cannot write the journals, lock files, and temporary files that boot requires, so services fail across the board and the machine hangs or comes up broken. The serial log shows widespread "No space left on device" errors rather than one failing service.

Confirming it is straightforward once you have any shell, including the serial console: `df -h` shows the root filesystem at or near one hundred percent. The fix has two flavors depending on whether you can clear space quickly or need more of it. If something filled the disk that you can safely remove, the fastest recovery is to reclaim space directly, which often means rotating or truncating runaway logs and clearing the systemd journal:

```bash
# From a shell on the affected machine (serial console) or via a rescue VM mount
df -h /                          # confirm the root volume is full
journalctl --disk-usage         # see how much the journal is consuming
journalctl --vacuum-size=200M   # cap the journal and reclaim space
du -xh / | sort -rh | head -20  # find the largest space consumers
```

If the disk is genuinely too small for the workload, the durable fix is to grow the OS disk and then extend the partition and filesystem to use the new space. Growing the managed disk is an Azure operation, and extending the filesystem is a guest operation, and the two must both happen for the new capacity to be usable. The OS disk can be resized while the machine is deallocated, after which the guest must grow the partition and the filesystem. Treat the specific maximum OS disk sizes and the resize constraints as values to confirm against the current official limits, because Azure has raised disk size ceilings repeatedly.

The guest side of the growth is two operations that engineers frequently forget to complete, leaving the larger disk doing nothing. After the managed OS disk is enlarged and the instance starts, the partition table still describes the old, smaller partition, and the filesystem still describes the old partition size, so you grow the partition first and then the filesystem on top of it. The partition grow uses `growpart`, and the filesystem grow uses the tool matching the filesystem type, `resize2fs` for the ext family and `xfs_growfs` for XFS, which is the default root filesystem on several current images:

```bash
# Identify the disk, partition, and filesystem type
lsblk
df -Th /

# Grow the root partition (example: device sda, partition 1)
sudo growpart /dev/sda 1

# Grow an ext4 filesystem to fill the partition
sudo resize2fs /dev/sda1

# Or, for an XFS root filesystem, grow by mount point
sudo xfs_growfs /
```

One full-disk variant deserves a separate mention because it confuses people who see free space yet still cannot write: inode exhaustion. A filesystem can have plenty of free bytes and still refuse new files because it has run out of inodes, the structures that track files, which happens when a directory accumulates an enormous number of tiny files. The byte count from `df -h` looks healthy, while `df -i` shows inode usage at one hundred percent, and the symptom is the same write failure and boot hang. The fix is to find and remove the directory full of small files rather than to grow the disk, because adding space does not add inodes to an already-created filesystem. Checking `df -i` alongside `df -h` whenever a disk-full symptom does not match the apparent free space is the habit that catches this quickly.

The prevention is monitoring: an alert on OS disk free space that fires well before the disk fills turns a no-boot into a ticket you handle during business hours.

## A kernel or initramfs update that left the VM unbootable

This failure mode is the one that catches careful engineers, because it follows a routine patch and surfaces only on the next reboot, sometimes long after the update ran. A package manager installs a new kernel, regenerates the initramfs, and updates the bootloader configuration so the new kernel becomes the default. If any step in that chain went wrong, if the initramfs was built without a driver the root filesystem needs, if the regeneration failed silently, or if the bootloader points at a kernel that is not actually present, the next boot panics. The console shows a kernel panic with a message about being unable to mount the root filesystem, or about no init being found, immediately after the bootloader hands control to the kernel.

The first thing to try is the cheapest. Most Linux distributions keep the previous kernel installed and listed in the GRUB menu, so from the serial console you can interrupt the boot, open the advanced options or the previous-versions submenu, and boot the older kernel that was working before the update. If the machine comes up on the old kernel, you have confirmed the diagnosis and bought yourself a working system from which to repair or remove the broken kernel without any disk surgery at all.

When booting the previous kernel is not possible, the repair is to chroot into the root filesystem from a rescue machine and rebuild the initramfs and the bootloader configuration so they agree with the kernel that is actually installed. The exact tooling differs by distribution family, with `dracut` on the Red Hat family and `update-initramfs` on the Debian and Ubuntu family, and the GRUB regeneration command differing similarly. The principle is constant: regenerate the initramfs for the target kernel, regenerate the GRUB configuration, and confirm the bootloader entry points at a kernel and initramfs that both exist. The prevention here is to stage kernel updates rather than applying them blindly to a fleet, and to reboot a canary machine after a kernel update before the same update reaches anything that matters, so that a bad initramfs is discovered on a disposable instance rather than a production one.

Once you have booted the previous kernel and confirmed it works, resist the urge to immediately delete the broken kernel, because the boot menu may still default to it and you want a deliberate, tested transition. The cleaner path is to make the working kernel the default, regenerate the boot configuration, and reboot to prove the default now lands on the good kernel before removing the bad one. The mechanism varies: some distributions track a saved default entry that you set explicitly, others select by the order of installed kernels. After the working kernel is confirmed as the default and survives a reboot on its own, you remove the broken kernel package through the package manager, which also regenerates the boot configuration so the menu no longer offers the failed entry. Removing a kernel package rather than hand-deleting files is important, because the package manager updates the bootloader and the initramfs bookkeeping in step, whereas deleting files by hand leaves the menu pointing at images that no longer exist, which recreates the very problem you just escaped.

## A broken bootloader and the GRUB rescue prompt

When the bootloader itself is damaged, the machine never even reaches the kernel. Instead of a panic, you get a `grub rescue>` or a bare `grub>` prompt on the console, which means GRUB loaded far enough to start but cannot find its own configuration, its modules, or the kernel it is supposed to load. This happens after a partition change, a disk that was resized in a way that confused the bootloader, an interrupted GRUB update, or a filesystem repair that moved blocks GRUB had hardcoded. The signature is the prompt itself, which is GRUB telling you it is alive but lost.

You can sometimes hand-walk GRUB to a working kernel from the rescue prompt, by setting the root and prefix variables and loading the normal module, but that is a fragile manual procedure that does not survive the next reboot. The durable fix is to chroot from a rescue machine and reinstall GRUB to the disk, then regenerate its configuration so the next boot finds everything where it expects. The reinstall writes a correct bootloader to the boot sector or the EFI partition, and the configuration regeneration rebuilds the menu from the kernels actually present. Because this depends on the partition layout, the boot mode, and whether the machine uses BIOS or UEFI boot, the precise commands vary, and you should confirm the boot mode of the affected machine before reinstalling, since installing a BIOS bootloader on a UEFI machine or the reverse will not help. The recovery scaffold below makes the chroot mechanical.

## An LVM root volume that fails to mount

Machines whose root filesystem sits on a logical volume add one more place for a no-boot to hide. If the volume group is not activated during the initramfs phase, because of a metadata problem, a missing physical volume, or an initramfs that was rebuilt without the LVM tools, the boot drops into an initramfs shell with a message that the volume group or the logical volume cannot be found. The machine is not damaged in any deep sense; the boot simply could not assemble the volume that holds root.

From the initramfs shell on the serial console, you can often scan for and activate the volume group manually, which confirms the diagnosis and lets the boot continue once. To make it permanent, the initramfs must include the LVM tooling and the boot must activate the volume group automatically, which means rebuilding the initramfs from a chroot on a rescue machine, the same operation used for the kernel repair above. The diagnostic commands to run from the initramfs shell are the LVM scan and activate pair, and the confirming check is that the root logical volume appears and can be mounted:

```bash
# From the initramfs shell on the serial console
lvm vgscan                 # discover volume groups
lvm vgchange -ay           # activate all volume groups
ls /dev/mapper/            # confirm the root LV is now present
exit                       # let the boot continue with the volume activated
```

If the volume group is genuinely missing a physical volume, that is a deeper data problem and the rescue-machine path lets you inspect the LVM metadata offline before deciding whether to repair or restore. For most cases the cause is a benign activation failure that the chroot rebuild resolves.

When the metadata itself is damaged rather than merely unactivated, LVM keeps its own safety net that many engineers never use. Every metadata change is archived under `/etc/lvm/archive`, and the `vgcfgrestore` command can roll a volume group's metadata back to a known-good archived version, which recovers from a botched resize or a partial operation that left the group inconsistent. You inspect the available archives with `vgcfgrestore --list <vgname>` and restore a specific one when the current metadata is the problem. Thin-provisioned volumes add a wrinkle worth flagging: a thin pool that has run out of physical space behaves like a full disk for everything stored in it, and the boot can fail because the root logical volume cannot write even though the volume group reports free extents, since the thin pool, not the group, is exhausted. The tell is a thin pool at full data or metadata usage in the LVM reporting, and the fix is to extend the pool rather than the volume. Treat any in-place metadata operation as risky and snapshot the disk first, because LVM repair on a damaged group can make matters worse if the wrong archive is chosen.

## Permissions or ownership on a system path that breaks systemd

A surprisingly common self-inflicted no-boot comes from a well-meant `chmod` or `chown` run too broadly, recursively, against a path the operating system depends on. systemd and the services it starts are particular about the ownership and mode of certain directories and files, and if a recursive permission change swept through a system path, the boot can fail with a cascade of services refusing to start, often citing permission or security context errors. The console shows core services failing in a pattern that points back to a directory whose ownership or mode is wrong rather than to any single application.

The fix is to restore correct ownership and mode on the affected path, which is best done offline from a rescue machine where you can compare against a known-good reference and set the paths back to what the distribution expects. There is no universal one-line repair, because the correct ownership depends on which path was damaged, but the principle is to identify the path from the console errors, mount the disk on a rescue machine, and restore the expected ownership and mode. The prevention is discipline around recursive permission changes: never run a recursive `chown` or `chmod` against a path near the system root, and when you must change permissions broadly, scope the change tightly and test it on a disposable machine first.

Restoring the correct ownership and mode offline is easier when you have a reference to compare against, and the cheapest reference is a healthy instance built from the same image. From a working instance of the same distribution, you can read the expected ownership and mode of the damaged path and apply exactly those values to the mounted copy on the rescue machine, which removes the guesswork of remembering what a given system directory should be. Some package managers can also verify and reset the ownership and permissions of files they installed against their own database, which is the most reliable correction when a broad change swept through package-managed paths, because it restores precisely what the packages declared. The principle either way is to restore the specific expected values rather than to open permissions broadly in frustration, since a second overly broad change compounds the original mistake and can introduce a security exposure on top of the boot failure.

## Windows no-boot: INACCESSIBLE_BOOT_DEVICE and the update loop

Windows machines fail to boot in their own characteristic ways, and two dominate the support queue. The first is the INACCESSIBLE_BOOT_DEVICE stop code, a blue screen that appears when Windows cannot reach the volume that holds the operating system early in boot. On a cloud instance this is almost never a physical storage problem; it is a boot-critical storage driver that changed, a controller configuration that no longer matches, or an update that altered the driver stack so the boot volume is no longer reachable with the drivers loaded at that stage. The second is the recovery loop, where the machine sits on "Getting Windows ready" or "Undoing changes" indefinitely, or cycles through them, because an update was half-applied and the guest cannot move forward or cleanly back on its own.

Both are repaired the same way, offline, from a rescue machine, by reverting the pending servicing actions so the half-applied change is undone, and by repairing the boot configuration so the machine knows where to find its system. The servicing image tools let you point at the offline Windows installation and revert pending actions, which clears a stuck update, and the boot configuration tools repair the entries that tell the firmware where the system lives. Because the exact command syntax targets an offline image path and depends on the Windows version, confirm the current servicing and boot-repair command syntax against the official documentation before running it, and always work against the copy of the volume on the rescue instance so that a mistake costs you nothing. The pattern is the same as the Linux cases: read the stop code or the stuck screen from boot diagnostics, attach the disk to a rescue machine, revert and repair, then reattach.

Working against the offline Windows volume mounted on the rescue machine, the servicing tooling points at the offline installation directory rather than the running system, which is the detail that makes these commands safe and offline. Reverting a stuck update uses the deployment image servicing tool aimed at the offline image, and repairing the boot records uses the boot configuration tools aimed at the offline system volume. The commands below are illustrative of the approach rather than a guaranteed transcription, because the exact switches and the offline-image syntax depend on the Windows version; confirm them against the current official documentation before running, and operate only on the disk copy:

```text
:: Assume the broken Windows volume is mounted as F: on the rescue VM

:: Revert a stuck/half-applied update offline
dism /image:F:\ /cleanup-image /revertpendingactions

:: Check and repair the filesystem on the offline volume
chkdsk F: /f

:: Repair the boot configuration data (run from the recovery environment)
bootrec /scanos
bootrec /rebuildbcd
```

For the INACCESSIBLE_BOOT_DEVICE case specifically, the additional step is to ensure the boot-critical storage drivers are present and enabled in the offline image, since the stop code reflects the operating system reaching the boot disk with the wrong or a missing controller driver. That is more involved than a single command and is the strongest argument for capturing a working image before making driver or controller changes, so that a regression has a known-good state to return to. As with every case in this guide, the read of the boot diagnostics screen comes first; the stop code on the screenshot is what tells you whether you are reverting an update, repairing boot records, or restoring a driver.

## The rescue VM workflow: az vm repair end to end

Every offline repair above shares one scaffold: get the broken OS disk attached to a healthy machine where you can work on it, fix the fault, and put the disk back. Azure provides a dedicated extension that automates exactly this, and it is the single most valuable tool for no-boot recovery. The repair extension creates a rescue machine in the same region, attaches a copy of the broken machine's OS disk to it as a data disk, and gives you a shell from which to work. When you are done, a restore command swaps the repaired disk back as the original machine's OS disk and cleans up the rescue machine.

The three commands form a complete cycle. The create step builds the rescue machine and attaches the disk copy. The run step can execute a canned repair script for the common faults, or you can skip it and work by hand. The restore step swaps the repaired disk back:

```bash
# 1. Create a rescue VM with a copy of the broken OS disk attached
az vm repair create \
  --resource-group myResourceGroup \
  --name myVm \
  --repair-username azureuser \
  --repair-password 'a-strong-password-here' \
  --verbose

# 2. (Optional) run a canned repair script against the attached disk,
#    for example a filesystem check or an fstab fix
az vm repair run \
  --resource-group myResourceGroup \
  --name myVm \
  --run-id linux-alar2 \
  --run-on-repair \
  --verbose

# 3. Swap the repaired disk back as the original VM's OS disk
az vm repair restore \
  --resource-group myResourceGroup \
  --name myVm \
  --verbose
```

### How do I use the VM repair commands to fix a no-boot VM?

Run `az vm repair create` to build a rescue machine with a copy of the broken OS disk attached, fix the fault on that disk either manually or with `az vm repair run`, then `az vm repair restore` to swap the repaired disk back as the original machine's OS disk. This avoids rebuilding the machine.

The canned scripts cover the high-frequency Linux faults, including filesystem checks, fstab repair, kernel cleanup, and GRUB fixes, under the automated Linux repair toolset, and the run identifiers for those scripts plus the equivalent Windows scripts should be confirmed against the current extension documentation, because the script catalog grows over time. When the canned scripts do not fit, you do the same work by hand. After the create step, the broken disk is mounted on the rescue machine as a data disk; you mount its root filesystem, chroot into it for the kernel, initramfs, or GRUB repairs, edit `/etc/fstab` directly for the mount repairs, or reclaim space for the full-disk case, then run the restore step. The restore is what makes this safe: it operates on the disk you repaired and reattaches it to the original machine, preserving the identity, the network configuration, and the data, which is exactly what a redeploy or a backup restore would have thrown away.

If you prefer not to use the extension, the same workflow is available manually. You stop and deallocate the broken machine, detach its OS disk, create or reuse a healthy rescue machine, attach the broken disk to it as a data disk, mount and repair it, detach it, and then swap it back onto the original machine as its OS disk with a disk swap operation. The extension simply automates this sequence and reduces the chance of a misstep, and it is worth using as the default. Either way, you will want to confirm that you have spare vCPU quota in the region for the rescue machine, since a rescue machine is a real machine that consumes quota; if you are near a regional or family quota ceiling, the rescue create can fail for the same quota reasons covered in the broader troubleshooting series, and you would resolve that first.

## Snapshotting the OS disk before you touch it

There is a step that experienced responders take before any repair and that newcomers skip under pressure: capture a point in time copy of the operating system volume before changing a single byte on it. A no-boot is stressful, and the temptation is to start editing the moment you have a shell on the rescue instance, but a repair is itself a change, and an incorrect repair can turn a recoverable fault into a harder one. A snapshot taken first is cheap insurance. It freezes the exact state of the failing volume so that every subsequent attempt starts from the same known baseline, and if a repair makes things worse, you create a fresh copy from the snapshot and try again rather than living with the damage your own commands caused.

The mechanics are simple and worth wiring into the runbook as a mandatory first action. A snapshot is a read only, point in time copy of a managed volume, billed only for the differential it holds, so it costs little and creates in seconds. You take one against the failing instance's operating system volume, give it a name that records the incident and the time, and only then proceed to attach a working copy to the rescue instance. Because the repair extension already operates on a copy rather than the live volume, the snapshot is a second layer of protection that guards you even against a mistake made on that copy:

```bash
# Capture a point-in-time snapshot of the failing OS disk before any repair
az snapshot create \
  --resource-group myResourceGroup \
  --name myVm-osdisk-incident-20220523 \
  --source "$(az vm show -g myResourceGroup -n myVm --query storageProfile.osDisk.managedDisk.id -o tsv)"
```

The discipline pays off in three distinct ways. First, it gives you freedom to be aggressive in diagnosis: you can run a filesystem check that might alter on disk structures, force a configuration edit, or rebuild an initramfs, knowing the original state is preserved and reproducible. Second, it gives you evidence. After the incident is resolved, the snapshot is a forensic record you can attach to a separate instance to understand exactly what failed, which is how a one time outage becomes a documented root cause rather than a mystery that recurs. Third, it gives you a clean fallback that is faster than a full backup restore: spinning a new volume from the incident snapshot is a quick operation, so even the worst case, where the repair path fails entirely, lands you back at the captured baseline rather than at last night's backup with a day of lost work.

There is one nuance worth stating for encrypted volumes. A snapshot of an encrypted volume is itself encrypted and depends on the same key, so the evidence and fallback value only holds while the key remains valid, which is one more reason to guard the backing vault. For the common unencrypted case, though, the rule is unconditional: snapshot first, repair second. It adds seconds to the start of every recovery and removes the single largest risk in the whole procedure, which is that the act of fixing a fragile system breaks it further with no way back.

## What the canned repair scripts cover and when to skip them

The repair extension's run step is worth understanding in more depth, because used well it turns several of the manual procedures above into a single command, and used blindly it can mask a fault you needed to understand. The automated Linux repair toolset ships a catalog of scripts identified by run identifiers, each targeting a common no-boot signature. There are scripts that run a filesystem consistency check and repair on the attached operating system volume, scripts that comment out or correct a faulty entry in the mount configuration, scripts that clean up after a kernel update by removing the broken kernel and regenerating the initramfs, and scripts that reinstall or repair the bootloader so the firmware can find a valid loader again. There are equivalent automated procedures on the Windows side for the servicing and filesystem faults that produce the stop codes covered earlier. The exact run identifiers and the current catalog should always be confirmed against the live extension documentation, because the toolset grows and the identifiers are extended as new signatures are added.

The decision of when to lean on a canned script and when to do the work by hand comes down to whether you already know the fault. If the screen named the cause unambiguously, a full operating system volume that needs space reclaimed, a single bad mount entry, a kernel that did not finish installing, then the matching script is the fastest safe path, and running it against the attached copy is exactly what the automation is for. The script does on your behalf what you would otherwise type, and it does it consistently, which is valuable at three in the morning when a typo in a hand entered command is its own kind of risk.

The case for stepping in by hand is the case where the cause is not yet certain or where the fault is unusual. A canned filesystem repair is the right reflex for a clean, common corruption, but if the volume has an LVM layout, a thin pool that needs activation, or an encryption layer, the generic script may not understand the structure and you are better mounting it yourself and working deliberately. Likewise, when two faults stack, a kernel problem hidden behind a full volume, for instance, a script that fixes one will leave the instance still unable to start, and the manual path lets you see and clear both. The rule of thumb is that the automation is excellent at executing a known fix and poor at diagnosing an ambiguous one, so you let the console name the cause, and only then decide whether the canned script matches it closely enough to trust.

There is also a middle path that the best responders use: run the script with the option that operates on the attached copy, inspect the result before committing, and only then restore. Because the extension works against a copy rather than the live volume, a script that does not fully resolve the fault has cost you nothing but a few minutes, and you can fall back to the manual procedure on the same attached copy. This is why the snapshot first habit and the repair extension complement each other so well. The snapshot guarantees a baseline, the extension's copy guarantees the live original is untouched, and the run step gives you a fast first attempt that you can verify before it becomes permanent. Treated this way, the canned scripts are a force multiplier rather than a black box, and the engineer stays in control of a recovery that the automation merely accelerates.

## Mounting and chrooting the broken disk on a rescue VM

Several of the repairs above, the kernel and initramfs rebuild, the GRUB reinstall, and the deeper LVM work, share one offline procedure: mount the broken root filesystem on the rescue machine and enter it with `chroot` so that the repair commands run as though they were executing inside the original guest. This is the single most useful manual skill for no-boot recovery, because once you are chrooted, the distribution's own tools regenerate the initramfs, reinstall the bootloader, and rebuild the boot menu exactly as they would on a healthy system.

After the repair extension attaches the copy of the broken disk to the rescue machine as a data disk, you first identify which device it became and which partition holds root. `lsblk` lists the block devices with their sizes and mount points, and the attached copy is the unmounted disk that is not the rescue machine's own root. With the root partition identified, you mount it, bind the kernel's runtime filesystems into it so that tools relying on `/dev`, `/proc`, and `/sys` work correctly inside the chroot, and then enter:

```bash
# Identify the attached copy of the broken OS disk
lsblk

# Mount the broken root partition (example: /dev/sdc1) on a mount point
sudo mkdir -p /rescue
sudo mount /dev/sdc1 /rescue

# If the broken system has a separate /boot or EFI partition, mount those too
sudo mount /dev/sdc15 /rescue/boot/efi   # example EFI system partition

# Bind the runtime filesystems so chrooted tools behave correctly
for d in dev proc sys run; do sudo mount --bind /$d /rescue/$d; done

# Enter the broken system as if it were live
sudo chroot /rescue /bin/bash
```

Inside the chroot you run the distribution's normal repair commands. To rebuild the early boot image and the boot menu after a kernel problem, the Debian and Ubuntu family uses `update-initramfs -u -k all` followed by `update-grub`, while the Red Hat family uses `dracut --force --regenerate-all` followed by `grub2-mkconfig -o` against the appropriate grub configuration path. To reinstall a broken bootloader, you run the install command for the boot mode the machine uses, which is where confirming BIOS versus UEFI matters, since the install target differs. When the repairs are done, you leave the chroot and unmount cleanly so that nothing is left holding the disk, then return to the repair extension's restore step:

```bash
# Exit the chroot
exit

# Unmount in reverse order, including the bind mounts
for d in run sys proc dev; do sudo umount /rescue/$d; done
sudo umount /rescue/boot/efi 2>/dev/null
sudo umount /rescue
```

The mount points and device names in these examples are illustrative; read your own from `lsblk` rather than copying the letters, because the device assignment depends on how many disks the rescue machine already has. The pattern, however, is invariant: mount, bind, chroot, repair with the native tools, exit, unmount, restore. Confirm the exact initramfs and bootloader command names for the distribution you are repairing, since they differ across families and have changed across releases.

## Performing the disk swap manually without the extension

The repair extension automates a sequence you can perform directly, and understanding the manual version is worth the time, both because it works when the extension is unavailable and because it makes clear what the extension is actually doing. The manual swap rests on one Azure rule that trips people up: you cannot detach the OS disk from a machine that is merely stopped from inside the guest. The machine must be deallocated, the state in which Azure has released the compute, before the OS disk will detach. With that understood, the sequence is to deallocate the broken machine, detach its OS disk, attach that disk as a data disk to a healthy rescue machine, repair it, detach it again, and then set it back as the broken machine's OS disk with a swap operation:

```bash
# Deallocate the broken VM so its OS disk can be detached
az vm deallocate --resource-group myResourceGroup --name myVm

# Find the OS disk name
az vm show --resource-group myResourceGroup --name myVm \
  --query "storageProfile.osDisk.managedDisk.id" -o tsv

# Attach the broken OS disk to a healthy rescue VM as a data disk
az vm disk attach --resource-group myResourceGroup \
  --vm-name myRescueVm --name <brokenOsDiskName>

# ... mount, repair, and unmount on the rescue VM as shown above ...

# Detach the repaired disk from the rescue VM
az vm disk detach --resource-group myResourceGroup \
  --vm-name myRescueVm --name <brokenOsDiskName>

# Swap the repaired disk back as the original VM's OS disk
az vm update --resource-group myResourceGroup --name myVm \
  --os-disk <brokenOsDiskName>

# Start the original VM
az vm start --resource-group myResourceGroup --name myVm
```

The swap operation, setting the OS disk on the original machine to the disk you repaired, is the step that preserves identity. The machine keeps its name, its network interface, its public address, and its place in any availability construct, because only the OS disk changed and everything else about the resource stayed put. That preservation is the entire reason this approach beats a rebuild. A genuinely safer variant, when the data on the disk matters and the repair is risky, is to take a snapshot of the broken OS disk first and create the working copy from the snapshot, so that a botched repair costs you nothing and you can start over from the snapshot. The repair extension takes this protective approach by working on a copy; doing it manually, you add the snapshot step yourself.

## Live recovery from the serial console

Not every no-boot needs the rescue machine. When the fault is a configuration error you can correct in place, and you have working credentials, the serial console is faster because it skips the disk copy and swap entirely. The serial console is a live connection to the machine's console channel, so you can interrupt the bootloader, change the boot, and fix the running system. For the fstab and LVM cases above, the serial console fix shown in those sections is often all you need, and it leaves the original disk in place.

The most useful live technique on Linux is editing the kernel command line at the GRUB menu to force a recovery mode. The concrete keystrokes matter because the window to act is short. When the GRUB menu appears on the serial console, you highlight the default entry and press `e` to edit it, find the line beginning with `linux` that holds the kernel command line, move to its end, and append a directive that forces a minimal target. Appending `systemd.unit=emergency.target` boots to the emergency shell after the real root is mounted, which is enough to edit `/etc/fstab` or restore a permission. Appending `rd.break` instead stops inside the initramfs before root is mounted, which is where you go when the root filesystem itself needs a check before it is safe to mount. You then boot the edited entry with the key combination the menu shows:

```bash
# After reaching the emergency shell via systemd.unit=emergency.target
mount -o remount,rw /        # make root writable
# correct the offending /etc/fstab line or restore an ownership/mode here
systemctl daemon-reload
reboot

# If you used rd.break and landed in the initramfs before root mounted:
mount -o remount,rw /sysroot # root is mounted read-only under /sysroot
chroot /sysroot              # operate inside the real root
# run fsck or fix the boot-critical file, then:
exit
reboot
```

These edits are not persistent; they change only the single boot you are performing, which is exactly right for a one-time recovery. Once the system is up, you make the durable correction and regenerate the boot configuration if needed, and the next normal boot proceeds without the directive. On Windows, the serial console reaches the Special Administration Console, a text channel from which you can launch a command shell, though for most Windows no-boot cases the offline servicing through a rescue machine is more reliable than trying to repair a half-booted Windows from the text console. The decision rule between the two paths is simple: if the fault is a single editable file or a recoverable configuration and you have credentials, use the serial console; if the fault needs offline servicing, a chroot, a disk too full to write to, or you lack credentials, use the rescue machine.

## Disk encryption and the keys that block a boot

Machines with disk encryption add a dependency that can itself cause a no-boot, and it is one engineers often overlook because the encryption was set up long ago and forgotten. When the OS disk is encrypted, the machine needs the encryption key at boot to unlock the volume, and that key lives in a key vault. If the key vault access changed, if the key was rotated or disabled, or if the relationship between the machine and the vault was disturbed, the machine cannot unlock its own disk and cannot boot. The console signature here is the boot stalling at the point where it would unlock the encrypted volume, and the diagnosis is to check the encryption configuration and the key vault rather than the filesystem.

Recovering an encrypted machine through a rescue machine is more involved than the unencrypted cases, because the rescue machine must be able to unlock the disk to work on it, which means the key and the access to it must still be valid. This is the strongest argument for guarding the key vault that backs disk encryption as carefully as the machines themselves, and for confirming that key rotation procedures account for the machines that depend on those keys. If you operate encrypted machines, treat the key vault as a boot dependency in your runbooks, because a key vault change that looks harmless can render a fleet unbootable. The key management and access details belong with the broader identity and secrets practices in the series, and the specific recovery steps for an encrypted no-boot should be confirmed against the current official guidance, since the encryption tooling has evolved.

The practical recovery flow for an encrypted instance differs from the unencrypted cases in one decisive way: the rescue machine cannot read the attached copy until the volume is unlocked, so the key and the access to it must still be valid for any offline repair to be possible at all. This makes the order of operations matter. You first confirm that the key in the vault still exists and is enabled, that the access the unlock depends on is intact, and only then attempt the rescue attach, because attaching a disk you cannot unlock leaves you stuck at the same wall the original instance hit. If the key was deleted, the recovery is no longer a boot repair but a key recovery, and a vault with soft delete and purge protection becomes the difference between a recoverable instance and a lost one. The lesson for anyone running encrypted instances is to treat the backing vault as a first-class boot dependency: protect the keys with soft delete and purge protection, document which instances depend on which keys, and rehearse the unlock path so that a no-boot on an encrypted instance is a known procedure rather than a discovery made under pressure.

## Why redeploy and restore-from-backup are the last resort, not the first

The redeploy operation moves a machine to a different host in the fabric. It is the right tool when the problem is the host: a machine that became unreachable because of an underlying hardware fault, a host that needs to be vacated, a platform-level issue with the specific node the machine landed on. It is the wrong tool for a guest no-boot, because moving the same broken disk to a new host changes nothing about the kernel, the fstab, the bootloader, or the full disk that is actually stopping the boot. Reaching for redeploy on a guest no-boot is the single most common misdiagnosis, and it wastes time while the cause sits unread in the boot log.

Restoring from backup is similarly a last resort rather than a first move, because it trades away every change made since the last backup to solve a problem that the rescue machine usually fixes without losing anything. A backup restore is the correct answer when the disk is genuinely damaged beyond repair, when the data is corrupted rather than the boot configuration, or when the recovery time of a restore is genuinely shorter than a diagnosis under a hard deadline. Those cases exist, which is exactly why a tested backup matters, and the safety net is worth building before you need it; the series covers that in the guide to [configuring Azure Backup for virtual machines correctly](/2023/07/03/configure-azure-vm-backup/). The point is sequencing: diagnose from the console, repair through the rescue machine, and treat redeploy and restore as the fallbacks for the genuinely unrecoverable, not as the reflex for a machine that simply has a bad line in a configuration file.

The signals that genuinely point at the host rather than the guest are worth naming so you can recognize the rare case where redeploy is correct. A host problem typically shows up as an instance that became unreachable without any change inside it, often accompanied by a platform health notification about the underlying node, scheduled maintenance, or a degraded host, and crucially the boot diagnostics screenshot shows the guest healthy or shows nothing because the issue is below the guest. When the platform itself reports a node problem, when several instances on the same host degrade together, or when an instance stops responding with no corresponding guest change and a clean console history, moving to a fresh host is the right move. The discriminator remains the console: a guest that the screenshot shows panicking or hanging is a guest problem that travels with the disk, while a guest the screenshot shows healthy on an instance the platform flags as unhealthy is a host problem that a new host resolves.

## Preventing the next no-boot

Most no-boot causes are preventable with a handful of habits that cost nothing and pay off the first time they save a machine. Every optional mount in `/etc/fstab` should carry `nofail`, so a missing data disk degrades to a missing mount that you can fix over SSH rather than a hang that locks you out. Free space on the OS disk should be monitored with an alert that fires while there is still room to act, because a disk that fills overnight becomes a no-boot by morning. Kernel and operating system updates should be staged through a canary machine that reboots after patching, so a bad initramfs or a half-applied Windows update is discovered on a disposable instance rather than a production one. Recursive permission changes near the system root should be banned outright, because the few seconds they save are not worth the cleanup of a machine that will not start.

Boot diagnostics should be enabled on every machine before you need it, not after, because enabling it on a machine that is already dark is one more step between you and the screenshot that names the cause. The same goes for the serial console packages in any custom image you build; baking them in means the live console is available the day a machine refuses to boot, rather than discovering at the worst moment that the image cannot expose it. None of these is expensive, and together they turn most no-boot incidents into either a non-event or a five-minute repair.

## Building a no-boot runbook your on-call can follow

The fastest recoveries happen when the diagnosis is not improvised at three in the morning but followed from a runbook the on-call engineer already trusts. The serial-console-first rule turns naturally into an ordered procedure, and writing it down so anyone on the rotation can execute it is what separates a team that recovers in minutes from one that escalates and waits. The first step is always to confirm the instance actually reached a host, ruling out an allocation or quota condition, because that sends you to a different playbook entirely. The second step is to read the boot diagnostics screenshot and serial log and place the symptom on the triage table, which names the cause and the branch. The third step is to choose the path: a live serial console fix when the fault is a single editable configuration and credentials exist, or the rescue machine when the fault needs offline servicing. The fourth step is the repair itself, taken from the relevant section above. The fifth step is to reattach and verify, confirming the instance reaches a login and the workload returns. The sixth step, the one teams skip and regret, is to record what caused the incident and add the prevention so the same cause cannot recur silently.

A runbook is only as good as the access and the artifacts behind it, so the runbook should also state what must already be in place: boot diagnostics enabled on every instance, the permissions to create a rescue machine and swap disks held by whoever is on call, spare regional quota for a rescue machine, and a known-good reference instance of each common image for comparing permissions and configuration. It should name the commands rather than leave them to memory, the instance-view check, the boot-log retrieval, the repair create, run, and restore, and the manual swap as a fallback, so that the engineer copies and adapts rather than recalls under pressure. The point of the runbook is not to replace understanding but to make the understanding executable when the person executing it is tired and the workload is down. The triage table and the ordered steps together are the artifact to paste into your operations documentation and rehearse, because the rehearsal is what makes the real incident unremarkable.

The most valuable rehearsal is deliberate breakage in a safe place. Building an instance specifically to break and recover, adding a bad fstab line and recovering it, filling the disk and recovering it, removing a kernel and recovering it, teaches the muscle memory that a written runbook alone cannot. Doing this on a disposable instance means the first time an engineer performs the rescue swap is not during a real outage, which is exactly when a missed step costs the most. Treat the no-boot recovery as a drill, run it until each branch is familiar, and the genuine incident becomes a procedure you have done many times rather than a crisis you are improvising through.

## Related failures this is often confused with

A genuine no-boot, where the operating system never reaches a login, is different from a machine that booted fine but will not let you in, and conflating the two sends you down the wrong path. When the machine is up and serving but you cannot connect, the problem lives in the network path or the remote-access service rather than the boot, and the diagnosis is entirely different. A Windows machine you cannot reach over RDP is usually a network or authentication problem at the remote desktop layer, which the series treats in the guide to [fixing Azure VM RDP connection errors](/2022/05/30/fix-azure-vm-rdp-connection-error/), and a Linux machine you cannot reach over SSH is usually a port, key, or service problem, covered in the companion guide to [fixing Azure VM SSH connection refused](/2022/06/06/fix-azure-vm-ssh-connection-refused/). The tell is whether boot diagnostics shows a login prompt: if the console reached a login and the machine is listening, it booted, and your problem is connectivity rather than boot.

The other frequent confusion is the provisioning timeout, where a machine boots, reaches a login on the console, but the deployment still reports a failure because the guest agent or cloud-init did not finish its work in time. That is not a no-boot; the operating system is running. The fix is in the agent or the provisioning configuration, not in the bootloader or the filesystem, and reading the console screenshot prevents you from treating a provisioning fault as a boot fault. The discipline that prevents both confusions is the same one this entire guide rests on: read the console first, and let what it shows route you to the correct class of problem.

## The verdict

A dead Azure machine is far less alarming once you treat it as a short list of readable symptoms rather than a black box. The boot diagnostics screenshot and the serial log tell you whether you are looking at an fstab hang, a full disk, a kernel or initramfs problem, a broken bootloader, an LVM activation failure, a permissions cascade, or a Windows servicing fault, and each of those has a confirming check and a tested fix. The recovery scaffold is constant across all of them: read the screen, attach the disk to a rescue machine, fix the specific fault, and reattach. Redeploy and restore are the fallbacks for the genuinely unrecoverable, not the reflex for a machine with a bad configuration line.

The engineers who recover a no-boot in minutes are not faster typists; they are the ones who look before they act and who built the cheap prevention in advance. Enable boot diagnostics everywhere, add `nofail` to every optional mount, monitor disk space, stage kernel updates through a canary, and keep a tested backup as the genuine last resort. Do that, and the next time a machine goes dark you will read the cause off the screen, fix the disk on a rescue machine, and bring the original back with its state intact. To practice the full sequence on a machine you can safely break and recover, [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), and to drill the diagnosis under realistic incident conditions, [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html), where you can reproduce each no-boot signature and rehearse the rescue workflow until it is muscle memory.

## Frequently Asked Questions

### Q: Why did my Azure VM stop booting after a kernel update?

A kernel update installs a new kernel, rebuilds the initramfs, and points the bootloader at the new kernel as the default. If the initramfs was built without a driver the root filesystem needs, or the regeneration failed quietly, or the bootloader points at a kernel that is not present, the next boot panics with an inability to mount the root filesystem. The cheapest recovery is to interrupt GRUB on the serial console and boot the previous kernel, which most distributions keep installed, confirming the diagnosis and giving you a working system to repair from. If that is not possible, chroot from a rescue machine and rebuild the initramfs and GRUB configuration so they agree with the installed kernel. Prevent it by staging kernel updates through a canary machine that reboots after patching.

### Q: How do I use the serial console to recover a VM that will not boot?

The serial console is a live connection to the machine's console channel, available once boot diagnostics is enabled and the image supports it. For Linux you can interrupt GRUB, edit the kernel command line to add an emergency or single-user target, and reach a shell before the failing mount or service stalls the boot, then remount root read-write and fix the file that broke. For Windows you reach the Special Administration Console and can launch a command shell. Use the serial console when the fault is a single editable configuration and you have credentials, because it avoids the disk copy and swap that the rescue machine requires. When the fault needs offline servicing or you lack credentials, switch to the rescue machine workflow instead.

### Q: What is the difference between a VM redeploy and the repair workflow?

A redeploy moves the machine to a different host in the fabric, which fixes host-level problems such as a hardware fault or an unhealthy node, but does nothing for a guest no-boot, because the same broken disk with its bad fstab, full filesystem, or non-bootable kernel travels to the new host unchanged. The repair workflow instead attaches a copy of the broken OS disk to a rescue machine, lets you fix the actual fault, and swaps the repaired disk back, preserving the machine's identity, network configuration, and data. Reaching for redeploy on a guest no-boot is a common misdiagnosis that wastes time. Use redeploy for host problems and the repair workflow for anything the boot log shows is inside the guest.

### Q: My VM shows a GRUB rescue prompt, how do I fix it?

A `grub rescue>` prompt means the bootloader started but cannot find its configuration, its modules, or the kernel, often after a partition change, an interrupted GRUB update, or a filesystem repair that moved blocks. You can sometimes hand-walk GRUB to a kernel by setting the root and prefix variables and loading the normal module, but that is fragile and does not survive a reboot. The durable fix is to chroot into the root filesystem from a rescue machine, reinstall GRUB to the correct boot location, and regenerate its configuration so the next boot finds everything. Confirm whether the machine boots in BIOS or UEFI mode before reinstalling, because installing the wrong bootloader type will not help.

### Q: How do I recover a VM with a full OS disk if I cannot log in?

Attach the OS disk to a rescue machine using the repair workflow, mount it, and reclaim space offline where you have a working shell with room to operate. The usual culprits are runaway application logs and an oversized systemd journal, which you can cap and vacuum, and large temporary files you can identify by scanning for the biggest space consumers. If the disk is simply too small for the workload, grow the managed OS disk while the machine is deallocated and then extend the partition and filesystem from the guest so the new capacity is usable. Both the Azure resize and the guest filesystem extension must happen for the space to count. Prevent recurrence with a free-space alert that fires before the disk fills.

### Q: Does the serial console require boot diagnostics to be enabled?

Yes. The serial console relies on the same console channel that boot diagnostics captures, so boot diagnostics must be enabled for the serial console to connect, and the image must include the serial console support that the standard Azure Marketplace images carry. Managed boot diagnostics, which writes to an Azure-managed location rather than a storage account you provision, is the current default for many images, but you should confirm it is on for any machine you intend to operate seriously, ideally before a problem arises. Enabling it on a machine that is already dark is one more step between you and the screenshot that names the cause, so treat enabling boot diagnostics as part of provisioning rather than as a reaction to an incident.

### Q: Why does my Linux VM drop into emergency mode on boot?

Emergency mode means systemd could not complete the early boot, and on a cloud machine the overwhelming cause is a failed mount declared in `/etc/fstab`, usually for a data disk whose device is missing, whose UUID changed, or whose entry has a typo. systemd treats each fstab line as a required mount, so a failure stalls the local filesystems target and the rest of the boot with it. From the serial console, log in at the emergency prompt, remount root read-write, correct or comment out the bad line, add `nofail` to optional mounts, and reboot. The prevention is to add `nofail` to every non-essential mount so a missing data disk becomes a missing mount you can fix over SSH rather than a hang.

### Q: What does INACCESSIBLE_BOOT_DEVICE mean on an Azure Windows VM?

It is a Windows stop code that appears when the operating system cannot reach the disk holding the system early in boot. On a cloud machine this is almost never a physical disk fault; it is a boot-critical storage driver that changed, a controller configuration that no longer matches, or an update that altered the driver stack so the boot disk is unreachable with the drivers loaded at that stage. The repair is offline from a rescue machine: revert the pending servicing actions to undo a half-applied update, and repair the boot configuration so the firmware finds the system. Confirm the current servicing and boot-repair command syntax against the official documentation, and always work against the copy of the disk on the rescue machine.

### Q: My Windows VM is stuck on "Getting Windows ready", what do I do?

That screen, along with "Undoing changes", means an update was half-applied and the machine cannot move forward or cleanly roll back on its own, leaving it in a loop. Waiting rarely resolves it once it has stalled for an extended period. The fix is to revert the pending servicing actions offline from a rescue machine, which undoes the stuck update and lets the machine boot. Attach a copy of the OS disk to the rescue machine, point the servicing image tools at the offline Windows installation, revert the pending actions, then swap the disk back. Because the exact command targets an offline image path and depends on the Windows version, verify the current syntax against the official documentation before running it, and operate only on the disk copy so a mistake costs nothing.

### Q: Can I fix a no-boot VM without creating a rescue VM?

Sometimes. If the fault is a single editable configuration such as a bad fstab line or an LVM activation that you can correct from the initramfs shell, and you have working credentials, the serial console lets you fix it in place without any disk copy or swap. That path is faster when it applies. When the fault needs offline servicing, a chroot to rebuild an initramfs or reinstall GRUB, a disk too full to write to, a Windows update reversal, or when you lack credentials at the console, the rescue machine is necessary because you cannot safely do that work on the running system. The decision rule is whether the repair can be made live with credentials or needs the disk worked on offline; choose the lighter path when it fits.

### Q: How do I tell whether the problem is the boot or the network?

Read the boot diagnostics screenshot. If the console reached a login prompt, whether a Linux getty or a Windows sign-in screen, the machine booted successfully and your inability to connect is a network or remote-access problem rather than a boot problem. If the console shows a kernel panic, a GRUB prompt, an emergency shell, a stop code, or a stalled update screen, it is a genuine no-boot. This single check routes you to the correct class of problem and prevents the common mistake of treating an unreachable but running machine as a no-boot, or treating a no-boot as a firewall issue. The console screenshot is the fastest discriminator you have, which is why reading it first is the rule.

### Q: What permissions or roles do I need to run the VM repair commands?

The repair workflow creates a rescue machine, attaches disks, and swaps the OS disk back, which are write operations against the resource group and the machine, so you need a role with permission to create and manage virtual machines and disks in that scope, such as a contributor-level role on the resource group. You also need spare vCPU quota in the region for the rescue machine, since it is a real machine that consumes quota. Confirm the exact role and quota requirements against the current official documentation, because role definitions and the repair extension both evolve. If you are near a regional or family quota ceiling, the rescue create can fail, and you would request a quota increase or free capacity before retrying the repair.

### Q: Why did my VM boot fine before but fail after I attached a data disk?

Because the change that breaks boot is usually the fstab entry you added for the new disk, not the disk itself. When you format a data disk and add a mount line to `/etc/fstab` so it mounts on reboot, you create a hard boot dependency on that device. The machine keeps running until the next restart, which may be days later, and then hangs in emergency mode if the device is missing, the UUID is wrong, or the line has a typo. This delayed failure is why the cause feels disconnected from the change. Always add `nofail` to data-disk mounts so the boot tolerates a missing disk, and test the entry with `mount -a` before relying on a reboot to validate it.

### Q: How long should I wait before deciding a Windows update loop is stuck?

There is no fixed number, and treating one as universal would be misleading, because legitimate update processing can take a long time on a slow disk or a large update. The better signal is behavior rather than a stopwatch: if the screen has not changed for an extended period, if there is no disk activity, or if the machine has cycled through "Getting Windows ready" and "Undoing changes" repeatedly, it is stuck rather than working. At that point, rather than waiting longer, attach the disk to a rescue machine and revert the pending servicing actions offline, which is deterministic and does not depend on guessing whether more patience would help. Confirm the current revert syntax against the official documentation before running it.

### Q: Can a recursive chmod or chown cause an Azure VM no-boot?

Yes, and it is a self-inflicted failure worth guarding against specifically. systemd and the services it starts require correct ownership and mode on certain system directories and files, and a recursive permission change that sweeps through a path near the system root can leave core services unable to start, producing a boot that fails with a cascade of permission or security errors. The repair is to restore the expected ownership and mode on the affected path, best done offline from a rescue machine where you can compare against a known-good reference. There is no universal one-line fix because the correct ownership depends on which path was damaged. Prevent it by banning broad recursive permission changes near the system root and scoping any permission change tightly.

### Q: Should I restore from backup when a VM will not boot?

Only as a last resort. A backup restore trades away every change made since the last backup, which is exactly the state you want to preserve, to solve a problem the rescue machine usually fixes without losing anything. Restore is the right answer when the disk is genuinely damaged beyond repair, when the data itself is corrupted rather than the boot configuration, or when a restore is provably faster than diagnosis under a hard deadline. Those cases are why a tested backup matters and should be configured in advance. For an ordinary no-boot caused by a bad configuration line, a full disk, or a kernel problem, diagnose from the console and repair through the rescue machine first, and keep restore as the fallback for the genuinely unrecoverable.

### Q: How do I prevent the most common Azure VM boot failures?

Build a few cheap habits. Add `nofail` to every optional mount in `/etc/fstab` so a missing data disk degrades to a missing mount rather than a hang. Monitor OS disk free space with an alert that fires while there is still room to act. Stage kernel and operating system updates through a canary machine that reboots after patching, so a bad initramfs or half-applied update is caught on a disposable instance. Ban recursive permission changes near the system root. Enable boot diagnostics on every machine before you need it, and bake the serial console packages into any custom image. None of these is expensive, and together they turn most no-boot incidents into either a non-event or a five-minute repair instead of a lost afternoon.

### Q: Why does my VM hang on "A start job is running for"?

That message means systemd is waiting for a unit to finish and counting down a timeout, and the boot will not proceed until the job completes or the timeout expires. The usual culprits are a network mount or a device that is not present, a service that blocks on something unavailable, or a fsck that is taking a long time on a large or dirty filesystem. The serial console shows which unit the job belongs to, which points you straight at the cause: a network filesystem that is unreachable, a data disk that detached, or a check in progress. The fix depends on the unit. For a stuck device or mount, the durable correction is the same `nofail` and device-timeout treatment used for fstab; for a long fsck, letting it finish once and then addressing the underlying filesystem error prevents the repeat.

### Q: How do I chroot into the broken OS disk on a rescue VM?

After the broken OS disk is attached to the rescue machine as a data disk, identify its root partition with `lsblk`, mount that partition on a directory such as `/rescue`, mount any separate boot or EFI partition into the right place beneath it, then bind the runtime filesystems with `mount --bind` for `/dev`, `/proc`, `/sys`, and `/run` so that tools inside the chroot behave correctly. Enter with `chroot /rescue /bin/bash`, run the distribution's native repair commands to rebuild the initramfs, reinstall the bootloader, or regenerate the boot menu, then exit and unmount everything in reverse order, including the bind mounts, before running the restore step. Read your own device names from `lsblk` rather than copying example letters, because the assignment depends on how many disks the rescue machine already has.

### Q: Can a guest agent or extension failure cause an Azure VM boot failure?

It can cause a deployment to report failure, but it is usually not a true no-boot, and telling the two apart prevents the wrong fix. If the operating system reaches a login on the boot diagnostics screenshot, the instance booted, and a guest agent or extension that failed or timed out is a provisioning problem to address in the agent logs or the extension configuration, not in the bootloader or the filesystem. A genuine no-boot, where the console shows a panic, a GRUB prompt, an emergency shell, or a stop code, is a different class entirely. The exception is a poorly written custom extension or a boot-time script that damages a system file or fills the disk, which can produce a real no-boot as a side effect; in that case you diagnose and repair the underlying damage through the rescue workflow, then fix the script so it cannot recur.
