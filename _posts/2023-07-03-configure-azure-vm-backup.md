---
layout: post
title: "Configure Azure Backup for VMs Correctly"
page_title: "Configure Azure Backup for VMs: Recovery Services Vault, Policy, App-Consistent Snapshots, and a Tested Restore"
date: 2023-07-03
categories: ["Technology"]
tags: ["Azure", "Azure Backup", "Virtual Machines", "Architecture", "Cloud Computing"]
excerpt: "Configure Azure Backup for VMs so a machine is recoverable, not merely protected: the vault, the policy, app-consistent snapshots, and a tested restore."
image: "/assets/images/blog/blog-40.webp"
reading_time: 63
author: "ryan-walsh"
last_updated: 2023-07-03
lang: en
---
A virtual machine that has a green checkmark next to its name in the portal is not the same as a virtual machine you can get back. The gap between those two states is where most teams discover, at the worst possible moment, that they configured Azure Backup to run rather than configured it to recover. The job succeeds every night, the protected-instance count looks healthy, and then a ransomware event or a botched in-place upgrade arrives and the restore either fails, takes far longer than anyone budgeted, or hands back a database in a torn state that the application refuses to open. To configure Azure Backup for VMs correctly, you have to treat the running job as the means and the proven recovery as the end. This guide walks the whole path: the Recovery Services vault and the backup policy, the schedule and retention tiers, the snapshot consistency levels that decide whether a restored database opens cleanly, the restore options that determine how fast you can be back, cross-region restore for a regional outage, the cost drivers that creep up quietly, and the one verification step that separates a backup from a recovery. The reward for getting it right is dull and precise: when something destroys a machine, you bring it back, and the incident becomes a footnote instead of a postmortem.

![Configure Azure Backup for VMs correctly with a Recovery Services vault, backup policy, application-consistent snapshots, and a tested restore](/assets/images/blog/blog-40.webp)

## What correct configuration buys, and what breaks when it is wrong

The thing correct configuration buys is a recovery time and a recovery point you can actually defend in a meeting. A recovery point is how far back in time you can go, set by how often the job runs and how long each point is kept. A recovery time is how long it takes to put a working machine back in service once you decide to recover. Both are properties you design, not properties you discover during an outage. When the policy is right, the consistency level matches the workload, and a restore has been rehearsed, those two numbers are known quantities you can quote to the business with a straight face.

When the configuration is wrong, the failures cluster into a small set of recurring shapes, and every one of them is avoidable at setup time. A protected machine whose restore has never been tried is the most common and the most dangerous, because confidence runs high right up until the recovery itself produces an error nobody has seen before. A database captured with the wrong consistency level restores into a state the engine treats as crash recovery at best and corruption at worst. A retention window set to a tidy thirty days quietly violates a compliance rule that demanded a year. A full-machine restore eats hours when all anyone needed was a single deleted folder that file-level recovery would have produced in minutes. A regional outage finds a team with every recovery point trapped in the dead region because cross-region restore was never enabled. And a monthly bill climbs without explanation because retention got generous and nobody connected the dollars to the days.

The unifying idea across all of these is the namable rule this article is built around, the one to carry into every backup design you ever touch.

### What is the tested-restore rule?

The tested-restore rule says a backup is only real once a restore has been performed and verified. A successful job proves the protection pipeline can read your disks; it proves nothing about whether you can get a working machine back. The configuration is finished at the first verified recovery, not the first green job.

That distinction reframes the entire setup. Every decision below, from which consistency level to pick to how long to retain points to whether to turn on cross-region restore, exists to make the eventual restore succeed and succeed quickly. The job running is table stakes. The restore working is the product. Hold that idea while we walk the prerequisites, because the order in which you build the pieces matters as much as the pieces themselves.

## How Azure Backup actually works for a virtual machine

Before configuring anything well, you need a mental model of what the service does under the hood, because nearly every misconfiguration traces back to a model that is missing a piece. Azure Backup for a machine is a two-phase operation, and the two phases live in two different places with two different cost and speed characteristics. Understanding that split explains why a restore can be nearly instant in one situation and slow in another, why a job can report success while leaving you exposed, and why some settings cannot be changed after the fact.

The first phase is the snapshot. When a job runs, the platform takes a snapshot of the machine's managed disks, and for a brief window that snapshot is held locally, close to the machine, in what is sometimes called the instant-recovery tier. A restore from a snapshot still sitting in this tier is fast, because the data has not had to travel anywhere and the recovery point is essentially a local copy. The second phase is the transfer, where the snapshot data is copied into the Recovery Services vault's own storage. Once a recovery point lives in vault storage, it is durable according to the vault's redundancy setting, but a restore from it has to read it back out of that storage rather than from a local snapshot, which is part of why restore times vary with where the recovery point currently lives and how large it is.

This two-phase shape has direct consequences for configuration. The snapshot phase is what the quiesce affects, so consistency is decided there, in cooperation with the guest. The transfer phase is what the vault redundancy affects, so durability and regional resilience are decided there. The brief local-snapshot retention controls how long the fast instant-recovery path is available before a restore has to come from vault storage. A team that does not know the two phases exist will be puzzled when an early restore is quick and a later one from the same machine is slow, when the only difference is which tier the recovery point was read from.

### What is the difference between the snapshot tier and the vault tier?

The snapshot tier holds a recovery point locally near the machine for a short window, so a restore from it is fast. The vault tier holds the recovery point in the Recovery Services vault's durable, redundant storage for the full retention period. A point moves from snapshot to vault as the job completes its transfer phase.

The second piece of the model is the protected item and the container. When you enable protection on a machine, the vault gains a container representing the machine and a protected item representing what is being backed up within it. Recovery points attach to that protected item. This is why deleting the machine does not delete the recovery points: the protected item and its history live in the vault independently of the running machine, and they persist until you explicitly stop protection and remove the points. It is also why the command line refers to a container name and an item name separately; they are distinct objects in the vault's model, even though for a single machine they often share a name.

The third piece is the relationship between the vault and the policy. A policy is a vault-scoped object that several machines can share, and a machine references exactly one policy at a time. Changing a policy changes the behavior for every machine bound to it, which is powerful and dangerous in equal measure. Tightening retention on a shared policy to save money on one workload silently shortens the recoverable history for every other machine on that policy, which is one more reason to group machines by genuine requirement rather than convenience. Holding these three pieces, the two phases, the protected item, and the shared policy, makes the rest of the configuration legible rather than a sequence of opaque clicks.

## The prerequisites and the correct order of operations

Azure Backup for virtual machines is an agentless service for the snapshot itself, but that phrasing hides a detail that trips people up. The platform takes a disk-level snapshot at the infrastructure layer without you installing anything, yet the quality of that snapshot, specifically whether it is application-consistent, depends on an extension that runs inside the guest. So the mental model to carry is two cooperating layers: an outer layer that owns the Recovery Services vault, the policy, and the snapshot orchestration, and an inner layer, the guest agent, that quiesces the operating system and any registered applications so the snapshot captures a coherent moment rather than a smear across time.

Before any of that, the prerequisites split into identity, networking, and the guest itself. On identity, the account or service principal driving the configuration needs rights to create the vault, define the policy, and enable protection on the target machine. The Backup Contributor and Backup Operator roles exist precisely for this division of labor, and granting the narrower of the two to the automation that enables protection is the least-privilege choice. On networking, the snapshot transfer and the metadata traffic need a path out; a machine locked down with no outbound route, no service tag allowance, and no private endpoint for the vault will take snapshots that then cannot be copied to vault storage, and the job will stall at the transfer phase rather than the snapshot phase. On the guest, a Linux or Windows machine needs the Azure VM Agent present and healthy, because the backup extension rides on top of it; a machine whose agent has gone stale after an image build will report the snapshot succeeded while silently downgrading to a crash-consistent capture.

The order of operations is not arbitrary, and doing it out of order is one of the quieter ways to end up with a configuration that looks complete but recovers badly. Build the vault first, because the policy lives inside it and the protection assignment references both. Define the policy second, because enabling protection without a deliberate policy lands the machine on a default schedule and retention that almost never match what the workload actually needs. Enable protection third, binding the machine to the policy. Then, and this is the step that converts a setup into a recovery capability, run an on-demand backup and immediately rehearse a restore from it. Skipping the rehearsal is the single most common reason a team believes it is protected when it is not.

### Why does the order of operations matter so much?

Each artifact references the one built before it, so building out of sequence forces rework or, worse, accepts a default you did not choose. The vault holds the policy; the policy shapes the schedule and retention; the protection assignment binds a machine to that policy. Build them in that order and every later decision inherits a deliberate foundation.

### The InsightCrunch VM backup setup checklist

The findable artifact for this guide is a checklist that maps each setup step to the decision it forces and the gotcha that bites teams who skip the thinking. Treat it as the spine of the whole configuration, and treat the rightmost column as the part most people get wrong.

| Step | The decision it forces | The gotcha to avoid |
| --- | --- | --- |
| Create the Recovery Services vault | Region, redundancy (LRS, ZRS, or GRS), and whether cross-region restore is on | Leaving redundancy at the default means a regional event can strip every recovery point at once |
| Define the backup policy | Frequency, the time of the daily snapshot, and the retention tiers for daily, weekly, monthly, yearly points | Accepting the default policy lands a workload on a schedule and retention nobody chose |
| Confirm snapshot consistency | Whether the guest agent is healthy enough for an application-consistent capture | A stale agent silently downgrades to crash-consistent, and the database restores in a bad state |
| Enable protection on the machine | Which machines bind to which policy, and how that scales across a fleet | Enabling per-machine by hand does not scale and drifts; this is the step to express as code |
| Set retention against the requirement | The longest legal or business obligation the points must satisfy | A tidy thirty-day window can violate a one-year compliance mandate |
| Decide on cross-region restore | Whether a regional outage must be survivable from the recovery side | Cross-region restore generally cannot be retrofitted onto an existing vault after the fact |
| Run an on-demand backup | That a real recovery point exists before you depend on the schedule | Waiting for the first scheduled job delays the only thing that proves the pipeline works |
| Rehearse and verify a restore | That recovery actually produces a working machine, file, or disk | A restore that has never been run is an assumption, not a capability |

The checklist is deliberately ordered so that the verification step sits at the bottom, because that is where the tested-restore rule lands. Everything above it is preparation; the last row is the only one that proves the preparation paid off.

## Networking and identity prerequisites in depth

The prerequisites deserve more than a checklist mention, because a backup that fails at the transfer phase rather than the snapshot phase almost always traces to networking, and a configuration that cannot be enabled at all almost always traces to identity. Both are worth setting up deliberately rather than discovering reactively.

On networking, recall the two-phase model: the snapshot is local, but the transfer moves data into vault storage, and that transfer needs a path. A machine in a locked-down subnet with no outbound internet route, restrictive network security group rules, and no allowance for the backup service will snapshot fine and then stall when the data tries to reach the vault. There are two clean ways to provide the path. The first is to allow the backup service through using the appropriate service tags on the network security group rules, which lets the transfer traffic reach the platform endpoints without opening broad internet access. The second, and stronger for a security-sensitive environment, is a private endpoint for the vault, which brings the vault into your private address space so the transfer never traverses the public internet at all. The private-endpoint path takes more setup but produces a backup flow that satisfies a no-public-egress policy, and it composes naturally with the rest of a private networking design. Whichever path you choose, decide it before enabling protection, because a transfer that stalls on a network gap looks like a backup problem when it is really a routing problem, and chasing it in the wrong layer wastes the time you would rather spend elsewhere.

On identity, the division of roles matters for both least privilege and operational clarity. The identity that creates and manages vaults and policies needs broad backup-management rights, and the contributor-level role grants them. The identity that runs jobs and restores but should never redefine protection needs only the operator-level role, which is the right grant for day-to-day automation. The identity that only watches needs reader-level rights and nothing more. Mapping these to real principals, with the powerful role reserved for the few identities that genuinely manage policy and the narrower roles for everything else, keeps a compromised credential from being able to dismantle the protection it was only ever supposed to monitor. This is the same least-privilege thinking that runs through the rest of a well-built Azure estate, and the backup configuration is no place to abandon it.

### Why does my backup job fail at the transfer step but the snapshot succeeds?

The snapshot is local and needs no network path, but the transfer moves data into vault storage and does need one. A locked-down subnet with no outbound route or no allowance for the backup service will let the snapshot succeed and then stall the transfer. Allow the service via network security group service tags or, better, a private endpoint for the vault.

The order-of-operations point applies here too: provision the network path and assign the identity roles before you enable protection, not after the first job fails. A configuration built in the right order rarely surfaces these as incidents at all, because the path and the permissions were in place before anything depended on them, which is the whole reason the order matters.

## The step-by-step setup with working commands

The portal walks you through this with a wizard, and the wizard is fine for a first machine. For anything beyond a single learning exercise, the command line is the honest way to configure Azure Backup, because it forces every choice into the open instead of accepting whatever the wizard pre-selected. The walkthrough below uses the Azure CLI; the equivalent PowerShell cmdlets exist for every step and follow the same shape. Treat the values here as illustrative and verify any limit, region availability, or SKU name against the current official documentation at the time you read this, since Azure revises these regularly.

Start with a resource group and the vault. The vault is a regional resource, and it must live in the same region as the machines it protects.

```bash
# Variables for the walkthrough
RG="rg-backup-prod"
LOC="eastus"
VAULT="rsv-prod-eastus"
VM="vm-app-01"

# Create the resource group if it does not exist
az group create --name "$RG" --location "$LOC"

# Create the Recovery Services vault
az backup vault create \
  --resource-group "$RG" \
  --name "$VAULT" \
  --location "$LOC"
```

With the vault created, set its storage redundancy deliberately. This is one of the settings the default gets wrong for a recovery-focused design, and it is also one you generally cannot change once recovery points exist in the vault, so decide it now. Geo-redundant storage keeps a copy of recovery points in a paired region, which is the foundation cross-region restore builds on. Zone-redundant storage protects against a single datacenter failure within the region. Locally redundant storage is the cheapest and the least resilient.

```bash
# Set storage redundancy to geo-redundant and enable cross-region restore
az backup vault backup-properties set \
  --resource-group "$RG" \
  --name "$VAULT" \
  --backup-storage-redundancy GeoRedundant \
  --cross-region-restore-flag true
```

Now define the backup policy. A policy bundles the schedule, the time of day the snapshot runs, the time zone, and the retention tiers. The point of writing it out rather than accepting a default is that every one of those values is a design decision. The snippet below shows a policy defined from a JSON document, which is the form you will reuse when you express the configuration as code later.

```bash
# Export the default policy as a starting template, then edit it
az backup policy show \
  --resource-group "$RG" \
  --vault-name "$VAULT" \
  --name "DefaultPolicy" \
  --output json > policy.json

# After editing policy.json to set schedule, time, and retention tiers:
az backup policy set \
  --resource-group "$RG" \
  --vault-name "$VAULT" \
  --policy policy.json \
  --name "prod-daily-35d-12m"
```

The policy name above encodes its intent, a daily snapshot with thirty-five daily points and twelve monthly points, so that anyone reading the vault later understands the obligation it satisfies without opening the JSON. Naming a policy after its retention shape is a small discipline that pays off when a fleet has a dozen policies and someone has to reason about which machines satisfy which rule.

With the vault and policy in place, enable protection on the machine. This is the step that binds a specific machine to a specific policy and starts the schedule.

```bash
# Enable backup protection for the VM under the named policy
az backup protection enable-for-vm \
  --resource-group "$RG" \
  --vault-name "$VAULT" \
  --vm "$VM" \
  --policy-name "prod-daily-35d-12m"
```

The schedule will now produce a recovery point at the policy's chosen time. Do not wait for it. The tested-restore rule says the configuration is unproven until a recovery has happened, so create a recovery point on demand right now and use it to rehearse.

```bash
# Trigger an on-demand backup, retained for 30 days
az backup protection backup-now \
  --resource-group "$RG" \
  --vault-name "$VAULT" \
  --container-name "$VM" \
  --item-name "$VM" \
  --retain-until 30-07-2023 \
  --backup-management-type AzureIaasVM
```

When the on-demand job completes, list the recovery points so you have an identifier to restore from. This identifier is what every restore path below consumes.

```bash
# List recovery points for the protected VM
az backup recoverypoint list \
  --resource-group "$RG" \
  --vault-name "$VAULT" \
  --container-name "$VM" \
  --item-name "$VM" \
  --backup-management-type AzureIaasVM \
  --output table
```

### How do I create the vault and policy without the portal wizard?

Create the vault with `az backup vault create`, set its redundancy with `az backup vault backup-properties set`, define a policy from an edited JSON template with `az backup policy set`, then bind the machine with `az backup protection enable-for-vm`. Scripting it forces every schedule and retention choice to be explicit rather than inherited from a default.

What the command sequence above produces is a machine on a deliberate schedule with a known retention shape and at least one recovery point that exists right now rather than at the next scheduled slot. That last property is what lets you move directly to the verification step instead of waiting overnight to learn whether the pipeline even works. Before the verification, though, the configuration has a layer that the commands above touched only implicitly and that decides whether a restored database is usable: the snapshot consistency level.

## The settings the defaults get wrong

A backup configuration that accepts every default will run. It will produce green jobs and a reassuring protected-instance count. It will also, in three specific places, quietly choose values that betray you during recovery. These are the settings to override on purpose, and the reasons matter more than the values.

### Snapshot consistency: the setting that decides whether a database opens

There are three consistency levels a snapshot can reach, and they form a ladder of increasing trustworthiness. A crash-consistent snapshot captures the disk exactly as it would look if the machine had lost power at that instant. Everything that was already written to disk is present; everything still buffered in memory is gone. An operating system usually survives this because journaling file systems are built to recover from a power loss, but an application with in-flight transactions may restore into a state it has to repair, and a database may treat the restored volume as something to run crash recovery against before it will serve queries. A file-system-consistent snapshot goes one step further by flushing pending file-system writes and freezing the file system briefly so the on-disk image is internally coherent, which removes the file-system repair but still does not coordinate with the application. An application-consistent snapshot is the top of the ladder: it signals the registered applications to quiesce, flushing their own buffers and reaching a transactionally clean point before the snapshot is taken, so a restored database opens cleanly without recovery or repair.

The reason this is the setting the default most dangerously gets wrong is that the platform does not refuse to back up a machine whose guest agent cannot reach application consistency. It downgrades. A machine with a stale or unhealthy agent, or one running a workload the agent cannot quiesce, falls back to file-system-consistent or crash-consistent and reports the job as a success. The protected-instance count does not flinch. The team that needed application consistency for a database has no signal that it lost it until a restore produces a database the engine refuses to open without recovery. The fix is to confirm, after enabling protection, that the recovery point's consistency level is what the workload requires, and to treat any downgrade as a failure to investigate rather than a job to ignore.

### Why does an application-consistent backup matter for a database?

A database keeps recent changes in memory before flushing them to disk, so a crash-consistent snapshot can capture a moment where the on-disk state is mid-transaction. An application-consistent snapshot quiesces the database first, flushing those buffers to a clean point, so the restored copy opens without crash recovery or corruption.

### Retention: the setting that quietly violates compliance

The default retention on a wizard-created policy is a round number that has nothing to do with your obligations. The question retention answers is not "how long feels safe" but "what is the longest period any rule, legal, regulatory, or contractual, requires a recoverable point to exist." A workload under a financial-records mandate may owe seven years of monthly or yearly points. A workload under a privacy regime may owe the opposite, a maximum retention beyond which data must not persist. Either way, the tidy thirty-day default is a guess, and a guess is exactly the wrong thing to put between an audit and a fine. Set the daily, weekly, monthly, and yearly tiers against the written requirement, and write the requirement into the policy name or its tags so the obligation travels with the configuration.

### Schedule: the setting that collides with the workload

The default snapshot time is whatever the wizard picked, and for an application-consistent capture that timing is not cosmetic. The quiesce briefly pauses application writes, so scheduling the snapshot during a heavy batch window or a peak-traffic period puts the pause where it hurts most. Worse, a machine that runs a nightly job which itself holds the application busy can collide with the snapshot in a way that either degrades the job or forces a consistency downgrade. Pick a quiet window, confirm the chosen window against the machine's actual activity rather than an assumption, and revisit it when the workload's rhythm changes.

The thread running through all three settings is that the default optimizes for a job that completes, not for a recovery that works. Overriding them is not gold-plating; it is the difference between a backup and a recovery capability. Which brings us to the step that proves the difference is real.

## How retention tiers actually work

Retention is more than a single number, and treating it as one is how teams either overpay or under-comply. A backup policy expresses retention as a set of tiers that follow a grandfather-father-son scheme, where daily points are kept for a short window, a subset are promoted to weekly points kept longer, a subset of those to monthly points kept longer still, and a subset to yearly points kept the longest. The scheme exists so that recent history is dense, with a point per day for quick recovery from a recent mistake, while older history is sparse, with a point per month or per year for the rare case of needing to reach back a long way. You get fine resolution where you are most likely to need it and economical coverage where you need only proof that a point existed.

Configuring the tiers well means mapping each tier to a real obligation. The daily tier answers operational recovery, the day-to-day "we broke something this week and need yesterday" case, so it should cover at least your typical detection-to-recovery span with margin. The weekly and monthly tiers answer the "we discovered last month that something went wrong weeks ago" case, common with slow-burning data problems that are not noticed immediately. The yearly tier answers compliance and legal hold, the "an auditor or a lawsuit needs a point from two years ago" case, and it is the tier most often set by obligation rather than by operational need. Setting each tier to its purpose, rather than setting one window and hoping, is what makes retention both sufficient and economical.

### How long should I keep VM backups?

Set retention per tier to a purpose: the daily tier long enough to cover detection and operational recovery with margin, the weekly and monthly tiers to catch problems noticed weeks later, and the yearly tier to whatever legal or regulatory obligation governs the data. Match each tier to a written requirement rather than picking one round number for everything.

The cost consequence of the tiers is direct and worth internalizing. Every promoted point that is retained longer is storage you pay for over that longer period, so a generous yearly tier on a high-churn machine is a recurring cost that compounds across the fleet. The right move is not to minimize retention blindly, which risks compliance, but to set each tier against its stated reason and remove tiers no obligation requires. A workload with no legal hold obligation does not need a yearly tier at all, and removing it is found money. A workload under a seven-year mandate needs the yearly tier and will cost what it costs, which is fine, because that cost is the price of an obligation you actually have rather than a habit you never examined.

## When backup is the wrong tool

Configuring Azure Backup correctly includes knowing the cases where backup alone is not the answer, because reaching for it reflexively in those cases produces a configuration that technically runs while leaving the real requirement unmet. The counter-reading to engage is the assumption that a backup, by itself, is a complete protection strategy for every workload. It is not, and naming the gaps is part of getting the configuration right.

The first gap is the recovery point objective a daily snapshot cannot meet. A workload that cannot afford to lose more than minutes of data is not served by a backup that runs once a day, no matter how perfectly the backup is configured, because the most recent recovery point may be hours old. The honest answer there is replication, which the [Azure Site Recovery configuration](/2023/07/10/configure-azure-site-recovery/) provides, layered alongside backup rather than instead of it. Backup still earns its place for point-in-time recovery from corruption or ransomware, but it cannot be the near-zero-loss mechanism, and a configuration that pretends otherwise is misconfigured at the level of strategy rather than settings.

The second gap is recovery time for a complex application. A single machine restores in a bounded time, but an application spread across many machines with ordering dependencies between them is not recovered simply by restoring each machine independently. The orchestration that brings a multi-machine application back in the right order belongs to a recovery plan, and the broader design of how the pieces fit lives in the [disaster recovery architecture on Azure](/2024/07/22/azure-disaster-recovery-architecture/) discussion. Backing up each machine correctly is necessary but not sufficient; the recovery sequence across machines is a separate problem backup does not solve on its own.

The third gap is the database that needs finer recovery than a machine snapshot provides. As noted with special workloads, an engine-native backup offers log-based, point-in-time recovery that a daily machine-level snapshot cannot match, and for a database where losing a day is unacceptable, the machine snapshot is a coarse complement to a finer engine backup rather than a substitute for it.

### Is configuring VM backup enough for disaster recovery?

Not by itself. Backup gives point-in-time recovery from corruption, deletion, or ransomware, but it cannot meet a near-zero data-loss objective or orchestrate a multi-machine application's recovery order. For those, pair backup with replication and a recovery plan. Backup is a necessary layer of a disaster recovery strategy, not the whole of one.

Knowing these limits does not diminish backup; it places it correctly. A well-configured backup is the foundation that protects against the most common loss events and the ones replication cannot help with, such as corruption that replicates faithfully to the secondary or a deletion that propagates. The mature posture treats backup as one deliberate layer in a stack, configured for what it does best and explicitly paired with other tools for what it cannot do, rather than overloaded with expectations it was never built to meet.

## Achieving application consistency in practice on Windows and Linux

Application consistency is the setting most worth getting right, and getting it right means understanding how the guest actually reaches it, because the mechanism differs sharply between the two operating systems and the difference is where Linux workloads quietly fall short.

On Windows, the platform leans on the Volume Shadow Copy Service, the built-in framework that coordinates a consistent point across the operating system and any applications that register as writers. When the backup extension requests a snapshot, it asks the shadow-copy framework to quiesce, and well-behaved applications such as the major database engines participate by flushing their buffers and reaching a clean transactional point. The result is an application-consistent capture with no scripting on your part, provided the application registers as a writer and the framework is healthy. The failure mode on Windows is a writer that is unhealthy or an application that does not register, in which case the capture degrades, so the verification is to confirm the writer reported success and the recovery point shows application consistency.

On Linux there is no universal equivalent, and this is the gap that surprises teams. To reach application consistency on a Linux machine, you supply a pre-script that runs before the snapshot to quiesce the application, freezing writes and flushing to a clean point, and a post-script that runs after the snapshot to thaw the application and resume normal operation. The platform invokes these scripts around the snapshot through a defined framework, but the scripts themselves are your responsibility, and a Linux database without working pre and post scripts reaches only file-system consistency no matter how healthy the agent is. This is the single most common reason a Linux database restores in a state that needs recovery: not a broken backup, but the absence of the scripts that would have quiesced it.

### Why is my Linux VM only getting file-system-consistent backups?

Linux has no built-in shadow-copy framework, so application consistency requires you to supply pre-script and post-script hooks that freeze and thaw the application around the snapshot. Without working scripts, the capture reaches only file-system consistency. Provide the scripts, then confirm the consistency level on a real recovery point and rehearse a restore to prove they ran.

The practical discipline for both operating systems is identical even though the mechanism differs: never assume consistency, always confirm it on an actual recovery point, and rehearse a restore of the specific workload so you prove not just that a point exists but that what it captured opens cleanly. A Windows team confirms the shadow-copy writers participated; a Linux team confirms the scripts ran and the database opens without recovery. Both teams treat a consistency downgrade as a fault to fix rather than a warning to dismiss, because the whole value of application consistency is realized only at restore time, and restore time is the worst moment to learn it was never actually achieved.

## Selective disk backup and special workloads

Not every disk on a machine deserves the same treatment, and a one-size policy across all disks both wastes money and occasionally protects the wrong things. Selective disk backup lets you include or exclude individual data disks from a machine's protection, and used deliberately it sharpens both cost and recoverability. A disk that holds a reproducible cache, scratch space for a batch process, or content that is a copy of an authoritative source elsewhere does not need a recovery point, and excluding it trims the storage consumed and the protected footprint. The discipline is to make exclusion a documented, visible decision rather than a silent gap, because a teammate who assumes the whole machine is protected will be unpleasantly surprised when a restore brings back everything except the disk that mattered.

Special workloads carry their own caveats worth knowing at configuration time. A machine running a large transactional database may benefit from a backup approach tuned to the database engine itself rather than relying solely on the machine-level snapshot, because engine-native backup can offer finer-grained recovery points and log-based recovery that a daily machine snapshot cannot. The machine-level backup and the database-native backup are not mutually exclusive; many designs run both, the machine snapshot for whole-machine recovery and the database backup for fine-grained, point-in-time database recovery. A machine with very large disks may bump against the practical realities of how long a full-machine restore takes, which is exactly the kind of thing the setup-time rehearsal exposes, since timing a restore of a large machine tells you whether your recovery time objective is realistic before an incident tests it for you.

### Can I back up only some disks on a VM to save money?

Yes. Selective disk backup includes or excludes individual data disks, so you can leave out disks holding reproducible or scratch data and pay only to protect what matters. Document every exclusion clearly, because an excluded disk has no recovery point, and a teammate assuming full-machine protection will be surprised when a restore returns everything except the omitted disk.

The thread connecting selective backup, special-workload handling, and the consistency mechanics above is that correct configuration is workload-aware. A blanket policy applied uniformly will over-protect the trivial machines, under-protect the demanding ones, and miss the engine-specific recovery that a database really needs. Matching the configuration to what each workload actually requires is more work at setup time and far less work, and far less risk, at recovery time.

## The verification step that proves it worked

This is the section the whole article points at. Everything before it is preparation; this is where the tested-restore rule turns a configuration into a recovery capability. The verification is not "did the job succeed" but "can I produce a working machine, disk, or file from a recovery point, and is what comes back actually usable." Those are different questions, and only the second one matters when a real incident arrives.

Azure Backup offers three restore shapes for a virtual machine, and rehearsing the right one is part of the verification. You can restore a full machine, creating a new machine from the recovery point. You can restore individual disks, attaching them to an existing or new machine, which is faster when the operating system is fine and only data is lost. And you can restore individual files through file recovery, which mounts the recovery point as a drive and lets you copy back exactly what was deleted without rebuilding anything. The right rehearsal mirrors the failure you actually fear. If your nightmare is a deleted folder, rehearse file recovery; restoring a whole machine to prove you can retrieve one folder wastes hours and proves the wrong thing.

A full-machine restore from the command line consumes the recovery point identifier you listed earlier and produces the restored disks, which you then use to build the recovered machine.

```bash
# Capture a recovery point ID from the earlier list, then restore disks
RP_ID="<recovery-point-id-from-the-list>"
STORAGE_ACCT="strestorestaging01"

az backup restore restore-disks \
  --resource-group "$RG" \
  --vault-name "$VAULT" \
  --container-name "$VM" \
  --item-name "$VM" \
  --rp-name "$RP_ID" \
  --storage-account "$STORAGE_ACCT" \
  --restore-to-staging-storage-account true \
  --backup-management-type AzureIaasVM
```

File-level recovery takes a different and often faster path. It generates a script that, when run on a machine with network access to the recovery point, mounts the point as a local volume so you can browse and copy files directly.

```bash
# Provision the file-recovery mount for a recovery point
az backup restore files mount-rp \
  --resource-group "$RG" \
  --vault-name "$VAULT" \
  --container-name "$VM" \
  --item-name "$VM" \
  --rp-name "$RP_ID" \
  --backup-management-type AzureIaasVM
```

The command returns a script and a password; running the script mounts the recovery point, you copy back the lost files, and then you unmount the point to release it. The whole cycle for a handful of files is minutes, which is exactly why file recovery exists and why a team that only ever rehearses full-machine restores will reach for the slow tool under pressure.

### How do I verify a backup is actually recoverable?

Trigger an on-demand backup, then perform a real restore from it, matching the restore shape to the failure you fear: file recovery for deleted data, disk restore for a damaged operating system, full-machine restore for a destroyed machine. Confirm the restored item opens and functions. A job marked successful proves nothing until a restore has been run and the result verified.

Verification is not a one-time event at setup. The configuration drifts, the workload changes, the guest agent ages, and a consistency level that was application-consistent in March can be silently downgraded by June. The practice that keeps the tested-restore rule honest over time is a recurring restore drill: on a schedule, pick a protected machine, perform a restore, and confirm the result. This is precisely the kind of muscle that decays without exercise, and rehearsing it on a cadence is the only way to know the capability is still there when an incident demands it. VaultBook is built for this rehearsal; its hands-on Azure labs let you stand up a vault, a policy, and a protected machine in a sandbox and run the full restore cycle end to end without touching production, and its tested command and template library gives you the exact CLI, PowerShell, and Bicep sequences for each restore shape so the rehearsal matches what you will run for real. You can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to practice the vault build and every restore path until the sequence is reflexive.

## A worked end-to-end recovery, from incident to verified machine

Reading about restore shapes is not the same as having walked one, so here is a complete recovery played out as it would happen, because the worth of the configuration is only ever visible in the recovery it enables. Picture a production application machine, protected nightly under a deliberate policy, with geo-redundancy and cross-region restore enabled at vault creation. On a Tuesday morning, an automated configuration change goes wrong and corrupts the application's data directory. The application will not start. The machine is reachable, the operating system is healthy, but the data is gone or unusable. This is a data-loss incident, not a machine-loss incident, and recognizing that shapes everything that follows.

The first decision is the restore shape, and the worked-restore discipline pays off immediately. The machine itself is fine; only a data directory is corrupt. A full-machine restore would recreate an entire machine to recover one directory, consuming an hour or more and forcing a cutover to the new machine. A file-level recovery, by contrast, can mount a clean recovery point and copy the data directory back into the existing, still-running machine in minutes. Because the team rehearsed file recovery rather than only ever running full-machine restores, the right tool is reflexive. They reach for file recovery.

The second step is choosing the recovery point. The corruption happened during a known change window this morning, so the right recovery point is the most recent one taken before that window, last night's scheduled snapshot. Listing the recovery points shows their timestamps and, critically, their consistency levels. The team confirms that last night's point is application-consistent, which matters because the data directory belongs to a stateful application; a crash-consistent point might restore files mid-write. With an application-consistent point selected, they provision the file-recovery mount.

```bash
# List points to find last night's application-consistent recovery point
az backup recoverypoint list \
  --resource-group "$RG" \
  --vault-name "$VAULT" \
  --container-name "$VM" \
  --item-name "$VM" \
  --backup-management-type AzureIaasVM \
  --query "[].{name:name, time:properties.recoveryPointTime, type:properties.recoveryPointType}" \
  --output table

# Provision the file-recovery mount for the chosen point
az backup restore files mount-rp \
  --resource-group "$RG" \
  --vault-name "$VAULT" \
  --container-name "$VM" \
  --item-name "$VM" \
  --rp-name "$RP_ID" \
  --backup-management-type AzureIaasVM
```

The mount command returns a downloadable script and a password. The team runs that script on a recovery workstation with network reach to the recovery point, which mounts the point as a local volume. They browse to the data directory on the mounted volume, confirm it contains the clean, pre-corruption state, and copy it back over the corrupt directory on the production machine. They restart the application, which now starts cleanly because the data is coherent and complete. Finally, they unmount the recovery point to release the resources the mount held.

```bash
# After copying files back, release the recovery mount
az backup restore files unmount-rp \
  --resource-group "$RG" \
  --vault-name "$VAULT" \
  --container-name "$VM" \
  --item-name "$VM" \
  --rp-name "$RP_ID" \
  --backup-management-type AzureIaasVM
```

The whole incident, from recognizing the data loss to a verified working application, takes minutes rather than hours, and the reason it does is not luck. It is that the configuration was built for recovery: the consistency level was right because a healthy agent was a prerequisite, the recovery point existed because the schedule and an early on-demand backup guaranteed it, and the team knew which tool to reach for because they had rehearsed it. Now contrast the alternative timeline. A team that never rehearsed reaches for the only restore they know, the full-machine restore, spins up a new machine over the course of an hour, then has to re-point networking and re-validate the whole machine, turning a minor data incident into a major outage. The configuration was nominally identical. The preparation was not.

### How do I pick the right recovery point to restore from?

Choose the most recent recovery point taken before the event that caused the loss, and confirm its consistency level matches the workload. For a stateful application or database, restore from an application-consistent point; restoring from a crash-consistent point risks files captured mid-write. The recovery point list shows both the timestamp and the consistency type for exactly this decision.

This worked recovery also surfaces why the verification at setup time and the periodic drill thereafter are not the same exercise repeated. The setup-time verification proves the pipeline can produce a working restore at all. The periodic drill proves it still can, after months of drift, agent aging, and workload change, and it keeps the team's hands trained on the exact sequence above so that under real pressure they execute rather than improvise.

## Choosing the restore shape: a decision walkthrough

The three restore shapes are not interchangeable, and choosing among them quickly under pressure is a skill the rehearsal builds. The decision turns on one question asked first and a second question asked to confirm, and walking it deliberately now means executing it reflexively later.

The first question is what was actually lost. If the loss is a file or a folder, with the operating system and the rest of the data intact, file-level recovery is almost always right, because it returns exactly the lost items into the still-running machine in minutes without touching anything else. Reaching for a full-machine restore here is the classic wrong move, trading a five-minute fix for a multi-hour rebuild and a cutover that introduces its own risk. If the loss is the data on one or more disks, with the operating system fine, disk restore is the candidate, because swapping recovered disks back is faster than recreating the whole machine and preserves the machine's identity and configuration. If the loss is the machine itself, whether it was deleted, made unbootable, or has to be reconstituted in another region, the full-machine restore is the tool, because there is nothing left to restore into.

The second question confirms the consistency requirement. For any stateful workload, especially a database, the chosen recovery point must be application-consistent, because a crash-consistent point risks files captured mid-write that restore into a state needing recovery. This is where the recovery point list's consistency column earns its place: it lets you pick not just the right time but the right quality of point. A file recovery of a database's data files from a crash-consistent point can hand back files the engine will not open cleanly, so the consistency check is not optional even when the restore shape is correct.

### Which restore option should I use for a deleted file versus a dead machine?

Use file-level recovery for a deleted file or folder when the machine is otherwise fine, because it returns the items in minutes without a rebuild. Use disk restore when data disks are damaged but the operating system is healthy. Reserve the full-machine restore for a machine that is deleted, unbootable, or must be rebuilt elsewhere.

There is a third consideration that the rehearsal surfaces and the documentation rarely emphasizes: time. Each shape has a different recovery time, and the only honest way to know yours is to have timed it. File recovery of a small set of items is minutes. Disk restore scales with the disk size being swapped. Full-machine restore scales with the total footprint and adds the post-restore work of validating and re-pointing the machine. A team that has timed each shape on its own machines can quote a real recovery time for each failure type, which is exactly the number the business asks for and exactly the number an untested configuration cannot provide. The decision walkthrough and the timing together turn recovery from an improvisation into a procedure, which is the entire point of configuring backup correctly in the first place.

## Cross-region restore and surviving a regional outage

A vault protects against the loss of a machine. It does not, by default, protect against the loss of the region the vault lives in. If the vault uses locally redundant or zone-redundant storage, every recovery point sits inside one region, and a regional event takes the machine and its recovery points together. Cross-region restore is the capability that closes that gap, and it is the clearest example of a setting you must choose at vault-creation time rather than retrofit later.

Cross-region restore builds on geo-redundant storage. With geo-redundancy, recovery points are replicated to the Azure paired region, and with the cross-region restore flag enabled, you gain the ability to trigger a restore in that paired region from the replicated points, on your own initiative, without waiting for Azure to declare a regional failover. That self-service property is the point: during a regional incident you do not want your recovery to depend on a platform-wide failover decision you do not control. You want to be able to bring the machine up in the paired region because you decided to.

The order-of-operations consequence is sharp. Geo-redundancy and the cross-region restore flag are vault-level properties, and once a vault holds recovery points, you generally cannot switch its redundancy. A vault created with locally redundant storage to save money is a vault that can never offer cross-region restore for the machines already in it; the only remedy is a new vault and a fresh protection history. This is why the setup checklist puts the redundancy decision near the top and flags the default as a trap. The cheap choice at creation is the expensive choice during a regional outage.

### Can I restore a VM backup in a different region?

Yes, if the vault uses geo-redundant storage and the cross-region restore flag was enabled. Recovery points replicate to the Azure paired region, and you can trigger a restore there yourself during a regional incident. Both properties must be set at or near vault creation, because vault redundancy cannot be changed once recovery points exist.

Cross-region restore is one half of a regional-resilience story, and it is worth being precise about where it sits relative to the heavier machinery. Azure Backup with cross-region restore gives you point-in-time recovery in the paired region, which is the right tool when the goal is to retrieve a known-good state after a loss. It is not continuous replication, and it does not give you a near-zero recovery point for a machine you cannot afford to lose more than seconds of. For that, the replication-based approach in [configure Azure Site Recovery](/2023/07/10/configure-azure-site-recovery/) is the sibling capability, and the broader question of how backup and replication fit into a coherent regional design belongs to the [disaster recovery architecture on Azure](/2024/07/22/azure-disaster-recovery-architecture/) discussion. Backup answers "get me back a clean copy"; replication answers "fail me over with almost nothing lost." A complete design usually uses both, and confusing one for the other is a recurring and costly mistake.

## The common misconfigurations and their symptoms

Six failure patterns account for most of the backup-related incidents engineers actually report, and each one traces directly to a setup choice. Recognizing the symptom and walking it back to the choice is the fastest route to a fix, and configuring against it in the first place is faster still.

The first pattern is the untested restore. The symptom is a recovery that fails or stalls during a real incident, often with an error the team has never seen, because the restore path was never exercised. The protected-instance count was healthy, the jobs were green, and confidence was high right up to the moment recovery was needed. The setup choice that prevents it is the on-demand backup and rehearsed restore at configuration time, repeated as a periodic drill. This is the tested-restore rule in its purest form, and it is the single highest-value habit in the entire discipline.

The second pattern is the inconsistent database restore. The symptom is a restored database that will not open, or that opens only after a lengthy recovery, or that opens with data the application reports as corrupt. The cause is almost always a crash-consistent or file-system-consistent snapshot used for a workload that needed application consistency, frequently because a stale guest agent silently downgraded the capture. The setup choice is to confirm the consistency level after enabling protection and to monitor for downgrades thereafter rather than trusting the green job.

The third pattern is the wrong restore shape. The symptom is an hours-long full-machine restore performed to retrieve a single deleted file or folder, turning a five-minute problem into a half-day outage. The cause is a team that only knows the full-machine restore because it is the only path it ever rehearsed. The setup choice is to rehearse file-level recovery and disk restore as well, so the right tool is reflexive under pressure.

The fourth pattern is the trapped recovery point during a regional outage. The symptom is a regional incident where the machine is down and every recovery point is in the same dead region, leaving no recovery path until the region returns. The cause is a vault on locally redundant or zone-redundant storage with cross-region restore never enabled. The setup choice is geo-redundancy and the cross-region restore flag at vault creation, because neither can be added afterward.

The fifth pattern is the compliance-short retention. The symptom is an audit that asks for a recovery point from eleven months ago and finds the oldest point is thirty-five days old. The cause is a default retention window accepted without checking the obligation. The setup choice is to set the daily, weekly, monthly, and yearly tiers against the written requirement and record that requirement with the policy.

The sixth pattern is the cost creep. The symptom is a monthly bill that climbs steadily without a corresponding change in workload, traced eventually to retention that grew generous and storage that accumulated. The cause is retention set longer than any requirement demands, multiplied across a fleet. The setup choice is retention matched to obligation rather than to a vague sense that more is safer, and a periodic review of what each policy actually costs.

### Why does my restored database open in an inconsistent state?

The recovery point was crash-consistent or file-system-consistent rather than application-consistent, so the database's in-memory state was not flushed to a clean point before the snapshot. This commonly happens when a stale guest agent silently downgrades the capture. Confirm the consistency level on the recovery point and treat any downgrade as a fault.

Diagnosing these patterns under pressure is its own skill, separate from configuring against them in advance, and it is worth rehearsing deliberately. ReportMedic complements the VaultBook labs here: its scenario-based troubleshooting drills put you in front of a failed or inconsistent restore and ask you to work back to the setup choice that caused it, which is exactly the reasoning an incident demands. You can [work through scenario-based recovery drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) to build the diagnostic reflex alongside the hands-on configuration practice, so that when a restore misbehaves you are walking a path you have walked before rather than improvising.

## Securing the backup configuration against deliberate attack

The threat model for backup has changed, and a configuration built only against accidental loss is dangerously incomplete. Ransomware operators understand that a victim with good backups will not pay, so the modern attack pattern includes finding and destroying the backups before triggering the encryption. A backup configuration that any compromised administrative credential can erase in seconds is a configuration that does not survive the attack it most needs to survive. Hardening it is part of configuring it correctly, not an optional extra for the paranoid.

The first hardening layer is soft delete. With soft delete enabled, a deleted recovery point is not gone immediately; it is retained for a recovery window during which it can be brought back, even though someone, or something, asked for its deletion. That window is the difference between an attacker who can instantly destroy your recovery ability and an attacker who triggers a deletion that you can undo. Soft delete turns destruction into a delay, and the delay buys the time to notice and respond. It is enabled by default on the vault for exactly this reason, and disabling it to simplify cleanup is one of the quieter ways to reopen the hole it closes.

The second layer is immutability. An immutable vault locks recovery points so they cannot be modified or deleted before their retention expires, which closes a subtler attack than outright deletion. A sophisticated actor who cannot delete points may instead try to shorten their retention so they expire on their own, achieving the same result without an obvious delete operation. Immutability removes that path by making the retention itself unalterable downward for the locked period. Where the workload's risk justifies it, an immutable, locked vault is the strongest posture, with the trade-off that you lose the flexibility to shorten retention even when you legitimately want to.

The third layer is access control, applied with the principle of least privilege and reinforced by multi-user authorization where available. The fewer identities that can alter the backup configuration, the smaller the blast radius of any one compromised credential, and multi-user authorization adds a second-approver requirement for the most destructive operations, so that a single stolen credential cannot by itself disable protection or purge points. Combining narrow role assignments with a second-approver gate on critical actions means an attacker needs to compromise more than one identity to reach the backups, which is a meaningfully higher bar.

### How do I stop ransomware from destroying my Azure backups?

Enable soft delete so deleted recovery points are retained for a recovery window and can be restored, add vault immutability so retention cannot be shortened to force early expiry, and apply least-privilege access with multi-user authorization so destructive operations need a second approver. Together these turn instant destruction into a delayed, multi-step action you can detect and reverse.

These three layers compose. Soft delete defeats the blunt delete, immutability defeats the retention-shortening trick, and access control with multi-user authorization raises the cost of reaching the configuration at all. None of them is exotic to configure, and all of them belong in the setup of any machine whose loss would matter, because the attack that needs them is precisely the attack that disables an unhardened backup first.

## Monitoring and operating the configuration over time

A backup configuration is not a thing you set once and forget, because the conditions it depends on drift. Agents age, workloads change their write patterns, machines join and leave the fleet, and a consistency level that was application-consistent at setup can quietly degrade. Operating the configuration well means watching the right signals and acting on the right ones, and the platform gives you a consolidated place to do it.

The Backup center is the single pane for the fleet, showing protected items, recent jobs, and the health of the protection across vaults. The job history is the first signal, but reading it correctly means looking past the binary success status to the detail, especially the consistency level of completed jobs, because that is where a silent downgrade hides behind a green result. A job that succeeded but produced a file-system-consistent point for a database is a problem the success column will never show you, so the operational discipline is to inspect the consistency type, not just the pass or fail.

Alerts are the second signal, and the trap is alerting only on failures. A failed job is loud and gets attention. The dangerous condition is the quiet one: a job that succeeds at a lower consistency than required, a machine that has stopped being protected because someone removed it from the policy, or a recovery point chain that has not produced a fresh point in longer than the schedule should allow. Configure alerts for these conditions, not only for outright failures, so the silent gaps surface before an incident reveals them.

Backup reports are the third signal, and they answer the questions a green dashboard cannot: which machines are consuming the most storage, whether retention is trending in a way that explains a rising bill, and whether any protected item is approaching a limit. Reviewing reports on a cadence is how the cost-creep pattern gets caught early, while it is still a trend rather than a surprise on an invoice. Pair that review with the periodic restore drill, and the operational loop is complete: the drill proves recoverability still works, the consistency inspection proves the captures are still trustworthy, the alerts catch the silent gaps, and the reports keep cost and retention honest.

### How do I know if a protected VM has silently stopped being backed up?

Do not rely on the absence of failure alerts, because a machine removed from a policy or one whose recovery point chain has gone stale may raise no failure at all. Use the Backup center to confirm each protected item has a recent recovery point, and configure alerts on stale or missing points, not only on failed jobs, so a quiet gap surfaces before you need to recover.

## What drives the cost, and how to keep it deliberate

Backup cost has two main components, and understanding them is what lets you set retention against obligation without flinching at the bill. The first component is the protected-instance charge, levied per protected machine and scaled by the size of the machine's used disk footprint. The second is the storage consumed by the recovery points themselves, which depends on how much data changes between snapshots and how long each point is retained. The redundancy choice multiplies the storage component: geo-redundant storage costs more than zone-redundant, which costs more than locally redundant, because it keeps more copies in more places.

The lever that moves cost most is retention, because storage accumulates with every point kept and every additional day of keeping it. This is why retention set to a vague "longer is safer" is a slow financial leak, and why retention set to a written obligation is both compliant and economical. A workload that genuinely owes seven years of yearly points will cost what it costs; a workload that kept seven years out of habit is paying for an obligation it does not have. The second lever is the redundancy choice, where the right move is to pay for geo-redundancy where a regional outage must be survivable and not to pay for it where it is not. The third, smaller lever is the change rate, which you influence only indirectly by how the workload writes, but which explains why a high-churn database costs more to protect per gigabyte than a static file server.

The discipline that keeps cost deliberate is the same discipline that keeps retention compliant: tie every retention tier to a stated reason, review the tiers periodically against the actual bill, and remove retention that no obligation requires. This is the inverse of the cost-creep pattern, and it is worth pairing with the broader cost hygiene that the [Azure VM auto-shutdown configuration](/2023/04/10/configure-azure-vm-autoshutdown/) brings to compute spend, since the same instinct that leaves a development machine running overnight tends to leave backup retention generous beyond need.

### What drives the cost of Azure VM backup?

Two things: a protected-instance charge that scales with the machine's used disk size, and the storage the recovery points consume, which grows with the change rate between snapshots and the length of retention. The vault's redundancy multiplies the storage cost. Retention is the lever with the largest effect on the bill.

One further cost lever is worth naming because it is easy to overlook: the storage tier the recovery points live in. Long-retention points that exist only to satisfy a compliance hold and are unlikely to ever be restored do not need to sit in the most expensive, fastest-access storage, and where the platform offers a lower-cost archive-style tier for such points, moving them there cuts the cost of the obligation without abandoning it. The trade-off is access latency, since retrieving an archived point is slower than retrieving a hot one, which is exactly the right trade for a point you keep for an auditor rather than for operational recovery. The discipline is to match the storage tier to the point's purpose just as you matched the retention tier to its obligation: hot, fast storage for the recent operational points you might actually restore in a hurry, and cheaper, slower storage for the long-tail compliance points you keep but rarely touch. Read against the broader cost hygiene the auto-shutdown habit brings to compute, the pattern is identical, which is that deliberate matching of resource to need beats a single blanket setting every time, on the backup bill as much as on the compute bill.

## How to make the configuration repeatable as code

Enabling protection one machine at a time in the portal is fine for learning and untenable for a fleet. It does not scale, it drifts as machines come and go, and it leaves the configuration as a series of clicks that nobody can audit or reproduce. The mature form of a backup configuration is expressed as code, so that a vault, a policy, and the binding of machines to that policy are defined declaratively and applied the same way every time. This is also where backup configuration connects to the wider operational model in the [Azure Virtual Machines complete engineering guide](/2022/01/03/azure-virtual-machines-complete-guide/), which treats the machine and its supporting resources as a single deployable unit rather than a thing you assemble by hand.

A Bicep module captures the vault and policy cleanly. The sketch below shows the shape; treat the exact resource API versions and property names as values to confirm against the current Bicep reference, since they are revised regularly.

```bicep
param location string = resourceGroup().location
param vaultName string = 'rsv-prod-eastus'

resource vault 'Microsoft.RecoveryServices/vaults@2023-04-01' = {
  name: vaultName
  location: location
  sku: {
    name: 'RS0'
    tier: 'Standard'
  }
  properties: {}
}

resource policy 'Microsoft.RecoveryServices/vaults/backupPolicies@2023-04-01' = {
  parent: vault
  name: 'prod-daily-35d-12m'
  properties: {
    backupManagementType: 'AzureIaasVM'
    schedulePolicy: {
      schedulePolicyType: 'SimpleSchedulePolicy'
      scheduleRunFrequency: 'Daily'
      scheduleRunTimes: [
        '2023-07-03T02:00:00Z'
      ]
    }
    retentionPolicy: {
      retentionPolicyType: 'LongTermRetentionPolicy'
      dailySchedule: {
        retentionDuration: {
          count: 35
          durationType: 'Days'
        }
      }
    }
  }
}
```

Defining the vault and policy as code is half the story. The other half is binding machines to the policy without per-machine clicks, and for a fleet the cleanest mechanism is policy-driven assignment, where Azure Policy detects machines that match a scope and enables backup on them automatically under the named protection policy. That turns "did someone remember to enable backup on the new machine" from a hope into an enforced invariant, which is exactly the kind of guarantee a fleet needs. Express the vault, the backup policy, and the assignment together, keep them in source control, and the configuration becomes reproducible, auditable, and resistant to the drift that per-machine setup invites.

### How do I make VM backup repeatable across a fleet?

Express the vault and backup policy as code with Bicep or an equivalent template, then bind machines to the policy through Azure Policy auto-enablement rather than enabling each machine by hand. That makes backup an enforced invariant for matching machines, eliminates drift, and keeps the configuration auditable in source control.

## Handling drift, decommissioning, and the configuration lifecycle

A backup configuration has a lifecycle beyond its initial setup, and the moments that go wrong are the transitions: a machine resized, a policy changed, a workload retired, a vault migrated. Each transition can silently break what the setup got right, so configuring backup correctly includes planning for how the configuration changes over time rather than treating it as frozen.

Drift is the first lifecycle problem. A machine that grows new data disks does not automatically protect them if the policy was set with selective disk backup and the new disks were never added, so a disk created months after setup can sit unprotected while the dashboard shows the machine as backed up. A machine moved between resource groups or subscriptions can lose its protection association if the move is not handled with backup in mind. The defense is the same enforcement that prevents per-machine drift at setup: policy-driven protection that re-evaluates machines against a scope, so a machine that drifts out of compliance is caught and corrected rather than quietly slipping through. Pairing that enforcement with the monitoring discipline, where alerts fire on stale or missing recovery points rather than only on failures, closes the loop so drift surfaces as a signal instead of a surprise at recovery time.

Policy change is the second lifecycle problem, and it is subtle because the change can be well-intentioned. Tightening retention on a shared policy to control cost shortens the recoverable history for every machine bound to it, not just the one whose cost prompted the change. Loosening a schedule to reduce performance impact lengthens the recovery point objective for everyone on the policy. Because a policy is shared, every change to it is a change to a group, so the discipline is to reason about the full set of machines a policy governs before editing it, and to split a policy when one machine's needs diverge rather than bending the shared policy and affecting the rest. Expressing policies as code helps here, because a change becomes a reviewable diff against a known set of bound machines rather than an untracked edit in a portal blade.

Decommissioning is the third lifecycle problem and the one most often fumbled. Retiring a workload is not the same as deleting its recovery points, and the two should be deliberate, separate decisions. Stopping protection halts new recovery points but, depending on how you stop it, may retain the existing ones, which continue to consume storage and cost until explicitly removed. That retention is sometimes exactly right, because a decommissioned workload may still owe a compliance retention obligation, and deleting its points the day the machine retires would violate the very rule the yearly tier existed to satisfy. So the decommissioning decision is two questions asked in order: does any obligation require keeping these points, and if not, are we confident enough in that answer to delete them. Answering both deliberately is what keeps decommissioning from either leaking cost on points no obligation needs or destroying points an obligation still demands.

### What happens to my backups and their cost when I retire a VM?

Retiring or deleting a machine does not delete its recovery points; they remain in the vault under the policy's retention and keep consuming storage until you explicitly remove them. Decide deliberately whether a compliance obligation requires keeping them. If not, stop protection and delete the points to halt the cost; if so, retain them until the obligation expires.

The lifecycle view reframes the whole configuration from a one-time setup into an operated capability. The setup gets the vault, policy, consistency, and verification right. The lifecycle discipline keeps them right as machines, policies, and obligations change, through enforced protection that resists drift, careful reasoning about shared-policy changes, monitoring that catches silent gaps, periodic restore drills that prove recoverability survives the drift, and deliberate decommissioning that neither leaks cost nor breaks compliance. A configuration treated as frozen decays; a configuration treated as a lifecycle stays a recovery capability for as long as the workload exists.

## The closing verdict

Configuring Azure Backup for a virtual machine is not hard. Configuring it so the machine is recoverable, rather than merely protected, takes a handful of deliberate decisions that the defaults will make badly on your behalf if you let them. Build the vault with the redundancy and cross-region restore you will need, because you cannot add them later. Define a policy whose schedule and retention match the workload and the written obligation, not a round number. Confirm the snapshot reaches the consistency the workload requires, and treat a silent downgrade as a fault rather than a footnote. Choose the restore shape that matches the failure you fear, and rehearse it. Express the whole thing as code so it survives a fleet and an audit.

Above all, hold the tested-restore rule. A green job tells you the pipeline can read your disks. Only a verified restore tells you that you can get a working machine, disk, or file back, and how long it takes, and whether what comes back is usable. The configuration is not finished when the first backup succeeds. It is finished when the first restore succeeds and you have seen it with your own eyes. Treat recoverability as the goal and the backup as the means, and the worst day becomes a recoverable one.

## Frequently Asked Questions

### Q: Do I need to install a backup agent inside an Azure VM?

For the snapshot itself, no separate backup agent is required, because Azure Backup takes the disk snapshot at the infrastructure layer without software you install for that purpose. What you do need is a healthy Azure VM Agent already present in the guest, because the extension that reaches application consistency rides on top of it. The distinction matters: the agentless snapshot will still run if the VM Agent is missing or stale, but it cannot quiesce applications, so the capture downgrades to file-system-consistent or crash-consistent without raising an obvious alarm. If your workload needs the database to restore cleanly, treat a healthy VM Agent as a prerequisite, not an optional extra, and verify the consistency level on the resulting recovery point rather than assuming the absence of an installed agent means the snapshot is fine.

### Q: How often should an Azure VM be backed up?

Frequency is a function of how much data you can afford to lose, expressed as your recovery point objective. A daily snapshot means the most you can lose is roughly a day of changes, which suits many general workloads. A database where losing a day is unacceptable needs either more frequent backup, where the policy supports it, or a replication-based approach layered alongside backup for the near-zero loss window. The mistake is picking a frequency by habit rather than by stated tolerance. Decide the acceptable loss window first, then set the schedule to satisfy it, and remember that more frequent snapshots increase both the storage consumed and any performance impact from the quiesce, so the right frequency is the least frequent one that still meets the loss tolerance.

### Q: What is the difference between Azure Backup and Azure Site Recovery for a VM?

They solve different problems and are often wrongly treated as substitutes. Azure Backup produces point-in-time recovery points you restore from after a loss, with recovery points spaced by your schedule, so the recovery window is measured in hours or days depending on the policy. Azure Site Recovery continuously replicates a machine to another region so you can fail over with a recovery point measured in seconds or minutes. Backup answers "give me back a clean copy from a known time"; Site Recovery answers "fail me over now with almost nothing lost." A workload that cannot tolerate losing more than seconds needs replication, while one that mainly needs protection against deletion, corruption, or ransomware is well served by backup. Many production designs use both, with backup for point-in-time recovery and Site Recovery for regional failover.

### Q: Can I change a vault's storage redundancy after I have started backing up?

Generally no. The storage redundancy of a Recovery Services vault, whether locally redundant, zone-redundant, or geo-redundant, is fixed once the vault contains recovery points. This is why the redundancy decision belongs at vault creation, before any protection is enabled. If you created a vault with locally redundant storage to save money and later need cross-region restore, which requires geo-redundancy, the remedy is a new vault with the correct redundancy and a fresh protection history, not a property change on the existing vault. Plan the redundancy against the regional resilience you will need from the start, because the cheap choice made early becomes the expensive constraint discovered during a regional incident, when it is far too late to change it.

### Q: How long does it take to restore an Azure VM from backup?

It depends heavily on the restore shape and the data size. A file-level recovery for a few deleted files completes in minutes because it mounts the recovery point and copies only what you need. A disk restore that swaps damaged data disks back into a running machine is faster than rebuilding from scratch. A full-machine restore that recreates the machine from the recovery point is the slowest, scaling with the total disk footprint. The number that matters is your recovery time objective, and the only honest way to know whether your configuration meets it is to rehearse the relevant restore shape and time it. A restore you have never run has an unknown duration, which is the same as having no defensible recovery time at all.

### Q: Why does my backup job succeed but show a consistency warning?

A success with a consistency warning means the snapshot completed but reached a lower consistency level than application-consistent, typically because the guest agent could not quiesce the applications. The job is marked successful because the disk data was captured; the warning is telling you the capture is crash-consistent or file-system-consistent rather than transactionally clean. For a stateless machine this may be acceptable. For a database, it is a quiet failure waiting to surface at restore time as a database that will not open cleanly. Investigate the agent health, confirm the workload is one the agent can quiesce, and resolve the cause rather than dismissing the warning, because a backup that succeeds with a downgrade is exactly the configuration that betrays you when you finally need to recover.

### Q: Can I exclude specific disks from a VM backup?

Yes, selective disk backup lets you include or exclude individual data disks from a machine's protection, which is useful when a disk holds scratch data, a temporary cache, or content reproduced from elsewhere that does not need a recovery point. Excluding such a disk reduces both the storage consumed and the cost. The caution is to be deliberate about what you exclude, because a disk left out of the policy has no recovery point at all, and a teammate who assumes the whole machine is protected can be surprised during recovery. Document which disks are excluded and why, ideally in the policy's tags or naming, so the exclusion is a visible decision rather than a silent gap someone discovers mid-incident.

### Q: What permissions does a service principal need to configure VM backup?

The configuration splits along least-privilege lines. Creating and managing the vault and policies requires the Backup Contributor role, which grants full management of the backup configuration within its scope. Triggering backups and restores without the ability to alter policies is covered by the Backup Operator role, which is the right grant for automation that runs jobs but should not redefine protection. The narrower Backup Reader role allows monitoring without any change rights. For automation that enables protection on new machines, granting the operator-level rights rather than full contributor rights follows the principle of least privilege, and reserving the contributor role for the smaller set of identities that genuinely manage policy keeps the blast radius of a compromised credential small.

### Q: Will backing up a VM affect its performance?

The disk snapshot itself is lightweight, but the quiesce that produces an application-consistent capture briefly pauses application writes so the on-disk state reaches a clean point. For most workloads this pause is short and unnoticeable. For a machine under heavy write load or running a sensitive batch job at the snapshot time, the pause can be felt, which is why the snapshot schedule should target a quiet window rather than a peak. The transfer of snapshot data to vault storage happens in the background and competes minimally for resources. If you observe a performance impact, the usual culprit is a snapshot scheduled during a busy period, and moving the schedule to a genuinely quiet window resolves it without sacrificing consistency.

### Q: How do I restore just a few files instead of the whole machine?

Use file-level recovery. Provision the file-recovery mount for the chosen recovery point, which generates a script and a password. Run that script on a machine with network access to the recovery point, and it mounts the point as a local volume you can browse like an ordinary drive. Copy back the specific files or folders you lost, then unmount the recovery point to release it. The whole cycle for a small set of files takes minutes, which is dramatically faster than restoring an entire machine to retrieve a single folder. Rehearsing this path is worthwhile precisely because the temptation under pressure is to reach for the full-machine restore you already know, turning a five-minute fix into a multi-hour outage for no reason.

### Q: Can I back up a VM that uses customer-managed encryption keys?

Yes, Azure Backup supports machines whose disks are encrypted, including those using customer-managed keys, and the recovery points preserve the encryption relationship so a restored machine remains encrypted. The configuration detail to get right is access: the backup and restore operations must be able to work with the key material, which means the relevant identity needs the appropriate access to the key vault holding the encryption key. A restore that fails with a key-access error almost always traces to a missing grant on the key, not to a backup problem. Confirm the key access as part of the setup and rehearse a restore of an encrypted machine specifically, because the encryption path adds a dependency that a restore of an unencrypted machine never exercises.

### Q: What happens to backups if I delete the protected VM?

Deleting the machine does not delete its recovery points. The protected item remains in the vault with its existing recovery points, retained according to the policy, which is exactly what you want when the deletion was an accident or an attack and you need to bring the machine back. To recover, you restore a full machine from one of the retained recovery points. This also means that stopping protection and deleting recovery points are separate, deliberate actions, so cost does not silently vanish when a machine is deleted; the retained points continue to consume storage until you explicitly remove them. If a machine is genuinely gone for good, stop protection and decide whether to retain or delete its points based on your obligation.

### Q: How do I protect backups against ransomware or malicious deletion?

The defenses are soft delete and immutability working together. Soft delete retains recovery points for a recovery window even after someone attempts to delete them, so a malicious actor with credentials cannot instantly erase your ability to recover. Immutability locks recovery points against modification or premature deletion for their retention period, which closes the gap where an attacker tries to shorten retention to force points to expire. Enable both where the workload's risk justifies it, and combine them with least-privilege access so that the identities able to alter backup configuration are few. The threat model for backup has shifted from accidental loss to deliberate attack, and a backup configuration that assumes only honest mistakes is a configuration an attacker will happily exploit.

### Q: Why is my first backup taking so long compared to later ones?

The initial backup is a full capture of the machine's used disk data, so it transfers the entire footprint to vault storage and naturally takes the longest. Subsequent backups are incremental, transferring only the blocks that changed since the previous recovery point, which is why they complete far faster and consume far less additional storage. A long first backup is expected behavior, not a fault. If later incremental backups are also slow, the likely causes are a high change rate on the machine, a constrained network path for the transfer, or contention during the snapshot window. The first backup's duration is also a useful planning signal, because it approximates the data volume a full-machine restore will have to move back in the other direction.

### Q: Should every machine use the same backup policy?

No, and forcing one policy onto every machine is a common over-simplification. Different workloads have different recovery point objectives, different retention obligations, and different consistency needs, so they warrant different policies. A high-value database with a regulatory retention mandate and a need for application consistency should not share a policy with a stateless web front end that can be rebuilt from an image. Group machines by their actual requirements, define a policy per group, and name each policy after the obligation it satisfies. The discipline of matching policy to workload is what keeps both cost and compliance honest, whereas a single blanket policy either over-protects cheap machines, wasting money, or under-protects important ones, creating risk.

### Q: Can I automate enabling backup on every new VM?

Yes, and for a fleet you should, because per-machine enablement drifts the moment someone forgets. Azure Policy can detect machines that match a defined scope and automatically enable backup on them under a named protection policy, turning "did someone remember to protect the new machine" into an enforced invariant. Combine the policy-driven assignment with vault and backup policy defined as code, keep all of it in source control, and the result is a backup posture that applies itself to new machines without manual intervention and resists the slow drift that hand-enablement invites. This is the difference between a backup configuration that depends on human diligence and one that is structurally guaranteed, and at fleet scale only the second kind holds up.

### Q: How do I confirm a recovery point reached application consistency?

After a backup completes, inspect the recovery point's consistency level rather than trusting the job's success status. The recovery point carries metadata indicating whether it is application-consistent, file-system-consistent, or crash-consistent, and that field is the authoritative answer for whether a database will restore cleanly. Make this check part of your setup verification and your ongoing monitoring, because the consistency level can silently drop over time as the guest agent ages or the workload changes. A configuration that was application-consistent when first built can degrade without any change to the policy, so the only reliable way to know is to look at the consistency level on actual recovery points on a recurring basis and alert on any downgrade.

### Q: Does Azure Backup work the same for Linux and Windows VMs?

The outer mechanics are identical: the same vault, the same policy structure, the same restore shapes apply to both. The difference is in how application consistency is achieved inside the guest. On Windows, the platform coordinates with the Volume Shadow Copy Service to quiesce applications. On Linux, application consistency relies on pre-script and post-script hooks you provide, which freeze and thaw the application around the snapshot, because there is no universal equivalent of the Windows shadow-copy mechanism. So a Linux database that needs application consistency requires you to supply working pre and post scripts, and a Linux machine without them will reach only file-system consistency. Confirm the scripts run correctly by checking the consistency level on a real recovery point, and rehearse a restore of the Linux workload specifically to prove the scripts did their job.
