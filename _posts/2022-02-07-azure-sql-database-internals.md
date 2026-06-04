---
layout: post
title: "Azure SQL Database Internals Explained"
page_title: "Azure SQL Database Internals Explained: Service Tiers, vCore vs DTU, Hyperscale, and High Availability for Engineers"
date: 2022-02-07
categories: ["Technology"]
tags: ["Azure", "Azure SQL Database", "Databases", "PaaS", "High Availability", "Hyperscale", "Architecture"]
excerpt: "Azure SQL Database internals decoded: how service tiers map to storage and replica architecture, why throttling is not an outage, and how to pick right."
image: "/assets/images/blog/blog-51.webp"
reading_time: 60
author: "marcus-hall"
last_updated: 2022-02-07
lang: en
---
Most teams adopt Azure SQL Database the way they would order a laptop: they pick a number that sounds big enough, accept the default, and discover the consequences in production. The number turns out to govern far more than raw speed. In Azure SQL Database the service tier you choose silently selects how your data is stored, how many copies of it exist, where those copies live, how a failure is absorbed, and what latency a single committed write will cost. The gap between using the platform and understanding it is exactly this: a developer who treats the tier as a performance slider will be surprised by latency, by throttling that looks like an outage, and by a recovery story they never designed. An engineer who reads the tier as a choice of internal architecture will provision the right shape on the first attempt and reason confidently about why it behaves the way it does.

![Azure SQL Database internals: service tiers, vCore and DTU purchasing models, and high availability architecture - Insight Crunch](/assets/images/blog/blog-51.webp)

This guide takes the platform apart at the level a working engineer actually needs. It covers the deployment options and what each is for, the two purchasing models and how they map to physical resources, the three service tiers and the genuinely different storage and replica architectures hiding under each name, the resource governor that produces throttling, and the high availability and failover design that decides your recovery objectives. The aim is a mental model durable enough that you can stand in a design review, defend a tier choice by naming the deciding factor, and explain what a committed transaction costs in milliseconds on the architecture you picked.

## What Azure SQL Database actually is

Azure SQL Database is a fully managed relational database platform built on the same database engine that powers SQL Server, exposed as a service so that you never touch the operating system, the patching cycle, the backup jobs, or the failover plumbing. What you get is a logical database with a T-SQL surface that is largely compatible with a modern SQL Server, plus a control plane that handles provisioning, scaling, patching, automated backups, and high availability on your behalf. What you give up is direct access to the box: there is no operating system to log into, no SQL Server Agent in the single-database model, no cross-database queries in the way an on-premises instance allows, and no instance-level configuration knobs. The platform trades control for operational relief, and the whole point of understanding its internals is knowing precisely which controls you traded away and what the platform does in their place.

The mental model to hold is a separation of three layers. There is a logical server, which is a connection and administration endpoint, not a machine, and which groups databases for shared login and firewall configuration. There are databases, which are the units of compute, storage, and billing. And underneath both there is a physical fabric of compute nodes, storage, and replicas that the platform manages and that you never name directly. The tier and purchasing model you select are instructions to that fabric about how to assemble the physical resources behind your logical database. When you grasp that the logical name is stable while the physical assembly underneath it can be local SSD with synchronous replicas in one tier and remote page servers in another, the otherwise confusing differences in latency, cost, and recovery behavior become a single coherent picture.

### Is Azure SQL Database the same engine as SQL Server?

Yes, in the sense that matters for queries and largely the same for T-SQL, and no, in the sense that matters for operations. Azure SQL Database runs the latest stabilized database engine continuously updated by Microsoft, so your queries, indexes, and most stored procedures behave as they would on a current SQL Server, but instance-level features, the file system, and the surrounding management surface differ substantially.

This compatibility is why a migration from SQL Server often succeeds at the query layer with little change, and why it can still fail at the feature layer when an application leans on something the single-database model does not expose. The engine understands your T-SQL; the platform may not host the instance-scoped feature your application assumed was always there. That distinction, query compatibility high and instance compatibility partial, is the single most useful thing to internalize before planning any move onto the platform.

## The deployment options and what each is for

Before the tier conversation begins, you choose a deployment model, and this choice frames everything after it. Azure SQL Database offers three shapes: the single database, the elastic pool, and the managed instance. Each answers a different question about how many databases you run and how much instance-level surface you need.

A single database is one database with its own dedicated set of resources. It is the cleanest unit of the platform, billed and scaled on its own, and it suits an application that owns one database whose load is reasonably predictable or whose scaling you want to control directly. The resources you assign, whether expressed in DTUs or vCores, belong to that database alone, which makes its performance easy to reason about and its cost easy to attribute, at the price of paying for headroom each database holds in reserve even when idle.

An elastic pool is a set of databases that share a single allocation of resources. Instead of giving every database its own dedicated compute, you give the pool a budget and let the databases inside it draw from that shared budget as their individual loads rise and fall. The pool is the right shape for a multi-tenant or software-as-a-service pattern where you operate many databases whose peaks do not coincide: tenant A spikes at nine in the morning while tenant B spikes in the evening, and the pool lets them share the same compute rather than each paying for a peak it hits rarely. The deciding factor for a pool is correlation of load. When many databases peak together, the pool must be sized for the sum of the peaks and saves nothing; when their peaks are staggered, the pool can be sized for the aggregate rather than the sum and the savings are real.

A managed instance is a different animal. It is a near-complete SQL Server instance delivered as a managed service, with instance-scoped features that the single-database and pool models do not provide: cross-database queries within the instance, the SQL Server Agent, the Service Broker, linked servers, and a far higher compatibility surface for code written against an on-premises instance. You reach for a managed instance when an application depends on instance-level features that the single database cannot offer, which is the precise condition that should drive the choice rather than a vague sense that a managed instance is the more powerful option.

### When do I need a managed instance instead of a single database?

Choose a managed instance when your workload depends on instance-scoped capabilities that the single-database model does not expose, such as cross-database queries inside one instance, the SQL Server Agent, Service Broker, or linked servers. If your application uses only database-scoped features, a single database or an elastic pool is simpler and usually cheaper.

The mistake worth avoiding is selecting a managed instance for its perceived power when a single database would serve, because the managed instance carries a higher floor cost and a larger management surface. Let the feature dependency, not the prestige of the name, make the call. If you can enumerate the instance-level features your code actually invokes and the list is empty, the single database is the correct and leaner choice, and the broader engine-choice question of relational against other models is one we take up in the comparison of [Azure SQL against Cosmos DB and PostgreSQL](/2025/05/05/azure-sql-vs-cosmos-vs-postgres/) when the question is whether a relational engine fits at all.

## The two purchasing models and how they map to resources

Within the single-database and pool models you choose a purchasing model, and there are two: DTU and vCore. They are two languages for describing the same underlying resources, and the difference between them is whether the platform bundles those resources for you or lets you specify them separately.

The DTU model, where DTU stands for database transaction unit, bundles compute, memory, and IO into a single blended metric. You buy a number of DTUs, and behind that number the platform has chosen a fixed ratio of processor, memory, and IO throughput. The appeal is simplicity: one dial, one number, one bill, and for a small or steady workload that does not need to tune the mix, the DTU model is genuinely the easier path. The limitation is that the ratio is fixed. If your workload is memory-hungry but light on processor, or processor-hungry but light on IO, the blended unit forces you to buy along all three axes to satisfy the one that is constrained, and you pay for the dimensions you did not need.

The vCore model unbundles the resources. You choose a number of virtual cores, a memory allocation that scales with those cores on a given hardware generation, and a storage size and type, each more or less independently. The vCore model is the path for any workload large enough or specific enough to benefit from sizing the resources to the actual bottleneck, and it is the only model that unlocks the higher service tiers and the most capable hardware. It also enables the licensing benefit that lets organizations with existing SQL Server licenses reduce the compute rate, which for a large estate is a material cost lever worth confirming against the current pricing terms.

### Should I use the DTU or vCore purchasing model?

Use vCore for anything beyond a small, steady workload, because it lets you size processor, memory, and storage to the actual constraint and unlocks the higher tiers and hardware. Use DTU only for small or predictable databases where the simplicity of a single blended dial outweighs the loss of control over the resource mix.

The practical rule is that vCore is the default for production of any consequence and DTU is a convenience for the low end. The vCore model also exposes a serverless compute tier within General Purpose, where compute scales automatically between a minimum and maximum and pauses entirely after an idle window, billing only for the seconds it runs. Serverless fits intermittent and unpredictable workloads, development and test databases, and any database whose idle time is a large fraction of the day, with the trade-off that a paused database takes a short time to resume on the next connection. For workloads where that resume latency on the first hit is unacceptable, the provisioned compute path keeps the database always warm at a steady rate.

## The three service tiers and the architecture under each

This is where the platform's internals reward study, because the tier is not a performance setting layered over one architecture. Each tier is a genuinely different storage and replica design, and the tier-equals-architecture rule is the single most useful frame for the whole platform: in Azure SQL Database the service tier is not a performance dial but a choice of internal architecture, so picking the tier is really picking how the database stores and replicates data. Name the architecture you want and the tier follows; pick a tier by its price tag and you inherit an architecture you may not have wanted.

The General Purpose tier separates compute from storage. The database engine runs on a compute node, and the data and log files live on remote storage, reached over the network rather than sitting on a disk attached to the compute node. This separation is what makes General Purpose economical and what makes its failure recovery straightforward: if the compute node fails, the platform spins up a new compute node and reattaches the same remote storage, so no data copy is required to recover, only a reattach and a recovery of the database. The cost of the separation is latency. Every read that misses the local cache and every log write must cross the network to the remote store, so General Purpose carries higher and more variable IO latency than a tier with local storage. For a great many workloads this latency is entirely acceptable, and General Purpose is the correct default. For a latency-sensitive transactional workload it is the wrong default, and choosing it by price is the classic mistake.

The Business Critical tier puts the data on local SSD attached directly to the compute node and maintains several synchronous replicas of the database, arranged as an availability group behind the scenes. Because the data sits on local SSD rather than remote storage, read and write latency are markedly lower and more predictable, which is why Business Critical is the tier for latency-sensitive online transaction processing. Because there are multiple synchronous replicas, a failure of one node is absorbed by promoting another that already holds an up-to-date copy, so failover is fast and no data is lost in the synchronous set. As a bonus, one of those replicas is readable, giving you a built-in read scale-out endpoint at no extra compute. The cost is exactly what you would expect: maintaining several full copies on local SSD is more expensive than one copy on remote storage, and you pay for the resilience and the latency you bought.

The Hyperscale tier is architecturally distinct from both. Rather than storing the whole database as files on one node's storage, Hyperscale decomposes storage into a tier of page servers, each responsible for a slice of the database's pages, fronted by a layer of caching on the compute node and backed by a separate log service that durably records changes. This decomposition is what lets Hyperscale grow storage far beyond the limits of the file-based tiers and add read replicas quickly, because a new replica attaches to the shared page-server tier rather than copying the entire database. It also changes the backup and restore story: because storage is snapshot-based at the page-server layer, backups are nearly instantaneous regardless of database size, and restore times are driven by the snapshot mechanism rather than by streaming the whole database back. Hyperscale fits very large databases and workloads that need rapid read scale-out or fast restore at size, and it is the answer to the question of what to do when a database has outgrown the storage ceiling of the other tiers.

### Which Azure SQL service tier should I choose?

Choose General Purpose for the broad middle of workloads where moderate IO latency is fine and cost matters. Choose Business Critical for latency-sensitive transactional workloads that need the lowest, most predictable IO and fast failover. Choose Hyperscale for very large databases or workloads needing rapid read scale-out and fast restore at size.

The deciding factor is never the headline number; it is the IO latency profile your workload tolerates and the storage size and recovery behavior you require. The InsightCrunch Azure SQL tier decision table below maps the workload profile to the tier, the purchasing model, and the high availability architecture, with the deciding factor named on each row, so the choice is made on the architecture the workload forces rather than on the tier the price suggests.

| Workload profile | Tier | Purchasing model | Storage and HA architecture | Deciding factor |
|---|---|---|---|---|
| Steady or moderate OLTP, cost-sensitive | General Purpose | vCore (or DTU for the low end) | Remote storage separated from compute; recover by reattaching storage to a fresh node | Tolerates remote-storage IO latency to save cost |
| Latency-sensitive OLTP, fast failover required | Business Critical | vCore | Local SSD with several synchronous replicas as an availability group; one replica readable | Needs the lowest, most predictable IO and near-zero-loss failover |
| Very large database, rapid read scale-out, fast restore at size | Hyperscale | vCore | Page-server storage tier with a log service; snapshot-based backup and fast replica attach | Database has outgrown file-based storage limits or needs fast scale and restore |
| Intermittent or unpredictable load, dev and test | General Purpose serverless | vCore serverless | Remote storage; compute autoscales and pauses when idle | Idle time is a large share of the day and resume latency is acceptable |
| Many databases with staggered peaks (SaaS) | Any tier, elastic pool | vCore or DTU pool | Shared resource budget across databases in the pool | Peaks do not coincide, so shared compute beats per-database dedicated compute |

This table is the findable artifact of the article, and the namable claim it encodes is the tier-equals-architecture rule. Treat the table as the starting point of a tier decision and the rule as the sentence you say out loud in the design review to justify it.

## The resource governor and why throttling is not an outage

A subtlety that trips up many teams is that Azure SQL Database does not let a database consume resources without limit and then fail when the box runs out. Instead, a resource governor continuously enforces the resource ceilings implied by your tier and size: a cap on processor, a cap on memory, a cap on data IO, a cap on log write throughput, a cap on the number of concurrent workers and sessions, and a cap on the rate of certain operations. When a workload pushes past one of these ceilings, the platform does not crash; it throttles, slowing or queuing the work that exceeds the cap and, in some cases, returning a specific error that tells the client the limit was hit.

Reading this behavior correctly is the difference between a five-minute fix and a misdirected incident. A database pinned at its processor or log-IO ceiling and consequently slow is not experiencing an outage; it is experiencing resource governance, the platform doing exactly what it was configured to do at the size you selected. The signal is observable: the platform exposes the consumption of each governed dimension as a percentage of the limit, so you can see which ceiling you are hitting rather than guessing. The fix follows from the dimension. If the bottleneck is a missing index or a regressed plan driving processor far higher than the work requires, the correct response is to tune the query, which we treat in depth in the [Azure SQL performance tuning guide](/2024/08/19/azure-sql-performance-tuning/), and which is almost always cheaper than buying a larger tier. If the workload genuinely needs more of a dimension than the size provides, scaling up is the right answer, but only after you have confirmed the dimension rather than reflexively upgrading. The throttling-specific error behavior and the diagnosis of which dimension is constrained are covered in the dedicated treatment of [Azure SQL DTU and throttling errors](/2022/08/29/fix-azure-sql-dtu-throttling/).

### Why does my Azure SQL Database slow down instead of failing under load?

Because a resource governor enforces the processor, memory, IO, log, and worker limits implied by your tier and size, and when a workload exceeds a limit the platform throttles the excess rather than crashing. The slowdown is governance working as designed, not a fault, and the consumption percentages reveal exactly which ceiling you reached.

The practical consequence is that you should never diagnose a slow database by assuming a platform fault first. Look at the governed dimensions, identify which one is saturated, and decide between tuning the workload and scaling the resource based on what the data shows. The resource governor is also why two databases at the same nominal tier can behave differently: the one with the efficient query plan stays under its ceilings while the one with the missing index slams into the processor cap and throttles, even though both were given identical resources.

## High availability and failover internals

The high availability story differs by tier because, as established, the tiers are different architectures, and availability is a property of architecture. Understanding the differences lets you state your recovery objectives rather than hope for them.

In General Purpose, high availability rests on the separation of compute and storage. There is effectively one copy of the data on durable remote storage, and the database engine runs on a compute node in front of it. If the compute node fails, or the platform needs to move it for patching, a new compute node is brought up and the same remote storage is reattached, after which the database recovers and resumes serving. No data copy crosses the wire during this process because the storage was never on the failed node, which makes the recovery mechanism simple and the data durable, at the cost of a brief unavailability during the reattach and recovery. The data is protected because remote storage is itself replicated underneath, but the compute layer is a single active node rather than a hot standby.

In Business Critical, high availability is provided by the synchronous replica set. Several replicas each hold a full copy of the database on their own local SSD, kept in sync so that a committed transaction is acknowledged only once it is durable on the synchronous set. If the primary fails, one of the synchronous secondaries is promoted, and because it already holds an up-to-date copy, the failover is fast and loses no committed data within the synchronous group. This is the tier to choose when both low latency and rapid, lossless failover matter, and the readable secondary it provides is a genuine asset for offloading read-only reporting from the primary.

In Hyperscale, the picture changes again because storage is decomposed. The compute layer can fail over to another compute node, and because the durable state lives in the log service and the page-server tier rather than on the compute node, the new compute node attaches to the shared storage layer rather than rebuilding a copy. Read replicas in Hyperscale attach to the same page-server tier, which is why they can be added quickly and why scaling reads does not require duplicating the full database. The recovery behavior is therefore a function of the page-server and log-service design rather than of file-based replicas.

All of this protects against the failure of a node, but none of it protects against the loss of an entire region, and conflating the two is a common and dangerous error. Local high availability keeps the database serving when a node or a zone fails within a region; surviving the loss of a region requires a separate cross-region construct. That construct is the failover group, which maintains a continuously replicated secondary in a paired region and provides a stable listener endpoint so that applications connect to a name that follows the primary across a failover rather than to a fixed server. Setting up and testing that cross-region protection is its own discipline, covered end to end in the guide to [configuring Azure SQL failover groups](/2023/06/12/configure-azure-sql-failover-groups/), and it is the piece most teams forget until a regional event forces the lesson.

### How does high availability work across Azure SQL tiers?

It differs by tier because each tier is a different architecture. General Purpose recovers by reattaching durable remote storage to a fresh compute node. Business Critical promotes one of several synchronous local-SSD replicas for fast, lossless failover. Hyperscale fails compute over to a node that reattaches the shared page-server and log-service storage layer.

The recovery objective you can promise, the recovery point and the recovery time, is therefore set by the tier you chose long before any failure occurs. A team that needs near-zero data loss on failover and chose General Purpose to save money has bought a recovery story that does not meet the requirement, and no amount of operational diligence will change the architecture after the fact. State the recovery objective first, then choose the tier whose architecture delivers it, and then add a failover group if the objective includes surviving a regional loss.

## The connection model and transient faults

A managed platform that patches itself, fails compute nodes over, and scales databases up and down on demand will, by design, occasionally move your database's compute, and during those brief moves the existing connections drop. This is not a malfunction; it is the natural consequence of running on a fabric that maintains itself underneath you. The platform classifies these brief interruptions as transient faults, and the correct application behavior is to retry the operation with a backoff rather than to surface the error to the user as a permanent failure.

The most cited of these is the unavailability error the platform raises when a database is briefly reconfiguring, scaling, or, in the serverless case, resuming from a paused state. Because it is on the transient-fault list, the right response is resilient retry with exponential backoff, and an application that lacks retry logic will turn a routine sub-second reconfiguration into a visible error for a user. The diagnosis and the precise handling, including how to distinguish a transient blip that retry absorbs from a persistent problem that retry merely reveals, are covered in the treatment of [Azure SQL error 40613 and database-unavailable conditions](/2022/08/15/fix-azure-sql-40613-unavailable/). The sibling connection failure, the authentication and login error that looks similar from the application's vantage point but has an entirely different cause, is covered separately in the guide to [fixing the Azure SQL login failed error 18456](/2022/08/22/fix-azure-sql-login-failed-18456/). The architectural point for this deep dive is simply that transient connection drops are an expected property of the managed fabric, that resilient retry with backoff is therefore mandatory rather than optional, and that designing for it from the start prevents a whole class of phantom incidents.

## Configuration and usage that matters

Several configuration choices shape how the platform behaves day to day, and getting them right early prevents the most common surprises.

Scaling is online in the common cases. You can change the vCore count, move between tiers, or grow storage while the database keeps serving, with the change applied through a brief reconfiguration that drops connections momentarily, which is exactly why the retry logic discussed above is a prerequisite for smooth scaling. Treat a scale operation as a transient event the application must absorb, and a vertical scale becomes a routine, low-drama action rather than a maintenance window.

Storage and compute are decoupled in their limits. The maximum database size you can configure depends on the tier and, in the vCore model, partly on the vCore count, and these ceilings differ enough between tiers that a database approaching a storage limit on General Purpose is often the real reason to move to Hyperscale rather than any performance need. Treat the storage ceiling as a first-class input to the tier decision, not an afterthought, and verify the current per-tier maximums against the official documentation because these numbers are raised over time.

Backups are automatic and the retention is configurable. The platform takes regular backups and keeps them for a default retention window that you can extend, and it supports point-in-time restore within that window, restoring to a new database rather than overwriting the original. This is the safety net for accidental data loss, and the operational habit worth building is to know your retention setting and to rehearse a restore before you need one, because a restore you have never tested is a plan you do not actually have.

Security configuration is its own large topic, spanning authentication, network access, and encryption, and it deserves more than a paragraph. The platform supports identity-based authentication that removes stored credentials from the equation, network isolation that closes the public path, and encryption both at rest and, with the right feature, for sensitive columns in use. The full treatment of authentication, network lockdown, and the two encryption models lives in the [Azure SQL security guide on authentication and encryption](/2024/02/26/azure-sql-security-guide/), and any production database should be configured against it rather than left on the permissive defaults.

### Can I scale Azure SQL Database up or down without downtime?

In the common cases yes, scaling is an online operation that keeps the database serving, applied through a brief reconfiguration that momentarily drops connections. Because that brief drop is a transient event, an application with retry-and-backoff logic experiences scaling as a routine change rather than an outage, which is why resilient retry is a prerequisite for smooth scaling.

The nuance is that some operations, particularly certain moves between fundamentally different architectures, take longer than a momentary reconfiguration because data must be reorganized to fit the new storage design. A scale within a tier is fast; a move that changes the underlying storage architecture can take longer and should be planned accordingly. Knowing which of your scale operations is a quick reconfiguration and which is an architectural reshape lets you set expectations correctly before you start.

## Failure modes and how to avoid them

The recurring ways teams get hurt by the platform follow a small number of patterns, and naming them is the cheapest insurance available.

The first pattern is choosing General Purpose for a latency-sensitive transactional workload because its price is attractive, then being surprised that committed writes and cache-missing reads are slower than the application needs. The avoidance is to recognize that the latency comes from the remote-storage architecture under General Purpose, not from insufficient resources, so the fix is the architecture, meaning Business Critical, rather than a larger General Purpose size. No amount of additional vCores changes where the storage lives.

The second pattern is reading throttling as an outage and escalating it as a platform fault, when the resource governor is simply enforcing the limits of the size you bought. The avoidance is to inspect the governed-dimension percentages, identify the saturated dimension, and then decide between tuning the workload and scaling the resource, treating an upgrade as the response to a confirmed shortfall rather than a reflex.

The third pattern is conflating an elastic pool with a managed instance, or reaching for a managed instance when a single database would serve. The avoidance is to keep the two questions separate: the pool answers "how do I share resources across many databases with staggered load," while the managed instance answers "do I need instance-scoped features." Confusing them leads to paying for an instance you did not need or trying to force instance-level behavior out of a single database that cannot provide it.

The fourth pattern is treating local high availability as regional disaster recovery. The avoidance is to remember that the synchronous replicas and the storage reattach protect against node and zone failure within a region but not against the loss of the region, and that surviving a regional event requires a failover group with its secondary in a paired region. Designing the cross-region story only after a regional incident is the most expensive way to learn this.

The fifth pattern is shipping an application without retry logic and then surfacing every routine reconfiguration as a user-visible error. The avoidance is to build resilient retry with backoff from the start, treating transient connection drops as the expected behavior of a self-maintaining fabric rather than as exceptional events.

## When to use Azure SQL Database and when to reach for an alternative

Azure SQL Database is the right choice when your data is relational, your consistency requirements are strong, your query needs are served by T-SQL, and you want a managed platform that removes the operational burden of patching, backup, and failover. Within that envelope, the tier decision tunes the architecture to the workload's latency, size, and recovery needs, and the platform rewards the engineer who chooses on architecture rather than on price.

It is the wrong choice, or at least not the obvious one, when the data shape or scale pattern points elsewhere. A globally distributed workload that needs multi-region writes and tunable consistency is a better fit for a horizontally distributed store, and a workload that is fundamentally non-relational gains little from a relational engine. The full comparison of when a relational engine fits against the alternatives, including a globally distributed document store and an open-source relational option, is laid out in the decision guide for [Azure SQL versus Cosmos DB versus PostgreSQL](/2025/05/05/azure-sql-vs-cosmos-vs-postgres/), and the deeper treatment of the distributed alternative lives in the [Azure Cosmos DB engineering guide](/2022/02/14/azure-cosmos-db-engineering-guide/). The honest version of this section is that Azure SQL Database is an excellent default for relational, transactional workloads on Azure, and that the decision to use something else should follow from a data-shape or scale argument rather than from novelty.

There is also the choice within the SQL family itself. When an application depends on instance-level features, the managed instance is the right member of the family; when it does not, the single database or the pool is leaner. And when even the managed instance does not provide enough control, for instance because the workload needs operating-system access or an unsupported feature, the remaining option is to run SQL Server on a virtual machine and accept the operational burden in exchange for full control, an option whose cost in management effort should be weighed honestly against the relief the managed platform provides.

## How to think about Azure SQL Database

If you keep one idea from this guide, keep the tier-equals-architecture rule: the service tier is not a performance dial but a selection of internal architecture, so choosing a tier is choosing how your data is stored, replicated, and recovered. From that single idea the rest follows. General Purpose separates compute from remote storage and recovers by reattaching it, trading IO latency for cost. Business Critical keeps data on local SSD with synchronous replicas, trading cost for the lowest latency and fastest lossless failover. Hyperscale decomposes storage into page servers with a log service, trading the file-based simplicity for enormous size, fast read scale-out, and near-instant backup. The purchasing model is the language you use to specify resources, with vCore the default for anything serious and DTU a convenience for the low end. The resource governor enforces the limits of the size you bought and throttles rather than crashes, so a slow database is a governance signal to read, not an outage to escalate. And local high availability is not regional disaster recovery, which is why a failover group exists.

Hold those mechanics together and the platform stops being a pricing slider with mysterious behavior and becomes a system whose every visible property, latency, cost, throttling, and recovery, traces back to the architecture you selected. That is the level of understanding that lets you provision correctly the first time and defend the choice afterward. The same frame extends to the harder decisions that come later, when a workload outgrows a single database and must shard, when a regional objective forces a failover group, or when the bottleneck turns out to be a governed dimension rather than a missing resource. In each case the question is the same one this guide has returned to throughout: what architecture does the workload actually require, and which tier, model, and configuration deliver it.

## Closing verdict

Azure SQL Database is one of the strongest managed relational platforms available, and the engineers who get the most from it are the ones who treat the tier and purchasing model as architectural decisions rather than as numbers to satisfy a budget. Decide the workload's tolerance for IO latency, its storage size trajectory, and its recovery objectives first; let those three inputs select the tier and therefore the architecture; choose vCore unless the workload is small enough that DTU's simplicity wins; and design the application to absorb transient reconfigurations from day one. Add a failover group when the recovery objective includes surviving a regional loss, and lean on tuning before scaling whenever the resource governor reports a saturated dimension. Do those things and the platform behaves predictably and economically; skip them and you will meet the consequences in production, where they are most expensive to fix. To run, provision, and observe these tiers and the resource-governor behavior hands-on, VaultBook provides an interactive lab and sandbox environment with a tested command and template library spanning the Azure CLI, PowerShell, Bicep, and KQL, plus a searchable error and issue reference that pairs each symptom with its root causes, which is the natural next step for turning this model into muscle memory.

## The connection architecture: gateway, redirect, and pooling

A part of the internals that quietly shapes latency and reliability is how a client actually reaches the database, and it is more involved than a single hop to a server. Connections arrive first at a gateway, a regional front door that authenticates the connection, applies firewall rules, and routes the session to the compute node currently hosting the database. There are two policies that govern what happens after that initial routing. Under the proxy policy, every packet continues to flow through the gateway for the life of the connection, which keeps the network path simple and works well across restrictive firewalls but adds a hop to every round trip. Under the redirect policy, the gateway hands the client the address of the compute node and the client then talks to that node directly, removing the gateway from the hot path and lowering latency, at the cost of requiring the client network to permit the broader port range the direct path uses.

For workloads inside the same virtual network or region, the redirect policy is usually the better choice because shaving the gateway hop off every query measurably improves latency on chatty workloads. For clients reaching the database across the public internet or through tightly controlled egress, the proxy policy is often the only path that works. Knowing which policy is in effect explains a class of otherwise puzzling latency differences between two clients hitting the same database, and it explains why a connection that worked from one network fails from another when only the proxy path is permitted.

### Does connection pooling matter on Azure SQL Database?

It matters a great deal, because each connection consumes a worker and the platform enforces a hard ceiling on concurrent workers and sessions tied to your tier and size. Without pooling, a busy application opens and closes connections rapidly and can exhaust the worker limit, producing errors that look like the database is failing when it is actually out of connection capacity.

A connection pool keeps a set of established connections open and reuses them across requests, which both avoids the cost of repeatedly establishing connections and keeps the worker count bounded and predictable. The worker limit is one of the governed dimensions the resource governor enforces, so an application that leaks connections or refuses to pool can hit the worker ceiling well before it exhausts processor or memory, and the symptom, new requests failing to obtain a connection, is easy to misread as a platform fault. Sizing the pool to the application's real concurrency, returning connections promptly, and confirming that the framework's pooling is actually enabled rather than silently disabled are the habits that keep the worker dimension comfortably below its limit. When an application scales out across many instances, the aggregate of all the per-instance pools must still fit under the database's worker ceiling, which is a calculation worth doing before a scale-out rather than discovering under load.

## A reproducible provisioning walkthrough

Reasoning about the tiers is sharper when you can stand each one up and watch it behave, so the following commands provision a logical server and a database in each architecture using the Azure CLI. Treat these as a starting point to adapt; confirm the exact size names and any limits against the current documentation, since the available hardware generations and ceilings change over time.

First, create the resource group and the logical server, which is the administration and connection endpoint rather than a machine:

```bash
az group create \
  --name rg-sql-internals \
  --location eastus

az sql server create \
  --name srv-sql-internals-demo \
  --resource-group rg-sql-internals \
  --location eastus \
  --admin-user sqladmin \
  --admin-password '<a-strong-password>'
```

A General Purpose database in the vCore model, with compute separated from remote storage, is provisioned by naming the General Purpose edition and a vCore-based objective:

```bash
az sql db create \
  --resource-group rg-sql-internals \
  --server srv-sql-internals-demo \
  --name db-general-purpose \
  --edition GeneralPurpose \
  --family Gen5 \
  --capacity 4 \
  --compute-model Provisioned
```

A Business Critical database, which places data on local SSD with synchronous replicas, changes only the edition while keeping the same vCore family, and the difference in behavior, lower IO latency and a readable secondary, comes entirely from the architecture the edition selects:

```bash
az sql db create \
  --resource-group rg-sql-internals \
  --server srv-sql-internals-demo \
  --name db-business-critical \
  --edition BusinessCritical \
  --family Gen5 \
  --capacity 4
```

A serverless General Purpose database, which scales compute automatically and pauses when idle, is created by choosing the serverless compute model and setting the autoscale bounds and the auto-pause delay:

```bash
az sql db create \
  --resource-group rg-sql-internals \
  --server srv-sql-internals-demo \
  --name db-serverless \
  --edition GeneralPurpose \
  --family Gen5 \
  --compute-model Serverless \
  --min-capacity 0.5 \
  --capacity 4 \
  --auto-pause-delay 60
```

A Hyperscale database, with its page-server storage tier, is selected by the Hyperscale edition, and you can provision read replicas at creation time by setting the replica count:

```bash
az sql db create \
  --resource-group rg-sql-internals \
  --server srv-sql-internals-demo \
  --name db-hyperscale \
  --edition Hyperscale \
  --family Gen5 \
  --capacity 4 \
  --read-replicas 1
```

The same shapes express cleanly in infrastructure as code, which is the form you want for anything beyond a demo because it makes the architecture choice explicit and reviewable. A minimal Bicep fragment for a Business Critical database reads as follows, and the edition and family names are the levers that select the architecture and the hardware:

```bicep
resource sqlServer 'Microsoft.Sql/servers@2022-05-01-preview' = {
  name: 'srv-sql-internals-demo'
  location: 'eastus'
  properties: {
    administratorLogin: 'sqladmin'
    administratorLoginPassword: adminPassword
  }
}

resource db 'Microsoft.Sql/servers/databases@2022-05-01-preview' = {
  parent: sqlServer
  name: 'db-business-critical'
  location: 'eastus'
  sku: {
    name: 'BC_Gen5'
    tier: 'BusinessCritical'
    family: 'Gen5'
    capacity: 4
  }
  properties: {
    zoneRedundant: true
  }
}
```

The single most instructive exercise is to provision the same nominal vCore count in both General Purpose and Business Critical, run an identical write-heavy workload against each, and compare the commit latency. The Business Critical database will show markedly lower and steadier write latency, and the reason is not more resources, since the vCore count is identical, but the local-SSD-with-synchronous-replicas architecture against the remote-storage architecture. Watching that difference appear with your own workload is what converts the tier-equals-architecture rule from a sentence you read into an intuition you trust.

## The control plane and the data plane

A distinction that pays off when automating the platform or interpreting an incident is the split between the control plane and the data plane. The control plane is the management surface: it provisions servers and databases, changes their size and tier, configures failover groups, and performs the administrative operations you issue through the portal, the CLI, the Resource Manager API, or infrastructure as code. The data plane is the database engine itself: it runs your queries, enforces transactions, and serves your application's traffic over the database protocol.

These two planes can be affected independently, and recognizing which one is involved sharpens both automation and diagnosis. A control-plane disruption might delay a scale operation or a provisioning request while your existing databases keep serving queries normally, because the data plane is unaffected. Conversely, a data-plane event such as a compute-node failover interrupts query traffic briefly while the control plane remains perfectly able to accept management commands. When you script provisioning and scaling, you are issuing control-plane operations, and their success or failure is separate from whether the database is currently serving traffic. When you design retry logic, you are protecting the data plane against transient interruptions. Keeping the two mentally separate prevents the error of assuming that a slow management operation means the database is down, or that a healthy management surface means query traffic is unaffected, neither of which follows from the other.

## Zone redundancy and maintenance windows

Within a single region, the platform offers a configuration that raises the resilience of the high availability story without crossing into cross-region territory: zone redundancy. When you enable it on a tier that supports it, the replicas that provide local high availability are spread across availability zones, which are physically separate locations within the region with independent power, cooling, and networking. The effect is that the loss of an entire zone, not merely a single node, is absorbed because a replica in another zone takes over. This is a meaningful step up from same-zone high availability for any workload whose availability target justifies surviving a zone failure, and it is a setting to decide deliberately rather than leave at the default, because the difference between surviving a node failure and surviving a zone failure can be the difference between meeting and missing an availability commitment.

The other single-region resilience lever is the maintenance window. The platform periodically performs maintenance that includes brief reconfigurations, and by default these can occur at times the platform chooses. A maintenance window lets you nominate a recurring period, such as a quiet overnight stretch, during which these planned maintenance events are concentrated, so that the brief reconfigurations land when your workload can most easily absorb them rather than during a peak. Configuring a maintenance window does not eliminate the brief connection drops that reconfigurations cause, which is why the retry logic discussed earlier remains necessary, but it does let you steer the predictable maintenance to a time of your choosing. For a workload with a clear daily rhythm, aligning the maintenance window to the trough is a small configuration that meaningfully reduces the chance of a planned reconfiguration colliding with the busiest hour.

### Should I enable zone redundancy on my database?

Enable it when your availability target requires surviving the loss of an entire availability zone rather than just a single node, and when your tier supports it. Zone redundancy spreads the high-availability replicas across physically separate zones within the region, so a zone failure is absorbed by a replica elsewhere in the region rather than taking the database down.

The decision is an availability-objective decision, the same kind that should drive the tier choice. If your target tolerates a zone failure taking the database offline briefly, the default same-zone arrangement may suffice; if it does not, zone redundancy is the in-region answer, and a failover group remains the separate answer for surviving the loss of the whole region. Layering them, zone redundancy for in-region zone failure and a failover group for regional loss, gives a graduated resilience posture that matches the graduated nature of the failures you are defending against.

## Inside a committed transaction: the log path by tier

The deepest reason the tiers behave differently lives in what happens when a transaction commits, because durability of the log is where the architectures diverge most sharply and where write latency is decided. In every tier, a transaction is not considered committed until its log records are durable, but the path those log records take to durability is tier-specific.

In General Purpose, the log is written to the remote storage layer, so a commit must wait for the log write to be acknowledged by storage reached over the network. This network round trip on the commit path is the structural reason General Purpose carries higher write latency, and it is unavoidable in the architecture because the durable copy of the log lives away from the compute node by design. The compute node caches data pages locally to keep reads fast when the cache is warm, but the commit cannot be acknowledged until the log reaches the durable remote store.

In Business Critical, durability is achieved by the synchronous replica set. A commit is acknowledged once the log records are hardened on the local SSD of the primary and replicated to the synchronous secondaries, and because those secondaries are local and the storage is fast SSD rather than remote, the commit latency is both lower and more consistent. The synchronous replication is also what makes the failover lossless within the set: a promoted secondary already holds the committed log, so no committed transaction is lost in the promotion. The cost of this design is the resource it consumes, several full copies kept continuously in sync, which is exactly what the higher price of the tier reflects.

In Hyperscale, the commit path is mediated by the separate log service. Rather than writing the log to files on the compute node or to a single remote store, the engine sends log records to a dedicated log service that durably persists them and then forwards them to the page servers and any replicas. This decoupling of the log from both the compute and the page-server storage is what lets Hyperscale scale storage and replicas independently, and it gives a commit path whose latency is governed by the log service rather than by file-based replication. The architecture is more elaborate than the other tiers precisely because it is solving a harder problem: durability and scale-out at a size the file-based tiers cannot reach.

The practical upshot for an engineer is that write-heavy, latency-sensitive workloads should expect their best commit latency on Business Critical, that General Purpose trades commit latency for cost through its remote-log path, and that Hyperscale's commit behavior is a property of the log service rather than of conventional replication. When a write workload feels slow on General Purpose, the remote-log commit path is the structural cause to suspect before reaching for query-level explanations, though confirming the bottleneck through measurement, as the [Azure SQL performance tuning guide](/2024/08/19/azure-sql-performance-tuning/) lays out, is always the disciplined next step rather than assuming.

## Observing the platform: metrics and the governed dimensions

Because the resource governor enforces a ceiling on each resource dimension, the most useful thing you can observe about a database is how close it is running to each of those ceilings, expressed as a percentage of the limit. The platform surfaces the consumption of processor, data IO, log IO, memory, and the worker and session counts, and reading these together tells you whether the database has headroom or is pressed against a limit, and crucially which limit. A database at modest processor but pinned log IO is constrained on log throughput, a very different situation from one pinned on processor, and the response differs accordingly.

This observation discipline is what turns a vague report of slowness into a precise diagnosis. Rather than asking whether the database is slow, you ask which governed dimension is saturated, and the answer points directly at the fix: a saturated processor with an inefficient plan calls for tuning, a saturated log IO from a write-heavy batch might call for batching changes or a tier with more log throughput, and a saturated worker count points at connection management rather than at compute at all. The platform also records the waits the engine experiences, which reveal what queries are waiting on, and while the detailed query-level interpretation belongs to performance tuning, the high-level habit of correlating a saturated governed dimension with the waits the engine reports is the bridge between the platform view and the query view. Building the reflex to look at the governed dimensions first, before assuming a platform fault or reflexively scaling, is one of the highest-value operational habits for anyone running the platform, and it is the same reflex that prevents the throttling-as-outage misdiagnosis described earlier and treated in depth for the throttling case in the [Azure SQL DTU and throttling errors guide](/2022/08/29/fix-azure-sql-dtu-throttling/).

## Geo-replication versus failover groups

Cross-region protection comes in two related but distinct forms, and choosing between them depends on whether you want the platform to manage the endpoint and the failover policy for you or to keep manual control. Active geo-replication creates one or more readable secondary databases in other regions, continuously replicated from the primary, which you can fail over to manually and which you can also use to serve read traffic close to users in those regions. It gives you fine control: you decide when to fail over and you address each secondary by its own name.

A failover group builds on the same replication but adds management on top. It groups one or more databases, maintains the secondary in a paired region, and provides a stable listener endpoint, a single name that always points at whichever region currently holds the primary, so that applications connect to the listener rather than to a specific server and follow the primary across a failover without changing their connection string. It can also apply an automatic failover policy that promotes the secondary without manual intervention when the platform detects a sustained regional problem, subject to a grace period that prevents a transient blip from triggering an unnecessary regional failover.

The decision rule is straightforward. Choose a failover group when you want the stable listener endpoint and the option of automatic failover, which is the common production choice because it removes the application's need to know which region is primary and removes the human from the critical path of a regional failover. Choose bare active geo-replication when you specifically want manual control over the failover decision or when you are using the secondaries primarily to serve regional read traffic rather than as a disaster-recovery target. The most common mistake is hard-coding a specific server name in the connection string and then wondering why the application does not follow a failover, when the whole point of the listener endpoint is to be the name the application uses. The end-to-end setup, the listener behavior, the automatic policy and its grace period, and how to test a failover safely are covered in the guide to [configuring Azure SQL failover groups](/2023/06/12/configure-azure-sql-failover-groups/), which is the companion to this section for anyone implementing cross-region protection.

## Elastic pool mechanics in depth

The elastic pool deserves a closer look because its economics depend on details that are easy to get wrong. A pool has a total resource budget, expressed in pooled eDTUs in the DTU model or pooled vCores in the vCore model, that all databases in the pool draw from. The savings come from sharing this budget across databases whose peaks are staggered, but the platform also lets you set per-database minimum and maximum limits within the pool, and those limits are the control that makes a pool safe to operate.

The per-database maximum caps how much of the pool's budget any single database can consume, which prevents one busy database from starving the others, the noisy-neighbor problem that would otherwise undermine the shared model. The per-database minimum guarantees each database a floor of resources, which matters when you need to assure a tenant of a baseline regardless of what the others are doing. Tuning these two limits is how you balance the efficiency of sharing against the isolation of dedication: a generous maximum lets a database absorb a spike by borrowing idle pool capacity, while a sensible minimum protects the others from being crowded out. The pool's total budget must still be sized to the realistic aggregate of the databases' loads, and the correlation of those loads is, as established, the deciding factor for whether a pool saves money at all.

The pool is therefore not a way to get something for nothing but a way to convert the gap between the sum of individual peaks and the aggregate peak into savings, with the per-database limits as the safety controls that keep the sharing fair. For a multi-tenant software-as-a-service application with many small-to-moderate databases and staggered usage, a well-sized pool with sensible per-database limits is frequently the most cost-effective shape on the platform, and it is the configuration to reach for before assuming each tenant needs its own dedicated database. When the question broadens from how to host many relational databases to whether a relational engine is the right choice at all, the [comparison of Azure SQL against Cosmos DB and PostgreSQL](/2025/05/05/azure-sql-vs-cosmos-vs-postgres/) is the place that decision is worked through.

## Hardware generations and how resources scale with vCores

In the vCore model the hardware generation you choose is a real lever, not a cosmetic label, because the generation sets the ratio of memory to each vCore, the processor type, and the IO characteristics the platform provisions. A given vCore count on one generation grants a different memory allocation than the same count on another, and for a memory-bound workload the generation can matter as much as the vCore count itself. The platform offers a small family of generations aimed at different balances, with the broadly applicable generation suiting most workloads and the memory-optimized options serving workloads whose working set is large relative to their processor demand.

The reason this matters in practice is that engineers frequently size a database by vCores alone and overlook that the memory came along for the ride at the generation's fixed ratio. A workload that thrashes because its working set does not fit in cache is not necessarily short on processor; it may be short on memory, which on the vCore model is often better solved by a memory-optimized generation than by simply adding vCores on the default generation and paying for processor the workload does not use. Treat the generation as a deliberate choice tied to the workload's memory-to-processor balance, confirm the current generations and their ratios against the official documentation because the lineup is refreshed over time, and you avoid the quiet inefficiency of buying the wrong resource shape. The same reasoning extends to the maximum IO throughput each generation and size permit, which becomes the binding constraint for IO-heavy workloads well before processor does, and which is the kind of limit worth flagging for verification against the current source before committing a production size.

## What you do not control, and why it is mostly fine

Part of understanding a managed platform is knowing which familiar knobs are gone and why their absence rarely hurts. There is no operating system to tune, no manual file placement, no control over the physical storage layout beyond the tier choice, and in the single-database model no SQL Server Agent for scheduled jobs. The platform also manages the system database used for temporary objects, sizing it in proportion to the compute you provisioned rather than letting you configure it directly, which means that a workload leaning heavily on large temporary objects scales its temporary capacity with the vCore count rather than through a separate setting.

For most workloads this loss of control is a relief rather than a constraint, because the platform's automated management of patching, file growth, and the temporary database removes a category of operational toil that on-premises teams spend real effort on. The cases where it bites are specific and worth knowing in advance: a workload that depends on a scheduled agent job in the single-database model needs an external scheduler or a move to a managed instance that provides the agent, and a workload that generates enormous temporary objects may find the temporary capacity tied to compute forces a larger compute size than the steady workload would otherwise need. Recognizing these few genuine constraints before migrating, rather than discovering them after, is the difference between a smooth adoption and a surprised one, and it is exactly the kind of feature-level compatibility question that the move onto the platform turns on.

## Compatibility, migration surprises, and the engine version

Because the engine is largely compatible with SQL Server, migrations often succeed at the query layer with little change, but the surprises that do occur cluster around a few predictable places, and anticipating them prevents a failed cutover. The compatibility level of the database, which governs how the engine interprets certain behaviors and which optimizer features apply, can be set to match an older SQL Server so that a migrated workload behaves as it did before, and then raised deliberately once the workload is validated against the newer behavior. Leaving the compatibility level at the migration default and only raising it after testing is the disciplined path, because a jump in compatibility level can change query plans in ways that occasionally regress a specific query even as it improves others.

The features that most often block or complicate a migration to the single-database model are the instance-scoped ones already named: cross-database queries, the agent, linked servers, and certain instance-level configurations. A workload that depends on these does not fail to migrate so much as it points to the managed instance as the correct target, which is precisely the compatibility-driven targeting that the migration discipline rests on. Assessing the database against the target before moving, rather than discovering an unsupported dependency mid-cutover, is the practice that the dedicated treatment of [migrating SQL Server to Azure SQL](/2025/06/30/migrate-sql-server-to-azure/) builds its whole method around, and the brief version for this deep dive is that query compatibility is high, instance compatibility is partial, and the assessment is what tells you which target the partial features force.

### Will my SQL Server database migrate to Azure SQL Database without changes?

Often the queries and most stored procedures move with little or no change because the engine is largely compatible, but the migration can stall on instance-scoped features the single-database model does not provide, such as cross-database queries, the agent, or linked servers. A workload using those features points to a managed instance rather than a single database.

The reliable approach is to assess the database against the intended target before moving, set the compatibility level to match the source initially, validate the workload, and only then raise the compatibility level deliberately. That sequence keeps the migration's behavior predictable and surfaces any unsupported dependency during assessment rather than during the cutover, when discovering it is most disruptive and most expensive to work around.

## Cost optimization levers specific to the platform

Cost on this platform is largely an architecture-and-sizing problem, and the levers with the highest savings per hour of effort follow directly from the internals already covered. The first and largest lever is choosing the smallest tier whose architecture meets the requirement, because moving from Business Critical to General Purpose when the workload does not actually need local-SSD latency or several synchronous replicas removes the cost of copies and local storage you were not benefiting from. The tier-equals-architecture rule is therefore also a cost rule: you are paying for an architecture, so paying for one you do not need is the most common source of overspend.

The second lever is right-sizing the vCores and the generation to the confirmed need rather than to a cautious guess, which requires the observation discipline of reading the governed dimensions to see how much headroom the database actually carries. A database steadily running far below its ceilings is over-provisioned, and the governed-dimension percentages are the evidence that justifies a reduction. The third lever is matching the compute model to the load pattern: serverless for intermittent and bursty workloads with substantial idle time, an elastic pool for many databases with staggered peaks, and provisioned compute only where steady traffic or strict latency rules out the alternatives. The fourth lever is the commitment-based discount available for steady, predictable workloads, where committing to a level of usage in advance reduces the rate compared with paying as you go, which suits a production database whose baseline is known and stable. The fifth is the license benefit on the vCore model for organizations with eligible existing SQL Server licenses, which lowers the compute rate and can be material across a large estate.

The false economies to avoid are the mirror images of the failure modes. Under-sizing a latency-sensitive workload onto General Purpose to save money is not a saving but a deferred cost paid in poor performance and eventual re-architecture. Skipping the high availability configuration a workload's availability target requires is not a saving but an unhedged risk. And committing to a usage level for a workload whose baseline is not yet stable can lock in spend that right-sizing would have lowered. The durable way to keep cost down is to choose the architecture the workload truly needs, size to the measured demand, match the compute model to the load pattern, and apply commitments and license benefits only where the baseline is genuinely steady, which is the same architecture-first discipline that runs through every other decision on the platform.

## Horizontal scale-out and the limits of a single database

Everything covered so far scales a database vertically, by giving one database more resources or a more capable architecture, and for the large majority of workloads that vertical headroom, especially with Hyperscale's enormous storage ceiling, is enough. There is, however, a point at which a single database, however large its tier, becomes the wrong unit, and recognizing that point is part of understanding the platform's boundaries. When write throughput or working-set size exceeds what a single primary can serve even at the top of the tier range, the answer is no longer a bigger database but more databases, with the data partitioned across them. This is horizontal scale-out, or sharding, and it is a different design discipline from picking a tier.

In a sharded design, the data is divided by a sharding key, such as a tenant identifier or a customer region, so that each shard is an independent database holding a slice of the whole, and the application routes each request to the shard that owns the relevant slice. The platform supports this pattern through elastic database tooling that maintains a shard map, a directory that records which shard owns which range or set of key values, so the application can resolve a key to its shard and connect to the right database. The same tooling provides the means to query across shards when an operation must touch several, and to move data between shards as the distribution evolves, the split-and-merge operations that rebalance a sharded set when one shard grows hot or a new shard is added.

The decision to shard is one to make deliberately and, ideally, late, because it adds real complexity: the application must become shard-aware, cross-shard queries are more expensive and more constrained than queries within one database, and operations such as maintaining referential integrity across shards or running a transaction that spans shards range from awkward to impractical. The discipline that pays off is to exhaust vertical scale-out first, since a single Hyperscale database reaches a size and read-scale that many applications assumed would require sharding, and to shard only when the workload genuinely exceeds what one primary can write or one working set can hold. When that point does arrive, designing the sharding key with the same care you would give a partition key, choosing a key with high cardinality and even distribution so that load spreads across shards rather than concentrating on one, is what determines whether the sharded design scales smoothly or simply relocates the bottleneck.

### When does a single Azure SQL Database stop being enough?

A single database stops being enough when write throughput or working-set size exceeds what one primary can serve even at the top of its tier, since vertical scaling and read replicas cannot raise the write ceiling of a single primary. At that point the answer is to partition the data across multiple databases, a sharded design, rather than a larger single database.

The threshold is genuinely high, particularly with Hyperscale's large storage ceiling and fast read scale-out absorbing many workloads that teams assume will need sharding, so the disciplined sequence is to scale vertically and add read replicas first and to shard only when a single primary's write capacity or working set is the confirmed limit. Sharding adds application complexity and constrains cross-shard operations, so it is a step to take when the workload forces it, with a well-chosen sharding key, rather than pre-emptively. For workloads whose shape suggests a horizontally distributed store from the outset, the broader engine decision in the [Azure SQL versus Cosmos DB versus PostgreSQL comparison](/2025/05/05/azure-sql-vs-cosmos-vs-postgres/) is the place to weigh a natively distributed alternative against a sharded relational design before committing to either.

## Frequently Asked Questions

### Q: How is Azure SQL Database built internally?

Internally the platform separates a logical layer from a physical fabric. A logical server is a connection and administration endpoint that groups databases for shared login and firewall settings, while each database is the unit of compute, storage, and billing. Beneath both sits a managed fabric of compute nodes, storage, and replicas whose exact assembly is dictated by the tier you choose. In General Purpose the engine runs on a compute node in front of durable remote storage; in Business Critical the data sits on local SSD with several synchronous replicas; in Hyperscale storage is decomposed into a page-server tier backed by a separate log service. The control plane handles provisioning, patching, automated backup, and failover on your behalf, so the internals you most need to understand are which physical assembly each tier produces and how that assembly determines latency, cost, and recovery.

### Q: Should I use the DTU or vCore purchasing model for Azure SQL Database?

The DTU model bundles processor, memory, and IO into one blended unit at a fixed ratio, which is simple for small, steady databases but forces you to buy along every dimension to satisfy the one that is constrained. The vCore model unbundles those resources so you size cores, memory, and storage closer to the actual bottleneck, and it unlocks the higher tiers, the most capable hardware, the serverless compute option, and the license benefit for existing SQL Server licenses. The working rule is that vCore is the default for any production workload of consequence, because the ability to size to the constraint and the access to better architecture nearly always outweigh the convenience of a single dial. Reserve DTU for small or predictable databases where simplicity genuinely matters more than control over the resource mix.

### Q: Which Azure SQL Database service tier should I choose for my workload?

Choose by the workload's IO latency tolerance, storage size trajectory, and recovery objective rather than by price. General Purpose suits the broad middle where moderate IO latency is acceptable and cost matters, because it separates compute from remote storage. Business Critical suits latency-sensitive transactional workloads that need the lowest, most predictable IO and fast lossless failover, because it keeps data on local SSD with synchronous replicas. Hyperscale suits very large databases or workloads needing rapid read scale-out and fast restore at size, because it decomposes storage into page servers. Decide the architecture the workload requires, then take the tier that delivers it. Picking a tier by its headline number and being surprised by latency or recovery behavior is the most common and avoidable mistake.

### Q: What is the Hyperscale tier and when does it fit?

Hyperscale is a service tier whose storage architecture differs fundamentally from the file-based tiers. Instead of holding the whole database as files on one node, it spreads storage across a tier of page servers, each owning a slice of the database's pages, fronted by caching on the compute node and backed by a separate durable log service. This design lets the database grow far beyond the storage ceilings of the other tiers, lets read replicas attach quickly because they connect to the shared page-server tier rather than copying the full database, and makes backups nearly instantaneous through snapshots regardless of size. Hyperscale fits very large databases, workloads that need to add read replicas rapidly, and situations where fast restore at size matters. It is the natural answer when a database has outgrown what the file-based tiers can store.

### Q: How does high availability work across the Azure SQL Database tiers?

High availability differs by tier because each tier is a different architecture. General Purpose recovers from a compute-node failure by bringing up a fresh node and reattaching the same durable remote storage, so no data copy is required, only a reattach and recovery, with a brief unavailability during the move. Business Critical maintains several synchronous replicas on local SSD as an availability group, so a primary failure is absorbed by promoting an up-to-date secondary with fast, lossless failover, and one replica is readable. Hyperscale fails compute over to a node that reattaches the shared page-server and log-service storage layer rather than rebuilding a copy. In every case this protects against node or zone failure within a region but not against losing the region, which requires a separate failover group.

### Q: When do I need an Azure SQL Managed Instance instead of a single database?

Choose a managed instance when your application depends on instance-scoped features that the single-database model does not expose, such as cross-database queries within one instance, the SQL Server Agent, Service Broker, or linked servers, along with the higher compatibility surface for code written against an on-premises instance. If your application uses only database-scoped features, a single database or an elastic pool is simpler and usually less expensive. The decision should rest on an enumerated list of the instance-level features your code actually invokes; if that list is empty, the single database is correct. Reaching for a managed instance because it sounds more powerful, when a single database would serve, means paying a higher floor cost and managing a larger surface for capabilities you never use.

### Q: What is an elastic pool and when does it save money?

An elastic pool is a set of databases that share one allocation of resources rather than each holding its own dedicated compute. You give the pool a budget, and the databases inside it draw from that shared budget as their individual loads rise and fall. The pool saves money when the databases have staggered peaks, because you can size the pool for the aggregate load rather than the sum of every database's individual peak. The deciding factor is correlation: if many databases spike at the same time, the pool must be sized for the sum of the peaks and saves nothing, but if their busy periods are spread across the day, as in many multi-tenant patterns, the pool serves them all from shared compute far more economically than per-database dedicated allocations would.

### Q: What does the serverless compute tier offer and when does it fit?

Serverless is a compute option within the General Purpose vCore tier where compute scales automatically between a minimum and maximum and pauses entirely after a configurable idle period, billing only for the seconds it actually runs plus storage. It fits intermittent and unpredictable workloads, development and test databases, and any database whose idle time is a large fraction of the day, because you stop paying for compute while it sleeps. The trade-off is that a paused database takes a short time to resume on the next connection, so the first request after an idle period sees added latency. For workloads where that resume delay on the first hit is unacceptable, the provisioned compute path keeps the database always warm at a steady hourly rate, which is the right choice for steady or latency-critical traffic.

### Q: Why is throttling in Azure SQL Database not the same as an outage?

Because a resource governor continuously enforces the processor, memory, IO, log-write, and worker limits implied by your tier and size, and when a workload exceeds one of those limits the platform throttles the excess rather than crashing. A database pinned at its processor or log ceiling and consequently slow is experiencing governance working exactly as designed, not a fault. The platform exposes the consumption of each governed dimension as a percentage of its limit, so you can see which ceiling you hit. The correct response is to read the saturated dimension and then choose between tuning the workload, which is usually cheaper, and scaling the resource, which is right only when a real shortfall is confirmed. Escalating throttling as a platform outage misdirects the investigation entirely.

### Q: How does the General Purpose tier separate compute and storage?

In General Purpose the database engine runs on a compute node while the data and log files live on durable remote storage reached over the network rather than on a disk attached to the compute node. This separation is the source of both its economy and its recovery simplicity: because the storage is independent of the compute node, a node failure is recovered by bringing up a new node and reattaching the same storage, with no need to copy the database. The cost of the separation is latency, since reads that miss the local cache and all log writes must cross the network to the remote store, giving General Purpose higher and more variable IO latency than a local-SSD tier. For many workloads this latency is acceptable and General Purpose is the right economical default; for latency-sensitive transactional work it is the wrong default.

### Q: Does Azure SQL Database support read replicas or read scale-out?

It depends on the tier, which again reflects the architecture. Business Critical includes a readable secondary among its synchronous replicas, giving you a built-in read scale-out endpoint at no additional compute cost, which is ideal for offloading read-only reporting from the primary. Hyperscale supports adding read replicas that attach to the shared page-server storage tier, which is why they can be provisioned quickly and why scaling reads does not require duplicating the full database. General Purpose, with its single active compute node in front of remote storage, does not provide a local readable secondary in the same way. So if read scale-out is a requirement, it should steer you toward Business Critical or Hyperscale at the tier-decision stage rather than being bolted on afterward when the architecture does not support it.

### Q: How are backups and point-in-time restore handled in Azure SQL Database?

The platform takes automated backups on your behalf and retains them for a configurable window, supporting point-in-time restore within that window by restoring to a new database rather than overwriting the original. The mechanism differs by tier: the file-based tiers stream backups in the conventional way, while Hyperscale uses snapshots at the page-server layer, making backups nearly instantaneous and restore times driven by the snapshot mechanism rather than by streaming the whole database back, which is a major advantage at large size. The operational habit worth building is to know your retention setting, extend it if your compliance or recovery needs require, and rehearse a restore before you actually need one. A restore procedure you have never tested is not a recovery plan; it is an untested assumption you will discover the truth of at the worst possible moment.

### Q: How is Azure SQL Database billed and what drives the cost?

Cost is driven mainly by the compute you provision, the tier and its architecture, and the storage you allocate, plus extras such as extended backup retention and any cross-region replication. In the vCore model you pay for the vCore count and the storage, with the tier setting the per-vCore rate, and Business Critical costs more than General Purpose because it maintains several full copies on local SSD. Serverless bills compute by the second it runs and pauses billing while idle, which lowers cost for intermittent workloads. The DTU model rolls compute, memory, and IO into a single rate per DTU level. The biggest levers are choosing the smallest tier whose architecture meets the requirement, sizing vCores to the confirmed need rather than to a guess, using serverless or pools where the load pattern fits, and applying the existing-license benefit on the vCore model where eligible.

### Q: What is the difference between Azure SQL Database, Managed Instance, and SQL Server on a VM?

These three sit on a spectrum of control against operational burden. Azure SQL Database, in its single-database or elastic-pool form, is the most managed and the least burdensome: you get a database with a T-SQL surface and the platform handles everything below it, at the price of no instance-level features and no operating-system access. Managed Instance sits in the middle, offering a near-complete SQL Server instance with instance-scoped features and high compatibility while still being managed, suiting applications that need those instance features but want the platform to handle the infrastructure. SQL Server on a virtual machine is the least managed and most flexible: you run the full product on a machine you administer, gaining complete control and operating-system access in exchange for owning patching, backup, and high availability yourself. Choose by how many instance features you need and how much management you are willing to own.

### Q: Why does Azure SQL Database occasionally drop connections even when it is healthy?

Because the platform runs on a self-maintaining fabric that patches itself, fails compute nodes over for resilience, and applies scaling changes through brief reconfigurations, and during those routine moves existing connections are dropped momentarily. This is an expected property of a managed service rather than a malfunction, and the platform classifies these brief interruptions as transient faults that the application should retry with a backoff. An application without retry logic turns a routine sub-second reconfiguration into a user-visible error, which is why resilient retry is mandatory rather than optional for any production workload. The architectural takeaway is to design for transient drops from the start, treating them as the normal cost of running on a fabric that maintains itself, so that scaling and patching pass invisibly rather than registering as incidents.

### Q: How much can an Azure SQL Database grow and does storage size affect the tier choice?

The maximum database size depends on the tier and, in the vCore model, partly on the vCore count, and the ceilings differ substantially between tiers, with Hyperscale designed to grow far beyond what the file-based tiers can hold. This makes storage size a first-class input to the tier decision rather than an afterthought: a database approaching the storage limit of General Purpose is often pointed toward Hyperscale by its size alone, independent of any performance need, because Hyperscale's page-server architecture is what removes the file-based ceiling. Treat the projected storage trajectory as one of the three inputs to the tier choice, alongside latency tolerance and recovery objective, and verify the current per-tier maximums against the official documentation before committing, since these limits are raised over time and a number that was a ceiling last year may no longer bind.

### Q: Is a single region's high availability enough, or do I need cross-region disaster recovery?

Local high availability and cross-region disaster recovery solve different problems and conflating them is a dangerous error. The replicas, storage reattach, and zone-redundant options protect the database when a node or an availability zone fails within a region, keeping it serving with no data loss in the synchronous cases. None of that protects against the loss of an entire region, which requires a failover group maintaining a continuously replicated secondary in a paired region behind a stable listener endpoint that follows the primary across a failover. Whether you need the cross-region construct depends on your recovery objective: if surviving a regional event is in scope, local high availability alone does not meet it. Decide the objective first, then provision local high availability for node and zone failure and a failover group for regional survival as the objective requires.
