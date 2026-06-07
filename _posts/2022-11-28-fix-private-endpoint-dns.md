---
layout: post
title: "Fix Private Endpoint DNS Not Resolving"
page_title: "Fix Private Endpoint DNS Not Resolving: Why a Private Endpoint Returns the Public IP and How to Repair the Private DNS Zone Resolution Chain"
date: 2022-11-28
categories: ["Technology"]
tags: ["Azure", "Private Endpoint", "Private Link", "DNS", "Troubleshooting", "Networking"]
excerpt: "A private endpoint resolving to a public IP means one link in its DNS chain is missing. Trace and repair the whole Private DNS resolution path end to end."
image: "/assets/images/blog/blog-25.webp"
reading_time: 62
author: "marcus-hall"
last_updated: 2022-11-28
lang: en
---
You created a private endpoint for your storage account, your SQL server, or your Key Vault, you disabled public network access, and now your application cannot reach the service at all, or worse, it reaches it over the internet path you thought you had closed. You run a name lookup from inside the virtual network and the answer comes back as a public IP address in the service's shared range rather than the endpoint IP you provisioned. This is the single most common failure with Private Link, and it is almost never a problem with the private endpoint itself. A private endpoint not resolving is a DNS problem: the network interface and the endpoint IP were created correctly, but nothing is telling clients to use that private IP instead of the service's public address. The endpoint is a parked car with no road sign pointing to it.

![Fixing private endpoint DNS not resolving and repairing the Private DNS zone chain - Insight Crunch](/assets/images/blog/blog-25.webp)

The reason this trips up so many engineers is that the Azure portal lets you create a working private endpoint, complete with an approved connection and an allocated private IP, without ever creating the DNS records that make that IP reachable by name. The connection status reads "Approved," the endpoint IP shows up in the endpoint blade, and every signal in the resource view says success. Then the application tries to connect to `mystorageacct.blob.core.windows.net` or `mysql-server.database.windows.net`, the operating system asks DNS where that name lives, and DNS hands back the public IP because no one ever told it about the internal one. The fix is to trace the resolution chain link by link, find the one that is broken, and repair it. This article walks that chain from the client's name lookup all the way to the A record that should point at your private IP, names the distinct causes that break it, gives you the confirming command for each, and shows the prevention that stops the problem from recurring across every endpoint you build afterward.

## What a private endpoint actually changes, and what it does not

A private endpoint is a network interface, with a private IP from your subnet, that maps to a specific resource over the Azure backbone. When you create one for a platform-as-a-service resource, Azure provisions a NIC in the subnet you chose, assigns it an address from that subnet's range, and wires a connection from that NIC to the target resource through the Microsoft network rather than the public internet. Traffic to that private IP reaches the service privately, and if you have also disabled public network access on the service, traffic to the public IP is rejected. So far the model is clean and the endpoint works exactly as advertised.

The piece that surprises people is what the private endpoint does not do automatically. It does not change the name your application uses. Your code, your connection string, and your SDK still target the service's canonical hostname, the same fully qualified domain name the service has always had. That name belongs to a public DNS zone owned by Microsoft, and by default it answers with a public IP. Creating a private endpoint allocates a private IP but does nothing, on its own, to make the canonical name answer with that private IP. Bridging the gap between the public name and the private address is the job of DNS, and specifically of an Azure Private DNS zone whose name matches the service's privatelink subdomain, linked to the virtual network where your clients live, and populated with an A record that maps the name to the endpoint IP.

### Why does my private endpoint name resolve to the public IP?

The name resolves to the public IP because the public DNS answer is still the only answer your client can find. The private endpoint created a private IP, but without a Private DNS zone holding an A record for the name and linked to your virtual network, nothing overrides the public record, so the lookup falls through to the internet-facing address.

That single sentence is the whole problem in miniature, and almost every variation of "private endpoint not resolving" reduces to it. The public name has a canonical chain that, for most services, ends in a `privatelink` subdomain. Take blob storage: `mystorageacct.blob.core.windows.net` is a CNAME that points to `mystorageacct.privatelink.blob.core.windows.net`, and that name is where the override happens. Microsoft's public DNS resolves the privatelink name to the public IP. An Azure Private DNS zone named `privatelink.blob.core.windows.net`, linked to your VNet and holding an A record for `mystorageacct`, resolves the same privatelink name to the endpoint IP instead. Your client follows the CNAME to the privatelink name, asks for its address, and gets whichever answer its resolver reaches first. If the resolver reaches your linked Private DNS zone, it gets the endpoint IP. If it does not, it gets the public IP. The entire diagnosis is figuring out why the resolver is not reaching the right zone.

## How to read the symptom before you change anything

The cardinal mistake is to start deleting and recreating the private endpoint when the endpoint is fine. Before touching anything, gather the diagnostic signal, and that signal comes from a name lookup run from the exact place your application runs. The location of the lookup matters enormously, because DNS answers depend on which resolver the querying machine uses, and a lookup from your laptop over the public internet will always return the public IP and tell you nothing useful. Run the lookup from a virtual machine inside the same virtual network as the consuming workload, or from the workload's own host.

On a Linux host inside the VNet, the canonical first command is a name lookup against the service hostname:

```bash
nslookup mystorageacct.blob.core.windows.net
```

Read the answer carefully. A correctly resolving private endpoint produces a chain that ends in the privatelink name and an address inside your subnet's private range:

```
Server:         168.63.129.16
Address:        168.63.129.16#53

Non-authoritative answer:
mystorageacct.blob.core.windows.net  canonical name = mystorageacct.privatelink.blob.core.windows.net.
Name:   mystorageacct.privatelink.blob.core.windows.net
Address: 10.1.2.4
```

Two things in that output confirm health. The CNAME has folded to the `privatelink` subdomain, and the final address is a internal one from your subnet, here `10.1.2.4`. When the endpoint is broken, the same command returns the privatelink CNAME but ends in a public address from the service's shared range, something that is plainly routable on the internet rather than an RFC 1918 address from your VNet. That public answer is the symptom. It means the CNAME chain is intact, which it always is because Microsoft maintains it, but the privatelink name is being answered by the public zone rather than your Private DNS zone.

On Windows, the equivalent is `Resolve-DnsName`, which is more precise than the legacy `nslookup` because it shows the record type explicitly:

```powershell
Resolve-DnsName mystorageacct.blob.core.windows.net
```

Note the resolver address in the output. Inside an Azure VNet that uses Azure-provided DNS, the server answering should be `168.63.129.16`, the Azure platform DNS resolver that every VNet can reach. That address is a virtual public IP Azure uses for the wire server and for DNS, reachable from inside any VNet, and it is the resolver that knows about your linked Private DNS zones. If your lookup is being answered by some other resolver, a domain controller, a third-party DNS appliance, a public resolver like a well-known 8-dot address, then you have found a strong lead immediately: the query is bypassing the resolver that holds the internal answer. Hold that thread; it is one of the distinct causes below.

### How do I confirm whether the problem is DNS or the endpoint?

Run a name lookup from inside the VNet and read the final address. If it is a private IP from your subnet, DNS is correct and the fault is elsewhere, such as a firewall or routing. If it is a public IP, DNS is the fault, and you should trace the Private DNS zone chain rather than recreate the endpoint.

There is a second confirming test that isolates DNS from connectivity decisively. Take the private IP shown in the private endpoint blade, the address Azure allocated to the endpoint NIC, and connect to the service directly by that IP, bypassing the name. For an HTTPS service you can test the TCP path with a port probe:

```bash
nc -vz 10.1.2.4 443
```

If that succeeds while the name lookup returns the public IP, you have proven the case beyond doubt: the network path to the private endpoint is open and healthy, and the only thing wrong is that the name does not point to that IP. That is a pure DNS repair, and you should not go near the endpoint resource. If the direct IP probe also fails, you have a different problem, a network security group blocking the subnet, a route table sending traffic the wrong way, or the endpoint connection not actually approved, and the DNS chain is a red herring for now. Most of the time the direct probe succeeds and the name fails, which points you squarely at the resolution chain.

## The resolution chain, link by link

The mental model that makes every cause obvious is the chain a name lookup travels from the client to the private IP. There are four links, and a private endpoint resolves correctly only when all four hold. Break any one and the name falls through to the public IP. Naming this chain is the core contribution of this article, because once you can see the four links, the diagnosis stops being guesswork and becomes a checklist you walk in order.

The first link is that an Azure Private DNS zone exists with the exact name of the service's privatelink subdomain. For blob storage that is `privatelink.blob.core.windows.net`. For Azure SQL it is `privatelink.database.windows.net`. For Key Vault it is `privatelink.vaultcore.azure.net`. The zone name must match the privatelink suffix for the specific service exactly, because the resolver matches the query against zone names, and a zone named for the wrong service or with a typo simply never matches. If no such zone exists, there is nowhere for the internal answer to live, and the public zone wins by default.

The second link is that the Private DNS zone is linked to the virtual network where the consuming client runs. A Private DNS zone is a standalone resource; it does nothing until it is associated with one or more VNets through a virtual network link. The link is what tells the Azure resolver at `168.63.129.16` to consult that zone when answering queries from machines in that VNet. A zone can exist, be perfectly populated with the right A record, and still be invisible to your client because the link to the client's VNet was never created. This is the single most common broken link in hub-and-spoke topologies, where the zone is often linked to the hub VNet but not to the spoke where the workload actually runs.

The third link is that the zone contains an A record mapping the resource's name to the private IP. The record's name is the resource-specific label, the storage account name or the SQL server name, and its value is the private IP allocated to the endpoint NIC. This record is normally created and maintained automatically by a private DNS zone group, an association you attach to the private endpoint that registers and updates the A record for you. Without the zone group, you have an empty or stale zone: the zone exists and is linked, but it holds no record for your resource, so the query matches the zone, finds nothing, and the resolver returns the public answer through the upstream chain.

The fourth link applies only to clients that resolve through something other than the Azure platform resolver, which in practice means on-premises machines reaching the VNet over a gateway or ExpressRoute, and any client whose VNet uses a custom DNS server. The Azure resolver at `168.63.129.16` is reachable only from inside Azure VNets; an on-premises resolver cannot query it directly. For on-premises clients to get the internal answer, their DNS must conditionally forward the relevant zone, or its parent public zone, to a resolver inside Azure that can reach the Private DNS zone, typically a DNS forwarder VM or Azure DNS Private Resolver in the hub. If that forwarder is missing or pointed at the wrong place, on-premises clients resolve the public IP even though everything inside Azure is correct.

### Is creating the private endpoint enough on its own?

No. Creating the endpoint allocates a private IP and approves the connection, but it does not register any DNS record by itself unless you also attach a private DNS zone group. Without the zone, the link to your VNet, and the zone group that writes the A record, the canonical name keeps resolving to the public IP and clients never use the private path.

That answer is the counter-reading this article exists to correct. A large share of broken private endpoints were built by someone who created the endpoint in the portal, saw "Approved," and assumed the work was done. The portal's create flow does offer to integrate with a Private DNS zone, but it is a step you can skip, and many automated deployments and older templates skip it. The endpoint is real, the private IP is real, and the connection is genuinely approved, yet the name resolves publicly because three of the four chain links were never built. The discipline that prevents this is to treat the private endpoint and its DNS integration as one inseparable unit of work, never as two optional steps.

## The distinct causes, with the confirming check and the tested fix for each

Every "private endpoint not resolving" case maps to one of a small set of root causes, each corresponding to a broken link in the chain above. Walk them in order, because they are roughly ordered from most to least common, and each has a specific signature you can confirm before you change anything.

### Cause one: no Private DNS zone exists for the service

This is the textbook case and the most frequent. The endpoint was created without the optional DNS integration, and no Private DNS zone was ever provisioned. The name lookup from inside the VNet returns the public IP, and when you look at your resource group or subscription for a zone named after the service's privatelink suffix, there is none.

Confirm it by listing the private DNS zones in the subscription and checking for the privatelink name your service needs:

```bash
az network private-dns zone list --query "[].name" -o tsv
```

If `privatelink.blob.core.windows.net` (or the relevant privatelink suffix for your service) is absent from that list, this is your cause. The fix is to create the zone, link it to the consuming VNet, and attach a zone group to the endpoint so the record gets written. Create the zone first:

```bash
az network private-dns zone create \
  --resource-group rg-network \
  --name privatelink.blob.core.windows.net
```

Then link it to the VNet where the client runs, enabling registration is unnecessary here because the zone group will write the record, so a resolution-only link is correct:

```bash
az network private-dns link vnet create \
  --resource-group rg-network \
  --zone-name privatelink.blob.core.windows.net \
  --name link-to-app-vnet \
  --virtual-network app-vnet \
  --registration-enabled false
```

Finally, attach a private DNS zone group to the existing endpoint so Azure writes and maintains the A record:

```bash
az network private-endpoint dns-zone-group create \
  --resource-group rg-app \
  --endpoint-name pe-storage \
  --name default \
  --private-dns-zone privatelink.blob.core.windows.net \
  --zone-name blob
```

After the zone group is created, repeat the name lookup from inside the VNet. The final address should now be the private IP. If it still returns the public address, give the resolver a moment for any cached public answer to expire, and confirm the A record actually landed in the zone, which is the next cause.

### Cause two: the zone exists but is not linked to the client's VNet

Here the zone is present and even holds the correct A record, but the consuming VNet was never linked to it. The Azure resolver only consults a Private DNS zone for VNets that have an explicit virtual network link to that zone, so a workload in an unlinked VNet never sees the internal answer. This is the dominant failure in hub-and-spoke designs, where a platform team links the zone to the hub and forgets the spokes, or links it to one spoke but not the spoke that holds the new workload.

Confirm it by listing the VNet links on the zone and checking whether your client's VNet is among them:

```bash
az network private-dns link vnet list \
  --resource-group rg-network \
  --zone-name privatelink.blob.core.windows.net \
  --query "[].{name:name, vnet:virtualNetwork.id}" -o table
```

If the consuming VNet's resource ID is not in that list, this is your cause. The fix is to add the missing link, exactly as in the create step above but pointed at the VNet that holds the client. A subtle variant worth checking: in a hub-and-spoke with custom DNS, the spoke VNet may use the hub's DNS forwarder rather than Azure-provided DNS, in which case the zone must be linked to the hub VNet where the forwarder lives, not to the spoke. Match the link to wherever the resolver that answers the query actually sits, because the resolver, not the client, is the thing that needs to reach the zone.

### Cause three: the zone group is missing, so no A record was registered

In this case the zone exists, it is linked to the right VNet, but it holds no A record for your resource, or holds a stale one pointing at an old IP. The private DNS zone group is the automation that registers the endpoint's private IP as an A record in the zone and updates it if the IP ever changes. Skip the zone group and you get an empty or stale zone that matches the query but returns nothing private.

Confirm it by listing the A records in the zone and looking for your resource's label:

```bash
az network private-dns record-set a list \
  --resource-group rg-network \
  --zone-name privatelink.blob.core.windows.net \
  --query "[].{name:name, ip:aRecords[0].ipv4Address}" -o table
```

If there is no record whose name matches your resource (for a storage account named `mystorageacct`, you want a record named `mystorageacct` resolving to the private IP), the record was never written. Check whether the endpoint has a zone group at all:

```bash
az network private-endpoint dns-zone-group list \
  --resource-group rg-app \
  --endpoint-name pe-storage -o table
```

An empty result means no zone group exists, which is the root cause. The fix is to create the zone group as shown under cause one, which triggers Azure to register the A record from the endpoint's allocated IP. You can write the A record manually instead, but resist that temptation: a manual record does not update if the endpoint IP changes, so it drifts silently. The zone group keeps the record correct for the life of the endpoint, which is the durable fix.

### Cause four: on-premises clients resolve the public IP with no conditional forwarder

Everything inside Azure is correct, the zone exists, is linked, holds the right record, and Azure VMs resolve the private IP perfectly. But machines on-premises, reaching the VNet across a VPN gateway or ExpressRoute, still get the public IP. The cause is that on-premises DNS servers cannot query the Azure resolver at `168.63.129.16`, because that address is reachable only from inside Azure. On-premises resolvers go straight to the public internet for the name and naturally receive the public answer.

Confirm it by running the same name lookup from an on-premises machine and comparing it to the answer from an Azure VM in the linked VNet. If the Azure VM returns the private IP and the on-premises machine returns the public one, this is your cause. The fix has two parts that work together. First, stand up a DNS resolver inside Azure that can reach the Private DNS zones, either a small DNS forwarder VM in the hub VNet that forwards to `168.63.129.16`, or the managed Azure DNS Private Resolver, which exists precisely for this hybrid pattern. Second, configure the on-premises DNS servers with a conditional forwarder for the relevant public zone, sending queries for names like `blob.core.windows.net` to that in-Azure resolver. The forwarder relays the query into Azure, the in-Azure resolver consults the linked Private DNS zone, and the private IP travels back to the on-premises client. Forward the parent public zone rather than the privatelink zone itself, because the client asks for the public name first and follows the CNAME inside Azure.

### Cause five: a custom DNS server on the VNet bypasses Azure-provided resolution

A VNet can be configured to use custom DNS servers rather than Azure-provided DNS. When that is set, every client in the VNet sends its queries to those custom servers, and unless those servers ultimately forward to `168.63.129.16`, they never consult the Private DNS zone. The lookup returns whatever the custom server resolves the name to, which over the public path is the public IP. This is a common self-inflicted wound when a team points a VNet at a domain controller or a third-party resolver for internal naming and forgets that the same change blinds the VNet to its Private DNS zones.

Confirm it by inspecting the VNet's DNS settings:

```bash
az network vnet show \
  --resource-group rg-network \
  --name app-vnet \
  --query "dhcpOptions.dnsServers" -o tsv
```

If that returns custom server addresses rather than being empty (empty means Azure-provided DNS), your clients are resolving through those servers. The fix is to make those custom servers forward the platform zones to the Azure resolver. On the custom DNS server, configure a forwarder for the public zones in question, or a catch-all forwarder, pointing at `168.63.129.16`. Once the custom resolver relays platform names into Azure, the linked Private DNS zone answers and the private IP comes back. Do not simply revert the VNet to Azure-provided DNS unless you are certain nothing depends on the custom servers for internal naming, because that trades one outage for another.

### Cause six: the zone is linked to the wrong VNet in a hub-and-spoke topology

This is a refinement of cause two that deserves its own treatment because it is so easy to misdiagnose. In a hub-and-spoke, the Private DNS zones usually live centrally and are linked to the hub. Spokes either use Azure-provided DNS, in which case each spoke needs its own link to the zone, or the spokes point their DNS at a forwarder in the hub, in which case only the hub needs the link. The failure happens when the design mixes the two: a spoke is configured for Azure-provided DNS but the zone is linked only to the hub, so the spoke's clients query the Azure resolver, which has no link to that zone from the spoke's perspective, and the internal answer never appears.

Confirm it by checking the spoke VNet's DNS setting and the zone's links together. If the spoke uses Azure-provided DNS (empty `dnsServers`) and the zone has no link to that spoke, the answer is wrong by construction. The fix depends on the intended design. If spokes are meant to use the hub forwarder, set the spoke's DNS servers to the forwarder's address and ensure the hub is linked to the zone. If spokes are meant to use Azure-provided DNS, link the zone to every spoke that consumes a private endpoint. Pick one model and apply it consistently, because the cross-wired hybrid where some spokes forward and some resolve directly is the configuration that produces intermittent, hard-to-explain failures.

## The findable artifact: the private endpoint DNS resolution chain table

The fastest way to diagnose any private endpoint that returns the public IP is to walk the four links of the resolution chain in order, confirming each with a single command before moving to the next. This table is the InsightCrunch private-endpoint DNS chain reference. Each row is one link, the check that confirms it, and the fix when the check fails. Run them top to bottom and you will land on the broken link within a few minutes.

| Chain link | What it must be true | Confirming check | Fix when missing |
| --- | --- | --- | --- |
| Zone exists | A Private DNS zone named for the service privatelink suffix exists | `az network private-dns zone list --query "[].name"` | Create the zone with the exact privatelink name for the service |
| Zone linked | The zone is linked to the VNet (or hub) whose resolver answers the client | `az network private-dns link vnet list --zone-name <zone>` | Add a virtual network link to the resolving VNet |
| Record present | The zone holds an A record mapping the resource name to the private IP | `az network private-dns record-set a list --zone-name <zone>` | Attach a private DNS zone group to the endpoint |
| Client uses Azure resolver | The querying machine resolves through `168.63.129.16` or a forwarder that does | `nslookup <name>` and read the Server line | Add a conditional forwarder (on-premises) or fix custom DNS forwarding |

The table doubles as a prevention checklist. Before you declare any private endpoint finished, confirm all four rows return green. Most broken endpoints fail the first three rows because the deployment created the endpoint and stopped; the fourth row is the one that bites hybrid and custom-DNS environments specifically.

### Which check should I run first when a private endpoint will not resolve?

Run the name lookup from inside the VNet first and read the final address. A public IP confirms a DNS fault, after which you walk the chain table top to bottom: zone exists, zone linked, record present, client uses the right resolver. The first row that fails is your root cause.

## How the resolver actually reaches the right answer

To debug the harder cases with confidence, it helps to understand what the Azure resolver at `168.63.129.16` does when a query arrives. The resolver is a recursive service every VNet can reach. When a client in a VNet using Azure-provided DNS asks for a name, the query goes to that resolver. The resolver checks whether any Private DNS zone linked to the client's VNet matches the queried name. If a linked zone matches, the resolver answers authoritatively from that zone. If no linked zone matches, the resolver resolves the name through the public DNS hierarchy and returns the public answer.

This is why the link is the pivotal element. The match the resolver performs is scoped to zones linked to the querying VNet, not to every Private DNS zone in the subscription. A zone can be linked to ten VNets and unlinked from yours, and from your VNet's point of view it does not exist. The resolver is not withholding the answer; it genuinely has no path to that zone for your query. The same logic explains the CNAME behavior. The client asks for `mystorageacct.blob.core.windows.net`, which is a public CNAME to `mystorageacct.privatelink.blob.core.windows.net`. The resolver follows that CNAME, then looks for a linked zone matching `privatelink.blob.core.windows.net`. If your zone is linked and holds the `mystorageacct` A record, the resolver answers with the private IP. If not, it resolves the privatelink name publicly, where Microsoft has published the public IP, and you get the public answer with a perfectly intact CNAME chain. The CNAME being correct is what fools people into thinking DNS is healthy; the CNAME is always correct, and the only question that matters is whether the final A record came from your zone or from the public zone.

### Why does the CNAME look right but the IP is still public?

The CNAME to the privatelink subdomain is published by Microsoft and is always present, so seeing it does not mean the private path is working. The IP stays public when no linked Private DNS zone answers the privatelink name, so the resolver falls back to the public record at the end of the same correct-looking chain.

Understanding this also clarifies why caching can make a fix look like it failed. DNS answers carry a time to live, and a resolver or client that cached the public answer before you repaired the chain will keep returning the public IP until that cached entry expires. After fixing the chain, flush the client's resolver cache, or wait out the time to live, before concluding the repair did not work. On Windows, `ipconfig /flushdns` clears the local cache; on Linux it depends on the resolver in use, but restarting the local caching service or the application is the pragmatic move. The platform resolver's own caching is short, so a brief wait usually suffices.

## Prevention: build the endpoint and its DNS as one unit

The recurrence of this problem across an organization is almost always a process gap, not a knowledge gap. Someone, or some pipeline, creates private endpoints without their DNS integration, and the same broken-chain incident repeats every time a new endpoint ships. The durable prevention is to make the DNS integration inseparable from the endpoint creation, which you do with infrastructure as code and policy.

In Bicep, the private endpoint and its zone group are defined together, so it becomes impossible to deploy one without the other. The zone group child resource references the endpoint and the Private DNS zone, and Azure writes the A record on deployment:

```bicep
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2022-07-01' = {
  name: 'pe-storage'
  location: location
  properties: {
    subnet: {
      id: subnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'pe-storage-conn'
        properties: {
          privateLinkServiceId: storageAccountId
          groupIds: [
            'blob'
          ]
        }
      }
    ]
  }
}

resource zoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2022-07-01' = {
  parent: privateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'blob-config'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}
```

Because the `zoneGroup` resource is part of the same template and depends on both the endpoint and the zone, a deployment cannot produce a private endpoint that lacks its A record. That single pattern eliminates causes one and three at the source for every endpoint you ever deploy from code. Pairing it with a centrally managed set of Private DNS zones, linked to every consuming VNet through links that are themselves defined in code, closes cause two as well.

Policy is the enforcement layer on top of the template. Azure Policy ships with built-in definitions that audit or enforce private DNS zone group association on private endpoints, and assigning the deny or audit variant at the subscription or management group level catches any endpoint created outside the sanctioned templates, including ones created by hand in the portal. The combination of a template that always builds the zone group and a policy that rejects endpoints without one is what turns a recurring incident into a configuration that cannot regress. For the full end-to-end build, including the subnet network policy settings and the order of operations, the companion setup guide on configuring private endpoints walks the entire procedure, and pairing that with the deeper Private Link model gives the reasoning behind each step. You can [set up private endpoints end to end with the correct order of operations](/2023/05/01/configure-private-endpoints/) and then harden the build with policy so the DNS integration is never optional.

### How do I stop private endpoints from breaking DNS again?

Define the endpoint and its private DNS zone group together in one template so neither can deploy without the other, link the central zones to every consuming VNet in code, and assign an Azure Policy that denies any endpoint lacking a zone group. That makes the broken chain impossible to ship.

## Related failures this is often confused with

A private endpoint returning the public IP looks, to the application, identical to several other failures, and misreading the symptom sends engineers down the wrong path. Distinguishing them quickly saves the most time.

The closest relative is a broader Azure DNS resolution failure that has nothing to do with private endpoints, where names fail to resolve because of a custom DNS server outage, a missing forwarder, or a misconfigured resolver. If multiple unrelated names fail to resolve from the VNet, not just your private endpoint name, the problem is general DNS, not Private Link, and you should diagnose the resolver itself. The general resolution family is covered in the dedicated troubleshooting guide, and when the failure spans many names rather than one endpoint, [work through the broader Azure DNS resolution failures](/2022/12/26/fix-azure-dns-resolution/) before assuming the private endpoint is at fault.

The second confusable failure is a network security group or firewall blocking the private IP, which presents as a connection timeout rather than a public-IP answer. In that case the name resolves correctly to the private IP, but traffic to it never lands, because an NSG on the subnet, a route table sending the traffic to a network virtual appliance, or a host firewall on the client is dropping the connection. The tell is that the name lookup returns the private IP while the connection still fails; that is a routing or filtering problem, not a DNS one. The direct IP probe described earlier separates these cleanly: if the name resolves privately and the IP probe still times out, stop looking at DNS.

The third is service-side public access still being enabled, which masks the problem rather than causing it. If the service has public network access left on and the name resolves to the public IP, the application keeps working over the internet, and nobody notices the private endpoint is not being used until an audit or a public-access lockdown breaks everything at once. The fix for the DNS chain is the same, but the lesson is to verify the private path works before disabling public access, not after, so the cutover is controlled rather than a surprise. The deeper model of how Private Link composes the endpoint, the connection approval, and the service exposure is worth holding in full, and the [Azure Private Link and private endpoints deep dive](/2023/09/11/azure-private-link-deep-dive/) lays out that model, while the [Azure DNS and Private DNS zones explained guide](/2023/09/18/azure-dns-private-zones-explained/) covers the zone and link mechanics that this troubleshooting path depends on.

## Reproducing the failure and the fix so you can see the flip

The most convincing way to internalize the resolution chain is to build it broken on purpose and then repair it link by link, watching the name lookup flip from the public address to the internal one at the exact step that closes the chain. Create a storage account, create a private endpoint for its blob service without any DNS integration, and run the name lookup from a VM in the same VNet. The answer is the public IP, because no zone exists. Create the Private DNS zone for the blob privatelink suffix, link it to the VNet, and look again: still the public IP, because the zone is empty. Attach the zone group, wait for the record to register, flush the client cache, and look once more: now the private IP. You have watched each link take effect, and the failure is no longer abstract.

This is the kind of controlled reproduction that turns a memorized fix into understanding you can apply to a service you have never used a private endpoint for, because the chain is identical across services and only the privatelink suffix changes. To run that reproduction in a clean sandbox without touching production, and to pull the exact commands for every service's privatelink suffix from a tested library, [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), which includes a private endpoint lab built precisely to show the resolution flip. To drill the diagnosis under time pressure, the way you would mid-incident, [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html), where the private endpoint DNS scenario hands you a broken chain and scores you on finding the right link. Both platforms keep their command sets and scenario libraries current as Azure adds new privatelink suffixes and as the portal's DNS integration flow changes, so the practice stays aligned with what you hit in production.

## Service-specific suffixes and the sub-resource trap

The chain is identical across every service, but the privatelink suffix and, critically, the number of A records you need are not. Most engineers learn the chain on a storage account and then assume every service behaves the same way, which leads to a subtle failure that the simple chain check above can miss: a single logical resource can expose several sub-resources, each with its own privatelink suffix, its own zone, and its own A record. Get the suffix right for one sub-resource and wrong for another, and half your traffic resolves privately while the other half quietly uses the public path.

Storage is the canonical offender. A storage account exposes blob, file, queue, table, web, and Data Lake (dfs) sub-resources, and each one has a distinct privatelink suffix: `privatelink.blob.core.windows.net`, `privatelink.file.core.windows.net`, `privatelink.queue.core.windows.net`, `privatelink.table.core.windows.net`, `privatelink.web.core.windows.net`, and `privatelink.dfs.core.windows.net`. A private endpoint targets one or more of these sub-resources through its group IDs, and the zone group registers an A record only in the zone matching the sub-resource the endpoint was created for. So if you created an endpoint for the blob sub-resource and registered its record in the blob zone, but your application also reaches the file share, the file name still resolves publicly because no endpoint, no zone, and no record exist for the file sub-resource. The symptom is maddening: blob operations succeed over the private path while file operations either fail or escape over the public one, and a casual name lookup against the blob name looks perfectly healthy.

### Why does blob resolve privately but file resolve publicly on the same account?

Each storage sub-resource has its own privatelink suffix, zone, and A record, and a private endpoint registers a record only for the sub-resource it targets. An endpoint for blob does nothing for file, so the file name keeps resolving to the public IP until you create a separate endpoint, zone, and record for it.

The fix is to enumerate every sub-resource your application actually uses and confirm each has its own endpoint, zone, and record. You can create one endpoint per sub-resource, or a single endpoint with multiple group IDs where the service supports it, but in every case each sub-resource needs an A record in the zone matching its suffix. Confirm coverage by listing the zones and checking that one exists for each sub-resource in use:

```bash
az network private-dns zone list \
  --query "[?starts_with(name, 'privatelink.')].name" -o tsv
```

If your application uses blob and file but only the blob zone exists, you have found the gap. Cosmos DB has the same shape, with separate suffixes for its SQL, MongoDB, Cassandra, Gremlin, and Table APIs, so a Cosmos endpoint created for the SQL API does nothing for a client using the MongoDB API on the same account. Azure SQL is simpler, with a single `privatelink.database.windows.net` suffix that covers the database engine, but it carries its own twist: connecting through the SQL redirect connection policy can attempt ports beyond 1433 to backend nodes, and those must also reach the private endpoint, which is a connectivity concern layered on top of resolution. The general rule is to map every distinct endpoint your application talks to onto a sub-resource, and confirm a zone and record exist for each, rather than assuming one endpoint covers the whole account.

### Do I need a separate Private DNS zone for each sub-resource?

Yes, when your application uses more than one sub-resource of a service that splits them across suffixes. Storage and Cosmos DB both do this. Each sub-resource resolves through its own privatelink zone and A record, so covering only one leaves the others resolving to the public IP even though they live on the same underlying account.

A related trap appears when the same service name needs to resolve to different private endpoints in different virtual networks, which happens in segmented environments where each spoke has its own endpoint to the same shared service. A single Private DNS zone holds one A record per name, so you cannot have the same storage account name point at two different private IPs from one zone linked to both VNets. The supported pattern is one zone per VNet, or per group of VNets that should share an endpoint, each zone holding the A record for the endpoint that serves that group, with links scoped so no VNet sees two conflicting zones. Trying to force one shared zone to serve VNets that need different endpoints produces a record that is correct for one VNet and wrong for the other, which presents as intermittent resolution that flips depending on which VNet last won the registration race.

## The registration-enabled flag, and why it must be off for privatelink zones

A virtual network link to a Private DNS zone carries a registration-enabled flag, and getting it wrong on a privatelink zone is a quiet source of trouble. Auto-registration is a feature where Azure automatically creates and maintains DNS records for the virtual machines in a linked VNet, so that VMs can resolve each other by hostname. It is useful for general-purpose private zones that hold your own internal naming, but it has no place on a privatelink zone, and enabling it there can cause the platform to write VM host records into a zone that should contain only the A records the endpoint zone group manages.

When you link a privatelink zone to a VNet for the purpose of private endpoint resolution, the link must be resolution-only, with registration disabled. The records in that zone come exclusively from the zone groups attached to your private endpoints, never from VM auto-registration. A link with registration enabled invites the platform to clutter the zone and, in edge cases, to collide with the names the zone group manages. Confirm the flag on each link:

```bash
az network private-dns link vnet show \
  --resource-group rg-network \
  --zone-name privatelink.blob.core.windows.net \
  --name link-to-app-vnet \
  --query "registrationEnabled"
```

A return of `false` is correct for a privatelink zone. If it shows `true`, recreate the link with `--registration-enabled false`. The deeper reason this matters is that auto-registration and zone-group registration are two different writers competing for the same zone, and a zone should have exactly one source of truth for its records. For a privatelink zone, that single source is the set of zone groups, and the link exists only so the resolver can read the zone, not so the platform can write to it.

### Should the VNet link for a privatelink zone have registration enabled?

No. The link must be resolution-only, with registration disabled. Auto-registration writes virtual machine host records and belongs to general internal zones, not privatelink zones. The only writer for a privatelink zone should be the private endpoint zone group, so enabling registration invites a second writer and possible record collisions.

## Diagnosing with Network Watcher and the resolver directly

When the chain check does not immediately reveal the broken link, two deeper tools pin the problem down. The first is to query the Azure resolver explicitly rather than relying on the client's default resolver, which removes any ambiguity about which resolver answered. From a VM inside the VNet, direct the lookup straight at the platform resolver:

```bash
nslookup mystorageacct.blob.core.windows.net 168.63.129.16
```

By forcing the query to `168.63.129.16`, you bypass any local caching resolver, any custom DNS server the VNet might point at, and any forwarder in between. If this returns the private IP while the client's default lookup returns the public one, the problem is not the Private DNS zone at all; it is that the client is not using the Azure resolver, which sends you to the custom-DNS or forwarder causes. If even this direct query returns the public IP, the zone, link, or record is genuinely missing, and you walk the chain table. This single test cleanly separates "the answer is missing" from "the client is asking the wrong resolver," which are the two top-level branches of the whole diagnosis.

The second tool is Network Watcher, which can probe the path independently of your client's DNS configuration. The connection troubleshoot capability tests reachability from a source VM to a destination by IP and port, which confirms whether the private endpoint IP is reachable once resolution is set aside:

```bash
az network watcher test-connectivity \
  --source-resource vm-app \
  --dest-address 10.1.2.4 \
  --dest-port 443 \
  --resource-group rg-app
```

A successful result against the private IP, paired with a name lookup that returns the public IP, is the strongest possible confirmation that you have a pure DNS problem and an intact network path. Network Watcher also exposes the effective security rules and effective routes on a network interface, which matter when the name resolves privately but traffic still fails, because they reveal an NSG or a route that is dropping or redirecting the connection. Keeping these two diagnostics in mind, the forced resolver query for the DNS branch and the connectivity test for the path branch, lets you state with certainty which half of the system is at fault rather than guessing.

### How can I tell whether the client or the zone is the problem?

Query `168.63.129.16` directly with `nslookup name 168.63.129.16`. If the forced query returns the private IP but the client's default lookup returns the public one, the client is reaching the wrong resolver. If even the forced query returns the public IP, the zone, link, or record is missing. This split decides which branch of the diagnosis to follow.

## Defining the chain in Terraform

Teams that build with Terraform rather than Bicep get the same guarantee by defining the endpoint and its zone group association in one configuration, where the `private_dns_zone_group` block is nested inside the private endpoint resource and cannot be omitted without the whole resource being incomplete. The pattern also defines the zone and the VNet link as code, closing the same causes the Bicep approach closes:

```hcl
resource "azurerm_private_dns_zone" "blob" {
  name                = "privatelink.blob.core.windows.net"
  resource_group_name = azurerm_resource_group.network.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "blob_link" {
  name                  = "link-to-app-vnet"
  resource_group_name   = azurerm_resource_group.network.name
  private_dns_zone_name = azurerm_private_dns_zone.blob.name
  virtual_network_id    = azurerm_virtual_network.app.id
  registration_enabled  = false
}

resource "azurerm_private_endpoint" "storage" {
  name                = "pe-storage"
  location            = azurerm_resource_group.app.location
  resource_group_name = azurerm_resource_group.app.name
  subnet_id           = azurerm_subnet.endpoints.id

  private_service_connection {
    name                           = "pe-storage-conn"
    private_connection_resource_id = azurerm_storage_account.this.id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [azurerm_private_dns_zone.blob.id]
  }
}
```

The `registration_enabled = false` on the link enforces the resolution-only rule from the previous section, and the `private_dns_zone_group` block inside the endpoint means a `terraform apply` cannot produce an endpoint without its A record. Because Terraform tracks the zone, the link, and the endpoint as one dependency graph, a change to the endpoint that would alter its IP also re-runs the zone group association, keeping the record correct. The same discipline that the Bicep template enforces is enforced here, and the choice between the two is a matter of which tool your delivery flow already uses rather than any difference in the resolution outcome.

### Will infrastructure as code keep the record correct if the endpoint IP changes?

Yes, when the zone group is part of the same configuration as the endpoint. The zone group reads the endpoint's current private IP and writes the matching A record, and a redeploy that changes the IP re-runs the association. Manual records do not get this; they drift the moment the IP changes, which is why the zone group is the durable mechanism.

## A full worked reproduction, transcript and all

To make the chain concrete, here is the complete sequence built broken and repaired step by step, with the name lookup at each stage so you can see exactly when the answer flips. Start by creating the storage account and the private endpoint with no DNS integration whatsoever:

```bash
az storage account create \
  --name mystorageacct \
  --resource-group rg-app \
  --location eastus \
  --sku Standard_LRS

az network private-endpoint create \
  --name pe-storage \
  --resource-group rg-app \
  --vnet-name app-vnet \
  --subnet endpoints \
  --private-connection-resource-id $(az storage account show -n mystorageacct -g rg-app --query id -o tsv) \
  --group-id blob \
  --connection-name pe-storage-conn
```

At this point the endpoint exists, the connection is approved, and a private IP is allocated. From a VM in `app-vnet`, the lookup returns the public address:

```bash
$ nslookup mystorageacct.blob.core.windows.net
mystorageacct.blob.core.windows.net  canonical name = mystorageacct.privatelink.blob.core.windows.net.
Name:   mystorageacct.privatelink.blob.core.windows.net
Address: 20.150.43.36
```

That `20.x` address is the public IP. The CNAME folded to privatelink, proving the chain is structurally intact, but no zone answers the privatelink name. Now create the zone and link it, but stop short of the zone group:

```bash
az network private-dns zone create \
  --resource-group rg-network \
  --name privatelink.blob.core.windows.net

az network private-dns link vnet create \
  --resource-group rg-network \
  --zone-name privatelink.blob.core.windows.net \
  --name link-to-app-vnet \
  --virtual-network app-vnet \
  --registration-enabled false
```

Look again, and the answer is still public, because the zone is empty:

```bash
$ nslookup mystorageacct.blob.core.windows.net
mystorageacct.blob.core.windows.net  canonical name = mystorageacct.privatelink.blob.core.windows.net.
Name:   mystorageacct.privatelink.blob.core.windows.net
Address: 20.150.43.36
```

The query now matches your linked zone, but the zone holds no A record for `mystorageacct`, so the resolver still falls through to the public answer. Attach the zone group, which writes the record:

```bash
az network private-endpoint dns-zone-group create \
  --resource-group rg-app \
  --endpoint-name pe-storage \
  --name default \
  --private-dns-zone privatelink.blob.core.windows.net \
  --zone-name blob
```

Flush the client cache and look one final time:

```bash
$ nslookup mystorageacct.blob.core.windows.net
mystorageacct.blob.core.windows.net  canonical name = mystorageacct.privatelink.blob.core.windows.net.
Name:   mystorageacct.privatelink.blob.core.windows.net
Address: 10.1.2.4
```

The address is now the private IP from your subnet. You watched the answer stay public through the first two links and flip private only when the third link, the record, was written. That is the entire diagnosis made visible, and it is why the chain table works: each link is necessary, and the answer only goes private when the last necessary link closes. Anyone who has run this reproduction once never again wonders why an approved endpoint resolves to the public IP, because they have seen that approval and resolution are different milestones reached by different steps.

## When the chain is correct but the answer is still wrong

A final category of trouble appears when every link looks correct yet resolution still misbehaves, and these cases reward patience over recreating resources. The most common is a stale record after an endpoint was recreated: the zone group wrote a new A record, but a long time to live on the old record means clients keep the previous IP cached well past the change. Private DNS zone records carry a default time to live, and lowering it before a planned endpoint change reduces the window where a stale answer lingers. Another is a duplicate or conflicting record left behind by a manual edit, where someone added an A record by hand alongside the zone-group-managed one, and the resolver returns whichever it finds, sometimes the wrong one. Auditing the zone for records the zone group did not create catches this. A third is a links-to-the-wrong-zone mistake in a subscription with multiple zones of the same name across resource groups, where the VNet is linked to a zone that exists but is not the one the zone group writes to, so the link points at an empty namesake. Confirm that the zone the link references and the zone the zone group writes to are the same resource by their full resource IDs, not merely the same name, because two zones can share a name across resource groups and the resolver only honors the one your VNet is actually linked to.

### Why does resolution flip back to the public IP intermittently?

Intermittent flips usually mean two writers or two zones are in play: a manual A record competing with the zone-group record, or a VNet linked to a namesake zone in a different resource group than the one the endpoint writes to. Resolve it by ensuring a single zone holds a single, zone-group-managed record for the name.

These corner cases share a theme: the chain has the right shape, but a second source of truth has crept in, whether a stale cache, a hand-edited record, or a duplicate zone. The remedy in each is to reduce the system to one authoritative answer, the zone group writing one record in one zone linked to one resolver path, and to wait out caching rather than recreating resources that are already correct. The investment that pays off most is making the zone group the sole writer everywhere, because a system with one writer cannot produce two answers.

## Azure DNS Private Resolver in practice: inbound, outbound, and rulesets

For hybrid environments the managed Azure DNS Private Resolver replaces the old forwarder VM, and understanding its three moving parts removes most of the confusion around on-premises resolution. The resolver lives in the hub VNet and has two kinds of endpoints. An inbound endpoint is an IP address inside the hub that on-premises DNS servers forward queries to; it is the door through which on-premises names enter Azure resolution. An outbound endpoint is the egress side, which the resolver uses to send queries onward according to forwarding rules. Between them sits a forwarding ruleset, a set of rules that say, for a given domain suffix, forward to this destination resolver.

The pattern that makes private endpoints resolve from on-premises is straightforward once the parts are named. On-premises DNS gets a conditional forwarder for the service's public parent zone, pointed at the resolver's inbound endpoint IP. The query arrives at the inbound endpoint, the resolver consults the Private DNS zones linked to the hub VNet, and because the privatelink zone is linked there, the resolver answers with the private IP and sends it back across the inbound endpoint to the on-premises client. For names that should be forwarded elsewhere rather than answered from Azure private zones, the outbound endpoint and a ruleset send those queries to wherever they belong, such as back on-premises for internal corporate names. The result is bidirectional resolution: Azure clients resolve on-premises names through the outbound path, and on-premises clients resolve Azure private names through the inbound path.

### How do on-premises clients resolve a private endpoint through the DNS Private Resolver?

On-premises DNS conditionally forwards the service's public zone to the resolver's inbound endpoint IP. The resolver, sitting in a hub VNet linked to the privatelink zones, answers the privatelink name with the private IP and returns it through the inbound endpoint. No forwarder VM is needed, and the privatelink zones must be linked to the hub VNet.

The element teams most often miss is that the Private DNS zones still need to be linked to the VNet where the resolver lives, exactly as they would for any Azure client. The resolver is not magic; it is an Azure client of the platform resolution path, and it only sees the zones its own VNet is linked to. So the hub VNet that holds the resolver must be linked to every privatelink zone whose names on-premises clients need, and the inbound endpoint must be reachable from on-premises across the gateway or ExpressRoute. When on-premises resolution fails despite a resolver being present, the two things to check first are whether the privatelink zone is linked to the resolver's hub VNet and whether the on-premises conditional forwarder targets the inbound endpoint IP rather than some stale address. The outbound side and rulesets matter for the reverse direction and for splitting which suffixes go where, but the inbound path plus the hub zone links is what carries the private endpoint answer to on-premises.

## Key Vault, App Service, and other PaaS specifics

Each service carries small specifics worth knowing, because the suffix and the sub-resource shape differ even though the chain is the same. Key Vault uses the `privatelink.vaultcore.azure.net` suffix, and a single endpoint and zone cover the vault, so it is one of the simpler cases; the common mistake is using a guessed suffix like the public `vault.azure.net` for the zone name rather than the privatelink form, which produces a zone that never matches. App Service is more involved because a web app exposes both the site and its source-control and deployment endpoint, the scm site, and both share the `privatelink.azurewebsites.net` suffix; the endpoint registers records for both the site and its scm counterpart, so a name lookup against the scm host should also return the private IP, and if it returns the public one while the main site resolves privately, deployment over the private path will fail even though the running app reaches the service.

### Why does my app run privately but deployments still go over the public path?

App Service exposes the site and a separate source-control endpoint, the scm host, both under the same privatelink suffix. The private endpoint should register both, so if the scm name resolves to the public IP while the main site resolves privately, the deployment path is escaping publicly and you need the scm record present in the zone.

Cosmos DB, as noted with storage, splits its APIs across suffixes, so an account using the SQL API needs the SQL-API privatelink zone, and an account accessed through a different API needs that API's zone instead; mixing them gives the same blob-resolves-file-does-not pattern. Azure SQL's single suffix is simple for resolution, but its connection policy interacts with the private path: in proxy mode all traffic flows through the gateway on port 1433, which the private endpoint handles cleanly, while redirect mode steers the client to connect directly to the backend node on a higher port range, and those connections must also reach the private endpoint, which is a connectivity rather than a resolution concern but is frequently blamed on DNS. The lesson across all of these is to learn the exact suffix and sub-resource shape for the specific service before building the zone, because the chain mechanics are universal but the names and the count of records you need are service-specific, and a wrong suffix is indistinguishable at first glance from a missing zone.

## Catching the failure before users do

The recurring nature of this problem makes it worth detecting proactively rather than waiting for an application to fail. A synthetic check that runs a name lookup from inside each consuming VNet on a schedule, and alerts when the answer for a known endpoint name is a public address rather than the expected internal one, turns a silent misconfiguration into an alert the platform team sees before the application team files a ticket. The check is trivial: resolve the endpoint name, parse the returned address, and compare it against the private range or against the IP recorded in the endpoint blade. Run it from a small always-on VM or a scheduled job in each VNet that consumes private endpoints, and you catch a broken chain the moment it appears, whether from a new endpoint shipped without its zone group or a VNet's DNS setting drifting.

### How do I detect a broken private endpoint chain automatically?

Schedule a name lookup from inside each consuming VNet against your known endpoint names and alert when the resolved address is public rather than the expected private IP. This surfaces a missing zone group or a drifted DNS setting proactively, before an application fails or a public-access lockdown turns the silent gap into an outage.

Pairing the synthetic resolution check with the Azure Policy that denies endpoints lacking a zone group gives two layers of defense: policy stops most broken endpoints from deploying, and the synthetic check catches the residue, such as a zone unlinked from a new spoke or an on-premises forwarder that went stale. Logging the resolution result over time also gives you a record of when an answer flipped, which is invaluable when an intermittent failure needs to be tied to a specific change. The combination converts the private endpoint chain from a thing you debug reactively under incident pressure into a thing you monitor like any other dependency, which is the posture a mature platform takes toward a failure mode it has seen more than once. A team that has been burned by a public-access lockdown breaking traffic that was silently using the public path learns to verify the internal answer continuously, not just at build time, because the gap between building the endpoint and depending on it is exactly where the silent failure hides.

## When Azure Firewall sits in the DNS path

A pattern that surprises engineers is an environment where Azure Firewall is configured as a DNS proxy, with the VNets pointing their DNS at the firewall's private IP. In that design, every name lookup from a workload goes to the firewall, the firewall forwards it to the Azure resolver, and the answer comes back through the firewall. This works for private endpoint resolution only if the firewall forwards to `168.63.129.16` and the firewall's own VNet, or the VNet it resolves on behalf of, is linked to the privatelink zones. The failure mode is a firewall configured as DNS proxy but with its DNS settings pointed at a public resolver rather than the Azure platform resolver, in which case every workload behind the firewall resolves the public IP, because the firewall never consults the Private DNS zones.

### Why do all my private endpoints resolve publicly when Azure Firewall is the DNS proxy?

The firewall is forwarding name lookups to a public resolver instead of `168.63.129.16`, so the Private DNS zones are never consulted. Set the firewall policy DNS servers to the Azure platform resolver and ensure the firewall's VNet is linked to the privatelink zones, and resolution through the firewall returns the private IP.

This pattern also explains a particularly confusing symptom where resolution works from a test VM but not from the production workload: the test VM may use Azure-provided DNS directly while the production subnet routes DNS through the firewall, so the two take different paths to different answers. Whenever a firewall sits in the DNS path, treat the firewall as the resolver for diagnostic purposes. Run the forced lookup against the firewall's IP to see what the firewall returns, and check the firewall policy's DNS configuration to confirm it forwards to the Azure resolver. The firewall DNS proxy is a legitimate and common design, particularly where DNS queries must be logged and inspected centrally, but it inserts one more hop that must be configured to reach the platform resolver, and a misconfigured hop there breaks resolution for everything behind it at once, which is why the blast radius of this particular mistake is so large.

## Connection approval, cross-subscription, and the pending-state confusion

A private endpoint's connection to its target can sit in a state other than approved, and that state is sometimes misread as a DNS problem because the symptom, an application that cannot reach the service, looks similar. When the endpoint and the target resource are in the same subscription and you own both, the connection is auto-approved. When they are in different subscriptions or tenants, or when the resource owner requires manual approval, the connection enters a pending state until the resource owner approves it, and a pending connection does not carry traffic even when DNS resolves perfectly to the private IP.

### Why does the name resolve to the private IP but the connection still fails?

The private endpoint connection may be pending rather than approved, which happens with cross-subscription, cross-tenant, or manually approved connections. DNS resolving to the private IP does not imply the connection is live. Check the connection state on the endpoint, and have the resource owner approve a pending request before treating it as a network or DNS fault.

Confirm the connection state directly on the endpoint:

```bash
az network private-endpoint show \
  --name pe-storage \
  --resource-group rg-app \
  --query "privateLinkServiceConnections[].privateLinkServiceConnectionState.status" -o tsv
```

A return of `Approved` is what you want. `Pending` means the connection awaits approval from the resource owner, and until that happens the private IP is allocated and DNS may resolve to it correctly while no traffic flows. This is the cleanest example of why resolution and connectivity must be diagnosed separately: a pending connection is a connectivity-layer state that the DNS chain knows nothing about, so the name resolves privately and the connection still refuses traffic. In cross-tenant scenarios the approval is done by the team that owns the target resource, which means the fix sometimes lives in an entirely different organization's portal, and the engineer chasing a DNS ghost is looking in the wrong place entirely. Whenever the name resolves to the private IP and traffic still fails, check the connection state before anything else, because an unapproved connection is a one-field fix that no amount of DNS work will resolve.

## Triage order when you inherit a broken environment

Walking into someone else's broken private endpoint, with no knowledge of how it was built, calls for a fixed triage order so you do not waste time. Start by establishing where you are resolving from, because the single most common waste of effort is diagnosing from a machine that uses the wrong resolver. Confirm you are on a VM inside the consuming VNet and note which resolver answers its lookups. Next, run the name lookup and read the final address; a private IP ends the DNS investigation and moves you to connectivity, while a public IP keeps you on the chain. With a public answer confirmed, run the forced lookup against `168.63.129.16` to split the client-resolver branch from the missing-record branch in one command. If the forced lookup answers privately, the client is reaching the wrong resolver, so investigate the VNet's DNS server setting, any firewall in the DNS path, and on-premises forwarders. If the forced lookup also answers publicly, the zone, link, or record is missing, so walk the chain table top to bottom.

### What should I check first on a private endpoint someone else built?

Confirm you are testing from inside the consuming VNet, run the name lookup and read the final address, then force a lookup against `168.63.129.16`. That sequence tells you in three commands whether the fault is the resolver path or the missing record, which is the fork the rest of the diagnosis hangs on.

The reason this order works is that it eliminates the largest sources of wasted effort first. Testing from the wrong machine, blaming the resolver when the record is missing, and blaming the record when the resolver is being bypassed are the three mistakes that turn a five-minute fix into an afternoon, and the triage order rules out each one before you commit to a deeper change. Only after the chain confirms a internal answer should you turn to the connectivity layer, where the connection-approval state, the network security group on the endpoint subnet, and the route table on the client subnet are the usual suspects. Resisting the urge to recreate the endpoint is the discipline that matters most here, because recreating it changes the private IP, invalidates any manual record, and resets approval state, often turning a single broken link into several while leaving the original cause untouched. The endpoint you inherited is almost always fine; the chain around it is what someone left half-built, and the triage order finds the gap without disturbing the parts that work.

## The verdict

A private endpoint that resolves to the public IP is never an endpoint problem and almost always a DNS problem, and the fix is to repair a specific broken link in a four-link chain rather than to recreate anything. The endpoint allocated a private IP and the connection is approved; what is missing is the Private DNS zone, its link to the consuming VNet, the A record the zone group writes, or the forwarder that lets a non-Azure resolver reach the answer. The resolution-chain rule for private endpoints is the whole diagnosis in one sentence: a private endpoint is only as useful as the DNS that points its name at the private IP, so resolving to the public IP means one named link in the chain is missing, and you find which one by walking the chain in order with a single confirming command at each step. Build the endpoint and its zone group together in code, link your zones to every consuming VNet, enforce the pairing with policy, and the broken chain stops recurring. Diagnose it with a name lookup from inside the VNet, confirm each link with the chain table, and you will fix in minutes what otherwise turns into an afternoon of recreating endpoints that were never broken.

## Frequently Asked Questions

### Q: Why does my private endpoint resolve to a public IP instead of the internal one?

The private endpoint allocated a private IP, but nothing is telling DNS to hand that IP back for the service name. The canonical name follows a public CNAME to the privatelink subdomain, and unless an Azure Private DNS zone for that privatelink suffix is linked to your virtual network and holds an A record for the resource, the resolver falls through to the public DNS hierarchy and returns the service's public address. The endpoint connection can read "Approved" and the private IP can be allocated correctly while this is still broken, because the connection and the DNS integration are separate pieces of work. To fix it, confirm a Private DNS zone with the exact privatelink name exists, that it is linked to the VNet where your client runs, and that it contains an A record mapping the resource name to the private IP. Repair whichever of those is missing and the name will return the private address.

### Q: Do I actually need a Private DNS zone for a private endpoint to work?

You need a way for the service name to resolve to the private IP, and an Azure Private DNS zone is the standard mechanism. Without it, clients keep getting the public IP because the public DNS record is the only answer they can reach. You could in theory maintain host file entries on every client or run your own authoritative records, but those approaches do not update when the endpoint IP changes and do not scale beyond a handful of machines. The Private DNS zone, paired with a zone group on the endpoint, registers and maintains the A record automatically for the life of the endpoint, which is why it is the recommended and most reliable option. The zone must be named for the service's privatelink suffix, linked to the consuming virtual network, and populated by the zone group. Skipping the zone is the most common reason a private endpoint never carries any traffic.

### Q: What does the private DNS zone group on an endpoint actually do?

The zone group is the automation that writes and maintains the A record in your Private DNS zone. When you attach a zone group to a private endpoint and point it at a Private DNS zone, Azure reads the private IP allocated to the endpoint's network interface and creates an A record in that zone mapping the resource's name to that IP. If the endpoint's IP ever changes, the zone group updates the record. Without a zone group you have a zone that may exist and be linked correctly but holds no record for your resource, so the query matches the zone, finds nothing, and the resolver returns the public answer. You can write the A record by hand instead, but a manual record drifts when the IP changes and no one notices until connectivity breaks. The zone group keeps the record correct automatically, which is why it is the durable approach rather than a manual entry.

### Q: Why do on-premises machines resolve the public IP when Azure VMs resolve the internal one?

On-premises DNS servers cannot query the Azure platform resolver at `168.63.129.16`, because that address is only reachable from inside Azure virtual networks. When an on-premises machine looks up the service name, its resolver goes straight to public DNS and gets the public IP, even though everything inside Azure is configured correctly. The fix is to stand up a DNS resolver inside Azure that can reach your Private DNS zones, either a small forwarder virtual machine in the hub or the managed Azure DNS Private Resolver, and then configure your on-premises DNS with a conditional forwarder that sends queries for the relevant public zone to that in-Azure resolver. The forwarder relays the query into Azure, the in-Azure resolver consults the linked Private DNS zone, and the private IP travels back to the on-premises client. Forward the parent public zone rather than the privatelink zone, since clients ask for the public name first.

### Q: How do I confirm a private endpoint is resolving correctly?

Run a name lookup against the service's canonical hostname from a machine inside the virtual network where your workload lives, not from your laptop over the internet. Use `nslookup mystorageacct.blob.core.windows.net` on Linux or `Resolve-DnsName` on Windows, and read the final address in the output. A healthy private endpoint produces a CNAME chain that folds to the privatelink subdomain and ends in a private IP from your subnet's range. If the final address is a public one, the chain is broken. Check the resolver shown in the Server line too; inside a VNet using Azure-provided DNS it should be `168.63.129.16`. As a decisive second test, take the private IP from the endpoint blade and probe it directly with a port test. If the direct probe succeeds while the name returns the public IP, the network path is healthy and the fault is purely DNS, so you should fix the resolution chain rather than touch the endpoint.

### Q: I created the endpoint and the portal said Approved, so why does nothing connect?

"Approved" describes only the connection between the private endpoint and the target resource; it says nothing about whether DNS points the service name at the private IP. The portal lets you create a fully approved endpoint with an allocated private IP while skipping the DNS integration step entirely. When that happens, the connection is real but the canonical name still resolves to the public address, so your application either reaches the service over the public path or fails outright if public access is disabled. The missing pieces are the Private DNS zone for the service, the link from that zone to your virtual network, and the zone group that writes the A record. Confirm each of those exists and is correct. The most reliable way to avoid this is to create the endpoint and its zone group together in a single template so the approved connection always ships with the DNS record that makes it usable.

### Q: Why did my private endpoint work yesterday and stop resolving today?

Two patterns produce a sudden regression. The first is an endpoint IP change without a zone group: if someone deleted and recreated the endpoint, or the underlying IP allocation shifted, and the A record was maintained by hand rather than by a zone group, the manual record now points at the old, dead IP while the name still resolves to it. The second is a DNS configuration change on the virtual network, such as switching the VNet to a custom DNS server, or a forwarder going offline, which blinds the VNet to its Private DNS zones. Check whether the A record in the zone matches the IP currently shown in the endpoint blade, and check whether the VNet's DNS server setting changed recently. If the record is stale, attach a zone group so it self-maintains. If the VNet's DNS changed, ensure the custom resolver forwards platform names to `168.63.129.16` so the Private DNS zone is consulted again.

### Q: Does disabling public network access on the service break DNS resolution?

Disabling public network access does not break DNS resolution, but it exposes a DNS problem that was already there and hidden. While public access is on, an unresolved private endpoint quietly works over the public path, so nobody notices the name is resolving to the public IP. The moment you disable public access, that public path is rejected, and the application fails because the name still points at an address the service no longer answers on. The lesson is sequencing: verify the private endpoint resolves to the private IP from inside the VNet before you disable public access, not after. Run the name lookup, confirm the internal answer, test connectivity to the resource, and only then lock down public access. If you disabled public access first and now everything is broken, the fix is the same chain repair, but you have turned a silent misconfiguration into an outage.

### Q: Why does my custom DNS server return the public IP for the private endpoint?

A virtual network set to use custom DNS servers sends every query to those servers, and unless they forward platform zones to the Azure resolver at `168.63.129.16`, they never consult your Private DNS zones. The custom server resolves the name through the public path and returns the public IP. The fix is not to abandon the custom servers, which usually exist for legitimate internal naming, but to add a forwarder on them. Configure the custom DNS server to forward queries for the relevant public zones, or a catch-all forwarder, to `168.63.129.16`. Once the custom resolver relays platform names into Azure, the linked Private DNS zone answers and the private IP comes back. Confirm the VNet's DNS setting with a query against its `dhcpOptions.dnsServers`, and if it lists custom addresses, the forwarding configuration on those servers is where the fix belongs.

### Q: In a hub-and-spoke network, where should the Private DNS zone be linked?

It depends on where the resolver that answers your client's query actually sits, and you must pick one model and apply it consistently. If your spokes use Azure-provided DNS, each spoke that consumes a private endpoint needs its own virtual network link to the zone, because the Azure resolver only consults zones linked to the querying VNet. If instead your spokes point their DNS at a forwarder in the hub, then only the hub VNet needs the link, since the hub forwarder is the resolver doing the lookup. The failure case is a mixed design where a spoke uses Azure-provided DNS but the zone is linked only to the hub, so the spoke's clients query the Azure resolver with no linked zone to match. Check the spoke's DNS setting and the zone's links together, decide whether spokes resolve directly or through the hub, and wire the links to match that decision rather than leaving it cross-wired.

### Q: How long does it take for a private endpoint's DNS record to start resolving?

Once the zone group is attached and the A record is registered in the Private DNS zone, new queries from inside the linked VNet should resolve to the private IP almost immediately, because the Azure resolver consults the zone live. The delay people experience is usually caching, not registration. A client or resolver that cached the public answer before you repaired the chain keeps returning that stale public IP until its time to live expires. Flush the client's DNS cache after the fix; on Windows that is `ipconfig /flushdns`, and on Linux it depends on the local resolver, where restarting the caching service or the application clears it. For on-premises clients reaching the answer through a forwarder, also consider the cache on the forwarder and on any intermediate resolver. After flushing, repeat the lookup, and if it still returns the public IP, the record probably did not register, which points back to the zone group rather than to timing.

### Q: Can I just add a host file entry to point the name at the private IP?

You can, and it will work for that one machine, but it is a trap for anything beyond a quick test. A host file entry hard-codes the private IP, so when the endpoint's IP changes, and it can change if the endpoint is recreated, the entry silently points at a dead address and connectivity breaks with no obvious cause. It also does not scale: every client needs the entry, and there is no central place to update it. Host files bypass the entire DNS chain, which means you lose the automatic record maintenance the zone group provides. Use a host entry only to prove that connectivity to the private IP works while you build the proper Private DNS zone, then remove it. The supported and durable solution is the Private DNS zone with a zone group, which keeps the record correct automatically and serves every client in the linked VNet.

### Q: What is the correct privatelink zone name for my service?

Each Azure service that supports private endpoints has a specific privatelink subdomain, and the Private DNS zone name must match it exactly or the resolver never matches the query. Blob storage uses `privatelink.blob.core.windows.net`, Azure SQL Database uses `privatelink.database.windows.net`, and Key Vault uses `privatelink.vaultcore.azure.net`, while other storage services, Cosmos DB, and the rest each have their own suffix. The pattern is the public hostname with `privatelink` inserted before the service-specific portion. A typo in the zone name, or using the suffix for the wrong service, produces a zone that exists but never matches the query, so the lookup falls through to the public answer. Always confirm the exact suffix for your service against the current list before creating the zone, because new services and sub-resources are added over time and the suffix for a sub-resource can differ from the parent service.

### Q: Why does the name lookup show the right CNAME but still give a public address?

The CNAME from the public name to the privatelink subdomain is published by Microsoft and is always present whether or not your private endpoint resolves correctly, so seeing the CNAME tells you nothing about the private path. The resolver follows that CNAME to the privatelink name, then looks for a Private DNS zone linked to your VNet that matches it. If a linked zone holds the A record, you get the private IP at the end of the chain. If no linked zone matches, the resolver resolves the privatelink name through public DNS, where Microsoft has published the public IP, and you get the public address at the end of the same correct-looking CNAME chain. This is why a healthy-looking CNAME fools people. The only part of the output that answers whether the private path works is the final A record's address, so read that, not the CNAME.

### Q: Should I use Azure DNS Private Resolver or a forwarder VM for hybrid resolution?

Both solve the on-premises resolution problem by giving on-premises DNS a way to reach your Private DNS zones, and the choice comes down to operational overhead. A forwarder virtual machine is a small DNS server you run in the hub that forwards platform queries to `168.63.129.16`; it works, but you own its patching, availability, and scaling. Azure DNS Private Resolver is the managed alternative built for exactly this pattern, with inbound endpoints that on-premises resolvers forward to and outbound endpoints with forwarding rules, and no VM to maintain. For most hybrid environments the managed resolver is the better default because it removes the maintenance burden and the single-VM availability risk. Choose a forwarder VM only if you have an existing DNS appliance strategy you must fit into, or a requirement the managed resolver does not yet meet. Either way, the on-premises side still needs a conditional forwarder pointed at the in-Azure resolver.

### Q: How do I prevent every new private endpoint from breaking DNS the same way?

Make the DNS integration impossible to skip by combining infrastructure as code with policy. In a template, define the private endpoint and its private DNS zone group together so a deployment cannot produce an endpoint without the A record being written, and keep your Private DNS zones centrally managed with virtual network links to every consuming VNet defined in code. Then assign an Azure Policy that audits or denies any private endpoint lacking a zone group, which catches endpoints created by hand in the portal or by pipelines that drift from the standard. The template removes the human step where the DNS integration gets forgotten, and the policy rejects anything created outside the template. Together they turn a recurring incident into a configuration that cannot regress, because the only endpoints that deploy are ones that already carry their DNS record, and anything else is blocked before it reaches production.

### Q: Why does the private endpoint resolve correctly from one subnet but not another?

If two subnets sit in the same virtual network, both should resolve identically through the linked Private DNS zone, so a difference points to the subnets being in different VNets, or to one subnet's traffic taking a different DNS path. Check whether the failing subnet is actually in a separate VNet that lacks a link to the zone, which is common in hub-and-spoke where one spoke was linked and another was missed. Also check whether route tables or a network virtual appliance are sending DNS traffic from one subnet through a path that lands at a different resolver, since traffic forced through a firewall appliance can be answered by a custom resolver that does not forward to Azure. The fix is to ensure the failing subnet's VNet is linked to the zone, or that its DNS path ultimately reaches `168.63.129.16`. Resolution is a property of the VNet and its resolver, so identical VNets resolve identically.

### Q: Does the private endpoint need its own subnet, and does that affect DNS resolution?

A private endpoint consumes a private IP from whatever subnet you place it in, and while it does not strictly require a dedicated subnet, the subnet must have the right network policy setting for the endpoint to be created. The subnet choice does not affect DNS resolution directly, because the A record points at the endpoint's IP regardless of which subnet that IP comes from, and clients resolve through the VNet's resolver rather than through the endpoint's subnet. Where the subnet matters for connectivity, not resolution, is in network security group and route table behavior on the path from client to the endpoint IP. If the name resolves to the private IP correctly but traffic does not land, look at the filtering and routing on the endpoint's subnet, not at DNS. Keep DNS diagnosis and connectivity diagnosis separate: the subnet placement is a connectivity and policy concern, while resolution depends on the zone, the link, and the record.

### Q: Why do I get the private IP from nslookup but my application still cannot connect?

If the name resolves to the private IP and the application still fails, you have moved past the DNS problem and into a connectivity problem, and the two require different fixes. Probe the private IP directly with a port test from the client; if that also fails, the issue is on the network path, not in resolution. Common causes are a network security group on the endpoint's subnet blocking the port, a route table forcing the traffic to a network virtual appliance that drops or fails to return it, a host firewall on the client, or the endpoint connection sitting in a pending rather than approved state. Check the endpoint's connection status, the effective security rules on the subnet, and the route table applied to the client's subnet. Resolution returning the private IP proves DNS is healthy, so stop looking there and diagnose the path the packets take to reach the private endpoint.
