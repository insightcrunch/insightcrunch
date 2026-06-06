---
layout: post
title: "Fix NSG Blocking Traffic Unexpectedly"
page_title: "Fix NSG Blocking Traffic in Azure: Diagnose the Exact Rule with Effective Security Rules, Priority, and Subnet-Plus-NIC Stacking"
date: 2022-11-21
categories: ["Technology"]
tags: ["Azure", "NSG", "Networking", "Troubleshooting", "Cloud Computing"]
excerpt: "NSG blocking traffic in Azure almost always traces to one rule. Read the effective security rules, find the exact blocker by priority, then fix only that rule."
image: "/assets/images/blog/blog-46.webp"
reading_time: 60
author: "alex-cunningham"
last_updated: 2022-11-21
lang: en
---
An NSG blocking traffic is one of the most common and most misdiagnosed connectivity failures in Azure, and the reason it feels mysterious is almost never that the platform is behaving strangely. A network security group is a deterministic packet filter. Given a flow, it evaluates an ordered set of rules and returns exactly one verdict, allow or deny, and it tells you which rule produced that verdict if you ask it the right way. When a connection that should work does not, the platform already knows why; the engineer simply has not yet read the decision. The afternoon you lose to a blocked port is the afternoon you spent guessing at rules instead of asking Azure which rule actually matched.

![Diagnosing an NSG blocking traffic in Azure by reading the effective security rules - Insight Crunch](/assets/images/blog/blog-46.webp)

This article treats the block as a lookup, not a mystery. You will learn to read the effective security rules so you can see the single rule that decided your flow, understand why a lower priority number wins and why an NSG on both the subnet and the network interface stacks into a logical AND, recognize the six recurring patterns that produce a surprising block, and apply the narrow one-rule fix for each instead of pasting a broad allow-any rule that quietly over-exposes the workload. The promise is concrete: after this, finding the blocker is a two-command diagnosis, and the fix is one targeted rule, confirmed by the same tool that exposed the problem.

## What "NSG blocking traffic" actually means

A network security group is a stateful firewall that attaches to a subnet, to a network interface, or to both, and filters traffic against a prioritized list of security rules. Each rule names a direction (inbound or outbound), a priority number, a source, a destination, a port range, a protocol, and an action. When a packet arrives at an interface or crosses a subnet boundary, Azure walks the applicable rules in ascending priority order and applies the first rule whose five-tuple match (source, source port, destination, destination port, protocol) covers the flow. That first match is final. No later rule is consulted, and because the group ships with a default deny at the bottom, any flow that matches no explicit allow falls through to that deny and is dropped.

"NSG blocking traffic" is therefore shorthand for a specific event: a flow matched a deny rule, or it matched no allow rule and hit the default deny. The symptom you see is connection-level, not rule-level. A TCP handshake never completes, so the client reports a connection timeout rather than a connection refused, because a dropped SYN produces silence rather than a reset. SSH hangs and eventually times out. RDP shows a generic "can't connect" without a clean rejection. An application gateway or load balancer marks the backend unhealthy because its health probe cannot reach the pool member. A database client stalls on connect. The shared thread is silence on the wire, and silence is the fingerprint of a packet filter dropping the SYN, distinct from a service that is up and actively refusing the connection.

### What does the NSG default deny do when no rule matches?

Every NSG carries default rules you cannot delete. Inbound, it allows traffic from within the virtual network and from the Azure load balancer, then denies everything else. Outbound, it allows traffic to the internet and within the virtual network, then denies the rest. A flow that matches none of your custom allows falls to the default deny and is dropped silently.

The default rules deserve precise attention because they are the floor every other rule sits on. On the inbound side, three default rules exist at the very bottom of the priority order: an allow for traffic whose source is the VirtualNetwork service tag (so peered and same-VNet hosts can reach each other), an allow for the AzureLoadBalancer service tag (so health probes from the platform's load balancer reach your instances), and a deny-all that catches everything else. On the outbound side, there is an allow for VirtualNetwork-destined traffic, an allow for Internet-destined traffic, and a deny-all. These default rules occupy the highest priority numbers, which means the lowest precedence, so any custom rule you write with a normal priority number is evaluated before them. The consequence engineers forget is that inbound from the public internet is denied by default and outbound to the internet is allowed by default, an asymmetry that explains why a fresh VM can reach out to install packages but cannot be reached on a web port until you add an allow.

Understanding the rule model at this depth is the foundation, and the [Network Security Groups (NSG) deep dive](/2023/09/25/azure-nsg-deep-dive/) walks the full evaluation engine, the service-tag catalog, and the stateful return-traffic behavior that this troubleshooting article builds on. Where NSGs attach in the broader topology, and why a subnet association behaves differently from an interface association, is covered in the [Azure Virtual Network (VNet) deep dive](/2022/02/28/azure-virtual-network-vnet-deep-dive/). This piece assumes the model and goes straight to the diagnosis.

### Why does a blocked flow time out instead of getting refused?

A network security group that denies a flow drops the packet rather than sending a reset. The sender never receives a SYN-ACK and never receives a refusal, so the TCP stack retransmits the SYN until its timeout expires, then reports a timeout. A connection refused, by contrast, means the packet reached a host whose port had no listener.

That distinction is your first triage lever, because it separates a filtering problem from a service problem before you open a single rule. If a client gets connection refused, the SYN reached the destination host and the operating system answered with a reset, which means the security group allowed the flow and the application is the issue, whether the listener is down, bound to localhost only, or listening on a different port. If the client gets a timeout, the SYN died somewhere on the path, and a security group dropping it is the leading suspect, alongside a missing route or a host firewall. Reading the failure mode this way keeps you from auditing rules when the listener was never running, and from restarting a healthy service when the packet never arrived.

## How to read the block: the diagnostic signal before you touch a rule

The single most valuable habit when an NSG blocks traffic is to read the effective security rules before changing anything. The effective security rules are the merged, evaluated rule set that Azure actually applies to a given network interface, combining the rules from the subnet NSG and the interface NSG into the ordered list the platform really uses. Because a single interface can be governed by two groups at once, the rule you wrote and the rule that matched are not always the same object, and the effective view is the only place the truth is assembled.

### How do I see the effective security rules?

Query the effective rules directly against the network interface. With the CLI, run `az network nic list-effective-nsg`, passing the interface name and resource group. The output lists every rule from both the subnet and the NIC group in evaluation order, including the default rules, so you can scan for the first rule that matches your flow's five-tuple and read its action.

Here is the command, with the resource group and interface name substituted for your own:

```bash
az network nic list-effective-nsg \
  --name myVmNic \
  --resource-group myResourceGroup \
  --output json
```

The interface must belong to a running virtual machine for this call to return data, because the effective set is computed against a live interface. The response groups rules by their association (the subnet group and the interface group appear as separate networkSecurityGroup entries) and lists each rule with its priority, direction, protocol, source and destination address prefixes or service tags, port ranges, and access value. Scan it in priority order, find the first inbound rule whose source, destination, and port cover the flow you care about, and read whether its access is Allow or Deny. That single rule is your verdict. Everything below it in the ordering was never consulted for this flow.

The portal exposes the same data under the network interface's "Effective security rules" view and under Network Watcher's security group view, which renders the merged set visually and is often faster to scan when you are not sure which interface to start from. Either path gives you the authoritative answer, and both beat reading the individual rules on each group separately, because reading them separately forces you to merge and re-sort the two lists in your head, which is exactly the error-prone step the effective view removes.

### Which Network Watcher tool confirms a block fastest?

IP flow verify is the fastest confirmation. It asks Azure to evaluate a specific five-tuple, a direction, a local IP and port, a remote IP and port, and a protocol, against the effective rules for an interface, and it returns Allow or Deny along with the name of the matching rule. You get the verdict and the responsible rule in one call without sending a packet.

IP flow verify is the tool to reach for when you want a definitive yes or no for one precise flow, because it does not depend on the application being up, on a route existing, or on a packet actually traversing the path. It is a pure evaluation of the security group's decision for the tuple you describe. With the CLI it surfaces through Network Watcher:

```bash
az network watcher test-ip-flow \
  --vm myVm \
  --resource-group myResourceGroup \
  --direction Inbound \
  --protocol TCP \
  --local 10.1.0.4:443 \
  --remote 203.0.113.10:51234 \
  --output json
```

The response contains an access field of Allow or Deny and a ruleName field naming the exact rule that produced the decision. When ruleName is one of the default deny rules, you have a missing-allow problem; when it is a custom rule with a deny action, you have a deny that is shadowing your intended allow; when it is your allow but the connection still fails, the security group is not the cause and you move on to routing or the host. This is the closest thing Azure gives you to a definitive answer, and it is why the discipline of this article is to confirm with IP flow verify before editing a rule. Guessing and editing creates two changes to reason about; confirming and editing creates one.

Two more signals round out the toolkit. NSG flow logs record, per flow, the source and destination, the port, the protocol, and whether the security group allowed or denied it, written to a storage account and queryable after the fact, which is how you diagnose an intermittent or historical block that you cannot reproduce on demand. Connection troubleshoot (the connectivity check in Network Watcher) actually attempts a connection from a source to a destination and reports where it failed along the path, including a security-rule hop when a group is the cause, which is useful when you are not certain whether the block is the security group, a route, or the host. Between the effective rules view, IP flow verify, flow logs, and connection troubleshoot, every NSG block is observable, and none of the four requires you to change a rule to learn the cause.

For the cases where you need to watch actual packets rather than evaluate rules, two more Network Watcher capabilities go deeper. Packet capture records the real frames on an interface to a file you can open in a protocol analyzer, which is how you prove whether a SYN even arrives at the destination interface; if the capture on the destination shows no inbound SYN while the source insists it sent one, something on the path dropped it, and the security group's IP flow verify result tells you whether the group was that something. Connection Monitor runs continuous reachability checks between endpoints and graphs success, latency, and the hop where failures occur over time, which turns an intermittent block into a monitored signal rather than a story you piece together after the fact. These are heavier instruments than IP flow verify and you reach for them when the lightweight evaluation says the group allows the flow yet packets still go missing, because at that point you need to observe the wire, not re-read the rules.

### The same diagnosis in PowerShell

The Az PowerShell module exposes the identical signals for teams whose tooling is built on PowerShell rather than the CLI. To pull the effective rules for an interface, fetch the network interface object and call the effective-security-group cmdlet against it:

```powershell
$nic = Get-AzNetworkInterface -Name "myVmNic" -ResourceGroupName "myResourceGroup"
Get-AzEffectiveNetworkSecurityGroup -NetworkInterfaceName $nic.Name -ResourceGroupName "myResourceGroup"
```

The output object carries the same merged, evaluated set, with each rule's priority, direction, access, and matched address prefixes, so you read it in the same priority order and look for the first match. To run the equivalent of IP flow verify, you target the Network Watcher in the region of the resource and pass the flow you want evaluated:

```powershell
$nw = Get-AzNetworkWatcher -Location "eastus"
Test-AzNetworkWatcherIPFlow -NetworkWatcher $nw `
  -TargetVirtualMachineId "/subscriptions/.../virtualMachines/myVm" `
  -Direction Inbound -Protocol TCP `
  -LocalIPAddress "10.1.0.4" -LocalPort "443" `
  -RemoteIPAddress "203.0.113.10" -RemotePort "51234"
```

The result returns an Access of Allow or Deny and a RuleName naming the deciding rule, exactly as the CLI does. The point of showing both surfaces is that the diagnosis does not depend on the tool; the security group's decision is the same object whether you read it through the CLI, PowerShell, or the portal, and the discipline of reading that decision before editing a rule is the constant.

### Why a blocked inbound flow does not need a matching outbound allow

A network security group is stateful, which changes how you read the rules and prevents a whole category of phantom blocks. When an inbound flow is allowed, the return traffic for that established connection is allowed back out automatically, regardless of the outbound rules, and when an outbound flow is allowed, the return traffic is allowed back in automatically regardless of the inbound rules. You do not write a matching reverse rule for the responses of an established connection, because the platform tracks the connection state and permits the replies.

This statefulness matters during diagnosis because it tells you where not to look. If a client can open a TCP connection inbound to a web server and the server's responses flow back without an explicit outbound allow for the ephemeral return ports, that is the stateful behavior working as intended, not a misconfiguration to fix. The corollary is that an outbound block almost always concerns a connection the host itself initiates, not the responses to inbound connections, so when you are chasing an outbound failure you are looking at a flow the workload starts, such as a call to an external API or a package repository, rather than the return path of an inbound session. Misunderstanding statefulness leads engineers to add reverse rules that do nothing and to suspect the outbound rules when an inbound session's replies are involved, when in fact the established connection's return traffic was never subject to a separate rule lookup. Read the direction the connection is initiated in, evaluate the rules for that direction, and trust that the replies for an established flow are handled by the connection state.

### How do I read the effective-rules output without misjudging a match?

Three fields decide every match and each is misread in a predictable way. The address-prefix fields can be an IP range, a single address, or a service tag, and a flow matches only if its real address falls inside that prefix or tag, so a rule whose source is a service tag matches a far wider or narrower set of addresses than an IP range that merely looks similar. Confirm what a tag actually covers before assuming a flow matches it.

The port-range field is the second trap. A rule with a destination port range of a single value matches only that port, while an asterisk matches every port, and a range matches the span inclusive of its ends, so a flow to port 8443 does not match a rule scoped to 443 even though the numbers are close and the intent feels related. Read the exact range, not the apparent purpose, because the platform matches the number, not your intent. The third field is the protocol: a rule scoped to TCP does not match a UDP flow and a rule scoped to a single protocol will pass a flow on a different protocol straight through to the next rule, which is why a flow you expected a TCP rule to catch sometimes sails past it to a later deny. When you walk the effective set, evaluate each candidate rule against all three dimensions at once, the address prefix, the port range, and the protocol, and stop at the first rule that covers the flow on all three; that rule, and only that rule, is your verdict. The most common misread is to find a rule whose name or address looks right and declare it the match without checking that the port and protocol also cover the flow, which sends you fixing a rule that was never the one the platform applied. Match on the full five-tuple or do not call it a match.

## The InsightCrunch NSG diagnosis flow

The diagnosis is the same every time, and naming the sequence turns a vague hunt into a four-step procedure. The InsightCrunch NSG diagnosis flow is: read the effective security rules for the affected interface, find the matching rule by walking priority order until the first five-tuple match, check whether the deciding group is on the subnet or the interface (and whether the other group also has a relevant rule), then adjust the one specific rule rather than opening a broad allow. The flow works because it follows the platform's own evaluation order, so you are reading the decision the same way Azure made it.

The findable reference below maps each recurring symptom to the rule pattern that produces it, the effective-rule signature that confirms it, and the narrow fix. Use it as the triage table you return to whenever a flow is blocked.

| Symptom | Likely cause | Effective-rule signature | One-rule fix |
| --- | --- | --- | --- |
| Subnet allows the port but traffic still drops | Interface NSG denies or lacks an allow | IP flow verify names a NIC-group deny or default deny | Add or correct the allow on the interface group so both groups allow |
| A new allow has no effect | A lower-numbered custom deny shadows it | Matching rule has a smaller priority number and Deny action | Lower the allow's priority number below the deny, or scope the deny tighter |
| Inbound from the internet always times out | No explicit allow exists, default deny matches | ruleName is DenyAllInBound (the default) | Add a scoped inbound allow for the source prefix and port |
| Traffic to or from an Azure service is dropped | Wrong or missing service tag | Matching rule's prefix is an IP literal or the wrong tag | Replace the IP literal with the correct service tag |
| Outbound calls fail while inbound works | A custom outbound deny matches | Outbound IP flow verify names a custom Deny | Scope or remove the outbound deny, add the needed outbound allow |
| A rule targeting an ASG never matches | The interface is not in the ASG | Rule lists the ASG but the NIC membership is absent | Associate the interface with the application security group |

Naming this the diagnosis flow matters for a practical reason: it gives the on-call engineer a script to follow at 2 a.m. when judgment is thin. Read, match, locate, adjust. The same four verbs resolve every block in the table, and the table itself is the artifact you bookmark.

## The distinct root causes of an NSG block

Almost every surprising NSG block reduces to one of six patterns. They share a single underlying mechanic, the first-match-wins evaluation against a merged rule set, but they present differently and demand different fixes. Working through them in order builds the instinct to recognize each from its effective-rule signature.

### Why does a subnet rule allow the port but traffic is still blocked?

Because an interface can be governed by two groups at once. When an NSG is associated with both the subnet and the network interface, inbound traffic must be allowed by the subnet group and then by the interface group, and outbound traffic must be allowed by the interface group and then by the subnet group. The two evaluations stack as a logical AND, so one allow is not enough.

This stacking is the single most common reason a correct-looking rule fails to take effect, and it catches experienced engineers because the rule they added is genuinely there and genuinely correct, just on the wrong layer. Picture a subnet group that allows TCP 443 inbound and an interface group that was created from a template allowing only SSH. Traffic to 443 clears the subnet group and then dies at the interface group, which has no allow for 443 and falls through to its own default deny. IP flow verify run against the interface names the interface group's DenyAllInBound, and the moment you see a default deny when you were certain you wrote an allow, suspect the other layer. The fix is to make both groups allow the flow: add the 443 allow to the interface group, or, if the interface group exists only by accident, consider whether you need two groups at all. Many designs are cleaner with a single subnet-level group and no interface group, because the interface group adds a second place for a flow to die and a second place for the next engineer to forget. The platform supports both layers for legitimate segmentation needs, but two groups mean two ANDed gates, and every gate is a place to be blocked.

### How does NSG rule priority decide which rule wins?

Rules are evaluated in ascending priority order, and the first rule that matches the flow's five-tuple wins. Lower priority numbers are evaluated first, so a lower number has higher precedence. Custom rules use numbers from 100 to 4096; the default rules sit at the top of that range with the lowest precedence. The first match is final, and no later rule is consulted.

The trap here is intuitive-but-wrong: a new allow added to fix a block sometimes does nothing because an existing deny carries a smaller priority number and is evaluated first. Suppose a security baseline rule denies inbound TCP 3389 from the internet at priority 200, and you add an allow for 3389 from your office prefix at priority 300. Your allow is correct, but the deny at 200 is evaluated first, matches the flow if its source covers your office prefix, and the verdict is sealed before your allow is ever considered. IP flow verify names the priority-200 deny, and the smaller number is the tell. The fix is one of two moves: give your allow a priority number smaller than the deny so it is evaluated first, taking care that doing so does not punch an unintended hole through a deny that exists for a good reason, or tighten the deny so its source no longer covers your office prefix. The correct move depends on intent. If the deny is meant to block the broad internet and your office is a sanctioned exception, a narrower allow at a smaller number is right. If the deny was meant to be absolute, the allow should not exist at all and the real fix is elsewhere. Priority is not a popularity contest; the smallest matching number governs, full stop.

### Does the default deny block traffic when no explicit allow exists?

Yes. Every NSG ends with a deny-all rule that you cannot remove, sitting at the lowest precedence. Inbound traffic from outside the virtual network that matches no explicit allow falls through every custom rule and the VirtualNetwork and load-balancer defaults, lands on the inbound deny-all, and is dropped. The absence of an allow is itself the block.

This is the cause that feels least like a misconfiguration, because nothing is wrong with any rule you wrote; the rule you needed simply is not there. A freshly created network interface behind a group with only an SSH allow will refuse every web connection from the internet, not because a deny targets web traffic but because no allow admits it and the default deny catches the remainder. IP flow verify returns Deny with ruleName equal to DenyAllInBound, the unambiguous signature of a missing allow rather than an active deny. The fix is to add the specific inbound allow your workload needs, scoped as tightly as the use case permits: a source prefix rather than the internet at large where you can, the exact destination port, and the right protocol. The temptation in the heat of an incident is to allow everything inbound to make the symptom vanish, which works and is the single worst thing you can do, because it converts a closed posture into an open one and the next person to read the group sees a wide-open allow with no explanation. Scope the allow to the flow you actually need, and the default deny continues to protect everything else, which is precisely its job.

### What happens when a service tag is wrong or missing?

A service tag is a named, Microsoft-managed group of IP prefixes, such as VirtualNetwork, AzureLoadBalancer, Internet, Storage, Sql, or a regional variant, and you use it as a source or destination in place of brittle IP literals. When a rule that should match an Azure service uses the wrong tag, an out-of-date IP literal, or no tag at all, the flow does not match the intended allow and falls to a deny.

Service-tag mistakes produce blocks that look like routing problems because the traffic is to or from an Azure platform endpoint whose addresses you do not control and that change over time. The classic case is a load balancer health probe failing because the inbound allow for the probe was scoped to a hard-coded IP range instead of the AzureLoadBalancer service tag; the probe source addresses shift, the literal range goes stale, and the probe is denied, marking the backend unhealthy even though the application is fine. Another is an outbound rule that allows traffic to a storage endpoint by IP, which breaks the day the storage service's address space expands. The effective-rule signature is a matching rule whose prefix is an IP literal or a mismatched tag where a service tag belonged. The fix is to replace the literal with the correct service tag, which Microsoft keeps current automatically, so the rule tracks the service's real address space without you maintaining a range. Service tags exist precisely to remove the brittleness of IP literals from your rules, and reaching for a literal where a tag fits is the misconfiguration that bites later. When you must allow a platform service, find its tag and use it.

A subtlety inside service tags causes its own blocks: many tags come in both a global form and a regional form, such as the storage tag for all regions versus the storage tag scoped to a single region. The regional variant matches only the service's addresses in that region, which is what you want when you intend to permit traffic to storage in your own region and deny it elsewhere, but it produces a block when you scope a rule to one region and the traffic actually targets a resource in another. The reverse mistake is using the global tag where a regional scope was the security intent, which over-permits without an obvious symptom until an audit finds it. When a rule built on a regional service tag denies a flow you expected it to allow, confirm that the resource the flow targets really lives in the region the tag names, because a resource created in a different region than you assumed will sit outside the regional tag's address set and fall to a deny. Reading the effective rules shows you which tag the matching rule carries, and matching that against the actual region of the destination resolves the case quickly. Choosing the global or the regional variant deliberately, rather than grabbing whichever the editor suggested first, prevents both the surprise block and the silent over-permission.

### Why do outbound calls fail when inbound works fine?

Because inbound and outbound rules are independent, and an outbound deny can match a flow that the inbound rules never see. The default outbound posture allows traffic to the virtual network and the internet, so outbound usually works without custom rules, which makes a custom outbound deny easy to overlook when one is present and matches.

Engineers reach for the inbound rules first by reflex, since most blocks are inbound, and an outbound block hides because the outbound side is permissive by default and rarely audited. A security baseline that denies outbound to the internet except through a controlled egress, a rule meant to force traffic through a firewall, will block an application's direct outbound call to an external API, and the application reports a timeout connecting out while every inbound test passes cleanly. Run IP flow verify with the direction set to Outbound to catch this, because an inbound test will always look healthy and tell you nothing about the failing direction. The signature is an outbound IP flow verify naming a custom deny, often a deny-internet-outbound rule that is doing exactly what it was written to do. The fix depends on the design: if outbound to that destination is sanctioned, add a scoped outbound allow at a smaller priority number than the deny; if the egress is meant to flow through a firewall or NAT, the application's destination or next hop is what needs correcting, not the security group. Always test the direction that is actually failing, because the two directions are evaluated separately and a clean inbound result proves nothing about the outbound path.

### Why does a rule targeting an application security group never match?

Because the interface is not a member of the application security group the rule references. An application security group lets you write a rule against a logical group of interfaces, such as "web" or "db," instead of IP addresses, but the rule only applies to an interface once that interface has been associated with the group. A rule that names an ASG the interface does not belong to simply does not match it.

This pattern produces a block that is invisible in the rule text, because the rule looks correct, it names the right ASG and the right port, and yet the interface it should protect is untouched by it. The membership, not the rule, is missing. A common version is a deployment that creates the application security groups and the rules referencing them but never associates the new virtual machine's interface with the appropriate group, so a rule meant to allow web traffic to the "web" ASG members never sees the new web server, and the server falls to the default deny. The effective-rule signature is telling: the rule referencing the ASG does not appear in the effective set for the interface, because it does not apply to an interface outside the group. The fix is to associate the interface with the application security group, after which the rule begins to apply and the effective set includes it. Application security groups move the segmentation logic off IP addresses and onto roles, which is a real improvement for maintainability, but the association step is a prerequisite that is easy to skip in automation, and skipping it produces a rule that protects nothing.

## Fixing each cause without over-exposing the workload

The through-line across all six causes is the same discipline: the fix is one narrow rule, not a broad allow. The effective-rules-rule for NSGs states the principle plainly. The effective security rules show the exact rule that decided a flow, so finding the blocker is a lookup rather than a guess, and the correct remedy is to adjust that one rule rather than to add a wide allow that over-exposes the workload and may still be overridden by a lower-priority deny on the other group. This claim is worth internalizing because it inverts the instinct that incidents train into people. Under pressure, the move that makes the red symptom turn green fastest is an allow-any rule, and it works, and it is almost always wrong.

Consider why the broad allow is doubly bad. First, it over-exposes: an inbound allow-any opens every port from every source, so the moment the symptom clears you have a workload reachable on services you never meant to expose, and the rule carries no record of which flow it was actually meant to permit, so no future engineer can safely narrow it. Second, it may not even work, because if the real blocker is a lower-priority deny on the other group in the stack, your broad allow on this group is evaluated, the flow proceeds to the second ANDed gate, and the deny there still drops it. You have created exposure and not fixed the problem. The narrow fix avoids both failure modes: it permits exactly the flow you confirmed was blocked, it documents intent through its scope, and because you confirmed the deciding rule with IP flow verify first, you fix the gate that was actually closed.

The mechanics of the narrow fix are the same family of commands regardless of cause. To add a scoped inbound allow that admits only the flow you need, name the source prefix, the destination port, and the protocol explicitly:

```bash
az network nsg rule create \
  --resource-group myResourceGroup \
  --nsg-name myInterfaceNsg \
  --name allow-https-from-office \
  --priority 150 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefixes 198.51.100.0/24 \
  --source-port-ranges '*' \
  --destination-address-prefixes '*' \
  --destination-port-ranges 443
```

The priority of 150 places this allow ahead of a baseline deny at 200, which is the right move only when the deny is meant to admit sanctioned exceptions; if the deny is absolute, do not punch through it. To inspect the rules on a single group before you edit, list them and read the priorities and actions:

```bash
az network nsg rule list \
  --resource-group myResourceGroup \
  --nsg-name myInterfaceNsg \
  --include-default \
  --output table
```

The `--include-default` flag matters because it shows the default rules in the listing, so you can see the deny-all you are falling through to rather than wondering why an empty-looking group blocks everything. After any change, re-run IP flow verify for the exact flow, and only call the fix done when the access flips to Allow and the ruleName is your intended allow. Confirming with the same tool that diagnosed the block closes the loop: you saw the deny, you made one change, and you saw the allow, with no ambiguity about which edit mattered. This is the difference between fixing the cause and merely changing things until the symptom stops, and the [hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) is where you can reproduce each block pattern, read its effective rules, and practice the one-rule fix against a live group until the sequence is muscle memory.

## Reproduce every NSG block in a lab

Reading about a block teaches less than producing one and watching IP flow verify name the rule, so the fastest way to internalize the diagnosis is to build a small environment and recreate each pattern on purpose. The following sequence stands up a virtual network, a subnet, a virtual machine, and the security groups you need, then walks through inducing and confirming the recurring causes. Run it in a throwaway resource group you can delete afterward, and read each IP flow verify result as the authoritative verdict it is.

Start by creating the resource group, the network, and a virtual machine with a public interface so you have a real flow to test:

```bash
az group create --name nsg-lab-rg --location eastus

az network vnet create \
  --resource-group nsg-lab-rg \
  --name lab-vnet \
  --address-prefix 10.20.0.0/16 \
  --subnet-name app-subnet \
  --subnet-prefix 10.20.1.0/24

az vm create \
  --resource-group nsg-lab-rg \
  --name lab-vm \
  --image Ubuntu2204 \
  --vnet-name lab-vnet \
  --subnet app-subnet \
  --admin-username azureuser \
  --generate-ssh-keys \
  --public-ip-sku Standard
```

Creating the VM provisions a network interface, and depending on the image and defaults it may also create an interface-level security group with a starter rule. Inspect what you have before you change anything, because the starting state is itself a lesson in how groups attach:

```bash
az network nic list \
  --resource-group nsg-lab-rg \
  --query "[].{nic:name, nsg:networkSecurityGroup.id}" \
  --output table
```

### Reproduce the missing-allow default deny

The simplest block to produce is the absence of an allow. Create a clean subnet group with only an SSH allow, associate it with the subnet, and then test an inbound web flow that no rule admits:

```bash
az network nsg create --resource-group nsg-lab-rg --name subnet-nsg

az network nsg rule create \
  --resource-group nsg-lab-rg --nsg-name subnet-nsg \
  --name allow-ssh --priority 300 \
  --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes '*' --source-port-ranges '*' \
  --destination-address-prefixes '*' --destination-port-ranges 22

az network vnet subnet update \
  --resource-group nsg-lab-rg --vnet-name lab-vnet \
  --name app-subnet --network-security-group subnet-nsg

az network watcher test-ip-flow \
  --vm lab-vm --resource-group nsg-lab-rg \
  --direction Inbound --protocol TCP \
  --local 10.20.1.4:443 --remote 203.0.113.10:50000
```

The result returns Deny with a ruleName of the inbound default deny, because port 443 matches no allow and falls through. You have reproduced the missing-allow case and seen its signature. The narrow fix is to add the 443 allow scoped to the source you actually need, then re-test and watch the verdict flip to Allow naming your new rule.

### Reproduce the lower-priority deny shadowing an allow

Now produce the priority trap. Add a deny for a port at a small number, then add an allow for the same port at a larger number, and observe that the deny wins:

```bash
az network nsg rule create \
  --resource-group nsg-lab-rg --nsg-name subnet-nsg \
  --name deny-rdp-baseline --priority 200 \
  --direction Inbound --access Deny --protocol Tcp \
  --source-address-prefixes Internet --source-port-ranges '*' \
  --destination-address-prefixes '*' --destination-port-ranges 3389

az network nsg rule create \
  --resource-group nsg-lab-rg --nsg-name subnet-nsg \
  --name allow-rdp-office --priority 400 \
  --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes 198.51.100.0/24 --source-port-ranges '*' \
  --destination-address-prefixes '*' --destination-port-ranges 3389

az network watcher test-ip-flow \
  --vm lab-vm --resource-group nsg-lab-rg \
  --direction Inbound --protocol TCP \
  --local 10.20.1.4:3389 --remote 198.51.100.10:50000
```

IP flow verify names the deny at priority 200, even though your allow at 400 is correct in every other respect, because 200 is evaluated first and matches the office source through the broad Internet tag. The fix that respects intent is to give the office allow a number below 200, so the sanctioned exception is evaluated before the broad deny. Re-create the allow at priority 150, re-test, and the verdict flips to Allow naming the office rule, with the broad internet still denied.

### Reproduce the subnet-plus-interface stack block

To see the two-group AND, add an interface group that lacks an allow the subnet group has. First ensure the subnet group allows a port, then attach an interface group that does not, and test:

```bash
# subnet group allows 8080
az network nsg rule create \
  --resource-group nsg-lab-rg --nsg-name subnet-nsg \
  --name allow-8080 --priority 250 \
  --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes '*' --source-port-ranges '*' \
  --destination-address-prefixes '*' --destination-port-ranges 8080

# create a NIC group with no 8080 allow, attach it to the interface
az network nsg create --resource-group nsg-lab-rg --name nic-nsg
NIC=$(az vm show --resource-group nsg-lab-rg --name lab-vm \
  --query "networkProfile.networkInterfaces[0].id" -o tsv)
az network nic update --ids "$NIC" --network-security-group nic-nsg

az network watcher test-ip-flow \
  --vm lab-vm --resource-group nsg-lab-rg \
  --direction Inbound --protocol TCP \
  --local 10.20.1.4:8080 --remote 203.0.113.10:50000
```

The flow clears the subnet group's 8080 allow but dies at the interface group, where no allow exists and the default deny matches, so IP flow verify returns Deny naming the interface group's default deny. This is the signature engineers misread most: a default deny when they were certain they wrote an allow, because the allow was on the subnet and the block is on the interface. The fix is to add the 8080 allow to the interface group so both gates permit the flow, after which the effective rules and IP flow verify both confirm the flow passes.

### Reproduce the outbound and service-tag cases

For the outbound block, add a custom deny on internet-bound traffic and test the outbound direction, which exposes a failure an inbound test would never reveal:

```bash
az network nsg rule create \
  --resource-group nsg-lab-rg --nsg-name subnet-nsg \
  --name deny-internet-out --priority 280 \
  --direction Outbound --access Deny --protocol '*' \
  --source-address-prefixes '*' --source-port-ranges '*' \
  --destination-address-prefixes Internet --destination-port-ranges '*'

az network watcher test-ip-flow \
  --vm lab-vm --resource-group nsg-lab-rg \
  --direction Outbound --protocol TCP \
  --local 10.20.1.4:51000 --remote 203.0.113.50:443
```

The outbound test returns Deny naming the custom rule, while an inbound test would have looked perfectly healthy, which is why testing the failing direction is non-negotiable. For the service-tag lesson, replace a tag with a stale IP literal in an allow meant to admit a platform service and watch the intended flow miss the literal and fall to a deny, then restore the correct tag and watch it match again. Each reproduction follows the same loop: induce the block, read the verdict and rule name, apply the one-rule fix, and confirm the verdict flips. When you have produced all six and recognized each signature on sight, the next real incident is a lookup rather than a hunt. Delete the lab with `az group delete --name nsg-lab-rg --yes --no-wait` when you are done.

### Confirm the fix with an actual connection

IP flow verify proves the security group's verdict, but an end-to-end test proves the whole path, and the two together leave no ambiguity. After IP flow verify reports Allow for a flow you fixed, start a listener on the target and attempt a connection from a source to confirm a packet actually completes the handshake. On the target virtual machine, a simple listener on the port under test answers the connection:

```bash
# on the target VM
sudo nc -l -p 8080
```

From a client that should be allowed, attempt the connection and watch for a successful handshake rather than a timeout:

```bash
# from an allowed source
nc -vz 10.20.1.4 8080
# or for a web port
curl -v --max-time 5 http://10.20.1.4:8080/
```

A successful connection confirms the security group, the routes, and the host firewall all permit the flow end to end, which IP flow verify alone cannot tell you because it evaluates only the group. A timeout after IP flow verify said Allow sends you to the route table and the host firewall, exactly the lookalikes the previous section described, and now you know the group is not the cause because you confirmed its verdict first. A connection refused after IP flow verify said Allow tells you the path is open and the listener is the problem, so you check whether the service is running and bound to the right address and port. Running the real connection test closes the gap between what the security group decided and what the wire actually does, and pairing the two is the habit that keeps you from declaring a block fixed when only the group, not the whole path, was ever permitting the flow. The full command library for these checks across the CLI, PowerShell, and the Network Watcher tools lives in the [hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), which is the place to rerun the whole loop on demand.

## How NSG priority and the subnet-plus-NIC stack interact

The two mechanics that produce most surprises, priority ordering and the two-group AND, interact in ways worth making explicit, because a block sometimes emerges only from their combination. Within a single group, priority is a clean total order: the smallest matching number wins, and you can reason about one group as a sorted list. But an interface governed by two groups is not one sorted list; it is two sorted lists, each producing its own verdict, joined by AND for the flow to pass. A flow that is allowed in the subnet group by a rule at priority 100 can still be denied in the interface group by a rule at priority 4096, because the two lists are evaluated independently and both must allow. The priority number from one group says nothing about precedence in the other; there is no cross-group priority comparison. This is why "I have an allow at priority 100, how can anything block it" is a flawed question when two groups are in play. Your allow at 100 governs its own group only.

The effective security rules view is what rescues you from holding two lists in your head, because it presents both groups' rules together and labels which group each rule belongs to, so you can see the subnet verdict and the interface verdict side by side. When you read it, evaluate each group separately for your flow, find the first match in each, and remember that a Deny in either group is fatal regardless of how permissive the other group is. The mental model that prevents the most wasted time is this: traffic must survive every gate it passes through, a flow inbound to an interface passes the subnet gate and then the interface gate, and each gate is an independent first-match-wins decision. Hold that, and the combination of priority and stacking stops being a source of surprise and becomes a checklist: which gates does this flow pass, and does each one allow it.

## NSG requirements for Azure platform services

Several Azure platform services run inside your virtual network on dedicated subnets and depend on specific security rules to function, and attaching a restrictive group to one of their subnets without the rules they require produces a block that looks like a service fault rather than a filtering problem. These cases are worth their own treatment because the missing allow is not for your application's traffic but for the platform's control and data plane, and engineers who do not know the requirement add a tight group and break the service without realizing the group is the cause. Treat the exact ports and tags below as the durable pattern and confirm the specific values against the current official requirements, since the platform revises them.

### Why does Azure Bastion stop working after I add an NSG?

Azure Bastion runs in its own dedicated subnet and requires a defined set of inbound and outbound allows to operate, so attaching a group to that subnet without those rules breaks the session even though Bastion itself is healthy. The session relies on platform control-plane traffic and data-plane traffic that a default-deny posture drops.

When you place a group on the Bastion subnet, the inbound side needs allows for the HTTPS traffic that reaches the service, for the GatewayManager service tag that carries the control plane, for the AzureLoadBalancer tag used by the platform, and for the internal data-plane ports the Bastion hosts use among themselves. The outbound side needs allows reaching the target virtual machines on the remote-desktop and secure-shell ports, reaching the AzureCloud service tag for dependencies, and reaching the data-plane ports within the virtual network. Miss any of these and the connection fails in a way that points at Bastion, when the real cause is a group on the Bastion subnet that lacks a required rule. Diagnose it the same way as any other block: read the effective rules on the Bastion subnet group and run IP flow verify for the specific platform flow that the requirement names, and you will see the default deny matching a flow that should have been allowed. The fix is to add the documented allows for the Bastion subnet rather than loosening the group wholesale, and because the exact ports have changed across versions of the service, verify the current required set against the official requirements before you write the rules.

### Why does my Application Gateway report unhealthy backends with an NSG attached?

An Application Gateway lives in a dedicated subnet and requires inbound allows for a specific high port range used by the gateway's health and management infrastructure, along with the AzureLoadBalancer tag. A group on the gateway subnet that lacks these allows blocks the platform's own management traffic, which the gateway reports as backend health and provisioning failures.

The high port range differs between the v1 and v2 gateway generations, and inbound traffic from the GatewayManager service tag on that range is what keeps the gateway healthy; blocking it leaves the gateway unable to receive the platform communication it needs, and the symptom surfaces as unhealthy backends or a gateway stuck in a failed state. This is one of the clearer cases where the block is not on your application's traffic at all but on the platform's management of the resource you deployed, so an engineer auditing the backend pool and the application finds nothing wrong because the fault is a missing allow on a port range they never think about. Read the effective rules on the gateway subnet group, confirm the high-range inbound allow exists from the correct tag, and add it if it is missing. The closing thread is identical to every other case in this article: the gateway subnet group is just another set of rules, the platform requirement names the flow, and IP flow verify confirms whether the group admits it. Verify the exact range for your gateway generation against the current official requirements, since the values are version-specific.

### Do NSGs even apply to private endpoints?

This is the case where the surprising answer is that the group may not be filtering the traffic you think it is. Historically, a group on a subnet that hosted a private endpoint did not apply to the private endpoint's network interface, so a rule you believed was protecting or blocking the endpoint had no effect on it, and engineers spent time editing a group that the endpoint traffic bypassed entirely. The platform later added the ability to apply network policies to private endpoints, controlled by a network-policies setting on the subnet, and whether your group filters the endpoint depends on that setting.

The practical consequence is twofold. If you intend a group to filter traffic to a private endpoint, confirm that network policies are enabled on the subnet, because with them disabled the group is bypassed and your rules do nothing, which can read as either a security gap or, when you are trying to allow traffic, a block that is not actually the group. If you find that adding or removing a rule on a private-endpoint subnet has no effect on the endpoint's reachability, the network-policies setting is the first thing to check, not the rules. This case inverts the usual diagnosis: instead of finding the rule that blocked the flow, you confirm whether the group is even in the path. Because the behavior and the controlling setting have evolved, verify the current behavior and the setting name against the official documentation for private endpoints before concluding that a group does or does not govern an endpoint's traffic.

## Preventing the block from recurring

The cheapest block to fix is the one you design out. A few habits remove most recurring NSG surprises before they reach an incident channel. Prefer a single group per layer of segmentation rather than reflexively attaching groups to both the subnet and every interface, because each additional group is another independent gate and another place for the next engineer to add a deny that shadows an allow. When a design genuinely needs both a subnet group and interface groups, document why, so the second gate is intentional rather than an artifact of a template nobody questioned. Use service tags instead of IP literals wherever a Microsoft-managed prefix set fits, because literals go stale silently and tags track the service's real address space, which eliminates an entire class of blocks that masquerade as routing failures. Use application security groups to express segmentation by role rather than by address, and bake the interface-to-ASG association into the same deployment that creates the rule, so a rule never ships referencing a group that no interface has joined.

Reserve a clear priority band for baseline denies and another for exceptions, and never improvise a priority number under pressure, because an allow whose number lands on the wrong side of a deny is the priority trap waiting to happen. Treat the security group as code: define it in a template or module, review changes the way you review application changes, and keep the rules expressing intent through tight scoping, so a future reader can tell what each allow is for from its source, port, and name. Enable NSG flow logs on the groups that matter, so when an intermittent block does occur you have the historical record to query rather than a symptom you cannot reproduce. Each of these is a small upfront cost that converts a future guessing game into a quick lookup, and together they shift the team from reacting to blocks to designing groups that rarely block what they should not. The discipline of reading the platform's own decision before changing a rule, the habit this whole series argues for, is far easier to practice when the groups were built to be readable in the first place.

### Define the security group as code

A security group that lives in a Bicep module or a Terraform configuration is reviewable, diff-able, and reproducible, which removes the largest source of accidental blocks: an ad-hoc portal edit that no one recorded and no one can explain a month later. The Bicep below defines a group with named, scoped rules whose intent is legible from the resource itself:

```bicep
resource appNsg 'Microsoft.Network/networkSecurityGroups@2023-05-01' = {
  name: 'app-subnet-nsg'
  location: location
  properties: {
    securityRules: [
      {
        name: 'allow-https-from-office'
        properties: {
          priority: 150
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: '198.51.100.0/24'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '443'
        }
      }
      {
        name: 'allow-lb-probe'
        properties: {
          priority: 200
          direction: 'Inbound'
          access: 'Allow'
          protocol: '*'
          sourceAddressPrefix: 'AzureLoadBalancer'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
    ]
  }
}
```

Two design choices in that snippet prevent specific blocks discussed earlier. The probe allow uses the AzureLoadBalancer service tag rather than an IP literal, so it never goes stale and never causes the health-probe failure that masquerades as a routing problem. The office allow sits at priority 150, deliberately ahead of the priority band you reserve for baseline denies, so it is evaluated first as a sanctioned exception rather than being shadowed. Committing the group to source control means the next change is a reviewed pull request rather than a portal click, and the priority bands and service tags are visible to the reviewer, who can catch a number that lands on the wrong side of a deny before it ships. The [Azure VNet deep dive](/2022/02/28/azure-virtual-network-vnet-deep-dive/) discusses associating these groups to subnets in the same template, which keeps the association from being the forgotten step that leaves an interface unprotected.

### Consolidate rules with augmented security rules

A security group rule can carry multiple source prefixes, multiple destination prefixes, multiple ports, and multiple service tags in a single rule, which the platform calls augmented security rules. Consolidating several related allows into one rule reduces the count you have to reason about and, more importantly, reduces the chance that a flow you meant to permit slips through a gap between two narrowly scoped rules. Where you might otherwise write three separate allows for three application ports from the same trusted source, one rule listing all three ports keeps the intent in a single place and the priority consistent across them.

The benefit for diagnosis is real: fewer rules means a shorter effective-rules list to walk, and a shorter list means the first match is found faster and misread less often. The caution is that an augmented rule's breadth must still be scoped to intent; listing many ports in one allow is fine when those ports genuinely share a source and a purpose, but cramming unrelated flows into one rule to shrink the count sacrifices the legibility that scoping buys you. The right granularity is one rule per coherent intent, broad enough to cover the related ports and prefixes of that intent and no broader. When you read an effective set later, a well-named augmented rule tells the whole story of one access need in a single line.

### Read flow logs with Traffic Analytics

NSG flow logs become far more useful when paired with Traffic Analytics, which aggregates the raw per-flow records into a queryable dataset in a Log Analytics workspace, so you can ask which flows the security group denied over a window rather than parsing storage blobs by hand. A focused query surfaces the denied flows for a destination and port across an incident window:

```kusto
AzureNetworkAnalytics_CL
| where SubType_s == "FlowLog" and FlowStatus_s == "D"
| where DestPort_d == 443
| project TimeGenerated, SrcIP_s, DestIP_s, DestPort_d, NSGRule_s, FlowDirection_s
| order by TimeGenerated desc
```

The NSGRule_s field names the rule that denied each flow, which is the same answer IP flow verify gives but for traffic that already happened, making this the tool for the intermittent block you cannot reproduce on demand. Filtering on the deny status and the port of interest narrows thousands of flows to the handful that were dropped, and the source addresses in the result tell you whether the denied traffic came from where you expected, which often reveals that the real problem is a client calling from an address your allow did not cover. Standing up flow logs and Traffic Analytics before an incident is the difference between diagnosing a transient denial from evidence and trying to recreate a failure that has already passed.

## The failures NSGs get confused with

Not every flow that times out is an NSG, and the most expensive diagnostic errors come from auditing security rules when the block lives elsewhere on the path. The signature that the security group is innocent is an IP flow verify that returns Allow for the exact failing flow; once the group says Allow, stop reading rules and look at routing and the host. Several adjacent failures mimic an NSG block closely enough to send engineers down the wrong path.

A route table, or user-defined route, can drop or misdirect traffic that the security group cheerfully allows. If a UDR sends a flow to a next hop that is a firewall that drops it, or to a virtual appliance that is down, or to None, the packet never reaches the destination even though no security rule denied it. The symptom is identical, a timeout, but IP flow verify on the security group returns Allow, and the next-hop check in Network Watcher reveals the route sending traffic somewhere it dies. The routing layer is a separate filter on the same path, and the [Azure Route Tables and UDRs explained](/2023/12/11/azure-route-tables-udr-explained/) guide covers how a route silently drops traffic the security group permitted, which is the routing counterpart to this article and the place to go the moment IP flow verify exonerates the group.

Peering introduces its own confusion. After two virtual networks are peered, engineers sometimes assume connectivity is established and blame the security group when a flow still fails, but a peering can be connected while a security group on either side denies the traffic, and two spokes peered to a hub cannot reach each other through it at all because peering is not transitive. When traffic fails after a peering is set up, confirm the peering state on both sides and the security rules on both ends before concluding either is the cause; the [fix for Azure VNet peering connection failures](/2022/11/14/fix-vnet-peering-failures/) details the post-peering block where the link is healthy but a rule or a transitivity expectation drops the flow. The two articles pair directly: peering establishes the path, the security group filters it, and a block after peering is almost always one or the other.

The host firewall is the layer Azure cannot see. A flow that clears the security group and the routes can still die at the guest operating system's own firewall, Windows Defender Firewall or iptables, which has no relationship to the Azure security group and is invisible to IP flow verify. When the platform says Allow end to end and the connection still times out, the guest firewall and the application's bind address are the remaining suspects: a service listening only on localhost, a port the application is not actually bound to, or an OS firewall rule that drops the port. Other lookalikes include an application gateway or load balancer health probe failing for a reason other than the security group (a wrong probe path or port), and asymmetric routing where the return path differs from the forward path and a stateful device on the return path drops the reply. The discipline that separates all of these from a real NSG block is the same: confirm the security group's verdict with IP flow verify first, and only when it returns Allow do you spend time on routes, peering, the host, or the probe. To drill these distinctions under realistic incident conditions, [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html), which sets up blocks across the security group, the route table, and the host so you practice telling them apart by signature rather than by guesswork.

A firewall in the path adds another filter that a security group does not see. When a route sends traffic through Azure Firewall or a network virtual appliance, that device applies its own rule set, and it can deny a flow the security group cheerfully allowed, producing the same timeout while IP flow verify on the group returns Allow. The two controls are complementary rather than redundant: the security group is a stateful packet filter close to the resource, while the firewall typically applies application-layer and broader network rules at a central choke point the routes steer traffic toward. Diagnosing a firewall denial means reading the firewall's own logs and rule collections, not the security group, and the tell that you are in firewall territory is a route whose next hop is the firewall combined with a security group that says Allow. Knowing which control owns the decision saves you from auditing security rules when the central firewall is the one dropping the flow, and the order matters: traffic leaving a subnet is filtered by the security group on the way out, then steered by the route table, then filtered by whatever the route points it at.

Two more lookalikes deserve a mention so you do not chase the group for them. Outbound connection failures under load are sometimes source-NAT port exhaustion rather than a security-group deny, where the resource has run out of the ephemeral ports it needs for outbound connections to the same destination, and the symptom is intermittent outbound failures that correlate with connection volume rather than a clean deny that IP flow verify would name. And a flow can be dropped by platform protections or abuse mitigations that are not your security group at all, which again leaves IP flow verify reporting Allow. In every one of these, the single most clarifying action is the same: ask the security group for its verdict on the exact flow, and let an Allow result redirect your attention away from the rules and toward the layer that actually owns the drop.

## Verdict

An NSG blocking traffic is the rare incident where the platform has already computed the answer and is waiting for you to read it. The effective security rules show the exact rule that decided your flow, IP flow verify confirms the verdict and names the responsible rule for a precise five-tuple, and between them the diagnosis is a lookup rather than a hunt. The six causes, the two-group AND, a lower-numbered deny shadowing an allow, a missing allow falling to the default deny, a stale IP literal where a service tag belonged, an overlooked outbound deny, and a missing ASG association, all share the same evaluation mechanic and all yield to the same four-step flow: read the effective rules, find the matching rule by priority, locate which group decided, adjust that one rule. The fix is never a broad allow-any, which over-exposes the workload and may not even resolve the block if the real deny lives on the other group. It is one scoped rule, confirmed by the same IP flow verify that exposed the problem. Read the decision before you change anything, fix the gate that was actually closed, and the afternoon you used to lose to a blocked port becomes a two-command diagnosis. That habit, reasoning from how the platform actually behaves rather than guessing at rules, is what turns a frustrating block into a five-minute fix and is the whole point of learning the security group at the level of its real behavior.

## Frequently Asked Questions

### Q: Why is my NSG blocking traffic even though I added an allow rule?

The most likely reason is that a rule with a smaller priority number is evaluated before your allow and matches the same flow with a Deny, sealing the verdict before your allow is consulted, since the first matching rule wins. The second most likely reason is the subnet-plus-interface stack: your allow is on one group, but the other group governing the same interface lacks the allow or has its own deny, and both groups must allow for traffic to pass. Run IP flow verify for the exact flow to see which rule and which group decided it. If the named rule is a lower-numbered deny, lower your allow's number below it or tighten the deny; if it is a default deny on the other group, add the matching allow to that group. The allow you added is real, it is simply not the rule the platform reached first or not on the layer that mattered.

### Q: How do I find exactly which NSG rule is blocking my connection?

Use IP flow verify in Network Watcher, which evaluates a specific five-tuple against the effective rules for an interface and returns the access value and the name of the matching rule in one call, without sending a packet or depending on the application being up. Supply the direction, the protocol, the local IP and port, and the remote IP and port, and read the ruleName field in the response: it is the exact rule that decided the flow. For a broader view, query the effective security rules for the interface, which merges the subnet and interface groups into the ordered list Azure actually applies, so you can scan in priority order for the first rule that covers your flow. Both approaches give the authoritative answer, and IP flow verify is the faster of the two when you already know the precise flow you are testing.

### Q: Does a lower priority number win in an NSG?

Yes, a lower priority number has higher precedence and is evaluated first. Azure walks the rules in ascending numeric order and applies the first rule whose source, destination, port, and protocol match the flow, and that first match is final, so a smaller number takes effect over any larger-numbered rule that would also match. Custom rules occupy numbers from 100 to 4096, and the un-removable default rules sit at the very top of that range with the lowest precedence, which is why any normal custom rule is evaluated before the defaults. The practical consequence is that adding an allow with a larger number than an existing deny does nothing if the deny matches first. To make an allow take precedence over a deny, give it a smaller number, but only when the deny is meant to permit sanctioned exceptions rather than being absolute.

### Q: What happens when an NSG is on both the subnet and the network interface?

Both groups apply, and their verdicts combine as a logical AND, so traffic must be allowed by both for it to pass. For an inbound flow, the subnet group is evaluated and then the interface group; for an outbound flow, the interface group is evaluated and then the subnet group. Each evaluation is an independent first-match-wins decision, and a Deny in either group drops the flow no matter how permissive the other group is. This stacking is the most common reason a correct-looking allow has no effect: the rule is right but sits on one group while the other group lacks the allow or carries a deny. Reading the effective security rules shows both groups' rules labeled by association, so you can check each gate separately. When the design does not need two layers of segmentation, a single group per layer removes the second gate and the confusion it causes.

### Q: Does the NSG default deny block traffic with no explicit allow?

Yes. Every network security group ends with an inbound deny-all and an outbound deny-all that you cannot delete, sitting at the lowest precedence. Any flow that matches none of your custom rules and none of the higher-precedence default allows falls through to the relevant deny-all and is dropped. The absence of an allow is therefore itself a block, which is why a freshly created group that allows only SSH will refuse every other inbound connection from outside the virtual network. IP flow verify confirms this case by returning Deny with the ruleName set to the default deny, the unambiguous signature of a missing allow rather than an active deny. The fix is to add the specific inbound allow your workload needs, scoped to the source prefix, destination port, and protocol you actually require, so the default deny continues to protect every flow you did not explicitly permit.

### Q: How do service tags and application security groups affect what an NSG matches?

A service tag is a Microsoft-managed set of IP prefixes for a service, such as VirtualNetwork, AzureLoadBalancer, Internet, or Storage, used as a source or destination in place of IP literals, and Microsoft keeps the underlying addresses current so the rule tracks the service automatically. Using a stale IP literal or the wrong tag where a service tag belongs causes the rule to miss the flow, which then falls to a deny, a failure that looks like routing but is a matching problem. An application security group is a logical group of network interfaces you reference in a rule instead of addresses, expressing segmentation by role; the rule only applies to an interface once that interface is associated with the group. A rule naming an ASG the interface has not joined does not match it at all, so the interface falls to the default deny while the rule appears correct.

### Q: Why does my load balancer health probe fail with an NSG in place?

A health probe originates from the platform's load balancer infrastructure, whose source addresses are covered by the AzureLoadBalancer service tag, and the default inbound rules include an allow for that tag. The probe fails when a custom rule denies it or when an allow meant to admit it was scoped to a hard-coded IP range instead of the service tag, because the literal range goes stale as the probe source addresses shift. The result is a backend marked unhealthy even though the application is healthy, since the probe cannot reach the instance. Confirm with IP flow verify using a source in the load balancer range and the probe port, and read whether a custom deny matched or a stale literal failed to match the allow. The fix is to allow the probe using the AzureLoadBalancer service tag rather than an IP literal, so the rule tracks the real probe source space.

### Q: How do I check whether the block is the NSG or the route table?

Run IP flow verify for the exact failing flow first. If it returns Allow, the security group is not the cause and you should look at routing, so use the next-hop check in Network Watcher to see where the route table sends the traffic. A user-defined route can send a flow to a firewall that drops it, to a virtual appliance that is down, or to a None next hop, and the packet never reaches the destination even though no security rule denied it, producing the same timeout symptom. The two layers filter the same path independently: the security group decides allow or deny, and the route table decides where the packet goes next. Confirming the group's Allow verdict before touching routes prevents the most common wasted effort, auditing security rules when the route is the real cause, and the next-hop check pinpoints the misdirecting route directly.

### Q: Why do my outbound connections fail while inbound works?

Inbound and outbound rules are evaluated independently, so an outbound deny can block a flow that no inbound rule ever sees. The default outbound posture allows traffic to the virtual network and the internet, so outbound usually works without custom rules, which makes a custom outbound deny easy to overlook when one exists and matches your flow. A baseline that denies outbound to the internet to force traffic through a controlled egress will block a direct outbound call, and the application reports a timeout connecting out while every inbound test passes. Run IP flow verify with the direction set to Outbound, because an inbound test proves nothing about the failing direction and will always look healthy. If the outbound destination is sanctioned, add a scoped outbound allow at a smaller priority number than the deny; if egress should flow through a firewall, the destination or next hop is what needs fixing rather than the security group.

### Q: Can I just add an allow-any rule to unblock traffic quickly?

You can, and it is the single worst fix in most situations, for two reasons. First, an inbound allow-any opens every port from every source, converting a closed posture into an open one the moment the symptom clears, and the rule carries no record of the flow it was meant to permit, so no one can safely narrow it later. Second, it may not even work: if the real blocker is a lower-priority deny on the other group in a subnet-plus-interface stack, your broad allow on this group lets the flow proceed to the second gate, where the deny still drops it, leaving you with exposure and an unresolved block. The correct approach is to confirm the deciding rule with IP flow verify, then add one scoped allow for exactly the flow that was blocked, on the group that actually denied it, and re-confirm with IP flow verify that the verdict flipped.

### Q: How do I confirm an NSG fix actually worked?

Re-run IP flow verify for the exact five-tuple you were testing before the change, and treat the fix as complete only when the access value flips to Allow and the ruleName names your intended allow rather than a deny. Confirming with the same tool that diagnosed the block closes the loop, because you saw the original deny, you made one targeted change, and you see the allow, with no ambiguity about which edit mattered. If the access is still Deny, read the ruleName again: a different deny may be matching, or the change landed on the wrong group in a two-group stack. For an end-to-end check that a real connection now succeeds, follow IP flow verify with a connectivity check from the source, which actually attempts the connection and reports the path, but the security-group verdict from IP flow verify is the definitive answer for whether the group still blocks the flow.

### Q: Why does my rule referencing an application security group have no effect?

The interface you expect it to protect is almost certainly not a member of the application security group the rule references. An ASG rule applies to an interface only after that interface has been associated with the group, so a rule naming the "web" ASG does not touch a web server whose interface was never joined to it, and the server falls to the default deny while the rule looks correct in the text. This commonly happens in automation that creates the application security groups and the rules but omits the interface association step. The signature is that the ASG-referencing rule does not appear in the effective security rules for the interface, because it does not apply outside the group. The fix is to associate the interface with the application security group, after which the rule applies and the effective set includes it. Bake the association into the same deployment that creates the rule to prevent the gap.

### Q: Does an NSG block traffic between two subnets in the same VNet?

By default, no, because the inbound default rules include an allow for traffic whose source is the VirtualNetwork service tag, which covers all address space in the virtual network and any peered networks, so same-VNet subnet-to-subnet traffic is permitted unless you add a rule that denies it. When subnet-to-subnet traffic is blocked, a custom rule is the cause: a deny scoped to the VirtualNetwork tag or to the other subnet's prefix, or an allow that was supposed to permit the flow but is shadowed by a lower-numbered deny. IP flow verify with a source and destination in the two subnets names the deciding rule. If you intend to segment subnets from each other, you do so by adding explicit denies, and if that segmentation is blocking traffic you actually need, the fix is a scoped allow at a smaller priority number than the deny, permitting only the specific intra-VNet flow required.

### Q: What does it mean when IP flow verify says Allow but the connection still fails?

It means the security group is not blocking the flow and the cause lies elsewhere on the path. The remaining suspects are the route table, where a user-defined route may send the packet to a next hop that drops it; the guest operating system firewall, which Azure cannot see and which can drop the port independently of the security group; the application itself, which may not be listening, may be bound only to localhost, or may be on a different port; and asymmetric routing, where the return path differs from the forward path and a stateful device drops the reply. Check the next hop with Network Watcher to clear the route table, then inspect the host firewall and the application's bind address and listening port. The value of the Allow verdict is that it definitively removes the security group from the investigation, so you stop reading rules and move to the layers Azure's filter does not govern.

### Q: How do NSG flow logs help diagnose an intermittent block?

NSG flow logs record each flow that the security group evaluated, including the source and destination addresses, the port, the protocol, and whether the group allowed or denied it, written to a storage account and queryable after the fact. This is the tool for a block you cannot reproduce on demand, because IP flow verify and the effective-rules view tell you the current decision for a flow you can describe now, while flow logs preserve the history of what was actually allowed and denied over time. When a connection fails intermittently, query the flow logs for the affected source, destination, and port across the window when it failed, and look for denied entries to confirm whether the security group dropped the flow during the incident or whether the drops happened elsewhere. Enabling flow logs in advance on the groups that matter is the difference between diagnosing a transient block from evidence and trying to recreate a failure that no longer occurs.

### Q: Should I use one NSG on the subnet or separate NSGs per interface?

Prefer a single group at the layer of segmentation you need, usually the subnet, unless a specific requirement justifies a second layer. Each additional group is an independent gate that traffic must pass and an additional place for an engineer to add a deny that shadows an allow or to forget an allow entirely, so two groups on the same interface double the surface for the subnet-plus-interface block. A subnet group governs every interface in the subnet uniformly, which is simpler to reason about and easier to audit. Interface groups earn their place when a single subnet hosts workloads that need genuinely different rules and you do not want to split them into separate subnets, in which case the interface group expresses the per-workload difference. When you do use both, document why the second layer exists, so the next engineer treats it as intentional rather than an unexplained second gate to debug.

### Q: Why is inbound internet traffic blocked by default but outbound allowed?

The default rules are asymmetric by design. Inbound, the defaults allow traffic from the virtual network and from the Azure load balancer, then deny everything else, so traffic originating on the public internet is denied unless you add an explicit allow. Outbound, the defaults allow traffic to the virtual network and to the internet, then deny the rest, so a host can initiate connections out without a custom rule. This asymmetry reflects a sensible posture: a resource should not be reachable from the internet until you deliberately expose it, but it should be able to reach out to fetch updates and call services. It explains the common early experience of a new virtual machine that can install packages and call APIs but cannot be reached on a web port until an inbound allow is added. To expose an inbound service, add a scoped allow for the source and port; the default outbound allow already permits the host's own outbound calls.

### Q: Why does Azure Bastion fail to connect after I attach an NSG to its subnet?

Bastion runs in a dedicated subnet and depends on a defined set of inbound and outbound allows for its control plane and data plane, so a group on that subnet without those rules drops the platform traffic the session needs even though Bastion itself is healthy. Inbound, it needs allows for the HTTPS entry traffic, the GatewayManager service tag, the AzureLoadBalancer tag, and the internal data-plane ports; outbound, it needs allows to reach target machines on the remote-desktop and secure-shell ports, the AzureCloud tag, and the data-plane ports within the network. Diagnose it like any block by reading the effective rules on the Bastion subnet and running IP flow verify for the specific platform flow, which shows the default deny matching a flow that should pass. Add the documented allows rather than loosening the group, and verify the current required ports against the official requirements, since they have changed across service versions.

### Q: Why does adding or removing an NSG rule have no effect on my private endpoint?

Because the group may not be in the path of the private endpoint's traffic at all. A group on a subnet that hosts a private endpoint historically did not apply to the endpoint's interface, and whether it applies now depends on a network-policies setting on the subnet. If that setting leaves network policies disabled, the group is bypassed for the endpoint and your rule changes do nothing to its reachability, which can look like either a stubborn block or a security gap depending on what you were trying to do. When edits to a private-endpoint subnet's group produce no change in the endpoint's behavior, check the network-policies setting before you keep editing rules, because the rules are not being evaluated for that traffic. The behavior and the controlling setting have evolved over time, so confirm the current behavior against the official documentation for private endpoints before concluding whether the group governs the endpoint.
