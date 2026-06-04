---
layout: post
title: "Azure Container Apps Explained"
page_title: "Azure Container Apps Explained: Serverless Containers, Revisions, KEDA Scaling, and When to Choose It Over AKS and App Service"
date: 2022-03-14
categories: ["Technology"]
tags: ["Azure", "Container Apps", "Serverless", "Containers", "KEDA", "Architecture", "Cloud Computing"]
excerpt: "Azure Container Apps explained: how the serverless container platform runs revisions, scales to zero with KEDA, and when to pick it over AKS or App Service."
image: "/assets/images/blog/blog-11.webp"
reading_time: 60
author: "Insight Crunch Team"
last_updated: 2022-03-14
---

Azure Container Apps is the platform engineers reach for when they have a containerized workload, want Kubernetes-grade scaling and rolling traffic control, and have no appetite for operating a cluster. That sentence hides the single decision most teams get wrong. They see "containers" and "scaling" and "Kubernetes under the hood," and they provision an Azure Kubernetes Service cluster they will spend the next year patching, upgrading, and right-sizing, when the workload would have run on a managed service that bills to zero between requests and asks nothing of them operationally. The gap between using this platform well and misusing it is not a feature gap. It is a reasoning gap about what you are actually buying, what you are giving up, and which of the three Azure container hosts your workload truly needs.

![Azure Container Apps serverless container platform architecture and revision model - Insight Crunch](/assets/images/blog/blog-11.webp)

This is a service deep dive, so the goal is not a quickstart. The goal is the mental model that lets you reason about the platform during a design review, predict its behavior under load, debug it when a deployment will not take traffic, and defend the choice against an architect who reflexively wants Kubernetes. By the end you should be able to explain what an environment, a revision, and a replica are and how they relate, why an app can cost nothing while idle and what that costs you in latency, how event-driven scaling reaches all the way down to zero, what the Dapr sidecar adds and when it earns its place, and the one rule that settles the question of when to walk past this service and stand up a real cluster instead.

## What Azure Container Apps Is and the Mental Model to Hold

Azure Container Apps is a managed, serverless platform for running containers. You hand it a container image and a small amount of declarative configuration, and it runs that image as one or more replicas, scales the replica count up and down (including to zero) based on demand signals, exposes it over HTTP or TCP if you ask, and rolls new versions out as immutable revisions you can split traffic across. Underneath, it runs on a managed Kubernetes substrate that you never see, never administer, and never patch. There is a real Kubernetes control plane and real nodes somewhere in the platform, but they are Microsoft's operational responsibility, not yours. You get the scaling primitives and the rollout primitives that a Kubernetes operator would build by hand, delivered as a service.

The mental model that keeps you out of trouble has three nouns: the environment, the app, and the revision, with the replica sitting underneath the revision. Hold those four and most of the platform's behavior becomes predictable.

The **environment** is the security and network boundary that a group of container apps share. It is the closest analog to a Kubernetes namespace plus the cluster networking around it. Apps in the same environment share a virtual network, can reach each other over a private internal DNS name, write logs to the same Log Analytics workspace, and sit behind the same managed ingress layer. When you decide which apps belong together, you are really deciding which apps should share a network and a billing and observability boundary. Microservices that call each other belong in one environment so the calls stay internal and free of public exposure. Workloads that must be network-isolated from each other belong in separate environments.

The **app** (the container app itself) is the deployable unit: a name, a container image or images, the resource allocation per replica, the ingress configuration, the secrets and environment variables, and the scale rules. An app is long-lived. Its configuration, though, is not edited in place in the way you might expect.

The **revision** is where the platform's discipline lives. A revision is an immutable snapshot of your app's configuration and image at a point in time. You do not mutate a running app and watch it change underneath you. Instead, certain changes (a new image tag, a change to scale rules, a change to resource allocation, a change to environment variables) create a brand new revision, and the platform decides how traffic moves to it. Other changes (revision-scope changes such as a secret value or certain ingress settings) apply across revisions without minting a new one. The immutability is the point: a revision is a known, frozen thing you can roll traffic toward and away from with confidence, because it cannot drift.

The **replica** is the running instance of a revision: an actual container (plus any sidecars) executing on the managed substrate. Scaling is the act of changing how many replicas of a revision exist, from zero up to a configured ceiling. The replica is what you pay for while it runs, and the replica is what disappears when the app scales to zero.

### What does Azure Container Apps actually run?

It runs Linux containers as serverless replicas on a managed Kubernetes substrate you never administer. You supply an image, resource limits, ingress and scale rules, and the platform handles scheduling, rolling revisions, scale-to-zero, the ingress proxy, and optional Dapr and KEDA integration. You operate the app, not a cluster.

Once those four nouns are in place, a lot of folklore about the platform dissolves. "Is it just hosted Kubernetes?" No, because you cannot reach the Kubernetes API, run arbitrary controllers, install a service mesh of your choosing, or schedule pods directly; the cluster is an implementation detail, not a surface you program against. "Is it just App Service for containers?" Also no, because the revision-and-traffic-split model, the event-driven scaling that reaches zero, and the first-class Dapr and KEDA integration are not how App Service thinks about a workload. It sits deliberately between the two, and understanding that middle position is most of understanding the service.

For engineers who already know Kubernetes, the cleanest way to load the model is to map each platform noun to the primitive it abstracts. The environment corresponds to a namespace plus the cluster networking and ingress layer around it: a shared boundary with its own network and observability. A revision corresponds to a Deployment at a fixed configuration, an immutable description of desired state that the platform reconciles into running instances. A replica corresponds to a Pod, the actual running unit, here including any injected sidecars such as Dapr. The scaling behavior corresponds to KEDA driving the Horizontal Pod Autoscaler, which is literally what runs underneath, except you configure it through simple scale rules instead of authoring KEDA and autoscaler objects. The managed ingress corresponds to an ingress controller and its routing, except you do not deploy or operate it. The value of the mapping is not nostalgia for YAML; it is that an engineer who knows what a Deployment, a Pod, a namespace, and an ingress controller do already understands what the platform is doing, and can predict its behavior accordingly, while being spared the operational work of running any of those components. The one primitive that has no equivalent you can reach is the API server itself, and that absence is the whole trade.

## How Azure Container Apps Works Internally

The platform is an opinionated wrapper around a handful of Kubernetes-native projects, packaged so you never touch them directly. Knowing which projects do what lets you predict behavior the documentation describes only loosely. The wrapper makes three deliberate trades: it hides the control plane so you cannot misconfigure or neglect it, it constrains the surface to scaling rules, revisions, ingress, secrets, and the Dapr and KEDA integrations so the configuration space stays small enough to reason about, and it bills on a serverless model so idle capacity costs nothing. Each trade buys operational calm at the price of control, and the sections below show exactly where that line falls so you can tell in advance whether a given workload lives comfortably inside the surface the platform exposes or keeps reaching for something behind the wrapper that is not there.

### The environment as the shared substrate

When you create an environment, the platform provisions the managed control plane and a pool of compute behind it. Every app you create inside that environment is scheduled onto that shared substrate. Newer environments default to the workload profiles model, where the environment can host both a serverless consumption profile and dedicated profiles side by side, and each app picks which profile it runs on. The consumption profile is the pure serverless experience: scale on demand, scale to zero, pay only for what runs. A dedicated profile gives you reserved compute with a single-tenancy guarantee and access to larger or specialized instance types, billed by the provisioned profile rather than per running replica. The environment also carries the networking stack: in the workload profiles model that includes virtual network integration, support for private endpoints, and firewall control over egress. Treat the environment as the unit of network design, not an afterthought you create with a default and forget.

Apps in one environment reach each other by name. An app named `orders` with internal ingress is reachable from a sibling app at a stable internal fully qualified domain name the platform assigns, with traffic staying inside the environment's network. That internal reachability is why co-locating chatty microservices in a single environment is the right default; splitting them across environments forces their traffic out to public ingress or through peered networking, which is slower, costlier, and more exposed.

### Revisions, revision modes, and traffic splitting

A revision being immutable is the foundation, and the revision mode is the lever that decides how revisions coexist. In **single revision mode**, the platform keeps exactly one active revision serving traffic; deploying a new revision deactivates the old one once the new one is healthy, which gives you a straightforward rolling replacement. In **multiple revision mode**, several revisions can be active at once, and you control what fraction of incoming traffic each one receives. That traffic split is the mechanism behind blue-green deployments and canary releases without any external tooling: you bring up a new revision holding ten percent of traffic, watch its error rate and latency, and shift the remaining ninety percent over only when it proves itself, or pull it back to zero if it misbehaves.

The split is declarative and weighted by revision. A canary that sends five percent to the candidate and ninety-five percent to the incumbent is two lines of configuration, not a load balancer you wire up yourself. The important subtlety is that traffic weights only mean something for revisions that are active and healthy. A revision that has not finished provisioning, or that fails its health checks, does not silently absorb its share of traffic and start returning errors; it simply does not enter the rotation until it is ready. This is the behavior that confuses engineers who deploy a broken revision and then wonder why the ingress is returning a 503 instead of routing to the new code. The new code never became eligible. We return to that failure mode below.

```bash
# Create an environment, then an app, then inspect revisions.
az containerapp env create \
  --name prod-env \
  --resource-group rg-apps \
  --location eastus

az containerapp create \
  --name orders-api \
  --resource-group rg-apps \
  --environment prod-env \
  --image myregistry.azurecr.io/orders-api:1.4.0 \
  --target-port 8080 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 10 \
  --revision-suffix v140

az containerapp revision list \
  --name orders-api \
  --resource-group rg-apps \
  --output table
```

The `az containerapp revision list` output is where you confirm what is actually live: each revision's name, whether it is active, its health state, its replica count, and its traffic weight. When a deployment behaves unexpectedly, this command is the first place to look, because it tells you which revision the platform considers the source of truth.

### How does traffic splitting work across revisions?

In multiple revision mode you assign each active revision a traffic weight, and the managed ingress routes that percentage of incoming requests to it. Weights apply only to healthy, provisioned revisions, which makes weighted canary and blue-green rollouts a configuration change rather than external load-balancer plumbing you build and maintain.

### KEDA-driven scaling and what scale-to-zero really means

Scaling in Azure Container Apps is powered by KEDA, the Kubernetes Event-driven Autoscaling project that Microsoft and Red Hat originated and that the platform embeds so you configure it through simple scale rules rather than raw KEDA objects. The model is event-driven by design. You declare one or more scale rules, each tied to a trigger: an HTTP rule that scales on the number of concurrent requests, a TCP rule that scales on concurrent connections, or a custom rule that points at one of KEDA's many scalers for external sources such as an Azure Service Bus queue, an Event Hubs stream, a Storage queue, or anything else KEDA supports. The platform watches the trigger metric and adjusts the replica count between your configured minimum and maximum.

The two properties that govern the envelope are `minReplicas` and `maxReplicas`. Set the minimum to zero and the app can scale all the way down to no running replicas when there is nothing to do, which is the property people mean when they say "serverless." Set the minimum to one or more and you keep that many replicas always warm. The maximum caps how far the app spreads under load. There is a platform ceiling on the maximum replica count per app, and because that ceiling has moved upward across platform versions, treat the specific number as a value to confirm against the current official limits rather than a constant; the behavior to internalize is that there is a ceiling and you should set your maximum deliberately rather than leaving it at a default.

The mechanism behind scale-from-zero is worth a sentence because it explains the cold-start contract. For an HTTP app at zero, the managed ingress is always present even when no replica is, so the first arriving request is what the platform observes to trigger a replica, and that request waits for the replica to start before it is served. For an event-driven app at zero, the platform polls the configured event source on an interval (checking a queue's depth, a stream's lag) and starts a replica when there is work, so there is a short detection delay between work appearing and a replica processing it. In both cases the trigger is observed from outside any running replica, which is exactly why these triggers can reach zero while a CPU rule cannot. Tuning the polling interval and the per-replica work unit (how many messages one replica takes per cycle) is how you balance responsiveness against the cost of waking up, and the deeper mechanics of each scaler belong to the dedicated KEDA treatment this section links to.

The one scaling rule that trips people is the interaction between resource-based rules and scale-to-zero. A CPU or memory scale rule cannot scale an app to zero, because evaluating CPU or memory usage requires at least one replica to be running and producing metrics. If you want true scale-to-zero, your scaling has to be driven by an external signal the platform can observe without a running replica: HTTP requests arriving at the ingress, or an event source such as a queue with messages waiting. An app with only a CPU rule will idle at a minimum of one replica, not zero, no matter how you set `minReplicas`. Engineers who expect their CPU-scaled app to drop to zero and save money, and then find it never does, have hit exactly this. The deeper treatment of the scaler model, the full set of triggers, and how KEDA delegates to the underlying autoscaler lives in the dedicated guide to [KEDA event-driven autoscaling on Azure](/2024/09/16/azure-keda-autoscaling/); here the point is that the same engine drives both AKS workloads and this platform, and that the trigger type decides whether zero is reachable.

### What the Dapr integration provides

Dapr (the Distributed Application Runtime) is a portable runtime for the cross-cutting concerns of distributed systems: service-to-service invocation with retries and mTLS, publish and subscribe messaging, state management against a pluggable store, secrets retrieval, and bindings to external systems. Azure Container Apps integrates Dapr as a first-class, opt-in feature. When you enable Dapr on an app, the platform injects the Dapr sidecar alongside your container and exposes the Dapr APIs to your code over localhost, so your application calls a local endpoint and Dapr handles the distributed mechanics.

The value is concrete and worth naming precisely so you can decide whether you need it. Without Dapr, if service A calls service B you write the HTTP client, the retry policy, the timeout, the circuit breaker, and the service discovery yourself, and you do it again in every language your services are written in. With Dapr, service A calls its local Dapr sidecar with the logical name of service B, and the sidecar resolves, retries, and secures the call. Publish and subscribe works the same way: your code publishes to a topic through the sidecar, and the Dapr component configuration (not your code) decides whether that topic is backed by Service Bus, a Storage queue, or another broker. State management lets a stateless container externalize its state to a configured store through a uniform API, so the container stays disposable while the state persists. The honest counterpoint is that Dapr is not free conceptually: it adds a sidecar, a set of component definitions to manage, and a programming model your team has to learn. For a single web app it is overkill. For a fleet of polyglot microservices that need consistent service invocation, messaging, and state handling, it removes a large amount of bespoke plumbing, and because the component bindings live outside your code, you can change the backing infrastructure without recompiling. The pattern this enables most cleanly is covered in the treatment of [event-driven architecture on Azure](/2024/04/22/azure-event-driven-architecture/), where pub/sub and bindings are the connective tissue.

A Dapr component is a declarative definition that binds a Dapr building block to a concrete backing service, and it lives in the environment rather than in your image, which is what makes the infrastructure swappable. A pub/sub component might point a logical topic at Azure Service Bus in production and at a local broker in development, and your code, which only ever publishes to the logical topic through the sidecar, does not change between the two. A state-store component binds the state API to a store such as a Cosmos DB container or a Redis cache, so a stateless container reads and writes state through a uniform key-value interface while the actual store is a configuration concern. Components scope to specific apps in the environment, so you control which apps can use which broker or store. The mental shift Dapr asks for is to stop calling infrastructure directly and start calling the local sidecar with intent, letting the component definition decide the realization. For a team running several services that all need the same messaging and state patterns, that shift removes a large surface of duplicated, language-specific integration code and centralizes it in configuration the platform manages.

```yaml
# A Dapr pub/sub component binding a logical topic to Service Bus.
componentType: pubsub.azure.servicebus.topics
version: v1
metadata:
  - name: connectionString
    secretRef: sb-connection
scopes:
  - orders-api
  - fulfillment-worker
```

### Ingress: external, internal, and the built-in HTTP scaler

Ingress is how traffic reaches your app, and the platform gives you a managed ingress layer so you do not deploy your own. You choose external ingress to expose the app on a public HTTPS endpoint with a platform-provided certificate and hostname (or a custom domain you bind), or internal ingress to expose it only inside the environment for sibling apps to call. You set the target port to the port your container actually listens on, and the ingress proxy forwards to it. The proxy terminates TLS, can enforce that the app is reached only over the assigned hostname, and is the component that the HTTP scale rule observes: because all external HTTP traffic flows through the managed proxy, the platform can count concurrent requests and drive scaling (including the scale from zero on the first request) without your container participating in the measurement.

The target port is the single most common configuration mistake on first deploy. If your container listens on 3000 and you tell the ingress the target port is 8080, the proxy forwards requests to a port nothing is listening on, the health probe fails, the revision never becomes healthy, and the ingress returns 503 while you stare at a green deployment. The fix is always to align the configured target port with the port the process inside the container binds. When the symptom is a revision that will not activate at all, the systematic diagnosis (pull failure, failed probe, wrong target port, missing secret) is laid out in [fixing Container Apps revision failures](/2023/02/13/fix-container-apps-revision-failed/), and reading that alongside this section is the fastest way to turn a 503 into a working endpoint.

### Pulling images from a registry

Your app runs an image, and that image comes from a registry, most commonly Azure Container Registry. On the very first deploy this is where authentication bites. A public image pulls without credentials, but a private registry requires the platform to authenticate, and the cleanest way to do that is to grant the container app a managed identity and assign that identity the AcrPull role on the registry, so no registry password is ever stored. If the identity is missing or under-privileged, the pull fails, the replica cannot start, and the revision fails to provision with an image pull error. This is the same family of failure as the cluster-side `ImagePullBackOff` and `ErrImagePull` that AKS surfaces, and the registry-side root causes are identical; the unauthorized-pull diagnosis is worked end to end in [fixing Container Registry pull unauthorized errors](/2023/02/06/fix-acr-pull-unauthorized/), and the correct identity setup is covered in [setting up managed identities the right way](/2023/04/17/configure-managed-identities/). Wire the identity and the role assignment before the first deploy and this entire class of failure never appears.

```bash
# Grant the app a system-assigned identity and let it pull from ACR.
az containerapp identity assign \
  --name orders-api \
  --resource-group rg-apps \
  --system-assigned

PRINCIPAL_ID=$(az containerapp show \
  --name orders-api \
  --resource-group rg-apps \
  --query identity.principalId -o tsv)

ACR_ID=$(az acr show --name myregistry --query id -o tsv)

az role assignment create \
  --assignee "$PRINCIPAL_ID" \
  --role AcrPull \
  --scope "$ACR_ID"
```

### Health probes and why a misconfigured probe stalls a deploy

The platform decides whether a revision is healthy enough to receive traffic by running health probes against your container, and the three probe types mirror the Kubernetes model the substrate is built on. A startup probe gates the others: until it succeeds, the platform does not consider the container started, and it does not begin liveness or readiness checks. A readiness probe decides whether a started container should receive traffic; while it fails, the replica stays out of rotation even though the process is running. A liveness probe decides whether a running container has become unhealthy and should be restarted. Each probe is an HTTP, TCP, or command check against a path and port you specify, with a period, a timeout, an initial delay, and a failure threshold.

The configuration error that stalls deployments is a probe that can never pass. A readiness probe pointed at `/healthz` when the app serves health at `/health`, or at a port the container does not bind, will fail forever, the revision will never go ready, and the ingress will return 503 because nothing is eligible to serve. The diagnostic tell is a revision that provisions its replicas but never reaches an active, healthy state, with the probe failures recorded in the system logs. The discipline is to make the probe match a route the app genuinely answers quickly and cheaply, to keep the readiness check lightweight so it does not itself time out under load, and to set the initial delay long enough that a slow-starting runtime is not killed before it finishes booting. A liveness probe that is too aggressive can put an app into a restart loop, repeatedly killing a container that was merely slow, which looks like instability but is a probe-tuning problem.

```yaml
# Probe configuration in the app's container template (Bicep/ARM/YAML shape).
probes:
  - type: Startup
    httpGet:
      path: /health/startup
      port: 8080
    initialDelaySeconds: 5
    periodSeconds: 5
    failureThreshold: 30
  - type: Readiness
    httpGet:
      path: /health/ready
      port: 8080
    periodSeconds: 10
    failureThreshold: 3
  - type: Liveness
    httpGet:
      path: /health/live
      port: 8080
    periodSeconds: 15
    failureThreshold: 3
```

Separating the three endpoints in the application matters. A startup endpoint can be cheap and immediate. A readiness endpoint should reflect genuine ability to serve, returning failure while a dependency such as a database connection pool is still warming, so the platform holds traffic until the app can actually handle it. A liveness endpoint should detect a wedged process without coupling to external dependencies, because a liveness failure restarts the container, and you do not want a transient database outage to trigger a restart storm across every replica.

### Secrets and configuration the right way

A container app holds secrets at the app level and references them from environment variables or from scale-rule authentication, so sensitive values never sit in plaintext in the container definition or in your image. You define a secret with a name and a value (or a reference to a Key Vault secret resolved through the app's managed identity), and then an environment variable points at the secret by name rather than carrying the value inline. Updating a secret value is a revision-scope change: it does not mint a new revision, which is convenient for rotating a credential, though your application has to be written to pick up the new value, since a long-running process that read the secret once at startup will not see the change until it restarts.

The cleaner pattern for anything stored in Azure Key Vault is to reference the Key Vault secret directly and let the app's managed identity resolve it, so the secret lives in one place, rotates in one place, and is access-controlled by Key Vault policy rather than copied into the app. The anti-pattern is baking configuration or credentials into the image, which couples a secret rotation to an image rebuild and leaks the value to anyone who can pull the image. Externalize configuration through environment variables and secrets, keep the image free of environment-specific values, and the same image promotes cleanly from a test environment to production with only its configuration differing.

```bash
# Store a secret and reference it from an environment variable.
az containerapp secret set \
  --name orders-api \
  --resource-group rg-apps \
  --secrets "db-conn=$CONNECTION_STRING"

az containerapp update \
  --name orders-api \
  --resource-group rg-apps \
  --set-env-vars "DB_CONNECTION=secretref:db-conn"
```

### Running more than one container in a single app

An app's replica usually runs one application container, but the platform allows additional containers in the same replica, which share the replica's network namespace and lifecycle. The first-class case is the Dapr sidecar, injected automatically when you enable Dapr. You can also define sidecar containers explicitly for patterns such as a log shipper, a local proxy, or an init-style helper. The thing to hold clearly is the scope: containers defined together in one app's template run together in every replica of that app, scale together, and are billed together, because they occupy the same replica. That is different from running two separate apps in an environment, which scale independently and communicate over the internal network. Use multiple containers in one app when the helper genuinely belongs to the application instance and must live and die with it; use separate apps when the components scale on different signals or have independent lifecycles. Reaching for multiple containers to emulate a full Kubernetes pod with several co-equal services is usually a sign the workload wants AKS instead.

### Container Apps jobs for finite and scheduled work

Not every workload is a long-running service that answers requests. A great deal of real work is finite: process a batch, run a nightly report, handle a burst of messages and then stop. The platform models this as a container apps job, which runs a container to completion rather than keeping it alive to serve traffic. A job has three trigger types. A manual job runs when you start it, which suits ad hoc or pipeline-invoked tasks. A scheduled job runs on a cron expression, which replaces a separate scheduler for periodic work. An event-driven job starts executions in response to a KEDA scaler, for example pulling from a queue and running an execution per batch of messages, which gives you event-triggered batch processing that scales the number of concurrent executions to the backlog and stops when the work is gone.

The distinction between a job and a service with scale-to-zero is worth internalizing, because both can sit idle at zero cost and wake on an event. A service is meant to handle ongoing requests and stays up while there is traffic; a job runs a unit of work to completion and exits, with a defined retry and parallelism policy per execution. For a continuously consumed queue that backs an API, a service scaling on queue depth is natural. For a discrete task with a clear start and end, such as transcoding a file or running a scheduled cleanup, a job is the cleaner model because it expresses completion, retries, and parallelism directly. Jobs do not have ingress, so they are not subject to the per-request billing that applies to services, and they bill purely on the resources their executions consume while running.

```bash
# A scheduled job that runs nightly at 02:00 UTC.
az containerapp job create \
  --name nightly-report \
  --resource-group rg-apps \
  --environment prod-env \
  --trigger-type Schedule \
  --cron-expression "0 2 * * *" \
  --image myregistry.azurecr.io/report-runner:2.1.0 \
  --cpu 0.5 --memory 1.0Gi \
  --replica-timeout 1800 \
  --replica-retry-limit 2
```

### Observability: where the logs and metrics actually are

When something misbehaves, the answer is in two places, and knowing which is which saves real time. System logs record platform-level events about the app and its revisions: provisioning, scaling decisions, probe results, image pulls, and the lifecycle events that explain why a revision did or did not become healthy. Console logs (also called application logs) record whatever your container writes to standard output and standard error, which is your application's own logging. Both flow to the Log Analytics workspace the environment is wired to, where you query them with KQL, and the platform also offers a live log stream so you can watch a container's output in real time during a deploy or a reproduction.

The practical workflow for a failed revision is to look at the revision's state, then read the system logs to see whether the platform reports a pull failure, a probe failure, or a scheduling problem, and read the console logs to see whether the application itself crashed or logged an error on startup. A missing secret usually shows in the console logs as the application throwing on a null configuration value at boot; a wrong target port shows in the system logs as a probe that never connects; a pull failure shows in the system logs as an image pull error before the container ever runs. Metrics (replica count, request volume, CPU and memory usage, request latency) live in the metrics view and in the workspace, and they are how you confirm that a scale rule is firing as intended and that a new revision under a canary weight is behaving. Building the habit of reading the right log for the right symptom is most of what separates a quick fix from an afternoon of guessing.

```kql
// Console (application) logs for a specific revision, most recent first.
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == "orders-api"
| where RevisionName_s == "orders-api--v140"
| project TimeGenerated, Log_s
| order by TimeGenerated desc
```

## Tiers, Limits, and Quotas That Shape Design

The platform's pricing and capacity model is not a footnote; it shapes architecture, because it is the reason the service is attractive in the first place and the reason it is wrong for certain workloads.

### How is Azure Container Apps billed?

The consumption model bills two things: resource allocation, in vCPU-seconds and gibibyte-seconds for the time replicas are running, and requests, counting HTTP requests that arrive from outside the environment. A monthly free grant covers an amount of vCPU-seconds, gibibyte-seconds, and requests per subscription before charges begin. When an app scales to zero, no resource charges accrue. Confirm the current figures against the official pricing page, since they change.

The structural facts behind that summary are what matter for design. Under the consumption plan you are billed on a per-second basis for the resources your replicas are allocated while they run, measured in vCPU-seconds and gibibyte-seconds, plus a charge based on the number of requests your app receives. Crucially, only requests that originate outside the Container Apps environment are billable, and health probe requests are not billed, so internal service-to-service chatter inside one environment does not rack up request charges. There is a monthly free allowance per subscription for vCPU-seconds, gibibyte-seconds, and requests; the platform's published figures put that grant in the range of the first 180,000 vCPU-seconds, 360,000 gibibyte-seconds, and 2 million requests per month, but because Microsoft revises these values, treat them as numbers to verify at read time rather than fixed constants. When an app is scaled to zero, it allocates no resources and incurs no usage charge, which is the entire economic argument for the platform on spiky or intermittent workloads.

The dedicated plan changes the calculation. Instead of paying per running replica, you pay for provisioned workload profile instances, billed by the vCPU-seconds and gibibyte-seconds of the profile across its instances, plus a base management charge for the dedicated profile. The dedicated model wins when you have steady, predictable, high-throughput load where the consumption model's per-replica billing would cost more than reserving the compute, or when you need single-tenancy isolation or specialized hardware. The decision between them is a load-shape decision: bursty and intermittent favors consumption and scale-to-zero, steady and high favors dedicated.

There is a real cost trap hiding in scale-to-zero, and it is not a billing line. It is latency. An app at zero replicas has no warm instance, so the first request after an idle period pays a cold start while a replica is scheduled and the container starts. For a background queue processor that is irrelevant; for a user-facing API with a tight latency budget it can be unacceptable. The lever is `minReplicas`: setting it to one keeps a warm replica at the cost of paying for that replica around the clock, trading money for predictable latency. The full set of cold-start levers across Azure compute, ranked by impact, is the subject of [optimizing cold starts and warmup](/2024/10/07/azure-cold-start-optimization/); for this platform specifically the trade is direct, you are choosing between a zero-cost idle state with a cold first request and a small standing cost with a warm one.

### Scaling limits and resource boundaries

Each replica gets an allocation of vCPU and memory within bounds the platform enforces, and the ratio between CPU and memory is constrained, so you cannot allocate arbitrary combinations. The per-app maximum replica count is capped at a platform ceiling, and concurrency settings on the HTTP scale rule determine how many in-flight requests one replica handles before the platform adds another. All of these specific numbers move across platform versions and regions, so the engineering habit is to confirm the current values from the official limits documentation when you size a workload, and to design against the existence of the ceilings rather than against a memorized figure. The behavior to plan around is constant even when the numbers are not: replicas are bounded in size, the app is bounded in replica count, and concurrency tuning is how you control the relationship between load and replica count.

### Networking: virtual network integration, ingress scope, and egress

The environment is where networking is decided, and the workload profiles model gives you a meaningful network surface. You can deploy the environment into your own virtual network so the apps run on a subnet you control, which lets the platform participate in your private address space, reach private resources over service or private endpoints, and route egress through your network controls. An environment can be configured so that even its ingress is internal-only, meaning the apps are reachable from inside the virtual network and from peered networks but never from the public internet, which is the right posture for internal services and for apps fronted by a gateway or a firewall you operate.

Ingress scope and environment network type combine into the exposure model. An app with external ingress in a public environment gets a public hostname. An app with internal ingress is reachable only by siblings in the environment. An environment that is itself internal keeps even externally scoped apps off the public internet, exposing them only within the connected network. Getting this layering right is how you avoid the common exposure mistake of putting a service on a public endpoint when it only ever needs to be called by another service in the same system. For workloads with stricter requirements, the workload profiles environment supports private endpoints and egress firewall control, so inbound access can be locked to a private link and outbound traffic can be inspected or restricted rather than flowing freely to the internet. The general reasoning about when a private endpoint is the right control, and how its DNS resolution must be wired to work, is developed across this series' networking articles; for this platform the point is that the environment, not the individual app, is the unit at which you make those network decisions, so design the environment's networking before you start filling it with apps.

A subtle constraint that surprises teams is address space planning. The environment consumes IP space from its subnet for the platform's own components and for the replicas it schedules, and a busy environment scaling many apps to many replicas needs enough address space to grow into. Sizing the subnet too small caps how far the environment can scale regardless of your replica settings, and because changing the subnet of a running environment is not a trivial operation, this is a decision to get right at creation time. Plan the subnet for the environment's eventual scale, not its initial footprint.

### The cost levers worth pulling first

Within the platform, a handful of levers move the bill more than any others, and they rank cleanly by impact per unit of effort. The largest is the minimum replica count: an app held at one or more replicas around the clock pays for that capacity continuously, while the same app at a minimum of zero with an HTTP or event trigger pays nothing during idle stretches, so the single biggest cost decision is whether the workload's latency budget genuinely requires a warm replica or whether it can tolerate a cold start and ride scale-to-zero. The second is the maximum replica count and concurrency together, because an overly generous maximum combined with a too-low concurrency lets the app sprawl into far more replicas than the load requires, each one billed while it runs; tightening concurrency to match real per-replica capacity and capping the maximum at a defensible ceiling keeps the replica count honest. The third is right-sizing the per-replica vCPU and memory allocation, since over-allocating resources inflates the vCPU-seconds and gibibyte-seconds bill for every second every replica runs, and many apps are provisioned with more than they use out of caution. The fourth, for steady high-throughput apps, is moving off consumption to a dedicated profile where reserved compute beats per-replica billing. The general discipline of ranking cost levers by savings per hour of effort is the method this series applies across services; on this platform the order above is the one that pays.

## Configuration and Usage That Matters

A correct first deploy comes down to four settings that the defaults or the documentation make easy to get wrong: the target port, the ingress scope, the scale rule and replica range, and the registry authentication. Get those right and the app runs; get any one wrong and the revision either fails to provision or behaves unexpectedly.

The target port must match the port your process binds inside the container. The ingress scope (external versus internal) must match whether the app is meant to be public or only reachable by siblings. The scale rule must use a trigger compatible with your intent, an HTTP or event trigger if you want scale-to-zero, with `minReplicas` and `maxReplicas` set deliberately rather than defaulted. The registry authentication must be in place before the first pull, via a managed identity with AcrPull as shown above. Each change to these (other than secret values and a few revision-scope settings) mints a new revision, which is exactly what you want: the change is captured as an immutable snapshot you can roll toward or away from.

Making the configuration repeatable is the difference between a one-off and a production practice. The entire app definition expresses cleanly as infrastructure as code (Bicep, ARM, or Terraform), so the environment, the app, its scale rules, its ingress, and its identity and role assignments are version-controlled and reproducible rather than clicked together in the portal. The companion to this article is the place to run that end to end: you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to deploy a container app, split traffic across two revisions, watch it scale to zero and back, and reproduce the registry-pull and target-port failures in a sandbox so the diagnosis is muscle memory before you meet it in production.

### Tuning concurrency so replica count matches real capacity

The HTTP scale rule's concurrency setting is the lever most teams never touch and most need to. It tells the platform how many concurrent requests one replica should handle before another replica is added. Set it too low and the platform spins up replicas long before each is busy, overspending and fragmenting load; set it too high and each replica is overloaded, latency climbs, and the app scales too late to protect its tail latency. The right value is a property of your application measured under load, not a guess. An app that does light, fast work might comfortably handle many concurrent requests per replica; an app that does heavy synchronous work per request might saturate at a handful.

The procedure is empirical. Deploy with a starting concurrency, drive load with a known request rate, and watch two things in the metrics: the per-replica request latency and the replica count. If latency stays flat as load rises and the replica count tracks load smoothly, the concurrency is roughly right. If latency spikes before the platform adds replicas, the concurrency is too high and each replica is overloaded, so lower it. If the platform adds replicas while each is plainly underused, the concurrency is too low, so raise it. Because changing the scale rule mints a new revision, you can run this as a controlled experiment, holding a small traffic weight on the candidate concurrency while the incumbent serves the rest, and promote the value that holds latency steady at the lowest replica count.

```bash
# Set an HTTP scale rule with explicit concurrency, min, and max.
az containerapp update \
  --name orders-api \
  --resource-group rg-apps \
  --min-replicas 1 \
  --max-replicas 20 \
  --scale-rule-name http-concurrency \
  --scale-rule-type http \
  --scale-rule-http-concurrency 50
```

### A reproducible walkthrough: cause a 503, then fix it

The fastest way to internalize the revision-health model is to break it deliberately and watch the platform behave exactly as the model predicts. Deploy an app where the container listens on port 8080 but tell the ingress the target port is 9090. The deploy reports success, because creating the revision succeeds; the revision begins provisioning, its readiness probe (or the ingress connection check) cannot reach a listening port, the revision never reaches a healthy active state, and the public endpoint returns 503 because the ingress has no eligible revision to route to. Nothing here is mysterious once you hold the model: a revision must pass health to take traffic, and a port mismatch guarantees it cannot.

Now diagnose it the way you would in production. Run `az containerapp revision list` and observe the revision in a provisioning or failed state with zero healthy replicas and no traffic. Open the system logs in the workspace and find the probe or connection failures against port 9090. The signal names the cause. The fix is to align the target port with the real listening port, which mints a corrected revision; in single revision mode it replaces the broken one once healthy, and the 503 clears the moment the corrected revision goes active. Run the same exercise with a deliberately missing secret reference and you will see a different signature: the revision's replicas start but the container crashes on boot, the console logs show the application throwing on the missing configuration value, and the revision cycles without becoming healthy. Two different root causes, two different log signatures, one diagnostic habit. You can run both reproductions safely in a sandbox; the companion labs are built for exactly this kind of break-and-fix practice.

```bash
# Reproduce the 503: wrong target port (container listens on 8080).
az containerapp update \
  --name orders-api \
  --resource-group rg-apps \
  --target-port 9090

az containerapp revision list \
  --name orders-api \
  --resource-group rg-apps \
  --query "[].{name:name, active:properties.active, health:properties.healthState, replicas:properties.replicas, weight:properties.trafficWeight}" \
  --output table

# Fix: align the target port with the real listening port.
az containerapp update \
  --name orders-api \
  --resource-group rg-apps \
  --target-port 8080
```

### Managing revisions day to day

Working with revisions in practice comes down to a few operations you will run constantly, and naming them removes the mystery from the deployment lifecycle. Every revision has a name composed of the app name and a revision suffix, and supplying a meaningful suffix (a version, a build identifier) rather than accepting a generated hash makes the revision list readable at a glance, which matters when you are deciding where to send traffic under pressure. Listing revisions shows you what exists and their state; showing a single revision gives you its full configuration and health detail. Activating and deactivating revisions controls which ones are eligible to serve at all, separate from the traffic weights that apportion load among the active ones. Setting traffic weights is how you actually move load, and you can address a weight to a specific revision by name or, in workflows that use revision labels, to a stable label that you repoint at whichever revision should currently receive that slice.

The labels mechanism is worth understanding because it decouples a routing target from a specific revision name. A label such as a green or blue marker, or a staging marker, can be attached to a revision, and traffic or a test endpoint can be directed at the label rather than the underlying revision name. When you cut over, you move the label to the new revision, and everything pointing at the label follows without itself being reconfigured. That indirection is what makes a clean blue-green flow repeatable: you bring up the new revision, attach the staging label, exercise it through the label's endpoint, then shift production traffic and move the production label, retiring the old revision once the new one is proven. The discipline that keeps this safe is never deactivating the prior revision until the new one has demonstrably held under real traffic, because the prior revision sitting active and weighted at zero is your instant rollback, and a single weighting change returns to it without a rebuild.

```bash
# Show one revision's detail, then shift traffic between two revisions.
az containerapp revision show \
  --name orders-api \
  --resource-group rg-apps \
  --revision orders-api--v140

az containerapp ingress traffic set \
  --name orders-api \
  --resource-group rg-apps \
  --revision-weight orders-api--v140=90 orders-api--v141=10
```

A point that trips teams new to the model is which changes create a revision and which do not, because it determines whether a change rolls out through the traffic model or applies in place. Changes to the container image, the resource allocation, the scale rules, the environment variables, and similar template-scope settings produce a new revision, so they go through provisioning, health, and whatever traffic policy you have set, which is exactly the safety you want for a code or configuration change that could fail. Revision-scope changes such as a secret value or certain ingress settings apply across revisions without minting a new one, which is convenient for operations like rotating a credential but means the change is not gated by the revision health check. Knowing the category of a change before you make it tells you whether to expect a controlled rollout or an immediate effect, and prevents the surprise of a change that either did not create the revision you expected or created one you did not.

### Why does my container app return 503 right after a successful deploy?

Almost always the new revision never became healthy, so the ingress has nothing eligible to route to. The usual causes are a target port that does not match the listening port, a readiness probe that never passes, a failed image pull, or a missing secret crashing the container on start. Check `revision list` first.

## Failure Modes and How to Avoid Them

The platform fails in a small number of recognizable ways, and each maps to a confirming signal and a fix. Naming them is what turns a frustrating afternoon into a five-minute diagnosis.

A revision that will not activate is the most common. The platform refuses to send traffic to a revision until it provisions and passes health, so a stuck or failed revision is reporting that something prevented it from becoming ready. The signal is the revision's state in `az containerapp revision list` showing a failed or provisioning state rather than active, and the cause is named in the system and console logs in the environment's Log Analytics workspace. The root causes cluster into a short list: an image pull failure from a private registry, a startup or readiness probe that never succeeds, a target port the container does not listen on, or a missing secret or environment variable that crashes the process on launch. The fix is to read the logs, identify which of those it is, and correct that specific thing rather than redeploying the same broken image and hoping. The full triage, cause by cause, is the entire subject of [fixing Container Apps revision failures](/2023/02/13/fix-container-apps-revision-failed/).

The image pull failure deserves its own mention because it is the first-deploy classic. A private registry without a configured pull identity produces a pull error, the replica cannot start, and the revision fails. It is the same root cause as the AKS `ImagePullBackOff` family, and the registry-side fix is identical: grant the pull identity and the AcrPull role.

Ingress returning 503 while a revision is unhealthy is the symptom that masquerades as an ingress problem but is really a revision problem. The proxy has no healthy revision to route to, so it returns 503; the fix is upstream, in whatever is keeping the revision from becoming healthy, almost always the target port or a failing probe.

Cold starts after scale-to-zero are not a bug, they are the contract. An app at zero has no warm replica, so the first request pays the start latency. If that is unacceptable for the workload, set a minimum of one replica and accept the standing cost, or move to a plan and configuration that keeps capacity warm.

KEDA scaler authentication errors appear when a custom scale rule points at an event source (a Service Bus queue, say) but the authentication for the scaler is missing or wrong, so the platform cannot read the queue depth and the app does not scale on the event as intended. The fix is to supply the scaler's authentication correctly, usually as a secret reference the rule consumes, and to confirm in the system logs that the scaler is reading the source.

### Can a container app scale to zero with a CPU-based rule?

No. A CPU or memory rule needs a running replica to produce the metric it evaluates, so an app relying only on resource-based scaling idles at a minimum of one replica. True scale-to-zero requires an externally observable trigger, an HTTP rule the ingress can count, or an event-source rule like a queue, that the platform reads without a replica running.

## Two Misconceptions That Drive the Wrong Choice

Almost every poor decision about this platform traces to one of two misreadings, and engaging them directly is the fastest way to reason correctly about where it fits.

The first misreading is that Azure Container Apps is just hosted Kubernetes, so any team that wants Kubernetes-like behavior should reflexively reach for AKS and skip the managed service. The half-truth that fuels it is real: there is genuine Kubernetes underneath, KEDA is a Kubernetes project, and the scaling and rollout primitives are recognizably Kubernetes-shaped. But "powered by Kubernetes" and "is Kubernetes you operate" are different claims. You cannot reach the API server, apply arbitrary manifests, run controllers and operators, schedule pods by hand, choose and install a service mesh, or manage node pools and the scheduler. Those capabilities are precisely what AKS exists to give you and precisely what this platform deliberately withholds in exchange for taking the operational weight off your shoulders. So the correct reading is that the managed service covers the large majority of teams whose actual need is "run containers, scale them, roll them out safely," and that needing the Kubernetes control surface itself is the specific, identifiable signal that pushes a workload to AKS. Treating the hidden cluster as a reason to provision a visible one gets the logic backward.

The second misreading is the mirror image: that the platform is just App Service for containers, a minor variation on the PaaS you already know, with nothing distinctive to offer. The half-truth here is that both are managed and both run web workloads with low operational burden. But the revision-and-traffic-split model, event-driven scaling that reaches all the way to zero, the first-class KEDA and Dapr integration, and the container-native packaging are not how App Service frames a workload. App Service thinks in apps and deployment slots and a plan you pay for; this platform thinks in immutable revisions, weighted traffic, and replicas that bill per second and vanish at zero. The distinction matters most for two kinds of workload: bursty or intermittent ones, where scale-to-zero is a real economic advantage App Service does not match, and microservice fleets, where revisions, internal networking, KEDA event scaling, and managed Dapr remove plumbing App Service would leave you to build. Dismissing the platform as warmed-over App Service costs you those capabilities exactly when a workload needs them.

Place both misreadings on the decision table that follows and they resolve into a single axis. App Service, this platform, and AKS trade control against operational burden, and the honest question is never which one has the most features but how much of Kubernetes the workload genuinely needs and how much of its idle time should cost nothing. Answer those two and the choice is usually obvious.

## When to Use Azure Container Apps and When to Reach for an Alternative

This is the decision the whole article exists to make defensible, and it comes down to a single rule that names the deciding factor instead of comparing feature checklists.

**The no-cluster rule for Azure Container Apps: it gives you Kubernetes-style scaling, rolling revisions, and traffic splitting without a cluster to operate, so the only good reason to choose AKS over it is needing the Kubernetes API itself, not merely needing to run containers.** If your requirement is "run my containers, scale them on demand, roll out new versions safely, maybe scale to zero," that is precisely the platform's job and AKS is operational overhead you will pay for and not use. If your requirement genuinely reaches the Kubernetes API, custom operators and controllers, a specific service mesh, DaemonSets, privileged workloads, GPU scheduling beyond what the managed profiles offer, or fine-grained control over node pools and the scheduler, then you need the cluster and AKS is the right tool. The mistake is choosing AKS by default because the workload involves containers, when "containers" alone is satisfied by the managed service.

The other side of the rule guards against the opposite over-correction. If your workload is a single web app or API that does not even need containers as a portability or packaging requirement, App Service may be the lower-burden home, because it abstracts the container away entirely for many languages and asks even less of you. The platform sits in the middle on purpose: more control and more container-native primitives than App Service, far less operational burden than AKS.

The findable artifact below is the InsightCrunch container-host decision table. Read each row as a question about your workload, and let the deciding signal in the last column settle it.

| Dimension | App Service | Azure Container Apps | Azure Kubernetes Service (AKS) | Deciding signal |
|---|---|---|---|---|
| Cluster ownership | None; fully managed PaaS | None; managed substrate hidden from you | You own and operate the cluster, nodes, and upgrades | Do you want to operate Kubernetes at all? If no, App Service or Container Apps |
| Scale-to-zero | Limited; not the model | Yes, with an HTTP or event trigger | Possible only with added components, not native | Does the workload idle and need to cost nothing when idle? If yes, Container Apps |
| Per-use billing | Plan-based (you pay for the plan) | Per-second resource plus requests on consumption; zero when idle | Pay for nodes whether busy or idle | Is load bursty or intermittent? If yes, Container Apps consumption |
| Container-native rollout (revisions, traffic split) | App-level slots, not container revisions | First-class immutable revisions and weighted traffic split | You build it (Deployments, Services, a mesh) | Do you want canary and blue-green without building it? If yes, Container Apps |
| Dapr integration | Not built in | First-class, opt-in sidecar | Install and operate Dapr yourself | Do you want managed Dapr for microservices? If yes, Container Apps |
| Kubernetes API access | None | None | Full | Do you need the Kubernetes API, operators, or a chosen mesh? If yes, AKS |
| Operational burden | Lowest | Low | Highest | How much platform operations can the team absorb? Lower budget favors App Service or Container Apps |

A few recurring patterns show how the rule plays out in practice. A team with a single internal web app reaches for AKS because "that is where containers go," stands up a cluster, and spends more effort keeping the cluster healthy than building the app; the app would have run on App Service or this platform with no cluster at all, and the over-engineering is pure cost. A set of containerized microservices that call each other, scale on queue depth, and need safe rollouts fits this platform almost exactly: the environment gives them private internal networking, KEDA scales each on its own event signal, revisions give each safe canary deployments, and optional Dapr removes the cross-service plumbing, none of which requires the Kubernetes API. A platform team that genuinely needs cluster-level control, custom operators, a specific mesh, and fine node management has the one requirement that justifies AKS, and choosing it there is correct rather than over-engineering. A spiky workload that sits idle most of the day and bursts unpredictably is the textbook case for consumption with scale-to-zero, paying nothing through the quiet hours and absorbing the burst on demand. And a team migrating from App Service to containers, wanting more container-native control without taking on a cluster, lands naturally on this platform as the next step up the control axis rather than the leap to AKS. In each case the deciding factor is the same single question, and the workload's shape answers it.

The full three-way comparison, with the control-versus-burden reasoning developed in depth and more workload profiles mapped to a verdict, is the dedicated decision article on [App Service versus AKS versus Container Apps](/2025/04/21/app-service-vs-aks-vs-container-apps/). Before any of these hosts can run your code, the image has to be production-ready, stateless, and correctly built, which is the subject of [containerizing legacy apps for Azure](/2025/07/07/containerizing-apps-for-azure/); a container that holds local state or runs as root will disappoint on any of the three, and on a scale-to-zero platform especially, since replicas come and go constantly.

## How to Think About Azure Container Apps in One Paragraph

If you remember one thing, remember the position. Azure Container Apps is the managed middle: it hands you the scaling, the rolling revisions, the weighted traffic control, and the event-driven scale-to-zero that you would otherwise build on Kubernetes, and it bills to zero between requests, all without a cluster to patch, upgrade, or right-size. You give up direct access to the Kubernetes API and the full control that comes with it. So the design question is never "does this involve containers," which would point everything at a cluster, but "does this workload need the Kubernetes API itself." When the answer is no, the managed platform is the cheaper, calmer home, and reaching past it for AKS is the most common piece of over-engineering in the Azure container space.

## What the Platform Deliberately Does Not Give You

A fair deep dive names the boundaries as clearly as the capabilities, because the limits are where a wrong fit shows up. You do not get the Kubernetes API, so anything that depends on applying custom resources, running operators, or programming the scheduler is out of reach, and a workload built around those is an AKS workload wearing the wrong host. You do not choose or install your own service mesh; the platform's networking and the Dapr integration cover a large share of what teams want a mesh for, but a requirement for a specific mesh and its full feature set is a signal to use a cluster. You do not manage node pools, so workloads that need particular node types, taints and tolerations, or fine placement control beyond what the workload profiles offer will feel constrained. State is expected to live outside the replica, so a genuinely stateful workload that resists externalizing its state fights the platform's ephemerality and is better served elsewhere. And while the platform supports GPU-backed serverless options for inference and similar tasks, deep control over specialized hardware scheduling is the kind of thing a cluster gives you that the managed surface does not.

None of these are defects; they are the consequences of the trade that makes the platform attractive. The reason to enumerate them is that they convert a vague unease ("will this be enough?") into a checklist of concrete requirements you can test a workload against before committing. If a workload trips none of these limits, the managed platform is almost certainly the right home and a cluster is overhead you will not use. If it trips one or more in a way that is essential rather than incidental, that is the platform telling you the workload wants AKS, and listening to it early saves a migration later. The skill the series keeps returning to is matching the workload's real requirement to the host that meets it with the least burden, and naming the limits is how you do that matching honestly rather than discovering a wall after you have built against it.

## The Strategic Verdict

Azure Container Apps earns its place by collapsing the most common reason teams adopt Kubernetes (they have containers and want them scaled and rolled out safely) into a managed service that asks nothing operationally and costs nothing when idle. The platform is the correct default for containerized web apps, APIs, background processors, and microservices that do not require the Kubernetes control surface, and the consumption plan with scale-to-zero is close to unbeatable economically for spiky and intermittent load. Choose it deliberately by reasoning about the environment as your network boundary, revisions and traffic weights as your release mechanism, the trigger type as the gate on whether zero is reachable, and Dapr as an optional accelerant for genuine microservice fleets rather than a default. Reserve AKS for the workloads that truly program against Kubernetes, and reserve App Service for the simplest web workloads where even containers are more than the job needs. Decide on the workload's real requirement, not on the presence of the word "containers," and this platform will be the right answer far more often than the cluster you were about to provision.

One last framing helps the decision stick. The cost of choosing this platform when you later need AKS is a migration, which is real but bounded, because a well-built container with externalized state moves between hosts with modest effort. The cost of choosing AKS when this platform would have done is open-ended and recurring: every cluster upgrade, every node pool decision, every patch cycle, and every on-call page about cluster health is operational time spent on infrastructure the workload never required. Those costs compound quietly for the life of the system, which is why the default should lean toward the managed platform and why the burden of proof sits with the choice to run a cluster. Ask the workload to justify Kubernetes, not the other way around. When it cannot, take the calm, cheaper path, ship the container to a service that scales it, rolls it out safely, and bills to zero between requests, and spend the operational time you saved on the application instead of the platform. That is the whole argument for Azure Container Apps in a sentence: it gives you what most teams actually wanted from Kubernetes and asks for none of what they did not.

## Frequently Asked Questions

### Q: What is Azure Container Apps and what does it run?

Azure Container Apps is a managed, serverless platform for running Linux containers without operating a cluster. You provide a container image plus declarative configuration (resource allocation, ingress, scale rules, secrets), and the platform runs it as one or more replicas on a managed Kubernetes substrate you never administer. It scales replicas up and down on demand, including to zero, exposes the app over HTTP or TCP, and rolls new versions out as immutable revisions you can split traffic across. It embeds KEDA for event-driven scaling and offers an opt-in Dapr sidecar for distributed-application concerns. What it does not give you is access to the Kubernetes API, node-level control, or the ability to run arbitrary cluster components; those are deliberately hidden so the platform stays operationally hands-off. It runs the workload, you operate the app rather than infrastructure.

### Q: How does scale-to-zero work in Azure Container Apps?

Scale-to-zero means the platform removes all running replicas when there is no work, so you allocate and pay for nothing while idle. It works only when scaling is driven by a signal the platform can observe without a running replica: HTTP requests arriving at the managed ingress, or an event source such as a queue with messages waiting, both of which KEDA can read externally. Set `minReplicas` to zero and use one of those triggers, and the app drops to zero replicas during idle periods and spins a replica back up on the next request or event. The trade-off is the cold start: the first request after idle waits while a replica is scheduled and the container starts. A resource-based rule (CPU or memory) cannot reach zero, because the metric requires a live replica to measure, so such an app idles at a minimum of one. Choose the trigger to match whether reaching zero matters.

### Q: What is a Container Apps environment and why does it matter?

The environment is the shared security and network boundary for a group of container apps, the closest analog to a Kubernetes namespace plus its surrounding cluster networking. Apps in one environment share a virtual network, reach each other over stable internal DNS names with traffic staying private, write to the same Log Analytics workspace, and sit behind the same managed ingress layer. It matters because it is the unit of network design: co-locating microservices that call each other in one environment keeps their traffic internal, free of public exposure, and not subject to per-request billing, since only requests from outside the environment are billable. Newer environments default to the workload profiles model, which lets a single environment host both the serverless consumption profile and dedicated profiles, and adds virtual network features such as private endpoints and egress firewall control. Decide environment membership early; it is not a default to set and forget.

### Q: What is a revision in Azure Container Apps?

A revision is an immutable snapshot of a container app's configuration and image at a point in time. You do not edit a running app in place; instead, certain changes (a new image tag, a change to scale rules, resource allocation, or environment variables) mint a brand new revision, while a few revision-scope settings such as a secret value apply across revisions without creating one. Immutability is the whole point: because a revision cannot drift, you can route traffic toward and away from it with confidence. In single revision mode the platform keeps one active revision and replaces it on deploy; in multiple revision mode several revisions stay active at once and you assign each a traffic weight. A revision only becomes eligible for traffic after it provisions and passes health, which is why a broken deploy produces a 503 rather than routing requests to failing code. Inspect the live state with `az containerapp revision list`.

### Q: How does traffic splitting enable canary and blue-green deployments?

In multiple revision mode you keep more than one revision active and assign each a percentage of incoming traffic, and the managed ingress routes requests according to those weights. A canary release is a revision brought up holding a small slice, say five or ten percent, while the incumbent holds the rest; you watch the candidate's error rate and latency, then shift weight toward it as it proves itself, or pull it to zero if it misbehaves. Blue-green is the same mechanism with two revisions and a clean cutover. Because the split is declarative and weighted per revision, you get progressive delivery without deploying or maintaining an external load balancer or service mesh. The safety property is that weights only apply to healthy, provisioned revisions, so a candidate that fails to become ready never silently absorbs its share of traffic and starts returning errors; it stays out of rotation until it is genuinely serving.

### Q: What does the Dapr integration add to Azure Container Apps?

Dapr is a portable runtime for distributed-application concerns: service-to-service invocation with retries and mTLS, publish and subscribe messaging, pluggable state management, secrets access, and bindings to external systems. Container Apps injects the Dapr sidecar next to your container when you opt in, and your code calls local Dapr endpoints while the sidecar handles the distributed mechanics. The benefit is removing bespoke plumbing: instead of writing retry, timeout, and discovery logic in every service and every language, your service names a logical target and Dapr resolves and secures the call. Because component bindings (which broker backs a topic, which store holds state) live in configuration outside your code, you can swap backing infrastructure without recompiling. The honest caveat is that Dapr adds a sidecar, component definitions to manage, and a model to learn, so it is overkill for a single app and earns its place mainly for polyglot microservice fleets needing consistent invocation, messaging, and state.

### Q: When should I choose Azure Container Apps over AKS?

Choose Container Apps when your requirement is to run containers, scale them on demand, roll out versions safely, and possibly scale to zero, and choose AKS only when you genuinely need the Kubernetes API itself: custom operators and controllers, a specific service mesh, DaemonSets, privileged workloads, granular node pool and scheduler control, or GPU scheduling beyond the managed profiles. The deciding factor is not whether the workload involves containers, since both run containers; it is whether you must program against Kubernetes. Container Apps gives you Kubernetes-style scaling and rollout without a cluster to patch, upgrade, or right-size, so picking AKS by default because "it has containers" buys operational burden you will pay for and not use. If the workload never touches the cluster API, the managed platform is the calmer, cheaper home. The detailed three-way reasoning, including App Service, is developed in the dedicated comparison article this deep dive links to.

### Q: When is App Service a better fit than Azure Container Apps?

App Service is the better fit when the workload is a straightforward web app or API and containers are not themselves a requirement, because App Service can abstract the container away entirely for many supported languages and runtimes and asks even less of you operationally than Container Apps does. If you are deploying code rather than a custom image, do not need container-native rollout primitives like immutable revisions and weighted traffic splits, and do not need event-driven scale-to-zero, App Service is the lower-burden home. Container Apps becomes the better choice the moment you need a custom container image, want first-class revisions and traffic splitting, need scale-to-zero on bursty load, or want managed Dapr and KEDA for a microservices fleet. Think of it as a spectrum of control versus burden: App Service is the least of both, Container Apps the managed middle, and AKS the most of both. Match the workload's real needs to the right point on that spectrum.

### Q: Does Azure Container Apps run on Kubernetes?

Yes, internally it runs on a managed Kubernetes substrate, but that is an implementation detail rather than a surface you interact with. There is a real control plane and real nodes that Microsoft provisions, patches, upgrades, and operates, and you never see or touch them. You cannot reach the Kubernetes API, schedule pods directly, install arbitrary controllers, or choose your own service mesh; the platform exposes scaling rules, revisions, ingress, and Dapr and KEDA integration instead. This is the precise reason the "is it just hosted Kubernetes" framing is misleading: it is Kubernetes-powered without being Kubernetes-operated by you. If your design genuinely needs the cluster API and its extensibility, that need is exactly the signal to use AKS instead, where the cluster is a surface you program against rather than a hidden substrate.

### Q: How much does Azure Container Apps cost when idle?

On the consumption plan, an app scaled to zero replicas allocates no compute and incurs no resource charge, so an idle app's running cost on that dimension is nothing. You are billed for vCPU-seconds and gibibyte-seconds only while replicas are running, plus a charge for requests arriving from outside the environment, and there is a monthly free grant per subscription for resources and requests before charges begin. The economic catch is not a hidden charge but a latency one: an app at zero pays a cold start on the first request after idle, so if you set a minimum of one replica to keep it warm, you trade the zero idle cost for a small standing charge around the clock. Verify the current free-grant figures and per-unit prices against the official pricing page, since Microsoft revises them; the durable fact is that scale-to-zero genuinely means zero usage charge while idle.

### Q: What is the difference between the consumption and dedicated plans?

The consumption plan is serverless: you pay per second for the resources your replicas are allocated while running, plus requests, and you pay nothing when scaled to zero, which suits bursty or intermittent workloads. The dedicated plan reserves compute as workload profile instances and bills by the provisioned profile (its vCPU-seconds and gibibyte-seconds across instances) plus a base management charge, rather than per running replica, and it adds a single-tenancy guarantee and access to larger or specialized hardware. Dedicated wins when load is steady, predictable, and high enough that reserving compute costs less than per-replica consumption billing, or when isolation or specialized instances are required. In the newer workload profiles environment model, a single environment can host both, so different apps in the same environment can run on whichever plan fits, and you decide per app by the shape of its load rather than committing the whole environment to one model.

### Q: Can multiple container apps communicate privately within an environment?

Yes. Apps in the same environment can call each other over stable internal DNS names the platform assigns, with the traffic staying inside the environment's virtual network and never traversing the public internet. To make an app reachable only by its siblings, configure its ingress as internal rather than external, which exposes it on the internal endpoint without a public hostname. This internal reachability is why co-locating microservices that call each other in one environment is the sensible default: the calls are private, lower latency, and not subject to the per-request billing that applies only to traffic arriving from outside the environment. Splitting interdependent services across separate environments forces their traffic out to public ingress or through peered networking, which is slower, more exposed, and more expensive. Design environment membership around the call graph: services that talk to each other belong together.

### Q: What is the maximum number of replicas a container app can run?

There is a platform-enforced ceiling on the maximum replica count per app, and the configured `maxReplicas` value you set caps your app below that ceiling. The specific ceiling has increased across platform versions, so rather than memorize a number, confirm the current value from the official limits documentation when you size a workload, and design against the existence of a bound rather than a fixed figure. What matters for design is constant even when the number is not: each replica is bounded in vCPU and memory, the app is bounded in replica count, and the concurrency setting on your HTTP scale rule (how many in-flight requests one replica handles before another is added) is the lever that controls how quickly you approach your maximum under load. Set `maxReplicas` deliberately to bound cost and blast radius, and tune concurrency to match what one replica of your app actually handles well.

### Q: Do I need to manage TLS certificates for Azure Container Apps ingress?

For the default public endpoint the platform provides, ingress terminates TLS with a platform-managed certificate on the assigned hostname, so you do not manage a certificate to get HTTPS working out of the box. When you bind a custom domain, you supply or provision a certificate for that domain, and the platform supports managed certificate options to reduce that burden. The ingress proxy handles TLS termination in front of your container, so your application does not need to implement HTTPS itself; it listens on its plain target port and the proxy presents the encrypted endpoint to the outside world. Because the proxy is also the component that observes HTTP traffic, it both secures the endpoint and feeds the HTTP scale rule. The practical implication is that securing the public endpoint is largely handled for the default hostname, and custom domains add a certificate step you configure once.

### Q: How do I get my container app to pull an image from a private registry?

Grant the container app a managed identity and assign that identity the AcrPull role on the Azure Container Registry, so the platform authenticates the pull without any stored registry password. A system-assigned identity is the cleanest option for a single app: assign it, read its principal ID, and create a role assignment giving it AcrPull scoped to the registry, before the first deploy. If that identity is missing or under-privileged, the pull fails, the replica cannot start, and the revision fails to provision with an image pull error, which is the same root cause family as the AKS `ImagePullBackOff` problem. The fix is identical on the registry side: correct the identity and the role assignment. Avoid embedding registry usernames and passwords as secrets when an identity will do, since the identity approach removes a credential to rotate and leak. This series' managed-identity setup and registry-pull troubleshooting articles cover the exact steps.

### Q: Are Azure Container Apps suitable for stateful workloads?

The platform is built for stateless workloads, and you should externalize state rather than keep it inside a replica. Replicas are ephemeral by design: they are created and destroyed as the app scales, and on a scale-to-zero app they disappear entirely during idle periods, so any state written to a replica's local filesystem or held in its memory is lost when that replica goes away. The correct pattern is to push state to an external store (a database, a cache, blob storage, or a Dapr state component) so the container stays disposable while the state persists independently. The platform does offer storage mounts for cases that need shared or persistent volumes, but the architectural default remains stateless containers with externalized state. If a workload is inherently stateful in a way that resists externalizing, that is a signal to reconsider the design or the host, because fighting the ephemerality of replicas on a serverless platform is a losing battle.

### Q: What kinds of workloads is Azure Container Apps best suited for?

It fits containerized web apps and HTTP APIs, background and queue processors, event-driven microservices, and scheduled or event-triggered jobs, especially when load is bursty or intermittent and scale-to-zero saves real money. It is strong for microservice fleets that benefit from internal private networking, managed Dapr for service invocation and messaging, and KEDA scaling on event sources rather than CPU alone. It is a poor fit when you need the Kubernetes API and its extensibility (that is AKS), when the workload is a simple web app that does not need containers at all (App Service may be lower burden), or when a workload is inherently stateful in ways that resist externalizing state. The clean test is whether the workload needs to run containers with on-demand scaling and safe rollouts but does not need to program against a cluster; when that is true, this platform is usually the right answer and a cluster is over-provisioning.

### Q: Where do I find logs for an Azure Container Apps app?

Logs flow to the Log Analytics workspace the environment is connected to, and they come in two kinds you should keep separate in your head. System logs record platform-level events about the app and its revisions: provisioning, scaling decisions, probe results, image pulls, and the lifecycle events that explain why a revision did or did not become healthy. Console logs record what your container writes to standard output and standard error, which is your application's own logging. You query both with KQL in the workspace, and the platform also offers a live log stream to watch a container's output in real time during a deploy or reproduction. The diagnostic habit is to match the log to the symptom: a wrong target port or failing probe shows in the system logs as a connection or probe failure, while a missing secret or a startup crash shows in the console logs as the application throwing at boot. Reading the right one first is most of a fast diagnosis.

### Q: Can I run scheduled or batch jobs on Azure Container Apps?

Yes, through container apps jobs, which run a container to completion rather than keeping it alive to serve requests. A job supports three trigger types: manual, started on demand or by a pipeline; scheduled, run on a cron expression to replace a separate scheduler for periodic work; and event-driven, which starts executions in response to a KEDA scaler such as a queue, scaling concurrent executions to the backlog and stopping when the work is gone. Jobs differ from a service with scale-to-zero in that a job expresses completion, retries, and parallelism per execution, which fits discrete tasks with a clear start and end like transcoding a file or running a nightly cleanup, whereas a service keeps handling ongoing requests. Jobs have no ingress, so they are not subject to the per-request charge that applies to services and bill purely on the resources their executions consume while running. Choose a job when the work finishes; choose a service when it does not.

### Q: How do I roll back a bad release in Azure Container Apps?

Because revisions are immutable and the previous revision still exists, rollback is a traffic-weight change rather than a redeploy. In multiple revision mode you shift the traffic weight back to the known-good revision and away from the bad one, and the managed ingress immediately routes accordingly, so recovery is near-instant and does not require rebuilding or redeploying an image. In single revision mode you redeploy by activating the prior revision, which the platform retains. This is one of the strongest operational arguments for the platform: the safe-release machinery (canary, blue-green, instant rollback) is built into the revision and traffic model rather than something you assemble from a load balancer and deployment scripts. The practice that makes rollback reliable is keeping the previous revision active or readily activatable during a rollout, so the moment the new revision's metrics look wrong, returning traffic to the incumbent is a single weighting change.
