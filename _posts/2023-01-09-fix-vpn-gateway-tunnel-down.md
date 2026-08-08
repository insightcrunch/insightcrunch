---
layout: post
title: "Fix Azure VPN Gateway Tunnel Disconnects"
page_title: "Fix Azure VPN Gateway Tunnel Down: Diagnose IPsec and IKE Mismatch, Wrong Pre-Shared Key, Traffic Selector, and Routing Failures Step by Step"
date: 2023-01-09
categories: ["Technology"]
tags: ["Azure", "VPN Gateway", "Troubleshooting", "Networking", "IPsec", "Cloud Computing"]
excerpt: "An Azure VPN gateway tunnel that drops or never connects is almost always a setting the two ends disagree on. Diagnose the real cause and align both sides."
image: "/assets/images/blog/blog-22.webp"
reading_time: 60
author: "benjamin-scott"
last_updated: 2023-01-09
lang: en
---
A site-to-site connection that sits at Connecting forever, a tunnel that comes up and then drops every few hours, a link that carries traffic to one subnet but blackholes another: these are the three faces of the same incident, and an Azure VPN gateway tunnel that will not stay up is one of the most common connectivity failures an engineer inherits. The symptom looks like an Azure problem, so the reflex is to delete the gateway and build a fresh one. That reflex is almost always wrong, and it wastes the better part of an hour because gateway provisioning is slow. The tunnel is not a thing Azure owns. It is a negotiation between two devices, the Azure gateway on one end and your on-premises firewall or router on the other, and a negotiation fails when the two parties cannot agree on terms. The fix is to find the term they disagree on and make them agree, not to replace one of the negotiators.

This article diagnoses the failure to root cause. You will learn to read the two phases a tunnel goes through before it carries a single packet, to gather the diagnostic signal that tells you which phase failed, and to map the failure to one of a small set of distinct causes: an IKE phase 1 parameter mismatch, an IPsec phase 2 parameter mismatch, a wrong or rotated pre-shared key, a traffic-selector or policy-based mismatch, a routing problem over an otherwise healthy tunnel, or a tunnel that flaps under rekey. For each cause you get the check that confirms it is yours and the command that fixes it on the correct end.

![Diagnosing Azure VPN gateway tunnel disconnects and IPsec mismatch root causes - Insight Crunch](/assets/images/blog/blog-22.webp)

## What a down Azure VPN gateway tunnel actually means

Before you can fix the tunnel you have to know what "the tunnel" is, because the word covers two separate negotiations that happen one after the other, and they fail for different reasons with different fixes. A site-to-site connection is an IPsec tunnel, and IPsec is built on top of the IKE protocol, the Internet Key Exchange. IKE runs first and establishes a secure channel between the two gateways so they can exchange keys safely. IPsec runs second and uses that secure channel to negotiate the encryption that protects the actual data packets. Microsoft and the IPsec standard label these as Main Mode and Quick Mode, or as phase 1 and phase 2. IKE is phase 1, the Main Mode handshake. IPsec is phase 2, the Quick Mode that follows. A tunnel that never reaches Connected has failed in one of these two phases, and knowing which one narrows the cause from a dozen possibilities to two or three.

Phase 1 establishes the IKE security association. The two ends must agree on an encryption algorithm, an integrity or hashing algorithm, a Diffie-Hellman group for the key exchange, the authentication method, and the lifetime of the association. They also have to authenticate each other, and for a site-to-site connection that authentication is a pre-shared key, a secret string that must be byte-for-byte identical on both ends. If phase 1 cannot complete, nothing else happens, and the connection sits at Connecting because the two gateways are still arguing about how to talk securely. Phase 2 establishes the IPsec security association that protects the data. It negotiates the encryption and integrity for the data packets, an optional Perfect Forward Secrecy group, the security association lifetimes, and the traffic selectors that define which address ranges are allowed through the tunnel. Phase 2 can fail even when phase 1 succeeded, and that distinction is one of the fastest ways to localize the problem.

The mental model worth holding is that a tunnel is a contract with many clauses, and both signatories have to accept every clause for the contract to take effect. The Azure side states its terms through its connection configuration and, optionally, a custom IPsec policy. The on-premises device states its terms through its own crypto configuration. When the two documents differ on even one clause, the negotiation collapses, and the side that initiated will log a proposal mismatch while the side that responded will log that it rejected the offer. This is the foundation of every diagnosis that follows, and it is why recreating the gateway so rarely helps: a fresh gateway with the same connection settings restates the same terms the on-premises device already rejected.

### Why does my Azure VPN tunnel keep disconnecting?

A tunnel that connects and then drops repeatedly is rarely a broken gateway. The usual causes are a security association lifetime mismatch that makes rekey fail, dead peer detection tearing down an idle tunnel, an on-premises device that renegotiates on its own schedule, or an underlying internet path that is itself unstable. Confirm with the tunnel diagnostic logs before changing anything.

The reason this question matters so much is that an intermittent drop and a never-connect are different incidents with overlapping symptoms. A tunnel that has carried traffic for weeks and then begins dropping every few hours did not suddenly develop a parameter mismatch, because a mismatch would have stopped it from ever connecting. Something changed, or something time-based is firing: a rekey interval was reached and the rekey negotiation failed, a key was rotated on one end only, the on-premises device rebooted, or the public IP on either side changed. A tunnel that has never connected at all, by contrast, almost certainly has a mismatch present from the first handshake. Reading the history of the tunnel, not just its current state, is the single most useful diagnostic habit you can build.

## How to read the tunnel state and gather the diagnostic signal

The first move on any tunnel incident is to read the connection status and the diagnostic logs rather than to change a setting. Guessing at parameters and toggling them one at a time is the slowest path to a fix, because each guess requires a renegotiation and a wait, and a wrong guess can break a tunnel that was only half-broken. Azure exposes the tunnel's health in several places, and each tells you a different part of the story.

The connection status is the headline. A site-to-site connection reports one of a few states, and the two that matter most are Connecting and Connected. Connected means phase 1 and phase 2 both completed and the IPsec security associations are established; if traffic still does not flow at that point, the problem is routing, not the tunnel itself, and you move to a different part of this guide. Connecting means the negotiation has not completed, which points at a parameter mismatch, a pre-shared key problem, or a path that never reaches the peer. You read the status with the CLI or PowerShell rather than the portal, because the command output is scriptable and shows the byte counters that tell you whether anything has ever crossed the tunnel.

```bash
# Read the connection status and the traffic counters with the Azure CLI
az network vpn-connection show \
  --resource-group rg-network-prod \
  --name cn-onprem-hq \
  --query "{status:connectionStatus, ingress:ingressBytesTransferred, egress:egressBytesTransferred}" \
  --output table
```

```powershell
# The same read in PowerShell, which also surfaces the tunnel-level connection status
$conn = Get-AzVirtualNetworkGatewayConnection `
  -ResourceGroupName 'rg-network-prod' `
  -Name 'cn-onprem-hq'
$conn | Select-Object Name, ConnectionStatus, EgressBytesTransferred, IngressBytesTransferred
```

The byte counters are more revealing than they look. Egress bytes that climb while ingress bytes stay at zero is the classic signature of an asymmetric problem: the Azure side is sending, the on-premises side is not sending back, and the cause is usually on-premises routing or a firewall rule that drops the return traffic. Both counters at zero with a Connecting status means the tunnel never established. Both counters climbing means the tunnel is healthy and any application complaint is above the network layer.

The diagnostic logs are where the negotiation itself is recorded, and turning them on is the highest-value preparation you can do before an incident. The gateway emits several log categories to a Log Analytics workspace, and the two that carry the most diagnostic weight are the tunnel diagnostic log, which records connect and disconnect events with a reason, and the IKE diagnostic log, which records the phase 1 and phase 2 negotiation messages including the proposal that was rejected. You enable them through a diagnostic setting on the gateway resource, then query them with KQL once they have accumulated a few minutes of data.

```kusto
// Tunnel connect and disconnect events with the reason the gateway recorded
AzureDiagnostics
| where Category == "TunnelDiagnosticLog"
| where TimeGenerated > ago(2h)
| project TimeGenerated, OperationName, remoteIP_s, instance_s, stateChangeReason_s
| order by TimeGenerated desc
```

```kusto
// IKE negotiation messages, which name the proposal mismatch when phase 1 or phase 2 fails
AzureDiagnostics
| where Category == "IKEDiagnosticLog"
| where TimeGenerated > ago(1h)
| where Message contains "negotiation" or Message contains "proposal" or Message contains "payload"
| project TimeGenerated, remoteIP_s, Message
| order by TimeGenerated asc
```

The IKE diagnostic log is the closest thing to a confession the gateway will give you. When phase 1 fails on a parameter, it logs that it received a proposal and found no matching policy, and the message frequently names the algorithm or group that did not match. When the pre-shared key is wrong, it logs an authentication failure during the handshake rather than a proposal mismatch, which is how you tell a key problem apart from a crypto mismatch without touching either. When phase 2 fails, it logs a Quick Mode failure after phase 1 succeeded, which immediately tells you the IKE settings are fine and the problem is in the IPsec proposal or the traffic selectors. Reading these messages turns a guessing game into a lookup.

When the logs are not enough, a packet capture on the gateway shows the IKE exchange on the wire, and it is the tool that resolves the ambiguous cases. A capture that shows your gateway sending IKE packets to the peer with no response means the packets are not arriving, which is a firewall or NAT problem on the path rather than a parameter mismatch. A capture that shows packets in both directions but the negotiation never completing means the two ends are reaching each other and disagreeing on terms.

```powershell
# Capture IKE traffic on the gateway to a storage account for offline analysis
Start-AzVirtualNetworkGatewayConnectionPacketCapture `
  -ResourceGroupName 'rg-network-prod' `
  -Name 'gw-hub-vpn' `
  -LinkConnectionName 'cn-onprem-hq'

# Stop the capture and write it to a SAS URL when you have reproduced the failure
Stop-AzVirtualNetworkGatewayConnectionPacketCapture `
  -ResourceGroupName 'rg-network-prod' `
  -Name 'gw-hub-vpn' `
  -SasUrl '<storage-sas-url>'
```

You should pair these reads with the on-premises side from the start, because half of every tunnel lives on a device Azure cannot see. The firewall or router logs its own view of the negotiation, and the most efficient diagnosis lays the Azure IKE log next to the on-premises IKE log and reads them together. If you want a place to rehearse this side-by-side reading against a tunnel you can break on purpose, you can [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html), which is exactly the kind of practice that makes the log messages familiar before you meet them under incident pressure.

### How do I tell which side of the tunnel is failing?

Read the phase that failed. If the Azure IKE log shows no matching policy during Main Mode, phase 1 failed and the disagreement is in the IKE crypto or the pre-shared key. If Main Mode completed and Quick Mode failed, phase 2 is the problem, which is the IPsec proposal or the traffic selectors. The phase localizes the clause both ends disagree on.

This phase-first approach saves you from the most common waste of effort, which is changing IPsec settings when the failure was in IKE, or rotating a key when the failure was a Diffie-Hellman group. The negotiation is strictly ordered, so a failure in the later phase is proof that everything in the earlier phase already agreed. Once you know the phase, you know which set of parameters to compare, and the comparison itself usually finds the mismatch in under a minute.

## The both-ends-must-agree rule

The single claim that organizes every VPN tunnel diagnosis is this: a tunnel is a negotiation, so a drop or a failure to establish is almost always a parameter the two ends disagree on, and you find it by comparing both configurations rather than changing one side. Call it the both-ends-must-agree rule. It is the same diagnostic instinct that runs through the rest of this series, the habit of finding the root cause before changing anything, and it reframes the work from "fix the Azure gateway" to "find the clause the contract disagrees on." This is the same two-sided reasoning that the private-connectivity sibling demands, and you can see it applied to a circuit failure in the guide to [fixing an ExpressRoute circuit that is down](/2023/01/02/fix-expressroute-circuit-down/), where the diagnosis again splits across the Azure edge and the provider edge.

The rule has a sharp practical consequence. Because the negotiation is symmetric, a setting that looks correct in the Azure portal can still be wrong, because correct means matching, not matching some default. The Azure default policy proposals are chosen to interoperate with a wide range of devices, but the moment either end specifies a custom policy, both ends must use the exact same combination, and a partial match is no match at all. The standard supports many algorithms in many combinations, and the gateway will only accept the specific proposal it has been told to accept. A clause that is reasonable on its own, such as a 28800 second IKE lifetime, breaks the tunnel if the other end insists on 86400, not because either value is wrong but because they differ.

This is also why the most damaging misdiagnosis is to recreate the gateway. Deleting and rebuilding the Azure gateway restates the identical connection terms to an on-premises device that already rejected them, costs you the long provisioning time, and changes the gateway public IP, which then forces a configuration change on the on-premises device anyway. The rule tells you to compare first. If the two configurations agree on every clause, you have a path or routing problem, not a negotiation problem, and rebuilding the gateway would not have touched it.

## The InsightCrunch VPN tunnel table

The findable artifact for this article is a table that maps each cause to the signal that confirms it and the end you fix it on. Keep it next to the IKE diagnostic log while you work. The phase column tells you where to look, the confirming signal tells you when you have found it, and the fix-on column reminds you that some fixes belong on the Azure side, some on the on-premises side, and many require a coordinated change on both.

| Cause | Phase that fails | Confirming signal | Fix is applied on |
| --- | --- | --- | --- |
| IKE crypto mismatch | Phase 1 (Main Mode) | IKE log: no matching policy during Main Mode; names a mismatched algorithm or DH group | Both ends, aligned to one policy |
| Wrong or rotated pre-shared key | Phase 1 (Main Mode) | IKE log: authentication failure, not a proposal mismatch | Both ends, identical key string |
| IPsec crypto or PFS mismatch | Phase 2 (Quick Mode) | Main Mode completes, Quick Mode fails on the proposal | Both ends, aligned to one policy |
| Traffic selector or policy-based mismatch | Phase 2 (Quick Mode) | Quick Mode fails on selectors; one end is policy-based, the other route-based | On-premises selectors or Azure UsePolicyBasedTrafficSelectors |
| Static or BGP routing failure | None (tunnel is Connected) | Status Connected, egress climbs, ingress stays zero, or routes not learned | Route tables, UDRs, or BGP configuration |
| Rekey or DPD flap | Phase 1 or 2 on renegotiation | Periodic disconnect in the tunnel log at the lifetime interval | SA lifetimes and DPD timeout, aligned both ends |
| Firewall or NAT blocking the path | None reaches the gateway | Capture shows outbound IKE with no response | On-premises firewall, UDP 500 and 4500, ESP |
| Point-to-site client failure | Client-side TLS or auth | P2S diagnostic log; client cannot authenticate or route | Client config, certificates, address pool |

The table is deliberately organized by phase first, because the phase is the cheapest thing to read and it eliminates whole rows at a stroke. If Main Mode completes, the first two rows are gone. If the status is Connected, every row above the routing row is gone and you are looking at a routing or path problem. Work the table top to bottom only after the phase has narrowed it.

## Cause one: an IKE phase 1 parameter mismatch

The most frequent reason a brand-new tunnel never connects is that the IKE phase 1 proposals do not match. Phase 1 negotiates five things, and all five have to align: the encryption algorithm, the integrity or pseudo-random function, the Diffie-Hellman group, the authentication method, and the SA lifetime. The Azure gateway, left on its default policy, offers a set of proposals chosen for broad interoperability, and a stock firewall left on its defaults will often find one in common. The trouble starts when either end is pinned to a specific policy, which happens constantly in regulated environments that mandate a particular cipher suite, or when an older device only supports algorithms the modern default set has dropped.

### Does an IPsec or IKE parameter mismatch drop the tunnel?

Yes, and it is the most common reason a new tunnel never reaches Connected. Both ends must agree on the encryption, integrity, and Diffie-Hellman group for IKE, and on the encryption, integrity, and Perfect Forward Secrecy group for IPsec. A single mismatched value makes the proposal unacceptable, the negotiation fails, and the connection stays at Connecting.

You confirm an IKE mismatch by reading the IKE diagnostic log during a reconnect attempt. The telltale message is that the gateway received a Main Mode proposal and found no matching policy, and the message will often print the offered transform so you can see exactly which value differs from your Azure side. The Diffie-Hellman group is the most common single offender, because device vendors default to different groups and a group mismatch produces a clean, early failure that is easy to read once you know to look for it. The fix is to define one IKE policy you control and apply it identically to both ends rather than relying on either set of defaults. On Azure you build a custom IPsec policy object and attach it to the connection.

```powershell
# Define one explicit IKE and IPsec policy and apply it to the Azure connection
$policy = New-AzIpsecPolicy `
  -IkeEncryption AES256 `
  -IkeIntegrity SHA256 `
  -DhGroup DHGroup14 `
  -IpsecEncryption AES256 `
  -IpsecIntegrity SHA256 `
  -PfsGroup PFS2048 `
  -SALifeTimeSeconds 27000 `
  -SADataSizeKilobytes 102400000

$conn = Get-AzVirtualNetworkGatewayConnection `
  -ResourceGroupName 'rg-network-prod' -Name 'cn-onprem-hq'

Set-AzVirtualNetworkGatewayConnection `
  -VirtualNetworkGatewayConnection $conn `
  -IpsecPolicies $policy `
  -UsePolicyBasedTrafficSelectors $false
```

When you apply a custom policy you must specify the complete policy for both IKE and IPsec, because a partial specification is not allowed and the gateway will reject an incomplete object. Once the policy is set, the gateway sends and accepts only that exact proposal, which removes the ambiguity of the default set entirely. The matching step is to configure the on-premises device with the identical encryption, integrity, group, and lifetime values. The specific algorithms and Diffie-Hellman groups supported, and the default proposal sets, are values to confirm against the current Azure cryptographic requirements documentation at the time you build the tunnel, because the supported set changes as weaker algorithms are deprecated. The route-based default and the full algorithm matrix are covered in depth in the [Azure VPN gateway deep dive](/2023/11/27/azure-vpn-gateway-deep-dive/), which is the right reference when you are choosing the policy rather than repairing a mismatch.

A subtle variant of the IKE mismatch is an IKE version mismatch. Azure route-based gateways negotiate IKEv2, and many older configurations or policy-based scenarios assume IKEv1. If the on-premises device is configured for IKEv1 while the Azure connection expects IKEv2, the Main Mode handshake never finds common ground, and the symptom is identical to a crypto mismatch even though the cause is a protocol version. The fix is to align the IKE version, which usually means configuring the on-premises device for IKEv2 against a modern route-based gateway.

## Cause two: an IPsec phase 2 parameter mismatch

When the IKE log shows Main Mode completing and Quick Mode failing, the disagreement has moved to phase 2, the IPsec security association that protects the data. Phase 2 negotiates the data encryption algorithm, the data integrity algorithm, an optional Perfect Forward Secrecy group, and the SA lifetimes for the data channel. A phase 2 mismatch is genuinely good news during a diagnosis, because it proves phase 1 agreed, which means the pre-shared key is correct and the IKE crypto is aligned, eliminating the two most common causes at once.

The PFS group is the most frequent phase 2 culprit. Perfect Forward Secrecy performs a fresh Diffie-Hellman exchange for the data keys so that compromising one key does not expose past traffic, and it is an optional feature that one end can enable and the other disable. If Azure expects PFS group 14 and the on-premises device has PFS disabled, the Quick Mode proposals will not match, and the tunnel fails at phase 2 with a clean log entry. The fix is to choose one PFS setting and apply it on both ends, including the choice to disable it on both if your policy allows. The second frequent culprit is the IPsec SA lifetime, where a difference in the data SA lifetime seconds or the SA data size kilobytes produces a phase 2 rejection on some device implementations even though others tolerate the difference and simply use the lower value.

```bash
# Inspect the IPsec policy currently applied to the connection, then align the on-premises device to it
az network vpn-connection ipsec-policy list \
  --resource-group rg-network-prod \
  --connection-name cn-onprem-hq \
  --output json
```

The matching discipline for phase 2 is the same as phase 1: define the values once on the Azure side, read them back to confirm they took effect, and transcribe the identical data encryption, integrity, PFS group, and lifetimes onto the on-premises device. Because the standard supports null encryption for maximum throughput on route-based and high performance gateways, you will occasionally meet a tunnel that negotiated null encryption when someone chose it for a throughput benchmark, which protects nothing and should never survive into production. Reading the negotiated phase 2 transform confirms what the tunnel actually settled on rather than what you intended.

## Cause three: a wrong or rotated pre-shared key

The pre-shared key is the authentication for a site-to-site tunnel, and it must be byte-for-byte identical on the Azure connection and the on-premises device. A key mismatch fails in phase 1, during the authentication step of Main Mode, and the IKE diagnostic log distinguishes it from a crypto mismatch by recording an authentication failure rather than a no-matching-policy message. That distinction is the fastest way to tell a key problem from a parameter problem without changing either, and it is worth committing to memory because the two failures look identical from the connection status alone.

### Can a wrong pre-shared key break a tunnel that worked yesterday?

Yes, and it is a common cause of a tunnel that suddenly drops. A key rotation applied to only one end, a trailing space pasted into the key field, an encoding difference, or a secret that expired in a key store all change the effective key on one side. The authentication step of Main Mode then fails even though every crypto parameter still matches, and the tunnel will not reestablish until both ends carry the identical string.

You confirm a key problem by reading the current key from the Azure connection and comparing it character for character against the on-premises configuration. The most common real-world causes are mechanical: a key copied with a trailing newline, a key that contains a character the on-premises device mishandles, or a key rotation that updated the secret store but never propagated to one of the two devices. Treat the key as a literal string and compare it byte for byte.

```bash
# Read the shared key currently set on the Azure connection
az network vpn-connection shared-key show \
  --resource-group rg-network-prod \
  --connection-name cn-onprem-hq \
  --output tsv

# Set a new shared key on the Azure side; apply the identical string on the on-premises device
az network vpn-connection shared-key update \
  --resource-group rg-network-prod \
  --connection-name cn-onprem-hq \
  --value 'the-exact-same-secret-on-both-ends'
```

When you rotate a key, the only safe procedure is to change it on both ends inside a short window and accept a brief drop while the tunnel renegotiates, because there is no moment at which two different keys can both be valid. A change-management habit that updates one device and schedules the other for later guarantees an outage. If you store the key in a secret store and have automation push it to both ends, the failure mode shifts to the automation: a pipeline that updated the Azure connection but failed silently on the on-premises push leaves you with a one-sided rotation that looks exactly like a typo. Reading the key from both ends after any rotation is the cheap confirmation that closes the case.

## Cause four: traffic selectors and the policy-based versus route-based trap

The deepest and most confusing tunnel failure is the traffic-selector mismatch, and it is rooted in the difference between route-based and policy-based gateways. A route-based gateway uses any-to-any traffic selectors and decides what to send through the tunnel based on routes, which is why it supports multiple connections and BGP. A policy-based gateway, the legacy model, ties the tunnel to specific source and destination address prefixes, the traffic selectors, and only traffic matching those exact prefixes is allowed through. The trap appears when one end uses one model and the other uses the other, because their idea of what the tunnel carries is structurally different.

The most common form of this is a modern Azure route-based gateway facing an on-premises device that can only do policy-based, prefix-bound tunnels. By default they will not agree on selectors, because the route-based side offers the wildcard any-to-any selector and the policy-based side insists on specific prefixes. Azure solves this with a connection option that makes the route-based gateway present prefix-based traffic selectors to satisfy the policy-based peer, but you have to enable it explicitly and pair it with a custom IPsec policy. The on-premises device must support IKEv2 for this to work, and the connection through a policy-based peer set up this way can reach only the Azure virtual network, not transit to other networks through the same gateway.

```powershell
# Enable prefix-based (policy-based) traffic selectors on a route-based gateway connection
$policy = New-AzIpsecPolicy `
  -IkeEncryption AES256 -IkeIntegrity SHA384 -DhGroup DHGroup24 `
  -IpsecEncryption AES256 -IpsecIntegrity SHA256 -PfsGroup None `
  -SALifeTimeSeconds 14400 -SADataSizeKilobytes 102400000

$conn = Get-AzVirtualNetworkGatewayConnection `
  -ResourceGroupName 'rg-network-prod' -Name 'cn-onprem-policybased'

Set-AzVirtualNetworkGatewayConnection `
  -VirtualNetworkGatewayConnection $conn `
  -IpsecPolicies $policy `
  -UsePolicyBasedTrafficSelectors $true
```

A second form of the selector problem is subtler and survives even between two route-based ends: the address spaces simply do not include the subnets that need to talk. If the Azure local network gateway defines the on-premises address space as a single prefix but the on-premises device expects to reach an Azure subnet that is not in the connection's address scope, the tunnel can connect and still drop the traffic for the missing range. This is where a Connected tunnel that carries some traffic but not all sends people chasing the wrong cause. Confirm the address spaces on both the local network gateway and the on-premises selectors match the subnets that actually need connectivity, and widen them together if they do not. The choice between route-based and policy-based, and when each connectivity model fits, is laid out fully in the comparison of [VNet peering, VPN, and ExpressRoute](/2023/09/04/vnet-peering-vpn-expressroute/), which is the right place to decide the model before you inherit a mismatch.

## Cause five: routing problems over the tunnel

When the connection status is Connected and the byte counters show egress climbing while ingress sits at zero, the tunnel is healthy and the problem is routing. This is the cause most often misdiagnosed as a tunnel failure, because the symptom, traffic not reaching the other side, looks identical to a down tunnel from the application's point of view. The discipline here is to trust the Connected status: phase 1 and phase 2 both succeeded, the IPsec security associations exist, and packets the gateway accepts will be encrypted and sent. If they do not come back, the return path is broken, and the return path lives in route tables and on-premises routing rather than in the IPsec negotiation.

For a static-routing tunnel, the Azure side learns which prefixes to send through the tunnel from the local network gateway's address space, and the on-premises device learns which prefixes to send to Azure from its own route configuration. A missing prefix on either end means traffic to that range never enters the tunnel. The Azure effective routes on the gateway subnet's network interface, and any user-defined routes that might override the gateway-propagated routes, are the first things to read. A UDR that sends the return traffic to a firewall appliance or a different next hop will silently break a tunnel that negotiated perfectly. The interaction between gateway-propagated routes and user-defined routes is exactly the subject of the guide to [Azure route tables and user-defined routes](/2023/12/11/azure-route-tables-udr-explained/), and a routing override is the most common reason a Connected tunnel carries no return traffic.

For a BGP-enabled tunnel, the routing is dynamic, and the failure mode is that BGP does not establish or does not advertise the expected prefixes. A tunnel can be Connected at the IPsec layer while the BGP session over it is down, in which case no routes are learned and no traffic flows even though the encryption is healthy. You read the BGP peer status and the learned and advertised routes directly.

```bash
# Confirm the BGP peer is established and that routes are being learned over the tunnel
az network vnet-gateway list-bgp-peer-status \
  --resource-group rg-network-prod \
  --name gw-hub-vpn \
  --output table

az network vnet-gateway list-learned-routes \
  --resource-group rg-network-prod \
  --name gw-hub-vpn \
  --output table
```

If the peer status shows the session as anything other than connected, the BGP problem is the cause and the IPsec tunnel is a red herring. Common BGP failures are an APIPA address mismatch where the BGP peering addresses on the two ends do not align, an autonomous system number mismatch, or an on-premises device that established the IPsec tunnel but never brought up the BGP peering. The learned routes output tells you whether the Azure side is hearing the on-premises prefixes, and the advertised routes output tells you whether Azure is offering its own. A healthy tunnel with an empty learned-routes table is a BGP problem, not a tunnel problem, and the fix lives in the BGP configuration on both ends rather than anywhere in the IPsec policy.

## Cause six: the tunnel flaps under rekey or dead peer detection

A tunnel that connects, runs cleanly, and then drops on a regular cadence is almost always failing a renegotiation rather than the initial handshake. IPsec security associations have lifetimes, and when a lifetime expires the two ends must rekey, performing the negotiation again to establish fresh keys. If the rekey negotiation fails for the same reason an initial negotiation would fail, but only intermittently, you get the maddening pattern of a tunnel that works for exactly the lifetime interval and then drops. The cadence of the drop is the clue: a disconnect every eight hours points at an 28800 second SA lifetime, and matching the drop interval to a configured lifetime confirms the cause.

Dead peer detection is the second flap mechanism. DPD is a keepalive that lets each end notice when the peer has gone silent and tear down the tunnel so it can be rebuilt. The default DPD timeout on Azure VPN gateways has historically been on the order of tens of seconds, a value worth confirming against the current documentation because it is configurable per connection across a defined range. If an on-premises device sends keepalives on a schedule the Azure side considers too infrequent, or if the underlying internet path has brief outages that exceed the DPD timeout, the tunnel will tear down and rebuild, producing a flap that correlates with path quality rather than with a configured lifetime. The tunnel diagnostic log records each disconnect with a reason, and a DPD-triggered teardown reads differently from a rekey failure, which is how you separate the two.

```kusto
// Find the cadence of disconnects to distinguish a lifetime rekey from a DPD or path flap
AzureDiagnostics
| where Category == "TunnelDiagnosticLog"
| where OperationName == "TunnelDisconnected"
| where TimeGenerated > ago(24h)
| project TimeGenerated, remoteIP_s, stateChangeReason_s
| order by TimeGenerated asc
```

The fix for a rekey flap is to align the SA lifetimes on both ends so the rekey negotiation uses matching parameters, and to ensure the crypto policy that succeeds on the initial handshake is the same one used on rekey. The fix for a DPD or path flap is partly outside Azure: align the DPD timeout to a value both ends tolerate, and address the underlying path instability, which for an internet-based VPN may mean accepting that a consumer-grade or congested link will flap and that a private circuit is the durable answer for a connection that cannot tolerate drops. That trade-off, the moment a VPN's reliance on the public internet becomes the limiting factor, is the decision point that pushes a workload toward a private circuit instead.

## When point-to-site is the one failing

Everything to this point has concerned site-to-site tunnels between two gateways, but a large share of VPN incidents are point-to-site, where individual client machines connect to the Azure gateway rather than a whole on-premises network. Point-to-site uses a different protocol stack, typically an SSL or IKEv2 client tunnel, and it authenticates individual users or devices through certificates or an identity provider rather than a single pre-shared key. The failure modes are correspondingly different, and the diagnostic signal lives in the point-to-site diagnostic log and on the client rather than in the IKE negotiation between gateways.

The most common point-to-site failures are an authentication problem, where the client certificate is not trusted by the gateway or the user is not authorized through the configured identity method, and an address-pool or routing problem, where the client connects but cannot reach the Azure subnets because the routes pushed to the client do not include them. A client that connects and then cannot reach anything is the point-to-site analog of the Connected-but-no-traffic site-to-site case, and the fix is again routing: confirm the address pool does not overlap with the networks the client needs and that the routes advertised to the client cover the target subnets. Certificate failures are confirmed by reading the point-to-site diagnostic log, which records the authentication outcome for each client connection attempt, and the fix is to align the trusted root certificate on the gateway with the client certificate chain or to correct the identity provider configuration.

```kusto
// Point-to-site connection attempts and their authentication outcome
AzureDiagnostics
| where Category == "P2SDiagnosticLog"
| where TimeGenerated > ago(6h)
| project TimeGenerated, OperationName, Message
| order by TimeGenerated desc
```

Treating point-to-site as a separate diagnosis rather than forcing it into the site-to-site model is the key, because the instinct to compare IPsec proposals leads nowhere when the real problem is a certificate that expired or an address pool that overlaps the corporate LAN the client is sitting on.

## The firewall and NAT path: UDP 500, UDP 4500, and ESP

A tunnel that fails with no response from the peer, where a packet capture shows the gateway sending IKE packets into silence, is not a parameter problem at all. The negotiation cannot disagree if the packets never arrive. IKE negotiation uses UDP port 500, and when either end is behind a NAT device the negotiation switches to UDP port 4500 for NAT traversal. The encrypted data itself uses the ESP protocol, IP protocol 50, which is not a UDP or TCP port and which some firewalls and home routers do not forward correctly. If an on-premises firewall blocks UDP 500 or 4500, or fails to pass ESP, the tunnel cannot establish and the symptom is a clean absence of response rather than a rejection.

Confirming this cause is what the packet capture is for. A capture on the Azure gateway that shows outbound IKE on UDP 500 with no inbound reply, combined with an on-premises capture that shows the packets never arriving, localizes the block to the path between them. The fix lives entirely on the on-premises side and its network path: permit UDP 500 and UDP 4500 inbound and outbound to and from the Azure gateway public IP, and ensure ESP is allowed through any device that does deep packet inspection or strict protocol filtering. A NAT device in front of the on-premises gateway that does not handle ESP and NAT traversal cleanly is a frequent cause, and it is why NAT traversal on UDP 4500 exists in the first place. Because this failure presents identically to a few others from the connection status alone, the capture is not optional; it is the only signal that distinguishes a blocked path from a rejected proposal.

## A reproduction you can run to break a tunnel on purpose

The fastest way to internalize the both-ends-must-agree rule is to build a tunnel that works and then break it one clause at a time, watching the diagnostic log change as each clause goes out of alignment. You need a route-based gateway in an Azure virtual network, a local network gateway that describes the remote end, and a connection that ties them together with a shared key and a policy. The remote end can be a second Azure gateway in another region acting as a stand-in for an on-premises device, which lets you control both halves of the negotiation and observe each failure cleanly without touching a production firewall.

Start with a healthy tunnel using an explicit policy on both connections so there is no default ambiguity to confuse the picture. With both ends carrying the identical IKE encryption, integrity, Diffie-Hellman group, IPsec encryption, integrity, PFS group, and lifetimes, the connection reaches Connected and the byte counters begin to climb once you send traffic across it. This is the baseline. Confirm it with the status read and a ping or a small transfer between a virtual machine on each side, and read the IKE diagnostic log to see a clean Main Mode and Quick Mode completion so you know what success looks like in the log before you cause a failure.

Now break phase 1. Change the Diffie-Hellman group on one connection only, leaving everything else identical, and reset the connection so it renegotiates. The status falls to Connecting and stays there, the byte counters stop, and the IKE diagnostic log records a no-matching-policy event during Main Mode. This is the signature of an IKE crypto mismatch, and you have produced it deliberately so the message is familiar the next time a real tunnel shows it. Restore the group, confirm the tunnel recovers, then break phase 2 instead by changing the PFS group on one end alone. This time Main Mode completes in the log and Quick Mode fails, which is the signature that tells you the key and the IKE crypto are fine and the problem is in the IPsec proposal.

Break the key next. With both crypto policies identical again, change the pre-shared key on one connection only. The status returns to Connecting, but the IKE log now records an authentication failure during Main Mode rather than a no-matching-policy message, which is the distinction that separates a key problem from a crypto problem without any further change. Finally, break routing on a Connected tunnel: leave the negotiation correct but remove a prefix from one local network gateway's address space, and watch the tunnel stay Connected while traffic to the removed range stops, with egress climbing and ingress flat on the affected direction. Each of these four breaks maps directly to a row in the InsightCrunch VPN tunnel table, and having caused each one on purpose turns the table from a reference into a reflex.

## The local network gateway and the connection object

A frequent source of confusion is that the Azure side of a site-to-site tunnel is not one resource but three, and a mistake in any of them produces a tunnel failure that is easy to misattribute. The virtual network gateway is the Azure endpoint, the local network gateway is Azure's description of the remote end, and the connection object binds the two and holds the shared key and the IPsec policy. The local network gateway is the resource engineers get wrong most often, because it is where you tell Azure two things that have to be exactly right: the public IP of the on-premises device, and the address prefixes that live behind it.

The remote public IP on the local network gateway has to match the address the on-premises device actually presents to the internet, which is not always the address someone wrote down. A device behind a NAT presents its NAT public IP, not its internal address, and a local network gateway pointed at the internal address will send IKE to an unroutable destination and see no response, producing the blocked-path signature even though no firewall is blocking anything. When the on-premises public IP changes, whether through an ISP change or a failover, the local network gateway must be updated or the tunnel goes dark, and this is a common cause of a tunnel that worked for months and then died with no configuration change on either end except the one nobody made deliberately.

The address prefixes on the local network gateway define what Azure routes through the tunnel for a static-routing connection, and a missing or wrong prefix is the routing failure covered earlier seen from the configuration side. If the on-premises network adds a subnet and nobody adds it to the local network gateway, that subnet becomes unreachable from Azure while the rest of the network works, which looks like a partial tunnel failure but is a stale address description. Reading the local network gateway alongside the connection and the virtual network gateway, as one logical unit rather than three separate resources, prevents the misattribution. The connection object itself holds the connection type, the shared key, the routing protocol choice, and the custom IPsec policy if one is set, and reading it back after any change confirms the change took effect rather than failing silently.

## MTU, MSS clamping, and packet fragmentation over the tunnel

One of the most baffling tunnel symptoms is a tunnel that is Connected and passes small packets perfectly, so a ping succeeds and a simple request works, while large transfers stall or applications hang partway through a response. This is almost never a tunnel negotiation problem and almost always a maximum transmission unit and fragmentation problem. Encapsulating a packet in IPsec adds overhead, which reduces the effective payload size the tunnel can carry without fragmentation. A packet sized for a standard ethernet link can become too large once the IPsec headers are added, and if the do-not-fragment bit is set and the path drops the oversized packet without signaling back, the result is a silent failure that only affects traffic above a certain size.

### Why does my VPN pass pings but stall on large transfers?

This is a maximum transmission unit and fragmentation problem, not a tunnel failure. IPsec encapsulation adds header overhead, so a full-size packet can exceed what the tunnel carries without fragmentation. Small packets like a ping fit, large ones do not, and if the path silently drops oversized packets the transfer stalls. The fix is MSS clamping so endpoints negotiate a payload size that fits the tunnel.

The mechanism that prevents this is maximum segment size clamping, where a device in the path adjusts the TCP MSS value during the connection handshake so the two endpoints agree to send segments small enough to fit through the tunnel after the IPsec overhead. The Azure VPN gateway performs MSS clamping bidirectionally, which handles the TCP case for traffic crossing the gateway, but the symptom can still appear when an on-premises device or an intermediate appliance interferes with the clamping, when the traffic is not TCP and therefore has no MSS to clamp, or when path MTU discovery is broken because an intermediate device drops the ICMP messages that would tell the sender to use smaller packets. Confirming the cause is a matter of testing with deliberately sized packets: a transfer that works below a certain size and fails above it, while the tunnel stays Connected, is the fingerprint. The fix lives in MSS and MTU configuration on the endpoints and the on-premises device, and in ensuring the path does not silently drop the ICMP that path MTU discovery depends on. Because this failure leaves the tunnel Connected and the byte counters moving, it is invisible to the negotiation-focused diagnosis, which is exactly why it is worth knowing as its own cause.

## Gateway SKU, generation, and throughput saturation

A tunnel that is healthy under light load and drops or degrades under heavy load is not failing its negotiation; it is hitting the throughput ceiling of its gateway SKU. The virtual network gateway is provisioned at a specific SKU and generation, and that SKU bounds the aggregate throughput across all of the gateway's tunnels and the number of tunnels and point-to-site connections it supports. A gateway sized for a modest connection that later carries a backup job or a bulk replication can saturate, and the symptom under saturation can look like instability, with degraded throughput, increased latency, and in some cases tunnel resets, rather than a clean negotiation failure.

The diagnostic move is to read the gateway throughput and tunnel metrics in Azure Monitor and correlate the degradation with load rather than with a configured lifetime or a path event. A throughput curve that flattens at the SKU's documented ceiling exactly when the application complains is the confirmation that the gateway, not the tunnel, is the limit. The specific throughput figures and tunnel counts for each SKU and generation are values to confirm against the current official limits at the time you size the gateway, because the SKUs and their published numbers change as new generations are introduced and older ones are retired. The point that does not change is that the SKU is a sizing decision with a real ceiling, and a gateway chosen for the connection's first month can become the bottleneck as the workload grows.

The fix for saturation is to resize the gateway to a SKU with the throughput the workload now needs, which is a different operation from rebuilding it to fix a negotiation, though both involve a maintenance window. The deeper preventive answer is to size the gateway from the expected aggregate throughput across all tunnels rather than from the count of tunnels alone, because two tunnels each carrying heavy replication need more gateway capacity than a dozen tunnels carrying occasional management traffic. When the aggregate throughput a VPN can deliver becomes the constraint, the architecture conversation shifts toward a private circuit with predictable bandwidth, which is the trade-off the connectivity comparison weighs in detail. Reading the metrics before resizing confirms that throughput, not a parameter, is the cause, and it keeps you from resizing a gateway that was never the bottleneck.

## Overlapping address spaces and the addressing design that breaks routing

Some tunnel problems are not tunnel problems or even routing-configuration problems but addressing-design problems that no gateway change can fix. The most consequential is an address space overlap, where the on-premises network and the Azure virtual network use the same private IP range, or two networks joined through a hub use overlapping ranges. Routing depends on each destination prefix being unambiguous, and when the same prefix exists on both sides of a tunnel, a device cannot decide whether a destination in that range is local or across the tunnel, so connectivity breaks in ways that look like a flaky tunnel.

The symptom is selective and confusing: some destinations are reachable and some are not, the pattern depends on which side a given address happens to resolve to, and restarting or rebuilding the tunnel changes nothing because the tunnel is not the problem. Confirming an overlap is a matter of comparing the address ranges on both ends and looking for any range that appears on both, including the ranges learned through peering or other tunnels in a hub-and-spoke design where a spoke's range might collide with an on-premises range reachable through the hub. Once you see the overlap, the cause is settled, because overlapping ranges cannot be routed between without translation.

The fix is an addressing change, not a tunnel change, and it is the most expensive fix in this article because it touches the network design rather than a connection setting. The clean answer is to renumber one side so the ranges no longer overlap, which is disruptive and often resisted but is the only durable resolution. Where renumbering is impossible, network address translation on the path can present one side's overlapping range as a different range to the other, but NAT over a VPN adds complexity and its own failure modes and should be a last resort rather than a first reach. The preventive lesson is to plan the address space across on-premises and Azure as one coherent plan before the first tunnel exists, because an overlap discovered after the fact is far costlier to resolve than one designed out from the start. This is a design decision that belongs to the broader connectivity plan rather than to any single tunnel.

## Defining the tunnel as code for a repeatable configuration

The most durable prevention against drift is to define the gateway, the local network gateway, the connection, and the explicit IPsec policy as code, so the configuration is versioned, reviewed, and reproducible rather than clicked into a portal once and forgotten. When the tunnel is described in a template, a rebuild restores the exact same terms, a change goes through review before it reaches production, and the on-premises configuration can be documented alongside it so both halves of the negotiation live in one place. The pattern is the same whether you use Bicep or Terraform, and the key discipline is to make the IPsec policy explicit in the code rather than relying on a default that each tool or vendor interprets differently.

```hcl
# Terraform: a route-based connection with an explicit, matching IPsec/IKE policy
resource "azurerm_virtual_network_gateway_connection" "onprem" {
  name                       = "cn-onprem-hq"
  location                   = azurerm_resource_group.net.location
  resource_group_name        = azurerm_resource_group.net.name
  type                       = "IPsec"
  virtual_network_gateway_id = azurerm_virtual_network_gateway.hub.id
  local_network_gateway_id   = azurerm_local_network_gateway.onprem.id
  shared_key                 = var.vpn_shared_key

  ipsec_policy {
    ike_encryption   = "AES256"
    ike_integrity    = "SHA256"
    dh_group         = "DHGroup14"
    ipsec_encryption = "AES256"
    ipsec_integrity  = "SHA256"
    pfs_group        = "PFS2048"
    sa_lifetime      = 27000
    sa_datasize      = 102400000
  }
}
```

```bicep
// Bicep: the connection with the same explicit policy so both ends can be aligned to one source of truth
resource onpremConnection 'Microsoft.Network/connections@2023-09-01' = {
  name: 'cn-onprem-hq'
  location: location
  properties: {
    connectionType: 'IPsec'
    virtualNetworkGateway1: { id: hubGateway.id }
    localNetworkGateway2: { id: onpremLocalGateway.id }
    sharedKey: vpnSharedKey
    usePolicyBasedTrafficSelectors: false
    ipsecPolicies: [
      {
        ikeEncryption: 'AES256'
        ikeIntegrity: 'SHA256'
        dhGroup: 'DHGroup14'
        ipsecEncryption: 'AES256'
        ipsecIntegrity: 'SHA256'
        pfsGroup: 'PFS2048'
        saLifeTimeSeconds: 27000
        saDataSizeKilobytes: 102400000
      }
    ]
  }
}
```

The value of expressing the policy in code is that the matching configuration on the on-premises device can be generated or documented from the same source, so the two ends are aligned by construction rather than by a manual transcription that drifts over time. A review of the template catches a mismatched lifetime or a changed group before it reaches a renegotiation, and a rebuild from the template restores a known-good configuration rather than a default. To practice building and tearing down these definitions against a real gateway without risking a production link, the same labs that cover the policy object on [the VaultBook hands-on Azure command library](https://vaultbook.net/tools/azure-labs.html) let you apply a template, observe the negotiation, and confirm the configuration took effect, which is the loop that turns the code pattern into a habit.

## Building a VPN tunnel incident runbook

When a tunnel goes down in production, the cost of the incident is mostly the time spent deciding what to check, so the highest-value preparation is a runbook that fixes the order of checks before the pressure arrives. The runbook encodes the diagnosis this article describes as a sequence anyone on the team can follow, which matters because a tunnel incident often lands on whoever is on call rather than the person who built it. The first step is always the connection status and byte counters, because they split the problem into negotiation, routing, or path in a single read and prevent the most common waste of effort, which is changing crypto settings on a tunnel that is actually Connected.

The second step branches on what the first revealed. A Connecting status sends you to the IKE diagnostic log to identify the failed phase, then to the configuration comparison for that phase's parameters. A Connected status with asymmetric or absent traffic sends you to the effective routes, the BGP peer status if the tunnel uses BGP, and the security rules on the destination. A periodic disconnect sends you to the tunnel diagnostic log to read the disconnect cadence and reason. Each branch ends in a specific check that confirms a specific cause, so the runbook never leaves the responder guessing about what to do with what they found.

The runbook should also fix the things not to do, because under pressure the wrong reflex is as costly as no plan. Do not rebuild the gateway as a first move, because it restates rejected terms and changes the public IP. Do not rotate the pre-shared key on one end as a test, because a one-sided rotation guarantees an outage and proves nothing. Do not change crypto parameters on a Connected tunnel, because the negotiation already succeeded and the problem is elsewhere. A runbook that names the checks in order and names the moves to avoid turns a tunnel incident from an open-ended investigation into a bounded procedure, and pairing it with rehearsed practice on the diagnostic drills means the team has read the same log messages before, in a sandbox, rather than meeting them for the first time during the outage.

## When the answer is a private circuit instead of a VPN

A site-to-site VPN runs over the public internet, and most of the time that is exactly the right trade-off: it is fast to stand up, it costs little, and it carries encrypted traffic well enough for a wide range of workloads. The limit appears when the workload cannot tolerate the variability the public internet introduces. A VPN's throughput is bounded by the gateway SKU and by the internet path, its latency varies with internet conditions, and a tunnel that flaps because the underlying path is unstable cannot be made stable by any configuration change, because the instability is in a path neither end controls. When you find yourself repeatedly diagnosing flaps that trace to path quality rather than to a parameter, the diagnosis has stopped being a tunnel problem and started being an architecture decision.

The decision rule is straightforward once the symptoms point at the path. If the workload needs predictable bandwidth, consistent latency, or traffic that stays off the public internet entirely, the answer is a private circuit rather than a VPN, and the deciding factor is whether the requirement is for reliability and predictability that the public internet cannot guarantee. A VPN remains the right default for connectivity that tolerates internet variability and benefits from low cost and fast setup, and many designs run a VPN as a backup path to a private circuit so that the cheap, flexible option covers the failure of the expensive, predictable one. The full comparison of when each connectivity model fits, including the cost and bandwidth trade-offs that tip the decision, is the subject of the broader connectivity guide, and the private-circuit failure modes have their own diagnosis when the circuit itself goes down. Recognizing that a flap is a path problem rather than a parameter problem is the moment the VPN diagnosis hands off to the architecture decision, and knowing where that handoff sits keeps you from tuning a tunnel that was never going to be stable.

## Diagnosing the path with Network Watcher and effective routes

When the IKE diagnostic log points away from a parameter mismatch and toward a path or routing cause, the next instruments are Network Watcher and the effective routes on the gateway subnet. These tools answer a different question from the IKE log: not whether the two ends agreed on terms, but whether packets can physically reach the gateway and whether Azure knows to send the right prefixes through the tunnel. They are the right reach for a Connected tunnel with asymmetric traffic and for a Connecting tunnel where a capture suggests the packets are not arriving.

The effective routes read is the most direct way to see what Azure will actually do with a packet destined for the remote network. The gateway propagates routes for the tunnel's prefixes into the route tables of the subnets that should use it, and a user-defined route can override those propagated routes with a different next hop. Reading the effective routes on a network interface in the affected subnet shows the merged result of the system routes, the gateway-propagated routes, and any user-defined routes, and a remote prefix that points anywhere other than the virtual network gateway is the smoking gun for a routing override that breaks an otherwise healthy tunnel.

```bash
# Show the effective routes on a NIC to see whether the remote prefix points at the gateway
az network nic show-effective-route-table \
  --resource-group rg-network-prod \
  --name nic-app-vm01 \
  --output table
```

Network Watcher adds the ability to test reachability and to confirm where in the path a packet is being dropped. A connection troubleshoot test from a virtual machine toward an on-premises address tells you whether the traffic reaches the gateway and what happens next, and the IP flow verify check tells you whether a network security group rule would allow or deny a specific flow, which separates an NSG block from a routing problem from a tunnel problem in a single test. When the effective routes are correct and Network Watcher shows the traffic reaching the gateway and entering the tunnel, the problem has moved to the remote side, and the diagnosis hands off to the on-premises routing and firewall. When the effective routes are wrong, you have found the cause without ever touching the tunnel, which is the outcome the both-ends-must-agree rule predicts for a Connected tunnel that carries no traffic. The interaction between propagated routes and user-defined routes, including the precedence rules that decide which wins, is exactly the routing-layer detail that turns an ambiguous symptom into a clear cause.

## The VNet-to-VNet tunnel and its few differences

A VNet-to-VNet connection is a site-to-site tunnel where both ends are Azure virtual network gateways rather than one Azure gateway and one on-premises device. It is the same IPsec and IKE negotiation, governed by the same both-ends-must-agree rule, but it removes the variable that causes the most trouble in a classic site-to-site tunnel, the on-premises device you cannot see. Because both ends are Azure gateways, you can read both halves of the negotiation from the same control plane, compare both connection objects directly, and apply an identical custom IPsec policy to each side with the same tooling, which makes a VNet-to-VNet mismatch faster to diagnose than its cross-premises cousin.

The diagnosis is the same in structure with a smaller search space. A VNet-to-VNet tunnel stuck at Connecting is still a phase 1 or phase 2 problem, read the same way through the IKE diagnostic log on either gateway, but the cause is narrowed because both ends are Azure and therefore support the same algorithm set, which eliminates the legacy-device and version-mismatch causes that complicate a cross-premises tunnel. The pre-shared key still has to match on both connections, the IPsec policy still has to be identical, and a Connected VNet-to-VNet tunnel that carries no traffic is still a routing problem, typically a missing or overridden route or a BGP session that did not establish. The shared key is set on both connection objects, and because both are under your control, a one-sided key is a configuration slip rather than a coordination problem across organizations.

Where VNet-to-VNet differs in practice is in when to use it at all, because peering is often the better tool for connecting two Azure virtual networks. A gateway-based VNet-to-VNet tunnel makes sense when you need transit routing that peering does not provide, when the networks are in different deployment models, or when you specifically want encrypted transit between regions, but for straightforward intra-Azure connectivity, peering is simpler, faster, and does not require a gateway at all. Reaching for a VNet-to-VNet tunnel where peering would serve is a design choice worth revisiting, and the decision between them belongs to the connectivity comparison rather than to a tunnel diagnosis. When you do run one and it fails, the comfort is that both ends are yours to read, which makes the both-ends-must-agree rule trivial to apply.

## Prevention: align both ends once and keep them aligned

The durable fix for VPN tunnel incidents is to remove the ambiguity that lets the two ends drift apart. The single most effective prevention is to define one explicit IPsec and IKE policy that you control, apply it identically to the Azure connection and the on-premises device, and treat that policy as a versioned artifact rather than a set of defaults that each vendor interprets differently. A custom policy on the Azure side, paired with a matching configuration on the on-premises device captured in that device's configuration management, means a rebuild of either end restores the exact same terms rather than whatever the current defaults happen to be.

The second prevention is to enable the diagnostic logs before you need them. A gateway with the tunnel, IKE, and route diagnostic logs streaming to a Log Analytics workspace turns a future incident from an hour of guessing into a two-minute log read, because the proposal mismatch or authentication failure is already recorded the moment it happens. Setting an alert on the tunnel disconnect event so that a flap pages you before a user reports it converts a silent intermittent failure into a known one. The third prevention is to manage the pre-shared key and the key rotation as a coordinated, both-ends operation in your secrets workflow, so that a rotation can never update one end and leave the other behind.

To practice these alignments against tunnels you can configure and break deliberately, you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.net/tools/azure-labs.html), where building a route-based gateway, applying a custom IPsec policy, and reproducing a selector mismatch are exactly the kind of repeatable exercises that make the policy object and the diagnostic logs second nature before a real connection depends on them. Reproducing a failure on purpose, in a sandbox where the stakes are zero, is the fastest way to learn to read its signal under pressure.

## Failures often confused with a down tunnel

Several problems present as a down tunnel and are not. The most common is the routing case already covered, a Connected tunnel that carries no return traffic, which is a route-table or BGP problem wearing a tunnel costume. The second is a DNS problem on top of a healthy tunnel: name resolution across a VPN frequently fails because the on-premises DNS servers are not configured on the Azure virtual network or the conditional forwarders are missing, and the user reports that they cannot reach the on-premises server when in fact the tunnel is fine and only the name lookup fails. Testing connectivity by IP address rather than by name immediately separates a DNS problem from a tunnel problem.

The third confusion is an NSG or on-premises firewall rule that blocks the application traffic after it has traversed a healthy tunnel. The tunnel delivers the packet to the Azure subnet, an NSG on the destination subnet or network interface drops it, and the symptom is a connection that times out as if the tunnel were down. The fifth confusion is a forced-tunneling or default-route surprise, where a user-defined route or a BGP-advertised default sends traffic that should stay local out through the tunnel or out through a firewall, so a destination that has nothing to do with the on-premises network becomes unreachable the moment the tunnel comes up. The tunnel is working exactly as configured, but the routing it introduces captures more traffic than intended, and the symptom is a connectivity change that correlates with the tunnel's state even though the tunnel is healthy. Confirming it is again a matter of reading the effective routes and noticing a default route or an overly broad prefix pointing at the gateway, and the fix is in the route configuration rather than the tunnel. Each of these five confusions shares a tell: the tunnel status is Connected, which means the negotiation succeeded and the cause lives somewhere above the IPsec layer.

## Closing verdict

An Azure VPN gateway tunnel that drops or will not establish is a negotiation that failed, and the discipline that resolves it every time is to find the clause the two ends disagree on rather than to rebuild one of the negotiators. Read the phase first: a Main Mode failure is IKE crypto or the pre-shared key, a Quick Mode failure is the IPsec proposal or the traffic selectors, and a Connected status with no traffic is routing rather than the tunnel at all. Let the IKE diagnostic log tell you whether the failure was a proposal mismatch or an authentication failure, because that one distinction separates a crypto problem from a key problem without a single change. Define one explicit policy, apply it identically to both ends, and the most common failures disappear before they start. The both-ends-must-agree rule is not a slogan; it is the fastest path from a tunnel stuck at Connecting to a tunnel carrying traffic, and it works because a tunnel was never a thing one side owns.

## Frequently Asked Questions

### Q: Why does my Azure VPN tunnel keep disconnecting?

A tunnel that disconnects repeatedly after working is failing a renegotiation rather than the initial handshake. The usual causes are a security association lifetime that triggers a rekey the two ends cannot complete, dead peer detection tearing down an idle or path-disrupted tunnel, a one-sided key rotation, or an unstable internet path beneath the tunnel. The diagnostic move is to read the tunnel diagnostic log and look at the cadence of the disconnects: a regular interval that matches a configured SA lifetime points at a rekey failure, while irregular drops that track network quality point at dead peer detection or path instability. Match the drop interval to a lifetime value to confirm the cause, then align the lifetimes on both ends or address the path. A tunnel that has never connected at all is a different problem, a parameter mismatch present from the first negotiation, and it is diagnosed by reading the failed phase rather than the disconnect cadence.

### Q: Does an IPsec or IKE parameter mismatch bring the tunnel down?

Yes, and a mismatch is the most common reason a new tunnel never reaches Connected. The two ends must agree on every parameter in both phases: the encryption, integrity, and Diffie-Hellman group for IKE phase 1, and the encryption, integrity, and Perfect Forward Secrecy group for IPsec phase 2, plus the security association lifetimes. A single differing value makes the proposal unacceptable, and the negotiation fails with the connection stuck at Connecting. The IKE diagnostic log records a no-matching-policy message during the failed phase and frequently names the offending algorithm or group, with the Diffie-Hellman group and the IKE version being the most common single offenders. The fix is to stop relying on either vendor's defaults, define one explicit policy, and apply the identical encryption, integrity, group, and lifetime values to both the Azure connection and the on-premises device.

### Q: Can a wrong pre-shared key stop the VPN from connecting?

Yes, and a key mismatch is one of the few causes that fails in phase 1 without being a crypto mismatch. The pre-shared key authenticates the two ends during Main Mode, and it must be byte-for-byte identical on the Azure connection and the on-premises device. When it differs, the IKE diagnostic log records an authentication failure rather than a no-matching-policy message, which is precisely how you tell a key problem apart from a parameter problem without changing either setting. The most common real-world causes are mechanical: a trailing space or newline pasted into the key, a character the on-premises device mishandles, or a rotation that updated one end and not the other. Read the key from both ends and compare it as a literal string, then set the identical value on both within a short window, accepting a brief renegotiation drop because two different keys can never both be valid at once.

### Q: How do I tell which side of the VPN tunnel is failing?

Read the phase that failed in the IKE diagnostic log. If Main Mode reports no matching policy, phase 1 failed and the disagreement is in the IKE crypto or the pre-shared key. If Main Mode completed and Quick Mode failed, phase 2 failed and the problem is the IPsec proposal or the traffic selectors. The negotiation is strictly ordered, so a later-phase failure proves everything earlier already agreed, which eliminates causes rather than adding them. For traffic direction, read the connection byte counters: egress climbing with ingress at zero is an asymmetric routing problem on the return path, and both counters at zero with a Connecting status is a negotiation that never completed. When the logs are ambiguous, a packet capture resolves it: outbound IKE with no response means the packets are blocked on the path, while packets in both directions with no completion means the two ends are reaching each other and disagreeing on terms.

### Q: Why do traffic selectors fail between a policy-based and route-based gateway?

A route-based gateway uses wildcard any-to-any traffic selectors and routes traffic into the tunnel based on routing, while a policy-based gateway binds the tunnel to specific source and destination prefixes. When a route-based Azure gateway faces an on-premises device that only does policy-based, prefix-bound tunnels, their selectors structurally disagree and phase 2 fails. The Azure fix is to enable prefix-based traffic selectors on the connection by setting UsePolicyBasedTrafficSelectors to true and pairing it with a complete custom IPsec policy, which makes the route-based gateway present the prefix-based selectors the policy-based peer expects. The on-premises device must support IKEv2 for this to work, and a connection set up this way reaches only the Azure virtual network rather than transiting to other networks. The cleaner long-term answer, where the device supports it, is to use a route-based configuration on both ends and avoid the selector negotiation entirely.

### Q: Why are routes not learned over my VPN when BGP is enabled?

A tunnel can be Connected at the IPsec layer while the BGP session running over it is down, in which case no routes are exchanged and no traffic flows despite healthy encryption. Read the BGP peer status directly; if it shows anything other than connected, BGP is the cause and the IPsec tunnel is a distraction. The frequent BGP failures are a peering-address mismatch where the APIPA or assigned BGP addresses on the two ends do not align, an autonomous system number mismatch, or an on-premises device that brought up the IPsec tunnel but never started the BGP peering. The learned-routes output tells you whether Azure is hearing the on-premises prefixes and the advertised-routes output tells you whether Azure is offering its own; an empty learned-routes table on a Connected tunnel is a BGP problem, not a tunnel problem. The fix lives in the BGP configuration on both ends rather than in any IPsec setting.

### Q: Should I recreate the Azure VPN gateway to fix a tunnel that will not connect?

Almost never, because recreating the gateway restates the same connection terms to an on-premises device that already rejected them. Gateway provisioning is slow, so the rebuild costs you a long wait, and it changes the gateway public IP, which then forces a configuration change on the on-premises device regardless. The both-ends-must-agree rule says to compare the two configurations first: if they disagree on a clause, fix that clause on both ends, and if they agree on everything, the problem is routing or a blocked path rather than the gateway, which a rebuild would not have touched. The only cases where rebuilding genuinely helps are a gateway in a failed provisioning state or a deliberate change of SKU or generation, and even then the connection settings must still match the peer afterward. Reach for the diagnostic logs and a configuration comparison before reaching for delete.

### Q: Why does my VPN tunnel come up but no traffic passes through it?

A Connected status with no traffic means the tunnel negotiated correctly and the problem is above the IPsec layer, almost always routing. Read the byte counters first: egress climbing with ingress at zero is the signature of a broken return path, where Azure is sending but the on-premises side is not sending back. The usual causes are a missing route on either end so traffic to a given prefix never enters the tunnel, a user-defined route that overrides the gateway-propagated routes and sends return traffic to a different next hop, an address space on the local network gateway that does not include the subnet that needs connectivity, or an NSG on the destination interface dropping the application traffic after a healthy tunnel delivered it. Test by IP address rather than by name to rule out DNS, then check the effective routes and the security rules on the destination. The fix lives in routing and filtering, not in the tunnel.

### Q: What does a connection status of Connecting that never reaches Connected indicate?

A status stuck at Connecting means the negotiation has not completed, which points at a parameter mismatch, a pre-shared key problem, or a path that never reaches the peer. The connection status alone cannot distinguish these, so the next step is the IKE diagnostic log. A no-matching-policy message during Main Mode is a phase 1 crypto mismatch, an authentication failure during Main Mode is a wrong key, and a Quick Mode failure after a successful Main Mode is a phase 2 proposal or selector problem. If the log shows the gateway sending proposals with no response at all, the packets are not arriving, which is a firewall or NAT block on UDP 500, UDP 4500, or ESP rather than a disagreement. Reading the byte counters alongside confirms it: both at zero is consistent with a tunnel that never established. Connecting is the state to diagnose by phase, never the state to fix by rebuilding.

### Q: Does a mismatched Diffie-Hellman or PFS group break the tunnel?

Yes, and group mismatches are among the most common single causes of a failed negotiation. The Diffie-Hellman group is negotiated in IKE phase 1 for the key exchange, and the Perfect Forward Secrecy group is negotiated in IPsec phase 2 for the data keys. Different device vendors default to different groups, so two ends left on their defaults can disagree on the group while agreeing on everything else, producing a clean early failure. A PFS mismatch is especially common because PFS is optional: one end can enable it and the other disable it, and the Quick Mode proposals then will not match. The fix is to choose one group setting for each phase and apply it identically on both ends, including the decision to disable PFS on both if your policy permits. The specific supported groups change as weaker options are deprecated, so confirm the current supported set against the official cryptographic requirements when you build the policy.

### Q: How do I read the Azure VPN connection status and gateway diagnostics?

Read the connection status with the CLI or PowerShell rather than the portal, because the command output is scriptable and includes the byte counters that reveal whether traffic has ever crossed the tunnel. The status shows Connecting or Connected, and the egress and ingress counters tell you the traffic direction story. For the negotiation itself, enable diagnostic settings on the gateway to stream the tunnel diagnostic log, the IKE diagnostic log, and the route diagnostic log to a Log Analytics workspace, then query them with KQL. The tunnel log records connect and disconnect events with a reason, the IKE log records the phase 1 and phase 2 negotiation and names proposal mismatches, and the route log records routing changes. When the logs are not conclusive, start a packet capture on the gateway connection to see the IKE exchange on the wire. Enabling these logs before an incident is the difference between a two-minute diagnosis and an hour of guessing.

### Q: Why does my point-to-site VPN client fail to connect when site-to-site works?

Point-to-site is a different protocol stack with different failure modes, so a working site-to-site tunnel tells you little about a point-to-site problem. Point-to-site authenticates individual clients through certificates or an identity provider rather than a single pre-shared key, and its two common failures are authentication, where the client certificate is not trusted by the gateway or the user is not authorized, and routing, where the client connects but the routes pushed to it do not cover the Azure subnets it needs. Read the point-to-site diagnostic log, which records the authentication outcome for each client attempt, to confirm a certificate or identity problem. For the routing case, confirm the client address pool does not overlap the network the client is sitting on and that the advertised routes include the target subnets. Forcing point-to-site into the site-to-site mental model and comparing IPsec proposals leads nowhere when the real cause is an expired certificate.

### Q: Can an on-premises firewall blocking UDP 500 or 4500 stop the tunnel?

Yes, and this failure presents as a clean absence of response rather than a rejected proposal. IKE negotiation uses UDP port 500, and when either end is behind NAT the negotiation switches to UDP port 4500 for NAT traversal, while the encrypted data uses the ESP protocol, IP protocol 50. If an on-premises firewall blocks UDP 500 or 4500, or a device fails to pass ESP, the tunnel cannot establish, and a packet capture on the gateway shows outbound IKE with no reply. The fix lives entirely on the on-premises path: permit UDP 500 and UDP 4500 in both directions to and from the Azure gateway public IP, and ensure ESP passes through any device doing deep packet inspection or strict protocol filtering. A NAT device that does not handle ESP and NAT traversal cleanly is a frequent cause, which is the reason NAT traversal on UDP 4500 exists. Because the symptom mimics a parameter failure, the packet capture is the only signal that confirms a blocked path.

### Q: Why does only one of my two VPN tunnels come up in an active-active gateway?

An active-active gateway presents two instances with two public IPs and establishes two tunnels for resilience, so one tunnel up and one down is a per-tunnel configuration problem rather than a gateway failure. The healthy tunnel proves the crypto policy and the pre-shared key are correct, which means the failing tunnel differs in something specific to its instance: the on-premises device may not be configured for the second Azure public IP, the second local network gateway or peer definition may be missing or wrong, or the on-premises device may not support connecting to both Azure instances. Read each tunnel's status and the IKE log for the failing one independently, treating it as its own negotiation. The fix is usually to add or correct the on-premises configuration for the second Azure instance so both tunnels have a matching peer, which restores the redundancy active-active was deployed to provide.

### Q: Why does the VPN reach some subnets but not others?

Selective reachability over a Connected tunnel is an address-space or routing problem, not a tunnel negotiation problem. The tunnel only carries traffic for the prefixes both ends have agreed to route through it, so a subnet that is missing from the connection's address scope, the local network gateway's defined address space, or the on-premises selectors will be unreachable while the rest of the network works fine. Confirm that the address spaces on both ends include every subnet that needs connectivity, and widen them together where they do not. On a BGP tunnel, the same symptom appears when a prefix is not being advertised or learned, so check the learned and advertised routes for the missing range. An NSG or on-premises firewall rule that blocks one subnet's traffic while allowing another produces the same selective pattern, so check the effective security rules on the unreachable subnet as well before concluding it is purely an addressing issue.

### Q: How do I confirm an IKEv1 versus IKEv2 mismatch is the cause?

An IKE version mismatch fails in phase 1 and looks identical to a crypto mismatch from the connection status, so you confirm it by reading the IKE diagnostic log and checking the configured IKE version on both ends. Azure route-based gateways negotiate IKEv2, and many older or policy-based configurations assume IKEv1, so a device pinned to IKEv1 against a connection expecting IKEv2 never finds common ground in Main Mode. The log will show the negotiation failing early without a successful version agreement, and the on-premises device configuration will reveal which version it is offering. The fix is to align the IKE version, which for a modern route-based gateway means configuring the on-premises device for IKEv2. When IKEv1 and IKEv2 connections coexist on the same gateway, transit between them is handled automatically, but a single connection must settle on one version that both ends speak, and a version mismatch is resolved by configuration rather than by any crypto change.

### Q: What is the fastest order of checks for a VPN tunnel that is down?

Start with the connection status and byte counters, because they split the problem in one read: Connected with traffic is not a tunnel problem, Connected without traffic is routing, and Connecting is a negotiation that never completed. For a Connecting status, read the IKE diagnostic log next and identify the failed phase, because the phase eliminates whole categories of cause: Main Mode failure is IKE crypto or the key, Quick Mode failure is IPsec or selectors. Within Main Mode, a no-matching-policy message is crypto and an authentication failure is the key. For a Connected-without-traffic case, read the effective routes and the BGP peer status, then the NSG rules on the destination. Only when the logs are ambiguous do you run a packet capture to separate a blocked path from a rejected proposal. This order works because each step is cheaper than the next and eliminates more possibilities, which is the opposite of toggling parameters and waiting for renegotiations.
