---
layout: post
title: "Fix Azure Front Door 502 and Origin Errors"
page_title: "Fix Azure Front Door 502 Origin Error: Diagnose Unhealthy Origin, Host Header, SNI, and Service Tag Causes"
date: 2022-12-19
categories: ["Technology"]
tags: ["Azure", "Front Door", "502 Bad Gateway", "Troubleshooting", "Networking", "Cloud Computing"]
excerpt: "A Front Door 502 origin error almost always means the backend rejected the request, not the edge. Diagnose the host header, SNI, probe, and service tag."
image: "/assets/images/blog/blog-94.webp"
reading_time: 59
author: "ryan-walsh"
last_updated: 2022-12-19
lang: en
---
A Front Door 502 is one of the most misread errors in Azure, because the page that surfaces it sits at the edge while the actual fault almost always lives at the upstream server behind it. When Azure Front Door returns a 502, it is telling you that it reached out to your configured origin, tried to get a valid response, and could not. The edge did its job: it accepted the client request, matched a route, selected a backend from the group, and forwarded the request. What it could not do was complete a usable round trip to the server you pointed it at. That gap, between a healthy edge and an upstream server that will not answer the way Front Door expects, is the entire subject of this article, and learning to localize the 502 to the origin contract is the difference between an afternoon of guessing and a five-minute fix.

![Fixing Azure Front Door 502 origin error root causes - Insight Crunch](/assets/images/blog/blog-94.webp)

The reason engineers waste so much time on a Front Door 502 is that the symptom and the cause sit in different places. The browser shows a generic Microsoft error page, the kind that says the service is not available right now, and the natural instinct is to blame Front Door, open a support ticket about the edge, or start toggling routing rules. Most of the time none of that is the problem. The origin behind the edge is rejecting an unexpected host header, failing its health probe, presenting a certificate Front Door will not trust, timing out under load, or sitting behind a firewall that silently drops the edge's traffic. This article gives you the InsightCrunch Front Door 502 cause table, a confirming signal for each cause, and the tested fix, so you can name which of the distinct failures is yours and repair the server or the routing instead of the edge.

## What a Front Door 502 actually means

A Front Door 502 means the edge could not obtain a valid response from the backend server it selected for your request. Front Door is a reverse proxy running across Microsoft's global edge network. A client connects to the nearest edge point of presence, the edge terminates that connection, evaluates your route, picks an origin from the origin group, opens its own connection to that backend, and relays the request. The 502 is generated at the moment the second leg of that journey, edge to origin, fails to produce something the edge can hand back to the client.

That framing matters because it tells you where to look. A 502 is not a client problem and it is rarely an edge problem. It is a statement about the relationship between Front Door and the server you told it to talk to. The edge forwards the request with a specific host header, over a specific protocol, to a specific address, and it expects a response within a timeout, over a connection it can establish, secured by a certificate it can validate when the origin is HTTPS. If any link in that chain breaks, the edge has nothing valid to relay, and it answers the client with a 502.

It helps to separate the 502 from its neighbors before going further. A 502 says the edge talked to the target server and got back something unusable, or could not finish the exchange at all. A 503 from Front Door usually means the edge itself has no healthy origin to send the request to, or the request hit a platform condition like rate limiting. A 504 means the backend accepted the connection but did not finish responding inside the allowed window, a pure timeout. The codes overlap in practice, and the same underlying origin problem can surface as a 502 in one configuration and a 504 in another, which is exactly why reading the precise error subcode rather than the bare HTTP status is the first diagnostic move.

### Why does Front Door return a 502 when my origin is healthy?

Because Front Door forwards the host header you configure, a 502 with a server that is up and serving traffic almost always means the origin is rejecting that forwarded host or refusing the edge's certificate, not that anything failed on the platform. The server is healthy for requests it recognizes; it simply does not recognize the request Front Door is sending it. Confirm by reproducing the exact request the edge makes, host header and all, against the upstream server directly.

This is the namable claim at the center of the whole diagnosis, the server-host-header rule. The edge does not send your custom domain to the origin by default in every configuration; it sends whatever host header the origin definition tells it to send, and the backend server behaves according to that header. A web server with name-based virtual hosts, an App Service with host name bindings, an ingress controller with host rules, or a reverse proxy with server blocks all route on the host header. If the host header the edge forwards does not match a name the target server is configured to serve, the origin returns a 404, a redirect, a connection reset, or a TLS failure, and the edge translates that dead end into a 502 for the client. The server is healthy. The contract between the edge and the server is broken.

## How to read a Front Door 502 and gather the diagnostic signal

The single most useful habit when chasing a Front Door 502 is to stop reading the browser page and start reading the response headers and the resource logs, because Front Door embeds the real diagnostic information there. The generic error page is deliberately uninformative to the public; the detail you need rides alongside it in headers and lands in your log workspace if you have logging enabled.

Front Door stamps every response with an `X-Azure-Ref` value, a tracking identifier that ties the client-visible failure to the internal telemetry for that exact request. When you open a support case or correlate against logs, that reference is the thread you pull. Capture it first. A simple verbose request from your own machine shows you both the status and the reference, along with the cache disposition that tells you whether the request was even forwarded to the backend:

```bash
curl -sv https://www.contoso.com/health 2>&1 | grep -iE "x-azure-ref|x-cache|HTTP/"
```

The `X-Cache` header is more revealing than it looks. A value indicating a cache miss or a no-cache configuration means the request was forwarded to the upstream server, so a 502 alongside a miss points squarely at the server leg. A value indicating a cache hit means Front Door served the response from its own store and never touched the origin, so a 502 there would implicate the edge or the cached object rather than the server. For a 502 you are almost always looking at a forwarded request, and confirming that with the cache header rules out a stale cached error before you go any further.

Front Door also supports debug response headers that expose the route and origin it selected and the internal reason for a failure. When you enable the optional debug headers on the profile, responses carry the matched route name and the selected origin, which immediately tells you whether the edge even picked the backend server you expected. If the edge selected the wrong origin group because of a routing rule, the debug headers reveal that before you waste time inspecting a healthy server that was never in the request path.

### How do I read Front Door origin health to diagnose a 502?

Read it in two places at once: the origin group's health probe status in the portal or CLI, and the resource logs filtered to the failed request's reference. The probe status tells you whether the edge currently considers the target server reachable and healthy; the logs tell you the exact error subcode for the specific 502 you are chasing. Together they separate a probe-level outage from a per-request rejection.

The resource logs are where the precise subcode lives, and the precise subcode is what collapses five possible causes down to one. Enable diagnostic settings on the Front Door profile and route the access log to a Log Analytics workspace, then query for the failing requests. Front Door's access log records an error info field on failures that carries values like a server connection abort, an origin certificate problem, a backend that is unhealthy, or a request that timed out at the origin. Each of those values maps to a different row in the cause table below, so the query is the fastest path from symptom to cause:

```kusto
AzureDiagnostics
| where ResourceType == "FRONTDOORS" or Category == "FrontDoorAccessLog"
| where httpStatusCode_s == "502"
| project TimeGenerated, requestUri_s, errorInfo_s, originName_s, routingRuleName_s, pop_s, timeTaken_d
| order by TimeGenerated desc
| take 100
```

Read the `errorInfo_s` column first. An abort on the backend connection points at a network reset, an idle timeout on an intermediate load balancer, or a service tag block. A certificate value points at the TLS leg. An unhealthy origin value points at the probe. A timeout value points at origin latency. The `originName_s` and `routingRuleName_s` columns confirm which origin and which route handled the request, which catches the wrong-origin-group case before you debug the wrong server. The `timeTaken_d` value distinguishes a fast failure, which usually means a connection or certificate rejection, from a slow failure, which usually means a timeout under load.

One caution on logs: enabling diagnostic settings does not backfill history, so if you have not been logging, you will not have data for the 502 that already happened. Turn logging on now, reproduce the failure, and then query. For a failure you cannot reproduce on demand, the access log is the only durable record, which is why every production Front Door profile should ship its access log to a workspace from the day it goes live.

## The InsightCrunch Front Door 502 cause table

Almost every Front Door 502 reduces to one of a small set of distinct causes, each with a confirming signal you can check and a fix that targets it. This table is the findable artifact for this article, the InsightCrunch Front Door 502 cause table. Read across each row: the cause, the signal that confirms it is yours, and the fix that resolves it. The sections after the table walk through each cause with the commands to confirm and repair it.

| Cause | Confirming signal | Fix |
| --- | --- | --- |
| Unhealthy origin (probe failing) | Origin shows unhealthy in the origin group health; probe path returns non-200 or a redirect; error info reports an unhealthy origin | Make the probe path return a clean 200; align probe protocol, port, and method with what the upstream server serves |
| Origin response timeout | Slow failures with high time taken; error info reports a timeout; origin slow under load | Reduce origin latency, raise the origin response timeout, fix the slow dependency or scale the origin |
| Origin host header mismatch | Origin returns 404, redirect, or reset for the forwarded host; works when you send the expected host directly | Set the origin host header to the value the server expects, or align the backend server to accept the forwarded name |
| Certificate or SNI mismatch on HTTPS origin | Error info reports a certificate problem; origin presents a self-signed or name-mismatched certificate | Present a trusted-CA certificate matching the origin host name, or fix the SNI and name validation settings |
| Service tag or firewall block | Probe and requests fail silently; origin logs show no Front Door traffic; NSG or firewall denies the edge | Allow inbound from the AzureFrontDoor.Backend service tag on the backend's listening port |
| Wrong origin group in routing rule | Debug headers or logs show an unexpected origin selected; the healthy server was never in the path | Point the routing rule at the correct origin group and verify origin definitions |
| Private Link origin not approved | Private endpoint connection sits in pending rather than connected; edge cannot route through it | Approve the Private Link connection so it reaches the connected state |

The discipline this table enforces is the discipline the whole series argues for: do not apply a fix until you have confirmed the cause. Reproducing the edge's request against the origin directly, reading the error subcode in the access log, and checking the origin group health are three cheap checks that point you at exactly one row. Guessing, by contrast, tends to produce a sequence of unrelated changes that mask the real fault and break something else.

## Cause one: an unhealthy origin failing its health probe

The most common Front Door 502, and the one that produces the most confusion, comes from a health probe that the target server is failing. Front Door continuously probes each backend in an origin group on a configured path, protocol, and interval. If the probe does not get a clean success, the edge marks that server unhealthy and stops sending it traffic. When every backend in the group is unhealthy, there is no server to forward to, and requests fail. Depending on the exact disposition, that can surface as a 502 or a 503, and the access log error info will name an unhealthy origin condition.

What trips engineers up is that the backend is often perfectly capable of serving real traffic while still failing the probe, because the probe path and the application path are different things. A probe configured against the site root might receive a redirect from HTTP to HTTPS, and Front Door treats a 301 or 302 on the probe path as a probe failure rather than a success. A probe against a path that requires authentication receives a 401 and fails. A probe against a path that does not exist receives a 404 and fails. A probe configured for HTTPS against an upstream server that only listens on HTTP fails to connect at all. In every one of these cases the application works when a real user hits the right path, but the probe never sees a 200, so the edge considers the origin dead.

### Why does my origin show unhealthy when the application works?

Because Front Door judges origin health by the probe path's response, not the application's, and a probe path that returns a redirect, a 401, a 404, or connects on the wrong protocol fails the probe even when real traffic succeeds. Front Door requires a clean success on the probe; a 301 redirect counts as a failure. Point the probe at a lightweight path that returns a plain 200 over the same protocol and port the upstream server actually serves.

To confirm this cause, check the origin group health and then test the probe path exactly as the edge tests it. In the portal the origin group blade shows each server's current health state; from the CLI you can inspect the origin group and the probe configuration so you know what path and protocol the edge is using:

```bash
az afd origin-group show \
  --resource-group rg-edge \
  --profile-name fd-contoso \
  --origin-group-name og-api \
  --query "{probePath:healthProbeSettings.probePath, probeProtocol:healthProbeSettings.probeProtocol, probeMethod:healthProbeSettings.probeRequestType, probeInterval:healthProbeSettings.probeIntervalInSeconds}" \
  --output table
```

Then reproduce the probe against the server directly, using the probe's protocol and path, and watch the status code the backend server returns. If you see anything other than a 200, you have found the cause:

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://origin.internal.contoso.com/health
```

The fix is to give the probe a path that returns a clean 200 over the protocol and port the target server serves. Build a dedicated lightweight health endpoint on the backend that returns a 200 with a tiny body, requires no authentication, and does not redirect. Point the probe at that path. Match the probe protocol to the server's listener: probe HTTPS if the origin serves HTTPS, probe HTTP if it serves HTTP, and probe the port the upstream server actually listens on. If the server redirects HTTP to HTTPS at the site root, do not probe the root; probe a path that answers directly. A well-designed health endpoint also reflects real readiness, returning a non-200 when a critical downstream dependency is unavailable, so that Front Door pulls a server out of rotation when it genuinely cannot serve requests rather than only when it is completely down.

There is a subtle variant worth naming. With multiple origins in a group, a single unhealthy origin does not by itself cause a 502, because the edge routes around it to the healthy ones. The 502 appears when enough origins fail the probe that the group has no healthy member, or when there is only one origin and it fails. If you have intermittent 502s under load with a multi-origin group, suspect that origins are flapping in and out of health as the probe catches them during brief slow periods, which points you toward the timeout cause below as much as the probe configuration itself.

## Cause two: an origin response timeout under load

A timeout cause produces a slower, more intermittent 502 than a probe failure, and the access log gives it away through a high time-taken value paired with a timeout in the error info. Here the edge establishes a connection to the origin and sends the request, but the backend server does not finish responding inside the window the edge allows. The edge gives up and returns a 502 to the client, or a 504 depending on exactly where in the exchange the deadline hit. The connection worked, the certificate validated, the host header matched; the server simply was too slow.

This cause is insidious because it is load-dependent. At low traffic the target server responds in tens of milliseconds and everything looks fine. Under load, a slow database query, an exhausted connection pool, a saturated CPU, garbage collection pauses, or a downstream dependency that itself slowed down pushes the origin's response time past the edge's timeout, and a fraction of requests start returning 502. The error appears to come and go for no visible reason, which is the signature of a timeout rather than a configuration mistake. A configuration mistake fails every request the same way; a timeout fails the slow ones.

### How do I tell a Front Door 502 timeout from a connection failure?

Read the time-taken value in the access log. A connection or certificate rejection fails fast, in single-digit or low double-digit milliseconds, because the backend refuses or resets immediately. A timeout fails slow, at or near the configured origin response timeout, because the edge waited for a response that never completed. Fast 502s point at host headers, certificates, or service tags; slow 502s point at origin latency.

To confirm, query the access log for the failing requests and look at the distribution of time taken alongside the error info:

```kusto
AzureDiagnostics
| where Category == "FrontDoorAccessLog" and httpStatusCode_s == "502"
| summarize count(), avg(timeTaken_d), percentile(timeTaken_d, 95) by errorInfo_s, originName_s
| order by count_ desc
```

If the average and ninety-fifth percentile time taken sit close to your configured origin response timeout, the upstream server is timing out. Correlate that against the upstream server's own application metrics for the same window: response latency, request queue length, CPU, memory, and any database or dependency latency. The 502 timestamps should line up with latency spikes on the server, which confirms that the edge is timing out on a genuinely slow server rather than failing for a configuration reason.

The fix has two levers, and the order matters. The durable fix is to make the origin faster or to give it more capacity, because a timeout is the backend server telling you it cannot keep up. Profile the slow path, fix the slow query or the exhausted connection pool, add caching for expensive responses, or scale the target server out so each instance carries less load. The second lever is to raise the origin response timeout on Front Door so the edge waits longer before giving up, which is appropriate when the origin legitimately needs more time for certain requests, such as large file generation or long-running reports. Raising the timeout alone, without addressing the latency, only converts fast 502s into slow successful-but-painful responses and does nothing for the underlying saturation, so treat it as a tuning knob rather than a fix. The strategic position is to fix the backend first and adjust the timeout to match the backend's real, healthy response profile.

## Cause three: the origin host header mismatch

The host header mismatch is the cause that most directly embodies the upstream server-host-header rule, and it produces a 502 with a server that is demonstrably up. Front Door forwards a host header to the origin determined by the server's configuration. If you leave the origin host header blank in some configurations, the edge forwards the incoming host, your custom domain; if you set it explicitly, the edge forwards that value. The origin then routes the request based on that host header, and if it does not recognize the value, it rejects the request, which the edge surfaces as a 502.

This bites hardest when the backend server does name-based routing, which most modern origins do. An App Service maps requests to a site by host name binding, so a request carrying a host the app does not have bound returns the default page or a rejection. A Kubernetes ingress matches host rules, so a host with no matching rule gets a 404 or the default backend. An NGINX or IIS server selects a server block or site by host header, so an unrecognized host hits the wrong site or none at all. In each case the server is healthy and serving its real traffic; it just refuses the host header Front Door sent.

### Why does a wrong origin host header produce a Front Door 502?

Because the origin routes on the host header, and a header it does not recognize gets a 404, a redirect, or a connection reset rather than a 200, which the edge translates into a 502. The edge forwards exactly the host you configure on the origin definition; the target server treats that as the site to serve. If that host does not match a name the backend is configured for, the origin rejects it, and the client sees a 502. Set the origin host header to the name the upstream server expects.

To confirm, reproduce the edge's request against the server with the exact host header the edge forwards, then again with the host the origin expects, and compare. First read what host header the origin definition tells the edge to send:

```bash
az afd origin show \
  --resource-group rg-edge \
  --profile-name fd-contoso \
  --origin-group-name og-api \
  --origin-name origin-1 \
  --query "{hostName:hostName, originHostHeader:originHostHeader, httpsPort:httpsPort, enabledState:enabledState}" \
  --output table
```

Then send a request to the server's actual address while forcing the host header the edge uses, which is the request the backend server is rejecting:

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  --resolve www.contoso.com:443:203.0.113.10 \
  https://www.contoso.com/
```

If that returns a 404, a 301, or a reset while a request carrying the upstream server's own expected host name returns a 200, the host header is your cause. The fix is to align the two ends of the contract. Either set the origin host header on the Front Door origin definition to the name the target server is configured to serve, so the edge forwards a host the backend recognizes, or add a binding, an ingress rule, or a server block on the origin for the host the edge forwards. Setting the origin host header explicitly is usually the cleaner fix, because it keeps the backend's configuration stable and makes Front Door adapt to it:

```bash
az afd origin update \
  --resource-group rg-edge \
  --profile-name fd-contoso \
  --origin-group-name og-api \
  --origin-name origin-1 \
  --origin-host-header origin.internal.contoso.com
```

After the change, reproduce the request through Front Door and confirm a 200. The choice between forwarding the custom domain and forwarding the server's internal name has downstream effects worth thinking through: an application that builds absolute URLs from the host header, sets cookies scoped to the host, or enforces host-based security will behave differently depending on which name it sees, so pick the host header that keeps the application's own host-dependent logic correct, not just the one that stops the 502.

## Cause four: a certificate or SNI mismatch on an HTTPS origin

When the upstream server is HTTPS, the TLS handshake between the edge and the server adds two more ways to produce a 502, and the access log names a certificate problem in the error info. Front Door establishes its own TLS connection to the origin, and it validates the backend server's certificate the way any strict client would. It uses the origin host name as the Server Name Indication during the handshake, the target server must present a certificate that matches that name, and the certificate must chain to a Certificate Authority that Front Door trusts. Break any of those and the handshake fails before a single byte of HTTP is exchanged, and the edge returns a 502 with a certificate error subcode.

The most frequent version of this is a self-signed certificate on the origin. Front Door accepts certificates issued by a Certificate Authority on the Microsoft-trusted list; a self-signed certificate does not chain to any trusted CA, so Front Door refuses it and the request fails with a certificate error. Engineers who set up a backend with a self-signed certificate for internal testing, then point Front Door at it, hit this immediately. The second version is a name mismatch: the certificate is from a trusted CA but its subject or subject alternative name does not match the host name Front Door uses for SNI, so validation fails on the name even though the chain is fine. A third version is an expired or not-yet-valid certificate, which fails validation on the date.

### Can an origin certificate problem cause a Front Door 502?

Yes, and it is a fast, total failure rather than an intermittent one. Front Door validates the origin certificate against the origin host name and the Microsoft-trusted CA list during the TLS handshake, so a self-signed certificate, a name mismatch against the SNI, or an expired certificate fails the handshake and produces a 502 with a certificate error subcode. Present a trusted-CA certificate whose name matches the origin host name, or align the certificate name validation setting.

To confirm, inspect the certificate the backend presents for the name Front Door uses as SNI, and check the chain, the name, and the validity dates:

```bash
echo | openssl s_client -connect origin.internal.contoso.com:443 \
  -servername origin.internal.contoso.com 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
```

Read three things in the output. The subject and any subject alternative names must include the host name Front Door uses for SNI, which is the origin host name. The issuer must be a real CA, not the certificate itself, because a self-signed certificate lists itself as the issuer. The validity dates must straddle the current time. If the issuer is self-signed, if the name does not match, or if the certificate has expired, you have confirmed the certificate cause.

The fix depends on which version you hit. For a self-signed certificate, replace it with one issued by a publicly trusted CA whose name matches the origin host name. This is the correct production fix and the only one that works without weakening validation. For a name mismatch, either reissue the certificate to include the origin host name or set the origin host header to a name the existing certificate already covers, so the SNI and the certificate agree. Front Door also exposes a certificate subject name validation setting on the upstream server; disabling it tells the edge to skip the name check, which can be a deliberate choice for an internal origin whose certificate name cannot match, but it weakens the security of the edge-to-origin leg and should be a considered decision rather than a reflex. The strategic default is a trusted-CA certificate that matches the origin host name and full validation enabled, because that closes the gap a permissive setting would leave open.

## Cause five: a service tag or firewall block

A service tag block produces the most baffling Front Door 502 because the failure is silent at the server: the upstream server's own logs show no requests from Front Door at all, because the packets never arrive. The edge's traffic, both the health probes and the real requests, is being dropped by a network security group, an Azure Firewall, an on-origin firewall, or an appliance in front of the origin before it ever reaches the listening port. From the edge's perspective the backend server is unreachable; from the backend's perspective there is nothing to see.

Front Door's outbound traffic originates from a set of Microsoft edge addresses that change over time, so allowing it by static IP is fragile and quickly goes stale. Azure provides the `AzureFrontDoor.Backend` service tag precisely for this: it represents the set of addresses Front Door uses to reach origins, and Microsoft keeps it current as the address set evolves. The origin's inbound security rules must allow traffic from that service tag on the port the target server listens on, typically 443 for HTTPS or 80 for HTTP. Without that allow rule, the NSG or firewall denies the edge's probes and requests, the origin appears unhealthy or unreachable, and clients get a 502.

### Can a firewall blocking the Front Door service tag cause a 502?

Yes, and it is the cause to check when the backend's own logs show no Front Door traffic at all. Front Door reaches origins from the addresses represented by the AzureFrontDoor.Backend service tag, and if the server's NSG, Azure Firewall, or host firewall does not allow inbound from that tag on the listening port, the probes and requests are dropped before they arrive, the upstream server looks unreachable, and the client sees a 502. Add an inbound allow rule for the AzureFrontDoor.Backend service tag.

To confirm, inspect the upstream server's effective inbound rules and check the origin's access logs for the period of the failure. If the server logs no requests from Front Door, the traffic is being dropped upstream. Look at the NSG rules on the backend's subnet or interface:

```bash
az network nsg rule list \
  --resource-group rg-origin \
  --nsg-name nsg-origin-subnet \
  --query "[].{name:name, priority:priority, direction:direction, access:access, source:sourceAddressPrefix, ports:destinationPortRange}" \
  --output table
```

If there is no rule allowing inbound from the `AzureFrontDoor.Backend` service tag on the server's port, or if a higher-priority deny rule shadows the traffic, you have found the cause. The fix is to add an inbound allow rule for the service tag at a priority above any broad deny rule:

```bash
az network nsg rule create \
  --resource-group rg-origin \
  --nsg-name nsg-origin-subnet \
  --name Allow-FrontDoor-Backend \
  --priority 200 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefixes AzureFrontDoor.Backend \
  --destination-port-ranges 443 \
  --description "Allow inbound from Azure Front Door edge to origin"
```

For an Azure Firewall in front of the backend server, the equivalent is a network rule allowing the service tag as source on the relevant port. For a host-based firewall on a virtual machine origin, allow the service tag's address ranges, ideally driven from the published service tag data rather than hand-entered addresses, because those addresses change. There is one more layer worth restricting after you allow the tag: allowing only the `AzureFrontDoor.Backend` service tag means anyone could in principle route through Front Door to your backend, so production origins commonly add a check on the `X-Azure-FDID` header, which Front Door stamps with your specific profile identifier, and reject requests that do not carry your expected value, ensuring traffic arrives only through your own Front Door instance and not someone else's.

## Cause six: a routing rule pointing at the wrong origin group

The wrong-origin-group cause is the one that wastes the most time when undiagnosed, because the engineer debugs a healthy server that was never in the request path. Front Door matches each request to a route based on the domain and the path pattern, and the route forwards to an origin group. If a route's path pattern is misconfigured, or a route forwards to the wrong origin group, or two routes overlap and the wrong one wins, the request lands at an upstream server you did not intend, and if that backend cannot serve the request you get a 502. You then inspect the target server you meant to use, find it perfectly healthy, and grow more confused with every check.

This surfaces in a few recurring shapes. A new origin group is created for a new service but the route still points at the old one. A path pattern is too broad and catches requests meant for a different route. A wildcard route and a specific route both match a request and the precedence resolves to the wrong one. A staging origin group is left wired to a production route after a test. In each case the edge is doing exactly what the configuration says; the configuration just says the wrong thing.

### Why would a routing rule send my request to the wrong origin group?

Because Front Door selects a route by matching the request's domain and path pattern, and a misconfigured pattern, an overlapping route, or a route wired to the wrong origin group sends the request somewhere you did not intend. The edge follows the route precedence and path match exactly; if those resolve to a server that cannot serve the request, the result is a 502 from a server you never meant to use. Read the matched route and selected origin from the debug headers or the access log.

To confirm, enable the Front Door debug response headers and read which route matched and which origin was selected, or read the same fields from the access log's routing rule and origin name columns. The CLI also lets you inspect the route's path patterns and the origin group it forwards to:

```bash
az afd route show \
  --resource-group rg-edge \
  --profile-name fd-contoso \
  --endpoint-name ep-contoso \
  --route-name route-api \
  --query "{patterns:patternsToMatch, originGroup:originGroup.id, forwardingProtocol:forwardingProtocol, httpsRedirect:httpsRedirect}" \
  --output table
```

If the matched route's origin group is not the one you expected, or the path patterns catch requests they should not, you have confirmed the routing cause. The fix is to correct the route: point it at the intended origin group, tighten or correct the path patterns so each route matches only the requests it should, and resolve any overlap by making patterns specific enough that precedence is unambiguous. After the change, send a request for the affected path and read the debug headers again to confirm the edge now selects the correct origin group and returns a 200. Keeping route definitions in infrastructure as code, where the path patterns and origin group references are reviewed before they deploy, prevents most of this class of mistake, because the overlap or the wrong reference is visible in the diff rather than discovered in production.

## Cause seven: a Private Link origin not approved

When the backend sits behind Private Link rather than on a public address, an additional state has to be correct, and a Front Door 502 appears when it is not. Front Door Premium can reach a backend privately through a Private Link service, which projects the upstream server into Front Door's managed network without exposing it publicly. For that path to carry traffic, the private endpoint connection that Front Door creates against the upstream server's Private Link service must be approved on the origin side. Until it is approved, the connection sits in a pending state, the edge cannot route through it, the server is unreachable from Front Door, and clients get a 502.

This is a setup-time failure that masquerades as a runtime one. The Front Door configuration looks complete, the backend server is healthy on its own network, and yet every request fails, because the private path between them is half-built. The connection request exists but no one approved it, so the tunnel is not live.

To confirm, check the state of the private endpoint connection on the backend's Private Link service. A pending state confirms the cause; a connected state rules it out:

```bash
az network private-endpoint-connection list \
  --resource-group rg-origin \
  --name pls-origin \
  --type Microsoft.Network/privateLinkServices \
  --query "[].{name:name, status:properties.privateLinkServiceConnectionState.status}" \
  --output table
```

The fix is to approve the pending connection so the private path becomes live:

```bash
az network private-endpoint-connection approve \
  --resource-group rg-origin \
  --name <connection-name> \
  --type Microsoft.Network/privateLinkServices \
  --description "Approved for Front Door private origin"
```

After approval the connection moves to connected, the edge can route through the private path, and requests succeed. The deeper model behind this, how Private Link projects a service into another network and why the approval step exists as a cross-tenant trust boundary, is worth understanding fully, and the [Private Link and private endpoint model](/2023/09/11/azure-private-link-deep-dive/) underpins not just this 502 case but a whole family of private-origin patterns across the platform. When you build private origins routinely, the approval step belongs in your provisioning automation so a freshly created origin is never left in pending.

## How the causes interact, and the order to check them

The seven causes are distinct, but they share a diagnostic spine, and checking them in the right order turns a confusing 502 into a quick one. Start by confirming the request even reached the target server, because that single check splits the seven causes into two groups. Read the access log's error info and the server's own logs together. If the backend logged the request, the edge reached it, and your cause is a host header rejection, a slow timeout, or a per-request problem the origin itself produced. If the upstream server logged nothing, the traffic never arrived, and your cause is a service tag block, a certificate failure that aborted the handshake before HTTP, a probe that marked the server dead, or a routing rule that sent the request to a different origin entirely.

From there the error subcode in the access log usually names the row directly. A certificate value sends you to the TLS leg. A timeout value with high time taken sends you to origin latency. An unhealthy origin value sends you to the probe. A connection abort sends you to the service tag, an intermediate idle timeout, or a network reset. The subcode is doing most of the work; the commands in each section above confirm the specific instance.

The order that wastes the least time is: reproduce the edge's exact request against the origin directly, because that one command distinguishes a host header mismatch and a certificate failure from everything else in seconds; read the access log error info and time taken, because that names the cause family; check the origin group health, because that catches the probe case; and check the routing rule's selected origin, because that catches the request going to the wrong server. Four checks, in that order, localize every row in the table. Reproducing what the edge sends, rather than what a browser sends, is the move that matters most, and it is the one engineers skip because it is slightly more work to forge the host header and the SNI than to refresh a browser tab.

### Does an unhealthy origin always cause a Front Door 502?

No. An unhealthy origin in a multi-origin group does not cause a 502 as long as at least one origin in the group stays healthy, because the edge routes around the unhealthy member to a healthy one. The 502 appears only when the group has no healthy origin to serve the request, whether because the single origin failed its probe or because every server in a multi-origin group failed at once. Use a multi-origin group with independent failure domains to keep one bad origin from taking the route down.

## Reproducing a Front Door 502 to confirm the cause

The fastest way to be certain which row of the cause table you are in is to reproduce the failure deliberately against a controlled backend, because a repro you can turn on and off proves the cause in a way that staring at a production incident rarely does. The series argues for reproducible diagnosis over description throughout, and a 502 is an ideal candidate, since each cause can be provoked with a small, reversible change and then cleared. Building the repro once teaches you the signals well enough that the next real incident resolves in minutes.

Start with the host header case, because it is the most common and the cheapest to provoke. Stand up a small web server that serves a site only for a specific host name and returns a rejection for anything else, point a Front Door profile at it, and set the backend host header on the origin definition to a name the server does not serve. The endpoint returns a 502, the access log records the failure, and a request reproduced against the server with the forwarded host header forced reproduces the rejection directly. Then change the backend host header to the name the server expects, and the 502 clears. Watching the failure appear and disappear as you toggle that one value is what makes the host header rule concrete rather than abstract.

```bash
# Force the exact host header and address the edge uses, against the backend directly.
# A 404, 301, or reset here while the server's own host returns 200 confirms the header cause.
curl -s -o /dev/null -w "status=%{http_code} time=%{time_total}s\n" \
  --resolve app.contoso.com:443:203.0.113.10 \
  https://app.contoso.com/

# Now send the host the server actually serves, to prove the server itself is healthy.
curl -s -o /dev/null -w "status=%{http_code} time=%{time_total}s\n" \
  --resolve internal-app.contoso.com:443:203.0.113.10 \
  https://internal-app.contoso.com/
```

The certificate case reproduces just as cleanly. Put a self-signed certificate on an HTTPS backend, point the edge at it with certificate name validation enabled, and the handshake fails with a certificate subcode in the access log. Replace the self-signed certificate with one from a trusted Certificate Authority whose name matches the backend host name, and the handshake succeeds. The same `openssl` inspection that confirms the production cause confirms the repro, which is why building the repro doubles as practice for the real diagnosis:

```bash
echo | openssl s_client -connect 203.0.113.10:443 -servername app.contoso.com 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
```

The service tag case is the most instructive to reproduce because the failure is silent at the server. Place an inbound deny on the backend's network security group, confirm the edge can no longer reach it, and observe that the server logs record nothing while the edge returns a 502, because the packets never arrive. Add the inbound allow for the `AzureFrontDoor.Backend` service tag, and traffic flows again. The lesson that sticks is that a server with empty access logs during a 502 is almost never the server's fault; the traffic is being dropped before it lands, and the network path is the place to look.

The timeout case needs load rather than a config change. Put an artificial delay on a backend path that exceeds the configured response timeout, drive traffic at it, and watch intermittent 502s appear with a high time-taken value in the access log while fast paths keep succeeding. Reduce the delay below the timeout, or raise the timeout to match, and the failures stop. This repro teaches the single most useful timeout signal: the failure is slow, it is intermittent, and it tracks load, which separates it cleanly from the fast, total failures the other causes produce.

### How do I reproduce a Front Door 502 without breaking production?

Reproduce it against a throwaway backend and profile rather than your production path, toggling one cause at a time. Stand up a small server, point a test Front Door endpoint at it, and provoke each cause in turn: set a wrong backend host header, install a self-signed certificate, add a network deny for the edge, or inject a delay past the timeout. Each produces the matching access-log signal, and reversing the change clears it, so you learn the signals safely.

A controlled repro also gives you a baseline for the response headers. Capture the `X-Azure-Ref`, the `X-Cache`, and, with debug headers enabled, the matched route and selected backend on both a healthy request and a failing one. Comparing the two side by side trains your eye to read a real incident's headers quickly, because you already know what a healthy exchange looks like for your own profile. Engineers who have built the repro once tend to skip straight to the right row of the cause table on the next real failure, which is the entire point of investing the time.

## Backend-specific patterns: App Service, AKS ingress, and virtual machine servers

The cause table is the same for every backend, but the way each cause shows up depends on what kind of server sits behind the edge, and recognizing the backend-specific shape of a 502 shortens the diagnosis further. The three backends engineers most often place behind Front Door are App Service, an AKS ingress, and a virtual machine running a web server, and each has its own characteristic failure.

An App Service backend produces a host header 502 in a recognizable way. App Service routes incoming requests to a site by the host name, and a request carrying a host the app does not have configured returns the platform's default response rather than the application. When you point Front Door at an App Service default host name but leave the backend host header set to forward your custom domain, the app receives a host it does not recognize and answers with something the edge cannot use. The clean fix is to set the backend host header to the App Service default host name so the app recognizes the request, or to add the custom domain to the app's host name bindings so it serves that host directly. App Service also offers an access restriction that allows traffic only from your specific Front Door instance, keyed on the service tag and the profile identifier header, which is the App Service version of the service tag plus `X-Azure-FDID` discipline described earlier. Configuring that restriction without the matching service tag rule, or with the wrong profile identifier, produces a 502 because the app rejects the edge's traffic, so the access restriction and the edge configuration have to agree.

### Why does my App Service backend return a 502 through Front Door?

Because App Service routes on the host name, and a host header it does not recognize gets the platform default response instead of your application, which the edge cannot use. Set the backend host header on the Front Door origin to the App Service default host name, or bind your custom domain on the app so it serves that host. If you enabled the access restriction that allows only your Front Door instance, confirm the service tag rule and the profile identifier match, or the app will reject the edge.

An AKS ingress behind an internal load balancer produces a different signature, often an intermittent connection abort rather than a clean rejection. Here the edge reaches an internal load balancer that fronts an ingress controller, and the 502 frequently traces to an idle timeout or a TCP reset on the internal load balancer, to an ingress host rule that does not match the forwarded host header, or to the ingress controller's own readiness flapping under load. The connection abort subcode in the access log, paired with a very low time taken, points at a reset rather than a slow response, which sends you to the load balancer's idle timeout and the keep-alive behavior between the edge and the ingress rather than to the application. When the cause is the ingress host rule, the fix is the same host header alignment as any other backend; when the cause is the load balancer reset, the fix lives in the load balancer's idle timeout and the connection handling, not in the application at all. Reaching an AKS ingress privately rather than over the internet brings the Private Link approval state into the picture as well, which is why a freshly wired private path that was never approved fails every request until the connection is approved.

A virtual machine running IIS or NGINX produces the most classic host header and certificate cases, because both servers select a site by host header and present a certificate per binding. IIS selects a site by the host header binding, so a forwarded host with no matching binding hits the wrong site or the default, and the certificate bound to the HTTPS listener must match the host the edge uses for SNI. NGINX selects a server block by the `server_name` directive, so a forwarded host that matches no server block falls through to the default server, and the certificate in that server block must match the SNI. On a virtual machine the host firewall adds a layer the platform backends do not have, so the service tag allow may need to be present both on the network security group and in the guest operating system's firewall, and a 502 with empty server logs on a virtual machine points at one of those two layers dropping the edge's traffic before the web server ever sees it.

### Does an unhealthy backend behind a load balancer cause a different 502?

It produces a connection-abort signature rather than a clean rejection, because the failure is often a reset or an idle timeout on the load balancer rather than a response from the application. A very low time-taken value with a connection-abort subcode points at a TCP reset or an idle timeout on the intermediate load balancer, not at the web server. Tune the load balancer's idle timeout and keep-alive handling, and align the backend host header and certificate, before suspecting the application.

The common thread across all three backends is that the cause table holds, but the layer the cause lives in shifts with the backend. A platform backend like App Service hides the network layer, so its 502s cluster around host headers, certificates, and the access restriction. A virtual machine exposes every layer, so its 502s can come from the guest firewall, the certificate binding, or the web server's host routing. An AKS ingress adds the internal load balancer and the ingress controller, so its 502s often trace to resets and host rules rather than to the pods. Knowing the backend tells you which causes are most likely before you read a single signal, which is why naming the backend type is part of the diagnosis.

## Prevention: keeping the backend server contract intact

Preventing a Front Door 502 is mostly a matter of keeping the contract between the edge and the target server explicit, tested, and codified, so the configuration that works in the portal cannot silently drift. The recurring failures in the cause table are all violations of that contract: a probe path that does not return a clean 200, a host header the origin does not recognize, a certificate the edge will not trust, a firewall rule that drops the edge's traffic, a route wired to the wrong group. Each is preventable by making the correct configuration the one that ships.

Design the upstream server's health endpoint deliberately. Give it a dedicated lightweight path that returns a 200 with no authentication, no redirect, and a tiny body, and have it reflect real readiness so that an upstream server which cannot serve traffic is pulled from rotation rather than left in it. Match the probe protocol and port to what the backend actually serves, and never probe a path that redirects. A health endpoint that is part of the application's own contract, versioned and tested alongside the code, does not drift the way an afterthought probe path does.

Make the host header explicit rather than implicit. Set the origin host header on the Front Door origin definition to the exact name the upstream server is configured to serve, and keep that name aligned with the backend's bindings, ingress rules, or server blocks and with the certificate the origin presents. When the host header, the server's routing configuration, and the certificate name all reference the same value, the host header and certificate causes both disappear, because the three ends of the contract agree.

Codify the whole edge configuration as infrastructure as code. The routing rules, the origin groups, the origin definitions with their host headers and timeouts, the probe settings, and the NSG rule allowing the `AzureFrontDoor.Backend` service tag all belong in a Bicep or Terraform definition that is reviewed before it deploys. The wrong-origin-group mistake and the missing service tag rule are both visible in a diff and invisible in a portal click, so the same change that prevents the mistake also documents the correct state. A small Bicep fragment for the backend server and its host header makes the contract reviewable:

```bicep
resource origin 'Microsoft.Cdn/profiles/originGroups/origins@2023-05-01' = {
  parent: originGroup
  name: 'origin-1'
  properties: {
    hostName: 'origin.internal.contoso.com'
    originHostHeader: 'origin.internal.contoso.com'
    httpsPort: 443
    httpPort: 80
    priority: 1
    weight: 1000
    enabledState: 'Enabled'
    enforceCertificateNameCheck: true
  }
}
```

Ship the access log to a Log Analytics workspace from the day the profile goes live, and build an alert on a sustained rate of 502 responses broken down by error info, so a certificate that is about to expire or a backend that is starting to flap surfaces before it becomes an incident. A scheduled query rule that counts 502 responses per error info and per backend over a short window, and fires when the count crosses a threshold, turns the access log into an early warning rather than a forensic record. The same query that diagnoses a live incident becomes the alert definition, so the alert and the diagnosis stay in step:

```kusto
AzureDiagnostics
| where Category == "FrontDoorAccessLog" and httpStatusCode_s == "502"
| where TimeGenerated > ago(15m)
| summarize failures = count() by errorInfo_s, originName_s, bin(TimeGenerated, 5m)
| where failures > 20
```

Break the alert down by error info rather than firing on a bare 502 count, because the breakdown tells you the cause before you open the portal: a certificate value warns of an expiring or rotated certificate, an unhealthy value warns of a flapping backend or a broken probe, a timeout value warns of a saturated server, and a connection abort warns of a network reset or a service tag change. An alert that names the cause family is an alert the on-call engineer can act on immediately, which is the difference between a page that starts a diagnosis and a page that ends one. The access log is the only durable record of a 502 you cannot reproduce, and an alert on the error info turns a class of failure that used to be discovered by users into one discovered by the team. To rehearse the whole diagnosis end to end against a controlled environment, you can [reproduce a server 502 and read origin health in the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), where the probe, host header, certificate, and service tag cases are each set up as a runnable scenario, and you can [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) that present a 502 with its signals and ask you to name the cause, which is the exact skill the cause table is meant to build.

## Related failures the Front Door 502 is confused with

Several other failures look like a 502 at a glance, and telling them apart saves you from applying the wrong fix. The closest neighbor is the Application Gateway 502, the regional layer-7 sibling of this edge-level failure. Application Gateway sits inside a virtual network and proxies to a backend pool, and it produces its own 502 from an unhealthy backend, a probe mismatch, a backend timeout, or an NSG blocking the backend. The shape of the diagnosis is the same, localize to the backend rather than the gateway, but the specific signals and fixes differ, and the [Application Gateway 502 diagnosis](/2022/12/12/fix-application-gateway-502/) walks the regional version of this same family. When you run both, a request can traverse Front Door to an Application Gateway to a backend, and a 502 can originate at either hop, so reading which proxy generated the error is the first split.

A Front Door 503 is the next neighbor, and it usually means the edge had no healthy origin to send to, or the request hit a platform condition such as rate limiting, rather than the edge reaching a backend and getting an unusable response. The fixes overlap with the probe and capacity causes here, but a 503 points you at availability of the origin group as a whole or at platform limits, while a 502 points you at the quality of a specific origin's response. A Front Door 504 is a pure timeout, the target server accepted the connection but did not finish responding, which overlaps heavily with the timeout cause above; the difference between a 502 and a 504 for the same slow origin often comes down to exactly where in the exchange the deadline fell.

There is also the question of whether the edge is even the right tool for the workload, which is a design decision rather than a failure. Front Door is a global edge with caching, WAF, and global load balancing; Application Gateway is a regional layer-7 load balancer; a CDN is a content cache. Choosing the wrong one produces architectures that fight their tools, and the [edge service comparison across Front Door, CDN, and Application Gateway](/2023/10/09/front-door-vs-cdn-vs-gateway/) names the deciding factors. If the 502 you are chasing is really a sign that the request should not be going through Front Door at all, or that the routing should be structured differently, the [Front Door routing and origin setup](/2023/05/15/configure-front-door-routing/) covers building the routes and origin groups correctly from the start, which prevents the wrong-origin-group cause before it can happen.

### What is the difference between a Front Door 502 and a 504?

A 502 means the edge reached the backend and got back something unusable, or could not complete the exchange, while a 504 means the origin accepted the connection but did not finish responding inside the timeout, a pure deadline failure. The same slow origin can produce either depending on where the deadline falls in the request lifecycle. A 502 sends you to the upstream server's response validity, certificate, and reachability; a 504 sends you specifically to origin latency and the response timeout.

## The misdiagnoses that waste the most time

Three wrong turns account for most of the hours engineers lose to a Front Door 502, and naming them is as useful as naming the causes, because avoiding a wrong turn is faster than recovering from it. Each wrong turn feels reasonable in the moment, which is exactly why it persists.

The first and most expensive is blaming the edge. The 502 page carries Microsoft branding, the failure surfaces at a Microsoft-operated layer, and the natural conclusion is that the platform is broken. Engineers open a support case about the edge, toggle routes, recreate endpoints, or wait for a platform incident to clear, while the real fault sits untouched at the backend. The corrective habit is to treat the 502 as a report rather than an accusation: the edge is telling you it could not get a usable response from the server you pointed it at, and that report is almost always accurate. The first move is never to change the edge; it is to reproduce the edge's request against the backend and read what the backend does with it. The platform is rarely the problem, and the few times it is, the access log and the service health view will say so plainly rather than leaving you to guess.

The second wrong turn is misreading the host header. Engineers know the host header matters but set it to the wrong value, most often by forwarding the public custom domain to a backend that only recognizes its internal name, or by leaving the header at a default that does not match either. The failure then looks like a server problem, because the server returns a 404 or a redirect, and the investigation drifts into the application code or the web server configuration when the fix is a single field on the Front Door origin definition. The corrective habit is to make the host header the second thing you check after confirming the request reached the backend, and to check it by reproducing the exact forwarded header rather than by reading the configuration and assuming it is right. A header that looks correct in the portal can still be wrong for the backend, and only the reproduced request settles it.

The third wrong turn is missing the service tag allow. When a backend sits behind a network security group or a firewall, engineers often allow a fixed set of addresses they captured once, or they allow a broad public range, or they forget the inbound rule entirely, and the edge's traffic is dropped before it arrives. The investigation then chases a server that appears unreachable, with empty access logs that seem to confirm the server is down, when the server is fine and the network is the wall. The corrective habit is to check the inbound rules for an allow on the `AzureFrontDoor.Backend` service tag whenever the backend's own logs show no traffic during a 502, because empty logs during a failure are the signature of traffic dropped upstream, not of a dead server. Allowing the service tag by name rather than by captured address also prevents the slower version of this failure, where a working allow rule silently goes stale as the edge's address set changes underneath it.

### Why does a Front Door 502 keep coming back after I fix it?

Because the fix addressed a symptom rather than the cause, or because the cause was load-dependent and only reappears under traffic. A host header or certificate fix that clears a single test request but not the sustained error rate usually means a second cause is also present, or the change did not actually take effect on the path the real traffic uses. A 502 that returns only under load points at a timeout or a flapping backend rather than a static misconfiguration. Confirm a fix by watching the error rate across real traffic over time, broken down by error info, not by a single successful request.

## Reading the triage in one pass

The whole diagnosis compresses into a short decision rule that you can run from the access log and a single reproduced request. Begin by confirming the request reached the backend, because that split is the most informative one you can make. If the backend logged the request, the edge reached it, and the fault is a host header rejection, a slow response, or something the backend itself produced; if the backend logged nothing, the traffic never arrived, and the fault is a service tag block, a certificate failure that aborted the handshake before any HTTP, a probe that pulled the backend from rotation, or a route that sent the request to a different server entirely.

From there the error info in the access log names the family. A certificate value sends you to the TLS leg, where you inspect the chain, the name against the Server Name Indication, and the validity dates. A timeout value with a high time-taken figure sends you to backend latency, where you correlate the failures against the server's own response time and capacity metrics. An unhealthy value sends you to the probe, where you test the probe path for a clean 200 over the right protocol and port. A connection abort with a very low time taken sends you to the network: a reset, an intermediate idle timeout, or a service tag that is not allowed. The subcode does the heavy lifting; the commands in the cause table sections confirm the specific instance and apply the fix.

The reproduced request is the check that resolves the ambiguous cases fastest, because it forges exactly what the edge sends. Forcing the forwarded host header and the Server Name Indication against the backend's real address, rather than refreshing a browser, distinguishes a host header mismatch and a certificate rejection from everything else in a single command, and it does so without waiting for the next real failure. Engineers skip this step because forging the request is slightly more work than reloading a page, and skipping it is the single most common reason a 502 diagnosis runs long. The triage is four checks in order: reproduce the edge's request, read the access log error info and time taken, check the origin group health, and check the route's selected backend. Those four localize every row in the cause table, and each row has a fix that targets the backend or the routing rather than the edge.

## The strategic verdict on Front Door 502 errors

The discipline that resolves a Front Door 502 quickly is the discipline of localizing the failure to the server contract before touching the edge. The 502 is generated at the edge, but the fault almost always lives in the relationship between the edge and the origin: a probe the backend server fails, a host header the target server rejects, a certificate the edge will not trust, a firewall that drops the edge's traffic, a route wired to the wrong group, or an origin too slow to answer in time. The origin-host-header rule captures the most common case in a sentence: because the edge forwards the host header you configure, a 502 with a healthy server is usually the origin rejecting an unexpected host or certificate, not a Front Door fault.

The fastest path through the cause table is mechanical and worth internalizing. Reproduce the edge's exact request against the backend, host header and SNI included, and a host header or certificate mismatch reveals itself in one command. Read the access log's error info and time taken, and the cause family names itself. Check the origin group health, and the probe case is confirmed or ruled out. Check the route's selected origin, and the wrong-group case is caught. Four checks localize every row, and each row has a fix that targets it rather than the edge. An engineer who works the table rather than guessing fixes the right thing the first time and prevents the recurrence by codifying the contract that the failure violated.

The broader lesson, the one this article shares with the rest of the series, is that a clear error at one layer is frequently a symptom of a broken contract at the layer below, and the skill that matters is finding the real boundary rather than fixing the place the error happened to surface. A Front Door 502 is the edge being honest that it could not get a valid response from your server. Believe it, localize to the upstream server, confirm the specific cause, and the fix follows directly. That habit, applied consistently across every incident, turns a frightening error into a routine triage that closes in minutes rather than hours, and it compounds over time: each contract you codify is one fewer recurrence the team has to absorb later, and one more piece of the platform that simply behaves.

## Frequently Asked Questions

### Q: What does a Front Door 502 origin error actually mean?

A Front Door 502 origin error means the edge could not get a valid response from the origin it selected for your request. Front Door is a reverse proxy: a client connects to the nearest edge location, the edge matches a route, picks an upstream server from the origin group, opens its own connection to that server, and relays the request. The 502 is generated when that second leg, edge to origin, fails to produce something usable, whether because the server rejected the forwarded request, refused the connection, failed the certificate handshake, timed out, or was unreachable. It is a statement about the relationship between the edge and your server, not a client problem and rarely an edge problem, which is why the fix lives at the backend server or in the routing almost every time rather than at the edge that surfaced the code.

### Q: Does an unhealthy origin cause a Front Door 502?

An unhealthy origin causes a Front Door 502 when the origin group has no healthy member left to serve the request. Front Door probes each backend on a configured path and protocol, and if the probe does not get a clean success, the edge marks that backend unhealthy and stops routing to it. With a single origin, one failed probe leaves nothing to forward to, and requests fail. With multiple origins, the edge routes around an unhealthy member to a healthy one, so a 502 appears only when every backend in the group fails at once. The common trap is a probe path that returns a redirect, a 401, or a 404, which fails the probe even though real traffic on a different path succeeds, so the origin looks dead while the application works.

### Q: Can an origin response timeout trigger a Front Door 502?

An origin response timeout triggers a Front Door 502 when the edge establishes a connection and sends the request but the target server does not finish responding inside the configured window. This is a load-dependent failure: at low traffic the backend answers in milliseconds and looks fine, while under load a slow query, an exhausted connection pool, a saturated CPU, or a slow dependency pushes response time past the timeout and a fraction of requests start failing. The signature is intermittent 502s with a high time-taken value in the access log, in contrast to the fast failure a connection or certificate rejection produces. The durable fix is to make the origin faster or add capacity; raising the origin response timeout is a tuning knob that helps legitimately slow requests but does nothing for underlying saturation.

### Q: Why does a wrong origin host header produce a Front Door 502?

A wrong origin host header produces a Front Door 502 because the upstream server routes requests based on the host header, and a value it does not recognize gets a 404, a redirect, or a connection reset rather than a 200, which the edge translates into a 502. Front Door forwards exactly the host header the origin definition specifies; if that header does not match a name the server is configured to serve through its bindings, ingress rules, or server blocks, the origin rejects it. The server is healthy for the traffic it recognizes; it simply does not recognize the request the edge is sending. Confirm by reproducing the edge's request against the backend server with the forwarded host header forced, and fix by setting the origin host header to the name the target server expects.

### Q: Does an SNI or certificate mismatch cause a Front Door 502?

An SNI or certificate mismatch causes a Front Door 502 because the edge validates the origin's certificate during the TLS handshake, and a failure there aborts the connection before any HTTP is exchanged. Front Door uses the origin host name as the Server Name Indication, the backend must present a certificate matching that name, and the certificate must chain to a Certificate Authority on the Microsoft-trusted list. A self-signed certificate, a certificate whose name does not match the SNI, or an expired certificate all fail validation and produce a 502 with a certificate error subcode. This is a fast, total failure rather than an intermittent one. The fix is a trusted-CA certificate matching the origin host name, or aligning the certificate name validation setting deliberately when an internal origin cannot match.

### Q: Can a firewall blocking the Front Door service tag cause a 502?

A firewall blocking the Front Door service tag causes a 502 because the edge's probes and requests are dropped before they reach the upstream server, making the origin appear unreachable. Front Door reaches origins from the addresses represented by the AzureFrontDoor.Backend service tag, and those addresses change over time, so allowing them by static IP goes stale. If the server's network security group, Azure Firewall, or host firewall does not allow inbound from that service tag on the listening port, the traffic never arrives, the server logs show no Front Door requests, and clients get a 502. The fix is an inbound allow rule for the AzureFrontDoor.Backend service tag at a priority above any broad deny. Add a check on the X-Azure-FDID header afterward so only your own Front Door profile can route through.

### Q: How do I read Front Door origin health to diagnose a 502?

Read origin health in two places at once. The origin group health blade in the portal, or the origin group settings from the CLI, shows whether the edge currently considers each server healthy and what probe path and protocol it uses. The resource logs, once you have enabled diagnostic settings to a Log Analytics workspace, record the exact error info for each failed request, with values that name an unhealthy origin, a certificate problem, a timeout, or a connection abort. Query the access log filtered to the 502 status and read the error info, origin name, routing rule, and time-taken columns. The probe status tells you about the upstream server's general health; the log tells you the precise cause of the specific 502 you are chasing, and together they separate a probe outage from a per-request rejection.

### Q: Why would a routing rule pointing at the wrong origin group cause a 502?

A routing rule pointing at the wrong origin group causes a 502 because the edge forwards the request to a server you did not intend, and if that origin cannot serve the request, the result is a 502 from a server that was never meant to be in the path. Front Door selects a route by matching the request's domain and path pattern, then forwards to that route's origin group. A misconfigured path pattern, an overlapping route whose precedence resolves the wrong way, or a route left wired to a stale or staging origin group all send traffic to the wrong place. The edge follows the configuration exactly; the configuration is wrong. Confirm by reading the matched route and selected origin from the debug headers or the access log, and fix by correcting the route's origin group and tightening the path patterns.

### Q: Why does Front Door mark my origin unhealthy when the probe returns a 301?

Front Door marks an origin unhealthy when the probe returns a 301 because it treats a redirect on the probe path as a probe failure rather than a success, since the probe expects a clean 200. This commonly happens when the probe is configured against the site root and the backend server redirects HTTP to HTTPS, so the probe receives a 301 instead of a 200 and the edge concludes the origin is not serving. Real users follow the redirect and reach the site, so the application works while the probe fails, which makes the target server look healthy to people and dead to Front Door. The fix is to point the probe at a dedicated lightweight path that returns a 200 directly, over the same protocol and port the backend actually serves, without redirecting.

### Q: What is the difference between a Front Door 502 and a 504?

A Front Door 502 means the edge reached the origin and got back something unusable, or could not complete the exchange at all, while a 504 means the upstream server accepted the connection but did not finish responding inside the timeout, a pure deadline failure. The two overlap because the same slow origin can produce either depending on exactly where in the request lifecycle the deadline falls. A 502 directs you to the validity of the server's response, its certificate, and its reachability, covering the host header, certificate, service tag, and probe causes. A 504 directs you specifically to origin latency and the configured response timeout. Reading the error info in the access log alongside the status code tells you which family you are in and which fix applies.

### Q: How do I find the specific Front Door error code behind a 502?

Find the specific error code behind a 502 by reading the access log's error info field and the response headers. Front Door records an error info value on each failed request that names the actual cause, such as a backend connection abort, an origin certificate problem, an unhealthy origin, or a request timeout, and each value maps to a different cause and fix. Enable diagnostic settings on the profile to send the access log to a Log Analytics workspace, then query for the 502 requests and read the error info, origin name, and time-taken columns. On the response itself, capture the X-Azure-Ref header, which ties the failure to the internal telemetry for that request, and the X-Cache header, which confirms whether the request was forwarded to the origin at all.

### Q: Why does a Front Door 502 happen with a Private Link origin in pending state?

A Front Door 502 happens with a Private Link origin in pending state because the private path between the edge and the backend server is only half-built until the connection is approved. Front Door Premium can reach an upstream server privately through a Private Link service, which projects the target server into Front Door's managed network without exposing it publicly. For traffic to flow, the private endpoint connection Front Door creates against the origin's Private Link service must be approved on the backend side. Until then the connection sits in pending, the edge cannot route through it, the upstream server is unreachable from Front Door, and clients get a 502. Confirm by listing the private endpoint connection status, and fix by approving the pending connection so it reaches the connected state.

### Q: Does a Front Door 502 only on cache misses point to the origin?

A Front Door 502 that appears only on cache misses points to the server, because a cache miss means the request was forwarded to the backend server rather than served from the edge's store. The X-Cache response header tells you the disposition: a value indicating a miss or a no-cache configuration means the origin was contacted, while a value indicating a hit means Front Door answered from its own cache without touching the target server. A 502 alongside a miss therefore implicates the backend leg, which is where almost every 502 originates. A 502 on a cached path would instead suggest the cached object or the edge, which is rare. Checking the cache header before anything else rules out a stale cached error and confirms you are looking at a forwarded request.

### Q: Can high load on the origin cause intermittent Front Door 502 responses?

High load on the upstream server causes intermittent Front Door 502 responses when the load pushes the server's response time past the edge's timeout for a fraction of requests, or when it makes origins flap in and out of health as the probe catches them during brief slow periods. The intermittence is the signature: a configuration mistake fails every request the same way, while load-induced failures come and go with traffic. Correlate the 502 timestamps against the backend's own latency, queue length, CPU, and dependency metrics, and they should line up with the spikes. The fix is to relieve the origin: profile and fix the slow path, add caching for expensive responses, or scale the backend server out so each instance carries less load, rather than only raising the timeout, which masks the saturation without resolving it.

### Q: How do I confirm a Front Door 502 is fixed after changing the target server?

Confirm a Front Door 502 is fixed by reproducing the edge's exact request through Front Door and checking for a 200, then verifying the server's health and the access log together over a sustained window. After changing the origin host header, certificate, probe, or firewall rule, send a request to the Front Door endpoint and confirm the status, the X-Cache header showing the request was forwarded, and the absence of an error subcode. Check the origin group health to confirm the origin reads as healthy. Then watch the access log for a period that covers real traffic, because an intermittent timeout or a flapping origin will not show in a single request. A fix is confirmed only when the error rate stays at zero across normal load, not when one request succeeds.

### Q: Is a Front Door 502 a problem with the edge or the backend?

A Front Door 502 is almost always a problem with the upstream server or the routing, not the edge, because the 502 is generated precisely when the edge cannot get a valid response from the origin it contacted. The edge accepted the client, matched the route, selected the server, and forwarded the request; what failed was the backend server's ability to answer in a way the edge could relay. The fault lives in the contract between them: a probe the origin fails, a host header it rejects, a certificate the edge will not trust, a firewall dropping the edge's traffic, a route wired to the wrong group, or an origin too slow to respond. Localizing to the target server and confirming the specific cause is the diagnosis; touching the edge first is the mistake that wastes the most time.

### Q: How do I prevent recurring Front Door 502 origin errors?

Prevent recurring Front Door 502 origin errors by keeping the backend contract explicit, tested, and codified. Design a dedicated health endpoint that returns a clean 200 with no authentication or redirect over the protocol and port the origin serves, and version it alongside the application so it does not drift. Set the origin host header explicitly to the name the upstream server is configured to serve, and keep that name aligned with the upstream server's routing configuration and its certificate. Codify the routing rules, origin definitions, probe settings, and the AzureFrontDoor.Backend service tag allow rule as infrastructure as code so mistakes are visible in a diff. Ship the access log to a workspace from day one and alert on a sustained 502 rate broken down by error info, so a flapping origin or an expiring certificate surfaces before it becomes an incident rather than being discovered by users.

### Q: What is the difference between a Front Door 502 and a 503?

A Front Door 502 means the edge reached the backend it selected and got back something unusable, or could not complete the exchange, while a 503 usually means the edge had no healthy backend in the group to send the request to at all, or the request hit a platform condition such as rate limiting. The distinction points you in different directions: a 502 sends you to the quality of a specific backend's response, its certificate, its host header, and its reachability, while a 503 sends you to the availability of the origin group as a whole or to platform limits. When every backend in a group fails its probe, you can see either code depending on the exact disposition, so read the error info in the access log to separate a group with no healthy member from a single backend returning an unusable response.
