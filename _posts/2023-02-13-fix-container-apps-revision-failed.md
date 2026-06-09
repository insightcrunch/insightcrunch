---
layout: post
title: "Fix Container Apps Revision Failures"
page_title: "Fix Container Apps Revision Failed: Diagnose Why a Revision Will Not Provision or Take Traffic and Repair the Image Pull, Probe, Target Port, or Secret Cause"
date: 2023-02-13
categories: ["Technology"]
tags: ["Azure", "Container Apps", "Troubleshooting", "Containers", "DevOps", "Cloud Computing"]
excerpt: "A Container Apps revision failed and refuses traffic? Read the revision and system logs to find the pull, probe, port, or secret cause and fix it fast."
image: "/assets/images/blog/blog-16.webp"
reading_time: 59
author: "jason-mckenzie"
last_updated: 2023-02-13
lang: en
---
You push a new image to your container app, the deployment reports success, and then nothing changes. The old version keeps serving traffic, or the endpoint starts returning errors, and the portal shows your newest revision sitting in a failed or unhealthy state instead of taking over. When a Container Apps revision failed to become active, the platform is telling you something precise even when the message on screen looks generic: a revision only receives traffic after it provisions its replicas and those replicas pass health, so a revision that never activates is stuck at one of a small set of gates. The image would not pull, a probe never reported ready, the container does not listen on the target port you configured, a secret or environment variable is missing and the process crashes on start, or the resource and scale settings cannot place a replica. Each of those gates leaves a distinct fingerprint in the revision status and the logs, and the difference between a frustrating afternoon and a five minute fix is knowing which fingerprint is yours.

![Diagnosing Azure Container Apps revision failed states and the pull, probe, port, and secret root causes - Insight Crunch](/assets/images/blog/blog-16.webp)

This guide treats the failed revision as a diagnosis rather than a symptom. The central idea, the one worth carrying out of this article and into every future incident, is what I will call the pass-health-to-activate rule: a Container Apps revision takes traffic only once it provisions successfully and its replicas pass their health checks, which means a stuck or failed revision is always a pull, a probe, a port, or a configuration problem that the logs will name if you read them in the right order. Redeploying the same image into the same broken configuration cannot fix any of those, which is why the most common mistake is also the least productive: pushing the build again and hoping the platform behaves differently the second time. It will not. The revision failed for a reason, the reason is recorded, and your job is to surface it and match it to the fix.

Azure Container Apps is the managed serverless container platform that runs your image on top of Kubernetes and the Kubernetes Event Driven Autoscaler without asking you to operate a cluster. It abstracts the nodes, the scheduler, the ingress controller, and the scaler, and in exchange it expresses your application as a sequence of revisions. Understanding the revision is the whole game here, because the failure modes you will chase are all failures of a revision to provision or to pass health. We will build the mental model of how a revision provisions and why it gates on health, then read the exact signals the platform exposes, then walk every distinct root cause with the command that confirms it is yours and the fix that resolves it, and finally cover prevention and the neighboring failures that get mistaken for this one.

## What a Container Apps revision actually is and why it gates on health

A revision in Azure Container Apps is an immutable snapshot of a specific version of your container app: a particular image, a particular set of environment variables and secret references, a particular ingress and scale and resource configuration, frozen together and given a name. You do not edit a revision. When you change the image tag or any property that affects the running container, the platform mints a new revision with a new name, provisions it, and, depending on your revision mode, shifts traffic to it. The old revision continues to exist, which is what makes rollback in Container Apps a matter of pointing traffic back rather than redeploying anything. This immutability is the reason a failed revision is so diagnosable: the exact configuration that failed is preserved and inspectable, not overwritten by your next attempt.

Two revision modes shape how a new revision behaves once it provisions. In single revision mode, which is the default, the platform keeps exactly one active revision and automatically routes all traffic to the latest revision once it is healthy, deactivating the previous one. In multiple revision mode, several revisions can be active at once and you control the traffic split with weights, which is how blue green and canary rollouts work on the platform. The mode matters for diagnosis because of what happens on failure. In single revision mode, if the new revision never becomes healthy, the platform holds traffic on the previous healthy revision, so your application keeps serving the old version and the symptom is "my changes did not take effect" rather than an outage. In multiple revision mode with the new revision weighted to receive traffic, a failure to provision can take down the share of traffic you routed to it. Knowing the mode tells you whether a failed revision is a silent non event or an active incident.

### How does a revision provision before it takes traffic?

A revision provisions by pulling its image from the registry, scheduling one or more replicas onto the underlying compute, starting the container in each replica, and then waiting for the replica to report healthy through its probes before marking the revision provisioned and eligible for traffic. Only after that health gate passes does the platform route requests to it. Any failure along that path leaves the revision in a failed or unhealthy state.

Walk that sequence slowly, because every root cause lives at one of its steps. First the platform resolves and pulls the image referenced by the revision. If the registry rejects the credentials, or the image and tag do not exist, or the registry is unreachable, the pull fails and the replica never starts; the revision cannot provision because there is no container to run. Second, assuming the image pulls, the platform creates the replica and starts the container process. If the process exits immediately because a required secret is absent, a connection string is malformed, or an entry point is wrong, the container crashes and the platform restarts it, and a container that keeps crashing on start never reaches a healthy state. Third, once the process is running, the platform evaluates health. A startup probe, if defined, must succeed before liveness and readiness are considered; a readiness probe must succeed before the replica is added to the set that receives traffic; a liveness probe that fails causes a restart. Fourth, for an application with ingress enabled, the platform must be able to reach the container on the target port you configured, because that is where it sends both health traffic and real requests; if the container listens on a different port, the platform finds nothing there and the replica never becomes ready. The revision activates only when a sufficient replica passes all of this. The pass-health-to-activate rule is simply the name for that gate.

### What does a healthy revision look like versus a failed one?

A healthy revision shows a provisioning state of Provisioned and a running state of Running, with at least one replica reporting ready, and in single revision mode it holds the full traffic weight. A failed revision shows a provisioning state of Failed or stays in Provisioning indefinitely, often with a running state of Degraded or Failed, zero ready replicas, and a traffic weight that never moved off the previous revision.

The portal surfaces this in the Revision management blade, where each revision lists its name, its active or inactive status, its provisioning and running state, the replica count, the traffic percentage, and the creation timestamp. A revision you expected to take over that shows zero traffic and a Failed state is the headline of your incident. The detail that matters next is why, and the why is never in that summary view; it is in the system logs and the console logs, which we will read in a moment. The summary tells you that a revision failed and roughly where it stalled, in provisioning or in health, but the precise cause comes from the log signal, and reading that signal in the right order is the difference between guessing and diagnosing.

### Why does my old version keep serving after I deployed a new one?

Because in single revision mode the platform refuses to shift traffic to a revision that has not passed health, so when your new revision fails to provision or fails its probes, traffic stays on the last revision that was healthy. The deployment command can still report success because it accepted the configuration; success there means the revision was created, not that it became active.

This is the single most confusing part of the platform for engineers new to it, and it is worth dwelling on because it inverts the intuition built from editing a running service in place. With a virtual machine or a classic App Service in place deploy, a broken deployment usually breaks the running app, so the failure is loud. Container Apps in single revision mode does the opposite: a broken new revision fails safely behind the healthy old one, so the failure is quiet. The endpoint still works, the old behavior persists, and the only sign that anything is wrong is the new revision sitting failed in the management blade. Engineers chase this for a long time when they assume the new code is live and debug application logic that is not even running. The first question to ask when "my change did not take effect" is not "is my code wrong" but "did my new revision actually become active," and the Revision management blade answers it in one glance.

## How to read the failure: the diagnostic signal in the right order

Before touching a single root cause you need the signal, and the signal comes from three places that you read in a fixed order: the revision status to localize the failure to provisioning or to health, the system logs to see what the platform itself observed, and the console logs to see what your container printed before it died. Reading them out of order wastes time, because the system logs often name the cause outright and make the console logs unnecessary, or vice versa.

Start with the revision list to confirm which revision failed and what state it is in. The command lists every revision with its provisioning state, running state, active status, replica count, and traffic weight, which immediately tells you whether the platform got as far as starting replicas or failed earlier at the image.

```bash
# List all revisions for the app with their state and traffic
az containerapp revision list \
  --name my-container-app \
  --resource-group my-rg \
  --output table

# Inspect one failed revision in full detail
az containerapp revision show \
  --name my-container-app \
  --resource-group my-rg \
  --revision my-container-app--abc1234 \
  --output json
```

The detailed show output carries the fields that matter for localization. The `provisioningState` tells you whether the revision provisioned at all; a value of Failed combined with zero replicas points at the image or the placement, while Provisioned with a Degraded running state and replicas that exist but never went ready points at a probe, a port, or a crash after start. The `runningState` and the replica information narrow it further. You are not trying to fix anything yet; you are deciding which family of cause to investigate, so you read the logs against the right hypothesis instead of scrolling blind.

### Where are the system logs and what do they tell you?

The system logs are the platform's own record of provisioning and lifecycle events for your revision: image pull attempts and their outcomes, replica scheduling, probe results, and restarts. They are the first log to read because they describe what Azure did and saw, which usually names the cause directly, such as a failed pull or a probe that never succeeded.

You can stream them live or query them after the fact. The streaming command attaches to the system event stream for a revision, which is ideal while you redeploy and watch the failure happen in real time.

```bash
# Stream platform/system logs for the app (provisioning, pulls, probes, restarts)
az containerapp logs show \
  --name my-container-app \
  --resource-group my-rg \
  --type system \
  --follow

# Stream the application's stdout/stderr (console) logs for a specific replica
az containerapp logs show \
  --name my-container-app \
  --resource-group my-rg \
  --type console \
  --follow
```

The `--type system` stream is where the platform announces a pull failure with the registry response, a probe that timed out or returned a non success status, a container that was killed for exceeding memory, or a replica that could not be scheduled. The `--type console` stream is your application's own output, the stack trace it printed before it exited, the message about a missing connection string, the line where it tried to bind a port and failed. Read system first to learn the platform's verdict, then read console to see the application's side of the story when the system verdict points at a crash rather than a pull or a placement.

### How do I query the logs in Log Analytics with KQL?

When your container app sends logs to a Log Analytics workspace, the system events land in the ContainerAppSystemLogs_CL table and the application output lands in the ContainerAppConsoleLogs_CL table, and you query them with KQL filtered by your revision name to see exactly what happened during the failed provisioning window.

The streaming commands are perfect in the moment, but they only show recent events and they do not let you correlate across replicas or look back at a failure that happened overnight. For that, the workspace tables are the durable record. A focused query against the system table, filtered to the failed revision and ordered by time, reconstructs the provisioning timeline.

```kusto
// System events for one failed revision, newest first
ContainerAppSystemLogs_CL
| where RevisionName_s == "my-container-app--abc1234"
| project TimeGenerated, Type_s, Reason_s, Log_s, ReplicaName_s
| order by TimeGenerated desc
| take 200
```

```kusto
// Application console output for the same failed revision
ContainerAppConsoleLogs_CL
| where RevisionName_s == "my-container-app--abc1234"
| project TimeGenerated, ContainerName_s, Log_s
| order by TimeGenerated desc
| take 200
```

The `Reason_s` column in the system table is the field to read first, because it carries the categorized cause: a pull related reason, a probe related reason, an unhealthy or killed reason. The `Log_s` column carries the human readable detail. Filtering by `RevisionName_s` keeps you focused on the one revision that failed rather than drowning in events from healthy revisions. The exact column names and table names can vary slightly across workspace configurations and environment versions, so confirm them against your own schema; the pattern, filter by revision and read the reason then the detail, holds regardless of the precise field names.

### Why should I check the replica state, not just the revision state?

Because a revision is an aggregate over its replicas, and the replica view tells you whether the platform created a replica at all, whether the container inside it started, and how many times it has restarted, which separates an image or scheduling failure from a crash loop after a successful start.

```bash
# List the replicas for a specific revision and their container state
az containerapp replica list \
  --name my-container-app \
  --resource-group my-rg \
  --revision my-container-app--abc1234 \
  --output table
```

If the replica list is empty, the platform never created a replica, which points hard at an image pull failure or a resource or quota problem that prevented scheduling, because there was no container to run. If a replica exists but its container shows repeated restarts, the image pulled and the container started but then exited, which points at a missing secret, a bad environment variable, a startup crash, or a memory kill. If a replica exists and the container is running but the revision still shows unhealthy and takes no traffic, the container is up but failing its readiness gate, which points at a probe misconfiguration or a target port mismatch. The replica view, read alongside the system reason, narrows five possible causes to one before you change anything.

## The InsightCrunch revision-failure table: every cause, its log signal, and its fix

Here is the findable artifact this article is built around, the InsightCrunch revision-failure table. It maps each distinct cause of a failed Container Apps revision to the log signal that confirms it and the fix that resolves it. Read it as the index to the sections that follow, each of which takes one row and shows the confirming command and the tested repair.

| Root cause | Where it stalls | Log signal that confirms it | Fix |
| --- | --- | --- | --- |
| Image pull failure | Provisioning, no replica | System reason names pull or unauthorized; registry response in detail; empty replica list | Grant the pull identity AcrPull, attach the registry, correct the image and tag |
| Startup or readiness probe failure | Health, replica running but not ready | System reason names an unhealthy probe; probe timeouts or non success status | Point the probe at the real path and port, widen the timing, or remove a wrong probe |
| Target port mismatch | Health, replica running but not ready | No connection on target port; readiness never passes; app logs show it binding a different port | Set the ingress target port to the port the container actually listens on |
| Missing secret or env var | Crash on start, replica restarts | Console log shows a null or missing config exception; system reason shows restarts | Create the secret, fix the secretRef name, supply the environment variable |
| Resource or scale limit | Provisioning or runtime | Invalid CPU and memory combination rejected; OOM kill in system reason; scheduling failure | Use a valid CPU and memory pair, raise memory to stop OOM, fix scale rules |
| Bad command, entry point, or architecture | Crash on start, immediate exit | Console shows exec format error or command not found; container exits nonzero at once | Fix the entry point and arguments, build the image for the correct CPU architecture |

The namable claim sits behind every row: the pass-health-to-activate rule means each of these is a gate the revision could not clear, and the gate it stalled at is recorded. The table is the map; the sections are the territory.

## Cause one: the image will not pull

The most common reason a revision fails before it ever runs a container is that the platform could not pull the image. The revision provisioning state goes to Failed, the replica list comes back empty because no container was ever created, and the system logs name a pull or authorization problem with the registry's own response embedded in the detail. This is the cause to suspect first whenever the replica count is zero, because a pull failure stops everything downstream before it can start.

There are three flavors of pull failure and they are worth separating because the fix differs. The first is authentication: the platform's pull identity does not have permission to pull from the registry. The second is existence: the image repository or the specific tag does not exist at the path the revision references, often because of a typo, a registry login server mismatch, or a tag that was never pushed. The third is reachability: the registry is behind a network restriction or a private endpoint that the Container Apps environment cannot reach. Each produces a recognizable signal.

### Why does my revision fail with an unauthorized pull from ACR?

Because the identity Container Apps uses to pull, either a managed identity or the registry's admin credentials, lacks the AcrPull role on the Azure Container Registry, so the registry returns an unauthorized response and the platform cannot fetch the image. The fix is to grant the pulling identity AcrPull on the registry and attach the registry to the app with that identity.

The modern and recommended path is a managed identity with the AcrPull role, which avoids storing registry passwords as secrets. You assign the identity, grant it AcrPull scoped to the registry, and tell the container app to use that identity for the registry. The commands below configure a user assigned managed identity for the pull, which is the cleanest pattern because the identity outlives any single revision.

```bash
# Grant the app's managed identity AcrPull on the registry
PRINCIPAL_ID=$(az containerapp show \
  --name my-container-app --resource-group my-rg \
  --query identity.principalId --output tsv)

ACR_ID=$(az acr show --name myregistry \
  --resource-group my-rg --query id --output tsv)

az role assignment create \
  --assignee "$PRINCIPAL_ID" \
  --role AcrPull \
  --scope "$ACR_ID"

# Tell the container app to use that identity for this registry
az containerapp registry set \
  --name my-container-app \
  --resource-group my-rg \
  --server myregistry.azurecr.io \
  --identity system
```

After the role assignment, create a fresh revision so the platform retries the pull with the corrected permission, because the failed revision is immutable and will not retry on its own. Role assignments can take a short while to propagate, so if the immediate retry still fails with the same unauthorized signal, wait briefly and create another revision before assuming the assignment is wrong. The pull authorization story is the same one that produces cluster side pull failures elsewhere, and if you want the full registry authentication treatment beyond the Container Apps case, the dedicated walkthrough on how to [fix an Azure Container Registry pull that returns unauthorized](/2023/02/06/fix-acr-pull-unauthorized/) goes layer by layer through identity, scope, and credential, and it applies directly here because the registry does not care whether the caller is a cluster or a container app.

### Why does the platform say the image was not found?

Because the image repository or tag referenced by the revision does not exist at the registry path the revision uses, which happens when the login server is wrong, the repository name is misspelled, the tag was never pushed, or a build pipeline tagged the image differently than the deployment expects. The fix is to confirm the exact image path and tag exist in the registry and correct the reference.

Confirm what is actually in the registry before assuming the platform is wrong. Listing the repository and its tags shows you the truth, and comparing that truth to the image string in the revision usually reveals the mismatch immediately.

```bash
# Confirm the repository and tag actually exist in the registry
az acr repository show-tags \
  --name myregistry \
  --repository my-api \
  --output table

# See exactly what image the failed revision referenced
az containerapp revision show \
  --name my-container-app --resource-group my-rg \
  --revision my-container-app--abc1234 \
  --query "properties.template.containers[].image" \
  --output tsv
```

A frequent and maddening version of this is the `latest` tag. If your pipeline pushes a new image under `latest` but the revision was created before that push completed, or the revision pins a digest that no longer matches, the platform pulls something other than what you expect or fails to find it. Pinning to an explicit, immutable tag per build rather than reusing `latest` removes a whole class of these failures, because each revision then references an image that either exists exactly or does not, with no ambiguity about which build is live. Getting the image itself correct, well formed, and pushed to the right place is its own discipline, and the guide on [containerizing applications for Azure](/2025/07/07/containerizing-apps-for-azure/) covers building, tagging, and pushing an image that will pull cleanly, which is the upstream half of this whole cause family.

### Why does a private registry behind a firewall fail to pull?

Because the Container Apps environment cannot reach a registry that is locked behind a private endpoint or a network restriction that does not permit the environment's outbound traffic, so the pull times out or is refused at the network layer rather than at authentication. The fix is to ensure network reachability between the environment and the registry, through the appropriate private networking configuration for your environment type.

This flavor is distinguishable from authentication because the registry never gets far enough to evaluate credentials; the system log shows a connection or timeout rather than an unauthorized response. The resolution depends on how your Container Apps environment is networked. An environment integrated with a virtual network needs a path to the registry, whether that is a private endpoint on the registry with DNS that resolves inside the network, or a firewall rule that admits the environment's egress. The specifics of private networking are environment dependent and change as the platform evolves, so verify the current requirements for your environment type rather than assuming a fixed rule; the durable point is that a pull which fails on connectivity rather than credentials is a network problem, and you fix it at the network layer, not by re granting roles.

## Cause two: the health probe never reports ready

Once the image pulls and the container starts, the revision still will not take traffic until a replica passes health, and the gate that most often blocks a running container is a probe that never succeeds. The revision shows a replica that exists and a container that is running, yet the running state stays Degraded and the traffic weight never moves, because the platform will not route requests to a replica it considers unready. The system log names an unhealthy probe, often with the path, the port, or the timing it tried.

Container Apps supports three probe types, and confusing them is a common source of self inflicted failures. A startup probe gates the others: until it succeeds, liveness and readiness are not evaluated, which gives a slow starting application time to come up without being killed. A readiness probe controls traffic: a replica is only added to the serving set when readiness succeeds, so a readiness probe that never passes keeps the revision out of traffic indefinitely. A liveness probe controls restarts: if it fails, the platform kills and restarts the container, so a liveness probe pointed at the wrong place causes an endless restart loop that looks like a crash but is actually the platform euthanizing a healthy container.

### Why is my container running but the revision stays unhealthy?

Because a readiness probe is failing, so the platform considers the replica not ready to serve and keeps it out of the traffic set even though the process is alive; the revision therefore never reaches a healthy active state. The fix is to point the readiness probe at a path and port the application actually answers, and to give it enough time and tolerance to pass during normal startup.

The most frequent probe mistakes are a wrong path, a wrong port, and an impatient timing. A readiness probe configured to call `/healthz` when your application exposes `/health`, or configured for port 8080 when the application listens on 3000, will fail every time because there is nothing valid at the target. An aggressive `initialDelaySeconds` or `failureThreshold` that does not allow for your real startup time fails a container that would have become ready a few seconds later. The probe definition lives in the container app template, and correcting it means updating that template so the next revision carries the right values.

```yaml
# Probe block in the containerapp template (YAML deploy)
probes:
  - type: readiness
    httpGet:
      path: /health
      port: 3000
    initialDelaySeconds: 5
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 6
  - type: startup
    httpGet:
      path: /health
      port: 3000
    initialDelaySeconds: 5
    periodSeconds: 10
    failureThreshold: 30
```

Match the probe path to a route the application genuinely serves, match the port to the port the container binds, and size the startup probe so that `initialDelaySeconds` plus `failureThreshold` times `periodSeconds` comfortably exceeds your worst case cold start. A readiness probe should test something cheap that genuinely indicates the app can serve, not a heavy dependency check that fails when a downstream service is briefly slow. Apply the corrected template to create a new revision, then watch the system stream to confirm the probe now succeeds and the replica goes ready.

### Why does my container keep restarting in a loop?

Because a liveness probe is failing repeatedly, so the platform interprets the container as unhealthy and kills it, then restarts it, and the cycle repeats; the replica shows climbing restart counts while the application itself may be perfectly capable of serving. The fix is to correct the liveness probe target or timing so it reflects real liveness rather than a wrong endpoint.

This is the probe failure that masquerades as a crash, and it is worth distinguishing carefully from an actual application crash, which we cover under the secret and command causes. In a liveness probe loop, the console logs often show the application starting normally and then being terminated mid run, with no stack trace of its own, because the container did not crash; the platform stopped it. In an actual crash, the console logs show the application's own error before it exits. If you see clean startup followed by an external termination on a rhythm that matches your probe period and threshold, the probe is the culprit. A liveness probe should be even more conservative than readiness, testing only that the process is fundamentally alive, because the cost of a false positive is a restart of a working container. When a container repeatedly cycles like this, the pattern is the same one Kubernetes surfaces as a crash loop in raw clusters, and the diagnosis discipline transfers directly; the deep treatment of how to [read the previous container logs to fix a Kubernetes CrashLoopBackOff](/2022/07/18/fix-aks-crashloopbackoff/) lays out the previous state and last termination reasoning that applies to a restarting Container Apps replica just as it does to an AKS pod.

### Do I even need to define probes?

Not always, and a wrong probe is worse than none, because the platform applies sensible default health behavior tied to your ingress target port when you do not define custom probes. If your application is straightforward and listens on the target port promptly, omitting custom probes and letting the platform check the target port can be the most reliable choice; you add probes when the default does not fit your startup or your readiness semantics.

The trap engineers fall into is copying a probe block from another service, pointing it at an endpoint this application does not serve, and turning a working default into a guaranteed failure. If your revision was healthy before you added probes and failed after, remove the probes and confirm it recovers on the default behavior, then reintroduce a correct probe only if you genuinely need one. The exact default probe behavior depends on whether ingress is enabled and on the platform version, so verify it against the current documentation for your environment; the durable guidance is to treat custom probes as a deliberate choice you make when the default does not serve your startup and readiness needs, not as a box to fill in by reflex.

## Cause three: the target port does not match what the container listens on

A revision with ingress enabled will not become healthy if the platform cannot reach the container on the configured target port, because that port is where the platform sends both its health checks and the real request traffic. The container can be running perfectly, the process can be listening, and the revision will still sit unhealthy with no traffic because the platform is knocking on the wrong door. This is one of the most common and most quietly frustrating causes, because everything looks fine inside the container while the platform reports it as unready.

The target port is a single integer in your ingress configuration, and it must equal the port your application process binds inside the container. Web frameworks default to a range of ports depending on the stack: a Node application might listen on 3000, a .NET application on 8080 or whatever you set in the host configuration, a Python application on 8000, a Go service on whatever you hard coded. If your ingress target port says 80 but the application binds 3000, the platform finds nothing on 80, readiness never passes, and the revision fails its health gate. The fix is trivial once you see it, which is exactly why reading the application's own startup log to learn which port it actually bound is the fastest path to the answer.

### How do I find which port my container actually listens on?

Read the application's console log at startup, where most frameworks announce the port they bound, and compare that to the ingress target port on the revision; a mismatch is the cause. The fix is to set the ingress target port to the port the application logs say it is listening on.

```bash
# Read the container's own startup output to see the bound port
az containerapp logs show \
  --name my-container-app --resource-group my-rg \
  --type console --revision my-container-app--abc1234 \
  --tail 50

# Check the ingress target port the revision is configured with
az containerapp show \
  --name my-container-app --resource-group my-rg \
  --query "properties.configuration.ingress.targetPort" \
  --output tsv
```

If the console log shows the application listening on 3000 and the target port query returns 80, you have found it. The correction sets the target port to match, which creates a new revision with the right ingress configuration.

```bash
# Set the ingress target port to the port the app actually binds
az containerapp ingress update \
  --name my-container-app \
  --resource-group my-rg \
  --target-port 3000
```

There is a related variant worth naming: an application that reads its listen port from an environment variable, commonly `PORT`, and a target port that disagrees with whatever that variable is set to. Container Apps may inject a port expectation, and if your application ignores it and binds a hard coded port, or if you set `PORT` to one value and the target port to another, you get the same mismatch through a different route. The reliable pattern is to have the application read its port from the environment, set that environment variable explicitly, and set the ingress target port to the identical number, so all three agree by construction rather than by luck.

### Why does a container that binds localhost fail the port check?

Because a process bound to 127.0.0.1 or localhost only accepts connections from inside the container itself, so the platform's health and traffic connections from outside the process are refused even though the port number is correct; the application must bind 0.0.0.0 to accept external connections. The fix is to configure the application to listen on all interfaces, not just loopback.

This is a subtle and common cause that survives a correct target port, because the port matches but the bind address does not. A development configuration that listens on `localhost:3000` works on a laptop, where the client and server share the loopback interface, and fails in a container, where the platform reaches the process across the container's network boundary. The application must bind `0.0.0.0:3000` so that connections arriving on the container's external interface are accepted. The fix lives in the application or its configuration, not in the platform: set the host to `0.0.0.0`, or to the framework's equivalent of all interfaces, rebuild, and deploy. If the console log shows the app listening but the platform still cannot reach it on a matching port, suspect a loopback bind before you suspect anything in Azure.

## Cause four: a missing secret or environment variable crashes the container

When the image pulls and starts but the container exits immediately and the replica shows climbing restart counts, the most common cause is that the application could not find a configuration value it needs to start: a secret that does not exist, a `secretRef` that points at the wrong name, or a plain environment variable that was never set. The application reads the value, finds it null, and throws on startup, and the platform restarts the failed container only to watch it fail the same way. The revision never becomes healthy because no replica ever survives long enough to pass readiness.

Secrets in Container Apps are defined at the application level as named key value pairs and referenced from environment variables through a `secretRef` rather than inlined, which keeps the secret value out of the revision's plain configuration. The reference is by name, and a mismatch between the secret name you defined and the name the environment variable references is silent until runtime, when the container starts, the environment variable resolves to nothing, and the application falls over. This is distinct from the probe loop because the container genuinely crashes with its own error, which the console log records.

### Why does my container crash on startup with a missing connection string?

Because the application expects a connection string or other required value from an environment variable, that variable is unset or its `secretRef` points to a secret that does not exist, so the value resolves to null and the application throws during initialization. The fix is to define the secret with the correct name and reference it correctly, or to set the missing environment variable directly.

The console log is decisive here because it carries the application's own exception, which usually names the configuration key it could not find. Read it first.

```bash
# Read the crash output to see which value the app could not find
az containerapp logs show \
  --name my-container-app --resource-group my-rg \
  --type console --revision my-container-app--abc1234 \
  --tail 100
```

Once you know which value is missing, set the secret and wire the reference. The two step pattern is to create or update the named secret and then reference it from the environment variable with `secretref:` pointing at the same name.

```bash
# Define or update the named secret at the app level
az containerapp secret set \
  --name my-container-app \
  --resource-group my-rg \
  --secrets db-connection="Server=...;Database=...;"

# Reference the secret from an environment variable in the container
az containerapp update \
  --name my-container-app \
  --resource-group my-rg \
  --set-env-vars "DB_CONNECTION=secretref:db-connection"
```

The two names that must agree are the secret name, `db-connection` in the example, and the value after `secretref:` in the environment variable. If they differ by even a character, the reference resolves to nothing and the container crashes exactly as before. Reading them side by side after the change, and confirming the new revision starts cleanly in the console stream, closes the loop. A common variant is a secret sourced from Key Vault through a reference rather than set inline; if that integration is misconfigured, the symptom is identical, a null value at startup, so confirm the Key Vault reference resolves and that the app's identity can read the vault.

### Why does the same image work locally but crash in Container Apps?

Because your local environment supplies configuration that the Container Apps revision does not: a `.env` file, an exported shell variable, a local service on localhost, or a default that exists on your machine but not in the cloud, so the container finds the value locally and finds nothing in the revision. The fix is to enumerate every environment variable and secret the application reads and ensure each is provided in the revision's configuration.

This gap between local success and cloud failure is one of the most reliable signals that the cause is configuration rather than code, because identical code with identical dependencies behaves differently only when its inputs differ. The disciplined fix is to audit the application's configuration surface: every environment variable it reads, every connection string, every feature flag, every secret, and to confirm that the revision provides each one, either as a plain environment variable for non sensitive values or as a secret reference for sensitive ones. Building that audit once and encoding it in your deployment template, rather than discovering each missing value through a separate crash, turns a string of failed revisions into a single correct one.

## Cause five: resource and scale settings prevent a replica from running

A revision can fail because the resources you requested are invalid or insufficient, or because the scale rules cannot place a replica. The platform constrains the CPU and memory you can request to a set of valid combinations, and an out of range request is rejected at provisioning. A memory allocation that is too small for the workload lets the container start and then get killed when it exceeds the limit, which the system log records as an out of memory kill. Scale settings that conflict, such as a minimum replica count the environment cannot satisfy, can prevent placement.

The resource model is specific and worth getting exactly right. In the Consumption profile, CPU and memory come in fixed pairings rather than arbitrary values, with memory scaling in proportion to CPU. Requesting a CPU and memory combination that is not on the allowed list causes the revision to fail at creation because the platform cannot place a replica with an invalid resource shape. The current allowed combinations and their exact values change as the platform adds profiles and capacity, so verify the valid pairings against the current documentation for your environment and profile; the durable rule is that CPU and memory are not independently arbitrary, they come in supported pairs, and a rejected revision with a resource related message means you chose a pair that is not supported.

### Why does my revision fail with an invalid CPU and memory combination?

Because Container Apps only accepts specific CPU and memory pairings for a given profile, and the values you requested are not a supported pair, so the platform rejects the revision at provisioning rather than placing a replica with an impossible resource shape. The fix is to set the CPU and memory to a valid supported combination.

```bash
# Set a valid CPU/memory pair (verify the current allowed pairs for your profile)
az containerapp update \
  --name my-container-app \
  --resource-group my-rg \
  --cpu 0.5 \
  --memory 1.0Gi
```

The pattern to internalize is that memory is expressed with its unit and must match the CPU value according to the supported table for your environment, so a request like a fractional CPU paired with a memory value that does not correspond is rejected. When a revision fails immediately at creation with a message about resources, this is almost always the cause, and the fix is mechanical once you consult the current valid pairings. Do not guess at arbitrary values; pick from the supported set.

### Why does my container get killed with an out of memory error?

Because the container's working set exceeds the memory you allocated to it, so the platform terminates it to protect the host, and the revision shows a replica that starts and then is killed and restarted on a memory related reason. The fix is to raise the memory allocation to a valid pair that fits the workload, or to reduce the application's memory footprint.

An out of memory kill is different from a startup crash because the container runs successfully for a while, doing real work, and is then terminated when it crosses the limit. The system log records the kill with a memory related reason, and the timing correlates with load or with a memory intensive operation rather than with startup. Two fixes exist and you should choose deliberately. Raising the memory to the next valid pair gives the workload room, which is right when the application's footprint is legitimate. Reducing the footprint, by fixing a leak, lowering an in memory cache, or tuning the runtime's heap, is right when the memory growth is a bug rather than a need. Throwing memory at a leak only delays the kill; measure the working set under real load and decide which fix the evidence supports.

### Can scale rules cause a revision to fail to activate?

Yes, when the scale configuration cannot be satisfied, such as a minimum replica requirement the environment cannot place or a scale rule that holds the revision at zero replicas so nothing ever runs to pass health. The fix is to set scale bounds the environment can satisfy and to confirm a scale trigger will actually bring up a replica.

A subtle version of this is a revision configured to scale to zero with no traffic and no event to wake it, so it sits at zero replicas, and an observer mistakes the absence of a running replica for a failure when it is actually correct idle behavior. Distinguish "failed" from "scaled to zero" in the running state before you chase a phantom. The genuine failure case is a minimum replica count or a scale rule that the environment cannot honor, which prevents a replica from being placed at all. Setting sane scale bounds, a minimum and a maximum the environment can support, and confirming the scale trigger fires, resolves the activation failure that comes from scaling rather than from the image, the probe, or the port. The full revision and scaling model, including how the autoscaler and revision lifecycle interact, is laid out in the [Azure Container Apps service deep dive](/2022/03/14/azure-container-apps-explained/), which is the right place to build the complete picture of how revisions, traffic, and scale fit together once you have resolved the immediate failure.

### Why does a revision pass health at one replica but fail under scale?

Because a rollout that provisions and serves correctly at a single replica can still fail once the scaler adds more, when the additional replicas hit a downstream limit, exhaust a connection pool, or contend for a resource that was adequate for one instance but not for many, so the failure appears only after traffic or an event triggers scale out. The tell is a rollout that is healthy and serving immediately after deploy and then degrades or restarts replicas as the replica count climbs, rather than failing at activation.

This is the failure that survives every check in the table because the initial provisioning was genuinely fine. The first replica pulled its image, started, passed health, and took traffic, so the rollout activated cleanly and you moved on. The trouble surfaces later, under the load or the event volume that drives the scaler past one replica, and now the symptom is restarts or out of memory kills that correlate with the replica count rather than with the deploy. Several distinct causes hide here. A database or downstream service with a connection cap that one replica respected can be overwhelmed when ten replicas each open a pool, producing errors that look like application bugs but are really a scale interaction. A per replica memory footprint that fit comfortably at low concurrency can cross the limit when each replica handles more in flight requests, producing out of memory kills that only appear under load. A scale rule tuned too aggressively can add replicas faster than a stateful dependency can absorb them. The diagnosis is to correlate the replica count over time against the errors, which the system and console logs timestamped against the scale events make possible, and then to fix the actual constraint: raise the downstream limit, size memory for peak concurrency rather than idle, or temper the scale rule so growth stays within what the dependencies tolerate. Distinguishing a scale interaction from a provisioning failure keeps you from re examining an image or a probe that was never the problem.

## Cause six: a bad command, entry point, or CPU architecture

The last distinct cause is the container that exits immediately, before it does any work, because the image cannot run as configured. A wrong entry point or command means the container starts and the process cannot be found or fails its arguments. An image built for the wrong CPU architecture means the platform cannot execute the binary at all and reports an exec format error. Both produce an instant nonzero exit and a replica that restarts without ever serving, and both are visible in the console log as the container's own first and last words.

### Why does my container exit immediately with an exec format error?

Because the image was built for a different CPU architecture than the platform runs, most often an ARM image built on an Apple Silicon machine deployed to an x86 environment, so the platform cannot execute the binary and the container exits at once with an exec format error. The fix is to build the image for the architecture Container Apps runs, typically linux/amd64, or to build a multi architecture image.

This cause has become far more common as developers build on ARM based laptops and push images that run locally and fail in the cloud. A local build defaults to the build machine's architecture, so an image built on Apple Silicon is an ARM image, and deploying it to an x86 environment yields an exec format error the instant the platform tries to start the process. The fix is to specify the target platform at build time.

```bash
# Build explicitly for the platform Container Apps runs
docker build --platform linux/amd64 -t myregistry.azurecr.io/my-api:1.4.2 .
docker push myregistry.azurecr.io/my-api:1.4.2

# Or build a multi-arch image that runs on either
docker buildx build --platform linux/amd64,linux/arm64 \
  -t myregistry.azurecr.io/my-api:1.4.2 --push .
```

If your console log shows an exec format error and your build happened on an ARM machine, this is almost certainly the cause, and rebuilding with an explicit `--platform linux/amd64` resolves it. Confirm the architecture mismatch rather than assuming, because the same instant exit can also come from a wrong entry point.

### Why does my container exit nonzero before it does anything?

Because the configured command or entry point is wrong, the binary is not at the path specified, or the arguments cause an immediate failure, so the process exits before it can listen or serve and the replica restarts on a failed container. The fix is to correct the command and arguments in the container configuration to match what the image actually contains.

Read the console log for the first lines the container produced. A "command not found," a "no such file or directory" for the entry point, or an immediate usage error tells you the command configuration disagrees with the image. The container configuration in Container Apps can override the image's default command and arguments, and an override that does not match the image is a common self inflicted failure: someone sets a command that exists in one image and reuses the configuration with a different image. Either remove the override and let the image's own entry point run, or set the command to a path and arguments that the image genuinely provides. A quick test is to run the image locally with the same command and confirm it starts; if it fails locally with the same error, the platform is innocent and the configuration is the cause.

## A worked diagnosis from a single failed deploy

The fastest way to internalize the pass-health-to-activate rule is to walk one failure end to end, from the moment the deploy reports success to the moment a corrected rollout takes traffic, so the order of the signals becomes muscle memory. Picture a typical incident: you push a new build, the deploy command returns cleanly, and your endpoint keeps serving the previous behavior. Nothing is on fire, which is the trap, because in single revision mode the platform held traffic on the last healthy version while the new one quietly stalled.

You begin where the diagnosis always begins, with the rollout list, because it localizes the failure before you read a single line of log output.

```bash
az containerapp revision list \
  --name my-container-app --resource-group my-rg --output table
# NAME                       ACTIVE  TRAFFICWEIGHT  PROVISIONINGSTATE  RUNNINGSTATE  REPLICAS
# my-container-app--abc1234  False   0              Provisioned        Degraded      1
# my-container-app--prev999  True    100            Provisioned        Running       1
```

The newest rollout is Provisioned but Degraded, holds zero traffic, and has one replica. That single line already eliminates half the table: the image pulled, because a replica exists, and the resource pair was valid, because the platform placed a replica and provisioning succeeded. The stall is therefore at health, which means a probe, a target port, or a crash after start. You do not yet know which of those three, so you read the platform's verdict next.

```bash
az containerapp logs show \
  --name my-container-app --resource-group my-rg \
  --type system --revision my-container-app--abc1234 --tail 40
# ... Reason: Unhealthy  Readiness probe failed: connection refused on :8080 ...
```

The system stream names it: a readiness probe failed with a connection refused on port 8080. A connection refused is not a slow probe or a wrong path; it is the absence of anything listening at that port, which points squarely at a target port mismatch or a localhost bind rather than a probe timing problem. You confirm against the application's own startup output, where the framework announces what it actually bound.

```bash
az containerapp logs show \
  --name my-container-app --resource-group my-rg \
  --type console --revision my-container-app--abc1234 --tail 20
# ... Server listening on http://0.0.0.0:3000 ...
```

There it is. The application binds 0.0.0.0:3000, so the bind address is fine, but the platform's readiness check and the ingress target are aimed at 8080, where nothing answers. The two numbers disagree, the probe gets a connection refused, the replica never goes ready, and the health gate holds. The fix is a single field, and applying it mints a fresh rollout because the failed one is immutable.

```bash
az containerapp ingress update \
  --name my-container-app --resource-group my-rg --target-port 3000
```

You watch the system stream as the new rollout provisions, see the readiness probe report success this time, and confirm with the list that the corrected version now shows Running with full traffic while the previous one steps down. Total elapsed time once you knew the method: a few minutes. The same shape of diagnosis works for every cause in the table. You read the state to localize, read the system reason to categorize, read the console output to confirm the application's side when the category is a crash, change the one thing the signal named, and create a new rollout that clears the gate. The discipline is the order, and the order is always state, then system reason, then console detail.

### What does the diagnosis look like when the replica list is empty?

When the replica list is empty, the platform never created a container, so you skip the console logs entirely and read the system reason for a pull or a scheduling failure, because there was no application output to produce. An empty replica list with a Failed provisioning state is the cleanest signal in the whole model: it means the failure happened before any container ran.

This is the mirror image of the worked case above. There, a replica existed, so the failure was at or after start, and the console logs mattered. With an empty replica list, the container never came into being, so the console stream has nothing to show and reading it wastes time. Go straight to the system reason. If it names an unauthorized response or a registry error, you are in cause one, the pull, and the fix is identity, reference, or reachability. If it names a resource problem or a scheduling failure with no pull error, you are in cause five, the resource pair or the scale rule, and the fix is a valid CPU and memory combination or a satisfiable scale bound. The empty replica list is the fork in the road: container created means read console, no container means read the system reason and stop.

## Prevention: stop revisions from failing before you deploy

The fastest fix is the failure you never ship, and a handful of habits eliminate most of the causes above before a revision is ever created. Each habit targets a specific cause family, and together they turn a stream of failed revisions into clean activations.

Pin every image to an explicit immutable tag per build rather than reusing `latest`, so each revision references an image that either exists exactly or does not, removing the ambiguity that causes both pull failures and the wrong code running. Build that image with an explicit `--platform linux/amd64` in your pipeline so an architecture mismatch can never reach the platform from a developer's ARM laptop. Use a managed identity with AcrPull for the registry rather than admin credentials, configured once at the app level, so the pull authorization is stable across revisions and you are not re granting permissions per deploy. Audit the application's full configuration surface, every environment variable and secret it reads, and encode it in your deployment template so a missing value is caught in review rather than at runtime. Set the ingress target port to a port the application reads from an environment variable you control, so the port the app binds and the port the platform probes are the same number by construction. Choose CPU and memory from the supported pairings and size memory against measured working set under load, not against a guess. Define probes only when the default does not fit, and when you do, point them at endpoints the application genuinely serves with timing that covers real startup.

### How do I encode a correct revision as code so it cannot drift?

Define the container app in Bicep or another infrastructure as code template that pins the image tag, declares the secrets and their references by matching names, sets the ingress target port to the port the application reads from its environment, and chooses a supported CPU and memory pair, so that every rollout is reviewed as a diff and the values that cause failures are caught before they are deployed. A template makes the configuration that fails or succeeds a reviewable artifact rather than an ad hoc series of CLI flags.

The point of encoding it is that each of the six causes corresponds to a field in the template, so getting the template right once eliminates the whole family from your future incidents. A small Bicep fragment shows the fields that matter, with the target port, the secret reference, and the resource pair all explicit and reviewable.

```bicep
resource app 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'my-container-app'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 3000        // must equal the port the container binds
      }
      secrets: [
        { name: 'db-connection', value: dbConnection }
      ]
      registries: [
        { server: 'myregistry.azurecr.io', identity: 'system' }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: 'myregistry.azurecr.io/my-api:1.4.2'  // pinned, never latest
          resources: { cpu: json('0.5'), memory: '1.0Gi' }  // supported pair
          env: [
            { name: 'PORT', value: '3000' }
            { name: 'DB_CONNECTION', secretRef: 'db-connection' }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 10 }
    }
  }
}
```

Read that template against the table of causes and every row is closed by a field you can see. The pinned image tag closes the pull existence failure. The registry identity closes the pull authorization failure. The matching secret name and secretRef close the missing secret crash. The single explicit port shared between the `PORT` environment variable and the ingress target port closes the port mismatch. The supported CPU and memory pair closes the invalid combination rejection. The sane scale bounds close the activation failure from scaling. When the template is the source of truth, a change that would break a rollout shows up as a suspicious diff in review, not as a failed revision in production. This is the same delivery discipline that keeps any Azure resource reproducible, and pairing the template with a deploy that validates before it applies turns the whole failure class into something you catch at the pull request rather than at the incident.

The deepest prevention is to reproduce the failure before it matters. Spinning up a throwaway revision that intentionally omits a secret, points a probe at the wrong port, or references a missing image teaches you exactly what each failure looks like in the system and console logs, so that when it happens for real you recognize the signal in seconds. VaultBook is the hands on companion for exactly this kind of practice: you can [run the hands on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to stand up a Container Apps environment, deploy a deliberately broken revision, and read the resulting logs in a sandbox where breaking things costs nothing, with the tested CLI, Bicep, and KQL commands ready to copy. The library covers the registry, identity, probe, and ingress configuration you need to both break and fix a revision on demand.

## Related failures often mistaken for a failed revision

Several neighboring problems look like a failed revision at first glance and send engineers down the wrong path, so it is worth naming them and the tell that separates each from a genuine revision failure.

A traffic split that never moved looks like a failed revision when the new revision is actually healthy but you are in multiple revision mode with traffic still weighted to the old one, so the new code is provisioned and ready yet receives no requests because you never shifted the weight. The tell is a new revision showing Provisioned and Running with ready replicas but zero traffic; this is a traffic configuration issue, not a provisioning failure, and the fix is to set the traffic weight rather than to debug the revision. A scaled to zero revision looks failed when it is correctly idle, with no replica running because no event or traffic has woken it; the tell is a running state of ScaledToZero rather than Failed, and the fix is nothing, because the next request or event will bring up a replica.

An application level error after a healthy activation looks like a revision problem when the revision provisioned fine and the container is serving, but your application returns errors for its own reasons; the tell is a healthy revision with traffic flowing and errors in the application's responses rather than in provisioning, which moves the investigation into your code and dependencies and out of the revision lifecycle entirely. A registry pull failure that is really a registry side outage or throttling looks like an authorization or existence problem when the registry itself is degraded; the tell is intermittency and a registry status that is not green, which means waiting or retrying rather than re granting roles. Keeping these distinctions sharp stops you from fixing the wrong layer, which is its own kind of wasted afternoon.

Practicing the discrimination between these neighbors is exactly the kind of scenario based work that builds real diagnostic speed. You can [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) that present a failed or stuck revision and ask you to localize it to the right cause from the logs and state alone, which trains the reflex to read the revision state, then the system reason, then the console output in the order that resolves the incident fastest. The drills also serve as cutover rehearsal for teams adopting multiple revision mode, where confusing a traffic split with a failed revision is the single most common early mistake.

## The verdict: read the gate the revision stalled at

Every failed Container Apps revision is a revision that could not clear the pass-health-to-activate gate, and the gate it stalled at is recorded in the revision state, the system reason, and the console output. Read those three in order and the diagnosis is mechanical: an empty replica list with a pull reason is the image, a running container that never goes ready is the probe or the target port, a container that crashes and restarts with its own exception is a missing secret or a bad command, a replica killed on memory is the resource size, and a rejected revision is an invalid resource pair or a scale rule the environment cannot honor. The one move that never helps is redeploying the same configuration into the same gate; the revision is immutable, the failure is preserved, and the fix is always to change the specific thing the log names and create a new revision that clears the gate. Hold the rule, read the signal in order, match the cause to the fix in the table, and a failed revision stops being a mystery and becomes a five minute repair. The teams that move fastest on this platform are not the ones who never break a rollout; they are the ones who have read enough system reasons that the category is obvious at a glance, who keep prior revisions active so rollback is a traffic weight rather than a rebuild, and who encode the configuration as a reviewable template so the failure is caught in a diff long before it reaches production.

## Frequently Asked Questions

### Q: Why does my Container Apps revision fail to provision?

A revision fails to provision when it cannot complete the sequence of pulling its image, scheduling a replica, starting the container, and passing health, and the provisioning state goes to Failed at whichever step blocked. Read the revision detail first to localize the stall: an empty replica list with a Failed provisioning state points at an image pull failure or a resource and scheduling problem before any container ran, while a replica that exists but a Degraded running state points at a crash on start, a failing probe, or a target port mismatch after the container started. The system logs name the categorized reason, whether that is a pull, a probe, or a kill, and the console logs carry the application's own error when the cause is a crash. The revision is immutable, so you fix the specific thing the logs name and create a new revision; you do not retry the failed one.

### Q: Does an image pull failure fail the revision?

Yes, a pull failure stops the revision before it can run a container, so the provisioning state goes to Failed and the replica list is empty because nothing was ever created to run. There are three flavors. An authorization failure means the pull identity lacks AcrPull on the registry, and the system log shows an unauthorized response from the registry; the fix is to grant AcrPull to the identity and attach the registry with that identity. An existence failure means the repository or tag does not exist at the referenced path, often a typo or a tag never pushed; the fix is to confirm the image and tag in the registry and correct the reference. A reachability failure means the environment cannot reach a registry behind a private endpoint or firewall, and the log shows a connection or timeout rather than an unauthorized; the fix is at the network layer. The empty replica list is the strongest tell that the failure is at the pull and not later.

### Q: Can a failing startup or readiness probe fail a revision?

Yes, a probe that never succeeds keeps the revision from reaching a healthy active state even when the container is running, because the platform will not route traffic to a replica it considers unready. A readiness probe controls whether a replica joins the traffic set, so a readiness probe pointed at a wrong path or port keeps the revision at zero traffic indefinitely. A startup probe gates the others and, if it is too impatient for your real startup time, fails a container that would have come up moments later. A liveness probe that fails causes the platform to kill and restart the container in a loop, which looks like a crash but is the platform terminating a healthy process. The tell for a probe loop is a clean startup in the console log followed by an external termination on a rhythm that matches the probe period. The fix is to point the probe at an endpoint the application genuinely serves on the correct port and to size its timing for your real startup, or to remove a wrongly copied probe and rely on the default behavior.

### Q: Does a wrong target port fail the revision health?

Yes, an ingress target port that does not match the port the container actually listens on keeps the revision unhealthy, because the platform sends health checks and traffic to the target port and finds nothing there, so readiness never passes. Read the application's console log at startup to see the port it bound, query the configured target port, and compare the two; a mismatch is the cause. The fix is to set the ingress target port to the port the application logs say it is listening on. A related variant is an application bound to localhost or 127.0.0.1, which accepts only connections from inside the container and refuses the platform's external connection even when the port number matches; that application must bind 0.0.0.0 to accept connections across the container boundary. The most reliable pattern is to have the application read its port from an environment variable, set that variable explicitly, and set the target port to the identical number so the bind and the probe agree by construction.

### Q: Does a missing secret or env var fail the revision?

Yes, when the application reads a required value from an environment variable that is unset or whose secretRef points at a secret that does not exist, the value resolves to null, the application throws during initialization, and the container crashes on start; the platform restarts it and it fails the same way, so the revision never gets a healthy replica. The console log is decisive because it carries the application's own exception naming the configuration key it could not find. The fix is to define the named secret correctly and reference it from the environment variable with secretref pointing at the same name, or to set the missing plain environment variable directly. The two names that must agree are the secret name and the value after secretref in the environment variable; a single character difference resolves to nothing. A frequent variant is a Key Vault sourced secret whose reference is misconfigured or whose identity cannot read the vault, which produces an identical null at startup.

### Q: How do I find why a Container Apps revision is unhealthy?

Read three sources in a fixed order: the revision state to localize the failure, the system logs to see the platform's verdict, and the console logs to see the application's own error. Start with the revision show command to find the provisioning and running state and whether a replica exists, which tells you whether the stall is before the container ran or after. Then stream or query the system logs, where the categorized reason field names a pull, a probe, or a kill, and the detail field carries the human readable specifics. Then read the console logs only when the system verdict points at a crash, to see the stack trace or message the application printed before it exited. In Log Analytics, the system events land in the system table and the application output in the console table, both filterable by revision name. The replica view adds whether a container started and how many times it restarted, which separates a pull or scheduling failure from a crash loop after a successful start.

### Q: Why does my old revision keep serving after I deploy a new one?

Because in single revision mode the platform only shifts traffic to a revision that has passed health, so when the new revision fails to provision or fails its probes, traffic stays on the last healthy revision and the old behavior persists. The deployment command can still report success because success there means the revision was created and accepted, not that it became active and took traffic. This fails safely, which is the point of the design, but it confuses engineers who assume the new code is live and debug application logic that is not even running. The first check when a change does not take effect is the Revision management blade or the revision list: if the newest revision shows Failed or Degraded with zero traffic, the new code never went live, and you diagnose the failed revision rather than the application. This silent failure mode is the opposite of an in place deploy, where a broken deployment breaks the running app loudly.

### Q: How do I roll back a failed Container Apps revision?

You roll back by directing traffic to a previous healthy revision rather than redeploying anything, because revisions are immutable and the old one still exists. In single revision mode, the platform already holds traffic on the last healthy revision when the new one fails, so the practical rollback is automatic; you simply fix the new revision or deactivate it. In multiple revision mode, you set the traffic weight back to the known good revision, which routes requests away from the failed one immediately. You can also explicitly activate a prior revision and weight it to receive traffic. Because rollback is a traffic operation rather than a rebuild, it is fast and does not depend on your pipeline being healthy, which is one of the strongest operational advantages of the revision model. Keep prior revisions active long enough to roll back to during a risky rollout rather than deactivating them the moment a new one goes live.

### Q: Why does the same image run locally but fail in Container Apps?

Because the difference is almost always configuration or architecture, not code, since identical code with identical dependencies behaves differently only when its inputs or its runtime differ. The two leading causes are a missing environment variable or secret that your local environment supplies through a dotenv file or an exported shell variable but the revision does not, which crashes the container on start, and an image built for the wrong CPU architecture, where a build on an ARM laptop produces an ARM image that fails with an exec format error on an x86 environment. A third is a localhost bind that works on your machine but refuses the platform's external connection in a container. Audit every environment variable and secret the application reads and confirm the revision provides each, build the image with an explicit linux/amd64 platform, and bind 0.0.0.0 rather than localhost. The local versus cloud divergence is itself a strong signal that the cause is environmental rather than logical.

### Q: What is the difference between provisioning state and running state?

The provisioning state describes whether the revision successfully completed its setup, with Provisioned meaning the platform pulled the image and prepared the revision and Failed meaning it could not, while the running state describes the live behavior of the revision's replicas, with values such as Running, Degraded, Failed, and ScaledToZero. A revision can be Provisioned yet show a Degraded or Failed running state when the container started but then crashed, failed a probe, or could not be reached on the target port. Conversely a Failed provisioning state usually means the failure was earlier, at the image or the resource shape, before a replica ran. Reading both together localizes the stall: Failed provisioning with no replica points at the pull or the resource pair, while Provisioned with a Degraded running state points at a probe, a port, or a crash after start. A ScaledToZero running state is not a failure at all; it is correct idle behavior awaiting an event or request.

### Q: Why does my revision fail with an invalid CPU and memory combination?

Because Container Apps accepts only specific CPU and memory pairings for a given profile rather than arbitrary independent values, and a request that is not one of the supported pairs is rejected at provisioning so the platform never places a replica with an impossible resource shape. Memory is expressed with its unit and must correspond to the CPU value according to the supported table for your environment and profile. When a revision fails immediately at creation with a resource related message and no replica is ever scheduled, this is the likely cause, and the fix is mechanical: choose a CPU and memory pair from the current supported set rather than guessing. The exact allowed pairings change as the platform adds profiles and capacity, so verify them against the current documentation for your environment type rather than relying on a fixed list. Do not confuse this rejection at creation with an out of memory kill at runtime, which is a different cause with a different fix.

### Q: Why does my container get killed with an out of memory error?

Because the container's working set exceeded the memory you allocated, so the platform terminated it to protect the host, and the system log records the kill on a memory related reason. This differs from a startup crash because the container ran successfully and did real work before being killed, and the timing correlates with load or a memory intensive operation rather than with startup. You have two fixes and should choose by evidence. Raising the memory to the next supported pair is right when the application's footprint is legitimate and simply needs more room. Reducing the footprint, by fixing a leak, shrinking an in memory cache, or tuning the runtime heap, is right when the growth is a bug. Measuring the working set under realistic load tells you which. Throwing memory at a genuine leak only postpones the kill, so confirm whether the memory use is a need or a defect before you decide which lever to pull.

### Q: Do I need to define health probes for my container app?

Not always, because the platform applies sensible default health behavior tied to your ingress target port when you define no custom probes, and a wrong custom probe is worse than relying on that default. Define custom probes when your application has a startup that is slow enough to need a startup probe's grace, a readiness condition more specific than the port being open, or a liveness check that genuinely reflects health. The common self inflicted failure is copying a probe block from another service, pointing it at an endpoint this application does not serve, and converting a working default into a guaranteed failure. If a revision was healthy before you added probes and failed after, remove them, confirm recovery on the default, and reintroduce a correct probe only if you need one. The exact default behavior depends on whether ingress is enabled and on the platform version, so verify it for your environment; treat probes as a deliberate choice rather than a box to fill by reflex.

### Q: How do I read Container Apps logs to diagnose a failed revision?

Use the streaming commands while you reproduce the failure and the Log Analytics tables for the durable record. The system stream, requested with the system log type, shows the platform's provisioning and lifecycle events: pull outcomes, scheduling, probe results, and kills. The console stream, requested with the console log type, shows your application's stdout and stderr, including the stack trace before a crash. Read system first for the platform's verdict, then console when the verdict points at a crash. For history and correlation across replicas, query the workspace, where the system events land in the system table and the application output in the console table, both filtered by revision name and ordered by time. The reason field in the system table carries the categorized cause and the log field carries the detail. The exact table and column names can vary by workspace and platform version, so confirm them against your own schema while keeping the filter by revision then read reason then detail pattern.

### Q: Why does my container exit immediately with an exec format error?

Because the image was built for a different CPU architecture than the platform runs, most commonly an ARM image built on an Apple Silicon machine deployed to an x86 environment, so the platform cannot execute the binary and the container exits at once. This has grown common as developers build on ARM laptops, since a local build defaults to the build machine's architecture and produces an image that runs locally and fails in the cloud. The console log shows the exec format error as the container's first and last output. The fix is to build for the platform Container Apps runs by passing an explicit linux/amd64 platform at build time, or to build a multi architecture image with a build tool that targets both amd64 and arm64 so the same tag runs on either. If your console log shows an exec format error and your build happened on an ARM machine, this is almost certainly the cause, and rebuilding with the explicit platform resolves it. Confirm the architecture rather than assuming, because a wrong entry point produces a similar instant exit with a different message.

### Q: Can a scale rule cause a revision to fail to activate?

Yes, when the scale configuration cannot be satisfied, such as a minimum replica count the environment cannot place, the revision cannot bring up a replica to pass health and therefore never activates. A subtler case is a revision configured to scale to zero with no traffic and no event to wake it, which sits at zero replicas; that is correct idle behavior, shown as a ScaledToZero running state, and mistaking it for a failure sends you chasing a phantom. Distinguish a genuine activation failure from correct idleness by reading the running state before anything else. The real failure is a scale bound or rule the environment cannot honor, and the fix is to set a minimum and maximum the environment supports and to confirm the scale trigger actually fires to bring up a replica. The revision and scaling lifecycle interact closely, so understanding how the autoscaler decides to place replicas clarifies both the failure and the correct idle behavior.

### Q: Why does my probe pass locally but fail in Container Apps?

Because the probe target that works against a local process can fail against a containerized one for the same reasons a real request would: the application binds localhost rather than 0.0.0.0 and refuses the platform's external connection, the target port disagrees with the bound port, or the startup timing that is instant on a warm laptop is too slow for the probe's threshold during a cold container start. A local health check from the same machine reaches the process over loopback, masking a bind to localhost that fails the moment the platform connects across the container boundary. The fix mirrors the target port and bind guidance: bind 0.0.0.0, match the probe port to the bound port, and size the startup probe so its initial delay plus failure threshold times its period comfortably exceeds the real cold start. A probe that tests a heavy dependency rather than the app's own readiness also passes locally and fails in the cloud when that dependency is briefly slow, so test something cheap that genuinely indicates the app can serve.

### Q: Should I use latest or pinned tags for my container images?

Pin every image to an explicit immutable tag per build rather than reusing latest, because a pinned tag makes each revision reference an image that either exists exactly or does not, removing the ambiguity that causes both pull failures and the wrong code running. With latest, a revision created before a push completes can pull a stale or absent image, and you cannot tell from the revision which build is actually live, which turns a rollback into guesswork. A per build tag, such as a version or a commit hash, ties each revision to a known artifact, so the failed revision's image is unambiguous and the healthy revision you roll back to is unambiguous. This single habit prevents a class of pull existence failures and makes the whole revision history auditable, since the tag on each revision tells you exactly what code it ran. Reserve latest for convenience in non production experimentation, never for the revisions you depend on.
