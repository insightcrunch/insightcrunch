---
layout: post
title: "Fix Azure SQL Error 40613: Database Not Available"
page_title: "Fix Azure SQL Error 40613 Database Is Not Currently Available: Causes, Transient Retry Logic, and Serverless Resume Explained"
date: 2022-08-15
categories: ["Technology"]
tags: ["Azure", "Azure SQL", "40613", "Troubleshooting", "Database", "Cloud Computing"]
excerpt: "Azure SQL error 40613 means the database is temporarily unavailable. Learn the real causes, when to retry with backoff, and how to handle serverless resume."
image: "/assets/images/blog/blog-91.webp"
reading_time: 63
author: "thomas-reid"
last_updated: 2022-08-15
lang: en
---
When an application throws Azure SQL error 40613, the message reads "Database '%.*ls' on server '%.*ls' is not currently available. Please retry the connection later." That single line panics teams because it looks like the database vanished. It almost never has. This code sits squarely on the transient-fault list, which means the platform is telling you the database is momentarily out of reach, not gone. The right response is rarely a frantic investigation and almost always a measured retry with backoff. The engineers who keep getting paged for 40613 are usually the ones whose code treats a five second blip as a permanent failure and surfaces it to the user.

![Diagnosing Azure SQL error 40613 database not currently available - Insight Crunch](/assets/images/blog/blog-91.webp)

The frustrating part is that 40613 is genuinely ambiguous on its own. The same code fires during a routine high-availability reconfiguration, during a service-tier change you triggered yourself, during the resume of a serverless database that auto-paused overnight, during sustained throttling, and during the rare regional incident. Five very different situations, one identical error string. This guide separates those five so you can tell, within a minute or two, which one is yours, whether to wait it out or act, and how to write the retry logic that turns the common cases into a non-event your users never notice. By the end you will be able to look at a burst of 40613 in your logs and say with confidence whether it was a failover that resilient code should have absorbed, a paused database that needed a warm-up, or something that warrants a support ticket.

## What Azure SQL Error 40613 Actually Means

Azure SQL Database is a platform-as-a-service offering, and that single fact explains most of what 40613 is trying to communicate. You do not run the engine on a server you own. Microsoft runs many replicas of your database across a fabric of nodes, keeps one primary serving your connections, and moves that primary around whenever the platform needs to patch a host, rebalance load, recover from hardware trouble, or apply a change you requested. During the brief instant when the primary is being relocated or rebuilt, there is no node ready to accept your session, and the gateway returns 40613. The database is not corrupt, not deleted, not missing. It is between homes.

### Why does a managed database report "not currently available"?

A managed database reports 40613 because the control plane is reconfiguring where and how your database runs. For a short window during a failover, a scaling operation, or a serverless resume, no replica is ready to serve connections, so the gateway rejects new sessions with this transient code until the database settles on a healthy node and comes back online.

That mental model matters because it changes the question you ask. With a database engine you manage yourself, "not available" usually means a process crashed, a disk filled, or the service stopped, and the fix is operational. With Azure SQL, "not currently available" usually means a routine platform event is in flight and the fix is patience plus retry. The deeper you understand how the service keeps itself highly available behind the scenes, the more obvious it becomes that occasional 40613 errors are the visible edge of a feature working as designed, not a defect. The high-availability machinery that produces these momentary drops is the same machinery described in the broader walkthrough of [how Azure SQL Database works internally](https://insightcrunch.com/2022/02/07/azure-sql-database-internals/), and reading that model first makes the troubleshooting that follows far more intuitive.

The full error text is worth quoting once so you recognize it in any form. The gateway returns it as "Database '<name>' on server '<server>' is not currently available. Please retry the connection later. If the problem persists, contact customer support, and provide them the session tracing ID of '<guid>'." Three pieces of that string are useful. The database and server names confirm which target failed, which sounds trivial but routinely reveals that an app pointed at the wrong logical server. The phrase "retry the connection later" is the platform itself instructing you to retry, which is your strongest hint about the correct handling. And the session tracing ID is the value support will ask for if the problem turns out to be a real incident rather than a blip, so capture it in your logs rather than discarding it.

### Is error 40613 the same as a database being offline?

No. An offline database in the traditional sense stays unreachable until an administrator brings it back. Error 40613 is a momentary state during a platform operation that clears on its own within seconds in the typical case. If your retry succeeds a few seconds later, the database was never offline in any meaningful sense; it was simply mid-reconfiguration.

This distinction is the single most useful thing to internalize. A database that is truly offline because it was dropped, paused without resume, or hit by an outage will keep returning errors no matter how many times you retry. A database that threw 40613 during a reconfiguration will accept your very next attempt, or the one after that. The behavior of the retry, not the text of the error, tells you which situation you are in. That is why the resilient pattern doubles as a diagnostic: a retry that clears the error proves it was transient, and a retry that never clears proves the cause is one of the persistent ones this guide covers later.

## How to Read the Error and Gather the Diagnostic Signal

Before you change a single line of code or open a single portal blade, collect three signals. They take under five minutes to gather and they narrow five possible causes down to one or two almost every time.

The first signal is the shape of the failures over time. Pull the timestamps of every 40613 in your application logs for the incident window. A tight cluster of failures lasting a handful of seconds that then stops on its own is the signature of a reconfiguration or failover. A wall of failures that begins at a precise moment and continues until you take action points at a paused serverless database or a genuine outage. A pattern that recurs on a schedule, the same minute every night or every weekend, hints at a maintenance window or an auto-pause cycle. The temporal shape alone eliminates several causes.

The second signal is what you were doing when it started. If your team or your automation triggered a service-tier change, a compute resize, a backup restore, or a geo-failover in the minutes before the errors, that operation is almost certainly the cause and the errors are expected collateral that resilient retry would have hidden. Check your activity log with a single command rather than relying on memory, because "nobody changed anything" is the most frequently wrong sentence in incident response.

```bash
# List recent management operations against the logical server and database.
# Anything here in the minutes before the 40613 burst is a prime suspect.
az monitor activity-log list \
  --resource-group myResourceGroup \
  --offset 1h \
  --query "[?contains(resourceId, 'myserver/databases/mydb')].{op:operationName.value, status:status.value, time:eventTimestamp}" \
  --output table
```

The third signal is the database health as the platform itself reports it. The Resource Health blade for the database in the Azure portal records whether the platform considered the database available, degraded, or unavailable during your incident window, along with whether the cause was a platform-initiated action or a customer-initiated one. This is the closest thing to an authoritative verdict, because it reflects the control plane's own view rather than your application's. You can reach the same information from the command line.

```bash
# Resource Health for the database resource. The availabilityState and the
# reason fields tell you whether the platform saw an outage or a planned action.
az rest --method get \
  --uri "https://management.azure.com/subscriptions/<sub-id>/resourceGroups/myResourceGroup/providers/Microsoft.Sql/servers/myserver/databases/mydb/providers/Microsoft.ResourceHealth/availabilityStatuses/current?api-version=2020-05-01"
```

### How do I tell a transient blip from a persistent failure?

Retry the connection three or four times with a short, growing delay between attempts. If a later attempt succeeds, the cause was transient and no further action is needed beyond making that retry automatic. If every attempt over a minute or two fails identically, the cause is persistent: a paused serverless database, a wrong connection target, or an outage.

This is worth doing deliberately even by hand during an incident, because it instantly halves the diagnostic tree. Open a query tool, attempt the connection, wait five seconds, attempt again, wait ten, attempt again. A success anywhere in that sequence sends you down the transient branch, where the only real fix is making retry automatic in code so the next occurrence is invisible. A run of identical failures sends you down the persistent branch, where you check the serverless state, the connection string target, and Resource Health in that order. Almost no incident requires more than these two branches.

The catalog of error numbers that accompany or resemble 40613 is also a signal. The gateway and engine emit a family of transient codes during reconfiguration and throttling, and recognizing the neighbors of 40613 helps you confirm you are looking at a transient event rather than something else wearing a similar mask. Error 40197 ("The service has encountered an error processing your request") accompanies reconfigurations and is also transient and retryable. Error 40501 ("The service is currently busy") signals engine-level throttling and carries a suggested wait. Errors 49918, 49919, and 49920 indicate the subscription or instance is too busy to process the request right now. Seeing 40613 interleaved with 40197 in the same brief window is a strong confirmation that a reconfiguration was in progress, because those two travel together during failovers.

## The Five Distinct Causes Behind Error 40613

Every 40613 you will ever see traces back to one of five situations. They differ in how long they last, whether you should act or wait, and what confirms them. The table below is the diagnostic spine of this guide; the prose after it expands each row into a confirmation step and a fix.

| Cause | Retry? | How long it lasts | Confirming signal |
| --- | --- | --- | --- |
| Transient reconfiguration or failover | Yes, with backoff | Seconds, clears on its own | Tight burst in logs, 40197 alongside, Resource Health shows a platform action |
| Service-tier or compute scaling in progress | Yes, with backoff | Seconds to a couple of minutes | Activity log shows a recent update or resize operation you triggered |
| Serverless database resuming from auto-pause | Yes, longer first attempt | Until warm-up completes, then stable | Database state was Paused, errors start on the first hit after idle time |
| Sustained throttling under extreme load | Yes, but also reduce load | Persists while the overload continues | 40501 or resource-limit codes alongside, high DTU or vCore utilization |
| Genuine platform outage | Yes, but escalate | Until the incident is resolved | Resource Health shows Unavailable, Azure Service Health posts an active event |

### Cause one: a transient reconfiguration or failover

This is the most common cause and the most benign. Azure SQL maintains your database with built-in redundancy, and from time to time the platform moves the primary replica to a different node. Patching the underlying host, recovering from a hardware fault, load rebalancing, and routine failovers all trigger this relocation. While the primary is being established on a new node, existing connections are severed and fresh connection attempts receive 40613 until the database is ready. The whole event usually spans seconds.

To confirm it, look at the temporal shape and the company the error keeps. A reconfiguration produces a short, dense cluster of failures that ends on its own, frequently with 40197 errors mixed in. The Resource Health blade will often attribute the brief dip to a platform-initiated action rather than anything you did. There is no command that prevents reconfigurations, because they are intrinsic to how the service stays available, so the fix is entirely on your side of the wire: resilient retry. Code that retries on 40613 with a short backoff absorbs these events so completely that you stop noticing them, and most teams discover their reconfigurations only when they go looking in the logs after adding proper retry handling. If you operate with a failover group for cross-region resilience, the same momentary drops accompany planned and forced failovers there too, which is why the setup walkthrough for [Azure SQL failover groups](https://insightcrunch.com/2023/06/12/configure-azure-sql-failover-groups/) stresses that application retry logic is a prerequisite, not an optional extra.

### Cause two: a service-tier or compute scaling operation in progress

Changing the service tier, switching between the DTU and vCore purchasing models, or resizing the compute allocation all trigger a reconfiguration that closely resembles a failover from the client's point of view. The platform provisions the new capacity, copies or repoints the database, and cuts over, and during the cutover your connections drop and new ones receive 40613. Unlike a spontaneous failover, this one has a clear instigator: someone or something asked for the change.

Confirm it by reading the activity log with the command shown earlier. A scaling or update operation in the minutes before the errors is the cause, full stop. The cure is to expect it. Scaling operations are routine and should be performed during low-traffic windows when feasible, and the application should retry through the cutover so that a planned resize does not become a visible incident. Teams that scale on a schedule, ramping up before a known peak and down afterward, learn to treat the brief 40613 burst at each transition as the normal cost of elasticity rather than an alarm. If your scaling is reactive rather than scheduled, the same retry logic still covers you, because the cutover behaves identically whether you triggered it at three in the afternoon or an autoscale rule triggered it at three in the morning.

### Cause three: a serverless database resuming from auto-pause

The serverless compute tier introduces a cause that confuses more engineers than any other, because it does not look transient at all on the first encounter. A serverless database automatically pauses after a configurable period of inactivity to save compute cost, and it stays paused until the next connection attempt wakes it. That first connection after a pause triggers a resume, and while the database warms up, connection attempts can fail with 40613. To an application that has been idle overnight, the first morning request appears to hit a dead database, when in fact it hit a sleeping one that is in the middle of getting up.

Confirm it by checking whether the database is on the serverless tier and what its state was when the errors began. A database that was Paused and threw 40613 on the very first request after a long idle period is textbook serverless resume. You can inspect the auto-pause configuration directly.

```bash
# Inspect the serverless auto-pause setting. A value other than -1 means the
# database pauses after that many minutes of inactivity and must resume on the
# next connection, during which 40613 can appear briefly.
az sql db show \
  --resource-group myResourceGroup \
  --server myserver \
  --name mydb \
  --query "{tier:currentServiceObjectiveName, autoPauseDelay:autoPauseDelay, minCapacity:minCapacity}" \
  --output table
```

There are three legitimate fixes, and which you choose depends on the workload. The first and best for most applications is to retry with a slightly more patient backoff so the resume completes before you give up; a resume takes longer than a failover, so a retry policy tuned only for sub-second blips may time out before the database is ready. The second is to extend or disable auto-pause if the cost savings are not worth the resume latency for a workload that needs to be responsive on the first hit. The command below sets the delay, and a value of negative one disables pausing entirely.

```bash
# Increase the inactivity window before auto-pause, or pass -1 to disable
# auto-pause so the database never goes cold. Disabling pausing removes the
# resume latency but also removes the compute savings of going idle.
az sql db update \
  --resource-group myResourceGroup \
  --server myserver \
  --name mydb \
  --auto-pause-delay 120
```

The third fix is to keep the database warm with a lightweight scheduled query if you want both the pause savings during truly idle periods and a guarantee that it is awake before your business hours begin. A tiny ping a few minutes before the first users arrive resumes the database on your schedule rather than on a customer's unlucky first click. Whichever you choose, recognizing serverless resume as the cause is the hard part; the fixes are straightforward once you know that a Paused state and a first-request failure are the fingerprints.

### Cause four: sustained throttling under extreme load

Azure SQL enforces the resource limits of your chosen tier, and when a database is pushed past what its compute allocation can sustain, the platform protects itself by rejecting work. Most throttling surfaces as resource-limit codes rather than 40613, but under extreme and sustained pressure you can see 40613 appear because the database genuinely cannot accept new connections while it is saturated. The distinguishing feature is that this cause does not clear on its own the way a reconfiguration does; it persists for as long as the overload persists, and retrying without reducing the load simply adds more failed attempts to an already drowning database.

Confirm it by correlating the errors with utilization. If your DTU consumption or vCore CPU sat pinned near its ceiling during the incident, and you saw 40501 or resource-limit codes alongside the 40613, the cause is load rather than a platform event. The fix here is not primarily retry, although retry with a longer backoff still helps smooth the recovery; the fix is to relieve the pressure. That can mean scaling the database up to a tier with more headroom, tuning the queries and indexing that are driving the consumption, spreading load across read replicas, or throttling the application's own request rate so it stops hammering a saturated instance. The full mechanics of how the platform meters and rejects work under pressure, and how to read the utilization signals that confirm it, are the subject of the dedicated guide to [Azure SQL DTU and throttling errors](https://insightcrunch.com/2022/08/29/fix-azure-sql-dtu-throttling/), which picks up exactly where the load-related branch of 40613 leaves off.

### Cause five: a genuine platform outage

Rarely, 40613 reflects an actual incident in the region or the service rather than a routine event. When this happens, no amount of client-side retry will help until the platform recovers, and the correct response shifts from coding to escalation. The signature is that Resource Health reports the database as Unavailable for an extended period and attributes it to a platform problem, and Azure Service Health shows an active advisory or incident affecting Azure SQL in your region.

Confirm it by checking both health surfaces. Resource Health gives you the database-specific verdict, and Service Health gives you the regional picture. If both point at an active incident, capture the session tracing ID from the error string, note the timeline, and open or follow the support and status channels rather than churning retries. Resilient retry is still correct to leave running, because it will reconnect automatically the moment the platform recovers and spare you a manual restart, but the resolution is in Microsoft's hands during a true outage. The reason this cause sits last is that it is the least common by a wide margin; the overwhelming majority of 40613 errors are the first three causes, and treating every occurrence as a suspected outage is how teams waste hours on what a five second retry would have solved.

## The Retry-the-Transient Rule: The Fix That Covers Most Cases

Here is the rule worth memorizing: error 40613 is on the transient-fault list, so the correct default response is resilient retry with exponential backoff, and a 40613 that never clears is a different problem the retry will reveal. That sentence does double duty. It tells you what to build, and it tells you how to diagnose: write the retry, and let its behavior expose whether you were dealing with a transient blip or one of the persistent causes. Code that retries turns failovers, scaling cutovers, and serverless resumes into events your users never see, and it converts the rare persistent cases into clearly visible signals because they are the only ones that survive the retry.

The shape of good retry logic is consistent regardless of language. Catch the connection failure, check whether the error number is on your retryable list, wait a short and growing interval with a little randomness added so a fleet of clients does not all reconnect in lockstep, and try again up to a sensible cap. The randomness, called jitter, matters more than it looks: without it, every instance of a busy application retries at the same instant after a reconfiguration and slams the recovering database with a synchronized thundering herd, which can prolong the very event you are trying to ride out.

### Which error numbers belong on the retryable list?

Retry on the transient connection and reconfiguration codes: 40613, 40197, 40501, 49918, 49919, and 49920, plus the connection-level codes a dropped session raises such as 4060, 233, 64, and 10928 through 10929. Treat any code off the list as a real fault to surface, so a bad password fails fast instead of looping.

That last point prevents a common mistake. A retry policy that catches every exception and retries blindly will loop forever on a genuine error like a syntax mistake, a permission denial, or a login failure, wasting time and hiding the real problem. The login-failure case in particular is worth keeping distinct, because 18456 looks like a connection problem but is an authentication problem that retry cannot fix; the separate guide to [the Azure SQL login failed error 18456](https://insightcrunch.com/2022/08/22/fix-azure-sql-login-failed-18456/) walks through reading its state number to localize the real cause. Keep your retryable list tight and let everything else fail fast.

Most platforms now ship retry handling so you rarely need to hand-roll the loop. In .NET with the modern Microsoft.Data.SqlClient driver, you can attach a configurable retry provider to the connection so transient errors are handled below your application code entirely.

```csharp
// Microsoft.Data.SqlClient built-in retry logic. The driver retries the
// configured transient error numbers (which include 40613) with backoff,
// so application code never sees the blip.
var options = new SqlRetryLogicOption
{
    NumberOfTries = 5,
    DeltaTime = TimeSpan.FromSeconds(5),
    MaxTimeInterval = TimeSpan.FromSeconds(60),
    TransientErrors = new int[] { 40613, 40197, 40501, 49918, 49919, 49920, 4060, 233, 64, 10928, 10929 }
};

var provider = SqlConfigurableRetryFactory.CreateExponentialRetryProvider(options);

using var connection = new SqlConnection(connectionString);
connection.RetryLogicProvider = provider;
connection.Open();
```

If you use Entity Framework Core, the equivalent is a single line in your context configuration that enables the SQL Server execution strategy, which already knows the Azure SQL transient codes and retries them with backoff.

```csharp
// EF Core enables resilient connections with one option. The SQL Server
// provider's execution strategy retries Azure SQL transient faults,
// 40613 among them, without further code.
optionsBuilder.UseSqlServer(
    connectionString,
    sqlOptions => sqlOptions.EnableRetryOnFailure(
        maxRetryCount: 5,
        maxRetryDelay: TimeSpan.FromSeconds(30),
        errorNumbersToAdd: null));
```

In Python the pattern is explicit but short. Wrap the connect-and-run in a loop that inspects the error, backs off, and retries only the transient numbers.

```python
import time, random, pyodbc

TRANSIENT = {40613, 40197, 40501, 49918, 49919, 49920, 4060, 10928, 10929}

def connect_with_retry(conn_str, max_tries=5, base=2.0):
    for attempt in range(1, max_tries + 1):
        try:
            return pyodbc.connect(conn_str)
        except pyodbc.Error as exc:
            code = exc.args[0]  # driver-specific; inspect the SQL error number
            number = getattr(exc, "sqlstate", None) or code
            if attempt == max_tries or not _is_transient(number, TRANSIENT):
                raise
            sleep = base * (2 ** (attempt - 1)) + random.uniform(0, 1)
            time.sleep(sleep)

def _is_transient(number, transient):
    # Map the driver's reported value to the numeric SQL error and test membership.
    try:
        return int(number) in transient
    except (TypeError, ValueError):
        return False
```

In Java with the Microsoft JDBC driver, you can configure connection retry properties on the connection string or wrap the logic in a resilience library such as Resilience4j, but the principle is identical: a tight transient list, exponential backoff, jitter, and a cap.

```java
// JDBC connection string with built-in connect retry. The driver retries
// the connection on transient failures including 40613 before giving up.
String url = "jdbc:sqlserver://myserver.database.windows.net:1433;"
           + "database=mydb;encrypt=true;"
           + "connectRetryCount=5;connectRetryInterval=10;"
           + "loginTimeout=30";
```

### How patient should the backoff be for a serverless database?

More patient than for a failover. A reconfiguration clears in seconds, so a policy that gives up after a few short attempts usually succeeds. A serverless resume takes longer to warm up, so a policy capped too tightly will abandon a database that was about to come online. Allow a longer total retry window when serverless is in play.

This is the one place where a single retry policy may not fit every workload. Applications that talk only to provisioned databases can use a snappy policy tuned for the seconds-long reconfiguration window. Applications that talk to serverless databases, especially ones that go fully idle, need a policy whose total elapsed retry time comfortably exceeds the resume warm-up, or they will convert a perfectly recoverable resume into a user-visible failure. If you run a mix, set the more patient policy as the floor, because over-waiting on a fast failover costs a few harmless extra seconds while under-waiting on a resume costs an actual error. The exact resume latency varies and should be verified against current behavior for your tier rather than assumed from an old number, but the design rule holds regardless of the figure: give serverless room.

## Preventing Error 40613 from Reaching Your Users

You cannot prevent reconfigurations, scaling cutovers, or the occasional outage, and you should not try, because they are the cost of a managed, highly available service. What you can prevent is those events reaching a user as a visible failure. Prevention for 40613 is almost entirely about resilience engineering rather than configuration.

The foundation is the retry logic covered above, applied everywhere the application opens a connection or runs a command, not just in the one code path someone remembered. A surprising number of 40613 incidents trace to an application that retries its main query path but not its health check, its background job, or its migration step, so the transient event slips through the unguarded door. Audit every place your code reaches the database and confirm the resilient policy wraps all of them.

The second layer is connection pooling discipline. A reconfiguration invalidates the existing connections in your pool, and an application that hands out a stale pooled connection without validating it will throw an error that looks like 40613's cousins even after the database is healthy again. Ensure your pool tests connections on borrow or recycles them promptly so a post-failover request gets a fresh, valid connection rather than a dead one held over from before the event.

The third layer applies specifically to serverless. If first-request latency after idle is unacceptable for your workload, decide deliberately between a longer auto-pause delay, disabling pause, and a keep-warm ping, rather than discovering the resume behavior through a production incident. The cost trade-off is real: pausing saves compute during idle periods, and removing the pause spends that saving to buy first-hit responsiveness. Make the call with the workload's actual idle pattern and latency tolerance in front of you.

The fourth layer is scheduling. Where you control when scaling and maintenance-adjacent operations happen, push them into low-traffic windows so the unavoidable brief cutover lands when the fewest users are watching. Combined with retry, scheduled changes become essentially invisible, while the same change fired during peak traffic, even with retry, produces a flurry of retried requests that can briefly raise latency.

The fifth layer is observability. Log every 40613 with its timestamp, the session tracing ID, the database and server names from the message, and the eventual outcome of the retry. This turns the error from a mystery into a measurable event. You will be able to see your reconfiguration frequency, confirm that retries are absorbing them, and immediately distinguish a normal week from one where the same error suddenly stops clearing and signals a real problem. The teams that handle 40613 calmly are invariably the ones who can pull up a chart of it.

## Errors That Get Confused with 40613

Several Azure SQL errors live near 40613 in the symptom space, and mistaking one for another sends you down the wrong branch. Knowing the neighbors keeps your diagnosis honest.

Error 40197 is the closest relative. It reads "The service has encountered an error processing your request. Please try again," and it accompanies the same reconfigurations that produce 40613. Both are transient, both belong on your retry list, and seeing them together confirms a reconfiguration rather than a different cause. Treat 40197 exactly as you treat 40613.

Error 40501 is the throttling signal. It reads that the service is busy and carries a recommended wait time before retrying. Where 40613 says the database is not currently reachable, 40501 says it is reachable but overloaded. If you are seeing 40501, the load-relief branch matters more than the retry branch, and the throttling guide referenced earlier is the place to go deep.

Errors 49918, 49919, and 49920 indicate the subscription or instance cannot process the request because too many operations are in flight or the instance is too busy. They are retryable like 40613 but point at operation volume rather than a single database's availability, so a flood of them suggests you are issuing management operations faster than the platform will accept.

Error 18456 is the impostor that catches the most people. It is a login failure, and although it interrupts a connection just as 40613 does, retrying it is pointless because the credentials, firewall rule, or database context is wrong and will be wrong on every attempt. The tell is that 18456 carries a state number that pinpoints the authentication cause, whereas 40613 carries a session tracing ID and an instruction to retry. If your retry loop is spinning on 18456, you have miscategorized an authentication problem as a transient one, and the fix is to read the state and correct the credential or firewall rather than retry.

The resource-limit codes 10928 and 10929 report that the database has hit a session, request, or resource governance limit. They can appear under heavy concurrency and are retryable with backoff, but persistent occurrences mean you are bumping the ceiling of your tier and should consider scaling or reducing concurrency rather than relying on retry alone.

### Why does retrying 18456 never work when retrying 40613 does?

Because they describe opposite situations. Error 40613 means the database is momentarily unreachable and will accept your connection shortly, so a retry succeeds once the platform settles. Error 18456 means the connection was reached but the login was rejected for a fixed reason, so every retry presents the same rejected credential and fails identically.

## Real-World 40613 Scenarios and How Each Resolves

The abstract causes become concrete in the situations engineers actually report. Walking through the recurring ones shows the diagnosis in motion.

A team wakes to a pager alert showing a burst of 40613 at 2:14 in the morning that stopped by 2:15. Nothing was deployed, nobody was awake, and the application recovered on its own. The temporal shape, a tight cluster that self-cleared, plus a Resource Health entry attributing a brief dip to a platform action, identifies a routine failover. The correct outcome is not an investigation but a code change: resilient retry would have absorbed the entire event, and the fix is to add it so the next 2 a.m. failover never pages anyone. This is the single most common 40613 story, and its lesson is that the absence of a human cause points at the platform doing its job.

A serverless database that backs an internal tool throws 40613 every morning on the first request after the overnight idle period, then works flawlessly for the rest of the day. The database state was Paused, and the first hit triggered a resume that the application's short retry policy abandoned before warm-up finished. The fix is a more patient backoff, or a keep-warm ping a few minutes before the workday, or a longer auto-pause delay if the cost trade-off favors responsiveness. Recognizing the Paused state and the first-request timing is the whole diagnosis.

An application starts returning 40613 to users the instant an engineer kicks off a service-tier upgrade to handle growing load. The activity log shows the update operation seconds before the errors began. This is the scaling cutover, working as designed, made visible only because the application lacked retry on that path. The resolution is to retry through cutovers and to schedule deliberate scaling changes for quieter windows, turning a planned improvement into a silent one.

A high-traffic service sees 40613 interleaved with 40501 during a traffic spike, and the errors persist rather than clearing. DTU utilization was pinned at its ceiling throughout. This is throttling under sustained load, not a reconfiguration, and retry alone makes it worse by adding attempts to a saturated database. The resolution is load relief: scale up, tune the heaviest queries, add read scale-out, or rate-limit the application. The persistence of the errors and the company of 40501 distinguish this from the benign causes.

A globally distributed application using a failover group sees a wave of 40613 across many clients at once during a regional failover event. Connections to the old primary dropped and the new primary needed a moment to accept them. Because the application had resilient retry, most clients reconnected within seconds and users barely noticed. The scenario validates the design principle that failover groups and application retry are partners; the group provides the regional resilience and the retry makes the cutover smooth from the client's side.

An automation pipeline that restores a database from backup hits 40613 while the restore is still finalizing. The database was mid-provisioning and not yet ready to accept connections. The fix is for the pipeline to poll the database's readiness and retry the connection until the restore completes rather than assuming the target is available the instant the restore command returns. Treating provisioning as a transient window the same way you treat a failover keeps the automation robust.

## How the Platform's High-Availability Design Produces 40613

Understanding why these momentary drops are unavoidable makes peace with them far easier. Azure SQL keeps your data on multiple replicas, with one acting as the primary that serves your reads and writes and others kept in sync as standbys. The platform constantly monitors the health of the nodes hosting these replicas, and it will promote a standby to primary whenever the current primary's host needs maintenance, suffers a fault, or must be vacated for load balancing. That promotion, fast as it is, has a moment where the old primary is no longer serving and the new one is not yet serving, and that moment is when 40613 appears for any connection attempt that lands in the gap.

The same gap opens during the scaling and provisioning operations that repoint your database to different compute, and during serverless resume, where the database has no active compute at all until the resume completes. In every case the error is the honest report of a transitional state, not a malfunction. A service that hid these transitions entirely would have to keep redundant capacity hot at all times and never move your database, which would forfeit the elasticity and efficiency that make the platform worthwhile. The bargain the service offers is that it will keep your database highly available across hardware faults and maintenance with no operational work from you, in exchange for the occasional seconds-long blip that your retry logic is expected to absorb. Once you see the architecture this way, 40613 stops being an error to eliminate and becomes a contract term to design around. The deeper treatment of replicas, primaries, and the reconfiguration machinery in the internals guide referenced earlier fills in the mechanics, and the failover groups guide shows how the same principle scales to cross-region resilience.

If you want to move from reading about these events to producing them on demand and watching your retry logic absorb them, the [hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) let you trigger a scaling cutover, pause and resume a serverless database, and observe exactly when 40613 appears and clears against your own code. Pairing that with the [scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) lets you practice the diagnostic branch under simulated incident pressure, so the five-cause split and the retry-or-investigate decision become reflexes rather than something you reconstruct from documentation while the pager is buzzing.

## Designing Retry That Is Safe, Not Just Present

Adding a retry policy is the easy half. Adding one that does not silently corrupt your data is the half that separates a robust application from a fragile one. The danger lives in what was happening on the connection at the instant it dropped, because a reconfiguration does not politely wait for your transaction to finish.

### What happens to an in-flight transaction when 40613 interrupts it?

The transaction is rolled back. When the primary replica relocates, any open transaction on the severed connection is aborted and never commits, so the database is left in a consistent state with that unit of work undone. Your application sees the connection failure, and on retry it is talking to a fresh session with no memory of the abandoned work.

This rollback behavior is a gift and a trap at the same time. It is a gift because it guarantees you will never have a half-applied transaction lingering after a failover; the database's consistency is preserved automatically. It is a trap because your application code must not assume the work succeeded just because it was sent. If you fired an insert, lost the connection to 40613, and blindly retried by issuing the same insert again, you might think you are recovering from a transient blip when in fact the first attempt rolled back cleanly and the retry is the only one that lands, which is correct, or the first attempt had already committed before the drop and the retry now duplicates it, which is a bug. The way out is idempotency.

The retry that is always safe is the one whose operation produces the same result whether it runs once or three times. A connection that only reads is trivially safe to retry. A write that uses a deterministic key, an upsert keyed on a natural identifier, or a check-then-act guarded by a uniqueness constraint can be retried without fear of duplication. A naive insert with an auto-generated surrogate key fired outside any deduplication is the dangerous case, because a retry after an ambiguous failure can produce two rows. Design the write path so that replaying it is harmless, and your retry on 40613 becomes unconditionally safe. Where idempotency is genuinely hard, wrap the work in a transaction so that an interrupted attempt rolls back wholesale and the retry starts clean, which is precisely the behavior the platform already gives you for free during a reconfiguration.

There is a subtlety in distinguishing a failure that happened before the work was sent from one that happened after. A 40613 thrown while opening the connection is unambiguous: nothing ran, so retrying is pure upside. A failure thrown after a command was dispatched but before the result came back is the ambiguous middle, where you cannot be certain whether the work committed. Idempotent operations make that ambiguity irrelevant. Non-idempotent operations force you to either make them idempotent or to record a unique operation token with the work so a retry can detect that the prior attempt already succeeded and skip the duplicate.

### Should the retry policy live in the driver, the framework, or the application?

Prefer the lowest layer that can handle it cleanly. Driver-level and framework retry, such as the SqlClient provider or the EF Core execution strategy, suits connection and simple command failures because it is centralized and consistent. Application-level retry fits when the unit you must replay is a multi-step business operation the lower layers cannot see whole.

The reason to push retry as low as possible is consistency. A retry policy buried in the data-access driver applies uniformly to every query in the application, including the ones a developer forgot existed, so a transient failover is absorbed everywhere at once. A retry policy scattered through application code is only as good as the discipline of the team applying it, and the gaps are exactly where production incidents hide. The exception is the multi-statement business transaction that must succeed or fail as a unit, where only the application knows the boundary of the work to replay. In that case, wrap the whole operation in an application-level resilient block that begins a transaction, runs the steps, and commits, retrying the entire block on a transient fault so the unit replays atomically. Combining a low-level policy for ordinary queries with a higher-level policy for these compound operations gives you both breadth and correctness.

## Tuning Serverless to Control When 40613 Can Appear

Because serverless resume is the cause that most often surprises people, it deserves a deliberate configuration strategy rather than a default left untouched. The serverless tier exposes three levers that together determine how often a cold resume can produce 40613 and how long that resume takes.

The auto-pause delay sets how long the database must sit idle before it pauses. A short delay aggressively reclaims compute during quiet periods and maximizes the cost saving, at the price of more frequent resumes and therefore more opportunities for a first-request 40613. A long delay keeps the database awake through brief lulls, trading some saving for fewer cold starts. Disabling auto-pause with a value of negative one removes resume-related 40613 entirely, because the database never goes cold, and is the right call for any workload where first-hit latency matters more than idle savings.

The minimum and maximum capacity bounds set the compute floor and ceiling the database scales between while active. They do not directly cause 40613, but the minimum capacity influences how quickly a resumed database becomes responsive, and the maximum protects you from the throttling-related branch by giving the database room to absorb load spikes before it saturates. Setting these thoughtfully keeps both the resume and the overload causes of 40613 in check at once.

```bash
# Tune the three serverless levers together: a longer pause delay to reduce
# cold resumes, and capacity bounds that give the database room under load.
az sql db update \
  --resource-group myResourceGroup \
  --server myserver \
  --name mydb \
  --auto-pause-delay 240 \
  --min-capacity 1 \
  --max-capacity 8
```

The keep-warm pattern deserves its own mention because it gives you the best of both worlds for predictable workloads. A scheduled, lightweight query that runs a few minutes before your business day resumes the database on your timetable, so the first real user hits an already-warm database while the database still gets to pause through the genuinely idle overnight hours. The ping costs almost nothing and converts an unpredictable customer-triggered resume into a predictable system-triggered one. For workloads with no predictable rhythm, a more patient retry policy that outlasts the resume is the cleaner answer, since there is no schedule to warm against.

Whichever combination you choose, the goal is to make the appearance of 40613 from serverless a conscious decision rather than an accident. A team that has set the pause delay, the capacity bounds, and a warm-up or patient retry on purpose will never be surprised by a morning resume error, while a team running pure defaults will rediscover the behavior in production every time the workload pattern shifts.

## Monitoring and Alerting So 40613 Tells You Something

Logging the error is the floor; turning it into signal is the goal. The reason to invest in observation is that 40613 is normal in small amounts and alarming in large or persistent amounts, and only measurement tells the two apart. An alert that fires on a single occurrence will cry wolf during every routine failover, and an alert that never fires will miss the day a transient error turns persistent.

The useful approach is to track the rate and the clearing behavior rather than the raw count. A handful of 40613 that each clear on the first retry is healthy background noise from the platform keeping itself available. A rate that climbs well above your established baseline, or a cluster that stops clearing on retry, is the signal worth waking someone for. Build the alert on the delta from normal, not on presence, so the platform's routine maintenance does not generate noise while a genuine problem still surfaces promptly.

If your application logs flow into a Log Analytics workspace, a query that counts transient connection failures over time and compares against a rolling baseline gives you both the chart and the alert source.

```kusto
// Count 40613 occurrences per 5-minute bin from application traces, so you can
// chart the baseline and alert on a rate that rises above it or stops clearing.
AppExceptions
| where TimeGenerated > ago(24h)
| where OuterMessage has "40613" or OuterMessage has "not currently available"
| summarize occurrences = count() by bin(TimeGenerated, 5m)
| order by TimeGenerated asc
```

Pair the application-side view with the platform-side metrics. The database's own telemetry exposes connection successes and failures and resource utilization, and correlating a spike in failed connections with high utilization confirms the throttling branch, while a spike with normal utilization and a matching Resource Health event confirms the reconfiguration branch. The correlation is what makes the monitoring diagnostic rather than merely descriptive: the same 40613 count means very different things depending on what the utilization and health signals were doing at the same moment.

Capture the session tracing ID in every logged occurrence. On the rare day a 40613 turns out to be a real incident, that identifier is what support will use to trace your specific sessions through the platform, and an application that discarded it forces you to reproduce the problem to get one. The few bytes of storage are cheap insurance.

## Testing Your Resilience Before the Platform Tests It for You

The worst time to discover that your retry logic does not work is during a real failover. The best time is during a test you triggered on purpose. Azure SQL lets you force the kind of reconfiguration that produces 40613, which means you can validate your handling on demand rather than waiting for the platform to do it unannounced.

A manual failover of the database triggers the same primary relocation that a spontaneous failover would, and watching your application during one tells you immediately whether your retry absorbs it or whether users see errors.

```bash
# Force a failover to relocate the primary replica, reproducing the brief
# unavailability that yields 40613. Run this in a test environment and watch
# whether your retry logic absorbs the cutover transparently.
az sql db failover \
  --resource-group myResourceGroup \
  --server myserver \
  --name mydb
```

For serverless, the test is to let the database pause and then hit it cold, confirming that your more patient retry policy rides out the resume. You can hasten a pause in a test environment by setting a very short auto-pause delay, waiting for the database to go idle, and then issuing a first request while watching the latency and the error handling. If your policy abandons the resume, you will see it here, in a controlled setting, instead of in a morning incident.

For the throttling branch, a load test that drives utilization to the ceiling reveals whether your application degrades gracefully or melts down under the resource-limit and 40613 errors that saturation produces. The point of all three tests is the same: every cause of 40613 except a true outage can be reproduced deliberately, so there is no excuse for meeting any of them for the first time in production. A resilience test plan that exercises a forced failover, a serverless cold start, and a saturation event gives you confidence that the code path you reasoned about on paper actually behaves the way you intended when the connection really drops.

Running these exercises against a scratch database is exactly what the VaultBook labs referenced earlier are built for, and rehearsing the decision tree under the simulated incidents in the ReportMedic drills turns the reasoning in this guide into muscle memory. The combination of producing the error on demand and practicing the response is what moves a team from reacting to 40613 to expecting it.

## Connection Policy, Timeouts, and Giving Retry Room to Work

Two configuration details quietly determine how gracefully your application rides out the brief window that produces 40613, and both are easy to overlook because they sit in the connection setup rather than in the error handling.

The first is the server connection policy, which controls how your client reaches the database behind the logical server gateway. In the proxy mode, every query travels through the gateway, which adds a hop but keeps reconnection simple because the gateway always knows where the current primary lives. In the redirect mode, the gateway hands the client a direct path to the node hosting the database after the initial handshake, which lowers latency for the steady state. The relevance to 40613 is that after a reconfiguration relocates the primary, a redirected client must re-establish the path to the new node, so the reconnection sequence differs slightly between the two modes. Neither mode prevents the transient error, and both reconnect fine with proper retry, but knowing which policy your connections use explains the exact reconnection behavior you observe in logs after a failover and prevents you from misreading a normal redirect re-handshake as a new problem.

The second detail is the timeout configuration, which decides whether your retry policy ever gets the chance to succeed. The connection timeout governs how long the client waits to establish a session before giving up, and the command timeout governs how long it waits for a query to return. If your connection timeout is shorter than the time the platform needs to settle after a reconfiguration, the client abandons the attempt before the database is ready, and your retry sees a timeout rather than a clean 40613, which can confuse the handling. A connection timeout with enough headroom to span a typical reconfiguration, combined with a retry policy whose total elapsed window comfortably exceeds the longest expected transitional state, gives the platform room to recover and your code room to reconnect. The interplay matters most for serverless: a connection timeout too short to outlast a resume converts a recoverable cold start into a hard failure no retry count can fix, because each attempt dies before warm-up completes.

### How long is the database unavailable during a typical 40613 event?

It depends on the cause. A routine reconfiguration or failover usually clears in seconds. A scaling cutover can run from seconds to a couple of minutes as new capacity comes online. A serverless resume takes longer and varies by tier. An outage lasts until the platform resolves it. Tune timeouts to outlast the longest case.

The practical move is to size your connection timeout and retry window against the worst transient case your workload realistically encounters rather than the best. An application that talks only to provisioned databases can keep both tight, because reconfigurations and scaling cutovers clear quickly. An application that touches serverless databases needs both wider, so the resume warm-up fits inside the window. Sizing for the worst transient case costs nothing on the common fast cases, where success arrives long before the generous limits are reached, and it saves you on the slow ones, where a tight limit would have turned a recoverable event into an error.

## A 60-Second Runbook for the Next 40613

When the next burst of 40613 lands, the goal is to reach the right branch fast rather than to investigate everything. Start by pulling the timestamps and asking whether the failures clustered briefly and self-cleared or whether they persisted. A brief, self-clearing cluster is a reconfiguration or scaling cutover, and the action is to confirm with the activity log whether a change you triggered lines up with the timing, then ensure resilient retry covers the affected path so the next one is invisible. There is nothing to fix on the platform side, because the platform behaved correctly.

If the failures persisted rather than clearing, branch on the database tier. A serverless database whose state was Paused and that failed on the first request after idle is a resume, and the action is to make the retry more patient, add a keep-warm ping, or extend the auto-pause delay. A database that was active throughout, with utilization pinned near its ceiling and 40501 errors alongside, is throttling, and the action is load relief through scaling, query tuning, or rate limiting rather than retry. A database that Resource Health reports as Unavailable for an extended period, with a matching Azure Service Health advisory, is a genuine incident, and the action is to capture the session tracing ID, leave resilient retry running so the application reconnects automatically on recovery, and follow the support and status channels.

The runbook fits in a minute because the signals that separate the branches are quick to read: the temporal shape of the failures, the activity log, the serverless state, the utilization, and the two health surfaces. Each is a single glance, and together they route you to one of five known causes with one of five known actions. The teams that handle 40613 without drama are the ones who have this branch reflexively memorized, which is exactly what rehearsing the scenarios in a drill environment builds. Run the forced failover, the serverless cold start, and the saturation test once in a safe environment, walk the runbook against each, and the real incident becomes a formality rather than an investigation.

## Geo-Replication, Read Scale-Out, and 40613 Across Replicas

The behavior of 40613 takes on extra nuance once your database spans more than one replica for reading or for regional resilience, and understanding those cases prevents a class of confused diagnoses.

When you enable read scale-out, read-only traffic is routed to a secondary replica while writes go to the primary. A reconfiguration can relocate either the primary or the readable secondary, so a 40613 on a read-only connection points at the secondary being momentarily unavailable rather than anything wrong with the primary that your writes use. The handling is identical, resilient retry, but the diagnosis differs: a read path throwing the error while the write path stays healthy tells you the secondary reconfigured, not the primary. Routing your read and write connections through distinct connection strings makes this distinction visible in your logs, because the error then carries the read-only intent that localizes it to the secondary.

Geo-replication and failover groups add the cross-region dimension. During a planned or forced regional failover, the secondary in the partner region is promoted to primary, and connections to the old primary drop while the new one comes online, producing a wave of 40613 across clients at once. This is the expected cost of a regional cutover, and an application built with resilient retry reconnects within seconds to the newly promoted primary, especially when it uses the failover group listener endpoint that follows the current primary automatically rather than a fixed server name. The setup walkthrough for failover groups referenced earlier stresses that the listener endpoint plus application retry are what make a regional failover smooth, and a wave of brief 40613 during such an event is the visible proof that the cutover is in progress rather than a sign that anything failed. The lesson across all the multi-replica cases is the same: the error localizes to whichever replica is reconfiguring, and resilient retry carries the application through regardless of which one it was.

## Why a Tight Transient List Beats a Catch-All Handler

The temptation when first taming 40613 is to wrap every database call in a handler that catches all exceptions and retries, on the theory that retrying more broadly can only help. It cannot, and the broad handler is one of the most damaging anti-patterns in data-access code, because it converts fast, loud, correctable faults into slow, silent loops.

A handler that retries everything will spin on a login failure, repeating the same rejected credential until it exhausts its cap, then surface a generic timeout that hides the real 18456 underneath. It will loop on a syntax error in a query, masking a bug that should have failed instantly during testing. It will retry a permission denial, hiding a missing role assignment behind what looks like a flaky connection. In every case the broad handler delays the failure, strips away the specific error that would have pointed at the fix, and burns time that a fast failure would have saved. The cost is paid twice: once in the wasted retries and again in the diagnostic information destroyed by collapsing a precise error into a vague timeout.

The tight list avoids all of this by retrying only the error numbers that genuinely represent a momentary, self-correcting condition, with 40613 and its transient siblings on the list and everything else passing straight through to fail fast. This is why the retry-the-transient rule is phrased around a specific list rather than a blanket catch. The discipline of naming the retryable codes forces you to decide, for each failure class, whether waiting could plausibly help, and the answer for an authentication error, a syntax error, or a permission problem is always no. A precise list turns retry into a scalpel that removes exactly the transient blips while leaving real faults visible and immediate, which is the entire point of the pattern. When you audit a codebase for 40613 resilience, the broad catch-all handlers are the first thing to replace, because they are simultaneously hiding transient events that should be retried quietly and real faults that should be surfaced loudly.

## Extracting the Error Number Reliably Across Drivers

Every retry policy in this guide hinges on one operation: correctly reading the numeric error so you can test whether it is 40613 or another transient code. That sounds trivial, yet it is where hand-rolled handlers most often go wrong, because each driver exposes the number in a different place, and a handler that reads the wrong field silently fails to recognize 40613 and either retries nothing or retries everything.

In .NET with Microsoft.Data.SqlClient, the failure arrives as a SqlException, and the reliable field is the Number property on the exception, with each individual error available through the Errors collection when a single failure carries several. Reading exception.Number and testing membership in your transient set is the correct check. Reading the message text instead and searching for the digits is fragile, because the wording can change and localization can alter it, so always prefer the structured number over string matching.

```csharp
// Read the structured error number rather than parsing the message text.
// Each SqlError in the collection carries its own Number; any match against
// the transient set marks the failure retryable.
catch (SqlException ex)
{
    bool transient = ex.Errors.Cast<SqlError>().Any(e => TransientNumbers.Contains(e.Number));
    if (!transient) throw;
    // ... back off and retry
}
```

In Python with pyodbc, the structured number is less direct, because the driver surfaces the database error through SQLSTATE and a message rather than a clean integer property, so a robust handler parses the SQL error number out of the error arguments or matches on the recognizable message fragment as a fallback. The safest approach is to extract the numeric code from the driver's error tuple where the backend provides it and to keep a message-fragment check only as a secondary guard, because relying on message text alone is the same fragility warned about for .NET.

```python
# Pull the SQL error number from the driver error where available, and fall
# back to a recognizable fragment only as a secondary guard.
def is_transient(exc, transient_numbers):
    text = str(exc)
    for token in transient_numbers:
        if str(token) in text:
            return True
    return "not currently available" in text.lower()
```

In Java with the Microsoft JDBC driver, the SQLException exposes getErrorCode for the database error number and getSQLState for the state, and testing getErrorCode against your transient set is the correct check, mirroring the .NET pattern. Chained exceptions are walked with getNextException so a failure carrying several errors is fully inspected.

```java
// JDBC exposes the database error number through getErrorCode. Walk the
// chain so a multi-error failure is fully inspected against the transient set.
catch (SQLException ex) {
    boolean transient = false;
    for (SQLException e = ex; e != null; e = e.getNextException()) {
        if (TRANSIENT.contains(e.getErrorCode())) { transient = true; break; }
    }
    if (!transient) throw ex;
}
```

The cross-cutting rule is to read the structured number wherever the driver provides one and to treat message-text matching as a last resort, because the number is stable while the text is not. A handler that gets this right recognizes 40613 the same way regardless of how the underlying connection dropped, and a handler that gets it wrong either misses the transient entirely or, worse, matches too broadly and retries faults it should surface. When you port the retry pattern to a new language or driver, the first thing to verify is exactly where that driver puts the database error number, because the entire transient-versus-fault decision rests on reading it correctly. This small detail is the difference between a retry policy that quietly absorbs every reconfiguration and one that looks correct in review but never actually fires on the error it was written to handle.

## The Cost Trade-Off Behind the Serverless Choices

The fixes for the serverless cause of 40613 are not purely technical; each carries a billing consequence, and choosing among them well means weighing responsiveness against spend rather than reaching for whichever option silences the error fastest.

Leaving auto-pause enabled with a short delay maximizes the compute saving, because the database stops billing for compute whenever it sits idle past the threshold. The price of that saving is the resume latency on the next request and the brief 40613 window it can produce. For a workload that is genuinely idle for long stretches and tolerant of a slower first hit, this is the economical and correct choice, and a patient retry policy absorbs the resume so users see a one-time delay rather than an error.

Disabling auto-pause removes the resume entirely by keeping the database always active, which guarantees a fast first request and eliminates the resume-related transient error, but it forfeits the idle saving because compute bills continuously whether or not anyone is connected. For a workload where first-hit responsiveness directly affects users or revenue, paying for always-on compute to remove the cold start is often worth it, and the calculation is simply whether the cost of continuous compute is less than the cost of the latency and complexity the resume introduces.

The keep-warm ping is the middle path that often wins for workloads with a predictable rhythm. A lightweight scheduled query a few minutes before the business day resumes the database on your timetable, so it is warm when real users arrive, while still allowing it to pause through the genuinely idle overnight hours. The ping itself costs almost nothing, and the result is most of the idle saving with none of the customer-facing cold start. The judgment is whether your traffic is predictable enough to schedule against; if it is, keep-warm captures both the saving and the responsiveness, and if it is not, the patient retry policy is the cleaner answer because there is no schedule to warm against.

Framing the serverless decision as a cost trade-off rather than a bug fix changes how you make it. The error is not something to eliminate at any price; it is one consequence of a billing model that trades idle compute for resume latency. Decide where your workload sits on the responsiveness-versus-spend axis, pick the lever that matches, and the appearance or absence of a resume-related 40613 becomes a deliberate outcome of a cost decision rather than an accident discovered in production.

## When 40613 Appears During Deployments and Schema Migrations

Deployment and migration pipelines meet 40613 in ways that ordinary application traffic does not, because they often run management operations and schema changes that touch the database during exactly the windows when it may be reconfiguring. Recognizing these cases keeps your delivery automation from failing on transient events it should have ridden out.

A pipeline that scales the database up before a heavy migration and back down afterward triggers the scaling cutover described earlier, and any connection the pipeline opens during that cutover can receive 40613. The robust pattern is for the pipeline to treat the scaling operation as asynchronous, poll the database until it reports ready, and only then open connections for the migration, rather than assuming the database is available the instant the scale command returns. The same applies to a restore-then-migrate sequence, where the database is still finalizing provisioning after the restore command completes and is not yet accepting connections.

Schema migration tools that run a long series of statements are particularly exposed, because a reconfiguration mid-migration severs the connection and rolls back the open transaction, leaving the migration partially applied from the tool's point of view even though the database is consistent. The defense is to make migrations resumable and idempotent where possible, so a migration interrupted by a transient event can be rerun safely from where it left off, and to wrap each migration step in a transaction so an interrupted step undoes cleanly and reruns from a known state. A migration tool with resilient connection handling and idempotent steps treats a 40613 mid-run as a pause to retry through rather than a failure that leaves the schema in limbo.

Blue-green and rolling deployment strategies add their own wrinkle, because they often run health checks against the database as part of the cutover decision, and a health check that hits a 40613 during a reconfiguration can wrongly mark a healthy database as failed and abort or roll back a perfectly good deployment. The fix is to apply the same resilient retry to deployment health checks that you apply to application traffic, so a transient blip during the check does not masquerade as a failed deployment. Delivery automation that lacks retry on its database touchpoints is a frequent and avoidable source of failed deployments that had nothing wrong with them beyond meeting a routine platform event at an unlucky moment. The broader discipline of building idempotent, retry-aware delivery is what keeps a transient database event from ever cascading into a rolled-back release.

## Anti-Patterns That Keep Teams Stuck on Error 40613

The teams that struggle longest with 40613 tend to repeat the same handful of mistakes, and naming them directly is often faster than re-explaining the fix, because recognizing the anti-pattern points straight at the correction.

The first is surfacing the error to users instead of retrying it. An application with no resilient handling passes every reconfiguration straight through as a user-facing failure, so a routine platform event that should have been invisible becomes a support ticket. The correction is the retry policy this guide centers on, applied to every connection path rather than the one someone remembered.

The second is retrying without backoff. Immediate, tight-loop retries against a database that is mid-reconfiguration hammer the recovering instance with synchronized attempts and can prolong the very event you are trying to ride out, especially across a fleet of clients reconnecting in lockstep. The correction is exponential backoff with jitter, which spreads the reattempts and gives the platform room to settle.

The third is ignoring the serverless resume. A team that runs a retry policy tuned only for sub-second blips abandons a resume before warm-up finishes and then concludes that retry does not work for their database, when the real problem is a retry window too short for a serverless cold start. The correction is a more patient policy, a keep-warm ping, or a longer pause delay, chosen against the workload.

The fourth is the catch-all handler that retries every exception, which loops uselessly on real faults like a login failure and hides the specific error that would have pointed at the fix. The correction is a tight transient list that retries 40613 and its siblings while letting genuine faults fail fast.

The fifth is treating every occurrence as a suspected outage. A team that opens an investigation for each 40613 burns hours on events that a five second retry would have resolved, because the rare true outage is buried among many routine reconfigurations. The correction is to retry first and investigate only the occurrences that survive the retry, since those are the only ones that carry real signal.

The thread through all five is the same misconception: that 40613 is a failure to eliminate rather than a transient state to absorb. Once a team internalizes that the error is the visible edge of a managed service keeping itself available, each anti-pattern resolves into its correction almost automatically, and the error moves from a recurring source of confusion to a well-understood and quietly handled part of running on the platform.

## The Strategic Verdict on Error 40613

The single most valuable shift in handling Azure SQL error 40613 is to stop treating it as a failure and start treating it as a signal. It is the visible edge of a managed service keeping itself available, and the overwhelming majority of occurrences are routine reconfigurations, scaling cutovers, and serverless resumes that resilient retry with backoff was designed to absorb. Build that retry once, push it as low in your stack as it will cleanly go, make it idempotent-safe, tune it patient enough for serverless, and apply it to every connection path, and the common causes simply disappear from your users' experience.

What remains after retry is precisely the set of problems worth your attention: a serverless database that needs warming, a load pattern that needs relief, or the rare genuine incident that needs escalation. Because resilient code makes the transient cases invisible, the 40613 that does survive your retry is a clean, high-value signal rather than noise. That is the whole strategy in one sentence: retry the transient, instrument the rest, and let the error tell you which is which. A team that adopts this posture finds that 40613, once a recurring source of pages and confusion, becomes one of the quietest and best-understood corners of their Azure SQL operations.

## Frequently Asked Questions

### Q: What does Azure SQL error 40613 mean?

Error 40613 means the database is not currently available and the platform is asking you to retry the connection shortly. The full message names the database and logical server that failed and provides a session tracing ID for support. The code sits on the transient-fault list, which signals that the database is momentarily unreachable rather than permanently broken. It typically appears during a high-availability reconfiguration, a scaling operation, or a serverless resume, when the primary replica is being relocated or rebuilt and no node is ready to accept connections for a brief window. In the overwhelming majority of cases the right response is a measured retry with backoff, because the database becomes available again within seconds. Treating 40613 as a permanent failure and surfacing it to users is the most common mistake, since resilient retry would have absorbed the event entirely.

### Q: Is error 40613 a transient error I should retry?

Yes. Error 40613 is on the documented transient-fault list, so the correct default response is resilient retry with exponential backoff and a touch of jitter. A retry that succeeds a few seconds later proves the cause was transient, which is the common case during reconfigurations, scaling cutovers, and serverless resumes. The retry doubles as a diagnostic: if a later attempt connects, the database was simply mid-transition, and if every attempt over a minute or two fails identically, the cause is one of the persistent situations such as a paused serverless database that needs warming, sustained throttling that needs load relief, or a genuine outage that needs escalation. Keep your retryable list tight so the policy retries true transients like 40613 and 40197 while letting real faults such as a login failure fail fast rather than looping uselessly.

### Q: Does a failover or scaling event cause 40613?

Yes, both do, and they are among the most common causes. Azure SQL keeps your database highly available by maintaining multiple replicas and relocating the primary when a host needs maintenance, suffers a fault, or must be rebalanced. During that relocation there is a brief instant when no node is serving connections, and any attempt in that gap receives 40613. A scaling operation, whether a service-tier change, a switch between purchasing models, or a compute resize, triggers the same kind of cutover and produces the same transient error while the new capacity comes online. The activity log will show a scaling or update operation in the minutes before the errors if scaling was the trigger, while a spontaneous failover shows up in Resource Health as a platform-initiated action. In both cases resilient retry absorbs the cutover, and scheduling deliberate scaling changes for low-traffic windows keeps the brief disruption out of sight.

### Q: Can a paused serverless database cause 40613?

Yes, and this is the cause that confuses the most engineers. A serverless database automatically pauses after a configured period of inactivity to save compute cost, and it stays paused until the next connection wakes it. That first request after idle triggers a resume, and while the database warms up, connection attempts can fail with 40613. To an application idle overnight, the first morning request looks like it hit a dead database when it actually hit a sleeping one mid-wakeup. Confirm it by checking that the database is on the serverless tier and that its state was Paused when the errors began. The fixes are a more patient retry policy that outlasts the resume, a longer auto-pause delay or disabling pause entirely if first-hit latency matters, or a lightweight keep-warm query scheduled just before your business day so the database is awake before real users arrive.

### Q: How long is the database unavailable when I get a 40613?

It depends entirely on the cause. A routine reconfiguration or failover usually clears within seconds, often before a user notices anything beyond a momentary pause. A scaling cutover can run from a few seconds to a couple of minutes while the new compute provisions and the database repoints. A serverless resume takes longer than a failover and varies with the tier and configuration, which is why a retry policy tuned only for sub-second blips can abandon a resume prematurely. A genuine platform outage lasts until the incident is resolved, which is outside your control. Because the duration varies so widely, the safe design is to size your connection timeout and total retry window against the longest transient case your workload realistically meets, since generous limits cost nothing on the fast common cases and rescue you on the slow ones.

### Q: How do I add retry logic for error 40613?

Catch the connection or command failure, check whether the error number is on your retryable list, wait a short and growing interval with jitter added, and try again up to a sensible cap. In .NET, attach a configurable retry provider to the SqlConnection or enable the EF Core execution strategy with EnableRetryOnFailure, both of which already know the Azure SQL transient codes. In Python, wrap the connect-and-run in a loop that backs off exponentially and retries only the transient numbers. In Java, set the connection retry properties on the JDBC connection string or wrap the work in a resilience library. Across all of them the principles are identical: a tight transient list that includes 40613 and 40197, exponential backoff, jitter so a fleet does not reconnect in lockstep, a reasonable retry cap, and idempotent operations so replaying a write is harmless. Push the policy as low in the stack as it cleanly goes so every connection path is covered.

### Q: Why does retrying never clear a 40613 sometimes?

Because not every 40613 is transient in practice. The code appears during transient reconfigurations that clear in seconds, but it also surfaces when a serverless database is paused and your retry policy abandons the resume before warm-up finishes, when the database is saturated under sustained load and cannot accept connections until you relieve the pressure, or during a genuine outage that lasts until the platform recovers. In each of those cases the retry behavior is the diagnostic: a retry that never clears tells you the cause is persistent rather than a routine blip. Check the serverless state, the utilization and accompanying 40501 errors, and the Resource Health and Service Health surfaces in that order. A paused database needs a more patient retry or warming, a saturated one needs load relief, and a true outage needs escalation rather than more retries.

### Q: Should I disable auto-pause to stop getting 40613?

Disabling auto-pause stops the serverless resume cause of 40613 specifically, but it does not stop the others. Setting the auto-pause delay to negative one keeps the database always on, so it never goes cold and never produces a resume-related transient error, which is the right call when first-hit latency matters more than the compute savings of idling. It does nothing, however, for the 40613 that comes from reconfigurations, scaling cutovers, throttling, or outages, which still require resilient retry. The decision is a cost trade-off: pausing saves compute during genuinely idle periods, and disabling it spends that saving to buy first-request responsiveness. Many teams compromise with a longer pause delay or a keep-warm ping scheduled before business hours, getting most of the idle savings while ensuring the database is awake when real users arrive. Whichever you choose, retry remains necessary for the non-serverless causes.

### Q: How is 40613 different from the 18456 login error?

They describe opposite situations and demand opposite responses. Error 40613 means the database was momentarily unreachable and will accept your connection shortly, so retrying succeeds once the platform settles. Error 18456 means the connection reached the server but the login was rejected for a fixed reason such as a wrong password, a missing login, a firewall block, or a contained user connecting to the wrong database context, so every retry presents the same rejected credential and fails identically. The tell is in the message: 40613 carries a session tracing ID and an instruction to retry, while 18456 carries a state number that pinpoints the authentication cause. If your retry loop is spinning on 18456, you have miscategorized an authentication problem as a transient one. Read the 18456 state and fix the credential, firewall rule, or connection context rather than retrying, because no number of attempts will make a wrong password right.

### Q: Does 40613 mean my data was lost or corrupted?

No. Error 40613 reflects a momentary availability gap during a platform operation, not any loss or corruption of your data. The database keeps multiple synchronized replicas, and when the primary relocates, the data moves with it intact. Any transaction that was open on the severed connection is rolled back cleanly, leaving the database in a consistent state with that unit of work undone rather than half-applied. This automatic rollback is why an interrupted write does not corrupt anything: the platform guarantees consistency across the reconfiguration. The practical implication for your code is to make retried writes idempotent, so replaying an operation after an ambiguous failure cannot duplicate a row that may have committed just before the drop. Wrapping multi-step work in a transaction gives you the same wholesale rollback behavior the platform already provides during a failover, so an interrupted attempt undoes entirely and the retry starts clean.

### Q: What error numbers should I treat as transient alongside 40613?

Treat the connection and reconfiguration codes as transient: 40613 for the database not currently available, 40197 for a service processing error during reconfiguration, 40501 for service-busy throttling that carries a suggested wait, and 49918, 49919, and 49920 for the subscription or instance being too busy to process a request. Add the connection-level codes a driver raises when a session drops, such as 4060, 233, and 64, and the resource governance codes 10928 and 10929 that appear under heavy concurrency. Retry all of these with exponential backoff. Crucially, keep the list tight: do not retry codes that represent real faults such as a login failure, a syntax error, or a permission denial, because those will fail identically on every attempt and a blind retry merely hides the real problem while wasting time. A precise transient list is what lets your policy absorb blips while surfacing genuine errors fast.

### Q: Will resilient retry slow down my application?

In the common case retry adds no meaningful latency, because the first attempt usually succeeds and the policy never engages. Retry only adds delay when a transient failure actually occurs, and in that situation the small wait it introduces is far better than the alternative of surfacing an error to the user. The design detail that keeps retry cheap is the backoff curve: a short first delay catches the quick reconfigurations without much wait, while the growing intervals reserve the longer pauses for the rarer slow cases like a serverless resume. Jitter prevents a fleet of clients from retrying in lockstep and amplifying load on a recovering database. The only way retry meaningfully slows an application is if it is misconfigured to retry non-transient errors, looping uselessly on a fault that will never clear. A tight transient list and a sensible cap keep retry invisible during normal operation and helpful during the brief windows when it matters.

### Q: Can connection pooling cause lingering 40613-style errors after a failover?

It can if the pool hands out stale connections. A reconfiguration invalidates the existing pooled connections, and an application that borrows one without validating it may throw a connection error even after the database is healthy again, because the connection object refers to a session that no longer exists. The fix is pooling discipline: configure the pool to test connections on borrow or to recycle them promptly so that a request arriving after a failover receives a fresh, valid connection rather than a dead one held over from before the event. This is why a small number of post-failover errors sometimes persist a moment longer than the actual unavailability window; the database recovered, but the pool was still serving connections established before the cutover. Pairing resilient retry with sound pool validation closes that gap, so the application reconnects cleanly the instant the database is back.

### Q: How do I monitor 40613 without alerting on every routine failover?

Alert on the rate relative to your baseline and on the clearing behavior, not on raw presence. A handful of 40613 that each clear on the first retry is healthy background noise from the platform staying available, so an alert that fires on a single occurrence will cry wolf during every routine maintenance. Build the alert on the delta from normal, so a rate climbing well above your established baseline or a cluster that stops clearing on retry triggers attention while ordinary reconfigurations stay quiet. Feed application logs into a workspace, count occurrences in time bins, and compare against a rolling baseline. Correlate the application view with the database's utilization and Resource Health metrics, because the same count means throttling when utilization is pinned and a benign reconfiguration when utilization is normal and a platform action is recorded. Always log the session tracing ID so a real incident can be traced without reproduction.

### Q: How can I reproduce 40613 to test my retry logic?

Trigger the platform operations that produce it in a test environment. A manual failover relocates the primary replica and reproduces the brief unavailability of a spontaneous failover, letting you watch whether your retry absorbs the cutover transparently. For the serverless cause, set a short auto-pause delay, let the database go idle until it pauses, then issue a first request and confirm your more patient retry policy rides out the resume rather than abandoning it. For the throttling cause, run a load test that drives utilization to the ceiling and observe whether the application degrades gracefully under the resulting resource-limit and availability errors. Every cause of 40613 except a true outage can be reproduced deliberately, so there is no reason to meet any of them for the first time in production. A resilience plan that exercises a forced failover, a serverless cold start, and a saturation event validates that the handling you reasoned about actually works when the connection really drops.

### Q: Does the server connection policy affect how 40613 recovers?

The connection policy does not prevent 40613, but it shapes the reconnection sequence you observe afterward. In proxy mode every query passes through the logical server gateway, so reconnection is simple because the gateway always knows where the current primary lives. In redirect mode the gateway gives the client a direct path to the node hosting the database after the handshake, which lowers steady-state latency, and after a reconfiguration relocates the primary the client must re-establish that direct path to the new node. Both modes reconnect correctly with proper retry, and neither stops the transient error, but knowing which policy your connections use explains the exact post-failover behavior in your logs and stops you from misreading a normal redirect re-handshake as a fresh fault. The takeaway is that connection policy is a latency and routing choice, while resilient retry is what actually carries you through the brief unavailability that 40613 reports.

### Q: When should I open a support ticket for 40613 instead of just retrying?

Open a ticket when the error stops behaving like a transient one and the platform's own signals point at a real problem. The threshold is a 40613 that persists rather than clearing on retry, combined with Resource Health reporting the database as Unavailable for an extended period and Azure Service Health showing an active incident affecting Azure SQL in your region. At that point client-side retry cannot help until the platform recovers, and the correct action is to capture the session tracing ID from the error message, note the timeline of the occurrences, and engage support and the status channels. Leave resilient retry running while you do, because it will reconnect the application automatically the moment the platform recovers and spare you a manual restart. Do not open a ticket for the routine case where retries clear within seconds, since that is the service keeping itself available as designed and a ticket would only confirm normal behavior.
