---
layout: post
title: "Fix Cosmos DB RU Throttling and Hot Partitions"
page_title: "Fix Cosmos DB RU Throttling and Hot Partitions: Diagnose Skew, Read Per-Partition Metrics, and Choose the Right Partition Key"
date: 2022-09-12
categories: ["Technology"]
tags: ["Azure", "Cosmos DB", "Troubleshooting", "Performance", "Cloud Computing"]
excerpt: "Cosmos DB RU throttling on a single hot partition is rarely a true capacity shortage. Read the per-partition metric, find the skew, and fix the key behind it."
image: "/assets/images/blog/blog-43.webp"
reading_time: 60
author: "thomas-reid"
last_updated: 2022-09-12
lang: en
---
You raised the provisioned throughput on the container, the bill went up, and the 429 responses kept coming. That is the moment most engineers realize that Cosmos DB RU throttling is not always a story about buying more capacity. When a single physical partition saturates while the rest of the container sits nearly idle, no amount of extra request units fixes the symptom, because the extra capacity lands on partitions that were never the problem. The throttle you are watching is almost always a hot spot, and a hot spot is a key design problem wearing the costume of a capacity shortage.

This article gives you the diagnosis and the ranked set of fixes. By the end you will be able to read the per-partition request-unit metric, confirm whether one partition is pinned at its ceiling while the others stay quiet, and decide between the cheap remedy of reshaping a query and the expensive remedy of re-keying the container. The work is mostly investigative. The throttle tells you something is uneven, the metrics tell you exactly which partition is hot, and the key tells you why.

![Diagnosing Cosmos DB RU throttling and hot spot skew - Insight Crunch](/assets/images/blog/blog-43.webp)

The reason this matters beyond the immediate fire is cost. Over-provisioning to mask a hot spot is one of the most expensive mistakes a team can make on Cosmos DB, because the spend scales with the whole container while the relief scales with nothing. You pay for throughput spread across every physical partition, the hot one keeps throttling at its slice of that total, and the invoice climbs without the errors falling. Understanding the even-split mechanism turns a recurring panic into a one-time design decision.

## What Cosmos DB RU Throttling Actually Means

A 429 from Cosmos DB is the service telling you that a request would exceed the request units available to the partition that owns the request, within the one-second window the service accounts against. The status is documented as request rate too large, and it arrives with a response header named `x-ms-retry-after-ms` that tells the client how many milliseconds to wait before retrying. The SDKs read that header and retry automatically up to a configurable limit, which is why a moderate throttle often looks like nothing more than elevated latency rather than visible failures. The errors only surface to your application once the retries are exhausted.

The unit of accounting is the request unit, abbreviated RU, a normalized currency that rolls the CPU, memory, and IOPS cost of an operation into one number. A point read of a one-kilobyte item costs one RU by definition. A query, a write, a stored-procedure execution, and a read of a larger item all cost more, and the cost rises with item size, index footprint, and the amount of data the engine has to touch. Provisioned throughput is expressed in RU per second, and when consumption in a given second exceeds what is available, the excess is throttled with a 429.

The single fact that reframes the whole problem is how that provisioned throughput is distributed. Cosmos DB does not maintain one shared pool of request units that any request can draw from. It splits the provisioned total evenly across the physical partitions that hold the container's data. If you provision 30,000 RU per second and the container currently spans three physical partitions, each physical partition is granted roughly 10,000 RU per second, and a request is throttled when the partition it targets has spent its share, regardless of how idle the other two partitions are.

### Why does one partition throttle while the others sit idle?

Because provisioned throughput is divided evenly across physical partitions, not pooled. A request that lands on a saturated partition is throttled even when the container as a whole is using a fraction of its total RU. The metric to trust is per-partition consumption, not the container-level average, which hides the skew entirely.

That distinction is the entire article in miniature. The container-level dashboard you reach for first shows an average or a sum, and an average across one hot spot and several cold ones looks reassuringly low. You see twenty percent total utilization and conclude you have headroom, while one partition is at one hundred percent and rejecting work. The throttle is real, the headroom is real, and they coexist because they describe different scopes. The fix is never to trust the aggregate when a 429 is firing; it is to open the per-partition view and find the outlier.

## How Cosmos DB Splits Throughput Across Partitions

To diagnose a hot spot you need a working mental model of how Cosmos DB physically lays out data, because the throttle is a consequence of that layout. The model has two layers, logical and physical, and conflating them is the source of most confusion.

A logical partition is the set of all items that share the same key value. Every item you write carries a value for the key path you chose when you created the container, and all items with the value `tenant-42` belong to one logical partition, all items with `tenant-43` belong to another. A logical partition is bounded; it has a storage ceiling that you should treat as a hard limit to verify against the current documentation, historically in the tens of gigabytes. A single logical partition cannot be split across physical partitions, which is the constraint that makes key choice so consequential.

A physical partition is a unit of compute and storage that the service manages on your behalf. It hosts a range of logical partitions, allocated by a hash of the key value. You do not create or address physical partitions directly. Cosmos DB decides how many you have based on two pressures: total storage, because a physical partition has a storage ceiling, and total provisioned throughput, because a physical partition also has a maximum throughput it can serve. As either pressure grows past a threshold, the service splits a physical partition into two and redistributes the logical partitions between them. This is why a container that started with one physical partition silently grows to several as data or throughput increases.

### How many physical partitions does my container have?

Divide your provisioned throughput by the per-partition throughput ceiling, then compare against the count implied by total storage divided by the per-partition storage ceiling, and take the larger. The service provisions enough physical partitions to satisfy both. You can also infer the count from the per-partition metrics, which list every partition separately.

The even split follows directly. When the service grants your container 30,000 RU per second and has placed your data on three physical partitions, it does not weight the grant by how busy each partition is. Each gets ten thousand. A logical partition that receives a flood of requests is hosted on exactly one physical partition, so the flood is metered against that one partition's ten thousand, and once it crosses that line the requests are throttled while the other twenty thousand sit unused on the other two. The throughput is provisioned globally and consumed locally, and the gap between those two facts is where hot spots live.

This is the even-split rule for Cosmos throughput, and it is worth stating as a rule you can carry into a design review: provisioned RU is divided across physical partitions, so a hot spot is a key-design problem that the total RU cannot solve. Only a better key or a query that touches fewer of them changes the outcome. Adding RU raises every partition's ceiling proportionally, which helps a container that is uniformly busy and does almost nothing for a container where one partition carries the load.

## Reading the Metrics to Find the Hot Partition

The diagnosis hinges on one metric and one chart. The metric is Normalized RU Consumption, and the chart is its breakdown by physical partition. Normalized RU Consumption reports, as a percentage, how close a partition came to its allocated throughput in a given interval. A value of one hundred percent means a partition spent its entire allocation for that interval and any further request in that window was throttled. The metric is exposed in Azure Monitor and surfaced in the Insights blade for the Cosmos DB account.

The trap is that the default view often shows this metric aggregated, as a maximum or an average across the account, which tells you whether anything was hot without telling you which thing. To find the hot spot you split the metric by the PhysicalPartitionId dimension. When you do, a healthy container shows a cluster of physical units hovering at similar, moderate values. A container with a hot spot shows one line pinned near one hundred percent while the others trace a low band well beneath it. That single divergent line is your hot spot, and its identifier is the thread you pull to find the offending key values.

Here is how to pull that metric with the Azure CLI so the diagnosis is reproducible rather than a matter of squinting at a portal chart:

```bash
# Get the resource ID of the Cosmos DB account
ACCOUNT_ID=$(az cosmosdb show \
  --name my-cosmos-account \
  --resource-group my-rg \
  --query id --output tsv)

# Read Normalized RU Consumption, split by physical partition,
# over the last hour at one-minute granularity
az monitor metrics list \
  --resource "$ACCOUNT_ID" \
  --metric NormalizedRUConsumption \
  --dimension PhysicalPartitionId \
  --interval PT1M \
  --start-time "$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)" \
  --output table
```

When the output lists several partition identifiers and one of them reports values near one hundred while the rest report values in the teens or twenties, you have confirmed skew rather than a global shortfall. If every one reports high values at the same time, you have the opposite situation, a genuinely under-provisioned container, and the fix there is more throughput or a query that costs less, not a key change. The metric tells you which world you are in before you spend a dollar or schedule a migration.

### Is my throttling a hot spot or a real capacity shortage?

Split Normalized RU Consumption by physical partition. If one partition pins at one hundred percent while the others stay low, it is a hot spot and more RU will not help. If all partitions rise together, it is a true capacity shortage, and raising throughput or cutting per-request cost is the correct response.

The second signal worth reading is the request-charge of individual operations, returned on every response in the `x-ms-request-charge` header and exposed by the SDKs as the RequestCharge property of the response. A query that costs four hundred RU because it fans out across every partition and scans far more than it returns is a different problem from a hot spot, but the two often travel together, and reading the per-operation charge tells you whether an expensive query is part of what is loading the hot spot. You want both numbers in hand before you decide on a remedy: which partition is hot, and what the costly operations against it actually charge.

## The InsightCrunch Hot-Partition Diagnosis Flow

The remedies for a hot spot range from a query rewrite you can ship this afternoon to a container migration that takes planning and a maintenance window. Reaching for the expensive fix first is the most common waste, so the diagnosis should walk from cheapest to most involved and stop at the first remedy that resolves the skew. The table below is the reference to keep beside the metrics chart.

| Signal in the metrics | Likely cause | Cheapest viable fix | Cost and effort | Escalate to if it fails |
| --- | --- | --- | --- | --- |
| One partition pinned, expensive cross-partition queries in the logs | Fan-out query scanning the hot spot repeatedly | Add the key to the query filter; add or tune the index | Low; code and index change, no migration | Query is already scoped; treat as access skew below |
| One partition pinned, writes concentrated on recent items | Monotonic key (timestamp, sequence) creating an append hot spot | Switch writes to a higher-cardinality or synthetic key | High; requires re-key migration | None; this is the root fix |
| One partition pinned, one key value dominates reads and writes | Low-cardinality key (status, country, boolean) | Re-key to a high-cardinality or synthetic composite | High; requires re-key migration | Hierarchical key if the dominant value is a tenant |
| One partition pinned for one tenant in a multi-tenant container | A single large tenant outgrowing its partition | Hierarchical (subpartitioned) key, or dedicated container for that tenant | Medium to high | Dedicated throughput container per large tenant |
| All partitions high together | Genuine under-provisioning | Raise provisioned RU or enable autoscale; cut per-request cost | Low to medium; no migration | Optimize indexing and item size |

The flow reads top to bottom. Confirm the hot spot in the metrics, check whether expensive queries are hitting it, and if a query rewrite removes the load you are done with no migration at all. Only when the access pattern is already as tight as it can be, and it is still hot, do you accept that the key itself concentrates load and plan the migration. The discipline is to exhaust the cheap fixes before committing to the expensive one, because the expensive one cannot be undone in place.

## Root Cause One: A Low-Cardinality Partition Key

Cardinality is the number of distinct values a key path can take. It is the first thing to interrogate when one partition runs hot, because cardinality sets the ceiling on how finely Cosmos DB can spread your data. A path with three possible values can produce at most three logical partitions, and three logical partitions cannot be balanced across more than a few physical partitions no matter how much throughput you provision. The classic offenders are status fields, country codes, boolean flags, document types, and environment names. They feel natural to query on, which is exactly why engineers reach for them, and they are catastrophic as keys because a handful of values cannot distribute load.

The failure mode is concrete. Suppose you key an orders container on `status`, with values of pending, shipped, and delivered. Almost every active order spends its early life as pending, so writes and the hottest reads all target the pending logical partition. That logical partition lives on one physical partition, which absorbs the entire write-heavy and read-heavy workload of new orders while the partitions holding delivered orders, the bulk of your storage, see almost no traffic. The metrics show one partition at the ceiling and the rest cold. You have plenty of storage spread across partitions and all of your activity funneled into one.

### How do I confirm a low-cardinality key is the cause?

Run a query that groups item counts and request charges by the key value. If a small number of values hold most of the active items, or one value absorbs most of the recent writes, the key cannot distribute load. Confirm it against the per-partition metric showing one physical partition carrying the traffic.

To confirm it directly, query the distribution of items across key values and look at how lopsided it is. A query like the following, run with cross-partition enabled, shows you how many items sit under each key value, which exposes a low-cardinality or heavily skewed key immediately:

```sql
SELECT c.status AS partitionKeyValue, COUNT(1) AS itemCount
FROM c
GROUP BY c.status
```

If three values account for the entire container and one of them holds the active working set, the diagnosis is settled. The remedy is to choose a key with many more distinct values and an access pattern that spreads requests across them. For the orders example, the order identifier itself is a far better key than the status, because each order has a unique identifier, the cardinality is effectively unbounded, and reads and writes for a given order target exactly one small logical partition. You trade the convenience of querying all pending orders in a single partition for an even distribution of load, and you recover the ability to filter on status through the index rather than the key.

The cost of this fix is the cost of every key change in Cosmos DB: the key is fixed at container creation and cannot be altered in place. Changing it means creating a new container with the better key and migrating the data, which the prevention section covers in detail. That cost is why the diagnosis flow tries query rewrites first. But when the key genuinely lacks the cardinality to distribute load, no query rewrite saves it, and the migration is the only honest fix. Recognizing a low-cardinality key early, ideally before the container holds production data, is worth far more than any remedy applied later.

## Root Cause Two: A Monotonically Increasing Key

A key can have effectively unlimited cardinality and still create a hot spot if its values are produced in order. This is the monotonic-key trap, and it is the most counterintuitive of the hot-partition causes because the key looks healthy by every cardinality test. A timestamp, an auto-incrementing sequence, a date string, or any value that climbs steadily over time produces a brand-new logical partition for each new value, which sounds ideal, but it concentrates all current activity on the newest values, and the newest values hash to a narrow band of physical partitions at any given moment.

The mechanism is the append hot spot. Consider a telemetry container keyed on a per-second timestamp. Every reading written in the current second carries the same key value, so they all land in one logical partition, on one physical partition. The next second they all move to the next value, which may or may not live on the same physical partition, but the point is that at any instant the entire write workload is concentrated on whichever partition owns the current value. Reads of recent data, which is the data anyone actually queries, hit the same narrow set. The historical data, which is the overwhelming majority of the storage, sits cold across the other partitions. You get a hot spot that migrates over time but is always hot somewhere, and the aggregate metrics again hide it.

### Why does a unique timestamp key still cause a hot spot?

Because uniqueness is not the same as distribution. A monotonic key produces a new value for each write, but all concurrent writes share the current value and land on the same physical partition, creating an append hot spot. The fix is a key whose concurrent writes scatter across partitions rather than clustering on the newest value.

Confirming a monotonic-key hot spot means correlating the hot spot with recency. Pull the per-partition metric and note which physical partition is hot, then check whether the hot spot tracks the most recently written key values. If the hot spot shifts over time and always corresponds to current writes, the append hot spot is confirmed. You can also reason about it from the schema alone: if the key is a time value, a sequence, or anything that increases with insertion order, you have a monotonic key and an append hot spot is structurally guaranteed under sustained write load.

The remedy is to break the ordering so that concurrent writes scatter. The standard technique is a synthetic key that combines the time component with a high-cardinality discriminator, so that writes in the same second spread across many logical partitions. For telemetry you might combine the device identifier with the hour, producing a key like `device-9f3a_2022091214`, which keeps related readings together for efficient querying while ensuring that thousands of devices writing in the same second distribute across thousands of logical partitions rather than piling onto one. The synthetic key is computed and stored on the item at write time:

```python
# Build a synthetic partition key that scatters concurrent writes
# while keeping a device's readings co-located for querying
def synthetic_partition_key(device_id: str, event_time) -> str:
    hour_bucket = event_time.strftime("%Y%m%d%H")
    return f"{device_id}_{hour_bucket}"

item = {
    "id": reading_id,
    "pk": synthetic_partition_key(device_id, reading_time),
    "deviceId": device_id,
    "timestamp": reading_time.isoformat(),
    "value": measured_value,
}
container.create_item(body=item)
```

The synthetic key requires the same migration as any other key change, because you are changing the key path. The payoff is that write load distributes across as many partitions as you have active discriminator values, and the append hot spot disappears. The design lesson is durable: never partition on a value that increases with insertion time unless you deliberately add a high-cardinality component to scatter the writes.

## Root Cause Three: A Single Dominant Value in an Otherwise Healthy Key

Sometimes the key is well chosen, cardinality is high, writes are not monotonic, and one partition is still hot because one key value carries vastly more load than the rest. This is the dominant-value problem, and it is most common in multi-tenant systems keyed on a tenant identifier. The tenant key is excellent in principle: tenants are numerous, each tenant's data co-locates for efficient querying, and a typical tenant fits comfortably in one logical partition. The trouble starts when one tenant grows an order of magnitude larger than the others, or sends an order of magnitude more traffic, because that tenant's logical partition is bounded to one physical partition and cannot be split.

The dominant-value problem differs from low cardinality because the key is fine for the long tail and broken only for the outlier. You cannot fix it by switching to a higher-cardinality key, because the key already has high cardinality; the issue is the distribution of load across the existing values, not the count of values. A small number of whales, in tenant-system parlance, can each saturate their own partition while the thousands of small tenants share cold partitions and never come close to their share of throughput.

### How do I handle one tenant that keeps overloading its partition?

Two paths exist. Subpartition the dominant value with a hierarchical key so the large tenant's data spreads across multiple physical partitions, or move the heavy tenant into a dedicated container with its own throughput. Subpartitioning keeps the schema uniform; a dedicated container isolates the noisy neighbor entirely.

Confirming a dominant value means ranking key values by traffic and storage, not just counting them. The grouping query from the cardinality section reveals it: if one tenant value holds a disproportionate share of items, and the per-operation request charges concentrate on that tenant, you have a whale. Cross-reference with the per-partition metric to confirm the hot physical partition corresponds to the whale tenant's hash range.

The first remedy is the hierarchical key, also called subpartitioning, which lets you specify a key with multiple levels, such as tenant identifier followed by a secondary path like user identifier or a date bucket. Cosmos DB then partitions on the combination, so a single large tenant's data spreads across multiple physical partitions by its second-level values while queries scoped to the tenant remain efficient. This is the cleanest fix when most tenants are small and a few are large, because the schema stays uniform and you do not special-case the whales in application code:

```python
# Container created with a hierarchical (subpartitioned) key
# so a large tenant spreads across physical partitions by user
container = database.create_container(
    id="multitenant",
    partition_key=PartitionKey(
        path=["/tenantId", "/userId"],
        kind="MultiHash",
    ),
)
```

The second remedy, for a tenant so large that even subpartitioning strains, is to move that tenant into its own container with dedicated throughput. This isolates the noisy neighbor completely, gives the whale its own RU budget, and protects the shared container holding the long tail. It costs operational complexity, because your application must route the whale to a different container, and it costs a minimum throughput floor for the dedicated container, but it removes the contention entirely. The choice between subpartitioning and isolation comes down to how extreme the dominant value is and whether you can tolerate the routing logic, a trade-off the related decision guidance below develops further.

## Root Cause Four: Expensive Cross-Partition Queries Loading the Hot Partition

Not every hot-partition story is about writes. A query that omits the key from its filter cannot be routed to a single partition, so the engine fans it out to every physical partition, asks each to evaluate the predicate, and merges the results. Each partition that participates spends RU proportional to the data it scans, and if the query runs frequently it can load a partition heavily even when the data distribution is perfectly even. When the fan-out query repeatedly scans a partition that already carries write load, the two combine and push that partition over its ceiling.

The cost of a cross-partition query is easy to underestimate because it is invisible in the query text. A filter on a non-key, non-indexed field forces a scan, the scan touches every one, and the request charge climbs with the data volume rather than the result size. A query that returns ten rows can charge hundreds of RU if it scanned a hundred thousand items across every one of them to find them. Multiply that by a high call rate and a single endpoint can dominate the RU consumption of an entire container while looking innocent in the code.

### Does a cross-partition query waste request units?

It can charge far more RU than a scoped query, because it fans out to every physical partition and each one spends units scanning. The waste compounds when the filtered field is unindexed, forcing a full scan. Add the key to the filter, or index the filtered field, to collapse the fan-out and cut the charge.

To confirm a query is the culprit, read the request charge and the query metrics for the suspect operation. The SDKs expose the charge on the response, and the query metrics report how many partitions were touched and how much data was scanned. A high charge combined with a small result set and a touched-partition count equal to your physical-partition count is the fingerprint of an unscoped fan-out. The diagnostic call is cheap and reproducible:

```python
# Inspect the request charge and partition fan-out of a query
items = list(container.query_items(
    query="SELECT * FROM c WHERE c.email = @email",
    parameters=[{"name": "@email", "value": target_email}],
    enable_cross_partition_query=True,
    populate_query_metrics=True,
))
charge = container.client_connection.last_response_headers["x-ms-request-charge"]
metrics = container.client_connection.last_response_headers.get(
    "x-ms-documentdb-query-metrics", ""
)
print(f"Request charge: {charge} RU")
print(f"Query metrics: {metrics}")
```

The fix is the cheapest in the entire diagnosis flow because it requires no migration. If the query can include the key, add it, and the query routes to a single partition and stops fanning out. If the query must filter on a field that is not the key, ensure that field is indexed, because an indexed lookup scans far less than a full partition scan and cuts the per-partition charge dramatically. When neither is possible because the access pattern genuinely needs to search across partitions on a non-key field, consider a secondary access pattern: a materialized view in another container keyed on the field you query, kept current through the change feed, so the lookup becomes a point read against a purpose-built container rather than a fan-out against the primary. The change feed and materialized views are the standard answer to a query pattern the primary key cannot serve, and they avoid loading the primary container's hot spot entirely.

## The Re-Key Migration: Fixing a Key You Cannot Change in Place

Three of the four root causes resolve only by changing the key, and the key is immutable once a container is created. There is no portal switch, no command, and no online operation that rewrites the key of an existing container. The fix is a migration: create a new container with the better key, copy the data, redirect the application, and retire the old container. The migration is mechanical, but it has to be planned so that no writes are lost during the cutover, and the planning is where teams trip.

The migration has a stable shape regardless of the tool you use. You create the target container with the corrected key and an appropriate throughput setting, you backfill the existing data from the source into the target with the new key value computed for each item, you keep the target current with writes that arrive during the backfill, and then you cut the application over to the target and stop writing to the source. The backfill and the keeping-current step are the two that demand care, because a naive copy captures a snapshot and then drifts as new writes land in the source after the copy started.

### How do I change a Cosmos DB key without downtime?

Create a new container with the corrected key, backfill existing data while computing the new key value per item, and use the change feed to stream writes that arrive during the backfill into the target. Cut the application over once the target has caught up, then retire the source. The change feed is what closes the drift gap.

The change feed is the mechanism that makes a zero-downtime cutover practical. It is an ordered record of every create and update in a container, which you can read from the beginning to backfill the entire history and then continue reading to capture every subsequent change in near real time. A migration built on the change feed reads from the start of the source container to populate the target, then keeps consuming so that any write landing in the source during the backfill flows into the target within seconds. When the target has caught up, you switch the application's writes to the target, let the feed drain the last few changes, and the cutover completes with no lost data and no maintenance window. The Azure Cosmos DB Data Migration tools and the change-feed processor library both implement this pattern; for a one-time move the bulk executor combined with a change-feed reader is a common choice:

```python
# Skeleton of a change-feed-driven re-key migration
# 1. Backfill from the start of the source feed into the new key
for change in source.query_items_change_feed(start_time="Beginning"):
    change["pk"] = compute_new_partition_key(change)
    target.upsert_item(change)

# 2. Continue from the saved continuation token to capture
#    writes that arrived during the backfill, then cut over.
```

Two planning notes save real pain. First, provision generous throughput on the target during the backfill, because a backfill is write-heavy and a stingy RU setting on the target turns the migration itself into a throttling problem; you can lower it after the cutover. Second, validate the new key against the diagnosis before you migrate, because migrating to a second poorly chosen key wastes the entire effort. Run the grouping query against a sample of the data using the proposed new key to confirm that the values distribute and that no single value dominates, so the migration lands on a key that actually spreads the load rather than relocating the hot spot.

## Distinguishing a Hot Partition From a Genuine Capacity Shortage

The most expensive misdiagnosis in this whole space is treating uniform throttling as if it were skew, or skew as if it were a shortage. The two demand opposite responses, and applying the wrong one either wastes money or wastes a migration. The per-partition metric is the arbiter, and reading it correctly is the single most valuable habit this article can leave you with.

A genuine capacity shortage shows every physical partition rising toward its ceiling together. The workload is distributed, the container is simply asked to do more than its provisioned throughput allows, and the honest fix is more throughput or cheaper requests. You raise the provisioned RU, or you enable autoscale so the ceiling rises automatically with demand, or you reduce the per-request cost by tightening the indexing policy and trimming item size. None of these require a migration, because the key is doing its job; the container is correctly distributing load and merely needs a bigger budget or a lighter workload.

### When should I add request units instead of changing the key?

Add request units only when every physical partition rises together in the metrics, which means load is distributed and the container is genuinely under-provisioned. If one partition is pinned while others stay idle, more units land on partitions that were never the bottleneck and the throttle persists, so a key or query change is the correct response instead.

A hot spot shows the opposite signature, one partition pinned and the rest idle, and adding throughput to that container is close to pure waste. The extra RU is divided evenly across all partitions, so the hot one gains only its even share of the increase while you pay for the increase across every one of them. If one partition out of five is hot and you double the provisioned throughput, you have quadrupled, in effect, the spend per unit of relief on the partition that actually needed it, because four-fifths of the new capacity lands where there was never any pressure. This is the arithmetic that turns a hot spot into a runaway bill, and it is why the metric reading comes before any change to provisioned throughput.

There is a middle case worth naming. Autoscale raises and lowers the provisioned throughput between a floor and a ceiling you set, billed by the peak each hour, and it is excellent for distributed workloads with variable demand. It does nothing for a hot spot except raise the ceiling that the hot spot's even share is computed from, which means autoscale on a skewed container scales your cost with the hot spot's appetite while the cold partitions ride along at inflated allocations. Autoscale is a capacity tool, not a skew tool, and reaching for it to silence a hot spot is the same mistake as manually over-provisioning, dressed up as automation.

## Prevention: Choosing a Partition Key That Will Not Run Hot

Because every key fix is a migration, the highest-leverage work happens before the container exists. A key that distributes load is chosen by reasoning about three properties together, and a key that satisfies all three at design time saves you from every remedy in this article. The properties are cardinality, distribution of access, and co-location of related reads.

Cardinality has to be high enough that the values can spread across many physical partitions as the container grows. A key with thousands or millions of distinct values can distribute; a key with a handful cannot. Distribution of access has to be even, meaning requests should spread across the values rather than concentrating on a few, which rules out monotonic keys whose newest values absorb all current traffic and dominant-value keys where one value carries the load. Co-location is the property that makes the key useful for querying: items you read together should share a key value so the read targets one partition, which is why a tenant key or an entity-identifier key serves so well when the entity's data is read as a unit.

### What makes a good Cosmos DB key?

High cardinality so values spread across many partitions, even access so no single value absorbs the load, and co-location so items read together share a key value. A key that satisfies all three distributes writes and reads while keeping queries efficient. The order identifier, the device-and-time composite, and the tenant-and-user hierarchy are common examples.

The synthetic and hierarchical keys exist precisely to satisfy all three properties when no natural field does. A synthetic key concatenates fields to manufacture cardinality and break monotonicity, as the device-and-hour key did for telemetry. A hierarchical key adds levels so a dominant first-level value subpartitions by its second level, as the tenant-and-user key did for the whale tenant. Reaching for these at design time, when you can see the access pattern and estimate the distribution, is far cheaper than discovering the need after the hot spot fires in production. The grouping query that confirms a bad key in diagnosis is the same query you should run against representative sample data before you commit a key, turning prevention into the same five-minute check you would otherwise run during a fire.

One more preventive habit pays off repeatedly: model the write path and the read path separately and confirm both distribute. A key can spread writes beautifully and still force every important read into a fan-out, or serve reads perfectly while concentrating writes on a monotonic edge. Walk the highest-volume write and the highest-volume read against the candidate key, confirm each targets a well-distributed set of partitions, and you will catch the append hot spot and the unscoped query before either reaches production. When the read pattern genuinely conflicts with the write pattern, the change feed feeding a second container keyed for reads resolves the tension without compromising either.

## Related Failures Often Confused With a Hot Partition

A hot spot rarely arrives alone in the logs, and several neighboring failures wear similar symptoms. Telling them apart keeps you from fixing the wrong thing.

The plain 429 rate-limit error is the surfaced symptom rather than a separate cause, and it deserves its own treatment because the same status code appears for a genuine shortage, a hot spot, and a burst that briefly exceeds a healthy allocation. The status is identical in all three; only the per-partition metric and the request pattern distinguish them. A burst against an otherwise healthy container is handled by the SDK retry and a modest throughput buffer, a shortage is handled by more capacity, and a hot spot is handled by a key or query change. Treating every 429 as the same problem is how teams end up over-provisioning a container that had a hot partition all along.

### Why do I get 429 errors even with high provisioned throughput?

Because provisioned throughput is split across physical partitions and consumed per partition. A single hot partition throttles at its share regardless of how high the container total is, so a richly provisioned container still returns 429 when one partition saturates. The total is a red herring; the per-partition consumption is the real measure.

Rate-limit retries that exhaust look like timeouts or transient failures in application logs, because once the SDK has retried up to its configured limit it surfaces the 429 to your code, and a layer above may translate it into a generic error. An application reporting intermittent failures under load, with no obvious cause, is often hitting a hot partition whose throttle the SDK absorbed until the retry budget ran out. Reading the request diagnostics from the SDK, which record the retry count and the status codes, reveals the throttle hiding behind the generic error and points you back at the per-partition metric.

Storage-related splits are the benign cousin of a hot partition and are sometimes mistaken for one. As a container grows, Cosmos DB splits physical partitions to stay under the per-partition storage ceiling, and during a split there can be brief periods of elevated latency or transient throttling as data redistributes. This is normal, self-resolving, and not a design problem; it is the service doing its job. The tell is that the elevated metrics coincide with growth and subside on their own, whereas a hot partition persists and tracks a specific key value or access pattern rather than overall size. If the throttling clears itself after a split completes, you witnessed a redistribution, not a hot partition.

Index-driven write cost is the last common confusion. A write charges RU for every indexed path it updates, so a container with a broad indexing policy can make writes far more expensive than necessary, which raises per-partition consumption uniformly and can tip a busy partition over its ceiling. This presents as throttling under write load, but the fix is to narrow the indexing policy to the paths you actually query, not to change the key. If trimming the index drops the write charge and the throttling eases, the index was the load, and the partition was never genuinely hot in the design sense.

## A Worked Diagnosis From Alert to Fix

Walking a single case end to end ties the pieces together. The setup is a multi-tenant analytics container provisioned at 40,000 RU per second, keyed on `tenantId`, spread across five physical partitions. The on-call alert fires for sustained 429 responses, and the first reflex, the wrong one, is to raise the throughput. Resist it until the metric speaks.

Step one is the per-partition read. Splitting Normalized RU Consumption by PhysicalPartitionId shows four partitions tracing a calm band near fifteen percent and one partition pinned at one hundred percent for the entire alert window. That single divergent line settles the category immediately: this is skew, not a shortage, and raising the 40,000 total would have spent four-fifths of the increase on partitions that were already idle. The container does not need more capacity. It needs the load on one partition to come down.

Step two is to identify what is loading the hot partition. Two questions run in parallel. The grouping query by `tenantId` ranks tenants by item count and reveals that one tenant holds roughly sixty percent of the items in the container, far more than any other. Separately, inspecting the request charges on the heaviest endpoint shows a dashboard query filtering on a date range without the tenant in the filter, fanning out across all five partitions at a charge of several hundred RU per call. Now both contributors are visible: a dominant tenant concentrating storage and writes on one partition, and a fan-out query repeatedly scanning every partition including the hot one.

Step three is to apply the cheap fix first and measure. The dashboard query can include the tenant identifier, because the dashboard is always scoped to one tenant at a time, so adding `WHERE c.tenantId = @tenant` to the filter collapses the fan-out from five partitions to one and drops the per-call charge by roughly it count. After deploying that one-line change, the per-partition metric shows the hot partition easing from one hundred percent to the mid seventies. The query was a real contributor, the rewrite required no migration, and it bought immediate relief. If that had brought it into the safe band, the case would close here, which is the outcome in a meaningful share of real incidents.

Step four, because it is still in the seventies under write load from the dominant tenant, is the structural fix. The diagnosis points at a whale tenant, so the remedy is either subpartitioning the container with a hierarchical key of tenant plus a second level, or moving the whale to a dedicated container. Given that one tenant holds the majority of the data and the rest are small, the team chooses a dedicated container for the whale with its own throughput, routes that tenant in application code, and leaves the shared container keyed on tenant for the long tail. After the migration, the shared container's partitions settle into an even band and the whale's dedicated container carries its own load against its own budget. The total spend drops, because the shared container no longer needs inflated throughput to keep the hot partition alive, and the whale pays for exactly the capacity it uses. The full mechanics of it model that underlies this whole sequence are developed in the [Azure Cosmos DB engineering guide](/2022/02/14/azure-cosmos-db-engineering-guide/), which is the reference to keep open while you reason about physical partitions and the even split.

## Monitoring So the Next Hot Partition Announces Itself

Diagnosis after an alert is reactive. The better posture is an alert that fires on skew specifically, before the 429 storm reaches users. Because Normalized RU Consumption is reported per partition, you can alert on the maximum across partitions rather than the average, and that single choice transforms the signal from useless to diagnostic. An average across one hot and four cold partitions stays low and never alarms; a maximum captures the hot partition the instant it pins.

The alert rule to configure watches the maximum Normalized RU Consumption across physical partitions and fires when it sustains above a threshold, commonly in the eighty to ninety percent range, for several minutes. The sustained window matters because brief spikes to one hundred percent are normal under bursty load and the SDK retries absorb them; what you want to catch is a partition that stays pinned, which is the fingerprint of skew rather than a momentary burst. Pair the alert with a dashboard that always shows the per-partition breakdown so that when the alert fires, the responder opens straight to the chart that names the hot partition.

```bash
# Alert when the busiest physical partition stays near its ceiling
az monitor metrics alert create \
  --name cosmos-hot-partition \
  --resource-group my-rg \
  --scopes "$ACCOUNT_ID" \
  --condition "max NormalizedRUConsumption > 90" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --description "A single physical partition is sustaining near its RU ceiling"
```

The aggregation choice in that condition, taking the maximum rather than the average, is the entire point. It is the monitoring expression of the even-split rule: because each partition has its own ceiling, the health of the container is the health of its busiest partition, and the busiest partition is the maximum of the per-partition metric. An alert built on the average is an alert that will stay silent through every hot-partition incident you ever have, which is worse than no alert because it manufactures false confidence.

Beyond the throttle alert, track the request charge of your top endpoints over time, because a query that drifts from scoped to fan-out, often through a well-meaning feature change that drops the key from a filter, shows up as a rising per-call charge long before it saturates a partition. Logging the RequestCharge of representative operations and charting it turns a slow regression into something you notice in a code review's aftermath rather than in an incident. The deeper treatment of tuning request units and reading these signals lives in the [Cosmos DB throughput and RU optimization](/2024/08/26/cosmos-db-throughput-optimization/) guide, which extends this monitoring posture into systematic RU reduction.

## The Cost Arithmetic of Ignoring Skew

The financial case for diagnosing before provisioning deserves to be spelled out, because it is the argument that gets a migration prioritized over a quick throughput bump. Cosmos DB bills provisioned throughput by the RU per second you reserve, across the whole container, whether or not every partition uses its share. When you raise throughput to silence a hot partition, you pay the increase multiplied across every physical partition, and you receive relief multiplied across only the one that was hot.

Put numbers on it. A container at 20,000 RU per second across four partitions grants each partition 5,000. One partition is hot, pinned at its 5,000 while the others idle near 1,000. To give the hot partition another 5,000 by raising the total, you must provision 40,000, because the grant is even, so all four partitions now hold 10,000. You doubled the bill to double one partition's ceiling, and three-quarters of the new capacity sits idle on partitions that were already cold. If the hot partition needs not double but triple its headroom, you triple the whole container, and the waste compounds. There is no setting that adds capacity to one partition; the even split is structural.

The migration that fixes the key, by contrast, is a one-time cost in engineering time and a brief period of dual-running throughput, after which the container distributes load and runs comfortably at or below its original provisioned level. The recurring saving is the difference between the inflated throughput you would otherwise carry forever and the modest throughput a well-distributed container actually needs. Over a year, the migration usually pays for itself many times over, which is why the diagnosis flow treats over-provisioning as a temporary bridge at most and never as the resolution. The broader discipline of pricing throughput against real consumption, including where autoscale earns its keep and where it quietly inflates the bill on skewed containers, is the subject of the wider RU-tuning material and worth internalizing before you set any throughput number in production.

## Shared-Throughput Databases Make Skew Worse

There is a configuration that multiplies every hot-partition problem described so far, and teams adopt it precisely because it looks like a cost saving. Cosmos DB lets you provision throughput at the database level and share it across all containers in that database, rather than provisioning each container its own dedicated budget. Shared throughput is attractive for many small containers that each see light, sporadic traffic, because they pool a single allocation instead of each paying a minimum floor. The trap is that the same even-split mechanics apply, now across containers as well as partitions, so a hot partition in one container competes for the shared pool with every other container in the database.

The mechanics deserve a careful look. With shared throughput, the database's provisioned units are distributed across the physical partitions of all the containers that share the budget. A single container with a hot partition does not merely throttle itself; it consumes a disproportionate share of the pooled throughput, starving the other containers that share the database. An incident that would be contained to one container under dedicated throughput now radiates across every container in the database, and the symptom appears in containers that have nothing wrong with their own key design. Diagnosing this is harder because the per-partition metric still points at the genuinely hot partition, but the collateral throttling shows up in unrelated containers, which sends responders chasing phantom problems in code that is working correctly.

### Should I use shared or dedicated throughput to avoid hot partitions?

Use dedicated throughput for any container with meaningful or uneven traffic, because dedicated throughput contains a hot partition to its own container and gives it an isolated budget. Reserve shared throughput for many small, uniformly light containers where pooling saves the per-container minimum and no single container can dominate the pool.

The resolution mirrors the dedicated-container fix for a whale tenant. When a container in a shared-throughput database develops a hot partition or simply grows busy enough to dominate the pool, move it to dedicated throughput so its load is contained and the other containers regain their share. The decision rule is straightforward: shared throughput suits a population of small, uniformly light containers where the pooling genuinely saves money and no member can monopolize the budget, while dedicated throughput suits any container with meaningful or uneven traffic, because dedication is what isolates a hot partition's blast radius to the container that owns it. Choosing shared throughput for a database that contains even one busy or skew-prone container is a false economy that converts a local problem into a database-wide one.

The lesson generalizes. Every layer of sharing in Cosmos DB, whether across partitions within a container or across containers within a database, follows the even-split logic, and every layer of sharing widens the area that a single hot spot can disrupt. When isolation matters, dedication is the tool, and the cost of a dedicated allocation is usually small against the cost of an incident that spreads across an entire database because one container's key concentrated load into the shared pool.

## Bulk Operations, the Retry Budget, and Hidden Throttling

A category of throttling hides inside the SDK and never reaches your application logs until it is severe, and it is worth understanding because it changes how you interpret a quiet incident. The Cosmos DB SDKs implement automatic retry on 429 responses, reading the `x-ms-retry-after-ms` header and waiting the indicated interval before retrying, up to a configurable maximum number of retries and a maximum cumulative wait. Under moderate throttling this machinery is invisible: requests succeed after a retry or two, the application sees only slightly elevated latency, and no error surfaces. The throttle is real and it is hot, but the SDK absorbs it, which is why a hot partition can run for a long time before anyone notices, masquerading as a latency problem rather than a capacity one.

The retry budget is finite, and when a partition is hot enough that retries exhaust before a request succeeds, the SDK finally surfaces the 429 to your code, often translated by an upper layer into a generic failure. This is why a hot-partition incident frequently presents as intermittent, unexplained errors under load rather than as obvious throttling: the SDK hid the early throttling and only the overflow reaches the application. Reading the request diagnostics that the SDKs expose, which record the retry count and the status codes encountered, reveals the throttling that the retry machinery concealed and points back at the per-partition metric. A request that succeeded only after several retries is telling you the partition is already near its ceiling, well before the errors become visible.

### Why does a bulk import suddenly start throwing 429 errors?

A bulk import drives a far higher write rate than steady-state traffic, and if the writes concentrate on one partition through a low-cardinality or monotonic key, that partition saturates immediately while the import exhausts the retry budget. Spread the import across key values, throttle the client write rate, or temporarily raise throughput for the load.

Bulk operations are where this surfaces most violently. A bulk import or a backfill drives a write rate far above steady state, and if the items being written concentrate on one partition, that partition saturates instantly and the SDK's retry budget exhausts almost immediately, turning a quiet absorbed throttle into a flood of surfaced 429 errors. This is common during the very migrations meant to fix a hot partition, when a backfill writes the full history at high speed: if the target container is under-provisioned or, worse, the new key still concentrates the writes, the migration throttles itself. The remedies are to provision generous throughput on the target during the load and lower it afterward, to ensure the write distribution actually spreads across key values, and to tune the bulk client's concurrency so it pushes hard without overrunning a single partition. A bulk operation that throttles is doing the diagnosis for you at high volume: it reveals whether the key distributes under real write pressure, and a backfill that saturates one partition is telling you the new key is no better than the old one before you finish the migration.

Understanding the retry machinery also clarifies why monitoring on surfaced errors alone is insufficient. By the time 429 responses reach your application logs in numbers, the partition has been hot long enough to exhaust retries repeatedly, which means the problem predates the visible symptom by a wide margin. This is the case for alerting on the per-partition Normalized RU Consumption maximum rather than on application error rates: the metric pins at one hundred percent while the SDK is still successfully absorbing the throttle, giving you a head start of minutes or longer before the errors break through. Watching the cause rather than the surfaced effect is what turns a hot partition from a user-facing incident into a quiet alert you resolve before anyone outside the team notices.

## When the Read Pattern and the Write Pattern Want Different Keys

A subtler hot-partition cause appears when a single container has to serve two access patterns that pull the key in opposite directions. The write path wants a key that scatters inserts so no partition becomes an append hot spot, while the read path wants a key that co-locates the items a query needs so the read targets one partition instead of fanning out. Sometimes one key satisfies both. Often it does not, and forcing one key to serve both produces either a write hot spot or an expensive fan-out, with no single choice that escapes both. Trying to resolve this tension by compromising on a mediocre key for both paths usually yields the worst of each.

The honest resolution is to stop forcing one container to serve both patterns. The change feed lets you maintain a second container whose key is chosen for the access pattern the primary container's key cannot serve, kept current automatically as writes land in the primary. The primary container is keyed for its dominant pattern, typically writes and the most common scoped reads, and a change-feed processor reads every change from the primary and writes a copy into a secondary container keyed for the secondary read pattern. A query that would have fanned out across the primary becomes a point read or a scoped query against the secondary, and the primary container never sees that load at all. This is the materialized-view pattern, and it is the standard answer when one key cannot reconcile competing access patterns.

### Should I denormalize into a second container to avoid fan-out?

When a frequent query filters on a field that is not the key and cannot include it, yes. Maintain a second container keyed on that field, populated from the primary through the change feed, so the query becomes a scoped read against a purpose-built container instead of a fan-out that loads the primary's partitions.

The trade-off is real and worth naming so the decision is deliberate rather than reflexive. A materialized view costs additional storage, additional throughput on the secondary container, and the operational weight of a change-feed processor that must keep running and must be monitored for lag. The view is also eventually consistent with the primary, lagging by the time it takes the processor to apply each change, which is acceptable for most read patterns but not for a read that must reflect a write immediately. You accept these costs in exchange for removing a fan-out that would otherwise load the primary container's partitions on every query, and the calculus favors the view when the fan-out query is frequent and the consistency lag is tolerable. For an occasional query the fan-out may be cheaper than maintaining a whole second container, so the pattern is not free and should not be the first reach.

The deeper point is that the key is not a single global decision when access patterns diverge; it is a decision per access pattern, reconciled through the change feed rather than through a compromise key. A team that internalizes this stops searching for the one perfect key that serves every query, accepts that the primary key serves the writes and the dominant read, and builds purpose-keyed views for the rest. This is how high-scale Cosmos DB designs avoid both the write hot spot and the fan-out at once, and it is why the change feed appears in so many of the remedies in this article. The same mechanism that closes the gap during a re-key migration also closes the gap between a write-optimized key and a read-optimized query, and recognizing that one tool serves both jobs simplifies the whole mental model.

A practical confirmation that you have hit this tension is a container where the per-partition metric is even under writes but a specific reporting or lookup query carries a high request charge and a fan-out across every partition. The writes are healthy, the key distributes inserts, and yet one query pattern remains expensive because it filters on a field the key does not serve. That is the signature that no single key will satisfy both paths, and rather than re-keying the container and trading the write distribution for the read distribution, you build the view. The diagnosis flow's cheapest rung, scoping the query to the key, fails here precisely because the query genuinely cannot include the key, so the next cheapest move is the view rather than a migration that would only relocate the problem.

## Putting the Diagnosis Into Practice

Reading about the even split is one thing; watching a partition go hot under load you created is what makes the model stick. The reproductions are short to build: a container keyed on a low-cardinality field that you hammer until one partition pins, a monotonic key that grows an append hot spot under a write loop, and a fan-out query whose charge balloons next to a scoped version of the same query. Each one shows the per-partition metric diverge in real time, and each one responds to the matching fix in the diagnosis table. You can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to stand up these containers, drive the load, and watch the metrics move, so the mechanism becomes something you have seen rather than something you have only read.

Because the value of this article is diagnostic, the practice that reinforces it is scenario-based: given a metric chart and a query log, name the cause and pick the fix from cheapest to most involved before you act. You can [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) that present exactly these situations, a pinned partition with a fan-out query, a whale tenant, a monotonic write spike, and ask you to choose between a query rewrite, a synthetic key, subpartitioning, isolation, and more throughput. Drilling the decision is what turns the even-split rule from a fact you can recite into a reflex you reach for when the alert fires at an inconvenient hour. The choice of key that prevents all of this in the first place is covered step by step in the guide to [configuring Cosmos DB keys](/2023/06/19/configure-cosmos-db-keys/), and the surfaced rate-limit error that a hot partition produces is dissected in the companion piece on how to [fix Cosmos DB 429 too many requests](/2022/09/05/fix-cosmos-db-429-rate-limit/).

## The Verdict

Cosmos DB RU throttling is a question disguised as an emergency, and the question is always the same: is the load distributed or concentrated. The per-partition Normalized RU Consumption metric answers it in seconds. If every partition rises together, the container is genuinely under-provisioned and more throughput or a lighter workload is the right response. If one partition pins while the rest stay idle, you have a hot partition, and the even-split rule tells you that adding throughput is mostly burning money, because the new capacity lands evenly while the pressure is local.

From there the diagnosis flow is a ladder you climb only as far as you must. A fan-out query that you can scope to the key, or an unindexed filter you can index, is the cheapest rung and resolves a real share of incidents with no migration at all. A low-cardinality key, a monotonic key, or a dominant value is a key-design problem, and because the key is immutable the honest fix is a change-feed-driven migration to a key chosen for cardinality, even access, and co-location. Subpartitioning and dedicated containers handle the whale-tenant case without re-keying the whole design. The expensive fixes exist for the cases the cheap ones cannot reach, and the discipline is to confirm the cheap ones are exhausted before committing to a migration you cannot reverse in place.

The durable lesson is that the best time to fix a hot partition is before the container holds a single row of production data, when the key is still a choice rather than a migration. Run the grouping query against representative sample data, walk the highest-volume read and write against the candidate key, and confirm both distribute. The five minutes that costs at design time is the same five minutes you would spend diagnosing the fire later, spent once, without the incident. Treat the partition key as the most consequential decision in the container's life, because it is, and the throttle that brought you here becomes a problem you design out rather than one you keep paying to mask.

One last framing makes the habit stick. Treat the throttle not as a capacity question but as a distribution question, and the right next move follows almost automatically. The metric answers whether load is even or concentrated, the request charge answers whether a query is doing more work than it should, and the grouping query answers whether one value carries the rest. Three cheap readings, taken in order, route you to the correct remedy and away from the reflex that empties a budget without quieting an error. Make those readings the first response to any 429, and the spend stays tied to real demand rather than to a guess.

## Frequently Asked Questions

### Q: Why does one Cosmos DB partition throttle while the others are idle?

Provisioned throughput in Cosmos DB is not a shared pool. The service divides the total you provision evenly across the physical partitions that hold the container's data, and it meters each request against the share belonging to the partition that owns it. A request targeting a partition that has spent its share is throttled with a 429, even when every other partition is nearly idle and the container's total utilization looks low. This is why the container-level average misleads so badly during a hot-partition incident: it blends one saturated partition with several quiet ones and reports comfortable headroom. The only reliable signal is Normalized RU Consumption split by physical partition, which exposes the one pinned line. Once you see a single partition at one hundred percent while the rest trace a low band, you have confirmed skew rather than a shortage, and you know that adding throughput will land mostly on partitions that were never the bottleneck.

### Q: Does a low-cardinality partition key cause RU throttling?

Yes, and it is one of the most common root causes. Cardinality is the number of distinct values the key path can take, and it sets the ceiling on how finely Cosmos DB can spread data and load. A key with only a few values, such as a status field, a country code, or a boolean flag, can produce only a few logical partitions, and a few logical partitions cannot distribute across many physical partitions no matter how much throughput you provision. Worse, the active working set usually concentrates on one value, like the pending status of new orders, so that value's partition absorbs the write-heavy and read-heavy traffic while the others sit cold. Confirm it by grouping item counts and request charges by the key value; if a small number of values hold the active load, the key cannot distribute it. The fix is a migration to a higher-cardinality key, because the partition key is immutable once the container exists.

### Q: How do I find a hot partition in Cosmos DB metrics?

Open Azure Monitor or the Insights blade for the Cosmos DB account and chart Normalized RU Consumption, then split it by the PhysicalPartitionId dimension rather than viewing the account-level aggregate. A healthy container shows partitions clustered at similar moderate values. A container with a hot partition shows one line pinned near one hundred percent while the others stay in a low band. That divergent line is the hot partition, and its identifier is the starting point for finding which key values concentrate the load. You can reproduce the read with the Azure CLI by listing the NormalizedRUConsumption metric with the PhysicalPartitionId dimension over the incident window, which gives you a table you can inspect or pipe into a script. The discipline is to always reach for the per-partition split before trusting any aggregate, because the aggregate is exactly the view that hides skew.

### Q: Why does one query consume so many request units?

A query charges request units in proportion to the work the engine does, not the rows it returns, so a query that scans far more than it yields is expensive even when the result is tiny. The two biggest amplifiers are cross-partition fan-out and unindexed filters. A query that omits the partition key from its filter cannot route to a single partition, so the engine fans it out to every physical partition and each one spends units evaluating the predicate. A filter on a field that is not indexed forces a scan of the data rather than a lookup in the index, multiplying the cost again. Read the charge from the `x-ms-request-charge` header and the query metrics to see how many partitions were touched and how much was scanned; a high charge with a small result and a touched-partition count equal to your physical-partition count is the signature of a wasteful fan-out. Adding the partition key to the filter or indexing the filtered field collapses the cost.

### Q: How do I fix a hot partition that needs a new partition key?

Because the partition key cannot be changed in place, the fix is a migration to a new container with the corrected key. Create the target container with the better key and generous throughput for the backfill, then use the change feed to copy the data. Read the source change feed from the beginning to backfill the full history, computing the new key value for each item as you write it to the target, and keep consuming the feed so that writes arriving during the backfill flow into the target within seconds. When the target has caught up, cut the application's writes over to it, let the feed drain the final changes, and retire the source. This pattern achieves the cutover without downtime or lost writes, because the change feed closes the gap between the snapshot you backfilled and the live writes that landed afterward. Validate the new key against the grouping query before migrating, so you do not move a hot spot to a second poorly chosen key.

### Q: Does a cross-partition query waste request units?

It often does, sometimes dramatically. A cross-partition query fans out to every physical partition because the engine cannot route it to one without the partition key in the filter, and each participating partition spends request units scanning its data. A query that returns a handful of rows can charge hundreds of units if it scanned a large container across every partition to find them, and at a high call rate that single query can dominate the request-unit consumption of the entire container. The waste compounds when the filtered field is not indexed, forcing a full scan rather than an index lookup. Inspect the request charge and query metrics for the operation; a high charge, a small result, and a touched-partition count equal to your partition count confirm the fan-out. Add the partition key to the filter if the access pattern allows it, index the filtered field if it does not, or build a materialized view in a second container keyed on the queried field and kept current through the change feed.

### Q: Why do I still get 429 errors with high provisioned throughput?

Because provisioned throughput is split across physical partitions and consumed per partition, not from a shared pool. A single hot partition throttles at its even share of the total regardless of how high you set the container's provisioned throughput, so a richly provisioned container still returns 429 responses when one partition saturates. The container total is a red herring during a hot-partition incident; the real measure is per-partition consumption. Raising the total adds capacity evenly across all partitions, so the hot one gains only its even share of the increase while you pay for the increase everywhere, which is why over-provisioning rarely resolves the throttling and reliably inflates the bill. Confirm with the per-partition Normalized RU Consumption metric: if one partition is pinned while others are idle, more throughput is the wrong tool, and a query rewrite or a key change is the correct response.

### Q: What is Normalized RU Consumption and how do I read it?

Normalized RU Consumption is a metric that reports, as a percentage, how close a partition came to its allocated throughput in a given interval. One hundred percent means the partition spent its entire allocation for that interval and any further request in that window was throttled. The metric is the single most useful signal for hot-partition diagnosis because it is reported per physical partition, so splitting it by the PhysicalPartitionId dimension shows you whether one partition is pinned while others are idle, which is skew, or whether all partitions rise together, which is a genuine shortage. Read it with the maximum aggregation across partitions rather than the average, because an average across one hot and several cold partitions stays misleadingly low. The metric is what tells you, before you spend money or schedule a migration, which kind of throttling you are facing and therefore which remedy applies.

### Q: How do I change a Cosmos DB partition key safely?

You cannot change it in place, so safety comes from the migration design. Build it on the change feed so no writes are lost during the cutover. Create the new container with the corrected key and ample throughput for a write-heavy backfill, read the source change feed from the beginning to populate the target while computing the new key per item, and keep reading the feed so writes that land during the backfill stream into the target. When the target has caught up to the source, switch the application's writes to the target, allow the feed to drain the last changes, and decommission the source. Validate the proposed key first by running the grouping query against a representative sample to confirm the values distribute and no single value dominates. Provision generous throughput on the target during the migration to avoid making the backfill itself a throttling problem, then lower it once the cutover completes and the container settles.

### Q: What makes a partition key likely to run hot?

Three weaknesses produce hot partitions. Low cardinality means too few distinct values to spread across many partitions, so the active value's partition carries the load. Monotonic ordering means values increase with insertion time, so all concurrent writes share the current value and pile onto one partition as an append hot spot, even though the key is unique over time. A dominant value means the key has high cardinality overall but one value, often a large tenant, carries far more traffic or storage than the rest and saturates its own partition. A key is safe when it has high cardinality, distributes access evenly so no value dominates, and co-locates items that are read together. Synthetic keys that concatenate fields manufacture cardinality and break monotonicity, and hierarchical keys add levels so a dominant first-level value subpartitions by its second level. Reasoning about all three weaknesses at design time is far cheaper than the migration that fixes them later.

### Q: When should I add request units instead of changing the partition key?

Add request units only when the metrics show every physical partition rising toward its ceiling together, which means the load is distributed and the container is genuinely asked to do more than its provisioned throughput allows. In that case more capacity, or autoscale to raise the ceiling with demand, or a lighter per-request cost through tighter indexing and smaller items, is the correct and migration-free response. Do not add request units when one partition is pinned while the others are idle, because the increase is divided evenly across all partitions and four-fifths or more of it lands where there was never any pressure, so the hot partition gains little while the bill rises everywhere. The per-partition Normalized RU Consumption metric is the arbiter: uniform high consumption justifies more throughput, while a single pinned partition calls for a query rewrite or a key change instead.

### Q: What is a synthetic partition key and when do I use it?

A synthetic partition key is a value you compute and store on each item by combining two or more fields, used when no single natural field satisfies cardinality, even distribution, and co-location at once. The most common use is breaking a monotonic key. Telemetry keyed on a timestamp creates an append hot spot because all writes in the current second share one value; a synthetic key that concatenates the device identifier with an hour bucket scatters those concurrent writes across as many values as you have active devices while keeping a device's readings co-located for querying. You build the key at write time and persist it on the item, then use it in queries to route reads to a single partition. The synthetic key requires a migration if you are introducing it on an existing container, because you are changing the key path, so it is most valuable as a design-time decision when you can see the write pattern and choose to scatter it deliberately.

### Q: What is a hierarchical partition key and how does it help?

A hierarchical partition key, also called subpartitioning, lets you define a key with multiple levels, such as a tenant identifier followed by a user identifier or a date bucket. Cosmos DB partitions on the combination, so a single first-level value that would otherwise be bounded to one physical partition can spread across multiple physical partitions by its second-level values. This is the cleanest fix for the dominant-value problem in multi-tenant systems, where most tenants are small and fit comfortably in one partition but a few large tenants would saturate their own. Subpartitioning keeps the schema uniform and avoids special-casing the large tenants in application code, while queries scoped to a tenant remain efficient because they target the tenant's hash range. When even subpartitioning strains under an extreme outlier, the alternative is moving that tenant to a dedicated container with its own throughput, which isolates it completely at the cost of routing logic in the application.

### Q: How does the change feed help fix a hot partition?

The change feed is an ordered record of every create and update in a container, and it is the mechanism that makes a zero-downtime re-key migration practical. Because the partition key is immutable, fixing a hot partition caused by a bad key requires migrating data to a new container with a better key, and the risk in any migration is losing writes that land in the source after the copy begins. Reading the change feed from the beginning lets you backfill the entire history into the target, and continuing to read it captures every subsequent write in near real time, so the target stays current while the application still writes to the source. When the target has caught up, you cut over, let the feed drain the last changes, and the migration completes without a maintenance window. The change feed also powers materialized views: a second container keyed on a frequently queried non-key field, kept current by the feed, turns a fan-out query into a point read and offloads the primary container's hot partition.

### Q: Will enabling autoscale fix a hot partition?

No. Autoscale raises and lowers the provisioned throughput between a floor and a ceiling you set, billed by the peak each hour, and it is genuinely useful for distributed workloads with variable demand. But it does nothing for a hot partition except raise the ceiling from which each partition's even share is computed, so on a skewed container autoscale scales your cost with the hot partition's appetite while the cold partitions ride along at inflated allocations they never use. It is a capacity tool, not a skew tool, and reaching for it to silence a hot partition is the same mistake as manually over-provisioning, just automated and therefore easier to leave running. Diagnose the skew with the per-partition metric first; if one partition is pinned while the others are idle, autoscale will inflate the bill without resolving the throttle, and the real fix is a query rewrite or a key change.

### Q: How can I tell a hot partition from a normal partition split?

As a container grows past the per-partition storage ceiling, Cosmos DB splits a physical partition into two and redistributes data, and during that redistribution there can be brief elevated latency or transient throttling. This is normal and self-resolving, and the tell that distinguishes it from a hot partition is timing and persistence. A split-related blip coincides with growth, lasts only as long as the redistribution, and clears on its own once the split completes. A hot partition persists, tracks a specific key value or access pattern rather than overall size, and does not resolve until you change the query or the key. If you see elevated metrics that subside after a split finishes, you witnessed a benign redistribution. If the elevated per-partition consumption continues and one partition stays pinned independent of any split activity, you have a genuine hot partition and the diagnosis flow applies.

### Q: Does a broad indexing policy contribute to throttling?

It can, and it is a contributor people often overlook. Every write charges request units for each indexed path it updates, so a container that indexes every property, which is the default, makes writes more expensive than a container that indexes only the paths you actually query. Under heavy write load that elevated per-write cost raises consumption across partitions and can tip a busy partition over its ceiling, presenting as throttling. The distinguishing feature from a true hot partition is that narrowing the indexing policy to the queried paths drops the write charge and eases the throttling, whereas a genuine hot partition persists regardless of indexing because the load is concentrated by the key. Review the indexing policy as part of any throttling investigation, exclude paths you never filter or sort on, and re-measure the per-write charge; if it falls and the throttling eases, the index was carrying load the design did not need.

### Q: What per-operation signal tells me a query is too expensive?

The request charge, returned on every response in the `x-ms-request-charge` header and exposed by the SDKs as a RequestCharge property, is the direct measure. Read it for your highest-volume operations and watch for charges that are large relative to the data returned, which indicates the engine scanned far more than it yielded. Pair the charge with the query metrics, which report how many partitions the query touched and how much data it scanned, to see whether a high charge comes from a cross-partition fan-out. A useful preventive habit is to log the request charge of representative operations over time and chart it, because a query that drifts from scoped to fan-out, often through a feature change that drops the partition key from a filter, shows up as a rising per-call charge well before it saturates a partition. Catching that drift in monitoring turns a slow regression into something you notice and correct before it becomes an incident.

### Q: How do I set up an alert that actually catches a hot partition?

Configure a metric alert on Normalized RU Consumption using the maximum aggregation across physical partitions, not the average, and fire it when the maximum sustains above a threshold in the eighty to ninety percent range for several minutes. The maximum is the critical choice, because it captures the busiest partition while an average blends the hot one with the cold ones and stays misleadingly low, so an average-based alert will sleep through every hot-partition incident you have. The sustained window filters out brief bursts that the SDK retries absorb, leaving the persistent pinning that signals real skew. Pair the alert with a dashboard that always shows the per-partition breakdown so the responder opens directly to the chart that names the hot partition. With this in place, skew announces itself before the throttle reaches users, and the responder arrives at the metric that distinguishes a hot partition from a genuine shortage in seconds rather than minutes.

### Q: Can I prevent hot partitions entirely at design time?

You can prevent the great majority of them, which is why design-time key choice is the highest-leverage work in this whole area. Reason about three properties together before the container exists. Cardinality must be high enough that values spread across many physical partitions as the container grows. Access must distribute evenly so no single value, and no monotonic edge, concentrates the load. Co-location must hold so items read together share a key value and reads target one partition. Run the grouping query against representative sample data with the candidate key to confirm the values distribute and none dominates, and walk the highest-volume write and the highest-volume read against the key to confirm both spread rather than concentrate. When no natural field satisfies all three, a synthetic key that concatenates fields or a hierarchical key that adds levels usually does. The five minutes this costs at design time is the same diagnosis you would otherwise run during an incident, spent once and without the outage.
