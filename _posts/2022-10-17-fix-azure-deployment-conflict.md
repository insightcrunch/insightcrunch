---
layout: post
title: "Fix Azure Deployment Conflict Errors"
page_title: "Fix Azure Deployment Conflict Errors: Diagnose 409 Conflict, Another Operation Is In Progress, and Resource Lock Failures"
date: 2022-10-17
categories: ["Technology"]
tags: ["Azure", "ARM", "Troubleshooting", "DevOps", "Deployment", "Cloud Computing"]
excerpt: "An Azure deployment conflict error means another operation already owns the resource. Learn the four root causes, their confirming checks, and how to fix each."
image: "/assets/images/blog/blog-84.webp"
reading_time: 60
author: "alex-cunningham"
last_updated: 2022-10-17
lang: en
---
An Azure deployment conflict error is the platform telling you that the change you just submitted cannot proceed because something else already owns the resource you are touching. The wording varies. You might see a bare `409 Conflict` returned from the Azure Resource Manager API, a deployment that fails with the message that another operation is in progress, a write that is rejected because a lock forbids it, or a create that fails because the name is already taken or the resource sits in a transitioning state. Whatever the surface text, the underlying meaning is consistent: the control plane has decided that your operation and the current state of the resource cannot both be true at the same moment, so it refuses yours rather than corrupting the resource.

![Diagnosing Azure deployment conflict errors and the 409 control-plane race - Insight Crunch](/assets/images/blog/blog-84.webp)

That single meaning is the most useful thing to carry into the diagnosis, because it reframes the whole problem. A conflict is not a transient network blip and it is not usually a bug in your template. It is a statement about ownership and timing. Some other operation, some lock, or some property of the existing resource is incompatible with what you asked for right now. The engineer who internalizes that stops doing the thing almost everyone does first, which is to rerun the deployment immediately and hope. Rerunning collides with the very same in-progress operation or the very same lock that produced the first rejection, and the second attempt fails for the identical reason. The work of fixing a conflict is the work of finding out who or what currently owns the resource, and then either waiting for that owner to finish, removing the thing that blocks you, or serializing your own operations so they stop racing each other.

This guide treats the deployment conflict as a diagnosis problem rather than a syntax problem. We will read the error the way the platform means it, gather the diagnostic signal from the activity log and the resource provisioning state, separate the four distinct root causes that produce a conflict, show the confirming check and the tested fix for each, and then build the prevention that stops the conflict from coming back. By the end you should be able to look at any conflict, name which of the four causes is yours, prove it with a command, and resolve it without retrying into the same race.

## What an Azure Deployment Conflict Error Actually Means

Azure Resource Manager, the control plane that sits in front of every resource you deploy, processes operations as a sequence of state transitions on each resource. When you submit a deployment, ARM does not simply write your desired state into a database and move on. It takes the resource through a lifecycle: it validates the request, accepts it, marks the resource as updating, asks the relevant resource provider to perform the work, and finally records the resource as succeeded or failed. While a resource is mid-transition, the provider holds a logical claim on it. A second operation that arrives during that window cannot be allowed to interleave, because two providers writing to the same resource state would produce undefined results. ARM resolves this by rejecting the later operation with a conflict.

The HTTP status code that carries this rejection is `409 Conflict`. In the REST semantics that ARM follows, a 409 means the request could not be completed because of a conflict with the current state of the target resource. That definition is worth reading slowly, because it names both halves of the problem. There is a request, which is what you asked for, and there is the current state of the target resource, which is what the resource is doing or being right now. A conflict exists when those two cannot be reconciled. The current state might be that another operation is in progress, that a lock forbids the change, that the resource is still provisioning, or that a resource with that identity already exists. Each of those is a different current state, and each produces a conflict for a different reason, which is exactly why a single retry rarely helps: you have not changed the current state that caused the rejection.

The conflict surfaces in several places depending on how you deploy. If you use the Azure CLI, you will usually see the error text printed at the end of `az deployment group create`, often with a top-level code such as `DeploymentFailed` wrapping a nested code that names the real cause. If you use a pipeline, the conflict appears in the task log and fails the stage. If you call the REST API directly, you receive the 409 status and a JSON body with an `error` object. The portal shows the failed deployment in the resource group's Deployments blade, and clicking into the operation reveals the same nested error. The presentation differs but the payload is the same, and learning to read that payload is the first real skill in resolving a conflict.

### What does "Another operation is in progress" mean?

It means a second operation is already running against the same resource and holds it, so the control plane refuses your operation rather than letting two writers interleave. The fix is to find that operation in the activity log, let it finish, and then run yours, instead of retrying into the live race.

The phrase reads like a vague status update, but it is precise. The resource provider has accepted an earlier request, that request has not yet reached a terminal state of succeeded or failed, and the provider therefore considers the resource busy. Your request arrives, the provider checks the resource, finds it occupied, and returns the conflict. The earlier operation might be a deployment you triggered yourself a moment ago from a second shell, a pipeline run that started in parallel, an autoscale or platform action, or a long-running provisioning step on a resource that simply takes minutes to settle. The single most common version of this in real teams is two pipeline runs deploying the same resource group at the same time, where each run trips over the other and both fail with the in-progress message.

## How to Read the Conflict and Gather the Diagnostic Signal

Before you change anything, you gather signal. A conflict that you fix by guessing is a conflict you will see again, because the guess does not tell you which of the four causes was real. The signal lives in three places: the error payload itself, the activity log, and the resource's own provisioning state. Reading all three takes a few minutes and turns a vague failure into a named cause.

Start with the error payload, because it often names the cause outright. ARM errors nest. The outermost code is frequently generic, something like `DeploymentFailed`, and the actionable detail sits inside it. When you run a deployment from the CLI, add output that exposes the structure so you are not reading a truncated single line:

```bash
az deployment group create \
  --resource-group rg-payments-prod \
  --template-file main.bicep \
  --parameters @prod.parameters.json \
  --name deploy-payments-$(date +%s) \
  --verbose
```

If the deployment fails, pull the full error from the deployment record rather than relying on the console tail, which often clips the nested message:

```bash
az deployment operation group list \
  --resource-group rg-payments-prod \
  --name deploy-payments-1666000000 \
  --query "[?properties.provisioningState=='Failed'].properties.statusMessage" \
  --output json
```

That query returns the status message for every failed operation in the deployment, and the conflict message you are chasing is almost always in there with its real code. The codes you are looking for are the ones that distinguish the four causes. A code or message mentioning that an operation is in progress points at concurrency. A code such as `ScopeLocked` or a message that the scope is locked points at a resource lock. A message that the resource is in a transitioning or updating state points at provisioning timing. A code such as `Conflict` paired with text about a resource already existing or a property already in use points at a collision.

### Where do I find the operation that is blocking my deployment?

You find it in the Azure activity log, which records every control-plane operation against the resource with a timestamp, a caller, and a status. Filter the log to the resource and the time window around your failure, look for an operation that started before yours and has not reached a terminal status, and that is the operation holding the resource.

The activity log is the authoritative record of what the control plane did and is doing, and it is where you confirm the in-progress case rather than assuming it. Query it for the resource group around the moment of the failure:

```bash
az monitor activity-log list \
  --resource-group rg-payments-prod \
  --start-time 2022-10-17T09:00:00Z \
  --end-time 2022-10-17T09:30:00Z \
  --query "[].{op:operationName.value, status:status.value, caller:caller, time:eventTimestamp, resource:resourceId}" \
  --output table
```

Reading the result, you are looking for the operation that competes with yours. If you see a write operation on the same resource, started by a different caller or a different pipeline service principal, with a status of Started or Accepted but no matching Succeeded or Failed near your failure time, you have found the operation that owns the resource. The caller field tells you who launched it, which is often the moment the cause becomes obvious: a second engineer running a deployment, a parallel pipeline stage, or an automation account. If instead the competing entry is a Microsoft platform operation, the resource may be under a managed action such as a maintenance or scaling event, and the right move is to wait and retry once it clears.

The third source of signal is the resource's own provisioning state. Every ARM resource carries a `provisioningState` property that reflects where it sits in its lifecycle. A resource that reads Succeeded is settled and ready for the next operation. A resource that reads Updating, Creating, Deleting, or any non-terminal value is mid-transition and will reject a competing write. Read it directly:

```bash
az resource show \
  --resource-group rg-payments-prod \
  --name payments-api \
  --resource-type Microsoft.Web/sites \
  --query "properties.provisioningState" \
  --output tsv
```

If that returns something other than Succeeded, the resource is busy, and the conflict you saw was the platform protecting an in-flight change. The provisioning state, the activity log, and the nested error message together pin the cause. With those three readings in hand, you can stop guessing and route the conflict to one of the four root causes below.

## The Distinct Root Causes Behind a Deployment Conflict

Every deployment conflict reduces to one of four causes, and the entire diagnosis is the work of deciding which one you are looking at. The first is concurrency: two operations touch the same resource at the same time, and the second is rejected. The second is a lock: a management lock on the resource, the resource group, or the subscription forbids the write or the delete you attempted. The third is provisioning timing: the resource is still mid-transition from an earlier operation and is not ready for the next one. The fourth is a collision: a resource with the same name or a property that must be unique already exists, so the create cannot complete.

These four are genuinely distinct, they have different confirming signals, and they have different fixes. Conflating them is the source of most wasted time, because a fix for one does nothing for another. Serializing your pipeline solves concurrency and does nothing for a lock. Removing a lock solves the lock case and does nothing for a provisioning-state race. Renaming a resource solves a collision and does nothing for two parallel runs. The table below is the findable reference for this article, the InsightCrunch deployment-conflict cause table, mapping each cause to the signal that confirms it and the fix that resolves it. Keep it open while you work through the diagnosis.

| Root cause | What you see | Confirming signal | The fix |
|---|---|---|---|
| Concurrent operations | "Another operation is in progress" or a 409 on a resource a second run also targets | Activity log shows a second write on the same resource, different caller or pipeline, no terminal status near your failure | Serialize the operations: pipeline concurrency control, Terraform state locking, or sequencing the writes so one finishes before the next starts |
| Resource lock | `ScopeLocked`, "the scope is locked", or a delete or write rejected with a lock reference | `az lock list` shows a `CanNotDelete` or `ReadOnly` lock at the resource, group, or subscription scope | Remove or scope down the lock for the operation, perform the change, then restore the lock, or grant the deploy identity the right to manage locks where policy allows |
| In-progress provisioning state | A 409 on a resource you just created or modified | `provisioningState` reads Updating, Creating, or Deleting rather than Succeeded | Wait for the resource to reach a terminal state, add an explicit dependency so the next step waits, then retry |
| Name or property collision | `Conflict` with "already exists", a globally unique name taken, or a delete and create racing on one name | The resource exists already, or a soft-deleted resource holds the name, or two operations target the same name | Choose a unique name, wait for a soft-deleted resource to purge or recover it, or sequence the delete before the create |

## Cause One: Concurrent Operations on the Same Resource

The concurrency case is the most common deployment conflict in any team that has more than one person or more than one pipeline, and it is the case the in-progress message describes directly. Two operations target the same resource within the same window. ARM accepts the first, marks the resource busy, and rejects the second with a conflict. Neither operation is wrong on its own. The problem is purely one of timing and serialization, and the fix lives at the level of how operations are scheduled rather than in any template.

### Do two concurrent deployments cause a conflict?

Yes, when both deployments write to the same resource. ARM lets one operation hold a resource at a time, so the second deployment that reaches a busy resource is rejected with a conflict. Deployments that touch entirely separate resources can run in parallel safely; the conflict only appears where the write targets overlap.

The reason this matters is that parallelism is usually a feature you want, not a bug you must eliminate. A deployment that creates twelve unrelated resources benefits enormously from ARM running those creations in parallel, and most of the time it does exactly that without any conflict, because the resources do not contend. The conflict appears specifically where two operations write to one resource, or to resources that share an underlying object. Two pipeline runs that both deploy the same App Service contend on that site. Two modules that both update the same network security group contend on that group. A deployment that updates a virtual network while a second deployment updates a subnet within it contends, because the subnet write is, at the provider level, a write to the parent network.

Confirming the concurrency cause is the activity-log reading described above. You are looking for two write operations on the same resource, overlapping in time, ideally with different callers so you can see who launched the competitor. In a pipeline context the competitor is frequently the same pipeline running twice: a developer pushed two commits in quick succession, each triggered a run, and both runs reached the deploy stage at the same time. The service principal is identical in that case, which can briefly fool you into thinking there is only one operation, so lean on the timestamps and the operation identifiers rather than the caller alone.

The fix is serialization, and the right mechanism depends on what is launching the operations. When the source is a CI/CD pipeline, the cleanest answer is to make the pipeline refuse to run a second deployment to the same environment while one is already running. Azure Pipelines expresses this through environment and deployment-job semantics, and through explicit concurrency control on the stage. In a YAML pipeline you constrain concurrency at the job level so a new run waits for the prior one rather than racing it:

```yaml
jobs:
  - deployment: DeployPayments
    environment: production
    strategy:
      runOnce:
        deploy:
          steps:
            - task: AzureCLI@2
              inputs:
                azureSubscription: 'payments-prod-connection'
                scriptType: bash
                scriptLocation: inlineScript
                inlineScript: |
                  az deployment group create \
                    --resource-group rg-payments-prod \
                    --template-file main.bicep \
                    --parameters @prod.parameters.json \
                    --name deploy-$(Build.BuildId)
```

Binding the deploy job to a named environment gives the platform a serialization point, and many teams add an approval or an exclusive-lock check on that environment so that only one run can deploy to production at a time. GitHub Actions expresses the same idea through a concurrency group, which cancels or queues a second run that shares the group key:

```yaml
concurrency:
  group: deploy-payments-prod
  cancel-in-progress: false
```

Setting `cancel-in-progress` to false queues the second run behind the first rather than cancelling it, which is usually what you want for a deployment, because cancelling mid-deploy can leave a resource half-updated. With the queue in place, the two runs that used to collide now proceed one after the other, and the conflict disappears because there is never a second operation racing the first.

When the source is Terraform rather than ARM or Bicep, the serialization mechanism is state locking. Terraform takes a lock on its state backend at the start of an apply and releases it at the end, which prevents two applies from running against the same state at once. If your backend is an Azure Storage account, that locking is provided by the blob lease on the state file. A conflict in this context often means the lock is configured incorrectly, or a previous apply crashed and left the lease held. You inspect and, where you are certain no apply is running, force-unlock it:

```bash
terraform force-unlock 1a2b3c4d-5e6f-7890-abcd-ef1234567890
```

Use force-unlock only when you have confirmed no apply is genuinely in progress, because clearing a live lock reintroduces the very race you are trying to prevent. The disciplined pattern is to let the state lock do its job, route all applies through a single pipeline, and treat a stuck lock as the rare exception rather than the routine clearing step.

When the source is neither a pipeline nor Terraform but two humans, the fix is process: a single deployment path that everyone uses, so that ad hoc portal edits and local CLI runs do not race the pipeline. The control-plane model that makes all of this coherent is worth understanding in depth, and the way Azure Resource Manager sequences and serializes operations is covered in the dedicated treatment of [how Azure Resource Manager processes and orders deployments](/2022/05/16/azure-resource-manager-arm-explained/), which explains why ARM holds a resource during a transition and how parallel resource creation is scheduled underneath a single deployment.

## Cause Two: A Resource Lock Blocking the Write or Delete

A management lock is a deliberate guardrail that prevents resources from being changed or deleted, and it is the second cause of a deployment conflict. Locks exist precisely to make certain operations fail, so when a lock is the cause, the conflict is the system working as intended, even if the failure is inconvenient at that moment. The skill here is recognizing the lock signal quickly, deciding whether the lock should yield to your operation or your operation should yield to the lock, and handling the change without leaving the resource unprotected afterward.

### Can a resource lock cause a deployment conflict?

Yes. A `CanNotDelete` lock blocks any delete and a `ReadOnly` lock blocks both writes and deletes, so a deployment that modifies or removes a locked resource is rejected. The conflict references the locked scope. Listing the locks on the resource, its group, and the subscription tells you which lock applied and at which level it sits.

Azure offers two lock levels, and they behave differently. A `CanNotDelete` lock allows reads and writes but forbids deletion, which protects against accidental removal while still permitting configuration changes. A `ReadOnly` lock is stricter: it forbids any operation that the platform classifies as a write, which includes both modification and deletion, leaving only read operations permitted. The practical surprise with `ReadOnly` is how many operations count as writes under the covers. Adding a record to a resource, listing keys on some resource types, or any action that the provider implements as a POST or PUT can be blocked, which means a `ReadOnly` lock sometimes rejects operations an engineer thinks of as harmless reads. When a deployment hits a lock, the conflict text references the lock and the scope it sits at, and that scope matters because locks inherit downward.

Locks apply at three scopes, and a lock at a higher scope cascades to everything beneath it. A lock placed on a subscription applies to every resource group and every resource in that subscription. A lock on a resource group applies to every resource in the group. A lock on a single resource applies only to that resource. The cascading is the part that catches people, because a deployment that targets one resource can be blocked by a lock that was placed on the resource group for an entirely unrelated reason, and the engineer looking only at the resource finds no lock there. Confirming the lock cause therefore means listing locks at every applicable scope, not just the resource:

```bash
az lock list \
  --resource-group rg-payments-prod \
  --query "[].{name:name, level:level, notes:notes, scope:id}" \
  --output table
```

To catch a subscription-level lock that cascades into the group, widen the query to the subscription scope as well:

```bash
az lock list \
  --query "[?level=='ReadOnly' || level=='CanNotDelete'].{name:name, level:level, scope:id}" \
  --output table
```

Reading the output, the level field tells you whether the lock blocks deletes alone or all writes, the scope tells you where the lock sits and therefore how widely it cascades, and the notes field, if whoever created the lock filled it in, often tells you why the lock exists and who to ask before touching it. That last detail is more important than it looks. A lock with a note that reads as a compliance requirement or a production safeguard is not a lock you quietly remove to push a deployment through. The note is a signal that the conflict is protecting something, and the correct response may be to route the change through whatever process the lock was meant to enforce rather than to delete the guardrail.

When the lock genuinely should yield to your operation, the disciplined pattern is to remove or downgrade the lock for the duration of the change and restore it immediately afterward, so the resource spends the minimum possible time unprotected. You capture the lock definition, delete it, run the deployment, and recreate it:

```bash
# Capture the lock so it can be restored exactly
az lock show \
  --name lock-payments-prod \
  --resource-group rg-payments-prod \
  --output json > /tmp/lock-backup.json

# Remove the lock for the operation
az lock delete \
  --name lock-payments-prod \
  --resource-group rg-payments-prod

# Run the deployment that the lock was blocking
az deployment group create \
  --resource-group rg-payments-prod \
  --template-file main.bicep \
  --parameters @prod.parameters.json \
  --name deploy-after-lock-clear

# Restore the lock immediately
az lock create \
  --name lock-payments-prod \
  --resource-group rg-payments-prod \
  --lock-type CanNotDelete \
  --notes "Production safeguard, restored after deploy"
```

Doing this by hand is acceptable for a one-off incident, but baking it into a pipeline is risky, because a failed deployment can leave the lock deleted and never restored if the restore step does not run on failure. If you must automate it, put the lock restoration in a step that always runs regardless of the deployment outcome, so a failed deploy never leaves production unguarded. The cleaner long-term answer is to give the deployment identity the explicit right to manage locks where your governance policy permits, so the deployment can downgrade and restore the lock as part of its own run under a controlled identity, and to keep `ReadOnly` locks off resources that legitimate deployments need to modify regularly. The permission a deployment needs to manage locks is itself an authorization concern, and when a deployment fails not because of a lock but because the identity lacks a role, you are looking at a different error entirely, which is the authorization failure diagnosed in the guide to [resolving Azure RBAC AuthorizationFailed errors during deployment](/2022/10/10/fix-azure-rbac-authorizationfailed/).

## Cause Three: A Resource Still in a Transitioning Provisioning State

The third cause is timing against a resource that has not finished an earlier operation. Unlike the concurrency case, where two distinct operations race, the provisioning-state case often involves a single logical sequence where the second step starts before the first step truly settled. The resource is still Creating, Updating, or Deleting, and a new write arrives while it is mid-transition, so the platform rejects the write to protect the in-flight change. This is the conflict that appears most often right after a successful-looking create, because the API call returned before the resource fully provisioned.

The subtlety is that many ARM operations are asynchronous. When you create or modify a resource, the control plane frequently accepts the request and returns quickly while the provider continues working in the background. The CLI or the SDK may report success at the point of acceptance, not at the point of completion, depending on how the call is made. An automation script that fires a create and immediately fires a follow-up modification can therefore hit a resource that, from the script's point of view, already exists and succeeded, but from the provider's point of view is still settling. The follow-up write lands during the transition and is rejected with a conflict. The resource is not locked and there is no second operator; the script is simply racing itself by not waiting for the first operation to reach a terminal state.

Confirming this cause is the provisioning-state reading shown earlier. You query the resource directly and check whether it reads Succeeded or some non-terminal value:

```bash
az resource show \
  --resource-group rg-payments-prod \
  --name payments-api \
  --resource-type Microsoft.Web/sites \
  --query "properties.provisioningState" \
  --output tsv
```

If the answer is Updating or Creating at the moment your follow-up operation failed, the provisioning race is confirmed. You can also watch the state settle rather than polling by hand, which is useful when you are trying to understand how long a given resource takes to finish:

```bash
az resource wait \
  --resource-group rg-payments-prod \
  --name payments-api \
  --resource-type Microsoft.Web/sites \
  --custom "properties.provisioningState=='Succeeded'" \
  --timeout 600
```

That command blocks until the resource reaches Succeeded or the timeout elapses, which is exactly the behavior a script needs before it proceeds to the next dependent operation. The fix for the provisioning-state conflict is to make the waiting explicit rather than implicit. Inside a single ARM or Bicep deployment, you express the wait declaratively through dependencies. When resource B must not be written until resource A has finished, you declare that B depends on A, and ARM will not begin B until A reaches a terminal state. In Bicep, a dependency is usually inferred automatically when one resource references another's properties, but you can also state it explicitly:

```bicep
resource plan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: 'plan-payments'
  location: location
  sku: {
    name: 'P1v3'
  }
}

resource site 'Microsoft.Web/sites@2022-03-01' = {
  name: 'payments-api'
  location: location
  properties: {
    serverFarmId: plan.id
  }
  dependsOn: [
    plan
  ]
}
```

Because the site references `plan.id`, Bicep already infers the dependency and would serialize the two even without the explicit `dependsOn`, but stating it makes the intent unambiguous and protects against a refactor that removes the reference. The dependency model is how a single deployment avoids racing itself: ARM walks the dependency graph and only starts a resource once everything it depends on has settled. When your conflict comes from a script that stitches together several separate deployments or CLI calls, the equivalent is the explicit `az resource wait` between steps, so each operation confirms the previous resource reached Succeeded before it writes.

The provisioning-state conflict also appears around deletes. A delete is a transition like any other, and a resource that is mid-delete will reject a create that reuses its name, because the resource still exists in a Deleting state. That overlap between a delete and a create is where the third cause and the fourth cause meet, and it is the bridge into the collision case below.

## Cause Four: A Name or Property Collision

The fourth cause is identity. A deployment that creates a resource fails with a conflict because something with that identity already exists, or because a property that must be unique within a scope is already taken. This is a different shape of conflict from the first three, because it is not about timing or ownership at all. It is about the namespace. Two things cannot occupy the same name, and ARM enforces that by rejecting the second create.

The collision comes in several flavors, and telling them apart sharpens the fix. The simplest is a plain name clash within a resource group: you try to create a resource with a name that an existing resource already holds, and the create is rejected. The more frustrating flavor involves globally unique names. Several Azure resource types require names that are unique not within your subscription but across all of Azure, because the name becomes part of a public DNS label. A storage account name becomes part of `blob.core.windows.net`, an App Service name becomes part of `azurewebsites.net`, a Key Vault name becomes part of `vault.azure.net`, and a Cosmos DB account name becomes part of its public endpoint. When you try to create one of these with a name that someone else, possibly in an entirely different organization, already registered, you receive a conflict that has nothing to do with your own resources. The name is simply gone from the global namespace.

A third flavor is the soft-delete collision, which is the one that surprises engineers most. Some resource types, most notably Key Vault, support soft delete, where a deleted resource is not immediately purged but retained for a recovery window. During that window, the name remains reserved. An engineer who deletes a Key Vault and immediately tries to recreate it with the same name receives a conflict, because the soft-deleted vault still holds the name and must either be recovered or purged before the name frees up. The same pattern applies to other soft-delete-capable types, and the conflict text usually hints at it by referencing a deleted resource or a name in a deleted state.

Confirming the collision cause is direct. For a name clash within your own subscription, you check whether the resource already exists:

```bash
az resource list \
  --resource-group rg-payments-prod \
  --name payments-api \
  --output table
```

For a globally unique name, you check availability through the provider's name-availability operation. Storage accounts expose this directly:

```bash
az storage account check-name \
  --name paymentsprodstore \
  --query "{available:nameAvailable, reason:reason, message:message}" \
  --output json
```

If `available` is false and the reason indicates the name is already taken, the global namespace is the cause and you need a different name. If the reason indicates the name is invalid rather than taken, the conflict is actually a validation problem in disguise, and you adjust the name to fit the rules for that resource type. For the soft-delete flavor, you list the soft-deleted resources of that type and decide whether to recover or purge:

```bash
az keyvault list-deleted \
  --query "[].{name:name, scheduledPurgeDate:properties.scheduledPurgeDate, location:properties.location}" \
  --output table
```

If your intended name appears in that list, the previous resource is holding it. You either recover the soft-deleted vault if you actually want it back, or purge it if you genuinely want a fresh resource with that name, accepting that purging is irreversible and discards the retained contents.

The fix for a collision depends on which flavor you confirmed. For a plain clash, you choose a unique name, ideally through a naming convention that makes clashes structurally impossible, such as embedding the environment, the workload, and a short unique suffix so that two deployments never generate the same name by accident. Bicep can generate a deterministic unique suffix from the resource group identity, which keeps globally unique names both unique and reproducible across redeployments of the same environment:

```bicep
param workload string = 'payments'
var uniqueSuffix = uniqueString(resourceGroup().id)
var storageName = take('st${workload}${uniqueSuffix}', 24)

resource store 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
}
```

The `uniqueString` function returns a deterministic hash from the inputs you give it, so the same resource group always produces the same suffix, which means redeploying the template targets the existing storage account rather than trying to create a new one and colliding. The `take` wrapper enforces the 24-character limit that storage account names carry. For a globally unique collision against a name held outside your control, there is no fix except a different name, and the deterministic-suffix pattern is the durable way to avoid the problem entirely. For the soft-delete collision, the fix is to recover or purge the retained resource before recreating, and the prevention is to enable purge protection thoughtfully and to script the recover-or-purge decision into your teardown process rather than discovering it mid-deploy.

The delete-create race deserves a specific note, because it sits at the boundary between this cause and the provisioning-state cause. When a pipeline tears down a resource and recreates it under the same name in quick succession, the create can land before the delete finishes, and the still-deleting resource holds the name. The conflict reads like a collision but is really a sequencing failure. The fix is to wait for the delete to complete before starting the create, using the same `az resource wait` pattern shown for the provisioning case, watching for the resource to disappear rather than for it to reach Succeeded.

## Serializing Deployments: The Core Fix

Three of the four causes share a single underlying remedy, which is serialization, and it is worth treating that remedy as a first-class practice rather than a per-incident patch. The concurrency cause is solved by serializing two operations that race. The provisioning-state cause is solved by serializing a follow-up against the operation it depends on. The delete-create race is solved by serializing the create behind the delete. The lock cause is the odd one out, because it is about authorization to change rather than timing, but even there the safe lock-and-restore pattern is a kind of serialization, ensuring the unprotect, the change, and the reprotect happen in a controlled order. Serialization, in other words, is the through-line of conflict resolution, and the namable principle this article advances is the serialize-not-retry rule: a conflict means another operation owns the resource right now, so the fix is to serialize or wait, never to retry blindly into the same race.

### How do I serialize deployments to avoid conflicts?

You give every deployment to a given target a single ordered path. Use pipeline concurrency control or a named environment so only one run deploys at a time, use Terraform state locking so only one apply touches state at once, and use ARM dependencies so dependent resources wait for the resources they need. Each mechanism removes a race rather than retrying through it.

The pipeline-level controls shown earlier are the front line. A concurrency group in GitHub Actions or a deployment job bound to a named environment in Azure Pipelines ensures that two runs targeting the same environment queue rather than race. The most robust version of this pairs the concurrency control with the principle that there is exactly one path to each environment. When the only way a resource changes is through the pipeline, and the pipeline serializes itself, the concurrency conflict cannot occur, because there is never a second uncontrolled writer. Teams that still see conflicts after adding concurrency control almost always have a second path: a portal edit, a local CLI run, or a separate automation account that bypasses the queue. Closing those side doors is as important as configuring the queue.

Within a deployment, serialization is the dependency graph, and the discipline is to let ARM infer dependencies from references wherever possible and to add explicit `dependsOn` only where the reference does not exist but the ordering still matters. Over-declaring dependencies has a cost, because it forces ARM to serialize resources that could safely run in parallel, which slows the deployment. Under-declaring them has the opposite cost, the provisioning-state conflict. The right balance is to depend on exactly what you must and no more, and to verify the resulting order with a what-if run before deploying, which previews the operations ARM intends to perform and surfaces ordering problems before they become conflicts:

```bash
az deployment group what-if \
  --resource-group rg-payments-prod \
  --template-file main.bicep \
  --parameters @prod.parameters.json
```

The what-if output shows you each resource ARM will create, modify, or delete, and reviewing it is the cheapest way to catch a deployment that is about to race itself or collide with an existing resource. For teams managing complex resource lifecycles where the create, update, and delete ordering across many resources is itself the hard part, Azure offers deployment stacks as a managed construct that tracks a set of resources as a unit and handles their lifecycle coherently, which removes a class of ordering and cleanup races that hand-managed deployments are prone to, and the way deployment stacks manage a grouped resource lifecycle is covered in the dedicated guide to [managing resource lifecycles with Azure deployment stacks](/2025/03/10/azure-deployment-stacks/).

## Preventing Deployment Conflicts from Recurring

A conflict you fixed once will return unless you address the structural cause, and the structural causes are few. The first is uncontrolled concurrency, which you prevent by ensuring a single ordered deployment path to each environment and by configuring the pipeline to queue rather than race. The second is locks that sit on resources legitimate deployments must change, which you prevent by placing locks at the right scope and level, keeping `ReadOnly` locks off resources that need regular modification, and giving the deployment identity a controlled way to manage locks where governance allows. The third is implicit ordering, which you prevent by making dependencies explicit in your templates and by waiting for terminal provisioning states between separate operations. The fourth is naming, which you prevent by adopting a deterministic naming convention that makes both local and global collisions structurally unlikely.

Beyond those four specific preventions, two habits reduce conflicts across the board. The first is idempotent deployments. A deployment you can run repeatedly without changing the outcome after the first successful run is a deployment that does not collide with its own prior state, because rerunning it targets the existing resources rather than trying to recreate them. ARM and Bicep are declarative and idempotent by design, so a well-written template that references resources by stable names and uses deterministic unique suffixes will converge on the same state every time. Scripts that imperatively create resources without checking whether they already exist break that idempotency and reintroduce collisions, so the move from imperative create scripts to declarative templates is itself a conflict-prevention measure.

The second habit is observability of the control plane. A team that routinely watches the activity log and alerts on failed deployments catches a conflict pattern early, before it becomes a recurring fire. Setting up an alert on deployment failures in a resource group, and reviewing the activity log when one fires, turns the conflict from a surprise into a signal. The activity log retains control-plane events for a window, and exporting those events to a Log Analytics workspace lets you query conflict patterns over time, such as how often two pipeline runs collide on the same environment, which tells you whether your concurrency control is actually holding.

A short post-incident habit closes the loop on prevention. When a conflict does occur, spend the few minutes after the fix recording which of the four causes it was, what signal confirmed it, and what change would have prevented it, then feed that change back into the delivery system. A conflict that was a pipeline race becomes a missing concurrency group you add; a conflict that was a cascading lock becomes a lock placed at too broad a scope that you narrow; a conflict that was a self-racing script becomes a missing wait step you insert. Treating each conflict as a small lesson about a gap in serialization, rather than as a one-off annoyance, is how a team moves from recovering from conflicts to not having them, and the cumulative effect over a quarter is a delivery path where the four causes simply stop finding purchase.

There is one prevention that is really an anti-prevention, and it is worth naming so you do not adopt it: the retry loop. The instinct to wrap a deployment in a loop that retries on failure feels like resilience, and for genuinely transient errors it can be. A conflict is usually not transient in the relevant sense. A retry that fires immediately collides with the same in-progress operation or the same lock and fails identically, and a retry loop that hammers the control plane can extend the window of contention rather than shortening it. If you retry at all, retry with a backoff long enough for the competing operation to reach a terminal state, and only after you have confirmed that the conflict was a timing race rather than a lock or a collision, because no amount of retrying clears a lock or frees a taken name. The disciplined posture is to diagnose first and serialize the cause, and to treat a bare retry loop as the thing you reach for only when you have proven the conflict is a brief provisioning race and nothing more.

## A Worked Diagnosis: From 409 to Root Cause in One Pass

The fastest way to make the four-cause model concrete is to walk a single failure from the raw error to a named cause and a fix, the way you would at a desk mid-incident. Picture a common situation. A team runs a release pipeline that deploys a payments API to production. A developer merges two pull requests within a minute of each other, each merge triggers a pipeline run, and both runs reach the deploy stage at nearly the same time. The first run completes. The second fails with a message that another operation is in progress on the App Service. The engineer on call sees a red pipeline and a 409 buried in the task log, and the clock is running.

The wrong first move, the one almost everyone makes, is to click rerun. That rerun queues nothing, races the lingering operation, and either fails again or, worse, succeeds intermittently and teaches the team that conflicts are flaky rather than that they are races. The disciplined first move is to read, not retry. Pull the failed operation's full status message rather than trusting the clipped console line:

```bash
az deployment operation group list \
  --resource-group rg-payments-prod \
  --name deploy-payments-build-4412 \
  --query "[?properties.provisioningState=='Failed'].{target:properties.targetResource.id, message:properties.statusMessage}" \
  --output json
```

The message names the App Service site and states that an operation is already running against it. That single reading rules out the lock cause and the collision cause immediately, because the platform is not complaining about a lock or an existing name; it is complaining about an operation in flight. Two candidates remain: a genuine second operation racing yours, or the same logical operation that has not yet settled. The activity log discriminates between them:

```bash
az monitor activity-log list \
  --resource-group rg-payments-prod \
  --start-time 2022-10-17T14:20:00Z \
  --end-time 2022-10-17T14:35:00Z \
  --query "[?contains(resourceId, 'payments-api')].{op:operationName.localizedValue, status:status.value, caller:caller, time:eventTimestamp}" \
  --output table
```

The log shows two write operations on the same site, started forty seconds apart, both initiated by the pipeline's service connection identity. The first reached a succeeded status; the second, the one the engineer is staring at, was rejected. There is the proof: two runs of the same pipeline contended on one site, which is the concurrency cause. The provisioning state confirms the site itself is now settled:

```bash
az resource show \
  --resource-group rg-payments-prod \
  --name payments-api \
  --resource-type Microsoft.Web/sites \
  --query "properties.provisioningState" \
  --output tsv
```

It reads Succeeded, which means the resource is no longer busy and a single deploy now would work. The immediate unblock is therefore to run the deployment once more, deliberately and alone, knowing the competitor has finished. That is not a blind retry; it is a retry that follows a confirmed reading that the race is over. The durable fix is the one that prevents the next pair of merges from doing the same thing, which is the concurrency control covered earlier: bind the deploy job to a named environment and add a concurrency group so a second run queues behind the first instead of racing it.

### How do I know a retry is safe rather than blind?

A retry is safe when you have confirmed the competing operation reached a terminal state and the target now reads a settled provisioning state. A blind retry fires without that confirmation and collides with the same in-flight work. The difference is one activity-log reading and one provisioning-state check, which together take under a minute.

This single pass, reading the operation message, the activity log, and the provisioning state, is the whole diagnosis loop, and it generalizes to every conflict. The message narrows the candidates, the activity log distinguishes a real competitor from a self-race, and the provisioning state tells you whether the contended object is now free. An engineer who runs that loop reflexively spends a minute confirming the cause and resolves the conflict once, while an engineer who reruns on instinct can lose an afternoon to a race that never resolves because each attempt recreates it.

## Where Conflicts Concentrate: High-Contention Objects

Conflicts are not evenly distributed across Azure. They cluster on a handful of resource shapes where many operations naturally converge on one underlying object, and knowing those shapes lets you anticipate a conflict before it happens and design around it. The unifying idea is contention on a shared parent or a shared dependency: wherever several operations must write through one object, that object becomes a serialization point, and operations that arrive together collide there.

The clearest example is the parent-child relationship in networking. A virtual network and its subnets look like separate things, but at the provider level a subnet write is a write to the parent network. When two deployments each add or modify a subnet in the same virtual network at the same time, they both write the parent, and one is rejected with a conflict even though the subnets themselves are different. The same pattern holds for a route table referenced by many subnets, and for a network security group attached to several network interfaces. The fix is not to stop using shared networking objects, which would be impractical, but to serialize the writes that touch them, either by routing all network changes through one deployment or by sequencing the modules that touch the shared parent so they do not run in parallel.

### Why do two subnet deployments conflict when the subnets are different?

Because a subnet is a child of its virtual network, and writing a subnet is, at the provider level, a write to the parent network. Two parallel subnet operations both write that single parent, so the platform serializes them and rejects the second. Sequencing the subnet writes, or routing them through one deployment, removes the contention.

App Service shows a different flavor of the same theme. An App Service plan hosts many sites, and operations that change the plan, such as scaling it, contend with operations on the sites it hosts, because the platform must coordinate the change across the plan. Two deployments that both touch the plan, or a plan scale running alongside a site update, can conflict. The practical guidance is to treat the plan as a shared object that wants serialized changes and to avoid scaling a plan in the same window that you deploy sites onto it. Within a single site, the most common contention is two pipeline runs deploying the same site, the scenario walked through above, and the answer there is pipeline concurrency control.

Managed Kubernetes clusters concentrate conflicts on the cluster object and its node pools. An operation that updates the cluster, such as a version upgrade, and an operation that scales or modifies a node pool both write through the cluster's control-plane object, so firing them together produces a conflict. Cluster operations are also long-running, which compounds the timing problem, because an upgrade can hold the cluster for many minutes, and any node pool change submitted during that window is rejected. The discipline is to let one cluster operation finish before starting another, confirmed by reading the cluster's provisioning state, rather than queuing several cluster changes optimistically and hoping they interleave.

Storage accounts present a subtler case that blends two causes. The account itself is a control-plane object, and operations that reconfigure it, such as changing network rules or rotating settings, serialize through the account. At the same time, the account name lives in the global namespace, so a create can collide on the name. An engineer reconfiguring an account while a pipeline also touches it sees the concurrency flavor, while an engineer recreating a recently deleted account sees the collision flavor. Separating the two requires reading the message: an in-progress note points at concurrency on the account object, while an already-exists note points at the name.

The general lesson is to map your deployment to its shared objects before you run it. Ask which underlying parent or dependency each operation writes through, and wherever two operations write through the same one, expect contention and serialize deliberately. This is where the what-if preview earns its place, because it lists the operations ARM intends to perform and lets you spot two writes converging on one object before they collide in production.

## Validating Before You Deploy: What-If, Validate, and Deployment Mode

The cheapest conflict is the one a pre-flight check catches before the deployment runs, and ARM offers two pre-flight tools plus a mode setting that, used well, prevent a meaningful share of conflicts. The first tool is validate, which submits the template for the platform to check without performing the deployment. Validation catches structural problems and many provider-level objections early, and while it does not catch every timing race, it catches the malformed requests that would otherwise fail mid-run and leave a partial deployment that is harder to reason about:

```bash
az deployment group validate \
  --resource-group rg-payments-prod \
  --template-file main.bicep \
  --parameters @prod.parameters.json
```

The second and more powerful tool is what-if, which previews the exact set of changes ARM intends to make: the resources it will create, the ones it will modify and how, and crucially the ones it will delete. Reading the what-if output before a production deploy is the single most effective habit for catching a deployment that is about to race itself or collide with existing state. If what-if shows two operations converging on one shared object, or a delete and a create on the same name, you have found a conflict before it happened:

```bash
az deployment group what-if \
  --resource-group rg-payments-prod \
  --template-file main.bicep \
  --parameters @prod.parameters.json \
  --result-format FullResourcePayloads
```

The full payload format shows the complete intended state of each changed object, which is more verbose but more revealing when you are trying to understand exactly what a modification will do. For routine review the default format, which summarizes the change type per object, is usually enough.

Deployment mode is the setting most directly tied to the delete-create race. ARM deployments run in one of two modes. Incremental mode, the default, adds and updates the resources in the template and leaves everything else in the group untouched. Complete mode, by contrast, makes the group match the template exactly, which means it deletes any resource in the group that is not in the template. Complete mode is powerful for keeping an environment clean, but it is also a frequent source of conflicts and surprises, because a deployment that deletes a resource and a near-simultaneous operation that touches that resource will contend, and a complete-mode deploy that removes and recreates objects can hit the delete-create race on names. The guidance is to use incremental mode unless you have a specific reason to enforce exact-match cleanup, and when you do use complete mode, to run what-if first so the deletions are visible and intentional rather than discovered through a conflict. The mode is set on the deployment:

```bash
az deployment group create \
  --resource-group rg-payments-prod \
  --template-file main.bicep \
  --parameters @prod.parameters.json \
  --mode Incremental \
  --name deploy-payments-safe
```

Pairing validate, what-if, and a deliberate mode choice turns the deployment from a hopeful action into a reviewed one. You see what will change, you confirm no two operations converge on one object, you confirm no unintended delete will race a create, and only then do you run it. That review costs a minute and removes the class of conflicts that come from deploying blind, which is a better trade than any retry loop can offer.

## Conflicts in Terraform-Managed Azure: State, Drift, and Lifecycle

Teams that manage Azure with Terraform meet conflicts in a slightly different shape, because Terraform interposes its own state and locking layer between the engineer and the control plane. Understanding that layer explains both the conflicts Terraform prevents and the ones it introduces. Terraform keeps a state file that records what it believes exists, and at the start of an apply it takes a lock on that state so a second apply cannot mutate the same record concurrently. When the backend is an Azure Storage account, the lock is a blob lease on the state file, and two applies launched together contend on that lease, with the second receiving a state lock error. That error is Terraform doing exactly what it should, protecting the state from a corrupting double write, and the right answer is to serialize applies through a single ordered path rather than to weaken the lock.

The conflict that surprises Terraform users most is the one that comes from drift. Drift is the gap between what the state file records and what actually exists in Azure, and it opens whenever something changes a managed object outside Terraform, such as a portal edit, a direct CLI call, or another tool. When Terraform next plans, it compares its state to reality, sees a difference, and tries to reconcile, and that reconciliation can collide with the out-of-band change or with an operation the other tool left in flight. The classic case is an engineer who tweaks a setting in the portal to fix an incident, then a scheduled apply runs, disagrees with the portal change, and either reverts it or conflicts with a control-plane operation the portal change set in motion. The prevention is the same single-path discipline that prevents pipeline races: changes to a Terraform-managed environment go through Terraform, and the portal is read-only for managed infrastructure except in a declared break-glass situation that is immediately reconciled back into state.

Terraform's resource lifecycle settings interact directly with the name-collision cause. By default, when a change forces replacement, Terraform destroys the old object and then creates the new one, which is the delete-create order that avoids a name collision but causes downtime. The `create_before_destroy` lifecycle setting inverts that order so the new object is created before the old one is removed, which avoids downtime but reintroduces the collision risk for any property that must be unique, because for a moment both objects must coexist with the same unique attribute. The fix is to ensure that anything which must be unique, such as a globally unique name, varies between the old and new object during the overlap, typically by deriving the name from an input that changes when the object is replaced. Choosing between the two lifecycle orders is therefore partly a conflict decision: destroy-first avoids collisions at the cost of downtime, create-first avoids downtime at the cost of needing genuinely distinct unique attributes during the swap.

### Why does a portal change cause a Terraform apply to conflict?

Because the portal edit creates drift between Terraform's recorded state and the live infrastructure, and the next apply tries to reconcile that gap. The reconciliation can revert the change or collide with an operation the portal edit left running. Routing all changes through Terraform, and treating the portal as read-only for managed objects, closes the gap.

The practical setup that keeps Terraform conflict-free mirrors the ARM and Bicep guidance with Terraform-specific mechanics. Route every apply through one pipeline so the state lock is never contended by parallel runs. Keep the portal and ad hoc CLI out of managed environments so drift does not accumulate. Run `terraform plan` and review it the way you would review a what-if, so a replacement that will destroy and recreate an object is visible before it happens rather than discovered through a conflict. Derive unique names from stable inputs so that neither a normal apply nor a create-before-destroy swap collides on the global namespace. With those four habits, the conflicts that Terraform users hit shrink to the rare genuine race, which the state lock already handles by queuing.

## Building Conflict-Resistant Pipelines: A Reference Pattern

The individual fixes in this guide assemble into a single delivery pattern that makes conflicts structurally rare rather than merely recoverable, and it is worth stating that pattern as a whole so a team can adopt it deliberately. The pattern rests on five commitments, each of which closes off one path to a conflict, and together they leave very little room for the four causes to occur.

The first commitment is a single ordered path to each environment. Every change to a given environment flows through one pipeline, and that pipeline is the only identity with standing write access to the environment's infrastructure. This closes the side doors, the portal edits and local runs, that produce uncontrolled concurrency and drift. The second commitment is concurrency control on that path, expressed as a concurrency group or an environment gate, so that two runs targeting the same environment queue rather than race. With a single path that serializes itself, the concurrency cause cannot arise, because there is never a second uncontrolled writer and never two simultaneous runs of the controlled one.

The third commitment is explicit ordering inside each deployment. Dependencies are declared so the platform serializes operations that write through a shared parent or that depend on one another, and separate operations stitched together by a script wait for terminal provisioning states between steps. This closes the provisioning-state race, both the self-race inside a script and the shared-parent contention on objects like virtual networks and App Service plans. The fourth commitment is deterministic, collision-resistant naming. Names derive from stable inputs through a function that produces the same value for the same environment, so redeploys target existing objects rather than colliding, and globally unique names carry a suffix that makes a clash with another tenant unlikely. This closes the collision cause for both local and global namespaces.

The fifth commitment is a pre-flight review gate. Before a production deployment runs, the pipeline runs what-if and surfaces the intended changes for review, with deletions and replacements made explicit, and it uses incremental mode unless exact-match cleanup is specifically required. This catches the conflicts that the other four commitments do not, the unexpected delete-create race or the two operations converging on one object, before they reach the live control plane. A team that holds all five commitments finds that conflicts stop being a recurring incident and become the rare exception, usually a genuine platform action or a long-running operation that simply needs a wait. The investment is modest, a concurrency setting, a naming function, a wait step, and a review gate, and the return is an entire class of failure that stops happening. That is the difference between treating conflicts as noise to retry through and treating them as a property of the delivery system that good design removes.

## Related Failures Often Confused with a Deployment Conflict

A conflict is easy to misidentify, because several unrelated failures present with similar text or the same status code, and chasing the wrong one wastes the time the diagnosis was meant to save. Knowing the near neighbors keeps you on the right cause.

The closest neighbor is the storage 409. Azure Storage returns its own family of 409 conflicts that have nothing to do with control-plane deployment. A blob lease conflict, a container that is mid-delete, or a blob that already exists all produce a 409 from the data plane, and those are resolved with storage-specific handling such as lease management and ETags rather than with deployment serialization. The tell is the scope: a deployment conflict comes back from a resource-management operation through ARM, while a storage 409 comes back from a data-plane call to a blob or container endpoint. If the failing operation is reading or writing blob data rather than deploying a resource, you are in the storage family, and the handling for each storage 409 subtype is covered separately because the fixes are different in kind.

The next neighbor is the authorization failure. A deployment that fails because the deploying identity lacks the role assignment it needs returns an AuthorizationFailed error, not a conflict, but the two get conflated because both stop a deployment and both can mention the scope. The distinction is that a conflict is about timing or ownership of the resource state, while an authorization failure is about the identity's permission to act at all. If the activity log shows the operation was denied for lack of permission rather than blocked by a competing operation or a lock, you have an authorization problem, and the diagnosis path is the role-and-scope reading rather than the serialize-or-wait response.

The third neighbor is the broader family of template errors. A deployment can fail with an InvalidTemplate, a nested DeploymentFailed, a circular dependency, or a resource-provider validation error, and none of those is a conflict. They are problems with the template itself or with the resource definition, and the actionable detail lives in the nested provider message rather than in any notion of a competing operation. When the failure references the template, an expression, a dependency cycle, or a property the provider rejected, you are reading a template error, and the way to read the nested provider message that names the real cause is laid out in the guide to [diagnosing ARM template deployment failures down to the nested provider error](/2022/10/24/fix-arm-template-deployment-errors/). The quick discriminator is to ask whether the platform is complaining about the shape of your request, which is a template error, or about the state of the target resource, which is a conflict. Those two questions route you to two different diagnoses, and answering them first prevents the most common misdirection in this whole area.

## The Serialize-Not-Retry Verdict

A deployment conflict is not a random failure and it is not usually a defect in your template. It is the control plane refusing to let two incompatible truths about a resource hold at once, and the refusal is almost always correct. The work is to find out what the other truth is. Either another operation is in progress, a lock forbids the change, the resource is still mid-transition, or the name is already taken. Each has a confirming signal you can read in minutes from the error payload, the activity log, and the provisioning state, and each has a fix that is some form of serialization or sequencing rather than a blind retry.

The serialize-not-retry rule is the durable takeaway. When you see a conflict, resist the reflex to rerun, because the rerun collides with the same owner that rejected you the first time. Read the signal, name the cause, and address it: queue the racing operations, remove or scope down the lock and restore it safely, wait for the resource to settle, or choose a name that cannot clash. Build the prevention into your delivery so the conflict does not recur, with a single ordered deployment path per environment, explicit dependencies, deterministic naming, and locks placed with intent. An engineer who treats every conflict as a question about ownership and timing, rather than as noise to retry through, resolves it the first time and stops it from coming back. To put this into practice on a resource you can break and rebuild safely, [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to reproduce each conflict type against a sandbox resource group, and [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) to rehearse the serialize-or-wait decision under the kind of time pressure a real incident brings, so the diagnosis becomes reflex rather than research.

## Frequently Asked Questions

### Q: Why does my Azure deployment fail with a 409 Conflict status code?

A 409 means your request conflicts with the current state of the target resource. In deployment terms that current state is one of four things: another operation already holds the resource, a management lock forbids the change, the resource is still in a non-terminal provisioning state from an earlier operation, or a resource with that name already exists. The status code alone does not tell you which, so the productive next step is to read the nested error message and the activity log rather than to retry. The nested message usually names the cause, and the activity log shows you any competing operation with its caller and timestamp. Resolving the 409 means identifying which of the four states applies and addressing that specific state, because the same code carries four different problems with four different fixes.

### Q: How long should I wait before retrying after a deployment conflict?

There is no universal number, because the right wait equals however long the competing operation needs to reach a terminal state, and that varies by resource type from seconds to many minutes. The disciplined approach is to stop guessing at a wait time and instead confirm the resource has settled before retrying. Query the resource's provisioning state and proceed only when it reads Succeeded, or use a wait command that blocks until the terminal state is reached with a generous timeout. Retrying on a fixed short interval tends to collide repeatedly with a long-running operation and can extend the contention. If the conflict came from a lock or a name collision rather than a timing race, no amount of waiting helps at all, so confirm the cause is genuinely a transient in-progress operation before you wait and retry.

### Q: Is a deployment conflict the same as a 409 error from Azure Storage?

No, though they share the status code. A deployment conflict comes back from the Azure Resource Manager control plane when a resource-management operation collides with the resource's state. A storage 409 comes back from the data plane when a blob or container operation collides, for example a blob lease conflict, a container that is mid-delete, or a blob that already exists. The fixes differ entirely: a deployment conflict is resolved by serializing operations, clearing a lock, waiting for provisioning, or renaming, while a storage 409 is resolved by managing leases, using ETags for optimistic concurrency, or backing off after a container delete. The discriminator is the operation that failed. If it was deploying or modifying a resource, it is a deployment conflict; if it was reading or writing blob data, it belongs to the storage family.

### Q: How do I tell whether a lock or a concurrent run caused my conflict?

Read two signals. First, list the management locks at the resource, resource group, and subscription scopes, because a lock cascades downward and a group-level or subscription-level lock can block an operation on a single resource. If a CanNotDelete or ReadOnly lock applies to your target, the lock is a strong candidate. Second, query the activity log for the time window around your failure and look for a second write operation on the same resource with a non-terminal status. If you see a competing operation, concurrency is the cause; if you see no competitor but you do see an applicable lock, the lock is the cause. When both appear, address the lock first, because it will block the operation regardless of timing. The two causes have distinct fixes, so confirming which one applies before acting saves a wasted attempt.

### Q: Why does redeploying the same Bicep template suddenly cause a conflict?

The most common reason is that something changed in the resource's state between deployments. A resource that is still provisioning from a prior run will reject the new write, so a redeploy fired too soon hits a transitioning resource. A second pipeline run racing yours produces the in-progress message. A lock added since the last successful deploy now blocks the write. Or a name that your template generates non-deterministically differs from the existing resource, so ARM tries to create a new resource that collides with something else. Bicep is idempotent when names are stable and unique suffixes are deterministic, so a template that suddenly conflicts on redeploy usually has a timing race, a new lock, or a naming function that is not deterministic. Check the provisioning state and the activity log first, then verify your naming derives from a stable input such as the resource group identity.

### Q: What is the difference between a CanNotDelete lock and a ReadOnly lock?

A CanNotDelete lock permits reads and writes but forbids deletion, so you can still modify a resource's configuration while being protected against accidental removal. A ReadOnly lock is stricter and forbids any operation the platform classifies as a write, which includes both modification and deletion, leaving only read operations permitted. The practical catch with ReadOnly is that many operations engineers think of as harmless are implemented as writes under the covers, such as listing certain keys or adding a child record, so a ReadOnly lock can block more than it appears to. For resources that legitimate deployments must change regularly, a CanNotDelete lock usually gives the right balance of protection without breaking routine updates, while a ReadOnly lock is better reserved for resources that genuinely should not change at all during its lifetime.

### Q: Can two Azure Pipelines stages deploy the same resource group safely?

They can if they never write to the same resource at the same time, and they cannot safely if they do. Two stages that create or modify disjoint resources can run in parallel without conflict, because ARM serializes only contending writes. Two stages that both touch a shared resource, such as the same network security group or the same App Service, will race and one will be rejected. The safe pattern is to bind deployment jobs to a named environment and use concurrency control so that only one run deploys to a given environment at a time, queuing rather than cancelling a second run. Where stages must touch shared resources, sequence them with explicit dependencies so one completes before the next begins, rather than relying on luck that their timing will not overlap.

### Q: Why does creating a Key Vault with a reused name return a conflict?

Because Key Vault supports soft delete, and a deleted vault retains its name for a recovery window rather than freeing it immediately. During that window the name remains reserved, so a create that reuses the name conflicts with the soft-deleted vault still holding it. You have two clean choices. Recover the soft-deleted vault if you actually want it back with its prior contents and access policies, or purge it if you genuinely want a fresh vault with that name, accepting that purging is irreversible and discards the retained material. List the soft-deleted vaults to confirm yours is there, then recover or purge before recreating. If purge protection is enabled, you cannot purge early and must either wait out the retention window or recover, which is a deliberate safeguard rather than a bug.

### Q: How do I check a resource's provisioning state before deploying again?

Query the resource directly and read its provisioningState property. A value of Succeeded means the resource has reached a terminal state and is ready for the next operation, while Updating, Creating, or Deleting means it is mid-transition and will reject a competing write. The Azure CLI exposes this through a resource show command with a query that extracts just the provisioning state, which is faster to read than the full resource body. For scripts that must wait for a resource to settle before proceeding, a wait command that blocks until the state reaches Succeeded with a sensible timeout is cleaner than polling by hand, because it removes the guesswork about how long the resource takes. Reading the provisioning state is the single most useful check for confirming whether a conflict came from a timing race against an in-flight operation.

### Q: Does a deployment conflict mean my ARM template has a syntax error?

No. A conflict is about the state of the target resource, not the shape of your template. A template syntax or schema problem surfaces as an InvalidTemplate error, and a deeper template problem such as a circular dependency or a rejected expression surfaces as a nested DeploymentFailed with a provider message describing what was wrong with the request. A conflict, by contrast, means the request was well formed but could not proceed because another operation owns the resource, a lock forbids it, the resource is provisioning, or the name is taken. The quick discriminator is whether the platform is complaining about the shape of your request, which is a template error, or about the state of the resource, which is a conflict. If you see InvalidTemplate or a circular dependency message, you are reading a template error and should diagnose the template, not serialize operations.

### Q: Why do parallel Terraform applies cause an Azure state lock error?

Terraform takes a lock on its state backend at the start of an apply and releases it when the apply finishes, specifically to prevent two applies from mutating the same state at once. When the backend is an Azure Storage account, that lock is implemented as a blob lease on the state file. Two applies launched in parallel will contend on that lease, and the second receives a state lock error, which is Terraform protecting you from a corrupted state. The right response is not to disable locking but to route all applies through a single ordered path so they never run concurrently. If a previous apply crashed and left the lease held, you can force-unlock the state, but only after confirming no apply is genuinely running, because clearing a live lock reintroduces the race the lock exists to prevent.

### Q: How do I find which user or service principal holds a resource?

The activity log records the caller for every control-plane operation, so querying it for the resource and the time window around your conflict reveals who launched the competing operation. The caller field shows the user principal name or the service principal identity that initiated the operation, and the operation name and status tell you what they were doing and whether it has finished. When the competing operation comes from a pipeline, the caller is the pipeline's service connection identity, which points you at which pipeline to check. When it comes from a person, the caller names them directly. This is often the moment the cause becomes obvious, because seeing that a second engineer or a parallel pipeline started a write on the same resource explains the conflict immediately and tells you whether to wait, coordinate, or fix the concurrency control.

### Q: Can a subscription-level lock block a deployment to a single resource?

Yes. Management locks inherit downward through the scope hierarchy, so a lock placed on a subscription applies to every resource group and every resource within that subscription, and a lock on a resource group applies to every resource in the group. This is the source of a frequently confusing case, where an engineer examines the resource they are deploying, finds no lock on it, and concludes locks are not the issue, when in fact a lock several scopes above is cascading down. Confirming the lock cause therefore requires listing locks at the resource, the resource group, and the subscription, not only at the resource itself. If a ReadOnly lock sits at the subscription scope, it will block writes to every resource beneath it, which can be exactly the intended governance behavior, so the fix may be to route the change through an approved process rather than to remove the lock.

### Q: Why does an automation script hit a conflict right after creating a resource?

Because many ARM operations are asynchronous, and the API call that created the resource often returns at the point the request was accepted rather than the point the resource finished provisioning. The script sees success and immediately fires a follow-up modification, which lands while the resource is still in a Creating or Updating state, and the platform rejects the follow-up to protect the in-flight change. The resource is not locked and there is no second operator; the script is racing itself by not waiting. The fix is to wait for the resource to reach a terminal provisioning state before the next operation, using a wait command that blocks until the state reads Succeeded. Inside a single ARM or Bicep deployment, the equivalent is to declare the dependency so the platform serializes the dependent resource behind the one it needs.

### Q: Should I use a retry loop to handle Azure deployment conflicts?

Only with care, and only after diagnosis. A bare retry loop that fires immediately collides with the same in-progress operation or the same lock that rejected the first attempt and fails identically, and hammering the control plane can extend the contention window rather than shorten it. A retry helps only for the narrow case where the conflict was a brief provisioning race, and even then it should use a backoff long enough for the competing operation to reach a terminal state. No amount of retrying clears a lock, frees a globally taken name, or recovers a soft-deleted resource holding a name, so retrying those causes is pure waste. The disciplined posture is to confirm the conflict is a transient timing race before retrying with backoff, and to serialize the underlying operations so the race does not recur.

### Q: How does uniqueString help prevent name collisions in Bicep?

The uniqueString function returns a deterministic hash derived from the inputs you pass it, which makes it ideal for generating names that are both unique and reproducible. Seeding it with the resource group identity means the same resource group always produces the same suffix, so redeploying a template targets the existing resource rather than trying to create a new one and colliding. This solves the two flavors of name collision at once. It keeps locally generated names from clashing within a subscription, and for resource types that require globally unique names, such as storage accounts, it produces a suffix unlikely to be taken elsewhere. Wrapping the result to respect each resource type's length limit, for example trimming a storage account name to its character cap, completes the pattern and makes deterministic, collision-resistant naming a structural property of the template rather than a manual chore.

### Q: What does ScopeLocked mean in an Azure deployment error?

ScopeLocked indicates that a management lock at the scope of your operation is preventing the change. The scope might be the resource itself, the resource group, or the subscription, and because locks cascade downward, the lock causing a ScopeLocked error is not always on the resource you are deploying. The error is the platform enforcing a deliberate guardrail rather than a transient failure, so retrying achieves nothing until the lock is addressed. The response is to list the locks at every applicable scope, read the level to see whether it forbids deletes alone or all writes, and check the notes to understand why the lock exists before touching it. If the lock should yield to your operation, remove or downgrade it for the change and restore it immediately afterward so the resource spends minimal time unprotected.

### Q: Why do a delete and a create on the same name race and conflict?

Because a delete is a state transition that takes time, and during it the resource still exists in a Deleting state while holding its name. When a pipeline tears down a resource and recreates it under the same name in quick succession, the create can start before the delete finishes, so it collides with the still-present resource and is rejected. The conflict reads like a name collision but is really a sequencing failure between two operations that should have run in order. The fix is to wait for the delete to complete before starting the create, watching for the resource to disappear rather than to reach a succeeded state. For soft-delete-capable resource types the wait is longer still, because the name stays reserved through the recovery window, so the create must wait for a purge or trigger a recovery instead.

### Q: Can I cancel an in-progress Azure operation to clear a conflict faster?

Sometimes, but it is rarely the right move. A few long-running operations expose a cancel action, and cancelling one frees the resource sooner than waiting for it to finish. The risk is that cancelling a deployment mid-flight can leave the object in a half-applied state that is harder to reason about than the original conflict, and a partial change may itself need cleanup. The safer default is to let the competing operation reach its terminal state and then proceed, especially in production, where an interrupted change can be worse than a short wait. Cancel only when you understand exactly what the operation was doing and you are confident the object tolerates an interruption at that point. For most conflicts, confirming the operation has finished and then running once is both faster overall and less risky than cancelling and cleaning up.

### Q: Does deploying in incremental mode versus complete mode change conflict risk?

Yes. Incremental mode, the default, adds and updates the resources in your template and leaves everything else in the group alone, which keeps the deployment focused on the objects you intend to change and avoids triggering deletes. Complete mode makes the group match the template exactly, deleting anything not present in the template, which is powerful for cleanup but introduces conflict risk in two ways. The deletes it performs can race a concurrent operation touching those objects, and a complete-mode run that removes and recreates an object can hit the delete-create race on names. The guidance is to default to incremental mode and reserve complete mode for cases where exact-match cleanup is genuinely required, always running what-if first so the deletions are visible and intended rather than discovered through a conflict mid-run.
