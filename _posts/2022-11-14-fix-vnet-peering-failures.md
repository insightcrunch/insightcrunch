---
layout: post
title: "Fix Azure VNet Peering Connection Failures"
page_title: "Fix Azure VNet Peering Connection Failures: Disconnected State, Overlapping Address Space, Non-Transitive Routing, and Gateway Transit Diagnosed to Root Cause"
date: 2022-11-14
categories: ["Technology"]
tags: ["Azure", "VNet Peering", "Networking", "Troubleshooting", "Cloud Computing"]
excerpt: "Fix Azure VNet peering failures by root cause: Disconnected state, address overlap, non-transitive routing, and gateway transit, with confirming commands."
image: "/assets/images/blog/blog-70.webp"
reading_time: 60
author: "alex-cunningham"
last_updated: 2022-11-14
lang: en
---
A VNet peering that will not connect, or that connects and still passes no traffic, is one of the most misread failures in Azure networking, because the symptom and the cause almost never live in the same place. You create the link, the portal shows **Disconnected**, and the instinct is to delete the whole thing and start over. Or the two virtual networks show **Connected** on both sides, every blade looks green, and yet a virtual machine in one network cannot reach a virtual machine in the other. The reader who treats either of these as a single bug burns an afternoon recreating resources that were never broken. The reader who knows the four behaviors that actually produce a peering failure finds the cause in minutes and changes exactly one setting.

![Fixing Azure VNet peering connection failures and Disconnected state root causes - Insight Crunch](/assets/images/blog/blog-70.webp)

This article diagnoses VNet peering to root cause. Every failure you will hit reduces to one of a small set of distinct mechanisms: a link configured on only one of the two networks, an address range that overlaps between them, an expectation that traffic will route transitively through a shared hub, a gateway-transit setting that on-premises routes need and never received, or a peering that is genuinely up while a network security group or a route table quietly drops the packet downstream. Each mechanism has a state or a command that confirms it is yours, and each has a fix that touches the real cause rather than rebuilding the relationship. The thesis of this series applies directly here: a peering problem is not a mystery, it is a short list of behaviors, and knowing which one you are looking at is the difference between a five-minute change and a wasted day.

## What a VNet peering actually is, and why the symptom misleads

Before the diagnosis, hold a precise model of what peering does, because most wrong fixes come from a fuzzy one. A peering is not a tunnel, a gateway, or a piece of hardware. It is a pair of objects in the Azure control plane, one belonging to each virtual network, that together instruct the software-defined network to route traffic between the two address spaces over the Microsoft backbone as though the machines sat on adjacent networks. There is no appliance to fail, no bandwidth to provision, no public path involved. The data plane is the same backbone that already carries traffic inside a single network, so once a peering is correctly established the latency between peered networks is effectively the latency of the backbone itself.

The single most important structural fact, and the one that explains the majority of failures, is that a peering is two linked objects, not one. When you peer network A with network B, Azure creates a peering resource on A that points at B, and it expects a matching peering resource on B that points back at A. The relationship is only live when both halves exist and reference each other. If you create the link on A and never create it on B, A reports a state that looks broken, but nothing is broken in the sense of a fault. The relationship is simply half-built. This is why deleting and recreating is so often the wrong move: recreation rebuilds the half that already existed and leaves the missing half still missing.

The second structural fact is that peering moves traffic only between the two networks directly joined by the pair of objects. It does not forward traffic on behalf of a third network. If network A peers with a hub H, and network B also peers with H, traffic from A does not reach B by passing through H, because H's peering with A says nothing about B and H's peering with B says nothing about A. There is no rule that chains them. Engineers expect this chaining because routers on a traditional network forward for one another by default, and Azure peering deliberately does not. The behavior is called non-transitive, and it is not a limitation to work around so much as a property to design for.

### Is a VNet peering one object or two?

A VNet peering is two linked objects, one on each virtual network, that must both exist and reference each other for traffic to flow. Creating the link on only one side leaves the relationship half-built, which is why the incomplete side reports a non-connected state and why recreation alone rarely fixes it.

Hold those two facts, that a peering is a matched pair and that it carries traffic only between the two networks it directly joins, and most of what follows is the consequence of one of them being violated. The remaining failures come from the peering being genuinely healthy while a separate control, a security rule or a custom route, drops the traffic after the peering has already agreed to carry it. The art of fixing peering is deciding, quickly and from evidence, which of those situations you are in.

## How to read the state and gather the diagnostic signal

The platform already tells you which situation you are in, if you ask it the right way. Three signals, read in order, localize almost every peering failure before you change anything: the peering state on each side, the effective routes on the network interface that should be sending the traffic, and a connectivity test that reports the first hop that drops the packet. Reading these three is faster than guessing, and it is the habit that separates a clean fix from a string of hopeful edits.

Start with the peering state, and read it on both networks, not one. Each object reports a `peeringState` that is either `Initiated` or `Connected`. `Initiated` means this side has created its half and is waiting for a matching half on the other network that either does not exist yet or does not point back correctly. `Connected` means both halves exist and agree. The portal surfaces an older label, **Disconnected**, when a peering that was previously `Connected` loses its partner, typically because the matching peering on the other network was deleted or its target network was removed. The Azure CLI reads the state directly:

```bash
# Read the peering state on network A's side
az network vnet peering show \
  --resource-group rg-network \
  --vnet-name vnet-a \
  --name a-to-b \
  --query peeringState -o tsv

# Read the peering state on network B's side
az network vnet peering show \
  --resource-group rg-network \
  --vnet-name vnet-b \
  --name b-to-a \
  --query peeringState -o tsv
```

If one side returns `Connected` and the other returns `Initiated`, or if one side has no peering object at all, you have a one-sided relationship and the cause is structural, not a fault. If both sides return `Connected`, the link itself is healthy and the problem is downstream: routing, a security rule, or a transitivity expectation. That single comparison, the state on A against the state on B, splits the entire problem space in half and tells you which branch of the diagnosis to walk.

The second signal is the effective routes on the network interface of the machine that should originate the traffic. When a peering is `Connected`, Azure injects a system route for the peer network's address space into the route table of every interface in the local network, with a next hop type of `VNetPeering`. If you query the effective routes and the peer's address range is present with that next hop type, routing across the peering is in place and the platform intends to deliver the packet. If the range is absent, the peering is not delivering routes, which points back to the state check. If the range is present but a more specific custom route or a `0.0.0.0/0` route to a virtual appliance overrides it, the packet is being steered somewhere other than the peer:

```bash
# Inspect the effective routes on the NIC that should send the traffic
az network nic show-effective-route-table \
  --resource-group rg-workload \
  --name vm-a-nic \
  --output table
```

The third signal is a direct connectivity test that names the hop where the packet dies. Azure Network Watcher's connection troubleshoot runs a probe from a source virtual machine to a destination address and port and reports whether the path is reachable, and if not, the first hop that drops or blackholes the traffic, naming the resource responsible, a security rule, a route, or a missing path:

```bash
# Probe from a source VM to a destination IP and port across the peering
az network watcher test-connectivity \
  --resource-group rg-workload \
  --source-resource vm-a \
  --dest-address 10.2.0.4 \
  --dest-port 443
```

When the probe reports the path as unreachable and attributes the block to a security rule, the peering is doing its job and a network security group is the cause. When it attributes the block to a route or reports no route to the destination, the cause is routing or a transitivity gap. When it cannot even begin because the peer range is not routed at all, you are back to the state check. These three reads, state on both sides, effective routes, and a targeted probe, are the diagnostic spine of every section that follows.

### How do I confirm the peering state on both sides?

Query `peeringState` on each network's own peering object with the CLI or the portal, and compare the two results. Both must read `Connected`. If either reads `Initiated`, or one side has no peering object, the relationship is half-built and that missing or mismatched half is your cause, not a fault to recreate.

The reason to read all three signals before touching anything is that they distinguish causes that look identical from the application's point of view. A timeout from a client in network A trying to reach a server in network B is the same timeout whether the peering is one-sided, the address spaces overlap, the traffic is expected to transit a hub it cannot, or a security group is dropping it on arrival. The application cannot tell these apart. The state, the routes, and the probe can, and reading them turns a single ambiguous symptom into a specific named cause.

## The InsightCrunch peering failure table

The following table is the findable artifact for this article: the InsightCrunch peering failure map. It pairs each symptom you can observe with the single mechanism that produces it and the fix that addresses that mechanism. Read it as a router. Find your symptom, confirm the cause with the listed signal, and apply the matching fix rather than the reflexive one.

| Symptom you observe | Confirming signal | Root cause | The fix that works |
|---|---|---|---|
| Peering shows Disconnected or one side reads Initiated | State differs between the two sides | One-sided relationship: matching half missing or deleted | Create or repair the peering object on the side that lacks it; do not recreate the side that exists |
| Peering creation is rejected at submit time | Error names overlapping address space | The two networks share an address range | Re-IP one network, or add a non-overlapping range and place workloads there, then peer |
| Both sides Connected, two spokes cannot reach each other | Effective routes lack the far spoke's range with a VNetPeering next hop | Non-transitive routing: spokes peered to a hub do not route through it | Peer the spokes directly, or route spoke-to-spoke through an appliance in the hub with custom routes |
| Peered, but on-premises networks are unreachable from the spoke | Spoke route table lacks the on-premises ranges | Gateway transit not enabled across the peering | Set Allow Gateway Transit on the hub side and Use Remote Gateways on the spoke side |
| Both sides Connected, machines still cannot talk | Probe attributes the block to a security rule | An NSG on the subnet or NIC denies the flow | Adjust the specific NSG rule; do not loosen the peering |
| Peered through a hub appliance, traffic dropped at the hub | Hub forwards nothing despite a route pointing at it | Allow Forwarded Traffic not enabled on the hub's peerings | Enable Allow Forwarded Traffic on the hub peering objects so the hub may relay non-local traffic |

This map is the namable claim of the article in compact form. The claim is the both-sides-and-non-transitive rule: a peering needs a live object on each of the two networks, and it never forwards traffic on behalf of a third network, so a Disconnected state is almost always a missing or mismatched half, and a spoke-to-spoke failure is almost always a transitivity expectation rather than a fault. Hold that rule and the table becomes something you can reconstruct from memory rather than look up. The sections that follow walk each row in depth, with the confirming command and the tested fix.

## Cause one: the relationship is one-sided, and the state reads Disconnected

The most common peering failure, by a wide margin, is a relationship built on only one of the two networks. You open the link blade on network A, create a peering that targets network B, and assume the link is now live. It is not. Azure has created A's half and is waiting for a matching half on B. Until that second object exists and points back at A, A's peering sits in `Initiated`, and if B's half is later deleted while A's remains, A flips to the **Disconnected** label that sends so many engineers down the recreate-everything path.

### Why does my VNet peering show a Disconnected state?

A Disconnected state means this network's peering object lost its partner: the matching peering on the other network was deleted, or the network it targeted was removed. The local half still exists and still points outward, but there is nothing on the far side to agree with it, so the relationship cannot be live.

Confirming this cause takes one comparison. Read `peeringState` on both networks as shown earlier. The signature of a one-sided relationship is asymmetry: A reads `Initiated` or `Disconnected` while B has no peering object at all, or B's peering targets a different network than A, or B once existed and was removed. When you see that asymmetry, you have found the cause, and the fix is to build or repair the missing half, never to tear down the half that is already correct.

There are several distinct ways a relationship ends up one-sided, and naming them matters because the repair differs slightly for each. The first is the simple omission: someone created A's peering and never created B's. This happens constantly when peerings are made by hand in the portal, one blade at a time, and the operator gets interrupted between the two creations. The fix is to create B's peering pointing back at A:

```bash
# Create the missing half on network B, pointing back at network A
az network vnet peering create \
  --resource-group rg-network \
  --vnet-name vnet-b \
  --name b-to-a \
  --remote-vnet vnet-a \
  --allow-vnet-access true
```

Once both halves exist and reference each other, both flip to `Connected` within seconds and the system routes appear. Verify with the state read on both sides and confirm A's `peeringState` has moved from `Initiated` to `Connected`. If it has not, the half you just created targets the wrong network or the wrong subscription, which is the second way a relationship goes one-sided.

The second cause is a half that exists but points at the wrong target. When networks live in different subscriptions or have similar names, it is easy to peer B back to a network that is not A, or to reference A by an identifier that resolves to a different resource. Both halves then read `Initiated` forever because each is waiting for a partner that points back at it, and neither does. The confirming signal is that both sides show `Initiated` with no error, and inspecting each peering's `remoteVirtualNetwork` shows they do not reference each other. The fix is to correct the remote network reference on the mismatched side. Across subscriptions, reference the peer by its full resource ID rather than its name, because a bare name is ambiguous outside the local subscription:

```bash
# Peer across subscriptions using the full resource ID of the remote network
az network vnet peering create \
  --resource-group rg-network \
  --vnet-name vnet-b \
  --name b-to-a \
  --remote-vnet "/subscriptions/<sub-id-of-A>/resourceGroups/rg-network/providers/Microsoft.Network/virtualNetworks/vnet-a" \
  --allow-vnet-access true
```

The third cause is the genuine Disconnected: both halves existed and were `Connected`, and then one half, or the network it lived in, was deleted. The surviving half cannot return to `Connected` on its own because its partner is gone. The confirming signal is that one side reads `Disconnected` and the other side has no peering object or no network at all. The fix is to delete the orphaned surviving half and create the relationship cleanly on both sides, because a Disconnected object cannot be reconnected in place once its partner is destroyed; it must be removed and the pair rebuilt:

```bash
# Remove the orphaned half left in a Disconnected state
az network vnet peering delete \
  --resource-group rg-network \
  --vnet-name vnet-a \
  --name a-to-b

# Recreate both halves so each references the other
az network vnet peering create \
  --resource-group rg-network --vnet-name vnet-a \
  --name a-to-b --remote-vnet vnet-b --allow-vnet-access true

az network vnet peering create \
  --resource-group rg-network --vnet-name vnet-b \
  --name b-to-a --remote-vnet vnet-a --allow-vnet-access true
```

This is the one situation where recreation is correct, and it is worth being precise about why. You are not recreating because the peering was mysteriously broken; you are recreating because the relationship genuinely lost a partner and the orphaned object has no path back to a connected state. The distinction matters because the reflex to recreate is right perhaps one time in five and wrong the other four, when the real issue was an omitted or mistargeted half that recreation does not address.

The fourth and subtlest one-sided case is a permissions failure during creation. Peering across two networks requires write permission on both networks, and the built-in Network Contributor role on each is the cleanest way to grant it. When an operator has rights on A but not on B, creating A's half succeeds and creating B's half fails, leaving the relationship one-sided through no fault of the configuration. The confirming signal is an authorization error in the activity log at the moment the second half was attempted, and a peering object that exists on A but not on B. The fix is to grant the operator the appropriate role on the second network, then create the missing half:

```bash
# Grant the operator rights to peer on network B's resource group
az role assignment create \
  --assignee <operator-object-id> \
  --role "Network Contributor" \
  --scope "/subscriptions/<sub-id>/resourceGroups/rg-network"
```

Across all four variants, the discipline is identical: read the state on both sides first, identify which half is missing or mismatched, and repair that half. The phrase to keep in mind is that a peering is a matched pair, and a pair with one element missing is not a broken pair, it is an incomplete one. The portal's **Disconnected** wording invites the wrong mental model, suggesting a connection that snapped rather than a relationship that was never fully built or that lost a partner. Reading the state on both networks dissolves that confusion every time, and the model this article shares for [how an Azure Virtual Network is structured and how peering links two of them](/2022/02/28/azure-virtual-network-vnet-deep-dive/) makes clear why the matched pair is fundamental rather than incidental.

## Cause two: the address spaces overlap, and the peering is rejected outright

The second mechanism is the one that fails earliest and most visibly. When you try to peer two networks whose address spaces overlap, even partially, Azure refuses the operation at submit time and returns an error naming the conflict. This is not a quiet failure that surfaces later as a timeout; it is an immediate rejection, because the platform cannot build a coherent routing table when the same address could belong to two different networks. There would be no way to decide where to send a packet bound for an address that exists on both sides of the link.

### Can overlapping address space break VNet peering?

Overlapping address space does not merely break peering, it prevents the peering from being created at all. Azure rejects the operation the moment you submit it, because two networks that share any address range cannot be routed between unambiguously. The packet's destination would resolve to two places, so the platform refuses to establish the relationship.

The confirming signal is the error message itself, returned synchronously when you attempt to create the peering. It states that the address spaces overlap and typically names the conflicting ranges. There is no ambiguity to diagnose here; the platform has already told you the exact cause. What requires thought is the fix, because the overlap is usually the symptom of an address-planning decision made long before anyone wanted to peer the networks, and unwinding it touches running workloads.

Confirm the overlap precisely before choosing a remedy by reading the address space of each network:

```bash
# List the address prefixes of each network to find the overlap
az network vnet show \
  --resource-group rg-network --name vnet-a \
  --query addressSpace.addressPrefixes -o tsv

az network vnet show \
  --resource-group rg-network --name vnet-b \
  --query addressSpace.addressPrefixes -o tsv
```

If both return `10.0.0.0/16`, the overlap is total and the networks share every address. If A is `10.0.0.0/16` and B is `10.0.5.0/24`, B sits entirely inside A and the overlap is partial but still fatal to peering. Even a single shared address range blocks the relationship; there is no partial peering that routes the non-overlapping portion. The whole link is refused.

There are three honest ways to resolve an overlap, and they differ sharply in disruption. The least disruptive, when it is available, is to add a second, non-overlapping address range to one of the networks and migrate the workloads that need to be reachable across the peering into a subnet carved from that new range. A virtual network can carry more than one address prefix, so you can extend B with a range that does not collide with A, create a subnet there, and move the relevant machines into it. The machines keep functioning; only their addresses change. Peering then succeeds because the ranges that must communicate no longer overlap:

```bash
# Add a non-overlapping prefix to network B, then a subnet within it
az network vnet update \
  --resource-group rg-network --name vnet-b \
  --address-prefixes 10.0.0.0/16 172.16.0.0/16

az network vnet subnet create \
  --resource-group rg-network --vnet-name vnet-b \
  --name subnet-peered --address-prefixes 172.16.1.0/24
```

The second remedy, more disruptive but sometimes unavoidable, is to re-IP one network entirely. This is the right move when the overlap is total, when the networks must be fully reachable to each other rather than only at a handful of machines, or when the existing addressing was a copy-paste default that should never have been reused. Re-IPing means assigning a new, non-overlapping address space and recreating or readdressing the subnets and the resources inside them, which is real work and a real maintenance window. The investment buys a clean topology that peers without contortion and that can join a larger hub-and-spoke design later without colliding with a sibling network.

The third path is to avoid peering altogether and connect the overlapping networks through an intermediary that performs network address translation, so that each network sees the other behind translated addresses that do not collide. This is the escape hatch for situations where two organizations merge and neither can readdress on a reasonable timeline, or where a regulatory boundary forbids changing one side. It is heavier than peering, it introduces a device to operate and scale, and it gives up the flat, backbone-speed routing that makes peering attractive in the first place. Reach for it only when re-IPing is genuinely impossible, not merely inconvenient.

The lasting fix for overlap is not any single remedy but the address-planning discipline that prevents it. The reason teams collide is that the default address space offered when a network is created is reused across many networks, so a fleet of networks all claim the same range and none of them can ever peer. Planning a non-overlapping address scheme across every network an organization might one day want to connect, even networks that have no relationship today, is the cheap prevention that makes peering a configuration choice later rather than a migration project. The series treatment of [how to plan VNet address space and subnets so future peering stays possible](/2022/02/28/azure-virtual-network-vnet-deep-dive/) develops this discipline in full, and it is the single design decision that most determines whether peering will ever be painful.

A subtle variant of the overlap problem appears when the networks do not overlap each other but one of them overlaps a third network that both are, or will be, peered to. In a hub-and-spoke layout, two spokes can each peer cleanly with the hub yet carry colliding ranges with each other. The hub-to-spoke peerings succeed because neither spoke overlaps the hub, but the moment you try to route between the spokes, the colliding spoke ranges make the routing ambiguous from the hub's perspective. The lesson is that address planning must consider not only the pair you are peering today but the full set of networks that will share routing reachability, because an overlap anywhere in that set eventually surfaces as a failure somewhere.

## Cause three: the non-transitive rule, and why two spokes cannot talk through a hub

The third mechanism produces the most surprising failure, because everything looks correct. Two networks both peered to a shared hub, every peering reading `Connected`, every blade green, and yet a machine in one spoke cannot reach a machine in the other. Nothing is broken. The peerings are healthy. The traffic simply has no route, because Azure peering is non-transitive: a peering carries traffic only between the two networks it directly joins, and it never relays traffic on behalf of a third network.

### Why can two spokes not talk through a peered hub?

Because peering is non-transitive. The hub's peering with spoke one knows nothing about spoke two, and the hub's peering with spoke two knows nothing about spoke one. Neither peering authorizes the hub to forward traffic between the spokes, so a packet from one spoke reaches the hub and then has nowhere defined to go.

This behavior trips up engineers who carry a traditional networking model into Azure, where routers forward for one another by default and a packet finds its way across multiple hops without explicit per-pair configuration. Azure peering deliberately does not chain. When spoke one is peered to the hub, the system route injected into spoke one covers the hub's address range and nothing else. The hub's own ranges are reachable; the second spoke's ranges are not, because no peering told spoke one that the second spoke exists. Confirm this immediately by reading the effective routes on the originating machine:

```bash
# Look for the FAR spoke's address range on the originating NIC
az network nic show-effective-route-table \
  --resource-group rg-spoke-one --name vm-spoke-one-nic \
  --output table
```

The signature of the non-transitive failure is unmistakable in that output: you will see a `VNetPeering` route for the hub's address range and no route at all for the second spoke's range. The platform never learned the second spoke's addresses on this side, so there is nothing to route. This is not a missing fix to a broken thing; it is the absence of a relationship that was never created. The traffic dies not because a rule denies it but because no route describes where it should go, and a packet with no route is dropped.

There are two legitimate ways to give the spokes a path to each other, and choosing between them is a topology decision rather than a troubleshooting step. The first and simplest, when the number of spokes is small and stable, is to peer the spokes directly to one another. A direct peering between spoke one and spoke two is a matched pair like any other, it routes at backbone speed, and it sidesteps the hub entirely for spoke-to-spoke traffic. The cost is that the number of peerings grows with the square of the number of spokes, so a full mesh of many spokes becomes a large set of pairs to create and maintain:

```bash
# Peer the two spokes directly so traffic does not need the hub
az network vnet peering create \
  --resource-group rg-spoke-one --vnet-name vnet-spoke-one \
  --name one-to-two --remote-vnet vnet-spoke-two --allow-vnet-access true

az network vnet peering create \
  --resource-group rg-spoke-two --vnet-name vnet-spoke-two \
  --name two-to-one --remote-vnet vnet-spoke-one --allow-vnet-access true
```

The second way, and the one that scales, is to route spoke-to-spoke traffic through a network virtual appliance or a firewall placed in the hub, using custom routes so the spokes send each other's traffic to the hub appliance, which then forwards it. This is the canonical hub-and-spoke pattern: the spokes peer only to the hub, and a device in the hub relays inter-spoke traffic. It keeps the number of peerings linear in the number of spokes, it gives a single place to inspect and police east-west traffic, and it is why hub-and-spoke is the default enterprise topology. The trade-off is that you now operate and scale the hub appliance, and every spoke-to-spoke packet takes two hops through it rather than one direct hop. Making this work requires two things beyond the peerings: a user-defined route in each spoke that sends the other spoke's range to the hub appliance, and a setting on the hub's peerings that permits the hub to forward traffic it did not originate.

That forwarding setting is **Allow Forwarded Traffic**, and it is the piece most often missed when building hub relaying. By default a peering allows a network to receive traffic that originated in the peered network, but it does not allow that network to receive traffic the peer merely forwarded from somewhere else. When the hub appliance relays a packet from spoke one to spoke two, the packet arrives at spoke two's peering as forwarded traffic rather than traffic that originated in the hub, and unless spoke two's peering with the hub has **Allow Forwarded Traffic** enabled, spoke two drops it. Enable it on the spoke side of each hub peering that must accept relayed traffic:

```bash
# Allow the spoke to accept traffic the hub forwarded on behalf of another network
az network vnet peering update \
  --resource-group rg-spoke-two --vnet-name vnet-spoke-two \
  --name spoke-two-to-hub --set allowForwardedTraffic=true
```

The user-defined route that steers spoke-to-spoke traffic to the hub appliance is the routing half of the same pattern, and the series article on [how route tables and user-defined routes override the system routes a peering installs](/2023/12/11/azure-route-tables-udr-explained/) walks through building it correctly, including the common error of pointing the next hop at the appliance's network rather than its specific private address. The topology choice between a direct spoke mesh and a hub-relayed design is itself a decision worth making deliberately, and the comparison of [hub-and-spoke against Virtual WAN for connecting many spokes](/2024/06/17/hub-spoke-vs-virtual-wan/) lays out when the managed transit of Virtual WAN earns its cost over a hand-built hub, because Virtual WAN exists precisely to provide the transitive routing that raw peering withholds.

The deepest point to carry away from the non-transitive rule is that it is a feature, not a defect. Non-transitive peering means a spoke cannot reach another spoke, or the rest of the network, by accident. Reachability is granted only by an explicit relationship or an explicit route, so the blast radius of a compromised spoke is bounded by what you deliberately connected it to. An engineer who internalizes this stops fighting the rule and starts designing with it, treating every path between networks as a decision to be made rather than a default to be assumed.

## Cause four: gateway transit is missing, and on-premises routes never reach the spoke

The fourth mechanism appears when a spoke that peers cleanly with a hub still cannot reach an on-premises network that the hub connects to over a VPN or ExpressRoute gateway. The hub has the gateway, the hub knows the on-premises routes, the spoke peers with the hub, and yet the spoke has no path to the on-premises ranges. The reason is that learning the gateway's routes across a peering is not automatic; it requires a paired setting that is off by default, and the spoke simply never received the routes the hub's gateway holds.

### What does gateway transit require for on-premises routes?

Gateway transit requires a paired setting: **Allow Gateway Transit** enabled on the hub side of the peering, and **Use Remote Gateways** enabled on the spoke side. Only when both are set does the spoke learn the on-premises routes that the hub's VPN or ExpressRoute gateway advertises. Set one without the other and the routes never propagate.

This is the same matched-pair discipline that governs the link itself, applied to gateway sharing. The hub must offer transit, and the spoke must opt in to using the hub's gateway. The hub-side setting, **Allow Gateway Transit**, tells the hub's peering that it may advertise its gateway and the routes behind it to the peered spoke. The spoke-side setting, **Use Remote Gateways**, tells the spoke to use the hub's gateway for the ranges it learns and not to expect a gateway of its own. Confirm the current state of both settings before changing anything:

```bash
# Check Allow Gateway Transit on the hub's peering toward the spoke
az network vnet peering show \
  --resource-group rg-hub --vnet-name vnet-hub \
  --name hub-to-spoke \
  --query allowGatewayTransit -o tsv

# Check Use Remote Gateways on the spoke's peering toward the hub
az network vnet peering show \
  --resource-group rg-spoke --vnet-name vnet-spoke \
  --name spoke-to-hub \
  --query useRemoteGateways -o tsv
```

If the hub returns `false` for `allowGatewayTransit`, the hub is not advertising its gateway and no spoke can learn the on-premises routes through it. If the spoke returns `false` for `useRemoteGateways`, the spoke is not asking to use the hub's gateway even if the hub offers it. Either gap breaks the propagation, and the fix is to set both:

```bash
# Enable gateway transit on the hub side
az network vnet peering update \
  --resource-group rg-hub --vnet-name vnet-hub \
  --name hub-to-spoke --set allowGatewayTransit=true

# Enable remote gateway use on the spoke side
az network vnet peering update \
  --resource-group rg-spoke --vnet-name vnet-spoke \
  --name spoke-to-hub --set useRemoteGateways=true
```

After both are set, the spoke's effective routes should include the on-premises ranges with a next hop that points through the hub's gateway. Confirm it on a spoke machine, because the goal is reachability, not merely a configured flag:

```bash
# Confirm the on-premises ranges now appear in the spoke's effective routes
az network nic show-effective-route-table \
  --resource-group rg-spoke --name vm-spoke-nic \
  --output table
```

Several constraints around gateway transit catch engineers who set the flags and still see nothing. The first is ordering and existence: the hub must actually have a functioning gateway before transit means anything. Enabling **Use Remote Gateways** on a spoke whose hub has no gateway, or whose gateway is still provisioning, fails or yields no routes, because there is no gateway to use. Provision and confirm the hub gateway first, then enable transit. The second constraint is that a spoke configured to use the hub's remote gateways must not have a gateway of its own; the two are mutually exclusive, since a network either uses its own gateway or borrows the hub's, not both. The third is that transit shares the hub's gateway but does not make the spoke transitively reachable from the on-premises side without the on-premises routing also learning the spoke's ranges, which depends on how the gateway advertises routes. The flags propagate the hub's gateway to the spoke; making the return path work end to end is a routing exercise that includes the on-premises device.

A frequent misdiagnosis here is to blame the gateway, the VPN tunnel, or ExpressRoute when the spoke cannot reach on-premises, and to spend time debugging the tunnel that is in fact perfectly healthy and serving the hub. The tell is that the hub itself reaches on-premises fine while the spoke does not. When the hub has connectivity and the spoke does not, the gateway is not the problem; the transit settings between the hub and that spoke are. Reading the two flags and the spoke's effective routes localizes it in seconds and saves an hour of tunnel debugging that was never warranted.

The matched-pair theme recurs because it is the same idea in a new place. A peering is a pair of objects; gateway transit is a pair of flags. In both cases one side offering without the other side accepting yields nothing, and in both cases the failure looks like brokenness but is really an incomplete agreement. The reader who has internalized the model from the [VNet deep dive on how networks, gateways, and peerings compose](/2022/02/28/azure-virtual-network-vnet-deep-dive/) recognizes gateway transit as the same pattern rather than a new and separate mystery.

## Cause five: the peering is healthy, but a security rule or a custom route drops the packet

The fifth mechanism is the one that survives every check you have run so far and still fails. Both sides read `Connected`, the effective routes show the peer range with a `VNetPeering` next hop, gateway transit is irrelevant because the two networks are directly peered, and yet the application still times out. At this point the peering is doing exactly what it should, and the packet is being dropped by a separate control that sits between the two machines: a network security group that denies the flow, or a user-defined route that steers the traffic somewhere other than the peer.

### Why does traffic fail even when the peering is Connected?

Because a peering only grants a route between the networks; it does not override the security rules and custom routes that govern the traffic once it arrives. A network security group on the destination subnet or interface can still deny the flow, and a user-defined route can still send the packet to an appliance or a black hole instead of the peer.

The link establishes that traffic may travel between the two address spaces and installs the system route to carry it. It says nothing about which ports are allowed, which sources are permitted, or whether a custom route overrides the system route for a more specific prefix. Those decisions belong to the security and routing layers, which operate independently of the peering and are applied after the peering has agreed to carry the packet. A link that is up is necessary for cross-network traffic, but it is not sufficient, and conflating the two is the error that keeps engineers staring at a healthy peering while a security rule three layers down does the dropping.

The connectivity probe from earlier is the fastest way to separate a security drop from a routing drop. Run it from the source machine to the destination address and port, and read what it blames:

```bash
# Determine whether a rule or a route is dropping the cross-peering traffic
az network watcher test-connectivity \
  --resource-group rg-workload \
  --source-resource vm-a \
  --dest-address 10.2.0.4 --dest-port 443
```

When the probe reports that a security rule blocked the traffic and names the rule, the cause is a network security group, and the fix is to adjust that one rule rather than to touch the peering. A network security group can attach to a subnet, to a network interface, or to both, and when both are present, both must allow the flow for it to pass. The single most common cross-peering security drop is the default deny that applies when no explicit allow exists: the destination subnet allows traffic from its own network and from the load balancer, denies everything else inbound, and the peered network's range was never added as an allowed source. The fix is a specific inbound allow rule for the source range and port, not a blanket opening. Reading the effective security rules on the destination interface shows the exact rule that decided the flow, turning the fix into a lookup rather than a guess:

```bash
# Read the effective security rules on the destination NIC to find the blocker
az network nic list-effective-nsg \
  --resource-group rg-workload --name vm-b-nic \
  --output table
```

This is precisely the diagnosis the series develops for security-group drops in general, and rather than restate it here the article on [how to find exactly which NSG rule is blocking a flow and fix that rule](/2022/11/21/fix-nsg-blocking-traffic/) covers the priority ordering, the subnet-plus-interface stacking, and the effective-rules lookup in full. The relationship between the two articles is the relationship between the two layers: the peering grants the path, and the security group polices what travels on it, so a post-peering block is almost always a security-group question rather than a peering one.

When the probe instead reports that a route, not a rule, is sending the traffic elsewhere, the cause is a user-defined route. The classic case is a route table on the source subnet with a `0.0.0.0/0` entry pointing all traffic at a firewall or a network virtual appliance for inspection. That default route is more general than the peer's range, so for the peer's prefix the system `VNetPeering` route still wins by longest-prefix match, but a custom route that is equally or more specific than the peer's range will override the system peering route and pull the traffic off the direct path. If someone added a route for the peer's exact range pointing at an appliance that is down or misconfigured, the peering is healthy and the traffic still dies at the appliance. Inspect the effective routes and look for any custom entry that covers the destination more specifically than the system peering route:

```bash
# Find a custom route that overrides the peering route for the destination
az network nic show-effective-route-table \
  --resource-group rg-workload --name vm-a-nic \
  --output table
```

The fix depends on intent. If the override route is wrong, remove it or correct its next hop so the system route carries the traffic. If the override is deliberate, sending cross-network traffic through an appliance for inspection, then the appliance is part of the path and the real problem is at the appliance, not the peering, and the routing layer treatment in [route tables and user-defined routes and how they interact with peering routes](/2023/12/11/azure-route-tables-udr-explained/) explains how to reason about which route wins and why.

There is one more downstream block worth naming because it is specific to hub topologies and easily confused with the others. When traffic is meant to flow from one spoke to another through an appliance in the hub, the hub must be permitted to forward traffic it did not originate, which is the **Allow Forwarded Traffic** setting discussed under the non-transitive rule. A spoke peering that lacks this setting drops relayed traffic even though the peering is `Connected` and the routes point at the hub, because the arriving packet is forwarded rather than originated and the default peering posture rejects forwarded traffic. The confirming signal is that direct hub-to-spoke traffic works while spoke-through-hub-to-spoke traffic fails, and the fix is to enable **Allow Forwarded Traffic** on the receiving spoke's hub peering as shown earlier. This sits at the boundary between the link layer and the routing layer, which is exactly why it is so often misattributed to one when it belongs to the other.

The discipline that ties this cause to the others is to read the platform's own verdict before forming a theory. The connection troubleshoot probe names the layer that dropped the packet, the effective security rules name the deciding rule, and the effective routes name the deciding route. With those three reads in hand, a post-peering failure is never a mystery; it is a security rule, a custom route, or a forwarding setting, each with a named confirming signal and a fix that touches the actual cause.

## Reproducing a Disconnected state so you can recognize it instantly

The fastest way to stop misreading peering failures is to build one on purpose and watch it behave. Reproducing a Disconnected state takes three steps and a few minutes, and seeing the state transition firsthand fixes the mental model far more durably than reading about it. Create two networks with non-overlapping ranges, peer them on both sides so they reach `Connected`, then delete one half and watch the surviving half flip to **Disconnected**.

```bash
# Two non-overlapping networks
az network vnet create -g rg-lab -n vnet-a --address-prefix 10.10.0.0/16 --subnet-name s1 --subnet-prefix 10.10.1.0/24
az network vnet create -g rg-lab -n vnet-b --address-prefix 10.20.0.0/16 --subnet-name s1 --subnet-prefix 10.20.1.0/24

# Peer both sides; both reach Connected
az network vnet peering create -g rg-lab --vnet-name vnet-a -n a-to-b --remote-vnet vnet-b --allow-vnet-access
az network vnet peering create -g rg-lab --vnet-name vnet-b -n b-to-a --remote-vnet vnet-a --allow-vnet-access

# Confirm Connected on both
az network vnet peering show -g rg-lab --vnet-name vnet-a -n a-to-b --query peeringState -o tsv
az network vnet peering show -g rg-lab --vnet-name vnet-b -n b-to-a --query peeringState -o tsv

# Delete one half and re-read the survivor: it flips to Disconnected
az network vnet peering delete -g rg-lab --vnet-name vnet-b -n b-to-a
az network vnet peering show -g rg-lab --vnet-name vnet-a -n a-to-b --query peeringState -o tsv
```

The survivor now reads `Disconnected`, and the lesson is concrete: nothing about A changed, A's object is intact, and A is broken only in the sense that its partner is gone. Recreating A would do nothing; the correct repair is to recreate B's half. Run this once and the **Disconnected** label stops suggesting a snapped connection and starts meaning exactly what it is, a half-built or orphaned relationship. The place to run this repro safely, alongside a tested library of peering, routing, and gateway commands you can adapt, is the [hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), where you can peer two networks, break the link deliberately, and read every state transition without touching a production environment. To turn the reading into diagnostic reflex, [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) that present a failed peering and ask you to localize the cause from the state, the routes, and a probe, which is the exact skill this article teaches.

## Making peering repeatable so the one-sided failure cannot happen

Most one-sided peerings are an artifact of building them by hand, one portal blade at a time, where the operator creates the first half and never gets to the second. The durable prevention is to stop building peerings by hand and to define both halves together as code, so the matched pair is created atomically or not at all. A small Bicep module that takes the two networks and emits both peering objects removes the entire class of omitted-half failures, because there is no moment between the two creations for an interruption to leave the relationship incomplete.

```bicep
// Both halves of a peering, defined together so the pair is atomic
param vnetAName string
param vnetBName string
param vnetBId string
param vnetAId string

resource aToB 'Microsoft.Network/virtualNetworks/virtualNetworkPeerings@2022-07-01' = {
  name: '${vnetAName}/a-to-b'
  properties: {
    remoteVirtualNetwork: { id: vnetBId }
    allowVirtualNetworkAccess: true
    allowForwardedTraffic: false
    allowGatewayTransit: false
    useRemoteGateways: false
  }
}

resource bToA 'Microsoft.Network/virtualNetworks/virtualNetworkPeerings@2022-07-01' = {
  name: '${vnetBName}/b-to-a'
  properties: {
    remoteVirtualNetwork: { id: vnetAId }
    allowVirtualNetworkAccess: true
    allowForwardedTraffic: false
    allowGatewayTransit: false
    useRemoteGateways: false
  }
}
```

Defining the pair as code does three things beyond preventing the omitted half. It documents the intent, so the four settings that govern transit and forwarding are visible and reviewed rather than left at portal defaults that surprise people later. It makes the relationship auditable, so drift between the declared peering and the deployed one is detectable. And it makes the topology reproducible across environments, so the development networks peer the same way the production networks do and a peering that works in one place is not a special case that breaks in another. The transit and forwarding flags belong in this declaration too, because a hub-and-spoke design that depends on **Allow Gateway Transit** and **Use Remote Gateways** should not leave those settings to be toggled by hand on each spoke, where they are forgotten exactly as often as the second half of a peering is.

The verification step that proves the code worked is the same state read used throughout this article, run as a post-deployment check: confirm both halves read `Connected`, confirm the effective routes on a representative interface include the peer's range, and for a transit relationship confirm the on-premises ranges appear on the spoke. Bake those checks into the pipeline that deploys the networks and a regression that breaks peering is caught at deploy time rather than discovered weeks later by a developer whose traffic mysteriously stopped.

## Failures that look like a peering problem but are not

Several failures present as broken peering and originate elsewhere, and recognizing them prevents hours spent debugging a healthy relationship. The most common is the security-group drop already covered under cause five: both sides `Connected`, routes present, and a network security group denying the flow on arrival. The tell is that the connectivity probe blames a security rule, and the fix lives in the [diagnosis of which NSG rule is blocking the traffic](/2022/11/21/fix-nsg-blocking-traffic/), not in the link blade.

The second is a name-resolution failure mistaken for a connectivity failure. The peering carries traffic by address, and if the client resolves the destination's name to an address that the peering does not route, or fails to resolve it at all, the symptom is a timeout that looks like a dead peering. The give-away is that connecting to the destination by its private address succeeds while connecting by name fails, which points at DNS rather than the peering. Peered networks do not automatically share Azure-provided name resolution across the link, so a name that resolves inside one network may not resolve from the other unless a custom DNS arrangement spans both. When connectivity by address works and by name does not, stop looking at the peering and look at how each network resolves names.

The third is a gateway or tunnel problem misattributed to peering, the inverse of cause four. When a spoke cannot reach on-premises, the suspicion falls on the peering or the gateway transit settings, but if the hub itself also cannot reach on-premises, the gateway or the tunnel is down and the peering is irrelevant. Test from the hub first: if the hub reaches on-premises and the spoke does not, it is a transit-settings problem between the hub and that spoke; if the hub also fails, it is a gateway or tunnel problem that no peering change will fix.

The fourth is an application-level failure wearing a network costume. A service listening on the wrong interface, a host firewall inside the guest operating system denying the port, or an application that binds only to localhost will all refuse a connection that the network delivered correctly. The connectivity probe is decisive here: if it reports the path as reachable and the packet as delivered, the network has done its job and the failure is above it, inside the machine. Engineers lose real time treating an in-guest firewall rule as a peering fault, and the probe ends that detour by confirming the packet arrived.

The common thread across these four is that the peering is healthy and the failure lives in a neighboring layer, security, name resolution, the gateway, or the application. The way to avoid the detour is the discipline this article has pressed throughout: read the state, the routes, and the probe before forming a theory, and let the platform tell you which layer dropped the packet rather than assuming the layer you happen to be looking at.

## A worked hub-and-spoke example, from broken to flowing

Putting the causes together, here is the topology where the most peering questions actually arise, walked from a non-working state to a flowing one. The layout is a hub network holding a VPN gateway to on-premises and a firewall appliance for inspection, plus two spoke networks that must reach on-premises, reach the internet through the firewall, and reach each other. This single design exercises the matched-pair rule, the non-transitive rule, gateway transit, forwarding, and routing all at once, which is why so many engineers first meet every cause described above inside it.

Begin with the address plan, because the plan is what makes or breaks everything downstream. Give the hub a range, give each spoke a distinct non-overlapping range, and reserve room so future spokes do not collide. Suppose the hub is `10.0.0.0/16`, the first spoke is `10.1.0.0/16`, and the second spoke is `10.2.0.0/16`. No two ranges intersect, so every peering this design needs can be created without the overlap rejection, and a third spoke at `10.3.0.0/16` will slot in later without forcing a readdressing project. The single most consequential decision in the whole topology was made here, before any peering existed, and a careless default range copied across the spokes would have made the design impossible to assemble without re-IPing.

Create the spoke-to-hub peerings as matched pairs, both halves each, and confirm both reach `Connected`. At this point each spoke can reach the hub and the hub can reach each spoke, because each relationship is a direct, two-object pair. What no spoke can yet do is reach the other spoke or on-premises, and understanding why each of those fails is the heart of the design. The spoke-to-spoke path fails because peering is non-transitive: the hub's peering with the first spoke says nothing about the second, so a packet from spoke one to spoke two reaches the hub and stops. The spoke-to-on-premises path fails because gateway transit is off by default: the spoke has not learned the routes the hub's gateway holds. Two different causes, both presenting as a timeout, both invisible until you read the routes.

Fix the on-premises path first, since it is the cleaner of the two. Enable Allow Gateway Transit on each hub-to-spoke peering and Use Remote Gateways on each spoke-to-hub peering, the matched pair of flags that lets the spokes borrow the hub's gateway. The hub must already have a working gateway for this to mean anything, so provision and confirm the gateway before toggling the flags. After the flags are set, read a spoke machine's effective routes and confirm the on-premises ranges now appear with a next hop through the hub's gateway. If they do not, recheck that both flags are set on the correct sides and that the gateway itself is functioning, testing from the hub to be sure the gateway connection is healthy independent of any spoke.

Now the spoke-to-spoke path, which requires routing and forwarding rather than another peering, because the design goal is to inspect east-west traffic at the hub firewall rather than to let spokes talk directly. Place a user-defined route in each spoke that sends the other spoke's range to the firewall's private address as the next hop, so spoke one's traffic for `10.2.0.0/16` goes to the firewall and spoke two's traffic for `10.1.0.0/16` does the same in reverse. A route alone is not enough, because the relayed packet arrives at the destination spoke as forwarded traffic rather than traffic that originated in the hub, and the default peering posture rejects forwarded traffic. Enable Allow Forwarded Traffic on each spoke-to-hub peering so the destination spoke accepts the packet the firewall relayed. The firewall itself must also be configured to permit and route the east-west flow, since the spokes are merely steering traffic to it; the device decides whether to pass it.

```bash
# Route spoke-one traffic for spoke-two through the hub firewall
az network route-table create -g rg-spoke-one -n rt-spoke-one
az network route-table route create \
  -g rg-spoke-one --route-table-name rt-spoke-one -n to-spoke-two \
  --address-prefix 10.2.0.0/16 \
  --next-hop-type VirtualAppliance --next-hop-ip-address 10.0.1.4
az network vnet subnet update \
  -g rg-spoke-one --vnet-name vnet-spoke-one -n workload \
  --route-table rt-spoke-one

# Let the destination spoke accept the forwarded packet
az network vnet peering update \
  -g rg-spoke-two --vnet-name vnet-spoke-two \
  -n spoke-two-to-hub --set allowForwardedTraffic=true
```

With the address plan clean, the spoke-to-hub peerings Connected on both sides, gateway transit enabled as a matched pair of flags, the spoke-to-spoke routes pointing at the firewall, and forwarding allowed on the receiving peerings, every required path now flows. The exercise is worth doing once end to end because it shows that no single setting builds the topology; each cause described in isolation above is a piece of the same assembly, and a failure anywhere reads as a timeout that only the state, the routes, and a probe can tell apart. An engineer who has built this once stops treating hub-and-spoke as a collection of mysterious toggles and starts seeing it as the matched-pair and non-transitive rules expressed across several networks.

### Should two spokes peer directly or relay through the hub?

Relay through the hub when you need to inspect or police east-west traffic centrally, or when the number of spokes makes a full mesh of direct peerings unmanageable. Peer directly when the two spokes exchange high-volume or latency-sensitive traffic and you do not need to inspect it, since a direct peering avoids the extra hop and the firewall's throughput ceiling.

The deciding factor is whether the traffic must be inspected and how many spokes there are. A direct spoke-to-spoke peering routes at backbone speed with no intermediate device, which is ideal for heavy or latency-sensitive flows, but it bypasses any central inspection and adds a peering for every pair, so a large set of spokes becomes a sprawling mesh. Relaying through a hub appliance keeps the peering count linear and gives one place to inspect and log east-west traffic, at the cost of an extra hop and a device whose throughput becomes the ceiling for inter-spoke traffic. Most enterprise designs relay through the hub for the inspection and the manageability, and add a direct peering only for the specific spoke pair whose traffic volume or latency budget cannot tolerate the hub hop. That selective approach, hub relay by default with direct peering as a deliberate exception, captures the benefit of both without committing wholesale to either.

## Diagnosing global, cross-subscription, and cross-tenant peering

Peering is not confined to two networks in one region and one subscription, and the variants introduce a few failure modes worth naming because they are easy to misattribute to the basic peering mechanics. Global peering joins networks in different Azure regions, cross-subscription peering joins networks owned by different subscriptions, and cross-tenant peering joins networks in different directories. The core rules are unchanged in every case, a peering is still a matched pair and still non-transitive, but the way the relationship is referenced and authorized differs, and that is where the new failures hide.

### Does peering work across regions and subscriptions?

Yes. Peering works across regions as global peering, across subscriptions, and even across tenants with appropriate permissions. The matched-pair and non-transitive rules are identical in every case. What changes is referencing and authorization: across subscriptions you must reference the remote network by its full resource ID, and across tenants both sides need rights to create their half of the relationship.

Global peering, joining networks in two regions, behaves like local peering for the engineer's purposes: the relationship is a matched pair, both halves must read Connected, and the routes appear the same way. The traffic crosses Microsoft's inter-region backbone rather than staying within a region, so the latency reflects the distance between the regions, but there is no separate switch to enable and no different state model. The most common global-peering confusion is not a failure at all but a performance expectation: engineers sometimes assume global peering is slow or capped in a way local peering is not, then misread normal inter-region latency as a fault. Confirm reachability with a probe and judge latency against the realistic distance between the regions rather than against same-region numbers.

Cross-subscription peering adds the referencing and permission wrinkles described under the one-sided failures. Because a bare network name is ambiguous outside the local subscription, the remote network must be referenced by its full resource ID when creating the peering, and the operator must hold write permission on both networks, which the Network Contributor role on each scope provides. The signature cross-subscription failure is a relationship that is one-sided because the operator had rights in one subscription and not the other, so the first half succeeded and the second failed with an authorization error. The fix is to grant the role on both scopes and reference each remote network by its resource ID, then confirm both halves reach Connected. Reading the state on both sides remains the first diagnostic step; the only addition is checking the activity log of the side that failed for an authorization error that explains the missing half.

Cross-tenant peering, joining networks in different directories, layers an additional authorization step because the two networks belong to different identity boundaries. Each side must grant the other the rights to create its half of the relationship, typically by assigning a role to a guest identity or a service principal from the other tenant on the relevant network scope, and then each side creates its own half referencing the remote network by resource ID. The failure mode is the same one-sided relationship, now caused by a missing cross-tenant role assignment rather than a missing role within one tenant. The diagnosis is unchanged: read the state on both sides, find which half is missing, and trace the missing half to the permission that was never granted across the tenant boundary. The matched-pair model holds throughout; only the authorization paperwork grows.

What does not change across any of these variants is the diagnostic spine. The state on both sides localizes a structural failure, the effective routes confirm whether the peer range is carried, and a probe names any downstream block. Global, cross-subscription, and cross-tenant peering add referencing and authorization requirements at creation time, and those requirements produce one-sided relationships when unmet, but they do not create a new category of failure to learn. An engineer who can diagnose a local peering can diagnose every variant by adding two questions: is the remote network referenced correctly for its scope, and does each side have the rights to build its half. With those two answered, the familiar state, route, and probe reads finish the job.

## The verdict: a peering is a matched pair that never forwards for a third

The fix for almost every VNet peering failure follows from two facts and a habit. The two facts are that a peering is a matched pair of objects, one on each network, both of which must exist and agree, and that a peering carries traffic only between the two networks it directly joins and never relays for a third. The habit is to read the peering state on both sides, the effective routes on the originating interface, and a targeted connectivity probe before changing anything. Those two facts explain the Disconnected state and the spoke-to-spoke failure, the two most misread symptoms, and the habit localizes every remaining case to security, routing, transit, or forwarding with a named confirming signal.

The reflex to delete and recreate a peering is wrong far more often than it is right, because the usual cause is a missing or mismatched half that recreation does not address, and the rare case where recreation is correct, a genuinely orphaned object whose partner was destroyed, is identifiable from the state read in seconds. The reflex to open a broad allow rule when traffic fails after peering is equally wrong, because the peering was never the gate; a specific security rule was, and loosening the network to fix a rule trades a connectivity problem for an exposure. Reason from how peering actually behaves, confirm the cause with the platform's own signals, and change the one setting that is wrong. That is the whole method, and it turns the most misread failure in Azure networking into one of the most mechanical to fix.

## Frequently Asked Questions

### Q: Why does my VNet peering show a Disconnected state?

A Disconnected state means the object on this network lost its partner. The matching peering on the other network was deleted, or the network it pointed to was removed, so the local half still exists and still points outward but has nothing to agree with. The local object is intact; the relationship is simply orphaned. Confirm it by reading `peeringState` on both networks: the Disconnected side has a peering object while the other side has none, or has one that no longer targets this network. The fix is not to recreate the side that exists. Delete the orphaned half and recreate the relationship cleanly on both networks so each references the other, because a Disconnected object cannot return to Connected in place once its partner is gone.

### Q: Does peering have to be configured on both VNets?

Yes. A peering is two linked objects, one belonging to each network, and the relationship is live only when both exist and reference each other. Creating the link on one network and not the other leaves that side in an Initiated state, waiting for a matching half that never arrives. This is the single most common peering failure, and it happens most often when peerings are built by hand in the portal one at a time, with the operator creating the first half and never completing the second. The cure is to read the state on both sides whenever a peering looks wrong, and to define both halves together as code so the pair is created atomically and an omitted half becomes impossible. Two halves that point at each other reach Connected within seconds.

### Q: Can overlapping address space break VNet peering?

It does more than break it; it prevents the peering from being created at all. Azure rejects the operation synchronously at submit time and returns an error naming the conflicting ranges, because two networks that share any address range cannot be routed between unambiguously. A packet bound for an address that exists on both networks has no single correct destination, so the platform refuses to establish the relationship rather than build an incoherent routing table. Even a partial overlap, where one range sits inside the other, is fatal; there is no partial peering that routes the non-overlapping portion. The fix is to remove the overlap by adding a non-overlapping range to one network and migrating the relevant workloads into it, by re-IPing one network entirely, or, when readdressing is impossible, by connecting through an intermediary that translates addresses.

### Q: Why can two spokes not talk through a peered hub?

Because Azure peering is non-transitive: a peering carries traffic only between the two networks it directly joins and never relays on behalf of a third. The hub's peering with the first spoke knows nothing about the second spoke, and the hub's peering with the second spoke knows nothing about the first, so neither peering authorizes the hub to forward traffic between them. A packet from one spoke reaches the hub and finds no route onward. Confirm it by reading the originating machine's effective routes: you will see a route for the hub's range and none for the far spoke's range. The fix is to peer the spokes directly, or to route spoke-to-spoke traffic through an appliance in the hub using user-defined routes plus the Allow Forwarded Traffic setting on the spoke peerings.

### Q: What does gateway transit require for on-premises routes?

It requires a paired setting, the same matched-pair discipline that governs link itself. The hub side of the peering must have Allow Gateway Transit enabled so the hub advertises its gateway and the routes behind it, and the spoke side must have Use Remote Gateways enabled so the spoke uses the hub's gateway rather than expecting its own. Only when both are set does the spoke learn the on-premises ranges the hub's VPN or ExpressRoute gateway holds. Setting one without the other propagates nothing. The hub must also have a functioning gateway before transit means anything, and a spoke using remote gateways must not have a gateway of its own, since the two are mutually exclusive. Confirm success by checking that the on-premises ranges appear in a spoke machine's effective routes, not merely that the flags are set.

### Q: Why does traffic fail even when both sides read Connected?

Because a peering grants a route between the networks but does not override the security and routing controls that govern the traffic once it arrives. A network security group on the destination subnet or interface can still deny the flow, and a user-defined route can still steer the packet to an appliance or a black hole instead of the peer. A Connected link is necessary for cross-network traffic but not sufficient. Run a connectivity probe from the source to the destination address and port: if it blames a security rule, fix that specific rule rather than the peering; if it blames a route, inspect the effective routes for a custom entry that overrides the system peering route. Reading the effective security rules and the effective routes names the exact control that dropped the packet, turning the fix into a targeted change.

### Q: How do I confirm a peering's state from the command line?

Query the peering object on each network and read its `peeringState` field. With the Azure CLI, run `az network vnet peering show` against each network's own peering, selecting `peeringState`, and compare the two results. Both must read `Connected`. A value of `Initiated` means that side has built its half and is waiting for a matching, correctly targeted half on the other network. The portal's Disconnected label corresponds to a peering that was Connected and lost its partner. Reading the state on both networks, not just the one that looks broken, is the single most useful diagnostic step, because the asymmetry between the two sides tells you immediately whether the cause is a missing half, a mismatched target, or a healthy peering whose problem lies downstream in routing or security.

### Q: I deleted and recreated the peering and it still fails. Why?

Recreation rebuilds the half that already existed and does nothing about the half that was missing or mistargeted, which is the actual cause in most one-sided failures. If you recreated A's peering but B still has no matching half, or B points at the wrong network, the relationship is still incomplete and still fails. Recreation is the correct move in exactly one situation: a genuinely orphaned object whose partner was destroyed, where the surviving half cannot return to Connected in place and must be removed and rebuilt on both sides. Outside that case, stop recreating and read the state on both networks. The fix is almost always to create or correct the specific half that is missing or mismatched, not to tear down and rebuild a half that was already right.

### Q: Does VNet peering have a bandwidth limit or extra latency?

Peering routes traffic over the same Microsoft backbone that carries traffic inside a single network, so it does not introduce an appliance, a tunnel, or a public hop, and the latency between peered networks is effectively the latency of the backbone itself. There is no peering bandwidth cap to provision in the way a gateway has a throughput tier; the data plane is the network fabric. This is why peering is the preferred way to connect networks in the same or different regions when a direct relationship is acceptable, and why a hub appliance, which does add a hop and a device to scale, is introduced only when transitive routing or traffic inspection is required. Always confirm current performance characteristics against the official documentation, since platform capabilities evolve.

### Q: Can I peer VNets in different regions or different subscriptions?

Yes to both. Peering works across regions and across subscriptions, and even across tenants with the right permissions. Cross-region peering, sometimes called global peering, joins networks in different Azure regions and routes over the backbone between them. Cross-subscription peering requires that the operator hold write permission on both networks, which the Network Contributor role grants, and that the remote network be referenced by its full resource ID rather than a bare name, because a name is ambiguous outside the local subscription. A frequent one-sided failure across subscriptions is exactly this: the first half succeeds where the operator has rights, and the second half fails for lack of permission on the other subscription, leaving the relationship incomplete. Grant the role on both scopes and reference each remote network by resource ID.

### Q: How do I check whether the peer's routes actually reached my machine?

Read the effective route table on the network interface of the machine that should send the traffic, using `az network nic show-effective-route-table`. When a link is Connected, Azure injects a system route for the peer network's address space with a next hop type of `VNetPeering`. If that range appears with that next hop type, routing across the peering is in place and the platform intends to deliver the packet. If the range is absent, the peering is not delivering routes and you should return to the state check on both sides. If the range is present but a more specific custom route overrides it, a user-defined route is pulling the traffic off the direct path, which is a routing problem rather than a peering one. The effective routes are the authoritative view of what the platform will actually do.

### Q: What is the difference between Allow Forwarded Traffic and Allow Gateway Transit?

They govern two different relay behaviors and are easy to confuse. Allow Forwarded Traffic lets a network accept traffic that the peered network forwarded on behalf of a third network, rather than only traffic that originated in the peer. It is what a spoke needs when an appliance in the hub relays spoke-to-spoke traffic, because the relayed packet arrives as forwarded rather than originated. Allow Gateway Transit, with its partner Use Remote Gateways, lets a spoke learn and use the hub's VPN or ExpressRoute gateway and the on-premises routes behind it. One concerns forwarding arbitrary traffic through a network; the other concerns sharing a gateway's routes. A hub-and-spoke design that relays both east-west spoke traffic and on-premises traffic typically needs both, set on the correct sides of the correct peerings.

### Q: Why can my spoke reach the hub but not on-premises networks?

Because reaching the hub only requires the spoke-to-hub peering, while reaching on-premises additionally requires gateway transit so the spoke learns the routes the hub's gateway holds. If the spoke reaches the hub but not on-premises, the peering is fine and the transit settings are the gap: either Allow Gateway Transit is off on the hub side, or Use Remote Gateways is off on the spoke side, or both. Confirm by checking those two flags and by reading the spoke's effective routes for the on-premises ranges. If the on-premises ranges are absent, the routes never propagated. Importantly, test from the hub first; if the hub also cannot reach on-premises, the gateway or the tunnel is down and the problem is not transit at all but the gateway connection itself.

### Q: Does peering automatically let me resolve the peer network's hostnames?

No. Peering carries traffic by address; it does not share name resolution across the link. Each network resolves names according to its own DNS configuration, so a hostname that resolves inside one network may not resolve from the peered network unless a custom DNS arrangement spans both, such as a shared private DNS zone linked to both networks or custom DNS servers that both use. A common misdiagnosis is to see name-based connections fail across a peering and blame the peering, when connecting by private address succeeds. That pattern, address works and name does not, points squarely at DNS rather than at peering. Resolve it by linking a private DNS zone to both networks or by pointing both at DNS that can answer for the names in question, not by changing the peering.

### Q: How do I peer many spokes without a separate peering for every pair?

Use a hub-and-spoke topology where each spoke peers only to the hub, and route spoke-to-spoke traffic through an appliance in the hub rather than through a full mesh of direct peerings. A full mesh requires a peering for every pair of networks, which grows with the square of the number of spokes and becomes unmanageable. Hub-and-spoke keeps the number of peerings linear in the number of spokes, gives a single point to inspect east-west traffic, and is the default enterprise pattern for that reason. It requires user-defined routes that send each spoke's traffic for the others to the hub appliance, plus Allow Forwarded Traffic on the spoke peerings so the relayed packets are accepted. When the operational weight of a hand-built hub grows too large, a managed transit option exists to provide the transitive routing peering withholds.

### Q: My peering creation failed with an authorization error. What permission do I need?

Creating a peering requires write permission on both networks involved, because the operation touches each network's peering collection. The built-in Network Contributor role on each network's scope grants the necessary rights cleanly. When an operator holds rights on one network but not the other, the first half of the peering is created and the second fails with an authorization error, leaving a one-sided relationship that looks broken but is really a permissions gap. The confirming signal is an authorization failure in the activity log at the moment the second half was attempted, alongside a peering object that exists on one network and not the other. Grant the operator the appropriate role on the second network's scope, then create the missing half so both sides reference each other and reach Connected.

### Q: Can I change a peering's settings after it is created, or must I recreate it?

You can update most peering settings in place without recreating the relationship. The Allow Virtual Network Access, Allow Forwarded Traffic, Allow Gateway Transit, and Use Remote Gateways flags are all updatable on an existing peering with `az network vnet peering update` or the equivalent portal toggle, and the change takes effect without breaking the link. What you cannot change in place is the remote network a peering targets; retargeting means deleting the peering and creating a new one pointing at the correct network. This is why the omitted-half and wrong-target failures are repaired by creating or correcting the specific half rather than by editing a target, and why genuinely orphaned objects must be removed and rebuilt. For everything short of changing the peer itself, an in-place update is the correct and least disruptive fix.

### Q: How can I prevent one-sided peering failures from happening at all?

Stop building peerings by hand and define both halves together as infrastructure code, so the matched pair is created atomically or not at all and there is no window for an interrupted operator to leave the relationship incomplete. A small Bicep or Terraform module that takes the two networks and emits both peering objects removes the entire class of omitted-half failures, documents the transit and forwarding settings so they are reviewed rather than defaulted, and makes the topology reproducible across environments. Pair the code with a post-deployment check that reads the state on both sides and confirms the effective routes carry the peer's range, so a regression is caught at deploy time. Building peerings declaratively converts the most common peering failure from a recurring incident into a structural impossibility.

### Q: Does a Connected peering guarantee my application traffic will flow?

No. A Connected state guarantees that the relationship is live and that the system routes between the networks are installed, but it says nothing about whether a network security group allows the specific flow, whether a user-defined route overrides the system peering route, whether the destination host's own firewall permits the port, or whether the application is even listening on the right interface. Connected is necessary but not sufficient. Treat it as one confirmed layer in a stack: the peering grants the path, security groups police what travels on it, routes decide where it goes, and the host and application decide whether to accept it. When traffic fails on a Connected peering, a connectivity probe names the layer that dropped the packet, and the fix belongs to that layer rather than to the peering.

### Q: What is the fastest way to localize any peering failure?

Read three signals in order before changing anything. First, the peering state on both networks, which splits the problem into a structural failure (a missing or mismatched half) or a healthy peering with a downstream issue. Second, the effective routes on the originating interface, which confirm whether the peer's range is routed with a VNetPeering next hop or absent or overridden. Third, a connectivity probe from source to destination, which names the first hop that drops the packet and attributes it to a rule, a route, or a missing path. These three reads distinguish causes that produce identical timeouts at the application, and they convert an ambiguous symptom into a specific named cause with a matching fix. Forming a theory before reading them is what turns a five-minute fix into a wasted afternoon.
