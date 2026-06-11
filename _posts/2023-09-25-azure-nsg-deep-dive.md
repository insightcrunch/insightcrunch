---
layout: post
title: "Network Security Groups (NSG) Deep Dive"
page_title: "Azure Network Security Groups (NSG) Deep Dive: Rule Priority, Default Rules, Service Tags, ASGs, and Flow Logs Explained for Engineers"
date: 2023-09-25
categories: ["Technology"]
tags: ["Azure", "Network Security Group", "Networking", "NSG", "Security", "Cloud Infrastructure"]
excerpt: "A Network Security Group decides every flow by priority order across both the subnet and the interface, and this guide shows how to predict any allow or deny."
image: "/assets/images/blog/blog-40.webp"
reading_time: 61
author: "james-carter"
last_updated: 2023-09-25
lang: en
---
An engineer stares at a Network Security Group, sees an entry that plainly allows TCP 443 from the internet, and cannot understand why the connection still times out. The clause is right there, green and explicit, and the connection still dies. This is the single most common confusion in Azure filtering, and it comes from treating a security group as a checklist where any matching allow wins. It is not a checklist. A Network Security Group is an ordered decision engine, and the only allow that matters for a given packet is the first matching entry by priority, evaluated separately for the subnet and for the network interface, with a silent default deny waiting at the bottom of each list. Once you hold that model, the timeout stops being a mystery and becomes a prediction you can make before you ever open the portal.

![Network Security Groups deep dive evaluation map](/assets/images/blog/blog-40.webp)

This article builds the complete mental model of how a security group evaluates a packet, so that you can look at a set of security rules, a subnet association, and an interface association, and state with confidence whether a particular connection will be permitted or dropped. We will work through the definition model and its priority ordering, the default rules that ship with every group, the stacking of subnet and interface NSGs, the way service tags and application security groups compress and clarify large directive sets, and the flow logs that show you what the engine actually decided rather than what you assumed it would. The goal is not familiarity. The goal is the ability to reason from the mechanism, the same habit this series applies across [Azure networking fundamentals](/2023/08/28/azure-networking-fundamentals/), where filtering sits alongside routing as one of the two forces that govern whether a packet reaches its destination.

## What Is a Network Security Group and How Does It Decide Traffic?

A Network Security Group is a stateful packet filter that Azure attaches to a subnet, to a network interface, or to both, and that evaluates inbound and outbound flows against an ordered set of security rules. Each entry carries a priority number, a direction, a protocol, a source, a destination, a port range, and an action of allow or deny. The engine walks the rules in priority order for the relevant direction, and the first entry whose conditions match the packet decides the outcome. No later clause is consulted once a match is found.

The word stateful matters more than it first appears. When a security group permits an inbound connection, the return traffic for that same connection is allowed automatically, without a matching outbound definition, because the group tracks the connection state. The reverse holds for an allowed outbound session: its inbound responses are permitted without an explicit inbound entry. This is why a great many directive sets that look incomplete still work. People write an inbound allow for a web port and no corresponding outbound allow for the response, and the response flows anyway because the connection is already established and tracked. Understanding statefulness keeps you from writing redundant return rules and from misreading a working configuration as a broken one.

### How Does a security group Differ From a Firewall?

A security group is a distributed, entry-based packet filter operating at layers three and four, bound to subnets and interfaces, with no application awareness and no logging of allowed sessions by default. A firewall such as Azure Firewall is a managed appliance with stateful inspection, fully qualified domain name filtering, threat intelligence, and centralized logging. They solve adjacent problems and frequently run together.

The distinction is worth drawing carefully because the two controls are often confused, and the confusion leads to using one where the other belongs. A security group cannot filter by domain name, cannot inspect the application payload, and cannot apply a single egress policy across an entire hub and its spokes. A firewall can do all three, but it is a billed resource that sits in the path and adds a hop, whereas a security group is free, runs in the platform fabric, and adds no measurable latency. The series treats this trade in detail in the comparison of [Azure Firewall, network virtual appliances, and NSGs](/2023/10/30/azure-firewall-vs-nva-vs-nsg/), and the short version is that a security group handles micro-segmentation between workloads while a firewall handles inspected, centralized egress. They complement rather than replace each other.

## The First-Match-by-Priority Rule: How a security group Reaches a Verdict

Here is the claim this article is built around, the one to commit to memory: a security group decides a connection by the lowest-priority matching entry across both the subnet and the network interface, so predicting traffic is a matter of reading the entries in priority order, not guessing which allow looks most relevant. Call it the first-match-by-priority rule. Every confusing outcome resolves once you apply it directly.

Priority is a number between 100 and 4096 that you assign to each custom clause. Lower numbers are evaluated first, and lower numbers therefore win. A definition at priority 100 is considered before a directive at priority 200, and if the priority 100 entry matches the packet, the priority 200 entry is never reached. This inversion trips people up constantly, because intuition says a higher number should mean higher importance. In a security group the opposite is true. The number is a position in a queue, and the front of the queue holds the smallest number.

The engine evaluates inbound and outbound rules as two separate ordered lists. For an inbound packet, only inbound rules are consulted; for an outbound packet, only outbound rules. Within the relevant list, the engine compares the packet against each clause from the smallest priority number upward, checking whether the source, the destination, the protocol, and the port all fall within the definition's conditions. The first directive that matches on every condition fires its action, allow or deny, and evaluation stops. If no custom entry matches, the default rules at the very end of the list decide the outcome, and as we will see, the last default entry denies everything that reached it.

### Why Does a Lower Priority Number Win?

A lower priority number wins because Azure evaluates security rules in ascending numerical order and stops at the first match. Priority encodes position, not weight. A deny at priority 110 overrides an allow at priority 4000 for any packet both rules would match, because the engine reaches and applies the priority 110 entry first and never consults the later one.

This single behavior explains a large fraction of real incidents. An engineer adds a broad allow for a management subnet at priority 3000, then later adds a tighter deny for a specific address range at priority 200 to block a noisy scanner, and is surprised when legitimate management traffic from inside that range also stops. Both rules match the offending packets, but the priority 200 deny is reached first, so it decides. The fix is never to argue with the engine; it is to renumber so that the more specific allow sits above the broad deny, or to narrow the deny so it no longer overlaps the traffic you meant to keep. When you reason in priority order, the surprise disappears and the renumbering is obvious.

### Does an Allow Rule Guarantee Access?

No. An allow clause guarantees access only if it is the first matching definition for that packet and no lower-numbered directive on either the subnet NSG or the interface security group denies the same packet. An allow can be shadowed by a lower-priority deny above it, and an allow on one attachment cannot rescue a connection that the other attachment denies.

This is the counter-reading the model must defeat. People see an explicit allow and conclude the path is open, then spend an afternoon debugging a connection that a different entry, often on the other attachment point, has already dropped. The allow is necessary but not sufficient. It must be the entry the engine actually reaches, and it must not be contradicted by the second group in the stack. Holding both conditions in mind is the difference between guessing and knowing.

## The Default security group Rules: The Floor Every Group Stands On

Every Network Security Group ships with six default rules, three inbound and three outbound, that cannot be deleted and that occupy the highest priority numbers, meaning they are evaluated last, after all of your custom entries. They establish the baseline the platform guarantees, and understanding them is the difference between a clause set you can reason about and one you treat as superstition.

On the inbound side, the defaults are, in evaluation order by priority: AllowVNetInBound at priority 65000, which permits traffic where both source and destination carry the VirtualNetwork service tag, so resources inside the virtual network and its peered and connected networks can reach each other; AllowAzureLoadBalancerInBound at priority 65001, which permits the Azure load balancer health probe and management traffic that arrives from the AzureLoadBalancer service tag; and DenyAllInBound at priority 65500, which drops everything that no earlier definition allowed. On the outbound side: AllowVNetOutBound at 65000, AllowInternetOutBound at 65001 which permits outbound flows to the Internet service tag, and DenyAllOutBound at 65500.

The shape of this baseline is the whole story. Inbound traffic from outside the virtual network is denied unless you explicitly allow it, because the only inbound allows by default are intra-VNet and load balancer traffic, and everything else falls through to DenyAllInBound. Outbound traffic, by contrast, is open by default, because AllowInternetOutBound permits egress to the internet before the outbound deny is ever reached. New engineers are often startled that a freshly created virtual machine can reach the internet with no rules written, yet cannot be reached from the internet without one. The defaults explain both facts at once.

### What Happens If No Custom Rule Matches a Packet?

If no custom directive matches, the packet falls through to the default rules. Inbound, that means DenyAllInBound drops it unless it was intra-VNet or load balancer traffic caught by a default allow. Outbound, AllowInternetOutBound or AllowVNetOutBound usually permits it before DenyAllOutBound is reached. The default deny is the silent cause of most inbound timeouts.

The practical lesson is to design as though the default deny is always watching, because it is. You do not block inbound traffic by writing deny rules; the platform already denies by default. You open precisely the flows you intend with explicit allows, and you leave everything else to fall through to the default deny. An entry set that is mostly allows with a tightly scoped set of denies for exceptions is healthier than one that tries to enumerate every deny, because the former works with the default and the latter fights it.

### Can You Override a Default Rule?

You cannot delete a default entry, but you can override its effect by writing a custom clause with a lower priority number that matches the same traffic. A custom deny at priority 4000 for internet-bound traffic will be reached before AllowInternetOutBound at 65001, so it overrides the permissive default for the flows it matches without removing the default itself.

This is the supported way to close down the open egress that the defaults grant. Many security baselines add a low-numbered DenyAllOutBound override, then layer specific allows above it for the destinations a workload genuinely needs, recreating a default-deny posture for egress that the platform does not provide out of the box. The defaults remain in place beneath your custom rules; you simply ensure the engine reaches your intent first.

## The InsightCrunch filter Evaluation Map

To turn the first-match-by-priority rule into something you can apply mechanically, this is the InsightCrunch group evaluation map: a fixed procedure for taking any session and any pair of associations and arriving at the verdict the platform would reach. Run it the same way every time and you will stop guessing.

The procedure has five steps. First, identify the connection precisely: the direction relative to the resource, the source address or tag, the destination address or tag, the protocol, and the port. Second, find the two definition lists that apply, the security group on the subnet and the group on the network interface, remembering that one or both may be absent. Third, for inbound traffic, evaluate the subnet security group first and then the interface NSG; for outbound traffic, evaluate the interface NSG first and then the subnet security group. Fourth, within each group, walk the rules for the matching direction in ascending priority order and record the first directive that matches the packet on every condition. Fifth, the connection is permitted only if both evaluated NSGs allow it; if either one denies or falls through to its default deny, the session is dropped.

That ordering in the third step is the detail people miss. For inbound packets the subnet NSG is applied before the interface one, and for outbound packets that order reverses. The traffic must clear both regardless of order, so the order itself rarely changes the final verdict, but it changes which security group you should inspect first when you are debugging, and it explains the sequence you see in flow logs. The decisive entry is the conjunction at the end: both attachments must allow, so a single deny anywhere in the stack is final.

The evaluation map renders cleanly as a worked table. Consider a virtual machine whose interface sits in a subnet, where the subnet carries one filter and the interface carries another, and a client on the internet attempts to reach TCP 443.

| Step | What you evaluate | Example input | Example result |
| --- | --- | --- | --- |
| 1. Define the connection | Direction, source, destination, protocol, port | Inbound, internet client, VM private IP, TCP, 443 | Flow defined |
| 2. Find both NSGs | Subnet group and interface security group | Subnet group present, interface security group present | Two lists to evaluate |
| 3. Order of evaluation | Inbound: subnet then interface | Subnet first | Sequence set |
| 4a. Subnet filter match | First matching entry by priority | Allow 443 from internet at priority 300 | Subnet allows |
| 4b. Interface group match | First matching clause by priority | No custom allow for 443, falls through to DenyAllInBound | Interface denies |
| 5. Final verdict | Both must allow | Subnet allows, interface denies | Flow dropped |

Read the table from top to bottom and the timeout from the opening of this article finally makes sense. The subnet definition that allowed 443 was real, and the engineer was looking straight at it, but the interface security group never had a matching allow, so it fell through to its own DenyAllInBound and dropped the connection. The allow was true and useless, because the conjunction at step five requires both. The lab environment in [VaultBook](https://vaultbook.org) reproduces exactly this two-group stack and lets you toggle each directive and watch the verdict change, which is the fastest way to internalize the map until you can run it in your head. Building the rules by hand, watching one allow get overridden by a deny on the other attachment, and reading the resulting flow log is worth more than any amount of reading, and VaultBook's command library carries the Azure CLI and PowerShell to recreate the scenario in your own subscription.

### How Do I Predict Whether a Flow Will Be Allowed?

Run the evaluation map. Define the packet, locate the subnet security group and the interface NSG, walk each one in ascending priority order to its first matching entry, and apply the conjunction: the connection is allowed only if both NSGs allow it. If either denies or falls through to the default deny, the session is dropped. No allow on one side rescues a deny on the other.

The strength of the map is that it removes intuition from the loop. You are not asking which entry feels most relevant; you are asking, list by list, which clause the engine reaches first and what it does. Once the procedure is a habit, you predict outcomes faster than the portal can render the definition blades, and you stop being surprised by shadowed allows and silent default denies.

## Subnet and Interface: Why Both NSGs Always Apply

A security group can attach to a subnet or to a network interface, and Azure permits both at once on the same resource. When both are present, both are evaluated, and the traffic must be allowed by both to pass. This is the stacking behavior that the evaluation map encodes, and it is the source of more debugging hours than any other group feature.

Attaching at the subnet level applies one directive set to every network interface in that subnet, which is the right altitude for broad, role-based policy: the database subnet allows SQL only from the application subnet, the web subnet allows 443 from the internet, and so on. Attaching at the interface level applies an entry set to a single resource, which is the right altitude for an exception or a per-machine refinement. The two layers are not redundant; they are different scopes of the same control. A subnet security group expresses the policy for a tier, and an interface NSG expresses the policy for one member of that tier.

The trap is that the two layers can disagree, and when they disagree the more restrictive one wins because of the conjunction. A subnet security group that allows 443 means nothing if the interface NSG on a particular machine lacks a matching allow, and an interface NSG that allows SSH means nothing if the subnet security group denies it. Engineers who manage the subnet and the interface separately, or who inherit a subnet policy they did not write, routinely add an allow at one layer and forget that the other layer still denies. The evaluation map catches this every time, because it forces you to inspect both lists rather than the one you happen to be editing.

### Should a security group Attach to a Subnet or a Network Interface?

Prefer the subnet for policy that applies to a whole tier, because it is fewer objects to manage and it covers new interfaces automatically as machines are added. Reserve the interface NSG for genuine per-machine exceptions. Attaching at both levels is supported and sometimes correct, but remember that both must allow, so two layers double the places a connection can be blocked.

The operational guidance that follows is to keep one authoritative layer wherever you can. If your segmentation is tier-based, put it on subnets and leave interfaces unassociated, so there is exactly one rule set to read per packet. Introduce an interface security group only when one machine genuinely needs a different policy than its subnet peers, and document why, because the next engineer will run the evaluation map and needs to understand why two lists exist. When you do run both, treat the subnet NSG as the coarse policy and the interface NSG as the narrow refinement, never as two independent attempts to express the same intent.

### What If the Subnet security group and the Interface group Conflict?

When they conflict, the deny wins, because a connection must be allowed by both the subnet security group and the interface NSG to pass. There is no precedence by attachment type and no merge of the two rule sets into one. Each is evaluated independently against the packet, and a single deny or a single fall-through to default deny on either attachment is final for that session.

This is worth stating plainly because people look for a tiebreaker rule and there is none. The subnet does not outrank the interface, and the interface does not outrank the subnet. The platform evaluates each group to a verdict and then requires both verdicts to be allow. If you find yourself wishing one layer could override the other, that is the signal to consolidate to a single layer rather than to search for a precedence that does not exist.

## Service Tags: Naming the Moving Targets

A service tag is a named group of IP address prefixes that Microsoft maintains and updates, letting you write a rule against a logical destination such as Storage or Sql or AzureCloud instead of an address range you would otherwise have to track by hand. When the underlying prefixes change, the tag updates with them, and your rule keeps meaning what you intended without an edit. Service tags are the answer to the question of how to allow a managed Azure service whose addresses you do not control and should not hardcode.

The built-in defaults already use service tags: VirtualNetwork, AzureLoadBalancer, and Internet are the tags behind the six default rules. You write your own rules against the same vocabulary. To permit a virtual machine to reach Azure Storage in its own region without opening the whole internet, you target the regional Storage tag rather than a list of storage front-end addresses. The rule reads as intent rather than as arithmetic, and it survives the next time Microsoft rotates the storage fleet's addresses.

A small Azure CLI example shows the shape of a service-tag rule. The command creates an outbound allow that lets resources in the subnet reach Azure Storage in the West Europe region over HTTPS, while everything else outbound still falls to whatever deny you have layered in.

```bash
az network nsg rule create \
  --resource-group rg-network \
  --nsg-name nsg-app-tier \
  --name AllowStorageOutbound \
  --priority 200 \
  --direction Outbound \
  --access Allow \
  --protocol Tcp \
  --destination-address-prefixes Storage.WestEurope \
  --destination-port-ranges 443 \
  --source-address-prefixes VirtualNetwork \
  --description "Permit HTTPS egress to regional Azure Storage"
```

The destination prefix is the regional service tag, written as the service name and the region joined by a dot. Regional tags are tighter than the global tag and should be preferred when the service offers them, because allowing Storage globally is far broader than allowing Storage.WestEurope. The same pattern works for Sql.WestEurope, AzureKeyVault.WestEurope, and the many other services that publish regional tags. When you allow a managed service this way, you are describing the dependency rather than chasing its addresses, which is the entire point.

### How Do Service Tags Simplify a Broad Allow?

Service tags replace a fragile list of IP prefixes with a single maintained name, so a rule that would otherwise need dozens of ranges, each subject to change, becomes one entry that Microsoft keeps current. You allow Storage or Sql or AzureMonitor by intent, the prefixes update automatically, and your rule set stays both shorter and correct as the platform's addresses shift underneath it.

The discipline that pays off is to reach for the narrowest tag that expresses the dependency. AzureCloud is enormous, the regional variants are smaller, and the per-service regional tags are smaller still. A rule that says AllowAzureCloudOutbound has opened the egress to nearly everything Azure runs, which is rarely the intent. A rule scoped to Sql.WestEurope says precisely what the workload needs and nothing more, and it is the kind of entry a security reviewer can read and approve without a spreadsheet of addresses to verify.

## Application Security Groups: Grouping by Role, Not by Address

An application security group, or ASG, lets you assign network interfaces to a named group and then write rules whose source or destination is that group, so your policy speaks in terms of application roles rather than IP addresses. Instead of allowing the web tier to reach the application tier by listing the application machines' addresses, you put the application interfaces in an ASG called asg-app, the web interfaces in asg-web, and write a rule that allows asg-web to reach asg-app on the application port. New machines join the role by joining the ASG, and the rule needs no edit.

The power of ASGs shows in environments where addresses are dynamic or numerous. A scale set adds and removes instances constantly, and any rule pinned to specific addresses is wrong the moment the set scales. An ASG-based rule remains correct because membership, not address, defines the group. The same holds for a tier that spans multiple subnets: the role is the constant, the addresses are not, and the ASG captures the role. ASGs also document intent in a way address ranges never can, because asg-web to asg-app on the application port reads as architecture, while 10.1.2.0/24 to 10.1.3.0/24 reads as a puzzle.

A CLI sketch shows the assembly. First the groups are created, then interfaces are placed into them, then a rule references them as source and destination.

```bash
# Create the application security groups
az network asg create --resource-group rg-network --name asg-web --location westeurope
az network asg create --resource-group rg-network --name asg-app --location westeurope

# Associate a network interface's IP configuration with an ASG
az network nic ip-config update \
  --resource-group rg-network \
  --nic-name nic-web-01 \
  --name ipconfig1 \
  --application-security-groups asg-web

# Allow the web role to reach the app role on the application port
az network nsg rule create \
  --resource-group rg-network \
  --nsg-name nsg-app-tier \
  --name AllowWebToApp \
  --priority 300 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-asgs asg-web \
  --destination-asgs asg-app \
  --destination-port-ranges 8080 \
  --description "Permit web tier to reach app tier"
```

The rule names roles, and the membership lists do the rest. As the web tier scales, each new interface that joins asg-web inherits the permission with no rule change, and as the application tier scales, each interface that joins asg-app becomes reachable from the web tier automatically. This is segmentation that scales with the architecture instead of fighting it, and it is the recommended way to express tier-to-tier policy in any environment large enough that addresses are not stable.

### How Do Service Tags and Application Security Groups Differ?

Service tags name groups of IP prefixes that Microsoft maintains for Azure services and the internet, used when the other end is a managed platform you do not control. Application security groups name groups of your own network interfaces by role, used when both ends are your resources. Tags handle the platform side of a rule; ASGs handle your side. Many rules use both together.

The combination is the idiom to aim for. A rule that allows asg-web as the source and Storage.WestEurope as the destination uses an ASG for your machines and a service tag for the platform dependency, and it reads as a single clear statement of who may talk to what. When you find yourself typing an address range into a rule, pause and ask whether a tag or an ASG would say it better, because in most production rule sets the literal address is the exception, not the norm.

## security group Flow Logs: Seeing the Decision the Engine Made

filter flow logs record the flows that a security group evaluated, including the action it took, and write them to a storage account where you can read them or feed them into traffic analytics for aggregation and visualization. They are the ground truth of what the filter actually did, as opposed to what you believe the rules say it should do, and they are the single most underused diagnostic in Azure networking. The evaluation map predicts an outcome; the flow log confirms it.

A flow log entry captures the five-tuple of a flow, the source and destination addresses, the source and destination ports, and the protocol, along with the direction, whether the flow was allowed or denied, and which rule made the decision. When a connection mysteriously fails, the flow log tells you whether the packet even reached the group, which rule matched it, and whether that rule allowed or denied. This converts debugging from speculation into reading. You stop asking why the connection might be failing and start reading which rule denied it and on which attachment.

Flow logs come in versions, and the later version records additional state about whether a flow was begun, continued, or ended, along with byte and packet counts in each direction, which lets you distinguish a flow that was denied at the first packet from one that was allowed and then went quiet for an application reason. Traffic analytics builds on the logs to show top talkers, denied flow patterns, and the rules that fire most often, which surfaces both attacks and misconfigurations that a single flow log line would not reveal on its own. Enabling flow logs on every security group carrying production traffic is one of those investments that costs little and repays itself the first time an incident would otherwise have been a guessing game.

Enabling flow logs from the CLI ties a security group to a storage account and a Network Watcher in the same region. The command below turns on logging for a single NSG and points it at a storage account, with traffic analytics attached to a Log Analytics workspace for aggregation.

```bash
az network watcher flow-log create \
  --resource-group rg-network \
  --name fl-nsg-app-tier \
  --nsg nsg-app-tier \
  --storage-account stflowlogs \
  --enabled true \
  --retention 30 \
  --traffic-analytics true \
  --workspace law-network \
  --location westeurope
```

Once the log is flowing, the denied entries are where you look first during an incident. A burst of denied inbound flows to a port you expected to be open points straight at a missing or shadowed allow, and the rule field tells you whether the deny came from a custom entry or from a default DenyAllInBound, which tells you whether you have a wrong rule or a missing one. The VaultBook lab environment includes the storage account and workspace wiring so you can generate real denied connections and read them back, which is the fastest way to get fluent at interpreting the log fields under time pressure.

### How Do NSG Flow Logs Give Traffic Visibility?

Flow logs write every evaluated flow, with its five-tuple, direction, allow-or-deny action, and the deciding rule, to a storage account, and traffic analytics aggregates them into talkers, denied patterns, and frequently firing rules. Together they show what the NSG actually decided rather than what the rules appear to say, turning a connectivity mystery into a record you can read line by line.

The habit to build is to enable flow logs before you need them, not during the incident, because logs only capture flows that occurred while logging was on. An NSG without flow logs is a filter making decisions in the dark, and the first sign of trouble is exactly when you wish you had the record. Turn them on across the environment, set a sensible retention, and wire traffic analytics so that the aggregated view is there waiting when a pattern of denials needs explaining.

## The Failure Modes and How to Read Them

Most NSG incidents are one of a small set of recurring patterns, and each one is a direct consequence of the model we have built. Naming them makes them diagnosable, because once you recognize the pattern you already know where to look.

The first pattern is the subnet-allows-while-interface-denies case, the one from the opening table. The flow has an allow on the subnet NSG and no matching allow on the interface NSG, so it falls through to the interface's default deny and dies. The symptom is a timeout despite a rule that plainly permits the traffic, and the diagnosis is to run the evaluation map across both attachments rather than the one you were editing. The flow log on the interface NSG shows the deny against DenyAllInBound, which is the tell.

The second pattern is the low-priority deny that shadows a higher-numbered allow. A broad deny sits at a small priority number and matches traffic that a later, larger-numbered allow was meant to permit. Because the deny is reached first, the allow never fires. The symptom is that adding an allow rule does nothing, and the diagnosis is to sort the rules by priority and read downward until you find the first rule that matches the flow, which will be the deny. The fix is to renumber the allow below the deny or to narrow the deny so it stops matching the wanted traffic.

The third pattern is relying on the default deny without an explicit allow. Someone assumes that because the architecture diagram shows a connection, the connection is permitted, but no rule was ever written and the default DenyAllInBound is doing exactly its job. The symptom is a flow that never worked rather than one that stopped working, and the diagnosis is to confirm whether any custom allow matches the flow at all. This pattern is common right after deployment, when the infrastructure exists but the intended allows were never created.

The fourth pattern is the service-tag scope that is too broad or too narrow. A rule allows AzureCloud when it meant a single service, opening far more than intended, or allows a global tag when a regional one was required and a cross-region flow is unexpectedly permitted or denied. The symptom is a flow that is allowed when it should not be, or a regional dependency that breaks, and the diagnosis is to read the tag in the matching rule and ask whether its scope matches the intent.

The fifth pattern is the ASG membership that was never applied. A rule references an ASG correctly, but the interface that should belong to the group was never added to it, so the rule matches nothing for that machine. The symptom is that one machine in a tier behaves differently from its peers, and the diagnosis is to check the interface's IP configuration for its ASG membership. The rule is right; the membership is missing.

The sixth pattern is the missing flow log itself, where an incident cannot be diagnosed because no record exists of what the NSG decided. This is less a failure of the filter than a failure of preparation, and its only fix is the discipline of enabling logging in advance. When you meet an NSG mystery with no flow log, the first action is to enable the log, reproduce the flow, and read the result, after which the incident usually resolves quickly.

### Why Does a Flow Fail When an Allow Rule Exists?

Because the allow is not the rule the engine reaches first, or because the other attachment denies the same flow. A lower-priority deny above the allow shadows it, or the interface NSG falls through to its default deny while the subnet NSG allows. Run the evaluation map across both attachments and read the flow log to find the deciding rule.

The discipline that resolves all six patterns is the same: stop trusting the rule that looks relevant and start tracing the rule the engine actually applies, list by list, in priority order, across both attachments, and confirm it against the flow log. Every one of these failures is invisible to intuition and obvious to the procedure. The model is the diagnostic; the patterns are just the model failing in predictable ways. When a flow misbehaves and the rules look correct, the series troubleshooting reference on [fixing an NSG that blocks traffic unexpectedly](/2022/11/21/fix-nsg-blocking-traffic/) walks the same patterns from the symptom side, and pairing the mechanism here with the symptom-first walkthrough there is the fastest path from confusion to a confirmed cause.

## How an NSG Interacts With the Rest of the Network

A Network Security Group does not operate alone. A packet's fate is decided by both routing and filtering, and the NSG is only the filtering half. Understanding where the filter sits relative to the route table, the firewall, and the peering boundary keeps you from blaming the NSG for a problem that lives elsewhere, and from blaming routing for a deny that the NSG owns.

Routing decides where a packet goes; the NSG decides whether it is allowed once its path is set. Azure applies the effective route table to choose the next hop, and the NSG evaluates the flow against its rules, and both must cooperate for the packet to arrive and be accepted. A user-defined route that sends traffic to a network virtual appliance changes the path, and the NSG still evaluates the flow on the interfaces and subnets it touches. When a flow fails, the first fork in the diagnosis is whether the packet was misrouted or filtered, and the two are answered by different tools: the effective routes for the path, the NSG flow log for the filter. The series treats the routing half in the deep dive on [Azure route tables and user-defined routes](/2023/12/11/azure-route-tables-udr-explained/), and the pairing of that article with this one gives you both forces in one mental model, which is exactly the route-then-filter reasoning that diagnoses connectivity properly.

A subtle interaction arises when a user-defined route forces traffic through a firewall or appliance. The NSG on the source subnet may allow the flow, the route may send it to the firewall, the firewall may allow or deny it, and the NSG on the destination subnet may then evaluate the flow again when it arrives. A single connection can therefore be checked by two NSGs and a firewall, and any one of them can drop it. Engineers who think of the NSG as the only gate are surprised when a flow the NSG allows is stopped at the firewall, or when a flow the firewall allows is stopped by the destination subnet's NSG. The discipline is to enumerate every control on the path and confirm each one rather than assuming the first allow you find is the whole answer.

Peering adds another wrinkle worth naming. The VirtualNetwork service tag in the default rules includes peered virtual networks and connected on-premises ranges, so the default AllowVNetInBound permits traffic from a peered network as though it were local. This is convenient and occasionally surprising: peer two networks and the default rules already allow intra-tag traffic between them, so segmentation between peered networks requires explicit denies or tighter allows rather than reliance on the default. When you peer networks that should not freely communicate, the NSG rules, not the peering itself, are where you enforce the boundary.

### Does an NSG Control Routing?

No. An NSG only filters traffic; it never changes where a packet is routed. Routing is decided by the effective route table and any user-defined routes, which choose the next hop, while the NSG independently allows or denies the flow on the subnets and interfaces it touches. A misrouted packet and a filtered packet are different failures diagnosed with different tools.

Keeping the two responsibilities separate in your head is the key to fast diagnosis. When connectivity breaks, ask first whether the path is correct by reading the effective routes, and only then whether the filter permits the flow by reading the rules and the flow log. Conflating the two sends you editing NSG rules to fix a routing problem, or rebuilding routes to fix a filtering problem, and both waste the afternoon.

## Diagnostic Tooling Beyond the Flow Log

Flow logs tell you what happened, but two other Network Watcher capabilities tell you what will happen and what is currently in force, which is often what you need before traffic has even flowed. The effective security rules view and the IP flow verify check are the companions to the evaluation map, because they let the platform run the map for you.

The effective security rules view shows the combined, evaluated rule set that applies to a network interface, merging the subnet NSG and the interface NSG into the ordered list the engine actually uses. This is invaluable when two attachments are in play, because it spares you from mentally merging two lists and shows you the real priority-ordered sequence including the defaults. Reading the effective rules for an interface is the fastest way to find a shadowed allow or a forgotten deny, because the shadowing is visible directly in the ordering.

IP flow verify takes a specific flow, a direction, a local and remote address, a protocol, and a port, and reports whether the NSG configuration would allow or deny it, naming the rule that decides. It is the evaluation map executed by the platform against the live configuration. When you want to confirm before deployment that a flow will be permitted, or to prove during an incident that the NSG is or is not the cause, IP flow verify gives a definitive answer in seconds.

```bash
# Run IP flow verify for an inbound HTTPS flow to a VM
az network watcher test-ip-flow \
  --resource-group rg-network \
  --vm vm-web-01 \
  --direction Inbound \
  --protocol TCP \
  --local 10.1.1.4:443 \
  --remote 203.0.113.10:51000 \
  --nic nic-web-01
```

The output names the access result and the rule that produced it. If the result is a deny against DenyAllInBound, you have a missing allow; if it is a deny against a named custom rule, you have a shadowing or scoping problem in that rule; if it is an allow yet the connection still fails, the NSG is exonerated and the problem lives in routing, the firewall, the guest operating system firewall, or the application itself. This single command resolves the perennial question of whether the NSG is the culprit, and it does so without waiting for a flow log to populate. The VaultBook command library keeps tested invocations of effective security rules and IP flow verify alongside the rule-creation commands, so you can move from building a rule to proving its effect without leaving the lab.

### What Is the Fastest Way to Confirm an NSG Is Blocking a Flow?

Run IP flow verify in Network Watcher for the exact flow in question. It evaluates the live NSG configuration and reports allow or deny along with the deciding rule, in seconds, without waiting for traffic or flow logs. A deny against DenyAllInBound means a missing allow; a deny against a named rule means a scoping or shadowing problem; an allow exonerates the NSG entirely.

The reason this matters is that it ends the argument about whether the NSG is at fault before it starts. Half of debugging here is, in practice, proving the filter is not at fault so attention can move to routing or the application. IP flow verify settles that in one command, and the effective security rules view explains the verdict by showing the ordered list that produced it. Between the two, you rarely need to guess.

## Designing NSGs for Production

The model so far explains how the engine behaves. Designing for production is the matter of arranging rules so the engine's behavior matches your intent reliably, survives change, and stays readable to the next engineer. A few principles do most of the work.

Choose one authoritative attachment layer per flow wherever the architecture allows. The fewer NSGs a flow must clear, the fewer places it can be silently dropped, and the easier the evaluation map is to run. Tier-based segmentation belongs on subnets, where it covers every interface automatically and reads as one rule set per tier. Reserve interface NSGs for the rare machine that genuinely needs a different policy, and when you use one, document the reason so the second list is not a mystery. Two layers are sometimes correct, but every additional layer is another conjunction the flow must satisfy and another list a debugger must read.

Number rules with deliberate spacing rather than consecutively. Priorities of 100, 110, 120 leave no room to insert a rule between two existing ones without renumbering, while priorities of 100, 200, 300 leave a comfortable gap for the inevitable later insertion. Reserve low numbers for the few high-precedence denies that must override everything, a middle band for the role-to-role allows that carry the workload, and a high band for broad fallbacks, so that reading the rule set top to bottom tells a coherent story about precedence. A rule set whose numbering encodes its logic is one you can reason about months later.

Express policy in tags and ASGs, not addresses, so the rules survive scaling and re-addressing. A rule that names asg-web and Storage.WestEurope keeps meaning the right thing as machines come and go and as Microsoft rotates the storage fleet, while a rule pinned to literal ranges drifts out of correctness the moment the topology changes. Treat a literal address in a rule as a smell to investigate, not a default to reach for. When you must use a literal range, comment it in the rule description so the reason is recorded.

Layer an explicit egress deny when the workload's security posture requires it, because the platform leaves outbound open by default. A low-numbered DenyAllOutBound override with specific allows above it for the destinations the workload needs recreates a default-deny egress posture, which many compliance regimes expect. Build this deliberately and test it with IP flow verify before it reaches production, because an over-tight egress deny breaks platform dependencies such as monitoring, key retrieval, and update channels in ways that are tedious to diagnose after the fact.

Enable flow logs and traffic analytics on every NSG that carries production traffic, before any incident, with a retention that matches your investigation window. The cost is small and the payoff is the difference between reading what happened and guessing. Wire traffic analytics so the aggregated view of denied patterns and top talkers is there when you need it, because the moment you wish you had the data is precisely the moment it is too late to start collecting it.

Make the whole configuration reproducible as code. NSGs defined in Bicep or Terraform, with rules expressed against ASGs and service tags, give you a reviewable, version-controlled record of intent that a portal click can never match. A code review of an NSG change shows the diff in precedence and scope, which is exactly where the dangerous mistakes hide, and a redeployment from code recreates the exact rule set rather than an approximation assembled by memory.

### How Should I Structure NSG Rules for a Multi-Tier Application?

Put tier policy on subnets, one NSG per tier, and express tier-to-tier flows with ASGs as source and destination. Allow only the ports each tier needs from the tier that needs them, scope managed-service egress with regional service tags, and lean on the default deny for everything else. Number rules with gaps, enable flow logs, and define it all as code.

A three-tier web application makes the pattern concrete. The web subnet's NSG allows 443 from the internet to asg-web and allows asg-web to reach asg-app on the application port. The application subnet's NSG allows asg-app inbound from asg-web on the application port and allows asg-app outbound to Sql.WestEurope on 1433 and to Storage.WestEurope on 443. The data subnet's NSG allows the database port inbound only from asg-app and denies everything else inbound. No tier allows more than the adjacent tier requires, every cross-tier flow is named by role, every platform dependency is a regional tag, and the default deny closes the rest. The result is segmentation that reads as architecture and scales as the tiers scale.

## A Worked End-to-End Diagnosis

To put every piece together, walk a realistic incident from symptom to confirmed cause using only the model and the tooling. An application team reports that a newly deployed virtual machine in the application subnet cannot reach Azure SQL, while its identical neighbor in the same subnet can. The connection from the new machine times out; the neighbor works. Nothing in the architecture diagram explains the difference.

Begin with the evaluation map. The flow is outbound, from the new machine's private address, to the regional SQL endpoint, over TCP 1433. For outbound traffic the interface NSG is evaluated before the subnet NSG, so inspect the interface first. The new machine has one; the neighbor does not. This asymmetry is the first clue, because it explains why two machines in one subnet behave differently. Read its outbound rules in priority order and look for the first rule that matches a flow to Sql.WestEurope on 1433.

The interface NSG has an outbound allow for Storage.WestEurope but none for Sql, and a low-numbered DenyAllOutBound override that someone added to tighten the machine. The SQL flow matches no allow, reaches the DenyAllOutBound override, and is dropped. The subnet NSG would have allowed it, but the conjunction requires both, and the interface denies. The neighbor, having no interface NSG, clears only the subnet NSG, which allows the flow, so it works.

Confirm rather than assume. Run IP flow verify for the outbound flow on the new machine's interface and read the result: a deny against the custom DenyAllOutBound rule on the interface NSG. That is the proof. The effective security rules view for the interface shows the override sitting above where a SQL allow would need to be, which explains the shadowing directly. The flow log, once read, shows the denied outbound flow against the named override rule, corroborating the verdict a third way.

The fix follows from the diagnosis. Add an outbound allow for Sql.WestEurope on 1433 to the interface NSG at a priority below the DenyAllOutBound override, scoped by an ASG if other machines will need the same, and re-run IP flow verify to confirm the verdict flips to allow against the new rule. The incident closes not with trial and error but with a traced cause and a confirmed fix, which is exactly what the model is for. The reproducible version of this entire scenario, with the asymmetric interface NSG and the shadowing override, lives in the VaultBook lab so you can run the diagnosis end to end before you meet it in production.

### Why Do Two Identical Machines in One Subnet Behave Differently?

Almost always because one carries an interface NSG that the other lacks, adding a second rule list that the flow must also satisfy. The subnet NSG treats both machines alike, but the interface NSG on one machine can deny a flow the subnet allows, since both must allow for the flow to pass. Check each machine's interface for an attached NSG first.

This asymmetry is one of the most reliable diagnostic shortcuts in the whole subject. When peers in a subnet diverge, the cause is rarely the shared subnet policy and almost always a per-interface attachment or membership difference: an interface NSG on one and not the other, or an ASG membership applied to one and forgotten on the other. Checking the per-interface configuration first turns a baffling difference into a two-minute confirmation.

## The Anatomy of a Security Rule in Detail

A custom security rule is more expressive than the simple allow-this-port mental shorthand suggests, and knowing the full anatomy prevents both over-broad rules and ones that fail to match the flow you meant. Each rule carries a name, a priority, a direction, an access of allow or deny, a protocol, a source, a source port range, a destination, a destination port range, and an optional description.

The protocol field accepts TCP, UDP, ICMP, or the asterisk that matches any protocol. Reaching for the asterisk is convenient and almost always wrong for an allow, because it opens UDP and ICMP alongside the TCP you intended. A web allow should name TCP, a DNS allow should name UDP and TCP as appropriate, and only a deliberate any-protocol policy should use the wildcard. The same caution applies to the destination port range: an allow that names the asterisk for ports opens every port, which is rarely the intent behind a rule that was supposed to permit a single service.

Augmented rules let a single rule carry multiple source prefixes, multiple destination prefixes, multiple port ranges, multiple service tags, and multiple ASGs, which collapses what would otherwise be many rules into one readable entry. Rather than three separate allows for three management ranges, one augmented rule lists all three sources. Rather than separate allows for 80 and 443, one rule lists both ports. This keeps the rule count low and the intent legible, and it reduces the priority-numbering pressure that comes from a sprawling rule set. The trade-off is that an augmented rule must be read carefully, because a single entry now expresses several conditions, and a reviewer must check each one.

Source and destination accept an address prefix in CIDR notation, a service tag, an ASG, the VirtualNetwork or AzureLoadBalancer or Internet keyword, or the asterisk for any. The richer the vocabulary you use, the more the rule reads as intent. A source of asg-web and a destination of asg-app says who talks to whom; a source of a CIDR block and a destination of another CIDR block says nothing about why. Prefer the named forms, fall back to CIDR when no name fits, and reserve the asterisk for the genuine any-source or any-destination case such as an internet-facing allow.

The port range deserves a specific caution about the difference between the source port and the destination port. The destination port is the service port you almost always mean to control, such as 443 for HTTPS or 1433 for SQL. The source port is the ephemeral port the client picked, which is effectively random and should almost always be the asterisk. Engineers occasionally pin the source port to a service number by mistake, producing a rule that matches almost nothing because real clients never use that source port. When a rule that looks correct matches no traffic, an over-specified source port is a frequent and easily missed cause.

### What Is the Difference Between the Source Port and the Destination Port in an NSG Rule?

The destination port is the service port the flow is reaching, such as 443 or 1433, and it is what you almost always control. The source port is the ephemeral port the client chose, which is effectively random and should be left as the asterisk. Pinning the source port to a service number produces a rule that matches almost no real traffic.

This distinction causes a quiet class of bugs because the rule looks reasonable at a glance. The fields are symmetric in the form, so it is easy to enter the service port in the source position by habit, and the rule then silently fails to match. When debugging a rule that appears correct yet never fires, reading the source port field and confirming it is the wildcard is a fast check that catches the mistake.

## The Recurring Scenarios the Model Explains

The brief for this subject names a handful of patterns that engineers report again and again, and each one is now just an application of the model. Walking them as a set shows how a single mechanism accounts for the whole landscape of NSG behavior.

A subnet NSG allows while a NIC NSG denies, and the flow dies despite the visible allow. The conjunction requires both attachments to allow, so the NIC's default deny or explicit deny is final. The diagnosis is the evaluation map across both lists, confirmed with IP flow verify, and the fix is to add the matching allow to the interface NSG or to remove the unnecessary interface attachment.

A low-priority custom deny overrides a higher-numbered allow, and adding the allow seems to accomplish nothing. The engine reaches the smaller-numbered deny first and stops. The diagnosis is to sort by priority and read to the first match, and the fix is to renumber the allow beneath the deny or narrow the deny so it no longer overlaps the wanted flow.

A workload relies on the default deny without an explicit allow, so a connection that the diagram implies was never actually permitted. The diagnosis is to confirm that no custom allow matches the flow, and the fix is to write the allow that the design always required.

A service tag simplifies a broad allow, replacing a brittle list of prefixes with a maintained name, and the lesson is to scope the tag as narrowly as the dependency allows, preferring the regional variant to the global one. An ASG groups an application tier so that membership rather than address defines the rule, and the lesson is to confirm that every interface that should belong to the group actually does. Flow logs reveal the actual decision, turning a connectivity mystery into a record of which rule allowed or denied, and the lesson is to enable them before the incident rather than during it.

These are not six unrelated problems. They are six faces of one engine that evaluates ordered rules across two attachments with a default deny at the bottom, and the same procedure diagnoses all of them. That is the payoff of reasoning from the mechanism: the catalog of failures collapses into a single model, and the model is short enough to hold in your head while you work.

### Why Does Allowing a Service Tag Sometimes Open More Than Expected?

Because a tag such as AzureCloud or a global service tag spans a very large set of prefixes, far broader than the single regional service you had in mind. Allowing the broad tag permits flows to everything the tag covers. Prefer the narrowest tag available, usually the regional variant of the specific service, so the rule grants only what the dependency needs.

The fix is always to tighten the tag rather than to abandon tags for raw addresses, because addresses bring back the maintenance burden tags were meant to remove. When a security review flags a rule as too permissive, the usual remedy is to replace a global tag with a regional one, or a broad platform tag with the specific service tag, which narrows the grant while keeping the rule readable and self-maintaining.

## Statefulness and Its Edge Cases

The stateful nature of an NSG is a convenience most of the time and a source of confusion at the edges. Because the engine tracks established connections, an allowed inbound flow has its return traffic permitted automatically and an allowed outbound flow has its responses permitted automatically, which is why so many rule sets work despite listing only one direction. Most engineers never need to think past this, but a few edge cases reward a deeper look.

The first edge case is the long-lived idle connection. Connection tracking holds state for a flow, and a flow that goes silent for a long period can eventually be aged out of the tracking table, after which the next packet on that flow is treated as a new connection and re-evaluated against the rules. For most application traffic this is invisible, but for a protocol that opens a connection and then sits idle for many minutes between exchanges, the re-evaluation can surface a rule gap that the initial handshake hid. The remedy is usually a keepalive at the application or transport layer that keeps the flow active, rather than an NSG change.

The second edge case is asymmetric routing. Stateful tracking assumes that the return path for a flow traverses the same NSG that saw the outbound direction. When routing sends the response through a different path, perhaps because a user-defined route steers return traffic to a different appliance, the NSG that would expect to see the established return may never see it, and the connection can fail in ways that look like a filtering problem but are in fact a routing one. This is one more reason to keep the routing and filtering questions separate during diagnosis, and to read the effective routes whenever a stateful flow behaves inconsistently.

The third edge case is the interaction between the NSG and the guest operating system firewall. The NSG is one filter; the operating system inside the virtual machine runs another. A flow that the NSG allows can still be dropped by the Windows or Linux firewall on the machine, and IP flow verify, which evaluates only the NSG, will report allow while the connection still fails. When IP flow verify says allow and the flow still dies, the guest firewall is a prime suspect, alongside routing and the application. The NSG model is complete for the NSG layer, but the NSG is not the only filter a packet meets.

### Do I Need an Outbound Rule for the Response to an Allowed Inbound Flow?

No. An NSG is stateful, so the return traffic for an allowed inbound flow is permitted automatically without a matching outbound rule, and the responses to an allowed outbound flow are permitted without a matching inbound rule. Writing redundant return rules is unnecessary and clutters the rule set. Reserve outbound rules for flows your resources initiate.

This is one of the most freeing facts about NSGs once it is internalized, because it halves the number of rules you might otherwise write and removes a whole category of imagined problems. When you find yourself about to add an outbound allow purely to let a response back out, stop: the platform already handles it. Outbound rules exist for connections your workload initiates, not for the replies to connections it accepts.

## Making NSGs Reproducible as Code

A production NSG should never be a hand-assembled artifact that exists only in the portal, because a portal-built rule set has no diff, no review, and no reliable way to recreate it exactly. Defining NSGs as code, in Bicep or Terraform, turns the rule set into a reviewable, version-controlled statement of intent that recreates identically on every deployment.

A Bicep fragment shows the shape of an NSG defined as code, with rules expressed clearly and priorities spaced for later insertion. The example defines a small application-tier group with an inbound allow from a web ASG and an outbound allow to regional SQL.

```bicep
resource appNsg 'Microsoft.Network/networkSecurityGroups@2023-05-01' = {
  name: 'nsg-app-tier'
  location: location
  properties: {
    securityRules: [
      {
        name: 'AllowWebToApp'
        properties: {
          priority: 300
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceApplicationSecurityGroups: [ { id: webAsgId } ]
          destinationApplicationSecurityGroups: [ { id: appAsgId } ]
          sourcePortRange: '*'
          destinationPortRange: '8080'
        }
      }
      {
        name: 'AllowSqlOutbound'
        properties: {
          priority: 310
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: 'Sql.WestEurope'
          sourcePortRange: '*'
          destinationPortRange: '1433'
        }
      }
    ]
  }
}
```

The value of this representation is that a change to the security posture becomes a pull request. A reviewer sees that a new allow was added at priority 310, that it targets the regional SQL tag rather than a global one, and that it scopes the source to the virtual network, which is exactly the information needed to judge whether the change is safe. A portal click offers none of that, and a portal-built NSG cannot be redeployed from source when an environment is rebuilt. Expressing the rules against ASGs and service tags, as the fragment does, keeps the code correct as the architecture scales, because the named groups absorb the churn that literal addresses would expose. The series treats the broader practice in its infrastructure-as-code material, and an NSG is one of the cleanest resources to bring under code because its entire behavior is captured in a short, declarative list.

### How Do I Audit an NSG Configuration at Scale?

Read the effective security rules per interface to see the real merged, priority-ordered rule set including both attachments and the defaults, and aggregate flow logs through traffic analytics to find broad allows and unexpected denied patterns. Define NSGs as code so every rule is reviewable in version control, and use IP flow verify to confirm specific flows before and after a change.

Auditing at scale is where the disciplines compound. Code review catches over-broad rules before they ship, effective security rules expose shadowing across attachments, traffic analytics surfaces the rules that fire and the flows that are denied, and IP flow verify proves individual flows on demand. No single tool gives the whole picture, but together they turn a sprawling estate of NSGs from an opaque liability into a set of configurations you can read, review, and verify with confidence.

## Security Groups and Load Balancers: The Health Probe You Must Permit

A pattern that surprises engineers more than it should involves the Azure load balancer and its health probe. The probe originates from a platform address represented by the AzureLoadBalancer service tag, and the default inbound baseline already permits it through AllowAzureLoadBalancerInBound. The trouble starts when a security baseline adds a tight, low-numbered inbound deny that matches the probe before the permissive default is ever reached, silently starving the probe and marking every backend instance unhealthy.

The symptom is distinctive: the application itself works when reached directly on a backend instance, yet the load balancer reports every member down and serves nothing. The cause is that the probe, arriving from the platform tag, matched a custom deny placed above the default allow, so the health check never completed. The diagnosis follows the same priority-ordered reading we have used throughout: sort the inbound definitions by number, read to the first one that matches a connection from AzureLoadBalancer on the probe port, and you will find the deny that shadowed the default. The remedy is an explicit allow from the AzureLoadBalancer tag on the probe port, numbered below the offending deny, which restores the health check without loosening anything else.

This is also where the difference between an internal and a public load balancer matters. A public balancer brings client connections from the internet, which your inbound definitions must permit on the service port, while the probe still arrives from the platform tag. An internal balancer brings client connections from inside the virtual network, caught by the intra-network default allow, but the probe still needs its own clearance if a custom deny would otherwise catch it. In both cases the probe is a separate concern from the client connection, and treating them as one is the mistake that produces a healthy application behind an unhealthy pool.

### Why Does My Load Balancer Mark Every Backend Unhealthy?

Most often because a custom inbound deny, placed at a low priority number, matches the health probe from the AzureLoadBalancer tag before the default allow is reached, so the probe never completes and every member is marked down. Add an explicit allow from the AzureLoadBalancer service tag on the probe port, numbered below the deny, and the pool recovers.

The broader lesson is that platform-originated connections, the probe being the clearest example, follow the same priority-ordered evaluation as everything else and are just as easy to shadow with a well-meaning but over-broad deny. Whenever you tighten an inbound baseline with a low-numbered deny, ask which platform connections that deny might also catch, and clear each one explicitly. The probe is the connection people forget, and forgetting it turns a working application into an empty pool.

## Operating a Security Group Estate Over Time

A single group is simple; an estate of dozens, spread across tiers, environments, and subscriptions, is where discipline pays off or its absence compounds. The behaviors that keep an estate legible are mostly conventions, applied consistently, rather than platform features.

Adopt a naming convention that encodes scope and intent, so a reader can tell from the name alone what a group governs. A name that pairs the environment, the tier, and the purpose communicates far more than a generic label, and it makes the inventory searchable when an audit asks which groups touch a given tier. The same discipline applies to the individual definitions inside a group: a descriptive name and a populated description field turn each entry into self-documenting intent, which is exactly what a reviewer needs months later when the original author has moved on.

Guard against configuration drift, the slow divergence between what the code declares and what the portal actually holds, because drift is where surprises hide. When definitions are added by hand in the portal during an incident and never reconciled back into the code, the next deployment from source either erases them or conflicts with them, and either outcome is a fresh incident. The remedy is to treat the code as the single source of truth, to make emergency portal changes the exception that is always reconciled afterward, and to detect drift on a schedule so it is caught while small.

Establish an ownership and review cadence, because a security boundary nobody reviews decays into a collection of accreted exceptions whose original reasons are forgotten. A periodic review that reads the effective definitions per interface, checks the aggregated traffic record for entries that fire on nothing and broad allows that should be narrowed, and confirms that each exception still has a living justification keeps the estate honest. Entries that match no connection over a long window are candidates for removal, and broad allows that a tighter tag could replace are candidates for refinement. The review is cheap; the breach that an unreviewed broad allow eventually enables is not.

### How Do I Keep a Large Security Group Estate Manageable?

Encode scope and intent in names, document every entry in its description, treat the code as the single source of truth and reconcile any emergency portal change, detect drift on a schedule, and run a periodic review that reads effective definitions and the aggregated traffic record to retire dead entries and tighten broad allows. Consistent conventions, not platform features, keep an estate legible.

The compounding benefit is that a well-operated estate is one you can reason about as a whole, not just one group at a time. When names tell the story, code holds the truth, and reviews retire the cruft, an auditor can read the posture, an engineer can predict a connection's fate, and a change can be reviewed for its effect on precedence and scope before it ships. That is the difference between an estate that gets safer as it grows and one that becomes an unaccountable liability.


## What an NSG Cannot Do

A complete model includes the boundary of the tool, because half of using an NSG well is knowing when it is the wrong instrument. The NSG operates at layers three and four, on addresses, protocols, and ports, and that ceiling defines its limits precisely.

An NSG cannot filter by fully qualified domain name. It matches on IP prefixes, service tags, and ASGs, none of which is a hostname, so a policy that needs to allow traffic to a specific domain while denying others belongs to a firewall, not an NSG. The common workaround of allowing a service tag covers a managed Azure service, but for arbitrary external domains the NSG simply lacks the vocabulary. When a requirement reads in terms of domains, that is the signal to reach for Azure Firewall and its FQDN filtering.

An NSG cannot inspect the application payload. It does not see HTTP paths, headers, request bodies, or TLS contents, so it cannot enforce a rule such as block this URL path or strip this header. Layer-seven concerns belong to an application gateway with its web application firewall or to a dedicated appliance. The NSG decides whether a packet on a port may flow; it never decides anything about what the packet carries.

An NSG cannot apply a single egress policy across an entire hub and its spokes from one place. Each NSG is scoped to the subnet or interface it attaches to, so centralized, inspected egress for a whole topology is the firewall's job. NSGs provide the micro-segmentation between workloads, the firewall provides the inspected perimeter, and conflating the two leads to either a sprawl of duplicated NSG rules or a firewall asked to do segmentation it is poorly suited for. The comparison across these controls is exactly why the series weighs Azure Firewall, network virtual appliances, and NSGs against one another, because choosing the wrong control for a requirement is a costly and common mistake.

A subtle limit concerns private endpoints. Network policies for private endpoints, including NSG enforcement on the private endpoint's subnet, behave specially and have historically required an explicit setting to enable, so an NSG that you assume is filtering private endpoint traffic may not be enforcing as expected unless the subnet's private endpoint network policies are configured to allow it. When a private endpoint flow does not respond to an NSG rule the way the model predicts, the private endpoint network policy setting on the subnet is the first thing to verify, because it is a documented exception to the otherwise uniform evaluation.

### When Should I Use a Firewall Instead of an NSG?

Use a firewall when the requirement needs domain-name filtering, application-layer inspection, threat intelligence, or a single centralized egress policy across many networks, because an NSG operates only on addresses, protocols, and ports at layers three and four. Use an NSG for fast, free micro-segmentation between subnets and workloads. The two run together: NSGs segment, the firewall inspects and centralizes egress.

The decision is rarely either-or in a serious environment. NSGs do the high-volume, zero-cost segmentation work close to every workload, and the firewall handles the smaller set of flows that need inspection or domain awareness, usually the egress to the internet. Asking each control to do only what it is good at keeps both rule sets small and the overall posture comprehensible, which is worth far more than forcing one tool to cover the other's job.

## The Verdict: Read the Rules, Do Not Guess Them

The whole of NSG behavior reduces to one habit. An NSG is an ordered decision engine, not a checklist, and it reaches a verdict by walking the rules in priority order to the first match, separately for the subnet and the interface, with a default deny waiting beneath every custom rule. Predicting any flow is therefore a procedure rather than an intuition: define the flow, find both attachments, walk each rule list in ascending priority to its first match, and apply the conjunction that both must allow. The first-match-by-priority rule is the entire mechanism, and every confusing outcome, the visible allow that does nothing, the deny that shadows an allow, the two machines that diverge, dissolves the moment you apply the procedure.

Around that core, the rest is reinforcement. Service tags let you name the platform dependencies you cannot track by hand, and the regional variants keep the grants tight. Application security groups let you express policy by role so it scales with the architecture instead of breaking on every change. Flow logs and traffic analytics show you what the engine actually decided, and IP flow verify and the effective security rules view let the platform run the evaluation map for you before traffic ever flows. Defined as code and audited with these tools, an NSG estate becomes something you reason about rather than something you fear.

The strategic point is the one this series returns to across every networking subject: you debug from the mechanism, not from the symptom. An engineer who holds the first-match-by-priority rule and the both-must-allow conjunction can look at a rule set and a pair of associations and state the verdict before opening a single diagnostic, and can confirm it in seconds when needed. That is the difference between owning the network and being surprised by it. Build the model, keep flow logs running, express intent in tags and ASGs and code, and the timeout that opened this article becomes a prediction you make rather than a mystery you chase.

## Frequently Asked Questions

### What is a Network Security Group and how does it work?

A Network Security Group is a stateful, layer three and four packet filter that Azure attaches to a subnet, a network interface, or both, and that evaluates each flow against an ordered set of security rules. The engine walks the rules for the relevant direction in ascending priority order and applies the first one that matches the flow's source, destination, protocol, and port. Because it is stateful, return traffic for an allowed connection is permitted automatically. A silent default deny sits beneath every rule set, so any flow not explicitly allowed is dropped.

### How do NSG rules and priority evaluate traffic?

Each rule has a priority between 100 and 4096, and lower numbers are evaluated first. The engine processes the rules for the matching direction from the smallest number upward and stops at the first rule whose conditions all match the packet, applying that rule's allow or deny and ignoring everything below it. A lower number therefore wins, which inverts the intuition that higher should mean more important. When both a subnet NSG and an interface NSG apply, each is evaluated independently and both must allow for the flow to pass.

### What are the default NSG rules?

Every NSG carries six default rules that cannot be deleted and that occupy the highest priority numbers, so they are evaluated last. Inbound, they allow traffic within the virtual network, allow the Azure load balancer, and deny everything else. Outbound, they allow traffic within the virtual network, allow traffic to the internet, and deny everything else. The effect is that inbound is denied by default while outbound is open by default. You override a default by writing a custom rule with a lower priority number that matches the same traffic.

### Should an NSG attach to a subnet or a network interface?

Prefer the subnet for policy that covers a whole tier, because it is fewer objects to manage and it covers new interfaces automatically as machines are added. Use an interface NSG for genuine per-machine exceptions. Both can attach at once, and when they do, both are evaluated and the flow must be allowed by both, so two layers double the places a flow can be silently dropped. Wherever the architecture allows, keep one authoritative layer per flow so there is a single rule set to read when you diagnose.

### How do service tags and application security groups help?

Service tags name groups of IP prefixes that Microsoft maintains for Azure services and the internet, so a rule can target Storage or Sql by intent and stay correct as the underlying addresses change. Application security groups name groups of your own network interfaces by role, so a rule can allow a web role to reach an app role without listing addresses, and new machines inherit the policy by joining the group. Tags express the platform side of a rule and ASGs express your side, and many rules use both together for clarity that scales.

### How do NSG flow logs give traffic visibility?

Flow logs record every flow an NSG evaluated, capturing the five-tuple, the direction, the allow-or-deny action, and the rule that decided, and they write to a storage account. Traffic analytics aggregates them into top talkers, denied-flow patterns, and frequently firing rules. Together they show what the filter actually did rather than what the rules appear to say, which turns a connectivity mystery into a record you read line by line. Enable them before an incident, because logs capture only the flows that occurred while logging was active.

### Why does a flow fail when an allow rule exists?

Because the allow is not the rule the engine reaches first, or because the other attachment denies the same flow. A lower-priority deny placed above the allow shadows it, so the engine applies the deny and never reaches the allow. Alternatively, the subnet NSG allows the flow while the interface NSG falls through to its default deny, and the conjunction that both must allow makes the deny final. Run the evaluation map across both attachments and read the flow log to find the deciding rule.

### Does a lower priority number win in an NSG?

Yes. Azure evaluates security rules in ascending numerical order and stops at the first match, so the rule with the smallest priority number that matches a packet is the one that decides. Priority encodes position in a queue, not weight or importance, which is why a deny at priority 110 overrides an allow at priority 4000 for any packet both would match. When a new rule seems to have no effect, sort by priority and read downward to the first matching rule, which is almost always a lower-numbered entry shadowing the one you added.

### Do I need an outbound rule for the response to an allowed inbound flow?

No. An NSG is stateful, so it tracks established connections and automatically permits the return traffic for an allowed inbound flow without a matching outbound rule, and likewise permits responses to an allowed outbound flow without a matching inbound rule. Writing redundant return rules only clutters the set and invites confusion. Outbound rules exist to govern connections your resources initiate, not to permit the replies to connections they accept, so reserve them for genuine egress you want to control.

### Can an NSG filter traffic by domain name?

No. An NSG operates at layers three and four and matches on IP prefixes, service tags, and application security groups, none of which is a hostname, so it cannot allow or deny by fully qualified domain name. A service tag can cover a managed Azure service, but arbitrary external domains are outside its vocabulary. When a requirement is expressed in terms of domains or needs application-layer inspection, the right tool is Azure Firewall with FQDN filtering or an application gateway, with the NSG handling address-and-port segmentation alongside.

### What happens if no custom rule matches a packet?

The packet falls through to the default rules at the end of the list. Inbound, that usually means the default deny drops it, unless it was intra-virtual-network or load balancer traffic caught by a default allow. Outbound, a default allow to the internet or within the virtual network usually permits it before the default deny is reached. This is why most inbound timeouts trace to a missing allow rather than a wrong one: the default deny is doing its job on a flow nobody explicitly permitted.

### How do I override a default NSG rule?

You cannot delete a default rule, but you can override its effect by adding a custom rule with a lower priority number that matches the same traffic. Because the engine reaches the lower-numbered custom rule first, it decides before the default is ever consulted. This is how a security baseline closes the open egress the defaults grant: add a low-numbered outbound deny, then layer specific allows above it for the destinations the workload needs, recreating a default-deny egress posture while the original default remains untouched beneath.

### Why do two identical machines in one subnet behave differently?

Almost always because one carries an interface NSG that the other lacks, or because an ASG membership was applied to one and forgotten on the other. The shared subnet NSG treats both alike, so a difference points to per-interface configuration. An interface NSG adds a second rule list the flow must also satisfy, and since both attachments must allow, the extra list can deny a flow the subnet permits. Check each machine's interface for an attached NSG and its ASG memberships first.

### What is the fastest way to confirm an NSG is blocking a flow?

Run IP flow verify in Network Watcher for the exact flow, giving the direction, protocol, local and remote addresses, and port. It evaluates the live NSG configuration and reports allow or deny with the deciding rule in seconds, without waiting for traffic or flow logs. A deny against the default deny means a missing allow; a deny against a named rule means a scoping or shadowing problem; an allow exonerates the NSG and points you toward routing, the guest firewall, or the application.

### How should I structure NSG rules for a multi-tier application?

Put tier policy on subnets, one NSG per tier, and express tier-to-tier flows with application security groups as source and destination. Allow only the ports each tier needs from the tier that needs them, scope managed-service egress with regional service tags, and rely on the default deny for the rest. Number rules with gaps so later insertions do not force a renumber, enable flow logs across the tiers, and define the whole configuration as code so every change is reviewable.

### Does an NSG control how traffic is routed?

No. An NSG only filters; it never changes where a packet goes. Routing is decided by the effective route table and any user-defined routes, which select the next hop, while the NSG independently allows or denies the flow on the subnets and interfaces it touches. A misrouted packet and a filtered packet are different failures, diagnosed with different tools: the effective routes for the path, the flow log and IP flow verify for the filter. Keeping the two questions separate is the key to fast diagnosis.

### Why does allowing a service tag sometimes open more than expected?

Because a broad tag such as AzureCloud or a global service tag spans an enormous set of prefixes, far wider than the single regional service you likely intended. Allowing the broad tag permits flows to everything it covers. The remedy is to use the narrowest tag available, usually the regional variant of the specific service, so the rule grants only what the dependency requires. Replacing a global tag with a regional one is the standard fix when a security review flags a rule as too permissive.

### Do NSGs apply to private endpoint traffic?

Historically, NSG enforcement on a private endpoint's subnet required the subnet's private endpoint network policies to be enabled, so an NSG you assumed was filtering private endpoint traffic might not have been enforcing as expected. When a private endpoint flow does not respond to an NSG rule the way the evaluation map predicts, verify the private endpoint network policy setting on the subnet first, since it is a documented exception to the otherwise uniform evaluation. Confirm the current behavior against the official documentation, because platform defaults in this area have evolved.

### What is the difference between the source port and the destination port in a rule?

The destination port is the service port the flow is reaching, such as 443 for HTTPS or 1433 for SQL, and it is what you almost always intend to control. The source port is the ephemeral port the client chose, which is effectively random and should be left as the asterisk. Pinning the source port to a service number produces a rule that matches almost no real traffic, a quiet bug to check whenever a rule that looks correct never seems to fire.

### How do I make an NSG configuration reproducible and auditable?

Define NSGs as code in Bicep or Terraform, expressing rules against application security groups and service tags so they survive scaling and re-addressing, and review every change as a pull request where the diff in precedence and scope is visible. Read the effective security rules per interface to see the merged, priority-ordered set, aggregate flow logs through traffic analytics to surface broad allows and denied patterns, and use IP flow verify to confirm specific flows before and after a change.
