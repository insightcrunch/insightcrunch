---
layout: post
title: "Set Up Azure Front Door Routing Rules"
page_title: "Set Up Azure Front Door Routing Rules: Origin Groups, Health Probes, Path Patterns, Caching, Custom Domains, and WAF Configuration"
date: 2023-05-15
categories: ["Technology"]
tags: ["Azure", "Azure Front Door", "Networking", "Security", "Cloud Computing"]
excerpt: "Configure Azure Front Door routing rules end to end: origin groups, health probes, path patterns, caching, a custom domain, and an attached WAF policy."
image: "/assets/images/blog/blog-48.webp"
reading_time: 62
author: "nathan-cole"
last_updated: 2023-05-15
lang: en
---
Correct Front Door routing buys you one thing that nothing else in your stack can: a single global entry point that sends each request to a healthy backend, over the protocol you intended, with the caching and security behavior you chose. When the configuration is right, a user in Singapore and a user in Dublin both land on the closest edge, the edge forwards to an upstream that is actually serving traffic, and the response comes back transformed exactly as the route specifies. When the configuration is wrong, the same setup returns a 502 to every visitor while the portal shows a green checkmark and a route that looks perfectly valid. The gap between those two outcomes is rarely the route itself. It is almost always the origin contract sitting behind the route, and that contract is the part most setup guides skip.

![Set Up Azure Front Door Routing Rules - Insight Crunch](/assets/images/blog/blog-48.webp)

This article walks the full setup for Azure Front Door routing rules and treats the origin contract as a first-class part of the procedure rather than an afterthought. You will create an origin group with a health probe, define a route with a path pattern, configure caching so the right responses are served from the edge, attach a custom domain with a managed certificate, and bind a Web Application Firewall policy to the endpoint. At each step the gotcha that produces a silent failure gets called out next to the command that avoids it. By the end you will have a working profile and, more importantly, a mental model that explains why a route that matches the path can still fail at the backend.

Front Door routing is not a single setting. It is a chain of objects that must agree with one another: the endpoint, the route, the origin group, the backend, the health probe, the caching policy, the domain, and the security policy. A break anywhere in that chain surfaces as the same handful of symptoms, and the symptoms point at the wrong object more often than not. A 502 looks like a routing problem and is usually an upstream problem. A request hitting the wrong backend looks like a backend problem and is usually a path-pattern ordering problem. Learning which symptom maps to which object is the difference between fixing the configuration in ten minutes and rebuilding the profile twice.

A quick note on scope before the procedure. This guide uses the Standard and Premium tiers of Azure Front Door, the current generation, rather than the classic tier, which Microsoft has placed on a retirement path. The object names, the route model, and the WAF integration described here are the modern ones. If you are choosing between Front Door and a regional load balancer or a content delivery network in the first place, that decision belongs to a different conversation, and the comparison in [Front Door versus CDN versus Application Gateway](/2023/10/09/front-door-vs-cdn-vs-gateway/) walks through where each edge service fits before you ever create a route. Assume here that the decision is made and Front Door is the right tool.

## The route-and-origin-contract rule

Here is the claim this entire article is built around, stated plainly so you can quote it and test it: Front Door routing is a path match plus an origin contract. The path match decides which route handles the request. The origin contract decides whether the chosen backend will actually answer. A setup that gets the path match right but breaks the origin contract returns a 502 even though the route, on inspection, looks completely correct. Call it the route-and-origin-contract rule. Almost every confusing Front Door failure resolves once you separate those two halves and ask which one broke.

The path match is the part everyone configures. You define a route, you give it a path pattern such as `/*` or `/api/*`, you associate it with an endpoint and a domain, and Front Door uses the pattern to decide which route owns an incoming request. This half is visible, declarative, and easy to reason about. If a request to `/api/orders` does not reach the route you expected, you look at the path patterns of every route on the endpoint, work out which one matched first, and adjust. The logic is mechanical.

The origin contract is the part that hides. An upstream is not just an address. It is an address plus a set of expectations the backend holds about the requests it receives, and Front Door has to satisfy those expectations or the upstream refuses to serve. The two expectations that break setups most often are the host header and the health probe. The host header is the value Front Door sends in the `Host` line of the forwarded request. Many backends, especially App Service, multi-tenant gateways, and anything doing host-based routing internally, decide which site or which certificate to present based on that header. If Front Door sends its own endpoint hostname when the backend expects its own hostname, the upstream returns an error that surfaces at the edge as a 502. The route matched. The backend rejected. The rule held.

The health probe is the second half of the origin contract. Front Door periodically sends a request to a probe path on each upstream and uses the response to decide whether the backend is eligible to receive traffic. A backend that fails its probe is dropped from the origin group, and if every upstream in the group fails, Front Door has nowhere to send the request and returns a 502. The probe is silent by design. You will not see a request error in your application logs because the application may be perfectly healthy on the real paths. The probe is hitting a path that returns a 404, or a redirect, or a slow response, and Front Door reads that as unhealthy. The route matched. The backend was marked down. The rule held again.

Once you internalize the rule, the diagnostic flow for a 502 becomes short. First confirm the path matched the route you think it did, because if the wrong route handled the request, everything downstream is the wrong upstream. Then confirm the origin contract: is the host header the backend expects, and is the probe path returning a success code the backend actually serves. Nine times out of ten the answer is in those two questions, and the matching deep dive in [fixing Front Door 502 and upstream errors](/2022/12/19/fix-front-door-502-backend-error/) walks the same split in full when you are debugging an existing profile rather than building a new one.

The reason this rule matters for a setup guide, and not only for a troubleshooting guide, is that the origin contract is established at configuration time. You decide the host header behavior when you create the upstream. You decide the probe path when you configure the origin group. If you make those two choices correctly while you build the profile, the 502 never happens. If you accept the defaults without understanding them, you ship a route that looks right and fails the first real request. The procedure below front-loads both choices so the contract is correct before any traffic arrives.

## The InsightCrunch Front Door routing checklist

Before the step-by-step, here is the artifact to bookmark: the InsightCrunch Front Door routing checklist. It lists every object you must create, in order, with the single setting that most often breaks at each step and the verification that proves the step worked. Work top to bottom and you build a profile whose origin contract is correct by construction rather than by luck.

| Step | Object to create | The setting that breaks it | How to verify the step |
|------|------------------|----------------------------|------------------------|
| 1 | Front Door profile and endpoint | Choosing classic instead of Standard or Premium | Endpoint hostname resolves and returns the default response |
| 2 | Origin group | Probe path set to a path the backend does not serve with 200 | Backend shows healthy in the origin group health view |
| 3 | Upstream | Host header left blank when the backend needs its own hostname | A direct curl to the upstream with that host header returns 200 |
| 4 | Health probe | Probe method or protocol mismatched to the backend | Probe success rate near 100 percent in metrics |
| 5 | Route | Path pattern overlapping another route so the wrong one wins | A request to a known path reaches the intended backend |
| 6 | Caching rule | Caching enabled on responses that must stay dynamic | Cache-status header shows HIT or MISS as intended per path |
| 7 | Custom domain | DNS validation record not added, so the domain stays pending | Domain validation state reads Approved |
| 8 | Managed certificate | Domain not associated to a route, so the certificate never binds | HTTPS to the custom domain presents the managed certificate |
| 9 | WAF policy | Policy left in Detection when you intended Prevention | A test malicious request is blocked, a normal request passes |
| 10 | End-to-end verification | Skipping the host-header and probe confirmation | Full request path returns the expected upstream response |

The checklist is deliberately ordered so that the origin contract (steps 2 through 4) is in place before the route (step 5) exists. Building the route first is the most common reason a profile fails on its first request: the route is valid, but the origin behind it has never been confirmed reachable on the host header and probe path the route will use. Reverse the order and the failure has nowhere to hide.

Each row names one breaking setting because, in practice, that is how these failures arrive. They are not subtle systemic problems. They are a single field left at its default or set to a plausible wrong value, and the symptom is disproportionate to the cause. A blank host header is one empty field that turns every request into a 502. A probe path off by one segment drops an entire origin group. The checklist exists so those single fields get a deliberate decision instead of a default.

## Prerequisites and the correct order of operations

Front Door sits in front of backends, so the upstreams have to exist and be reachable before the profile can do anything useful. The prerequisites are an Azure subscription with rights to create Front Door and networking resources, at least one backend that already serves your application (an App Service, a storage account static site, a virtual machine behind a public IP, a Kubernetes ingress, or a Private Link service), control over the DNS zone for any custom domain you intend to attach, and a clear answer to one question that governs the whole origin contract: what host header does each backend expect.

That last prerequisite deserves a moment because it determines every later choice. App Service upstreams, by default, route incoming requests by the `Host` header to the correct site and serve the matching certificate. If you point Front Door at an App Service and let Front Door send its own endpoint hostname as the host header, the App Service front end does not recognize the host, and you get an error. A storage static website backend behaves differently and generally tolerates the origin hostname as the host header. A plain virtual machine running a single site on a single IP may not care about the host header at all. The point is that you decide this per upstream, and you decide it before you create the backend, because the host header is a property of the backend object.

The order of operations matters more in Front Door than in most Azure services because of the dependency chain. Endpoints reference routes, routes reference origin groups, origin groups reference upstreams, backends carry the host header, and origin groups carry the probe. If you build top down (endpoint, then route) you immediately hit a wall because the route needs an origin group that needs an upstream that needs a confirmed host header you have not decided yet. Build bottom up instead. Confirm the backend is reachable. Create the origin group and its probe. Create the backend with the correct host header. Confirm the upstream reports healthy. Only then create the route. Finally layer on caching, the custom domain and certificate, and the WAF.

### Why does build order change whether the profile works?

Build order changes the outcome because the route is the only object users hit, but it is the last object whose correctness you can confirm. If you create the route before the backend is confirmed healthy on the right host header, the route is live and failing before you have verified the contract behind it. Building bottom up confirms the contract first, so the route is correct the moment it exists.

There is a practical reason to script the whole thing rather than click through the portal, and it is not only repeatability. The portal hides the host header behind an advanced toggle and defaults the probe to a path and protocol that suit a generic upstream rather than yours. When you build through the CLI or Bicep, every field is explicit and visible in the file, which means the two fields that break the origin contract are in front of you instead of behind a collapsed section. The procedure below shows the CLI for clarity and the Bicep equivalent at the end for production use.

One more prerequisite that people skip: decide whether any backend is private. If a backend is behind a Private Link service rather than a public endpoint, Front Door Premium can reach it through a private origin connection, and the setup adds an approval step on the Private Link service. The mechanics of that private path are their own subject, and the [Azure Private Link and private endpoints deep dive](/2023/09/11/azure-private-link-deep-dive/) covers the connection model in full. For the main procedure here, assume public upstreams, and treat the private-origin path as a variation noted where it diverges.

## How do I configure origin groups and health probes?

The origin group is the container that holds your backends and the health probe that decides which of them are eligible to serve. It is the heart of the origin contract, so it is the first object to build after confirming the upstreams themselves work. An origin group answers two questions for Front Door: which backends can handle this traffic, and how do I tell whether each one is currently healthy.

### What does an origin group actually decide?

An origin group decides which backends share a probe and a load-balancing policy, and which of those backends are healthy enough to receive requests right now. Front Door probes every upstream in the group on the same path and interval, marks each backend up or down by the result, and distributes traffic across the healthy ones by priority and weight. The group, not the individual upstream, owns the probe.

Start by creating the profile and the origin group. The profile is the top-level resource and the endpoint is the hostname users reach. With the Azure CLI the sequence reads cleanly:

```bash
# Create the resource group
az group create \
  --name rg-frontdoor-demo \
  --location eastus

# Create the Front Door profile (Standard tier)
az afd profile create \
  --profile-name afd-insightcrunch \
  --resource-group rg-frontdoor-demo \
  --sku Standard_AzureFrontDoor

# Create the endpoint (the global hostname users hit)
az afd endpoint create \
  --endpoint-name shop \
  --profile-name afd-insightcrunch \
  --resource-group rg-frontdoor-demo \
  --enabled-state Enabled
```

With the profile and endpoint in place, create the origin group and define the health probe at the same time. The probe settings here are the ones that most often go wrong, so set them deliberately rather than accepting defaults:

```bash
az afd origin-group create \
  --origin-group-name og-app \
  --profile-name afd-insightcrunch \
  --resource-group rg-frontdoor-demo \
  --probe-request-type GET \
  --probe-protocol Https \
  --probe-path /health \
  --probe-interval-in-seconds 30 \
  --sample-size 4 \
  --successful-samples-required 3 \
  --additional-latency-in-milliseconds 50
```

The `--probe-path` is the field that quietly breaks origin groups. The default in many examples is `/`, and `/` works only if the root of your backend returns a 200. A great many applications return a redirect at the root, or a 403 because the root requires authentication, or a slow render because the root is the heaviest page. Front Door reads any of those as a failing probe and drops the backend. The fix is to give the upstream a dedicated probe endpoint that returns a fast, unauthenticated 200, conventionally `/health` or `/healthz`, and point the probe at it. If you cannot add a health endpoint, choose a real path that you know returns 200 quickly and is not behind authentication.

The `--probe-protocol` has to match what the backend serves on the probe path. If the upstream redirects HTTP to HTTPS, a probe sent over HTTP receives a redirect, not a 200, and the backend is marked down. Probe over HTTPS to a path served over HTTPS. The `--probe-request-type` of `GET` versus `HEAD` matters when the backend treats the two differently; some upstreams do not implement `HEAD` and return a 405, which fails the probe. Start with `GET` unless you have a reason to use `HEAD`.

The sample math controls how aggressive the health decision is. With `--sample-size 4` and `--successful-samples-required 3`, Front Door looks at the last four probe results and needs at least three successes to consider the backend healthy. A 30-second interval means the health state can lag a real outage by up to roughly two minutes in the worst case, which is the trade-off for not flapping upstreams in and out on a single transient blip. Tighten the interval and the required samples only if your backends genuinely need faster failover and can absorb the extra probe traffic.

### Why does a backend drop out even when the app is up?

An upstream drops out when the probe path returns anything other than the success it expects, regardless of whether the application serves real traffic correctly. A probe hitting a root that redirects, a path that needs authentication, or an endpoint served only over the other protocol fails even on a perfectly healthy app, so Front Door marks the backend down and stops sending it requests.

With the origin group and probe defined, add the upstream itself. This is where the host header decision becomes a concrete field, and it is the single most common cause of a 502 on a brand new profile:

```bash
az afd origin create \
  --origin-name app-primary \
  --origin-group-name og-app \
  --profile-name afd-insightcrunch \
  --resource-group rg-frontdoor-demo \
  --host-name myapp.azurewebsites.net \
  --origin-host-header myapp.azurewebsites.net \
  --http-port 80 \
  --https-port 443 \
  --priority 1 \
  --weight 1000 \
  --enabled-state Enabled \
  --enforce-certificate-name-check true
```

Read `--host-name` and `--origin-host-header` as two different ideas that happen to share a value here. The `--host-name` is where Front Door connects, the address it opens a socket to. The `--origin-host-header` is what Front Door puts in the `Host` line of the forwarded request. For an App Service upstream, both are the `azurewebsites.net` hostname because the App Service front end routes by that header and presents the matching certificate. If you set `--host-name` to the App Service address but leave `--origin-host-header` blank, Front Door defaults the header to its own endpoint hostname, the App Service front end does not recognize it, and every request returns a 502. Setting the origin host header to the upstream's own hostname is the fix, and it is the field the checklist flags at step 3.

The `--enforce-certificate-name-check` setting tells Front Door to verify that the certificate the backend presents matches the hostname Front Door connected to. Leave it on for public backends with valid certificates. Turn it off only for upstreams with self-signed or mismatched certificates, and understand that doing so removes a real protection on the edge-to-backend hop.

Priority and weight govern load balancing inside the group. Priority is for failover: Front Door sends traffic to the lowest-priority-number healthy upstreams first and only falls back to higher numbers when the lower ones are all unhealthy. Weight is for distribution among backends at the same priority. A single backend at priority 1 weight 1000 simply receives everything. To add a hot standby in another region, create a second upstream at priority 2, and Front Door uses it only when the priority 1 backends fail their probes. To split traffic across two active upstreams, give them the same priority and proportional weights.

After creating the backend, do not move on until the origin group reports healthy. The portal shows origin health in the origin group view, and the CLI exposes it through metrics. This is the verification for steps 2 through 4 of the checklist, and skipping it is how a broken origin contract reaches production. If the backend shows unhealthy, the cause is in the probe path, the probe protocol, or the host header, in that order of likelihood. Confirm the probe path returns 200 with a direct request that carries the same host header Front Door uses:

```bash
# Simulate the probe with the origin host header Front Door will send
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "Host: myapp.azurewebsites.net" \
  https://myapp.azurewebsites.net/health
```

If that curl returns 200, the origin contract is satisfied and Front Door will mark the upstream healthy. If it returns anything else, you have found the failure before any user did, which is the entire point of building bottom up. You can practice this whole backend-group-and-probe loop, watch the health state flip as you change the probe path, and see the host-header failure reproduce on demand in the [hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), which keeps a tested Front Door command set you can run against a sandbox profile rather than your production one.

## How do route path patterns and matching work?

A route ties everything together. It associates a domain on the endpoint with an origin group, decides which paths it handles through path patterns, sets the forwarding protocol, and turns caching on or off. With the origin contract already confirmed, the route is the object that finally makes the profile serve traffic. The subtlety in routes is path-pattern matching, because the order and specificity of patterns across multiple routes decide which route wins a given request, and the wrong winner sends traffic to the wrong upstream.

### How does Front Door pick which route handles a request?

Front Door matches an incoming request against the path patterns of every route on the endpoint and selects the most specific match, not the first one listed. A request to `/api/orders` matched against a route with `/api/*` and a route with `/*` goes to the `/api/*` route because it is the more specific pattern. Specificity, not declaration order, decides the winner, and exact paths beat wildcards.

Create the route once the origin group is healthy. A single catch-all route is the simplest case:

```bash
az afd route create \
  --route-name route-default \
  --endpoint-name shop \
  --profile-name afd-insightcrunch \
  --resource-group rg-frontdoor-demo \
  --origin-group og-app \
  --supported-protocols Http Https \
  --patterns-to-match "/*" \
  --forwarding-protocol HttpsOnly \
  --https-redirect Enabled \
  --link-to-default-domain Enabled
```

The `--patterns-to-match "/*"` makes this route handle every path. The `--forwarding-protocol HttpsOnly` tells Front Door to forward to the backend over HTTPS regardless of how the user connected, which is what you want for any backend that serves HTTPS. The `--https-redirect Enabled` sends users who arrive over HTTP a redirect to HTTPS at the edge, before the request ever reaches an upstream. The `--link-to-default-domain Enabled` attaches the route to the endpoint's own `azurefd.net` hostname so you can test before a custom domain exists.

Path patterns become interesting the moment you have more than one route. Suppose you want `/api/*` to go to an API origin group and everything else to go to a web origin group. You create two routes on the same endpoint, one with `/api/*` pointing at the API group and one with `/*` pointing at the web group. Front Door evaluates a request to `/api/orders` against both patterns. Both match: `/api/*` matches because the path starts with `/api/`, and `/*` matches because it matches everything. Front Door resolves the tie by specificity and chooses `/api/*`. A request to `/products` matches only `/*`, so it goes to the web group. The model is predictable once you accept that specificity, not order, decides the winner.

The supported path pattern forms are deliberately limited, which keeps matching predictable. You can write an exact path like `/login`, a wildcard prefix like `/api/*`, or a single-segment-and-below wildcard. You cannot write arbitrary regular expressions in the path pattern. This limitation is a feature: complex regex routing is exactly where overlapping rules produce the wrong winner, and Front Door avoids that class of bug by keeping patterns simple and resolving ties by specificity.

### Why does the wrong backend answer when two routes overlap?

The wrong upstream answers when two routes both match a request and the one you did not intend is more specific, or when an exact path you forgot about outranks the wildcard you were relying on. Front Door always serves the most specific match, so a stray `/api/orders` exact route silently outranks your `/api/*` route for that one path, sending it somewhere unexpected.

Overlapping patterns are the first of the real-world failure patterns to plan for. The symptom is that most paths behave correctly but one specific path goes to the wrong place, and it is maddening to debug from the outside because the route list looks reasonable. The cause is almost always a forgotten exact-path route or a too-broad wildcard added later that now outranks an earlier route for some subset of paths. The cure at setup time is discipline: keep the number of routes small, make each pattern as specific as it needs to be and no broader, and write down which route is supposed to win each important path so you can confirm it. When you add a route later, re-check every existing pattern for new overlaps before you ship it.

There is a related field that interacts with patterns: the origin path, sometimes called URL rewrite. By default Front Door forwards the full incoming path to the backend unchanged, so `/api/orders` arrives at the backend as `/api/orders`. If your upstream expects a different prefix, you configure an origin path on the route to rewrite the matched portion. This is flexible and also a source of confusion, because a rewrite that drops or adds a segment changes what reaches the backend and can produce a 404 from the upstream that looks like a routing failure. If you do not need a rewrite, leave the origin path empty and forward paths unchanged, which is the least surprising behavior.

## How do I configure caching on Front Door?

Caching is where Front Door earns much of its value and also where it most often serves the wrong thing. The edge can store a response and return it to later visitors without touching the backend, which cuts latency and offloads the backend, but only some responses are safe to cache, and the line between safe and unsafe is exactly the line that, when crossed, serves stale or private content to the wrong person. Configure caching per route, and configure it conservatively.

### What is safe to cache and what is not?

Static, public, identical-for-everyone responses are safe to cache: images, scripts, stylesheets, fonts, and public pages that do not vary per user. Anything personalized, authenticated, or frequently changing is not safe to cache by default, because the edge would serve one user's response to another or return content that has already changed at the upstream. When in doubt, leave a route uncached.

Caching is enabled on the route. With the CLI you set it when creating or updating the route:

```bash
az afd route update \
  --route-name route-static \
  --endpoint-name shop \
  --profile-name afd-insightcrunch \
  --resource-group rg-frontdoor-demo \
  --enable-caching true \
  --query-string-caching-behavior IgnoreQueryString \
  --patterns-to-match "/assets/*"
```

The `--enable-caching true` flag turns caching on for this route. The `--query-string-caching-behavior` decides whether the query string is part of the cache key. `IgnoreQueryString` caches one copy regardless of the query string, which is right for static assets where `?v=2` is just a cache buster and the bytes are the same. `UseQueryString` caches a separate copy per unique query string, which is right when the query string actually changes the response, such as a thumbnail service that resizes by query parameter. Choosing the wrong behavior here produces the stale-content failure pattern: ignore a query string that matters and you serve the wrong variant; use a query string that does not matter and you shatter the cache into thousands of near-identical copies that never get hit twice.

The more important caching control is the one Front Door does not own: the backend's `Cache-Control` and `Expires` headers. Front Door honors the caching directives the upstream sends. If the backend sends `Cache-Control: no-store` on a response, Front Door does not cache it even on a caching-enabled route, which is the correct and safe default. If the backend sends `Cache-Control: public, max-age=86400`, Front Door caches the response for a day. This means the cleanest way to control caching is to set the right headers at the upstream and let Front Door honor them, rather than fighting the backend from the edge. The route-level toggle decides whether caching is possible; the upstream headers decide what actually gets cached and for how long.

The stale-content failure pattern deserves a concrete description because it is the caching mistake that reaches users. You enable caching on a route that includes a path serving content that changes, the backend does not send a `no-store` directive, and Front Door caches a response that is now wrong. A price updates at the backend and the edge keeps serving the old price for the cache lifetime. A deploy ships new JavaScript and some users keep getting the old bundle because the filename did not change and the query string is ignored. The fix at setup time is twofold: scope caching-enabled routes tightly to paths you are certain are cacheable, and make sure dynamic upstreams send `no-store` or a short `max-age` so even a too-broad route does not cache them. When you need to invalidate immediately, Front Door supports a cache purge, but purging is a recovery action, not a configuration strategy. Build the configuration so you rarely need to purge.

One verification habit closes the loop on caching. Front Door returns an `X-Cache` response header that tells you whether a response was a HIT from the edge or a MISS that went to the backend. Request a cacheable asset twice and confirm the second request shows a HIT. Request a dynamic path and confirm it never shows a cached value. That single header turns caching from a guess into something you can verify per path, which is the verification the checklist names at step 6.

## How do I add a custom domain and certificate?

Users do not connect to `shop.azurefd.net`. They connect to `www.yourcompany.com`, and getting that custom domain onto the endpoint with a valid certificate is the step that makes the profile real. The process has two distinct phases that people conflate: proving you own the domain, and binding it to a route so the certificate takes effect. Both phases have a failure mode that leaves the domain looking present but not working, so treat them as separate verifications.

### Why does my custom domain stay in a pending state?

A custom domain stays pending when the validation DNS record has not been added to your zone, or was added with the wrong name or value, so Front Door cannot confirm you control the domain. Front Door issues a TXT validation token and waits to see it in your DNS. Until that record resolves, the domain sits at pending and no certificate is issued, no matter how correct everything else looks.

Begin by registering the custom domain on the profile and choosing the certificate type. A managed certificate is the right default because Front Door provisions it and, more importantly, renews it automatically before expiry, which removes the most common cause of a sudden site-wide TLS outage: a human forgetting to renew. Bring your own certificate only when policy requires a specific certificate authority or an extended validation certificate that the managed option does not provide.

```bash
# Register the custom domain with a managed certificate
az afd custom-domain create \
  --custom-domain-name www-yourcompany \
  --profile-name afd-insightcrunch \
  --resource-group rg-frontdoor-demo \
  --host-name www.yourcompany.com \
  --minimum-tls-version TLS12 \
  --certificate-type ManagedCertificate
```

Creating the domain returns a validation token. You add that token as a TXT record at `_dnsauth.www` in your DNS zone, and you add the routing record (a CNAME pointing `www` at the endpoint hostname, or an alias record at apex) so traffic actually flows. The validation TXT and the routing CNAME are two different records doing two different jobs, and missing either one produces a different failure. Miss the TXT and the domain stays pending and never gets a certificate. Miss the CNAME and the certificate may issue but no traffic reaches the endpoint because DNS still points elsewhere.

```bash
# Read back the validation token to place in DNS
az afd custom-domain show \
  --custom-domain-name www-yourcompany \
  --profile-name afd-insightcrunch \
  --resource-group rg-frontdoor-demo \
  --query "validationProperties.validationToken"
```

After the TXT record propagates, Front Door validates the domain, the state moves to Approved, and the managed certificate is issued and deployed across the edge. This can take from several minutes to the better part of an hour, and watching the validation state rather than guessing is the verification for step 7. Do not move on while the domain reads pending, because every later symptom will trace back to a domain that never validated.

The second phase, the one people forget, is associating the validated domain to a route. A custom domain that is validated and has a certificate still serves nothing until a route includes it in its list of domains. This is the unvalidated-certificate-versus-unassociated-domain confusion: the certificate exists, the domain is approved, and the site still does not load, because no route claims the domain. Add the domain to the route:

```bash
az afd route update \
  --route-name route-default \
  --endpoint-name shop \
  --profile-name afd-insightcrunch \
  --resource-group rg-frontdoor-demo \
  --custom-domains www-yourcompany
```

Once the domain is on a route, an HTTPS request to `https://www.yourcompany.com` should complete the handshake with the managed certificate and return your upstream's response. Confirm the certificate subject matches the domain and that the chain is trusted. That handshake is the verification for step 8, and it is the moment the profile is genuinely live on the name your users will type. The managed certificate renews itself on its own schedule from here, which is the durable payoff for choosing it over a manually managed certificate that someone has to remember to rotate.

## How do I attach a WAF policy to Front Door?

Front Door can carry a Web Application Firewall at the edge, inspecting requests before they ever reach a backend and blocking the common attack classes that managed rule sets recognize. Attaching a WAF to Front Door is a two-part operation: create the policy with the rules and mode you want, then associate it with the endpoint and the domains it should protect through a security policy. The mode you choose at creation time is the setting that most often surprises people in production.

### Should the WAF start in Detection or Prevention mode?

Start in Detection mode, watch the logs, then switch to Prevention. Detection mode evaluates every rule and logs what it would have blocked without actually blocking anything, so you can find the false positives your real traffic triggers before they turn into blocked customers. Prevention mode enforces the rules and returns a 403 on a match. Switching to Prevention before you have read the detection logs is how a WAF blocks a legitimate checkout flow on launch day.

Create the policy and add a managed rule set. The managed rule set is a curated collection that Microsoft maintains and updates, covering the common web attack categories. Enabling it gives broad coverage without writing individual rules:

```bash
# Create the WAF policy in Detection mode first
az network front-door waf-policy create \
  --name wafInsightCrunch \
  --resource-group rg-frontdoor-demo \
  --sku Premium_AzureFrontDoor \
  --mode Detection \
  --disabled false

# Add the Microsoft managed default rule set
az network front-door waf-policy managed-rules add \
  --policy-name wafInsightCrunch \
  --resource-group rg-frontdoor-demo \
  --type Microsoft_DefaultRuleSet \
  --version 2.1 \
  --action Block
```

The managed default rule set is available on the Premium tier; the Standard tier offers a more limited managed rule capability, which is one of the practical reasons to choose Premium when the WAF matters to you. The same managed-rule and custom-rule model appears on Application Gateway, and if you are deciding between protecting at the regional gateway or at the global edge, the [Application Gateway WAF configuration guide](/2023/05/08/configure-app-gateway-waf/) covers the regional side of the same decision in detail. The two are complementary rather than redundant: edge WAF on Front Door stops attacks before they cross into your network, and a regional WAF protects backends that are reachable by paths other than Front Door.

Exclusions are the second WAF setting that setup guides skip and production demands. A managed rule set occasionally flags a legitimate request because a field in your application happens to look like an attack pattern, for example a rich-text field that contains characters a SQL-injection rule treats as suspicious. The wrong fix is to disable the rule globally, which removes protection everywhere. The right fix is an exclusion that tells the WAF to skip that specific rule for that specific request attribute, leaving the rule active for everything else. You discover which exclusions you need by running in Detection mode and reading which rules fire on known-good traffic, which is the entire reason to start in Detection.

Custom rules sit alongside the managed set for the controls only you know you need: rate limiting a login endpoint, blocking or allowing specific countries, or matching a header your application uses. Custom rules evaluate before managed rules and can allow, block, or rate-limit. A common pairing is a rate-limit custom rule on the authentication path to blunt credential-stuffing, combined with the managed set for the generic attack classes.

Creating the policy does not protect anything until you associate it. On the current Front Door, the association is made through a security policy that binds the WAF policy to the endpoint's domains:

```bash
az afd security-policy create \
  --security-policy-name sp-waf \
  --profile-name afd-insightcrunch \
  --resource-group rg-frontdoor-demo \
  --domains /subscriptions/<sub-id>/resourceGroups/rg-frontdoor-demo/providers/Microsoft.Cdn/profiles/afd-insightcrunch/afdEndpoints/shop \
  --waf-policy /subscriptions/<sub-id>/resourceGroups/rg-frontdoor-demo/providers/Microsoft.Network/frontdoorWebApplicationFirewallPolicies/wafInsightCrunch
```

The wrong-mode failure pattern is worth naming because it is silent in both directions. A policy left in Detection when you intended Prevention logs attacks but blocks none, so you believe you are protected and are not. A policy switched to Prevention before exclusions are tuned blocks legitimate requests, so customers see 403s on normal actions and you believe the WAF is broken when it is doing exactly what it was told. The verification for step 9 is to send one request that should be blocked, such as an obvious injection string in a query parameter, and confirm a 403 in Prevention mode, then send a normal request and confirm it passes. Both checks together prove the WAF is enforcing and not over-blocking.

## The settings the defaults get wrong

Front Door's defaults are tuned for a generic upstream, and a generic backend is not yours. Four defaults cause more first-day failures than anything else, and each one is a single field you can set correctly while you build rather than discover after launch.

The first is the origin host header, already covered but worth repeating because it is the single biggest cause of a new-profile 502. The default sends Front Door's own hostname. App Service and any host-routing upstream reject it. Set the origin host header to the backend's own hostname unless you have confirmed the backend tolerates the default. This one field accounts for a remarkable share of the support questions that begin "my route looks correct but I get a 502."

The second is the probe path. The default of `/` works only if your root returns a fast, unauthenticated 200, and many roots do not. A root that redirects, authenticates, or renders slowly fails the probe and drops the upstream. Point the probe at a dedicated health path that returns 200 quickly. The cost of getting this wrong is the whole origin group going dark while the application is perfectly healthy, which is the most disorienting failure to debug because nothing in the application logs looks wrong.

The third is caching behavior on query strings. The default depends on the route, and the wrong choice produces either stale content or a cache that never hits. Decide per route whether the query string changes the response and set `IgnoreQueryString` or `UseQueryString` to match. Pair that with correct backend cache headers so a dynamic path is never cached even if a broad route would allow it.

The fourth is the WAF mode. A newly created policy in Detection mode protects nothing, and many teams attach a policy and assume protection is on. Detection logs without blocking. Move to Prevention once exclusions are tuned, and verify with a request that should be blocked. The inverse mistake, jumping straight to Prevention without tuning, blocks real traffic, so the correct path is Detection first, read the logs, then Prevention.

A fifth default is quieter but still bites: the minimum TLS version. The default has trended upward over time, but if you inherit an older profile or a bring-your-own-certificate setup, confirm the minimum TLS version is set to a modern floor so the edge does not negotiate a weak protocol with clients. Setting it explicitly to a current minimum removes the ambiguity.

The common thread across all five is that the default is a reasonable guess for an average upstream and a poor fit for a specific one. The procedure in this article sets each of these fields deliberately, which is why building bottom up and scripting the profile pays off: every default that bites is a visible field in the script instead of a collapsed advanced section in the portal you never expanded.

## Verifying the configuration worked

A profile that deploys without error is not a profile that works. Verification is a distinct phase, and it checks the two halves of the route-and-origin-contract rule plus the layers added on top. Run these checks in order, because an earlier failure makes a later check meaningless.

First, confirm origin health. In the portal the origin group view shows each backend as healthy or unhealthy, and the probe success metric shows the rate over time. A healthy upstream here means the probe path and host header are correct. If this check fails, stop and fix the probe before anything else, because no amount of correct routing can send traffic to a backend Front Door considers down.

Second, confirm the path match. Send a request to a known path and confirm it reaches the intended origin group. With multiple routes, send one request to a path that should hit each route and confirm each lands where you expect. This is where overlapping patterns reveal themselves: a path that goes somewhere surprising means a more specific route is winning that you did not account for. The fix is in the patterns, not the upstreams.

Third, confirm the origin contract end to end. The cleanest single check is a request through Front Door compared against a direct request to the backend carrying the origin host header. If the direct request with the correct host header returns 200 and the Front Door request returns 502, the break is between the edge and the backend, which narrows it to the host header, the forwarding protocol, or certificate name enforcement. If both fail, the upstream itself is the problem and Front Door is correctly reporting it.

```bash
# Through Front Door (custom domain)
curl -s -o /dev/null -w "FrontDoor: %{http_code}\n" \
  https://www.yourcompany.com/

# Direct to origin with the host header Front Door sends
curl -s -o /dev/null -w "Origin: %{http_code}\n" \
  -H "Host: myapp.azurewebsites.net" \
  https://myapp.azurewebsites.net/
```

Fourth, confirm caching behavior per path using the `X-Cache` header. A cacheable asset should show a MISS on first request and a HIT on the second. A dynamic path should never show a cached response. If a dynamic path shows a HIT, the route is caching something it should not, and the fix is a tighter route scope or a `no-store` header at the backend.

Fifth, confirm TLS and the custom domain. An HTTPS request to the custom domain should complete the handshake with the managed certificate, and the certificate subject should match the domain. A handshake failure points at an unvalidated domain or an unassociated domain, both covered earlier.

Sixth, confirm the WAF. In Prevention mode, a request carrying an obvious attack pattern should return a 403, and a normal request should pass. Both halves matter: a WAF that blocks everything is as broken as one that blocks nothing. Reading the WAF logs after a few minutes of real traffic also surfaces false positives early, while they are cheap to fix with an exclusion.

## Common misconfigurations and their symptoms

The brief for this article names six recurring cases that engineers report, and each one is a configuration step done slightly wrong rather than a platform fault. Naming the symptom next to the setup step that causes it turns a confusing failure into a quick lookup. These are the patterns the InsightCrunch checklist is built to prevent, and recognizing them by symptom is half the cure.

The first pattern is overlapping path patterns where the wrong route wins. The symptom is that most paths behave correctly and one specific path goes to the wrong upstream or returns the wrong content. The cause is two routes whose patterns both match that path, with the more specific one winning when you expected the other. The setup step that prevents it is keeping patterns minimal and re-checking overlaps every time you add a route. The diagnostic is to send a request to the surprising path and trace which route's pattern is most specific for it.

The second pattern is an origin host header the backend rejects. The symptom is a 502 on every request to an otherwise correct route, often immediately after a brand new profile goes live. The cause is the default host header reaching a backend that routes by host. The setup step that prevents it is setting the origin host header to the upstream's own hostname at origin creation. The diagnostic is the direct curl with the host header: if direct succeeds and Front Door fails, the header is the culprit.

The third pattern is a health probe returning a non-200 so the backend drops. The symptom is intermittent or total 502s with no application errors in the upstream logs, because the application never sees the real traffic, only the probe. The cause is a probe path that redirects, authenticates, or is served on the other protocol. The setup step that prevents it is a dedicated health endpoint returning a fast unauthenticated 200 over the probe protocol. The diagnostic is the origin health view plus a direct request to the probe path.

The fourth pattern is caching serving stale content. The symptom is users seeing old prices, old assets, or old pages after the backend has updated. The cause is a caching-enabled route covering a path that changes, with a backend that does not send a `no-store` directive. The setup step that prevents it is tight route scoping for cacheable paths and correct cache headers at the upstream. The diagnostic is the `X-Cache` header showing HIT on a path that should never cache. A purge clears the immediate problem, but the configuration fix is what stops it recurring.

The fifth pattern is a custom domain certificate that never validates. The symptom is a domain stuck at pending and HTTPS that fails the handshake on the custom name while the `azurefd.net` name works fine. The cause is a missing or wrong validation TXT record, or a domain that validated but was never associated to a route. The setup step that prevents it is placing the validation TXT correctly and then explicitly adding the domain to a route. The diagnostic is the domain validation state and the route's domain list.

The sixth pattern is a WAF attached in the wrong mode. The symptom is either attacks that should be blocked passing through, or legitimate requests returning 403 on normal actions. The cause is Detection when you wanted Prevention, or Prevention before exclusions were tuned. The setup step that prevents it is starting in Detection, reading the logs, tuning exclusions, then switching to Prevention. The diagnostic is a deliberate test request in each direction: one that should block and one that should pass.

These six share a structure worth internalizing. Each is a single configuration decision whose default or careless value produces a symptom that points at the wrong object. The 502 from a host header looks like routing. The dropped backend from a probe looks like an outage. The stale page from caching looks like an application bug. The 403 from a WAF looks like a broken site. The skill is mapping the symptom back to the one configuration field that caused it, and that map is exactly what the checklist encodes. Working through these failures deliberately, reproducing each one and then fixing it, builds the recognition faster than reading about them, and the [hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) lets you trigger each of these six failures against a disposable profile and watch the symptom appear and clear as you change the offending field.

## Making the configuration repeatable as code

A profile clicked together in the portal works until the day you need a second one, or need to recreate the first after someone changes a field nobody documented. Front Door is a clean fit for infrastructure as code precisely because its objects are declarative and their relationships are explicit, and putting the whole profile in a template makes the two fields that break the origin contract permanent, visible, and reviewable. Bicep is the most direct option for an Azure-only stack.

### Why is the host header so much safer in a template?

In a template the host header is a named property in source control, reviewed in a pull request and identical on every deployment, so the field that silently breaks a portal-built profile can never be left blank by accident. The probe path, the caching behavior, and the WAF mode get the same treatment: each becomes an explicit value that a reviewer can see and a diff can catch.

A Bicep module for the core of the profile reads as a direct translation of the steps above. The objects nest in the same dependency order the procedure followed, which is the order that keeps the origin contract correct:

```bicep
param profileName string = 'afd-insightcrunch'
param originHostName string = 'myapp.azurewebsites.net'

resource profile 'Microsoft.Cdn/profiles@2023-05-01' = {
  name: profileName
  location: 'global'
  sku: {
    name: 'Standard_AzureFrontDoor'
  }
}

resource endpoint 'Microsoft.Cdn/profiles/afdEndpoints@2023-05-01' = {
  parent: profile
  name: 'shop'
  location: 'global'
  properties: {
    enabledState: 'Enabled'
  }
}

resource originGroup 'Microsoft.Cdn/profiles/originGroups@2023-05-01' = {
  parent: profile
  name: 'og-app'
  properties: {
    loadBalancingSettings: {
      sampleSize: 4
      successfulSamplesRequired: 3
      additionalLatencyInMilliseconds: 50
    }
    healthProbeSettings: {
      probePath: '/health'
      probeRequestType: 'GET'
      probeProtocol: 'Https'
      probeIntervalInSeconds: 30
    }
  }
}

resource origin 'Microsoft.Cdn/profiles/originGroups/origins@2023-05-01' = {
  parent: originGroup
  name: 'app-primary'
  properties: {
    hostName: originHostName
    originHostHeader: originHostName
    httpPort: 80
    httpsPort: 443
    priority: 1
    weight: 1000
    enabledState: 'Enabled'
    enforceCertificateNameCheck: true
  }
}

resource route 'Microsoft.Cdn/profiles/afdEndpoints/routes@2023-05-01' = {
  parent: endpoint
  name: 'route-default'
  properties: {
    originGroup: {
      id: originGroup.id
    }
    supportedProtocols: [ 'Http', 'Https' ]
    patternsToMatch: [ '/*' ]
    forwardingProtocol: 'HttpsOnly'
    httpsRedirect: 'Enabled'
    linkToDefaultDomain: 'Enabled'
    cacheConfiguration: {
      queryStringCachingBehavior: 'IgnoreQueryString'
    }
  }
}
```

The value of seeing the whole profile in one file is that the dangerous fields are no longer hidden. `originHostHeader` is right there next to `hostName`, set to the same value on purpose, with a parameter so a second environment cannot forget it. `probePath` reads `/health` explicitly rather than defaulting to a root nobody checked. `forwardingProtocol` reads `HttpsOnly` so the edge-to-upstream hop is encrypted. A reviewer scanning the pull request can confirm the origin contract is satisfied without deploying anything, which moves the catch from production to code review.

The same approach extends to the custom domain, the security policy, and the WAF, each as additional resources in the module. Keeping the WAF policy itself in a separate module is sensible because its rules and exclusions change on a different cadence than the routing, and a separate module keeps a routing change from forcing a WAF redeploy. Parameterize the origin hostname, the custom domain, and the WAF mode so the same module produces a Detection-mode profile in staging and a Prevention-mode profile in production from one source of truth.

Drift is the failure mode infrastructure as code is meant to prevent, and Front Door drifts the moment someone fixes a 502 in the portal by changing the host header without updating the template. The discipline that keeps the template authoritative is simple to state and hard to maintain: every change goes through the template, and the portal is read-only for the profile. When that discipline holds, the profile that recreates from the template is identical to the one in production, which means a disaster-recovery rebuild or a new region is a deploy rather than an archaeology project. You can keep tested, parameterized versions of this module and the matching CLI sequence in the [hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) so the starting point is a known-good profile rather than a blank file.

## How does Front Door balance traffic across multiple origins?

Most real profiles end up with more than one backend, either for resilience (a standby in a second region) or for capacity (two active backends sharing load). The origin group governs both behaviors through two fields on each backend, priority and weight, and understanding the interaction between them and the health probe is what turns a multi-origin group from a liability into genuine resilience.

### What is the difference between priority and weight?

Priority is a failover ranking and weight is a distribution ratio. Front Door sends traffic only to the healthy upstreams with the lowest priority number, and among those it splits traffic in proportion to their weights. Higher-priority-number backends receive nothing until every lower-number upstream in the group is marked unhealthy by the probe, at which point traffic shifts to the next tier.

Picture a group with a primary backend in one region at priority 1 and a standby in another region at priority 2. Under normal conditions the probe finds the primary healthy, so all traffic goes there and the standby idles, costing money but serving no requests. When the primary region has an outage, its backend fails the probe, drops out of the eligible set, and Front Door shifts traffic to the priority 2 standby automatically. The failover speed is governed by the probe interval and the sample math: with a 30-second interval and a requirement of three failures out of four samples, the shift takes on the order of a minute and a half in a hard outage. That window is the price of stability, because a tighter setting would flap the upstream in and out on a single slow probe.

An active-active split uses equal priorities and proportional weights instead. Two backends both at priority 1, one with weight 700 and one with weight 300, receive roughly seventy and thirty percent of the traffic for that group while both are healthy. If one fails its probe, the other absorbs everything, because it becomes the only healthy upstream at the top priority. This pattern spreads load and survives the loss of either backend, at the cost of running both warm. The weights let you bias toward a larger backend or shift traffic gradually during a migration by adjusting the ratio over time.

The health probe is the connective tissue under both patterns, which is why the probe configuration earlier in this article matters so much here. Failover and load distribution are only as reliable as the probe that decides who is healthy. A probe pointed at a path that flaps between 200 and 500 will flap backends in and out, sending traffic to a backend that just recovered and yanking it away again. A probe pointed at a path that always returns 200 even when the application is broken will keep a dead backend in rotation, defeating the failover entirely. The probe path should reflect real application health, which is the argument for a health endpoint that checks the dependencies the application actually needs rather than a static page that returns 200 no matter what.

One caution on cross-region failover: the standby upstream has to be genuinely ready to serve, not merely deployed. A standby that has never received traffic may have cold caches, unwarmed connection pools, or a database replica that is read-only until promoted. Failover moves traffic in under two minutes, which is faster than some standbys can warm up, so the first wave of failover traffic can hit a standby that returns errors precisely when you need it most. The configuration fix is to keep the standby warm with a trickle of real or synthetic traffic, or to accept and plan for the warm-up window. The routing layer does its job; the readiness of the backend behind it is a separate responsibility.

## How do the rules engine and request transformations fit routing?

Beyond the route itself, Front Door carries a rules engine that can inspect and modify requests and responses at the edge before forwarding or returning them. The rules engine is optional, and many profiles never need it, but it solves a specific class of problems that would otherwise force changes at the backend: header manipulation, redirects, URL rewrites, and conditional routing based on request attributes. Knowing what it can do prevents the mistake of pushing edge logic down into every upstream.

A rule in the engine is a set of conditions paired with a set of actions. Conditions match on attributes of the request such as the path, the query string, a header, the request method, or the device type. Actions modify the request or response: add or remove a header, rewrite the URL, return a redirect, or override the cache behavior for the matched requests. Rules are grouped into a rule set, and the rule set associates with one or more routes, so the same edge logic applies consistently to every request a route handles.

The most common use is header injection. Security headers such as a strict transport policy or a content security policy belong on every response, and rather than configuring them on each backend separately, a single edge rule adds them to every response a route returns. This centralizes the header policy, keeps it consistent across heterogeneous backends, and means a header change is one edit at the edge rather than a deploy to every backend. The same applies to stripping headers an upstream leaks that should not reach clients.

Redirects at the edge are the second common use and a performance win. A redirect served by the edge never touches a backend, so moving a legacy path to a new location, or forcing a canonical host, happens at the edge in microseconds instead of round-tripping to a backend. A rule that matches the old path and returns a redirect to the new one offloads that entire class of request from the upstreams. The trade-off is that edge redirect logic is one more place routing behavior lives, so document it alongside the routes or it becomes a source of surprise when a path behaves differently than the route table suggests.

URL rewrites in the rules engine overlap with the route's origin path field and can conflict with it, which is the subtlety to watch. The route's origin path rewrites the matched prefix; a rules engine action can rewrite more flexibly based on conditions. Using both on the same path is how a request ends up at an origin path neither you nor the backend expected, producing a 404 from the backend that reads like a routing bug. The guidance is to pick one mechanism for a given rewrite and apply it consistently, rather than layering a route origin path under a rules engine rewrite for the same requests.

The rules engine is genuinely useful and also genuinely a place to overreach. Edge logic is harder to test and observe than upstream logic because it runs in a distributed system you do not control directly. The discipline is to use the engine for cross-cutting concerns that belong at the edge by nature, security headers, canonical redirects, simple rewrites, and to keep application logic at the backend where you can test it normally. A profile whose rules engine encodes business rules becomes a hidden second application that no one remembers to maintain.

## How do I observe routing behavior in production?

A profile that you cannot observe is a profile you cannot trust, because the symptoms that matter, a 502 on a subset of requests, a probe flapping, a cache serving stale content, are invisible until you wire up the logs and metrics that expose them. Front Door emits both, and turning them on during setup rather than during the first incident is what lets you verify the configuration with data instead of hope.

Front Door sends access logs, health probe logs, and WAF logs to a destination you choose, typically a Log Analytics workspace. The access log records every request the edge handled, with the route that matched, the upstream it forwarded to, the response code, the cache result, and the time spent at each hop. That last detail is the one that resolves the route-and-origin-contract questions definitively: a log entry showing the route matched and the backend returned a 502 confirms the break is at the upstream, not the routing, in a way that guessing never can. Enable diagnostic settings on the profile and route the access log to a workspace as part of the build, not as a follow-up.

The metrics complement the logs with the aggregate view. The origin health metric shows the probe success rate per backend over time, which surfaces a flapping probe as a sawtooth pattern long before it causes a visible outage. The request count and response status metrics, split by upstream and by response code, show a rising 502 rate the moment a host header or probe breaks. The cache hit ratio metric shows whether caching is doing its job; a hit ratio near zero on a route you enabled caching for means the cache key or the backend headers are defeating it.

The single most useful query during an incident is one that joins the route and the backend response code, because it answers the route-and-origin-contract question directly. Filter the access log to the failing path, group by the matched route and the backend status, and the result tells you whether the wrong route is winning or the right upstream is failing. From there the fix is mechanical: a wrong-route result sends you to the path patterns, a failing-backend result sends you to the host header and probe.

Alerting closes the loop. An alert on a rising 502 rate, an alert on origin health dropping below a threshold, and an alert on a sudden change in cache hit ratio turn the three most common configuration failures into a notification rather than a customer complaint. Set these during the build so the profile is observable from its first day of traffic, when configuration mistakes are most likely to surface. Observability is not a separate project; it is the verification step extended over time.

## What changes when the backend is private?

Everything above assumes a public upstream that Front Door reaches over the internet. When a backend must not have a public endpoint, Front Door Premium can connect to it privately through a Private Link service, and the routing model stays the same while the connection underneath changes. The route, the path patterns, the caching, and the WAF behave identically; only the path from edge to upstream becomes private.

The mechanism is a private origin: instead of a public hostname, the backend references a Private Link service, and Front Door establishes a private connection to it. The connection requires an approval on the Private Link service side, because the owner of the private resource must consent to the edge connecting to it. That approval step is the new gotcha in the private path: a private origin that looks configured but sits in a pending approval state cannot receive traffic, and the symptom is the backend never becoming healthy. Approving the private endpoint connection on the Private Link service clears it.

The host header logic does not disappear in the private case; it still applies, because the origin behind the Private Link service may still route by host. The probe still runs, over the private connection, and the probe path and protocol rules are unchanged. What changes is purely the network path, which means the origin contract you confirmed for a public upstream transfers directly, with the added approval step layered on top. The full model of Private Link, the service, the endpoint, and the approval flow, is its own substantial topic, and the [Azure Private Link and private endpoints deep dive](/2023/09/11/azure-private-link-deep-dive/) covers the connection mechanics that this private-origin path depends on.

The decision to use a private origin is a security one, not a routing one. It removes the public endpoint from the backend entirely, so the only way to reach the application is through Front Door, which means the edge WAF is no longer one of several entry points but the only one. That is a strong posture, and it is the reason a private origin pairs naturally with a strict edge WAF policy: when Front Door is the sole path to the upstream, the protection at the edge protects everything.

## A worked end-to-end setup for a real application

Abstract steps are easier to follow when anchored to a concrete shape, so here is a full profile for a common application layout: a web front end, a separate API, and a bucket of static assets, all behind one custom domain with a managed certificate and an edge WAF. Walking it end to end shows how the individual steps compose and where the origin contract has to hold at each junction.

The application has three backends. The web front end runs on an App Service at `web-app.azurewebsites.net`. The API runs on a second App Service at `api-app.azurewebsites.net`. The static assets live in a storage account static website at `assets.z13.web.core.windows.net`. All three should be reachable only through Front Door on the domain `www.example.com`, with the API under `/api/*`, the assets under `/assets/*`, and everything else served by the web front end.

Start at the bottom, with the origin contract for each backend. The two App Service backends route by host header, so each gets its own origin group with its host header set to its own `azurewebsites.net` hostname and a probe pointed at a `/health` endpoint the application serves with a fast 200. The storage upstream tolerates its own hostname as the host header and serves a 200 at its root, so its probe can point at a known asset path or the root, whichever returns 200 reliably. Three origin groups, three probes, three host headers decided deliberately. Confirm all three report healthy before any route exists, using the direct curl with the matching host header for each.

With the contract confirmed, build the routes on a single endpoint. The most specific patterns come first in your thinking even though Front Door resolves by specificity automatically. The API route matches `/api/*` and points at the API origin group. The assets route matches `/assets/*`, points at the storage origin group, and enables caching with `IgnoreQueryString` because the assets are static and versioned by filename. The default route matches `/*`, points at the web origin group, and leaves caching off because the web pages are dynamic. A request to `/api/orders` matches both `/api/*` and `/*`, and Front Door serves the more specific API route. A request to `/assets/logo.png` matches both `/assets/*` and `/*`, and the assets route wins. A request to `/dashboard` matches only `/*` and goes to the web front end. The behavior is predictable because the patterns are specific and non-redundant.

Now the domain and certificate. Register `www.example.com` with a managed certificate, place the validation TXT record, and wait for the state to reach Approved. Add the routing CNAME pointing `www` at the endpoint hostname. Then, the step people forget, associate the validated domain with all three routes, because a domain serves nothing on a route that does not list it. Once the domain is on every route, `https://www.example.com/`, `https://www.example.com/api/health`, and `https://www.example.com/assets/logo.png` all complete the TLS handshake with the managed certificate and reach their respective backends.

Finally the WAF. Create one policy, add the managed default rule set, and start in Detection mode. Associate it with the endpoint through a security policy so it covers all three routes. Run real traffic for a day, read the WAF logs, and add exclusions for any rule that fires on legitimate requests, most likely on the API where structured payloads can resemble attack patterns. Once the exclusions are tuned, switch the policy to Prevention. Verify with a deliberate injection string that should return a 403 and a normal request that should pass, on each of the three paths.

The whole profile is then verifiable against the route-and-origin-contract rule at every junction: each route matched the path you intended, and each origin behind it satisfied its host header and probe. When a 502 appears later, the diagnosis is immediate, because you know exactly which origin contract to check for the path that failed. That is the payoff of building bottom up and confirming the contract before the route: the profile is not only working, it is debuggable.

## Closing verdict

Front Door routing rewards a particular discipline and punishes its absence in a particular way. The discipline is to treat the origin contract as part of the routing setup rather than a separate concern, and to build the profile bottom up so that contract is confirmed before any route depends on it. The punishment for skipping that discipline is the 502 that looks like a routing fault and is in fact a backend fault, the failure mode that sends people in circles editing routes that were correct all along.

The route-and-origin-contract rule is the one idea to carry away. A route is a path match plus an origin contract. The path match is visible and easy. The origin contract, the host header the upstream expects and the probe path it answers with a 200, is the part that hides and the part that breaks. Get those two fields right at origin creation and the route works on its first request. Get them wrong and no amount of correct routing saves you. Every confusing Front Door failure resolves faster once you ask which half of the rule broke before touching anything.

The rest of the setup layers cleanly on a sound contract. Path patterns resolve by specificity, so keep them minimal and re-check overlaps when you add a route. Caching helps and harms in equal measure, so scope it tightly and let backend headers do the deciding. A managed certificate removes the renewal time bomb, so prefer it unless policy forbids it, and remember that a validated domain still serves nothing until a route claims it. The WAF protects only in Prevention mode, so start in Detection, tune exclusions, then enforce. And put the whole thing in a template, because the fields that break the contract are exactly the fields a code review can catch and a portal click cannot.

A profile built this way is more than working. It is debuggable, repeatable, and observable, which means the next incident is a quick lookup against the rule rather than a rebuild. That is the difference between a Front Door profile you maintain and one that maintains a low-grade anxiety in whoever owns it. Build the contract first, and the routing takes care of itself.

## Frequently asked questions

**How do I set up Front Door routing rules from scratch?**
Create the profile and endpoint, then build bottom up. Make an origin group with a health probe pointed at a path that returns a fast 200, add the upstream with its host header set to the value the backend expects, and confirm the backend reports healthy. Only then create the route with its path pattern and forwarding protocol. Building the origin contract before the route is what keeps the first request from returning a 502.

**How do I configure origin groups and health probes correctly?**
An origin group holds the upstreams and owns the probe. Set the probe path to a dedicated health endpoint, not the root, because roots often redirect or authenticate and fail the probe. Match the probe protocol to what the backend serves, usually HTTPS. The sample size and required successes control how fast an upstream is marked down, trading failover speed against stability. Confirm the group reports healthy before adding any route.

**How do route path patterns and matching work?**
Front Door matches a request against every route's path pattern and serves the most specific match, not the first listed. A request to `/api/orders` goes to a `/api/*` route over a `/*` route because the former is more specific. Patterns are limited to exact paths and prefix wildcards, which keeps matching predictable. The wrong backend answering almost always means a more specific route is winning a path you did not expect.

**How do I configure caching on Front Door?**
Enable caching per route and choose the query-string behavior to match whether the query string changes the response. Use `IgnoreQueryString` for static assets and `UseQueryString` when the query string selects a real variant. Front Door honors the backend's `Cache-Control` headers, so the cleanest control is correct headers at the upstream: send `no-store` on dynamic responses so a broad route cannot cache them. Verify with the `X-Cache` header showing HIT or MISS per path.

**How do I add a custom domain and certificate to Front Door?**
Register the domain on the profile with a managed certificate, place the validation TXT record so the domain reaches Approved, and add the routing CNAME so traffic flows. Then associate the validated domain with a route, because a domain serves nothing on a route that does not list it. A managed certificate renews automatically, which removes the most common cause of a sudden TLS outage. Verify the HTTPS handshake presents the managed certificate on the custom name.

**Why does my Front Door route return a 502 when it looks correct?**
Because the route matched but the origin contract broke. The two usual causes are an origin host header the backend rejects, often the default reaching an App Service that routes by host, and a health probe failing so the upstream is marked down. Confirm with a direct request to the backend carrying the host header Front Door sends: if direct succeeds and Front Door fails, the host header or forwarding protocol is the culprit, not the routing.

**How do I attach a WAF policy to Front Door?**
Create a WAF policy, add the Microsoft managed default rule set, and start in Detection mode. Associate it with the endpoint through a security policy so it covers the domains you want protected. Run real traffic, read the logs, add exclusions for rules that fire on legitimate requests, then switch to Prevention. A policy in Detection blocks nothing, and a policy in Prevention before tuning blocks real users, so the order matters.

**Should the Front Door WAF run in Detection or Prevention mode?**
Detection first, then Prevention. Detection evaluates every rule and logs what it would block without blocking anything, which lets you find false positives in your real traffic before they become blocked customers. Once you have read the detection logs and added exclusions for the rules that fire on legitimate requests, switch to Prevention so the rules actually enforce. Verify both directions: a malicious request blocks, a normal request passes.

**Why does a backend show unhealthy when the application is running fine?**
Because the probe is hitting something other than your real traffic. A probe pointed at a root that redirects, a path that needs authentication, or an endpoint served only on the other protocol returns a non-200, and Front Door marks the upstream down even though the app serves real requests correctly. Point the probe at a dedicated unauthenticated health path that returns a fast 200 over the probe protocol, and the backend recovers.

**Can I route different paths to different backends?**
Yes. Create multiple routes on the same endpoint, each with its own path pattern and origin group. Put the API under `/api/*` pointing at the API origin group, static assets under `/assets/*` pointing at the storage origin group, and everything else under `/*` pointing at the web origin group. Front Door resolves overlaps by specificity, so `/api/orders` goes to the API route and `/dashboard` goes to the default route, predictably.

**How fast does Front Door fail over to a standby upstream?**
The failover speed depends on the probe interval and the sample math. With a 30-second interval and a requirement of three failures out of four samples, a hard outage shifts traffic to a higher-priority-number backend in roughly a minute and a half. Tightening the interval and required samples speeds failover but risks flapping backends on transient blips. The standby must also be warm enough to absorb the first wave, or it returns errors when it takes over.

**What is the difference between origin host name and origin host header?**
The host name is where Front Door connects, the address it opens a socket to. The host header is the `Host` value Front Door puts in the forwarded request. For an App Service they are the same `azurewebsites.net` value because the App Service front end routes by that header. Setting the host name correctly but leaving the host header at its default sends Front Door's own hostname to the upstream, which a host-routing backend rejects with an error that surfaces as a 502.

**Why is my custom domain stuck in a pending state?**
The validation DNS record is missing or wrong. Front Door issues a TXT token that you add at `_dnsauth.<subdomain>` in your zone, and it waits to see that record before approving the domain and issuing a certificate. Until the TXT resolves, the domain stays pending. Note that the validation TXT and the routing CNAME are two separate records: the TXT proves ownership, the CNAME directs traffic, and missing either produces a different failure.

**Does Front Door cache dynamic or authenticated content by mistake?**
Only if you let it. Caching is off unless you enable it per route, and even on a caching route Front Door honors the upstream's `Cache-Control` headers, so a `no-store` directive prevents caching. The stale-content failure happens when a caching route covers a dynamic path and the backend omits the directive. Scope caching routes tightly and send `no-store` or a short `max-age` on dynamic responses so the edge never serves them stale.

**How do I make my Front Door configuration repeatable?**
Put the whole profile in a Bicep module or equivalent template, with the origin host header and probe path as explicit, parameterized properties. A template makes the two fields that break the origin contract visible in source control, catchable in code review, and identical across environments. Keep the WAF in a separate module since its rules change on a different cadence, and treat the portal as read-only so the template stays the authoritative source.

**Do I need Premium or is Standard enough for routing?**
Standard handles routing, origin groups, health probes, path patterns, caching, custom domains, and managed certificates, which covers most setups. Premium adds the full managed WAF rule set, private origin connections through Private Link, and bot protection. If your security posture needs the managed rule set or your backends must be private with no public endpoint, choose Premium. If you only need global routing and caching with a basic security policy, Standard is sufficient.

**How do I observe what my routing is doing in production?**
Enable diagnostic settings on the profile and send the access log, health probe log, and WAF log to a Log Analytics workspace during setup. The access log records the matched route, the upstream, the response code, and the cache result per request, which resolves route-versus-backend questions directly. Watch the origin health and 502-rate metrics, and alert on a rising 502 rate or dropping origin health so configuration failures become notifications rather than complaints.

**Can Front Door reach an upstream that has no public endpoint?**
Yes, on the Premium tier, through a private origin that connects to a Private Link service. The routing, caching, and WAF behave identically; only the edge-to-origin path becomes private. The new step is approving the private endpoint connection on the Private Link service side, and a private origin stuck in pending approval never becomes healthy. The host header and probe rules still apply over the private connection, so the origin contract transfers directly from the public case.

## How do I change a live profile without downtime?

The first setup is the easy part. Changing a profile that already carries production traffic is where caution earns its keep, because the same edits that are harmless on an empty profile can break thousands of in-flight requests on a busy one. The good news is that the dependency model that makes setup predictable also makes safe change predictable, as long as you respect the order and verify each edit against the route-and-origin-contract rule before moving on.

The safest pattern for adding a new backend to an existing group is to add it as a low-priority member first, confirm it reports healthy through the probe, and only then raise its priority or weight to take traffic. A new member that joins at the same priority as the active one immediately receives a share of live requests, so if its contract is wrong, real users feel it. Joining at a lower priority means the member sits idle and probed until you have proof it is healthy, at which point promoting it is a single field change with a known-good target.

Changing a path pattern on a live route is the edit most likely to surprise, because a pattern change silently re-sorts which route wins for some set of paths. Before editing a pattern, list every existing route and write down which one currently wins each important path, then make the change and confirm the winners are still what you intend. A pattern that looks like a small tweak can hand a whole path prefix to a different backend, and the symptom appears only for the affected paths, which makes it hard to spot after the fact. Verify the path matches explicitly after any pattern edit.

Certificate and domain changes deserve their own caution. Removing a domain from a route stops serving that name immediately, so confirm no traffic depends on it first. Rotating a bring-your-own certificate has a window where the new certificate must be in place before the old one expires, which is exactly the failure a managed certificate avoids by renewing itself. When the change is large, such as moving a domain to a new endpoint, stage it by validating the domain on the new target before cutting DNS over, so the new path is proven before any user reaches it.

The discipline that ties all of this together is the same one that governs the initial build: change one object at a time, verify it against the rule, and keep the template authoritative so the live state and the source agree. A change made in the portal to put out a fire is a change the template does not know about, and the next deploy from that template will quietly undo the fix. The slower path of editing the template and deploying is the path that does not surprise you a month later.

## What does a secure edge-to-origin posture look like?

Routing correctness and security posture are different concerns that share the same objects, and a profile that routes perfectly can still be exposed if the security choices are loose. A few decisions, made at setup, turn the edge from a routing layer into a protective one.

The forwarding protocol from the edge to the backend should be HTTPS, set through the route's forwarding protocol field, so the hop between the edge and the backend is encrypted rather than carried in clear text across whatever network sits between them. Pair that with certificate name enforcement on the backend so the edge verifies the certificate the backend presents matches the host it connected to, which closes the gap where a misrouted or impersonated backend could intercept traffic. Both fields exist for this reason, and turning them off should be a deliberate, documented exception rather than a default left unexamined.

The minimum TLS version on the client side, set on the custom domain, controls the weakest protocol the edge will negotiate with a visitor. Pinning it to a current floor refuses the outdated protocol versions that carry known weaknesses, and because the edge terminates TLS for every visitor, that one setting raises the floor for the entire audience at once. Set it explicitly rather than trusting the inherited default, especially on a profile that has been around for a while.

The WAF is the active half of the posture, and its value depends entirely on running in Prevention with tuned exclusions, as covered earlier. A profile that locks down the transport but leaves the WAF in Detection has armored the doors and left the alarm in test mode. The strongest posture combines a private backend with no public endpoint, an edge WAF in Prevention, encrypted forwarding with name enforcement, and a modern TLS floor, so the only path to the application runs through a protected, encrypted edge. Each piece is a single setting, and together they make the difference between a profile that merely works and one that is safe to put in front of something that matters.


**Why does forwarding HTTP to an HTTPS-only backend break the probe and the route?**
Because the backend answers an HTTP request with a redirect to HTTPS, and both the health probe and the route read that redirect as a failure rather than a success. The probe expects a 200 on the probe path, and a 301 or 302 fails it, dropping the backend. Set the probe protocol to HTTPS and the route forwarding protocol to HTTPS-only so every hop to the backend uses the protocol the backend actually serves, and the redirect never enters the picture.

**How do I roll out a routing change safely on a busy profile?**
Change one object at a time and verify each against the route-and-origin-contract rule before the next. Add a new backend at low priority, confirm it probes healthy, then promote it. Before editing a path pattern, record which route wins each important path so you can confirm the winners afterward. Keep the template authoritative so a portal hotfix does not get undone by the next deploy, and stage domain moves by validating on the new target before cutting DNS over.
