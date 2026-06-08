---
layout: post
title: "Set Up Azure SQL Failover Groups"
page_title: "How to Set Up Azure SQL Failover Groups: Listeners, Failover Policy, and a Tested Failover Drill"
date: 2023-06-12
categories: ["Technology"]
tags: ["Azure", "Azure SQL", "Failover Groups", "High Availability", "Disaster Recovery", "Geo-Replication"]
excerpt: "Azure SQL failover groups survive a regional outage only when apps connect through the read-write listener and the failover policy is tuned and tested."
image: "/assets/images/blog/blog-74.webp"
reading_time: 61
author: "marcus-hall"
last_updated: 2023-06-12
lang: en
---
A correctly configured Azure SQL failover group is the difference between a regional outage that your application rides out in seconds and one that pages your on-call engineer at three in the morning with a database that has vanished from the only endpoint the code knows about. The feature itself is not hard to switch on. The portal walks you through it, the CLI does it in two commands, and the result looks finished the moment the secondary finishes seeding. The trap is that the visible part of the setup, the part the wizard finishes for you, is the part that almost never goes wrong. What goes wrong is the connection string, the promotion policy that nobody tuned, and the drill that nobody ran. This guide treats the group not as a checkbox but as a contract between your database tier and your application tier, and it spends most of its length on the half of that contract the documentation tends to skip.

![Set Up Azure SQL Failover Groups](/assets/images/blog/blog-74.webp)

The promise of the feature is specific and worth stating plainly before the procedure starts. A group gives your databases a stable, region independent name that always resolves to whichever server currently holds the writable copy. When the primary region fails, the group can move the writable role to the secondary region, repoint that name, and bring your application back online without anyone editing a configuration file. The cost of getting it wrong is equally specific. If your application connects to the underlying server name instead of the group name, the move happens at the database layer and the application never notices, because it is still asking for a server that is now read only or unreachable. The database failed over and the application did not follow. That single mismatch is the most common reason teams run a flawless failover test on paper and then discover, during a real outage, that traffic never moved.

## What an Azure SQL failover group actually is and what it is not

Before the first command, hold a clear mental model, because the configuration choices later only make sense once the moving parts are named. An Azure SQL failover group is a managed wrapper built on top of active geo-replication. Geo-replication on its own creates an asynchronous copy of a database in another region and keeps it current; what it does not provide is a single name that follows the writable copy, nor an orchestrated way to move many databases together, nor an automatic trigger when a region goes dark. The group adds exactly those three things. It groups one or more databases that should move as a unit, it provides two DNS endpoints that abstract away which physical server is primary at any moment, and it adds a policy that can promote the secondary automatically after a defined waiting period.

The two endpoints are the heart of the design and the part most worth internalizing. When you create a group named, for example, `shop-fog`, Azure provisions a read-write listener at `shop-fog.database.windows.net` and a read-only listener at `shop-fog.secondary.database.windows.net`. The read-write listener resolves, through DNS, to whichever server currently owns the writable databases. The read-only listener resolves to the geo-secondary. These names never change for the life of the group. What changes, silently, behind them is the IP and server they point to. A failover is, mechanically, a DNS update plus a role swap: the writable role moves to the other server and the read-write name is updated to point there. Your application keeps asking for `shop-fog.database.windows.net` and keeps getting an answer; the answer simply comes from a different region after the move.

It helps to separate the group from the underlying high availability that every Azure SQL database already has within a single region. The local replicas that keep a Business Critical database online when one node fails are a different mechanism entirely, covered in depth in our walkthrough of the platform internals at [Azure SQL Database internals](/2022/02/06/azure-sql-database-internals/). That intra region resilience handles a failed node or a patched host transparently and has nothing to do with the group you are about to build. The group is strictly about surviving the loss of a whole region, and it does so by keeping a warm copy somewhere else and giving you a name that can point at either copy. Confusing the two leads to the belief that a single region database is somehow protected against a regional event, which it is not, and to the opposite error of paying for a geo-secondary when the requirement was only to survive a node failure.

A group is also not a backup. It replicates the current state of the database, including a mistaken `DELETE` that drops half a table. If a bad deployment corrupts data, the corruption replicates to the secondary within seconds, and failing over lands you on an identical bad copy. Point in time restore and long term retention solve the data corruption problem; the group solves the lost region problem. The two are complementary, and a serious resilience posture uses both, a point we return to when discussing how this fits a wider design.

### What does the read-write listener actually point to?

The read-write listener is a CNAME style endpoint that always resolves to the server currently holding the writable replicas of the group. It moves the instant a role swap completes. Applications that connect through it never need to learn the underlying server name, which is precisely why connection strings must use it rather than the raw server.

## The namable claim: the listener-in-the-connection-string rule

Everything in this guide reduces to one rule that deserves a name, because naming it makes it the thing you check first when a drill disappoints. Call it the listener-in-the-connection-string rule: a group only protects an application if that application connects through the read-write listener, never through the underlying server name, because the listener moves with the primary while a hard coded server name stays bolted to a single region.

The rule sounds obvious written out, and teams nod at it, and then they fail it anyway. The reason is that the setup flow encourages the failure. When you provision a database, the portal hands you a server name like `shop-eastus.database.windows.net` and a ready made connection string built around it. You wire that into the application, ship it, and it works. Months later you add a group, the wizard succeeds, the secondary seeds, the green checkmarks appear. Nothing in that flow ever tells you to go back and change the connection string you wired in on day one. So the application keeps pointing at `shop-eastus`, the group quietly does its job at the database layer, and the gap between the two only becomes visible during a role swap, which is the worst possible moment to discover it.

The fix is to treat the listener name as the only database address the application is ever allowed to know. The underlying server name becomes an implementation detail used by infrastructure tooling and nothing else. Once you adopt that discipline, the group does what it promises, because the one name your code depends on is the one name engineered to follow the writable copy across regions.

## Prerequisites and the correct order of operations

Failover groups are unforgiving about ordering in a few specific ways, and getting the sequence right the first time saves a seeding cycle that can take a long time for a large database. Start with the prerequisites that the wizard assumes you have already satisfied.

The first prerequisite is two logical servers in two different regions. A group for Azure SQL Database joins two `Microsoft.Sql/servers` resources, the primary server and a secondary server, and they must live in different Azure regions. You cannot build a group between two servers in the same region, because the whole point is regional survival. If you have only the primary server today, create the secondary server first, in your chosen disaster recovery region, before you touch the group.

The second prerequisite is matching server level configuration on both servers. Logins, firewall rules, virtual network rules, and any server scoped settings do not replicate through the group. The group replicates databases, not the server objects around them. If your primary server has a set of SQL logins or a private endpoint and the secondary does not, then after a role swap your application authenticates against a server that has never heard of those logins, and you get an authentication failure that looks exactly like the transient login problem covered in our guide to [Azure SQL login failures](/2022/08/15/fix-azure-sql-40613-unavailable/), except that this one will not clear on retry because the cause is structural. Mirror the server configuration before you fail over, not after.

The third prerequisite is a compatible service tier and enough capacity in the secondary region. The geo-secondary should match the compute size of the primary, because after a role swap it carries the full production load. A secondary that is smaller to save money becomes a self inflicted outage the moment it is promoted, when it cannot keep up with the traffic the primary handled comfortably. Verify that the secondary region has quota for the tier and size you need before you start, since a capacity rejection mid seeding is a frustrating place to learn about a quota limit.

With those satisfied, the correct order of operations is fixed. Create the secondary server. Confirm the server level configuration matches. Create the group on the primary server and add the databases to it, which triggers the initial seed of each database to the secondary. Wait for seeding to complete. Set the promotion policy and grace period deliberately rather than accepting the default. Repoint every connection string at the read-write listener. Run a planned promotion as a drill, confirm the application followed, and fail back. Only after that last step is the configuration actually finished, regardless of what the portal said three steps earlier.

## The InsightCrunch failover-group setup checklist

The findable artifact for this guide is a checklist that pairs each step with the specific mistake that step invites. Most published walkthroughs give you the happy path; the value here is the gotcha column, because the gotcha is where the real outages come from. Keep this table next to you while you work, and treat the right hand column as the list of things to verify before you call any step done.

| Step | What you do | The gotcha that bites here |
|------|-------------|----------------------------|
| 1. Add the secondary | Create a logical server in the DR region and confirm logins, firewall, and network rules match the primary | Server objects do not replicate; an unmirrored login becomes a post failover auth failure |
| 2. Create the group | Create the group on the primary and add the databases, starting the seed | Adding a database larger than expected starts a long seed; size the maintenance window for it |
| 3. Set the policy | Choose automatic or manual failover and set the grace period | Accepting the one hour default grace period silently caps your effective recovery time |
| 4. Point connections at the listener | Replace every server name in connection strings with the read-write listener, and use the read-only listener for reporting | Leaving one service on the raw server name means that service never fails over |
| 5. Run a test failover | Execute a planned promotion, confirm writes land in the new region, then fail back | Skipping the drill means the first real switchover is also the first test, under maximum pressure |

The table is deliberately short, because the setup itself is short. The length of this article lives in understanding why each gotcha happens and how to prove you avoided it, which the sections below take in turn.

## Step by step: building the group with working commands

The cleanest way to learn the moving parts is the Azure CLI, because each command maps to exactly one concept and the output tells you what changed. The portal hides the same operations behind a wizard, and infrastructure as code expresses them declaratively, but the imperative commands make the model legible. Adapt the names and regions to your environment.

Start by confirming both servers exist and noting their names. The primary server here is `shop-eastus` in East US, and the secondary is `shop-westus` in West US, both inside the resource group `shop-rg`.

```bash
# List the servers so you can confirm both exist before grouping them
az sql server list \
  --resource-group shop-rg \
  --query "[].{name:name, region:location, state:state}" \
  --output table
```

Create the group on the primary server, naming the secondary server as the partner. The group name becomes the DNS label for both listeners, so choose it carefully and treat it as permanent; renaming a group means rebuilding it, which means reseeding.

```bash
# Create the failover group and attach it to the secondary server
az sql failover-group create \
  --name shop-fog \
  --resource-group shop-rg \
  --server shop-eastus \
  --partner-server shop-westus \
  --failover-policy Automatic \
  --grace-period 1
```

That single command creates the group, provisions both listener endpoints, and sets an automatic promotion policy with a one hour grace period. It does not yet add any databases, which is intentional: an empty group is cheap to create and lets you confirm the listeners resolve before you commit to a long seed. Confirm the endpoints exist.

```bash
# Show the group, including both listener endpoints and current roles
az sql failover-group show \
  --name shop-fog \
  --resource-group shop-rg \
  --server shop-eastus \
  --output jsonc
```

The output reports the read-write endpoint, the read-only endpoint, the replication role of each partner server, and the replication state. The primary server shows the role Primary and the partner shows Secondary. Now add the databases that should move together. Adding a database starts an asynchronous seed of that database to the secondary region, and the seed must finish before the database is protected.

```bash
# Add a database to the group; this starts the geo-seed to the secondary
az sql failover-group update \
  --name shop-fog \
  --resource-group shop-rg \
  --server shop-eastus \
  --add-db catalog orders inventory
```

Three databases join the group in one call. Each begins seeding independently, and a large database can take a while to copy across regions for the first time. You can watch the replication state move from Seeding to Catchup to a synchronized state by repeating the show command. Do not run a role swap while any database is still seeding; a database that has not finished its initial copy cannot be promoted, and attempting it returns an error rather than failing over the rest of the group cleanly.

For teams standardized on PowerShell, the same sequence reads almost identically, and many shops keep both forms in their runbook so whoever is on call can use the tool they know.

```powershell
# PowerShell equivalent of creating the group and adding a database
$primaryServer = "shop-eastus"
$secondaryServer = "shop-westus"
$resourceGroup = "shop-rg"

New-AzSqlDatabaseFailoverGroup `
  -ResourceGroupName $resourceGroup `
  -ServerName $primaryServer `
  -PartnerServerName $secondaryServer `
  -FailoverGroupName "shop-fog" `
  -FailoverPolicy Automatic `
  -GracePeriodWithDataLossHours 1

# Add a database to the group
$db = Get-AzSqlDatabase -ResourceGroupName $resourceGroup -ServerName $primaryServer -DatabaseName "orders"
$db | Add-AzSqlDatabaseToFailoverGroup -ResourceGroupName $resourceGroup -ServerName $primaryServer -FailoverGroupName "shop-fog"
```

The PowerShell parameter `GracePeriodWithDataLossHours` names the trade off directly, which is useful, because the grace period is exactly the window during which Azure will wait before promoting the secondary at the risk of losing the most recent transactions. The CLI flag `--grace-period` sets the same value. We return to why one hour is rarely the right answer.

## Pointing connections at the listener, the step that decides everything

With the group built and the databases seeded, the configuration is half finished, and the unfinished half is the half that determines whether any of it works. This is where the listener-in-the-connection-string rule earns its name. Every application, job, function, and reporting tool that touches these databases must now connect through a listener endpoint rather than through `shop-eastus.database.windows.net`.

For the writable workload, that means the read-write listener. A typical ADO.NET connection string changes only in the server portion.

```text
Server=tcp:shop-fog.database.windows.net,1433;
Database=orders;
Authentication=Active Directory Default;
Encrypt=True;
TrustServerCertificate=False;
Connection Timeout=30;
```

The database name, authentication, and encryption settings are unchanged. The only edit is the server, which now names the group rather than the physical primary. After this change, a role swap that moves the writable role to West US is invisible to the application, because the read-write listener now resolves to West US and the connection string never mentioned a region in the first place.

For read only workloads, reporting queries, dashboards, exports, and anything that does not write, point at the read-only listener instead, and set the application intent so the driver cooperates with routing.

```text
Server=tcp:shop-fog.secondary.database.windows.net,1433;
Database=orders;
ApplicationIntent=ReadOnly;
Authentication=Active Directory Default;
Encrypt=True;
```

This sends read traffic to the geo-secondary, which offloads it from the primary and puts otherwise idle replica capacity to work. There is a nuance worth stating exactly, because it trips people: the read-only listener of the group routes to the geo-secondary server in the partner region. That is distinct from the local read replica that a Business Critical database keeps inside its own region, which you reach by setting `ApplicationIntent=ReadOnly` against the read-write listener. The two read paths exist for different reasons. The geo-secondary read path is about using the disaster recovery copy for cross region reporting; the local read replica is about offloading reads without leaving the primary region. Decide which one a given reporting workload needs and point it at the matching listener.

The discipline that makes this durable is treating the listener names as configuration that lives in exactly one place. If the read-write listener is hard coded into a dozen services, then a future change, perhaps a migration to a new group, requires twelve edits and the near certainty of missing one. Put the listener endpoints in a single source of configuration, a Key Vault secret, an app configuration store, an environment variable injected at deploy time, and have every service read from there. The goal is that the database address is a single fact the whole estate agrees on, not a string copied into a dozen places.

### How do read-only connections route in a group?

Set `ApplicationIntent=ReadOnly` and connect to the read-only listener, `groupname.secondary.database.windows.net`, to reach the geo-secondary in the partner region. To use a local read replica inside the primary region instead, set the same intent but connect to the read-write listener. The endpoint you choose decides which replica answers.

## The settings the defaults get wrong

A group created with default settings works, in the sense that it will fail over, but two defaults quietly undercut the resilience you think you bought. Tuning them is the difference between a configuration that meets your stated recovery objective and one that only appears to.

The first default that misleads is the grace period on automatic promotion. When you set an automatic promotion policy, Azure does not promote the secondary the instant it detects a problem in the primary region. It waits for the grace period to elapse, and only then, if the outage persists and the role swap would risk data loss beyond the replication lag, does it promote the secondary. The reason for the wait is sound: a brief blip in the primary region is not worth a role swap that may lose the last few seconds of committed transactions, so Azure gives the primary a chance to recover before accepting that risk. The consequence, though, is that your effective recovery time includes the entire grace period. If you set a one hour grace period and the primary region truly fails, your application is impaired for up to that hour before automatic promotion even begins. Teams that quote a tight recovery objective to their business and leave the grace period at a long default have, without realizing it, promised something the configuration cannot deliver. Choose the grace period as a deliberate trade off between tolerating a transient blip and bounding your worst case recovery time, and write the chosen value into your runbook so it is a decision on record rather than an accident of the default.

The second default that misleads is the assumption that automatic promotion is always what you want. Automatic failover is attractive because it removes the human from the critical path, but it carries the risk of failing over on a problem that was about to resolve, and of doing so with the data loss that asynchronous replication implies. Some teams deliberately choose a manual promotion policy precisely so that a human confirms the region is genuinely gone before accepting the data loss of a forced promotion. The right choice depends on how your business weighs a slightly longer recovery against the risk of an unnecessary failover, and the next section unpacks that decision rather than pretending one answer fits everyone.

### Automatic versus manual failover: which should I configure?

Choose automatic when fast, hands off recovery matters more than avoiding the rare unnecessary failover, and tune the grace period to bound the wait. Choose manual when a human must confirm a true regional loss before accepting potential data loss. Many teams run automatic with a short grace period and keep a manual override in the runbook.

## Understanding the role swap modes you can trigger

There are three distinct operations that all get called failover in casual conversation, and conflating them causes real mistakes during an incident. Knowing which one you are invoking, and what it costs, is part of a complete configuration.

A planned promotion, sometimes called a friendly or manual failover, synchronizes the secondary fully before swapping roles, so it completes with no data loss. It is the operation you use for a drill, for a maintenance window, or for moving the writable role closer to a shifted user base. Because it waits for full synchronization, it can take a moment longer to complete, and it requires the secondary to be reachable. You trigger it with `az sql failover-group set-primary` against the secondary server, which tells Azure to make that server the new primary.

A forced promotion, the data loss variant, promotes the secondary without waiting for synchronization. You reach for it when the primary region is genuinely unreachable and waiting for synchronization is impossible because the primary cannot be contacted. It accepts the loss of any transactions that had not yet replicated, bounded by the replication lag at the moment of the outage. The CLI exposes this through the same set-primary command with the `--allow-data-loss` flag, and the choice to add that flag should be a conscious one made during a real regional event, not a habit.

The automatic promotion orchestrated by the policy is, mechanically, the forced variant, performed by Azure on your behalf after the grace period, when it has decided the primary is genuinely down. That is why the grace period matters so much: it is the window during which Azure is willing to wait rather than accept the data loss that an automatic promotion entails.

Here is the planned promotion that every drill should use, run against the current secondary so that it becomes primary.

```bash
# Run a planned (no data loss) failover by promoting the current secondary
az sql failover-group set-primary \
  --name shop-fog \
  --resource-group shop-rg \
  --server shop-westus
```

Note that the `--server` argument names the secondary, `shop-westus`, because you are telling that server to take the primary role. Running it against the current primary is a common slip that returns an error rather than doing anything harmful, but it wastes time during a drill. After the command completes, the read-write listener resolves to West US, and a query through the listener lands there.

```bash
# Force a failover with data loss, used only when the primary region is unreachable
az sql failover-group set-primary \
  --name shop-fog \
  --resource-group shop-rg \
  --server shop-westus \
  --allow-data-loss
```

The difference between those two commands is one flag and a large difference in consequence. Keep both in the runbook, clearly labeled, so that under pressure the on-call engineer reaches for the right one. Rehearsing both in a controlled setting, which the companion drill environment makes safe to do, is the only way to build the muscle memory that an incident demands.

## What RPO and RTO the configuration targets

Two numbers define what a group buys you, and quoting them accurately to your business is part of configuring the feature responsibly. The recovery point objective, RPO, is how much recent data a role swap can lose, and it follows from the asynchronous nature of geo-replication: committed transactions on the primary that have not yet reached the secondary are at risk during a forced or automatic promotion. Microsoft documents an RPO target for active geo-replication and groups that you should confirm against the current official documentation for your service tier, because it is the kind of number that can be revised and that varies with configuration; treat the published figure as the planning value and verify it before you quote it to anyone.

The recovery time objective, RTO, is how long the role swap itself takes once it begins, and for automatic promotion your effective RTO is the documented promotion time plus the grace period you configured. This is the calculation teams get wrong most often. The marketing friendly number is the promotion time alone; the number your business actually experiences during an automatic recovery includes the grace period during which Azure waited. If your stated RTO is fifteen minutes and your grace period is one hour, the configuration cannot meet the stated objective during an automatic promotion, no matter how fast the promotion itself is. Reconcile the two before you publish a recovery objective, and flag both the documented RPO and the documented promotion time for verification against the current official source whenever you cite them, since both can change with service tier and over time.

A planned promotion, by contrast, has an RPO of zero, because it synchronizes fully before swapping. This is why drills use planned promotion and why a planned promotion is the right tool for a maintenance event in the primary region: you move the writable role with no data loss and bring it back the same way. The data loss numbers only enter the picture when the primary is genuinely gone and waiting for synchronization is not an option.

### What RPO and RTO do Azure SQL groups provide?

A planned promotion has an RPO of zero because it synchronizes first. Automatic or forced promotion has a small nonzero RPO bounded by replication lag, and an effective RTO equal to the documented failover time plus your configured grace period. Confirm the exact published figures against current Microsoft documentation before quoting them.

## Verifying the configuration actually worked

A group that has never failed over is a hypothesis, not a safety net. Verification has two layers: confirming the steady state is healthy, and confirming a real switchover moves traffic end to end. Both matter, and the second is the one teams skip.

For the steady state, check that every database in the group has finished seeding and reports a synchronized replication state, that both listener endpoints resolve, and that the role assignments are what you expect. The show command reports the roles and the replication state; a database stuck in a seeding or catchup state for an unusually long time is a signal to investigate capacity or throttling on the secondary before you rely on the group.

```bash
# Confirm every database in the group is synchronized and both endpoints resolve
az sql failover-group show \
  --name shop-fog \
  --resource-group shop-rg \
  --server shop-eastus \
  --query "{readWrite:readWriteEndpoint, readOnly:readOnlyEndpoint, role:replicationRole, state:replicationState, databases:databases}" \
  --output jsonc
```

A DNS check from a machine that resembles your application environment confirms the listener resolves and shows you which region it currently points to, which is a fast sanity check before and after any failover.

```bash
# Confirm the read-write listener resolves; the target reveals the current primary region
nslookup shop-fog.database.windows.net
```

The second layer, the end to end test, is the one that proves the listener-in-the-connection-string rule was actually honored. Connect through the read-write listener, run a write, perform a planned promotion, and confirm the same connection string still lands a write afterward in the new region. If the write succeeds before the role swap and fails after it, you have just found a service that was connecting through the raw server name rather than the listener, and you found it during a drill rather than during an outage. That is the entire value of the drill: it surfaces the connection string mismatch while the stakes are low.

```sql
-- Run before and after a planned failover, through the read-write listener,
-- to confirm writes follow the failover and to see which region is serving
SELECT @@SERVERNAME AS current_server, DATABASEPROPERTYEX(DB_NAME(), 'Updateability') AS updateability;
```

Before the role swap the query reports the primary server name and an updateable state; after a planned promotion, run through the same listener based connection, it reports the secondary server name and still shows updateable, proving the writable role moved and the listener followed it. If instead the post failover query reports a read only state or fails to connect, the connection was not going through the read-write listener, and you have the precise diagnosis in hand.

## The six failure patterns engineers actually hit

The documentation describes the happy path. The patterns below are what teams report after the happy path is built, and each maps to a specific configuration step that was done incompletely. Reading them as a catalog of symptoms means you can recognize your situation quickly and go straight to the step that needs attention.

The first pattern is the role swap that works at the database layer while the application keeps hitting the old primary. The database failed over cleanly, the read-write listener now points to the new region, and yet the application still throws errors or, worse, silently connects to a now read only copy. The cause is always the same: a connection string that names the underlying server rather than the listener. The application is asking for `shop-eastus.database.windows.net`, which after the role swap is the secondary and is read only, so writes fail while reads might still succeed, producing a confusing partial outage. The fix is the listener-in-the-connection-string rule applied to every service without exception, and the way to find the offending service is the end to end drill described above, which exposes exactly which connection did not follow.

The second pattern is read traffic that never offloads to the geo-secondary. The team built the group expecting reporting queries to run against the secondary and lighten the primary, but the primary stays saturated and the secondary sits idle. The cause is that the reporting workloads were never repointed at the read-only listener, or were pointed there without setting the read only application intent, so the driver routed them back to the writable replica. The fix is to confirm both halves: the read-only listener as the server, and `ApplicationIntent=ReadOnly` in the connection string, so the driver honors the routing.

The third pattern is the automatic promotion grace period surprising the team during a real outage. The primary region degrades, the application is impaired, and nothing happens for a long stretch because Azure is still inside the grace period before it will accept a data loss promotion. The team expected near instant recovery and instead watched a clock they did not know existed. The cause is a grace period left at a default that nobody chose, and the fix is to set the grace period as a deliberate decision and, separately, to keep a manual forced promotion command ready so a human can promote immediately when the team is confident the region is gone rather than waiting out the policy.

The fourth pattern is needing a manual failover for planned maintenance and discovering the runbook does not distinguish planned from forced. Someone needs to move the writable role to the secondary for a maintenance event, reaches for the role swap command, and either runs the forced variant unnecessarily, accepting avoidable data loss risk, or hesitates because the runbook never spelled out which command is the safe one. The fix is a runbook that names both commands explicitly, marks the planned promotion as the default for maintenance and drills, and reserves the data loss flag for genuine region loss.

The fifth pattern is the test failover that the team keeps postponing until it becomes the real switchover. The group is built, the connection strings are updated, everyone believes it works, and the first time the configuration is exercised is during an actual regional incident, under maximum pressure, with no prior confirmation that the application follows. This is less a misconfiguration than a missing practice, and it is the most dangerous of the six, because it hides every one of the other five until the worst moment. The fix is to schedule planned promotion drills on a cadence, run them in a low traffic window, and treat any drill that does not move traffic cleanly as a finding to fix rather than a one off to ignore.

The sixth pattern is a secondary placed in the wrong region. The group works, drills pass, and then a compliance review or a latency complaint reveals that the secondary sits in a region that violates a data residency requirement or that adds unacceptable latency for the read offload workload. The cause is a region chosen for convenience during setup rather than against the real constraints. The fix is more disruptive than the others, because moving the secondary means rebuilding the group and reseeding, so it is worth getting the region right at step one by checking data residency, the supported region pairing, and the latency your read workloads can tolerate before you create the secondary server.

### Why does my application fail after a successful database failover?

Almost always because the connection string names the underlying server instead of the read-write listener. The database failed over, but the application is still asking for the old primary, which is now a read only secondary. Repoint every connection string at the group listener and rerun a drill to confirm.

## Running a safe test failover, the drill that proves it all

The single highest value activity in this entire setup is the planned promotion drill, because it is the only step that exercises the whole contract at once: the listeners, the connection strings, the policy, and the application's tolerance for a brief role swap. A drill done well is boring, which is the goal.

Schedule the drill in a low traffic window and announce it, because even a planned promotion causes a short interruption while connections are dropped and reestablished against the new primary. Existing connections are terminated during the swap, so the application sees a brief burst of connection errors and must reconnect; an application with sensible retry logic rides through this in seconds, and an application without retry logic will surface the gap, which is itself a useful finding. Before you start, capture the current primary region from the read-write listener so you have a clean before picture.

Run the planned promotion, promoting the secondary, then immediately run the verification query through the listener based connection to confirm writes land in the new region. Exercise the actual application, not just a query tool: place a test order, write a record, do whatever your real write path does, and confirm it succeeds through the same configuration the application uses in production. This is what catches the service that quietly kept the raw server name. Then fail back to the original region the same way, with a second planned failover, and confirm the application follows again. A complete drill exercises the move in both directions, because failing back is just as much a real operation as failing over, and a runbook that only covers one direction is half a runbook.

Record three things from every drill: how long the application took to recover, whether any service failed to follow, and whether the recovery time matched the objective you quoted to the business. Those three numbers turn a drill from a checkbox into evidence. Over a few drills you build a defensible recovery time figure grounded in measurement rather than in the marketing number, and you build the on-call team's confidence that the procedure works.

This is exactly the kind of procedure that benefits from rehearsal in a sandbox before you run it against production, and the hands on labs in VaultBook give you a disposable Azure SQL environment where you can build a group, break the primary, and watch the listener move without risking a real workload, which is the fastest way to internalize the mechanics described here. For building the incident response habit specifically, the scenario based disaster recovery drills in ReportMedic put you through a simulated regional outage and have you execute the role swap under time pressure, so that the planned failover command and the forced promotion command are familiar in your hands before an incident demands them. Pairing a calm sandbox to learn the mechanics with a pressured drill to practice the response is how teams move from a configuration that exists to a capability they can rely on.

### How do I test an Azure SQL failover safely?

Run a planned failover with `az sql failover-group set-primary` against the secondary in a low traffic window. It synchronizes first, so there is no data loss. Confirm writes land in the new region through the listener, exercise the real application, then fail back the same way and record the recovery time.

## Making the configuration repeatable as code

A group clicked together in the portal is a configuration that exists in exactly one place and disappears the moment someone deletes it by accident. Expressing it as code makes it reproducible, reviewable, and recoverable, and it forces the region and policy choices to be explicit rather than buried in a wizard. Bicep is the most direct way to declare a group for Azure SQL Database, and the declaration reads as a faithful map of the concepts covered above.

```bicep
// Declares a failover group joining an existing primary and secondary server.
// The databases array lists the resource IDs of the databases that move together.

param primaryServerName string
param secondaryServerName string
param databaseIds array
param groupName string = 'shop-fog'
param gracePeriodHours int = 1

resource failoverGroup 'Microsoft.Sql/servers/failoverGroups@2023-05-01-preview' = {
  name: '${primaryServerName}/${groupName}'
  properties: {
    readWriteEndpoint: {
      failoverPolicy: 'Automatic'
      failoverWithDataLossGracePeriodMinutes: gracePeriodHours * 60
    }
    readOnlyEndpoint: {
      failoverPolicy: 'Enabled'
    }
    partnerServers: [
      {
        id: resourceId('Microsoft.Sql/servers', secondaryServerName)
      }
    ]
    databases: databaseIds
  }
}
```

A few details in that template are worth reading closely, because they encode decisions the portal makes silently. The grace period is expressed in minutes in the resource model, so the template converts the hours parameter, and exposing it as a parameter means the recovery time trade off is a reviewable value in a pull request rather than a default nobody noticed. The read only endpoint promotion policy set to Enabled is what makes the read-only listener follow along during a role swap so your reporting workloads keep resolving. The databases array is the explicit list of what moves together, which makes the grouping a deliberate, version controlled fact. The API version is the kind of string to confirm against the current provider documentation, since resource schemas evolve and an older version may not expose a property you need.

The same shape is expressible in an ARM template directly, in Terraform through the `azurerm_mssql_failover_group` resource, and in Pulumi, and the choice among them is your team's existing standard rather than anything specific to groups. What matters is that the group, its policy, its grace period, and its membership live in source control alongside the rest of the database infrastructure, so that rebuilding the estate in a new subscription or recovering from an accidental deletion is a deploy rather than an archaeology project. Teams already templating their database tier as part of a broader move to Azure will find this slots naturally into the patterns covered in our guide to [migrating SQL Server to Azure](/2025/06/30/migrate-sql-server-to-azure/), where the group becomes one more declared resource in the target environment rather than a manual afterthought.

There is one ordering subtlety with infrastructure as code that mirrors the imperative ordering discussed earlier. The template assumes both servers and the databases already exist, because a group cannot be declared before its members. In a full deployment you express the dependency so that the servers and databases are created first and the group follows, and you accept that the first deploy includes the seeding time for each database. Subsequent deploys are fast because the group already exists and only its properties are reconciled.

## How the group fits the wider disaster recovery design

A group is a building block, not a complete disaster recovery strategy, and configuring it well means understanding where it sits in the larger picture. The database tier is one of several tiers that must all fail over together for an application to actually survive a regional event, and a database that fails over alone, while the application tier, the cache, the storage accounts, and the DNS all stay pinned to the dead region, has not bought you a recovery.

The application tier needs its own regional redundancy, whether that is a second deployment in the secondary region kept warm, a traffic manager or front door profile that routes users to a healthy region, or an active configuration in both regions at once. The group handles the database's role swap, but something has to route user traffic and application compute to the region that now holds the writable database. Designing that coordination is the subject of our broader treatment at [disaster recovery architecture on Azure](/2024/07/22/azure-disaster-recovery-architecture/), which places the database group inside the full pattern of regional failover for an application, including how to sequence the tiers and how to avoid the split brain risk of a database in one region serving an application stranded in another.

Monitoring closes the loop. A group should raise an alert when a role swap occurs, automatic or manual, so the team knows the writable role moved even if the application rode through it smoothly. Configure an alert on the group's health and on the replication state of its databases, so that a database falling out of a synchronized state, perhaps because the secondary is throttling, becomes a warning you act on before an outage rather than a surprise you discover during one. A degraded secondary that nobody noticed is a group that will not actually protect you when the primary fails, which returns to the theme of the whole guide: the configuration that looks finished is not the same as the configuration that has been proven.

It also pays to remember that a group protects against region loss but not against logical corruption, since a bad write replicates to the secondary as faithfully as a good one. Pair the group with point in time restore and an appropriate backup retention policy so that a data corruption event has a recovery path that does not depend on a copy that holds the same corruption. The transient, self healing errors that Azure SQL surfaces during normal operation, the kind that clear on a retry, are a separate concern from regional failover, and recognizing the difference keeps you from reaching for a role swap when the right response is a retry, a distinction drawn out in our guide to the [transient database unavailable error](/2022/08/15/fix-azure-sql-40613-unavailable/).

## A note on managed instance and multiple databases

Two variations on the basic setup come up often enough to address directly. The first is the group for Azure SQL Managed Instance, which differs from the database variant in an important way: a managed instance group operates at the instance level and moves all databases on the instance as a unit, rather than letting you pick individual databases. The listener concept is the same, the policy and grace period work the same way, and the drill discipline is identical, but you do not add and remove individual databases, because the unit of failover is the whole instance. If your workload runs on a managed instance, plan around moving everything together.

The second variation is grouping multiple databases that must fail over consistently. When an application spans several databases that reference each other or that must stay mutually consistent, putting them in the same group ensures they move together, so you never end up with an orders database in one region and an inventory database in another after a partial failover. The cost is that the pairing fails over as a unit, so a problem isolated to one database still moves the whole group. Decide which databases must share a region at all times, and keep databases that are genuinely independent in separate groups so their failovers do not entangle.

## Choosing the secondary region deliberately

The region you pick for the secondary server shapes everything downstream, and it is the one decision that is expensive to revisit, because changing it means rebuilding the group and reseeding every database. Three constraints should drive the choice, and weighing them up front prevents the sixth failure pattern from ever appearing.

Data residency is the first and the hardest to negotiate, because it is usually a legal rather than a technical constraint. If your data must remain within a particular jurisdiction, the secondary region is limited to the set of regions inside that boundary, and no amount of latency optimization overrides a residency requirement. Establish the residency constraint before you look at anything else, because it can eliminate most of the map in a single stroke and there is no point optimizing among regions you are not allowed to use.

Latency is the second constraint, and it matters in two distinct ways. The replication latency between the primary and the secondary influences how far behind the secondary runs, which feeds directly into the data at risk during a forced promotion. A geographically distant secondary replicates with more lag than a nearby one. Separately, if you offload read workloads to the geo-secondary, the latency from your reporting consumers to that secondary region affects their experience. A secondary chosen only for replication proximity can be a poor home for read offload if your analysts sit on the other side of the world, so reconcile the two before committing.

Region pairing is the third constraint, and Azure designates paired regions that receive certain platform benefits during broad outages, including sequential rather than simultaneous updates and prioritized recovery. Using the paired region for your secondary is a reasonable default unless residency or latency points elsewhere, because it aligns your disaster recovery with the platform's own recovery behavior. The specific pairings and the guarantees attached to them are details to confirm against current Azure documentation, since the platform's regional structure evolves, but the principle of preferring the designated pair as a starting point holds.

The practical upshot is to settle residency first, then narrow by region pairing, then validate latency against both your replication needs and your read offload consumers, and only then create the secondary server. Doing the analysis in that order means you build the group once rather than rebuilding it after a compliance review or a latency complaint forces your hand.

## Authentication and access after a role swap

The most insidious gap in a group setup is authentication, because it passes every test you are likely to run in the primary region and fails only after a real switchover, when the application is suddenly talking to a server that does not recognize it. The group replicates database contents, but it does not replicate the server level security objects that surround them, and that asymmetry is where teams get caught.

Consider SQL authentication first. A SQL login created at the server level on the primary does not automatically exist on the secondary server, even though the contained database user inside the database does replicate. After a role swap, the application presents credentials that the contained user can honor only if the login mapping resolves, and a server scoped login that was never created on the secondary leaves the user orphaned. The durable answer is to use contained database users wherever possible, since they travel with the database, and where server level logins are unavoidable, to script their creation on both servers as part of provisioning so the secondary is never missing a login the primary has.

Microsoft Entra authentication sidesteps much of this, because identity lives in the directory rather than on the server, so an Entra principal that can authenticate to the primary can authenticate to the promoted secondary as well, provided the server's Entra admin configuration matches. That last clause matters: the Entra admin assignment is a server level setting and should be configured identically on both servers. Using Entra authentication is generally the cleaner path for groups precisely because it removes the per server login replication problem, and it aligns with the broader identity posture most Azure estates are moving toward.

Firewall and network access form the parallel gap. Server level firewall rules, virtual network rules, and private endpoint configurations are server scoped and do not replicate. An application that reaches the primary through a private endpoint must have an equivalent private endpoint to the secondary server, or after a role swap the listener will resolve to a server the network cannot reach. The fix is to mirror the network access configuration on the secondary as deliberately as you mirror the compute size, and to include the network path in the drill, so that the planned promotion proves not just that the role moved but that the application can actually reach the new primary over the network it uses in production. A failover that moves the database to a server the application cannot route to is a role swap in name only.

### Why does authentication fail only after a role swap?

Because server level logins, firewall rules, and network configuration do not replicate through the group; only database contents do. After a role swap the application meets a server missing those objects. Mirror logins, firewall rules, and network access on the secondary, or use Entra authentication and contained users to avoid the gap.

## Connection resiliency the application must provide

A group hands the application a stable name, but it cannot reach into the application and add the retry logic that a role swap demands. During any failover, planned or forced, existing connections are terminated, and the application must reconnect. An application with no retry handling treats those dropped connections as hard errors and surfaces them to users, turning a few seconds of role swap into a visible outage. An application with sound retry logic reconnects against the new primary within seconds and the user sees, at most, a brief pause.

The retry pattern that fits Azure SQL is well established: catch the transient connection failures, wait with an increasing backoff, and retry a bounded number of times before giving up. The point during a role swap is that the listener will, after the swap completes, resolve to a server that accepts the connection, so a retry that waits out the swap succeeds where an immediate hard failure would not. Many data access libraries offer this resiliency as a built in option, and turning it on is a small change with a large payoff during a role swap. The same retry logic also smooths over the routine transient errors that Azure SQL produces during normal operation, the brief unavailability that clears on its own, so building it in serves double duty.

There is a DNS caching nuance that interacts with reconnection. The listener is a DNS name, and after a role swap its resolution changes to point at the new primary. An application or a runtime that caches DNS resolutions aggressively, beyond the time to live on the record, can keep trying the old region after the listener has already moved. Most modern runtimes respect the record's time to live, but environments with custom DNS caching should confirm they are not holding a stale resolution past a role swap, because a stale cache produces exactly the symptom of an application that will not follow the role swap even though the connection string correctly names the listener. When a drill shows the database moved and the listener moved but a particular host kept hitting the old region, DNS caching on that host is a prime suspect alongside a hard coded server name.

## What a group costs to run

Resilience is not free, and configuring a group responsibly means understanding the bill so the cost is a decision rather than a surprise on the invoice. The dominant cost is the geo-secondary itself, which is a fully provisioned database running continuously in the secondary region. It is billed like any other database of its tier and size, which is why sizing it to match the primary, necessary for it to carry production load after a role swap, also means paying for a second production grade database around the clock. There is no way to run a warm geo-secondary for free, and a secondary sized smaller to cut the bill is a false economy that turns a role swap into an overload.

Cross region data transfer is the second cost, incurred as the primary replicates changes to the secondary. For most transactional workloads this is modest relative to the compute cost of the secondary, but a write heavy workload generates correspondingly more replication traffic, so it is worth being aware of for high write volume databases. The figures here are the kind to confirm against current Azure pricing, since data transfer rates and database pricing both change, and a cost model built on stale numbers misleads.

The honest framing for the business is that a group roughly doubles the steady state database cost in exchange for surviving the loss of a region, and that this is the price of regional resilience rather than an inefficiency to optimize away. The optimization that is legitimate is using the geo-secondary for read offload, which extracts value from capacity you are paying for regardless, so that the secondary is not purely an idle insurance policy but an active part of the read serving architecture. Pointing your reporting workloads at the read-only listener turns the secondary's cost into partly a performance investment, which is the closest a group comes to paying for itself.

## A worked end to end setup, start to finish

It helps to walk the whole procedure once as a single narrative, because seeing the steps in sequence with the reasoning attached makes the ordering stick in a way that a command reference does not. Picture a retail application whose data lives in three databases, catalog, orders, and inventory, all on a primary server in East US, and a business requirement that the application survive the loss of that region with a recovery measured in minutes and minimal data loss.

The work starts not with the group but with the secondary server, because the group cannot exist before both partners do. You create a logical server in West US, the chosen disaster recovery region, having already confirmed that West US satisfies the data residency rules for this retail data and sits in a reasonable position for both replication latency and the analysts who will read from the secondary. Before going further, you reproduce the primary server's surrounding configuration on the new server: the Microsoft Entra admin assignment so directory based authentication resolves identically, the firewall and virtual network rules so the application's network path reaches the secondary, and any server scoped settings the application depends on. None of this replicates through the group, so doing it now prevents the post failover authentication and connectivity surprises that otherwise wait silently until the worst moment.

With both servers prepared, you create the group on the East US server, naming the West US server as the partner, choosing an automatic policy, and setting a grace period that reflects the business's tolerance rather than accepting whatever the default offers. The command returns quickly and the two listener endpoints come into existence, but no database is protected yet, so you resist the temptation to declare victory. You add the three databases to the group, which starts each one seeding to West US, and you watch the replication state until all three report a synchronized condition. A large inventory database takes the longest, which is expected, and you do not attempt anything that depends on it being failover ready until its seed completes.

Now comes the half of the work that actually delivers the protection, and the half the wizard never prompts for. Every connection string in the estate that touches these databases gets repointed at the read-write listener. The web application, the order processing worker, the background jobs, the scheduled exports, each one stops naming the East US server and starts naming the group. You centralize the listener endpoint in a single configuration source so that this is one fact the whole estate reads rather than a string scattered across a dozen deployments, and you separately point the analytics queries at the read-only listener with the read only intent set, so reporting load lands on the West US secondary and lightens the primary. You ship those configuration changes as a deliberate deployment and confirm each service comes up healthy against the listener.

Only now do you find out whether any of it works, and you find out on purpose rather than by accident. In a low traffic window you announce a drill, capture which region the read-write listener currently resolves to, and run a planned promotion that promotes the West US server. The listener swings to West US, and you immediately exercise the real write path, placing a test order through the application exactly as a customer would, and confirm it succeeds. You check that the analytics queries still resolve through the read-only listener, now pointing back at East US in its secondary role. Then you fail back to East US the same way and confirm the application follows again. You record the recovery time the application actually experienced, note that every service followed the listener with no straggler stuck on the old server name, and compare the measured recovery against the objective you promised the business. With those numbers in hand, the configuration is finally finished, because it has been proven rather than merely built, and the runbook now contains a procedure the team has executed rather than a procedure the team hopes will work.

That narrative is deliberately mundane at the end, and the mundanity is the point. A group setup that concludes with a boring, successful drill is one you can rely on during a real outage. A setup that concludes at the portal's green checkmark, with the drill perpetually postponed, is a setup whose first real test arrives at the least convenient possible moment, carrying every unexamined gap with it.

## Private connectivity and encryption across the group

Two cross cutting concerns, network privacy and data encryption, deserve explicit attention because they interact with failover in ways that are easy to overlook and painful to discover late. Both follow the same theme as the rest of this guide: the thing that works perfectly in the primary region can fail after a switchover precisely because it was configured for one region rather than two.

Private connectivity is the first. Many production databases are reached only over a private endpoint, with public network access disabled, so that traffic never traverses the public internet. A private endpoint is a server scoped resource, and like other server scoped configuration it does not extend itself to the partner server when you create a group. If the application reaches the East US server through a private endpoint and the West US server has no equivalent endpoint, then after a switchover the read-write listener resolves to a server the application's network cannot reach privately, and the connection fails even though the database is perfectly healthy. The correct configuration provisions a private endpoint to the secondary server as well, integrated into the network the application uses in its disaster recovery posture, so that the private path exists in both regions before it is needed. The listener resolves to whichever server is primary; the network must be able to reach both. Including the private network path in the drill, by confirming the application connects over its real network rather than a public fallback, is what proves this was done rather than assumed.

There is a DNS dimension to private connectivity worth naming, because it compounds the listener's own DNS behavior. Private endpoints rely on private DNS zones to resolve the database name to the private address, and the group listener must resolve correctly through that private DNS configuration in both regions. A private DNS setup that only accounts for the primary region produces an application that resolves the listener to a public address it cannot use, or fails to resolve the secondary's private address after a switchover. Confirm that the private DNS configuration covers the listener and both partner servers, so that resolution stays private and correct regardless of which region currently holds the primary.

Encryption is the second concern, and it centers on transparent data encryption when the encryption key is one you manage rather than one the platform manages. With a service managed key, encryption follows the database across regions without any extra thought, because the platform handles the key on both sides. With a customer managed key held in a key vault, the secondary database needs access to a key it can use, and a key vault in a single region becomes a dependency that can itself be lost in a regional outage, defeating the purpose of the geo-secondary. The robust configuration ensures the customer managed key is available to the secondary region, whether through a key vault that is itself resilient across regions or through a configuration that grants the secondary server access to a key it can reach even when the primary region is gone. A geo-secondary that cannot decrypt its own data after a switchover, because the key it depended on lived only in the failed region, is a group that protects the data right up until the moment you need it. As with the network path, the way to be sure is to include encryption in the drill: confirm the promoted secondary actually serves queries, which it can only do if it can decrypt, rather than assuming the key arrangement carried over.

Both concerns reduce to the same discipline that runs through every part of this guide. The group moves the database role between two servers, and anything the database depends on, logins, firewall rules, private endpoints, private DNS, and encryption keys, must exist and be reachable in both regions, because the group replicates the database and nothing around it. Build for two regions from the start, prove it with a drill that exercises the real network and the real encryption, and the role swap becomes the transparent event it is meant to be.

## Diagnosing a failover that did not move traffic

When a drill or a real switchover leaves some traffic stranded on the old region, the diagnosis follows a short decision path that isolates the cause quickly. Start at the database layer and confirm the role actually swapped, by running the show command and checking that the server you expected to become primary now reports the primary role. If the role did not swap, the role swap itself did not complete, perhaps because a database was still seeding or the command targeted the wrong server, and the problem is upstream of any connection concern.

If the role swapped cleanly but a particular service still cannot write, move to that service's connection string. The single most common finding is a server name where the listener should be, so inspect the exact string the failing service uses, not the string you believe it uses, since configuration drift between what is documented and what is deployed is itself a frequent culprit. A service writing successfully before the role swap and failing after it, while other services follow correctly, is almost a signature of a hard coded server name on that one service.

If the connection string correctly names the listener and the service still fails, suspect resolution and reachability rather than the group. Confirm the host running the service resolves the listener to the new region, which catches stale DNS caching that holds the old resolution past the role swap. Then confirm the host can actually reach the new primary over its network path, which catches a missing private endpoint or a private DNS configuration that only ever accounted for one region. Working through the layers in that order, role, then connection string, then resolution, then reachability, turns a vague report that the role swap did not work into a precise finding you can fix, and every one of those findings is cheaper to discover in a drill than in an incident.

## Closing verdict

A group is one of the most valuable configurations available in Azure SQL, and it is also one of the easiest to get superficially right and substantively wrong. The mechanics are genuinely simple: two commands build the group, the listeners appear, the secondary seeds, and the portal declares success. The substance lives entirely in the parts the wizard does not finish for you, and the whole of this guide reduces to making those parts deliberate rather than accidental.

Hold the listener-in-the-connection-string rule as the center of gravity. A group protects exactly the applications that connect through the read-write listener, and no others, because the listener is the only name engineered to follow the writable copy across regions. Every connection string that still names the underlying server is a service that will not follow a failover, and the only reliable way to find those services is to run a planned promotion drill and watch which connections move. Tune the grace period as a conscious trade off rather than accepting a default that silently caps your recovery time, mirror the server level logins and network access that do not replicate, give the application retry logic so a role swap is a pause rather than an outage, and place the database failover inside a wider disaster recovery design that moves the application tier alongside it. Do those things, rehearse the drill until it is boring, and the group becomes what it promises to be: a regional outage that your users never notice, instead of an incident that proves your safety net had a hole in it the whole time.

## Frequently Asked Questions

### Q: How do I set up an Azure SQL failover group from scratch?

Begin with two logical servers in two different regions, since a group cannot span one region. Confirm the secondary server has matching logins, firewall rules, and network access, because those do not replicate. Then run `az sql failover-group create` against the primary, naming the partner server, the promotion policy, and the grace period. That command provisions both listener endpoints and sets the policy but adds no databases. Add the databases with `az sql failover-group update --add-db`, which starts an asynchronous seed of each one to the secondary. Wait for every database to report a synchronized state before relying on the group. Finally, repoint every application connection string at the read-write listener, then run a planned promotion as a drill and fail back. The group is only finished after that drill proves the application follows the listener, regardless of what the portal reported earlier.

### Q: What is the read-write listener endpoint and why must connection strings use it?

The read-write listener is a stable DNS endpoint, `groupname.database.windows.net`, that always resolves to whichever server currently holds the writable databases. When a failover moves the writable role to the other region, Azure updates that name to point there, so an application connecting through it reaches the new primary without any configuration change. A connection string that names the underlying server, such as `myserver-eastus.database.windows.net`, is bolted to a single region and does not move, so after a switchover it keeps reaching a server that is now read only or unreachable. Using the listener is therefore not a style preference but the mechanism by which the group protects the application at all. Treat the listener as the only database address the application is allowed to know, and keep it in one configuration source so it is defined in a single place rather than copied across many services.

### Q: Should I use automatic or manual failover for my workload?

Automatic failover removes the human from the recovery path and promotes the secondary after the grace period when Azure determines the primary region is genuinely down. It suits workloads where fast, hands off recovery outweighs the small risk of an unnecessary failover. Manual failover keeps a human in the loop to confirm a true regional loss before accepting the data loss that a forced promotion entails, which suits workloads where avoiding an unnecessary failover matters more than the fastest possible recovery. Many teams run an automatic policy with a deliberately short grace period for fast recovery while keeping a manual forced promotion command ready in the runbook, so a confident engineer can promote immediately rather than waiting out the policy. The decision is a trade off between recovery speed and failover certainty, and it should be made explicitly and recorded, not left to whatever the setup wizard defaulted to.

### Q: How long does the initial seeding of a database into a group take?

Seeding copies the full database across regions for the first time, so the duration scales with the database size and the available throughput between the regions. A small database synchronizes quickly, while a large one can take a considerable stretch, and the time is not something you can rush, since it is bounded by how fast the data can be copied and applied in the secondary region. Plan the setup so that seeding happens in a window where you are not waiting on it for anything time sensitive, and do not attempt a failover while any database is still seeding, because a database that has not finished its initial copy cannot be promoted. Watch the replication state with the show command, where it moves from a seeding state through catchup to a synchronized state. Only when every database in the group reports synchronized is the group actually protecting all of them.

### Q: Can I add a group to a database that is already in production?

Yes, and it is the common case, because most teams add resilience after a workload is already live rather than before. Adding the group does not interrupt the primary database; the seed to the secondary runs in the background while the primary keeps serving traffic normally. The one operationally significant change is the connection strings: adding the group does nothing for an application that still connects through the underlying server name, so the production change that actually delivers the protection is repointing those connections at the read-write listener. Plan that connection string change as a deliberate deployment, ideally one that reads the listener from a central configuration source, and follow it with a planned promotion drill in a low traffic window to confirm the live application follows the listener. The group existing and the application using it are two separate facts, and only the second one protects you.

### Q: What happens to existing connections during a switchover?

Existing connections are terminated during the role swap, so the application sees a brief burst of dropped connections and must reconnect. This is true for both planned and forced failovers, because the writable role is moving to a different server and the open sessions against the old primary cannot continue. An application with sound retry logic catches the transient failures, waits with a short backoff, and reconnects, by which time the listener resolves to the new primary and the connection succeeds, so the user experiences a pause of seconds rather than an error. An application without retry logic surfaces the dropped connections as hard failures, which turns a quick role swap into a visible outage. The group cannot supply this resiliency for you; the application must provide it. Enabling the built in connection resiliency that most data access libraries offer is a small change that converts a failover from an incident into a non event.

### Q: Does the read-only listener point to a local replica or the geo-secondary?

The read-only listener of the group, `groupname.secondary.database.windows.net`, routes to the geo-secondary server in the partner region. That is the right endpoint for cross region reporting that you want served from the disaster recovery copy. It is distinct from the local read replica that a Business Critical database keeps inside its own region, which you reach by setting `ApplicationIntent=ReadOnly` on a connection to the read-write listener rather than the read-only listener. The two read paths serve different purposes: the geo-secondary path uses the remote copy for cross region reads, while the local replica path offloads reads without leaving the primary region. Choose by where you want the read served and what latency the consumer can tolerate. In both cases, setting the read only application intent is required so the driver honors the routing rather than sending the query to the writable replica.

### Q: How much does running a group add to my Azure bill?

The main cost is the geo-secondary, a fully provisioned database running continuously in the secondary region and billed like any database of its tier and size. To carry production load after a switchover it should match the primary's compute size, which means paying for a second production grade database around the clock. A secondary sized smaller to save money becomes an overload the moment it is promoted, so undersizing is a false economy. A secondary cost roughly equal to the primary, effectively doubling the steady state database spend, is the price of surviving a regional outage. Cross region data transfer for replication adds a smaller amount that grows with write volume. The legitimate optimization is pointing reporting workloads at the read-only listener so the secondary does useful read work instead of sitting idle, which turns part of its cost into a performance investment. Confirm current database and data transfer pricing against the official pricing pages before you model the exact figure.

### Q: Can I fail back to the original region after a switchover?

Yes, and failing back is a first class operation that your runbook should cover as fully as failing over. After the primary region recovers, a planned promotion promotes the original primary back to the writable role with no data loss, since a planned failover synchronizes before swapping. Mechanically it is the same `set-primary` command, run against the server you want to become primary again. Failing back is not automatic; the automatic policy promotes the secondary during an outage but does not move the role back on its own when the original region returns, because deciding when the original region is trustworthy again is a judgment call. A complete drill exercises both directions, failing over and then failing back, because a runbook that only rehearses one direction leaves the team improvising the other under pressure. Confirm the application follows the listener in both directions during the drill.

### Q: What is the difference between active geo-replication and a group?

Active geo-replication creates and maintains an asynchronous readable copy of a database in another region, but it gives you no single name that follows the writable copy, no way to move several databases as a unit, and no automatic promotion when a region fails. A group is built on top of geo-replication and adds exactly those missing pieces: the two listener endpoints that abstract away which server is primary, the grouping of databases that should fail over together, and the policy that can promote the secondary automatically after a grace period. In practice, most teams that want regional resilience for Azure SQL Database want a group rather than raw geo-replication, because the listener and the orchestrated promotion are what make a failover transparent to the application. Geo-replication alone is appropriate mainly when you need a readable secondary for a specific purpose and are handling the endpoint and promotion logic yourself.

### Q: How do groups work for Azure SQL Managed Instance?

A managed instance group operates at the instance level rather than the individual database level, so it moves all databases on the instance together as a single unit. You do not add and remove individual databases the way you do with the Azure SQL Database variant, because the unit of failover is the whole instance. The listener concept is the same, with a read-write endpoint that follows the primary and a read-only endpoint for the secondary, and the policy, grace period, and drill discipline all carry over unchanged. The practical implication is that you plan around moving everything on the instance at once, which is usually what you want for a managed instance, since its databases often form a single application's data tier. Mirror the instance level configuration on the secondary instance, including any cross instance dependencies, so that after a switchover the promoted instance is a complete environment rather than one missing a setting the primary had.

### Q: Why should I group multiple databases in the same group?

Group databases together when they must always share a region, typically because they reference one another or must stay mutually consistent for the application to function. Putting them in one group guarantees they fail over as a unit, so you never end up with one database promoted to a new region while a related database stays behind, which would leave the application reading from two regions at once. The cost of grouping is that the whole arrangement moves together, so a failover triggered by a problem with one database also moves the others. Keep genuinely independent databases apart so their failovers do not entangle and so each can be moved for maintenance without disturbing the rest. Decide membership by the question of which databases the application cannot tolerate being split across regions, and let that consistency requirement, rather than convenience, define the boundaries of each set.

### Q: Why does my secondary database show as not synchronized?

A secondary that does not reach or stay in a synchronized state usually points to capacity or throughput pressure on the secondary, not to a problem with the configuration itself. If the secondary is sized smaller than the primary, it may not keep up with the change rate the primary generates, so it lags and reports a catchup rather than a synchronized state. The fix is to size the secondary to match the primary, which you need anyway for it to carry load after a switchover. A secondary still in a seeding state simply has not finished its initial copy, which is normal for a large database and resolves with time. Persistent lag despite matching capacity warrants checking for throttling on the secondary and confirming the cross region replication path is healthy. Configure an alert on the replication state so a database falling out of synchronization becomes a warning you act on, since a degraded secondary is a group that will not protect you when you need it.

### Q: Do I need retry logic in my application if I have a group?

Yes, because the group moves the database but cannot reconnect the application for you. During any failover, open connections are dropped and the application must reestablish them against the new primary. Without retry logic, those dropped connections surface as hard errors during the role swap, so a failover that should be a brief pause becomes a visible outage. With retry logic that catches transient failures, waits with an increasing backoff, and retries a bounded number of times, the application reconnects within seconds once the listener resolves to the new primary, and the user sees little or nothing. The same retry handling also smooths over the routine transient errors Azure SQL produces during normal operation, so it earns its place regardless of failover. Most data access libraries offer connection resiliency as a built in setting, and enabling it is a small change with a large payoff during the exact moment the group is meant to protect you.

### Q: How do I choose the right region for my secondary server?

Settle data residency first, because a legal requirement to keep data in a jurisdiction can eliminate most regions before any technical factor applies. Among the regions residency permits, prefer the designated paired region as a starting point, since Azure aligns certain platform recovery behaviors with region pairs. Then validate latency in two directions: the replication latency between primary and secondary, which influences how far behind the secondary runs and therefore the data at risk in a forced promotion, and the latency from any read offload consumers to the secondary, which affects reporting performance if you serve cross region reads from it. Choose the region that satisfies residency, aligns with the pairing where possible, and balances both latency concerns. Get this right at the start, because the secondary region is the one decision that is expensive to revisit, since changing it means rebuilding the group and reseeding every database from scratch.

### Q: What is the grace period and how should I set it?

The grace period is how long Azure waits, after detecting a problem in the primary region, before it will promote the secondary automatically at the risk of losing the most recent unreplicated transactions. The wait exists so a brief blip in the primary does not trigger a data loss failover that was not needed. Its consequence is that your effective recovery time for an automatic promotion includes the entire grace period, so a long grace period silently caps how fast the configuration can recover. Set it as a deliberate trade off between tolerating a transient interruption without failing over and bounding your worst case recovery time, and reconcile the chosen value with any recovery objective you have quoted to the business. A team promising a tight recovery while leaving a long grace period has promised something the configuration cannot deliver during an automatic promotion. Record the chosen value in the runbook so it is a decision rather than a default.

### Q: How do I monitor a group so I know when it fails over?

Configure alerts on two things: the occurrence of a failover and the replication state of the databases in the group. An alert on promotion events tells the team the writable role moved even when the application rode through it without surfacing errors, which matters because a smooth failover can otherwise go unnoticed until someone wonders why traffic is in a different region. An alert on replication state catches a database falling out of a synchronized state, often a sign the secondary is throttling or undersized, so you fix a degraded secondary before an outage rather than discovering during one that the safety net was already compromised. Build these into the same monitoring you use for the rest of the database tier, and treat a replication state warning with the seriousness of an impending outage, because a group whose secondary is not synchronized is a group that will not actually protect you when the primary region fails.

### Q: Can a group protect me from accidental data deletion?

No, and relying on it for that is a dangerous misunderstanding. A group replicates the current state of the database faithfully, including a mistaken deletion or a bad migration, and the change reaches the secondary within seconds, so failing over lands you on an identical damaged copy. The group solves the lost region problem, not the corrupted data problem. The right tools for accidental deletion are point in time restore and an appropriate backup retention policy, which let you recover the database to a moment before the damage. A complete resilience posture uses both: the group for regional outages and point in time restore for logical corruption, because the two failure modes are unrelated and neither tool covers the other. Treating the geo-secondary as a backup is one of the more common and more costly conceptual errors, because it feels like a safety copy while offering no protection against the most frequent cause of data loss, which is human error rather than regional failure.

### Q: Can I run application workloads against the geo-secondary while it is a secondary?

You can run read only workloads against it through the read-only listener, which is the intended way to extract value from capacity you are paying for regardless. Pointing reporting queries, dashboards, and exports at the read-only listener with the read only application intent set offloads that read traffic from the primary and turns the secondary from a purely idle insurance copy into an active part of the read serving architecture. What you cannot do is write to the secondary while it holds the secondary role, because only the current primary accepts writes, and the secondary is kept consistent by replication from the primary. If a workload needs to write, it must reach the current primary through the read-write listener. Designing the read offload around the read-only listener is one of the few ways a group partly pays for itself, since the secondary's continuous cost buys both disaster recovery and read capacity rather than disaster recovery alone.

### Q: What happens if I delete the group, do my databases survive?

Deleting the group removes the grouping and the listener endpoints but does not delete the databases. The primary databases continue to exist and serve traffic on their original server, and the geo-secondary copies remain as standalone geo-replicated databases unless you also remove the replication relationship. What you lose immediately is the stable listener names, so any application connecting through the read-write listener loses its endpoint the moment the group is gone, which is exactly why the listener belongs in a single configuration source rather than scattered across services. If you intend to rebuild the group, be aware that recreating it generally means reestablishing the relationship and, depending on how you tear it down, potentially reseeding, so treat group deletion as a deliberate operation rather than a casual cleanup. Confirm the current behavior against official documentation before deleting a production group, since the exact consequences depend on how the teardown is performed.
