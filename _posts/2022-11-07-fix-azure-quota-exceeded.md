---
layout: post
title: "Fix Azure Quota Exceeded and vCPU Limits"
page_title: "Fix Azure Quota Exceeded and vCPU Limit Errors: QuotaExceeded vs SkuNotAvailable vs AllocationFailed, Per-Region and Per-Family vCPU Quota, and How to Request the Right Increase"
date: 2022-11-07
categories: ["Technology"]
tags: ["Azure", "Quota", "Virtual Machines", "Troubleshooting", "Compute", "vCPU"]
excerpt: "An Azure quota exceeded error blocks your deployment. Tell QuotaExceeded from SkuNotAvailable, find the limiting vCPU quota, and request the right fix."
image: "/assets/images/blog/blog-35.webp"
reading_time: 60
author: "andrew-price"
last_updated: 2022-11-07
lang: en
---
A deployment fails, the portal turns red, and the message reads "Operation could not be completed as it results in exceeding approved quota." That single line of text is where most engineers make their first mistake, because an Azure quota exceeded error is not one problem but the visible end of three completely different ones. The deployment might have hit a soft limit you can raise with a request that often clears in seconds. It might have hit a hard wall of regional capacity that no request will ever move. Or it might have hit a transient allocation shortage in one availability zone that disappears if you point the same template a few kilometers away. The fix for the first is paperwork, the fix for the second is a different region or size, and the fix for the third is a retry with a tweak. Apply the wrong one and you wait days on a support ticket that was never going to help, or you keep hammering a zone that has nothing left to give.

![Diagnosing Azure quota exceeded and vCPU limit errors by cause - Insight Crunch](/assets/images/blog/blog-35.webp)

This article treats the quota exceeded message as a diagnosis problem first and a paperwork problem second. The goal is that you leave able to read which of the three failures you actually hit, confirm it with a command rather than a guess, and take the matching action. Compute capacity on Azure is governed by a layered system of allowances scoped per subscription, per region, and per virtual machine family, and the same red banner can mean any layer is full. Reading the error correctly is the whole game, and the rest of this guide walks the layers one at a time, with the command that confirms each and the fix that resolves it.

## How to Read the Quota Exceeded Error Before You Touch Anything

The first discipline is to read the literal text of the failure rather than the color of the banner. Three error codes account for nearly every deployment that fails for "not enough room," and they live in different parts of the platform. `QuotaExceeded` is a billing and governance limit on how many cores your subscription is allowed to run in a region. `SkuNotAvailable` is a catalog and capacity statement that the specific size you asked for is not offered to you in that region or zone. `AllocationFailed` and its zonal sibling `ZonalAllocationFailed` are a real-time statement that the datacenter does not have a free physical host of the size you want at the moment you asked. The words around each code tell you which one you hit, and the words matter more than the HTTP status, because several of these can surface as a generic deployment failure once they bubble up through Azure Resource Manager.

The quota family reads like an accounting statement. You will see phrasing close to "Operation could not be completed as it results in exceeding approved quota," followed by the resource type, the region, the current usage, the amount the operation needs, and the approved limit. That last set of numbers is the diagnostic gold, because it tells you not only that you are over the line but by how much and against which counter. A capacity failure reads differently. The allocation message says something close to "Allocation failed. We do not have sufficient capacity for the requested VM size in this region. Read more about improving likelihood of allocation success." There is no approved limit in that text because no limit was crossed; the hardware was simply not free. The catalog failure reads differently again, naming the SKU and saying it is not available in the location, sometimes adding that it is restricted for your subscription or offered only in certain zones.

### What is the difference between a quota error and a capacity error?

A quota error means your subscription has run out of its approved allowance of cores and you can ask for more, often with instant approval. A capacity error means the datacenter has no free hardware of that size right now, so no allowance change helps. The text names which one you hit.

That distinction is the single most useful thing in this article, so it is worth slowing down on. When you raise a quota, you are editing a number in a governance database that says how many cores Microsoft will let your subscription bill in a region. When you hit a capacity wall, you are bumping against the physical inventory of servers in a building. The first is a policy you can renegotiate in minutes. The second is supply you cannot conjure by asking nicely. Engineers who conflate the two file a quota increase request for an `AllocationFailed`, wait for it to be approved, redeploy into the same exhausted zone, and fail again with the same message, now convinced the platform is broken. The platform is behaving exactly as designed; the diagnosis was wrong.

There is a fast way to gather the signal you need. Before you change a single setting, capture three facts: the exact error code and its message text, the region and zone you targeted, and the precise VM size you requested. With those three facts you can route the rest of the work. If you only have a portal screenshot, expand the deployment's operation details to find the inner error, because Resource Manager often wraps the real code inside a parent `DeploymentFailed`. The command line gives you the same depth without hunting through blades. After a failed CLI deployment, the response body carries the inner error, and you can also pull the deployment operations directly:

```bash
az deployment group show \
  --resource-group rg-app \
  --name vm-deploy \
  --query "properties.error" -o json

az deployment operation group list \
  --resource-group rg-app \
  --name vm-deploy \
  --query "[?properties.provisioningState=='Failed'].properties.statusMessage" -o json
```

The `statusMessage` field holds the inner error object, and inside it the `code` is one of the three families above. Reading that code is the branch point for everything that follows. If it is the quota family, you are in a governance problem and the rest of the diagnosis is about finding which counter is full. If it is the capacity or catalog family, no amount of requesting will help, and the work shifts to choosing a different size, zone, or region. The series treats this kind of confirming distinction as the heart of troubleshooting, the same way the guide to [fixing ARM template deployment failures](/2022/10/24/fix-arm-template-deployment-errors/) insists you read the inner error before editing the template. A quota exceeded message that you have not yet decoded into one of these three codes is not yet a diagnosis; it is a banner.

## The Quota Versus Capacity Rule and the Diagnosis Table

The namable claim this article advances is the quota-versus-capacity rule: `QuotaExceeded` is a soft limit you raise with a request, while `SkuNotAvailable` and `AllocationFailed` describe capacity and availability you cannot request away, so the first and only correct first step is reading which one you hit and routing to the matching action. State it that plainly to a teammate and you will save them the most common wasted day in Azure compute work.

The findable artifact is the diagnosis table below. It maps each error code to whether it is a soft governance limit or a hardware and catalog reality, to the command that confirms it is yours, and to the action that actually resolves it. Pin this table; it is the decision surface for the entire problem space.

| Error code and message clue | Soft quota or capacity reality | How to confirm it is your cause | The matching action |
| --- | --- | --- | --- |
| `QuotaExceeded` / "exceeding approved quota," names current usage and limit | Soft governance limit | `az vm list-usage` shows current at or near the limit for that family or the regional total | Request an increase for the specific family or the regional total in that region |
| `SkuNotAvailable` / "not available in location," may say restricted | Catalog and capacity reality | `az vm list-skus` shows a restriction entry for that size in that region or zone | Pick a region or zone where the size is offered, or choose an available size |
| `AllocationFailed` / "do not have sufficient capacity for the requested VM size" | Real-time capacity reality | Usage is below the limit yet the deploy fails; a smaller or different size succeeds | Retry with a different size or zone, deallocate and reallocate, or use capacity reservations |
| `ZonalAllocationFailed` / capacity message naming a zone | Real-time capacity reality in one zone | The same size deploys in a different zone or as regional (no zone) | Target a different zone, drop the zone constraint, or reserve capacity in the needed zone |
| `OverconstrainedAllocationRequest` (common with spot) | Capacity plus your constraints | The spot price cap, zone, or size combination has no offer right now | Loosen the spot constraints, raise the max price, or widen the eligible sizes |

The table is the artifact, but the reasoning behind it is what keeps you from misreading a new variant. Anything in the quota family is a number in a database; anything in the capacity or catalog family is physical supply or a regional offering decision. When a brand new message arrives that is not in the table, ask the one question the table encodes: does the text name an approved limit you crossed, or does it name supply that was not there? That question sorts almost every compute deployment failure into the correct lane.

## How Azure vCPU Quota Is Actually Scoped

To find which counter is full when you hit `QuotaExceeded`, you have to know how the counters are laid out, and the layout surprises people because it is not a single number. Compute quota on Azure is scoped along three axes at once, and a deployment must satisfy all of them. The axes are the subscription, the region, and the virtual machine family.

The subscription is the billing and ownership boundary, and quotas are tracked per subscription, never pooled across the subscriptions in a tenant. If you run two subscriptions, each carries its own allowances, and a generous limit in one does nothing for a deployment in the other. The region is the second axis: a limit approved in East US has no bearing on West Europe, and a fresh region you have never deployed into starts with default allowances that are frequently lower than the region you have been scaling in for a year. The third axis, the one that catches the most engineers, is the virtual machine family. Azure groups VM sizes into families such as the Dsv5 family, the Esv5 family, the Fsv2 family, and many more, and each family carries its own per-region core allowance that is independent of the others and independent of the regional total.

### Why is vCPU quota scoped per region and per VM family?

Azure tracks cores separately for each VM family in each region so that capacity planning and billing controls can be managed per hardware generation and per datacenter. A deployment must fit under both the family limit for the size you chose and the total regional vCPU limit, whichever is reached first.

This dual-counter design is the source of the most confusing quota failures, because two different ceilings can stop you and the error names only the one you hit. There is a per-family counter, for example "Standard DSv3 Family vCPUs," and there is a separate aggregate counter, "Total Regional vCPUs," that sums every running core across all families in the region. A deployment of eight Dsv5 cores must fit under the remaining Dsv5 family allowance and under the remaining total regional allowance simultaneously. You can sit comfortably under your total regional limit, with hundreds of cores to spare, and still fail because the one family you chose is maxed out. The reverse also happens: each family has room, but the regional total is the wall. The error message will tell you which counter you crossed if you read it, naming either the family resource or the total regional resource, but engineers skim past that and assume the deployment was simply "too big" when the real fix is either a family increase or a switch to a family with headroom.

There are further independent allowances that ride alongside the core counts and trip deployments that have nothing to do with vCPUs. Spot and low-priority cores are tracked under their own family counters, distinct from the standard on-demand counters for the same hardware, so plenty of standard Dsv5 quota does not grant you a single spot Dsv5 core. Virtual machine scale sets count their instance cores against the same family and regional counters as standalone VMs, which means an autoscale event can quietly consume the headroom a later manual deployment was counting on. And entirely separate resource quotas, such as public IP addresses, network interfaces, managed disk storage, and the number of VMs in a region, can fail a deployment with a message that looks like a quota error but points at a counter that has nothing to do with cores. The discipline is always the same: read which counter the message names, then confirm that counter's current usage before acting. Understanding this scoping is also why the [complete engineering guide to Azure Virtual Machines](/2022/01/03/azure-virtual-machines-complete-guide/) spends time on the size and family model; the family you pick is not just a performance decision, it is a quota decision that determines which wall you hit first.

## Cause One: A Real QuotaExceeded Limit, and How to Confirm and Raise It

When the inner error code is `QuotaExceeded` and the message names an approved limit, you are in governance territory and the fix is a request. Before you file it, confirm the exact counter that is full, because requesting the wrong one wastes the round trip. The fastest confirmation is the usage listing for the region, which prints every compute counter with its current value and its limit side by side:

```bash
az vm list-usage --location eastus --output table
```

The output lists rows such as Total Regional vCPUs, Standard DSv3 Family vCPUs, Standard ESv5 Family vCPUs, and Virtual Machines, each with a current value and a limit. Find the row whose name matches the resource in your error message and read its current value against its limit. If the current value sits at the limit, that is your wall. If you prefer PowerShell, the equivalent reads the same data:

```powershell
Get-AzVMUsage -Location "eastus" | Where-Object { $_.CurrentValue -ge ($_.Limit * 0.9) }
```

That filter surfaces every counter at or above ninety percent of its limit, which is exactly the set you want to watch before a scaling event. The table from `az vm list-usage` answers the question "which counter blocked me," and it also answers the quieter question "which counter is about to block me," which is the foundation of prevention later in this guide.

Once you know the counter, decide what you are raising. If your error named a family resource such as Standard DSv3 Family vCPUs, you raise that family in that region. If it named Total Regional vCPUs, you raise the regional total. Raising one does nothing for the other, and this is the single most common request mistake: an engineer raises the regional total, redeploys, and fails again because the family counter was the actual wall. Match the request to the named counter.

### How do I request an Azure quota increase?

Open the Quotas page in the portal, filter to Compute, the subscription, and the region, select the family or regional total that is full, and request a new limit. Many standard vCPU increases approve automatically within seconds when regional capacity allows; the rest route to a support engineer.

The portal path is the centralized Quotas experience, reached from the portal search or from a subscription's Usage and quotas blade. You filter by provider (Microsoft.Compute), by subscription, and by region, then locate the row that is full, enter the new limit you want, and submit. The modern self-service flow evaluates the request against available regional capacity and, when the capacity exists and the increase is within policy, approves it on the spot, so the deployment that failed a moment ago succeeds on the next attempt. When the requested increase is large, or the region is constrained, the request is routed to a support engineer and you receive a tracking case. There is no fixed approval time to promise, and you should verify the current behavior and any limits against the official Azure quota documentation at the time you read this, because the self-service policy and the default limits change.

The same operation is scriptable, which matters when you manage many subscriptions or want the increase recorded in source control. The Azure CLI exposes quotas through the quota extension, which talks to the Microsoft.Quota provider. You list the current limits for a scope, then update the one you need:

```bash
# Scope is the Compute provider in a specific region
SCOPE="/subscriptions/<sub-id>/providers/Microsoft.Compute/locations/eastus"

# See current limits and names for that scope
az quota list --scope "$SCOPE" --output table

# Raise a specific family to a new absolute limit value
az quota update \
  --resource-name standardDSv3Family \
  --scope "$SCOPE" \
  --limit-object value=200 limit-object-type=LimitValue
```

The `--resource-name` is the canonical name of the counter, which you read from the `az quota list` output rather than guessing, because the friendly portal name and the API name differ. The value is the new absolute ceiling you want, not the amount to add. If the provider can satisfy the request from capacity it approves immediately and the new limit appears in a subsequent `az quota show`; if it cannot, the response indicates the request was submitted for review. For the rare counter the quota extension does not yet cover, or for an increase the self-service flow rejects, you fall back to a support request of type "Service and subscription limits (quotas)," choosing the compute quota subtype and entering the region, family, and new limit. The practice drills on [ReportMedic for working a quota request end to end](https://reportmedic.org/tools/azure-troubleshooting-drills.html) walk this exact flow, from reading the failed deployment to confirming the raised limit, which is worth rehearsing before you are doing it under deployment pressure.

One subtlety closes this cause. A quota increase changes what you are allowed to run; it does not guarantee the hardware exists to run it. If you raise a family limit in a constrained region and the region has no free capacity of that size, your next deployment can fail with `AllocationFailed` even though the quota now permits it. That is not a contradiction; it is the two-layer system working as designed, the governance layer saying yes and the capacity layer saying not right now. When that happens you have moved from cause one to cause three, and the work shifts accordingly.

## Cause Two: SkuNotAvailable, the Error a Quota Increase Will Never Fix

The most expensive misdiagnosis in this space is filing a quota increase for a `SkuNotAvailable` error and waiting on it. The request will be approved, because nothing was over your allowance, and the deployment will fail again, because the size you asked for is simply not offered to you in that region or zone. The increase did not address the cause, and the days spent waiting were wasted. `SkuNotAvailable` is a catalog statement, not a counter, and you confirm it by reading the catalog.

The catalog command is `az vm list-skus`, which enumerates every size in a region along with the restrictions that apply to your subscription. A size that is not available carries a restriction entry naming the scope of the limitation, either the whole location or specific zones, and the reason, which is usually that the size is not offered there for your subscription type or that it is capacity restricted at the location level. You query it directly for the size you wanted:

```bash
# Show restrictions for one size in a region
az vm list-skus \
  --location eastus \
  --size Standard_D4s_v5 \
  --all \
  --query "[].{Name:name, Restrictions:restrictions}" -o json
```

If the `Restrictions` array is empty, the size is offered to you and your failure is capacity or quota, not catalog. If it contains an entry with `type` of `Location`, the size is not available to your subscription anywhere in that region, and no setting you change will deploy it there; you must choose a different region or a different size. If it contains a `Zone` restriction listing specific zones, the size is offered in the region but not in those zones, so you target a different zone. The `--all` flag is important, because without it the command hides sizes that are restricted, which is the opposite of what you want when you are diagnosing a restriction.

### Why does Azure say my VM size is not available in a region?

A `SkuNotAvailable` error means the size is not offered to your subscription in that location or those zones, either because the hardware generation is not deployed there or because it is capacity restricted at the catalog level. A quota increase cannot change a catalog decision; you pick an available size or region.

To choose the alternative quickly, list the sizes that are available without restriction in the region and pick the nearest match on cores and memory. The same command, filtered to drop restricted entries, gives you the menu:

```bash
# List sizes that are actually available (no restrictions) in the region
az vm list-skus \
  --location eastus \
  --resource-type virtualMachines \
  --query "[?length(restrictions)==\`0\`].name" -o tsv | sort -u
```

That produces the set of sizes you can deploy in the region right now, and from it you select a size in the same family generation when one is available, since staying in the family preserves the performance profile your workload was tuned for. When the family itself is not offered in the region, you move to the closest adjacent family, accepting that the processor generation and the price will shift. The decision rule is simple: match cores and memory first, family generation second, and verify the alternative is unrestricted before you redeploy, so you do not trade one catalog wall for another.

There is a zonal nuance worth naming because it produces a `SkuNotAvailable` that looks regional but is not. Some sizes are offered in a region overall yet absent from one or two of its availability zones, often the newest hardware generations that have not rolled out evenly. A template that pins the VM to a specific zone can fail with the catalog error while the same template with no zone, or with a different zone, succeeds. Reading the restriction array tells you whether the limitation is at the location level, which forces a region change, or at the zone level, which only forces a zone change. The distinction is the difference between a small edit and a migration.

## Cause Three: AllocationFailed, When the Hardware Simply Is Not There

`AllocationFailed` and `ZonalAllocationFailed` are the platform telling you, in real time, that there is no free physical host of the size you requested in the region or zone you targeted at the moment you asked. Your quota is fine, the size is in the catalog, and yet the deployment fails, because allocation is a live inventory operation and inventory fluctuates. This is the cause engineers find hardest to accept, because it feels like the cloud should be infinite, and the honest answer is that any given datacenter, region, zone, and hardware generation has a finite pool that can be momentarily exhausted, especially for the largest sizes, the newest generations, and the most popular regions during peak demand.

You confirm it by elimination and by the message text. The message names insufficient capacity for the requested size and does not name an approved limit, which already separates it from `QuotaExceeded`. You confirm your quota has room with `az vm list-usage`, which will show the relevant counters below their limits, and you confirm the size is in the catalog with `az vm list-skus`, which will show no location restriction. With quota clear and catalog clear and the deployment still failing on capacity, you have isolated cause three, and the fixes are about flexibility rather than requests.

### How do I fix an AllocationFailed error in Azure?

Retry with a different VM size in the same family, or target a different availability zone or region, since the shortage is specific to one size in one location at one moment. For stopped VMs failing to start, fully deallocate and start again so the platform places them on a host with capacity. For predictable needs, reserve capacity in advance.

The flexibility levers, in rough order of least to most effort, start with size. A neighboring size in the same family, one step smaller or a sibling with the same core count on a slightly different sub-variant, often allocates immediately because its pool is less contended. Next is the zone: if you pinned the VM to zone one and hit `ZonalAllocationFailed`, zones two or three frequently have capacity, and dropping the zone constraint entirely lets the platform place the VM wherever it has room within the region. Beyond that is the region: a less saturated region of the same geography deploys the original size without complaint, at the cost of moving the workload's location. For a virtual machine that already exists but fails to start after being stopped, a full deallocate and start cycle is the specific fix, because a stopped-allocated VM still holds its host, while a deallocated VM releases the host and is re-placed on start onto hardware that currently has room:

```bash
# Release the host and re-place the VM on capacity that exists now
az vm deallocate --resource-group rg-app --name vm-01
az vm start      --resource-group rg-app --name vm-01
```

For capacity you cannot afford to gamble on, the durable answer is to reserve it. On-demand capacity reservations let you hold a guaranteed pool of a given size in a given zone before you need it, so the allocation succeeds when you scale because the hardware was set aside in advance. That converts a probabilistic allocation into a certainty, at the cost of paying for the reserved capacity whether or not it is in use, which is the trade-off you weigh for workloads where a failed scale-out is unacceptable. The same capacity-reservation thinking underpins why a sudden scale event can fail even when steady state is healthy, and it connects directly to the scaling failures covered when [AKS pods are stuck pending](/2022/07/25/fix-aks-pods-pending/), where a node pool cannot grow because the underlying VM size has no capacity to allocate.

## Spot and Low-Priority Cores Have Their Own Separate Quota

A failure that baffles teams the first time they meet it is a spot deployment rejected for quota when the standard quota for the identical hardware is wide open. The cause is that spot capacity, the deeply discounted evictable cores Azure sells from spare inventory, is tracked under a completely separate counter from on-demand capacity. You can hold two hundred on-demand Dsv5 cores of approved allowance and still fail to launch a single spot Dsv5 core, because the spot counter for that family started at its own default and you never raised it. The two counters share a family name in the portal but are distinct rows, and `az vm list-usage` lists the low-priority and spot counters separately from the standard ones.

### Do spot or low-priority VMs have a separate quota from regular VMs?

Yes. Spot and low-priority cores are tracked under dedicated counters, separate from on-demand vCPU quota for the same VM family. Approved standard quota grants you nothing on the spot side; you request the spot or low-priority increase independently, scoped to the same region and family.

To confirm a spot quota wall, read the usage table and look specifically for the low-priority or spot rows rather than the standard family rows:

```bash
az vm list-usage --location eastus --output table | grep -i "spot\|low"
```

If the spot counter for your family sits at its limit, the fix is a separate increase request for that spot counter, filed the same way as a standard increase but selecting the spot or low-priority quota type. Raising the standard family does not touch it.

Spot has a second failure that is not a quota at all and gets conflated with one: `OverconstrainedAllocationRequest`. This appears when the combination of your spot price cap, the eligible sizes, the zone, and the region leaves no offer the platform can fulfill at that moment, because spot capacity is the spare inventory that evicts under pressure and the spare pool for your exact constraints is empty. The fix is to loosen constraints rather than to request quota: widen the set of acceptable sizes so the scheduler can place you on whatever spare hardware exists, raise the maximum price you will pay so you are not eliminated by a price ceiling below the current spot rate, or relax the zone pinning. The discipline mirrors the rest of this guide. Read whether the message names an approved limit, which means request, or names constraints and capacity, which means loosen and retry. Spot rewards flexibility precisely because it is selling whatever is left over, and a rigid request against a thin spare pool fails where a flexible one succeeds.

## When AKS, Scale Sets, and Autoscale Hit the Quota Wall

Quota failures rarely arrive at a tidy moment when an engineer is watching a single `az vm create`. They arrive when something scales, and the most common surprise is an Azure Kubernetes Service node pool that cannot grow. The cluster autoscaler decides it needs more nodes, asks the underlying virtual machine scale set to add instances, and the scale set fails to allocate them because the node VM family has no remaining quota in the region. To the Kubernetes operator this looks like pods stuck pending with no obvious cause; to the platform it is a textbook `QuotaExceeded` against the node pool's VM family counter, buried in the scale set's activity rather than surfaced in the cluster.

You find it by reading the right layer. The Kubernetes events show the symptom, a failure to scale up, and the scale set's deployment or activity log shows the cause, the quota or allocation error on the instances the autoscaler requested:

```bash
# Symptom at the Kubernetes layer
kubectl get events -A --field-selector reason=FailedScaleUp

# Cause at the scale set layer: read the node resource group's activity
az aks show -g rg-aks -n aks-prod --query nodeResourceGroup -o tsv
az monitor activity-log list \
  --resource-group MC_rg-aks_aks-prod_eastus \
  --offset 1h \
  --query "[?contains(operationName.value,'write')].{op:operationName.localizedValue, status:status.value, sub:subStatus.localizedValue}" -o table
```

The `subStatus` on the failed scale operation carries the quota or allocation reason, and from there the fix is the same as any compute quota: confirm which family counter is full with `az vm list-usage`, then either request an increase for that family in that region or change the node pool to a VM size that has headroom. Changing the node VM size is often the faster fix in an incident, because adding a second node pool on a different family sidesteps the exhausted counter entirely while a quota request is in flight. The deeper treatment of why nodes will not come up lives in the guide to [AKS pods stuck in the pending state](/2022/07/25/fix-aks-pods-pending/), and quota is one of the named causes there for exactly this reason.

### Why does my AKS node pool fail to scale up?

The most common cause is that the node pool's VM family has no remaining vCPU quota in the region, so the underlying scale set cannot allocate new instances and pods stay pending. Read the node resource group's activity log for the quota or allocation reason, then raise that family's limit or move the node pool to a size with headroom.

Virtual machine scale sets outside Kubernetes behave the same way, and they introduce a planning hazard worth calling out. Because scale set instances draw from the same family and regional counters as standalone VMs, an autoscale rule can silently consume the headroom that a later, unrelated deployment was counting on. A team scales a web tier scale set up during a traffic spike, the scale set eats the remaining Dsv5 regional cores, and an engineer in another project fails to deploy a single Dsv5 VM an hour later with a quota error that has nothing visibly to do with the web tier. The counters are shared across the subscription and region, so capacity planning has to be done at that level, not per project. This is also why monitoring usage against limits, rather than reacting to failures, is the only reliable way to run a busy subscription, and it is the heart of the prevention section.

## A Worked Diagnosis: Family Headroom With a Regional Total Wall

Walk a concrete case to see the dual-counter design bite. A team runs a batch fleet on the Fsv2 family in East US and decides to add a new analytics tier on the Esv5 family in the same region. They have never run Esv5 there, so its family counter starts at a modest default, but they assume the region is "their region" and capacity is a solved problem. The Esv5 deployment of sixteen cores fails with `QuotaExceeded` naming the Standard ESv5 Family vCPUs counter. The engineer reads only the word quota, opens the increase form, and raises the total regional vCPUs, reasoning that more regional cores must mean more room. The redeploy fails identically, because the wall was never the regional total; it was the Esv5 family counter sitting at its low starting value. The correct request was an Esv5 family increase, and reading the named resource in the error would have routed it correctly the first time.

The mirror case is just as instructive. A different team has generous family limits across Dsv5, Esv5, and Fsv2, each raised over a year of growth, but the Total Regional vCPUs counter was never raised in step. They scale three tiers at once for a launch, each family has plenty of room individually, and the deployment fails on the regional total because the sum across families crossed the aggregate ceiling. Here the family increases were the distraction and the regional total was the real wall. The lesson both cases teach is the one the diagnosis table encodes: read the exact counter named in the error, confirm it with `az vm list-usage`, and request that counter, because the family limit and the regional total are independent walls and the error always tells you which one you hit if you read past the word quota.

## How Quota Errors Surface Through ARM and Bicep Deployments

When you deploy a VM directly, the quota error is immediate and obvious. When you deploy through an Azure Resource Manager template or a Bicep file as part of a larger stack, the same error hides inside the deployment's operation details, and engineers often misread the parent failure as a template problem. Resource Manager reports the overall deployment as failed and the specific VM or scale set resource as the failing operation, with the quota or allocation code nested in that operation's status message. The template is correct; the platform refused the resource for capacity reasons. Reading the inner operation is the skill, and it is identical to the inner-error reading that the guide to [fixing ARM template deployment failures](/2022/10/24/fix-arm-template-deployment-errors/) treats as the first move for any deployment failure.

Pull the failed operation and read its status message rather than trusting the top-level summary:

```bash
az deployment operation group list \
  --resource-group rg-stack \
  --name analytics-stack \
  --query "[?properties.provisioningState=='Failed'].{resource:properties.targetResource.resourceType, message:properties.statusMessage}" \
  -o json
```

The `message` field contains the inner error object, and inside it the code resolves to one of the three families this article walks. From there the diagnosis is the same as a direct deployment, and the fix is the same, with one template-specific addition: parameterize the VM size and the region so that switching to an available size or a region with capacity is a parameter change rather than a template rewrite. A template that hardcodes a single size in a single region turns every capacity or catalog failure into an edit; a template that takes size and location as parameters turns the same failure into a redeploy with a different value, which is the difference between a five-minute fix and a code review. Understanding how Resource Manager orchestrates and reports these operations is covered in the deep dive on [how Azure Resource Manager works](/2022/05/16/azure-resource-manager-arm-explained/), and the control-plane context there explains why the quota check happens at resource provisioning time rather than at template validation, which is why a template that validates cleanly can still fail to deploy.

## The Wrong-Family Approval and Other Request Traps

A request approved for the wrong counter feels like progress and delivers none, and a few traps account for most of these. The first is the family mismatch already shown: approving more regional total when the family was full, or more family when the regional total was full. The second is the region mismatch, approving an increase in the region you usually work in while the failing deployment targeted a newer region with its own untouched defaults. The third is the spot mismatch, approving standard cores when the deployment was a spot request that needed the separate spot counter. The fourth is the subscription mismatch, approving the limit in one subscription while the pipeline deployed into another. Each of these produces the same demoralizing pattern, a request granted and a deployment that fails identically, and each is prevented by confirming the exact counter, region, and subscription named in the error before filing anything.

There is also a timing trap. A self-service increase that the platform approves instantly takes effect for the next deployment, but a request routed to support for review does not raise your limit until it is approved, and deploying again in the meantime fails against the unchanged limit. Watching the request's state rather than assuming approval, and confirming the new limit with `az quota show` or `az vm list-usage` before retrying, closes that gap. The confirming command is the same one you used to diagnose, which is why the usage listing is the most-used tool in the entire workflow, from first failure to final verification.

## Prevention: Watch Usage Against Limits Instead of Reacting to Failures

Every quota failure described so far is preventable, because a quota wall is never a surprise to the platform, only to the team that did not watch the counter approaching it. The shift from reactive to proactive is the single highest-leverage change you can make, and it rests on monitoring current usage against approved limits continuously rather than discovering the limit at deployment time. The data is already available from the same usage listing you used to diagnose, and turning it into a watch is a matter of evaluating headroom regularly and acting before the gap closes.

A simple watch reads the usage for every region you operate in and flags any counter above a threshold, say eighty percent of its limit, which leaves room to request an increase before a scaling event consumes the rest:

```bash
for region in eastus westus2 westeurope; do
  echo "== $region =="
  az vm list-usage --location "$region" -o json \
    | jq -r '.[] | select(.limit > 0)
        | select((.currentValue / .limit) >= 0.8)
        | "\(.name.localizedValue): \(.currentValue)/\(.limit)"'
done
```

Running that on a schedule and routing its output to a chat channel or a ticket turns the day-of-launch quota scramble into a routine top-up done a week ahead. The principle is to request increases when you cross a usage threshold, not when a deployment fails, so the approval round trip happens off the critical path. For teams that scale unpredictably, the threshold should be lower and the watch more frequent, because an autoscale event can close a wide gap in minutes.

### How can I avoid hitting quota limits during a scaling event?

Monitor each region's vCPU usage against its limits on a schedule, request increases when any family or the regional total crosses roughly eighty percent, and pre-provision capacity for predictable peaks. For unavoidable surges, reserve capacity in advance so the cores you will need are already set aside.

Beyond watching, a few design choices shrink the surface where quota bites. Spreading a workload across two families gives you a fallback family with headroom when one is contended, so a deployment can fall back rather than fail. Spreading across two regions does the same at the regional level and is the only real protection against a region-wide capacity squeeze. Reserving capacity in advance, through on-demand capacity reservations, guarantees the hardware for a known peak so allocation cannot fail when it matters most, trading the cost of holding reserved cores against the cost of a failed scale-out. And requesting comfortable family and regional limits proactively in any region you intend to grow into, rather than starting from defaults at launch time, removes the cold-start quota problem that catches teams expanding into a new region. None of these eliminate the need to read errors correctly when they do occur, but together they move most of the failures from production incidents to scheduled maintenance, which is where capacity work belongs. Rehearsing the read-and-request loop on the [hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) builds the muscle memory so that when a real limit is approaching, checking usage and filing the right increase is automatic rather than improvised.

There is a governance angle that pairs with the monitoring. Because counters are shared across a subscription and region, a single subscription that hosts many teams will see one team's autoscale consume another team's headroom invisibly. Separating workloads that scale aggressively into their own subscriptions isolates their quota consumption, so a spike in one does not starve a deployment in another, at the cost of managing more subscriptions and requesting limits in each. Whether that isolation is worth the overhead depends on how often the shared counters cause cross-team surprises, and the deciding factor is contention: if you regularly see deployments fail because an unrelated workload ate the cores, the isolation pays for itself, and if you do not, a single well-monitored subscription is simpler.

## Related Failures That Look Like a Core Quota But Are Not

The word quota appears in many Azure errors that have nothing to do with vCPUs, and treating them all as core problems sends you to the wrong counter. Knowing the neighbors keeps you from raising compute limits that were never the issue. The most frequent imposter is a public IP address limit. A deployment of many VMs each with a public address can exhaust the public IP quota for the region while the vCPU counters sit comfortably below their limits, and the error names the network resource, not cores. You confirm it with the network usage listing rather than the compute one:

```bash
az network list-usages --location eastus --output table
```

That prints the public IP, network interface, virtual network, and load balancer counters with their limits, and a deployment failing on any of them needs an increase to that specific network counter, requested through the same Quotas experience but under the networking provider rather than compute. Raising vCPU quota does nothing for a public IP wall.

The second imposter is managed disk and storage limits. A fleet that attaches large premium disks can hit a storage account or disk count limit, or a regional storage quota, and the failure looks like a deployment problem while the cores were never the constraint. The third is the count of virtual machines themselves, which is a separate counter from cores: you can have core headroom yet hit a limit on the number of VMs in a region, particularly with many tiny VMs that consume few cores each but many VM slots. The fourth is the network interface count, which large multi-NIC deployments exhaust independently of cores. Each of these is read from `az network list-usages` or `az vm list-usage` depending on the resource, and each is raised against its own counter.

### Is SkuNotAvailable the same as a quota error?

No. `SkuNotAvailable` means the size is not offered to you in that location, which is a catalog decision, while a quota error means you exceeded an approved allowance of cores you can raise. A quota increase cannot fix `SkuNotAvailable`; you change the size or region instead.

There is also a family of failures that look like capacity but stem from your own constraints, of which the spot `OverconstrainedAllocationRequest` is the headline example, joined by proximity placement group constraints that force all instances into one datacenter that lacks room, and zone-pinned deployments that fail when one zone is short even though the region has capacity. Each of these resolves by loosening the constraint rather than requesting anything, and each is distinguished from a true quota error by the same reading discipline: the message names constraints and capacity, not an approved limit you crossed. The recurring theme across every imposter is that the named resource in the error is the truth, and the word quota in the banner is not, so the confirming command is always the one that reads the specific counter the message points at.

## The Verdict: Read the Counter, Then Act

The fastest path through any Azure quota exceeded failure is to refuse to act until you have decoded the error into one of three causes. If the message names an approved limit you crossed, you have `QuotaExceeded`, a soft governance wall, and the fix is a request scoped to the exact family or regional total the error named, in the exact region and subscription, confirmed against `az vm list-usage` before and after. If the message says the size is not available in the location, you have `SkuNotAvailable`, a catalog wall no request can move, and the fix is a different size or region chosen from the unrestricted set in `az vm list-skus`. If the message says there is insufficient capacity for the requested size, you have `AllocationFailed`, a real-time hardware wall, and the fix is flexibility on size, zone, or region, a deallocate-and-start cycle for an existing VM, or a capacity reservation for a peak you cannot risk. The discipline that ties them together is the quota-versus-capacity rule, and an engineer who internalizes it stops wasting days on requests that were never going to help and starts resolving the right failure on the first try. Watch your counters against their limits on a schedule, request headroom before a scaling event rather than after a failure, and treat the named resource in the error as the only fact that matters, and the quota exceeded banner stops being an incident and becomes a number you manage.

## Reading the Usage Listing Line by Line

The usage listing is the instrument panel for this entire problem, so it pays to read it precisely rather than skim for red. Each row carries a name, a current value, and a limit, and the name is the canonical counter that an increase request must match. The rows fall into three groups. The aggregate row, Total Regional vCPUs, sums the cores of every running compute instance in the region across all families, and it is the ceiling a multi-tier launch hits first when several families each have headroom. The per-family rows, one for each hardware generation you might deploy, such as Standard DSv3 Family vCPUs or Standard ESv5 Family vCPUs, govern individual sizes and are the ceiling a single-family scale-out hits. The resource-count rows, such as Virtual Machines, Virtual Machine Scale Sets, and Availability Sets, cap the number of those objects independently of how many cores they consume.

Reading current against limit on the named row is the confirmation step, and the gap between them is your remaining headroom for that counter. A subtlety that trips people is that the current value reflects allocated cores, which include running and stopped-but-allocated machines, but not fully deallocated ones, because a deallocated VM has released its host and no longer counts. This is why deallocating idle machines can reclaim headroom that a merely stopped machine still holds, and why a row sitting near its limit sometimes drops after a cleanup of forgotten allocated VMs.

### Does deleting or deallocating a VM free up quota immediately?

Deallocating or deleting a VM releases its cores back to the counter promptly, so the headroom returns and the usage value drops on the next listing. A merely stopped VM that remains allocated still holds its cores and its host, so stopping without deallocating does not reclaim the allowance.

The other detail worth internalizing is that the limit shown is the approved limit for your subscription in that region, not a platform maximum. Two subscriptions in the same region can show different limits on the same row because each negotiated its own allowances over time. A new subscription, or an existing one entering a region for the first time, shows the regional defaults, which are intentionally conservative so that a misconfigured automation cannot accidentally bill thousands of cores. Those defaults are the cold-start problem behind most new-region failures, and they are exactly what a proactive increase request, filed before you scale into the region, removes.

## The Self-Service Quota Experience and the Provider Model

The mechanism behind a modern increase request rewards understanding, because it explains why some requests clear in seconds and others sit in review. Azure exposes quotas through a dedicated resource provider, Microsoft.Quota, which models each counter as an addressable object under a scope. The scope for compute is the Compute provider in a region, and within it each counter has a canonical resource name that the API uses, distinct from the friendly label the portal shows. When you submit an increase, the provider checks the requested limit against the region's available capacity and your subscription's policy, and when both allow it the new limit is written immediately, which is the instant approval you see for routine vCPU bumps. When the requested value is large, or the region is capacity constrained, or the family is a scarce one, the request cannot be auto-satisfied and is routed to a support engineer who evaluates it against capacity planning, which is the review path with a tracking case and no fixed turnaround.

Working through the provider directly, rather than the portal, makes the increase reproducible and auditable. You read the current limits for a scope, identify the canonical name of the counter you need, and submit a new limit value as a limit object:

```bash
SCOPE="/subscriptions/<sub-id>/providers/Microsoft.Compute/locations/westeurope"

# Enumerate counters and their canonical names and current limits
az quota list --scope "$SCOPE" \
  --query "[].{name:name, limit:properties.limit.value}" -o table

# Inspect one counter in detail before changing it
az quota show --resource-name standardESv5Family --scope "$SCOPE" -o json

# Submit a new absolute limit for that counter
az quota update \
  --resource-name standardESv5Family \
  --scope "$SCOPE" \
  --limit-object value=128 limit-object-type=LimitValue
```

Because the operation is idempotent against an absolute target value rather than a delta, you can express your intended ceiling in a script and re-run it safely, which fits the infrastructure-as-code discipline the series favors. For counters the quota extension does not expose, or increases the self-service path declines, the support request remains the path, filed under the service and subscription limits category with the region, the canonical family, and the target value. Whatever path you use, verify the result with `az quota show` or the usage listing before redeploying, because an instant approval and a queued review look identical at submission time and only the confirmed limit tells you which one you got. Treat any specific default limit, scope name, or approval policy as something to verify against the current official quota documentation when you read this, since the provider's behavior and the defaults are revised regularly.

## Finding Where a Size Is Actually Available

When the diagnosis lands on `SkuNotAvailable` or a stubborn `AllocationFailed`, the practical question becomes where the size you want is offered and has room, and the catalog answers it across regions and zones. The same `az vm list-skus` that confirms a single region's restriction can map a size's availability so you choose the alternative deliberately rather than by trial and error. To see which zones in a region offer a size, read the zone details:

```bash
# Zone availability for a size in a region
az vm list-skus \
  --location eastus \
  --size Standard_E8s_v5 \
  --zone \
  --query "[].{name:name, zones:locationInfo[0].zones, restrictions:restrictions[].type}" -o json
```

An empty restrictions array with all three zones listed means the size is broadly available; a restrictions array with a zone type and a subset of zones means some zones are excluded, which routes you to the open zones rather than a new region. To compare regions, you run the size query across a candidate set and pick the nearest region without a location restriction, which lets you keep the workload geographically close while escaping the constrained location. The decision rule for the alternative stays consistent: prefer the same family generation in an open zone of the same region first, then the same family in a nearby region, then an adjacent family in the original region, choosing in that order because each step preserves more of the workload's original characteristics. The catalog turns "not available" from a dead end into a menu, and reading it is faster than guessing through redeployments that each cost minutes.

Scarce specialized families deserve a note, because they fail differently. The largest memory-optimized sizes and the accelerated families with attached accelerators are deployed to fewer regions, carry lower default limits, and are more often capacity constrained, so a failure on one of them is more likely to be a genuine catalog or capacity wall than a simple soft limit. Increases on these families are also more frequently routed to review rather than auto-approved, because the underlying inventory is thinner and the platform manages it more tightly. Planning for these sizes means requesting their limits earlier, confirming their regional availability before committing an architecture to them, and building a fallback to a more widely available family for the cases where the preferred one cannot be allocated when you need it.

## A Runbook for the Next Quota Exceeded Banner

When the banner appears again, the sequence that resolves it fastest is short enough to commit to memory. Capture the inner error code, the region and zone, the size, and the subscription before changing anything, because those four facts route the entire diagnosis. Decode the code into one of the three families, reading the named resource rather than the word quota. For the soft-limit family, confirm the named counter with the usage listing, request that exact counter in that region and subscription, and confirm the new limit before retrying. For the catalog family, read the restriction in the size listing, decide whether it is a location or zone limitation, and pick an open zone or region accordingly. For the capacity family, confirm quota and catalog are both clear, then apply flexibility, retrying a sibling size, an open zone, or a different region, deallocating and starting an existing VM, or reserving capacity for a peak you cannot gamble on.

The runbook works because it front-loads reading and back-loads action, which is the inversion of the instinct that causes the wasted days. The instinct is to act on the word quota immediately, file an increase, and wait. The discipline is to read which counter and which cause first, so the action you take is the one that resolves the actual failure. Teams that adopt the runbook stop seeing quota errors as random platform misbehavior and start seeing them as a small, finite set of well-understood conditions, each with a confirming command and a matching fix, which is exactly what they are. The same patient, read-first method is what separates an engineer who can defend a diagnosis in an incident review from one who guessed and got lucky, and it is the habit the entire troubleshooting block of this series is built to instill.

## Capacity Reservations: Turning a Probabilistic Allocation Into a Guaranteed One

For the workloads where a failed scale-out is unacceptable, the answer to `AllocationFailed` is to stop gambling on real-time inventory and reserve the hardware in advance. An on-demand capacity reservation holds a pool of a specific size in a specific zone of a region, set aside for your subscription, so that when you create or scale a VM of that size into the reservation the allocation succeeds because the host was already held. You create a reservation group, then a reservation within it for the size and zone you need, and you associate VMs with it at deployment time:

```bash
# Create a reservation group, then reserve a size in a zone
az capacity reservation group create \
  --resource-group rg-capacity \
  --name crg-prod \
  --zones 1

az capacity reservation create \
  --resource-group rg-capacity \
  --capacity-reservation-group crg-prod \
  --name cr-esv5 \
  --sku Standard_E8s_v5 \
  --capacity 10 \
  --zone 1
```

Once the reservation exists, VMs and scale sets created against the reservation group draw from the held pool, and their allocation cannot fail for capacity because the capacity is yours. The trade-off is direct and worth stating plainly: you pay for the reserved cores whether or not a VM is running on them, because the platform is holding the hardware out of the shared pool on your behalf. That cost is the price of certainty, and it is justified for a launch you cannot afford to have fail, a failover target that must be there when the primary dies, or a scheduled batch that must run on time. It is not justified for elastic workloads that tolerate a retry, where the flexibility levers, a sibling size or an open zone, resolve the occasional allocation failure at no standing cost. The deciding factor is the cost of a failed allocation: when that cost is high and predictable, reserve; when it is low and the workload is flexible, retry with flexibility instead.

A reservation also interacts with quota in a way that closes the loop on the two-layer model. Creating a reservation consumes your vCPU allowance for that family and region, because reserved cores are cores you are permitted to hold, so a reservation can itself fail with `QuotaExceeded` if the family limit has no room for the reserved pool. You raise the family limit first, then create the reservation, and the reservation then guarantees the allocation that the quota now permits. Governance grants the right to run the cores, the reservation guarantees the hardware to run them on, and together they remove both the soft-limit and the capacity failure for the workload that needs the certainty.

## Default Limits, New Subscriptions, and the Cold-Start Problem

A large share of first-time quota failures trace to a single fact: a region you have never deployed into gives your subscription conservative default limits, and a subscription type meant for evaluation gives lower defaults still. Pay-as-you-go and enterprise subscriptions carry higher starting allowances than trial or credit-based ones, and even within a generous subscription each new region starts near the defaults until you raise it. The result is a cold-start problem. A team that has scaled comfortably in one region for a year assumes the platform "knows" they run large fleets, expands into a second region for resilience, and fails immediately because the second region's counters are at their starting values. The platform does not carry your scale from one region to another; each region is its own ledger.

The fix is to treat a new region's quota as a setup step, not a runtime discovery. Before you deploy anything meaningful into a region, read its current limits with the usage listing, compare them to the cores your architecture will need at peak, and request the family and regional totals you will require ahead of the first real deployment. Doing this as part of standing up the region, alongside the network and identity setup, removes the cold-start failure entirely and moves the approval round trip off the critical path. For subscriptions created from trials or credit grants, the defaults are low enough that even a modest deployment can fail, and the same proactive request resolves it; the limits are not punishments, they are guardrails that you lift deliberately as your legitimate need grows.

### Why does a new Azure region start with lower quota than my main region?

Quota is tracked per region and starts at conservative defaults for any region your subscription has not used, regardless of how much you run elsewhere, because the platform applies allowances per region as a guardrail. Request the family and regional limits you will need as part of standing up the new region, before the first real deployment.

## Monitoring Quota With Alerts Rather Than Scripts Alone

A scheduled script that prints headroom is a good start, but a busy environment benefits from alerts that fire when a counter approaches its limit without anyone running anything. Azure surfaces usage metrics that you can alert on, so a counter crossing a threshold raises a notification the same way a high-CPU condition would. The pattern is to define an alert on the relevant usage metric for the subscription and region, set the threshold to a fraction of the limit that leaves time for an approval round trip, and route the notification to the team that owns capacity. The threshold is a judgment: too high and the alert fires with no time to act before a scaling event consumes the rest, too low and it fires constantly on healthy churn. A starting point of eighty percent for slow-moving workloads and lower for ones that scale fast gives room to request an increase before the wall, and you tune it from experience.

The alerting approach pairs with the design choices from the prevention section rather than replacing them. Spreading across families and regions reduces how often any single counter approaches its limit, the alert catches the cases that still do, and the proactive request clears them before they fail a deployment. Together they make a quota wall something the team sees coming and steps over, rather than something a deployment discovers at the worst possible moment. The investment is small relative to the cost of a launch that fails on capacity it could have requested a week earlier, and rehearsing the full loop, from alert to confirmed increase, on practice scenarios builds the reflex so the real event is routine. The troubleshooting drills are built around exactly this kind of read-confirm-request rehearsal, which is why pairing the labs with scenario practice turns a theoretical understanding of the three causes into a fix you can execute under pressure.

## Quota and Disaster Recovery: The Failover That Fails on Capacity

A disaster recovery design has a quota dependency that is invisible until the day it matters. If your recovery plan is to spin up the production fleet in a secondary region when the primary fails, that secondary region needs the family and regional vCPU allowances to hold the entire fleet, and a secondary you have kept idle to save money has almost certainly never had its limits raised. The failover then fails on `QuotaExceeded` at the exact moment the primary is down, which is the worst possible time to discover a soft limit and the worst possible time to file an increase that might route to review. The recovery that was supposed to take minutes stalls behind a quota request, and the outage extends.

The prevention is to provision the recovery region's quota as part of the recovery design, sized for the full failover footprint, and to verify it on the same cadence you test the failover itself. Reading the secondary region's usage limits against the cores the recovery plan needs, and requesting the gap ahead of time, removes the capacity dependency from the recovery path. For recovery targets where even an instant allocation cannot be risked, a capacity reservation in the secondary region guarantees the hardware will be there, at the standing cost of holding it, which is a cost many teams accept for a tier-one workload's recovery target precisely because the alternative is a failover that cannot allocate. The general lesson generalizes beyond disaster recovery: any region you intend to run a workload in, even occasionally and even under duress, needs its quota sized for that workload in advance, because the platform will not raise a limit faster because you are mid-incident.

## Subscription, Regional, and Resource Group Limits Are Different Walls

Three scopes of limit coexist and get conflated, and separating them prevents another class of misdirected requests. The vCPU counters this article centers on are regional, tracked per region per subscription, and they are what `QuotaExceeded` on a VM deployment almost always names. Distinct from those are subscription-wide limits that are not regional, such as the number of resource groups a subscription may hold or the number of certain resource types across all regions, which a deployment can hit independently of any regional core count. Distinct again are resource group limits, such as the number of resources in a single group, which a very large deployment into one group can reach while every regional and subscription counter has room. Each scope is read and raised differently, and a deployment failing on one will not be helped by raising another.

The diagnostic habit that sorts them is, once more, reading the named resource and its scope in the error. A regional vCPU counter names a family or the regional total and a region; a subscription limit names a subscription-wide resource type with no region; a resource group limit names the group. The usage and network listings cover the regional counters, the subscription's limits are read from the subscription's own limit listings, and the resource group's resource count is read from the group itself. Knowing which scope you are in tells you which listing confirms the wall and which request raises it, and it keeps a regional core problem from being answered with a subscription-level request that changes nothing about the failing deployment. The control-plane model that organizes these scopes, and why a limit applies at one level rather than another, is the kind of foundational understanding the deep dive on [how Azure Resource Manager works](/2022/05/16/azure-resource-manager-arm-explained/) is meant to give, and it is what lets you reason about a new limit you have not seen before rather than memorizing each one.

## Why the Same Deployment Worked Yesterday and Fails Today

A failure that erodes trust in a diagnosis is the one that is intermittent: the identical template deploys fine in the morning and fails on capacity in the afternoon. This is not a bug and it is not your quota changing under you; it is the live nature of allocation. The pool of free hosts of a given size in a given zone rises and falls as every tenant in that datacenter creates and releases machines, so a size that had room at one hour can be momentarily exhausted at another, particularly for popular sizes in busy regions during business hours. A quota wall, by contrast, does not move on its own, so an intermittent failure is a strong signal that you are looking at `AllocationFailed` rather than `QuotaExceeded`, and the message text confirms it.

The practical consequence is that flexibility, not requests, smooths intermittent capacity failures. A deployment that can accept any of three sibling sizes, or any of a region's zones, will succeed far more reliably than one pinned to a single size in a single zone, because the scheduler can place it wherever the spare pool happens to have room at that moment. Building that flexibility into templates and scale set definitions, by allowing a set of acceptable sizes and not over-constraining zones, turns the afternoon failure into a non-event. For the workloads that cannot accept any flexibility, the reservation is the answer, because reserved capacity does not fluctuate. Reading the intermittency as a capacity signal, rather than chasing it as a phantom quota change, is what keeps you from filing increase requests against a counter that was never full.

This volatility is also why the advice to retry an `AllocationFailed` is not a brush-off. A genuine retry, ideally with a small change of size or zone, frequently succeeds within minutes because the pool refills as other tenants release hosts, and a deallocate-and-start cycle on an existing VM re-enters the placement queue against the current inventory rather than the stale one that held the old host. Retrying the exact same size in the exact same exhausted zone, with no change, is the version of retry that does not help, because it asks the same empty pool the same question. The difference between a useful retry and a useless one is whether anything about the request changed to let the scheduler find room.

## Managing Quota Across Many Subscriptions

Large estates rarely live in one subscription, and quota behavior across many of them follows a rule worth stating directly: counters never pool across subscriptions, so each one carries its own allowances in each region and a generous limit in one grants nothing to a deployment in another. This is a deliberate isolation boundary, and it is useful, because it lets you cap how many cores a given workload or team can ever bill by capping the subscription that hosts it. It also means that consolidating workloads into fewer subscriptions concentrates their quota consumption, so a team that scales aggressively can starve a quieter neighbor sharing the same subscription and region, while separating them into their own subscriptions isolates the contention at the cost of more boundaries to manage.

The decision between consolidation and separation turns on contention rather than tidiness. If deployments regularly fail because an unrelated workload consumed the shared cores, the isolation of a dedicated subscription pays for itself by giving each workload its own ledger to watch and raise. If the shared counters rarely cause cross-team surprises, a single well-monitored subscription is simpler and avoids the overhead of requesting limits in many places. Whichever shape you choose, the operational practice is the same: read each subscription's usage per region on a schedule, request headroom against the counters approaching their limits before a scaling event, and treat a new subscription entering a region exactly like a new region, with its conservative defaults raised as a setup step rather than discovered at the first failed deployment. The scoping that makes counters per subscription and per region also makes capacity planning a per-subscription, per-region exercise, and an estate that treats it that way stops being surprised by walls that were always visible in the usage listings.

## Frequently Asked Questions

### Q: What does a quota exceeded vCPU error mean in Azure?

It means your subscription has reached the approved number of cores it is allowed to run for a particular VM family, or across all families combined, in a specific region. Azure tracks compute cores per subscription, per region, and per family, and a deployment must fit under both the family counter for the size you chose and the total regional counter. The error names which counter you crossed and shows your current usage against the limit. This is a soft governance limit rather than a hardware shortage, which is the key distinction: you can request an increase to that counter, and many standard increases are approved automatically within seconds when the region has capacity to back them. Read the named resource in the message, confirm it with the usage listing for the region, and request that exact counter rather than guessing, because the family limit and the regional total are independent walls.

### Q: How do I request an Azure quota increase for vCPUs?

Open the centralized Quotas page in the portal, filter to the Compute provider, your subscription, and the region, then locate the row that is full, whether a specific VM family or the total regional vCPUs, and enter the new limit you want. Submit the request, and if the region has capacity and the increase is within policy, the platform approves it on the spot; otherwise it routes to a support engineer with a tracking case. The same operation is scriptable through the Azure CLI quota extension, where you set an absolute new limit value against the counter's canonical name for a region scope, which makes the increase reproducible and reviewable. Whichever path you use, confirm the new limit took effect with a usage listing or a quota show before redeploying, because a queued review and an instant approval look identical at submission and only the confirmed value tells you which you received.

### Q: Why is vCPU quota scoped per region and per VM family?

Azure manages compute capacity and billing controls at the granularity of each hardware generation in each datacenter, so the allowances follow the same shape. Each VM family, such as the Dsv5 or Esv5 generation, draws from its own hardware pool in a region, and each carries an independent per-region core counter. Above the families sits a Total Regional vCPUs counter that sums every running core across all families in the region. A deployment must satisfy both the family counter for the size you picked and the regional total at once. This dual-counter design is why you can have hundreds of unused cores in your regional total and still fail because one family is maxed out, and why raising the regional total does nothing when the family was the wall. Reading which counter the error names is the whole diagnosis.

### Q: What is SkuNotAvailable versus a quota error in Azure?

`SkuNotAvailable` is a catalog statement that the size you requested is not offered to your subscription in that region or those zones, while a quota error is a governance statement that you exceeded an allowance of cores you can raise. The two require opposite actions. A quota increase will never resolve `SkuNotAvailable`, because no allowance was crossed; the size is simply not in the menu for that location, often because the hardware generation has not rolled out there or is restricted at the catalog level. You confirm `SkuNotAvailable` by listing the size's restrictions in the region, which will show a location or zone restriction entry. The fix is to choose a different region where the size is offered, or a different size that is available in your region, rather than filing a request that will be approved and change nothing about the deployment.

### Q: Do spot or low-priority VMs have separate quota from regular VMs?

Yes, and this catches teams the first time they use spot capacity. Spot and low-priority cores, the discounted evictable inventory Azure sells from spare hosts, are tracked under their own counters, completely separate from the on-demand vCPU counters for the identical VM family. Approved standard quota grants you nothing on the spot side, so a deployment of spot instances can fail with a quota error while your standard quota for the same family sits wide open. The usage listing shows the spot and low-priority rows separately from the standard family rows, and a spot quota wall is raised with its own increase request, scoped to the spot or low-priority quota type for that region and family. Spot also has a non-quota failure, an overconstrained allocation request, which is resolved by loosening size, zone, or price constraints rather than by requesting more allowance.

### Q: How do I check my current Azure quota usage?

Run the compute usage listing for the region you care about, which prints every counter with its current value beside its approved limit. From the Azure CLI the command lists the regional total, every family counter, and the resource-count counters in one table for a location, and the equivalent PowerShell cmdlet returns the same data, which you can filter to surface only the counters near their limits. The usage listing is the single most-used tool in the entire quota workflow, because it both diagnoses a failure, by showing which counter is at its limit, and verifies a fix, by showing the raised limit after an increase. Running it on a schedule across every region you operate in, and flagging any counter above a threshold, is the foundation of preventing failures rather than reacting to them, since a counter approaching its limit is visible well before a deployment hits the wall.

### Q: How do I fix an AllocationFailed error when my quota is fine?

`AllocationFailed` means the datacenter has no free host of the requested size in the region or zone at that moment, so it is a real-time capacity shortage rather than a limit you crossed. The fix is flexibility. Retry with a sibling size in the same family, which often has a less contended pool, or target a different availability zone, or drop the zone constraint so the platform places the VM wherever the region has room. For a stopped VM that fails to start, fully deallocate it and start it again so it is re-placed onto hardware with current capacity, because a merely stopped VM still holds its old host. For peaks you cannot risk failing, reserve capacity in advance so the hardware is held for you. A retry that changes nothing about the request and aims at the same exhausted pool will keep failing, so a useful retry always changes the size, zone, or region.

### Q: Why does my AKS node pool fail to scale up with no clear error?

The most common hidden cause is that the node pool's VM family has run out of vCPU quota in the region, so the underlying virtual machine scale set cannot allocate the new instances the cluster autoscaler requested, and pods sit pending. The Kubernetes layer only shows the symptom, a failure to scale up, while the cause lives in the scale set's activity in the node resource group, where the quota or allocation reason appears on the failed write operation. Read that activity log, confirm which family counter is full with a usage listing, and either request an increase for that family in the region or move the node pool to a VM size that has headroom. Adding a second node pool on a different family is often the faster incident fix, because it sidesteps the exhausted counter while a quota request is in flight.

### Q: Will deallocating a VM free quota immediately for a new deployment?

Yes. A deallocated VM releases its host back to the platform and no longer counts against the vCPU counter, so the headroom returns and the usage value drops on the next listing, freeing those cores for a new deployment promptly. The important distinction is between stopped and deallocated. A VM that is stopped from inside the guest, or stopped without deallocation, remains allocated, still holds its host, and still counts against your quota, so stopping that way reclaims nothing. Only a full deallocate, which the platform performs when you stop a VM through the Azure control plane or run the deallocate command, releases the cores. This is why a quick way to reclaim headroom near a limit is to find and deallocate forgotten allocated VMs that are running but idle, which can drop a counter enough to let a blocked deployment through without any increase request.

### Q: Does a quota increase guarantee my VM will deploy?

No, and conflating the two causes real confusion. A quota increase changes what your subscription is permitted to run, but it does not create hardware. If you raise a family limit in a region that is currently capacity constrained for that size, your next deployment can still fail with `AllocationFailed` even though the quota now allows it, because the governance layer said yes while the capacity layer has nothing free. The two layers are independent by design: quota is the policy, allocation is the supply. When a deployment fails after an approved increase, read the new error, because you have almost certainly moved from a quota failure to a capacity failure, and the fix shifts from requesting to flexibility on size, zone, or region, or to reserving capacity so the hardware is held for you before you need it.

### Q: How long does an Azure quota increase take to approve?

There is no single fixed time, because two paths exist. Routine vCPU increases that the region can satisfy from available capacity and that fall within policy are approved by the self-service flow within seconds, so the deployment that just failed succeeds on the next attempt. Larger increases, requests in capacity-constrained regions, and requests for scarce specialized families cannot be auto-satisfied and route to a support engineer for review, which carries a tracking case and a turnaround that depends on the request and the region. Because the two paths look identical at submission, the reliable practice is to watch the request's state and confirm the new limit with a usage or quota listing before retrying, rather than assuming approval. Verify the current self-service behavior against the official quota documentation when you read this, since the policy and the auto-approval thresholds change.

### Q: Why did my deployment fail on quota when I have plenty of regional cores left?

Because the wall was almost certainly the per-family counter, not the regional total. The two are independent, and the family counter for the specific size you deployed can be full while the Total Regional vCPUs counter has hundreds of cores to spare. This is the most common quota surprise. The error names the family resource if you read past the word quota, and the usage listing will show that family row at its limit while the regional total sits well below its own. The fix is to request an increase for that exact family in that region, or to deploy a size from a different family that still has headroom, which sidesteps the full counter entirely. Raising the regional total in this situation changes nothing, because the regional total was never the constraint.

### Q: Is SkuNotAvailable a regional restriction or a temporary capacity issue?

It can be either, and the restriction detail in the size listing tells you which. If the restriction entry has a location type, the size is not offered to your subscription anywhere in that region, which is a catalog decision you cannot wait out; you must change region or size. If the entry has a zone type listing specific zones, the size is offered in the region but excluded from those zones, often because a newer hardware generation has not rolled out evenly, so you target an open zone. Some capacity-driven restrictions are more fluid and can clear as the platform rebalances, but you should not architect around the hope that a location restriction will lift. Read the restriction type, treat a location restriction as a hard catalog wall and a zone restriction as a routing decision, and pick the alternative deliberately from the unrestricted sizes the listing shows.

### Q: How do I plan quota for a disaster recovery region?

Size the recovery region's vCPU allowances for the full footprint you would fail over, not for the idle baseline you keep there to save money. A recovery plan that spins up the production fleet in a secondary region needs the family and regional limits to hold that fleet, and a secondary you have kept minimal almost certainly has limits near the defaults. If you discover that during an actual failover, the recovery stalls behind an increase request at the worst possible time. Provision the recovery region's quota as part of the recovery design, verify it on the same cadence you test the failover, and for tier-one targets consider a capacity reservation so the hardware is guaranteed rather than merely permitted. The principle generalizes: any region you might run a workload in, even under duress, needs its quota sized for that workload ahead of time, because the platform will not raise a limit faster mid-incident.

### Q: Can a public IP or disk limit cause an error that looks like a quota problem?

Yes, and treating every quota-shaped error as a core problem sends you to the wrong counter. A deployment of many VMs each with a public address can exhaust the region's public IP allowance while the vCPU counters sit well below their limits, and the error names the network resource rather than cores. The network usage listing shows public IP, network interface, virtual network, and load balancer counters, and a deployment failing on one of those needs an increase to that specific counter under the networking provider, not a vCPU increase. Managed disk and storage limits, the count of virtual machines independent of their cores, and network interface counts behave the same way, each its own wall read from its own listing. The recurring discipline is that the named resource in the error is the truth, so confirm the specific counter the message points at before requesting anything.

### Q: What is the difference between OverconstrainedAllocationRequest and a quota error?

`OverconstrainedAllocationRequest`, which you meet most often with spot deployments, means the combination of constraints you set, the spot price cap, the eligible sizes, the zone, and the region, leaves no offer the platform can fulfill at that moment, whereas a quota error means you crossed an approved allowance. The overconstrained failure is about your constraints meeting thin supply, not about a limit, so the fix is to loosen rather than request. Widen the set of acceptable sizes so the scheduler can place you on whatever spare hardware exists, raise the maximum price so a low ceiling does not eliminate every current offer, or relax the zone pinning. Spot capacity is the spare inventory Azure sells cheaply and reclaims under pressure, so a rigid request against a thin spare pool fails where a flexible one succeeds. As with capacity failures generally, the message naming constraints and supply rather than an approved limit is the signal that requesting more allowance is the wrong move.

### Q: Should I request quota proactively or wait until a deployment fails?

Request proactively, because the approval round trip belongs off the critical path. A quota wall is never a surprise to the platform, only to the team that did not watch the counter, and the data to watch is the same usage listing you would use to diagnose a failure. Read each region's counters on a schedule, flag any family or regional total crossing roughly eighty percent of its limit, and request the headroom before a scaling event consumes the rest. For workloads that scale fast, set the threshold lower and check more often, because an autoscale event can close a wide gap in minutes. Pair the watching with alerts on the usage metrics so a counter approaching its limit raises a notification without anyone running a script. The payoff is that the day-of-launch scramble becomes a routine top-up done a week ahead, and most quota failures move from production incidents to scheduled maintenance.

### Q: Why are large GPU and memory-optimized VM sizes harder to get quota for?

The largest memory-optimized sizes and the accelerated families with attached accelerators are deployed to fewer regions, start with lower default limits, and run on a thinner inventory, so failures on them are more often genuine catalog or capacity walls than simple soft limits. Increases for these families are also more frequently routed to support review rather than auto-approved, because the platform manages the scarce hardware more tightly. Planning for these sizes means requesting their limits earlier, confirming their regional and zonal availability before you commit an architecture to them, and building a fallback to a more widely available family for the times the preferred size cannot be allocated when you need it. Reading the size listing across candidate regions tells you where the family is offered, and treating its limits as something to arrange ahead of time, rather than discover at deployment, avoids the worst surprises with constrained hardware.
