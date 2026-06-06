---
layout: post
title: "Configure Application Gateway WAF the Right Way"
page_title: "Configure Application Gateway WAF: Detection vs Prevention Mode, OWASP Rule Sets, Exclusions, and Custom Rules"
date: 2023-05-08
categories: ["Technology"]
tags: ["Azure", "Application Gateway", "WAF", "Security", "Networking", "Cloud Computing"]
excerpt: "Configure Application Gateway WAF the safe way: start in detection mode, tune exclusions, add custom rules, then switch to prevention without breaking your app."
image: "/assets/images/blog/blog-67.webp"
reading_time: 62
author: "ryan-walsh"
last_updated: 2023-05-08
lang: en
---
A web application firewall that blocks your own customers is worse than no firewall at all, because it fails loudly and unpredictably while still leaving you convinced you are protected. The fastest way to reach that state is to enable an Application Gateway WAF in prevention mode on day one, point production traffic at it, and wait for the support tickets. The slower and far better way is the one this guide walks through end to end: stand the policy up in detection mode, watch what it would have blocked, carve out the legitimate traffic that trips the managed rules, layer in the custom rules your app actually needs, and only then flip the switch to prevention. Get that sequence right and the firewall protects the application without anyone noticing it exists. Get it wrong and you spend a week explaining why uploads, API calls, and search queries started failing for no reason a developer can see in the application logs.

The reason this trips up so many teams is that the WAF lives at a layer most application engineers rarely think about. It inspects HTTP requests before your code ever runs, matches them against hundreds of pattern rules written to catch SQL injection, cross-site scripting, protocol violations, and a long tail of attack signatures, and either logs or blocks anything that matches. When one of those rules fires on a perfectly normal request, the application returns a 403 that has nothing to do with your authentication or authorization logic, and the stack trace you would normally reach for simply is not there. Configuring the WAF correctly means understanding where it sits, how its rules decide, and how to tune it so it stops attackers without ever touching a real user.

![Application Gateway WAF configuration](/assets/images/blog/blog-67.webp)

This guide is built around one organizing idea, the detect-then-prevent rule, and one reusable deliverable, the InsightCrunch WAF setup checklist. By the end you will be able to choose detection versus prevention mode on purpose, pick the right managed rule set and version, tune exclusions so legitimate traffic survives, write custom rules for rate limiting and geographic or address matching, associate the policy correctly, and confirm in the logs what the firewall actually did rather than guessing. Every command shown has been run against a real gateway, and every claim about behavior has been verified rather than assumed, because a security control you cannot reason about is one you cannot trust.

## What an Application Gateway WAF Actually Is and What It Protects

Before any configuration makes sense, you need an accurate mental model of where the firewall lives and what it can and cannot see. Azure Application Gateway is a regional layer-7 load balancer and reverse proxy. It terminates the client connection, reads the full HTTP request including the method, the path, the headers, the query string, and the body, and then forwards a request to one of your backend servers. The web application firewall is an inspection stage bolted onto that proxy. Because the gateway already has the decoded request in hand, the firewall can examine the parts of a request that a layer-4 load balancer never sees, which is exactly why it can catch application-layer attacks that a network firewall or a simple port filter would pass straight through.

That position carries a consequence worth stating plainly. The WAF inspects requests on their way in, north to south, from the public internet toward your application. It does not inspect traffic between your backend servers, it does not inspect outbound responses for data exfiltration by default, and it cannot see anything that arrives over a connection that bypasses the gateway. If a client can reach your backend directly, perhaps because a public IP was left on a virtual machine or a network security group rule is too broad, the firewall protects nothing on that path. The first architectural rule of running a WAF is therefore to make the gateway the only door into the application, and the related failure mode of a misrouted or misconfigured gateway is covered in depth in our guide to [fixing Application Gateway 502 errors](/2022/12/12/fix-application-gateway-502/), because a backend that the gateway cannot reach and a backend that bypasses the gateway are two sides of the same routing question.

### What is the difference between the WAF and a network security group?

A network security group filters by address, port, and protocol at layers 3 and 4, so it can allow or deny a connection but cannot read what the connection carries. The WAF operates at layer 7, reading the decoded HTTP request, so it can block a single malicious request on an otherwise permitted connection. The two are complementary controls, not substitutes for each other.

The firewall enforces its decisions through rules, and the rules come from two sources. The first is a managed rule set that Microsoft maintains, derived from the OWASP Core Rule Set, which encodes hundreds of signatures for the common attack classes. The second is your own custom rules, which you write to express policy the managed set knows nothing about, such as throttling an abusive client or refusing traffic from a country you do not serve. Understanding that division matters because the two sources are tuned in completely different ways. You tame the managed rules by adding exclusions and overrides when they misfire, and you extend the firewall's behavior by adding custom rules. Confusing the two is a common source of wasted effort, because people try to write a custom rule to undo a managed signature when an exclusion is the correct tool, or they disable a whole managed rule group when a narrow exclusion would have done the job without opening a hole.

There is also a packaging distinction that has changed over the life of the product and still confuses people who learned the older model. The modern and recommended approach uses a standalone WAF policy resource that you create independently and then associate with one or more Application Gateways, with listeners, or even with specific URI paths. The legacy approach kept the WAF configuration inside the gateway resource itself. Throughout this guide the WAF policy is a separate resource, because that model supports per-site and per-path policies, is easier to manage as code, and is where all current development goes. If you are working with the layer choices around the gateway itself, including when an Application Gateway is the right edge component versus a different service, the trade-offs are laid out in our comparison of [load balancer versus Application Gateway](/2023/10/02/load-balancer-vs-app-gateway/).

## The Detect-Then-Prevent Rule, and Why Mode Sequence Decides Everything

Here is the single most important idea in this entire guide, the one that separates a smooth rollout from a painful one. A WAF policy runs in one of two modes. In detection mode the firewall evaluates every request against every rule, writes a log entry for anything that matches, and then lets the request through unchanged. In prevention mode the firewall evaluates the same rules and actively blocks anything that matches, typically returning a 403 to the client. Detection mode observes. Prevention mode enforces. The detect-then-prevent rule states that you always run a new policy in detection mode long enough to learn its false positives, tune exclusions for the legitimate traffic that trips the rules, and only then promote it to prevention. Going straight to prevention is the usual cause of a WAF that breaks the application, and it is entirely avoidable.

The reasoning behind the rule is grounded in how managed rules behave on real traffic. The OWASP-derived signatures are deliberately broad, because an attacker who can predict exactly what a firewall ignores can craft around it. Broad signatures catch attacks, and they also catch a steady trickle of perfectly normal requests that happen to look like attacks. A base64 blob in a request body can resemble an encoded payload. A JSON document with SQL keywords in a free-text field can resemble injection. A long query string can trip a request-size check. None of these are attacks, but the firewall cannot know that until you tell it. Detection mode is how you find every one of these collisions on your actual traffic before any of them costs a user a failed request.

### Should a WAF run in detection or prevention mode?

Run a brand-new policy in detection mode first, for long enough to cover your real traffic patterns including peak load, batch jobs, and any monthly or quarterly workflows. Review the logged matches, build exclusions for the legitimate ones, then switch to prevention mode. Detection mode never blocks, so it is safe to enable in production while you tune.

How long is long enough in detection mode depends entirely on your traffic, and the honest answer is that calendar time matters less than coverage. You are waiting to observe every kind of legitimate request your application produces, and some of those appear only during specific workflows. A reporting export that runs on the first of the month, a bulk import an administrator triggers rarely, an integration partner that calls a particular endpoint with an unusual payload, all of these can trip a rule the first time they run in prevention mode if you never saw them during detection. A reasonable default is to hold a new policy in detection mode for at least one full business cycle of your application, which for many teams means a couple of weeks, and longer if you know there are infrequent but important traffic patterns you have not yet exercised. The cost of waiting is small because detection mode is already protecting nothing by blocking, but it is already telling you everything by logging.

A second, subtler point is that mode interacts with rule-set tuning, and this is where teams who rush get burned twice. Suppose you enable prevention mode immediately, a legitimate upload gets blocked, and the on-call engineer, under pressure, disables the WAF entirely to restore service. Now the application works, the incident closes, and the firewall is off, often permanently, because no one circles back to re-enable a control that caused an outage. The detect-then-prevent sequence prevents this failure cascade by surfacing the upload problem in the logs, in detection mode, where it costs nothing, so you can write the targeted exclusion before the rule ever blocks a real request. The counter-reading worth engaging directly is the temptation to treat the WAF as binary, on or off, when the actual tool you reach for after a false positive is almost always a narrow exclusion, not the off switch.

## Prerequisites and the Correct Order of Operations

Configuration goes wrong most often not because a single step is hard but because the steps are done in the wrong order, leaving the gateway in a half-configured state that produces confusing errors. The correct order of operations for an Application Gateway WAF is to confirm the gateway prerequisites, create the WAF policy as a standalone resource in detection mode, attach the managed rule set at a known version, associate the policy at the right scope, send representative traffic, read the logs, build exclusions and custom rules, and finally promote to prevention. Each step depends on the one before it, and skipping ahead is what produces a policy that blocks the wrong things or protects nothing.

Start with the gateway itself, because the WAF rides on top of it and inherits its constraints. The web application firewall requires a WAF-capable SKU. On the v2 generation that means the WAF_v2 SKU rather than Standard_v2, and the SKU is fixed at creation for the firewall capability, so a Standard_v2 gateway cannot simply have a WAF switched on without moving to the WAF_v2 tier. Confirm which SKU your gateway runs before you plan anything else, because the entire approach differs if you first need to provision or migrate to a WAF-capable gateway. You also need diagnostic logging configured and flowing to a destination you can query, because the WAF is close to useless without its logs. In detection mode the logs are the only output the firewall produces, and in prevention mode they are how you confirm what was blocked and why. Send the firewall log category to a Log Analytics workspace so you can run queries against it, which is the verification backbone for everything that follows.

You also need to settle the scope question before you create anything, because the WAF policy can be associated at three levels and the choice shapes how you tune it. A policy can apply to an entire Application Gateway, so every listener and every site behind it inherits the same rules. A policy can apply to a specific listener, which lets one gateway host several sites each with its own firewall posture. And a policy can apply to a specific URI path through a path-based routing rule, which lets you, for example, run stricter rules on an administrative path than on a public marketing path. Most teams begin with a gateway-wide policy for simplicity and move to per-listener or per-path policies as their tuning needs diverge. Decide your starting scope now, because exclusions and custom rules are written into the policy, and a policy attached at the wrong scope tunes the wrong traffic.

### What are the prerequisites for enabling Application Gateway WAF?

You need an Application Gateway on a WAF-capable SKU such as WAF_v2, diagnostic logging routed to a queryable destination like a Log Analytics workspace, a decision on association scope (gateway, listener, or path), and confidence that the gateway is the only network path into the backend so the firewall cannot be bypassed.

One prerequisite is easy to overlook and expensive to miss, which is making sure the gateway is genuinely the only route to the backend. The firewall protects only the traffic that passes through it, so if a backend virtual machine still has a public IP, or a network security group permits inbound traffic from outside the gateway's subnet, attackers can knock on the backend directly and the WAF never sees them. Lock the backend so it accepts traffic only from the gateway's subnet, remove any stray public addresses, and treat that lockdown as part of standing up the firewall rather than a separate hardening task. The model of how traffic flows through an Azure virtual network, including subnets, routing, and the default behaviors that surprise people, is covered thoroughly in our [Azure networking fundamentals](/2023/08/28/azure-networking-fundamentals/) guide, and a WAF on top of a leaky network model is a lock on a door next to an open window.

## The InsightCrunch WAF Setup Checklist

Every configuration article in this series ships a findable artifact you can keep, and for the WAF that artifact is the InsightCrunch WAF setup checklist. It compresses the entire procedure into the seven steps that matter, each paired with the one mistake that most often derails it. Work down the list in order, and do not promote to prevention until every prior step is genuinely complete rather than nominally done.

| Step | What you do | The gotcha that derails it |
|------|-------------|----------------------------|
| 1. Choose the mode | Create the policy in detection mode | Starting in prevention mode blocks real traffic before you have seen it |
| 2. Pick the rule set and version | Attach a managed rule set and pin its version | Leaving the version implicit means a later upgrade silently changes what is blocked |
| 3. Route the logs | Send the firewall log category to Log Analytics | Without logs you cannot see what detection mode found or what prevention mode blocked |
| 4. Tune exclusions | Add exclusions for the legitimate traffic that trips rules | A broad exclusion disables protection; scope it to the field, the rule, and the path |
| 5. Add custom rules | Write rules for rate limiting, geo, and IP policy | Custom rules run before managed rules, so a misordered allow rule can skip inspection |
| 6. Associate the policy | Attach the policy at the gateway, listener, or path scope | Attaching at the wrong scope tunes the wrong traffic and protects the wrong site |
| 7. Verify and promote | Confirm behavior in the logs, then switch to prevention | Promoting without reading the logs ships your false positives straight to users |

The checklist is deliberately ordered so that every protective decision is made before the firewall is allowed to block anything. Steps one through six all happen while the policy is in detection mode, where mistakes are visible but harmless, and step seven is the only one that changes the firewall from an observer into an enforcer. If you find yourself promoting to prevention with unanswered questions about what the logs showed, stop and return to step four, because an unread log is an untuned exclusion waiting to become an outage.

## Step by Step: Building the WAF Policy in Detection Mode

With the prerequisites settled, the build itself is a short sequence of resource operations. The commands below use the Azure CLI because it reads cleanly and translates directly to scripts and pipelines, but every operation maps to the portal and to PowerShell as well. The guiding principle is that you create everything in detection mode first, so nothing you do during this phase can block a real request.

Begin by creating the standalone WAF policy. A fresh policy needs a name, a resource group, and an initial mode. You set the mode to Detection and the state to Enabled so the firewall starts evaluating and logging immediately without blocking.

```bash
az network application-gateway waf-policy create \
  --name waf-prod-policy \
  --resource-group rg-edge-prod \
  --location eastus

# Set the policy settings: detection mode, enabled, with request body inspection on
az network application-gateway waf-policy policy-setting update \
  --policy-name waf-prod-policy \
  --resource-group rg-edge-prod \
  --mode Detection \
  --state Enabled \
  --request-body-check true \
  --max-request-body-size-in-kb 128 \
  --file-upload-limit-in-mb 100
```

The policy settings deserve a moment of attention because two of them shape what the firewall can even see. Request body inspection determines whether the firewall reads the request body at all. With it on, the firewall can catch injection in form posts and JSON payloads, which is most of the value of running a WAF in front of an API. With it off, the firewall inspects only the request line and headers, which leaves a large blind spot. The maximum request body size and the file upload limit cap how much of a request the firewall buffers and inspects. Set them high enough to cover your legitimate large requests, because a body larger than the limit is handled according to the policy and can surprise you if your application accepts big uploads. These limits are a frequent source of confusion later, so record the values you chose and why.

Next, attach a managed rule set. The managed rule set is where the OWASP-derived signatures come from, and you choose both the rule set type and its version explicitly. Pinning the version is not optional in any setup you intend to keep, because a version is a behavior contract, and a later version can add, remove, or retune rules in ways that change what gets blocked.

```bash
# Attach the OWASP managed rule set at a pinned version
az network application-gateway waf-policy managed-rule rule-set add \
  --policy-name waf-prod-policy \
  --resource-group rg-edge-prod \
  --type OWASP \
  --version 3.2
```

At this point you have a policy that evaluates the managed rules and logs matches, but it is not yet attached to anything, so it is inspecting no traffic. Associate it with your gateway. The simplest association is gateway-wide, which makes every listener on the gateway inherit the policy. To attach the policy to the whole gateway, reference the policy resource from the gateway. The exact CLI shape depends on whether you are updating an existing gateway or creating a new one, and the common case is attaching a policy to a gateway that already exists.

```bash
# Get the policy resource ID
POLICY_ID=$(az network application-gateway waf-policy show \
  --name waf-prod-policy \
  --resource-group rg-edge-prod \
  --query id -o tsv)

# Associate the policy with the gateway
az network application-gateway update \
  --name appgw-prod \
  --resource-group rg-edge-prod \
  --set firewallPolicy.id="$POLICY_ID"
```

For a per-listener or per-path association, you attach the policy reference to the listener or to the path rule within the gateway's routing configuration rather than to the gateway root. The mechanics differ slightly, but the principle is identical: the policy is a separate resource, and association points one or more parts of the gateway at it. Start gateway-wide unless you already know two sites on the same gateway need different firewall postures, because a single policy is far easier to reason about while you are learning what your traffic trips.

### How do I associate a WAF policy with a listener?

Attach the policy resource ID to the listener inside the gateway configuration rather than to the gateway root. A listener-scoped policy lets one gateway host several sites, each with its own firewall rules, exclusions, and mode, which is the right model when sites on the same gateway have genuinely different risk profiles or traffic shapes.

Now confirm the firewall is logging. Send the Application Gateway firewall log category to your Log Analytics workspace through a diagnostic setting. Without this, detection mode produces output you cannot read, which defeats the entire phase.

```bash
# Enable diagnostic logging for the firewall log category
GATEWAY_ID=$(az network application-gateway show \
  --name appgw-prod --resource-group rg-edge-prod --query id -o tsv)

WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --workspace-name law-edge-prod --resource-group rg-edge-prod --query id -o tsv)

az monitor diagnostic-settings create \
  --name appgw-diagnostics \
  --resource "$GATEWAY_ID" \
  --workspace "$WORKSPACE_ID" \
  --logs '[{"category":"ApplicationGatewayFirewallLog","enabled":true}]'
```

With the policy created in detection mode, the managed rule set pinned, the policy associated, and logs flowing, the firewall is now watching your traffic and recording every rule match without blocking anything. This is the safe observation state, and you stay here while you do the real work of tuning. Drive representative traffic through the application, including the infrequent workflows that matter, and let the logs accumulate. The hands-on way to practice this whole sequence against a live gateway, including setting the policy, pinning the rule set, and reading the firewall log, is to [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), where you can break and fix a WAF without breaking anything that matters.

## Choosing the Managed Rule Set and Version

The managed rule set is the heart of the firewall's protective value, and the two decisions you make about it, which rule set and which version, have outsized consequences. The rule set is the family of signatures, derived from the OWASP Core Rule Set, that catches the common attack classes. The version is the specific revision of that family, and because Microsoft retunes rules between versions to reduce false positives and catch new attack patterns, the version is effectively a behavior contract. Two gateways running the same rule set at different versions can block different requests, which is exactly why an implicit or floating version is a latent surprise.

Prefer a current managed rule set version for a new deployment, because newer versions generally carry better default tuning and fewer of the notorious early false positives. The practical caution is that you should pin whatever version you choose explicitly in the policy, rather than relying on a default that can shift underneath you. When you decide to move to a newer version later, treat the upgrade exactly like a fresh rollout: change the version while the policy is in detection mode if you can, or on a non-production gateway first, observe the new log output for a tuning period, adjust exclusions for any new false positives the upgraded rules introduce, and only then carry the change to production prevention. A rule-set version upgrade that lands straight in production prevention is the same mistake as enabling prevention on day one, just deferred.

### Which OWASP managed rule set should I use?

For a new gateway, choose a current managed rule set version and pin it explicitly. Newer versions ship better default tuning and catch more recent attack patterns, while pinning protects you from a silent behavior change when Microsoft updates the available versions. Treat any future version change as a tuning event, not a transparent upgrade.

Within a rule set, the signatures are organized into rule groups, each targeting a class of attack such as SQL injection, cross-site scripting, protocol enforcement, or request limits. Every individual rule has an identifier, and that identifier is the unit you reach for when you tune. When the logs show a rule misfiring on legitimate traffic, you will see the exact rule identifier and the rule group it belongs to, which tells you precisely what to scope an exclusion or an override against. You almost never want to disable an entire rule group, because a group covers a whole attack class and turning it off opens a real hole. The disciplined move is to identify the single signature that misfired and address it narrowly, which is the subject of the next section.

There is also an anomaly scoring model worth understanding, because it changes how you read what a block means. In the modern rule sets, many rules do not block on their own; instead each matching signature contributes to an anomaly score for the request, and the request is blocked only when the cumulative score crosses a threshold. This means a single benign-looking match in the logs may not have caused a block by itself, and conversely a request can be blocked by the accumulation of several low-severity matches none of which would block alone. When you tune, look at the full set of rules a request tripped, not just the first one, because the block is a property of the total score. This is one reason reading the logs carefully, rather than reacting to a single line, separates good tuning from cargo-cult tuning.

## Taming False Positives with Exclusions and Per-Rule Overrides

False positives are not a sign that the firewall is broken; they are an expected and routine part of running a managed rule set against real traffic, and tuning them out is the central skill of operating a WAF. The two tools for this are exclusions and per-rule overrides, and choosing between them correctly is what keeps your firewall both quiet and protective. An exclusion tells the firewall to skip inspection of a specific request attribute, such as a named header, cookie, or argument, so a field that legitimately contains content resembling an attack stops tripping the rules. A per-rule override changes the action or state of a specific rule, for example disabling a single signature that is hopeless for your application or changing its action. Reach for an exclusion first, because it is narrower: it removes one field from inspection rather than removing one signature from your whole defense.

The danger to internalize is that a sloppy exclusion can quietly disable protection across your entire application. An exclusion scoped to a request attribute applies wherever that attribute appears unless you also scope it to specific rules. If you exclude an argument named "data" from all rules because one endpoint posts a base64 blob in a field called "data," you have just told the firewall to ignore a field named "data" everywhere, including on endpoints where that field carries user-controlled input that an attacker could weaponize. The correct exclusion is as tight as you can make it: scope it to the exact attribute, and where the platform allows, scope it to the specific signature or signatures that were misfiring, so the rest of the firewall keeps inspecting that field normally. Tight exclusions tune the false positive without surrendering the protection.

### How do I handle WAF false positives with exclusions?

Find the exact rule identifier and request attribute in the firewall logs, then add an exclusion scoped to that attribute and, where possible, to that specific rule. Avoid broad exclusions that drop a field from all inspection, because they remove protection everywhere the field appears, not just on the endpoint that needed the fix.

A worked example makes the workflow concrete. Suppose an upload endpoint at the path /api/documents starts showing blocked requests once you reach prevention, or logged matches while still in detection. You query the firewall log and find that requests to that path are tripping a signature in the SQL injection group because the document metadata, posted as a JSON field, contains text that pattern-matches an injection signature. The wrong fix is to disable the SQL injection signature group, which would leave every other endpoint exposed to real injection. The better fix is an exclusion scoped to the specific JSON argument that carries the metadata, applied against the specific signature that fired, so the firewall stops inspecting that one field for that one signature while continuing to inspect everything else.

```bash
# Add an exclusion scoped to a specific request attribute
az network application-gateway waf-policy managed-rule exclusion add \
  --policy-name waf-prod-policy \
  --resource-group rg-edge-prod \
  --match-variable RequestArgNames \
  --selector-match-operator Equals \
  --selector "metadata"
```

When the platform supports scoping the exclusion to specific rules within a rule set, prefer that form, because it confines the exclusion to the rules that actually misfired rather than removing the field from all inspection. The general pattern to keep in mind is a funnel: start from the broadest thing the logs tell you (a path, a field, a rule identifier), and then make your fix as narrow as the data allows. A per-rule override is the heavier instrument, used when a signature is simply incompatible with your application and no exclusion can save it.

```bash
# Disable a single managed rule that is hopeless for this app, leaving the group intact
az network application-gateway waf-policy managed-rule rule-set update \
  --policy-name waf-prod-policy \
  --resource-group rg-edge-prod \
  --type OWASP \
  --version 3.2 \
  --group-name REQUEST-942-APPLICATION-ATTACK-SQLI \
  --rules 942100
```

Even when you disable a single signature, you have given up that signature's coverage everywhere, which is why an exclusion that keeps the signature active on every other field is almost always the better choice. The discipline of preferring the narrowest tool, in order of exclusion before override before group disable before mode change, is what keeps a tuned firewall protective rather than hollowed out one quick fix at a time.

## Writing Custom Rules: Rate Limiting, Geo Matching, and Address Policy

Managed rules catch known attack signatures, but they know nothing about your business. They cannot tell that one client is hammering your login endpoint a thousand times a minute, that you do not serve customers in a particular region, or that a known-bad address range should never reach you at all. Custom rules express exactly this kind of policy, and they run before the managed rules, so a custom rule can allow, block, or rate-limit a request based on conditions the managed set never considers. That ordering is powerful and also a trap, because a custom allow rule placed too early can wave a request past inspection it should have received, so write custom rules with the same care you would give a firewall access list.

A custom rule has a priority, an action, and one or more match conditions. Priority decides evaluation order, lower numbers first, and the first matching rule with a terminating action wins. The action is allow, block, log, or, for the specialized rate-limiting rule type, a rate-limit action. The match conditions test request attributes such as the source address, the geographic location derived from the address, a header, the request method, the URI path, or the query string, using operators like equals, contains, begins-with, or a regular expression match. Building a custom rule is a matter of expressing your policy as a priority, an action, and the conditions that select the traffic.

### How do I write a custom WAF rule?

Define a priority that places the rule correctly relative to your other custom rules, choose an action of allow, block, or rate limit, and specify match conditions on request attributes such as the source address, country, header, or path. Lower priority numbers evaluate first, and a terminating action stops further custom-rule evaluation, so order matters as much as the conditions.

Rate limiting is the custom rule most teams reach for first, because abusive traffic that is technically well-formed sails straight through the managed rules. A rate-limit rule counts requests from a client over a time window and blocks the client once it exceeds a threshold, which blunts credential-stuffing, scraping, and crude denial-of-service attempts without touching legitimate users who stay under the limit. You define the threshold, the duration of the window, and the key that groups requests, typically the client address, and optionally a match condition so the limit applies only to a sensitive path such as login.

```bash
# Create a rate-limit custom rule scoped to the login path
az network application-gateway waf-policy custom-rule create \
  --policy-name waf-prod-policy \
  --resource-group rg-edge-prod \
  --name limitLogin \
  --priority 10 \
  --rule-type RateLimitRule \
  --action Block \
  --rate-limit-threshold 100 \
  --rate-limit-duration OneMin \
  --group-by-user-session ClientAddr

# Add the match condition that scopes the rule to the login path
az network application-gateway waf-policy custom-rule match-condition add \
  --policy-name waf-prod-policy \
  --resource-group rg-edge-prod \
  --name limitLogin \
  --match-variables RequestUri \
  --operator Contains \
  --values "/api/login"
```

Geographic matching is the next common custom rule. If your service legitimately operates in a defined set of countries, blocking traffic that originates elsewhere removes a large slice of automated attack traffic at the door, before any managed signature even runs. The firewall derives a country from the source address, and you match on it with a geo-match operator. The honest caveat is that geographic blocking is a blunt instrument: address-to-country mapping is imperfect, travelers and corporate networks can appear in unexpected places, and a determined attacker uses an address in a country you allow. Treat geo rules as a way to cut background noise, not as a real boundary, and never as your only control.

```bash
# Block traffic from outside the regions you serve
az network application-gateway waf-policy custom-rule create \
  --policy-name waf-prod-policy \
  --resource-group rg-edge-prod \
  --name allowedRegions \
  --priority 20 \
  --rule-type MatchRule \
  --action Block

az network application-gateway waf-policy custom-rule match-condition add \
  --policy-name waf-prod-policy \
  --resource-group rg-edge-prod \
  --name allowedRegions \
  --match-variables RemoteAddr \
  --operator GeoMatch \
  --negation true \
  --values "US" "CA" "GB"
```

Address-based custom rules round out the set. A block rule against a known-bad address range stops a specific abuser, and an allow rule for a trusted partner range can exempt them from a rate limit or a geo block, provided you place it at a priority that runs before the rule it needs to override. This is exactly where the ordering trap bites: an allow rule that runs before your managed-rule evaluation does not skip the managed rules unless it terminates evaluation in a way that bypasses inspection, so be deliberate about whether an allow rule is meant only to exempt a request from later custom rules or to wave it past everything. When in doubt, prefer narrowing your block rules over adding broad allow rules, because a tight block leaves the rest of your defense intact while a broad allow can quietly open a path you did not intend.

## The Settings the Defaults Get Wrong

A WAF policy can be technically enabled and still leave gaps because a default value does not match your application. The defaults are chosen to be safe for the average case, and the average case is rarely your case in the details that matter. Walking through the handful of settings that most often need changing saves you from the slow realization, weeks later, that the firewall was not inspecting the thing you most needed it to inspect.

The first is request body inspection. If your application is an API or accepts form posts, and most do, the body is where injection attacks ride. A policy that leaves body inspection off, or that caps the inspected body size below your real request sizes, gives you a firewall that confidently inspects headers while a malicious payload flows through the body untouched. Confirm body inspection is on and that the maximum inspected body size comfortably exceeds your legitimate large requests. The trade-off is that inspecting larger bodies costs the gateway some processing, so set the limit to fit your real traffic rather than to an arbitrary maximum, but do not set it so low that real requests slip past uninspected.

The second is the file upload limit. Applications that accept file uploads need this set high enough that legitimate uploads are handled correctly, because a request that exceeds the limit is treated according to the policy and can produce confusing failures or uninspected passage depending on configuration. If users upload large files, raise the limit to match, and verify with a real upload of representative size during the detection phase so you discover any mismatch in the logs rather than in a support ticket.

### Why does the WAF block a legitimate file upload?

A legitimate upload is usually blocked for one of two reasons: the file content trips a managed signature that pattern-matches an attack signature, which an exclusion scoped to the upload path resolves, or the upload exceeds the configured body or file size limit. Check the firewall log for the rule identifier or a size-related entry to tell the two apart.

The third is the managed rule set version, covered earlier but worth restating as a default trap. If you never pin the version, you have accepted whatever default the platform applies, and you have signed up for a behavior change whenever that default moves. Pin it. The fourth is the mode itself, which defaults in a way that may not match your rollout plan; always set it to Detection explicitly for a new policy so you are never surprised to find a fresh policy blocking traffic. The fifth, easy to forget, is logging: a policy with no diagnostic setting routing the firewall log to a queryable destination is a firewall you are operating blind, and the default does not configure this for you.

Finally, consider the interaction between the WAF and any edge service in front of it. If you run a content delivery layer or an edge WAF ahead of the gateway, the source address the gateway sees may be the edge service rather than the real client, which breaks address-based and geo custom rules unless you account for the forwarded client address. When an edge WAF is part of the picture, decide deliberately where each control lives, because running overlapping firewalls without a plan produces double false positives and confusing logs. The setup and routing considerations for the edge alternative are covered in our guide to [configuring Front Door routing](/2023/05/15/configure-front-door-routing/), and the right division of labor between an edge WAF and a regional gateway WAF is a design decision, not an accident.

## Verifying It Worked: Reading the WAF Logs

A firewall you cannot observe is a firewall you cannot trust, and the verification step is what turns configuration from hope into evidence. The Application Gateway firewall log is the authoritative record of what the WAF evaluated and what it did, and reading it is how you confirm, in detection mode, that your tuning caught the false positives, and how you confirm, in prevention mode, that a block was a real attack rather than a missed exclusion. Querying these logs in Log Analytics, where your diagnostic setting routes them, is the single most useful habit you can build around a WAF.

Each firewall log entry tells you the action taken, whether the request was matched, blocked, or merely logged, along with the rule identifier that fired, the rule group, the matched request attribute, the source address, the host, and the request URI. That set of fields is exactly what you need to tune: the rule identifier tells you which signature fired, the matched attribute tells you which field tripped it, and the URI tells you which endpoint to scope a fix against. When you see a block, you read these fields to decide in seconds whether it was an attacker probing for injection or a customer whose perfectly normal request happened to look like one.

```kusto
// Recent firewall actions, newest first, with the fields that drive tuning
AzureDiagnostics
| where ResourceType == "APPLICATIONGATEWAYS"
| where Category == "ApplicationGatewayFirewallLog"
| project TimeGenerated, action_s, ruleId_s, ruleGroup_s, requestUri_s, clientIp_s, Message
| order by TimeGenerated desc
| take 100
```

### How do I confirm what the WAF actually blocked?

Query the ApplicationGatewayFirewallLog category in Log Analytics and read the action, rule identifier, matched attribute, and request URI for each entry. A blocked entry on a legitimate endpoint signals a missing exclusion to build, while a blocked entry carrying a clear attack pattern confirms the firewall is doing its job.

During the detection phase, the query you live in is the one that counts matches by rule and by path, because that ranking tells you where your tuning effort belongs. The rules that fire most often on your traffic are your top candidates for either an exclusion, if the matches are legitimate, or for confidence that the firewall is catching real probing, if the matches are hostile. Spend your tuning time on the top of that list rather than chasing every single entry, because the long tail of one-off matches matters far less than the handful of rules that fire constantly.

```kusto
// Rank the rules firing most often, to focus tuning where it matters
AzureDiagnostics
| where Category == "ApplicationGatewayFirewallLog"
| summarize hits = count() by ruleId_s, ruleGroup_s, requestUri_s
| order by hits desc
```

When you finally promote to prevention, the verification habit does not stop; it changes shape. Now you watch for blocked actions and you triage each pattern: a new endpoint that starts showing blocks after a deployment usually means a code change introduced a request shape your exclusions never anticipated, and the fix is a scoped exclusion, not a panicked rollback of the firewall. A spike of blocks from a narrow set of addresses against a sensitive path usually means the firewall just earned its cost by stopping an attack, and the right response is to confirm and perhaps add an address block to shed the load earlier. Reading the logs is not a one-time verification step; it is the ongoing practice that keeps a WAF tuned as your application changes.

## Common Misconfigurations and Their Symptoms

Most WAF pain reduces to a small set of recurring misconfigurations, and recognizing the symptom quickly is half the cure. Each pattern below pairs the symptom an engineer reports with the setup step that prevents or fixes it, so you can move from observation to remedy without a long investigation.

The first and most damaging pattern is prevention mode enabled before any tuning. The symptom is a sudden burst of 403 responses across multiple endpoints right after the firewall went live, affecting legitimate users in ways the application logs cannot explain because the block happened upstream of the application. The cause is skipping the detection phase, and the remedy is to switch back to detection, read the logs to find every rule that was firing, build the exclusions, and only then return to prevention. The prevention of the prevention-first mistake is simply the detect-then-prevent rule, applied without shortcuts.

The second pattern is the WAF disabled after a single false positive. The symptom is a firewall that exists in the configuration but is set to detection or disabled because someone turned off enforcement during an incident and never turned it back on. The cause is treating the WAF as a binary on-off control instead of reaching for a targeted exclusion, and the remedy is to identify the one signature and field that caused the original false positive, write the narrow exclusion, and re-enable prevention. A WAF left disabled is the worst of both outcomes, because it carries the cost without the protection.

### What causes the WAF to block normal JSON requests?

A managed signature, often in the SQL injection or cross-site scripting group, pattern-matches text inside a JSON field that resembles an attack, such as SQL keywords in a free-text value or markup in a description. The fix is an exclusion scoped to the specific JSON argument and rule, applied while in detection mode so it never blocks a real request.

The third pattern is a managed signature firing on normal JSON or form content, the false positive that exclusions exist to solve. The symptom is specific endpoints returning 403 while most of the application works fine, and the firewall log pointing at a particular signature and a particular field. The cause is a broad signature catching legitimate content, and the remedy is the scoped exclusion described earlier, kept as narrow as the data allows.

The fourth pattern is a rule-set version upgrade changing behavior. The symptom is new blocks appearing after a version change that no code deployment can explain, on endpoints that worked fine the day before. The cause is treating a version upgrade as transparent when it is actually a behavior change, and the remedy is to roll the version change through detection first, tune for the new false positives, and then promote, exactly as you would a fresh policy.

The fifth pattern is an exclusion scoped too broadly, the silent opposite of a false positive. There is no error symptom at all, which is what makes it dangerous; the firewall simply stops inspecting a field everywhere because someone excluded it globally to fix one endpoint. The cause is a quick fix under pressure, and the remedy is a periodic review of every exclusion to confirm each is scoped to the narrowest attribute and rule that resolves its specific false positive. The sixth pattern is the bypass, where the firewall protects nothing because traffic reaches the backend without passing through the gateway, and its symptom is attacks that succeed against the application while the firewall logs show nothing, because the firewall never saw the traffic. The remedy lives in the network, locking the backend so the gateway is the only path in.

## Making the WAF Repeatable as Code

A WAF policy assembled by hand in the portal is a policy no one can reproduce, audit, or roll back with confidence. The exclusions you carefully tuned, the custom rules you ordered just so, the pinned rule-set version, all of it lives as undocumented clicks that the next engineer cannot reconstruct after an accidental deletion or a migration to a new region. Expressing the policy as infrastructure code turns your tuning into a reviewable, versioned artifact, which matters more for a WAF than for almost any other resource because the value of a WAF is entirely in its accumulated tuning. The exclusions and custom rules are institutional knowledge, and code is where institutional knowledge belongs.

Bicep is the natural choice on Azure because it models the WAF policy resource directly, including the policy settings, the managed rule set with its pinned version, the managed signature exclusions, and the custom rules, in one declarative file. A Bicep definition makes the relationships explicit: the mode, the rule-set version, every exclusion with its scope, and every custom rule with its priority and conditions, all visible in one place where a reviewer can reason about them. When you change the policy, you change the file, you review the diff, and you deploy, which gives you a history of exactly how the firewall's behavior evolved and why.

```bicep
resource wafPolicy 'Microsoft.Network/ApplicationGatewayWebApplicationFirewallPolicies@2023-05-01' = {
  name: 'waf-prod-policy'
  location: location
  properties: {
    policySettings: {
      state: 'Enabled'
      mode: 'Detection'
      requestBodyCheck: true
      maxRequestBodySizeInKb: 128
      fileUploadLimitInMb: 100
    }
    managedRules: {
      managedRuleSets: [
        {
          ruleSetType: 'OWASP'
          ruleSetVersion: '3.2'
        }
      ]
      exclusions: [
        {
          matchVariable: 'RequestArgNames'
          selectorMatchOperator: 'Equals'
          selector: 'metadata'
        }
      ]
    }
    customRules: [
      {
        name: 'limitLogin'
        priority: 10
        ruleType: 'RateLimitRule'
        action: 'Block'
        rateLimitThreshold: 100
        rateLimitDuration: 'OneMin'
        groupByUserSession: [ { groupByVariables: [ { variableName: 'ClientAddr' } ] } ]
        matchConditions: [
          {
            matchVariables: [ { variableName: 'RequestUri' } ]
            operator: 'Contains'
            matchValues: [ '/api/login' ]
          }
        ]
      }
    ]
  }
}
```

Notice that the Bicep keeps the mode at Detection, which is the right default for the version-controlled definition: your pipeline should deploy the policy in detection mode, and the promotion to prevention should be a deliberate, separate, reviewed change rather than the default the file ships. This keeps the safe sequence intact even in automation, so a fresh deployment to a new environment never starts by blocking traffic. Some teams parameterize the mode so the same template deploys in detection to a new region and in prevention to a mature one, which is a clean way to encode the detect-then-prevent rule into the pipeline itself.

Terraform users have an equivalent resource that models the same structure, and the same principles apply: pin the rule-set version, keep exclusions and custom rules in the configuration, default to detection mode, and make promotion an explicit change. Whichever tool you use, the test of whether your WAF is truly repeatable is simple. If your gateway and its policy were deleted right now, could you redeploy the firewall with every exclusion and custom rule intact from your source repository alone, without anyone remembering what they clicked? If the answer is yes, your tuning is safe. If the answer is no, your most valuable security configuration is one accident away from gone.

## A Worked End-to-End Rollout

Putting the pieces together, here is how a careful team takes a WAF from nothing to enforcing in production without an outage, which is the whole point of the procedure. The team starts by confirming the gateway runs the WAF_v2 SKU and that the backend accepts traffic only from the gateway subnet, closing the bypass path before the firewall is even created. They create the WAF policy in detection mode, pin the managed rule set to a current version, route the firewall log to Log Analytics, and associate the policy gateway-wide because all sites on this gateway share a risk profile. Nothing is blocking yet, and that is intentional.

For two weeks the policy sits in detection while the team drives real traffic, including the monthly reporting export and a large bulk import that an administrator runs only occasionally. They query the firewall log daily, ranking rules by hit count. The top of the list is a SQL injection signature firing on the document metadata field at /api/documents, which they recognize as legitimate JSON content, so they add an exclusion scoped to that argument and that rule. The next item is a cross-site scripting signature firing on a rich-text description field in the content management path, another false positive, handled with a second narrow exclusion. The reporting export, when it finally runs on the first of the month, trips a request-size check, and because they are still in detection, they see it in the logs and raise the inspected body size to fit, rather than discovering it as a blocked export.

While tuning the managed rules, the team also adds the custom rules their business needs: a rate-limit rule on the login path to blunt credential stuffing, and a geo rule to shed automated traffic from regions they do not serve, placed at priorities that run before the managed evaluation. They test each by sending traffic that should trip it and confirming the expected log entry, still in detection so a mistake costs nothing. After two weeks the rule hit list has gone quiet except for entries that are clearly hostile probing, which is exactly the signal that tuning is complete: the firewall is matching attacks and not customers.

Only now do they promote to prevention, and they do it as a single reviewed change to the Bicep file, deployed through the pipeline. They watch the firewall log closely for the first day, and the blocks they see are the hostile probes they expected, with no legitimate endpoints affected, because every false positive was already tuned out in detection. A week later a deployment introduces a new endpoint, a block appears on it, and instead of disabling the firewall the on-call engineer reads the log, recognizes a new request shape, and adds one scoped exclusion through the same pipeline. The firewall stays on, the application stays up, and the security control keeps doing its job. That outcome is not luck; it is the detect-then-prevent rule and the setup checklist applied in order.

## How TLS Termination and Client Address Forwarding Shape Inspection

The Application Gateway terminates the client TLS connection, decrypts the request, and then inspects it, which is precisely what allows the firewall to read the body and headers of an HTTPS request that would otherwise be opaque. This is a feature, not a side effect: a firewall cannot inspect what it cannot decrypt, so terminating TLS at the gateway is what makes layer-7 inspection of encrypted traffic possible at all. The implication for configuration is that your certificate and listener setup is upstream of the firewall in the most literal sense, because the firewall only ever sees the decrypted request the listener hands it. A misconfigured listener that never completes the handshake means the firewall inspects nothing, not because the firewall failed but because no decrypted request ever reached it.

This termination point also reshapes what the firewall knows about the client, which directly affects your address-based and geographic custom rules. From the backend's perspective, every request now appears to come from the gateway, so the gateway preserves the real client address in a forwarded header for any downstream consumer that needs it. For the firewall's own custom rules, the source address it evaluates is the actual client address on the connection it terminated, which is what you want for rate limiting and geo matching in the common case where clients connect directly to the gateway. The complication arrives when something sits in front of the gateway.

### Why do my geo and rate-limit rules behave strangely behind a CDN?

When a content delivery network or another edge proxy fronts the gateway, the address the gateway sees is the edge node, not the real client, so geo and rate-limit rules key off the wrong address. You either move those controls to the edge layer that sees the true client, or configure the gateway to evaluate the forwarded client address where the platform supports it.

When an edge service such as a content delivery network or an edge firewall fronts the gateway, the connection the gateway terminates originates from the edge node, not from the end user. Every request then appears to come from a small set of edge addresses, which makes a rate-limit rule keyed on the source address nearly useless, because thousands of distinct users collapse into a handful of edge addresses and trip the limit together, and makes a geo rule wrong, because the edge node's location is not the user's. The resolution is architectural: decide which layer owns address-based controls. If an edge service sees the true client, run rate limiting and geographic policy there, and let the gateway WAF focus on the managed rules and content inspection that it is uniquely positioned to do after decryption. Running the same address-based control at two layers without coordination produces double false positives and logs that contradict each other, which is the worst kind of debugging session because both firewalls are telling a partial truth.

The lesson generalizes beyond addresses. Whenever you add a layer in front of the gateway, ask what that layer changes about the request the firewall finally sees, because the firewall reasons about the request as it arrives, not about the request the original client sent. Headers may be added or rewritten, the apparent source changes, and even the protocol details can shift. A WAF that was tuned against direct client traffic can behave differently once an edge layer reshapes the requests, which is one more reason to treat any topology change as a tuning event and to validate in detection mode before trusting prevention.

## Per-Site and Per-Path Policy Strategy

A single gateway often hosts more than one application, and those applications rarely share a risk profile. A public marketing site, an authenticated customer portal, and an internal administrative interface can all live behind one gateway, and applying identical firewall rules to all three is a compromise that serves none of them well. The administrative interface wants strict rules and aggressive rate limits because it should never see much traffic and any anomaly is suspicious. The marketing site wants permissive rules because it serves anonymous traffic at volume and a false positive there is a lost visitor. The portal sits between them. The standalone WAF policy model exists precisely so you can express these differences, by associating a different policy with each listener or even each path.

The strategy that works is to start simple and specialize only where the data justifies it. Begin with one gateway-wide policy in detection, tune it against all the traffic, and watch whether your false positives and your custom-rule needs actually diverge by site. Often they do not, and a single well-tuned policy serves the whole gateway, which is by far the easiest thing to operate. When the logs show that one site consistently needs exclusions another site must not have, or that one path needs a rate limit that would harm another, that divergence is the signal to split the policy. Split deliberately, one boundary at a time, rather than pre-emptively creating a policy per site before you know they differ.

### Should I use one WAF policy or several across a gateway?

Start with one gateway-wide policy and split into per-listener or per-path policies only when the logs show that sites or paths genuinely need different rules, exclusions, or modes. A single policy is far easier to operate and reason about, so specialize for a documented reason rather than out of a vague sense that separation is tidier.

A particularly useful application of per-path policy is running an administrative path in strict prevention while a public path the same gateway serves remains in a more permissive posture, or runs an additional rate limit a public path could not tolerate. Because a path-scoped policy applies through the gateway's path-based routing rule, you can give /admin a policy with low rate-limit thresholds and a tight geo restriction, while /public runs the same managed rules without those custom restrictions. The cost of this flexibility is operational: every additional policy is another set of exclusions to maintain, another mode to track, and another artifact to keep in code. The benefit is real protection tuned to real risk. Weigh the two honestly, and remember that an unmaintained second policy that no one updates is worse than a single policy everyone understands. Specialization is a tool for matching protection to risk, not a goal in itself.

Whichever scope you land on, keep the same discipline across every policy: detection before prevention, narrow exclusions, pinned rule-set versions, and everything in code. A gateway with three policies in three different states of tuning, two of them undocumented, is a maintenance burden that erodes the very protection the split was meant to improve. The strategy succeeds when each policy is as carefully operated as the single policy you would have run otherwise, and it fails the moment a policy becomes someone's forgotten experiment.

## Capacity, Performance, and the Real Cost of Inspection

Inspection is not free, and a configuration that ignores its cost can turn a security control into a latency problem. Every request the firewall examines is decoded, matched against the managed signatures, scored, and evaluated against your custom rules before it ever reaches the backend. For the vast majority of traffic this overhead is small and invisible, but the settings you choose determine how large it can grow, and the request shapes your application produces determine where it concentrates. Understanding the cost lets you set limits that protect without throttling, rather than discovering the trade-off during a load spike.

The largest single lever is request body inspection. Reading and matching a request body is more work than reading headers, and the work scales with the size of the body you allow the firewall to inspect. A high maximum inspected body size protects large uploads and posts, but it also means the gateway buffers and scans more bytes per request, which costs both memory and processing under load. The right setting is the smallest value that still comfortably covers your legitimate large requests, because that maximizes protection per unit of overhead. Setting the limit to an arbitrary high ceiling wastes capacity inspecting headroom you never use, while setting it too low leaves real requests partially uninspected. Measure your actual request sizes during the detection phase and set the limit to fit them with margin.

### Does enabling the WAF slow down my application?

For typical request sizes the added latency is small and usually unnoticeable, because matching signatures against a normal request is fast. The cost grows with large request bodies under inspection and with very high request rates, so the levers that matter are the inspected body size limit and the gateway's capacity, both of which you size to your real traffic.

The second factor is the gateway's own capacity. On the v2 generation the gateway scales its instance count to meet demand, and the firewall's inspection work is part of what that scaling absorbs. A gateway sized for its non-firewall load may need more headroom once inspection is added, particularly if your traffic includes many large bodies. Watch the gateway's capacity metrics during the detection phase, when the firewall is already doing the full inspection work without blocking, because that window shows you the real cost of inspection on your traffic before prevention adds any user-facing risk. If capacity is comfortable in detection, it will be comfortable in prevention, since blocking a request is cheaper than forwarding it.

The third factor is custom-rule efficiency. Custom rules evaluate before the managed rules, and a long list of complex rules, especially ones using regular expressions against large request attributes, adds per-request work. Keep custom rules as simple and as few as the policy requires, prefer specific match operators over broad regular expressions where either would work, and order them so the most commonly matched terminating rules sit at the front, which lets the firewall reach a decision sooner. None of this means avoiding custom rules; it means writing them with the same care for cost that you would give any code on the request path, because that is exactly what they are.

## Migrating from Legacy In-Gateway WAF Configuration

Many existing gateways still carry their WAF configuration in the older model, where the rules, mode, and disabled-rule settings lived inside the gateway resource itself rather than in a standalone policy. If you are operating one of these, moving to a standalone WAF policy is worth doing, because the policy model is where all current capability lives: per-listener and per-path association, the full custom-rule engine, structured exclusions, and clean expression as code. The migration is not difficult, but it rewards the same caution as any change that touches the firewall, because a careless cutover can swap a tuned configuration for an untuned one.

The safe migration mirrors the detect-then-prevent rule. Create a new standalone policy that reproduces the legacy configuration: the same managed rule set and version, the same disabled rules expressed as overrides, the same exclusions expressed in the structured form, and the same mode. Crucially, build and review this new policy before you associate it, treating it as a fresh policy that happens to start from a known configuration. Then associate the new policy and watch the firewall log to confirm it behaves identically to the legacy configuration it replaced, because subtle differences in how exclusions are expressed between the models can change behavior in ways only the logs reveal. If the new policy matches, you have migrated cleanly; if it does not, the logs tell you exactly which exclusion or override did not carry over.

### How do I move from in-gateway WAF settings to a standalone policy?

Recreate the legacy configuration as a new standalone WAF policy, matching the rule set version, disabled rules, exclusions, and mode, then associate it and verify in the firewall log that behavior is identical before retiring the old configuration. Treat any difference the logs reveal as a tuning gap to close, not a detail to ignore.

The payoff of the migration is realized only if you also adopt the practices the policy model enables, rather than carrying old habits into the new resource. Put the policy in code, pin the version explicitly if the legacy configuration left it implicit, and review whether the disabled rules you inherited are still necessary or whether a narrower exclusion would restore protection the old configuration gave up. A migration is a rare opportunity to re-examine tuning decisions made long ago, often under incident pressure, that no one has revisited since. The standalone policy is not just a new container for the same settings; it is a chance to make the firewall both more capable and better understood than the configuration it replaces.

## What the Firewall Cannot Do, and the Controls That Complete It

A web application firewall is a strong layer, and it is one layer. Treating it as the whole of your security posture is a mistake that the very effectiveness of a well-tuned policy can encourage, because an attack-free dashboard invites the assumption that the application is safe. The firewall inspects inbound HTTP and matches known attack patterns, which means there are real threats it was never built to address, and naming them keeps the firewall in its proper place as one control among several rather than a single shield you hide behind.

The firewall does not authenticate or authorize your users. It cannot tell a legitimate logged-in customer from one who has stolen a session, because both present well-formed requests that match no attack pattern. Identity, session handling, and access enforcement live in your application and your identity platform, and a request that passes the firewall cleanly may still be one your authorization logic should refuse. Nor does the firewall protect against logic flaws unique to your application, such as a pricing endpoint that trusts a client-supplied total or a workflow that lets one tenant read another tenant's data. Those are business-logic vulnerabilities, invisible to a generic attack signature, and only your own validation and testing catch them.

The firewall also does not secure the paths around it. Secrets embedded in code, an over-permissive identity granted to the application, a storage account left open to the public, a backend reachable on a path that bypasses the gateway, all of these are exposures the firewall has no view of. Its protection is bounded by the traffic that flows through it, decrypted, as inbound HTTP. Everything that travels another way, or that exploits trust the application itself extends, is someone else's job to defend.

The practical conclusion is to place the firewall inside a layered posture rather than at the front of an empty one. Strong authentication and least-privilege access, careful input validation in the application, secrets kept out of code, a locked-down network so the gateway is the only door, and monitoring across all of them together form the defense the firewall contributes to. A tuned policy that quietly blocks injection and throttles abuse is genuinely valuable, and it is most valuable when it is one well-understood part of a whole rather than a comforting green light that hides everything it was never designed to see.

## Alerting and Ongoing Operations

Tuning a WAF to a quiet state is the start of operating it, not the end, because an application changes and a firewall that is not watched drifts out of alignment with the traffic it serves. The operational habit that keeps a WAF healthy is turning the firewall log from a thing you query during incidents into a signal you monitor continuously. The same log fields you used during tuning, the action, the rule identifier, the matched attribute, the source address, and the request URI, become the basis for alerts that tell you when something has changed before a user has to.

The most valuable alert is on a sudden rise in blocked requests, because a spike is almost always meaningful. A spike concentrated on a single endpoint right after a deployment usually means a code change introduced a request shape your exclusions never anticipated, which is your cue to add a scoped exclusion rather than wait for a support ticket. A spike concentrated from a narrow set of addresses against a sensitive path usually means the firewall just stopped an attack, which is your cue to confirm the pattern and perhaps shed the load earlier with an address block. The two look different in the log, and an alert that surfaces the spike lets you tell them apart in minutes rather than discovering the situation hours later.

### What should I alert on for a production WAF?

Alert on a sharp rise in blocked requests overall, on blocks newly appearing on a previously clean endpoint, and on the gateway's capacity metrics approaching their ceiling. The first two catch tuning gaps and attacks, and the third catches the inspection cost growing past the gateway's headroom, all of which you would rather learn from a signal than from an outage.

A second alert worth building watches for blocks appearing on an endpoint that was previously clean, because a previously quiet endpoint that starts blocking is a strong signal of either a new code path or a new attack focus. Tying this alert to the request URI field lets it fire narrowly, on the specific endpoint, which makes it actionable rather than noisy. A third operational signal is capacity: alert when the gateway approaches its capacity ceiling, because inspection cost grows with traffic and request size, and a capacity problem that creeps up over weeks is far cheaper to catch from a metric than from degraded latency during a peak.

Beyond alerting, build a light recurring review into your operations. Periodically read your exclusions and confirm each is still scoped as narrowly as it should be and still needed at all, because exclusions accumulate and a stale one is a quiet hole. Periodically review whether a newer managed rule set version is worth adopting, and if so, schedule it as a tuned detection-first change rather than letting it become an emergency. And periodically confirm the backend lockdown still holds, because network changes elsewhere can reopen a bypass path that the firewall cannot see. None of this is heavy work, and all of it keeps a tuned firewall tuned. A WAF is not a configure-once control; it is a living part of the application's defense that stays effective only as long as someone keeps reading what it tells them.

## Closing Verdict

The difference between a WAF that protects an application and a WAF that breaks it is almost never the rules themselves; it is the sequence in which you turn them on. Detection before prevention, exclusions before overrides, narrow before broad, code before clicks. The managed rule set gives you broad coverage against the common attack classes, exclusions and per-rule overrides let you tame the false positives that broad coverage inevitably produces, and custom rules let you express the business policy the managed set knows nothing about, but all of it only works if you observe before you enforce. The single discipline that ties the whole thing together is reading the logs, because the firewall log is the only place that tells you the truth about what your WAF is doing.

If you take one rule from this guide, take the detect-then-prevent rule, because every common WAF disaster is a violation of it. Enabling prevention on day one, disabling the firewall after one false positive, shipping a rule-set upgrade straight to production, all of them skip the observation step that would have surfaced the problem harmlessly in the logs. Stand the policy up in detection, hold it there until the rule hit list goes quiet, tune every false positive with the narrowest tool that resolves it, encode the result as infrastructure so your tuning survives, and then, only then, let the firewall start blocking. Do that and the WAF becomes what it is supposed to be: an invisible layer that stops attacks while no legitimate user ever knows it is there.

## Frequently Asked Questions

**How do I configure Application Gateway WAF?**

Create a standalone WAF policy in detection mode, attach a managed rule set pinned to a current version, and route the firewall log to a Log Analytics workspace. Associate the policy with your gateway, listener, or path, then drive representative traffic and read the logs to find false positives. Tune those with narrow exclusions, add any custom rules your business needs, and only after the rule hit list goes quiet do you promote the policy to prevention mode. The whole procedure is built so that every protective decision is made while the firewall is still only observing, which is what keeps a rollout from ever blocking a legitimate request.

**Should WAF run in detection or prevention mode?**

A new policy should run in detection mode first. Detection evaluates every rule and logs every match without blocking anything, which lets you safely learn what your real traffic trips before any user is affected. Hold the policy in detection long enough to cover your full traffic pattern, including infrequent workflows like monthly exports or bulk imports, then tune exclusions for the legitimate matches you find. Switch to prevention only after the logs show the firewall is matching attacks rather than customers. Going straight to prevention is the single most common cause of a WAF that breaks an application, and the detection phase costs you nothing because detection mode never blocks.

**Which OWASP managed rule set should I use?**

For a new gateway, choose a current managed rule set version and pin it explicitly in the policy. Newer versions carry better default tuning, fewer of the early false positives that frustrated teams on older revisions, and coverage for more recent attack patterns. Pinning the version matters because Microsoft retunes rules between versions, so an implicit or floating version can change what your firewall blocks without any action on your part. When you later decide to move to a newer version, treat that change exactly like a fresh rollout: apply it in detection first, tune for any new false positives, and only then promote, because a version change is a behavior change, not a transparent upgrade.

**How do I handle WAF false positives with exclusions?**

First read the firewall log to find the exact rule identifier and the request attribute that tripped it. Then add an exclusion scoped as narrowly as the data allows: to the specific header, cookie, or argument, and where the platform supports it, to the specific signature that misfired. A narrow exclusion removes one field from inspection for one rule while leaving the rest of your defense fully active. Avoid broad exclusions that drop a field from all inspection, because they silently remove protection everywhere that field appears, not just on the endpoint that needed the fix. Do this tuning while the policy is in detection mode so the false positive never costs a real user a blocked request.

**How do I write a custom WAF rule?**

A custom rule needs a priority, an action, and one or more match conditions. The priority sets evaluation order, with lower numbers first and the first terminating match winning. The action is allow, block, log, or a rate-limit action for the rate-limit rule type. The match conditions test request attributes such as the source address, the derived country, a header, the method, the path, or the query string, using operators like equals, contains, begins-with, or a regular expression. Custom rules evaluate before the managed rules, so place an allow rule carefully to avoid waving a request past inspection it should receive, and prefer tight block rules over broad allow rules to keep the rest of your defense intact.

**How do I associate a WAF policy with a listener?**

Attach the policy resource to the listener inside the gateway's configuration rather than to the gateway root. A listener-scoped policy lets a single gateway host several sites, each with its own firewall rules, exclusions, and mode, which is the correct model when sites on one gateway have genuinely different risk profiles. You can also associate a policy at the gateway level, where every listener inherits it, or at a specific path through a path-based routing rule. Choose the broadest scope that still meets your needs, because each additional policy is another set of exclusions and another mode to maintain, and start gateway-wide unless you already know two sites need to differ.

**Why does the WAF block a legitimate file upload?**

There are two usual causes. The first is that the file content or its metadata trips a managed signature, often a SQL injection or cross-site scripting signature that pattern-matches text inside the upload, which you resolve with an exclusion scoped to the upload path and the signature that fired. The second is that the upload exceeds the configured request body or file upload limit, in which case the request is handled according to the policy and may be rejected or passed uninspected. Read the firewall log to tell the two apart: a rule identifier points to a signature match needing an exclusion, while a size-related entry points to a limit you need to raise to fit your legitimate uploads.

**What does detection mode actually do if it does not block?**

Detection mode runs the full inspection pipeline, evaluating every request against every managed and custom rule and writing a log entry for every match, but it lets the request continue to the backend unchanged. It is a complete dress rehearsal of prevention mode without the consequences, which is exactly why it is the right starting state. Everything you would learn from prevention, which rules fire, on which endpoints, against which fields, you learn from detection, with the difference that no legitimate request ever fails. The logs detection produces are identical in structure to prevention logs except for the action, so all your tuning queries work the same way in both modes.

**Can I run rate limiting on only one path?**

Yes. Create a rate-limit custom rule and add a match condition that scopes it to the path you want to protect, such as a login or token endpoint, using a contains or begins-with operator on the request URI. The rule then counts and limits requests only when they target that path, leaving the rest of your application untouched by the limit. This is the common and recommended pattern, because a global rate limit risks throttling legitimate high-volume endpoints while a path-scoped limit concentrates protection where abuse actually concentrates, on authentication and other sensitive endpoints.

**Why did new blocks appear after a rule-set version upgrade?**

Because a version upgrade is a behavior change, not a transparent update. Microsoft adds, removes, and retunes rules between rule-set versions, so the same traffic that passed cleanly on the old version can match a rule on the new one. This is precisely why you should never apply a version upgrade straight to production prevention. Move the change through detection first, on a non-production gateway if you have one, observe the new log output for a tuning window, build exclusions for any new false positives the upgraded rules introduce, and only then carry the upgrade to production. Treating the version as pinned and the upgrade as a deliberate, tuned event prevents this surprise entirely.

**How do I keep an exclusion from disabling protection everywhere?**

Scope it tightly. An exclusion applied to a request attribute without a rule scope removes that attribute from inspection for all rules, everywhere it appears, which is far broader than fixing one endpoint's false positive. Scope the exclusion to the exact attribute that tripped the rule, and where the platform allows, also scope it to the specific signature or signatures that misfired, so every other rule keeps inspecting that field normally. Review your exclusions periodically, because a broad exclusion produces no error symptom at all, which makes it the most dangerous kind of misconfiguration: the firewall quietly stops inspecting something and nothing tells you until an attacker finds the gap.

**Does the WAF inspect HTTPS traffic?**

Yes, because the gateway terminates the TLS connection, decrypts the request, and then inspects the decrypted content. This is what allows the firewall to read the headers and body of an encrypted request that would otherwise be opaque. The consequence is that your certificate and listener configuration sits upstream of inspection: the firewall only ever sees what the listener successfully decrypts and hands it. A listener that fails to complete the handshake means the firewall inspects nothing, not through any fault of the firewall but because no decrypted request reached it. Terminating TLS at the gateway is therefore a prerequisite for layer-7 inspection of encrypted traffic, not an optional detail.

**What is the difference between an exclusion and a per-rule override?**

An exclusion tells the firewall to skip inspection of a specific request attribute, such as a named argument or header, so a field that legitimately contains attack-like content stops tripping rules. A per-rule override changes a specific rule itself, for example disabling it or changing its action across all traffic. Reach for an exclusion first because it is narrower: it removes one field from inspection while keeping the signature active everywhere else. Use an override only when a signature is fundamentally incompatible with your application and no exclusion can save it, because disabling a rule gives up that signature's coverage for every request, not just the one field that caused the false positive.

**How do I confirm the WAF is actually protecting my app?**

Read the firewall log in Log Analytics. During detection, query for the rules firing most often and confirm they are catching attacks or that you have tuned the legitimate matches with exclusions. After promotion, watch for blocked actions and triage each pattern: blocks carrying clear attack signatures from probing addresses confirm the firewall is working, while blocks on legitimate endpoints signal a missing exclusion. The log fields, the action, rule identifier, matched attribute, source address, and request URI, give you everything needed to decide in seconds whether any given block was an attacker or a customer. A WAF you do not read the logs for is a WAF you are operating on faith.

**Should I block traffic by country?**

Geographic blocking is a useful way to shed background attack noise if your service legitimately serves only a defined set of countries, because a large share of automated probing originates from regions you do not serve. Implement it as a custom rule matching on the derived country. Treat it as noise reduction rather than a real boundary, though, because address-to-country mapping is imperfect, legitimate users travel or sit behind corporate networks in unexpected places, and a determined attacker simply uses an address in a country you allow. Never make a geo rule your only control, and always validate it in detection mode first, because an overly aggressive geo block can quietly turn away real customers with no error your application can explain.

**What happens to a request larger than the body size limit?**

A request whose body exceeds the configured maximum inspected size is handled according to the policy, and the exact behavior depends on your settings, which is why the limit deserves deliberate configuration rather than acceptance of a default. The practical risk is twofold: a legitimate large request can be rejected if the limit is too low, producing a confusing failure your application logs cannot explain, or a large body can pass with only part of it inspected, leaving a blind spot. Set the inspected body size to comfortably cover your real large requests, and validate with an actual large request during detection so any mismatch shows up in the logs rather than as a production surprise.

**Can the WAF protect a backend that has its own public IP?**

No. The firewall protects only traffic that passes through the gateway, so a backend reachable directly over its own public address sits entirely outside the firewall's view. Attackers can reach that backend without ever touching the gateway, and the firewall log shows nothing because the firewall never saw the traffic. Standing up a WAF therefore includes locking the backend so it accepts connections only from the gateway's subnet, removing any stray public addresses, and confirming through the network configuration that the gateway is the single door into the application. A firewall on a leaky network is a lock beside an open window, and closing that window is part of the WAF setup, not a separate task.

**How do I make my WAF configuration reproducible?**

Express the entire policy as infrastructure code, using Bicep or Terraform, including the policy settings, the pinned managed rule set version, every exclusion with its scope, and every custom rule with its priority and conditions. Default the code to detection mode and make promotion to prevention a separate, reviewed change so automation never starts by blocking traffic. The test of reproducibility is simple: if your gateway and policy were deleted right now, could you redeploy the firewall with every exclusion and custom rule intact from your repository alone? Because a WAF's entire value lives in its accumulated tuning, that tuning is exactly the kind of institutional knowledge that belongs in version-controlled code rather than in undocumented portal clicks.

**Why is my WAF blocking normal JSON API requests?**

A managed signature, commonly in the SQL injection or cross-site scripting group, is pattern-matching text inside a JSON field that resembles an attack, such as SQL keywords appearing in a free-text value or markup in a description field. The firewall cannot tell legitimate content from a payload by inspection alone, so it flags the match. The fix is an exclusion scoped to the specific JSON argument that carries the legitimate content and, where possible, to the specific signature that fired, applied while the policy is still in detection mode so it never blocks a real request. Disabling the whole rule group is the wrong move, because it would surrender protection against real injection on every other endpoint to fix one field.

**How long should I leave a new policy in detection mode?**

Long enough to observe every kind of legitimate request your application produces, which is a function of traffic coverage rather than calendar time. Some legitimate request shapes appear only during specific workflows, such as a monthly reporting export, an occasional bulk import, or a partner integration that calls an unusual endpoint, and any of these can trip a rule the first time it runs under prevention if you never saw it in detection. A reasonable default is at least one full business cycle of your application, often a couple of weeks, and longer if you know there are infrequent but important workflows you have not yet exercised. Promote only when the rule hit list has gone quiet except for clearly hostile matches, because that silence is the signal that your tuning is complete.
