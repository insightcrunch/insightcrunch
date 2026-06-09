---
layout: post
title: "Idempotency and Exactly-Once Patterns on Azure"
page_title: "Idempotency Patterns on Azure: Idempotency Keys, the Outbox Pattern, Deduplication, and Exactly-Once Processing Explained"
date: 2024-07-15
categories: ["Technology"]
tags: ["Azure", "Idempotency", "Architecture", "Messaging", "Cloud Computing"]
excerpt: "Idempotency on Azure turns at-least-once delivery into safe, effectively-once processing using idempotency keys, a processed-state store, and the outbox."
image: "/assets/images/blog/blog-24.webp"
reading_time: 61
author: "david-thornton"
last_updated: 2024-07-15
lang: en
---
A payment service charged a customer twice on a Friday afternoon. Nothing crashed, no exception was logged, and the code passed every unit test. The message that triggered the charge was delivered to the handler two times, the handler ran cleanly both times, and the customer saw two line items on a statement. This is the failure that idempotency on Azure exists to prevent, and it is the most common production surprise for teams who assume the messaging platform delivers each event once. It does not. Azure messaging is built on at-least-once delivery, which means a consumer can and will see the same message more than once, and the responsibility for making that safe sits in the consumer, not in the broker.

The gap between expecting exactly-once delivery and getting at-least-once delivery is where double charges, duplicate emails, doubled inventory decrements, and replayed state transitions come from. Closing that gap is not a feature you toggle on. It is a small set of patterns you apply deliberately: an idempotency key that names a unit of work, a processed-state store that records what has already happened, deduplication that rejects a repeat before it does damage, and the outbox pattern that keeps your database and your published events from drifting apart. Put together, these turn an at-least-once channel into processing that behaves as though each message landed exactly once.

![Idempotency and exactly-once patterns on Azure](/assets/images/blog/blog-24.webp)

## The effectively-once rule that most exactly-once expectations miss

The single idea this article is built around is what we will call the effectively-once rule: Azure gives you at-least-once delivery, so exactly-once is achieved in the consumer through an idempotency key and a processed-state store, never by the platform alone. Teams reach for a setting called "exactly-once" and assume the problem is solved at the broker. The reality is narrower than the name suggests, and the part that actually protects your data lives in code you write.

Why does the platform not just deliver everything once? Because true exactly-once delivery across an unreliable network is impossible to guarantee end to end without cooperation from the receiver. A broker can send a message and wait for an acknowledgment. If the acknowledgment is lost in transit, the broker cannot tell whether the consumer processed the message and the ack went missing, or whether the consumer never received it at all. Faced with that ambiguity, a system that values not losing messages will resend. Resending is what makes delivery at-least-once, and it is the correct trade for most workloads, because a lost payment instruction is worse than a duplicated one you can detect and discard.

So the platform chooses to never lose a message, and it pushes the deduplication responsibility to you. That is not a deficiency. It is the only honest division of labor available, and once you accept it, the design becomes clear. You stop trying to make delivery exactly-once and start making your processing idempotent, so that whether a message arrives once or five times, the observable effect on your system is identical. An operation is idempotent when applying it more than once produces the same result as applying it a single time. A charge that checks "have I already charged for this order" before charging is idempotent. A charge that blindly debits an account is not.

### Why does at-least-once delivery require idempotency?

At-least-once delivery means the broker guarantees a message will be processed one or more times, never zero times, but it cannot promise exactly one. Because retries and redeliveries are part of normal operation rather than rare faults, every handler that produces a side effect must assume it will run on the same message again, and idempotency is the property that makes the repeat harmless.

This is worth sitting with, because the instinct is to treat a duplicate as a bug to be eliminated rather than a condition to be handled. Consider the concrete sequence that produces a duplicate even when nothing is broken. A producer sends a message to a queue. The broker stores it and returns an acknowledgment. On the network path back, the acknowledgment is dropped. The producer, having waited and seen no confirmation, follows its retry policy and sends the message again. Now two copies sit in the queue. The producer did exactly what a reliable producer should do, the broker did exactly what a durable broker should do, and yet a consumer will be handed the same logical message twice.

A second, independent source of duplication happens entirely on the consumer side, and it survives any broker-level deduplication. A consumer receives a message, runs the business logic, commits a database row, and then crashes before it can tell the broker the message is complete. The broker, having never received completion, returns the message to the queue and redelivers it. The work was done once, but the broker has no way to know that, so it sends the message again and a second consumer instance processes it. The only thing that can prevent a doubled side effect here is the consumer recognizing that it has already handled this message. The broker cannot help, because from its point of view the message was never finished.

These two paths, the lost-ack resend and the post-commit crash redelivery, are why idempotency is mandatory rather than optional in any system that does real work in response to messages. The first can be reduced by broker features. The second can only be solved in your code.

## The Azure services that deliver at-least-once and what each gives you

Idempotency is a consumer-side discipline, but the exact shape of the duplicates you face depends on which Azure service is carrying your messages. The pattern is the same across all of them; the knobs differ. Understanding what each service offers keeps you from either over-engineering where the platform already helps or under-engineering where it does not.

Azure Service Bus is the broker most teams reach for when ordering, transactions, and delivery guarantees matter. It delivers at-least-once by default, and it offers a feature called duplicate detection that catches a specific class of duplicates: repeated sends of the same message identified by the same MessageId, within a configurable time window. When duplicate detection is enabled, the broker keeps a history of message identifiers it has seen, and any send with a MessageId already in that window is silently discarded before it lands in the queue. Microsoft describes this as guaranteeing exactly-once delivery over a user-defined span of time, and the phrasing matters: the guarantee is scoped to the window and scoped to the sender retry case. Duplicate detection is available on the Standard and Premium tiers and cannot be added to a queue or topic after it is created, so it is a design-time decision.

There is a sharp limit to what Service Bus duplicate detection covers, and missing it is the most common reason teams believe they are protected when they are not. Duplicate detection compares only the MessageId. If you send the same logical event with two different identifiers, both are delivered. More importantly, duplicate detection does nothing about the post-commit crash redelivery described earlier, because in that case the broker is redelivering a message it already accepted exactly once, not receiving a duplicate send. The official guidance is explicit that broker-level deduplication is not a substitute for an idempotent consumer; you combine the two, letting the broker catch most sender retries and letting your consumer catch the redeliveries it cannot see.

Azure Event Hubs sits at the other end of the spectrum. It is a high-throughput streaming ingestion service that delivers at-least-once, and it does not offer a broker-side deduplication switch comparable to Service Bus. Consumers read from partitions and track their position with a checkpoint. When a consumer fails and another picks up the partition, processing resumes from the last committed checkpoint, which means events between that checkpoint and the failure are read again. Duplicate processing in Event Hubs is therefore routine by design, and the only defense is idempotent handling keyed on something stable in the event. For the design behind these channels, the article on [event-driven architecture on Azure](/2024/04/22/azure-event-driven-architecture/) walks through how Event Grid, Event Hubs, and Service Bus differ in their delivery semantics and where each fits.

Azure Event Grid delivers events at-least-once as well, retrying delivery to a subscriber until it receives a success response, with retries spread over time and a dead-letter destination for events that never succeed. A subscriber that is slow to acknowledge, or that acknowledges after doing the work but before the response reaches Event Grid, will receive the event again. The shape is identical to the Service Bus and Event Hubs cases: the platform errs toward delivering rather than losing, and the subscriber must be safe to call twice.

### Does Azure Service Bus duplicate detection give me exactly-once?

No, not on its own. Duplicate detection rejects repeated sends carrying the same MessageId within the configured window, which covers producer retries after a lost acknowledgment, but it cannot prevent the redelivery that happens when a consumer processes a message and crashes before completing it. End-to-end exactly-once still requires an idempotent consumer.

The distinction is easiest to hold if you separate the two halves of a message's life. The send half is producer to broker. Duplicate detection protects this half: if the producer resends because it never saw an ack, the broker discards the repeat. The receive half is broker to consumer. Duplicate detection does not protect this half at all, because the broker is doing its job correctly when it redelivers a message that was never completed. A consumer that locks a message, does the work, commits, and then dies during the network round trip that would have told the broker "done" leaves the broker no choice but to redeliver. Your consumer must therefore record that it finished the work in a place that survives the crash, and check that record before acting. That record is the processed-state store, and it is the second half of the effectively-once rule. The deeper treatment of competing consumers, sessions, and ordering lives in the guide to [async messaging patterns on Azure](/2024/06/24/azure-async-messaging-patterns/).

## The InsightCrunch idempotency toolkit

To make the pattern concrete and reusable, here is the InsightCrunch idempotency toolkit: the four mechanisms that, applied together, turn at-least-once delivery into effectively-once processing. Each one prevents a duplicate at a different point, and the value of naming them is that you can audit a handler against the list and see exactly which protection is missing.

| Mechanism | What it is | Where it prevents a duplicate side effect | Primary Azure home |
| --- | --- | --- | --- |
| Idempotency key | A stable identifier for a unit of work, supplied by the caller or derived deterministically from the message | At the entry to the handler, by naming the work so a repeat can be recognized | The message body, a header, or an HTTP `Idempotency-Key` |
| Processed-state store | A durable record of which keys have already been handled, and optionally the result that was produced | After the work runs, by letting the next attempt see the key was finished and skip the side effect | Azure SQL, Cosmos DB, or Table storage |
| Deduplication | Rejecting a repeat before it does work, either at the broker or at the store | Before the side effect, by discarding a known repeat early | Service Bus duplicate detection plus the store check |
| Outbox pattern | Writing the event to publish into the same transaction as the state change, then relaying it separately | Across the database-and-publish boundary, by removing the dual-write that loses or duplicates events | An outbox table in Azure SQL or Cosmos DB |

The toolkit is deliberately small. You do not need a distributed transaction coordinator, a saga framework, or a custom broker to be safe. You need a way to name work, a place to remember what you did, a gate that turns away repeats, and a discipline for keeping your data store and your event stream consistent. The rest of this article walks each one through a reference design, names the trade-offs, and shows where each mechanism earns its keep and where it is overkill.

## The idempotency key, defined plainly

An idempotency key is a stable identifier that names a unit of work so that two attempts at the same work can be recognized as the same. It is the foundation of every other mechanism, because deduplication and the processed-state store both need something to deduplicate on. Choose the key badly and the whole structure leaks; choose it well and the rest follows.

The key must be stable across retries and unique per logical operation. Stable means the same logical request carries the same key every time it is retried, so a resend after a lost acknowledgment presents the identifier the system has already seen. Unique per operation means two genuinely different requests never collide on the same key, because a collision would cause the system to treat a new operation as a duplicate and silently drop it. Those two requirements pull in opposite directions, and getting the balance right is the real work.

There are three common sources for the key, and the right one depends on who has the authority to define what "the same operation" means. The cleanest source is the client. In an HTTP API, the caller generates a key, often a GUID, and sends it in an `Idempotency-Key` header. The server records the key with the result, and any retry carrying the same header gets the stored result rather than a second execution. This is how payment APIs protect against double charges, and it works because the client is the only party that knows whether a second request is a deliberate new charge or a retry of a previous one.

```http
POST /v1/charges HTTP/1.1
Host: api.example.com
Content-Type: application/json
Idempotency-Key: 8f14e45f-ea35-4c1e-9b2a-2d6c7e9f0a31

{
  "order_id": "ORD-10241",
  "amount_cents": 4999,
  "currency": "usd"
}
```

When the client cannot supply a key, derive one deterministically from the content of the operation. If every charge is tied to exactly one order and an order can only be charged once, the order identifier is a natural key. The rule is that the derived key must come from fields that are identical across retries and different across distinct operations. Deriving a key from a timestamp fails, because the retry has a different timestamp. Deriving it from the order identifier plus the operation type usually succeeds, because both are stable and together they pin down the work.

The third source is the broker's own message identifier. Service Bus exposes a MessageId, Event Hubs events can carry an identifier in their properties, and Event Grid events have an `id` field. Using the message identifier as the idempotency key is convenient and works for redeliveries of the same message, but it has a trap: if the same logical event is published twice with two different message identifiers, the keys differ and the duplicate slips through. The message identifier protects against redelivery of one message, not against double publication of one fact. When double publication is possible, key on a business identifier the producer controls, not on the transport's identifier.

### Which idempotency key should I choose?

Choose a key that is stable across every retry of the same operation and distinct across every different operation. A client-supplied GUID in an `Idempotency-Key` header is best when the caller controls retries; a business identifier such as an order ID derived from the message is best for asynchronous events; the broker's message identifier is a fallback that only protects against redelivery of that exact message.

The failure modes of a bad key are instructive. A key that is too coarse, such as keying only on the customer identifier when a customer can place many orders, causes false duplicates: the second legitimate order is dropped because the system thinks it has already processed work for that customer. A key that is too fine, such as keying on a value that changes between retries, causes missed duplicates: the retry presents a new key and the side effect runs again. The discipline is to ask, for any two messages, whether they represent the same business fact, and to make the key equal exactly when the answer is yes. When you cannot decide from the data alone, push the decision to the client and let it supply the key, because the client is usually the only party with the context to know.

## The processed-state store, where idempotency actually lives

The processed-state store is the durable record of which idempotency keys have been handled. It is what lets a consumer that crashed and is reprocessing a message recognize that the work is already done. Without it, the idempotency key is just a label with nowhere to be remembered. With it, the key becomes a lookup: before doing the side effect, check whether this key is in the store, and if it is, skip the work and return the recorded result.

The mechanics matter because the check and the work and the recording must be arranged so there is no window in which a crash leaves the system in a state that allows a double effect. The naive version, check the store, then do the work, then write to the store, has a gap. If the consumer crashes between doing the work and writing to the store, the redelivery finds no record and does the work again. Closing that gap is the heart of getting the store right, and there are two solid approaches.

The first approach makes the side effect and the store write part of the same transaction. If the work you are protecting is itself a database write, you record the idempotency key in the same database transaction as the business change. Either both commit or neither does. On redelivery, you attempt to insert the key first; a unique constraint on the key column makes the second insert fail, and you treat that failure as the signal that the work is already done. This is the strongest form, because the database's own atomicity guarantees the key and the effect move together.

```sql
-- Processed-state table keyed by idempotency key
CREATE TABLE ProcessedMessages (
    IdempotencyKey  VARCHAR(64)   NOT NULL PRIMARY KEY,
    ProcessedAtUtc  DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
    ResultPayload   NVARCHAR(MAX) NULL
);

-- Handler: insert-first, then do work, all in one transaction
BEGIN TRANSACTION;

    INSERT INTO ProcessedMessages (IdempotencyKey)
    VALUES (@idempotencyKey);
    -- If this row already exists, the INSERT fails on the primary key,
    -- the transaction rolls back, and the caller treats it as a duplicate.

    UPDATE Accounts
    SET Balance = Balance - @amountCents
    WHERE AccountId = @accountId;

COMMIT TRANSACTION;
```

The second approach is needed when the side effect is not a database write you control, for example calling an external payment processor or sending an email. You cannot put a third-party HTTP call inside your database transaction. Here you split the record into two states. Before the side effect, you write a row marking the key as in progress. After the side effect succeeds, you update the row to completed and store the result. On redelivery, if you find a completed row, you skip and return the stored result. If you find an in-progress row, you know a previous attempt started but you cannot be sure it finished, and you must reconcile, which usually means querying the external system using the same idempotency key to ask whether the operation completed. This is why the idempotency key should be passed to the downstream system too: it lets you ask the question after a crash.

Choosing the store is mostly about access pattern and scale. Azure SQL is the natural choice when the protected work is already an Azure SQL transaction, because you get the key insert and the business change in one atomic commit. Cosmos DB fits high-throughput, globally distributed handlers, and its per-item optimistic concurrency with etags gives you the conditional write you need; the trade is that Cosmos consistency level affects whether a read immediately after a write sees the latest value, so design the check against the consistency you have configured. Azure Table storage is the cheapest option for simple key existence checks and works well when the result you need to store is small or not needed at all.

### Where should I store processed-message state?

Store it wherever the protected side effect already commits, so the key and the effect move atomically. If the handler writes to Azure SQL, put the processed-state row in the same database and the same transaction. If the handler is high-throughput and distributed, use Cosmos DB with a conditional write keyed on the idempotency key. Use Table storage when you only need a cheap existence check and no stored result.

A practical refinement is to store not just the key but the result of the operation. When a retry arrives for a completed key, returning the stored result rather than a generic "already processed" message lets the caller behave identically whether it is the first call or the tenth. A payment API that returns the original charge confirmation on every retry of the same idempotency key gives the client a consistent answer and removes the need for the client to reason about duplicates at all. Storing the result also bounds the store's growth, because you can age out old keys once you are confident no further retries can arrive, typically after a window longer than your longest retry horizon.

## The outbox pattern and the dual-write problem it solves

The outbox pattern solves a problem that idempotency keys alone cannot touch: the dual-write inconsistency between your database and your message broker. It is the mechanism that keeps a state change and the event announcing that change from drifting apart, and it is the piece teams most often leave out, because the failure it prevents is invisible until it happens.

The dual-write problem appears the moment a handler needs to do two things that must both happen or neither: change state in a database and publish an event about that change. The obvious code writes to the database, then publishes to the broker. Consider what happens if the process crashes between the two. The database commit succeeded, so the state changed, but the event was never published, so every downstream system that should react to the change never hears about it. An order is marked paid in the database, but the fulfillment service never receives the "order paid" event, and the customer's goods never ship. The reverse ordering is no better: publish first, then write to the database, and a crash in between produces an event for a state change that never committed, so downstream systems act on a fact that is not true.

The reason this cannot be fixed by careful ordering is that there is no transaction spanning the database and the broker. They are two separate systems with two separate commits, and any point between them is a window where a crash leaves them inconsistent. You could reach for a distributed transaction across both, but distributed transactions are slow, fragile, and not supported across most cloud database and broker combinations, so they are the wrong tool for almost every workload.

The outbox pattern removes the dual write by making the publish part of the database transaction. Instead of publishing to the broker directly, the handler writes the event into an outbox table in the same database, inside the same transaction as the state change. Now there is a single commit: either the state change and the outbox row both persist, or neither does. The event can never be lost relative to the state change, because they share one atomic operation.

```sql
CREATE TABLE Outbox (
    Id            BIGINT IDENTITY(1,1) PRIMARY KEY,
    OccurredAtUtc DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
    EventType     VARCHAR(128)  NOT NULL,
    Payload       NVARCHAR(MAX) NOT NULL,
    Published     BIT           NOT NULL DEFAULT 0,
    PublishedAtUtc DATETIME2    NULL
);

BEGIN TRANSACTION;

    UPDATE Orders
    SET Status = 'Paid'
    WHERE OrderId = @orderId;

    INSERT INTO Outbox (EventType, Payload)
    VALUES ('OrderPaid', @orderPaidJson);

COMMIT TRANSACTION;
```

A separate relay process then reads unpublished rows from the outbox and publishes them to the broker, marking each as published once the broker acknowledges. This relay is where at-least-once delivery reappears, and where idempotency closes the loop. If the relay publishes a row and crashes before marking it published, it will publish that row again on restart. The event is therefore delivered at-least-once to the broker, which is exactly the condition the consumer's idempotency key and processed-state store are built to handle. The outbox does not eliminate duplicates; it eliminates loss, and it hands the duplicate problem to the part of your system already equipped to solve it.

### How does the outbox pattern prevent lost events?

The outbox pattern writes the event into an outbox table in the same database transaction as the state change, so the two commit atomically and an event can never be lost relative to the change it describes. A separate relay reads the table and publishes the events to the broker afterward, retrying until each publish succeeds, which makes delivery at-least-once and leaves duplicate handling to the consumer.

The relay can be built two ways. The simpler is polling: a background worker, an Azure Function on a timer, or a hosted service queries the outbox for unpublished rows on an interval, publishes them, and marks them done. Polling is easy to reason about and easy to operate, and the only cost is a small latency between commit and publish equal to the polling interval. The more advanced approach reads the database's change feed or transaction log directly, so events flow as soon as they commit with no polling delay; Cosmos DB's change feed is well suited to this, turning every committed document into a stream the relay consumes. The change-feed approach has lower latency and avoids the load of repeated polling queries, at the cost of more moving parts. Most teams start with polling and move to the change feed only when latency or query load justifies it. The outbox pairs naturally with event sourcing, where the stored events are themselves the source of truth; the relationship is explored in the article on [CQRS and event sourcing on Azure](/2024/06/03/azure-cqrs-event-sourcing/).

## A reference design walked end to end

The mechanisms are clearer assembled into one flow. Here is a reference design for an order-payment handler that consumes a message from Service Bus, charges a payment processor, marks the order paid, and publishes an "order paid" event, all idempotently. Every step earns its place by closing a specific window where a duplicate could cause harm.

The producer publishes an `OrderSubmitted` message to a Service Bus queue with duplicate detection enabled and a MessageId derived from the order identifier. Duplicate detection on the queue catches the easy case: if the producer retries the send after a lost acknowledgment, the broker discards the repeat within the detection window. That handles producer-side duplicates without any consumer code, which is exactly the division of labor the effectively-once rule prescribes.

The consumer receives the message and extracts an idempotency key. The key here is the order identifier, because an order can be paid exactly once and the order identifier is stable across every redelivery of the message. The consumer opens a database transaction and attempts to insert the order identifier into the processed-state table. If the insert succeeds, this is the first time the work is being done, and the handler proceeds. If the insert fails on the primary key constraint, the work has already been done, and the handler completes the message without charging anything, because charging again is exactly what idempotency exists to prevent.

```csharp
public async Task HandleAsync(ServiceBusReceivedMessage message)
{
    string idempotencyKey = message.ApplicationProperties["orderId"].ToString();

    // 1. Check the processed-state store first.
    var existing = await _store.TryGetAsync(idempotencyKey);
    if (existing is { Status: "completed" })
    {
        // Already done. Return the recorded result and complete the message.
        await _receiver.CompleteMessageAsync(message);
        return;
    }

    // 2. Mark in-progress so a crash mid-flight is recoverable.
    await _store.MarkInProgressAsync(idempotencyKey);

    // 3. Perform the external side effect, passing the same key downstream.
    var charge = await _payments.ChargeAsync(
        idempotencyKey: idempotencyKey,
        amountCents: 4999,
        currency: "usd");

    // 4. Commit the state change and the completion atomically.
    using (var tx = _db.BeginTransaction())
    {
        await _orders.MarkPaidAsync(idempotencyKey, tx);
        await _outbox.AddAsync("OrderPaid", BuildPayload(charge), tx);
        await _store.MarkCompletedAsync(idempotencyKey, charge.Id, tx);
        await tx.CommitAsync();
    }

    // 5. Acknowledge the message only after the commit succeeds.
    await _receiver.CompleteMessageAsync(message);
}
```

The external charge is the part you cannot wrap in a database transaction, so the idempotency key travels to the payment processor as well. Payment processors expose an idempotency key precisely for this reason: a charge request carrying a key the processor has already seen returns the original charge result instead of creating a second one. This is the same pattern applied one layer down, and it is why the key must be passed through rather than kept local. If the consumer crashes after the processor charged but before the local transaction committed, the redelivery finds an in-progress record, re-sends the charge with the same key, and the processor returns the existing charge rather than billing twice. The local transaction then commits, the message completes, and the system is consistent.

The state change, the outbox insert, and the processed-state completion all commit in one transaction. This is the crucial atomic step. After it commits, the order is paid, the "order paid" event is durably queued in the outbox, and the processed-state store records the key as completed with the charge result. None of these can exist without the others, because they share one commit. The message is acknowledged only after that commit succeeds, so if the consumer dies before acknowledging, the broker redelivers, the redelivery sees the completed record, and it simply acknowledges without redoing anything.

Finally, the outbox relay publishes the `OrderPaid` event to its own topic, where the fulfillment service subscribes. The fulfillment consumer is itself idempotent, keyed on the order identifier, because the relay delivers at-least-once and may publish the event more than once if it crashes between publishing and marking the row done. The chain is idempotent at every link, which is what makes the whole flow effectively-once even though every individual channel is only at-least-once. Retrying these external calls safely is its own discipline, covered in the article on [retry and circuit breaker patterns on Azure](/2024/05/13/azure-retry-circuit-breaker/), and the two patterns are designed to be used together: retries make transient faults heal, and idempotency makes those retries safe.

### How do idempotency and retries work together?

Retries and idempotency are complementary halves of resilience. A retry policy resends a request that failed transiently, which is what keeps a momentary fault from becoming a permanent failure, but every retry is a potential duplicate. Idempotency makes those duplicates harmless, so you can retry aggressively without fear of doubling a side effect. Use the same idempotency key on every retry of the same operation so the receiver recognizes the repeat.

The pairing is what makes aggressive retrying safe. Without idempotency, a retry policy is a liability: each retry risks a second charge, a second email, a second inventory decrement, so teams tune retries down to avoid duplicates and accept more failures as a result. With idempotency, the calculus flips. Because a repeat is harmless, you can retry as many times as the situation warrants, with backoff and jitter to avoid hammering a struggling dependency, knowing the worst case is wasted work rather than corrupted state. The idempotency key must remain constant across the retries; generating a fresh key per attempt would defeat the entire mechanism, because each attempt would look like new work. This is the most common implementation mistake, and it is silent, because the code looks correct and only doubles effects under the exact conditions that idempotency was meant to handle.

## Making real side effects safe under retry

The reference design covers the structure. The harder part in practice is the specific side effects, because each kind of effect has its own way of resisting idempotency. The pattern is always the same, name the work and remember it, but the place you remember it and the way you reconcile after a crash differ by effect.

### Why was a payment charged twice and how do I prevent it?

A payment is charged twice when the handler debits without first checking whether this exact operation already ran, so a redelivered or retried message triggers a second debit. Prevent it by deriving an idempotency key from the order, passing that key to the payment processor, and recording the completed charge in a processed-state store so any repeat returns the original charge instead of creating a new one.

The double charge is the canonical idempotency failure, and it is worth tracing precisely because the fix generalizes. The naive handler receives a message and calls the payment processor. When the message is redelivered, whether from a producer resend, a consumer crash, or an Event Hubs checkpoint replay, the handler calls the processor again, and the customer is billed twice. The processor did nothing wrong; it received two charge requests and honored both. The fix has two layers. First, the handler checks the processed-state store for the order's idempotency key before charging, and skips if the key is completed. Second, and this is the belt to the store's suspenders, the charge request itself carries the idempotency key to the processor, so even if the local check is bypassed by a race between two consumer instances, the processor recognizes the repeat and returns the original charge. Defense at both layers matters because the local store and the external processor can briefly disagree during a crash, and the only value that ties them together is the shared key.

Sending an email is deceptively similar and quietly different. An email provider usually does not offer an idempotency key, so you cannot ask the provider to deduplicate for you. The work must be guarded entirely on your side. Before sending, record an in-progress marker keyed on the logical email, the recipient plus the message type plus the triggering entity, for instance. After the send succeeds, mark it completed. On redelivery, a completed marker means skip. The awkward case is a crash after the provider accepted the email but before you recorded completion: you have an in-progress marker and no way to ask the provider whether it sent, because the provider has no concept of your key. Here you must choose a policy. For a transactional email like a receipt, sending a possible duplicate is usually acceptable, so you re-send and accept that the customer might rarely see two receipts. For a high-stakes email, you suppress on in-progress and alert an operator to reconcile manually. The lesson is that idempotency for effects you do not control is a matter of bounding the damage, not eliminating it, and the bound you choose should match the cost of a duplicate.

An inventory decrement shows a third shape. Decrementing stock is not naturally idempotent, because subtracting one twice subtracts two. The fix is to make the operation set-based rather than delta-based where possible, or to guard the delta with the processed-state key. A reservation model helps: instead of decrementing a counter, you insert a reservation row keyed on the order, and a unique constraint on the order identifier makes the second reservation insert fail. The available stock is then computed from the reservations rather than mutated directly, which turns a non-idempotent subtraction into an idempotent insert. This is the same move as the processed-state insert, applied to the business data directly, and it is often cleaner than bolting a separate idempotency table onto an operation that can be expressed idempotently in the first place.

### How does an idempotency key deduplicate a retried request?

An idempotency key deduplicates by giving the receiver a stable name for the operation, which it looks up before acting. On the first request, the receiver records the key with its result and performs the work. On any retried request carrying the same key, the receiver finds the recorded key, skips the work, and returns the stored result, so the side effect happens once no matter how many times the request arrives.

The recording and the lookup must be tight enough that two requests racing with the same key cannot both pass the check. This is where the unique constraint shines: rather than reading the store, deciding, and then writing, which has a race between the read and the write, you write first and let the database's uniqueness enforcement decide the winner. Whichever request's insert lands first does the work; the other's insert fails and it treats the failure as "already handled." The database becomes the arbiter, and because the constraint check is atomic, there is no window for both to proceed. This insert-first discipline is the difference between a deduplication scheme that works under concurrency and one that works only in tests where requests arrive politely one at a time.

## The trade-offs and the failure modes the pattern must handle

Idempotency is not free, and pretending it is leads to designs that are correct but slow, or fast but subtly wrong. The honest accounting names what each mechanism costs and which failures it still leaves open.

The processed-state store adds a write and often a read to every operation. For a high-throughput handler, that is a meaningful tax: the store becomes a dependency on the hot path, and its latency and availability now gate your handler's. The mitigation is to put the store close to the work, ideally in the same database so the key write rides along with the business transaction at no extra round trip. When the store must be separate, choose one whose latency you can tolerate and whose availability matches the handler's, because an unavailable store means you must either block or risk a duplicate, and neither is comfortable.

The store also grows, and unbounded growth is a slow failure. Every processed key is a row, and a busy system accumulates them quickly. The fix is to expire keys after a retention window longer than the longest possible retry horizon. If no retry can arrive more than seven days after the original, keys older than seven days can be deleted, because any message carrying them is so stale it should be treated as new or dead-lettered. Cosmos DB's time-to-live makes this automatic; in Azure SQL you run a scheduled cleanup. Choosing the window too short reopens the duplicate window; choosing it too long wastes storage. Size it to your retry and redelivery horizons with margin.

The outbox pattern adds latency between the state change and the event's arrival downstream, equal to the relay's polling interval or change-feed lag. For most workflows this is acceptable, measured in seconds, but for latency-sensitive flows it is a real cost, and the change-feed relay rather than polling is the answer. The outbox also requires the relay to be operated: it is another process that can fall behind, fail, or double-publish, and it needs monitoring on its lag and its unpublished-row backlog. A growing backlog of unpublished outbox rows is the signal that the relay has stalled, and it should page someone, because every unpublished row is an event the rest of the system has not yet heard.

The deepest failure mode is the one idempotency cannot fully close: the gap between an external side effect and your record of it. When you call a system you do not control and crash before recording the outcome, you are left uncertain, and certainty can only be recovered by asking the external system, which is only possible if it accepted your idempotency key. Systems that do not accept a key, like most email providers, leave a residual window where you must choose between a possible duplicate and a possible omission. Naming this gap honestly is better than pretending a pattern closes it, because the choice of which way to fail is a business decision, not a technical one, and it should be made deliberately per side effect.

### When is idempotency overkill?

Idempotency is overkill when the operation is already naturally idempotent or when a duplicate causes no harm. Setting a field to a fixed value, deleting a record by identifier, or writing a value that does not depend on its previous value are all safe to repeat without any extra machinery. Reserve the toolkit for operations with side effects that compound on repetition, such as charges, sends, and increments.

The instinct after learning the pattern is to apply it everywhere, and that instinct should be resisted, because the machinery has a cost and many operations do not need it. An operation that sets a status to "paid" is idempotent by nature: setting it twice leaves it "paid," exactly as setting it once does. A delete by primary key is idempotent: deleting an already-deleted row is a no-op. A write that replaces a value wholesale, rather than adjusting it relative to its current value, is idempotent. For these, adding an idempotency key and a processed-state store buys nothing and slows the hot path. The discipline is to ask, before reaching for the toolkit, whether repeating this exact operation actually causes harm. If the answer is no, the operation is already safe, and the simplest correct design is to let the redelivery happen and do nothing special. Idempotency machinery is for the operations where repetition compounds: money moved, messages sent, counters changed, resources allocated. Spend the complexity there and nowhere else.

## When the pattern fits and how to evolve it

The pattern fits any system where a message or request can trigger a side effect that matters and where the transport delivers at-least-once, which on Azure is every messaging transport. That is broad, but the depth you apply should scale with the cost of a duplicate. A system that sends marketing emails can tolerate a rare duplicate and might need only a light processed-state check. A system that moves money needs the full toolkit, the shared key passed to the processor, and a reconciliation path for the crash window. Match the rigor to the stakes rather than applying the heaviest version everywhere.

A sensible evolution path starts simple and adds protection as the cost of a duplicate rises. The first version of a handler can rely on the operation being naturally idempotent where it is, and add a processed-state check only for the operations that are not. As the system grows and more handlers publish events, the dual-write problem appears, and that is the moment to introduce the outbox, beginning with a polling relay because it is the easiest to operate. When latency on the outbox becomes a constraint, move the relay to a change feed. When throughput on the processed-state store becomes a constraint, move it from a shared database to one sized for the load, or to Cosmos DB with its higher write ceiling. Each step is driven by a measured constraint rather than anticipation, which keeps the system from carrying machinery it does not yet need.

The pattern also evolves in how broadly you push the idempotency key. Early on, the key lives in one handler. As the architecture matures, the same key flows through the whole chain, from the originating request, through every broker hop, into every downstream call, so that the entire path can recognize a repeat of the same logical operation end to end. A correlation identifier that is also the idempotency key turns your tracing and your deduplication into the same mechanism, and it makes diagnosing a duplicate far easier, because you can follow one identifier through every log and every store. This is the mature state: one stable name for a unit of work, understood by every component it touches, used both to deduplicate and to trace.

You can practice building each of these pieces, an idempotency key, a processed-state store, an outbox relay, and a deliberate replay to confirm the handler is safe, in a sandbox rather than in production. The hands-on way to internalize the pattern is to [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), where you can wire a Service Bus queue to a consumer, force a redelivery, and watch the processed-state store turn a duplicate into a no-op. Reproducing the double charge once, and then watching the idempotent version refuse to charge twice, teaches the pattern more durably than any description.

## How idempotency interacts with ordering and sessions

Idempotency and ordering are separate guarantees that people often conflate, and getting them straight prevents a class of subtle bugs. Idempotency makes a repeated message harmless. Ordering makes messages arrive in a defined sequence. A system can need one, the other, both, or neither, and the mechanisms that provide each are different. Confusing them leads to designs that deduplicate correctly but process out of order, or that preserve order but still double a side effect.

Service Bus provides ordering through sessions. A session groups related messages by a session identifier and delivers them to a single consumer in the order they were enqueued, which is what you need when the sequence matters, such as applying account transactions in the order they occurred. Sessions do not provide idempotency. A session can redeliver a message after a consumer crash exactly as a non-session queue can, so a session-ordered handler still needs an idempotency key and a processed-state store. The two compose cleanly: the session gives you order, the key gives you safety against repeats, and a handler that needs both applies both. What you must not do is assume that because a session preserves order it also prevents duplicates, because it does not.

There is a real interaction to handle when ordering and idempotency meet. If a message is redelivered within an ordered session, the handler must skip it without disturbing the position of the messages that follow. Because the session delivers in order and the handler recognizes the redelivered message as already processed, it completes that message and moves to the next, preserving the sequence. The processed-state check sits cleanly inside the ordered flow: it does not reorder anything, it only turns a repeat into a no-op, and the ordering guarantee is untouched. The mental model is two independent filters on the same stream, one for sequence and one for repetition, and they do not interfere.

### Do I still need idempotency if I use Service Bus sessions for ordering?

Yes. Sessions guarantee that related messages are delivered in order to one consumer, but they do not prevent a message from being redelivered after a consumer crash, so a session-ordered handler can still see the same message twice. Idempotency and ordering are independent properties: use sessions for sequence and an idempotency key with a processed-state store for safety against repeats, and apply both when a handler needs both.

The ordering case also surfaces a question about the idempotency key's granularity. In an ordered session where each message advances a state machine, the key cannot be the session identifier alone, because the session carries many messages and they are distinct operations. The key must identify the individual message within the session, often a sequence number or a per-message identifier, so that each step is deduplicated independently. Keying too coarsely on the session would cause the second message in the session to be treated as a duplicate of the first, which is exactly the false-duplicate failure described earlier, now hiding inside an ordered flow where it is harder to spot. The rule holds: the key names a unit of work, and in an ordered session each message is its own unit of work.

## Dead-lettering, poison messages, and the limits of replay

At-least-once delivery has a dark corner: a message that fails repeatedly. If a consumer keeps failing to process a message, the broker keeps redelivering it, and without a backstop the message cycles forever, blocking the queue and burning compute. This is the poison message, and the broker's answer is the dead-letter queue, a separate holding area where a message is moved after it has been delivered more than a configured number of times. Dead-lettering interacts with idempotency in ways worth making explicit, because a poison message and a duplicate are different problems that can masquerade as each other.

A message can become poison for two very different reasons, and idempotency is relevant to one of them. The first reason is a genuine defect in the message or the handler: the payload is malformed, a referenced entity does not exist, or the handler has a bug on that path. No amount of redelivery fixes this, and dead-lettering is the correct outcome, moving the message aside for inspection rather than letting it block the queue. The second reason is a transient fault that happens to recur, such as a downstream dependency being briefly unavailable on each attempt. Here the message is not poison at all; it would succeed if retried later. Distinguishing these is an operational skill, and the delivery count plus the dead-letter reason are the signals that tell them apart.

Idempotency matters because a message that fails partway through can leave a side effect behind before it fails, and the redelivery must not repeat that side effect even as it retries the part that failed. Consider a handler that charges a payment, then writes to a database that is briefly unavailable. The charge succeeded, the database write failed, and the message will be redelivered. Without idempotency, the redelivery charges again before reaching the database write. With idempotency, the redelivery finds the charge's key already recorded, skips the charge, and proceeds straight to the database write, which now succeeds. The processed-state store turns a partially completed handler into one that resumes from where it failed rather than restarting from the top, which is what makes retrying a partially failed message safe. This is the deeper value of recording each side effect's completion separately rather than only recording that the whole handler finished.

When a message does land in the dead-letter queue, replaying it later is itself an at-least-once operation, because the replay re-injects the message into the main queue and the consumer processes it as a new delivery. The idempotency key carries through, so a replayed message whose side effects already partially completed is handled correctly: the completed steps are skipped and only the failed step runs. This is why the key must be derived from the business operation and not from anything tied to a single delivery attempt, because the replay is a new delivery of the same logical operation and must present the same key. A key bound to the delivery attempt would change on replay and cause the completed side effects to run again, defeating the recovery the dead-letter replay is meant to enable.

### What happens to idempotency when a message is dead-lettered and replayed?

The idempotency key persists across the dead-letter and the replay, so a replayed message is recognized as the same logical operation it was before. Side effects that completed on earlier attempts are skipped via the processed-state store, and only the steps that failed are retried. This requires the key to be derived from the business operation rather than from a single delivery attempt, because the replay is a fresh delivery of the same work and must present the same key to be deduplicated correctly.

## Idempotency at the HTTP boundary

Much of this article concerns asynchronous messaging, but the same discipline applies at the synchronous HTTP boundary, and it is where many readers first meet idempotency through payment APIs. An HTTP request that creates a resource or moves money is exposed to the same at-least-once reality, not from a broker but from the client's own retry behavior and from network failures that leave the client unsure whether its request succeeded. A client that sends a charge request, times out waiting for the response, and retries has produced exactly the duplicate that idempotency must absorb.

The HTTP convention is an `Idempotency-Key` header carrying a client-generated unique value, usually a GUID, scoped to a single logical operation. The server records the key on first receipt, performs the operation, and stores the full response. On any retry carrying the same key, the server returns the stored response without re-executing, so the client sees an identical answer whether it is the first attempt or the fifth, and the operation runs once. This is the same idempotency-key-plus-processed-state-store pattern, with the store now keyed on the header value and the stored result being the HTTP response itself.

The subtle parts of the HTTP version are worth naming. The key's scope matters: a key should be valid for a bounded time, after which it expires and a request reusing it is treated as new, which prevents the store from growing without bound and stops an old key from blocking a genuinely new operation. The server must also handle the in-progress case, where a retry arrives while the first request is still executing; returning a status that tells the client to wait, rather than starting a second execution, is the correct behavior, and it requires the same in-progress marker used for asynchronous handlers. Finally, the key must cover the request body: if a client reuses a key with a different body, the server should reject the mismatch rather than silently returning the old result, because the client has made an error that hiding would compound. These refinements turn a simple header into a contract the client can rely on for safe retries.

```http
POST /v1/transfers HTTP/1.1
Host: api.example.com
Idempotency-Key: 3f29c1a8-0b2d-4e77-9a13-7c6f5e4d2b10
Content-Type: application/json

{ "from": "acct_001", "to": "acct_002", "amount_cents": 25000 }

HTTP/1.1 200 OK
Idempotent-Replayed: true
Content-Type: application/json

{ "transfer_id": "trf_77af", "status": "settled" }
```

The HTTP boundary and the messaging boundary are the same problem with different transports, and treating them the same way keeps a system coherent. A request enters over HTTP with a client idempotency key, the handler records that key, does its work, writes an event to the outbox, and the event flows asynchronously to consumers that are themselves idempotent on a key derived from the same operation. The one stable identifier threads through synchronous and asynchronous hops alike, and at every hop the rule is identical: name the work, check whether it is done, do it once. The transport changes; the discipline does not.

## A second worked example: the order-to-fulfillment fan-out

The first reference design covered a single handler. A more realistic system fans an event out to several consumers, and seeing idempotency hold across a fan-out shows why every link must be idempotent independently. Consider an order that, once paid, must trigger fulfillment, send a confirmation email, update a loyalty balance, and notify an analytics pipeline. One `OrderPaid` event drives four side effects across four consumers, and at-least-once delivery means each consumer can see the event more than once, independently of the others.

The publishing side uses the outbox, so the `OrderPaid` event is written in the same transaction that marks the order paid, and the relay publishes it to a Service Bus topic with four subscriptions. The relay is at-least-once, so it may publish the event twice if it crashes mid-publish, and the topic fans each published event to all four subscriptions. From the consumers' point of view, the event can arrive more than once for two independent reasons: the relay double-published, or the consumer itself crashed and the broker redelivered. Both are absorbed the same way.

Each of the four consumers carries its own processed-state store, keyed on the order identifier plus its own consumer name, so the fulfillment consumer's record of having processed order ORD-10241 is separate from the email consumer's record of the same order. This separation matters because the consumers fail independently. If the email consumer crashes and replays while the fulfillment consumer has already finished, only the email side effect is at risk of repetition, and only the email consumer's store is consulted to prevent it. A shared store keyed only on the order identifier would be wrong here, because it could not distinguish "fulfillment is done" from "email is done," and a single record would either over-suppress, skipping a side effect that had not run, or under-suppress, allowing one that had. The key must therefore name both the operation and the consumer for a fan-out, which is the natural extension of "the key names a unit of work" to a setting where one event is four units of work.

```csharp
// Per-consumer idempotency key in a fan-out:
// the order plus the consumer's own identity.
string idempotencyKey = $"{orderId}:{ConsumerName}";

if (await _store.IsCompletedAsync(idempotencyKey))
{
    await _receiver.CompleteMessageAsync(message);
    return; // This consumer already handled this order.
}

await DoSideEffectAsync(orderId);          // fulfill, email, credit, or notify
await _store.MarkCompletedAsync(idempotencyKey);
await _receiver.CompleteMessageAsync(message);
```

The loyalty-balance update in this fan-out deserves a note, because it is the non-idempotent operation among the four. Crediting points is an increment, and incrementing twice credits twice, so it cannot rely on the operation being naturally safe the way marking an order paid is. The consumer guards it with the processed-state key exactly as the payment charge was guarded: record the key, credit once, and on any repeat find the key and skip. The analytics notification, by contrast, may be a case where a duplicate is harmless, because the pipeline deduplicates downstream or because a double-counted event is acceptable for the metric in question, and there the team may choose to skip the idempotency machinery deliberately. The fan-out shows the toolkit applied with judgment: full protection where repetition compounds, lighter or no protection where a duplicate does no harm, and the decision made consumer by consumer rather than uniformly. The broader design of fanning events to many consumers, and choosing topics over queues for it, is covered in the article on [event-driven architecture on Azure](/2024/04/22/azure-event-driven-architecture/).

## Consistency, concurrency, and the store's correctness guarantees

The processed-state store is only as trustworthy as the consistency it gives you, and a store that returns a stale answer to "has this key been processed" reopens the duplicate window it was built to close. The correctness of the whole pattern rests on a single property: that the check for a key and the recording of a key are serialized so that two attempts cannot both conclude the work has not been done. How you get that property depends on the store.

Azure SQL gives it to you through transactions and constraints with no special configuration. A unique constraint on the key column means the database itself serializes competing inserts, and the isolation level of the transaction ensures the check and the business change see a consistent view. This is the strongest and simplest guarantee, and it is the reason to colocate the processed-state row with the business data whenever the protected work is a SQL write. You get the serialization for free from the database you were already using, and the atomic commit ties the key to the effect without any distributed coordination.

Cosmos DB requires more thought because its consistency is configurable, and the level you choose changes whether a read immediately after a write observes that write. Under strong consistency, a read always sees the latest committed write, so a key check immediately after a key write is reliable, at the cost of higher latency and reduced availability during partition events. Under the weaker default of session consistency, reads within the same session see their own writes, which is sufficient when the same consumer instance does both the write and the check, but can mislead when a different instance performs the check, because it may not yet see the other instance's write. For idempotency under concurrency, the safer technique in Cosmos DB is not to read-then-write at all but to perform a conditional create with the key as the item identifier: the create fails if the item already exists, and that failure is the atomic signal of a duplicate, independent of read consistency. Relying on the conditional write rather than a prior read sidesteps the consistency question entirely, which is why it is the recommended approach.

### How does optimistic concurrency keep idempotency correct?

Optimistic concurrency keeps idempotency correct by letting the store reject a write that races with another, rather than allowing both. In Cosmos DB, an etag captures the item's version, and a conditional write succeeds only if the etag still matches, so two consumers updating the same key cannot both win. Combined with a conditional create keyed on the idempotency key, this makes the first writer the processor and forces the second to observe the existing record and skip, with no dependence on read timing.

The concurrency story extends to the business effect itself, not just the key. When two consumer instances race on the same operation, the atomic key insert decides which one proceeds, but the losing instance must still behave correctly: it has to recognize that it lost, refrain from the side effect, and complete its message so the broker does not redeliver to it again. The losing path is as important as the winning path, and a common bug is to handle the unique-constraint failure as an error to be retried rather than as the normal signal that another instance is handling the work. Treating the constraint violation as success, not failure, is what lets the loser exit cleanly. The store does not just record what happened; it arbitrates who gets to make it happen, and the handler must read that arbitration correctly on both sides.

## Monitoring and proving idempotency in production

A pattern you cannot observe is a pattern you cannot trust, and idempotency is especially prone to silent success and silent failure. When it works, nothing visible happens: a duplicate arrives and is quietly skipped, which produces no error and no alert. When it fails, the symptom is a doubled side effect that may not surface until a customer complains. Making idempotency observable means instrumenting the skips and the gaps so the pattern's health is visible before a duplicate reaches a customer.

The first signal to emit is the deduplication itself. Every time the processed-state store turns a message into a no-op, that event should be counted and logged with the idempotency key, so the rate of duplicates is a visible metric rather than an invisible occurrence. A sudden rise in the deduplication rate is informative: it can mean a producer's retry policy has become too aggressive, a consumer is crashing and forcing redeliveries, or an upstream system is republishing events. The metric turns a property that is normally silent into a leading indicator of trouble elsewhere in the system, and teams that track it catch retry storms and crash loops earlier than teams that do not. The deeper patterns behind competing consumers and redelivery behavior that drive this metric are detailed in the guide to [async messaging patterns on Azure](/2024/06/24/azure-async-messaging-patterns/).

The second signal is the in-progress backlog. Records stuck in the in-progress state, neither completed nor cleaned up, mark operations that started and never finished, which is exactly the crash-window gap that idempotency cannot fully close. A query that counts in-progress records older than a threshold surfaces operations that need reconciliation, and it should feed an alert when the count grows, because each stuck record is a place where a side effect may have happened without being recorded, or may need to be retried. This backlog is the operational expression of the residual gap named earlier, and watching it is how a team keeps that gap small rather than letting it accumulate unseen.

The third signal belongs to the outbox relay. The count of unpublished outbox rows and the age of the oldest unpublished row together describe the relay's health. A backlog that grows means the relay has stalled or cannot keep up, and every unpublished row is an event the rest of the system has not heard, so the alert on this metric is one of the more important in the whole pattern. A relay that silently stops is among the worst failures available, because the database looks correct, the handlers look correct, and yet downstream systems are starving for events that sit unpublished in a table no one is watching. Instrumenting the relay's lag turns that catastrophic-but-invisible failure into a routine alert.

Proving idempotency, as opposed to monitoring it, is done with deliberate exercises rather than passive metrics. Periodically replaying a known message into a non-production copy of the system and asserting that side effects occur exactly once verifies that the pattern still holds as the code changes. Building this replay into a test suite, so that every deployment confirms the double-message and mid-flight-crash cases still produce single effects, prevents a refactor from silently breaking idempotency. The pattern is easy to break without noticing, because the breaking change passes every test that only ever sends each message once, so the test that sends it twice is the one that protects the property over time.

## The closing verdict

Idempotency on Azure is not a platform feature you enable; it is a consumer discipline you design. The platform's job is to never lose your messages, and it does that job by delivering at-least-once, which means duplicates are a normal condition rather than a fault. The effectively-once rule follows directly: because the platform will hand you the same message more than once, exactly-once behavior can only be achieved in your code, through an idempotency key that names the work and a processed-state store that remembers it, with the outbox pattern keeping your database and your events from drifting apart and deduplication catching repeats early.

The four mechanisms of the toolkit are small and composable. The idempotency key names a unit of work so a repeat can be recognized. The processed-state store remembers what was done so a redelivery can skip it. Deduplication, at the broker and at the store, turns away repeats before they do harm. The outbox removes the dual-write inconsistency by making the publish part of the same transaction as the state change. None of them is complex on its own, and the art is in composing them so that every link in a chain is idempotent and the whole behaves as exactly-once even though no single channel is.

The mistakes that matter are predictable. Expecting the platform to deliver exactly-once leaves every handler exposed. Performing a non-idempotent side effect on every delivery doubles charges and sends. Generating a fresh key per retry defeats deduplication silently. Writing to the database and publishing separately loses or duplicates events across the gap. Each has a named fix in this article, and the discipline is to audit a handler against the toolkit and confirm, for every side effect, that a duplicate is either impossible or harmless. Build that habit and the Friday-afternoon double charge stops being a possibility, because the system was designed from the start to treat a repeated message as the ordinary event it is. The shift in thinking is the lasting lesson: a duplicate is not an exception to be feared but a condition to be expected, and a system that treats redelivery as routine is calmer and more correct than one that treats it as a crisis. Once the toolkit is in place and observable, the team stops firefighting duplicates and starts trusting the channel to do what it actually promises, which is to never lose a message and to let the consumer make the rest safe.

## Frequently Asked Questions

### Q: How do I achieve idempotency and exactly-once processing on Azure?

You achieve it in the consumer, not the platform, because Azure messaging delivers at-least-once and cannot guarantee a single delivery end to end. The recipe has three parts. Give every unit of work a stable idempotency key, either supplied by the caller or derived from a business identifier such as an order. Keep a processed-state store, a durable table keyed on that identifier, and check it before performing any side effect, skipping the work if the key is already recorded as completed. Use the outbox pattern to publish events in the same transaction as your state change so the two never drift apart. Together these turn an at-least-once channel into processing whose observable effect is exactly-once. Broker features like Service Bus duplicate detection help with one class of duplicate, producer resends, but they do not replace the consumer-side store, because the broker still redelivers a message whose consumer crashed before completing it.

### Q: Why does at-least-once delivery require an idempotent consumer?

At-least-once delivery guarantees a message is processed one or more times but never promises exactly one, so a consumer will sometimes see the same message again. Two independent paths cause this even when nothing is broken. First, a producer that does not receive an acknowledgment resends, putting two copies in the queue. Second, a consumer that does the work and commits but crashes before telling the broker it finished leaves the broker to redeliver, because from its view the message was never completed. The broker cannot prevent the second case, since it is behaving correctly by redelivering an uncompleted message. The only defense is a consumer that recognizes it has already done the work and refuses to do it again. That recognition requires a stable key and a durable record, which is what makes idempotency mandatory rather than optional in any system that produces real side effects.

### Q: What is the difference between exactly-once delivery and exactly-once processing?

Exactly-once delivery is a property of the transport, meaning each message is delivered to the consumer precisely once, and it is effectively impossible to guarantee end to end over an unreliable network because a lost acknowledgment leaves the broker unable to tell whether to resend. Exactly-once processing is a property of the system's observable behavior, meaning the side effects happen as though each message were handled once, regardless of how many times it was actually delivered. Azure provides at-least-once delivery and lets you build exactly-once processing on top of it. The shift from chasing the first to building the second is the central insight, because the first is a fight against physics and the second is an achievable design. You stop trying to make the channel deliver once and start making your handler safe to call repeatedly, which is both attainable and durable.

### Q: How does an idempotency key actually deduplicate a request?

The key gives the receiver a stable name for the operation, which it consults before acting. On the first arrival, the receiver records the key, performs the work, and stores the result. On any later arrival carrying the same key, the receiver finds the record, skips the work, and returns the stored result, so the side effect occurs exactly once however many times the request arrives. The recording must be atomic to survive concurrency: rather than read-then-write, you insert the key under a unique constraint and let the database reject the second insert, so two racing requests cannot both proceed. The key must be identical across retries of the same operation and distinct across different operations. A client-supplied GUID in a header works when the caller controls retries; a derived business identifier works for asynchronous events where no caller key exists.

### Q: Does Azure Service Bus duplicate detection guarantee exactly-once?

It guarantees exactly-once delivery only over a configured time window and only for the sender-retry case. Duplicate detection keeps a history of MessageId values and discards any send whose identifier it has already seen within the window, which cleanly handles a producer that resends after a lost acknowledgment. It does not handle the redelivery that occurs when a consumer processes a message and crashes before completing it, because the broker is then redelivering a message it accepted exactly once, not receiving a duplicate send. It also keys only on MessageId, so the same logical event published with two different identifiers passes through as two messages. Duplicate detection is available on Standard and Premium tiers and must be enabled at creation time. Treat it as a useful first line that reduces duplicates, paired with a consumer-side processed-state store that catches the duplicates it cannot.

### Q: Where should I store processed-message state on Azure?

Store it wherever the protected side effect already commits, so the key and the effect move atomically. When the handler writes to Azure SQL, put the processed-state row in the same database and the same transaction, and use a unique constraint on the key so the second insert fails and signals a duplicate. When the handler is high-throughput or globally distributed, Cosmos DB fits, using a conditional write with an etag and a time-to-live to age out old keys automatically; mind that the configured consistency level affects whether a read immediately sees a just-written key. When you only need a cheap existence check with no stored result, Azure Table storage is the least expensive option. The guiding principle is colocation: the closer the store is to the business transaction, ideally inside it, the smaller the window in which a crash can leave the key and the effect inconsistent.

### Q: How does the outbox pattern prevent lost or duplicated events?

The outbox prevents lost events by writing the event into an outbox table in the same database transaction as the state change, so both commit atomically and an event can never be missing relative to the change it describes. A separate relay then reads unpublished rows and publishes them to the broker, marking each published once acknowledged. The relay delivers at-least-once, so it may publish a row twice if it crashes between publishing and marking it done, which means the pattern does not by itself prevent duplicate events. Instead it converts a hard problem, the lost event from a dual write, into an easy one, the duplicate event, which your idempotent consumers already handle. The relay can poll the table on an interval or read the database change feed for lower latency. Monitor the count of unpublished rows, because a growing backlog means the relay has stalled.

### Q: What is the dual-write problem and why can't I just order my writes carefully?

The dual-write problem is the inconsistency that arises when a handler must change state in a database and publish an event about it, but the two are separate systems with separate commits. If you write to the database then publish, a crash in between leaves the state changed with no event, so downstream systems never react. If you publish then write, a crash leaves an event for a change that never committed. No ordering removes the window, because there is no transaction spanning both systems, and the gap between their two commits is always exposed to a crash. A distributed transaction across both is theoretically possible but slow, fragile, and unsupported across most cloud database and broker pairings. The outbox pattern is the standard fix: it collapses the two writes into one by putting the event in the database transaction, then relays it to the broker afterward.

### Q: How do idempotency and retry policies work together?

They are complementary. A retry policy resends a request that failed transiently, which prevents a momentary fault from becoming a permanent failure, but every retry is a potential duplicate. Idempotency makes the duplicate harmless, so you can retry freely without risking a doubled side effect. The two together let you retry aggressively, with exponential backoff and jitter to spare a struggling dependency, knowing the worst case is wasted work rather than corrupted state. The one rule that ties them is that the idempotency key must stay constant across every retry of the same operation. Generating a new key per attempt makes each retry look like fresh work and defeats deduplication entirely, which is a common and silent mistake because the code reads as correct and only doubles effects under the exact failure it was meant to prevent. Design the retry and the key together.

### Q: Why was my payment charged twice and how do I stop it?

A payment is charged twice when the handler debits without first checking whether this exact operation already ran. A redelivered message, a producer resend, or a stream replay triggers a second call to the processor, and the processor honors both because it received two valid requests. Stop it with two layers. First, derive an idempotency key from the order and check a processed-state store before charging, skipping if the key is already completed. Second, pass that same key to the payment processor, which exposes an idempotency key precisely so a repeated charge request returns the original charge instead of creating a new one. The two layers matter because the local store and the processor can briefly disagree during a crash, and the shared key is what reconciles them. After a crash, re-sending the charge with the same key returns the existing charge rather than billing again.

### Q: How do I make sending an email idempotent when the provider has no idempotency key?

Guard the send entirely on your side, because the provider will not deduplicate for you. Before sending, write an in-progress marker keyed on the logical email, typically the recipient plus the message type plus the triggering entity. After the send succeeds, mark it completed, and on redelivery skip any email whose marker is completed. The unavoidable gap is a crash after the provider accepted the message but before you recorded completion, leaving an in-progress marker you cannot resolve by asking the provider, since it has no concept of your key. Resolve this with a policy chosen per email type. For a low-stakes transactional email such as a receipt, re-send and accept a rare duplicate. For a high-stakes message, suppress on in-progress and alert an operator to reconcile. Idempotency for effects you do not control bounds the damage rather than eliminating it.

### Q: Can I make an inventory decrement idempotent?

Yes, by changing the operation from a delta to something that does not compound on repetition. Subtracting one twice subtracts two, so a raw decrement is not idempotent. The cleanest fix is a reservation model: instead of decrementing a counter, insert a reservation row keyed on the order identifier with a unique constraint, so a second attempt to reserve for the same order fails and the stock is unaffected. Compute available stock from the reservations rather than mutating a counter directly, which turns a non-idempotent subtraction into an idempotent insert. This is the same insert-first discipline used for processed-state, applied to the business data itself, and it is usually cleaner than attaching a separate idempotency table to an operation that can be expressed idempotently. Where a reservation model does not fit, guard the delta with a processed-state key so the decrement runs at most once per key.

### Q: When is building idempotency machinery overkill?

It is overkill when the operation is already naturally idempotent or when a duplicate causes no harm. Setting a field to a fixed value, deleting a record by identifier, or replacing a value wholesale rather than adjusting it relative to its current value are all safe to repeat with no extra machinery. Adding a key and a store to these buys nothing and slows the hot path. Reserve the toolkit for operations whose effects compound on repetition: money moved, messages sent, counters incremented, resources allocated. The discipline is to ask, for each side effect, whether repeating this exact operation actually causes harm. If not, let the redelivery happen and do nothing special, because the simplest correct design is to recognize the operation is already safe. Spend complexity only where repetition is genuinely dangerous, and keep the rest of the system lean.

### Q: How long should I keep idempotency keys in the processed-state store?

Keep them at least as long as the longest window in which a retry or redelivery could arrive, plus a margin. If your retry policy and broker redelivery horizon mean no repeat of an operation can appear more than a few days after the original, keys older than that window can be deleted safely, because any message carrying such a key is so stale it should be treated as new or routed to a dead-letter queue rather than silently deduplicated. Setting the retention too short reopens the duplicate window for slow retries; setting it too long wastes storage and slows lookups as the table grows. Cosmos DB's time-to-live expires items automatically, which makes this self-managing. In Azure SQL, run a scheduled cleanup that deletes rows past the retention window. Size the window to your specific retry and redelivery horizons rather than guessing.

### Q: What is the difference between broker-side and consumer-side deduplication?

Broker-side deduplication, such as Service Bus duplicate detection, runs in the messaging platform and rejects repeated sends that carry an identifier the broker has already seen within a time window. It protects the send half of a message's life, the path from producer to broker, and it requires no consumer code. Consumer-side deduplication runs in your handler, using an idempotency key and a processed-state store to recognize a message it has already processed. It protects the receive half, the path from broker to consumer, including the redelivery that follows a consumer crash, which the broker cannot prevent. The two cover different windows and are not interchangeable. A well-built system uses both: the broker catches most producer resends cheaply, and the consumer catches the redeliveries and any duplicates that carry different identifiers. Relying on either alone leaves a gap the other was meant to close.

### Q: How do I test that my handler is genuinely idempotent?

Force the duplicate rather than waiting for one. Send the same message twice on purpose and assert that the side effect happened exactly once: one charge, one email, one decrement, one published event. Then simulate the harder case by killing the consumer after it commits the business change but before it acknowledges the message, and confirm that the broker's redelivery is recognized and skipped. Reproduce the dual-write crash by failing the publish after the database commit, and confirm the outbox relay still delivers the event. Each test targets a specific window, and passing all of them is what tells you the handler is safe under the conditions that actually occur in production. A handler that only ever sees each message once in testing has never exercised the code that matters, so the deliberate duplicate and the deliberate mid-flight crash are the tests that count.

### Q: Should the idempotency key be the same as a correlation or trace identifier?

It can be, and unifying them is a mature design choice. A correlation identifier follows a logical operation through every component for tracing; an idempotency key names a unit of work so repeats are recognized. When they are the same value, flowing from the originating request through every broker hop and downstream call, your deduplication and your distributed tracing become one mechanism. This makes diagnosing a duplicate far easier, because you follow a single identifier through every log and every store to see where a repeat entered and how it was handled. The requirement is that the value satisfies the idempotency constraint, stable across retries of the same operation and distinct across different operations, which a well-chosen correlation identifier usually does. Passing one identifier end to end, used both to trace and to deduplicate, is the state most resilient systems converge on as they mature.

### Q: Does using Event Hubs change how I handle idempotency compared to Service Bus?

The discipline is the same, but the duplicate source differs. Event Hubs is a streaming service that delivers at-least-once and tracks consumer position with a checkpoint rather than per-message acknowledgments. When a consumer fails and another resumes a partition, processing restarts from the last committed checkpoint, so events between that checkpoint and the failure are read again. There is no broker-side duplicate detection comparable to Service Bus, so all deduplication is consumer-side, keyed on a stable identifier in the event. With Service Bus you can lean on duplicate detection for producer resends and add a processed-state store for the rest; with Event Hubs you rely entirely on the processed-state store. In both cases the consumer must be idempotent, because both deliver at-least-once. The practical difference is that Event Hubs replays a span of events on recovery rather than redelivering one message, so test your handler against a checkpoint replay specifically.

### Q: Can two consumers process the same message at the same time, and how does idempotency handle that?

Yes, under competing-consumer patterns or during a redelivery race, two instances can briefly hold the same logical message. Idempotency handles this through an atomic gate rather than a read-then-act check, which would let both pass. The standard technique is to insert the idempotency key under a unique constraint as the first step: whichever instance's insert commits first wins and proceeds with the work, while the other's insert fails on the constraint and it treats the failure as a signal that the work is already claimed. Because the database enforces uniqueness atomically, there is no window in which both insert successfully, so the side effect runs once. For external effects you cannot wrap in the database transaction, also pass the shared key downstream so the external system rejects the second call. The combination of the atomic local gate and the shared downstream key keeps concurrent processing from doubling the effect.

### Q: Can idempotency cause me to silently drop a legitimate request?

Yes, and it is the failure mode of an over-coarse key. If the key identifies work more broadly than the actual unit of work, a genuinely new operation can collide with a past one and be treated as a duplicate, so the system skips it and the caller never learns the work did not run. Keying a charge on the customer rather than the order does this: the customer's second order matches the first order's key and is dropped. The defense is to make the key equal exactly when two requests represent the same business fact and different otherwise, and to err toward client-supplied keys when the data alone cannot decide. Monitoring the deduplication rate also helps, because a spike in skips can reveal a key that is collapsing distinct operations together. A dropped legitimate request is the mirror image of a double effect, and a well-chosen key avoids both.
