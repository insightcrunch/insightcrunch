---
layout: post
title: "Azure Load Balancer vs Application Gateway Explained"
page_title: "Azure Load Balancer vs Application Gateway: Layer 4 vs Layer 7, WAF, Path Routing, SSL Termination, and How to Choose the Right Service"
date: 2023-10-02
categories: ["Technology"]
tags: ["Azure", "Load Balancer", "Application Gateway", "Networking", "Cloud Computing"]
excerpt: "Load Balancer versus Application Gateway comes down to layer 4 versus layer 7. Learn which features force App Gateway and when raw TCP stays on the LB."
image: "/assets/images/blog/blog-44.webp"
reading_time: 63
author: "thomas-reid"
last_updated: 2023-10-02
lang: en
---
Choosing between Load Balancer versus Application Gateway is the moment most Azure networking decisions either click into place or quietly go wrong. An engineer needs to spread traffic across a set of backend machines, opens the portal, and finds two services that both promise to do exactly that. Load Balancer sounds general and cheap. Application Gateway sounds powerful and modern. So the temptation is to read a marketing page, pick whichever one was mentioned in the last tutorial, and move on. That guess works often enough to feel safe, which is precisely why it is dangerous: the day a path-based routing requirement or a security-team mandate for a web firewall lands, the wrong choice forces a redesign that touches DNS, certificates, health probes, and every downstream dependency.

![Azure Load Balancer vs Application Gateway layer 4 versus layer 7 decision - Insight Crunch](/assets/images/blog/blog-44.webp)

The fix is not memorizing a feature matrix. It is holding a single rule that the entire comparison reduces to, so that any new requirement sorts itself onto the correct service without a coin flip. That rule is the layer the service operates at. Azure Load Balancer is a layer-4 distributor that moves TCP and UDP flows without ever reading what they carry. Application Gateway is a layer-7 reverse proxy that terminates the connection, reads the HTTP request, and acts on its contents. Once you internalize which layer each one lives at, every downstream question (Can it route by URL path? Can it run a web application firewall? Can it offload TLS? Can it pin a user to one backend?) answers itself, because each of those capabilities is a property of layer 7, and only the layer-7 service can have it. This article builds that mental model from the protocol up, gives you a decision table you can keep next to the keyboard, and walks the recurring real-world patterns where the layer is the deciding signal.

## The layer-decides-the-tool rule, stated plainly

The single claim this article defends is the layer-decides-the-tool rule: the choice between the two services is a choice between layer 4 and layer 7, so any requirement that depends on the contents of an HTTP request forces Application Gateway, while a requirement to spread raw TCP or UDP belongs to Load Balancer. Everything else is detail hanging off that one decision.

Why does the layer carry so much weight? Because a network device can only act on what it can see, and what it can see is fixed by where it sits in the protocol stack. The OSI model is a teaching abstraction, but the part that matters here is concrete and physical. A layer-4 device inspects the transport header: source and destination IP, source and destination port, and the protocol number that says TCP or UDP. It makes a forwarding decision from those few fields and then gets out of the way. It does not assemble the byte stream into a request. It does not know whether the payload is HTTP, a database protocol, a game server heartbeat, or encrypted noise. To a layer-4 distributor, every flow is an opaque pipe identified by a five-tuple.

A layer-7 device sits one conceptual floor higher. It accepts the client connection, completes the handshake, reassembles the bytes into a full application-protocol message, and only then decides what to do. For web traffic that message is an HTTP request, complete with a method, a URL path, a host header, cookies, and a body. Because the proxy holds the parsed request in hand, it can branch on any field inside it. It can send `/api/*` to one pool and `/images/*` to another. It can read the `Host` header and serve two different sites from one public address. It can inspect the body for an injection attack. It can decrypt the TLS session, look inside, and re-encrypt to the backend. None of those actions is possible without parsing the request, and parsing the request is the defining act of layer 7.

That is the whole comparison in one breath. Load Balancer is fast and indifferent because it never opens the envelope. Application Gateway is feature-rich and heavier because it reads every letter. The cost, the latency profile, the protocol support, and the entire feature gap between them all descend from that one structural difference. When a colleague asks which to use, the productive question to ask back is never "how much traffic" or "what is the budget" first. It is "does the decision depend on something inside the HTTP request?" If yes, the answer is Application Gateway, full stop. If no, Load Balancer is almost certainly the cheaper, simpler, faster fit.

### What does layer 4 actually mean for a load balancer?

Layer 4 means the load balancer routes by the transport-level five-tuple (source IP, source port, destination IP, destination port, and protocol) and never reads the payload. It forwards TCP and UDP flows as opaque streams, which makes it protocol-agnostic and extremely fast, but blind to anything an HTTP request contains.

Holding that definition steady prevents the most common category error in Azure networking, which is expecting a layer-4 service to perform a layer-7 trick. People ask why their Load Balancer will not route based on the URL, why it will not terminate TLS, why it cannot block a SQL-injection string. The answer in every case is identical: those actions require reading the request, the load balancer never reads the request, so it cannot. The limitation is not a missing feature that Microsoft forgot to ship. It is a direct consequence of the layer the service was built to operate at, and no configuration toggle can move a device up the stack.

## The InsightCrunch layer-4-versus-7 decision table

The findable artifact for this comparison is a decision table that maps each concrete need to the service that can satisfy it and names the deciding signal. Keep it next to your architecture notes. When a requirement lands, find the row, read the verdict, and move on without relitigating the whole comparison.

| Need | Load Balancer (Layer 4) | Application Gateway (Layer 7) | Deciding signal |
|------|-------------------------|-------------------------------|-----------------|
| Spread raw TCP or UDP across backends | Yes, this is its core job | No, it is HTTP and HTTPS only | The protocol is not HTTP |
| Distribute a high-throughput, latency-sensitive non-web service | Yes, minimal added latency | Poor fit, proxy overhead per request | Throughput and latency dominate |
| Route by URL path (for example `/api` versus `/static`) | No, cannot see the path | Yes, path-based routing rules | The route depends on the URL |
| Host multiple sites or domains on one public address | No, cannot read the host header | Yes, multi-site listeners | The route depends on the `Host` header |
| Run a web application firewall (OWASP rule protection) | No, cannot inspect the payload | Yes, the WAF SKU provides this | A managed web firewall is required |
| Terminate (offload) TLS at the front | No, passes encrypted bytes through | Yes, SSL termination and re-encryption | Decryption at the edge is needed |
| Pin a user session to one backend by cookie | No, has no cookies to read | Yes, cookie-based affinity | Sticky sessions keyed on a cookie |
| Rewrite headers or URLs in flight | No | Yes, rewrite rules | The request must be modified |
| Keep a backend tier private and internal | Yes, internal Load Balancer | Yes, internal (private) Application Gateway | Either, choose by the layer above |
| Minimize cost for a simple distribution job | Yes, the cheaper option by far | No, carries a higher hourly and capacity cost | Budget with no layer-7 need |

The table reads top to bottom as a sieve. Any single Yes in the Application Gateway column that your workload genuinely needs settles the decision, because Load Balancer cannot grow those capabilities. If every need you have sits in rows where Load Balancer says Yes, you are paying for nothing by reaching for the gateway, and the simpler service is the correct call. The deciding-signal column is the part worth memorizing, because it lets you classify a brand-new requirement you have never seen before by asking which signal it triggers.

## How Azure Load Balancer works as a layer-4 distributor

Picture a flow arriving at the public frontend IP of a Standard Load Balancer. The packet carries a destination port, say 443, and a source IP and port that together with the destination form the five-tuple. The load balancer consults its rules, finds the one bound to that frontend IP and port, and selects a backend instance from the associated pool. By default it picks using a hash over the five-tuple, which means every packet of a given flow lands on the same backend for the life of that connection, while a new connection from the same client may hash to a different instance. The selected backend receives the packet, and from that point the load balancer is mostly a bystander, rewriting addresses as needed and tracking the flow so return traffic finds its way back. It never buffers a request, never parses a protocol, and never holds application state.

This design is why Load Balancer scales to enormous packet rates with negligible added latency. There is no per-request parsing tax because there are no requests as far as the device is concerned, only flows. A streaming ingestion endpoint, a custom TCP protocol, a database front end, a fleet of game servers, a set of SIP or RTP media nodes: all of these are natural Load Balancer workloads precisely because they are not HTTP and would gain nothing from a proxy that insists on understanding HTTP. The service is built on the software-defined networking fabric of the platform, so it is not a virtual appliance sitting in your traffic path consuming CPU. It is a distributed rule applied in the network itself, which is part of why it adds so little overhead.

The Standard tier is the one to reason about for any production comparison, because the Basic tier is being retired and lacks the availability-zone support, the larger backend pool sizes, the secure-by-default posture, and the metrics that a serious deployment needs. A frontend can be public, fronted by a standard public IP, or internal, bound to a private address inside a virtual network. The backend pool can hold virtual machines, scale-set instances, or other resources reachable inside the network. Load-balancing rules tie a frontend port to a backend port and a health probe. Inbound NAT rules map a specific frontend port to one specific backend instance, which is how people expose, for example, SSH or RDP to individual machines behind a single public IP. Outbound rules govern how backends reach the internet, a topic that connects directly to source NAT and port exhaustion, which the deep dive on outbound connectivity and SNAT covers in detail.

What Load Balancer deliberately does not do is the entire point of this comparison. It will not present a certificate, because TLS termination requires reading and rewriting the encrypted stream. It will not route on a URL, because there is no URL at layer 4. It will not block a malicious payload, because it never sees the payload. Asking it to do any of these is asking a layer-4 device to behave like a layer-7 one, and the request is structurally impossible rather than merely unconfigured.

## How Application Gateway works as a layer-7 reverse proxy

Application Gateway sits in the traffic path as a true reverse proxy, which changes the entire model. When a client connects, the gateway, not the backend, completes the TCP handshake and, for HTTPS, the TLS handshake. The client's connection ends at the gateway. The gateway then reads the full HTTP request, evaluates it against its listeners and routing rules, and opens a separate connection to the chosen backend to relay the request. Two connections exist where Load Balancer had one flow: client-to-gateway and gateway-to-backend. That split is what unlocks every layer-7 capability, because the gateway is now a participant in the conversation rather than a forwarder of packets.

The moving parts follow from that role. A frontend IP, public or private, receives connections. A listener binds to that frontend IP, a port, and optionally a hostname and a certificate, and it represents the gateway's willingness to accept a particular kind of traffic, such as HTTPS on port 443 for `shop.example.com`. Routing rules connect a listener to a backend pool, either directly (basic routing) or through a URL path map (path-based routing) that sends different path patterns to different pools. Backend HTTP settings describe how the gateway talks to the backends: the port, the protocol, whether to re-encrypt, the timeout, the cookie-affinity choice, and which custom probe to use. Backend pools list the targets, which can be IP addresses, FQDNs, scale sets, or App Service apps. Health probes, richer than the layer-4 kind, check an actual HTTP path and can match on status codes and response bodies.

The current generation runs on the v2 SKU, which autoscales, supports availability zones, and uses a static public address, and it is the one to design against rather than the legacy v1. The WAF capability is offered as the WAF v2 SKU, which adds managed rule sets that inspect requests for common attack patterns. Because the gateway terminates and re-originates every connection, it incurs a per-request processing cost that Load Balancer does not, and its capacity is measured in capacity units that reflect compute, connections, and throughput rather than in raw flow counts. That overhead is the price of sight, and it is worth paying only when the workload needs the gateway to act on what it sees.

### Why does a reverse proxy see more than a load balancer?

A reverse proxy terminates the client connection and reassembles the bytes into a complete HTTP request before forwarding it. Holding the parsed request, it can branch on the method, path, host header, cookies, and body. A layer-4 load balancer only forwards opaque packets by their transport tuple, so it has no parsed request to inspect or modify.

That difference is not a matter of degree but of kind. It is the reason the gateway can offer path routing, host-based multi-site hosting, header rewrites, cookie affinity, TLS offload, and a web firewall, while the load balancer can offer none of them no matter how it is configured. When you read the marketing comparison and wonder why one list is so much longer than the other, the explanation is always the same single fact: one service parses the request and the other does not.

## The layer-7 features only Application Gateway provides

Four capabilities define the gap between the two services, and each one is a direct expression of reading the request. Understanding them concretely is what turns the abstract layer rule into an operational instinct, so it pays to walk each capability down to the field in the request that makes it possible.

Path-based routing is the ability to send different URL paths to different backend pools. A single hostname, `app.example.com`, can route `/api/*` to a pool of API servers, `/images/*` to a pool optimized for static assets, and everything else to a default pool. The gateway reads the path segment of the request line, matches it against a URL path map, and selects the pool accordingly. A layer-4 device sees only that a TCP connection arrived on port 443; the path lives inside the encrypted, parsed request it never assembles, so path routing is forever beyond its reach. When an architecture diagram shows one front door fanning out to specialized backend tiers by URL, an Application Gateway is doing that work, or a more global edge service is.

Host-based, or multi-site, routing extends the same idea to the `Host` header. One gateway with one public IP can serve `shop.example.com`, `blog.example.com`, and `admin.example.com`, each with its own listener, certificate, and backend pool, because the gateway reads the host header to decide which site the request belongs to. This is how teams consolidate many small sites behind one entry point without standing up a load balancer per site. Again, the deciding field, the host header, lives in the parsed request, which keeps this firmly on the layer-7 side.

SSL termination, also called TLS offload, lets the gateway hold the certificate and complete the TLS handshake with the client, decrypt the traffic, act on the plaintext request, and then either forward in plaintext or re-encrypt to the backend. Offloading decryption centralizes certificate management and frees backends from the cryptographic load, while end-to-end TLS keeps the gateway-to-backend hop encrypted when compliance requires it. None of this is possible at layer 4, where the bytes stay encrypted end to end and the device has no certificate and no plaintext to inspect. A Load Balancer can pass an encrypted stream through to a backend that terminates TLS itself, but it cannot terminate TLS, because terminating means decrypting, and decrypting means reading.

Cookie-based session affinity pins a given client to the same backend for the life of a session by issuing and reading a cookie the gateway controls. Stateful applications that keep session data in process memory rather than in a shared store depend on this so a user's requests keep landing on the instance that holds their session. The gateway can do it because it reads and writes HTTP headers, where cookies live. Load Balancer offers a coarser form of stickiness through source-IP affinity, a two-tuple or three-tuple hash that keeps a client on one backend by address rather than by cookie, but it has no cookies to set or read, so true cookie affinity is a layer-7-only behavior.

The web application firewall is the capability that most often forces the decision regardless of any other factor. The WAF SKU inspects each request against managed rule sets that target common attack classes such as SQL injection and cross-site scripting, blocking or logging matches before they reach the backend. Inspection requires the full parsed request, including the body, so a web firewall can only live on a layer-7 device. When a security team mandates a managed web firewall in front of an application, that single requirement settles the comparison in favor of Application Gateway, and the detailed steps for standing one up live in the walkthrough on [how to configure the Application Gateway WAF](/2023/05/08/configure-app-gateway-waf/). The alternative, placing the firewall at a global edge, is a different architecture that the edge comparison article weighs.

### Which features force you onto Application Gateway?

Any need that depends on the contents of an HTTP request forces Application Gateway: routing by URL path, hosting multiple sites by host header, terminating or re-encrypting TLS, pinning sessions by cookie, rewriting headers or URLs, and running a web application firewall. Each of these reads or modifies the request, which only a layer-7 proxy can do.

The practical test is faster than scanning a feature list. Ask whether the requirement could be satisfied by a device that sees nothing but IP addresses, ports, and protocol numbers. If a human reading only that handful of fields could fulfill the requirement, Load Balancer can do it. If fulfilling it requires knowing the URL, the host, the cookie, or the payload, only Application Gateway can, because only it reads those fields.

## Internal versus public variants on both services

A point of genuine confusion in the comparison is that both services come in public and internal forms, which means the public-versus-internal axis is not what distinguishes them. People sometimes reach for Application Gateway because they need an internal endpoint for a backend tier, not realizing that Load Balancer offers an internal variant too, and the cheaper one is usually the right one when no layer-7 feature is in play.

An internal (private) Load Balancer binds its frontend to a private IP inside a virtual network rather than to a public IP. It distributes traffic among backends that should never be reachable from the internet, such as a middle tier of application servers fronting a database, or a set of services consumed only by other workloads in the network. This is the classic pattern for a three-tier design where a public Load Balancer or gateway fronts the web tier, and an internal Load Balancer sits between the web tier and the application tier, spreading internal calls without exposing anything publicly.

Application Gateway likewise supports a private deployment, where the frontend uses a private IP and the gateway serves traffic that originates inside the network or arrives through a private path. The reason to choose a private Application Gateway over a private Load Balancer is identical to the reason to choose the public versions: a layer-7 need. If internal traffic must be routed by path, inspected by a firewall, or terminated for TLS, the internal gateway earns its place. If internal traffic just needs spreading across a pool, the internal Load Balancer does it cheaper and with less latency.

### Is an internal load balancer different from a public one?

An internal load balancer is the same engine with a private frontend IP instead of a public one. It distributes traffic among backends inside a virtual network and is unreachable from the internet. Everything about the layer-4 behavior, the probes, and the rules is identical; only the frontend address and reachability change.

Keeping the public-versus-internal axis separate from the layer-4-versus-layer-7 axis prevents a frequent design mistake. The two axes are orthogonal: you can have a public layer-4 Load Balancer, an internal layer-4 Load Balancer, a public layer-7 Application Gateway, or an internal layer-7 Application Gateway, and the choice along each axis is made independently. Reachability is about where the traffic comes from. Layer is about what the device needs to do with it. Decide them as two separate questions and the architecture falls out cleanly.

## How health probes work at each layer, and why they confuse the comparison

Health probes are where many comparisons go sideways, because both services probe their backends, yet they probe at the layer they operate at, and that produces meaningfully different behavior. A backend can look healthy to one service and unhealthy to the other for reasons that make perfect sense once the layer difference is clear.

A Load Balancer health probe operates at layer 4 or with a shallow layer-7 check. A TCP probe simply opens a connection to the configured backend port and considers the instance healthy if the handshake completes. It says nothing about whether the application behind that port is actually serving correct responses; it confirms only that something is listening and accepting connections. An HTTP or HTTPS probe on the Standard tier goes a step further and checks that a path returns a 200, but the layer-4 service's primary contract is reachability of the port. If the probe is misconfigured (wrong port, blocked by a network security group rule that does not permit the probe source, or pointed at a path the backend does not serve), the instance is marked down and removed from rotation, and traffic silently stops flowing to it. The full anatomy of why a probe marks a backend down, and how to confirm each cause, is the subject of the dedicated guide on [fixing Load Balancer probe failures](/2022/12/05/fix-load-balancer-probe-failure/).

An Application Gateway health probe operates at layer 7 by definition. It issues a real HTTP request to a path on the backend and evaluates the response against expected status codes and, optionally, a body match string. Because the gateway is already a layer-7 device, its probe naturally tests the application, not just the socket. This is richer, but it introduces its own failure surface: if the probe path returns a redirect, an authentication challenge, or a status the gateway is not told to accept, the backend is judged unhealthy even though it is serving real users fine on other paths. A mismatch between the host header the probe sends and the host the backend expects is a classic cause of a backend pool that shows as unhealthy, which in turn produces the gateway's signature 502 error. The end-to-end diagnosis of why Application Gateway returns a 502, including unhealthy pools and probe mismatches, is covered in the troubleshooting article on [why Application Gateway returns a 502](/2022/12/12/fix-application-gateway-502/).

```bash
# Inspect Load Balancer health probe configuration
az network lb probe list \
  --resource-group rg-net \
  --lb-name lb-internal \
  --output table

# Inspect Application Gateway backend health (the layer-7 view)
az network application-gateway show-backend-health \
  --resource-group rg-net \
  --name appgw-prod \
  --output table
```

### Why do health probes behave differently on each?

Load Balancer probes confirm transport-level reachability of a port, while Application Gateway probes issue a real HTTP request and judge the response status and body. The same backend can pass a layer-4 TCP probe yet fail a layer-7 probe if the application returns an unexpected status, a redirect, or a host-header mismatch.

The lesson for the comparison is that you cannot reason about probe behavior without first fixing which service you are using, because the probe inherits the service's layer. When someone reports that a backend is healthy on one service and unhealthy on the other, the explanation is almost always that the layer-4 probe is satisfied by an open port while the layer-7 probe is failing on a response detail. The probe is not buggy; it is testing a different thing because it lives at a different layer.

## The cost and complexity trade-off

Money and operational weight track the layer too. Load Balancer is the inexpensive option, and for a clean reason: it is a rule in the network fabric rather than a fleet of proxy instances, so there is no compute to pay for in the data path. Its pricing centers on the rules configured and the data processed, and for a straightforward distribution job it is dramatically cheaper than the alternative. There is little to operate beyond the rules and probes themselves, because the service has no application-layer state to manage.

Application Gateway is the more expensive and more involved service because it runs actual capacity that terminates and re-originates connections. Its v2 pricing combines a fixed hourly charge with a consumption component measured in capacity units that reflect compute, persistent connections, and throughput. The WAF SKU costs more than the standard SKU because rule inspection adds processing per request. Beyond the bill, the gateway carries operational surface that Load Balancer does not: certificates to rotate, listeners and routing rules to maintain, backend HTTP settings to keep correct, WAF rules to tune against false positives, and a richer set of failure modes to diagnose. That is not a criticism of the service; it is the natural cost of a device that does more because it sees more.

The trap runs in both directions. Reaching for Application Gateway to perform a simple TCP or non-web distribution job means paying for a proxy and operating its full surface to gain capabilities the workload never uses, while accepting per-request latency that a layer-4 distributor would not impose. Reaching for Load Balancer when the workload genuinely needs path routing, a web firewall, or TLS offload means discovering mid-project that the cheaper service structurally cannot do the job, then redesigning under pressure. The correct framing is not "which is cheaper" in the abstract, because the cheaper service is only a bargain if it meets the requirement. The correct framing is "what is the minimum layer that satisfies every requirement," and then choosing the service at that layer, which usually also happens to be the cheaper one that fits.

### Does Application Gateway cost more than Load Balancer?

Yes, in nearly every comparison Application Gateway costs more, because it runs proxy capacity that terminates and re-originates connections, billed by an hourly charge plus consumption-based capacity units, with the WAF SKU costing more still. Load Balancer is a fabric rule with no data-path compute, so it is far cheaper for equivalent distribution work.

Treat both pricing models as values to verify against the current Azure pricing page at the time you design, since rates, SKUs, and the metering details change. The durable point is structural rather than numeric: a proxy that processes every request will always carry more cost and more operational weight than a fabric rule that forwards flows, so the gateway should earn its higher cost by delivering a layer-7 capability the workload actually requires.

## Real-world patterns and the deciding factor in each

The layer rule earns its keep when you stop reasoning in the abstract and start matching concrete situations to it. The patterns below recur constantly in engineering work, and each one resolves cleanly once you identify the deciding signal. Reading them as a set trains the instinct to classify a new requirement in seconds.

The first pattern is a need for path-based routing that only the gateway provides. A team runs a monolith that has begun to split: the `/api` surface should go to a new service while the legacy `/app` surface stays on the old fleet, all under one hostname and one certificate. The deciding signal is that the route depends on the URL path, which lives inside the parsed request. A layer-4 Load Balancer sees one connection on port 443 and cannot tell `/api` from `/app`, so the requirement is structurally impossible for it. Application Gateway with a URL path map is the answer, and the design is a single listener feeding a path map that sends each prefix to its own backend pool.

The second pattern is the inverse: a TCP workload over-served by the gateway. A team stands up a custom binary protocol on port 9000, or a database proxy, or a message broker frontend, and an architect reflexively proposes Application Gateway because it sounds like the serious choice. The deciding signal is that the protocol is not HTTP, which puts the workload outside the gateway's competence entirely, since Application Gateway handles HTTP and HTTPS only. Load Balancer is not merely the cheaper option here; it is the only one of the two that can carry the traffic at all. Choosing the gateway would be choosing a service that cannot accept the workload.

The third pattern is TLS termination at the front. A team wants to centralize certificate management and stop installing certificates on every backend instance, terminating TLS once at the entry point and forwarding decrypted traffic, or re-encrypting to the backends for end-to-end protection. The deciding signal is that the requirement is to decrypt and act on the traffic at the edge, which only a layer-7 device can do. Application Gateway terminates the TLS session, optionally re-encrypts, and gives one place to rotate certificates. A Load Balancer can pass the encrypted stream through to backends that terminate it themselves, but it cannot own termination, because owning it means reading the decrypted request.

The fourth pattern is a web firewall requirement forcing the gateway. A compliance or security mandate requires a managed web application firewall in front of an application to block injection and scripting attacks. The deciding signal is the need to inspect request contents, including the body, against attack rule sets, which is a layer-7 act. The WAF SKU of Application Gateway delivers this, and no Load Balancer configuration can, because the load balancer never sees the payload to inspect. This single requirement frequently settles a comparison on its own, overriding cost and simplicity preferences, because there is no layer-4 path to a web firewall.

The fifth pattern is an internal load balancer for a backend tier. A three-tier application needs its web tier to reach its application tier through a stable, balanced endpoint that is never exposed publicly, and the calls between tiers are plain internal traffic with no path routing, firewall, or TLS-offload need. The deciding signal is that there is no layer-7 requirement and the endpoint must be private, so an internal Load Balancer is the precise fit: cheaper, faster, and exactly as private as required. Reaching for an internal Application Gateway here would pay for sight the tier never uses.

The sixth pattern is health-probe differences confusing a comparison. An engineer migrating a service from one entry point to another finds that the backends were healthy behind a Load Balancer but show as unhealthy behind an Application Gateway, or the reverse. The deciding signal is that each service probes at its own layer, so a backend that satisfies a layer-4 TCP probe by merely listening can fail a layer-7 probe that checks a real HTTP response. The fix is to align the gateway probe's path, host header, and expected status with what the backend actually serves, not to assume one of the services is broken.

```text
Pattern -> Deciding signal -> Service
Path routing under one host    -> route depends on URL path     -> Application Gateway
Custom TCP or non-HTTP service -> protocol is not HTTP           -> Load Balancer
Centralized TLS termination    -> decrypt at the edge           -> Application Gateway
Managed web firewall mandate   -> inspect request contents      -> Application Gateway (WAF SKU)
Private balanced backend tier  -> private, no layer-7 need       -> Internal Load Balancer
Probe health mismatch          -> probe lives at service's layer -> align probe to the layer
```

## How the two interact with the rest of your network

Neither service lives alone, and several recurring questions are really about how each one composes with the surrounding network. Treating that composition deliberately avoids surprises that look like service bugs but are really integration details.

Network security groups sit beneath both services and can quietly break either one. For Load Balancer, the most common failure is an NSG that does not allow the platform's probe source, so probes fail and backends drop out of rotation even though the application is fine. For Application Gateway v2, the gateway subnet needs inbound access from the gateway manager's address range and the infrastructure ports it uses, and an overly tight NSG on that subnet can prevent the gateway from operating at all. The rule of thumb is that the NSG is part of the data path for both services, and a healthy-looking backend with no traffic is often an NSG problem rather than a load-balancing problem.

Routing through user-defined routes interacts with both, especially in hub-and-spoke designs where traffic is steered through a firewall. A UDR that sends a backend subnet's traffic somewhere unexpected can break the return path for a load-balanced flow or interfere with the gateway's connection to its backends. When a backend is reachable directly but not through the front, the route table is a prime suspect.

Composition with a global edge is the most strategic interaction. Application Gateway is a regional service: it lives in one region and fronts backends there. When an application must be global, with traffic entering near the user and failing over across regions, a global front end such as Azure Front Door sits in front of regional Application Gateways, each fronting that region's backends. Front Door provides global routing, caching, and an edge web firewall, while each regional gateway provides regional path routing and a regional firewall. They compose rather than compete, and the comparison of when to use a global edge versus a regional gateway, alongside a CDN, is the subject of the article weighing [Front Door against a CDN and the gateway](/2023/10/09/front-door-vs-cdn-vs-gateway/). Load Balancer, being layer 4 and regional, fits a similar composition for non-web global services through a global layer-4 tier, but the web case is the one most teams meet first.

A clean way to hold the composition is to think in entry tiers. The outermost tier is global and concerned with where in the world a request lands and whether it can be cached. The next tier is regional and concerned with which backend pool inside a region serves the request and whether the request is safe. The innermost tier is internal and concerned with spreading internal calls among instances. Application Gateway naturally occupies the regional web tier, Load Balancer naturally occupies the internal layer-4 tier and the regional non-web tier, and a global edge occupies the outermost tier. Most confusion about which service to use dissolves once you place the requirement in the correct tier first.

## Configuring each service, so the comparison stays concrete

Reading the configuration of each service side by side makes the layer difference tangible, because the gateway's configuration is visibly about requests while the load balancer's is visibly about flows. The snippets below are minimal, illustrative shapes rather than copy-and-paste production templates, and any port, SKU, or option should be checked against the current Azure CLI and documentation when you build, since flags and defaults shift over time.

A Standard Load Balancer is assembled from a frontend IP, a backend pool, a health probe, and a rule that ties them together. The configuration never mentions URLs, hosts, certificates, or cookies, because none of those exist at the layer it works at.

```bash
# Create a Standard public Load Balancer with a frontend and backend pool
az network lb create \
  --resource-group rg-net \
  --name lb-web \
  --sku Standard \
  --public-ip-address pip-lb-web \
  --frontend-ip-name fe-web \
  --backend-pool-name bep-web

# A TCP health probe: confirms the port is listening
az network lb probe create \
  --resource-group rg-net \
  --lb-name lb-web \
  --name probe-tcp-443 \
  --protocol Tcp \
  --port 443

# A load-balancing rule: frontend 443 to backend 443, using the probe
az network lb rule create \
  --resource-group rg-net \
  --lb-name lb-web \
  --name rule-https \
  --protocol Tcp \
  --frontend-port 443 \
  --backend-port 443 \
  --frontend-ip-name fe-web \
  --backend-pool-name bep-web \
  --probe-name probe-tcp-443
```

An Application Gateway configuration tells the opposite story. It is built from a listener that knows about hostnames and certificates, backend HTTP settings that describe how to talk HTTP to the backends, an HTTP probe that checks a real path, and routing rules that can branch by URL. Every concept references the request.

```bash
# Create an Application Gateway v2 (illustrative; verify SKU and options when building)
az network application-gateway create \
  --resource-group rg-net \
  --name appgw-web \
  --sku Standard_v2 \
  --capacity 2 \
  --vnet-name vnet-app \
  --subnet snet-appgw \
  --public-ip-address pip-appgw \
  --frontend-port 443 \
  --http-settings-protocol Https \
  --http-settings-port 443 \
  --servers 10.0.2.10 10.0.2.11

# An HTTP probe: checks a real path and matches an expected status
az network application-gateway probe create \
  --resource-group rg-net \
  --gateway-name appgw-web \
  --name probe-health \
  --protocol Https \
  --path /healthz \
  --host-name-from-http-settings true

# A URL path map: route /api to one pool, default elsewhere (path-based routing)
az network application-gateway url-path-map create \
  --resource-group rg-net \
  --gateway-name appgw-web \
  --name pathmap-web \
  --paths "/api/*" \
  --address-pool bep-api \
  --default-address-pool bep-default \
  --http-settings http-settings-default \
  --default-http-settings http-settings-default
```

The contrast is the comparison in miniature. The load balancer's rule speaks of protocol, frontend port, and backend port. The gateway's configuration speaks of HTTPS, host names, paths, and a health path. You could read either configuration with no labels and immediately tell which layer it operates at, because the vocabulary itself is layer-specific. That is a useful sanity check when inheriting an unfamiliar environment: read the configuration and the layer announces itself.

### Can I route by URL on a Load Balancer if I add a custom probe?

No. A custom HTTP probe lets a Load Balancer check a path for health, but probing a path is not routing by path. The load balancer still selects a backend by the five-tuple and forwards opaque flows; it has no parsed request to branch on, so URL routing remains impossible regardless of probe configuration.

This is a frequent source of false hope, because the presence of an HTTP probe on the Standard tier makes it look as though the load balancer understands HTTP. It does not understand HTTP for routing purposes; it merely uses an HTTP request to test health, then forwards the real traffic by transport tuple as always. Health checking and traffic routing are separate concerns, and only one of them gained a shallow layer-7 ability. Routing stayed at layer 4.

## Migration, coexistence, and changing your mind later

Decisions are rarely final, so it helps to know how each service behaves when requirements evolve. The good news is that the two compose cleanly, so a wrong early call is usually a redesign rather than a dead end, though the redesign cost is real and worth avoiding.

When a workload that started on a Load Balancer grows a layer-7 requirement, the typical move is to introduce an Application Gateway in front of, or in place of, the load balancer for the web traffic, while keeping any non-web traffic on the load balancer. The gateway becomes the new public front for HTTP and HTTPS, terminates TLS, applies routing and the firewall, and forwards to the same backends the load balancer was using, often through the load balancer for non-web ports. The migration touches DNS (pointing the hostname at the gateway's IP), certificates (moving them to the gateway), and probes (recreating them as HTTP probes), which is exactly the work the earlier layer guess could have avoided.

When a workload that was placed on an Application Gateway turns out to be plain TCP distribution with no layer-7 need, the move is to replace the gateway with a Load Balancer, dropping the proxy overhead and the cost. This is a simpler migration in concept, since you are removing capability rather than adding it, but it still means rebuilding the frontend and probes and repointing DNS.

Coexistence is common and healthy in larger designs. A single application might use a global edge for entry, a regional Application Gateway for web routing and the firewall, and an internal Load Balancer between the web and application tiers, with each device doing the job its layer suits. Seeing all three in one architecture is not a sign of indecision; it is a sign that each requirement was placed at the correct tier. The skill the layer rule builds is precisely this: knowing which device belongs where so the architecture is neither under-built (missing a layer-7 capability it needs) nor over-built (paying for a proxy where a fabric rule would do).

### How do I decide when I only need raw TCP distribution?

When the workload is plain TCP or UDP with no dependence on URL paths, host headers, cookies, TLS termination, or request inspection, choose Load Balancer. It carries the protocol natively, adds almost no latency, and costs far less. Application Gateway cannot even accept non-HTTP traffic, so it is not a candidate for raw TCP distribution.

The only reason to hesitate is a near-future layer-7 requirement you can already see coming, such as a planned web firewall or path split. If that requirement is genuinely imminent and certain, building the gateway path early can save a migration. If it is speculative, build the simple, correct thing now, since the composition path means adding a gateway later is a known, bounded piece of work rather than an architectural impossibility.

## Designing each for production

Picking the right layer is the first decision, but a production deployment of either service carries a set of design choices that determine whether it survives a region event, scales under load, and stays observable when something goes wrong. The choices differ between the two precisely because one is a fabric rule and the other is running capacity.

Availability across zones is the first concern for both. A Standard Load Balancer can be zone-redundant, meaning its frontend is served from all zones in the region and survives the loss of any single zone, and its backend pool should span zones so the distribution targets are themselves resilient. Application Gateway v2 likewise supports zone redundancy, spreading its instances across zones so the proxy tier itself does not become a single point of failure. In both cases the load-balancing tier being zone-redundant is necessary but not sufficient: the backends must also span zones, because a perfectly resilient front that points at backends in one zone still fails when that zone does. Designing for a zone event means treating the front and the back as one system.

Scaling behavior is where the two diverge sharply. Load Balancer does not scale in the conventional sense because there is no instance count to grow; it is a distributed rule that handles flows at fabric scale, and the thing that scales is the backend pool, which you size and autoscale yourself. Application Gateway v2 autoscales its own capacity in response to load, growing and shrinking the proxy tier within configured bounds. That autoscaling is a feature and a cost lever at once: it absorbs traffic spikes without manual intervention, and it means the bill tracks usage rather than a fixed provisioned size. Setting sensible minimum and maximum capacity bounds keeps the gateway from being slow to absorb a sudden spike while also keeping a runaway from quietly scaling into a large bill.

Certificate strategy applies only to the gateway, since the load balancer holds no certificates. Centralizing certificates at the gateway is one of its main attractions, and the production discipline around it is rotation: certificates expire, and an expired certificate at the gateway takes down every site behind the listener that uses it. Tying certificate storage to a managed secret store and automating rotation removes the most common self-inflicted outage. When end-to-end encryption is required, the gateway re-encrypts to the backends, which means the backends also hold certificates the gateway must trust, adding a second rotation concern that the plain-offload design avoids.

Web firewall tuning is the operational tax that comes with the WAF SKU. Managed rule sets block known attack patterns, but they also produce false positives against legitimate traffic that happens to look suspicious, such as a form field that contains characters a SQL-injection rule flags. Running the firewall in a detection mode first, observing what it would have blocked, and tuning exclusions before switching to prevention mode is the standard path to a firewall that protects without breaking the application. This tuning loop is ongoing rather than one-time, because both the rule sets and the application evolve, and the detailed setup of the firewall and its rules is covered in the configuration guide for the Application Gateway WAF.

Observability rounds out the production picture. Both services emit metrics and logs, but the gateway's are richer because it understands requests: it can report on request counts, response codes, latency, and firewall matches, while the load balancer reports on flow-level and health-probe metrics. Wiring these into a monitoring workspace and alerting on backend health, response codes, and capacity gives the early warning that turns a potential outage into a non-event. The single most valuable signal for the gateway is backend health, because an unhealthy pool is the root of its most common failure, and the single most valuable signal for the load balancer is probe success, for the same reason at its own layer.

### How do I keep an Application Gateway from becoming a single point of failure?

Deploy the v2 SKU with zone redundancy so its instances span availability zones, set a minimum capacity high enough to absorb normal load, and ensure the backend pool also spans zones. Pair this with automated certificate rotation and backend-health alerting, since an expired certificate or an unhealthy pool is a more common cause of outage than a zone loss.

The same logic, minus certificates, applies to a Load Balancer: make the frontend zone-redundant and spread the backend pool across zones. The recurring mistake is hardening the load-balancing tier while leaving the backends in a single zone, which moves the single point of failure one hop back rather than removing it. Resilience is a property of the whole path, not of the front device alone.

## Common misreadings that send teams to the wrong service

A handful of misreadings account for most wrong choices, and naming them makes them easy to catch in a design review. Each one is a way of forgetting the layer rule under the pressure of a deadline or a half-remembered tutorial.

The first misreading is treating Application Gateway as the default, more capable load balancer and reaching for it reflexively. It is more capable, but only at layer 7, and that capability is wasted weight and cost for a layer-4 workload. Defaulting to the gateway is as wrong as defaulting to the load balancer; the correct default is no default, only the layer question.

The second misreading is assuming Load Balancer can be coaxed into layer-7 behavior with enough configuration. People spend hours trying to make a load balancer route by path or terminate TLS, treating the limitation as a setting they have not found yet. There is no such setting, because the limitation is the layer, and no amount of configuration moves a device up the stack. Recognizing this early saves the hours.

The third misreading is conflating the public-versus-internal choice with the layer choice, leading someone to pick Application Gateway because they need a private endpoint, when an internal Load Balancer would serve a private layer-4 need for far less. Reachability and layer are independent axes, and collapsing them produces over-built internal tiers.

The fourth misreading is judging by traffic volume rather than by request dependence. A very high-throughput web workload still belongs on a layer-7 device if it needs path routing or a firewall, and a very low-throughput non-web workload still belongs on a layer-4 device. Volume influences sizing and cost, not the layer decision, which is governed solely by whether the workload depends on the request's contents.

The fifth misreading is forgetting that the gateway is regional and trying to make it serve a global audience directly, when the right pattern is a global edge in front of regional gateways. A single regional gateway fronting a worldwide user base adds latency for distant users and offers no cross-region failover, and the symptom (slow far-away users) gets misattributed to the gateway's performance rather than to a missing global tier.

The sixth misreading is blaming the load-balancing service for a backend or network problem. A healthy front device pointing at backends that fail their probes, or sitting behind an NSG that blocks the probe source, looks like a load-balancing failure but is a backend or NSG failure. The discipline is to check backend health and the surrounding network before concluding the service itself is at fault, which is exactly what the troubleshooting guides for probe failures and gateway 502s walk through.

### Which one should I choose for a multi-site or multi-domain web app?

Choose Application Gateway. Hosting multiple sites or domains behind one public address requires reading the `Host` header to route each request to the correct site, listener, and certificate, which is a layer-7 capability. A Load Balancer cannot read the host header, so it cannot distinguish the sites and cannot serve a multi-domain web application from one frontend.

The gateway handles this with multi-site listeners, one per hostname, each bound to its own certificate and routing rule. This consolidates many small sites behind a single entry point and a single set of public infrastructure, which is both cheaper and simpler to operate than a separate frontend per site. The deciding signal is unmistakable: the moment routing depends on which domain was requested, the decision lives at layer 7.

## Tracing one request through each service

A useful way to cement the layer difference is to follow a single client request through each service and notice exactly what the device does and does not touch. The same request, sent to the same backend, has a markedly different journey depending on which front it passes through, and the divergence is the comparison made physical.

Start with the journey through a Load Balancer. A client opens a TCP connection to the frontend IP on port 443 and begins the TLS handshake. The load balancer hashes the five-tuple, selects a backend, and forwards the packets. The TLS handshake completes between the client and the backend, not the load balancer, because the load balancer is not a party to the conversation; it only forwards the encrypted bytes. Every subsequent packet of that connection hashes to the same backend, so the session stays intact. The backend receives a connection that, from its perspective, came more or less directly from the client, and it terminates TLS, reads the HTTP request, and responds. The load balancer never saw the request line, never saw the host header, never saw the path, and never saw the certificate. It saw addresses, ports, and a protocol number, and it forwarded accordingly. If the client sent a request to `/api/orders` with a session cookie and a JSON body, none of that was visible to the front device. The load balancer's entire contribution was choosing which backend would receive the flow and keeping that choice consistent for the connection's life.

Now follow the same request through an Application Gateway. The client opens a TCP connection to the gateway's frontend IP on port 443 and begins the TLS handshake, but this time the handshake completes with the gateway, because the gateway holds the certificate and terminates the session. The gateway now has the decrypted request in hand: the method `GET`, the path `/api/orders`, the host header, the cookie, and the body. It evaluates the request against its listeners and routing rules, matches the path against a URL path map, and selects the backend pool that serves `/api`. If the WAF SKU is in use, it runs the request through the managed rule sets first, blocking it if a rule matches. It applies any header or URL rewrites. It checks cookie affinity to decide whether this client should stick to a particular backend. Then it opens a separate connection to the chosen backend, either in plaintext or re-encrypted, and relays the request. The backend receives a connection from the gateway, not from the client, and the response travels back through the gateway to the client. Where the load balancer touched nothing inside the request, the gateway touched almost everything: it read the path to route, read the body to inspect, read and wrote cookies to pin the session, and held the certificate to decrypt.

Laying the two journeys side by side makes the cost and capability difference self-evident rather than abstract. The gateway did more work because it read and acted on the request at every step, which is exactly why it offers more features and exactly why it costs more and adds latency. The load balancer did almost nothing per packet, which is exactly why it is cheap and fast and exactly why it cannot route by path or run a firewall. Neither is better in the abstract; each is the right answer for the journey its layer is built to perform.

### What can a Load Balancer never see about my traffic?

A Load Balancer never sees anything inside the request: not the URL path, not the host header, not cookies, not the request body, and not the decrypted contents of a TLS session. It sees only the transport-level addresses, ports, and protocol number. Every layer-7 capability it appears to lack is missing for this one reason, that the data those features need is invisible to a layer-4 device.

This is worth stating bluntly because it reframes every feature question. People often ask whether a load balancer can be made to do some layer-7 task, as if the capability were hidden behind a flag. The honest answer always traces back to visibility: the load balancer cannot act on what it cannot see, it cannot see inside the request, and the feature needs something inside the request, so the answer is no by construction rather than by configuration.

## Throughput, connection handling, and behavior under load

Beyond features and cost, the two services behave differently when traffic surges, and understanding that behavior prevents surprises during a spike or a load test. The difference again traces to the fabric-rule versus running-proxy distinction.

A Load Balancer scales transparently because it is part of the network fabric and does not maintain per-request application state. Its capacity to handle flows is enormous and does not require provisioning a proxy tier, so a sudden surge of new connections is distributed without the front device becoming a bottleneck. The pressure point under load is the backend pool, which must have enough instances to absorb the traffic the load balancer spreads to it, and the autoscaling you configure on that pool, not on the load balancer, is what keeps the system healthy. Connection handling at layer 4 is lightweight: the device tracks flows to keep return traffic consistent, but it does not buffer requests or hold connections open on the application's behalf. This is why a layer-4 front is the natural choice for very high connection rates and latency-sensitive protocols, where any per-request processing would be a measurable tax.

An Application Gateway, being a running proxy, has its own capacity that must scale to meet load. The v2 SKU autoscales its instances within configured bounds, growing the proxy tier as traffic rises and shrinking it as traffic falls. This absorbs spikes without manual intervention, but two design choices govern how gracefully it does so. The minimum capacity determines how much headroom exists before autoscaling has to react, so a minimum set too low can let a sudden spike outrun the scale-out and briefly degrade response times. The maximum capacity caps both the protection against overload and the worst-case bill, so it should be high enough to handle a realistic peak but bounded to prevent a runaway. Because the gateway terminates and re-originates connections, it also manages connection pools to the backends, reusing connections where it can to reduce overhead, which is part of why a healthy gateway can serve far more client connections than it opens to the backends.

The diagnostic implications follow directly. When a layer-4 system struggles under load, the investigation almost always lands on the backends or the network, because the load balancer itself rarely saturates. When a layer-7 system struggles under load, the gateway's own capacity is a legitimate suspect alongside the backends, because the proxy tier can be the bottleneck if its capacity bounds are set wrong. Watching the gateway's capacity-unit consumption and its backend response times together tells you whether a slowdown is the proxy needing to scale or the backends needing help. Watching the load balancer's backend health and the backend instances' own metrics tells the same story at layer 4. In both cases the front device's metrics and the backend's metrics must be read together, because a load-balancing tier is only ever as healthy as the pool behind it.

### Why does the backend pool, not the front device, usually limit throughput?

For Load Balancer, the front is a fabric rule with vast capacity, so the backends almost always saturate first. For Application Gateway, the proxy tier can be a bottleneck if its capacity bounds are set too low, but a well-bounded gateway also pushes the limit onto the backends. In both designs, sizing and autoscaling the backend pool is the main lever for throughput.

The recurring lesson is that hardening or scaling the front device alone rarely fixes a throughput problem, because the front was seldom the constraint. The constraint lives in the pool it feeds, so capacity planning should start there, with the front device's capacity treated as a separate, usually smaller, concern that matters most for the gateway and barely at all for the load balancer.

## The decision rule, branch by branch

To turn the layer rule into something you can run mechanically, walk it as a short series of branches. Each branch tests one signal, and the first Yes that lands you at layer 7 ends the walk. The order matters, because some signals are absolute (they make one service structurally impossible) and others are merely preferential.

Begin with protocol, because it can eliminate a service entirely. Is the traffic HTTP or HTTPS? If it is not (a custom TCP protocol, UDP, a database wire protocol, a media stream), Application Gateway is out, since it accepts only HTTP and HTTPS, and Load Balancer is the answer by elimination. The walk ends here for every non-web workload, and this branch alone resolves a large share of real cases without any further thought.

If the traffic is HTTP or HTTPS, move to request-content dependence. Does any routing, security, or session decision depend on the URL path, the host header, a cookie, or the request body? If yes, Application Gateway is required, because every one of those decisions reads the parsed request, and only a layer-7 proxy holds it. Path routing, multi-site hosting, cookie affinity, and request inspection all live in this branch, and a single Yes settles the choice. This is the branch that most often forces the gateway over the load balancer even when cost would prefer the simpler service.

If the traffic is HTTP but no decision depends on the request's contents, move to the security mandate. Is a managed web application firewall required in front of the application? If yes, the WAF SKU of Application Gateway is the answer, because firewall inspection is a layer-7 act with no layer-4 equivalent. A firewall requirement is effectively a request-content dependence in disguise, since inspecting the request is reading it.

If none of those branches forced the gateway, you are at a workload that is HTTP, routes by nothing inside the request, and needs no firewall, which is rare for web traffic but does happen, for example a single backend pool served at one path with TLS terminated on the backends. Here both services could carry the traffic, and the tiebreaker is cost and simplicity, which favor Load Balancer. The honest note is that pure cases like this are uncommon, because most web workloads eventually want at least path routing, host-based hosting, or a firewall, and planning for that near future often justifies starting on the gateway.

Finally, regardless of the layer outcome, decide reachability as a separate question. Does the endpoint need to be public or private? That choice selects the public or internal variant of whichever service the layer branches chose, and it never overrides the layer decision. Reachability and layer are decided independently and then combined.

```text
1. Is the protocol HTTP/HTTPS?
     No  -> Load Balancer (Application Gateway cannot carry it)
     Yes -> continue
2. Does a routing/security/session choice depend on path, host, cookie, or body?
     Yes -> Application Gateway
     No  -> continue
3. Is a managed web application firewall required?
     Yes -> Application Gateway (WAF SKU)
     No  -> continue
4. Both can work; choose Load Balancer for cost and simplicity
   (reconsider if a layer-7 need is imminent)
5. Separately: public or internal? -> pick the matching variant of the chosen service
```

This branch walk is the decision table from earlier rendered as a procedure, and either form works. Some engineers prefer to scan the table and find the row; others prefer to run the branches in order. Both reduce to the same rule, that the layer the requirement lives at picks the service, with cost serving only as a tiebreaker when the layer genuinely does not decide.

### If my app needs both raw TCP services and HTTP routing, which do I choose?

Use both. Put the HTTP traffic that needs path routing, host-based hosting, TLS termination, or a firewall on an Application Gateway, and put the raw TCP or UDP services on a Load Balancer. They coexist in one architecture, each handling the traffic its layer suits. Forcing everything onto one service either strands the non-HTTP traffic or wastes a proxy on flows that never needed one.

This split is common in real systems that expose a web front and a set of non-web endpoints, such as an application with an HTTP API behind a gateway and a separate streaming or database endpoint behind a load balancer. The architecture is not more complex for using two services; it is correctly factored, with each requirement placed at its proper layer. The mistake would be insisting on a single device and then fighting its layer for the traffic it was never built to handle.

## Run and reproduce the comparison hands-on

Reading the layer rule builds the model, but the rule sticks once you have stood up both services, watched a Load Balancer forward an opaque TCP flow, and watched an Application Gateway split traffic by path under one hostname. The fastest way to do that without assembling a lab from scratch is to [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), which provides a sandbox where you can build a Standard Load Balancer and an Application Gateway side by side, point them at the same backend pool, and observe directly how each one treats the traffic. Seeing a path-based routing rule send `/api` and `/static` to different pools, and then confirming that the load balancer cannot do the same, turns the abstract layer difference into something you have touched.

The same lab environment is the place to reproduce the patterns from this article: configure a layer-7 health probe and watch a backend flip to unhealthy on a host-header mismatch, terminate TLS at the gateway and inspect the decrypted request, or stand up an internal Load Balancer between two tiers and confirm it is unreachable from outside the network. The command library carries tested Azure CLI, PowerShell, and Bicep snippets for both services, so you can move from the minimal shapes in this article to a fuller configuration without guessing at flag names. Building the comparison yourself, rather than only reading it, is what converts the decision rule from something you recognize into something you reach for automatically the next time a requirement lands.

## Reading an inherited environment for the layer signal

Much of the time the decision is not made fresh but inherited, where you arrive at an existing system and must judge whether the load-balancing tier already in place is the right one. The same layer rule that guides a new choice also audits an old one, and a few quick reads tell you whether the inherited design matches its requirements or quietly mismatches them.

Begin by reading what the front device is configured to do, because the vocabulary gives it away. A configuration full of listeners, hostnames, certificates, URL path maps, and HTTP settings is an Application Gateway, and one full of frontend IPs, transport-level rules, and TCP or UDP ports is a Load Balancer. Once you know which service is deployed, ask the diagnostic question in reverse: does this workload actually use any layer-7 capability? If the system runs an Application Gateway but no routing depends on the path or host, no firewall is configured, no TLS is terminated at the gateway, and no cookie affinity is set, the gateway is doing a layer-4 job at a layer-7 price, and a Load Balancer would serve the same traffic for less. That is an over-build worth flagging, though not always worth immediately changing, since a migration carries its own cost and risk.

The opposite mismatch is rarer to find in place, because a workload that needed layer 7 and was put on a layer-4 device usually failed loudly during development rather than shipping. But it does appear when requirements grew after deployment, leaving a Load Balancer fronting a web application that has since sprouted a need for path routing or a firewall, satisfied through awkward workarounds such as a separate public IP per path or a firewall bolted onto each backend. Those workarounds are the symptom of a layer mismatch that has been patched rather than corrected, and the clean fix is to introduce an Application Gateway for the web traffic, consolidating the workarounds into the layer-7 features that were built for exactly this.

A second read concerns the surrounding network, because a front device can be correct while its integration is broken. Check whether the network security groups permit the platform's health-probe source for a load balancer, or the gateway manager's address range and infrastructure ports for an Application Gateway v2, since an overly tight rule there produces healthy backends that receive no traffic. Check the route tables for a user-defined route that sends backend traffic somewhere unexpected, breaking the return path. These integration faults masquerade as load-balancing failures, so reading them as part of the audit separates a genuine service mismatch from a network misconfiguration sitting beneath a perfectly appropriate service.

The audit ends where the new-build decision ends, with the layer question. Whether you are choosing for the first time or judging an inherited choice, the productive move is identical: identify whether the workload depends on the contents of the HTTP request, and confirm that the deployed service operates at the layer that dependence requires. A match is a correct design. A layer-7 service doing a layer-4 job is an over-build. A layer-4 service patched to fake layer 7 is an under-build with workarounds. Naming which of the three you are looking at is the whole skill, and it is the same skill in both directions.

## The verdict: let the layer pick the tool

The choice between Load Balancer versus Application Gateway is not a close judgment call that demands a long pros-and-cons weighing each time. It is a single structural question with a clear answer, and the entire purpose of this article has been to make that question reflexive. Load Balancer is a layer-4 distributor that forwards TCP and UDP flows by their transport tuple without ever reading the payload, which makes it fast, cheap, protocol-agnostic, and blind to anything inside an HTTP request. Application Gateway is a layer-7 reverse proxy that terminates the connection, parses the HTTP request, and acts on its contents, which gives it path routing, host-based hosting, TLS termination, cookie affinity, header rewriting, and a web application firewall, at the cost of per-request processing, a higher bill, and more operational surface.

Everything else flows from that. The features are layer-7 because they read the request. The cost gap exists because one service runs proxy capacity and the other is a fabric rule. The probe differences exist because each service probes at its own layer. The composition into global, regional, and internal tiers exists because each device fits one tier. When a requirement arrives, the productive move is to ask the one question that decides everything: does fulfilling this requirement depend on something inside the HTTP request? If yes, Application Gateway. If the traffic is not even HTTP, Load Balancer by elimination. If it is HTTP but nothing inside the request matters and no firewall is mandated, either works and the cheaper, simpler Load Balancer wins on the tiebreaker, with an eye on whether a layer-7 need is coming soon.

Hold the layer rule and the rest of the comparison stops being a matrix to memorize and becomes a consequence to derive. That is the difference between an engineer who looks up the answer each time and one who already knows it, and it is the capability this article set out to leave you with.

## Frequently Asked Questions

### Q: Should I use Azure Load Balancer or Application Gateway for my workload?

Decide by the layer the workload needs. If the traffic is plain TCP or UDP, or it is HTTP but no routing, security, or session decision depends on the URL path, host header, cookie, or body, use Load Balancer, which is cheaper and adds almost no latency. If any decision depends on the contents of the HTTP request, or a managed web application firewall is required, use Application Gateway, because reading and acting on the request is a layer-7 capability the load balancer structurally lacks. The fast version of the test is to ask whether a device that sees only IP addresses, ports, and protocol numbers could do the job. If yes, the load balancer suffices. If fulfilling the requirement needs the URL, the host, the cookie, or the payload, only the gateway qualifies, and cost is irrelevant because the cheaper service cannot do it.

### Q: What is the practical difference between layer 4 and layer 7 load balancing?

Layer 4 balancing forwards traffic by the transport-level five-tuple, the source and destination IP and port plus the protocol, treating each flow as an opaque pipe and never reading the payload. Layer 7 balancing terminates the connection, reassembles the bytes into a full HTTP request, and makes decisions from the request's contents, such as the URL path, host header, and cookies. The practical consequences are direct. A layer-4 balancer is fast, protocol-agnostic, and cheap, but it cannot route by URL, terminate TLS, run a web firewall, or set a session cookie, because it never sees those things. A layer-7 balancer can do all of that because it parses the request, but it pays per-request processing cost and operates more machinery. The layer is not a tuning option; it is the structural floor that fixes what each service can and cannot do.

### Q: Can Azure Load Balancer do path-based or URL routing?

No. Path-based and URL routing require reading the URL inside an HTTP request, and Azure Load Balancer operates at layer 4, where it forwards flows by transport tuple and never parses the request. It has no URL to inspect, so it cannot send `/api` to one pool and `/static` to another. Adding a custom HTTP health probe does not change this, because a probe checks a path for health while traffic is still routed by the five-tuple; health checking and routing are separate concerns, and only the former gained a shallow HTTP ability. If the architecture needs to route by path under one hostname, that requirement forces Application Gateway, which holds the parsed request and can match the path against a URL path map. There is no Load Balancer configuration that enables URL routing, because the limitation comes from the layer the service works at, not from a missing setting.

### Q: Does Application Gateway support TCP or UDP traffic?

No. Application Gateway is an HTTP and HTTPS reverse proxy and does not carry raw TCP or UDP traffic. If a workload speaks a custom binary protocol, a database wire protocol, UDP, or any non-HTTP protocol, the gateway cannot accept it at all, and Load Balancer is the correct service by elimination. This is the mirror image of the path-routing limitation: just as the load balancer cannot rise to layer 7, the gateway cannot drop to plain transport-level forwarding of arbitrary protocols. A common design mistake is reaching for Application Gateway because it sounds like the more capable service, then discovering it will not even bind the non-web port the workload needs. When you have a mix of HTTP traffic that needs layer-7 features and non-HTTP services that need distribution, run both services together, each handling the traffic its layer suits, rather than forcing everything onto one.

### Q: Which Azure load balancing option includes a web application firewall?

Application Gateway includes a web application firewall through its WAF SKU, which inspects each request against managed rule sets targeting attack classes such as SQL injection and cross-site scripting, blocking or logging matches before they reach the backend. Load Balancer offers no web firewall, because inspecting request contents, including the body, requires a parsed HTTP request that a layer-4 device never assembles. When a security or compliance mandate requires a managed web firewall in front of an application, that single requirement settles the comparison in favor of Application Gateway regardless of cost or simplicity preferences, since there is no layer-4 path to a web firewall. A separate option places a firewall at a global edge service rather than at a regional gateway, which is a different architectural choice, but within this two-service comparison the firewall lives only on Application Gateway.

### Q: Is SSL termination possible on Azure Load Balancer?

No. SSL or TLS termination means decrypting the encrypted session, acting on the plaintext request, and optionally re-encrypting, all of which require reading the traffic. Azure Load Balancer operates at layer 4 and forwards encrypted bytes as an opaque stream, so it has no certificate and no plaintext to work with, and it cannot terminate TLS. It can pass an encrypted connection through to a backend that terminates TLS itself, which is a valid pattern, but the termination happens on the backend, not on the load balancer. Application Gateway can terminate TLS at the front, hold the certificate, decrypt, apply routing and firewall rules to the plaintext, and forward in plaintext or re-encrypt to the backend for end-to-end protection. Centralizing certificates at the gateway is one of its main attractions, and it is a layer-7 capability with no layer-4 equivalent.

### Q: When is Application Gateway overkill for a workload?

Application Gateway is overkill when the workload gains nothing from layer 7. A plain TCP or UDP service, a database front end, a streaming endpoint, or an HTTP workload that routes to a single backend pool with no path routing, host-based hosting, cookie affinity, TLS offload, or firewall requirement, all run perfectly on a Load Balancer for less money and with less latency. In those cases the gateway adds per-request processing cost, a higher bill, certificates to rotate, and a larger set of failure modes, in exchange for capabilities the workload never uses. The honest qualification is timing: if a layer-7 need such as a planned firewall or path split is genuinely imminent and certain, building the gateway early can save a migration. But choosing it speculatively, on the theory that more capable is safer, means paying continuously for sight the traffic does not need, which is the textbook over-build.

### Q: How do the pricing models of Load Balancer and Application Gateway compare?

Load Balancer is priced as a fabric rule with no data-path compute, centered on the rules configured and the data processed, which makes it inexpensive for distribution work. Application Gateway combines a fixed hourly charge with a consumption component measured in capacity units that reflect compute, persistent connections, and throughput, and the WAF SKU costs more than the standard SKU because rule inspection adds processing per request. In nearly every equivalent comparison the gateway costs more, because a proxy that terminates and re-originates every connection inevitably carries more cost than a rule applied in the network. Treat the exact rates as values to verify against the current Azure pricing page when you design, since SKUs and metering change. The durable point is structural rather than numeric: the gateway should earn its higher cost by delivering a layer-7 capability the workload truly requires, not by being chosen as a more impressive default.

### Q: Should I pick an internal or a public variant for a backend tier?

For a backend tier that should never be reachable from the internet, pick an internal variant, whose frontend binds to a private IP inside the virtual network. The more useful question is which service to make internal, and that is decided by the layer, not by the privacy requirement. If the internal tier just needs traffic spread across instances with no dependence on the request's contents, an internal Load Balancer is the precise fit, cheaper and lower-latency. If internal traffic must be routed by path, inspected by a firewall, or terminated for TLS, an internal Application Gateway earns its place. The mistake to avoid is conflating the public-versus-internal axis with the layer-4-versus-layer-7 axis. They are independent: decide reachability based on where traffic comes from, decide the layer based on what the device must do with the traffic, then combine the two answers.

### Q: Can I use Load Balancer and Application Gateway together in one architecture?

Yes, and doing so is common in well-factored designs. A single application might place an Application Gateway at the regional web tier to handle path routing, TLS termination, and the firewall, while an internal Load Balancer sits between the web tier and the application tier to spread internal calls that have no layer-7 need. Non-HTTP services in the same system, such as a streaming or database endpoint, sit on their own Load Balancer because the gateway cannot carry non-HTTP traffic. Seeing both services in one architecture is not indecision; it is each requirement placed at its correct layer. A global edge service can sit in front of the regional gateway to provide worldwide entry and cross-region failover, producing a three-tier composition of global edge, regional gateway, and internal load balancer. The skill is knowing which device belongs at which tier so the design is neither under-built nor over-built.

### Q: Does cookie-based session affinity require Application Gateway?

Yes, true cookie-based session affinity requires Application Gateway, because it works by issuing and reading an HTTP cookie that the gateway controls, and only a layer-7 proxy reads and writes HTTP headers where cookies live. This pins a client to the same backend for a session, which stateful applications that keep session data in process memory depend on. Load Balancer offers a coarser stickiness through source-IP affinity, a hash over two or three tuple fields that keeps a client on one backend by address rather than by cookie. Source-IP affinity can break when many clients share an address behind a NAT, or when a client's address changes, whereas cookie affinity is precise per browser session. So if the requirement is genuinely sticky sessions keyed on a cookie, the gateway is required; if a coarser address-based stickiness is acceptable, the load balancer can approximate it without rising to layer 7.

### Q: Can Application Gateway replace Load Balancer entirely?

No, Application Gateway cannot replace Load Balancer entirely, because it handles only HTTP and HTTPS and cannot carry raw TCP, UDP, or other non-HTTP protocols. Any system with non-web endpoints, such as database front ends, custom binary protocols, media streams, or game-server traffic, needs a Load Balancer for that traffic regardless of how much HTTP the gateway also handles. Even for purely web systems, an internal Load Balancer is often the better fit for a middle tier whose internal calls have no layer-7 need, since it is cheaper and lower-latency than an internal gateway. The two services are not a hierarchy where the more capable one subsumes the other; they are different layers with different competencies. The gateway does more at layer 7, but it cannot do the layer-4 job for non-HTTP protocols, so a complete architecture frequently needs both rather than one standing in for the other.

### Q: How does choosing the wrong layer show up as a problem later?

Choosing the wrong layer rarely fails immediately; it fails when a new requirement arrives that the chosen service structurally cannot meet. A workload placed on a Load Balancer hits a wall the day it needs path routing, a web firewall, or TLS offload, none of which the layer-4 service can grow, forcing a migration to Application Gateway that touches DNS, certificates, and probes under deadline pressure. A workload placed on Application Gateway hits a different wall when it turns out to need a non-HTTP endpoint the gateway cannot carry, requiring a Load Balancer to be added anyway. In both cases the symptom is a redesign that the original layer question would have prevented. The cost of the wrong choice is not a runtime error but an architectural migration, which is why deciding the layer correctly at the start, by asking whether the requirement depends on the request's contents, pays off well beyond the first deployment.

### Q: Do health probes mark backends down differently on each service?

Yes, because each service probes at the layer it operates at. A Load Balancer probe confirms transport-level reachability: a TCP probe marks a backend healthy when the handshake completes, saying nothing about whether the application serves correct responses, while a Standard-tier HTTP probe adds a shallow path check. An Application Gateway probe issues a real HTTP request and judges the response status and, optionally, a body match, so it tests the application rather than just the socket. The consequence is that the same backend can pass a layer-4 TCP probe by merely listening yet fail a layer-7 probe on a host-header mismatch, an unexpected redirect, or a status the gateway is not told to accept. When a backend looks healthy on one service and unhealthy on the other after a migration, the probe layer is almost always the explanation, and the fix is to align the gateway probe's path, host, and expected status with what the backend actually serves.

### Q: Is the Standard tier required to compare Load Balancer fairly with Application Gateway?

For any production comparison, yes, reason about the Standard Load Balancer rather than the Basic tier. Basic lacks availability-zone support, the larger backend pool sizes, the secure-by-default posture, and the richer metrics that a serious deployment needs, and it is being retired, so comparing Basic against Application Gateway v2 is comparing a deprecated service against a current one. The fair comparison is Standard Load Balancer against Application Gateway v2, both zone-capable and production-grade, differing in layer rather than in maturity. On the gateway side, design against the v2 SKU and, when a firewall is needed, the WAF v2 SKU, rather than the legacy v1. Verify the current tier and SKU availability when you build, since Azure adjusts SKUs over time, but the principle holds: compare the current production-grade tier of each so the difference you are weighing is layer 4 versus layer 7, not old versus new.

### Q: Which service belongs at the regional tier when a global entry point already exists?

When a global edge such as Azure Front Door already provides worldwide entry, caching, and a global firewall, the regional tier behind it is usually an Application Gateway for web traffic that needs regional path routing or a regional firewall, or a Load Balancer for regional distribution of non-web or layer-7-free traffic. The global tier and the regional tier are not competitors; they compose, with the global edge deciding where in the world a request lands and the regional service deciding which backend pool inside that region serves it. The decision at the regional tier follows the same layer rule as always: layer-7 web needs go to the gateway, layer-4 or non-HTTP needs go to the load balancer. The broader question of when to use a global edge, a content delivery network, or a regional gateway is a separate comparison, but within a region the layer rule still governs which of the two services you reach for.

### Q: How do I migrate from a Load Balancer to an Application Gateway when a layer-7 need appears?

Introduce the Application Gateway as the new public front for the HTTP and HTTPS traffic while keeping any non-web traffic on the existing Load Balancer. The migration centers on three moves: point the application's DNS hostname at the gateway's static public IP, move the TLS certificates to the gateway so it can terminate and present them, and recreate the health probes as HTTP probes that check a real path and expected status. Configure the listeners, routing rules, and any URL path map to reproduce how requests should reach the backends, then validate against the gateway's backend-health view before cutting traffic over. Keep the load balancer in place for non-HTTP ports, since the gateway cannot carry them. The migration is bounded and well understood, but it touches DNS, certificates, and probes at once, which is precisely the work a correct early layer choice would have saved, so plan the cutover with a rollback that repoints DNS if validation fails.

### Q: Why does Application Gateway add latency that Load Balancer does not?

Application Gateway adds latency because it is a reverse proxy that terminates the client connection, parses the full HTTP request, evaluates routing and firewall rules, and opens a separate connection to the backend to relay the request. Each of those steps takes processing time, and the proxy sits in the data path consuming capacity. Load Balancer adds almost no latency because it never assembles a request; it is a rule in the network fabric that forwards flows by their transport tuple, so there is no per-request parsing tax and no proxy instance in the path. The latency the gateway adds is the price of sight, the cost of a device that reads and acts on every request, and it is worth paying only when the workload needs the layer-7 capabilities that reading enables. For a latency-sensitive non-web service, that overhead is pure cost with no benefit, which is one more reason such workloads belong on the layer-4 service.

This is a technical comparison rather than a sensitive topic, but if any part of a real outage or security concern sits behind your question, a colleague who knows your specific environment is the right person to confirm the design before you ship it.
