---
layout: post
title: "Fix Azure Application Gateway 502 Bad Gateway Error"
page_title: "Application Gateway 502 Bad Gateway: How to Find the Cause in Server Health and Fix the Probe, NSG, Timeout, or Certificate Behind It"
date: 2022-12-12
categories: ["Technology"]
tags: ["Azure", "Application Gateway", "502 Bad Gateway", "Troubleshooting", "Networking", "Cloud Computing"]
excerpt: "An Application Gateway 502 means no pool member is healthy, so read the Backend health view first to name the real cause before touching a rule or timeout."
image: "/assets/images/blog/blog-05.webp"
reading_time: 61
author: "nathan-cole"
last_updated: 2022-12-12
lang: en
---
An Application Gateway 502 is one of the most misread errors in Azure networking, because the page the browser shows says almost nothing about where the failure actually lives. The visitor sees "502 Bad Gateway" with a small "Microsoft-Azure-Application-Gateway/v2" line beneath it, and the instinct is to assume the gateway itself broke. It almost never did. A 502 from Application Gateway means the gateway accepted the client request, tried to forward it to a member of the backend pool, and could not get a valid response back. The gateway is reporting a problem with the upstream, not with itself, and the single most reliable way to find which target host problem you have is to open the Backend health view before you change anything else.

That distinction is the whole article. Engineers lose afternoons restarting the gateway, recycling the backend virtual machines, scaling the instance count, and reissuing certificates, all while the Backend health blade sits one click away with the exact reason written in plain text. The fastest path from a 502 to a fix is to read what the gateway already knows about each server, match that reason to one of a small number of root causes, and apply the change that cause calls for. Everything below builds that habit into a repeatable method.

![Fixing Azure Application Gateway 502 Bad Gateway root causes - Insight Crunch](/assets/images/blog/blog-05.webp)

## What a 502 From Application Gateway Actually Means

Application Gateway is a layer-7 reverse proxy. A client opens a connection to the gateway frontend, the gateway terminates that connection, evaluates listeners and routing rules, and then opens its own connection to a chosen member of the backend pool to fetch the response. When the gateway cannot complete that second leg with a usable answer, it returns a 502 to the client. The status code is the proxy telling you that the upstream half of the conversation failed. The client connection was fine. The backend connection was not.

This matters because it rules out an entire class of guesses immediately. A 502 is not a frontend listener problem, because a broken listener would refuse the connection or return a different error before any pool member was contacted. It is not a routing rule that points nowhere, because that surfaces differently. It is not usually a client networking problem, because the client reached the gateway well enough to receive the 502 body. The error is scoped to what happens after the gateway decides which upstream should serve the request and tries to talk to it.

The gateway makes that decision based on health. Application Gateway continuously probes every member of every backend pool and keeps an internal map of which members are healthy and which are not. It will only forward a request to a member it currently considers healthy. When every member of the chosen pool is unhealthy, there is no eligible target, and the gateway has nowhere to send the request. The result is a 502 on every request to that pool until at least one member recovers. This is why health is the center of the diagnosis rather than a side detail. The gateway routes by health, so the 502 is almost always a statement that health checks are failing for a reason you can read.

### Why does Application Gateway return 502 instead of a connection error?

Because the gateway already accepted the client connection at layer 7 before it tried the server. It cannot refuse a request it has already received, so when the upstream fetch fails it returns a 502 to report that the proxy could not get a valid response from the pool member it selected.

A second reason the 502 specifically appears, rather than a timeout page or a blank response, is that Application Gateway has a defined behavior for upstream failure. In the v2 SKU, if a selected backend member does not respond within the configured interval, the gateway will try the request against another healthy member of the same pool before giving up. The 502 you see is the gateway reporting that it exhausted its eligible members without a valid response. That behavior is helpful to understand, because it tells you the gateway is not stubbornly hammering one dead node. It tried what it could and ran out of healthy targets, which again points you straight at why the members are unhealthy.

The corollary is the foundation of this entire diagnosis. When you see a 502, the question is never "why did the gateway break." The question is "why does the gateway believe it has no healthy target host to serve this request," and occasionally "why did a server the gateway believes is healthy still fail to return a valid response." Both questions are answered in the same place.

## The Pool member Health First Rule

The namable claim of this article is the backend-health-first rule for a 502: Application Gateway returns 502 when it has no healthy upstream to serve the request, so the Backend health view names the cause before any rule change, timeout adjustment, or restart. You read health first, and only then do you act. Every minute spent changing settings before reading health is a minute spent guessing.

The Backend health view lives on the Application Gateway resource in the portal, under the Backend health blade, and it lists every backend pool, every member of each pool, and a status for each member. The status is Healthy, Unhealthy, or Unknown, and when a member is not healthy the Details column carries a message that usually names the cause directly. That message is the single most valuable artifact in the whole troubleshooting process, and the entire discipline of fixing a 502 quickly comes down to reading it carefully and acting on what it says rather than on what you assume.

You can read the same information from the command line, which is faster when you are already in a terminal and far better for capturing a record of the state. The command queries the live backend health and returns the per-member status and the detail message.

```bash
# Read backend health for an Application Gateway, with the detailed per-member reason
az network application-gateway show-backend-health \
  --resource-group rg-edge-prod \
  --name agw-edge-prod \
  --query "backendAddressPools[].backendHttpSettingsCollection[].servers[].{address:address, health:health, why:healthProbeLog}" \
  --output table
```

The output gives you, for each backend member, an address, a health verdict, and a reason. When every member reads Unhealthy, you have a 502 cause to chase and the reason text tells you which family it belongs to. When members read Healthy but clients still receive a 502, you are in the narrower territory of a request the gateway forwards but the server rejects, which the certificate and host-header section covers. Reading this first splits the problem in half before you touch a single setting.

### What does the Backend health Details message tell me?

The Details message names the failing condition the probe encountered, such as a connection refusal, a timeout, an HTTP status the probe treats as a failure, or a certificate mismatch. Reading it first tells you which root cause family you are in, so you change the one setting that matters instead of guessing across several.

The Details text is worth learning to read closely, because the wording maps cleanly onto causes. A message about the pool member not responding or the connection being refused points at a reachability or listening problem, which means a probe that cannot reach the member, an NSG or route blocking the path, or an upstream not listening on the expected port. A message about an HTTP status code that the probe does not accept points at a probe configuration that disagrees with what the application returns. A message about a certificate, a common name, or a trust failure points at the HTTPS target host territory. A message about a timeout points at a server that is reachable but slow. Learning these mappings turns the Details column from a cryptic line into a near-direct answer.

The remainder of this article walks the distinct causes one at a time. For each, it gives the Backend health signal you should expect to see, the confirming command or check, and the fix that the cause actually calls for. The order is roughly the order of frequency in real incidents, but you should always let the Backend health Details message, not the list order, decide which section you jump to.

## How to Gather the Full Diagnostic Signal

The Backend health view is the fastest read, but it is not the only signal the gateway produces, and a thorough diagnosis pulls from three sources that corroborate one another: the backend health, the access logs, and the metrics. Reading all three takes a few minutes longer than reading health alone, and it pays for itself when the health view is ambiguous or when you need to prove what happened after the fact. The habit worth building is to capture all three at the start of an incident so you are reasoning from evidence rather than from a single snapshot.

The access log is where the gateway records every request it served, including the ones that returned a 502, and it carries fields the health view does not. Each 502 entry includes the HTTP status the gateway returned to the client, the backend pool and backend setting involved, the response time, and an error information field that names the upstream condition the gateway hit. That error information field is the corroborating detail that turns a vague 502 into a specific cause. A value indicating the upstream closed the connection points at a pool member that is terminating connections prematurely, often a keep-alive mismatch or a backend crashing under load. A value indicating no error on the gateway side, combined with a 502, points back at the backend health and the probe. Reading the access log alongside the health view confirms which half of the conversation actually failed.

If you have routed the gateway's diagnostic logs to a Log Analytics workspace, you can query the access log directly and isolate the 502 responses with the upstream context attached, which is far more precise than scrolling raw log files. The query groups the failures so you can see whether they cluster on one backend pool, one URL path, or one time window, each of which narrows the cause.

```kql
// Application Gateway access log: isolate 502 responses with backend context
AzureDiagnostics
| where Category == "ApplicationGatewayAccessLog"
| where httpStatus_d == 502
| project TimeGenerated, requestUri_s, backendPoolName_s, backendSettingName_s,
          serverResponseLatency_s, error_info_s
| summarize count() by backendPoolName_s, error_info_s, bin(TimeGenerated, 5m)
| order by TimeGenerated desc
```

The grouping in that query is what makes it useful. If every 502 lands on a single backend pool, you have localized the failure to that pool's members and their probe, which sends you to the membership or probe causes. If the 502s cluster on one URL path while other paths succeed, you are likely looking at a slow or failing endpoint rather than a pool-wide outage, which points at the timeout family. If the error information field consistently reports the upstream closing the connection, you are in the keep-alive and connection-reuse territory. The log turns a binary "we are getting 502s" into a shaped picture of which requests fail and why.

### What do the Application Gateway metrics tell me about a 502?

The metrics show the healthy host count per backend pool, the failed request count, and the response status distribution over time. A healthy host count that drops to zero on a pool is the metric-level statement of "no healthy server," and watching when it dropped against when the 502s began pins the cause to a specific change or event.

The metrics that matter most for a 502 are the healthy host count per backend pool, the unhealthy host count, the total request count split by response status, and the backend response time. The healthy host count is the headline number: when it sits at zero for a pool, the gateway has no eligible target and every request to that pool returns a 502, which is the metric expression of the entire backend-health-first rule. Charting the healthy host count over time and overlaying the moment the 502s started tells you whether the backends fell out of rotation gradually under load, all at once after a deployment, or on a schedule that points at a recurring job exhausting the pool member. The backend response time metric corroborates the timeout family: a response time creeping up toward and past the request-timeout right as 502s appear is the signature of a slow upstream rather than an unreachable one.

Azure Resource Health is the third corroborating signal and the one that rules out the rare case where the platform itself is degraded. It reports whether the Application Gateway resource is healthy from the platform's perspective, and while a platform-side degradation is uncommon, checking Resource Health early costs nothing and removes the one cause you cannot fix yourself from the list. If Resource Health reports the gateway as degraded for a platform reason, the fix is to wait or to open a support case rather than to keep changing your own configuration. In the far more common case where Resource Health reports the gateway as available, you have confirmed that the 502 is yours to fix and that the cause lives in the target host, the probe, the network, the timeout, or the certificate, exactly as the cause table lays out.

## The InsightCrunch Application Gateway 502 Cause Table

Before the detailed walkthroughs, here is the findable artifact this article is built around. The InsightCrunch App Gateway 502 cause table maps each distinct root cause to the Backend health signal it produces and the fix it calls for. Keep this open in a second tab during an incident, read the Backend health Details column, and jump to the row that matches.

| Root cause | Backend health signal | The fix it calls for |
| --- | --- | --- |
| No healthy server or empty pool | All members Unhealthy, or pool shows no members | Confirm the pool has correct members and that at least one passes the probe; add or correct members |
| Health probe mismatch | Unhealthy with a status-code, path, or host-header reason in Details | Align the probe path, port, protocol, host, and accepted status range with what the app actually serves |
| NSG, UDR, or DNS blocking the path | Unhealthy with a connection refused or unreachable reason | Allow the probe and traffic ports on the gateway and pool member path; fix the route or the DNS resolution |
| Upstream timeout over the request limit | Intermittent 502 under load, members flip Healthy to Unhealthy | Reduce server latency or raise the request-timeout and connection-draining settings to match |
| HTTPS host-header or certificate mismatch | Healthy probe but client 502, or certificate or CN reason in Details | Match the probe host header to the certificate common name and trust the backend certificate chain |
| Upstream listening on the wrong port | Unhealthy with a connection refused reason on the configured port | Point the backend HTTP setting at the port the application actually listens on |

Each row below becomes a full section. The table is the map; the sections are the territory. The reason it is worth memorizing the shape of this table is that the Backend health Details message will usually drop you onto one row within seconds, and from there the fix is mechanical rather than exploratory.

## Cause One: No Healthy Target host or an Empty Pool

The most direct cause of a 502 is the one the gateway states most plainly. There is no member of the backend pool that the gateway currently considers healthy, so there is nowhere to send the request. This happens in two distinct shapes, and they need different fixes, so it is worth separating them.

The first shape is a pool that contains members, all of which are failing their health probe. The Backend health view shows the members listed with an Unhealthy status against each, and a Details message that hints at why. This is not really a separate cause from the probe and reachability families below; it is the symptom they all produce. When every member is Unhealthy, you read the Details message and follow it to the probe section, the network section, or the certificate section. The pool is not empty, it is just that nothing in it is currently serving.

The second shape is genuinely different. The pool is empty, or it contains addresses that no longer correspond to running backends. This happens far more often than teams expect, especially where infrastructure is recreated frequently through pipelines. A deployment tears down a virtual machine scale set and rebuilds it with new private addresses, but the backend pool still references the old addresses. Or a backend pool was created and associated with a rule, but the addresses were never populated. Or a pool points at a fully qualified domain name that no longer resolves from inside the gateway subnet. In each case the gateway has no reachable member, and every request returns a 502.

### How do I confirm the backend pool actually has healthy members?

Open the Backend health view and read the member count and status for the pool the failing listener routes to. If the pool is empty, or every listed address is Unhealthy, or the addresses do not match the current private IPs or FQDNs of your running backends, you have found the cause without changing anything.

To confirm this from the command line, list the backend pool members and compare them to the actual addresses of your running backends. If you use IP addresses in the pool, the addresses must match the current private IPs of the backend virtual machines or scale set instances. If you use fully qualified domain names, those names must resolve correctly from the gateway subnet, which is a separate check covered in the network section.

```bash
# List the addresses currently configured in each backend pool
az network application-gateway address-pool list \
  --resource-group rg-edge-prod \
  --gateway-name agw-edge-prod \
  --query "[].{pool:name, addresses:backendAddresses[].{ip:ipAddress, fqdn:fqdn}}" \
  --output json
```

Compare that output against the real backends. For a scale set, list the current instance private IPs and confirm at least one of them appears in the pool and is reachable. The fix is then to populate the pool with the correct addresses or to switch the pool to a reference that survives recreation, such as targeting the scale set or App Service directly rather than hardcoding addresses that change on every rebuild.

When the server is an App Service, the empty-or-wrong-member case has a specific trap. The pool must target the App Service default hostname, the name that ends in azurewebsites.net, and the backend HTTP setting must pick the host name from the backend target so the App Service receives a host header it recognizes. Pointing the pool at a custom domain that only resolves publicly, or that the App Service does not have bound, produces a pool member the gateway cannot reach internally, and the result is a 502. The fix is to use the platform hostname for the pool and let the host header derive from it, or to bind and configure the custom domain on the App Service so it actually answers to it.

The prevention here is structural. Stop hardcoding ephemeral addresses into upstream pools. Where the platform allows it, reference the server by an identity that survives recreation, and where you must use addresses, make pool population part of the same deployment that creates the backends so the two can never drift apart. A pool that is updated by hand after every rebuild will eventually be forgotten after one rebuild, and that rebuild is the one that pages you.

## Cause Two: A Health Probe That Disagrees With the Application

When the pool has members but they all read Unhealthy, the probe is the next thing to examine, because the probe is the gateway's definition of healthy. Application Gateway decides a member is healthy by sending it a probe request and judging the response. If the probe asks for something the application does not serve, or judges a perfectly normal response as a failure, the gateway marks the member down even though the application is running fine. This is the single most common cause of a 502 in production, and almost all of it comes down to a mismatch between what the probe expects and what the application returns.

A probe has several dimensions, and any one of them can disagree with reality. There is the path the probe requests, the port it connects to, the protocol it uses, the host header it sends, the interval and timeout that govern timing, the unhealthy threshold that decides how many failures mark a member down, and the range of HTTP status codes the probe accepts as healthy. A default probe derives most of these from the backend HTTP setting and requests the root path, and a custom probe lets you set each one explicitly. Either way, a 502 caused by the probe is a 502 caused by one of these dimensions being wrong.

The status code range is the classic trap. By default the probe treats responses in the 200 to 399 range as healthy. If your health endpoint returns a 401 because it sits behind authentication, or a 403 because of an authorization rule, or a 302 redirect to a login page, the probe sees a status outside the accepted range and marks the member unhealthy, and you get a 502 even though the application is serving every real request correctly. The fix is either to give the probe a path that returns a clean success without authentication, such as a dedicated unauthenticated health endpoint, or to widen the accepted status range to include the code your endpoint legitimately returns.

The path is the second classic trap. A probe configured to request /health when the application has no such route gets a 404, which falls outside the default healthy range, so every member reads Unhealthy. The application is fine; the probe is asking for a door that does not exist. The fix is to point the probe at a path the application actually serves and that returns a success status, which is often a purpose-built lightweight endpoint that does nothing but confirm the process is up.

### Why does my pool member show Unhealthy when the app works fine in a browser?

Because the probe judges health differently from how you browse. Your browser follows redirects, sends cookies, and accepts pages the probe rejects, while the probe requests one fixed path and accepts only a status range. A probe path that 404s, or an endpoint that returns 401 or 302, reads as Unhealthy even when the site loads for you.

To confirm a probe mismatch, read the probe configuration and the backend HTTP setting together, then reproduce the exact request the probe makes. The Backend health Details message often states the status code it received, which tells you immediately whether the application answered with something the probe rejected.

```bash
# Show the probe configuration so you can compare it to what the app serves
az network application-gateway probe list \
  --resource-group rg-edge-prod \
  --gateway-name agw-edge-prod \
  --query "[].{name:name, protocol:protocol, host:host, path:path, interval:interval, timeout:timeout, threshold:unhealthyThreshold, statusCodes:match.statusCodes}" \
  --output json
```

Then reproduce the probe request against the upstream from a machine inside the same virtual network, so the network path matches what the gateway uses. If you curl the probe path and port from a jump box in the gateway subnet and receive a status the probe would reject, you have confirmed the cause and you know exactly what to change.

```bash
# Reproduce the probe request from inside the VNet, matching path, port, and host header
curl -sS -o /dev/null -w "%{http_code}\n" \
  -H "Host: app.internal.example.com" \
  http://10.0.2.4:8080/health
```

If that returns a 404, fix the path. If it returns 401 or 403, either move the health endpoint outside authentication or widen the probe status range. If it returns 200 but the gateway still marks the member down, the probe is sending a different host header than your curl, which is the host-header case in the certificate section. The principle throughout is that the probe is a contract between the gateway and the application, and a 502 from this family means the two sides of that contract disagree on the path, the port, the status, or the host. Reconcile them and the members go healthy and the 502 clears.

The timing dimensions deserve a note because they cause a subtler version of this failure. If the probe timeout is shorter than the time the application needs to answer a probe, the probe records a timeout and marks the member unhealthy under load even though it is technically serving. If the unhealthy threshold is very low, a single slow response flips the member out of rotation. Tuning the interval, timeout, and threshold so they tolerate the application's real behavior keeps a momentarily slow target host from being declared dead and producing a 502.

## Cause Three: An NSG, Route, or DNS Blocking the Path to the Server

When the Backend health Details message says the gateway could not reach the backend at all, with a connection refused or an unreachable reason rather than an unexpected status code, the problem is on the path between the gateway and the backend, not in the application. Three things sit on that path and any of them can break it: a network security group, a user-defined route, and DNS resolution. Each blocks the gateway from completing the probe or the request, the member reads Unhealthy, and the result is a 502.

The network security group case is the one that catches teams most often, and it has two halves that are easy to confuse. The first half is the NSG on the backend subnet or backend network interface. If that NSG does not allow inbound traffic on the port the gateway uses to probe and to serve, the probe cannot reach the backend, the member reads Unhealthy, and every request 502s. The fix is to allow inbound traffic from the gateway to the backend on the relevant ports. The second half is the NSG on the gateway subnet itself, which has its own non-negotiable requirements. The gateway subnet must permit the inbound infrastructure ports the platform requires for the gateway to function, and it must allow outbound traffic to the backends. A common mistake is locking the gateway subnet NSG down so tightly that it interferes with the gateway's own operation, which can manifest as backends that cannot be reached and 502s that no backend change resolves.

### Does an NSG on the gateway subnet cause a 502?

Yes, it can. The gateway subnet has required inbound infrastructure ports and must allow outbound to the backends. An NSG that blocks those, or that blocks the probe and traffic ports on the backend side, stops the gateway from reaching any member, every member reads Unhealthy, and the client receives a 502.

The reliable way to confirm a network block is to read the effective security rules on the backend network interface, which shows the combined result of the subnet NSG and the interface NSG after priority is applied. This is the same technique that resolves a general filtering mystery, and it tells you exactly which rule allows or denies the gateway's traffic rather than leaving you to read two rule sets in your head.

```bash
# Show the effective security rules on the backend NIC to see what actually allows or denies the gateway
az network nic list-effective-nsg \
  --resource-group rg-edge-prod \
  --name nic-backend-01 \
  --query "value[].effectiveSecurityRules[?direction=='Inbound'].{name:name, priority:priority, access:access, proto:protocol, dest:destinationPortRange, src:sourceAddressPrefix}" \
  --output table
```

Read the output for a rule that allows inbound traffic on the gateway-to-backend port from the gateway subnet, and confirm no higher-priority rule denies it first. If the allowing rule is missing or a deny rule wins on priority, you have found the cause, and the fix is to add or reprioritize a rule that permits the gateway's probe and traffic ports. This is the same effective-rule reading that the deeper treatment of [why an NSG blocks traffic unexpectedly](/2022/11/21/fix-nsg-blocking-traffic/) walks through in detail, and the discipline transfers directly: stop reasoning about rules in the abstract and read the effective set the platform actually applies.

A user-defined route can break the path in a less obvious way. If a route table on the gateway subnet sends backend-bound traffic, or the return traffic, through an appliance or a next hop that drops or mangles it, the gateway cannot complete the conversation with the backend and the member reads Unhealthy. Asymmetric routing, where the request goes one way and the response tries to return another, is a frequent culprit when a firewall appliance sits in the path. Confirming this means reading the effective routes on the network interface and tracing where backend traffic and its return are actually sent.

```bash
# Show the effective routes on the backend NIC to find a route that diverts or drops backend traffic
az network nic show-effective-route-table \
  --resource-group rg-edge-prod \
  --name nic-backend-01 \
  --output table
```

DNS is the third path problem, and it appears specifically when the backend pool references fully qualified domain names rather than IP addresses. The gateway must resolve those names from within its own subnet, using whatever DNS the virtual network is configured to use. If the virtual network points at a custom DNS server that cannot resolve the backend name, or the name only resolves on the public internet and not internally, the gateway cannot find the backend, the member reads Unhealthy, and the client gets a 502. Confirming this means resolving the backend FQDN from a machine in the gateway subnet using the same DNS the gateway uses, and the fix is to make the name resolve correctly from inside the network, whether by correcting the custom DNS configuration, adding a private DNS zone, or fixing on-premises forwarding.

The prevention across this whole family is to treat the gateway-to-backend path as a first-class part of the design rather than an afterthought. Document the required ports, keep the gateway subnet NSG aligned with the platform requirements rather than over-locked, avoid routing backend traffic through appliances that introduce asymmetry unless you have validated the return path, and make sure any FQDN-based backend resolves from inside the network the gateway lives in.

## Cause Four: A Backend Timeout Longer Than the Request Limit

Some 502s are not about reachability at all. The backend is healthy, the probe passes, the network path is open, and most requests succeed. Then under load, or on a particular slow endpoint, requests start returning 502 intermittently. This is the timeout family, and it is distinct because the Backend health view may show members as Healthy even while clients receive 502s, or members may flip between Healthy and Unhealthy as load rises and falls.

Application Gateway has a backend request-timeout setting in the backend HTTP setting. It defines how long the gateway will wait for the backend to return a response before it gives up and returns a 502 to the client. If a backend operation legitimately takes longer than that timeout, the gateway abandons the request and the client sees a 502 even though the backend would have answered given a few more seconds. This is common with report generation, large uploads, slow database queries behind the application, and any endpoint whose work is genuinely lengthy. The 502 in this case is not a broken backend; it is a backend that is slower than the gateway is configured to tolerate.

### Can a slow backend cause a 502 even when it is healthy?

Yes. The backend HTTP setting has a request-timeout, and if the backend takes longer than that to respond, the gateway abandons the request and returns a 502 even though the backend is up and the probe passes. Slow endpoints, heavy queries, and large transfers hit this while the member still reads Healthy.

Confirming a timeout 502 means correlating the failures with backend response time rather than with reachability. If the failures are intermittent, cluster under load, and the affected requests are the slow ones, the timeout is the likely cause. Read the current request-timeout on the backend HTTP setting and compare it against how long the slow operations actually take.

```bash
# Read the backend HTTP setting request-timeout and related connection settings
az network application-gateway http-settings list \
  --resource-group rg-edge-prod \
  --gateway-name agw-edge-prod \
  --query "[].{name:name, port:port, protocol:protocol, timeout:requestTimeout, drain:connectionDraining}" \
  --output table
```

If the request-timeout is shorter than the real duration of the slow operations, you have two honest options and one false one. The honest options are to make the backend faster, which is the better long-term answer, or to raise the request-timeout to a value that accommodates the legitimate slow operations without masking a genuinely broken backend. The false option is to crank the timeout to an enormous value to hide the problem, which trades a fast 502 for a slow hang and a worse experience. Raise the timeout to fit the real work, and treat any operation that needs a very long timeout as a candidate for a redesign that returns quickly and does the slow work asynchronously.

There is a related timing failure that produces 502s under load even with a reasonable request-timeout: a mismatch between the gateway's idle timeout and the backend's keep-alive timeout. If the backend closes idle connections faster than the gateway expects, the gateway can try to reuse a connection the backend has already torn down, and the request fails. The fix is to make the backend keep-alive timeout longer than the gateway idle timeout so the gateway never reuses a connection the backend has closed underneath it. Connection draining is the companion setting that lets in-flight requests finish gracefully when a backend is being removed, and enabling it prevents 502s during scaling and deployment events when members come and go.

The prevention for the timeout family is to size the request-timeout to the real distribution of backend response times with headroom, to keep slow operations off the synchronous request path where possible, and to align the keep-alive and idle timeouts so connection reuse never races a teardown. This family rewards measurement: capture the backend response-time distribution, set the timeout above the high percentile of legitimate work, and you stop both the premature 502s and the temptation to hide a real slowdown behind an enormous timeout.

## Cause Five: An HTTPS Host-Header or Certificate Mismatch

The most confusing 502 of all is the one where the Backend health view shows the member as Healthy and the client still receives a 502, or where the probe itself fails with a certificate or common-name message. This is the HTTPS backend family, and it confuses people precisely because the usual instinct, reading backend health and finding it green, seems to clear the backend of blame. It does not, because for an HTTPS backend there are two distinct conversations that must both succeed: the probe and the real request, and they can carry different host headers and hit different certificate checks.

When the gateway talks to an HTTPS backend, it must validate the backend's certificate and it must send a host header the backend will accept. Two things commonly go wrong. The first is the certificate trust and common name. The gateway must trust the certificate the backend presents, and on an end-to-end TLS configuration the certificate's common name or subject alternative name must match the host name the probe is configured to send. If the probe sends one host name and the certificate is issued for another, the validation fails and the member reads Unhealthy with a certificate or common-name reason in the Details column. The fix is to make the probe host header match the name on the backend certificate and to ensure the gateway trusts the certificate chain, either through a well-known certificate authority setting or by providing the trusted root certificate.

The second failure is the host header the gateway forwards on the real request. Even when the probe passes, the actual client request carries a host header derived from the backend HTTP setting, and if that host header is not what the backend expects, the backend can reject the request and the gateway returns a 502. This is exactly the scenario where backend health is green, because the probe used an acceptable host, but real requests fail because they carry a host the backend does not serve. An App Service backend is the classic example: it answers to its azurewebsites.net hostname, and if the gateway forwards a different host header the App Service may reject the request, producing a 502 against a perfectly healthy-looking backend.

### Why is my 502 happening when Backend health shows Healthy?

Because the probe and the real request are separate conversations. The probe can pass with one host header while the actual request carries a different host the backend rejects, or an HTTPS backend can accept the probe yet fail certificate validation on the real path. A green probe does not guarantee the real request succeeds.

Confirming the certificate and host-header family means inspecting the backend HTTP setting's host name configuration and the certificate the backend presents, then reproducing both the probe request and a real request from inside the network. The key insight is to test the same host header the gateway sends rather than whatever default your test tool uses, because the whole failure is about the host header and the certificate name lining up.

```bash
# Inspect the backend HTTP setting host-header behavior for an HTTPS backend
az network application-gateway http-settings list \
  --resource-group rg-edge-prod \
  --gateway-name agw-edge-prod \
  --query "[].{name:name, protocol:protocol, port:port, hostFromBackend:pickHostNameFromBackendAddress, hostNameOverride:hostName, trustedRoot:trustedRootCertificates}" \
  --output json
```

If pickHostNameFromBackendAddress is set, the gateway uses the backend address as the host header, which works for an App Service default hostname and breaks for a backend that expects a different name. If a hostName override is set, the gateway sends that fixed name, which must match both what the backend serves and the certificate common name. Reproduce the real request against the backend with that exact host header over HTTPS, and watch whether the backend accepts it and whether the certificate validates.

```bash
# Reproduce the real HTTPS request with the host header the gateway actually sends
curl -sS -o /dev/null -w "%{http_code} %{ssl_verify_result}\n" \
  --resolve app.internal.example.com:443:10.0.2.4 \
  https://app.internal.example.com/
```

If the certificate fails to validate, fix the trust configuration so the gateway accepts the chain, or align the certificate's common name with the host the probe and request send. If the backend returns an error status to the forwarded host header, change the host-header behavior so the backend receives a name it serves. The discipline that makes this family tractable is to stop treating the probe result as the whole story for HTTPS backends and to always test the real request with the real host header and the real certificate path.

The prevention is to keep the three names aligned by design: the host header the probe sends, the host header the real request carries, and the common name on the backend certificate should all agree, and the gateway should trust the chain that issued that certificate. When those align, the HTTPS backend family of 502s disappears, and when they drift apart, you get the maddening green-health-but-502 symptom that this section exists to explain.

## Cause Six: A Backend Listening on the Wrong Port

The simplest cause is worth its own short treatment because it is so easy to overlook once you have learned to suspect the elaborate ones. The backend HTTP setting tells the gateway which port to connect to on the backend, and the probe inherits that port unless a custom probe overrides it. If the application listens on a different port than the one configured, the gateway connects to a closed port, gets a connection refused, marks the member Unhealthy, and returns a 502. The application is running. The gateway is simply knocking on the wrong door.

This happens when an application is moved between environments and the port changes, when a container is mapped to a host port that differs from what the configuration expects, or when someone configures the backend setting for 80 while the application listens on 8080. The Backend health Details message typically reports a connection refused or no-response reason on the configured port, which is the same signal as a network block but with a different fix. The way to tell them apart is to test the port directly from inside the network: if a network block were the cause, the connection would fail even to a port the application listens on, whereas a wrong-port problem connects fine to the real port and refuses only the configured one.

```bash
# Test which port the backend actually listens on from inside the VNet
for port in 80 8080 443 5000; do
  echo -n "port $port: "
  timeout 3 bash -c "</dev/tcp/10.0.2.4/$port" 2>/dev/null && echo open || echo closed
done
```

When the test shows the application open on a port other than the one the backend HTTP setting names, the fix is immediate: point the backend HTTP setting and the probe at the port the application actually listens on. This is the cause that most rewards the discipline of reading backend health and reproducing the probe from inside the network, because the fix is a single setting change and the only way to waste time on it is to skip the read and start restarting things.

## When End-to-End TLS Trust Breaks: The 502 That Survives a Correct Host Header

Cause Five covered the host header and the certificate common name, but there is a separate end-to-end TLS failure that produces a 502 even when the host name lines up correctly, and it is worth its own treatment because the signal looks almost identical while the fix lives somewhere else entirely. When a v2 SKU forwards traffic to an HTTPS pool member, it does not simply open a socket and trust whatever certificate the server presents. It validates the certificate chain the server offers, and if it cannot build a path from the leaf certificate up to a root it trusts, it refuses the connection, marks the member Unhealthy, and returns a 502 to the client. The host name can match perfectly and the certificate can be valid in a browser, yet the handshake still fails because the gateway never received an intermediate certificate it needed to complete the chain, or because the root that signed the server certificate was never uploaded to the gateway for a member using a privately issued certificate.

The two shapes here are an incomplete chain and an untrusted root. An incomplete chain happens when the server presents only its leaf certificate and omits the intermediate, which many browsers paper over by fetching the missing piece on their own but which the gateway does not, so the validation fails on the gateway while the same site loads cleanly in a browser. The fix is to install the full chain on the server so the leaf and every intermediate are presented together during the handshake. An untrusted root happens when the server uses a certificate issued by a private or internal authority, and the fix on a v2 gateway is to upload that issuing root or the explicit trusted root list onto the HTTPS setting so the gateway can complete the path. The way to confirm this family rather than the host-name family is to read the Details message, which names a trust or chain failure rather than a name mismatch, and to run an explicit handshake test from inside the network that prints the certificate chain the server actually presents.

```bash
# Show the exact certificate chain the server presents during a TLS handshake
echo | openssl s_client -connect 10.0.2.4:443 -servername app.internal.example.com 2>/dev/null \
  | openssl x509 -noout -issuer -subject
# A missing intermediate or an unexpected issuer here explains a 502 that a browser hides
```

When the handshake test shows a chain the gateway cannot complete, no amount of host-header correction will clear the 502, because the name was never the problem. The discipline that saves the afternoon is the same one the whole article rests on: read the Details message before assuming, and let the trust failure it names send you to the chain and the root list rather than back to the host configuration you already verified.

## When the Backend Closes the Connection: Keep-Alive and Buffering 502s

A distinct slice of 502s comes not from the gateway failing to reach the backend but from the backend closing the connection underneath the gateway mid-conversation. The access log signature is an error information field reporting that the upstream closed the connection, and the symptom is intermittent 502s that do not correlate with the backend being down, because the backend is up and answering most requests. This family is worth separating because the fixes live on the backend's connection behavior rather than in the gateway's pool, probe, or network configuration.

The most frequent shape is a keep-alive timeout mismatch. Application Gateway reuses connections to the backend for efficiency, holding them open according to its own idle timeout. If the backend's keep-alive timeout is shorter than the gateway's idle timeout, the backend closes an idle connection that the gateway still believes is open, and when the gateway sends the next request down that connection, the backend has already torn it down and the request fails with a 502. The failures are intermittent because they only happen when the gateway reuses a connection that the backend closed in the gap. The fix is to make the backend keep-alive timeout longer than the gateway idle timeout so the gateway never sends a request down a connection the backend has already closed. This is a backend web server setting, configured on the application's server rather than on the gateway, and aligning it removes a whole class of maddening intermittent 502s.

A second shape involves large request bodies. When a client sends a large upload, Application Gateway may buffer the request body to a temporary file before forwarding it, and on certain workloads the interaction between that buffering and the backend's expectations produces a 502. The relevant lever is the request and response buffering configuration on the gateway, which controls whether the gateway buffers bodies before forwarding them. Changing buffering behavior is a measured trade-off rather than a free fix, because buffering affects throughput and memory, so the right approach is to test the change against a representative load before applying it to a production gateway. The buffering lever is genuinely useful for the narrow case of large-body uploads that 502, but it is not a general-purpose fix and should not be reached for before the cause table's more common rows are ruled out.

A third shape is the backend crashing or recycling under load. If the backend process restarts, runs out of memory, or recycles its worker, it drops in-flight connections, and the gateway reports the upstream closing the connection. The 502s here track load and resource pressure, and the access log will show them clustering when the backend is busiest. The fix is on the backend's capacity and stability rather than on the gateway: give the backend enough headroom that it does not recycle under normal load, and fix whatever causes it to crash. Connection draining on the gateway helps the controlled case where a backend is being removed deliberately, letting in-flight requests finish gracefully rather than dropping them into a 502, and enabling it smooths deployments and scaling events where members come and go.

The way to tell this family apart from the reachability and probe families is the access log error information field combined with the backend reading Healthy. When the gateway can clearly reach the backend, the probe passes, and the 502s still appear intermittently with an upstream-closed reason in the log, you are in the connection-behavior family, and the fixes are keep-alive alignment, measured buffering changes, and backend stability rather than anything in the pool or the network.

## Catching the 502 Before Users Do: Monitoring and Alerting

Every cause in the table is easier to handle if you learn about the 502 from an alert rather than from an affected user, and the same signals that diagnose a 502 also detect one early. The two most valuable alerting signals are the healthy host count metric and the 502 rate in the access log, and wiring both into alerts converts the incident from a surprise into a notification with the cause already half-identified.

The healthy host count per backend pool is the single best leading indicator. When it drops to zero on a pool, a 502 is imminent or already happening, and the moment of the drop is the moment to investigate. An alert that fires when the healthy host count for any pool falls below one gives you the earliest possible warning and, because the metric is per pool, it tells you which pool to look at before you even open the Backend health view. Setting the threshold at one rather than zero gives a margin: you learn when a multi-member pool is down to its last healthy member, before the last one fails and every request starts returning a 502.

```kql
// Alert query: count 502 responses per backend pool over the last five minutes
AzureDiagnostics
| where Category == "ApplicationGatewayAccessLog"
| where httpStatus_d == 502
| summarize errors = count() by backendPoolName_s, bin(TimeGenerated, 5m)
| where errors > 0
```

The 502 rate from the access log is the confirming signal that pairs with the metric. An alert on a rising count of 502 responses tells you that clients are actually being affected, which the healthy host count alone does not, because a pool can lose a member without any client-facing 502 if the remaining members absorb the load. Running the two alerts together gives you both the leading indicator and the impact signal: the healthy host count warns you that a pool is degrading, and the 502 rate tells you whether users are feeling it yet. Together they let you intervene during the window when one member is failing but the others are still serving, which is exactly when a fix is cheapest.

The durable prevention is to make these checks part of the gateway's definition rather than a manual afterthought. Deploy the gateway, its backend pools, its probes, and its alerts together as code, so that a probe path, a backend port, and a healthy-host alert are all created and updated in the same change. When the probe path and the backend port live in the same template that deploys the application, they cannot drift apart the way they do when one is changed by hand and the other is forgotten, which is the structural cause behind a large share of the 502s in the cause table. Treating the alerting and the configuration as one deployable artifact closes the gap between a change that breaks a backend and the moment someone notices, and it turns the read-then-fix discipline into something the platform enforces rather than something an engineer has to remember mid-incident.

## How to Read a 502 End to End in Under Five Minutes

Putting the causes together, a fast and reliable 502 diagnosis follows a fixed order that always starts with reading rather than changing. Open the Backend health view and read the status and Details for every member of the pool the failing listener routes to. If the pool is empty or its addresses do not match your running backends, you are in cause one and you fix the membership. If members are Unhealthy with a status-code or path reason, you are in cause two and you reconcile the probe with the application. If members are Unhealthy with a connection refused or unreachable reason, you are in cause three or cause six, and you reproduce the probe from inside the network to tell a network block from a wrong port. If members are Healthy but clients still see 502s, you are in cause four if the failures correlate with slow requests under load, or cause five if an HTTPS backend has a host-header or certificate mismatch.

That single decision tree, driven entirely by the Backend health Details message, resolves the overwhelming majority of Application Gateway 502s without a single speculative change. The reason it works is the backend-health-first rule: the gateway already wrote down why it considers each backend healthy or not, and reading that note is faster and more accurate than any guess. The only reason a 502 takes hours instead of minutes is that the engineer started changing settings before reading the note the gateway left them.

For the layer choice that sits behind some of these incidents, it helps to understand when Application Gateway is even the right tool, which is the subject of the comparison between [a layer-4 load balancer and the layer-7 Application Gateway](/2023/10/02/load-balancer-vs-app-gateway/) and how each handles backends differently. Application Gateway operates at layer 7 and makes routing and health decisions based on HTTP, which is exactly why its 502 diagnosis centers on health, host headers, and status codes rather than on raw connectivity alone.

## Reproduce a 502 and Practice the Diagnosis

The fastest way to internalize this decision tree is to break each cause on purpose in a safe environment and watch the Backend health view report it, so that during a real incident you recognize the signal immediately. You can stand up an Application Gateway with a small backend, then deliberately misconfigure the probe path, block the backend port with an NSG, point the backend setting at a wrong port, and introduce a slow endpoint, observing the distinct Backend health signal each one produces. That muscle memory is what turns the five-minute diagnosis from an aspiration into a habit.

To build that environment without assembling it by hand, you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), which provides a sandbox for standing up an Application Gateway with a backend pool and a tested library of the exact commands this article uses to read backend health, inspect probes, and reproduce the probe request from inside the virtual network. Reproducing each cause in that sandbox and watching the Backend health Details message change is the single most effective way to make the cause table second nature.

Once you can stand up the failure, the next step is rehearsing the diagnosis under realistic conditions, and you can [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html), where each drill presents a 502 with a different underlying cause and asks you to read the backend health, name the cause, and apply the matching fix against the clock. Practicing the read-then-fix discipline on varied scenarios is what keeps you from reverting to the restart-and-hope reflex when a real 502 lands during an incident.

## A Worked Example: Tracing a Real 502 From Log to Fix

To show the method end to end, consider a concrete incident of the kind teams report repeatedly. An application behind Application Gateway starts returning 502 to all users at once, shortly after a routine deployment that rebuilt the backend virtual machine scale set. The on-call engineer has two instincts available: restart the gateway, or read the evidence. Reading wins.

The first read is the Backend health view, which shows the backend pool with two members, both Unhealthy, and a Details message reporting that the gateway received no response from either member on port 8080. That single read already narrows the field dramatically. The pool is not empty, so cause one's empty-pool shape is out. The reason is no-response rather than an unexpected status code, so the probe-status case is unlikely. No-response on the configured port points at either a network block or a wrong port, the two causes that share that signal.

The second read separates those two. From a jump box in the gateway subnet, the engineer tests the backend addresses on several ports and finds the application open on port 80 and refusing connections on port 8080. That is decisive. The application is listening, the network path is open, and the gateway is simply connecting to the wrong port because the backend HTTP setting names 8080 while the rebuilt scale set now serves on 80. The deployment changed the listening port and the backend setting was never updated to match. Confirming the cause took two reads and zero configuration changes.

```bash
# The two reads that solved it, in order
az network application-gateway show-backend-health \
  --resource-group rg-edge-prod --name agw-edge-prod \
  --query "backendAddressPools[].backendHttpSettingsCollection[].servers[].{address:address, health:health}" -o table

# From a jump box in the gateway subnet:
for p in 80 8080; do echo -n "port $p: "; timeout 3 bash -c "</dev/tcp/10.0.2.4/$p" 2>/dev/null && echo open || echo closed; done
```

The fix follows directly from the confirmed cause: update the backend HTTP setting and the probe to target port 80, the port the application actually listens on after the rebuild. Within a probe interval the members read Healthy again and the 502s clear. The prevention is equally clear from the post-mortem: the deployment that changed the listening port must also update the backend setting, so the two cannot drift apart, which is the same structural lesson that the empty-pool case teaches. The whole incident, from page to fix, fits inside the five-minute decision tree precisely because the engineer read the backend health and the port before changing anything.

The same trace shape applies to every cause. A status-code reason in the health Details sends you to reproduce the probe path and confirm a 404 or a 401, then fix the path or the status range. A certificate reason sends you to reproduce the HTTPS request with the gateway's host header and confirm the common-name mismatch, then align the names. A timeout signature in the metrics and access logs sends you to compare the backend response time against the request-timeout, then size the timeout to the real work. The method is invariant: read the signal, reproduce the failing condition from inside the network, confirm the cause, apply the matching fix.

## The AKS Ingress Backend: A 502 Pattern Worth Its Own Treatment

A particularly common and confusing 502 appears when the backend behind Application Gateway is an Azure Kubernetes Service cluster, whether through the application gateway ingress controller or through the gateway pointing at an ingress controller running in the cluster. The reason it deserves its own treatment is that the failure surface combines the gateway's backend-health logic with the cluster's own routing, so a 502 can originate in either layer, and the diagnosis has to localize which one.

When the gateway points at an ingress controller's service, the backend the gateway probes is the ingress controller, not the application pod directly. A 502 in this setup can mean the ingress controller is up but has no matching ingress rule for the requested host or path, so it returns a status the gateway treats as a failure, or it can mean the ingress controller is forwarding to a pod that is not ready, or it can mean the gateway's probe is hitting the ingress controller on a path the controller does not serve a success on. The layered routing means the gateway's Backend health can read Healthy because the ingress controller answers the probe, while real requests 502 because the controller has no route for them or the upstream pod is unready.

### How do I localize a 502 between Application Gateway and the AKS ingress?

Reproduce the request directly against the ingress controller from inside the cluster network, bypassing the gateway. If the ingress returns the response correctly when called directly, the problem is in the gateway's host header, path routing, or probe. If the ingress itself returns a 502 or an error when called directly, the problem is inside the cluster's routing or the pod readiness.

The decisive test is to bypass the gateway and call the backend directly, which is the same isolation principle the broader diagnosis uses, applied to the layered case. From a pod or a node inside the cluster network, send the same request the gateway would send, with the same host header, directly to the ingress controller's service address. If the ingress returns the correct response, the cluster routing is fine and the gateway is sending something the ingress does not match, which is almost always a host header the ingress rules do not recognize or a path the gateway probe judges as unhealthy. The fix lives in aligning the gateway's host header and probe with the ingress rules. If the ingress itself returns a 502 when called directly, the problem is inside the cluster: a pod that is not ready, a service with no healthy endpoints, or an ingress rule pointing at the wrong service, and the fix lives in the cluster rather than in the gateway.

```bash
# From inside the cluster, call the ingress controller directly with the gateway's host header
kubectl run probe-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -sS -o /dev/null -w "%{http_code}\n" \
  -H "Host: app.internal.example.com" \
  http://ingress-nginx-controller.ingress-nginx.svc.cluster.local/
```

A clean response from that test clears the cluster and points back at the gateway's host-header and probe configuration. A 502 or an error from that test sends you into the cluster to check pod readiness, the service endpoints, and the ingress rules. This bypass test is the AKS-specific version of the read-then-reproduce discipline, and it resolves the layered ambiguity that makes these 502s feel intractable when you try to diagnose them from the gateway alone. The recurring lesson is that a 502 against a layered backend is still answered by localizing which layer failed, and the way to localize is to reproduce the request one layer at a time until the failure appears.

## Related Failures Often Confused With a 502

A 502 is easy to confuse with its neighbors, and knowing the difference saves you from chasing the wrong diagnosis. A 504 Gateway Timeout is the closest relative and the one most often mistaken for a 502, but it means something specific: the gateway reached the backend and waited, but the backend did not respond in time. A 504 points hard at the timeout family and at slow backends, where a 502 spans the whole cause table. If you see 504 rather than 502, jump straight to the backend response-time and request-timeout analysis rather than walking the full tree.

A 403 from Application Gateway with a web application firewall enabled is a different animal entirely. That is the firewall blocking a request it judged malicious, not a backend problem, and no amount of backend-health reading will explain it because the request never reached the backend. The fix lives in the firewall rules and exclusions, not in the backend pool. Recognizing a firewall 403 keeps you from misreading a security action as a backend failure.

A health probe failure at the layer-4 load balancer is the sibling failure one layer down, and the diagnostic discipline is the same even though the surface differs. When a load balancer marks a backend down, the symptom and the read-the-health-first method mirror the Application Gateway case closely, and the deeper treatment of [why a load balancer health probe marks a backend down](/2022/12/05/fix-load-balancer-probe-failure/) covers the layer-4 equivalent of everything in this article. The shared lesson across both layers is that the platform records why it considers a backend healthy, and reading that record beats guessing every time.

At the edge, a 502 from Front Door is the layer-above sibling, where the edge could not get a valid response from its origin. The cause families rhyme with the Application Gateway ones but the names differ, and choosing between the edge services in the first place is the subject of the comparison of [Front Door, CDN, and Application Gateway](/2023/10/09/front-door-vs-cdn-vs-gateway/) and which belongs where in an architecture. If your 502 is coming from Front Door rather than from Application Gateway, the origin-health reading is the right starting point, and it parallels the backend-health reading exactly.

## The Misdiagnoses That Waste the First Hour

A handful of wrong turns account for most of the time teams lose on a 502, and naming them helps you avoid the reflex that leads to each. The first and most expensive is changing configuration before reading the health view, in any of its forms: restarting the gateway, recycling the virtual machines, scaling the instance count, or reissuing certificates on a hunch. Each of these is a plausible fix for some other problem, and each leaves the actual cause untouched, so the 502 returns the moment the change settles and you are no further along than when you started, only an hour poorer.

The second misdiagnosis is trusting a green health view as proof that the upstream is blameless. As the host-header and certificate section showed, the probe and the real request are different conversations, and a pool member can pass its probe while rejecting the request the gateway actually forwards. An engineer who sees Healthy and immediately concludes the problem must be the gateway or the client has skipped the one read that would have shown the host header or the certificate name mismatch. The discipline is to reproduce the real request with the real host header whenever the health view looks clean but clients still fail, rather than treating green as the end of the inquiry.

The third is mistaking a network block for a wrong port, or the reverse, because both produce a connection-refused signal. Teams that stop at the signal without running the from-inside-the-network port test open firewall rules that were never the problem, or rewrite routing that was always fine, while the application quietly listens on a port nobody checked. The port test from a jump box in the gateway subnet costs seconds and resolves the ambiguity outright, and skipping it is how a one-setting fix turns into a firewall investigation.

The fourth is reaching for the request and response buffering lever as a general remedy. Because adjusting buffering occasionally clears a narrow large-upload 502, it acquires a reputation as a thing to try, and engineers apply it to 502s that have nothing to do with body buffering, changing a throughput-affecting setting on a production gateway for no reason and sometimes introducing a new problem. Buffering is the right lever only for the specific large-body case the access log points at, and it belongs after the common rows of the cause table are ruled out, never before.

The fifth is blaming the platform. A 502 feels like the gateway is broken, and it is tempting to assume Azure is having a bad day, but a quick Resource Health check almost always reports the gateway as available, which puts the cause squarely back in your own configuration. Assuming a platform fault delays the real diagnosis and occasionally produces a support case that returns the same answer the cause table would have given in five minutes. Check Resource Health to rule the platform out, then read the health view and work the table.

## The Verdict on Application Gateway 502s

A 502 from Application Gateway is not a mysterious failure of the gateway. It is the gateway telling you, in the Backend health view, that it has no healthy backend to serve a request, or occasionally that a backend it believes is healthy still failed to return a valid response on the real path. The entire art of fixing it quickly is the backend-health-first rule: read the Backend health Details message, match it to one of the six causes, and apply the fix that cause calls for. An empty or wrong pool, a probe that disagrees with the application, a network block on the path, a backend slower than the timeout, an HTTPS host-header or certificate mismatch, and a wrong port are the whole territory, and each one announces itself in the health view if you read it before you act.

The discipline that this article exists to instill is the refusal to change settings before reading health. Restarting the gateway, recycling the backends, scaling the instances, and reissuing certificates are all changes you might eventually make, but making them before reading the Backend health Details message is how a five-minute fix becomes an afternoon. Read first. The gateway already knows why it is returning a 502, and it wrote the reason down where you can find it. Match the reason to the cause table, apply the matching fix, and the 502 clears.

## Frequently Asked Questions

### Q: What does a 502 Bad Gateway from Azure Application Gateway actually mean?

It means the gateway accepted the client request, tried to forward it to a member of the backend pool, and could not get a valid response back. Application Gateway is a layer-7 reverse proxy, so a 502 is the proxy reporting that the upstream connection to the backend failed, not that the gateway itself broke. The client connection succeeded, which is why the client received the 502 body at all. The failure is scoped entirely to what happens after the gateway selects a backend and tries to talk to it. Because the gateway only routes to members it considers healthy, a 502 almost always means every member of the chosen pool is currently unhealthy, and the Backend health view names the reason. The correct first move is always to read that view rather than to assume the gateway needs a restart.

### Q: Where do I look first to diagnose an Application Gateway 502?

Open the Backend health view on the Application Gateway resource, which lists every backend pool, every member, and a status of Healthy, Unhealthy, or Unknown for each, along with a Details message that usually names the cause. This is the single most valuable artifact in the diagnosis because the gateway has already recorded why it considers each backend healthy or not. You can read the same information from the command line with the show-backend-health command, which is faster in a terminal and better for capturing a record. The Details message maps cleanly onto causes: a status-code reason points at the probe, a connection-refused reason points at the network or a wrong port, a certificate reason points at the HTTPS backend, and a timeout reason points at a slow backend. Reading this first splits the problem before you change anything.

### Q: Does an empty backend pool cause a 502 error?

Yes. If the backend pool contains no members, or its members reference addresses that no longer correspond to running backends, the gateway has nowhere to send the request and returns a 502 on every request to that pool. This happens often where infrastructure is recreated through pipelines, because a rebuilt scale set or virtual machine gets new private addresses while the pool still references the old ones. It also happens when a pool points at a fully qualified domain name that no longer resolves from inside the gateway subnet. Confirm it by listing the pool addresses and comparing them to the current private IPs or hostnames of your running backends. The durable fix is to stop hardcoding ephemeral addresses and instead reference backends by an identity that survives recreation, or to make pool population part of the same deployment that creates the backends so the two never drift apart.

### Q: Why does my backend show Unhealthy when the application works in a browser?

Because the health probe judges health differently from how a browser experiences the site. Your browser follows redirects, sends cookies and authentication, and accepts pages the probe rejects, while the probe sends one fixed request and accepts only a defined status range, by default 200 to 399. A probe path that returns 404 because the route does not exist, or an endpoint that returns 401 or 403 because it sits behind authentication, or a path that 302 redirects to a login page, all read as Unhealthy even though the application serves real traffic perfectly. The fix is to point the probe at a path that returns a clean success without authentication, often a dedicated lightweight health endpoint, or to widen the accepted status range to include the code your endpoint legitimately returns. Reproducing the exact probe request from inside the network confirms which of these applies.

### Q: Can a misconfigured health probe path cause a 502?

Yes, and it is one of the most common causes in production. The probe requests a specific path, and if the application does not serve that path it returns a 404, which falls outside the default healthy status range, so the gateway marks the member Unhealthy and every request returns a 502. The application is running fine; the probe is asking for a door that does not exist. Confirm it by reading the probe path from the probe configuration and reproducing that exact request against the backend from a machine in the gateway subnet. If the request returns a 404, the path is wrong. The fix is to point the probe at a path the application actually serves and that returns a success status, which is usually a purpose-built endpoint that does nothing but confirm the process is up and reachable.

### Q: Does an NSG blocking the backend port cause an Application Gateway 502?

Yes. If a network security group on the backend subnet or backend network interface does not allow inbound traffic from the gateway on the port used for probing and serving, the gateway cannot reach the backend, the member reads Unhealthy, and every request returns a 502. Confirm it by reading the effective security rules on the backend network interface, which shows the combined result of the subnet and interface NSGs after priority is applied, and look for a rule that allows the gateway's traffic on the relevant port without a higher-priority deny winning first. The fix is to add or reprioritize a rule that permits the gateway's probe and traffic ports. This is distinct from a wrong-port problem, which you tell apart by testing the port directly from inside the network: a network block fails even to a port the application listens on, while a wrong port connects fine to the real port.

### Q: Can the gateway subnet NSG itself cause a 502?

Yes, and it is easy to overlook. The Application Gateway subnet has required inbound infrastructure ports that the platform needs for the gateway to operate, and it must allow outbound traffic to the backends. An NSG locked down so tightly that it interferes with these requirements can stop the gateway from functioning correctly or from reaching its backends, which surfaces as members that cannot be reached and 502s that no backend-side change resolves. The mistake usually comes from applying a restrictive security baseline to every subnet uniformly without accounting for the gateway subnet's special requirements. The fix is to align the gateway subnet NSG with the platform's documented inbound infrastructure requirements and outbound-to-backend allowance rather than over-locking it. When a 502 persists despite a healthy-looking backend and an open backend NSG, the gateway subnet NSG is worth examining directly.

### Q: How do I tell a network block from a wrong backend port?

Both produce a connection-refused or unreachable reason in the Backend health Details, so you separate them by testing the backend's ports directly from inside the virtual network. Connect to several candidate ports from a machine in the gateway subnet and observe which respond. If the port the backend HTTP setting names is closed but another port is open, the application is listening on a different port than the gateway expects, and the fix is to point the backend setting and probe at the real port. If every port including the real one fails to connect, a network block such as an NSG rule or a route is preventing the connection regardless of the port, and the fix lives in the security rules or the route table. This single test resolves the ambiguity between the two causes that share the same health signal.

### Q: Why do I get intermittent 502s only under load?

Intermittent 502s that cluster under load usually point at the timeout family rather than reachability. The backend HTTP setting has a request-timeout that defines how long the gateway waits for a response before returning a 502, and under load a backend can exceed that timeout on slow operations even though it answers fine when idle. Members may show as Healthy because the probe still passes, while real requests to slow endpoints fail. Confirm it by correlating the failures with backend response time and checking whether the affected requests are the slow ones. The fix is to make the backend faster where possible, or to raise the request-timeout to accommodate the legitimate slow work without setting it so high that it hides a genuinely broken backend. A related cause is a backend keep-alive timeout shorter than the gateway idle timeout, which causes connection-reuse failures under load.

### Q: How do I fix a 502 caused by a backend request timeout?

First confirm it is a timeout by checking that failures correlate with slow requests rather than with reachability, then read the request-timeout on the backend HTTP setting and compare it against how long the slow operations actually take. If the timeout is shorter than the real duration of legitimate slow work, raise it to a value with headroom above the high percentile of that work. The better long-term fix is to make the backend faster or to move genuinely slow operations off the synchronous request path so they return quickly and do their work asynchronously. Avoid the false fix of setting an enormous timeout to hide the problem, because that trades a fast failure for a slow hang. Also align the backend keep-alive timeout to be longer than the gateway idle timeout so connection reuse never races a teardown, and enable connection draining so in-flight requests finish during scaling events.

### Q: Why does my 502 happen when Backend health shows the backend as Healthy?

Because the probe and the real request are separate conversations that can behave differently. The probe can pass with one host header while the actual client request carries a different host header that the backend rejects, producing a 502 against a backend the health view calls Healthy. For an HTTPS backend, the probe can succeed while the real request fails certificate validation on a different path. An App Service backend is the classic case: it answers to its platform hostname, and if the gateway forwards a different host header the App Service rejects real requests even though the probe passed. Confirm it by reproducing the real request with the exact host header the gateway sends, not whatever default your test tool uses, and watch whether the backend accepts it. The fix is to align the host header the gateway forwards with a name the backend serves.

### Q: How does an HTTPS certificate mismatch cause a 502?

When the gateway connects to an HTTPS backend it validates the backend's certificate, and on an end-to-end TLS configuration the certificate's common name or subject alternative name must match the host name the probe sends. If the probe sends one host name and the certificate is issued for another, validation fails, the member reads Unhealthy with a certificate or common-name reason, and the client receives a 502. The gateway must also trust the chain that issued the certificate. Confirm it by reading the backend HTTP setting host configuration and reproducing the HTTPS request from inside the network with the host header the gateway sends, watching whether the certificate validates. The fix is to make the probe host header match the certificate common name and to ensure the gateway trusts the chain, either through the well-known certificate authority setting or by providing the trusted root certificate explicitly.

### Q: Does pointing the backend pool at an App Service custom domain cause a 502?

It can. An App Service answers reliably to its default platform hostname, the one ending in azurewebsites.net, and the backend pool and host-header behavior should normally target that name so the App Service receives a host it recognizes. Pointing the pool at a custom domain that only resolves on the public internet, or that the App Service does not have bound, can produce a backend the gateway cannot reach internally or that rejects the forwarded host header, and the result is a 502. The fix is either to use the platform hostname for the pool and let the host header derive from the backend address, or to properly bind and configure the custom domain on the App Service so it answers to that name. The principle is that the App Service must recognize the host header the gateway forwards, or it will reject otherwise valid requests.

### Q: What is the difference between a 502 and a 504 from Application Gateway?

A 502 Bad Gateway means the gateway could not get a valid response from the backend, which spans the whole cause table from an empty pool to a probe mismatch to a network block to a certificate problem. A 504 Gateway Timeout means something more specific: the gateway reached the backend and waited, but the backend did not respond within the allowed time. A 504 points hard at the timeout family and at slow backends, so when you see 504 rather than 502 you can skip most of the cause tree and go straight to the backend response-time and request-timeout analysis. The two share the timeout cause, but a 502 has many other causes a 504 does not, so the status code itself narrows the diagnosis. Reading which code you actually received tells you how wide to cast the search.

### Q: Will restarting the Application Gateway fix a 502?

Almost never, and reaching for it first is the most common way to waste time on a 502. The gateway is not in a broken state that a restart clears; it is correctly reporting that it has no healthy backend to serve the request. Restarting the gateway does not change the probe configuration, the backend pool membership, the network rules, the timeout, or the certificate, which are where the actual cause lives. The same applies to recycling the backend virtual machines, scaling the instance count, and reissuing certificates before you know the cause. The reliable approach is to read the Backend health view first, match the Details message to one of the six causes, and apply the specific fix that cause calls for. Restarting may eventually be part of a fix for an unrelated state issue, but as a first response to a 502 it is guessing.

### Q: How do I prevent Application Gateway 502 errors from recurring?

Prevention follows the cause table. Stop hardcoding ephemeral backend addresses and reference backends by an identity that survives recreation, or make pool population part of the same deployment that builds the backends. Give the probe a dedicated unauthenticated health endpoint that returns a clean success, and tune the interval, timeout, and threshold to tolerate the application's real behavior. Keep the gateway subnet NSG aligned with the platform's required infrastructure ports rather than over-locked, and document the backend ports the gateway needs. Size the request-timeout above the high percentile of legitimate backend work and move genuinely slow operations off the synchronous path. For HTTPS backends, keep the probe host header, the request host header, and the certificate common name aligned and trust the chain. Each of these closes one row of the cause table, and together they remove the conditions that produce a 502 in the first place.

### Q: Can I read backend health from the command line instead of the portal?

Yes, and it is often faster and better for record-keeping. The show-backend-health command on the Application Gateway returns the per-member health verdict and the reason the gateway recorded, which is the same information the portal Backend health blade displays. Reading it from a terminal lets you capture the state into a file, compare it before and after a change, and script the check into a runbook so an on-call engineer runs one command rather than clicking through the portal mid-incident. The output gives you each backend member's address, its health status, and a detail message, which you then map to the cause table exactly as you would the portal view. For reproducing the probe request itself, you pair the health read with a curl from inside the virtual network using the same path, port, and host header the gateway uses, which confirms the cause directly.

### Q: Why does only one backend show Unhealthy while others are fine?

When a single member of a multi-member pool reads Unhealthy while the others are Healthy, the gateway routes around it to the healthy members, so you may see intermittent 502s only if the unhealthy member is occasionally selected, or no client-facing 502 at all if the healthy members absorb the load. The single unhealthy member usually has a member-specific problem rather than a pool-wide one: that particular instance is not listening, has crashed, is overloaded and failing the probe, or has a stale address after a partial rebuild. Read the Details message for that specific member, then reproduce the probe against its address from inside the network. The fix is to recover or replace that instance, or to correct its address in the pool. A pool-wide 502 means every member is failing for a shared reason; a single-member failure is local to that instance.
