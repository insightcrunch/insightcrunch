---
layout: post
title: "Fix Azure Storage 409 Conflict Errors"
page_title: "Fix Azure Storage 409 Conflict Errors: Diagnose Lease, BlobAlreadyExists, ETag, and ContainerBeingDeleted Conflicts"
date: 2022-08-08
categories: ["Technology"]
tags: ["Azure", "Azure Storage", "Blob Storage", "Troubleshooting", "Error Codes", "Cloud Computing"]
excerpt: "Azure Storage 409 conflict errors split into four types: existence, lease, container-lifecycle, and blob-state. Diagnose which one you hit and fix each."
image: "/assets/images/blog/blog-68.webp"
reading_time: 60
author: "nathan-cole"
last_updated: 2022-08-08
lang: en
---
A 409 from Azure Storage almost never means what the first guess assumes. The status line reads `409 Conflict`, the application logs a stack trace, and the reflex is to wrap the call in a retry loop and move on. That reflex is exactly what turns a five-minute fix into a recurring incident. An Azure Storage 409 conflict error is the service telling you that the request you sent disagrees with the current state of the target resource, and there are at least four structurally different reasons a resource can be in a state your request did not expect. One of them clears on its own in a second. One of them will never clear no matter how many times you retry, because the retry itself is the thing holding the conflict open. Reading the 409 correctly means deciding which of those four you are looking at before you write a single line of handling code.

This guide takes the single status code `409` and decomposes it into the conflict families that actually produce it: an existence conflict such as `BlobAlreadyExists`, a lease conflict such as `LeaseAlreadyPresent`, a container-lifecycle conflict such as `ContainerBeingDeleted`, and a blob-state conflict such as `SnapshotsPresent` or `PendingCopyOperation`. For each family you get the response signal that confirms it is yours, the tested fix with a command, and the design change that stops it coming back. The boundary that wastes the most engineering time, the line between a 409 and its lookalike `412 Precondition Failed`, gets its own treatment, because half the "random 409s" reported in production are 412s misread, and the rest are 409s a developer expected to behave like a 412.

![Fix Azure Storage 409 Conflict Errors](/assets/images/blog/blog-68.webp)

## What an Azure Storage 409 conflict actually means

HTTP defines `409 Conflict` as a response sent when the request could not be completed because it conflicts with the current state of the target resource, and the specification expects the response to carry enough information for the client to recognize the source of the conflict and resubmit a corrected request. Azure Storage follows that definition precisely, which is the single most useful fact to hold onto. A 409 is never a transport problem, never a throttle, and never an authentication failure. The credentials were accepted, the network path was open, the request reached the storage service, the service parsed it, and then the service compared what the request asked for against the present state of the blob, container, queue, table entity, or file and found a contradiction it refuses to resolve silently.

That refusal is deliberate. Storage could, in principle, paper over many of these conflicts. It could let a create call quietly overwrite an existing blob, let a lease acquisition steal an active lease, or let a container be recreated the instant a delete is requested. It does none of those things by default because each would hide a correctness problem from the caller. The 409 is a correctness signal pushed back to the client so the client can decide what the right behavior is. The whole skill of handling a 409 well is recognizing that the service has handed you a decision, not an error to suppress.

Because the conflict is about resource state, the same line of application code can produce a 409 for completely different reasons on different days. A `CreateContainer` call returns 409 with `ContainerAlreadyExists` when the container is simply already there, and returns 409 with `ContainerBeingDeleted` when a delete issued seconds earlier has not finished. Both are 409s on the identical call, both are conflicts of state, and they demand opposite handling. The first wants you to stop trying to create and proceed; the second wants you to wait and then create. A retry loop that treats them the same will sail through the first case by accident and spin forever on the second. This is why the families matter more than the status code.

The account-level access model, the redundancy options, and the resource hierarchy that all of this sits on are covered in depth in [the complete guide to Azure Storage accounts](/2022/01/31/azure-storage-accounts-complete-guide/); this article assumes that model and focuses on the conflict semantics that ride on top of it.

## Reading the 409: where the real diagnostic signal lives

A bare `409 Conflict` status is almost useless on its own. Azure Storage attaches the information you need in three predictable places, and learning to read all three is the difference between guessing and diagnosing. The status code tells you a conflict happened. The error code tells you which conflict. The request identifiers tell you which specific request to trace if you need platform support to look deeper.

### Where does Azure Storage put the specific 409 error code?

Every Storage 409 carries an `x-ms-error-code` response header naming the exact condition, and the response body repeats it as an XML `<Error><Code>` element with a human-readable `<Message>`. Read the header first; it is the canonical machine-readable cause and the value your handling code should branch on.

The XML body of a Storage error looks like this, and the `<Code>` value is the field that decides everything downstream:

```xml
<?xml version="1.0" encoding="utf-8"?>
<Error>
  <Code>ContainerBeingDeleted</Code>
  <Message>The specified container is being deleted. Try operation later.
RequestId:00000000-0000-0000-0000-000000000000
Time:2022-08-08T12:00:00.0000000Z</Message>
</Error>
```

The same `Code` string appears in the `x-ms-error-code` header, which is the value to inspect from code rather than parsing the body. Two more headers belong in every Storage error log you keep. The `x-ms-request-id` is the service-side identifier for the request; it is the value support engineers ask for first when they need to trace a request through the storage backend. The `x-ms-client-request-id`, which you can set yourself on the outgoing request, lets you correlate the failure in your own logs with the platform record. Setting a client request ID on writes that can conflict is one of the cheapest diagnostic investments available, because it turns "a 409 happened somewhere around noon" into "request abc-123 conflicted at 12:00:01.4 against this blob."

You can pull the raw headers and body for a single object with a direct REST call when you want to see exactly what the service is returning, before any SDK has wrapped it in an exception:

```bash
# Inspect the raw response for a blob operation, headers included
curl -i -X PUT \
  -H "x-ms-version: 2021-08-06" \
  -H "x-ms-blob-type: BlockBlob" \
  -H "If-None-Match: *" \
  "https://<account>.blob.core.windows.net/<container>/<blob>?<sas>" \
  --data-binary @localfile.bin
```

When that `PUT` carries `If-None-Match: *` against a blob that already exists, the response status is `409` and the `x-ms-error-code` header reads `BlobAlreadyExists`. Strip the `If-None-Match` header and the same call becomes a plain overwrite that returns `201 Created`. Seeing that flip happen against your own account, with your own eyes, is worth more than any amount of reading, and reproducing each subtype this way is exactly the kind of drill you can [work through on ReportMedic's scenario-based troubleshooting drills](https://reportmedic.org/tools/azure-troubleshooting-drills.html) once you know which conditions to set.

### How does a 409 surface inside the Azure SDKs?

The modern Azure SDKs raise a single typed exception for any non-success status and expose the error code as a property. In .NET the type is `RequestFailedException` with `.Status` equal to 409 and `.ErrorCode` equal to the `x-ms-error-code` value; in Python it is `ResourceExistsError` or `HttpResponseError` with `.error_code`; in Java it is `BlobStorageException` with `.getErrorCode()`.

Branching on the typed error code rather than the numeric status is the pattern that separates robust handling from fragile handling. In .NET with the `Azure.Storage.Blobs` v12 library, the shape is consistent across every operation:

```csharp
using Azure;
using Azure.Storage.Blobs;
using Azure.Storage.Blobs.Models;

try
{
    await blobClient.UploadAsync(stream, overwrite: false);
}
catch (RequestFailedException ex) when (ex.Status == 409)
{
    switch (ex.ErrorCode)
    {
        case BlobErrorCode.BlobAlreadyExists:
            // The blob is already there. Decide overwrite vs skip.
            break;
        case BlobErrorCode.LeaseAlreadyPresent:
            // Someone holds a lease. Acquire later or coordinate.
            break;
        case BlobErrorCode.ContainerBeingDeleted:
            // The container delete has not finished. Back off and wait.
            break;
        default:
            // Unhandled 409 subtype. Log the error code and surface it.
            throw;
    }
}
```

The Python equivalent reads the same way, with the error code surfaced on the exception:

```python
from azure.core.exceptions import ResourceExistsError, HttpResponseError

try:
    blob_client.upload_blob(data, overwrite=False)
except ResourceExistsError:
    # 409 BlobAlreadyExists, the SDK maps this conflict to a dedicated type
    handle_already_exists()
except HttpResponseError as ex:
    if ex.status_code == 409:
        code = ex.error_code  # e.g. "LeaseAlreadyPresent", "ContainerBeingDeleted"
        route_by_conflict(code)
    else:
        raise
```

The point in every language is identical. Catch the conflict, read the error code, and route on the error code. The numeric `409` tells you a state conflict exists; only the error code tells you which state and therefore which fix. Code that catches a `RequestFailedException` and retries on `409` without reading `.ErrorCode` is the single most common reason a `ContainerBeingDeleted` turns into a hung process.

### Where do 409s show up after the fact?

Resource logs are the answer when the conflict already happened and you need to find it later. With diagnostic settings sending blob logs to a Log Analytics workspace, the `StorageBlobLogs` table records every operation with its `StatusCode`, `StatusText`, and the operation name, so you can query for the exact requests that returned 409 and group them by error.

If you have routed diagnostic settings for the storage account to Log Analytics, this Kusto query surfaces the conflicts and shows which operations are producing them:

```kusto
StorageBlobLogs
| where TimeGenerated > ago(24h)
| where StatusCode == 409
| summarize Count = count() by OperationName, StatusText
| order by Count desc
```

The `StatusText` column carries the same error code string you saw in the header, so a result row reading `OperationName = "PutBlob"` and `StatusText = "BlobAlreadyExists"` tells you a create-only write is colliding with existing blobs, while `OperationName = "CreateContainer"` and `StatusText = "ContainerBeingDeleted"` tells you something is recreating containers too fast after deleting them. Diagnostic logging on the data plane is not on by default, so flag it for verification against your account configuration; without it, the only record of a 409 is whatever your own application captured at the moment it happened.

## The four families of an Azure Storage 409 conflict error

Every Storage 409 belongs to one of four families, and the family, not the status code, determines the fix. The families are existence conflicts, lease conflicts, container-lifecycle conflicts, and blob-state conflicts. The table below is the reference to keep open while debugging; it maps each common error code to the family it belongs to, the state condition that produces it, and the handling that resolves it. This is the InsightCrunch 409 conflict table, and it exists to replace the blind retry loop with a routing decision.

| Error code (`x-ms-error-code`) | Family | State that produced it | Correct handling |
| --- | --- | --- | --- |
| `BlobAlreadyExists` | Existence | A create-only write (`If-None-Match: *`) hit a blob that exists, or two writers raced to create | Decide overwrite vs skip; for create-only, treat the loser of the race as a no-op |
| `ContainerAlreadyExists` | Existence | `CreateContainer` ran against a container that already exists | Treat as success if create-if-not-exists was the intent; otherwise stop |
| `PathAlreadyExists` | Existence | A Data Lake Gen2 `Create Path` hit an existing file or directory | Use overwrite semantics or branch to update instead of create |
| `LeaseAlreadyPresent` | Lease | `Acquire Lease` ran while an active lease exists | Wait for release, use the existing lease ID, or break the lease if it is orphaned |
| `LeaseIdMismatchWithLeaseOperation` | Lease | Renew, change, or release used a lease ID that does not match the active one | Use the correct lease ID; the holder changed or the lease was reacquired |
| `LeaseNotPresentWithLeaseOperation` | Lease | Renew, change, or release ran when no lease is held | The lease already expired or was released; stop trying to manage it |
| `LeaseAlreadyBroken` | Lease | A break was requested on a lease already in the broken state | No action; the lease is gone |
| `ContainerBeingDeleted` | Container lifecycle | `CreateContainer` ran while a delete of the same name is in progress | Back off with increasing delay until the name frees, then create |
| `ContainerBeingDisabled` | Container lifecycle | An operation hit a container mid-disable | Back off and retry the operation after the transition completes |
| `SnapshotsPresent` | Blob state | A blob delete omitted snapshot handling while snapshots exist | Reissue the delete with the include-snapshots option |
| `PendingCopyOperation` | Blob state | A write or delete hit a blob with a copy still in flight | Wait for the copy to finish or abort the copy first |
| `BlobImmutableDueToPolicy` | Blob state | A write or delete hit a blob under an immutability policy or legal hold | Respect the policy; the operation is blocked until the retention window or hold clears |

The namable rule that runs through every row is the conflict-is-state rule: a Storage 409 is the service reporting that the resource state changed under you, so the fix is to match the handling to the conflict type, never to retry blindly. Retrying a `ContainerAlreadyExists` is harmless and pointless. Retrying a `ContainerBeingDeleted` immediately is harmful, because the retry arrives while the delete is still running and conflicts again, and a tight loop can keep arriving inside the delete window indefinitely. Retrying a `LeaseAlreadyPresent` will never succeed until the lease holder releases, which your retry has no power to make happen. The rule is not "do not retry"; it is "retry only the families where waiting changes the state, and even then with backoff."

## Existence conflicts: BlobAlreadyExists and ContainerAlreadyExists

The existence family is the most common 409 and the easiest to reason about once the create-only semantics are clear. It appears whenever an operation asks the service to bring a resource into being on the assumption that it does not yet exist, and the resource is already there. The two everyday forms are `BlobAlreadyExists` on a write and `ContainerAlreadyExists` on a container create, with `PathAlreadyExists` as the Data Lake Gen2 cousin.

### Why a create-only write returns BlobAlreadyExists

The behavior hinges on the conditional header on the write. A normal `Put Blob` with no conditional header overwrites whatever is there and returns `201 Created`; the service treats the upload as authoritative. A `Put Blob` carrying `If-None-Match: *` is a create-only write, an instruction that reads "write this only if no blob currently exists at this name." When a blob does exist, the precondition is not met and the service returns `409 BlobAlreadyExists`. The conditional header is the entire difference between an overwrite and a conflict.

This is where intent and code diverge most often. A developer calls an upload method, the SDK defaults to create-only behavior for that overload, a blob already exists from a previous run, and the result is a 409 that reads like a bug but is the SDK doing exactly what create-only means. In the .NET v12 library, `UploadAsync(stream)` without `overwrite: true` sends the create-only precondition and throws `RequestFailedException` with `BlobAlreadyExists` if the blob is present; `UploadAsync(stream, overwrite: true)` drops the precondition and overwrites. The fix is not a retry. The fix is deciding what you actually want:

```csharp
// Intent A: overwrite whatever is there
await blobClient.UploadAsync(stream, overwrite: true);

// Intent B: write only if absent, and accept "already there" as a no-op
try
{
    await blobClient.UploadAsync(stream, overwrite: false);
}
catch (RequestFailedException ex) when (ex.ErrorCode == BlobErrorCode.BlobAlreadyExists)
{
    // Another writer already created this blob. For idempotent create,
    // that is success, not failure. Log and continue.
}
```

Intent B is the correct shape for an idempotent create under concurrency. When two workers process the same message and both try to create the same blob, exactly one wins with `201 Created` and the other receives `409 BlobAlreadyExists`. If the desired outcome is "the blob exists with this content," the loser of the race has nothing to fix; the blob exists, the work is done, and the 409 is the signal that someone else did it first. Treating that 409 as a fatal error is the misdiagnosis; treating it as a confirmation that the create succeeded somewhere is the correct reading.

### Handling ContainerAlreadyExists and create-if-not-exists

Container creation behaves the same way. `Create Container` against a name that exists returns `409 ContainerAlreadyExists`. The SDKs ship a create-if-not-exists variant precisely so you do not have to wrap every container create in a try-catch: `CreateIfNotExistsAsync` in .NET returns the existing container without raising on the 409, and `create_container` in Python paired with catching `ResourceExistsError` gives the same result. The command-line equivalent is idempotent by design as well.

```bash
# Idempotent container creation from the CLI; succeeds whether or not it exists
az storage container create \
  --name mycontainer \
  --account-name myaccount \
  --auth-mode login
```

The CLI `container create` does not error when the container exists; it reports `created: false` and returns success, which is the behavior you want for setup scripts that run repeatedly. The lesson generalizes: when the operation is "make sure this exists," use the create-if-not-exists form and the 409 never surfaces. The 409 is reserved for the case where you genuinely needed the resource to be new, and that case deserves a real decision rather than a swallowed exception.

A subtler existence conflict appears in Data Lake Gen2, where the hierarchical namespace makes a path a first-class object. Creating a file or directory that already exists returns `PathAlreadyExists`, and because directories are real objects in the Gen2 namespace rather than virtual prefixes, you can hit this on directory creation in ways that flat blob storage never produces. The handling is the same family logic: decide whether you meant create-only or overwrite, and branch to an update path if the object already exists.

## Lease conflicts: when a 409 means someone holds the blob

Lease conflicts are the family that punishes blind retries hardest, because the state holding the conflict open is owned by another process and your retries cannot change it. A lease is an exclusive write-and-delete lock on a blob or container, taken explicitly through the lease API and identified by a lease ID. While a lease is active, the only writer who can modify or delete the resource is the one holding the matching lease ID. Leases are the mechanism behind many coordination patterns in Azure, including the way some platform services elect a single owner for a resource, and the lease state machine is worth understanding precisely because its conflicts are otherwise mystifying. The mechanics of leases and how they interact with ETags are laid out in [the Blob Storage engineering guide](/2022/05/09/azure-blob-storage-engineering-guide/), and the conflict semantics below build directly on that model.

### What does LeaseAlreadyPresent mean and how do I clear it?

`LeaseAlreadyPresent` is a 409 returned when you call Acquire Lease on a resource that already has an active lease. It means another holder took the lease and has not released it or let it expire. Acquiring again will keep failing until the lease ends, so the fix is to wait for expiry, coordinate to reuse the lease ID, or break the lease if its holder has crashed.

A lease can be taken for a fixed duration between 15 and 60 seconds or as an infinite lease that lasts until it is explicitly released or broken; treat these durations as values to verify against the current Storage documentation, since service limits do change. A fixed lease auto-expires if the holder stops renewing, which means a `LeaseAlreadyPresent` from a fixed lease resolves itself within at most the lease duration. An infinite lease never expires on its own, so a process that acquires an infinite lease and then crashes leaves the blob locked until someone breaks the lease deliberately. That orphaned-infinite-lease scenario is the classic "I cannot write to this blob and nothing has a lease that I can see" incident, and the resolution is to break the lease.

```bash
# See whether a blob is leased and in what state
az storage blob show \
  --name myblob --container-name mycontainer \
  --account-name myaccount --auth-mode login \
  --query "properties.lease"

# Break a stuck lease immediately (break-period 0 ends it at once)
az storage blob lease break \
  --blob-name myblob --container-name mycontainer \
  --account-name myaccount --auth-mode login \
  --lease-break-period 0
```

The `blob show` query returns the lease `status`, `state`, and `duration`, which is how you confirm a lease is the cause before touching anything. A `state` of `leased` with `duration` of `infinite` and no living process that should hold it is the orphaned-lease fingerprint. Breaking with a break period of zero ends the lease at once; a non-zero break period lets the current holder finish but blocks new acquisitions during the break window, which is the gentler choice when you are not certain the holder is dead.

### The acquire-use-release pattern that prevents lease conflicts

Most lease conflicts trace back to a missing release. A process acquires a lease, does its work, and exits, by exception or by crash, without releasing. The next process to need the blob hits `LeaseAlreadyPresent` and, if the lease was infinite, stays blocked. The pattern that prevents this is to scope the lease to a try-finally so the release runs on every exit path, and to prefer a fixed-duration lease with renewal over an infinite lease so that even a hard crash self-heals within the lease duration.

```csharp
var leaseClient = blobClient.GetBlobLeaseClient();
BlobLease lease = await leaseClient.AcquireAsync(TimeSpan.FromSeconds(30));
try
{
    // Renew periodically if the work outlasts the lease duration.
    // All writes must pass the lease ID as a condition:
    var conditions = new BlobRequestConditions { LeaseId = lease.LeaseId };
    await blobClient.UploadAsync(stream, new BlobUploadOptions { Conditions = conditions });
}
finally
{
    await leaseClient.ReleaseAsync();
}
```

Two failure modes hide in lease handling and both produce 409s on the lease-management calls. The first is renewing or releasing with the wrong lease ID, which returns `LeaseIdMismatchWithLeaseOperation`; this happens when the lease expired and a different process reacquired it, giving the resource a new lease ID while your code still holds the old one. The correct reading is that you lost the lease and must stop assuming you own the blob. The second is renewing or releasing a lease that no longer exists, which returns `LeaseNotPresentWithLeaseOperation`; this means the lease already expired or was released, and the fix is to stop the lease-management call rather than to keep issuing it.

A critical distinction belongs here and it is the source of enormous confusion: the conflicts above are 409s on lease-management operations, but a write to a leased blob that omits the lease ID does not return 409. It returns `412 Precondition Failed` with `LeaseIdMissing`, and a write with the wrong lease ID returns `412` with `LeaseIdMismatchWithBlobOperation`. The brief framing that lumps `LeaseIdMissing` in with the 409 family is the trap; the service draws a clean line. Lease management that conflicts is 409. Data operations that violate a lease condition are 412. Routing both into the same handler is why teams chase phantom errors. The 409-versus-412 boundary gets its own section below because it is the most expensive confusion in this entire error space.

## Container-lifecycle conflicts: ContainerBeingDeleted and the reserved-name window

The container-lifecycle family contains the one 409 that genuinely requires patience, and it is the conflict most likely to be misdiagnosed as a hang. When you delete a container, the operation returns quickly and reports success, but the actual deletion of the container and its contents proceeds asynchronously on the storage backend. During that window the container name is reserved and cannot be reused. Any attempt to create a container with the same name while the delete is in progress returns `409 ContainerBeingDeleted`.

### Why does creating a container right after deleting it fail?

Container deletion is asynchronous. The delete call returns success immediately, but the backend continues removing the container and its blobs for a period that depends on how much data the container held. Until that completes, the name stays reserved and a recreate attempt returns `409 ContainerBeingDeleted`. The recreate cannot succeed until the delete finishes, so the only correct response is to wait.

This is the conflict that exposes a blind retry loop as actively harmful. The instinct after a `ContainerBeingDeleted` is to retry the create, and a naive loop retries immediately, arrives while the delete is still running, conflicts again, and repeats. If the container held a lot of data, the delete window can be long enough that a tight retry loop spins through hundreds of attempts before the name frees, and an aggressive loop can run long enough to look like a deadlock. The fix is a backoff with a meaningful, increasing delay, not a tight retry.

```csharp
// Recreate a container after a delete, waiting out the reserved-name window
async Task RecreateContainerAsync(BlobContainerClient container)
{
    var delay = TimeSpan.FromSeconds(5);
    var deadline = DateTimeOffset.UtcNow.AddMinutes(5);
    while (true)
    {
        try
        {
            await container.CreateAsync();
            return;
        }
        catch (RequestFailedException ex) when (ex.ErrorCode == "ContainerBeingDeleted")
        {
            if (DateTimeOffset.UtcNow > deadline)
                throw new TimeoutException("Container name did not free within the window.");
            await Task.Delay(delay);
            delay = TimeSpan.FromSeconds(Math.Min(delay.TotalSeconds * 1.5, 30));
        }
    }
}
```

The backoff here starts at five seconds, grows by half each iteration, caps at thirty seconds, and gives up after a bounded deadline rather than looping forever. The cap and the deadline matter as much as the backoff itself; a loop with no ceiling on total time is how a transient lifecycle conflict becomes a stuck worker. The deeper lesson is architectural: deleting and immediately recreating a container by the same name is a pattern to avoid, not a pattern to make resilient. If you find yourself writing the loop above as a routine operation rather than a rare recovery, the design wants rethinking.

### Designing around the reserved-name window

There are three durable ways to avoid the recreate conflict entirely, and they beat any retry loop. The first is to not delete the container at all when the goal is to clear its contents; deleting the blobs inside and keeping the container avoids the lifecycle conflict because the container never enters the deleting state. The second is to use a fresh container name on recreate, typically by appending a timestamp or a generation counter, so the new container never collides with the reserved name of the old one. The third applies when the delete was a mistake: container soft delete, when enabled on the account, lets you restore a deleted container within the retention period instead of recreating it, which sidesteps the conflict and recovers the data.

```bash
# Clear contents without deleting the container (no lifecycle conflict)
az storage blob delete-batch \
  --source mycontainer \
  --account-name myaccount --auth-mode login

# If container soft delete is enabled, restore rather than recreate
az storage container restore \
  --name mycontainer \
  --account-name myaccount --auth-mode login
```

Container soft delete and the restore command depend on the feature being enabled on the account and on the deleted container still being inside its retention window, so verify both against the account configuration before relying on restore as your recovery path. The broader point holds regardless: the container-lifecycle 409 is the one place where the right answer often includes waiting, but the better answer is a design that never enters the conflicting state.

## Blob-state conflicts: snapshots, pending copies, and immutability

The fourth family covers conflicts that arise from a blob being in a particular state that blocks the operation you requested, even though the blob exists, no lease is held, and no name is reserved. These are less common than the first three but harder to diagnose precisely because they do not match the mental model of "create collided" or "someone holds a lock." The blob simply has a property or an in-flight operation that makes your request invalid right now.

The most frequent of these is `SnapshotsPresent`. A blob can carry point-in-time snapshots, and deleting the base blob while snapshots exist requires telling the service what to do with them. A plain delete that omits snapshot handling returns `409 SnapshotsPresent`, because deleting the base blob would orphan its snapshots and the service refuses to do that implicitly. The fix is to reissue the delete with an explicit snapshot option, either deleting the snapshots along with the base blob or deleting only the snapshots.

```bash
# Delete a blob and its snapshots together
az storage blob delete \
  --name myblob --container-name mycontainer \
  --account-name myaccount --auth-mode login \
  --delete-snapshots include
```

In the SDKs the same choice is an enum on the delete call: `DeleteSnapshotsOption.IncludeSnapshots` to remove the base blob and its snapshots, or `DeleteSnapshotsOption.OnlySnapshots` to keep the base blob and clear its snapshots. Choosing one of these turns the 409 into a clean delete. The misdiagnosis here is assuming the blob is locked or leased when in fact it simply has snapshots; the `x-ms-error-code` header reading `SnapshotsPresent` settles the question instantly, which is one more reason to read the header before theorizing.

A second blob-state conflict is `PendingCopyOperation`. When you start an asynchronous copy into a blob, that destination blob has a copy in flight, and certain operations against it while the copy is pending return 409. The resolution is either to wait for the copy to finish, polling its copy status, or to abort the copy explicitly with an abort-copy call before doing what you intended. The copy status is readable from the blob's properties, so the confirming signal is a copy state of `pending` on the destination blob.

The third blob-state conflict is the one that should not be retried at all: immutability. A blob under a time-based retention policy or a legal hold cannot be modified or deleted until the retention window elapses or the hold is removed, and an attempt returns a 409 indicating the blob is immutable due to policy. This is not a transient conflict and not a coordination problem; it is the storage account enforcing a compliance guarantee. The correct handling is to respect it. Retrying, breaking, or working around an immutability conflict is precisely what the feature exists to prevent, and the only legitimate path forward is to wait out the retention period or to have an authorized principal clear the legal hold through the proper governance process.

## The 409-versus-412 boundary that wastes the most engineering time

More 409 incidents are actually 412 incidents, or 409s expected to behave like 412s, than any other single confusion in Azure Storage error handling. The two status codes are siblings, both are about preconditions and state, and the SDKs raise similar-looking exceptions for both, which is exactly why teams conflate them. Drawing the line cleanly removes a whole category of phantom bugs.

A `409 Conflict` says the request conflicts with the resource state in a way the service will not resolve, and the conflict is usually about existence or about a management operation on a lock. A `412 Precondition Failed` says a conditional header you sent, an `If-Match`, an `If-None-Match`, an `If-Modified-Since`, or a lease condition on a data operation, evaluated to false against the current state. The shared idea is "the state is not what your request assumed," but the mechanism differs, and so does the right handling.

Optimistic concurrency is where this bites hardest. The standard read-modify-write pattern reads a blob, captures its ETag, modifies the content, and writes back with `If-Match: <etag>` so the write succeeds only if no one changed the blob in between. When someone did change it, the ETag no longer matches, the precondition fails, and the service returns `412 Precondition Failed`, not 409. Developers who expect "a concurrency conflict" reach for 409 handling and never catch it, because the conflict surfaced as 412. The create-only side of the same coin is the 409: `If-None-Match: *` on a create returns `409 BlobAlreadyExists` when the blob exists. So the ETag mechanism produces a 412 on the update path and a 409 on the create-only path, and treating them as one error is the mistake.

```csharp
// Optimistic concurrency: 412 on a mid-air collision, not 409
BlobDownloadResult download = await blobClient.DownloadContentAsync();
ETag etag = download.Details.ETag;
byte[] updated = Modify(download.Content.ToArray());

try
{
    await blobClient.UploadAsync(new BinaryData(updated), new BlobUploadOptions
    {
        Conditions = new BlobRequestConditions { IfMatch = etag }
    });
}
catch (RequestFailedException ex) when (ex.Status == 412)
{
    // Someone else wrote between read and write. Re-read and retry the merge.
    await RetryWithFreshEtag(blobClient);
}
```

The lease side of the boundary follows the same split, and it is worth restating because it is the precise error the brief's framing risks blurring. Lease-management operations that conflict return 409: `LeaseAlreadyPresent`, `LeaseIdMismatchWithLeaseOperation`, `LeaseNotPresentWithLeaseOperation`. Data operations against a leased blob that violate the lease condition return 412: `LeaseIdMissing` when you write to a leased blob without supplying the lease ID, and `LeaseIdMismatchWithBlobOperation` when you supply the wrong one. The rule of thumb that survives every case is this: a conflict on the management of state, creating, acquiring, releasing, is a 409; a conflict on a conditional data operation, your `If-Match` or your lease-on-write condition, is a 412. Build two handlers, route by status code first and error code second, and the phantom-409 incidents stop appearing.

This boundary is also why the [403 AuthorizationFailure](/2022/08/01/fix-storage-403-authorization-error/) gets confused into the same bucket by teams that catch every Storage exception in one place: a 403 is an access decision, a 409 is a state conflict, and a 412 is a precondition failure, and collapsing all three into a generic retry is how a permissions problem, a concurrency problem, and a coordination problem all get the same wrong fix. Separate the status codes, read the error code, and each lands in the handler that can actually resolve it.

## Building retry logic that respects the conflict-is-state rule

Retry policy for Storage 409s is not "retry or do not retry"; it is "retry the families where waiting changes the state, do not retry the families where it cannot, and back off in both directions." The conflict-is-state rule turns directly into a routing table for the retry layer, and the routing is the whole design.

`ContainerBeingDeleted` and `ContainerBeingDisabled` are the retry-with-backoff cases, because the state that holds the conflict, an in-progress lifecycle transition, will complete on its own and free the resource. These deserve an exponential or near-exponential backoff with jitter and a bounded total time, exactly the shape shown in the container-recreate example. Jitter matters when many clients hit the same transition at once, because synchronized retries arrive in a thundering herd and prolong the contention; spreading them out with a random component smooths the load.

`LeaseAlreadyPresent` is a conditional retry case. If the conflicting lease is fixed-duration, waiting out at most the lease duration may clear it, so a backoff bounded by slightly more than the maximum lease duration is reasonable. If the lease is infinite and orphaned, no amount of waiting helps and the correct action is to break the lease, not to retry. The retry layer cannot tell these apart on its own, which is why a lease conflict should escalate to a deliberate decision, breaking or coordinating, rather than disappearing into a generic retry.

`BlobAlreadyExists`, `ContainerAlreadyExists`, and `PathAlreadyExists` are the do-not-retry-as-failure cases. Retrying does not change the outcome because the resource already exists and will keep existing. For an idempotent create these are success in disguise and should be caught and treated as a no-op; for a genuine create-only requirement they are a real conflict that needs a decision about overwrite or skip. Either way, looping is wrong.

`SnapshotsPresent`, immutability conflicts, and most other blob-state conflicts are do-not-retry cases that need the request itself changed. `SnapshotsPresent` needs the delete reissued with a snapshot option; retrying the same delete reproduces the conflict every time. Immutability needs the operation abandoned until the policy clears. `PendingCopyOperation` is the partial exception, a wait-then-retry case where polling the copy status and proceeding once it completes is appropriate.

The clean implementation separates the two questions every Storage exception raises: is this retryable at all, and if so, with what delay. A retry policy that asks both questions per error code, rather than treating `409` as a single retryable class, is the difference between a layer that absorbs transient lifecycle conflicts and a layer that hangs on orphaned leases and burns cycles on permanent existence conflicts. The Azure SDKs include built-in retry policies for transient transport and server errors, but those policies deliberately do not retry 409s by default, because a 409 is a client-state conflict the SDK cannot resolve on your behalf. Any 409 retry is logic you write, and writing it per family is the point of this entire article. You can build and exercise these policies against real conflicts in a sandbox using the [hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), which is the fastest way to confirm a retry layer behaves the way the families demand before it ships.

## Preventing Azure Storage 409 conflicts by design

Every 409 family has a design that makes it rare, and the prevention is cheaper than the handling in all four cases. The conflicts are not inevitable; most of them come from code that assumed a state without expressing the assumption to the service.

Idempotent operations prevent the existence family. When the intent is "make sure this exists," use the create-if-not-exists form rather than a plain create, and the `ContainerAlreadyExists` conflict never surfaces. When the intent is "write this content," decide explicitly between overwrite and create-only and set the conditional header to match, so a `BlobAlreadyExists` either does not occur, because you overwrite, or is caught and treated as the no-op it is, because you genuinely meant create-only. Designing writes to be safely repeatable also removes the cascade where a retried message reprocesses and collides with its own earlier work.

Disciplined lease handling prevents the lease family. Acquire leases inside a try-finally so the release runs on every exit, prefer fixed-duration leases with renewal over infinite leases so a crash self-heals within the lease duration, and keep the lease ID where the cleanup path can reach it. An infinite lease is the right tool only when a deliberate, monitored process owns it and a clear operational procedure exists to break it if that process dies. Treat the infinite lease the way you treat any lock with no timeout: as a liability that needs an explicit recovery plan.

Avoiding delete-then-recreate prevents the container-lifecycle family. Clear a container's contents by deleting the blobs and keeping the container, or recreate under a fresh name, or enable container soft delete so a mistaken delete is a restore rather than a recreate. The reserved-name window is a fact of how container deletion works, and the only design that never touches it is one that does not delete and immediately recreate the same name.

Explicit state handling prevents the blob-state family. Delete blobs with the snapshot option chosen up front when snapshots are part of your data model, poll copy status before operating on copy destinations, and design retention and legal-hold workflows so that operations which would violate an immutability policy are not attempted in the first place. The blob-state conflicts are the service enforcing a state contract; the prevention is to honor that contract in the code path rather than to discover it through a 409.

Across all four families the through-line is the same: express the assumption to the service. A create-only write should carry `If-None-Match: *` so the service knows the assumption and can report cleanly when it fails; an idempotent create should use the create-if-not-exists form; a leased write should carry its lease ID; a snapshotted blob should be deleted with its snapshot option. The 409 is what happens when the assumption stays implicit and the service finds it violated. Make the assumption explicit and the conflict either does not happen or arrives as a clean, routable signal.

## Errors people mistake for an Azure Storage 409 conflict

Several Storage failures get filed under "409" in incident reports when they are nothing of the kind, and untangling them saves the debugging time that misclassification costs. The most common mistaken sibling is the `412 Precondition Failed` covered above; if your "409" is an optimistic-concurrency `If-Match` failure or a write to a leased blob without the lease ID, it is a 412, and the handler that catches 409 will never see it.

A `403` is the next most common misfile. A `403 AuthorizationFailure` or `AuthorizationPermissionMismatch` is an access decision: the credential lacked the data-action role, the SAS expired or lacked the permission, or a firewall rule blocked the source. None of that is a state conflict, and the fix lives entirely in the identity and network configuration rather than in the request body or conditional headers. The full diagnosis for that family is in the companion article on the [403 AuthorizationFailure](/2022/08/01/fix-storage-403-authorization-error/), and the quick discriminator is that a 403 fails before the service evaluates resource state at all, while a 409 fails specifically because of resource state.

A `404` after a delete is sometimes reported as a conflict because it appears in the same delete-then-access sequence that produces `ContainerBeingDeleted`. The distinction is timing and direction: `ContainerBeingDeleted` is a 409 on a create during the delete window, while a `404 ContainerNotFound` is what you get on a read or write after the delete has completed and the container is genuinely gone. The same operation sequence can produce a 409 early and a 404 late, and reading the status code tells you which side of the deletion you are on.

A `500` or `503` is a server-side or throttling condition, not a conflict. `ServerBusy` under throttling returns 503 and is the case the built-in SDK retry policies handle automatically with backoff, exactly the opposite of a 409, which those policies leave to you. Misreading a throttle as a conflict leads to writing custom 409 handling that never fires while the real 503s sail through unaddressed. The status code is the first discriminator every time: 403 is access, 404 is absence, 409 is state conflict, 412 is precondition, 429 and 503 are throttling, and routing on the status code before anything else keeps each in its own lane.

## The lease state machine behind the lease conflicts

The lease conflicts make far more sense once you can see the state machine they come from, because each 409 lease code maps to a transition the service refused. A lease moves a blob or container through five states, and the conflict you receive depends on which state the resource is in when your operation arrives. Holding the machine in your head turns "why did this lease call fail" into "the resource was in this state, so that transition was illegal."

A resource with no lease is in the `available` state. Acquiring a lease moves it to `leased`, where it stays as long as the holder renews a fixed-duration lease or until an infinite lease is released. A fixed-duration lease that the holder stops renewing transitions to `expired` when its duration elapses; the lease is gone for practical purposes, though the state reads `expired` until someone acquires again or changes the lease. Breaking a lease moves it to `breaking` for the duration of the break period, then to `broken`, after which a new acquisition can take it back to `leased`. Releasing a lease returns the resource straight to `available`.

Each 409 names a transition the current state forbids. `LeaseAlreadyPresent` is an acquire attempted while the state is `leased`; the machine does not allow a second simultaneous lease. `LeaseNotPresentWithLeaseOperation` is a renew, change, or release attempted while the state is `available` or `expired`; there is no lease to operate on. `LeaseIdMismatchWithLeaseOperation` is a management call whose lease ID does not match the one the `leased` state currently records, which happens when the lease expired and a different caller reacquired it, minting a new ID. `LeaseAlreadyBroken` is a break attempted on a resource already in `broken`. Reading the state with the blob's lease properties before acting tells you which transition is legal, which is why the `properties.lease` query is the first move on any lease conflict.

The practical upshot is a rule for choosing lease durations. A fixed-duration lease auto-transitions from `leased` to `expired` when renewal stops, so it self-heals after a crash within at most the lease duration, and a `LeaseAlreadyPresent` from it is bounded in how long it can persist. An infinite lease never makes that transition on its own, so a crash in the `leased` state is permanent until a deliberate break. Choosing fixed duration with renewal over infinite is the design that keeps lease conflicts transient rather than terminal, and reserving infinite leases for monitored owners with a documented break path is what keeps the rare orphaned-lease incident recoverable rather than mysterious.

## 409 conflicts beyond blobs: queues, tables, and file shares

The blob service produces the most-searched 409s, but the queue, table, and file services raise their own conflicts on the same state principle, and they trip up engineers precisely because the codes differ while the families stay the same. Recognizing the parallel lets you apply the routing you already learned to services you touch less often.

### What 409s does the Queue service produce?

The Queue service raises existence and lifecycle conflicts that mirror the container family exactly. Creating a queue that already exists returns `409 QueueAlreadyExists`, the queue equivalent of `ContainerAlreadyExists`, and the fix is the create-if-not-exists form. Creating a queue whose delete has not finished returns `409 QueueBeingDeleted`, the direct analog of `ContainerBeingDeleted`, with the same reserved-name window and the same correct handling: back off until the name frees, or avoid delete-then-recreate of the same queue name. A queue that an administrator has disabled returns `409 QueueDisabled` on operations against it, which is not transient and resolves only when the queue is re-enabled at the account level. The lesson carries over without change: route on the error code, treat the existence conflict as a create-if-not-exists, and back off on the lifecycle conflict.

```python
from azure.core.exceptions import ResourceExistsError, HttpResponseError

try:
    queue_service.create_queue("work-items")
except ResourceExistsError:
    # 409 QueueAlreadyExists; idempotent intent, treat as success
    pass
except HttpResponseError as ex:
    if ex.status_code == 409 and ex.error_code == "QueueBeingDeleted":
        wait_then_recreate("work-items")
    else:
        raise
```

### How does the Table service split 409 from 412?

The Table service draws the same 409-versus-412 line that blobs do, and seeing it there cements the rule. Inserting an entity whose partition key and row key already exist returns `409 EntityAlreadyExists`, an existence conflict identical in spirit to `BlobAlreadyExists`; the insert collided with an entity that is already present. Creating a table that exists returns `409 TableAlreadyExists`, and operating on a table mid-delete returns `409 TableBeingDeleted`, both lifecycle and existence analogs of the blob and container codes.

The optimistic-concurrency side, though, lands on 412 exactly as it does for blobs. A merge, update, or delete that carries an `If-Match` ETag which no longer matches the entity returns `412` with `UpdateConditionNotSatisfied`, not 409. So the Table pattern is the blob pattern in miniature: a create collision is a 409 `EntityAlreadyExists`, and a read-modify-write collision is a 412 `UpdateConditionNotSatisfied`. An application that wants insert-or-replace semantics should use the upsert operation, which sidesteps both by neither failing on an existing entity nor requiring an ETag, and an application that wants strict optimistic concurrency should keep the ETag and handle the 412. Routing an `EntityAlreadyExists` into the same handler as an `UpdateConditionNotSatisfied` repeats the blob mistake one layer over.

### What 409s appear in Azure Files?

The file service adds conflicts that the object services do not have, because Azure Files exposes SMB and NFS semantics where multiple clients open and lock files concurrently. Creating a share that exists returns `409 ShareAlreadyExists`, and a share mid-delete returns `409 ShareBeingDeleted`, the familiar existence and lifecycle pair. Beyond those, the file protocols introduce sharing and locking conflicts that have no blob equivalent. An SMB sharing violation, where one client opens a file with a sharing mode that denies the access another client requests, surfaces as a 409 sharing-violation condition. A byte-range lock conflict, where one handle holds a lock on a region another handle tries to write, surfaces as a 409 lock conflict. These are genuine concurrency conflicts arising from the file-sharing model rather than from create-only writes, and the handling is to coordinate access, retry after the conflicting handle releases its lock or closes, or open with a sharing mode that permits the intended concurrency. The state principle still holds: the file is in a state, an open handle with a lock or a restrictive sharing mode, that conflicts with your request, and the resolution is to change the access pattern rather than to retry blindly into the same lock.

## Data Lake Storage Gen2: path, rename, and filesystem conflicts

Data Lake Storage Gen2 layers a hierarchical namespace over blob storage, and that namespace introduces conflict codes the flat object model never produces, because directories, renames, and a filesystem object all become real operations that can collide with state. Teams running analytics workloads on Gen2 hit these often enough that they deserve their own treatment.

The filesystem, which is the Gen2 name for what blob storage calls a container, produces the same existence and lifecycle conflicts under Gen2 codes: `FilesystemAlreadyExists` on a create that collides, and `FilesystemBeingDeleted` on a create during the delete window. The handling matches the container family precisely, create-if-not-exists for the existence case and bounded backoff for the lifecycle case.

Paths are where Gen2 diverges. Because a directory is a first-class object rather than a virtual prefix, creating a file or directory at an occupied path returns `409 PathAlreadyExists`, and the conflict can appear on directory creation in ways flat storage cannot reproduce, for example when two parallel jobs both attempt to materialize the same directory tree before either has finished. Renames, which Gen2 supports as an atomic operation rather than the copy-then-delete that flat blob storage requires, add their own conflicts: a rename whose source is mid-delete or whose destination is mid-delete returns a being-deleted conflict, and the resolution is to wait out the in-progress operation before retrying the rename. Gen2 paths also support leases, so the entire lease family, `LeaseAlreadyPresent` and the mismatch and not-present management conflicts, applies to paths exactly as it does to blobs, and the lease state machine described above governs them identically.

```bash
# Create a Gen2 directory idempotently, tolerating the existence conflict
az storage fs directory create \
  --name raw/2022/08/08 \
  --file-system mydata \
  --account-name myaccount --auth-mode login || true
```

The broader point for Gen2 is that the hierarchical namespace makes more operations stateful than the flat model does, so more of them can conflict. The same four families still describe every 409, but the surface area is larger, and a workload that creates directory trees, renames paths, and takes path leases needs the routing logic applied across all of those operations rather than only on blob writes.

## Reading a 409 across the language SDKs

The error-code-first routing principle holds in every Azure SDK, but the exact type and property names differ, and knowing the shape in each language removes the friction of translating the pattern at the moment you need it. The constant across all of them is that a typed exception carries both the numeric status and the string error code, and your handler branches on the error code.

In Java, the `azure-storage-blob` library raises `BlobStorageException`, with `getStatusCode()` returning 409 and `getErrorCode()` returning a `BlobErrorCode` enum value:

```java
import com.azure.storage.blob.models.BlobStorageException;
import com.azure.storage.blob.models.BlobErrorCode;

try {
    blobClient.upload(data, false); // overwrite = false, create-only
} catch (BlobStorageException ex) {
    if (ex.getStatusCode() == 409) {
        BlobErrorCode code = ex.getErrorCode();
        if (code == BlobErrorCode.BLOB_ALREADY_EXISTS) {
            // idempotent create: another writer won, treat as success
        } else if (code == BlobErrorCode.LEASE_ALREADY_PRESENT) {
            // coordinate or break, do not retry
        } else {
            throw ex;
        }
    } else {
        throw ex;
    }
}
```

In Node.js, the `@azure/storage-blob` package throws a `RestError` whose `statusCode` is 409 and whose `code` carries the error string:

```javascript
const { RestError } = require("@azure/storage-blob");
try {
  await blockBlobClient.upload(content, content.length, {
    conditions: { ifNoneMatch: "*" } // create-only
  });
} catch (err) {
  if (err instanceof RestError && err.statusCode === 409) {
    if (err.code === "BlobAlreadyExists") {
      // create-only collision; idempotent intent means this is success
    } else if (err.code === "ContainerBeingDeleted") {
      // back off and retry until the name frees
    } else {
      throw err;
    }
  } else {
    throw err;
  }
}
```

In Go, the `azblob` package exposes a helper that tests an error for a specific code rather than a typed exception, which reads cleanly:

```go
import "github.com/Azure/azure-sdk-for-go/sdk/storage/azblob/bloberror"

_, err := client.UploadStream(ctx, containerName, blobName, body, nil)
if bloberror.HasCode(err, bloberror.BlobAlreadyExists) {
    // idempotent create: the blob already exists, proceed
} else if bloberror.HasCode(err, bloberror.ContainerBeingDeleted) {
    // back off and retry
} else if err != nil {
    return err
}
```

In PowerShell, the `Az.Storage` cmdlets surface the underlying conflict as a terminating error you can trap, and inspecting the message or the inner exception's error code routes the same way. The pattern in every language is identical in spirit even though the syntax differs: catch the conflict, read the error code, and branch on the family. Writing a single helper that maps the language-specific error code to a family enum, then routing on the family, keeps the conflict logic in one place and out of every call site, and it is the cleanest way to keep the four-family rule consistent across a codebase.

## Three incident walkthroughs

Seeing the diagnosis run end to end on realistic incidents ties the families to the work of actually fixing a 409 in production. Each walkthrough below follows the same path: the symptom, the signal that named the cause, and the fix that matched the family.

The first incident is a queue-triggered function that began throwing `BlobAlreadyExists` under load. The function wrote a result blob named after the message ID, and the writes used a create-only overload. Under normal traffic the function processed each message once and the blob did not exist yet, so the create-only write succeeded. Under load, the platform's at-least-once delivery occasionally delivered the same message to two function instances, both computed the same blob name, and the second to arrive received `409 BlobAlreadyExists`. The signal that named it was the `StorageBlobLogs` query showing `PutBlob` with `StatusText` of `BlobAlreadyExists` clustered during traffic spikes, correlated with duplicate message IDs in the function logs. The fix was not a retry; it was recognizing that the function's intent was idempotent, since the same message always produces the same result, so the second write reaching `BlobAlreadyExists` had nothing to do. Catching the conflict and treating it as a successful no-op turned a stream of errors into expected, harmless duplicates.

The second incident is a nightly job that deleted and recreated a staging container, which began hanging intermittently. The job deleted the container, then immediately created it under the same name, and on nights when the container held a large volume of data the delete window stretched long enough that the recreate hit `409 ContainerBeingDeleted`. The job's retry was a tight loop with no delay, so it spun through the recreate hundreds of times inside the delete window, pinning a thread and looking, from the outside, like a deadlock. The signal was the log query showing `CreateContainer` with `ContainerBeingDeleted` repeating thousands of times in a few seconds. The immediate fix was a bounded backoff with a deadline, which let the recreate wait out the delete instead of hammering it. The durable fix was changing the job to clear the container's contents with a batch delete and keep the container, removing the lifecycle conflict entirely because the container never entered the deleting state.

The third incident is a coordinator process that stopped being able to write to a control blob, with every write failing. The writes carried no lease ID, so they returned `412 LeaseIdMissing`, which the on-call engineer initially filed as a 409 lease problem and tried to fix by breaking a lease that the blob's properties showed did not exist in the way expected. Reading the properties told the real story: the blob was in the `leased` state with an `infinite` duration, held by a coordinator instance that had crashed days earlier without releasing. The writes failed with 412 because they violated the lease condition, not with 409, which is why the lease-conflict handler never fired. The fix had two parts. First, break the orphaned infinite lease so the blob returned to a writable state. Second, change the coordinator to take a fixed-duration lease with renewal instead of an infinite one, so a future crash would self-heal within the lease duration rather than locking the blob until a human intervened. The incident is the 409-versus-412 boundary in concrete form: the visible error was a 412, the root cause was an orphaned lease, and the fix touched both the immediate lock and the design that created it.

## Confirming the cause: a diagnostic order that never guesses

When a 409 lands and you do not yet know which family it belongs to, a fixed order of inspection gets you to the cause without theorizing, and following the same order every time builds the reflex that makes these incidents quick. The order moves from the cheapest signal to the most specific, and it stops the moment the cause is named.

Read the `x-ms-error-code` header first, because it names the cause in one field and ends the investigation for most incidents. If you are looking at an SDK exception rather than a raw response, read the equivalent error-code property. With the code in hand, map it to a family using the reference table earlier in this article, and the family dictates the action. Only when the code alone leaves a question, for example whether a `LeaseAlreadyPresent` comes from a fixed or an infinite lease, do you reach for the second signal, which is the resource's own state. For lease questions that means the blob's lease properties; for copy questions it means the copy status; for container questions it means whether a delete is in flight. The third signal, used only when you need to trace a specific request through the platform, is the request identifier pair: the `x-ms-request-id` the service assigned and the `x-ms-client-request-id` you set on the way out.

The confirmation recipes differ by family and each is a single command. For an existence conflict, list or show the resource to verify it is present, which confirms the create-only write or the create call hit something already there. For a lease conflict, query the blob's lease properties and read the state and duration. For a container-lifecycle conflict, attempt a show on the container and watch for the transition from being-deleted to not-found to recreatable. For a blob-state conflict, read the blob's properties and look for snapshots, a pending copy status, or an immutability policy.

```bash
# Existence: is the resource actually there?
az storage blob exists --name myblob --container-name mycontainer \
  --account-name myaccount --auth-mode login

# Blob state: snapshots, copy status, immutability in one look
az storage blob show --name myblob --container-name mycontainer \
  --account-name myaccount --auth-mode login \
  --query "{copy:properties.copy.status, lease:properties.lease, blobType:properties.blobType}"
```

The discipline of reading the code before acting is worth restating because it is the habit that separates a quick fix from a long one. A glance at one header settles which of four families you face; an hour of guessing settles nothing and often lands on the wrong fix, because two families can produce the same status on the same line of code. The order is the whole method: header, then state, then request identifiers, stopping as soon as the cause is named.

## The cost of getting 409 handling wrong

Misrouting a 409 is not a cosmetic problem; it costs throughput, latency, money, and incident time in ways that compound under exactly the conditions where the conflicts appear, which is load. Seeing the cost makes the case for routing by family rather than retrying everything.

A tight retry on a non-clearing conflict burns compute for no result. A loop that retries `ContainerBeingDeleted` with no delay can issue thousands of requests in the seconds a large delete takes, and every one of those requests consumes a connection, a transaction against the account, and a slice of the worker's CPU, while the outcome is identical to having waited. In a serverless function billed by execution time, that loop runs up the bill directly, because the function is awake and spinning rather than completing. The same loop against an orphaned infinite lease never terminates on its own, so it either runs until a timeout kills the worker or, in the worst case, holds a thread until the process is restarted. The difference between a bounded backoff and a tight loop here is the difference between a brief pause and a pinned worker.

Misrouting also lengthens incidents by sending the on-call engineer to the wrong fix. A 412 read as a 409 leads to breaking leases that are not the problem; a 403 read as a 409 leads to inspecting request bodies when the fix is in the role assignment; a throttling 503 read as a conflict leads to writing handling that never fires while the real throttle goes unaddressed. Each misread adds a cycle of investigation that the error code would have skipped. The throughput cost shows up too: under concurrency, a create-only write that should treat `BlobAlreadyExists` as an idempotent no-op instead surfaces it as an error, which can fail a whole batch when one duplicate would have been harmless, forcing a reprocess of work that already completed.

The measured version of the argument is simple to reason about even without a benchmark. Replacing a tight retry with a bounded backoff that starts at a few seconds and caps low cuts the request count against the account from thousands to a handful for the same lifecycle conflict, which reduces both the transaction charges and the contention that prolongs the delete window for everyone hitting it. Treating an idempotent-create conflict as success rather than failure removes an entire class of false alarms from the error budget. Neither change adds latency in the common case, because the common case is no conflict at all; both changes only alter what happens on the conflict, which is exactly where the cost lives. The handling pattern that respects the families is cheaper on every axis than the blanket retry it replaces.

## Where 409 conflicts hide in higher-level tools

The conflict families do not only appear in code you wrote against the SDK; they surface through the higher-level tools that sit on top of Storage, and recognizing them there saves the confusion of a 409 that seems to come from nowhere. The tool hides the REST call, but the conflict underneath is one of the same four families.

Infrastructure-as-code deployments are a frequent source. A Bicep or ARM or Terraform run that deletes a container or a storage resource and recreates it in the same deployment can hit the being-deleted lifecycle conflict when the recreate races the asynchronous delete, and the deployment reports a 409 that looks like a platform glitch. The fix is the same as in code: avoid delete-then-recreate of the same name in a single run, or sequence the operations so the delete completes before the create begins, or use a fresh name. Redeployments that reuse a recently torn-down name are the usual trigger, and the resource-graph nature of the templates can obscure the ordering that creates the race.

Bulk copy tools surface the existence family. AzCopy, copying into a destination that already holds objects, applies an overwrite policy, and depending on that policy a collision either overwrites, skips, or prompts; the underlying behavior is the create-only-versus-overwrite decision expressed as a tool option rather than a conditional header. Choosing the overwrite policy deliberately is the tool-level equivalent of deciding overwrite versus create-only in code, and a copy job that fails or skips unexpectedly on existing objects is usually a policy set to the conservative default. Storage Explorer and the portal hide the same decision behind a confirmation prompt when you upload over an existing blob.

Function and trigger bindings hide lease conflicts. Several Azure features take leases on blobs to coordinate single ownership, and a feature that competes for the same blob, or a stale owner that crashed holding a lease, produces the lease family through a binding rather than an explicit acquire call. When a trigger stops firing or a coordinator stops advancing and the storage logs show lease activity, the diagnosis runs exactly as it does for an explicit lease: read the blob's lease state, identify whether the holder is alive, and break an orphaned lock if one is the cause. The tool changed the call site, not the conflict. Reproducing these tool-level conflicts in a controlled setting, where you can trigger a redeploy race or a stale owner on purpose, is straightforward in the [hands-on Azure labs on VaultBook](https://vaultbook.org/tools/azure-labs.html), and seeing the same four families appear through a template or a binding is what makes the pattern portable across every layer of the stack.

## Reasoning about 409s on geo-replicated and read-access accounts

Geo-replication and read-access secondary endpoints add a layer that confuses 409 reasoning until you fix one fact in place: a 409 always reflects the state of the primary region, because writes only ever go to the primary, and the conflict is the primary's current state disagreeing with your request. Replication topology does not create new conflict families, and understanding why removes a recurring source of misattribution.

A read-access geo-redundant account exposes a secondary endpoint you can read from, reached by appending a secondary suffix to the account name in the host. That secondary is read-only by design. You cannot write to it, so it cannot produce a state conflict on a write; an attempt to write to the secondary endpoint fails because the endpoint does not accept writes, which is a different failure from a 409 and should be read as such. Every create, lease, delete, and conditional write that can return a 409 targets the primary, and the primary's state is what the conflict describes.

The genuine trap is a stale ETag captured from the secondary. Because the secondary lags the primary by the geo-replication delay, a value read from the secondary can be older than the primary's current value. Capture an ETag from a secondary read, modify, and write back to the primary with an `If-Match`, and the precondition can fail because the primary has moved on since the secondary's snapshot. That failure is a `412 Precondition Failed`, not a 409, which keeps it firmly on the precondition side of the boundary this article has drawn throughout: optimistic-concurrency mismatches are 412s regardless of which endpoint you read from. The fix is to capture the ETag for a read-modify-write from a primary read, or to treat the 412 as the signal to re-read from the primary and retry the merge against current state. The last-sync-time property on a read-access account tells you how far the secondary trails, which is the value to check when reasoning about how stale a secondary read might be.

Geo-failover changes which physical region serves as primary, but it does not change any of this. After a failover the new primary is authoritative, writes go there, and 409s describe its state exactly as before. The mental model survives the topology unchanged: writes and their conflicts live on the primary, the secondary is a read-only, slightly delayed view, and the only cross-endpoint subtlety is that an ETag is only as current as the endpoint it came from. None of the four conflict families is specific to replication, and none of them behaves differently because an account is geo-redundant. The 409 is the primary's state talking, and that is true whether the account is locally redundant or replicated across regions.

## Verdict

An Azure Storage 409 conflict error is a decision the service handed back to you, not a failure to suppress, and the decision has four shapes. An existence conflict wants you to choose overwrite or treat the collision as an idempotent no-op. A lease conflict wants you to wait for expiry, use the right lease ID, or break an orphaned lock, and it never wants a blind retry. A container-lifecycle conflict wants a bounded backoff while a delete finishes, and better still a design that never recreates a name it just deleted. A blob-state conflict wants the request itself changed, a snapshot option supplied, a copy awaited, an immutability policy respected. The conflict-is-state rule ties them together: a 409 means the resource state changed under your request, so the fix is to match the handling to the conflict type, read from the `x-ms-error-code` header, and never to loop on a state that retrying cannot change. Get the status code, read the error code, route on the family, and the recurring 409 incident becomes a one-time fix that also tells you what design change retires it for good. The single most valuable habit to leave with is reading the error code before forming any theory, because the header settles in one glance what an hour of guessing cannot.

## Frequently asked questions

### Q: What does a 409 conflict error mean on Azure Storage?

A 409 conflict means your request reached Azure Storage successfully and was rejected because it disagrees with the current state of the target resource. The credentials were valid and the network path was open; the service compared what you asked for against the present state of the blob, container, or path and found a contradiction it will not resolve silently. The exact reason is in the `x-ms-error-code` response header, which names whether the conflict is an existence collision such as `BlobAlreadyExists`, a lease conflict such as `LeaseAlreadyPresent`, a container-lifecycle conflict such as `ContainerBeingDeleted`, or a blob-state conflict such as `SnapshotsPresent`. The status code alone tells you a state conflict occurred; only the error code tells you which conflict and therefore which fix applies, so reading that header is always the first diagnostic step.

### Q: Can a blob lease cause a 409 conflict?

Yes, but only on lease-management operations, and the distinction matters. Calling Acquire Lease on a blob that already has an active lease returns `409 LeaseAlreadyPresent`. Renewing, changing, or releasing a lease with a lease ID that no longer matches returns `409 LeaseIdMismatchWithLeaseOperation`, and doing so when no lease exists returns `409 LeaseNotPresentWithLeaseOperation`. What does not return 409 is a data operation against a leased blob: writing without supplying the lease ID returns `412 Precondition Failed` with `LeaseIdMissing`, and supplying the wrong ID returns `412 LeaseIdMismatchWithBlobOperation`. The clean rule is that conflicts on managing the lease are 409s, while conflicts on writing to a leased blob are 412s. Confusing the two sends both into the wrong handler, which is a frequent cause of leases that appear to fail mysteriously.

### Q: Why do I get BlobAlreadyExists on a create?

`BlobAlreadyExists` appears when a create-only write hits a blob that already exists. A write carrying `If-None-Match: *` instructs the service to succeed only if no blob occupies that name, so when one does, the precondition fails and the service returns `409 BlobAlreadyExists`. Many SDK upload overloads default to create-only behavior, which is why the error often surprises developers who expected an overwrite. The fix depends on intent. If you meant to overwrite, drop the create-only condition or pass the overwrite option, for example `UploadAsync(stream, overwrite: true)` in .NET. If you genuinely meant create-only and two workers raced, exactly one wins and the other gets the 409; for an idempotent create that loser should treat the conflict as success, because the blob now exists with the intended content. Retrying the create-only write changes nothing.

### Q: Do concurrent writes cause 409 ETag conflicts?

Concurrent writes cause conflicts, but on the update path they surface as `412 Precondition Failed`, not 409. The optimistic-concurrency pattern reads a blob, captures its ETag, and writes back with `If-Match: <etag>` so the write succeeds only if no one changed the blob in between; when someone did, the ETag no longer matches and the service returns 412. The 409 form of an ETag conflict is specifically the create-only case, `If-None-Match: *` returning `409 BlobAlreadyExists` when the blob exists. So the same ETag mechanism produces a 412 on a mid-air update collision and a 409 on a create-only collision. The fix for the 412 is to re-read the blob, capture the fresh ETag, reapply your change to the current content, and write again; the fix for the create-only 409 is to decide overwrite or treat the collision as an idempotent no-op.

### Q: Why a 409 ContainerBeingDeleted right after delete?

Container deletion is asynchronous. The delete call returns success immediately, but the storage backend continues removing the container and its blobs, and during that window the container name is reserved and cannot be reused. Creating a container with the same name while the delete is in progress returns `409 ContainerBeingDeleted`. The delete window length depends on how much data the container held, so a container with many blobs can stay reserved noticeably longer than an empty one. The correct response is to back off with an increasing delay and a bounded total time until the name frees, never a tight retry loop, because a tight loop keeps arriving inside the delete window and conflicts repeatedly. The better fix is a design that avoids delete-then-recreate entirely: clear the container's contents instead of deleting it, recreate under a fresh name, or use container soft delete to restore rather than recreate.

### Q: How should an application handle a storage 409?

Route on the error code, not the status code. Catch the conflict, read `x-ms-error-code` or the SDK's `ErrorCode` property, and branch by family. Treat existence conflicts such as `BlobAlreadyExists` as an overwrite-or-skip decision, and for idempotent creates accept them as a no-op. Escalate lease conflicts such as `LeaseAlreadyPresent` to a deliberate wait, coordinate, or break, rather than a retry. Apply a bounded exponential backoff with jitter to `ContainerBeingDeleted`. Change the request itself for blob-state conflicts: supply a snapshot option for `SnapshotsPresent`, await or abort a copy for `PendingCopyOperation`, and respect immutability conflicts rather than working around them. The anti-pattern that causes most recurring incidents is catching a generic `409` and retrying every subtype the same way, which spins forever on orphaned leases and permanent existence conflicts while doing nothing useful.

### Q: Is a 409 conflict ever a transient error I can retry?

Only the container-lifecycle subtypes are genuinely transient. `ContainerBeingDeleted` and `ContainerBeingDisabled` clear on their own once the in-progress transition completes, so a bounded backoff is appropriate and will eventually succeed. A fixed-duration lease conflict is conditionally transient, because the lease auto-expires within its duration, but an infinite-lease conflict is not transient at all and needs a break instead of a retry. Existence conflicts such as `BlobAlreadyExists` and `ContainerAlreadyExists` are not transient; the resource exists and will keep existing, so retrying never changes the outcome. Blob-state conflicts such as `SnapshotsPresent` and immutability are not transient either; they need the request changed or the operation abandoned. The discriminator is whether waiting changes the state. If the conflicting state is an in-progress operation, waiting helps; if it is a stable property or another holder's lock, it does not.

### Q: How do I find which storage operations are returning 409s?

Route the storage account's data-plane diagnostic logs to a Log Analytics workspace, then query the `StorageBlobLogs` table for `StatusCode == 409`, grouping by `OperationName` and `StatusText`. The `StatusText` column carries the same error code string as the response header, so a result showing `PutBlob` with `BlobAlreadyExists` points at create-only writes colliding with existing blobs, while `CreateContainer` with `ContainerBeingDeleted` points at code recreating containers too quickly after deleting them. Data-plane logging is not enabled by default, so confirm the diagnostic setting exists before relying on it; without it, the only record of a 409 is whatever your application captured. In real time, set an `x-ms-client-request-id` on conflict-prone writes so you can correlate the failure in your own logs with the platform's `x-ms-request-id`, which turns a vague timestamp into a traceable request.

### Q: What is the difference between a 409 and a 412 in Azure Storage?

A 409 Conflict means the request conflicts with the resource state in a way the service will not resolve, typically an existence conflict or a lock-management conflict. A 412 Precondition Failed means a conditional header you sent evaluated to false against the current state, typically an `If-Match` ETag check on an update or a lease condition on a data operation. The shared theme is "the state is not what you assumed," but the source differs: 409 comes from creating, acquiring, or releasing; 412 comes from your conditional headers on a data operation. Optimistic-concurrency update collisions are 412s; create-only collisions are 409s. Writing to a leased blob without the lease ID is a 412; acquiring a lease that already exists is a 409. Build two handlers, route on the status code first and the error code second, and the phantom-409 incidents that are really 412s stop appearing.

### Q: How do I delete a blob that returns SnapshotsPresent?

`SnapshotsPresent` is a 409 returned when you try to delete a base blob that still has point-in-time snapshots without telling the service what to do with them. Deleting the base blob would orphan its snapshots, which the service refuses to do implicitly. Reissue the delete with an explicit snapshot option: from the CLI, `az storage blob delete --delete-snapshots include` removes the base blob and its snapshots together, and `--delete-snapshots only` keeps the base blob while clearing its snapshots. In the SDKs the same choice is an enum, `DeleteSnapshotsOption.IncludeSnapshots` or `DeleteSnapshotsOption.OnlySnapshots`. The common misdiagnosis is assuming the blob is leased or locked when the `x-ms-error-code` header reading `SnapshotsPresent` makes the cause unambiguous, which is one more reason to read the header before forming a theory.

### Q: Can an orphaned lease lock a blob permanently?

An infinite lease can, which is why fixed-duration leases are safer. A lease taken with infinite duration never expires on its own; it persists until something explicitly releases or breaks it. If the process holding an infinite lease crashes without releasing, the blob stays locked against writes and deletes from every other client, and acquire attempts return `409 LeaseAlreadyPresent` indefinitely. The recovery is to break the lease deliberately, using a break period of zero to end it at once, after confirming with the blob's lease properties that the lease is the cause and that no living process should still hold it. A fixed-duration lease between 15 and 60 seconds avoids this trap because it auto-expires if the holder stops renewing, so even a hard crash self-heals within the lease duration. Reserve infinite leases for deliberately owned, monitored resources with a documented break procedure.

### Q: Why does container creation sometimes succeed and sometimes return 409?

The same `CreateContainer` call returns different results depending on the container's state at the moment it runs. If the container does not exist, the call succeeds with `201 Created`. If the container already exists, it returns `409 ContainerAlreadyExists`. If a delete of the same name is still finishing, it returns `409 ContainerBeingDeleted`. All three are the identical line of code producing different outcomes because the resource state differs each time, which is the defining behavior of the conflict family. For setup code that should be idempotent, use the create-if-not-exists form, which treats an existing container as success and never raises the `ContainerAlreadyExists` conflict. For the `ContainerBeingDeleted` case, back off and retry until the delete completes, or avoid recreating a just-deleted name altogether.

### Q: Does the Azure SDK retry 409 conflicts automatically?

No, and that is deliberate. The built-in retry policies in the Azure SDKs retry transient transport failures and server-side conditions such as `503 ServerBusy`, applying backoff automatically, but they do not retry 409s. A 409 is a client-state conflict the SDK cannot resolve on your behalf, because the right response depends on intent the SDK does not know: whether you meant overwrite or create-only, whether a lease should be broken or waited out, whether a container should be recreated or left alone. Any 409 retry is logic you must write, and writing it per family is the correct approach, because the families need opposite handling. Relying on the default policy to absorb 409s leaves every conflict unhandled; relying on a custom blanket 409 retry spins on the subtypes that retrying cannot fix. Route by error code instead.

### Q: What causes PathAlreadyExists in Data Lake Storage Gen2?

`PathAlreadyExists` is the existence conflict in the hierarchical namespace of Data Lake Storage Gen2, where files and directories are first-class objects rather than the virtual prefixes of flat blob storage. Creating a file or directory at a path that already holds one returns this 409. Because Gen2 directories are real objects, you can hit the conflict on directory creation in ways that flat storage never produces, for example when two jobs both attempt to create the same directory tree. The handling mirrors the flat-storage existence family: decide whether you meant create-only or overwrite, branch to an update or append path when the object already exists, and for idempotent directory creation treat the conflict as a no-op rather than a failure. As with blob existence conflicts, the create-if-not-exists pattern removes the surprise entirely when the intent is simply to ensure the path exists.

### Q: How do I confirm a 409 is a lease problem before changing anything?

Read the blob's lease properties first. The `az storage blob show` command with a query of `properties.lease` returns the lease `status`, `state`, and `duration`, and these three values confirm whether a lease is the cause and what kind. A `state` of `leased` means an active lease is present, a `status` of `locked` confirms it blocks conflicting operations, and a `duration` of `infinite` versus a fixed value tells you whether the lease will expire on its own. If the state is `leased` and `infinite` and no living process should hold it, you have the orphaned-infinite-lease fingerprint and breaking is the resolution. If the duration is fixed, waiting out the duration may clear it without intervention. Checking the properties before breaking or retrying prevents the mistake of breaking a lease that a legitimate process still holds.

### Q: Should I retry a 409 with exponential backoff?

Only for the families where waiting changes the state, which means the container-lifecycle subtypes `ContainerBeingDeleted` and `ContainerBeingDisabled`. For those, an exponential or near-exponential backoff with jitter and a bounded total time is the right pattern, because the in-progress transition completes on its own and frees the resource; the jitter prevents many clients from retrying in lockstep and prolonging the contention, and the bound prevents a transient conflict from becoming a stuck worker. For existence conflicts, lease conflicts, and blob-state conflicts, backoff is the wrong tool: the resource already exists, the lock is held by someone your retries cannot influence, or the request itself must change. Applying exponential backoff uniformly to every 409 wastes cycles on permanent conflicts and hides the orphaned-lease case that needs a break rather than a wait. Decide retryability per error code first, then choose the delay.

### Q: Can a pending copy operation cause a 409 conflict?

Yes. When you start an asynchronous server-side copy into a destination blob, that blob has a copy in flight, and certain operations against it while the copy is pending return `409 PendingCopyOperation`. The confirming signal is the destination blob's copy status, which reads `pending` while the copy runs; you can read it from the blob's properties. There are two valid resolutions. Wait for the copy to finish by polling its status and proceed once it reports `success`, which suits cases where the copy is expected and short. Or abort the in-flight copy explicitly with an abort-copy call before doing what you intended, which suits cases where the copy is stale or no longer needed. Retrying the conflicting operation without addressing the copy reproduces the 409 each time, so check the copy status first and choose wait or abort based on whether the copy should complete.

### Q: Why does immutability cause a 409 and how do I handle it?

A blob protected by a time-based retention policy or a legal hold cannot be modified or deleted until the retention window elapses or the hold is removed, and an attempt returns a 409 indicating the blob is immutable due to policy. Unlike the other families, this conflict is intentional and protective: immutability exists to guarantee that records cannot be altered or removed during a compliance period, so the 409 is the feature working as designed rather than an error to route around. The only legitimate handling is to respect it. Wait out the retention period for a time-based policy, or have an authorized principal clear the legal hold through the proper governance process for a hold. Retrying, attempting to break the protection, or engineering a workaround defeats the guarantee the policy exists to provide, and in regulated environments doing so can be a compliance violation rather than merely a failed request.

### Q: How do I tell a 409 apart from a 403 or a 404 in storage logs?

Route on the status code first, because each code marks a different stage of request processing. A `403` is an access decision made before the service evaluates resource state: the credential lacked the role, the SAS was invalid, or a firewall blocked the source. A `409` is a state conflict the service raises after access succeeds but the request disagrees with the resource's current state. A `404` is absence: the container or blob the request targeted does not exist, which is what a read or write returns after a delete completes, distinct from the `409 ContainerBeingDeleted` that the same name returns during the delete window. In `StorageBlobLogs`, the `StatusCode` column separates these cleanly, and the `StatusText` column names the specific error within each. The quick mental model is 403 for access, 404 for absence, 409 for state conflict, with the error code settling the exact cause in every case.
