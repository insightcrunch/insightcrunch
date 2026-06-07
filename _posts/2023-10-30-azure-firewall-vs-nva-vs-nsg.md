---
layout: post
title: "Azure Firewall vs NVA vs NSG"
page_title: "Azure Firewall vs NVA vs NSG: Statefulness, FQDN Egress Filtering, and the Decision Rule for Choosing Each in Production"
date: 2023-10-30
categories: ["Technology"]
tags: ["Azure", "Azure Firewall", "NSG", "Networking", "Security", "Cloud Computing"]
excerpt: "Azure Firewall vs NSG vs NVA confuses many teams. Learn how statefulness, FQDN egress control, and layer differences decide which one each need wants."
image: "/assets/images/blog/blog-01.webp"
reading_time: 59
author: "Insight Crunch Team"
last_updated: 2023-10-30
---

A surprising number of Azure designs treat the network security group, Azure Firewall, and a third-party network virtual appliance as three names for the same job. They are not. The recurring confusion behind every Azure Firewall vs NSG argument, and behind every debate over whether a network virtual appliance belongs in the picture, is the assumption that these three controls compete for one slot in the design. They do not compete. They sit at different layers, hold different scopes, and answer different questions, and the moment you see that clearly the choice stops being a coin flip and becomes a short chain of reasoning.

![Azure Firewall vs NVA vs NSG comparison](/assets/images/blog/blog-01.webp)

This piece walks the full distinction. It builds the mental model for each control, shows exactly where the filtering decision happens for a packet, names the one fact that wrecks most designs (a network security group cannot screen outbound flows by domain name), and gives you a decision table you can paste into a design review. By the end you should be able to look at any requirement, whether it is screening a subnet, governing what your workloads may reach on the public internet, or supporting an inspection feature the managed service does not offer, and say with confidence which control owns that requirement and how the others layer around it.

## What problem does each control actually solve?

The first mistake is treating "network security" in Azure as a single capability. It is not one capability. It is a stack of distinct jobs, and each of these three products was built for a different job in that stack. Untangling them starts with a plain statement of what each one is for, stripped of marketing language and reduced to the function an engineer can act on.

A network security group is a stateful packet screen that attaches to a subnet or to a single interface. It evaluates the five-tuple of a connection (source address, source port, destination address, destination port, and protocol) and either permits or blocks based on priority-ordered entries. It is free, it is built into the platform, and it lives as close to the workload as you can get. What it does not do is the thing teams most often expect of it: it has no awareness of domain names, no application-layer understanding, and no built-in threat intelligence. It screens by address and port, and that is the whole of its vocabulary.

Azure Firewall is a managed, highly available stateful firewall service that you deploy once, usually at the center of a hub network, and route many workloads through. Where the network security group speaks only in addresses and ports, the managed firewall adds application rules that match on fully qualified domain names, network rules that match on the classic five-tuple at scale, destination NAT for inbound publishing, and a threat-intelligence feed that can alert on or deny known-bad addresses and domains. It is centralized, it logs every decision, and Microsoft operates the underlying capacity and patching. You pay an hourly charge plus a data-processing charge, which is the price of handing the operational burden to the platform.

A network virtual appliance is a third-party firewall or routing product (a Palo Alto, Fortinet, Check Point, Cisco, or similar image) that you run as a virtual machine inside your own network. You own its lifecycle, its scaling, its high availability, and its licensing. People reach for it when they need a capability the managed service genuinely lacks: deep TLS inspection with their existing certificate tooling, an intrusion prevention engine they already operate elsewhere, single-vendor policy across cloud and on-premises, or a specialized routing behavior. The appliance gives you maximum control at the cost of maximum responsibility.

Hold those three sentences in mind, because almost every design error in this area comes from asking one of them to do another's job. Expecting a network security group to block a workload from reaching an arbitrary domain, or standing up an appliance for a feature the managed service already ships, are the two most common forms of that error, and both dissolve once the roles are clear. For the broader context of how routing and screening fit together in an Azure network, the [Azure networking fundamentals](/2023/08/21/azure-networking-fundamentals/) walkthrough sets the foundation this comparison builds on.

### Are these three controls really alternatives to each other?

Mostly no. A network security group and Azure Firewall are complementary far more often than they are alternatives, because one screens at the subnet edge and the other governs centralized egress at a different layer. An appliance is an alternative to the managed firewall only for the narrow set of features the managed service does not provide. Treating all three as interchangeable is the root of most misdesigns.

The cleaner way to frame it is by question. If the question is "which workloads on this subnet may talk to which other addresses and ports," the answer lives in a network security group. If the question is "what may anything in my environment reach on the public internet, by name," the answer lives in a managed firewall or an appliance. If the question is "I need a specific inspection or routing capability that neither of the above offers," the answer is an appliance. These are three questions, not one, and a mature design answers all three at once rather than forcing a single product to stretch across them.

## How does a network security group screen a packet?

To compare these controls honestly you have to understand the screening model of each, because the differences that matter are mechanical. The network security group is the simplest and the most misunderstood, so it earns the first deep look.

A network security group holds an ordered set of security entries, each with a priority number from 100 to 4096. Lower numbers win. Each entry describes a direction (inbound or outbound), a source, a destination, a port range, a protocol, and an action of allow or deny. When a packet arrives at a screened boundary, the platform walks the entries in priority order and applies the first one that matches the packet's five-tuple. If nothing custom matches, a set of default entries decides the outcome, and those defaults permit outbound traffic to the internet and inbound traffic from within the same virtual network while denying inbound from the internet.

The single most important property of this screen is that it is stateful. When an outbound connection is permitted, the return packets for that same connection are permitted automatically, without a matching inbound entry. The platform tracks the connection as a flow and allows its replies. This is why you write entries for the direction a connection is initiated and do not have to mirror them for the responses. Engineers coming from older stateless access-list models often double-write entries out of habit and then chase phantom problems caused by the redundant logic. The flow tracking handles the return path for you.

The property that matters most for this comparison is what the screen cannot see. A network security group evaluates addresses, ports, and protocols. It has no view into the application payload, no understanding of HTTP or TLS, and critically no resolution of domain names. You cannot write an entry that says "permit outbound to api.contoso.com and block everything else," because the screen never sees "api.contoso.com." It sees an address and a port. By the time a name has been resolved to an address, the screen is looking at the address, and that address may change minute to minute for any large service behind a content delivery network or a cloud load balancer. This single limitation is the hinge of the entire Azure Firewall vs NSG decision, and the next section gives it the attention it deserves.

### What is a service tag and how does it help an NSG?

A service tag is a named group of address ranges that Microsoft maintains for an Azure service, such as `Storage`, `Sql`, or `AzureCloud`. You reference the tag in a network security group entry instead of hardcoding addresses, and the platform keeps the underlying ranges current. It lets the address-based screen target Azure services cleanly without tracking changing address blocks by hand.

Service tags are the closest a network security group comes to naming a destination, and they are genuinely useful for permitting or blocking whole categories of Azure-owned endpoints. What they are not is a substitute for domain-based egress screening of the open internet. There is no service tag for "the specific set of partner APIs my application is allowed to call," because those live outside Azure and change on their own schedule. Service tags solve the Azure-endpoint case and leave the arbitrary-domain case entirely unsolved, which is exactly the gap the managed firewall and the appliance exist to fill. The [network security group deep dive](/2023/09/25/azure-nsg-deep-dive/) covers tags, priorities, and the default entries in full, and it is worth reading alongside this comparison if the screening model is new to you.

## Why can a network security group not filter outbound traffic by domain name?

This is the fact that decides more designs than any other, so it gets its own section and a direct answer. A network security group cannot screen outbound traffic by domain name because it operates at layers three and four of the network stack, where the only identifiers are addresses and ports, while a domain name is an application-layer concept that the screen never observes. The name has already been resolved to an address before the packet reaches the screen.

Walk the sequence of a workload reaching out to a public service. The application asks a resolver for the address of `download.example.com`. The resolver returns one or more addresses, possibly different ones on each query, possibly anycast addresses shared by thousands of unrelated sites behind the same content delivery network. The application then opens a connection to one of those addresses on port 443. The packet that hits the network security group carries that address and that port and nothing about the original name. The screen can permit or deny the address. It cannot tie the address back to the name, because the name is gone, and even if it could, the same address might serve a hundred other names you did not intend to permit.

This is not a configuration gap you can close with cleverness. It is a structural property of where the screen sits. People try several workarounds and each one fails in a predictable way. Hardcoding the current addresses of a service breaks the moment the service rotates its addresses, which large services do constantly. Permitting an entire content-delivery range opens far more than the one site you wanted. Permitting a broad service tag and hoping the destination falls inside it gives you no precision at all. Each workaround either over-permits, breaks under address churn, or both. The honest conclusion is that domain-based egress governance is simply not a job the network security group can do, and pretending otherwise produces brittle designs that fail at the worst time.

The control that does this job is one that terminates or at least inspects the connection at the application layer, reads the requested name from the TLS handshake or the HTTP host header, and decides based on that name. Azure Firewall does this with its application rules, and a network virtual appliance does it with its own application-aware engine. Both sit at a point in the path where the name is still visible, which is precisely why they can do what the address-and-port screen cannot.

### Does a firewall see the domain name even over encrypted HTTPS?

Yes, at least partially, without decrypting anything. During the TLS handshake the client sends the server name it wants in a field called Server Name Indication, in clear text, before encryption begins. Azure Firewall reads that field to match application rules against the requested name. Full payload inspection requires TLS termination, which the managed firewall offers in its premium tier and an appliance offers with your own certificates.

That distinction matters when you size the requirement. If you only need to govern which domains a workload may reach, the Server Name Indication field is enough and the standard managed-firewall tier handles it by reading the name from the handshake. If you need to inspect the actual content inside the encrypted session, scanning for malware or data exfiltration in the payload, you need true termination, which means the premium managed tier or an appliance carrying your certificate authority. Knowing which of these two needs you actually have prevents both under-buying and over-buying, and it is the kind of precise decomposition the [hub-and-spoke topology](/2023/10/16/hub-spoke-topology-explained/) design discipline rewards.

## What does Azure Firewall add that a network security group cannot?

With the limitation of the address-based screen established, the value of the managed firewall comes into focus. Azure Firewall adds four capabilities the network security group structurally cannot offer, and understanding each one tells you when the managed service earns its place in a design.

The first and most important is application rules. These match outbound connections on the fully qualified domain name, supporting both exact names and wildcards such as `*.windowsupdate.com`. This is the domain-based egress governance the address screen cannot do, and it is the single feature that most often justifies bringing the managed firewall into a network. When a compliance requirement says "workloads may only reach this explicit set of external services," the application rule is the mechanism that enforces it.

The second is network rules, which match on the classic five-tuple much as a network security group does, but centrally and at scale. You write these once at the hub and they govern flows from every spoke routed through the firewall, rather than maintaining parallel address-and-port logic on every subnet across the estate. The managed firewall does not replace the subnet screen here so much as provide a central enforcement point for the address-and-port decisions that need to apply broadly.

The third is destination network address translation for inbound publishing. The firewall can present a public address and port and translate connections arriving there to a private workload, which lets you publish an inbound service through the same managed control plane that governs egress. The fourth is threat intelligence, a Microsoft-maintained feed of known-malicious addresses and domains that the firewall can be set to alert on or to deny outright, giving you a baseline of protection against traffic to and from flagged endpoints without building that intelligence yourself.

Layered on top of all four is centralized logging. Every permit and deny decision the managed firewall makes can flow to a workspace for query and alerting, which gives you a single auditable record of what the environment reached and what was refused. The address screen logs flows too, but spread across every subnet rather than gathered at one inspection point. For an environment that must answer "what did we talk to, and what did we block, last Tuesday," the central log is a meaningful operational advantage.

### When is Azure Firewall overkill for a requirement?

When the requirement is purely subnet-level address-and-port screening with no domain-based egress, no central inbound publishing, and no threat-intelligence need, the managed firewall is overkill and a network security group does the job for free. Paying an hourly and per-gigabyte charge to enforce rules the built-in screen already enforces adds cost and a routing hop with no security benefit.

The test is whether any of the four firewall-only capabilities is actually required. If a workload simply needs "permit these subnets to reach these addresses and ports, deny the rest," the free screen covers it. The managed firewall earns its cost the moment you need to govern egress by domain name, centralize enforcement across many spokes, publish inbound services through one control plane, or apply threat intelligence. Absent those, you are buying capability you will not use, and a lean design declines it.

## What does a network virtual appliance offer that Azure Firewall does not?

If the managed firewall covers domain-based egress, centralized network rules, inbound publishing, and threat intelligence, the natural question is why anyone would run a third-party appliance at all. The answer is narrow but real: an appliance fills capability gaps the managed service genuinely does not cover, and outside those gaps it is usually the wrong choice.

The clearest gap is feature parity with an existing on-premises platform. An organization that runs a particular vendor's firewalls in its data centers, with a mature policy base, a trained operations team, and integrations into its security tooling, often wants the same vendor in the cloud so that one policy model and one skill set span both environments. The managed firewall does not speak that vendor's policy language, so the appliance is the way to keep a single pane of management across the hybrid estate.

A second gap is advanced inspection. Some appliances offer intrusion prevention engines, data-loss prevention, sandboxing, or signature sets that go beyond what the managed firewall provides even in its premium tier. If a security program depends on a specific engine or a specific certification, and the managed service does not carry it, the appliance is the only way to bring that engine into the Azure path. A third gap is specialized routing or protocol behavior, where an appliance acts as a custom router, a SD-WAN endpoint, or a gateway for a protocol the platform services do not handle natively.

Against these genuine gaps stands the cost of ownership, and it is substantial. You size, scale, patch, and provide high availability for the appliance yourself, typically running at least two instances behind a load balancer for resilience, carrying the vendor's license fees on top of the compute, and owning every upgrade and failure. The managed firewall hands all of that to Microsoft. So the appliance is the right answer precisely when a required capability outweighs that ownership cost, and the wrong answer when it is brought in for features the managed service already provides, which is the more common error of the two.

### Should I run an NVA just to save on firewall data-processing charges?

Almost never. The managed firewall's per-gigabyte data charge looks avoidable until you price the appliance's full cost: two or more virtual machines for high availability, vendor licensing, and the engineering time to operate, patch, and scale them. For most egress volumes that total exceeds the managed charge, and you have also taken on operational risk the platform was carrying.

The data-processing charge is visible and the appliance's costs are diffuse, which makes the appliance look cheaper than it is. Run the real comparison before deciding: compute for redundant instances, license fees, the load balancer, the egress that still flows, and the salary cost of the team that now owns availability and patching. Cost can legitimately drive a firewall-versus-appliance choice, but only when you compare the complete totals rather than the one line item that happens to be itemized on the managed service.

## The InsightCrunch firewall decision table

Here is the findable artifact this article is built around. The InsightCrunch firewall decision table maps each common need to the control that owns it and notes how the others layer. Treat the leftmost column as the question you are actually asking, and read across to the control that answers it. The point of the table is that most rows have a clear single owner, and the controls stack rather than collide.

| Need | Owner | How the others layer |
| --- | --- | --- |
| Screen which addresses and ports a subnet may use | Network security group | Firewall and appliance do not replace this; they govern at the hub, the screen governs at the subnet |
| Govern outbound traffic to the public internet by domain name | Azure Firewall (application rules) or NVA | The address screen cannot do this at all; it is the deciding capability |
| Centralize address-and-port enforcement across many spokes | Azure Firewall (network rules) | Per-subnet screens still apply locally; the firewall provides one central enforcement point |
| Publish an inbound service through one control plane | Azure Firewall (destination NAT) or NVA | A network security group can restrict but cannot translate and publish |
| Alert on or block known-malicious endpoints | Azure Firewall (threat intelligence) | The screen and the appliance do not carry the Microsoft feed; an appliance brings its own |
| Match a specific vendor's policy model across cloud and on-premises | NVA | Neither the screen nor the managed firewall speaks the vendor's policy language |
| Run a specific intrusion-prevention or inspection engine | NVA | Use only when the managed premium tier does not cover the requirement |
| Inspect the payload inside an encrypted session | Azure Firewall Premium or NVA | Requires TLS termination; the standard tier reads only the requested name |
| Provide subnet screening at zero additional cost | Network security group | Always available; the baseline every design should start from |

The shape of the table is the argument. Subnet-level address screening is almost always a network security group, because it is free, native, and lives next to the workload. Domain-based egress is almost always the managed firewall, with an appliance only when a specific feature or vendor-parity need pushes past what the managed service offers. The controls are layered, not exclusive, and a production design typically uses at least two of them together.

## The complement-not-compete rule

This is the namable claim. The complement-not-compete rule states that network security groups, Azure Firewall, and network virtual appliances operate at different layers and scopes, so a sound design uses network security groups for subnet screening and a centralized firewall for egress governance, reaching for an appliance only when a specific capability the managed firewall lacks justifies its ownership cost. Stated as a single sentence it sounds obvious. Applied consistently it eliminates most of the design errors in this space.

The rule works because each control has a natural home. The network security group's home is the subnet and the interface, the closest possible enforcement point to the workload, where it screens lateral and local address-and-port flows cheaply. The managed firewall's home is the hub, the centralized choke point through which spoke networks route their outbound and cross-segment traffic, where domain-based governance, central network rules, and threat intelligence apply once and cover everything that passes. The appliance's home is wherever a required capability has no other home, and nowhere else.

When you accept that each control has a home, the design writes itself. You put a network security group on every subnet because it costs nothing and screens the workload's immediate neighborhood. You route spoke egress through a managed firewall in the hub because that is where domain governance and central enforcement belong. You introduce an appliance only after naming the specific capability it provides that the managed firewall does not, and you can defend that decision in a review by pointing at the named capability. The rule does not tell you to use all three every time; it tells you to assign each requirement to the control whose home it falls in, and to layer the controls rather than substituting one for another.

### Can I use only Azure Firewall and skip network security groups entirely?

You can, but it is usually a mistake. The managed firewall governs traffic routed through it, typically north-south egress and cross-spoke flows, but it does not screen traffic that stays within a subnet or moves laterally between workloads that never traverse the hub. A network security group screens that close-in lateral movement cheaply, so dropping it removes a defense-in-depth layer for no saving.

The two controls cover different blast radii. Skipping subnet screens means a compromised workload can move freely to its neighbors on the same segment without ever passing the hub firewall, because that lateral traffic never routes through the central inspection point. Keeping a network security group on each subnet closes that path at no cost. The defense-in-depth posture that pairs a hub firewall with per-subnet screens is the standard recommendation precisely because each control catches what the other cannot see.

## How do you configure each control so they layer cleanly?

Understanding the model is half the work; wiring the controls together so they reinforce rather than fight each other is the other half. The configuration that realizes the complement-not-compete rule has three moving parts: the subnet screens, the central firewall, and the routing that forces spoke egress through that firewall. Get the routing wrong and the firewall never sees the traffic it was deployed to govern, which is the most common configuration failure in this whole area.

Start with the subnet screens. Each subnet that hosts workloads carries a network security group sized to that subnet's role. A web tier permits inbound on its serving port from the load balancer's source and denies the rest; an application tier permits inbound only from the web tier's subnet; a data tier permits inbound only from the application tier and from nothing else. These entries describe the lateral relationships between tiers and the local inbound exposure, and they apply regardless of what the central firewall does, because they screen traffic that may never leave the subnet.

Next, deploy the managed firewall into a dedicated subnet named `AzureFirewallSubnet` inside the hub network. The firewall takes a private address inside that subnet and one or more public addresses for egress and inbound publishing. You then author the policy: application rules listing the domains workloads may reach, network rules for the address-and-port flows that must be governed centrally, and the threat-intelligence mode set to alert or deny. The policy can be managed as a standalone object and associated with the firewall, which lets you version it and reuse a base policy across several firewalls in a hierarchy.

The piece that ties it together is routing. By default a spoke workload reaching the internet goes straight out through the platform's implicit default route, never touching the hub firewall. To force it through, you attach a route table to each spoke subnet with a user-defined route sending the default destination to the firewall's private address as the next hop. Now the spoke's outbound traffic lands at the firewall, gets evaluated against the policy, and either proceeds or is refused. The return path is handled by the firewall's stateful tracking. Without this route, every application rule you wrote is dead weight, because the traffic those rules govern never arrives. The mechanics of these routes, their precedence, and how to read the effective routes on an interface are covered in depth in the [route tables and user-defined routes](/2023/12/04/azure-route-tables-udr-explained/) guide, and getting them right is the difference between a firewall that works and one that is silently bypassed.

For an appliance the configuration mirrors this but you own more of it. The appliance runs as virtual machines in the hub, usually a pair behind an internal load balancer for resilience, and the spoke route table sends the default route to that load balancer's address rather than to a managed firewall. You then configure the appliance's own policy inside the vendor's interface, manage its scaling and patching, and monitor its health. The routing principle is identical; only the next hop and the ownership of the box differ.

### What goes wrong if the user-defined route is missing or wrong?

The firewall or appliance is bypassed silently. Traffic takes the platform's default internet route, exits without inspection, and every egress rule you authored is ignored, yet nothing errors and nothing logs a denial because the traffic never reached the control. The symptom is a firewall that shows no relevant flows while workloads happily reach destinations you meant to block.

This failure is insidious because it looks like success. The deployment completes, the policy is in place, and a casual check shows the firewall running. Only when you inspect the effective routes on a spoke interface, or notice that the firewall logs are empty of the flows you expected, do you find that the default route still points at the internet rather than at the firewall's address. The fix is to attach the route table and confirm the user-defined route overrides the default. Verifying effective routes on the interface, rather than trusting that the route table is associated, is the check that catches this every time.

## What are the common misdiagnoses, and how do you confirm each one?

Six failure patterns recur in real environments, and each has a confirming check and a fix. Naming them as a set turns a vague "the firewall isn't working" into a fast triage. Work through them in order and the cause usually falls out within a few minutes.

The first pattern is attempting domain-based egress with a network security group. Someone writes address entries hoping to constrain a workload to a set of public services, the addresses drift, and connections that should work start failing intermittently while connections that should be blocked succeed. Confirm it by checking whether the egress requirement is stated in terms of domain names while the enforcement is written in terms of addresses. The fix is to move domain governance to the managed firewall's application rules and leave the network security group to its address-and-port job.

The second pattern is the bypassed firewall described above, where a missing or wrong user-defined route lets spoke traffic exit without inspection. Confirm it by reading the effective routes on a spoke interface and checking whether the default destination's next hop is the firewall's private address or the internet. The fix is to correct the route table so the default route points at the firewall.

The third pattern is a redundant appliance, deployed for a capability the managed firewall already provides. A team stands up a vendor appliance to do domain-based egress filtering, which the managed firewall does natively, and now carries the appliance's full ownership cost for no capability gain. Confirm it by listing the specific features the appliance provides that the managed service does not; if the list is empty, the appliance is redundant. The fix is to retire the appliance in favor of the managed firewall unless a genuine gap is named.

The fourth pattern is the missing subnet screen, where a design routes everything through a hub firewall and drops the per-subnet network security groups, leaving lateral movement inside a subnet uninspected. Confirm it by checking whether workloads on the same subnet can reach each other on arbitrary ports without any local screen. The fix is to restore a network security group on each subnet so lateral flows are governed close to the workload.

The fifth pattern is the asymmetric-routing break, where traffic enters through one path and the platform tries to return it through another, and the stateful firewall drops the reply because it never saw the request. This shows up when an appliance pair or a firewall is inserted on only one direction of a flow. Confirm it by tracing both directions of a connection and checking whether both traverse the same control. The fix is to ensure symmetric routing so the stateful control sees both halves of every connection.

The sixth pattern is the over-broad application rule, where a wildcard such as `*.com` is written to make a workload "just work," which permits essentially everything and defeats the purpose of domain governance. Confirm it by reviewing the application rules for wildcards broader than the actual requirement. The fix is to tighten each wildcard to the narrowest pattern that covers the legitimate destinations, such as a specific vendor's subdomain rather than an entire top-level domain.

### How do I tell whether my egress problem is a routing fault or a policy denial?

Check the firewall logs first. If the firewall logged an explicit denial for the flow, the cause is a policy gap and you adjust the rules. If the firewall logged nothing at all for that flow, the traffic never reached it, which points at a routing fault: a missing or wrong user-defined route is sending the connection out the default path instead.

The presence or absence of a log entry splits the diagnosis cleanly. A denial in the log means the control saw the connection and refused it on purpose, so the work is in the policy. Silence in the log for traffic you expected to see means the control was bypassed, so the work is in the routing. Running an end-to-end diagnosis with this single question, did the firewall see the flow at all, collapses most egress investigations into one of two short paths, and it is the kind of confirming check that VaultBook's hands-on labs are built to let you rehearse against a live topology rather than learning under incident pressure.

## Six real-world patterns and the factor that decides each

Briefs and tables describe the controls in the abstract; engineers meet them as concrete situations. Here are six recurring cases reported in real environments, each framed as a pattern with the one factor that decides it. Recognizing which pattern you are in tells you which control owns the requirement before you write a single entry.

### Pattern one: a workload must reach a fixed set of public APIs and nothing else

A payment service may call only its processor's endpoints and a couple of named partner domains; every other outbound destination must be refused. The deciding factor is that the requirement is expressed in domain names, not addresses. A network security group cannot enforce it because it never sees the names. The owner is the managed firewall, with application rules listing the permitted domains and a default deny for everything else. A per-subnet screen still sits underneath for local address-and-port hygiene, but the domain governance lives at the hub. This is the textbook case for the managed firewall, and it is also the case people most often try and fail to solve with the address screen.

### Pattern two: centralizing egress for an entire spoke estate through one hub

A platform team runs dozens of spoke networks and wants one place to govern and log what all of them reach on the internet, rather than maintaining egress logic on every subnet across every spoke. The deciding factor is centralization at scale. The owner is the managed firewall in the hub, with spoke route tables sending default traffic to it, so one policy and one log cover the whole estate. Per-subnet screens remain for local relationships, but the estate-wide egress decision is made once. This pattern is the heart of the [hub-and-spoke topology](/2023/10/16/hub-spoke-topology-explained/), where the hub firewall is the shared service every spoke routes through.

### Pattern three: a security program requires a specific intrusion-prevention engine

An organization's security standard mandates a particular vendor's intrusion-prevention signatures and a data-loss-prevention engine that the managed firewall does not carry. The deciding factor is a named capability gap. The owner is a network virtual appliance running that vendor's image, inserted in the path the same way a firewall would be, because only the appliance brings the required engine. The managed firewall and the subnet screens still have roles, but the inspection requirement forces the appliance. This is one of the few cases where the appliance is the correct first choice rather than a redundant addition.

### Pattern four: per-subnet screening complementing a hub firewall

A three-tier application needs each tier screened so the web tier cannot reach the data tier directly and lateral movement between peers on a subnet is constrained, while a hub firewall governs what any tier may reach outbound. The deciding factor is that the requirement is local and address-based, not domain-based or central. The owner is a network security group on each subnet, layered beneath the hub firewall. The two controls cover different scopes, the subnet screen for close-in lateral relationships and the hub firewall for outbound governance, and the design uses both. This pattern is the everyday embodiment of the complement-not-compete rule.

### Pattern five: cost driving a firewall-versus-appliance choice

A team must govern domain-based egress and is weighing the managed firewall's hourly and per-gigabyte charges against running an appliance pair they already license elsewhere. The deciding factor is the complete cost comparison, not the visible line item. The owner depends on the arithmetic: if the appliance's compute, licensing, load balancer, and operational labor total less than the managed charge for the actual egress volume, the appliance wins; if not, the managed firewall wins. Most moderate-volume environments favor the managed service once the diffuse appliance costs are summed honestly, but a high-volume environment with an existing license can tip the other way. The point is to compare totals, because cost is a legitimate deciding factor only when measured completely.

### Pattern six: threat-intelligence filtering as a baseline

A team wants a floor of protection against traffic to and from known-malicious endpoints without building or buying a threat feed of its own. The deciding factor is the desire for a maintained, zero-effort intelligence baseline. The owner is the managed firewall with threat intelligence set to deny, because Microsoft maintains the feed and the firewall applies it with no work from the team. An appliance can do this too, but it brings the vendor's feed and the vendor's operational overhead, so for a baseline rather than a specialized requirement the managed service is the lighter choice. The subnet screens contribute nothing to this pattern because they have no concept of endpoint reputation.

## How do these controls interact with the rest of the network?

A control never lives alone. Each of the three interacts with routing, with name resolution, and with the other controls, and the interactions are where designs succeed or quietly fail. The dominant interaction is with routing, because routing decides whether the central controls ever see the traffic they are meant to govern, as the earlier configuration section stressed.

The managed firewall and the appliance both depend on user-defined routes to draw spoke traffic toward them. The platform's default routing sends internet-bound traffic straight out, so without an explicit route to the firewall as the next hop, the central control is bypassed. Route precedence matters here: a user-defined route overrides the system default, and a more specific prefix overrides a less specific one, so a design that mixes several routes must reason about which one actually wins for a given destination. The longest-prefix-match behavior and the precedence between user-defined, border-gateway-protocol, and system routes are the mechanics that decide whether your firewall route or some other path takes the packet, and they are worth understanding precisely before inserting a central control.

Name resolution interacts strongly with the managed firewall's application rules. The firewall matches on the requested domain name, but it also needs to resolve those names to verify and connect, and in designs that use private resolution or custom resolvers the firewall must be pointed at the right resolver or its application rules will behave unexpectedly. A workload that resolves a name through a private zone and then connects must have its traffic routed through the firewall for the application rule to apply, and the firewall must resolve the same name consistently, or you get mismatches between what the workload intended and what the firewall evaluated.

The interaction between the subnet screen and the central control is the cleanest, because they operate at different scopes and rarely conflict. The network security group screens the local five-tuple at the subnet boundary; the firewall governs the routed flows at the hub. A flow that stays inside a subnet meets only the screen; a flow that leaves for the internet meets the screen on the way out of its interface and then the firewall at the hub. The two stack in series along the path, each applying its own logic, and because the screen is stateful and the firewall is stateful, the return path is handled by both without extra entries. The only real failure here is the asymmetric-routing case, where a reply tries to take a different path than the request and a stateful control drops it for lack of a matching flow, which symmetric routing prevents.

### Does the order of evaluation between the NSG and the firewall matter?

It matters for where a flow is screened, not for correctness of the layering. On the way out, a packet leaving a workload meets the subnet screen at its interface first, and only the permitted flows then route to the hub firewall for domain and central evaluation. A denial at either layer stops the flow, so the two screens compound rather than override one another.

Because both controls are stateful and sit at different points on the path, you reason about each independently: the screen decides the local address-and-port question at the subnet, the firewall decides the central and domain question at the hub, and a flow must satisfy both to complete. There is no merging of their logic and no precedence puzzle between them; they are separate gates in series. The practical consequence is that when a flow fails you check both gates, but you check them as distinct controls with distinct purposes rather than trying to reconcile them into one rule set.

## How do you design this for production?

A production-grade design assembles the three controls into a defense-in-depth posture where each does its own job and the failure of one does not collapse the others. The reference shape is a hub-and-spoke network with a managed firewall in the hub, per-subnet network security groups in every spoke, and an appliance only where a named capability demands it.

Put a network security group on every subnet without exception, because it is free and it screens the workload's immediate neighborhood, the layer no central control covers. Size each screen to its tier's real relationships: inbound only from the sources that legitimately initiate connections, outbound constrained where the local case allows, and a default-deny posture on inbound from outside the virtual network. These screens are your innermost ring, closest to the workload, and they keep working even if the central control has a bad day.

Place a managed firewall in the hub and route every spoke's egress through it with user-defined routes. Author the policy as a base policy plus per-environment child policies if you run several firewalls, so common rules are shared and environment-specific rules are local. Turn on threat intelligence in deny mode for a maintained baseline, write application rules that name the domains workloads may reach with the narrowest wildcards that work, and write network rules for the address-and-port flows that must be governed centrally. Send every firewall decision to a workspace so you have one auditable record of what the estate reached and refused.

Reach for an appliance only after naming the specific capability it provides that the managed firewall does not, and when you do, run it as a resilient pair behind an internal load balancer with the spoke routes pointing at that balancer. Own its patching and scaling deliberately, because the platform is no longer doing that for you, and revisit the decision periodically in case the managed service has since gained the capability that justified the appliance, which would let you retire the operational burden.

Finally, build the routing with the same care you build the policy, because the routing is what makes the policy real. Confirm the effective routes on a representative interface in each spoke, verify that the default destination's next hop is the firewall, and treat an empty firewall log for traffic you expected as a routing problem until proven otherwise. The whole posture rests on the traffic actually reaching the control, and the route is the thread that delivers it.

### How should the design evolve as the estate grows?

Centralize earlier than feels necessary. As spokes multiply, maintaining egress logic per subnet stops scaling and the hub firewall's single policy and single log become the only sustainable model. Introduce a firewall policy hierarchy so a base policy covers shared rules and child policies carry environment specifics, and keep the per-subnet screens lean and local.

Growth changes which control carries which burden. Early on, a handful of subnets can be governed with screens alone, but past a certain count the operational cost of parallel per-subnet egress logic exceeds the cost of a hub firewall, and the centralization pays for itself in both consistency and audit. Plan the hub firewall before you need it, because retrofitting routing across an estate already in production is harder than building it in from the start. The appliance decision should be revisited at each major platform update, since capabilities that once required a third-party box periodically arrive in the managed service.

## How do statefulness and layer actually differ across the three?

The phrase "stateful" gets used loosely, so it helps to be precise about what each control tracks and at which layer it operates, because those two properties explain most of the behavioral differences a reader will meet.

All three controls are stateful in the connection-tracking sense: each remembers the flows it has permitted so the return packets are allowed without a mirrored entry. The network security group tracks the five-tuple flow and permits its replies. The managed firewall tracks the connection it inspected and permits the response. An appliance tracks state in its own engine, often with deeper context such as the application session. So none of them requires you to write reverse entries for return traffic, and the older stateless-access-list habit of doing so is unnecessary and error-prone across all three.

The layer is where they diverge sharply. The network security group operates at layers three and four, the network and transport layers, where the identifiers are addresses, protocols, and ports. It has no view above that, which is the structural reason it cannot screen by domain name, inspect payloads, or understand application sessions. Everything it does is expressible in terms of who, where, and which port, and nothing in terms of what application or what name.

The managed firewall operates across layers three, four, and seven. Its network rules work at layers three and four like the subnet screen, but at scale and centrally; its application rules reach layer seven, reading the requested name from the TLS handshake or HTTP host header and matching on it. In its premium tier it can terminate TLS and inspect the decrypted payload, which is layer-seven inspection in the fullest sense. An appliance similarly spans these layers and often goes further, with intrusion-prevention signatures and content inspection that examine the payload in depth.

This layer difference is the entire reason the three are not interchangeable. A requirement stated in layer-three-and-four terms (addresses and ports) can be met by any of them, but the cheapest and closest is the subnet screen. A requirement stated in layer-seven terms (domain names, payloads, application sessions) can only be met by the firewall or the appliance, because the subnet screen does not reach that layer. When you find yourself unsure which control a requirement needs, restate the requirement in terms of the layer it lives at, and the answer usually becomes obvious: an address-and-port requirement goes to the screen, a name-or-payload requirement goes to the firewall or the appliance.

### Is Azure Firewall stateful in the same way a network security group is?

Both track connections so return traffic flows without a reverse entry, so in the connection-tracking sense they are equally stateful. The difference is depth: the subnet screen tracks only the address-and-port flow, while the firewall tracks the connection with awareness of the requested name in application rules, and in the premium tier with awareness of the decrypted session.

The shared statefulness means neither one needs mirrored entries for replies, which is the practical takeaway for anyone writing rules. The divergence is in what each one understands about the connection it is tracking. The screen knows the five-tuple and nothing more; the firewall knows the five-tuple plus, for application rules, the name the client asked for. That extra context is what lets the firewall make decisions the screen structurally cannot, even though both honor the return path automatically.

## What does each control cost, and where does the money go?

Cost is a deciding factor in real designs, so it deserves a clear treatment rather than a hand-wave. The three controls sit at very different points on the cost spectrum, and the cheapest by sticker price is not always the cheapest in total once operational burden is counted.

The network security group is free. It carries no charge for the screen itself or for the traffic it evaluates. Its only cost is the human time to author and maintain the entries, which for a well-structured set of subnet screens is modest. This is why every design should start with subnet screens: they add a defense layer at zero platform cost, and declining them saves nothing while removing protection.

The managed firewall charges in two dimensions: an hourly deployment charge for the firewall instance and a per-gigabyte charge for the data it processes. The hourly charge is fixed regardless of traffic; the data charge scales with the volume that flows through. For a centralized hub firewall governing a busy estate, the data charge can become the larger line item, which is what prompts teams to wonder whether an appliance would be cheaper. The premium tier costs more than the standard tier and adds TLS inspection and a fuller intrusion-detection capability, so you pay the premium only when you need payload inspection rather than name-based governance.

The appliance's cost is diffuse and easy to underestimate. You pay for the compute of at least two virtual machines sized for your throughput, the vendor's license fees which can dwarf the compute, the internal load balancer that fronts the pair, the egress that still flows out, and, least visible but often largest, the engineering time to size, patch, scale, monitor, and recover the appliance. The managed firewall folds the operational labor into Microsoft's charge; the appliance hands it back to you. A complete comparison sums all of these, and only then can you say honestly whether the appliance undercuts the managed service for your volume and your existing licensing.

The honest cost rule is to compare totals, not line items. The managed firewall's data charge is visible and itemized, which makes it feel expensive, while the appliance's costs are scattered across compute, licensing, and salaries, which makes it feel cheap. Itemize both fully. For most moderate-volume environments the managed service wins on total cost because the operational labor it absorbs is real money. For a high-volume environment with an already-paid enterprise license and a team that operates the vendor's product anyway, the appliance can win. The decision is arithmetic, and it must use complete figures on both sides.

### Why does the managed firewall sometimes cost more than expected?

The per-gigabyte data-processing charge scales with the volume routed through the firewall, and a hub that centralizes egress for a large estate processes a great deal of data. Teams budget for the hourly charge and forget the data dimension, so the bill surprises them. Routing only the traffic that genuinely needs governance, rather than everything, keeps the data charge proportionate.

The fix for an unexpectedly high firewall bill is rarely to abandon the managed service; it is to be deliberate about what routes through it. Traffic that needs domain governance or central logging should traverse the firewall; bulk traffic that needs neither, such as backup flows to a trusted Azure service, can often use a service endpoint or private path that does not incur the firewall's data charge. Designing the routing so the firewall processes the traffic that benefits from inspection, and not the traffic that does not, controls the cost without sacrificing the governance.

## How do the three compare on management and operations?

Beyond capability and cost, the daily operational burden differs sharply across the three, and that burden is often the factor that decides a long-running design even when capability and cost are close.

The network security group is the lightest to operate. Microsoft runs the platform underneath it, there is nothing to patch or scale, and the only ongoing work is keeping the entries correct as the workload's relationships change. The risk is sprawl: across a large estate, hundreds of subnet screens can drift into inconsistency if there is no discipline of templating and review. Managing them as code, with the screens defined in templates and applied uniformly, keeps the sprawl in check and makes the whole set auditable.

The managed firewall is moderate to operate. Microsoft handles the capacity, the high availability, and the patching, so you never size instances or apply updates. Your work is the policy: authoring and reviewing the application and network rules, tuning the threat-intelligence mode, and reading the logs. The policy hierarchy, where a base policy carries shared rules and child policies carry specifics, is the tool that keeps a multi-firewall estate consistent. The operational ceiling is low because the platform carries the heavy parts.

The appliance is the heaviest to operate, and this is the cost most often underestimated when one is chosen. You size the instances for throughput, you scale them as load grows, you patch the operating system and the vendor software, you provide high availability through a resilient pair and tested failover, you monitor health and capacity, and you own every incident. None of this is hidden when you choose the appliance, but it is easy to discount it against the appeal of feature parity or a familiar vendor. A team that already operates the vendor's product elsewhere absorbs this more easily; a team new to it takes on a real operational learning curve.

The management comparison usually reinforces the capability one. The managed firewall's low operational burden is a strong reason to prefer it whenever it covers the requirement, and the appliance's high burden is a strong reason to reserve it for the cases where a named capability leaves no alternative. The subnet screen's near-zero burden is why it belongs in every design as the baseline layer. Stated as a single principle: let the platform carry the operational weight wherever it can, and take the weight onto your own team only where a requirement forces it.

### How do I keep dozens of subnet screens consistent across a large estate?

Manage them as code. Define each screen's entries in a template, apply the templates through your deployment pipeline rather than by hand, and review changes the way you review application code. Uniform templates prevent the drift that creeps in when screens are edited individually in the portal, and they make the entire set auditable from one source.

The discipline that tames subnet-screen sprawl is the same one that tames any large configuration: a single source of truth and a pipeline that applies it. When every screen comes from a reviewed template, you can answer "what does this tier permit" from the template rather than from a portal blade, and a drift between intended and actual configuration shows up as a difference against the source. This is also where VaultBook's tested template and command library earns its place, giving you vetted starting points for the screen definitions rather than authoring each one from a blank file.

## How does observability differ across the three controls?

A control you cannot see into is a control you cannot trust, and the three differ meaningfully in what they reveal about themselves. Logging and diagnostics are part of the comparison because an environment that must answer "what did we reach, and what did we refuse" depends on the quality of the record each control keeps.

The network security group emits flow logs that record which connections were permitted and which were dropped at a screened boundary, written to a storage account and optionally enriched by traffic analytics. These logs are accurate but distributed: every subnet's screen keeps its own record, so reconstructing a full picture of an estate means gathering logs from many places and correlating them. For local troubleshooting, where you want to know whether a specific subnet permitted a specific flow, the per-subnet log is exactly right. For an estate-wide question, the distribution becomes a chore.

The managed firewall, by contrast, gathers its record at one point. Every application-rule and network-rule decision, every threat-intelligence alert or denial, and every translated inbound connection can stream to a workspace where you query them together. Because the hub firewall is the single choke point that spoke egress routes through, its log is the closest thing to a complete account of what the estate reached outbound and what was refused. This central record is one of the underrated reasons to centralize egress: the firewall earns its place not only as an enforcement point but as the one log that answers governance questions without correlation across dozens of sources.

An appliance keeps whatever logs its vendor provides, often rich and detailed, frequently in the vendor's own format and console. The depth can exceed what the managed services offer, with full session detail and inspection verdicts, but the record lives in the vendor's tooling rather than natively in an Azure workspace, so integrating it into a unified Azure observability story takes deliberate work. For a team already running the vendor's logging pipeline, this is familiar ground; for a team that wants everything in one Azure workspace, it is an extra integration to build and maintain.

The practical upshot is that the central firewall gives the cleanest answer to estate-wide governance questions, the subnet screens give the most precise answer to local flow questions, and the appliance gives the deepest answer within its own console. A mature observability design uses each log for the question it answers best rather than expecting any single one to cover everything. When you query the firewall log and find no entry for a flow you expected to see, that absence is itself a diagnostic signal pointing at a routing bypass, which is why the central log is as useful for confirming what did not happen as for recording what did.

### Where should I send the logs from each control?

Send them all to one analytics workspace where the query language can join across them. The subnet flow logs, the firewall decision logs, and, where feasible, the appliance logs gathered through its vendor connector belong in a common store so a single query can trace a flow from the subnet screen through the hub control. Centralizing the logs, even when the controls are distributed, gives one place to investigate.

The goal is a single investigative surface even though the controls themselves sit at different layers. When a flow misbehaves, you want to ask one query that shows whether the subnet screen permitted it, whether it reached the hub control, and what verdict that control returned, rather than hopping between three consoles. Routing all three records into a shared workspace, with the firewall and flow logs native and the appliance log bridged through its connector, builds that surface and turns a multi-control investigation into a single trace.

## What does high availability look like for each option?

Resilience is built differently for each control, and the difference is one of the strongest arguments for the managed services over an appliance for teams without deep operational bandwidth.

The network security group inherits the platform's resilience entirely. It is a property of the subnet and interface, enforced by the platform's own distributed infrastructure, with nothing for you to make redundant. There is no instance to fail, no failover to test, and no capacity to scale; the screen simply applies wherever it is associated. This is the simplest resilience story of the three because there is effectively nothing to engineer.

The managed firewall is highly available by design within a region, and you can spread it across availability zones so a zone failure does not take it down. Microsoft operates the underlying capacity and scales it to the throughput the service handles, so you do not size instances or build failover. Your resilience work is limited to choosing zone redundancy and, for multi-region designs, deciding whether each region carries its own firewall. The heavy lifting of keeping the enforcement point alive belongs to the platform.

The appliance is where resilience becomes your job in full. A single appliance instance is a single point of failure, so a production deployment runs at least two instances, fronted by an internal load balancer that health-probes them and steers traffic to a healthy one. You must handle the failover behavior of the vendor's product, ensure session state is handled sanely across a failover where the vendor supports it, size the instances for peak throughput with headroom, and scale them as load grows. Asymmetric routing is a particular hazard with an appliance pair, because traffic that enters through one instance and tries to return through the other will be dropped by the stateful engine that never saw the original connection, so the routing must keep both directions of a flow on the same instance. None of this is hidden, but it is real engineering that the managed services simply do not ask of you.

This resilience contrast often settles a close decision. When capability and cost are roughly even between the managed firewall and an appliance, the fact that the platform carries availability for the managed service while you carry it for the appliance tilts most teams toward the managed option, reserving the appliance for the cases where its unique capability leaves no choice. Resilience engineering is expensive in attention as well as money, and handing it to the platform is a genuine benefit, not a minor convenience.

### Why is asymmetric routing especially dangerous with an appliance pair?

Because the stateful engine on each instance tracks only the connections it personally handled. If a request enters through instance one and the reply tries to leave through instance two, instance two has no record of that connection and drops the reply as unsolicited. The flow half-completes and then stalls, which is maddening to diagnose because the request clearly succeeded.

The cure is to make routing symmetric so both halves of any connection traverse the same instance, typically by using the load balancer's session persistence and consistent routing rules on both directions. This is a class of problem the managed firewall largely spares you, since the platform handles its own internal symmetry, but with a self-operated pair it is your responsibility to design and verify. Tracing both directions of a stalled flow and checking whether they share an instance is the confirming step that exposes this fault quickly.

## A worked end-to-end design for a regulated workload

Putting the pieces together, walk through a single concrete design so the reasoning is visible from requirement to configuration. The workload is a regulated payment platform with three tiers, a hard rule that it may reach only a named set of external processors, an audit obligation to record every outbound destination, and a security standard that for now is satisfied by the managed service's capabilities.

Begin with the requirements restated by layer and scope, because that is what assigns each one to a control. The tier-to-tier relationships (web may reach application, application may reach data, peers may not roam) are local address-and-port rules, so they go to subnet screens. The "only these external processors" rule is stated in domain names, so it goes to the managed firewall's application rules. The audit obligation is an estate-wide record, so it goes to the central firewall log. The security standard, satisfied by the managed service today, does not force an appliance, so none is introduced. Already the design has written itself from the requirements.

Now the configuration. Each tier sits on its own subnet with a network security group: the web subnet permits inbound on the serving port from the load balancer and denies the rest; the application subnet permits inbound only from the web subnet; the data subnet permits inbound only from the application subnet. These screens enforce the tier boundaries and constrain lateral movement at no cost, and they keep working independently of anything at the hub. A hub network holds the managed firewall in its dedicated subnet, with application rules naming exactly the processor domains the platform may reach and a default deny beneath them, network rules for any address-and-port flows that must be governed centrally, and threat intelligence set to deny for a maintained baseline.

The routing is the thread that makes the firewall real. Each spoke subnet carries a route table whose default route sends outbound traffic to the firewall's private address, so every connection toward an external processor lands at the firewall and is matched against the application rules before it proceeds. The firewall's decisions stream to a workspace, satisfying the audit obligation with a single queryable record of what the platform reached and what was refused. The return traffic is handled by the firewall's stateful tracking and by the subnet screens' stateful tracking, with no reverse entries needed.

Verification closes the loop. You read the effective routes on a representative interface in each spoke and confirm the default next hop is the firewall, not the internet, which proves the firewall is not bypassed. You generate a test connection to a permitted processor and confirm it succeeds and appears in the firewall log as an allow; you generate a connection to a non-permitted domain and confirm it is refused and appears as a deny. You confirm a web-tier workload cannot open a connection straight to the data tier, proving the subnet screens enforce the tier boundary. With those checks green, the design is not merely deployed but demonstrated, and the demonstration is exactly the kind of drill VaultBook's labs let you rehearse against a live topology before the requirement is real.

### When would this design need an appliance added later?

When a new requirement names a capability the managed service does not cover, such as a mandated intrusion-prevention signature set or deep payload inspection with the organization's own certificate authority integrated into existing tooling. At that point you introduce an appliance for that specific capability, keep the subnet screens and the hub firewall, and route the relevant traffic through the appliance.

The design stays stable until a requirement crosses the line the managed service cannot reach, which is the discipline the whole comparison teaches: you add the appliance only when you can name the capability it brings that nothing else does, and you revisit that need as the managed service grows, because a future platform update may absorb the capability and let you retire the operational burden you took on.

## How do you migrate an existing design toward this model?

Most environments do not start clean; they arrive at this comparison already carrying a design that grew without the discipline the complement-not-compete rule provides. Two starting points are common, and each has a sane path toward the layered model.

The first starting point is an estate governed by subnet screens alone, with no central control, where teams have been writing address entries to approximate egress governance. The symptoms are familiar: address lists that drift, egress rules that break when a service rotates its addresses, and no single record of what the estate reached. The path forward is to introduce a hub network and a managed control at its center, then migrate spokes onto it one at a time. For each spoke you add the route table that draws its egress to the central control, move the domain-based intent out of the brittle address entries and into application rules, and leave the subnet screens in place for their local job. Migrating spoke by spoke rather than all at once limits the blast radius if a route is misconfigured, and verifying effective routes after each spoke confirms the central control is actually in the path before you trust it.

The second starting point is an estate that over-invested in a third-party appliance, routing everything through it for capabilities the managed service now provides. The symptoms here are operational rather than functional: a heavy patching and scaling burden, a resilience design the team struggles to keep current, and licensing costs that no longer map to a capability the appliance uniquely delivers. The path forward begins with an honest capability audit. List the features the appliance provides that the managed service genuinely does not, today, in the tier you would buy. If that list is empty, the appliance is a candidate for retirement: stand up the managed control alongside it, shift spokes onto the managed path, validate that egress governance and logging behave as required, and decommission the appliance once the managed control proves out. If the list is not empty, keep the appliance for exactly the traffic that needs its unique features and route the rest through the lighter managed path, shrinking the appliance's footprint to the cases that justify it.

Both migrations share a sequencing principle: change routing last and verify it first. The policy on the new control can be authored and reviewed without affecting live traffic, because traffic does not reach the new control until the route points at it. So you build the policy, confirm it is complete, and only then flip the route for one spoke, watch the central log fill with that spoke's flows, confirm the permits and denials match intent, and proceed to the next spoke. Treating the route change as the commit step, rather than the policy authoring, keeps each migration step reversible and observable. A spoke that misbehaves after its route flips can be rolled back by reverting that one route table, and the central log tells you immediately whether the flip worked because the spoke's flows either appear or they do not.

Throughout either migration, the subnet screens stay put. They are the one layer you never remove, because they cost nothing, screen the local neighborhood the central control cannot see, and provide the defense-in-depth floor that keeps a compromised workload from roaming its subnet freely. Whatever else changes at the hub, the per-subnet screens remain the innermost ring, and a migration that touches them at all should only be tightening them, never dropping them.

### How do I avoid an outage when flipping a spoke onto the central control?

Author and review the policy before any route changes, then flip one spoke's route during a low-traffic window and watch the central log immediately. If the expected flows appear as allows and the unwanted ones as denials, the flip worked; if expected flows are missing, the route or a rule is wrong and you revert that single route table to restore the prior path.

The safety comes from making the route the last and smallest change, scoped to one spoke at a time. Because nothing reaches the new control until its route points there, the policy can be wrong without consequence until you flip, and a wrong flip affects only the one spoke you changed and is undone by reverting one route table. Pairing each flip with a live look at the central log turns the cutover into an observed, reversible step rather than a leap, which is precisely the rehearsal VaultBook's labs are designed to let you practice safely before doing it in production.

## Closing verdict

The argument of this entire piece reduces to one sentence: stop treating the network security group, Azure Firewall, and the network virtual appliance as competitors for a single slot, and start assigning each requirement to the control whose layer and scope it falls in. The subnet screen owns address-and-port screening at the workload's edge, for free, in every design. The managed firewall owns domain-based egress governance, central enforcement, inbound publishing, and threat intelligence, from the hub, whenever any of those is required. The appliance owns only the specific capabilities the managed service does not provide, and it earns its substantial ownership cost solely in those cases.

The fact that decides the most designs is the one worth carrying away above all others: a network security group cannot govern outbound traffic by domain name, because it operates below the layer where names exist. The moment a requirement is stated in domain names, the subnet screen is out and the managed firewall or the appliance is in. Conversely, the moment a requirement is purely address-and-port and local, the free subnet screen covers it and a paid central control adds cost without benefit. Most environments need both, layered, which is why the complement-not-compete rule is the through-line of the whole comparison.

Choose by reasoning, not by reflex. Restate each requirement in terms of its layer and scope, read it against the decision table, and the owner falls out. Put a screen on every subnet, route egress through a hub firewall, and reach for an appliance only when you can name the capability it provides that nothing else does. Revisit the appliance decision as the managed service grows, because the gap that justified it today may close tomorrow. A design built this way is cheaper, simpler, and more defensible in a review than one that forced a single product to do three jobs, and it fails more gracefully because each layer covers what the others cannot see. The deeper payoff is that the design stays legible as it grows: a new engineer can read the requirement, name the layer it lives at, and find the control that owns it without untangling a knot of overlapping rules spread across products that were never meant to overlap. Legibility is its own form of resilience, because a design people understand is a design people maintain correctly, and a design nobody fully understands drifts toward the silent failures that cost the most to find. To turn this reasoning into muscle memory, [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), where you can compare a subnet screen, a managed firewall, and an appliance against the same topology and watch each one's filtering behavior directly rather than reasoning about it on paper.

## Frequently asked questions

### Azure Firewall versus an NVA versus an NSG: which should I choose?

Choose by the question you are answering. Subnet-level address-and-port screening goes to a network security group, for free and close to the workload. Domain-based egress governance, central enforcement, and threat intelligence go to Azure Firewall in the hub. A third-party appliance is for capabilities the managed firewall lacks, such as a specific inspection engine or single-vendor parity with on-premises. Most designs use the screen and the firewall together.

### How do the three differ in statefulness and layer?

All three are stateful in that they track permitted connections and allow the return traffic without a reverse entry. They diverge by layer. The network security group works at layers three and four, seeing only addresses, protocols, and ports. Azure Firewall spans layers three, four, and seven, reading domain names and, in its premium tier, decrypted payloads. An appliance spans the same layers and often adds deeper inspection.

### Which of them controls egress and FQDN filtering?

Domain-name egress filtering belongs to Azure Firewall through its application rules, or to a network virtual appliance with an application-aware engine. A network security group cannot do it at all, because the domain name has been resolved to an address before the packet reaches the screen, and the screen never sees the name. This single limitation decides most designs that involve governing outbound internet access.

### When do I actually need a third-party NVA?

You need an appliance when a required capability has no other home: a specific intrusion-prevention or data-loss-prevention engine the managed firewall does not carry, single-vendor policy parity across cloud and on-premises, your own certificate authority for deep TLS inspection integrated with existing tooling, or a specialized routing behavior. If none of those applies, the appliance is usually a redundant cost and the managed firewall is the better choice.

### How do NSGs complement a hub firewall rather than compete with it?

They cover different scopes. A network security group screens traffic at the subnet, including lateral movement between workloads that never routes through the hub, which the central firewall never sees. The hub firewall governs the routed egress and cross-spoke flows, with domain rules and threat intelligence the subnet screen lacks. Layering both gives defense in depth: the screen catches close-in traffic, the firewall catches what leaves.

### How do Azure Firewall and an NVA compare on cost and management?

Azure Firewall charges hourly plus per gigabyte processed, and Microsoft operates the capacity, availability, and patching, so the operational burden is low. An appliance carries compute for a resilient pair, vendor licensing, a load balancer, and the full operational labor of sizing, patching, scaling, and recovery, which you own. Compare complete totals, not line items; for moderate volumes the managed service usually wins on cost and effort.

### Can a network security group block traffic to a specific website?

Not reliably. A network security group can block the address a website currently resolves to, but websites behind content delivery networks change addresses constantly and share addresses with unrelated sites, so an address-based block either breaks or over-blocks. Blocking a specific website by name requires Azure Firewall application rules or an appliance, because those evaluate the requested domain name rather than only the address.

### Why is my firewall not blocking traffic I expected it to block?

The most common cause is a routing fault rather than a policy gap. If the firewall logs show no entry for the flow, the traffic never reached the firewall, which means a missing or wrong user-defined route is sending it out the default internet path instead. Check the effective routes on the spoke interface and confirm the default destination's next hop is the firewall's private address.

### Do I still need NSGs if I deploy Azure Firewall?

Yes, in almost every case. The hub firewall governs traffic routed through it, but traffic that stays within a subnet or moves laterally between peers never reaches the hub and so is never inspected by the firewall. A network security group screens that lateral movement at the subnet for free, so keeping the screens adds a defense layer the firewall cannot provide and removing them saves nothing.

### What is the difference between Azure Firewall standard and premium for this decision?

The standard tier reads the requested domain name from the unencrypted Server Name Indication field of the TLS handshake, which is enough to govern which domains a workload may reach. The premium tier adds true TLS termination and decrypted-payload inspection plus a fuller intrusion-detection system. Choose standard for name-based egress governance and premium only when you must inspect the content inside encrypted sessions.

### Can an NSG do FQDN filtering with service tags?

No. Service tags name groups of Azure-owned address ranges that Microsoft maintains, which lets a network security group target Azure services such as storage or SQL cleanly. They do not cover arbitrary internet domains, because those live outside Azure and change independently. Service tags solve the Azure-endpoint case and leave the arbitrary-domain case unsolved, which is the gap Azure Firewall application rules exist to fill.

### How do I force spoke traffic through the firewall?

Attach a route table to each spoke subnet with a user-defined route that sends the default destination to the firewall's private address as the next hop. This overrides the platform's implicit internet route and draws the spoke's outbound traffic into the firewall for evaluation. Without this route the firewall is bypassed silently, so verifying the effective routes on a spoke interface is the essential confirmation step.

### What happens to return traffic when a stateful control is in the path?

The control permits the return traffic automatically. Because the network security group, Azure Firewall, and an appliance all track the connections they permit, the reply packets for an allowed connection flow back without any reverse entry. The only failure here is asymmetric routing, where the reply tries a different path than the request and the stateful control drops it because it never saw the original flow. Symmetric routing prevents that.

### Is an NVA more secure than Azure Firewall?

Not inherently. An appliance can carry inspection engines the managed firewall lacks, which adds capability in specific areas, but it also adds operational risk because you own its patching, scaling, and availability, and an unpatched or mis-scaled appliance is less secure than a managed service Microsoft keeps current. Security depends on the requirement and the operational discipline, not on the appliance being a third-party product.

### How do I decide between routing all traffic or only some through the firewall?

Route the traffic that benefits from inspection and central logging, and let traffic that needs neither take a more direct path. Flows that require domain governance, threat intelligence, or a central audit record should traverse the firewall; bulk flows to trusted Azure services can use a service endpoint or private link that avoids the firewall's data charge. This keeps the per-gigabyte cost proportionate to the governance you actually need.

### Can Azure Firewall replace my on-premises firewall vendor in the cloud?

It can replace the function for most cloud egress and inbound publishing needs, but it does not speak your vendor's policy language, so it will not give you a single policy model across cloud and on-premises. If unified vendor management across both environments is a hard requirement, an appliance running the same vendor's image preserves that single pane; if it is not, the managed firewall covers the cloud side with far less operational burden.

### How does threat intelligence work in Azure Firewall?

Azure Firewall can subscribe to a Microsoft-maintained feed of known-malicious addresses and domains and be set to either alert on or deny traffic to and from those endpoints. It applies the feed with no work from your team, giving a maintained baseline of protection that neither a network security group nor a bare appliance provides by default. An appliance can do similar filtering but brings its own feed and operational overhead.

### What is the single most common mistake teams make with these three controls?

Trying to enforce domain-based egress with a network security group. Teams write address entries hoping to constrain a workload to a set of public services, the addresses drift, and the rules either break or leak. The screen cannot see domain names, so the requirement belongs to Azure Firewall application rules or an appliance. Recognizing that a domain requirement cannot be solved at the address layer prevents the most frequent design failure in this space.
