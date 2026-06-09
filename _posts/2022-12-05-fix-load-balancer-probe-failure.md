---
layout: post
title: "Fix Azure Load Balancer Probe Failures"
page_title: "Fix Azure Load Balancer Health Probe Failures: Why Your Backend Shows Unhealthy and How to Diagnose Probe Port, NSG, Protocol, and Path Causes"
date: 2022-12-05
categories: ["Technology"]
tags: ["Azure", "Load Balancer", "Health Probe", "Networking", "Troubleshooting", "NSG"]
excerpt: "An Azure Load Balancer probe failing and marking a backend unhealthy has five root causes. Learn which one is yours, how to confirm it, and the exact fix."
image: "/assets/images/blog/blog-79.webp"
reading_time: 65
author: "robert-quinn"
last_updated: 2022-12-05
lang: en
---
An Azure Load Balancer probe failing is one of the most common reasons a healthy looking application stops serving traffic, and it is also one of the most misdiagnosed. The instance is running. The service is up. You can sign in and watch it respond on the box itself. Yet the portal insists the backend is unhealthy, the load balancer has pulled the instance out of rotation, and every request now lands on a different instance or, when every instance fails the same way, on nothing at all. The instinct is to blame the load balancer, recreate it, or open a support case about a routing fault. That instinct is almost always wrong. The load balancer is doing exactly what it was built to do, which is route only to instances whose probe succeeds, and a backend marked down is a health check that cannot reach a healthy response, not a load balancer that has misbehaved.

![Fixing Azure Load Balancer health probe failures and unhealthy backends - Insight Crunch](/assets/images/blog/blog-79.webp)

This article diagnoses the failing probe to its root cause and gives you the confirming test and the tested fix for each. By the end you will be able to look at an unhealthy backend, read the one signal Azure exposes that names the cause, and decide in a few minutes whether the check is hitting a blocked source range, a port nothing listens on, a path that returns the wrong status, the wrong protocol entirely, or a health endpoint that has tied its own fate to a downstream dependency that is down. Each of those is a distinct failure with a distinct repair, and the difference between a frustrating afternoon and a five minute correction is knowing which one you have and how to confirm it before you change anything.

## What a failing health probe actually means

A load balancer in Azure does not guess which backend instances are alive. It checks. At a fixed interval it opens a connection to each instance in the backend pool on the port and, for HTTP and HTTPS probes, the path you configured, and it decides from the response whether that instance is healthy. When an instance passes, it stays in rotation and receives its share of new flows. When it fails the configured number of consecutive probes, the load balancer marks it down and stops sending it new connections. The probe is the entire basis of the routing decision. Nothing else feeds into it. The load balancer does not look at CPU, it does not read your application logs, and it does not know whether your code is throwing exceptions deeper in the request. It knows one thing about each instance: did the check succeed.

That single fact is the foundation of every diagnosis in this article, and it deserves a name. Call it the probe-is-the-truth rule: the load balancer routes only to instances whose probe currently succeeds, so a backend marked down is a health check that could not reach a healthy response on the configured port and path, never a load balancer that decided to drop a working instance for no reason. Once you internalize that rule, the diagnosis stops being a hunt through the load balancer configuration and becomes a single, answerable question. What is standing between the check and a successful response on this instance. The answer is one of a small set of causes, and the rest of this article is about telling them apart.

The rule also explains why the symptom is so confusing. The probe and a real client request can take different paths, hit different ports, and traverse different rules. Your own session to the instance, whether through the serial console, a jump box, or a peered network, says nothing about whether the check specifically can reach the configured endpoint. The application can be perfectly healthy from where you stand and completely unreachable to the check, because the check arrives from a particular source address, on a particular port, expecting a particular response, and any one of those can be broken while everything else looks fine. Diagnosing a health-check failure means reproducing the check, not the user, and that is a different test than most engineers run first.

There is one more piece of the model worth holding before we get to causes. Azure exposes two load balancer products with the same probe mechanic but different surrounding behavior. The Standard tier surfaces per instance probe status through Azure Monitor metrics, supports the service tag and explicit network security group rules that govern probe traffic, and is the tier you should assume in any production design. The Basic tier is older, more permissive about network flows by default, and on a path to retirement, so if you are on Basic and seeing odd probe behavior, part of the answer is to plan the move to Standard rather than to tune the old one. The diagnosis below applies to both, but the confirming signals are richer on Standard, and the examples use it.

### How does the load balancer decide a backend is down?

The load balancer sends a health check to each backend on the configured protocol, port, and (for HTTP and HTTPS) path at a set interval. A TCP probe counts a completed handshake as success. An HTTP or HTTPS probe counts only a 200 response as success. After the configured number of consecutive failures, the instance is marked down and removed from rotation until its probe recovers.

This is worth stating precisely because the precision is where the fixes live. A TCP probe succeeds the moment the three way handshake completes; it never inspects what the application does after the socket opens, which is why a TCP probe can report an instance as healthy while the application behind that open port is returning errors to every real request. An HTTP or HTTPS probe is stricter. Regardless of the timeout you configure, an HTTP health check marks the instance down if the server returns any status code other than 200, and it also marks it down if the connection is reset before a response arrives. A 301 redirect fails the check. A 401 fails the check. A 403 fails the check. A 500 fails the check. Only a clean 200 keeps the instance in rotation, which means a health endpoint that returns anything other than a flat 200 under the conditions the check arrives in will pull the instance out even when the application is, from a human perspective, working.

## How to read the signal before you change anything

The fastest way to waste an hour on a health-check failure is to start editing the check configuration before you have read what Azure already tells you. The platform exposes the verdict in more than one place, and reading it first turns a guessing game into a short list. On a Standard Load Balancer, open the resource in the portal and look at the backend pool and the health probe status. Azure Monitor exposes a Health Probe Status metric that you can split by backend instance, so you can see whether one instance is failing or all of them are, and that single split is diagnostic on its own. If one instance is down and the rest are healthy, the cause is local to that instance: its service is not listening, its guest firewall is blocking the check, or it is mid restart. If every instance is down at once, the cause is shared: the network security group rule that should allow the check applies to the whole subnet, the check is pointed at a port or path that no instance serves, or the protocol is wrong for the endpoint.

That one fork, one instance versus all instances, eliminates half the causes before you run a single command. Read it first, every time. You can pull the same metric from the command line so the check is scriptable and repeatable across incidents. Azure Monitor exposes the dimension by backend IP, and querying it gives you the same one instance versus all instances answer without clicking through blades.

```bash
# Read the Health Probe Status metric for a Standard Load Balancer,
# split by backend IP, over the last hour.
az monitor metrics list \
  --resource "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Network/loadBalancers/<lb-name>" \
  --metric "DipAvailability" \
  --dimension "BackendIPAddress" \
  --interval PT1M \
  --start-time "$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)" \
  --output table
```

The `DipAvailability` metric is the per instance probe health on a Standard Load Balancer; a value at or near 100 means the check is succeeding for that instance, and a value at or near 0 means it is failing. Splitting by `BackendIPAddress` gives you the per instance breakdown. When you see the split, you have already narrowed the field. The next step is to reproduce the check from a position that matches where the check arrives from, because the platform metric tells you the check is failing but not why, and the why is on the instance.

To reproduce the check you have to think like the check. It arrives on the instance from the source address the platform uses for health checks, it targets the configured port, and for an HTTP health check it requests the configured path and expects a 200. The cheapest reproduction is to get onto the instance and confirm two things in order: that something is listening on the check port, and that a request to the probe endpoint from the instance itself returns what the probe expects. If the application is not listening on the port, no amount of network rule tuning will help. If it is listening but the path returns a non-200, the network is fine and the endpoint is the problem. Checking listening sockets first saves you from chasing a network ghost when the service simply is not up.

```bash
# On a Linux backend instance: confirm the app is listening on the probe port (example 8080).
ss -ltnp | grep ':8080' || echo "Nothing is listening on 8080"

# From the instance itself, reproduce an HTTP probe to the configured path and read the status code.
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/healthz
```

```powershell
# On a Windows backend instance: confirm a listener on the probe port (example 80).
Get-NetTCPConnection -State Listen -LocalPort 80 -ErrorAction SilentlyContinue

# Reproduce the probe locally and read the status code.
(Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:80/healthz").StatusCode
```

If the local request returns a 200 and a listener is present, the endpoint is healthy and the problem is in the path between the check source and the instance, which points you at the network security group or a guest firewall. If the local request returns a non-200 or the port has no listener, the endpoint itself is the problem and no network change will fix it. This single ordering, platform metric to confirm which instances are failing, then a local listener and status check on a failing instance, resolves most health-check failures to a cause in under five minutes. Everything below is the catalog of what that cause turns out to be and how to repair it.

### Where does Azure show you the probe verdict?

On a Standard Load Balancer the verdict lives in Azure Monitor as the per instance probe health metric and in the portal on the backend pool view. Split the metric by backend instance to see whether one instance or all instances are failing. That split alone separates instance local causes, such as a stopped service, from shared causes, such as a subnet wide rule or a wrong check port.

## The five root causes of a failing probe

Almost every Azure Load Balancer health-check failure reduces to one of five distinct causes, and each one has a different confirming test and a different fix. Naming them and keeping them separate is the whole skill, because the wrong repair for the right symptom wastes time and sometimes makes the situation worse. The five are: the network security group or guest firewall blocks the check source; the probe points at a port nothing is listening on; the HTTP health path returns a status that is not 200; the probe protocol does not match the endpoint; and the health endpoint depends on a downstream component that is itself down. The table below is the InsightCrunch probe-failure table, and it is the artifact to bookmark, because it maps each cause to the test that confirms it is yours and the fix that resolves it.

| Root cause | What it looks like | Confirming test | Fix |
| --- | --- | --- | --- |
| NSG or guest firewall blocks the probe source | All instances behind one subnet go down together; local curl to the endpoint succeeds | Check the effective security rules for the NIC or subnet for an allow on the AzureLoadBalancer service tag to the probe port; check the guest OS firewall | Add an inbound NSG allow rule with source `AzureLoadBalancer` to the probe port; open the port in the guest firewall |
| Probe port has no listener | A single instance, or all instances, with nothing bound to the probe port | `ss -ltnp` on Linux or `Get-NetTCPConnection -State Listen` on Windows shows no listener on the probe port | Point the probe at the port the app actually binds, or start the service on the configured port |
| HTTP probe path returns a non-200 | Listener present, network open, but the probe still fails | `curl -w "%{http_code}"` against the probe path from the instance returns 301, 401, 403, or 500 | Make the probe path return a flat 200 with no redirect or auth, or repoint the probe at a dedicated health route |
| Protocol mismatch | A TCP probe reports healthy while users get errors, or an HTTP probe fails on a non HTTP port | Compare the configured probe protocol against what the port actually speaks | Use an HTTP probe with a real health path for HTTP services; reserve TCP probes for genuinely non HTTP listeners |
| Health endpoint depends on a downstream that is down | All instances fail together exactly when a database, cache, or dependency degrades | The probe path runs a deep check that calls a dependency; the dependency is down | Make the probe a shallow liveness check; move dependency checks to a separate readiness signal that does not pull the whole pool |

Read the table top to bottom against the signal you already gathered. If all instances went down together and your local curl succeeds, you are on row one. If a listener is missing, row two. If the listener is present and the path returns a non-200, row three. If a TCP probe is masking a broken application or an HTTP health check is aimed at a port that does not speak HTTP, row four. If the whole pool dropped at the exact moment a dependency degraded, row five. The sections that follow take each row in turn, with the reproduction, the confirming command, and the tested repair.

## Cause one: the network security group or guest firewall blocks the probe

This is the single most common health-check failure in production, and it is the one engineers misdiagnose most often, because the application is genuinely healthy and a local request to the endpoint succeeds, which makes the load balancer look broken. It is not. The probe arrives at the instance from a specific platform source, and a network security group or a guest operating system firewall is dropping that source before it ever reaches the listener. The probe never gets a response, the load balancer counts consecutive failures, and the instance falls out of rotation while looking perfectly fine to anyone signed in to it.

The source the probe uses is the key fact, and Azure makes it concrete. All IPv4 health probes originate from the address 168.63.129.16, a special platform virtual IP that Azure uses for several host to guest functions including DNS, the instance metadata service, and load balancer probes. In network security group rules you do not have to hardcode that address; Azure provides the `AzureLoadBalancer` service tag, which resolves to the check source and lets you write a rule that allows probe traffic without pinning a literal IP. The default network security group ruleset includes an allow for this tag, which is why probes often work until someone tightens the rules and removes or overrides that default allow with a deny that catches the check source as collateral. The moment a deny rule with a lower priority number, and therefore higher precedence, matches the probe traffic before the AzureLoadBalancer allow does, every instance under that rule goes down together.

### Why does the NSG block the load balancer probe?

The probe arrives from the platform source identified by the `AzureLoadBalancer` service tag, resolving to 168.63.129.16. If a network security group has no allow rule for that source to the check port, or a higher priority deny rule matches it first, the probe is dropped before it reaches the listener. The instance then fails consecutive probes and the load balancer removes it from rotation.

Confirming this cause takes one command. Ask Azure for the effective security rules applied to the network interface of a failing instance and look for whether probe traffic to the check port is allowed. The effective rules view collapses the subnet level and NIC level network security groups into the actual decision the platform will make, so you are reading the real outcome rather than guessing from two separate rule sets.

```bash
# Show the effective NSG rules on a backend NIC and search for the probe allow.
az network nic list-effective-nsg \
  --name "<nic-name>" \
  --resource-group "<rg>" \
  --output json | grep -i -A3 -E "AzureLoadBalancer|Deny"
```

If the output shows that an inbound deny rule with a lower priority number matches the check source or the check port, or shows no allow for the `AzureLoadBalancer` tag at all, you have confirmed the cause. The repair is to add an explicit inbound allow rule for the probe, with a priority high enough (a low enough number) to win against any deny that would otherwise catch it. Allow the `AzureLoadBalancer` service tag as the source, the check port as the destination, and the protocol the probe uses.

```bash
# Add an inbound allow for the load balancer probe ahead of any blanket deny.
az network nsg rule create \
  --resource-group "<rg>" \
  --nsg-name "<nsg-name>" \
  --name "Allow-LB-HealthProbe" \
  --priority 200 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefixes "AzureLoadBalancer" \
  --source-port-ranges "*" \
  --destination-address-prefixes "*" \
  --destination-port-ranges "8080"
```

A network security group is only half of the picture. The guest operating system has its own firewall, and a health check that clears the network security group can still be dropped inside the instance by Windows Defender Firewall or by an iptables, nftables, or firewalld rule on Linux. When the effective network security group rules show the probe allowed but the instance is still down, move the investigation inside the box. On Linux, confirm that the guest firewall is not dropping inbound traffic to the check port; on Windows, confirm the equivalent inbound rule exists. The check source, 168.63.129.16, must be permitted to reach the check port both at the network security group and at the guest firewall, because either one dropping it produces the identical symptom of an instance that is healthy locally and down to the load balancer.

```bash
# Linux: confirm the guest firewall is not blocking the probe port (example firewalld).
sudo firewall-cmd --list-ports
# Open the probe port if it is missing.
sudo firewall-cmd --permanent --add-port=8080/tcp && sudo firewall-cmd --reload
```

```powershell
# Windows: confirm an inbound allow exists for the probe port and add one if needed.
Get-NetFirewallRule -Direction Inbound -Enabled True |
  Where-Object { $_.DisplayName -like "*8080*" }
New-NetFirewallRule -DisplayName "Allow LB Probe 8080" -Direction Inbound `
  -LocalPort 8080 -Protocol TCP -Action Allow
```

One subtle trap deserves a warning. Azure documents that you should not block the check source with network security group rules as a way of mass marking instances down, because doing so is an unsupported pattern that can make rule changes take delayed effect and cause the probe to report stale availability. If you ever want to deliberately remove an instance from rotation, change the backend pool membership or the application's own health response rather than reaching for a deny rule on the check source. The probe-allow rule should be a stable allow, not a knob you toggle. If you are wrestling with network security group precedence in general, the same priority and effective rules reasoning that fixes a health check block is the reasoning that resolves the broader class of unexpectedly dropped traffic, and working through how an NSG silently blocks legitimate flows makes the probe case fall out as a special instance of a pattern you will see again. You can sharpen the muscle by deliberately breaking and repairing this exact rule in a lab; one good way to practice the full sequence is to [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) and watch the probe go red the moment the deny rule wins, then green again the moment the allow takes precedence.

## Cause two: the probe points at a port nothing is listening on

The second cause is the simplest to confirm and the easiest to overlook, because it hides behind an assumption. The probe is configured to check a port, and the application is assumed to be listening on that port, and the assumption is wrong. Maybe the application binds to a different port than the one the probe targets. Maybe the service that should bind the port failed to start, or started and then crashed, or is bound only to the loopback interface and not to the address the probe reaches. In every variation the result is the same: the probe opens a connection to the port, finds nothing accepting, and counts a failure.

When this is the cause, the local listener check from the diagnosis section is the entire confirmation. Get onto a failing instance and ask the operating system what is listening. If the probe targets port 8080 and nothing is bound to 8080, you have found it. If something is bound to 8080 but only on 127.0.0.1, the probe still fails, because the probe arrives on the instance's network address, not the loopback, and a service bound only to loopback is invisible to anything off the box. The distinction between a missing listener and a loopback only listener matters because the fixes differ: a missing listener means starting or repairing the service, while a loopback only listener means changing the bind address to 0.0.0.0 or the instance's address so the probe can reach it.

```bash
# Linux: see exactly what address and port the app is bound to.
ss -ltnp
# A healthy line for an off-box probe looks like:  LISTEN 0 4096 0.0.0.0:8080
# A loopback-only bind that defeats the probe looks like:  LISTEN 0 4096 127.0.0.1:8080
```

```powershell
# Windows: list listeners with their local address.
Get-NetTCPConnection -State Listen |
  Select-Object LocalAddress, LocalPort, OwningProcess |
  Sort-Object LocalPort
```

The fix has two branches and you choose by which side is wrong. If the application is correctly listening on the port it should and the probe is simply pointed at the wrong number, repoint the probe at the real port; that is a load balancer side change to the probe configuration. If the check port is correct and the application is not listening there, the application side is wrong, so start the service, fix its bind address, or correct the configuration that put it on the wrong port. Repointing the probe is the right move only when the application genuinely serves health on a different port than the probe was configured for; it is the wrong move when the real problem is a stopped service, because pointing the probe at a port that also has no listener just moves the failure. Confirm the listener exists first, then decide which side to change.

```bash
# Load balancer side fix: repoint the probe at the port the app actually serves (example 80).
az network lb probe update \
  --resource-group "<rg>" \
  --lb-name "<lb-name>" \
  --name "<probe-name>" \
  --port 80
```

A worked version of this cause shows how cleanly it resolves. Suppose every instance in a backend pool reports unhealthy after a deployment. The Health Probe Status metric shows all instances at zero, which points at a shared cause rather than a single sick instance. A local curl to the health path on one instance fails to connect, and `ss -ltnp` shows the application bound to port 5000 while the probe is configured for 8080. The deployment changed the application's listen port and the probe configuration was not updated to match. Repointing the probe to 5000 brings every instance back into rotation within a couple of probe intervals. No load balancer recreate, no support case, no restart loop, just a port number reconciled between two places that drifted apart.

## Cause three: the HTTP probe path returns a status that is not 200

The third cause appears only with HTTP and HTTPS probes, and it catches engineers who have correctly opened the network and confirmed a listener, then cannot understand why the probe still fails. The answer is the strictness of the HTTP health check contract. An HTTP or HTTPS probe treats only a 200 as success. Any other status code marks the instance down, and that includes status codes that a human would read as the application working fine. A 301 or 302 redirect, which is what many web frameworks return when they push HTTP to HTTPS or add a trailing slash, fails the probe. A 401 or 403, which is what an authenticated application returns when an unauthenticated probe hits a protected route, fails the probe. A 404 on a health path that does not exist fails the probe. Even a 500 from a health endpoint that runs a heavy check and times out internally fails the probe.

The confirmation is the local status check, read carefully. From a failing instance, request the exact path the probe is configured for and read the status code, not the page content. A page that renders in a browser can still be a 301 to the browser's eye that the browser silently follows; the probe does not follow redirects, so the 301 is a failure even though a human never sees it. Read the raw code.

```bash
# Read the exact status code the probe will see, without following redirects.
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/

# If you suspect a redirect, see it explicitly.
curl -s -I http://localhost:8080/ | head -n 1
```

If that returns anything other than 200, you have the cause, and the fix is to give the probe a path that returns a flat 200 under the conditions the probe arrives in. The clean pattern is a dedicated health route, often named `/healthz` or `/health`, that is exempt from authentication, does not redirect, and returns 200 with a trivial body whenever the process is able to serve. Repoint the probe at that route and the failure clears.

```bash
# Repoint an HTTP probe at a dedicated, unauthenticated, redirect-free health path.
az network lb probe update \
  --resource-group "<rg>" \
  --lb-name "<lb-name>" \
  --name "<probe-name>" \
  --protocol Http \
  --port 8080 \
  --path "/healthz"
```

The redirect variant deserves its own emphasis because it is so common and so invisible. An application configured to redirect all HTTP traffic to HTTPS will answer the probe's HTTP request with a 301 to the HTTPS URL. The probe sees the 301, counts a failure, and the instance goes down even though the application is serving HTTPS perfectly. The fix is not to disable the redirect, which you usually want for real clients, but to exempt the health path from it so the probe gets its 200 while every other path still redirects. If you would rather probe over HTTPS to match production exactly, switch the probe to the HTTPS protocol and ensure the instance presents a certificate the probe will accept; an HTTPS probe still requires a 200 and is subject to the same status strictness, with the added requirement that the TLS handshake completes.

## Cause four: the protocol does not match the endpoint

The fourth cause is a mismatch between the probe protocol and what the endpoint actually speaks, and it produces two opposite and equally misleading symptoms. The first is a false negative: an HTTP health check is configured against a port that does not speak HTTP, so the probe sends an HTTP request, the listener does not answer with a valid HTTP response, and the probe fails even though the service on that port is healthy for its own protocol. A database listener, a custom binary protocol, or a raw TCP service will all defeat an HTTP health check pointed at them, because they were never going to return a 200 to an HTTP request. The fix is to use a TCP probe for a genuinely non HTTP listener, since a TCP probe asks only whether the socket accepts a connection and does not impose the HTTP status contract.

The second symptom is the more dangerous one, a false positive: a TCP probe is configured against an HTTP application, the TCP handshake completes because the web server is accepting connections, the probe reports the instance healthy, and yet every real request returns a 500 because the application behind the open socket is broken. The TCP probe never looked past the handshake, so it cannot tell a working application from a broken one that still accepts connections. The instance stays in rotation, serving errors to clients, while the probe insists everything is fine. This is the case where the probe-is-the-truth rule has a sharp edge: the probe is telling the truth about what it checked, but what it checked was too shallow to catch the failure. The fix is to use an HTTP health check with a real health path for any HTTP service, so the probe's notion of healthy actually matches the client's notion of healthy.

### Should I use a TCP or HTTP health probe?

Use an HTTP or HTTPS probe with a dedicated health path for any HTTP service, because a TCP probe only confirms the socket accepts connections and will report a broken application as healthy. Reserve TCP probes for genuinely non HTTP listeners, such as databases or custom protocols, where there is no HTTP status to evaluate and the handshake is the only meaningful liveness signal available.

There is a small but real operational detail inside the HTTP health path that bites people who pick low numbered ports. The probe's HTTP client, on the platform side, refuses a specific set of ports for HTTP health checks for historical security reasons, and configuring an HTTP health check on one of them fails silently in a way that looks like a mismatch. The restricted ports for HTTP probes are 19, 21, 25, 70, 110, 119, 143, 220, and 993. If you have an HTTP health check configured on one of those, move the health endpoint to a normal application port such as 80, 8080, or a high numbered port, and the probe will work. This is rare, because few applications serve health on those legacy ports, but when it happens it is maddening precisely because every other check passes.

Confirming a protocol mismatch is a matter of comparing the configured probe protocol against what the port actually does. Read the probe configuration, then test the port with the protocol you think it speaks. If an HTTP health check is failing, try a raw TCP connection to see whether the socket is even open, and try an HTTP request to see whether it answers HTTP. If the socket opens but HTTP gets no valid response, the port is not HTTP and the probe protocol is wrong. If you are deciding between a layer 4 load balancer with these probe semantics and a layer 7 service that understands HTTP natively and gives you richer routing, that decision has its own trade-offs worth reading separately; the comparison of [the layer 4 load balancer against Application Gateway](/2023/10/02/load-balancer-vs-app-gateway/) lays out when the deeper HTTP awareness justifies the move and when a TCP or HTTP health check on a load balancer is the simpler right answer.

```bash
# Is the socket open at all (TCP-level reachability)?
nc -zv <backend-ip> 8080

# Does it actually answer HTTP, or just accept the socket?
curl -s -o /dev/null -w "%{http_code}\n" http://<backend-ip>:8080/healthz
```

## Cause five: the health endpoint depends on a downstream that is down

The fifth cause is the most architecturally interesting and the one most likely to take an entire fleet down at once for a reason that has nothing to do with the load balancer. The health path runs a deep health check that, before returning 200, verifies that a database is reachable, a cache responds, or some other downstream dependency is healthy. The intent is good: do not route traffic to an instance that cannot actually serve a request. The failure mode is brutal. When the shared dependency degrades, every instance's deep health check fails simultaneously, every probe returns a non-200, the load balancer marks the entire backend pool down, and the application goes from degraded to completely unavailable because there are now zero healthy instances in rotation. A dependency hiccup that should have caused slow or partial errors instead causes a total outage, and the load balancer, faithfully applying the probe-is-the-truth rule, is the mechanism that amplified it.

You confirm this cause by correlation and by reading the health endpoint's code. If the entire pool dropped at the exact moment a database, cache, or external service degraded, and the health path is known to call that dependency, you have it. The metric shows all instances failing in lockstep, which already pointed at a shared cause, and the timing lines up with the dependency event rather than with any change to the instances or the network. The repair is a design change rather than a configuration toggle, and it is the right change regardless of how you got here: separate liveness from readiness. The load balancer probe should hit a shallow liveness endpoint that returns 200 whenever the process itself is up and able to accept work, without calling any downstream dependency. A separate, deeper readiness check can exist for orchestration or for application logic, but it must not be the thing that decides whether the load balancer keeps the instance in rotation, because a shared dependency failing should degrade the application, not delete the entire backend pool.

```python
# A shallow liveness endpoint for the load balancer probe: returns 200 whenever the
# process can serve, with no downstream dependency call that could take the whole pool down.
from http import HTTPStatus

def healthz(request):
    # Liveness: the process is up and the event loop is responsive.
    # Deliberately does NOT check the database, cache, or any external dependency.
    return ("ok", HTTPStatus.OK)

def readyz(request):
    # Readiness: a separate, deeper check used by orchestration or app logic,
    # NOT wired to the load balancer probe, so a downstream blip degrades rather
    # than deletes the backend pool.
    if database_reachable() and cache_reachable():
        return ("ready", HTTPStatus.OK)
    return ("not ready", HTTPStatus.SERVICE_UNAVAILABLE)
```

The principle generalizes beyond load balancers. Any health check that gates traffic should be as shallow as the routing decision it informs, because a health check that fails for reasons broader than "this specific instance cannot serve" turns a localized problem into a fleet wide one. The deep check still has value as a signal you alert on and as a readiness gate during rollout, but the thing the load balancer reads to decide rotation should answer one narrow question about one instance. Getting this boundary right is the difference between a dependency outage that costs you some failed requests and one that costs you the whole site, and reasoning through it under realistic failure conditions is exactly the kind of practice that builds the instinct; you can rehearse the cascade and its fix by working through [scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html), where you take a pool down with a deep probe and bring it back by splitting liveness from readiness.

## Putting the table to work: a full diagnosis from symptom to fix

A complete walkthrough ties the five causes together into a single repeatable method, because in a real incident you do not know which cause you have, and the value is in the order you check rather than in any one command. Start with the platform signal. Open the Health Probe Status metric and split it by backend instance. The first decision is one instance or all instances. Suppose the metric shows all instances at zero, which points away from a single sick instance and toward a shared cause, which is causes one, two, four, or five.

Next, reproduce the probe locally on one failing instance. Confirm a listener on the check port, then request the health path and read the raw status code. Suppose the listener is present and a local request to the path returns 200. That clears cause two, because the listener exists, and cause three, because the path returns 200, on the instance itself. A healthy local response with an unhealthy probe verdict is the signature of cause one, the network path between the check source and the instance is blocked. Pull the effective network security group rules for the instance's interface and look for the AzureLoadBalancer allow. Suppose you find a recently added deny rule at priority 100, ahead of the AzureLoadBalancer allow at priority 300, and the deny matches the check port. There is the cause, named and confirmed. Add an allow for the AzureLoadBalancer service tag at priority 90, ahead of the deny, and within a few probe intervals every instance returns to rotation. Total elapsed time, a few minutes, because each step eliminated a set of causes rather than guessing among all of them.

Now suppose a different branch. The metric shows all instances down, the listener is present, but the local request returns 301. Cause two is cleared by the listener, cause one is unlikely because the request connected, and the 301 is the signature of cause three. The application redirects HTTP to HTTPS and the probe's plain HTTP request gets the redirect. Exempt the health path from the redirect or move the probe to HTTPS, and the instances recover. Or suppose the metric shows all instances healthy yet users report errors; that paradox is the signature of cause four's false positive, a TCP probe over a broken HTTP application, and the fix is to switch to an HTTP health check with a real health path so the probe's verdict matches the client's experience. The method is always the same: platform signal first to count failing instances, local reproduction second to separate endpoint problems from network problems, and the specific confirming command for whichever cause the first two steps point at. The table is the map and the order is the route.

This method is also what makes a health-check failure teachable rather than mysterious, and it is why the load balancer rarely deserves the blame it gets. The probe is a precise instrument reporting a precise fact, and the fact is always actionable once you read it in the right order. The broader Azure traffic model, how packets reach an instance, how rules are evaluated, and where the platform inserts itself, is the context that makes all five causes obvious rather than surprising, and grounding yourself in [the fundamentals of how Azure networking moves traffic](/2023/08/28/azure-networking-fundamentals/) turns probe diagnosis from a checklist you memorize into a model you reason from.

## What each health-check setting actually controls

The configuration of a health check is small, four or five values, and understanding what each one does removes a lot of guesswork from both diagnosis and prevention. The protocol decides what counts as success: TCP asks only for a completed handshake, while HTTP and HTTPS require a 200 on a path. The port decides where the check connects, and it must match where the application listens, which is the reconciliation that cause two is about. For HTTP and HTTPS, the path decides which route the check requests, and it must return a flat 200, which is what cause three turns on. The interval decides how often the check runs, and the count of allowed failures decides how many consecutive misses trigger removal. Those last two together set the reaction time and the noise tolerance, and tuning them is the difference between a pool that flaps on transient blips and one that is slow to shed a dead instance.

Each setting maps to a failure you have already met. A wrong protocol is cause four, the mismatch between what the check expects and what the endpoint speaks. A wrong port is cause two, the check connecting where nothing listens. A path that returns anything but 200 is cause three. An interval and failure count set too tight produce the transient flapping that a deployment or a restart triggers, while set too loose they leave a genuinely broken instance serving errors longer than it should. Reading a failure backward from the setting it implicates is often faster than reading it forward from the symptom, because the configuration is a short, fixed list and each entry has exactly one failure mode it can produce.

The values that age are the interval and the failure count, because the right setting depends on how your application actually behaves, and that changes as the application changes. An application that used to answer its health route in single digit milliseconds and now sometimes takes longer, because it grew a heavier startup or a more expensive route, will start flapping under an interval that was comfortable a year ago. The fix is not a one time tuning but a periodic check that the interval still rides over the application's real response variability with margin to spare. The protocol, port, and path, by contrast, are correctness values rather than tuning values: they are either right or wrong, and when they are wrong the check fails completely rather than intermittently, which is why a steady failure points at one of those three and a flapping failure points at the interval and count.

One configuration mistake deserves a specific warning because it is silent. If the health route and the route that serves real traffic are the same path, then a change to that path's behavior, a new redirect, a new authentication requirement, a new dependency call, silently changes the health verdict as a side effect, and an unrelated application change takes the pool down. Giving the check its own dedicated route, separate from any route real clients use, isolates the health verdict from application changes that were never meant to affect it, which is why the dedicated health path is a recurring recommendation across every cause in this article rather than a detail of any one of them.

## Internal load balancers run the same check, with one twist

Everything above applies whether the load balancer is public, with a frontend on a public IP, or internal, with a frontend on a private address inside the virtual network. The health check mechanic is identical: the platform sends a request from the same source to the configured port and path, and a clean response keeps the instance in rotation. The one twist with an internal load balancer is that engineers reach for it precisely when they want traffic to stay private, and that desire to lock things down is exactly what produces the network security group blocks of cause one. A team that builds an internal load balancer to keep a service off the public internet often writes a tight inbound ruleset that allows traffic only from a known application subnet, and that ruleset, written for client traffic, forgets the platform source the health check arrives from. The result is the classic symptom: a private service that is healthy locally, reachable from its intended clients on the application subnet, and yet marked down by the load balancer because the health check source was never in the allow list.

The fix is identical to cause one, an explicit allow for the platform health source ahead of any blanket deny, but the lesson is worth drawing out because it recurs every time a team tightens an internal design. The allow for the platform source is not a loosening of your security posture; the source is a Microsoft owned virtual IP that is not routable from the internet and originates only from Azure's internal infrastructure, so allowing it to reach the health port does not expose the service to anyone. Treat that allow as a fixed part of the internal load balancer pattern rather than as an exception you grant reluctantly, and the internal variant stops producing surprises. The same reasoning extends to a load balancer fronting a service that other rules restrict heavily, such as a database tier or an internal API, where the instinct to permit nothing by default collides hardest with the platform's need to verify health.

There is a related private networking case that masquerades as a health failure. When the backend service itself reaches a dependency over a private endpoint and that endpoint's name does not resolve, a deep health route that calls the dependency fails, and the whole pool drops in the cause five pattern even though nothing about the load balancer or its source allow is wrong. The underlying problem there is resolution, not the check, and keeping the health route shallow removes the overlap, but it is worth recognizing the shape so you do not chase a network security group rule when the real fault is a private DNS zone that is not linked to the virtual network. The private endpoint resolution chain is its own diagnosis, and a deep readiness route that depends on it is a good reason to keep that route off the load balancer entirely.

## How the check behaves with Virtual Machine Scale Sets

Most production load balancers front a Virtual Machine Scale Set rather than a fixed set of individually managed instances, and the scale set adds behavior worth understanding because it interacts with the health verdict in ways that change what a failure means. A scale set can use the load balancer health signal, or its own application health extension, as the definition of instance health that drives automatic repair. When that wiring is in place, an instance that fails its health check is not merely pulled from rotation; it can be automatically reimaged or replaced by the scale set's repair policy, on the theory that an unhealthy instance should be healed rather than left in place. That is powerful and usually correct, but it turns a misconfigured health route into a destructive loop. If the health check fails for a configuration reason rather than a real fault, such as a wrong port or a non-200 path, the scale set sees a perpetually unhealthy instance, repairs it, the replacement comes up with the same misconfiguration, fails the same check, and gets repaired again. The pool churns endlessly, each instance healthy in itself and condemned by a check it can never pass.

The signature of this loop is instances that cycle through provisioning states while the health metric never stabilizes, and the diagnosis is the same five cause search applied to the route the scale set health is reading. The danger is that the automatic repair masks the real cause by constantly replacing the evidence, so the discipline is to pause automatic repair while you diagnose, reproduce the check on a held instance, find which of the five causes is in play, fix it in the scale set model so every future instance inherits the correction, and then resume repair. Pausing repair is the step engineers skip, and skipping it means debugging a target that is being deleted and recreated underneath you, which is its own special frustration.

The second scale set nuance is rolling upgrades. When a scale set rolls out a new model version in batches, it relies on the health signal to decide whether a batch came up healthy before it proceeds to the next. A health route that is slow to return 200 after a fresh instance boots, because the application takes time to warm up, can stall a rolling upgrade or, worse, cause the upgrade to judge a batch unhealthy and pause or roll back. The cure is to make the health route reflect readiness to serve as soon as the process can serve, and to set the check interval and the grace period so a normal warm up does not read as a failure. A health route that returns 200 only after a long initialization is indistinguishable, to the load balancer and the scale set, from an instance that is genuinely broken, and the two deserve different responses.

## Watching the health check arrive at the instance

When the platform metric says the check is failing and a local request to the route succeeds, the missing link is whether the check traffic is actually arriving at the instance, and you can watch for it directly. The check arrives from the platform source on the configured port, so a packet capture filtered to that source and port tells you definitively whether the traffic reaches the network interface. If you see the inbound connection attempts arriving and being answered, the network path is open and the fault is at the application or the response. If you see the attempts arriving and getting no answer, something inside the instance, the guest firewall or a service bound to the wrong address, is dropping or ignoring them. If you see nothing arriving at all, the traffic is being dropped upstream, which points squarely at a network security group rule.

```bash
# Linux: watch for health check traffic arriving from the platform source on the probe port.
sudo tcpdump -ni any "src host 168.63.129.16 and dst port 8080"
# Connection attempts that arrive and get a SYN-ACK back mean the path is open and the app answers.
# Attempts that arrive with no response mean a guest firewall or wrong bind is dropping them.
# No packets at all mean an NSG is dropping the traffic before it reaches the NIC.
```

```powershell
# Windows: capture briefly to a file and inspect, or use Get-NetTCPConnection to see the active flow.
# Start a capture (requires the netsh trace facility), reproduce the window, then stop and read it.
netsh trace start capture=yes tracefile=C:\probe.etl
# ... wait one or two probe intervals ...
netsh trace stop
```

The capture resolves the ambiguity that the platform metric alone cannot. The metric tells you the verdict, failing or passing, but not the stage at which the failure happens, and the three stages, dropped upstream, dropped inside the box, or answered with the wrong response, map to three different causes and three different fixes. Reading the capture is the most direct way to assign the failure to a stage, and it is worth doing when the faster checks have not been conclusive, because it converts a guess into an observation. It is also the way to settle an argument about whether a network security group is the culprit, since the presence or absence of the check packets at the interface is not a matter of opinion.

A lighter weight version of the same observation uses connection counters rather than a full capture. On the instance you can watch the count of inbound connections on the check port over a few intervals; a steadily incrementing count means the check is arriving and connecting, while a flat count means it is not reaching a listener. This is cruder than a capture but faster to read, and for the common case of confirming that traffic does or does not arrive it is often enough. The point of either tool is the same: stop inferring from the verdict and start observing the traffic, because the traffic does not lie about which stage is failing.

## Why deployments and restarts trigger transient failures

A large share of health check failures are not steady state misconfigurations but transient events around a deployment or a restart, and they deserve their own treatment because the fix is different from the five causes. When you deploy a new version, the application stops, the new version starts, and there is a window during which the process is not yet listening or not yet ready to return 200. If the check interval and the failure threshold are tight, the load balancer counts failures during that window and pulls the instance out, which is correct behavior but can look alarming if you did not expect a deployment to flap the health verdict. The instance returns to rotation as soon as the new version is up and answering, so a brief drop during a deploy is often benign, but it becomes a real outage if you deploy to every instance at once and the whole pool is in its restart window simultaneously.

The discipline that prevents a deploy from becoming an outage is to deploy in a way that keeps a healthy quorum in rotation at all times, never restarting more instances than the pool can lose while still serving, and to make the new version come up to a 200 on the health route as fast as it can serve real traffic. A health route that returns 200 the moment the process can accept work, rather than after a long warm up, shortens the window during which a freshly started instance reads as failing, which both speeds the return to rotation and reduces the chance that a rolling deploy stalls. Where the application genuinely needs warm up time before it should take traffic, that is a readiness concern, and the right tool is a readiness gate that holds the instance out of rotation until warm up completes, distinct from the liveness check that the load balancer reads, so the two notions of ready do not blur.

Restarts that are not deploys produce the same transient pattern. A platform maintenance event, an operating system update that reboots the instance, or a crash and automatic restart all create a window where the check fails legitimately because the instance truly cannot serve for a moment. These are the cases the failure threshold exists for: a threshold of two or three consecutive failures rides over a single missed interval from a momentary blip while still reacting promptly to a sustained failure. Setting the threshold to one makes the load balancer maximally twitchy, evicting instances for transient noise, while setting it very high makes the pool slow to shed a genuinely dead instance. The judgment is to ride over the noise you expect, the brief windows of a restart or a garbage collection pause, without riding over a real failure long enough to serve a meaningful number of errors to clients.

## The outbound and SNAT picture is separate from the health verdict

A recurring source of confusion is conflating an inbound health failure with an outbound connectivity problem, because both can make an application appear broken behind a load balancer, and they are entirely different mechanisms with different fixes. The health check is purely inbound: the platform reaches into the instance to verify it can serve. Outbound connectivity, by contrast, is how the instance reaches the rest of the world, and on a Standard Load Balancer outbound flows consume source network address translation ports from a finite pool. When an instance exhausts its allocated outbound ports under heavy connection churn, its outbound calls start failing, which can make a deep health route that calls an external dependency fail, which then looks like an inbound health problem when the root cause is outbound port exhaustion.

The way to keep these separate in diagnosis is to notice which direction the failure lives in. If the instance cannot be reached by the check, that is inbound and lands in the five causes above. If the instance is reached fine but its own outbound calls fail, that is the SNAT and outbound rule picture, and it is fixed by provisioning adequate outbound ports through an outbound rule or a separate egress path, not by touching the health check at all. The overlap appears only when a deep health route ties the inbound verdict to an outbound dependency, which is one more argument for the shallow liveness route: a liveness check that does not make outbound calls cannot be dragged down by outbound port exhaustion, so it keeps reporting the instance healthy for what the load balancer actually needs to decide, which is whether to send it inbound traffic.

Recognizing the boundary matters because the fixes pull in opposite directions. The inbound health failure is fixed by allowing the platform source and ensuring a 200 on the route. The outbound exhaustion is fixed by giving the instance more outbound capacity. Applying the outbound fix to an inbound problem, or the reverse, wastes effort and leaves the real cause untouched. The clean mental model is that the load balancer makes two independent kinds of decision, where to send inbound flows based on the health check, and how outbound flows leave based on the outbound rules, and a health check diagnosis is concerned only with the first.

## How to prevent probe failures from recurring

Prevention is mostly about removing the gaps where a health check and a backend can drift apart, and the most effective single practice is to define the load balancer, the probe, the backend pool, and the network security group rules together as infrastructure as code, so the check port, the listener port, and the allow rule cannot drift out of sync through manual edits. When the probe configuration lives in the same template as the rule that allows the check source, a change to one forces a review of the other, and the most common cause, a tightened network security group that silently catches the probe, becomes visible in a diff rather than discovered in an incident. The Bicep below shows the shape: a health check, a rule that uses it, and a network security group allow for the AzureLoadBalancer service tag, all in one place.

```bicep
// A health probe, a load balancing rule that uses it, and the NSG allow
// for the probe source, declared together so they cannot drift apart.
resource probe 'Microsoft.Network/loadBalancers/probes@2023-09-01' = {
  name: '${lbName}/healthz-probe'
  properties: {
    protocol: 'Http'
    port: 8080
    requestPath: '/healthz'
    intervalInSeconds: 5
    numberOfProbes: 2
  }
}

resource probeAllow 'Microsoft.Network/networkSecurityGroups/securityRules@2023-09-01' = {
  name: '${nsgName}/Allow-LB-HealthProbe'
  properties: {
    priority: 200
    direction: 'Inbound'
    access: 'Allow'
    protocol: 'Tcp'
    sourceAddressPrefix: 'AzureLoadBalancer'
    sourcePortRange: '*'
    destinationAddressPrefix: '*'
    destinationPortRange: '8080'
  }
}
```

The same intent expressed in Terraform keeps the health route, the rule that uses it, and the source allow in one module, so a reviewer sees all three together and a drift in any one is visible in the plan output before it ever reaches production. Declaring them as a unit is the structural defense against the most common cause, the source allow that someone removes or overrides without realizing it gates every instance in the pool.

```hcl
# Terraform: the health check, the rule that consumes it, and the NSG allow,
# kept in one module so the three cannot silently drift apart.
resource "azurerm_lb_probe" "healthz" {
  loadbalancer_id     = azurerm_lb.this.id
  name                = "healthz-probe"
  protocol            = "Http"
  port                = 8080
  request_path        = "/healthz"
  interval_in_seconds = 5
  number_of_probes    = 2
}

resource "azurerm_network_security_rule" "allow_lb_probe" {
  name                        = "Allow-LB-HealthProbe"
  priority                    = 200
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_address_prefix       = "AzureLoadBalancer"
  source_port_range           = "*"
  destination_address_prefix  = "*"
  destination_port_range      = "8080"
  resource_group_name         = azurerm_resource_group.this.name
  network_security_group_name = azurerm_network_security_group.this.name
}
```

Beyond the template, three habits prevent the recurring cases. First, design the health endpoint as a shallow liveness check from the start, so cause five can never take the pool down, and keep any dependency aware readiness check on a separate route that does not feed the probe. Second, expose the check port consistently across deployments and treat a change to the application's listen port as a change that must update the probe, ideally enforced by the shared template rather than by memory. Third, alert on the per instance probe health metric so that a single instance falling out of rotation is noticed before a second one does, because the difference between one unhealthy instance and a pattern is the early warning that something systemic is starting. An alert on the probe metric also catches the slow cases that the deep dependency check would otherwise hide, such as a certificate that is about to expire on an HTTPS probe or a guest firewall rule that drifts after a base image update.

The probe interval and the failure threshold are worth tuning deliberately rather than leaving at defaults. A short interval with a low failure count makes the load balancer react quickly to a real failure but also makes it twitchy about a transient blip, pulling an instance out for a single missed probe that recovers immediately. A longer interval or a higher threshold makes the pool more stable but slower to evict a genuinely failing instance. The right setting depends on how fast your instances genuinely fail and recover, and the way to choose it is to measure how your application behaves under a real restart or a real dependency blip rather than guessing, then set the interval and threshold so the load balancer reacts to sustained failure without flapping on noise.

## Reading the health metric over time, not just right now

A single glance at the current health verdict tells you the state this instant, but the shape of the verdict over time is what separates a steady misconfiguration from a flapping instance from a dependency event, and those three patterns call for different responses. A steady failure, where the metric sits at zero for an instance or the whole pool from a clear starting moment, is a configuration or a hard fault and maps to the five causes directly. A flapping pattern, where an instance oscillates between healthy and unhealthy on a short cycle, points at something marginal: a check interval too tight for an application that has occasional slow responses, a garbage collection pause that briefly stops the process answering, or an instance under enough load that it sometimes misses a response window. A sudden simultaneous drop across the whole pool that correlates with an external event is the dependency signature of cause five. You cannot tell these apart from a point in time reading; you need the time series.

On a Standard Load Balancer the health signal flows into Azure Monitor, and querying it as a time series over the incident window gives you the pattern rather than the snapshot. If you route the metric and the relevant resource logs into a Log Analytics workspace, you can express the read as a query that buckets the verdict per instance over time and surfaces flapping and correlated drops, which is far more diagnostic than the live blade. The query below sketches the shape: bucket the availability signal into short windows per backend address and look at how it moves, so a flap shows up as oscillation and a dependency event shows up as a synchronized cliff.

```kusto
// Health verdict per backend instance over the incident window, bucketed to expose
// flapping (oscillation) versus a steady drop versus a synchronized pool-wide cliff.
AzureMetrics
| where ResourceProvider == "MICROSOFT.NETWORK"
| where MetricName == "DipAvailability"
| where TimeGenerated between (ago(2h) .. now())
| summarize avg_availability = avg(Average) by bin(TimeGenerated, 1m), BackendIPAddress = tostring(Dimensions.BackendIPAddress)
| order by TimeGenerated asc
```

Reading the result is the skill. An instance whose availability marches between near zero and near one hundred on a tight cycle is flapping, and the response is to widen the interval or the failure threshold, or to fix the marginal slowness that causes the misses, rather than to treat it as a hard failure. A flat zero from a clean edge is a hard failure to diagnose with the five causes. A pool wide synchronized drop aligned to the minute a dependency degraded is the deep health check pulling everything down at once, and the durable response is the liveness and readiness split rather than anything about the instances themselves. The time series turns three failures that look identical in a snapshot into three clearly different stories, and the right fix follows from which story you are in.

The same logging foundation supports proactive alerting rather than reactive reading. An alert that fires when any single instance's availability drops and stays down for a couple of intervals catches a problem while the pool still has healthy members, which is the window in which a fix is calm rather than urgent. An alert that fires when the count of healthy instances falls below a floor catches the dangerous case before it becomes a full outage. Both are cheap to define once the metric is flowing into a workspace, and both convert the silent degradation that engineers discover from customer reports into a signal that reaches the on call engineer first. Alerting on the count of healthy members specifically, rather than on any single failure, is the alert that matters most, because one instance down is routine and the count approaching zero is an outage in the making.

## When the verdict is right and the instance really is broken

The probe-is-the-truth rule cuts both ways, and the second edge is the one engineers resist: sometimes the verdict is correct, the instance genuinely cannot serve, and the work is to fix the application rather than to make the check more forgiving. The temptation, after diagnosing a few failures that turned out to be network or configuration, is to assume every failure is a false alarm and to relax the check until it stops complaining. That is the worst possible response, because it reconnects a broken instance to live traffic, and the symptom moves from a visible unhealthy verdict to invisible errors served to real users. The discipline is to treat a sustained failure as real until the local reproduction proves otherwise, not the reverse.

When the local reproduction confirms the instance truly cannot return a 200, the diagnosis leaves the load balancer entirely and becomes an application troubleshooting problem. The health route is failing because the process is out of memory and cannot allocate, or because the application threw an unhandled exception during startup and never finished initializing, or because a configuration value the application needs is missing and it is returning a 500 from every path including the health route. These are real faults, and the correct action is to read the application logs, find why the process cannot serve, and fix that, then watch the health verdict recover on its own as the cause clears. The check is not the problem in these cases; it is the messenger, and shooting the messenger by loosening the check leaves the real fault in production.

The way to keep the rule honest is the local reproduction, run faithfully. If a request to the health route from the instance itself returns a non-200, the instance really cannot serve that route, and no change to the check protocol, interval, or threshold will make that instance healthy in any meaningful sense; it will only hide the failure. If the request returns a 200 and the check still fails, the fault is in the path between the source and the instance, which is the network family of causes. That single test, run on the instance, is the arbiter of whether you are looking at a false alarm to fix in the network or a real fault to fix in the application, and respecting its answer is what keeps the load balancer doing its job. An engineer who learns to trust the verdict and interrogate it rather than to suppress it ends up with a pool that genuinely reflects which instances can serve, which is the entire point of having a health check at all.

## The failures this gets confused with

A health-check failure is frequently confused with three neighboring problems, and telling them apart saves you from applying the right fix to the wrong layer. The first is a general network security group block that is not specific to the probe at all. When client traffic and probe traffic are both being dropped by the same overly broad deny rule, the symptom can look like a probe issue, but the cause is the broader rule and the fix is the broader allow; the reasoning is identical to the probe case but the scope is wider, and working through how an NSG ends up [blocking traffic it should permit](/2022/11/21/fix-nsg-blocking-traffic/) shows the general method that the probe-allow rule is one instance of.

The second confusion is with an Application Gateway 502, which lives at layer 7 and has a similar but distinct backend health concept. Application Gateway also probes its backend pool and pulls unhealthy members out, but a 502 from Application Gateway surfaces through its own Backend health view with its own reasons, and the causes, while rhyming with the load balancer's, include HTTP specific issues such as host header and certificate mismatches that a layer 4 load balancer never evaluates. If you are seeing a 502 rather than a layer 4 instance simply falling out of rotation, the diagnosis moves to the gateway's backend health, and the [Application Gateway 502 diagnosis](/2022/12/12/fix-application-gateway-502/) is the right place to take it, since the confirming signal lives in a different blade and the protocol contract is richer.

The third confusion is with a name resolution problem, where the backend appears unreachable not because the probe is blocked but because a name the application or the probe depends on does not resolve. This is less common for a load balancer probe, which targets an IP and a port rather than a name, but it appears when a health endpoint's deep check resolves a dependency by name and that resolution fails, which then looks like cause five even though the underlying issue is DNS. Keeping the probe shallow removes this overlap entirely, which is one more reason the liveness versus readiness split earns its place.

## The verdict

An Azure Load Balancer health-check failure is a precise, diagnosable event, not a mystery and not a load balancer fault. The probe-is-the-truth rule resolves the entire class: the load balancer routes only to instances whose probe currently succeeds, so a backend marked down is always a probe that could not reach a healthy response, and the diagnosis is the short, ordered search for what stands between the probe and that response. Read the per instance metric first to count failing instances and separate shared causes from instance local ones. Reproduce the probe locally to split network problems from endpoint problems. Then confirm the specific cause, one of the five in the InsightCrunch probe-failure table, with its one command, and apply its one fix. The network security group or guest firewall block is the most common and the most misdiagnosed, because the application looks healthy locally; the missing listener and the non-200 path are the fastest to confirm and repair; the protocol mismatch hides both false negatives and dangerous false positives; and the dependency in the health check is the one that can take an entire fleet down and is fixed by design rather than by configuration. Treat the probe as the instrument it is, design the health endpoint shallow, allow the check source explicitly and stably, keep the check port and the listener port reconciled in code, and the failures that fill incident channels stop recurring. The load balancer was never the problem. The probe was telling you something true, and now you can read it.

## Frequently Asked Questions

### Q: Why are my Azure Load Balancer health probes failing?

A health probe fails when it cannot reach a healthy response on the configured port and path of a backend instance, and that reduces to five distinct causes. A network security group or guest firewall is dropping the check source before it reaches the listener; the probe targets a port nothing is listening on; an HTTP health path returns a status that is not 200; the probe protocol does not match what the endpoint speaks; or the health endpoint runs a deep check that fails when a downstream dependency is down. Start by reading the per instance probe metric to see whether one instance or all of them are failing, then reproduce the probe locally on a failing instance by confirming a listener on the check port and requesting the path to read its status code. That ordering separates network causes from endpoint causes in a couple of minutes and points you at the specific repair rather than leaving you to guess among all five.

### Q: Does a probe port or path mismatch cause health probe failures?

Yes, and it is one of the most common causes precisely because it hides behind an assumption that the application is serving on the port and path the probe was configured for. If the probe checks port 8080 but the application binds 5000, the probe finds nothing accepting on 8080 and counts a failure even though the application is healthy on its own port. The same happens when an HTTP probe targets a path that returns a 301, 401, 403, or 404, because the HTTP probe treats only a 200 as success. Confirm by checking listening sockets with ss on Linux or Get-NetTCPConnection on Windows, then requesting the health path locally and reading the raw status code. The fix is to reconcile the two sides: repoint the probe at the real port and path when the application is correct, or correct the application's bind and health route when the probe is correct.

### Q: Must the NSG allow the load balancer probe source?

Yes. The probe arrives from the platform source identified by the AzureLoadBalancer service tag, which resolves to the address 168.63.129.16, and a network security group must allow that source to reach the check port or the probe is dropped before it reaches the listener. The default network security group ruleset includes an allow for the AzureLoadBalancer tag, which is why probes usually work until someone tightens the rules and a higher priority deny catches the probe traffic as collateral. Confirm by reading the effective security rules on the backend network interface and looking for an allow on the AzureLoadBalancer tag to the check port, or for a deny with a lower priority number that matches first. The fix is an explicit inbound allow for the AzureLoadBalancer source at a priority high enough to win against the deny, and you must also confirm the guest operating system firewall is not separately dropping the same traffic.

### Q: Why does the backend show unhealthy to the probe when the app is running?

Because the application being up is not the same as the probe being able to reach a healthy response, and the two can diverge in several ways. The most common is a network security group or guest firewall that drops the check source even though your own session to the instance works, since your session and the probe arrive from different sources and may traverse different rules. Another is a service bound only to the loopback interface, which answers a local request but is invisible to the probe arriving on the instance's network address. A third is an HTTP probe whose path returns a redirect or an authentication challenge, which a human reads as working but the probe counts as a non-200 failure. Reproduce the probe specifically, from the probe's perspective, rather than testing the way a signed in user would, and the divergence becomes visible.

### Q: Should I use a TCP or an HTTP health probe?

Use an HTTP or HTTPS probe with a dedicated health path for any HTTP service, and reserve TCP probes for genuinely non HTTP listeners. A TCP probe confirms only that the socket accepts a connection; it never inspects what the application does after the handshake, so it will report a broken application that still accepts connections as perfectly healthy, leaving it in rotation to serve errors to clients. An HTTP probe is stricter and more honest for web workloads, because it requires a 200 from a real path, so its notion of healthy matches the client's notion of healthy. The TCP probe earns its place only where there is no HTTP status to evaluate, such as a database or a custom binary protocol, where the completed handshake is the only meaningful liveness signal available. Choosing the wrong one produces either a false negative, an HTTP probe failing a healthy non HTTP port, or the more dangerous false positive of a TCP probe masking a broken application.

### Q: How do I confirm why a health probe is failing?

Work in a fixed order so each step eliminates causes rather than adding guesses. First, read the per instance probe health metric in Azure Monitor and split it by backend instance to learn whether one instance or all of them are failing, which immediately separates instance local causes from shared ones. Second, get onto a failing instance and confirm a listener exists on the check port using ss or Get-NetTCPConnection. Third, request the health path locally and read the raw status code with curl, without following redirects, so you see exactly what the probe sees. If the local request returns 200 and a listener is present, the endpoint is healthy and the problem is the network path, so read the effective network security group rules for the AzureLoadBalancer allow. If the local request fails or returns a non-200, the endpoint itself is the cause. This sequence resolves most failures to a named cause within minutes.

### Q: What is the 168.63.129.16 address and why does it matter for probes?

It is a special Azure platform virtual IP used across all regions for several host to guest functions, including DNS, the instance metadata service, and load balancer health probes. All IPv4 load balancer probes originate from this address, which is why it must be allowed to reach the check port. You rarely hardcode it, because the AzureLoadBalancer service tag resolves to it and lets you write network security group rules without pinning a literal IP, but knowing the address helps when you inspect guest firewall logs or run packet captures and want to confirm that probe traffic is arriving and from where. The address is not routable from the internet; only Azure's internal platform infrastructure originates traffic from it. If your virtual network is configured with an address space that collides with the range containing this IP, probes and other platform functions can break, so avoid that overlap.

### Q: Why does an HTTP probe fail when the page loads fine in a browser?

Because the probe does not behave like a browser. A browser silently follows redirects, presents cookies, and may carry an authenticated session, so a page that renders for you can still be a 301 redirect or a 200 that only appears after authentication. The HTTP probe sends a plain request from the platform source, does not follow redirects, carries no session, and counts only a direct 200 as success. The most common version is an application that redirects HTTP to HTTPS: the browser follows the 301 to the secure page and shows you content, while the probe sees the 301 and marks the instance down. Read the raw status code with a tool that does not follow redirects to see what the probe sees. The fix is a dedicated health path that returns a flat 200 with no redirect and no authentication, repointing the probe at it.

### Q: Can a guest OS firewall cause a probe failure even when the NSG allows the probe?

Yes, and it is a frequent second layer trap. The network security group governs traffic at the Azure network level, but the guest operating system has its own firewall that can independently drop the probe source after it clears the network security group. When the effective network security group rules show the probe allowed but the instance is still down, move the investigation inside the box: check Windows Defender Firewall for an inbound allow on the check port, or check firewalld, iptables, or nftables on Linux. The probe source must be permitted to reach the check port at both layers, because either one dropping it produces the identical symptom of an instance that is healthy locally and unreachable to the probe. A base image update or a configuration management run that resets the guest firewall is a common way this regresses after working for months.

### Q: Why did my entire backend pool go down at the same time?

A whole pool failing in lockstep points at a shared cause rather than a single sick instance, and there are three usual culprits. A network security group rule applied at the subnet level can drop the probe source for every instance at once. A probe pointed at a wrong port or path will fail identically on every instance because they all serve the same way. The most dramatic is a deep health endpoint that calls a shared dependency: when the database or cache degrades, every instance's health check fails simultaneously, every probe returns a non-200, and the load balancer removes the entire pool, turning a dependency hiccup into a total outage. Read the per instance metric to confirm the lockstep, correlate the timing against any dependency event, and inspect what the health path actually checks. The durable fix for the dependency case is to make the probe a shallow liveness check that never calls a downstream.

### Q: How do I test a load balancer probe failure on purpose for a drill?

The supported way to simulate a health-check failure for testing is to make the probe genuinely fail at the endpoint or to block its source with an explicit network security group rule for the duration of the drill, then remove it. Creating a temporary inbound deny that matches the check port or the AzureLoadBalancer source will pull the targeted instances out of rotation, letting you watch the metric drop and your failover behave. Azure notes that blocking the probe source with network security group rules is not a supported way to run production for long, because rule changes against the probe can take delayed effect and report stale availability, so use it only as a short, deliberate test and revert it. A cleaner drill changes the application's own health response to a non-200 temporarily, which exercises the same rotation behavior without touching network rules at all.

### Q: What is the difference between a load balancer probe and an Application Gateway backend probe?

Both check backend health and remove unhealthy members, but they operate at different layers and surface their verdicts differently. The load balancer is layer 4 and its probe evaluates a TCP handshake or an HTTP 200 on a port and path, with the per instance verdict exposed as a metric. Application Gateway is layer 7, understands HTTP natively, and exposes a Backend health view that names the failing backend and the reason, including HTTP specific causes such as host header and certificate mismatches that a layer 4 probe never evaluates. A 502 from Application Gateway is its way of saying it could not get a valid response from a healthy backend, and the diagnosis moves into its Backend health blade. If you are choosing between them, the layer 7 awareness buys richer routing and health semantics at a higher cost and complexity, while the layer 4 load balancer is simpler and faster for straightforward traffic distribution.

### Q: Does the probe interval and failure threshold affect how fast an instance is removed?

Yes, directly. The interval sets how often the probe runs, and the failure threshold sets how many consecutive failures trigger removal, so together they determine both how quickly a genuinely failing instance leaves rotation and how tolerant the load balancer is of a transient blip. A short interval with a low threshold reacts fast but can flap, pulling an instance out for a single missed probe that immediately recovers. A longer interval or higher threshold is more stable but slower to evict a real failure, during which clients hitting that instance get errors. Tune by measuring how your application actually fails and recovers under a real restart or dependency blip, then set the values so the load balancer responds to sustained failure without overreacting to noise. There is no universal best setting; the right one depends on your instances' real failure and recovery profile.

### Q: Why does a TCP probe show healthy while users get errors?

Because a TCP probe stops at the handshake and never inspects the application's response. The web server is accepting connections, so the TCP handshake completes and the probe reports the instance healthy, but the application behind that open socket can be returning 500s to every real request. The probe is telling the truth about what it checked; what it checked was simply too shallow to catch an application layer failure. This false positive is the dangerous side of choosing a TCP probe for an HTTP service, because the broken instance stays in rotation serving errors. The fix is to switch to an HTTP probe with a real health path so the probe evaluates an actual 200 from the application rather than just socket acceptance, aligning the probe's notion of healthy with the client's experience.

### Q: Are there ports an HTTP probe cannot use?

Yes. The platform's HTTP probe client refuses a specific set of ports for HTTP health checks for historical security reasons, and an HTTP probe configured on one of them fails in a way that looks like a protocol mismatch with no obvious cause. The restricted ports for HTTP probes are 19, 21, 25, 70, 110, 119, 143, 220, and 993. Few applications serve health on these legacy ports, so the case is rare, but when it happens it is hard to spot because every other check passes and the configuration looks correct. The fix is to move the health endpoint to a normal application port such as 80, 8080, or a high numbered port, and configure the HTTP probe against that. If you must use a restricted port for the application itself, serve the health endpoint on a different, unrestricted port and point the probe there.

### Q: Should the load balancer health probe call my database?

No. The load balancer probe should hit a shallow liveness endpoint that returns 200 whenever the process itself is up and able to accept work, without calling any downstream dependency. If the health path checks the database and the database degrades, every instance fails its probe at once and the load balancer removes the entire pool, converting a dependency problem into a complete outage with zero healthy instances. Keep a deeper readiness check that verifies dependencies as a separate route used by orchestration or application logic, but do not wire it to the load balancer probe. The boundary is the principle that a health check gating traffic should be exactly as shallow as the routing decision it informs, so a shared dependency failing degrades the application rather than deleting the backend pool.

### Q: How do I check what port my application is actually listening on?

On Linux, run ss with the listening, TCP, numeric, and process flags, which shows each listener with its bound address and port and the owning process; the command is ss with the appropriate flags and you read the local address column. A line bound to 0.0.0.0 on the probe port is reachable to the probe, while a line bound to 127.0.0.1 is loopback only and invisible to the probe even though it answers local requests. On Windows, use Get-NetTCPConnection filtered to the Listen state and select the local address, local port, and owning process. Compare the result against the probe's configured port. If nothing is bound to the probe port, the service is not listening there, and you either repoint the probe at the real port or start and fix the service. If it is bound to loopback, change the bind to the instance address so the probe can reach it.

### Q: Why does my HTTPS probe fail even though HTTPS works for clients?

An HTTPS probe adds a TLS handshake to the HTTP requirements, so it can fail at the certificate layer even when clients succeed. The probe must complete the TLS handshake with the backend and then receive a 200, so a certificate the backend presents that the probe cannot validate, a missing intermediate, or a handshake that the server rejects will fail the probe before any status code matters. Clients can succeed where the probe fails if the client tolerates a certificate condition the probe does not, or if the client reaches a different endpoint. Confirm by reproducing the HTTPS request from a position similar to the probe and watching the handshake, then read the status code. The fix is to ensure the backend presents a valid certificate the probe accepts and that the health path returns a flat 200 over HTTPS, with the probe configured for the correct protocol and port.

### Q: One instance is unhealthy but the rest are fine. Where do I look?

When a single instance fails while the rest of the pool stays healthy, the cause is local to that instance rather than shared across the subnet or the configuration, which immediately rules out a wrong probe port or a subnet wide network security group rule, since those would fail every instance identically. Focus the diagnosis inside the failing box. Confirm the service is actually running and listening on the check port, since a crashed or stopped service on one instance is the most common single instance cause. Check that the guest firewall on that instance has not drifted out of line with the others, which happens after an out of band change or a failed configuration run. Look at whether the instance is mid restart or mid reimage, in which case the failure is transient and will clear on its own. The shortcut is to compare the failing instance against a healthy peer item by item, because the difference between them is almost always the cause, and the healthy peers prove the shared configuration is sound.

### Q: Can I keep a backend instance out of rotation deliberately without breaking the probe design?

Yes, and the right way is to control the application's own health response or the backend pool membership rather than manipulating the probe source with deny rules. To drain an instance for maintenance, have the application return a non-200 from its health path so the probe fails for that instance and the load balancer stops sending it new flows, then return to 200 when maintenance is done. Alternatively, remove the instance from the backend pool through the load balancer configuration, which takes it out cleanly. Avoid using a network security group deny on the probe source as a drain mechanism, because blocking the probe with network security group rules is an unsupported pattern that can cause rule changes to take delayed effect and report stale availability. Keep the probe-allow rule a stable allow and drain through the application or the pool membership instead.
