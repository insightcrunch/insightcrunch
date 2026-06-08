---
layout: post
title: "Azure Private Link and Private Endpoints"
page_title: "Azure Private Link and Private Endpoints Explained: How Private Endpoints, DNS, and Service Endpoints Work"
date: 2023-09-11
categories: ["Technology"]
tags: ["Azure", "Private Link", "Private Endpoint", "Networking", "DNS", "Cloud Computing"]
excerpt: "Azure Private Link projects a service into your VNet as a private endpoint, and DNS is the linchpin that decides whether traffic ever reaches it correctly."
image: "/assets/images/blog/blog-40.webp"
reading_time: 62
author: "alex-cunningham"
last_updated: 2023-09-11
lang: en
---
# Azure Private Link and Private Endpoints

Most engineers meet Azure Private Link on a bad afternoon. A storage account, a SQL database, or a Key Vault has been locked down so that public network access is disabled, a endpoint has been created in the right subnet, and yet an application sitting two subnets away still cannot reach it, or worse, it reaches the public front door and gets refused. The team stares at a endpoint that looks correct in the portal, a network interface that holds a tidy private IP, and a connection that behaves as if none of it exists. The configuration is not wrong in the way most people assume. The piece that decides whether any of this works is name resolution, and name resolution is the half of Azure Private Link that the portal makes look optional when it is not.

This deep dive treats Azure Private Link as a mechanism rather than a checkbox. By the end you should be able to hold a clear mental model of what a endpoint actually is at the network layer, explain why DNS is the load-bearing element rather than a finishing touch, reason about how the consumer side and the producer side fit together, and tell the difference between a endpoint and a service endpoint without reaching for a vendor comparison chart. The goal is the kind of understanding that lets you predict behavior before you deploy and localize a failure quickly when it appears.

![Azure Private Link and private endpoints model map](/assets/images/blog/blog-40.webp)

## What Azure Private Link actually is

Strip away the marketing language and Private Link is a way to take a service that normally answers on a public address and project a single instance of it into your virtual network as a network interface card that carries a private IP from your own address space. That projected interface is the endpoint. From the perspective of anything inside the network, the service stops looking like a public destination on the internet and starts looking like a host that lives down the hall, reachable over the same routed paths and subject to the same network controls as any other internal workload.

The word that does the most work in that description is projection. The service itself does not move. A storage account remains a multitenant resource running in a region, shared across many customers, fronted by a public endpoint that the rest of the world can still reach unless you turn that access off. What changes is that one mapping from a customer to that service now has a dedicated network presence inside the customer network. The endpoint is a tenant-specific doorway into a service that otherwise has no idea which virtual network any given request originated from.

Underneath, the doorway is built from a network interface. When you create a endpoint, the platform allocates a NIC in the subnet you nominate, assigns it an address from that subnet's range, and wires that interface to the target resource through the Azure backbone. The interface is real in the sense that it consumes an address, shows up in the resource group, and can be inspected like any other interface. It is special in the sense that you cannot attach it to a virtual machine or repurpose it. Its only job is to terminate traffic destined for the linked resource and forward that traffic across the backbone to the actual service instance.

### Is a private endpoint just a fancy firewall rule?

No. A endpoint is a routable network object with its own address, not a permission. A firewall rule decides whether a packet is allowed to pass; a endpoint creates a new, internal destination that did not exist before and that traffic can route to natively. The distinction matters because it explains why the endpoint, once created, behaves like any other host on the network.

That difference becomes concrete the moment you think about routing. A firewall rule on a storage account that allows a particular subnet still sends traffic to the service over its public IP; the packets leave your network, traverse the internet or the Microsoft backbone toward a public front end, and the firewall simply decides whether to accept them on arrival. A endpoint inverts the geometry. The destination address is now inside your network, the route to it is a connected route in your own subnet, and the packets never need a public path at all. You have not merely permitted the connection, you have relocated the destination.

## The model map: consumer, producer, DNS, and the service-endpoint contrast

The single most useful artifact for reasoning about Private Link is a map that places the four moving parts side by side. Everything else in this article is an elaboration of one row or another in the InsightCrunch Private Link model map below.

| Element | What it is | Where it lives | What it does | What breaks if it is missing |
| --- | --- | --- | --- | --- |
| Private endpoint (consumer side) | A NIC with a private IP from your subnet, bound to one target resource | Your virtual network, in a subnet you choose | Terminates traffic for the resource and forwards it over the backbone | The service has no internal address; nothing to route to |
| Private Link service (producer side) | A front-end that exposes a service behind a standard load balancer for others to reach privately | The provider's virtual network, attached to a load balancer | Publishes the service so consumers can create endpoints to it | First-party services already publish this; for your own service there is nothing to connect to |
| DNS (the linchpin) | A record that maps the service hostname to the endpoint's private IP, usually in a Private DNS zone | A Private DNS zone linked to the consuming network | Makes the client resolve the public hostname to the internal address | The name resolves to the public IP and the interface is bypassed |
| Service endpoint (the contrast) | A subnet setting that routes traffic to a service over the backbone using the public IP | A property on the subnet, not a separate object | Keeps traffic on the backbone but gives no private IP and no inbound reach | Nothing, it is a different mechanism with different properties |

Read the map top to bottom and the architecture tells its own story. The first two rows are the two halves of the connection: the consumer creates an interface, the producer publishes through a Private Link service, and for the first-party Azure resources most teams use the producer half is already built and managed by the platform. The third row is the part that decides whether the first two rows do anything useful, because a private IP that no client ever resolves to is an address nobody dials. The fourth row exists to keep you honest about what you are choosing, since service endpoints solve a narrower problem and confusing the two is the most common conceptual error in this entire area.

When you set this up for real, the configure-private-endpoints walkthrough at [/2023/05/01/configure-private-endpoints/](/2023/05/01/configure-private-endpoints/) takes the model map and turns it into an ordered sequence of commands; this article stays at the level of why each row exists so the sequence makes sense rather than reads as ritual.

## The DNS-is-the-linchpin rule

Here is the claim this article is built to make memorable: a endpoint delivers private connectivity only when DNS resolves the service hostname to the endpoint's private IP, so the NIC and its name resolution are one inseparable unit rather than two features you can adopt separately. Create the interface and skip the DNS, and you have spent an address to build a door that no client knows how to find. The DNS-is-the-linchpin rule is the single idea that, once internalized, makes nearly every Private Link incident obvious.

The reason DNS carries this weight is that clients do not connect to IP addresses, they connect to names. An application does not open a socket to a numeric address for a storage account; it opens a socket to a hostname such as the account's blob service name, and a library resolves that name to whatever address the resolver returns. The service keeps its public hostname even after you add a endpoint. Nothing about the application's connection string changes. So the only lever that decides whether the application reaches the public front end or the internal interface is the answer the resolver gives when the client asks for that name. Point the answer at the public address and traffic goes out the public path; point it at the endpoint's private IP and traffic goes to the interface in your subnet. That is the entire decision, and it lives in DNS.

### Why does my name still resolve to a public IP after I create the endpoint?

Because creating the NIC does not, by itself, change what any resolver returns. The hostname keeps its public record in public DNS until you introduce a private record that overrides it for your network. Without a linked Private DNS zone holding the right entry, the client resolves the same public address it always did and the interface sits unused.

This is the failure that sends most teams to the troubleshooting article first and the deep dive second. The full diagnostic chain, including the nslookup signatures that distinguish each variant, lives in the dedicated guide at [/2022/11/28/fix-private-endpoint-dns/](/2022/11/28/fix-private-endpoint-dns/). The point worth absorbing here is structural rather than procedural: the public record never disappears, it is merely shadowed, and only inside the networks where you have arranged the shadow. A virtual machine in a linked network resolves to the internal address while a laptop on the public internet resolves to the public one, and both are behaving correctly. The split is the design, not a bug.

### How the override actually happens

When a first-party Azure service is fronted by a endpoint, the public hostname is typically a friendly name that resolves through a chain to a service-specific zone. A storage blob name, for example, follows a CNAME to a privatelink-prefixed zone name, and it is that prefixed zone that you control. You create a Private DNS zone whose name matches the service's privatelink zone, you add an A record in it that maps the resource to the endpoint's private IP, and you link that zone to every virtual network whose clients should resolve internally. The public chain still ends at a CNAME pointing into the privatelink zone; the difference is that inside your linked networks the privatelink zone now answers with the private address instead of forwarding to the public one.

The mechanism that keeps the A record correct without manual editing is the private DNS zone group, an object associated with the NIC that registers and updates the record automatically as the endpoint's address is assigned or changes. When teams report that resolution worked at first and then drifted, or that a record points at a stale address after a recreate, the zone group is usually the part that was skipped, leaving a hand-entered record that nobody maintained. The relationship between zones, links, records, and the resolver is its own substantial topic, and the mechanics of zones and links are unpacked in the dedicated reference at [/2023/09/18/azure-dns-private-zones-explained/](/2023/09/18/azure-dns-private-zones-explained/).

The architectural takeaway is blunt. If you remember nothing else, remember that an interface without its zone, its link, and its record is a half-built feature that resolves publicly, and that the half you can see in the portal is the half that matters least to whether traffic flows correctly.

## How traffic actually flows over a private endpoint

Picture a single request and follow it. An application in a subnet wants to read a blob. It hands the storage hostname to the resolver. Because a Private DNS zone is linked to this network and holds an A record for the account, the resolver returns the endpoint's private IP rather than the public address. The application now has an internal destination, and the operating system consults its route table. The endpoint's address falls inside the local virtual network's address space, so the matching route is a connected route within the network; no gateway, no public hop, no internet path is involved. The packet travels to the network interface that backs the endpoint.

At the interface, the platform takes over. The endpoint is wired across the Azure backbone to the specific service instance it was created for, and traffic is forwarded over that backbone path to the resource. The response returns by the same private route. From the application's point of view it simply connected to the storage account by name and got an answer; from the network's point of view the connection never left the routed boundary of the customer's own address space until it crossed onto the managed backbone, and it never touched a public IP at any point.

Two properties of this flow are worth holding onto. First, the private endpoint is an inbound construct from the service's perspective and a destination from the client's perspective; it does not provide a path for the service to initiate connections back into arbitrary parts of your network. Second, because the interface terminates on a NIC inside a subnet, the traffic is subject to the network controls that apply to that subnet and that interface, which is what makes the next several behaviors, around network security groups and routing, follow naturally rather than as special cases.

## The producer side: the Private Link service

Everything so far has described the consumer half, where you create an interface to reach a service somebody else runs. The other half of the mechanism is the producer side, and it is the part most engineers never touch directly because the Azure first-party services already implement it on their behalf. When you create an interface to a storage account, you are connecting to a publishing surface that the storage team built once and exposes to every customer. The Private Link service is the object that does that publishing, and understanding it removes the mystery from how a single regional service can present a different internal interface to thousands of separate networks at once.

A Private Link service sits in front of a standard load balancer in the provider's own virtual network. The provider builds the application, places it behind that load balancer, and then creates a Private Link service that references the load balancer's front-end configuration. That service becomes an offer: it has an alias, and any consumer who knows the alias or is granted visibility can create a private endpoint that connects to it. When a consumer's endpoint connects, the platform stitches a path from the consumer's interface, across the backbone, to the provider's load balancer front end, and from there to whatever pool of machines or containers the provider placed behind it. The provider never sees the consumer's address space and the consumer never sees the provider's; each side only sees its own end of the tunnel.

### When would I build my own Private Link service?

You build one when you are the provider, not the consumer. If your team runs a service that other teams or other companies need to reach privately, you front it with a standard load balancer, create a Private Link service against that front end, and hand out the alias. Consumers then create endpoints to your alias exactly as they would to a first-party Azure resource.

The asymmetry is the useful part. As a consumer you create endpoints; as a provider you create one service and approve the endpoints that connect to it. This is how a software vendor can offer a multitenant platform that every customer reaches over a private address without the vendor ever peering networks with anyone or exposing the platform on the public internet. The vendor publishes once and approves many. It is also why the producer side scales without the address-space collisions that plague network peering: nothing is peered, nothing shares a route table, and the only shared object is the alias that consumers connect to.

There is a NAT subtlety on the producer side worth naming because it surfaces in real designs. Because many consumer networks may use overlapping private address ranges, the platform applies source NAT on the producer's load balancer for traffic arriving through the Private Link service, so the provider sees connections from a consistent, provider-side address rather than from the consumer's actual client addresses. Providers who need to identify the originating connection rely on the proxy protocol option on the Private Link service rather than on the source IP, since the source IP has been translated by design.

## Private endpoint versus service endpoint: the contrast that matters

The most common conceptual mistake in this whole area is treating service endpoints and private endpoints as two names for the same feature. They are not, and the difference is not cosmetic. A clear grasp of the contrast prevents both overbuilding, where a team stands up endpoints and Private DNS zones for a case a service endpoint would have covered, and underbuilding, where a team enables service endpoints and then wonders why on-premises clients still cannot reach the resource over the private path.

A service endpoint is a property you switch on at the subnet level. It tells the platform that traffic from that subnet to a particular service should take an optimized path over the Microsoft backbone using the service's public IP, and it lets the service's firewall recognize and allow that subnet as a source. Crucially, it does not create any new address. The service still answers on its public endpoint, DNS still resolves to the public IP, and there is no interface in your network. Traffic stays on the backbone and the service trusts the subnet, but the destination is unchanged. Because the source is still your subnet identity expressed over the backbone, a service endpoint helps only resources inside Azure on that subnet; an on-premises client reaching across a gateway gets none of the benefit because it is not in the subnet that the NIC applies to.

A private endpoint, by contrast, creates the interface, assigns the private IP, and changes the destination to an address inside your network. That single structural difference cascades into every distinguishing property. Because the destination is now a private address, DNS must be arranged to resolve to it, which is the work the service endpoint never required. Because the destination is a routable internal address, an on-premises client that can route into the network and resolve the name reaches the resource over the private path, which the service endpoint could never offer. Because the interface is a real object with an address, it costs money per hour and per volume of data processed, where a service endpoint is free. And because the NIC pins one resource to one interface, it gives the tight, single-resource exposure that compliance reviewers usually want, where a service endpoint opens the subnet to a whole service category.

### Which one should I actually choose?

Choose a private endpoint when you need a true private IP, when on-premises or peered clients must reach the resource privately, or when policy demands that public access be disabled entirely. Choose a service endpoint when Azure-resident workloads simply need an optimized, subnet-scoped path and the public endpoint staying reachable is acceptable. The deciding factor is whether you need a private address, not whether you want security.

That decision deserves its own treatment because the cost, the on-premises reach, and the migration path between the two are where teams spend real deliberation, and the side-by-side decision rule lives in the comparison at [/2023/11/06/service-vs-private-endpoints/](/2023/11/06/service-vs-private-endpoints/). For the purposes of the model, hold this line: a service endpoint changes who the service trusts, while a private endpoint changes where the service lives. One is a trust statement, the other is a topology change, and topology is the stronger guarantee precisely because it does not depend on the public endpoint remaining reachable.

## The cross-tenant approval model

A private endpoint is not only a network object, it is also a relationship that someone on the resource side has to consent to. This consent model is invisible when you connect to your own storage account in your own subscription, because the platform auto-approves a connection whose owner has rights over both ends. It becomes very visible the moment the consumer and the producer sit in different subscriptions or different tenants, which is exactly the situation when one company consumes another company's Private Link service or when an organization separates its networking and workload subscriptions for governance.

Every private endpoint carries a connection state, and the state is the heart of the approval model. A freshly created endpoint to a resource the creator does not own enters a Pending state. It exists, it has consumed an address, and it cannot carry traffic until the owner of the target resource moves it to Approved. The owner may instead Reject it, which is a terminal refusal, or later Disconnect an approved connection to sever it. The consumer can supply a request message when creating the endpoint, and the approver sees that message alongside the requesting connection, which is how the two sides coordinate when they cannot see each other's portals.

### Who approves a cross-tenant private endpoint, the consumer or the producer?

The producer approves. The party who owns the target resource or the Private Link service holds the approval right, because the interface is asking for access into something they control. The consumer creates and pays for the endpoint, but it stays in Pending and carries no traffic until the resource owner approves the connection on their side.

This split is deliberate and it mirrors how trust should flow. The consumer can spend their own address space and their own money to build a doorway, but they cannot force the service to accept callers through it; the service owner retains the final say. In a manual-approval flow the consumer creates the NIC by resource ID or by alias, the connection appears in the provider's list of pending connections with the request message attached, and an operator or an automated policy on the provider side approves or rejects it. For first-party resources within a single ownership boundary the platform short-circuits this to automatic approval, which is why the model is easy to forget until a cross-tenant case forces it into view.

The connection state is also a diagnostic surface. An endpoint that was working and then stopped, with no DNS or routing change, frequently turns out to have been disconnected from the resource side, perhaps by a policy sweep or a deliberate revocation. Reading the connection state before chasing name resolution saves time, because a disconnected or rejected connection will never carry traffic no matter how perfect the DNS chain is.

## The configuration that realizes the model

Reasoning about Private Link is the point of this article, but a model you cannot instantiate is just a diagram, so it helps to see the commands that turn each row of the model map into a real object. The deep walkthrough belongs to the setup guide, yet a compact reference makes the moving parts concrete.

Creating an interface to a first-party resource with the Azure CLI looks like this:

```bash
# Create the private endpoint against a target resource and its sub-resource (group ID)
az network private-endpoint create \
  --name pe-storage-blob \
  --resource-group rg-network \
  --vnet-name vnet-prod \
  --subnet snet-endpoints \
  --private-connection-resource-id "/subscriptions/<sub>/resourceGroups/rg-data/providers/Microsoft.Storage/storageAccounts/stproddata" \
  --group-id blob \
  --connection-name conn-storage-blob
```

The group ID, also called the sub-resource, is the field that tells the platform which facet of a multifaceted service you are reaching. A storage account exposes separate group IDs for blob, file, queue, table, and other services, and each warrants its own endpoint with its own DNS zone, because each facet has its own hostname. Choosing the wrong group ID is a quiet error: the interface creates successfully, but it fronts a service facet your application never calls, so connectivity to the facet you actually use never improves.

The DNS half is what makes the NIC usable, and it is the half the command above does not do on its own. Wiring the zone group ties the record to the interface so it stays correct automatically:

```bash
# Create or reference the service-specific privatelink zone, link it, then attach a zone group
az network private-dns zone create \
  --resource-group rg-network \
  --name "privatelink.blob.core.windows.net"

az network private-dns link vnet create \
  --resource-group rg-network \
  --zone-name "privatelink.blob.core.windows.net" \
  --name link-vnet-prod \
  --virtual-network vnet-prod \
  --registration-enabled false

az network private-endpoint dns-zone-group create \
  --resource-group rg-network \
  --endpoint-name pe-storage-blob \
  --name zg-blob \
  --private-dns-zone "privatelink.blob.core.windows.net" \
  --zone-name blob
```

The same shape expresses cleanly as infrastructure as code, which is how production teams keep the NIC and its DNS chain together so neither drifts from the other:

```bicep
resource pe 'Microsoft.Network/privateEndpoints@2023-09-01' = {
  name: 'pe-storage-blob'
  location: location
  properties: {
    subnet: { id: subnetId }
    privateLinkServiceConnections: [
      {
        name: 'conn-storage-blob'
        properties: {
          privateLinkServiceId: storageAccountId
          groupIds: [ 'blob' ]
        }
      }
    ]
  }
}

resource zoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = {
  parent: pe
  name: 'zg-blob'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'blob'
        properties: { privateDnsZoneId: privateDnsZoneId }
      }
    ]
  }
}
```

Notice that the infrastructure-as-code form keeps the interface and the zone group in the same template. That co-location is not a style preference, it is the structural expression of the linchpin rule: define the NIC without the zone group and you have codified the half-built state into your pipeline, guaranteeing that every environment you deploy resolves publicly until somebody fixes DNS by hand. If you want a sandbox to create these objects, disable public access, and watch resolution change before and after, you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), which lets you project a service privately and trace the name resolution end to end without touching a production tenant.

## Failure modes and the tools that expose them

Private Link fails in a small number of recognizable ways, and almost all of them trace back to one of the four rows in the model map being absent, misconfigured, or in the wrong state. Learning to map a symptom to a row is faster than learning a checklist, because the model tells you where to look rather than what order to click.

The first and most frequent failure is the name resolving to the public address. The endpoint exists, the interface holds an address, but a client resolves the service hostname and gets the public IP, so traffic takes the public path and then either succeeds against the public front end, which masks the misconfiguration, or fails because public access has been disabled, which surfaces it as a refused connection. The confirming move is to resolve the name from the client and inspect the answer. A private answer means DNS is wired; a public answer means the zone, the link, or the record is missing, and the diagnosis narrows immediately to which of those three.

The second failure is the right DNS in the wrong place. A Private DNS zone holds the correct record, but it is linked to a different virtual network than the one the client lives in, so the client never consults it and resolves publicly. This is the hub-and-spoke trap: the zone is linked to the hub, the client sits in a spoke, and unless the spoke's resolution path leads to a network where the zone is linked, the spoke gets the public answer. The fix is conceptual before it is procedural, because it requires understanding that a zone resolves only for the networks it is linked to and for networks whose DNS forwards into a linked network.

The third failure is the stale or hand-entered record. Someone created the interface and typed an A record manually instead of attaching a zone group, the endpoint's address later changed on a recreate, and the record now points at an address nothing answers on. The signature is a private answer that nonetheless fails to connect, which distinguishes it cleanly from the public-answer failures above.

The fourth failure is the connection state, covered earlier: a Pending, Rejected, or Disconnected connection that no amount of correct DNS will rescue. The fifth is a network control sitting in the path, which the next section addresses. The sixth is the wrong group ID, where everything is correct for a service facet the application does not use.

### What tool tells me which failure I have?

Name resolution from the client tells you whether DNS is the problem: a public answer points at the zone, link, or record; a private answer that still fails points at routing, a network control, the connection state, or a stale record. Network Watcher's connection troubleshoot and IP flow verify then localize a private-answer failure to its exact hop.

The discipline that makes diagnosis fast is to resolve first and route second. Resolution from the affected client is a single question with a binary answer that immediately splits the entire failure space in half. If the answer is public, you are working the DNS rows of the model and nothing else matters yet. If the answer is private, DNS is exonerated and you move to routing, network security groups, the connection state, and the record's accuracy. Skipping this split is why teams burn hours editing firewall rules to fix what was always a missing zone link, and the full set of nslookup signatures that separate the DNS variants is laid out in the troubleshooting guide at [/2022/11/28/fix-private-endpoint-dns/](/2022/11/28/fix-private-endpoint-dns/).

## How a private endpoint interacts with the rest of the network

Because a private endpoint terminates on a network interface inside a subnet, it inherits the network's behavior rather than standing outside it, and several questions that seem like special Private Link mysteries are simply the ordinary rules of subnets, routing, and security groups applied to an unusual interface.

Take network security groups. For a long time, network security group rules did not apply to traffic destined for a private endpoint, which surprised teams who expected to filter access to the NIC with the same rules they used everywhere else. The platform now supports applying network security groups to private endpoint traffic when the subnet is configured to enforce network policies for endpoints, through a subnet setting that controls whether network security group and user-defined route rules take effect on endpoint traffic. The practical consequence is that whether your security group rules govern who can reach the interface depends on a subnet-level policy switch, and a rule that appears to be ignored is often a policy that was never enabled rather than a rule that was written wrong.

Routing interacts in a more subtle way. The platform installs a system route for the endpoint's private IP with a very high specificity, effectively a host route, so that traffic to the NIC goes directly to it. This matters when you run forced tunneling or a network virtual appliance that pulls all traffic through an inspection device with a broad user-defined route. The host route for the endpoint can take precedence over your broad route, which means traffic to the endpoint may bypass the appliance you intended it to traverse. Teams who require that interface traffic be inspected have to account for this explicitly rather than assuming a default route to an appliance will capture it, and the subnet policy that governs user-defined routes for endpoints is the lever that brings that traffic back under the route table's control.

The third interaction is peering and on-premises reach, which is where the private endpoint earns its keep over a service endpoint. Because the endpoint's address is an ordinary private IP in the subnet, any network that can route to that subnet and resolve the name reaches the resource. A peered virtual network reaches it if the Private DNS zone is also linked to a network in the resolution path. An on-premises client reaches it across a gateway if a conditional forwarder sends the relevant zone's queries to a resolver that can answer with the private address, typically the Azure-provided resolver reached through a DNS forwarder in Azure. This is precisely the reach a service endpoint cannot provide, and it is the single most common reason a design that started with service endpoints migrates to private endpoints once on-premises clients enter the picture.

## Designing Private Link for production

Building one endpoint by hand teaches the mechanism. Running Private Link across a fleet of subscriptions and hundreds of resources is a different problem, and the design decisions that matter at that scale are mostly about where DNS lives, how endpoints get created consistently, and how you keep the whole thing from rotting as people come and go.

The first decision is centralizing the Private DNS zones. In a hub-and-spoke or landing-zone design, you create each service's privatelink zone once in a central networking subscription and link it to every virtual network that needs to resolve privately, rather than scattering per-team zones that drift apart. Centralized zones give you one authoritative record set per service and one place to audit resolution, and they match the way most clients resolve, since spokes typically forward DNS to a central resolver in the hub. The cost of centralization is a dependency: every spoke's private resolution now relies on the central zones being linked and the forwarding path being intact, so that path becomes something you monitor rather than assume.

The second decision is automating endpoint creation and DNS together. Manual endpoint creation is where the linchpin rule gets violated, because a human creates the endpoint, gets distracted, and never attaches the zone group. Azure Policy can both detect and remediate this. A policy can require that any supported resource have public network access disabled, can deny resources created without a private endpoint, and can automatically create the private DNS zone group for new endpoints so the record is always registered against the central zone. Wiring these policies means the half-built state stops being reachable: an endpoint cannot exist for long without its DNS because the platform repairs the omission. This is the production answer to the most common failure, and it is far more reliable than documentation asking engineers to remember the zone group.

The third decision is per-facet discipline. Because each service facet has its own group ID and its own hostname, a storage account used for both blobs and files needs two endpoints and two zones, and a data platform that exposes several sub-resources needs an endpoint and a zone per sub-resource your applications actually call. Teams that create a single endpoint and assume it covers the whole account discover later that one workload resolves privately and another still resolves publicly, because the second workload calls a facet the lone endpoint never fronted. Designing per facet from the start avoids a confusing partial rollout.

### How many private endpoints do I need for one resource?

You need one endpoint per service facet your applications actually use, each with its own DNS zone. A storage account reached for both blob and file traffic needs two endpoints and two zones, because each facet has a distinct group ID and hostname. Facets you never call need no endpoint at all.

The fourth decision is sizing the endpoint subnet and watching the address budget. Each endpoint consumes an address, and a large estate can place hundreds of endpoints in a dedicated subnet, so the subnet must be sized for growth rather than for the initial count. Many teams reserve a dedicated endpoints subnet per spoke precisely so that the address consumption is isolated and visible, and so that the subnet policy that governs network security groups and routes for endpoints can be set once for the whole class of objects rather than negotiated per resource. The broader picture of how this fits a routed, filtered Azure network is the subject of the networking fundamentals material, and the model map in this article is meant to slot into that larger view rather than stand alone.

## Real-world patterns the model explains

The value of holding the model rather than a checklist is that recurring situations engineers hit at work stop being surprises and become predictable instances of the same few rules. A handful of patterns recur often enough to be worth naming.

The first pattern is choosing an endpoint over a service endpoint for a true private address. A team needs the resource reachable from on-premises over the private path and needs public access disabled for compliance. The model says immediately that a service endpoint cannot satisfy either requirement, because it gives no private IP and helps only the in-subnet source, so the endpoint is the only mechanism that fits. The deciding factor is the private address, and once that is named the choice is not a debate.

The second pattern is the endpoint that resolves publicly. An application cannot reach a locked-down resource, the endpoint looks correct, and resolution from the client returns the public address. The model places this on the DNS rows instantly: zone missing, zone present but unlinked to this network, or record missing because no zone group was attached. The fix is to identify which of the three and repair it, and the symptom never required touching the endpoint object at all.

The third pattern is exposing an internal service through a Private Link service. A platform team runs a service that partner teams must reach without peering and without public exposure. The model says they are now the producer, so they front the service with a standard load balancer, create a Private Link service, and hand out the alias, after which consumers create endpoints and the platform team approves them. The asymmetry of the producer and consumer halves is the whole answer.

The fourth pattern is approving a cross-tenant connection. A consumer in another tenant has created an endpoint to your resource and reports that it does not work. The model says to read the connection state before anything else, because a Pending connection carries no traffic until you approve it, and a Rejected or Disconnected one never will. This is a thirty-second check that frequently ends the investigation.

The fifth pattern is the storage decision between Private Link and a service endpoint. A team weighs the free, simple service endpoint against the endpoint that costs money but gives a private address and on-premises reach. The model frames the trade as trust statement versus topology change, and the decision rule turns on whether a private address and external reach are required; the detailed cost and migration analysis sits in the dedicated comparison article.

The sixth pattern is the traffic-flow question itself, usually phrased as a worry that the endpoint somehow opens an inbound path from the service into the network. The model answers that the endpoint is a destination for the client and an inbound termination for the service, not an initiator, so the service cannot use it to reach arbitrary hosts in the network; the flow is client to endpoint to backbone to service and back, and nothing in that path lets the service originate connections inward.

## A worked end-to-end diagnosis

Patterns are easier to trust after watching the model resolve a single messy case from symptom to cause. Consider a realistic report: an application in a spoke network cannot reach a SQL database that has had public access disabled and a private endpoint added, and the team has already spent an afternoon adjusting firewall settings on the database with no change.

Start by resolving the database hostname from the application host. The answer comes back as the public address. That single result collapses the problem space: this is a DNS-row failure and nothing on the database firewall was ever going to fix it, which explains why the afternoon was wasted. The next question is which of the three DNS conditions holds. A Private DNS zone for the SQL privatelink name exists in the central networking subscription, so the zone is not missing. Checking the zone's virtual network links shows links to the hub and to two other spokes but not to the spoke this application runs in. That is the cause: the zone is correct, the record is correct, but the zone is not linked to the network whose clients need to resolve it, and the spoke's resolver forwards to a path that never consults the zone.

The repair is to link the zone to the spoke, or to ensure the spoke's DNS forwards into a network where the zone is linked, after which resolution from the application host returns the private address. A second resolution check confirms the private answer, a connection attempt succeeds, and the connection state on the endpoint reads Approved because this is a same-tenant resource that auto-approved. The whole diagnosis took four checks: resolve, confirm the answer is public, find the missing link, repair and re-resolve. The model turned an open-ended firewall hunt into a short, ordered walk down the rows of the map.

## The two counter-readings worth correcting

Two wrong mental models cause most of the confusion in this area, and naming them directly inoculates against the failures they produce.

The first wrong model is that service endpoints and private endpoints are interchangeable, two flavors of the same private-access feature. They are not the same kind of object at all. One is a subnet property that optimizes the path to a public IP and lets the service trust the subnet; the other is a network interface with a private address that relocates the destination into your network. The harm in conflating them is bidirectional. A team that reaches for an endpoint when a service endpoint would do pays for endpoints and maintains Private DNS zones for an in-Azure case that needed neither. A team that enables service endpoints expecting on-premises clients to gain private reach discovers that the on-premises clients see nothing, because the service endpoint applies to the subnet and an on-premises client is not in it. The correction is the line from earlier: a service endpoint changes who the service trusts, a private endpoint changes where the service lives.

The second wrong model is that the private endpoint works on its own, with DNS as an optional refinement you can add later. This is the more dangerous error because the endpoint looks finished in the portal, which makes the missing half invisible. The endpoint without its zone, link, and record is a private address that no client resolves to, so traffic continues out the public path until that path is also closed, at which point the application simply fails. The correction is the linchpin rule, and the strongest way to enforce it is structural: keep the endpoint and its zone group together in the same template and let policy remediate any endpoint created without DNS, so the half-built state cannot persist long enough to cause an incident.

Both corrections share a theme. Private Link looks like a single feature you toggle, and it is actually a small system of cooperating parts where the visible part is not the decisive one. Engineers who internalize that the decisive part is name resolution, not the endpoint object, debug these systems in minutes rather than afternoons.

## The privatelink DNS zones you will actually use

Because DNS is the linchpin, the most practical reference an engineer can carry is the mapping from a service to the privatelink zone name its endpoint requires, since getting the zone name wrong is the same as having no zone at all. The hostnames differ by service and sometimes by cloud, and the privatelink-prefixed zone is the one you create and link, while the public chain ends with a CNAME into it.

| Service facet | Public hostname suffix | Private DNS zone to create and link |
| --- | --- | --- |
| Storage blob | blob.core.windows.net | privatelink.blob.core.windows.net |
| Storage file | file.core.windows.net | privatelink.file.core.windows.net |
| Azure SQL Database | database.windows.net | privatelink.database.windows.net |
| Key Vault | vault.azure.net | privatelink.vaultcore.azure.net |
| Cosmos DB (SQL API) | documents.azure.com | privatelink.documents.azure.com |
| App Service / Functions | azurewebsites.net | privatelink.azurewebsites.net |

The table is a starting reference rather than an exhaustive list, and the authoritative set of zone names for every service is published in the official Azure documentation, which should be checked when you onboard a service not shown here. The structural point the table reinforces is that the zone name is service-specific and facet-specific, so a single estate that uses storage, SQL, Key Vault, and a web app maintains several distinct privatelink zones, each linked to the networks that resolve it. Misreading the suffix, for example creating a zone for the public suffix rather than the privatelink-prefixed one, produces a zone that the public CNAME chain never lands in, so resolution proceeds to the public address as if no zone existed. The fix is to match the prefixed zone name exactly to the one the service's CNAME chain expects.

## What Private Link protects and what it does not

It is worth being precise about the security posture a private endpoint gives you, because the word private invites the assumption that the endpoint is, by itself, a complete access control. It is not, and treating it as one leaves gaps.

A private endpoint removes the need for the resource to be reachable over the public internet, which shrinks the externally exposed surface to nothing once public access is disabled. That is a real and significant reduction: an attacker who cannot resolve or route to a private address cannot reach the resource at all from outside the network. What the endpoint does not do is authenticate or authorize the callers that can reach it. Any host that can route to the endpoint's address and resolve the name can attempt a connection, so the endpoint must still sit behind the resource's own authentication and authorization, behind network security groups that limit which sources can reach it where subnet policy enforces them, and within a network whose segmentation reflects who should be able to reach what. The endpoint changes the topology so that access requires being on the network; it does not decide who on the network is allowed in.

This is why the production designs that hold up pair the endpoint with the rest of the controls rather than leaning on it alone. Disabling public access closes the outside path, the endpoint provides the inside path, network security groups and segmentation decide who on the inside may use that path, and the resource's identity and authorization decide what an allowed caller may do. Each layer answers a different question, and the endpoint answers only the question of where the service lives. Reasoning about exposure this way, layer by layer, prevents the false comfort of assuming that a private address is the same thing as a secured one.

## Public access modes and the resource firewall

A private endpoint does not exist in isolation from the target resource's own network settings, and the interplay between the two is where a surprising number of half-working configurations come from. Most first-party services expose a public network access control with a few positions: allow from all networks, allow from selected networks, or disable public access entirely. The endpoint is orthogonal to this control in principle but tightly related in practice.

When public access is left at allow from all networks, the endpoint works and the public path also remains open, so both routes reach the service. This is the configuration that masks DNS mistakes, because an application that resolves to the public address still connects and nobody notices that the endpoint is being bypassed. When public access is set to selected networks, the resource firewall begins refusing sources it does not recognize, and traffic arriving through the endpoint is treated as coming from the private path and is allowed, while public traffic from unlisted sources is refused. When public access is disabled, the only way in is the endpoint, which is the configuration most compliance regimes want and the one that turns a DNS mistake from invisible into a hard failure.

The lesson for design is to disable public access deliberately as the final step, after the endpoint and its DNS are verified working, not before. Disabling it first produces an outage while the DNS chain is still being assembled, and teams under pressure then sometimes re-enable public access to restore service, which quietly reintroduces the exposure they were trying to remove. The correct order is to build the endpoint, wire and verify DNS, confirm the application resolves and connects over the private path, and only then close the public door. Done in that order, closing public access is a non-event because nothing was depending on the public path anymore.

There is also a distinction between disabling public access and using a resource firewall allowlist that includes trusted Azure services or specific public ranges. The allowlist keeps the public endpoint reachable for the listed sources, which is sometimes necessary for a service that cannot use a private endpoint, while the private endpoint serves the workloads that can. A mixed posture like this is legitimate, but it should be a conscious choice rather than the accidental result of never having closed public access, and an audit of public-access settings across an estate routinely turns up resources that were meant to be private but were left open because the closing step was skipped.

## Controlling who can connect to a Private Link service

On the producer side, beyond manual and automatic approval, the Private Link service offers controls over who can even see and request a connection, and these matter for any team publishing a service to consumers they do not fully control. The service has a visibility setting that determines which subscriptions can discover and connect to it, and an auto-approval list that lets named subscriptions connect without a manual approval step while everyone else lands in the pending queue.

The combination gives a provider a spectrum of openness. A fully private offering restricts visibility to a known set of subscriptions and approves them automatically, so trusted consumers connect without friction and nobody else can even request. A broader offering makes the alias discoverable and relies on manual approval to vet each requester, which suits a service offered to many customers where each connection should be reviewed. The request message that the consumer supplies becomes the human context for that review, since the provider cannot see the consumer's environment and has only the message and the requesting subscription to judge by.

Designing this well means deciding early whether the service is an invite-only resource for a handful of known subscriptions or a published offering open to request, because the two imply different visibility and approval settings and different operational load. An invite-only service runs itself once the auto-approval list is set; a published offering needs someone or some automated policy watching the pending queue. Getting this wrong in the open direction means a flood of pending connections nobody triages; getting it wrong in the closed direction means legitimate consumers cannot even find the alias to request a connection.

## Observing endpoints in production

A private endpoint is mostly invisible when it works, which is a virtue until something changes and you need to know whether the endpoint is the reason. A few signals are worth wiring into monitoring so that an endpoint problem announces itself rather than hiding behind an application error.

The connection state is the first signal, because an endpoint that moves from Approved to Disconnected, perhaps because a policy on the resource side revoked it, will break traffic with no DNS or routing change to explain it. Watching the state of important endpoints catches this class of failure at its source. The endpoint also emits metrics for data processed in and out, and a sudden drop to zero on an endpoint that normally carries steady traffic is a strong early indicator that something upstream, often DNS, has started sending clients to the public path instead. Network Watcher's tools turn an alert into a localized cause: connection troubleshoot exercises the path end to end, IP flow verify confirms whether a network security group is permitting the flow, and next hop confirms whether routing is sending endpoint traffic where you expect rather than into an appliance that black-holes it.

The deeper habit worth building is to monitor resolution, not just the endpoint object. Because name resolution is the linchpin, a synthetic check that resolves the service hostname from a representative client and asserts that the answer is the private address catches the most common failure before any user does. An endpoint can be perfectly healthy while a DNS change three layers away quietly redirects clients to the public path, and only a resolution check from the client's vantage point sees that, since the endpoint itself has no way to know that nobody is dialing its number.

## How the cost model shapes design

The endpoint is not free, and while the per-hour and per-gigabyte charges are modest for a single endpoint, they shape design at scale in ways worth anticipating. A private endpoint bills for the time it exists and for the data processed through it, in both directions, so an estate with many endpoints carrying heavy traffic accrues a cost that a service endpoint, which is free, does not. This is not a reason to avoid endpoints where they are needed, since the private address and the on-premises reach they provide are often non-negotiable, but it is a reason to be deliberate about creating endpoints only for facets that workloads actually use rather than blanketing every account with endpoints for every sub-resource by default.

The cost interacts with the per-facet discipline discussed earlier. Creating an endpoint for a storage facet no application calls spends money to front a door nobody opens, so the per-facet rule saves cost as well as preventing confusion. At the high end, very high-throughput workloads should account for the data-processing charge in their cost model, and in some such cases the comparison against a service endpoint, which carries no data charge but offers no private address, becomes a genuine trade rather than a foregone conclusion. The detailed cost comparison belongs to the dedicated service-versus-private-endpoint analysis, but the design principle that follows from the cost model is simple: create endpoints where the private address or the external reach is required, size and place them deliberately, and do not let a default of an endpoint for everything turn a security improvement into an avoidable line item.

## How resolution traverses the CNAME chain

The override that DNS performs is worth tracing one more level down, because the CNAME chain is where teams who think they have the right zone discover they created a record in the wrong place. When a client asks for a storage blob hostname, public DNS does not answer with an address directly. It answers with a CNAME that redirects the query toward a privatelink-prefixed name, and that prefixed name is the one the privatelink zone owns. Inside a network where the privatelink zone is linked and holds the endpoint's record, the query lands in the zone and resolves to the private address. Outside that network, the prefixed name resolves through the platform to the public address, completing the same chain to a different end.

The consequence is that you do not override the friendly public name directly; you let the public chain redirect to the privatelink name and you control what the privatelink name resolves to. A team that tries to short-circuit this by creating a zone for the public suffix rather than the privatelink suffix builds a zone the CNAME chain never reaches, so the carefully entered record sits in a zone no query consults. The signature of this mistake is a record that looks correct in a zone that looks correct, with resolution that still returns the public address, and the resolution lives in matching the zone name exactly to the privatelink target the public CNAME points at.

This also explains why on-premises resolution needs a forwarder rather than a copy of the record. An on-premises resolver that simply held an A record for the friendly name would miss the CNAME chain and would not benefit from the platform's record management. The supported pattern is to conditionally forward the relevant zones to a resolver in Azure that can follow the chain into the linked privatelink zone, so that on-premises queries traverse the same redirection the in-Azure clients do and arrive at the same private answer. The full mechanics of conditional forwarding and the Azure-provided resolver are the territory of the dedicated DNS article, and the point to carry from here is that resolution is a chain, not a single record, and the privatelink zone is the link in that chain you actually own.

## The regional nature of endpoints and what it means for resilience

A private endpoint connects to a specific resource, and that binding has implications for how a design survives a regional problem. The endpoint itself lives in a subnet in a region, and it fronts a particular resource instance. For a regional service with its own failover, such as a database with a geo-secondary, the question becomes how clients reach the secondary when a failover occurs, since the endpoint was created against the primary's connection surface.

The general shape of the answer is that resilient designs create endpoints for the resources clients need to reach in each region they may run in, and arrange DNS so that the name a client uses resolves to the appropriate regional endpoint. Some services expose a failover-aware listener name that, combined with endpoints in both regions and the right zone links, lets clients follow the service's failover without changing their connection string. The detail varies enough by service that the resilient pattern has to be designed per service rather than assumed, but the underlying principle is consistent with the rest of the model: the endpoint is a regional, resource-bound object, and DNS is what lets a single client name point at whichever endpoint is currently correct.

The practical caution is to test failover with the private path in place rather than validating it only over public access. A failover that works when clients resolve public names can still strand clients that resolve private names if the secondary region lacks an endpoint or a zone link, because the private resolution path was never built on the secondary side. Designing and exercising the private path in both regions before relying on it is the difference between a failover that is clean on paper and one that holds up when it is actually needed.

## Private endpoint versus virtual network integration

A confusion that sits adjacent to the service-endpoint mix-up is conflating a private endpoint with virtual network integration, particularly for App Service and Functions, where both terms appear in the same settings area. They solve opposite directions of the same problem and mixing them produces designs that are exactly backward.

A private endpoint is about inbound: it gives a service a private address so that clients in your network reach it privately. Virtual network integration is about outbound: it lets a web app or function send its outbound calls into your virtual network so that the app can reach private resources, such as a database behind its own private endpoint. A team that wants its web app reachable only from inside the network adds a private endpoint to the app; a team that wants the app to reach a private database adds virtual network integration to the app and a private endpoint to the database. The two are frequently used together precisely because they cover the two directions, and naming the direction you care about, inbound to the service or outbound from the app, immediately tells you which feature you need.

The harm in confusing them is concrete. A team that adds virtual network integration expecting to make the app private discovers the app is still publicly reachable, because integration changed only the outbound path. A team that adds a private endpoint expecting the app to reach a private database finds the app still cannot reach it, because the endpoint changed only how clients reach the app, not how the app reaches others. The correction is the direction test, and it generalizes: whenever a feature touches networking, ask whether it changes inbound reach to the resource or outbound reach from it, and the right tool follows.

## Migrating from service endpoints to private endpoints

Many estates start with service endpoints because they are free and simple, and migrate to private endpoints when a private address or on-premises reach becomes a requirement. The migration is less a cutover than an overlap, and understanding the model makes the overlap safe rather than risky.

The safe sequence builds the private path beside the existing one before removing anything. You create the endpoint and its DNS chain while the service endpoint and the public path still function, so nothing breaks during construction. You verify that clients in the target networks resolve to the private address and connect over it. Only once the private path is proven do you tighten the resource firewall, moving from selected networks that trusted the service-endpoint subnet to disabling public access entirely, which retires the service-endpoint path. Because the private path was built and verified first, the moment you close the public door no client is depending on it, and the migration completes without a connectivity gap.

The trap to avoid is reversing the order, disabling public access or removing the service-endpoint trust before the private path resolves and connects, which produces an outage during the very change meant to harden the system. The model makes the correct order obvious: the linchpin is DNS, so the private path is not real until resolution returns the private address, and you never remove the old path until the new one is real. The decision of whether to migrate at all, weighing the cost and the reach, is the subject of the dedicated comparison, but the mechanics of doing it safely follow directly from holding the model in mind.

## Anti-patterns to avoid

A few recurring anti-patterns cause a disproportionate share of incidents, and naming them makes them easier to catch in review. The first is the endpoint without a zone group, the half-built state that resolves publicly and is the single most common cause of Private Link confusion. The second is scattering per-team Private DNS zones instead of centralizing them, which produces divergent record sets and resolution that works in some networks and not others for reasons nobody can trace. The third is disabling public access before verifying the private path, which converts a hardening change into an outage. The fourth is creating one endpoint for a multi-facet resource and assuming it covers every facet, leaving some workloads resolving privately and others publicly. The fifth is treating the endpoint as a complete access control and skipping the network security groups, segmentation, and resource authorization that decide who on the network may actually use it.

Every one of these anti-patterns is a violation of a single rule from the model: the linchpin rule for the first and third, the centralization principle for the second, the per-facet rule for the fourth, and the layered-posture principle for the fifth. That is the payoff of holding the model rather than a checklist, because the model both predicts the correct design and names the failure when a design departs from it.

## Private Link in a landing-zone topology

At enterprise scale the questions stop being about a single endpoint and become about where responsibility sits. A landing-zone design typically separates a platform team that owns networking and shared services from application teams that own workloads, and Private Link has to fit that division cleanly. The pattern that works places the privatelink DNS zones in a central connectivity subscription owned by the platform team, links those zones to every spoke through automation, and uses policy to ensure that application teams creating endpoints get their records registered into the central zones without needing rights to the zones themselves.

This division resolves a tension that otherwise causes friction. Application teams need to create endpoints as part of deploying their workloads, but they should not own the authoritative DNS zones, because scattered ownership is how record sets diverge. Centralizing the zones with the platform team and remediating endpoint DNS through policy lets application teams create endpoints freely while the platform team retains a single, auditable source of truth for resolution. The endpoint lives with the workload, the zone lives with the platform, and policy is the seam that keeps them consistent. When an auditor asks how the organization knows that a given resource is reachable only privately, the answer is a query against the central zones and the public-access settings, not a survey of every team's individual configuration.

The governance payoff compounds with scale. A handful of policies, requiring public access disabled on supported resources and auto-creating the DNS zone group for new endpoints, enforces the linchpin rule across hundreds of resources without anyone remembering it manually. The same policies make drift visible, because a resource that somehow has public access enabled shows up as non-compliant rather than hiding until an incident. This is the difference between Private Link as a feature that teams apply correctly when they remember and Private Link as a property the platform guarantees, and the second is the only version that holds at scale.

## A decision flow for the common failure

It helps to compress the diagnostic discipline into an ordered flow that any engineer can run when a private endpoint is not behaving, because the order is what makes it fast. The flow has four questions, and each answer eliminates a large part of the problem space.

The first question is what the client resolves the service name to. A public answer means the failure is on the DNS rows, and the second question becomes which of zone-missing, zone-unlinked, or record-missing applies, checked by looking for the privatelink zone, its links to the client's network, and the A record the zone group should have registered. A private answer exonerates DNS entirely and moves to the third question. The third question is the connection state on the endpoint, since a Pending, Rejected, or Disconnected connection carries no traffic regardless of resolution, and this is a thirty-second check that frequently ends the hunt for a cross-tenant or policy-revoked case. If resolution is private and the connection is Approved, the fourth question is whether a network control or route sits in the path, answered with IP flow verify for network security groups and next hop for routing, accounting for the subnet policy that governs whether those rules apply to endpoint traffic at all.

Run in that order, the flow converts a vague connectivity complaint into a localized cause in minutes. The reason it works is that it walks the model map row by row, eliminating each as a cause before moving on, rather than guessing at whichever knob is most familiar. Most teams who struggle with Private Link are not missing knowledge of the knobs; they are missing the order, and the order is the whole value of the model. Resolve, then check state, then check the path, and the failure has nowhere left to hide.

## Closing verdict

Azure Private Link is best understood as a topology change wearing the disguise of a feature toggle. The visible object, the private endpoint, is a network interface that projects a service into your address space as a private IP, and that projection is genuinely useful, because it lets you disable public access and reach a service over a routed private path that on-premises and peered clients can use. But the endpoint is only half the mechanism. The half that decides whether any of it works is DNS, because clients connect to names and the answer the resolver returns is the single lever that sends traffic to the private interface or out the public door. That is the DNS-is-the-linchpin rule, and it is the one idea that turns Private Link from a source of mysterious afternoon-long incidents into a system you can reason about and debug in minutes.

Hold the model map and the rest follows. The consumer creates an endpoint, the producer publishes through a Private Link service that first-party resources already provide, DNS ties the name to the private address, and the service endpoint is the lighter, free alternative that changes trust rather than topology. Build the endpoint and its zone group together, centralize your zones, enforce the linchpin with policy, design per facet, verify resolution before you close public access, and layer the endpoint behind network security groups, segmentation, and the resource's own authorization rather than treating a private address as a finished security control. Do that, and Private Link stops being the thing that breaks on a bad afternoon and becomes the quiet, dependable foundation it is meant to be.

## Frequently Asked Questions

### Q: What is Azure Private Link and what does it actually provide?

Azure Private Link is the mechanism that projects a specific service instance into your virtual network as a network interface carrying a private IP from your own address space, called a private endpoint. It does not move the service; it creates a tenant-specific internal doorway to a service that otherwise answers on a public address. What it provides is the ability to reach that service over a routed private path, to disable the service's public access entirely, and to let peered and on-premises clients reach it privately, all without the traffic ever traversing a public IP. The endpoint behaves like any other host on the network, subject to the same routing and, where subnet policy enforces them, the same security controls. The decisive companion to the endpoint is DNS, which must resolve the service hostname to the endpoint's private address for any of this to take effect.

### Q: What is the difference between a private endpoint and a Private Link service?

They are the two halves of the connection and they sit on opposite sides. A private endpoint is the consumer side: the network interface with a private IP that you create in your subnet to reach a service somebody else runs. A Private Link service is the producer side: the publishing surface, fronted by a standard load balancer, that a provider creates so consumers can connect endpoints to it. When you reach a first-party Azure resource, the producer half is already built and operated by the platform, so you only ever create endpoints. You build a Private Link service yourself only when you are the provider exposing your own application for others to reach privately. The asymmetry is the key: consumers create endpoints, providers publish one service and approve the endpoints that connect, which is how a multitenant platform serves many private consumers without peering networks.

### Q: Why does my private endpoint name still resolve to a public IP?

Because creating the endpoint does not change what any resolver returns. The service keeps its public DNS record, and that record stays the answer until you introduce a private record that overrides it inside your network. The three conditions that produce a public answer are a missing Private DNS zone for the service's privatelink name, a zone that exists but is not linked to the virtual network your client lives in, or a missing A record because no private DNS zone group was attached to the endpoint to register it. Resolve the name from the affected client: a public answer points you at one of those three, and the repair never touches the endpoint object itself. This is the most common Private Link failure precisely because the endpoint looks complete in the portal while the resolution half, which is what actually matters, is invisible there.

### Q: How does DNS make Private Link work?

Clients connect to names, not addresses, so the only thing deciding whether traffic reaches the endpoint or the public front end is the answer a resolver gives for the service hostname. The public name follows a CNAME chain that redirects toward a privatelink-prefixed zone name, and that prefixed zone is the one you own. You create a Private DNS zone matching the privatelink name, the endpoint's private DNS zone group registers an A record mapping the resource to the endpoint's private IP, and you link the zone to every network that should resolve internally. Inside those linked networks the chain lands in your zone and returns the private address; outside them the same chain resolves to the public address. That split is the design. Because DNS is the deciding lever, an endpoint without its zone, link, and record is a private address nobody dials, which is why DNS is the linchpin rather than a finishing touch.

### Q: Should I use a private endpoint or a service endpoint?

Choose a private endpoint when you need a true private IP for the service, when on-premises or peered clients must reach it over the private path, or when policy requires public access to be disabled. Choose a service endpoint when Azure-resident workloads only need an optimized, subnet-scoped path to the service over the backbone and the public endpoint remaining reachable is acceptable. The deciding factor is whether you need a private address, not whether you want security, because both improve posture in different ways. A service endpoint changes who the service trusts by letting its firewall recognize your subnet over the backbone using the public IP, costs nothing, and helps only in-subnet sources. A private endpoint changes where the service lives by giving it a private address in your network, costs money per hour and per gigabyte, and extends private reach to on-premises and peered clients. Topology is the stronger guarantee because it does not depend on the public endpoint staying up.

### Q: How does cross-tenant Private Link approval work?

Every endpoint carries a connection state, and the producer who owns the target resource holds the approval right. When a consumer creates an endpoint to a resource they do not own, often in another subscription or tenant, the connection enters a Pending state and carries no traffic until the resource owner moves it to Approved. The owner can instead Reject it, which is terminal, or Disconnect it later to sever an approved connection. The consumer can attach a request message that the approver sees alongside the pending connection, which is how the two sides coordinate when they cannot see each other's environments. For first-party resources within a single ownership boundary the platform auto-approves, which is why the model is easy to forget until a cross-tenant case surfaces it. The connection state is also a diagnostic: an endpoint that stopped working with no DNS or routing change has often been disconnected from the resource side.

### Q: How does traffic flow over a private endpoint?

A client resolves the service name and, because a linked Private DNS zone holds the record, receives the endpoint's private IP. The operating system matches that address to a connected route inside the local virtual network, so no gateway or public hop is involved, and the packet travels to the network interface backing the endpoint. At the interface the platform forwards the traffic across the Azure backbone to the specific service instance the endpoint was created for, and the response returns by the same private route. From the application's view it simply connected to the service by name; from the network's view the traffic never touched a public IP and never left the routed private boundary until it crossed onto the managed backbone. Importantly, the endpoint is a destination for the client and an inbound termination for the service, not an initiator, so the service cannot use it to open connections back into arbitrary hosts on your network.

### Q: Do I need a separate private endpoint for each part of a storage account?

Yes, because each service facet of a multifaceted resource has its own group ID and its own hostname. A storage account exposes distinct group IDs for blob, file, queue, table, and other services, and an endpoint connects to exactly one of them. If your applications use both blob and file storage, you need two endpoints and two Private DNS zones, one per facet, each registering its own record. Creating a single endpoint and assuming it covers the whole account is a common error that produces a partial rollout, where one workload resolves privately and another still resolves publicly because it calls a facet the lone endpoint never fronted. Designing per facet from the start avoids that confusion, and it also controls cost, since an endpoint for a facet no application calls spends money to front a door nobody opens. Create endpoints only for the facets your workloads actually use.

### Q: Do network security group rules apply to private endpoint traffic?

It depends on a subnet-level policy setting. Historically, network security group rules did not affect traffic destined for a private endpoint, which surprised teams expecting their usual filtering to govern endpoint access. The platform now supports applying network security groups and user-defined routes to endpoint traffic when the subnet is configured to enforce network policies for private endpoints, controlled by a subnet property that toggles whether those rules take effect. The practical consequence is that a security group rule appearing to be ignored on endpoint traffic is usually a policy that was never enabled rather than a rule written incorrectly. If you intend to filter who can reach an endpoint with network security groups, confirm the subnet's private endpoint network policy is set to enforce them, otherwise the endpoint receives traffic regardless of the rules you wrote. The same policy governs whether user-defined routes apply, which matters when you want endpoint traffic to traverse an inspection appliance.

### Q: Can on-premises clients reach a resource through a private endpoint?

Yes, and this is one of the main reasons to choose a private endpoint over a service endpoint, which cannot offer it. Because the endpoint's address is an ordinary private IP in a subnet, any network that can route to that subnet and resolve the service name reaches the resource. For on-premises clients that means two pieces must be in place: a routed path into the Azure network, typically over a VPN or ExpressRoute gateway, and a DNS arrangement that lets the on-premises resolver follow the privatelink CNAME chain to the private answer. The supported pattern is a conditional forwarder that sends the relevant zones' queries to a resolver in Azure, often a DNS forwarder that consults the Azure-provided resolver, so on-premises queries traverse the same redirection in-Azure clients do. Simply copying an A record on-premises does not work, because it misses the CNAME chain and the platform's automatic record management.

### Q: Does a private endpoint secure the resource by itself?

No, and assuming so leaves gaps. A private endpoint removes the need for the resource to be reachable over the public internet, which shrinks the external attack surface to nothing once public access is disabled, because an attacker who cannot route to or resolve a private address cannot reach the resource from outside. What the endpoint does not do is authenticate or authorize callers. Any host that can route to the endpoint's address and resolve the name can attempt a connection, so the resource still needs its own authentication and authorization, network security groups limiting which sources may reach the endpoint where subnet policy enforces them, and network segmentation reflecting who should reach what. The endpoint changes the topology so that access requires being on the network; it does not decide who on the network is allowed in. Sound designs layer the endpoint behind these controls rather than leaning on a private address as a complete safeguard.

### Q: What is the private DNS zone group and why does it matter?

The private DNS zone group is an object associated with the endpoint that automatically registers and maintains the A record mapping the resource to the endpoint's private IP in the Private DNS zone you specify. It matters because it is the difference between resolution that stays correct on its own and resolution that drifts. Without the zone group, the only way to get a record is to type one by hand, and a hand-entered record becomes stale the moment the endpoint's address changes on a recreate, producing a private answer that fails to connect because it points at an address nothing answers on. Attaching the zone group ties the record's lifecycle to the endpoint's, so the record is always present and accurate. In production, automating the zone group through infrastructure as code or Azure Policy is the most reliable way to enforce the linchpin rule, because it makes the half-built state, an endpoint without DNS, impossible to leave lying around.

### Q: In what order should I disable public access on a resource?

Disable it last, after the endpoint and its DNS are built and verified. The correct sequence is to create the endpoint, wire and link the Private DNS zone with its zone group, confirm from a representative client that the service name resolves to the private address and that a connection succeeds over the private path, and only then disable public network access. Done in that order, closing the public door is a non-event because nothing is depending on the public path anymore. Reversing the order, disabling public access before the DNS chain resolves, produces an outage during the very change meant to harden the system, and teams under pressure then sometimes re-enable public access to restore service, quietly reintroducing the exposure they were removing. The principle is that the private path is not real until resolution returns the private address, so you never close the public path until the private one is proven.

### Q: How do I control who can connect to a Private Link service I publish?

A Private Link service offers a visibility setting that determines which subscriptions can discover and request a connection, and an auto-approval list that lets named subscriptions connect without a manual approval step. The combination gives a spectrum of openness. An invite-only service restricts visibility to a known set of subscriptions and auto-approves them, so trusted consumers connect without friction and nobody else can even request. A published offering makes the alias discoverable and relies on manual approval to vet each requester, suiting a service offered broadly where each connection should be reviewed using the request message the consumer supplies. Decide early which model fits, because an invite-only service runs itself once the auto-approval list is set, while a published offering needs someone or an automated policy watching the pending queue. Getting it wrong in the open direction floods the queue; getting it wrong closed means legitimate consumers cannot find the alias.

### Q: Why does my private endpoint resolve correctly but still fail to connect?

A private answer exonerates the DNS rows, so the cause is elsewhere, and there are three usual suspects. First, the connection state: a Pending, Rejected, or Disconnected connection carries no traffic no matter how perfect resolution is, so check the endpoint's state before anything else, especially for cross-tenant or policy-managed resources. Second, a network control in the path: a network security group denying the flow, or a route sending endpoint traffic into an appliance that black-holes it, where the subnet's private endpoint network policy determines whether those rules even apply. Third, a stale record: if someone typed the A record by hand instead of attaching a zone group and the endpoint's address later changed, the private answer points at an address nothing answers on. Use Network Watcher's connection troubleshoot and IP flow verify to localize the failure to the exact hop, having first confirmed the connection state is Approved.

### Q: What is the difference between a private endpoint and virtual network integration?

They solve opposite directions of the same problem and are easy to confuse, especially for App Service and Functions. A private endpoint is about inbound reach: it gives a service a private address so clients in your network can reach it privately. Virtual network integration is about outbound reach: it lets a web app or function send its outbound calls into your virtual network so the app can reach private resources, such as a database behind its own endpoint. If you want your app reachable only from inside the network, add a private endpoint to the app. If you want the app to reach a private database, add virtual network integration to the app and a private endpoint to the database. The two are often used together because they cover the two directions. The test that prevents the mix-up is to ask whether you need inbound reach to the resource or outbound reach from it, and the right feature follows.

### Q: How do I migrate from service endpoints to private endpoints safely?

Build the private path beside the existing one before removing anything. Create the endpoint and its full DNS chain while the service endpoint and public path still function, so nothing breaks during construction. Verify that clients in the target networks resolve to the private address and connect over it. Only once the private path is proven do you tighten the resource firewall, moving from selected networks that trusted the service-endpoint subnet to disabling public access entirely, which retires the service-endpoint path. Because the private path was built and verified first, the moment you close the public door no client depends on it, and the migration completes without a connectivity gap. The trap is reversing the order, removing the old path before the new one resolves and connects, which causes an outage during a hardening change. The model makes the order obvious: the private path is not real until resolution returns the private address.

### Q: Why does endpoint traffic sometimes bypass my network virtual appliance?

Because the platform installs a highly specific system route for the endpoint's private IP, effectively a host route, that can take precedence over a broad user-defined route pointing all traffic at an inspection appliance. The result is that traffic to the endpoint goes directly to it rather than through the appliance you intended to traverse, which surprises teams running forced tunneling or centralized inspection. Whether you can bring endpoint traffic back under your route table depends on the subnet's private endpoint network policy: enabling enforcement of user-defined routes for endpoints lets your routes apply to endpoint traffic, so a route to the appliance is honored. Teams that require endpoint traffic be inspected must account for this explicitly rather than assuming a default route captures it. Use Network Watcher's next hop to confirm where endpoint traffic is actually heading, and set the subnet policy deliberately so the routing matches your inspection requirements.
