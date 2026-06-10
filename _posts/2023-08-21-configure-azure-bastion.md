---
layout: post
title: "Set Up Azure Bastion for Secure Access"
page_title: "Set Up Azure Bastion for Secure Access: Configure the AzureBastionSubnet, SKU, NSG Rules, and Browser RDP and SSH Without Public IPs"
date: 2023-08-21
categories: ["Technology"]
tags: ["Azure", "Azure Bastion", "Networking", "Security", "Cloud Computing"]
excerpt: "Set up Azure Bastion for secure browser RDP and SSH access, with the correct AzureBastionSubnet, SKU, and NSG rules so your VMs need no public IP at all."
image: "/assets/images/blog/blog-27.webp"
reading_time: 63
author: "kevin-reeves"
last_updated: 2023-08-21
lang: en
---
Most teams that deploy Azure Bastion think the job is done the moment the resource shows a green checkmark in the portal. It is not. A Bastion that sits next to virtual machines still wearing public IP addresses, with port 3389 and port 22 open to the internet, has changed nothing about the attack surface it was bought to shrink. You have added a managed jump host and paid for it, while the doors it was meant to lock are still propped open. The setup is finished only when the public IPs are gone and the management ports face nothing but your own network.

That gap between deploying Bastion and actually securing access is where this guide lives. Azure Bastion is a managed platform service that gives you remote desktop and secure shell to your machines through the browser, over TLS, without exposing those machines to the public internet. Getting it right means a dedicated subnet with an exact name, a SKU chosen for the features you need, a precise set of network security group rules, and a verification pass that proves the old exposure is closed rather than merely hidden behind a new tool.

![Azure Bastion setup with AzureBastionSubnet, SKU selection, and NSG rules for browser RDP and SSH without public IPs - Insight Crunch](/assets/images/blog/blog-27.webp)

This guide treats the configuration as a single outcome rather than a checklist of clicks. The outcome is the no-public-IP rule: Bastion exists so that your machines need no public IP and no open management port, which means a deployment that leaves either of those in place has not met its own goal. Everything that follows, from the subnet you create first to the public IP you remove last, serves that one measurable result. By the end you will be able to build the service, connect to a machine that has no route from the internet, and confirm with a command that the exposure is genuinely gone.

## What Correct Bastion Configuration Buys, and What Breaks When It Is Wrong

A correctly configured Bastion replaces a whole category of risk. Before it, the common pattern for reaching a virtual machine is a public IP on the machine and an inbound rule allowing 3389 for Windows or 22 for Linux, often scoped to a single office address that drifts out of date the moment someone works from home. That arrangement is the single most scanned and brute-forced entry point in any cloud estate. Internet-wide scanners find an open 3389 within minutes of it appearing, and credential-stuffing against exposed remote desktop is a daily event, not a rare one. Every machine with a public management port is a standing invitation.

Bastion removes the invitation by inverting the model. The browser session you open in the portal terminates on the Bastion host inside your virtual network, and the host then reaches the target machine over its private address using the platform's internal path. The target never needs a public IP, and its network security group never needs an internet-facing management rule. The only thing exposed to the public internet is the Bastion host's own front end on 443, which speaks TLS and sits behind the platform's own protections rather than your machine's bare operating system.

When the configuration is wrong, the failure is usually quiet, which is what makes it dangerous. A Bastion that deploys successfully but reaches nothing because its subnet rules block the internal path leaves engineers connecting through the old public IPs they never removed, and the security posture is worse than before because now there are two ways in and one of them is forgotten. A subnet sized too small refuses the deployment outright, which at least fails loudly. The genuinely hazardous case is the silent one: a working Bastion beside machines that still answer the internet, where the team believes the migration is complete and the audit later shows it was not.

### What does Azure Bastion actually do at a technical level?

Azure Bastion is a fully managed host that lives inside your virtual network and brokers RDP and SSH sessions delivered through the browser over TLS on port 443. The platform runs and patches the host, scales it, and connects to your machines over their private IP addresses, so no target machine requires a public IP or an internet-facing management port.

The mental model that keeps configuration straight is a two-leg connection. The first leg runs from your browser to the Bastion host over HTTPS, encrypted end to end and terminating on the managed service rather than on your machine. The second leg runs from the Bastion host to the target over the private network, using standard RDP or SSH but confined to traffic that originates inside the virtual network. You never speak RDP or SSH across the public internet at any point. The protocol that crosses the internet is HTTPS, and the protocol that reaches your machine never leaves your address space. Holding those two legs separate in your head explains almost every rule you will write later, because each rule governs one leg or the other.

This is why the service needs a home inside your network rather than being a setting you toggle on a machine. The Bastion host is a real set of compute instances that the platform places into a subnet you provide, and those instances need their own address range, their own inbound path from the management plane, and their own outbound path to your machines. The configuration work is mostly about giving those instances exactly the network access they require and nothing more, then proving the targets no longer need any access of their own.

## Prerequisites and the Correct Order of Operations

Bastion configuration fails most often because steps are done in the wrong order, so it helps to fix the sequence before touching anything. You need a virtual network that already contains, or will contain, the machines you want to reach. You need the right role assignments, since creating the host, the subnet, and a public IP for the host touches several resource types. You need to decide on a SKU before deployment because some properties cannot be changed in place later without a redeploy. And you need to know which machines will move off their public IPs, because that removal is the final step that makes the work mean something.

The order that avoids rework is deliberate. First, confirm or create the virtual network and note its address space, because the subnet you add for Bastion must fit inside it without overlapping anything already allocated. Second, create the dedicated subnet with the exact required name and a size large enough for the SKU and the scaling you expect. Third, choose the SKU and create the host, which in most paths also creates or attaches a standard public IP for the host's own front end. Fourth, set the network security group rules on the Bastion subnet and on the target machines so the internal path works and the external path is limited to what the platform needs. Fifth, connect to a target through the browser and confirm the session works end to end. Sixth, and only after a successful connection, remove the public IPs from the targets and delete their internet-facing management rules, then verify the exposure is gone.

Reversing any of these creates a predictable problem. Removing target public IPs before confirming Bastion works locks you out if the host is misconfigured. Creating the subnet after the host is impossible because the host needs the subnet to land in. Choosing the SKU last forces a redeploy when you discover you needed the native client or an IP-based connection that the lower tier does not offer. The sequence is not arbitrary; each step depends on the one before it and prevents a specific failure that teams hit repeatedly.

### Which roles and permissions do I actually need?

You need permissions to create and configure the network resources involved: the virtual network and subnet, a public IP address for the host, the Bastion resource itself, and the network security groups on both the Bastion subnet and the targets. A network contributor role on the resource group, combined with the ability to create the Bastion resource, covers the common case; tighter environments split these across custom roles.

The reason permissions trip people up is that Bastion deployment is a multi-resource operation that looks like a single action in the portal. When you click create, the platform provisions the host, attaches a public IP, validates the subnet, and writes configuration that touches the virtual network. If your role grants Bastion creation but not subnet modification, or public IP creation but not the network changes, the deployment stops partway with an error that names the resource it could not touch rather than the role you are missing. Reading that error backward to the missing permission is straightforward once you know the operation spans several resource types, and confusing before you do. In production you will usually want a custom role that grants exactly these actions and nothing wider, which the official Azure role documentation describes in terms of the specific resource provider operations involved. Treat the exact role names and included actions as values to verify against the current portal, since Azure revises built-in roles regularly.

## Creating the AzureBastionSubnet Correctly

The first concrete step is the subnet, and it carries the rule that breaks the most deployments: the subnet must be named exactly `AzureBastionSubnet`. Not bastion-subnet, not BastionSubnet, not AzureBastion. The platform identifies the subnet that hosts the service by this reserved name, and a subnet with any other name is invisible to the deployment no matter how it is configured. This is a hard requirement, not a convention, and it is the single most common reason a first Bastion attempt fails with a confusing message about a missing subnet when a subnet is plainly present.

The second rule on the subnet is size. The Bastion host needs room for its instances and for the address overhead the platform reserves in every subnet, and it needs additional room if you intend to scale the host to handle many concurrent sessions. The practical guidance has tightened over time: where a smaller range was once accepted for a single small host, a `/26` is the size to plan for so that scaling and newer features have the addresses they need. Provisioning a subnet that is too small produces a clear rejection at deploy time, so this failure is loud rather than silent, but it still costs a redeploy if you guessed low. Size for the SKU and the concurrency you expect, and confirm the current minimum against the official Bastion documentation at the time you build, since the platform has raised this floor before and may again.

Here is the subnet creation in the Azure CLI, assuming the virtual network already exists. The address prefix must fit inside the virtual network's space and must not overlap an existing subnet.

```bash
# Variables
RG="rg-bastion-demo"
VNET="vnet-prod"
LOCATION="eastus"

# Create the dedicated subnet with the EXACT reserved name.
# A /26 leaves room for host scaling and newer SKU features.
az network vnet subnet create \
  --resource-group "$RG" \
  --vnet-name "$VNET" \
  --name AzureBastionSubnet \
  --address-prefixes 10.0.250.0/26
```

If you prefer the portal, the create-a-Bastion wizard offers to add the subnet for you and pre-fills the reserved name, which removes the naming error entirely for a first deployment. The cost of the wizard is less control over the exact address prefix and over whether the network security group is created at the same time, so for repeatable infrastructure the explicit subnet creation above is easier to template and review.

### Why must the subnet be named AzureBastionSubnet?

The platform locates the host's subnet by the reserved name `AzureBastionSubnet`, so the name is functional rather than cosmetic. A subnet with any other name will not be recognized as the Bastion subnet, and the deployment fails reporting that no suitable subnet exists even when one is present, because the one present does not carry the name the service looks for.

Reserved subnet names are a pattern across Azure for services that inject managed infrastructure into your network. Gateways use a reserved name, certain firewall services use reserved names, and Bastion follows the same convention so the platform can find and manage its own footprint without you having to tell it which subnet to use. The practical consequence is that you cannot share this subnet with anything else and cannot rename it after the fact. If you created a subnet under the wrong name, the fix is to create a correctly named one and point the deployment at it, not to rename the existing one, since the platform keys on the name at creation. Plan the address range with this in mind, because the reserved subnet is single-purpose and you should not try to fit other resources into it.

## Choosing the SKU Before You Deploy

The SKU decision matters more than its single dropdown suggests, because it fixes a set of capabilities at deploy time, and moving between some tiers later requires a redeploy rather than an in-place upgrade. The tiers range from a lightweight option suitable for occasional development access through to a tier carrying advanced session features, and each step up unlocks specific functionality rather than simply more of the same. Decide based on how you will connect, not on a guess about scale, because the connection method is what the higher tiers actually change.

The lower tier delivers the core promise: browser-based RDP and SSH to machines that have no public IP, through the portal, over TLS. For a team whose only need is to reach machines occasionally from the portal, this is enough, and paying for more buys features that will sit unused. The higher tier adds the capabilities that change how power users work: connecting with the native Windows or SSH client instead of the browser, connecting to a machine by its private IP address rather than selecting it from the portal, and scaling the host across more instances to carry many simultaneous sessions. There are further tiers that add session recording and the ability to deploy the host without any public front end at all for the most restrictive environments. The exact feature-to-tier mapping is something the platform revises, and tiers have been renamed and re-bundled before, so confirm the current matrix against the official Bastion pricing and SKU documentation rather than trusting a tier name to mean what it meant a year ago.

The redeploy trap is worth stating plainly. If you deploy the lower tier and later discover your team needs the native client or IP-based connection, you generally cannot toggle a setting to gain it; you delete and recreate the host at the higher tier. Because the host carries a public IP and a subnet dependency, that recreation is more than a checkbox, so the cheap insurance is to think through the connection methods your team will need before the first deployment rather than after. If there is any chance you will want the native client, IP-based connection, or significant concurrency, deploy the tier that includes them from the start.

### What do the Bastion SKUs and tiers offer?

Each SKU is a bundle of connection capabilities. The lower tier provides browser RDP and SSH to machines with no public IP. The higher tier adds native client connections, connecting to a machine by its private IP, and host scaling for concurrency. Further tiers add session recording and host deployment without a public front end. Choose by connection method, since some changes need a redeploy.

The scaling dimension deserves its own note because it is the one tied to capacity rather than features. On the tier that supports it, the host runs as a configurable number of scale instances, and that count is what determines how many concurrent sessions the host can carry. A host sized for a handful of administrators will refuse new sessions under a crowd, so a team that expects many simultaneous connections, such as during an incident when a dozen engineers all need into the same environment, should set the instance count to match rather than discovering the ceiling mid-incident. Instance count is adjustable on the supporting tier without a full redeploy, which is one reason the scaling-capable tier is worth choosing when concurrency is plausible, since you can then dial capacity up and down with demand instead of being stuck at a fixed size.

## Deploying the Host

With the subnet in place and the SKU chosen, the host deployment itself is straightforward. The host needs a standard public IP address for its own front end, which is the only public exposure in the entire design, and that IP serves the HTTPS endpoint your browser reaches rather than any of your machines. The deployment associates the host with the virtual network through the reserved subnet, attaches the public IP, and provisions the managed instances. It takes several minutes because real compute is being placed and configured, not because anything is wrong.

Here is the end-to-end deployment in the CLI, creating the public IP and then the host. The SKU is set explicitly so the capability set is intentional rather than defaulted.

```bash
# Standard public IP for the Bastion host's own front end.
# This is the ONLY public IP in the design; targets get none.
az network public-ip create \
  --resource-group "$RG" \
  --name pip-bastion \
  --sku Standard \
  --location "$LOCATION" \
  --allocation-method Static

# Create the Bastion host. Set the SKU deliberately.
# --sku Standard unlocks native client, IP-based connection, and scaling.
az network bastion create \
  --resource-group "$RG" \
  --name bastion-prod \
  --vnet-name "$VNET" \
  --public-ip-address pip-bastion \
  --location "$LOCATION" \
  --sku Standard
```

The public IP must be a standard SKU and statically allocated, which the command above sets explicitly. A basic-SKU or dynamically allocated address will be rejected, so if a deployment complains about the public IP, that mismatch is the first thing to check. Once the command returns, the host exists, but it secures nothing yet, because the targets still have their own public IPs and rules. The next two steps, the network security group rules and the removal of target exposure, are what convert a deployed host into a closed perimeter.

## The Network Security Group Rules Bastion Requires

This is the step where deployments that look healthy quietly fail to work, so it rewards precision. If you place a network security group on the `AzureBastionSubnet`, and many environments require one by policy, you must allow the specific traffic the host needs in both directions, because an NSG that denies the host's own management and data paths will leave you with a host that deploys but cannot broker a session. The platform documents an exact set of rules, and the safest approach is to write them deliberately rather than to leave the subnet without an NSG and hope policy never forces one on later.

The required rules separate cleanly along the two-leg model from earlier. The inbound rules govern what reaches the host: HTTPS on 443 from the public internet for the browser sessions, HTTPS on 443 from the platform's gateway manager so the management plane can reach the host, traffic from the platform load balancer on 443 for health, and the host's internal data-plane ports from within the virtual network so the host instances can coordinate. The outbound rules govern where the host can go: RDP and SSH to the virtual network so it can reach your machines, HTTPS to the Azure cloud for session logging and dependencies, the internal data-plane ports back into the virtual network, and an outbound path the host uses for session management. Each rule maps to a leg of the connection: the external inbound rules serve the browser-to-host leg, and the outbound RDP and SSH rules serve the host-to-machine leg.

The findable artifact for this section is the InsightCrunch Bastion NSG rule map, which pairs each required rule with the reason it exists, so you can read any rule and know which part of the connection it serves and what breaks if you omit it.

| Direction | Source / Destination | Port | Why it exists | Symptom if missing |
|-----------|---------------------|------|---------------|--------------------|
| Inbound | Internet (or your client range) | 443 | Browser reaches the host over TLS | Portal cannot open a session at all |
| Inbound | GatewayManager | 443 | Control plane manages the host | Host unhealthy or unmanageable |
| Inbound | AzureLoadBalancer | 443 | Health probes reach the host | Host marked unhealthy, sessions fail |
| Inbound | VirtualNetwork (host data ports) | 8080, 5701 | Host instances coordinate | Multi-instance host fails internally |
| Outbound | VirtualNetwork | 3389, 22 | Host reaches target VMs | Connects to portal but VM never opens |
| Outbound | AzureCloud | 443 | Session logging and dependencies | Sessions drop or diagnostics break |
| Outbound | VirtualNetwork (host data ports) | 8080, 5701 | Host instances coordinate | Multi-instance host fails internally |

The exact ports, the service tags, and whether some rules are required or merely recommended are details the platform has adjusted over time, particularly the internal data-plane ports, so treat the table as the structure to verify against the current official Bastion NSG guidance rather than as eternal port numbers. The structure, the two-leg logic, and the symptom-to-rule mapping hold even when a specific port changes. Here is the same set expressed as CLI rules on an NSG attached to the Bastion subnet, written so each rule's purpose is legible.

```bash
NSG="nsg-bastion"

# --- Inbound ---
# Browser sessions from clients over TLS.
az network nsg rule create -g "$RG" --nsg-name "$NSG" \
  --name AllowHttpsInbound --priority 120 --direction Inbound \
  --access Allow --protocol Tcp --source-address-prefixes Internet \
  --destination-port-ranges 443 --destination-address-prefixes '*'

# Control plane reaches the host.
az network nsg rule create -g "$RG" --nsg-name "$NSG" \
  --name AllowGatewayManagerInbound --priority 130 --direction Inbound \
  --access Allow --protocol Tcp --source-address-prefixes GatewayManager \
  --destination-port-ranges 443 --destination-address-prefixes '*'

# Health probes from the platform load balancer.
az network nsg rule create -g "$RG" --nsg-name "$NSG" \
  --name AllowAzureLoadBalancerInbound --priority 140 --direction Inbound \
  --access Allow --protocol Tcp --source-address-prefixes AzureLoadBalancer \
  --destination-port-ranges 443 --destination-address-prefixes '*'

# Host instance coordination.
az network nsg rule create -g "$RG" --nsg-name "$NSG" \
  --name AllowBastionHostCommunication --priority 150 --direction Inbound \
  --access Allow --protocol '*' --source-address-prefixes VirtualNetwork \
  --destination-port-ranges 8080 5701 --destination-address-prefixes VirtualNetwork

# --- Outbound ---
# Reach target machines over RDP and SSH inside the VNet.
az network nsg rule create -g "$RG" --nsg-name "$NSG" \
  --name AllowSshRdpOutbound --priority 100 --direction Outbound \
  --access Allow --protocol '*' --source-address-prefixes '*' \
  --destination-port-ranges 22 3389 --destination-address-prefixes VirtualNetwork

# Session logging and platform dependencies.
az network nsg rule create -g "$RG" --nsg-name "$NSG" \
  --name AllowAzureCloudOutbound --priority 110 --direction Outbound \
  --access Allow --protocol Tcp --source-address-prefixes '*' \
  --destination-port-ranges 443 --destination-address-prefixes AzureCloud

# Host instance coordination outbound.
az network nsg rule create -g "$RG" --nsg-name "$NSG" \
  --name AllowBastionCommunicationOutbound --priority 120 --direction Outbound \
  --access Allow --protocol '*' --source-address-prefixes VirtualNetwork \
  --destination-port-ranges 8080 5701 --destination-address-prefixes VirtualNetwork
```

### What NSG rules does Bastion require on its subnet?

If you attach an NSG to the Bastion subnet, allow inbound 443 from clients, 443 from the gateway manager, 443 from the load balancer, and the host data ports from the virtual network; allow outbound 3389 and 22 to the virtual network, 443 to the Azure cloud, and the host data ports. Each rule serves either the browser leg or the machine leg.

A point that catches teams is the target machine's own NSG, which is separate from the Bastion subnet's. The machine you connect to needs an inbound rule allowing 3389 or 22 from the Bastion host's path, which in practice means allowing those ports from the virtual network or from the Bastion subnet's range, not from the internet. This is the rule that replaces the old internet-facing management rule. You are not removing remote access to the machine; you are changing where that access may originate, from anywhere on the internet to only inside your own network by way of the host. Getting this backward, by deleting the management rule entirely rather than re-scoping it to the virtual network, produces a Bastion that connects to the portal and then times out reaching the machine, which is the single most common post-deployment symptom and almost always this rule.

## Connecting Through the Browser and the Native Client

Once the host is healthy and the rules are in place, connecting is the part that finally demonstrates the value. From the portal, you select the target machine, choose to connect through Bastion, supply credentials, and a session opens in a browser tab. The machine has no public IP, you opened no port to the internet for it, and yet you have a full remote desktop or shell. The session is delivered over the HTTPS connection to the host, and the host speaks RDP or SSH to the machine privately, which is the two-leg model made concrete.

For Windows targets, the browser session gives a full desktop with clipboard support, and for Linux targets it gives a shell, both rendered in the browser without any client software installed locally. This is the capability that makes Bastion usable from a locked-down workstation or a tablet, since the only requirement on your side is a browser and the portal. For SSH to Linux machines you can supply a password, a private key from your local machine, or a key stored in Key Vault, which keeps the key off disk and under access control rather than pasted into a session.

On the tier that supports it, the native client extends this. Instead of the browser, you connect through the Azure CLI, which tunnels RDP or SSH to the target over the host, letting you use the full native client experience including features the browser cannot offer, such as file transfer in some configurations and multi-monitor remote desktop. The native client connection looks like this for RDP and for SSH respectively.

```bash
# Native client RDP through Bastion (Standard SKU and above).
# Opens the local RDP client tunneled through the host.
az network bastion rdp \
  --name bastion-prod \
  --resource-group "$RG" \
  --target-resource-id "/subscriptions/<sub>/resourceGroups/$RG/providers/Microsoft.Compute/virtualMachines/vm-win"

# Native client SSH through Bastion.
az network bastion ssh \
  --name bastion-prod \
  --resource-group "$RG" \
  --target-resource-id "/subscriptions/<sub>/resourceGroups/$RG/providers/Microsoft.Compute/virtualMachines/vm-linux" \
  --auth-type ssh-key \
  --username azureuser \
  --ssh-key ~/.ssh/id_rsa
```

The IP-based connection, also a higher-tier feature, lets you reach a machine by its private IP rather than selecting it from the portal's resource list. This matters when the target is not a first-class virtual machine resource the portal can enumerate, such as a machine reached across a peered network or a device that presents only an address. Without IP-based connection you are limited to targets the portal can list; with it, anything reachable on the private network by address is in range, which is what makes the higher tier worthwhile for hybrid and peered topologies.

### How do I RDP or SSH through Bastion in the browser?

From the portal, open the target machine, choose Connect and then Bastion, and enter credentials; a session opens in a new browser tab over TLS with no client install and no public IP on the machine. For SSH you can supply a password, a local private key, or a key held in Key Vault for tighter control.

The credential handling is worth a closer look because it is where convenience and security meet. For Windows, you supply the local or domain account at connect time, and Bastion passes it to the RDP session; the credentials travel inside the encrypted session rather than over an exposed port. For Linux, the Key Vault option is the one to prefer in a managed environment, since it means the private key never sits on the connecting workstation and access to the key is governed by the vault's own access policy and audit trail. A team that standardizes on Key Vault-stored keys for Bastion SSH gets a clean story for who can reach which machine, enforced by vault permissions rather than by who happens to have a key file, and that story is far easier to audit than scattered key files on individual laptops.

## Removing the Public IPs, the Step That Finishes the Job

Everything to this point has built the secure path. This step closes the insecure one, and skipping it is the difference between a Bastion that looks deployed and a Bastion that actually changed your exposure. With a confirmed working session through the host, you now remove the public IP from each target machine and delete or re-scope the internet-facing management rules that allowed 3389 and 22 from outside. Until this is done, both paths exist, the old one is still scannable, and you have spent money to add a tool without subtracting the risk it was meant to remove.

The removal has two parts per machine. First, dissociate and delete the public IP so the machine has no internet-routable address at all. Second, ensure the machine's network security group no longer allows management ports from the internet, which it should not need to once the IP is gone but which should be removed explicitly so a future public IP cannot accidentally reopen the exposure. Here is the removal for a single machine.

```bash
# Dissociate the public IP from the VM's NIC, then delete it.
NIC="vm-win-nic"
az network nic ip-config update \
  --resource-group "$RG" \
  --nic-name "$NIC" \
  --name ipconfig1 \
  --remove publicIpAddress

az network public-ip delete \
  --resource-group "$RG" \
  --name vm-win-pip

# Remove any internet-facing management rule from the VM's NSG.
az network nsg rule delete \
  --resource-group "$RG" \
  --nsg-name nsg-vm-win \
  --name AllowRdpFromInternet
```

After the IP is gone, the machine is reachable only through Bastion, which is the entire point. The machine still has its private IP and still answers RDP or SSH on the private network, so the host can reach it, but nothing on the internet can. If you skipped the earlier verification and the IP removal locks you out, the recovery is to reattach a public IP temporarily, fix the Bastion path, confirm a session works, and then remove the IP again, which is exactly why the order of operations puts the working-session check before the removal. Never remove the last public path before you have proven the new one.

### How does Bastion let me drop public IPs on VMs?

Bastion reaches your machines over their private IP addresses from inside the virtual network, so a machine no longer needs a public IP to be reachable for management. Once a Bastion session is confirmed working, you delete the public IP and the internet-facing 3389 or 22 rule, and the machine becomes reachable only through the host.

The verification that the removal worked is as important as the removal itself, because believing a port is closed is not the same as confirming it. From outside the network, attempt to reach the old public IP on 3389 or 22; the attempt should fail to connect rather than refuse, because there should be no address answering at all. A simple connectivity probe from any machine outside Azure, or a port scan of the formerly exposed address, should show the port closed or the host unreachable. Inside Azure, the effective security rules on the machine's NIC should show no inbound allow for the management ports from the internet. Confirming both, the dead public address and the absent internet rule, is what lets you write in the change record that the exposure is gone rather than that Bastion was deployed.

## The Settings the Defaults Get Wrong

Several Bastion defaults are reasonable for a first look and wrong for production, and knowing them ahead of time saves a round of rework. The default deployment through the portal wizard often creates the smallest viable configuration, which is fine for a test and short for real use. The defaults worth reconsidering cluster around scale, SKU, and the network security group.

The instance count on a scaling-capable host defaults low, sized for a single administrator rather than a team, so a host left at the default will refuse sessions the first time several engineers connect at once. If the environment will ever see concurrent access, set the instance count to match the realistic peak rather than the default, and remember that on the supporting tier this is adjustable later without a full redeploy, so erring slightly high and tuning down is cheaper than being caught short during an incident. The SKU default may also be lower than your eventual needs, and since some capabilities require a redeploy to gain, the default tier is a decision to make consciously rather than accept silently.

The network security group is the subtlest default. A Bastion subnet created without an NSG works, because the platform's own internal protections cover the host, but many organizations have policy that automatically applies an NSG to every subnet, and that policy-applied NSG will not contain the rules Bastion needs unless you put them there. The result is a Bastion that worked yesterday and stops working when a governance policy applies a restrictive NSG overnight. The defensive move is to attach the correct NSG yourself from the start, with the rules from the artifact above, so that no later policy can replace an open subnet with a closed one and break the host without warning.

### Which Bastion defaults should I change for production?

Raise the instance count above the single-administrator default if a team will connect concurrently, choose the SKU deliberately rather than accepting the lowest tier since some features need a redeploy, and attach the correct NSG to the Bastion subnet yourself so a later governance policy cannot apply a restrictive one that breaks the host.

There is a quieter default around diagnostics that matters for any environment with an audit requirement. Session logging and diagnostic settings are not all on by default, and a Bastion that brokers administrative access without recording who connected to what and when is missing the audit trail that justifies it to a security team. Turning on diagnostic settings to send Bastion logs to a Log Analytics workspace, and on the tier that supports it enabling session recording, converts the host from a convenient access tool into an accountable one. The configuration to route Bastion diagnostics is the same pattern as any other resource's diagnostic settings, and pairing it with the access controls already discussed gives a complete picture of who reached which machine and what the session contained.

## Verifying the Configuration Worked

Verification is not a single check but a short sequence that proves each layer is doing its job, and running it turns a hopeful deployment into a confirmed one. The sequence walks the connection from the outside in, then confirms the old path is dead.

Start by confirming the host itself is healthy in the portal, since an unhealthy host points at the inbound NSG rules or the public IP SKU before anything else. Then open a session to a target through the browser and confirm the desktop or shell appears, which proves the browser-to-host leg and the host-to-machine leg both work and the outbound RDP and SSH rules are correct. Then, separately, attempt to reach a target's former public address from outside Azure and confirm the connection fails, which proves the exposure removal worked. Each step isolates one part of the system, so a failure tells you exactly where to look rather than leaving you guessing across the whole configuration.

The effective security rules view is the tool that makes verification precise rather than impressionistic. On a target machine's network interface, the effective rules show the combined result of every NSG applied at the subnet and the interface, which is what actually governs traffic regardless of what any single rule looks like in isolation. Checking the effective rules on a target confirms that inbound management is allowed from the virtual network and denied from the internet, in one view, without having to reason about rule precedence by hand. This is the same diagnostic that resolves most connectivity confusion in Azure networking generally, and it is worth knowing well, which the walkthrough of [how to diagnose an NSG that blocks traffic unexpectedly](/2022/11/21/fix-nsg-blocking-traffic/) covers in detail.

```bash
# Show the effective security rules on a target VM's NIC.
# Confirm: management ports allowed from VirtualNetwork, denied from Internet.
az network nic list-effective-nsg \
  --resource-group "$RG" \
  --name vm-win-nic \
  --output table
```

### How do I confirm Bastion is set up correctly?

Confirm the host shows healthy in the portal, open a working browser session to a target with no public IP, and then verify from outside Azure that the target's former public address no longer accepts a connection. Check the effective security rules on the target's NIC to confirm management is allowed from the virtual network and denied from the internet.

The reason to verify from genuinely outside Azure, rather than from another Azure resource, is that traffic between Azure resources can take internal paths that do not represent what the public internet sees. A probe from your laptop on a home or office network, or from a machine in an entirely different cloud, tests the path an attacker would actually use. If that external probe cannot reach the old port, and the effective rules confirm the internet is denied, the configuration has met its goal in the only terms that matter, which is the perspective of the network the threat comes from rather than the network you trust.

## Common Misconfigurations and Their Symptoms

The failures teams hit with Bastion are a small, repeatable set, and recognizing each by its symptom turns a frustrating debug into a quick lookup. These are the patterns that account for the large majority of Bastion problems, each with the setup step that prevents it.

The misnamed subnet is the first deployment killer. A subnet named anything other than `AzureBastionSubnet` is invisible to the deployment, which fails reporting no suitable subnet despite a subnet being present. The symptom is a creation error that mentions the subnet at the moment of host deployment; the fix is to create a correctly named subnet and the prevention is to use the exact reserved name from the start, ideally through a template that cannot typo it.

The undersized subnet is the second. A subnet too small for the host and its scaling overhead is rejected at deploy time with a message about address space. This one fails loudly, so it costs time rather than security, and the prevention is to size for a `/26` so scaling and newer features have room, confirming the current minimum against the official documentation since the floor has risen before.

The missing NSG rules are the third and most insidious, because the host deploys successfully and then cannot broker sessions. The symptom splits by which rules are missing: missing inbound 443 rules leave the host unhealthy or unreachable from the portal, while missing outbound RDP and SSH rules let the portal session start and then time out reaching the machine. The split symptom is diagnostic: an unhealthy host points inbound, a healthy host that cannot reach the target points outbound. The prevention is the rule artifact above, applied deliberately.

The target machine's own rule is the fourth, and it is the most common post-deployment complaint. A machine whose NSG does not allow management ports from the virtual network refuses the host's connection even when the Bastion subnet's rules are perfect, producing a session that connects to the portal and then fails to open the machine. The fix is the re-scoped management rule allowing 3389 or 22 from the virtual network rather than the internet, which is the same connectivity logic that the guide to [diagnosing an NSG that blocks traffic unexpectedly](/2022/11/21/fix-nsg-blocking-traffic/) works through for the general case, since a Bastion-to-target failure is an NSG problem wearing a different hat.

The leftover public IP is the fifth, and it is the one that defeats the purpose silently. A deployment that works perfectly while leaving target public IPs and internet management rules in place has added a tool without removing the exposure, and the symptom is not an error at all but a security finding weeks later when an audit notices machines still answering the internet. This is exactly the exposure that the SSH connection refused failure and the RDP connection error are both symptoms of when public access is the access path, and Bastion is the structural fix that the troubleshooting guides for [a refused SSH connection](/2022/06/06/fix-azure-vm-ssh-connection-refused/) and [a failed RDP connection](/2022/05/30/fix-azure-vm-rdp-connection-error/) both point toward as the way to stop fighting the exposed port and remove it instead. The prevention is the verification sequence: prove the new path, then close the old one, then confirm it is closed.

The SKU mismatch is the sixth. A team that deployed the lower tier and then needs the native client, IP-based connection, or significant concurrency discovers the capability is not a setting they can enable, and the symptom is a missing feature rather than an error. The fix is a redeploy at the higher tier, and the prevention is the SKU decision made before the first deployment with the team's real connection methods in mind.

### Why does Bastion connect to the portal but fail to reach the VM?

The browser session reaching the portal but timing out on the machine means the host-to-target leg is broken, almost always the target's own NSG. The Bastion subnet rules can be perfect while the target machine's NSG lacks an inbound allow for 3389 or 22 from the virtual network. Add that re-scoped rule and the session opens.

## Making the Configuration Repeatable as Code

A Bastion built by clicking through the portal is fragile in the way all hand-built infrastructure is fragile: it cannot be reviewed, it cannot be reproduced identically in another environment, and a change made in a hurry leaves no record. The configuration described here maps cleanly to infrastructure as code, and expressing it as a template is what makes it durable. The template encodes the reserved subnet name so it cannot be mistyped, the SKU so it is chosen deliberately, the NSG rules so they cannot drift, and the whole arrangement so a second environment is identical to the first by construction rather than by careful copying.

Here is the core of a Bicep template that creates the subnet, the public IP, the network security group with the required rules, and the host. It is abbreviated to the structure that matters; a production template would parameterize the address ranges, the location, and the SKU.

```bicep
@description('Existing VNet name')
param vnetName string
param location string = resourceGroup().location
param bastionName string = 'bastion-prod'
param bastionSku string = 'Standard'

resource vnet 'Microsoft.Network/virtualNetworks@2023-04-01' existing = {
  name: vnetName
}

resource bastionNsg 'Microsoft.Network/networkSecurityGroups@2023-04-01' = {
  name: 'nsg-bastion'
  location: location
  properties: {
    securityRules: [
      {
        name: 'AllowHttpsInbound'
        properties: {
          priority: 120
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: 'Internet'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '443'
        }
      }
      {
        name: 'AllowGatewayManagerInbound'
        properties: {
          priority: 130
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: 'GatewayManager'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '443'
        }
      }
      {
        name: 'AllowSshRdpOutbound'
        properties: {
          priority: 100
          direction: 'Outbound'
          access: 'Allow'
          protocol: '*'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: 'VirtualNetwork'
          destinationPortRanges: [ '22', '3389' ]
        }
      }
      {
        name: 'AllowAzureCloudOutbound'
        properties: {
          priority: 110
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: 'AzureCloud'
          destinationPortRange: '443'
        }
      }
    ]
  }
}

resource bastionSubnet 'Microsoft.Network/virtualNetworks/subnets@2023-04-01' = {
  parent: vnet
  name: 'AzureBastionSubnet'
  properties: {
    addressPrefix: '10.0.250.0/26'
    networkSecurityGroup: {
      id: bastionNsg.id
    }
  }
}

resource bastionPip 'Microsoft.Network/publicIPAddresses@2023-04-01' = {
  name: 'pip-bastion'
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
  }
}

resource bastion 'Microsoft.Network/bastionHosts@2023-04-01' = {
  name: bastionName
  location: location
  sku: {
    name: bastionSku
  }
  properties: {
    ipConfigurations: [
      {
        name: 'bastionIpConfig'
        properties: {
          subnet: {
            id: bastionSubnet.id
          }
          publicIPAddress: {
            id: bastionPip.id
          }
        }
      }
    ]
  }
}
```

The template makes the reserved name a literal that the deployment enforces, removes the chance of an undersized subnet by fixing the prefix, and bundles the NSG rules with the host so the two cannot drift apart. Parameterizing the SKU lets you promote a configuration from a development tier to a production tier through a pipeline rather than a redeploy by hand. This is the same discipline the broader VNet design benefits from, and the deep dive on [how the virtual network and its subnets fit together](/2022/02/28/azure-virtual-network-vnet-deep-dive/) explains why pinning the subnet model in a template pays off across every networking service, not just Bastion.

### Should I deploy Bastion through a template or the portal?

Use the portal for a one-off test where the wizard's pre-filled reserved subnet name removes the easiest mistake. Use a template for anything you will keep, since the template encodes the reserved name, the subnet size, the SKU, and the NSG rules so they cannot drift, and reproduces an identical host in a second environment by construction.

The version-control benefit compounds over time. A Bastion expressed as a template lives in the same repository as the rest of the environment, changes to it go through review, and the history shows who changed the SKU or the rules and when. When a security team asks why a particular NSG rule exists on the Bastion subnet, the answer is a commit with a reviewer and a reason rather than a shrug. Pairing the template with a pipeline that deploys it on change closes the loop, so the running Bastion always matches the reviewed template and configuration drift, the slow divergence between what is documented and what is real, never gets a chance to start.

## Scaling Bastion for Many Concurrent Sessions

Capacity is the dimension teams most often discover late, usually during an incident when a crowd of engineers all need into the same environment and the host refuses sessions past a low ceiling. The scaling-capable tier addresses this directly through the instance count, which sets how many host instances back the service and therefore how many concurrent sessions it can carry. The relationship is direct: more instances, more simultaneous sessions, and a host left at its low default will hit the wall exactly when the pressure is highest.

Sizing the instance count is a planning decision rather than a guess if you reason from the realistic peak. A platform team supporting a large estate during a major incident might see a dozen or more engineers connecting at once, while a small team's peak is two or three. Set the count for the peak you can foresee, knowing that on the supporting tier the count adjusts without a full redeploy, so the cost of setting it slightly high is small and the cost of setting it too low is a refused session during an emergency. The instance count also interacts with the subnet size, which is part of why the `/26` matters: a host scaled to many instances needs the addresses, and a subnet sized for a single small host cannot grow into a large one without a redeploy.

The configuration to set the instance count is a property on the host, adjustable after deployment on the supporting tier. Pair the scaling decision with the diagnostic and session-logging configuration discussed earlier, because a host that carries many sessions during an incident is exactly the host whose access record you will most want afterward. Scaling for capacity and logging for accountability are two halves of preparing Bastion for the moment it matters most, which is rarely the quiet day and usually the bad one.

### How many Bastion instances do I need?

Set the instance count to your realistic concurrent-session peak: a couple of instances for a small team, more for a platform team that sees many engineers connect at once during incidents. On the scaling-capable tier the count adjusts without a redeploy, so size for the foreseeable peak and tune from there rather than accepting the low default.

## A Worked End-to-End Setup, Narrated

It helps to see the whole sequence run once as a single story, because the individual commands above hide how the steps depend on one another in practice. Picture a subscription with a production virtual network at `10.0.0.0/16` holding a Windows machine and a Linux machine, both currently carrying public IP addresses and both with internet-facing management rules that a security review has just flagged. The goal is to reach both through a managed broker and to retire those public addresses, and the work proceeds in the order that prevents lockout.

The first move is to carve out the address space the broker will live in. The virtual network already uses `10.0.0.0/24` and `10.0.1.0/24` for the two machine subnets, so a free `/26` at `10.0.250.0/26` sits well clear of them. Creating the reserved subnet at that prefix gives the service a home that will not collide with anything and that has room for the instances a scaled deployment will eventually want. With the subnet created under its exact reserved name, the deployment that follows can find it.

The second move is to decide how the team connects before committing to a tier. This team has two power users who prefer the native Windows remote desktop client over a browser tab and a hybrid topology where some machines sit across a peering, so the IP-based connection matters. Those two needs point at the higher tier, and choosing it now avoids the painful discovery later that the lower tier cannot do either. The host gets created at that tier with a standard, statically allocated public IP for its own TLS endpoint, and several minutes pass while the platform places the compute.

The third move is the network security group, written before the first connection attempt so the host can actually broker a session. The team's governance policy attaches an NSG to every subnet automatically, so leaving the Bastion subnet bare is not an option; an empty-but-policy-managed NSG would arrive later and break everything. Writing the inbound 443 rules for clients, the gateway manager, and the load balancer, plus the outbound management and cloud rules, gives the host the exact access it needs. On the target machines, the existing internet-facing management rules stay in place for now, because removing them before a working session is proven would be the lockout the order of operations exists to prevent.

The fourth move is the proof. Opening the portal, selecting the Windows machine, choosing to connect through the broker, and entering credentials produces a desktop in a browser tab. The Linux machine, connected with a key held in Key Vault, produces a shell. Both sessions reached machines that still have public IPs, but they reached them over the private path, which proves the host-to-target leg works through the new NSG rules. Only now is it safe to change the targets.

The fifth move is the removal that gives the work meaning. With both sessions confirmed, the public IP comes off the Windows machine's interface and is deleted, the internet-facing remote desktop rule is dropped, and the same happens for the Linux machine and its secure shell rule. The machines keep their private addresses and still answer the broker, but nothing on the public internet can reach them. The sixth and final move is verification from outside Azure: a connection attempt to each former public address on the management port, from a laptop on a home network, fails to connect because no address answers, and the effective rules on each interface confirm the internet is denied and the virtual network is allowed. The change record can now say the exposure is gone, with the evidence to back it.

### What does a complete Bastion migration look like in practice?

A complete migration creates the reserved subnet, deploys the host at a deliberately chosen tier, writes the NSG rules on the subnet and re-scopes the management rules on the targets, proves a working session to each machine, then deletes the public IPs and internet rules and verifies from outside Azure that the old ports no longer answer. The host running is the start, not the finish.

The narrated sequence also exposes the single most common reason a migration stalls halfway: the team proves the session, feels the work is done, and never circles back to remove the public IPs. The deployment looks complete, the broker works, and the original exposure quietly persists for weeks until an audit finds it. Building the removal and the external verification into the same change ticket as the deployment, as non-optional steps rather than follow-up tasks, is the discipline that closes this gap. A useful framing for the team is that deploying the host is the easy eighty percent and removing the exposure is the twenty percent that was the actual point, so the ticket is not closeable until the external probe fails.

## Running One Central Bastion Across a Hub-and-Spoke Network

Most real estates are not a single virtual network with a few machines; they are a hub-and-spoke topology where a central hub network holds shared services and many spoke networks hold workloads. Deploying a separate broker in every spoke would be wasteful and would multiply the cost, so the pattern that scales is one central host in the hub serving machines across all the spokes. This is where the higher tier's IP-based connection stops being a convenience and becomes a requirement, since machines in a spoke are not always first-class resources the portal can enumerate from the hub's perspective, and reaching them by private address is what makes the central model work.

The mechanics rest on peering and routing rather than on anything special about the broker. A host in the hub can reach a machine in a spoke when the hub and spoke are peered, the peering allows forwarded traffic, and the routing carries the management ports between the two networks. The broker does not bypass these network controls; it relies on them, which means a central deployment is only as reachable as the peering and routing allow. A spoke that is peered but whose peering blocks the traffic, or whose route table sends the return path somewhere unexpected, will refuse the central host's connection in exactly the way a misconfigured NSG would, and the diagnosis is the same family of network reasoning.

The payoff of the central model is operational and financial at once. One host to deploy, patch, scale, and audit, instead of one per spoke, collapses the management surface dramatically. One audit trail captures every administrative session into every spoke, instead of a scattered set of per-spoke logs nobody correlates. And the cost of a single scaled host in the hub is far below the cost of many small hosts duplicated across spokes, which matters because the host bills continuously whether or not anyone is connected. For an estate of any size, the central host in the hub is the design that the topology naturally wants.

### Can one Bastion serve machines in multiple spoke networks?

A single host in the hub can serve machines across peered spokes when the peering allows forwarded traffic and the routing carries the management ports, and the higher tier's IP-based connection lets you reach those machines by private address. This central model replaces a wasteful per-spoke deployment with one host to manage, audit, and pay for, which is the design a hub-and-spoke topology naturally favors.

There is a routing subtlety worth flagging for the central model, because it catches teams who assume peering alone is enough. When a spoke routes its traffic through a network virtual appliance or a firewall in the hub, the path from the central host to a spoke machine and back may not be symmetric, and asymmetric routing can break the session even when every NSG rule is correct. The fix is to ensure the return path from the spoke machine to the host follows the same route the forward path took, which usually means accounting for the broker's subnet in the route tables that steer spoke traffic. Reasoning about which route a packet takes, separately from which rule filters it, is the core networking skill that makes this kind of problem tractable, and it is the same separation of routing from filtering that underlies almost every connectivity question in Azure.

## Keeping Bastion Cost-Conscious

Because the host bills for as long as it exists rather than only while sessions run, cost discipline with the broker is mostly about not paying for capacity you are not using. The continuous-billing model is the first thing to internalize: a host deployed into a development environment that sees a connection twice a month is a steady monthly charge for a service that sits idle most of the time, and that idle cost is pure waste. The levers that control spend are the tier, the instance count, and the number of hosts, and pulling each one deliberately keeps the bill matched to the value.

The tier lever is the largest. The higher tiers cost more than the lower one for every hour they run, so a tier chosen for features the team does not use is an ongoing overpayment. The honest question for each environment is which connection methods it genuinely needs: an environment whose only access is occasional browser-based administration does not need the tier that adds the native client and IP-based connection, and paying for that tier there is a recurring leak. The discipline is to match the tier to the environment's real access pattern rather than standardizing every environment on the highest tier for uniformity, because uniformity here is uniformly overpaying.

The instance-count lever matters on the scaling-capable tier, where capacity costs money. A host scaled to many instances to survive an incident crowd carries that capacity, and its cost, continuously, even on quiet days. Because the count adjusts without a redeploy on the supporting tier, a team can size for the realistic baseline and scale up only when a known busy period approaches, then scale back down, which keeps the average cost near the baseline rather than pinned at the peak. The host-count lever is the central-deployment point from the previous section: one scaled host in a hub serving many spokes costs far less than many small hosts, so consolidating onto a central broker is itself a cost optimization, not only an operational one.

### How do I keep Azure Bastion costs under control?

Match the tier to each environment's real access pattern rather than standardizing on the highest tier, since the host bills continuously whether or not it is used. On the scaling tier, size the instance count to the baseline and raise it only for known busy periods. Consolidate onto one central host in the hub instead of many small hosts across spokes, which the topology favors anyway.

A lightweight option exists for the development case where even a continuously billed standard host feels heavy. A lower-footprint deployment mode aimed at occasional development access trades away the dedicated subnet and some features for a much lighter cost and operational profile, suitable for a developer who needs a quick browser session into a machine now and then without standing up a full host. The trade-off is real: it lacks the scaling, the native client, and the advanced features of the standard tiers, so it fits the casual case and not the production one. Confirm the current capabilities and constraints of this lighter mode against the official documentation, since it is a newer option whose feature set and availability the platform is still shaping, and treat it as the answer to the idle-development-host cost problem rather than as a general replacement for a properly sized standard deployment.

## Fitting Bastion Into an Access-Control Posture

The broker is a network control, and a network control on its own is only half of a secure access story; the other half is identity, deciding who is allowed to open a session at all and under what conditions. The host removes the public attack surface, but it does not by itself decide that only certain people, from certain devices, at certain times, may reach a given machine. Pairing the network control with identity controls is what turns a tool that removes exposure into a complete access posture that also governs use.

Access to open a session flows from role assignments rather than from any setting inside the broker, which means you grant the ability to connect by assigning the appropriate roles on the target machine and the broker resource, and you withhold it by not assigning them. Scoping these roles narrowly, so a person can reach only the machines their work requires, is the principle of least privilege applied to administrative access, and it is far stronger than the old model where anyone who could reach the public IP and guess or steal a credential was in. Layering Key Vault-held SSH keys on top, with the vault's access policy governing who may retrieve the key, adds a second gate: permission to open the session and permission to obtain the key it needs are separate grants, and a person needs both.

The conditions under which a session may open are the domain of conditional access, the identity control that evaluates signals like the user, the device state, the location, and the sign-in risk before allowing the access the role permits. A session into a production machine through the broker is a sign-in to the platform, and conditional access can require multi-factor authentication for it, block it from unmanaged devices, or restrict it to known locations, which means the network control and the identity control reinforce each other. The deeper treatment of how to design these policies belongs to the dedicated configuration material on conditional access, but the pairing principle is simple: the broker decides the path, identity decides the permission, and the two together decide who reaches what and how.

### How do I control who can open a Bastion session?

Grant access through role assignments on the target machine and the broker resource, scoping them narrowly so each person reaches only the machines their work needs, and layer Key Vault-held keys so opening a session and obtaining its key are separate grants. Add conditional access to require multi-factor authentication or restrict sessions by device and location, so the network path and the identity permission reinforce each other.

The accountability half of the posture is the logging discussed earlier, and it completes the picture. A complete access posture can answer three questions for any administrative session: who was permitted to open it, under what conditions it was actually opened, and what happened inside it. Role assignments answer the first, conditional access and its sign-in records answer the second, and diagnostic logging with session recording on the supporting tier answers the third. A team that wires all three gets an access model where reach is granted deliberately, use is conditioned on real-time signals, and every session is recorded, which is the standard a security review of privileged access is looking for and which a bare public IP could never provide. Building this posture incrementally, starting with the network control the broker provides and adding the identity and logging layers as the environment matures, is a reasonable path that does not require everything at once but does require knowing where it is headed.

## Reading a Bastion Failure Quickly

When a deployment misbehaves, the fastest path to the cause is to ask one question first: did the host deploy and report healthy, or not? That single split sends you down one of two short branches, and following the right branch saves the scattershot checking that turns a five-minute fix into an afternoon. The branch logic is the named diagnostic for this guide, the InsightCrunch Bastion failure split, and it works because the symptoms cluster cleanly by which leg of the connection broke.

If the host did not deploy at all, the cause sits in the subnet or the public IP, because those are what the deployment validates before it provisions anything. A creation error mentioning the subnet means the reserved name is wrong or the range is too small, and the cure is a correctly named subnet sized to a `/26`. A creation error mentioning the public IP means the address is the wrong SKU or dynamically allocated, and the cure is a standard, statically allocated address. These two account for nearly every failure that stops the deployment before a host exists, and both fail loudly with a message that names the offending resource, so the message itself points at the branch.

If the host deployed but reports unhealthy, the cause sits in the inbound path, because health depends on the platform reaching the host and the host answering. The inbound 443 rules from the gateway manager and the load balancer are what let the control plane manage the host and the probes confirm it is alive, so a missing inbound rule leaves a deployed host that cannot report healthy. This branch is the one teams reach when a governance policy has applied a restrictive NSG to the subnet without the required allows, which is why attaching the correct NSG yourself at creation forecloses it.

If the host is healthy but a session connects to the portal and then fails on the machine, the cause sits in the outbound path or the target's own NSG, because the browser leg clearly works and the machine leg clearly does not. An outbound rule missing on the subnet blocks the host from reaching the management ports, and far more commonly, the target machine's NSG lacks an inbound allow for the management port from the virtual network. The split within this branch is itself diagnostic: if no target works, suspect the subnet's outbound rules; if one specific target fails while others succeed, suspect that machine's own NSG. This is the most frequent post-deployment symptom and almost always the target's re-scoped management rule.

### How do I tell which part of a Bastion setup is broken?

Ask whether the host deployed and is healthy. A deployment that never completed points at the subnet name, the subnet size, or the public IP SKU. A deployed but unhealthy host points at the inbound 443 rules. A healthy host whose session times out on the machine points at the outbound rules or, most often, the target machine's own NSG missing an allow from the virtual network.

The decision path also tells you where not to look, which is half its value during a stressful debug. A team that does not know the split will check the target's NSG when the host is unhealthy, which is wasted effort because an unhealthy host cannot reach any target regardless of the target's rules. They will check the subnet name when a single machine fails while others work, which cannot be the cause because a wrong subnet name fails the whole deployment, not one connection. Letting the symptom select the branch, and trusting the branch to exclude the irrelevant checks, is what makes the diagnosis fast. Pair this with the effective-rules view on a failing target and a health check on the host, and most problems resolve to a specific missing rule within a few minutes.

## When Bastion Is Not the Right Choice

A clear-eyed setup guide should say where the tool does not fit, because deploying it everywhere by reflex wastes money and adds management for no gain. The continuous-billing model is the crux: a broker that bills for every hour it exists is poorly matched to an environment that needs administrative access a handful of times a year, where the steady cost dwarfs the value. For those rare-access environments, a lighter approach, whether the low-footprint development mode or a just-in-time access pattern that opens a port only for a brief approved window, can be the more sensible answer, and forcing a full standard host into that situation is the kind of uniformity that quietly drains a budget.

The tool is also not a fit when the access need is broad connectivity into a network rather than administrative sessions to specific machines. A developer who needs to reach many services, databases, and internal endpoints across a network is describing a VPN's job, not a broker's, and trying to serve that need through browser sessions to individual machines is a poor substitute. The clean division is that a VPN extends the network to the client so many things become reachable, while the broker gives clean, auditable administrative sessions to particular machines without a jump box or an open port. An estate often wants both, each doing its own job, and reaching for one to do the other's work produces friction in daily use.

Finally, the tool does not absolve the rest of the security model. Removing the public management port is a large and real improvement, but a machine reachable only through the broker is still a machine that can be compromised through its application, its patches, or a stolen credential that the broker happily passes through. The broker narrows one important door; it does not harden the room behind it. Treating its deployment as the completion of machine security, rather than as the removal of one specific and severe exposure, is a mistake that leaves the other doors unwatched. The honest framing is that it does one thing extremely well, and that one thing is worth doing, while the rest of the posture, patching, application security, identity, and monitoring, remains exactly as necessary as before.

### Is deploying Bastion always the right move?

No. Its continuous billing makes it a poor fit for environments needing access only a few times a year, where a lighter just-in-time pattern costs less. It also does not replace a VPN's broad connectivity, and it hardens only the management path, not the application, the patching, or the identity behind it. Deploy it where regular administrative access justifies a steady cost, and pair it with the rest of the security model.

## The Verdict

Azure Bastion is worth deploying, and it is worth deploying correctly, which are two different statements. The service genuinely removes the most-scanned entry point in a cloud estate, the public management port, and replaces it with a brokered, encrypted, auditable path that needs no public IP on any machine. That value is real, and it is also conditional: it exists only when the configuration follows through to the end, which means the reserved subnet named exactly right and sized for growth, the SKU chosen for the connection methods the team actually uses, the network security group rules written deliberately on both the Bastion subnet and the targets, and, above all, the removal of the public IPs and internet management rules that the host was bought to replace.

The no-public-IP rule is the standard to hold the work to. A Bastion deployment is complete not when the host shows healthy but when an external probe of every former public address fails to connect and the effective rules confirm the internet is denied. Measure the work by that result and the configuration becomes hard to get wrong, because every step has a clear purpose and the final state is verifiable rather than assumed. To build and break this in a safe environment before you do it in production, you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) and deploy a Bastion, connect to a machine with no public IP, and watch the old exposure disappear, which is the fastest way to internalize the sequence before it counts.

The broader lesson the series keeps returning to applies here in full: the platform rewards verifying the goal, not the deployment. A green checkmark proves a resource exists; it does not prove the resource achieved what you bought it for. The discipline of checking the outcome, the dead external address and the denied internet rule, against the intention, secure access without exposure, is what separates an estate that is genuinely safer from one that merely looks busier. Carry that habit from this configuration into the next, and the work compounds.

## Frequently Asked Questions

### Q: How do I set up Azure Bastion for secure access end to end?

Set up Azure Bastion in a fixed order so the steps do not undo each other. First confirm the virtual network that holds your machines. Second create a dedicated subnet named exactly `AzureBastionSubnet`, sized to a `/26` so it has room to scale. Third choose the SKU based on whether you need the native client, IP-based connection, or concurrency, since some of those require a redeploy to add later, then create the host with a standard static public IP for its front end. Fourth attach the required NSG rules to the Bastion subnet and allow the management ports from the virtual network on the target machines. Fifth open a browser session and confirm it works. Sixth, only after a confirmed session, remove the public IPs and internet management rules from the targets and verify externally that the old ports no longer answer. The configuration is complete at step six, not at deployment.

### Q: Why does Bastion need a subnet named AzureBastionSubnet specifically?

The platform identifies the subnet that hosts the service by the reserved name `AzureBastionSubnet`, so the name is a functional requirement rather than a label you choose. A subnet under any other name is invisible to the deployment, which then fails reporting that no suitable subnet exists even though a subnet is plainly present, because the present one does not carry the name the service searches for. This mirrors how other managed services that inject infrastructure into your network, such as gateways, use reserved subnet names so the platform can find and manage its own footprint. The practical consequences are that the subnet is single-purpose, cannot host anything else, and cannot be renamed after creation; if you used the wrong name, you create a correctly named subnet rather than renaming the existing one. Plan the address range knowing the subnet is dedicated entirely to Bastion.

### Q: What size should the AzureBastionSubnet be?

Plan for a `/26` so the host has room for its instances, the platform's reserved address overhead, and the scaling and newer features the higher SKUs offer. A smaller range was accepted historically for a single small host, but the practical floor has tightened, and provisioning a subnet too small produces a clear rejection at deploy time rather than a silent failure, so the cost of guessing low is a redeploy. Because the subnet cannot be resized trivially once the host is in it, sizing for growth at creation is cheaper than discovering the limit when you try to scale the host across more instances. Confirm the exact current minimum against the official Bastion documentation at the time you build, since the platform has raised this floor before and the safe value to plan around is the larger one.

### Q: What is the difference between the Bastion SKU tiers?

The tiers are bundles of connection capability rather than degrees of the same thing. The lower tier delivers the core promise of browser RDP and SSH to machines with no public IP, through the portal, over TLS, which is enough for occasional portal-based access. The higher tier adds the native client, so you connect through your local RDP or SSH client tunneled over the host; the IP-based connection, so you reach machines by private IP rather than selecting them from the portal; and host scaling, so the instance count carries many concurrent sessions. Further tiers add session recording and the ability to deploy the host with no public front end for the most restricted environments. Choose by how your team will connect, because moving between some tiers requires a redeploy rather than an in-place change, and the exact feature mapping is something to verify against the current SKU documentation since it has been re-bundled before.

### Q: Do I need a network security group on the Bastion subnet?

You do not strictly need one for the host to function, because the platform's own internal protections cover the host, but you almost always want one and should plan for the rules regardless. Many organizations run a governance policy that automatically attaches an NSG to every subnet, and a policy-applied NSG without the Bastion rules will break the host when it lands. The defensive approach is to attach the correct NSG yourself from the start, with inbound rules allowing 443 from clients, the gateway manager, and the load balancer plus the host data ports from the virtual network, and outbound rules allowing the management ports to the virtual network, 443 to the Azure cloud, and the host data ports. Doing this proactively means no later policy can replace an open subnet with a closed one and silently disable your host overnight.

### Q: Why does Bastion connect to the portal but then time out reaching the VM?

A session that reaches the portal and then fails on the machine has a broken host-to-target leg, which is almost always the target machine's own NSG rather than the Bastion subnet's rules. The Bastion subnet rules can be perfect, the host healthy, and the browser session open, yet the connection to the machine times out because the machine's NSG lacks an inbound allow for 3389 or 22 from the virtual network. The fix is the re-scoped management rule: allow the relevant management port from the virtual network or the Bastion subnet's range rather than from the internet. This rule replaces the old internet-facing management rule you removed; you are not blocking management access, you are confining where it may originate. Once the rule allows the port from inside the network, the host's connection succeeds and the session opens.

### Q: How do I connect to a Linux VM through Bastion using an SSH key?

You have three credential options for SSH through Bastion, and the choice matters for security. You can type a password, supply a private key file from your local machine at connect time, or reference a key stored in Azure Key Vault. The Key Vault option is the one to prefer in a managed environment, because the private key never sits on the connecting workstation and access to it is governed by the vault's access policy and audit trail rather than by who happens to have a key file. In the portal you select the Key Vault and the secret holding the key during the connect dialog. With the native client on the supporting tier you pass the key through the CLI command. Standardizing on Key Vault-held keys gives a clean, auditable answer to who can reach which machine, enforced by vault permissions rather than scattered local files.

### Q: Can I use Bastion to reach a VM in a peered virtual network?

You can, and the IP-based connection on the higher tier is what makes it practical. A Bastion host in one virtual network can reach machines in a peered network as long as the peering allows the traffic and the routing is in place, and the IP-based connection lets you target a machine by its private address rather than selecting it from the portal's resource list, which is necessary when the target is across a peering or is not a first-class resource the portal enumerates. The lower tier, limited to portal-listed targets in the host's own network, generally cannot do this, which is one of the clearest reasons to choose the higher tier for a hub-and-spoke topology where one central Bastion serves machines across many spokes. Confirm the peering and routing carry the management ports between the networks, since Bastion does not bypass those network controls.

### Q: How much does Azure Bastion cost to run?

Bastion bills on a combination of the host running and the data it transfers, and the host charge accrues as long as the host exists rather than only while sessions are open, which surprises teams who expect a per-session model. The higher tiers cost more than the lower one, and the scaling-capable tier's cost rises with the instance count you configure, so a host scaled for high concurrency costs more than one sized for a small team. Because the host bills continuously, a Bastion deployed and forgotten in a rarely used environment is a steady cost for little value, and one pattern teams use is to keep Bastion only in environments with regular access need and reach occasional ones another way. Treat the specific rates as values to verify against the current Azure pricing page at the time you plan, since pricing and tier bundling change and the host-running model means the monthly figure depends on tier and scale rather than usage alone.

### Q: Can I deploy Bastion without giving the host a public IP?

The standard tiers require a standard public IP for the host's own front end, which is the only public exposure in the design and serves the HTTPS endpoint your browser reaches rather than any of your machines. For environments that cannot tolerate any public IP at all, a higher tier offers a deployment mode without a public front end, intended for the most restricted networks where access comes entirely through private connectivity. This is a deliberate higher-tier capability rather than a setting on the standard tiers, so if a no-public-IP host is a hard requirement, choose the tier that supports it from the start, since adding the capability later means a redeploy. For most teams the host's single standard public IP is acceptable because it exposes only a TLS endpoint behind the platform's protections, not a machine's operating system, which is the exposure Bastion exists to remove.

### Q: What NSG rules do I put on the target VM, not the Bastion subnet?

The target machine needs exactly one management rule, and it is a re-scoping rather than an opening. Allow inbound RDP on 3389 for Windows or SSH on 22 for Linux from the virtual network, or more tightly from the Bastion subnet's address range, and deny it from the internet. This rule lets the host reach the machine privately while ensuring nothing on the public internet can. The mistake teams make is deleting the old internet-facing management rule and adding nothing in its place, which leaves the machine unreachable even from the host and produces a session that opens in the portal and then times out. The correct change keeps management access alive but confines its origin to inside your network, which is the entire shift Bastion enables: the same port, reachable only from where you control rather than from anywhere.

### Q: How do I verify that removing the public IP actually closed the exposure?

Verify from genuinely outside Azure, because traffic between Azure resources can take internal paths that do not reflect what the public internet sees. From your own laptop or a machine in a different network, attempt to reach the target's former public address on the management port and confirm the connection fails with no host answering, which is the result you want once the public IP is deleted. Inside Azure, check the effective security rules on the target's network interface, which show the combined result of every applied NSG and confirm management is allowed from the virtual network and denied from the internet. Confirming both, the dead external address and the absent internet rule, is what lets you record that the exposure is gone rather than that Bastion was deployed. The external probe is the one that matters most, since it tests the path an attacker would actually take.

### Q: Why does my Bastion host show as unhealthy?

An unhealthy host points at the inbound path before anything else, since health depends on the platform reaching the host and the host answering. The usual causes are an NSG on the Bastion subnet that blocks the required inbound 443 traffic from the gateway manager or the load balancer, or a public IP that is not a standard SKU or not statically allocated, both of which the platform requires. Check the inbound rules first: the gateway manager rule lets the control plane manage the host, and the load balancer rule lets health probes reach it, so missing either leaves the host unable to report healthy. Then confirm the public IP is standard and static, since a basic or dynamic address is rejected. A host that is unhealthy rather than merely unable to reach a target is an inbound or public IP problem, which narrows the search considerably compared to a healthy host that cannot open a machine.

### Q: Can I restrict who can use Bastion to reach which machines?

You control access through role assignments rather than through Bastion itself, since the right to open a Bastion session to a machine flows from permissions on the machine and the Bastion resource. Granting a user the ability to connect requires the appropriate reader and login roles on the target machine and the permission to use the Bastion resource, so you scope access by assigning those roles narrowly rather than broadly. Combined with Key Vault-held SSH keys, whose access the vault policy governs, this gives a layered control: who may open a session at all, and who may retrieve the key the session needs. Pairing this with diagnostic logging that records who connected to what and when produces an auditable access model where reach is granted deliberately and every use is recorded, which is the accountability a security team expects from a tool that brokers administrative access.

### Q: Does Bastion replace a VPN or a jump box VM?

Bastion replaces the self-managed jump box pattern cleanly and overlaps partially with a VPN, so the answer depends on what you are solving. A hand-built jump box, a VM with a public IP that administrators connect to and then hop from, is exactly what Bastion replaces with a managed, patched, auditable equivalent that needs no public IP of its own beyond a TLS front end. A VPN solves a broader problem, extending your network to a client so many services become reachable, while Bastion solves the narrower problem of administrative access to specific machines through the browser. Teams often run both: a VPN for general connectivity and Bastion for clean, auditable RDP and SSH without managing a jump box or opening management ports. If your only need is browser-based administrative access to machines without public IPs, Bastion alone is the simpler and more secure choice than maintaining a jump box VM.

### Q: How do I enable session logging and recording for Bastion?

Session logging and recording are configured through diagnostic settings and the supporting tier rather than being on by default, and a Bastion that brokers administrative access without an audit trail is missing the accountability that justifies it. Turn on diagnostic settings on the Bastion resource to route its logs to a Log Analytics workspace, using the same pattern as any other resource's diagnostics, so you capture who connected and when. On the tier that supports session recording, enable it to capture the session content itself, which a security team may require for privileged access. Pairing logging with the role-based access controls that govern who may open a session gives a complete record: the access was granted to a named principal, used at a recorded time, and on the recording tier, captured in full. Configure this as part of the initial setup rather than after an incident, when the missing logs are the problem.

### Q: What is the correct order to deploy Bastion to avoid rework?

The order matters because each step depends on the previous one and prevents a specific failure. Confirm the virtual network first, since the subnet must fit inside it. Create the `AzureBastionSubnet` second with the exact name and a `/26` size, since the host needs the subnet to land in. Choose the SKU and create the host third with a standard static public IP, since the SKU fixes capabilities that may need a redeploy to change. Apply the NSG rules fourth on both the subnet and the targets, since the host cannot broker sessions without them. Confirm a working browser session fifth, before changing anything on the targets. Remove the public IPs and internet management rules sixth, only after the new path is proven, then verify externally. Reversing any step creates a predictable problem, most dangerously removing target public IPs before confirming Bastion works, which can lock you out.
