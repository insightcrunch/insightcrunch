---
layout: post
title: "Service Endpoints vs Private Endpoints"
page_title: "Service Endpoints vs Private Endpoints in Azure: Private IP, DNS, On-Premises Reach, and Cost Explained"
date: 2023-11-06
categories: ["Technology"]
tags: ["Azure", "Private Endpoint", "Service Endpoint", "Networking", "Private Link", "Cloud Computing"]
excerpt: "Service endpoints versus private endpoints in Azure differ on private IP, DNS, on-premises reach, and cost. Learn which one to choose and why it matters."
image: "/assets/images/blog/blog-88.webp"
reading_time: 64
author: "jason-mckenzie"
last_updated: 2023-11-06
lang: en
---
Two features in Azure share a goal, securing traffic to a platform service so it no longer rides the open internet, and engineers conflate them constantly. The choice between a service endpoint and a private endpoint looks like a naming quirk until a storage account refuses a connection from an on-premises server, or a firewall rule that worked yesterday starts dropping requests after a subnet change. The confusion is understandable. Both keep traffic off the public path. Both attach to a virtual network. Both get described in the portal with overlapping language about securing access to a resource. Yet they solve different problems with different mechanics, and treating them as interchangeable is the single most common reason a connectivity design fails review or breaks in production.

This guide draws the line cleanly. By the end you will choose between the two by reasoning about four concrete questions, whether you need a stable private IP address, how name resolution has to behave, whether anything outside the virtual network has to reach the resource, and what you are willing to pay and operate. Those four questions decide every case. Get them straight and the rest follows.

![Service endpoints versus private endpoints in Azure comparison of private IP, DNS, and on-premises reach - Insight Crunch](/assets/images/blog/blog-88.webp)

## What each feature actually is

The fastest way to stop conflating the two is to hold a precise mental model of each. They are not two flavors of the same thing. They are two different answers to the question of how a workload inside a virtual network should reach a platform resource such as a storage account, a SQL database, or a Key Vault without exposing that traffic to the public internet.

A service endpoint is a property you switch on at the subnet level. When you enable it for a given resource type, say `Microsoft.Storage`, the platform programs the subnet so that traffic bound for that resource type leaves through Azure's own backbone rather than across the public internet, and it stamps the request with the subnet's identity. The target resource, the storage account in this example, can then trust that subnet through its own firewall. Crucially, the resource keeps its public address. Nothing about its name or its IP changes. What changes is the path the packet takes and the identity the resource sees on the far side.

A private endpoint is a different animal entirely. It is a network interface placed inside your subnet, and that interface holds an address from your own private range. The platform resource is projected into your network behind that interface through the Private Link service. From the workload's point of view the resource now lives at a private address inside the network, reachable the way any internal host is reachable. The public address of the resource is no longer the path you use. You connect to the projected interface, and the platform stitches the connection through to the underlying resource.

Hold those two pictures side by side and the rest of this article is mostly consequences. One leaves the resource public and routes the trip privately while trusting a subnet. The other gives the resource a genuine presence inside your address space. That difference, public-but-trusted versus genuinely-internal, drives every behavior that follows.

### Is a service endpoint just a cheaper private endpoint?

No, and the framing is the trap. A service endpoint does not hand the resource a private address, so it cannot satisfy a requirement that depends on one. It is not a budget version of the same capability, but a separate mechanism, subnet trust plus backbone routing, that only overlaps on the goal of keeping traffic off the public internet.

The mechanism gap matters because requirements are usually written against the address, not against the routing. A security team that says "the database must not be reachable on a public IP" is describing the projection a private endpoint provides, and no amount of subnet trust will meet that wording. A team that says "traffic to storage must stay on the Azure backbone and only our subnet may reach the account" is describing exactly what a service endpoint delivers. The words in the requirement tell you which mechanism you are actually being asked for. Read them carefully before reaching for either.

## The named rule that decides almost every case

Here is the claim worth bookmarking, the private-IP-and-on-premises rule. If your requirement depends on a stable address from your own range, or anything outside the virtual network has to reach the resource over a private path, only a private endpoint qualifies. In every other situation, where subnet-level trust over the backbone is enough, a service endpoint is the simpler and cheaper choice and you should prefer it.

That single rule resolves the vast majority of designs without further thought. The two triggers, a needed private address and outside reach, are the decisive cuts. Everything else, name resolution, cost, operational burden, follows from which side of those cuts you land on. The remaining sections turn the rule into a table you can apply at the whiteboard and then walk through each consequence so you can defend the choice when someone challenges it.

### The InsightCrunch endpoint decision table

The findable artifact for this article maps each common need to the feature that satisfies it and names the deciding signal. Tape it to the wall next to the architecture diagram.

| Need | Service endpoint | Private endpoint | Deciding signal |
| --- | --- | --- | --- |
| A stable private address for the resource | No, the resource keeps its public address | Yes, a network interface holds an address from your range | The requirement names an IP or a private address rather than a path |
| Reach from on-premises over the private connection | No, the trust is tied to the subnet identity | Yes, the projected interface is reachable across peering and gateways | A client living outside the virtual network must connect privately |
| Simple subnet-level trust for in-network workloads | Yes, switch it on per subnet and trust it at the resource firewall | Yes, but heavier than needed for the in-network case | All consumers already sit inside the virtual network |
| Change to name resolution | No, the public name resolves as before | Yes, a private DNS zone must override the name to the private address | Whether you can tolerate or must avoid touching DNS |
| Lowest cost and least to operate | Yes, no per-resource hourly or processing charge | No, each interface carries an hourly and a data-processing charge | Budget pressure with no private-address or outside-reach requirement |
| Scope of protection | Per subnet, all enabled resources of that type | Per resource instance, one interface per protected resource | Whether you are gating a subnet or isolating one specific resource |

Read the table top to bottom for any given design. The moment you hit a row where only one column says yes and that row matches a hard requirement, the decision is made. The first two rows, private address and outside reach, are the ones that most often force the answer, which is why the named rule leads with them.

## Why name resolution is the difference people miss

Of all the behaviors that separate the two features, DNS is the one that surprises engineers most, because it is invisible until it breaks. A service endpoint changes nothing about how a name resolves. The storage account answers on the same public name and the same public address it always did. The packet simply takes the backbone path and arrives stamped with the subnet identity, which the resource firewall then trusts. You never touch a DNS zone, and that simplicity is a real advantage when you only need subnet trust.

A private endpoint forces the opposite. The resource is now reachable at a private address, but its public name still resolves, by default, to its public address. If a client looks up the storage account's hostname and gets the public address, it will try the public path, which the firewall may now be blocking, and the connection fails in a way that looks like a permission problem but is actually a resolution problem. The fix is a private DNS zone linked to the virtual network that overrides the resource's hostname so it answers with the private address instead. Get that zone wrong and the private endpoint sits there, healthy and provisioned, while every client still aims at the public address and fails.

This is why so many private endpoint problems are name resolution problems in disguise. The interface is fine. The link is fine. The lookup is wrong. We cover that failure pattern in depth in our walkthrough of [why a private endpoint stops resolving and how to repair the zone](/2022/11/28/fix-private-endpoint-dns/), and the underlying zone mechanics live in our piece on [the Private Link model that projects the resource into your network](/2023/09/11/azure-private-link-deep-dive/).

### Why does my private endpoint resolve to a public address?

Because creating the interface does not automatically rewrite the resource's name. The hostname still points at the public address until a private DNS zone, linked to the virtual network and holding the override record, answers the lookup with the private address instead. Without that zone, clients keep aiming at the public path the firewall blocks.

The mechanics deserve a careful walk. When you provision a private endpoint, the platform allocates the interface and an address in your subnet, and it knows the mapping between the resource's hostname and that address. What it does not do, unless you wire it up, is make every client in the network learn that mapping. The Azure-provided resolver inside the virtual network will return the private answer only if a linked private DNS zone holds the record. Integrate the zone at creation time, through the portal option or the automation that links the zone and registers the record, and resolution just works. Skip it, hand-build a conditional forwarder that points the wrong way, or forget to link the zone to the consuming network, and you get the classic symptom, a provisioned endpoint and a client that cannot reach it.

For hybrid setups the resolution story gets one layer deeper. An on-premises client cannot use the Azure-provided resolver directly, so it needs a forwarding path, usually a DNS forwarder inside Azure that the on-premises servers conditionally forward to, so that the lookup eventually reaches the resolver that knows the private record. This is the part teams underbuild, and it is the reason on-premises reach is treated as its own decision rather than a footnote.

## On-premises reach, the cut that ends the argument

If a single fact settles more designs than any other, it is this one. A service endpoint trusts a subnet inside a virtual network. It has no meaning for a machine that lives in your datacenter, because that machine is not in the subnet and cannot be granted the subnet identity that the resource firewall trusts. So the moment a requirement says an on-premises client must reach the resource over the private connection, the service endpoint is eliminated and a private endpoint is the only option that works.

A private endpoint reaches from on-premises because it is just an address inside your network, and your network already extends to the datacenter through a gateway or a direct circuit. A request from an on-premises host crosses that link, lands in the virtual network, and finds the private interface exactly as an in-cloud workload would. The interface does not care where the client sits, only that the route to its private address exists. Combine the route with the forwarding path for name resolution described above and the hybrid client connects privately end to end.

This asymmetry is not a limitation anyone chose arbitrarily. It falls directly out of the two mechanisms. Subnet trust is a property of a subnet, and a datacenter is not a subnet. A private address is reachable from anywhere with a route to it, and a hybrid network supplies that route. So the rule writes itself, hybrid private access means a private endpoint, full stop.

### Can a service endpoint ever work from my datacenter?

No. The trust a service endpoint establishes is bound to the identity of a virtual network subnet, and an on-premises machine has no such identity. It cannot present the subnet stamp the resource firewall checks for, so traffic from the datacenter is treated as ordinary public traffic and gated accordingly.

People try to work around this in ways that quietly fail. Routing on-premises traffic through a virtual network does not lend that traffic the subnet identity, because the stamp is applied to traffic originating in the enabled subnet, not to traffic merely passing through. Adding the datacenter's public ranges to the resource firewall as allowed addresses can let connections through, but that is the public path with an allow-list, not the private backbone path the requirement asked for, and it widens the surface rather than narrowing it. If the requirement is genuinely private reach from on-premises, the honest answer is a private endpoint and the forwarding to resolve its name. The networking context that makes this concrete, how routes and gateways carry that traffic, is laid out in our [foundations of Azure networking for engineers](/2023/08/28/azure-networking-fundamentals/).

## Cost and operational weight, the other side of the ledger

If on-premises reach and a private address are the reasons to choose a private endpoint, cost and simplicity are the reasons not to reach for one reflexively. A service endpoint carries no per-resource hourly charge and no data-processing charge. You toggle it on the subnet and you are done. There is nothing to provision per resource, nothing that bills by the hour, and no interface to manage. For a workload that lives entirely inside the virtual network and only needs the backbone path plus subnet trust, that is the lighter, cheaper, and more maintainable answer by a clear margin.

A private endpoint bills differently. Each interface carries an hourly charge for existing and a charge for the data it processes, and those add up when you protect many resources or move large volumes. Beyond the bill there is operational weight, a private DNS zone to maintain, records to keep aligned as resources change, forwarding to run for hybrid clients, and one interface per protected resource rather than one switch per subnet. None of this is prohibitive, and for a resource that does require private projection it is the cost of doing the thing correctly. But it is real, and it is the reason the decision table puts cost and simplicity in their own row. Paying for projection you do not need is a quiet, recurring waste.

### When is a service endpoint the smarter choice even though it is older?

When every consumer already sits inside the virtual network, you do not need a private address, and nothing on-premises has to reach the resource. In that case subnet trust over the backbone meets the requirement with no per-resource cost, no DNS zone to maintain, and nothing to provision per resource, which is the simpler and cheaper design.

The temptation in modern designs is to default to private endpoints everywhere because they feel more thorough, and to treat service endpoints as legacy. That instinct overspends and over-operates. A great many real requirements are satisfied entirely by subnet trust, and forcing a private endpoint onto them buys a private address nobody needed, a DNS zone somebody now has to keep correct, and a recurring charge for both. The discipline is to apply the named rule honestly, reach for the private endpoint only when the address or the outside-reach trigger fires, and let the service endpoint do its job everywhere else. If you want to model both behaviors side by side and watch how each resolves and routes, you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), which lets you stand up each configuration against the same storage account and compare what the firewall and the resolver actually see.

## Six recurring patterns and the factor that decides each

Designs rarely arrive as clean textbook questions. They arrive as half-stated requirements, inherited configurations, and symptoms that point sideways. The patterns below are the ones engineers report again and again, each framed as a problem with the one factor that settles it. Learn to spot the factor and the choice stops being a debate.

### A storage account needs a private address

The pattern is a security or compliance line that reads something like, the account must not be reachable on a public address from anywhere. A service endpoint cannot meet this, because the account keeps its public address by design even when the backbone path and subnet trust are in place. The deciding factor is the word address. The requirement is written against the resource having a presence in your range, and only the projected interface of a private endpoint supplies that. This is the cleanest case for a private endpoint, and it is also where teams most often try to substitute subnet trust and then fail an audit, because the auditor checks the resolved address, not the routing.

### An on-premises client must reach the resource privately

A reporting server in the datacenter has to query a database without the traffic touching the public internet. The subnet-trust mechanism is meaningless here, because the reporting server has no subnet identity to present. The deciding factor is the location of the consumer. A consumer outside the virtual network needs an address it can route to across the hybrid link, which is precisely the private interface. Pair it with a forwarding path so the server can resolve the resource's name to that private address, and the query travels privately from the datacenter all the way through.

### An in-network workload needs nothing more than subnet trust

A set of application servers, all inside the virtual network, read and write to a storage account, and the only requirement is that the account refuse everyone except those servers and keep the traffic off the public path. There is no private-address requirement and nothing external in play. The deciding factor is that every consumer already lives in the subnet. A service endpoint satisfies this exactly, with no interface to provision, no zone to maintain, and no recurring per-resource charge. Reaching for a private endpoint here is the overspend the named rule is designed to prevent.

### A change to name resolution is unacceptable, or mandatory

Two opposite versions of the same factor. In one, an application hardcodes or caches the resource's public name and the team cannot tolerate the resolution override a private endpoint requires, which argues for a service endpoint that leaves resolution untouched. In the other, policy demands that the resource's name resolve only to a private address everywhere, which is exactly what the private DNS zone behind a private endpoint enforces. The deciding factor is whether your constraint is on leaving DNS alone or on locking DNS down. Name which one applies and the feature follows.

### Cost pressure with no private-address requirement

A platform team is rationalizing spend and finds dozens of private endpoints fronting resources whose only real requirement was subnet trust. Each interface bills hourly and per processed gigabyte, and the DNS apparatus is overhead nobody is using for its intended purpose. The deciding factor is the absence of either trigger, no private address needed, nothing external reaching in. Converting those cases back to service endpoints removes a recurring charge and a maintenance burden without weakening anything the requirement actually asked for.

### Migrating from service endpoints to private endpoints

An older design used service endpoints throughout, and a new compliance mandate now requires private addresses and on-premises reach. The deciding factor is that the requirement changed, not that the original choice was wrong. Service endpoints were correct for the earlier requirement and private endpoints are correct for the new one. The migration is real work, covered next, but the framing matters, you are not fixing a mistake, you are responding to a requirement that crossed one of the two triggers. Practicing that migration against a sandbox before doing it for real is exactly the kind of scenario drill that ReportMedic builds into its troubleshooting practice, where you can rehearse the cutover and the resolution change without risking a production outage.

## How to migrate from service endpoints to private endpoints

When a requirement crosses a trigger and you have to move, the work is methodical rather than hard, but the order matters because the failure mode is a window where clients resolve the wrong address. The end-to-end setup is covered step by step in our guide to [standing up private endpoints from start to finish](/2023/05/01/configure-private-endpoints/); what follows is the migration reasoning that sits on top of it.

Start by provisioning the private endpoint and its DNS before you remove anything. Create the interface in the appropriate subnet, integrate the private DNS zone, link it to every virtual network whose clients consume the resource, and confirm the override record resolves to the private address from inside each of those networks. For hybrid consumers, stand up or confirm the forwarding path so the datacenter resolves the same private answer. At this stage both paths can coexist, the public path that the service endpoint trusted and the new private path, which lets you validate the private route under real traffic before you cut over.

```bash
# Create the private endpoint for a storage account's blob service
az network private-endpoint create \
  --name pe-storage-blob \
  --resource-group rg-network \
  --vnet-name vnet-prod \
  --subnet snet-endpoints \
  --private-connection-resource-id "/subscriptions/<sub>/resourceGroups/rg-data/providers/Microsoft.Storage/storageAccounts/myaccount" \
  --group-id blob \
  --connection-name conn-storage-blob

# Link a private DNS zone for blob storage and register the record
az network private-dns zone create \
  --resource-group rg-network \
  --name "privatelink.blob.core.windows.net"

az network private-dns link vnet create \
  --resource-group rg-network \
  --zone-name "privatelink.blob.core.windows.net" \
  --name link-vnet-prod \
  --virtual-network vnet-prod \
  --registration-enabled false

# Confirm the name now resolves to the private address from inside the network
nslookup myaccount.blob.core.windows.net
```

Only once the private path is proven do you tighten the resource firewall to drop the public path and remove the service endpoint trust from the subnet. Reversing that order, removing the service endpoint trust before the private route resolves, is what creates an outage, because clients briefly resolve a public address that the firewall has already started refusing. Sequence it as provision, link, verify, then cut, and the migration is uneventful. After cutover, watch the resource's connection metrics and the resolver answers for a full business cycle before you call it done, since cached public answers can linger on long-lived clients.

## How each feature interacts with the rest of the network

Neither feature lives alone. Each sits inside a larger network of routes, filters, peerings, and resolvers, and the interactions are where second-order surprises come from. Understanding them is the difference between a design that works on the first server and one that works across every consumer.

A service endpoint changes the path that traffic to the enabled resource type takes out of the subnet, steering it onto the backbone, and it changes the identity the resource sees. It does not change filtering inside the subnet, so a network security group still evaluates the traffic by its rules, and you can still scope outbound to the resource's service tag. Because the trust is per subnet and per resource type, enabling it affects every resource of that type that the subnet talks to, which is broad by design. That breadth is fine when you mean to trust the subnet for storage generally, and a trap when you only meant to trust one account, because subnet trust does not distinguish one account from another within the type. When you need that finer grain, the per-resource isolation of a private endpoint is the better fit.

A private endpoint introduces an interface into the subnet, and that interface participates in routing and resolution like any internal host. Across peered networks the interface is reachable as long as the route exists and the consuming network is linked to the private DNS zone, which is the step teams forget when they peer a new spoke and wonder why only the original network resolves the private name. The interface also interacts with network policies on its own subnet, which historically were disabled for endpoint subnets and now can be applied, so confirm whether your filtering actually evaluates traffic to the interface or passes it through. The broader routing and filtering picture, how a packet gets from client to interface and where it can be dropped, is the model we build in [the networking fundamentals walkthrough](/2023/08/28/azure-networking-fundamentals/), and it is worth holding in mind because most private endpoint connectivity tickets resolve to either a missing route, a missing zone link, or a filter nobody expected to be active.

### Does enabling a service endpoint affect other resources of the same type?

Yes. Subnet trust is granted per resource type, not per individual resource, so enabling the storage service endpoint on a subnet steers and stamps traffic to storage generally, and any storage account that trusts that subnet will accept it. If you need to isolate exactly one account, the per-resource scope of a private endpoint is the precise tool.

## Designing for production: putting the rule to work at scale

A single resource is easy. A platform with hundreds of resources across many teams is where the discipline pays off. The production posture is not "private endpoints everywhere" and it is not "service endpoints everywhere." It is the named rule applied consistently, with the two triggers driving every exception. Resources that must present a private address, or that on-premises clients reach privately, get private endpoints with a well-run DNS story. Everything else, the large set of in-network-only consumers with subnet-trust requirements, uses service endpoints and stays cheap and simple.

At scale the DNS apparatus for private endpoints becomes the thing that makes or breaks the design, so centralize it. A small number of private DNS zones, linked to every consuming network and to the hybrid forwarding path, beats a sprawl of per-team zones that drift out of alignment. Automate the zone link whenever a new spoke is peered, because the most common production failure is a freshly peered network that can route to the interface but was never linked to the zone, so it resolves the public address and fails. Treat the zone-and-link step as part of peering, not as an afterthought, and a whole class of tickets disappears.

For the service-endpoint side, the production discipline is narrower but still real. Keep the subnet trust scoped to the subnets that actually consume the resource type, document which subnets are trusted at each resource firewall, and remember that the trust is broad across the type, so a subnet trusted for storage is trusted for every account that lists it. When that breadth stops matching the requirement, that is your signal that the resource has crossed into private-endpoint territory and the rule says to move it.

Above all, write the decision down. For each protected resource, record which feature it uses and which trigger, if any, forced a private endpoint. That record turns future reviews from arguments into lookups, and it is what lets a platform team rationalize cost later by finding the private endpoints that no live requirement justifies.

## The counter-reading worth engaging

Two wrong instincts cause most of the bad designs in this space, and both deserve a direct answer rather than a dismissal. The first is assuming a service endpoint gives a private address or works from on-premises. It does neither, and the assumption usually surfaces as a failed audit or a datacenter client that cannot connect. The honest correction is that subnet trust and a private address are different things, and the requirement almost always wanted the address, so read the requirement against the mechanism and the gap becomes obvious before it becomes an incident.

The second instinct is the opposite overreach, using a private endpoint where subnet trust would have done, on the theory that more isolation is always better. It is not always better, because it is not free. Each unnecessary interface bills by the hour and by the gigabyte, and each one adds a record to a zone that someone has to keep correct as resources move. More isolation than the requirement asks for is not rigor, it is recurring waste plus maintenance surface. The corrective is the same rule from the other direction, if neither trigger fires, the service endpoint is the disciplined choice, and defaulting to a private endpoint anyway is a decision you should be able to justify against a real requirement rather than a feeling.

## How a service endpoint stamps and trusts traffic

To use either feature with confidence you have to know what the platform is doing underneath, because the abstractions hide exactly the detail that matters when something breaks. Take the subnet-trust mechanism first.

Enabling subnet trust for a resource type is a single property on the subnet. You list the resource types the subnet should reach over the backbone, and the platform adds optimized routes for those types so the traffic stays on Azure's own infrastructure instead of egressing to the public internet. At the same time, requests leaving that subnet for the enabled type carry the subnet's virtual network identity. The target resource sees that identity arrive and, if its own access rules list the subnet as trusted, admits the request. Two halves have to line up: the subnet has to be enabled for the type, and the resource has to trust the subnet. Miss either half and the request is treated like any other public caller.

The command to enable the subnet half is a property update on the subnet, and the command to add the trust half lives on the resource. For a storage account the pair looks like this:

```bash
# Half one: enable the optimized route and identity on the subnet
az network vnet subnet update \
  --resource-group rg-network \
  --vnet-name vnet-prod \
  --name snet-apps \
  --service-endpoints Microsoft.Storage

# Half two: tell the storage account to trust that subnet
az storage account network-rule add \
  --resource-group rg-data \
  --account-name myaccount \
  --vnet-name vnet-prod \
  --subnet snet-apps

# And switch the account's default action to deny so only trusted subnets pass
az storage account update \
  --resource-group rg-data \
  --name myaccount \
  --default-action Deny
```

That third command is the one people forget. Enabling the optimized route and adding the subnet to the trusted list does nothing visible if the account still defaults to allowing every caller, because the public path remains wide open alongside the backbone path. Switching the default action to deny is what turns the trusted-subnet list into an actual gate. The symptom of forgetting it is a design that looks locked down on the diagram but answers any caller in practice, which is the kind of gap a security review catches and a casual test does not.

The identity that arrives at the resource is worth dwelling on, because it explains the on-premises limitation cleanly. The stamp is a property of the originating subnet, generated by the platform as traffic leaves that subnet. It is not a credential the caller holds and can carry elsewhere. A machine that does not originate inside the enabled subnet has no way to produce the stamp, which is precisely why a datacenter host cannot benefit from the arrangement no matter how its traffic is routed. The trust is structural, tied to where the packet starts, not to who sent it.

### What exactly does the resource trust when I enable a service endpoint?

It trusts the virtual network subnet the traffic originates from, identified by a stamp the platform applies as the packet leaves that subnet. The resource does not trust a user, an application, or a credential. It trusts a location in the network, which is why only workloads running inside the enabled subnet benefit and outside callers do not.

## How Private Link projects a resource into your network

The projection mechanism is more involved, and the extra machinery is exactly what buys the private address and the outside reach. When you create the interface, you are not just dropping a network card into a subnet. You are establishing a connection between that interface and a specific resource through the Private Link service, and that connection has a lifecycle, an approval state, and a target sub-resource you have to name.

Start with the target. A single platform resource often exposes more than one logical function, and the interface attaches to one of them, identified by a group designation. A storage account, for instance, exposes blob, file, queue, table, and other functions separately, and an interface created for blob access does not cover file access. You pick the function you need when you create the interface, and a resource that needs several functions reached privately needs several interfaces, one per function. This is the detail that trips up first attempts: the interface comes up healthy, the blob path works, and the file path still resolves and routes to the public address because no interface was ever created for it.

Next comes approval. The connection between your interface and the target resource is not always automatic. When you own both sides, in the same directory, the connection is auto-approved and comes up ready. When the resource lives in another party's directory, as it does for a shared platform offering or a partner's service, the connection enters a pending state and the resource owner has to approve it before traffic flows. The connection therefore has a state you can query, and a stuck connection in a pending or rejected state is a distinct failure from a routing or resolution problem. You read it directly:

```bash
# Inspect the connection state of a private endpoint
az network private-endpoint show \
  --name pe-storage-blob \
  --resource-group rg-network \
  --query "privateLinkServiceConnections[].privateLinkServiceConnectionState"
```

A connection reading approved means the projection is live; pending means it is waiting on the resource owner; rejected means the owner declined and the interface, while provisioned, carries no traffic. Treating these three states as part of your diagnostic vocabulary saves hours, because a rejected connection looks identical from the client side to a routing problem, yet the fix is entirely different.

The cross-directory approval model is also what makes the projection safe to offer between organizations. A provider can publish a service and let consumers request a private projection into their own networks, approving each request explicitly, without ever exposing the service on a shared public surface. That capability has no analogue in subnet trust, which only ever applies within a single network boundary. The full mechanism, including how the provider side publishes the service and how the consumer side requests and consumes it, is the subject of our [deep dive on the Private Link model](/2023/09/11/azure-private-link-deep-dive/), and it is worth reading alongside this article when the projection crosses an organizational line.

### Why does my private endpoint work for blob but not file storage?

Because each interface attaches to one function of the resource, named by a group designation, and an interface created for the blob function does not cover the file function. The file path still resolves and routes to the public address until you create a second interface for it, with its own record in the matching private DNS zone.

## The DNS architecture behind a projected resource, in detail

Name resolution is where most projection designs succeed or fail, so it earns a full treatment. The core problem is a split between two answers to the same lookup. By default the resource's hostname resolves, on the public internet and inside any network without an override, to its public address. Once you project the resource, you want clients inside your network, and any hybrid clients, to receive the private address instead. Achieving that split cleanly is the whole job.

The platform solves it with a dedicated zone whose name follows a fixed pattern tied to the resource type. Blob storage uses one zone name, file storage another, SQL another, Key Vault another, and so on, each beginning with a reserved label that marks it as the projection zone for that service. When you create the interface and integrate it, the platform writes a record into that zone mapping the resource's hostname to the interface's address. The resource's public hostname is itself a pointer that, inside a network linked to the zone, redirects to the projection name the zone answers privately. The effect is that the same lookup returns the public address outside your network and the private address inside it, which is the split you wanted.

Three steps have to be right for that split to hold, and each is a common point of failure. The zone must exist with the correct reserved name for the resource type, an easy thing to fumble because the names are specific and unforgiving. The zone must be linked to every network whose clients consume the resource, which is the step teams skip when they peer a new spoke and assume reachability implies resolution. And the record inside the zone must map the hostname to the current interface address, which can drift if interfaces are recreated without updating the record. Walk those three, zone, link, record, in order whenever a projected resource is unreachable, and you will localize the fault quickly. The detailed failure walkthrough lives in our piece on [repairing a private endpoint that will not resolve](/2022/11/28/fix-private-endpoint-dns/).

### How does the same hostname return two different addresses?

Inside a network linked to the projection zone, the resource's public hostname redirects through a pointer to a projection name that the zone answers with the interface's address. Outside that network, with no linked zone, the same hostname resolves the ordinary way to the public address. One name, two answers, decided by whether the asking network holds the override.

Hybrid resolution adds a layer that teams routinely underbuild, and it deserves its own attention because it is the most common reason a datacenter client fails against an otherwise healthy projection. An on-premises machine cannot query the in-cloud resolver directly, so it cannot learn the private record on its own. You bridge the gap with a forwarder. A resolver running inside the virtual network can answer with the private record because it sits where the projection zone is linked, and the on-premises name servers conditionally forward queries for the relevant zones to that in-cloud forwarder. The query then reaches a resolver that knows the private address, and the datacenter client connects privately. Build that forwarding chain deliberately, because without it the projection is perfect and the datacenter still resolves the public address and fails.

There is also a split-horizon trap to avoid. If the on-premises name servers hold their own records for the resource's domain, or a conditional forwarder points at the wrong target, the lookup can be answered locally with the public address before it ever reaches the in-cloud resolver. The discipline is to forward only the specific projection zones to the in-cloud resolver and to make sure no local record shadows them. The general routing and resolution context that makes this tractable is laid out in our [networking fundamentals walkthrough](/2023/08/28/azure-networking-fundamentals/), which is the backdrop for reasoning about where a lookup actually gets answered.

```bash
# Inspect the record the projection zone holds for the resource
az network private-dns record-set a list \
  --resource-group rg-network \
  --zone-name "privatelink.blob.core.windows.net" \
  --query "[].{name:name, ip:aRecords[].ipv4Address}"

# From a client, confirm which address the hostname resolves to
nslookup myaccount.blob.core.windows.net
# Inside a linked network this should return the interface's private address;
# from an unlinked machine it returns the public address.
```

## Configuring subnet trust end to end, with verification

A working example for the subnet-trust side closes the loop and gives you something to test against. The order is enable the route and identity on the subnet, add the subnet to the resource's trusted list, switch the resource's default action to deny, then verify from inside and outside the subnet.

```bash
# Enable the subnet for two resource types at once
az network vnet subnet update \
  --resource-group rg-network \
  --vnet-name vnet-prod \
  --name snet-apps \
  --service-endpoints Microsoft.Storage Microsoft.KeyVault

# Trust the subnet at the storage account and deny everyone else
az storage account network-rule add \
  --resource-group rg-data --account-name myaccount \
  --vnet-name vnet-prod --subnet snet-apps
az storage account update \
  --resource-group rg-data --name myaccount --default-action Deny

# Verify: from a VM inside snet-apps the account answers;
# from a host outside the subnet the same request is refused.
az storage blob list \
  --account-name myaccount --container-name data --auth-mode login
```

Verification matters more here than in many configurations because the failure is silent in one direction. A test from inside the trusted subnet succeeding tells you the trust works, but it does not tell you the gate is closed. You confirm the gate by testing from outside the subnet and seeing the request refused. Only when the inside test passes and the outside test fails is the design proven. Skipping the outside test is how a default action left on allow ships to production looking correct. If you want a sandbox where you can stand up both halves and watch the resource firewall accept the trusted subnet and refuse everything else in real time, you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) and exercise the full sequence against a disposable account.

## Diagnosing a connectivity failure with either feature

When a connection to a protected resource fails, the symptom is almost always the same generic refusal, and the art is in localizing the actual cause quickly rather than guessing. The two features fail in different places, so the first useful question is which feature is in play, and the second is which layer the fault sits at. A short, ordered checklist beats trial and error.

For the subnet-trust case the layers are few. Confirm the subnet is enabled for the resource type, confirm the resource lists the subnet as trusted, and confirm the resource's default action is set to deny rather than allow, because a default of allow makes the trust list irrelevant and a default of deny with a missing subnet entry refuses the workload. Then confirm the request actually originates inside the enabled subnet, since traffic that egresses through a different path, a forced tunnel to an appliance or an on-premises hop, loses the subnet identity and arrives as a public caller. Most subnet-trust failures resolve to one of those four checks.

For the projection case the layers are more numerous, which is why a fixed order helps. Walk them as connection state, resolution, route, then filtering.

```bash
# 1) Connection state: is the projection approved, pending, or rejected?
az network private-endpoint show -g rg-network -n pe-storage-blob \
  --query "privateLinkServiceConnections[].privateLinkServiceConnectionState.status"

# 2) Resolution: from the failing client, what address does the name return?
nslookup myaccount.blob.core.windows.net

# 3) Route: does the client's subnet have an effective route to the interface address?
az network nic show-effective-route-table \
  --resource-group rg-network --name <client-nic-name> --output table

# 4) Filtering: is a network security group on the path dropping the flow?
az network nic list-effective-nsg \
  --resource-group rg-network --name <client-nic-name>
```

Read the four answers in sequence and the fault localizes itself. A connection that is not approved is a control-plane problem the resource owner has to clear, and no client-side change will help. A name that resolves to the public address is a zone problem, the linked zone or its record, and the connection itself is fine. A missing route is a peering or routing problem rather than a resolution problem, common when a new spoke can resolve the name but has no path to the address. And a network security group that drops the flow is filtering that someone applied to the interface subnet, which used to be impossible and now is not. Each answer points at a different owner and a different fix, which is why guessing wastes so much time and the ordered walk does not.

### How do I tell a resolution failure from a routing failure?

Resolve the name from the failing client. If it returns the public address, the fault is name resolution, the linked zone or its record, and the interface is healthy. If it returns the private address but the connection still fails, the fault is downstream, a missing route or a filter dropping the flow, checked with the effective route table.

## Per-service specifics that change the details

The general model holds across services, but the particulars differ enough that a few service notes save real time. Storage exposes its functions separately, so a single account can need several interfaces, one each for blob, file, queue, table, or other functions in use, with a matching record in each function's projection zone. Designing a storage projection means enumerating which functions the workload uses and provisioning an interface per function, not a single interface for the account.

A database service introduces a connection-policy wrinkle. Some database connections negotiate a redirect to a backend address after an initial handshake, and that redirect has to land on a path the projection covers, so the connection policy and the projection have to agree or the handshake succeeds while the data connection fails. The fix is to align the connection policy with the projected path, which is a setting on the database service rather than on the interface, and a failure here looks like an intermittent or stage-specific timeout rather than a clean refusal, which is what makes it puzzling until you know to look.

A secrets vault is simpler in shape but strict about resolution, because clients fetch from it on a hostname that must resolve to the interface address inside the network, and a vault left resolving to its public address while its firewall denies public callers is the textbook resolution failure. The lesson repeats across services: provisioning the interface is the easy half, and aligning resolution is where the work concentrates. A globally distributed database adds the further point that a projection is regional in nature, so a multi-region deployment may need an interface and a record in each region rather than assuming one projection serves the whole footprint.

The throughline across all of these is that the interface is necessary but not sufficient. For every service, the questions that decide whether it actually works are which functions or regions need a projection, whether the resolution override is present in every consuming network, and whether any service-specific policy, a connection policy or a public-access toggle, agrees with the private path. Hold those three questions and the per-service quirks become checklist items rather than surprises.

## Modeling the cost difference concretely

Abstract talk of hourly charges does not help a budget conversation, so model it. Subnet trust costs nothing per resource and nothing per gigabyte; it is a property toggle. Projection costs an hourly amount for each interface to exist plus an amount for the data each interface processes. The shape of the difference, not the exact figures which you should confirm against current pricing, is what drives the decision.

Picture a platform protecting fifty resources, each of which only needs in-network trust. With subnet trust the marginal cost of protection is zero; you enable the relevant types on the consuming subnets and trust them at each resource. With projection you would create fifty interfaces, each billing hourly to exist and per gigabyte for the traffic it carries, plus the zones and records to maintain. Across fifty resources the hourly charges alone become a standing line item, and the data charges scale with throughput, so a high-volume workload multiplies the gap. None of that buys anything if the requirement was only in-network trust, which is the precise waste the named rule exists to prevent.

The calculus inverts the moment a trigger fires. For a resource that has to present a private address or be reached from the datacenter, the interface is not overhead, it is the only mechanism that meets the requirement, and its cost is the price of the capability. The discipline is therefore not to minimize interfaces blindly but to provision exactly the interfaces the triggers demand and to meet every other requirement with the free mechanism. A platform that follows the rule ends up with a small set of interfaces around the resources that need them and subnet trust everywhere else, which is both the cheapest posture and the easiest to reason about.

## Security posture: blast radius and exfiltration

Security reviews often drive the choice, so it helps to compare the two on the terms a reviewer uses, blast radius and exfiltration, rather than on a vague sense that one is stronger. Both keep traffic off the public internet, so neither leaves data exposed in transit on a shared path. The differences are about scope and about what a compromised workload can reach.

Subnet trust grants at the granularity of a subnet and a resource type, which means every workload in a trusted subnet can reach every resource of that type that trusts the subnet. The blast radius of a compromised workload in that subnet is therefore the set of resources that trust the subnet, which can be broad if the subnet is trusted widely. To narrow exfiltration risk, the platform offers a policy layer on the subnet-trust path that restricts which specific resource instances a trusted subnet may reach, so that a compromised workload cannot ship data to an arbitrary account of the same type. Using that policy layer is the way to keep subnet trust from becoming a wide-open lane to every resource of a type.

Projection grants at the granularity of a single resource instance reached through a specific interface, so the blast radius is naturally narrower; a workload reaches exactly the resources it has an interface for and no others. That tighter default is part of why security teams favor projection for sensitive resources. It is not magic, a compromised workload with an interface to a resource can still use it, but the scope of what any one workload can reach privately is bounded by the interfaces present rather than by a subnet-wide trust. When a review frames the requirement as limiting what a compromised in-network workload could reach, that framing is usually pointing at projection for the sensitive resources and at the policy layer for the rest. The hardening context, how these choices sit alongside firewalls and routing, builds on the same [networking foundations](/2023/08/28/azure-networking-fundamentals/) the rest of this series leans on.

## A complete worked design

Tie it together with a realistic shape. Picture a three-tier application running in a virtual network, with web and application tiers in their own subnets, a managed database, a storage account for blobs, and a secrets vault, plus a reporting server back in the corporate datacenter that has to query the database. Apply the rule resource by resource.

The database has to be reachable privately from the datacenter reporting server, so the outside-reach trigger fires and the database gets a projection, with a record in the database projection zone, the zone linked to the application virtual network, and a forwarding path so the datacenter resolves the private address. The connection policy on the database is aligned with the projected path so the handshake and the data connection both land privately. That is one interface, justified by a trigger, with its DNS and forwarding built deliberately.

The storage account is consumed only by the application tier inside the network, with no private-address mandate and nothing external reaching it, so neither trigger fires and subnet trust is the right answer. The application subnet is enabled for the storage type, the account trusts that subnet, the account's default action is set to deny, and a policy on the trust path restricts the subnet to this one account so a compromised application workload cannot reach an arbitrary account. No interface, no zone, no recurring per-resource charge.

The secrets vault is read by the application tier and also by a deployment process that runs inside the network, again with no outside reach and no private-address mandate, so it too uses subnet trust, enabled on the consuming subnets and denied by default elsewhere. The result is a design with exactly one interface, around the one resource a trigger forced, and free subnet trust around the rest, with a policy layer narrowing exfiltration where the trust is broad. It is cheaper than projecting everything, simpler to operate because only one zone and one forwarding path exist, and defensible in review because every choice traces to a trigger or its absence. Practicing this kind of end-to-end design against a sandbox, including rehearsing the datacenter resolution path, is the sort of scenario ReportMedic turns into a repeatable drill, so the first time you build it for real it is not the first time you have built it.

## How subnet trust interacts with routing, forced tunneling, and appliances

A subtlety that bites larger networks is the interaction between subnet trust and the rest of the routing table. The optimized route the platform adds for an enabled resource type steers matching traffic onto the backbone and stamps it with the originating subnet identity. That works cleanly when the traffic is allowed to take that route. It stops working the moment a user-defined route or a forced tunnel redirects the traffic somewhere else first, because the stamp is tied to leaving the enabled subnet on the optimized path, and traffic pulled toward an appliance or pushed down a tunnel to the datacenter no longer leaves that way.

The practical failure looks like this. A security team installs a network virtual appliance and adds a route that sends all egress, including traffic to storage, through the appliance for inspection. The workload still resolves the storage account's public name, the request now travels to the appliance instead of onto the optimized backbone path, and it arrives at the resource as an ordinary public caller without the subnet stamp. The resource firewall, set to deny by default and trusting only the subnet stamp it is no longer receiving, refuses the request. The team sees a connection that worked yesterday fail today with no change to the storage configuration, and the cause is a routing change two layers away.

The lesson is that subnet trust assumes the optimized route is the route the traffic actually takes. Where a design forces egress through an appliance or a tunnel, you either have to exempt the resource type's traffic from that redirection so it keeps the optimized path, or you have to recognize that the redirection has effectively removed the subnet stamp and choose a mechanism that does not depend on it. Projection sidesteps the whole issue, because reaching an interface address is ordinary internal routing that an appliance route does not strip of meaning, which is one more reason projection tends to win in heavily inspected networks even when the in-network requirement alone would have allowed subnet trust.

### Why did my storage connection break after a routing change?

Because subnet trust depends on traffic leaving the enabled subnet on the optimized path that stamps it with the subnet identity. A user-defined route or forced tunnel that redirects that traffic through an appliance or to the datacenter strips the stamp, so the request reaches the resource as a public caller and the deny-by-default firewall refuses it.

## What neither feature does, and the myths worth dropping

Several persistent myths cause bad designs, and naming them directly is the fastest way to clear them. Neither feature encrypts traffic that was not already encrypted; both keep traffic off the public internet, but the encryption of the payload is a separate concern handled by the protocol the application uses. Treating either as a substitute for transport encryption is a mistake a review will catch.

Neither feature authenticates the caller. Subnet trust admits anything originating in the trusted subnet regardless of identity, and a projection carries whatever the application presents. Both are network controls, not identity controls, so the resource's own access model, its keys, tokens, or role assignments, still has to do the authentication work. A design that leans on the network control and leaves the resource open to any caller that reaches it has confused two layers that have to both be present.

Subnet trust specifically does not give a private address, does not work from outside the network, and does not isolate one resource instance from another of the same type without the extra policy layer. Projection specifically does not remove the need to manage resolution, does not automatically extend to every function or region of a resource, and does not authenticate anything. Listing what each does not do is as useful as listing what each does, because most incidents trace to an assumption that one of these features quietly handles something it never touched. Hold the boundaries clearly and the surprises stop.

There is also a myth of permanence worth dropping, the idea that the choice, once made, is fixed. It is not. Requirements move, and the right answer moves with them. A resource correctly served by subnet trust today can cross a trigger tomorrow and warrant a projection, and a resource over-projected in a cautious early design can be returned to subnet trust once a review confirms no trigger applies. Treating the decision as revisable rather than carved in stone is what lets a platform stay both correct and economical over time.

## The decision rule, branch by branch

The named rule compresses into a short branch you can run in your head, and writing it out branch by branch removes the last of the ambiguity. Begin with the address question, because it is the one most often hidden in compliance language.

If the requirement depends on the resource presenting an address from your own range, or on the resource not being reachable on a public address, choose a projection. There is no second branch here; subnet trust cannot meet an address requirement, so the moment that requirement is real the decision is made and the remaining branches only confirm how to build it.

If the address question is no, ask the reach question. If any consumer that has to reach the resource over a private path lives outside the virtual network, in the datacenter or another network not covered by subnet trust, choose a projection, because subnet trust has no meaning for a caller without a subnet identity. If every consumer that needs the private path lives inside the network, continue.

With both trigger questions answered no, choose subnet trust, and then ask only the operational questions that shape how you build it rather than which feature to use. Does any single account need isolating from others of its type? Add the policy layer to the subnet-trust path. Is the traffic redirected through an appliance or tunnel? Exempt the resource type's traffic from the redirection or reconsider whether the redirection has effectively pushed you toward a projection after all. Is name resolution required to stay untouched? Subnet trust already satisfies that, which is a point in its favor. None of these reopen the feature choice; they refine the build of the cheaper option you have already earned the right to use.

The branch is therefore short: address, then reach, then build. Two questions select the feature and the rest selects the configuration. Memorize the two questions and you will rarely need the table.

## Governing the choice across a platform

A single team can hold the rule in their heads, but a platform spanning many teams needs governance that makes the right choice the default and surfaces the wrong one automatically. Three mechanisms carry most of the weight: policy that audits and enforces, tagging that records intent, and automation that removes the error-prone manual steps.

Start with policy that audits public reachability. A platform can require that sensitive resource types deny public network access by default and flag any resource that leaves it open, which catches the case where someone provisioned a resource and never closed the public path. Pair that with a policy that audits whether a projected resource has its zone integration in place, so an interface created without its resolution override is surfaced rather than discovered later as a connectivity ticket. These audits do not decide the feature for a team, but they make the consequences of a half-finished design visible the day it ships rather than the day it breaks.

Tagging records the intent behind each choice so that future reviews are lookups rather than archaeology. A simple convention, tagging each protected resource with the feature it uses and, where a projection was chosen, the trigger that forced it, turns the question "why does this resource have an interface" into a one-line answer. Without that record, a later cost review cannot tell an interface that a trigger justified from one that a cautious default created, and so it cannot safely reclaim the waste. The tag is cheap to apply at provisioning time and expensive to reconstruct afterward, so apply it as the resource is created.

Automation removes the steps people get wrong. The most valuable automation links the projection zone to every network that should resolve the private name, triggered whenever a new network is peered, because the single most common platform failure is a freshly peered spoke that can route to an interface but was never linked to the zone. Folding the zone link into the peering process, so that adding a spoke automatically links it to the relevant zones, eliminates that whole class of incident. Automating the interface-and-record creation together likewise prevents the drift where an interface is recreated and its record is not, which leaves clients resolving a stale address. Treat resolution as something the platform maintains, not something each team hand-builds, and the projection side of the house becomes reliable at scale.

## Expressing both as infrastructure code

Both features belong in your templates rather than in portal clicks, both because reproducibility matters and because the difference between them is clearer in code than in prose. Subnet trust is a property on the subnet plus a rule on the resource; a projection is a separate resource with its own zone and record. Seeing them side by side in a template makes the contrast concrete.

```bicep
// Subnet trust: a property on the subnet and a rule on the account
resource subnet 'Microsoft.Network/virtualNetworks/subnets@2023-05-01' = {
  name: 'vnet-prod/snet-apps'
  properties: {
    addressPrefix: '10.10.1.0/24'
    serviceEndpoints: [
      { service: 'Microsoft.Storage' }
    ]
  }
}

resource account 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'myaccount'
  location: 'eastus'
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    networkAcls: {
      defaultAction: 'Deny'
      virtualNetworkRules: [
        { id: subnet.id, action: 'Allow' }
      ]
    }
  }
}
```

The projection is a heavier shape, and the template makes the extra machinery visible at a glance, which is itself an argument for not reaching for it without a trigger.

```bicep
// Projection: an interface, a zone, a link, and a record group
resource pe 'Microsoft.Network/privateEndpoints@2023-05-01' = {
  name: 'pe-storage-blob'
  location: 'eastus'
  properties: {
    subnet: { id: endpointSubnetId }
    privateLinkServiceConnections: [
      {
        name: 'conn-storage-blob'
        properties: {
          privateLinkServiceId: account.id
          groupIds: [ 'blob' ]
        }
      }
    ]
  }
}

resource zone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.blob.core.windows.net'
  location: 'global'
}

resource zoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: zone
  name: 'link-vnet-prod'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: { id: vnetId }
  }
}
```

Notice that the subnet-trust template is two small additions to resources you already have, while the projection template introduces an interface, a zone, a link, and the record group that ties them together, with the hybrid forwarding path still to build outside the template. The line count is a fair proxy for the operational weight, which is why the named rule treats subnet trust as the default and projection as the choice you make deliberately when a trigger demands it. Building both shapes as code, testing them against a sandbox, and keeping them in version control is the discipline that keeps a large platform's network posture reviewable rather than mysterious.

## Revisiting the decision as requirements change

A correct decision has a shelf life, because the triggers are properties of requirements and requirements move. Build a habit of revisiting the choice on the events that tend to flip a trigger rather than on a calendar, because the calendar review finds nothing and the event review finds the real changes.

The events that warrant a look are specific. A new compliance mandate that forbids public reachability flips the address trigger and pulls affected resources toward a projection. A new consumer in the datacenter or a partner network flips the reach trigger for the resources that consumer touches. A consolidation that removes the last on-premises consumer or relaxes an address requirement can flip a trigger off and make a previously justified interface into reclaimable cost. A network redesign that introduces forced tunneling through an appliance can quietly break subnet trust and force a move to projection even though the underlying access requirement did not change. Each of these is a moment to re-run the two-question branch for the affected resources, not the whole estate.

When a trigger flips on, the migration is the provision-link-verify-then-cut sequence covered earlier, sequenced to avoid the resolution window that causes outages. When a trigger flips off, the move is the reverse and just as deliberate: stand up subnet trust, confirm the in-network consumers work over it, then remove the interface and retire its zone records, watching for any consumer you forgot was relying on the private address. Either direction is routine when sequenced carefully and an outage when rushed. The tag that recorded the original trigger is what makes these reviews fast, because it tells you in one line whether the resource still has a live reason to be where it is. Keep the tags current, run the branch on the events that matter, and the platform's posture stays both correct and economical as the requirements underneath it shift.

## Observability: knowing each one is working

A design you cannot observe is a design you cannot trust, and the two features expose their health through different signals. Knowing where to look turns a vague "is it working" into a precise answer and shortens every future incident.

For the subnet-trust case the clearest signal is the resource firewall's own view of what it admitted and refused. A request that arrives with the expected subnet identity and is admitted, contrasted with a request from outside that is refused, is the proof the gate is doing its job. Diagnostic logs on the resource record the access and the rule that governed it, so a log showing in-subnet access succeeding and out-of-subnet access denied is the confirmation the design is both open where it should be and closed where it must be. Flow logs on the subnet add the network-level view, showing the optimized path the traffic took, which is how you confirm the traffic actually rode the backbone rather than slipping out a redirected route that would have stripped its identity.

For the projection case the signals are spread across the interface, the resolution layer, and the resource. The interface reports its connection state, so a periodic check that every interface remains approved catches a connection that was later rejected or a resource that was recreated and lost its approval. The resolution layer is best watched from the clients themselves: a synthetic lookup from each consuming network that asserts the resource's name returns the private address catches a zone link that lapsed or a record that drifted before any user hits the failure. The resource's own diagnostic logs then confirm the traffic arriving over the private path. Watching all three, interface state, client-side resolution, and resource access, gives you the full picture, and a gap in any one localizes the fault before it becomes a ticket.

### What is the first thing to monitor for a projected resource?

Client-side resolution from every consuming network. A synthetic lookup that asserts the resource's name returns the interface's address, run from inside each network including the hybrid path, catches the most common failure, a lapsed zone link or a drifted record, before any user hits it. Interface connection state and resource access logs come next.

The deeper point is that observability should mirror the failure modes. Subnet trust fails at the gate or at the route, so you watch the firewall's verdicts and the path the traffic took. Projection fails at the connection state, the resolution, or the route, so you watch all three. Aligning the monitoring with the way each feature actually breaks means an alert fires on the thing that will go wrong rather than on a generic health check that stays green while the real problem hides one layer down.

## Edge cases and gotchas that catch experienced teams

Beyond the main decision, a handful of edge cases recur often enough to be worth naming, because they catch people who already understand the basics. Each is a place where the obvious assumption is slightly wrong.

The first is the multi-network consumer. A projection's resolution override has to exist in every network that consumes the resource, and the easy mistake is to integrate the zone with the network where the interface lives while forgetting a second network that also has clients. The interface is reachable from the second network by routing, but the second network resolves the public name and fails, which looks like an intermittent problem because it depends on which network the failing client sits in. The fix is to treat zone linking as per-consuming-network, not per-interface.

The second is the regional nature of a projection. An interface lives in a region, and a resource with a presence in several regions may need an interface and a record in each, rather than one interface serving the global footprint. Teams that deploy a globally distributed resource and project it once in the primary region are surprised when a client routed to a secondary region cannot reach it privately. Enumerate the regions a workload actually uses and provision per region.

The third is resource recreation. If an interface or the underlying resource is torn down and rebuilt, the address or the mapping can change, and a record left pointing at the old address silently breaks resolution. Automating the record alongside the interface, so they are created and destroyed together, prevents the drift. The fourth is the assumption that filtering does not apply to an interface. Network policies on an interface subnet, once impossible, can now be active, so a rule that drops the flow to the interface is a real and easily overlooked cause of a connection that resolves correctly and still fails.

The fifth is the silent default on the subnet-trust side. Adding a subnet to a resource's trusted list while leaving the default action on allow produces a design that looks restricted and admits everyone, and the only way to see the gap is to test from outside the trusted subnet. The sixth is the inspection appliance described earlier, where a route added for security strips the subnet identity and breaks trust with no change to the resource. None of these is exotic, and all of them share a shape: the obvious half of the configuration is right and a second, less obvious half is missing or has drifted. Keeping a checklist of these six turns each from a multi-hour mystery into a quick elimination.

## Field notes: three failures and what they taught

Concrete failures stick better than abstract rules, so here are three composite cases drawn from the patterns teams report, each with the lesson it leaves behind.

The first is the audit that failed on a resource everyone believed was locked down. The team had enabled subnet trust and added the subnet to the resource's trusted list, and every functional test passed because the in-network workloads connected fine. The auditor resolved the resource's name and saw a public address answering, then connected from outside and got in, because the default action was still allow. The lesson is that subnet trust is only a gate when the default action denies, and that functional tests from inside never reveal an open default. The verification that matters is the negative one, the test from outside that must fail.

The second is the new spoke that could not reach a database everyone else reached fine. The database had a healthy projection, the original network resolved the private address and connected, and a newly peered spoke could route to the interface but timed out. The cause was a zone never linked to the new spoke, so its clients resolved the public address and aimed at a path the firewall refused. The lesson is that routing reachability and name resolution are separate, and peering a network does not link it to the zone. Folding the zone link into the peering process retired the whole class of incident.

The third is the connection that broke after a security change with no change to the resource. A workload had reached storage over the backbone via subnet trust for months. A new inspection appliance and a route sending all egress through it arrived, and storage connections began failing. The traffic now reached the resource through the appliance as a public caller without the subnet identity, and the deny-by-default firewall refused it. The lesson is that subnet trust assumes the optimized path is the path taken, and a routing change two layers away can invalidate it. The team either had to exempt the resource type's traffic from the redirection or move to a projection that does not depend on the stamp. They chose the projection, because the inspected network made the dependency fragile, and the move also positioned them for a later datacenter consumer that would have forced it anyway.

Each story is the same lesson from a different angle: the feature works exactly as designed, and the failure lives in an assumption about the surrounding network or the resource's own defaults. Carry the assumptions explicitly, test the negative cases, and align resolution with routing, and the failures above never reach production.

## Where this choice sits in the broader connectivity toolbox

It helps to place this decision inside the larger set of tools, because engineers sometimes try to solve the wrong problem with it. Both mechanisms address one narrow question: how a workload inside a virtual network reaches a managed platform service privately. They are not general connectivity tools. They do not connect virtual networks to each other, they do not connect a network to the datacenter, and they do not filter traffic between workloads. Those jobs belong to peering, gateways, circuits, and the security controls that sit on the network, and conflating any of them with this choice leads to a design that reaches for the wrong instrument.

The relationship runs the other way: the broader connectivity has to already exist for a projection's outside reach to mean anything. An interface is reachable from the datacenter only because a gateway or circuit already carries the route, and reachable from a peered network only because the peering already exists and the zone is linked across it. The endpoint choice rides on top of the connectivity rather than replacing it. So the order of design is to establish the network shape first, the virtual networks, their peering, the hybrid links, and only then decide, resource by resource, whether each managed service is reached through subnet trust or a projection over that established fabric.

Seen this way, the two features are the last mile of private access to managed services, not the road itself. The road is the network you built with the rest of the toolbox. Keeping that separation clear prevents the common confusion of expecting an endpoint choice to solve a routing or peering gap it was never meant to touch, and it keeps the decision focused on the question it actually answers, which is how the last hop to a managed service should behave once the network underneath it is in place.

### Do these features connect networks or filter traffic between workloads?

No. Both address only how a workload inside a virtual network reaches a managed platform service privately. Connecting networks is the job of peering, gateways, and circuits, and filtering traffic between workloads is the job of security groups and firewalls. The endpoint choice rides on top of that connectivity rather than providing it.

## A reference you can hand to a teammate

When you onboard someone to a platform that uses both features, the fastest way to make them productive is a short reasoning script rather than a feature tour. Give them the two questions and the consequences, and they can make and defend the choice the same day.

The script is this. For any managed service a workload needs to reach privately, ask whether the requirement depends on a private address or on the resource being unreachable on a public address. If yes, the answer is a projection, and the work is an interface for each function and region in use, a resolution override in every consuming network, a forwarding path for any datacenter clients, and alignment of any service-specific connection policy with the private path. If no, ask whether anything that needs the private path lives outside the network. If yes, again a projection, for the same reasons and with the same work. If both are no, the answer is subnet trust, and the work is enabling the type on the consuming subnets, trusting those subnets at the resource, setting the default action to deny, and adding the policy layer if one account must be isolated from others of its type.

Pair that script with the three habits that keep the platform healthy. Test the negative case, the access that must fail, not only the access that must succeed, because the silent open default is invisible to positive tests. Treat resolution as per consuming network and fold the zone link into peering, because a routable interface with an unlinked zone is the most common failure. And tag each resource with its feature and, for a projection, the trigger that forced it, because that tag is what makes every later review a lookup instead of an investigation. A teammate who holds the two questions, the consequences of each answer, and those three habits will make choices that pass review and survive contact with production, which is the whole point of having a rule rather than a reflex.

The reason this compresses so cleanly is that the underlying distinction is genuinely simple once the conflation is broken. One mechanism trusts a location in the network and leaves the resource public; the other gives the resource a private presence and demands you manage its name. Every behavior, every cost, every failure mode, and every governance habit follows from that one difference. Teach the difference, hand over the two questions, and the rest is consequence.

## Why the confusion persists, and how to inoculate a team against it

It is worth understanding why these two features are conflated so reliably, because naming the cause helps a team avoid the trap rather than rediscovering it. The confusion comes from the surface. Both are configured near the same place in the portal, both are described with overlapping language about securing access to a managed service, and both produce the same headline outcome of keeping traffic off the public internet. A reader skimming the documentation comes away with the impression of two settings that do roughly the same thing, one perhaps newer or more thorough than the other, which is exactly the wrong model.

The inoculation is to anchor the team on the mechanism rather than the outcome. The outcome is shared, which is what creates the confusion, but the mechanism is different, and the mechanism is what determines every behavior that matters. Drill the one-sentence contrast until it is reflexive: one trusts a location in the network and leaves the resource public, the other gives the resource a private presence and makes you manage its name. A team that reaches for that sentence first, before reaching for the portal, will not confuse the two, because the sentence forces the two trigger questions into view. The address question and the reach question are right there in the contrast, and they are the questions that decide.

A second habit reinforces the first. Whenever someone proposes a feature for a resource, ask them to say which trigger justifies it or, if neither does, to confirm they are choosing the cheaper option deliberately. That single question, asked routinely in design review, surfaces both failure modes, the under-reach that picks subnet trust when an address or outside consumer demanded a projection, and the overreach that projects everything out of caution. Make the justification a normal part of the conversation and the choices improve across the whole platform, because each one is now defended against the rule rather than chosen by habit. The confusion persists in the wider world because most material describes the outcome; a team that describes the mechanism and demands the justification simply stops being confused.

## The verdict

Stop treating these two as variations on a theme. A service endpoint is subnet trust over the backbone with the resource keeping its public address and its name resolving as before. A private endpoint is a genuine private presence for the resource, an interface in your range, a name that must be overridden in a private DNS zone, and a path that reaches from on-premises. The private-IP-and-on-premises rule decides almost everything: need a private address or outside reach, choose the private endpoint; otherwise let the cheaper, simpler service endpoint do its job. Apply that rule honestly, run the DNS apparatus well when you do reach for projection, and resist the reflex to isolate more than the requirement asks. Do that and you will never again confuse the two, and you will never again pay for projection nobody needed or fail an audit because subnet trust was mistaken for a private address.

## Frequently asked questions

### What is the core difference between a service endpoint and a private endpoint?

A service endpoint keeps the resource on its public address but routes traffic over the Azure backbone and lets the resource trust the originating subnet. A private endpoint places a network interface holding a private address inside your subnet and projects the resource there, so the resource gains a presence inside your own network.

### Does a service endpoint give my resource a private IP address?

No. This is the most consequential misunderstanding in the whole topic. A service endpoint never changes the resource's address; the account, database, or vault keeps its public address and only the path and the trusted identity change. If a requirement depends on a private address, the service endpoint cannot satisfy it and a private endpoint is required.

### Does either option change how the resource's name resolves?

A service endpoint changes nothing about resolution; the public name answers with the public address as it always did. A private endpoint requires a change: the resource's name must be overridden by a private DNS zone so it answers with the private address, otherwise clients resolve the public address and fail against a firewall that now blocks the public path.

### Which one works for an on-premises client?

Only a private endpoint. Its interface holds a private address that an on-premises host can route to across a gateway or circuit, given a forwarding path that resolves the resource's name to that private address. A service endpoint relies on subnet identity, which an on-premises machine cannot present, so it offers no private path from the datacenter.

### Why does my private endpoint exist but clients still cannot connect?

Almost always a resolution problem rather than a connectivity one. The interface is provisioned and healthy, but the consuming client resolves the resource's public address because the private DNS zone is missing, unlinked to that client's network, or holds the wrong record. Confirm the name resolves to the private address from the client's own network first.

### How do the two compare on cost?

A service endpoint has no per-resource hourly charge and no data-processing charge; you enable it on the subnet and that is the cost. A private endpoint bills an hourly charge per interface plus a charge for the data it processes, so protecting many resources or moving large volumes adds up. With no private-address or outside-reach requirement, the service endpoint is the cheaper design.

### Is a private endpoint always the more secure choice?

It depends on what the requirement means by secure. A private endpoint removes the resource from a public address and projects it privately, which some policies require. But a service endpoint also keeps traffic off the public internet and restricts the resource to a trusted subnet. If neither a private address nor outside reach is required, the extra isolation of a private endpoint buys cost and maintenance rather than meeting a real requirement.

### Can I use both for the same resource?

Yes, and during a migration you often do temporarily. The two mechanisms can coexist while you provision and validate a private path before tightening the firewall and removing the subnet trust. As a permanent design, running both for one resource is usually a sign that the requirement was unclear; settle which trigger applies and keep the matching mechanism.

### When should I migrate from a service endpoint to a private endpoint?

When a requirement crosses one of the two triggers, a newly required private address or a newly required private reach from on-premises. The original service endpoint was not a mistake; the requirement changed. Migrate by provisioning the private path and its DNS, validating resolution from every consuming network, and only then removing the public path and the subnet trust.

### What breaks most often during that migration?

Cutting over in the wrong order. If you remove the service endpoint trust or tighten the firewall before the private name resolves everywhere, clients briefly resolve a public address the firewall already refuses, and connections drop. Provision and verify the private route first, confirm resolution from every network including hybrid clients, and only then close the public path.

### Does enabling a service endpoint affect more than one resource?

Yes. The trust is granted per resource type at the subnet, not per individual resource. Enabling the storage service endpoint on a subnet steers and stamps traffic to storage generally, and any account that trusts that subnet accepts it. To isolate exactly one resource instance, use the per-resource scope of a private endpoint.

### Do I need a private DNS zone for a service endpoint?

No. A service endpoint leaves name resolution untouched, so there is no zone to create, link, or maintain. The absence of any DNS apparatus is one of the reasons a service endpoint is simpler and cheaper to operate when subnet trust is all the requirement needs.

### How does a private endpoint reach across peered networks?

The interface is reachable from a peered network when a route to its private address exists and that network is linked to the private DNS zone holding the override record. The route alone is not enough; a peered spoke that can reach the address but was never linked to the zone resolves the public name and fails, which is a frequent oversight when adding new spokes.

### Can I route on-premises traffic through a virtual network to use a service endpoint?

No. The subnet stamp that a service endpoint relies on is applied to traffic originating in the enabled subnet, not to traffic merely transiting the network. On-premises traffic passing through does not gain the subnet identity, so the resource firewall treats it as public traffic. Private reach from on-premises needs a private endpoint.

### Which feature should I default to for a new in-network workload?

If every consumer sits inside the virtual network, you do not need a private address, and nothing external reaches the resource, default to a service endpoint. It meets the requirement with the least cost and the least to operate. Reach for a private endpoint only when one of the two triggers actually fires.

### How do network security groups interact with each feature?

Both still pass through the subnet's filtering. A service endpoint changes the path and the trusted identity but a network security group still evaluates the flow, and you can scope outbound rules with the resource's service tag. A private endpoint's interface can have network policies applied on its subnet, so confirm whether your filtering actually evaluates traffic to the interface.

### What is the single fastest way to decide between them?

Ask the two trigger questions in order. Do you need a private address for the resource? Does anything outside the virtual network need to reach it privately? If either is yes, choose a private endpoint. If both are no, choose a service endpoint. The remaining considerations, DNS, cost, and operations, follow from that answer rather than override it.

### Where can I practice configuring both safely?

Stand up each configuration against the same resource in a sandbox so you can see the difference in resolution and routing directly. The hands-on labs and command library let you enable a service endpoint, then add a private endpoint with its DNS zone, and watch how the firewall and the resolver respond to each, which makes the abstract distinction concrete in a way reading alone does not.

### Do I need an interface per function of a resource?

Often yes. A resource that exposes several functions, such as a storage account with blob, file, queue, and table access, attaches each function to its own interface and its own record. An interface created for one function does not cover the others, so enumerate the functions a workload uses and provision one interface per function in use.

### How does the choice change for a resource shared across organizations?

Subnet trust only applies within one network boundary, so it cannot serve a consumer in another organization. A projection can, through an approval model: the consumer requests an interface into its own network and the resource owner approves the connection explicitly. That cross-directory approval, with its pending and rejected states, is unique to projection and has no equivalent in subnet trust.
