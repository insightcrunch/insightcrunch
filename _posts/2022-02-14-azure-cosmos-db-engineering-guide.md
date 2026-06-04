---
layout: post
title: "Azure Cosmos DB: The Engineering Guide"
page_title: "Azure Cosmos DB: The Complete Engineering Guide to Partition Keys, Request Units, and Consistency Levels"
date: 2022-02-14
categories: ["Technology"]
tags: ["Azure", "Cosmos DB", "Architecture", "Performance", "Cloud Computing"]
excerpt: "Azure Cosmos DB lives or dies by the partition key. Learn the RU model, the five consistency levels, and how to design a container that scales, not throttles."
image: "/assets/images/blog/blog-39.webp"
reading_time: 62
author: "nathan-cole"
last_updated: 2022-02-14
lang: en
---
Most teams adopt Azure Cosmos DB for the promise on the label: a globally distributed database with single-digit-millisecond reads, elastic scale, and a tunable consistency dial. Then the first production load test arrives, the application starts returning 429 responses, and someone doubles the provisioned throughput, watches the bill climb, and discovers the throttling has not moved. The gap between using Cosmos DB and understanding it is wide, and it is almost always the same gap: every behavior that matters, the scale ceiling, the cost, the throttling, the query speed, follows from two design choices made at container creation. One is the partition key. The other is the throughput model. Get those two right and the rest of the service behaves the way the label promised. Get the partition key wrong and no amount of money buys your way out.

This guide builds the mental model an engineer needs to reason about Cosmos DB at the level where production incidents actually happen, rather than at the level where the marketing happens. We will work from the resource hierarchy down through logical and physical partitions, treat request units as the unit of currency they really are, walk the five consistency levels and what each one costs you, and finish with a partition-key scorecard you can apply to any container before you ever write a query.

![Azure Cosmos DB engineering guide to partition keys, request units, and consistency - Insight Crunch](/assets/images/blog/blog-39.webp)

## What Azure Cosmos DB Actually Is: The Mental Model to Hold

Azure Cosmos DB is a fully managed, globally distributed database that stores semi-structured items and serves them with latency and availability guarantees backed by a financial SLA. The framing that helps most is to stop thinking of it as a single database server in a region and start thinking of it as a partitioned, replicated index spread across a set of machines, where your data layout decides which machine serves any given request.

### What is Azure Cosmos DB and how is it distributed?

Azure Cosmos DB is a managed NoSQL service that horizontally partitions your data across many backend machines and replicates each partition across regions you select. You write to a logical container; the platform spreads the physical storage and the request capacity across nodes automatically, scaling out rather than up.

That last sentence carries the whole design. A traditional relational database scales up: you give one server more CPU, more memory, faster disks. Cosmos DB scales out: it adds machines and splits your data across them. Scaling out is what makes the global, elastic story possible, and it is also why the partition key matters so much. The key is the instruction that tells the platform how to split your data. Choose a key that splits evenly and the load spreads across every machine. Choose one that does not and the load piles onto a single machine while the others sit idle, which is the root of most throttling complaints.

### The resource hierarchy: account, database, container, item

Four nested resources make up the model, and getting the vocabulary exact prevents a lot of confused troubleshooting later. At the top sits the **account**, the billing and global-distribution boundary. An account is bound to a single API (more on that shortly) and holds the list of regions your data replicates to. Inside an account live one or more **databases**, which are mostly organizational containers and, optionally, a place to provision shared throughput. Inside a database live **containers**, the unit that actually holds data and, in most designs, the unit that carries throughput and a partition key. A container is called a collection in the MongoDB API, a table in the Cassandra and Table APIs, and a graph in the Gremlin API, but it is the same underlying object. At the bottom sit **items**: the individual JSON documents, rows, or graph elements you read and write.

The container is where the engineering lives. When you create one, you make two decisions that shape everything: you name the partition-key path, and you decide how throughput is supplied. Those two choices are far harder to change later than anything else about the service, which is why the rest of this guide keeps returning to them.

A useful habit is to picture a container not as a table but as a dictionary of partitions. Each distinct value of the partition key opens a logical bucket. All items sharing a key value land in the same bucket and are guaranteed to be co-located, which is what makes a single-partition query fast and a transactional batch possible. Items with different key values may live on entirely different machines. Hold that picture and the throttling behavior, the query-cost behavior, and the transaction scope all become predictable rather than surprising.

## How Cosmos DB Works Internally at the Level You Need

You do not need the source code to operate Cosmos DB well, but you do need the layer of internals that explains why a container throttles, why a query fans out, and why adding throughput sometimes helps and sometimes does nothing. That layer is the relationship between logical partitions, physical partitions, and the partition key.

### How does a partition key map to physical storage?

The partition key value is hashed, and the hash determines a logical partition. The platform groups logical partitions onto physical partitions, the actual storage-and-compute nodes. A physical partition has a fixed ceiling on storage and on request units per second, so when a container grows past those ceilings the platform splits it into more physical partitions.

Walk that mechanism slowly because it is the crux of the whole service. A **logical partition** is the set of all items that share one partition-key value. If your key is `/customerId`, then every item for customer A forms one logical partition, every item for customer B forms another, and so on. A logical partition has a hard storage ceiling (commonly cited as 20 GB, a value worth confirming against the current official limits, since these change), and it cannot be split. This is the first design constraint: any single key value whose items will exceed that ceiling is a key you cannot use, full stop.

A **physical partition** is the real backend resource: a replica set of machines that stores some range of the hashed key space and serves requests against it. The platform decides how many physical partitions a container has based on two pressures, the total stored data and the total provisioned throughput. As either grows, the platform adds physical partitions and redistributes the logical partitions across them. You never manage physical partitions directly; you influence their behavior only through your key choice and your throughput setting.

The link between the two layers is the source of the most expensive misunderstanding in the service. Provisioned throughput is divided as evenly as possible across the physical partitions. If a container has 10,000 request units per second and ten physical partitions, each physical partition gets roughly 1,000 of them. A request that lands on a physical partition can only draw from that partition's share. So if your access pattern concentrates traffic on the logical partitions that happen to live on one physical partition, that single physical partition's slice of throughput is your real ceiling, not the container total. You can have 9,000 unused request units across the other nine physical partitions while the hot one returns 429 after 429. That is the hot-partition problem, and it is why throwing throughput at throttling so often fails.

### Why does adding throughput sometimes do nothing?

Because provisioned throughput is split across physical partitions, raising the container total only helps if the extra capacity lands where the traffic is. When a single partition-key value is hot, its physical partition still gets only its proportional slice, so the bottleneck stays in place while every other partition wastes the increase.

There is a subtle second-order effect worth knowing. Raising provisioned throughput high enough can trigger the platform to add physical partitions, which redistributes the key space and can dilute a hot spot, but only if the heat is spread across several key values rather than concentrated on one. If a single key value is taking all the traffic, more physical partitions do not help, because that one logical partition still lives on exactly one physical partition and draws from that one slice. The fix in that case is never more throughput; it is a better key. We will return to this when we build the scorecard.

## Request Units: The Currency of Throughput

Cosmos DB does not bill or limit you in CPU, IOPS, or connections. It abstracts all of those into a single normalized currency called the request unit, abbreviated RU. Understanding RUs is what lets you predict cost and capacity before you deploy, instead of discovering them on the invoice.

### What is a request unit and how is throughput measured?

A request unit is a normalized cost for a database operation that rolls together CPU, memory, and IO into one number. Reading a small item by its id and partition key costs a fixed, low amount; queries, writes, and large items cost more. Throughput is measured in request units per second (RU/s), the capacity you provision or consume.

The canonical anchor most engineers memorize is that a point read of a 1 KB item costs 1 RU. From there, everything scales by work done. A write of that same item costs several RUs because indexing the new document is more expensive than fetching an existing one. A query costs RUs proportional to how many items it has to examine and how much of the index it touches, not to how many items it returns. That distinction trips people constantly: a query that returns three rows but had to scan a million to find them is expensive, while a query that uses the index efficiently to return the same three rows is cheap. The returned row count is not the cost driver; the work the engine did is.

Every response carries the exact charge for the operation in a header (`x-ms-request-charge` in the NoSQL API, surfaced as `RequestCharge` in the SDKs). This is the single most useful diagnostic in the entire service, and most teams ignore it. If you log the request charge for your hot paths during development, you can multiply by your expected requests per second and size your container with arithmetic instead of guesswork. A read path that costs 1 RU at 5,000 reads per second needs 5,000 RU/s for that path. A poorly indexed query that costs 50 RUs at the same rate needs 250,000 RU/s, which is a wildly different bill and an immediate signal to fix the query before you provision anything.

### What drives the cost of an operation up?

Item size, the number of indexed properties, query complexity, consistency level, and whether a query stays within one partition all move the charge. A point read by id and partition key is the floor. A cross-partition query that scans many partitions and sorts results is near the ceiling, sometimes hundreds of RUs for a single call.

Indexing deserves a paragraph of its own because it is the lever most teams never touch. By default, Cosmos DB indexes every property of every item. That default makes ad-hoc queries fast without thought, but it also makes writes more expensive, because every indexed property must be updated on every write, and it inflates storage. For a write-heavy workload with a known, narrow query pattern, customizing the indexing policy to index only the properties you actually filter or sort on can cut write charges substantially. The reasoning to internalize is that indexing trades write cost and storage for read flexibility, and the default sits at maximum read flexibility, which is rarely what a high-throughput production path wants. Tuning this, alongside the partition strategy, is the heart of [the deeper RU and throughput optimization work covered later in the series](/2024/08/26/cosmos-db-throughput-optimization/).

## The Throughput Models: Provisioned, Autoscale, and Serverless

Once you understand RUs as currency, the three ways to supply them become a real decision rather than a default you accept. Each model fits a different traffic shape, and choosing by traffic shape rather than by familiarity is how you avoid both throttling and waste.

### Should I use provisioned, autoscale, or serverless throughput?

Use standard provisioned throughput for steady, predictable load where you can size the floor accurately. Use autoscale when traffic swings between a baseline and bursts, because it scales between ten percent and one hundred percent of a ceiling automatically. Use serverless for spiky, low-average, or intermittent workloads that would waste a provisioned floor.

**Standard provisioned throughput** reserves a fixed RU/s figure that you set, and you pay for that reservation whether you use it or not. It rewards accurate sizing: if your load is steady and you have measured your request charges, provisioned throughput is the cheapest way to serve it, because you are not paying any autoscale or serverless premium per operation. Its weakness is the mirror image: if your load is bursty, you must provision for the peak and pay for that peak around the clock, or provision for the average and throttle during peaks.

**Autoscale** lets you set a maximum RU/s, and the platform scales the actual provisioned capacity between ten percent of that maximum and the full maximum based on observed utilization, adjusting within seconds. You pay a per-RU premium over standard provisioned in exchange for not having to size the peak yourself or eat throttling during a spike. The decision rule is utilization: if your container would sit above roughly two-thirds average utilization of a fixed provisioned number, standard is usually cheaper; if it would swing widely and spend much of its life idle between bursts, autoscale usually wins despite the premium. Confirm the exact premium and the ten-percent floor against the current pricing, since both have moved over time.

**Serverless** removes provisioning entirely and bills purely per request unit consumed, with no reservation. It is the right model for development environments, for genuinely intermittent workloads, and for new applications whose traffic you cannot yet predict. Its constraints are real: serverless containers have a lower throughput ceiling and a lower storage ceiling than provisioned ones, and they run in a single region, so a multi-region production workload cannot use it. The mental test is average utilization over time: a workload that is busy most of the time wants provisioned or autoscale; a workload that is quiet most of the time and occasionally active wants serverless.

A common and effective pattern combines models across the resource hierarchy. You can provision throughput at the database level to share a pool across many low-traffic containers, while giving a hot container its own dedicated provisioned or autoscale throughput so it cannot be starved by its neighbors. Shared database throughput is economical for many small containers but offers no isolation, so the moment one container in the pool becomes hot, give it dedicated throughput.

## The Limits and Quotas That Shape Design

Every distributed store has limits, and in Cosmos DB the limits are not arbitrary; each one falls out of the partitioned, replicated design, so knowing them tells you how to model rather than merely what to avoid. Treat the specific numbers below as values to confirm against the current official limits, because the platform raises them over time, but treat the shapes as durable.

The limit that bites most often is the per-logical-partition storage ceiling, commonly documented at twenty gigabytes. Because a logical partition cannot be split, any single partition-key value whose items would exceed that figure is a modeling error you must design around, which is the structural reason synthetic and hierarchical keys exist. The companion to it is the per-physical-partition throughput ceiling: a single physical partition serves up to a documented maximum RU/s, so a single hot logical-partition value cannot exceed that slice no matter how high you set the container total. Together these two ceilings explain why a good key both spreads storage and spreads traffic.

Item size carries a hard limit as well, documented around two megabytes per item. That ceiling steers you away from embedding unbounded collections inside a single document, an arrays-that-grow-forever anti-pattern, and toward a model where high-growth child data is referenced rather than embedded. A single request also has a payload ceiling and a maximum request-unit charge it may consume, which is one more reason a runaway cross-partition query is something to design out rather than tune around.

On the throughput side, the supply models impose their own bounds. A container with provisioned throughput has a minimum RU/s it cannot go below, scaled by its stored data, so a very large container retains a floor cost even when idle. Autoscale operates over a fixed range, scaling between ten percent and one hundred percent of the maximum you set, which means a workload that needs a wider dynamic range than ten to one is a poor autoscale fit. Serverless containers cap at lower throughput and storage ceilings than provisioned ones and run in a single region, which is why serverless is a development and intermittent-workload model rather than a global-production one. The global story has its own quota: an account can replicate across many regions, but each added region multiplies both your storage cost and, under multi-region writes, your write cost, so the region list is a deliberate cost-and-latency decision, not a free resilience upgrade.

The practical move is to read these limits as modeling instructions. The logical-partition storage ceiling says keep any single key value's data bounded. The physical-partition throughput ceiling says spread the traffic. The item-size ceiling says reference unbounded child collections rather than embedding them. The autoscale range says match the supply model to the dynamic range of the load. Read this way, the quota table stops being a list of restrictions and becomes a design checklist that the well-architected container already satisfies.

Cosmos DB exposes a consistency dial with five named settings, a finer-grained control than most databases offer, and the reason the dial exists is that consistency, latency, and availability cannot all be maximized at once. Tightening consistency costs you latency and, in some failure scenarios, availability; loosening it buys speed and resilience at the price of possibly reading slightly stale data. The skill is matching the level to what the workload genuinely requires rather than reflexively choosing the strongest.

### Which Cosmos DB consistency level should I choose?

Default to session consistency, which guarantees that a client reads its own writes and sees monotonic progress within a session, and covers most application needs at low cost. Step up to bounded staleness or strong only when a workload cannot tolerate any staleness, and accept the added latency that choice imposes.

The five levels form a spectrum from strongest to weakest. **Strong** consistency guarantees a linearizable view: any read returns the most recent committed write, as if there were a single copy of the data. This is the most intuitive model and the most expensive one, because in a multi-region account it requires reads to coordinate across regions, which adds latency, and it constrains how the system behaves during a partition. Strong consistency is also incompatible with multi-region writes, a constraint that surprises teams who want both maximum consistency and maximum write availability.

**Bounded staleness** guarantees that reads lag writes by no more than a configured bound, expressed as a number of versions or a time interval. Within that bound, reads may be stale; beyond it, they are guaranteed current. It gives you a tunable, predictable staleness window, which suits workloads that need near-strong behavior but can tolerate a defined lag.

**Session** consistency is the default and the right answer for the large majority of applications. It guarantees consistency within a single client session: a client reads its own writes, never sees time go backward, and sees writes in order, all scoped to that session's context. Different sessions may briefly see different states, but each user's own experience is coherent, which is exactly what most interactive applications need. It delivers this at low latency and low RU cost.

**Consistent prefix** guarantees that reads never see writes out of order; you might not see the latest write, but you will never see write three before writes one and two. **Eventual** consistency, the weakest, guarantees only that replicas converge over time, with no ordering guarantee in the interim. Both suit workloads where freshness matters little and throughput and availability matter most, such as view counters, telemetry, or non-critical feeds.

The trade-off to hold in mind is that you set a default consistency at the account level, and you can relax it per request (asking for a weaker level on a specific read to save latency) but the SLA-backed guarantees apply to the account default. The engineering move is to default to session, then identify the specific operations that genuinely need stronger guarantees and the specific reads that can tolerate eventual, rather than picking one level for everything. The full derivation of what each level guarantees during region failover, and how the staleness bounds are measured, is the subject of [the dedicated consistency-models analysis later in the series](/2025/09/29/cosmos-db-consistency-models/).

## Global Distribution and the Multi-Region Write Model

The headline feature of Cosmos DB is the ability to replicate your data to any of the Azure regions with a few clicks and serve reads and writes from the region nearest each user. This is genuinely powerful, and it also introduces the trade-offs that the consistency dial exists to manage.

Adding a region to an account replicates all of the account's data to that region and lets clients there read locally, cutting latency to the nearest replica. This is **single-region write with multi-region reads** by default: one region is the write region, and the others are read replicas. It is simple to reason about and pairs cleanly with strong or bounded-staleness consistency.

Turning on **multi-region writes** (sometimes called multi-master) lets every region accept writes locally, which removes the cross-region write latency entirely and improves write availability, because losing one region does not stop writes elsewhere. The cost is conflict: two regions can write the same item at the same time, and the system must resolve which write wins. Cosmos DB offers conflict resolution policies, the default being last-writer-wins based on a timestamp, with the option of a custom resolution procedure. The engineering reality is that multi-region writes are excellent for workloads where writes to the same item from different regions are rare or where last-writer-wins is acceptable, and they are a trap for workloads where conflicting concurrent writes to the same item are common and the resolution actually matters. Choose multi-region writes deliberately, with a conflict story you have thought through, not as a default toggle.

Region failover is the other half of the global story. You configure a priority order for regions, and if the write region becomes unavailable the platform can fail over to the next region automatically (if enabled) or on manual trigger. The recovery objectives you can achieve depend on the consistency level: stronger consistency means less potential data loss on failover but more latency in normal operation, which is the same trade-off viewed through the lens of disaster recovery rather than steady-state reads.

## The APIs: NoSQL, MongoDB, Cassandra, Gremlin, and Table

Cosmos DB presents the same underlying engine through several API surfaces, and the choice among them is mostly about compatibility with what you already have, not about a difference in the core capabilities.

### Which Cosmos DB API should I build on?

Choose the NoSQL (Core) API for new applications, because it exposes every feature first and has the deepest tooling. Choose the MongoDB, Cassandra, Gremlin, or Table API when you are migrating an existing application built on one of those and want wire-protocol compatibility so the code mostly works unchanged.

The **NoSQL API** (historically the SQL or Core API) is the native interface and the one that receives new features earliest. It speaks a SQL-like query language over JSON documents and has the richest SDK support, the best integration with change feed and the analytical store, and the most complete control over indexing. For anything greenfield, this is the default, and it is the API this guide's examples assume.

The **MongoDB API** implements the MongoDB wire protocol, so existing MongoDB applications and tools can connect to Cosmos DB with a connection-string change and minimal code edits. It is the migration path for teams with a MongoDB codebase who want a managed, globally distributed backend without rewriting their data layer. The **Cassandra API** does the same for Cassandra Query Language workloads, the **Gremlin API** offers a graph interface for traversal-heavy data, and the **Table API** provides a richer, globally distributed successor to Azure Table Storage. All of them sit on the same partitioned, RU-metered engine underneath, so the partition-key reasoning, the RU model, and the consistency levels in this guide apply to every one of them, even when the surface vocabulary differs.

The one durable warning is that compatibility APIs implement a version of the target protocol, not every feature of the original product, so a migration should always include a compatibility test against the specific features and operators your application uses. The core engine is the same; the API surface is a translation layer, and translation layers have edges.

## Creating and Configuring a Container: The Commands That Matter

Theory becomes operational the moment you create an account and a container, so this section walks the configuration that actually shapes behavior, with commands you can run. The order of operations matters: you create the account (choosing the API, which is permanent for that account), then a database, then a container where you set the partition key and the throughput.

A minimal account and container created with the Azure CLI looks like this for the NoSQL API:

```bash
# Create the account (the API choice is fixed for the life of the account)
az cosmosdb create \
  --name ic-cosmos-demo \
  --resource-group ic-rg \
  --kind GlobalDocumentDB \
  --default-consistency-level Session \
  --locations regionName=eastus failoverPriority=0 isZoneRedundant=False

# Create a database
az cosmosdb sql database create \
  --account-name ic-cosmos-demo \
  --resource-group ic-rg \
  --name appdb

# Create a container with an explicit partition key and provisioned throughput
az cosmosdb sql container create \
  --account-name ic-cosmos-demo \
  --resource-group ic-rg \
  --database-name appdb \
  --name orders \
  --partition-key-path "/customerId" \
  --throughput 4000
```

Three of those flags are the consequential ones. The `--default-consistency-level` sets the account-wide guarantee discussed earlier, defaulting to `Session` here, which is the sensible starting point. The `--partition-key-path` is the immutable choice the scorecard exists to inform; once data lands in this container, that path cannot change. The `--throughput` sets a fixed provisioned figure. To use autoscale instead, you swap `--throughput` for `--max-throughput`, which sets the autoscale ceiling and lets the platform scale between ten percent of it and the full value:

```bash
az cosmosdb sql container create \
  --account-name ic-cosmos-demo \
  --resource-group ic-rg \
  --database-name appdb \
  --name orders \
  --partition-key-path "/customerId" \
  --max-throughput 40000
```

To declare a hierarchical partition key, you pass multiple paths in priority order, which lets the platform route at the first level and still subdivide a high-volume top-level value underneath:

```bash
az cosmosdb sql container create \
  --account-name ic-cosmos-demo \
  --resource-group ic-rg \
  --database-name appdb \
  --name events \
  --partition-key-path "/tenantId" "/deviceId" "/yyyyMM" \
  --partition-key-version 2 \
  --max-throughput 40000
```

### How do I read what an operation actually costs?

Read the request-charge header on every call during development. In the .NET SDK the response object exposes `RequestCharge` directly; in other SDKs it surfaces the same `x-ms-request-charge` header. Log that figure for each hot path, and you size capacity from measured numbers rather than guesses.

The discipline that separates teams who succeed from teams who chase throttling is logging that charge while building. A short read path in the .NET SDK makes the pattern concrete:

```csharp
// A point read: the cheapest possible operation
ItemResponse<Order> response = await container.ReadItemAsync<Order>(
    id: orderId,
    partitionKey: new PartitionKey(customerId));

double charge = response.RequestCharge;   // e.g. 1.0 for a small item
logger.LogInformation("Point read cost {Charge} RU", charge);

// A query: cost depends on work done, not rows returned
QueryDefinition query = new QueryDefinition(
    "SELECT * FROM c WHERE c.customerId = @cid AND c.status = @status")
    .WithParameter("@cid", customerId)
    .WithParameter("@status", "open");

// Scoping to the partition key keeps this single-partition and cheap
using FeedIterator<Order> iterator = container.GetItemQueryIterator<Order>(
    query,
    requestOptions: new QueryRequestOptions
    {
        PartitionKey = new PartitionKey(customerId)
    });

double totalCharge = 0;
while (iterator.HasMoreResults)
{
    FeedResponse<Order> page = await iterator.ReadNextAsync();
    totalCharge += page.RequestCharge;
}
logger.LogInformation("Single-partition query cost {Charge} RU", totalCharge);
```

### A worked sizing example you can copy

Suppose the orders service has two dominant paths. The first is a point read of an order by id, measured at 1 RU, expected to run at 3,000 reads per second at peak. The second is a write of a new order, measured at 7 RU because the item is larger and fully indexed, expected at 400 writes per second at peak. The arithmetic is direct: the read path needs 3,000 multiplied by 1, giving 3,000 RU/s, and the write path needs 400 multiplied by 7, giving 2,800 RU/s. Summed, the container needs roughly 5,800 RU/s at peak, so a provisioned figure of 6,000 RU/s covers it with a small margin, and if the traffic is steady that fixed reservation is the cheapest way to serve it. If instead the peak occurs for two hours a day and the container is near idle the rest of the time, an autoscale ceiling of 6,000 lets the platform drop to 600 RU/s during the quiet hours, trading a per-RU premium for not paying the peak around the clock. This is the entire sizing method: measure each path's charge, multiply by its rate, sum, add margin, and choose the supply model by how the load varies through the day. The deeper variations, including how to spot a path whose charge is quietly inflating your bill, run through [the throughput and RU optimization guide](/2024/08/26/cosmos-db-throughput-optimization/).

## Indexing Policy: The Lever Most Teams Never Touch

The indexing policy is where a write-heavy workload reclaims a large share of its request-unit budget, and it is the setting most teams leave at the default for the life of an application. By default Cosmos DB applies automatic indexing to every property of every item, including nested paths, which is why an ad-hoc query against any field returns quickly with no configuration. That convenience has a price paid on every single write, because each indexed property must be updated when an item changes, and on storage, because the index itself consumes space.

The reasoning to hold is that indexing trades write cost and storage for read flexibility, and the default sits at maximum read flexibility, which a high-throughput production path rarely needs. When you know your query shapes, you index for them and exclude everything else. A policy that includes only the paths you filter or sort on, and excludes the rest, looks like this:

```json
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    { "path": "/customerId/?" },
    { "path": "/status/?" },
    { "path": "/createdAt/?" }
  ],
  "excludedPaths": [
    { "path": "/*" }
  ]
}
```

The pattern is to exclude the wildcard root and then explicitly include the handful of paths your queries actually use. On a write-heavy container with large items and many properties, narrowing the index this way often cuts write charges by a meaningful fraction, because the engine stops maintaining index entries for dozens of fields no query ever touches. Measure the write request charge before and after the change to confirm the saving on your own data, since the exact reduction depends on item shape.

Two refinements matter for real workloads. A **composite index** accelerates queries that filter on one property and order by another, or that order by multiple properties, which the default range indexes do not serve efficiently:

```json
{
  "compositeIndexes": [
    [
      { "path": "/customerId", "order": "ascending" },
      { "path": "/createdAt", "order": "descending" }
    ]
  ]
}
```

A query such as filtering by customer and sorting by creation time descending becomes much cheaper with that composite index in place, because the engine reads the ordered result directly from the index rather than sorting in memory. The second refinement is the indexing mode itself: `consistent` (the default) keeps the index synchronized with writes, while `none` disables indexing entirely, which suits a container used purely as a key-value store accessed only by point reads, where every query is a direct id-and-partition-key lookup that needs no index at all. Switching such a container to indexing mode `none` removes the write-time indexing cost completely. The lesson across all of this is that the indexing policy is a design surface, not a fixed default, and that tuning it alongside the partition strategy is how a write-heavy Cosmos DB workload stays affordable at scale.

## Designing the Data Model: Embedding versus Referencing

The partition key decides how data spreads; the data model decides how data is shaped, and in a document store the central modeling question is whether to embed related data inside one item or to reference it across separate items. Getting this right is the difference between a read that fetches everything it needs in one cheap operation and a read that issues a fan of follow-up queries.

The guiding principle is to model for the way you read. Embed related data inside a single item when it is read together, changes together, and is bounded in size. An order with its line items is the classic case: you almost always read the order and its lines as a unit, they change as a unit, and a single order has a bounded number of lines, so embedding the lines inside the order document means one point read returns the whole order at the cost of a single request unit. Embedding turns what would be a join in a relational database into a free, co-located read.

Reference related data, storing it as separate items linked by an identifier, when it is large, when it grows without a natural bound, or when it is shared across many parents and updated independently. A product catalog referenced by many orders is the case for referencing: duplicating the full product into every order would bloat each order, would force a fan of updates whenever a product changed, and would risk the item-size ceiling. Instead each order stores a product id, and the product lives once in its own item. The cost is that reading an order plus its full product details now takes two reads rather than one, which is the trade you accept to avoid duplication and unbounded growth.

The decision is rarely all-or-nothing; the strong pattern is selective denormalization. Embed the fields you read most often alongside the reference, so the common read path is satisfied from one item and only the rare path that needs the full related entity issues a second read. An order might embed the product name and price (the fields shown on the order summary) while referencing the full product item for the rare detail view. This hybrid keeps the hot path to a single cheap read while keeping the duplicated data small and the update surface narrow. The same thinking interacts directly with the partition key: data you want to read or update together atomically should share a partition-key value so it lands in one logical partition, which is why modeling and key choice are two halves of the same design conversation rather than separate steps.

The anti-patterns are the mirror images of the principles. Embedding an unbounded collection, such as every event a device has ever emitted, inside one document drives that item toward the size ceiling and that logical partition toward the storage ceiling, and the fix is to make each event its own item under a key that spreads them. Referencing data that is always read together and never shared, such as splitting an order header from its lines into separate items, imposes a needless second read on the hottest path, and the fix is to embed. Read for the access pattern, bound every embedded collection, and let the partition key and the document shape be designed together.

## The Analytical Store and Azure Synapse Link

A frequent and reasonable worry about putting an operational workload on Cosmos DB is that analytical queries, the aggregations and scans that reporting needs, would hammer the same request-unit budget that serves production traffic and would run slowly against a row-oriented operational store. The analytical store, exposed through Azure Synapse Link, is the platform's answer to that worry, and it is worth understanding because it changes the calculus of when one engine can serve both jobs.

When you enable the analytical store on a container, Cosmos DB maintains a second, column-oriented copy of the data automatically, updated from the operational store in the background. This is a hybrid transactional and analytical processing design: the operational store stays row-oriented and serves your low-latency reads and writes, while the analytical store stays column-oriented and serves large scans and aggregations efficiently, exactly the layout analytical engines want. The two stay in sync without you writing any extract-transform-load pipeline, which removes the usual lag and operational burden of copying operational data into a separate warehouse for reporting.

The decisive property is isolation. Analytical queries run against the analytical store through Synapse, and they do not consume the container's provisioned request units, so a heavy reporting query cannot throttle the production path. This directly addresses the fear that drives many teams to copy operational data elsewhere: with the analytical store, the operational and analytical workloads share data without sharing the throughput budget, so a long aggregation over months of orders runs in Synapse without touching the request units serving live order reads. The pricing model for the analytical store is separate from the operational request-unit cost, billed on storage and on the analytical queries, so confirm the current rates when you weigh it against a separate warehouse.

The honest boundary is that the analytical store complements rather than replaces a purpose-built warehouse for the heaviest, most complex analytical estates, and it does not turn Cosmos DB into a relational analytics engine with rich cross-entity joins. What it does is let an operational Cosmos DB workload serve near-real-time analytics over its own data without an ETL pipeline and without stealing throughput from production, which for many systems removes the need to stand up and synchronize a second data store at all.

## Transactions, Stored Procedures, the Change Feed, and Time to Live

A complete model of Cosmos DB includes the features that operate on items beyond the basic read and write, because each one has a scope rule that follows directly from the partitioning design. Understanding those scope rules prevents a class of surprises that the documentation states but that teams routinely miss.

Transactional operations are scoped to a single logical partition. A **transactional batch** lets you group several item operations (creates, replaces, deletes) into one atomic unit that either all succeed or all roll back, but every operation in the batch must target the same partition-key value. This is a direct consequence of the storage layout: items in one logical partition are guaranteed co-located, so an atomic operation across them is cheap, while a transaction spanning partitions would require a distributed commit the service deliberately does not offer. The design implication is that if your domain requires atomic updates across a set of related items, your partition key should place those items in the same logical partition, which is a real input to the scorecard's query-alignment thinking. A simple transactional batch in the .NET SDK shows the constraint:

```csharp
// All operations share one partition-key value, customerId
PartitionKey pk = new PartitionKey(customerId);
TransactionalBatch batch = container.CreateTransactionalBatch(pk)
    .CreateItem(orderItem)
    .ReplaceItem(customerSummary.Id, customerSummary);

using TransactionalBatchResponse batchResponse = await batch.ExecuteAsync();
if (!batchResponse.IsSuccessStatusCode)
{
    // The whole batch rolled back; inspect batchResponse for the failing operation
    logger.LogWarning("Batch failed with status {Status}", batchResponse.StatusCode);
}
```

**Stored procedures**, triggers, and user-defined functions written in JavaScript run on the server inside a single logical partition as well, which is why a stored procedure must be invoked with a partition-key value. They suit operations where executing logic next to the data avoids multiple round trips, but they carry the same single-partition scope, so they are not a route around the cross-partition transaction limit.

**Optimistic concurrency** prevents the lost-update problem without locking. Every item carries an `_etag` that changes on each write; you read the item, get its etag, and supply that etag as a condition on your replace, which the service rejects with a 412 Precondition Failed if the item changed in the meantime. You then re-read and retry. This is the correct pattern for read-modify-write sequences on a shared item, and it is why a high rate of 449 RetryWith or 412 responses points to genuine contention on a single item that the data model might need to spread out.

The **change feed**, introduced earlier as an event source, deserves its operational detail here because it is how most serious Cosmos DB systems do replication, materialized views, and partition-key migrations. The feed is a durable, per-partition-ordered log of creates and updates. Consumers read it through the change-feed processor in the SDK, which distributes the feed's partitions across consumer instances and checkpoints progress to a lease container, so processing resumes after a restart without missing or reprocessing items. That durability and ordering is exactly what makes the feed the safe vehicle for migrating to a better partition key: you create the new container, run a change-feed processor that reads every item from the old container and writes it into the new one, and once the new container has caught up you cut traffic over, all without a maintenance window.

**Time to Live (TTL)** lets the container expire items automatically, which is the right tool for telemetry, sessions, caches, and any data with a natural lifespan. You enable it at the container level and optionally override it per item:

```bash
# Enable TTL at the container level, expiring items 30 days after last write
az cosmosdb sql container update \
  --account-name ic-cosmos-demo \
  --resource-group ic-rg \
  --database-name appdb \
  --name events \
  --ttl 2592000
```

Expired items are removed in the background using leftover throughput, so TTL deletion does not compete with your foreground traffic for request units in the way an explicit delete sweep would. The engineering value is that TTL keeps a high-ingest container from growing without bound and keeps per-logical-partition storage under the ceiling, which removes a whole category of operational toil around manual cleanup jobs.

## The InsightCrunch Cosmos Partition-Key Scorecard

Everything above converges on one decision, so it earns a concrete artifact. The partition key is the single choice that determines whether a container scales smoothly or throttles under load, and unlike throughput or consistency, it is the choice you cannot cheaply change after data exists, because changing it means migrating to a new container. Score every candidate key on three axes before you commit.

| Axis | What it measures | Strong key | Weak key | Why it matters |
| --- | --- | --- | --- | --- |
| Cardinality | Number of distinct key values | Thousands to millions of values, growing with the data | A handful of fixed values (status, region, type, boolean) | Low cardinality forces many items onto few logical partitions, capping how far the data can spread and risking the per-partition storage ceiling |
| Access distribution | How evenly read and write traffic spreads across key values | Traffic spreads roughly evenly across many values | Traffic concentrates on one or a few hot values | A hot key value pins load to one physical partition's RU slice, producing 429s while other partitions sit idle |
| Query alignment | How often your common queries filter on the key | Most high-volume queries include the key, staying single-partition | Common queries omit the key and fan out across all partitions | A query without the partition key scans every physical partition, multiplying RU cost and latency |

The scorecard turns a vague instruction ("pick a good partition key") into three testable questions. A field like `/status` with values such as `active` and `inactive` fails cardinality and almost certainly fails access distribution, because most items will be `active` and that one logical partition will take most of the traffic. A field like `/customerId` usually passes all three for a business application: there are many customers, traffic spreads across them, and most queries scope to one customer. A field like `/id` (the item id itself) has perfect cardinality but fails query alignment for any access pattern that does not look up single items by id.

When no natural field scores well on all three axes, the answer is a **synthetic key**: a property you construct specifically to be a good partition key. Two patterns dominate. A concatenated synthetic key combines two fields, for example `customerId-yyyyMM`, to raise cardinality and spread a single high-volume customer's data across monthly buckets while keeping related items together. A hierarchical partition key (a newer capability worth confirming availability for your API and region) lets you specify multiple key paths in order, so the platform can route at the top level and still subdivide hot values underneath, which directly addresses a tenant whose data outgrows a single logical partition. The rule is simple to state: a synthetic or hierarchical key beats a natural one whenever the best natural field fails any of the three axes, and the cost of constructing the key is trivial next to the cost of migrating a throttling container later. The mechanics of declaring these keys, including the hierarchical variant, are covered step by step in [the dedicated guide to configuring Cosmos DB partition keys](/2023/06/19/configure-cosmos-db-partition-keys/).

## Failure Modes and How to Avoid Them

The value of the model above is that it makes the common failures predictable. Each of the symptoms engineers search for maps to a cause you can now reason about, and to a fix that is rarely "add throughput."

The most-searched failure is **429 TooManyRequests**, the response that means a request exceeded the available throughput. A small, transient rate of 429s is normal and expected; the SDKs retry them automatically with backoff, and a low background rate is the system working as designed. The problem is a sustained, high rate of 429s, and that has two distinct causes that demand opposite responses. If the throttling spreads across many partition-key values, the container is genuinely under-provisioned, and raising throughput or moving to autoscale is the right fix. If the throttling concentrates on one or a few key values while overall consumption sits well below the provisioned total, you have a hot partition, and the fix is a better partition key, not more RUs. Diagnosing which case you are in by reading the per-partition metrics, then applying the matching remedy, is the subject of [the focused guide to fixing Cosmos DB 429 responses](/2022/09/05/fix-cosmos-db-429-rate-limit/) and [the deeper treatment of RU throttling and hot partitions](/2022/09/12/fix-cosmos-db-ru-throttling/).

**Hot-partition skew** is the underlying disease behind most 429 complaints, and it is worth naming separately because it can exist without obvious throttling, showing up instead as uneven latency or as a single partition approaching its storage ceiling. The cause is always a partition key that fails the access-distribution axis of the scorecard. The prevention is to score the key before deploying; the cure, once data exists, is to migrate to a new container with a better key, often using the change feed to replay data into the new layout with minimal downtime.

A **408 request timeout** points to network conditions, an overloaded client, or an operation that genuinely takes too long, often a cross-partition query doing more work than the timeout allows. The fix is usually to scope the query to a single partition by including the partition key, to tighten the query so it touches less of the index, or to address client-side resource exhaustion, rather than to assume the service is at fault.

A **449 RetryWith** appears on concurrent writes to the same item when an optimistic concurrency conflict occurs; it is a signal to retry the operation, and the SDKs handle it, but a high rate of 449s indicates contention on a single item that the data model should probably spread out.

The quiet, expensive failure is the **cross-partition query fan-out**: a query that omits the partition key and therefore runs against every physical partition, gathering and merging results. It does not error; it simply costs far more RUs and far more latency than a single-partition query, and at scale it drives both the bill and the throttling. The prevention is the query-alignment axis of the scorecard: design the partition key so your high-volume queries can include it, and reserve cross-partition queries for genuinely analytical, low-frequency access.

## Reproducing and Fixing a Hot Partition

The fastest way to make the hot-partition lesson permanent is to cause one on purpose and watch the metrics, because the symptom and the cure stop being abstract once you have seen the throttling appear on a container with throughput to spare. Create a container keyed on a low-cardinality field, drive load at it, and the failure reproduces reliably.

Start with a container deliberately keyed on `/region`, a field with only a few values:

```bash
az cosmosdb sql container create \
  --account-name ic-cosmos-demo \
  --resource-group ic-rg \
  --database-name appdb \
  --name skewed \
  --partition-key-path "/region" \
  --throughput 10000
```

Then push writes where the overwhelming majority carry the same region value, simulating a real-world skew where one region dominates traffic. Within seconds the writes targeting the dominant value begin returning 429, even though the container holds 10,000 provisioned RU/s and total consumption sits far below that figure. The diagnostic that confirms the diagnosis is the per-partition view: Azure Monitor exposes normalized request-unit consumption per physical partition, and a hot partition shows one partition pinned near one hundred percent while the others idle. A KQL query against the metrics surfaces the imbalance directly:

```kusto
AzureMetrics
| where ResourceProvider == "MICROSOFT.DOCUMENTDB"
| where MetricName == "NormalizedRUConsumption"
| summarize MaxNormalized = max(Maximum) by bin(TimeGenerated, 5m), PartitionKeyRangeId
| order by TimeGenerated desc
```

When one `PartitionKeyRangeId` reports a normalized consumption near one hundred while others report single digits, the throttling is a hot partition, not under-provisioning, and the metric proves it. This is the moment the partition-key-first rule earns its keep: you can now state, with evidence, that raising the 10,000 figure to 50,000 will not help, because the dominant region's data lives on one physical partition that still receives only its proportional slice.

The cure is to re-key. Migrate to a container keyed on a property that spreads the load, perhaps a synthetic key combining region with a higher-cardinality field such as `/region-deviceId`, or a hierarchical key of `/region` then `/deviceId`. The migration uses the change feed: stand up the new container, run a change-feed processor that reads each item from the skewed container and writes it into the well-keyed one, let it catch up, and cut traffic over. Because the change feed is durable and ordered per partition, the processor can be restarted safely and will not lose or duplicate items. After the cutover, the same KQL query shows consumption spread across many partition-key ranges, and the 429s vanish at the same provisioned throughput that was throttling before, which is the clearest possible demonstration that the key, not the capacity, was the constraint. The full diagnostic walk-through for distinguishing the two causes lives in [the guide to fixing Cosmos DB RU throttling and hot partitions](/2022/09/12/fix-cosmos-db-ru-throttling/).

## Securing and Operating the Account

A service deep dive is incomplete without the controls that keep an account safe and recoverable, because most production incidents that are not throttling are access or recovery problems instead. Cosmos DB separates the control plane (managing the account, its throughput, its regions) from the data plane (reading and writing items), and the security model reflects that split.

For the data plane, prefer Azure RBAC over the account's primary keys. The primary keys grant full access to all data in the account and cannot express least privilege, so embedding them in an application is the equivalent of shipping a root credential. The data-plane RBAC model instead lets you assign a managed identity a role that grants only the read or read-write data actions it needs, with no key in the application at all. The application acquires a token through its managed identity, exactly the credential-free pattern used across Azure services, and the account can then disable key-based access entirely. Combine that with the control-plane separation so the team that manages the account's configuration is not automatically the team that can read its data, and you have a posture that survives a security review.

For network exposure, the default is a public endpoint protected by access control, but a production account holding sensitive data should restrict the network surface. A firewall can limit access to specific address ranges, a service endpoint can tie access to a virtual network, and a private endpoint can remove the public surface entirely by giving the account a private address inside your network, so traffic never traverses the public internet. The private-endpoint option is the strongest and the one to reach for when compliance requires that the database not be reachable from outside the network boundary.

For recovery, Cosmos DB offers two backup modes, and the choice is consequential. Periodic backup takes snapshots on an interval and retains a number of them, with restore handled by a support process. Continuous backup, the more capable mode, records changes continuously and lets you perform a self-service point-in-time restore to any second within the retention window, which is what you want when a bad deployment corrupts data and you need to rewind to the moment before it. Continuous backup is the right default for any account where data loss matters, and it pairs naturally with the soft-delete-style safety that point-in-time restore provides. Confirm the current retention windows and any cost difference between the modes against the official documentation, since these details are revised periodically.

Operating the account well also means watching the right signals. Beyond the per-partition normalized consumption used to catch hot partitions, the metrics that earn a dashboard are the rate of 429 responses (a low background rate is fine, a sustained high rate is a problem), the server-side latency split by operation type, the request-unit consumption against the provisioned figure to spot both throttling headroom and waste, and the data and index storage per partition to catch a logical partition approaching its ceiling before it becomes an incident. Wiring those into Azure Monitor with alerts on the thresholds that matter turns the reasoning in this guide into an early-warning system rather than a post-incident autopsy.

## Client-Side Performance: Getting the Latency the Architecture Promises

The single-digit-millisecond latency in the Cosmos DB promise is achievable, but the client configuration decides whether you actually get it, and the defaults in a hastily written application leave performance on the table. The server can only respond as fast as the connection path and the client allow, so a few client-side choices matter as much as the partition key for tail latency.

The first choice is connection mode. The SDK can talk to the service in gateway mode, routing requests through a gateway endpoint, or in direct mode, connecting straight to the backend replicas over an optimized protocol. Direct mode delivers lower latency because it removes the gateway hop, and it is the right default for a latency-sensitive application running where it can open the necessary connections. Gateway mode suits environments behind restrictive firewalls that cannot open the direct ports. Selecting direct mode is a one-line client option, and on a hot read path it is the difference between meeting and missing a latency target.

The second choice is the client lifetime. The SDK client is designed to be created once and reused for the lifetime of the application, because it maintains connection pools, routing caches, and metadata that are expensive to rebuild. Creating a new client per request, a mistake that looks harmless, destroys performance and exhausts connections, producing latency spikes and timeouts that look like a service problem but are entirely self-inflicted. A singleton client, shared across the application and never disposed until shutdown, is the correct pattern:

```csharp
// Create once, at startup, and reuse everywhere
CosmosClient client = new CosmosClientBuilder(connectionString)
    .WithConnectionModeDirect()
    .WithApplicationPreferredRegions(new[] { "East US", "West US" })
    .Build();

// Register the single instance for the application's lifetime (dependency injection)
services.AddSingleton(client);
```

The third choice is the preferred-region list. For a globally distributed account, telling the client which regions to prefer routes reads to the nearest replica and gives it an ordered fallback if the nearest region is unreachable, which both lowers latency and improves resilience. Without it, the client may read from a region farther away than necessary, paying network latency the architecture was meant to eliminate.

For high-volume ingestion, the SDK offers a bulk-execution mode that batches many operations together for far higher write throughput than issuing them one at a time, which matters when you are loading data or replaying a change feed during a partition-key migration. Enabling bulk mode and parallelizing the work lets a migration or an initial load run in a fraction of the wall-clock time a serial loop would take. Finally, lean on the SDK's built-in retry behavior rather than reinventing it: the client already retries throttled requests with backoff and honors the retry-after hint the service returns on a 429, so the correct posture is to let those automatic retries absorb the normal background rate of throttling and to treat a sustained, high rate as the signal to fix the key or the capacity, not as something to paper over with more aggressive client retries.

## Three Misdiagnoses That Waste the Most Time

The recurring Cosmos DB incidents an engineer hits at work cluster around three wrong fixes, and naming them as a set makes them easy to catch in a design review or a postmortem before they cost a sprint. Each one is a reasonable-sounding instinct that the model in this guide reveals as a dead end.

The first is throwing throughput at a hot partition. The instinct is sound for genuine under-provisioning and wrong for a hot partition, and the two look identical from the application's point of view because both produce 429 responses. The discriminating evidence is the per-partition normalized consumption: spread across many partition-key ranges means under-provisioned, so raise the throughput; pinned to one range while the others idle means hot, so re-key. Reaching for the throughput slider without reading that metric is how teams spend money for weeks without moving the throttling.

The second is choosing a natural partition key by convenience rather than by cardinality and access distribution. A field is tempting because it already exists on the item and reads naturally, such as a status, a type, a country, or a tenant that turns out to dominate traffic. The scorecard exists precisely to interrupt this instinct: score cardinality and access distribution before committing, and when the convenient field fails either axis, build a synthetic or hierarchical key, because the small effort of constructing the right key now is trivial against the migration the wrong key forces later.

The third is defaulting every read to strong consistency because it sounds safest. Strong consistency raises both the request-unit cost and the latency of reads, and it forecloses multi-region writes entirely, all to provide a guarantee that most operations do not need. The corrective is to default to session consistency, which gives each user a coherent view of their own writes at low cost, and to step up to bounded staleness or strong only for the specific operations that genuinely cannot tolerate any staleness. Treating the consistency dial as a quality setting to maximize, rather than a deliberate trade to tune per workload, quietly inflates both the bill and the latency for no benefit the application can observe.

## Reading the Bill: Where Cosmos DB Cost Actually Comes From

Cost surprises with Cosmos DB are almost always traceable to one of a few drivers, and because the service bills on the same request-unit currency it limits on, the bill is more predictable than most teams expect once you know where to look. Reasoning about cost up front is the same exercise as reasoning about capacity, which is why the request-charge measurement discipline pays off twice.

The dominant driver is provisioned throughput. You pay for the RU/s you reserve, billed hourly, whether or not you consume them, so an over-provisioned container quietly burns money around the clock and an under-provisioned one throttles. The sizing arithmetic shown earlier, measuring each path's charge and multiplying by its rate, is the tool that lands the reservation on the workload rather than above or below it. The second driver is storage, billed per gigabyte for both data and the index, which is one more reason a narrowed indexing policy and a Time to Live on transient data pay off: less index and less retained data mean a smaller storage line.

The supply model adds its own multiplier. Autoscale charges a per-RU premium over standard provisioned in exchange for handling bursts automatically, so a steady workload pays needlessly for elasticity it does not use, while a spiky workload saves overall because it scales down during quiet periods despite the premium. Serverless flips the model to pure consumption billing, which is cheapest for genuinely intermittent traffic and more expensive than a well-sized reservation for a busy container. The deciding factor is the same average-utilization question that governs the capacity choice, so the cost-optimal model and the capacity-optimal model are the same model, chosen by how the load varies through the day.

Global distribution multiplies cost in a way that catches teams off guard. Each region you add replicates the full dataset, so storage cost scales with the region count, and under multi-region writes you also pay write throughput in every write region rather than one. A region list chosen for resilience without that arithmetic can multiply the bill several times over, so add regions for a reason, latency to a real user base or a resilience requirement, not as a default. The analytical store, when enabled, bills separately on its own storage and query model rather than against the operational request units, so it is a distinct line to account for when you adopt it.

The optimization levers fall straight out of the drivers. Size provisioned throughput from measured request charges rather than guesses; move bursty containers to autoscale and intermittent ones to serverless; narrow the indexing policy on write-heavy containers so writes cost fewer request units; apply Time to Live so transient data does not accumulate storage cost forever; pool many small containers on shared database throughput while giving hot containers dedicated capacity; and treat each added region as a deliberate cost decision. Applied together, these turn the bill from a monthly surprise into a number you can predict from the workload, which is exactly the posture the request-charge discipline was building toward all along, and which [the throughput and RU optimization guide](/2024/08/26/cosmos-db-throughput-optimization/) develops in full.

## When to Use Cosmos DB and When to Reach for an Alternative

Cosmos DB earns its place when you need horizontal scale to very high request rates, predictable single-digit-millisecond latency at that scale, global distribution with local reads and writes, and a flexible schema for semi-structured data. Workloads that fit naturally include high-traffic web and mobile backends, IoT and telemetry ingestion, personalization and catalog services, gaming leaderboards and player state, and any application whose write or read volume would overwhelm a single relational instance. The change feed also makes it a strong event source for event-driven architectures, since every write can drive downstream processing.

It is the wrong tool when your data is deeply relational with many-to-many joins across entities, when you need rich ad-hoc analytical queries with aggregations and joins across the whole dataset, or when your workload is small and steady enough that a single managed relational database would serve it at a fraction of the cost and operational complexity. A common and sound architecture pairs Cosmos DB for the high-throughput operational path with a relational database such as Azure SQL for the relational and reporting workload, rather than forcing one engine to do both jobs. The decision rule is the access pattern: if your queries are predominantly key-scoped point reads and writes at high volume, Cosmos DB fits; if they are predominantly relational and analytical, a different engine fits, and the honest answer is sometimes that you need both.

## How to Think About Azure Cosmos DB: The Partition-Key-First Rule

If you remember one thing from this guide, make it this. The partition key decides scalability, cost, and throttling before a single query runs, so it is the one decision in Azure Cosmos DB that cannot be cheaply changed later. Throughput you can raise or lower in seconds. Consistency you can tune per request. Regions you can add and remove. The partition key is set at container creation and effectively immutable, because changing it means building a new container and migrating every item. That asymmetry is why the key deserves more design attention than every other setting combined.

The reasoning chain that follows from the rule is the model to carry: a partition key with high cardinality and even access spreads your data and your traffic across many physical partitions, so the container's full provisioned throughput is actually available to your workload, queries that include the key stay on one partition and stay cheap, and the container scales out smoothly as data grows. A partition key with low cardinality or skewed access concentrates data and traffic onto one physical partition, so the per-partition throughput slice becomes your real ceiling regardless of the container total, queries fan out and cost multiplies, and no amount of provisioned throughput rescues you. Every downstream behavior of the service, the cost, the speed, the throttling, the scale limit, traces back to this one choice. Score it on cardinality, access distribution, and query alignment before you create the container, and reach for a synthetic or hierarchical key the moment a natural field fails any axis.

## The Verdict

Azure Cosmos DB delivers exactly what it promises, global distribution, elastic horizontal scale, predictable low latency, and a tunable consistency model, to teams that design for how it actually works and punishes teams that treat it as a relational database with a NoSQL label. The service is not difficult to operate once you internalize that it scales out rather than up, that request units are the single currency of both cost and capacity, that the consistency dial is a deliberate trade rather than a quality setting to max out, and above all that the partition key is the root decision from which every other behavior follows. The engineers who succeed with it are the ones who measure request charges in development, size with arithmetic instead of hope, default to session consistency and step up only where a workload demands it, and score the partition key before they create the container. Do that, and the 429s never come, the bill matches the workload, and the database scales as far as you need it to. Skip the partition-key analysis, and you will eventually pay for it in throttling, in cost, and in a painful migration to the key you should have chosen on day one.

The fastest way to make this concrete is to build it. You can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to create a container, choose a partition key, push synthetic load through it, and watch the per-partition RU consumption and hot-partition behavior in real time, which turns the model in this guide into something you have felt rather than only read.

## Frequently Asked Questions

### Q: What is Azure Cosmos DB used for?

Azure Cosmos DB is a managed, globally distributed NoSQL database for workloads that need horizontal scale to high request rates, predictable low-millisecond latency, and the option to serve users from regions worldwide. It suits high-traffic web and mobile backends, IoT and telemetry ingestion, product catalogs, personalization, gaming state, and event sourcing through its change feed. It stores semi-structured JSON items rather than rigid relational tables, which fits applications whose schema evolves or varies across records. It is less suited to deeply relational data with heavy joins or to ad-hoc analytical reporting across an entire dataset, where a relational engine like Azure SQL serves better. Many production systems use both: Cosmos DB for the high-volume operational path and a relational database for the reporting and relational workload.

### Q: How is throughput measured in Cosmos DB?

Throughput is measured in request units per second, written RU/s. A request unit is a normalized cost that combines the CPU, memory, and IO a database operation consumes into one number, so you reason about capacity in a single currency instead of juggling separate resource limits. A point read of a small one-kilobyte item by its id and partition key is the reference cost at roughly one request unit; writes cost more because of indexing, and queries cost in proportion to the work the engine does, not the rows returned. You either provision a fixed RU/s figure, set an autoscale ceiling, or run serverless and pay per request unit consumed. Every response returns the exact charge for that operation in a header, which lets you measure real costs during development and size capacity with arithmetic.

### Q: How do I choose a good Cosmos DB partition key?

Score every candidate on three axes. Cardinality asks how many distinct values the key has; you want many values that grow with the data, not a handful of fixed ones. Access distribution asks whether traffic spreads evenly across those values or concentrates on a few hot ones; even spread is the goal. Query alignment asks whether your common, high-volume queries filter on the key, so they stay on a single partition and stay cheap. A field like a customer or device identifier often passes all three for business applications. A field like status, type, or region usually fails cardinality and access distribution. When no natural field scores well, build a synthetic key by concatenating fields or use a hierarchical key, because constructing the right key is trivial next to migrating a throttling container later.

### Q: Why does adding more RU/s not fix my 429 errors?

Provisioned throughput is divided as evenly as possible across the physical partitions that store your data, and a request can only draw from the throughput slice of the partition it lands on. When throttling comes from a hot partition, where one or a few partition-key values take most of the traffic, that value's physical partition still gets only its proportional slice no matter how high you raise the container total. You can have most of your provisioned capacity sitting unused on other partitions while the hot one keeps returning 429. Raising throughput only helps when the throttling is spread across many key values, meaning the container is genuinely under-provisioned. For a hot partition, the only real fix is a better partition key that distributes the load, which usually means migrating to a new container.

### Q: Which Cosmos DB consistency level should I use?

Default to session consistency for almost all applications. It guarantees that each client reads its own writes, never sees data move backward, and sees writes in order within its session, which matches what interactive applications need, and it delivers this at low latency and low request-unit cost. Move to bounded staleness when you need near-current reads with a predictable, configured lag, or to strong consistency when a workload genuinely cannot tolerate any staleness and you accept the added latency and the incompatibility with multi-region writes. Drop to consistent prefix or eventual for workloads where freshness barely matters and throughput and availability dominate, such as counters or telemetry feeds. You set a default at the account level and can relax it per request, so the practical approach is session by default with targeted exceptions.

### Q: What is the difference between a logical and a physical partition?

A logical partition is the set of all items that share one partition-key value; every item for one customer, if your key is the customer id, forms one logical partition. A logical partition has a fixed storage ceiling and cannot be split, so any single key value whose data would exceed that ceiling is unusable. A physical partition is the actual backend resource, a replica set of machines that stores a range of the hashed key space and serves requests against it, with its own storage and throughput limits. The platform maps many logical partitions onto each physical partition and adds physical partitions as your data or provisioned throughput grows, redistributing the key space automatically. You never manage physical partitions directly; you influence them only through your partition-key choice and your throughput setting.

### Q: Should I use provisioned, autoscale, or serverless throughput?

Match the model to your traffic shape. Standard provisioned throughput reserves a fixed RU/s and is cheapest for steady, predictable load you can size accurately, but you pay for the reservation whether you use it or not. Autoscale sets a maximum and scales actual capacity between ten percent and the full ceiling automatically, charging a per-RU premium in exchange for handling bursts without throttling or manual sizing; it wins when load swings widely and is often idle. Serverless removes provisioning and bills purely per request unit, which fits development, intermittent, or low-average workloads, but it has lower ceilings and runs in a single region, so it cannot serve a multi-region production system. The deciding factor is average utilization over time: busy most of the time favors provisioned or autoscale, quiet most of the time favors serverless.

### Q: What does the request charge header tell me?

Every operation returns its exact request-unit cost in a response header, surfaced as the request charge in the SDKs. This is the most useful diagnostic in the service and the one most teams ignore. By logging the charge for your hot read and write paths during development, you learn precisely what each operation costs before you ever deploy, and you can multiply that cost by your expected requests per second to size a container with arithmetic instead of guesswork. It also exposes inefficiency immediately: a query that costs fifty request units when a well-indexed equivalent would cost two is a signal to fix the query or the indexing policy before you provision capacity around the waste. Treat the request charge as the primary feedback loop while building, not an afterthought.

### Q: Can I change the partition key after creating a container?

Not in place. The partition key is set when you create a container and is effectively immutable, because the platform hashes the key to decide where every item lives, so changing it would mean relocating all data. To adopt a different key you create a new container with the better key and migrate your data into it, commonly by reading from the change feed of the old container and writing into the new one, which can be done with minimal downtime. This immutability is exactly why the partition key deserves more design attention than any other setting: throughput, consistency, and regions are all adjustable later, but the key is a one-time decision whose consequences compound. Score it carefully before creation rather than discovering its limits under production load.

### Q: How does multi-region write differ from multi-region read?

By default a Cosmos DB account has one write region and replicates data to other regions as read replicas, so clients everywhere read locally but writes travel to the single write region. Enabling multi-region writes lets every region accept writes locally, which removes cross-region write latency and improves write availability, since losing one region does not stop writes elsewhere. The cost is write conflicts: two regions can update the same item concurrently, and the platform must resolve which wins, using last-writer-wins by default or a custom procedure you supply. Multi-region writes suit workloads where conflicting writes to the same item are rare or last-writer-wins is acceptable, and they become a liability where concurrent conflicting writes are common and resolution genuinely matters. Choose it deliberately with a conflict story, not as a reflexive toggle.

### Q: Why is my Cosmos DB query so expensive in RUs?

Query cost scales with the work the engine does, not the number of rows returned, so an expensive query is usually doing far more work than its result suggests. The two common causes are a missing partition key and inefficient index use. A query that omits the partition key fans out across every physical partition, gathering and merging results, which multiplies cost and latency. A query that filters or sorts on properties the index does not cover, or that the engine cannot satisfy from the index, forces it to examine many items. Fixes include scoping the query to a single partition by including the partition key, tightening predicates so the engine touches less data, and tuning the indexing policy to cover the properties you actually filter and sort on. Always read the request charge on the query to confirm the improvement.

### Q: What happens during a region failover?

You configure a priority order for the regions in your account. If the write region becomes unavailable, the platform can promote the next region in priority either automatically, when automatic failover is enabled, or on manual trigger. Read regions continue serving reads locally throughout. How much recently written data is at risk during failover depends on your consistency level: stronger consistency replicates writes more synchronously and so loses less on failover but adds latency in normal operation, while weaker consistency is faster day to day but may lose more recent writes if a region is lost before replication completes. This is the same consistency-versus-latency trade-off seen from the disaster-recovery angle. Design your region priority and consistency together against your recovery objectives rather than treating them as separate settings.

### Q: How does indexing affect cost in Cosmos DB?

By default Cosmos DB indexes every property of every item, which makes ad-hoc queries fast without any configuration but raises write cost, because every indexed property must be updated on each write, and increases storage. Indexing trades write cost and storage for read flexibility, and the default sits at maximum read flexibility. For a write-heavy workload with a known, narrow set of queries, customizing the indexing policy to include only the properties you actually filter or sort on can cut write request charges noticeably and reduce storage. The reasoning is to index for the queries you run, not for every query you might theoretically run. Measure write request charges before and after a policy change to confirm the saving, and remember that an under-indexed property used in a filter will make that query scan more and cost more.

### Q: Is Cosmos DB a relational database?

No. Cosmos DB is a NoSQL database that stores semi-structured JSON items and scales horizontally by partitioning data across many machines, in contrast to a relational database that stores rows in fixed-schema tables and typically scales up on a single instance. It does not perform relational joins across entities the way SQL engines do, and it is not built for ad-hoc analytical queries that aggregate and join across an entire dataset. Its strengths are high-throughput key-scoped reads and writes, flexible schema, predictable low latency at scale, and global distribution. When your data is deeply relational or your queries are heavily analytical, a relational engine such as Azure SQL is the better fit, and a common architecture uses Cosmos DB for the high-volume operational path alongside a relational database for the relational and reporting workload.

### Q: What is the change feed and why does it matter?

The change feed is a persistent, ordered record of the creates and updates to items in a container, which you can read to react to changes as they happen. It turns Cosmos DB into an event source: downstream processors can consume the feed to update materialized views, push notifications, replicate data, feed analytics, or trigger workflows, without the application having to publish events separately. It is also the standard tool for migrating to a new partition key, because you replay the feed of the old container into a new one with the better key. Because the feed is ordered per partition and durable, consumers can checkpoint their position and resume after a restart without missing or duplicating processing. Building event-driven and data-pipeline patterns on the change feed is one of the service's most useful capabilities beyond simple storage.

### Q: How do I avoid hot partitions in Cosmos DB?

Avoid them at design time by scoring the partition key on access distribution before you create the container. A hot partition forms when one or a few partition-key values take a disproportionate share of reads or writes, pinning that load to a single physical partition's throughput slice while other partitions sit idle. Choose a key whose values spread traffic evenly, which usually means high cardinality combined with naturally balanced access, such as a customer or device identifier in a multi-tenant application. When a single tenant or value is inherently high-volume, use a synthetic key that subdivides it, for example by concatenating a time bucket, or a hierarchical key that routes at the top level and subdivides underneath. If a hot partition already exists in production, the durable fix is migrating to a new container with a better key using the change feed.

### Q: What is the storage limit per logical partition?

A single logical partition, meaning all items sharing one partition-key value, has a fixed storage ceiling that is commonly documented at twenty gigabytes, though you should confirm the current figure against the official limits because these values change over time. This ceiling is a hard design constraint: if the data for any one key value would grow beyond it, that key is unusable as written, regardless of how much throughput you provision. The constraint pushes you toward keys with enough cardinality that no single value accumulates excessive data, and toward synthetic or hierarchical keys when a natural high-volume value would otherwise overflow a single logical partition. Container-level storage, by contrast, scales effectively without a practical ceiling because the platform adds physical partitions as data grows, so the limit that bites in practice is the per-logical-partition one.

### Q: Does stronger consistency cost more in RUs?

Yes, in two senses. Read operations at strong or bounded-staleness consistency consume more request units than the same reads at session, consistent prefix, or eventual consistency, because the stronger levels require more coordination to guarantee the result is current within the promised bound. Beyond the per-operation request-unit cost, stronger consistency also imposes a latency cost, since reads may need to coordinate across replicas or regions, and strong consistency is incompatible with multi-region writes entirely. The practical implication is that defaulting every read to strong consistency raises both your bill and your latency for guarantees most operations do not need. Default to session and reserve stronger levels for the specific reads that genuinely require them, relaxing consistency per request where a read can tolerate slight staleness to recover both cost and speed.

### Q: How do I size a Cosmos DB container before deploying?

Measure, then multiply. During development, log the request charge header for each operation on your high-volume read and write paths to learn its exact request-unit cost. Estimate the peak requests per second for each path, multiply cost by rate, and sum across paths to get the RU/s the container needs at peak. If the load is steady around that figure, provision it directly; if it swings widely, set an autoscale maximum above the peak and let the platform scale down during quiet periods; if it is intermittent, consider serverless. Crucially, fix any operation whose request charge is surprisingly high, usually a cross-partition query or an under-indexed filter, before you size around it, because sizing around waste bakes the waste into your bill. This arithmetic approach replaces guesswork and prevents both throttling from under-provisioning and cost from over-provisioning.

### Q: Can I use Cosmos DB with my existing MongoDB application?

In most cases yes, through the MongoDB API, which implements the MongoDB wire protocol so existing applications and tools connect with a connection-string change and minimal code edits, while the data lives on Cosmos DB's globally distributed, RU-metered engine underneath. This is the standard migration path for teams who want a managed, globally distributed backend without rewriting their data layer. The caveat is that the compatibility API implements a version of the protocol rather than every feature of the original product, so before committing you should test the specific operators, aggregation stages, and features your application relies on against the API to confirm they are supported. The same pattern applies to the Cassandra, Gremlin, and Table APIs for those ecosystems. The partition-key, request-unit, and consistency reasoning in this guide applies to every API surface, because they all sit on the same engine.
