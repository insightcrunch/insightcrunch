---
layout: post
title: "Microservices on AKS: Reference Architecture"
page_title: "Microservices on AKS: A Reference Architecture for Ingress, Service Mesh, Sync vs Async Communication, Observability, Autoscaling, and Data per Service"
date: 2024-04-29
categories: ["Technology"]
tags: ["Azure", "AKS", "Microservices", "Architecture", "Kubernetes", "Cloud Computing"]
excerpt: "A microservices on AKS reference architecture: ingress, service mesh, sync versus async communication, observability, autoscaling, and private data per domain."
image: "/assets/images/blog/blog-02.webp"
reading_time: 61
author: "Insight Crunch Team"
last_updated: 2024-04-29
---

A microservices on AKS deployment usually starts well and then quietly turns into something worse than the monolith it replaced. The teams split the codebase along domain lines, package each piece as a container, and schedule it all onto Azure Kubernetes Service. For a few months the architecture diagram looks clean. Then one deploy of the orders component forces a coordinated release of three other components, a single slow downstream call takes the whole checkout path down, and nobody can answer why a request took four seconds because the trace stops at the first hop. The pieces are separate. The system is not.

That gap, between a set of separately deployed containers and a set of genuinely independent components, is what this reference architecture exists to close. The promise of the style is that each domain ships on its own schedule, fails on its own without dragging neighbors down, and scales to its own load. The reality is that those properties are not free. They come from a small number of design decisions made deliberately at the start, and they are lost the moment a shared database, an all-synchronous call chain, or a missing trace creeps in. The aim here is to give you a design you can reason about rather than a pile of parts you assemble and hope.

The central rule this article defends, and returns to at every layer, is what we will call the decouple-with-async-and-data rule: components stay independent only when they talk asynchronously wherever the work allows it and each one owns its own data. Break either half, share a database or wire everything as a blocking call, and you have built a distributed monolith, which carries the operational cost of distribution with none of the independence that was supposed to justify it. Everything below is an attempt to honor that rule concretely on Azure.

This is a reference architecture, not a tutorial for one app. It walks the layers you have to decide on, names the deciding question at each, and shows where Azure primitives fit. You will leave able to lay out the cluster, choose where calls go over HTTP and where they go over a queue, wire observability so a request is traceable end to end, set up scaling at both the pod and node level, and keep each domain's data private. If you want the cluster fundamentals underneath all of this, the deep dive on [Azure Kubernetes Service](/2022/01/17/azure-kubernetes-service-aks-explained/) covers the control plane, node pools, and networking model this design assumes you already have.

![Microservices on AKS reference architecture diagram showing ingress, service mesh, communication, observability, autoscaling, and data layers](/assets/images/blog/blog-02.webp)

## What the microservices pattern actually promises, stated plainly

Before the Azure parts, it helps to be precise about what the style is for, because most of the failures trace back to building it for the wrong reason. A microservices architecture decomposes an application into independently deployable components, each owning a discrete business capability, each running as its own process or set of processes, each free to be released, scaled, and operated on its own. The decomposition is along the seams of the business, not along technical layers. An orders domain, a payments domain, a catalog domain, an inventory domain: those are candidates. A "data access layer" or a "controllers layer" is not, because splitting there gives you the cost of distribution with the coupling of the monolith intact.

The benefit is organizational as much as technical. When each domain is owned by a team that can release it without a change-coordination meeting, throughput goes up and blast radius goes down. A bug in catalog rendering does not block a payments fix. A traffic spike on checkout does not require scaling the reporting jobs. That independence is the whole point, and it is the thing that gets eroded first.

### Why does the decomposition itself rarely cause trouble?

Splitting a codebase into components is the easy part and almost never where teams come to grief. The damage comes from how the pieces then relate: whether they share storage, whether they call each other synchronously in long chains, and whether a request can be followed across them. The boundaries are cheap; the relationships are where the architecture lives or dies.

The counter-reading worth taking seriously is that you may not need this style at all. A single well-structured deployable, a modular monolith, gives you most of the organizational clarity with a fraction of the operational tax. There is no network between modules, no distributed transaction problem, no separate database per concern to keep consistent, no tracing to stitch together. The honest position is that microservices buy independent deployment and independent scaling at the price of distributed-systems complexity, and you should only pay that price when the independence is worth more than the complexity costs. For a team of six shipping one product, it usually is not. For thirty teams shipping a platform, it usually is. The pattern is a response to organizational scale first and technical scale second.

When the answer is genuinely yes, AKS is a reasonable host because it gives you the scheduling, the rollout primitives, the horizontal scaling hooks, and the network policy surface that the style needs, without forcing you to operate the control plane yourself. The rest of this article assumes you have made that call deliberately and now want a layout that keeps the independence you paid for.

## The Azure building blocks that realize the pattern

A microservices design on AKS is assembled from a handful of Azure and Kubernetes primitives, and the architecture is mostly the set of decisions about how they fit. It is worth naming them up front so the reference design below reads as choices rather than magic.

The cluster itself provides the compute substrate: node pools of virtual machines, the Kubernetes scheduler placing pods onto them, and the kubelet keeping them alive. Each domain's component is packaged as a container image, stored in Azure Container Registry, and deployed as a Kubernetes Deployment with its own replica count, resource requests, and rollout strategy. Namespaces partition the cluster so that one domain's objects, quotas, and policies are isolated from another's.

Ingress brings outside traffic into the cluster and routes it to the right component. On Azure this is typically a managed ingress controller, with Application Gateway or an internal load balancer in front of it providing the public entry point and TLS termination. The ingress layer is the seam between the public internet and the private mesh of components, and getting its TLS and routing right is a prerequisite the configuration guide for [AKS ingress with TLS](/2023/05/22/configure-aks-ingress-tls/) covers in the depth it deserves.

An optional service mesh sits between components inside the cluster. Azure offers the Istio-based service mesh add-on, an officially supported integration that injects a sidecar proxy alongside each pod and intercepts the traffic between them. The mesh gives you mutual TLS between components without code changes, fine-grained traffic control such as canary splits and retries, and a uniform source of telemetry. It is genuinely useful and genuinely a cost, and the decision of whether to adopt it is one of the load-bearing choices in this design.

Asynchronous communication runs over messaging primitives rather than direct calls. Azure Service Bus provides queues and topics with ordering and dead-lettering, and Azure Event Hubs or Event Grid handle higher-volume event streams. These let one component hand work to another without waiting for it, which is the mechanical basis of the decoupling the namable rule demands. The patterns for using them well are the subject of the dedicated treatment of [async messaging patterns on Azure](/2024/06/24/azure-async-messaging-patterns/), and this architecture leans on them heavily.

Observability is provided by Azure Monitor, the managed Prometheus offering for metrics, Container Insights for logs and container telemetry, and a distributed tracing backend, with Managed Grafana as the dashboard surface. In a distributed design these are not optional extras. They are the only way to understand a system whose behavior is spread across a dozen processes and a network.

Scaling happens at two layers. The Horizontal Pod Autoscaler adjusts the replica count of a component based on metrics, the Kubernetes Event-driven Autoscaler extends that to event sources such as a queue depth, and the cluster autoscaler or node autoprovisioning adds and removes the underlying virtual machines so the pods have somewhere to run. The interaction between these is covered end to end in the piece on [AKS autoscaling](/2024/08/12/aks-autoscaling-explained/), and the reference design wires them together.

Data per component is realized with one managed data store per domain: an Azure SQL database here, a Cosmos DB container there, a Redis cache for one, a blob container for another, each owned exclusively by the component that needs it. The rule that no two components share a store is the second half of the namable claim, and it is enforced by discipline and network boundaries rather than by any single Azure feature.

### How do these primitives map onto the decoupling rule?

Two of the building blocks carry the rule directly. Messaging gives components a way to communicate without blocking on each other, which delivers the async half. A private data store per domain delivers the data half. The mesh, ingress, observability, and scaling layers are supporting structure that lets the decoupled components be operated, secured, and grown safely.

## The InsightCrunch AKS microservices reference

The findable artifact at the heart of this article is a layered reference you can hold in your head and apply to any AKS microservices design. Each layer names what it provides and the single deciding question that determines how you configure it. The table is the map; the prose after it walks each layer in the order a request and a design actually flow.

| Layer | What it provides | The deciding question |
|-------|------------------|-----------------------|
| Ingress | Public entry, TLS termination, host and path routing into the cluster | Where does outside traffic stop being public and start being internal? |
| Service mesh (optional) | mTLS between components, retries, traffic splitting, uniform telemetry | Is the mTLS and traffic control worth the per-pod proxy and operational overhead yet? |
| Communication | The wiring between components: HTTP/gRPC for sync, messaging for async | Does the caller need the answer now, or only that the work will happen? |
| Observability | Metrics, logs, and end-to-end distributed traces across components | Can you follow one request across every hop it touches? |
| Autoscaling | Pod-level scaling on load or events, node-level capacity to back it | What signal should drive scale, and is there room to grow onto? |
| Data | One private store per domain, owned and accessed by one component | Does any two components reach into the same store? If yes, they are coupled. |

This is the InsightCrunch AKS microservices reference. The deciding questions are the part worth memorizing, because they are the questions that, answered honestly, keep a design on the right side of the decouple-with-async-and-data rule. The sections below take each layer in turn, walk a concrete configuration, and name the failure that follows from getting the deciding question wrong.

## The cluster layout: namespaces, ingress, and where public stops

The first decisions shape everything after them: how the cluster is partitioned, how traffic enters, and where the boundary between the public internet and the internal component graph sits. Get this layer right and the rest has a clean foundation. Get it wrong and you end up with components that can reach anything, traffic that bypasses your controls, and a security posture that is impossible to reason about.

### Partitioning the cluster with namespaces

Each business domain gets its own namespace. This is not cosmetic. A namespace is the unit that resource quotas, network policies, and role bindings attach to, so a per-domain namespace lets you cap a domain's memory and CPU, restrict which other domains it can talk to, and grant a team rights over its own objects and nothing else. The orders team operates in the orders namespace, owns the Deployments and Services there, and cannot accidentally redeploy payments.

A minimal namespace with a resource quota looks like this:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: orders
  labels:
    domain: orders
    istio-injection: enabled
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: orders-quota
  namespace: orders
spec:
  hard:
    requests.cpu: "8"
    requests.memory: 16Gi
    limits.cpu: "16"
    limits.memory: 32Gi
    pods: "50"
```

The quota matters because in a shared cluster one runaway domain can starve the others. With a hard cap on requests, the orders namespace can consume at most its allotment, and the scheduler refuses to place pods that would exceed it. That refusal is a signal, not a failure: it tells you the domain has outgrown its budget and the budget needs a deliberate increase rather than a silent overrun.

Network policy is the second reason namespaces earn their keep. By default, every pod in a Kubernetes cluster can reach every other pod, which means a compromise of one component is a foothold against all of them. A default-deny policy per namespace, with explicit allowances for the traffic that should flow, turns that flat network into a segmented one:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: orders
spec:
  podSelector: {}
  policyTypes:
    - Ingress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-ingress-controller
  namespace: orders
spec:
  podSelector:
    matchLabels:
      app: orders-api
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8080
```

With this in place the orders API accepts traffic only from the ingress controller's namespace, and everything else inside the cluster is refused at the network layer unless a policy explicitly permits it. That is defense in depth: even if an attacker lands in one pod, the network does not hand them the rest of the cluster.

### Where does outside traffic stop being public?

The deciding question for this layer is where the public internet ends and the internal graph begins. The answer should be a single, well-guarded seam: the ingress controller, fronted by a load balancer that terminates TLS. Outside that seam, everything is public and untrusted; inside it, traffic is internal and subject to mesh and network policy. A request that reaches a component without crossing that seam is a hole.

The ingress controller is the reverse proxy that maps a hostname and path to a component. A request to `shop.example.com/api/orders` lands on the controller, which routes it to the orders Service, which load-balances across the orders pods. The controller is the only component with a public address; the rest have cluster-internal addresses only. An Ingress resource expresses the routing:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: shop-ingress
  namespace: orders
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - shop.example.com
      secretName: shop-tls
  rules:
    - host: shop.example.com
      http:
        paths:
          - path: /api/orders
            pathType: Prefix
            backend:
              service:
                name: orders-api
                port:
                  number: 8080
```

A real production note belongs here, and it is one to re-verify against current Azure documentation before you publish your own infrastructure. The community Ingress NGINX project entered retirement in 2026, and Microsoft's managed application routing add-on that wrapped NGINX is on a published support timeline rather than an open-ended one. Microsoft's recommended direction for new clusters is the application routing add-on built on the Kubernetes Gateway API, which runs a lightweight Istio control plane to manage gateway infrastructure. The architectural role does not change: you still need a single guarded seam where public traffic terminates and routing into the cluster begins. What changes is the specific controller you choose to fill that role, so treat the controller as a slot in the design and pick the currently supported occupant when you build. The Gateway API model, with its separation of the gateway from the routes that bind to it, also maps more cleanly onto a multi-team cluster, since a platform team can own the gateway while each domain team owns its own routes.

The failure that follows from getting this layer wrong is subtle. If components are reachable on public addresses individually, or if some path skips the ingress controller, then your TLS, your authentication at the edge, and your rate limiting all have a bypass. The discipline is that there is exactly one front door, it terminates TLS, and nothing inside the cluster is exposed except through it.

## The service mesh layer: power you should defer until you need it

A service mesh is the most over-adopted piece of a microservices architecture, and the discipline around it is mostly about restraint. The Istio-based add-on for AKS is a capable, officially supported integration, and it solves real problems. It also taxes every pod with a sidecar proxy, adds a control plane to operate and upgrade, and inserts a layer that you now have to understand when you debug. The deciding question is whether the problems it solves are problems you actually have yet.

### What the mesh gives you

The mesh injects a proxy alongside each pod and routes all inter-component traffic through those proxies. Because the proxies sit on both ends of every call, they can do three categories of work without any change to your application code.

The first is mutual TLS. The proxies negotiate certificates and encrypt traffic between components, and they verify the identity of the caller, so a component can require that the traffic it accepts comes from an authenticated peer rather than anything that can reach its port. In a cluster where you have already applied network policy, mesh mTLS adds identity on top of reachability: not just "can this pod reach me" but "is this pod who it claims to be." Enabling strict mTLS for a namespace is a single policy object once the add-on is installed:

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: orders
spec:
  mtls:
    mode: STRICT
```

The second is traffic control. The proxies can split traffic between two versions of a component by weight, which is the mechanism behind canary releases and blue-green cutovers. They can retry failed calls, set timeouts, and inject faults for testing. A canary that sends a tenth of orders traffic to a new version is expressed declaratively:

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: orders-api
  namespace: orders
spec:
  hosts:
    - orders-api
  http:
    - route:
        - destination:
            host: orders-api
            subset: stable
          weight: 90
        - destination:
            host: orders-api
            subset: canary
          weight: 10
```

The third is telemetry. Because every call passes through a proxy, the mesh emits a uniform set of metrics, logs, and trace spans for inter-component traffic regardless of the language each component is written in. This is the strongest argument for a mesh in a polyglot estate: you get consistent golden-signal telemetry without instrumenting each component by hand.

### Is the mesh worth the overhead yet?

The deciding question is honest and uncomfortable. The mesh's mTLS, traffic splitting, and uniform telemetry are valuable, but each can be obtained another way at smaller scale, and the sidecar tax is real. For a handful of components, network policy plus library-level retries plus application tracing may be enough, and a mesh is premature.

The cost is concrete. Every pod gains a sidecar container that consumes memory and CPU and adds a hop of latency to every call. The control plane is another system to monitor and to keep compatible with your cluster version, since each mesh revision supports a range of Kubernetes versions and you upgrade them in a coordinated dance. When something breaks, the proxy is now in the path and you have to know whether the fault is in your component, the proxy, or the mesh configuration. None of this is prohibitive, but it is not free, and adopting it before you have the scale or the polyglot spread to justify it means paying the tax without collecting the benefit.

The pattern to follow is to defer the mesh until a specific need names it: you have enough components that per-pair mTLS and identity matter, you have a polyglot estate where uniform telemetry would otherwise mean instrumenting many languages, or you need weighted traffic control for safe releases and the alternatives have become awkward. Adopt it then, namespace by namespace, using the injection label so you can onboard domains incrementally rather than flipping the whole cluster at once. The premature-mesh failure is one of the recurring ones engineers report: a small system carrying a mesh it does not need, where the proxy layer is now a source of incidents rather than a solver of them.

## The communication layer: synchronous versus asynchronous, and why the choice decides everything

This is the layer where the namable claim is won or lost. How components talk to each other determines whether a slow or failed dependency stays contained or cascades, whether one domain's deploy forces another's, and whether the system behaves like a set of independent parts or a single brittle whole. The first half of the decouple-with-async-and-data rule lives here: communicate asynchronously wherever the work allows it.

### Synchronous calls: HTTP and gRPC, and what they cost

A synchronous call is a request the caller blocks on until it gets an answer. The orders component calls the pricing component over HTTP or gRPC, waits, and uses the result to finish handling the user's request. This is the obvious way to wire components together because it mirrors a function call, and that familiarity is exactly the trap.

Synchronous calls are the right tool when the caller genuinely needs the answer to proceed and needs it now. A checkout request needs the current price before it can total the cart. A login needs the identity check before it can issue a session. In these cases the user is waiting, the answer is required, and there is no honest way to defer it. HTTP with JSON is the lingua franca; gRPC over HTTP/2 is the better choice for internal high-frequency calls because it is binary, multiplexed, and has a typed contract through protocol buffers, which catches mismatches at build time rather than in production.

The cost of synchronous calls is coupling in the temporal dimension. When orders calls pricing synchronously, orders is only as available as pricing, only as fast as pricing, and only as scalable as pricing. If pricing is down, orders fails. If pricing is slow, orders is slow. This is acceptable for one hop. It becomes dangerous as a chain.

### How does a synchronous chain cascade into a full outage?

Picture a request that enters orders, which calls pricing, which calls inventory, which calls a tax component, each synchronously. The user-facing latency is the sum of every hop, and the availability is the product of every component's availability. If inventory slows to two seconds, the whole chain takes at least two seconds, and threads pile up waiting all the way back to the edge. One slow leaf takes the trunk down.

The arithmetic is unforgiving. Four components each at 99.9 percent availability, called in a synchronous chain, give a combined availability of roughly 99.6 percent, because the failures multiply rather than mask each other. Add more hops and it gets worse. The thread-exhaustion mechanics are sharper still: each in-flight request holds a thread and a connection while it waits, so when one component slows, the callers fill their thread pools with blocked requests, stop accepting new work, and the slowness propagates upstream until the edge itself is unresponsive. This is the cascading-failure pattern, and it is the single most common way a microservices system fails in production. The architecture did not remove the monolith's fragility; it spread it across a network and added latency.

The containment tools for unavoidable synchronous calls are timeouts, retries with backoff, and circuit breakers, which stop a caller from hammering a dependency that is already down. Those resilience patterns deserve their own treatment and have one, but they are mitigation, not a cure. The cure is to not make the call synchronous in the first place when the work does not require it.

### Asynchronous communication: messaging and the decoupling it buys

An asynchronous interaction is one where the caller hands off the work and does not wait for it to complete. The orders component, having captured an order, publishes an event saying the order was placed, and returns to the user immediately. The inventory, shipping, and notification components consume that event on their own schedule and do their part. Orders does not know who is listening and does not wait for them.

This is the mechanical basis of decoupling. Because orders does not block on inventory, inventory can be slow, can be briefly down, can be redeployed, can scale independently, and none of it affects whether a user can place an order. The message sits durably in a queue or a topic until inventory is ready to process it. The temporal coupling that made the synchronous chain brittle is gone, replaced by a durable buffer that absorbs the difference in speed and availability between producer and consumer.

On Azure, the two main shapes are queues and topics. Azure Service Bus provides both: a queue is point to point, where one message is processed by one consumer, suited to commands like "charge this card"; a topic is publish and subscribe, where one published message fans out to many subscriptions, suited to events like "an order was placed" that several domains care about. Service Bus gives you ordering through sessions, at-least-once delivery, and dead-lettering for messages that cannot be processed, which is the safety net for poison messages. For high-volume telemetry-style streams, Event Hubs is the better fit, and Event Grid handles reactive routing of discrete events. The selection among them, and the delivery-guarantee and idempotency concerns that come with messaging, are exactly what the dedicated piece on async messaging patterns works through, and a serious design reads it alongside this one.

A consumer that processes order-placed events from a Service Bus topic, written against the Azure SDK, has this shape:

```csharp
var client = new ServiceBusClient(fullyQualifiedNamespace, credential);
var processor = client.CreateProcessor(
    topicName: "orders",
    subscriptionName: "inventory",
    new ServiceBusProcessorOptions
    {
        MaxConcurrentCalls = 10,
        AutoCompleteMessages = false
    });

processor.ProcessMessageAsync += async args =>
{
    var body = args.Message.Body.ToString();
    var orderPlaced = JsonSerializer.Deserialize<OrderPlaced>(body);

    // Idempotent: safe to run twice for the same order id.
    await inventory.ReserveStock(orderPlaced.OrderId, orderPlaced.Items);

    await args.CompleteMessageAsync(args.Message);
};

processor.ProcessErrorAsync += args =>
{
    logger.LogError(args.Exception, "Failed processing order event");
    return Task.CompletedTask;
};

await processor.StartProcessingAsync();
```

Two details in that snippet carry the whole pattern. The message is completed only after the work succeeds, so a crash mid-processing leaves the message in the queue to be retried rather than losing it. And the work is idempotent, because at-least-once delivery means the same message can arrive twice, so reserving stock for an order id that is already reserved must be a no-op rather than a double reservation. Idempotency is not optional in an asynchronous design; it is the price of the durability that makes the design resilient.

### Does the caller need the answer now, or only that the work will happen?

That is the deciding question for the communication layer, and it sorts almost every interaction cleanly. If the caller needs the result to continue and the user is waiting on it, the call is synchronous and you accept the coupling for that one hop. If the caller only needs the work to eventually happen, and can return to the user before it does, the interaction is asynchronous and you publish a message instead. Most interactions in a well-designed system fall into the second category once you look honestly: notifying, updating a projection, reserving stock, sending a receipt, updating a search index. They feel synchronous only because the monolith did them inline.

The discipline that follows is to default to asynchronous and justify synchronous, rather than the reverse. Every synchronous call is a thread of coupling you are choosing to keep; make the choice deliberately and keep the chains short. A design where the only synchronous calls are the ones the user is genuinely blocked on, and everything else flows over messages, is a design where one component's trouble stays one component's trouble. That is the decouple-with-async half of the rule, made concrete.

It also reshapes how you handle consistency. Once work is asynchronous, you give up the illusion of an immediate, globally consistent state and accept eventual consistency: the order is placed now, the inventory reflects it a moment later, the search index a moment after that. This is a feature, not a defect, because the alternative, a distributed transaction spanning components, reintroduces the tight coupling you were trying to escape. The pattern for multi-step workflows across components is the saga, a sequence of local transactions each emitting an event that triggers the next, with compensating actions to undo earlier steps if a later one fails. The saga keeps each step owned by one component and each component's data private, which is precisely where the data half of the rule comes in.

## The observability layer: making a distributed system legible

A monolith is debuggable with a stack trace and a log file because the whole request runs in one process. A distributed design throws that away. One request now touches the ingress controller, the orders component, a message on a topic, the inventory consumer, and a database call, across separate processes on separate nodes. Without deliberate observability, a question as basic as "why was this request slow" has no answer, because the evidence is scattered and uncorrelated. Observability is not a dashboard you add at the end; it is a first-class layer you design in, and the reference treats it as such.

The three pillars are metrics, logs, and traces, and a distributed system needs all three because each answers a different question. Metrics tell you that something is wrong and roughly where: error rate climbing, latency at the ninety-ninth percentile rising, a queue backing up. Logs tell you what a single component did at a moment: the exception, the input that triggered it, the decision it made. Traces tell you how a single request moved across components: which hops it took, how long each took, and where it stalled. Miss any one and you are debugging with a hand tied.

### Metrics: the golden signals per component

On AKS the managed Prometheus offering scrapes metrics from your components and the cluster, and Managed Grafana renders them. The metrics that matter most are the golden signals, tracked per component: request rate, error rate, latency distribution, and saturation of the resources the component depends on. For an asynchronous consumer, queue depth and message age join the set, because a consumer that is keeping up shows a shallow, stable queue and a consumer that is falling behind shows a queue that grows without bound.

A component exposes these on a metrics endpoint, and a scrape configuration or a pod annotation tells Prometheus to collect them:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders-api
  namespace: orders
spec:
  template:
    metadata:
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      containers:
        - name: orders-api
          image: myregistry.azurecr.io/orders-api:1.4.2
          ports:
            - containerPort: 8080
            - containerPort: 9090
```

The discipline with metrics is to alert on symptoms the user feels, not on causes you guess at. An alert on rising error rate or rising user-facing latency fires when something the user cares about is wrong; an alert on high CPU may or may not matter. Per-component golden-signal dashboards, with alerts on the request-facing signals, give an on-call engineer the "something is wrong, and it is over there" that points them at the right component before they open a single log.

### Logs: structured and correlated

Logs in a distributed design must be structured and must carry a correlation identifier, or they are noise. Structured means each log line is a set of fields, not a sentence, so you can query for "all log lines for this order id across all components." The correlation identifier is the thread that ties a request's log lines together across the components it touched. When the ingress controller stamps an incoming request with a trace identifier and every component propagates it into its logs, you can pull the full story of one request out of a sea of unrelated lines.

Container Insights collects container stdout and stderr into a Log Analytics workspace, where a query language lets you filter and join across components. The pattern that makes this work is propagation: each component reads the trace identifier from the incoming request or message, attaches it to every log line it writes, and passes it to every downstream call or published message. Without propagation, logs are per-component islands; with it, they are a single searchable record of the system's behavior.

### Can you follow one request across every hop it touches?

That is the deciding question for observability, and distributed tracing is what makes the answer yes. A trace is the record of one request as it flows across components, made of spans, where each span is one unit of work, one component handling one hop, with a start time, a duration, and a parent. Stitched together, the spans form a tree that shows the request entering at the edge, fanning out across components, and where the time went.

The mechanism is context propagation. The edge generates a trace identifier, and each component reads the incoming trace context, creates a child span for its own work, and injects the context into any call or message it sends onward. The components instrument themselves with OpenTelemetry, the vendor-neutral standard, and export spans to a backend such as Application Insights, where you can open a single trace and see the whole request laid out as a waterfall. When a request is slow, the trace shows exactly which span ate the time, which turns "the system is slow" into "the inventory database call in this component took 1.8 seconds," which is an actionable diagnosis rather than a shrug.

The failure that follows from skipping tracing is the one engineers report most often about distributed systems: debugging becomes archaeology. A request was slow, or failed, and the only evidence is disconnected log lines in five components with no way to know which lines belonged to that request or in what order the hops happened. Teams without tracing spend hours reconstructing what a single trace would have shown in seconds. The cost of instrumenting tracing up front is small; the cost of not having it, paid every incident, is large. In a polyglot estate this is also the strongest standalone argument for the service mesh, since the mesh can emit spans for inter-component hops without each language being instrumented by hand, though application-level spans still need OpenTelemetry inside each component to see what happens within a hop.

A component configured to export traces and propagate context, sketched in code, makes the shape clear:

```python
from opentelemetry import trace
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

trace.set_tracer_provider(TracerProvider())
exporter = AzureMonitorTraceExporter(connection_string=APPINSIGHTS_CONNECTION)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(exporter))

# Outgoing HTTP calls now propagate trace context automatically.
RequestsInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

def reserve_stock(order_id, items):
    with tracer.start_as_current_span("reserve_stock") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("items.count", len(items))
        # The database call below is a child span; its duration shows in the trace.
        return inventory_db.reserve(order_id, items)
```

With every component doing this, the trace identifier born at the edge flows through synchronous calls in HTTP headers and through asynchronous messages in message properties, and the backend reassembles the full tree. That continuity across the asynchronous boundary is the part teams most often miss: a trace that stops when an order-placed event is published, and a separate disconnected trace when the inventory consumer picks it up, hides the very handoff you most need to see. Propagating the context into the message and reading it back out on consumption keeps the request whole.

## The autoscaling layer: pod scaling and node capacity, working together

Independent scaling is half the reason to adopt this style, so the architecture has to make each component scale on its own load without manual intervention, and it has to ensure there is underlying capacity for the scaled pods to run on. Those are two distinct layers, and conflating them is a common source of confusion. Pod scaling changes how many replicas of a component run. Node scaling changes how many virtual machines the cluster has. Both must be wired, and they cooperate: pod scaling creates demand, node scaling supplies the capacity to meet it.

### Pod scaling: the Horizontal Pod Autoscaler and KEDA

The Horizontal Pod Autoscaler adjusts a component's replica count based on a metric, most commonly CPU or memory utilization against the resource requests you set. When average CPU across the orders pods rises above the target, the autoscaler adds replicas; when it falls, it removes them. The control loop reads metrics roughly every fifteen seconds and the underlying kubelet reports utilization on its own cadence, so scaling reacts within a minute or so rather than instantly, which is worth knowing when you tune it. A basic autoscaler on CPU is short:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orders-api
  namespace: orders
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: orders-api
  minReplicas: 3
  maxReplicas: 30
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 65
```

CPU is a fine signal for a request-serving component, but it is the wrong signal for an asynchronous consumer. A consumer draining a Service Bus queue is not CPU-bound; it is bound by how many messages are waiting. Scaling it on CPU means it stays at minimum replicas while the queue grows to thousands of messages, because draining a queue slowly does not spike CPU. The right signal is the queue depth itself, and that is what the Kubernetes Event-driven Autoscaler provides.

KEDA, available as a managed AKS add-on, extends pod scaling to event sources. It watches an external metric, a Service Bus queue length, an Event Hubs lag, a Kafka topic offset, and scales the consumer to match. Its defining capability over plain CPU scaling is scaling to zero: when the queue is empty, KEDA can take the consumer down to no replicas, and bring the first one up the instant a message arrives, which removes the cost of idle consumers entirely for spiky workloads. Under the hood KEDA creates and feeds a Horizontal Pod Autoscaler object, so it complements rather than replaces the metrics-driven model, and the guidance is to let KEDA own a given workload rather than pointing both at the same Deployment. A consumer scaled on Service Bus queue depth is expressed as a ScaledObject:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: inventory-consumer
  namespace: inventory
spec:
  scaleTargetRef:
    name: inventory-consumer
  minReplicaCount: 0
  maxReplicaCount: 50
  triggers:
    - type: azure-servicebus
      metadata:
        topicName: orders
        subscriptionName: inventory
        messageCount: "20"
      authenticationRef:
        name: keda-servicebus-auth
```

With `messageCount` at twenty, KEDA targets roughly twenty messages per replica, so a backlog of four hundred messages drives the consumer toward twenty replicas, and an empty queue drives it to zero. The asynchronous consumer now scales on the thing that actually loads it, which closes the loop the synchronous design could not.

### Node scaling: cluster autoscaler and node autoprovisioning

Pod scaling is useless if there is nowhere to put the new pods. When the autoscaler asks for fifteen more replicas and the nodes are full, those pods sit in a Pending state, scheduled to nothing, until capacity appears. Node scaling supplies that capacity. The cluster autoscaler watches for pods that cannot be scheduled for lack of resources and adds nodes to the node pool to fit them, then removes nodes when they sit underused. It is the native, well-worn mechanism on AKS, tightly integrated and dependable, with the one caveat that adding a node means provisioning a full virtual machine, which takes minutes, so node scaling is slower than pod scaling and you size your buffers accordingly.

A newer option, node autoprovisioning based on the open-source Karpenter project, takes a different approach: rather than scaling fixed node pools of identical machines, it looks at the resource shape of the pending pods and provisions right-sized machines to fit them, choosing the virtual machine type and count to match real-time demand. This can be more efficient for heterogeneous workloads where a one-size node pool wastes capacity, and it has been maturing on AKS, so its support status is one to confirm against current documentation when you design. The architectural point holds regardless of which you pick: there must be a node-scaling mechanism behind the pod-scaling one, or pod scaling stops at the edge of the cluster's fixed capacity.

### What signal should drive scale, and is there room to grow onto?

The deciding question for this layer has two parts, one per sub-layer. For pod scaling, the signal must match how the component is actually loaded: utilization for request servers, queue depth for asynchronous consumers, a custom business metric where neither fits. For node scaling, there must be headroom and a mechanism to extend it, so that scaled pods land on real capacity rather than queueing in Pending. Answer both and a load spike on checkout grows the checkout component on the right signal and grows the cluster underneath it, while the reporting jobs and the catalog component sit untouched. That selective, signal-driven elasticity is the independent-scaling property the style promised, delivered.

The interplay is where it gets interesting, and the dedicated autoscaling deep dive walks it in full, but the short version is that the layers form a chain: a load signal drives the pod autoscaler, which requests replicas, which the scheduler tries to place, which, failing for lack of room, triggers the node autoscaler, which adds capacity, which lets the pending replicas schedule. A break anywhere in that chain shows up as a component that will not grow under load, and tracing the break to its layer, pod metric, scheduler, or node capacity, is a routine diagnosis once you know the chain exists.

## The data layer: one private store per domain, and why sharing one breaks everything

The second half of the namable rule is the one teams violate most quietly, because violating it is so convenient. Each component owns its data exclusively. No two components read or write the same database. A component that needs another domain's data asks for it through that domain's interface or learns it through an event, never by reaching into its store. This is the data-per-domain rule, and it is the difference between an architecture that can evolve and one that has fused into a distributed monolith with extra network hops.

### Why a shared database recreates the monolith

When two components share a database, they are coupled through the schema whether or not they call each other. The orders component cannot change its table layout without checking that the reporting component, which reads those tables directly, still works. A migration becomes a coordinated multi-team event. A bad query from one component locks rows the other needs. The independent deployment the whole style was built to deliver is gone, because a schema change in shared storage ripples to every component that touches it. The components look separate on the architecture diagram and behave as one in practice, which is the precise definition of a distributed monolith: the operational cost of many deployables with the change-coupling of one.

The shared-database coupling is seductive because it is the path of least resistance. The data is right there; a join is easier than an API call or an event subscription; the deadline is today. Every shortcut of this kind is a thread sewing two components back together, and a system accumulates them until a "microservices" architecture has a single database at its center that every component depends on, at which point none of the independence properties hold and the team wonders why deploys are still coordinated and failures still cascade.

### Owning data on Azure: the right store per domain

The discipline is one private managed store per component, chosen to fit that component's access pattern. Azure gives you a range, and matching the store to the domain is part of the design rather than a default. A transactional domain with relational integrity needs lands on Azure SQL Database. A domain with high write throughput, flexible schema, and global distribution needs reaches for Cosmos DB, where the partition-key choice governs how it scales. A domain that needs a fast cache or ephemeral state uses Azure Cache for Redis. A domain handling large objects uses blob storage. The point is not which store but that the store belongs to exactly one component, sized and scaled and backed up on that component's terms, with credentials that no other component holds.

Access is enforced, not merely agreed. Each component authenticates to its own store with a managed identity scoped to that store and nothing else, so even if a developer is tempted to point the reporting component at the orders database, the credentials do not exist to let them. Combined with the network policy from the cluster layer, which can block a component from even reaching another domain's data endpoint, the data boundary is defended by identity and network rather than by a comment in a design document. Discipline that depends on everyone remembering the rule fails; discipline enforced by absent credentials and a closed network port holds.

### How does a component get data it does not own?

If components cannot share a store, the obvious question is how one gets data another owns, and there are two honest answers. The first is to ask the owner: a synchronous query to the owning component's API when the caller needs the current value right now and is blocked on it. The second, and the one that keeps decoupling intact, is to listen: the owning domain publishes events when its data changes, and the interested component maintains its own local copy, a read model, built from those events and shaped for its own queries. The reporting component does not query the orders database; it subscribes to order events and builds the reporting view it needs in its own store.

This is the same eventual-consistency trade the communication layer asked you to accept, applied to data. The read model lags the source by the time it takes an event to propagate, usually milliseconds to seconds, and in exchange the reporting component can query its own optimized copy without touching the orders domain at all, can be down without affecting orders, and can reshape its read model without asking anyone. The pattern is materialized views driven by events, and it is how a strict data boundary stays practical rather than paralyzing. When a single user action must update several domains' data consistently, the saga from the communication section orchestrates it as a sequence of local transactions, each within one component's own store, each emitting the event that triggers the next, with compensating transactions to roll back if a later step fails. No step ever reaches across the boundary, so the boundary survives even complex workflows.

### Does any two components reach into the same store?

That is the deciding question, and it admits a one-word audit. Walk the connection strings. If two components hold credentials to the same database, they are coupled, and the architecture is one shared schema away from the distributed monolith no matter how clean the container diagram looks. The fix is to give the second component its own store and feed it through events or an API, never a second set of credentials to the first component's database. A design that passes this audit, where the connection strings partition cleanly and each store has exactly one owner, has earned the data half of the decouple-with-async-and-data rule, and with the communication half it has the independence the whole effort was for.

## Deploying components independently without breaking each other

Independent deployment is the headline benefit of the style, but it is a property you have to engineer rather than one you get for free by putting components in separate pipelines. The mechanics live in two places: how a single component rolls out without dropping requests, and how two components keep talking while one of them changes shape.

A component rolls out as a Kubernetes rolling update by default, replacing old pods with new ones a few at a time while keeping the Service endpoint serving throughout. For that to be safe, the new pods must be ready before they receive traffic and the old pods must drain their in-flight work before they stop, which is what readiness probes and graceful termination provide. A rollout that ignores these drops requests at every deploy, which quietly undermines the availability the architecture is supposed to improve. The rollout strategy is set on the Deployment so the control plane never takes too many pods down at once:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders-api
  namespace: orders
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  minReadySeconds: 10
```

With `maxUnavailable` at zero, the cluster brings up a new pod and waits for it to pass readiness before retiring an old one, so capacity never dips below the desired count during a deploy. That single setting turns a deploy from a brief availability dip into a non-event, which is what makes deploying ten times a day across many domains safe rather than scary.

### How do components keep talking while one of them changes?

The answer is contract discipline: a component may change freely behind its interface, but the interface itself evolves only in backward-compatible ways, adding optional fields rather than renaming or removing existing ones, so that callers built against the old shape keep working against the new one. A breaking change is rolled out as a new version that coexists with the old until callers migrate.

This matters because the whole point of independent deployment is that the orders team can ship without coordinating with the four teams that call it. That holds only if orders does not break the contract those callers depend on. The practical rule is that contracts are append-only within a version: you add an optional field, you tolerate fields you do not recognize, and you never repurpose or remove a field that a caller might read. When a genuinely incompatible change is unavoidable, you expose it as a new endpoint or a new message schema version alongside the old, announce a deprecation window, and retire the old shape only after telemetry confirms no caller still uses it. The same discipline applies to messages: an event's schema grows by adding optional fields, and consumers ignore fields they do not know, so a producer can enrich an event without forcing every consumer to redeploy in lockstep. Contract versioning is the unglamorous discipline that makes the glamorous property, independent deployment, actually true in practice rather than only on the diagram.

The failure to watch for is the lockstep deploy: a change to one component's interface that forces a coordinated release of its callers, which is independent deployment lost. When you find yourself needing to deploy several components together, treat it as a signal that a contract was broken rather than evolved, and look for the append-only path that would have let each side move on its own schedule.

## Keeping components healthy: probes, limits, and graceful shutdown

Operability is a layer the reference assumes even though it cuts across the others, because a distributed system multiplies the number of processes that can be unhealthy and the architecture only delivers its resilience if each component reports its health honestly and fails cleanly.

Every component declares a liveness probe and a readiness probe, and the distinction is load-bearing. The liveness probe answers whether the process is alive or wedged, and a failing liveness probe causes the kubelet to restart the pod, which recovers a deadlocked process automatically. The readiness probe answers whether the process is ready to serve right now, and a failing readiness probe removes the pod from the Service endpoints without restarting it, which is exactly what you want when a component is alive but temporarily unable to serve, such as during startup or while a dependency it needs is briefly unavailable. Conflating the two, using a liveness probe that fails when a downstream dependency is down, causes the pod to restart pointlessly and can turn a small dependency blip into a restart storm. The probes are declared per container:

```yaml
livenessProbe:
  httpGet:
    path: /healthz/live
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /healthz/ready
    port: 8080
  periodSeconds: 5
resources:
  requests:
    cpu: 250m
    memory: 256Mi
  limits:
    cpu: "1"
    memory: 512Mi
```

The resource requests and limits in that block are not boilerplate. The request is what the scheduler uses to place the pod and what the autoscaler measures utilization against, so an absent or wrong request breaks both placement and scaling. The memory limit is what protects a node from one component's leak taking down its neighbors, since a container that exceeds its memory limit is terminated rather than allowed to consume the node. Sizing these per component, from observed usage rather than guesses, is part of keeping the cluster stable as load shifts between domains.

Graceful shutdown closes the loop. When a pod is told to stop, during a deploy, a scale-down, or a node drain, it receives a termination signal and a grace period before it is killed. A component that handles this correctly stops accepting new work, finishes the requests and messages already in flight, closes its connections, and then exits, so no request is dropped and no message is half-processed. A component that ignores the signal and is killed mid-work drops whatever it was doing, which for a synchronous request is a failed call the user sees and for an asynchronous message is a redelivery that the consumer's idempotency must absorb. Graceful shutdown is the operational counterpart to readiness: readiness keeps traffic off a pod that is not ready, and graceful shutdown drains traffic off a pod that is going away, and together they make the constant churn of a scaling, deploying cluster invisible to the user.

## The trade-offs and failure modes the design has to handle

A reference architecture earns trust by naming what it costs and how it breaks, not by promising it is free. Microservices on AKS carry real, recurring failure modes, and the layers above are arranged specifically to contain them. Naming them as patterns, each with the design choice that addresses it, is more useful than a generic warning.

The distributed-monolith failure is the master failure that the others feed into: components that are deployed separately but cannot change, fail, or scale separately because they share a database or call each other synchronously everywhere. The design choice against it is the namable rule itself, applied at the data layer and the communication layer together. Every other discipline in this article is downstream of avoiding this one outcome.

The cascading-failure pattern is the synchronous chain taking the whole path down when one link slows, through latency summation and thread exhaustion. The design choice is to default to asynchronous communication and contain the synchronous calls that remain with timeouts, retries with backoff, and circuit breakers, keeping the blocking chains short and the user-facing path resilient to a slow leaf.

The premature-mesh pattern is a small system carrying a service mesh it does not yet need, paying the sidecar tax and the control-plane operational cost without the scale or polyglot spread that would justify them. The design choice is to defer the mesh until a specific need names it and to onboard it namespace by namespace when that need arrives, rather than as a default first move.

The missing-trace pattern is a distributed system with no end-to-end tracing, where every incident becomes archaeology across disconnected logs. The design choice is to instrument distributed tracing as a first-class layer, propagate context across both synchronous calls and asynchronous messages, and never let a trace stop at a component boundary.

The shared-database pattern is the data-layer version of the master failure: two components coupled through a schema, where a migration is a multi-team event and the independence properties quietly die. The design choice is one private store per component, enforced by managed identity and network policy, with cross-domain data delivered through events and read models rather than shared credentials.

The runaway-scaling pattern is the inverse of the elasticity the style promised: a component that will not grow under load because it scales on the wrong signal, or grows but lands its pods in Pending because there is no node capacity behind the pod autoscaler. The design choice is to match the scaling signal to the real load, queue depth for consumers, utilization for request servers, and to back pod scaling with a node-scaling mechanism so there is room to grow onto.

Each of these is something engineers report hitting in production, and each maps to a specific layer and a specific deciding question in the reference. That is the value of holding the layered map: when a symptom appears, it tells you which layer to inspect and which question you may have answered wrong.

## A request's journey through the reference design

It helps to walk a single user action through every layer, because the layers only matter in how they combine. Take a customer placing an order, and follow it.

The request arrives at `shop.example.com/api/orders` over TLS. It hits the load balancer, terminates TLS at the ingress controller, and the controller routes it by host and path to the orders Service, which load-balances across the orders pods. The public-to-internal seam has been crossed exactly once, at a single guarded door. The edge stamps the request with a trace identifier, which will follow it everywhere.

Inside, the orders component does the minimum the user is blocked on. It validates the cart and needs the current prices to total it, so it makes one synchronous gRPC call to the pricing component, blocking only on the answer the user genuinely cannot proceed without. That call carries the trace context in its headers, so the pricing work shows as a child span in the same trace. If the mesh is enabled, that call is mutually authenticated and encrypted by the sidecar proxies without the orders code knowing. With the price in hand, orders writes the order to its own private Azure SQL database, the only component with credentials to that store.

Then orders does the decoupled part. Rather than synchronously calling inventory, shipping, and notifications and waiting on all three, it publishes a single order-placed event to a Service Bus topic, injecting the trace context into the message properties, and returns success to the customer. The user's request is done in the time it took to price and persist, not the time it would take every downstream domain to react.

The event fans out. The inventory subscription delivers it to an inventory consumer, which KEDA has scaled to match the queue depth, possibly from zero if the shop was quiet. The consumer reserves stock idempotently in its own store and completes the message only on success, so a crash mid-work redelivers rather than loses. The shipping subscription and the notifications subscription each get their own copy and act independently, one scheduling a dispatch, one sending a receipt. Each reads the trace context from the message and continues the same trace, so the full fan-out shows in one tracing waterfall, the synchronous pricing hop and the asynchronous inventory, shipping, and notification hops all stitched to the order that began at the edge.

If inventory is briefly down during all this, nothing the customer saw is affected; the message waits durably until the consumer recovers, then processes. If checkout traffic spikes, the orders pods scale on utilization and the consumers scale on queue depth, and the cluster adds nodes underneath them, while the catalog and reporting domains sit at their baseline. If a developer later changes the inventory store's schema, no other component breaks, because no other component touches that store. Every property the style promised, independent failure, independent scale, independent change, is visible in this one request, and each traces to a specific layer of the reference. That is what the architecture is for.

## When the pattern fits, and when it is overkill

A reference architecture that never tells you to walk away is marketing. Microservices on AKS is the right answer for a specific situation and the wrong one for many others, and naming the boundary is part of the design.

The pattern fits when organizational scale demands it. The clearest signal is many teams that need to ship independently and are currently blocked by each other in a shared codebase or a coordinated release train. When a release means a meeting to align ten teams, when one team's bug blocks another's fix, when the deploy cadence is throttled by the slowest contributor, the independent-deployment property is worth real money, and that is the property microservices deliver first. Technical signals reinforce it: domains with genuinely different scaling profiles, where checkout needs to scale ten times under a sale while reporting does not, or domains with different availability and data needs that a single deployable serves poorly. When several of these hold at once, the distributed-systems tax buys something worth more than it costs.

The pattern is overkill when the independence is not yet worth the complexity. A small team on one product almost always ships faster as a modular monolith: one deployable, one database with clean module boundaries, no network between modules, no distributed transactions, no tracing to stitch, no per-domain store to keep eventually consistent. The modular monolith gives you most of the design clarity, clear domain seams in the code, for a fraction of the operational load, and it leaves the door open: well-drawn module boundaries are exactly the seams along which you later extract components if and when scale demands it. Starting with microservices for a team that does not have the scale to justify them is the most expensive common mistake in this space, because you pay the full distributed-systems tax up front and collect the independence benefit never, since there are not enough teams to need it.

There is an operational cost that rarely shows up in the initial enthusiasm and dominates the running total later. A distributed design multiplies the number of things that can break and the number of places to look when they do. Each component is a pipeline to maintain, a set of dashboards to watch, an on-call surface, a dependency graph to keep compatible, and a store to back up and patch. The failure modes that do not exist in a single process, partial failures where some components are up and others down, network partitions between components, eventual-consistency windows where two components briefly disagree, retries that duplicate work, become everyday concerns that the team must design for and reason about. Testing gets harder too, because a behavior that emerges from the interaction of several components cannot be exercised by a unit test of any one of them, and a realistic test needs the messaging, the data stores, and the network in the loop. None of this is a reason to avoid the style when scale demands it, but all of it is cost that a team without that scale pays in full while collecting little in return.

The honest framing is that microservices are a solution to a scaling problem, organizational first and technical second, and applying them in the absence of that problem imports the cost without the payoff. The decision rule is to ask whether the independent deployment and independent scaling are worth more, today, than the complexity of a distributed system, and to default to the modular monolith until the answer is a confident yes. When it is a confident yes, this reference is how you build the distributed version without recreating the monolith you left.

## How to evolve the design over time

An architecture is a living thing, and the reference is a starting layout that you grow as the system and the team grow. The evolution path matters as much as the initial design, because most systems arrive at microservices rather than starting there, and most that start there started too large.

The common and recommended starting point is a modular monolith with strong internal boundaries, where each future domain is a module with its own data access confined to its own tables and its interactions with other modules going through interfaces rather than shared internals. This gives the organizational clarity early and, when a module's scaling or team-ownership needs diverge enough to justify extraction, that module becomes the first component to leave, carrying its tables into its own store and its interface into an API and events. Extracting along boundaries you already drew is far cheaper than discovering the boundaries while pulling a tangled codebase apart.

As components multiply, the layers of the reference come online in a natural order. Observability comes first and early, because you cannot operate even a few distributed components blind, and retrofitting tracing after the fact is painful. Asynchronous communication comes as soon as you have interactions that do not need an immediate answer, which is most of them, because it is the decoupling that makes adding components safe. Per-component data is non-negotiable from the first extraction, since the whole reason to extract is to own the data. Autoscaling per component arrives when load profiles diverge enough that uniform scaling wastes money or misses spikes. The service mesh comes last, deferred until the count of components, the polyglot spread, or the need for fine traffic control names it, and onboarded incrementally rather than all at once.

The discipline through all of it is to keep checking the deciding questions of the reference as the system changes. A new interaction prompts the communication question: does the caller need the answer now, or only that the work happens. A new component prompts the data question: does it share a store with anyone. Growth in load prompts the scaling question: is the signal right and is there room to grow. The architecture stays healthy not because it was drawn correctly once but because each change is checked against the same small set of questions that keep it on the right side of the namable rule. A system that drifts, that lets a shared store creep in here and an all-synchronous chain there, decays into the distributed monolith one convenient shortcut at a time, and the antidote is the recurring, deliberate audit against the layered reference.

For the hands-on side, the place to build and observe a design like this is [the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), where you can stand up an AKS cluster, deploy components across namespaces, wire Service Bus messaging between them, enable the mesh add-on, and watch the inter-component behavior in metrics and traces, which is how the layers stop being abstract and start being something you have actually run.

## The verdict: independence is bought, not assumed

The single thing to carry away is that the properties that justify microservices, independent deployment, independent failure, independent scale, do not come from chopping a codebase into containers and scheduling them on a cluster. They come from two deliberate disciplines held at the same time: components communicate asynchronously wherever the work allows, and each component owns its data privately. That is the decouple-with-async-and-data rule, and the moment either half lapses, through an all-synchronous call chain or a shared database, the architecture reverts to a distributed monolith that costs more than the monolith it replaced and delivers less.

The layered reference is the operational form of that rule. Ingress gives one guarded seam between public and internal. The mesh, deferred until it is earned, adds identity and traffic control across components. The communication layer chooses synchronous only where the caller is actually blocked and asynchronous everywhere else. Observability makes the distributed system legible through metrics, correlated logs, and traces that survive every hop. Autoscaling matches each component's scaling signal to its real load and backs it with node capacity. Data stays private per domain, enforced by identity and network rather than by good intentions. Each layer has a deciding question, and answering those questions honestly, at design time and again at every change, is what keeps the system on the right side of the rule.

For most teams the more valuable verdict is the one about when not to do this at all: start as a modular monolith, draw the domain boundaries cleanly in code, and extract components only when organizational or technical scale makes the independence worth the distributed-systems tax. When that day comes, build the distributed version against this reference, layer by layer and question by question, and you get the independence you paid for instead of a monolith wearing a cluster as a disguise.

## Frequently Asked Questions

### Q: What is a microservices reference architecture on AKS?

A microservices reference architecture on AKS is a layered design that turns separately deployed containers into genuinely independent components. It names six layers and the deciding question at each: ingress for the public-to-internal seam, an optional service mesh for inter-component identity and traffic control, a communication layer that chooses synchronous or asynchronous wiring, an observability layer for metrics, logs, and traces, an autoscaling layer at both pod and node level, and a data layer with one private store per component. The point of the reference is not a fixed product list but a set of decisions you make deliberately. Holding the map lets you reason about a design rather than assembling pieces blindly, and it gives you a fixed place to look when a symptom appears, since each common failure maps to one layer and one question you may have answered wrong.

### Q: How do ingress and a service mesh fit together on AKS?

They sit at different boundaries. Ingress is the seam between the public internet and the cluster: a controller fronted by a load balancer terminates TLS and routes external requests by host and path to the right component, and it should be the single guarded door through which all outside traffic enters. A service mesh, by contrast, governs traffic between components already inside the cluster, adding mutual TLS, retries, and weighted traffic splitting through sidecar proxies. Ingress is essentially always present because something has to accept external traffic. The mesh is optional and should be deferred until its mTLS, uniform telemetry, or traffic control is genuinely needed, because every pod pays a sidecar tax and the control plane is another system to operate. In short, ingress handles north-south traffic at the edge, the mesh handles east-west traffic between components, and you add the mesh only once the scale justifies its overhead.

### Q: When should microservices communicate synchronously versus asynchronously?

The deciding question is whether the caller needs the answer now or only needs the work to eventually happen. Use a synchronous call, HTTP or gRPC, when the user is blocked on the result and the caller cannot proceed without it, such as fetching a price before totaling a cart. Use asynchronous messaging, a queue or a topic, when the caller only needs the work done eventually and can return before it completes, such as updating inventory or sending a receipt after an order is placed. The default should be asynchronous, with synchronous calls justified individually, because every synchronous call couples the caller to the callee's availability and latency. Long synchronous chains cause cascading failures through latency summation and thread exhaustion, while asynchronous messaging decouples components so one can be slow or briefly down without affecting the others. Most interactions are asynchronous once examined honestly.

### Q: How do I add observability and distributed tracing to microservices on AKS?

Treat observability as a first-class layer designed in from the start, not a dashboard added at the end. Collect metrics with the managed Prometheus offering and render them in Managed Grafana, tracking the golden signals per component plus queue depth and message age for consumers. Send structured logs carrying a correlation identifier to a Log Analytics workspace through Container Insights, so you can query one request's lines across every component it touched. Add distributed tracing with OpenTelemetry inside each component, exporting spans to a backend such as Application Insights, and propagate the trace context across both synchronous calls in HTTP headers and asynchronous messages in message properties. The critical discipline is continuity: a trace must survive the asynchronous handoff rather than stopping when an event is published and restarting disconnected when it is consumed. With propagation in place, one trace shows a request's full journey as a waterfall and turns a vague slowness into a precise diagnosis.

### Q: How do I scale microservices on AKS at both the pod and node level?

Scaling happens in two cooperating layers. At the pod level, the Horizontal Pod Autoscaler adjusts replica count based on a metric, with CPU or memory utilization suiting request-serving components. For asynchronous consumers, the right signal is queue depth rather than CPU, so the Kubernetes Event-driven Autoscaler watches an event source like a Service Bus queue and scales the consumer to match, including scaling to zero when the queue is empty. At the node level, the cluster autoscaler adds virtual machines when pods cannot schedule for lack of capacity and removes them when nodes sit idle, while node autoprovisioning based on Karpenter can provision right-sized machines to fit pending pods. Pod scaling creates demand and node scaling supplies capacity, so both must be wired or scaled pods sit in a Pending state. Match the pod signal to how the component is actually loaded, and ensure there is room to grow onto.

### Q: How do I handle data per service in a microservices architecture?

Each component owns its data exclusively in its own managed store, and no two components share a database. A component that needs another domain's data either queries that domain's API synchronously when it needs the current value immediately, or subscribes to the owning domain's events and maintains its own local read model shaped for its queries. Enforce the boundary with managed identities scoped so each component holds credentials only to its own store, and with network policy that blocks reaching another domain's data endpoint, so the rule is defended by absent credentials rather than by good intentions. The reason the rule matters is that a shared database couples components through the schema: a migration becomes a multi-team event and independent deployment dies. Audit the design by walking the connection strings, and if two components reach the same store, give the second its own and feed it through events instead.

### Q: What is a distributed monolith and how do I avoid one?

A distributed monolith is a system whose components are deployed separately but cannot be changed, scaled, or failed independently, because they are coupled underneath. It carries the full operational cost of distribution, the network, the separate processes, the tracing, with none of the independence that was supposed to justify that cost. The two coupling mechanisms that create it are a shared database, which couples components through a schema so a migration ripples across teams, and pervasive synchronous calls, which couple components in time so one slow dependency drags down the chain. You avoid it by holding both halves of the decouple-with-async-and-data rule: communicate asynchronously wherever the work allows and give each component its own private store. The distributed monolith is the master failure that the other common failures feed into, and every discipline in the reference architecture exists to keep a design from drifting into it one convenient shortcut at a time.

### Q: Do I always need a service mesh for microservices on AKS?

No, and adopting one too early is a common mistake. The mesh provides genuine value, mutual TLS between components, weighted traffic splitting for safe releases, and uniform telemetry across a polyglot estate, but each pod gains a sidecar proxy that costs memory, CPU, and a hop of latency, and the control plane is another system to monitor and keep version-compatible. For a small number of components, network policy plus library-level retries plus application-level tracing often covers the same ground without the overhead. Defer the mesh until a specific need names it: enough components that per-pair identity matters, a polyglot spread where uniform telemetry would otherwise mean instrumenting many languages by hand, or a need for traffic control the alternatives handle awkwardly. When that day comes, onboard it namespace by namespace using the injection label rather than flipping the whole cluster at once, so you adopt the capability incrementally where it earns its place.

### Q: How does a saga keep data consistent across microservices?

A saga coordinates a workflow that spans several components without a distributed transaction, which would reintroduce the coupling microservices exist to avoid. Instead of one atomic transaction across stores, a saga is a sequence of local transactions, each committed within one component's own store, where each step emits an event that triggers the next step in another component. If a later step fails, the saga runs compensating transactions to undo the earlier steps, leaving the system in a consistent state without ever locking data across components. For example, placing an order commits locally and emits an event, reserving stock commits locally in the inventory store and emits its own event, and charging payment follows; if payment fails, a compensating action releases the reserved stock. The saga preserves both halves of the namable rule, because every step is asynchronous and every step touches only its own component's data, so even a complex multi-domain workflow never reaches across a data boundary.

### Q: Why do synchronous call chains cause cascading failures?

Because synchronous calls couple components in time, and that coupling compounds along a chain. When a component calls another and blocks on the reply, it is only as available and as fast as that dependency. Chain several such calls, where component A calls B calls C calls D, and two things go wrong at once. Latency sums, so the user-facing time is the total of every hop, and availability multiplies, so four components each at 99.9 percent give a combined figure near 99.6 percent because failures stack rather than mask. Worse, each in-flight request holds a thread and a connection while it waits, so when one component slows, its callers fill their thread pools with blocked requests, stop accepting new work, and the slowness propagates upstream until the edge itself is unresponsive. One slow leaf takes the whole tree down. The structural fix is to default to asynchronous communication; the tactical containment for unavoidable synchronous calls is timeouts, retries with backoff, and circuit breakers.

### Q: What is the difference between a queue and a topic in Azure Service Bus?

A queue is point to point: one message is delivered to and processed by a single consumer, which suits commands where exactly one handler should act, such as charging a specific card. A topic is publish and subscribe: one published message fans out to many independent subscriptions, each of which gets its own copy, which suits events that several domains care about, such as an order being placed that inventory, shipping, and notifications all react to. Both provide durable storage so a message survives until processed, at-least-once delivery so you must make consumers idempotent, and dead-lettering so a message that cannot be processed is set aside rather than blocking the queue. Choose a queue when one and only one component should handle each message, and a topic when an event is a fact that multiple components independently respond to. The topic is usually the better fit for the event-driven decoupling a microservices architecture relies on.

### Q: Should I start a new project with microservices or a monolith?

For most teams, start with a modular monolith and extract components later. A small team on one product ships faster as a single well-structured deployable: there is no network between modules, no distributed transactions, no per-component store to keep eventually consistent, and no tracing to stitch together. Draw clean domain boundaries in the code, confine each module's data access to its own tables, and route inter-module interactions through interfaces rather than shared internals. Those boundaries are exactly the seams along which you extract components later, so the modular monolith keeps the door open without paying the distributed-systems tax up front. Microservices are a response to scale that is organizational first and technical second, so adopt them when many teams need to ship independently and are blocked by each other, or when domains have genuinely divergent scaling and availability needs. Starting distributed before that scale exists imports the full cost and collects the benefit never.

### Q: How do I make a message consumer idempotent, and why does it matter?

Idempotency means processing the same message twice produces the same result as processing it once, with no extra side effect. It matters because durable messaging systems deliver at least once, so the same message can legitimately arrive more than once after a retry or a redelivery, and a consumer that is not idempotent will double-charge, double-reserve, or otherwise corrupt state. You achieve idempotency by keying side effects on a stable identifier from the message, such as an order id, and checking whether the work is already done before doing it: reserving stock for an order id that is already reserved becomes a no-op, and writing a record with a unique key fails harmlessly on the second attempt. Complete the message only after the work succeeds, so a crash mid-processing redelivers rather than loses the message. Idempotency is not an optional refinement in an asynchronous design; it is the price of the durability that makes the design resilient in the first place.

### Q: How does KEDA differ from the Horizontal Pod Autoscaler?

The Horizontal Pod Autoscaler scales a component on resource metrics, typically CPU or memory utilization, which fits a request-serving component whose load shows up as CPU. The Kubernetes Event-driven Autoscaler scales on external event metrics instead, such as the depth of a Service Bus queue, the lag on an Event Hubs stream, or a Kafka topic offset, which fits an asynchronous consumer whose load is the backlog of work waiting rather than CPU. KEDA's defining capability is scaling to zero: when there are no events, it can take a consumer to no replicas and bring the first one up the instant a message arrives, removing the cost of idle consumers. KEDA does not replace the autoscaler; under the hood it creates and feeds a Horizontal Pod Autoscaler object with external metrics, so it extends the model. The guidance is to let one own a given workload rather than pointing both at the same Deployment, since two controllers fighting over one target is unstable.

### Q: What goes wrong when two microservices share a database?

Sharing a database couples the two components through the schema, which quietly destroys the independence that justified splitting them. Neither can change its table layout without verifying the other still works, so a migration becomes a coordinated multi-team event rather than a local change. A heavy or badly tuned query from one component locks rows or consumes connections the other needs, so a problem in one becomes an incident in both. Backup, scaling, and failover decisions can no longer be made per component because the store serves several. The result is a distributed monolith: components that look separate on the diagram but cannot deploy, fail, or scale separately in practice. The fix is one private store per component, with cross-domain data delivered through events and read models or through the owning component's API, and with access enforced by scoped managed identities so the credentials to reach another domain's store simply do not exist.

### Q: How should I evolve a monolith into microservices on AKS?

Evolve incrementally along boundaries you have already drawn, rather than rewriting wholesale. Begin from a modular monolith with strong internal boundaries, where each future domain is a module owning its own tables and interacting with others through interfaces. When a module's scaling needs or team ownership diverge enough to justify it, extract that module first, carrying its tables into a private store and its interface into an API plus events. Bring the reference layers online in order: observability early, because you cannot operate distributed components blind; asynchronous communication as soon as you have interactions that do not need an immediate answer; per-component data from the first extraction; per-component autoscaling when load profiles diverge; and the service mesh last, when the component count or polyglot spread names it. Throughout, re-check the deciding questions of the reference at every change, because a system decays into a distributed monolith one convenient shortcut at a time, and the deliberate recurring audit is what keeps it healthy.

### Q: What observability signals matter most for an asynchronous consumer?

For an asynchronous consumer the standard golden signals still apply, but two queue-specific signals matter most: queue depth and message age. Queue depth is the number of messages waiting to be processed, and a consumer that is keeping up shows a shallow, stable depth while one falling behind shows a depth that grows without bound, which is the earliest sign it needs to scale or is failing to process. Message age, the time the oldest waiting message has been in the queue, tells you how stale the backlog is and whether messages are at risk of breaching a processing deadline. Alongside these, track the processing error rate and the dead-letter count, since a rising dead-letter count signals poison messages that no retry will fix. These signals also feed scaling: the same queue depth that warns you of a backlog is the metric the event-driven autoscaler uses to add consumer replicas, so good observability and good autoscaling draw on the same measurement.

### Q: Can a distributed trace follow a request across an asynchronous message?

Yes, and making it do so is one of the most important and most often missed parts of observability in this architecture. A trace follows a synchronous call naturally because the trace context travels in the HTTP headers, but an asynchronous handoff breaks the chain unless you carry the context across it deliberately. The technique is to inject the trace context into the message properties when you publish, and to read it back out and continue the trace when you consume, so the span for publishing the event and the span for processing it belong to the same trace tree. Without this, you get two disconnected traces, one ending when the event is published and a separate one beginning when it is consumed, which hides the very handoff you most need to see when diagnosing a slow or lost workflow. With context propagation across the message boundary, a single trace shows the whole journey, the synchronous hops and the asynchronous fan-out alike, as one continuous waterfall.
