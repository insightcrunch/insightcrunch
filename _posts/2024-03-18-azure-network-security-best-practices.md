---
layout: post
title: "Azure Network Security Best Practices"
page_title: "Azure Network Security Best Practices: Segmentation, Egress Filtering, Private Endpoints, DDoS Protection, and Monitoring for Defense in Depth"
date: 2024-03-18
categories: ["Technology"]
tags: ["Azure", "Network Security", "Security", "Networking", "Cloud Computing"]
excerpt: "Azure network security best practices for defense in depth: layer segmentation, egress filtering, private endpoints, DDoS protection, and flow log monitoring."
image: "/assets/images/blog/blog-41.webp"
reading_time: 63
author: "kevin-reeves"
last_updated: 2024-03-18
lang: en
---
Most network breaches in Azure do not start with a clever exploit. They start with a single control asked to do a job it was never built for. A team attaches a network security group to a subnet, allows the ports the application needs, and calls the workload secured. Then an attacker who lands inside that subnet moves laterally without resistance, exfiltrates data to an arbitrary internet host because nothing inspects outbound traffic, reaches a storage account over its public endpoint because no private path was ever configured, and rides out a volumetric flood that saturates the public IP because no perimeter protection was in place. Each of those failures is a different exposure, and no single rule on a single device closes more than one of them. Azure network security best practices exist precisely because the platform gives you distinct controls for distinct exposures, and a defensible posture comes from layering them rather than over-trusting one.

![Azure network security best practices defense in depth layering - Insight Crunch](/assets/images/blog/blog-41.webp)

This article assembles those controls into a posture you can defend in a design review. It treats segmentation, controlled egress, private access, DDoS protection, and monitoring as five separate layers, each implemented by a specific control and each closing an exposure the others leave open. The goal is not a checklist of features. The goal is a reasoning model: when you can name the exposure a control closes, you can tell whether your design has a gap, and you can explain to an auditor or an architect why each piece is present. By the end you will be able to look at a network and say which layer is missing and what an attacker would do with the gap.

## The defense-in-depth rule for Azure networks

The organizing principle of this article is one claim, and everything that follows defends it. No single network control in Azure is sufficient on its own, because each control was designed to address one class of exposure and is blind to the others. A network security group filters by IP address, port, and protocol; it cannot inspect outbound traffic by destination domain, it cannot absorb a volumetric flood, and it cannot remove a resource from the public internet. Azure Firewall inspects egress by fully qualified domain name; it does not micro-segment a subnet down to individual workloads, and it is not a substitute for taking a database off its public endpoint. Private endpoints pull a service onto your private address space; they say nothing about which subnets may reach that endpoint or what the workload behind it may call outbound. DDoS protection guards the perimeter; it has no opinion about lateral movement once traffic is inside. Security therefore comes from layering, and the defense-in-depth rule states it plainly: design five layers, give each its own control, and confirm that each layer closes the specific exposure the layer above does not.

The reason this rule matters in practice is that the failures engineers report are almost never a control that broke. They are a control that was never present. The subnet was segmented but egress was open. Egress was filtered but the database still answered on its public IP. The database was private but no flow log existed to show that an internal host was probing it. When you reason layer by layer, you stop asking whether a single device is configured correctly and start asking whether every exposure has an owner. That shift is the whole point of defense in depth, and it is the difference between a posture and a pile of rules.

### Why is layering more than just adding controls?

Layering is not stacking redundant copies of the same control. Each layer addresses a distinct exposure: segmentation limits lateral reach, egress filtering limits outbound abuse, private access removes public exposure, DDoS protection absorbs floods, and monitoring catches what slips through. Adding a second firewall does not close a segmentation gap.

### The InsightCrunch network defense-in-depth map

The artifact that anchors this article is a map of those five layers. Read it as a contract: each row names a layer, the Azure control that implements it, and the exact exposure that layer closes. If a row has no control assigned in your environment, that exposure is open, and the map tells you what an attacker does with it.

| Layer | Control that implements it | Exposure it closes | What happens if the layer is missing |
|-------|----------------------------|--------------------|---------------------------------------|
| Segmentation | NSGs at subnet and NIC, application security groups, subnet design | Unrestricted lateral movement between workloads | A foothold in one workload reaches every other workload in the network |
| Controlled egress | Azure Firewall with FQDN application rules, forced tunneling via UDR | Outbound traffic to arbitrary internet destinations | A compromised host exfiltrates data to any host or calls a command-and-control server |
| Private access | Private endpoints, Private Link, public network access disabled | Public exposure of PaaS data services | A storage account or database is reachable and brute-forced over its public endpoint |
| DDoS protection | Azure DDoS Network Protection or IP Protection on public IPs | Volumetric and protocol floods at the perimeter | A public endpoint is saturated and the application is unavailable |
| Monitoring | NSG flow logs, traffic analytics, Network Watcher | Blindness to what traffic actually flows | An intrusion or misconfiguration goes unseen because no record of traffic exists |

Each of the sections that follow takes one row, explains how the control works at the level you need to design it, shows the configuration that realizes it, names the misconfiguration that breaks it, and gives the command that proves the layer is in place. The primary keyword for this guide, Azure network security best practices, reduces to exactly this: own every row, leave no exposure unassigned.

## Layer one: segmentation that limits lateral movement

Segmentation is the first layer because it shapes the blast radius of everything that follows. When an attacker compromises a single virtual machine, a single container, or a single function, the only thing standing between that foothold and the rest of your estate is how the network is divided and what is allowed to cross the divisions. A flat network where every host can reach every other host on every port turns one compromise into a full estate compromise. A segmented network turns the same compromise into a contained incident that monitoring can catch before it spreads.

The control that implements segmentation in Azure is the network security group, supported by application security groups and a deliberate subnet design. An NSG is a stateful packet filter that evaluates traffic against an ordered set of rules, each rule matching on source, destination, port, and protocol, with an action of allow or deny. Stateful means that when an inbound rule permits a connection, the return traffic is allowed automatically without a matching outbound rule, and the reverse holds for outbound connections. You associate an NSG either with a subnet, where it governs every interface in that subnet, or with a network interface directly, where it governs only that one workload. When both associations exist, inbound traffic is evaluated by the subnet NSG first and then the NIC NSG, and outbound traffic is evaluated in the reverse order, so a packet must survive both sets of rules to pass.

### How does an NSG actually decide to allow or deny a packet?

An NSG processes rules in priority order from lowest number to highest, stops at the first match, and applies that rule's action. Default rules sit at the highest priority numbers and allow intra-VNet traffic and outbound internet while denying inbound internet. Your custom rules override the defaults because they carry lower priority numbers.

That default behavior is the first thing to internalize, because it explains the most common segmentation gap. Every NSG ships with a default rule named AllowVnetInBound that permits all traffic whose source and destination both fall inside the virtual network address space, across every port. The intent is convenience: workloads in the same network can talk without you writing a rule for each pair. The consequence is that segmentation does not exist until you override that rule. A subnet with an NSG attached but no custom deny rule for intra-VNet traffic is, from a lateral-movement standpoint, identical to a subnet with no NSG at all. Best practice is to treat the default allow-VNet rule as a starting point to be narrowed, not a safe baseline to be left alone.

Narrowing it is where application security groups earn their place. Writing per-IP rules in a network that scales is unmaintainable, because every new workload means editing rules and every IP change risks a stale rule that either blocks legitimate traffic or leaves a hole. An application security group is a named grouping of network interfaces that you reference in NSG rules instead of IP addresses. You define an ASG for the web tier, another for the application tier, and another for the data tier, then assign each workload's NIC to the appropriate group. Your NSG rules then read in terms of intent: allow the web ASG to reach the application ASG on the application port, allow the application ASG to reach the data ASG on the database port, and deny everything else between tiers. When you add a new web server, you assign its NIC to the web ASG and it inherits the policy with no rule edits. The segmentation logic stays readable as the estate grows.

A worked example makes the pattern concrete. Suppose a three-tier application with a web subnet, an app subnet, and a data subnet. The naive design attaches an NSG to each subnet allowing the ports each tier needs and relies on the implicit allow-VNet rule for everything else. The segmented design defines three application security groups and writes rules that permit only the legitimate tier-to-tier paths.

```bash
# Create application security groups for each tier
az network asg create --resource-group rg-prod --name asg-web --location eastus
az network asg create --resource-group rg-prod --name asg-app --location eastus
az network asg create --resource-group rg-prod --name asg-data --location eastus

# Allow the web tier to reach the app tier on the application port only
az network nsg rule create \
  --resource-group rg-prod --nsg-name nsg-app \
  --name AllowWebToApp --priority 100 \
  --direction Inbound --access Allow --protocol Tcp \
  --source-asgs asg-web --destination-asgs asg-app \
  --destination-port-ranges 8080

# Allow the app tier to reach the data tier on the database port only
az network nsg rule create \
  --resource-group rg-prod --nsg-name nsg-data \
  --name AllowAppToData --priority 100 \
  --direction Inbound --access Allow --protocol Tcp \
  --source-asgs asg-app --destination-asgs asg-data \
  --destination-port-ranges 1433

# Deny all other intra-VNet inbound traffic to the data tier
az network nsg rule create \
  --resource-group rg-prod --nsg-name nsg-data \
  --name DenyVnetInbound --priority 4000 \
  --direction Inbound --access Deny --protocol "*" \
  --source-address-prefixes VirtualNetwork \
  --destination-address-prefixes VirtualNetwork \
  --destination-port-ranges "*"
```

The deny rule at priority 4000 sits below your allow rules but above the default AllowVnetInBound rule at priority 65000, so it overrides the implicit allow while leaving your explicit tier paths intact. Now a compromise of a web server cannot reach the data tier directly, because the only inbound rule on the data NSG that matches VNet traffic is the allow from the app ASG; everything else hits the deny. Lateral movement is constrained to the legitimate application flow, which is exactly what segmentation should buy.

Subnet design carries its own segmentation decisions that NSGs cannot make for you. Place workloads with different trust levels in different subnets so that a single NSG governs a single trust boundary; mixing a public-facing web server and an internal batch processor in one subnet forces you to write rules that try to be two policies at once. Reserve subnets for the platform services that require their own, such as Azure Firewall, gateways, and Azure Bastion, because those services have fixed subnet-name and sizing requirements and refuse to deploy into a shared subnet. Size subnets with headroom but not excess, remembering that Azure reserves five addresses in every subnet for its own use, so a small subnet loses a meaningful fraction of its space to reservations. The discipline of one trust boundary per subnet is what makes the NSG rules legible later, and legible rules are rules an auditor can confirm and an engineer can change without fear.

### What segmentation does not do, and why that matters

The boundary of this layer is the start of the next one. Segmentation governs which workloads may talk to which other workloads and on which ports. It says nothing about where a workload may send traffic on the wider internet, because an NSG rule that allows outbound to the Internet service tag allows outbound to every internet address indiscriminately. You can narrow an NSG's outbound rules to specific IP ranges, and for a small set of fixed destinations that is reasonable, but the moment a legitimate destination is identified by domain name rather than a stable IP, the NSG is the wrong tool. Content delivery networks, software update services, and most software-as-a-service endpoints sit behind rotating IP ranges that an IP-based rule cannot track. That gap is the exposure the egress layer exists to close, and it is the single most common reason engineers who rely on NSGs alone end up with a network that segments internal traffic well and controls outbound traffic not at all. The NSG deep dive covers the rule-processing internals in more detail at [the network security group deep dive](/2023/09/25/azure-nsg-deep-dive/), and the design here builds directly on that model.

## Layer two: controlled egress that limits outbound abuse

The exposure this layer closes is the one most teams discover only after an incident. When a host inside your network is compromised, the attacker's next move is almost always outbound: exfiltrate the data they came for, or call back to a command-and-control server to receive further instructions. A network that allows unrestricted outbound traffic offers no resistance to either. The data leaves over HTTPS to a destination that looks no different from any other web request, and the callback succeeds because nothing inspects where outbound connections are going. Controlled egress is the layer that turns outbound traffic from an open door into a gated path, and the gate is a central firewall that filters by destination domain.

Azure Firewall is the managed control that implements this layer. It is a stateful, cloud-native firewall that you deploy into a dedicated subnet, typically in a hub virtual network that spoke networks route through. Its decisive capability for egress control is the application rule, which filters outbound traffic by fully qualified domain name rather than by IP address. An application rule that allows traffic to a named domain permits a workload to reach that destination and nothing else on the wider internet. This is the capability an NSG cannot provide, and it is the reason a firewall, not an NSG, owns the egress layer.

### Why can't an NSG filter egress by domain name?

An NSG matches on IP address, port, and protocol only. It has no awareness of the domain a connection is destined for, because the destination domain is not part of the IP and transport headers an NSG inspects; the domain lives in the TLS handshake or the HTTP host header. Filtering by domain requires a firewall that inspects that layer.

To route traffic through the firewall so that its rules actually apply, you steer egress with a user-defined route. By default, Azure sends internet-bound traffic straight out through the platform's implicit default route. A user-defined route on each workload subnet overrides that default, sending all outbound traffic to the firewall's private IP as the next hop. This is forced tunneling: the firewall becomes the only path to the internet, so no workload can bypass it. Without the route, the firewall exists but governs nothing, because traffic still takes the default path around it. The route is as essential as the rules.

```bash
# Route all outbound traffic from a workload subnet to the firewall
az network route-table create --resource-group rg-prod --name rt-spoke

az network route-table route create \
  --resource-group rg-prod --route-table-name rt-spoke \
  --name DefaultToFirewall \
  --address-prefix 0.0.0.0/0 \
  --next-hop-type VirtualAppliance \
  --next-hop-ip-address 10.0.1.4

# Associate the route table with the workload subnet
az network vnet subnet update \
  --resource-group rg-prod --vnet-name vnet-spoke \
  --name snet-app --route-table rt-spoke
```

With traffic flowing through the firewall, the application rules express your egress policy as a list of permitted destinations. A workload that must reach a specific package repository, a specific update service, and your own API is allowed those domains and denied everything else.

```bash
# Allow only specific outbound destinations by FQDN
az network firewall application-rule create \
  --resource-group rg-hub --firewall-name fw-hub \
  --collection-name AppEgress --priority 200 \
  --action Allow \
  --name AllowUpdates \
  --protocols Https=443 \
  --source-addresses 10.1.0.0/16 \
  --target-fqdns "*.ubuntu.com" "packages.microsoft.com" "api.internal.example.com"
```

The default behavior of Azure Firewall is to deny any traffic that no rule explicitly allows, so once you have an allow collection in place, everything outside the named domains is blocked. A compromised host can no longer exfiltrate to an arbitrary destination, because the only destinations it can reach are the ones you sanctioned. The callback to a command-and-control server fails at the firewall, and the failure is logged, which feeds the monitoring layer later in this article.

For destinations identified by IP rather than domain, such as a partner's fixed endpoint or an on-premises range reached over a private connection, network rules complement application rules. A network rule filters by IP, port, and protocol, the same dimensions an NSG uses, but centralized at the firewall where the rule applies to every subnet that routes through it. The division of labor is clean: application rules for domain-based egress, network rules for IP-based traffic that must traverse the firewall, and threat intelligence filtering layered on top to deny traffic to and from IP addresses and domains that Microsoft's feed flags as malicious. The firewall comparison at [Azure Firewall versus NVA versus NSG](/2023/10/30/azure-firewall-vs-nva-vs-nsg/) walks through when a third-party appliance fills a gap the firewall does not, but for the egress layer of a standard posture, Azure Firewall's application rules are the control that does the job.

### Where engineers get egress control wrong

The recurring mistake is treating egress as an afterthought once segmentation is done. A team segments the network carefully, attaches NSGs to every subnet, and then leaves outbound rules at the default allow-internet posture because the application needs to reach external services and writing IP rules for rotating ranges is painful. The result is a network that contains lateral movement well and contains exfiltration not at all. The fix is to make the firewall the default route for every workload subnet from the start, begin with a deny-all egress posture, and add application rules for each legitimate destination as the application's outbound needs become known. This inverts the default: instead of allowing everything and trying to block the bad, you allow only the known-good and deny the rest. The inversion is the entire value of the egress layer, and it is what separates a network that an attacker can quietly drain from one where exfiltration trips a denied-traffic log entry within seconds.

A second mistake is forgetting that the route is what activates the firewall. Teams deploy Azure Firewall, write thorough application rules, and then find that workloads still reach blocked destinations, because no user-defined route was ever attached to the workload subnets and traffic continues to take the platform default path. The confirming check is to inspect the effective routes on a workload's interface and verify that the 0.0.0.0/0 route points at the firewall's private IP, not at the internet. If the next hop for the default route is anything other than the firewall, the egress layer is not in effect regardless of how complete the rules are.

## Layer three: private access that removes public exposure

The third layer addresses an exposure the first two cannot touch. Segmentation governs traffic inside your network and egress governs traffic leaving it, but neither does anything about the fact that most Azure platform services answer on a public endpoint by default. A storage account, a SQL database, a Key Vault, and a Cosmos DB account each receive a public DNS name and a public IP, and unless you change the default, they are reachable from the internet. The access keys and authentication in front of those services are a control, but they are a single control, and a public endpoint means the service is exposed to credential stuffing, brute force, and any vulnerability in the authentication path, from anywhere on the internet, around the clock. Private access is the layer that takes the service off the public internet entirely so that the only path to it runs through your private network.

The control that implements this layer is the private endpoint, built on Azure Private Link. A private endpoint is a network interface in your virtual network that receives a private IP address from one of your subnets and maps to a specific instance of a platform service. Once the endpoint exists, the service is reachable at that private IP over the private network, and you disable public network access on the service so that its public endpoint stops answering. The combination is what closes the exposure: the private endpoint provides a private path, and disabling public access removes the public one. A private endpoint without public access disabled is a private path layered on top of a still-open public door, which is a common half-measure that does not actually close the exposure.

### Does a private endpoint on its own remove public exposure?

No. A private endpoint adds a private path to the service, but the public endpoint keeps answering until you separately disable public network access on the resource. Both steps are required: create the private endpoint for the private path, then set public network access to disabled so the public endpoint stops accepting connections.

The DNS behavior is where private endpoints most often go wrong, so it is worth understanding the resolution chain. When you create a private endpoint, the service's public DNS name must resolve to the private IP for workloads inside the network, while continuing to resolve correctly for anything that legitimately remains public. Azure handles this with a private DNS zone specific to the service, such as the zone for blob storage or for the SQL database service. You link that private DNS zone to your virtual network, and a record in the zone maps the service's name to the private endpoint's IP. A workload in the linked network resolves the service name, gets the private IP, and connects over the private path. If the private DNS zone is missing or not linked to the network, the name resolves to the public IP, the connection attempts to reach a public endpoint you have disabled, and it fails. The DNS chain is the part that breaks; the configuration steps are mechanical.

```bash
# Create a private endpoint for a storage account's blob service
az network private-endpoint create \
  --resource-group rg-prod --name pe-storage \
  --vnet-name vnet-spoke --subnet snet-data \
  --private-connection-resource-id "/subscriptions/<sub>/resourceGroups/rg-prod/providers/Microsoft.Storage/storageAccounts/stprod" \
  --group-id blob \
  --connection-name pe-storage-conn

# Create and link the private DNS zone so the name resolves privately
az network private-dns zone create \
  --resource-group rg-prod --name "privatelink.blob.core.windows.net"

az network private-dns link vnet create \
  --resource-group rg-prod --zone-name "privatelink.blob.core.windows.net" \
  --name dns-link-spoke --virtual-network vnet-spoke --registration-enabled false

# Disable public network access so the public endpoint stops answering
az storage account update \
  --resource-group rg-prod --name stprod \
  --public-network-access Disabled
```

The third command is the one that actually closes the exposure, and it is the one teams skip. Creating the private endpoint and linking DNS gives you a working private path, and it is tempting to stop there because the application now connects privately and everything works. But the public endpoint is still answering, so the service is still exposed, and an attacker who never touches your network can still reach it over the internet. Disabling public network access is what removes the public door. After it runs, the service answers only on the private endpoint, and a connection attempt from outside the network fails at the network layer before authentication is ever reached.

Verifying that the exposure is closed takes two checks rather than one. First, confirm from inside the network that the service name resolves to the private IP, which proves the DNS chain works and the private path is live. Second, confirm from outside the network, or by inspecting the service's configuration, that public access is disabled, which proves the public door is shut. A posture review that checks only the first misses the most common gap, because the private path can be perfect while the public endpoint remains wide open. The end-to-end setup, including the DNS resolution chain across hub-spoke topologies, is covered at [the end-to-end private endpoint setup guide](/2023/05/01/configure-private-endpoints/), and the pattern there is the one to follow for every data service that supports Private Link.

The principle of least privilege applies to this layer in the form of network reachability. A private endpoint makes the service reachable from the network it lives in, but you can and should constrain which subnets reach the endpoint using the segmentation layer's NSG rules. The data tier's NSG should allow inbound to the private endpoint's subnet only from the application tier that legitimately uses the service, denying every other subnet. This is the two layers working together: the private endpoint removes public exposure, and segmentation ensures that even inside the network, only the workloads that need the service can reach it. Least privilege on the network is not a single setting; it is the cumulative effect of each layer narrowing reach to exactly what the application requires.

## Layer four: DDoS protection at the perimeter

The fourth layer protects the one part of your network that must remain public. Even a posture that pushes data services onto private endpoints keeps some public-facing entry points: the application gateway or load balancer that fronts a web application, the public IP of a service that customers reach directly, the DNS name that resolves to your front door. Those public IPs are exposed to a class of attack the inner layers cannot address, because the attack does not try to get inside or move laterally. A distributed denial-of-service flood simply overwhelms the public endpoint with traffic until legitimate requests cannot get through. Segmentation, egress control, and private endpoints all assume the traffic in question is trying to reach something specific; a volumetric flood is trying to reach nothing except the saturation point. DDoS protection is the layer that absorbs it at the perimeter.

Azure provides DDoS protection in three forms, and knowing which one applies is the substance of this layer. Every public IP in Azure receives DDoS infrastructure protection at no cost and with no configuration, which mitigates the largest volumetric attacks at the platform level to protect Azure itself. This baseline protects the platform but does not give you tuned protection, telemetry, or guarantees for your specific application. Above it sit two paid tiers. DDoS Network Protection is enabled by creating a protection plan and associating it with a virtual network, after which every public IP in that network receives adaptive, application-tuned mitigation, attack telemetry, alerting, rapid-response support, and cost protection against scale-out charges incurred during an attack. DDoS IP Protection is a newer per-public-IP model that delivers the same core mitigation engine on individual public IP addresses without requiring a network-wide plan, which suits smaller deployments that protect a handful of endpoints.

### Which DDoS protection tier should I choose?

Choose IP Protection when you protect a small number of public IPs, since it is billed per protected address and avoids the fixed plan cost. Choose Network Protection when you protect many public IPs in a virtual network, since its plan covers a block of addresses and adds value-added features. The crossover sits at roughly fifteen public IPs, so verify current pricing before deciding.

The deciding factor between the two paid tiers is the count of public IPs and the value of the added features. Network Protection carries a fixed monthly plan cost that includes protection for a block of public IP resources, with additional resources charged per address, and it bundles features that matter during an actual attack: rapid-response engineering support, cost protection that shields you from the autoscale bill an attack can trigger, and a discount on the Web Application Firewall when an application gateway sits in the protected network. IP Protection is billed per protected public IP with no plan floor, which makes it the cheaper choice when you are protecting only a few endpoints. The published guidance places the crossover near fifteen public IP resources, below which IP Protection tends to cost less and above which the plan-based Network Protection tends to win, but pricing changes, so confirm the current rates against the official pricing page before you commit a design to one tier.

```bash
# Create a DDoS Network Protection plan and attach it to a virtual network
az network ddos-protection create \
  --resource-group rg-hub --name ddos-plan-prod --location eastus

az network vnet update \
  --resource-group rg-hub --name vnet-hub \
  --ddos-protection-plan ddos-plan-prod --ddos-protection true
```

What DDoS protection does not do marks the boundary of this layer clearly. It absorbs volumetric and protocol floods aimed at the network and transport layers, and the auto-tuned mitigation policies adapt to your traffic baseline so that legitimate spikes are not mistaken for attacks. It does not inspect the content of application-layer requests, so an attack that sends well-formed but malicious HTTP requests at the application is a job for the Web Application Firewall on an application gateway or front door, not for DDoS protection. The two complement each other at the perimeter: DDoS protection absorbs the flood that tries to saturate the pipe, and the Web Application Firewall filters the malicious request that tries to exploit the application. A perimeter posture wants both, and the DDoS layer is specifically the volumetric and protocol defense.

The common misconfiguration here is assuming the free infrastructure protection is the same as the paid tiers. It is not. Infrastructure protection defends the Azure platform's capacity and will mitigate the largest attacks, but it gives you no telemetry about an attack on your application, no tuned mitigation for your traffic profile, no alerting when an attack begins, and no cost protection when the attack drives autoscale. A team that believes it is protected because Azure mitigates DDoS at the platform level discovers during an incident that it has no visibility and no support path. The best practice is to enable a paid tier on the public IPs that matter, choose the tier by the IP count and feature value, and confirm that protection is reporting telemetry so that an attack is visible rather than merely absorbed somewhere in the platform.

## Layer five: monitoring that ends the blindness

The fifth layer is the one that makes the other four observable. A network can be segmented, its egress filtered, its data services private, and its perimeter defended, and still be a black box in which an intrusion or a misconfiguration goes unseen because no record of actual traffic exists. Monitoring closes the exposure of blindness. It does not block anything; it records what flows, surfaces what is anomalous, and gives you the evidence to confirm that the other layers are doing their jobs and to detect when they are not. A posture without monitoring is a posture you cannot verify, which is to say it is a posture you are merely hoping is correct.

The controls that implement this layer are NSG flow logs, traffic analytics, and Network Watcher. NSG flow logs record every flow that an NSG evaluates, capturing the source and destination IP and port, the protocol, the direction, and whether the flow was allowed or denied. The current generation of flow logging, the virtual network flow log, records at the network level and supersedes the older per-NSG flow log, but the principle is the same: a durable record of which connections were attempted and what the network decided about them. The logs land in a storage account and become the raw evidence of network behavior. On their own they are voluminous and hard to read, which is where traffic analytics comes in. Traffic analytics processes flow logs into an analyzed view: the top talkers, the traffic between subnets and regions, the flows that were denied, and the connections to and from the public internet. It turns a flood of flow records into a picture of how the network actually behaves, which is what you need to spot the anomaly that signals a problem.

### What can flow logs reveal that the other layers cannot?

Flow logs show traffic that the other controls allowed and traffic they denied, which exposes both intrusions and misconfigurations. A burst of denied egress flows to an unknown destination signals a compromised host trying to call out. A surprising allowed flow between two subnets that should be isolated reveals a segmentation rule that is missing or too broad.

The diagnostic value becomes concrete in the scenarios engineers actually hit. A flow log that shows a workload making repeated denied outbound connections to an unfamiliar domain is the egress layer catching an exfiltration attempt, and the log is how you learn it happened. A flow log that shows allowed traffic between two subnets that your design says should never communicate reveals a segmentation gap, an NSG rule that is too permissive or missing, before an attacker exploits it. A flow log that shows inbound connection attempts to a private endpoint's subnet from a subnet that has no business reaching the data tier reveals that the least-privilege reachability you intended is not actually enforced. In each case, the monitoring layer is not preventing the problem; it is making the problem visible so that you can fix the layer that should have prevented it. That feedback loop, from observed traffic back to corrected control, is what turns a static configuration into a posture you can trust.

Network Watcher rounds out the layer with the diagnostic tools that answer specific questions about a path. The IP flow verify tool tells you whether a given packet, from a given source to a given destination on a given port, would be allowed or denied and which rule decides, which collapses an hour of rule-reading into one query. The next-hop tool tells you where a packet from a given interface to a given destination actually goes, which is how you confirm that the egress layer's user-defined route is steering traffic to the firewall rather than out the default path. The connection troubleshoot tool tests an actual path end to end and reports where it breaks. These are the tools you reach for when a layer appears not to be working, and they turn the question of why traffic is or is not flowing from a guess into a measurement.

```bash
# Enable a virtual network flow log to a storage account, with traffic analytics
az network watcher flow-log create \
  --resource-group rg-prod --name flowlog-prod \
  --location eastus \
  --vnet vnet-spoke \
  --storage-account stflowlogs \
  --traffic-analytics true \
  --workspace "/subscriptions/<sub>/resourceGroups/rg-prod/providers/Microsoft.OperationalInsights/workspaces/law-prod" \
  --interval 10

# Verify whether a specific flow would be allowed or denied
az network watcher test-ip-flow \
  --resource-group rg-prod --vm vm-app01 \
  --direction Outbound --protocol TCP \
  --local 10.1.2.4:443 --remote 203.0.113.10:443
```

The misconfiguration that undermines this layer is enabling the logs and never analyzing them. Flow logs that accumulate in a storage account but feed no analytics workspace and trigger no alert are evidence that nobody reads, which is the same as no evidence at all when an incident happens. The best practice is to route flow logs into traffic analytics tied to a Log Analytics workspace, build alerts on the signals that matter such as a spike in denied egress or unexpected internet-bound traffic from an internal subnet, and treat the analyzed view as a regular operational review rather than a forensic resource you open only after a breach. Monitoring earns its place in the defense-in-depth map only when it changes behavior, and it changes behavior only when someone or something is watching the analyzed output.

## The counter-reading: why NSGs alone are not a security posture

The most persistent wrong belief about Azure network security is that a network security group is the security. It is an understandable belief, because the NSG is the first control most engineers meet, it is free, it attaches in seconds, and it visibly blocks traffic, so it feels like protection. The trouble is that the NSG addresses exactly one of the five exposures in the defense-in-depth map, and a posture built on it alone leaves the other four open. Engaging this counter-reading directly is worth doing, because the gap it creates is the gap most real networks have.

Walk through what an NSG-only posture actually defends. It can limit lateral movement, provided you override the default allow-VNet rule, so the segmentation layer is covered if you do the work. From there the gaps open. The NSG cannot filter egress by domain, so outbound traffic to arbitrary internet destinations is either fully open or pinned to brittle IP rules that break the moment a destination's address rotates; the egress layer is missing. The NSG cannot remove a service from the public internet, so a storage account or database reached over its public endpoint stays exposed no matter how the NSG is written, because the NSG governs traffic to network interfaces in your subnets, not traffic to a platform service's public endpoint that lives outside them; the private access layer is missing. The NSG cannot absorb a volumetric flood, because a flood that saturates a public IP overwhelms capacity rather than violating a rule; the DDoS layer is missing. The NSG produces flow logs, which is genuine monitoring value, but logs without analysis and alerting are not the monitoring layer, only its raw material. Four of five layers are absent or incomplete, and the network feels secure because the one visible control is doing its visible job.

The fix is not to abandon the NSG; it is to stop asking it to be the whole posture. The NSG owns the segmentation layer and does it well. The other layers get their own owners: Azure Firewall for egress, private endpoints for private access, a DDoS protection plan for the perimeter, and flow logs plus traffic analytics for monitoring. Each control does the one thing it was built for, and the map confirms that every exposure has an owner. When an architect asks in a design review why the NSG is not enough, the answer is precise: the NSG closes lateral movement, and here are the four other exposures with the four other controls that close them. That answer is the difference between a defensible posture and a hopeful one.

This layering is the network face of Zero Trust, which assumes breach and verifies every access rather than trusting a perimeter. A Zero Trust network does not assume that traffic inside the boundary is safe, which is exactly why segmentation constrains lateral movement and monitoring watches internal flows; it does not assume that a service should be reachable just because a request authenticates, which is why private endpoints and least-privilege reachability narrow the path. The principles map onto these layers directly, and [the Azure Zero Trust architecture explainer](/2024/02/05/azure-zero-trust-architecture/) develops the broader model across identity, network, and data, of which the network controls here are the network slice.

## Applying least privilege across the whole network

Least privilege is usually discussed as an identity principle, the idea that a user or workload should hold only the permissions it needs. The network has its own version, and a strong posture applies it as deliberately as the identity version. Network least privilege means that each workload can reach only the destinations it legitimately needs, on only the ports it needs, in only the directions it needs, and nothing more. The five layers each enforce a slice of this, and the cumulative effect is a network where reach is narrowed to the application's actual requirements rather than left open to whatever the defaults permit.

Inbound least privilege is the segmentation layer's job. A workload should accept connections only from the specific sources that legitimately initiate them, expressed through application security groups so the rules stay readable. The data tier accepts inbound only from the application tier, the application tier only from the web tier, and the web tier only from the load balancer or gateway that fronts it. Every other inbound path is denied, so a foothold anywhere in the network cannot reach a tier it has no legitimate reason to reach. Outbound least privilege is the egress layer's job. A workload should reach only the external destinations it needs, expressed as firewall application rules for domains and network rules for fixed IPs, with everything else denied by the firewall's default. A workload that needs to reach one package repository and one internal API is allowed exactly those and nothing else, so a compromise cannot exfiltrate to an arbitrary destination.

Reachability least privilege ties the layers together at the private endpoint. When a data service lives behind a private endpoint, the endpoint is reachable from the network, but least privilege says only the subnets that use the service should reach it. You enforce that with the segmentation layer, writing an NSG rule on the endpoint's subnet that allows inbound only from the application tier's application security group and denies the rest. Now the service is private, removed from the public internet, and reachable inside the network only from the one tier that uses it. Three layers compose into a single least-privilege outcome: private access removes public exposure, segmentation narrows internal reach, and the combination means the data service answers only to exactly the workloads that need it.

The discipline that makes network least privilege durable is starting from deny and adding only what the application proves it needs. A network that starts open and tries to close gaps over time accumulates exceptions and never reaches a clean state, because nobody can safely remove a rule they are unsure about. A network that starts closed and opens a path only when a real requirement appears stays minimal, because every open path has a known reason. This is the same inversion the egress layer relies on, applied to the whole network: default deny, explicit allow, documented reason. It is more work at the start and far less work and far less risk over the life of the network.

## Verifying the posture layer by layer

A posture you cannot verify is a posture you do not have. Each layer in the map comes with a confirming check, and running those checks turns a configuration you believe is correct into one you have demonstrated is correct. Verification is also how you catch the silent gaps, the cases where a layer appears present because its control is deployed but is not actually in effect because a route is missing, a DNS zone is unlinked, or a public endpoint was never disabled. Treat the following as the verification pass you run before declaring a network secured and again on a schedule afterward.

For the segmentation layer, the check is whether the paths you intend to deny are actually denied. Network Watcher's IP flow verify answers this directly: pick a source and destination that your design says should not communicate, ask whether a packet between them is allowed, and confirm the answer is deny and that the deciding rule is the one you expect. A common surprise is discovering that the implicit allow-VNet rule is still deciding the flow because no explicit deny was ever written, which means segmentation was assumed rather than enforced. Run the check for each tier boundary that should be closed.

```bash
# Confirm the web tier cannot reach the data tier on the database port
az network watcher test-ip-flow \
  --resource-group rg-prod --vm vm-web01 \
  --direction Outbound --protocol TCP \
  --local 10.1.1.4:50000 --remote 10.1.3.5:1433
```

For the egress layer, the check is whether outbound traffic actually traverses the firewall and whether undesired destinations are blocked. Network Watcher's next-hop tool confirms the route: ask where a packet bound for an internet address goes from a workload's interface, and confirm the next hop is the firewall's private IP rather than the internet. Then test an actual outbound connection to a destination that should be blocked and confirm it fails and appears as a denied flow in the firewall logs. If the next hop is the internet, the user-defined route is missing or wrong and the firewall governs nothing.

For the private access layer, the check has two parts, because the layer has two requirements. From inside the network, resolve the service's name and confirm it returns the private IP, which proves the private endpoint and DNS chain work. From the service's configuration, confirm public network access is disabled, which proves the public endpoint is closed. A frequent gap is a perfect private path with public access still enabled, so checking only the resolution misses the exposure. The two-part check is what catches it.

```bash
# From a workload inside the network, confirm private resolution
nslookup stprod.blob.core.windows.net
# Expect the answer to be a private IP from the endpoint's subnet, not a public address

# Confirm public network access is disabled on the service
az storage account show \
  --resource-group rg-prod --name stprod \
  --query "publicNetworkAccess" -o tsv
# Expect: Disabled
```

For the DDoS layer, the check is whether the public IPs that matter are covered by a paid tier and reporting telemetry, not merely sitting under the free infrastructure protection. Inspect the protection status of each public-facing IP and confirm it shows the protection plan or IP Protection you intended. For the monitoring layer, the check is whether flow logs are flowing into traffic analytics and whether alerts exist on the signals that matter; an enabled flow log with no analytics workspace and no alert is monitoring in name only. Confirm the flow log is enabled, points at a workspace, and that you can see analyzed traffic in the workspace, then confirm an alert fires on a test condition such as a spike in denied flows. When all five checks pass, the posture is verified rather than assumed, and the verification record is itself the evidence an auditor wants.

## Making the posture auditable and repeatable

A posture configured by hand in the portal is correct exactly once, at the moment someone finishes clicking. It drifts the first time a teammate makes an undocumented change, and it is unauditable because there is no single artifact that states what the network security configuration is supposed to be. Infrastructure as code solves both problems: the configuration becomes a reviewed, version-controlled artifact that is the source of truth, drift becomes detectable by comparing the deployed state to the code, and an audit becomes a reading of the templates rather than a tour of the portal. The five layers all express cleanly as code, and expressing them that way is what makes the posture durable past its first day.

Encode each layer as a module so the structure of the code mirrors the structure of the map. A networking module defines the virtual network, the subnets with one trust boundary each, and the route tables that steer egress to the firewall. A segmentation module defines the network security groups, the application security groups, and the rules that express tier-to-tier least privilege. An egress module defines the firewall and its application and network rule collections. A private access module defines the private endpoints, the private DNS zones and their links, and the public-access-disabled setting on each service. A perimeter module defines the DDoS protection plan and its association, and a monitoring module defines the flow logs, the Log Analytics workspace, the traffic analytics configuration, and the alert rules. A small Bicep fragment shows the shape, encoding the segmentation rule from earlier as reviewable code rather than a one-time command.

```bicep
resource nsgData 'Microsoft.Network/networkSecurityGroups@2023-09-01' = {
  name: 'nsg-data'
  location: location
  properties: {
    securityRules: [
      {
        name: 'AllowAppToData'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceApplicationSecurityGroups: [ { id: asgApp.id } ]
          destinationApplicationSecurityGroups: [ { id: asgData.id } ]
          destinationPortRange: '1433'
          sourcePortRange: '*'
        }
      }
      {
        name: 'DenyVnetInbound'
        properties: {
          priority: 4000
          direction: 'Inbound'
          access: 'Deny'
          protocol: '*'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: 'VirtualNetwork'
          destinationPortRange: '*'
          sourcePortRange: '*'
        }
      }
    ]
  }
}
```

The auditability payoff is concrete. When an auditor asks how the data tier is protected, the answer is a file: this module shows the private endpoint, this setting disables public access, this NSG rule restricts reachability to the application tier, and this flow log records every attempt. When a change is proposed, it arrives as a pull request that a reviewer reads against the map, asking whether it opens an exposure before it merges rather than after it breaks something. When you suspect drift, a what-if deployment compares the code to the live state and reports the difference, so an out-of-band portal change surfaces as a discrepancy rather than hiding until an incident. Repeatability follows for free: the same templates stamp out a second environment with the same posture, so staging and production are secured identically rather than diverging because someone configured them by hand on different days. To build and reproduce these layered controls hands-on, [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), which carries tested Bicep, Terraform, and CLI examples for each layer so you can practice the configuration against a live environment before you apply it to your own.

## Recurring patterns engineers report, mapped to their layer

The value of the defense-in-depth map is that it turns the incidents engineers actually report into a small set of recognizable patterns, each pointing at the layer that was missing. The following patterns recur across community forums and incident reviews, and naming the layer for each is how you move from firefighting a symptom to closing the exposure.

The lateral-movement pattern starts with a single compromised workload, often a web server reachable from the internet through a vulnerable component. In a flat network, the attacker who lands on that web server can immediately reach the application servers and the database, because nothing inside the network restricts traffic between subnets. The incident review finds that NSGs were attached but the implicit allow-VNet rule was never overridden, so internal traffic flowed freely. The missing layer is segmentation, and the fix is the application-security-group tier model that permits only legitimate tier-to-tier paths and denies the rest. The pattern is so common because attaching an NSG feels like segmenting, even though without an explicit intra-VNet deny it does not.

The exfiltration pattern starts after a compromise and shows a workload sending unexpected outbound traffic to an unfamiliar destination, sometimes a data sink and sometimes a command-and-control server. The network allowed it because outbound rules were left at the default allow-internet posture, on the reasoning that the application legitimately needs to reach external services and IP-based rules for rotating ranges were too painful to maintain. The missing layer is controlled egress, and the fix is to make Azure Firewall the default route for the workload subnets, start from deny-all egress, and allow only the specific domains the application needs by fully qualified domain name. The pattern is the direct consequence of treating egress as someone else's problem after segmentation is done.

The public-exposure pattern shows a data service, usually a storage account or a database, receiving connection attempts from internet addresses that have no business reaching it, sometimes credential-stuffing attempts and sometimes successful access after a key leaked. The service was reachable because it answered on its public endpoint, which is the default, and the team relied on access keys as the only control. The missing layer is private access, and the fix is a private endpoint to provide a private path plus disabling public network access so the public endpoint stops answering. The pattern persists because the application works fine over the public endpoint, so nothing prompts the team to close it until an incident does.

The half-private pattern is a subtler variant of the previous one and worth calling out separately. The team created a private endpoint, the application connects privately, and everyone believes the service is off the internet, but public network access was never disabled, so the public endpoint is still answering alongside the private path. The service is exposed exactly as before; the private endpoint added a path without removing one. The missing step is the public-access-disabled setting, and the diagnostic is the two-part verification: confirm private resolution and separately confirm public access is disabled. This pattern catches careful teams precisely because they did most of the work.

The saturation pattern shows a public-facing endpoint becoming unavailable under a flood of traffic that is not trying to exploit anything, just to overwhelm. The team assumed the free infrastructure protection covered them, and it did mitigate the largest platform-level attacks, but it gave no tuned protection, no telemetry, and no support path for an attack against their specific application. The missing layer is perimeter DDoS protection in a paid tier, and the fix is to enable Network Protection or IP Protection on the public IPs that matter, chosen by IP count and feature value. The pattern recurs because the free baseline is real but is not the same as protecting your application, and the difference is invisible until an attack arrives.

The blindness pattern is the one that hides all the others. An intrusion or a misconfiguration persists undetected because no analyzed record of network traffic exists. Sometimes flow logs were never enabled; more often they were enabled but flow into a storage account that nobody reads, with no traffic analytics and no alerts. The missing layer is monitoring that is actually watched, and the fix is to route flow logs into traffic analytics tied to a workspace and alert on the signals that matter. The flip side of this pattern is the good outcome: a flow log that reveals unexpected traffic, a denied-egress spike or an allowed flow between subnets that should be isolated, and lets the team close the gap before it is exploited. Monitoring is the layer that converts the other four from hopeful to verifiable.

## The order to build the layers

When you are securing a network from scratch or hardening an existing one, the order of operations matters, because some layers depend on others and building in the wrong order produces rework. Start with the virtual network and subnet design, since one trust boundary per subnet is the foundation that segmentation rules attach to and that every other layer assumes. Reserve the platform subnets for the firewall, gateways, and Bastion at this stage, because retrofitting them into a network that already allocated their address space is disruptive.

Build segmentation next, defining application security groups and the tier-to-tier NSG rules that override the implicit allow-VNet rule. Doing this early means that as you add the remaining layers, internal traffic is already constrained, so a mistake in a later layer is contained rather than estate-wide. Build egress third, deploying the firewall, attaching the user-defined routes that force traffic through it, and starting from a deny-all posture that you open destination by destination. Egress depends on the subnet and route design being in place, which is why it follows segmentation rather than leading.

Build private access fourth, creating private endpoints for the data services, linking the private DNS zones, and disabling public access. This layer interacts with segmentation, because you will write NSG rules to restrict which subnets reach each endpoint, so having segmentation already built makes the reachability rules natural to add. Build the perimeter DDoS protection for the public-facing IPs, choosing the tier by IP count. Build monitoring last in sequence but treat it as always-on from that point forward, enabling flow logs, wiring traffic analytics, and setting alerts, because the moment the other layers are in place is the moment you want visibility into whether they behave as designed. Finally, capture the whole configuration as infrastructure as code so the posture you just built is the posture that persists, reviewable and reproducible rather than dependent on the memory of whoever clicked through the portal.

## A request's journey through the five layers

To see how the layers compose, follow two requests through a fully built posture: one legitimate, one malicious. The trace makes concrete how each control sees only its slice and why the slices together produce a defensible whole.

A legitimate request begins at the internet, aimed at the public IP of the application gateway that fronts the web tier. The DDoS layer sees it first, evaluating the traffic against the auto-tuned mitigation policies; a single well-formed request is nowhere near the volumetric threshold, so it passes untouched, and only a flood would trigger mitigation here. The request reaches the gateway, which terminates the connection and forwards to a web server in the web subnet. The segmentation layer governs that forward: the web subnet's NSG allows inbound from the gateway's source on the application port, so the packet is permitted. The web server processes the request and needs data, so it opens a connection to an application server in the app subnet. Segmentation governs again: the app subnet's NSG allows inbound from the web application security group on the application port and denies everything else, so the legitimate path is permitted while any other source would be denied. The application server needs the database, opens a connection to the data subnet, and the data NSG allows inbound from the app application security group on the database port only. The database itself sits behind a private endpoint, so the connection resolves the database name to its private IP through the linked private DNS zone and reaches it over the private path; the public endpoint is disabled and plays no part. The data returns along the same stateful paths, and the monitoring layer records each allowed flow in the flow log, building the evidence that the request behaved as designed. Every layer saw the request, each permitted its slice, and the request completed.

Now a malicious request, from an attacker who has compromised the web server through an application vulnerability and wants to exfiltrate the database. The attacker first tries to reach the database directly from the web server, skipping the app tier. Segmentation stops this: the data NSG allows inbound only from the app application security group, and the web server is not in it, so the connection is denied, and the denied flow appears in the log where monitoring can surface it. The attacker pivots to the legitimate path, compromising the app tier through the web tier's allowed connection, and now can reach the database the way the application does. This is where the inner layers have done their job of slowing and channeling the attacker, and the next layers take over. The attacker tries to exfiltrate the data to an external server, opening an outbound connection to their own host. The egress layer stops this: the workload's traffic is forced through the firewall by the user-defined route, the firewall's application rules allow only the specific domains the application needs, the attacker's destination is not among them, and the connection is denied and logged. The attacker tries to reach the database's public endpoint as an alternative path, perhaps with a stolen key, but the private access layer closed that door: public network access is disabled, so the public endpoint does not answer at all. At each turn the attacker meets a layer that closes the exposure the previous layer left open, and the monitoring layer records the denied attempts, giving the team the signal that an intrusion is in progress. No single control stopped the attack; the layering did, which is the defense-in-depth rule demonstrated end to end.

The trace also shows why a missing layer is fatal in a way that a weakened layer is not. If egress were missing, the attacker's exfiltration would succeed the moment they reached data they could read, regardless of how good segmentation was, because nothing would inspect the outbound connection. If private access were missing, the public-endpoint path would work, regardless of how good egress was, because the attacker would not need to traverse your network at all. Each missing layer is a complete bypass of the others for the exposure it owns, which is why the map insists that every row have an owner rather than treating the controls as interchangeable strength to be piled where it is easy.

## Hardening an existing network without breaking it

Most engineers apply these practices not to a greenfield network but to one already carrying production traffic, where a wrong move breaks a working application. The layers can be added to a live network safely if you add them in an order that fails closed only against traffic that should not exist, and if you use the monitoring layer to see what you are about to block before you block it.

Begin by turning on monitoring first, even though it is last in the build order for a new network, because on an existing network you need to see the real traffic before you constrain it. Enable flow logs and traffic analytics, and let them run long enough to capture the actual communication patterns: which subnets talk to which, what outbound destinations the workloads reach, and which services are accessed over public endpoints. This analyzed view is your map of what the application actually does, as opposed to what the documentation or the team's memory says it does, and it is what lets you write segmentation and egress rules that permit the real traffic rather than guessing.

With the traffic understood, add segmentation in audit before enforce. Write the tier-to-tier allow rules based on the observed flows, but before adding the intra-VNet deny that closes the rest, confirm from the flow logs that no legitimate traffic falls outside your allow rules. Then add the deny and watch the logs for newly denied flows that turn out to be legitimate, ready to add an allow rule if a real path was missed. This is the safe way to segment a live network: the allow rules go in first and harmlessly, the deny goes in only once you have evidence it will not break anything, and monitoring catches the surprise. Add egress the same way, routing traffic through the firewall and starting with the observed destinations allowed, then tightening, watching denied-egress logs for legitimate destinations you missed. Add private endpoints for data services with public access still enabled at first so the application keeps working over either path, confirm the application has switched to the private path by watching the flow logs and the service's connection telemetry, and only then disable public access, which is the irreversible-feeling step you take last and with evidence. Add DDoS protection at any point, since it does not block legitimate traffic and carries no risk of breaking the application. Sequenced this way, an existing network gains all five layers without an outage, because every enforcing change is preceded by the evidence that it will not break the traffic that should flow.

## How the layers apply to different workload types

The five layers are universal, but how you realize them shifts with the kind of workload you are protecting, and knowing the variation prevents the mistake of applying a virtual-machine mental model to a platform service that behaves differently.

For virtual machines, the layers map most directly, because a VM has a network interface you can govern with an NSG, a subnet you can segment, and outbound traffic you can force through a firewall. The one VM-specific practice worth emphasizing is removing public IPs from VMs that do not need to be reached from the internet, and reaching them for management through Azure Bastion rather than a public RDP or SSH port. A VM with a public IP and an open management port is the classic exposure, scanned and brute-forced within minutes of going live; Bastion provides browser-based management over the private network so the VM needs no public IP and no open management port at all. Segmentation, egress, DDoS on any remaining public IP, and monitoring then apply as described.

For Azure Kubernetes Service, segmentation operates at two levels, and conflating them is a frequent error. The node subnet is governed by NSGs like any other subnet, but traffic between pods inside the cluster is governed by Kubernetes network policies, not by Azure NSGs, because pod-to-pod traffic does not traverse the subnet boundary an NSG sees. A team that segments the node subnet carefully but leaves pod traffic unrestricted has segmented the outer layer and left the inner one flat. The egress layer applies to the cluster's outbound traffic, which should route through the firewall so that a compromised pod cannot exfiltrate freely, and AKS has specific outbound dependencies on registries and control-plane endpoints that the firewall rules must allow. Private access applies through a private cluster, where the API server is reachable only over the private network rather than a public endpoint, and through private endpoints for the data services the workloads use.

For App Service and other multitenant platform services that host your code, the network model is the inverse of a VM: you do not place the service in your subnet, you connect it to your subnet. Outbound traffic from the app reaches your virtual network through regional virtual network integration, which is what lets the app's egress route through the firewall and reach private endpoints, and inbound traffic to the app is restricted with access restrictions or, for full private exposure, a private endpoint on the app itself. The mistake here is assuming the app sits in your network the way a VM does; it does not, and the integration and private endpoint are the constructs that bring it into the posture. Segmentation for these services is access restrictions and integration rather than subnet NSGs, but the exposures the layers close are the same.

For the PaaS data services, the storage accounts, databases, Key Vaults, and messaging services, the dominant layer is private access, because these services exist to be connected to rather than to host your code, and their default public endpoint is the exposure that matters most. Every such service that supports Private Link should get a private endpoint and have public access disabled, with the linked private DNS zone making resolution work. Segmentation then restricts which subnets reach each endpoint, and monitoring records the access. Egress is less relevant for these services since they are destinations rather than sources, and DDoS protection applies to any public IP they expose, though disabling public access removes most of that surface. The common thread across all four workload types is that the map's five exposures are constant even though the controls that close them change shape, so you reason from the exposure to the right control for that workload rather than reaching for an NSG out of habit.

## The verdict

Azure network security best practices reduce to a single discipline: name every exposure and give each its own control, because no one control covers more than a slice. Segmentation with NSGs and application security groups limits lateral movement, but only once you override the implicit allow-VNet rule that otherwise leaves internal traffic open. Controlled egress through Azure Firewall's application rules limits outbound abuse, the one job an NSG cannot do because it cannot filter by domain, and only once a user-defined route forces traffic through the firewall. Private endpoints with public access disabled remove the public exposure of data services, and the second step, disabling public access, is the one that actually closes the door. DDoS protection in a paid tier defends the public-facing perimeter that must remain reachable, and the free baseline is not a substitute. Flow logs and traffic analytics end the blindness that hides every other gap, and only when someone is actually watching the analyzed output.

The strongest default, then, is the full map: build all five layers, in the order that contains mistakes as you go, verify each with its confirming check, and capture the whole configuration as infrastructure as code so it persists and audits cleanly. The counter-reading to reject is that an NSG is the security; it owns one row of the map and is blind to the other four. When you can trace a request through the layers and name, for any attacker move, the layer that stops it and the exposure that move targets, you have a posture rather than a pile of rules, and that is the line the best practices are drawn to put you on the right side of.

## Frequently Asked Questions

### Q: What are the five layers of Azure network defense in depth?

The five layers are segmentation, controlled egress, private access, DDoS protection, and monitoring, and each closes a distinct exposure the others leave open. Segmentation uses network security groups and application security groups to limit lateral movement between workloads. Controlled egress uses Azure Firewall application rules to limit outbound traffic to approved domains. Private access uses private endpoints with public network access disabled to remove the public exposure of data services. DDoS protection uses a paid Azure protection tier to absorb volumetric floods at the public perimeter. Monitoring uses flow logs and traffic analytics to make all of the above observable. The organizing rule is that no single control covers more than one of these exposures, so a defensible posture assigns every layer its own control and confirms none is missing. If you can name the layer that is absent in a given network, you can name what an attacker would do with the gap.

### Q: Is a network security group enough to secure an Azure network?

No. A network security group owns one of the five layers, segmentation, and is blind to the other four. It filters traffic by IP address, port, and protocol, which lets it limit lateral movement once you override the default allow-VNet rule, but it cannot filter outbound traffic by domain name, so it cannot control egress to arbitrary internet destinations. It cannot remove a platform service from the public internet, so a storage account or database stays exposed on its public endpoint regardless of NSG rules. It cannot absorb a volumetric flood, because saturation overwhelms capacity rather than violating a rule. It produces flow logs, which is raw monitoring material, but logs without analysis are not the monitoring layer. A posture built on the NSG alone covers one exposure and leaves four open, which is why a complete design pairs it with a firewall, private endpoints, DDoS protection, and analyzed monitoring.

### Q: How do I segment an Azure virtual network for security?

Segment by placing workloads of different trust levels in different subnets, then writing NSG rules that permit only the legitimate tier-to-tier paths and deny the rest. Use application security groups rather than raw IP addresses so the rules express intent and stay readable as the estate grows: define a group per tier, assign each workload's interface to its group, and write rules such as allow the web group to reach the app group on the application port. The step teams skip is overriding the implicit allow-VNet rule, which permits all intra-network traffic by default; until you add an explicit deny for intra-VNet traffic that your allow rules do not cover, segmentation is assumed rather than enforced. Place the deny at a priority below your allow rules but above the default rule so it overrides the implicit allow while leaving the legitimate paths intact. Confirm the result with Network Watcher by checking that a path you intend to block is actually denied.

### Q: How do I control outbound internet traffic from an Azure network?

Route all outbound traffic through Azure Firewall and let its application rules permit only the domains your workloads legitimately need. Two pieces are required. First, a user-defined route on each workload subnet sends internet-bound traffic to the firewall's private IP as the next hop, overriding the platform default route so no workload can bypass the firewall. Second, application rules on the firewall allow specific fully qualified domain names, and the firewall denies everything no rule permits. This is the capability a network security group lacks, because an NSG filters by IP and cannot match a destination domain. The discipline that makes egress control effective is starting from deny-all and adding an allow rule only for each destination the application proves it needs, which inverts the default from allowing everything to allowing only the known-good. Confirm the route is in effect by checking the effective next hop on a workload's interface; if it points at the internet rather than the firewall, the control governs nothing.

### Q: What happens if I forget to disable public network access on a service?

The service stays exposed to the internet even though you created a private endpoint, which is one of the most common half-measures in Azure network security. A private endpoint adds a private path to the service, but it does not remove the public one; the service's public endpoint keeps answering connections until you separately set public network access to disabled. The application works fine over the new private path, so nothing prompts the team to notice that the public door is still open, and an attacker who never touches your network can still reach the service over the internet and attempt to brute-force its authentication. The fix is the explicit public-access-disabled setting on the resource, and the way to catch the gap is a two-part verification: confirm from inside the network that the name resolves to the private IP, and separately confirm from the service configuration that public access is disabled. Checking only resolution misses the exposure entirely.

### Q: What does Azure DDoS infrastructure protection cover at no cost?

Every public IP in Azure receives DDoS infrastructure protection automatically, with no configuration and no charge, and it mitigates the largest volumetric attacks at the platform level to protect Azure's shared capacity. What it does not give you is the substance of the paid tiers: tuned mitigation policies adapted to your application's traffic baseline, telemetry about an attack on your specific endpoints, alerting when an attack begins, rapid-response engineering support during an incident, and cost protection that shields you from the autoscale bill an attack can trigger. A team that assumes the free baseline is full protection discovers during an attack that it has no visibility and no support path, because the baseline absorbs at the platform level without surfacing anything to you. For public-facing endpoints that matter, enable a paid tier, DDoS Network Protection for many public IPs in a network or DDoS IP Protection for a small number of individual addresses, and confirm it reports telemetry so an attack is visible rather than silently absorbed.

### Q: How do I monitor Azure network traffic for security?

Enable flow logs, feed them into traffic analytics tied to a Log Analytics workspace, and alert on the signals that indicate a problem. Flow logs record every connection a network security group or virtual network evaluates, capturing source, destination, port, protocol, direction, and whether the flow was allowed or denied, which is the raw evidence of network behavior. Traffic analytics processes those voluminous logs into an analyzed view: top talkers, inter-subnet and cross-region traffic, denied flows, and connections to and from the public internet. The mistake that defeats this layer is enabling logs that nobody reads; logs accumulating in a storage account with no analytics and no alerts are the same as no evidence when an incident happens. Build alerts on signals such as a spike in denied egress, which suggests an exfiltration attempt, or an allowed flow between subnets your design isolates, which reveals a segmentation gap. Network Watcher tools such as IP flow verify and next hop answer specific questions about why a particular flow is allowed, denied, or routed where it is.

### Q: What is network least privilege and how do I apply it?

Network least privilege means each workload can reach only the destinations it legitimately needs, on only the ports it needs, in only the directions it needs. It is the network counterpart of identity least privilege, and the five layers each enforce a slice of it. Inbound least privilege comes from segmentation: a tier accepts connections only from the specific tier that legitimately initiates them, expressed through application security groups. Outbound least privilege comes from the egress layer: a workload reaches only the external domains it needs, allowed as firewall rules with everything else denied. Reachability least privilege ties the layers together at a private endpoint, where you restrict which subnets may reach the endpoint using segmentation rules, so a private data service answers only to the one tier that uses it. The discipline that keeps it durable is starting from deny and adding only what the application proves it needs, because a network that starts open accumulates exceptions nobody dares remove, while a network that starts closed stays minimal.

### Q: How do I secure outbound traffic from Azure App Service?

App Service is a multitenant platform service, so it does not sit in your subnet the way a virtual machine does; you connect it to your network with regional virtual network integration. That integration is what routes the app's outbound traffic into your virtual network, where the user-defined route can send it through Azure Firewall and where it can reach private endpoints over the private path. Without integration, the app's outbound traffic leaves over the platform's shared egress and never touches your firewall, so the egress layer does not apply to it. Once integrated, the app's outbound traffic is governed exactly like a VM's: the firewall's application rules permit only the domains the app needs. Inbound exposure to the app is controlled separately, with access restrictions for IP-based rules or a private endpoint on the app itself for full private exposure. The mental model to drop is that the app lives in your network; it connects to your network, and integration plus private endpoints are the constructs that bring it into the posture.

### Q: How do I restrict which subnets can reach a private endpoint?

A private endpoint makes a service reachable from the network it lives in, but network least privilege says only the subnets that actually use the service should reach it, and you enforce that with the segmentation layer rather than with any setting on the endpoint itself. Write a network security group rule on the endpoint's subnet that allows inbound traffic only from the application security group of the tier that uses the service, on the service's port, and denies all other intra-network sources. The result composes three layers into one outcome: private access removes the public exposure, segmentation narrows the internal reach, and the service answers only to exactly the workloads that need it. This matters because a private endpoint without reachability restrictions is private from the internet but open to every subnet inside your network, so a foothold in any subnet could reach the data service. Confirm the restriction with Network Watcher by testing that a subnet which should not reach the endpoint is in fact denied.

### Q: What order should I apply Azure network security controls in for a new network?

Build in an order where each layer's dependencies are already in place. Start with the virtual network and subnet design, one trust boundary per subnet, reserving the dedicated subnets that the firewall, gateways, and Bastion require. Build segmentation next, defining application security groups and the tier-to-tier rules that override the implicit allow-VNet rule, so internal traffic is constrained before you add anything else. Build controlled egress third, deploying the firewall, attaching the user-defined routes that force traffic through it, and starting from deny-all. Build private access fourth, creating private endpoints, linking private DNS zones, and disabling public access, adding segmentation rules to restrict endpoint reachability. Add DDoS protection on the public-facing IPs. Enable monitoring and treat it as always-on from that point so you have visibility into whether the layers behave as designed. Finally, capture the whole configuration as infrastructure as code so the posture persists and audits cleanly. The sequence matters because building egress before the subnet and route design, for example, produces rework.

### Q: How do I harden an existing Azure network without causing an outage?

Reverse the build order and use monitoring to see traffic before you constrain it. Enable flow logs and traffic analytics first, even though they come last for a new network, and let them run long enough to capture the real communication patterns: which subnets talk, what outbound destinations workloads reach, and which services are accessed publicly. With the actual traffic understood, add segmentation in audit before enforce: write the tier allow rules based on observed flows, confirm from the logs that no legitimate traffic falls outside them, then add the intra-VNet deny and watch for newly denied legitimate flows. Add egress the same way, routing through the firewall with observed destinations allowed first, then tightening. Add private endpoints with public access still enabled, confirm the application switched to the private path through the flow logs, and only then disable public access. Add DDoS protection at any time since it blocks no legitimate traffic. Every enforcing change is preceded by evidence it will not break the traffic that should flow.

### Q: What does a Web Application Firewall add over Azure DDoS protection?

They defend different parts of the same perimeter and are complementary rather than alternatives. DDoS protection absorbs volumetric and protocol floods at the network and transport layers, the kind of attack that tries to saturate a public IP's capacity rather than exploit the application; its auto-tuned policies adapt to your traffic baseline so legitimate spikes are not mistaken for attacks. A Web Application Firewall, attached to an application gateway or front door, inspects the content of application-layer requests and filters those that are well-formed at the network level but malicious in their payload, such as injection attempts or known exploit patterns. DDoS protection cannot inspect request content, and a Web Application Firewall cannot absorb a volumetric flood, so a public-facing perimeter wants both: the flood is absorbed by DDoS protection while the malicious request is filtered by the firewall. When an application gateway with a Web Application Firewall sits in a network protected by DDoS Network Protection, the firewall is billed at a discounted rate, which is one of the value-added features of the paid DDoS tier.

### Q: How do application security groups improve network security?

Application security groups make segmentation rules express intent rather than addresses, which is what keeps a segmented network maintainable as it grows. Instead of writing network security group rules against IP addresses, which break when an address changes and become unmanageable as workloads multiply, you define a named group per role, the web tier, the app tier, the data tier, and assign each workload's network interface to the appropriate group. Your rules then read as policy: allow the web group to reach the app group on the application port, allow the app group to reach the data group on the database port, deny the rest. When you add a workload, you assign its interface to the right group and it inherits the policy with no rule edits, and when you decommission one, you remove it from the group with no stale rule left behind. The security benefit is indirect but real: rules that stay readable are rules an engineer can change correctly and an auditor can confirm, so segmentation does not silently rot into a set of exceptions nobody understands.

### Q: How do I verify that my Azure network security posture is actually in effect?

Run a confirming check for each of the five layers, because a control that is deployed is not the same as a control that is working. For segmentation, use Network Watcher's IP flow verify to confirm that a path your design denies is actually denied and that the deciding rule is the one you expect, not the implicit allow-VNet rule. For egress, use the next-hop tool to confirm outbound traffic routes to the firewall rather than the internet, then test that a blocked destination fails. For private access, confirm from inside the network that the service name resolves to the private IP, and separately confirm that public network access is disabled on the resource. For DDoS, confirm the public IPs that matter show a paid protection tier and report telemetry. For monitoring, confirm flow logs feed a traffic analytics workspace and that an alert fires on a test condition. When all five checks pass, the posture is demonstrated rather than assumed, and the verification record is the evidence an auditor wants.

### Q: Does Azure network security work differently for AKS clusters?

Yes, segmentation in particular operates at two levels in Azure Kubernetes Service, and treating it as one level is a common error. The node subnet is governed by network security groups like any other subnet, but traffic between pods inside the cluster is governed by Kubernetes network policies, not by Azure NSGs, because pod-to-pod traffic does not cross the subnet boundary an NSG sees. A cluster with a carefully segmented node subnet but no network policies has segmented the outer layer and left pod traffic flat, so a compromised pod can reach any other pod. The egress layer applies to the cluster's outbound traffic, which should route through the firewall, with the firewall rules allowing the registries and control-plane endpoints AKS requires. Private access applies through a private cluster, where the API server answers only over the private network rather than a public endpoint, and through private endpoints for the data services the workloads use. The five exposures are the same; the controls that close them include Kubernetes-native ones alongside the Azure network controls.

### Q: What is the single most common Azure network security mistake?

Asking one control to be the whole posture, almost always the network security group. The NSG is the first control engineers meet, it is free, it attaches quickly, and it visibly blocks traffic, so it feels like security, and a team attaches NSGs everywhere and considers the network secured. The reality is that the NSG owns one of five layers and is blind to the other four: it cannot filter egress by domain, cannot take a service off the public internet, cannot absorb a flood, and produces logs nobody analyzes. The networks that get breached are rarely ones where a control failed; they are ones where a layer was never present, and the absent layer is usually one of the four the NSG cannot cover. The fix is not to distrust the NSG but to stop overloading it: let it own segmentation, and give egress, private access, perimeter, and monitoring their own owners. The defense-in-depth map is the antidote, because it forces every exposure to have an assigned control rather than an assumption.

### Q: How do these network layers relate to a Zero Trust model?

These five layers are the network expression of Zero Trust, which assumes breach and verifies every access rather than trusting a perimeter. A Zero Trust network does not treat traffic inside the boundary as safe, which is exactly why segmentation constrains lateral movement and monitoring watches internal flows; it does not assume a service should be reachable just because a request authenticates, which is why private endpoints and least-privilege reachability narrow the path to a service. The principle of verify explicitly maps onto the controls that decide each flow on its own merits, least privilege maps onto the deny-by-default posture across segmentation and egress, and assume breach maps onto the monitoring that watches for the intrusion you expect rather than hope against. Network controls are only the network slice of Zero Trust, which spans identity and data as well, so the full model layers identity controls such as Conditional Access on top of these network controls. The network layers alone are not Zero Trust, but a Zero Trust posture cannot be built without them.
