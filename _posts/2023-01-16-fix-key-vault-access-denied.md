---
layout: post
title: "Fix Key Vault Access Denied (Forbidden)"
page_title: "Fix Key Vault Access Denied and Forbidden: Diagnose the Access Model, Missing Roles, Firewall, and Soft Delete to Resolve 403 on Azure Key Vault"
date: 2023-01-16
categories: ["Technology"]
tags: ["Azure", "Key Vault", "Troubleshooting", "Security", "Identity", "Cloud Computing"]
excerpt: "Key Vault access denied or Forbidden usually means the wrong access model is in force, a missing data-plane role, the firewall, or a soft-deleted object."
image: "/assets/images/blog/blog-48.webp"
reading_time: 60
author: "nathan-cole"
last_updated: 2023-01-16
lang: en
---
A call to Azure Key Vault that returns Forbidden is one of the most disorienting failures in the platform, because everything around it looks correct. You can see the vault in the portal, you can see the secret listed, the application has an identity, and someone on the team swears they granted access last week. Yet the request comes back with a 403 and a message that the caller does not have permission to read the secret. The reason the failure feels contradictory is almost always the same: the permission you granted exists, but it exists in a place the vault is not looking. **Key Vault access denied** is rarely a case of no access being configured at all. It is a case of access being configured against the wrong authorization model, at the wrong scope, for the wrong identity, or behind a network boundary that rejects the caller before authorization is even evaluated.

This article diagnoses the Key Vault Forbidden response to root cause rather than describing the symptom. By the end you will be able to tell which of the distinct causes is yours, confirm it with a command instead of a guess, and grant the access that the vault actually checks, rather than switching authorization models blindly and hoping the error clears. The central idea is a rule worth naming up front, because it explains most of these incidents in a single sentence: a Key Vault request is authorized against whichever model the vault enforces, so a grant made in the other model is invisible, which is exactly why access can look correct and still return Forbidden.

![Fixing Azure Key Vault access denied and Forbidden root causes - Insight Crunch](/assets/images/blog/blog-48.webp)

## What Forbidden and access denied actually mean on Key Vault

A 403 from Key Vault is an authorization verdict, not a connectivity problem and not an authentication problem. The distinction matters because it tells you where to look. When a caller reaches the vault and the vault rejects the operation with Forbidden, the caller has already proven who it is. The platform accepted the token, resolved the identity, and then asked a separate question: is this identity allowed to perform this specific operation on this specific object in this vault? Forbidden is the answer to that second question. If the caller had failed the first question, you would see an authentication error instead, with a token or credential message rather than a permission message.

The most common literal strings are worth recognizing on sight, because each one points at a slightly different part of the model. The classic access-policy denial reads that the user, group, or application does not have secrets get permission on the vault, sometimes naming the missing operation precisely, such as get, list, set, or delete. The role-based denial reads that the caller is not authorized to perform an action over a scope, often with the action expressed as a data action like Microsoft.KeyVault/vaults/secrets/getSecret/action. A network denial reads that the request is not permitted because public network access is disabled or the client address is not in the allowed list, and it can surface as a 403 with a ForbiddenByFirewall or a similar network-oriented result type rather than a permission message. Reading which of these you have is the first cut of the diagnosis, and it is free.

There is a subtlety here that trips up even experienced engineers. The data plane of Key Vault, where secrets, keys, and certificates actually live, is authorized separately from the control plane, where the vault resource itself is created, configured, and deleted. A person or service can have full control-plane rights over a vault, enough to change its firewall, rotate its access model, and even delete it, while still having no data-plane right to read a single secret value inside it. The portal blurs this line because it shows you the vault and its objects in one interface, but the two planes are governed by different role assignments and different evaluation paths. When a Contributor on a vault gets Forbidden trying to read a secret, the model is working exactly as designed, and the fix is a data-plane grant, not a broader control-plane role.

### What does the Key Vault Forbidden message tell you?

The Forbidden message names the identity, the operation, and sometimes the object, and the shape of the message tells you which authorization model the vault is using. A message about a missing secrets get permission points at the access-policy model, while a message about an unauthorized action on a data action path points at the role-based model. Read the operation it names, note the identity it names, and confirm both against the vault before changing anything, because the message is the cheapest diagnostic signal you have.

The identity named in the message is the second thing to read carefully, and it is the part people skip. If the message names an object ID or an application ID you do not recognize, the caller is not the identity you assigned access to. A web app running under a system-assigned managed identity authenticates as the managed identity's object ID, not as the developer who deployed it and not as the app registration's client ID unless that is what was wired up. A function pulling a secret through a user-assigned managed identity authenticates as that user-assigned identity, and if several user-assigned identities are attached, the runtime may pick a different one than you expect. Matching the named identity in the error against the identity you actually granted access to resolves a surprising share of these incidents before any deeper investigation begins.

## How to read the Key Vault denial and gather the diagnostic signal

Before you touch a role assignment or an access policy, gather three facts: which model the vault enforces, what the failing identity is, and whether the request even reached the authorization stage or was stopped at the network boundary. These three facts narrow the cause space immediately, and each one is a single command away. Diagnosing in this order prevents the most common waste of an afternoon, which is granting access in the model the vault is not using and then being baffled that the denial persists.

Start by reading the vault's authorization configuration. The property that decides everything is whether the vault has role-based access control enabled for its data plane. When that property is true, the vault evaluates Azure roles for data-plane operations and ignores access policies entirely. When it is false or unset, the vault evaluates access policies and ignores data-plane role assignments for those operations. You cannot reason about a denial without knowing this value, so read it first:

```bash
az keyvault show \
  --name my-vault \
  --query "properties.enableRbacAuthorization" \
  --output tsv
```

If that returns true, the vault is in the role-based model, and every grant must be an Azure role assignment with a data action that covers the operation. If it returns false or empty, the vault is in the access-policy model, and every grant must be an entry in the vault's access policy list for the operation. This single value is the fork in the entire diagnosis, and reading it wrong sends you down the wrong branch.

Next, capture the identity that is actually failing. If the workload runs under a managed identity, resolve the identity's object ID so you can match it against grants. For a system-assigned identity on, say, a web app, you read the principal ID from the resource itself:

```bash
az webapp identity show \
  --name my-web-app \
  --resource-group my-rg \
  --query "principalId" \
  --output tsv
```

For a user-assigned identity, resolve its principal ID and its client ID, because the runtime sometimes needs the client ID specified explicitly when more than one identity is attached, and that mismatch produces a token under the wrong identity, which then fails authorization at the vault:

```bash
az identity show \
  --name my-user-assigned-identity \
  --resource-group my-rg \
  --query "{principalId:principalId, clientId:clientId}" \
  --output json
```

The third fact is whether the request reached authorization at all. If the vault's public network access is disabled or its firewall denies the caller's address, the request is rejected before any role or policy is evaluated, and no amount of permission granting will help. Read the network configuration so you can rule this layer in or out:

```bash
az keyvault show \
  --name my-vault \
  --query "{publicNetworkAccess:properties.publicNetworkAccess, networkAcls:properties.networkAcls}" \
  --output json
```

If public network access is disabled and the caller is not arriving through a private endpoint or an allowed network, the denial is a network denial wearing the costume of a permission denial, and you fix it in the network rules, not in the access model. With these three facts in hand, the rest of the diagnosis is a matter of matching the symptom to the cause.

One more piece of signal lives in how the failing application surfaces the error, because the same underlying 403 reads differently through a command-line call than through an application using a credential library. A direct command-line call returns the platform's verbatim message, which names the operation and the model cleanly, so the command line is the fastest place to read the raw denial. An application using a credential library wraps the failure in its own exception, and the wrapping can obscure whether the failure was authorization or something earlier in the credential chain. A library that tries several credential sources in turn, for example an environment credential, then a managed identity, then a developer credential, can report a confusing aggregate error that lists every source it tried, and buried inside it is the real cause: either a credential that never produced a token, or a token that produced a clean 403 at the vault. Reading the wrapped exception to find which credential succeeded in producing a token, and whether the vault then refused that token, tells you whether you are looking at an authorization denial or a credential-acquisition failure dressed up as one. When the application logs are ambiguous, reproduce the call from the command line under the same identity, because the command line strips away the credential-chain noise and hands you the platform's own verdict.

The reason this matters is that a credential chain that falls through to a developer credential during local testing, and to a managed identity in the cloud, can succeed locally and fail in the cloud for reasons that have nothing to do with the vault's access model. The local run authenticated as the developer, who happens to hold a data-plane role, while the cloud run authenticated as a managed identity that does not, so the same code reads a secret on a laptop and gets Forbidden in production. The denial is real and the access model is correct; the difference is which identity each environment authenticated as. Reading the named identity in the cloud error against the role assignments for the managed identity, rather than against the developer's access, resolves this quickly. The habit of always asking which identity actually called, in this specific environment, is the through-line of the whole diagnosis.

### How do I confirm which authorization model my vault enforces?

Read the vault's enableRbacAuthorization property: a value of true means the vault evaluates Azure role assignments for data-plane operations and ignores access policies, while false or unset means it evaluates access policies and ignores data-plane roles. This one property decides whether your fix is a role assignment or an access-policy entry, so confirm it before granting anything. A grant made in the model the vault does not enforce is invisible to the authorization check.

The reason this property is so decisive is that the two models do not blend or fall back to each other. There is no behavior where the vault checks roles, finds nothing, and then checks policies as a backup. The model in force is the only model consulted for the data-plane operation. A vault that was created years ago likely defaults to access policies, while a vault created more recently or provisioned through a security-conscious template may have been created with role-based access enabled. Inheriting a vault from another team without reading this property is how engineers end up adding an access policy to a role-based vault, watching the denial persist, and concluding that Key Vault is broken when the configuration is simply being read against the wrong model.

## The model-in-force rule: why a correct-looking grant returns Forbidden

The single most useful idea for diagnosing Key Vault denials is the model-in-force rule. Stated plainly: a Key Vault data-plane request is authorized only against the authorization model the vault is currently configured to enforce, so a grant placed in the other model has no effect on the decision, which is precisely why a vault can show a grant that looks correct and still return Forbidden. The grant is real. It is simply being evaluated by a part of the system the vault is not asking.

This rule explains the most frequent baffling incident in the entire space. An engineer hits a Forbidden, opens the vault, sees the access-policy list, adds the identity with get and list permissions on secrets, saves, retries, and gets the same Forbidden. From inside the access-policy view everything looks resolved. What the engineer did not check is that the vault has role-based access enabled, which means the access-policy list is decorative for data-plane decisions: the vault never consults it. The fix was never to add a policy; it was to assign an Azure role. The reverse happens too, where someone assigns the Key Vault Secrets User role to a vault that is still in the access-policy model, sees the role assignment in the access control blade, and cannot understand why the application still cannot read its secret. The role is assigned. The vault is not looking at roles.

The practical consequence of the model-in-force rule is that the first corrective action is never to grant access. It is to confirm the model. Once you know the model, the grant is mechanical and reliable. Skipping this step is the difference between a five-minute fix and an afternoon of granting access in two models, broadening roles, and eventually enabling something you did not need to enable. The rule also has a useful corollary for prevention, which is that flipping a vault from one model to the other silently invalidates every grant made in the old model, so a migration that changes the model must re-establish access in the new model as part of the same change, never as a follow-up someone remembers later.

Treat the model-in-force rule as the lens for everything that follows. Each cause below is, at heart, a different way the request fails to find a valid grant in the model the vault enforces, whether because the grant is in the other model, because no grant exists in either, because the grant is at the wrong scope, or because the request never reached the grant check because the network turned it away first.

## The InsightCrunch Key Vault denial table

The denial table below is the findable artifact for this diagnosis. Each row pairs a cause with the command that confirms it is yours and the fix that resolves it. Work the table top to bottom, because the rows are ordered the way the request is evaluated: the network boundary is checked before authorization, and the model in force is checked before any individual grant.

| Cause of Forbidden | How to confirm it is yours | The fix |
| --- | --- | --- |
| Network boundary denies the caller | `properties.publicNetworkAccess` is Disabled or `networkAcls.defaultAction` is Deny and the caller is not in an allowed network or private endpoint | Add the caller's network or private endpoint, or set bypass for trusted services, rather than opening the role |
| Grant lives in the wrong access model | `enableRbacAuthorization` is true but access was added as a policy, or it is false but access was added as a role | Re-grant in the model the vault enforces, and remove the dead grant in the other model |
| Identity has no data-plane grant at all | No matching access policy entry and no role assignment with the needed data action at vault or object scope | Assign the right data-plane role or add the access policy entry for the operation |
| Control-plane role mistaken for data-plane access | Identity holds Contributor or Owner on the vault under the role-based model but no Key Vault data-plane role | Assign a data-plane role such as Key Vault Secrets User; control-plane roles do not grant secret reads |
| Wrong scope on the role assignment | Role assigned at a scope that does not cover the vault or object, confirmed by listing assignments at the vault scope | Re-assign the role at the vault scope, or at the object scope if you intend object-level access |
| Object is soft-deleted, not missing | The secret appears under deleted secrets and a normal read returns Forbidden or not found | Recover the soft-deleted object rather than creating a new one with the same name |
| Operation permission missing within a model | Access policy grants list but not get, or a narrow role grants read but not the specific data action | Add the missing operation to the policy or assign a role whose data action covers it |
| Role assignment propagation delay | Assignment exists and is correct but was created moments ago | Wait for propagation, then retry; the assignment becomes effective after the platform replicates it |

The discipline this table enforces is that you confirm before you fix. Every row has a confirming check precisely so you never apply a fix to a cause you have not verified. The most expensive Key Vault incidents are the ones where an engineer applies three fixes at once, the denial clears, and nobody knows which change mattered or whether two of them widened access for no reason.

## Cause one: the grant lives in the wrong access model

The wrong-model cause is the direct consequence of the model-in-force rule, and it is the single most common reason a correct-looking grant fails. The vault is in the role-based model, access was added as a policy, and the policy is ignored. Or the vault is in the access-policy model, access was added as a role, and the role is ignored. The confirming check is two commands: read the model, then read the grant that exists, and notice that they belong to different models.

If the vault has role-based access enabled, the access-policy list is irrelevant to the decision. Confirm whether someone added a policy that the vault is not consulting:

```bash
# Read the model
az keyvault show --name my-vault --query "properties.enableRbacAuthorization" -o tsv

# If the above is true, this policy list is being ignored for data-plane decisions
az keyvault show --name my-vault --query "properties.accessPolicies" -o json
```

When the model is true and the policy list contains your identity, you have found the cause. The fix is to grant access the way the vault evaluates it, which is an Azure role assignment carrying a data action that covers the operation. For reading and listing secret values, the built-in role is Key Vault Secrets User, assigned at the scope of the vault:

```bash
VAULT_ID=$(az keyvault show --name my-vault --query id -o tsv)

az role assignment create \
  --assignee "<principal-object-id>" \
  --role "Key Vault Secrets User" \
  --scope "$VAULT_ID"
```

After the assignment propagates, the same call that returned Forbidden succeeds. The reverse situation is just as common and is fixed in mirror image. If the vault is in the access-policy model, a role assignment does nothing for data-plane reads, and the fix is to add a policy entry for the identity and the operation:

```bash
az keyvault set-policy \
  --name my-vault \
  --object-id "<principal-object-id>" \
  --secret-permissions get list
```

Once you have re-granted in the correct model, remove the dead grant in the other model. Leaving it behind is not merely untidy; it is an audit liability, because a reviewer reading the access-policy list on a role-based vault will believe the listed identities have access when the vault is ignoring the list, and a future migration back to access policies would silently re-activate those stale grants. Cleaning up the dead grant keeps the vault's stated access and its enforced access identical, which is the property you want when someone audits the vault months from now.

### Why does adding an access policy not fix a Forbidden on an RBAC vault?

Because a vault with role-based access enabled does not consult its access-policy list for data-plane operations at all, an access policy you add to such a vault has no effect on the authorization decision. The vault evaluates Azure role assignments instead, so the Forbidden persists until you assign a data-plane role. The policy you added is real and visible, but it is being evaluated by a path the vault has switched off, which is why the change appears to do nothing.

This is the textbook expression of the model-in-force rule, and it is worth internalizing because it recurs constantly. Engineers reach for the access-policy view by habit, especially those who learned Key Vault before role-based access existed, and the access-policy view is the more discoverable of the two in the portal for older vaults. The habit is harmless until the vault has been switched to the role-based model, at which point the habitual fix becomes a no-op that wastes time and erodes confidence in the platform. The cure is the same one the whole diagnosis rests on: read the model before you grant, and grant in the model the vault enforces.

## Cause two: the identity is missing the data-plane grant entirely

The second cause is the case where no valid grant exists in either model, often because the only grant the identity holds is a control-plane role that does not extend to data-plane operations. This is the trap that catches the most experienced engineers, because the control-plane role looks generous. An identity with Contributor on the vault can change almost everything about the vault, and it is natural to assume that level of control includes reading the secrets inside it. Under the role-based model, it does not. Reading a secret value is a data-plane operation governed by data-plane roles, and Contributor is a control-plane role.

To confirm this cause, list the role assignments the identity actually holds at the vault scope and read them against what each role grants. A Contributor or Owner assignment with no Key Vault data-plane role is the signature of this cause:

```bash
VAULT_ID=$(az keyvault show --name my-vault --query id -o tsv)

az role assignment list \
  --assignee "<principal-object-id>" \
  --scope "$VAULT_ID" \
  --query "[].roleDefinitionName" \
  --output tsv
```

If that returns Contributor, Owner, or Key Vault Contributor and nothing else, the identity can manage the vault but cannot read its data. The data-plane roles are a distinct set, and choosing the right one is a least-privilege decision rather than a reflex to assign the most powerful. Key Vault Secrets User grants reading and listing of secret values, which is what an application typically needs. Key Vault Secrets Officer grants managing secrets, including writing and deleting, which a deployment pipeline that rotates secrets may need. Key Vault Crypto User grants cryptographic operations with keys without exposing the key material, which a service performing encryption or signing needs. Key Vault Certificates Officer governs certificate management. Key Vault Reader grants reading metadata about objects, not their values, and assigning it to an application that needs to read a secret value is a common near-miss that still produces Forbidden on the read because the role stops at metadata. Key Vault Administrator grants the full data plane and should be reserved for break-glass and administration, not handed to a workload.

The fix is to assign the narrowest data-plane role that covers the operation. For a workload that reads secrets, that is Key Vault Secrets User at the vault scope, or at the individual secret scope if you want the workload limited to specific objects. The identity that needs this role is usually a managed identity rather than a user, and getting that identity wired up correctly is a topic in its own right; if the managed identity itself is misconfigured, the role assignment cannot help, so it is worth confirming the identity is attached and resolvable, which the guidance on how to [set up managed identities the right way](/2023/04/17/configure-managed-identities/) walks through end to end. With the identity confirmed and the role assigned, the data-plane read succeeds.

### Does a Contributor or Owner role let me read Key Vault secrets?

No, not under the role-based model. Contributor and Owner are control-plane roles that let you manage the vault resource, change its configuration, and even delete it, but they do not grant the data-plane permission to read a secret, key, or certificate value. Reading a secret requires a data-plane role such as Key Vault Secrets User. This separation is deliberate, so that managing a vault and reading its contents are independent privileges that can be granted to different identities.

The separation has a security rationale that is worth holding onto, because it changes how you design access. If control-plane and data-plane access were the same grant, then anyone who could manage the vault could read every secret it held, which would make the most operationally necessary role also the most dangerous. By splitting them, the platform lets you give a platform team the ability to manage vaults at scale through Contributor without handing that team the contents of every application's secrets. The same split means an application identity can be given exactly the data-plane read it needs and nothing about managing the vault. Designing access around this split is the difference between least privilege and an over-broad grant that passes today and becomes an audit finding later, a theme explored further in the [Key Vault security best practices](/2024/01/15/key-vault-security-best-practices/) for hardening a vault.

A close relative of this cause is the wrong-scope assignment. A role assignment is only effective for operations within its scope, so a Key Vault Secrets User role assigned at the scope of a different vault, a different resource group, or a subscription that does not contain the vault will not authorize a read against the vault in question. The confirming check is to list assignments specifically at the vault's own scope rather than across the subscription, because a broad listing can show a role that looks right while it is anchored to a scope that does not cover the object. When the scope is wrong, re-assign at the vault scope, or at the secret's object scope if you intend to limit the identity to particular secrets.

## Cause three: the vault firewall is denying the caller

The third cause is the one that masquerades most convincingly as a permission problem, because the result is still a 403 and the caller still has, on paper, every right it needs. The difference is that the request never reaches the authorization stage. If the vault's public network access is disabled, or its network rules default to Deny and the caller's address is not in an allowed network and not arriving through a private endpoint, the vault rejects the request at the network boundary. You can assign every data-plane role in the catalog and the denial will not move, because authorization is downstream of the network check and the request never gets there.

Confirming this cause is a matter of reading the network configuration and comparing it to where the caller actually originates:

```bash
az keyvault show \
  --name my-vault \
  --query "{publicNetworkAccess:properties.publicNetworkAccess, defaultAction:properties.networkAcls.defaultAction, bypass:properties.networkAcls.bypass, ipRules:properties.networkAcls.ipRules, vnetRules:properties.networkAcls.virtualNetworkRules}" \
  --output json
```

If public network access is disabled, the vault accepts traffic only through a private endpoint, and a caller coming over the public internet is rejected regardless of its permissions. If the default action is Deny, only the addresses in the IP rules and the subnets in the virtual network rules are admitted, and a caller outside those is rejected. The bypass setting determines whether trusted Azure services are allowed through even when the default action is Deny, and a workload that relies on that bypass but is not actually a trusted service in the platform's sense will still be turned away.

The fix depends on where the legitimate caller lives and how the vault is meant to be reached. If the vault is intended to be reached privately and the caller is a workload inside a virtual network, the correct fix is a private endpoint and the matching private DNS resolution, not opening the firewall to the public internet. If the caller is a specific known address, such as a build agent with a stable egress IP, adding that address to the IP rules admits it without weakening the rest of the boundary:

```bash
az keyvault network-rule add \
  --name my-vault \
  --ip-address "203.0.113.10"
```

If the caller is a service inside a subnet that should reach the vault, add the subnet as a virtual network rule rather than an IP rule, which keeps the grant tied to the network rather than to an address that may change:

```bash
az keyvault network-rule add \
  --name my-vault \
  --subnet "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/virtualNetworks/<vnet>/subnets/<subnet>"
```

The instinct to fix a firewall denial by widening a role is the classic misdiagnosis here, and it does real damage because it broadens access that was never the problem while leaving the actual boundary in place. The discipline is to read the network configuration first, decide whether the caller is supposed to reach the vault over the path it is using, and adjust the network rule to match the intended access path rather than reaching for the authorization model at all.

### Can the Key Vault firewall cause access denied even with the right role?

Yes. The vault evaluates network rules before it evaluates authorization, so if public network access is disabled or the default network action is Deny and the caller is not in an allowed network or private endpoint, the request is rejected with a 403 before any role or policy is checked. The identity can hold every correct data-plane role and still be denied, because the denial happens at the network boundary. The fix is to admit the caller's network path, not to broaden the role.

Recognizing this cause early saves the most time, because it is the one where every authorization fix is guaranteed to fail. The tell is that the denial is total and immediate regardless of which identity calls, and that it began the moment someone hardened the vault's network posture rather than the moment someone changed a role. If the timeline of when the denial started lines up with a network change, look at the firewall before you look at anything else. The interaction between the firewall and a workload's identity is also why a managed identity that worked yesterday can fail today without any change to its roles, and that token-level sibling failure is diagnosed separately in the guidance on how to [fix managed identity token failures](/2023/01/23/fix-managed-identity-token-error/) when the identity cannot even obtain a usable token.

The private-endpoint path deserves its own attention, because it produces a network denial that looks even less like a network problem than a plain firewall block. When a vault is reached through a private endpoint, the vault's public name must resolve to the private address of that endpoint inside the calling network, which depends on a private DNS zone linked to the network and a record that points the vault name at the private address. If that DNS chain is incomplete, the vault name resolves to its public address instead, the caller's traffic goes to the public endpoint, and a vault with public network access disabled rejects it. The symptom is a 403 on every call, identical to a permission denial, while the access model and the roles are entirely correct. The confirming check is to resolve the vault's name from inside the calling network and observe whether it returns a private address or a public one:

```bash
# Run from inside the calling network (for example, an SSH session on a VM in the VNet)
nslookup my-vault.vault.azure.net
```

If that resolves to a public address rather than the private endpoint's private address, the DNS chain is broken, and the fix is in the private DNS zone and its network link rather than in the vault's access model or its firewall. Restoring the record so the vault name resolves privately routes the traffic through the private endpoint, where the vault accepts it, and the 403 clears without any change to roles or policies. Treating this as a permission problem and widening a role is the misdiagnosis that wastes the most time here, because the role was never the obstacle; the traffic was arriving at a door the vault had closed to the public.

## Cause four: the object is soft-deleted, not missing

The fourth cause is the subtlest, because the object you are trying to read genuinely is not available for reading, yet it has not been permanently removed either. Soft delete keeps a deleted secret, key, or certificate in a recoverable state for a retention period, during which the object name is reserved and the object cannot be read through the normal data path. A read against a soft-deleted object does not return the value; depending on the exact operation and configuration, it returns a not-found or a forbidden-style rejection, and an attempt to create a new object with the same name can collide with the soft-deleted one rather than succeeding cleanly. Engineers who do not know the object was deleted experience this as an access denial on a secret they can see existed, which sends them into the authorization model looking for a missing grant that is not the problem.

Confirming this cause means looking specifically at the deleted objects rather than the live ones. A live listing will not show a soft-deleted secret, so you have to query the deleted set:

```bash
az keyvault secret list-deleted \
  --vault-name my-vault \
  --query "[].{name:name, deletedDate:deletedDate, scheduledPurgeDate:scheduledPurgeDate}" \
  --output table
```

If the secret you are chasing appears in the deleted list, the access denial is a deletion in disguise, and the fix is recovery rather than a grant or a recreate. Recovering the object restores it to the live data path under its original name and version history, which is almost always what you want, because creating a new secret with the same name produces a different object with a fresh version history and breaks any reference that expected the original:

```bash
az keyvault secret recover \
  --vault-name my-vault \
  --name my-secret
```

After recovery, the object is readable again through the normal path, assuming the caller has a valid grant in the model the vault enforces. If purge protection is enabled on the vault, the object cannot be permanently purged before its retention period elapses, which is a protection against malicious or accidental destruction but also means a name stays reserved for the full retention window. Knowing whether soft delete and purge protection are on changes how you reason about a missing object, and the distinction between recovering and recreating is the practical difference between restoring service in seconds and quietly creating a second object that breaks every consumer expecting the first. The conceptual model behind soft delete and purge protection is covered in the [complete guide to Azure Key Vault](/2022/03/07/azure-key-vault-complete-guide/), which lays out the access models and the deletion lifecycle that this troubleshooting builds on.

### Why can I not access a soft-deleted Key Vault secret?

A soft-deleted secret is held in a recoverable state and is not available through the normal read path, so a read returns a not-found or forbidden-style rejection until the object is recovered. The name remains reserved during the retention period, which is why creating a new secret with the same name can collide rather than succeed. The fix is to recover the deleted object, which restores it under its original name and version history, rather than creating a replacement that would be a different object with a different lineage.

The reason this cause is so easy to misread is that the secret feels present. It was there last week, its name is familiar, and the application has always read it, so a denial on it reads as a permission regression rather than a deletion. The discipline that catches it quickly is to query the deleted set whenever a previously working secret starts returning denials with no change to the vault's access model or network posture. If the object is in the deleted list, no authorization change will help, and recovery is the only fix that restores the original object. If it is not in the deleted list, the cause is elsewhere, and you return to the model and the grants.

## Denials on keys and certificates, not just secrets

Most Key Vault denial discussions center on secrets because secrets are the most commonly read object, but keys and certificates have their own data-plane operations and their own roles, and a denial on them follows the same model-in-force rule with different operation names. A service that encrypts, decrypts, signs, or verifies using a key in the vault performs cryptographic operations, not a secret read, and those operations are authorized by a different data-plane role. Under the role-based model, Key Vault Crypto User grants the cryptographic operations a workload needs without exposing the key material itself, which is the point of keeping a key in the vault rather than in the application: the application asks the vault to perform the operation and never holds the key. A workload assigned Key Vault Secrets User but expected to wrap or sign with a key will get Forbidden on the cryptographic call, because the secrets role does not cover key operations, and the fix is to assign the crypto role rather than to widen the secrets one.

The certificate plane works the same way, with its own operations and its own officer role for management. Reading a certificate's public parts, managing its lifecycle, and reading the private key behind it are distinct operations with distinct authorization, and a denial on a certificate read names the certificate operation rather than a secret or a key operation. A subtle trap here is that a certificate stored in the vault has an associated secret and key behind it, so a workload that needs the certificate's private material may need a grant that covers the secret behind the certificate as well as the certificate object, depending on how it retrieves the material. When a certificate read fails while the certificate plainly exists, read the named operation in the error to see whether it is a certificate operation, a secret operation on the backing secret, or a key operation on the backing key, because the grant you need follows the operation the call actually makes.

The confirming check across all three object types is the same discipline applied to a different role and data action. Read the model, read the named operation in the error, and then read whether the failing identity holds a role whose data actions cover that operation at a scope that includes the object. Under the access-policy model the equivalent is to read whether the policy entry grants the specific key or certificate permission rather than only the secret permissions, because the policy permissions are granular per object type and an identity can hold full secret permissions and no key permissions at all. The cross-object lesson is that Key Vault is not one permission surface but three that share a vault, and a denial on a key or a certificate is solved by granting the right operation on the right object type, never by assuming a secrets grant covers everything the vault holds.

### Which role do I need for cryptographic operations with a Key Vault key?

For a workload that encrypts, decrypts, wraps, unwraps, signs, or verifies using a key stored in the vault, assign Key Vault Crypto User under the role-based model, which authorizes those cryptographic operations without exposing the key material. The Key Vault Secrets User role does not cover key operations, so a workload assigned only the secrets role gets Forbidden on a cryptographic call even though it can read secrets. Reserve Key Vault Crypto Officer for an identity that must create, import, or manage keys rather than only use them, and keep crypto and secret grants separate so each workload holds exactly the operations it performs. The denial on a cryptographic operation names the key operation rather than a secret read, which is the signal that you are in the crypto plane and need the crypto role, not the signal to broaden a secrets grant that was never relevant to the failing call.

## The narrower cases: operation gaps, half-migrated vaults, and cross-tenant identities

Beyond the four primary causes, a handful of narrower patterns produce a Forbidden that confuses people because the access looks almost right. The first is an operation gap within a model. Under the access-policy model, the permissions for secrets are granular, so an identity can hold list without get, which means it can enumerate the secret names but not read their values, producing a Forbidden on the read while the list succeeds. The reverse also occurs, where an identity has get for a known secret but lacks list, so a direct read of a named secret works while any code path that lists secrets first fails. The confirming check is to read the exact permissions in the policy entry and compare them to the operations the application performs:

```bash
az keyvault show \
  --name my-vault \
  --query "properties.accessPolicies[?objectId=='<principal-object-id>'].permissions" \
  --output json
```

If the policy grants list but not get, add get; if it grants get but not list, add list, but only if the application genuinely needs to enumerate, since granting list widens what the identity can discover. Under the role-based model the equivalent gap is rarer because Key Vault Secrets User covers both reading and listing of secrets, but a custom role scoped to a single data action can produce the same shape, and the fix is to assign a role whose data actions cover every operation the workload performs.

The second narrow case is the half-migrated vault. Someone began moving the vault from access policies to the role-based model, flipped the enableRbacAuthorization property to true, and either never created the corresponding role assignments or created them for some identities and not others. The vault now ignores the old access policies and authorizes only against role assignments, so any identity that was relying on a policy and never received a role is denied. The confirming check is the same model read combined with a role-assignment listing for the failing identity, and the fix is to complete the migration by assigning the data-plane roles that replace the old policies for every identity that needs access. The lesson for prevention is that a model migration is not done when the property flips; it is done when every grant that existed in the old model has an equivalent in the new one, verified per identity.

The third narrow case is a cross-tenant or wrong-tenant identity. A service principal or managed identity belongs to a specific tenant, and a vault authorizes identities from its own tenant. An application configured with credentials from a different tenant, or a token acquired against the wrong authority, can authenticate as an identity that the vault simply does not recognize, producing a denial that no in-tenant grant resolves. The confirming check is to read the tenant the failing identity actually belongs to and compare it to the vault's tenant, and the fix is to use an identity in the correct tenant or to configure the cross-tenant access path deliberately rather than assuming a grant in the vault's tenant will cover a foreign identity.

A fourth pattern worth naming is replication delay on a fresh role assignment. A role assignment that is correct in every respect still takes a short period to propagate before it becomes effective, and a retry immediately after creating the assignment can fail while a retry a few minutes later succeeds. The tell is that nothing about the configuration looks wrong, the assignment is present at the right scope with the right role, and the denial clears on its own after a brief wait. Distinguishing this from a genuine misconfiguration matters, because the wrong conclusion is to start adding more grants in response to a denial that was only ever a matter of timing.

## Reproducing the Forbidden end to end

The fastest way to internalize the model-in-force rule is to produce the denial deliberately and then clear it, because doing so once makes the diagnosis muscle memory. The reproduction is short. Create a vault in the role-based model, give an identity nothing, attempt a read, observe the Forbidden, and then grant the right role and watch the read succeed. Creating the vault with role-based access enabled sets the stage:

```bash
az keyvault create \
  --name repro-vault-$RANDOM \
  --resource-group my-rg \
  --location eastus \
  --enable-rbac-authorization true
```

With the vault in the role-based model, set a secret as the vault administrator who created it, since the creator typically holds an administrative data-plane role at the subscription or resource-group scope, then attempt to read it as a separate identity that has no data-plane grant. The read returns Forbidden, and the message names the unauthorized action over the vault scope, which is the role-based model's signature. This is the moment to read the error carefully and confirm it is an authorization verdict rather than a network rejection, because the vault was created with public access and the caller is reaching it cleanly, so the denial can only be the missing grant. Now grant the least-privilege role and retry:

```bash
VAULT_ID=$(az keyvault show --name repro-vault-XXXX --query id -o tsv)

az role assignment create \
  --assignee "<test-principal-object-id>" \
  --role "Key Vault Secrets User" \
  --scope "$VAULT_ID"

# Wait briefly for propagation, then the read that returned Forbidden now succeeds
az keyvault secret show --vault-name repro-vault-XXXX --name test-secret
```

The same reproduction in the access-policy model teaches the mirror lesson. Create a second vault without role-based access enabled, assign the same Key Vault Secrets User role to the test identity, and watch the read still fail, because the access-policy vault ignores the role. Then add the access policy with the get permission and watch the read succeed. Running both reproductions side by side burns the model-in-force rule into intuition: the identical role assignment authorizes the read on one vault and does nothing on the other, and the only difference is which model each vault enforces. After the exercise, delete the throwaway vaults so they do not linger, remembering that soft delete will hold the names for the retention period, which is itself a useful reminder of the soft-delete cause.

This kind of deliberate reproduction is exactly what a sandbox is for, since you can break and fix a vault repeatedly without touching anything that matters. Provisioning vaults in each model, triggering every cause in the denial table in turn, and applying each fix until the access path is deterministic is the practice that turns the table from a reference you look up into a diagnosis you run from memory.

## Prevention: making Key Vault access deterministic

Preventing the next Forbidden is mostly a matter of removing the ambiguity that makes the current one hard to diagnose. The largest single source of confusion is uncertainty about which model a vault enforces, so the first prevention is to standardize on one model across an environment and to make the choice explicit and visible. A team that runs every vault under the role-based model never has to ask which model a given vault uses, and a new engineer inheriting a vault can reason about access without first discovering its history. Standardizing also makes infrastructure as code cleaner, because the same grant pattern applies to every vault rather than branching on the model.

The second prevention is to define access as code rather than clicking it into the portal, because a portal grant is invisible to review and easy to apply in the wrong model, while a declared role assignment or access policy is reviewable, repeatable, and tied to the model the template sets. A Bicep snippet that both sets the model and assigns the data-plane role in one place makes the relationship between model and grant impossible to get wrong, because the same file that enables role-based access is the file that assigns the role:

```bicep
resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: vaultName
  location: location
  properties: {
    tenantId: tenant().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enableSoftDelete: true
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
  }
}

resource secretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, principalId, 'Key Vault Secrets User')
  scope: vault
  properties: {
    // Key Vault Secrets User built-in role definition ID, verify against the current catalog
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}
```

The role definition ID in that snippet is the well-known identifier for the built-in role at the time of writing, and you should verify it against the current built-in role catalog because role definitions and their identifiers are platform values that can change. Declaring the model and the grant together means a deployment can never produce a vault whose enforced model and whose grants disagree, which is the exact condition that produces the wrong-model denial.

The third prevention is least privilege expressed through the right data-plane role rather than a broad control-plane role, both because it limits exposure and because it makes denials more legible. When every workload holds exactly the data-plane role its operations require, a denial almost always means a missing or mis-scoped grant rather than a tangle of overlapping broad roles, and the diagnosis is faster. Reaching for Owner or Key Vault Administrator to clear a denial trades a quick fix today for a vault whose access is impossible to reason about tomorrow, and it is the opposite of the discipline the role split was designed to enable.

The fourth prevention is to enable and watch the vault's diagnostic logging, so that a denial leaves a record you can query rather than a mystery you reconstruct. Routing the vault's audit events to a Log Analytics workspace lets you find the exact denied operation, the caller, and the result, which collapses the diagnosis from guesswork to a query. To reproduce a denial safely and then watch it clear once the model and the grant agree, an isolated lab is the right setting, and you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to provision a vault in each model, trigger a Forbidden deliberately, and apply each fix until the access path is deterministic. A query against the audit log that surfaces denied operations gives you the signal directly:

```kql
AzureDiagnostics
| where ResourceType == "VAULTS"
| where OperationName has "Secret" or OperationName has "Key"
| where ResultType != "Success" or httpStatusCode_d == 403
| project TimeGenerated, OperationName, ResultType, httpStatusCode_d, identity_claim_oid_g, CallerIPAddress
| order by TimeGenerated desc
```

That query names the denied operation, the result, the caller's object ID, and the caller's address, which is enough to tell whether the denial is an authorization verdict or a network rejection and which identity it concerns. Column names in diagnostic tables can change as the platform evolves, so confirm the field names against the current schema if a column comes back empty. With logging in place, the next Forbidden is a query rather than an investigation.

A fifth prevention scales the discipline across an estate rather than one vault, because in any real environment the question is rarely about a single vault and usually about which of dozens enforce which model and which grants. An audit that reports each vault's model alongside its grants turns the wrong-model cause from a per-incident surprise into a standing inventory you can review. A short loop over the vaults in a subscription, reading the model for each, produces exactly that inventory and surfaces the vaults whose model and grants are likely to disagree:

```bash
for v in $(az keyvault list --query "[].name" -o tsv); do
  model=$(az keyvault show --name "$v" --query "properties.enableRbacAuthorization" -o tsv)
  net=$(az keyvault show --name "$v" --query "properties.networkAcls.defaultAction" -o tsv)
  echo "$v rbac=$model network=$net"
done
```

Reading that output, a vault reporting role-based access true with a populated access-policy list is a candidate for stale grants that will mislead an auditor, and a vault reporting access policies with role assignments attached is a candidate for the mirror confusion. Catching these in a periodic audit, rather than during an incident, is the difference between a planned cleanup and an emergency diagnosis. The audit also makes a model migration safe to plan, because you can see every vault that would need its grants re-established before the property flips.

The final prevention is a deliberate break-glass path, so that the cure for a denial is never to permanently over-grant. Reserve a high-privilege data-plane role such as Key Vault Administrator for a tightly controlled emergency identity rather than handing it to workloads, and grant it through a process that is logged and time-bounded rather than a standing assignment. When an incident tempts someone to assign Owner or Administrator to clear a denial quickly, the existence of a defined break-glass path gives them a sanctioned way to get emergency access without leaving a broad standing grant behind. The pattern that erodes a vault's security posture over time is the accumulation of broad roles assigned in the heat of incidents and never removed, and a break-glass path plus the audit above is what keeps that accumulation from happening.

## Related failures Key Vault Forbidden is confused with

A Key Vault Forbidden sits in a neighborhood of failures that look alike from the application's vantage point, because the application usually just sees that it could not get its secret. Distinguishing them matters because each has a different fix, and treating a token failure as a permission failure sends you to the access model when the real problem is upstream of authorization entirely.

The closest neighbor is a managed identity token failure. If the workload cannot obtain a token in the first place, it never reaches the vault's authorization stage, and the application's symptom can look similar to a denial because the end result is the same failure to read a secret. The difference is in the error: a token failure names the credential or the identity acquisition, while a Forbidden names the operation and the permission. The token-level failure has its own distinct causes, including an unreachable metadata endpoint, the wrong identity type configured, or a missing role on the target resource, and it is diagnosed on its own terms rather than by changing the vault's access model. When the application logs show a credential or identity error rather than a permission error, you are in token-failure territory, not Forbidden territory.

A second neighbor is an authentication failure on a service principal, where an expired secret, a certificate problem, or a wrong tenant or client ID means the principal cannot authenticate at all. Like the token failure, this happens before authorization, and its error names the credential rather than a permission. The distinction between an authentication failure and an authorization failure is the same distinction that runs through this entire diagnosis: authentication is proving who you are, authorization is being allowed to do something, and Key Vault Forbidden is always the second, never the first. If the principal cannot prove who it is, no vault grant will help.

A third neighbor is a general role-based authorization failure on a resource that is not Key Vault, which produces a similar unauthorized message but for a different action on a different resource type. The shape of the message is the same, an unauthorized action over a scope, but the action and the resource differ. Reading the action and the resource in the message keeps you from applying a Key Vault fix to a storage or a compute denial that happens to read similarly. The common thread across all of these is that the precise error text, the identity it names, and the operation it names are the cheapest and most reliable diagnostic signals you have, and reading them carefully before acting is what separates a targeted fix from a round of guessing.

For diagnosis practice that drills exactly these distinctions, working a set of denials where you have to decide whether the cause is the model, the role, the firewall, the deletion state, or a token failure builds the reflex faster than reading about it, and you can [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) that present a Forbidden and ask you to localize it before revealing the cause. The skill being built is the one the model-in-force rule names: confirm where the request is being evaluated before you change anything about how it is granted.

## Custom roles, group assignments, and the action versus data action trap

Two refinements of the role-based model produce denials that look like bugs until you understand the mechanics, and both are worth knowing because they recur in environments that have moved past the built-in roles. The first is the distinction between an action and a data action in a role definition. Control-plane permissions are expressed as actions, and data-plane permissions, the ones that authorize reading a secret or performing a cryptographic operation, are expressed as data actions. A custom role that grants a Key Vault action but no data action gives the holder control-plane management without data-plane access, which reproduces the Contributor trap in a hand-rolled role: the role looks like it grants Key Vault rights, but it never lists the data action for the operation, so the read returns Forbidden. When a custom role does not authorize a data-plane operation you expected it to, read the role definition and confirm the operation appears under data actions rather than actions, because a data-plane read is only authorized by a data action.

```bash
az role definition list \
  --name "My Custom Key Vault Role" \
  --query "[].{actions:permissions[0].actions, dataActions:permissions[0].dataActions}" \
  --output json
```

If the failing operation is a secret read and the role lists no data action covering the secret get operation, that is the cause, and the fix is to add the data action to the role definition or to assign a built-in role whose data actions cover the operation. The built-in data-plane roles exist precisely so that most teams never have to reason about data actions by hand, and reaching for them rather than a custom role is the simpler path when the built-in set covers the need.

The second refinement is group-based assignment. Assigning a data-plane role to a group rather than to each identity directly is good practice at scale, because it lets membership rather than a sprawl of individual assignments govern access, but it introduces two new ways a denial can appear correct. The first is that the failing identity is simply not a member of the group that holds the role, so the role assignment is real and at the right scope and the identity still has no effective access because it does not inherit the group's grant. The confirming check is to read the group's membership and look for the failing identity rather than reading only the role assignments. The second is membership propagation: adding an identity to a group, like creating a role assignment, takes time to become effective, so an identity added to a granting group moments before a call can still be denied until the membership replicates. The tell for both is the same as the propagation case earlier, an assignment that looks entirely correct with a denial that either persists because the identity is not actually in the group or clears on its own once membership takes effect.

Group assignment also interacts with how you read effective access, because a flat listing of an identity's direct role assignments will not show a role the identity inherits through a group. To see whether an identity has effective access through a group, you have to account for the group memberships, not just the direct assignments, which is why a denial on an identity that appears to have no roles at all can still be a group problem rather than a missing grant. The discipline that resolves both refinements is to trace the full path from the operation to the data action to the role to the assignment to the identity, including any group in the chain, rather than stopping at the first assignment that looks relevant. The full path is what the vault effectively evaluates, and reasoning about the full path is what turns a baffling denial into a located one.

### Why does my identity still get Forbidden when the group has the role?

Because the failing identity is either not a member of the group that holds the role, or its membership in that group has not yet propagated. A role assigned to a group only authorizes identities that are effective members of the group, so an identity outside the group inherits nothing from the assignment, and an identity added to the group moments ago can still be denied until the membership replicates. Confirm by reading the group's membership for the failing identity rather than reading only the role assignments, since a flat listing of direct assignments will not show a role inherited through a group. If the identity is a member and membership has had time to propagate, the role's data actions and scope are the next thing to check, tracing the full path from the operation through the data action and the role to the group and finally the identity.

## The verdict

Key Vault access denied is almost never an absence of access and almost always a mismatch between where access was granted and where the vault is looking. The model-in-force rule is the lens that resolves most of these incidents: a request is authorized only against the model the vault enforces, so the first action is to read that model, not to grant access. Once you know the model, the four primary causes are quick to separate. A network boundary that rejects the caller before authorization is checked. A grant placed in the model the vault is not using. A missing data-plane grant, often hidden behind a control-plane role that looks generous but does not extend to reading secrets. And an object that is soft-deleted rather than missing, which needs recovery rather than a grant. Each has a confirming command, and confirming before fixing is the discipline that turns an afternoon of guessing into a five-minute resolution.

The deeper lesson is the one the series returns to repeatedly: the engineer who reasons about why a service behaves the way it does solves problems the documentation never directly addresses. Key Vault separates its planes, enforces one authorization model at a time, and checks the network before it checks permissions, and every one of these design decisions has a reason rooted in security and least privilege. An engineer who holds that model can look at a Forbidden, read the error, the identity, and the operation, and know within a minute whether to look at the network, the model, the grant, or the deletion state. That is the difference between treating Key Vault as an opaque box that sometimes says no and treating it as a system whose verdicts are legible once you know what it is actually evaluating. Standardize the model, declare access as code, grant least privilege through data-plane roles, and log the denials, and the next Forbidden becomes a query with an answer rather than a mystery with a guess.

## Frequently Asked Questions

### Q: Why do I get Key Vault access denied or Forbidden when everything looks configured?

A Forbidden from Key Vault is an authorization verdict, which means the caller authenticated successfully and was then refused permission for the specific operation. The most common reason it looks configured yet still fails is that the grant exists in one authorization model while the vault enforces the other, so the vault never consults the grant you can see. Read the vault's enableRbacAuthorization property first: if it is true the vault checks Azure role assignments and ignores access policies, and if it is false it checks access policies and ignores roles. The other frequent causes are a control-plane role that does not grant data-plane reads, a network boundary that rejects the caller before authorization, and a secret that is soft-deleted rather than missing. Confirm which model the vault uses and which identity is failing before granting anything, because granting in the wrong model wastes time and leaves the real cause untouched.

### Q: How do I tell whether my Key Vault uses access policies or RBAC?

Read the vault's enableRbacAuthorization property with a single command: az keyvault show with a query on properties.enableRbacAuthorization. A value of true means the vault is in the role-based model and authorizes data-plane operations against Azure role assignments, ignoring the access-policy list entirely. A value of false or empty means the vault is in the access-policy model and authorizes against the policy list, ignoring data-plane role assignments. The two models do not blend and there is no fallback from one to the other, so this single property determines whether your fix is a role assignment or an access-policy entry. Reading it wrong sends the whole diagnosis down the wrong branch, which is why it is the first thing to check. If you inherited the vault from another team, do not assume the model from habit, because older vaults often default to access policies while newer or security-hardened vaults are frequently created with role-based access enabled.

### Q: Does a Contributor role let me read a secret in Key Vault?

No. Contributor is a control-plane role that lets you manage the vault resource, change its configuration, and even delete it, but under the role-based model it does not grant the data-plane permission to read a secret, key, or certificate value. Reading a secret requires a data-plane role such as Key Vault Secrets User, which is a separate assignment from any control-plane role. This separation is intentional, so that the ability to manage a vault and the ability to read its contents are independent privileges. A platform team can hold Contributor across many vaults to manage them without gaining access to the secrets inside, and an application identity can be given exactly the data-plane read it needs and nothing about managing the vault. If your identity holds only Contributor or Owner and still gets Forbidden on a read, that is the model working as designed, and the fix is to assign the appropriate data-plane role at the vault scope rather than broadening the control-plane role.

### Q: Which Key Vault data-plane role should I assign for an application that reads secrets?

For an application that only needs to read and list secret values, assign Key Vault Secrets User at the vault scope, or at the individual secret scope if you want the workload limited to specific objects. That role covers reading and listing secrets without granting the ability to write or delete them, which matches least privilege for a typical consumer. Reserve Key Vault Secrets Officer for an identity that must manage secrets, such as a pipeline that rotates them, because it adds write and delete. Use Key Vault Crypto User for an identity that performs cryptographic operations with keys without needing the key material, and Key Vault Certificates Officer for certificate management. Avoid assigning Key Vault Administrator to a workload, since it grants the full data plane and should be reserved for administration and break-glass. A common near-miss is assigning Key Vault Reader, which grants metadata reads but not secret values, so a read of the value still returns Forbidden.

### Q: Can the Key Vault firewall cause a 403 even when my role is correct?

Yes, because the vault evaluates network rules before it evaluates authorization. If public network access is disabled, or the network default action is Deny and the caller is not in an allowed IP range, an allowed subnet, or arriving through a private endpoint, the request is rejected at the network boundary before any role or policy is consulted. The identity can hold every correct data-plane role and still receive a 403, because the denial happens upstream of the permission check. The tell is that the denial is total and immediate for every caller and that it began when someone hardened the vault's network posture rather than when a role changed. The fix is to admit the legitimate caller's network path, by adding its IP rule, its subnet as a virtual network rule, or a private endpoint, rather than broadening the authorization model, which would widen access that was never the problem while leaving the boundary in place.

### Q: Why can I not read a secret that I know existed yesterday?

If a previously working secret starts returning denials with no change to the vault's access model or network posture, check whether the object is soft-deleted rather than missing. A soft-deleted secret is held in a recoverable state for a retention period, during which it is not available through the normal read path and its name remains reserved. A read returns a not-found or forbidden-style rejection, and creating a new secret with the same name can collide with the soft-deleted one. List the deleted secrets with az keyvault secret list-deleted, and if your secret appears there, recover it with az keyvault secret recover rather than creating a replacement. Recovery restores the original object under its name and version history, which is what consumers expect, whereas creating a new secret with the same name produces a different object with a fresh lineage that breaks any reference to the original version. If the secret is not in the deleted list, the cause is elsewhere and you return to the model and the grants.

### Q: I added an access policy but the Forbidden persists. What did I miss?

You almost certainly added the policy to a vault that has role-based access enabled, which means the vault does not consult its access-policy list for data-plane operations and the policy you added has no effect on the decision. Read the enableRbacAuthorization property: if it is true, remove your reliance on the policy and assign the data-plane role instead, such as Key Vault Secrets User at the vault scope. The access-policy view is more discoverable in the portal for older vaults and is a habitual first stop, but once a vault has been switched to the role-based model, an access-policy entry becomes a visible but inert grant. This is the textbook expression of the model-in-force rule: a grant in the model the vault does not enforce is invisible to authorization. After you grant correctly in the enforced model, remove the dead policy so the vault's stated access matches its enforced access and a future auditor is not misled.

### Q: How long does a Key Vault role assignment take to become effective?

A role assignment that is correct in every respect still takes a short period to propagate before the platform considers it effective, so a retry immediately after creating the assignment can fail while a retry a few minutes later succeeds. The tell for this cause is that nothing about the configuration looks wrong: the assignment is present at the right scope with the right role and the right principal, yet the call returns Forbidden. Distinguishing propagation delay from a genuine misconfiguration matters because the wrong response is to start adding more grants in reaction to a denial that was only ever timing. Confirm the assignment exists at the vault scope, then wait briefly and retry before changing anything else. If the denial clears on its own without further changes, it was propagation. If it persists well beyond a reasonable propagation window, look again at the scope, the role's data actions, and whether the vault is even in the role-based model.

### Q: What is the difference between control-plane and data-plane access in Key Vault?

The control plane governs the vault as an Azure resource: creating it, configuring its firewall, changing its authorization model, and deleting it. The data plane governs the objects inside the vault: reading and writing secrets, performing cryptographic operations with keys, and managing certificates. These two planes are authorized separately, through different role assignments and different evaluation paths, which is why an identity can fully manage a vault while being unable to read a single secret it holds. The separation is a deliberate security boundary, so that the operationally necessary ability to manage vaults at scale does not automatically expose every secret those vaults contain. When you diagnose a Forbidden, deciding which plane the failing operation belongs to is fundamental: reading a secret value is a data-plane operation and needs a data-plane role, so a control-plane role like Contributor, however broad, will not authorize it under the role-based model.

### Q: How do I find the exact identity that Key Vault is denying?

Read the identity named in the Forbidden message first, because it names the object ID or application ID that the vault refused, and that is the identity that actually called. The frequent surprise is that the calling identity is not the one you granted access to: a web app under a system-assigned managed identity calls as that managed identity's object ID, not as the developer or the app registration, and a workload with several user-assigned identities attached may call under a different one than you expect. Resolve the managed identity's principal ID from the resource with az webapp identity show or az identity show, then list role assignments for that exact principal at the vault scope. If the principal in the error does not match the principal you granted, the grant is on the wrong identity, and the fix is to grant the calling identity rather than the one you assumed was calling. Matching the named identity to the granted identity resolves a large share of these incidents quickly.

### Q: My managed identity cannot read a secret. Is it a Key Vault problem or an identity problem?

Read the error to decide. If the message names a permission or an operation, such as a missing secrets get permission or an unauthorized data action, the request reached the vault and was denied at authorization, so the fix is in the access model or the role. If the message names a credential or the token acquisition, such as a failure to obtain a token or an unreachable metadata endpoint, the workload never reached the vault's authorization stage at all, and the problem is in the identity rather than in Key Vault. The two failures share an end symptom, an application that cannot read its secret, but they have entirely different causes and fixes. A token failure has its own distinct causes, including the wrong identity type configured or a missing role on the target, and it is diagnosed on its own terms. Changing the vault's access model will not help a workload that cannot obtain a token in the first place.

### Q: Does Key Vault Reader let an application read secret values?

No. Key Vault Reader grants the ability to read metadata about the vault and its objects, such as the names and properties of secrets, keys, and certificates, but it does not grant the ability to read the secret value itself. An application assigned only Key Vault Reader can enumerate that a secret exists and see its attributes, yet a read of the value returns Forbidden, which is a common near-miss because the role name suggests reading and the metadata read succeeds. For an application that needs the actual secret value, assign Key Vault Secrets User, which covers reading and listing secret values. The distinction between reading metadata and reading values runs through the data-plane roles and is a deliberate part of least privilege, so that a monitoring or inventory tool can be given visibility into what a vault holds without being given the contents. When a read of the value fails while listing names works, suspect this role gap.

### Q: How do I grant access to a specific secret rather than the whole vault?

Assign the data-plane role at the scope of the individual secret rather than the vault, which limits the identity to that object. The secret's resource ID extends the vault's ID with the secrets path and the secret name, and assigning Key Vault Secrets User at that object scope authorizes reads of only that secret. This is the role-based model's expression of least privilege at the object level, and it is useful when a workload should reach exactly one secret rather than every secret the vault holds. Under the access-policy model, granularity is per-operation across the vault rather than per-object, so object-level isolation is one of the reasons teams prefer the role-based model for fine-grained access. Confirm the model is role-based first, since object-scoped role assignments only take effect when the vault authorizes against roles, and verify the assignment by listing role assignments at the secret's scope after the platform has had time to propagate it.

### Q: What does enabling diagnostic logging on Key Vault give me for troubleshooting?

Routing the vault's audit events to a Log Analytics workspace records every operation, its caller, and its result, which turns a Forbidden from a mystery you reconstruct into a query you run. A query over the diagnostic table can surface the denied operation, the result type, the HTTP status, the caller's object ID, and the caller's address, which is enough to tell whether a denial is an authorization verdict or a network rejection and which identity it concerns. That single distinction, authorization versus network, points you at either the access model or the firewall and saves the most common wasted effort. Logging also gives you a historical record, so you can correlate when a denial started with when a configuration changed, which is how you catch a denial that began the moment someone hardened the network or flipped the authorization model. Column names in diagnostic tables can change as the platform evolves, so confirm field names against the current schema if a query returns empty columns.

### Q: Why does my secret read fail with list permission but not get?

Under the access-policy model the permissions for secrets are granular, so an identity can hold list without get. List lets the identity enumerate secret names but not read their values, so any code path that reads a value returns Forbidden while the listing succeeds, which reads as a partial failure that confuses people. The reverse also happens, where an identity has get for a named secret but lacks list, so a direct read of a known secret works while any path that enumerates secrets first fails. Read the exact permissions in the policy entry for the identity and compare them to the operations the application actually performs, then add only the missing operation. Under the role-based model this particular gap is rarer because Key Vault Secrets User covers both reading and listing, but a custom role limited to a single data action can reproduce the same shape, and the fix there is to assign a role whose data actions cover every operation the workload runs.

### Q: I switched my vault to RBAC and now everything is denied. How do I recover?

Switching enableRbacAuthorization to true makes the vault ignore its access policies for data-plane operations, so every identity that was relying on a policy and never received a role assignment is now denied. This is a half-migrated vault, and the recovery is to complete the migration by assigning the data-plane roles that replace the old policies for every identity that needs access. Inventory the identities that appeared in the old access-policy list, decide the least-privilege data-plane role each one needs, and assign those roles at the vault or object scope. The lesson for next time is that a model migration is not finished when the property flips; it is finished when every grant that existed in the old model has an equivalent in the new one, verified per identity, ideally as a single change in infrastructure as code that sets the model and assigns the roles together so the two can never disagree. Until the roles are in place, the old policies are inert and the denials will persist.

### Q: Can a cross-tenant identity cause a Key Vault Forbidden?

Yes. A service principal or managed identity belongs to a specific tenant, and a vault authorizes identities from its own tenant by default. An application configured with credentials from a different tenant, or a token acquired against the wrong authority, authenticates as an identity the vault does not recognize as one of its own, producing a denial that no in-tenant grant resolves. The confirming check is to read the tenant the failing identity actually belongs to and compare it to the vault's tenant, which you can see on the vault's properties. If they differ, the fix is to use an identity in the vault's tenant or to set up the cross-tenant access path deliberately rather than assuming a grant in the vault's tenant will cover a foreign identity. This cause is easy to miss because the identity is valid and authenticates fine in its own tenant, so the denial reads as a permission gap when it is really an identity from the wrong directory.

### Q: How do I prevent Key Vault access-denied incidents from recurring?

Remove the ambiguity that makes them hard to diagnose. Standardize on one authorization model across an environment so no one has to discover which model a vault uses, and prefer the role-based model for object-level least privilege. Define access as code, setting the model and assigning the data-plane roles in the same template so the enforced model and the grants can never disagree. Grant least privilege through the narrowest data-plane role that covers each workload's operations, which both limits exposure and makes denials legible, because a denial then almost always means a missing or mis-scoped grant rather than a tangle of broad roles. Enable diagnostic logging to a workspace so the next denial is a query rather than an investigation. Finally, treat any model migration as complete only when every prior grant has an equivalent in the new model, verified per identity. These habits turn Key Vault access from a recurring mystery into a deterministic system whose verdicts you can predict and audit.

### Q: How do I verify a fix actually resolved the Forbidden?

Reproduce the exact failing call as the failing identity and confirm it now succeeds, rather than assuming the grant worked because it was created. For a managed identity workload, the most faithful verification is to trigger the application's own code path that reads the secret, since that exercises the real identity, the real network path, and the real operation together. If you need a lower-level check, acquire a token as the identity and call the data plane directly, then read the returned value or the success status. After confirming success, list the effective grant once more to document what resolved it, whether a role assignment at the vault scope, an access-policy entry, a network rule, or a recovery of a soft-deleted object, so the resolution is recorded rather than lost. Verifying by reproduction rather than by inspection catches the cases where a grant is present but at the wrong scope, in the wrong model, or against the wrong identity, which inspection alone can miss.

### Q: What is the fastest first command to run on a Key Vault Forbidden?

Read the vault's enableRbacAuthorization property, because that single value determines whether your fix is a role assignment or an access-policy entry and is the fork in the entire diagnosis. Run az keyvault show with a query on properties.enableRbacAuthorization, and in the same breath read properties.networkAcls.defaultAction and properties.publicNetworkAccess so you also know whether the network boundary could be rejecting the caller before authorization. Those two reads, the model and the network posture, eliminate the two largest sources of wasted effort: granting in the model the vault does not enforce, and granting access at all when the request is being turned away at the network. With the model known, capture the failing identity from the error message and resolve it to an object ID, then list its role assignments or the access policies at the vault scope. Three cheap reads, model, network, and the failing identity's grants, narrow almost every Forbidden to a single cause before you change anything.
