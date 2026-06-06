---
layout: post
title: "Fix ExpressRoute Circuit Down Issues"
page_title: "ExpressRoute Circuit Down: How to Diagnose and Fix a Down Circuit, BGP Session, or Peering Failure in Azure"
date: 2023-01-02
categories: ["Technology"]
tags: ["Azure", "ExpressRoute", "Networking", "Troubleshooting", "BGP", "Hybrid Connectivity"]
excerpt: "An ExpressRoute circuit down is rarely one failure. Localize it to the provider link, BGP, a peering, or a routing problem, then fix the correct layer."
image: "/assets/images/blog/blog-01.webp"
reading_time: 60
author: "Insight Crunch Team"
last_updated: 2023-01-02
---

You open the portal expecting a healthy private path into Azure, and instead the graphs go flat. Applications that depend on on-premises systems begin timing out, a database replication job stalls partway through, and someone on the network team announces that the ExpressRoute circuit is down. That sentence is carrying far more weight than it sounds, because an ExpressRoute circuit down can describe at least six distinct situations, and each one lives at a different layer of the stack and belongs to a different owner. Some of those layers are yours to fix in the next ten minutes from a terminal. One of them is not yours at all, and the only correct action is to open a ticket with the carrier who runs the physical segment. The fastest engineers in an incident like this are not the ones who know the most commands. They are the ones who localize the failure to a single layer first, because the layer tells them whether to reach for the keyboard or the phone.

![Diagnosing an ExpressRoute circuit down to the failed layer and its owner - Insight Crunch](/assets/images/blog/blog-01.webp)

The reason teams lose an hour to this is that ExpressRoute presents one resource in the portal, a circuit, but that single object sits on top of a stack with four mechanically separate parts: a physical or provider connection at layer 2, a BGP session running over a primary and a secondary link, one or both peerings that ride those sessions, and the route advertisement that decides which prefixes actually move. A break in any one of those parts can produce the same surface symptom, a loss of reachability, while leaving the others perfectly healthy. Treating the whole thing as a single on-or-off switch is what sends people resetting gateways that were never the problem, or escalating to a carrier for something the carrier cannot touch. This guide walks the stack from the bottom up, gives you the command that confirms each layer, names the owner of each fix, and shows you the tested remedy once you know where the break actually sits. If you want the broader picture of how the service is built before you debug it, the architecture is covered in depth in [the full ExpressRoute deep dive](/2023/11/20/azure-expressroute-deep-dive/); this article assumes you are mid-incident and need the diagnosis now.

## What an ExpressRoute circuit down actually means

Before any command runs, fix the vocabulary, because the word "down" is the source of half the confusion. A circuit in ExpressRoute is the logical resource Azure exposes, identified by a service key, that represents your dedicated connection through a connectivity provider into the Microsoft network. It is not a cable and it is not a router. It is a control-plane object whose health is a roll-up of several lower facts. When a teammate says the circuit is down, they almost always mean that traffic stopped, not that the circuit object reports a specific failed state, and those two things are not the same. The object can read as healthy at the provisioning layer while no packets move, and it can read as degraded while half the traffic still flows over the surviving link.

The stack has four parts, and naming them precisely is the entire method. At the bottom sits the physical or provider connection, the layer-2 segment that the carrier owns and operates between your edge and the Microsoft Enterprise Edge routers, the devices Microsoft calls MSEEs. Above that runs BGP, the routing protocol that exchanges reachability between your equipment and Microsoft, and BGP runs as two independent sessions, one over the primary link and one over the secondary link, which is where redundancy comes from. On top of BGP sit the peerings, the routing contexts that decide what kind of destinations the sessions carry: Azure private peering for traffic to your virtual networks, and Microsoft peering for the public endpoints of platform services. Finally there is route advertisement, the act of announcing and accepting prefixes, which can fail on its own even when everything beneath it is up. A failure can occur at exactly one of these parts while the rest stay healthy, and the symptom at the top can look identical no matter where the break is.

### Does ExpressRoute have a single thing that can be down?

No, and that assumption is the first wrong turn. The circuit resource is a roll-up of a provider connection, two BGP sessions, one or two peerings, and route advertisement. Any one can fail alone and produce a reachability loss that looks total. The diagnosis always starts by asking which of those parts actually stopped, not by treating the circuit as one switch.

The practical consequence of this structure is that the question "is the circuit down" has no useful answer. The useful questions are narrower and each maps to a layer. Is the provider connection up at layer 2, meaning has the carrier's segment failed or gone into maintenance? Are both BGP sessions established, or is one neighbor stuck in an Idle or Connect state while the other holds? Is the peering you depend on configured and reporting a state, or is it blank because the provider has not finished the layer-3 part? Are the prefixes you expect actually being advertised and received, or is the session up while the route table is empty because a limit was tripped? Each of those is a separate check, each has a command, and each points at a different owner. The rest of this guide is organized around exactly those questions, because answering them in order is the diagnosis.

There is one more piece of vocabulary worth pinning down, because it confuses people during the most stressful version of this incident. ExpressRoute is deliberately built so that one link can drop while the other carries traffic. The primary and secondary links are not active and standby in the sense of one sitting idle; both are meant to be up and both carry traffic, and the loss of either should degrade capacity and resilience without taking the connection offline. This is why a real circuit-down event and a single-link failure feel completely different on the ground, and why mistaking one for the other wastes time. If applications still work but alerting is screaming, you very likely have a single dropped session over redundant infrastructure, not an outage, and the urgency is different even though the alert text is not.

## How to read circuit and peering state before you change anything

The discipline that separates a five-minute fix from a two-hour scramble is refusing to change anything until you have read state from three places: the circuit object, the BGP session summary, and the route and ARP tables. These reads are non-destructive, they take under a minute, and they tell you which layer broke. Skipping them and jumping straight to "reset the gateway" or "call the provider" is how the wrong layer gets touched. Read first, act second.

Start at the circuit object itself, because it carries two distinct provisioning fields that people routinely conflate. The first is the circuit provisioning state, which reflects whether Azure has the circuit object enabled, and the second is the service provider provisioning state, which reflects whether your carrier has actually lit the connection on their side. A circuit can be Enabled in Azure while the provider state still reads NotProvisioned, which means Azure is ready and the carrier is not, and no amount of work on your side will help.

```bash
# Read both provisioning states and the circuit's service key in one shot.
az network express-route show \
  --resource-group rg-hybrid-core \
  --name er-circuit-prod \
  --query "{circuitState:circuitProvisioningState, providerState:serviceProviderProvisioningState, sku:sku.tier, bandwidth:serviceProviderProperties.bandwidthInMbps}" \
  --output table
```

If the provider state reads anything other than Provisioned, you have found the layer already and it is not yours; the action is a carrier ticket, and the section below on the provider link covers what to put in it. If both states read healthy, move up the stack to the peerings and their sessions, because the circuit object being enabled tells you nothing about whether routes are moving.

The next read is the peering list, which tells you which peerings exist and what subnets they were given. A peering that should be present but is missing entirely is a configuration or provisioning gap rather than a session failure, and the fix differs accordingly. In the IPVPN model that many carriers use, the provider configures the layer-3 peering, so a blank peering in the portal often means the carrier has not finished, not that you misconfigured anything.

```bash
# List the peerings configured on the circuit and the addresses each link uses.
az network express-route peering list \
  --resource-group rg-hybrid-core \
  --circuit-name er-circuit-prod \
  --query "[].{peering:name, state:state, primarySubnet:primaryPeerAddressPrefix, secondarySubnet:secondaryPeerAddressPrefix, asn:azureASN}" \
  --output table
```

### How do I tell whether the failure is mine or the provider's?

Read the service provider provisioning state on the circuit and the BGP session summary together. If the provider state is not Provisioned, or the layer-2 ARP table is empty on a path the carrier owns, the break is theirs. If the provider state is Provisioned and ARP resolves but BGP is down, the break sits at routing, which is usually yours to fix.

The deepest read, and the one that actually localizes the break between layer 2 and layer 3, is the pair of route-table and ARP-table queries. The ARP table is a layer-2 view: it maps the on-premises router interface address and the Microsoft router interface address to their hardware addresses for a given peering and path. If ARP resolves for both the on-premises side and the Microsoft side, layer 2 is healthy on that path and the break is higher up. If ARP is empty or only shows one side, the physical or provider segment for that path is the suspect, which points you back at the carrier.

```bash
# Layer-2 view: does ARP resolve on the primary path for private peering?
az network express-route list-arp-tables \
  --resource-group rg-hybrid-core \
  --name er-circuit-prod \
  --path primary \
  --peering-name AzurePrivatePeering \
  --output table

# Repeat for the secondary path to see whether one link is dead while the other lives.
az network express-route list-arp-tables \
  --resource-group rg-hybrid-core \
  --name er-circuit-prod \
  --path secondary \
  --peering-name AzurePrivatePeering \
  --output table
```

Once ARP confirms layer 2, the route-table summary gives you the BGP neighbor state and the count of prefixes received, which is the single most informative read in the whole sequence. A neighbor in an established state with a sensible prefix count means the session is healthy and carrying routes. A neighbor that never leaves Idle or Connect, or one that flaps between states, is a BGP problem. A neighbor that is established with a received-prefix count of zero is the trap that looks like a full outage but is in fact a route-advertisement failure, and it is treated in its own section below.

```bash
# BGP view: neighbor state and prefixes received per path.
# The summary command is in preview; the route-table command is stable.
az network express-route list-route-tables-summary \
  --resource-group rg-hybrid-core \
  --name er-circuit-prod \
  --path primary \
  --peering-name AzurePrivatePeering \
  --output table

# Full received route table for the same path, to see exactly which prefixes arrived.
az network express-route list-route-tables \
  --resource-group rg-hybrid-core \
  --name er-circuit-prod \
  --path primary \
  --peering-name AzurePrivatePeering \
  --output table
```

The PowerShell equivalents exist for shops that live in that world, and they return the same facts. `Get-AzExpressRouteCircuitARPTable` gives the layer-2 mapping, `Get-AzExpressRouteCircuitRouteTableSummary` gives the neighbor state and prefix counts, and `Get-AzExpressRouteCircuitRouteTable` gives the full received prefixes, each taking a `-DevicePath` of Primary or Secondary and a `-PeeringType` of AzurePrivatePeering or MicrosoftPeering. Whichever tooling you use, the order is the same: provider state, then ARP for layer 2, then the route summary for BGP and prefixes. Three reads, in that order, and you have localized the break before touching anything. To rehearse this exact sequence against a sandbox circuit until it is muscle memory, [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), where the circuit, ARP, and route-table reads are wired into a guided walkthrough.

## The InsightCrunch ExpressRoute layer table

Here is the artifact that turns the reads above into a decision. Call it the layer-and-owner rule: an ExpressRoute outage lives in exactly one of four layers, and naming the layer also names who owns the fix, you or the provider. Every diagnosis below resolves to a row in this table. The point of the table is not to memorize commands; it is to force the question "which layer" before the question "which fix," because the layer is what tells you whether the next action is a CLI command or a carrier ticket.

| Layer | What it is | State to check | Command that confirms it | Who owns the fix |
|-------|-----------|----------------|--------------------------|------------------|
| Provider / layer 2 | The physical segment the carrier runs between your edge and the MSEEs | Service provider provisioning state; ARP table on each path | `az network express-route show` (providerState); `az network express-route list-arp-tables` | The connectivity provider (carrier ticket) |
| BGP session | The two eBGP sessions, one per link, that exchange routes | Neighbor state (established or not) per path | `az network express-route list-route-tables-summary` | You, unless the provider runs layer 3 (IPVPN model) |
| Peering | The routing context (private or Microsoft) riding the sessions | Peering present and reporting a state | `az network express-route peering list` | Shared: you configure, provider may provision |
| Route advertisement | The prefixes announced and accepted over an up session | Received-prefix count; advertised prefixes | `az network express-route list-route-tables` | You (and your on-premises routing policy) |

The table also encodes the most common misdiagnosis directly. The reason people escalate the wrong things is that the symptom at the top of the stack, lost reachability, is identical across all four rows, so the instinct is to act on the most visible object, the circuit or the gateway, regardless of which layer actually broke. The layer table breaks that instinct by making the owner column a function of the state column. If the provider state is bad or ARP is empty on the carrier-owned path, the owner is the provider and your keyboard cannot help. If the provider state is good and ARP resolves but BGP is down or the route table is empty, the owner is you, and a carrier ticket only adds delay. Print this table, pin it near the runbook, and make the first move in any ExpressRoute incident the act of filling in the state column. The fix follows from the row, and the row follows from three reads.

One nuance the table compresses: the BGP and peering rows have a shared-owner asterisk because of the two connectivity models carriers offer. In the model where you run your own edge routers and only the physical port is the carrier's, BGP and route advertisement are entirely yours. In the IPVPN model, the provider operates the layer-3 edge and configures the peering and the BGP session on your behalf, which moves the BGP row partly into their column. Knowing which model your circuit uses changes who you escalate the BGP row to, and it is worth writing that fact into the runbook once so nobody has to rediscover it mid-incident.

## Root cause one: the provider link or layer-2 segment is down

This is the cause that is not yours, and recognizing it quickly is what stops you from burning an hour on a problem your keyboard cannot reach. The physical or provider connection is the layer-2 path the carrier operates between your edge equipment and the Microsoft routers. When that segment fails, whether through a fiber cut, a cross-connect problem in the colocation facility, a port fault on the carrier's switch, or scheduled maintenance the carrier did not flag clearly, the symptom on your side is a session that will not establish and an ARP table that does not resolve. Nothing above layer 2 can work, because there is no layer-2 adjacency for BGP to run over.

The confirming signal is specific and unambiguous. Read the service provider provisioning state on the circuit object first; if the carrier has dropped the provisioning, it may read NotProvisioned or Provisioning rather than Provisioned, which is a direct statement that the carrier's side is not lit. The provisioning state does not always change during a transient layer-2 fault, though, so the more reliable confirmation is the ARP table. Pull the ARP table on each path for the affected peering, and look at whether the on-premises router interface and the Microsoft router interface both resolve to hardware addresses.

```bash
# If ARP returns no entries, or only the Microsoft side, layer 2 is the suspect.
az network express-route list-arp-tables \
  --resource-group rg-hybrid-core \
  --name er-circuit-prod \
  --path primary \
  --peering-name AzurePrivatePeering \
  --output json
```

If ARP is empty on both paths, the carrier segment is almost certainly the break, and the action is a carrier ticket with the right details attached so the carrier does not bounce it back asking for more. Put the circuit service key in the ticket, because that is how the carrier identifies your connection on their side. State which paths are affected, primary, secondary, or both, and include the timestamp the ARP resolution was lost. Note whether the service provider provisioning state changed, and attach the ARP output showing the missing entries. A ticket with the service key, the affected path, and the empty ARP evidence is one the carrier can act on immediately; a ticket that just says "ExpressRoute is down" starts a round trip you cannot afford during an incident.

There is a subtle version of this cause worth calling out, because it produces a partial symptom rather than a total one. When the carrier performs maintenance on one of the two physical links, ARP and BGP drop on that single path while the other path keeps carrying traffic. Applications stay up because of redundancy, but your alerting fires because a session went down, and a half-asleep responder at 3 a.m. can easily read the alert as a full outage and start escalating aggressively. The tell is that ARP resolves on one path and is empty on the other, and the route-table summary shows one neighbor established and one not. That is a single-link event over redundant infrastructure, and while it deserves a carrier ticket to restore full resilience, it is not an emergency in the way a both-paths-down event is. Knowing the difference changes the tone of the entire incident.

### Why does the circuit show enabled while traffic still fails?

Because the circuit's enabled state only means Azure has the object provisioned; it says nothing about whether the carrier lit the physical link or whether BGP came up. A circuit can read Enabled with the service provider state stuck at NotProvisioned, or with both BGP sessions down. Always confirm layer 2 and BGP separately rather than trusting the circuit's headline state.

The prevention angle for this cause is mostly contractual and architectural rather than something you fix from a terminal, and it is covered in the prevention section below, but the short version is that a single circuit through a single provider has the provider's layer-2 segment as a single point of failure no command can remove. The only structural answer is a second circuit, ideally through a second provider in a second peering location, which is exactly the kind of decision that belongs in the design review rather than the incident. When you are weighing whether ExpressRoute, a VPN gateway, or plain peering is the right connectivity model for a given workload, the trade-offs including this provider-dependency are laid out in the comparison of [VNet peering, VPN, and ExpressRoute](/2023/09/04/vnet-peering-vpn-expressroute/).

## Root cause two: a BGP session is down on one or both peerings

Once layer 2 is confirmed healthy, the next layer up is BGP, and this is where most of the genuinely yours-to-fix problems live. BGP is the protocol that exchanges reachability between your routers and the Microsoft edge, and ExpressRoute runs it as two independent external BGP sessions per peering, one over the primary link and one over the secondary. For routes to move, the session must reach the established state; a session stuck in Idle, Connect, or Active, or one that establishes and then drops repeatedly, carries no prefixes, and the result is lost reachability even though the carrier's segment is fine.

The confirming read is the route-table summary, which reports the neighbor state and the prefix count per path. A neighbor that shows as established with a non-zero received-prefix count is healthy. A neighbor that never reaches established is a session failure, and the cause is almost always a mismatch in the BGP parameters between your edge and Microsoft. The usual suspects are a wrong peer ASN, the wrong IP address on the /30 subnet, a VLAN tag mismatch, or an MD5 authentication key that does not match on both ends. Microsoft uses autonomous system 12076 on its side for all peering types, and on the /30 subnet assigned to each link, Microsoft takes the second usable address while your router must hold the first; getting that backward is a classic reason a session refuses to come up.

```bash
# Confirm the neighbor state and prefix count on both paths.
az network express-route list-route-tables-summary \
  --resource-group rg-hybrid-core \
  --name er-circuit-prod \
  --path primary \
  --peering-name AzurePrivatePeering \
  --output table

az network express-route list-route-tables-summary \
  --resource-group rg-hybrid-core \
  --name er-circuit-prod \
  --path secondary \
  --peering-name AzurePrivatePeering \
  --output table
```

The fix depends on which side owns the misconfiguration, and that depends on your connectivity model. If you run your own edge routers, the parameters to align are on your equipment: confirm the peer ASN points at 12076, confirm the local and remote addresses on the /30 match the assignment with your interface on the first usable address, confirm the VLAN tag matches what the peering expects, and confirm the optional MD5 key is identical on both ends or absent on both. On the Azure side, the peering configuration must reflect the same subnets and ASN, and you can correct it without recreating the peering.

```bash
# Correct the private peering parameters on the Azure side without recreating it.
az network express-route peering update \
  --resource-group rg-hybrid-core \
  --circuit-name er-circuit-prod \
  --name AzurePrivatePeering \
  --peer-asn 65010 \
  --primary-peer-subnet 192.168.10.16/30 \
  --secondary-peer-subnet 192.168.10.20/30 \
  --vlan-id 200
```

If the circuit uses the IPVPN model where the carrier operates the layer-3 edge, the BGP session parameters are largely the carrier's responsibility, and a session that will not establish becomes a carrier ticket rather than a change on your equipment. This is the case where knowing your model up front saves the most time, because the natural instinct of an engineer who runs their own edge in other contexts is to start changing router config that, on this circuit, they do not even own. The route-table summary read tells you the session is down; the connectivity model tells you whose change brings it up.

### Why is only one of my BGP sessions established?

Usually because the parameter mismatch or the link fault affects one path and not the other. The primary and secondary sessions are configured independently over independent links, so a VLAN, address, or physical problem on one path leaves the other established. Compare the two paths' parameters and ARP tables side by side; the working path is your reference for what the broken one should look like.

A particularly frustrating variant is the flapping session, one that reaches established and then drops on a cycle. Flapping usually traces to a layer-1 problem the carrier should chase, a marginal optic or a link with errors, or to a route-count problem that trips a limit and forces the session to renegotiate, which is the next cause. The route-table summary captured at intervals shows the flap as a neighbor that oscillates and a prefix count that resets. Persistent flapping that you cannot tie to a route-count limit is layer-1 evidence for the carrier, and the ARP and route summaries over time are exactly the data the carrier needs. To drill the BGP-localization sequence against realistic broken-session scenarios rather than learning it live during an incident, [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html), which sets up sessions in each failure state so the read becomes automatic.

## Root cause three: one peering is up, the other is down, and redundancy is masking it

This cause is not a failure so much as a misread, and it accounts for a startling share of the time teams waste on ExpressRoute alerts. The design intent of the two links is that either can carry the full logical connection while the other is degraded, so a single dropped session reduces resilience and capacity without taking reachability offline. The trap is that monitoring fires on the dropped session, the alert text says something stark like "BGP down," and a responder reads that as a total outage and begins escalating, restarting, or recreating things that were never broken. Meanwhile applications are working fine over the surviving path, and the aggressive remediation risks turning a non-event into a real one.

The confirming signal is the contrast between the two paths. Pull the route-table summary for the primary and the secondary, and you will see one neighbor established with a healthy prefix count and one neighbor down. That asymmetry is the entire diagnosis: a real circuit-down event has both paths down, while a single-link event has exactly one. Confirm it from the application side too, because if real traffic is still flowing, you have proof that redundancy is doing its job and the urgency is to restore the lost path, not to treat the connection as offline.

```bash
# The diagnostic contrast: one path established, one path down, means redundancy is holding.
echo "PRIMARY:" && az network express-route list-route-tables-summary \
  -g rg-hybrid-core -n er-circuit-prod --path primary \
  --peering-name AzurePrivatePeering --output table
echo "SECONDARY:" && az network express-route list-route-tables-summary \
  -g rg-hybrid-core -n er-circuit-prod --path secondary \
  --peering-name AzurePrivatePeering --output table
```

The correct response is calibrated to what you find. If exactly one path is down and traffic flows, you restore the lost path with appropriate urgency but without emergency escalation: investigate whether the down path is a layer-2 fault for the carrier or a BGP parameter problem on your edge, using the same checks as the two causes above, and fix that single path. If both paths are down, you have an actual outage and the escalation is justified. The mistake to avoid is letting the alert's tone dictate the response; the route summaries dictate the response, and they distinguish a degraded-but-working connection from a true outage in one read.

There is a planning lesson buried in this cause. If a single dropped session causes a panic every time, the monitoring is miscalibrated: it should distinguish "one link down, connection degraded" from "both links down, connection offline" and alert at different severities. Wiring that distinction into the alert rules, so that a single-path drop pages at a lower severity than a both-paths drop, removes the panic permanently and is one of the highest-value preventive changes you can make. It costs nothing in infrastructure and saves the most expensive resource in an incident, which is the responder's judgment under pressure.

## Root cause four: routes are not advertised or received

This is the cause that most convincingly impersonates a full outage while every layer beneath it is healthy, and it is the one that humbles experienced engineers. The session is established, ARP resolves, the provider state is Provisioned, every headline looks green, and yet nothing is reachable, because no prefixes are crossing the session. BGP being up only means the two routers agreed to talk; it does not guarantee they exchanged any routes. If the received-prefix count is zero on an otherwise established session, the break is route advertisement, not connectivity, and the fix is in routing policy rather than in the circuit or the gateway.

The confirming read is the prefix count in the route-table summary alongside the full route table. An established neighbor with a received count of zero means the other side is announcing nothing to you, or is announcing it and you are rejecting it. Pull the full received route table to see exactly which prefixes arrived, and compare it against what you expect.

```bash
# Established session, zero prefixes received, points at route advertisement, not connectivity.
az network express-route list-route-tables \
  --resource-group rg-hybrid-core \
  --name er-circuit-prod \
  --path primary \
  --peering-name AzurePrivatePeering \
  --output table
```

The causes of empty advertisement cluster into a few families. On private peering, the most consequential is the route-count limit: Azure caps the number of prefixes a private peering session will accept, and exceeding the cap forces the session to drop the routes and refuse to reestablish them until the count comes back under the limit. The standard private-peering limit sits at a few thousand prefixes, and the premium add-on raises it substantially; the exact figures are values to confirm against the current Microsoft limits at read time, because Azure revises them, but the behavior is durable: cross the cap and the session sheds routes rather than degrading gracefully. A team that summarizes on-premises routes loosely and advertises tens of thousands of prefixes will trip this and see a session that is technically up carrying nothing.

```bash
# On the Azure side, the gateway and circuit must be connected for VNet prefixes to advertise.
# Confirm the connection between the ExpressRoute gateway and the circuit exists and is connected.
az network vpn-connection list \
  --resource-group rg-hybrid-core \
  --query "[?contains(name, 'er')].{name:name, status:connectionStatus}" \
  --output table
```

The fix follows the family. If the cap is the problem, reduce the advertised prefix count by summarizing on-premises routes into fewer, larger prefixes, or enable the premium add-on if the larger limit is genuinely needed and justified, then let the session pick the routes back up. If the problem is that your on-premises routers are not advertising the expected prefixes at all, the fix is in your routing policy: confirm the network statements or redistribution that should be injecting those routes into the session, because Azure can only receive what your side announces. If the problem is on the Azure-to-on-premises direction, where your virtual network prefixes are not reaching on-premises, confirm that the ExpressRoute gateway exists in the GatewaySubnet, that a connection object links the gateway to the circuit, and that the virtual network's address space is what you expect, because the gateway is what advertises the VNet prefixes into the circuit. The interaction between advertised prefixes, the gateway, and the on-premises route table is exactly where the routing layer meets the circuit, and if you need to reason about how those routes are then steered inside Azure, the mechanics of [route tables and user-defined routes](/2023/12/11/azure-route-tables-udr-explained/) determine what happens to traffic once a prefix is learned.

### Why is my ExpressRoute session up but nothing routes?

Because an established BGP session carries no traffic until prefixes are exchanged, and exchange can fail independently of the session. The common reasons are a private-peering route-count limit forcing the session to shed prefixes, an on-premises router not advertising the expected networks, or the ExpressRoute gateway not connected to the circuit so VNet prefixes never advertise. Read the received-prefix count to confirm.

The escalation rule for this cause is the inverse of the layer-2 cause, and confusing the two is the single most common ExpressRoute escalation error. A route-advertisement problem is almost always yours, sitting in your on-premises routing policy, your prefix summarization, or your Azure gateway and connection objects. Escalating an empty-route-table problem to the carrier wastes a round trip, because the carrier's layer-2 segment is healthy and they will tell you so. The carrier owns the segment when ARP is empty; you own the routing when the session is up and the route table is bare. Reading the prefix count before you escalate is what keeps the ticket from bouncing.

## Root cause five: the circuit is provisioned but not wired to a gateway

This cause shows up most often on a new deployment or after a redeployment, and it produces a circuit that looks completely healthy in isolation while no virtual network traffic moves. A circuit can be provisioned by the carrier, have private peering configured, and have both BGP sessions established, and still carry no traffic to or from your Azure virtual networks, because the circuit by itself does not connect to anything inside Azure. Reaching a virtual network requires an ExpressRoute gateway deployed in that network's GatewaySubnet and a connection object that links the gateway to the circuit. Without the connection, the circuit is a healthy private path that terminates in nothing on the Azure side.

The confirming signal is the absence of a connection object or a connection in a non-connected state, combined with healthy lower layers. If the provider state is Provisioned, the peering exists, BGP is established, and prefixes are being received from on-premises, but VNet traffic still fails, the gap is between the circuit and the gateway. Confirm the gateway exists and is of the ExpressRoute type, confirm a connection object references both the gateway and the circuit, and confirm that connection reports a connected status.

```bash
# Confirm an ExpressRoute gateway exists in the VNet.
az network vnet-gateway list \
  --resource-group rg-hybrid-core \
  --query "[?gatewayType=='ExpressRoute'].{name:name, type:gatewayType, sku:sku.name}" \
  --output table

# Confirm a connection links the gateway to the circuit and is connected.
az network vpn-connection show \
  --resource-group rg-hybrid-core \
  --name conn-er-prod \
  --query "{name:name, status:connectionStatus, type:connectionType}" \
  --output table
```

The fix is to create the missing piece. If the gateway is absent, deploy an ExpressRoute gateway into the GatewaySubnet of the target virtual network, sized appropriately for the throughput you need, and be aware that gateway deployment takes time to complete. If the gateway exists but no connection links it to the circuit, create the connection object that references both. The connection is what carries the VNet prefixes into the circuit for advertisement to on-premises and pulls on-premises prefixes into the VNet route table, so until it exists and reports connected, the two sides cannot see each other regardless of how healthy the circuit looks on its own.

```bash
# Create the connection that wires an ExpressRoute gateway to the circuit.
az network vpn-connection create \
  --resource-group rg-hybrid-core \
  --name conn-er-prod \
  --vnet-gateway1 ergw-prod \
  --express-route-circuit2 er-circuit-prod \
  --connection-type ExpressRoute
```

The reason this cause is so easy to miss is that every read aimed at the circuit comes back green, so an engineer who only checks the circuit concludes everything is fine and starts looking for the problem in the wrong place, often blaming DNS or the application. The discipline that catches it is to trace the path end to end rather than stopping at the circuit: provider link up, BGP established, prefixes received, gateway present, connection connected, VNet route table showing the on-premises prefixes. The break is wherever that chain stops, and on a fresh deployment it stops most often at the connection between the circuit and the gateway, because that is the step a hurried deployment skips.

## Root cause six: asymmetric routing after a failover

The most intellectually slippery cause is asymmetric routing, because nothing is technically down. Every layer reports healthy, both sessions are established, prefixes are exchanged in both directions, and yet specific flows break, often only after a failover or a routing change, and often only for certain destinations or certain protocols. The reason is that traffic leaves on one path and returns on a different one, and a stateful device somewhere in the path, a firewall most commonly, drops the return packets because it never saw the outbound half of the conversation. Asymmetry is invisible to the per-layer reads above precisely because no single layer is broken; the break is in the relationship between the forward and reverse paths.

Asymmetric routing on ExpressRoute typically appears in one of a few patterns. A common one is a topology that has both an ExpressRoute path and a VPN path to the same on-premises network, where outbound traffic prefers the ExpressRoute path because of route preference while return traffic comes back over the VPN, or the reverse, splitting the flow across two stateful firewalls that each see only one direction. Another appears after a planned or unplanned failover between the primary and secondary links, or between two circuits in an active-active design, where the forward path moves to the new link but the reverse path has not converged, leaving a window where flows cross. A third shows up when on-premises route preference and Azure route preference disagree about which path is best, so the two ends each pick a different link as primary.

```bash
# Compare what each path receives and advertises to spot a preference split.
# Different prefixes or different preferences on primary versus secondary hint at asymmetry.
az network express-route list-route-tables \
  -g rg-hybrid-core -n er-circuit-prod --path primary \
  --peering-name AzurePrivatePeering --output table
az network express-route list-route-tables \
  -g rg-hybrid-core -n er-circuit-prod --path secondary \
  --peering-name AzurePrivatePeering --output table
```

Confirming asymmetry takes a flow-level view rather than a layer-level one. The signal is that connectivity tests like a simple reachability probe may succeed while application sessions that hold state fail, or that traffic works in one direction and not the other. A packet capture at the firewall that shows outbound packets with no matching return, or return packets with no matching outbound, is the definitive evidence. On the Azure side, comparing the prefixes and route preferences received over each path, and checking whether a competing VPN connection is advertising overlapping prefixes, points at where the forward and reverse paths diverge.

The fix is to make the forward and reverse paths agree, and the right mechanism depends on the topology. Where the asymmetry comes from competing ExpressRoute and VPN paths, the resolution is to set a deterministic preference so both directions favor the same path, using connection-level routing weight or local preference so the two ends do not disagree about which link is best. Where a stateful firewall sits in the path, the cleaner fix is often to ensure the firewall sees both directions by steering both halves through it, or to remove the statefulness for the flows that cross. Where the asymmetry is transient after a failover, the answer is to tune convergence and to design the failover so the reverse path follows the forward path. The unifying principle is that ExpressRoute redundancy and dual-path topologies introduce multiple valid paths, and stateful middleboxes punish any flow whose two halves take different ones, so the cure is determinism in path selection rather than any change to the circuit itself.

A sibling failure mode worth knowing about, because it presents almost identically from the application's point of view, is a VPN tunnel that drops or refuses to establish in a topology that uses VPN as a backup to ExpressRoute. When the ExpressRoute path degrades and traffic should fail over to the VPN but the tunnel is itself broken, the result looks like an ExpressRoute problem when it is in fact a backup-path problem. Diagnosing the tunnel half of such a topology follows its own method, covered in the companion guide to fixing a [VPN gateway tunnel that is down](/2023/01/09/fix-vpn-gateway-tunnel-down/), and in any design that pairs the two, both paths need their own health checks so a failover does not land on a path that was quietly broken all along.

## How to prevent an ExpressRoute circuit-down incident

Prevention for ExpressRoute splits cleanly into things you fix in configuration and monitoring, which are yours, and structural single points of failure, which require design decisions and budget. Treating both honestly is what turns a recurring fire drill into a non-event, and the discipline is to address the layers the layer table named rather than buying redundancy you do not need while ignoring the misconfiguration that actually bites.

The highest-value preventive change costs nothing in infrastructure: calibrate monitoring to the layer it watches. Alert on the service provider provisioning state changing, on each BGP session's neighbor state per path, and on the received-prefix count dropping toward zero, and give these different severities. A single BGP session dropping over redundant links is a degraded-resilience event that should page at a lower severity, while both sessions dropping or the provider state failing is an outage that should page hard. Wiring that distinction in removes the panic that the redundancy-masking cause creates and ensures the response matches the reality. Monitoring the received-prefix count specifically is what catches the route-count-limit problem before it trips, because a steadily climbing prefix count is a warning that you are approaching the cap, and you would rather summarize routes on a schedule than discover the cap when the session sheds everything at once.

The second preventive layer is configuration hygiene that you can audit on a cadence rather than rediscover during an incident. Keep the BGP parameters documented and version-controlled: the peer ASN, the /30 subnets with which address belongs to whom, the VLAN tags, and whether MD5 authentication is in use, so a session that will not establish can be checked against a known-good record rather than reverse-engineered. Summarize on-premises advertisements deliberately so the prefix count stays comfortably under the private-peering limit with headroom for growth, and know whether your circuit carries the premium add-on, because the limit differs. Document the connectivity model, whether you run your own edge or the carrier runs layer 3, because that single fact determines who owns the BGP row in the layer table and therefore who you escalate a session failure to. Each of these is a fact that, written down once, saves an argument during the next incident.

### How do I keep an ExpressRoute outage from taking everything down?

Build redundancy at the layer that actually fails. A second circuit through a second provider in a second peering location removes the single-provider, single-location layer-2 risk that no command can fix. Add a VPN backup for graceful failover, calibrate monitoring to distinguish a single dropped link from a true outage, and keep advertised prefixes under the peering limit.

The structural preventions cost money and belong in the design review rather than the incident, but they are the only answer to the layer that is not yours. A single circuit through a single provider terminating in a single peering location has three stacked single points of failure: the provider, the location, and the physical segment, none of which you can fix from a terminal. Genuine resilience means a second circuit, ideally through a different connectivity provider and a different peering location, so that a carrier outage or a facility problem cannot take the whole connection down. For workloads that can tolerate the lower bandwidth and higher latency of an internet path during a failure, a VPN connection configured as a backup to the ExpressRoute path provides graceful degradation rather than an outage, though it introduces the asymmetric-routing risk discussed above and must be tested so the failover does not land on a broken tunnel. The decision of how much redundancy to buy is a function of how much an outage costs the business, and that calculation, not a default, is what should drive the topology. To build and tear down these redundant topologies in a sandbox so the failover behavior is proven before it matters, [the hands-on Azure labs on VaultBook](https://vaultbook.org/tools/azure-labs.html) include dual-circuit and circuit-plus-VPN designs you can exercise end to end.

## Failures often mistaken for an ExpressRoute circuit down

Several problems present as an ExpressRoute outage while having nothing to do with the circuit, and recognizing them keeps you from debugging the wrong system entirely. The pattern in every case is that the symptom, lost reachability to or from on-premises, points the finger at the most visible piece of hybrid infrastructure, the circuit, when the actual break is elsewhere in the path.

The most frequent impostor is a name-resolution failure that has nothing to do with routing. If applications can reach on-premises systems by IP address but fail by hostname, the circuit is fine and DNS is the problem, often a conditional forwarder or a Private DNS zone link that is not resolving the on-premises names from inside the virtual network. The tell is that a reachability test by address succeeds while the application that uses names fails, which immediately moves the investigation off the circuit and onto the resolver chain. Spending time on ARP tables and BGP states when the route table is healthy and only name resolution fails is a classic misdirection.

A second impostor is a network security group or firewall rule that blocks the traffic after it has crossed a perfectly healthy circuit. The prefixes are advertised, the session is up, the route table shows the on-premises networks, and yet a specific flow fails because a security rule denies it. This looks like a partial outage tied to particular destinations or ports, which is the signature of a filtering rule rather than a routing failure, and the route table being healthy while specific flows die is the distinguishing evidence. The circuit carries the packet to the subnet; what happens at the subnet boundary is a separate control.

A third impostor is the gateway-not-connected case described as root cause five, which technically is an ExpressRoute-adjacent problem but is so commonly misread as a circuit failure that it belongs on this list too. The circuit is healthy in every read, but no VNet traffic moves because the connection object is missing, and an engineer who stops at the circuit concludes the circuit is broken. The cure for all three impostors is the same end-to-end tracing discipline: do not stop at the circuit. Confirm the circuit, then confirm the gateway and connection, then confirm the route table inside the VNet, then confirm the security rules at the subnet, then confirm DNS resolution. The break is wherever that chain stops, and three of the most common stopping points are not the circuit at all.

## Reading the BGP neighbor state correctly

The route-table summary reports a neighbor state, and knowing what each state means turns that one field into a precise diagnosis rather than a binary up-or-down read. BGP moves a session through a sequence of states as it establishes, and a session stalled in a particular state points at a particular layer, so an engineer who reads the state rather than just noticing it is not established can often skip straight to the cause.

A neighbor in the Idle state has not even begun to establish, which usually means the lower layer is missing: there is no TCP path to the peer, often because layer 2 is down or the addresses on the /30 do not match, so an Idle neighbor sends you back to the ARP table to confirm the physical adjacency. A neighbor cycling through Connect and Active is attempting the TCP session and failing, which points at a reachability or addressing problem between the two routers, a wrong remote address, or a firewall blocking the BGP port on the path. A neighbor in OpenSent or OpenConfirm has a TCP session but is failing the BGP negotiation itself, which points at a parameter mismatch such as the wrong ASN or a disagreement on authentication. A neighbor that reaches Established has agreed to exchange routes, and from there the only remaining question is the prefix count, which is the route-advertisement layer. Mapping the state to the layer this way means you are not guessing; the state names where in the establishment sequence the session got stuck, and the layer table names the owner of that layer.

### What does an Established session with zero prefixes mean?

It means the routers completed the BGP handshake but exchanged no routes, so the failure is route advertisement, not the session. The usual causes are a private-peering route-count limit shedding prefixes, an on-premises router not announcing the expected networks, or a missing gateway connection on the Azure side. Read the full route table to see exactly what arrived.

Microsoft peering adds a wrinkle that private peering does not have, and it produces its own version of a circuit-down symptom that catches teams off guard. On Microsoft peering, the public prefixes you advertise must be registered to you and pass a validation step, and if the advertised public prefixes fail validation, Microsoft will not accept them even though the BGP session is established. The result is a session that looks up but carries none of the public prefixes you expected, which presents as a Microsoft-peering outage while private peering on the same circuit is perfectly healthy. The confirming read is the peering's advertised-public-prefixes state, which reports whether validation succeeded, and the fix is to ensure the prefixes are registered to you in a routing registry and that the autonomous system number you claim matches the registration. This is a configuration and registration problem on your side rather than a connectivity failure, and escalating it to the carrier wastes time because the layer-2 segment and the session are both fine.

```bash
# For Microsoft peering, confirm the advertised public prefixes validated.
az network express-route peering show \
  --resource-group rg-hybrid-core \
  --circuit-name er-circuit-prod \
  --name MicrosoftPeering \
  --query "microsoftPeeringConfig.{prefixes:advertisedPublicPrefixes, state:advertisedPublicPrefixesState}" \
  --output table
```

There is also a circuit-down variant that only appears in topologies using Global Reach, the capability that links two ExpressRoute circuits so two on-premises sites can reach each other through the Microsoft network. When the symptom is that site-to-site connectivity between two on-premises locations has failed, the instinct is to look at the circuit carrying the traffic, but the break may be in the Global Reach association between the two circuits rather than in either circuit's connection to Azure. Each circuit can be perfectly healthy in its own reads, with provider state Provisioned, sessions established, and prefixes flowing to Azure, while the on-premises-to-on-premises path is down because the Global Reach link between them was removed, never created, or affected by a route-advertisement problem specific to that path. The diagnosis is to confirm the Global Reach connection exists and is connected separately from confirming each circuit's health, because a Global Reach failure hides behind two circuits that both report healthy when measured against Azure rather than against each other. This is the same lesson the layer table teaches in a different shape: the symptom points at the most visible object, the circuit, while the break sits in a relationship that none of the per-circuit reads expose unless you specifically look for it.

The throughput dimension is the last thing the neighbor state does not show, and it produces a softer version of circuit-down that is in fact circuit-saturated. A circuit provisioned at a given bandwidth, and an ExpressRoute gateway sized at a particular SKU, each impose a ceiling, and when traffic approaches that ceiling the connection does not report itself as down but begins dropping or delaying packets, which applications experience as intermittent failures that look like a flapping connection. The tell is that the layer reads all come back healthy, the sessions are established, prefixes are flowing, and yet performance degrades under load, with the degradation correlating to traffic volume rather than to any session state change. The confirming evidence is the bytes-in and bytes-out metrics pushing against the provisioned bandwidth or the gateway SKU's documented throughput, and the fix is to raise the circuit bandwidth, move to a larger gateway SKU, or shed traffic, none of which is a troubleshooting action on a broken layer because no layer is broken. Distinguishing saturation from an outage matters because the response is capacity planning, not incident remediation, and treating a saturated circuit as a down circuit sends you reading session states that will never reveal the problem.

## A worked diagnosis: one circuit-down incident from alert to fix

Walking a realistic incident end to end shows how the layer table turns a frightening alert into a short, ordered investigation. Picture the page that lands at 2 a.m.: monitoring reports that the production ExpressRoute connection is down, an application that reaches an on-premises payments system is throwing connection timeouts, and the on-call engineer has a dashboard full of red. The temptation is to start somewhere visible, restart the gateway, or call the carrier and demand they fix it. The disciplined response is three reads in order, and each read either localizes the break or sends the investigation to the next layer.

The first read is the circuit object and its two provisioning states. The engineer runs the show command and sees a circuit provisioning state of Enabled and a service provider provisioning state of Provisioned. That single fact rules out the carrier's control plane as the cause and means the carrier believes their side is lit. It does not yet rule out a transient layer-2 fault, so the next read is the ARP table on both paths.

```bash
# 2:01 a.m. read one: both provisioning states.
az network express-route show -g rg-hybrid-core -n er-circuit-prod \
  --query "{circuit:circuitProvisioningState, provider:serviceProviderProvisioningState}" -o table
# Result: circuit=Enabled, provider=Provisioned. Carrier control plane is fine.
```

The ARP read comes back with both the on-premises and the Microsoft interface addresses resolving on the primary path and on the secondary path. Layer 2 is healthy on both links, which moves the break decisively above the physical layer and tells the engineer not to call the carrier yet, because the carrier's segment is carrying frames. With the bottom two rows of the layer table cleared, the investigation moves to BGP.

```bash
# 2:03 a.m. read two: ARP on both paths resolves. Layer 2 is healthy. Not the carrier.
az network express-route list-arp-tables -g rg-hybrid-core -n er-circuit-prod \
  --path primary --peering-name AzurePrivatePeering -o table
az network express-route list-arp-tables -g rg-hybrid-core -n er-circuit-prod \
  --path secondary --peering-name AzurePrivatePeering -o table
```

The route-table summary is the read that breaks the case open. It shows both neighbors in the established state, which at first glance looks like everything is fine and contradicts the outage, except the received-prefix count reads zero on both paths. An established session carrying no prefixes is the route-advertisement signature, not a connectivity failure, and it immediately reframes the whole incident: nothing is physically broken, and the carrier has nothing to fix. The prefixes that should be arriving from on-premises are not arriving.

```bash
# 2:05 a.m. read three: both neighbors established, zero prefixes received.
# Session is up, route advertisement has failed. The fix is in routing, and it is ours.
az network express-route list-route-tables-summary -g rg-hybrid-core -n er-circuit-prod \
  --path primary --peering-name AzurePrivatePeering -o table
```

From here the diagnosis narrows quickly. The engineer checks the timeline and finds that a change went into the on-premises routing earlier in the evening that added a large block of unsummarized prefixes, pushing the advertised count past the private-peering limit, at which point the session shed every route rather than degrading partially. The fix is not a gateway restart and not a carrier ticket; it is to summarize the on-premises advertisement back under the limit. Once the on-premises routers advertise the aggregated prefixes, the count falls under the cap, the session accepts the routes, and the prefix count climbs from zero to the expected value. Reachability returns without anyone touching the gateway or the carrier. The entire incident, from alert to fix, took the three reads plus a look at the change log, and the reason it was fast is that each read localized the break to one row of the layer table before any action was taken.

The counterfactual is worth holding in mind, because it is the version that takes two hours. An engineer who skips the reads and acts on the alert text restarts the gateway first, which does nothing because the gateway was never the problem, then opens an urgent carrier ticket, which the carrier closes after confirming their segment is healthy, then finally, an hour and a half in, someone reads the prefix count and sees the route-advertisement failure that was visible in the first five minutes. Same root cause, same fix, ten times the duration, because the investigation chased the symptom instead of localizing the layer. The reads are not bureaucracy; they are the shortest path to the fix.

## Making the gateway and connection repeatable as code

Several of the causes above, particularly the missing connection between the circuit and the gateway and the drift in BGP and peering parameters, are prevented far more reliably by infrastructure as code than by careful manual work. When the gateway, the circuit reference, and the connection are defined in a template that is reviewed and deployed as a unit, the fresh-deployment gap where someone forgets to wire the connection simply cannot happen, because the connection is part of the same artifact as the gateway. Capturing the topology as code also gives you the known-good record that the configuration-hygiene part of prevention depends on, so a session that will not establish can be compared against the committed definition rather than reverse-engineered.

A Bicep definition for the Azure side of the topology makes the gateway and connection a single reviewable change. The circuit itself is often provisioned through the carrier's process, so the template references an existing circuit by resource ID and builds the gateway and the connection around it, which is the part that the fresh-deployment gap most often misses.

```bicep
// expressroute-gateway.bicep
// Wires an ExpressRoute gateway to an existing, provider-provisioned circuit.
param location string = resourceGroup().location
param vnetName string
param gatewaySku string = 'ErGw1AZ'
param circuitResourceId string

// The gateway must live in a subnet literally named GatewaySubnet.
resource gatewaySubnet 'Microsoft.Network/virtualNetworks/subnets@2023-09-01' existing = {
  name: '${vnetName}/GatewaySubnet'
}

resource gatewayPip 'Microsoft.Network/publicIPAddresses@2023-09-01' = {
  name: 'pip-ergw-prod'
  location: location
  sku: { name: 'Standard' }
  properties: { publicIPAllocationMethod: 'Static' }
}

resource erGateway 'Microsoft.Network/virtualNetworkGateways@2023-09-01' = {
  name: 'ergw-prod'
  location: location
  properties: {
    gatewayType: 'ExpressRoute'
    sku: { name: gatewaySku, tier: gatewaySku }
    ipConfigurations: [
      {
        name: 'ergwIpConfig'
        properties: {
          subnet: { id: gatewaySubnet.id }
          publicIPAddress: { id: gatewayPip.id }
        }
      }
    ]
  }
}

// This connection is the piece the fresh-deployment gap forgets. Defining it here
// means the gateway and the wiring to the circuit ship as one reviewed unit.
resource erConnection 'Microsoft.Network/connections@2023-09-01' = {
  name: 'conn-er-prod'
  location: location
  properties: {
    connectionType: 'ExpressRoute'
    virtualNetworkGateway1: { id: erGateway.id }
    peer: { id: circuitResourceId }
    routingWeight: 100
  }
}
```

The routing weight on the connection is more than a default to leave alone, because it is the lever that prevents one flavor of the asymmetric-routing problem. In a topology that has both an ExpressRoute connection and a VPN connection to the same on-premises network, the routing weight sets which path Azure prefers, and setting it deterministically on both the ExpressRoute and the VPN connections is how you keep the forward and reverse paths from disagreeing about the best link. Encoding that weight in the template, rather than leaving it to a manual setting that someone might change without thinking, makes the path preference a reviewed decision rather than an accident waiting to surface after the next failover.

The peering parameters that BGP depends on also belong under version control, even if the carrier provisions them in the IPVPN model, because the committed record is what lets you confirm a session against a known-good state during an incident. A small declarative file that records the peer ASN, the primary and secondary /30 subnets with the address assignment, the VLAN tag, and whether MD5 authentication is in use turns the BGP-parameter-mismatch diagnosis from a reverse-engineering exercise into a one-line comparison. The same applies to the on-premises advertisement policy: documenting the summarized prefixes you intend to advertise, and the count that keeps you under the private-peering limit with headroom, means the route-count-limit cause is something you audit against a target rather than discover when the session sheds its routes. None of this removes the need to read state during an incident, but it shrinks the space the incident can hide in, because the difference between the running state and the committed definition is itself a diagnostic signal. The reads tell you what the connection is doing; the code tells you what it is supposed to be doing, and the gap between them is often the answer.

## The verdict: name the layer, name the owner

The single habit that resolves an ExpressRoute circuit down faster than any command memorization is to refuse to act until you have named the layer. The connection is not one switch; it is a stack of four mechanically separate parts, and the symptom at the top is identical regardless of which part broke. The provider link at layer 2, the BGP sessions over the primary and secondary links, the peerings that ride them, and the route advertisement that decides what moves are each a distinct failure domain with a distinct owner. Read the provider state, then the ARP table for layer 2, then the route-table summary for BGP and prefixes, and the three reads localize the break to a single row of the layer table before you change anything.

The reason the layer-and-owner rule matters so much in practice is that the two most expensive mistakes in an ExpressRoute incident are mirror images of each other, and both come from skipping the localization. Escalating a route-advertisement problem to the carrier, when the session is up and the route table is empty, wastes a round trip on a layer-2 owner whose segment is healthy. Trying to fix a layer-2 provider fault from your own routers, when ARP is empty and the carrier's segment is dead, wastes effort on a layer you do not own. The state column of the layer table sorts these in one read: ARP empty on the carrier's path means the owner is the provider, while an up session with a bare route table means the owner is you. Get the owner right and the fix is fast; get it wrong and you lose the incident to a ticket bouncing between two teams who each correctly believe the problem is not theirs.

If you take one thing from this guide into the next incident, let it be the order of operations. Provider state first, because if the carrier has not lit the link, nothing above it can work and the action is a ticket with the service key and the affected path. ARP next, because it draws the line between layer 2 and layer 3 cleanly. Route-table summary after that, because the neighbor state and the prefix count together distinguish a down session from an up session carrying nothing, which are different problems with different owners. Then trace upward through the gateway, the connection, the VNet route table, and the security rules to catch the impostors that are not the circuit at all. ExpressRoute rewards engineers who reason about the stack and punishes those who treat it as a single object, and the layer table is the artifact that keeps the reasoning honest under pressure.

## Frequently Asked Questions

### Q: Why is my ExpressRoute circuit down even though the portal shows it enabled?

The circuit's enabled state only reports that Azure has provisioned the circuit object; it is a control-plane fact, not a statement that traffic is flowing. A circuit can read as enabled while the service provider provisioning state is still NotProvisioned, meaning the carrier has not lit the physical segment, or while both BGP sessions are down so no routes are exchanged. The headline state and actual reachability are independent. To find the real problem, read the service provider provisioning state, the ARP table on each path to confirm layer 2, and the route-table summary to confirm the BGP neighbor state and prefix count. The break sits at whichever of those reads comes back unhealthy, and only one of them, the provider state and ARP, points at the carrier. The other reads point at routing problems that are usually yours to fix, so trusting the enabled state alone sends you debugging the wrong layer.

### Q: Does a single dropped BGP session take the whole ExpressRoute connection offline?

No, and assuming it does causes a large share of the unnecessary panic around ExpressRoute alerts. The connection runs two independent BGP sessions, one over the primary link and one over the secondary, and the design intent is that either can carry the full logical connection while the other is degraded. A single dropped session reduces resilience and capacity but does not take reachability offline as long as the surviving session is established and carrying prefixes. The way to confirm this is to read the route-table summary for both paths and look at the contrast: a single-link event shows one neighbor established and one down, while a true outage shows both down. If applications are still working while one session is down, redundancy is doing exactly what it was built to do, and the response is to restore the lost path without emergency escalation. Calibrating monitoring to alert at different severities for one-link versus both-links removes the panic permanently.

### Q: Is the connectivity provider or the layer-2 link the cause of my circuit failure?

Read the ARP table and the service provider provisioning state to decide. The ARP table maps the on-premises and Microsoft router interface addresses to hardware addresses for a given peering and path, and it is a pure layer-2 view. If ARP resolves for both sides, layer 2 is healthy and the break is higher up in BGP or route advertisement, which is usually yours. If ARP is empty on a path the carrier owns, or the service provider provisioning state reads anything other than Provisioned, the physical or provider segment is the suspect and the fix belongs to the carrier. The action then is a ticket containing the circuit service key, the affected path, the timestamp the ARP resolution was lost, and the ARP output showing the missing entries. A ticket with that evidence is one the carrier can act on, whereas a vague report of an outage starts a slow round trip. Reading ARP before escalating is what keeps the ticket from going to the wrong team.

### Q: Why are my routes not advertised over ExpressRoute when the session is up?

An established BGP session means the two routers agreed to talk; it does not guarantee they exchanged any prefixes, so an up session can carry zero routes. The common reasons are a private-peering route-count limit that forces the session to shed prefixes when the advertised count crosses the cap, an on-premises router that is not advertising the expected networks because of a routing-policy gap, or an Azure-side gap where the ExpressRoute gateway is not connected to the circuit so virtual-network prefixes never advertise. Read the received-prefix count in the route-table summary; if it is zero on an established session, the problem is advertisement rather than connectivity. The fix follows the family: summarize on-premises routes to stay under the limit or enable the premium add-on if the larger limit is genuinely needed, correct the on-premises advertisement policy, or create the gateway connection. Escalating an empty route table to the carrier wastes time because their layer-2 segment is healthy.

### Q: How do I check the ExpressRoute circuit and peering state from the command line?

Read three things in order. First, the circuit object with `az network express-route show`, querying the circuitProvisioningState and serviceProviderProvisioningState, which tell you whether Azure and the carrier each have their side ready. Second, the peering list with `az network express-route peering list`, which shows which peerings exist and the subnets and ASN they use; a missing peering is a configuration or provisioning gap rather than a session failure. Third, the route-table summary with `az network express-route list-route-tables-summary` for each path, which reports the BGP neighbor state and the received-prefix count, the single most informative read because it distinguishes a down session from an up session carrying nothing. The ARP table from `az network express-route list-arp-tables` adds the layer-2 view that separates a carrier fault from a routing problem. PowerShell offers the same facts through Get-AzExpressRouteCircuitRouteTableSummary, Get-AzExpressRouteCircuitARPTable, and Get-AzExpressRouteCircuitRouteTable. Read provider state, then ARP, then the route summary.

### Q: What does an empty ARP table on an ExpressRoute peering tell me?

The ARP table is a layer-2 mapping of interface IP addresses to hardware addresses for a peering and path, so an empty table is a strong signal that layer 2 is not healthy on that path. If both the on-premises and Microsoft sides are missing, the physical or provider segment for that path is almost certainly the break, which points at the carrier rather than at your routing configuration. If only one side resolves, the partial mapping suggests the adjacency is forming but not complete, which can mean a one-sided physical problem or an addressing mismatch on the /30 subnet. Because ARP sits below BGP, you cannot have a working BGP session over a path whose ARP is empty, so confirming ARP first saves you from chasing a BGP parameter problem that is in fact a physical fault. When ARP is empty on a carrier-owned path, gather the output and the service key and open a carrier ticket rather than changing your own router configuration.

### Q: What is the difference between Azure private peering and Microsoft peering when troubleshooting?

The two peerings are separate routing contexts on the same circuit, and a failure in one does not imply a failure in the other, so you must troubleshoot the one that carries the affected traffic. Azure private peering carries traffic to your private virtual networks and is what most hybrid workloads depend on, while Microsoft peering carries traffic to the public endpoints of platform and software services. Each peering has its own pair of BGP sessions over the primary and secondary links, its own ARP tables, and its own route tables, so the diagnostic reads take a peering name argument and you run them against the specific peering that matters. A private peering session can be down while Microsoft peering is fine, or the reverse, and treating them as one thing leads to reading the healthy peering's state and concluding everything is fine while the broken one stays broken. Always confirm which peering the failing traffic uses, then run the layer-2 and BGP reads against that peering specifically.

### Q: Why did my ExpressRoute BGP session drop after I added more on-premises routes?

This is the classic route-count-limit symptom. Azure private peering accepts a bounded number of prefixes, and when the advertised count crosses the cap, the session does not degrade gracefully; it drops the routes and refuses to reestablish them until the advertised prefix count comes back under the limit. So a change that increased the number of advertised prefixes, often an unsummarized advertisement of many small networks, can trip the cap and present as a session that flaps or carries nothing right after the change. The confirming evidence is a received-prefix count that sits at the limit just before the drop, correlated with the timing of your routing change. The fix is to reduce the advertised prefix count by summarizing on-premises networks into fewer, larger prefixes so the count falls back under the cap, or to enable the premium add-on if the larger limit is genuinely required. Confirm the current limit against Microsoft's published figures, because Azure revises them, but the shedding behavior is durable.

### Q: My ExpressRoute circuit looks healthy but no virtual network traffic moves. What is missing?

The most likely gap is that the circuit is not connected to a gateway. A circuit can be provisioned, have private peering configured, and have both BGP sessions established, yet carry no traffic to your virtual networks, because the circuit by itself does not terminate inside Azure. Reaching a virtual network requires an ExpressRoute gateway deployed in that network's GatewaySubnet and a connection object that links the gateway to the circuit. If every circuit read comes back green but VNet traffic fails, confirm the gateway exists and is of the ExpressRoute type, confirm a connection references both the gateway and the circuit, and confirm that connection reports a connected status. On a fresh deployment this is the step most often skipped, because an engineer who only checks the circuit sees health everywhere and concludes the circuit is broken when the real gap is the missing connection between the circuit and the gateway.

### Q: How does ExpressRoute redundancy actually work across the primary and secondary links?

ExpressRoute provisions two links for every circuit, a primary and a secondary, and runs an independent BGP session over each. The two links are not active and standby in the sense of one sitting idle; both are intended to be up and both carry traffic, so the loss of either degrades capacity and resilience without taking the logical connection offline as long as the other link holds. This is why a single dropped session is a degraded-resilience event rather than an outage, and why monitoring should distinguish a one-link drop from a both-links drop. The redundancy is at the link layer within a single circuit and a single peering location, however, so it protects against a single physical link or session failing, not against the connectivity provider having an outage or the peering location going dark. Protecting against those larger failures requires a second circuit, ideally through a different provider and a different location, which is a design decision rather than something the built-in dual-link redundancy provides.

### Q: Why does specific application traffic fail over ExpressRoute while reachability tests succeed?

That pattern points at asymmetric routing rather than a circuit failure. When a simple reachability probe succeeds but stateful application sessions fail, traffic is likely leaving on one path and returning on a different one, and a stateful device in the path, usually a firewall, drops the return packets because it never saw the outbound half. This happens in topologies with both an ExpressRoute and a VPN path to the same network, after a failover where the forward path moved but the reverse path has not converged, or when on-premises and Azure route preferences disagree about which link is best. The confirming evidence is a packet capture at the firewall showing outbound packets with no matching return, or the reverse. The fix is to make the forward and reverse paths agree through deterministic route preference, or to ensure the stateful device sees both directions. Nothing in the circuit itself is broken, which is why the per-layer reads all come back healthy.

### Q: Should I escalate an ExpressRoute problem to my carrier or fix it myself?

Decide by which layer broke, because the layer names the owner. If the service provider provisioning state is not Provisioned, or the ARP table is empty on a carrier-owned path, the physical or layer-2 segment is the break and it belongs to the carrier; the action is a ticket with the service key, the affected path, and the ARP evidence. If the provider state is Provisioned and ARP resolves but the BGP session is down or the route table is empty on an established session, the break is at routing, which is almost always yours unless your circuit uses the IPVPN model where the carrier operates the layer-3 edge. The most expensive mistakes are escalating a routing problem to a carrier whose segment is healthy, and trying to fix a physical fault from your own routers. Reading the provider state and the ARP table before you escalate sorts the owner in one step and keeps the ticket from bouncing between two teams.

### Q: How do I confirm whether my circuit uses the IPVPN model or my own edge routers?

The connectivity model determines who owns the BGP and peering layers, so it is worth confirming once and documenting. In the model where you run your own customer edge routers, only the physical port is the carrier's, and you configure and own the BGP sessions, the peering parameters, and the route advertisement entirely. In the IPVPN model, the provider operates the layer-3 edge, so the carrier configures the peering and the BGP session on your behalf, and a session that will not establish becomes a carrier ticket rather than a change on your equipment. A practical tell is whether you have ever configured BGP parameters on your own routers for this circuit, or whether the peering simply appeared in the portal after the provider finished their work. If the peering shows up provisioned without you touching router configuration, you are likely on the IPVPN model. Knowing this before an incident is what prevents an engineer from changing router config they do not actually own.

### Q: Why does my ExpressRoute peering show as blank in the portal?

A blank peering usually means the layer-3 configuration is incomplete rather than that a session failed. In the IPVPN connectivity model, the service provider configures the layer-3 peering, so a peering that is blank in the portal after the provider was supposed to configure it often means the carrier has not finished their part, not that you misconfigured anything. The first remedy is to refresh the circuit configuration using the refresh action in the portal, which reapplies the routing configuration on the circuit and can populate a peering that is present on the carrier side but not yet reflected in Azure. If the peering stays blank after a refresh, confirm with the carrier whether they have completed the layer-3 provisioning for that peering. If you run your own edge and configure the peering yourself, a blank peering instead means your create operation did not complete, and you would recreate or correct the peering with the right subnets, ASN, and VLAN. The model determines which of these two paths applies.

### Q: Can a flapping ExpressRoute BGP session be fixed from the Azure side?

Sometimes, but often the cure is elsewhere, so confirm the cause before changing Azure configuration. A flapping session, one that reaches established and then drops on a cycle, has two common roots. The first is a route-count problem where the advertised prefix count hovers near the private-peering limit, so the session repeatedly sheds routes and renegotiates; that one is fixed from your side by summarizing advertisements to stay comfortably under the cap. The second is a layer-1 problem, a marginal optic or a link carrying errors, which is the carrier's to chase and which you cannot fix from Azure at all. Distinguish them by watching the route-table summary over time: a flap tied to the prefix count resetting near the limit points at the route-count cause, while a flap with a healthy prefix count and no correlation to advertisement changes points at layer 1. Persistent flapping you cannot tie to a route limit is layer-1 evidence to hand the carrier, with the ARP and route summaries over time as the supporting data.

### Q: What should I include in an ExpressRoute ticket to my connectivity provider?

Include enough for the carrier to act without a round trip. The circuit service key is essential, because that is how the carrier identifies your connection on their side; without it they cannot locate the circuit. State precisely which paths are affected, primary, secondary, or both, since a single-path fault and a both-paths fault are different problems for them. Include the timestamp the connectivity or ARP resolution was lost, so they can correlate it with their own logs and any maintenance window. Note whether the service provider provisioning state changed, and attach the ARP table output showing the missing entries as evidence that layer 2 is the suspect. If the session flaps rather than drops cleanly, include the route-table summaries captured over time showing the oscillation. A ticket with the service key, the affected path, the timestamp, and the ARP evidence is one the carrier can investigate immediately, while a ticket that just reports an outage starts a slow exchange of clarifying questions during the worst possible moment.

### Q: How can I monitor an ExpressRoute circuit to catch problems before an outage?

Monitor each layer the failure can live in, and give the alerts severities that match the impact. Watch the service provider provisioning state for changes, because a state moving away from Provisioned is a direct statement that the carrier's side changed. Watch each BGP session's neighbor state per path, alerting at a lower severity when one path drops over redundant links and at a high severity when both drop, so a single-link event does not trigger the same panic as a true outage. Watch the received-prefix count, because a count climbing toward the private-peering limit is an early warning that lets you summarize routes on a schedule rather than discovering the cap when the session sheds everything at once, and a count falling toward zero on an up session is the route-advertisement failure signature. Watching bytes in and out per path catches a link that is up but carrying no traffic. The principle is that the circuit is a stack, so the monitoring should watch the stack rather than a single rolled-up health value that hides which layer is degrading.

### Q: Does enabling the ExpressRoute premium add-on fix a route-count problem?

It raises the prefix limit, which addresses the cause when the cause is genuinely a need to advertise more prefixes than the standard private-peering limit allows, but it is not the right first move for every empty route table. The standard private-peering limit accepts a few thousand prefixes and the premium add-on raises that ceiling substantially; confirm the current figures against Microsoft's published limits because Azure revises them. If your on-premises advertisement is large because it is unsummarized, the cheaper and cleaner fix is to summarize those routes into fewer, larger prefixes so the count falls under the standard limit, rather than paying for the premium tier to carry routes you could have aggregated. Reserve the premium add-on for the case where the prefix count is legitimately large after sensible summarization, or where you need its other capabilities such as a higher route limit alongside global reach. Throwing the premium add-on at a route-advertisement problem that is in fact an unsummarized-routing-policy problem treats the symptom and leaves the underlying habit in place.

### Q: Why does traffic work in one direction over ExpressRoute but not the other?

One-directional success is a strong indicator of either asymmetric routing or a filtering rule, and the two are distinguished by where the break sits. If outbound traffic reaches on-premises but return traffic does not arrive, the reverse path may be taking a different route than the forward path, so a stateful firewall on the return path drops packets it has no session for, which is the asymmetric-routing pattern common in topologies with both ExpressRoute and VPN paths. Alternatively, a security rule may permit traffic in one direction and deny it in the other, which presents as clean one-way failure tied to specific ports or destinations while the route table stays healthy. Distinguish them by checking whether the route preferences differ between the forward and reverse paths and whether a packet capture shows the return packets arriving at the firewall, versus checking the security rules at the subnet boundary. Asymmetry is fixed by making both directions prefer the same path; a filtering problem is fixed at the rule.

### Q: Is ExpressRoute reachability loss always a circuit problem?

No, and assuming it is sends you debugging the wrong system. Several failures present as an ExpressRoute outage while the circuit is perfectly healthy. A name-resolution failure makes applications fail by hostname while succeeding by IP address, which is a DNS problem in the resolver chain rather than a routing problem. A security rule or firewall can block specific flows after they have crossed a healthy circuit, presenting as a partial outage tied to particular ports or destinations while the route table shows the networks correctly. A missing connection between the circuit and the gateway leaves the circuit green in every read while no virtual-network traffic moves. The cure is end-to-end tracing rather than stopping at the circuit: confirm the circuit, then the gateway and connection, then the virtual-network route table, then the security rules, then DNS resolution, and the break is wherever that chain stops. Three of the most common stopping points are not the circuit at all, so confirming the circuit's health is the start of the investigation, not the end.
