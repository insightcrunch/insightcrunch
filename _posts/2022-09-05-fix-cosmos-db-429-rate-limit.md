---
layout: post
title: "Fix Cosmos DB 429 Too Many Requests"
page_title: "Fix Cosmos DB 429 Too Many Requests: Diagnose RU Throttling vs Hot Partition and Apply the Right Fix"
date: 2022-09-05
categories: ["Technology"]
tags: ["Azure", "Cosmos DB", "429", "Troubleshooting", "Performance", "Cloud Computing"]
excerpt: "A Cosmos DB 429 Too Many Requests means a request outran available RU. Learn to tell a real throughput shortfall from a hot partition and fix the right one."
image: "/assets/images/blog/blog-21.webp"
reading_time: 60
author: "alex-cunningham"
last_updated: 2022-09-05
lang: en
---
A Cosmos DB 429 is the response code that says your request asked for more than the database was willing to serve in that instant. The status line reads `429 Too Many Requests`, the older SDKs surfaced it as `RequestRateTooLarge`, and the substatus that pins it to rate limiting is `3200`. Engineers meet it the moment a workload crosses from a demo into real traffic, and the reflex is almost always the same: open the throughput blade and slide the number up. Sometimes that works. Often it does nothing, the 429s keep coming, the monthly bill climbs, and the team is left staring at a graph that refuses to flatten. The reason is that a 429 has more than one cause, and only one of those causes is cured by buying more capacity.

![Diagnosing Cosmos DB 429 Too Many Requests root causes - Insight Crunch](/assets/images/blog/blog-21.webp)

The single most useful idea to carry into this problem is what we will call the RU-or-partition rule: a Cosmos DB 429 is either a genuine shortage of request units across the container, or it is a hot partition concentrating load on one physical slice of the data, and the metrics, not your intuition, decide which. Adding throughput before you have read the per-partition view is the most common wasted fix in the entire service, because no amount of provisioned capacity relieves a partition that is hot by design. Everything that follows is built to let you make that determination quickly, confirm it with a command or a metric rather than a guess, and then apply the remedy that matches the cause instead of the remedy that is easiest to reach.

This piece treats the 429 as a diagnostic problem first and a tuning problem second. We will read the error and the headers it carries, separate the three distinct conditions that all surface as the same code, give you a way to confirm each one against a signal you can see, walk the tested fix for each, and then close on the prevention that keeps the code from returning. If you want the model underneath all of this, the request-unit currency and the partition architecture are laid out in the [Cosmos DB engineering guide](/2022/02/14/azure-cosmos-db-engineering-guide/), and the deepest treatment of the hot-partition case lives in the companion troubleshooting piece on [RU throttling and hot partitions](/2022/09/12/fix-cosmos-db-ru-throttling/). This article is the entry point that tells you which door to walk through.

## What Cosmos DB 429 Too Many Requests Actually Means

Azure Cosmos DB does not charge you per query in the way a relational engine bills CPU time after the fact. It meters every operation up front in a normalized currency called the request unit, abbreviated RU. A point read of a small item costs a small, predictable number of RU. A write costs more. A query that scans and filters costs more still, scaling with the work the engine performs. You provision, or autoscale, a budget of request units per second, and the service spends from that budget as requests arrive. When the spend in a given window would exceed what is available, the engine does not queue the request indefinitely or silently degrade. It rejects the surplus immediately with `429 Too Many Requests` and tells the caller, through a response header, how long to wait before trying again.

That rejection is not an error in the sense of a bug. It is the database enforcing the contract you bought. The 429 is back-pressure, and back-pressure is a feature: it keeps a single noisy workload from starving the rest, and it gives a well-behaved client a precise instruction for when to retry. The trouble begins when an application treats the 429 as a hard failure, retries it in a tight loop without honoring the wait instruction, or responds to a steady drizzle of 429s by provisioning capacity it does not actually need. Reading the code correctly starts with knowing exactly what the engine is telling you and what it is not.

### What does the 429 substatus code 3200 tell me?

Substatus `3200` confirms the 429 is request-unit rate limiting rather than another throttle. Cosmos reuses the 429 status for a handful of conditions, so the substatus is the disambiguator. When you see 429 with 3200, the request exceeded the available RU for its target, and the server has attached a retry-after value telling the SDK precisely how long to back off.

The reason the substatus matters is that not every 429 is an RU problem. The service applies the same HTTP status to a small set of distinct throttles, and the substatus is how the engine names which one fired. The rate-limit substatus, `3200`, is the one this article is about and the one the overwhelming majority of real 429s carry. Other substatus values point at conditions such as a partition-level operation in flight or a metadata throttle on control-plane calls, and those are handled differently. Before you act on a 429, read the substatus, because acting on the assumption that every 429 is plain RU exhaustion is how teams end up tuning the wrong dial.

### Which response headers carry the diagnostic signal?

Three headers tell you almost everything. `x-ms-request-charge` reports the RU the operation consumed, `x-ms-retry-after-ms` gives the milliseconds the server wants you to wait, and the substatus inside the error names the throttle. Read all three before reacting, because the request charge often reveals an expensive operation hiding behind a capacity complaint.

The request-charge header is the one engineers most often overlook, and it is frequently the fastest path to the truth. If a single read is costing far more RU than a point lookup should, the document model or the query is the problem, not the throughput ceiling. The retry-after header is the instruction your retry logic must obey: a value in the tens of milliseconds signals brief contention, while values that climb and stay high signal a sustained shortfall or a saturated single partition. The substatus, as covered above, separates rate limiting from the other throttles. Together these three give you a reading of the failure before you have touched a single metric blade, and they cost nothing to capture because the SDK already receives them on every response.

## How to Read the Error and Gather the Diagnostic Signal

Diagnosis begins in two places: the response your application already receives, and the platform metrics Azure Monitor records whether or not you are watching. The application side is faster and is where you should start, because the headers travel with every request and require no portal navigation. The metrics side is where you confirm the shape of the problem across the whole container and, critically, across each physical partition. A disciplined reading uses the headers to form a hypothesis and the metrics to confirm or reject it, and it does so before any throughput change is made.

On the application side, instrument the request charge and the status on every Cosmos call you care about. In the .NET v3 SDK the charge is on the response object, and a 429 arrives as a `CosmosException` whose status code is 429 and whose `RetryAfter` property carries the server-suggested wait. Capturing these is a few lines and pays for itself the first time it tells you a query is costing two orders of magnitude more than you assumed.

```csharp
ItemResponse<Order> response = await container.ReadItemAsync<Order>(
    id, new PartitionKey(tenantId));

double charge = response.RequestCharge;        // RU this operation spent
Console.WriteLine($"Read cost {charge} RU");

// When the operation is throttled:
try
{
    await container.CreateItemAsync(order, new PartitionKey(order.TenantId));
}
catch (CosmosException ex) when ((int)ex.StatusCode == 429)
{
    // The server tells you exactly how long to wait.
    TimeSpan wait = ex.RetryAfter ?? TimeSpan.FromMilliseconds(50);
    Console.WriteLine($"Throttled. Server asked for {wait.TotalMilliseconds} ms");
}
```

The platform side lives in Azure Monitor metrics and in the diagnostic logs you route to a Log Analytics workspace. Two metrics carry most of the diagnostic weight. The first is the count of requests with status 429, which tells you that throttling is happening and at what rate. The second, and the one that separates the two root causes, is Normalized RU Consumption, which reports utilization as a percentage and, when you split it by partition key range, shows you whether the load is spread evenly or piled onto one slice. The whole RU-or-partition decision turns on that split, so it is worth setting up before you ever need it.

### How do I confirm 429s are happening from the logs?

Route Cosmos diagnostic logs to a Log Analytics workspace and query the data-plane requests table for status 429. A short KQL query grouped by time and collection shows the throttling rate and which container is affected, which confirms the problem is real and current rather than a stale alert or a one-off spike during a deploy.

```kusto
CDBDataPlaneRequests
| where TimeGenerated > ago(1h)
| where StatusCode == 429
| summarize Throttled = count()
    by bin(TimeGenerated, 5m), DatabaseName, CollectionName
| order by TimeGenerated desc
```

This query answers the first question any on-call engineer asks: is this still happening, and where. A count that rises and falls with traffic, then settles, points one way; a count pinned high and flat points another. Run it across a window wide enough to see the daily shape of your traffic, because a 429 pattern that tracks a nightly batch job tells a very different story from one that tracks user-facing peak hours. The table name and schema for resource-specific diagnostic logs change occasionally as the platform evolves, so confirm the current table and column names against the official diagnostic-logging documentation if a column does not resolve.

### How do I see whether the load is spread or concentrated?

Open the Normalized RU Consumption metric and split it by PartitionKeyRangeId. If every partition key range sits near the same high utilization, the container is genuinely short on throughput. If one range is pinned at 100 percent while the others idle, you have a hot partition, and adding RU will not move the throttling.

This single chart is the fork in the road. Normalized RU Consumption expresses how close a given partition key range is to its share of the provisioned budget, so a value near 100 percent on one range means that one slice of your data is doing all the work and has nothing left to give. Because Cosmos divides the container's throughput across its physical partitions, the budget belonging to an idle partition cannot be borrowed by the busy one. That is the mechanical reason the hot-partition case ignores extra capacity, and it is why this metric, split by range, is the most important single view in the entire diagnosis.

## The Three Root Causes Behind a Cosmos DB 429

Every rate-limit 429 reduces to one of three conditions, and they are genuinely different problems wearing the same status code. The first is a true throughput shortfall, where aggregate demand across the container simply exceeds the provisioned or available request units. The second is a hot partition, where the container has plenty of total RU but one physical partition is saturated because the data and access pattern concentrate there. The third is an expensive operation, where a single query or write is so costly in RU that even modest call volume overwhelms the budget. The fixes for the three do not overlap. Capacity solves the first, partition-key or query design solves the second, and query or model rework solves the third. Confusing them is how teams spend money without spending it well.

The InsightCrunch 429 cause table below is the findable artifact for this article: it maps each cause to the signal that confirms it and the fix that addresses it. Keep it next to the Normalized RU Consumption chart and you can resolve most 429 incidents in minutes rather than guessing across a maintenance window.

| Cause | What it is | How to confirm it is yours | The fix that works | The fix that fails |
|-------|-----------|----------------------------|--------------------|--------------------|
| True throughput shortfall | Aggregate RU demand exceeds the provisioned or available budget | Normalized RU Consumption high and even across all partition key ranges; 429 rate tracks traffic | Raise provisioned RU, enable autoscale, or lower per-operation RU | Repartitioning when capacity is the real ceiling |
| Hot partition | One physical partition saturated while others idle | Normalized RU near 100 percent on one PartitionKeyRangeId, low on the rest | Higher-cardinality, synthetic, or hierarchical partition key; spread writes | Adding RU; the idle partitions cannot lend their budget |
| Expensive operation | A single query or write costs far more RU than expected | High `x-ms-request-charge` per request; cross-partition or unindexed query | Add the partition key to the query, fix the indexing policy, reduce fan-out | Adding RU to absorb a query that should cost a fraction as much |

### Cause one: a genuine throughput shortfall

The simplest cause is also the only one that capacity fixes. Your workload is asking for more request units per second than the container has to give, the demand is spread reasonably evenly, and the budget is genuinely too small for the traffic. This is the case the throughput slider was built for, and when the metrics confirm it, raising the budget is the correct and complete answer.

Confirming a true shortfall means looking at Normalized RU Consumption across every partition key range and seeing roughly uniform high utilization, combined with a 429 rate that rises and falls with your traffic rather than staying pinned regardless of load. When demand is broadly distributed and every slice of the data is working near its ceiling at the same time, the container has simply outgrown its budget. The tell that distinguishes this from a hot partition is the evenness: a shortfall lights up the whole chart, while a hot partition lights up one line and leaves the rest dark. The tell that distinguishes it from an expensive operation is the request charge: in a true shortfall, individual operations cost what they should, and it is their volume, not their unit cost, that exhausts the budget.

The fix is to raise the available request units, and you have three ways to do it. You can increase manually provisioned throughput, which holds a fixed ceiling and bills for that ceiling whether or not you use it. You can switch to autoscale, which lets the container scale between ten percent and the maximum you set and bills for what it uses within that band, which suits spiky or unpredictable traffic. Or you can lower the RU each operation consumes so the same budget stretches further, which is the most durable fix because it reduces cost rather than raising it. The first two are reached with a single command.

```bash
# Inspect current throughput on the container
az cosmosdb sql container throughput show \
  --account-name <account> \
  --resource-group <rg> \
  --database-name <db> \
  --name <container>

# Raise manually provisioned throughput
az cosmosdb sql container throughput update \
  --account-name <account> \
  --resource-group <rg> \
  --database-name <db> \
  --name <container> \
  --throughput 10000
```

Switching to autoscale is a migration on the throughput offer rather than a simple number change, and it is reversible. Autoscale suits a workload whose peak is much higher than its average, because you pay for the band you actually touch rather than for a ceiling sized to the worst minute of the day.

```bash
# Move the container to autoscale throughput
az cosmosdb sql container throughput migrate \
  --account-name <account> \
  --resource-group <rg> \
  --database-name <db> \
  --name <container> \
  --throughput-type autoscale
```

The minimums that govern these offers, the manual floor for a container and the autoscale starting point and its scaling ratio, are platform values that have shifted over the life of the service, so confirm the current numbers against the official throughput documentation before you size a deployment around them. The decision logic, however, is stable: even and high utilization across all partitions means you are genuinely short, and capacity is the answer. The reliability of treating a 429 as something to retry rather than fail also matters here, and the cross-service view of that pattern is covered in the guide to [429 throttling across Azure services](/2023/04/03/fix-azure-429-throttling-guide/), because the same back-pressure contract appears far beyond Cosmos.

### Cause two: a hot partition that more capacity cannot relieve

The second cause is the one that punishes the throughput-slider reflex, and it is the reason the RU-or-partition rule exists. Cosmos DB distributes a container's provisioned throughput across its physical partitions. If a container has, say, ten physical partitions and a budget of ten thousand request units per second, each partition is entitled to roughly its share of that budget. When your data and your access pattern funnel most of the traffic onto one partition, that partition exhausts its share and starts returning 429s while the other nine sit nearly idle with budget they cannot lend. You can double the total throughput, and the hot partition's share doubles too, but if the access pattern is concentrated enough, the larger share still saturates, and you have paid twice as much to throttle just as often.

Confirming a hot partition is the entire point of the Normalized RU Consumption chart split by partition key range. One line pinned near 100 percent while the others sit low is the unambiguous signature. The diagnostic logs reinforce this: grouping throttled requests by PartitionKeyRangeId shows the 429s clustering on a single range rather than scattering across all of them.

```kusto
CDBDataPlaneRequests
| where TimeGenerated > ago(1h)
| where StatusCode == 429
| summarize Throttled = count() by PartitionKeyRangeId
| order by Throttled desc
```

When that query returns one range with thousands of throttles and the rest with a handful, you are looking at skew, and capacity is off the table as a remedy. The fix is to change what your data is partitioned on so that load spreads. A partition key with low cardinality, a status flag, a boolean, a coarse date bucket, or a single dominant tenant identifier, concentrates load by construction. The remedy is a key with high cardinality and even access: a more granular identifier, a synthetic key that combines fields to multiply distinct values, or a hierarchical key that partitions first by tenant and then by a finer dimension. The catch, and the reason this is the harder cause, is that the partition key is fixed when the container is created and cannot be changed in place. Spreading load onto a better key means writing the data into a new container, which is a migration rather than a setting change.

Because that migration is the real cost, the prevention is to choose the key correctly the first time, which is the subject of the configuration guide on [Cosmos DB partition keys](/2023/06/19/configure-cosmos-db-partition-keys/). The mechanics of locating and reasoning about a hot partition once you have one, including the per-partition metric reading and the re-key migration path, are the focus of the dedicated piece on [RU throttling and hot partitions](/2022/09/12/fix-cosmos-db-ru-throttling/). For the purpose of resolving a 429, the decisive move is the metric split: if one range is hot, stop reaching for the throughput slider and start reasoning about the key.

### Cause three: an operation that costs far more RU than it should

The third cause hides inside the request-charge header, and it is the one that gets missed because the symptom looks like a capacity problem from the outside. A single query that scans across partitions, filters on an unindexed path, or returns a large result set can cost tens or hundreds of times the RU of a point read. When such an operation runs even at modest frequency, it drains the budget and produces 429s that look exactly like a shortfall on the aggregate chart. The difference is visible only when you read what each operation actually costs.

Confirming an expensive operation means logging `x-ms-request-charge` per call and looking for the outliers. A point read of a single small item should cost a small, fixed amount. A query that includes the partition key and hits an indexed path should cost in proportion to the items it returns. When you find a request charging dramatically more than its peers, you have found the drain. The two usual culprits are a query that omits the partition key, forcing a fan-out across every physical partition, and a query that filters or sorts on a property the indexing policy does not cover, forcing a scan. The .NET SDK exposes query metrics that break the cost down further, which lets you separate index lookup from retrieval and confirm exactly where the RU went.

```csharp
var iterator = container.GetItemQueryIterator<Order>(
    new QueryDefinition(
        "SELECT * FROM c WHERE c.tenantId = @t AND c.status = @s")
        .WithParameter("@t", tenantId)
        .WithParameter("@s", "open"),
    requestOptions: new QueryRequestOptions
    {
        PartitionKey = new PartitionKey(tenantId)   // scope to one partition
    });

while (iterator.HasMoreResults)
{
    FeedResponse<Order> page = await iterator.ReadNextAsync();
    Console.WriteLine($"Page cost {page.RequestCharge} RU");
}
```

The fix follows the diagnosis. If the query fanned out because it lacked the partition key, scope it to the key as shown above so the engine touches one partition instead of all of them. If the query scanned because of an indexing gap, adjust the indexing policy to cover the filtered and sorted paths, accepting that a richer index costs more RU on writes in exchange for far cheaper reads. If the operation is a bulk import producing a 429 storm, enable the SDK's bulk mode so it batches and paces the writes rather than firing them all at once and tripping the limiter. The point is that none of these is solved by capacity. An operation that should cost a fraction as much should be made to cost a fraction as much, not absorbed by a bigger budget.

## Handling the Retry-After Header Correctly

A 429 is not a failure to surface to the user; it is an instruction to wait a stated interval and try again. The server attaches `x-ms-retry-after-ms` to every rate-limited response precisely so the client knows how long to pause. Honoring that value is the difference between a transient blip the user never notices and a cascading storm where impatient retries pile more load onto an already saturated target and make the throttling worse. The most damaging mistake in 429 handling is a tight manual retry loop that ignores the header and hammers the service the instant a request fails, because that loop converts back-pressure into a feedback loop.

The good news is that the official SDKs already do the right thing by default. The .NET, Java, Python, and JavaScript clients catch a rate-limited response, read the retry-after value, wait the prescribed interval, and try again, up to a configurable number of attempts and a configurable total wait budget. You generally do not need to write retry logic for 429 at all; you need to configure how patient the built-in logic should be and then let it work. The two knobs that matter cap how many times the client retries a throttled request and how long it will keep trying in total before giving up and surfacing the error.

```csharp
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    // How many times to retry a single rate-limited request
    MaxRetryAttemptsOnRateLimitedRequests = 9,

    // The total time budget across those retries before the error surfaces
    MaxRetryWaitTimeOnRateLimitedRequests = TimeSpan.FromSeconds(30)
});
```

Setting these well is a judgment call shaped by the workload. A user-facing read path wants a short total wait, because a request that cannot succeed within a second or two should fail fast and let the application degrade gracefully rather than hang. A background writer ingesting a batch can afford a generous wait budget, because completing eventually matters more than completing immediately, and a longer budget lets the built-in logic absorb a burst that would otherwise spill 429s to your code. The mistake to avoid in both cases is layering your own retry loop on top of the SDK's, because then a single logical operation can retry the retries, multiplying the load and the latency in ways that are hard to reason about. Configure the client, trust it to honor the header, and reserve your own handling for the case where the SDK exhausts its budget and the 429 genuinely escapes.

### Should I write my own retry loop for Cosmos 429?

In almost all cases, no. The SDK already catches the 429, reads the retry-after header, waits, and retries within the limits you configure. Writing a manual loop on top risks ignoring the header and amplifying load. Tune `MaxRetryAttemptsOnRateLimitedRequests` and the wait-time budget instead, and only handle the exception when the SDK gives up.

The reason this guidance is so firm is that hand-rolled retry logic almost never honors the server's wait instruction as faithfully as the built-in client does, and the failure mode is severe. A loop that retries immediately on 429 sends a fresh request into a target that just told it to wait, which consumes RU on the rejection itself and keeps the limiter tripped. Multiply that across many concurrent callers and the workload generates a self-sustaining throttle that no capacity increase can outrun, because the load is being manufactured by the retries rather than by the real work. The SDK's exponential, header-aware backoff exists specifically to break that loop, and the right posture is to let it do its job.

### How should bulk imports avoid a 429 storm?

Enable the SDK's bulk execution mode so it batches and paces writes against each partition rather than firing them all at once. A naive parallel loop of individual writes will trip the limiter immediately, while bulk mode groups operations by partition and respects the throughput budget, turning a 429 storm into a steady, efficient ingest.

```csharp
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    AllowBulkExecution = true
});
```

With bulk mode enabled, the recommended pattern is to create the write tasks and await them together, letting the SDK group them internally by physical partition and dispatch them at a rate the budget can sustain. This is dramatically more efficient than a hand-written loop that issues writes one at a time or floods the service with unbounded parallelism, and it is the correct tool whenever you are loading a container rather than serving live traffic. For a sustained ingest, you may still raise throughput temporarily for the duration of the load and lower it afterward, which pairs the capacity fix with the operational fix for a one-time event.

## Real-World 429 Scenarios and How Each Resolves

The three causes are clean in theory, and the field is where they get muddy, because a real incident often shows symptoms of more than one at once. The scenarios below are the recurring shapes that engineers report, each presented with the confirming signal that pins it down and the move that resolves it. Reading them as patterns rather than one-offs is what lets you recognize the next incident quickly, because production 429s rhyme even when they do not repeat exactly.

The first and most instructive scenario is the throttle that persists after a throughput increase. A team sees 429s, raises provisioned RU, and watches the rate barely change. The confirming signal is the Normalized RU Consumption chart: one partition key range pinned high while the rest stay low. This is the hot-partition case asserting itself against the capacity reflex, and the resolution is not more RU but a partition-key change that spreads the load, which means a migration to a new container with a higher-cardinality key. The lesson teams carry away is to check the per-partition split before the first throughput bump, not after the third.

The second scenario is the 429 storm during a bulk import. An ingestion job kicks off, fires thousands of writes in parallel, and the limiter trips within seconds, spilling 429s into the job's logs. The confirming signal is that the throttling is concentrated in time around the job rather than tracking user traffic, and the request charges are ordinary while the request rate is extraordinary. The resolution is to enable bulk execution so the SDK paces the writes, optionally paired with a temporary throughput raise for the duration of the load. This is a true shortfall in the narrow sense that demand briefly exceeds budget, but the right fix is to flatten the demand rather than permanently inflate the budget.

The third scenario is the retry that makes everything worse. An application catches the 429, retries immediately in a loop, and the throttling escalates instead of clearing. The confirming signal is a 429 rate that climbs after a brief spike rather than settling, and latency that balloons as requests stack up. The resolution is to remove the manual loop and let the SDK honor the retry-after header, which breaks the feedback cycle. Teams are often surprised that the fix is to do less, but the retry-after contract only works when the client respects it.

The fourth scenario is the cross-partition query that drains the budget. A reporting query or a poorly scoped lookup omits the partition key, fans out across every physical partition, and consumes far more RU per call than anyone estimated. The confirming signal is a high `x-ms-request-charge` on that specific query while point operations remain cheap. The resolution is to scope the query to the partition key where possible, or to fix the indexing policy so the filter and sort paths are covered, turning a scan into a seek. This is the expensive-operation case, and it is invisible until you read the per-operation charge.

The fifth scenario is autoscale flapping at its ceiling. A container on autoscale repeatedly hits the top of its band, scales no further, and returns 429s at the peak. The confirming signal is utilization riding the autoscale maximum during peaks while the 429s appear only at those peaks. The resolution is to raise the autoscale maximum if the peak demand is legitimate, or to address the per-operation cost if the peak is inflated by expensive queries. Autoscale removes the need to provision for the worst minute, but it does not remove the ceiling, and a workload that genuinely needs more at peak needs a higher band.

The sixth scenario is a single tenant or key dominating traffic in a multi-tenant container. One large customer's activity concentrates on the partition that holds their data, saturating it while smaller tenants on other partitions are untouched. The confirming signal is, once again, the per-partition split, with the heavy tenant's range hot and the rest cool. The resolution is a partitioning strategy that does not let one tenant monopolize a partition, such as a hierarchical key that subdivides the large tenant, which is a design change rather than a capacity change. Multi-tenant skew is the most common hot-partition cause in software-as-a-service workloads, and it is why tenant identifiers make tempting but dangerous partition keys.

### Why do 429s continue after I add throughput?

Because the cause is a hot partition, not a shortfall. Cosmos divides throughput across physical partitions, so when one partition is saturated by skewed access, adding total RU raises every partition's share but the hot one still saturates. The per-partition Normalized RU Consumption metric confirms it, and the fix is a better partition key, not more capacity.

This is the single most common surprise in the entire 429 experience, and it follows directly from the architecture. The provisioned budget is not a shared pool that the busiest partition can draw down at will; it is apportioned, and an idle partition's allocation is unavailable to a hot one. When you raise the container's throughput, you raise the allocation of every partition uniformly, including the eight or nine that did not need it. If the hot partition was receiving, for example, ninety percent of the traffic on ten percent of the budget, doubling the budget still leaves it receiving ninety percent of the traffic on twenty percent of the budget, which may still saturate. The arithmetic only works in your favor when the load is spread, and spreading the load is a key-design problem.

## Preventing Cosmos DB 429s from Returning

Prevention runs along the same three axes as the cure, and the order of effort is deliberate. The cheapest and most durable prevention is to keep per-operation RU low, because every request unit you do not spend is one you never have to provision or throttle. The next is to choose the partition key so that load spreads evenly across physical partitions from the first day, because a good key prevents the hot-partition class of 429 entirely and a bad one guarantees a painful migration later. The last, and the one to reach for only when the first two are sound, is to size the throughput, manual or autoscale, to the real demand with a sensible margin.

Keeping per-operation cost low is mostly a matter of modeling and indexing discipline. Point reads by id and partition key are the cheapest operation Cosmos offers, so a data model that lets the hot paths read by key avoids queries altogether for the most frequent access. Where queries are unavoidable, scoping them to a single partition and ensuring the filtered and sorted properties are indexed keeps their cost proportional to the result rather than the collection. The indexing policy is a lever in both directions: indexing everything makes reads cheap and writes expensive, while indexing nothing does the reverse, so tune the policy to the read and write mix the workload actually has. The model and indexing decisions that govern this are part of the broader treatment in the [Cosmos DB engineering guide](/2022/02/14/azure-cosmos-db-engineering-guide/), which is worth revisiting whenever a query charge surprises you.

Choosing the partition key well is the prevention with the highest leverage and the steepest cost of getting wrong, because the key cannot be changed in place. A key with high cardinality, a value with many distinct possibilities, gives Cosmos enough distinct logical partitions to spread across physical ones. A key whose access is even, where no single value receives a disproportionate share of reads and writes, keeps any one physical partition from running hot. And a key that aligns with the common query, appearing in the filter of the requests you run most, keeps those queries scoped to a single partition rather than fanning out. The full method for scoring a candidate key against these properties, and the cases where a synthetic or hierarchical key beats a natural one, is laid out in the guide to [configuring Cosmos DB partition keys](/2023/06/19/configure-cosmos-db-partition-keys/), which is the prevention article this troubleshooting piece points back to.

Sizing throughput is the last prevention and the one most teams reach for first, which is backwards. Once the per-operation cost is reasonable and the key spreads load, autoscale handles variable demand well by paying for the band you touch rather than the ceiling you fear, and manual throughput suits steady, predictable workloads where the average and the peak are close. The trap is to use capacity as a substitute for the other two preventions, sizing a container generously to mask a hot partition or an expensive query. That works until the bill arrives, and then it stops working, because you are paying continuously for a problem a one-time design fix would have solved.

### What is the cheapest durable way to prevent 429s?

Reduce the RU each operation consumes. Point reads by id and partition key are the cheapest path, scoped single-partition queries are next, and a tuned indexing policy keeps both efficient. Every RU you do not spend is one you never provision or throttle, which makes per-operation efficiency the prevention with the best long-term return.

The reason efficiency beats capacity as a prevention is compounding. A capacity increase raises your bill every hour for as long as it stays in place, while a modeling change that halves a hot query's cost pays back on every single execution forever, lowering both the throughput you need and the throttling you risk. Teams that treat RU per operation as a number to drive down, the way they would treat latency or error rate, rarely fight 429s at all, because they have removed the demand that produces them rather than buying capacity to absorb it.

## How Request Units Are Calculated and Why It Matters for 429s

Because a 429 is fundamentally about spending more request units than are available, understanding what drives the request-unit cost of an operation is the foundation under every fix in this article. The request unit is a normalized abstraction over the resources an operation consumes: processor time, memory, and the input and output the storage layer performs. Cosmos rolls those underlying costs into one number so you can reason about throughput in a single currency rather than juggling several. The abstraction is what lets you provision a budget and predict whether a workload fits inside it, and it is also what makes the cost of a careless query so easy to underestimate, because the underlying input and output a fan-out performs is invisible until the charge lands.

A point read, fetching one item by its id within its partition, is the cheapest operation and has a small, stable cost that barely moves with the size of the container. A write costs more than a read of the same item, and the cost rises with the number of indexed paths the write must update, which is the mechanism by which an over-broad indexing policy quietly inflates write cost. A query costs in proportion to the work the engine does to satisfy it: the number of partitions it touches, the volume it scans, the predicates it evaluates, and the result it returns. This is why the same logical question, asked with the partition key in the filter versus without it, can differ in cost by more than an order of magnitude. The first scopes the work to one slice of the data; the second spreads it across all of them.

The practical consequence for 429 work is that the request-charge header is not a curiosity but the most direct window into the third root cause. When you log the charge per operation and find a request costing far more than its neighbors, you have found a candidate for the expensive-operation bucket without touching a metric blade. The charge also lets you do capacity math honestly: if you know the RU cost of each operation type and the rate at which each runs, you can compute the throughput the workload actually needs rather than guessing, and you can predict whether a planned feature will fit the budget before it ships rather than after it pages someone.

### Why does the same query cost different RU at different times?

The cost of a query can vary because the data it touches changes: more matching items, a larger result page, a cold versus warm cache, or a partition that has split and now spreads the work differently. The request charge reflects the actual work performed for that execution, so a query over a growing dataset naturally costs more over time even when its text is unchanged.

This variability is why a workload that fit comfortably at launch can begin throttling months later without any code change. As a collection grows, a query that scans a range returns more items and evaluates more candidates, and its request charge climbs in step. A container that started on a single physical partition and has since split to several will execute a cross-partition query across more slices than it used to, raising the cost of the fan-out. None of this is a defect; it is the cost model faithfully reporting more work for more data. The lesson is to watch the request charge as a trend, not a one-time measurement, because the operation that was cheap enough to ignore at a thousand items may be the one draining the budget at a million.

### How do I estimate the throughput a workload needs?

Multiply each operation type's measured RU charge by its expected rate per second, sum across all operations, and add a margin for bursts and growth. Reading the actual charges from the response headers rather than estimating them turns capacity planning from guesswork into arithmetic, and it surfaces expensive operations that would otherwise hide inside an aggregate number.

The discipline here is to plan from measured costs rather than from intuition, because intuition consistently underestimates the price of queries and overestimates the price of point operations. Capture the request charge for each distinct operation your workload performs, weight each by how often it runs at peak, and you have a defensible throughput target instead of a number chosen by how a graph looked during an incident. The margin you add on top should account for the burstiness of real traffic and the steady growth of both data volume and request rate, but it should be a margin over a measured baseline, not a substitute for measuring at all. A workload sized this way rarely throttles unexpectedly, because the budget was derived from the demand rather than reverse-engineered from the symptoms.

## Physical and Logical Partitions: Where the Budget Actually Lives

The hot-partition cause makes no sense until you hold the right mental model of how Cosmos stores and scales data, so it is worth laying the architecture out plainly. A container's data is divided into logical partitions, one for each distinct value of the partition key. All items sharing a partition-key value live in the same logical partition, and a logical partition is the unit of transactional scope and of co-location. Logical partitions are themselves grouped onto physical partitions, the actual compute-and-storage units the service runs, and it is across these physical units that throughput is divided. This two-level scheme is the source of both the scalability Cosmos offers and the hot-partition trap it sets for the unwary.

The crucial fact is that throughput is apportioned to physical partitions, and the engine maps logical partitions to physical ones to balance storage. When the partition key has many distinct, evenly accessed values, the logical partitions spread across the physical ones and the load distributes naturally, so each physical unit carries a manageable slice of the total work. When the key has few distinct values, or one value dominates the traffic, the logical partitions pile onto a small number of physical units, and those units saturate while the rest stand idle. The budget belonging to the idle units is genuinely unavailable to the busy ones, because the apportionment is by physical partition, not by demand. This is the mechanical reason, repeated throughout this article, that capacity cannot cure skew.

Physical partitions are not static. As a logical partition grows in storage or as the container's throughput rises, the service splits a physical partition into two, redistributing the logical partitions between them. A split is a normal, automatic operation, but it has two consequences worth knowing. First, during and immediately after a split, you may observe transient behavior as the engine rebalances, including brief errors that the SDK is built to retry. Second, a split changes how a cross-partition query fans out, because there are now more physical units to involve, which can raise that query's cost. Knowing that splits happen, and that they are the platform scaling your data rather than malfunctioning, keeps you from misreading a transient rebalance as a fault.

### What is the difference between a logical and a physical partition?

A logical partition is all the items sharing one partition-key value, the unit of co-location and transactional scope. A physical partition is the underlying compute-and-storage unit that hosts many logical partitions and receives a share of the container's throughput. You design for logical partitions through the key; the service manages physical partitions for you, dividing throughput across them.

The reason the distinction matters for 429 diagnosis is that the Normalized RU Consumption metric reports utilization per physical partition, exposed as the partition key range, while your design choices operate at the logical level through the key. When you see one partition key range hot, you are seeing one physical unit saturated, and the cause is that the logical partitions it hosts, determined by your key, are carrying too much of the load. The fix lives at the logical level, in the key design, even though the symptom appears at the physical level in the metric. Holding both levels in mind at once is what lets you connect a hot range on a chart to a low-cardinality key in your schema and reason from one to the other.

### Why can't I just change the partition key to fix a hot partition?

The partition key is fixed when the container is created and cannot be altered in place, because the entire physical layout of the data depends on it. Spreading load onto a better key requires writing the data into a new container with the new key, a migration rather than a configuration change, which is exactly why choosing the key well at design time has such high leverage.

This irreversibility is the single hardest constraint in Cosmos design and the reason the partition key deserves more thought than any other early decision. Everything downstream, how load distributes, which queries are cheap, whether a hot partition can form, follows from the key, and none of it can be revised without moving the data. Teams that treat the key as a detail to settle quickly often pay for it later with a migration under pressure, copying a live container into a new one while keeping both consistent during the cutover. Teams that treat it as the foundational decision it is, scoring candidate keys against cardinality, access evenness, and query alignment before a single item is written, rarely face that migration at all. The cost asymmetry between getting it right up front and fixing it later is enormous, and it is why the prevention article on partition keys is the most valuable companion to this one.

## Monitoring and Alerting on 429s Before They Page You

Diagnosing a 429 during an incident is reactive, and the better posture is to see the throttling building before it becomes a page. Cosmos surfaces everything you need for proactive monitoring through Azure Monitor metrics and through the diagnostic logs you route to a Log Analytics workspace, and a small amount of setup turns a 3 a.m. surprise into a daytime adjustment. The two signals to watch are the rate of 429 responses and the Normalized RU Consumption, the same two that drive reactive diagnosis, now used to catch the trend rather than the crisis.

A metric alert on the count of throttled requests is the first line of defense. Set it to fire when the 429 rate over a short window crosses a threshold meaningful for your workload, low enough to give you warning and high enough to ignore the occasional transient throttle that the SDK retries invisibly. Pair it with a second alert on Normalized RU Consumption crossing a high utilization threshold, because rising utilization is the leading indicator that a shortfall is approaching, often visible before the 429s themselves become significant. The two alerts together catch both the symptom and its precursor, and they let you act during business hours rather than in response to a user-facing failure.

The diagnostic logs give you the depth the metrics lack. Routed to Log Analytics, the data-plane request records let you slice throttling by collection, by partition key range, by operation type, and by time, which is exactly the breakdown you need to tell the three causes apart. A scheduled query that summarizes the previous day's 429s by partition key range, for instance, surfaces a forming hot partition while it is still a slow leak rather than a flood. The query below groups throttled requests by range and operation so a daily review shows both whether throttling is concentrating on one slice and which operation type is driving it.

```kusto
CDBDataPlaneRequests
| where TimeGenerated > ago(1d)
| where StatusCode == 429
| summarize Throttled = count()
    by PartitionKeyRangeId, OperationName
| order by Throttled desc
```

### What metric should I alert on for Cosmos throttling?

Alert on the count of 429 responses over a short window as the direct symptom, and add a second alert on Normalized RU Consumption crossing a high threshold as the leading indicator. The first tells you throttling is happening now; the second warns you that utilization is climbing toward the ceiling before the throttling becomes severe enough to affect users.

The value of the two-alert approach is that it separates urgency from warning. A spike in the 429 count means you have a problem in flight and need to decide quickly whether it is a transient burst, a shortfall, or a hot partition. A sustained climb in Normalized RU Consumption, by contrast, is a forecast: it tells you the workload is growing into its budget and that a shortfall is coming unless you raise capacity or reduce demand. Acting on the forecast is far cheaper and calmer than acting on the crisis, because you can plan a throughput change or a query optimization rather than scramble. Teams that watch the leading indicator rarely get paged for the symptom, because they have addressed the trend before it became an event.

### How do I review for a forming hot partition proactively?

Run a scheduled query that summarizes recent 429s grouped by partition key range and review it regularly. A range that begins accumulating disproportionate throttling while others stay quiet is a hot partition forming, and catching it early, while it is a slow trend rather than a saturation, gives you time to plan a key change before it becomes an emergency migration.

This proactive review is the difference between a planned remediation and a forced one. A hot partition rarely appears fully formed; it grows as one tenant scales, one key value accumulates traffic, or one access pattern intensifies. The per-range throttling summary, reviewed on a cadence, shows that growth as a trend you can act on deliberately, scheduling the migration to a better key during a maintenance window of your choosing. The alternative, discovering the hot partition only when it saturates and pages someone, forces the same migration under pressure with users affected. The work is identical; only the timing and the stress differ, and the scheduled review is what lets you choose the calm version.

## A Reproducible Walkthrough: Triggering and Resolving Each Cause

The fastest way to make the RU-or-partition rule reflexive is to produce each cause deliberately in a throwaway container and watch the metrics and headers respond, because a 429 you created on purpose teaches more than a dozen you read about. The walkthrough below describes how to provoke each of the three causes and confirm the signal that identifies it, using a small container you can create and delete in minutes. Treat it as a lab rather than a script to paste, adapting the specifics to your account, and use it to build the instinct that turns an incident into a quick decision.

To provoke a true shortfall, create a container with a deliberately small manual throughput and a partition key that spreads load well, then drive a steady, evenly distributed read-and-write workload across many distinct key values at a rate that exceeds the budget. Watch two things: the Normalized RU Consumption chart, which should light up roughly evenly across all partition key ranges, and the request-charge header on the operations, which should report ordinary, expected costs. The combination, even utilization and ordinary per-operation cost, is the signature of a shortfall. Raise the throughput, and the 429s should subside in proportion, confirming that capacity was the correct lever. This is the case the slider was built for, and seeing it behave as expected anchors your sense of what a real shortfall looks like.

To provoke a hot partition, create a container with a low-cardinality partition key, a status flag or a single dominant value, and drive load that concentrates on that value. The Normalized RU Consumption chart should now show one partition key range climbing toward saturation while the others stay low, and the per-range throttling query should cluster the 429s on that single range. Now perform the instructive step: raise the container's throughput and watch the hot range stay hot. The 429s persist because the idle ranges cannot lend their enlarged budget to the saturated one. Nothing teaches the futility of the capacity reflex against skew as vividly as watching the slider move and the throttling refuse to follow. The resolution, recreating the container with a high-cardinality key and reloading the data, then spreads the load and clears the throttling, demonstrating that the key, not the budget, was the lever.

To provoke an expensive operation, populate the container with enough data that a query matters, then run a query that omits the partition key so it fans out across every physical partition, or one that filters on a property excluded from the indexing policy so it scans. Log the request charge on that query and compare it to a point read of the same data. The query should charge dramatically more, and at a modest call rate it should produce 429s even though point operations remain cheap and the aggregate utilization looks unremarkable. Scope the query to the partition key, or extend the indexing policy to cover its paths, and the charge should fall sharply, the throttling clearing without any change to throughput. This is the case that hides from the aggregate chart and reveals itself only in the per-operation charge, and producing it once makes the habit of logging that charge stick.

### What is the fastest way to confirm which cause I have?

Read three things in order: the per-partition Normalized RU Consumption chart, the per-operation request charge, and the 429 rate over time. Even utilization with ordinary charges and traffic-tracking 429s means a shortfall; one hot range means a hot partition; an outlier charge means an expensive operation. Two minutes of reading these settles almost every incident.

The ordering is deliberate because it eliminates the most expensive mistake first. Checking the per-partition split before anything else rules in or out the hot-partition case, which is the one that wastes the most money when misdiagnosed, since it is the case where the capacity reflex fails silently. Reading the per-operation charge next catches the expensive query that would otherwise masquerade as a shortfall on the aggregate view. And watching whether the 429 rate tracks traffic or stays pinned distinguishes a transient burst from a sustained condition. Run through the three in that sequence and you will rarely apply the wrong fix, because each step removes a class of error before you reach the decision. The discipline is cheap, the signals are already being recorded, and the payoff is a remediation chosen on evidence rather than reflex.

## Manual, Autoscale, and Serverless: Matching the Throughput Mode to the 429 Risk

The throughput mode you choose shapes when and how a 429 appears, and matching the mode to the workload's shape is a prevention in its own right. Cosmos offers manually provisioned throughput, autoscale, and serverless, and each makes a different trade between cost predictability and elasticity. None of them eliminates the 429 mechanism, but the wrong mode for a given traffic pattern makes throttling more frequent or more expensive than it needs to be, while the right one absorbs the workload's natural variability without either over-paying or throttling at peak.

Manual throughput holds a fixed ceiling and bills for that ceiling continuously, whether the workload uses it or not. It suits steady, predictable traffic where the average and the peak are close, because a fixed budget sized to a flat demand wastes little. Its failure mode for 429s is the predictable one: when demand rises above the fixed ceiling, the container throttles until you raise it. For a workload that genuinely runs flat, manual is the cheapest and simplest choice, because elasticity you never use is elasticity you should not pay for. For a workload with sharp peaks, manual forces a painful choice between provisioning for the peak and paying for it around the clock, or provisioning for the average and throttling at the peak.

Autoscale resolves that tension for variable workloads by scaling within a band, typically between a tenth of the maximum and the maximum, and billing for the highest throughput used within each hour rather than for the ceiling. It suits spiky or unpredictable traffic, because it rises to meet a peak and falls back during quiet periods, so you neither throttle at the peak nor pay peak rates during the trough. Its limits are two: it still has a maximum, so a peak above the band throttles until you raise the maximum, and it scales the whole container uniformly, so it does nothing for a hot partition. Autoscale is the right default for most workloads whose demand varies meaningfully across the day, and it removes the most common manual-mode 429, the one that fires because nobody raised the fixed ceiling before traffic grew.

Serverless bills purely per operation with no provisioned budget at all, which suits intermittent, low-to-moderate, or unpredictable workloads such as development environments and applications with long idle stretches. Because there is no provisioned ceiling, the 429 dynamics differ: serverless has its own throughput limits per container that the platform enforces, and a workload that grows beyond what serverless is designed for should migrate to provisioned or autoscale. Serverless shines when paying for a provisioned budget that sits mostly idle would be wasteful, and it removes the question of sizing entirely for workloads small or sporadic enough to fit. The specific throughput ceilings and the boundaries where serverless stops being the right fit are platform values that evolve, so confirm them against the current documentation when a serverless container begins to throttle, because that throttling is usually the signal that the workload has outgrown the mode.

### Which throughput mode reduces 429s for spiky traffic?

Autoscale is the best fit for spiky traffic, because it raises throughput to meet a peak and lowers it during quiet periods, billing for what each hour actually uses. It removes the most common manual-mode 429, the one caused by a fixed ceiling that nobody raised before demand grew, without forcing you to pay peak rates around the clock.

The reason autoscale suits variability so well is that it decouples the throughput you pay for from the throughput you provision for the worst case. Under manual throughput, a workload that doubles its demand for two hours a day either throttles during those hours or pays for the doubled capacity for all twenty-four. Autoscale lets the same workload ride up to the peak when it needs to and settle back when it does not, so the bill tracks the demand curve rather than its maximum. The one thing to remember is that the band has a top, and a legitimate peak above the band still throttles, so size the maximum to the real peak with a margin. Used that way, autoscale turns the variable-demand 429 from a recurring incident into a non-event.

## SDK and Client Choices That Shape 429 Behavior

Beyond throughput and partitioning, several client-side choices influence how often a 429 appears and how gracefully it is handled, and getting them right is low-cost insurance against avoidable throttling. The connection mode, the consistency level, and whether the client routes requests with awareness of the partition key all affect the request-unit cost and the latency profile of a workload, and therefore the pressure it puts on the budget. These are not substitutes for correct partitioning or sizing, but they are easy wins that compound with the structural fixes.

Connection mode governs how the client talks to the service. Direct mode connects to the partitions handling the data more efficiently for most workloads, lowering latency and letting a given budget serve more requests per second, while gateway mode routes through an intermediate layer that is simpler in constrained network environments but generally less efficient for high-throughput, latency-sensitive paths. For a workload pushing enough volume to flirt with 429s, direct mode is usually the better choice, because the lower latency means requests complete and release their share of the budget faster, which in turn means the same provisioned throughput sustains a higher effective request rate. The choice interacts with your network topology, so confirm direct mode is reachable in your environment before assuming it.

Consistency level shapes request-unit cost in a way that surprises teams who default to the strongest setting without needing it. Stronger consistency guarantees cost more in request units and can cost more in latency, because the engine does more work to satisfy the stronger guarantee, while more relaxed levels cost less and serve more requests from the same budget. A workload that defaults to the strongest consistency it can get, without a requirement that demands it, pays a continuous RU premium that brings 429s closer, and relaxing the level to what the application actually needs can lower the pressure measurably. The right level is a correctness decision first, but where the application can tolerate a more relaxed guarantee, choosing it is also a throughput decision that reduces the cost of every read.

Partition-key-aware routing is the quiet efficiency that ties back to everything else. When the client knows the partition key for an operation, as it does for a point read or a scoped query, it can route the request directly to the partition that holds the data rather than involving others, which keeps the operation cheap and the load where it belongs. Supplying the partition key on every operation that has one, reads, writes, and scoped queries alike, is the simplest habit that keeps per-operation cost low and avoids the accidental fan-out that produces the expensive-operation 429. It costs nothing to supply the key you already know, and it is the difference between an operation touching one slice of the data and an operation touching all of them.

### Does the consistency level affect Cosmos DB 429s?

Yes, indirectly but measurably. Stronger consistency levels cost more request units per operation than relaxed ones, so a workload defaulting to the strongest setting without needing it spends more of its budget on every read, bringing 429s closer. Choosing the consistency level the application actually requires, rather than the strongest available, lowers per-operation cost and the throttling pressure that follows.

The interaction matters because consistency is often set once and forgotten, defaulted to a strong guarantee on the reasoning that stronger is safer. Stronger is indeed safer for correctness, but it is not free, and on a read-heavy workload the request-unit premium of an unnecessarily strong level adds up to real throughput the budget could have spent serving more traffic. The discipline is to treat consistency as a deliberate choice driven by what the application's correctness genuinely demands, then to recognize that whatever headroom a more relaxed level allows is headroom against 429s as well. Where the workload can tolerate a relaxed guarantee, the relaxation pays twice, in lower cost and in throttling avoided, and where it cannot, the stronger level is simply the price of correctness and should be sized for rather than fought.

## Failures Often Confused with a Cosmos DB 429

A 429 lives in a small family of Cosmos responses that engineers conflate under stress, and telling them apart saves real time. The most important distinction is between the rate-limit 429 and other conditions that either share the status code under a different substatus or produce superficially similar symptoms. Knowing the neighbors keeps you from applying a 429 remedy to a problem that is not a 429 at all.

The closest neighbor is the request timeout, surfaced as a 408 or as a client-side timeout, which can appear during the same incident as 429s and feels like the same thing to a user. A timeout means the operation did not complete in the allotted window, which can happen when a partition is so saturated that even retried requests cannot get through, but the timeout is a symptom of contention rather than the rate-limit signal itself. The fix for the underlying contention is the same partition or capacity work, but the diagnostic path differs because a timeout does not carry the request-charge and retry-after story a 429 does.

A second neighbor is the concurrency conflict, which Cosmos surfaces when an optimistic-concurrency write loses a race, distinct from rate limiting and resolved by a retry of the read-modify-write rather than by capacity or partitioning. It shares the general flavor of a request the server declined, but the cause and the cure have nothing to do with throughput. Confusing a concurrency conflict with a 429 leads to provisioning capacity that does nothing, because the conflict is about contention on a single item, not about the rate of requests.

A third neighbor sits outside Cosmos entirely: the 429s that other Azure services return under their own throttling contracts. Storage, the management plane, and several data services apply the same status code with their own retry-after semantics, and an application that talks to several of them can see 429s that have nothing to do with Cosmos at all. The cross-service pattern, and the shared discipline of honoring retry-after wherever it appears, is the subject of the broader guide to [429 throttling across Azure services](/2023/04/03/fix-azure-429-throttling-guide/), which is the right reference when a 429 in your logs turns out to originate somewhere other than the database. The discipline is the same, but the dial you turn lives in a different service.

## The Verdict on Fixing Cosmos DB 429 Too Many Requests

The whole of this article reduces to one habit: read the metrics before you reach for the throughput slider. A Cosmos DB 429 is the database enforcing the contract you bought, and it has three distinct causes that wear the same code. A true shortfall, confirmed by even, high utilization across every partition, is the one capacity fixes. A hot partition, confirmed by one partition key range pinned while the rest idle, is a key-design problem that more capacity only makes more expensive. And an expensive operation, confirmed by a request charge far above its peers, is a query or model problem that no budget should be asked to absorb. The RU-or-partition rule, paired with the per-operation charge, sorts almost every incident into the right bucket in minutes.

The retry-after header is the contract that makes 429s survivable, and the right posture is to configure the SDK's built-in retry generously enough for the workload and then trust it, rather than hand-rolling a loop that ignores the server's instruction and amplifies the load. Prevention runs cheapest first: drive down per-operation RU, choose a partition key that spreads load before the container ever exists, and size throughput to real demand only once the first two are sound. A team that internalizes this order rarely fights 429s, because it has removed the conditions that produce them. To go deeper on the hot-partition mechanics, follow the dedicated piece on [RU throttling and hot partitions](/2022/09/12/fix-cosmos-db-ru-throttling/); to prevent the problem at the source, work through [configuring Cosmos DB partition keys](/2023/06/19/configure-cosmos-db-partition-keys/).

The deeper habit underneath all of this is to treat request units the way a mature team treats latency and error rate: as a first-class metric you watch, attribute, and drive down rather than a bill you tolerate. A workload whose owners know the RU cost of every hot path, watch the per-partition split as a matter of routine, and review for forming skew on a cadence almost never meets a 429 it did not anticipate. The throttling that remains is the limiter protecting the workload during genuine bursts, which is the system working as designed. Reaching that state is not a matter of buying more capacity; it is a matter of understanding where the capacity goes, and the metrics that reveal that are already being recorded whether or not anyone is reading them.

When you are ready to reproduce these conditions and watch the metrics respond, [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to drive a 429, raise throughput, and observe whether the per-partition chart flattens or stays skewed. To sharpen the diagnostic instinct under realistic pressure, [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html), which present the RU-versus-partition decision as timed scenarios so the metric reading becomes reflex rather than recollection.

## Frequently Asked Questions

### Q: What does Cosmos DB 429 Too Many Requests mean?

A 429 Too Many Requests from Cosmos DB means a request asked for more request units than were available in that instant, and the engine rejected the surplus rather than queuing it. Cosmos meters every operation in request units and spends from a provisioned or autoscaled per-second budget; when the spend would exceed what is available, the server returns 429 with a retry-after header telling the client how long to wait. The rate-limit form carries substatus 3200. It is not a bug or a hard failure but back-pressure, the database enforcing the throughput contract you bought. The correct response is to honor the wait and retry, and, if the throttling persists, to diagnose whether the cause is a genuine shortfall, a hot partition, or an expensive operation before changing anything.

### Q: Does exceeding provisioned RU cause a 429?

Yes, exceeding the available request units is the direct trigger for a rate-limit 429, but the word available hides the important nuance. The budget is not a single shared pool; it is apportioned across the container's physical partitions. You can be far below your total provisioned throughput and still get 429s if one physical partition has exhausted its share while others sit idle. That is the difference between a true shortfall, where aggregate demand exceeds aggregate budget evenly, and a hot partition, where one slice saturates regardless of headroom elsewhere. So exceeding provisioned RU causes a 429, but you have to ask exceeding it where: across the whole container, which capacity fixes, or on one partition, which only a better key fixes. The Normalized RU Consumption metric split by partition key range answers that question.

### Q: How do I handle the Cosmos 429 retry-after header?

Read the `x-ms-retry-after-ms` value and wait at least that long before retrying, which is exactly what the official SDKs do for you by default. Rather than writing your own retry loop, configure the client's built-in retry through the maximum attempts on rate-limited requests and the maximum total wait time, then let the SDK honor the header and back off automatically. A user-facing path should set a short total wait so it fails fast and degrades gracefully, while a background writer can afford a longer budget so a transient burst is absorbed. The mistake to avoid is a manual loop that retries immediately and ignores the header, because it sends fresh requests into a target that just asked for a pause, consuming RU on the rejections and sustaining the throttle. Trust the SDK, tune its patience, and only handle the exception when it exhausts its budget.

### Q: Does autoscale throughput fix Cosmos 429s?

Autoscale fixes 429s only when the cause is a genuine, variable shortfall. It lets a container scale within a band, typically between a tenth of the maximum and the maximum you set, and bills for what it uses within that range, which suits spiky traffic far better than a fixed ceiling. But autoscale still has a ceiling, so a workload whose legitimate peak exceeds the band will hit the top and return 429s anyway, and raising the maximum is then the fix. More importantly, autoscale does nothing for a hot partition, because it scales the whole container's budget uniformly and the saturated partition's larger share may still saturate. And it does nothing for an expensive query, which should be made cheaper rather than absorbed by a bigger band. Use autoscale to handle variable demand, not to mask a partition or query problem.

### Q: Can a hot partition cause 429 even with spare RU?

Yes, and this is the most common surprise in the entire 429 experience. Cosmos divides a container's provisioned throughput across its physical partitions, and an idle partition cannot lend its allocation to a busy one. If your data and access pattern concentrate load on a single partition, that partition exhausts its share and returns 429s while the container as a whole shows plenty of unused budget. The aggregate throughput chart looks healthy, but the per-partition Normalized RU Consumption chart shows one range pinned at 100 percent and the rest idle. Adding total throughput raises every partition's share uniformly, including the ones that did not need it, so if the access is skewed enough the hot partition still saturates. The only real fix is a partition key that spreads load, which means a migration because the key is fixed at container creation.

### Q: How does the Cosmos SDK retry 429 responses?

The official SDKs catch a rate-limited 429, read the server's `x-ms-retry-after-ms` header, wait the prescribed interval, and retry the request, repeating up to a configurable number of attempts or until a configurable total wait budget is spent. In the .NET v3 client these are the maximum retry attempts on rate-limited requests and the maximum retry wait time on rate-limited requests, and similar options exist in the Java, Python, and JavaScript clients. The retry is header-aware rather than a fixed interval, so it backs off in step with what the server actually asks for, which is what keeps a transient burst from escalating. Because this logic is built in and correct, you should configure its patience to suit the workload and otherwise leave it alone, surfacing the 429 to your own code only in the rare case where the SDK exhausts its budget and the throttling genuinely persists.

### Q: What is the difference between a 429 and a 408 in Cosmos DB?

A 429 means the request was rejected because it exceeded available request units, and it carries a retry-after instruction and a request charge that tell the diagnostic story. A 408 means the request did not complete within its time window, a timeout rather than a rate limit. The two can appear in the same incident, because a partition saturated enough to throttle heavily can also leave some requests unable to complete in time, but they are distinct signals with distinct diagnostics. A 429 points you at the throughput and partition story directly through its headers, while a 408 points at contention or a slow operation and is read through latency and the operation's own behavior. Treat a 429 as back-pressure to honor and a 408 as a sign to investigate why an operation is taking too long, often a saturated partition or an expensive query underneath.

### Q: How do I find which query is consuming the most RU?

Instrument the `x-ms-request-charge` header, exposed as the request charge on every SDK response, and log it per operation so the outliers stand out. A point read of a small item costs a small, fixed amount, so any operation charging dramatically more is a candidate. For queries, the SDK also exposes query execution metrics that break the cost into index lookup and document retrieval, letting you see whether the expense comes from a fan-out across partitions or a scan over unindexed paths. The two usual culprits are a query that omits the partition key, which forces every physical partition to participate, and a filter or sort on a property the indexing policy does not cover. Once you have identified the costly query, scope it to the partition key where possible or extend the indexing policy to cover its paths, turning an expensive scan into a cheap seek.

### Q: Will raising RU stop 429s during a bulk import?

Raising throughput helps a bulk import only as a temporary measure, and it is not the primary fix. A bulk load that fires thousands of writes in unbounded parallelism trips the limiter because demand briefly outruns budget, but the durable remedy is to pace the writes rather than permanently inflate the budget. Enable the SDK's bulk execution mode, which groups operations by physical partition and dispatches them at a rate the throughput can sustain, turning a 429 storm into a steady ingest. You can pair this with a temporary throughput raise for the duration of the load and lower it afterward, which addresses the brief shortfall without leaving a permanently oversized, continuously billed container behind. The combination of bulk mode and a time-boxed capacity bump handles large one-time loads cleanly, while bulk mode alone often suffices for routine ingestion.

### Q: How do I tell a throughput shortfall from a hot partition?

Open the Normalized RU Consumption metric and split it by partition key range. If every range sits near the same high utilization, demand is spread and the container is genuinely short on throughput, which capacity fixes. If one range is pinned near 100 percent while the others idle, you have a hot partition, and adding throughput will not move the throttling because the idle partitions cannot lend their budget. The 429 rate reinforces the reading: a shortfall produces throttling that rises and falls with traffic, while a hot partition produces throttling that persists regardless of how much you scale. Grouping throttled requests in the diagnostic logs by partition key range id provides the same answer from a different angle, showing the 429s clustering on one range rather than scattering. This single comparison, even versus concentrated, is the fork that decides every 429 remedy.

### Q: Does a cross-partition query waste RU and cause 429s?

A cross-partition query can consume far more request units than a scoped one, and at any meaningful frequency it can produce 429s that masquerade as a capacity shortfall. When a query omits the partition key, the engine must fan the work out to every physical partition, gather the partial results, and merge them, which multiplies the cost by the number of partitions involved. The symptom is a high request charge on that specific query while point operations stay cheap, visible only if you log the per-operation charge. The fix is to include the partition key in the query so the engine touches a single partition, or, when a cross-partition query is genuinely necessary, to ensure the filtered and sorted paths are indexed so each partition does the minimum work. Treating the query as something to make cheaper is correct; adding throughput to absorb a needlessly expensive fan-out is not.

### Q: What is the RU-or-partition rule for 429s?

It is the diagnostic heuristic that a Cosmos DB 429 is either a genuine shortage of request units across the whole container or a hot partition concentrating load on one physical slice, and that the metrics, not your intuition, decide which. The rule exists to interrupt the reflex of raising throughput the moment a 429 appears, because that reflex cures only the first cause and wastes money on the second. You apply it by reading Normalized RU Consumption split by partition key range before changing any setting: even and high means shortfall and capacity is the answer, while one range hot and the rest idle means a partition problem and a key change is the answer. Adding a third check on per-operation request charge catches the expensive-query case that hides inside both. The rule turns a 429 from a vague capacity worry into a quick, evidence-based decision.

### Q: Can a single tenant cause 429s in a multi-tenant container?

Yes, and it is the most common hot-partition cause in software-as-a-service workloads. When a container is partitioned by tenant identifier, all of one tenant's data lands on the partition that holds that key value. A large or unusually active tenant then concentrates reads and writes on that single partition, saturating its share of the throughput while smaller tenants on other partitions are untouched. The aggregate throughput looks healthy, but the per-partition chart shows the heavy tenant's range hot. Because the partition key cannot be changed in place, the remedy is a partitioning strategy that prevents any one tenant from monopolizing a partition, such as a hierarchical key that subdivides large tenants by a finer dimension. This is why a bare tenant identifier is a tempting but risky partition key, and why multi-tenant designs need to plan for the largest tenant from the start rather than the average one.

### Q: Is a Cosmos DB 429 ever something I should let fail?

In most cases a 429 should be retried, not failed, because it is a transient instruction to wait rather than a permanent error, and the SDK's built-in retry handles it transparently. The exception is a latency-sensitive, user-facing path where waiting through several retries would itself break the experience; there, a short total retry budget that fails fast and lets the application degrade gracefully is the better choice, because a slow success can be worse than a quick, well-handled failure. The judgment turns on what the caller can tolerate: a background writer should retry patiently, while an interactive read should bound its wait tightly. What you should never do is fail a 429 immediately without any retry, because that surfaces transient back-pressure as a user-visible error, nor retry it forever, because that can mask a real shortfall or hot partition that needs a structural fix.

### Q: How long does a Cosmos DB 429 condition usually last?

The duration of any single 429 is exactly the retry-after value the server returns, often in the tens of milliseconds for brief contention, after which the retried request typically succeeds. The duration of a 429 condition, the period over which throttling keeps recurring, depends entirely on the cause. A transient burst against a healthy container clears as soon as demand drops below budget, sometimes within seconds. A true shortfall persists for as long as demand exceeds the provisioned budget, clearing only when you raise capacity or demand falls. A hot partition persists indefinitely under the same access pattern, because no passage of time spreads a skewed key, which is why it requires a structural fix rather than patience. Reading whether the 429 rate settles on its own or stays pinned is itself diagnostic: self-clearing points at a transient burst, while persistent points at a shortfall or a hot partition.

### Q: Does the indexing policy affect Cosmos DB 429s?

Indexing policy affects 429s indirectly but meaningfully, because it shapes how many request units reads and writes consume. A policy that indexes the properties your queries filter and sort on makes those queries cheap, often turning a costly scan into an efficient seek and lowering the RU pressure that produces 429s. The same policy, however, makes writes more expensive, because every indexed path must be updated when an item changes, so an over-broad index can raise write cost enough to trigger throttling on a write-heavy workload. The right policy matches the read and write mix the workload actually has: index what you query, exclude paths you never filter on, and watch the request charge on both reads and writes as you tune. Treating indexing as a free default in both directions is a common source of avoidable RU cost and, by extension, avoidable 429s.

### Q: Can I prevent 429s entirely, or only manage them?

You can prevent the structural causes of 429s entirely and reduce the transient ones to rare, self-clearing events, but you cannot and should not eliminate the 429 mechanism itself, because it is the back-pressure that protects the workload. Prevention means removing the conditions that produce sustained throttling: choose a partition key that spreads load so no hot partition can form, keep per-operation RU low through point reads and tuned indexing so the budget stretches, and size throughput to real demand with a sensible margin. Do those three and a healthy container may go for long stretches without a single sustained 429, seeing only the occasional transient one that the SDK retries invisibly. What remains is the limiter doing its job during genuine bursts, and that is desirable, not a defect. The goal is a container where every 429 is either transient and self-handled or a true signal that demand has outgrown a correctly sized budget.
