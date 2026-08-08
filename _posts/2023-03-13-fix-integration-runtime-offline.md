---
layout: post
title: "Fix Self-Hosted Integration Runtime Offline"
page_title: "Fix Self-Hosted Integration Runtime Offline: Diagnose IR Unavailable, Node Not Registered, and Outbound Connectivity Errors in Azure Data Factory and Synapse"
date: 2023-03-13
categories: ["Technology"]
tags: ["Azure", "Integration Runtime", "Data Factory", "Synapse", "Troubleshooting", "Cloud Computing"]
excerpt: "Fix a self-hosted integration runtime offline by checking the node service and its outbound connectivity to Azure first, before recreating the runtime."
image: "/assets/images/blog/blog-17.webp"
reading_time: 60
author: "thomas-reid"
last_updated: 2023-03-13
lang: en
---
A pipeline that ran cleanly yesterday refuses to start today, and the run history shows a single blunt reason: the activity could not find an available node because the self-hosted integration runtime offline status has taken every node out of rotation. The monitoring blade paints the runtime red, the word "Unavailable" sits where "Running" used to be, and the copy activity that pulls from an on-premises SQL Server now fails before it moves a single row. This is one of the most common operational stalls in Azure data integration, and it is also one of the most misdiagnosed. The reflex, under deadline pressure, is to delete the runtime and build a new one. That reflex is almost always wrong, and acting on it can turn a ten minute restart into a half day rebuild that touches every linked service and every pipeline binding.

![Fixing a self-hosted integration runtime offline in Azure Data Factory root causes and the node-and-connectivity rule - Insight Crunch](/assets/images/blog/blog-17.webp)

The self-hosted integration runtime, which engineers shorten to self-hosted IR or SHIR, is the bridge that lets a cloud data service reach data that does not live in the cloud. When you build pipelines in Azure Data Factory or in the pipeline engine inside Synapse, the managed Azure runtime can reach public cloud endpoints on its own, but it cannot reach a database sitting inside your corporate network, a file share behind a firewall, or a virtual machine with no public address. The self-hosted IR is the agent you install on a Windows machine inside that private boundary so the cloud control plane can hand it work and it can move the data without anyone opening an inbound hole through the perimeter. When that agent reports offline, the cloud has lost contact with the one component that can see your private sources, and every pipeline that depends on it stops. Understanding what offline actually means, and what it almost never means, is the difference between a quick recovery and a destructive overreaction. If you want the full picture of where this component sits in the broader service, the [complete guide to Azure Data Factory](/2022/04/18/azure-data-factory-complete-guide/) lays out the runtime model end to end, and this article zooms into the single failure that takes the runtime dark.

## What does it mean when the self-hosted integration runtime shows offline?

Offline is a statement about a network heartbeat, not about your data or your pipeline logic. The self-hosted IR runs as a Windows service on a host you control, and that service opens an outbound, long-lived connection to the Azure control plane. On a schedule, the node tells the cloud that it is alive, healthy, and ready to accept activities. The portal reads those heartbeats and renders a status. When heartbeats arrive on time the runtime shows Running. When they stop arriving, or arrive late and then stop, the control plane marks the runtime Unavailable and the individual node Inactive or Offline. Nothing about your pipelines changed. Nothing about your data changed. What changed is that the agent on the host stopped phoning home, and the cloud, having no way to reach into your network on its own, can only report the silence.

### Why does my self-hosted integration runtime show offline?

A self-hosted integration runtime shows offline when its node stops sending heartbeats to Azure. The cause is almost always local to the host: the Windows service stopped, a firewall now blocks the outbound connection the agent needs, the node lost its registration, or the machine itself is down. The runtime definition in the cloud is intact; only the heartbeat is missing.

That framing matters because it points your hands at the right place. The status you see in the portal is a downstream symptom rendered in the cloud, but the fault that produced it lives on the host machine or on the network path between that host and Azure. You cannot fix a missing heartbeat by editing anything in the portal, because the portal is the listener, not the speaker. You fix it by going to the node, finding why it went quiet, and restoring its voice. This is the entire reason the recreate-the-runtime reflex is so wasteful: recreating the runtime builds a brand new listener in the cloud and hands you a brand new key, but it does nothing about the silent speaker on your host, which will register against the new runtime and then go silent again for exactly the same reason within minutes.

To gather the diagnostic signal properly, you read three things in sequence, and you read them on the host, not in the portal. The first is the state of the Windows service that runs the agent. The second is the outbound connectivity from that host to the Azure endpoints the agent depends on. The third is the node's registration and version health. Each of these maps to a distinct family of root causes, and the order is deliberate: a stopped service is the cheapest thing to confirm and the most common cause, so you check it first; a connectivity block is the second most common and the most often misdiagnosed, so you check it second; and registration and version problems, which are real but less frequent, come last. Working the list in this order means you spend your first two minutes on the two causes that account for the large majority of incidents.

## The node-and-connectivity rule for a self-hosted integration runtime

Here is the claim this article is built around, and it is worth committing to memory because it will save you from the rebuild reflex every time. The node-and-connectivity rule states that a self-hosted integration runtime offline status almost always means one of two things: the node's service is not running, or the node's outbound connectivity to Azure is blocked. Everything else, including registration faults, version mismatches, and single-node fragility, is a smaller slice of cases. Because the two dominant causes both live on the node, the correct first move is always to restore the node, never to recreate the runtime. Recreating the runtime is the destructive non-fix that engineers reach for precisely because the portal is where they are looking, and the portal is the one place the actual fault is not.

The rule has a corollary that is just as useful. Because the agent initiates an outbound connection and the cloud never initiates an inbound one, you almost never need to touch inbound firewall rules, and you almost never need a public IP on the host. When connectivity is the problem, it is outbound connectivity, and the question is whether the host can reach Azure, not whether Azure can reach the host. Engineers who come from an on-premises networking background sometimes burn an hour opening inbound ports and chasing NAT rules because that is the mental model they carry, and the self-hosted IR quietly inverts it. The agent reaches out; the cloud waits to be reached.

The findable artifact for this article is the InsightCrunch IR-offline table, which maps each root cause family to the one check that confirms it and the one fix that resolves it. Keep it next to your runbook. When the runtime goes red, you walk the table top to bottom, and the cause that survives its confirming check is your cause.

| Root cause family | The confirming check | The fix |
| --- | --- | --- |
| Service stopped on the host | `Get-Service DIAHostService` returns Stopped, or the host's Services console shows the Integration Runtime Service not Running | Start the service, set its startup type to Automatic, and confirm the node returns to Running in the portal |
| Outbound connectivity blocked | The diagnostic tool's connectivity test to Azure Relay fails, or a manual test to `*.servicebus.windows.net` on port 443 fails | Allow outbound 443 to the required Azure endpoints through the corporate firewall and any proxy, then re-run the connectivity test |
| Registration or key problem | The node never reaches Running after install or key rotation, and the configuration manager reports the node is not registered | Regenerate the authentication key, re-register the node with the current key, and confirm the node binds to the correct runtime |
| Node health or version mismatch | The node shows Running but flaps, or an auto-update left the node on a version the runtime no longer accepts | Update or roll the node to a compatible version, restart the service, and verify the version in the node pane |
| Single node down, no high availability | The runtime has one registered node and that node is Offline, so the whole runtime is Unavailable | Restore the single node, then register a second node on a separate machine using the same key so one failure no longer takes the runtime down |
| Host machine offline or rebooted | The host is unreachable on the network, or it rebooted and the service did not auto-start | Bring the host back, set the service to start automatically, and confirm the node re-establishes its heartbeat |

Every row in that table resolves without deleting the runtime. That is the whole point. The sections that follow take each family in turn, show you the check that proves it is your problem, and give you the tested fix.

## How do I read the runtime status and gather the diagnostic signal?

Before you chase a specific cause, you confirm the shape of the failure, because the shape tells you how many nodes are affected and how fast you must move. In the Azure Data Factory or Synapse studio, open the management hub, select Integration runtimes, and open the self-hosted runtime that the failing pipeline uses. The overview gives you the runtime status, which is the aggregate, and a node list, which is the detail. A runtime with one node will show Unavailable the moment that node goes Offline, because the aggregate has nothing healthy to fall back on. A runtime with two or more nodes can show Running while one node sits Offline, because a surviving node still answers, and that distinction changes your urgency: a single dead node in a multi-node runtime is a resilience event you fix calmly, while a dead node in a single-node runtime is a full outage you fix now.

The portal gives you the cloud's view, but the authoritative signal lives on the host. Remote into the machine where the agent is installed, or use your management tooling to run commands there, and open three views. First, the Microsoft Integration Runtime Configuration Manager, which is the desktop application installed alongside the agent; it shows the node's self-reported connection status to the cloud and to the Configuration Manager service, and it is the fastest read on whether the node believes it is connected. Second, the Windows Services console or a PowerShell service query, which tells you whether the underlying service is even running. Third, the diagnostic command line tool that ships with the agent, which can actively test connectivity rather than just report a cached status. Reading the host's own view of itself, rather than the cloud's view of the host, is what separates a five minute diagnosis from an hour of guessing.

```powershell
# Check whether the self-hosted IR Windows service is running on the host
Get-Service -Name "DIAHostService" | Format-List Name, DisplayName, Status, StartType

# The display name you will see is "Integration Runtime Service".
# Status should be Running and StartType should be Automatic for a healthy node.
```

If the service is Stopped, you have very likely found your cause and you can skip ahead, because a service that is not running cannot send a heartbeat and the runtime will be offline by definition. If the service is Running but the runtime still shows offline, the heartbeat is leaving the service and dying somewhere on the network path, which points you squarely at connectivity. This single branch, service stopped versus service running, splits the two dominant causes cleanly and tells you which section to read next.

The diagnostic tool deserves a moment of its own, because it is the most underused asset in this whole investigation. It lives in the agent's installation directory and is named for diagnostics, and its connectivity check actively opens the outbound connection the agent needs and reports success or the specific failure. Running it turns "the runtime is offline and I do not know why" into "the host cannot reach Azure Relay on port 443," which is a sentence you can act on.

```cmd
:: From the self-hosted IR install directory, run the diagnostics tool.
:: The path varies by version; locate the folder under Program Files.
cd "C:\Program Files\Microsoft Integration Runtime\5.0\Shared"

:: Actively test the outbound connection to the Azure Relay and control endpoints.
dmgcmd.exe -CheckConnectivityToServiceBus

:: Restart the node's service from the command line if you need to cycle it.
dmgcmd.exe -Restart
```

With the shape of the failure understood and the host's own view in hand, you now have a clean branch to follow. A stopped service sends you to the first root cause. A running service that still cannot reach Azure sends you to the second. Everything else sends you down the table. The companion environment is the place to build this muscle without risking production: you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.net/tools/azure-labs.html) to stand up a self-hosted IR, register a node, and watch the heartbeat in the portal, and you can [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) that take a healthy runtime offline in each of the ways below and ask you to bring it back, so the diagnosis becomes reflex rather than research.

## Root cause one: the integration runtime service stopped on the host

The single most common reason a self-hosted IR goes offline is also the most mundane: the Windows service that runs the agent is not running. The service can stop for ordinary reasons that have nothing to do with Azure. The host rebooted for monthly patching and the service was set to Manual start instead of Automatic, so it never came back. An administrator stopped the service to install something and forgot to restart it. The service crashed under memory pressure because the host was undersized for the copy volume and Windows reclaimed it. A scheduled maintenance script restarted the host outside the window you expected. In every one of these cases, the cloud sees the same thing, which is silence, and reports the same status, which is offline, even though the cause is entirely local and entirely benign.

### Does the IR service or node need restarting?

In most offline incidents, yes, restarting the node's service is the fix, because a stopped or wedged service is the leading cause. Start the Integration Runtime Service on the host, confirm it reaches Running, and set its startup type to Automatic so a reboot cannot strand it again. The node should re-register its heartbeat and the runtime should return to Running within a minute or two.

Confirming this cause is fast. The PowerShell service query above tells you the state directly, and the Services console shows the same thing with a startup type column that is often the real culprit. A service set to Manual will survive a running host indefinitely but will silently fail to return after any reboot, which produces the maddening pattern where the runtime is fine for weeks and then goes offline every patch Tuesday. The fix is two actions taken together. First, start the service so the immediate outage clears. Second, set the startup type to Automatic, and on a busy host consider Automatic (Delayed Start) so the service does not race other boot-time work for resources, so the next reboot brings the node back without anyone touching it.

```powershell
# Start the service and make the recovery durable across reboots
Start-Service -Name "DIAHostService"
Set-Service  -Name "DIAHostService" -StartupType Automatic

# Confirm it is up
Get-Service  -Name "DIAHostService" | Select-Object Name, Status, StartType
```

There is a deeper version of this cause worth naming, because it masquerades as a connectivity problem and wastes time. If the host is genuinely undersized, the service will start, run for a while, consume memory under copy load, and then be killed or wedged when the host runs out of headroom. The runtime flaps: Running, then Offline, then Running again as the service restarts, then Offline again under the next heavy activity. The portal shows an intermittent status that looks like a flaky network, but the service event log on the host tells the real story, with restart and crash entries clustered around your heaviest pipeline runs. The fix here is not networking and not a restart loop; it is capacity. Move the agent to a host with enough cores and memory for the concurrent copies you run, or distribute load across additional nodes, which the high availability section covers. A host that cannot hold the service up under load will keep going offline no matter how many times you restart it.

When you have started the service, set it to Automatic, and watched the node return to Running in the portal, this cause is closed. If the service was already running when you checked, this is not your cause, and you move to connectivity, which is where the genuinely tricky incidents live.

## Root cause two: the node lost outbound connectivity to Azure

When the service is running but the runtime is still offline, the heartbeat is leaving the agent and failing to reach Azure. The self-hosted IR depends on outbound connectivity to a specific set of Azure endpoints, and if any layer between the host and those endpoints blocks the path, the node goes silent even though it is healthy and trying. This is the most misdiagnosed cause because the host looks fine, the service is up, and nothing on the machine is obviously broken; the failure is in the network path, which is invisible from a casual glance at the host.

### What outbound connectivity does the self-hosted IR need?

The self-hosted IR needs outbound HTTPS on port 443 to the Azure control endpoints and, critically, to Azure Relay at the service bus domain `*.servicebus.windows.net`. The connection is always outbound and agent-initiated, so you do not open inbound ports or assign a public IP. If a corporate firewall, a proxy, or a network security group blocks outbound 443 to these endpoints, the node cannot reach Azure and the runtime reports offline.

The mechanics are worth understanding so you know what to test. The agent establishes its command channel and its interactive authoring channel through Azure Relay, which is reached over the service bus domain on port 443. Interactive actions such as previewing data or testing a linked service connection lean on that relay specifically, which is why a common symptom of a partial connectivity block is a runtime that shows Running for scheduled work but fails every connection test and data preview in the studio: the heartbeat path is open but the relay path is not. The data movement itself may use additional ports depending on the source, for example outbound 1433 when copying directly from a SQL source, but the runtime's own liveness depends on the 443 path to the control and relay endpoints. If outbound 1433 is blocked but 443 is open, the runtime stays online while specific copies fail, which is a different problem you would chase as a [Data Factory pipeline error](/2023/03/06/fix-data-factory-pipeline-errors/) rather than a runtime outage.

Confirming a connectivity block is exactly what the diagnostic tool is for, and you should reach for it before you touch a firewall rule, because it tells you precisely which path is failing.

```cmd
:: Active connectivity test from the host to the Azure Relay and control plane
dmgcmd.exe -CheckConnectivityToServiceBus

:: A simple manual probe of the relay domain on 443, useful when the tool is unavailable.
:: Replace the host portion with a relay endpoint from your runtime's node pane.
powershell -Command "Test-NetConnection -ComputerName <yournamespace>.servicebus.windows.net -Port 443"
```

A failing test usually traces to one of three layers, and you check them in order of likelihood. The first and most common is the corporate firewall or a network security group rule that does not allow outbound 443 to the service bus domain. The cure is an allow rule for outbound 443 to the required endpoints; the exact endpoint list for your runtime appears in the node pane of the runtime, and Microsoft publishes the canonical set, which you should verify against the current official documentation because Azure revises endpoint lists over time. The second layer is a proxy. Many corporate hosts route all internet traffic through a proxy, and the agent does not automatically inherit the system proxy in every configuration; you set the proxy explicitly in the Configuration Manager or in the agent's configuration file so the relay traffic is directed to the proxy rather than failing to leave the host. The third layer is DNS. If the host cannot resolve the service bus domain to an address, the connection never starts, and the failure looks identical to a blocked port even though the port is open. When a connectivity test fails with a resolution error rather than a refused connection, you are in DNS territory, and the techniques in the guide to [fixing Azure DNS resolution failures](/2022/12/26/fix-azure-dns-resolution/) apply directly, because a name that will not resolve is a name the agent cannot reach no matter how permissive the firewall.

The private networking case adds a wrinkle that catches teams who lock the host down hard. If you front Data Factory with a private endpoint and route the host through a proxy, you must split the traffic: the relay traffic for the agent's command channel still goes outbound to the service bus domain, possibly through the proxy, while traffic intended for the private endpoint must stay on the private path and not be sent to the proxy at all. Misrouting these two flows is a classic cause of a node that registers but then cannot maintain its heartbeat, and the symptom is a runtime that comes up briefly during install and then drifts offline. The discipline is to know which Azure name belongs on the public relay path and which belongs on the private path, and to route each accordingly.

Once the connectivity test passes, the node's heartbeat will resume on its own and the runtime returns to Running without any further action. You do not restart anything, you do not re-register anything, and you certainly do not recreate the runtime; you simply open the path the agent was already trying to use, and the heartbeat that had been dying in transit now lands.

## Root cause three: the node failed to register, or its key is wrong

Registration is how a node and a runtime recognize each other. When you create a self-hosted runtime in the cloud, Azure generates a pair of authentication keys, and you paste one of those keys into the agent on the host during setup. That key is the credential the node presents to bind itself to that specific runtime. A registration problem produces a node that has never reached Running, or a node that was healthy until a key was rotated and now cannot reconnect, and it is distinct from the service and connectivity causes because here the service may be running and the network may be open, yet the node still cannot establish its identity to the cloud.

### Why does a node fail to register with its authentication key?

A node fails to register when the authentication key it holds is expired, wrong, or no longer valid because the key was regenerated in the cloud. The node presents a credential the runtime no longer accepts, so the bind fails and the node never sends a heartbeat. The fix is to obtain the current key from the runtime and re-register the node with it.

The most common version of this is key rotation gone half-finished. Someone regenerates the authentication keys in the portal, perhaps as a security hygiene step or because a key leaked, and the new key invalidates the old one immediately. Any node still holding the old key is now presenting a credential that the runtime refuses, and that node goes offline the moment its current session ends. The portal shows the runtime as Unavailable or shows the node as not registered, and the host's Configuration Manager reports that it could not connect with the supplied key. The cure is to fetch the current key and re-register every affected node with it, which you can do from the command line so it scripts cleanly across a multi-node fleet.

```bash
# Fetch the current authentication keys for the runtime (Azure CLI)
az datafactory integration-runtime list-auth-key \
  --resource-group "rg-data" \
  --factory-name "adf-prod" \
  --integration-runtime-name "shir-onprem"

# If you need to rotate, regenerate a key, then re-register every node with the new one
az datafactory integration-runtime regenerate-auth-key \
  --resource-group "rg-data" \
  --factory-name "adf-prod" \
  --integration-runtime-name "shir-onprem" \
  --key-name authKey1
```

On the host, you register the node against the current key using the diagnostic tool, which binds the agent to the runtime that owns that key.

```cmd
:: Register this node with the current authentication key
dmgcmd.exe -RegisterNewNode "<paste-the-current-auth-key-here>"
```

A subtler registration failure happens when a node is pointed at the wrong runtime entirely. In an organization with several factories or several runtimes, it is easy to register a node with a key from a different runtime than the pipelines expect, and the result is a node that comes up healthy and Running, but against a runtime your pipelines do not use, so the pipelines still fail to find an available node on the runtime they do reference. The confirming check is to read which runtime the node is bound to in its Configuration Manager and compare it to the runtime name the failing linked service points at. When those names differ, the node is online but irrelevant, and the fix is to re-register it with the key from the correct runtime. This failure mode is invisible if you only look at node status, because the status is green; you have to compare identities, not just states.

Registration problems do not call for recreating the runtime either, which is worth stressing because the temptation peaks here. When a node will not bind and you are under pressure, deleting the runtime and starting over feels decisive, but it forces you to re-point every linked service and every pipeline at the new runtime, and it does nothing the regenerate-and-re-register sequence above does not do faster and without collateral damage. The runtime definition is fine; only the credential handshake failed, and a credential is the cheapest thing in the system to replace.

## Root cause four: node health, version mismatch, and the auto-update trap

A node can be running, connected, and correctly registered, and still go offline because of its own health or its version. The agent updates itself on a schedule by default, pulling new versions from Azure during a maintenance window. Most of the time this is invisible and beneficial. Occasionally an update lands on a node and leaves it in a state the runtime will not accept, or an update applies to some nodes in a multi-node runtime and not others, producing a version skew that destabilizes the runtime. Version and health problems are less frequent than service and connectivity faults, which is why they sit lower in the table, but they produce a distinctive flapping or post-maintenance offline pattern that the first two causes do not.

The auto-update trap is the most instructive case. Auto-update runs in a window, and during the update the node restarts its service to apply the new build. If the update window collides with a heavy pipeline run, or if the new build has a regression on your particular Windows version, the node can come back unhealthy or fail to come back at all, and the runtime shows offline starting at the same time every update cycle. The confirming check is correlation: line up the offline timestamps with the auto-update window shown in the runtime's settings, and if they coincide, the update is your trigger. The fix is to control the update timing so it never overlaps your critical runs, and to keep nodes on a known-good version when an update regresses. You set the update window in the runtime's auto-update settings, and you can pause or roll a node's version when a specific build misbehaves, verifying the running version in the node pane after the change.

Version skew across nodes is the multi-node sibling of this problem. When a runtime has several nodes, they should run the same agent version, and a large gap between versions can cause the runtime to behave erratically as nodes that disagree about the protocol drop in and out. The check is to read the version column in the node pane and look for nodes that lag well behind the others. The fix is to bring the lagging nodes up to the common version, restart their services, and confirm the versions converge. Keeping a multi-node runtime on a uniform version is ordinary hygiene that prevents a class of intermittent offline events that are otherwise very hard to attribute.

Health, separate from version, covers the host conditions that degrade the agent without stopping it outright. A disk filling up where the agent writes its working files, a clock that has drifted far enough to break the time-sensitive parts of the secure handshake, or antivirus software quarantining a component the agent needs can all produce a node that struggles to stay online. These are host-administration problems wearing an Azure costume, and they yield to host-administration fixes: free the disk, fix the clock, exclude the agent's directory from aggressive scanning. The tell is that the node's troubles track the host's condition rather than anything in the cloud, and the host's own event logs name the real cause when the portal can only say offline.

## Root cause five: a single node went down and there was no high availability

Some offline incidents are not really about why one node failed, because nodes will always fail eventually for one of the reasons above. They are about why one node failing took the entire runtime down. The answer is that the runtime had exactly one node, so that node was a single point of failure, and the moment it went offline the runtime had nothing to fall back on. This is less a root cause than a design gap, and the fix is architectural: give the runtime more than one node so a single failure degrades capacity rather than ending availability.

### How do multiple IR nodes provide high availability?

Multiple nodes provide high availability because a self-hosted runtime can register up to four nodes against the same authentication key, and any healthy node can serve activities. If one node goes offline, the surviving nodes keep the runtime Running, so a single host failure becomes a capacity reduction instead of a full outage. The nodes should sit on separate machines so one host's failure cannot take more than one node.

The mechanism is straightforward once you have seen it. You install the agent on a second machine, and instead of generating a new runtime, you register that second node against the existing runtime using the same authentication key the first node used. The cloud now sees two nodes bound to one runtime, and it distributes activities across the healthy ones. When a node goes offline, whether from a stopped service, a connectivity blip on that host, or a reboot, the runtime stays Running on the survivors and the only effect a pipeline sees is reduced concurrency, not failure. You can scale this to four nodes for both resilience and throughput, and the canonical guidance is that each node belongs on a distinct physical or virtual machine, because two nodes on one host share that host's fate and provide no protection against the most common failure, which is the host itself going down.

```cmd
:: On the second (and third, fourth) machine, register the node with the SAME key
:: that the first node used. This binds it to the existing runtime for HA.
dmgcmd.exe -RegisterNewNode "<the-same-auth-key-the-first-node-used>"
```

The corollary for diagnosis is that a single-node runtime turns every node-level incident into a full outage, which inflates the apparent severity of routine failures. If your runtime goes Unavailable every time you patch the host, the underlying cause is whatever stopped the node, but the reason a routine patch became an outage is the absence of a second node to carry the load during the reboot. Teams that add a second node find that the same node-level events keep happening, because hosts still reboot and services still occasionally stop, but those events stop being incidents, because the runtime no longer goes dark when one node blinks. High availability does not prevent node failures; it prevents node failures from becoming runtime failures, and that is the right goal.

There is a credential design choice that pairs with high availability and prevents a self-inflicted offline event across the fleet. When several nodes share a runtime, storing each linked service credential locally on every node means a credential change must be pushed to every node and kept in sync, and a node that misses the sync can fail. Sourcing credentials from a managed secret store instead lets every node fetch the current credential directly, which removes the per-node sync problem entirely. The same Synapse pipeline engine that shares this runtime model benefits from the identical pattern, and the [Azure Synapse Analytics explainer](/2022/04/25/azure-synapse-analytics-explained/) walks through where the shared runtime sits in that service, because a self-hosted IR registered for Synapse goes offline for exactly the reasons covered here and recovers the same way.

## Root cause six: the host machine rebooted or went offline entirely

The plainest cause of all is that the host is simply not there. A virtual machine was deallocated to save cost, a physical server lost power, a maintenance reboot took the host down and the service did not auto-start, or a network change cut the host off from the network entirely. When the host is gone, the agent cannot run, the heartbeat cannot leave, and the runtime is offline for the most literal possible reason. This sounds too obvious to list, but it is a real and frequent cause precisely because it is easy to overlook while you are busy testing connectivity and checking keys on a host you have assumed is up.

The confirming check is to verify the host is actually reachable and running before you investigate anything on it. If you cannot remote in, if a ping or a connection attempt to the host fails, or if your virtualization platform shows the machine stopped or deallocated, then the host is your problem and nothing about Azure, the runtime, or the network is relevant yet. Bring the host back first. Start the virtual machine, restore power, or reconnect the network, and only then proceed to confirm the service started and the node re-registered its heartbeat.

The durable fix combines two habits. First, set the agent's service to start automatically, with delayed start on busy hosts, so any reboot, planned or not, brings the node back without human intervention; a host that comes back but whose service stays down is functionally still offline. Second, treat the host like the production dependency it is, which means it should not be on a cost-saving auto-shutdown schedule, it should be monitored so you learn it went down from your alerting rather than from a failed pipeline, and in a high-availability runtime it should have a sibling node on a separate host so its absence is survivable. A self-hosted IR host that is treated as a disposable utility machine will keep producing offline events; a host that is treated as a production component stops surprising you.

## What do the host event logs tell you about why the node went quiet?

The portal can only report that the heartbeat stopped; the host can tell you why, and the place it tells you is the Windows event log. When a node goes offline and the cause is not immediately obvious from the service state or a connectivity test, the event log on the host is the next read, because the agent writes its own operational and connection events there, and those entries name the failure in a way the cloud status never can. Learning to read these logs is what separates an engineer who recovers in minutes from one who guesses for an hour, because the log distinguishes a service crash from a connectivity drop from a registration rejection at the moment each occurred.

The agent records its activity under a dedicated event source on the host, alongside the standard Windows System and Application logs. The System log carries the service lifecycle events, which is where you confirm a stopped, crashed, or restarted service and the exact time it happened. The agent's own operational log carries the connection events, which is where you see the heartbeat establishing, the relay connecting, an authentication being accepted or refused, and a connection dropping. Reading these two together reconstructs the timeline: a service that crashed will show a System-log termination followed by a restart attempt, while a healthy service that lost connectivity will show no service event at all but a connection-drop entry in the agent's operational log at the moment the heartbeat stopped. That single distinction, a service event versus a connection event, tells you instantly whether you are chasing the service cause or the connectivity cause.

```powershell
# Pull recent agent service lifecycle events from the System log
Get-WinEvent -FilterHashtable @{ LogName = 'System'; ProviderName = 'Service Control Manager' } -MaxEvents 50 |
  Where-Object { $_.Message -match 'Integration Runtime' } |
  Select-Object TimeCreated, Id, LevelDisplayName, Message |
  Format-Table -Wrap

# Pull recent agent connection events from the Application log
Get-WinEvent -FilterHashtable @{ LogName = 'Application' } -MaxEvents 200 |
  Where-Object { $_.ProviderName -match 'Integration Runtime' -or $_.Message -match 'Integration Runtime' } |
  Select-Object TimeCreated, Id, LevelDisplayName, Message |
  Format-Table -Wrap
```

The specific entries you look for map cleanly to the root cause families. A repeated service termination clustered around heavy pipeline runs confirms the undersized-host variant of the service cause, where load is killing the agent rather than a network fault taking it offline. A connection entry that names a refused authentication confirms the registration cause, telling you the key is wrong or invalidated before you waste time on the firewall. A connection entry that names a failure reaching the relay endpoint confirms the connectivity cause and even narrows it, distinguishing a name that would not resolve, which points at DNS, from a connection that was refused, which points at the firewall or proxy. An entry that records an auto-update applying, immediately followed by a failure to restart cleanly, confirms the version cause and ties the offline event to the update rather than to anything you did.

Correlating timestamps across these logs is the discipline that resolves the ambiguous cases. When a runtime flaps, going offline and online repeatedly, the event timeline tells you whether the flap follows your pipeline schedule, which indicates load or capacity, or follows the auto-update window, which indicates a version problem, or follows nothing predictable, which points at an unstable network path or a failing host component. The cloud status shows you the flapping; only the host logs show you the rhythm behind it, and the rhythm is the diagnosis. An engineer who reads the host logs first, rather than treating them as a last resort, almost never recreates a runtime by mistake, because the log says plainly which of the six causes is in play before any destructive action becomes tempting.

## How do the nodes share work, and what limits throughput across them?

High availability and throughput are two faces of the same multi-node design, and understanding how work is distributed across nodes clears up a set of offline-adjacent confusions where pipelines slow or queue rather than fail outright. When a bridge has more than one node, the cloud distributes activities across the healthy ones, and each node runs activities up to a configured concurrency limit that reflects how much that host can handle. A node that is online but saturated will queue new work rather than refuse it, and a runtime where every node is saturated will show Running while pipelines wait, which is a capacity symptom that looks nothing like an offline event but is sometimes mistaken for one because the practical effect, work not getting done, feels similar.

The concurrent jobs limit is the lever that governs how many activities a single node runs at once, and it is set per node according to the host's cores and memory. Setting it too high on an undersized host is a direct path to the flapping service failure described earlier, because the host accepts more concurrent work than it can hold and the agent is reclaimed under pressure, which presents as an offline event even though the underlying problem is over-subscription. Setting it conservatively, in line with the host's real capacity, keeps each node stable, and adding nodes rather than cranking the per-node limit is the safer way to grow throughput, because each new node brings its own host resources rather than asking one host to do more than it can. The relationship between capacity and stability is therefore direct: a node that is asked to do only what its host can sustain stays online, while a node pushed past its host's limits joins the offline statistics.

There is a coordination role worth naming because it occasionally surfaces in diagnosis. Among the registered nodes, the cloud designates one to coordinate certain dispatch responsibilities, and the others act as workers that execute activities. In normal operation this is invisible, but when the coordinating node fails, the runtime promotes another to take its place, and the brief reshuffle can produce a momentary status wobble that resolves on its own. Recognizing this prevents an overreaction to a transient blip during a node failure in a multi-node bridge: the survivors reorganize, one of them takes up coordination, and the runtime stabilizes without intervention. The takeaway for throughput is that nodes are not merely redundant copies; they are a pool whose aggregate capacity grows with each member and whose resilience comes from any member being able to carry the load when another drops, which is exactly why distributing work across several modest hosts beats concentrating it on one large host that remains a single point of failure no matter how powerful it is.

Sizing the pool, then, is a balance between resilience and throughput that you tune from observed load rather than guessed at. Watch how often nodes saturate and queue, watch how the host metrics track your heaviest pipelines, and add nodes when saturation becomes routine rather than raising per-node concurrency past what the hosts can hold. A pool sized to its real workload, spread across separate hosts, with per-node concurrency matched to each host's capacity, is a pool that neither queues work it should be running nor goes offline under the load it accepted. That is the steady state the whole design is reaching for, and it is the opposite of the fragile single large host that runs fine until the one day it does not.

## How do I prevent the runtime from going offline again?

Prevention follows directly from the six causes, because each cause has a corresponding habit that removes it. The point of prevention here is not a generic best-practice lecture; it is a short list of concrete settings and design choices, each of which closes one of the failure families above so it cannot recur.

Start with the service, because it is the leading cause. Set the agent's Windows service to start automatically on every host, and prefer delayed automatic start on hosts that do heavy work at boot, so a reboot can never strand the node. This one setting eliminates the most common offline pattern, the runtime that fails every patch cycle, at zero ongoing cost. Pair it with right-sizing the host so the service is never killed under load, because a service that crashes under copy pressure produces the same offline status as a service that was never started, and no amount of restarting fixes an undersized host.

Next, lock down connectivity deliberately rather than discovering it during an incident. Document the outbound endpoints the agent needs, primarily 443 to the control plane and to Azure Relay on the service bus domain, create explicit firewall and proxy allow rules for them, and verify the endpoint list against the current official documentation on a periodic cadence because Azure revises it. Configure the proxy explicitly in the agent if the host uses one, so relay traffic is never silently dropped. Confirm DNS resolves the service bus domain from the host, since a name that will not resolve is a connection that cannot start. Doing this work proactively means a network change that would have caused an outage instead fails your pre-change connectivity test and gets caught before it ships.

For registration, treat key rotation as a coordinated operation rather than a single portal click. When you regenerate a key, plan to re-register every node against the new key in the same change, so you never leave a node holding an invalidated credential. Keep an inventory of which nodes belong to which runtime so a node is never accidentally bound to the wrong one. For version health, set the auto-update window to a time that cannot collide with critical pipeline runs, keep multi-node runtimes on a uniform version, and watch the node pane for version skew. For availability, the single highest-leverage prevention is to register at least two nodes on separate machines using the same key, which converts every node-level failure from an outage into a capacity dip. And for the host itself, monitor it as a production dependency and keep it off any auto-shutdown schedule, so it is never deallocated out from under a pipeline.

Run all of this as code where you can, so the prevention is reproducible rather than tribal. The runtime, its nodes, the firewall rules, and the auto-update settings can all be expressed in your infrastructure-as-code of choice, which means a rebuilt host comes back with the correct service startup type, the correct proxy configuration, and the correct registration without anyone remembering the steps. The companion labs are the place to rehearse the whole prevention checklist end to end; you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.net/tools/azure-labs.html) to script a two-node runtime with automatic service start and documented endpoints, and the troubleshooting drills let you verify that your prevention actually holds by trying to take the runtime offline the six ways above and watching it shrug each one off.

## How do I reproduce the offline failure safely so I can rehearse the fix?

The fastest way to internalize the recovery is to cause each failure on purpose in a place where nothing depends on it, then bring the bridge back. A reproducible exercise turns the diagnosis from something you read into something your hands already know, so the next real incident is a repetition rather than a discovery. Stand up a throwaway factory, register one agent on a sandbox host, and walk the failure families one at a time, observing the portal status and the host's own view at each step. The exercise is short, and the payoff is that you stop reasoning from first principles under pressure and start executing a sequence you have already performed.

Begin with the cheapest failure, the stopped service. Stop the agent's Windows service on the sandbox host and watch the portal: within a heartbeat interval the single-node runtime flips to Unavailable and the node shows Inactive. Note that nothing in the cloud changed and no pipeline edit occurred; the silence alone produced the red status. Now start the service and watch the green return. You have just witnessed, in under two minutes, the most common incident you will ever face and its complete resolution, and you have proven to yourself that the portal status is purely a reflection of the heartbeat.

```powershell
# Reproduce the stopped-service failure on a sandbox host, then recover
Stop-Service  -Name "DIAHostService"     # portal goes Unavailable shortly after
Start-Sleep   -Seconds 90                 # wait one heartbeat cycle
Start-Service -Name "DIAHostService"      # portal returns to Running
Get-Service   -Name "DIAHostService" | Select-Object Status, StartType
```

Next, reproduce the connectivity block without touching the agent at all, which proves that a perfectly healthy agent goes silent the instant the path closes. Add a temporary outbound deny rule on the host's local firewall for port 443 to the service bus domain, or block the endpoints at a test network boundary, and the heartbeat stops landing even though the service stays Running. The diagnostic tool's connectivity check will now fail with a specific endpoint error rather than a refused service, which is precisely the signal you want to recognize in production. Remove the deny rule and the path reopens, the heartbeat resumes on its own, and the bridge comes back green without any restart. The lesson lands hard when you see it: the agent was trying the whole time, and only the path was missing.

The registration failure is just as instructive to stage. Regenerate the authentication key in the sandbox factory and do nothing else, and the agent that still holds the old key goes offline the moment its session ends, because the credential it presents is now refused. Then fetch the current key, re-register the node against it, and watch the bind succeed and the heartbeat resume. Doing this once removes the temptation to rebuild the bridge when a key rotation strands a node, because you have already felt how cleanly the regenerate-and-re-register sequence solves it. Finish by staging the single-node fragility lesson: with one node registered, stop its service and confirm a full outage; add a second node on a separate sandbox host with the same key, stop one node again, and confirm the bridge stays green on the survivor. That single before-and-after, an outage becoming a non-event once a second node exists, is the most persuasive argument for high availability you will ever make to a skeptical team, and it costs ten minutes to demonstrate.

## How do I detect the runtime going offline before a pipeline fails?

The worst way to learn that the bridge is down is from a failed pipeline at the end of a long run, because by then the data is late and the failure has already propagated. Detection should run ahead of consumption, so an alert fires the moment the heartbeat stops rather than hours later when a copy activity finally tries to use the dead agent. The signal you watch is the agent's status itself, surfaced through the platform's own telemetry, and you wire an alert to the transition from healthy to unhealthy so a human or an automation hears about it immediately.

### How do I alert on a self-hosted IR that has gone offline?

Route the agent's status and node telemetry to a Log Analytics workspace through a diagnostic setting, then write an alert rule that fires when a node's reported status leaves the healthy state or when the expected heartbeat stops arriving. The alert reaches you in minutes, well before a scheduled pipeline tries the dead agent, so you recover during the quiet window instead of during the incident.

The mechanism rests on the same observability plumbing every Azure resource uses: a diagnostic setting routes the resource's logs and metrics to a workspace, and once the telemetry lands there you query it and alert on it. For the self-hosted bridge, the telemetry of interest is the per-node status and the connection events that mark a transition, and a query that watches for the unhealthy transition becomes the trigger for an alert rule. The query below is illustrative of the shape; the exact table and column names depend on the schema your diagnostic setting emits, which you confirm in your own workspace, but the pattern is to filter the runtime's telemetry to status-change events and surface any that land on an unhealthy value.

```kusto
// Illustrative: watch for a self-hosted IR node leaving the healthy state.
// Confirm table and column names against your own diagnostic-setting schema.
ADFSSISIntegrationRuntimeLogs
| where TimeGenerated > ago(15m)
| where Status in ("Offline", "Inactive", "Unavailable")
| summarize LastSeen = max(TimeGenerated) by IntegrationRuntimeName, NodeName, Status
| order by LastSeen desc
```

A second, more robust signal is the absence of an expected heartbeat rather than the presence of an explicit offline event, because a host that drops off the network ungracefully may never emit a clean offline log; it simply stops emitting anything. An alert built on absence watches for a node that was reporting and then went quiet for longer than a couple of heartbeat intervals, which catches the ungraceful failures that an event-based alert misses. You express this as a query that finds nodes with no telemetry in a recent window despite having reported earlier, and you alert when the count of silent-but-expected nodes rises above zero.

```kusto
// Illustrative absence detection: a node that reported earlier but is now silent.
let lookback = 1h;
let staleAfter = 10m;
ADFSSISIntegrationRuntimeLogs
| where TimeGenerated > ago(lookback)
| summarize LastBeat = max(TimeGenerated) by NodeName, IntegrationRuntimeName
| where LastBeat < ago(staleAfter)
```

This detection layer is what turns the whole article's diagnosis into a calm, scheduled activity rather than a fire drill. The same routing and querying model underpins observability across the platform, and the broader treatment of routing diagnostics and writing alert queries lives in the work on platform monitoring; here the point is narrower and sharper, which is that the agent's status is a first-class signal you should be watching, because the cost of wiring the alert is trivial and the cost of learning about an outage from a failed overnight pipeline is not. Detection ahead of consumption converts most offline incidents into a quick service start during business hours, which is exactly the outcome the node-and-connectivity rule is designed to produce.

## How do I express the host and runtime as repeatable infrastructure?

A bridge that is configured by hand will eventually be misconfigured by hand, and the misconfiguration will surface as an offline event nobody can explain. The durable cure for the whole class of host-level causes is to express the host, the service settings, the registration, and the network rules as code, so a rebuilt or replaced host returns with the correct automatic service startup, the correct proxy configuration, and the correct endpoints allowed, without anyone reconstructing the steps from memory. The cloud-side definition is the easy part; the host-side configuration is where reproducibility pays off most, because it is the host that goes offline.

On the cloud side, the bridge definition itself is a small, declarative resource that you author once and apply consistently across environments. Expressing it as code means the definition, its type, and its description are version controlled and identical between your development, staging, and production factories, which removes the drift where one environment's bridge behaves differently from another's for reasons no one recorded.

```bicep
// Declarative definition of the self-hosted bridge in a factory (Bicep).
resource factory 'Microsoft.DataFactory/factories@2018-06-01' existing = {
  name: 'adf-prod'
}

resource selfHostedIr 'Microsoft.DataFactory/factories/integrationRuntimes@2018-06-01' = {
  parent: factory
  name: 'shir-onprem'
  properties: {
    type: 'SelfHosted'
    description: 'On-premises bridge for the warehouse network. HA: two nodes.'
  }
}
```

The host side carries the settings that actually prevent offline events, and you encode them with a configuration-management approach so every host that ever runs the agent is identical. The two settings that matter most are the service startup type, which must be automatic so a reboot never strands the node, and the proxy configuration, which must be explicit when the host routes through a proxy so relay traffic is never silently dropped. A short provisioning script captures both, along with the registration step, so a fresh host joins the bridge correctly the first time and every time.

```powershell
# Host provisioning: make the service durable and register against the current key.
# Run after the agent MSI is installed.
Set-Service  -Name "DIAHostService" -StartupType Automatic
Start-Service -Name "DIAHostService"

# Register this host against the existing bridge using the current key,
# so it joins for high availability rather than creating a new bridge.
$installDir = "C:\Program Files\Microsoft Integration Runtime\5.0\Shared"
& "$installDir\dmgcmd.exe" -RegisterNewNode "$env:SHIR_AUTH_KEY"

# Verify the result
Get-Service -Name "DIAHostService" | Select-Object Status, StartType
```

The benefit of this discipline is concrete and shows up exactly when you need it. When a host dies and you replace it, the replacement does not require an engineer to remember that the service must be automatic, that the proxy must be set, and that the node registers with the shared key for high availability. The code remembers, the replacement comes up correctly, and the bridge gains back its capacity without a manual checklist that someone will eventually perform incorrectly at two in the morning. Reproducibility does not prevent hosts from failing; it ensures that recovering from a host failure is a deterministic, fast, and correct operation rather than an improvised one, which is the same philosophy that runs through every reliability practice in the series.

## How does a proxy or private network change the connectivity picture?

The connectivity cause acquires extra teeth in locked-down environments, where the host does not reach the internet directly and where the factory may be fronted by a private endpoint. These setups are common in security-conscious organizations, and they introduce two routing subtleties that produce a node which registers briefly and then drifts offline, a pattern that confuses engineers because the install seemed to work. Understanding the two flows the agent maintains, and where each must go, resolves the confusion.

The agent maintains a command and relay flow to Azure Relay over the service bus domain, and this flow is genuinely outbound to the public Azure endpoints. When the host sits behind a corporate proxy, this relay traffic must be directed through the proxy, because it is leaving for the internet, and the agent does not always inherit the system proxy automatically. You set the proxy explicitly, either choosing the system proxy in the Configuration Manager or specifying a custom proxy address and, where required, credentials, so the relay traffic reaches the proxy and then Azure rather than failing to leave the host. A node that comes up during install, when an interactive session may use a different path, and then goes offline once it relies on the unconfigured relay path, is the classic signature of a missing proxy configuration, and the fix is to make the proxy setting explicit and restart the service.

The second subtlety appears when the factory is fronted by a private endpoint, which the deep treatment of private connectivity covers in full, and the interaction with the agent is specific. Traffic intended for the factory's control plane must now stay on the private path and resolve to the private endpoint's address, while the relay traffic for the agent's command channel still goes outbound to the public service bus domain, possibly through the proxy. These two flows must be split: the private-endpoint traffic must not be sent to the proxy, and the relay traffic must not be forced onto the private path. Misrouting either one produces a node that cannot maintain its heartbeat, and because the symptom is an intermittent offline status rather than a clean failure, it is easy to chase the wrong layer for an hour. The discipline that resolves it is to know which Azure name belongs on the public relay path and which belongs on the private path, and to configure proxy exclusions and DNS so each name travels its correct route.

DNS sits underneath both subtleties, because a name that resolves wrong sends traffic down the wrong path regardless of how the firewall and proxy are set. When a private endpoint is introduced, the factory's name should resolve to the private address from the host, and if it instead resolves to the public address the agent will try the public path for traffic that should have stayed private, with predictable failure. Confirming resolution from the host, and ensuring the private DNS integration returns the private address where it should, is therefore part of diagnosing a connectivity-caused offline event in these environments, and it is the same resolution discipline that recurs throughout the networking work in this series. In the simplest deployments none of this applies and a single outbound 443 rule is the whole story; in the locked-down ones, the proxy split and the DNS routing are where the genuinely hard offline incidents hide.

## Which failures get confused with a self-hosted integration runtime offline?

Several distinct problems present with symptoms close enough to an offline runtime that engineers chase the wrong cause, and naming them saves the misdiagnosis. The most common confusion is between a runtime that is genuinely offline and a runtime that is online but failing specific copies because a data-path port or a source credential is blocked. In that case the runtime shows Running, the heartbeat is fine, and only certain activities fail, which means the fault is in the pipeline or the linked service, not the runtime; you would diagnose it as a pipeline failure rather than a runtime outage. The clean discriminator is the runtime status itself: offline runtime means no node is answering, while a Running runtime with failing activities means the node is answering but the work is failing for its own reasons.

A second confusion is between the relay path and the data path. A partial connectivity block that allows the heartbeat on 443 but blocks interactive authoring, or blocks a data-source port like 1433, produces a runtime that looks healthy in the overview but fails every connection test and certain copies. Engineers read the green status, conclude the runtime is fine, and then cannot explain why nothing works. The resolution is to test the relay path and the data path separately, because they can fail independently, and the runtime status only reflects the heartbeat path.

A third confusion is between a runtime problem and a name-resolution problem, which is why DNS sits adjacent to this whole topic. When the host cannot resolve the endpoints it needs, the failure looks like a blocked port or a dead runtime, but the cure is in resolution, not in the runtime or the firewall. The same applies when a private endpoint changes how a name resolves and the agent is suddenly sent down the wrong path. Treating resolution as a first-class suspect, rather than assuming the network path is the only variable, prevents a long detour. And finally, a single-node runtime's full outage gets confused with a catastrophic failure when it is really an ordinary node blip amplified by the lack of a second node; the fix is not heroic recovery but a second node, after which the same blip is invisible.

## The verdict on a self-hosted integration runtime offline

The discipline that resolves this failure fast is a refusal to recreate the runtime and an insistence on restoring the node. A self-hosted integration runtime offline status is a missing heartbeat, and a missing heartbeat is produced on the host or the network path between the host and Azure, never in the cloud definition you are tempted to delete. The node-and-connectivity rule compresses the whole diagnosis into a first move: check whether the service is running, and if it is, check whether the host can reach Azure on 443, because those two causes account for the large majority of incidents and both are fixed on the node in minutes. Registration, version, single-node fragility, and a dead host fill out the rest of the table, and not one of them is fixed by recreating the runtime; every one is fixed by acting on the node, the network, the key, the version, the second node, or the host.

Carry the InsightCrunch IR-offline table into your runbook and walk it top to bottom when the runtime goes red. Start the service and make it automatic. Test connectivity with the diagnostic tool before touching a firewall. Re-register against the current key rather than rebuilding. Control auto-update and keep versions uniform. Add a second node on a separate machine so one failure stops being an outage. Monitor the host as the production dependency it is. Do these things and the runtime stops being a source of surprise outages and becomes what it was meant to be, a quiet bridge between your private data and the cloud that keeps the heartbeat flowing.

## Frequently Asked Questions

### Q: Why is my self-hosted integration runtime showing offline when the pipeline worked yesterday?

A runtime that worked yesterday and shows offline today has lost the heartbeat from its node, and the cause is almost always a change on the host or the network path rather than anything in your pipeline. The most frequent triggers are a host that rebooted overnight for patching with the agent service set to manual start, a firewall or proxy change that now blocks the outbound connection, or a key rotation that invalidated the credential the node was using. Because pipelines and data are unchanged, you ignore the portal logic and go to the host: confirm the service is running, test outbound connectivity to Azure on port 443, and check that the node is registered with the current key. The fact that it worked yesterday is a strong hint that something on the host or the network changed in between, so look for what changed there rather than rebuilding the runtime.

### Q: Should I delete and recreate the integration runtime when it goes offline?

No, recreating the runtime is almost always the wrong move and it is the most common way teams turn a quick fix into a long one. Offline means the node stopped sending a heartbeat, and that fault lives on the host or the network, not in the runtime definition in the cloud. Recreating the runtime builds a fresh definition and hands you a new key, but it does nothing about the silent agent on your host, which will register against the new runtime and then go offline again for the same underlying reason. Worse, recreating forces you to re-point every linked service and pipeline at the new runtime, which is hours of error-prone rework. The correct sequence is to restore the node: start the service, fix connectivity, or re-register with the current key. Only consider recreating in the rare case where the runtime definition itself is corrupt, which is far less common than a stopped service or a blocked port.

### Q: What is the difference between the runtime being offline and a node being inactive?

The runtime status is an aggregate over its nodes, while a node status describes one host. A single-node runtime shows Unavailable the instant its only node goes Inactive or Offline, because the aggregate has no healthy node to report. A multi-node runtime can show Running while one node sits Inactive, because a surviving node still answers, so the aggregate stays healthy. This distinction sets your urgency. A dead node in a single-node runtime is a full outage you fix immediately, while a dead node in a multi-node runtime is a resilience event that reduces capacity but does not stop work, so you can fix it calmly. Always read both the runtime status and the node list, because the runtime status alone can hide which specific node failed and whether the runtime is actually down or merely degraded.

### Q: What outbound ports and endpoints does the self-hosted integration runtime require?

The agent requires outbound HTTPS on port 443 to the Azure control plane and to Azure Relay, reached over the service bus domain at `*.servicebus.windows.net`. All of this is outbound and agent-initiated, so you never open inbound ports or assign a public IP to the host. Interactive authoring actions such as data preview and connection testing depend specifically on the relay path, which is why a block there lets scheduled work run while every connection test fails. Data movement may need additional outbound ports depending on the source, for example 443 for cloud sources or 1433 when copying directly from a SQL source, but the runtime's own liveness rests on the 443 path to the control and relay endpoints. Always verify the precise endpoint list against the current official documentation, since Azure revises these endpoints over time, and the node pane in your runtime lists the specific endpoints your deployment needs.

### Q: How do I test connectivity from the host to Azure for the self-hosted IR?

Use the diagnostic command line tool that ships with the agent, found in the installation directory under Program Files. Its connectivity check actively opens the outbound connection the agent needs and reports either success or the specific failure, which turns a vague offline status into an actionable sentence. Run the tool's check for connectivity to the service bus, and if it fails, you have confirmed a connectivity block and know to look at the firewall, the proxy, or DNS. As a fallback when the tool is unavailable, you can probe the relay domain on port 443 with a network connection test from PowerShell, using a relay endpoint taken from your runtime's node pane. Testing connectivity before you change any firewall rule is the single best time saver in the whole diagnosis, because it tells you whether connectivity is even your problem and, if so, which layer is failing.

### Q: Does the integration runtime need inbound firewall rules or a public IP?

No, and assuming it does is a common time sink for engineers with an on-premises networking background. The agent initiates an outbound connection to Azure and the cloud never initiates an inbound connection to the host, so the host needs no public IP and no inbound firewall openings for Azure to reach it. When connectivity is the problem, it is outbound connectivity that is blocked, and the question is always whether the host can reach Azure, not whether Azure can reach the host. Some local Windows firewall configuration can matter for multi-node coordination or credential handling, but that is internal to your network, not an inbound path from the internet. Spending time opening inbound ports and chasing NAT rules is effort aimed at a path the runtime does not use, so redirect that effort to confirming the outbound path to port 443 is open.

### Q: How do I re-register a node after regenerating the authentication key?

After regenerating a key, fetch the current key from the runtime and register every affected node against it, because regenerating immediately invalidates the old key and any node still holding it will go offline. Retrieve the current keys with the Azure CLI command that lists authentication keys for the runtime, then on each host run the agent's diagnostic tool with the register-new-node action and the current key. The node will bind to the runtime and resume its heartbeat. Treat key rotation as a coordinated change that includes re-registering every node in the same operation, never as a single portal click, so you do not strand a node on an invalidated credential. In a multi-node runtime this is scriptable, and scripting it ensures every node is updated together rather than discovered to be offline one at a time over the following hours.

### Q: Why does my node show Running but pipelines still cannot find an available node?

This usually means the node is healthy but bound to a different runtime than your pipelines reference. In an organization with several runtimes, it is easy to register a node with a key belonging to the wrong runtime, after which the node comes up Running, but against a runtime your linked services do not use, so pipelines pointing at the intended runtime still find no available node. The confirming check is to compare the runtime name the node is bound to, visible in its Configuration Manager, against the runtime name the failing linked service references. When they differ, the node is online but irrelevant, and the fix is to re-register it with the key from the correct runtime. This failure is invisible if you only watch node status, because the status is green; you have to compare identities, not just states, to catch it.

### Q: Can auto-update cause the self-hosted integration runtime to go offline?

Yes, the agent's scheduled auto-update can take a node offline if an update lands badly or collides with a heavy run. During an update the node restarts its service to apply the new build, and if that window overlaps a critical pipeline or the new build regresses on your Windows version, the node can come back unhealthy or fail to return. The telltale sign is offline timestamps that line up exactly with the auto-update window shown in the runtime settings, repeating on each update cycle. The fix is to set the update window to a time that cannot collide with important runs, and to roll a node back to a known-good version when a specific build misbehaves, confirming the running version afterward in the node pane. Controlling update timing rather than disabling updates entirely keeps the node patched while removing the collision risk.

### Q: How many nodes can a self-hosted integration runtime have, and why add more than one?

A self-hosted runtime can register up to four nodes against the same authentication key, and adding more than one is the single most effective way to stop node failures from becoming outages. With one node, any failure of that node, whether a stopped service, a reboot, or a connectivity blip, takes the whole runtime down. With two or more nodes on separate machines, a single node failure only reduces concurrency while the surviving nodes keep the runtime Running. You add a node by installing the agent on a second machine and registering it with the same key the first node used, which binds it to the existing runtime rather than creating a new one. Each node should live on a distinct host, because two nodes on one machine share that machine's fate and provide no protection against the most common failure, the host itself going down.

### Q: Why does my runtime go offline every time the host is patched or rebooted?

This pattern almost always means the agent's Windows service is set to manual start, so it survives a running host but never returns after a reboot. Patch cycles reboot the host, the service does not auto-start, and the runtime goes offline like clockwork on each patch day. The fix is two settings taken together: set the service startup type to automatic, preferring delayed automatic start on busy hosts so the service does not contend for resources at boot, and in a high-availability runtime add a second node on a separate machine so the reboot of one host does not take the runtime down at all. With automatic start, the node comes back on its own after every reboot, and with a second node the reboot becomes a brief capacity dip rather than an outage. The recurring offline event disappears once the host is treated as a production dependency.

### Q: My connectivity test fails with a name resolution error. Is that the same as a blocked port?

No, a resolution error and a blocked port are different faults that look similar from the runtime status. A blocked port means the host found the endpoint's address but could not open the connection, while a resolution error means the host could not turn the endpoint name into an address at all, so the connection never even started. Both leave the runtime offline, but the cures live in different places: a blocked port is a firewall or proxy rule, while a resolution failure is a DNS problem, often a missing or wrong record, a private endpoint that changed how a name resolves, or a host pointed at a resolver that cannot answer for the Azure domain. When your connectivity test reports a resolution failure rather than a refused connection, stop looking at the firewall and start looking at name resolution, because no firewall change will help a name the host cannot resolve.

### Q: Where are credentials stored for a self-hosted IR, and does it affect multi-node setups?

Linked service credentials used by a self-hosted runtime can be stored locally on each node, encrypted on the host, or sourced from a managed secret store. The choice matters most in a multi-node runtime. Storing credentials locally means a credential change must be pushed to and kept in sync across every node, and a node that misses the sync can fail, which is a self-inflicted path to an offline or failing node. Sourcing credentials from a managed secret store instead lets every node fetch the current credential directly, removing the per-node sync problem entirely and avoiding the drift that takes nodes out of service. For any runtime with more than one node, the managed secret store approach is the more robust choice precisely because it eliminates a whole class of credential-sync failures that would otherwise present as mysterious node problems.

### Q: How do I confirm the integration runtime node status without using the portal?

The host carries its own authoritative view, which you read in three places. The Microsoft Integration Runtime Configuration Manager, the desktop application installed with the agent, shows the node's self-reported connection status to the cloud and is the fastest read on whether the node believes it is connected. A PowerShell service query against the agent's service tells you whether the underlying service is even running and what its startup type is. The diagnostic command line tool actively tests connectivity rather than reporting a cached status, so it can prove whether the outbound path to Azure is open right now. Reading the host's own view, rather than the cloud's view of the host, is what makes diagnosis fast, because the portal can only show you the consequence of a missing heartbeat while the host can show you the cause.

### Q: Does the self-hosted integration runtime work the same way in Synapse as in Data Factory?

Yes, the pipeline engine inside Synapse shares the same runtime model, so a self-hosted runtime registered for Synapse goes offline for the same reasons and recovers the same way as one registered for Data Factory. The node still runs as a Windows service on a host you control, still depends on outbound 443 to the control plane and Azure Relay, still binds to its runtime with an authentication key, and still gains high availability from multiple nodes on separate machines. The node-and-connectivity rule applies identically: offline means the service stopped or connectivity is blocked far more often than anything else, and the fix is to restore the node rather than recreate the runtime. The diagnostic tool, the service checks, and the re-registration steps are the same, so a runbook written for one service serves the other without modification.

### Q: Can a host that is too small cause the runtime to keep going offline?

Yes, an undersized host produces a flapping pattern that is easy to misread as a flaky network. The service starts, runs for a while, consumes memory under copy load, and is then killed or wedged when the host runs out of headroom, after which it restarts and the cycle repeats. The portal shows an intermittent status that looks like a connectivity problem, but the host's service event log tells the real story, with crash and restart entries clustered around your heaviest pipeline runs. No amount of restarting fixes this, because the next heavy activity tips the host over again. The fix is capacity: move the agent to a host with enough cores and memory for the concurrent copies you run, or distribute the load across additional nodes so no single host carries the full weight. When offline events track your busiest pipelines, suspect the host before you suspect the network.

### Q: How do I make recovery from an offline runtime automatic rather than manual?

Recovery becomes automatic when you remove the human step from each failure family. Set the agent service to automatic start, preferring delayed automatic start on busy hosts, so any reboot brings the node back without intervention, which alone handles the most common offline cause. Add a second node on a separate machine using the same key so a single node failure never takes the runtime down and there is nothing to recover in the moment. Source credentials from a managed secret store so a credential change cannot strand a node. Control the auto-update window so updates never collide with critical runs. Express the host, the runtime, the nodes, the firewall rules, and these settings as infrastructure-as-code so a rebuilt host returns correctly configured without anyone remembering the steps. The combined effect is a runtime where the routine failures still occur but no longer require a person to notice and react, because each one self-heals or is absorbed by a surviving node.

### Q: What should I check first when a self-hosted integration runtime is unavailable?

Check the agent's Windows service on the host first, because a stopped service is the single most common cause and the cheapest to confirm. A quick PowerShell service query tells you whether the service is running and whether its startup type would survive a reboot. If the service is stopped, start it, set it to automatic, and watch the node return to Running. If the service is already running, your problem is connectivity, so run the diagnostic tool's connectivity check next to see whether the host can reach Azure on port 443. Those two checks, in that order, resolve the large majority of offline incidents within minutes and steer you away from the destructive instinct to recreate the runtime. Only after both the service and connectivity check out clean do you move on to registration, version, and host-level causes, working down the IR-offline table until the cause that survives its confirming check reveals itself.

### Q: Can I install the self-hosted IR on a machine that already runs another gateway?

Sharing a host with another gateway is risky and a frequent source of avoidable offline events, because the two components can contend for the same resource. The most cited conflict is with the Power BI on-premises gateway, which leans heavily on the same port the self-hosted agent uses for its outbound connection, and co-locating them on one host invites a port contention that destabilizes one or both. Beyond the port, two resource-hungry agents on one machine compete for cores and memory, which can tip an otherwise adequate host into the over-subscription pattern where the agent is reclaimed under load and the bridge flaps. The safer design is a dedicated host for the self-hosted agent, sized for its own concurrency, so nothing else on the machine can starve it or collide with its connection. If a dedicated host is genuinely impossible, you must verify that the resource and port demands of every component on the machine fit together, which is more fragile than simply giving the agent its own home.

### Q: If I move the agent to a new host, do I have to recreate the runtime?

No, moving to a new host does not require recreating the bridge, and recreating it would force needless rework on every linked service. The bridge definition in the cloud and its authentication key are independent of any particular host, so you install the agent on the new machine and register it against the existing bridge using the current key, exactly as you would when adding a node for high availability. To migrate rather than expand, you register the new host and then retire the old one from the node list once the new one is healthy, and the bridge keeps the same name and the same key throughout, so nothing your pipelines reference changes. This is also how you replace a failed host: provision the replacement, register it with the shared key, confirm it reaches Running, and remove the dead node. The identity that matters lives in the cloud definition and the key, never in the host, which is why hosts are replaceable without touching the bridge.
