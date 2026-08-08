---
layout: post
title: "Set Up Storage Lifecycle Management"
page_title: "Storage Lifecycle Management in Azure: Configure Lifecycle Rules to Tier and Auto-Delete Blobs by Age Without Losing Needed Data"
date: 2023-06-26
categories: ["Technology"]
tags: ["Azure", "Storage", "Blob Storage", "Cost Management", "Configuration", "Cloud Computing"]
excerpt: "Storage lifecycle management lets you tier and auto-delete blobs by age. Configure scoped rules so cost falls automatically without removing needed data."
image: "/assets/images/blog/blog-15.webp"
reading_time: 61
author: "marcus-hall"
last_updated: 2023-06-26
lang: en
---
A storage account that grows without a plan turns into a slow, expensive liability, and the fix is rarely a one-time cleanup. The durable fix is storage lifecycle management: a set of rules that tier and delete blobs by age automatically, so the bill falls on its own and stays down without anyone running a manual purge every quarter. Configure it well and an account quiets itself, moving cold data to cheaper tiers and expiring what nobody reads anymore. Configure it badly and the same feature deletes a compliance archive at three in the morning, or buries a hot dataset in archive where every read now costs hours of waiting and a rehydration fee.

That gap between the two outcomes is the whole subject of this article. The feature itself is small. The reasoning that keeps it from hurting you is not, and it is the part the documentation tends to skip.

![Configuring Azure storage lifecycle management rules to tier and delete blobs by age - Insight Crunch](/assets/images/blog/blog-15.webp)

## The Age-and-Scope Rule: What a Lifecycle Rule Actually Is

Here is the single idea that prevents most lifecycle accidents, and it is worth naming so you can hold onto it. A lifecycle definition is nothing more than an age threshold plus a scope. The threshold answers "how old does a blob have to be," and the scope answers "which blobs are we even talking about." Every action a definition takes, whether it moves a blob to a cheaper tier or deletes it outright, is just those two halves meeting: blobs inside the scope that have crossed the age threshold get the action applied. This is the age-and-scope rule for lifecycle management, and once you internalize it the whole feature stops feeling mysterious.

The reason it matters so much in practice is diagnostic. When a lifecycle definition does something you did not expect, when it moves the wrong data or deletes blobs you still needed, the cause is almost never a platform bug. The cause is almost always one of the two halves being wrong. Either the age threshold was shorter than you thought, or, far more commonly, the scope was broader than you intended because a prefix matched more containers than you pictured or a filter you assumed was applied was never there. When you treat every surprising lifecycle outcome as a scope or threshold problem first, you find the real cause quickly instead of opening a support ticket against behavior that is working exactly as configured.

This framing also tells you where to spend your attention while setting a rule up. The action itself, tier to cool or delete, is trivial to specify and hard to get wrong. The age threshold is a single number. The scope is where the danger lives, because the scope is the part you cannot fully see from the policy definition alone. A prefix of `logs/` looks tidy in the editor, but whether it matches one container's worth of blobs or twenty depends on how your account is laid out, and the policy definition does not show you that. The discipline this article teaches is to make the scope explicit and verified before you ever let a delete action run against it.

### What does a lifecycle policy entry run against?

A lifecycle definition evaluates the blobs in a storage account against an age condition and a scope, then applies a tiering or deletion action to the matches. It does not run continuously; the platform evaluates rules on a schedule and acts in a batch. The action is the easy part. The scope, set by prefixes and blob filters, is the part that decides whether the definition helps or harms.

Understanding the rule as age-plus-scope rather than as a black box changes how you build it. You stop thinking "I want to clean up old logs" and start thinking "I want to delete block blobs whose last-modified date is older than 90 days, scoped to exactly the `app-logs/` container and nothing else." The second sentence is a rule you can verify. The first is a wish that a too-broad prefix will quietly betray. Throughout the rest of this guide, every step comes back to making the scope and the threshold precise and provable, because that precision is the entire difference between a feature that saves money and a feature that causes an incident.

For the underlying model of access tiers that lifecycle rules move blobs between, the [Azure storage accounts complete guide](/2022/01/31/azure-storage-accounts-complete-guide/) lays out the hot, cool, cold, and archive tiers and what each is priced and built for; this article assumes that tier model and focuses on the rules that automate movement across it.

## What Correct Lifecycle Configuration Buys You

Before the mechanics, it helps to be concrete about the payoff, because the payoff is what justifies the care the rest of this article asks for. A storage account with no lifecycle policy keeps every blob in whatever tier it was written to, usually hot, forever. Hot storage is the most expensive per gigabyte tier precisely because it is built for frequent, low-latency access, and most data does not stay frequently accessed. Logs from six months ago, backups from last year, telemetry that nobody has queried since the incident it was captured for: all of it sits in hot storage paying hot-storage rates while delivering cold-storage value.

A correct lifecycle policy fixes this without a human in the loop. Data that has not been modified in thirty days slides to cool, where the per-gigabyte cost is lower in exchange for a small per-read transaction cost and a minimum retention period. Data untouched for ninety days can slide further to cold or archive, where storage is cheaper still. Data that has aged past any usefulness or any retention requirement gets deleted, so you stop paying to store bytes that exist only out of inertia. The savings compound month over month, and because the policy entry keeps running, the account stays optimized even as new data arrives and ages. The full economics of this, including how to measure what you are actually spending and where, belong to the dedicated treatment in [Azure storage cost optimization](/2024/11/18/azure-storage-cost-optimization/); lifecycle rules are one of the largest single levers that guide describes, and this article is the configuration half of that lever.

What breaks when the configuration is wrong is the mirror image of those benefits, and it tends to be worse than simply missing the savings. A delete rule with a prefix that is broader than you realized does not fail loudly; it succeeds at deleting data you needed, on schedule, silently, and the loss surfaces only when someone tries to read a blob that it already expired. A definition that tiers active data into archive does not error either; it succeeds, and the symptom is that a workload that used to read a blob in milliseconds now waits hours for rehydration and pays a retrieval fee per gigabyte. These are not crashes. They are correct executions of an incorrect intent, which is exactly why the age-and-scope discipline matters: the platform will faithfully do what you told it, so the safety has to live in what you tell it.
## Prerequisites and the Correct Order of Operations

Lifecycle management is not a feature you bolt on in isolation; it depends on a few things being true about the account first, and getting the order right saves you from rules that silently do less than you expect. The first prerequisite is the account kind. Lifecycle management policies apply to general-purpose v2 accounts and to premium block blob accounts, and the richest set of tier actions, the ones that reach cool, cold, and archive, depend on the account supporting those tiers. A legacy general-purpose v1 account does not participate in the same way, and the first move when an account predates the v2 era is to confirm or upgrade the kind rather than to start authoring rules that will not have anywhere to move blobs.

The second prerequisite concerns what you intend to track. By default a lifecycle definition reasons about a blob's last-modified time, which the platform always records. If you want rules that react to the last time a blob was read rather than written, you must turn on access tracking at the account level first, because last-access time is not recorded unless you enable it. Authoring a last-access rule against an account that never started tracking access produces an entry that has no data to act on, and the symptom is a definition that simply never moves anything. Enabling access tracking before writing those rules is the order that avoids the confusion.

The third prerequisite is knowing your data layout well enough to write a scope you can defend. This is less a toggle than a piece of homework, and it is the one teams skip. Before you write a single prefix, you should be able to state which containers hold which classes of data and which prefixes inside them correspond to which workloads. A policy entry's prefix is matched against the blob path starting at the container name, so a prefix is only as safe as your certainty about what lives under it. If you cannot say with confidence what `backups/` contains across every container, you are not ready to point a delete action at it.

### In what order should I set this up?

Confirm the account is general-purpose v2 or premium block blob first, then enable last-access tracking only if you plan last-access rules, then map your container and prefix layout, and only then author rules. Tiering rules are safe to deploy early; delete rules should come last, after you have verified their scope against real blobs.

With those prerequisites met, the order of operations for the rules themselves follows a safety gradient. Deploy the reversible actions first and the irreversible ones last. Tiering is reversible in the sense that a blob moved to cool can be moved back, and even archive can be rehydrated, so a tiering rule that is slightly too aggressive is an annoyance and a cost, not a catastrophe. Deletion is irreversible unless you have soft delete or versioning catching the deletes, so a delete rule that is slightly too broad is a data-loss event. Building tiering rules first, watching them behave for a cycle, and adding delete rules only once you trust your scope definitions is the sequence that keeps mistakes recoverable.

## The Step-by-Step Setup With Working Definitions

A lifecycle policy is a JSON document attached to the storage account, and whether you author it in the portal, through the Azure CLI, or as infrastructure code, the underlying object is the same. Understanding that JSON shape is what lets you reason about a policy entry precisely, so it is worth seeing the structure plainly before reaching for a tool that hides it.

A policy contains an array of rules. Each rule has a name, an enabled flag, a type of `Lifecycle`, and a definition split into `actions` and `filters`. The filters carry the scope: a list of blob types the definition applies to and an optional set of prefix matches. The actions carry the threshold-and-action pairs, grouped by what they apply to: the base blob, its snapshots, or its previous versions. Here is a complete single-rule policy that tiers and then deletes blobs under one prefix, annotated so each half of the age-and-scope idea is visible.

```json
{
  "rules": [
    {
      "enabled": true,
      "name": "app-logs-tier-and-expire",
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": [ "blockBlob" ],
          "prefixMatch": [ "app-logs/" ]
        },
        "actions": {
          "baseBlob": {
            "tierToCool":    { "daysAfterModificationGreaterThan": 30 },
            "tierToArchive": { "daysAfterModificationGreaterThan": 90 },
            "delete":        { "daysAfterModificationGreaterThan": 365 }
          }
        }
      }
    }
  ]
}
```

Read that definition through the age-and-scope lens and it is fully transparent. The scope is the `filters` block: this definition touches only `blockBlob` objects whose path begins with `app-logs/`, and nothing else in the account. The thresholds are the day counts inside `actions`: at thirty days past last modification the blob moves to cool, at ninety it moves to archive, at three hundred sixty-five it is deleted. There is no hidden behavior. A blob outside `app-logs/` is never considered. A blob that is twenty days old is never moved. It does exactly what those two halves say and no more.

To apply this from the Azure CLI, you save the policy JSON to a file and attach it to the account in one command:

```bash
az storage account management-policy create \
  --account-name mystorageacct \
  --resource-group my-rg \
  --policy @lifecycle-policy.json
```

In the portal the same object is built through a guided form under the storage account's Data management section, in the Lifecycle management blade, where each rule is assembled with dropdowns for blob type, text fields for prefixes, and day-count inputs for each action. The form is convenient for a first rule and genuinely useful for seeing the available options, but it produces the identical JSON underneath, and for anything you intend to keep, version, or replicate across accounts, the JSON is the artifact that matters. You can always switch the portal blade into its code view to see and copy the exact policy the form is building.

### How do I write a rule that only tiers and never deletes?

Author the rule with tiering actions and no `delete` action at all. A rule whose `baseBlob` block contains only `tierToCool` or `tierToArchive` will move blobs between tiers on schedule and never remove them. Omitting the delete action entirely is safer than setting a very large day count, because there is no expiry to misjudge.

The single most useful habit when authoring is to start every rule disabled, attach it, and inspect what it would match before flipping `enabled` to true. A definition sitting in the policy with `enabled` set to false is inert; it changes nothing. That gives you a window to confirm the prefix resolves to the blobs you expect, which the verification section below covers in detail, before any action runs. The portal and the JSON both let you toggle the enabled flag independently per rule, so you can stage an expiry definition alongside live tiering rules and turn it on only once its scope is proven.
## Scoping a Rule With Prefixes and Filters

The scope half of a lifecycle aging rule is where precision pays off most, so it deserves its own careful treatment. A policy entry's scope is built from two ingredients: the blob type filter and the prefix match. Both narrow the set of blobs the policy entry will ever consider, and an entry with no narrowing applies to every block blob in the account, which is almost never what you want for a delete action.

The prefix match is a string compared against the start of each blob's full path, and the path begins at the container name. This is the detail that trips people up. A prefix of `logs/` does not mean "any blob with logs in its name"; it means "any blob whose path, read from the container name onward, starts with the characters logs slash." If your logs live in a container literally named `logs`, then the matching prefix is `logs/`, because the container name is the first path segment. If your logs instead live under a `data` container in a virtual folder called `logs`, the matching prefix is `data/logs/`. Getting this wrong is the most common way a definition matches nothing, and getting it loosely right is the most common way a policy entry matches too much.

Because the prefix is a leading-string match and not a glob, it cannot express "everything except." There is no way to write a prefix that means "all of the `data/` container but not `data/keep/`." If you need that shape, you express it as multiple narrower prefixes that each name what you do want, rather than one broad prefix you then try to carve exceptions out of. This constraint is a feature in disguise: it pushes you toward enumerating exactly the scopes you intend, which is precisely the explicitness the age-and-scope rule asks for.

### How do prefixes and filters scope a lifecycle definition?

A prefix match limits a rule to blobs whose path, starting at the container name, begins with the given string, and the blob type filter limits it to the chosen blob kinds. Together they define the exact set it acts on. A rule with a broad prefix and no further filter is the classic cause of over-deletion.

Beyond the prefix, newer policy schemas support a `blobIndexMatch` filter that scopes an entry by blob index tags rather than by path. Index tags are key-value attributes you set on individual blobs, and a definition can match on them, which lets you scope by a property like `project=alpha` or `retain=false` independent of where the blob sits in the path hierarchy. This is powerful for data that does not organize neatly by prefix, but it carries its own prerequisite: the tags have to be set correctly and consistently on the blobs, or the definition scopes to a smaller or different set than you assume. Tag-based scoping moves the precision burden from the path layout to the tagging discipline, and it only helps if that discipline is real.

The blob type filter is the quieter half of scope, and it matters more than it looks. A lifecycle definition must declare which blob types it applies to, and the available types are block blobs, append blobs, and page blobs. The tiering actions, moving to cool, cold, or archive, apply to block blobs; append and page blobs do not participate in tiering the same way, and page blobs in particular back disk images and behave differently. Most lifecycle rules you write will declare `blockBlob` and mean it, but if your container mixes blob types, a policy entry that names the wrong type silently does nothing to the blobs you cared about. The deeper mechanics of each blob type, and why block, append, and page blobs behave so differently, are laid out in the [Azure Blob Storage engineering guide](/2022/05/09/azure-blob-storage-engineering-guide/); for lifecycle purposes the practical rule is to match the blob type your data actually uses and to remember that tiering is a block-blob story.

## The Settings the Defaults Get Wrong

Lifecycle management has a handful of defaults and quiet behaviors that bite teams who assume the obvious, and walking through them is the fastest way to avoid the standard mistakes.

The first is the difference between last-modified and last-access as the basis for the age threshold. The default and always-available basis is modification time, expressed as `daysAfterModificationGreaterThan`. This counts from the last write to the blob, which for most data is a perfectly good proxy for staleness. But "not written in ninety days" and "not read in ninety days" are different statements, and for data that is written once and then read occasionally, modification time can tier a blob that is still actively read. If what you care about is genuine coldness, you want `daysAfterLastAccessTimeGreaterThan`, which counts from the last read or write. The catch, repeated here because it is the most common last-access mistake, is that this only works if you enabled last-access tracking on the account first. A last-access rule on an account that never tracked access is a rule with no clock.

### What is the difference between last-modified and last-access rules?

A last-modified rule ages a blob from its last write, which the platform always records. A last-access rule ages it from its last read or write, which requires last-access tracking to be enabled on the account first. Use last-access when read patterns, not write patterns, define whether data is cold.

The second quiet behavior is auto-tiering back up. When you enable last-access tracking, you can also enable a setting that automatically moves a blob from cool back to hot when it is read again, so a blob that goes cold and then becomes active again does not stay penalized in cool. This is genuinely useful for data with bursty access, but it surprises teams who expect a one-way street. If you see blobs you tiered to cool reappearing in hot, this auto-tier-up behavior, not a broken rule, is usually why. It is a setting you opt into, and knowing it exists prevents you from chasing a phantom bug.

The third is the minimum retention and early deletion economics of the cooler tiers, which the configuration does not stop you from fighting. Cool, cold, and archive each carry a minimum retention period, and a blob deleted or moved before that period elapses incurs an early deletion charge prorated to the remaining days. A lifecycle definition that tiers a blob to archive at ninety days and deletes it at one hundred days is technically valid but economically backwards: it pays to put the blob in archive and then pays an early deletion penalty for taking it out almost immediately. The configuration will let you write that definition. The age-and-scope discipline plus a glance at the tier minimums is what stops you from shipping it.

The fourth default worth naming is that a brand-new account has no policy at all, which means every blob stays in its write tier indefinitely until you create one. There is no implicit cleanup. Storage that looks like it is being managed because the account is "set up" is, by default, being managed by nothing. The absence of a policy is itself the most expensive misconfiguration, and it is the one nobody notices because it never throws an error.
## The InsightCrunch Lifecycle Setup Checklist

The recurring failures of lifecycle management are predictable enough that they map onto a short, ordered checklist, one step per decision that can go wrong, with the specific gotcha attached to each. This is the findable artifact of this article: the InsightCrunch lifecycle setup checklist. Work it top to bottom for every rule, and the over-deletion and mis-archiving incidents that fill support threads stop happening to you.

| Step | What you decide | The gotcha that bites if you skip it |
| --- | --- | --- |
| 1. Define the action | Tier (cool, cold, archive) or delete, per target | A delete action is irreversible without soft delete or versioning; tier first, delete last |
| 2. Set the age basis | Last-modified or last-access | Last-access needs account tracking enabled first, or the rule never fires |
| 3. Scope the prefix | The exact path the prefix matches from the container name | A broad prefix matches more containers and folders than you pictured |
| 4. Set the blob type filter | Block, append, or page blob | Tiering applies to block blobs; the wrong type silently does nothing |
| 5. Decide on snapshots and versions | Whether the policy entry touches them, separately from the base blob | A base-blob-only rule leaves snapshots and versions growing and billing |
| 6. Account for the lag | The delay before a saved rule first acts | The definition does nothing for up to a day; teams assume it is broken |
| 7. Verify against real blobs | Confirm it moved or marked the blobs you expected | An unverified delete rule is a data-loss event waiting on a schedule |

Each row is a place where the abstract age-and-scope idea meets a concrete choice, and each gotcha is a real pattern engineers report. The checklist is deliberately ordered as a safety gradient: the early steps are reversible and the late steps are where irreversible loss lives, so the discipline of working it in order is itself a safeguard. The sections that follow walk the steps that carry the most subtlety, starting with the one teams most often get wrong silently, the handling of snapshots and versions.

## Do Lifecycle Rules Apply to Snapshots and Versions?

This is the step that produces the most "but I thought the definition covered that" surprises, and the answer is precise: a lifecycle policy entry applies to whatever you explicitly tell it to apply to, and the base blob, its snapshots, and its previous versions are three separate targets you configure independently. A definition that specifies actions only under `baseBlob` does exactly that and nothing more, leaving snapshots and versions untouched even as they accumulate and bill.

### Do lifecycle rules apply to snapshots and versions?

Only if you configure them to. The `actions` block has separate `baseBlob`, `snapshot`, and `version` sections, each with its own thresholds. A policy entry with only a `baseBlob` action does not touch snapshots or versions, so they keep growing and costing money until you add the matching `snapshot` and `version` actions.

The mechanics follow from the schema. Where the base-blob actions use day counts measured from modification or last access, the snapshot and version actions are measured differently, because snapshots and versions are point-in-time copies whose own clock is the moment they were created. The snapshot action uses `daysAfterCreationGreaterThan`, and the version action uses `daysAfterCreationGreaterThan` as well, each counting from when that snapshot or version came into existence rather than from the base blob's modification time. A complete rule for an account that uses versioning therefore has three blocks, and leaving any one of them out leaves that category unmanaged.

```json
{
  "actions": {
    "baseBlob": {
      "tierToCool":    { "daysAfterModificationGreaterThan": 30 },
      "delete":        { "daysAfterModificationGreaterThan": 365 }
    },
    "snapshot": {
      "tierToCool":    { "daysAfterCreationGreaterThan": 30 },
      "delete":        { "daysAfterCreationGreaterThan": 90 }
    },
    "version": {
      "tierToArchive": { "daysAfterCreationGreaterThan": 90 },
      "delete":        { "daysAfterCreationGreaterThan": 365 }
    }
  }
}
```

This three-block shape is why so many storage accounts with versioning enabled grow far faster than their owners expect. They write a sensible base-blob rule, watch the live data tier and expire on schedule, and conclude the account is managed, while every overwrite quietly creates a new version that no rule ever touches. Versions are full copies for many blob types, so an account with heavy churn and versioning but no version action in its lifecycle policy can hold many times the data its current contents suggest, all of it billed. The fix is not exotic; it is simply remembering that snapshots and versions are separate targets and writing the two extra blocks. The setup checklist puts this at step five precisely so it does not get forgotten, because it is invisible until the bill arrives.

When you do age versions, the relationship between versioning and tiering deserves one note: archiving versions can be a large saving because old versions are by definition rarely read, but it brings the archive trade-off into play for them too, which the next sections address.
## The Rule Lag: Why Nothing Happens at First

A freshly saved lifecycle definition does not act immediately, and the delay confuses more teams than almost any other aspect of the feature. After you attach or change a policy, the platform needs time to register it, and the policy engine itself runs on a periodic cycle rather than continuously. The practical effect is that an entry you save now may not act for up to a day, and even once it begins, it processes the account in a batch that can itself take time to complete on a large account. This is the lag, and it is normal behavior, not a malfunction.

### Why is my new lifecycle definition not doing anything yet?

A new or changed lifecycle definition takes effect after a lag, commonly up to twenty-four hours, because the platform registers the policy and runs the policy engine on a periodic cycle rather than instantly. On a large account the first pass also takes time to scan and act. Wait a full cycle before concluding a definition is broken.

The lag has two consequences worth planning around. The first is psychological: a team that saves a policy entry, refreshes the portal, and sees no blobs moved often assumes the rule is misconfigured and starts editing it, which resets the clock and deepens the confusion. The discipline is to save the policy entry and wait a full cycle before judging it. The second is operational: because there is a delay between authoring and acting, you cannot use a lifecycle definition for anything that needs to happen at a precise moment. Lifecycle management is for steady-state, age-based hygiene, not for "delete this blob at exactly midnight." If you need precise timing, you script the operation directly rather than expressing it as a lifecycle aging rule.

The lag also interacts with verification in a way that matters. When you flip a delete action to enabled, the lag means the deletion does not happen the instant you save, which gives you a window. If you have any doubt about the scope, that window between enabling and the first run is your last chance to disable it before it acts. Treat the lag not only as an annoyance to wait out but as a built-in safety buffer on irreversible actions, and use it deliberately.

## The Verification Step That Proves It Worked

A lifecycle definition you have not verified is a hope, not a configuration, and the verification step is what separates an engineer who trusts the platform from one who proves their intent. There are two distinct things to verify, and they happen at different times: before the definition acts, that its scope matches the blobs you expect, and after it acts, that it actually moved or removed the blobs you intended.

Verifying scope before acting is the more important of the two, because it is the one that prevents loss rather than detecting it after the fact. The cleanest way to verify a prefix scope is to list the blobs the prefix would match and read that list with your own eyes before any action runs. The same prefix string the rule uses can be handed to a list command, and what comes back is exactly the set the policy entry will consider.

```bash
az storage blob list \
  --account-name mystorageacct \
  --container-name app-logs \
  --prefix "" \
  --query "[].name" \
  --output tsv | head
```

For a rule scoped across an account by path prefix rather than within one container, you list at the account or container level and confirm the matched set is the one you pictured. If the list returns blobs you did not expect, your prefix is broader than your intent, and you have caught a future incident before it happened. This is the single highest-value habit in lifecycle management: read the scope as data, not as a string you trust.

Verifying after it acts confirms the action took effect. For a tiering action, you check the access tier of a blob the definition should have moved:

```bash
az storage blob show \
  --account-name mystorageacct \
  --container-name app-logs \
  --name "2023/old-entry.log" \
  --query "properties.accessTier" \
  --output tsv
```

A blob that has been moved reports its new tier, `Cool` or `Archive`, where before it reported `Hot`. For a delete rule, the proof is the blob's absence, ideally confirmed against a known list of what should and should not have survived. The account's metrics and any diagnostic logs you have routed also show tiering and deletion activity in aggregate, which is how you confirm an entry is working across thousands of blobs rather than spot-checking one. The point of either check is the same: you do not declare a definition correct because it saved without error; you declare it correct because you observed it doing what you intended to the blobs you intended.

### How do I confirm a lifecycle definition actually applied?

Verify in two stages. Before enabling, list the blobs the rule's prefix matches and confirm the set is what you intended. After the policy entry runs, show the access tier of a blob it should have tiered, or confirm the absence of a blob it should have deleted, and check account metrics for aggregate tiering and deletion activity.

One related access concern surfaces during verification often enough to name: if your list or show command returns a 403 rather than the data, the problem is access control on the account, not the lifecycle definition, and the two are easy to conflate when you are mid-verification. The distinct causes of a storage 403 and how to confirm which one you are hitting are diagnosed in [fixing the Azure Storage 403 AuthorizationFailure](/2022/08/01/fix-storage-403-authorization-error/); when verification commands fail with a permission error, fix the access path first and then return to confirming it.
## Common Misconfigurations and Their Symptoms

Lifecycle problems cluster into a small number of recurring shapes, and recognizing the shape from the symptom is most of the diagnosis. Each pattern below pairs the misconfiguration with the symptom it produces and the setup step that prevents it, so you can read backward from what you are seeing to what went wrong.

The first and most damaging pattern is the over-broad delete prefix. The setup looks reasonable: a team wants to expire old data under one logical area, writes an expiry definition with a prefix they believe names that area, and enables it. The prefix, however, matches more than they pictured, because it sits higher in the path than they realized or because more than one container's worth of data falls under it. The symptom arrives later and quietly: someone goes to read a blob that should still exist and finds it gone, deleted on schedule by a policy entry doing exactly what its scope said. The prevention is step three of the checklist, verifying the prefix against a real blob list before enabling, and the deeper prevention is the age-and-scope habit of treating a delete rule's scope as the most dangerous string in your configuration. When this pattern bites an account without soft delete or versioning, the data is simply gone, which is why delete rules come last and verified.

The second pattern is archiving data that turns out to need fast reads. Archive is the cheapest tier for a reason: data there is offline in the sense that reading it requires a rehydration step that takes hours and incurs a retrieval cost. A rule that tiers data to archive at a short age, written by someone who assumed the data was cold, runs into trouble when a workload still reaches for that data and now waits hours per read and pays per gigabyte to pull it back. The symptom is not an error; it is latency and surprise cost. The prevention is to be honest about access patterns before archiving and to prefer last-access over last-modified for data whose read pattern, not its write pattern, determines coldness. Archive is correct for data you are confident you will rarely or never read; it is a trap for data you read occasionally but unpredictably.

The third pattern is the definition that does not touch snapshots or versions as expected, covered above but worth restating as a symptom: the account keeps growing and billing despite a sensible-looking base-blob rule, and the growth traces to versions or snapshots no action ever ages. The prevention is step five, configuring the snapshot and version action blocks explicitly rather than assuming the base-blob rule reaches them.

The fourth pattern is the lag mistaken for a broken rule, also covered above: a freshly saved rule appears to do nothing, the team edits it repeatedly, and each edit resets the clock so the rule never gets a clean cycle to run. The prevention is step six, knowing the lag exists and waiting a full cycle before judging.

The fifth pattern is tiering by the wrong clock, choosing last-modified when the data's relevant signal is last-access or the reverse. A dataset written once and read steadily, aged by modification time, gets tiered to cool or archive while still in active use, because modification time says it is old even though access time says it is hot. The symptom is active data sitting in a tier that penalizes reads. The prevention is matching the age basis to how the data is actually used, and enabling last-access tracking up front if access is the right signal.

The sixth pattern is the unverified rule in general, the absence of step seven. A definition is authored, enabled, and never checked, so whether it is doing the right thing, the wrong thing, or nothing at all is unknown until something goes wrong. The symptom is the absence of confidence, and the cost is that the first real signal you get about a misconfigured rule is the incident it causes. The prevention is the verification habit: every rule, before and after, confirmed against real blobs.

### Why did my lifecycle definition delete data I still needed?

Almost always because the delete action's prefix matched a broader set of blobs than intended, so it expired data outside the area you pictured. The rule did exactly what its scope said. Confirm by listing what the prefix matches; the fix is a narrower, verified prefix, and soft delete or versioning as a safety net under delete rules.

Reading these six patterns together, a theme emerges that is worth making explicit: not one of them is a platform bug, and every one of them is a scope, threshold, target, or verification gap. That is the age-and-scope rule restated as a troubleshooting heuristic. When a lifecycle policy entry misbehaves, the answer is in the policy entry, and it is always some combination of a too-broad scope, a wrong threshold, a missing target block, or a step you did not verify.

## The Archive Trade-Off, Configured Deliberately

Archive deserves a section of its own because it is simultaneously the largest saving lifecycle management offers and the easiest tier to misuse, and the difference is entirely in whether you configured it for data that genuinely belongs there.

Archive storage is offline storage. A blob in the archive tier is not readable in place; before you can read it, you must rehydrate it, which means moving it back to an online tier, an operation that takes a meaningful amount of time, often measured in hours rather than seconds, and which carries a data retrieval cost in addition to the tier change. There are priority options that rehydrate faster at higher cost, but even the fastest is not the instant read you get from hot or cool. This is the property that makes archive cheap to store and expensive to access, and a lifecycle definition that moves data to archive is making a bet that the data will rarely or never be read.

### When should a lifecycle aging rule send blobs to archive?

When you are confident the data will be read rarely or never, and you can tolerate hours of rehydration latency plus a retrieval cost on the rare read. Archive suits compliance copies, long-term backups, and aged log retention. It is wrong for anything read on an unpredictable schedule, because every read becomes a slow, billed rehydration.

The configuration discipline for archive is therefore to point archive actions only at data whose access profile you understand and can defend. Compliance archives that must be retained for years but are realistically never read, backup generations kept for a recovery scenario that rarely arrives, log data aged well past any active investigation window: these are archive's natural home, and tiering them there is one of the largest line-item reductions a storage bill can see. The mistake is reaching for archive's price without reckoning with its access cost, and the definition that prevents the mistake is to ask, for any data you are about to archive, what happens the day someone needs to read it. If the answer is "we wait hours and pay a fee, and that is acceptable because it almost never happens," archive is right. If the answer makes you wince, the data belongs in cool or cold, not archive.

There is also an interaction with the early deletion charge worth folding into the archive decision. Because archive carries the longest minimum retention of the tiers, a blob you archive and then delete soon after incurs the largest early deletion penalty. A lifecycle policy that archives at one age and deletes at a barely larger age pays to store offline and then pays again to remove it before it has earned its keep. The deliberate configuration sets the delete threshold far enough beyond the archive threshold that the archived blob spends real time in the cheap tier before any deletion, so the saving is actually realized rather than canceled by a penalty. The broader cost reasoning behind these thresholds, including how to weigh rehydration against retention, sits in the [Azure storage cost optimization](/2024/11/18/azure-storage-cost-optimization/) treatment, and a lifecycle policy is where that reasoning becomes a concrete, running configuration.
## Making the Configuration Repeatable as Code

A lifecycle policy authored once in the portal is a policy that drifts, gets forgotten, and cannot be reviewed or replicated. The mature practice is to express the policy as infrastructure code, version it alongside the rest of the account definition, and apply it the same way for every account, so that the rule that protects one account's bill protects every account's bill identically and on purpose. This is the same discipline the series applies everywhere: a configuration that matters belongs in source control, not in a portal blade someone clicked through once.

The policy is a property of the storage account resource, so it lives naturally in the same template that defines the account. In Bicep, the management policy is a child resource of the storage account, and the rules array is the same JSON shape you have already seen, simply expressed in the template language:

```bicep
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: 'mystorageacct'
}

resource lifecycle 'Microsoft.Storage/storageAccounts/managementPolicies@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    policy: {
      rules: [
        {
          enabled: true
          name: 'app-logs-tier-and-expire'
          type: 'Lifecycle'
          definition: {
            filters: {
              blobTypes: [ 'blockBlob' ]
              prefixMatch: [ 'app-logs/' ]
            }
            actions: {
              baseBlob: {
                tierToCool:    { daysAfterModificationGreaterThan: 30 }
                tierToArchive: { daysAfterModificationGreaterThan: 90 }
                delete:        { daysAfterModificationGreaterThan: 365 }
              }
            }
          }
        }
      ]
    }
  }
}
```

The name of the management policy resource is always `default`; a storage account has exactly one management policy, and that policy holds all the rules. This is a point of confusion worth flagging: you do not attach many policies to an account, you attach one policy containing many rules. Authoring the policy as code makes that structure obvious and stops the instinct to create a second policy that would only overwrite the first.

### How do I apply the same lifecycle policy across many accounts?

Express the policy as infrastructure code, a Bicep module or an ARM template, parameterized so the same rule set deploys to every account, and apply it through your pipeline. For fleet-wide enforcement, an Azure Policy definition can audit or deploy a standard lifecycle configuration so new accounts inherit it automatically.

For a fleet of accounts that should all carry the same baseline lifecycle hygiene, the per-account template is the building block and governance is the enforcement layer. You can wrap the standard rule set in a module and reference it from every account's deployment, which guarantees a new account ships with the policy rather than waiting for someone to remember. Going further, a governance policy can audit accounts for the presence of a lifecycle configuration and flag or remediate the ones missing it, turning "we should have lifecycle rules everywhere" from an aspiration into an enforced standard. The mechanics of that enforcement belong to the governance tooling rather than to lifecycle management itself, but the point for this article is that the lifecycle policy is a normal, templatable resource, and treating it as one is what makes the saving durable across an estate rather than a thing you did to one account once.

Whichever tool you use, the workflow that keeps a fleet honest is the same: the policy lives in source control, changes to it go through review where a human can read the scope and the thresholds before they ship, and deployment is automated so the deployed state matches the reviewed state. A delete rule's prefix reviewed by a second pair of eyes in a pull request is far less likely to be the over-broad prefix that causes an incident, which means the code discipline is not just tidiness; it is another layer of the same scope safety the whole article is built around.

## A Worked Setup: Lifecycle for a Mixed-Use Account

The abstract rules land harder against a concrete account, so consider a realistic one and build its policy end to end. Picture a storage account that serves three distinct workloads sharing the same general-purpose v2 account. A container named `app-logs` collects application log files written continuously and read only during incident investigations. A container named `backups` holds nightly database backup files that are kept for a year for recovery and audit but are realistically read only during a restore. A container named `exports` holds report files that a downstream team pulls from steadily for two weeks after generation and then never touches again. Three workloads, three access profiles, and a single policy must serve all of them without harming any.

Start with the logs, because they are the clearest case. Log files are written and then almost never read until something goes wrong, and when something does go wrong it is usually recent logs that matter. That access profile says: tier aggressively by modification age, keep recent logs readily available, and expire old logs once they are past any investigation or compliance window. A sensible rule cools log blobs at thirty days, archives them at ninety, and deletes them at a year, all scoped tightly to the one container by the `app-logs/` prefix. Because logs are written once and not modified, last-modified aging is the right clock here; there is no read pattern to preserve.

The backups are a different profile. They are written nightly, never modified, and read only during the rare restore, which makes them the textbook case for archive: cheap offline storage for data you keep out of caution and hope never to need. A policy entry scoped to `backups/` can tier straight to archive at a short age, because confidence that backups are cold is high, and delete them at the retention boundary the business requires. The one discipline to apply is spacing the delete threshold well past the archive threshold so the early deletion penalty never triggers, and the one thing to respect is that a restore from these archived backups will involve rehydration time, which the recovery runbook must account for. Archiving backups is one of the largest single savings available on an account like this, precisely because backups are voluminous and almost never read.

The exports are the trap waiting to happen, and they are why a single broad rule would be wrong for this account. Exports are read steadily for two weeks, which means a rule that ages them by modification time and tiers them to cool at, say, ten days would push actively read data into cool while the downstream team is still pulling it, paying read transaction costs and possibly latency on hot data. The correct configuration for exports uses last-access aging so that the two weeks of steady reads keep each blob warm, and only tiers a blob once it has actually gone fourteen days without a read. That requires last-access tracking enabled on the account, which is the prerequisite you set before authoring this definition, and it illustrates why the account-level toggle exists. After the read window, exports can cool and then expire on a modest schedule scoped to `exports/`.

The finished policy is three rules in one policy document, each scoped to one container, each with an age basis matched to its workload's real access pattern, and each verified independently. Before enabling any delete action, you list the blobs under each prefix and confirm the set, paying closest attention to the `backups/` expiry definition because its data is the most painful to lose. You enable the tiering actions first, watch a cycle, confirm with `accessTier` checks that log and backup blobs are moving as intended, and only then enable the delete actions, using the lag as a final window to catch a mistake. The result is an account where three very different data lifecycles coexist correctly, and not one rule can touch a workload it was not written for, because every scope names exactly one container and every threshold matches one access profile. That is the age-and-scope rule applied at the level of a real account rather than a single rule, and it is the shape every production lifecycle policy should take.

## Lifecycle Rules and Immutable or Legal-Hold Data

A behavior that surprises teams in regulated environments is what happens when a lifecycle delete rule meets a blob protected by an immutability policy or a legal hold. Immutable storage, configured through time-based retention policies or legal holds at the container level, prevents a blob from being modified or deleted for the duration of the retention or hold. This protection takes precedence over a lifecycle definition. A lifecycle delete action that targets a blob still under an active retention period or legal hold cannot remove it, and the protection wins.

### Can a lifecycle policy entry delete a blob that is under a legal hold?

No. A time-based retention policy or a legal hold protects a blob from deletion for its duration, and that protection overrides a lifecycle delete action. The lifecycle definition cannot expire a blob the immutability policy still protects; the blob is removed only once the retention period has elapsed or the hold is released.

This interaction is usually what you want rather than a problem, because the whole point of immutability is that nothing, including an automated rule, can prematurely destroy protected data. But it changes how you reason about a lifecycle policy on a container that also carries immutability. A delete threshold of one year on a container whose blobs sit under a two-year retention policy will not actually delete anything at the one-year mark; the blobs persist until the retention clears, and only then does the next lifecycle pass become able to expire them. If you observe a delete action that appears to be ignoring its threshold on certain blobs, an immutability policy or legal hold on those specific blobs is a leading suspect, and the diagnosis is to check the container's immutability configuration and the individual blobs' hold status before suspecting the policy entry.

The configuration guidance that follows is to keep lifecycle thresholds consistent with, rather than contradictory to, any immutability policy on the same data. Setting a lifecycle delete age shorter than an immutability retention period is not dangerous, since the protection prevents premature deletion, but it is misleading, because it's stated intent and the actual behavior diverge. The clearer configuration sets the lifecycle delete age at or beyond the immutability boundary so the policy reads as what it does. Tiering actions, by contrast, generally coexist with immutability without conflict, since moving a blob between tiers does not modify or delete its content, so you can still archive immutable data for cost while its protection persists.

## Reading the Signal: Metrics, Logs, and the Change Feed

Verification scales poorly if it means checking blobs one at a time, and on an account with millions of objects you need account-level observability to confirm a lifecycle policy is behaving across the whole estate rather than on the one blob you happened to inspect. Three sources give you that view, and configuring them turns lifecycle from a thing you hope is working into a thing you can see working.

The first is account metrics. Storage exposes metrics for capacity and transactions broken down by tier, and after a lifecycle policy starts acting you should see the capacity in hot decline and the capacity in cool, cold, or archive rise as blobs move, along with transaction counts for the tier-change operations. Watching the tier capacity split shift over the days after you enable a policy is the aggregate confirmation that tiering is happening at scale. A policy that you enabled but that shows no movement in the tier capacity breakdown after a full cycle is a policy worth investigating, because the metrics are telling you the definition is not matching what you thought it would.

The second is diagnostic logging. Routing the storage account's diagnostic logs to a Log Analytics workspace lets you query the actual operations the platform performed, including the tiering and deletion activity lifecycle rules generate, so you can ask precise questions like which blobs changed tier in the last day or how many deletions an entry performed. This is the difference between believing a definition ran and being able to show exactly what it did, which matters most for delete rules where the record of what was removed is itself valuable. The deeper mechanics of routing and querying storage telemetry are a topic of their own, but the lifecycle-relevant point is that the activity a policy generates is observable if you have configured the account to emit it.

The third is the change feed, an ordered, durable log of every change to blobs in the account, which when enabled records the create, update, tier-change, and delete events that lifecycle rules produce among all other changes. Where metrics give you aggregates and diagnostic logs give you queryable operations, the change feed gives you a complete, replayable record, which is useful for auditing exactly what a lifecycle policy did over time and for reconstructing the sequence of events if a policy entry behaved unexpectedly. Enabling the change feed has its own storage cost, so it is a deliberate choice rather than a default, but for accounts where the consequences of a lifecycle mistake are high, having an ordered record of every tier change and deletion is a strong safety and audit posture. Together these three signals mean that confirming a lifecycle policy is not a matter of faith or of inspecting a single blob; it is a matter of reading the account telling you, at scale, exactly what its rules are doing.

## How Lifecycle Interacts With the Rest of the Account

A lifecycle policy does not run in a vacuum, and a few interactions with other storage features are worth understanding before you enable rules on an account that uses them, because the interactions explain behavior that otherwise looks like a bug.

Blob versioning, covered earlier as a separate lifecycle target, interacts with lifecycle most heavily, and the relationship is the source of the unbounded-growth pattern: versioning silently creates a new version on every overwrite, and only a version action in the lifecycle policy ages those versions. The practical rule, restated as an interaction, is that enabling versioning without writing version lifecycle actions is choosing to accumulate copies indefinitely, so the two features should be configured together as a pair rather than versioning being switched on and lifecycle being assumed to cover it.

Point-in-time restore, which lets you roll a container back to an earlier moment, depends on versioning, change feed, and soft delete, and it sets a floor under what lifecycle can effectively expire within the restore window. If you rely on point-in-time restore with a given retention, a lifecycle policy that aggressively deletes the underlying versions or soft-deleted blobs the restore depends on can undercut the restore capability. The two need to be reconciled so that lifecycle expiry does not quietly shorten the real restore window below what you believe you have, which is a reconciliation to do deliberately rather than discovering after a failed restore.

Object replication, which copies blobs from a source account to a destination account, raises a sequencing question with lifecycle. A lifecycle definition on the source that tiers blobs to archive can affect what and how replication copies, and a lifecycle delete on the source does not necessarily clean the destination, which has its own policy. When an account participates in replication, you reason about lifecycle on both ends rather than assuming a source rule governs the replicated copy, because the destination is a separate account with its own lifecycle configuration and its own bill.

Finally, the tiering of a blob does not change its content, its name, its metadata, or its access control, only its access tier and therefore its storage cost and read behavior. This is reassuring and worth stating plainly, because it means a tiering rule is safe with respect to everything except read latency and transaction cost: applications that locate blobs by name and read them still find them after a cool or cold tier change, with the only difference being the per-read cost and, for archive, the rehydration requirement. The interactions that genuinely require care are with the features that themselves retain or replicate data, versioning, soft delete, point-in-time restore, immutability, and object replication, because those are the features whose data a lifecycle definition can either fail to manage or wrongly remove. Mapping which of them an account uses before enabling lifecycle rules is the last piece of the prerequisite homework, and it is what keeps a lifecycle policy from colliding with a feature it was supposed to coexist with.

## Rehydration: Getting Archived Data Back

Because lifecycle rules are the most common way data ends up in archive, understanding how to get it back is part of configuring archive responsibly, and the rehydration process has enough nuance that a runbook should describe it before anyone needs it under pressure. Rehydration moves a blob from archive to an online tier, hot or cool, where it can be read normally, and it is neither instant nor free.

You request rehydration in one of two ways. You can change the blob's access tier from archive to hot or cool, which begins a rehydration that the platform completes asynchronously, or you can copy the archived blob to a new online blob, leaving the original in archive, which is useful when you want to keep the archived copy untouched. Either way the operation takes time, and that time depends on the rehydration priority you request. Standard priority completes on a timescale that is commonly hours, while a high priority option completes faster for smaller blobs at a higher cost. Neither is a substitute for the data having been in an online tier to begin with, which is the entire point of being deliberate about what a lifecycle aging rule archives.

### How long does it take to read a blob a lifecycle definition archived?

You cannot read it until it is rehydrated, and rehydration commonly takes hours at standard priority, faster at high priority for an added cost. You trigger rehydration by changing the blob's tier to hot or cool or by copying it to an online blob. Plan archive only for data whose reads can tolerate that delay.

The cost of rehydration has two parts that surprise teams who focused only on archive's low storage price. There is a data retrieval charge proportional to the amount rehydrated, and there is the tier the data lands in, which then bills at its own rate. For data that is genuinely read rarely or never, these costs are trivial because they almost never occur, which is exactly why archive is correct for cold data. For data read even occasionally, the retrieval charges accumulate and the rehydration latency frustrates the workloads waiting on the data, which is exactly why archive is wrong for warm data and why a lifecycle policy entry that archives the wrong data is a slow, expensive mistake rather than a fast, obvious one. The configuration takeaway is to treat the question "what happens when we need this back" as part of writing any archive action, and to capture the answer in the operational runbook so that the day a restore or an audit needs archived data, the team knows the rehydration will take hours and a fee and has planned around it rather than discovering it mid-incident.

## When Not to Use a Lifecycle Rule

A guide to configuring a feature is incomplete without the boundary where the feature stops being the right tool, and lifecycle management has a clear one. Lifecycle rules are for age-based, steady-state movement and expiry of data at scale, and they are excellent at exactly that. They are the wrong tool whenever the decision about a blob depends on something other than its age and its scope.

If a blob should be deleted or moved based on an event, a record being processed, a job completing, a downstream system acknowledging receipt, that is application logic, and it belongs in the application or in a function triggered by the event, not in a lifecycle definition that knows only about age. If a blob needs to be handled at a precise time, a lifecycle aging rule cannot promise the timing because it runs on a periodic cycle after a registration lag, so a scheduled script or a timer-triggered function is the correct mechanism. If the set of blobs to act on is defined by a query over content or metadata more complex than a path prefix or an index tag, the rule's scoping cannot express it, and you need code that enumerates the target set itself. And if the action is anything other than tiering or deletion, lifecycle rules simply do not offer it, so renaming, transforming, or moving blobs between containers is work for a script or a data pipeline.

The corollary is reassuring: within its boundary, lifecycle management is the right tool and you should not reach for a custom script to do what a rule does well. Teams who do not trust the feature sometimes build their own age-based cleanup with scheduled scripts that list blobs and delete the old ones, which reinvents lifecycle management worse, with more code to maintain, more ways to get the scope wrong, and none of the platform integration. If the job is "tier or delete blobs by age, scoped by path," the lifecycle definition is the answer and a hand-rolled script is a step backward. The discipline is to know which side of the boundary a given requirement falls on: age and scope, use an entry; event, precise timing, complex selection, or a non-tier-non-delete action, use code. Drawing that line correctly keeps lifecycle policies simple and trustworthy and keeps the genuinely application-specific logic where it belongs.

## Editing and Evolving a Lifecycle Policy Safely

A lifecycle policy is not a thing you set once and forget, because the data on an account changes, new containers appear, and retention requirements shift, so the policy has to evolve, and editing it carries its own small risks worth handling deliberately. The first principle is that any edit to a delete rule deserves the same scope verification as the original, because widening a prefix or shortening a threshold during an edit can introduce exactly the over-broad-scope incident the original authoring avoided. Treat an edit to an expiry definition's scope or threshold as a new definition for review purposes, list what the changed prefix matches, and confirm it before the edited rule takes effect.

The second principle is to lean on the disabled state during transitions. When you are reworking a definition, disabling it while you edit, then re-enabling once the new definition is verified, prevents an intermediate, half-edited definition from acting during a portal session or a partial deployment. Because the policy is a single document, a careless save can replace the whole rule set, so when editing through code the safe pattern is to read the current policy, modify it, and write the complete intended set back, rather than assuming an edit appends to what exists. The one-policy-per-account structure means there is no merge; the last write of the policy document wins entirely, and a deployment that writes a policy with only the rules it knows about will silently drop any rules it does not include.

That last point is the most common policy-evolution mistake on accounts managed partly by hand and partly by code: someone adds a policy entry in the portal, then a later infrastructure deployment writes a policy from the template that never knew about the portal rule, and the portal rule vanishes because the deployment overwrote the whole document. The fix is to make code the single source of truth for the policy so there is never a portal rule for a deployment to clobber, which is another reason the infrastructure-as-code discipline matters beyond mere tidiness. When the policy lives entirely in source control and every change goes through the template, evolution is just a reviewed pull request, the complete intended rule set is written every time, and there is no hand-edited rule waiting to be silently lost. Evolving a lifecycle policy safely, then, is mostly about respecting that the policy is one document with last-write-wins semantics, verifying scope on every delete-rule change as carefully as on the first authoring, and using the disabled state and the lag as the buffers they are during any transition.

## Practicing This on a Real Account

Reading about lifecycle rules gets you the model; building one against an account and watching it behave is what makes the model stick, and it is worth doing in a place where a mistake costs nothing. The most useful way to internalize the age-and-scope rule is to write a rule, list the blobs its prefix matches, enable it, and watch the tier of a test blob change and a test blob expire, so the abstract becomes something you have seen happen. You can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.net/tools/azure-labs.html) to do exactly that against a sandbox storage account, authoring a lifecycle policy, scoping it with a prefix, and watching blobs tier and expire on a compressed schedule so you observe the full cycle without waiting days for it. VaultBook keeps a tested library of the storage CLI, PowerShell, and template commands this article uses, so the verification commands and the policy JSON are there to run and adapt rather than to retype, and the lab environment lets you make the over-broad-prefix mistake safely and see precisely what it does before you would ever risk it on real data. Working a lifecycle definition end to end once, including deliberately breaking the scope to watch the consequence, is the fastest path from understanding the feature to trusting your own configurations of it.

## Closing Verdict

Storage lifecycle management is one of the highest-impact configurations in Azure storage, and it is also one of the easiest to turn into a quiet incident, and both facts come from the same source: the platform faithfully executes the policy entry you give it, with no judgment about whether it's scope is what you meant. The age-and-scope rule is the entire defense. A lifecycle definition is an age threshold plus a scope, the threshold is a number you can check at a glance, and the scope is a prefix and a filter you must verify against real blobs because the policy definition alone cannot show you what they match. Build tiering rules first because they are reversible, add delete rules last and only after their scope is proven, configure snapshots and versions as the separate targets they are, expect and use the lag as a safety buffer, and verify every rule before and after it acts. Do that, and lifecycle management becomes what it should be: an account that quietly tiers and expires data by age, a bill that falls on its own and stays down, and a configuration you can defend in a review because every rule says exactly what it does and you have watched it do it. Skip the verification and trust a prefix you never read, and the same feature will one day delete something you needed, on schedule, without an error, which is the most expensive kind of working as configured there is.
## Frequently Asked Questions

### Q: How do I set up storage lifecycle management on an Azure storage account?

You set it up by attaching a lifecycle policy, a single JSON document of rules, to a general-purpose v2 or premium block blob account. Each rule names the blobs it scopes to, with a blob type filter and an optional path prefix, and the age-based actions it takes, tiering to cool, cold, or archive, or deleting. You can build the policy through the storage account's Lifecycle management blade in the portal, attach it with the Azure CLI management-policy command, or define it as infrastructure code in a Bicep or ARM template. The recommended order is to confirm the account kind first, enable last-access tracking only if you plan last-access rules, map your container and prefix layout, then author tiering rules before delete rules. Start each definition disabled, verify its scope against a real blob list, and enable it once you trust the scope.

### Q: How do lifecycle rules move blobs between storage tiers?

A rule moves blobs by pairing a tier action with an age threshold inside its `actions` block. The base-blob actions `tierToCool`, `tierToCold`, and `tierToArchive` each take a day count, and when a blob in the definition's scope crosses that age, the platform changes its access tier. The age is measured from last modification by default, or from last access if you enabled access tracking and used the last-access condition. Tiering applies to block blobs; append and page blobs do not participate the same way. The movement runs on the policy engine's periodic cycle rather than instantly, so a blob crossing the threshold today may tier on the next pass rather than the moment it ages. A blob can move through several tiers over its life if a single rule specifies cool at one age and archive at a later one, and the platform applies whichever threshold the blob has currently passed.

### Q: How do I auto-delete old blobs without removing data I still need?

You write a delete action with an age threshold and, critically, a scope you have verified. The `delete` action under `baseBlob` takes a day count, and any in-scope blob past that age is removed on the next evaluation cycle. The safety is entirely in the scope: before enabling the rule, list the blobs its prefix matches and read that list to confirm it contains only data you are willing to lose at that age. Keep delete rules narrow, prefer enumerating the exact prefixes you want over a broad prefix you hope is safe, and deploy delete rules last, after your tiering rules are proven. Enabling soft delete or blob versioning on the account gives you a recovery net so that a mistaken deletion is recoverable rather than permanent, which is worth having under any delete rule.

### Q: How do prefixes and filters scope a lifecycle policy entry?

The prefix and the blob type filter together define exactly which blobs an entry considers. The prefix is matched against each blob's full path starting at the container name, so `app-logs/` matches blobs whose path begins with that string and nothing else, and the match is a leading-string comparison, not a wildcard glob. The blob type filter limits the policy entry to block, append, or page blobs. A newer `blobIndexMatch` filter can additionally scope by blob index tags rather than by path. A definition with a broad prefix and no further filter applies to nearly everything, which is the classic cause of over-deletion. Because the prefix cannot express exclusions, you scope by naming the narrow prefixes you do want rather than carving exceptions out of a wide one. Verifying the matched set against a real blob listing before enabling it is the habit that keeps scope honest.

### Q: Do lifecycle rules apply to snapshots and versions automatically?

No. The base blob, its snapshots, and its previous versions are three independent targets, each configured in its own section of the `actions` block. A policy entry with only a `baseBlob` action leaves snapshots and versions completely untouched, so they keep accumulating and billing even while the live data tiers and expires correctly. To manage them you add `snapshot` and `version` sections, whose thresholds use `daysAfterCreationGreaterThan` measured from when each snapshot or version was created rather than from the base blob's modification time. This is a frequent cause of accounts that grow far faster than expected: versioning is enabled, every overwrite creates a new version, and no version action ever ages them. The fix is to write the two extra action blocks. If you use snapshots or versioning at all, treat configuring their lifecycle actions as a required step, not an optional one.

### Q: How do I confirm a lifecycle definition actually applied?

Verify in two stages. Before the definition acts, list the blobs its prefix matches and confirm the set is exactly what you intended, which catches an over-broad scope before any data is touched. After the rule runs, prove the action took effect: for a tiering action, show a moved blob's `accessTier` property and confirm it now reports Cool or Archive instead of Hot; for a delete action, confirm the absence of blobs that should have expired against a known list of what should and should not survive. Account metrics and any diagnostic logs you have routed show tiering and deletion activity in aggregate, which is how you confirm behavior across many blobs rather than spot-checking one. Do not treat a policy that saved without error as a working policy. A rule is correct only once you have observed it doing what you intended to the blobs you intended.

### Q: What is the difference between last-modified and last-access conditions in a lifecycle aging rule?

A last-modified condition, `daysAfterModificationGreaterThan`, ages a blob from its most recent write, and the platform always records modification time, so this condition works on any account with no setup. A last-access condition, `daysAfterLastAccessTimeGreaterThan`, ages a blob from its most recent read or write, which better reflects genuine coldness for data that is written once and read occasionally. The catch is that last-access tracking is off by default and must be enabled at the account level before any last-access rule has data to act on; a last-access rule on an account that never tracked access simply never fires. Choose last-modified when write recency is a good proxy for staleness, and last-access when read patterns, not write patterns, decide whether data is cold. Enabling access tracking up front is the prerequisite that makes the last-access choice viable.

### Q: Why is my new lifecycle definition not moving or deleting anything yet?

Almost certainly the lag. A newly saved or changed policy does not act immediately; the platform registers it and runs the policy engine on a periodic cycle, so a definition commonly takes up to about a day to first act, and on a large account the initial pass also takes time to scan and process. Teams who save a policy entry, refresh, and see nothing often assume it is broken and start editing, which resets the clock and prolongs the confusion. The discipline is to wait a full cycle before judging a rule. If after a full cycle the policy entry still does nothing, then look for a real cause: a prefix that matches no blobs, a blob type filter that excludes your data, or a last-access condition on an account without access tracking. The lag also doubles as a safety buffer, giving you a window to disable a delete rule before its first run if you have doubts.

### Q: Can a lifecycle definition move a blob straight from hot to archive?

Yes. A single rule can specify `tierToArchive` with an age threshold and the platform will move a qualifying blob directly from its current tier to archive when it crosses that age, without requiring an intermediate stop in cool or cold. You can also stage the movement deliberately, with `tierToCool` at one age and `tierToArchive` at a later age in the same rule, so a blob cools first and archives later, which can reduce early deletion exposure on the cool tier. Whether to jump straight to archive or stage through cool depends on the data's access profile and the tier minimums. Going straight to archive is fine for data you are confident is cold from a known age. Staging makes sense when there is a window where the data is cool-cold but still occasionally read and you want to avoid archive's rehydration cost during that window.

### Q: What happens when a workload reads a blob a lifecycle policy entry moved to archive?

The read does not just return slowly; it cannot complete in place at all until the blob is rehydrated. Archive is offline storage, so reading an archived blob requires first moving it back to an online tier through a rehydration operation that commonly takes hours and incurs a data retrieval charge. There are higher-priority rehydration options that complete faster at higher cost, but none of them is the instant read you get from hot or cool. This is why archiving data with an unpredictable read pattern is a trap: every unexpected read becomes a slow, billed rehydration. The configuration lesson is to point archive actions only at data whose access profile you understand and can defend as rarely or never read, and to prefer last-access aging for anything whose read pattern, rather than its write pattern, determines whether it is truly cold enough for archive.

### Q: How many lifecycle rules can one storage account have, and how many policies?

An account has exactly one lifecycle management policy, and that single policy holds all of its rules in a rules array, so you do not attach multiple policies; you add multiple rules to the one policy. The management policy resource is always named `default` for this reason. There is a documented upper bound on the number of rules a single policy can contain, and that limit, like other storage limits, is a value to confirm against the current official documentation at the time you build, since service limits are raised over time. For most accounts the practical rule count stays well below any ceiling, because a handful of well-scoped rules covers the common tiering and expiry needs. If you find yourself wanting dozens of rules, that is usually a sign the data layout could be simplified so that broader, safer prefixes do the work of many narrow ones.

### Q: Should I enable soft delete or versioning before turning on lifecycle delete rules?

It is strongly advisable. A lifecycle expiry definition is irreversible by itself: once it expires a blob, the blob is gone unless something captured the deletion. Blob soft delete retains deleted blobs for a configured retention window so a mistaken expiry can be recovered, and versioning preserves prior states of overwritten blobs. With either in place, an over-broad delete rule becomes a recoverable mistake rather than a permanent loss, which materially lowers the risk of the most damaging lifecycle misconfiguration. The trade-off is that both features retain data and therefore cost storage, and, importantly, the retained snapshots and versions themselves need lifecycle actions so they do not accumulate forever. The balanced configuration is to enable a recovery net under delete rules, then write the matching snapshot and version lifecycle actions so the safety net is itself managed rather than becoming a new source of unbounded growth.

### Q: Can I disable a single lifecycle definition without deleting it from the policy?

Yes. Each rule carries an `enabled` boolean independent of the other rules in the policy, so you can set an entry's `enabled` to false to make it inert while leaving its definition in place, and re-enable it later without rewriting it. This is the mechanism behind the recommended staging habit: author a definition disabled, verify its scope, then flip it on. It is equally useful operationally, letting you pause a delete action during a period when you are uncertain about an account's data, or temporarily suspend tiering during a migration, without losing the policy definition or its carefully verified prefix. The portal exposes a per-rule enable toggle and the JSON exposes the flag directly. Disabling is the safe, reversible way to stop a policy entry's behavior, and it is far preferable to deleting and later reconstructing a rule whose scope you spent effort getting right.

### Q: How do lifecycle rules treat append blobs and page blobs?

Lifecycle tiering between hot, cool, cold, and archive is a block blob story; append and page blobs do not move through those access tiers the way block blobs do. A definition's blob type filter lets you name `blockBlob`, `appendBlob`, or `pageBlob`, and the actions available depend on the type. For append blobs, the meaningful lifecycle action is expiry by age rather than tiering. Page blobs, which back managed and unmanaged disks and behave as random-access objects, follow their own rules and are generally not what you target with tiering actions. The practical guidance is to write tiering rules against block blobs and to be deliberate when an account mixes types, because an entry that names the wrong blob type silently does nothing to the data you cared about. When in doubt about which type your data is, inspect a representative blob's type before scoping a definition to it.

### Q: How do I scope a lifecycle definition to a single container only?

Use a prefix match equal to the container name followed by a slash, because the prefix is matched against the blob path starting at the container name. A prefix of `app-logs/` scopes it to exactly the `app-logs` container and nothing else, since no blob outside that container has a path beginning with those characters. If you want to scope to a virtual folder within a container, extend the prefix, for example `app-logs/2023/` to reach only that subtree. To confirm the scope is truly limited to the one container, list blobs at the account level with that prefix and verify nothing outside the intended container appears. This per-container scoping is the safe default for delete rules: a policy entry that can only ever touch one named container cannot accidentally expire data elsewhere, which contains the blast radius of any threshold mistake to a single, known area.

### Q: How do I express a lifecycle policy as infrastructure code?

Define it as a child resource of the storage account. In Bicep or ARM the resource type is `Microsoft.Storage/storageAccounts/managementPolicies`, its name is always `default`, and its `properties.policy.rules` array is the same JSON rule shape you would author in the portal. Putting the policy in the template alongside the account means the lifecycle configuration is versioned, reviewed, and deployed with everything else, so it cannot silently drift or be forgotten. The review step is itself a safety layer, because a second reader can catch an over-broad delete prefix in a pull request before it ever ships. For a fleet, wrap the standard rule set in a parameterized module referenced by every account deployment so new accounts inherit the baseline automatically, and use a governance policy to audit for accounts missing a lifecycle configuration. Treating the policy as ordinary, templatable infrastructure is what makes the saving durable across an estate.

### Q: Does a lifecycle aging rule incur an early deletion charge, and how do I avoid it?

It can, if the definition moves or deletes a blob out of cool, cold, or archive before that tier's minimum retention period has elapsed, because each cooler tier carries a minimum retention and an early exit is charged prorated to the remaining days. A policy that tiers a blob to archive at one age and deletes it at a barely larger age is the classic offender: it pays to store the blob offline and then pays a penalty for pulling it out almost immediately, canceling the saving. Avoid it by spacing your thresholds so a blob spends real time in the cheap tier before any later action, setting the delete age comfortably beyond the archive age rather than just past it. Archive carries the longest minimum, so it is where the penalty is largest and where threshold spacing matters most. Sanity-check every rule's threshold sequence against the tier minimums before enabling it.

### Q: Can a lifecycle definition run on a precise schedule, like deleting a blob at exactly midnight?

No, and using it that way is a mistake. Lifecycle management is built for steady-state, age-based hygiene, not precise timing. Because a rule acts on the platform's periodic evaluation cycle and only after the registration lag, there is no guarantee about the exact moment an in-scope, aged blob is tiered or deleted; it happens on a pass within the cycle, not at a clock time you choose. If you need an operation to happen at a precise instant, script it directly against the blob with the CLI, PowerShell, or an SDK, triggered by your own scheduler, rather than expressing it as a lifecycle policy entry. Reserve lifecycle rules for the large-scale, age-driven movement and expiry they excel at, where "sometime after the blob passes this age" is exactly the semantics you want, and keep precise, event-driven, or instant operations in code you control directly.

### Q: What account types support storage lifecycle management?

Lifecycle management policies apply to general-purpose v2 storage accounts and to premium block blob accounts, with the full set of tier actions reaching cool, cold, and archive available where the account supports those tiers. Legacy general-purpose v1 accounts do not participate in the same way, so the first step on an older account is to confirm or upgrade the account kind before authoring rules that would otherwise have nowhere to move blobs. Because account capabilities and the exact tiers supported evolve, treat the specific support matrix as something to verify against the current official documentation at the time you build rather than as a fixed constant. The practical takeaway is that a modern v2 or premium block blob account is the right foundation for lifecycle rules, and discovering an account is v1 explains why lifecycle options appear limited or absent in the portal blade.
