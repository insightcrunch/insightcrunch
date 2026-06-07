---
layout: post
title: "Azure Key Vault Security Best Practices"
page_title: "Azure Key Vault Security Best Practices: RBAC, Private Endpoints, Purge Protection, Rotation, and Auditing"
date: 2024-01-15
categories: ["Technology"]
tags: ["Azure", "Key Vault", "Security", "Identity", "Cloud Computing"]
excerpt: "Azure Key Vault security best practices to harden a vault with RBAC, network lockdown, soft delete, purge protection, secret rotation, and access auditing."
image: "/assets/images/blog/blog-02.webp"
reading_time: 60
author: "Insight Crunch Team"
last_updated: 2024-01-15
---

A key vault holds the material that protects everything else: the connection strings that reach your databases, the certificates that terminate your TLS, the keys that encrypt your storage accounts. When the vault is hardened, a stolen application credential buys an attacker very little, because the vault still gates what that credential can read. When the vault is left on defaults, the same vault becomes the single richest target in the subscription, and one over-broad role assignment or one open network path turns it into a master key for the estate. Azure Key Vault security best practices exist to close that gap on purpose rather than by accident.

The exposure is rarely a flaw in the vault itself. It is the posture around the vault. A vault that still uses the legacy access policy model lets anyone with a Contributor-style write permission grant themselves data-plane access. A vault reachable from the public internet trusts the network boundary to no one. A vault without purge protection can be deleted, secrets and all, by a single mistaken command or a malicious insider, and the encrypted data those secrets unlocked goes dark with it. None of these are exotic. They are the defaults or the legacy settings that a vault carries forward when nobody hardens it deliberately.

This article walks the full hardening posture for a production vault and names the rule that ties it together. The organizing principle is what we will call the rbac-network-and-recovery rule: a hardened vault uses RBAC for access, restricts the network, and enables soft delete with purge protection, because those three controls close the most common Key Vault exposures at once. Around that rule sits the InsightCrunch Key Vault hardening checklist, a step-by-step reference you can run against any vault to find the gap and the fix. Everything else in this article supports those two artifacts: how each control works, how to configure it correctly, how to verify the result, and how to make the whole posture auditable and repeatable so it does not drift back to defaults the next time someone provisions a vault in a hurry.

If you have not yet built a mental model of the service itself, the [Azure Key Vault complete guide](/2022/03/07/azure-key-vault-complete-guide/) lays out the keys, secrets, and certificates the vault stores and the control-plane and data-plane split that the rest of this discussion assumes. This article picks up where that one ends, treating the vault as a thing to defend rather than a thing to learn.

## How Key Vault access actually works

Every hardening decision starts with one fact: access to a vault runs through two separate planes, and they are authorized differently. Understanding that split is what turns a checklist into reasoning. The control plane is where you manage the vault as an Azure resource. Creating the vault, deleting it, reading its properties, configuring its firewall, and changing its access model all happen on the control plane, and they are authorized by Azure role-based access control through Azure Resource Manager. The data plane is where the actual secrets, keys, and certificates live. Reading a secret value, signing with a key, and importing a certificate all happen on the data plane, and that plane can be authorized one of two ways.

The first way is the legacy access policy model, native to the vault itself. The second is Azure RBAC for the data plane, the model Microsoft now recommends and the one that anchors the access half of the rbac-network-and-recovery rule. Both planes authenticate through Microsoft Entra ID, so the identity story is consistent; the difference is entirely in how that authenticated identity is granted permission to act.

### Why does the two-plane split matter for security?

It matters because a permission on one plane does not imply permission on the other, and the gap between them is where over-privilege hides. Someone can hold a control-plane write permission, never touch a secret value, and still grant themselves data-plane access under the legacy model. Closing that path is the first hardening move.

The legacy access policy model is where the most common and most dangerous misconfiguration sits. Under access policies, permissions are assigned at the level of the whole vault. You grant a principal the ability to get and list secrets, and that principal can now read every secret in the vault, not a chosen subset. There is no scoping to an individual secret. Worse, the right to set those access policies travels with any control-plane role that includes the write permission on the vault resource. A user with a broad Contributor assignment, or a Key Vault Contributor role, can open the access configuration and grant themselves full data-plane access, because configuring an access policy is a control-plane operation that their write permission already covers. The security boundary you thought you had is not a boundary at all; it is a suggestion that any vault writer can override on their own behalf.

Azure RBAC for the data plane closes that path. With RBAC, data-plane permissions are granted through role assignments that follow the same model as every other Azure resource: a security principal, a role definition, and a scope. The scope is the lever that changes the security picture. Instead of granting access to the entire vault, you can assign the Key Vault Secrets User role on a single secret, and that principal can read that one secret and nothing else. The right to hand out those assignments no longer travels with a generic write permission either. Granting RBAC access requires the Owner or User Access Administrator role, which separates the act of managing the vault from the act of granting access to its contents. That separation is the security gain. A platform engineer who manages vault infrastructure no longer automatically holds the keys to its data.

RBAC carries other advantages that compound over a real estate. It is a unified model, so the same role assignment APIs, the same audit trail, and the same tooling you use for storage accounts and virtual machines apply to the vault. Access can be inherited from a parent scope such as a resource group, which is convenient, though that same inheritance is a thing to watch during review, since a broad assignment high in the hierarchy reaches every vault beneath it. RBAC integrates with Privileged Identity Management, so a privileged data-plane role can be made eligible rather than permanent, activated only when needed and expiring automatically. And RBAC supports deny assignments, which can carve an exclusion out of an otherwise granted scope. None of this is available under the legacy access policy model, which is precisely why Microsoft now treats access policies as legacy and steers new vaults toward RBAC.

There is a hard operational fact to respect when you move a vault to RBAC. A vault uses one model at a time; it does not run access policies and RBAC simultaneously. Switching an existing vault to the RBAC permission model invalidates all of its access policies the moment you flip it. If you have not already created the equivalent RBAC role assignments for every principal that legitimately needs access, those principals lose access at the cutover, and the applications behind them start failing to read secrets. The migration is therefore an inventory exercise first and a switch second: enumerate every access policy, map each one to the narrowest RBAC role that reproduces its intent, assign those roles, test, and only then change the model. The reward for that care is a vault where access is granular, auditable, and no longer self-grantable by anyone who can write to the resource.

## Configuring the access model correctly

Knowing that RBAC is the better model is half the work. The other half is configuring it so that least privilege is the lived reality rather than a slogan in a policy document. The starting move is to provision new vaults on RBAC from the first line of infrastructure code, never on access policies. As of Key Vault API version 2026-02-01 and later, RBAC is the default access control model for new vaults, matching the portal experience, and earlier API versions are scheduled to retire by February 2027. Pin your ARM, Bicep, and Terraform definitions to a current API version so that a vault you create tomorrow inherits the hardened default rather than the legacy one. Treat the API version as a security setting, not a boilerplate string, because the version you target decides which model a fresh vault is born with. Flag the specific version numbers and the retirement date here for verification against the current Microsoft documentation before publish, since Azure roadmaps move.

With RBAC selected, the discipline is choosing the narrowest role at the tightest scope. Key Vault ships a set of built-in data-plane roles that separate reading from writing and separate secrets from keys from certificates. An application that only needs to read connection strings should hold the Key Vault Secrets User role, which permits reading secret values and nothing more. It should not hold Key Vault Secrets Officer, which can also create and delete secrets, and it certainly should not hold Key Vault Administrator, which governs the whole data plane. A certificate-management automation should hold a certificates role, not a blanket administrator role. The principle is concrete: match the role to the verb the workload actually performs, and match the scope to the object the workload actually touches.

```bicep
resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: vaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
  }
}
```

That template encodes most of the rbac-network-and-recovery rule in one resource block. The `enableRbacAuthorization` flag puts the data plane on RBAC. The soft delete and purge protection flags arm the recovery controls. The network section denies public access by default. What it does not encode is the role assignments, which belong in their own resource so that access is reviewed separately from infrastructure. Assigning the narrow role to a managed identity, scoped to the vault, looks like this.

```bicep
resource secretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, appIdentity.id, 'Key Vault Secrets User')
  scope: vault
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6'
    )
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}
```

Notice that the role definition is referenced by its stable GUID rather than its display name. Role names are for humans reading a script; the GUID is what survives a rename and what you should commit to source control. Notice too that the principal is a managed identity, not a secret-bearing service principal. That is not incidental. The cleanest data-plane access is access that carries no credential of its own, because a credential the workload holds is a credential an attacker can steal. The companion practice of pointing applications at the vault through references rather than copies is covered in [configuring Key Vault references in apps](/2023/04/24/configure-key-vault-references/), and it pairs with RBAC to remove standing secrets from your configuration entirely.

### Should I scope RBAC roles to the vault or to individual secrets?

Scope to the vault when a principal legitimately needs every secret in a single-purpose vault, which is the common case for a one-application vault. Scope to an individual secret when one vault holds secrets for several consumers and a principal should reach only its own. Per-secret scoping is the sharper tool; reach for it whenever the vault is shared.

The decision between vault-level and secret-level scope is at heart a decision about design. The cleanest pattern is one vault per application per environment, so that the natural blast radius of any single assignment is one application's secrets in one environment. When you follow that pattern, vault-level scope is already tight, because the boundary is the resource itself. Per-secret scope earns its complexity when a store is shared across consumers, for instance a platform vault that several teams draw from, where you genuinely want one team unable to read another team's entries. RBAC supports that granularity; access policies never could. The trade-off is management overhead: more assignments to track and review. The hardening checklist accounts for this by asking not just whether RBAC is on, but whether the scope of each assignment is justified by what the principal does.

## Locking down the network

Access control decides who may ask the vault for a secret. Network control decides from where the request may even arrive. The two are layers in defense in depth, and a hardened vault uses both, because either one alone leaves a gap the other would have caught. A vault with perfect RBAC but a public endpoint still answers every authentication attempt from every address on the internet, which means every stolen credential and every brute-force script can at least reach the door. A vault with a locked network but loose RBAC trusts anyone who gets inside the perimeter. The network half of the rbac-network-and-recovery rule exists to shrink the set of places a request can originate from to the set of places a legitimate request should originate from.

By default a new vault accepts traffic from all networks. The first hardening move is to change the default action of the vault firewall from allow to deny, so that the vault rejects traffic unless a rule or a private path explicitly permits it. From that deny-by-default stance you have two ways to grant the access your workloads need. The lighter-weight option is the service firewall with selected networks: you allow specific virtual network subnets through a service endpoint, and optionally a small set of trusted public IP ranges for administrative access. The stronger option, and the one to prefer for sensitive vaults, is the private endpoint.

### Is a private endpoint enough on its own?

A private endpoint is the strongest network control, but it is not a substitute for the firewall setting or for RBAC. It gives the vault a private address inside your virtual network and removes the public path, yet you still set public network access to disabled and still scope data-plane roles tightly. The endpoint controls the path; RBAC controls the permission.

A private endpoint projects the vault into your virtual network as a network interface with a private IP address. Traffic from your workloads reaches the vault over the Microsoft backbone and your private address space rather than over the public internet, and once the endpoint is in place you disable public network access entirely so that the public path simply does not exist. This is the configuration to aim for on any vault holding production secrets or encryption keys. It changes the threat model: an attacker who steals a credential but has no foothold inside your network cannot reach the vault at all, because there is no public address to reach. The credential becomes useful only in combination with network access you have not granted, which is exactly the layering defense in depth is meant to produce.

Two practical wrinkles deserve attention so the lockdown does not break legitimate flows. The first is the trusted services bypass. Some Azure services need to read from the vault as part of platform operations, for example a storage account fetching a customer-managed key, and they do not come from your virtual network. The bypass setting for trusted Azure services lets those platform flows through without opening the vault to the public, and it is the right way to handle them rather than relaxing the firewall. The second wrinkle is DNS. A private endpoint only works if the vault's name resolves to the private IP for the clients that should use it, which means a private DNS zone linked to the right virtual networks. A surprising share of private endpoint problems are DNS problems wearing a network costume, where the endpoint is correct but a client resolves the public name and fails. When access fails after a lockdown, resolution is the first thing to check, and the broader pattern of diagnosing a refused request is covered in [fixing Key Vault access denied and forbidden errors](/2023/01/16/fix-key-vault-access-denied/), which separates an authorization failure from a network failure so you fix the right thing.

The network posture is not only about blocking the outside. It is also about ensuring that the inside is segmented enough that reaching one workload does not mean reaching the vault. A vault private endpoint placed in a tightly controlled subnet, reachable only from the application tier that needs it, is far stronger than one reachable from a flat network where any compromised host can route to it. Network lockdown and least privilege are the same idea applied to two different planes: grant the minimum, from the minimum set of origins, to the minimum set of identities.

## Recovery: soft delete and purge protection

The third leg of the rbac-network-and-recovery rule protects the vault against destruction rather than against unauthorized reading. Access control and network control both assume the vault still exists. Recovery control assumes it might not, and ensures that a deletion, whether fat-fingered or malicious, does not become permanent before anyone can react. This is the leg engineers most often skip, because nothing about a vault on defaults signals that it is missing, and the cost of skipping it only appears at the worst possible moment.

Soft delete is the recycle bin for the vault and its contents. When soft delete is on, deleting a secret, key, certificate, or the whole vault moves it into a deleted state rather than erasing it, and it stays recoverable for a configurable retention period. The retention is set between 7 and 90 days, with 90 the default, and the interval can only be set when the vault is created; it cannot be changed afterward. This is a setting to get right at provisioning time, because a vault created with a 7-day window cannot be widened to 90 later without recreating it. Recovery during the window is straightforward: the deleted object is restored to its prior state. As of February 2025, Microsoft enabled soft delete on all key vaults and removed the ability to opt out, so a vault you create today has soft delete on and cannot have it turned off. Once enabled, soft delete cannot be disabled. Verify the specific enforcement date and retention bounds against current Microsoft documentation before publish, as these platform timelines are the kind of fact that shifts.

Soft delete alone, though, has a gap that purge protection closes. A soft-deleted object can still be purged during its retention window, which permanently destroys it before the window elapses. Purging requires an elevated permission that is not granted by default, which raises the bar, but an attacker or an administrator who holds that permission can delete a secret and then purge it, defeating the recycle bin entirely. Purge protection removes that escape hatch. When purge protection is on, a deleted vault or object cannot be purged until the full retention period passes, no matter who asks. There is no override. The data is recoverable for the entire window, and only after the window elapses does it leave on its own.

### Why enable purge protection if soft delete already recovers deletions?

Because soft delete on its own can be undone. A privileged user can delete an object and then purge it inside the retention window, making the recovery moot. Purge protection blocks that purge for the whole window with no override, so even a malicious insider with delete rights cannot make the loss permanent before anyone notices.

Purge protection carries one property that makes people hesitate, and it is worth stating plainly so the hesitation does not become an excuse to skip it. Once purge protection is enabled, it cannot be disabled. It is a one-way setting. The reason to enable it anyway is that the downside of a permanent, irreversible commitment to keeping deleted data recoverable for at most 90 days is negligible, while the downside of a permanently lost encryption key is total. If a vault holds keys that encrypt storage, disks, or databases, losing those keys means losing access to the encrypted data, and no support ticket recovers it. This is why most Azure services that integrate with Key Vault, such as Storage using a customer-managed key, require purge protection before they will trust the vault with their encryption keys. The platform is enforcing the recovery half of the rule on your behalf, because it has seen what happens when the key disappears.

The combined posture is simple to state and easy to verify. Soft delete on, with the longest retention the vault's purpose justifies, set at creation. Purge protection on, accepting that the choice is permanent. With both in place, the vault cannot be destroyed faster than your team can notice and respond, and the encryption keys that protect the rest of your estate cannot evaporate because of one command. The InsightCrunch Key Vault hardening checklist treats a vault without purge protection as an open finding regardless of how good its access and network posture look, because access and network controls protect a vault that exists, and recovery controls protect against the case where it does not.

## Rotating secrets, keys, and certificates

A vault that is locked down today protects credentials that may have leaked yesterday. Rotation is the control that limits how long any single secret stays valuable, so that a credential exposed at some point in its life stops working before an attacker can exploit it at leisure. Hardening the vault and never rotating its contents is like fitting a strong lock to a door whose key you handed out years ago and never changed.

The first rotation discipline is to stop creating copies that need rotating in the first place. Every place a secret is copied out of the vault into a configuration file, an environment variable baked into an image, or a pipeline variable becomes a second thing to rotate and a second place to leak from. The cleaner pattern is to keep the secret in the vault and have the application read it through a reference resolved at runtime, or better, to remove the shared secret entirely by using a managed identity so the workload authenticates with a platform-issued token that rotates itself. A workload on a managed identity has no stored secret to rotate, which is the strongest form of rotation: the absence of a long-lived credential. Where a stored secret is unavoidable, the reference pattern means there is one authoritative copy in the vault and rotation is a single update rather than a hunt across config.

### How should I rotate secrets and keys without breaking applications?

Rotate without downtime by overlapping validity: generate the new secret, make it active alongside the old one, point consumers at the new value, confirm they work, then retire the old. For keys, keep the previous version available for decryption while new operations use the current version. The overlap is what prevents a hard cutover from breaking live traffic.

The mechanics differ by object type, and the differences matter for getting rotation right. Keys support versioning natively: rotating a key creates a new version while prior versions remain available, so data encrypted under an old key version can still be decrypted while new operations use the current version. This makes key rotation a graceful transition rather than a break. Many key scenarios can be automated with a rotation policy that creates a new version on a schedule, removing the human from the loop and the risk that a manual rotation is simply never done. Certificates similarly support lifecycle management, with the vault able to renew a certificate before expiry, either through an integrated certificate authority or by signaling that a renewal is due, which prevents the recurring outage of a certificate that lapsed because nobody was watching the expiry date.

Secrets are the type that most often lacks native rotation logic, because a secret is opaque to the vault; it is just a value. The vault can store secret versions and notify when a secret nears its expiry, but the act of generating a new credential in the upstream system, a database password or an API key, and writing the new value into the vault has to be orchestrated. The durable pattern is an automation, often an event-driven function triggered by a near-expiry notification, that creates the new credential in the source system, writes it to the vault as a new version, and lets consumers pick it up through their references. The overlap window during which both the old and new credentials are valid is what keeps live applications from failing at the moment of rotation. Build the rotation around that overlap and a rotation is a routine event rather than a planned outage.

Rotation also closes a quieter risk: the credential that was correct when issued but should no longer exist because the person or service that needed it is gone. A rotation cadence forces a periodic reckoning with what each secret is for and whether it is still needed, which is the same hygiene that access reviews bring to role assignments. Hardening is not a one-time configuration; it is a posture maintained over time, and rotation is the part of the posture that keeps the vault's contents from quietly aging into liabilities.

## Least privilege applied concretely

Least privilege is the principle that every role assignment makes a more specific promise about who can do what. Stated as a principle it is uncontroversial; the difficulty is applying it to a real vault without leaving either gaps or friction. The concrete version of least privilege for a vault has three dimensions: the verb, the object, and the lifetime of the grant.

The verb is the action the principal may perform. A workload that reads a connection string needs the read verb on secrets, not the write verb, and not any verb on keys or certificates it never touches. Built-in roles already separate these verbs, so applying the verb dimension is mostly a matter of resisting the temptation to assign a broad role because it is convenient. Key Vault Administrator is convenient precisely because it covers every verb, which is exactly why it is the wrong choice for anything but a narrow administrative principal. The discipline is to start from the most restrictive role that includes the verb the workload uses and to widen only with a reason recorded.

The object is the resource the grant covers, expressed as scope. A grant scoped to a single secret is a narrower promise than a grant scoped to the vault, which is narrower than a grant scoped to the resource group containing the vault. The object dimension is where vault design and access design meet: a one-application vault makes vault scope already tight, while a shared vault demands per-secret scope to keep its tenants separated. The failure mode to watch is inherited scope. An assignment made at subscription or resource-group level for a different purpose can silently confer vault access, because RBAC inheritance flows downward. Part of applying least privilege is reading not just the assignments made on the vault but the assignments made above it that reach the vault by inheritance.

The lifetime is how long the grant lasts. A permanent assignment of a privileged role is a standing risk that exists whether or not anyone is using it. The lifetime dimension is addressed by making privileged roles eligible rather than active through Privileged Identity Management, so that a person who needs Key Vault Administrator activates it for a bounded window with justification, and it expires automatically. Standing access is the access an attacker inherits when they compromise an account; time-bound access is access an attacker must also time correctly, which is a meaningfully harder problem for them. For the deeper treatment of how Zero Trust frames this, the principle of verifying explicitly and granting the least standing privilege is developed in [Azure Zero Trust architecture](/2024/02/05/azure-zero-trust-architecture/), of which a hardened vault is one concrete instance.

These three dimensions also give review its structure. Reviewing access is not a vague instruction to look at who has access; it is a specific set of questions asked of every assignment. Does the verb match what the principal does? Does the object scope match what the principal touches? Does the lifetime match how often the principal actually needs the access? An assignment that fails any of the three is a finding. Reviewed this way, least privilege stops being aspirational and becomes a property you can audit, which is the only kind of security property that survives contact with a growing estate and changing teams.

## Monitoring and auditing access

A hardened vault that nobody watches is a vault whose first sign of compromise is the breach itself. Monitoring turns the vault from a silent component into one that produces evidence: who reached it, what they asked for, whether the request succeeded, and from where. That evidence is what lets you detect misuse, prove compliance, and reconstruct an incident after the fact. The monitoring half of hardening is what makes the rest of the posture auditable rather than merely configured.

The foundation is diagnostic logging. The vault can emit logs of every data-plane operation, each secret read, each key use, each certificate access, along with control-plane changes such as a modified network rule or a new role assignment. Routing those logs to a Log Analytics workspace gives them a queryable home and a retention period you control, and it lets you write detections against them. The vault's logging fits the same diagnostic-settings model the rest of the platform uses, and the service mechanics behind what a vault can emit are laid out in the [Azure Key Vault complete guide](/2022/03/07/azure-key-vault-complete-guide/). Without diagnostic logging enabled, the vault is operating blind: a credential could be reading every secret in the vault on a loop and there would be no record of it.

### How do I monitor and audit Key Vault access effectively?

Enable diagnostic logs for both data-plane and control-plane operations, route them to a Log Analytics workspace, and write queries that surface the patterns that matter: access from unexpected identities, spikes in secret reads, failed authorization attempts, and any change to the access model or network rules. Alert on the changes, review the access patterns periodically.

What you query for is the difference between collecting logs and actually monitoring. A useful baseline of detections starts with the events that precede or accompany misuse. A sudden spike in secret-read volume from a single identity can indicate a compromised credential enumerating the vault. Reads from an identity that has no business reading, or from a network location that should not have a path to the vault, are signals worth an alert. Failed authorization attempts in volume can indicate probing. On the control plane, any change to the permission model, the network rules, or the role assignments is high-value to alert on, because those are the changes an attacker makes to widen their own access, and they are changes that should only ever happen through your change process. An alert on an out-of-band access-model change is one of the highest-signal detections a vault can have.

Auditing extends monitoring backward in time and outward to compliance. The same logs that drive real-time alerts are the record you query during an audit to demonstrate that access was appropriate, or during an incident to determine exactly what an attacker reached. Retention matters here: an incident discovered months after the fact is only investigable if the logs still exist. Setting a retention period that matches your compliance and incident-response needs is part of the hardening, not an afterthought. The posture to aim for is one where every access leaves a record, every record is queryable, the records that signal misuse raise an alert, and the records persist long enough to investigate. A vault configured that way does not just resist compromise; it tells you when resistance fails, which is the property that turns a static configuration into an operational security control.

## The InsightCrunch Key Vault hardening checklist

The controls above combine into a posture you can run against any vault as a checklist. Each row names a control, the hardened state to reach, and the reason that state matters, so the checklist doubles as the rationale. Treat any vault that fails a row as having an open finding, and treat the access, network, and recovery rows as the non-negotiable core, since those three are the rbac-network-and-recovery rule made operational.

| Control | Hardened state | Why it matters |
|---|---|---|
| Permission model | Azure RBAC enabled for the data plane | Scopes access to individual objects and stops vault writers from self-granting data access |
| Role scope | Narrowest built-in role at the tightest scope | Limits the blast radius of any single compromised principal |
| Privileged access | Privileged roles eligible through PIM, not standing | Removes standing access an attacker would inherit |
| Public network access | Disabled | Removes the public path so a stolen credential alone cannot reach the vault |
| Firewall default action | Deny | Rejects traffic unless explicitly permitted |
| Private endpoint | Present for production vaults | Reaches the vault over private address space, not the internet |
| Trusted services bypass | Enabled where platform flows require it | Lets legitimate Azure platform reads through without opening the vault |
| Soft delete | Enabled, longest justified retention, set at creation | Makes deletions recoverable within the window |
| Purge protection | Enabled | Prevents permanent deletion during the window, even by a privileged insider |
| Secret references | Used instead of copied secrets | Keeps one authoritative copy and removes scattered leak points |
| Managed identity | Used instead of stored service principal secrets | Removes a long-lived credential the workload would otherwise hold |
| Rotation | Policy or automation in place per object type | Limits how long any exposed credential stays valuable |
| Diagnostic logging | Enabled to Log Analytics, adequate retention | Produces the evidence to detect misuse and investigate incidents |
| Access alerting | Alerts on model and network changes and anomalous reads | Surfaces the changes and patterns that signal compromise |

The checklist is deliberately ordered from access through network through recovery and then into the operational controls, because that is the order in which the controls reduce risk. If you can run only the top three rows on a vault today, you have closed the exposures that the rbac-network-and-recovery rule names as the most common, and you have a defensible baseline to build the rest on. The remaining rows turn a defensible baseline into a durable one. A vault that passes every row is not merely configured well; it is configured in a way you can prove, audit, and reproduce, which is the difference between a vault that is secure today and a fleet of vaults that stays secure as it grows.

## The common misconfigurations and the breaches they enable

Hardening is easier to internalize through the failures it prevents. Each of the following is a pattern engineers report repeatedly, paired with the breach it invites and the row of the checklist that closes it. Reading the posture as a set of avoided disasters rather than a set of settings is what makes the settings stick.

The first pattern is the vault left on access policies with open network access. This is the legacy default carried forward, and it fails two rows of the checklist at once. The access-policy model means anyone with a vault-write permission can grant themselves data-plane access, and the open network means they can do it from anywhere. The breach this enables is the quiet escalation: a contributor on the resource group, perhaps a developer who never needed secret access, opens the access configuration, grants themselves get and list on secrets, and reads every credential in the vault, all from a workstation on the public internet. Nothing about the operation looks anomalous because the permission to perform it was already present. The fix is the access half and the network half of the rule together: move to RBAC so vault-write no longer confers data access, and lock the network so the operation cannot originate from anywhere.

The second pattern is purge protection left off. The vault may have excellent access and network controls, but without purge protection a deletion is permanent during the window. The breach here is destructive rather than exfiltrating. An attacker who gains a privileged role, or an administrator acting maliciously or by mistake, deletes a key that encrypts a storage account and then purges it. The encrypted data is now unrecoverable, not because the storage failed but because the key that unlocked it is gone. This is the failure that integrating services try to prevent by refusing to use a vault without purge protection, and it is the reason the checklist treats a missing purge protection as a finding regardless of the rest of the posture.

The third pattern is secrets copied into configuration instead of referenced. A team reads a connection string out of the vault once and pastes it into an application setting, a container image, or a pipeline variable. The vault is now hardened and irrelevant, because the secret it was protecting lives in plaintext somewhere the vault does not control. The breach is a leak from the copy: the image is pushed to a registry someone can read, the pipeline log prints the variable, the config file lands in a repository. The vault never recorded an unauthorized access because the access that mattered happened outside it. The fix is the reference pattern and the managed identity: keep the authoritative secret in the vault, resolve it at runtime, and where possible remove the stored secret entirely so there is nothing to copy.

The fourth pattern is no rotation policy. Secrets and keys are created once and never changed, so a credential exposed at any point in its long life stays valid indefinitely. The breach is delayed and silent: a secret leaks through some unrelated channel, a logged variable, a former employee's notes, a compromised laptop, and remains usable months or years later because it never rotated. The fix is rotation as a standing process, automated where the object type allows, so that the useful life of any exposed credential is bounded.

The fifth pattern is no access logging. The vault has no diagnostic settings, so its data-plane operations are invisible. The breach is not caused by the missing logs, but it is hidden by them. A compromised credential reads the vault on a schedule, and there is no record to alert on and nothing to investigate when the downstream effects surface. The fix is diagnostic logging to a queryable store with alerts on the high-signal events, so that misuse is visible while it is happening rather than reconstructed after the damage.

Each pattern maps to a row, and each row maps to a breach it prevents. That mapping is the argument for the checklist: it is not a list of settings for their own sake, but a list of specific failures and the specific control that closes each one.

## Verifying the posture

A posture you cannot verify is a posture you are hoping for rather than holding. Verification turns each checklist row into a question you can answer with a command or a query, so that the claim "the vault is hardened" rests on evidence rather than memory. The verification commands below are the confirming half of every control discussed so far, and they are the practice that catches drift before an audit or an incident does.

Start with the access model, because it is the foundation. A single property tells you whether the vault is on RBAC or still on access policies, and reading it is the first verification step.

```bash
az keyvault show --name myvault \
  --query "properties.enableRbacAuthorization"
```

A result of true confirms RBAC; false or null means the vault is still on the legacy model and fails the first checklist row. Next, verify the recovery controls, which are two more properties on the same resource.

```bash
az keyvault show --name myvault \
  --query "{ softDelete: properties.enableSoftDelete, purgeProtection: properties.enablePurgeProtection, retention: properties.softDeleteRetentionInDays }"
```

You want soft delete enabled, purge protection enabled, and a retention value that matches the window your vault's purpose justifies. Remember that retention is fixed at creation, so a value you dislike here is a signal to plan a recreation rather than an edit. Then verify the network posture, which lives in the public network access setting and the network ACLs.

```bash
az keyvault show --name myvault \
  --query "{ publicAccess: properties.publicNetworkAccess, defaultAction: properties.networkAcls.defaultAction }"
```

You want public access disabled and the default action set to deny. If the vault uses a private endpoint, confirm the endpoint exists and, just as important, that DNS resolves the vault name to the private address from a client that should reach it, since a correct endpoint with broken resolution presents exactly as a network failure. Verify the role assignments next, scoped to the vault, to confirm that access matches intent.

```bash
az role assignment list --scope \
  "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/myvault" \
  --query "[].{principal: principalName, role: roleDefinitionName}" -o table
```

Read the result against the three dimensions of least privilege: the verb in each role, the scope of each assignment, and whether any privileged role is standing rather than eligible. Remember to check assignments above the vault too, since an assignment at the resource group or subscription reaches the vault by inheritance and will not appear when you scope the query to the vault alone. Finally, verify that diagnostic logging is on, because a vault with no diagnostic settings is one you cannot monitor.

```bash
az monitor diagnostic-settings list \
  --resource "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/myvault" \
  -o table
```

An empty result means the vault is logging nothing and fails the logging row. Run these five checks and you have verified the access, recovery, network, least-privilege, and logging controls directly against the live resource. Where you want a guided environment to practice running this verification and to see a hardened vault next to a misconfigured one, you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), which keeps a tested set of Key Vault commands and templates for exactly this kind of posture check. The point of the verification pass is not to run it once but to run it on a schedule, because a vault that passes today can drift tomorrow when someone adds an assignment or relaxes a rule, and the only way to know is to ask the resource directly.

## Making the posture auditable and repeatable

A vault hardened by hand is hardened once. The next vault, provisioned by a different person under deadline, starts from defaults again, and the posture you worked for does not propagate. The final move in Key Vault security best practices is to make the hardened state the default that every new vault inherits and the standard that every existing vault is measured against, so the posture is repeatable across a fleet and auditable without manual inspection.

Repeatability comes from infrastructure as code. The hardened vault, with RBAC enabled, public access disabled, the firewall denying by default, soft delete and purge protection on, and a current API version, lives as a module that teams instantiate rather than as a portal click sequence they reproduce from memory. A module bakes the checklist into the act of creation: a vault made from the module cannot be born on access policies or with an open network, because the module does not expose those as options. This is the most reliable form of hardening, because it removes the human decision at the moment the decision is most likely to be skipped. Role assignments belong in code too, but in their own files reviewed separately from the vault definition, so that a change to who can read a secret is a visible, reviewable event rather than a quiet portal action.

Auditability comes from policy. Azure Policy can assert the hardened state across every vault in scope and report or block the ones that fall short. A policy that requires RBAC authorization, a policy that requires purge protection, a policy that denies public network access, and a policy that requires diagnostic settings together encode the checklist as continuous, automatic compliance. The difference between this and a manual review is that policy never forgets to run and never tires of checking. A vault provisioned out of band, perhaps in a subscription the platform team does not watch closely, still shows up as non-compliant against the policy set, which is exactly the vault a manual review would have missed. For the broader treatment of operating a standard this way rather than auditing once, the discipline of enforcing and assessing a baseline connects directly to [Azure Zero Trust architecture](/2024/02/05/azure-zero-trust-architecture/), where the vault is one resource type among many held to a verifiable standard.

The two together, code for repeatability and policy for auditability, are what keep the rbac-network-and-recovery rule from being a thing you did once and lost. Code ensures new vaults start hardened. Policy ensures every vault, however it was created, is measured against the standard and the gaps surface on their own. After each new vault or each change to the standard, append the result to your own ledger of what the fleet looks like, so the audit trail is not just in the policy engine but in a record your team owns. A vault estate run this way does not drift toward defaults, because the defaults have been replaced and the drift is caught. That is the destination: not a hardened vault, but a hardening that holds.

## Credential-free access with managed identity

The strongest data-plane access is access that carries no secret of its own. A workload assigned a managed identity authenticates to Microsoft Entra ID with a platform-issued token rather than a stored client secret or certificate, and that token rotates on its own behind the scenes. There is no credential sitting in configuration for an attacker to lift, no expiry date a human has to remember, and no rotation chore to neglect. For any workload that runs on an Azure compute service that supports managed identity, this is the access model to reach for first, because it removes an entire class of leak at the source.

The mechanics are clean. You enable a system-assigned or user-assigned identity on the compute resource, assign that identity the narrow data-plane role it needs, such as Key Vault Secrets User scoped to the one store it reads from, and point the application at the store through the Azure identity libraries. The application asks the platform for a token, the platform issues one tied to the identity, and the request to read a secret succeeds because the identity holds the role. At no point does a long-lived credential change hands. A user-assigned identity is the better choice when several workloads should share one identity and one set of role assignments, since the identity outlives any single compute instance and the assignments do not have to be recreated when instances come and go.

### When should I prefer a managed identity over a service principal with a secret?

Prefer a managed identity whenever the workload runs on an Azure service that supports one, which covers most compute. A service principal with a stored secret is the fallback for workloads outside Azure or on services without managed identity support, and even then it should hold the narrowest role and have its secret rotated on a schedule. The default is the credential-free path.

The reason this matters for hardening is that it changes what a compromise yields. If a workload holds a stored secret and the host is compromised, the attacker now holds a credential that works from anywhere until it is rotated, which may be never. If the same workload uses a managed identity, a compromise of the host yields a token that is tied to that host's identity and expires quickly, and the attacker cannot lift a reusable credential because none exists. Combined with a private endpoint and a narrow role, the managed identity means a compromise has to clear several independent barriers at once rather than collecting a single reusable key. The companion practice of resolving secrets through references rather than copies fits the same goal, and the two together let you remove standing secrets from configuration almost entirely, leaving the store as the one authoritative source.

## A reference map of built-in data-plane roles

Choosing the narrowest role is easier with the built-in roles laid out by what they permit and the object type they cover. The map below is a supporting reference for the hardening checklist's role-scope row, pairing each role with the verb it grants and the workload it suits, so you can match a principal to the least privilege that still lets it do its job.

| Built-in role | Permits | Suits |
|---|---|---|
| Key Vault Secrets User | Read secret values | An application that only reads connection strings or API keys |
| Key Vault Secrets Officer | Read, set, and delete secrets | An automation that provisions and rotates secrets |
| Key Vault Crypto User | Use keys for cryptographic operations | A workload that signs, wraps, or decrypts with a key |
| Key Vault Crypto Officer | Manage keys, including create and delete | A key-management automation |
| Key Vault Certificates Officer | Manage certificates | A certificate-lifecycle automation |
| Key Vault Reader | Read metadata, not secret values | A monitoring or inventory principal that lists objects without reading them |
| Key Vault Administrator | Full data-plane control | A narrow break-glass or administrative principal only |

The pattern the map encodes is separation by verb and by object. A reading workload never needs an officer role; an officer automation never needs administrator. The reader role deserves a special mention, because it solves a common over-grant: a monitoring or inventory tool often needs to know what objects exist without needing to read their values, and granting it a secrets-read role to satisfy a listing requirement hands it far more than it needs. The reader role lets such a principal enumerate metadata while staying blind to the values, which is exactly the least privilege a monitoring principal should hold. Reach for administrator only for a deliberate break-glass identity, made eligible through Privileged Identity Management so it is activated with justification and expires, never as a convenience for a workload that could do its job with a narrower grant.

## Protecting customer-managed keys

The recovery controls take on extra weight when the store holds customer-managed keys, the keys you supply for services like Storage, managed disks, and databases to encrypt their data at rest. In that arrangement the key does not just protect a secret; it protects the entire encrypted dataset of another service, and the relationship between the key and that data is what makes purge protection non-negotiable rather than merely advisable.

The mechanism is straightforward and unforgiving. The encrypting service holds a reference to a key in your store and uses it to wrap and unwrap the data encryption keys that actually encrypt the bytes. If that referenced key is deleted and then purged, the wrap can never be undone, and the encrypted data becomes permanently unreadable even though the storage itself is intact. The bytes are still there; the means to decrypt them is gone. This is why most Azure services that integrate with the store for encryption require purge protection before they will trust it with a customer-managed key. The platform is refusing to let you put yourself one mistaken purge away from total data loss.

### What happens to my encrypted data if the key is deleted?

While soft delete holds the key in the deleted state, the encrypting service loses access and the data becomes unreadable until the key is recovered, so a deletion is already an outage. If the key is then purged, the loss is permanent: the data cannot be decrypted by anyone. Purge protection prevents that purge for the full retention window.

There is an operational subtlety worth internalizing. Even a soft-deleted key, recoverable though it is, causes an immediate outage for the dependent service, because the service cannot unwrap its data encryption keys while the key sits in the deleted state. Recovery restores access, but the window between deletion and recovery is downtime for everything the key protects. This argues for two habits beyond simply enabling the recovery controls. First, monitor for key-deletion events on stores that back encryption, and alert on them immediately, because a deletion is an incident the moment it happens rather than when the retention window expires. Second, treat the keys that back encryption as the most sensitive objects in the store and give the roles that can delete them the tightest scope and the shortest lifetime, since the blast radius of a deletion here is an entire encrypted service, not a single credential.

## Hardening certificates specifically

Certificates carry a hardening concern the other object types do not: they expire, and an expired certificate is an outage that arrives on a schedule whether or not anyone is watching. The store can manage the certificate lifecycle so that renewal happens before expiry rather than after the outage, and using that capability is part of the posture, because a lapsed TLS certificate takes a service offline as surely as a misconfigured firewall.

The store supports two renewal paths. When the certificate is issued by an integrated certificate authority, the store can renew it automatically before expiry, removing the human from the loop entirely. When the certificate comes from an authority the store does not integrate with, the store can still track the expiry and emit a near-expiry notification that triggers your renewal automation, so the renewal is prompted even if it is not fully automatic. Either path is better than the manual alternative, where renewal depends on someone remembering a date, which is the arrangement that produces the recurring expired-certificate outage. Configure the renewal threshold with enough lead time that a failed automatic renewal still leaves room to intervene before the certificate actually lapses.

The access discipline for certificates mirrors the discipline for the other object types. A workload that consumes a certificate needs to read it, not manage it, so it holds a reading role rather than the certificates officer role. The automation that requests, renews, and imports certificates is the one principal that needs the officer role, and that role is scoped to the store and made eligible where it is privileged enough to warrant it. Certificates also benefit from the reference pattern: a service that retrieves its TLS certificate from the store at startup, rather than embedding the certificate and its private key in a deployment artifact, keeps the private key out of images and pipelines where it could leak. The certificate's private key is exactly the kind of material the store exists to protect, so copying it out into a build artifact undoes the protection the store provides.

## Querying the logs for the detections that matter

Diagnostic logs are only as useful as the queries you run against them. With logs flowing to a Log Analytics workspace, a small set of queries turns the raw record into the detections that signal misuse, and writing them once and scheduling them as alerts is what converts passive collection into active monitoring. The queries below are illustrative shapes rather than tuned production rules, and the exact table and column names should be confirmed against the current schema before you rely on them.

```kql
// Spike in secret reads from a single identity
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.KEYVAULT"
| where OperationName == "SecretGet"
| summarize reads = count() by identity_claim_oid_g, bin(TimeGenerated, 1h)
| where reads > 100
| order by reads desc
```

A query like that surfaces an identity reading secrets at a rate that does not match normal application behavior, which is the signature of a credential enumerating the store after a compromise. The threshold is something you tune to your own baseline, since a busy application legitimately reads often; the signal is the deviation from that baseline, not the raw count.

```kql
// Any change to the access model or network rules
AzureActivity
| where ResourceProvider == "Microsoft.KeyVault"
| where OperationNameValue endswith "vaults/write"
| project TimeGenerated, Caller, CallerIpAddress, OperationNameValue, ActivityStatusValue
| order by TimeGenerated desc
```

That control-plane query is one of the highest-signal detections available, because changes to the permission model or the network rules are exactly the moves an attacker makes to widen access, and they should only ever happen through your change process. An alert on an out-of-band write, especially from an unexpected caller or address, catches the escalation while it is happening. Pair these with a query for failed authorization attempts in volume, which can indicate probing, and you have a detection set that covers exfiltration, escalation, and reconnaissance. The discipline is not the cleverness of any single query but the habit of running them continuously and alerting on the results, so that the record the store produces becomes a tripwire rather than an archive.

## Walking a hardening through one store end to end

The controls are easier to hold together when you watch them applied to a single store from defaults to hardened. Picture a store provisioned in a hurry to unblock a project: created through the portal with the access policy model, public network access on, a developer granted broad access policies, secrets read once and pasted into application settings, and no diagnostic settings. It works, and it is a liability on every row of the checklist. Hardening it is a sequence, and the order matters because each step depends on the one before.

The first step is access, because nothing else is safe while anyone with a write permission can self-grant. You inventory the existing access policies, find the developer's broad grant and the application's read access, map each to the narrowest built-in role at the right scope, create those role assignments, and confirm the principals can still reach what they legitimately need. Only then do you switch the store to the RBAC model, knowing the switch invalidates the old policies the instant it lands. The application keeps working because its role assignment is already in place; the developer's over-broad access is gone because you did not reproduce it.

The second step is the network. You set the firewall default action to deny, stand up a private endpoint in the subnet the application runs in, link a private DNS zone so the store name resolves to the private address, enable the trusted services bypass for the one platform integration that needs it, and disable public network access. You test that the application, now reaching the store over the private path, still reads its secrets, and that a client outside the network can no longer reach the store at all. The exposure that let the original self-grant happen from anywhere is closed.

The third step is recovery and hygiene. Soft delete is already on by platform enforcement; you confirm it and enable purge protection, accepting that the choice is permanent. You replace the pasted-in connection strings with references resolved at runtime, and where the application runs on a compute service that supports it, you switch it to a managed identity so the stored secret disappears entirely. You enable diagnostic logging to the workspace, add the spike and control-plane-change alerts, and set a retention period that meets your compliance needs. The store that began as a liability on every row now passes every row, and the last step is to capture its hardened definition as an infrastructure-as-code module and assert the standard with policy, so the next store anyone creates starts where this one ended rather than where it began.

## Securing access from pipelines and automation

Applications are not the only things that reach the store. Continuous integration and deployment pipelines, infrastructure automation, and operational scripts all need access too, and they are a frequent weak point because their access is often broader and longer-lived than any single application's. A pipeline that deploys to many environments can accumulate access to many stores, and a stored pipeline credential that leaks exposes all of them at once. Hardening therefore extends to the automation, applying the same least-privilege and credential-free principles to the machinery that builds and ships your software.

The first move is to remove standing pipeline secrets the same way you remove application secrets. Modern pipeline platforms support federated identity, where the pipeline authenticates to Microsoft Entra ID with a short-lived token tied to the pipeline's own identity rather than a stored client secret. This is the pipeline equivalent of a managed identity, and it removes the long-lived credential that would otherwise sit in the platform waiting to leak. Where federation is available, prefer it, and where a stored credential is unavoidable, scope it narrowly and rotate it on a schedule like any other secret.

The second move is to scope the pipeline's data-plane access to what the deployment actually requires, at the moment it requires it. A deployment that needs to read one secret to configure a service should hold a reading role on that store, not an officer role across every store in the subscription. Where a pipeline genuinely needs broad access for a short window, Privileged Identity Management can make that access eligible rather than standing, so the pipeline's identity activates the elevated role for the deployment and it expires afterward. The principle is the same one that governs human access: the breadth and the lifetime of the grant should match the task, not the convenience of never having to think about it again.

The third move is to keep secrets out of the pipeline's output. A logged variable, an echoed environment value, or a secret passed on a command line that lands in a process listing all leak the very material the store protects, and they leak it into logs that are often retained and widely readable. Pipeline platforms can mask registered secrets in logs, and the reference pattern helps here too: a deployment that hands a service a reference to resolve at runtime never has the secret value pass through the pipeline at all. The store's protection is only as strong as the weakest place the secret travels, and a pipeline is one of the most common places a well-protected secret escapes into plaintext.

### How do I give a CI/CD pipeline access to secrets safely?

Use federated identity so the pipeline authenticates with a short-lived token instead of a stored secret, assign it the narrowest reading role on only the stores it deploys to, and make any broad access eligible through Privileged Identity Management rather than standing. Mask secrets in logs and prefer references so secret values never pass through the pipeline in plaintext.

The automation case also reframes how you think about the blast radius of a single compromised identity. A developer's workstation, a build agent, and an operations script are all identities that can reach the store, and each is a path an attacker could take. Applying the checklist to every one of them, not just to the applications, is what closes the indirect paths. A perfectly hardened store reached by a pipeline that hardcodes an over-broad credential in a readable variable is not hardened in any meaningful sense, because the credential is the access and the credential is exposed. Treat every principal that touches the store, human or machine, as in scope for the same least-privilege and credential-free discipline, and the posture holds across the whole set of paths rather than just the obvious one.

## Reviewing access on a cadence

A posture set once decays as people join teams, leave teams, and change roles, and as workloads come and go. Access that was correct when granted becomes access nobody needs, and unneeded access is standing risk. The control that counters this decay is the periodic access review, which asks of every assignment whether it is still justified and removes the ones that are not. Reviewing access on a cadence is what keeps least privilege a present-tense property rather than a description of how things looked at provisioning time.

Azure provides access reviews as a feature, so the review need not be a manual spreadsheet exercise. An access review can be scheduled to recur, route to the right reviewer, and either remove access automatically when a reviewer does not approve it or flag it for action. For the data-plane roles on a sensitive store, a recurring review aimed at the owners who understand what each principal does turns the abstract goal of removing stale access into a concrete, scheduled task with an owner and a deadline. The review pairs naturally with the three dimensions of least privilege: each assignment is checked for whether its verb, its scope, and its lifetime still match the principal's actual need.

The review also reaches the assignments that inheritance brings in from above. A role granted at the subscription or resource-group level for some unrelated purpose can confer data-plane access by flowing down the hierarchy, and a review scoped only to the store will miss it. A thorough review reads the effective access, which includes the inherited assignments, not just the assignments made directly on the resource. This is the same inheritance that makes broad high-level grants convenient and dangerous in equal measure, and the review is where you catch the cases where convenience reached further than anyone intended.

Pair the recurring review with the alerting discussed earlier and you have both halves of staying current: alerts catch the changes as they happen, and reviews catch the slow accumulation of access that no single change would flag. Standing privileged roles deserve the most frequent review and the strongest preference for being made eligible rather than permanent, because a standing administrative grant is the single assignment an attacker most wants to inherit. Capture each review's outcome in your own ledger alongside the policy compliance state, so the record of who could reach the store, and why, is one your team keeps rather than one you reconstruct under pressure during an incident.

## The verdict

A key vault is the most concentrated trust in an Azure subscription, and its security is decided less by the service than by the posture you wrap around it. The rbac-network-and-recovery rule names the three controls that close the most common exposures together: RBAC so that access is granular and not self-grantable, a locked network so that requests can only originate where they should, and soft delete with purge protection so that the vault cannot be destroyed before anyone reacts. Around those three sit the operational controls that keep the posture honest over time: least privilege expressed as verb, object, and lifetime; rotation that bounds the useful life of any exposed credential; references and managed identities that remove copies and standing secrets; and logging with alerting that makes misuse visible. The InsightCrunch Key Vault hardening checklist gathers all of it into rows you can run against any vault, find the gap, and apply the fix.

The deciding factor, if there is one, is whether the posture is deliberate or inherited. A vault on defaults is not a secure vault that happens to lack a few settings; it is a vault whose security depends on nobody making the obvious mistakes. Hardening it deliberately, then encoding that hardening in code and asserting it in policy, turns security from a hope into a property you can verify and prove. Run the checklist against your vaults, close the access, network, and recovery rows first, and build the rest from there. The sequence is its own lesson: access before network before recovery, because each control rests on the one before it, and a posture applied in that order closes the largest exposures earliest while you still have the most secrets to protect. Encode the result so the next person inherits it, assert it so the gaps surface on their own, and review it so it does not quietly decay. The store that protects everything else deserves to be the most deliberately defended resource you own, and the work to make it so is finite, repeatable, and worth doing once well rather than partially many times.

## Frequently asked questions

### What are the most important Key Vault security best practices?

The core is the rbac-network-and-recovery rule: use Azure RBAC for the data plane so access is granular and cannot be self-granted by anyone who can write to the vault, lock down the network by disabling public access and preferring a private endpoint, and enable soft delete with purge protection so deletions stay recoverable. Around those three, apply least privilege by assigning the narrowest built-in role at the tightest scope, rotate secrets and keys on a policy, use references and managed identities instead of copying secrets into config, and enable diagnostic logging with alerts on access-model and network changes. Run the InsightCrunch hardening checklist to find which of these a given vault is missing. The access, network, and recovery controls are the non-negotiable foundation; the rest turn a defensible vault into a durable one that does not drift back to defaults.

### Should I use RBAC over access policies for Key Vault security?

Yes. Azure RBAC is the recommended authorization model for the Key Vault data plane, and access policies are now legacy. RBAC scopes permissions to individual secrets, keys, or certificates rather than the whole vault, and it removes a dangerous path in the access-policy model where anyone with a vault-write permission can grant themselves data-plane access. Granting RBAC access requires the Owner or User Access Administrator role, which separates managing the vault from accessing its contents. RBAC also integrates with Privileged Identity Management for time-bound access and supports deny assignments. When migrating an existing vault, remember that switching to RBAC invalidates all access policies at once, so inventory every policy, create equivalent role assignments, test, and only then change the model to avoid an outage. For new vaults, choose RBAC from the start.

### How do I lock down Key Vault network access?

Begin by setting the firewall default action to deny, so the vault rejects traffic unless explicitly permitted. Then grant access through the narrowest path your workloads need. For production vaults, prefer a private endpoint, which gives the vault a private IP inside your virtual network, and then disable public network access entirely so no public path exists. For lighter needs, allow specific virtual network subnets through service endpoints and a small set of trusted administrative IP ranges. Enable the trusted Azure services bypass where platform flows, such as a storage account fetching a customer-managed key, must reach the vault without coming from your network. Watch DNS: a private endpoint only works if the vault name resolves to the private address for the right clients, and many endpoint problems are actually resolution problems. Network control and access control are layers, so do both.

### Why should I enable soft delete and purge protection?

Soft delete makes a deleted vault or object recoverable for a retention window of 7 to 90 days, acting as a recycle bin so a mistaken deletion is reversible. As of February 2025 it is enabled on all vaults and cannot be turned off. Purge protection closes the gap soft delete leaves on its own: without it, a privileged user can delete an object and then purge it inside the window, making the loss permanent. Purge protection blocks any purge until the full window elapses, with no override, so even a malicious insider with delete rights cannot destroy the data before anyone notices. It is a one-way setting that cannot be disabled once on, but the downside of keeping deleted data recoverable for at most 90 days is negligible next to the downside of a permanently lost encryption key. Many Azure services require it before trusting a vault with their keys.

### How should I rotate secrets and keys without causing outages?

Rotate with overlap rather than a hard cutover. Generate the new secret, make it valid alongside the old one, point consumers at the new value, confirm they work, then retire the old. Keys make this graceful because they version natively: a new version becomes current while prior versions stay available, so data encrypted under an old version still decrypts during the transition, and a rotation policy can create new versions on a schedule automatically. Certificates support lifecycle renewal before expiry. Secrets are the type most often lacking native rotation, so orchestrate it: an automation triggered by a near-expiry notification creates the new credential in the upstream system, writes it to the vault as a new version, and lets consumers pick it up through their references. The strongest rotation is removing the stored secret entirely with a managed identity, since a workload with no long-lived credential has nothing to rotate or leak.

### How do I monitor and audit Key Vault access?

Enable diagnostic logging for both data-plane operations, every secret read, key use, and certificate access, and control-plane changes such as modified network rules or new role assignments. Route the logs to a Log Analytics workspace with a retention period that matches your compliance and incident-response needs, since logs you have deleted cannot be investigated. Then write detections against the high-signal patterns: spikes in secret reads from one identity, reads from identities or network locations that should not have access, volumes of failed authorization attempts, and any change to the permission model, the network rules, or the role assignments. Alert on the control-plane changes especially, because those are how an attacker widens access and they should only happen through your change process. The goal is a vault where every access leaves a queryable record, the records that signal misuse raise an alert, and the records persist long enough to reconstruct an incident.

### What is the difference between the control plane and the data plane for a vault?

The control plane is where you manage the vault as an Azure resource: creating and deleting it, reading its properties, configuring its firewall, and changing its access model. It is authorized by Azure RBAC through Azure Resource Manager. The data plane is where the secrets, keys, and certificates live: reading a secret value, signing with a key, importing a certificate. The data plane can be authorized either by the legacy access policy model or by Azure RBAC. The security significance is that a permission on one plane does not imply permission on the other, and the gap between them is where over-privilege hides. Under access policies, a control-plane write permission can be used to grant oneself data-plane access, because configuring a policy is a control-plane operation. RBAC for the data plane closes that path by requiring a distinct role to grant access.

### Does a private endpoint mean I can relax RBAC?

No. A private endpoint and RBAC control different things, and a strong network does not excuse loose access. The endpoint controls where a request can originate from; RBAC controls what an authenticated identity is permitted to do. An attacker who gains a foothold inside your network, through a compromised workload on the same virtual network, can reach a vault behind a private endpoint, at which point only RBAC stands between them and the secrets. Equally, RBAC without network control answers requests from the entire internet. Defense in depth means both layers stay tight: disable public access and use the private endpoint for the path, and scope data-plane roles narrowly for the permission. Relaxing either because the other is strong reintroduces exactly the single-layer dependency that defense in depth exists to remove.

### Can I switch a vault from access policies to RBAC without downtime?

Yes, but only with preparation, because the switch invalidates all access policies the moment it takes effect. A vault uses one model at a time, so when you enable RBAC, every existing access policy stops authorizing access immediately. If the equivalent RBAC role assignments are not already in place, the principals those policies covered lose access and their applications begin failing. The safe sequence is to inventory every access policy on the vault, map each to the narrowest built-in role that reproduces its intent at the right scope, create those role assignments while still on access policies, test that the intended principals can reach what they need, and only then change the model. Community tooling exists to compare access policies against RBAC role coverage to confirm nothing is missed. Treat the migration as an inventory and validation exercise first and a one-line setting change last.

### What built-in roles should an application use to read secrets?

An application that only reads secret values should hold the Key Vault Secrets User role, which permits reading secrets and nothing more. It should not hold Key Vault Secrets Officer, which can also create and delete secrets, and it should never hold Key Vault Administrator, which governs the entire data plane. Match the role to the verb the workload performs and the object type it touches: a certificate automation gets a certificates role, not a blanket administrator role. Scope the assignment to the vault for a single-application vault, or to an individual secret when the vault is shared across consumers and the application should reach only its own entries. Reference the role by its stable definition GUID in scripts rather than its display name, so a rename does not break automation. Assign the role to a managed identity rather than a secret-bearing service principal where the platform allows, to remove a stored credential entirely.

### Why does purge protection have to be permanent once enabled?

Purge protection is a one-way setting because its whole purpose is to be an irreversible guarantee that deleted data stays recoverable for the retention window. If it could be turned off, an attacker or a malicious administrator who gained sufficient permission could simply disable it and then purge, defeating the protection exactly when it matters. By making the setting permanent, Azure ensures that the recoverability promise cannot be revoked by anyone, including an insider with high privilege. The practical concern people raise is being locked into a setting forever, but the only thing you are locked into is keeping deleted objects recoverable for at most 90 days before they leave on their own. That cost is negligible against the alternative of a permanently destroyed encryption key, which is why integrating services often require purge protection before they will store their keys in the vault.

### How does one vault per application help security?

The one-vault-per-application-per-environment pattern makes the vault itself the security boundary, so the natural blast radius of any single access grant is one application's secrets in one environment. With this design, vault-level RBAC scope is already tight, because there is nothing else in the vault to over-expose, and you avoid the management overhead of per-secret scoping for the common case. It also simplifies monitoring and auditing, since access to a vault maps cleanly to one application, making anomalous access easier to spot. A shared vault holding many applications' secrets forces you to use per-secret scoping to keep tenants separated and makes every access harder to attribute. The pattern is not always practical for every estate, but where you can follow it, it turns vault design into a security control rather than just an organizational convenience.

### What network setting should a brand-new vault start with?

A new vault should start with public network access disabled and the firewall default action set to deny, so it begins from a closed posture rather than an open one. From there, grant only the access your workloads need, preferring a private endpoint for production vaults and a private DNS zone so the vault name resolves to the private address. The reason to start closed is that a vault left on the default open network trusts the entire internet to at least reach its authentication layer, which is the opposite of what you want for the most sensitive resource in the subscription. Encoding the closed default in an infrastructure-as-code module means a new vault cannot be born with an open network, removing the human decision at the moment it is most likely to be skipped under deadline. Open only what a specific workload requires, and document why each opening exists.

### How do I keep my vault posture from drifting over time?

Make the hardened state both repeatable and auditable. Repeatability comes from infrastructure as code: define the hardened vault as a module with RBAC, disabled public access, deny-by-default firewall, soft delete, and purge protection baked in, so every new vault inherits the posture and cannot be created on the legacy defaults. Auditability comes from Azure Policy: assert the hardened state across every vault in scope with policies that require RBAC, require purge protection, deny public access, and require diagnostic settings, so any vault that falls short surfaces as non-compliant on its own, including ones created out of band that a manual review would miss. Run the verification commands on a schedule to catch drift at the resource level, and keep a ledger of your fleet's state so the audit trail is one your team owns. Code stops drift at creation; policy catches it everywhere else.

### How often should I review access to a sensitive store?

Review access to a sensitive store on a recurring schedule rather than only when something changes, since stale access accumulates quietly between changes. A quarterly review suits most production stores, with more sensitive ones, especially those holding encryption keys or reached by privileged roles, reviewed monthly. Use Azure access reviews to schedule the recurrence, route each review to an owner who understands what the principals do, and remove access that is no longer justified. Check effective access, including roles inherited from the subscription or resource group, not just assignments made directly on the resource, because inheritance is where unintended access often hides. Pair the recurring review with alerts on access-model and network changes so that sudden changes and slow accumulation are both caught. Record each review's outcome so the audit trail of who could reach the store, and why, is one your team owns.

### Can I back up secrets and keys for disaster recovery?

Yes. Key Vault supports backing up individual secrets, keys, and certificates, producing an encrypted blob you can restore into a store in the same Azure geography. This is useful for recovering an object you have permanently lost in ways soft delete does not cover, or for moving an object between stores within a geography. The backup is encrypted and can only be restored into a store in the same geography, which is a deliberate boundary, not a limitation to work around, since it keeps key material within its compliance region. Backup and restore complement soft delete and purge protection rather than replacing them: the recovery controls guard against deletion within the retention window, while backups give you a longer-term copy under your own control. For a complete recovery posture, enable the recovery controls for the day-to-day protection and maintain backups of the most critical objects for the cases the retention window does not cover.

### Does enabling RBAC affect the control plane too?

The control plane already uses Azure RBAC regardless of the data-plane model, so enabling RBAC for the data plane does not change how the control plane is authorized. What it changes is that data-plane access now follows the same RBAC system as the control plane, giving you one consistent model across both rather than RBAC on the control plane and legacy access policies on the data plane. This consistency is part of the security gain: the same role-assignment APIs, the same audit trail, and the same review tooling apply to both planes. It also means you reason about access to the store the same way you reason about access to every other Azure resource, which reduces the chance of a mistake born of treating the store as a special case. The one operational caution remains that switching the data plane to RBAC invalidates existing access policies, so prepare the equivalent role assignments before the switch.

### What is the single biggest Key Vault security mistake to avoid?

Leaving a vault on the legacy access policy model with public network access enabled, because that single combination lets anyone holding a vault-write permission grant themselves access to every secret in the vault from anywhere on the internet, with nothing about the operation looking anomalous. It fails both the access and the network halves of the rbac-network-and-recovery rule at once and is the most common path to a quiet credential-harvesting breach. The fix is also the highest-value first move you can make on any vault: switch the data plane to RBAC so vault-write no longer confers data access, and disable public network access so requests cannot originate from arbitrary locations. Close those two and you have removed the most exploited exposure a vault carries. The destructive sibling mistake, leaving purge protection off, is the one to fix immediately after, since it guards against permanent loss rather than unauthorized reading.
