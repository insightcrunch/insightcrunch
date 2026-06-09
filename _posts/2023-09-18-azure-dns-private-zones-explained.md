---
layout: post
title: "Azure DNS and Private DNS Zones Explained"
page_title: "Azure DNS and Private DNS Zones Explained: VNet Links, Auto-Registration, the 168.63.129.16 Resolver, and Hybrid Conditional Forwarding"
date: 2023-09-18
categories: ["Technology"]
tags: ["Azure", "Azure DNS", "Private DNS", "Networking", "VNet", "Cloud Computing"]
excerpt: "Azure Private DNS zones resolve only for linked VNets. Learn VNet links, auto-registration, the Azure resolver, and hybrid DNS forwarding in depth here."
image: "/assets/images/blog/blog-71.webp"
reading_time: 62
author: "kevin-reeves"
last_updated: 2023-09-18
lang: en
---
A name that resolves perfectly from one virtual machine and returns nothing from the machine beside it is the single most common Azure DNS puzzle engineers carry into a support ticket. The record exists. The spelling is right. The application is healthy. Yet `nslookup app1.contoso.internal` answers on the VM in `vnet-prod` and times out on the VM in `vnet-dev`, and the team starts deleting and recreating records that were never broken. The fault is almost never the record. It is the link. An Azure Private DNS zone resolves only for the virtual networks it is explicitly linked to, and the moment you internalize that one rule, most private name resolution mysteries collapse into a five second check.

This article builds the full model of how name resolution works across Azure DNS, the public zones that serve the internet, the private zones that serve your virtual networks, the platform resolver that sits behind both, and the hybrid forwarding that stitches Azure resolution together with on-premises resolution. The goal is not to hand you a recipe to paste. It is to leave you able to design name resolution on purpose, to predict which answer a query will return before you run it, and to look at a resolution failure and know within seconds whether you are chasing a record problem, a link problem, or a forwarder problem.

![Azure DNS and Private DNS Zones explained with VNet links, auto-registration, and the 168.63.129.16 resolver - Insight Crunch](/assets/images/blog/blog-71.webp)

The reason private DNS confuses people is that it behaves nothing like the public DNS they already understand. Public DNS is global by design. You register a domain, you delegate it to a set of name servers, and from that moment any resolver anywhere on the planet can walk the delegation chain and find your records. There is no concept of scope. A record is either published or it is not. Private DNS inverts that assumption completely. A Private DNS zone is not published anywhere. It has no delegation, no public name servers, and no path for an outside resolver to find it. It exists only inside the boundary you draw with virtual network links, and outside that boundary it may as well not exist. Engineers who carry the public model into the private world expect a private record to resolve everywhere, and they spend hours hunting for a corruption that is really just an unlinked network.

## The mental model: two zone types, one resolver, and a scope boundary

Hold three objects in your head and the rest of Azure DNS follows from them. The first object is the public zone, a container of records for a domain that the internet can reach. The second object is the private zone, a container of records that only linked virtual networks can reach. The third object is the platform resolver at the address 168.63.129.16, a virtual public IP that every virtual network can talk to and that knows how to answer for Azure public names, for the private zones linked to the asking network, and for the internal machine names Azure registers automatically. Public and private zones are siblings, not parent and child. They can even share the same domain name, and when they do, the answer a client receives depends entirely on where the client sits. That last property, the same name returning different addresses in different places, is split-horizon resolution, and it is the engine behind private endpoints. We will get there, but the boundary concept comes first because everything else is built on it.

A virtual network link is the object that draws the boundary. When you link a private zone to a virtual network, you grant the machines in that network the ability to resolve names in the zone. Remove the link and the names vanish for that network, even though every record in the zone is still perfectly intact. The link is not a copy of the zone and it is not a forwarder. It is an authorization that says this network may see this namespace. A single zone can be linked to many networks at once, which is how a shared corporate suffix like `contoso.internal` resolves identically across a fleet of networks. A single network can be linked to many zones at once, which is how one workload network can see both your internal application suffix and the `privatelink` subdomains that back its private endpoints. The relationship is many to many, and the link is the join.

### How do Azure public and private DNS zones differ in practice?

A public zone is delegated and globally resolvable: you point your registrar at the Azure name servers and anyone can query it. A private zone has no delegation and no public name servers; it answers only for virtual networks you link, which makes scope, not publication, its defining property.

The practical consequences of that difference are worth making concrete because they drive real design decisions. A public zone needs a delegation step. After you create the zone in Azure DNS, the zone is assigned a set of Azure name servers, and your domain does not actually resolve through Azure until you update the name server records at your domain registrar to point at those Azure name servers. Until that delegation is in place, the zone exists but the world still resolves the domain through wherever it was delegated before. A private zone has no such step and no such name servers, because there is no public hierarchy for it to join. You create it, you link networks to it, and resolution works immediately inside those networks with no registrar involved.

The second consequence is reachability for troubleshooting. When a public zone misbehaves you can query it from anywhere, including your laptop, using the Azure name servers directly, which makes diagnosis straightforward. A private zone can only be tested from inside a linked network, so the first move when a private name fails is to get a shell on a machine that should be able to resolve it and run the query there, not from your workstation. People waste real time trying to `nslookup` a private name from a corporate laptop that has no path to the zone, conclude the zone is broken, and start changing things that were correct.

The third consequence is the record model, which is nearly identical across both zone types and is the part that feels familiar. Both public and private zones organize records into record sets. A record set is the collection of records that share a name and a type within the zone. The apex of `contoso.com` might have an A record set holding one or more IPv4 addresses, an AAAA record set holding IPv6 addresses, an MX record set for mail, a TXT record set for verification strings, and so on. You do not add a record in isolation; you add a record to the set identified by its name and type, and the set carries a single time to live that governs how long resolvers may cache every record in it. Private zones support the common record types you expect, including A, AAAA, CNAME, MX, PTR, SRV, and TXT, and every zone carries an automatically created start of authority record that defines the zone parameters. The difference that matters for design is not the record syntax. It is who can see the record once it is there.

## The InsightCrunch DNS resolution model

The findable artifact for this article is a single reference that maps every moving part of Azure name resolution to what it does, where it applies, and the one fact about it that engineers most often get wrong. Keep this table next to you while you design or debug, and read it as a decision aid rather than a glossary. The named claim it encodes is the rule the whole article defends, stated plainly below the table.

| Component | What it is | Scope of effect | The fact engineers miss |
| --- | --- | --- | --- |
| Public DNS zone | Records for a domain the internet resolves | Global, after registrar delegation | The zone does nothing until name servers are delegated at the registrar |
| Private DNS zone | Records only linked networks resolve | Exactly the networks linked to it | Unlinked networks cannot see the zone even though the records exist |
| Record set | Records sharing a name and type, with one TTL | Within its zone | The TTL is per set, so a stale cached answer is a set property, not a single record property |
| Virtual network link | Authorization tying a zone to a network | The one network it names | The link grants visibility; it is not a copy or a forwarder |
| Auto-registration | Per-link option that writes VM records into the zone | Virtual machines in the registration network | It registers virtual machine network interfaces only, not other resource types, and a network can register into one zone |
| The 168.63.129.16 resolver | The platform DNS service every network can reach | Reachable from inside any virtual network | On-premises clients cannot use it directly; they need a forwarder that lives in Azure |
| VNet DNS setting | Default Azure-provided or custom server list | The networks set to it | Custom servers stop resolving private zones unless they forward to 168.63.129.16 |
| Conditional forwarder | A rule sending one domain to a chosen resolver | The resolver running the rule | Hybrid resolution is two forwarders pointing opposite ways, not one |
| Split-horizon | Same name, different answer by location | Anywhere a private zone shadows a public name | The private zone overrides the public answer only inside linked networks |

The link-scopes-the-zone rule states the principle the table circles: a Private DNS zone resolves only for the virtual networks it is linked to, so a name that fails to resolve privately is almost always an unlinked zone or a missing forwarder, not a record problem. Internalize that and your diagnostic order changes. Before you touch a single record, you check whether the asking network is linked to the zone and whether the asking client is actually pointed at a resolver that can reach the zone. Nine times out of ten the answer is in one of those two checks, and the record was never the issue.

If you want the broader routing and filtering context that this resolution layer sits inside, the [Azure networking fundamentals walkthrough for engineers](/2023/08/28/azure-networking-fundamentals/) lays out how a packet travels through a virtual network before name resolution even enters the picture, and it is worth reading alongside this piece so the DNS model has somewhere to attach.

## How the private zone and the VNet link actually work

A Private DNS zone is created as a resource in a resource group, and at creation it is inert. It holds an automatically generated start of authority record and nothing else useful, because it is linked to no network and registers no machine. Creation and linking are deliberately separate steps, and understanding why clarifies the whole model: the zone is the namespace and the data, while the link is the grant of access. You can build a zone in one subscription, populate it with records, and then link it to networks that live in entirely different subscriptions, which is exactly how a central platform team publishes a shared resolution namespace to workload teams without handing them ownership of the records.

Creating a zone and linking a network with the Azure CLI takes two commands. The first creates the namespace, the second draws the boundary to a network and decides whether that network registers its machines automatically.

```bash
# Create the private zone (the namespace and the record data live here)
az network private-dns zone create \
  --resource-group rg-dns \
  --name contoso.internal

# Link a virtual network to the zone, with auto-registration enabled
az network private-dns link vnet create \
  --resource-group rg-dns \
  --zone-name contoso.internal \
  --name link-vnet-prod \
  --virtual-network vnet-prod \
  --registration-enabled true
```

The `--registration-enabled` flag is the hinge of the whole link. When it is `true`, the link is a registration link, and Azure writes an A record into the zone for every virtual machine network interface in the linked network, keeping those records current as machines come and go. When it is `false`, the link is a resolution link, which grants the network the ability to resolve names in the zone but writes nothing into it. The distinction maps cleanly onto two jobs. Registration links automate the internal naming of your own machines. Resolution links give a network read access to a namespace someone else populates, which is the right setting for `privatelink` zones backing private endpoints, where the records come from the endpoint and not from any virtual machine.

### How do Private DNS zones and VNet links work together?

The zone holds the records and the link authorizes a network to resolve them. A registration link also writes virtual machine A records into the zone automatically. A resolution link only grants visibility. Linking is many to many: one zone serves many networks, and one network sees many zones at once.

A few link constraints shape real designs and are worth stating exactly, with the caveat that the numeric limits move over time and should be confirmed against the current published Azure limits before you bet a design on them. A single zone can carry a large number of resolution links and a smaller number of registration links; the registration ceiling is the tighter of the two, so do not plan to auto-register thousands of machines into one zone across hundreds of networks without checking the current figure. More fundamentally, a virtual network can be a registration network for only one private zone at a time. That single-registration rule trips teams who try to auto-register the same machines into two different internal suffixes; the second registration link will not behave as a second source of truth, and you should treat one zone as the authoritative registration target per network and resolve any additional suffixes through resolution links or records you manage yourself.

To see what auto-registration produced, list the A record sets in the zone after a machine has booted in the registration network. The hostname of the virtual machine becomes the record name, and the address is the private IP of its primary network interface.

```bash
# List the A record sets, including the ones auto-registration created
az network private-dns record-set a list \
  --resource-group rg-dns \
  --zone-name contoso.internal \
  --output table
```

Records you add yourself sit alongside the auto-registered ones, and you add them to a named set rather than as free-floating entries. Adding a manual A record for an application alias looks like this, and the same pattern with a different record-set type covers CNAME, TXT, and the rest.

```bash
# Add a manual A record to the set named "app1"
az network private-dns record-set a add-record \
  --resource-group rg-dns \
  --zone-name contoso.internal \
  --record-set-name app1 \
  --ipv4-address 10.20.0.10
```

One subtlety catches people who mix manual and automatic records. Auto-registration owns the records it creates, and it will overwrite or remove them as the underlying machines change, so a manual A record using a hostname that collides with an auto-registered machine name is asking for the platform to win the conflict at an inconvenient time. Keep manual aliases in their own naming space, point them at machines through CNAME records to the auto-registered names where you can, and let auto-registration remain the single writer for machine hostnames. That discipline keeps the zone predictable and stops the maddening case where a record you added by hand quietly disappears because the registration system reconciled it away.

### What is auto-registration and what exactly does it register?

Auto-registration is a per-link option that makes Azure write and maintain A records for the virtual machines in the registration network, keyed on each machine hostname and pointing at its primary private IP. It registers virtual machine interfaces only. It does not register private endpoints, load balancers, or other resource types, which must be recorded another way.

The records auto-registration does not create are the ones that cause the most confusion, so it pays to name them. A private endpoint does not auto-register into your internal zone; its DNS lives in a `privatelink` zone and is wired up through the endpoint's own configuration. A load balancer front end does not auto-register. A platform service reached over a service or private endpoint does not auto-register. App Service and other PaaS resources do not auto-register. If you expect a name to exist because the resource exists, and the resource is anything other than a plain virtual machine, you almost certainly need to create that record deliberately or rely on the service's own DNS integration. The auto-registration system has exactly one job, machine hostnames in the registration network, and it does that job and nothing else.

## The Azure-provided resolver at 168.63.129.16

Every virtual network has access to a platform resolver reachable at the address 168.63.129.16. This is a virtual public IP that Azure uses as a communication channel for several platform functions, and DNS is the one that matters here. It is special in two ways. It is the same address in every region and every network, so the value never changes and you can hardcode it in a forwarder configuration with confidence. And it is reachable only from inside a virtual network or from a machine connected to one; it is not a public resolver you can query from the open internet, and it is not directly reachable from on-premises across a tunnel in the way a normal address would be. That second property is the source of half the hybrid DNS pain engineers hit, and we will return to it.

When a virtual network uses the default DNS setting, the machines in it are handed 168.63.129.16 as their resolver, and that resolver answers for three things at once. It answers for Azure public DNS, so external names resolve normally. It answers for the private zones linked to the asking network, so a name in `contoso.internal` resolves if and only if the asking machine sits in a network linked to that zone. And it answers for the internal naming Azure maintains, including the auto-registered machine records. The resolver is the point where the link boundary is actually enforced. Two machines in two different networks ask the same resolver address the same question and get different answers, because the resolver checks which network the query came from and consults only the zones linked to that network. The address is identical; the view is per network.

### What is the 168.63.129.16 address and why does it never change?

It is the Azure platform virtual IP that provides the default DNS resolver, plus other host communication functions, to resources inside a virtual network. It is a fixed, region-independent address reachable only from within a VNet, which is why forwarder configurations target it directly and why on-premises clients cannot query it without a relay in Azure.

The behavior changes the moment you move a network off the default DNS setting. A virtual network can be told to use custom DNS servers instead of the Azure-provided default, which you do when you run your own DNS infrastructure, domain controllers, or a centralized resolver. When you set custom servers, every machine in the network receives those server addresses rather than 168.63.129.16, and here is the trap that produces a flood of tickets: a custom DNS server does not know about your Azure private zones. The private zones are visible only through the platform resolver, so a custom server that does not forward to 168.63.129.16 will resolve everything it is configured for and fail every private zone lookup, because it is simply not asking the one resolver that holds those answers. The fix is a forwarder rule on the custom server that sends queries for the private domains, or all unmatched queries, to 168.63.129.16.

Setting a virtual network to custom DNS servers is one command, and the order of operations matters. Apply the setting, then reboot or renew the lease on the machines so they pick up the new resolver list, because a running machine keeps its old resolver until its lease renews.

```bash
# Point a virtual network at custom DNS servers
az network vnet update \
  --resource-group rg-net \
  --name vnet-hub \
  --dns-servers 10.10.0.4 10.10.0.5
```

On the custom DNS server itself, a conditional forwarder for the Azure private suffix completes the chain. The exact syntax depends on the DNS software, but the intent is constant: send queries for the private zone domains, and typically the `privatelink` subdomains, to 168.63.129.16, and let the platform resolver answer them. Without that rule the custom server is an island that cannot see the private namespace, and the symptom is the classic one where public names resolve and private names do not. If you are chasing exactly that symptom right now and want the failure-mode treatment rather than the model, the focused walkthrough on [why Azure DNS resolution fails and how to confirm the cause](/2022/12/26/fix-azure-dns-resolution/) covers the diagnostic commands and the specific fixes for each cause in depth.

## Hybrid resolution: conditional forwarding in both directions

The hardest part of Azure DNS is not Azure DNS. It is the seam where Azure resolution meets on-premises resolution, because the two systems cannot see each other by default and neither one is wrong. On-premises clients query on-premises DNS servers, which know about on-premises domains and have no idea your Azure private zones exist. Azure clients query the platform resolver, which knows about Azure private zones and has no idea your on-premises domains exist. Connecting a VPN gateway or an ExpressRoute circuit gives the two sides network reachability, but reachability is not resolution. A VPN does not teach on-premises DNS about `contoso.internal`, and it does not teach the Azure resolver about `corp.contoso.com`. You have to build the resolution path explicitly, and it is always two forwarders pointing in opposite directions, never one.

The on-premises to Azure direction needs a resolver inside Azure that on-premises DNS can forward to, because on-premises servers cannot query 168.63.129.16 directly. Historically engineers solved this by running a small DNS forwarder virtual machine in a hub network: the on-premises DNS server conditionally forwards the Azure private domains to that virtual machine, and the virtual machine forwards them on to 168.63.129.16, which can answer because the query now originates inside a linked network. The virtual machine is a relay whose only purpose is to give on-premises queries a place inside Azure from which the platform resolver is reachable. It works, but it is a machine you patch, scale, and monitor, and a single forwarder is a single point of failure for all hybrid resolution.

The Azure to on-premises direction is the mirror image. When an Azure machine needs to resolve an on-premises name, the Azure resolver has to be told to send those queries back across the link to an on-premises DNS server. With the older forwarder-virtual-machine pattern, you point the network at the forwarder virtual machine as its custom DNS server and configure that machine to forward on-premises domains to on-premises DNS and everything else to 168.63.129.16. The forwarder becomes the hinge in both directions, which is convenient and also why its availability matters so much.

### How does conditional forwarding make hybrid DNS work?

Conditional forwarding routes queries for a named domain to a chosen resolver instead of the default one. Hybrid DNS needs two such rules pointing opposite ways: on-premises servers forward Azure private domains to a resolver inside Azure, and Azure forwards on-premises domains back to on-premises servers, so each side resolves the other through the seam.

The managed answer to all of this is the Azure DNS Private Resolver, a platform service that removes the forwarder virtual machine from the picture. It provides inbound endpoints, which are addresses inside your virtual network that on-premises DNS can forward to and that resolve Azure private zones directly, replacing the relay virtual machine for the on-premises to Azure direction. It provides outbound endpoints and DNS forwarding rulesets, which let Azure conditionally forward named domains to on-premises or other DNS servers without you running a forwarding machine for the Azure to on-premises direction. The resolver is a managed, scaled, zone-aware service, and it is the current recommended way to build hybrid resolution because it turns two fragile virtual machines into two managed endpoints with rules attached. As with every Azure capability, confirm the regions where the resolver is available and its current limits against the official source before you design around it, since availability expands over time.

A minimal DNS Private Resolver build provisions the resolver against a virtual network, then adds an inbound endpoint in a dedicated subnet for on-premises queries and an outbound endpoint with a forwarding ruleset for Azure-originated queries to on-premises domains.

```bash
# Create the DNS Private Resolver bound to a virtual network
az dns-resolver create \
  --resource-group rg-dns \
  --name resolver-hub \
  --location eastus \
  --id "/subscriptions/<sub-id>/resourceGroups/rg-net/providers/Microsoft.Network/virtualNetworks/vnet-hub"

# Add an inbound endpoint in a delegated subnet so on-premises DNS can forward to Azure
az dns-resolver inbound-endpoint create \
  --resource-group rg-dns \
  --dns-resolver-name resolver-hub \
  --name inbound-from-onprem \
  --location eastus \
  --ip-configurations '[{"privateIpAllocationMethod":"Dynamic","id":"/subscriptions/<sub-id>/resourceGroups/rg-net/providers/Microsoft.Network/virtualNetworks/vnet-hub/subnets/snet-inbound"}]'
```

Once the inbound endpoint exists, you point your on-premises DNS server's conditional forwarder for the Azure private domains at the inbound endpoint's private IP, and on-premises clients begin resolving Azure private names without any forwarder virtual machine in between. The outbound endpoint plus a forwarding ruleset handles the reverse, sending the Azure machines' queries for on-premises domains to your on-premises servers. Two endpoints, two sets of rules, opposite directions, and the seam is bridged with managed infrastructure rather than machines you babysit.

The piece that ties hybrid resolution back to the private endpoint world is that the same inbound endpoint and the same linked private zones are what make an on-premises client able to reach an Azure storage account or database over a private endpoint by its normal name. The private endpoint's address lives in a `privatelink` zone, the zone is linked to the hub network the resolver sits in, and the on-premises forwarder sends the `privatelink` queries to the inbound endpoint, which resolves them to the private IP. The whole hybrid private-endpoint story is one consistent application of the model: records in a zone, a link that scopes the zone, a resolver that enforces the link, and a forwarder that lets a client outside the network reach the resolver. If you want the endpoint mechanics in their own right, the deep treatment of [how Azure Private Link projects a service into your VNet](/2023/09/11/azure-private-link-deep-dive/) follows the same thread from the endpoint side.

## Split-horizon: the same name, two answers

Split-horizon resolution is the property that one name returns one address to a client in one place and a different address to a client in another place. It sounds like a corner case and it is actually the foundation of how private connectivity to Azure platform services works, so it deserves a clean explanation rather than a footnote. The mechanism is straightforward once you accept that public and private zones are independent siblings that can share a name. If a public zone for `contoso.com` holds an A record pointing at a public address, and a private zone for the same `contoso.com` holds an A record for the same name pointing at a private address, then a client on the internet resolving through public DNS gets the public address, and a client inside a network linked to the private zone gets the private address. Neither answer is wrong. They are two zones, and the asker's location selects which one applies.

The private zone shadows the public one, but only inside linked networks and only for the names the private zone actually holds. A linked network resolving a name that exists in both zones sees the private answer because the platform resolver consults the linked private zone first. A name that exists only in the public zone still resolves to the public answer even from inside the linked network, because the private zone has nothing to say about it. This is why a private zone does not have to be a full mirror of a public domain. It only needs the handful of records you want to override locally, and everything else falls through to public resolution.

### How does split-horizon DNS behave inside and outside a linked network?

Inside a linked network, a private zone overrides the public answer for any name it holds, so the client gets the private address. Outside that network, or for names the private zone does not hold, public resolution applies and the client gets the public address. The same query, asked from two locations, returns two different records.

Private endpoints are split-horizon applied to Azure platform services, and walking the resolution chain makes the abstraction concrete. Suppose you create a private endpoint for a storage account named `acmestore`. The public name is `acmestore.blob.core.windows.net`, and that public name resolves, through a CNAME, to `acmestore.privatelink.blob.core.windows.net`. On the public internet that `privatelink` name resolves to the storage account's public address, because nothing private is in play. Inside a network linked to a private zone named `privatelink.blob.core.windows.net`, the platform resolver finds an A record for `acmestore` in that zone pointing at the private endpoint's private IP, and so the same chain that started at the public name ends at the private address. The application never changes its connection string. It always uses `acmestore.blob.core.windows.net`. The split-horizon resolution silently steers that name to the private address inside the network and to the public address everywhere else.

This is exactly why the private zone link is the most common failure point for private endpoints, and why the symptom is so counterintuitive. The endpoint is created, the network rules are correct, the storage firewall is set to deny public access, and the application still tries to reach the public address and fails, because the `privatelink` zone was never linked to the application's network. The records are not the problem. The records are perfect. The network was never authorized to see them, so the CNAME chain resolves to the public address, the public path is blocked, and the connection dies. The fix is one link, not a record change. The dedicated diagnosis of [why a private endpoint refuses to resolve to its private IP](/2022/11/28/fix-private-endpoint-dns/) walks the entire CNAME chain with the confirming commands at each hop, which is the fastest way to localize exactly where a real endpoint resolution breaks.

Wiring the `privatelink` zone into a private endpoint is done with a private DNS zone group on the endpoint, which is the piece that creates and maintains the A record for you so you do not manage endpoint addresses by hand. A compact Bicep fragment shows the shape: a private zone, a resolution link to the workload network, and a zone group on the endpoint that binds them.

```bicep
resource privateZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.blob.core.windows.net'
  location: 'global'
}

resource zoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: privateZone
  name: 'link-vnet-workload'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: workloadVnetId
    }
  }
}

resource endpointZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-04-01' = {
  parent: storagePrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'blobConfig'
        properties: {
          privateDnsZoneId: privateZone.id
        }
      }
    ]
  }
}
```

Note the `registrationEnabled: false` on the link. A `privatelink` zone is never a registration target, because its records come from private endpoints through the zone group, not from virtual machines. Setting it to a resolution link is the correct and only sensible choice, and getting that flag wrong is one of the quieter mistakes that leaves a zone technically linked but configured against its purpose.

## Resolution precedence and the fall-through path

A question that decides real designs is what the platform resolver does when a name could be answered from more than one place, and the answer follows directly from the scope model. When a client asks for a name, the resolver consults the private zones linked to the asking network first. If a linked zone holds a matching record, that record wins and the resolver returns it without ever consulting public DNS. If no linked zone holds the name, the query falls through to public resolution, and the resolver returns the public answer. This ordering, private linked zones first and public second, is what makes split-horizon override work, and it is also what lets a sparse private zone coexist with a full public domain. The private zone does not have to be complete. It only has to hold the names you want to capture locally, and every other name flows past it to the public answer.

The behavior when two linked zones could both match deserves care, because it is a design smell rather than a feature to rely on. If a network is linked to two private zones whose names overlap, the resolution becomes ambiguous in a way you do not want to depend on, and the right move is to design the namespace so a given name lives in exactly one linked zone per network. The clean pattern is one internal suffix that owns your machine and application names, plus the set of `privatelink` zones that each own a distinct platform domain, with no overlap among them. Overlap usually creeps in when teams link a network to two zones that both claim the same suffix during a migration, and the symptom is intermittent or surprising answers that depend on internals you should not be building on.

Negative answers cache too, which trips people who fix a record and still see failures. When a resolver asks for a name and gets back a definitive no-such-name response, that negative result is cacheable for a period governed by the zone's start of authority parameters, so a client that queried a name before you created its record can keep seeing the failure until the negative cache ages out. The practical consequence is that creating a record is not always instantly visible to a client that recently failed to resolve it, and the fix is patience or a cache flush rather than recreating a record that is already correct. Reading the failure as a caching artifact rather than a missing record saves you from changing things that were never wrong.

### How does the resolver choose between a private zone and the public answer?

The resolver checks the private zones linked to the asking network first and returns a match if one exists, falling through to public resolution only when no linked zone holds the name. That ordering is why a sparse private zone can override specific names while everything else resolves publicly, and why the asking network's link set decides the outcome.

## Reverse lookups and PTR records in private zones

Forward resolution, turning a name into an address, is the path almost everyone thinks about, but reverse resolution, turning an address back into a name, matters more often than teams expect, and Azure Private DNS supports it through reverse lookup zones. A reverse zone is a private zone whose name follows the `in-addr.arpa` convention that maps an address range to a namespace, and it holds PTR records that point an address back at a hostname. You create the reverse zone for the address space your network uses, link it to the networks that should resolve reverse queries, and populate PTR records either by hand or, where the platform supports it, alongside the forward auto-registration so a machine's address resolves back to its name.

Reverse resolution earns its keep in logging, security tooling, and any system that records connections by address and wants to present them by name. A flow log or an audit trail full of bare addresses is far harder to read than one annotated with hostnames, and a working reverse zone is what lets the tooling perform that annotation. It also matters for a handful of protocols and services that perform a reverse lookup as part of their handshake and behave oddly when the reverse path is missing. The design guidance is to treat the reverse zone as a deliberate companion to the forward zone for any address space where you care about name-annotated diagnostics, link it to the same networks, and keep its PTR records aligned with the forward A records so the two directions agree. A forward record without its reverse partner is a common and quiet gap that surfaces only when a tool you did not write performs a reverse query and gets nothing back.

## A worked end-to-end resolution: on-premises client to an Azure SQL private endpoint

Tracing one realistic query through the entire system turns the model from a set of rules into something you can picture, so consider a concrete case: an application server in your on-premises datacenter needs to reach an Azure SQL database over a private endpoint, using the database's normal name. The on-premises server resolves `acme-sql.database.windows.net`, and we will follow that query from the first hop to the private address it must reach, naming the component responsible at each step.

The first hop is the on-premises DNS server. It receives the query for `acme-sql.database.windows.net` and, because you have configured a conditional forwarder for the `database.windows.net` and `privatelink.database.windows.net` domains, it does not try to resolve the name itself. It forwards the query to the address you configured for the forwarder, which is the private IP of a DNS Private Resolver inbound endpoint sitting in your hub network in Azure. This forwarding rule is the on-premises to Azure half of hybrid resolution, and without it the on-premises server would resolve the public name to the public address and the private endpoint would go unused.

```bash
# On the on-premises DNS server: forward the Azure SQL domains to the
# DNS Private Resolver inbound endpoint's private IP (example: 10.10.4.4)
# The exact syntax depends on the on-premises DNS software; the intent is constant:
#   database.windows.net          -> 10.10.4.4
#   privatelink.database.windows.net -> 10.10.4.4
```

The second hop is the inbound endpoint. It receives the forwarded query from inside the hub network, which means the query now originates from a network in Azure, and it resolves the name against the private zones linked to that network. The public name `acme-sql.database.windows.net` resolves through a CNAME to `acme-sql.privatelink.database.windows.net`, and because the hub network is linked to a private zone named `privatelink.database.windows.net`, the resolver finds an A record for `acme-sql` in that zone. That A record was created and is maintained by the private endpoint's zone group, and it points at the private IP the endpoint exposes inside the network.

The third hop is the answer flowing back. The inbound endpoint returns the private IP to the on-premises DNS server, which returns it to the application server, which opens its database connection to the private address across the VPN or ExpressRoute circuit. The application never knew any of this happened. It asked for the database's normal name and received a private address, and the entire chain, the conditional forwarder, the inbound endpoint, the linked `privatelink` zone, the endpoint's A record, and the platform resolution behind it, executed silently. Every component we built earlier appears in this one trace, which is why understanding the model end to end pays off: when any single hop is misconfigured, you know exactly which link in the chain to inspect rather than guessing.

The failure version of this trace is instructive. If the `privatelink.database.windows.net` zone is not linked to the hub network, the inbound endpoint resolves the `privatelink` name to the public address, the on-premises server connects to the public endpoint, and the connection fails if the database's public access is disabled, with an error that looks like a firewall or connectivity problem rather than a DNS one. The fault is one missing link, and the model tells you to check the link before you touch anything in the database or the network security rules.

## The privatelink zone names that back common Azure services

Private endpoints for different Azure services use different `privatelink` zone names, and getting the zone name exactly right is a precondition for resolution working, because the endpoint's CNAME chain targets a specific `privatelink` subdomain and only the matching zone will hold the record. A short reference of well-known examples grounds the pattern, with the firm caveat that the authoritative and complete list is published by Microsoft and changes as services are added, so confirm any name you are not certain of against the current official source rather than trusting memory.

| Azure service (example) | Public domain pattern | Private DNS zone name to create and link |
| --- | --- | --- |
| Blob storage | blob.core.windows.net | privatelink.blob.core.windows.net |
| Azure SQL Database | database.windows.net | privatelink.database.windows.net |
| Key Vault | vaultcore.azure.net | privatelink.vaultcore.azure.net |
| App Service | azurewebsites.net | privatelink.azurewebsites.net |
| Cosmos DB (SQL API) | documents.azure.com | privatelink.documents.azure.com |

The pattern is consistent: the `privatelink` zone name is the service's public domain with a `privatelink` label prepended, and the endpoint's zone group binds the endpoint to that zone so the A record lands in the right place. The two mistakes this reference prevents are creating a zone with a near-miss name that the CNAME chain never targets, and linking the right zone to the wrong network. Both leave the endpoint unreachable by name while everything else looks correct, and both are caught instantly if you confirm the exact zone name against the service's public domain and verify the zone is linked to the consuming network. For the deeper treatment of how the endpoint and its CNAME chain are constructed in the first place, the walkthrough of [how Azure Private Link projects a service into your VNet](/2023/09/11/azure-private-link-deep-dive/) covers the endpoint side that produces these names.

## Migrating from forwarder virtual machines to the DNS Private Resolver

Many environments still run the older pattern of forwarder virtual machines, and migrating to the DNS Private Resolver is a common project worth doing carefully, because DNS is exactly the layer where a sloppy cutover causes a wide outage. The migration replaces two fragile machines with two managed endpoints, but the cutover has to keep resolution working at every moment, so it is done by adding the new path, shifting traffic to it, and only then retiring the old machines.

The first step is to provision the DNS Private Resolver against the hub network and create the inbound endpoint in a dedicated subnet, exactly as in a greenfield build, without changing anything that currently routes through the forwarder machines. At this point the resolver exists alongside the old forwarders and resolution still flows through the machines, so nothing has changed for clients. The second step is to create the outbound endpoint and a forwarding ruleset that reproduces the on-premises forwarding rules the old machines carried, so the Azure to on-premises direction is ready on the new path.

```bash
# Create the outbound endpoint for Azure-to-on-premises forwarding
az dns-resolver outbound-endpoint create \
  --resource-group rg-dns \
  --dns-resolver-name resolver-hub \
  --name outbound-to-onprem \
  --location eastus \
  --id "/subscriptions/<sub-id>/resourceGroups/rg-net/providers/Microsoft.Network/virtualNetworks/vnet-hub/subnets/snet-outbound"

# Create a forwarding ruleset and a rule sending an on-premises domain on-premises
az dns-resolver forwarding-ruleset create \
  --resource-group rg-dns \
  --name ruleset-onprem \
  --location eastus \
  --outbound-endpoints "[{\"id\":\"<outbound-endpoint-resource-id>\"}]"

az dns-resolver forwarding-rule create \
  --resource-group rg-dns \
  --ruleset-name ruleset-onprem \
  --name rule-corp \
  --domain-name "corp.contoso.com." \
  --forwarding-rule-state Enabled \
  --target-dns-servers "[{\"ipAddress\":\"10.50.0.10\",\"port\":53}]"
```

The third step shifts traffic. You update the on-premises conditional forwarders to point at the inbound endpoint's address instead of the forwarder machine, and you link the forwarding ruleset to the workload networks so their Azure-originated on-premises queries flow through the outbound endpoint. Do this one rule and one network at a time where you can, verifying resolution after each shift, so a mistake affects one slice rather than everything. Only when every forwarder and every network has been moved and verified do you take the final step of decommissioning the old forwarder virtual machines, and even then you keep them powered off rather than deleted for a short window so a fast rollback is possible. The whole project is an exercise in changing the resolution path without ever leaving clients without an answer, which is why the add-shift-retire order matters more than the speed of the cutover.

## Reading a resolution failure: the diagnostic order that saves hours

When a private name fails to resolve, the link-scopes-the-zone rule gives you a diagnostic order that localizes the fault fast, and following it in sequence beats guessing every time. Start at the client, not the zone, because the zone is rarely the problem. The first question is which resolver the client is actually using. On a Linux machine you read the configured resolver, on Windows you read the adapter's DNS server list, and you confirm it is either 168.63.129.16 or a custom server that you know forwards to it. If the client is pointed somewhere that cannot see the private namespace, you have found the fault and no record change will help.

```bash
# Confirm which resolver the client is using, then query the name directly
cat /etc/resolv.conf
nslookup app1.contoso.internal
nslookup app1.contoso.internal 168.63.129.16
```

The second query in that block is the one that decisively separates a link problem from a forwarder problem. If `nslookup` against the default resolver fails but the same name resolves when you query 168.63.129.16 directly, then the platform resolver has the answer and the client simply was not reaching it, which points at a custom DNS server without a forwarder or a stale resolver list. If the name fails even against 168.63.129.16 directly, then the platform resolver itself has no answer for this network, which points at an unlinked zone or a record that does not exist. Two queries, and you have cut the search space in half before changing anything.

The third check confirms the link. From the control plane you list the networks linked to the zone and verify the asking network is among them, and you check whether the link is a registration or resolution link if auto-registration is in play.

```bash
# List the networks linked to the zone and check the asking network is present
az network private-dns link vnet list \
  --resource-group rg-dns \
  --zone-name contoso.internal \
  --output table
```

Only after those three checks pass do you look at records, and by then you have usually already found the fault. This order works because it follows the model rather than fighting it: client resolver, then platform answer, then link, then record. The same Network Watcher and resolver tooling that exposes routing problems also helps here when the path itself is suspect, and the [route table and user-defined route reference](/2023/08/28/azure-networking-fundamentals/) is the place to confirm that a custom route is not silently blackholing traffic to the resolver before you blame DNS for something the routing layer broke.

## The recurring scenarios, each explained by the model

Several patterns show up again and again in real environments, and each one is the same rule wearing a different costume. A private zone not resolving for a network is the unlinked-network case: the records exist, the network was simply never linked, and one resolution link fixes it. Auto-registration creating or missing virtual machine records is the registration-link case: a machine resolves by hostname only if its network has a registration link to the zone, and a machine that does not auto-register usually sits in a network with a resolution link or no link at all, not a broken registration system. On-premises clients failing to resolve Azure private names is the missing-forwarder case: the on-premises servers have no path to the platform resolver, and the answer is a forwarder, historically a virtual machine and now a DNS Private Resolver inbound endpoint.

Split-horizon serving different answers inside and out is not a bug at all, it is the design working: the private zone overrides the public answer inside linked networks and the public answer applies everywhere else, and the moment you expect a single global answer you will misread the behavior as inconsistency. A private endpoint relying on a linked zone is the most consequential variant, because the endpoint can be perfectly configured and still unreachable if the `privatelink` zone is not linked to the consuming network, and the fault presents as a connection failure rather than a DNS error, which sends people debugging the wrong layer. A custom resolver bypassing the platform resolver is the island case: a network set to custom DNS servers resolves everything those servers know and nothing in the private zones, until a forwarder to 168.63.129.16 reconnects it to the private namespace.

### Why does a name resolve from one VM and fail from another in the same setup?

The two virtual machines almost certainly sit in different networks, and only one of those networks is linked to the zone. The platform resolver answers per network, consulting only the zones linked to the asking machine's network, so identical queries from differently linked networks return different results. Check the links before the records.

The counter-reading worth correcting head on is the belief that a Private DNS zone resolves everywhere once it exists, or that connecting on-premises to Azure with a tunnel makes Azure private names resolve on-premises automatically. Both come from importing the public DNS mental model, where publication equals global reachability, into a system built on scope. A private zone publishes nothing. It grants resolution to linked networks and to nothing else, and a network tunnel carries packets, not name resolution. On-premises clients see Azure private names only when an explicit forwarder gives their queries a path to a resolver that can read the linked zones, and that forwarder is a thing you build, not a thing connectivity provides. Hold the scope model rather than the publication model and both misconceptions disappear.

## Three resolution strategies and how to choose between them

Teams designing name resolution in Azure are really choosing among three strategies, and naming them plainly makes the trade-offs visible rather than letting a default win by inertia. The first strategy is the Azure-provided default, where networks use the platform resolver and you create private zones and links for any internal naming you need. The second is custom DNS servers, where you run your own resolving infrastructure, point networks at it, and forward to the platform resolver for the private namespace. The third is the DNS Private Resolver, a managed service that gives you the control of custom servers without the machines to operate them. Each fits a different situation, and the deciding factor is how much custom resolution behavior you need and how much operational burden you are willing to carry.

The Azure-provided default is the right starting point and the right answer for most cloud-native workloads. It requires no servers, it resolves Azure public names and the private zones linked to each network out of the box, and it enforces the link boundary automatically. Its limit is that it offers no place to inject custom forwarding rules of your own, so the moment you need to forward specific domains to an on-premises server or a third-party resolver, the plain default is not enough on its own. For a workload that lives entirely in Azure and talks to Azure services and the public internet, the default is not a compromise; it is the correct and simplest design, and reaching past it adds operational weight you do not need.

Custom DNS servers are the traditional answer for environments with substantial on-premises DNS infrastructure and a desire to keep one consistent resolution behavior across cloud and datacenter. You run the servers, you own the forwarding rules, and you forward the Azure private namespace to the platform resolver so private zones still work. The cost is real: these are machines you patch, monitor, scale for availability, and troubleshoot, and a mistake in their configuration is a resolution outage. The benefit is total control over forwarding and the ability to mirror an existing on-premises DNS design exactly. This strategy made sense for years because there was no managed alternative, and it still fits environments deeply invested in a specific DNS product, but for most teams it has been overtaken by the third option.

The DNS Private Resolver is the managed middle path, and it is the recommended default for any design that needs custom forwarding without the operational weight of servers. It gives you inbound endpoints for on-premises queries, outbound endpoints and forwarding rulesets for Azure-originated custom forwarding, and it scales and stays available as a platform service rather than as machines you keep alive. The deciding rule is straightforward: if the Azure-provided default resolves everything your workload needs, use it and add nothing; if you need custom forwarding rules, hybrid resolution to on-premises, or a single managed resolution layer across many networks, choose the DNS Private Resolver over forwarder virtual machines, and keep custom DNS server machines only where a specific product or behavior genuinely requires them. Confirm the resolver's regional availability against the official source before committing, since coverage expands over time.

### When should I run custom DNS servers instead of using Azure-provided DNS?

Run custom DNS servers only when you need forwarding behavior or product features the platform does not offer and a managed resolver cannot express, or when an existing on-premises DNS design must be mirrored exactly. For most workloads the Azure-provided default or the DNS Private Resolver covers the need with far less operational burden, so custom servers should be a deliberate exception, not the starting point.

## The start of authority record and what zone parameters control

Every zone, public or private, carries an automatically created start of authority record, and while it is easy to ignore, it controls behaviors that surface during real incidents, so a working understanding pays off. The start of authority record holds the parameters that govern how the zone is cached and how negative answers are handled, including the values that determine how long a resolver may cache a no-such-name response. When you create a record and a client that recently failed to resolve it keeps seeing the failure, the negative caching parameter in the start of authority record is the reason, and knowing that turns a baffling delay into an expected one with a known duration.

The start of authority parameters also matter when you reason about how quickly a change propagates. The record set's own time to live governs positive answers, while the start of authority governs the floor on negative caching, and together they set the window in which a client might still be acting on stale information after you have made a change. For a zone where records change often or where fast propagation matters, you tune these values deliberately rather than accepting whatever defaults the zone shipped with, lowering the relevant parameters before a planned change so caches expire quickly and raising them again afterward to reduce query load. Treating the start of authority record as a knob you understand rather than an automatic artifact you ignore is part of designing resolution on purpose.

A related subtlety is that private zones do not have the public name server records that a delegated public zone carries, because there is no public hierarchy for them to advertise into. The absence is correct and expected, and engineers who go looking for name server records to configure on a private zone are again importing a public concept that does not apply. The start of authority record is present and meaningful; the public name server delegation is absent and should be.

## CNAME chains across the public and private boundary

CNAME records, which alias one name to another, behave in a way that is worth making explicit because they cross the public and private boundary constantly and confuse people who expect resolution to stop at the first hop. When a name is a CNAME to another name, the resolver follows the chain, resolving each target in turn until it reaches an address record. The crucial property in Azure is that each hop in the chain is resolved according to the asking network's view, so a chain can begin at a public name, pass through a `privatelink` alias, and end at a private address inside a linked network while ending at a public address everywhere else. The chain is the same; the final answer depends on where it is resolved.

This is exactly the mechanism behind a private endpoint, and seeing it as a CNAME chain rather than as magic clarifies the whole behavior. The service's public name is a CNAME to its `privatelink` subdomain. That subdomain is the name the private zone holds an address record for. Inside a linked network the chain ends at the private address because the linked zone supplies the final record; outside, the chain ends at the public address because no private zone intervenes. When a chain resolves to the wrong end, you debug it hop by hop, resolving each name in the chain explicitly and watching where the answer diverges from what you expect, and the divergence point tells you precisely which zone or link is missing. A chain that reaches the `privatelink` name but resolves it to a public address is the signature of an unlinked private zone, and you have localized the fault to a single missing link without touching anything else.

The practical discipline with CNAME records in private zones is to use them for stable aliases that point at auto-registered machine names, rather than duplicating addresses by hand. An alias like `app1` as a CNAME to the auto-registered hostname of the machine currently serving the application keeps a single source of truth for the address, the auto-registered A record, and a stable name for clients to use, the CNAME, so moving the application to a different machine is a one-line CNAME change rather than an address edit. This keeps the zone legible and keeps the address owned by the registration system that maintains it.

## Anti-patterns the scope model exposes

A short tour of the anti-patterns that the scope model makes obvious is the fastest way to lock in the mental model, because each one is a violation of the link-scopes-the-zone rule wearing the disguise of a reasonable-looking configuration. The first anti-pattern is the orphaned zone: a private zone full of correct records that is linked to no network, or linked only to networks that no longer matter. It resolves nowhere useful, it looks healthy in the portal because the records are present, and it confuses everyone who assumes presence equals reachability. The model tells you that records without links resolve for no one, so the zone's link list is the first thing to read.

The second anti-pattern is the duplicate namespace, where the same internal suffix exists as separate zones in different subscriptions, each linked to its own networks, slowly drifting out of agreement. The model prefers one zone linked widely over many copies linked narrowly, because the link is many to many and a single zone can serve every network that needs it across subscription boundaries. Consolidating the duplicates into one centrally owned zone with broad resolution links eliminates the drift at its source. The third anti-pattern is the silent island, a network set to custom DNS servers with no forwarder to the platform resolver, which resolves everything except the private namespace and presents as a partial failure that is maddening to diagnose until you remember that the custom server simply is not asking the resolver that holds the private answers.

The fourth anti-pattern is the registration tangle, where teams attempt to auto-register the same machines into two zones, hit the one-registration-per-network constraint, and end up with inconsistent machine records. The model says one zone owns machine hostnames per network, and additional suffixes are served by resolution links or managed records rather than by a second registration link. The fifth is the on-premises expectation, the assumption that a network tunnel makes Azure private names resolve on-premises automatically, which ignores that connectivity carries packets and not resolution, and that a forwarder is always required for the on-premises side to see the Azure private namespace. Every one of these is the same rule restated, and an engineer who holds the rule recognizes the anti-pattern on sight rather than discovering it during an outage. The companion command library is the place to reproduce these patterns deliberately and watch each one fail and recover, and you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to build an orphaned zone, then link it and watch resolution appear, which makes the abstract rule concrete in a way reading alone does not.

## Designing private DNS for production

A production design for Azure name resolution comes down to a few deliberate choices, and making them on purpose is the difference between a namespace you can reason about and a sprawl of zones no one fully understands. Centralize the private zones in a hub or a dedicated DNS resource group rather than scattering them across workload subscriptions, because a private zone can be linked across subscription boundaries and a central home makes ownership, change control, and the link inventory legible. Link workload networks to the zones they need as resolution links, and reserve registration links for the one zone per network that owns machine hostnames, respecting the single-registration constraint rather than discovering it during an incident.

For hybrid resolution, prefer the DNS Private Resolver over forwarder virtual machines for new designs, because it replaces the machines you patch and the single points of failure they create with managed, scaled endpoints, and it keeps the resolution rules in a forwarding ruleset you can read and version rather than buried in a server's configuration. Place the inbound endpoint in the hub network where the `privatelink` zones are linked, so a single on-premises forwarder reaches every private endpoint name through one path. Keep the forwarding rulesets narrow and named by domain, so the seam between Azure and on-premises is documented in the rules themselves.

Make the whole arrangement repeatable as code. The Bicep and CLI fragments above are the building blocks, and the zone, the links, and the endpoint zone groups all express cleanly as templates, which means a new workload network gets its resolution links and its `privatelink` bindings from the same deployment that builds the network rather than from a manual click that someone forgets. Treat the private DNS layer as infrastructure with the same rigor as the networks themselves, because a missing link is as much an outage as a missing route, and an undocumented forwarder is as much a liability as an undocumented firewall rule.

Validation deserves a deliberate step rather than a hope that the deployment worked. After a zone, a link, and an endpoint binding go live, resolve the relevant names from a machine inside each consuming VNet and confirm the answer matches the design, because a deployment that succeeds at the control plane can still leave a name resolving to the wrong address if a link landed on the wrong VNet or a zone name carried a near-miss typo. The cheapest insurance against a quiet resolution fault is a short post-deployment check that resolves a known name from a known place and compares the result to the intended address, run as part of the same pipeline that built the resolution layer. When you want to build and trace these arrangements end to end against live resources, you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to stand up zones, attach VNet links, watch auto-registration populate records, and follow a query through the resolver until the model is something you can predict rather than something you look up.

## Observability and governance for the resolution layer

A resolution layer you cannot observe is one you debug only after it breaks, so treat the visibility of name resolution as part of the design rather than an afterthought. The most useful signal is the ability to query the system the way a client does, from inside the networks that matter, and to compare the answer against what the design intends. Building a small set of synthetic checks that resolve known names from known networks and alert when an answer changes unexpectedly catches an unlinked zone or a broken forwarder before a user does, because a resolution failure usually shows up first as a name returning the wrong address rather than as an obvious error. Where the platform exposes query telemetry for the DNS Private Resolver and the zones, collecting it into your logging workspace gives you the volume and the pattern of queries, which is invaluable both for capacity reasoning and for spotting the moment a workload starts resolving a name it should not.

Governance of the zones themselves is a security concern, not merely a tidiness one, because a virtual network link grants a network visibility into a namespace, and an over-broad set of links is an over-broad grant of resolution. Treat the right to create zones, edit records, and especially to add virtual network links as privileged operations controlled through role assignments, so a workload team can resolve the namespaces it needs without being able to link arbitrary networks to sensitive zones or alter records that other teams depend on. Centralizing the zones in a dedicated resource group makes this control practical, because the role assignments live in one place and the link inventory is readable in one place rather than scattered across every subscription that happens to host a zone. The principle is the same one that governs any access grant: the link is an authorization, so the ability to create links is the ability to extend access, and it belongs to the people accountable for the namespace.

The change-control story follows from expressing the layer as code. When zones, links, and endpoint zone groups are deployed from templates, a change to resolution is a reviewed change to a template rather than a click someone makes and forgets, which gives you both an audit trail and a rollback path. A new workload network arrives with its resolution links already declared, a retired network has its links removed by the same deployment that tears it down, and a drift between the declared state and the live state is something you can detect and correct rather than discover during an incident. The reverse situation, an undocumented link added by hand to solve an urgent problem, is exactly the kind of invisible grant that the governance model is designed to prevent, and the discipline of routing every change through code is what keeps the resolution layer auditable as it grows. For the broader routing and filtering context these governance choices sit alongside, the [Azure networking fundamentals walkthrough for engineers](/2023/08/28/azure-networking-fundamentals/) frames how name resolution fits the rest of the network's controls, and reading the two together gives you a single coherent picture of how a packet is routed, filtered, and resolved on its way to a service.

### How do I keep the private DNS layer auditable as it grows?

Centralize the zones in a dedicated resource group, control the right to create zones and links through role assignments, and deploy zones, links, and endpoint zone groups from templates so every change is reviewed and reversible. Synthetic resolution checks from known networks and collected query telemetry then surface drift or a broken link before users feel it.

## The verdict

Azure DNS is two independent zone types served by one platform resolver and bounded by virtual network links, and almost every difficulty engineers hit with it traces to importing the global-publication assumption from public DNS into a private system built on scope. The link-scopes-the-zone rule is the whole thing in a sentence: a Private DNS zone resolves only for the networks it is linked to, so a private name that fails to resolve is an unlinked zone or a missing forwarder far more often than a record problem, and your diagnostic order should reflect that probability. Design the layer on purpose, centralize the zones, reserve registration for the one zone that owns each network's machine names, bridge to on-premises with the DNS Private Resolver rather than fragile forwarder machines, and express all of it as code. Do that and name resolution stops being the thing that breaks mysteriously and becomes a layer you can reason about as confidently as routing or filtering.

## Frequently Asked Questions

### Q: What is the difference between an Azure public DNS zone and a private DNS zone?

A public zone holds records for a domain that the internet resolves, and it becomes authoritative only after you delegate your domain at the registrar to the Azure name servers assigned to the zone. A private zone holds records that only linked virtual networks can resolve, with no delegation, no public name servers, and no path for an outside resolver to find it. The record model is nearly identical between them, since both organize records into name-and-type record sets with a shared time to live. The defining difference is reach. A public zone is global once delegated, while a private zone is bounded to exactly the networks you link to it, which makes scope rather than publication the property that governs everything about how the private zone behaves.

### Q: Do I need to delegate anything at my registrar for a Private DNS zone to work?

No. Delegation is a public-zone concept. A public zone does nothing until you update the name server records at your domain registrar to point at the Azure name servers assigned to the zone, because that delegation is what inserts the zone into the global hierarchy. A private zone has no place in that hierarchy and no public name servers to delegate to. It resolves the instant you link a virtual network to it, with the registrar entirely uninvolved. If you find yourself looking for name server records to publish for a private zone, you are applying the public model to a system that does not use it, and the only step you actually need is the virtual network link that authorizes a network to see the namespace.

### Q: How many virtual networks can I link to a single Private DNS zone?

A single private zone supports a large number of resolution links and a tighter limit on registration links, with the registration ceiling being the more constrained of the two. The exact numbers have been raised over the life of the service, so treat any figure you remember as provisional and confirm the current values against the official Azure limits before you commit a design that approaches them. The practical guidance that does not change is to use resolution links generously for the many networks that need to read a namespace, and to keep registration links scarce because each network can register into only one zone. If a design needs auto-registration across a very large fleet, validate the registration ceiling first rather than discovering it when a link silently fails to register new machines.

### Q: Can one virtual network be linked to multiple Private DNS zones at the same time?

Yes, and this is the normal case for any real workload. A single network commonly links to an internal application suffix such as `contoso.internal` and to several `privatelink` zones that back the private endpoints the workload consumes, for example `privatelink.blob.core.windows.net` and `privatelink.database.windows.net`. The relationship between zones and networks is many to many: one zone serves many networks, and one network sees many zones. The platform resolver consults all the zones linked to the asking network when it answers a query, so the network resolves names from every linked namespace at once. The one constraint is that a network can be the registration target for only a single zone, which limits the auto-registration relationship to one zone per network even though resolution links have no such restriction.

### Q: What is the difference between a registration link and a resolution link?

The difference is whether the link writes records into the zone. A registration link, created with the registration-enabled flag set true, grants the network resolution and also makes Azure automatically write and maintain A records for the virtual machines in that network, keyed on each machine hostname. A resolution link grants resolution only and writes nothing. The two map onto two distinct jobs. Use a registration link for the one zone that should own your machine hostnames in a given network, so booting a machine publishes its name automatically. Use a resolution link for every namespace the network needs to read but should not write into, which includes all `privatelink` zones, since their records come from private endpoints rather than from virtual machines. Choosing the wrong link type leaves a zone either failing to auto-register or accumulating records it should never hold.

### Q: Why does auto-registration only create records for virtual machines and not private endpoints?

Auto-registration is scoped deliberately to virtual machine network interfaces, because those are the resources whose addresses change with the lifecycle of a machine and benefit from automatic upkeep. It writes an A record for each machine in the registration network and removes it when the machine is gone. Private endpoints, load balancers, and platform services are out of scope, so their records do not appear in your internal zone through auto-registration. A private endpoint instead carries its DNS in a `privatelink` zone wired up through the endpoint's own zone group, which creates and maintains the endpoint's A record for you. If you expect a name to exist because a non-virtual-machine resource exists, you almost always need to create that record deliberately or rely on the service's DNS integration, because the auto-registration system has exactly one job and does not stretch to cover other resource types.

### Q: Can I link a Private DNS zone to a virtual network in a different subscription?

Yes. A private zone lives in one resource group and subscription, but the virtual network link can target a network in another subscription entirely, which is precisely how a central platform team publishes a shared resolution namespace to workload teams without surrendering ownership of the records. The platform team owns and changes the zone, and the workload teams receive resolution through links to their own networks. This cross-subscription linking is the backbone of a centralized DNS design, where the private zones sit in a hub or a dedicated DNS subscription and every workload network links to the zones it needs. The records stay under one team's change control while resolution spreads as widely as the links allow, which keeps the namespace legible instead of duplicated across subscriptions.

### Q: What record types do Azure Private DNS zones support?

Private zones support the common record types you expect for internal naming, including A and AAAA for address records, CNAME for aliases, MX for mail routing, PTR for reverse lookups, SRV for service location, and TXT for arbitrary text such as verification strings. Every zone also carries an automatically created start of authority record that defines the zone parameters. The record set is the unit you work with: records sharing a name and type live in one set with a single time to live, and you add a record to its set rather than creating it in isolation. Auto-registration uses A records exclusively for machine hostnames, while aliases you want to expose are usually best expressed as CNAME records pointing at the auto-registered names, which keeps a single writer for the underlying address and a stable alias on top of it.

### Q: How does a record set and its TTL affect cached private DNS answers?

The time to live is a property of the entire record set, not of an individual record, so every record in a set shares the same caching window. A resolver that has cached an answer for a name will keep returning the cached value until the time to live expires, regardless of changes you make at the source. This is why a private name can keep resolving to an old address for a while after you update it: the answer is cached downstream for the duration the set's time to live allows. When you plan a change to a record that clients resolve frequently, lower the set's time to live ahead of the change so caches expire quickly, make the change, and raise it again afterward. Treating the caching behavior as a set-level property rather than a per-record one prevents the confusion of a change that seems not to take effect when it has simply not aged out of caches yet.

### Q: When should I use the Azure DNS Private Resolver instead of a forwarder virtual machine?

Prefer the DNS Private Resolver for any new hybrid design. The forwarder virtual machine pattern works, but it gives you a machine to patch, scale, and monitor, and a single forwarder is a single point of failure for all hybrid resolution. The DNS Private Resolver replaces it with managed inbound endpoints that on-premises DNS can forward to, and outbound endpoints with forwarding rulesets that send Azure-originated queries to on-premises or other servers, all as scaled platform infrastructure with rules you can read and version. The remaining reasons to keep a forwarder virtual machine are narrow, such as a region where the resolver is not yet available or a niche forwarding behavior the rulesets do not yet express, so verify regional availability against the official source and default to the managed resolver wherever it is offered.

### Q: What is the role of a private DNS zone group on a private endpoint?

A private DNS zone group binds a private endpoint to one or more `privatelink` zones and makes Azure create and maintain the endpoint's A record in those zones automatically. Without the zone group you would have to discover the endpoint's private IP and write the A record by hand, then keep it current, which is fragile. With the zone group, provisioning the endpoint also populates the correct record in the bound zone, so resolution for the service's `privatelink` name inside any linked network steers to the private address. The zone group handles the record creation; the virtual network link handles which networks can see it. Both are required for a private endpoint to be reachable by its normal name, and the zone group is the piece that keeps the address right as the endpoint's lifecycle changes.

### Q: How do I plan a private DNS namespace for many workload teams?

Centralize the private zones in a hub or a dedicated DNS resource group, and link workload networks to the zones they need with cross-subscription links. This keeps ownership and change control in one place while resolution spreads as widely as the links allow. Reserve registration links for the single zone per network that owns machine hostnames, and use resolution links for everything else, including all `privatelink` zones. Place a DNS Private Resolver inbound endpoint in the hub so a single on-premises forwarder path reaches every private endpoint name. Express the zones, the links, and the endpoint zone groups as templates so a new workload network gets its resolution wiring from the same deployment that builds the network. The goal is a namespace you can inventory and reason about rather than a sprawl of zones scattered across subscriptions that no one fully owns.

### Q: Does Azure Private DNS cost anything, and how is it billed?

Azure Private DNS carries a cost, and it is typically billed on the number of zones you host and the volume of DNS queries those zones answer, with the DNS Private Resolver billed separately for its endpoints and the queries they process. The specific rates and the units change over time and vary by region, so treat any number you remember as provisional and confirm the current pricing against the official Azure pricing page before you forecast spend. The cost is usually modest relative to the workloads it serves, and the practical optimization is architectural rather than per-query: consolidate zones where it makes sense, avoid duplicating the same namespace across subscriptions when a cross-subscription link would serve, and right-size the DNS Private Resolver to the hybrid traffic it actually carries rather than overprovisioning endpoints.

### Q: Can a Private DNS zone and a public zone use the same domain name?

Yes, and that overlap is the basis of split-horizon resolution. The two zones are independent siblings rather than parent and child, so a public zone for `contoso.com` and a private zone for `contoso.com` can both exist. A client on the internet resolving through public DNS receives the public records, while a client inside a network linked to the private zone receives the private records for any name the private zone holds. Names the private zone does not hold still fall through to public resolution even from inside the linked network, so the private zone does not have to mirror the public domain in full. It only needs the records you want to override locally. This is exactly how private endpoints present a private address inside the network and a public address everywhere else without any change to the name the application uses.

### Q: What happens to auto-registered records when a virtual machine is deleted or resized?

Auto-registration keeps the zone current with the lifecycle of the machines in the registration network. When a machine is deleted, its auto-registered A record is removed, so the zone does not accumulate stale hostnames pointing at addresses no longer in use. When a machine's primary private IP changes, the auto-registered record is updated to the new address. Because the registration system owns these records, you should not create manual records that collide with auto-registered hostnames, since the reconciliation can overwrite or remove a hand-made entry at an inconvenient moment. Keep manual aliases in a separate naming space and point them at machines with CNAME records to the auto-registered names where you can. That discipline lets auto-registration remain the single writer for machine hostnames while your aliases stay stable on top of records the platform maintains.

### Q: How does name resolution behave when a virtual network uses custom DNS servers?

When a network is set to custom DNS servers instead of the Azure-provided default, every machine in it receives those server addresses rather than the platform resolver, and the custom servers answer for whatever they are configured to know. The consequence that surprises people is that a custom server has no inherent knowledge of Azure private zones, because those are visible only through the platform resolver at 168.63.129.16. A custom server resolves the names it is configured for and returns nothing for the private zones unless it carries a forwarder rule that sends the relevant queries, or all unmatched queries, to the platform resolver. The behavior is entirely predictable once you see that the custom server is simply not asking the one resolver that holds the private answers, and the forwarder rule is what reconnects the custom server to the private namespace.

### Q: Can on-premises clients query the 168.63.129.16 resolver directly?

No. The platform resolver address is reachable only from inside a virtual network or from a machine connected to one, and it is not directly usable from on-premises even across a VPN or ExpressRoute connection. This is the property behind most hybrid DNS difficulty. Network connectivity carries packets between on-premises and Azure, but on-premises DNS servers still cannot send a query to the platform resolver and get an answer. The supported path is a relay inside Azure: historically a forwarder virtual machine and now a DNS Private Resolver inbound endpoint, which sits in an Azure network, is reachable from on-premises, and resolves the linked private zones on the on-premises client's behalf. On-premises DNS conditionally forwards the Azure private domains to that inbound endpoint, and the endpoint reaches the platform resolution that on-premises cannot reach directly.

### Q: How does split-horizon resolution make private endpoints work without changing connection strings?

The application keeps using the service's normal public name, such as a storage account's `blob.core.windows.net` name, and split-horizon steers that name to different addresses by location. The public name resolves through a CNAME to a `privatelink` subdomain. On the public internet that subdomain resolves to the service's public address, but inside a network linked to the matching `privatelink` private zone, the platform resolver finds an A record pointing at the private endpoint's private IP, so the same name ends at the private address. The connection string never changes. The location of the client selects the answer. This is why the link to the `privatelink` zone is the most common private endpoint failure point: with the zone unlinked, the name resolves to the public address, the blocked public path fails, and the symptom looks like a connectivity problem rather than the missing link it actually is.
