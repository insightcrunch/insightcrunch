---
layout: post
title: "Set Up Managed Identities the Right Way"
page_title: "Set Up Managed Identities in Azure: System-Assigned vs User-Assigned, Roles, and DefaultAzureCredential"
date: 2023-04-17
categories: ["Technology"]
tags: ["Azure", "Managed Identity", "Identity", "Security", "DevOps", "Cloud Computing"]
excerpt: "Set up managed identities in Azure the right way: choose the type, assign the identity, grant the least-privilege role, and select it correctly in code."
image: "/assets/images/blog/blog-15.webp"
reading_time: 63
author: "benjamin-scott"
last_updated: 2023-04-17
lang: en
---
A managed identity that exists but cannot read a single secret is the most common outcome of the first attempt, and it looks like success right up until the application throws a 403. The portal shows the toggle flipped to On, the principal has an object ID, and yet the call to Key Vault or Storage fails. This is the gap this guide closes. To set up managed identities the right way you complete two distinct actions, not one: you assign the credential to the resource, and then you grant that principal a specific role on the target it needs to reach. Skip the second action and the first looks done while nothing works. Get both right and your application authenticates to Azure without storing, rotating, or ever seeing a secret.

The reward for correct setup is concrete. The connection string with an embedded account key disappears from configuration. The certificate you used to rotate every ninety days stops being your problem. The credential that leaked in a public repository last year cannot leak again, because there is no credential to leak. What replaces all of it is a platform-issued token that Azure mints on demand, scoped to exactly the access you granted, tied to the lifecycle you chose. What breaks when the setup is wrong is equally concrete: the application authenticates fine and is still denied, because authentication and authorization are separate, and a managed identity setup that stops at authentication leaves the authorization half undone.

![Set Up Managed Identities the Right Way](/assets/images/blog/blog-15.webp)

This is the identity-then-role rule, and it is the single idea that turns a frustrating afternoon into a five-minute procedure. A managed identity becomes useful only after it is both assigned to a resource and granted the precise role on the target. Setup is therefore two steps wearing the disguise of one, and the missing role is the usual reason a correctly enabled identity still cannot do its job. Hold that rule through every section below and the failure modes stop being mysterious.

## What a managed identity actually is

A managed identity is a service principal that Azure creates and manages for you inside Microsoft Entra ID, with no secret or certificate that you ever handle. Ordinary application authentication needs a credential: a client secret, a certificate, a connection string. Every one of those is a thing that must be stored somewhere, protected, and rotated before it expires, and every one of them is a thing that can be copied. The managed identity removes the credential from the equation entirely. The platform holds the trust relationship, issues short-lived tokens to your resource when it asks, and you never see the secret because there is none to see.

Two facts about this principal matter for setup. First, it lives in your Entra tenant as a service principal with an object ID, and that object ID is what role assignments point at. Second, the token it receives is an OAuth 2.0 access token for a specific resource audience, such as `https://vault.azure.net` for Key Vault or `https://storage.azure.com` for Storage, and the application exchanges that token for access exactly as any other bearer token works. Nothing about the downstream call is special. The only special part is where the token came from, which is the platform rather than a stored credential.

Because the principal is a real Entra object, everything you already know about role assignments applies to it without modification. You assign it a role at a scope, the assignment grants the actions in that role's definition, and the principal can then perform those actions and no others. The reason a freshly enabled identity fails is never that managed identities are mysterious. It is that the role assignment, the second of the two setup steps, has not happened yet.

### What is the difference between system-assigned and user-assigned identities?

A system-assigned identity is created on and tied to a single resource, shares that resource's lifecycle, and is deleted automatically when the resource is deleted. A user-assigned identity is a standalone Azure resource with its own lifecycle that you can attach to many resources at once, so several applications can share one principal and one set of role grants.

The lifecycle difference is the one that drives the choice. A system-assigned identity cannot outlive its host and cannot be reused by anything else, which makes it the clean default for a single workload that owns its access. A user-assigned identity persists independently of any resource you attach it to, survives the deletion of those resources, and carries its role assignments with it, which makes it the right tool when a fleet of resources should all authenticate as the same principal or when you want the access grants in place before the compute that uses them exists.

## The identity-then-role setup checklist

Every correct managed identity setup walks the same five steps in the same order, and naming them as a checklist makes the gotchas impossible to forget. This is the InsightCrunch managed-identity setup checklist, the findable artifact this guide is built around. Each row carries the decision you make at that step and the mistake that most often breaks it.

| Step | What you decide | Action | The gotcha that breaks it |
|------|-----------------|--------|---------------------------|
| 1. Choose the type | System-assigned or user-assigned | Reason from lifecycle and sharing, not habit | Reaching for user-assigned everywhere when one resource owns the access |
| 2. Assign the credential | Which resource gets it | Enable system-assigned, or attach a user-assigned identity | Assuming the toggle alone grants access |
| 3. Grant the role | Which role at which scope | Assign a data-plane role on the specific target | Skipping the role, or granting Owner instead of a data role |
| 4. Select it in code | Which identity the code uses | Use DefaultAzureCredential, set the client ID when ambiguous | Multiple user-assigned identities with no client ID specified |
| 5. Verify | That the token and the access both work | Acquire a token, list the role assignment, make the call | Declaring victory at the toggle without testing the call |

The order is not cosmetic. The role grant in step three needs the principal that step two produces, the code in step four needs to know which identity to ask for when step one chose user-assigned and more than one is attached, and the verification in step five is the only thing that tells you the whole chain holds. Most failures trace to a step that was skipped because it looked optional. None of the five is optional.

### Why is enabling the principal not enough on its own?

Enabling a principal creates the principal and gives the resource a way to request tokens, but it grants no access to anything. Authentication and authorization are separate concerns: the credential proves who the caller is, and the role assignment decides what that caller may do. Without a role on the target, the token is valid and the call is still denied.

## Step one: choosing the identity type

The type choice is the first decision because it shapes every step after it, and the honest version of the decision is shorter than the documentation makes it look. Ask one question: does exactly one resource own this access, and should that access disappear when the resource does? If yes, system-assigned is the simpler and safer answer. If several resources need to act as the same principal, or the access must exist independently of any single resource, user-assigned is the answer. Everything else is a refinement of those two cases.

System-assigned earns its place when a workload is self-contained. A single web application that reads its own secrets from one vault has no reason to share a principal with anything, and tying the principal to the application's lifecycle means the cleanup happens for free: delete the app, and its principal and the trust relationship vanish with it, leaving no orphaned principal to audit later. The cost is that the principal is born with the resource, so you cannot grant it a role before the resource exists, and you cannot move it.

User-assigned earns its place the moment sharing or pre-provisioning enters the picture. A scale set whose instances come and go cannot rely on a per-instance system-assigned identity if you want stable, pre-granted access, because each new instance would need its own grants; one user-assigned identity attached to the set gives every instance the same principal and the same access with a single role assignment. A platform team that wants to grant access to a vault before the consuming applications are deployed creates the user-assigned identity and its role assignments first, then hands the principal's resource ID to each team to attach. A blue-green or slot-based deployment that must keep the same access across swaps benefits from a principal that does not change when the compute does.

### When should I use user-assigned over system-assigned?

Use user-assigned when more than one resource must authenticate as the same principal, when access must be granted before the consuming resource exists, or when the access should survive the resource being replaced. Use system-assigned for a single self-contained workload that owns its access, because tying the credential to the resource lifecycle keeps cleanup automatic and avoids orphaned principals.

The counter-reading worth engaging is the reflex to standardize on user-assigned for everything. It is a defensible policy in a large estate where central teams own principals and role grants, and it does remove the can't-grant-before-it-exists limitation. The trade-off is that user-assigned identities do not clean themselves up. Delete a hundred applications that each used the same convenient user-assigned identity and you are left with a live principal holding real role assignments that nothing uses, which is exactly the kind of standing access a security review flags. The right policy names the cases for each type rather than collapsing both into one. The hands-on Azure labs and command library on [VaultBook](https://vaultbook.org/tools/azure-labs.html) let you create both types against a sandbox subscription and watch the lifecycle difference directly, which is the fastest way to make the distinction stick before you apply it to production.

## Step two: assigning the principal to the resource

Assigning is the step that creates or attaches the principal, and the commands differ slightly by resource type while the shape stays the same. For a system-assigned identity you enable it on the resource and Azure creates the principal in your tenant. For a user-assigned identity you create the identity resource once and then attach it, by resource ID, to as many resources as you like.

Enabling a system-assigned identity on a web app is a single command, and the output you care about is the principal ID it returns, because that is the value step three will grant a role to.

```bash
# Enable a system-assigned identity on an App Service web app
az webapp identity assign \
  --name myapp \
  --resource-group myapp-rg

# The response includes the principalId you will grant a role to:
# {
#   "principalId": "11111111-1111-1111-1111-111111111111",
#   "tenantId":    "22222222-2222-2222-2222-222222222222",
#   "type":        "SystemAssigned"
# }
```

The same pattern applies across the compute services, with only the command group changing. A virtual machine uses `az vm identity assign`, a virtual machine scale set uses `az vmss identity assign`, a Function App uses `az functionapp identity assign`, and a Container App uses `az containerapp identity assign`. In every case the system-assigned form needs no extra arguments beyond the resource, and the principal ID in the response is the handle for the role grant.

A user-assigned identity is created as its own resource first. The create command returns three values that each have a distinct job: the `principalId` is the object the role assignment targets, the `clientId` is what your code uses to disambiguate which identity to request a token for, and the `id` is the full resource ID you use to attach the credential to compute.

```bash
# Create a user-assigned identity once
az identity create \
  --name myapp-uami \
  --resource-group identity-rg

# Returned values and what each one is for:
#   principalId : grant roles to THIS value
#   clientId    : select THIS identity in code when several are attached
#   id          : attach THIS resource ID to compute

# Attach the user-assigned identity to a web app (by resource ID)
az webapp identity assign \
  --name myapp \
  --resource-group myapp-rg \
  --identities "/subscriptions/<sub>/resourceGroups/identity-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myapp-uami"
```

You can attach the same user-assigned identity to a second and third resource with the same `--principals` argument, and all of them then authenticate as the one principal with the one set of role grants. That sharing is the entire point of the type, and it is why a single role assignment on the principal covers every resource you attach it to.

### How do I attach a managed identity to an AKS cluster or workload?

For pulling images, attach a user-assigned identity as the cluster's kubelet identity and grant it AcrPull on the registry. For pod-level access to Azure resources, enable workload identity on the cluster, create a user-assigned identity, add a federated credential that trusts the cluster's service account, and annotate the Kubernetes service account with the principal's client ID.

AKS is the one place where the assignment story has an extra layer, because a pod is not an Azure resource and cannot hold an Azure identity directly. Workload identity federation bridges that gap: the user-assigned identity trusts tokens issued by the cluster's OIDC issuer for a specific Kubernetes service account, so a pod running under that service account exchanges its projected token for an Azure access token. The setup is still the same five steps in spirit, with the federated credential standing in for the direct attachment, and the client ID annotation on the service account playing the role that the client ID plays in code elsewhere. The link to [configure-managed-principals for the identity model](/2023/04/17/configure-managed-principals/) that other cluster guides point at is this same procedure seen from the cluster side.

## Step three: granting the least-privilege role on the target

This is the step that the toggle hides and the step that, when skipped, produces the denied call that sent most readers to this guide. Granting a role takes the principal ID from step two and assigns a role definition at a scope, and the two decisions that matter are which role and at which scope. Get both narrow and you have least privilege. Get either wide and you have handed a workload more reach than it needs.

The role should be a data-plane role specific to the action, not a management role. To read secrets from Key Vault the credential needs Key Vault Secrets User, not Contributor and certainly not Owner. To read blobs it needs Storage Blob Data Reader, and to write them Storage Blob Data Contributor. These data roles grant the data actions and nothing more; the management roles grant control over the resource itself, which is almost never what an application needs and is exactly what a least-privilege review will challenge. The relationship between the role you pick and the actions it carries is the subject of [azure-rbac-vs-abac-explained for the role grant](/2024/01/01/azure-rbac-vs-abac-explained/), and it is worth understanding the action-level detail rather than copying a role name.

The scope should be the specific target, not the resource group and not the subscription. Grant Key Vault Secrets User on the one vault the application reads, not on the resource group that happens to contain five vaults. Scope is the difference between a principal that can read one vault and a principal that can read every vault you ever put beside it, and the narrow scope costs nothing extra to set.

```bash
# Grant the identity a data-plane role on the specific target vault.
# Use --assignee-object-id with the principal type to avoid a Graph lookup
# and the propagation race that --assignee sometimes hits.
az role assignment create \
  --assignee-object-id "11111111-1111-1111-1111-111111111111" \
  --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/<sub>/resourceGroups/myapp-rg/providers/Microsoft.KeyVault/vaults/myapp-kv"
```

The `--assignee-object-id` plus `--assignee-principal-type ServicePrincipal` form is deliberate. The plain `--assignee` argument asks Microsoft Graph to resolve the value to an object, and for a brand-new managed identity that has not finished replicating, the resolution can fail with a confusing error that looks like the principal does not exist. Passing the object ID directly with the principal type skips the lookup and avoids the race. This single detail prevents one of the most-reported setup failures, where the role assignment command errors out on a principal you can plainly see in the portal.

### Why does the credential still get a 403 after I enabled it?

Because enabling the principal completed authentication but not authorization. The token the resource receives is valid, but the target has no role assignment for that principal, so the data plane denies the call. The fix is the role grant from this step: assign the specific data-plane role at the target's scope, then wait for propagation before retrying.

Two timing facts save real debugging time here. A role assignment is not always instant; propagation across the platform can take a few minutes, so a call that fails immediately after the grant and succeeds a few minutes later was never broken, it was early. And a token is cached, so if your application acquired a token before the grant, it may keep using the old token's authorization view until the token is refreshed. When a grant looks like it did not take, give it a few minutes and a fresh token before assuming the assignment is wrong. The failure that survives both of those is the one to investigate, and it is usually a scope or role mismatch rather than a missing assignment, which is the territory of [fix-managed-identity-token-error for the failure mode](/2023/01/23/fix-managed-identity-token-error/).

The over-granting trap deserves its own warning, because it is the mistake that passes every functional test and fails every security review. Owner works. Contributor works. They both make the 403 disappear, which is exactly why people reach for them when they are tired of fighting the setup. They also grant the workload the ability to delete the resource, change its access policies, and reassign roles, none of which the application will ever do and all of which an attacker who compromises the application now can. The narrow data role does the same functional job with none of that blast radius. The discipline of granting the smallest role that makes the call succeed is the entire security value of managed identities, and throwing it away with a broad grant keeps the convenience while discarding the protection.

## Step four: selecting the credential in code

With the principal assigned and the role granted, the application has to actually ask for a token, and the recommended way is the credential chain that the Azure SDKs ship, exposed as `DefaultAzureCredential`. This type resolves a credential by trying a sequence of sources in order and using the first that succeeds, which is what lets the same code authenticate as a managed identity in Azure and as your developer account on your laptop with no code change between the two.

The resolution order is the part worth knowing, because it explains both the production behavior and the local-development behavior. The chain tries environment variables first, then a workload identity credential, then the managed identity, and then, when none of those are present, it falls back to developer credentials such as the Azure CLI login, Azure PowerShell, and the Azure Developer CLI. In Azure, the resource has a managed identity and no developer login, so the chain lands on the managed identity. On your machine, there is no managed identity but there is an `az login` session, so the same chain lands on your account. One credential object, two environments, no branching.

```csharp
// The same code authenticates as a managed identity in Azure
// and as your az login session on a developer machine.
using Azure.Identity;
using Azure.Security.KeyVault.Secrets;

var client = new SecretClient(
    new Uri("https://myapp-kv.vault.azure.net/"),
    new DefaultAzureCredential());

KeyVaultSecret secret = await client.GetSecretAsync("db-password");
string value = secret.Value;
```

```python
# The Python equivalent: identical pattern, identical resolution chain.
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://myapp-kv.vault.azure.net/",
    credential=credential)

secret = client.get_secret("db-password")
value = secret.value
```

The single most common code-side failure has nothing to do with the role and everything to do with ambiguity. When a resource has exactly one principal, the chain knows which one to use. When a resource has a system-assigned identity and one or more user-assigned identities attached at the same time, the managed-identity step of the chain cannot guess which one you mean, and the token request either fails or, worse, succeeds against the wrong principal that happens to lack the role, producing a 403 that looks like a missing grant when the real problem is the wrong identity. The fix is to name the credential explicitly by its client ID.

```csharp
// When several identities are attached, name the one to use by client ID.
var credential = new DefaultAzureCredential(
    new DefaultAzureCredentialOptions
    {
        ManagedIdentityClientId = "33333333-3333-3333-3333-333333333333"
    });
```

The client ID you pass is the `clientId` value from the `az identity create` output in step two, not the principal ID and not the resource ID. Confusing the three identifiers is its own small category of bug: the principal ID is what you grant roles to, the client ID is what code selects with, and the resource ID is what you attach to compute. They are three different GUIDs (the resource ID a path, the other two GUIDs) for three different jobs, and using one where another belongs produces errors that read as access problems but are really identity-selection problems.

### How does DefaultAzureCredential know which identity to use?

It walks a fixed chain of credential sources and uses the first that works. In Azure that is the managed identity; on a developer machine it is your CLI login. When a resource has more than one principal attached, the chain cannot choose for you, so you set the client ID, either through the credential options in code or the `AZURE_CLIENT_ID` environment variable.

There is also an environment-variable path that avoids touching code at all. Setting `AZURE_CLIENT_ID` to the user-assigned identity's client ID tells the managed-identity step of the chain which identity to use, which is convenient when you want the same compiled application to target different principals across environments by configuration rather than by rebuild. App Service and Functions expose this through application settings, so the principal selection becomes a deployment-time setting rather than a code constant, which is the cleaner pattern for anything that ships to more than one stage.

## Step five: verifying that it worked

Verification is the step people skip because the application either works or it does not, but skipping it means you only learn the setup was wrong when production traffic finds the gap. A two-minute verification pass confirms each link of the chain independently, so when something is wrong you know which link, not just that the whole thing failed.

The first check confirms the credential exists and is attached. Listing the principal on the resource shows the system-assigned principal ID and any attached user-assigned identities, and if the list is empty, step two never completed regardless of what the portal toggle suggested.

```bash
# Confirm what identities are actually attached to the resource
az webapp identity show \
  --name myapp \
  --resource-group myapp-rg
```

The second check confirms the role assignment exists at the scope you expect. Listing assignments filtered to the principal shows every role it holds and where, and this is where a missing grant, a wrong role, or a too-broad scope becomes visible at a glance.

```bash
# Confirm the role assignment exists, with its role and scope
az role assignment list \
  --assignee "11111111-1111-1111-1111-111111111111" \
  --all \
  --output table
```

The third check confirms the resource can actually acquire a token, which proves the platform side of the chain works before any application code runs. From inside the resource, the identity endpoint issues a token for a requested audience, and a successful response with an `access_token` field means the metadata service, the credential, and the audience are all in order. On a virtual machine this is the instance metadata service at `169.254.169.254`; on App Service and Functions it is the identity endpoint exposed through environment variables rather than that IP, which is a difference that trips people who copy the VM command into a web app and watch it time out.

```bash
# From inside an Azure VM: ask the instance metadata service for a token.
# A response with an access_token proves the platform side of the chain works.
curl -s -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://vault.azure.net"
```

When all three checks pass and the application still fails, the problem has moved out of setup and into the call itself: the wrong vault name, the wrong audience, a network path that blocks the data plane, or a firewall on the target. That narrowing is the value of verifying in pieces. The scenario-based troubleshooting drills on [ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) walk through exactly this kind of isolate-the-failing-link diagnosis with managed identity scenarios, which is useful practice for the times the failure is not in the obvious place, and the command library on [VaultBook](https://vaultbook.org/tools/azure-labs.html) keeps the token-acquisition and role-listing commands above in a form you can run against your own resource without retyping them.


## The settings the defaults get wrong

Some of the worst managed identity setups are not missing a step but accepting a default that quietly does the wrong thing, and these are harder to catch because nothing errors out. The configuration looks complete and behaves badly only later, when a security review, a multi-environment deployment, or an incident exposes the gap.

The first default worth challenging is the assignee resolution behavior of the role assignment command, covered above but worth restating as a setting choice. Letting the command resolve the principal through Graph is the path of least typing and the path that races against replication. Choosing the object-ID form is a small habit that removes a whole class of intermittent failure, and it costs one extra argument. Make it the default in your own scripts and templates and the new-identity propagation error stops appearing.

The second default is the audience and scope of the token your code requests, which the SDK usually handles correctly but which becomes a setting the moment you request tokens directly. The token is for a specific resource audience, and a token minted for `https://management.azure.com` will not work against `https://vault.azure.net` no matter how correct the role assignment is, because the audience in the token does not match the resource validating it. When a direct token call returns a token that the data plane still rejects, the audience is the first thing to check, and it is a configuration value, not a permission.

The third default is the slot story on App Service. Deployment slots each have their own identity surface, and a system-assigned identity enabled on the production slot does not automatically exist on a staging slot, nor does a slot inherit the role assignments of the slot it was cloned from in the way people expect. A setup that works in production and fails after a slot swap is almost always a principal or role that lived on one slot and not the other. The repeatable fix is to provision the principal and its grants for every slot the application runs in, or to use a user-assigned identity attached to each slot so the principal and its access stay constant across swaps, which is one of the cleanest arguments for user-assigned in a slot-heavy deployment.

The fourth default is the credential chain's reach in local development, which is a convenience until it becomes a confusion. The same chain that falls back to your CLI login also means that a developer who is logged in with a highly privileged account will see the application succeed locally with access the production identity does not have, masking a missing role grant until the code reaches Azure. The discipline that prevents this is to grant your developer account the same narrow roles the managed identity will have, so local success predicts production success rather than overstating it. Testing against the real permission set, not your personal admin reach, is what makes the local-development convenience trustworthy.

### Which role should a managed identity get for Key Vault and Storage?

For Key Vault under RBAC, grant Key Vault Secrets User to read secrets, Key Vault Certificate User for certificates, and Key Vault Crypto User for keys. For Storage, grant Storage Blob Data Reader to read blobs and Storage Blob Data Contributor to write them. Use these data-plane roles at the specific resource scope, never Owner or Contributor.

The data-role-versus-management-role distinction is the one that most often gets collapsed under time pressure, and naming the correct roles explicitly removes the temptation to reach for a broad role just to make progress. Key Vault in particular has two access models, the older access policies and the newer RBAC, and a vault configured for RBAC ignores access policies entirely, so a team that grants an access policy on an RBAC vault watches the access do nothing and reasonably concludes managed identities are broken. They are not; the grant landed in the wrong model. The full treatment of that two-model behavior lives in [azure-key-vault-complete-guide for the access model](/2022/03/07/azure-key-vault-complete-guide/), and it is the most common reason a Key Vault grant appears to be ignored.

## Common misconfigurations and their symptoms

Setup failures cluster into a small number of patterns, and recognizing the symptom is most of the diagnosis. The table below maps each recurring misconfiguration to what it looks like from the application's side and the fix that resolves it, so a symptom in production points straight at the step that needs attention.

| Symptom | Likely cause | The fix |
|---------|-------------|---------|
| 403 on a target right after enabling the credential | No role granted on the target (step three skipped) | Assign the specific data-plane role at the target scope |
| 403 that persists a few minutes after a correct grant | Token cached from before the grant, or propagation lag | Refresh the token; wait a few minutes for the assignment to replicate |
| Token request fails with multiple principals attached | Ambiguous identity, no client ID specified | Set ManagedIdentityClientId or AZURE_CLIENT_ID to the right client ID |
| Works in production, fails after a slot swap | Identity or role present on one slot only | Provision the principal and grants per slot, or use a user-assigned identity |
| Grant on a Key Vault appears ignored | Access policy set on an RBAC-mode vault | Grant an RBAC data role instead of an access policy |
| Role assignment command errors on a visible identity | Graph resolution racing replication | Use --assignee-object-id with --assignee-principal-type ServicePrincipal |
| Token acquired but data plane still rejects it | Wrong audience requested for the target resource | Request the token for the target's audience |
| Local success but Azure failure | Developer account has access the credential lacks | Grant the developer account the principal's narrow roles |

The pattern across the table is that almost none of these are bugs in managed identities and almost all of them are a setup step that was skipped, mistimed, or aimed at the wrong place. That is the encouraging news: the technology is reliable, and the failures are procedural, which means a checklist beats a guess every time. When a symptom does not match any row, the diagnosis moves to the token level, where the question becomes whether the resource can acquire any token at all, and that is the boundary where setup ends and the token-failure investigation begins.

### Can multiple resources share one managed identity?

Yes, and that is the defining capability of a user-assigned identity. Create the principal once, grant it the roles it needs, and attach it to as many virtual machines, web apps, function apps, or scale sets as should authenticate as the same principal. A single role assignment on the shared identity then covers every resource attached to it.

Sharing a principal is powerful and worth a deliberate boundary. Every resource attached to a shared identity has exactly the access that principal holds, so the role grants must be the union that every consumer needs and no more, and any consumer that needs less is over-privileged by the sharing. The clean pattern is to share a principal among resources that genuinely have the same access needs, such as the instances of one scale set or the slots of one application, and to give a resource its own identity when its access profile differs. Convenience that bundles unlike workloads under one over-broad identity recreates the over-granting problem at the credential level rather than the role level.

## Local development and the credential chain

The credential chain's local behavior is a feature designed to make the secretless pattern work on a laptop, and understanding it removes the most common what-do-I-do-locally question. Because `DefaultAzureCredential` falls back to your developer sign-in when no managed identity is present, the answer to running the application locally is usually nothing special: sign in with `az login`, ensure your account holds the roles the application needs, and the same code that uses the managed identity in Azure uses your account on your machine.

```bash
# Local development: sign in, and DefaultAzureCredential uses this session.
az login

# Confirm which account the chain will authenticate as locally
az account show --output table
```

The refinement worth applying is matching your local permissions to the production identity's permissions rather than relying on whatever your account already has. A developer whose account is Owner on the subscription will never see a missing role grant locally, because their account can do everything, and the gap only surfaces when the code reaches Azure and authenticates as the narrowly scoped managed identity. Granting your account the same data roles the principal will hold, at the same scopes, makes local development a faithful preview of production behavior, so a permission problem shows up on your machine where it is cheap to fix rather than in a deployed environment where it is not.

For teams that want local development to use a specific identity rather than the developer's account, the environment-variable path gives a clean override. Setting the variables that the chain reads first lets a local run authenticate as a service principal or a chosen identity, which is occasionally necessary when the developer's own account genuinely cannot be granted the access the application needs. That path is heavier than the default and should be the exception, because the whole appeal of the chain is that most local development needs no special configuration at all.

The contrast that makes the secretless pattern obvious is the path it replaces. The older approach to identity in code stored a client secret or a certificate, read it from configuration, and presented it to Entra to get a token, which meant the secret lived somewhere on disk or in a config store, had to be protected, and had to be rotated before it expired. The managed identity removes every part of that. The comparison of when a secret-bearing service principal still has a place and when a managed identity replaces it is the subject of [managed-identity-vs-service-principal for the choice](/2024/01/08/managed-identity-vs-service-principal/), and for any workload running on Azure compute the managed identity is the default that should need a reason to deviate from.

## Making the configuration repeatable as code

A managed identity setup done by clicking is a setup you will do again, slightly differently, in the next environment, and the drift between a hand-clicked production and a hand-clicked staging is where the slot-swap and works-here-not-there failures come from. Expressing the whole setup as code makes it identical across environments by construction, and Bicep expresses all five checklist steps in a form you can review and redeploy.

The pattern below provisions a user-assigned identity, attaches it to a web app, and grants it a data-plane role on a vault, with the role assignment using the principal's principal ID so the grant and the credential are deployed together and never drift apart. The role definition is referenced by its well-known GUID, which is how the platform names built-in roles independently of their display strings.

```bicep
// A user-assigned identity, attached to a web app, granted Key Vault
// Secrets User on a specific vault. All three steps in one deployment.

param location string = resourceGroup().location

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'myapp-uami'
  location: location
}

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: 'myapp-kv'
}

// Key Vault Secrets User built-in role definition ID
var secretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, uami.id, secretsUserRoleId)
  scope: vault
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions', secretsUserRoleId)
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource site 'Microsoft.Web/sites@2023-01-01' = {
  name: 'myapp'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uami.id}': {}
    }
  }
  properties: {}
}
```

Three details in that template carry weight. The role assignment sets `principalType: 'ServicePrincipal'` for the same reason the CLI used `--assignee-principal-type`: it tells the platform the principal is a service principal and avoids the replication race that an unqualified assignment can hit during a fresh deployment. The assignment's name uses a `guid()` derived from the scope, the principal, and the role, which makes the assignment idempotent so redeploying the template does not create duplicate assignments or fail on a name collision. And the role is referenced by its built-in GUID rather than its display name, because the GUID is stable while display strings are not the identifier the platform matches on.

Expressing the setup this way also makes the least-privilege grant auditable, because the role and scope are written down in a file that goes through review rather than living only in the access state of a resource. A reviewer can see that the application gets Secrets User on one vault and nothing else, and a change that widens that grant shows up as a diff. That visibility is the IaC dividend that matters most for identity: the access an application holds becomes a reviewed artifact instead of an after-the-fact discovery. The Bicep and Terraform examples in the command library on [VaultBook](https://vaultbook.org/tools/azure-labs.html) cover the same identity-attach-and-grant pattern across more resource types, which is the fastest way to adapt this template to a function app, a scale set, or a container app without rederiving the structure.

## Choosing the type in real scenarios

The type decision reads cleanly in the abstract and gets muddier against real workloads, so working through the recurring cases makes the rule concrete. Each scenario below is a pattern engineers report, with the setup that fits it.

A single web application reading its own secrets from one vault is the textbook system-assigned case. One workload owns the access, the access should die with the application, and there is nothing to share, so the system-assigned identity is the least-effort and least-residue choice. Enable it, grant Secrets User on the vault, and you are done, with no standalone identity resource to track and no orphan to clean up later.

A virtual machine scale set whose instances scale in and out needs stable access that does not depend on which instances currently exist, which is the user-assigned case. A single user-assigned identity attached to the scale set gives every instance, present and future, the same principal and the same grants, so a new instance is authorized the moment it joins without any per-instance setup. Trying to use system-assigned identities here means each instance has its own principal and would need its own grants, which does not scale with an autoscaling set.

A platform team that wants to grant a vault role before the consuming application is deployed has chosen user-assigned by necessity, because a system-assigned identity cannot be granted a role before its resource exists. The team creates the user-assigned identity and its role assignments first, hands the principal's resource ID to the application team, and the application is authorized from its first deployment. This pre-provisioning is one of the strongest arguments for user-assigned in an organization that separates platform and application ownership.

A blue-green deployment that swaps between two compute environments wants the access to stay constant across the swap, which favors a principal that is not tied to either environment's lifecycle. A user-assigned identity attached to both sides means a swap changes the running compute without changing the principal or its grants, so there is no window where the newly live environment lacks access because its system-assigned identity was never granted the role.

A fleet of microservices that all read from the same configuration vault could share one user-assigned identity, and whether they should is the judgment call. If every service genuinely needs the same access, sharing one principal and one grant is clean and auditable. If the services have different access needs, sharing forces the credential to hold the union of all of them, over-privileging every service that needs less, and the cleaner design gives each service its own identity scoped to its own needs. The sharing capability is a tool, not a default, and the right use of it is for resources with genuinely identical access profiles.

### Does deleting the resource delete its managed identity?

A system-assigned identity is deleted automatically with its resource, including its role assignments, which is why it leaves nothing to clean up. A user-assigned identity is independent and survives the deletion of any resource it was attached to, along with its role assignments, so it must be deleted explicitly when it is no longer needed to avoid leaving a standing principal with live access.

That cleanup difference is the quiet long-term cost of standardizing on user-assigned, and it is worth designing for rather than discovering. An estate that creates a user-assigned identity per application and never deletes the principals accumulates principals that hold real role assignments and map to applications that no longer exist, which is precisely the standing-access finding that audits flag. Whichever type a team standardizes on, the lifecycle has to be owned: system-assigned outsources the cleanup to the resource deletion, and user-assigned makes the cleanup an explicit responsibility that has to be assigned to someone or automated.

## How the token actually reaches your code

Understanding where the token comes from turns the most opaque failures into readable ones, because almost every token-side problem is a problem with one specific hop in a short chain. When your code calls a managed identity, it does not contact Microsoft Entra directly. It contacts a local endpoint on the resource, and that endpoint, trusted by the platform, contacts Entra on the resource's behalf and returns a token. The endpoint differs by host type, and that difference is the source of a recurring confusion.

On a virtual machine and a scale set, the endpoint is the instance metadata service, reachable at the link-local address `169.254.169.254`. A request to its token path, carrying the `Metadata: true` header and a `resource` query parameter for the audience, returns an access token for that audience. The address is not routable off the host, which is by design: only code running on the virtual machine can ask the metadata service for that machine's identity, so the token cannot be requested from anywhere else.

On App Service, Functions, and Container Apps, the endpoint is not the metadata IP. The platform injects two environment variables, `IDENTITY_ENDPOINT` and `IDENTITY_HEADER`, and the token request goes to the URL in `IDENTITY_ENDPOINT` carrying the value of `IDENTITY_HEADER` as a header that authenticates the request to the local endpoint. Code that hardcodes the `169.254.169.254` address into a web app, copied from a virtual machine example, will hang or time out, because that address is not where a web app's identity endpoint lives. This is the single most common reason a token call that works on a virtual machine fails on App Service, and the fix is to read the endpoint from the environment rather than assume the metadata IP.

```bash
# On App Service or Functions, the identity endpoint comes from env vars,
# NOT from 169.254.169.254. The SDKs read these for you.
curl -s -H "X-IDENTITY-HEADER: $IDENTITY_HEADER" \
  "$IDENTITY_ENDPOINT?resource=https://vault.azure.net&api-version=2019-08-01"
```

The Azure SDKs hide this difference, which is the main reason to use them rather than call the endpoint by hand. The managed-identity step of the credential chain detects the host type, reads the environment variables when they are present, and falls back to the metadata service when they are not, so the same SDK call works on a virtual machine and a web app without the caller knowing which endpoint answered. When you do call the endpoint directly, for a diagnostic or a language without an SDK, reading the host type correctly is the detail that separates a working call from a timeout.

### What is the audience and why does the wrong one cause a 401?

The audience is the resource the token is minted for, such as the Key Vault data plane or the Storage data plane, and it is embedded in the token. A target validates that the token's audience matches itself, so a token requested for the management plane and sent to the Key Vault data plane is rejected with a 401 even when the role assignment is correct, because the token is for the wrong audience.

The audience trips people because it is invisible until you decode the token, and a 401 with a correct role assignment sends people to re-check the role, which is fine, when the real problem is upstream of the role entirely. A token carries an `aud` claim, and the resource validates it before it ever checks what the principal is allowed to do. If the audience is wrong, the token never reaches the authorization check, so widening the role does nothing. The SDK clients set the right audience for their target automatically, so this failure mostly appears in hand-rolled token requests where the `resource` parameter was set to the management endpoint out of habit. Decoding the token and reading its `aud` claim is the fastest way to confirm the audience, and it is a thirty-second check that saves a long detour through the role assignments.

Token caching is the other token-side behavior that explains a class of confusing timing. The SDK caches an acquired token until shortly before it expires and reuses it, which is correct and efficient, and it means a role granted after the token was acquired does not take effect until the token is refreshed. A workload that started, acquired a token, and then received its role grant will keep being denied with a cached token that predates the grant, and the denial clears on the next refresh or a restart. When a grant looks like it landed but the application still fails, forcing a fresh token, by restarting the workload or waiting out the cache, is the check that separates a real authorization gap from a stale-token artifact.

## Auditing who used the principal and what it touched

A managed identity is a real principal, which means its activity is visible in the same logs that show any sign-in and any control-plane operation, and knowing where to look turns the credential from an opaque service account into an auditable actor. Two log sources answer the two questions an operator asks: who signed in as this principal, and what did this principal do.

The Entra sign-in logs include managed identity sign-ins as a distinct category, separate from interactive user sign-ins, and they record each time the principal acquired a token, the resource it requested the token for, and whether the acquisition succeeded. Filtering the managed-identity sign-in category to a specific identity shows its token-acquisition history, which answers whether the credential is being used at all, which resources it is reaching, and whether any acquisitions are failing in a way that points at a configuration problem rather than an application bug. An identity that shows no sign-ins is a principal nothing is using, which is a cleanup candidate; a principal with failing acquisitions for an unexpected audience is a misconfiguration in progress.

The activity log and the target resource's own diagnostic logs answer the second question. A role assignment is itself a logged control-plane operation, so the moment a principal was granted a role, by whom, and at what scope is recoverable from the activity log, which matters for an audit that needs to show when access was granted and by whom. The data-plane operations the principal performed against a target, such as the specific secrets it read from a vault, appear in that target's diagnostic logs when they are enabled, which is what lets an investigation reconstruct exactly what a compromised or misbehaving workload touched. Enabling those diagnostic logs on sensitive targets before an incident is the difference between an investigation that can answer what was accessed and one that cannot.

### How do I see whether a managed identity is actually being used?

Filter the Microsoft Entra sign-in logs to the managed-identity sign-in category and the principal's object ID. Each entry is a token acquisition, showing the resource requested and the result. No entries over a meaningful window means nothing is using the credential, which marks it for cleanup; failing entries for an unexpected resource point at a configuration error.

This auditability is one of the underrated advantages of the secretless pattern over stored credentials. A leaked client secret used from an attacker's machine is hard to distinguish from legitimate use, because the secret is the only thing being checked and it is valid wherever it is presented. A managed identity can only be used from the resource it is attached to, so its sign-in logs are inherently tied to the resource, and unexpected use is far easier to spot because the principal has a fixed, known home. The combination of no standing credential to steal and a clear log of where the credential was used is the security story that makes managed identities the default rather than a convenience, and it is worth instrumenting deliberately rather than assuming the logs will be there when an incident needs them.

## Cross-subscription and cross-tenant grants

The setup so far assumed the principal and its target live in the same subscription, which is the common case, but real estates cross subscription and occasionally tenant boundaries, and the rules at those boundaries are worth stating because they are where assumptions quietly break. A role assignment is scoped to a resource, and the scope can sit in a different subscription from the credential, so granting a managed identity in subscription A a role on a vault in subscription B is fully supported and works exactly as a same-subscription grant does, provided the principal granting the role has authority at the target scope. The identity does not need to move; the role assignment lives at the target and points back at the principal's object ID.

The tenant boundary is the harder one. A managed identity belongs to the tenant of the subscription it was created in, and Entra role assignments and resource RBAC operate within a tenant, so a managed identity cannot be directly granted a role on a resource in a different tenant the way it can across subscriptions in the same tenant. Scenarios that span tenants reach for different mechanisms, such as a multi-tenant application registration or a federated arrangement, rather than a direct cross-tenant role assignment to a managed identity, and treating a cross-tenant requirement as if it were a cross-subscription one is a setup that will not authorize no matter how the role is granted. Recognizing that the boundary is a tenant boundary, not a permission gap, is what redirects the design to the mechanism that actually spans tenants.

Within a single tenant, the cross-subscription grant is genuinely routine, and it is the basis for the platform-team pattern at scale. A central identity subscription can hold user-assigned identities that are granted roles on targets scattered across many application subscriptions, with the grants living at each target and pointing back at the central principals. That topology keeps identity ownership in one place while the access lands wherever the targets are, and it is one of the cleaner ways a large organization centralizes identity governance without forcing every resource into one subscription. The role assignment for it is the same command and the same template as a same-subscription grant, with only the scope's subscription differing, which is what makes the pattern straightforward to express as code.

## A worked end-to-end setup

Pulling the steps together into one worked example shows how short the procedure is when the rule is followed and how each step feeds the next. The scenario is a single web application that needs to read a database password from Key Vault and read blobs from a storage account, which means one principal and two role grants on two targets at two scopes.

The type choice is system-assigned, because one self-contained application owns this access and it should clean up with the app. Step two enables the principal and captures the principal ID. Steps three grants two narrow data roles, Secrets User on the vault and Blob Data Reader on the storage account, each at its own resource scope, using the object-ID form to avoid the replication race. Step four needs no special code because a single system-assigned identity is unambiguous, so `DefaultAzureCredential` with no options resolves it. Step five verifies both grants and a token acquisition before any production traffic.

```bash
# 1+2. Enable the system-assigned identity, capture the principal ID
PRINCIPAL_ID=$(az webapp identity assign \
  --name myapp --resource-group myapp-rg \
  --query principalId --output tsv)

# 3. Grant two narrow data roles at two specific scopes
az role assignment create \
  --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/<sub>/resourceGroups/myapp-rg/providers/Microsoft.KeyVault/vaults/myapp-kv"

az role assignment create \
  --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Reader" \
  --scope "/subscriptions/<sub>/resourceGroups/myapp-rg/providers/Microsoft.Storage/storageAccounts/myappstore"

# 5. Verify both grants landed where expected
az role assignment list --assignee "$PRINCIPAL_ID" --all --output table
```

The application code reads both the secret and the blobs with the same credential object, because the one principal now holds both roles, and the SDK clients for Key Vault and Storage each request the right audience for their target. The verification step's role-assignment listing is the artifact you keep, because it is the record of exactly what the application can do, and any future change to that access shows up against it. If a blob read later fails while the secret read succeeds, the listing immediately tells you whether the Storage grant is present, which narrows the problem to the storage side rather than the credential in general.

This is the whole procedure, and its brevity is the point. The reason managed identity setup feels hard is almost never the volume of work, which is a handful of commands, but the missing step that turns a near-complete setup into a non-working one. Follow the five-step checklist, keep the roles narrow and scoped to the target, name the principal in code only when more than one is attached, and verify in pieces, and the secretless pattern becomes a reliable default rather than a recurring puzzle.

## Prerequisites: the permissions the setup itself needs

Before step one, there is a quieter prerequisite that stops many setups cold: the person or pipeline doing the setup needs its own permissions, and they are not the same as the permissions the credential will end up with. Creating a principal and granting it a role are two different control-plane operations, and each needs a different right, so an account that can create resources but cannot assign roles will get halfway through the checklist and stall at step three with an authorization error that is about the operator, not the principal.

Enabling a system-assigned identity or attaching a user-assigned one is a write on the resource, which a Contributor on the resource already has, so step two rarely blocks anyone who can deploy the resource in the first place. Creating a user-assigned identity needs the right to create that identity resource, which the Managed Identity Contributor role grants specifically, or which any broader role with create rights at the scope covers. The step that surprises people is step three, because granting a role is a write to `Microsoft.Authorization/roleAssignments`, and a plain Contributor deliberately does not have that right. Assigning roles needs Owner, User Access Administrator, or the more targeted Role Based Access Control Administrator role, and an operator who is only a Contributor will create the credential successfully and then fail to grant it anything.

Naming this prerequisite up front saves the confusing experience of a setup that works for two steps and then refuses the third. In a pipeline, the deploying service principal or identity needs the role-assignment right at the scope where the grant lands, which is itself a deliberate grant that a platform team makes once, and treating that pipeline permission as part of the setup rather than an afterthought is what keeps automated deployments from failing on the role step. The order of operations, then, starts before the principal: confirm the operator can both create principals and assign roles at the target scope, and only then walk the five steps.

### What permissions do I need to assign a role to a managed identity?

You need the right to write role assignments at the target scope, which a plain Contributor does not have. Use Owner, User Access Administrator, or the narrower Role Based Access Control Administrator role at the scope where the grant lands. Creating a user-assigned identity additionally needs create rights such as Managed Identity Contributor, so the operator needs both capabilities to complete the setup.

## The targets a managed identity unlocks

A managed identity is only as useful as the targets it can reach, and the same identity-then-role pattern applies to each target with only the role name and audience changing, so learning the pattern once generalizes across the platform. The most common targets cluster into data services and platform features, and knowing the right role for each removes the guesswork that otherwise sends people to a broad grant.

For Key Vault under RBAC, the data roles split by object type: Key Vault Secrets User to read secrets, Key Vault Certificate User to read certificates, and Key Vault Crypto User to use keys for cryptographic operations. For Storage, the blob roles split by direction and need: Storage Blob Data Reader to read, Storage Blob Data Contributor to read and write, and Storage Blob Data Owner where the credential must also manage access at the data plane. Queue, table, and file storage each have their own parallel data roles, so a principal that needs queue access gets Storage Queue Data roles rather than a blob role, and mixing them up produces a 403 that looks like a missing grant when the grant simply named the wrong service.

Platform features extend the same idea. App Service and Functions support identity-based connections, where a trigger or binding authenticates to its backing service with the resource's managed identity rather than a connection string, which removes the storage connection string that a Function App would otherwise hold for its own runtime storage and its triggers. Setting that up is the same pattern: grant the Function App's identity the right Storage data role, configure the connection to use the principal, and the secret leaves the configuration. The Key Vault reference feature, where an app setting resolves to a secret in a vault at runtime through the app's identity, is the closely related case that has its own setup details in [configure-key-vault-references for a common target](/2023/04/24/configure-key-vault-references/), and it depends on exactly the credential and Secrets User grant this guide sets up.

### Which Storage role does a managed identity need to read and write blobs?

Storage Blob Data Reader grants read access to blob data, and Storage Blob Data Contributor grants read and write. Assign the role at the storage account or, more narrowly, at the container scope, not the management roles like Contributor, which control the account itself rather than its data. For queues, tables, or files, use that service's own data roles rather than a blob role.

## Setting it up across the portal, CLI, Bicep, and Terraform

The same setup can be done four ways, and the right one depends on whether you are exploring, scripting, or building something repeatable, so it helps to know what each path is good for rather than treating one as the only option. The portal is the fastest way to understand the shape of the setup and the worst way to keep it consistent, because every click is a manual action that the next environment will not reproduce exactly. It is the right tool for a first look and the wrong tool for anything that ships to more than one place.

The CLI is the right tool for one-off setup and for scripting that does not yet warrant a full template, and it is what most of this guide uses because the commands map one to one onto the checklist steps. A shell script that enables the principal, captures the principal ID, and grants the roles is reproducible enough for many cases and far more reliable than clicking, though it still drives imperative actions rather than declaring a desired state, so it does not detect or correct drift on its own.

Bicep and Terraform are the right tools when the setup must be identical across environments and reviewable as code, and the choice between them is usually about which the team already uses rather than a capability gap, because both express the credential, the attachment, and the role assignment as declarative resources. Terraform's version of the same setup attaches a user-assigned identity to a web app and grants it a role, with the role assignment referencing the principal's principal ID so the two deploy together.

```hcl
# Terraform: a user-assigned identity, attached to a web app,
# granted Key Vault Secrets User on a specific vault.

resource "azurerm_user_assigned_identity" "app" {
  name                = "myapp-uami"
  resource_group_name = azurerm_resource_group.app.name
  location            = azurerm_resource_group.app.location
}

resource "azurerm_role_assignment" "secrets" {
  scope                = azurerm_key_vault.app.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}

resource "azurerm_linux_web_app" "app" {
  name                = "myapp"
  resource_group_name = azurerm_resource_group.app.name
  location            = azurerm_resource_group.app.location
  service_plan_id     = azurerm_service_plan.app.id

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app.id]
  }

  site_config {}
}
```

The declarative versions carry the same three lessons the Bicep template did: the role assignment references the principal so they never drift apart, the assignment is idempotent so redeploying does not duplicate it, and the access an application holds becomes a reviewed diff rather than an after-the-fact discovery. The reason to graduate from the CLI to a template is not that the CLI is wrong but that a template makes the setup the same everywhere by construction, which is the only reliable cure for the works-here-not-there failures that hand-built environments produce. Whichever path you pick, the five checklist steps are the same; only the syntax for expressing them changes.

## Federated workload identity for pipelines and Kubernetes

Two important cases sit just outside the attach-an-identity-to-a-resource model, because the thing that needs the credential is not an Azure resource: a GitHub Actions workflow and a Kubernetes pod. Both are solved by federated identity credentials, which let an external token issuer stand in for the direct attachment, and the setup is the same five steps with the federated credential replacing step two's attachment.

A GitHub Actions workflow that deploys to Azure used to need a stored service principal secret in the repository, which is exactly the long-lived credential the secretless pattern exists to remove. Workload identity federation removes it: you create a user-assigned identity, add a federated credential that trusts tokens issued by GitHub's OIDC provider for a specific repository and branch or environment, and grant the principal the roles the deployment needs. The workflow then requests a short-lived OIDC token from GitHub, exchanges it for an Azure token against the federated identity, and deploys with no secret stored anywhere. The trust is pinned to the exact repository and ref in the federated credential, so a different repository cannot impersonate the deployment.

```bash
# Add a federated credential so a GitHub Actions workflow can use
# the identity with no stored secret. The subject pins the trust to
# one repository and ref.
az identity federated-credential create \
  --name github-deploy \
  --identity-name myapp-uami \
  --resource-group identity-rg \
  --issuer "https://token.actions.githubusercontent.com" \
  --subject "repo:my-org/my-repo:ref:refs/heads/main" \
  --audiences "api://AzureADTokenExchange"
```

The Kubernetes case is the same mechanism with a different issuer. AKS workload identity federates the cluster's OIDC issuer, so a user-assigned identity trusts tokens issued for a specific Kubernetes service account, and a pod running under that service account exchanges its projected service-account token for an Azure access token. The setup enables the OIDC issuer and workload identity on the cluster, creates the credential, adds a federated credential whose subject names the namespace and service account, grants the principal its roles, and annotates the service account with the principal's client ID so the in-cluster SDK knows which identity to request. The pod's code uses the same credential chain as everything else, and the workload identity step of the chain picks up the federated token, which is why application code written for a virtual machine or web app runs unchanged in a pod once the federation is configured.

### How do federated credentials remove the stored secret?

A federated credential tells the credential to trust tokens from an external issuer, such as GitHub's OIDC provider or a Kubernetes cluster's OIDC issuer, for a specific subject. The external workload presents a short-lived token from that issuer, the principal validates it against the configured trust, and Azure issues an access token in exchange, so no long-lived secret is ever stored in the pipeline or the cluster.

This is the same secretless principle the rest of the guide applies to Azure compute, extended to workloads that are not Azure resources, and it is why the stored deployment secret in a pipeline is now an avoidable choice rather than a necessity. The trust is narrow because the subject pins it to one repository and ref or one namespace and service account, so the federation grants exactly the workload you named and nothing else, which keeps the least-privilege discipline intact across the boundary. The relationship between this federated trust and the broader question of when a principal rather than a registered application is the right model is covered in [managed-identity-vs-service-principal for the choice](/2024/01/08/managed-identity-vs-service-principal/), and for new pipelines the federated identity is the path that avoids the stored secret from the start.


## Image pull: the credential that pulls from a registry

Pulling a container image from Azure Container Registry is a managed identity use that does not look like the others, because the caller is the hosting platform pulling on the workload's behalf rather than the application code requesting a token, yet it follows the same identity-then-role rule with one role: AcrPull. Getting this wrong produces a pull failure that reads as a registry or networking problem when it is really a missing role on the pulling identity, so naming the pattern saves a long detour.

On AKS, the principal that pulls images is the cluster's kubelet identity, which is a user-assigned identity the cluster uses for node-level operations, distinct from any identity a pod uses for application access. Granting that kubelet identity AcrPull on the registry lets nodes pull images, and a cluster that cannot pull from a registry it should reach is almost always missing that single grant. The pod-level workload identity covered earlier is a separate concern: kubelet identity pulls the image, workload identity gets the pod its application tokens, and conflating the two leads to granting the wrong identity the wrong role.

On App Service and Container Apps, pulling from a registry with a managed identity replaces the registry username and password that the platform would otherwise store. You enable the resource's identity, grant it AcrPull on the registry, and configure the platform to use the managed identity for the pull rather than admin credentials, which removes the registry password from the configuration the same way the application's data-plane grants remove its connection strings. The pull is a platform action, so there is no application code involved, but the verification is the same: list the role assignment to confirm AcrPull landed on the right identity at the registry scope, and the pull starts working once the grant propagates.

### Why does my container fail to pull even though the credential exists?

Because pulling an image needs the AcrPull role on the registry, and enabling the principal does not grant it. The pulling identity, the kubelet identity on AKS or the resource's identity on App Service and Container Apps, must hold AcrPull at the registry scope. A pull that fails with an authentication error while the credential plainly exists is the identity-then-role rule again: the principal is assigned, the role is missing.

## When the network blocks the token endpoint

A managed identity setup can be entirely correct at the credential and role level and still fail because the resource cannot reach the local endpoint that issues the token, and this network-side failure is worth separating because it looks identical to a permission problem from the application's logs while having nothing to do with permissions. The token request goes to a local endpoint, the instance metadata service on a virtual machine or the injected identity endpoint on App Service, and anything that blocks that local hop blocks the token before authorization is ever reached.

On a virtual machine, the metadata service lives at the link-local address that is supposed to be reachable from the host without any routing, but a custom route table, a misconfigured proxy, or an outbound rule that captures all traffic can intercept or drop the request, and the symptom is a token call that times out rather than returns an error. A proxy configuration that routes all outbound traffic, including the link-local metadata address, through an external proxy is a classic cause, because the metadata service is not something a proxy can reach, so the fix is to exclude the metadata address from the proxy rather than to change anything about the principal. The token endpoint failing is a network finding, and treating it as a permission problem sends the investigation in the wrong direction entirely.

The target side has its own network story that is separate from the token endpoint. Acquiring the token can succeed while the call to the target fails because the target has a firewall or private endpoint that the resource's network path does not satisfy, which is a data-plane network problem rather than a principal problem. A vault or storage account locked to selected networks will deny a correctly authenticated and authorized call that arrives from an address the firewall does not allow, so when the token is good and the role is granted and the call still fails, the next suspect is the network path to the target, not the credential. Separating these two network concerns, the path to the token endpoint and the path to the target, keeps a network failure from being misread as a setup failure, and verifying the token acquisition independently is exactly what draws that line. Working through these network-versus-permission distinctions as drills on [ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) builds the habit of isolating the failing hop, and the command library on [VaultBook](https://vaultbook.org/tools/azure-labs.html) keeps the token-endpoint and target-reachability checks ready to run against a real resource.


## Scope, inheritance, and the cost of a broad grant

The scope of a role assignment is as consequential as the role itself, and it is the dimension people flatten when they grant at a resource group or subscription to save a few keystrokes, not realizing that the breadth they bought is permanent reach the workload did not need. A role assignment applies at its scope and inherits downward, so a grant at the resource group level applies to every resource in that group, present and future, and a grant at the subscription level applies to everything in the subscription. That inheritance is convenient and dangerous in equal measure.

The danger is the future tense. Grant a workload Secrets User on the resource group because it is easier than naming the one vault, and the workload can read secrets from every vault anyone ever creates in that group, including vaults created later for entirely unrelated purposes by people who have no idea the workload can read them. The grant that was scoped for convenience becomes an access path nobody designed and nobody is watching, and it is exactly the kind of lateral reach an attacker who compromises the workload uses. The narrow grant at the single vault costs one more identifier in the command and forecloses that entire category of accidental access.

Inheritance also explains a confusing success that masks a problem. A workload that should fail because its target grant is missing can succeed anyway because it inherited the access from a broad grant higher up, which means the functional test passes while the least-privilege posture is quietly wrong, and the gap only appears in a security review or when the broad grant is finally tightened and the workload breaks. Listing a principal's assignments with the scope of each, which the verification step does, surfaces these inherited grants so a broad assignment that is silently doing the work is visible rather than hidden behind a passing test.

The discipline that follows is simple to state and worth holding: grant at the narrowest scope that makes the required call succeed, which for a single target is that target, not its container. The narrow scope is not extra work once it is a habit, it is one more identifier, and it is the difference between a principal whose reach you can describe in a sentence and one whose reach depends on what else happens to share its resource group. Expressing the grant as code makes the scope a reviewed value, so a change that widens it from a single resource to its group shows up as a diff a reviewer can question, which is the most reliable guard against scope creep over time.

## Migrating an existing application from stored secrets

Most managed identity setups in practice are not greenfield; they replace a stored secret in an application that already works, and doing that migration without an outage is its own short procedure that the identity-then-role rule still governs. The mistake to avoid is removing the secret first, which guarantees a window where the application has neither working credential, so the order is additive: stand up the principal path completely, verify it, and only then remove the secret.

The steps fall out of the checklist with one addition. Enable the credential on the resource, grant it the same access the stored secret currently provides as narrow data roles on the specific targets, and verify the grants and a token acquisition while the secret is still in place and still working. Then update the application code or configuration to use the credential chain instead of the stored secret, deploy, and confirm the application now authenticates through the principal by checking the sign-in logs for the principal's token acquisitions against the targets. Only once those acquisitions are succeeding do you remove the secret from configuration and revoke or delete it at its source, because at that point the credential path is proven and the secret is genuinely unused.

The verification through the sign-in logs is the step that makes the migration safe rather than hopeful, because it confirms the application is actually using the principal and not silently falling back to the still-present secret. An application that appears to work after the code change might be working through the old secret that has not been removed yet, and removing the secret would then break it, so seeing the principal's own token acquisitions in the logs is the proof that the new path carries the load. With that confirmation in hand, removing the secret is a non-event, which is exactly the calm cutover the additive order is designed to produce. The before-and-after comparison of an application carrying a rotating secret versus one authenticating through a principal it never sees is the clearest demonstration of what the pattern buys, and it is worth running on a non-critical workload first to rehearse the order before applying it to something that cannot tolerate a mistake.


## The verdict on setting up managed identities

The setup that works is the setup that treats authorization as a first-class step rather than an afterthought to authentication. Enabling the credential is the easy half and the half that feels like completion; granting the precise role on the precise target is the half that actually delivers access, and it is the half that gets skipped because the portal toggle makes the first half look like the whole job. The identity-then-role rule is the corrective: every managed identity setup is two steps, the missing role is the usual failure, and a setup that stops at the toggle is a setup that will throw a 403 the first time it tries to do anything real.

The type choice resolves to a short question about lifecycle and sharing. System-assigned for a single self-contained workload that should clean up after itself, user-assigned when several resources share a principal or when access must exist before or persist beyond the compute that uses it. Standardizing on one type for everything trades a real benefit for a real cost in either direction, and the mature policy names the cases for each rather than collapsing the decision into a slogan.

The code half is the credential chain, and its appeal is that one credential object authenticates as the managed identity in Azure and as the developer's account locally with no branching, provided you resolve the one ambiguity it cannot resolve for you by naming the principal's client ID when more than one is attached. Verify in pieces so a failure points at a link rather than the whole chain, express the setup as code so it is identical across environments and auditable in review, and instrument the sign-in logs so the principal is an actor you can see rather than a black box. Do those things and the secretless pattern stops being something that occasionally works and becomes the default that needs a reason to deviate from. Run the full setup end to end against a sandbox on [VaultBook](https://vaultbook.org/tools/azure-labs.html) and rehearse the failure cases as drills on [ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html), and the procedure becomes muscle memory rather than a thing you relearn from scratch each time.

## Frequently Asked Questions

**System-assigned or user-assigned: which should I set up?** Set up system-assigned when a single resource owns the access and that access should disappear when the resource does, because tying the credential to the resource lifecycle keeps cleanup automatic. Choose user-assigned when several resources must authenticate as the same principal, when you need to grant access before the consuming resource exists, or when the access must survive the resource being replaced. The decision is really a question about lifecycle and sharing, not about which one is newer or more capable.

**How do I assign a managed identity to a resource?** For a system-assigned identity, enable it on the resource with the relevant command, such as `az webapp identity assign` or `az vm identity assign`, and Azure creates the principal and returns its principal ID. For a user-assigned identity, create the principal once with `az identity create`, then attach it to the resource by its resource ID using the `--principals` argument. The same user-assigned identity can attach to many resources at once, which is the whole reason to choose that type.

**How do I grant the credential a role on the target?** Use `az role assignment create` with the principal's principal ID as the assignee, a specific data-plane role, and the target resource as the scope. Pass `--assignee-object-id` together with `--assignee-principal-type ServicePrincipal` rather than the plain `--assignee`, because that form skips the Graph lookup that races against a new identity's replication. Pick the narrowest role that makes the call succeed, such as Key Vault Secrets User rather than Contributor, and scope it to the one target rather than the resource group.

**How do I select the right user-assigned identity by client ID?** When a resource has more than one principal attached, the credential chain cannot guess which to use, so you name it by its client ID. In code, set `ManagedIdentityClientId` in the credential options to the `clientId` value from `az identity create`. Without touching code, set the `AZURE_CLIENT_ID` environment variable to the same value, which App Service and Functions expose as an application setting so the selection becomes a deployment setting rather than a constant.

**How does DefaultAzureCredential use the principal?** It walks an ordered chain of credential sources and uses the first that succeeds. It tries environment variables, then a workload identity credential, then the managed identity, and finally developer credentials such as your Azure CLI login. In Azure the resource has a managed identity and no developer login, so the chain lands on the managed identity; on your machine there is no managed identity but there is an `az login` session, so the same code authenticates as your account with no change.

**How do I keep a managed identity least-privilege?** Grant the smallest data-plane role that makes the required call succeed, and scope it to the specific target rather than a resource group or subscription. Resist Owner and Contributor even though they make a 403 disappear, because they let the workload delete and reconfigure the resource, which is reach an application never needs and an attacker who compromises it gains. Express the grant as code so the role and scope are reviewable, and audit the sign-in logs to confirm the credential uses only the access you intended.

**Why does my managed identity still get a 403 after I enabled it?** Because enabling the principal completed authentication but not authorization. The resource can acquire a valid token, but the target has no role assignment for that principal, so the data plane denies the call. Grant the specific data-plane role at the target's scope, and if the call still fails for a few minutes afterward, the cause is usually propagation lag or a token cached from before the grant rather than a wrong assignment. A 403 that survives a fresh token and a verified grant points at a scope or audience mismatch.

**Do managed identities cost anything?** No. Both system-assigned and user-assigned managed identities are free, with no per-identity charge and no charge for the tokens they acquire. The cost of the secretless pattern is setup discipline, not money, which makes the comparison against stored credentials lopsided: managed identities remove the credential, remove the rotation burden, and remove the leak risk at no added platform cost. The only resource you create is the user-assigned identity object itself, which is also free, so there is no budget reason to prefer a stored secret.

**Can I use a managed identity from my laptop?** Not directly, because a managed identity only issues tokens to the Azure resource it is attached to, and your laptop is not that resource. The credential chain handles local development differently: when no managed identity is present, it falls back to your developer sign-in, so the same code that uses the credential in Azure uses your `az login` account locally. Grant your account the same narrow roles the principal will hold so local success faithfully predicts production behavior rather than overstating it.

**How long does a role assignment take to propagate?** Usually seconds to a few minutes, but it is not guaranteed instant, and a call made immediately after the grant can fail and then succeed shortly after with nothing changed. Two timing effects stack here: the assignment must replicate across the platform, and a token acquired before the grant stays cached until it refreshes. When a fresh grant looks like it did not take, wait a few minutes and force a new token before concluding the assignment is wrong.

**Can I convert a system-assigned identity to a user-assigned one?** No, there is no in-place conversion, because they are different kinds of object with different lifecycles. To move from one to the other you create the user-assigned identity, grant it the roles the system-assigned identity held, attach it to the resource, update any code that selects a principal by client ID, verify, and then disable the system-assigned identity. Planning this as a deliberate migration rather than a flip avoids a window where the resource has neither working identity.

**Does a managed identity have a secret I need to rotate?** No, and that is the entire point. The platform holds the trust relationship and issues short-lived tokens on demand, so there is no client secret or certificate that you store, protect, or rotate. The tokens themselves expire and are reissued automatically by the platform and the SDK, which means rotation happens continuously without any action from you. Removing the long-lived credential is what eliminates both the rotation burden and the leak risk that stored secrets carry.

**Can a managed identity authenticate to Azure SQL Database?** Yes. Enable the credential, create a contained database user mapped to the principal in the database, grant that user the database roles it needs, and connect with a token acquired for the SQL audience through the credential chain. The setup adds a database-side user-creation step on top of the standard identity-and-role pattern, because SQL authorization lives inside the database rather than in resource RBAC, but the token acquisition is the same secretless flow used for any other target.

**Can one resource have both a system-assigned and a user-assigned identity?** Yes, a resource can carry a system-assigned identity and one or more user-assigned identities at the same time. The catch is that this makes identity selection in code ambiguous, so the credential chain can no longer guess which one to use, and you must name the intended identity by its client ID. Mixing types on one resource is occasionally useful but is also a frequent cause of the wrong-identity 403, so do it deliberately and set the client ID explicitly.

**How do I remove or disable a managed identity?** For a system-assigned identity, disable it on the resource, which deletes the principal and its role assignments automatically. For a user-assigned identity, detach it from each resource and then delete the identity resource itself, because it is independent and will otherwise persist with its role assignments intact. A user-assigned identity left behind after its consumers are gone is a standing principal with live access, which is the cleanup that audits flag, so deleting it explicitly is part of decommissioning.

**Why does my code work locally but the deployed app gets denied?** Almost always because your developer account has access the managed identity lacks. The credential chain uses your account locally and the credential in Azure, so if your account is broadly privileged it will succeed locally while the narrowly scoped identity fails in Azure, masking a missing role grant until deployment. Grant your account the principal's exact roles at the same scopes so local development tests the real permission set rather than your personal reach.

**Can a managed identity authenticate to a non-Azure service?** Sometimes, if that service accepts Microsoft Entra tokens for an audience the principal can request, which some third-party and partner services do. The identity acquires a token for the service's registered audience through the same chain, and the service validates it against Entra. Where the target does not accept Entra tokens, a managed identity cannot authenticate to it directly, and the integration needs a different mechanism, so confirm the target's support for Entra tokens before designing around a managed identity.

**How do I troubleshoot when no token is returned at all?** Separate the platform side from the authorization side. Acquire a token directly from the resource's identity endpoint, the instance metadata service on a virtual machine or the injected identity endpoint on App Service, and read the response. A token with an `access_token` field proves the platform side works, so any later denial is an authorization problem to fix with a role. No token at all points at the platform side: the credential not actually attached, the wrong endpoint for the host type, or a network path blocking the local endpoint, which is the boundary where setup ends and token-failure diagnosis begins.

