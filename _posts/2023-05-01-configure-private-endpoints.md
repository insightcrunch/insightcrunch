---
layout: post
title: "Configure Azure Private Endpoints End to End"
page_title: "How to Set Up Azure Private Endpoints End to End: Private DNS Zone, Zone Group, Disabling Public Access, and On-Premises Resolution"
date: 2023-05-01
categories: ["Technology"]
tags: ["Azure", "Private Endpoint", "Private Link", "Networking", "Private DNS", "Security"]
excerpt: "Set up an Azure private endpoint end to end: create the endpoint, link the Private DNS zone, build the zone group, then verify private name resolution."
image: "/assets/images/blog/blog-94.webp"
reading_time: 63
author: "marcus-hall"
last_updated: 2023-05-01
lang: en
---
A correctly configured Azure private endpoint moves traffic to a managed service off the public internet and onto your virtual network, where it rides a private IP address that only your network can reach. When the setup is right, an application in a subnet calls its storage account, its SQL database, or its Key Vault using the same hostname it always used, and that name now resolves to a private address inside your address space. Nothing about the connection string changes. The packets simply stop leaving the network. When the setup is wrong, and it is wrong far more often than teams expect, the endpoint exists, the portal shows it as approved and healthy, and the application still talks to the service over the public internet because the one piece almost everyone underestimates was skipped. That missing piece is the DNS chain, and getting it right is the whole job.

![Configuring Azure private endpoints end to end with Private DNS zone and zone group - Insight Crunch](/assets/images/blog/blog-94.webp)

This guide walks the full procedure from an empty subnet to a verified private connection, and it does so in the order Azure actually requires rather than the order the portal wizard suggests. You will create the private endpoint in a subnet, create or reuse the Private DNS zone that matches the service, link that zone to the consuming virtual network, configure the private-DNS-zone group so the address record registers automatically, decide whether to disable public network access on the service, and then verify with a name lookup that the hostname now answers with the private IP. Each step has a quiet failure mode that produces a working-looking endpoint with broken behavior, and each of those traps gets named as we reach it. The reader who follows this through leaves able to stand up private connectivity that genuinely keeps traffic private, and able to prove it rather than assume it.

## The Endpoint-Plus-DNS Rule: Why a Private Endpoint Without Its Zone Still Resolves Publicly

The single idea that governs every private endpoint deployment is this: a private endpoint without its Private DNS zone, its virtual network link, and its zone group still resolves to the public IP, so the DNS chain is not an optional follow-up to the setup, it is the setup. Call it the endpoint-plus-DNS rule. An endpoint resource by itself creates a network interface in your subnet and assigns it a private address. That much is real, and you can see the address in the portal. What the bare endpoint does not do is change how the service hostname resolves. The fully qualified domain name of a storage account, for example, continues to point at a public address served by Azure public DNS, because nothing has told your network to answer that name differently. The application resolves the name, gets the public IP, and connects over the internet exactly as before, all while a perfectly good private interface sits unused in the subnet.

This is why so many teams report that they "set up a private endpoint" and traffic is still going out the front door. They created the endpoint and stopped, treating DNS as a detail. The DNS chain is the mechanism that flips resolution from the public address to the private one. The Private DNS zone holds the address record for the service hostname. The virtual network link attaches that zone to the network so resources in the network use it for resolution. The zone group ties the endpoint to the zone so the record is created and maintained automatically as the endpoint's private IP is assigned. Remove any one of those three and the name resolves publicly. Understanding this rule turns the rest of the procedure from a sequence of mysterious clicks into a chain of steps where each one has an obvious purpose.

If you want the deeper model of how the underlying technology routes a private connection to a service behind a provider's load balancer, the [companion deep dive on Azure Private Link and private endpoints](/2023/09/11/azure-private-link-deep-dive/) lays out the data path and the approval flow that sit beneath everything covered here. This article assumes that model and concentrates on the act of configuring it correctly.

### What does a private endpoint actually create in my subnet?

A private endpoint creates a network interface in the subnet you choose, and that interface receives a private IP from the subnet's address range. The interface maps to a specific sub-resource of the target service, such as the blob endpoint of a storage account. The mapping is the connection; the IP is how your network reaches it.

The network interface that the endpoint produces is not a normal NIC you attach to a virtual machine. It is a managed interface tied to the endpoint resource, and you generally do not edit it directly. Its job is to terminate the private connection on your side of the link. On the service side, the provider has placed the actual resource behind its own load balancer, and the Private Link platform stitches a connection between your managed interface and that load balancer across the Microsoft backbone. The private IP your interface holds is the address your applications will eventually resolve and dial, but only once DNS knows to hand it out. A single service can host several sub-resources, and each sub-resource you want privately reachable needs its own endpoint or its own entry, because the address record is per sub-resource. A storage account with both blob and file access reached privately needs the blob sub-resource and the file sub-resource each represented, each with its own private IP and its own DNS record in the appropriate zone.

## Prerequisites and the Correct Order of Operations

Before the first command runs, four things must be true, and getting them straight up front prevents the most common mid-setup stalls. You need a virtual network with a subnet that has room for the endpoint's interface and does not have a conflicting network policy. You need the target service already created, because the endpoint binds to a specific resource and sub-resource that must exist first. You need permission to create the endpoint, to manage the Private DNS zone, and, if you plan to lock the service down, to change the service's network settings. And you need to know the correct Private DNS zone name for the service you are targeting, because each service family uses a specific zone name and using the wrong one is a silent failure that resolves publicly anyway.

The order of operations matters because two of the steps have a dependency the portal wizard hides. The zone group, which is the piece that auto-registers the address record, needs the Private DNS zone to exist and, in practice, to be linked to the network before the record is useful to clients. The cleanest order, and the one this guide follows, is to create the endpoint, create the zone if it does not exist, link the zone to the network, then attach the zone group. The portal can do several of these in one flow, which is convenient and also the reason people end up with a half-built chain when the flow is interrupted or when an existing zone in a hub network needs to be reused rather than created fresh.

### Which Private DNS zone name does my service need?

Each Azure service family maps to a specific Private DNS zone name, and the name must match exactly or resolution silently falls back to public. Storage blob uses privatelink.blob.core.windows.net, Key Vault uses privatelink.vaultcore.azure.net, and Azure SQL uses privatelink.database.windows.net. Confirm the current name for your service before you create the zone.

The reason the zone name is so specific is that the service's public hostname is a canonical name that ultimately points into the privatelink subdomain when a private endpoint is in play. When you create a private endpoint for a storage account, Azure arranges that the account's public FQDN resolves through a CNAME to a name under the privatelink zone. If you hold that exact privatelink zone in your network and it carries an address record for the account, your resolver answers with the private IP. If your zone name is even slightly off, the CNAME chain finds nothing private and continues to the public answer. This is the most common reason a setup that looks complete still sends traffic publicly, and it is why the [dedicated troubleshooting walkthrough for a private endpoint that will not resolve](/2022/11/28/fix-private-endpoint-dns/) spends most of its time on zone names and CNAME chains. Treat the zone name as a value to verify against the current service documentation rather than something to type from memory, because Azure has added zones as services gained Private Link support and a name that was right two years ago can be incomplete for a newer sub-resource today.

The cross-service mechanics of how these zones resolve, including the link scope and the autoregistration behavior, are covered in depth in the [explainer on Azure DNS and Private DNS zones](/2023/09/18/azure-dns-private-zones-explained/); if the zone concept itself is shaky, read that first and return here for the endpoint-specific procedure.

## The InsightCrunch Private-Endpoint Setup Checklist

Before walking the commands, here is the findable artifact this guide is built around: the six-step checklist that takes a service from publicly reachable to verifiably private, with the trap that waits at each step. Print it, pin it, and run a deployment against it. Every private endpoint that misbehaves is missing one of these rows.

| Step | What you do | The gotcha that breaks it |
| --- | --- | --- |
| 1. Endpoint | Create the private endpoint in a subnet, bound to the service and the specific sub-resource | Wrong sub-resource (blob vs file vs dfs); subnet has a network policy that blocks creation; subnet too small |
| 2. DNS zone | Create or reuse the Private DNS zone whose name matches the service exactly | Wrong zone name, so the CNAME chain finds no private record and resolution falls back to public |
| 3. VNet link | Link the Private DNS zone to the consuming virtual network | Zone created but never linked, so the network never consults it; in hub-and-spoke, linked to the wrong VNet |
| 4. Zone group | Attach a private-DNS-zone group so the address record registers and tracks the endpoint IP | Manual A record instead of a zone group, so the record goes stale when the IP changes; no group at all, so no record exists |
| 5. Public access | Decide and, if appropriate, disable public network access on the service | Left enabled, so both the public and private paths stay open and the private endpoint proves nothing |
| 6. Verify | Run a name lookup from inside the network and confirm the FQDN returns the private IP | Verifying from your laptop instead of from inside the VNet, so you test the public resolver and conclude wrongly |

The checklist reads top to bottom, but steps two through four form the DNS chain that the endpoint-plus-DNS rule is about. If you remember nothing else, remember that the endpoint in row one does almost nothing useful until rows two, three, and four are all present. Row five is the step that converts "private connectivity is available" into "private connectivity is the only connectivity," and row six is the step that turns a belief into a fact.

## Step by Step: Creating the Endpoint and Building the DNS Chain

The procedure below uses the Azure CLI because the commands are explicit about every dependency, which makes the chain visible. The same operations exist in PowerShell, in the portal wizard, and in declarative templates, and the repeatable-as-code section later translates the whole thing into Bicep. Work through the CLI first so the moving parts are clear, then automate.

### Setting up the variables and confirming the subnet

Start by fixing the names you will reuse so the commands stay readable. The target here is a storage account's blob sub-resource, which is the most common first private endpoint and the one whose DNS behavior trips the most people.

```bash
# Names and locations reused throughout
RG="rg-network-prod"
LOCATION="eastus2"
VNET="vnet-app-prod"
SUBNET="snet-private-endpoints"
STORAGE="stappprod0501"
PE_NAME="pe-stappprod-blob"
DNS_ZONE="privatelink.blob.core.windows.net"
ZONE_GROUP="zg-blob"

# Confirm the subnet exists and has room
az network vnet subnet show \
  --resource-group "$RG" \
  --vnet-name "$VNET" \
  --name "$SUBNET" \
  --query "{name:name, prefix:addressPrefix, peNetworkPolicies:privateEndpointNetworkPolicies}" \
  -o table
```

The query at the end prints the subnet's address prefix and its private-endpoint network-policy setting. Note that setting. On older subnets and on subnets created with infrastructure that explicitly enabled network policies, the value can be Enabled, and an Enabled network policy on a subnet historically blocked private endpoint creation. The setting that affects this changed over time and its default flipped for newly created subnets, so do not assume; read the value and, if creation fails with a policy error, disable the relevant policy on the subnet before retrying. The command to relax it is shown in the misconfigurations section, because it is most useful there as a fix rather than a routine step.

### Creating the private endpoint

With the subnet confirmed, create the endpoint. You bind it to the storage account's resource ID and name the sub-resource through the group-id, which for blob is the literal string blob.

```bash
# Resolve the storage account resource ID
STORAGE_ID=$(az storage account show \
  --resource-group "$RG" \
  --name "$STORAGE" \
  --query id -o tsv)

# Create the private endpoint bound to the blob sub-resource
az network private-endpoint create \
  --resource-group "$RG" \
  --name "$PE_NAME" \
  --vnet-name "$VNET" \
  --subnet "$SUBNET" \
  --private-connection-resource-id "$STORAGE_ID" \
  --group-id blob \
  --connection-name "conn-stappprod-blob" \
  --location "$LOCATION"
```

The group-id is the field people get wrong, so slow down on it. A storage account exposes several sub-resources: blob, file, queue, table, web, and dfs for the Data Lake endpoint. Each is a separate hostname and a separate private endpoint. If you create the endpoint with group-id blob and your application uses the file share, the file hostname still resolves publicly because you privatized the wrong sub-resource. The endpoint will look healthy, the connection will show approved, and the file traffic will go out the public path. When in doubt, create one endpoint per sub-resource your workload actually uses, and verify each one separately. After creation, read back the private IP the endpoint received, because you will check resolution against it later.

```bash
# Read the private IP assigned to the endpoint's interface
az network private-endpoint show \
  --resource-group "$RG" \
  --name "$PE_NAME" \
  --query "customDnsConfigs[].ipAddresses" -o tsv
```

### Creating or reusing the Private DNS zone

The endpoint exists and has a private IP, and at this exact moment the storage account FQDN still resolves to its public address. This is the state where most "it does not work" reports originate. Now build the DNS chain, starting with the zone.

```bash
# Create the Private DNS zone if it does not already exist
az network private-dns zone create \
  --resource-group "$RG" \
  --name "$DNS_ZONE"
```

In a single-network setup you create the zone in the same resource group and move on. In a hub-and-spoke design, the zone almost always already exists in the hub, created once and shared, and you should reuse it rather than create a duplicate in the spoke. Creating a second copy of privatelink.blob.core.windows.net in a spoke network produces two zones that can hold conflicting records, and which one a resolver consults depends on the link, which is exactly the kind of ambiguity that makes a hub-and-spoke private endpoint resolve correctly on Tuesday and publicly on Wednesday. The rule for shared environments is one privatelink zone per service family across the whole topology, held centrally, linked to every network that needs it. The choice between a per-network zone and a centralized one is a design decision, not a setup detail, and the [networking deep dive on private DNS zones](/2023/09/18/azure-dns-private-zones-explained/) works through the trade-offs.

### Linking the zone to the virtual network

A zone that is not linked to a network is invisible to that network. The link is the step that says "resources in this VNet should consult this zone when they resolve names." Without it, the zone holds a perfectly good private record that nobody ever reads.

```bash
# Link the Private DNS zone to the consuming VNet
VNET_ID=$(az network vnet show \
  --resource-group "$RG" \
  --name "$VNET" \
  --query id -o tsv)

az network private-dns link vnet create \
  --resource-group "$RG" \
  --zone-name "$DNS_ZONE" \
  --name "link-vnet-app-prod" \
  --virtual-network "$VNET_ID" \
  --registration-enabled false
```

Set registration-enabled to false. That flag controls whether the link auto-registers the records of virtual machines in the network, which is a feature for general VM name resolution and has nothing to do with private endpoints. For a privatelink zone you want it false, because the records you care about are written by the zone group, not by VM autoregistration, and enabling registration on a privatelink zone mixes two unrelated mechanisms in one place. In a hub-and-spoke topology you create one link per spoke network that needs the service, each pointing at the same central zone. A spoke without a link to the zone resolves publicly no matter how correct everything else is, and "we added the spoke but forgot to link the zone" is one of the most common scaling failures.

### Attaching the private-DNS-zone group

The zone group is the piece that makes the whole thing self-maintaining. It binds the endpoint to the zone and creates the address record automatically, then keeps that record correct if the endpoint's private IP ever changes. Skipping it and writing a manual A record works for exactly as long as the IP stays the same, which is why manual records are a slow-motion failure rather than an immediate one.

```bash
# Attach the zone group so the A record registers automatically
ZONE_ID=$(az network private-dns zone show \
  --resource-group "$RG" \
  --name "$DNS_ZONE" \
  --query id -o tsv)

az network private-endpoint dns-zone-group create \
  --resource-group "$RG" \
  --endpoint-name "$PE_NAME" \
  --name "$ZONE_GROUP" \
  --private-dns-zone "$ZONE_ID" \
  --zone-name blob
```

Once this command returns, the zone holds an address record for the storage account's privatelink hostname pointing at the endpoint's private IP, and the chain is complete. The CNAME from the public FQDN now lands on a name your linked zone answers privately. An application in the linked network that resolves the storage account hostname receives the private IP and connects across the VNet. The endpoint-plus-DNS rule is satisfied: endpoint, zone, link, and group all present.

## Deciding Whether to Disable Public Network Access

A working private endpoint does not, by itself, stop anyone from reaching the service over the public internet. The private path is now available, but the public path is still open unless you close it. This is the step that separates "we offer a private route" from "private is the only route," and it is the step most often deferred and then forgotten. A storage account, a SQL server, or a Key Vault with a private endpoint and public access still enabled is reachable both ways, and an attacker or a misconfigured client that has the connection string and a network route to the public endpoint connects exactly as if the private endpoint did not exist.

The decision is not automatic, because there are legitimate reasons to keep public access on for a window. A migration in progress may still have on-premises tools reaching the service over the public endpoint with firewall rules scoping the source. A shared service consumed by networks you have not yet fully privatized may need the public path until every consumer is moved. The honest position is that disabling public access is the goal, that you should disable it as soon as every consumer reaches the service privately, and that leaving it enabled "for now" tends to become permanent. The setting to change differs slightly per service, but the shape is the same.

```bash
# Disable public network access on the storage account
az storage account update \
  --resource-group "$RG" \
  --name "$STORAGE" \
  --public-network-access Disabled

# For Azure SQL the equivalent is on the server
az sql server update \
  --resource-group "$RG" \
  --name "sql-app-prod" \
  --enable-public-network false

# For Key Vault, set the default action and disable public access
az keyvault update \
  --resource-group "$RG" \
  --name "kv-app-prod" \
  --public-network-access Disabled
```

### Should I disable public network access on the service?

Yes, once every consumer reaches the service privately. Until then, keep public access on but scope it tightly with the service firewall so only known sources connect, and treat the open public path as a temporary state with an owner and a date. A private endpoint with public access left open provides no isolation guarantee.

There is a sharper version of this decision for regulated environments and for any service holding sensitive data: disable public access at creation and build the private path before any consumer exists, so the service is never publicly reachable for even a moment. This inverts the usual order, creating the endpoint and the DNS chain first and the service in a locked-down state, but it removes the window where the data sits behind an open public endpoint. The trade-off is operational friction, because every tool that touches the service now needs network line of sight to the private endpoint, including your deployment pipelines and your break-glass admin access. Plan that access before you flip the switch, because a service you cannot reach to fix is its own kind of incident. The principle of reaching a locked service only from inside the network ties directly into the broader question of when a private endpoint is the right control at all versus a service endpoint, which the [comparison of service endpoints and private endpoints](/2023/11/06/service-vs-private-endpoints/) settles with a decision rule.

## The Settings the Defaults Get Wrong

Several defaults in this flow are set for convenience rather than for a correct private setup, and each one produces a plausible-looking deployment that behaves wrongly. Knowing them in advance is faster than discovering them through a failed verification.

The first is the assumption that the portal wizard's "integrate with private DNS zone" toggle does the whole job. It often does, when you are in a simple single-network setup and let it create and link a fresh zone. The moment you are in a hub-and-spoke topology with a centralized zone, that toggle wants to create a new zone in the local resource group, which is precisely the duplicate-zone problem described earlier. The default convenience path actively fights the correct shared-environment design. When the zone should be reused, decline the wizard's offer to create one and point the zone group at the existing central zone instead, which the wizard supports but does not default to.

The second is the registration-enabled flag on the VNet link, which some templates and some portal flows leave at a value that enables VM autoregistration on a privatelink zone. As covered above, you want it disabled for these zones. The default is not catastrophic, but it muddies the zone with records you did not intend and makes the zone harder to reason about during an incident.

The third is the sub-resource selection, where storage in particular invites error because one account fronts several endpoints. The wizard remembers your last choice or offers the most common one, and a hurried operator accepts blob when the workload needs file or dfs. The fix is discipline: name the sub-resource your application uses, confirm it against the connection string, and create one endpoint per sub-resource in play.

The fourth is the quiet retention of public access, already discussed, which no default disables for you. Every service ships reachable over the public endpoint and stays that way until you act. Treat the disable step as part of the setup, not as hardening you will get to later, because "later" is where this control goes to die.

### Why does my endpoint look healthy but traffic still goes out publicly?

Because the endpoint resource and the DNS chain are independent. A healthy, approved endpoint with a private IP means the network interface and the Private Link connection exist. Traffic only follows the private path once the zone, the VNet link, and the zone group cause the service FQDN to resolve to that private IP from inside the network. Health says nothing about resolution.

The independence of endpoint health and DNS resolution is the conceptual trap that produces more wasted hours than any other part of this topic. Operators look at the endpoint, see green, see an approved connection state, and conclude the job is done, then spend an afternoon confused that traffic still leaves the network. The portal's health view reports on the Private Link connection between your managed interface and the provider's load balancer. It has no opinion about whether your network's resolvers hand out the private IP for the service name, because resolution is governed by the zone, the link, and the group, which are separate resources the health view does not summarize. The mental separation to hold is that connectivity health and name resolution are two different systems, and a private endpoint deployment is only correct when both are right. The first thing to check when traffic stays public despite a healthy endpoint is always resolution, and the [end-to-end DNS troubleshooting guide for private endpoints](/2022/11/28/fix-private-endpoint-dns/) is the right next read when verification fails.

## Verifying That the Setup Actually Works

Verification is where belief becomes fact, and the most important rule of verification is to test from the right place. Resolution depends on which resolver answers the query, and your laptop, your jump box on a different network, and a virtual machine inside the linked VNet can all give different answers for the same hostname. The only meaningful test is from inside a network that is linked to the zone, because that is where your applications live and where the private record applies.

From a virtual machine in the linked VNet, resolve the service FQDN and confirm the answer is the endpoint's private IP, not a public address.

```bash
# From a VM inside the linked VNet
nslookup stappprod0501.blob.core.windows.net

# Expected: a CNAME chain ending at the privatelink zone,
# resolving to the private IP you recorded earlier, for example 10.x.x.x

# A cleaner view of the resolution chain
dig stappprod0501.blob.core.windows.net +noall +answer
```

A correct result shows the public FQDN as a CNAME pointing into the privatelink subdomain, and the privatelink name resolving to a private address in your subnet's range. If instead you see a public IP, the DNS chain has a gap, and the gap is almost always a missing or mismatched zone, a missing VNet link, or a missing zone group. If you see the private IP but the application still cannot connect, the problem has moved from DNS to the network path or the service firewall, which is a different class of issue. Distinguishing "the name resolves wrong" from "the name resolves right but the connection fails" is the single most useful diagnostic split, because it tells you whether to look at the DNS chain or at routing and firewall rules.

A second verification confirms the address record actually exists in the zone, which catches the case where the zone group never ran or failed silently.

```bash
# Confirm the A record exists in the Private DNS zone
az network private-dns record-set a list \
  --resource-group "$RG" \
  --zone-name "$DNS_ZONE" \
  -o table
```

If this returns an address record for the storage account name pointing at the private IP, the zone group did its job. If the zone is empty, the zone group is missing or misconfigured, and no amount of resolving from the VM will produce a private answer because there is nothing private to resolve to. Checking the record in the zone and resolving from inside the network are complementary: the record check confirms the data exists, and the resolution check confirms clients actually use it.

### How do I confirm a private endpoint resolves to the private IP?

Run a name lookup of the service FQDN from a virtual machine inside the linked virtual network and confirm the answer is the endpoint's private address rather than a public one. Then list the address records in the Private DNS zone to confirm the record exists. Testing from outside the linked network tests the public resolver and proves nothing.

The reason testing location matters so much is that public DNS and your private zone hold different answers for the same name on purpose. The public answer is the legitimate, intended response for anyone not inside a network linked to the zone, because the service is still globally addressable by name. Your private zone overrides that answer only for networks that are linked to it. So a lookup from your workstation, which uses public resolvers, correctly returns the public IP and tells you nothing about whether the private path works. The mistake of verifying from the wrong place produces both false failures, where people think the setup is broken because their laptop sees the public IP, and false successes, where people think it works because they never tested the failure case. Always verify from inside, and when you cannot get a shell on a VM in the network, a small test deployment or a container instance attached to the subnet gives you a vantage point that reflects what your applications see.

## Making Private Endpoint Resolution Work From On-Premises

Everything above assumes the client lives in the linked virtual network. On-premises clients are a different problem, because an on-premises machine does not use your Azure Private DNS zone directly. The zone is consulted by the Azure-provided resolver inside the VNet; an on-premises resolver has no path to it. So an on-premises application that resolves the storage account name gets the public IP and connects publicly, even though the private endpoint and the whole Azure-side chain are perfect. The fix is to give on-premises a way to reach the Azure resolver, and the standard pattern is a conditional forwarder pointing at a DNS resolver that sits inside the VNet.

The mechanism is a forwarding chain. On-premises DNS forwards queries for the relevant public zones, such as blob.core.windows.net, to a resolver in Azure that can see the Private DNS zone. That resolver, which can be Azure DNS Private Resolver or a DNS forwarder virtual machine in the VNet, resolves the name through the private zone and returns the private IP back across the connection to the on-premises client. The on-premises machine then connects to the private IP over the ExpressRoute or VPN link. Without this forwarder, on-premises resolution has no route to the private record and falls back to public every time.

```bash
# Conceptual: the on-premises conditional forwarder targets the
# in-VNet resolver IP for the relevant public zone. Configuration
# lives on the on-premises DNS server, for example:
#
#   zone "blob.core.windows.net" forwarders { 10.x.x.4; };
#
# where 10.x.x.4 is the Azure DNS Private Resolver inbound endpoint
# or a forwarder VM inside the linked VNet.
```

The detail that catches teams is forwarding the right zone. You forward the public service zone, such as blob.core.windows.net or database.windows.net, not the privatelink zone, because the on-premises client resolves the public name and the CNAME chain into privatelink happens on the Azure resolver after the forward. Forwarding the privatelink zone directly is a common mistake that does not produce the intended result, because the client never asks for the privatelink name; it asks for the public name and expects the resolver to follow the chain. Get the forwarded zone right and on-premises resolution starts returning private IPs; get it wrong and the symptom is on-premises clients connecting publicly while in-Azure clients work fine, which is a confusing split until you realize the two populations use different resolvers.

### Why do on-premises clients still resolve the public IP?

Because on-premises DNS servers do not consult your Azure Private DNS zone. They resolve the service name through public DNS and get the public IP. To fix it, configure a conditional forwarder on the on-premises DNS server that forwards the service's public zone to a resolver inside the linked VNet, which can see the private zone and return the private IP.

The on-premises case is worth dwelling on because it is the failure that survives a perfect Azure-side setup, and that makes it especially frustrating. A team builds the endpoint, the zone, the link, and the group, verifies beautifully from an Azure VM, declares victory, and then the on-premises batch job that has been hitting the storage account for years keeps using the public path. Nothing in the Azure configuration is wrong. The gap is entirely in the on-premises resolution path, which needs the conditional forwarder to reach into Azure for the private answer. The architecture that makes this clean is a centralized DNS design where one resolver in the hub network sees all the privatelink zones and on-premises forwards to it for every relevant service zone, rather than a sprawl of per-service forwarders that drift out of sync. Designing that resolver layer once and pointing everything at it is the difference between on-premises resolution that works for every new private endpoint automatically and a setup where every new service needs a new forwarder negotiated with the network team.

## Common Misconfigurations and the Symptoms They Produce

The brief for any private endpoint deployment is short, but the ways it goes wrong are well worn. Each pattern below pairs the symptom an engineer reports with the setup step that was missed, so you can read backward from what you are seeing to what to fix. These are the recurring cases that show up again and again in real environments.

### The endpoint exists but the name resolves to the public IP

The symptom is the most common one in this entire topic: the private endpoint is created, the portal shows it approved and healthy, and a lookup from inside the network still returns a public address. The missed step is the DNS chain, specifically a Private DNS zone that was never created, never linked, or both. The endpoint produced a private interface and a private IP, but nothing tells the network to resolve the service name to that IP, so resolution follows its normal public path. The fix is to walk steps two through four of the checklist: confirm the zone exists with the exact correct name, confirm it is linked to the network the client lives in, and confirm a zone group is attached so the record registers. When you find the gap, it is usually that someone created the endpoint through a path that did not include DNS integration, or that the zone exists but the link to this particular network was never made.

### The zone exists but holds no address record

The symptom is a zone that is present and linked, yet the lookup still fails or returns public, and listing the records in the zone shows it empty. The missed step is the zone group. A Private DNS zone does not learn about an endpoint's IP on its own; the zone group is the connective tissue that writes and maintains the address record. Without it, the zone is a correctly named, correctly linked, completely empty container. The fix is to attach the zone group to the endpoint pointing at the zone, after which the record appears automatically. This pattern is especially common when someone built the zone and the link by hand, reasoning correctly that those were needed, but did not know about the zone group and assumed the record would materialize. It does not; the group creates it.

### Public access was left enabled

The symptom is subtler because nothing appears broken. The private endpoint works, in-network clients resolve and connect privately, and verification passes. The problem only surfaces in a security review or an incident: the service is still reachable over the public internet by anyone with the connection string and a route to the public endpoint. The missed step is disabling public network access on the service. The private path being available did not close the public path. The fix is to set public network access to disabled once you have confirmed every consumer reaches the service privately, and to scope the service firewall tightly in the interim. The reason this one slips through is that it has no functional symptom; the application works perfectly with public access on, so there is no error to chase, only an exposure that sits quietly until someone looks for it.

### On-premises clients connect over the public internet

The symptom is a clean split: clients inside Azure resolve and connect privately while clients on-premises resolve the public IP and connect over the internet, for the same service and the same name. The missed step is the on-premises conditional forwarder. On-premises resolvers cannot see the Azure Private DNS zone, so they fall back to public resolution. The fix is to configure a conditional forwarder on the on-premises DNS server that forwards the service's public zone to a resolver inside the linked VNet. The confusing part is that the Azure side is entirely correct, which sends people hunting for a problem in the endpoint or the zone that is not there. The tell is the in-Azure versus on-premises split; whenever resolution works from one population and not the other, suspect the resolver path before the endpoint.

### The subnet network policy blocked endpoint creation

The symptom is an outright failure to create the endpoint, with an error referring to network policies on the subnet. The cause is the subnet's private-endpoint network-policy setting, which on certain subnets is in a state that prevents endpoint creation. The fix is to adjust that setting on the subnet and retry.

```bash
# Relax the private-endpoint network policy on the subnet if creation is blocked
az network vnet subnet update \
  --resource-group "$RG" \
  --vnet-name "$VNET" \
  --name "$SUBNET" \
  --private-endpoint-network-policies Disabled
```

The behavior and the default of this setting have changed across Azure's history, and newer subnets behave differently from ones created years ago, so the practical advice is to read the setting first and change it only if creation actually fails. Do not disable policies reflexively as a precaution, because the setting interacts with network security group and route table enforcement on the subnet, and turning it off has implications beyond just allowing the endpoint. Read the current value, understand what the policy controls in your environment, and make a deliberate choice rather than copying a command from a forum.

### The hub-and-spoke design linked the zone to the wrong network

The symptom appears in shared environments: a new spoke gets a private endpoint, the central zone exists, the record is present, and yet the spoke still resolves publicly. The missed step is linking the central zone to the new spoke network specifically. In a hub-and-spoke topology the privatelink zone lives in the hub and must be linked to every spoke that needs the service. Adding the endpoint in the spoke does not link the zone to the spoke; those are separate operations. The fix is to create a VNet link from the central zone to the new spoke. This is the scaling failure of private endpoints, because the per-endpoint setup looks identical to the working ones but the network-to-zone link, which is per network rather than per endpoint, was never extended to the new spoke. The discipline that prevents it is treating the zone link as part of standing up any new network, automated alongside the network itself, so a spoke is never created without its links to the shared zones.

### How do I keep private endpoints consistent across many networks?

Centralize the Private DNS zones in a hub, hold one zone per service family for the whole topology, and link that zone to every spoke that needs the service. Automate the link as part of network provisioning so a new spoke gets its zone links automatically. Per-network duplicate zones are the main source of inconsistent resolution at scale.

Consistency at scale is fundamentally a design problem rather than a per-endpoint problem, and the teams that struggle with private endpoints in large estates are almost always fighting a sprawl of zones created ad hoc by individual deployments. The portal's convenient default of creating a local zone per endpoint is exactly wrong for a large environment, because it produces dozens of copies of the same privatelink zone scattered across resource groups, each linked to a different network, each holding a subset of the records, with no single source of truth. The repair is architectural: consolidate to one central zone per service family, link it everywhere, and forbid the local-zone-creation path in your standards and your templates. Once the zones are centralized, a new private endpoint is a small, predictable operation, because the zone and the links already exist and only the endpoint and its zone group are new. This is the difference between private endpoints that scale cleanly and an estate where every new service is a small DNS investigation.

## Making the Configuration Repeatable as Code

The CLI walkthrough makes the chain visible, but you should not build production private endpoints by typing commands. The whole setup is declarative and belongs in a template, both so it is repeatable and so the DNS chain cannot be half-built. A template that creates the endpoint and the zone group together makes it structurally impossible to ship an endpoint without its record, which removes the single most common failure from the table. The Bicep below provisions a private endpoint for a storage account's blob sub-resource and wires the zone group in one deployment, assuming the central zone already exists and is linked, which is the correct shape for a hub-and-spoke estate.

```bicep
@description('Name of the private endpoint')
param peName string

@description('Location for the endpoint')
param location string = resourceGroup().location

@description('Resource ID of the subnet that will host the endpoint')
param subnetId string

@description('Resource ID of the target storage account')
param storageAccountId string

@description('Resource ID of the existing central Private DNS zone')
param privateDnsZoneId string

@description('The sub-resource group id, for blob this is blob')
param groupId string = 'blob'

resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-04-01' = {
  name: peName
  location: location
  properties: {
    subnet: {
      id: subnetId
    }
    privateLinkServiceConnections: [
      {
        name: '${peName}-conn'
        properties: {
          privateLinkServiceId: storageAccountId
          groupIds: [
            groupId
          ]
        }
      }
    ]
  }
}

resource zoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-04-01' = {
  parent: privateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: groupId
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

output endpointId string = privateEndpoint.id
output endpointNicId string = privateEndpoint.properties.networkInterfaces[0].id
```

The structure of this module encodes the lessons from the failure patterns. The zone group is a child resource of the endpoint and is created in the same deployment, so the record always exists when the endpoint exists. The zone is passed in by resource ID rather than created locally, which enforces the centralized-zone design by making it the path of least resistance: the module cannot create a duplicate zone because it does not create a zone at all. The group id is a parameter, so the same module serves blob, file, and any other sub-resource by changing one value, which keeps the per-sub-resource discipline from earlier without copying the module. Deploy it once per sub-resource your workload uses, pass the matching central zone for each, and the result is consistent every time.

The VNet link from the central zone to a spoke is a separate concern, because it belongs to the lifecycle of the network rather than the endpoint, and that separation is deliberate. Put the link in the module that provisions a spoke network, so every new spoke is linked to the standard set of privatelink zones at creation. That way the endpoint module above can assume the link exists, the spoke module guarantees it, and neither has to know about the other beyond the zone ID. This division mirrors the real ownership boundary, where a platform team owns the hub zones and the spoke links and an application team owns the endpoints, and it prevents the cross-team gap where an app team creates an endpoint into a network whose zone link the platform team never made.

```bicep
// In the spoke-network module: link each central zone to the new spoke
resource zoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  name: '${blobZoneName}/link-${spokeVnetName}'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: spokeVnetId
    }
  }
}
```

With the endpoint module and the spoke-link pattern in place, standing up private connectivity for a new workload becomes two predictable deployments rather than a manual chain with six chances to slip. The pipeline that deploys an application provisions its endpoints from the module, the pipeline that provisions a network establishes its zone links, and the DNS chain is correct by construction. That is the end state worth aiming for: not a documented procedure people follow carefully, but a template structure where the wrong outcome is hard to produce.

### Can I create the endpoint and the DNS record in one deployment?

Yes, and you should. Define the private endpoint and its private-DNS-zone group in the same template so the address record is created automatically with the endpoint and the two can never drift apart. Reference an existing central Private DNS zone by ID rather than creating one locally, which both wires the record and enforces a single shared zone per service family.

The value of co-locating the endpoint and its zone group in one deployment is that it eliminates an entire class of failure rather than just documenting how to avoid it. When the record is a manual follow-up step, someone eventually forgets it, and you get the empty-zone symptom from the misconfigurations section. When the record is a child resource in the same template, forgetting is not possible, because deploying the endpoint deploys the record. This is the general principle behind making infrastructure repeatable as code: the goal is not merely to automate the steps you would otherwise type, but to encode the dependencies so the broken intermediate states cannot be shipped. A private endpoint without its record is a broken intermediate state, and a good template makes it unrepresentable. The same reasoning extends to the link, which belongs in the network template for the same reason, so that a network without its zone links is equally unrepresentable.

## Extending the Pattern to SQL, Key Vault, and Other Services

The storage blob example is the teaching case, but the procedure is identical in shape for every service that supports Private Link, and only three values change: the group id, the Private DNS zone name, and the public-access setting on the service. Learning the pattern once means you can privatize any supported service by looking up those three values.

For Azure SQL, the group id is sqlServer, the zone is privatelink.database.windows.net, and public access is controlled by the server's public network access property. The endpoint binds to the SQL server resource rather than to an individual database, because the server is the connection target, and once the chain is built every database on that server is reached privately. The most common SQL-specific trap is forgetting that the connection string uses the public server FQDN, which is exactly what you want, because the CNAME chain into privatelink handles the redirection; you do not change the connection string to a private name, you let DNS do its job. If you ever find yourself editing connection strings to point at private IPs, the DNS chain is not set up correctly and you are working around it instead of using it.

For Key Vault, the group id is vault, the zone is privatelink.vaultcore.azure.net, and public access is the vault's public network access setting combined with its network ACL default action. Key Vault deserves extra care on the public-access step because vaults frequently hold the most sensitive material in an estate, which makes the open public path a sharper exposure than for many other services. The pattern of locking the vault to private access only, and ensuring your deployment pipelines and identities reach it from inside the network, is the concrete application of least privilege to the network layer, and it pairs naturally with identity-based access controls on the vault itself.

For services with multiple sub-resources, the per-sub-resource rule from the storage example applies in full. Cosmos DB, for instance, exposes different group ids for its different APIs, and you privatize the one your application uses. Always confirm the current group id and zone name for the specific service and sub-resource against the service documentation at the time you build it, because Azure adds Private Link support to new services and new sub-resources regularly, and the list is longer now than it was when many older guides were written. The shape never changes, but the specific values do, and a value that was complete for a service a year ago may be missing a newer sub-resource today.

### Does every database on a SQL server need its own endpoint?

No. The private endpoint binds to the SQL server, not to individual databases, so one endpoint with the sqlServer group id makes every database on that server reachable privately. You need a separate endpoint only for a separate logical server. The same connection string works unchanged, because the public FQDN resolves through the privatelink chain to the private IP.

The server-level rather than database-level binding for SQL is a frequent point of confusion, because people reasonably expect to privatize the thing they connect to, and they connect to a database. The Private Link connection, though, terminates at the logical server, which is the network-addressable unit, and the databases are reached through it. This is convenient at scale, because adding a database to an existing private server requires no new endpoint and no DNS work; the new database inherits the private path automatically. It also means the blast radius of the public-access decision is the whole server, so disabling public access on a server affects every database on it, which is usually what you want but is worth knowing before you flip the switch on a shared server that still has a consumer reaching one of its databases publicly.

## A Worked End-to-End Example: Locking Down a Storage Account

To tie the pieces together, walk a complete scenario from start to verified finish. The setup is a typical one. An application runs on virtual machines in a subnet of a production VNet, it reads and writes blobs in a storage account, and a security review has flagged that the storage traffic leaves the network over the public endpoint. The goal is to move that traffic onto the private path and then close the public path, with proof at the end that both happened.

The first decision is which sub-resource to privatize. The application uses blob storage, so the blob sub-resource is the target, and because the application does not use file, queue, or table on this account, those sub-resources are left alone for now. This is the per-sub-resource discipline in practice: privatize what the workload uses, not everything reflexively, because each endpoint and record is a small ongoing cost in complexity. The blob endpoint goes into a dedicated subnet for private endpoints rather than into the application subnet, which keeps the endpoint interfaces organized and makes the subnet's address consumption predictable as more endpoints are added.

The endpoint is created bound to the storage account's resource ID with group id blob, and it receives a private IP from the dedicated subnet. At this moment, and this is the crucial checkpoint, the application still talks to the storage account publicly, because the DNS chain does not exist yet. A lookup of the account FQDN from an application VM returns a public address. Anyone who stops here and tests has just confirmed the endpoint exists and concluded, wrongly, that the work is incomplete or broken. The endpoint is fine; the chain is not built.

Next the Private DNS zone enters. In this estate the zones are centralized in a hub network, so privatelink.blob.core.windows.net already exists in the hub, and the correct action is to reuse it, not to create a local copy. The production VNet is already linked to the hub zone, because the platform team links every spoke to the standard privatelink zones when the spoke is created, so the link step is already satisfied. This is the payoff of the centralized design: two of the three DNS-chain steps are already done because they were done once for the whole environment. If this were a greenfield single-network setup instead, you would create the zone and the link here, as the CLI walkthrough showed.

The zone group is the step that remains, and it is attached to the endpoint pointing at the central blob zone. The instant it completes, the zone gains an address record for the account's privatelink hostname pointing at the endpoint's private IP. Now the chain is whole. A lookup of the account FQDN from the application VM returns the private IP, the CNAME chain visibly passing through the privatelink subdomain. The application, which never had its connection string touched, now reaches the account privately on its next connection, because resolution changed underneath it and the hostname it always used now answers privately.

Verification comes before the final lock, not after, because you want to confirm the private path works while the public path is still open as a safety net. From an application VM, the name resolves to the private IP and a test read of a blob succeeds, confirming both resolution and connectivity over the private path. The address record is confirmed present in the central zone. Only with that confirmation in hand does the last step proceed: public network access on the storage account is set to disabled. A second test read from the application VM still succeeds, proving the private path carries the real traffic. A test from outside the network now fails to connect, proving the public path is closed. The security finding is resolved, and you can show exactly why with two resolution results and two connection tests rather than an assertion that it should be fine.

The sequencing of that example is the part worth internalizing. Build the private path, verify it carries traffic, and only then close the public path, so you never have a window where the application is broken because you closed the public path before the private one worked. The reverse order, disabling public access first and then building the private chain, guarantees an outage for the duration of the gap, and it is a surprisingly common self-inflicted incident born of treating the lock-down as the first step rather than the last.

## Confirming the Posture Stays Correct Over Time

A private endpoint setup is not a one-time event that stays correct forever on its own. Several things can drift. A new consumer can appear that reaches the service over a path you did not privatize. A new spoke can be added without its zone link. Public access can be re-enabled by a well-meaning change that needed temporary public access for a migration and never reverted it. Someone can create a duplicate local zone that starts answering for some clients. Treating the posture as something to confirm periodically rather than assume keeps these drifts from becoming the next incident or the next audit finding.

The most valuable ongoing check is simply resolution from inside the relevant networks, because resolution is the behavior that actually matters and it captures most drift. If the service name resolves to the private IP from every network that should reach it privately, and resolves to nothing reachable from networks that should not reach it at all, the posture is intact. You can script this check across networks and run it on a schedule, alerting when a name that should resolve privately starts resolving publicly, which is the signal that a zone link broke or a duplicate zone appeared. The check is cheap and it tests the property you care about directly, rather than inferring health from the existence of resources.

The second valuable check is the public-access setting on the services themselves, because that is the control most likely to be silently reverted. A periodic scan of the public network access property across your storage accounts, SQL servers, and vaults catches the case where a service was reopened to the public internet and not reclosed. This is a configuration-drift check rather than a resolution check, and it complements the first: resolution tells you the private path works, the public-access scan tells you the public path is still closed. Both being true is the full definition of a correctly locked-down service, and confirming both periodically is the difference between a posture that holds and one that quietly erodes between audits.

### How do I detect if a service was reopened to public access?

Periodically read the public network access property across your storage accounts, SQL servers, Key Vaults, and other privatized services, and alert on any that flipped from disabled back to enabled. Pair that with a scheduled resolution check from inside each network, so you catch both a reopened public path and a broken private one before they reach an audit.

Detecting drift is fundamentally about choosing checks that test behavior rather than presence. It is easy to confirm that an endpoint resource still exists, but that confirms almost nothing, because the endpoint can exist while the chain around it has broken. The two checks that matter, resolution from inside the network and the public-access setting on the service, test the two properties that define a correct private posture: that traffic goes private and that it cannot go public. Building those two checks into a regular cadence, whether through a governance policy that flags noncompliant services or a simple scheduled script that resolves names and reads settings, turns the private endpoint from a thing you set up once and hope stays right into a thing you can demonstrate is right at any moment. For a regulated environment that demonstration is the deliverable, and for everyone else it is the early warning that catches drift while it is still a quick fix rather than an incident.

## Practicing the Setup Before You Run It in Production

Reading the procedure is not the same as having done it, and the parts that bite, the wrong zone name, the missing link in a spoke, the verification from the wrong place, are exactly the parts that a walkthrough cannot fully convey because they are about seeing the failure and the fix in a live environment. The fastest way to build that instinct is to stand the whole chain up in a sandbox where breaking it costs nothing. You can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to build a private endpoint against a real storage account, watch the name resolve publicly before the DNS chain exists, attach the zone and the group, and watch resolution flip to the private IP in real time. Doing the flip yourself, and then deliberately breaking it by removing the zone group and seeing the empty-zone symptom, fixes the endpoint-plus-DNS rule in your understanding far more durably than reading it does. VaultBook's command and template library also carries the tested CLI and Bicep for each service's group id and zone name, which is the reference you want open while you build, since those values are the ones worth confirming rather than typing from memory. For engineers who want to rehearse the diagnosis side, you can [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) that present a half-built chain and ask you to find the missing step, which builds the backward-reading skill that the misconfigurations section is really teaching. The two platforms cover the build side and the diagnose side of the same skill, and alternating between standing a setup up cleanly and repairing a broken one is the fastest way to make the whole procedure second nature.

## Managing the Connection Lifecycle: Approval, Status, and Removal

The connection between your managed interface and the target service has a lifecycle of its own, separate from the network and DNS work, and understanding it removes a class of confusion that surfaces mostly in shared and cross-team environments. When you stand up the interface against a resource you own and have write permission on, the connection is approved automatically and becomes usable the moment it is created. When the resource lives in another subscription, belongs to another team, or sits in a different tenant, the connection arrives in a pending state and waits for the resource owner to approve it. That waiting state is not a fault. It is the deliberate gate that lets a resource owner decide who is granted a route to their service.

Reading the connection status is the first move whenever traffic is not flowing and you suspect something earlier than DNS. The status lives on both sides, viewable from the consuming resource and from the target service, and the values you care about are approved, pending, and rejected. A pending status means the owner has not yet acted, and the cure is a conversation rather than a configuration change. A rejected status means the owner declined, and recreating the request without addressing why it was declined simply produces another rejection. An approved status means the gate is open and any remaining problem belongs to resolution or routing rather than to the connection itself. Keeping this triage order in mind, status first when traffic stalls and the interface is freshly created, then resolution, then routing, saves the time that is otherwise lost checking the wrong layer.

```bash
# Inspect the connection status from the consuming side
az network private-endpoint show \
  --resource-group "$RG" \
  --name "$PE_NAME" \
  --query "privateLinkServiceConnections[].privateLinkServiceConnectionState" -o json

# Approve a pending connection from the target service side (storage example)
az storage account private-endpoint-connection approve \
  --resource-group "$RG" \
  --account-name "$STORAGE" \
  --name "<connection-name-from-the-service>"
```

Removal deserves the same care as creation, because tearing things down in the wrong order produces the same outages that building them in the wrong order does. The lifecycle of the interface, the DNS record, and the public-access setting are three separate things, and a clean teardown reverses them deliberately. If the service had its public path closed, that path is reopened first and confirmed working, so consumers have a route while the rest is unwound. Then the record and the interface come down. A resource owner who instead deletes the interface while the public path is still closed has just severed every consumer's only route, and because the consumers' configuration never changed, the failure looks like a service outage rather than a network change, which sends the wrong team chasing the wrong cause. The discipline that prevents this is treating the public-access setting as the last thing closed and the first thing reopened, with the interface and record sitting inside that bracket on both setup and teardown.

There is also an ongoing custody question for the connection that matters in larger organizations. A connection approved months ago by a resource owner who has since changed teams is still approved, and nobody revisits it until an audit asks who has a route to a sensitive service. Periodically reviewing the approved connections on your most sensitive resources, and revoking the ones that no longer have a legitimate consumer, keeps the set of routes to a service matching the set of things that should have a route. This is the network-layer equivalent of reviewing who holds a key, and it tends to be neglected precisely because an approved connection keeps working silently whether or not anyone still needs it.

### How do I review who has a connection to a sensitive service?

List the connections on the resource and check each one's status and consuming owner, then revoke any that no longer map to a legitimate consumer. An approved connection persists until someone removes it, so a service can accumulate routes that outlived their purpose. A periodic review of the approved connections on sensitive resources keeps the route list matched to real need.

The custody review is worth building into the same cadence as the public-access scan and the resolution check, because together they answer the three questions an auditor or an incident responder actually asks: can the service still be reached publicly, does it resolve and connect privately from the networks that should reach it, and exactly which consumers hold an approved route to it. A posture that can answer all three on demand is a posture you control rather than one you hope is intact. The connections that linger past their usefulness are rarely a live exploit, but they are the kind of quiet sprawl that turns a clean design into an unauditable one over a year of small unreviewed changes, and a short recurring review keeps the design legible.

## Where Teams Lose Time, and How the Order of Steps Prevents It

Stepping back from the individual commands, almost every hour lost on this topic traces to one of a few recurring patterns, and naming them as patterns rather than as one-off mistakes makes them avoidable. The first is stopping at the interface. The resource is created, the portal reports it healthy, and the work is declared done, while the name still resolves to the public address because the resolution chain was never built. The cure is built into the order this guide insists on: the interface is step one of six, not the finish line, and the deployment is not complete until the verification in step six returns a private answer from inside the network. Anyone who internalizes that the green health indicator describes the connection and says nothing about resolution stops falling into this one.

The second pattern is verifying from the wrong vantage point. An engineer resolves the service name from a workstation, sees the public address, and either panics that the setup failed or, worse, builds the setup, never tests from inside, and assumes success. Both errors come from forgetting that the answer to a name lookup depends entirely on which resolver responds, and that the resolver inside a linked network and the resolver behind a laptop give different answers on purpose. The cure is a rule: verification happens from inside a linked network, full stop, and when no machine is available there, a small test workload attached to the subnet provides the vantage point. A result from anywhere else is not a verification of the thing you built.

The third pattern is the scaling gap, where the per-resource work is copied faithfully to a new network but the per-network resolution link is forgotten, because the link belongs to the network's lifecycle rather than the resource's and lives in a different team's templates. The new spoke gets its interface, the central zone already holds the record, and yet the spoke resolves publicly because nobody linked the zone to it. The cure is structural rather than procedural: the link is provisioned as part of standing up any network, automated alongside the network itself, so a new spoke is never born without its links to the shared zones. Teams that fix this once stop seeing the intermittent, network-specific resolution failures that otherwise recur every time the estate grows.

The fourth pattern is the deferred lock that never happens. Public access is left open during a migration with every honest intention of closing it once consumers move, the migration finishes, attention moves elsewhere, and the open public path quietly survives into production. There is no functional symptom, which is exactly why it persists, and it surfaces only when a review asks why a service with a fully built network path is still globally reachable. The cure is to attach an owner and a date to the open public path at the moment it is opened, and to treat closing it as a tracked task rather than a someday intention, with the public-access scan from the posture section as the backstop that catches it if the task slips.

What unifies these patterns is that each is prevented by the order and the structure of the procedure rather than by working more carefully within a sloppy procedure. Build in the right sequence, verify from the right place, automate the per-network link with the network, and treat the public-access close as a tracked step with the verification proving it. Do those four things and the patterns that cost teams the most time simply stop occurring, because the procedure is shaped so that the broken intermediate states are either impossible to ship or caught at the verification gate. That is the deeper reason the order of operations is worth taking seriously: it is not bureaucracy, it is the cheapest available defense against the exact mistakes this topic is famous for.

### Why is the order of operations so important for this setup?

Because two of the steps have hidden dependencies and several of the failure patterns come from doing things in the wrong sequence. Building the resolution chain before declaring success, verifying from inside the network, and closing public access only after the private path is proven each prevent a specific, common outage. The order is the defense, not a formality.

## Closing Verdict

A private endpoint is two things wearing one name. There is the endpoint resource, which creates a private interface and a Private Link connection, and there is the DNS chain, which makes the service name resolve to that interface from inside your network. The endpoint without the chain is the most common way this is done wrong, because the endpoint is the visible part, the part the portal celebrates as healthy, and the chain is the quiet part that does the actual work of keeping traffic private. The endpoint-plus-DNS rule is the whole lesson: a private endpoint without its Private DNS zone, its link, and its zone group still resolves publicly, so the DNS chain is not a follow-up to the setup, it is the setup.

Build it in the right order, endpoint then zone then link then group, decide deliberately whether to close the public path and close it once the private path is proven, handle on-premises resolution with a conditional forwarder to an in-network resolver, and verify from inside the network rather than from your laptop. Encode the whole thing as code so the endpoint and its record are born together and the broken intermediate states cannot ship. Do that, and private connectivity stops being a thing you hope is working and becomes a thing you can prove is working, service by service, network by network, with a resolution result and a connection test rather than an assumption. That proof is the real deliverable, and it is what separates a private endpoint that satisfies a security review from one that merely looks like it should.

## Frequently Asked Questions

### Q: What is the difference between a private endpoint and a service endpoint?

A private endpoint gives a service a private IP inside your virtual network and routes traffic to it over the Microsoft backbone, so the service is reachable by a private address and can be cut off from the public internet entirely. A service endpoint keeps the service on its public IP but adds an optimized route from your subnet and lets the service firewall trust traffic from that subnet, so the traffic still targets a public endpoint even though it does not traverse the public internet in the usual way. The practical difference is reach and isolation: a private endpoint can make the service private-only and is reachable from peered networks and on-premises, while a service endpoint is simpler and cheaper but cannot remove the public surface or extend to on-premises. The decision between them turns on whether you need true private addressing and a closed public path, which is the deciding factor worked through in the dedicated comparison article.

### Q: How many private endpoints do I need for a storage account?

One per sub-resource you actually use. A storage account fronts several distinct endpoints, including blob, file, queue, table, web, and the Data Lake dfs endpoint, and each is a separate hostname with its own private record. An endpoint created for the blob sub-resource privatizes blob traffic only; file traffic still resolves and connects publicly until you add an endpoint for the file sub-resource. So a workload using only blobs needs one endpoint, a workload using blobs and files needs two, and so on. Resist the urge to create endpoints for sub-resources you do not use, because each one is a private IP consumed, a record to maintain, and a small piece of standing complexity. Map your endpoints to the connection strings your application actually opens, confirm each sub-resource, and verify each one independently after creation rather than assuming one endpoint covers the account.

### Q: How do I find the right group id for my service?

The group id names the sub-resource the endpoint binds to, and it is service-specific. For storage it is blob, file, queue, table, web, or dfs depending on the sub-resource; for Azure SQL it is sqlServer; for Key Vault it is vault. The authoritative way to discover the available group ids for a resource is to query the resource's private link resources through the CLI or the portal's private endpoint creation blade, which lists the valid sub-resources for that specific service. Do not guess or copy from an old guide, because Azure adds sub-resources as services gain Private Link support, and a service may expose a group id today that did not exist when a tutorial was written. Confirm the current list against the service at the time you build, and match the group id to the sub-resource your application uses, since binding to the wrong one privatizes a path your workload never touches while leaving the real path public.

### Q: Does a private endpoint cost money and how is it billed?

Yes, private endpoints carry a cost, typically a charge for the time the endpoint exists plus a charge based on data processed through it. The exact rates change and vary by region, so treat any specific number you read as a value to confirm against the current Azure pricing for Private Link at the time you plan the deployment rather than as a fixed figure. The cost is generally modest relative to the security benefit for sensitive services, but it is not zero, and it scales with the number of endpoints, which is one more reason to create endpoints only for the sub-resources you actually use rather than reflexively privatizing everything. For a large estate the aggregate cost of many endpoints is worth modeling, especially when weighing a private endpoint against a service endpoint for a service where the simpler, cheaper service endpoint would satisfy the requirement. Verify current pricing before committing to a design that creates endpoints at scale.

### Q: Can a single private endpoint serve multiple virtual networks?

The endpoint itself lives in one subnet of one virtual network, but the private IP it exposes can be reached from other networks that have network connectivity to that subnet, such as peered networks in a hub-and-spoke topology or networks connected over a gateway. So one endpoint can serve many networks for connectivity, provided routing allows it. The piece that must extend to each consuming network separately is DNS: every network whose clients need to resolve the service name to the private IP must be linked to the Private DNS zone that holds the record. Connectivity and resolution are separate concerns here. A peered spoke can route to the endpoint's IP but will still resolve the name publicly unless its zone link exists. This is exactly why the centralized-zone, link-every-spoke design matters, because it makes one endpoint usable across the whole topology with consistent resolution rather than one that works only in its own network.

### Q: What happens to my connection string when I add a private endpoint?

Nothing changes in the connection string, and that is the intended design. The application keeps using the service's public fully qualified domain name exactly as before. What changes is resolution: with the DNS chain in place, that public hostname now resolves to the private IP from inside the network, because the public name CNAMEs into the privatelink zone your network holds. The redirection happens entirely in DNS, invisibly to the application. If you find yourself editing connection strings to point at private IP addresses or at privatelink hostnames directly, that is a sign the DNS chain is not set up correctly and you are working around the missing piece instead of using it. The correct end state is an unchanged connection string whose hostname simply resolves differently depending on whether the client sits inside a linked network or outside it, which is what makes private endpoints transparent to applications.

### Q: Can I use a private endpoint across subscriptions or tenants?

Yes. The private endpoint and the target service can live in different subscriptions, and with the right configuration in different tenants, because the endpoint binds to the service by resource ID and the Private Link connection is established across that boundary. When the endpoint and the service are in different subscriptions or owned by different teams, the connection may require manual approval rather than being auto-approved, which is the connection-approval flow. The service owner approves the pending connection request, after which the endpoint becomes usable. Cross-tenant scenarios add the requirement that the requester has the resource ID and the necessary permissions, and they almost always involve manual approval. The DNS side is unchanged by the boundary: the consuming network still needs the privatelink zone, the link, and the zone group, regardless of which subscription the service lives in, because resolution is a property of the consuming network rather than of the service's location.

### Q: When do I need to approve a private endpoint connection manually?

Manual approval applies when the person creating the endpoint does not have write access to the target service, which is common across subscription or team boundaries. In that case the endpoint is created in a pending state and the service owner must approve the connection before traffic flows. When you create an endpoint for a service you own and have permission on, the connection is auto-approved and immediately usable. You can see the connection state on either the endpoint or the service, and a connection stuck in pending is a signal that approval is outstanding rather than that something is broken. The approval is a deliberate control that lets a service owner decide who gets a private path to their service, which matters for shared services consumed by many teams. If your endpoint shows approved and healthy, approval is not your problem, and you should look at DNS for any resolution issue rather than at the connection state.

### Q: Do I need a network security group on the private endpoint subnet?

Network security group support for private endpoint traffic has evolved, and historically network policies on the subnet affected whether NSG and route table rules applied to the endpoint. Whether you need an NSG depends on your segmentation requirements: if your standard is to control traffic to every subnet with an NSG, you will want one here too, and you will need the subnet's network policies in a state that lets the NSG take effect for endpoint traffic. Read the current behavior of the private-endpoint network-policy setting for your subnet, because it governs this interaction and its default has changed over time. The practical guidance is to decide your segmentation posture first, then confirm the subnet setting supports it, rather than assuming the endpoint subnet behaves like an ordinary subnet. Do not disable network policies blindly, since that setting also interacts with how route tables and NSGs apply to the subnet.

### Q: How large should the private endpoint subnet be?

Each private endpoint consumes one private IP from the subnet, so the subnet must have enough addresses for every endpoint you plan to place there plus headroom for growth, on top of the addresses Azure reserves in every subnet. A dedicated subnet for private endpoints is the cleaner pattern than mixing endpoints into an application subnet, because it keeps address consumption predictable and the endpoint interfaces organized in one place. Size it for the number of endpoints you expect over the life of the network rather than the number you need today, since resizing a subnet later is disruptive. For an estate that privatizes many services, the endpoint count grows faster than people expect once the practice takes hold, so a subnet that felt generous can fill, and planning the address space with that growth in mind avoids a painful renumbering down the line. Reserve a block sized for the mature state of the environment, not its starting state.

### Q: Why does my application need no code change to use a private endpoint?

Because the private endpoint works at the DNS and network layer, not the application layer. The application resolves a hostname and connects to whatever address it gets back. Before the endpoint, that hostname resolves to a public IP; after the DNS chain is built, the same hostname resolves to the private IP from inside the network. The application is unaware that resolution changed, because it asked for a name and got an address, exactly as it always did. This transparency is the central design virtue of private endpoints. It means you can privatize an existing application's connectivity without touching its code, its configuration, or its connection strings, which removes an entire category of risk and coordination from the change. The only thing that must change is DNS, and the application simply follows DNS to the new address on its next connection. An application that requires a connection-string edit to use a private endpoint indicates a DNS chain that was not set up correctly.

### Q: How do I roll back a private endpoint safely?

The safest rollback re-opens the public path before removing anything private, which is the mirror image of the safe setup order. If you disabled public network access on the service, re-enable it first and confirm clients can reach the service publicly again, then remove the zone group, the record, and the endpoint if you are fully reverting. Doing it in that order means there is never a window where neither path works. The dangerous rollback removes the endpoint or the DNS record while public access is still disabled, which breaks all connectivity until you notice and re-enable the public path. Because the application's connection string never changed, re-enabling public access is usually enough to restore service immediately, since the hostname will resolve publicly again once the private record is gone or the network is unlinked. Plan rollback as part of the change, especially for the public-access step, so an unexpected problem has a fast, rehearsed reversal rather than an improvised one under pressure.

### Q: Can private endpoints and service firewalls be used together?

Yes, and they often should be during a transition. While you still have some consumers reaching a service over the public endpoint, you can keep public access enabled but scope the service firewall tightly so only known source addresses or subnets connect, then build private endpoints for the consumers you are migrating. As each consumer moves to the private path, you remove its public allowance, and once every consumer is private you disable public access entirely and the firewall becomes moot. The two controls are complementary rather than redundant: the firewall narrows the public surface during the migration window, and the private endpoint removes the need for that surface at all once the move is complete. The end state worth reaching is private-only access with public access disabled, but the firewall is the right tool for the interim, because it lets you tighten exposure incrementally instead of forcing a single risky cutover.

### Q: What is the difference between disabling public access and using a service firewall?

Disabling public network access closes the public endpoint entirely, so no public source can connect regardless of address; the service is reachable only over its private endpoints. A service firewall keeps the public endpoint open but restricts which sources may connect to it, so traffic still arrives at a public IP and is filtered by rule. The firewall narrows the public surface; disabling public access eliminates it. For a fully private posture you want public access disabled, because a firewall, however tight, still presents a public endpoint that depends on the rules staying correct. The firewall is the right control while you are migrating consumers and still need some public reach, and disabling public access is the right control once every consumer is private. Reaching the disabled state is the goal; the firewall is the safer interim while you get there, and confirming public access is disabled is the check that proves you arrived.

### Q: How does a private endpoint interact with hub-and-spoke routing?

The endpoint's private IP is reachable from any network with a route to it, which in a hub-and-spoke topology means peered spokes and the hub can all reach an endpoint placed in any of them, subject to the peering and any routing through a firewall. Many designs centralize endpoints in the hub or a shared services network so every spoke reaches them through peering, which keeps the endpoints in one managed place. Routing and resolution are separate, though: a spoke that can route to the endpoint still resolves the service name publicly unless it is linked to the privatelink zone. So the hub-and-spoke pattern that works is centralized zones linked to every spoke for resolution, plus routing that lets every spoke reach the endpoint IP. Get one without the other and you see the confusing partial failures where a spoke can reach the IP but does not know to use it, or knows the private IP but cannot route to it.

### Q: Do I need a private endpoint in every region for a global service?

It depends on where your clients are and how the service exposes itself. A private endpoint is regional in the sense that it lives in a subnet in a region, and clients in other regions reach it across the network if routing allows, which adds latency proportional to the distance. For a service consumed by clients in several regions, you may place an endpoint in each region near its clients to keep the private path short, or you may centralize endpoints and accept cross-region traversal for simplicity. The DNS records can be arranged so clients in each region resolve to the nearest endpoint. There is no universal rule; the deciding factors are latency tolerance, the cost of additional endpoints, and the complexity of regional DNS. Map your client populations to regions first, then decide whether the latency of a centralized endpoint is acceptable or whether per-region endpoints earn their additional cost and management overhead.

### Q: How do I give my deployment pipeline access to a locked-down service?

Once public access is disabled, anything that needs to reach the service must do so from inside a network with a private path, and that includes your deployment pipelines and any automation. The clean answer is a network-connected build agent: a self-hosted agent or runner that lives in a subnet with line of sight to the private endpoint, so pipeline steps resolve the service name privately and connect over the private path exactly as your applications do. Cloud-hosted agents on shared public infrastructure cannot reach a service whose public access is disabled, which is a common surprise that breaks pipelines the moment the service is locked down. Plan this before you disable public access, not after, because discovering that your deployment pipeline can no longer reach the service is an avoidable self-inflicted outage. The same applies to break-glass administrative access, which also needs a network-connected path to a service that no longer answers publicly.

### Q: Should I privatize a service that holds non-sensitive public data?

Not necessarily. A private endpoint adds cost, address consumption, DNS management, and the operational requirement that everything reaching the service has a network path to it, and those costs are only worth paying when the isolation matters. For a service holding genuinely non-sensitive data that is meant to be broadly reachable, a service firewall or even the default public access with good authentication may be the proportionate control, and the simpler option avoids the standing complexity a private endpoint introduces. Reserve private endpoints for the services where keeping traffic off the public internet is a real requirement, such as those holding sensitive data, those subject to regulatory constraints, or those whose exposure would be a meaningful risk. Applying private endpoints reflexively to everything produces an estate that is harder to operate without a corresponding security gain on the services that did not need it. Match the control to the sensitivity, and spend the complexity where it buys real isolation.
