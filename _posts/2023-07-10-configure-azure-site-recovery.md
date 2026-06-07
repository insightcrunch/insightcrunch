---
layout: post
title: "Set Up Azure Site Recovery for DR"
page_title: "Azure Site Recovery Setup Guide: Configure Replication, Recovery Plans, and Test Failover for Disaster Recovery"
date: 2023-07-10
categories: ["Technology"]
tags: ["Azure", "Azure Site Recovery", "Disaster Recovery", "Architecture", "Cloud Computing"]
excerpt: "Azure Site Recovery setup means more than enabling replication. Build a replication policy, order recovery plans, and prove DR with a real test failover."
image: "/assets/images/blog/blog-41.webp"
reading_time: 61
author: "ryan-walsh"
last_updated: 2023-07-10
lang: en
---
A green replication health icon is the most dangerous thing in your disaster recovery posture, because it looks like readiness and is not. Azure Site Recovery setup tends to stop at the moment the portal reports that a virtual machine is protected and the recovery points are flowing, and the team marks the workload as covered. Then the primary region has a bad afternoon, someone opens the recovery plan that was never built, and the failover that was supposed to be a button press becomes an improvised scramble across a dozen machines that come up in the wrong order with no network to land in. The gap between replication being healthy and a region loss being survivable is the entire subject of this article, and closing it is the difference between disaster recovery on paper and disaster recovery you can actually run.

![Azure Site Recovery setup for disaster recovery replication and test failover - Insight Crunch](/assets/images/blog/blog-41.webp)

The claim worth fixing in your head before any commands run is the test-failover rule: disaster recovery readiness is proven by a non-disruptive test failover, not by replication health alone. Replication tells you that bytes are leaving the primary region and landing in the secondary. It says nothing about whether those bytes assemble into a bootable machine, whether that machine can reach a domain controller, whether the application tier comes up after the database tier, or whether anyone has the runbook to coordinate the whole thing under pressure. A test failover answers every one of those questions in an isolated network without touching production, and a setup that skips it has bought storage replication and called it a recovery strategy. Everything below is organized around getting you to a rehearsed, repeatable failover rather than a healthy-looking replication dashboard.

## What Correct Site Recovery Configuration Buys You

Azure Site Recovery is a replication and orchestration service. Its job is to continuously copy the disks of a running machine to a secondary region, keep a window of recovery points so you can fail over to a moment before a problem started, and then coordinate the failover of many machines as an ordered, scripted operation rather than a manual one. When the configuration is right, a regional outage becomes a planned event: you trigger a recovery plan, the machines boot in dependency order into a network that already exists, the application answers, and you fail back and resynchronize when the primary region returns. When the configuration is wrong, each of those guarantees quietly evaporates while the dashboard still shows green.

The service sits in a different category from backup, and conflating the two is the most common conceptual error engineers bring to it. Backup, which the [Azure Backup configuration guide](/2023/07/03/configure-azure-vm-backup/) covers in depth, exists to restore a point in time after corruption, accidental deletion, ransomware, or a bad deployment. Its recovery objective is measured in hours and its retention in months or years. Site Recovery exists to move a running workload to another region within minutes of an outage, with a recovery point objective measured in minutes and a retention window measured in hours. You need both, for different failure classes, and a mature [disaster recovery architecture on Azure](/2024/07/22/azure-disaster-recovery-architecture/) treats them as complementary rather than interchangeable. Reaching for replication when you needed a six-month-old restore point, or for backup when a region just disappeared, is the symptom of having never drawn that line clearly.

### What does Site Recovery actually replicate and how?

For an Azure-to-Azure scenario, the service installs the Mobility extension on each protected VM, takes an initial crash-consistent copy of every disk into a cache storage account, and then ships only changed blocks continuously. Recovery points are assembled in the target region from that change stream, so failover means spinning up a VM from an already-staged set of disks.

The mental model that keeps the rest of this article coherent is a pipeline with three stages. The first stage is replication: change tracking on the source disks, a cache storage account in the source region that buffers writes, and a managed-disk target in the secondary region that holds the replica. The second stage is the recovery point: at the cadence your policy defines, the service crystallizes the change stream into a labeled point you can fail over to, optionally with an application-consistent variant that flushes the application's in-memory state to disk first. The third stage is orchestration: the recovery plan that groups machines, orders their boot, and injects scripts or manual pauses so dependencies satisfy in sequence. A correct setup configures all three deliberately. A weak setup configures the first, accepts defaults on the second, and never builds the third.

## The InsightCrunch Site Recovery Setup Checklist

Before any portal blade opens, it helps to have the whole sequence in view as a named artifact, because the order matters and skipping a stage is how teams end up with replication and nothing else. The InsightCrunch Site Recovery setup checklist runs in five stages, each with the gotcha that bites people who treat it as optional. Enable replication, with the gotcha that the target region's networking and resource group must be decided up front rather than accepted as auto-generated names you will never find again. Set the replication policy, with the gotcha that the default recovery-point retention and app-consistent frequency rarely match the objective you actually committed to. Build recovery plans with ordering, with the gotcha that machines default into a single group and boot simultaneously unless you split them into ordered groups. Run a test failover into an isolated network, with the gotcha that pointing it at a network reachable from production can corrupt the very thing you are protecting. Plan failback and reprotect, with the gotcha that a failover you cannot cleanly reverse leaves you stranded in the secondary region.

This checklist is the spine of the article. Each stage below expands into the prerequisites, the commands, the settings the defaults get wrong, and the verification that proves the stage actually did its job. Treat the five as a pipeline where each stage depends on the one before, and resist the strong pull to declare victory after stage one.

| Stage | What you configure | The default that bites | How you verify it |
|-------|-------------------|------------------------|-------------------|
| 1. Enable replication | Source VMs, target region, target resource group, cache storage, target network | Auto-named target resources you cannot locate later | Replication health reaches "Protected" with recent recovery points |
| 2. Replication policy | Recovery-point retention, app-consistent snapshot frequency | Retention and snapshot cadence that miss your stated objective | Policy values match the RPO and retention you committed to |
| 3. Recovery plans | Machine groups, boot order, pre and post scripts | All machines in one group booting at once | Plan shows dependency-ordered groups, not a flat list |
| 4. Test failover | Isolated target network, recovery point selection | A target network reachable from production | App boots and answers in the isolated network, then cleanup |
| 5. Failback and reprotect | Reverse replication, reprotect direction | No reverse path planned, stranding you in secondary | Reprotect succeeds and a return failover is rehearsed |

## Prerequisites and the Correct Order of Operations

The prerequisites for an Azure-to-Azure deployment are less about software you install and more about decisions you make before the first machine replicates, because several of them are awkward to change once replication is running. You need a secondary region chosen deliberately, ideally the paired region for your primary unless a specific compliance or latency reason argues otherwise, since paired regions receive sequential platform updates and have replication-friendly proximity. You need a Recovery Services vault, which is the same resource type that backup uses but should generally be a separate vault for replication so the two workloads do not contend for the same scaling and policy surface. You need the target-side networking decided in advance: the virtual network the failed-over machines will land in, the subnets, and the IP scheme, because while you can let the service generate these, you will be debugging name resolution and routing during an outage if you do.

The order of operations is the part teams most often get wrong, usually by enabling replication first and discovering the networking and identity decisions afterward. The correct sequence starts with the target environment. Decide and, where practical, pre-create the target resource group, the target virtual network, and any subnets the application needs, so that when you enable replication you map source networks to real target networks rather than placeholders. Establish the vault and confirm the managed identity or service principal that the service will use has the roles it needs in both the source and target scopes. Only then enable replication on the first workload, deliberately as a pilot, and watch it reach a protected state with healthy recovery points before you scale to the rest of the estate. Define the replication policy with intent rather than accepting the default. Build the recovery plans that encode the boot order. Finally, and this is the stage that converts the whole effort from theoretical to proven, run a test failover.

### Which region should I replicate to?

Default to your primary region's Azure paired region unless a concrete constraint overrides it. Paired regions get sequential maintenance and data-residency alignment, which reduces the chance both regions update or fail together. Override the pairing only for data-sovereignty rules, a latency requirement, or a service that is unavailable in the pair.

A subtle prerequisite that catches people is capacity and quota in the target region. Failover spins up real compute, and if your subscription's vCPU quota in the secondary region is sized only for the trickle of test machines you have run there, a real failover of the full estate will hit a quota wall at the worst possible moment. The fix is to confirm and, where needed, request quota in the target region sized for the full failed-over footprint, treating the secondary region as a place that must hold your entire production workload even though it normally holds none of it. This is also why a clear view of the [virtual machine sizing and behavior model](/2022/01/03/azure-virtual-machines-complete-guide/) matters here: the target VM sizes the service selects must exist and be available in the target region, and a size that is plentiful in your primary region is not guaranteed to be plentiful in the pair.

Identity and permissions form the other prerequisite that fails silently. The service needs permission to read the source machines, create resources in the target region, and write into the cache and target storage. When replication mysteriously fails to enable or a recovery plan cannot create the target VM, the cause is frequently a missing role assignment on the target resource group or a managed identity that was never granted access to the vault. Granting the correct scoped roles before enabling replication, rather than reacting to a failure during a drill, keeps the setup honest.

## Stage One: Enable Replication With Working Commands

Enabling replication is the stage that produces the reassuring green icon, and precisely because it is the satisfying part, it is where setups tend to stop. The work here is to enable it in a way that records every target-side decision explicitly, so that the eventual failover lands machines into a known network with known names rather than into auto-generated resources you cannot reason about during an incident.

In the portal, the path begins inside the Recovery Services vault under the Site Recovery section, where you choose to replicate Azure virtual machines, select the source region and the specific machines, and then map every target attribute. The target resource group, the target virtual network, the cache storage account, and the replication policy each get a field, and the temptation is to accept the values the wizard pre-populates. Resist it for the networking and resource group: type in the target VNet you pre-created, the subnet the application expects, and a resource group whose name you will recognize at three in the morning. The cache storage account can usually take the default, but even there, knowing which account buffers the change stream helps when you later debug replication lag.

The command-line path is what you will actually want for anything beyond a handful of machines, because it is repeatable and reviewable. Azure CLI exposes the workflow through the `az site-recovery` command group, and a representative enablement looks like this:

```bash
# Variables for the source and target topology
VAULT_RG="rg-dr-vault"
VAULT_NAME="rsv-dr-eastus"
SOURCE_RG="rg-prod-app"
TARGET_RG="rg-dr-app"
TARGET_REGION="westus"
TARGET_VNET="/subscriptions/<sub>/resourceGroups/rg-dr-network/providers/Microsoft.Network/virtualNetworks/vnet-dr"
TARGET_SUBNET="app-subnet"
CACHE_STORAGE="/subscriptions/<sub>/resourceGroups/rg-dr-vault/providers/Microsoft.Storage/storageAccounts/stcachedr"
POLICY="policy-prod-24h"

# Enable replication for a single VM into the target region
az site-recovery protection-container-mapping create \
  --resource-group "$VAULT_RG" \
  --vault-name "$VAULT_NAME" \
  --fabric-name "asr-a2a-default-eastus" \
  --protection-container "asr-a2a-default-eastus-container" \
  --name "a2a-policy-mapping" \
  --policy-id "$POLICY"
```

The exact parameter surface for Azure-to-Azure enablement has shifted across CLI versions, and Microsoft has moved some operations between the `az site-recovery` group and the older PowerShell `Az.RecoveryServices` module. Rather than treat any single flag set as eternal, confirm the current parameter names against the installed module version before scripting at scale, and prefer PowerShell for Azure-to-Azure enablement where the CLI coverage lags. A PowerShell enablement of an Azure VM looks like this:

```powershell
# Resolve the vault and set context
$vault = Get-AzRecoveryServicesVault -Name "rsv-dr-eastus" -ResourceGroupName "rg-dr-vault"
Set-AzRecoveryServicesAsrVaultContext -Vault $vault

# Resolve fabrics, container, and the protectable VM
$primaryFabric = Get-AzRecoveryServicesAsrFabric -Name "asr-a2a-default-eastus"
$recoveryFabric = Get-AzRecoveryServicesAsrFabric -Name "asr-a2a-default-westus"
$protectionContainer = Get-AzRecoveryServicesAsrProtectionContainer -Fabric $primaryFabric

# Map disks and enable replication with the chosen policy
$vmId = "/subscriptions/<sub>/resourceGroups/rg-prod-app/providers/Microsoft.Compute/virtualMachines/vm-app01"
$policy = Get-AzRecoveryServicesAsrPolicy -Name "policy-prod-24h"

New-AzRecoveryServicesAsrReplicationProtectedItem `
  -AzureToAzure `
  -AzureVmId $vmId `
  -Name "vm-app01" `
  -ProtectionContainerMapping $mapping `
  -RecoveryResourceGroupId "/subscriptions/<sub>/resourceGroups/rg-dr-app" `
  -RecoveryAzureNetworkId $targetVnetId `
  -RecoveryAzureSubnetName "app-subnet"
```

What both paths share is that the target network, subnet, and resource group are named explicitly. That single discipline removes most of the failover-day surprises, because the machine that boots in the secondary region lands somewhere you designed rather than somewhere the service guessed.

### How long does the initial replication take?

Initial replication copies every disk byte once, so its duration scales with total provisioned disk size and the bandwidth between regions, typically hours for a multi-terabyte machine. After the seed completes, only changed blocks ship, so steady-state replication is light. Plan the first sync as a background activity, not a quick task.

The verification that this stage worked is specific and worth waiting for. The protected item should reach a state the portal labels as protected or healthy, the replication health should report no errors, and recovery points should begin accumulating at the cadence your policy defines. If the protected item sits in a continuous synchronization state long past the initial seed, the usual culprits are throttled bandwidth, a cache storage account that is hitting its own limits, or a source disk with a churn rate that exceeds what the link can carry. None of these is fatal, but each is a real constraint that a test failover would eventually expose, which is exactly why you do not stop here.

## Stage Two: The Replication Policy, RPO, and the Settings Defaults Get Wrong

A replication policy is a small object with outsized consequences, because it governs how far back in time you can recover and how that recovery behaves. Two settings carry most of the weight. The recovery-point retention window determines how many hours of labeled points the service keeps in the target region, which sets the ceiling on how far back you can fail over if a problem went unnoticed for a while. The application-consistent snapshot frequency determines how often the service quiesces the application to produce a point you can trust to be transactionally clean rather than merely crash-consistent. Both have defaults, and both defaults are chosen to be safe and inexpensive rather than to match the objective your business actually committed to.

The recovery point objective for Azure-to-Azure replication is, in practice, low, because the service ships changes continuously rather than on a fixed schedule. Crash-consistent points are generated frequently, so the realistic RPO for most workloads sits in the range of minutes rather than the longer intervals you would see in a snapshot-based design. What the policy controls is not the floor of how fresh a point can be, but the retention of how many points are kept and how often the more expensive application-consistent variant is produced. The error teams make is to read the low achievable RPO as proof that the policy is fine, and to leave the retention window and application-consistent frequency at values that do not survive contact with a real recovery requirement.

Consider what retention actually buys. If your retention window is short and a corruption was introduced and replicated before anyone noticed, every retained point may already contain the corruption, leaving you with nothing clean to fail over to. This is the boundary where replication and backup stop overlapping, because the longer restore history that the [VM backup configuration](/2023/07/03/configure-azure-vm-backup/) provides is the right tool for recovering from a problem older than your replication retention. Sizing the retention window is therefore a question of how quickly you would detect a problem and want to fail over to a point before it, balanced against the storage cost of keeping more points. A policy is correct when its retention reflects that detection-to-decision window rather than a default someone never examined.

Creating a policy by command keeps the values explicit and reviewable:

```powershell
# Create an Azure-to-Azure replication policy with explicit retention and app-consistent cadence
New-AzRecoveryServicesAsrPolicy `
  -AzureToAzure `
  -Name "policy-prod-24h" `
  -RecoveryPointRetentionInHours 24 `
  -ApplicationConsistentSnapshotFrequencyInHours 4
```

```bash
# Azure CLI equivalent for an A2A policy
az site-recovery policy create \
  --resource-group "rg-dr-vault" \
  --vault-name "rsv-dr-eastus" \
  --name "policy-prod-24h" \
  --provider-specific-input '{"a2a": {"app-consistent-frequency-in-minutes": 240, "recovery-point-history-in-minutes": 1440}}'
```

### What RPO and RTO does Site Recovery actually target?

Site Recovery targets a recovery point objective of minutes for Azure-to-Azure replication, because changes ship continuously. The recovery time objective, how long the failover itself takes, depends on your recovery plan: boot order, script duration, and machine count. Replication sets the RPO; your orchestration design sets the RTO.

The distinction between RPO and RTO is where many setups reveal that they were never thought through end to end. RPO is a property of replication and the policy: how much data, measured in time, you might lose. RTO is a property of orchestration and is something you largely build rather than configure: how long it takes the workload to be serving again after you decide to fail over. A policy with a low RPO and a recovery plan that boots forty machines sequentially with long script timeouts can still produce an RTO measured in hours. The only honest way to know your RTO is to measure it during a test failover, which is the next reason the rehearsal is not optional. Application-consistent frequency interacts with both: more frequent application-consistent snapshots give you cleaner recovery points but add load on the source application during each quiesce, so the cadence is a deliberate trade between recovery cleanliness and steady-state impact rather than a value to maximize.

One default worth singling out is the multi-VM consistency option for groups of machines that must recover to the same shared point in time, such as the nodes of a distributed application or a database cluster. Without it, each machine has its own independent recovery points and a failover can land two tightly coupled machines at slightly different moments, which some applications tolerate and others do not. Enabling multi-VM consistency creates a replication group with shared, coordinated points, at the cost of additional overhead and the requirement that the grouped machines share a policy. Reaching for it indiscriminately wastes resources; ignoring it for a workload that genuinely needs a coordinated recovery point produces a failover that technically succeeds and functionally breaks.

## Stage Three: Recovery Plans and the Ordering That Makes Failover Coherent

A recovery plan is where Site Recovery stops being storage replication and becomes disaster recovery orchestration. Replication gets the disks to the other region; the recovery plan decides what happens when you push the failover button, in what order machines boot, what runs between those boots, and where a human is asked to confirm before the next group proceeds. A workload with healthy replication and no recovery plan can still be failed over machine by machine, but only by an operator who already knows the dependency graph by heart and has the time to execute it manually while the business waits. The recovery plan encodes that knowledge so the failover is a scripted operation rather than a feat of memory under stress.

The core mechanism is the group. Every machine in a recovery plan belongs to a numbered group, and groups boot in sequence: group one fully starts before group two begins. The default behavior, and the trap, is that all protected machines drop into a single group and therefore boot simultaneously, which is exactly wrong for any application with a dependency chain. A three-tier application wants its domain controllers and database tier in an early group, its application tier in a middle group that depends on the data tier being up, and its web or gateway tier in a final group. Building the plan means splitting machines into those ordered groups so the boot sequence respects the dependencies the application has at startup.

Between and within groups, the plan can inject two kinds of steps. A manual action pauses the failover and asks an operator to confirm something the automation cannot verify, such as a DNS change or a check that the database accepted connections, before the next group proceeds. An automated script, run through an Azure Automation runbook, performs a programmable action such as updating a load balancer, changing a connection string, or registering the failed-over machines in DNS. These steps are what turn a sequence of booting machines into a working application, because the machines coming up is necessary but rarely sufficient: something usually has to repoint traffic, update configuration for the new region, or wait for a service to become healthy before declaring the tier ready.

```json
{
  "recoveryPlan": "rp-prod-app",
  "groups": [
    {
      "groupNumber": 1,
      "role": "data-tier",
      "machines": ["vm-dc01", "vm-sql01", "vm-sql02"],
      "postSteps": [
        { "type": "ManualAction", "name": "Confirm SQL accepts connections" }
      ]
    },
    {
      "groupNumber": 2,
      "role": "app-tier",
      "machines": ["vm-app01", "vm-app02"],
      "preSteps": [
        { "type": "ScriptAction", "runbook": "Update-AppConnectionStrings" }
      ]
    },
    {
      "groupNumber": 3,
      "role": "web-tier",
      "machines": ["vm-web01", "vm-web02"],
      "postSteps": [
        { "type": "ScriptAction", "runbook": "Repoint-TrafficManager" }
      ]
    }
  ]
}
```

### How do recovery plans order the failover?

Recovery plans assign each machine to a numbered group, and groups boot strictly in sequence, so group two waits until group one finishes. Between groups you insert manual confirmations or Automation runbook scripts. This lets the database tier start, get verified, and have connection strings updated before the application tier ever boots.

The same recovery plan serves three operations, which is a design strength worth understanding. The plan you build for an unplanned failover is the same plan you use for a test failover and, with the direction reversed, the same structure that informs failback. This means the ordering and the scripts you invest in are exercised every time you run a test, so a team that drills regularly is continuously validating the exact orchestration it will rely on in a real outage. A recovery plan that exists only on paper, never run even as a test, is a hypothesis about your dependency order rather than a verified fact, and dependency assumptions are precisely the kind of thing that turns out to be wrong under load. Database replication concerns for the data tier specifically are better handled with the database-native mechanism described in the [SQL failover groups configuration](/2023/06/12/configure-azure-sql-failover-groups/), and a well-designed recovery plan coordinates with that rather than trying to replicate a managed database at the disk level.

The scripts deserve a note on idempotency and testing. A runbook that repoints DNS or rewrites a connection string will run during every test failover as well as during the real one, so it must be safe to run against the test environment without affecting production, and safe to run more than once. A script that hard-codes a production endpoint, or that fails the second time because it assumes a clean starting state, will either contaminate production during a test or break the failover during the real event. Writing these runbooks to detect their environment and to be repeatable is part of making the recovery plan trustworthy, not an optional refinement.

## Stage Four: The Test Failover That Proves Readiness

This is the stage the entire article has been building toward, because it is the one that converts a hopeful configuration into demonstrated readiness. A test failover spins up your replicated machines from a chosen recovery point into an isolated network, lets you confirm that the application actually comes up and works, and then cleans everything away, all without touching the production machines or interrupting ongoing replication. It is the single most valuable thing you can do with Site Recovery, and it is the step that distinguishes a team that has disaster recovery from a team that has a replication bill.

The non-negotiable rule of a test failover is isolation. The target network you fail over into must be isolated from production, because the test boots real copies of real machines that believe they are the production servers. If those copies can reach the production network, you can get duplicate machines answering for the same identities, two domain controllers fighting over the same directory, two database servers claiming the same role, or DNS and Active Directory replication carrying the test machines' state back into the real environment. The damage from a test failover into a connected network can be worse than the outage you were preparing for, which is a genuinely cruel irony for a safety exercise. The correct pattern is a dedicated, isolated virtual network in the target region with no peering or gateway connection back to production, used only for test failovers.

```bash
# Run a test failover for a recovery plan into an isolated network
az site-recovery recovery-plan test-failover \
  --resource-group "rg-dr-vault" \
  --vault-name "rsv-dr-eastus" \
  --recovery-plan-name "rp-prod-app" \
  --direction "PrimaryToRecovery" \
  --network-id "/subscriptions/<sub>/resourceGroups/rg-dr-isolated/providers/Microsoft.Network/virtualNetworks/vnet-dr-test" \
  --recovery-point-type "Latest"
```

```powershell
# PowerShell test failover for a recovery plan
$rp = Get-AzRecoveryServicesAsrRecoveryPlan -Name "rp-prod-app"
$testNetwork = Get-AzVirtualNetwork -Name "vnet-dr-test" -ResourceGroupName "rg-dr-isolated"

Start-AzRecoveryServicesAsrTestFailoverJob `
  -RecoveryPlan $rp `
  -AzureVMNetworkId $testNetwork.Id `
  -Direction PrimaryToRecovery
```

### How do I run a test failover without affecting production?

Run the test failover against an isolated virtual network in the target region that has no peering or VPN path back to production. The replicated machines boot there as copies, you validate the application, then run the cleanup operation to delete the test resources. Production and ongoing replication are never touched.

What you do during the test is where the value is realized, and a test failover that boots machines and is immediately cleaned up without anyone logging in has confirmed almost nothing. The point is to validate the things replication health cannot tell you. Log into the failed-over machines and confirm they booted to a usable state. Confirm the application tier can reach the data tier in the isolated network, which surfaces any hard-coded production endpoints that need to become runbook-driven. Confirm the recovery plan's boot order was actually correct rather than merely plausible, because a dependency you misjudged shows up here as a service that fails to start because the thing it needed was not up yet. Measure how long the whole sequence took, which is your real RTO and is almost always longer than the optimistic estimate. Record every gap, fix the recovery plan or the runbooks, and run the test again. This loop, run on a schedule rather than once at setup time, is what keeps the recovery plan aligned with an application that changes underneath it.

The cleanup step matters as much as the failover. After the test, you run a test failover cleanup operation, which deletes the test machines and resources and lets you record notes about what the test found. Skipping cleanup leaves orphaned machines accruing cost and, worse, leaves the protected items in a state that complicates the next operation. A disciplined test is failover, validation, notes, cleanup, in that order, every time. The cadence question of how often to run it has no universal answer, but a workload whose dependency graph changes with every release deserves a test failover often enough that no major change ships unrehearsed, and a stable workload still deserves a periodic test because the platform, the images, and the people all drift over time.

## Stage Five: Failover, Failback, and Reprotect

The four stages so far prepare you to fail over and prove you can. The fifth stage is the part of the lifecycle that an enabling-replication mindset forgets entirely: what happens after a real failover, when the primary region recovers and you need to bring the workload home. A failover you cannot cleanly reverse leaves you running production out of your secondary region indefinitely, which is survivable but is not where you designed the workload to live, and which often means running without the very disaster recovery protection you just used, because nothing is now replicating the secondary back to anywhere.

An unplanned failover is the operation you run when the primary region is already gone. You select the recovery plan, choose the recovery point, latest or a specific application-consistent point, and commit the failover. The machines boot in the target region in the order the plan defines, the scripts run, and the workload comes up in the secondary region. A planned failover, by contrast, is what you run for a rehearsed migration or a maintenance event where the primary is still healthy: it first synchronizes any final changes so there is zero data loss, then moves the workload. Both leave you in the same place afterward: running in the secondary region with the replication relationship now pointing the wrong way, from a source region that may no longer be the one holding your live workload.

Reprotect is the operation that fixes the direction. After a failover, reprotect establishes replication from the now-active secondary region back toward the original primary, so that the workload running in the secondary region is itself protected and a future failback has somewhere to go. This is the step that restores your disaster recovery posture after using it, and skipping it means the workload is running unprotected in the region you failed into. Reprotect requires the original region to be available again and may need to resynchronize disks, which takes time proportional to how much changed while you were running in the secondary region.

### How do I fail back to the primary region after a disaster?

Failback is a reprotect followed by a failover in the reverse direction. Once the primary region is healthy, you reprotect to replicate the secondary region's live workload back to the primary, let the disks resynchronize, then run a failover from secondary to primary. After failback, reprotect again to restore the original replication direction.

```powershell
# After the primary region recovers, reprotect to reverse replication
$rpi = Get-AzRecoveryServicesAsrReplicationProtectedItem -Name "vm-app01" -ProtectionContainer $container
Update-AzRecoveryServicesAsrProtectionDirection `
  -AzureToAzure `
  -ReplicationProtectedItem $rpi `
  -RecoveryAzureResourceGroupId "/subscriptions/<sub>/resourceGroups/rg-prod-app"

# Once resync completes, fail back by failing over in the reverse direction
$rp = Get-AzRecoveryServicesAsrRecoveryPlan -Name "rp-prod-app"
Start-AzRecoveryServicesAsrUnplannedFailoverJob `
  -RecoveryPlan $rp `
  -Direction RecoveryToPrimary
```

The full lifecycle, then, is a loop rather than a one-way trip: replicate primary to secondary, fail over to secondary, reprotect secondary to primary, fail back to primary, and reprotect primary to secondary to return to the starting posture. A complete setup has rehearsed enough of this loop, at least through reprotect, that the team knows the failback path works and is not discovering it for the first time while running production in an unfamiliar region. The commit operation deserves a final mention: after a failover, the operation is not finalized until you commit it, which discards the other recovery points and locks in the one you failed over to. Until you commit, you retain the option to change the recovery point. Committing is the deliberate act of saying this is the point we are keeping, and it precedes reprotect.

## The Common Misconfigurations and Their Symptoms

Several failure patterns recur across teams, and each maps to a specific stage of the checklist that was skipped or accepted by default. Naming them as patterns makes them easier to catch in your own setup before an outage does the catching for you.

The first and most common pattern is healthy replication with no recovery plan and no test failover ever run. The symptom is a dashboard full of green protected items and a complete absence of any artifact that describes how to actually fail over. The setup looks complete to a glance and is in fact only stage one of five. The fix is to build the recovery plan that encodes the boot order and to run a test failover, because until both exist, the workload is not recoverable in any coordinated way. This is the pattern the test-failover rule exists to prevent, and it is worth auditing every protected workload against it specifically.

The second pattern is a test failover, or worse a real failover, pointed at a network reachable from production. The symptom ranges from duplicate machine identities and Active Directory conflicts to outright corruption of the production directory as the test machines replicate their state back. The fix is architectural: a dedicated isolated network for test failovers with no path to production, verified before the first test rather than discovered after a bad one. This is the one misconfiguration where the safety exercise itself causes the damage, which makes it the one to be most careful about.

The third pattern is a recovery plan with no meaningful ordering, where every machine sits in a single group and boots at once. The symptom appears during the test failover as services that fail to start because their dependencies were not yet up: the application tier cannot reach the database because the database machine was still booting, or a service times out waiting for a domain controller. The fix is to split the machines into ordered groups that respect the dependency chain and to insert the manual checks or scripts that confirm each tier is ready before the next begins.

The fourth pattern is an RPO target the policy does not actually meet, usually because someone wrote a recovery point objective into a disaster recovery document without checking what the replication and retention settings deliver. The symptom is a discovery, during an audit or an incident, that the retention window is too short to reach a clean point or that the achievable data-loss window does not match the commitment. The fix is to reconcile the stated objective with the policy's retention and the achievable RPO, adjusting the policy or the objective until they agree, and to record the real numbers rather than aspirational ones.

The fifth pattern is confusing Site Recovery with backup, reaching for replication to recover from a problem that needed a point-in-time restore from weeks ago, or treating backup as a substitute for the rapid regional failover that only replication provides. The symptom is a recovery attempt that fails because the right tool was never configured for the failure class at hand. The fix is conceptual clarity, reinforced by configuring both, with replication sized for regional failover and backup sized for long-horizon restore, as the [disaster recovery architecture guide](/2024/07/22/azure-disaster-recovery-architecture/) lays out across the full design.

The sixth pattern is target-region capacity or permission gaps that lie dormant until a real failover. The symptom is a failover that partially succeeds and then stalls, with some machines unable to allocate because the target region lacks quota for the chosen VM size, or a recovery plan script that fails because the automation identity lacks a role it needs. The fix is to size target-region quota for the full failed-over footprint and to grant the required roles before a drill, then to confirm both during the test failover so they are never discovered during the real one.

## Making the Configuration Repeatable as Code

A Site Recovery setup that lives only in portal clicks is fragile in a way that defeats its own purpose, because the entire point of disaster recovery is reliability under stress, and a configuration nobody can reproduce is the opposite of reliable. When the engineer who clicked through the wizard leaves, when a new workload needs the same protection, or when the configuration drifts after a manual change, hand-built setups degrade quietly. Expressing the vault, the policy, the protected items, and the recovery plans as code makes the configuration reviewable, version-controlled, and reproducible, which is the standard the rest of your infrastructure already holds and which disaster recovery deserves more than most.

The Recovery Services vault and the replication policy are straightforward to declare in Bicep, since they are ordinary Azure resources. The protected items and the Azure-to-Azure replication relationships are more nuanced, because they involve the Mobility extension and an ongoing replication state that is not purely declarative, so teams often combine a declarative base with a scripted enablement step. A pragmatic pattern is to declare the durable scaffolding, the vault, the policy, the target networks, in Bicep, and to drive the per-machine enablement and the recovery-plan construction through an idempotent PowerShell or CLI script that the pipeline runs.

```bicep
// Bicep for the vault and an Azure-to-Azure replication policy
resource vault 'Microsoft.RecoveryServices/vaults@2023-04-01' = {
  name: 'rsv-dr-eastus'
  location: 'eastus'
  sku: {
    name: 'Standard'
  }
  properties: {}
}

resource policy 'Microsoft.RecoveryServices/vaults/replicationPolicies@2023-04-01' = {
  parent: vault
  name: 'policy-prod-24h'
  properties: {
    providerSpecificInput: {
      instanceType: 'A2A'
      recoveryPointHistory: 1440
      appConsistentFrequencyInMinutes: 240
      crashConsistentFrequencyInMinutes: 5
    }
  }
}
```

The recovery plan, with its groups and steps, is the artifact most worth keeping in source control, because it encodes the dependency knowledge that is otherwise locked in someone's head. Exporting the recovery plan definition to JSON and committing it means the boot order, the groups, and the script references are reviewed like any other change, and a pull request that reorders a group becomes a visible decision rather than a silent portal edit. The Automation runbooks the plan calls belong in the same repository, tested in isolation so that a change to a connection-string-rewrite script is validated before it ships into a recovery plan that a real failover will execute. The discipline that ties this together is treating disaster recovery configuration as production code: changes go through review, the test failover is the integration test, and a green test after every meaningful change is the standard rather than a one-time milestone.

There is a real limit worth stating plainly. The continuously changing replication state, the initial seed, the health of an ongoing relationship, is not something infrastructure-as-code expresses well, because it is operational state rather than desired configuration. Code can declare that a machine should be protected by a given policy into a given region; it cannot make the seed complete faster or assert that replication is currently healthy. So the right mental model is that code owns the configuration and a monitoring layer owns the state, with alerts on replication health and recovery-point age catching the operational drift that no template can prevent.

## A Worked End-to-End Setup for a Three-Tier Application

To make the five stages concrete, walk through a realistic example: a three-tier application in the East US region with a pair of web servers behind a load balancer, a pair of application servers, and a data tier of two database servers and a domain controller, which the team needs to survive a regional outage with a recovery point objective of minutes and a recovery time objective under an hour.

The team starts with the target environment in West US, the paired region. They create the resource group that will hold the failed-over machines, a target virtual network mirroring the production subnet layout, and, critically, a separate isolated virtual network with no peering to anything, reserved for test failovers. They confirm that the West US subscription quota covers seven machines of the relevant sizes, requesting an increase because the region previously held nothing. They create a Recovery Services vault dedicated to replication and confirm the managed identity has Contributor on the target resource group and the network resources.

With the target ready, they enable replication on all seven machines, mapping each to the real target subnet and the production-mirror network rather than auto-generated names. They watch the initial seed complete over several hours and confirm every protected item reaches a healthy state with recovery points accumulating. They create a replication policy with a twenty-four-hour recovery-point retention, reasoning that they would detect a problem and decide to fail over well within a day, and an application-consistent snapshot every four hours for the database tier. Because the two database servers and the domain controller must recover to a coordinated point, they enable multi-VM consistency for that group.

Next they build the recovery plan with three groups. Group one holds the domain controller and the two database servers, with a manual action after it that asks the operator to confirm the databases are accepting connections. Group two holds the two application servers, with a pre-step runbook that rewrites the application's connection strings to the West US database endpoints. Group three holds the two web servers, with a post-step runbook that repoints the traffic manager profile to the West US load balancer. They export the plan definition and the runbooks to their infrastructure repository.

Then they run the test failover into the isolated network. The first run reveals two problems the dashboard never would have: the application servers had a hard-coded production database hostname that the connection-string runbook did not cover, so they fail to connect, and the whole sequence takes eighty minutes, over their one-hour objective, because the database tier's manual confirmation step waited on an operator who was not watching. They fix the runbook to cover the hostname, convert the manual confirmation to an automated health check that polls the database port, and run the test again. The second run comes up cleanly in fifty-one minutes, the application answers in the isolated network, and they record the real RTO. They run the cleanup, commit the recovery plan and runbook changes, and schedule the test failover to run quarterly and after any release that changes the dependency graph.

Finally they rehearse the return path. They run a planned failover to West US during a maintenance window, confirm the workload runs there, reprotect back to East US, let the disks resynchronize, fail back to East US, and reprotect again to West US to restore the starting posture. Having run the full loop once, the team knows the failback path works and is not improvising it during a real incident. The workload now has disaster recovery they have actually executed, which is the standard the test-failover rule sets and the standard a green replication icon cannot meet on its own.

## Why Healthy Replication Is Not Readiness

The strongest counter-reading to confront directly is the belief that healthy replication is disaster recovery, because it is so intuitive and so wrong at the same time. Replication health is a real and necessary signal: it tells you that the change stream is flowing, the recovery points are current, and a failover has fresh disks to work from. The error is treating that signal as sufficient, as if the dashboard reporting all machines protected were equivalent to the dashboard reporting the workload recoverable. Those are different claims, and the distance between them is everything the recovery plan and the test failover supply.

The reason the belief persists is that the gap only reveals itself under conditions you rarely create on purpose. As long as the primary region keeps running, replication health is the only signal you ever see, and it is always green, so it trains you to equate green with safe. The recovery plan is never exercised, the boot order is never tested, the runbooks are never run, and the RTO is never measured, because nothing forces those things to happen until an outage does. A team can run for years in this state, accumulating confidence proportional to the uptime of the primary region rather than to any evidence of recoverability, which is exactly backwards: the longer the primary region stays healthy, the more untested the failover path becomes and the more confident the team feels about it.

A test failover collapses that distance by manufacturing the conditions you otherwise only meet during a disaster, safely. It forces the recovery plan to run, which surfaces ordering mistakes. It forces the runbooks to execute, which surfaces hard-coded endpoints and scripts that assume production. It forces the machines to boot in a real network, which surfaces the resolution and connectivity problems that a disk replica cannot reveal. And it produces a measured RTO, which replaces the optimistic estimate in the disaster recovery document with a number you have actually observed. Every one of those discoveries is one you want to make during a scheduled rehearsal rather than during the outage, and the only way to make them is to run the test. This is why the test-failover rule is the organizing principle of a real setup and not merely a recommended extra step: it is the difference between believing you can fail over and knowing it.

## Site Recovery Versus Backup, Drawn Precisely

The second counter-reading worth engaging is the conflation of Site Recovery with backup, which produces real recovery failures when the wrong tool is configured for the failure at hand. The two services solve adjacent problems with different shapes, and the precise distinction is what tells you which to reach for and confirms you need both.

Backup answers the question of how to recover to a point in time after something went wrong inside the data: corruption, an accidental deletion, a ransomware encryption, a bad migration that ran cleanly but produced wrong results. Its defining properties are a long retention horizon, often months or years, and a recovery granularity that can reach individual files or a whole machine as it existed at a chosen historical moment. Its recovery objective is relaxed, because recovering a file from last quarter is rarely an emergency measured in minutes. The [VM backup configuration](/2023/07/03/configure-azure-vm-backup/) details how that long-horizon protection is built, and the key property to hold here is that backup reaches far back in time but is not designed to move a running workload to another region in minutes.

Site Recovery answers the orthogonal question of how to keep a workload running when its entire region becomes unavailable: a regional outage, a major service disruption, a planned regional migration. Its defining properties are a short recovery point objective measured in minutes, a short retention measured in hours, and an orchestrated failover that brings many machines up in another region in a coordinated sequence. It does not reach back months, and it is not the tool for recovering a single file from last quarter, because its retention window is far too short and its granularity is the machine and the region rather than the file and the historical moment.

The reason you need both is that the failure classes do not overlap. A ransomware event that encrypted your data and replicated the encrypted state to the secondary region is a backup recovery, not a failover, because every replication recovery point may already hold the encryption. A region that vanished is a failover, not a backup restore, because waiting hours to restore the full estate from backup blows past any reasonable recovery time for a regional event. A team that configured only one is exposed to the failure class the other covers, and the symptom is always the same: a recovery attempt that fails not because the tool was misconfigured but because the right tool was never present. Configuring both, sized for their respective failure classes, is the only complete posture, and the [disaster recovery architecture guide](/2024/07/22/azure-disaster-recovery-architecture/) places them together in the broader design where each does the job it is shaped for.

## Monitoring the Configuration After Setup

A setup that was correct on the day it was built drifts, because the application changes, new machines appear, policies get edited, and replication health fluctuates with the underlying platform. The configuration is not a one-time act but a state to monitor, and the monitoring layer is what catches the drift that no template prevents. Two signals matter most. Replication health, surfaced as alerts when a protected item falls out of a healthy state, tells you when the change stream has stalled and a machine is no longer recoverable to a current point. Recovery point age, the time since the most recent point was created, tells you whether the achievable RPO is actually being met or whether something is silently degrading it.

Beyond the per-item signals, the estate-level question is coverage: which machines that should be protected are not. New machines deployed into production after the initial setup do not protect themselves, and a workload that grew three new servers since the last review has three unprotected machines that will not fail over. The remedy is the same governance instinct that applies across Azure: rather than protecting each machine by hand and hoping nobody forgets, use a policy-driven check that flags production machines without a protected-item relationship, so coverage gaps surface as a report rather than as a discovery during an outage. Tying replication health, recovery-point age, and coverage into the same monitoring surface you use for the rest of the platform keeps disaster recovery from becoming the one system nobody looks at until it is needed.

## Network Mapping, IP Addressing, and the Details That Break Failover

The disks replicating is the visible part of the setup; the networking the failed-over machines land in is the part that determines whether the application actually works once it boots, and it is where careful configuration pays off most. When you enable replication, you map each source network to a target network, and that mapping decides which virtual network and subnet the failed-over machine joins. The decision that follows is addressing: do the machines keep their original private IP addresses in the target region, or do they receive new ones. Retaining the same addressing in the target network simplifies any configuration that references machines by IP, because nothing has to change, but it requires the target network to use the same address space, which in turn requires that the target network never be connected to the source network at the same time, since two networks with the same range cannot coexist on a peering. New addressing avoids the range collision but forces every IP-referencing configuration, connection strings, firewall rules, allow lists, to be updated during failover, which is what the recovery-plan runbooks are for.

Name resolution is the quieter failure mode. A machine that boots in the target region needs to resolve the names of the services it depends on, and if your DNS infrastructure lives in the primary region and was not itself failed over or replicated, the application tier comes up unable to find the database by name even though both machines booted fine. The disciplined pattern is to ensure the target region has working DNS, whether by failing over the DNS servers as an early recovery-plan group, by using a regional DNS service that exists independently in both regions, or by pre-staging the necessary records. This is the kind of dependency that a test failover exposes immediately and that a disk-replication health check never will, which is one more reason the rehearsal earns its place in the process.

The load balancer and public-facing entry point need their own plan. The private machines failing over does nothing for external traffic unless something repoints the public entry point to the target region, which is typically a traffic manager or front door profile updated by a recovery-plan script, or a manual cutover step. A recovery plan that boots every internal machine perfectly but never repoints the external traffic produces an application that is running and unreachable, which from the user's perspective is indistinguishable from down. Treating the external entry point as an explicit recovery-plan step, tested during the failover, closes that gap.

## Multi-VM Consistency and Coordinated Recovery Points

For most workloads, each machine having its own independent recovery points is fine, because the machines are loosely coupled and a few seconds of difference in their recovery points does not matter. For tightly coupled workloads, that independence is a hazard. A distributed database, a clustered application, or any system where two machines exchange state continuously can be broken by a failover that lands them at slightly different moments, because one machine's view of the shared state is now inconsistent with the other's. Multi-VM consistency exists for exactly this case: it groups machines into a replication group with shared, coordinated recovery points, so a failover brings the whole group to the same instant.

The trade-off is real and worth weighing rather than defaulting either way. Coordinated recovery points add overhead, because the service must synchronize the points across the group, and they require the grouped machines to share a single replication policy, which constrains how you tune them individually. A group that is too large pays the overhead broadly; a group that omits a machine that genuinely shares state leaves a consistency gap. The right grouping follows the actual data-sharing boundaries of the application: the machines that must agree on a single point in time go in one consistency group, and the machines that are independent stay independent. Misjudging this produces a failover that the dashboard reports as successful and that the application experiences as corruption, which is the worst kind of failure because it looks like a win.

A practical caution applies to databases specifically. While multi-VM consistency can keep the disks of a database cluster coordinated, a managed database service usually has its own purpose-built replication and failover mechanism that is aware of the database's transactional state in a way disk-level replication is not. For those, the database-native path described in the [SQL failover groups setup](/2023/06/12/configure-azure-sql-failover-groups/) is the correct tool, and the Site Recovery plan coordinates with it rather than trying to replicate the database at the disk level. Knowing which machines belong to disk-level multi-VM consistency and which belong to a database-native failover mechanism is part of designing the recovery plan correctly, and getting it wrong means either redundant protection or a database that fails over inconsistently.

## Where to Run, Rehearse, and Research This

Reading the sequence is one thing; building it in an environment where a mistake costs nothing is what turns the procedure into a skill. The hands-on Azure labs and command library on VaultBook give you a sandbox to enable replication, author a replication policy, build a recovery plan with ordered groups, and run a test failover into an isolated network without spending production money or risking a real workload, and its tested command and template library covers the Azure CLI, PowerShell, and Bicep forms of each step in this article so you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) and reproduce the whole pipeline end to end. Configuring replication and authoring the recovery plan in a lab first means the first time you do it against a real workload, the muscle memory is already there.

Because disaster recovery is ultimately a skill exercised under pressure, the rehearsal matters as much as the configuration, and that is where scenario practice pays off. The scenario-based disaster-recovery drills on ReportMedic put you in front of the exact situations this article warns about, a healthy replication state with no recovery plan, a test failover pointed at the wrong network, a boot order that fails because a dependency was not up, and let you work through the diagnosis and the fix, so you can [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) and build the reflexes that make a real failover calm rather than chaotic. Practicing the failure patterns before you meet them is what converts the test-failover rule from advice into instinct.

## What Site Recovery Costs and What Drives the Bill

A disaster recovery posture nobody can afford gets quietly switched off, so understanding where the money goes is part of building a setup that survives a budget review as well as a region loss. The cost of Azure-to-Azure replication has a steady-state component and a failover component, and they behave very differently, which is the first thing to internalize. The steady-state cost is what you pay every month whether or not you ever fail over, and the failover cost is what you pay only during a test or a real event.

The steady-state spend has three contributors. There is a per-protected-instance charge for the orchestration the service provides, which scales with how many machines you protect. There is the storage in the secondary region that holds the replica disks, which scales with the provisioned disk size of the protected machines, since the replica must be able to become those disks. And there is the storage that holds the recovery-point history, which scales with how many points your retention window keeps and how much the source disks churn, because a longer history of a high-churn machine stores more change data. The cache storage account in the source region adds a smaller amount. The lever you control most directly here is retention: a longer window buys you the ability to fail over further back in time at the cost of storing more change data, so the retention you chose for recovery reasons is also a cost decision, and the two should be reconciled deliberately rather than one being set in ignorance of the other.

The failover spend appears only when machines are actually running in the secondary region, because that is when you pay for the compute. During normal operation the replica disks sit in storage and cost storage money, not compute money, which is the economic logic that makes regional disaster recovery affordable: you pay to keep the disks current continuously, but you pay for the expensive compute only when you fail over. A test failover incurs this compute cost for the duration of the test, which is one more reason the cleanup step matters, since test machines left running after a drill keep billing as live compute. The false economy to avoid is skipping test failovers to save the small, temporary compute cost they incur, because the money saved is trivial against the cost of discovering during a real outage that the failover does not work. The genuine saving is in right-sizing retention to what you actually need and in not protecting machines that do not warrant regional failover, where backup alone would suffice.

### What is the cheapest way to keep the configuration valid?

The cheapest durable validity comes from automation, not from manual diligence. Express the vault, policy, and recovery plans as code so they cannot silently drift, run test failovers on a schedule the pipeline enforces rather than relying on someone remembering, and clean up test resources automatically so no drill leaves compute billing. Manual upkeep degrades; automated upkeep holds.

A subtler cost trap is over-protection. Not every machine needs regional failover. A stateless worker that can be redeployed from a template in minutes, or a development environment whose loss costs nothing, does not warrant the steady-state replication spend, and protecting it indiscriminately inflates the bill without buying meaningful resilience. The discipline is to protect what a regional outage would genuinely hurt and to let cheaper recovery mechanisms cover the rest, which keeps the disaster recovery budget proportional to the business value at risk rather than to the machine count.

## Supported Scenarios and the Limits to Verify

Site Recovery covers several source-and-target combinations, and knowing which one you are in shapes everything about the setup, because the Azure-to-Azure path this article focuses on differs in its mechanics from the on-premises-to-Azure path. The Azure-to-Azure scenario replicates Azure virtual machines from one region to another and is the cleanest case, because both ends are native Azure and the Mobility extension handles the change tracking with no separate replication appliance to deploy. The on-premises-to-Azure scenarios, replicating physical servers or virtualized machines from a data center into Azure, involve additional infrastructure such as a configuration server or a replication appliance, and while the orchestration concepts of recovery plans, test failover, and reprotect carry over, the prerequisites and the components differ enough that an Azure-to-Azure runbook does not translate directly.

Within the Azure-to-Azure scenario there are constraints worth confirming against the current official source rather than assuming, because Azure revises them regularly. Disk type and size support, the operating system versions covered, the maximum churn rate a protected machine can sustain before replication falls behind, and the regions available as replication targets all have specific boundaries that move over time. The churn-rate limit is the one that surprises teams: a machine that writes to its disks faster than the service can ship the changes will accumulate replication lag and may fall out of a healthy state, so a database server or a logging machine with very high write volume deserves a check against the current churn guidance before you assume it is protectable as-is. The remedy when a machine exceeds the supported churn is usually to split its workload, move the high-churn data to a service with its own replication, or accept a different protection mechanism for that machine, rather than to fight the limit.

The honest stance on all of these numbers is to treat them as values to verify at the time you build, not as constants to memorize, because a limit that was true when this was written may have been raised or changed by the time you read it. The official documentation is the authority for the current disk, size, operating system, churn, and region support, and the correct engineering habit is to confirm the specific combination you are protecting against that source before committing a design to it. What does not change is the shape of the work: enable replication, set a policy that matches your objective, build recovery plans that order the failover, prove it with a test failover into an isolated network, and rehearse the path back. The specifics of what is supported evolve; the discipline of proving readiness rather than assuming it does not.

A final scenario note concerns machines that should not be protected by disk replication at all. A machine whose state lives entirely in a managed service, with nothing of value on its own disks, gains little from disk-level replication and is better handled by protecting the managed service through its own mechanism and redeploying the stateless machine from a template in the target region. Recognizing which machines are genuinely stateful, and therefore warrant replication, versus which are disposable front-ends that a template can recreate, keeps the protected estate focused on the machines where disk replication actually adds resilience. That focus is both a cost discipline and a clarity discipline, because a smaller, well-chosen protected estate is easier to test, easier to reason about, and easier to fail over cleanly than a sprawling one that protects everything indiscriminately.

### How do I decide which machines actually need replication?

Ask what a regional outage would cost for each machine. Stateful machines whose disks hold data that cannot be recreated quickly warrant replication. Stateless machines that a template can rebuild in the target region in minutes do not, and protecting them inflates the steady-state bill without adding real resilience. Protect by business impact, not by machine count.

The same reasoning extends to how you tier your protection across the whole estate. The most critical workloads, the ones whose downtime is measured in lost revenue per minute, earn the full treatment: replication with a tested recovery plan, a rehearsed failover, and a backup behind it for the failure classes replication does not cover. Important but less time-sensitive workloads might earn replication with a longer acceptable recovery time and a less frequent test cadence. The least critical workloads might rely on backup and a redeploy-from-template plan with no replication at all. Mapping each workload to a protection tier, and being honest about which tier it truly belongs in, turns disaster recovery from an undifferentiated blanket into a deliberate allocation of effort and money toward the places where a region loss would actually hurt. That allocation, reviewed as the estate changes, is what keeps the posture both affordable and genuinely protective over the years a workload lives in production. A protection tier chosen once and never revisited drifts out of alignment as workloads grow more or less critical, so the review is part of the discipline rather than an afterthought to it.

## Closing Verdict

Azure Site Recovery setup is not finished when replication turns green; it is finished when you have run a test failover, watched the application come up in an isolated network in the right order, measured the real recovery time, fixed what the test exposed, and rehearsed the path back home. The five-stage checklist exists to keep the whole pipeline in view, because the strong pull is always to stop at stage one, where the dashboard looks complete and the work feels done. The test-failover rule is the corrective: readiness is proven by a rehearsed, non-disruptive failover, not by a replication health icon, and a setup that skips the rehearsal has bought storage replication and named it disaster recovery.

The deciding discipline, the one that separates teams who survive a regional outage calmly from teams who scramble through it, is treating the failover as something you practice on a schedule rather than something you hope works once. Configure the replication and the policy with intent, encode the dependency order in a recovery plan you keep in source control, run the test failover often enough that no major change ships unrehearsed, and rehearse the reprotect and failback so the return path is known. Pair the replication with backup for the failure classes replication does not cover, monitor the configuration for the drift that setup-day correctness cannot prevent, and the region loss becomes a planned failover rather than a crisis. That is the whole of it: not a healthy dashboard, but a rehearsed outcome.

## Frequently Asked Questions

### Q: How do I set up Azure Site Recovery for disaster recovery from start to finish?

Start with the target environment before touching replication: choose a secondary region, usually the Azure paired region, pre-create the target resource group and virtual network, reserve a separate isolated network for tests, confirm target-region quota covers the full failed-over footprint, and grant the service identity the roles it needs in both scopes. Then create a Recovery Services vault dedicated to replication, enable replication on a pilot machine while mapping it to real target networks, and let the initial seed complete. Define a replication policy with retention and application-consistent frequency that match your stated objective rather than the defaults. Build a recovery plan that splits machines into ordered groups respecting their dependencies, with scripts or manual checks between groups. Then run a test failover into the isolated network, validate that the application boots and works, measure the real recovery time, fix what the test exposes, and finally rehearse the reprotect and failback path. The setup is complete when the test failover passes, not when replication shows healthy.

### Q: What is the difference between Azure Site Recovery and Azure Backup?

They solve adjacent problems with different shapes. Azure Backup recovers a point in time after something went wrong inside the data, such as corruption, accidental deletion, or ransomware, with a long retention horizon of months or years and granularity down to individual files, but it is not designed to move a running workload to another region in minutes. Azure Site Recovery keeps a workload running when its entire region becomes unavailable, with a recovery point objective measured in minutes, a short retention measured in hours, and an orchestrated failover that brings many machines up in another region in a coordinated sequence, but it does not reach back months and is not the tool for restoring a single old file. The failure classes do not overlap: ransomware that replicated to the secondary region is a backup recovery, because the replication points may all hold the encryption, while a region that vanished is a failover, because restoring the full estate from backup is too slow for a regional event. A complete posture configures both.

### Q: How do I configure the replication policy and what RPO does it deliver?

A replication policy controls two settings that carry most of the weight: the recovery-point retention window, which sets how many hours of labeled points the service keeps and therefore how far back you can fail over, and the application-consistent snapshot frequency, which sets how often the service quiesces the application to produce a transactionally clean point. For Azure-to-Azure replication the achievable recovery point objective is low, typically minutes, because changes ship continuously rather than on a fixed schedule, so the policy is not setting the freshness floor but the retention ceiling and the clean-point cadence. Size the retention to your detection-to-decision window, how quickly you would notice a problem and want to fail over to a point before it, balanced against the storage cost of keeping more points. The common error is reading the low achievable RPO as proof the policy is fine while leaving retention too short to reach a clean point after a problem that went unnoticed for a while.

### Q: How do I run a test failover without affecting production?

Run the test failover against an isolated virtual network in the target region that has no peering, gateway, or VPN path back to production. The service boots copies of your replicated machines in that isolated network, lets you log in and validate that the application works, and leaves the production machines and the ongoing replication completely untouched. The isolation is non-negotiable, because the test machines believe they are the production servers, and if they can reach the real network you risk duplicate machine identities, conflicting domain controllers, and corruption of the production directory as the test machines replicate their state back. After validating, run the test failover cleanup operation to delete the test resources and record notes about what the test found. A test failover into a connected network can cause damage worse than the outage you were preparing for, so verify the target network's isolation before the first test rather than discovering a connection afterward.

### Q: How do recovery plans order the failover across multiple machines?

A recovery plan assigns every machine to a numbered group, and groups boot strictly in sequence, so group two does not start until group one finishes. This lets you respect dependency chains: a three-tier application puts its domain controllers and database servers in an early group, its application servers in a middle group, and its web tier in a final group, so each tier is up before the tier that depends on it boots. Between and within groups you can insert manual actions that pause for an operator to confirm something, and automated scripts run through Azure Automation runbooks that perform programmable steps like rewriting connection strings or repointing a load balancer. The default behavior, and the trap, is that all machines drop into a single group and boot simultaneously, which breaks any application with a startup dependency. Splitting machines into ordered groups and inserting the checks and scripts that make each tier ready is what turns a sequence of booting machines into a working application.

### Q: Why is healthy replication not the same as being ready to fail over?

Replication health tells you the change stream is flowing and recovery points are current, which is necessary but not sufficient. It says nothing about whether those disks assemble into a bootable machine, whether the machine can reach a domain controller, whether the application tier comes up after the database tier, or whether anyone has the runbook to coordinate the failover under pressure. The gap persists because as long as the primary region runs, replication health is the only signal you see and it is always green, so it trains you to equate green with safe while the recovery plan goes unexercised and the boot order untested. A test failover collapses that gap by manufacturing the failover conditions safely: it forces the recovery plan to run, surfaces ordering mistakes and hard-coded endpoints, and produces a measured recovery time that replaces the optimistic estimate. The longer the primary region stays healthy, the more untested the failover path becomes, which is why proving readiness requires running the test rather than trusting the icon.

### Q: How do I fail back to the primary region after a real failover?

Failback is a reprotect followed by a reverse-direction failover. After a failover leaves you running in the secondary region, the replication relationship points the wrong way and the workload is unprotected, so the first step once the primary region recovers is to reprotect, which establishes replication from the now-active secondary region back toward the original primary and resynchronizes the disks. The resync takes time proportional to how much changed while you ran in the secondary region. Once the resync completes, you run a failover in the reverse direction, from secondary back to primary, which brings the workload home. After failback, you reprotect again to restore the original replication direction, primary to secondary, returning to the starting posture. A complete setup rehearses at least through reprotect during a drill, because a failover you cannot cleanly reverse strands you in the secondary region, often running without the disaster recovery protection you just used.

### Q: What does the commit operation do after a failover?

After you run a failover, the operation is not finalized until you commit it. Until the commit, the service retains the other recovery points, so you keep the option to change which point you failed over to, which is useful if the point you initially chose turns out to have a problem and you want to try an earlier one. Committing the failover discards the alternative recovery points and locks in the one you are keeping, which is the deliberate act of declaring this is the state we are running from. The commit precedes reprotect, because reprotect establishes a new replication relationship from the committed state, and you cannot reverse direction while the original failover is still uncommitted. In practice the sequence after an unplanned failover is to validate the workload, commit the failover once you are satisfied with the recovery point, and then reprotect to re-establish protection in the new direction.

### Q: How many recovery plans do I need and how should I group machines?

The grouping should follow the boundaries of your applications and their dependencies rather than a fixed number. A single application with a clear three-tier structure typically needs one recovery plan with groups ordered by tier, so the data tier boots and is verified before the application tier, which boots before the web tier. Independent applications that have no startup dependency on each other can each have their own recovery plan, which lets you fail one over without the other, or share a plan if they always fail over together. The principle is that machines which must boot in a specific order relative to each other belong in the same plan as ordered groups, while machines that are genuinely independent do not need to be coordinated. Building one giant plan for unrelated applications forces them to fail over together unnecessarily, while building too many fragmented plans for a single coupled application loses the ordering that the application needs at startup.

### Q: Does Site Recovery protect Azure SQL Database or managed databases?

Site Recovery replicates the disks of virtual machines, so it protects database engines you run yourself on VMs, but a managed database service usually has its own purpose-built replication and failover mechanism that understands the database's transactional state in a way disk-level replication cannot. For those, the database-native path is the correct tool, because it coordinates the failover with the database's own consistency model rather than treating the database as opaque disk blocks. In a mixed application, the Site Recovery recovery plan handles the VM-based tiers and coordinates with the database-native failover for the managed database, rather than trying to replicate the managed database at the disk level. Knowing which machines belong to disk-level replication, possibly with multi-VM consistency for self-hosted clustered databases, and which belong to a database-native failover group is part of designing the recovery plan correctly, and confusing the two produces either redundant protection or a database that fails over in an inconsistent state.

### Q: How do I make sure the failed-over machines can reach each other and resolve names?

Booting the machines is necessary but not sufficient; they need a working network and name resolution in the target region. When you enable replication you map each source network to a target network, which decides the virtual network and subnet the machine joins, and you decide whether machines retain their original private addresses or receive new ones. Retaining addresses simplifies IP-referencing configuration but requires matching address space and that the networks never connect simultaneously, while new addresses avoid range collisions but force connection strings and firewall rules to be updated by recovery-plan scripts. Name resolution is the quieter failure: if your DNS lives only in the primary region, the application tier boots unable to find the database by name. The fix is to ensure the target region has working DNS, by failing over the DNS servers as an early group, using a regional DNS service that exists in both regions, or pre-staging records. A test failover exposes both the addressing and the resolution problems immediately.

### Q: What is multi-VM consistency and when do I need it?

Multi-VM consistency groups machines into a replication group with shared, coordinated recovery points, so a failover brings the whole group to the same instant rather than letting each machine fail over to its own independent point. You need it for tightly coupled workloads where two machines exchange state continuously, such as a distributed database, a clustered application, or any system where one machine's view of shared state must match another's, because a failover that lands them at slightly different moments can leave the shared state inconsistent and break the application. You do not need it for loosely coupled machines that tolerate a few seconds of difference, and reaching for it indiscriminately wastes resources, since coordinated points add synchronization overhead and require the grouped machines to share a single replication policy. The right grouping follows the actual data-sharing boundaries: machines that must agree on a single point in time go in one consistency group, and independent machines stay independent.

### Q: How do I express my Site Recovery configuration as infrastructure as code?

Declare the durable scaffolding, the Recovery Services vault, the replication policy, and the target networks, in Bicep or another template language, since these are ordinary declarative resources. The per-machine replication enablement and the recovery-plan construction are more nuanced, because they involve the Mobility extension and an ongoing replication state that is not purely declarative, so drive those through an idempotent PowerShell or CLI script that the pipeline runs after the scaffolding deploys. Keep the recovery plan definition, exported to JSON, in source control, because it encodes the dependency knowledge that is otherwise locked in someone's head, and keep the Automation runbooks the plan calls in the same repository, tested in isolation. The limit to accept is that the continuously changing replication state is operational rather than declarative: code can declare that a machine should be protected into a region, but it cannot make the seed complete faster or assert that replication is currently healthy. So code owns the configuration and a monitoring layer owns the state.

### Q: How often should I run a test failover?

There is no universal interval, but the right cadence is tied to how fast the workload changes rather than to the calendar alone. A workload whose dependency graph shifts with each release deserves a test failover often enough that no major change ships unrehearsed, which in practice means running it as part of the release process for changes that touch the application's startup dependencies, its connection strings, or its network topology. A stable workload that rarely changes still deserves a periodic test, perhaps quarterly, because the platform, the base images, the runbooks, and the people all drift over time, and an annual surprise is worse than a quarterly confirmation. The honest test is the one that would catch a problem before a real outage does, so the cadence is correct when the time between tests is shorter than the time in which a meaningful change to the workload or its environment would accumulate. Each test ends with cleanup and recorded notes so the next one starts from a known state.

### Q: Why does my failover stall partway through with some machines failing to start?

The most common causes are target-region capacity and permission gaps that lie dormant until a real failover. If the secondary region's subscription quota was sized only for the trickle of test machines you have run there, a full-estate failover hits a vCPU quota wall and some machines cannot allocate, so the fix is to confirm and request quota in the target region sized for the entire failed-over footprint. A recovery-plan script can also fail if the automation identity lacks a role it needs on a target resource, stalling the plan at that step. A chosen VM size that exists in the primary region but is unavailable in the secondary region produces the same stall for the affected machines. Each of these is something a test failover would expose during a rehearsal, which is why running the test against the full recovery plan, rather than a single machine, matters: it forces the capacity, permission, and size assumptions to be validated before a real outage tests them for you.

### Q: Should I use a separate Recovery Services vault for replication and backup?

Generally yes. Backup and Site Recovery both use the Recovery Services vault resource type, but they are different workloads with different scaling and policy surfaces, and separating them keeps each cleaner to reason about and operate. A vault dedicated to replication holds the replication policies, the protected items, and the recovery plans without the backup policies and recovery points cluttering the same surface, which makes the replication configuration easier to audit, monitor, and express as code. It also avoids the two workloads contending for the same vault-level limits and lets you apply access control scoped to each concern, so the team responsible for failover orchestration is not entangled with the team managing long-horizon restore. The separation is a recommended practice rather than an absolute requirement, but the operational clarity it buys is worth the modest extra structure, especially as the estate grows and both workloads accumulate more items in their respective vaults.

### Q: How do I monitor a Site Recovery configuration after it is set up?

Watch three signals. Replication health, surfaced as alerts when a protected item falls out of a healthy state, tells you when the change stream has stalled and a machine is no longer recoverable to a current point. Recovery point age, the time since the most recent point was created, tells you whether the achievable recovery point objective is actually being met or whether something is silently degrading it. Coverage, the estate-level question of which production machines that should be protected are not, catches the gap created when new machines deploy without protecting themselves. For coverage specifically, a policy-driven check that flags production machines lacking a protected-item relationship turns gaps into a report rather than a discovery during an outage. Tie all three into the same monitoring surface you use for the rest of the platform, because disaster recovery configuration drifts as the application changes, policies get edited, and replication health fluctuates, and the monitoring layer is what catches the drift that setup-day correctness cannot prevent.

### Q: Can I fail over just one machine, or does the whole recovery plan fail over together?

You can do either, depending on how you trigger the operation. You can fail over a single protected item on its own, which is useful for testing one machine or recovering a single isolated workload, or you can fail over an entire recovery plan, which brings up all its machines in the ordered groups the plan defines. The choice depends on the situation: a regional outage calls for failing over the whole recovery plan so the application comes up coordinated, while a problem isolated to one independent machine might call for failing over just that item. The reason to build recovery plans even though single-item failover exists is that an application with dependencies needs the coordination, the boot order, and the scripts that only a plan provides, and failing over its machines one at a time by hand under pressure is exactly the scramble the recovery plan is meant to prevent. Independent machines with no dependencies can reasonably be failed over individually.

### Q: What happens to data written after the last recovery point if the region fails suddenly?

That data is the recovery point objective made concrete: the window of changes that had not yet been captured in a recovery point when the region became unavailable is the data you may lose. For Azure-to-Azure replication this window is typically small, on the order of minutes, because changes ship continuously and crash-consistent points are generated frequently, so the realistic data-loss window for a sudden region failure is short rather than the longer gap a snapshot-based design would carry. This is distinct from a planned failover, where the service first synchronizes any final changes before moving the workload, achieving zero data loss because the primary region is still healthy and reachable during the cutover. The lesson for setup is that the achievable recovery point objective for an unplanned failover is a property of replication, not something you set, while the retention window you do set determines how far back you can choose a point, which matters when you need to recover to before a problem rather than to the latest moment.
