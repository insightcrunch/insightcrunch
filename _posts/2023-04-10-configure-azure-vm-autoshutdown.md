---
layout: post
title: "Configure Azure VM Auto-Shutdown Correctly"
page_title: "Azure VM Auto-Shutdown: How to Configure the Schedule, Time Zone, Deallocation, Notification, and Auto-Start Correctly"
date: 2023-04-10
categories: ["Technology"]
tags: ["Azure", "Virtual Machines", "Cost Management", "DevOps", "Cloud Computing"]
excerpt: "Azure VM auto-shutdown saves money only when it deallocates in the right time zone. Set the schedule, notification, and the morning auto-start correctly."
image: "/assets/images/blog/blog-23.webp"
reading_time: 60
author: "robert-quinn"
last_updated: 2023-04-10
lang: en
---
A correctly configured Azure VM auto-shutdown schedule is one of the cheapest, highest-return settings in the entire platform, and a misconfigured one is a quiet disappointment that looks like savings and delivers none. The toggle sits in the portal under Operations, takes about ninety seconds to enable, and promises to power off your virtual machine every evening so you stop paying for compute you are not using. The trouble is that two of its most important behaviors are easy to get wrong without any error message to warn you. The schedule fires in a time zone you set separately and that defaults to coordinated universal time, so an engineer in Chicago who picks 19:00 and never touches the time zone gets a machine that powers off at 13:00 local. And the saving only materializes if the machine deallocates, which is exactly what this feature does, but which is also the precise thing that a stop issued from inside the guest operating system does not do. Get either of these wrong and you have a schedule that runs faithfully every day while saving you nothing or interrupting your work at lunchtime.

![Azure VM auto-shutdown schedule, time zone, and deallocation configuration - Insight Crunch](/assets/images/blog/blog-23.webp)

This article treats auto-shutdown as a configuration to verify rather than a checkbox to tick. The central rule that organizes everything below is what we will call the time-zone-and-deallocate rule: an auto-shutdown schedule earns its keep only when it deallocates the machine and fires in the time zone you actually live in, so confirming both is the difference between real savings and a schedule that does nothing useful while appearing busy. Around that rule we will build the InsightCrunch auto-shutdown setup checklist, a step-by-step procedure that names the gotcha at each stage: enable the schedule, set the correct time zone, add a notification with enough lead time to defer, confirm the machine reaches the deallocated state, layer on an auto-start mechanism because Azure does not include one, and extend the policy from a single machine to an entire fleet. By the end you will be able to set this up by hand, prove it worked, encode it as infrastructure, and pair it with the morning start that the built-in feature deliberately leaves out.

The reason this matters is simple arithmetic that compounds. A development or test machine that runs only during a ten-hour workday, five days a week, is idle for roughly seventy percent of the hours in a week. Compute charges are billed by the second while a machine is allocated, whether or not anyone is logged in, so seventy percent idle translates almost directly into seventy percent waste on the compute line of the bill. Auto-shutdown is the lever that captures that waste with no code, no agent, and no ongoing maintenance, provided it is configured to do the thing it claims. The cost reasoning sits alongside the broader discipline of [right-sizing Azure VMs to cut cost](/2024/11/04/azure-vm-right-sizing/), where picking the correct machine size and turning idle machines off are the two complementary halves of the same bill. This guide is the second half, done properly.

## What correct auto-shutdown configuration buys, and what breaks when it is wrong

Before any commands, it pays to be precise about what this feature does and does not promise, because the gap between expectation and behavior is where almost every wasted setup originates. Auto-shutdown is a scheduling feature attached to a single virtual machine. You give it a time and a time zone, and once a day, at that local time, Azure issues a deallocation against the machine. That is the whole of the built-in behavior. It is not a scaling system, it is not idle detection, and it is not a paired start-and-stop scheduler. It powers a machine off on a clock, nothing more, and the value of understanding that narrowness is that it tells you exactly which expectations the feature will quietly fail to meet.

What correct configuration buys you is a machine that stops billing for compute on a predictable schedule without anyone remembering to stop it. The win is durable because it requires no human in the loop and no infrastructure to babysit. A development box configured to power off at 19:00 local time will do so whether the engineer who owns it is on holiday, distracted, or asleep, and the compute meter halts within a minute or two of the schedule firing. Over a month, on a machine that would otherwise run continuously, that is the difference between paying for around 720 hours of compute and paying for roughly 220, a reduction that lands directly on the largest line item for most idle workloads.

What breaks when it is wrong is harder to notice precisely because the feature keeps running. A schedule set in the wrong time zone fires at the wrong hour every single day, with perfect reliability, and the only symptom is a machine that is unexpectedly off when someone tries to use it or unexpectedly on when the bill arrives. A schedule applied to a machine whose users stop it from inside the guest operating system rather than relying on deallocation saves nothing, because the compute reservation is still held even though the screen says the machine is off. And a schedule with no paired start mechanism leaves a team manually powering machines back on every morning, which works for one machine and collapses for fifty. None of these failures throws an error. Each one looks like success right up until you check the meter or the clock.

### Does auto-shutdown actually stop my Azure bill?

Auto-shutdown stops the compute portion of your bill because it deallocates the machine, which releases the underlying compute reservation. You continue to pay for the managed disks that remain provisioned and for any static public IP you reserved, but the per-second compute charge, which is the dominant cost for most machines, stops within a minute or two of the schedule firing.

This distinction between compute charges and the charges that persist is the single most important thing to internalize about the feature, and it is worth stating in plain terms. When a machine is deallocated, the virtual CPU and memory that backed it are returned to the Azure fabric and given to other tenants. You are no longer holding those resources, so you are no longer billed for them. What you keep, and keep paying for, is everything that has to survive the machine being off so that it can come back exactly as it was: the operating system disk, any data disks, and, if you reserved one, a static public IP address. Those storage and address charges are typically a small fraction of the compute charge for a running machine, which is why deallocation captures the overwhelming majority of the available saving. If your goal is to understand the cost model in full, the storage that persists is the same storage you would tune in [right-sizing Azure VMs to cut cost](/2024/11/04/azure-vm-right-sizing/), and the two articles together cover both the size of the machine and the hours it runs.

## The deallocate-versus-stop distinction that decides whether you save anything

The most consequential thing to understand before configuring auto-shutdown is the difference between a stopped machine and a deallocated machine, because the feature only saves money by reaching the second state, and a great many engineers assume the first state saves money when it does not. A machine has a power state and a provisioning state, and the combination that matters for billing is reported by the platform as a status string. A machine that is shut down but still holding its compute reservation reports as Stopped. A machine that has been shut down and has had its compute reservation released reports as Stopped (deallocated). The parenthetical is not cosmetic. It is the line between paying for compute and not paying for compute.

The trap is that there are two ways to turn a machine off and they produce different results. If you log into the guest operating system and issue a shutdown from inside it, the operating system halts, the screen goes dark, and the machine reports as Stopped. The compute reservation is still held, because from the fabric's point of view you have only powered down the guest, not released the resources. You will continue to be billed for compute on a machine that looks, to a casual glance, completely off. The other way is to deallocate the machine through the Azure control plane, which both halts the guest and returns the compute resources to the fabric, producing the Stopped (deallocated) status and halting the compute meter. Auto-shutdown does the second of these. It issues a control-plane deallocation, not a guest shutdown, which is precisely why it saves money where an in-guest shutdown would not.

This is worth dwelling on because it explains a confused support pattern that appears constantly. An engineer enables auto-shutdown, watches the machine go off on schedule, checks the bill a month later, and sees the expected drop. That is the feature working. A different engineer, who never enabled auto-shutdown but who diligently shuts machines down from inside Windows or Linux every evening, checks the bill and sees no change at all, and concludes that turning machines off does not save money in Azure. The conclusion is wrong. Turning machines off saves money; shutting them down from inside the guest does not turn them off in the sense Azure bills on. The full mechanics of these power states, including the timing of the deallocation and what survives it, are covered in the [complete engineering guide to Azure Virtual Machines](/2022/01/03/azure-virtual-machines-complete-guide/), which is the pillar reference for how the platform models a machine's lifecycle. For the purposes of configuring auto-shutdown, the operational rule is short: trust the status string, not the screen. A machine is only saving you money when its status reads Stopped (deallocated).

### Why does my VM still cost money after I shut it down?

A virtual machine that you shut down from inside its guest operating system still costs money because the compute reservation is never released. The machine reports as Stopped rather than Stopped (deallocated), so Azure continues billing for the virtual CPU and memory. Only a control-plane deallocation, which is what auto-shutdown performs, halts the compute charge.

The practical consequence is that you should never rely on people remembering to deallocate machines correctly, and you should never assume an in-guest shutdown is doing what auto-shutdown does. People will shut down from the Start menu or the command line because that is the habit muscle memory provides, and that habit costs money silently. The whole point of configuring auto-shutdown is to replace a fallible human habit, and a frequently mistaken one at that, with a control-plane action that always reaches the deallocated state. When you verify your configuration later in this guide, the single check that proves the feature is earning its keep is confirming the machine reaches Stopped (deallocated) after the schedule fires, not merely that it appears to be off.

## Prerequisites and the correct order of operations

The setup itself is short, but doing it in the right order saves a round of confusion, so it is worth naming the prerequisites before the steps. You need a virtual machine that already exists, because auto-shutdown is a property of a machine and there is nothing to schedule until one is present. You need permission to write to that machine's configuration, which in role terms means the Virtual Machine Contributor role or any role that includes the relevant write actions on the machine and on the schedule resource that backs the feature. If you intend to add a webhook notification or an auto-start mechanism, you will need a few additional pieces that we introduce when we reach them, namely an endpoint to receive the webhook and an automation principal with rights to start the machine. None of that is required for the core schedule.

The correct order of operations is to decide the intended local power-off time first, in words, before touching the portal, because the time and the time zone are configured as two separate fields and the second one is the one everyone forgets. Decide that the machine should power off at, for example, seven in the evening Central time. Then enable the schedule and enter the time. Then, and this is the step that the default actively works against, set the time zone to the one your intended time was expressed in. Then decide whether you want a pre-shutdown warning and configure the notification if so. Then save. Then, separately and deliberately, verify that the machine actually deallocates when the schedule fires, because a saved configuration is a claim, not a proof. Finally, if the machine needs to be available in the morning, add an auto-start mechanism, since the built-in feature handles only the power-off half of the day.

That ordering matters because the failure modes cluster at the boundaries between steps. The time zone is forgotten because it is a second field after the time field and the time field feels like the whole job. Verification is skipped because the portal shows the schedule as enabled and that feels like confirmation. Auto-start is overlooked because the feature is named for shutdown and gives no hint that startup is a separate concern. Naming the order and the gotcha at each boundary is most of what it takes to get this right, and it is exactly what the InsightCrunch auto-shutdown setup checklist captures at the end of this article.

## The step-by-step setup with working commands

There are several correct ways to configure auto-shutdown, and the right one depends on whether you are setting up one machine by hand or many machines repeatably. We will walk the portal path first because it is where most people start and where the time-zone trap is most visible, then give the command-line equivalents that you will actually want for anything beyond a single machine, and finally the infrastructure-as-code forms that make the configuration durable and reviewable.

### How do I configure Azure VM auto-shutdown correctly?

Open the virtual machine in the portal, select Auto-shutdown under Operations, toggle it on, enter the local time you want the machine to power off, and then set the time zone to match that local time before saving. The time and the time zone are separate fields, and the time zone defaults to coordinated universal time, so the second field is the one that determines whether the schedule fires when you expect.

In the portal, the full path is to navigate to the machine, scroll the left-hand menu to the Operations group, and select Auto-shutdown. You will see a toggle to enable the feature, a scheduled shutdown time entered as a 24-hour value, a time zone selector, and a notification section. The single most important action on this page, after entering the time, is to open the time zone selector and choose the zone your time was expressed in. The selector defaults to coordinated universal time, abbreviated UTC, and if you leave it there your machine powers off at the UTC interpretation of the clock value you typed, which for most of the world is not the local interpretation you intended. Once the time and the time zone are correct, optionally configure the notification, then save. The portal confirms the schedule with a small notification of its own, and the Auto-shutdown page thereafter shows the feature as enabled with your chosen values.

The portal is fine for one machine, but it does not scale and it does not leave an audit trail, so the command-line forms are what you want for anything serious. The Azure command-line interface configures the schedule through the same underlying resource the portal uses. The schedule is implemented as a resource in the Microsoft.DevTestLab provider namespace, specifically a global schedule associated with the machine, which is why some of the commands reference that provider even on a plain virtual machine that is not part of a lab. This is an implementation detail that surprises people who go looking for the setting and find it living under a lab-services provider, but it is harmless and you do not need a lab to use it.

Here is the pattern for setting auto-shutdown on a machine with the Azure command-line interface, expressed against the schedule resource directly:

```bash
# Variables for clarity
RG="rg-dev-workloads"
VM="vm-dev-box-01"
SUB=$(az account show --query id -o tsv)

# The auto-shutdown schedule is a DevTestLab global schedule
# named shutdown-computevm-<vmName>, associated with the VM resource ID.
VM_ID=$(az vm show -g "$RG" -n "$VM" --query id -o tsv)

az resource create \
  --resource-group "$RG" \
  --name "shutdown-computevm-$VM" \
  --resource-type "Microsoft.DevTestLab/schedules" \
  --location "centralus" \
  --properties "{
    \"status\": \"Enabled\",
    \"taskType\": \"ComputeVmShutdownTask\",
    \"dailyRecurrence\": { \"time\": \"1900\" },
    \"timeZoneId\": \"Central Standard Time\",
    \"targetResourceId\": \"$VM_ID\",
    \"notificationSettings\": {
      \"status\": \"Disabled\",
      \"timeInMinutes\": 30
    }
  }"
```

Two fields in that payload carry the whole weight of the time-zone-and-deallocate rule. The time value, written here as 1900 in the HHmm form the schedule resource expects, is the clock time the machine powers off. The timeZoneId value, written here as Central Standard Time, is the zone that clock time is interpreted in, and it is the field that the portal defaults to UTC and that you must set deliberately. Note that the time zone identifier is the Windows time zone name, not the Internet Assigned Numbers Authority identifier you might expect from Linux tooling. You write Central Standard Time rather than America/Chicago. Using the wrong identifier format is a common reason a command-line configuration silently does not apply the zone you meant.

The PowerShell equivalent uses the same underlying resource and the same two critical fields, which is useful if your tooling standardizes on PowerShell for Azure automation:

```powershell
$rg   = "rg-dev-workloads"
$vm   = "vm-dev-box-01"
$loc  = "centralus"
$vmId = (Get-AzVM -ResourceGroupName $rg -Name $vm).Id

$properties = @{
    status         = "Enabled"
    taskType       = "ComputeVmShutdownTask"
    dailyRecurrence = @{ time = "1900" }
    timeZoneId     = "Central Standard Time"
    targetResourceId = $vmId
    notificationSettings = @{
        status        = "Disabled"
        timeInMinutes = 30
    }
}

New-AzResource `
  -ResourceGroupName $rg `
  -ResourceType "Microsoft.DevTestLab/schedules" `
  -ResourceName "shutdown-computevm-$vm" `
  -Location $loc `
  -Properties $properties `
  -Force
```

Whichever surface you use, the principle is the same. The time field sets when, the time zone field sets the frame of reference for when, and leaving the second field at its default is the configuration error that produces a schedule that fires at the wrong hour with complete reliability.

### Configuring the schedule as Bicep and Terraform

For anything beyond a single hand-tended machine, the configuration belongs in source control, reviewed and applied the same way as the rest of your infrastructure. Bicep expresses the schedule as a resource of the same DevTestLab schedule type, attached to the machine by name. The advantage over the imperative command is that the file is the record: the intended time, the intended zone, and the notification posture are all visible in a diff, which means a wrong time zone gets caught in review rather than discovered on the bill.

```bicep
param vmName string
param location string = resourceGroup().location
param shutdownTime string = '1900'
param timeZone string = 'Central Standard Time'
param notificationEmail string = ''

resource vm 'Microsoft.Compute/virtualMachines@2023-09-01' existing = {
  name: vmName
}

resource autoShutdown 'Microsoft.DevTestLab/schedules@2018-09-15' = {
  name: 'shutdown-computevm-${vmName}'
  location: location
  properties: {
    status: 'Enabled'
    taskType: 'ComputeVmShutdownTask'
    dailyRecurrence: {
      time: shutdownTime
    }
    timeZoneId: timeZone
    targetResourceId: vm.id
    notificationSettings: {
      status: empty(notificationEmail) ? 'Disabled' : 'Enabled'
      timeInMinutes: 30
      emailRecipient: notificationEmail
      notificationLocale: 'en'
    }
  }
}
```

The Terraform form uses the dedicated resource the AzureRM provider exposes for this purpose, which is more ergonomic than the schedule type because the provider names the fields in plain terms. The same two critical values appear, here as daily_recurrence_time and timezone, and the provider validates the time zone identifier against the Windows naming, so a typo in the zone is caught at plan time rather than silently ignored.

```hcl
resource "azurerm_dev_test_global_vm_shutdown_schedule" "dev_box" {
  virtual_machine_id = azurerm_linux_virtual_machine.dev_box.id
  location           = azurerm_resource_group.dev.location
  enabled            = true

  daily_recurrence_time = "1900"
  timezone              = "Central Standard Time"

  notification_settings {
    enabled         = true
    time_in_minutes = 30
    webhook_url     = var.shutdown_webhook_url
  }
}
```

Whichever form you adopt, encoding the schedule as code does something the portal cannot: it makes the time zone a reviewed value rather than a forgotten one. A teammate reading the pull request sees timezone = "Central Standard Time" right next to the time, and a wrong value becomes a review comment instead of a month of mistimed power-offs. This is the same reasoning that pushes backup and recovery into code as well, and the [correct configuration of Azure Backup for VMs](/2023/07/03/configure-azure-vm-backup/) follows the identical pattern of putting the schedule, the retention, and the verification into a reviewable artifact rather than a portal click. Auto-shutdown and backup are the two scheduled lifecycle behaviors most worth treating as code, because both are easy to set wrong and invisible when they are.

## The settings the defaults get wrong, starting with the time zone

If there is one section of this guide to read twice, it is this one, because the default that the feature ships with is the cause of the most common auto-shutdown failure by a wide margin. The time zone field defaults to coordinated universal time, and that default is wrong for almost everyone who is not actually operating in that zone, which is almost everyone.

### Why does auto-shutdown fire at the wrong time?

Auto-shutdown fires at the wrong time because the schedule interprets your chosen clock value in the configured time zone, which defaults to coordinated universal time rather than your local zone. If you enter 19:00 but leave the zone at the default, the machine powers off at 19:00 UTC, which in Central time is one in the afternoon during daylight saving and seven in the morning the rest of the year, never the evening you intended.

The mechanism is worth spelling out because once you see it the fix is obvious. The schedule stores two things: a clock value and a zone. When the scheduling system decides whether to fire, it takes the clock value, interprets it in the stored zone, and compares that moment to the current time. It does not interpret the clock value in your browser's time zone, in the machine's region, or in the location of the resource group. It uses only the zone field. So the clock value you typed is meaningless on its own; it acquires a real meaning only when paired with the zone, and if the zone is the default UTC then your evening time becomes a UTC moment that lands somewhere unhelpful in your actual day.

The confusion is amplified by a reasonable but wrong assumption that the schedule uses local browser time, the way a calendar invite often does. People are used to entering a time and having software figure out their zone from context. Auto-shutdown does not do that. It treats the zone as an explicit, separate decision, and it defaults that decision to UTC. The portal does nothing to highlight that the default is probably not what you want, so the time zone field is skipped, the schedule is saved, and the machine begins powering off at a time that is offset from the intended one by however many hours separate your zone from UTC.

There is a second-order trap inside the time zone choice that catches even people who remember to set it, and that is daylight saving time. The Windows time zone identifiers that the schedule uses, names like Central Standard Time and Pacific Standard Time, are not fixed-offset zones despite the word Standard in them. They are full zones that observe daylight saving where the underlying region does, so Central Standard Time as an identifier shifts between a six-hour and a five-hour offset from UTC across the year, following the local rules. This is what you want, because it means a schedule set to 19:00 Central Standard Time fires at seven in the evening local time all year round, automatically adjusting across the spring and autumn transitions. The trap is for the engineer who, distrusting the Standard in the name, tries to compensate by entering a fixed UTC offset somewhere, or who picks a deliberately offset clock value to account for daylight saving manually. Do not compensate. Pick the zone that matches where you are and let the platform handle the seasonal shift. Manual compensation breaks twice a year, on exactly the days the platform would have handled correctly.

The fix for all of this is the same single action: set the time zone field to the zone your intended time was expressed in, and never leave it at the default unless you genuinely operate in UTC. If you manage machines for teams in several regions, set each machine's zone to that team's local zone, not to a single corporate standard, because the whole value of the feature is that the machine powers off at a sensible local hour for the people who use it. A development box used by a team in London should power off in London evening time; a box used by a team in Sydney should power off in Sydney evening time; and the only way to get both right is to set each schedule's zone correctly rather than relying on a default that serves neither.

## The pre-shutdown notification and why it is worth enabling

The notification is the feature's quiet courtesy, and it solves a real problem: a machine that powers off on schedule will interrupt anyone still using it, and without warning that interruption arrives with no chance to save work or defer. The notification section lets you send a message a set number of minutes before the schedule fires, giving whoever is logged in a window to either wrap up or postpone the shutdown.

### Can I get a warning before my VM shuts down?

Yes. In the notification section of the auto-shutdown configuration, enable notifications and set the lead time in minutes, which controls how long before the scheduled power-off the message is sent. You can deliver the notification to an email address or to a webhook, and the message includes a link that lets the recipient postpone the shutdown by a chosen interval if they are still working.

The lead time is the knob that makes the notification useful rather than merely informative. A notification that arrives one minute before shutdown is little better than none, because a minute is not enough time to react. A lead time in the range of fifteen to thirty minutes is the usual sweet spot: long enough that someone mid-task can finish a thought, save their work, and decide whether to defer, but short enough that the notification is clearly about the shutdown that is actually imminent rather than a vague future event. The configuration accepts the lead time as a number of minutes, and you set it once alongside the schedule.

The delivery target is the more interesting choice. Email is the simple option and works for a machine with a known human owner who will read the warning. The webhook option is the one that unlocks integration, because it lets you route the pre-shutdown event into whatever system your team already watches. A webhook can post into a chat channel so the warning lands where the team is already looking, or it can trigger an automated decision, such as checking whether a long-running job is in progress and deferring the shutdown if so. The webhook payload identifies the machine and the impending action, and the postponement link in the standard message lets a human extend the machine's life by a chosen interval directly from the notification. For a shared development box, routing the webhook into the team's chat is often the highest-value configuration, because it turns a silent scheduled action into a visible one that anyone can veto when they are in the middle of something.

There is a practical reason to enable the notification even on machines nobody is actively babysitting, which is that it converts an invisible scheduled action into an auditable one. When the notification fires, there is a record that the schedule is alive and behaving, which is a small but real reassurance that the configuration you set up months ago is still doing its job. A schedule that has silently stopped firing, perhaps because someone disabled it, is much easier to notice when its daily notification stops arriving than when the only evidence is a gradually rising bill.

## The verification step that proves it worked

A saved schedule is a claim, and the discipline that separates a configuration that works from one that merely looks configured is verifying the claim. There are two things to verify, corresponding to the two halves of the time-zone-and-deallocate rule: that the schedule fires at the time you intended, and that when it fires the machine reaches the deallocated state rather than merely stopping.

The fastest way to verify the timing without waiting a full day is to temporarily set the schedule to a few minutes in the future, in the correct zone, and watch what happens. Set the time to, say, five minutes ahead of the current local moment, save, and wait. If the machine powers off at that local moment, the time zone is correct. If it does not power off, or powers off at a different time, the zone is wrong and you have caught it in five minutes rather than discovering it on the bill. Once verified, set the schedule back to its intended evening time. This temporary-near-future test is the single most valuable verification you can run, because it directly exercises the exact behavior that the default gets wrong.

Verifying the deallocation is a matter of checking the machine's status string after the schedule fires, and this is where the command line earns its place because the status is unambiguous there. The relevant check reads the machine's instance view and looks at the power state code:

```bash
az vm get-instance-view \
  --resource-group "rg-dev-workloads" \
  --name "vm-dev-box-01" \
  --query "instanceView.statuses[?starts_with(code, 'PowerState/')].code" \
  -o tsv
```

After a correct auto-shutdown, that command returns PowerState/deallocated. If it returns PowerState/stopped, the machine has been stopped but not deallocated, and you are still paying for compute, which means something is wrong with how the machine is being powered off. After a normal auto-shutdown the value should always be deallocated, because the feature issues a deallocation by design; seeing stopped instead is a signal that the machine was powered off some other way, perhaps from inside the guest by a user, and that the saving is not being captured.

The PowerShell equivalent reads the same instance view and is convenient if your verification scripts live in that ecosystem:

```powershell
$state = (Get-AzVM -ResourceGroupName "rg-dev-workloads" `
    -Name "vm-dev-box-01" -Status).Statuses |
    Where-Object { $_.Code -like "PowerState/*" } |
    Select-Object -ExpandProperty Code
$state
```

For a fleet, you do not want to check machines one at a time, so a Resource Graph query gives you the power state of every machine at once and lets you spot the ones that are stopped rather than deallocated. A query that lists machines whose power state is stopped but not deallocated is exactly the report you want, because every machine on that list is one that is costing money while appearing to be off. Running that query on a schedule, and alerting when the list is non-empty, turns the deallocate half of the rule into a monitored invariant rather than a thing you hope is true.

## Common misconfigurations and the symptoms that reveal them

Every recurring auto-shutdown problem reduces to one of a small set of misconfigurations, and learning to map the symptom to the cause is most of the diagnostic skill. The findable artifact later in this article tabulates them, but it helps to walk the patterns in prose first because the symptoms are often subtle.

The first and most common is the wrong time zone, whose symptom is a machine that powers off at an unexpected hour, reliably, every day. The giveaway is the reliability: a machine that powers off at the wrong time once is a fluke, but a machine that powers off at exactly the wrong time every single day is a time zone that is offset from your intended one by a fixed number of hours. Compute the offset between the time it actually fires and the time you intended, and you will usually find it matches the gap between UTC and your local zone, which confirms the zone was left at the default. The fix is to set the zone correctly and re-verify with the near-future test.

The second is the stopped-not-deallocated pattern, whose symptom is a bill that does not fall even though machines appear to be turned off. This one does not come from the auto-shutdown feature itself, which always deallocates, but from machines being powered off some other way, typically a user shutting down from inside the guest. The diagnostic is the power state check above: if machines that should be off report PowerState/stopped rather than PowerState/deallocated, the saving is not being captured. The fix is partly technical, which is to ensure machines are deallocated through the control plane rather than stopped in-guest, and partly cultural, which is to stop relying on people to shut machines down correctly and let the schedule do it.

The third is the missing auto-start, whose symptom is not a cost problem but an availability one: the team arrives in the morning to find their machines off and has to power them on by hand, every day, which is tedious for one machine and unworkable for many. This is not a misconfiguration of auto-shutdown so much as an incomplete understanding of its scope, because the feature genuinely does not include a start half. The fix is to add a separate auto-start mechanism, which the next section covers in full.

The fourth is the schedule applied to a machine that should never auto-shut, whose symptom is an important machine going dark at an inconvenient moment. A production machine, a build agent that runs overnight jobs, or a shared service that someone might need at any hour should not be on an evening auto-shutdown schedule, and applying a blanket schedule across a subscription without excluding these is a classic over-reach. The fix is selective application: target the schedule at the machines that are genuinely idle off-hours, typically development and test boxes, and exclude the ones whose availability matters around the clock. When you apply auto-shutdown at scale, this selectivity is the difference between a cost win and an outage.

The fifth, subtler than the others, is the daylight saving miscompensation described earlier, whose symptom is a machine that fires at the right time for half the year and an hour off for the other half. This comes from someone trying to outsmart the time zone by entering a manually offset clock value, and it corrects itself the moment you stop compensating and simply set the correct named zone, which handles the seasonal shift on its own.

## Making the configuration repeatable across many machines

Configuring one machine in the portal is fine. Configuring fifty that way is a recipe for inconsistency, drift, and the exact time-zone errors this guide is built to prevent, because every manual setup is a fresh chance to forget the zone. The point of treating auto-shutdown as code is that it scales the correct configuration without scaling the error rate, and there are three broad ways to apply it across a fleet, each suited to a different organizational shape.

### How do I apply auto-shutdown across many VMs?

Apply auto-shutdown across many machines by defining the schedule as code, a Bicep module or Terraform resource, and deploying it to each machine through your normal pipeline, or by using Azure Policy to detect and remediate machines that lack a schedule. For machines created from a template or a lab, build the schedule into the template so every machine gets it at creation rather than as an afterthought.

The code-and-pipeline approach is the most direct. You write the schedule once as a module that takes the machine name, the time, and the zone as parameters, and you instantiate it for each machine, with the zone set per team or per region rather than globally. Because the configuration lives in source control, the time zone for every machine is visible and reviewable, and a wrong value is caught in a pull request rather than on a bill. This approach fits teams that already deploy their infrastructure as code and simply need to add the schedule resource alongside the machine definition. The schedule and the machine deploy together, so there is never a window where a machine exists without its power-off schedule.

The policy approach suits organizations that want a guardrail rather than a deployment step, where machines are created by many teams and central governance wants to ensure none of them are left running off-hours by accident. Azure Policy can audit for machines that lack an auto-shutdown schedule and flag them as non-compliant, and with a remediation task it can deploy the schedule to machines that are missing one. The policy becomes a standing invariant: any development machine created anywhere in the scope acquires a schedule, whether or not the team that created it remembered to add one. This is the same governance pattern that turns any desired configuration from a hope into an enforced standard, and it is worth pairing with a clear exclusion list so that production machines, build agents, and always-on services are exempt from the blanket schedule. The selectivity matters as much as the enforcement, because a policy that powers off machines that should stay up is worse than no policy at all.

The template approach fits the development and test scenario most cleanly, because machines in that world are often created from a known image or a lab definition, and building the schedule into that definition means every machine is born with the correct power-off behavior. Azure DevTest Labs, which is where the underlying schedule resource actually lives, makes auto-shutdown a lab-wide policy: every machine created in the lab inherits the lab's shutdown schedule and zone, so an engineer who spins up a machine for an afternoon's work gets the cost protection automatically without configuring anything. For teams whose development machines come and go frequently, baking the schedule into the lab or the template is the lowest-friction way to ensure the cost discipline is never skipped, because it removes the human step entirely.

Whichever approach you choose, the at-scale version of the time-zone-and-deallocate rule is to make both halves of the rule structural. Set the zone in the code, the policy, or the template so it cannot be forgotten, and monitor the deallocated state across the fleet so a machine that is merely stopped is caught and corrected. Scale multiplies both the savings and the errors, so the discipline that makes scale safe is removing the manual step where the error enters.

## Adding auto-start, the half Azure leaves out

The single most important thing to understand about auto-shutdown is that it has no built-in counterpart for starting machines back up. Azure deliberately ships the power-off half and leaves the power-on half to you, and the reasoning is sound: shutting an idle machine off is almost always safe and saves money, while starting a machine up is a decision that depends on whether anyone actually needs it that morning, which the platform cannot know. But the consequence is that a team relying only on auto-shutdown will find their machines off every morning, and the manual re-start that follows is exactly the kind of repetitive toil that automation exists to remove.

### How do I also start the VM automatically in the morning?

Azure does not include a built-in auto-start, so you add one using Azure Automation, a Logic App, or the packaged start-and-stop solution. The simplest reliable approach is an Azure Automation runbook that starts the tagged machines on a morning schedule, paired with a managed identity that has rights to start them, so the start runs without stored credentials and on a clock you control.

The Azure Automation runbook approach is the workhorse and the one most teams settle on. You create an Automation account, give it a managed identity, grant that identity the Virtual Machine Contributor role on the resource group or subscription scope that holds the machines, and write a short runbook that starts the machines you want, scheduled to run on weekday mornings. The runbook can target machines by tag, which is the pattern that scales: tag every machine that should follow business-hours scheduling with something like AutoSchedule = BusinessHours, and the runbook starts exactly those machines without needing to know their names in advance. A representative runbook reads the tagged machines and starts the ones that are deallocated:

```powershell
# Runbook: Start-BusinessHoursVMs
# Authenticates with the Automation account's managed identity.
Connect-AzAccount -Identity | Out-Null

$targets = Get-AzVM -Status | Where-Object {
    $_.Tags.AutoSchedule -eq "BusinessHours" -and
    $_.PowerState -eq "VM deallocated"
}

foreach ($vm in $targets) {
    Write-Output "Starting $($vm.Name) in $($vm.ResourceGroupName)"
    Start-AzVM -ResourceGroupName $vm.ResourceGroupName `
               -Name $vm.Name -NoWait
}

Write-Output "Start pass complete. Targeted $($targets.Count) machines."
```

The managed identity is the part to get right, because it is what lets the runbook act without a stored secret. Rather than embedding credentials in the runbook, the Automation account carries an identity that Azure manages, and you grant that identity the minimum role it needs, which is the ability to read and start machines in the relevant scope. Granting Virtual Machine Contributor on the resource group that holds the development machines is the least-privilege fit, because it allows starting and stopping without granting broader rights. This keeps the automation principal scoped to exactly what it needs and nothing more, which is the same identity discipline you would apply to any automated actor in the platform.

The Logic App approach is an alternative that suits teams who prefer a low-code, visual workflow and who may want to layer in conditions, such as starting machines only on working days, checking a calendar for holidays, or starting different groups at different times. A Logic App on a recurrence trigger can call the management API to start the tagged machines, and its visual nature makes the schedule and conditions easy for a non-specialist to read and adjust. The trade-off against the runbook is that the Logic App is a little heavier for a pure start-on-schedule task, but it shines when the start decision needs to consider more than the clock.

There is also a packaged solution that Microsoft maintains for exactly this start-and-stop pattern, built on Automation and Logic Apps, which deploys the scheduling machinery for you and lets you configure which machines to start and stop and when. It is the fastest way to get a complete morning-start and evening-stop cycle without writing the runbook yourself, and it is worth considering for teams who want the outcome without building the plumbing. Whichever route you take, the principle is constant: auto-shutdown handles the evening, and you own the morning, so a complete daily cycle is always two mechanisms working together, not one.

The two halves should be tuned to the team's actual hours with a deliberate gap. Power the machines off in the evening after the latest realistic end of the working day, and start them in the morning before the earliest realistic start, with enough margin that nobody arrives to a machine that is still booting. A common pattern is a power-off at seven in the evening local time through auto-shutdown and a start at seven in the morning local time through the runbook, which gives the team a full working day on either side and twelve idle hours overnight where the compute meter is silent. On weekends, the runbook simply does not run, so machines that powered off on Friday evening stay deallocated until Monday morning, capturing the weekend as pure saving with no manual intervention at all.

## Real-world scenarios and how to set each one up

The patterns engineers actually report cluster into a handful of recurring scenarios, and walking each one as a concrete setup makes the abstract rules above land. Each scenario is a small recipe with its own correct configuration.

The first is the single development box used by one engineer during business hours. This is the canonical case and the simplest. Enable auto-shutdown, set the power-off to an hour after the engineer's typical end of day, set the zone to the engineer's local zone, enable an email notification with a thirty-minute lead so a late session can be deferred, and pair it with a morning start through a runbook or simply accept a manual morning start if the engineer prefers to control when their day begins. For one box, even a manual morning start is tolerable, and the evening auto-shutdown alone captures most of the available saving because the machine is off all night and all weekend.

The second is the machine that should never auto-shut, such as a production service, a build agent running overnight jobs, or a shared service someone might need at any hour. The correct configuration here is to not configure auto-shutdown at all, and, if a blanket policy applies schedules across the subscription, to explicitly exclude this machine through a tag or an exemption. The failure to guard against is a well-meaning cost initiative powering off a machine whose availability matters, which converts a cost saving into an incident. Tag always-on machines clearly, exclude them from any fleet-wide schedule, and treat their continuous running as a deliberate cost, not an oversight.

The third is the team of development boxes that should follow business hours together. This is where the at-scale machinery earns its place. Tag every machine in the group with a scheduling tag, define the evening auto-shutdown as code so every machine gets the same correct zone, and run a morning start runbook against the tag. The result is a fleet that powers down every evening and comes up every morning with no per-machine intervention, and the saving scales linearly with the number of machines because each one is idle the same off-hours stretch. The discipline that keeps this safe is the deallocated-state monitoring described earlier, because at fleet scale a single machine that is merely stopped rather than deallocated is easy to miss and steadily costly.

The fourth is the machine someone is actively using when the schedule is about to fire, where the notification is the whole point. With a notification configured, the user receives the pre-shutdown warning, sees that a power-off is imminent, and uses the postponement link to push it out by a chosen interval so they can finish. This is the scenario that justifies the notification's existence: without it, the schedule interrupts work with no warning; with it, the schedule becomes a default that anyone present can override for the evening. For shared boxes, routing the notification webhook into the team's chat channel makes the warning visible to everyone, so whoever is mid-task can defer it for the group.

The fifth is the cost-sensitive workload where auto-shutdown is one lever among several. A development team trying to minimize spend will combine the off-hours schedule with the right machine size and, where the workload tolerates interruption, with cheaper interruptible capacity. The hours-based saving from auto-shutdown stacks with the rate-based saving from [spot VMs and cost-saving compute](/2024/12/23/azure-spot-vms-explained/), because the two attack different parts of the bill: auto-shutdown reduces the hours you pay for, while spot capacity reduces the price per hour. A development box on a spot-priced size with an evening auto-shutdown and a weekday-only morning start is close to the cheapest way to run a machine that only needs to exist during working hours, and each lever is independent enough to add or remove without disturbing the others.

To run, reproduce, and confirm any of these configurations end to end, including watching a machine reach the deallocated state and validating the time zone with the near-future test, [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), which carries the tested command sequences for setting the schedule, checking the power state, and wiring up the morning start runbook so you can practice the whole cycle in a sandbox before applying it to machines that matter.

## A worked cost example

Numbers make the case concrete, so consider a representative development machine and walk the arithmetic, treating the rate as a value to confirm against current pricing because rates change and vary by region and size. Suppose the machine costs roughly a dollar an hour to run, a plausible figure for a mid-sized development size though you should verify the exact rate for your size and region against current pricing. Run continuously, that is about 720 hours a month, or around 720 dollars in compute. Now apply a business-hours schedule: the machine runs ten hours a day on weekdays only, which is about 50 hours a week, or roughly 217 hours a month. At the same rate that is about 217 dollars in compute, a reduction of around 500 dollars a month on a single machine, or close to seventy percent of the compute line. The storage charge for the disks persists whether the machine runs or not, so it does not change, but on most development machines the disk cost is a small fraction of the compute cost and the net saving is dominated by the hours removed.

Scale that across a team of ten similar machines and the monthly saving approaches 5,000 dollars, again subject to the actual rates, which is real money for a configuration that takes minutes to set up and nothing to maintain once it is code. The reason this lever ranks so high in cost work is that the effort is near zero and the saving is large and recurring, which is the exact profile of a first-priority optimization. It is the off-hours complement to choosing the correct machine size in the first place, and a team serious about its Azure bill does both: it sizes machines correctly so the running rate is no higher than the workload needs, and it runs them only during the hours the workload is actually used. Auto-shutdown is the second of those two disciplines, and on idle development capacity it is often the larger of the two savings.

## The InsightCrunch auto-shutdown setup checklist

The findable artifact that gathers the whole procedure into one reviewable reference is the InsightCrunch auto-shutdown setup checklist. It names each step, the correct action, and the specific gotcha that step exists to catch, so it doubles as a setup guide and a troubleshooting index. When a schedule misbehaves, the symptom usually maps to a single row, and the row tells you what was skipped.

| Step | Correct action | The gotcha it catches |
| --- | --- | --- |
| Enable the schedule | Toggle auto-shutdown on for the target machine | Forgetting that the schedule is per-machine, not subscription-wide |
| Set the power-off time | Enter the local clock time you want, in HHmm form | Treating the time field as the whole job and skipping the zone |
| Set the time zone | Choose the zone your time was expressed in, never the default | The default is UTC, so the schedule fires offset from local time |
| Do not compensate for daylight saving | Pick the named zone and let it shift seasonally | Manual offsets break twice a year on the transition dates |
| Configure the notification | Enable it with a 15 to 30 minute lead and a webhook or email | A one-minute warning is useless; no warning interrupts work |
| Confirm deallocation | Check the power state reads PowerState/deallocated | A machine merely Stopped is still billing for compute |
| Verify the timing | Set a near-future test time and watch it fire | A saved schedule is a claim, not proof the zone is right |
| Add an auto-start | Use Automation, a Logic App, or the packaged solution | Azure has no built-in start; machines stay off every morning |
| Apply at scale as code | Define the schedule in Bicep, Terraform, or a template | Manual per-machine setup reintroduces the time zone error |
| Exclude always-on machines | Tag and exempt production, build agents, shared services | A blanket schedule powers off a machine whose uptime matters |
| Monitor the deallocated state | Query the fleet's power states and alert on stopped-not-deallocated | A single mis-stopped machine is invisible and steadily costly |

The checklist encodes the time-zone-and-deallocate rule as a procedure: the time zone rows guard the half of the rule about firing in the right zone, and the deallocation rows guard the half about actually stopping the compute charge. Work the checklist top to bottom on setup, and use it as a lookup when something is off, because the symptom you are seeing almost always corresponds to a row you skipped.

## Monitoring and auditing the configuration over time

A configuration that was correct when you set it up is not necessarily correct six months later, because schedules get disabled, machines get recreated without their schedule, and zones get copied from one machine to another along with their mistakes. The discipline that keeps a fleet's auto-shutdown healthy over time is auditing it as an ongoing invariant rather than a one-time setup, and Azure Resource Graph is the right tool because it can query every machine and every schedule across the subscription in one pass.

The two audits worth running on a schedule mirror the two halves of the rule. The first audits the deallocated state: list every machine that should be following a schedule and report any that are currently neither running during business hours nor deallocated outside them, because a machine that is Stopped rather than deallocated overnight is leaking money. The second audits the presence and consistency of the schedules themselves: list every development machine and check that each has an enabled auto-shutdown schedule with a sensible zone, flagging any that are missing one or that carry a default UTC zone that almost certainly was not intended. A machine on the development tag with no schedule, or with a UTC zone in a non-UTC team, is a finding worth correcting.

A representative Resource Graph query for the second audit lists machines and joins them to their shutdown schedules so you can see which machines lack one:

```kusto
Resources
| where type =~ 'microsoft.compute/virtualmachines'
| where tags['AutoSchedule'] == 'BusinessHours'
| project vmId = tolower(id), vmName = name, rg = resourceGroup
| join kind=leftouter (
    Resources
    | where type =~ 'microsoft.devtestlab/schedules'
    | where properties.taskType == 'ComputeVmShutdownTask'
    | extend targetVm = tolower(tostring(properties.targetResourceId))
    | project targetVm,
              scheduleStatus = tostring(properties.status),
              zone = tostring(properties.timeZoneId)
  ) on $left.vmId == $right.targetVm
| project vmName, rg, scheduleStatus, zone
| where isempty(scheduleStatus) or scheduleStatus != 'Enabled'
```

That query returns the machines tagged for business-hours scheduling that have no enabled shutdown schedule, which is exactly the list a governance team wants to chase down. A companion query that filters on zone equal to UTC surfaces the machines whose schedule exists but probably fires at the wrong local hour, which is the more insidious finding because those machines look configured. Running both on a recurring basis, and alerting when either returns rows, turns the setup checklist into a continuously enforced standard rather than a thing that was true once.

The reason to invest in this monitoring is that auto-shutdown's failures are silent by nature. Nothing throws an error when a schedule is left at the default zone, when a machine is stopped instead of deallocated, or when a recreated machine loses its schedule. The only evidence is timing and cost, both of which are easy to overlook until they accumulate. Monitoring converts those silent failures into visible findings, which is the difference between a fleet whose cost discipline holds over time and one that quietly erodes as machines come and go.

## How auto-shutdown interacts with the rest of a machine's lifecycle

Auto-shutdown does not exist in isolation, and a few interactions with other features are worth knowing because they change how you configure it. The most important is the interaction with backup, because a machine that is deallocated overnight is off when a backup might run, and you want the two schedules to coexist rather than collide. Azure Backup can protect a deallocated machine, taking its backup from the disks even while the machine is off, so an evening auto-shutdown does not prevent an overnight backup. The configuration to get right is the timing relationship, and the safe pattern is to let backup run against the deallocated machine on its own schedule, which the [correct configuration of Azure Backup for VMs](/2023/07/03/configure-azure-vm-backup/) covers in detail. The two scheduled behaviors, powering off and backing up, are complementary rather than conflicting once you understand that backup operates on the disks regardless of the machine's power state.

The interaction with scale sets is a place where the per-machine feature does not fit, because a scale set manages its instances as a group and you do not generally attach a per-machine shutdown schedule to instances that the set creates and destroys. For scale-set workloads, the equivalent cost lever is the set's own scaling rules, which scale the instance count down during off-hours rather than deallocating individual machines on a clock. The mental model carries over, which is to not pay for capacity you are not using, but the mechanism is the set's autoscale rather than the per-machine auto-shutdown.

The interaction with spot capacity is additive rather than conflicting, as the cost section noted. A spot-priced machine can carry an auto-shutdown schedule exactly like a regular machine, and the two savings stack: the spot price reduces the hourly rate, and the schedule reduces the hours. The one nuance is that a spot machine can also be evicted by the platform when capacity is reclaimed, which deallocates it outside your schedule, so a spot machine's morning start may find it already deallocated from an eviction rather than from your evening schedule, and the start runbook handles both cases identically because it simply starts whatever is deallocated. The combination is a natural fit for interruption-tolerant development work.

The interaction with reserved capacity is worth a caution, because a reservation commits you to paying for a machine size for a term whether or not you run it, which means deallocating a reserved machine overnight does not save the reservation's cost. Reservations and auto-shutdown serve opposite cost strategies: a reservation makes sense for a machine that runs continuously, while auto-shutdown makes sense for a machine that is idle off-hours, and applying both to the same machine wastes the reservation during the hours the schedule powers it off. Match the cost lever to the usage pattern, using reservations for the always-on machines you exempt from auto-shutdown and using auto-shutdown for the intermittent ones you would never reserve.

## When the setup itself misbehaves

A few problems show up while configuring the schedule rather than after, and they are worth naming because they stop people before they even reach the time-zone trap. The most common is a save action that appears to do nothing or a configuration that does not persist, which usually traces to a permissions gap: writing the schedule requires write access to both the machine and the schedule resource, and an account with only read access can open the blade, enter values, and find that the save quietly fails. The fix is to confirm the account holds a role that includes the write actions for the machine and the DevTestLab schedule resource, with Virtual Machine Contributor being the usual sufficient role.

Another setup-time confusion is finding the schedule resource itself when you go looking for it outside the portal, because it lives under the Microsoft.DevTestLab provider rather than under the compute provider where you would expect a machine setting to sit. An engineer searching the compute resources for the schedule finds nothing and concludes it is not there, when in fact it is a separate resource named for the machine in a different provider namespace. Knowing where it lives saves a confused search and explains why the command-line and infrastructure-as-code forms reference that provider on a machine that has nothing to do with labs.

A third is a schedule that is enabled but does not fire, which, once you have ruled out the time zone, usually means the schedule was disabled, deleted, or never actually saved, or that the machine was recreated and lost its schedule along with its identity. A machine rebuilt from a template that does not include the schedule comes back without one, even if the previous incarnation had it, which is a strong argument for putting the schedule in the template so it survives a rebuild. When a previously working schedule stops firing, check first that the schedule resource still exists and is enabled, then check the machine was not recreated, before suspecting anything more exotic.

A fourth, specific to machines that are part of larger management systems, is a schedule that fires but the machine restarts itself shortly after, which happens when something else, such as an autoscale plan or a session-management system, has its own opinion about whether the machine should be running. If a machine deallocates on schedule and then comes back up unbidden, look for another controller that is starting it, because two systems with opposite intentions about the same machine will fight, and the auto-shutdown schedule is rarely the one at fault in that contest. The fix is to reconcile the two controllers so only one owns the machine's power state.

## Designing the schedule for a real team rather than a single machine

The configurations above are correct, but a team rarely wants a single isolated schedule. It wants a coherent daily rhythm across a group of machines, tuned to how the people actually work, and getting that rhythm right is a design exercise rather than a toggle. The first design decision is the boundary of the working day, because the power-off and power-on times should bracket it with margin on both sides. Set the evening power-off after the latest realistic end of day, not the nominal one, because a machine that powers off while someone is finishing a late task is a daily irritation even with a notification. Set the morning start before the earliest realistic arrival, with enough margin that the machine is fully booted and ready by the time the first person needs it, because a team that waits for machines to boot every morning will quietly resent the cost saving that imposed the wait.

The second design decision is whether the whole group shares one rhythm or splits into sub-groups, and the answer follows the team's geography. A group spread across regions should not share a single zone, because a London evening and a Sydney evening are different moments, and a single schedule will power off one group during the other group's afternoon. The clean design is to tag machines by the team that uses them, set each tag's schedule to that team's local zone, and let the morning-start runbook target each group on its own local morning. This is more setup than a single global schedule, but it is the only design that gives every team a sensible local rhythm, and it is exactly the design that a single forgotten time zone field silently breaks.

The third design decision is how to handle the machines that do not fit the common rhythm, the late-night batch box, the occasionally-used demo machine, the machine that one person needs on weekends. The temptation is to carve special schedules for each, which multiplies the configurations and the chances for error. The cleaner approach is to define a small number of named rhythms, perhaps a standard business-hours rhythm, an extended rhythm for teams that work later, and a no-schedule exemption for always-on machines, and assign every machine to one of them by tag. A machine that genuinely fits none of the named rhythms is rare, and treating it as a deliberate exception rather than a fresh bespoke schedule keeps the overall design legible. When someone asks why a machine powers off when it does, the answer should be the name of its rhythm, not a one-off configuration nobody remembers setting.

The fourth design decision is what to monitor and who sees it, because a schedule design that nobody watches will drift. The monitoring described earlier becomes a small dashboard the team owner reviews: how many machines are following each rhythm, how many are merely stopped rather than deallocated, how many lack a schedule that should have one, and roughly what the schedules are saving against the counterfactual of continuous running. That last figure, the estimated saving, is the number that keeps the design funded politically, because it converts an invisible cost discipline into a visible result. A team that can say its schedules save several thousand dollars a month has a much easier time defending the small friction the schedules impose than a team for whom the saving is an unmeasured article of faith.

Designed this way, the schedule stops being a per-machine afterthought and becomes a property of the team: a named rhythm, applied by tag, set in the team's zone, verified to deallocate, paired with a morning start, exempting the always-on machines, and watched on a small dashboard that reports both health and saving. That is the difference between a feature someone enabled once and a cost discipline the team actually owns.

## The verdict

Auto-shutdown is the highest-return, lowest-effort cost control Azure offers for idle machines, and it fails for exactly two reasons that the time-zone-and-deallocate rule names directly. It saves money only by deallocating, which it does by design, so the saving is real as long as the machine is powered off through the feature rather than from inside the guest, and it fires correctly only in the zone you set, which defaults to UTC and so is wrong for almost everyone who does not change it. Configure both correctly, verify both rather than assuming them, and you capture seventy percent or more of the compute cost of a business-hours machine for a configuration that takes minutes and, once expressed as code, maintains itself.

The complete setup is never just the toggle. It is the toggle plus the correct zone, plus a notification that gives users a chance to defer, plus a verification that the machine truly deallocates, plus an auto-start mechanism because Azure deliberately leaves the morning to you, plus, at scale, a code or policy approach that removes the manual step where the time zone error enters and a monitor that catches the machine that is merely stopped. Treat auto-shutdown as a verified configuration rather than a one-click setting, work the InsightCrunch auto-shutdown setup checklist top to bottom, and the feature delivers the saving it promises instead of the saving it appears to. The difference between those two outcomes is entirely in the two fields and the one verification that this guide exists to get right.

## Frequently Asked Questions

### Q: How do I configure Azure VM auto-shutdown correctly from start to finish?

Open the machine in the portal, select Auto-shutdown under Operations, and toggle it on. Enter the local clock time you want the machine to power off in 24-hour form, then, before saving, set the time zone field to the zone that time was expressed in, because it defaults to coordinated universal time and that default is the most common reason a schedule fires at the wrong hour. Optionally enable a notification with a fifteen to thirty minute lead so anyone working can defer. Save, then verify by setting a near-future test time and confirming the machine powers off when expected, and by checking the power state reads deallocated rather than merely stopped. Finally, add a separate auto-start mechanism if the machine needs to be available in the morning, since the built-in feature handles only the power-off half of the day. That full sequence, not just the toggle, is what a correct setup looks like.

### Q: Why does my Azure VM auto-shutdown fire at the wrong time zone?

The schedule interprets your chosen clock value in the time zone stored in its configuration, and that field defaults to coordinated universal time rather than your local zone. If you entered an evening time but left the zone at the default, the machine powers off at that clock value interpreted as UTC, which lands somewhere unhelpful in your actual day, offset from your intention by however many hours separate your zone from UTC. The schedule does not read your browser's time zone or infer it from the machine's region; it uses only the explicit zone field. The fix is to open the time zone selector and choose the zone your time was expressed in, then re-verify with a near-future test. The reliability of the wrong timing is the tell: a machine that fires at exactly the wrong hour every single day has a fixed zone offset, not a glitch, and that offset almost always matches the gap between UTC and your local zone.

### Q: Does Azure VM auto-shutdown actually deallocate the machine and stop billing?

Yes. Auto-shutdown issues a control-plane deallocation, which both halts the guest and releases the underlying compute reservation, so the machine reaches the Stopped (deallocated) state and the per-second compute charge stops within a minute or two. This is the behavior that makes the feature worth using, because deallocation is precisely what stops the compute meter. You continue to pay for the managed disks that remain provisioned and for any static public IP you reserved, since those have to persist for the machine to come back as it was, but on most machines the disk and address costs are a small fraction of the compute cost, so deallocation captures the large majority of the available saving. The distinction matters because not every way of turning a machine off deallocates it; a shutdown issued from inside the guest stops the machine without releasing the compute reservation, and that does not stop the bill.

### Q: Can I get a notification before my VM is automatically shut down?

Yes. The notification section of the auto-shutdown configuration lets you enable a pre-shutdown warning and set how many minutes before the scheduled power-off it is sent. A lead time of fifteen to thirty minutes is the practical range, long enough that someone mid-task can save work and decide whether to defer, short enough that the warning is clearly about the imminent shutdown. You can deliver the message to an email address or to a webhook, and the standard message includes a link that lets the recipient postpone the shutdown by a chosen interval if they are still working. The webhook option is the more powerful, because it can route the warning into a team chat channel so everyone sees it, or trigger an automated check before the machine powers off. Enabling the notification even on unattended machines is useful because its daily arrival is evidence the schedule is still alive and behaving.

### Q: How do I automatically start my Azure VM in the morning?

Azure does not include a built-in auto-start, so you add one yourself, most commonly with an Azure Automation runbook scheduled to run on weekday mornings. Create an Automation account, give it a managed identity, grant that identity the Virtual Machine Contributor role on the resource group holding the machines, and write a short runbook that starts the machines you want, ideally targeted by a tag so it scales without hardcoding names. Schedule the runbook to run before the earliest realistic start of the working day, with enough margin that nobody arrives to a machine still booting. Alternatives include a Logic App, which suits teams wanting visual workflows and conditional logic such as skipping holidays, and the packaged start-and-stop solution Microsoft maintains, which deploys the scheduling machinery for you. Whichever you choose, the morning start is always a separate mechanism from auto-shutdown, so a complete daily cycle is two pieces working together.

### Q: Why does my VM still cost money after I shut it down from inside Windows or Linux?

Because shutting a machine down from inside its guest operating system does not release the compute reservation. The guest halts and the screen goes dark, but the machine reports as Stopped rather than Stopped (deallocated), and Azure continues billing for the virtual CPU and memory because those resources are still reserved for you. Only a control-plane deallocation returns the compute resources to the fabric and stops the compute charge, and that is what auto-shutdown performs. This catches many people who diligently shut machines down every evening from the Start menu or the command line and see no change in their bill, then wrongly conclude that turning machines off does not save money in Azure. It does, but you have to deallocate, not just shut down the guest. The reliable check is the power state: a machine is only saving you money when its status reads PowerState/deallocated.

### Q: What is the difference between the time field and the time zone field in auto-shutdown?

The time field sets the clock value at which the machine powers off, entered in 24-hour HHmm form, and the time zone field sets the frame of reference in which that clock value is interpreted. On their own, neither is sufficient: the clock value 1900 is meaningless until paired with a zone, because 1900 in coordinated universal time and 1900 in Central time are different moments. The scheduling system takes the clock value, interprets it in the stored zone, and fires when that local moment arrives. The reason this trips people is that the two fields are entered separately and the time field feels like the whole job, so the zone is left at its UTC default and the schedule fires at the wrong hour. Treat them as a pair that must both be correct, and remember that the zone is the field the default gets wrong.

### Q: How do I verify that auto-shutdown is working correctly?

Verify the two halves of the behavior separately. To verify the timing without waiting a full day, temporarily set the schedule to a few minutes in the future in the correct zone, save, and watch whether the machine powers off at that local moment; if it does, the zone is right, and you set the schedule back to its real time afterward. To verify the deallocation, check the machine's power state after the schedule fires using the instance view, which should return PowerState/deallocated; if it returns PowerState/stopped instead, the machine was powered off some other way and the compute charge is still running. For a fleet, a Resource Graph query that lists machines whose power state is stopped but not deallocated gives you the report of machines that are leaking money. Running that timing test on setup and the deallocation check on a schedule turns verification into a habit rather than an afterthought.

### Q: How do I apply auto-shutdown to many VMs at once without configuring each one?

Define the schedule as code and deploy it through your pipeline, or enforce it with policy. The code approach writes the schedule once as a Bicep module or a Terraform resource that takes the machine name, time, and zone as parameters, instantiated per machine with the zone set per team or region, so the configuration is reviewable and a wrong zone is caught in a pull request. The policy approach audits for machines lacking a schedule and can remediate them automatically, making the schedule a standing guardrail across a whole scope, paired with an exclusion list so production and always-on machines are exempt. The template approach, which fits development and test machines that come and go, builds the schedule into the image or the lab definition so every machine is born with it. All three remove the manual per-machine step where the time zone error enters, which is the real benefit of doing it at scale.

### Q: Does daylight saving time affect when auto-shutdown fires?

It does, but in the way you want, provided you set a named zone rather than trying to compensate manually. The Windows time zone identifiers the schedule uses, like Central Standard Time and Pacific Standard Time, are full zones that observe daylight saving where the underlying region does, so despite the word Standard in the name they shift their offset across the year following local rules. A schedule set to an evening time in Central Standard Time fires at that local evening time all year, adjusting automatically across the spring and autumn transitions. The trap is for someone who distrusts the name and tries to outsmart it by entering a fixed UTC offset or a manually adjusted clock value, which then breaks on exactly the two transition days the platform would have handled. The correct approach is to pick the zone that matches where you are and let the platform manage the seasonal shift on its own.

### Q: Which VMs should not have an auto-shutdown schedule?

Any machine whose availability matters around the clock should be exempt: production services, build agents that run overnight jobs, shared services someone might need at any hour, and anything backing a workload that does not have predictable off-hours. Auto-shutdown is for machines that are genuinely idle outside business hours, which in practice means development and test boxes. The failure to guard against is a well-intentioned cost initiative applying a blanket schedule across a subscription and powering off a machine whose uptime is essential, which converts a cost saving into an incident. When you apply schedules at scale through policy or code, pair the enforcement with a clear exclusion mechanism, typically a tag, so always-on machines are explicitly exempt. For those machines, continuous running is a deliberate cost, often best handled with a reservation, not an oversight to be corrected by a schedule.

### Q: Where does the auto-shutdown schedule actually live as an Azure resource?

The schedule is implemented as a resource in the Microsoft.DevTestLab provider namespace, specifically a global schedule named for the machine, even on a plain machine that is not part of any lab. This surprises engineers who go looking for the setting and find it living under a lab-services provider rather than under the compute provider where a machine setting would be expected. It is harmless and you do not need a lab to use it, but knowing where it lives explains why the command-line and infrastructure-as-code forms reference that provider, and why a search of a machine's compute resources for the schedule comes up empty. The resource name follows a predictable pattern based on the machine name, which is what lets you target it directly from a command or a template. Understanding this also clarifies why a machine recreated from a template that omits the schedule loses it, since the schedule is a separate resource, not an intrinsic property of the machine.

### Q: How much can auto-shutdown actually save on a development VM?

For a machine that only needs to run during business hours, the saving is roughly the proportion of the week it would otherwise sit idle, which for a ten-hour weekday schedule is around seventy percent of the compute cost. A machine that costs about a dollar an hour and runs continuously is roughly 720 hours a month; running it only ten hours a day on weekdays is around 217 hours, a reduction of close to 500 dollars a month on a single machine, subject to the actual rate for your size and region. Storage costs for the disks persist whether the machine runs or not, but on most development machines disk cost is a small fraction of compute, so the net saving is dominated by the hours removed. Across a team of ten similar machines the monthly saving approaches several thousand dollars, which is why this lever ranks first in most cost work: the effort is minutes and the saving is large and recurring.

### Q: Can I use auto-shutdown together with spot VMs and reservations?

Auto-shutdown stacks cleanly with spot capacity because the two attack different parts of the bill: the spot price reduces the hourly rate, and the schedule reduces the hours, so a spot-priced machine with an evening auto-shutdown is close to the cheapest way to run a machine needed only during working hours. The one nuance is that the platform can evict a spot machine outside your schedule, deallocating it when capacity is reclaimed, which your morning start runbook handles identically since it simply starts whatever is deallocated. Reservations are the opposite case and should not be combined with auto-shutdown on the same machine, because a reservation commits you to paying for the size for a term whether or not it runs, so deallocating a reserved machine overnight wastes the reservation during those hours. Use reservations for the always-on machines you exempt from schedules, and auto-shutdown for the intermittent ones you would never reserve.

### Q: Why does my VM start back up on its own after auto-shutdown?

When a machine deallocates on schedule and then comes back up unbidden, something other than auto-shutdown is starting it, because the feature only ever powers machines off, never on. The usual culprit is another controller with its own opinion about the machine's power state, such as an autoscale plan that maintains a minimum number of active instances, a session-management system that restarts hosts to meet availability, or a separate start runbook firing on an unexpected schedule. Two systems with opposite intentions about the same machine will fight, and the auto-shutdown schedule is rarely the one at fault, since deallocating is exactly what you asked it to do. The fix is to find the other controller and reconcile the two so only one owns the machine's power state. Checking the activity log for the identity that issued the start operation usually identifies which system is bringing the machine back up.

### Q: Can Azure Backup run while a VM is deallocated by auto-shutdown?

Yes. Azure Backup operates on the machine's disks and can protect a machine that is deallocated, so an evening auto-shutdown does not prevent an overnight backup from running. The two scheduled behaviors are complementary rather than conflicting once you understand that backup takes its snapshot from the disks regardless of the machine's power state, so a machine that is powered off all night is still backed up on its own schedule. The configuration to get right is simply to let each schedule run independently, and to be aware that an application-consistent backup, which coordinates with the guest to flush in-flight data, requires the machine to be running, so a machine that is deallocated at backup time gets a crash-consistent backup of its disks rather than an application-consistent one. For most development machines that is acceptable, but if application consistency matters, align the backup window with a time the machine is running rather than deallocated.

### Q: What permissions do I need to configure auto-shutdown?

You need write access to both the machine and the schedule resource, which the Virtual Machine Contributor role provides, since it includes the actions required to create and modify the DevTestLab schedule associated with the machine. An account with only read access can open the configuration blade, enter values, and find that the save quietly fails, which is a common and confusing setup-time symptom that traces directly to a permissions gap rather than to anything wrong with the values entered. If you are adding an auto-start runbook, the Automation account's managed identity needs its own grant, specifically the ability to read and start machines in the relevant scope, which the same Virtual Machine Contributor role provides when assigned on the resource group holding the machines. Scope that identity to exactly the resource group it needs rather than the whole subscription, keeping the automation principal at least privilege, which is the standard discipline for any automated actor acting on your resources.

### Q: How do I monitor that auto-shutdown stays configured correctly across a fleet over time?

Audit it as an ongoing invariant with Azure Resource Graph, because schedules get disabled, machines get recreated without them, and wrong zones get copied between machines. Run two recurring audits that mirror the two halves of the rule. The first lists machines tagged for scheduling that lack an enabled shutdown schedule, which surfaces machines that should be powering off but are not configured to. The second filters schedules whose zone is the default coordinated universal time in teams that do not operate there, which surfaces the more insidious case of a schedule that exists but fires at the wrong local hour. Alerting when either query returns rows turns the setup checklist into a continuously enforced standard rather than a thing that was true once. The investment is worthwhile precisely because auto-shutdown's failures are silent: nothing throws an error, so timing and cost are the only evidence until monitoring makes the drift visible.
