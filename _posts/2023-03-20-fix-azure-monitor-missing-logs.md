---
layout: post
title: "Fix Azure Monitor Missing Logs and Metrics"
page_title: "Azure Monitor Missing Logs: Why Telemetry Disappears and How to Restore the Flow (Diagnostic Settings, Agent, Workspace)"
date: 2023-03-20
categories: ["Technology"]
tags: ["Azure", "Azure Monitor", "Log Analytics", "Diagnostic Settings", "Troubleshooting", "Observability"]
excerpt: "Azure Monitor missing logs usually means a broken pipe, not a broken query. Find the real cause and restore your telemetry flow with quick confirming checks."
image: "/assets/images/blog/blog-109.webp"
reading_time: 59
author: "thomas-reid"
last_updated: 2026-08-09
lang: en
---
You open a dashboard expecting to see the last hour of telemetry, and the chart is empty. You run the query you have run a hundred times, and it returns nothing. The resource is running, traffic is flowing, the application is serving requests, and yet Azure Monitor missing logs is the problem staring back at you. The instinct, almost universal, is to blame the query. Engineers spend the next twenty minutes rewriting Kusto, widening the time range, changing the table name, and second-guessing a filter that was correct all along. The query was never the issue. In the overwhelming majority of these incidents, the telemetry never reached the place you are querying, because nothing was routing it there.

This is the single most important reframe for anyone debugging an empty workspace: a resource in Azure emits almost nothing to a queryable store until you explicitly connect a pipe from that resource to a destination. The platform does not assume you want every signal collected and retained, because collection and retention cost money and most signals are noise most of the time. So the default state of a freshly created resource is that its resource logs go nowhere. They are generated internally, they may surface briefly in a live stream, but they are not landing in any table you can query later unless a diagnostic setting carries them there. When the chart is empty, the question is not "what is wrong with my query," it is "is there a pipe, is it pointed at the workspace I am looking at, and is anything actually putting data into the pipe."

![Fix Azure Monitor Missing Logs and Metrics](/assets/images/blog/blog-109.webp)

This article gives you the full diagnostic path. You will learn how to read the symptom correctly, how to separate the distinct root causes that all present as an empty view, how to confirm which one is yours with a specific check rather than a guess, and how to restore the flow with a tested command for each cause. By the end you will be able to walk into a missing-telemetry incident and, within a few minutes, tell whether the resource has a routing pipe, whether an agent is alive, whether the data is landing in a different store than the one you are querying, and whether you are simply asking for a kind of signal the resource does not produce. The goal is to make this a fifteen-minute incident instead of a two-hour one, and to make it a problem you stop having because you build the pipe deliberately the next time.

If you want the conceptual ground underneath this, the broader mental model of how the platform collects, stores, and exposes telemetry is laid out in the [Azure Monitor and Log Analytics guide](/2022/04/11/azure-monitor-log-analytics-guide/), and the step-by-step routing configuration this article keeps pointing back to is covered end to end in [configuring diagnostic settings across Azure](/2023/07/17/configure-diagnostic-settings/). This piece assumes you already have a resource and a workspace and the data simply is not arriving, and it focuses on finding and fixing the break.

## What does an empty Azure Monitor view actually tell you?

An empty result is not one symptom. It is the shared appearance of at least six unrelated failures, and treating them as one is why the incident drags. Before you change anything, you need to gather a small set of signals that will separate them, because the fix for a missing pipe is nothing like the fix for a dead agent, and the fix for a wrong-workspace problem is nothing like the fix for an RBAC gap. Reading the symptom means collecting evidence that tells you which world you are in.

### Why does Azure Monitor show no logs even though the resource is running?

Because a running resource and a collected log are different things. The resource generates events internally, but those events are only persisted to a queryable store if a diagnostic setting routes them there. A running resource with no diagnostic setting produces zero rows in Log Analytics, and the query that targets that store correctly returns nothing because there is nothing to return.

That distinction is the whole game, so hold it firmly. The resource being healthy tells you about the resource. It tells you nothing about whether telemetry from that resource is being captured. The two are connected by a piece of configuration that you, or someone on your team, either created or did not. The first job in any of these incidents is to stop conflating the health of the workload with the presence of its telemetry, because they fail independently and they fail for different reasons.

The diagnostic signals you want to gather before you touch a query are small and quick to collect. First, does the resource have any diagnostic setting at all, and if so, what destination does it name? Second, if the resource depends on an agent rather than a platform diagnostic setting, is that agent alive and reporting a heartbeat? Third, which store does your query actually target, and is it the same store the pipe points at? Fourth, what kind of signal are you asking for, a metric or a log, because they travel down different roads. Fifth, is the specific category you expect even turned on inside the setting, since enabling a setting does not enable every category. Sixth, do you have the access rights to see the data, because a permission gap can render a full table invisible to you while it is full for someone else.

Each of those questions maps to one root cause, and each has a confirming check that takes under a minute. The rest of this article walks them in order, gives you the exact command or query to confirm each one, and then the fix. Practicing this sequence until it is muscle memory is exactly the kind of repeatable drill that [VaultBook](/2022/04/11/azure-monitor-log-analytics-guide/) hands-on labs are built around, where you stand up a resource, deliberately leave the pipe disconnected, and watch the empty view appear so you recognize it instantly in production.

### How do I gather the diagnostic signal quickly?

Start outside the query editor. Open the resource itself and look at its diagnostic settings blade, then check the workspace your query names, then confirm the signal type. Three checks, in that order, will tell you which of the root causes you are facing before you have rewritten a single line of Kusto. The query is the last thing to suspect, not the first.

A fast way to collect this without clicking through blades is the command line. The following sequence asks the three foundational questions in order, and the answers narrow the problem immediately.

```bash
# 1. Does this resource have any diagnostic setting, and where does it point?
az monitor diagnostic-settings list \
  --resource "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/<provider>/<type>/<name>" \
  --output table

# 2. What workspace does my query target, and does it exist?
az monitor log-analytics workspace show \
  --resource-group <rg> \
  --workspace-name <workspace-name> \
  --query "{name:name, id:customerId, retention:retentionInDays}" \
  --output table

# 3. Is the agent (if this resource uses one) reporting a heartbeat?
#    Run inside the workspace query view:
#    Heartbeat | where TimeGenerated > ago(15m) | distinct Computer
```

If the first command returns an empty list, you have your answer already and you can skip most of the rest of the diagnosis: there is no pipe, so there are no logs, and the fix is to create the setting. If the first command returns a setting that points at a different workspace than the second command describes, you have a wrong-destination problem. If both line up but the third query is empty for an agent-based resource, the agent is the suspect. Gathering these three answers first is the difference between a targeted fix and an afternoon of guessing.

## The diagnostic-settings-first rule

Here is the namable claim this article advances, and it is worth committing to memory because it resolves most of these incidents before you have finished reading the error: no diagnostic setting means no logs, so missing telemetry is a missing pipe far more often than it is a broken query. Call it the diagnostic-settings-first rule. When a view is empty, your first action is not to inspect the query and not to inspect the agent; it is to confirm that a pipe exists and that it points at the store you are reading. Only after you have established that the pipe is present and correctly aimed do the other causes become worth investigating.

The rule works because it matches the platform's actual behavior. Azure separates the generation of a signal from the collection of that signal on purpose. A resource always knows what is happening inside it, but it does not push that knowledge anywhere durable by default. The diagnostic setting is the explicit instruction that says "take these categories of events from this resource and deliver them to this destination." Without that instruction, the events are ephemeral. The platform metrics, a separate stream, are an exception that confuses people, and we will untangle that confusion shortly, but for resource logs the rule holds without exception: the pipe is the precondition for everything else.

Applying the rule changes how you triage. Instead of starting in the query editor, you start at the resource, you ask whether it has a setting, you note the destination, and you compare that destination to where you are looking. This single discipline collapses the most common version of the incident, the one where a resource was deployed without observability wired in and nobody noticed until someone needed the data. The data was never lost. It was never collected. The fix is forward-looking, not recovery: you connect the pipe now, and telemetry begins flowing from this moment. You cannot retrieve what was never captured, which is exactly why building the pipe at deployment time, as code, is the durable answer the prevention section returns to.

The rule also tells you when to stop suspecting the pipe and move on. If the setting exists, it points at the right workspace, and it has the category you want enabled, then the pipe is not your problem and you should look at the agent, the signal type, the time range, or your access. The rule is a gate, not a dogma. It puts the highest-probability cause first and gives you a clean way to rule it in or out, so the rest of the diagnosis proceeds with confidence rather than flailing.

## The InsightCrunch missing-telemetry table

This is the findable artifact for the article, the reference you bookmark and return to in the middle of an incident. Each row is a distinct cause that produces an empty view, paired with the single check that confirms whether it is yours and the action that restores the flow. Read it top to bottom the way the diagnostic-settings-first rule prescribes: the pipe causes are at the top because they are the most common, and the access cause is last because it is the rarest but the easiest to miss.

| Cause of missing telemetry | How to confirm it is yours | The fix that restores flow |
| --- | --- | --- |
| No diagnostic setting routes the logs | `az monitor diagnostic-settings list` on the resource returns an empty list | Create a diagnostic setting pointing the wanted categories at the target workspace |
| The Azure Monitor Agent is not reporting | A Heartbeat query for the last 15 minutes shows no row for the machine | Repair or reinstall the agent and confirm the data collection rule is associated |
| Logs land in a different workspace | The setting's `workspaceId` does not match the workspace your query targets | Repoint the setting at the correct workspace, or query the workspace the setting names |
| You expect logs where only metrics exist | The signal you want is a metric stream, not a resource log category | Read the metric through Metrics explorer or the metrics API rather than a log table |
| The log category is enabled in the setting | The setting exists but the specific category toggle is off | Enable the missing category in the diagnostic setting and wait for the next events |
| An RBAC gap hides the data from you | Another principal sees rows in the same query that returns nothing for you | Grant the reader the Log Analytics Reader role at the right scope |

Two of those rows deserve a caution that the table cannot carry. The metrics-versus-logs row is the one that traps experienced engineers, because they assume the workspace should hold everything, and platform metrics simply do not live there by default; that is a category confusion, not a broken pipe, and the fix is to look in the right place rather than to repair anything. The category-enabled row is the one that traps people who did the right thing halfway: they created a setting, they felt observability was handled, and they never noticed that turning on the setting did not turn on the category they actually needed. Both are quick to confirm and quick to fix once you know to look, which is the entire reason the table separates them out instead of folding them into a generic "no data" entry.

Keep the table next to you while you read the cause-by-cause sections that follow. Each section expands one row into the why, the confirming command, and the tested fix, and the order matches the table so you can jump straight to the row your evidence points at.

## Root cause one: no diagnostic setting routes the logs

This is the cause behind more empty workspaces than all the others combined, and it is the cause the diagnostic-settings-first rule is built to catch immediately. The resource is generating events. It has been generating them the entire time. But no instruction exists to carry those events from the resource to a store you can query, so they evaporate. There is nothing wrong with the workspace, nothing wrong with the query, and nothing wrong with the resource. There is simply no pipe.

### Does a missing diagnostic setting cause no logs?

Yes, completely. A resource log category is not collected anywhere queryable until a diagnostic setting routes it to a destination. With no setting present, the resource emits its events internally and they are discarded; no table fills, and any query against that table returns zero rows. This is the default state of every newly created resource.

The reason this trips so many teams is that the platform's behavior is the opposite of what intuition expects. Most people assume that creating a resource in a cloud that is famous for its monitoring means monitoring is on. It is not. The platform metrics for many resources are collected automatically, which adds to the confusion, but the rich resource logs, the ones that tell you what requests came in, what queries ran, what was denied and why, are off until you ask for them. A resource can run in production for months with full traffic and a completely empty log store because nobody ever created the setting that would have captured the detail.

Confirming this cause takes one command. List the diagnostic settings on the resource and read what comes back.

```bash
az monitor diagnostic-settings list \
  --resource "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Web/sites/<app-name>" \
  --output json
```

If the response is an empty array, the diagnosis is settled. There is no pipe. You do not need to look further. The portal shows the same thing under the resource's Diagnostic settings blade, where the list of settings will be empty and a banner will often invite you to add one. Either view confirms the same fact.

The fix is to create the setting, choosing the categories you actually need and pointing them at the workspace your dashboards and queries read from. Resist the temptation to enable every category for every resource, because each category you collect carries an ingestion and retention cost, and a setting that collects everything from a chatty resource can become an expensive surprise. Pick the categories that answer the questions you ask of this resource.

```bash
az monitor diagnostic-settings create \
  --name "send-to-central-workspace" \
  --resource "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Web/sites/<app-name>" \
  --workspace "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.OperationalInsights/workspaces/<workspace-name>" \
  --logs '[{"category":"AppServiceHTTPLogs","enabled":true},{"category":"AppServiceConsoleLogs","enabled":true}]' \
  --metrics '[{"category":"AllMetrics","enabled":true}]'
```

After the setting exists, give the resource a little time to generate fresh events and the platform a little time to ingest them, then run your query again. One caveat that matters here and matters even more in the next causes: the setting only captures events from the moment it exists forward. It does not backfill. The hour of telemetry you wanted to see when the view was empty is gone, because it was never collected. From here on it will be there, but the past is not recoverable, which is the strongest possible argument for wiring the setting in at deployment rather than discovering its absence during an incident.

The categories available to enable differ by resource type, and guessing wrong wastes a round trip. You can ask the platform exactly which categories a given resource type supports before you write the setting.

```bash
az monitor diagnostic-settings categories list \
  --resource "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Web/sites/<app-name>" \
  --output table
```

That listing returns every log category and every metric category the resource can route, so you can build a setting that captures precisely what you need and nothing you do not. Building these settings, breaking them on purpose, and watching the table go empty and then refill is the kind of deliberate practice that the [VaultBook](/2023/07/17/configure-diagnostic-settings/) lab environment is designed for, because the muscle memory of "empty view means check the pipe first" only forms when you have seen the empty view appear and disappear under your own hands.

## Root cause two: the Azure Monitor Agent is not reporting

Some telemetry does not flow through a resource-level diagnostic setting at all. It flows through an agent installed inside a virtual machine or a server, which collects from the guest operating system and ships the data to a workspace. Guest-level signals such as performance counters, syslog on Linux, Windows event logs, and custom text logs come from the agent, not from a platform setting on the resource. When those signals go missing, the pipe to suspect is the agent, and the most reliable evidence of an agent's health is its heartbeat.

### Why is the Azure Monitor Agent not reporting a heartbeat?

Because the agent is either not installed, not running, not associated with a data collection rule, or unable to reach the ingestion endpoint over the network. Each of those breaks the flow in a way that surfaces as a silent absence of guest data. The heartbeat is the agent's proof of life, so its absence in the workspace tells you the agent itself is the problem rather than the routing.

The heartbeat is your first confirming check, and it is a single query. Run it inside the workspace your agent should be reporting to.

```kql
Heartbeat
| where TimeGenerated > ago(15m)
| summarize LastSeen = arg_max(TimeGenerated, *) by Computer
| project Computer, LastSeen, Category, Version, OSType
```

If the machine you expect appears with a recent timestamp, the agent is alive and reporting, and your missing data is something other than agent health, probably a collection rule that is not gathering the specific signal you want. If the machine does not appear at all, the agent is not reporting, and you have isolated the cause to the agent layer. A machine that used to appear and stopped tells you the agent died or lost connectivity at a specific time, which you can read from the last heartbeat timestamp and correlate with a deployment, a network change, or a restart.

The Azure Monitor Agent collects on the basis of a data collection rule, and a frequent failure is that the agent is installed and healthy but no rule is associated with it, so it collects nothing despite being alive. The heartbeat will still appear in that case, because the heartbeat is built in, but no other table fills. This is the trap where the agent looks fine and the data is still missing. Check the associations on the machine.

```bash
# List data collection rule associations for a virtual machine
az monitor data-collection rule association list \
  --resource "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Compute/virtualMachines/<vm-name>" \
  --output table
```

An empty association list with a healthy heartbeat is the signature of "agent alive, collecting nothing." The fix is to create and associate a data collection rule that names the streams you want, for example the performance counters or the syslog facilities, and points them at the workspace. Once the rule is associated, the agent begins gathering those streams within a few minutes and the corresponding tables, Perf for counters or Syslog for Linux events, start to fill.

If the heartbeat is absent entirely, work down the agent stack. Confirm the extension is installed and provisioned successfully, because a failed extension provisioning leaves the agent absent. Confirm the machine has outbound reachability to the ingestion endpoints, because an agent that cannot reach the data collection endpoint cannot ship anything, and a tightened network security group or a firewall change is a common trigger for a previously healthy agent going dark. Confirm the agent service is running inside the guest. Each of those is a layer, and the heartbeat query plus the extension status tell you which layer broke.

```bash
# Confirm the agent extension is provisioned on the VM
az vm extension list \
  --resource-group <rg> \
  --vm-name <vm-name> \
  --query "[?contains(name,'AzureMonitor')].{name:name, state:provisioningState}" \
  --output table
```

A `provisioningState` of anything other than Succeeded points at a failed install, and reinstalling the extension is the corrective action. When the extension is healthy, the rule is associated, and the network path is open, the heartbeat returns and the guest data follows. Rehearsing this exact teardown, killing an agent, breaking its network path, and restoring it, is precisely the kind of controlled failure drill that [ReportMedic](/2025/03/31/azure-devops-observability/) troubleshooting exercises are structured around, so that the live incident is a repeat of a rehearsal rather than a first encounter.

## Root cause three: logs land in a different workspace than you are querying

This cause is insidious because everything appears configured. A diagnostic setting exists. The agent is healthy. Data is being collected. And the view is still empty, because the telemetry is arriving in one store while you are reading from another. Larger environments accumulate multiple Log Analytics workspaces over time, one per environment, one per team, one created by a default policy, one left behind by a proof of concept, and a resource quietly routes to a workspace nobody is watching while the dashboard queries the workspace everybody assumes is the source of truth.

### How do I tell which workspace a resource sends its logs to?

Read the workspace identifier inside the resource's diagnostic setting and compare it to the identifier of the workspace your query targets. They are GUID-bearing resource paths, so the comparison is exact and unambiguous. If the setting names workspace A and your saved query or dashboard reads workspace B, the data is in A and you are looking at B, and that mismatch is the entire problem.

Pull the destination out of the setting directly so there is no ambiguity.

```bash
az monitor diagnostic-settings list \
  --resource "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<account>" \
  --query "[].{name:name, workspace:workspaceId}" \
  --output table
```

The `workspaceId` that comes back is the full resource path of the destination. Now get the resource path of the workspace your query uses and lay them side by side. In the portal, the query view shows the active workspace at the top of the page; in code, you supply the workspace identifier explicitly. If the two paths differ, you have found it.

There are two fixes, and which one you choose depends on intent. If the resource should be reporting to the central workspace and was misconfigured, repoint the setting at the correct destination by updating it. If the resource is correctly reporting to its own workspace and your dashboard simply pointed at the wrong one, the fix is on the query side: aim your query and your saved views at the workspace that actually holds the data. Neither fix is hard once you know which way the mismatch runs, but you cannot choose until you have compared the two identifiers, which is why the comparison is the confirming step.

```bash
# Repoint a diagnostic setting at the correct workspace by updating it
az monitor diagnostic-settings create \
  --name "send-to-central-workspace" \
  --resource "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<account>" \
  --workspace "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.OperationalInsights/workspaces/<correct-workspace>" \
  --logs '[{"category":"StorageRead","enabled":true},{"category":"StorageWrite","enabled":true}]'
```

A related variant of this cause is querying across many workspaces when your data is split. If telemetry legitimately lives in several stores, a single-workspace query will only ever see one of them, and the rows you want may sit in another. Kusto can reach across workspaces in one statement, which both confirms where the data is and serves as a durable pattern for federated environments.

```kql
union
  workspace("workspace-A").StorageBlobLogs,
  workspace("workspace-B").StorageBlobLogs
| where TimeGenerated > ago(1h)
| summarize Rows = count() by SourceWorkspace = "see-table-name"
```

Running a cross-workspace union and seeing rows appear from one store and not another is the cleanest possible demonstration that the data exists and you were simply reading the wrong place. Once you know which store holds it, you either repoint the pipe or repoint the query, and the view fills.

## Root cause four: you expect logs where only metrics exist

This is the category confusion that catches the most experienced engineers, precisely because they know the platform well enough to assume the workspace holds everything. It does not. Metrics and logs are two distinct signal types that travel down different roads, are stored in different places by default, and are queried with different tools. When you go looking for a number that is actually a metric inside a log table, you find nothing, not because anything is broken but because you are looking on the wrong road.

### Why do I see metrics but no logs for a resource?

Because platform metrics are collected automatically and held in a time-series metrics store, while resource logs require a diagnostic setting to be routed into a workspace. The two are independent. A resource will show you charts in Metrics explorer out of the box because the metric stream is on by default, and at the same time return nothing from a log query because no setting ever carried its logs anywhere. Seeing one and not the other is the expected behavior of a resource with no log routing configured.

This explains a very common and very confusing observation: the resource's overview blade shows healthy graphs of CPU, request count, or latency, which makes it look thoroughly monitored, and yet a Kusto query for the detailed events returns an empty result. The graphs are platform metrics, collected and surfaced automatically. The detailed events are resource logs, and they were never routed. The presence of the graphs is actively misleading here, because it suggests observability is handled when only half of it is.

The confirming check is to ask what you are actually looking for. If the thing you want is a numeric measurement over time, a count, a percentage, a latency, a queue depth, it is almost certainly a metric, and you read it through Metrics explorer or the metrics API, not through a log table. If the thing you want is a record of discrete events, a request with its path and status, a query with its text, an authorization decision with its reason, that is a resource log, and it requires a diagnostic setting routing that category into a workspace before any query will find it.

```bash
# Read a platform metric directly from the metrics store, no workspace needed
az monitor metrics list \
  --resource "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Web/sites/<app-name>" \
  --metric "Requests" \
  --interval PT1M \
  --output table
```

If that returns data while your log query is empty, you have confirmed the split: the metric is flowing and the log is not. The fix depends on what you need. If you only ever needed the metric, you are done, you were simply looking in the wrong tool, and there is nothing to repair. If you genuinely need the detailed log events, then you are back to root cause one, because the absence of those events means there is no diagnostic setting routing them, and you create the setting to begin capturing them forward. You can also route platform metrics into a workspace through the same diagnostic setting if you want to query them with Kusto alongside the logs, by enabling the AllMetrics category, but that is a choice to make your metrics queryable in Kusto, not a requirement for the metrics to exist. The deeper model of how these two signal types differ and when to reach for each is developed in the [Azure Monitor and Log Analytics guide](/2022/04/11/azure-monitor-log-analytics-guide/), which is worth reading once so this distinction stops surprising you.

## Root cause five: the log category is enabled in the setting but the one you need is not

This cause is the half-finished pipe. Someone created a diagnostic setting, which feels like completing the task, but a setting is a container for category toggles, and enabling the setting does not enable every category inside it. The setting can be present and routing one category faithfully while the category you actually need sits switched off, so the table you query stays empty even though observability looks configured at a glance.

### Why does a log category return no rows even though the setting exists?

Because each category inside a diagnostic setting is toggled independently, and a setting only routes the categories that are switched on. If the setting enables, say, the HTTP logs but leaves the audit or the console logs off, then queries against the disabled categories find nothing while the enabled one works fine. The presence of the setting is not the same as the presence of every category.

This is why "we have a diagnostic setting, so logs are handled" is a dangerous half-truth. The setting handles exactly the categories its author turned on, and the author turned on the ones they needed at the time, which may not include the one you need now. The confirming check is to inspect the category toggles inside the setting rather than just confirming the setting exists.

```bash
az monitor diagnostic-settings show \
  --name "send-to-central-workspace" \
  --resource "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Sql/servers/<server>/databases/<db>" \
  --query "logs[].{category:category, enabled:enabled}" \
  --output table
```

The output lists every category the setting knows about and whether each is on. If the category you are querying shows `enabled: false`, you have found the cause. The fix is to enable it, which means recreating or updating the setting with that category switched on, after which events in that category begin routing forward from the change.

```bash
az monitor diagnostic-settings create \
  --name "send-to-central-workspace" \
  --resource "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Sql/servers/<server>/databases/<db>" \
  --workspace "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.OperationalInsights/workspaces/<workspace-name>" \
  --logs '[{"category":"SQLInsights","enabled":true},{"category":"QueryStoreRuntimeStatistics","enabled":true},{"category":"Errors","enabled":true}]'
```

Note again that enabling a category only captures events from the change forward. The events you missed while the category was off were never routed, so they are not recoverable, and the table will begin filling with new events rather than backfilling old ones. This is the same forward-only property every routing change shares, and it is the reason a thorough setting at deployment beats an incremental one assembled during incidents.

## Root cause six: an RBAC gap hides the data from you

This is the rarest of the six and the easiest to overlook, because the data is present and correct, the pipe is healthy, the agent is alive, and the query is right. The view is empty only for you, because your account lacks the rights to read the store or the rows. The telling signature is that a colleague runs the identical query and sees results while you see nothing, which is impossible if the data were genuinely absent and is exactly what a permission gap produces.

### Can a permission gap make logs appear missing?

Yes. Reading data from a Log Analytics workspace requires a role that grants read access at the workspace scope, and without it the query returns an empty result rather than an explicit denial in many surfaces, which is what makes it look like missing data instead of a blocked read. If you lack the reader role on the workspace, the rows are there but invisible to you.

The confirming check is comparison. Have someone you know has access run the same query, or check your own role assignments at the workspace scope. If the data appears for them and not for you, the cause is access, not collection.

```bash
# Check whether you (or a principal) hold a reading role on the workspace
az role assignment list \
  --assignee "<your-principal-id>" \
  --scope "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.OperationalInsights/workspaces/<workspace-name>" \
  --output table
```

If no reading role appears, that is your cause. The fix is to grant the appropriate role at the appropriate scope, most commonly the Log Analytics Reader role at the workspace, which lets the principal run queries and see results without granting any write or management rights.

```bash
az role assignment create \
  --assignee "<principal-id>" \
  --role "Log Analytics Reader" \
  --scope "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.OperationalInsights/workspaces/<workspace-name>"
```

A subtler variant of this cause is resource-context access, where a principal can see telemetry for the specific resources they have access to but not the whole workspace. In that model the rows visible to you are scoped to your resource permissions, so a query that spans resources you cannot see will return a partial or empty result that looks like missing data. The fix there is to grant access at the resource scope the principal needs, or to grant workspace-level read if a full view is appropriate. Either way, the diagnostic move is the same: confirm whether the data is invisible to everyone or only to you, because that single comparison separates a collection failure from an access failure cleanly.

## The complication: debugging the query when the pipe was never connected

Every section so far has been building toward the counter-reading this article exists to correct, the reflex that wastes the most time in real incidents. When the view is empty, the overwhelmingly common reaction is to assume the query is wrong and to start editing it. This is the wrong first move, and understanding why is what turns the diagnostic-settings-first rule from a slogan into a habit.

The query is the wrong first suspect because a query can only return what has been collected. If the pipe was never connected, the most perfectly written Kusto in the world returns nothing, because there is nothing in the table to match. You can widen the time range to a year, drop every filter, change the table name, and remove the where clause entirely, and the result is still empty, because the emptiness is upstream of the query. All that editing produces is a sequence of empty results that feel like progress and deliver none, while the actual cause, the missing setting or the dead agent or the wrong workspace, sits untouched.

There is a clean way to engage this complication rather than fall into it. Before you suspect the query, ask the table whether it holds any rows at all, independent of your filters. A query that strips everything down to a raw count over a generous window tells you instantly whether the problem is the query or the pipe.

```kql
AppServiceHTTPLogs
| where TimeGenerated > ago(7d)
| summarize Rows = count()
```

If that returns a count of zero, the table is empty over a full week and your query was never the problem; the pipe is. Go check the diagnostic setting, the agent, and the workspace, in that order. If that returns a positive count, then the table does hold data and your original query's filters or time range were excluding it, and now query debugging is the right activity. This single check is the fork in the road. It separates the pipe problem from the query problem in one statement, and it stops you from spending an hour optimizing a query against an empty table.

The same logic applies to the time range specifically, which is a frequent self-inflicted version of this complication. If your query filters to the last fifteen minutes and the data has an ingestion latency that pushes recent events past that window, the query can return nothing for genuinely fresh data even when the pipe is perfect and the table is filling normally. That is not a missing-telemetry problem at all, it is a latency-window problem, and it has its own diagnosis and its own normal-versus-abnormal baseline, covered in full in [fixing Log Analytics ingestion delay](/2023/03/27/fix-log-analytics-ingestion-delay/). The way to keep the two straight is the raw count over a wide window: if a seven-day count shows rows but a fifteen-minute query shows none, you are looking at latency or a time-range mistake, not at a broken pipe, and you should read the latency sibling rather than rebuild the setting.

## How do the six causes show up in real incidents?

Engineers do not encounter these causes as tidy categories; they encounter them as a confusing morning where a chart that worked yesterday is blank today, or a brand-new resource that refuses to surface anything. Recognizing the pattern behind the symptom is what shortens the incident, so it helps to walk the recurring shapes these failures take in practice and the check that nails each one.

The first and most frequent shape is the silent new resource. A team ships a service, it goes to production, traffic flows, and weeks later someone needs the request logs for an investigation and finds an empty table. No alarm fired because nothing was ever collected to alarm on. The check is the diagnostic settings list returning an empty array, and the lesson is that observability that is not wired in at deployment tends to be discovered missing at the worst possible moment.

The second shape is the agent that went dark. A virtual machine reported guest performance counters and syslog reliably, then a network change tightened outbound rules, and the agent quietly lost its path to the ingestion endpoint. The heartbeat stopped at a precise timestamp that lines up with the network change. The data before the break is intact; the data after it is simply absent, and the fix is restoring the network path and confirming the heartbeat returns.

The third shape is the dashboard pointed at the wrong store. Telemetry is collected faithfully, but a workspace consolidation or a copied dashboard left the query reading a store the resource never reported to. Everyone insists the data must be missing because the trusted dashboard is blank, when in fact the data is full in a store nobody is watching. The identifier comparison settles it in seconds.

A particularly common variant of the wrong-signal confusion deserves its own callout: the activity log. The activity log records control-plane operations, who created or deleted or modified a resource, and it lives at the subscription level rather than on an individual resource. People expecting to see those administrative events in a resource's logs find nothing, because the activity log has its own separate export to a workspace and its own table. If you want subscription operations queryable in Kusto, you create a subscription-level diagnostic setting that routes the activity log to the workspace, after which the AzureActivity table fills.

```bash
# Route the subscription activity log into a workspace so it is queryable
az monitor diagnostic-settings subscription create \
  --name "activity-to-workspace" \
  --location <region> \
  --subscription "<sub-id>" \
  --workspace "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.OperationalInsights/workspaces/<workspace-name>" \
  --logs '[{"category":"Administrative","enabled":true},{"category":"Security","enabled":true},{"category":"Policy","enabled":true}]'
```

The fourth shape is the half-configured setting, where a category the team needs now was never among the categories the original author enabled. The fifth is the partial visibility of an RBAC gap, where one person sees the data and another does not, and the comparison between the two accounts is the entire diagnosis. Each of these shapes maps to exactly one row in the missing-telemetry table, and the practice that makes them fast to recognize is having seen them before, deliberately reproduced. Standing up a resource, breaking each pipe in turn, and watching the specific symptom appear is the kind of structured failure rehearsal that [ReportMedic](/2025/03/31/azure-devops-observability/) drills are built to deliver, so that the production incident is recognition rather than discovery.

## How do I stop the telemetry pipe from breaking in the first place?

The cure for almost every cause in this article is the same, and it is preventive rather than reactive: build the pipe as code at deployment time, and verify it after deployment, so the resource is never live without its telemetry routed and you never discover the absence during an incident. The forward-only nature of every routing change makes this non-negotiable. You cannot recover the hour of logs you wanted when the view was empty; you can only ensure the next resource never has that gap.

The first preventive move is to define the diagnostic setting in the same template that defines the resource, so the resource cannot exist without its pipe. In Bicep, the setting is a child resource and a few lines, and once it is part of the module, every deployment of that resource ships with telemetry routing attached.

```bicep
resource appService 'Microsoft.Web/sites@2022-09-01' existing = {
  name: appServiceName
}

resource diag 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'send-to-central-workspace'
  scope: appService
  properties: {
    workspaceId: workspaceResourceId
    logs: [
      { category: 'AppServiceHTTPLogs', enabled: true }
      { category: 'AppServiceConsoleLogs', enabled: true }
    ]
    metrics: [
      { category: 'AllMetrics', enabled: true }
    ]
  }
}
```

The second preventive move is to enforce the setting at scale rather than relying on every author to remember it. A built-in or custom policy can require that resources of a given type carry a diagnostic setting routing to a designated workspace, and a deploy-if-not-exists policy can create the setting automatically when a resource is missing one. This turns "we forgot to add monitoring" from a recurring incident into a structural impossibility, because the platform adds the pipe for you. The governance approach to enforcing telemetry routing across an environment, and how it threads into a delivery pipeline, is developed in [monitoring and observability for DevOps](/2025/03/31/azure-devops-observability/), which treats observability as a shipped artifact rather than an afterthought.

The third preventive move is verification, because a setting that exists is not the same as a setting that works. After a deployment, a short check that confirms the expected tables are filling closes the loop. A scheduled query that counts rows per resource over the last hour and flags any expected source with zero rows catches a broken pipe within an hour instead of within an investigation.

```kql
// Flag resources that should be reporting but show no rows in the last hour
let expected = dynamic(["app-prod-01", "app-prod-02", "app-prod-03"]);
AppServiceHTTPLogs
| where TimeGenerated > ago(1h)
| summarize Rows = count() by _ResourceId
| extend name = tostring(split(_ResourceId, "/")[-1])
| where name in (expected)
```

Comparing the resources that reported against the resources you expected to report turns silence into a signal. The fourth preventive move is consolidation discipline: every extra workspace is another place data can hide, so a deliberate workspace design, with a clear rule for which telemetry lands where, removes the wrong-workspace cause structurally. The reasoning behind workspace topology, how many to run and how to scope them, is part of the [Azure Monitor and Log Analytics guide](/2022/04/11/azure-monitor-log-analytics-guide/), and getting it right once spares you a recurring class of confusion.

Practicing all of this, writing the setting in a template, breaking it with a policy exception, watching the verification query catch the gap, is exactly the rehearsal loop [VaultBook](/2023/07/17/configure-diagnostic-settings/) labs are designed to compress into an afternoon, so the preventive habits are built before the production resource needs them rather than after it failed silently.

The fifth preventive move is to alert on absence rather than only on errors. Most teams alert when a metric crosses a threshold or an error count climbs, but a silent pipe produces neither; it produces nothing, and nothing rarely triggers an alarm. A log-search alert that fires when an expected source reports zero rows over a window turns the most dangerous failure, the one nobody notices, into a page. For agent-based machines, a heartbeat alert that fires when a machine stops reporting catches a dead agent within minutes instead of when someone next needs the guest data. The pattern is to invert the usual logic: instead of alerting on a bad value, alert on the absence of any value from a source you expect to be chatty. A scheduled query that lists your expected sources, counts their recent rows, and raises an alert for any source at zero closes the loop that the verification query opened, because a verification you have to remember to run is a verification you will forget, while an alert that watches for silence runs itself. This is the single most effective habit for never being surprised by an empty view again, because it means the platform tells you the pipe broke before a human discovers it during an incident.

## Why does the data land in a table you did not expect?

A subtle source of empty results is not that telemetry is absent but that it arrived under a different table name than the one you queried. Resource logs can be stored in one of two layouts, and which layout a setting uses determines where the rows land. Querying the wrong layout returns nothing while the data sits, full, in a neighbor you never opened.

### What is the difference between the shared and resource-specific table modes?

The shared mode collects many resource types into a single broad table with a generic schema, while the resource-specific mode writes each resource type into its own dedicated table with a tailored schema and named columns. The mode is chosen on the diagnostic setting, and the two write to different table names, so a query aimed at one mode finds nothing if the setting used the other.

The practical consequence is that two engineers can both be correct and both see an empty result, because one queries the broad shared table and the other queries the dedicated table, and the data is in whichever one the setting selected. The shared layout puts a wide range of sources together with a column for the resource that emitted each row, which is convenient for cross-resource searches but awkward because the schema is generic and many fields are packed into a single properties column. The dedicated layout gives each source a clean, strongly typed table that is far easier to query and cheaper to scan, which is why newer guidance favors it, but it means the rows are not where someone trained on the older layout expects them.

The confirming check is to ask the platform which tables actually received rows, rather than to assume a name. A search across the store that summarizes by table name and recency surfaces exactly where the data landed.

```kql
search *
| where TimeGenerated > ago(2h)
| summarize Rows = count() by $table
| sort by Rows desc
```

If the rows you wanted appear under a dedicated table while you had been querying the broad one, or the reverse, you have found the cause, and the fix is to query the table the setting actually populates. If you want to change which layout a resource uses going forward, the mode is a property on the diagnostic setting, and switching it changes where future rows land without moving the rows already written under the old name. Knowing both layouts exist, and that a single resource type can have data split across them if the mode changed at some point, saves you from concluding that data is missing when it is merely filed under a name you did not check. The schema differences and the reasoning behind preferring the dedicated layout are part of the data model covered in the [Azure Monitor and Log Analytics guide](/2022/04/11/azure-monitor-log-analytics-guide/).

## Why is your Application Insights data missing?

Application telemetry follows a different road again. Traces, requests, dependencies, and exceptions from an instrumented application do not arrive through a resource diagnostic setting; they arrive because the application itself is instrumented to send them, and the failure modes are correspondingly different. When application telemetry goes missing, the diagnostic-settings-first rule still applies in spirit, but the pipe you check is the instrumentation, not a platform setting.

### Why does my instrumented app send no telemetry?

Because the application is either not configured with a valid connection string, not loading the instrumentation at runtime, or sending data that is being dropped by sampling before it lands. Application telemetry is pushed by the app's own code or runtime, so the break is on the sending side, and the check is whether the connection string is present and correct and whether the runtime actually initialized the telemetry pipeline.

The most common application gap is a missing or wrong connection string. The instrumentation needs to know where to send its data, and that destination is carried in a connection string that the application reads from configuration or an environment variable. If that value is absent, blank, or copied from a different component, the telemetry has nowhere to go and the resource shows nothing. Confirm it by inspecting the application's effective configuration for the connection string and comparing it to the target component's value.

```bash
# Check the connection string an App Service is actually configured with
az webapp config appsettings list \
  --resource-group <rg> \
  --name <app-name> \
  --query "[?name=='APPLICATIONINSIGHTS_CONNECTION_STRING'].value" \
  --output tsv
```

If that returns empty or a value that does not match the component you are querying, the application is either sending nowhere or sending elsewhere, which is the application-layer twin of the wrong-workspace cause. The fix is to set the correct connection string and restart the application so the runtime picks it up.

A second application gap is sampling. To control volume and cost, the instrumentation can sample, sending a representative fraction of telemetry rather than every item. Aggressive sampling can make low-frequency events appear absent when they are simply not in the sampled set, and a misconfigured rate can drop far more than intended. The tell is that high-frequency telemetry appears while rare events seem missing, which points at sampling rather than a dead pipe. Reviewing the sampling configuration and the ingestion sampling settings tells you whether data is being discarded by design. A third gap is that the application never initialized the telemetry at all, because the instrumentation package was not added or the startup code that wires it in was omitted, so the connection string is correct but nothing reads it. Confirming initialization usually means checking the application's startup logs for the telemetry pipeline starting, or sending a test event and watching for it. Across all three, the principle holds: application telemetry is pushed, so when it is missing you inspect the sender.

## A worked walkthrough: breaking and restoring each pipe

Reading about causes builds recognition slowly; reproducing them builds it fast. The most valuable thing you can do with this article is run a controlled exercise where you stand up a resource, break each pipe deliberately, watch the specific symptom appear, and restore the flow, so that every empty view in production maps instantly to a cause you have already seen. Here is the sequence, structured so you observe the symptom and the confirming check for each cause in turn.

Begin by deploying a simple resource, an App Service or a storage account, into a fresh resource group with a Log Analytics workspace alongside it, but deliberately do not create any diagnostic setting yet. Generate some activity against the resource, then query the log table you would expect. The result is empty. Run the diagnostic settings list and observe the empty array. You have just reproduced root cause one, the most common one, and you have seen its exact signature: activity occurring, table empty, setting list empty. The lesson lands because you watched it happen rather than read about it.

Now create the diagnostic setting pointing the resource's logs at the workspace, generate fresh activity, wait past the ingestion window, and query again. Rows appear. You have watched the pipe come alive, and you have learned the forward-only property firsthand, because the activity you generated before the setting existed is nowhere in the table while the activity after it is present. Note the boundary; it is the clearest possible demonstration that collection begins when the pipe is built and cannot reach backward.

Next, reproduce the wrong-workspace cause by creating a second workspace and repointing the setting at it, while leaving your query aimed at the first. Generate activity and query the first workspace; it is empty again, even though the setting exists and the resource is busy. Now query the second workspace and watch the rows appear there. Side by side, you have proven that an existing, healthy setting can still produce an empty view if it points somewhere other than where you read, and you have practiced the identifier comparison that confirms it. Repoint the setting back and the first workspace fills again.

For the agent case, deploy a small virtual machine with the agent and a collection rule, confirm the heartbeat appears, then break the pipe in two distinct ways. First, remove the collection rule association and observe that the heartbeat continues while the performance tables stop filling, the exact signature of an agent that is alive and collecting nothing. Restore the association and the tables resume. Second, tighten the network so the agent loses its outbound path, and watch the heartbeat itself stop at a timestamp you can read later. Open the path and the heartbeat returns. Having seen both, you will never again assume a present heartbeat means all agent data must be flowing, nor assume an absent heartbeat means the agent was never installed.

Finish with the cheap-to-reproduce causes. Create a setting with one category enabled and another disabled, query the disabled category's table, and confirm it is empty while the enabled one fills, reproducing the half-configured setting. Then remove your own read role on the workspace, run a query that returns nothing, have a colleague run the identical query and see rows, and restore your role, reproducing the access gap. By the end of this exercise you will have seen all six causes appear and disappear under your own hands, and the recognition you built is the difference between a fifteen-minute incident and a two-hour one. This entire loop, a resource, six deliberate breaks, six confirming checks, and six restorations, is the kind of structured failure rehearsal that the [ReportMedic](/2025/03/31/azure-devops-observability/) drill format is built to package, so a team can run it together and leave with shared muscle memory rather than individual war stories.

## What changed when the legacy collection agent retired?

A specific and time-bound cause deserves its own treatment because it produced a wave of missing-telemetry incidents: the retirement of the older guest collection agent in favor of the Azure Monitor Agent. For years, guest signals flowed through a legacy agent that used a different configuration model, and machines that depended on it kept reporting right up until that agent stopped being supported, at which point their guest data went silent unless they had been migrated. If a previously reliable machine stopped sending performance counters or syslog around the retirement window, an incomplete migration is a strong candidate.

### Why did guest data stop after the agent migration?

Because the legacy agent and its successor use different mechanisms to decide what to collect. The older agent read its configuration from workspace-level settings, while the Azure Monitor Agent collects on the basis of data collection rules associated with each machine. A machine migrated to the new agent without a corresponding collection rule keeps a heartbeat but gathers none of the streams the old agent used to, so its guest tables empty out even though the migration looked complete.

This is the agent-alive-collecting-nothing signature from root cause two, but with a specific historical trigger. The remedy is the same: confirm the collection rule associations on the machine, and if they are absent, create and associate a rule that names the streams the machine should gather. The reason this caught so many teams is that the legacy model's configuration did not translate automatically into the new model's rules, so a migration that moved the agent without recreating the collection intent left a gap that only surfaced when someone went looking for the guest data. Confirm which agent a machine runs and whether it has the rules it needs.

```bash
# Confirm the Azure Monitor Agent extension and its provisioning on a VM
az vm extension list \
  --resource-group <rg> \
  --vm-name <vm-name> \
  --query "[?contains(name,'AzureMonitor')].{name:name, state:provisioningState}" \
  --output table

# Then confirm a data collection rule is associated
az monitor data-collection rule association list \
  --resource "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Compute/virtualMachines/<vm-name>" \
  --output table
```

A successfully provisioned new agent with no associated rule is the exact gap the migration left, and creating the rule closes it. Because retirement dates and supported-agent guidance shift over time, treat the specifics here as a pointer to check against the current official documentation rather than a fixed fact; the durable lesson is that an agent change without a matching collection intent produces silent guest data, and the collection rule association is what you confirm. Rehearsing the migration in a lab, moving a machine to the new agent, watching its guest tables empty when no rule follows, and restoring them by associating a rule, is the kind of controlled exercise the [VaultBook](/2023/07/17/configure-diagnostic-settings/) environment is suited to, so the migration in production is a known quantity rather than a surprise.

## Which related failures get confused with missing telemetry?

Several adjacent problems wear the same empty-view costume, and mistaking one for another sends you down the wrong fix. Knowing the neighbors of this failure keeps you from repairing a pipe that was never broken.

The closest neighbor is ingestion latency. Data that is collected correctly still takes a bounded amount of time to become queryable, so a query against the last few minutes can show nothing for telemetry that is flowing perfectly and will appear shortly. The tell is that a wider time window shows the data while a narrow one does not, and the cause is timing rather than routing. Treating normal latency as missing data leads people to rebuild settings that were fine, which is why the raw count over a generous window is the first thing to run; the full treatment of normal versus abnormal delay lives in [fixing Log Analytics ingestion delay](/2023/03/27/fix-log-analytics-ingestion-delay/).

The second neighbor is a wrong table name or schema assumption. Resource logs land in either a shared table or a resource-specific table depending on the collection mode the setting uses, and querying the table you assumed rather than the table the data actually lands in returns nothing. The data is present under a different table name. The check is to list the tables that hold recent rows rather than to assume a table name.

```kql
// List which tables actually received data recently
search *
| where TimeGenerated > ago(1h)
| summarize Rows = count() by $table
| sort by Rows desc
```

That listing shows you every table with fresh rows, so if your expected table is absent but a neighbor is full, you were querying the wrong schema, not facing a missing pipe. The third neighbor is a retention expiry, where the data was collected and queried successfully in the past but has aged out of the workspace's retention window, so a query for last month returns nothing while last week is full. The tell is that recent data exists and only old data is gone, which is retention working as configured rather than a collection failure.

The fourth neighbor is a daily cap or a throttle. A workspace can be configured with a daily ingestion cap, and once the cap is hit, collection pauses for the rest of the day, producing a partial day of data followed by silence that resumes the next day. The tell is a clean cutoff at the same time each day with a fresh start the following morning. That is a cost-control feature behaving as set, not a broken pipe, and the fix is to raise or remove the cap if the data matters more than the ceiling. Distinguishing these four neighbors from a genuine routing failure is what the raw-count and table-listing checks are for; they tell you whether the data is absent, delayed, elsewhere, or aged out, and each of those leads to a different and correct response.

## How do you build a reusable runbook for an empty view?

The fastest responders do not rediscover the diagnosis each time; they run a fixed sequence and let the answers route them. Turning the diagnostic-settings-first rule into a written runbook means the next empty view becomes a checklist rather than an investigation, and it means anyone on the team, not just the person who has seen it before, can resolve it. The runbook is short because the checks are decisive.

### What sequence resolves a missing-telemetry incident fastest?

Run six checks in priority order: confirm a diagnostic setting exists, confirm it points at the workspace you query, confirm something is feeding it, confirm you are asking for the right signal type, confirm the category is enabled, and confirm you have read access. Stop at the first check that fails, because that is your cause, and apply the matching fix before moving on.

Step one is the setting existence check, because it catches the most common cause outright. List the settings on the resource; an empty array ends the investigation and sends you to create a pipe. Step two, if a setting exists, is the destination check; pull the workspace identifier from the setting and compare it to the store your query reads, and a mismatch ends the investigation and sends you to repoint either the setting or the query. Step three is the feed check; for platform-routed logs, the setting plus a recent raw count tells you data is arriving, and for agent-routed data, the heartbeat query tells you the agent is alive. Step four is the signal-type check; if you wanted a metric, read it from the metrics store and stop treating an empty log table as a fault. Step five is the category check; inspect the toggles inside the setting and enable the one you need if it is off. Step six is the access check; compare what you see against what a colleague sees, and if the data is visible to them and not you, grant yourself the reader role.

Codified as a query sequence to run inside the workspace, the heart of the runbook looks like this, and you can save it as a function so the whole team runs the same diagnosis.

```kql
// Step 3a: does ANY expected table hold recent rows?
search *
| where TimeGenerated > ago(24h)
| summarize Rows = count() by $table
| sort by Rows desc

// Step 3b: for agent data, is the machine alive?
Heartbeat
| where TimeGenerated > ago(30m)
| summarize LastSeen = arg_max(TimeGenerated, *) by Computer
| project Computer, LastSeen, OSType, Version

// Step 5 cross-check: which categories arrived for a given resource?
AzureDiagnostics
| where TimeGenerated > ago(24h)
| summarize Rows = count() by Category, ResourceProvider
| sort by Rows desc
```

The first query answers whether the store holds anything at all, which immediately separates a pipe failure from a query failure. The second answers the agent's alive-or-dead question for guest data. The third reveals which categories are actually arriving for a resource, which exposes a half-configured setting where one category flows and another is silent. Running these three before touching a dashboard query resolves the large majority of incidents, and pairing them with the command-line setting and association checks from earlier sections covers the rest.

A runbook is only durable if it is stored where the team finds it under pressure, so keep it next to the dashboards it supports and treat it as part of the observability deliverable rather than tribal knowledge. The discipline of shipping the diagnosis alongside the telemetry, so that an empty view comes with its own troubleshooting guide attached, is the same maturity the broader practice in [monitoring and observability for DevOps](/2025/03/31/azure-devops-observability/) argues for: observability is not just the data, it is the data plus the means to trust it and to debug it when it goes quiet. Building and drilling this runbook as a team, then timing how fast a fresh engineer can resolve a planted failure with it, is exactly the kind of measurable exercise the [ReportMedic](/2025/03/31/azure-devops-observability/) drill format turns into repeatable practice.

## The verdict on missing Azure Monitor telemetry

Strip the incident down to its essence and the lesson is a single sentence: an empty view is a question about the pipe, not the query. The diagnostic-settings-first rule holds because the platform separates the generation of a signal from its collection by design, so the default state of a resource is that its detailed logs go nowhere, and the most common reason a view is empty is that nobody ever built the route. Confirm the pipe exists, confirm it points at the store you are reading, confirm something is putting data into it, and only then suspect the query.

The six causes are distinct and each has a one-minute confirming check. No diagnostic setting is the listing that comes back empty. A dead agent is the heartbeat that does not appear. A wrong workspace is the identifier that does not match. A metrics-versus-logs confusion is the chart that exists while the table does not. A disabled category is the toggle that is off inside a setting that is on. An access gap is the data that one person sees and another does not. Run the checks in the order the missing-telemetry table lists them, because that order puts the highest-probability cause first, and you will resolve the typical incident in minutes rather than hours.

The durable answer is preventive. Build the diagnostic setting as code in the same template as the resource, enforce it with policy so no resource ships without its pipe, verify after deployment that the expected tables are filling, and keep workspace topology disciplined so data has fewer places to hide. Do that and the missing-telemetry incident stops recurring, because the only telemetry you cannot recover is the telemetry you never collected, and a pipe wired in at deployment never has that gap. A senior engineer reading this would recognize the diagnosis as the correct one and would hand it to a teammate staring at an empty chart, because it replaces the reflex to edit the query with the discipline to check the pipe, and that single reframe is what turns the incident around.

## Frequently asked questions

### Q: Why are my logs or metrics missing in Azure Monitor?

In most cases nothing is broken; the telemetry was never collected. A resource generates events internally but does not persist its detailed logs to any queryable store until a diagnostic setting routes them to a destination. With no setting present, the table you query stays empty no matter how the query is written. The fastest confirmation is to list the diagnostic settings on the resource; an empty result means there is no pipe, and the fix is to create one pointing the wanted categories at your workspace. Platform metrics behave differently because they are collected automatically, which is why you can see metric charts while log queries return nothing. Once you accept that a healthy resource and a collected log are independent facts, the diagnosis becomes a short sequence of checks rather than a long round of query edits, and the typical incident resolves in minutes.

### Q: Does a missing diagnostic setting cause no logs?

Yes, entirely. A resource log category is not captured anywhere you can query it until a diagnostic setting carries it to a destination such as a Log Analytics workspace. The default state of every newly created resource is that its logs route nowhere, so the corresponding tables never fill and queries return zero rows. This is the single most common reason a view is empty, which is why the first action in any missing-telemetry incident is to confirm whether a setting exists at all. Listing the settings on the resource answers it immediately; an empty array is the diagnosis. The fix is to create the setting with the categories you need, but remember that collection only begins from the moment the setting exists. It does not backfill the period before it was created, so any data you wanted from before the setting was added is gone, and the strongest argument for wiring the pipe in at deployment is precisely that you cannot recover what was never captured.

### Q: Why is the Azure Monitor Agent not reporting a heartbeat?

A silent agent has a short list of causes: the agent extension is not installed or failed provisioning, the agent service is not running inside the guest, no data collection rule is associated so it has nothing to collect, or the machine cannot reach the ingestion endpoint because a network change closed its outbound path. The heartbeat is the agent's proof of life, so its absence localizes the problem to the agent layer rather than the routing layer. Confirm by querying the Heartbeat table for the machine over the last fifteen minutes; if it does not appear, work down the stack. Check the extension provisioning state, confirm a collection rule is associated, and verify outbound reachability to the data collection endpoint. A previously healthy agent that goes dark at a specific timestamp almost always lines up with a network or firewall change, so correlate the last heartbeat with recent infrastructure edits. Restoring the broken layer brings the heartbeat back, and the guest data resumes shortly after.

### Q: Are my logs going to the wrong Log Analytics workspace?

This is common in environments that accumulated several workspaces over time. The resource collects faithfully, but its diagnostic setting points at one store while your dashboard queries another, so the view is empty even though the data is full somewhere else. Confirm it by reading the workspace identifier inside the resource's diagnostic setting and comparing it to the identifier your query targets; they are exact resource paths, so a mismatch is unambiguous. The fix depends on intent. If the resource should report to the central workspace and was misconfigured, repoint the setting at the correct destination. If the resource is correctly reporting to its own workspace and the dashboard simply aims at the wrong one, fix the query side instead. A cross-workspace union query is a useful confirmation because it shows rows appearing from one store and not another, proving the data exists and you were reading the wrong place rather than facing a collection failure.

### Q: Why do I see metrics but no logs for a resource?

Because metrics and logs are different signal types stored in different places. Platform metrics are collected automatically into a time-series store and surface in Metrics explorer without any configuration, while resource logs require a diagnostic setting to be routed into a workspace. A resource with no log routing will therefore show healthy metric charts on its overview blade and return nothing from a Kusto log query at the same time, which is misleading because the graphs make it look fully monitored. The confirming question is what you are actually after. A numeric measurement over time, such as a count or a latency, is a metric and you read it through the metrics tool. A record of discrete events, such as requests or queries or authorization decisions, is a resource log and needs a setting routing that category before any query finds it. If you only ever needed the metric, you were simply looking in the wrong tool; if you need the events, create the diagnostic setting.

### Q: How do I confirm telemetry is actually flowing?

Run a deliberately broad check before you trust any narrow query. A raw count over a generous window, such as seven days, against the table you expect tells you instantly whether the table holds any rows independent of your filters. A count of zero over a week means the pipe is the problem, so go check the diagnostic setting, the agent, and the workspace in that order. A positive count means the table holds data and your original query's filters or time range were excluding it, so query debugging is now the right activity. For agent-based data, query the Heartbeat table for a recent timestamp to confirm the agent is alive. For platform metrics, read them directly through the metrics API. These three confirmations, a raw count, a heartbeat, and a metric read, separate a collection failure from a query problem in under two minutes and stop you from editing a query against an empty table.

### Q: How do I check whether a resource has any diagnostic setting configured?

List the settings on the resource directly. The command line returns every diagnostic setting attached to a resource along with the destination each one points at, and an empty array is conclusive evidence that no pipe exists. The portal shows the same thing under the resource's Diagnostic settings blade, where an empty list and an invitation to add a setting both confirm the absence. This is the very first check in any missing-telemetry incident because it is fast, unambiguous, and resolves the most common cause outright. If the listing returns a setting, note the destination and the enabled categories rather than stopping there, because a setting that exists can still point at the wrong workspace or have the category you need switched off. The presence of a setting narrows the problem; it does not close it. But the absence of a setting closes it immediately, and you move straight to creating one.

### Q: Why does a log category return no rows even though the setting exists?

Because each category inside a diagnostic setting toggles independently, and the setting only routes the categories that are switched on. Someone created the setting and enabled the categories they needed at the time, which may not include the one you need now, so that category's table stays empty while the enabled ones fill. The presence of a setting is not the presence of every category. Confirm it by inspecting the category toggles inside the setting rather than just confirming the setting exists; the command output lists each category and whether it is enabled. If the category you query shows as disabled, you have the cause. The fix is to enable it by updating the setting, after which events in that category route forward from the change. As with every routing change, it does not backfill, so the table fills with new events rather than recovering old ones, which is why a thorough setting at deployment beats one assembled category by category during incidents.

### Q: Can a permission gap make logs appear missing?

Yes. Reading data from a workspace requires a role that grants read access at the workspace scope, and without it a query often returns an empty result rather than an explicit denial, which makes an access problem look like a collection problem. The signature is that a colleague who has access runs the identical query and sees rows while you see nothing, which is impossible if the data were truly absent. Confirm by checking your role assignments at the workspace scope or by having someone with access run the same query. The fix is to grant the appropriate role, most commonly Log Analytics Reader at the workspace, which permits querying without any write rights. A subtler variant is resource-context access, where a principal sees only telemetry for resources they have permission on, so a query spanning resources they cannot see returns partial or empty results. The diagnostic move is the same: determine whether the data is invisible to everyone or only to you.

### Q: Why does my Kusto query return nothing when the data is there?

When the table genuinely holds rows but your query returns none, the cause is on the query side: a time range that excludes the data, a filter that matches nothing, the wrong table name, or the wrong workspace selected. Prove the data exists first with a raw count over a wide window and no filters; a positive count confirms the table is full and the query is the problem. Then reintroduce your filters one at a time to find which one excludes everything. The most frequent culprit is the time range, especially a narrow recent window that falls inside the normal ingestion latency, so freshly collected data has not yet become queryable. The second most frequent is a table-name assumption, because resource logs can land in a shared table or a resource-specific one depending on the collection mode. Listing which tables received recent rows tells you where the data actually is, and once you query the right table over the right window with the right filters, the rows appear.

### Q: How do I find which workspace a resource sends its diagnostic logs to?

Read the destination out of the diagnostic setting itself. Listing the settings on the resource and projecting the workspace identifier returns the full resource path of the store each setting points at. Compare that path to the workspace your query or dashboard targets; if they differ, the data is in the destination the setting names and you have been reading a different store. The portal shows the destination on the setting's detail view, and the command line returns it as a field you can compare exactly. This comparison is the confirming step for the wrong-workspace cause, and it is decisive because the identifiers are precise resource paths rather than friendly names that might collide. Once you know the true destination, you either repoint the setting at the workspace you intend telemetry to land in, or you repoint your query and saved views at the workspace that actually holds the data, depending on which side of the mismatch was wrong.

### Q: Why did logging stop after I recreated or moved the resource?

A diagnostic setting is attached to a specific resource identity. When you delete and recreate a resource, or move it in a way that changes its resource identifier, the original setting does not follow automatically, so the new resource starts life with no pipe and its tables go empty from the moment of recreation. The data before the change is intact under the old identifier; the data after it is simply not being collected because the routing did not carry over. Confirm by listing the diagnostic settings on the new resource; an empty result against a resource that used to report is the signature. The fix is to recreate the setting on the new resource, which is exactly the situation that argues for defining the setting as code in the same template as the resource. When the pipe is part of the deployment, recreating or redeploying the resource recreates the pipe with it, and the gap never opens. A manual setting, by contrast, is easy to forget during a rebuild.

### Q: Why is the Azure Monitor Agent installed but collecting nothing?

Because the agent collects on the basis of a data collection rule, and an agent with no rule associated is alive but idle. The heartbeat still appears, since the heartbeat is built in, but no other table fills, which produces the confusing state where the agent looks healthy and the data is still missing. Confirm by listing the data collection rule associations on the machine; an empty association list alongside a healthy heartbeat is the exact signature of an agent that is running and gathering nothing. The fix is to create a collection rule that names the streams you want, such as the performance counters or the syslog facilities, point it at the workspace, and associate it with the machine. Within a few minutes the agent begins gathering those streams and the corresponding tables, Perf for counters or Syslog for Linux events, start to fill. This case is worth knowing because the heartbeat being present misleads people into thinking the agent layer is fine when the rule layer is the gap.

### Q: How do I query the Heartbeat table to check an agent?

Query the Heartbeat table for recent timestamps grouped by machine. Filtering to the last fifteen minutes and taking the most recent record per computer shows you which machines are reporting and when each was last seen. A machine that appears with a fresh timestamp is alive and shipping its heartbeat, so any missing data from it is a collection-rule or signal-type issue rather than agent death. A machine that does not appear at all is not reporting, which isolates the cause to the agent layer. A machine whose last heartbeat is older than expected tells you when it went silent, and that timestamp is the thread you pull, correlating it with a deployment, a restart, or a network change. The Heartbeat table is the single most useful confirmation for any agent-based telemetry gap because it answers the alive-or-dead question directly and gives you a timestamp to anchor the investigation, which is why it sits near the top of the diagnostic sequence for guest data.

### Q: Can a brand-new diagnostic setting take time before logs appear?

Yes, two timing effects apply. First, the setting only captures events from the moment it exists, so a quiet resource may not generate the events you want for a little while after you create the pipe, and the table will look empty until the resource actually does something worth logging. Second, even once events are generated, there is a normal, bounded ingestion latency before the data becomes queryable, so a query run immediately after creating the setting can return nothing for telemetry that is on its way. The fix is patience plus a wide window: give the resource time to produce events, then query over a generous range rather than the last minute. If after a reasonable wait the table is still empty, return to the other causes, confirming the category is enabled and the destination is correct. Distinguishing this expected startup delay from a genuine problem is the same skill as distinguishing normal latency from data loss, which is covered in depth in the ingestion-delay companion article.

### Q: Why do platform metrics show but activity logs are empty?

Because the activity log is a subscription-level signal, not a resource-level one, and it has its own separate routing. The activity log records control-plane operations, who created, modified, or deleted resources, and it lives at the subscription scope rather than on any individual resource. Looking for those administrative events in a specific resource's logs returns nothing, because that is not where they live. To make subscription operations queryable in a workspace, you create a subscription-level diagnostic setting that routes the activity log categories, such as Administrative, Security, and Policy, to the workspace, after which the AzureActivity table fills. This is distinct from platform metrics, which are collected automatically per resource, and distinct from resource logs, which need a per-resource setting. The three signal types, metrics, resource logs, and the activity log, each have their own collection path, and confusing one for another is a frequent reason a view looks empty. Routing the activity log at the subscription level is the fix for missing administrative events specifically.
