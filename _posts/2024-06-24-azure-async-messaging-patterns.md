---
layout: post
title: "Async Messaging Patterns on Azure"
page_title: "Async Messaging Patterns on Azure: Competing Consumers, Pub-Sub, Sessions, and Idempotent Consumers Explained"
date: 2024-06-24
categories: ["Technology"]
tags: ["Azure", "Service Bus", "Event Hubs", "Architecture", "Messaging", "Cloud Computing"]
excerpt: "Async messaging patterns on Azure ride on at-least-once delivery, so each pattern needs idempotent handling. A catalog mapping each design to its service."
image: "/assets/images/blog/blog-85.webp"
reading_time: 61
author: "abigail-cooper"
last_updated: 2024-06-24
lang: en
---
A team ships an order-processing service backed by a queue. It works in the demo. Then production traffic arrives, one consumer cannot keep up, and they add three more receivers to drain the backlog. Throughput recovers, and a week later finance reports that several hundred customers were charged twice. The team had reached for a scaling technique without noticing that it changed the delivery contract underneath them, and the queue that had quietly guaranteed order to a single reader now interleaved work across four readers with no order at all. Nothing in the code was wrong in isolation. The design drifted because the underlying guarantee was never made explicit.

This is the recurring shape of async messaging trouble on Azure. The platform hands you a small set of building blocks, queues, topics, subscriptions, sessions, partitions, and a delivery guarantee that is almost always at-least-once. Each building block solves one problem cleanly. The failures come from combining them without tracking what the combination does to ordering and duplication. An engineer who can name the four or five canonical designs, knows which Azure service realizes each, and treats duplicate handling as a non-negotiable companion to every one of them will not ship the double-charge bug. That is the gap this guide closes.

![Async messaging patterns on Azure with competing consumers, pub-sub, and sessions - Insight Crunch](/assets/images/blog/blog-85.webp)

The argument runs in one line that the rest of the article unpacks: every async messaging design on Azure rides on at-least-once delivery, so each design must be paired with idempotent handling, and that pairing is the discipline that makes the designs reliable rather than merely clever. Call it the pattern-plus-idempotency rule. A competing-consumers fan-out, a publish-subscribe broadcast, an ordered session stream, a claim-check for large payloads, none of them are safe on their own. They become safe when the consumer that processes a redelivered copy produces the same result as the consumer that processed the original. Hold that rule in mind and the rest of this is detail.

## What async messaging patterns actually are

A pattern in this context is not a library or a feature you switch on. It is a repeatable arrangement of producers, a broker, and consumers that solves one specific coordination problem. The problems are old: how do I spread work across many workers without losing any of it, how do I tell several interested parties about one event, how do I keep a related sequence in order while still scaling, how do I move a large blob through a system whose broker caps message size, how do I survive a worker crash without dropping or double-counting the unit of work. Each of these has a canonical answer, and on Azure each answer maps to a concrete configuration of Service Bus, Event Hubs, Event Grid, or Queue Storage.

The reason async messaging exists at all is decoupling. When service A calls service B synchronously over HTTP, A waits for B, A fails if B is down, and A must scale to match B's slowest moment. Place a broker between them and A records its intent and moves on. B reads when it is ready, at its own rate, and a B outage becomes a growing backlog rather than a cascading failure. That single move, replacing a blocking call with a durable handoff, is the foundation the entire field of [event-driven architecture on Azure](/2024/04/22/azure-event-driven-architecture/) builds on. The designs in this guide are the vocabulary you use once you have committed to that handoff.

### What does at-least-once delivery actually guarantee?

At-least-once delivery means the broker promises a consumer will see each message one or more times, never zero times. It does not promise exactly once. A crash between processing and acknowledgement causes the broker to redeliver, so the consumer must tolerate seeing the same item again without corrupting state.

The phrase deserves precision because everything downstream depends on it. Azure Service Bus, in its default PeekLock receive mode, hands a consumer a message and holds it invisible under a lock. The consumer does its work and then explicitly settles the message by completing it. If the consumer crashes after finishing the work but before the complete call lands, the lock eventually expires, the broker makes the item visible again, and a second consumer picks it up. The work runs twice. This is not a bug in Service Bus; it is the price of durability. The alternative receive mode, ReceiveAndDelete, removes the item the instant it is delivered, which yields at-most-once semantics and lower latency at the cost of silently losing anything that was in flight when a consumer died. Critical work almost never tolerates loss, so almost every production design uses PeekLock, accepts at-least-once, and pays for it with idempotency. Verify the exact lock and settlement behavior against the current Service Bus documentation before you depend on a specific timeout default, since these values are configurable and the platform revises guidance.

That is the whole basis of the namable claim. Because the delivery floor is at-least-once and not exactly-once, a design that assumes each message arrives exactly one time is wrong from the first line. The fix is never to chase a stronger broker guarantee Azure does not offer; it is to make the consumer indifferent to repetition.

## The Azure services that realize the patterns

Four services carry almost all async messaging on the platform, and choosing among them is the first design decision, not an afterthought. Each has a delivery model, an ordering model, and a throughput ceiling that decides which designs it can host.

Azure Service Bus is the enterprise broker. It speaks queues for point-to-point handoff and topics with subscriptions for fan-out, it supports sessions for ordered processing of related items, it offers broker-side duplicate detection on its standard and premium tiers, and it provides dead-lettering, scheduled delivery, transactions, and auto-forwarding. Its strength is correctness features rather than raw volume. When the workload is business transactions that must not be lost, reordered incorrectly, or processed twice, Service Bus is the default.

Azure Event Hubs is the high-throughput ingestion service. It is built for streams: telemetry, clickstream, application logs, anything that arrives at millions of events per second. It partitions the stream, preserves order within a partition, and lets consumers read at their own offset using checkpoints, which the [Azure Event Hubs engineering guide](/2022/03/28/azure-event-hubs-engineering-guide/) covers in depth. Event Hubs does not lock and complete individual events the way Service Bus does; consumers track position in a partition. That model is excellent for replayable streams and poor for per-item work distribution where each unit must be acknowledged independently.

Azure Event Grid is the reactive event router. It delivers discrete events from sources to subscribers using push semantics and HTTP webhooks or service handlers, with retry and dead-lettering. It is the right choice for "something happened, react to it" notifications rather than for buffering large volumes of work. Event Grid, Service Bus, and Event Hubs are easy to confuse, and the [comparison of Service Bus, Event Hubs, and Event Grid](/2025/05/12/service-bus-vs-event-hubs-vs-grid/) exists precisely to settle which one a given workload needs.

Azure Queue Storage is the simple, durable queue. It offers basic enqueue and dequeue with a visibility timeout and very high capacity at low cost, but it lacks sessions, topics, and broker-side duplicate detection. When the requirement is a plain, cheap, deep buffer and the consumer already handles ordering and duplicates on its own, Queue Storage is enough. When the requirement names ordering, fan-out, or deduplication, it is not.

### Which service should host ordered work?

Service Bus with sessions is the answer for ordered work where each item is acknowledged individually. Event Hubs preserves order only within a partition and suits high-volume streams. Queue Storage gives no ordering guarantee at all. Match the ordering requirement to the service before writing a line of consumer code.

## The InsightCrunch messaging-pattern catalog

Before the deep dives, here is the reference you can return to. Each row names a design, the coordination problem it answers, the Azure service that fits it, and the ordering and duplication property you must respect when you use it. This catalog is the findable artifact of the article; the sections that follow are its expansion.

| Design | Problem it solves | Azure service that fits | Ordering property | Duplication property |
| --- | --- | --- | --- | --- |
| Competing consumers | One consumer cannot drain the backlog | Service Bus queue or Queue Storage | Lost across the consumer group unless sessions are used | At-least-once, so consumers must be idempotent |
| Publish-subscribe | One event must reach many independent handlers | Service Bus topic with subscriptions, or Event Grid | Per subscription, optional with SupportOrdering on non-partitioned topics | Each subscriber gets its own copy, each delivered at-least-once |
| Ordered sessions | A related sequence must stay in order while still scaling | Service Bus sessions (SessionId) | Strict FIFO per session, parallel across sessions | At-least-once within the session, idempotency still required |
| Claim-check | The payload is too large for the broker | Service Bus or Event Grid plus Blob Storage | Inherits the carrier design's ordering | The reference is small and replayable; the blob is immutable |
| Message routing and filtering | Subscribers want only a subset of events | Service Bus subscription rules and filters | Per subscription | Filtered copies are still at-least-once |
| Idempotent consumer | At-least-once delivery causes duplicate side effects | Any of the above plus a processed-state store | Independent of ordering | Turns at-least-once into effectively-once side effects |

Read the table as a decision aid, not a menu of unrelated options. The bottom row is special: it is not an alternative to the others but a layer every other row depends on. That is the pattern-plus-idempotency rule in tabular form. You will choose competing consumers or sessions or pub-sub for the coordination shape you need, and you will add idempotent handling underneath whichever you chose, every time, without exception.

## Competing consumers: scaling work across receivers

The competing-consumers design answers one question. A single consumer reads from a queue and processes items one after another; when the arrival rate exceeds the processing rate, the backlog grows without bound. The answer is to run several consumer instances that all read from the same queue and race for each item. The broker hands any given item to exactly one of the competing instances, that instance processes and completes it, and total throughput scales close to linearly with the number of instances until some downstream resource becomes the bottleneck.

On Azure this is the most natural thing a Service Bus queue or a Queue Storage queue does. You do not configure a special mode. You point N worker instances at the same queue, and the broker's locking does the arbitration. With Service Bus PeekLock, when one worker locks an item the others cannot see it, so two workers never process the same item concurrently under normal operation. Scale the worker count up to drain a backlog faster, scale it down to save cost when the queue is shallow. Autoscale rules that watch queue depth, the same approach detailed for [autoscaling event-driven workloads](/2024/04/22/azure-event-driven-architecture/), turn this into a system that sizes its own worker fleet to the incoming load.

### Why does competing consumers break ordering?

Competing consumers breaks ordering because items are handed to whichever worker is free first, and workers finish at different speeds. Item two can complete before item one if a different, faster worker grabbed it. The queue's natural first-in arrival order survives only when exactly one consumer reads it serially.

This is the trap the opening team fell into. A single reader on a Service Bus queue processes in roughly first-in order because it takes one item, finishes, then takes the next. Add a second reader and that property evaporates. Reader A takes item one, reader B takes item two, B's work happens to be lighter and completes first, and now item two's effect lands before item one's. For independent items, account-creation jobs, image-resize tasks, notification sends, this does not matter and the throughput win is pure profit. For dependent items, the three events that must apply to one bank balance in order, it is a correctness failure. The competing-consumers design is correct only when the units of work are mutually independent. When they are not, you do not abandon scaling; you reach for sessions, covered below, which let you scale across independent groups while preserving order inside each group.

The second hazard is the duplicate. Because delivery is at-least-once, a worker that crashes after charging a card but before completing the message hands that exact item to another worker, which charges the card again. Competing consumers multiplies the surface for this because there are more workers and more chances for one to die mid-flight. The design does not cause duplicates, at-least-once delivery does, but a fleet of racing consumers is where duplicates show up first in production. The mandatory companion is an idempotent handler, which the dedicated section below builds.

## Publish-subscribe with topics and subscriptions

Competing consumers spreads one stream of work across many workers who share it. Publish-subscribe does the opposite: it takes one event and delivers a copy to every interested party independently. A Service Bus topic looks like a queue to the publisher, but instead of one queue behind it there are several subscriptions, and each subscription is itself a virtual queue with its own cursor. When a publisher sends to the topic, the broker drops a copy into every subscription whose filter the event matches. The orders subscription, the analytics subscription, and the audit subscription each receive their own copy and consume at their own pace, oblivious to one another.

This is the structural difference that matters. In a queue, one item is consumed once by one of the competing readers. In a topic, one item becomes as many copies as there are matching subscriptions, and each copy is consumed once within its subscription. A slow analytics consumer cannot back up the order processor, because they read from separate subscriptions. Adding a new consumer to the system means adding a new subscription, which the existing publishers and subscribers never notice. That additive property is why publish-subscribe is the backbone of loosely coupled designs: you grow the set of reactions to an event without touching the code that produces it.

```csharp
// Publisher sends once to the topic
ServiceBusSender sender = client.CreateSender("order-events");
var msg = new ServiceBusMessage(payload)
{
    Subject = "OrderPlaced",
    ApplicationProperties = { ["region"] = "us", ["tier"] = "gold" }
};
await sender.SendMessageAsync(msg);

// Each subscription receives its own copy, filtered by rule
ServiceBusProcessor processor =
    client.CreateProcessor("order-events", "analytics-sub", new ServiceBusProcessorOptions());
processor.ProcessMessageAsync += async args =>
{
    await HandleAnalytics(args.Message);
    await args.CompleteMessageAsync(args.Message); // settle within this subscription only
};
```

Event Grid offers a different flavor of the same idea. Where Service Bus topics pull copies into durable virtual queues that subscribers poll, Event Grid pushes events to subscriber endpoints, HTTP webhooks or Azure service handlers, with its own retry and dead-letter behavior. Use Service Bus topics when subscribers need a durable buffer they drain on their own schedule and when you want enterprise features like sessions or transactions on the subscription. Reach for Event Grid when the reaction is a lightweight push notification to a handler that is expected to be online. The decision between them, alongside Event Hubs, is the subject of the [Service Bus, Event Hubs, and Event Grid comparison](/2025/05/12/service-bus-vs-event-hubs-vs-grid/).

### How do publish-subscribe topics preserve order?

A non-partitioned Service Bus topic can preserve send order to each subscription when the SupportOrdering property is enabled, so subscribers receive items in the sequence the publisher sent them. Partitioned topics do not support this. For per-key order under load, combine the topic with sessions on the subscription instead.

Ordering in pub-sub is subtler than in a single queue because there are several independent readers. Within one subscription, a Service Bus topic with ordering support hands items to that subscription's consumer in send order, provided the topic is not partitioned and the consumer reads serially. The moment you add competing consumers to a single subscription to scale it, that subscription faces the same order-loss the queue faced, and the same remedy applies: sessions. Across subscriptions there is no cross-subscription ordering at all, and there should not be; the whole point is that the analytics path and the order path are independent. Design each subscription's ordering requirement on its own, and never assume the broadcast preserves a global sequence.

Duplication, again, rides along. Each subscription delivers its copy at-least-once, so a redelivery to the analytics consumer is independent of a redelivery to the order consumer. Two subscribers can each see their own copy twice for unrelated reasons. Every subscriber needs its own idempotent handling, scoped to what that subscriber does. The audit logger writing a duplicate row is a different problem from the billing consumer double-charging, and each is solved locally.

## Ordering with sessions

Sessions are the answer to the tension the competing-consumers section left open: you need order for related items, and you also need to scale. A Service Bus session groups items by a SessionId you set on each one. Within a single session, the broker guarantees first-in-first-out handling and hands the whole session to exactly one consumer at a time, so that consumer sees session items strictly in order and no other consumer can interleave with it. Across different sessions, consumers work in parallel. The result is order where order matters, in the session, and scale where it does not, across sessions.

The mental model is parallel ordered lanes rather than one ordered line or one unordered free-for-all. Picture a bank that processes account transactions. All events for account 1001 carry SessionId 1001, all events for account 1002 carry SessionId 1002, and so on. Consumer A locks session 1001 and drains it in order, consumer B locks session 1002 and drains it in order, and the two run at the same time. Account 1001's deposit-then-withdraw sequence can never be reordered, because one consumer owns that session exclusively and reads it FIFO. Yet the system still scales to many accounts at once, because sessions are independent and the consumer fleet spreads across them. The guaranteed FIFO pattern in Service Bus requires sessions; without a SessionId you get the unordered competing-consumers behavior by default.

```csharp
// Producer stamps the SessionId so related items share a lane
var msg = new ServiceBusMessage(payload) { SessionId = accountId };
await sender.SendMessageAsync(msg);

// Session-aware consumer locks one session and reads it FIFO
ServiceBusSessionProcessor processor = client.CreateSessionProcessor(
    "transactions", new ServiceBusSessionProcessorOptions { MaxConcurrentSessions = 8 });
processor.ProcessMessageAsync += async args =>
{
    await ApplyTransaction(args.Message);          // strict order within the session
    await args.CompleteMessageAsync(args.Message);
};
```

Sessions also carry session state, a small store the broker holds per session, which lets a session move safely between consumers in a high-availability fleet. If the consumer holding session 1001 dies, another consumer can accept that session and resume from the stored state rather than from scratch. This is what lets sessions scale without sacrificing the ordering guarantee even as consumers come and go.

### How do I choose a SessionId that scales?

Choose the SessionId as the key whose items must stay ordered relative to each other, and that has many distinct values so sessions spread across consumers. An account ID, an order ID, or a device ID works well. A single constant SessionId serializes everything to one consumer and destroys scale.

The SessionId choice is the same kind of decision as a partition key, and it has the same failure mode. Pick a key with high cardinality and even distribution and the work fans out across the consumer fleet. Pick a low-cardinality key, say a SessionId of "orders" on every item, and you have one giant session that one consumer must drain alone, which is slower than having no sessions at all. The right granularity is the smallest unit within which order is actually required. Bank transactions need order within an account, not across accounts, so the account is the session. An order's lifecycle events need order within that order, so the order ID is the session. Get the grain right and sessions give you ordered, parallel, scalable processing; get it wrong and you have rebuilt a single-threaded bottleneck with extra steps.

Even with sessions, delivery is still at-least-once within the session. A consumer that crashes mid-session has its uncompleted item redelivered, in order, when another consumer accepts the session. So the deposit that was charged but not completed will be redelivered and applied again unless the handler is idempotent. Ordering and idempotency are separate concerns: sessions fix order, they do not fix duplication. You need both.

## Idempotent consumers and at-least-once delivery

Every design above ends at the same place, so it earns its own section. At-least-once delivery means a consumer will sometimes see the same item twice, and the only defense that survives crashes, lock expiries, and retries is a consumer whose second execution has no additional effect. An idempotent consumer is one where processing the same logical unit any number of times produces the same end state as processing it once. Build that, and at-least-once delivery becomes effectively-once side effects, which is the strongest practical guarantee Azure messaging gives you.

There are two layers of defense, and durable systems use both. The first is broker-side: Service Bus duplicate detection, available on standard and premium tiers, drops a resend of an item whose MessageId the broker has already seen within a configurable detection window. If a producer retries a send after an ambiguous network failure, the broker discards the second copy based on MessageId, so the duplicate never reaches a consumer at all. This handles producer-side duplicates cleanly. It does not handle consumer-side redelivery, because that is the broker doing its job, redelivering an item the consumer never completed. Confirm the supported tiers and the maximum detection window against current Service Bus documentation, since tier capabilities and window limits are revised over time.

The second layer is the consumer's own idempotency, and it is the one you can never skip. The standard technique is an idempotency key plus a processed-state store. Each logical unit of work carries a stable, unique key, often the MessageId or a business key like an order ID. Before applying the side effect, the consumer records that key in a store, a Cosmos DB item, a SQL row with a unique constraint, a Redis entry, inside the same transaction as the side effect when possible. On redelivery the consumer finds the key already present and skips the side effect, completing the message without repeating the work.

```csharp
public async Task Handle(ServiceBusReceivedMessage m)
{
    string key = m.MessageId; // stable per logical unit
    // Atomic check-and-set in the processed-state store
    bool firstTime = await store.TryRecordProcessed(key);
    if (!firstTime)
        return;            // already done, redelivery is a no-op
    await ApplySideEffect(m);   // charge, write, send, exactly once in effect
}
```

The subtlety is atomicity. If the consumer records the key and then crashes before applying the side effect, the work is lost; if it applies the side effect and then crashes before recording the key, the work repeats. The durable answer ties the state record and the side effect together so they commit or fail as a unit, which the outbox pattern and a transactional store provide. Where the side effect is itself naturally idempotent, an upsert keyed by order ID, a set operation, a PUT to an object store, you get idempotency for free and the separate key store is unnecessary. The discipline is to ask of every handler: if this runs twice, what breaks? If the honest answer is "nothing," the handler is safe. If the answer names a double charge, a duplicate email, or a doubled balance, the handler is not finished.

### How does idempotency turn at-least-once into effectively once?

Idempotency does not change what the broker delivers; the broker still delivers at-least-once. It changes the effect of a second delivery to nothing. The first execution records its key and performs the side effect; the second finds the key and returns without acting, so the observable outcome matches exactly-once even though delivery is not.

## The claim-check pattern for large payloads

Brokers cap the size of a single item. Service Bus, for instance, enforces a maximum message size that depends on tier, and even where the cap is generous, pushing megabytes of payload through a broker is wasteful: it inflates broker storage, slows throughput, and burns bandwidth on data the broker only needs to route, not to inspect. The claim-check design solves this by separating the bulk from the routing. The producer writes the large payload to durable object storage, Azure Blob Storage, and sends through the broker only a small reference, the claim check, that says where the payload lives. The consumer receives the lightweight reference, fetches the blob, and processes it.

The name is the coat-check metaphor. You hand your heavy coat to the attendant and walk away with a small ticket; later you present the ticket and retrieve the coat. Here the coat is a one-gigabyte video, a large export file, or a fat document, the attendant is Blob Storage, and the ticket is a message carrying the blob URI and perhaps a content hash. The broker moves tickets, which are tiny, fast, and cheap, while the heavy data sits in storage built for exactly that. A queue or topic that would choke on the raw payload handles the references at full speed.

```csharp
// Producer: store the payload, send only the reference
BlobClient blob = container.GetBlobClient($"payloads/{id}");
await blob.UploadAsync(largeStream);
var msg = new ServiceBusMessage(BinaryData.FromObjectAsJson(new {
    blobUri = blob.Uri.ToString(),
    sha256 = hash,
    id
}));
await sender.SendMessageAsync(msg);

// Consumer: read the reference, fetch the payload
var check = args.Message.Body.ToObjectFromJson<ClaimCheck>();
BlobDownloadResult data = await new BlobClient(new Uri(check.blobUri)).DownloadContentAsync();
await Process(data.Content);
```

Claim-check composes with every other design rather than competing with them. You can run competing consumers over a queue of claim checks, fan claim checks out through a topic, or order claim checks within a session. It inherits the ordering property of whatever carrier you put it on, because the reference is just a small item flowing through that carrier. Its duplication property is favorable: the blob is written once and is immutable, identified by a stable name, so a redelivered reference points at the same unchanged data. The consumer fetching the same blob twice reads identical bytes, which makes the fetch half of the work naturally idempotent. The side effect the consumer then performs still needs the usual idempotency treatment, but the large data transfer itself stops being a duplication hazard.

### When is the claim-check pattern worth the extra hop?

Claim-check is worth it when payloads are large enough to strain the broker's size limit, throughput, or cost, typically anything from hundreds of kilobytes upward, or when many subscribers need the same large data and you would otherwise copy it into every subscription. For small messages the extra storage round trip adds latency without benefit.

The trade-off is an added dependency and an extra network hop. The consumer now relies on Blob Storage being reachable and the blob still existing, which introduces lifecycle questions: how long do payloads live, who deletes them, what happens if the reference outlives the blob. Set a retention policy that comfortably exceeds the maximum time an item can sit in the queue plus its dead-letter window, so a slow or dead-lettered reference never points at a deleted blob. For tiny payloads the indirection is pure overhead, so reserve claim-check for genuinely large data and let small items travel inline.

## Message routing and filtering

A topic broadcasts to every subscription, but most subscribers do not want every event. The routing design narrows the broadcast by attaching filters to each subscription so it receives only the subset it cares about. Service Bus supports SQL-style filter rules and correlation filters on subscriptions, evaluated against an item's system properties and application properties. The orders-us subscription takes only events whose region property equals "us"; the high-value subscription takes only events whose amount exceeds a threshold; the audit subscription takes everything with no filter. The publisher remains ignorant of all of it, sending one event to the topic and letting the subscription rules decide who sees it.

```sql
-- SQL filter rule on a subscription
region = 'us' AND tier = 'gold' AND amount > 1000
```

Filtering moves the routing decision out of consumer code and into broker configuration, which is where it belongs. Without filters, every subscriber receives every event and discards the ones it does not want, wasting delivery, compute, and the consumer's attention on items it will drop. With filters, the broker does the selection once, centrally, and each subscriber receives a clean stream of relevant events. This keeps consumers simple and makes the routing visible as configuration you can audit, rather than as scattered if-statements buried in handlers. Correlation filters, which match on exact property equality, are cheaper to evaluate than full SQL filters and suit high-volume routing on a small set of discriminating properties.

### Should routing logic live in filters or in consumer code?

Put coarse, stable routing in subscription filters so the broker discards irrelevant events before they reach a consumer, saving delivery and compute. Keep fine-grained, frequently changing business logic in the consumer, where it is testable and deployable without reconfiguring the broker. The boundary is how often the rule changes and how expensive a wrong delivery is.

Routing interacts with the other properties in predictable ways. A filtered subscription still delivers its matching copies at-least-once, so filtering reduces volume but does not remove the need for idempotency. Ordering within a filtered subscription follows the same rules as any subscription: serial single consumer or sessions for per-key order. The one trap is over-filtering, splitting a topic into so many narrow subscriptions that adding a new event property forces a sweep of filter rules across dozens of subscriptions. Keep the filter surface as small as the routing genuinely requires, and prefer a handful of broad subscriptions a consumer further refines over a sprawl of hyper-specific ones the broker must all evaluate on every send.

## A reference design walked through

Patterns are clearest when assembled into one system, so here is an order-processing pipeline that uses each design in the role it was built for. A storefront accepts an order over HTTP. The web tier does not process the order inline; it validates the request, writes an OrderPlaced event, and returns immediately, which keeps the customer-facing latency low and decouples the checkout from everything that happens next. This is the durable handoff that the whole design rests on.

The OrderPlaced event lands on a Service Bus topic named order-events. Three subscriptions hang off that topic. The fulfillment subscription drives the warehouse and shipping flow. The billing subscription charges the customer. The analytics subscription feeds a reporting pipeline. Each consumes its own copy at its own rate, so a slow analytics run never delays a shipment and a billing retry never blocks fulfillment. That is publish-subscribe doing its job: one event, three independent reactions, added or removed without touching the storefront.

The billing subscription needs order. A single order can emit OrderPlaced, then PaymentAuthorized, then OrderCancelled in quick succession, and applying a cancellation before the authorization it cancels would corrupt the ledger. So billing uses sessions keyed by order ID. Every event for order 7788 carries SessionId 7788, one billing consumer owns that session and applies its events strictly in order, while other billing consumers handle other orders in parallel. Ordering where it matters, scale where it does not.

The fulfillment subscription does not need order; picking and packing tasks are independent, and finishing order 7788's pick before order 7789's is harmless. So fulfillment uses competing consumers: a fleet of warehouse workers reads the fulfillment subscription, races for tasks, and scales on queue depth during a sales peak. The design that would be a bug in billing is the right call in fulfillment, because the ordering requirement differs.

Some orders include a large attached document, a bulk-order spreadsheet or a signed contract. Rather than push that through the broker, the storefront writes it to Blob Storage and the OrderPlaced event carries a claim check. The fulfillment and billing consumers that need the document fetch it by reference; those that do not ignore the field. Claim-check rides on top of the topic without disturbing it.

Underneath all three subscriptions sits the same discipline: every consumer is idempotent. Billing records the payment key before charging, so a redelivered PaymentAuthorized after a crash does not double-charge. Fulfillment records the task key before dispatching a pick, so a redelivered task does not ship twice. Analytics upserts by order ID, so a duplicate event does not double-count revenue. The brokers deliver at-least-once throughout, and the consumers turn that into effectively-once outcomes everywhere it counts. The same skeleton, an event store feeding projections through messaging, is what [CQRS and event sourcing on Azure](/2024/06/03/azure-cqrs-event-sourcing/) formalizes when the events themselves become the system of record.

Telemetry is the one part that does not belong on Service Bus. The storefront and the workers emit a high-volume stream of operational events, page views, latency samples, click traces, far too many and too low-value individually to lock and complete one at a time. That stream goes to Event Hubs, partitioned, where a consumer reads at its own offset and checkpoints its progress. Service Bus carries the business transactions that must not be lost or reordered; Event Hubs carries the firehose of telemetry that is read in bulk and replayed. Using the right broker for each half of the system is itself a design decision, and the next section makes it explicit.

## Choosing Service Bus versus Event Hubs

The two services look adjacent and are built for opposite jobs, and putting a workload on the wrong one is the most expensive mistake in this whole area because it is structural rather than a tunable. Service Bus is a broker for discrete units of work that are individually acknowledged: each item is locked, processed, and completed or dead-lettered, and the per-item lifecycle, sessions, duplicate detection, and transactions all assume that granularity. Event Hubs is a log for high-volume streams: events are appended to partitions, consumers read sequentially by offset and checkpoint their position, and there is no per-event lock or complete. One is a to-do list where each task is checked off; the other is a tape you play and rewind.

The decision rule is throughput and acknowledgement granularity, not topic similarity. If each item is a business transaction that must be processed once, in some defined order, with the option to dead-letter the ones that fail, and the volume is thousands to low millions per day, Service Bus fits. If the data is a continuous stream measured in many thousands to millions of events per second, consumed in bulk, where the consumer tracks a position rather than acknowledging each event, and replay of a window matters more than per-item delivery, Event Hubs fits. Order events, payment events, and command messages are Service Bus work. Clickstream, IoT telemetry, application logs, and metrics are Event Hubs work.

The ordering models differ in a way that decides borderline cases. Service Bus gives strict per-session FIFO and no order without sessions. Event Hubs gives order within a partition and none across partitions, and the partition is chosen by a partition key, so to keep a key's events ordered you route them to one partition exactly as you route a session by SessionId. The parallel is close, but the consumption model is not: Event Hubs consumers process a partition as a stream and cannot selectively dead-letter one poison event without stalling or skipping, while Service Bus consumers handle each item independently and dead-letter the bad ones in isolation. When individual poison-message isolation matters, that points to Service Bus; when raw ingestion volume dominates, that points to Event Hubs. The full three-way decision, including where Event Grid belongs, is laid out in the [Service Bus, Event Hubs, and Event Grid comparison](/2025/05/12/service-bus-vs-event-hubs-vs-grid/), and the streaming internals are in the [Event Hubs engineering guide](/2022/03/28/azure-event-hubs-engineering-guide/).

### Can one system use both brokers at once?

Yes, and mature systems usually do. Service Bus carries the business transactions that demand per-item delivery, ordering, and dead-lettering, while Event Hubs ingests the high-volume telemetry the same system produces. They are complementary tools, not competitors, and the order-processing reference design above runs both side by side without conflict.

## Trade-offs and the failure modes each design must handle

Every async design buys decoupling and scale at the cost of complexity that synchronous code never had to think about. The trade-offs are not reasons to avoid messaging; they are the bills that come due, and a design that has not budgeted for them fails in production in ways that are hard to reproduce. Five failure modes recur across all the designs above, and each has a concrete remedy.

The first is duplicate processing, the through-line of this whole guide. It appears wherever at-least-once delivery meets a non-idempotent handler, which is to say everywhere by default. The order-processing team double-charged customers because their billing handler applied a charge on every delivery, and competing consumers gave the broker more occasions to redeliver. The remedy is the idempotency layer: a processed-state store keyed by a stable identifier, or a naturally idempotent side effect, applied to every consumer regardless of which design it sits in. There is no design that is exempt, and treating idempotency as optional is the single most common root cause of correctness bugs in Azure messaging.

The second is lost ordering, which strikes when a design that scales across consumers is used for items that depend on each other. Competing consumers on dependent work, or competing consumers added to a single topic subscription, both reorder events that needed to stay in sequence. The remedy is sessions keyed by the unit within which order is required, accepting that the ordered unit is also the unit of serialization and therefore the limit on parallelism for that key. The discipline is to ask of every consumer whether its items are independent, and to use sessions exactly when they are not and plain competing consumers when they are.

The third is the poison message, an item that fails every time it is processed, perhaps because it is malformed, references data that no longer exists, or trips a bug. Under at-least-once delivery the broker keeps redelivering it, and a naive consumer keeps failing, locking the same item forever and starving the queue behind it. The remedy is dead-lettering: Service Bus moves an item to its dead-letter queue after a configurable maximum delivery count, where it waits for inspection and replay rather than blocking the live flow. Monitor dead-letter depth as a first-class health signal, because a growing dead-letter queue is the earliest sign that something downstream is broken.

The fourth is unbounded backlog. Async decoupling turns a downstream outage into a growing queue rather than a cascading failure, which is a feature until the queue grows past the broker's capacity or past any tolerable processing delay. A consumer that is permanently slower than its producers will fall behind without bound. The remedy is autoscaling consumers on queue depth so capacity tracks load, alerting on backlog age so a stuck consumer is caught early, and load-leveling expectations so a temporary spike drains in a known time. When the backlog is structural rather than a spike, the answer is more consumers or a faster downstream, which the queue depth makes visible and measurable.

The fifth is the lock-expiry surprise. In PeekLock mode a consumer holds a lock for a finite duration; if processing takes longer than the lock lasts, the lock expires, the broker redelivers the item to another consumer, and now two consumers are processing the same item concurrently, exactly the race the lock was meant to prevent. The remedies are to renew the lock for genuinely long-running work, to keep handlers short and push long work behind a claim-check or a follow-up message, and, as always, to make the handler idempotent so a concurrent reprocess does not corrupt state. Lock expiry is where many duplicate bugs actually originate, and it is easy to miss because it only shows up under the specific timing of slow processing.

### What is the most common async messaging mistake on Azure?

The most common mistake is assuming exactly-once delivery and writing a consumer with no idempotency. Because Azure brokers deliver at-least-once, any crash, lock expiry, or producer retry causes a duplicate, and a non-idempotent handler then double-applies the side effect. The fix is never a broker setting; it is an idempotent consumer.

## When each design fits and when it is overkill

Patterns are tools, and reaching for the wrong one, or for any one when none is needed, is its own failure. The honest counsel is that the simplest design that meets the requirement wins, and complexity must be earned by a named need.

Competing consumers fits when work units are independent and the arrival rate can exceed a single consumer's processing rate. It is overkill when one consumer comfortably keeps up and adds no resilience benefit, in which case a single reader is simpler and preserves natural order for free. It is wrong, not merely unnecessary, when the work units are dependent and order matters, where it silently corrupts sequence.

Publish-subscribe fits when one event genuinely needs several independent reactions that should evolve separately. It is overkill when there is exactly one consumer and will only ever be one, where a plain queue is simpler than a topic with a single subscription. The signal that you need pub-sub is that you keep wanting to add new reactions to an existing event without disturbing the producer; if that never happens, a queue suffices.

Sessions fit when a related sequence must stay ordered while the system still scales across unrelated sequences. They are overkill when items are independent, where they add a serialization constraint and consumer complexity for an ordering guarantee nobody needs, and they actively harm throughput when the SessionId has low cardinality. Use sessions only when you can name the key whose order matters and confirm that key has many distinct values.

Claim-check fits when payloads strain the broker's size limit, throughput, or cost, or when the same large data must reach many subscribers. It is overkill for small messages, where the extra storage round trip adds latency and a lifecycle dependency for no gain. Routing and filtering fit when subscribers want distinct subsets of a broadcast and the routing rules are coarse and stable; they are overkill when every subscriber wants everything, or when the rules change so often that broker reconfiguration becomes a bottleneck and consumer-side selection is simpler.

Idempotency is the exception to all of this. It is never overkill, because at-least-once delivery is always the floor. Even a single consumer on a single queue will occasionally see a duplicate from a lock expiry or a producer retry. There is no async design on Azure where skipping idempotency is the correct simplification.

### When should I avoid async messaging entirely?

Avoid async messaging when the caller genuinely needs the result before it can proceed, such as a synchronous read or a request whose response the user is waiting on inline. Messaging adds latency and complexity that a request-response call avoids. Use it for work that can complete after the caller moves on, not for answers the caller needs now.

## How to evolve the design over time

A messaging design is not set once and frozen; it grows as the system grows, and the patterns are chosen partly because they evolve gracefully. The starting point for most systems is a single queue with one consumer, which is the right amount of structure for a workload that one reader can handle and whose items are independent. This is not a primitive design to be embarrassed by; it is the correct design until a requirement says otherwise.

The first evolution is usually scale: the single consumer falls behind, and you add competing consumers reading the same queue. This is a configuration change, more instances, plus the idempotency you should already have had, not a rearchitecture. The second evolution is fan-out: a second team wants to react to the same events, and you promote the queue to a topic with two subscriptions, leaving the producer's send call almost unchanged. Because pub-sub is additive, each later consumer is a new subscription rather than a change to existing code, which is the property that lets the design absorb growth without churn.

The third evolution is ordering: a subset of the work turns out to be dependent, and you introduce sessions on the affected subscription keyed by the unit of order, while leaving the independent subscriptions on plain competing consumers. The fourth is payload growth: items get large, and you slot in claim-check on the affected flow without disturbing the carrier. Each step is a local change to one part of the design, enabled by having chosen patterns that compose. The system that started as a single queue can become a topic with ordered, scaled, filtered, claim-checked subscriptions feeding both Service Bus and Event Hubs, and at no point did the evolution require a rewrite, because each pattern was added where its specific need arose.

The discipline that makes this evolution safe is the one constant across every step: idempotent consumers from the very first version. A team that builds idempotency in when there is a single queue and one consumer pays a tiny cost then and can scale, fan out, and reorder freely later. A team that skips it because "one consumer never sees duplicates," which is not even true, will hit the double-charge wall the moment they add the second consumer, under production load, in the worst possible circumstances. Build the idempotency layer first and the rest of the evolution is a series of safe, local, additive moves.

### How do I migrate a synchronous call to async messaging safely?

Migrate by introducing the broker behind a facade while keeping the synchronous path live, then routing a slice of traffic through the queue and confirming the idempotent consumer produces identical results. Expand the slice as confidence grows, and remove the synchronous path only when the async one is proven. Never cut over all at once.

## Delivery guarantees in depth

The whole architecture turns on one property, so it repays a careful look at the three delivery guarantees and why Azure lands where it does. At-most-once means each item is delivered zero or one times: no duplicates, but possible loss. At-least-once means each item is delivered one or more times: no loss, but possible duplicates. Exactly-once means each item is delivered precisely one time: no loss and no duplicates, the property everyone wants and almost no distributed broker actually provides end to end.

Azure Service Bus offers the first two as receive modes. ReceiveAndDelete removes an item the moment it is delivered, which gives at-most-once: if the consumer crashes before finishing, the item is already gone and the work is lost. This is acceptable only for data where occasional loss does not matter, low-value telemetry being the textbook case. PeekLock locks the item, lets the consumer process it, and requires an explicit complete, which gives at-least-once: a crash before the complete causes redelivery, so nothing is lost but the work can repeat. Production systems that carry meaningful work choose PeekLock and pay the duplicate tax, because losing a customer's order is worse than processing it twice when the second processing is a harmless no-op.

True exactly-once delivery across a network is impossible in the general case, because the acknowledgement of a delivery can itself be lost, leaving the broker unable to know whether the consumer received the item. The broker's only safe choices are to assume it did not, and redeliver, which is at-least-once, or to assume it did, and risk loss, which is at-most-once. There is no third option at the delivery layer. What systems actually achieve is exactly-once processing, also called effectively-once, by combining at-least-once delivery with idempotent consumers and, optionally, broker-side duplicate detection. The delivery is at-least-once; the effect is once. That distinction is the most important idea in this entire guide, because it tells you to stop searching the Azure portal for an exactly-once toggle and start writing idempotent handlers.

Duplicate detection on Service Bus addresses the producer side of the problem and is worth enabling where the tier supports it. When a producer retries a send after an ambiguous failure, the broker recognizes the repeated MessageId within the detection window and discards the second copy, so a producer's own retries do not become consumer-visible duplicates. With partitioning enabled, the broker uses MessageId together with the partition key to determine uniqueness, and with sessions the partition key and session ID must align. This catches one class of duplicates cleanly, but it cannot catch consumer-side redelivery from a crash or lock expiry, because that is the broker correctly redelivering an uncompleted item. Producer-side duplicate detection and consumer-side idempotency are complementary defenses, and a system that wants effectively-once outcomes uses both. Confirm the tiers that support duplicate detection and the maximum detection window against current documentation, because these are platform values that change.

### Is exactly-once delivery possible on Azure?

Exactly-once delivery is not possible end to end, because a lost acknowledgement leaves the broker unable to know whether delivery succeeded, forcing either redelivery or loss. What is achievable is exactly-once processing: at-least-once delivery combined with an idempotent consumer, so the observable effect is once even though delivery is not. Aim for the effect, not the impossible guarantee.

## Operating async messaging: dead-lettering, retries, and observability

A messaging design that runs cleanly in a demo can still fail in operation, because operation is where poison messages, transient faults, and silent backlogs live. Running the patterns well means treating the broker's operational features as part of the design rather than as afterthoughts bolted on during an incident.

Dead-lettering is the safety valve for items that cannot be processed. Service Bus gives every queue and every subscription an associated dead-letter sub-queue, and an item moves there when it exceeds the maximum delivery count, when it expires, or when a consumer explicitly dead-letters it with a reason. The value of dead-lettering is that it removes a poison item from the live flow so the rest of the queue keeps moving, while preserving the bad item for inspection and replay rather than discarding it. Without dead-lettering, one malformed item under at-least-once delivery loops forever, consuming delivery attempts and blocking healthy work behind it. Set the maximum delivery count deliberately: too low and a transient fault dead-letters work that would have succeeded on the next try, too high and a genuine poison item wastes many attempts before it is quarantined.

Retry with backoff handles the transient fault, the downstream blip that will clear in a moment. The right response to a transient failure is not to dead-letter immediately but to retry, and the right way to retry is with exponential backoff and jitter so a fleet of consumers hitting a struggling downstream does not synchronize into a thundering retry storm. The Service Bus client libraries provide retry policies, and beyond the broker the resilience patterns of retry, circuit breaker, timeout, and bulkhead apply directly to messaging consumers. A circuit breaker that opens when a downstream is clearly down stops the consumer from burning delivery attempts against a dead dependency, letting items wait in the queue, exactly the load-leveling messaging is good at, until the dependency recovers.

Observability is what turns a silent backlog into an actionable alert. The metrics that matter are queue or subscription depth, the age of the oldest item, dead-letter depth, and the rate of completions versus the rate of arrivals. A backlog that grows means consumers are behind and need to scale; a rising oldest-item age means something is stuck even if the depth looks stable; a climbing dead-letter count means items are failing and a code or data problem needs attention. These signals are the difference between catching a degradation in minutes and discovering it when a customer complains hours later. The same diagnostic discipline that the [event-driven architecture guide](/2024/04/22/azure-event-driven-architecture/) applies to the broader design applies here at the level of each queue and subscription: instrument the flow, alert on the leading indicators, and treat the dead-letter queue as a monitored health signal rather than a forgotten corner.

### How do I handle a poison message that fails every time?

Configure a maximum delivery count so the broker dead-letters the item after a set number of failed attempts, removing it from the live flow without losing it. Then inspect the dead-letter queue, fix the underlying cause, and replay the item if appropriate. Monitor dead-letter depth so a rising count alerts you before the backlog spreads.

## Transactions, the outbox, and consistency across the boundary

The hardest correctness problem in messaging is the dual write: a consumer or producer that must update a database and send or complete a message as one atomic act, when the database and the broker are separate systems with no shared transaction. If the database commit succeeds and the send fails, downstream consumers never learn of a change that did happen; if the send succeeds and the database commit fails, consumers act on a change that did not happen. Either way the system's state and its messages disagree, and at-least-once delivery cannot fix a message that was never sent.

Service Bus supports transactions that group multiple messaging operations, sending several items, or receiving and sending, into one atomic unit that commits or rolls back together. This solves the all-messaging case: a consumer can complete one item and send a follow-up item atomically, so it never completes without sending or sends without completing. What broker transactions cannot do is span the broker and an external database, because those are different resource managers without a shared coordinator in the usual Azure setup.

The outbox pattern is the durable answer to the cross-system case. Instead of writing to the database and sending to the broker as two independent acts, the producer writes the business change and an outbox record into the same database transaction, so both commit or neither does. A separate relay process then reads unsent outbox records and publishes them to the broker, marking each as sent once the broker accepts it. If the relay crashes after publishing but before marking, it republishes on restart, which is a duplicate the broker or the idempotent consumer absorbs. The outbox converts the impossible atomic dual write into a reliable eventual one: the database transaction guarantees the change and the intent to publish are consistent, and at-least-once publishing with idempotent consumers guarantees the message eventually arrives and is processed once in effect. This is the same machinery that makes [CQRS and event sourcing on Azure](/2024/06/03/azure-cqrs-event-sourcing/) reliable, where the event store and the projections must never disagree.

Where the side effect is naturally idempotent, an upsert keyed by a business identifier, the consistency story simplifies, because a duplicate apply is harmless and the system tolerates the occasional double publish without any outbox at all. The design choice is therefore: make the side effect idempotent and tolerate at-least-once directly, or, when the side effect cannot be made idempotent, use the outbox to make publishing reliable and a processed-state store to make consumption idempotent. Both roads end at the same destination, an effectively-once outcome built on an at-least-once foundation, which is the only honest guarantee distributed messaging can offer.

### Why can't I just update the database and send the message together?

Because the database and the broker are separate systems with no shared transaction, so one can succeed while the other fails, leaving state and messages inconsistent. The outbox pattern fixes this by writing the change and the message intent in one database transaction, then publishing from the outbox reliably, which a relay retries until the broker accepts it.

## Recurring scenarios engineers report, and the design that fits each

The designs are easier to apply when you see them attached to the concrete situations that keep showing up in production. Each scenario below is a case engineers report repeatedly, paired with the design that resolves it and the property that has to be respected.

A queue is backing up during a sales peak and one consumer cannot keep pace. The fit is competing consumers: run more reader instances against the same queue and autoscale them on depth. The property to respect is independence, because the throughput win is only safe when the items do not depend on one another. If they do, the same scaling move reorders them, and the answer becomes sessions rather than plain competing consumers. The diagnosis question to ask is whether finishing item B before item A would corrupt anything; if not, scale freely.

A sequence of events for the same entity is being applied out of order. A withdrawal posts before the deposit that funds it, or a cancellation lands before the order it cancels. The fit is sessions keyed by the entity, so all of that entity's events flow through one lane that one consumer drains in order, while other entities process in parallel. The property to respect is SessionId cardinality, because a low-cardinality key serializes everything to one consumer and rebuilds the bottleneck you were trying to scale past. The fix is almost always that someone scaled a queue with competing consumers without realizing the items were dependent.

One event needs to trigger several independent reactions, and a new reaction keeps needing to be added without disturbing the others. The fit is publish-subscribe: a topic with a subscription per reaction, each consuming its own copy at its own pace. The property to respect is that each subscription is independently at-least-once, so each subscriber needs its own idempotency scoped to its own side effect. The signal you have outgrown a plain queue is exactly this repeated pressure to add reactions to an existing event.

A payload is too large to push through the broker, or the same large data must reach many subscribers. The fit is claim-check: write the bulk to Blob Storage and send a small reference through the broker. The property to respect is the blob lifecycle, because the reference must never outlive the data it points at; set retention to exceed the maximum queue plus dead-letter dwell time. The misdiagnosis here is treating a broker size-limit error as a reason to split the payload into many small items, which multiplies coordination problems instead of removing them.

Duplicate side effects appear under load, a customer charged twice, an email sent twice, a counter doubled. The fit is the idempotent consumer with a processed-state store, applied regardless of which other design is in play. The property to respect is atomicity between recording the key and performing the side effect, which the outbox pattern or a naturally idempotent upsert provides. The root cause is always the same: a handler that assumed exactly-once delivery met the reality of at-least-once.

A choice between Service Bus and Event Hubs is being made on surface similarity rather than on the workload. The fit is to decide on acknowledgement granularity and volume: per-item business transactions go to Service Bus, high-volume streams read in bulk go to Event Hubs. The property to respect is that the consumption models differ, per-item lock and complete versus offset and checkpoint, so the wrong choice is structural and expensive to undo. The misdiagnosis is putting a stream on Service Bus, where per-item locking cannot keep up, or putting per-item transactional work on Event Hubs, where individual poison-event isolation is not available.

### Why did adding consumers cause double-charging?

Adding consumers did not cause double-charging by itself; it exposed a handler that was never idempotent. More competing consumers meant more crashes and lock expiries mid-processing, and under at-least-once delivery each of those redelivered an item to another consumer that charged the card again. The fix is an idempotent billing handler, not fewer consumers.

## Anti-patterns and common misdiagnoses

Knowing the designs is only half the skill; recognizing their misuse is the other half, because the failures in this area are subtle and intermittent rather than loud and immediate. Several anti-patterns recur often enough to name.

The first is hunting for an exactly-once setting. Engineers new to Azure messaging spend hours searching the portal and the documentation for a toggle that makes delivery exactly-once, and there is none, because the guarantee is impossible end to end. The time is better spent writing an idempotent handler, which achieves the effect the toggle would promise. The tell is a design document that says "enable exactly-once delivery" as a requirement; rewrite it to say "idempotent consumer" and the design becomes buildable.

The second is scaling first and discovering ordering later. A team adds competing consumers to fix a backlog, ships it, and only finds the ordering requirement when a customer-visible corruption appears weeks later. The corruption is intermittent because it depends on the exact timing of which consumer finished first, which makes it maddening to reproduce. The remedy is to ask the ordering question before scaling, not after, and to default to sessions for anything that touches a single entity's state over time.

The third is the giant session. Reaching for sessions to fix an ordering problem, then keying every item with the same SessionId, produces strict global order at the cost of single-consumer throughput, which is slower than having used no sessions at all and accepting the original problem. The session key must be the narrowest unit within which order is required and must have high cardinality, or sessions become a serialization bottleneck wearing the costume of a scaling pattern.

The fourth is the forgotten dead-letter queue. A system runs for months, dead-lettered items quietly accumulate, and nobody notices until a downstream report comes up short or storage fills. Dead-lettering without monitoring is only half the safety valve; the dead-letter depth and the reasons attached to dead-lettered items must be watched and acted on, or the quarantine becomes a silent data-loss channel.

The fifth is pushing fat payloads through the broker because it technically fits under the size limit. Just because a payload is under the cap does not mean it belongs inline; large items inflate broker storage, slow throughput, and raise cost, and the broker is built to route references, not to warehouse blobs. When payloads are routinely large, claim-check is not optional polish, it is the design.

The sixth is treating idempotency as a feature to add later. Idempotency added under incident pressure, after the double-charge has happened, is far more expensive and error-prone than idempotency built in from the first version. The cheapest moment to make a handler idempotent is when it is first written, against a single queue, before any scale or fan-out exists. Every design in this guide assumes that layer is present, and the systems that fail are the ones that deferred it.

### How do I know if my consumer is genuinely idempotent?

Ask what happens if the exact same logical unit runs through the handler twice with no other change. If the end state is identical, the handler is idempotent. If running it again charges, sends, increments, or writes a second time, it is not, and at-least-once delivery will eventually expose that. Test it directly by replaying a completed item.

## Latency, throughput, and the cost of decoupling

Decoupling is not free, and a design that ignores its costs ships a system that is correct but slow, or correct but expensive. Three dimensions deserve explicit budgeting: the latency the broker adds, the throughput each design can sustain, and the cost model that bills for the volume.

Latency is the first surprise for teams coming from synchronous calls. A request that once returned in a few milliseconds now records its intent and returns, while the actual work happens later when a consumer reads the item. For the storefront checkout that is a feature, the customer gets a fast acknowledgement and the fulfillment happens behind the scenes, but for any path where the caller needs the result before proceeding, the added hop through the broker is pure cost. The honest guidance is to reserve messaging for work that can complete after the caller moves on and to keep synchronous request-response for answers the caller needs now. Within the messaging path itself, latency comes from the polling interval, the lock duration, the prefetch setting, and the consumer's own processing time, each of which is tunable. Prefetch, for instance, pulls a batch of items to the consumer ahead of time, which raises throughput at the cost of holding more locks and using more memory, so it trades latency smoothing against the blast radius of a consumer crash.

Throughput differs sharply by design and by service, and matching the workload to the ceiling avoids the structural mistake. A Service Bus queue with competing consumers scales throughput with the consumer count until a downstream resource saturates, which makes it ideal for independent work that parallelizes cleanly. Sessions cap per-session throughput at one consumer's rate, because a session is owned exclusively while it is processed, so a workload with a few high-volume sessions will bottleneck on those sessions no matter how many consumers stand idle. The remedy is to choose a session key fine enough that the hot sessions split into many smaller ones. Event Hubs scales throughput with partitions and throughput units, sustaining volumes that Service Bus is not built for, which is exactly why the telemetry firehose belongs there and the ordered business transactions belong on Service Bus. Knowing which ceiling you are approaching tells you which lever to pull: more consumers, a finer session key, more partitions, or a different service entirely.

Cost tracks the dimensions the platform bills for, and these change, so treat any specific figure as a value to confirm against current Azure pricing rather than a constant. Broadly, Service Bus bills by tier and by operation or messaging-unit volume, Event Hubs bills by throughput units or processing units and ingress volume, Queue Storage bills by storage and transactions, and Event Grid bills by operation. The design choices have cost consequences that are easy to miss. Pushing large payloads through a broker inflates the billed message size and storage, which is one more reason claim-check pays off when payloads are large. A topic with many subscriptions multiplies the delivered copies, each of which counts, so a fan-out to a dozen subscribers costs more than a single queue carrying the same events once. Duplicate detection and sessions are premium-leaning features that may require a higher tier. None of these costs are reasons to avoid the right design; they are reasons to choose the right design deliberately, knowing that Queue Storage for a simple buffer is cheaper than Service Bus, and that the enterprise features you pay for on Service Bus are worth it precisely when the workload needs ordering, fan-out, or deduplication. Attribute spend to each flow rather than to the namespace as a whole, because a single noisy topic with wide fan-out can dominate the bill while looking innocuous next to the others, and visibility at the per-flow level is what lets you decide whether a costly fan-out is earning its keep or quietly multiplying delivered copies that nobody reads.

### Does async messaging always reduce latency?

No. Async messaging improves the latency the caller experiences when the work can finish after the caller moves on, because the caller returns as soon as the item is recorded. It does not reduce, and usually increases, the end-to-end latency of the work itself, since the item now waits to be polled, locked, and processed. Use it to decouple, not to speed up work the caller is waiting on.

## The verdict

Async messaging on Azure is not a collection of independent tricks; it is a small vocabulary of designs that share one foundation and one discipline. The foundation is at-least-once delivery, the floor that every Azure broker provides and that no portal setting raises to true exactly-once. The discipline is idempotent handling, the consumer-side defense that turns at-least-once delivery into effectively-once side effects. Competing consumers scales independent work, publish-subscribe broadcasts one event to many reactions, sessions preserve order within a key while scaling across keys, claim-check moves large payloads through a small reference, and routing narrows a broadcast to the subset each subscriber wants. Each solves a specific coordination problem, and each is correct only when paired with the idempotency the delivery floor demands. That pairing is the pattern-plus-idempotency rule, and it is the difference between a design that works in a demo and one that survives production traffic without double-charging a customer.

Choose the broker before the design: Service Bus for discrete business transactions that need per-item delivery, ordering, and dead-lettering, Event Hubs for high-volume streams read in bulk, Event Grid for reactive notifications, and Queue Storage for a plain deep buffer. Choose the design for the coordination shape: competing consumers for independent work, sessions for ordered work, topics for fan-out, claim-check for bulk, filters for selective delivery. Then, under whichever you chose, build the idempotency layer first, because it is the one component that is never optional and the one that lets the rest of the design grow safely from a single queue to a full event-driven system. An engineer who internalizes that order of operations, broker, then design, then idempotency, will reason from the delivery guarantee outward and ship messaging that is reliable by construction rather than by luck.

To put these designs into practice, [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), where you can stand up a Service Bus namespace, create a topic with filtered subscriptions, send and complete items under PeekLock, watch a session preserve order while competing consumers scale alongside it, and force a redelivery to confirm your idempotent handler does what the pattern-plus-idempotency rule requires. Reading the designs builds the model; running them is what makes the model stick.

## Frequently Asked Questions

### Q: What are async messaging patterns on Azure?

They are repeatable arrangements of producers, a broker, and consumers that solve specific coordination problems without synchronous coupling. The canonical ones are competing consumers for scaling independent work across receivers, publish-subscribe for delivering one event to many handlers, sessions for keeping a related sequence ordered while scaling across unrelated sequences, claim-check for moving large payloads by reference, and message routing for delivering only a relevant subset to each subscriber. On Azure each maps to a configuration of Service Bus, Event Hubs, Event Grid, or Queue Storage. The common thread is that every one of them rides on at-least-once delivery, so each must be paired with an idempotent consumer to be reliable. That pairing, design plus idempotency, is the rule that separates a design that works in a demo from one that survives production traffic without double-applying side effects.

### Q: How does the competing-consumers pattern work?

Several consumer instances read from the same queue and race for each item; the broker hands any given item to exactly one of them, that instance processes and acknowledges it, and total throughput scales with the number of instances until a downstream resource becomes the limit. On Azure you do not enable a special mode. You point multiple workers at one Service Bus queue or Queue Storage queue, and the broker's locking ensures two workers do not process the same item concurrently under normal operation. Scale the worker count up to drain a backlog and down to save cost. The catch is that racing consumers lose the queue's natural order and increase the chances of a crash mid-processing, so the items must be independent and the handlers must be idempotent for the design to stay correct.

### Q: How do publish-subscribe topics differ from queues?

A queue delivers each item to exactly one of the consumers reading it, so the readers share one stream of work. A topic delivers a copy of each item to every subscription attached to it, so one event becomes as many independent copies as there are matching subscriptions. Each subscription behaves like its own virtual queue with its own cursor, consumed independently and at its own pace. The practical effect is that a queue spreads work across workers while a topic broadcasts an event to many separate reactions. Topics are additive: you add a new reaction by adding a subscription, which existing publishers and subscribers never notice. Use a queue when one logical consumer processes the work, and a topic when several independent consumers each need their own copy of the same event.

### Q: What is a Service Bus session and when do I need one?

A session groups related items by a SessionId you stamp on each one, and the broker hands an entire session to exactly one consumer at a time, which processes it strictly first-in-first-out. Different sessions are processed in parallel by different consumers. You need sessions when a sequence of items for the same entity must stay ordered, an account's transactions or an order's lifecycle events, while the overall system still scales across many entities. Without a SessionId, a queue read by multiple consumers gives no ordering guarantee. The key choice matters: the SessionId should be the entity within which order is required and should have many distinct values, so sessions spread across the consumer fleet. A single constant SessionId serializes everything to one consumer and removes the scaling you wanted.

### Q: What does PeekLock mode do compared to ReceiveAndDelete?

PeekLock delivers an item to a consumer while holding it under a lock that hides it from other consumers, and the consumer must explicitly complete the item after processing. If the consumer crashes before completing, the lock expires and the broker redelivers the item, giving at-least-once delivery with no loss but possible duplicates. ReceiveAndDelete removes the item the instant it is delivered, giving at-most-once delivery with lower latency but silent loss if the consumer dies before finishing. Production work that must not be lost uses PeekLock and pays for redelivery with idempotent handling, because processing an order twice harmlessly beats losing it. ReceiveAndDelete suits only data where occasional loss is acceptable, such as low-value telemetry. The choice between them is the choice between tolerating duplicates and tolerating loss, and most business workloads tolerate duplicates far more easily.

### Q: What is the claim-check pattern?

Claim-check separates a large payload from its routing. Rather than push megabytes through a broker that caps message size and is built to route rather than warehouse data, the producer writes the payload to Azure Blob Storage and sends through the broker only a small reference, the claim check, carrying the blob location and perhaps a content hash. The consumer receives the lightweight reference and fetches the blob to process it. The broker moves tiny references at full speed while the heavy data sits in storage designed for it. The pattern composes with the others, riding on a queue, a topic, or a session and inheriting that carrier's ordering. Its duplication property is favorable because the blob is written once and immutable, so a redelivered reference points at identical bytes. Set a blob retention policy that exceeds the maximum queue and dead-letter dwell time so a reference never outlives its data.

### Q: How does Service Bus duplicate detection work?

Duplicate detection is a broker-side feature on the standard and premium tiers that drops a resend of an item whose MessageId the broker has already seen within a configurable detection window. When a producer retries a send after an ambiguous network failure, the broker recognizes the repeated MessageId and discards the second copy, so the duplicate never reaches a consumer. With partitioning enabled, the broker uses MessageId together with the partition key to determine uniqueness, and with sessions the partition key and session ID must align. This addresses producer-side duplicates cleanly. It does not address consumer-side redelivery from a crash or lock expiry, because that is the broker correctly redelivering an uncompleted item. Use duplicate detection alongside consumer idempotency, not instead of it. Confirm the supported tiers and the maximum detection window against current documentation, since these platform values are revised over time.

### Q: What is a dead-letter queue and when does a message land there?

Every Service Bus queue and subscription has an associated dead-letter sub-queue that holds items that cannot be delivered or processed. An item moves there when it exceeds the maximum delivery count after repeated failed processing, when it expires past its time-to-live, or when a consumer explicitly dead-letters it with a reason. The value is that a poison item is removed from the live flow so healthy work keeps moving, while the bad item is preserved for inspection and replay rather than discarded. Without dead-lettering, one malformed item under at-least-once delivery loops forever, consuming delivery attempts and blocking the queue behind it. Monitor dead-letter depth and the attached reasons as a first-class health signal, because a rising dead-letter count is the earliest sign that a code or data problem is causing items to fail.

### Q: What is the outbox pattern and why is it needed?

The outbox pattern solves the dual-write problem, where a producer must update a database and send a message as one atomic act but the two systems share no transaction. Instead of writing to the database and sending to the broker independently, the producer writes the business change and an outbox record in the same database transaction, so both commit or neither does. A separate relay then reads unsent outbox records and publishes them to the broker, marking each sent once accepted. If the relay crashes after publishing but before marking, it republishes on restart, which a duplicate-tolerant consumer absorbs. The outbox converts an impossible atomic dual write into a reliable eventual one: the transaction guarantees the change and the intent to publish stay consistent, and at-least-once publishing with idempotent consumers guarantees the message eventually arrives and is processed once in effect.

### Q: How should I configure retries for a Service Bus consumer?

Distinguish transient faults from poison messages. A transient fault, a brief downstream blip, should be retried with exponential backoff and jitter so a fleet of consumers does not synchronize into a retry storm against a recovering dependency. The Service Bus client libraries provide retry policies for this, and a circuit breaker in front of a clearly dead dependency stops consumers from burning delivery attempts while items wait safely in the queue. A poison message that fails every time should not be retried indefinitely; configure a maximum delivery count so the broker dead-letters it after a set number of attempts, removing it from the live flow without losing it. Set the count deliberately, because too low dead-letters work a retry would have saved and too high wastes many attempts on a genuine poison item before quarantining it.

### Q: What is message filtering on a Service Bus subscription?

Filtering attaches rules to a subscription so it receives only the subset of a topic's events it cares about, rather than every event. Service Bus supports SQL-style filter rules and correlation filters evaluated against an item's system and application properties. A subscription might take only events whose region property equals a value, or whose amount exceeds a threshold, while an audit subscription with no filter takes everything. This moves the routing decision out of consumer code and into broker configuration, so each subscriber receives a clean stream of relevant events and the routing is visible as auditable configuration rather than scattered if-statements. Correlation filters that match exact property equality are cheaper to evaluate than full SQL filters and suit high-volume routing on a few discriminating properties. Avoid over-filtering into many narrow subscriptions, which forces a sweep of rule changes whenever a new property is added.

### Q: How many competing consumers can read from one queue?

There is no small fixed cap you will hit in practice; you scale consumers until a downstream resource, a database, an external API, or the broker's throughput on your tier, becomes the bottleneck rather than the consumer count. The right number is the one that keeps the queue depth stable under peak load without overwhelming downstream dependencies, and the practical approach is to autoscale on queue depth so the fleet sizes itself to the incoming rate. More consumers drain a backlog faster but also multiply the chances of a crash or lock expiry mid-processing, which under at-least-once delivery produces more duplicate deliveries, so the idempotency layer must hold regardless of fleet size. Watch the completion rate against the arrival rate: if completions keep pace, you have enough consumers, and if the backlog grows, add more or speed up the downstream.

### Q: Should I use Service Bus topics or Event Grid for publish-subscribe?

Use Service Bus topics when subscribers need a durable buffer they drain on their own schedule and when you want enterprise features like sessions, transactions, or dead-lettering on each subscription. Subscribers poll their subscription, which behaves like a virtual queue, so a slow subscriber accumulates a backlog without affecting others. Use Event Grid when the reaction is a lightweight push notification to a handler expected to be online, such as an HTTP webhook or an Azure service handler, with Event Grid's own retry and dead-letter behavior. Topics suit buffered, durable, enterprise fan-out where consumers process at their own pace; Event Grid suits reactive, push-based event routing where the subscriber acts immediately. The deciding question is whether subscribers need to buffer and pull at their own rate, which favors topics, or react to a push as it happens, which favors Event Grid.

### Q: When should I use Queue Storage instead of Service Bus?

Use Queue Storage when the requirement is a plain, durable, very deep buffer at low cost and the consumer already handles ordering and duplicates on its own. Queue Storage offers basic enqueue and dequeue with a visibility timeout and very high capacity, but it lacks sessions, topics and subscriptions, and broker-side duplicate detection. When the workload names ordering of related items, fan-out to multiple independent consumers, or deduplication, Queue Storage cannot provide it and Service Bus is the right choice. A useful rule is to start with Queue Storage for simple, independent work where cost and capacity dominate, and move to Service Bus the moment the requirements list grows to include sessions, topics, transactions, or duplicate detection. Choosing Queue Storage for work that genuinely needs those features means rebuilding them yourself, which is rarely worth it.

### Q: How do I keep a message backlog from growing without bound?

A backlog grows when consumers are persistently slower than producers, which async decoupling turns into a queue rather than a cascading failure, useful until the queue exceeds capacity or any tolerable delay. The first defense is autoscaling consumers on queue depth so capacity tracks load automatically, scaling out during spikes and back in when the queue is shallow. The second is alerting on the age of the oldest item, not just the depth, because a stuck consumer shows a rising oldest-item age even when depth looks stable. The third is recognizing structural backlog, where the consumers are persistently too slow for sustained load, which calls for more consumers or a faster downstream rather than more buffering. The queue depth and oldest-item age make all of this measurable, turning a silent degradation into an actionable signal you can catch in minutes.

### Q: What is auto-forwarding in Service Bus and when is it useful?

Auto-forwarding chains a queue or subscription to another queue or topic within the same namespace, so the broker automatically moves items from the source to the target transactionally. It is useful for fan-in and routing topologies: many subscriptions can auto-forward into a single aggregation queue that one consumer drains, or a subscription can forward into a topic for a second stage of fan-out. It keeps the routing in broker configuration rather than in a relay process you have to write and operate, and because the moves are transactional, items are not lost in transit between entities. Use it to build multi-stage pipelines and aggregation points without intermediate consumer code. As with every other arrangement, the items still travel at-least-once, so the eventual consumer at the end of the chain must remain idempotent regardless of how many forwarding hops the item passed through.

### Q: How do I choose a partition key for ordered Event Hubs streams?

Event Hubs preserves order within a partition and gives no ordering across partitions, so to keep a logical key's events ordered you route them all to one partition by setting a consistent partition key, exactly as you route related items to one session by SessionId in Service Bus. Choose a partition key with high cardinality and even distribution, a device ID, a user ID, or an account ID, so events spread evenly across partitions and no single partition becomes a hot spot that limits throughput. A low-cardinality key concentrates traffic on a few partitions and creates an imbalance that caps the stream's effective rate. The principle mirrors the SessionId choice: the key is the smallest unit within which order is actually required, with enough distinct values that the workload parallelizes across partitions rather than serializing onto one.
