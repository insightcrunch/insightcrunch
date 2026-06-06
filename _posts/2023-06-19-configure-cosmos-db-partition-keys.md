---
layout: post
title: "Configure Cosmos DB Partition Keys the Right Way"
page_title: "Configure Cosmos DB Partition Keys the Right Way: Cardinality, Synthetic and Hierarchical Keys, Query Alignment, and Migration Explained"
date: 2023-06-19
categories: ["Technology"]
tags: ["Azure", "Cosmos DB", "Performance", "Architecture", "Cloud Computing"]
excerpt: "Configure Cosmos DB partition keys the right way with high cardinality, even access, and query alignment, plus synthetic and hierarchical key patterns."
image: "/assets/images/blog/blog-02.webp"
reading_time: 61
author: "Insight Crunch Team"
last_updated: 2023-06-19
---

A correctly chosen partition key is the single configuration decision that decides whether an Azure Cosmos DB container scales smoothly to terabytes and millions of requests per second, or quietly collapses into throttling under load that the provisioned throughput should have absorbed easily. When you configure Cosmos DB partition keys well, the database spreads storage and request units evenly across its backing infrastructure, common queries touch one place instead of fanning out, and the cost stays proportional to the work. When you choose badly, a single value soaks up a disproportionate share of traffic, requests pile up behind one busy worker, and you pay for capacity the platform cannot actually use because it sits idle on the partitions that nobody is touching.

![Configuring Cosmos DB partition keys for even distribution and query alignment - Insight Crunch](/assets/images/blog/blog-02.webp)

The difficulty is that this decision is effectively permanent. The key path is fixed when the container is created and cannot be altered in place afterward, so a poor choice is not a setting you toggle later but a migration you schedule, build, and validate. That irreversibility is exactly why the choice deserves a deliberate, scored process rather than a glance at the schema and a guess. This guide gives you that process: a mental model of how the service distributes data, a scorecard for grading candidate keys before you commit, the exact commands and templates to create the container correctly, the synthetic and hierarchical patterns that rescue an otherwise weak natural key, and the verification and migration mechanics for when a key already in production turns out to be wrong.

## What the partition key actually controls in Cosmos DB

Before grading any candidate, you need a precise model of what the value you nominate as the placement field is really steering. Cosmos DB does not store a container as one monolithic file. It splits the data into ranges and spreads those ranges across a fleet of backing servers, and the placement path you declare is the rule the service uses to decide where every item lives and which server answers every request. Getting the configuration right starts with understanding the two layers of distribution that sit underneath that one declaration, because nearly every scaling surprise an engineer reports traces back to confusing one layer for the other.

The first layer is the logical grouping. Every item that shares the same value in the declared key path belongs to the same logical group. If you declare the path `/tenantId`, then all documents whose `tenantId` reads `acme` form one logical group, all documents whose `tenantId` reads `globex` form another, and so on. These groups are the unit of transactional scope: a stored procedure or a transactional batch can only span items inside a single logical group, because the service guarantees that one group's data is never split across machines. A single logical group also carries a hard storage ceiling. Historically that ceiling sits at twenty gigabytes for a non-subpartitioned container, a figure worth verifying against the current service limits at the time you read this, and once a group reaches that ceiling it cannot grow further no matter how much capacity the rest of the container has. A design that funnels an unbounded stream of writes into one group value is therefore not merely slow, it is a wall the data will hit.

The second layer is the physical placement. The service maps the logical groups onto a set of backing replicas, usually described as physical ranges, each of which owns a contiguous slice of the hashed key space and runs on dedicated compute and storage. A physical range holds a budget of storage, on the order of fifty gigabytes, and a budget of request throughput, on the order of ten thousand request units per second, and again those exact figures belong on your list of values to confirm against the live documentation rather than to memorize as constants. The platform splits a physical range automatically when it approaches either ceiling, redistributing the logical groups it held across two new ranges. You never provision these ranges directly. You influence them entirely through the field you pick and the volume and shape of the data and traffic that key produces.

### How does Cosmos DB spread throughput across the data?

Provisioned request units are divided as evenly as the platform can manage across the physical ranges that currently back the container. If a container has ten ranges and you provision forty thousand request units per second, each range receives roughly four thousand units of budget. A request that lands on a range exceeding its slice of the budget is throttled even when other ranges sit nearly idle.

That even division is the fact that turns a key mistake into a throttling incident, so it rewards a closer look. Suppose you provision one hundred thousand request units across a container that the platform has split into twenty ranges. Each range gets about five thousand units. If your traffic is spread so that every range fields a similar share, the container comfortably serves the full hundred thousand. But if eighty percent of your writes carry the same placement value, that value lives in one logical group, that group lives on one physical range, and that one range still only owns five thousand units of the hundred thousand you are paying for. The moment your concentrated traffic exceeds five thousand units against that range, the service returns the throttling response, even though nineteen other ranges are barely awake and ninety-five thousand units of provisioned capacity go unused. This is the precise mechanism behind the complaint that surfaces constantly in support threads: the dashboard shows plenty of spare throughput, yet the application is being throttled. The throughput is spare on the wrong ranges. For the deeper treatment of that failure once it is already happening, the companion analysis of why one range throttles while others stay idle in the guide to [Cosmos DB RU throttling and hot partitions](/2022/09/12/fix-cosmos-db-ru-throttling/) walks the diagnosis end to end; this article is about preventing it at configuration time.

### What is the difference between a logical and a physical partition?

A logical group is the set of all items sharing one placement value, and it is the boundary for transactions and the twenty-gigabyte storage ceiling. A physical range is a backing replica that holds many logical groups and owns a slice of storage and throughput. You control logical groups directly through the key; the platform manages physical ranges automatically.

The relationship between the two layers is many-to-one and dynamic. Early in a container's life, when the data is small, every logical group might sit on a single physical range. As the data grows past the storage budget of that range, or as provisioned throughput rises past what one range can serve, the platform splits the range and reassigns the logical groups across the new ranges using the hash of the placement value. A well-distributed key produces many logical groups of similar size and similar traffic, which the platform can pack and split cleanly, keeping every physical range balanced. A poorly distributed key produces a handful of enormous groups or one group that takes most of the traffic, and no amount of automatic splitting can rescue that, because the platform cannot split a single logical group across two ranges. The group is atomic at the physical layer. That atomicity is the hard constraint at the center of every partition design, and it is why the only durable fix for a concentrated key is to choose a different key, not to provision more capacity or wait for the service to rebalance.

For the full architectural treatment of request units, the consistency model, and how the distribution machinery fits the rest of the service, the [Azure Cosmos DB engineering guide](/2022/02/14/azure-cosmos-db-engineering-guide/) covers the surrounding system; here the focus stays narrowly on the one configuration knob and how to set it correctly.

## The cardinality-and-alignment rule and the scorecard

Every sound partition design reduces to one rule that I will state plainly and then defend for the rest of this guide. A good key is high in cardinality, even in access, and aligned to the query you run most. Miss any one of those three and you have planted the seed of a hot range that will sprout later under production load. The three properties are not a ranked list where you satisfy the top one and relax on the others. They are three independent gates, and a candidate that fails any single gate is disqualified regardless of how strongly it passes the other two.

Cardinality is the count of distinct values the key can take. A key on a boolean flag has a cardinality of two; a key on a calendar date over a year has a cardinality of roughly three hundred sixty-five; a key on a customer identifier in a large consumer application has a cardinality in the millions. High cardinality is what lets the platform create many logical groups and spread them across many physical ranges. Low cardinality forces the data into a small number of groups, and since a group cannot be split across ranges, low cardinality directly caps how far the container can scale and how evenly it can balance.

Even access means that traffic, both reads and writes, is spread roughly uniformly across the distinct values rather than concentrated on a few. A key can have enormous cardinality and still fail this gate. An identifier that is technically unique per record but where ninety percent of requests target last week's records concentrates access on the most recent values, so the property to watch is not how many values exist but how the live traffic distributes over them. Even access is the gate that low-cardinality keys fail most obviously, but it is also the gate that high-cardinality keys fail subtly, through skew, which is why it deserves its own column rather than being folded into cardinality.

Query alignment means the value you make the placement field is the value your most frequent and most latency-sensitive queries filter on. When a query includes an equality filter on the placement field, the service can route that query to the single range that owns the value and answer it cheaply. When a query omits the placement field, the service has no way to know which range holds the matching items, so it fans the query out to every range, gathers the partial results, and merges them, which costs more request units, adds latency, and scales its cost with the number of ranges. Alignment is the gate engineers most often overlook, because a key can be perfectly distributed and still force every important read into a fan-out if it is not the value those reads filter on.

### The InsightCrunch partition-key scorecard

The scorecard below is the findable artifact of this guide: a setup form you fill in for each candidate key before you commit any of them to a container. Rate each candidate on the three gates, note the dominant query it serves, and apply the decision rule in the final column. A candidate must earn a passing mark on all three gates to be eligible; if no natural candidate passes all three, the rule tells you whether a synthetic or hierarchical construction can lift it over the line.

| Candidate key | Cardinality | Access evenness | Query alignment | Verdict and rule |
| --- | --- | --- | --- | --- |
| Boolean or status flag (`/status`) | Very low (a few values) | Poor, traffic piles on the active value | Often poor, status rarely the main filter | Reject. Low cardinality plus skew guarantees a hot range. |
| Calendar date (`/date`, `/day`) | Low to moderate | Poor for write-heavy, today takes all writes | Good for time-range reads only | Reject for write-heavy. Time series concentrates writes on the current value. |
| Tenant identifier (`/tenantId`) | Moderate, equals tenant count | Uneven if one tenant dominates | Strong, most queries scope to a tenant | Conditional. Good unless one tenant is far larger; then go hierarchical. |
| Natural entity id (`/userId`, `/deviceId`) | High in a large population | Even if traffic is broad | Strong for per-entity access | Accept when the dominant query filters by that entity. |
| Document id (`/id`) | Maximum, one value per item | Even by construction | Strong only for point reads by id | Accept for point-read heavy, key-value style workloads. |
| Synthetic concatenation (`/tenantId_type`) | Raised above the natural field | Improved over the natural field | Good if queries filter on both parts | Use when one natural field is too coarse to distribute. |
| Synthetic with suffix (`/deviceId_bucket`) | Raised by a fan-out factor | Forced even by a random or hashed suffix | Weakened, reads must address all buckets | Use to spread a write hot spot, accept the read fan-out cost. |
| Hierarchical (`/tenantId` then `/userId`) | Effectively the product of levels | Even within and across tenants | Strong for prefix and full-path queries | Use for multi-level access and to break the per-tenant storage ceiling. |

The scorecard is deliberately blunt. The first two rows are rejected outright because they are the two mistakes engineers make most: reaching for a convenient status or date field because it is easy to reason about, and discovering under load that easy-to-reason-about and well-distributed are not the same thing. The middle rows are the natural keys that usually win. The last three rows are the engineered keys you build when no natural field clears all three gates at once, and the rest of this guide is largely about constructing them correctly and paying their trade-offs knowingly.

## Prerequisites and the correct order of operations

Configuring the key correctly is less about the single command that sets it and more about the order in which you make the surrounding decisions, because several of them constrain the key and a few of them cannot be revisited cheaply once data lands. The order below is the sequence I follow on every new container, and it exists so that the irreversible choices are made on purpose and with the reversible ones already settled around them.

Begin with the access patterns, not the schema. Write down the handful of queries the application will run most often and most urgently, the ones on the hot path of a user request rather than the nightly report. For each, note which field the query filters on and how selective that filter is. This list is the raw material for the alignment gate, and doing it first prevents the most common reversal, where a team designs the schema around how the data feels natural to store and only later discovers that the field they made the placement field is not the field the application reads by.

Next, estimate the distribution. For each candidate field, estimate the number of distinct values you expect in production, not in the test data, and estimate how traffic will spread across those values. A field that looks evenly distributed in a thousand-row sample can be brutally skewed at scale when one customer onboards ten million records. This estimate feeds the cardinality and evenness gates, and it is where you decide whether a natural field is strong enough or whether you will need to engineer a synthetic or hierarchical construction.

Only then decide the throughput model and the container topology, because these interact with the key. Provisioned throughput at the container level shares one budget across all logical groups, while throughput at the database level shares a budget across containers, and serverless bills per request with its own range and storage ceilings. The choice affects how forgiving the platform is of mild skew: a generously provisioned container tolerates more imbalance before throttling than a thinly provisioned one, though no amount of provisioning rescues a genuinely concentrated key. For the full treatment of choosing and tuning that budget, the guide to [Cosmos DB throughput and RU optimization](/2024/08/26/cosmos-db-throughput-optimization/) is the natural follow-up once the placement field is settled.

Finally, decide whether you need hierarchical subpartitioning before you create the container, because enabling it is part of the creation call and cannot be added to an existing container later. If your design has a natural prefix field, such as a tenant, that you expect to grow past the per-group storage ceiling, you commit to a hierarchical key now or you accept that you will be migrating later. This is the one prerequisite that most often gets skipped and most often forces a rebuild, so it belongs at the end of the planning sequence as the last gate before you run the command.

### What has to be true of the field before it can be the key?

The field must exist on every item written to the container, must hold a value rather than being absent or null on any item, and should be effectively immutable per item, since the value places the item physically and changing it means deleting and re-inserting. The field's value also has a length ceiling, on the order of a couple of kilobytes, worth confirming against current limits.

Those constraints are easy to overlook because the SDK will not stop you from writing an item whose key path is missing or null at creation time; it simply treats absent and null as their own distinct group value, which then becomes a magnet for every item that forgot to set the field. The result is a single group, often the largest in the container, holding all the malformed records, and it behaves exactly like a low-cardinality hot range. Validating that the key field is always present and always populated is therefore not a nicety but part of getting the configuration right, and it belongs in the write path of the application rather than in a cleanup job after the fact.

## Creating the container with the key set correctly

With the planning done, the act of declaring the key is a single argument on the container creation call, and the discipline is simply to never let a container be created without that argument set deliberately. The portal, the command line, and every infrastructure template expose the same setting, and the value you supply is a JSON path into the document, written with a leading slash, naming the property that holds the key.

The Azure command line creates a container and fixes its key in one call. The `--partition-key-path` argument takes the document path, and once the container exists this value is sealed.

```bash
# Create a container with a single-property partition key
az cosmosdb sql container create \
  --account-name mycosmosaccount \
  --resource-group my-rg \
  --database-name appdb \
  --name orders \
  --partition-key-path "/customerId" \
  --throughput 4000
```

The path points at a top-level property named `customerId`. A nested property is addressed by extending the path, so a key on `customerId` inside an `owner` object would be `/owner/customerId`. The service stores the value found at that path for every item and uses it to place the item. If the property is missing on an item, that item is grouped under an undefined value, which is the failure mode described earlier, so the application must guarantee the field is always written.

Declaring a hierarchical key is the same call with the path argument repeated, once per level, in priority order from the broadest grouping to the narrowest. Up to three levels are supported, and the order matters because the first level is the prefix that targeted queries will most often supply.

```bash
# Create a container with a hierarchical (multi-level) partition key
az cosmosdb sql container create \
  --account-name mycosmosaccount \
  --resource-group my-rg \
  --database-name appdb \
  --name events \
  --partition-key-path "/tenantId" "/userId" "/sessionId" \
  --throughput 4000
```

This declares a three-level key where items are grouped first by tenant, then by user within a tenant, then by session within a user. The behavior that makes this worth the extra thought is covered in its own section below; for now the point is that the levels and their order are fixed at creation alongside everything else.

### How do I set the partition key from the SDK?

In application code, you supply the same path when you create the container definition, so the database can be provisioned from the service that owns it rather than from a separate script. The .NET client below creates a container with a single-property key, and the value of `PartitionKeyPath` is the identical JSON path the command line used.

```csharp
// .NET SDK: create a container with a single partition key path
ContainerProperties props = new ContainerProperties(
    id: "orders",
    partitionKeyPath: "/customerId");

Container container = await database.CreateContainerIfNotExistsAsync(
    props,
    throughput: 4000);
```

For a hierarchical key the SDK takes a list of paths instead of one, again in broad-to-narrow order, and reads and writes then build the full key from its parts.

```csharp
// .NET SDK: create a container with a hierarchical partition key
ContainerProperties props = new ContainerProperties(
    id: "events",
    partitionKeyPaths: new List<string> { "/tenantId", "/userId", "/sessionId" });

Container container = await database.CreateContainerIfNotExistsAsync(
    props,
    throughput: 4000);
```

When you later read or write an item against a hierarchical container, you construct the placement value from its levels rather than passing a single string. A point read that supplies all three levels routes to exactly the right physical range and costs the minimum, while a read that supplies only the leading level or two scopes the work to the subtree under that prefix.

```csharp
// Build a full hierarchical key for a point read
PartitionKey pk = new PartitionKeyBuilder()
    .Add("tenant-acme")
    .Add("user-1024")
    .Add("session-55f0")
    .Build();

ItemResponse<EventDoc> response =
    await container.ReadItemAsync<EventDoc>("event-9001", pk);
```

### Can I declare the key in an infrastructure template?

Yes, and for anything beyond a throwaway experiment you should, so the placement field is reviewed in a pull request rather than typed once into a portal field and forgotten. A Bicep module declares the path in the container resource, which makes the irreversible choice an artifact in version control that a reviewer can challenge before it ships.

```bicep
resource ordersContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: appDatabase
  name: 'orders'
  properties: {
    resource: {
      id: 'orders'
      partitionKey: {
        paths: [
          '/customerId'
        ]
        kind: 'Hash'
        version: 2
      }
    }
    options: {
      throughput: 4000
    }
  }
}
```

For a hierarchical key the same `paths` array carries multiple entries and the `kind` becomes `MultiHash`, with the order of the array setting the level order. Declaring it this way means the most consequential and least reversible decision in the whole schema is captured in the same template as the rest of the topology, version-controlled, and subject to review, which is the single best guard against a key being chosen carelessly under deadline pressure. You can practice each of these creation paths against a live account and watch the distribution behave in the hands-on Cosmos labs and command library; the [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) environment lets you create containers with different keys, load skewed and even data sets, and read the resulting range spread without touching a production account.

## The three gates examined one at a time

The scorecard treats cardinality, evenness, and alignment as independent gates, and the reason they are independent rather than aspects of a single property becomes clear when you look at how a candidate can ace two and fail the third. Understanding each gate on its own is what lets you diagnose a weak candidate precisely instead of vaguely sensing that a key feels wrong.

### Why does cardinality matter so much?

Cardinality sets the ceiling on how many independent groups the data can form, and because a single group can never be split across two physical ranges, cardinality sets the hard upper bound on how far the container can spread its load and its storage. A two-value key can occupy at most two groups; everything else the platform might want to do to balance is foreclosed.

The trap with cardinality is that it interacts with growth in a way that punishes the convenient choice exactly when the application succeeds. A status field with five values seems harmless on a small container, where five groups comfortably fit on a couple of ranges and nothing throttles. The same five-value key on a container that has grown to need thirty ranges is a disaster, because the data can still only occupy five groups, those five groups crowd onto a handful of ranges, and the remaining ranges sit empty holding throughput you cannot use. Low cardinality does not announce itself in development; it waits for scale. This is why the estimate of distinct values must be a production estimate, and why a field whose value space is bounded by a small enumeration should be rejected on this gate alone before you even consider the other two.

The opposite extreme, a key with maximum cardinality such as the document identifier, raises its own consideration. A key where every item has a unique value distributes storage and write load beautifully, and it makes point reads by that identifier the cheapest possible operation, since the read addresses exactly one item in exactly one group. The cost is that no query can ever target more than a single item by the placement field, because no two items share a value, so any query that needs a set of related items must either fan out or rely on a secondary access path. The maximum-cardinality key is therefore ideal for a key-value or point-read workload and poor for a workload that reads collections of related records together, which is precisely the tension the alignment gate captures.

### Why is even access different from cardinality?

Even access concerns how live traffic distributes over the values rather than how many values exist. A key can clear the cardinality gate with millions of distinct values and still fail the access gate if requests cluster on a small subset of those values, because the busy values land on a few ranges and throttle while the rest stay idle. Cardinality is about the data; evenness is about the traffic.

The clearest example is a time-ordered key in a write-heavy ingestion workload. A timestamp truncated to the day has decent cardinality over a year, so it passes the first gate on a naive reading, but every write in a given day carries the same value, so one hundred percent of the write traffic concentrates on a single group at any moment. The group rolls over to a new value at midnight, but at every instant the writes are pounding one range. This is the canonical write hot spot, and it is invisible to a cardinality check because the cardinality is genuinely fine; only an access analysis reveals that the writes are serialized onto one value at a time. The same pattern appears with a monotonically increasing sequence number, an auto-incrementing identifier, or any candidate whose value is correlated with arrival time, since all recent writes share recent values.

Skew on the read side is subtler but just as real. A key on a customer identifier in a marketplace might have a million values, but if one enterprise customer drives a thousand times the traffic of a typical customer, the range that holds that customer becomes a hot spot for reads even though the key looks perfectly high in cardinality. The access gate is the one that forces you to ask not how many tenants or users or devices you have, but whether any single one of them is large or busy enough to dominate, because a single dominant value behaves exactly like a low-cardinality key for the range unlucky enough to hold it.

### Why is query alignment the gate engineers forget?

Query alignment is forgotten because it does not show up in any storage or throughput metric until the bill arrives. A key can distribute data and traffic flawlessly and still force every important query into a cross-range fan-out if the placement field is not the field those queries filter on. Alignment is about routing, and a misaligned key routes every read to every range.

When a query carries an equality filter on the placement field, the service hashes the value, identifies the one range that owns it, and executes the query there, reading only the data that could possibly match and charging request units proportional to that small slice. When a query omits the placement field, the service cannot know which range holds the matches, so it issues the query to every range, each range scans its data and returns its partial result, and the client SDK or gateway merges them. The request-unit charge for that fan-out scales with the number of ranges, so the same query that costs a handful of units on a small container costs many multiples of that on a large one, and the latency rises with the slowest range in the fan-out. A misaligned key thus produces a query whose cost grows as the container grows, which is the worst possible scaling characteristic and the one that turns a feature that worked in testing into a budget problem in production.

The resolution is to make the key the field that the dominant query filters on, even when some other field feels like the more natural identity of the record. If users are almost always retrieved within the context of their tenant, the tenant is a strong leading key even though the user identifier feels like the document's true identity, because tenant-scoped reads then route to one range. When two different query shapes each want a different field as the key, you have a genuine tension that no single natural key resolves, and that is the signal to reach for a synthetic or hierarchical construction or to accept a secondary access path such as a change-feed-fed materialized view keyed differently. Recognizing that tension at design time, rather than discovering it through a fan-out bill, is most of what separates a deliberate configuration from a guessed one.

## Synthetic partition keys: building a key when no natural field works

When no single field clears all three gates, you construct one. A synthetic key is a property you add to the document whose value you compute from other fields, and its whole purpose is to manufacture the cardinality, evenness, or alignment that the raw data does not offer. There are two distinct synthetic patterns, they solve opposite problems, and confusing them produces a field that fixes nothing while adding write-path complexity, so the first job is to know which problem you actually have.

The concatenation pattern raises cardinality and sharpens alignment by combining two or more fields into one value. Suppose your dominant query filters on both a tenant and a record type, and neither field alone has enough cardinality to distribute well, the tenant because a few tenants dominate and the type because there are only a handful of types. A synthetic key formed by joining them, written into a property such as `partitionKey` with a value like `acme_invoice`, multiplies the cardinality toward the product of the two fields and aligns perfectly with a query that filters on both. The cost is modest and entirely on the write path: the application must compute and store the combined value on every insert, and it must remember to keep that derived field consistent with its source fields, which is a reason to compute it in one place in the data layer rather than scattering the logic across call sites.

```csharp
// Concatenation synthetic key built in the write path
item.PartitionKey = $"{item.TenantId}_{item.RecordType}";
await container.CreateItemAsync(item, new PartitionKey(item.PartitionKey));
```

The suffix or spreading pattern solves the opposite problem, a write hot spot caused by too little cardinality or by skew, by deliberately fanning one logical value across several. You append a bounded random or hashed suffix to the natural value, turning one busy value into a fixed number of buckets. A device that emits a flood of telemetry under a single `deviceId` becomes, with a suffix in the range zero to nine, ten separate values `deviceId_0` through `deviceId_9`, and the writes that all targeted one range now spread across up to ten. This is the standard remedy for the timestamp and monotonic-key hot spots described earlier, because it breaks the serialization of writes onto a single current value.

```csharp
// Suffix synthetic key to spread a write hot spot across N buckets
int bucket = Random.Shared.Next(0, 10);
item.PartitionKey = $"{item.DeviceId}_{bucket}";
await container.CreateItemAsync(item, new PartitionKey(item.PartitionKey));
```

### What does a synthetic suffix cost on reads?

The suffix that rescues writes complicates reads, and the trade is the central fact to understand before adopting the pattern. Because the natural value is now split across a known set of buckets, any read that wants all data for the natural value must address every bucket and combine the results, so a single point read becomes a small fan-out across the bucket count.

If you spread `deviceId` across ten buckets, retrieving everything for one device means issuing the query against ten values, either as ten targeted reads or as a query with an `IN` clause over the ten suffixes, and merging what comes back. This is far cheaper than a full cross-range fan-out, because you address ten known values rather than every range in the container, but it is not free, and it pushes complexity into the read path that the write path shed. The decision rule is therefore directional: use a suffix when writes are the bottleneck and reads for a single natural value are rare or tolerant of the small fan-out, and avoid it when reads for a single natural value are themselves on the hot path, because then you have merely moved the cost from writes to reads. Choosing the bucket count is its own small trade, since more buckets spread writes more thoroughly but widen every read fan-out, and a count in the single or low double digits usually balances the two for a genuine hot spot.

### How do I keep a synthetic key consistent?

A synthetic value is derived, so it can drift out of agreement with the fields it was computed from if those fields are ever updated, and a drifted key is worse than a bad key because it scatters an item's logical group membership unpredictably. The defense is to compute the synthetic value in exactly one place, treat the source fields as immutable once the item is written, and never update a synthetic key in place.

Because the key places the item physically, you cannot change a synthetic key on an existing item with an update; you must delete the item and re-insert it with the new key, which is the same constraint that applies to any placement value. The practical consequence is that the fields feeding a synthetic key should be ones that do not change for the life of the item, such as a tenant assignment or a record type set at creation, rather than mutable attributes such as a status. If a feeding field genuinely must change, the synthetic key was the wrong design, because every change forces a delete-and-reinsert that the application has to orchestrate carefully to avoid losing the item. Picking immutable inputs is therefore part of designing the synthetic key, not an afterthought.

## Hierarchical partition keys: distributing on more than one level

The hierarchical key, also called subpartitioning, is the configuration that solves a problem the single key cannot: a natural prefix that you want to query by but that grows past the per-group storage ceiling. It lets you declare up to three levels, and the platform treats the combination as the placement value while still letting queries that supply only a leading prefix route efficiently to the subtree under that prefix. It is the cleanest answer to the dominant-tenant problem and the most underused of the three patterns.

Consider a multitenant application keyed on `/tenantId`. The key aligns beautifully with tenant-scoped queries, and for most tenants the data fits comfortably. The problem is the one enormous tenant whose data exceeds the twenty-gigabyte ceiling for a single logical group. With a single-level tenant key that tenant simply cannot store more than the ceiling allows, and no provisioning or rebalancing changes that, because the ceiling is a property of one group and that tenant is one group. A hierarchical key declared as `/tenantId` then `/userId` changes the arithmetic. Now the storage ceiling applies to each tenant-and-user combination rather than to the tenant as a whole, so a tenant with many users can spread far past the single-group ceiling, while a query that filters only on the tenant still routes to the set of ranges holding that tenant rather than fanning across the entire container.

That last property is what makes the hierarchical key superior to a synthetic concatenation for this case. A concatenated key of tenant and user would also raise cardinality, but a query that knows only the tenant and not the user could not target it, because the concatenated value is opaque and the query lacks the full string. The hierarchical key preserves the prefix as a first-class routing target, so a tenant-only query is a prefix query that the service can scope to the tenant's ranges, while a tenant-and-user query is a full-key query that routes to one range, and both are efficient. You get the distribution of the combined value and the queryability of the leading field at the same time, which the concatenation cannot offer.

### When does a hierarchical key beat a synthetic one?

Reach for the hierarchical key when you have a natural multi-level access pattern and a real risk that the top level grows past the per-group ceiling. The decisive test is whether you need to query efficiently by the prefix alone as well as by the full path. If both prefix queries and full-path queries are on the hot path, the hierarchical key serves both; a synthetic concatenation serves only the full path.

If, by contrast, you never query by the prefix alone, and you only need to raise cardinality so the data distributes, the synthetic concatenation is simpler and equally effective, and you should prefer it because it adds no creation-time commitment beyond a computed field. The hierarchical key earns its added planning when the prefix is itself a meaningful query boundary, which in practice means multitenant designs where some operations are tenant-wide and others are user-specific, device fleets where some queries span a device and others a single sensor, or any domain with a genuine containment relationship between the levels. Where there is no such containment, the hierarchy is overhead, and the flat synthetic key is the right tool.

### What are the limits of a hierarchical key?

The hierarchy supports a fixed maximum number of levels, currently three, and like every key it is set at creation and cannot be added to or changed on an existing container, so a flat container cannot be promoted to hierarchical in place. The level order is also fixed and meaningful, since only a leading prefix can be used to scope a query; you cannot supply the second level without the first and still route efficiently.

These constraints mean the hierarchical decision is the most consequential of the creation-time choices, because it cannot be retrofitted and because getting the level order wrong undermines the queries it was meant to serve. If your most common scoped query filters on the user across all tenants rather than the tenant, then leading with the tenant is the wrong order, and you will discover that your important query cannot use the prefix at all and fans out instead. The order must follow the queries, broadest meaningful scope first, and that ordering decision deserves the same scorecard scrutiny as the choice of fields themselves. As with the flat key, the safest way to validate a hierarchical design before committing production data is to build it against a sandbox account, load representative data, and watch how prefix and full-path queries route, which is exactly the kind of experiment the VaultBook labs are built to run without risk.

## Why the key cannot change, and what a change actually requires

The constraint that shapes every decision in this guide is that the placement path is immutable for the life of the container. You set it at creation, and there is no operation that alters it afterward, no portal toggle, no command-line flag, no template change that the platform will apply to an existing container's data in place. This is not an arbitrary restriction; it follows directly from the architecture, because the key determines where every item physically lives, and changing the placement path would mean rehashing and relocating every item in the container, which is precisely what a migration to a new container does, only done explicitly by you rather than silently by the service.

Engineers regularly assume the opposite, that a key is a setting like an index policy that can be revised when the access pattern shifts, and this assumption is the second great mistake the scorecard is built to prevent, alongside choosing a low-cardinality field. The two mistakes compound: a team picks a convenient low-cardinality key because they believe they can change it later, the container scales, the key throttles, and only then do they learn that the fix is a migration. Treating the key as permanent from the first day is therefore not pessimism but accuracy, and it is why the planning sequence puts the irreversible choices last and under the most scrutiny.

### Can I change a Cosmos DB partition key after creation?

Not in place. You change a key by creating a new container with the correct key and moving the data into it, then cutting traffic over to the new container and retiring the old one. The key path on an existing container is fixed; the only path to a different key is a new container and a data migration, planned and executed as a project rather than a configuration edit.

The migration itself has a standard shape worth knowing before you need it, because knowing it removes the panic from the moment you discover a key is wrong. You create the target container with the chosen field, then you copy the existing data into it, transforming each item to carry the new placement value as you go, which for a synthetic or hierarchical target means computing the new key field during the copy. The copy can run through a bulk tool, through a custom job using the bulk-execution mode of the SDK, or through the change feed, which is often the most graceful option because it lets you backfill the historical data with a one-time copy while the change feed streams ongoing writes into the new container, keeping the two in sync until you are ready to switch. Once the target is fully populated and caught up, you point the application's writes and reads at the new container, verify under real traffic, and then delete the old one. The cutover is the delicate part, since for a window both containers may receive writes, and the usual tactics are a brief write freeze, a dual-write period, or a change-feed-based catch-up that closes the gap just before the switch.

### How do I migrate to a new key with the change feed?

The change feed exposes an ordered record of every create and update in the source container, so a migration job reads that feed from the beginning, writes each item into the target container under its new key, and then continues consuming the feed to carry forward writes that arrive during the backfill. When the feed is caught up, you switch traffic.

```csharp
// Sketch: copy from source to a re-keyed target via the change feed
using FeedIterator<SourceDoc> iterator = sourceContainer
    .GetChangeFeedIterator<SourceDoc>(
        ChangeFeedStartFrom.Beginning(),
        ChangeFeedMode.Incremental);

while (iterator.HasMoreResults)
{
    FeedResponse<SourceDoc> page = await iterator.ReadNextAsync();
    foreach (SourceDoc doc in page)
    {
        // compute the new key value during the copy
        doc.PartitionKey = $"{doc.TenantId}_{doc.RecordType}";
        await targetContainer.UpsertItemAsync(doc, new PartitionKey(doc.PartitionKey));
    }
}
```

The reason the change feed approach is usually preferred over a one-shot bulk copy is that it decouples the slow historical backfill from the fast tail of recent writes, so you can run the heavy copy for as long as it takes without freezing the application, then close the remaining gap in a short final pass. It also gives you a natural validation point, since you can compare item counts and spot-check records between the two containers before committing the cutover. The migration is never trivial, which is the entire argument for grading the key carefully the first time, but it is a known, bounded procedure rather than a crisis, and treating it as one keeps the eventual re-key, if it ever comes, calm and reversible until the final switch.

## Aligning queries to the key so reads stay cheap

Choosing a well-distributed key is half the configuration; the other half is writing the queries so they actually use it. A perfectly distributed key delivers cheap, fast reads only when the queries supply its value, and the same key delivers expensive fan-out reads when they do not, so alignment is a property of the query as much as of the placement field, and the two have to be designed together. The single most valuable habit here is to include an equality filter on the key in every query on the hot path, and to know consciously which of your queries cannot do that and why.

A query that filters on the key with equality is a single-range query. The service resolves the value to one range and runs the query there, so the request-unit cost reflects only the data in that one group and the latency is the latency of one range. A query that filters on a non-key field, or that filters on a range of key values rather than a single value, becomes a cross-range query: the service runs it against every range, each contributes its matches, and the results are merged. The cost of the cross-range query rises with the number of ranges, which means it gets more expensive precisely as the container grows, and the latency is bounded by the slowest range rather than the average. The asymmetry between the two is large and grows with scale, which is why the alignment of the hot-path queries is a first-class part of the design rather than a tuning detail to revisit later.

### How do I know if a query is fanning out?

Read the request charge and the query metrics the SDK returns with every response. A single-range query shows a request charge that stays roughly flat as the container grows and as the number of ranges increases, while a cross-range query shows a charge that climbs with the range count and query metrics that report the query touching multiple physical ranges.

The request charge is the most direct signal, since it is returned on the response of every query and read, and watching how it behaves as your data set grows tells you immediately whether a query scales with the key or with the container. A query whose charge is two or three units on a small container and two or three units on a large one is aligned; a query whose charge climbs from a handful of units into the dozens or hundreds as ranges multiply is fanning out, and the climb is the warning that the query will become a cost problem at scale. The diagnostic discipline is to capture the request charge for each hot-path query against a representative data set rather than a tiny test set, because the fan-out penalty is invisible at small scale and only emerges once the platform has split the container into many ranges. The detailed walkthrough of reading these signals when a throttling incident is already underway lives in the guide to [fixing Cosmos DB 429 rate-limit errors](/2022/09/05/fix-cosmos-db-429-rate-limit/), and the same metrics serve you here as a preventive check rather than a postmortem.

### What if two queries want different keys?

When one query filters by tenant and another by user across all tenants, no single key serves both efficiently, and you resolve the conflict by choosing the key for the hotter query and giving the other query a separate path to its data. The usual separate path is a second container, fed by the change feed, keyed to suit the second query, so each query reads from a store aligned to it.

This pattern, a materialized view maintained by the change feed, is the standard answer to the genuine multi-access-pattern problem, and it is worth naming because engineers often torture a single key trying to serve two incompatible query shapes when the cleaner design is two stores. The primary container holds the data keyed for the dominant access pattern, the change feed projects every write into one or more secondary containers each keyed for a different query, and each read goes to the store whose key it can supply. The cost is the extra storage and the throughput to maintain the projections, and the benefit is that every read is a single-range read against a store aligned to it, which keeps the cost flat as the system scales. The decision between forcing one field and building a projection comes down to how hot the secondary access pattern is: a rare query can tolerate a fan-out, while a hot one earns its own aligned store.

## Six configuration patterns engineers meet in production

The scorecard and the three gates are the theory; the patterns below are the recurring shapes that theory takes in real systems. Each is a situation engineers report repeatedly, paired with the setup choice that resolves it. Reading them as a set is useful because most real designs are a blend of two or three, and recognizing which patterns your workload contains tells you directly which key construction to reach for.

### A status or boolean field concentrating all the writes

The first pattern is the team that keyed on a workflow status, an `isActive` flag, or a small category enumeration because it was the field they reasoned about most in code. The container behaves until it grows, and then every write to the busy status value lands on one range and throttles while the rest of the provisioned throughput sits unused on the ranges holding the other statuses. The fix at the design stage is to reject any low-cardinality field on the cardinality gate before it is ever chosen, and the fix once it is in production is a migration to a high-cardinality key, often the entity identifier the records actually belong to, with the status demoted to an ordinary indexed field that queries can still filter on without it being the placement value. Status is a fine thing to query by and a terrible thing to place by, and separating those two roles is the whole lesson of this pattern.

### A single large tenant dominating a tenant key

The second pattern is the multitenant container keyed on `/tenantId` that works for the long tail of small tenants and breaks on the one enterprise customer whose data and traffic dwarf everyone else's. The dominant tenant's group becomes a hot range and, if it keeps growing, approaches the per-group storage ceiling. The setup choice is the hierarchical key, leading with the tenant and adding a second level such as the user or the entity, which spreads the giant tenant across many ranges while preserving the tenant as an efficient query prefix for the small tenants and the large one alike. This is the textbook case for subpartitioning, and recognizing it early, before the big customer onboards, is what lets you create the container hierarchical from the start rather than migrating under pressure when that customer's load arrives.

### Needing a synthetic key to raise cardinality

The third pattern is the workload whose natural key candidates are all individually too coarse: the tenant has too few values, the type has too few values, and neither alone distributes. Here the setup choice is the synthetic concatenation, joining two natural fields into one computed key that multiplies their cardinality and aligns with the query that filters on both. This pattern is common in reference-data and configuration stores where the natural grain is a combination rather than a single field, and the key insight is that the combination, not either component, is the real identity by which the data is accessed, so making the combination the key simply names what was already true about the access pattern.

### A hierarchical key for tenant-then-entity access

The fourth pattern overlaps with the second but is driven by query shape rather than by a single dominant tenant. Some operations in the application are tenant-wide, listing or aggregating across a tenant, while others are entity-specific, reading one user's or one device's records. A flat tenant key serves the tenant-wide operations but forces the entity-specific ones to scan the whole tenant, while a flat entity key serves the entity reads but forces the tenant-wide ones to fan out. The hierarchical key of tenant then entity serves both, because the tenant-wide operation is a prefix query and the entity operation is a full-key query, and both route efficiently. The pattern is worth distinguishing from the second because the trigger is the dual query shape, not the size skew, and a workload can have the dual shape without any single tenant being dominant.

### A query without the key fanning out

The fifth pattern is the well-distributed container whose bill creeps up because an important query filters on a field that is not the key. The data spreads fine, nothing throttles, but a frequently run report or lookup fans across every range and its cost grows with the container. The setup choice depends on how hot the query is: a rare query can be left to fan out, an occasional one can be served by a narrower index or a more selective filter that reduces the data each range scans, and a hot one earns a change-feed-fed secondary container keyed to the query so the read becomes single-range. The discipline this pattern teaches is to inventory the hot-path queries against the chosen field during design and to plan a projection for any that cannot align, rather than discovering the misalignment through a cost report months later.

### Needing to migrate to a new key

The sixth pattern is the container that was keyed wrong, has grown, and now must be re-keyed, which is the situation the immutability of the key forces you into when one of the first five patterns was missed at design time. The setup choice is the migration procedure described earlier: a new container with the correct key, a change-feed-driven backfill and catch-up, a verified cutover, and the retirement of the old container. The pattern belongs in this list because it is so common, and its presence in nearly every mature Cosmos deployment that started without a scorecard is the strongest practical argument for using one. The cost of the migration, in engineering time and in the risk of the cutover, is the price of the original guessed key, and the scorecard exists to make sure you pay that price at most once.

## The defaults and interactions that surprise people

A correct placement field is necessary but not sufficient, because several surrounding settings have defaults that quietly undermine an otherwise sound design, and knowing them is part of configuring the container rather than just the field. The interactions below are the ones engineers most often discover after the fact, when a design that graded well on paper behaves worse than expected, and each has a default that leans the wrong way for a high-scale workload.

The first is the indexing policy. By default the container indexes every property of every document, which is convenient for ad hoc queries but expensive on the write path, since every write pays to update the index for fields it will never be queried on. The indexing policy does not change where items live, so it is independent of the placement decision, but it interacts with it through cost: a write-heavy container whose placement spreads beautifully can still burn request units indexing fields nobody filters on, and trimming the index to the properties your queries actually use frees budget that the even distribution can then put toward real work. The relationship between indexing and throughput cost is treated thoroughly in the [Cosmos DB throughput and RU optimization](/2024/08/26/cosmos-db-throughput-optimization/) guide, and the practical point here is that placement and indexing are two separate levers that both shape cost and should be tuned together rather than one in isolation.

The second is the throughput model and how forgiving it is of mild imbalance. Container-level provisioned throughput shares one budget across every logical group, database-level provisioned throughput shares a budget across containers, and serverless bills per request. A generously provisioned container tolerates more skew before any single range exceeds its slice, which can mask a marginal placement choice during early testing and let it slip into production undetected, only to throttle once the budget is tightened or the data grows. The lesson is to test the distribution under a realistic provisioning level rather than an inflated one, because a placement field that only looks balanced because it is swimming in spare capacity is a field that has not actually been verified.

### Which defaults most often cause trouble?

The full-indexing default and the assumption that placement can be revised later are the two that cause the most grief. Full indexing inflates write cost on properties nobody queries, and the belief that the placement field is editable leads teams to choose convenient low-cardinality fields they expect to change, only to find the choice sealed once data lands.

A third, quieter default is how absent and null values are handled, covered earlier: the platform groups them under a single undefined value rather than rejecting the write, so a field that is sometimes missing silently builds a hot group. None of these defaults is wrong in itself; each is a reasonable starting point for a small or exploratory container. They become problems only when a workload scales while still carrying defaults that were never revisited, which is why a deliberate configuration pass, walking the indexing policy, the throughput model, and the value-validation in the write path alongside the placement field itself, is what turns a container that works in development into one that holds up in production. Treating the placement field as the only decision and accepting every surrounding default is the most common way a well-graded field still underperforms.

The fourth interaction worth naming is between the placement decision and the consistency level. The consistency you choose affects read cost and latency but does not change where data lives, so it is orthogonal to distribution; the trap is assuming that a stronger consistency level can compensate for a concentrated design or that a weaker one can rescue a misaligned query. It cannot do either. Consistency governs how fresh a read is across replicas, distribution governs where the work lands, and conflating the two leads to tuning the wrong knob when a container struggles. Keep the decisions separate: grade the placement field on the three gates, set indexing to match the queries, size throughput to the verified distribution, and choose consistency for the freshness the application needs, each on its own merits.

## Verifying that the placement field is doing its job

A configuration is not done when the container is created; it is done when you have confirmed the key distributes data and traffic the way the scorecard predicted. Verification matters most for synthetic and hierarchical constructions, where the computed value can behave differently from the napkin estimate, but even a natural key benefits from a check against real data before the design hardens into a production dependency. The verification has two halves: confirm the storage spreads, and confirm the requests spread.

For storage, the portal exposes a view of how data is distributed across the physical ranges, and a healthy key shows ranges of comparable size rather than one or two ranges holding most of the data. A lopsided storage picture early is a warning that the key has a dominant value or a low effective cardinality, and it is far cheaper to catch and correct that during a load test than after months of production writes. The check is simple: load a representative volume of data, ideally with the skew you expect in production rather than uniform synthetic data, and look at whether the ranges fill evenly. If one range balloons, you have found a hot group before it became a hot range under live traffic.

For requests, the request-unit metrics show consumption across the ranges, and a healthy key shows consumption spread roughly in proportion to where the traffic should go rather than spiked on one range. The most direct preventive test is to replay or simulate the expected traffic mix against the loaded container and watch whether any single range approaches its throughput slice while others stay idle, because that imbalance is the exact precursor to throttling. Catching it in a test means you can adjust the placement field, the bucket count of a suffix, or the level order of a hierarchy before any of those choices is locked behind production data.

### How do I confirm the configuration worked?

Load representative data and run your expected query mix, then read two things: the storage distribution across physical ranges, which should be roughly even, and the per-query request charge, which for hot-path queries should stay flat as data grows rather than climbing. Even storage plus flat request charges on aligned queries is the signature of a field that will scale.

The pairing of those two checks is deliberate, because each catches a different failure. Even storage with climbing request charges means the data spreads but the queries are misaligned and fanning out, which points you at the query design or a secondary projection rather than at the key. Flat request charges with lopsided storage means the queries you tested happen to be aligned but the data has a dominant value that will eventually create a hot range, which points you at the cardinality or evenness of the key. Only when both checks pass together is the configuration genuinely sound, and running them as a deliberate gate before promoting the container to production is what converts the scorecard from a planning exercise into a verified result. The throughput side of this verification, including how to size the provisioned units so the even distribution actually has enough budget to work with, is covered in depth in the [Cosmos DB throughput and RU optimization](/2024/08/26/cosmos-db-throughput-optimization/) guide.

## Making the configuration repeatable as code

The last step in configuring a key well is to make sure the next container is configured just as deliberately, and that means capturing the decision in code rather than in a portal session and a memory. Because the placement field is irreversible, a container created by hand in the portal under deadline pressure is the single most dangerous artifact in a Cosmos deployment, since the one decision that cannot be undone is also the one most likely to be made carelessly when it is made by clicking through a wizard. Declaring the container, its key, and its throughput in an infrastructure template removes that danger by making the key a reviewed line in a pull request.

The template also documents the intent. A `paths` array with a single entry, or with three entries and a `MultiHash` kind, records not just the value but the shape of the decision, and a reviewer who understands the scorecard can read that line and ask the right question: is this field high in cardinality, is its access even, does it align with the dominant query. That review, applied before any data lands, is the cheapest possible place to catch a weak key, far cheaper than the storage check, which is cheaper than the request check, which is itself far cheaper than a migration. Pushing the scrutiny as early as possible in this chain, all the way back to a template review, is the operational expression of taking the irreversibility seriously.

Keeping the key in code also makes the eventual migration, if it comes, cleaner, because the target container is declared the same way and the difference between the old and new key is a visible diff rather than a remembered intention. A team that templates its containers can stand up a re-keyed target alongside the original, run the change-feed backfill, and cut over with the whole change captured in version control, which turns the migration from an improvised scramble into a reviewed, repeatable change. The same VaultBook labs that let you experiment with key choices also let you rehearse this template-driven creation and migration flow against a sandbox, so the first time you run it against a real container is not the first time you have run it at all.

## The verdict

The partition key is the one Cosmos DB decision that rewards being slow and deliberate, because it is the one decision you cannot take back. Everything else about a container, the throughput, the indexing policy, the consistency level, the network exposure, can be changed after the fact with a setting or a brief reconfiguration. The key cannot, and a wrong key does not announce itself until the container has grown enough to make the migration that fixes it genuinely costly. That asymmetry, cheap to get right at the start and expensive to fix later, is exactly the profile of a decision that deserves a scorecard.

So grade every candidate on the three gates before you commit one. Demand high cardinality so the data can spread, demand even access so no single value becomes a hot range, and demand alignment with your dominant query so reads stay single-range and cheap as the container grows. When no natural field clears all three, build a synthetic key to raise cardinality or to spread a write hot spot, or a hierarchical key when you need both a queryable prefix and distribution past the per-group ceiling, and pay each pattern's read trade-off knowingly. Verify the result against representative data before you trust it, capture the choice in a template so it is reviewed rather than guessed, and treat the key as permanent from the first line of code. Do that, and the irreversible decision becomes a deliberate one, which is the whole point: not that the placement field is hard to change, but that you choose it well enough that you never have to.

## Frequently Asked Questions

### Q: How do I choose a Cosmos DB partition key the right way?

Grade every candidate field against three independent gates and accept only one that passes all three. The first gate is cardinality: the field must take many distinct values so the data can spread across many ranges, which rules out status flags, booleans, and small enumerations. The second is even access: live read and write traffic must spread across those values rather than piling onto a few, which rules out timestamps in write-heavy workloads and any field where one value dominates. The third is query alignment: the field should be the one your most frequent, most latency-sensitive queries filter on, so those queries route to a single range. Start from the access patterns, not the schema, list the hot-path queries and the field each filters on, estimate distinct values at production scale rather than in test data, and only then pick the field. If no natural field clears all three gates, build a synthetic or hierarchical key rather than settling for a weak natural one.

### Q: Why does cardinality matter for the partition key?

Cardinality is the number of distinct values the key can take, and it sets the hard ceiling on how far the container can spread its load, because a single value forms one logical group and a logical group can never be split across two physical ranges. A low-cardinality key, such as a five-value status, can occupy at most a handful of groups no matter how large the data grows, so the data crowds onto a few ranges while the rest sit empty holding throughput you cannot use. The trap is that low cardinality is invisible at small scale, where a few groups fit comfortably, and only becomes a problem once the container grows enough to need many ranges. That is why the cardinality estimate must reflect production volume rather than test data, and why a field whose value space is bounded by a small enumeration should be rejected on this gate alone before you weigh anything else about it.

### Q: When should I use a synthetic partition key?

Use a synthetic key when no single natural field clears all three gates and you need to engineer the missing property. There are two cases. If the dominant query filters on a combination of fields and neither alone has enough cardinality, concatenate them into one computed value, such as joining a tenant and a record type, which multiplies cardinality and aligns with the combined query. If a natural value creates a write hot spot because too much traffic targets it, append a bounded random or hashed suffix to fan that one value across several buckets, turning a serialized write stream into a spread one. The concatenation pattern sharpens alignment; the suffix pattern spreads writes at the cost of turning single reads into a small fan-out across the buckets. Compute the synthetic value in one place in the data layer, feed it only from fields that never change for the life of the item, and never update it in place, since changing a placement value requires deleting and re-inserting the item.

### Q: What is a hierarchical partition key and when does it help?

A hierarchical partition key, also called subpartitioning, lets you declare up to three levels, such as tenant then user then session, and the platform places items by the full combination while still letting queries that supply only a leading prefix route efficiently. It helps in two situations that a flat key cannot serve together. First, when a natural prefix such as a tenant risks growing past the per-group storage ceiling, the hierarchy applies that ceiling to each combination rather than to the prefix as a whole, so a large tenant can spread far past the single-group limit. Second, when some queries are prefix-scoped, like everything for a tenant, and others are full-path, like one user's records, the hierarchy serves both because the prefix query routes to the tenant's ranges and the full-path query routes to one range. It beats a synthetic concatenation specifically when you need to query by the prefix alone, which a concatenated opaque string cannot support. Like any candidate, it is fixed at creation and cannot be added later.

### Q: Can I change a Cosmos DB partition key after creation?

No, not in place. The key path is immutable for the life of the container, because it determines where every item physically lives, so changing it would mean relocating every item, which is exactly what a migration to a new container does. To change a key you create a new container with the correct key, copy the existing data into it while computing the new placement value during the copy, then cut traffic over and retire the old container. The graceful way to run the copy is through the change feed: backfill the historical data with a one-time read from the beginning of the feed, keep consuming the feed to carry forward writes that arrive during the backfill, and when the target is caught up, switch the application to the new container, verify under real traffic, and delete the old one. The cutover is the delicate moment, usually handled with a brief write freeze, a dual-write window, or a change-feed catch-up that closes the gap just before the switch. Because the fix is a project rather than a setting, grade the key carefully the first time.

### Q: How do I align queries to the partition key?

Include an equality filter on the key field in every query on the hot path, so the service can resolve the value to one range and run the query there rather than fanning it across every range. A query that supplies the placement value is a single-range query whose cost stays roughly flat as the container grows; a query that omits the placement field, or that filters on a range of key values, becomes a cross-range query whose cost climbs with the number of ranges and whose latency tracks the slowest range. Watch the request charge returned on every query response: a charge that stays flat as data grows is aligned, while a charge that climbs as ranges multiply is fanning out. When two different queries each want a different field as the key, you cannot serve both with one field, so choose the key for the hotter query and give the other a change-feed-fed secondary container keyed to suit it, so each read goes to a store aligned to it.

### Q: Can I use the document id as the partition key?

Yes, and it is a strong choice for point-read, key-value style workloads. Using `/id` as the key gives maximum cardinality, since every item has a unique identifier, so storage and write load spread perfectly evenly with no risk of a dominant value. It also makes a point read by id the cheapest possible operation, because the read addresses exactly one item in exactly one group. The limitation is that no query can ever target more than a single item by the key, since no two items share a value, so any access pattern that needs to read a set of related items together cannot use the key for that and must either fan out across ranges or rely on a secondary access path. Choose `/id` when your dominant pattern is fetching individual documents by their identifier and you rarely need to read related collections in one query; avoid it when your workload is built around reading groups of related records, where a field that gathers those records into one group serves you better.

### Q: What happens if the partition key field is missing or null on an item?

The service treats a missing or null placement value as its own distinct group value rather than rejecting the write, which is more dangerous than an error because it fails silently. Every item written without the key field set, or with it set to null, lands in the same undefined group, and that group quickly becomes the largest in the container, behaving exactly like a low-cardinality hot spot: concentrated storage, concentrated traffic, and eventual throttling on the one range that holds it. Because the SDK will not stop you, the guard has to live in the application's write path, validating that the key field is present and populated on every item before it is inserted. This validation is part of configuring the key correctly, not a separate concern, and it belongs in the data layer where every write passes through rather than in a periodic cleanup job, since by the time a cleanup job runs the malformed items have already been placed and the only way to move them is to delete and re-insert each one with a proper placement value.

### Q: Is there a limit on how large a single logical partition can grow?

Yes. All items sharing one placement value form a single logical group, and that group has a storage ceiling, historically twenty gigabytes for a non-subpartitioned container, a figure worth confirming against current service limits when you read this. The ceiling exists because a logical group cannot be split across physical ranges, so it must fit within the storage one range can hold. When a group reaches the ceiling it cannot accept more data under that placement value, regardless of how much capacity the rest of the container has, and the application will see write failures for that value. This is why a field that funnels an unbounded stream into one value, such as a single dominant tenant on a flat tenant key, is a design wall rather than merely a performance issue. The remedy is a key with enough cardinality that no single value approaches the ceiling, or a hierarchical key that applies the ceiling per combination rather than per prefix, letting a large prefix spread its data across many groups and many ranges.

### Q: Can a Cosmos DB container exist without a partition key?

For practical, scalable workloads you should always define one, and the modern container model expects a key path at creation. While very small fixed-size containers existed in older models without an explicit user-chosen key, relying on that is a mistake for anything that will grow, because without a well-chosen key the container cannot spread across multiple physical ranges and is capped at the throughput and storage a single range can serve. The right mental stance is that every container has a placement rule, and your job is to make that rule a deliberate, high-cardinality, well-aligned field rather than to leave it to chance. Even a container you expect to stay small should be keyed on purpose, both because workloads outgrow expectations and because the placement field is irreversible, so the cost of choosing one thoughtfully at creation is trivial compared to the cost of discovering later that an unkeyed or poorly keyed container cannot scale and must be rebuilt.

### Q: How do I declare the partition key in a Bicep or ARM template?

In the container resource, set the `partitionKey` property with a `paths` array and a `kind`. For a single-property key the array has one entry, such as `/customerId`, and the kind is `Hash` with version 2. For a hierarchical key the array carries up to three entries in broad-to-narrow order and the kind becomes `MultiHash`, with the array order setting the level order. Declaring the key in a template rather than the portal is strongly recommended precisely because the choice is irreversible: a template makes the key a reviewed line in a pull request, where a colleague who understands the cardinality, evenness, and alignment gates can challenge it before any data lands, which is the cheapest possible place to catch a weak key. The template also documents intent and makes a future migration cleaner, since the re-keyed target container is declared the same way and the difference between old and new keys appears as a visible diff in version control rather than living only in someone's memory of a portal session.

### Q: What is the maximum length of a partition placement value?

A single partition key value has a length ceiling on the order of a couple of kilobytes, a limit worth confirming against the current documentation since service limits change. In practice this only matters if you are tempted to use a long string, such as a concatenation of many fields or an entire path, as the key value. If a synthetic concatenation grows long, that is usually a signal the key is carrying too much and you should reconsider which fields genuinely belong in it. For hierarchical keys the constraint applies across the combination, so very long values at multiple levels are something to watch. The everyday guidance is that good keys are short, stable identifiers, a tenant, a user, a device, or a compact concatenation of two such fields, and a key value approaching a kilobyte is almost always a design that has gone astray rather than a legitimate use of the available length. Keep the value compact and meaningful, and the length limit never becomes a concern.

### Q: Can I use a nested property as the partition key?

Yes. The key path is a JSON path into the document, so a property nested inside an object is addressed by extending the path, for example `/owner/customerId` for a `customerId` field inside an `owner` object. The service reads the value at that path on every item exactly as it does for a top-level property, and all the same rules apply: the nested property must be present and populated on every item, must be effectively immutable per item, and is graded on the same three gates. The one practical caution is that a nested key path makes the field's importance less obvious to someone reading the document or the write code, so it is easier to forget to populate it, which raises the risk of the missing-value failure where items collect under an undefined group. If you key on a nested property, make the validation that it is always set especially explicit in the write path, and consider whether promoting the field to the top level would make the design clearer without any cost to behavior.

### Q: How do I choose the level order for a hierarchical partition key?

Order the levels broadest meaningful query scope first, because only a leading prefix can scope a query efficiently, and you cannot supply a deeper level without the levels above it. The order must follow your queries: if your common scoped query filters by tenant and a deeper query adds the user, lead with tenant then user, so the tenant query is a prefix query and the tenant-and-user query is a full-key query, and both route efficiently. Getting the order wrong undermines the whole point of the hierarchy, because a query that filters only on what you placed second cannot use the prefix and will fan out across the container. Since the order, like the levels themselves, is fixed at creation and cannot be changed in place, it deserves the same scorecard scrutiny as the choice of fields. Before committing, list your scoped queries, confirm that each one filters on a contiguous leading prefix of your proposed order, and adjust the order until the hot-path queries all align to a prefix or to the full path.

### Q: Does the partition key matter for a small container that will never grow?

It matters less for behavior while the container stays small, since a few ranges absorb mild imbalance, but it still matters for two reasons that argue for choosing deliberately anyway. First, workloads routinely outgrow the expectations set at design time, and a container assumed to stay small often does not, at which point a convenient low-cardinality key becomes a migration. Second, the key is irreversible regardless of size, so the cost of choosing a sound key at creation is essentially zero while the cost of a wrong one is a rebuild, which makes deliberate choice a free insurance policy. The pragmatic stance is to apply the scorecard lightly to small containers rather than skipping it: pick a field with reasonable cardinality that aligns with how you read the data, and you have lost nothing if the container stays small and gained a smooth path if it grows. Treating even small containers as if they might scale is cheaper than the alternative of discovering, after growth, that the easy early choice now requires a migration.

### Q: How is a Cosmos partition key different from a primary key in a relational database?

They serve different purposes and conflating them causes design mistakes. A relational primary key uniquely identifies a row and enforces uniqueness; a Cosmos partition key determines physical placement and groups items that share its value, and it does not by itself enforce uniqueness. In Cosmos the combination of the partition key value and the item id together identifies an item uniquely within the container, so the key is closer to a sharding or distribution column than to a primary key. The consequence for design is that you choose a Cosmos key for how it spreads load and aligns queries, not for how it identifies records, which is why a field that makes a fine relational primary key, like an auto-incrementing sequence, can make a terrible Cosmos key because its values correlate with arrival time and concentrate writes. Think of the partition key as the answer to where should this item live and which range answers queries for it, and think of the id as the answer to which item is this within its group, and keep those two roles distinct when you model the data.

### Q: Can different items in the same container have different partition keys?

No. The key path is a single property of the container, fixed at creation, and every item is placed by the value found at that one path, so all items share the same key definition even though they have different key values. What varies per item is the value at the placement path, not which path is the key. If your data has genuinely different access patterns that want different placement fields, the answer is not different keys in one container but either a single container keyed for the dominant pattern with change-feed-fed secondary containers keyed for the others, or separate containers from the start. This is also why a synthetic key, which all items compute the same way from their own field values, is the tool for combining fields rather than letting different item types use different fields as their key. The container has one placement rule; your design works within that by choosing one strong key, engineering it synthetically or hierarchically when needed, and projecting to additional keyed stores when one rule cannot serve every query.
