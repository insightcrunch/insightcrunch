---
layout: post
title: "The Strangler Fig Migration Pattern on Azure"
page_title: "Strangler Fig Pattern on Azure: Incremental Monolith Migration With Facade Routing, Safe Rollback, and Data Coexistence"
date: 2024-07-01
categories: ["Technology"]
tags: ["Azure", "Strangler Fig", "Architecture", "Migration & Modernization", "API Management", "Cloud Computing"]
excerpt: "The Strangler Fig pattern migrates an Azure monolith one capability at a time behind a facade, with routing-based rollback and a data coexistence plan."
image: "/assets/images/blog/blog-11.webp"
reading_time: 60
author: "Insight Crunch Team"
last_updated: 2024-07-01
---

The Strangler Fig pattern is how you migrate a monolith on Azure without betting the business on one weekend cutover, and the easiest way to see why it matters is to picture the alternative first. A team inherits a monolith that has run the business for nine years. It works, it pays the bills, and nobody fully understands it anymore. Leadership wants microservices, the cloud, and faster releases, so somebody proposes the obvious plan: freeze new features, rewrite the whole thing on Azure, and switch over on a weekend. Eighteen months later the rewrite is two thirds done, the frozen feature backlog has become a competitive liability, and the cutover weekend keeps slipping because nobody can prove the new system matches the old one on every edge case the monolith quietly handles. This is the big-bang rewrite, and it fails the same way almost every time.

The Strangler Fig pattern is the answer to that failure. Named by Martin Fowler in 2004 after the tropical fig that grows around a host tree and gradually replaces it, the Strangler Fig pattern migrates a monolith to a modern architecture one capability at a time, behind a routing layer that decides on every request whether the old system or the new one answers it. The old and the new run side by side for as long as the migration takes, the risk of each step is bounded to the single capability being moved, and a step that goes wrong is undone by routing traffic back rather than by a panicked restore. On Azure the routing layer is realized by Azure API Management, Azure Front Door, or Application Gateway, and the surrounding services give you the observability, the deployment slots, and the data-replication options that make incremental replacement safe. This article gives you a repeatable migration step you can apply to one capability at a time until the monolith is gone.

![Strangler Fig migration pattern on Azure with facade routing between legacy and new systems - Insight Crunch](/assets/images/blog/blog-11.webp)

The promise is not that migration becomes easy. The promise is that migration becomes a sequence of small, reversible, individually shippable changes instead of one enormous irreversible one. That difference is the whole reason the pattern exists, and it is the difference between a modernization program that ships value every sprint and one that burns a year of engineering before it produces anything a customer can use.

## What the Strangler Fig pattern actually is

The Strangler Fig pattern is a method for replacing a legacy system gradually, by introducing a new system that grows alongside the old one and slowly takes over its responsibilities until the old system can be retired. The mechanism is a routing layer, often called the facade, that sits in front of both systems. Every client request hits the facade first. The facade looks at the request and decides whether the capability it asks for has already been migrated. If it has, the request goes to the new service. If it has not, the request goes to the legacy monolith exactly as it always did. The client cannot tell the difference, because the facade preserves the same external contract throughout.

That single design choice is what makes the pattern work. Because the client always talks to a stable address with a stable contract, you can move capabilities behind that address without coordinating a single client change. The migration becomes invisible to the outside world, which means you can do it during business hours, in small increments, with real production traffic validating each step. Microsoft's own architecture guidance describes the same four phases: a facade routing between the legacy and new systems, incremental decomposition that shifts more traffic to the new system over time, full decommissioning of the legacy system once nothing depends on it, and finally removal of the facade so clients talk directly to the modern system. Verify the current phase descriptions against the official Azure Architecture Center before you cite them in a design review, because the documentation is revised as the guidance matures.

### What problem does the Strangler Fig pattern solve?

It solves the risk of a big-bang rewrite. Instead of replacing an entire monolith in one cutover that cannot be partially undone, the pattern replaces it one capability at a time behind a facade. Each step ships independently, runs against real traffic, and rolls back by routing, so the blast radius of any single change stays small.

The named idea worth carrying out of this section is the route-a-slice-at-a-time rule: the Strangler Fig migrates exactly one capability at a time behind a facade, and the rollback for any step is a routing change rather than a data restore, so the risk attached to each step is bounded to that one capability. Everything else in the pattern, the data strategy, the observability, the cutover criteria, exists to keep that rule true. When a migration goes sideways, it is almost always because somebody broke the rule: they tried to move three capabilities at once, or they moved a capability whose data the monolith still writes to, or they shipped a step with no way to route back. Hold the rule and the pattern protects you. Break it and you have reinvented the big-bang rewrite with extra steps.

### How does the Strangler Fig differ from a parallel run?

A parallel run sends the same request to both old and new systems and compares the outputs without the new system being authoritative. The Strangler Fig actually routes a request to one system or the other, making the chosen system the source of truth for that capability. Parallel running is a validation technique you can use inside a strangler step, not a replacement for it.

The distinction matters because teams sometimes conflate the two and end up running both systems in full for every request indefinitely, paying double the compute and getting none of the decommissioning benefit. In a Strangler Fig migration the goal is always retirement. Every capability you move is a capability the monolith no longer needs to serve, and the program is not finished until the legacy system is switched off and its infrastructure is reclaimed. A parallel run that never converges on a single authoritative system is a cost center, not a migration. You can borrow the comparison technique, sending a copy of production traffic to the new service and diffing the results, as a way to gain confidence before you flip the routing rule, but the comparison is a means to an end and the end is always a clean cutover for that slice.

### Why is it called a strangler fig?

The tropical strangler fig germinates in the canopy of a host tree, sends roots down around the trunk, and gradually envelops the host. Over years the fig's own structure becomes self-supporting, the host dies inside it, and the fig stands where the tree once did. Software modernization follows the same arc: the new system grows around the old until the old is gone.

The metaphor is more than decoration, because it captures the property that makes the pattern safe. At no point does the fig cut the host down in a single act. The host keeps standing, keeps doing its job, right up until the moment the fig no longer needs it. A migration built on this pattern has the same property. The monolith keeps serving every capability that has not yet been moved, and it keeps serving them with its full, battle-tested behavior, including all the edge cases the team has long forgotten the code even handles. You are never in a state where a capability is half-migrated and served by neither system, and you are never betting the business on a cutover that has to work on the first try.

## The Azure services that realize the facade

The pattern is platform-agnostic, but the facade has to be a real piece of infrastructure, and on Azure you have three credible choices. Each routes traffic, each can preserve a stable external contract, and each carries different trade-offs around protocol support, routing granularity, and where it sits in the request path. Choosing the wrong facade is one of the more expensive early mistakes, because the facade is hard to swap once dozens of routing rules and clients depend on it.

### Azure API Management as the facade

Azure API Management, usually written APIM, is the natural facade when your monolith exposes an API and you want fine-grained, policy-driven control over which operation goes where. APIM puts a gateway in front of your backends and lets you attach policies to individual operations. A policy can inspect the path, the method, headers, the caller's identity, or a percentage roll, and then set the backend dynamically. That means you can migrate a single endpoint, say the order-status lookup, by changing one operation's backend from the monolith to the new service while every other operation keeps pointing at the monolith.

```xml
<!-- APIM inbound policy: route GET /orders/{id}/status to the new service -->
<policies>
  <inbound>
    <base />
    <choose>
      <when condition="@(context.Request.Url.Path.EndsWith("/status"))">
        <set-backend-service base-url="https://orders-svc.internal.contoso.com" />
      </when>
      <otherwise>
        <set-backend-service base-url="https://monolith.internal.contoso.com" />
      </otherwise>
    </choose>
  </inbound>
  <backend>
    <base />
  </backend>
</policies>
```

The policy language is the lever that makes APIM expressive enough for capability-level routing. You can split traffic by percentage to ramp a new service from one percent to one hundred, route by a header your load test injects, or send authenticated internal users to the new service while the public still hits the monolith. APIM also gives you a developer portal, request and response transformation, schema validation, and authentication integration with Microsoft Entra ID and OAuth2, which matters when the new services need a different auth model than the monolith assumed. The cost is that APIM is a heavier component than a plain load balancer, and the policy logic can accumulate complexity if you let business rules leak into it. Keep the policies limited to routing and contract enforcement, and resist the temptation to make the facade clever.

### Azure Front Door as the facade

Azure Front Door is the right facade when the deciding factor is global reach, edge presence, or weighted traffic distribution across regions. Front Door is a global, layer-7 entry point with built-in routing rules, health probes, and the ability to split traffic across origin groups by weight. For a strangler migration that needs canary-style rollout, Front Door's weighted routing lets you send five percent of traffic for a path to the new origin and the rest to the monolith, then increase the weight as confidence grows. It also terminates TLS at the edge and brings a web application firewall, which can be a clean place to consolidate security controls during a migration.

Front Door and APIM are not mutually exclusive, and a common production shape uses both. Front Door provides the global edge, the WAF, and coarse path or weight routing, and APIM sits behind it providing the per-operation policy control and the developer-facing API surface. The article on the differences between [Front Door, CDN, and Application Gateway](/2023/10/09/front-door-vs-cdn-vs-gateway/) walks through where each one belongs in the request path and why you would layer them, which is worth reading before you commit to a facade topology, because the decision shapes every routing rule you write afterward.

### Application Gateway as the facade

Application Gateway is the regional layer-7 load balancer with path-based routing, and it fits when your migration is single-region, the routing decisions are path-driven, and you want the facade inside your virtual network rather than at the global edge. It supports URL path maps, so you can point `/orders/*` at the new backend pool and leave `/inventory/*` on the monolith pool, and it integrates with the regional WAF. For a workload that lives in one region and talks mostly to internal clients, Application Gateway is often the simplest facade that does the job, with less operational surface than a global service.

```bash
# Application Gateway URL path map: route /orders/* to the new pool
az network application-gateway url-path-map create \
  --gateway-name strangler-agw \
  --resource-group rg-modernization \
  --name strangler-path-map \
  --paths "/orders/*" \
  --address-pool orders-new-pool \
  --http-settings orders-http-settings \
  --default-address-pool monolith-pool \
  --default-http-settings monolith-http-settings
```

The choice among the three comes down to scope and granularity. If you need per-operation policy logic and an API surface, reach for APIM. If you need global edge, weighted canary routing, and a WAF at the edge, reach for Front Door. If you are single-region and path-based, Application Gateway is the lean option. Whichever you choose, the facade must do two things reliably: intercept every request before it reaches the legacy system, and decide with precision whether that request goes to the old system or the new one. A facade that cannot intercept every request leaks traffic past your routing rules, and a facade that cannot decide precisely forces you to migrate in chunks larger than a single capability, which breaks the route-a-slice-at-a-time rule.

You can stand up and test all three facade options in a sandbox before committing, and the fastest way to feel the differences is to build each one against a stub backend and watch how the routing behaves under traffic. The [hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) is where to spin up a facade, wire it to a monolith stub and a new-service stub, and migrate a slice end to end so the routing logic stops being abstract.

## The InsightCrunch strangler migration map

A migration that survives contact with production needs a repeatable step, not a one-off plan. The InsightCrunch strangler migration map is that repeatable step expressed as five fields you fill in for every capability you move. Each row of the table below is one capability's migration, and the discipline is that you do not start moving a capability until all five fields are answered. If you cannot name the rollback path, you are not ready to ship the step. If you cannot describe the data-coexistence approach, you will create divergence between old and new. The map turns a vague modernization goal into a checklist you can apply slice by slice until the monolith is empty.

| Field | What it specifies | Example for an order-status slice |
|-------|-------------------|-----------------------------------|
| Facade | The routing layer and the rule type it uses | APIM, per-operation policy on `GET /orders/{id}/status` |
| Slice | The single capability being moved, defined by its external contract | The read-only order-status lookup, one endpoint, no writes |
| Routing rule | The condition that sends a request to the new service instead of the monolith | Path match on `/status`, ramped 5 percent to 100 percent by weight |
| Rollback path | The exact action that returns traffic to the monolith | Revert the operation backend to the monolith URL, one policy change |
| Data coexistence | How old and new stay consistent for the data this slice touches | Read-only slice reads the monolith database directly, no sync needed |

The power of the map is that it forces the right order of thinking. You start from the slice, the smallest capability with a clean external contract, because a clean contract is what lets the facade route it without the client noticing. You then choose the facade rule that can express the routing for that contract. You write the rollback path before you write the forward path, so that the undo is designed rather than improvised. And you resolve the data question last and most carefully, because data coexistence is where most strangler migrations actually fail.

A read-only slice is the easiest possible case and the right place to begin a program, which is why the example row above is an order-status lookup. It reads data the monolith owns, it writes nothing, and so the new service can read straight from the monolith's database during coexistence with zero risk of divergence. There is nothing to keep in sync because only one system writes. When you graduate to a slice that writes, the data field gets much harder, and the rest of this article spends most of its remaining length on exactly that problem, because it is the one that turns a tidy migration into a data-integrity incident.

### What is the smallest safe first slice?

The smallest safe first slice is a read-only capability with a clean, self-contained contract and no writes to shared data. Reading order status, fetching a product description, or returning a user's profile are ideal first moves: the new service reads the monolith's data, writes nothing, and rollback is a single routing revert with no data to reconcile.

Starting read-only is not timidity, it is sequencing. The first slice's real job is to prove the facade, the deployment pipeline, the observability, and the rollback mechanics on a capability where a mistake cannot corrupt data. Once the team has shipped one read-only slice, watched it ramp from a trickle of traffic to all of it, and practiced routing back and forward, the machinery is proven and the next slice can be more ambitious. Teams that skip this and lead with a write-heavy capability tend to discover their rollback path does not actually work at the worst possible moment, because the first time they exercise it is during an incident.

## A reference design walked through

Theory only goes so far, so walk through a concrete migration of one capability end to end. The workload is an e-commerce monolith on Azure: a single application behind a load balancer, backed by one relational database, serving orders, inventory, payments, and notifications. The target is a set of services on [Azure Kubernetes Service following a microservices reference architecture](/2024/04/29/aks-microservices-architecture/), reached through an APIM facade. The capability being moved in this walkthrough is order placement, which is a write capability, so it exercises every hard part of the pattern.

### Phase one, introduce the facade with everything still on the monolith

The first move changes nothing about behavior. You place APIM in front of the monolith so that every client now resolves to the APIM gateway address instead of the monolith's load balancer, and APIM routes one hundred percent of traffic straight through to the monolith. No capability has moved. The point of this phase is to insert the routing layer transparently and confirm that the facade preserves the contract exactly, that latency is acceptable, that authentication still works, and that your observability sees every request flowing through the new control point. You ship this, you watch it for a week, and you make sure the facade is boring before you ask it to do anything interesting.

This phase is where you also wire up the comparison harness if you intend to use one. You configure APIM to mirror a copy of order-placement traffic to the new order service running in the background, where it processes the request and records what it would have done without being authoritative. The monolith remains the only system that actually places orders. The mirror lets you diff the new service's behavior against the monolith on real production traffic before a single customer's order depends on it, which surfaces the edge cases the new code missed while the cost of being wrong is still zero.

### Phase two, build the new service and migrate the read side first

Before you move order writes, you move order reads. The new order service gets an endpoint that returns order details, and you flip the APIM routing rule for `GET /orders/{id}` to point at the new service while leaving `POST /orders` on the monolith. During this phase the new service reads order data directly from the monolith's database, because the monolith is still the only writer and reading from the source of truth guarantees the new read path returns exactly what the monolith would. You ramp this from a small percentage to all read traffic using a weighted policy, watching error rates and latency at each step. If anything regresses, you revert the one routing rule and reads go back to the monolith instantly.

```xml
<!-- Phase two: reads go to the new service, writes stay on the monolith -->
<choose>
  <when condition="@(context.Request.Method == "GET" &amp;&amp; context.Request.Url.Path.Contains("/orders/"))">
    <set-backend-service base-url="https://orders-svc.internal.contoso.com" />
  </when>
  <otherwise>
    <set-backend-service base-url="https://monolith.internal.contoso.com" />
  </otherwise>
</choose>
```

Splitting reads from writes is a deliberate sequencing tactic. Reads are idempotent and carry no risk of corrupting state, so moving them first lets you validate the new service's data access, its serialization of the order contract, and its performance under full read load, all before you take on the genuinely hard problem of moving the writes. By the time you are ready to move writes, the new service is already serving every read in production and you have high confidence in its data layer.

### Phase three, move the writes with a data-coexistence strategy

Moving order placement is the moment the data question becomes unavoidable. Once the new service accepts a `POST /orders`, two systems can write order data, and without a coexistence strategy they will diverge. The cleanest approach for this slice is to make the new order service the single writer for orders the moment you flip the write routing, and to give the monolith read access to the new orders through replication or a shared view, so that any monolith capability still reading orders sees the new ones. The principle is that for any given piece of data, exactly one system writes it at a time, and the other system reads a consistent copy. The detailed mechanics of keeping that copy consistent are the subject of the next section, because they are where the real engineering lives.

You flip the write routing the same careful way you flipped reads: a small percentage first, with the comparison harness confirming the new service produces the same order records the monolith would have, then ramping to full traffic. The rollback path is still a routing revert, but now it carries a data caveat. If you route writes back to the monolith after the new service has accepted real orders, those orders must be visible to the monolith, which is exactly why the coexistence strategy has to be in place before you flip writes, not after. A rollback that strands data in the new system while the monolith serves the old set is not a rollback, it is a second incident.

### Phase four, declare the slice migrated and remove it from the monolith

When the new service has served all order traffic, reads and writes, at full volume for long enough to trust it, the order capability is migrated. You delete the order code paths from the monolith, remove the monolith's order backend from the facade, and reclaim whatever order-specific infrastructure the monolith needed. The slice is done. The monolith is now strictly smaller than it was, and the next slice begins. Repeat the four phases for inventory, then payments, then notifications, and the monolith shrinks capability by capability until the day it serves nothing and you switch it off. That final decommissioning is the payoff the parallel run never reaches, and it is the only honest signal that the migration is finished.

## Data coexistence during migration

Routing requests is the easy half of the Strangler Fig pattern. The hard half is data, and it is the half that turns a clean migration into a corruption incident when teams treat it as an afterthought. The core problem is simple to state and hard to solve: while a capability is being migrated, the data that capability touches may be read or written by both the old and the new system, and unless you have a deliberate strategy, the two copies diverge. A customer updates their address through a path that hits the new service, then a monolith capability reads the stale address from the old database, and now the business is shipping to the wrong place. Every serious strangler failure traces back to a missing or wrong answer in the data-coexistence field of the migration map.

The governing principle is single-writer ownership. For any given piece of data, during coexistence, exactly one system is the authoritative writer and every other system reads a consistent copy. The migration of a capability is, at the data layer, the transfer of write ownership for that capability's data from the monolith to the new service. Before the transfer the monolith writes and the new service reads. After the transfer the new service writes and the monolith reads. The dangerous state, the one that causes divergence, is when both write the same data at the same time, and the entire job of the coexistence strategy is to make sure that state never occurs.

### How do old and new systems share data during migration?

They share data by designating one system as the single writer for each piece of data and giving the other system a consistent read copy, through direct reads from the source database, change-data-capture replication, an anti-corruption layer, or a shared store. The rule is that two systems never write the same data concurrently, which is what prevents divergence.

There are four practical mechanisms for sharing data during coexistence, and which one you use depends on whether the slice reads or writes, how tolerant the reading side is of staleness, and how cleanly the data can be partitioned by capability.

### Direct shared-database reads

The simplest mechanism is to let the non-writing system read directly from the writing system's database. When the new service serves reads while the monolith still owns writes, the new service can query the monolith's database and is guaranteed to see exactly what the monolith would, because there is only one copy. This is what the order-status read slice used, and it is the reason read-only slices are the safe first move. The drawback is coupling: the new service is now bound to the monolith's schema, which you wanted to escape, so direct shared reads are a coexistence tactic for the transition window, not a permanent design. You accept the temporary schema coupling because it eliminates divergence entirely while you validate the new service, and you break the coupling when write ownership transfers and the new service gets its own store.

### Change data capture and replication

When the new service needs its own database but the monolith still owns the writes, you replicate changes from the monolith's database into the new service's store using change data capture. The monolith remains the single writer, its changes stream into the new store with low latency, and the new service reads its own copy without coupling to the monolith schema. Azure offers several ways to build this, from native database replication features to a change feed processed by an event pipeline. The tradeoff is replication lag: the new service's copy is eventually consistent with the monolith, so this mechanism fits slices that tolerate a small staleness window and does not fit slices that demand read-your-writes consistency across the system boundary. You must measure the lag under production write volume and confirm it sits inside the slice's tolerance before you rely on it.

```sql
-- Enable change data capture on the orders table (SQL Server / Azure SQL MI)
EXEC sys.sp_cdc_enable_table
  @source_schema = N'dbo',
  @source_name   = N'Orders',
  @role_name     = NULL,
  @supports_net_changes = 1;
-- A capture process then exposes inserts, updates, and deletes
-- which a replication worker drains into the new service's store.
```

### The anti-corruption layer

A new service modeled cleanly should not inherit the monolith's data shapes, naming, or quirks. The anti-corruption layer is a translation boundary that converts between the monolith's model and the new service's model so that the legacy design does not leak into the new code. When the new service reads monolith data or consumes monolith events, the anti-corruption layer maps the old representation to the new one, and when it must write back to a monolith-owned store during transition, it maps the other direction. This layer is what lets you redesign the data model in the new service without being held hostage by the monolith's schema, and it is also a natural place to put the comparison logic that diffs new behavior against old during a mirrored run. Treat the anti-corruption layer as a first-class component of the migration, because skipping it is how the new system ends up as a monolith with a different deployment target.

### Transferring write ownership without dual writes

The riskiest moment is the handoff of write ownership, and the wrong way to do it is dual writing, where application code writes to both the old and new stores in the same operation to keep them in sync. Dual writes have no transactional guarantee across two systems, so a failure between the two writes leaves the stores inconsistent with no clean recovery, and this dual-write inconsistency is one of the classic distributed-systems traps. The right way is to make the cutover atomic at the routing layer: up to the flip, the monolith is the sole writer and the new store is kept current by replication; at the flip, the new service becomes the sole writer and replication reverses so the monolith's store is now the follower. There is a single authoritative writer at every instant, and the transition is a change of direction, not a window of concurrent writing.

For capabilities where even a brief inconsistency is unacceptable, the [event-driven architecture patterns](/2024/04/22/azure-event-driven-architecture/) that decouple writes through a durable log give you a cleaner handoff than synchronous replication, because the log is the single ordered source of truth and both stores are projections of it. The transactional outbox pattern, where a service writes its state change and its outgoing event in one local transaction and a relay publishes the event afterward, is the standard way to avoid the dual-write problem when a write must both update a store and notify another system. The migration map's data-coexistence field should name which of these mechanisms a slice uses, and that name is the single most important entry in the whole map.

## Keeping rollback safe

The reason the Strangler Fig pattern bounds risk is that every step has a rollback, and the rollback is a routing change rather than a restore. This is worth stating precisely because it is the property that separates the pattern from a big-bang rewrite, where the only rollback is reverting an entire cutover under pressure. In a strangler step, if the new service misbehaves, you change one routing rule and traffic returns to the monolith, which is still running and still correct. The mean time to recovery is the time it takes a facade configuration to propagate, usually seconds to a couple of minutes, not the hours a database restore would cost.

### How do I keep rollback safe during a migration?

Keep rollback safe by designing the routing revert before you ship the forward route, keeping the legacy system fully operational until the slice is proven, and ensuring no data is stranded if you route back. A rollback is safe only when routing traffic to the monolith leaves the system in a consistent, complete state with no orders or updates lost in the new service.

Safe rollback has three requirements, and a step that fails any of them is not actually reversible. The first is that the legacy system stays alive and correct for the entire coexistence window. The instant you delete monolith code for a capability you have not finished migrating, you have removed your rollback target, so decommissioning is the last phase for a reason. The second requirement is that the routing revert is a single, tested, fast operation. You should rehearse the revert on the read slice, where it is harmless, so that when you need it on a write slice it is muscle memory and the configuration is known to work. A rollback procedure that has never been run is a hypothesis, not a safety net.

The third requirement, and the one teams underestimate, is data reversibility. For a read-only slice, routing back is trivially safe because the new service wrote nothing. For a write slice, routing back is only safe if the data the new service wrote is visible to the monolith when it resumes ownership. This is the direct consequence of the coexistence strategy: if replication kept the monolith's store current as a follower while the new service was the writer, then routing back hands a current store to the monolith and the rollback is clean. If you flipped writes without keeping the monolith's store current, routing back strands every order the new service accepted, and the rollback produces a worse state than the failure it was meant to fix. This is why the data-coexistence field and the rollback-path field of the migration map are coupled, and why you cannot fill in one without the other.

A useful discipline is to define, for each slice, the rollback trigger as well as the rollback action. The trigger is the measurable condition that says route back now: an error rate above a threshold, a latency regression beyond a bound, a divergence the comparison harness flags. Naming the trigger in advance turns rollback from a judgment call made by a stressed engineer into an automatic response to a metric, and it removes the bias toward riding out a bad deploy in the hope it recovers. Wire the trigger into your alerting so the signal that should cause a rollback is the same signal that pages the on-call engineer.

## Knowing when a slice is fully migrated

A migration that never declares slices done is a migration that never finishes, so you need an explicit definition of done for each capability. A slice is fully migrated when the new service has served all of that capability's traffic, both reads and writes, at full production volume, for long enough to cover the capability's natural cycle, with error and latency metrics at or better than the monolith's baseline, and with the comparison harness showing no behavioral divergence. Only when all of that holds do you delete the capability from the monolith.

### When is a capability safe to remove from the monolith?

A capability is safe to remove when the new service has carried one hundred percent of its traffic at full volume through at least one complete business cycle with healthy metrics and no divergence, and when nothing else in the monolith still calls that capability's code or reads its data directly. Removing it any earlier destroys your rollback target.

The phrase one complete business cycle matters because some capabilities only exercise their hard paths periodically. A billing capability might look perfect for three weeks and then hit its month-end batch run, which is exactly the path most likely to expose a difference between old and new. Declaring billing done before it has survived a month-end cycle is declaring it done before you have tested the code that matters most. Match the soak time to the capability's real rhythm, not to a fixed calendar.

The second condition, that nothing else still depends on the capability, is where monolith coupling fights back. Monoliths are full of internal calls and shared-table reads that are not visible from the external contract, so a capability that looks isolated at the API may still be read internally by three other monolith capabilities through the database. Before you delete order code, you have to confirm that no remaining monolith capability reads the orders table directly, or you will break those capabilities silently. This is why the data-coexistence mechanism often needs to outlive the routing cutover: the monolith keeps a current copy of the orders data, through replication, until every monolith capability that read orders has itself been migrated and no longer needs it. Decommissioning is gradual at the data layer even when it looks instant at the routing layer.

When a slice is genuinely done, the cleanup is concrete: remove the capability's routes from the facade so the monolith backend is no longer reachable for it, delete the capability's code and tests from the monolith, drop the replication that kept the monolith's copy current once no monolith capability needs it, and reclaim the compute and storage the capability consumed. Each cleanup step is itself reversible until the final delete, so you can stage the decommissioning and confirm nothing breaks before you remove the last safety net.

## Trade-offs and failure modes

The Strangler Fig pattern is not free, and pretending otherwise sets a team up to abandon it halfway when the costs show up. The honest accounting is that the pattern trades a single large risk for a longer period of managed complexity. You avoid the catastrophic failure mode of a big-bang cutover, and in exchange you accept that two systems run side by side for the duration, that the facade is a new component to operate and secure, and that the data-coexistence machinery adds moving parts that did not exist before. For most non-trivial monoliths this is a good trade, because the big-bang risk is the kind that ends programs and careers, while the coexistence complexity is the kind that good engineering manages. But it is a real trade, and the team should go in with eyes open.

### The facade as a single point of failure

The facade sees every request, so if it goes down, everything goes down, including the capabilities still served by the monolith that would otherwise be fine. This is the most cited objection to the pattern, and it is legitimate. The mitigation is to choose a facade that is itself highly available and to treat it with the operational seriousness its position demands. APIM, Front Door, and Application Gateway all offer redundancy and health-based routing, and Front Door in particular is a global, multi-region service designed to absorb regional failure. You also keep the facade dumb. The more business logic you push into the routing layer, the more likely a facade change breaks something and the larger the blast radius of a facade incident. The facade coordinates traffic and enforces contracts; it does not run the business.

### Latency from the extra hop

Inserting a facade adds a network hop to every request, which adds latency. For most workloads the added milliseconds are negligible against the request's total time, especially when the facade also terminates TLS and caches at the edge, but for latency-sensitive paths it is a real cost to measure rather than assume. The phase-one step of inserting the facade with all traffic still going to the monolith exists partly to measure this latency before any capability moves, so you learn the facade's overhead on a known-good system and can decide whether a latency-critical path needs a different routing approach.

### The migration that stalls

The most common failure mode is not technical, it is organizational: the migration stalls. A team moves three easy read slices, declares early victory, and then the hard write capabilities and the tangled data dependencies sit untouched for two years while the monolith and the new services both keep running, both keep needing maintenance, and the promised decommissioning never arrives. A stalled strangler migration is worse than no migration, because you are now paying to operate and secure two systems and a facade indefinitely. The defenses are to sequence the hard slices deliberately rather than only picking low-hanging fruit, to track the migration as a percentage of capability moved with a visible burndown, and to treat the monolith's continued existence as a cost the program is accountable for retiring. If the organization will not commit to finishing, it should not start, because the half-done state is the most expensive place to live.

### Migrating a slice without a data plan

The technical failure mode that causes the most damage is moving a write capability without a coexistence strategy, so that old and new write the same data concurrently and diverge. This is the dual-write trap and the divergence it causes can be subtle, accumulating silently until a reconciliation or an audit reveals that the two systems disagree about something that matters, like account balances or inventory counts. The defense is the migration map's discipline: no slice ships until its data-coexistence field names a single-writer mechanism, and write slices are validated with a comparison harness before the routing flips. A slice whose data plan is undecided is not ready, no matter how clean its routing looks.

### No rollback path

The last failure mode is shipping a forward route with no working backward route, usually because the team designed the migration and treated rollback as obvious. Rollback is only obvious for read slices. For write slices it depends entirely on the data-coexistence strategy keeping the monolith's store current, and a team that did not design that will discover during an incident that routing back strands data. The defense is to design and rehearse the rollback before shipping the forward route, and to refuse to ship any step whose rollback has not been tested on a safe slice first.

## When the pattern fits and when it is overkill

The Strangler Fig pattern is the right tool for a specific shape of problem, and reaching for it when the problem is a different shape wastes effort. It fits when you have a large, business-critical system that cannot tolerate the downtime or the risk of a big-bang cutover, where the system can be decomposed into capabilities with reasonably clean contracts, and where the migration will take long enough that running old and new in parallel for a while is acceptable. It fits a nine-year-old monolith that the business depends on every minute, exactly the case the opening described.

### When is the Strangler Fig better than a big-bang rewrite?

It is better whenever the cost of a failed cutover is high and the system is large enough that a full rewrite would take many months. The pattern wins by bounding risk to one capability per step and making every step reversible by routing. A big-bang rewrite only competes when the system is small enough to rewrite and cut over in days, with low cost if the cutover fails.

The pattern is overkill for a small system. If the application is a few thousand lines that one engineer understands and a rewrite would take a couple of weeks with a cutover you can test exhaustively and reverse with a deployment rollback, the facade, the coexistence machinery, and the multi-phase ceremony are more overhead than the migration itself. The honest decision rule is to weigh the cost of a failed big-bang cutover against the cost of running the strangler machinery. When a failed cutover would be catastrophic and hard to reverse, the strangler's overhead is cheap insurance. When a failed cutover would be a minor inconvenience easily rolled back, the strangler's overhead is not worth paying.

The pattern is also a poor fit when the monolith genuinely cannot be decomposed, when its capabilities are so entangled that no slice has a clean contract and every read touches every table. In that case the honest first step is not a strangler migration but a period of decoupling work inside the monolith to create the seams the pattern needs, after which the strangler becomes viable. Trying to strangle a system with no seams produces slices so large that each step is itself a mini big-bang, which defeats the purpose. The broader [cloud migration strategy for Azure](/2025/08/04/azure-cloud-migration-strategy/) covers the assessment that tells you whether a workload is ready for a strangler approach or needs decoupling first, and that assessment is worth doing before you commit to the pattern, because it is far cheaper to learn a system lacks seams on paper than three slices into a stalled migration.

## How to evolve the migration over time

A strangler migration is not a single decision, it is a program that runs for months and sometimes years, and it has to evolve as it goes. The first slices teach the team things the plan could not anticipate, and the migration map should be revised as those lessons land. Early on you optimize for proving the machinery, so you pick safe read slices and accept temporary schema coupling through direct shared reads. As confidence grows you take on write slices and invest in proper coexistence through replication and anti-corruption layers. Late in the program you tackle the most entangled capabilities, the ones whose data the whole monolith touches, and these often require decoupling work inside the remaining monolith before they can be sliced cleanly.

The facade topology also evolves. A migration might start with a single Application Gateway because the workload is regional and path-based, then grow into an APIM-plus-Front-Door arrangement as the new services need per-operation policy and the business expands to multiple regions. Plan the facade so that this evolution does not require rewriting every routing rule, which usually means keeping the routing logic declarative and version-controlled rather than hand-edited in a portal. Treat the facade configuration as infrastructure as code so that every routing change is reviewed, versioned, and reversible, and so the rollback of a routing change is a revert in source control rather than a frantic portal edit.

### How do I track progress through a long migration?

Track progress as the percentage of capabilities fully migrated and decommissioned from the monolith, not as the percentage of new code written. A capability counts as done only when the monolith no longer serves it and its code is removed. This burndown makes a stall visible early, because the curve flattens the moment the team stops finishing slices.

Measuring migrated-and-decommissioned rather than built is the metric that keeps a program honest. It is easy to write a lot of new-service code and feel productive while the monolith shrinks not at all because nothing has actually been cut over and retired. The burndown of capabilities still served by the monolith is the only number that tracks real progress toward the goal, which is a monolith that serves nothing and can be switched off. When that number stops dropping, the migration has stalled, and the burndown surfaces the stall while it is still recoverable rather than after a year of drift.

As capabilities accumulate in the new architecture, the new system itself starts to need the patterns a distributed system requires, and the migration becomes an opportunity to adopt them deliberately. Inter-service communication, resilience against partial failure, and consistent observability across services are concerns the monolith handled implicitly through in-process calls and now have to be designed explicitly. The microservices reference architecture linked earlier covers how the target system should be shaped, and the strangler migration is the vehicle that gets you there one capability at a time rather than all at once.

## Observability for a strangler migration

You cannot run a strangler migration safely without strong observability, because every routing flip is a hypothesis that the new service behaves like the old one, and observability is how you test the hypothesis in production. The facade is the ideal place to instrument, because every request passes through it, so the facade can emit a consistent record of which system served each request, the latency, and the outcome. With that data you can compare the new service's behavior against the monolith's baseline for the same capability, which is the evidence that lets you ramp traffic with confidence and the signal that triggers a rollback when something regresses.

The comparison harness deserves first-class treatment. During a mirrored run, the facade sends a copy of production traffic to the new service while the monolith remains authoritative, and a comparison component diffs the two responses. Differences fall into three buckets: genuine bugs in the new service, acceptable differences like a reformatted timestamp, and differences caused by the two systems reading slightly different data because of replication lag. Triaging these before the routing flips is how you catch the edge cases the new code missed, and the rate of unexplained differences is a direct measure of how ready the slice is to take real traffic. A slice with a falling difference rate is converging on correctness; a slice with a stubborn difference rate has a real problem you have not understood yet.

Distributed tracing across the facade, the monolith, and the new services ties a single user request to every system that touched it, which is what lets you debug a problem that spans the boundary during coexistence. When an order looks wrong, you need to see whether the facade routed it to the new service or the monolith, what the new service did, and whether replication had caught up, all on one trace. Wiring this up early, ideally in phase one before any capability moves, means the visibility is there when you need it rather than something you scramble to add during an incident. The metrics, traces, and the comparison data together form the control surface for the migration, and a team that invests in that surface ships slices faster and rolls back less often because they can see what is happening instead of guessing.

You can practice building this control surface, and the routing and coexistence mechanics around it, against realistic Azure topologies in a sandbox rather than learning them for the first time on a production monolith. Standing up a facade, a monolith stub, a new service, replication between their stores, and a comparison harness, then migrating a write slice through all four phases, is the exercise that turns the pattern from a diagram into a skill, and the [hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) is built for exactly that kind of end-to-end rehearsal.

## Routing strategies the facade can express

The migration map names a routing rule for each slice, and the rule you choose shapes how safely you can ramp and how precisely you can target. The facade gives you several routing strategies, and a mature migration uses different ones for different slices depending on the risk profile and the audience the slice serves.

Path-based routing is the most common and the most legible. The facade matches the request path against a rule and sends matching requests to the new service. Path routing fits any capability whose contract maps to a distinct route, which is most of them, and it is the rule type both Application Gateway URL path maps and APIM operation policies express naturally. The strength of path routing is that it is easy to reason about and easy to revert; the limit is that it is all-or-nothing for a path unless you combine it with weighting.

Weighted or percentage routing is what turns a cutover into a canary. Instead of flipping all traffic for a path at once, the facade sends a small fraction to the new service and the rest to the monolith, and you raise the fraction as the metrics stay healthy. This is the safest way to move a high-volume capability, because a problem shows up at one percent of traffic where it affects few users and triggers a rollback before it reaches everyone. Front Door's weighted origin groups and APIM's policy-based splitting both implement this, and the comparison harness pairs naturally with it, since the small initial slice of real traffic is also the sample you diff against the monolith.

Identity-based or cohort routing sends specific users to the new service while everyone else stays on the monolith. You might route internal employees first, then beta customers, then everyone, so the people most tolerant of a rough edge meet it first and the people least tolerant meet it last, after it is proven. This requires the facade to read identity, which APIM does well through its Microsoft Entra ID integration, and it gives you a controlled rollout that follows your risk appetite rather than a blunt percentage. The tradeoff is that cohort routing needs the facade to understand who the caller is, which couples it more tightly to your auth model, so reserve it for slices where the controlled audience is worth that coupling.

### Can I combine routing strategies on one slice?

Yes, and mature migrations usually do. A typical safe rollout routes by path to scope the capability, by cohort to start with internal users, and by weight to ramp the percentage within that cohort. The facade evaluates the rules in order, so you can express compound conditions that target precisely who meets the new service and when, which is exactly the control a high-risk write slice needs.

Combining strategies is how you match the rollout's caution to the slice's risk. A read slice might use plain path routing and ramp to full traffic in a day, because the downside of a mistake is small. A write slice that touches money might use path plus cohort plus weight, starting with internal accounts at one percent, because the downside of a mistake is large and the extra precision buys you time to catch a problem against a forgiving audience. The facade's job is to make all of these expressible as configuration, so the team can dial the caution up or down per slice without changing application code.

## A second example, migrating a write-heavy capability

The order walkthrough showed the four phases on a capability with moderate write volume. A write-heavy capability like inventory, where stock counts change constantly and many readers depend on them being current, stresses the data-coexistence machinery harder and is worth walking through to see where the strategy bends.

Inventory is hard because it is both write-heavy and read-everywhere. Orders decrement stock, restocks increment it, and nearly every other capability reads it to decide whether an item can be sold. You cannot move inventory writes to a new service and leave the monolith reading a stale copy, because the monolith would oversell. The coexistence strategy therefore has to keep the monolith's view of inventory current with very low lag during the window where the monolith still serves capabilities that read stock. Change data capture with a tight, measured lag is the usual mechanism, and you validate that the lag sits well inside the tolerance that prevents overselling before you flip writes.

The sequencing also changes. With inventory you may keep the new service as the single writer but maintain bidirectional currency longer than usual, because so many monolith capabilities read stock that you cannot retire the monolith's inventory copy until most of those readers have themselves been migrated. The inventory slice's data-coexistence field in the migration map therefore names a replication that outlives the routing cutover by months, and the slice is not fully decommissioned until the last monolith reader of inventory is gone. This is the gradual-at-the-data-layer reality made concrete: the routing flip for inventory writes happens in an afternoon, but the data coexistence for inventory persists until the surrounding capabilities catch up.

The rollback for a write-heavy slice is where the rehearsal pays off. If inventory writes regress after the flip, routing back to the monolith is only safe because the change-data-capture stream kept the monolith's stock counts current as a follower, so the monolith resumes as authoritative writer against an accurate count. A team that flipped inventory writes without that follower stream would find, on rollback, that the monolith's stock counts were frozen at the moment of cutover and every sale since then had vanished from its view, which would cause exactly the overselling the migration was supposed to avoid. The lesson the inventory example drives home is that for a write-heavy, read-everywhere capability, the data-coexistence strategy is not a detail of the migration, it is the migration, and the routing is the easy part wrapped around it.

## Finding the seams that define a slice

A slice is only as clean as the seam you cut it along, and finding good seams in a tangled monolith is its own discipline. A seam is a boundary where a capability can be separated from the rest of the system with a contract narrow enough that the facade can route it and a data footprint contained enough that coexistence is manageable. The best seams follow business capabilities rather than technical layers, because a business capability like order placement has a natural contract and a natural set of data it owns, whereas a technical layer like the data-access tier cuts across every capability and gives you no routable boundary at all.

Identifying seams starts with mapping what the monolith actually does as a set of capabilities, then for each capability tracing which data it reads and writes. A capability that owns its data, reading and writing tables that no other capability touches, is a clean seam and a good early slice. A capability that shares heavily written tables with several others is a poor seam, because moving it means either moving the shared data too or living with a complex coexistence arrangement for a long time. The mapping exercise usually reveals that the monolith's capabilities cluster into a few natural groups by shared data, and those clusters, not the individual capabilities, are often the real units of migration.

### What if no capability has a clean seam?

Then the honest first work is decoupling inside the monolith to create seams before any slice moves. Introduce internal interfaces, separate the shared tables a capability owns from the ones it merely reads, and break the hidden internal calls that bind capabilities together. Only once a capability has a narrow contract and a contained data footprint is it a candidate to strangle.

This decoupling work is unglamorous and often resisted, because it changes the monolith without delivering a visible migration milestone, but it is what makes the strangler viable for a system that was not built with boundaries. Skipping it produces slices so large and so data-entangled that each one is a mini big-bang, which reintroduces exactly the risk the pattern exists to remove. The investment in seams up front is repaid many times over across the migration, because every clean seam is a slice that moves quickly and rolls back safely, while every ragged seam is a slice that drags and threatens data integrity. The assessment phase of any serious modernization program should produce a seam map, and the order in which you migrate slices should follow the seams from cleanest to most entangled, so the team builds skill on the easy ones before it meets the hard ones.

The anti-corruption layer is the tool that lets a new service have a clean internal model even when the seam it was cut along is ragged. When a capability's data is entangled with the monolith's, the new service still models its own domain cleanly and the anti-corruption layer translates at the boundary, absorbing the monolith's quirks so they do not propagate into the new code. Over the life of the migration the anti-corruption layers are temporary scaffolding: each one exists to bridge a new service to the monolith during coexistence, and each one is removed when the monolith capability on the other side of it is itself migrated and the two services can speak a shared, clean contract directly.

## Security and the facade during migration

Putting a facade in front of everything changes the security picture, and the change is mostly for the better if you use it deliberately. The facade is a single, consistent point to enforce authentication, authorization, rate limiting, and a web application firewall, which is often cleaner than the scattered controls a monolith accumulated over years. During migration you can consolidate security at the facade so that both the monolith and the new services sit behind a uniform front, and the new services can adopt a modern identity model through the facade's integration with Microsoft Entra ID without the monolith having to change its internal auth at all.

The risk to manage is that the facade becomes a high-value target precisely because it sees everything, so it must be hardened and monitored as the critical component it is. You also have to make sure the routing rules cannot be used to bypass a control: a slice routed to the new service must carry the same authorization guarantees the monolith enforced, or the migration quietly opens a hole. Treating the facade configuration as code, reviewed and version-controlled, is part of the security story as well as the operational one, because an unreviewed routing change is also an unreviewed change to who can reach what. The principle of least privilege applies to the facade's own identity too: the facade needs only the access required to route and enforce contracts, and granting it more makes a facade compromise more damaging than it needs to be.

## Validating that a migrated capability matches the original

Routing a slice to the new service is a claim that the new service does what the old one did, and that claim has to be tested, not assumed. The pre-cutover comparison harness gives you confidence before the flip, but validation continues after it. Once the new service is authoritative, you keep watching its behavior against the historical baseline the monolith set, because some differences only appear at full production volume or on the rare paths a mirrored sample never exercised. A capability that looked identical at one percent of traffic can reveal a subtle behavioral gap at full load, and the validation discipline is what catches it while the rollback is still cheap.

Reconciliation is the heaviest tool in the validation kit and the right one for capabilities where correctness is measurable, like financial or inventory data. A reconciliation job periodically compares the authoritative state the new service now owns against an independent calculation or against the replicated copy, and it flags any discrepancy for investigation. For a capability that handles money, a daily reconciliation that proves the new service's totals match what the records imply is worth the effort, because it converts trust in the migration from a feeling into a measured fact. The reconciliation does not have to run forever; it runs through the coexistence window and for a soak period after the slice is declared done, then retires once the capability has proven stable.

The validation evidence also feeds the decision to decommission. You do not delete the monolith's version of a capability on a calendar; you delete it when the validation says the new service has matched the old one across the full range of traffic and at least one complete business cycle, with no unexplained divergence and metrics at or better than baseline. Tying decommissioning to validation evidence rather than elapsed time is what keeps the rollback target alive exactly as long as it might be needed and not a day longer. A capability that the validation cannot vouch for is a capability that is not done, regardless of how long it has been running, and treating it as done is how a silent divergence slips into production and is discovered only by an angry customer or an audit months later.

## The cost and operational reality of coexistence

Running two systems side by side has a price, and a team that does not plan for it will feel the squeeze halfway through the program and be tempted to cut the migration short. During coexistence you are paying for the monolith's infrastructure, the new services' infrastructure, the facade, and the data-replication machinery that keeps the stores consistent, all at the same time. That overlap is unavoidable and it is the cost of avoiding a big-bang risk, but it is also a meter that runs the entire length of the migration, which is the strongest financial argument for moving briskly rather than letting the program drift.

The operational load follows the same shape. On-call now covers the monolith, the new services, and the facade, and an incident can originate in any of them or in the seam between them, so the team's debugging surface is larger during coexistence than it was before or will be after. This is precisely why the observability investment is not optional. A team that can see, on a single trace, which system served a request and whether replication had caught up will resolve a coexistence incident in minutes, while a team flying blind will spend hours guessing which of three systems is at fault. The cost of the observability is small against the cost of a long blind incident, and it pays for itself the first time a cross-boundary problem appears.

The way to keep the coexistence cost bounded is to keep the coexistence window short for each individual capability, even though the overall program runs long. A capability should spend as little time as possible in the half-migrated state where both systems and the replication for it are all running. You achieve this by ramping a slice to full traffic promptly once its metrics are healthy, declaring it done as soon as it has survived its business cycle, and decommissioning the monolith's version without delay. A program that moves each slice decisively, even while the whole migration takes months, pays far less in overlapping cost than one that leaves a dozen capabilities lingering in coexistence simultaneously because no one closes them out. The financial profile of the migration is set less by its total duration than by how many slices sit half-done at any given moment.

## How the target architecture takes shape

A strangler migration is not just a way to leave the monolith, it is a way to arrive at a coherent target, and the target deserves design attention from the start. As capabilities move out of the monolith they stop being in-process function calls and become independent services that communicate over the network, which surfaces concerns the monolith handled implicitly. Two services that used to share memory now exchange messages or make remote calls, and the failure modes of a network call, latency, partial failure, retries, do not exist inside a single process. The migration is the moment to adopt these patterns deliberately rather than discovering them through outages.

Inter-service communication splits into synchronous and asynchronous, and the choice shapes the system's resilience. Synchronous calls are simple to reason about but couple the caller's availability to the callee's, so a slow downstream service can stall an upstream one. Asynchronous messaging decouples the two, letting a service accept work and process it independently, which is why the [event-driven architecture patterns on Azure](/2024/04/22/azure-event-driven-architecture/) are worth adopting as capabilities separate, since the durable log between services also gives the cleaner write-ownership handoff the data section described. The target is rarely all one style; the system uses synchronous calls where an immediate answer is required and asynchronous messaging where the work can be deferred, and the migration is where you decide which is which for each interaction.

The hosting target matters too. As services accumulate they need a platform that gives them scaling, networking, and deployment as first-class concerns, which is what a Kubernetes platform provides and why the microservices reference architecture on Azure Kubernetes Service is the common destination for a strangler program. The strangler is the path; the reference architecture is the place it leads. Designing the target up front, even though you arrive at it incrementally, keeps the accumulating services coherent rather than letting each migrated slice make independent decisions that the system later has to reconcile. A migration that reaches a deliberate, designed target is a modernization; one that reaches a pile of services with no shared design is a distributed monolith, which is the one outcome worse than the monolith you started with.

## Closing verdict

The Strangler Fig pattern is the architecturally correct way to migrate a monolith that the business cannot afford to break. It wins because it converts one enormous irreversible risk into a long sequence of small reversible ones, and because it keeps the proven legacy system serving every capability that has not yet been moved, so the migration never depends on a cutover working on the first try. The route-a-slice-at-a-time rule is the whole pattern in a sentence: move one capability at a time behind a facade, make the rollback a routing change, and the risk of each step stays bounded to that one capability.

The two places teams fail are the two places this article spent the most time. They migrate a write capability without a single-writer data-coexistence strategy and the old and new systems diverge, or they let the migration stall after the easy slices and pay to run two systems forever. Both failures are avoidable with the migration map's discipline: fill in all five fields before you ship a slice, refuse to move a write capability until its data plan names a single authoritative writer, design and rehearse the rollback before the forward route, and track progress as capabilities decommissioned rather than code written. Do that, and a migration that would have been a year-long bet becomes a steady cadence of small, safe, shippable steps that ends with the monolith switched off and the new architecture carrying the business. That ending is the only proof that the migration worked, and it is the ending the pattern is designed to reach. Treat each slice as a complete, reversible unit of work, hold the route-a-slice-at-a-time rule when the pressure to cut corners rises, and the monolith that once felt impossible to replace comes apart one bounded, well-understood capability at a time.

## Frequently Asked Questions

### Q: What is the Strangler Fig migration pattern?

The Strangler Fig pattern is an approach to modernizing a legacy system by replacing it incrementally rather than all at once. A routing layer called a facade sits in front of both the old monolith and a new system, and on every request it decides which one answers based on whether that capability has been migrated yet. Capabilities move one at a time, the old and new run side by side during the transition, and the legacy system is decommissioned only when nothing depends on it. Named by Martin Fowler in 2004 after the tropical fig that grows around and eventually replaces its host tree, the pattern bounds the risk of each step to a single capability and makes rollback a routing change rather than a restore, which is why it is the standard alternative to a high-risk big-bang rewrite for any system the business cannot afford to break.

### Q: How does a facade route requests between the old and new systems?

The facade intercepts every incoming request before it reaches either system and applies a routing rule to decide the destination. The rule can match the request path, the HTTP method, a header, the caller's identity, or a weighted percentage, and it sets the backend accordingly. On Azure, API Management expresses this through per-operation policies, Application Gateway through URL path maps, and Front Door through weighted origin groups. A migrated capability's requests go to the new service while everything else flows to the monolith, and because the facade preserves the same external contract, the client never sees the difference. The facade must reliably intercept every request and decide with precision, since any traffic that slips past it bypasses your routing and any imprecision forces you to migrate in chunks larger than a single capability.

### Q: How do I incrementally replace a monolith with microservices on Azure?

Start by placing a facade such as API Management in front of the monolith with all traffic still routed through to it, so the routing layer is proven before anything moves. Map the monolith into business capabilities and find the ones with clean contracts and contained data. Migrate the easiest read-only capability first, ramping traffic from a small percentage to all of it while watching metrics, then graduate to write capabilities with a single-writer data-coexistence strategy. Each capability moves through introduce-facade, migrate-reads, migrate-writes, and decommission phases, and you repeat the cycle capability by capability until the monolith serves nothing. Track progress as capabilities decommissioned, not code written, and keep every step reversible by routing so a regression returns traffic to the monolith in seconds.

### Q: Should I use API Management, Front Door, or Application Gateway as the facade?

Choose by scope and routing granularity. Use API Management when the monolith exposes an API and you need per-operation policy control, request transformation, and an API surface, since its policies can route a single endpoint while leaving the rest on the monolith. Use Front Door when you need a global edge, weighted canary routing across regions, and a web application firewall at the edge. Use Application Gateway when the workload is single-region and path-based and you want the facade inside your virtual network. The three are not mutually exclusive, and a common production shape layers Front Door at the edge for global reach and weighting with API Management behind it for fine-grained policy. Verify the current feature set and limits of each against the official Azure documentation before committing, because capabilities change.

### Q: How do I avoid dual-write inconsistency when moving a write capability?

Never write the same data to both the old and new stores in the same operation, because there is no transaction across two systems and a failure between the writes leaves them inconsistent with no clean recovery. Instead enforce single-writer ownership: before the cutover the monolith is the sole writer and the new store is kept current by replication, and at the cutover the new service becomes the sole writer while replication reverses so the monolith's store becomes the follower. There is exactly one authoritative writer at every instant, and the transition is a change of direction rather than a window of concurrent writing. For cases where a write must update a store and notify another system atomically, use the transactional outbox pattern, writing the state change and the outgoing event in one local transaction and relaying the event afterward.

### Q: How long does a typical strangler fig migration take?

It depends entirely on the number of capabilities, how cleanly they decompose, and how much data entanglement exists, so any fixed estimate would be invented. What is reliable is the shape: the migration runs as long as it takes to move every capability one slice at a time, often months for a substantial monolith and sometimes longer when heavy decoupling work is needed first to create seams. The pattern's value is not that it is fast but that it delivers value continuously throughout, since each migrated slice is shippable on its own, rather than producing nothing until a final cutover. Track the duration against a burndown of capabilities still served by the monolith, and treat a flattening curve as the early warning that the migration is stalling rather than progressing.

### Q: Can the facade become a single point of failure?

Yes, and it is the most legitimate objection to the pattern, because the facade sees every request, so an outage there takes down even the capabilities the monolith would otherwise serve fine. The mitigation is to choose a facade that is itself highly available, configure redundancy and health-based routing, and treat the facade with the operational seriousness its position demands. Front Door is a global multi-region service designed to absorb regional failure, and API Management and Application Gateway both offer redundancy options. Equally important, keep the facade dumb: the more business logic you push into the routing layer, the larger the blast radius of any facade change and the more likely a routing edit breaks something. The facade coordinates traffic and enforces contracts, and it should not run the business.

### Q: How do I canary a new service before sending it all traffic?

Use weighted routing at the facade to send a small fraction of a capability's traffic to the new service while the rest continues to the monolith, then raise the fraction as the metrics stay healthy. Front Door's weighted origin groups and API Management's policy-based splitting both implement this. Pair the canary with a comparison harness that mirrors traffic to the new service and diffs its responses against the monolith's, so you catch behavioral differences on the small initial slice before they reach more users. Define the rollback trigger in advance as a measurable threshold on error rate, latency, or divergence, and wire it into alerting so the signal that should cause a rollback is the same one that pages the on-call engineer. Ramp only while the difference rate falls and the metrics hold at or better than baseline.

### Q: What is an anti-corruption layer and do I need one?

An anti-corruption layer is a translation boundary that converts between the monolith's data model and the new service's model, so the legacy design does not leak into your new code. When the new service reads monolith data, consumes monolith events, or temporarily writes to a monolith-owned store, the layer maps between the two representations. You need one whenever the new service should have a cleaner domain model than the monolith, which is almost always, because without it the new system inherits the monolith's quirks and naming and ends up as a monolith with a different deployment target. Treat the anti-corruption layer as temporary scaffolding: each one bridges a new service to the monolith during coexistence and is removed once the capability on the other side is itself migrated and the two can speak a shared clean contract directly.

### Q: How do I migrate a capability whose data many other capabilities read?

Keep the monolith's view of that data current with very low replication lag for the entire window in which the monolith still serves capabilities that read it. For something like inventory, where stock counts change constantly and nearly everything reads them, you make the new service the single writer at cutover but maintain a change-data-capture stream that keeps the monolith's copy accurate, so the monolith does not oversell against a stale count. The data-coexistence arrangement therefore outlives the routing cutover, sometimes by months, and the capability is not fully decommissioned until the last monolith reader of that data has itself been migrated. Measure the replication lag under real write volume and confirm it sits inside the tolerance the readers require before you flip writes.

### Q: Does the Strangler Fig pattern require downtime?

No, and avoiding downtime is one of its main reasons to exist. Because the facade preserves the external contract and routes capability by capability, clients keep talking to the same address throughout, and each capability moves with real production traffic rather than during a maintenance window. Inserting the facade in the first phase is transparent because all traffic still flows to the monolith, and each subsequent routing flip is a configuration change that can be ramped gradually and reverted instantly. The only theoretical exception is a capability whose data cutover genuinely cannot be made atomic, but the single-writer replication strategy is designed precisely to avoid that, transferring write ownership as a change of direction rather than a stop-the-world event. Done correctly, a strangler migration runs entirely during business hours with no scheduled downtime.

### Q: What happens if the migration stalls partway?

A stalled migration is the most expensive state to be in, because you are paying to operate, secure, and maintain two systems plus a facade indefinitely while getting none of the decommissioning benefit. Stalls usually happen organizationally rather than technically: the team moves the easy read slices, declares early victory, and leaves the hard write capabilities and data dependencies untouched. The defenses are to sequence the hard slices deliberately instead of only picking low-hanging fruit, to track progress as a visible burndown of capabilities still on the monolith, and to hold the program accountable for retiring the monolith. If an organization will not commit to finishing, it is better not to start, because the half-migrated state combines the costs of both architectures with the benefits of neither.

### Q: How do I handle authentication differences between the monolith and new services?

Use the facade as the consolidation point for authentication and authorization so both systems sit behind a uniform front. API Management integrates with Microsoft Entra ID and OAuth2, which lets the new services adopt a modern identity model through the facade without the monolith having to change its internal auth at all. The critical rule is that a capability routed to the new service must carry the same authorization guarantees the monolith enforced, or the migration quietly opens a security hole. Validate that the new service enforces equivalent access control before you flip its routing, and treat the facade configuration as reviewed, version-controlled code, since an unreviewed routing change is also an unreviewed change to who can reach which capability. Apply least privilege to the facade's own identity as well.

### Q: Can I use the Strangler Fig pattern to migrate from on-premises to Azure?

Yes, and it is a strong fit for an on-premises to cloud move when downtime is unacceptable. The facade sits in front of both the on-premises monolith and the new Azure-hosted services, routing each capability to wherever it now lives. You migrate capabilities into Azure one at a time, keeping the on-premises system authoritative for everything not yet moved, with hybrid connectivity linking the facade and the data-replication path across the boundary. The data-coexistence strategy carries extra weight here because replication now crosses the network between your datacenter and Azure, so you must measure that lag carefully and account for the connectivity's reliability. The broader assessment of whether a workload is ready for this should come first, since a system with no seams needs decoupling work before a cross-environment strangler becomes practical.

### Q: How is the Strangler Fig pattern different from a feature flag?

A feature flag toggles behavior inside a single deployed system, while the Strangler Fig routes a request to one of two separate systems at an external facade. Feature flags are a fine complement and you might use one inside a new service to control a sub-behavior, but they do not give you the core strangler property of running an old and a new system side by side with independent deployment and a routing-based rollback that returns traffic to a wholly separate, proven legacy system. The facade operates above the systems rather than within one of them, which is what lets you migrate capability by capability across a system boundary and ultimately decommission the old system entirely, something a feature flag cannot accomplish because it lives inside the code it would need to retire.

### Q: What metrics should I watch when ramping traffic to a new service?

Watch error rate, latency at representative percentiles, and behavioral divergence from the monolith baseline, and watch them for the new service specifically rather than only in aggregate, since a problem at one percent of traffic is invisible in a blended number. The comparison harness's rate of unexplained differences is the leading indicator of readiness: a falling difference rate means the new service is converging on correct behavior, while a stubborn one signals a real problem you have not yet understood. Define rollback triggers as thresholds on these metrics before you ramp, and route them into the same alerting that pages on-call, so a regression that should cause a rollback does so automatically rather than depending on a stressed engineer's judgment. Distributed tracing across the facade, monolith, and new services lets you debug a problem that spans the boundary.

### Q: Do I need a separate database for each new service from day one?

Not necessarily, and forcing it too early adds risk. For a read-only first slice the new service can read directly from the monolith's database, which guarantees it sees exactly what the monolith would and eliminates divergence while you validate the service. That direct read couples the new service to the monolith's schema, which you do want to escape eventually, so it is a transition tactic rather than a permanent design. You introduce the new service's own store, kept current by replication, when you move write ownership and need to break the schema coupling. The sequencing, shared read first, then own store at write cutover, lets you defer the harder data work until the new service has proven itself on reads, rather than taking on schema separation and behavioral validation at the same time.

### Q: When should I remove the facade entirely?

Remove the facade only after the legacy system is fully decommissioned and clients can talk directly to the new system without any routing decision left to make. In Microsoft's four-phase description this is the final phase: once every capability has migrated and the monolith serves nothing, the facade has no remaining routing work, and you can retire it so clients address the new system directly. In practice many teams keep a gateway in place permanently because it still provides value as an API gateway, a security boundary, and an edge, even after migration is complete, in which case you are not removing the facade so much as repurposing it from a migration tool into a standing part of the architecture. The decision is whether the routing layer earns its keep once the migration that justified it is over.
