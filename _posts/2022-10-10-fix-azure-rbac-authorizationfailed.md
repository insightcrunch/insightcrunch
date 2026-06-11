---
layout: post
title: "Fix Azure RBAC AuthorizationFailed Errors"
page_title: "Fix Azure RBAC AuthorizationFailed Errors: Diagnose Missing Role Assignments, Wrong Scope, Propagation Delay, and Control-Plane vs Data-Plane Denials"
date: 2022-10-10
categories: ["Technology"]
tags: ["Azure", "RBAC", "Troubleshooting", "Security", "Identity", "Cloud Computing"]
excerpt: "Fix Azure RBAC AuthorizationFailed errors by reading the exact action and scope from the message, then granting the least-privilege role that resolves it."
image: "/assets/images/blog/blog-70.webp"
reading_time: 60
author: "alex-cunningham"
last_updated: 2022-10-10
lang: en
---
An AuthorizationFailed response from Azure is one of the most misread errors on the platform, because the obvious reaction is the wrong one. The message looks like a wall, so people reach for the biggest key they have, assign the Owner role, and move on. Sometimes that papers over the symptom. Often it does nothing, because the failing call was a data-plane operation that no management role grants, or because a deny assignment outranks every role, or because the assignment simply has not propagated yet. The AuthorizationFailed error is not a vague "you lack permission" signal. It is a precise statement that names the exact action the caller tried and the exact scope it tried it on, and the fix is almost always the smallest role that grants that one action at that one scope. This article treats the error the way it deserves to be treated: as a diagnostic readout, not a wall.

![Diagnosing Azure RBAC AuthorizationFailed root causes and least-privilege fixes - Insight Crunch](/assets/images/blog/blog-70.webp)

The reason the error is worth a long, careful treatment is that it sits at the intersection of several systems that each fail in their own way. Azure role-based access control evaluates a request against role assignments, deny assignments, and increasingly attribute conditions, and it does so at two different planes that look identical from the outside but obey different rules. A request to create a storage account and a request to read a blob inside that account both travel over HTTPS to a Microsoft endpoint, both can return a 403, and both can surface AuthorizationFailed or a closely related denial, yet the role that satisfies one does nothing for the other. An engineer who understands that split, who can read the action string out of the error, and who knows which of a small set of root causes is in front of them will resolve the error in minutes. An engineer who guesses will over-permit an identity, leave a security hole, and frequently still be locked out. The goal here is the former.

## What AuthorizationFailed Actually Means

AuthorizationFailed is the error code the Azure Resource Manager control plane returns when the calling security principal does not hold a role assignment that grants the requested action at the requested scope. The HTTP status is 403 Forbidden. The body carries a code of `AuthorizationFailed` and a message that, in its standard form, reads close to this:

```text
{
  "error": {
    "code": "AuthorizationFailed",
    "message": "The client 'app-deploy@contoso.com' with object id
    '11111111-2222-3333-4444-555555555555' does not have authorization to
    perform action 'Microsoft.Storage/storageAccounts/write' over scope
    '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-prod/
    providers/Microsoft.Storage/storageAccounts/stprod01' or the scope is invalid.
    If access was recently granted, please refresh your credentials."
  }
}
```

Every word in that message is load-bearing. The client identifier and object id tell you which principal was evaluated, which matters more than it first appears, because the principal that ran the command is frequently not the one you assumed. The action string, here `Microsoft.Storage/storageAccounts/write`, names the precise operation the caller attempted in the resource-provider namespace. The scope string is the full resource path the action was attempted against. And the closing sentence, the gentle suggestion to refresh credentials if access was recently granted, is the platform telling you that propagation and token freshness are real causes you should rule out before assuming the assignment is missing.

The mental model to hold is that authorization in Azure is a function of three inputs evaluated together: who (the security principal, which is a user, a group, a service principal, or a managed identity), what (the action, expressed in the resource provider's operation namespace), and where (the scope, a node in the resource hierarchy). A role assignment binds a role definition, which is a set of allowed and disallowed actions, to a principal at a scope. When a request arrives, the platform asks whether any assignment grants the requested action at the requested scope or an ancestor scope, whether any deny assignment forbids it, and whether any attribute condition fails. AuthorizationFailed is the answer "no allowing assignment found, or an explicit denial applied." Reading the error as anything vaguer than that throws away the diagnostic information the platform handed you for free.

### What does AuthorizationFailed mean in one sentence?

It means the principal that made the call has no role assignment granting the specific action named in the error at the scope named in the error, or an explicit deny applied, so Azure refused the request with a 403. The fix is the least-privilege role that grants that action at that scope.

## How to Read the Error and Gather the Diagnostic Signal

Before changing a single role assignment, extract four facts from the failure, because each one points at a different root cause. The four are the principal that was evaluated, the action that was attempted, the scope it was attempted on, and whether the denial was a missing grant or an explicit block. The error message hands you the first three directly, and a few commands settle the fourth.

Start with the principal. The object id in the message is the canonical identifier; the friendly name can mislead because display names are not unique and because automation often runs as an identity nobody on the team thinks about. Confirm who you actually are in the current context with the account command:

```bash
az account show --query "{subscription:name, subscriptionId:id, tenant:tenantId, user:user.name, userType:user.type}" -o table
```

If you are debugging an interactive session, that tells you the signed-in account. If you are debugging automation, the identity is whatever credential the pipeline or the host authenticated with, which is usually a service principal or a managed identity whose object id you need to capture explicitly. For a signed-in user you can resolve the object id directly:

```bash
az ad signed-in-user show --query "{displayName:displayName, objectId:id, upn:userPrincipalName}" -o table
```

For a service principal identified by its application (client) id, resolve the object id of the service principal, not the application object, because role assignments bind to the service principal:

```bash
az ad sp show --id "<application-client-id>" --query "{displayName:displayName, spObjectId:id}" -o table
```

The distinction between the application object and the service principal object trips up a surprising number of role assignments. The application registration has one object id, and the service principal that represents that application in your tenant has a different object id. Role assignments must target the service principal's object id. If someone assigned a role to the application object id by mistake, the grant exists in the directory but never applies to the running principal, and you get AuthorizationFailed even though a casual look at the portal suggests access was granted.

Next, read the action. The action string in the error is the exact operation in the resource-provider namespace, and it is the single most useful piece of the message because it tells you precisely which role you need. `Microsoft.Storage/storageAccounts/write` is the management operation to create or update a storage account. `Microsoft.Storage/storageAccounts/listKeys/action` is the management operation to read the account keys. `Microsoft.KeyVault/vaults/write` creates or updates a vault. Note the shape: a provider namespace, a resource type path, and a verb that is usually `read`, `write`, `delete`, or a named `/action`. Once you have the action verbatim, finding the role that grants it is mechanical rather than a matter of memory.

Then read the scope. The scope is the full path the action was attempted on, and its shape tells you the level in the hierarchy. A path ending in a resource name is resource scope. A path ending in a resource group is resource-group scope. A path with only a subscription id is subscription scope. A path beginning `/providers/Microsoft.Management/managementGroups/` is management-group scope. The level matters because role assignments inherit downward, so a grant at the subscription covers every resource group and resource beneath it, but a grant at one resource group covers nothing in a sibling resource group and nothing at the subscription level above it.

### Which command shows what the failing identity is allowed to do?

List the principal's role assignments with `az role assignment list --assignee <objectId> --all -o table`. That returns every assignment for the identity across scopes, so you can see at a glance whether any assignment covers the action and scope in the error, or whether the identity has nothing relevant, an assignment at the wrong scope, or only a management-plane role.

With principal, action, and scope in hand, run the assignment listing to see what the identity actually holds:

```bash
az role assignment list --assignee "11111111-2222-3333-4444-555555555555" --all -o table
```

The `--all` flag is important: without it the command lists assignments only at and below the current subscription's default scope view, and you can miss an assignment made at a management group or in another subscription. Read the output against the action and scope you extracted. If there is no assignment whose role grants the action at a scope that is the failing scope or an ancestor of it, you are looking at a missing or misplaced grant. If there is an assignment that looks like it should cover the action at the right scope, you are looking at propagation, token freshness, an explicit deny, a failing condition, or a plane mismatch, and the rest of this article walks each of those down.

## The Action-and-Scope Rule

The single principle that turns this error from frustrating to mechanical is what this series calls the action-and-scope rule: the AuthorizationFailed message names the action it needs and the scope it needs, so the correct fix is the least-privilege role that grants that action at that scope, not a broad Owner assignment that grants thousands of actions you never intended. The error is, in effect, a specification for the grant. It tells you the exact operation and the exact place. Granting Owner to satisfy a request for one write action at one resource is like replacing a doorknob by rebuilding the house: it might let you through the door, and it creates problems far larger than the one you set out to solve.

Owner over-assignment is the default mistake, and it is worth understanding why it is both dangerous and frequently ineffective. It is dangerous because Owner grants full management access including the ability to grant access to others, which means an identity you handed Owner can now expand its own blast radius and anyone who compromises it inherits the keys to the scope. It is frequently ineffective because Owner is a control-plane role, and if the failing action was a data-plane operation, Owner does not grant it. You will have created a serious over-permission and still be locked out of the thing you were trying to do. The action-and-scope rule cuts through both problems: read the action, find the narrowest role that contains it, assign that role at the narrowest scope that covers the failing scope, and you have fixed the error without opening a hole.

Finding the narrowest role that grants a given action is a query, not a memory exercise. The role definitions are data you can search. To find which built-in roles grant a specific action, list the definitions and filter on the action you pulled from the error:

```bash
az role definition list \
  --query "[?permissions[0].actions && contains(to_string(permissions), 'Microsoft.Storage/storageAccounts/listKeys/action')].{role:roleName, type:roleType}" \
  -o table
```

That returns the roles whose permission set includes the listKeys action, and you pick the most restrictive one that fits the job. For listing storage account keys, that is typically a role scoped tightly to key management rather than a sweeping management role. The same pattern works for any action: substitute the action string from your error, run the query, and choose the smallest role that contains it.

## The Distinct Root Causes of AuthorizationFailed

AuthorizationFailed has a small, finite set of root causes, and almost every real incident is one of them. The diagnostic value of knowing the set is that it converts an open-ended "why am I denied" into a short checklist you can walk in order. The causes are: no role assignment grants the action at all; an assignment exists but at the wrong scope; an assignment was made recently and has not propagated; the action is a data-plane operation and only a control-plane role was granted; a deny assignment explicitly blocks the action regardless of roles; an attribute condition on an assignment fails for this request; the identity that ran the call is not the identity you assigned the role to; and a custom role that looks sufficient is missing the one action the operation needs. The cause table below is the artifact to keep, and the sections after it confirm and fix each one.

### The InsightCrunch AuthorizationFailed cause table

| Root cause | How to confirm it is yours | The least-privilege fix |
|---|---|---|
| No role assignment for the action | `az role assignment list --assignee <id> --all` shows nothing covering the action or scope | Assign the smallest built-in role containing the action at the failing scope |
| Assignment at the wrong scope | An assignment exists but its scope is a sibling or descendant of the failing scope, not an ancestor | Re-create the assignment at the failing scope or a true ancestor of it |
| Propagation delay | The assignment exists at the right scope but was created within the last several minutes | Wait for propagation, refresh the token, and retry; do not re-assign |
| Control-plane role for a data-plane action | The action is a `DataActions` operation; the identity holds only a management role like Contributor | Assign the matching data-plane role (for example, a Storage Blob Data role) |
| Deny assignment blocks the action | `Get-AzDenyAssignment` at the scope returns a deny covering the action and principal | Adjust the source of the deny (a blueprint, managed app, or system); roles cannot override it |
| Failing attribute condition | The assignment carries an ABAC condition the request does not satisfy | Meet the condition, or assign a role without the condition for this need |
| Wrong principal targeted | The role was assigned to the application object or a different identity than the one running the call | Re-assign to the running principal's service-principal or managed-identity object id |
| Custom role missing the action | A custom role is assigned but its `Actions` list does not include the action in the error | Add the specific action to the custom role definition |

## Cause One: No Role Assignment Grants the Action

The most common cause is also the most straightforward: the principal simply has no assignment that grants the action anywhere relevant. This is the new service principal that was created but never granted access, the managed identity that was enabled on a virtual machine but never given a role, the contractor account that was added to the directory but not to any resource. The listing command from earlier confirms it directly. If `az role assignment list --assignee <id> --all` returns an empty set, or returns only assignments whose roles plainly do not include the action you pulled from the error, you have a missing grant.

The fix is to assign the least-privilege role that contains the action at the scope where the work happens. Suppose the error names `Microsoft.Storage/storageAccounts/write` at a resource group, meaning the identity needs to create or update storage accounts inside that group. Rather than Owner or even the broad Contributor, consider whether a service-specific management role fits. If the identity manages storage and nothing else, a storage-focused role at the resource-group scope is tighter than Contributor. When no service-specific role fits and the identity genuinely needs general management of resources in that group, Contributor at the resource-group scope is the defensible choice, because Contributor grants management of resources without the right to grant access to others, which keeps the identity from expanding its own reach.

```bash
az role assignment create \
  --assignee "11111111-2222-3333-4444-555555555555" \
  --role "Contributor" \
  --scope "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-prod"
```

After the assignment, verify it landed where you expect rather than assuming the command's success message means the identity can now act:

```bash
az role assignment list \
  --assignee "11111111-2222-3333-4444-555555555555" \
  --scope "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-prod" \
  -o table
```

The verification matters because a successful create call only proves the assignment was recorded, not that it has propagated or that it is the assignment the failing operation needs. If the action was a data-plane operation, this control-plane assignment will record cleanly and the operation will still fail, which is exactly the trap that sends people toward Owner. Confirm that the role you granted actually contains the failing action before you consider the cause resolved.

### How do I grant access without using Owner or Contributor?

Find the built-in role whose action set most narrowly covers the failing action, then assign that role rather than a broad one. Query the role definitions for the action string from the error, pick the smallest matching role, and scope the assignment to the resource or resource group where the work happens, not the subscription.

## Cause Two: The Assignment Exists at the Wrong Scope

The second cause is subtler and produces a confusing symptom: someone assigned a role, the portal shows the assignment, everyone agrees access was granted, and the call still fails. The reason is almost always that the assignment sits at a scope that does not cover the failing operation. Azure RBAC inherits downward and only downward. An assignment at a scope applies to that scope and every descendant of it, never to an ancestor and never to a sibling. So a Reader role granted at one resource group does nothing for a resource in a different resource group, and a Contributor role granted at a single resource does nothing for a sibling resource or for operations at the resource-group level such as creating a new resource.

The classic version of this is the deployment that needs to create resources in a resource group but whose identity was granted Contributor on a single resource inside that group. Creating a new resource is a write at the resource-group scope, and an assignment at a child resource cannot reach up to authorize it. The error names a resource-group scope; the assignment lives at a resource scope below it; the two never meet.

Confirm the wrong-scope case by comparing the scope in the error against the scope of each assignment in the listing. Lay the failing scope and the assignment scopes side by side:

```bash
az role assignment list --assignee "<objectId>" --all \
  --query "[].{role:roleDefinitionName, scope:scope}" -o table
```

Read each assignment scope and ask whether it is the failing scope or a true ancestor of it. The ancestry chain runs management group, then subscription, then resource group, then resource. If your failing scope is a resource group and the only assignment is at a resource inside that group, the assignment is a descendant of the failing scope, which is backwards, and that is your cause. The fix is to re-create the assignment at the failing scope or a genuine ancestor of it. Grant at the resource group if the identity needs to work across that group, or at the subscription if it must work across many groups, choosing the lowest scope that covers the real need rather than reflexively granting high.

```bash
az role assignment create \
  --assignee "<objectId>" \
  --role "Contributor" \
  --scope "/subscriptions/<subId>/resourceGroups/rg-prod"
```

Scope discipline is where least privilege is won or lost. Granting at the subscription because it is easier than figuring out which resource groups an identity touches is the scope-level equivalent of granting Owner: it works, and it quietly hands the identity reach over everything in the subscription. The authorization model rewards precision here, and the cost of precision is one more minute of thought about which scope the work actually requires.

## Cause Three: Propagation Delay After a Fresh Assignment

The third cause is the one the error message itself warns you about, and it is the one most likely to send an engineer in circles. After you create a role assignment, the grant does not become effective everywhere instantaneously. It must propagate through the platform, and during that window a call can still return AuthorizationFailed even though the assignment is correct in every respect. The propagation window is usually a few minutes and is occasionally longer; treat it as a real interval to wait out rather than a fixed number to quote, because the platform's timing is a behavior to verify rather than a constant to memorize.

The trap is that the natural response to a continuing failure is to assume the assignment did not take, so you re-create it, which resets nothing and starts the clock over in your head while the original assignment was already propagating fine. Then you escalate to a broader role, which also has to propagate, and now you have an over-permission and the same wait. The discipline is to confirm the assignment exists at the right scope with the right role for the right principal, and if all three are correct, to wait and retry rather than to change anything.

Confirm propagation as the cause by checking two things: that the assignment is present and correct, and that it was created recently. The listing shows the assignment; the creation time is visible in the assignment's properties. If the assignment is correct and minutes old, propagation is your cause. The fix is to refresh the caller's token and retry. For an interactive session, the token refresh is a re-authentication; for automation, it is acquiring a new token on the next run. A blunt way to force a fresh token in a CLI session is to clear the account context and sign in again, which guarantees the next call carries a token issued after the assignment:

```bash
az account clear
az login
```

For a service principal in a pipeline, the next token request after propagation completes will carry the grant, so the practical fix is a short delay and a retry rather than any change to the assignment. Build that delay into automation deliberately when a pipeline creates a role assignment and then immediately uses it, because a deploy step that grants a role and the very next step that exercises it will frequently hit the propagation window. Separating the grant into an earlier stage, or adding a bounded retry on the AuthorizationFailed code specifically, turns the propagation window from an intermittent failure into a non-event.

### Why does my role assignment work for a colleague but not for me?

Most often the colleague's token was issued after the assignment propagated and yours was issued before. RBAC is evaluated against the principal at request time, but a stale token and the propagation window can leave a fresh assignment unseen. Sign out and back in to get a token issued after the grant, then retry.

## Cause Four: Control-Plane Role for a Data-Plane Action

The fourth cause is the conceptual heart of the whole topic and the one that most reliably defeats the Owner-fixes-everything reflex. Azure operations divide into two planes. The control plane is resource management: creating, reading the configuration of, updating, and deleting resources, all routed through Azure Resource Manager. The data plane is the data inside those resources: the blobs in a storage account, the secrets in a Key Vault, the messages in a queue, the documents in a Cosmos database. These planes have separate authorization. Role definitions express control-plane permissions in an `Actions` list and data-plane permissions in a `DataActions` list, and a role that grants management of a resource does not, by that fact, grant access to the data inside it.

This is why Owner and Contributor, the two roles people reach for, do nothing for a data-plane denial. Contributor can create a storage account, configure it, and delete it, yet reading a blob inside it requires a data-plane role such as a Storage Blob Data role, because reading a blob is a `DataActions` operation that Contributor's permission set does not include. The same split holds for Key Vault when it uses the RBAC permission model: a management role lets you create and configure the vault, while reading a secret requires a data-plane role like Key Vault Secrets User. The platform built this separation on purpose, so that the team that manages a resource and the workload that uses its data can be granted access independently and so that managing a vault does not silently expose its secrets.

Confirm the plane-mismatch cause by examining the action in the error. Data-plane actions appear in the `DataActions` portion of role definitions and typically include a data-oriented path segment such as `blobServices/containers/blobs/read` for blobs or `secrets/getSecret/action` for Key Vault secrets. If the failing action is a data action and the identity's only assignments are management roles, the plane mismatch is your cause. Inspect a role's data actions directly to see whether it grants the operation:

```bash
az role definition list --name "Storage Blob Data Reader" \
  --query "[].{role:roleName, dataActions:permissions[0].dataActions}" -o json
```

The fix is to assign the data-plane role that contains the failing data action, at the scope where the data lives, in addition to any management role the identity needs for separate management work. For a managed identity that must read blobs from a container, that is a Storage Blob Data Reader assignment scoped to the storage account or container:

```bash
az role assignment create \
  --assignee "<managedIdentityObjectId>" \
  --role "Storage Blob Data Reader" \
  --scope "/subscriptions/<subId>/resourceGroups/rg-prod/providers/Microsoft.Storage/storageAccounts/stprod01"
```

The verification for a data-plane grant is to perform the data operation itself, not a management call, because only the data operation exercises the `DataActions` path. After the assignment propagates, read a blob with the identity and confirm it succeeds. The reason this cause deserves the longest treatment is that it is invisible to the instinct that says a higher role fixes a permission error. No control-plane role, however broad, reaches the data plane. The setup work for identities that need data access pairs naturally with [getting managed identities configured correctly](/configure-managed-identities/), and the same plane split is the root of [a related storage 403 denial worth understanding alongside this one](/fix-storage-403-authorization-error/). The way Azure separates management permissions from data permissions is also the foundation that the broader authorization model builds on, so understanding [the difference between RBAC and attribute-based access control](/azure-rbac-vs-abac-explained/) clarifies why the planes are kept apart.

## Cause Five: A Deny Assignment Blocks the Action

The fifth cause is the one that survives every role you can throw at it, including Owner, which makes it both rare and memorable when it strikes. Azure RBAC supports deny assignments, which explicitly forbid a set of actions for a set of principals at a scope, and deny assignments take precedence over role assignments. If a deny assignment covers the failing action and the principal, no role grant will help, because deny wins. Deny assignments are not something you usually create by hand; they are produced by other systems, most commonly Azure Blueprints that lock resources, managed applications that protect the resources they deploy, and certain platform-managed protections. The effect from the caller's side is an AuthorizationFailed that looks identical to a missing grant but does not respond to any assignment.

Confirm the deny-assignment cause by listing deny assignments at the scope, which the Azure CLI does not surface as cleanly as role assignments, so PowerShell is the reliable tool:

```powershell
Get-AzDenyAssignment -Scope "/subscriptions/<subId>/resourceGroups/rg-prod" |
  Select-Object DenyAssignmentName, @{n='Actions';e={$_.Actions}},
  @{n='Principals';e={$_.Principals.DisplayName}}
```

If a returned deny assignment lists the failing action among its actions and your principal among the principals it applies to, you have found the cause, and the resolution is fundamentally different from the other causes. You cannot out-grant a deny. You have to address the source. If a blueprint assignment created the deny to lock resources, the resolution is at the blueprint assignment, not at the resource. If a managed application owns the resources and its deny protects them, the resolution involves the managed application's access model, not a role on the resource. The diagnostic insight is simply that an AuthorizationFailed that does not respond to a correct, propagated, plane-appropriate role assignment, for the right principal, with no failing condition, is very likely a deny assignment, and the investigation should turn to what system placed it there.

## Cause Six: A Failing Attribute Condition

The sixth cause appears when role assignments carry attribute-based access control conditions. A condition narrows an assignment so that it grants the action only when the request satisfies an expression over attributes of the request, the resource, or the principal. A common pattern conditions a Storage Blob Data role so that it applies only to blobs with a particular index tag, or only for read operations, or only when a request attribute matches a value. When the assignment is present and the role is right but the request does not satisfy the condition, the platform denies it, and the denial can surface as an authorization failure that is invisible to a plain reading of "they have the role."

Confirm the condition cause by inspecting the assignment for a condition rather than only its role and scope. The assignment listing can include the condition field:

```bash
az role assignment list --assignee "<objectId>" --all \
  --query "[?condition!=null].{role:roleDefinitionName, scope:scope, condition:condition}" -o json
```

If an assignment that should cover the action carries a condition, read the condition against the failing request. If the request does not meet it, that is your cause. The fix has two honest branches. If the condition is correct policy and the request genuinely should not be allowed, the answer is not to weaken access but to change the request so it complies, for example by tagging the blob the condition requires. If the condition is too tight for a legitimate need, the answer is to adjust the condition or to add a separate assignment without the condition for the specific need, scoped as narrowly as possible. The way conditions layer onto role assignments is part of the larger authorization model, and the difference between coarse role-based grants and fine attribute-based conditions is exactly what [the comparison of RBAC and ABAC](/azure-rbac-vs-abac-explained/) lays out in depth.

## Cause Seven: The Wrong Principal Was Targeted

The seventh cause is an identity mix-up, and it is more common than its simplicity suggests because Azure has several kinds of principal and several object ids floating around for what feels like one identity. The role was assigned, the portal shows it, and the call still fails because the assignment targets a different principal than the one that ran the call. The application-object-versus-service-principal confusion described earlier is one flavor. Another is a pipeline that authenticates as a service principal the team forgot it was using, while the role was granted to a developer's user account that works fine interactively. Another is a virtual machine with both a system-assigned and a user-assigned managed identity, where the role went to one and the code used the other.

This is why the very first diagnostic step is to capture the object id of the principal that actually made the call, from the error message, and to treat it as authoritative over any assumption about which identity is in play. Confirm the wrong-principal cause by comparing the object id in the error against the object id you granted the role to. If they differ, the grant is real but irrelevant to the failing call. The portal-works-but-the-pipeline-fails pattern is the textbook case: the human's account has access, so manual testing passes, and the automation runs as a separate service principal that has nothing.

Resolve it by assigning the role to the principal that the error names, which for a pipeline service principal means the service principal's object id and for a managed identity means the managed identity's principal id. For a system-assigned managed identity on a virtual machine, fetch the principal id from the machine and grant to that:

```bash
az vm identity show --name "vm-app01" --resource-group "rg-prod" \
  --query "principalId" -o tsv
```

Take that principal id and use it as the assignee in the role assignment so the grant lands on the identity the code authenticates as. The recurring lesson is that an authorization failure is a statement about a specific principal, the one in the message, and granting a role to any other identity, however similar its name, does not change the outcome for the one that failed. Getting the identity itself set up correctly, so that the right principal is the one running the workload, is the configuration discipline that prevents this whole class of mix-up, and the token-level failures that arise when an identity cannot even acquire a credential are a distinct problem from being authenticated but unauthorized.

### Why does the same command work in the portal but fail in my pipeline?

The portal runs as your signed-in user, which has access, while the pipeline authenticates as a separate service principal or managed identity that does not. The object id in the error is the pipeline's identity, not yours. Grant the role to that principal's object id, not to your account.

## Cause Eight: A Custom Role Missing One Action

The eighth cause hides inside an assignment that looks deliberately scoped and correct. A custom role was built to grant exactly what an identity should do, it is assigned at the right scope to the right principal, and one operation still fails because the custom role's `Actions` list does not include the single action that operation needs. Custom roles are defined by hand, and a hand-written action list is easy to leave one entry short, especially for operations whose action string is not obvious from the portal verb. The result is an AuthorizationFailed for one specific operation while everything else the identity does works, which is a strong signal that the role is almost right rather than absent.

Confirm the missing-action cause by reading the action in the error against the custom role's action list. Pull the role definition and inspect its actions:

```bash
az role definition list --name "Custom Storage Operator" \
  --query "[].{role:roleName, actions:permissions[0].actions, notActions:permissions[0].notActions}" -o json
```

Compare the failing action against the `Actions` array, and also against the `NotActions` array, because an action listed under `NotActions` is explicitly removed from the grant even if a wildcard in `Actions` would otherwise include it. If the action is absent from `Actions`, or present in `NotActions`, that is your cause. The fix is to add the specific action to the custom role definition and update it, keeping the addition as narrow as the operation requires rather than widening to a wildcard that pulls in operations you did not intend:

```bash
az role definition update --role-definition '{
  "roleName": "Custom Storage Operator",
  "assignableScopes": ["/subscriptions/<subId>"],
  "permissions": [{
    "actions": [
      "Microsoft.Storage/storageAccounts/read",
      "Microsoft.Storage/storageAccounts/listKeys/action"
    ],
    "notActions": [],
    "dataActions": [],
    "notDataActions": []
  }]
}'
```

Updating a custom role propagates like any assignment change, so apply the same patience the propagation section describes before concluding the addition did not work. The discipline that keeps custom roles maintainable is to add actions one at a time as real operations require them, each justified by an error that named it, rather than to widen the role speculatively. A custom role grown by wildcards to silence errors becomes indistinguishable from Contributor, which defeats the reason to build a custom role in the first place.

## Distinguishing AuthorizationFailed From Its Look-Alikes

Several denials look like AuthorizationFailed at a glance, return a 403, and send engineers down the role-assignment path when the real cause and the real fix live elsewhere. Telling them apart by their error code saves the most time, because the code names the system that denied the request.

The closest look-alike is RequestDisallowedByPolicy, the denial Azure Policy returns when a policy assignment with a deny effect blocks a request. It is a 403 and it stops the operation, but it has nothing to do with RBAC. A policy can forbid creating a resource in a disallowed region, or without a required tag, or of a disallowed SKU, and the request fails with `RequestDisallowedByPolicy` and a message naming the policy. No role assignment fixes a policy denial, because the request never failed on authorization in the RBAC sense; it failed on a governance rule. When the error code is RequestDisallowedByPolicy rather than AuthorizationFailed, stop looking at roles and read the named policy, then either comply with it or change the policy. Confirming a policy denial means reading the code in the error and, if needed, checking policy assignments at the scope:

```bash
az policy assignment list --scope "/subscriptions/<subId>/resourceGroups/rg-prod" -o table
```

A second look-alike sits at the data plane of storage specifically, where a 403 can come from network rules rather than identity. A storage account with a firewall that blocks the caller's network returns a 403 for reasons that have nothing to do with roles; the identity may hold a perfect data-plane role and still be blocked because the request arrived from a network the account rejects. The diagnostic separation is that an RBAC denial names an action and a scope and an authorization failure, while a network block on storage typically presents as an authorization-style failure tied to the request's origin, and adding roles does nothing. The companion troubleshooting for the storage 403 walks that network-versus-identity split in detail, and it is worth keeping distinct from the RBAC case in your head so you do not grant roles to fix a firewall.

A third look-alike is authentication failure masquerading as authorization. AuthorizationFailed means the platform knows who you are and has decided you may not do this. A token acquisition failure means the platform does not yet know who you are, and it produces a different class of error, often an AADSTS code from the identity platform rather than an ARM AuthorizationFailed. When a managed identity cannot get a token at all, you are not authenticated, so authorization never runs, and chasing role assignments wastes time on a problem one layer down. That [token-level failure is its own diagnosis](/fix-managed-identity-token-error/), and keeping the authenticate-then-authorize order straight, first confirm the identity got a valid token, then confirm the token's principal has the role, prevents the most disorienting kind of wild-goose chase.

### Is AuthorizationFailed the same as RequestDisallowedByPolicy?

No. AuthorizationFailed is an RBAC denial: the principal lacks a role granting the action at the scope. RequestDisallowedByPolicy is an Azure Policy denial: a governance rule with a deny effect blocked the request regardless of roles. Read the error code to tell them apart, because role assignments fix the first and never the second.

## How Azure Evaluates an Authorization Request

Understanding the order in which the platform decides a request explains why the causes behave the way they do, and it turns the checklist from a list to memorize into a sequence you can reason about. When a request reaches Azure Resource Manager, the platform gathers the principal that authenticated, the action the request maps to, and the scope it targets, and it walks an evaluation that has a definite shape. First it collects every role assignment that applies to the principal at the target scope and at every ancestor scope, because of downward inheritance, and it collects the principal's group memberships so that group-based assignments count. Then it collects every deny assignment that applies. The decision rule is that the request is allowed only if some role assignment grants the action and no deny assignment forbids it and every attribute condition on the granting assignment is satisfied. Deny is decisive: a single applicable deny assignment forbids the action no matter how many roles would otherwise allow it.

That ordering is the reason Owner cannot override a deny, the reason a fresh assignment that has not yet been collected into the evaluation returns a failure, and the reason a failing condition on the very assignment that would otherwise grant access produces a denial. Each cause maps to a stage of the evaluation. A missing grant means no role assignment was found that allows the action. A wrong-scope assignment means the assignment exists but does not apply at the target scope because it is not an ancestor. A propagation delay means the assignment exists in the directory but has not yet been incorporated into the live evaluation. A plane mismatch means the granted role's permission set does not contain the data action the request requires, so no allowing grant was found for that particular action even though management actions were allowed. A deny assignment means an explicit forbid won. A failing condition means the otherwise-granting assignment did not apply because its condition evaluated false. Holding the evaluation in mind lets you predict which check to run next instead of trying changes at random.

### In what order does Azure decide whether to allow a request?

Azure collects the principal's applicable role assignments across the scope and its ancestors, collects applicable deny assignments, then allows the request only if a role grants the action, no deny forbids it, and every condition on the granting assignment is met. Deny always beats allow, which is why no role overrides a deny assignment.

The practical payoff of the evaluation model is that it gives you a stopping rule for the investigation. If the listing shows a role that should grant the action at a covering scope for the correct principal, you have ruled out the missing-grant, wrong-scope, plane-mismatch, and wrong-principal causes in one pass, and the evaluation model tells you the only remaining stages are propagation, a deny assignment, or a failing condition. Those three are exactly the checks the cause table places at the harder-to-see end, and the evaluation order is why they belong there: they are the stages that can fail even when a correct-looking allow exists. Reasoning from the evaluation rather than from a flat list keeps you from re-checking a stage you already cleared.

## Diagnosing With the Activity Log and PowerShell

The Azure CLI is one lens on the problem, and two others are worth keeping ready because they expose information the CLI does not, or expose it more conveniently. The Activity Log records control-plane operations, including the ones that failed authorization, and reading the failed entry gives you the action, the scope, the caller, and a correlation id in a structured form that is useful when the original error scrolled past in a pipeline log. Query the failed authorization events at a scope to recover the details:

```bash
az monitor activity-log list \
  --resource-group "rg-prod" \
  --status "Failed" \
  --query "[?contains(operationName.value, 'write') || contains(authorization.action, 'Microsoft.')].{time:eventTimestamp, action:authorization.action, scope:authorization.scope, caller:caller, status:status.value}" \
  -o table
```

The Activity Log entry restates the action and scope, which is helpful when the raw error is gone, and it names the caller, which is the authoritative record of which principal the platform evaluated. The correlation id on the entry lets you tie together the steps of a multi-resource deployment so you can see exactly which operation in a larger run was the one that hit the authorization wall. For incidents that arrive as a failed deployment rather than a single command, the Activity Log is frequently the fastest way to recover the four diagnostic facts without rerunning anything.

PowerShell with the Az module is the other lens, and it is the reliable one for deny assignments, which the CLI surfaces poorly, as well as a clean way to do the same role listing and creation for teams standardized on PowerShell. The equivalents map directly. Listing a principal's assignments uses `Get-AzRoleAssignment`:

```powershell
Get-AzRoleAssignment -ObjectId "11111111-2222-3333-4444-555555555555" |
  Select-Object RoleDefinitionName, Scope, ObjectType |
  Format-Table -AutoSize
```

Creating an assignment uses `New-AzRoleAssignment`, with the same least-privilege discipline of role and scope:

```powershell
New-AzRoleAssignment `
  -ObjectId "11111111-2222-3333-4444-555555555555" `
  -RoleDefinitionName "Contributor" `
  -Scope "/subscriptions/<subId>/resourceGroups/rg-prod"
```

And listing deny assignments, the check that has no clean CLI equivalent, uses `Get-AzDenyAssignment` as the deny-assignment section showed. The reason to be fluent in both tools is that an incident does not wait for you to find the one command you remember; the CLI listing, the Activity Log query, and the PowerShell deny check together cover every fact the evaluation model says you might need, and a team that can reach for whichever fits the moment diagnoses faster than one that knows only half the surface.

### How do I find the failed authorization in the Activity Log?

Filter the Activity Log to failed events at the scope and look for entries whose authorization action matches the operation you attempted. The entry restates the action, the scope, and the caller, and carries a correlation id that links the steps of a larger deployment, so you can recover the diagnostic facts even after the original error message is gone.

## Scope Inheritance, Management Groups, and Cross-Subscription Grants

The hierarchy that governs inheritance is worth treating in its own right, because the wrong-scope cause and many of the confusing successes-and-failures trace back to a fuzzy picture of how scopes nest. The chain runs from management groups at the top, through subscriptions, to resource groups, to individual resources, and an assignment at any node applies to that node and everything beneath it. A management group sits above subscriptions and lets you grant once across many subscriptions, which is powerful and correspondingly dangerous: a broad role at a management group reaches every resource in every subscription under it, so the least-privilege instinct applies with extra force the higher you go.

The cross-subscription dimension is where the `--all` flag earns its place. When you list a principal's assignments, the default view is bounded by the current subscription context, so an assignment made in a different subscription, or at a management group that spans subscriptions, can be invisible. The result is a confusing diagnosis where the identity appears to have nothing at the failing scope while in fact it holds a broad grant at a management group above it that you simply did not see. Always list with `--all` when chasing an authorization failure so the full set of assignments across every scope the principal touches is in front of you:

```bash
az role assignment list --assignee "<objectId>" --all \
  --query "[].{role:roleDefinitionName, scope:scope}" -o table
```

Reading that complete list against the hierarchy answers two questions at once: whether any assignment is an ancestor of the failing scope, which would grant access through inheritance, and whether the identity holds broad access somewhere high in the tree that you would want to narrow on principle even if it happens to cover the current need. A management-group Owner that nobody remembers granting is exactly the kind of standing over-permission that an authorization-failure investigation is a good moment to catch and walk back.

Granting at a management group to fix a single subscription's problem is the high-altitude version of the Owner mistake. It works, because inheritance carries the grant down to the failing resource, and it hands the identity reach over every other subscription under that management group as a side effect nobody intended. The discipline is the same at every level: identify the lowest node that is an ancestor of the failing scope and still covers the identity's real work, and grant there. For a single resource group's worth of work, that is the resource group. For work that genuinely spans several groups in one subscription, that is the subscription. Only work that truly spans subscriptions justifies a management-group grant, and that breadth should be a recorded decision rather than a shortcut.

## Guest Users, Cross-Tenant Access, and B2B

A category of authorization failure that looks baffling until you see it involves guest users and cross-tenant access. A guest user invited into your tenant through business-to-business collaboration authenticates against their home tenant but is authorized in your tenant, and the two facts can come apart in ways that produce a clean AuthorizationFailed. The guest can sign in, so authentication clearly worked, and they still cannot act, because no role assignment in the resource tenant grants them the action. The instinct that a user who logged in must have access is wrong for guests: logging in proves the home tenant vouched for who they are, not that the resource tenant granted them anything.

The diagnostic separation is the same one that runs through this whole topic, the line between authentication and authorization, applied across a tenant boundary. The guest's object id in the resource tenant is a distinct directory object from their account in the home tenant, and role assignments must target that resource-tenant object id. Confirm the guest's object id in your tenant and assign roles to it exactly as you would for any other principal:

```bash
az ad user list --filter "mail eq 'partner@othercompany.com'" \
  --query "[].{displayName:displayName, objectId:id, userType:userType}" -o table
```

The userType in that output reading as Guest is the confirmation that you are dealing with a B2B identity, and the object id is the one to grant against. The same principle extends to multi-tenant service principals and to scenarios where automation in one tenant acts on resources in another: authorization is always evaluated in the tenant that owns the resource, against a principal object that lives in that tenant, and a grant in any other tenant is irrelevant to the failing call. When a partner or a cross-tenant automation hits AuthorizationFailed, the question is never whether they authenticated; it is whether the resource tenant holds a role assignment for their identity in that tenant.

## A Second Worked Diagnosis: A Managed Identity Denied Reading Blobs

The first worked example was a control-plane write; this one is the data-plane case that most often defeats the broad-role reflex, walked end to end. An application running on a virtual machine uses its system-assigned managed identity to read a blob from a storage account, and the read fails with an authorization error naming a data action such as `Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read`. The team's first reaction was to grant the identity Contributor on the storage account, the read still failed, and that failure after a broad grant is itself the clue: a control-plane role did nothing for a data action, which is the signature of the plane mismatch.

Begin by capturing the identity that actually made the call, the system-assigned principal id of the virtual machine:

```bash
az vm identity show --name "vm-app01" --resource-group "rg-prod" \
  --query "principalId" -o tsv
```

Confirm that principal id matches the object id in the error, ruling out the wrong-principal case where the machine might carry a user-assigned identity the code used instead. With the correct principal confirmed, read the action: it is a blob read, a data action, which lives in the DataActions portion of role definitions and is not granted by any management role. The fix is a data-plane role scoped to where the data lives. For read-only access to blobs, that is Storage Blob Data Reader, assigned at the storage account or, more tightly, at the specific container:

```bash
az role assignment create \
  --assignee "<vmSystemAssignedPrincipalId>" \
  --role "Storage Blob Data Reader" \
  --scope "/subscriptions/<subId>/resourceGroups/rg-prod/providers/Microsoft.Storage/storageAccounts/stprod01/blobServices/default/containers/app-data"
```

The verification has to exercise the data plane, because a management call would not touch the DataActions path and would prove nothing. After allowing time for the grant to propagate, perform an actual blob read as the identity and confirm it succeeds, for instance by having the application retry its read or by testing the data operation directly. If the read now works, the diagnosis is confirmed and the Contributor grant added earlier should be removed, because it was never the fix and it is a standing over-permission that grants management of the account the application has no reason to perform. Removing the role that did not help is as much a part of the fix as adding the one that did, since leaving it behind is exactly how identities accumulate access nobody can later justify.

This case also illustrates why the data-plane role belongs at the narrowest scope that works. Granting Storage Blob Data Reader at the container rather than the whole account confines the identity to the data it actually reads, so a bug or a compromise cannot range across every container in the account. The scope-precision argument that applies to management grants applies with equal force to data grants, and the container scope is available precisely so that data access can be confined to the data a workload needs.

## When the Same Identity Succeeds and Fails Intermittently

The hardest authorization failures to diagnose are the intermittent ones, where the same identity performing what looks like the same operation succeeds sometimes and fails other times. Intermittency rules out the static causes immediately: a permanently missing grant or a permanent plane mismatch would fail every time, not sometimes, so an operation that flickers between success and failure is pointing at something that changes between attempts. Three mechanisms produce that pattern, and naming them turns a maddening flake into a tractable problem.

The first is propagation interacting with retries. A pipeline that grants a role and then immediately uses it will fail on the attempts that race ahead of propagation and succeed on the ones that land after it, so the same step passes or fails depending on timing alone. The tell is that the failures cluster right after a role assignment was created and stop once enough time has passed. The fix is the separation and bounded retry the prevention section describes: do not exercise a grant in the breath after creating it.

The second is multiple identities masquerading as one. A workload that sometimes authenticates as a managed identity and sometimes as a fallback service principal, or a virtual machine scale set whose instances carry different identity configurations, will succeed on the calls made by the identity that holds the role and fail on the calls made by the one that does not. The tell is that the object id in the error is not always the same; capturing the principal id on every failure, not just the first, reveals that two identities are in play and only one was granted access. The fix is to make the identity deterministic, so the workload always authenticates as the principal that holds the role, and to grant the role to whichever identity the workload should consistently use.

The third is token caching against a changed group membership. When access is granted through a group, a user or workload whose token predates the membership change is evaluated without the group's assignment and fails, while a fresh token after the change succeeds. The tell is that signing out and back in, or restarting a process so it acquires a new token, reliably clears the failure. The fix is to force a token refresh after group changes and to understand that group-based access, for all its manageability benefits, takes effect for an individual only once a new token carries the membership.

### Why does the same call sometimes succeed and sometimes fail with AuthorizationFailed?

Intermittency points at something that changes between attempts, not a static missing grant. The usual three are propagation racing a retry right after a fresh assignment, a workload authenticating as different identities on different calls, and a token that predates a group-membership change. Capture the principal id on every failure and check assignment timing to tell them apart.

## Prevention: Stopping AuthorizationFailed Before It Happens

The errors that never reach production are cheaper than the ones you diagnose mid-incident, and AuthorizationFailed is highly preventable once the team treats authorization as something to design rather than to patch. Prevention rests on a few habits that each remove a whole class of the causes above.

Grant at the right scope from the start by mapping each identity to the lowest scope that covers its real work before you assign anything. An identity that operates on one resource group gets a grant at that group, not the subscription. An identity that genuinely spans many groups gets a subscription grant, with that breadth recorded as a deliberate decision rather than a convenience. This single habit eliminates the wrong-scope cause and shrinks the blast radius of every identity, so that a compromised principal reaches only what it was meant to.

Assign roles to groups rather than to individual users for human access, so that joining and leaving a team is a group-membership change rather than a flurry of per-resource assignments that drift out of sync. Group-based assignment also makes the access auditable, because the question "who can do this" reduces to "who is in this group" plus the group's assignments, rather than a scattered set of direct grants. The one operational subtlety is that group membership rides in the issued token, so a user newly added to a group needs a fresh token before the membership takes effect, which is the same token-refresh discipline propagation already taught.

Separate role creation from role use in automation. A pipeline that grants a role in one step and exercises it in the very next step is racing the propagation window and will fail intermittently in a way that is maddening to reproduce. Granting access in an earlier stage, or in a separate setup pipeline that runs ahead of the workload, removes the race. When the grant and the use genuinely must be close together, a bounded retry that specifically catches the AuthorizationFailed code and waits before retrying converts the propagation window from a failure into a brief, expected pause. This same separation is the fix for the deploy-time sibling of this error, where concurrent operations rather than authorization produce the conflict, and [the deployment-conflict troubleshooting](/fix-azure-deployment-conflict/) covers that race in its own right.

Use managed identities instead of service principals with secrets wherever the platform supports them, because a managed identity removes the credential-expiry and secret-rotation failures that produce a different but adjacent class of access errors, and it ties the identity cleanly to the resource that uses it, which removes the wrong-principal confusion. Setting up managed identities correctly is a configuration topic in its own right, and doing it well prevents both the identity mix-ups in this article and the token failures that look like authorization problems but are not.

Audit effective access on a schedule rather than only when something breaks. The portal's access-check feature answers "what can this identity do here" directly, and the assignment listing answers "what does this identity hold" across scopes. Reviewing those for the identities that matter catches the slow accumulation of over-permission, the Owner grant added to silence an error months ago and never walked back, and the orphaned assignment to a principal that no longer exists. An access model reviewed quarterly stays close to least privilege; one reviewed only during incidents drifts toward everyone-is-Owner, which is where authorization errors stop happening for the worst possible reason.

### How do I prevent AuthorizationFailed errors in deployment pipelines?

Grant the pipeline identity its roles in a setup stage that runs before the deploy stage so propagation completes first, assign at the lowest scope that covers the deploy, target the exact service principal or managed identity the pipeline authenticates as, and add a bounded retry on the AuthorizationFailed code for any grant the pipeline creates and immediately uses.

## A Worked End-to-End Diagnosis

Putting the pieces together, here is the full path from error to fix for a representative case, the kind that arrives as a failed pipeline run with an AuthorizationFailed in the logs. The deploy step tried to write a storage account and the run failed. The first move is not to touch any role. It is to read the four facts out of the error: the principal object id, the action `Microsoft.Storage/storageAccounts/write`, the scope ending in a resource group, and the fact that this is a control-plane write rather than a data action.

With the principal id from the message, list its assignments across all scopes:

```bash
az role assignment list --assignee "<principalIdFromError>" --all \
  --query "[].{role:roleDefinitionName, scope:scope}" -o table
```

Suppose the listing shows a single Reader assignment at the subscription. Reader grants read operations and does not include `storageAccounts/write`, so the action is not covered, which points at cause one, a missing grant for the action, rather than a scope problem. The scope in the error is a resource group, and a write at the resource group is what creating a storage account requires. The least-privilege fix is a management role that includes the write action, scoped to that resource group. If the identity manages only resources in that group, Contributor at the resource group fits, because it grants the write without the right to hand out access to others:

```bash
az role assignment create \
  --assignee "<principalIdFromError>" \
  --role "Contributor" \
  --scope "/subscriptions/<subId>/resourceGroups/rg-prod"
```

Then, rather than rerunning the pipeline immediately and risking the propagation window, confirm the assignment landed and wait for it to take effect:

```bash
az role assignment list --assignee "<principalIdFromError>" \
  --scope "/subscriptions/<subId>/resourceGroups/rg-prod" -o table
```

Once the assignment shows and a short interval has passed, rerun the pipeline. If it still fails with the identical action and scope, the next suspects in order are propagation, if the assignment is correct and fresh, then a deny assignment, checked with `Get-AzDenyAssignment` at the scope, then a wrong principal, by comparing the message's object id against the one you granted to. Walking the causes in that order, from the most common and cheapest to confirm toward the rarest, resolves the overwhelming majority of cases without ever reaching for Owner. This is the method the whole article exists to instill: read the error as a specification, confirm which single cause is in front of you, and grant the smallest thing that satisfies it.

## Common AuthorizationFailed Patterns by Service

Because the fix always starts from the action string, it helps to recognize the action strings the most common services produce and the grant that resolves each, so that the moment you read the operation out of an error you already know which direction to look. The patterns below are a reference for the services where this error shows up most, and they reinforce the control-plane-versus-data-plane split that underlies the whole topic.

Storage produces two distinct families. The management family includes operations like `Microsoft.Storage/storageAccounts/write` to create or update an account and `Microsoft.Storage/storageAccounts/listKeys/action` to read the account keys, both of which are control-plane operations a management grant covers. The data family includes `Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read` and its write counterpart for blobs, and the parallel queue, table, and file operations, all of which are data actions that only a Storage data grant such as Storage Blob Data Reader or Storage Queue Data Contributor satisfies. When a storage error names a path with `blobServices` or `queueServices` in it, you are in the data plane and a management grant will not help.

Key Vault depends on which permission model the vault uses. Under the RBAC model, reading a secret maps to a data action like `Microsoft.KeyVault/vaults/secrets/getSecret/action`, and the grant that covers it is a data-plane definition such as Key Vault Secrets User, while creating or configuring the vault itself is a management operation like `Microsoft.KeyVault/vaults/write` covered by a management grant. A vault still on the older access-policy model authorizes data access through access policies rather than RBAC entirely, which is its own source of confusion and a reason to confirm the vault's permission model before assuming a role assignment is the answer.

Container Registry pulls map to `Microsoft.ContainerRegistry/registries/pull/read`, satisfied by the AcrPull definition assigned to the pulling identity, which for a cluster is usually the cluster's identity rather than a human account. A Kubernetes cluster credential request maps to operations like `Microsoft.ContainerService/managedClusters/listClusterUserCredential/action`, which the Azure Kubernetes Service Cluster User definition grants, and the admin-credential variant is a separate, more sensitive operation with its own grant that should be handed out far more sparingly. Cosmos DB separates control-plane key retrieval, an operation like `Microsoft.DocumentDB/databaseAccounts/listKeys/action`, from its own data-plane access model for reading and writing items, so a grant that lets an identity read the account keys is distinct from one that lets it touch the data.

Messaging services follow the same shape. Sending and receiving on Service Bus or Event Hubs are data-plane operations covered by data grants like the Service Bus Data Sender and Data Receiver definitions, while creating the namespace or the queue is a management operation. The recurring lesson across every service is the one the data-plane cause established: read the action, notice whether its path points at the resource as a managed object or at the data inside it, and grant on the matching plane. An engineer who can glance at an action string and immediately place it on the control plane or the data plane has already done the hardest part of the diagnosis, because that single distinction determines whether any management grant, up to and including Owner, can possibly be the fix.

The action strings themselves are stable enough to recognize but specific enough that you should confirm the exact operation from the error rather than from memory, since resource providers add operations over time and the precise verb matters. The query approach from the action-and-scope section turns any action string into the set of definitions that grant it, so even an operation you have never seen resolves to a concrete grant in one command. Treat the patterns here as a way to know which plane and which family you are in at a glance, and treat the role-definition query as the authoritative way to pin down the exact grant for the exact operation.

## Practicing the Fix

Reading about the diagnosis builds the model; reproducing it builds the reflex, and the two reinforce each other in a way that no amount of reading alone achieves. The fastest way to internalize the action-and-scope rule is to cause an AuthorizationFailed deliberately, read the action and scope out of it, and grant the least-privilege role that clears it, then repeat for a data-plane denial, a wrong-scope assignment, and a propagation delay until each pattern is recognizable on sight. You can run that whole loop in a safe subscription, and you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to reproduce an AuthorizationFailed against storage and Key Vault, inspect the role definitions, and watch the difference between a control-plane and a data-plane grant in a controlled environment. Because diagnosis is a skill that sharpens under pressure, it also helps to [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) that present a failing call and ask you to name the cause and the least-privilege fix before revealing the answer, which trains the ordered checklist this article lays out until walking it becomes automatic.

## The Verdict

AuthorizationFailed is not a wall and it is not a mystery. It is a precise, machine-generated specification of a single missing capability: this principal cannot perform this action at this scope. Treated that way, it has a short list of root causes, each with a confirming check and a least-privilege fix, and the worst thing you can do is reach for Owner, because Owner over-permits, often does not even fix the problem when the failing action lives on the data plane, and trains a habit that erodes the security posture of every scope it touches. Read the action and the scope, confirm the principal, find the smallest role that grants the action, scope it to the smallest place that covers the need, and wait out propagation before you conclude the grant failed. The engineers who handle this error well are not the ones with the broadest access; they are the ones who read the message, because the message already told them exactly what to grant.

## Frequently Asked Questions

### Q: Why do I get an AuthorizationFailed error in Azure?

You get AuthorizationFailed when the security principal that made the call has no role assignment granting the specific action named in the error at the scope named in the error, or when an explicit deny applied. Azure Resource Manager evaluates every request against the principal's role assignments, any deny assignments, and any attribute conditions, and returns a 403 with the AuthorizationFailed code when no assignment grants the action or when a denial wins. The message names the action and the scope precisely, so the cause is one of a small set: a missing grant, an assignment at the wrong scope, a fresh assignment that has not propagated, a control-plane role granted for a data-plane action, a deny assignment, a failing condition, or the role assigned to the wrong principal. Reading the action and scope from the message points you at which one.

### Q: Is AuthorizationFailed caused by a missing role assignment?

A missing role assignment is the single most common cause, but it is not the only one, so confirm before assuming. Run `az role assignment list --assignee <objectId> --all` and check whether any assignment's role includes the action from the error at the failing scope or an ancestor of it. If nothing covers it, the grant is genuinely missing and the fix is to assign the least-privilege role containing the action. If an assignment looks like it should cover the action but the call still fails, the cause is elsewhere: the assignment may sit at the wrong scope, may be too fresh to have propagated, may be a control-plane role for a data-plane action, or may target a different principal than the one that ran the call. The missing-grant case is the first to check precisely because it is the most frequent, not because it is the only possibility.

### Q: Can the wrong scope cause AuthorizationFailed?

Yes, and it is a deceptive cause because the assignment is visibly present, which makes it look like access was granted. Azure RBAC inherits only downward through the hierarchy of management group, subscription, resource group, and resource. An assignment applies to its scope and every descendant, never to an ancestor and never to a sibling. So a Contributor role granted on a single resource does nothing for operations at the resource-group level, such as creating a new resource, and a role granted in one resource group does nothing in another. Confirm by comparing the scope in the error against each assignment's scope and asking whether the assignment scope is the failing scope or a true ancestor of it. If the only assignment is at a child of the failing scope, that is your cause, and the fix is to re-create the assignment at the failing scope or a genuine ancestor.

### Q: Why does a new role assignment take time to take effect?

A role assignment must propagate through the platform after you create it, and during that window a call can still return AuthorizationFailed even though the assignment is correct. The propagation interval is usually a few minutes and is occasionally longer; treat it as a real wait rather than a fixed number, because the timing is a behavior to verify rather than a constant. The error message itself hints at this when it suggests refreshing credentials if access was recently granted. The trap is to assume the assignment did not take and re-create it or escalate to a broader role, which only adds an over-permission with the same propagation wait. The discipline is to confirm the assignment is correct in role, scope, and principal, then refresh the caller's token and wait before concluding anything failed.

### Q: Does a control-plane role grant data-plane access?

No, and this catches more engineers than any other single misconception. Azure separates control-plane permissions, expressed in a role's Actions list, from data-plane permissions, expressed in its DataActions list. A management role like Contributor can create, configure, and delete a storage account or a Key Vault, but it does not grant access to the blobs inside the account or the secrets inside the vault, because those are data actions a management role does not include. Reading a blob needs a Storage Blob Data role; reading a vault secret under the RBAC permission model needs a role like Key Vault Secrets User. This is why assigning Owner to fix a data-plane denial fails: Owner is a control-plane role, and no control-plane role reaches the data plane. Assign the matching data-plane role at the scope where the data lives.

### Q: How do I check the effective permissions for an identity?

Two complementary methods answer it. The portal's access-check feature, available on the Access control blade of any scope, takes an identity and reports what it can do at that scope, which directly answers "is this identity allowed here." For a cross-scope view, list the identity's assignments with `az role assignment list --assignee <objectId> --all`, which returns every assignment across scopes so you can see the full picture rather than one scope at a time. Reading the assignment list against the action and scope from an error tells you whether a grant covers the failing operation. For deny assignments, which the CLI surfaces poorly, use `Get-AzDenyAssignment` in PowerShell at the scope. Together these show what the identity holds, what it is denied, and therefore what it can effectively do.

### Q: Why does assigning the Owner role not fix my AuthorizationFailed error?

Because Owner is a control-plane role, and if the failing action is a data-plane operation, Owner does not grant it. Owner gives full management of resources plus the ability to grant access to others, but reading a blob, getting a secret, or sending a queue message are data actions that live in a role's DataActions list, and Owner's permission set does not include them. So you can assign Owner, create a serious over-permission, and remain locked out of the exact operation you were trying to perform. Owner also fails to help when the real cause is a deny assignment, which outranks every role including Owner, or a failing attribute condition, or the role being assigned to the wrong principal. Read the action in the error first; if it is a data action, the fix is a data-plane role, not a broader management role.

### Q: How do I find the required action and scope in an AuthorizationFailed message?

The message states both explicitly. It names the action in the resource-provider operation format, such as `Microsoft.Storage/storageAccounts/write` or `Microsoft.KeyVault/vaults/secrets/getSecret/action`, which tells you the exact operation that was refused. It names the scope as a full resource path, and the shape of that path tells you the level: a path ending in a resource name is resource scope, one ending in a resource group is resource-group scope, one with only a subscription id is subscription scope, and one under managementGroups is management-group scope. With the action you can query the role definitions to find the smallest role that grants it; with the scope you know exactly where to make the assignment. Together they form a specification for the least-privilege grant that resolves the error.

### Q: Why does access work when I run a command locally but fail in CI?

Because the two run as different identities. A local command runs as your signed-in user account, which has access, while a CI pipeline authenticates as a separate service principal or managed identity that has its own, usually smaller, set of role assignments. The object id in the AuthorizationFailed message is the CI identity, not yours, and granting more access to your account changes nothing for the pipeline. Capture the object id from the error, confirm it is the pipeline's service principal or managed identity, and assign the needed least-privilege role to that principal at the failing scope. This wrong-principal pattern is one of the most common reasons access seems granted but the automation still fails, and the message's object id is the authoritative way to tell which identity actually needs the grant.

### Q: Why am I still blocked by AuthorizationFailed even though I have the Owner role?

The most likely reason is a deny assignment, which explicitly forbids a set of actions for a set of principals at a scope and takes precedence over every role assignment, Owner included. Deny assignments are usually created by other systems, such as an Azure Blueprint that locks resources or a managed application that protects what it deploys, rather than by hand. List them with `Get-AzDenyAssignment` at the scope; if one covers the failing action and your principal, no role will override it, and the resolution is to address the source of the deny rather than to grant more access. A second possibility is that the failing action is a data-plane operation Owner does not include, in which case the fix is a data-plane role. A third is a failing attribute condition on the path that grants access.

### Q: How can an Azure Policy assignment cause a denial that looks like AuthorizationFailed?

An Azure Policy with a deny effect blocks requests that violate a governance rule, such as creating a resource in a disallowed region or without a required tag, and it returns a 403 that can look like an authorization problem. The crucial difference is the error code: a policy denial returns `RequestDisallowedByPolicy` and names the policy, while an RBAC denial returns `AuthorizationFailed` and names an action and scope. No role assignment fixes a policy denial, because the request did not fail on RBAC authorization at all; it failed on a policy rule. When you see RequestDisallowedByPolicy, stop investigating roles and read the named policy, then either bring the request into compliance or change the policy assignment. Reading the error code first prevents the common waste of granting roles against a problem roles cannot touch.

### Q: Does a custom role missing one action cause AuthorizationFailed for just one operation?

Yes, and the telltale sign is that everything the identity does works except one specific operation. A custom role is a hand-written list of allowed actions, and it is easy to leave the list one entry short, especially for operations whose action string is not obvious from the portal verb. The identity then performs every action in the list successfully and fails with AuthorizationFailed on the one action that is absent. Confirm by pulling the custom role definition and comparing the failing action against its Actions array, and also against its NotActions array, because an action under NotActions is removed from the grant even when a wildcard in Actions would otherwise include it. The fix is to add the specific missing action and update the role, keeping the addition narrow rather than widening to a wildcard that pulls in unintended operations.

### Q: How do I find which built-in role grants a specific action?

Query the role definitions and filter on the action string from the error. A command like `az role definition list --query "[?contains(to_string(permissions), '<action>')].roleName"` returns the roles whose permission set includes that action, and from the results you pick the most restrictive one that fits the job rather than the broadest. For data actions, inspect the DataActions portion of candidate roles specifically, since a data operation is granted there rather than in Actions. This query-driven approach replaces guessing or memorizing the role catalog: the error names the action, the role definitions are searchable data, and the intersection is the set of roles that would resolve the error, from which least privilege says to choose the smallest.

### Q: Why does adding a user to a group not immediately fix their AuthorizationFailed?

Group membership is carried in the user's issued token, so a user newly added to a group that holds the needed role does not gain that access until they obtain a fresh token. Their current token was issued before the membership change and does not reflect it, so Azure evaluates their request without the group's assignment and denies it. The fix is to have the user sign out and back in, or otherwise acquire a new token, after which the group membership and its role assignments apply. This is the same token-freshness principle that makes a freshly created direct role assignment seem ineffective until the caller refreshes credentials, and it is why group-based access, while excellent for manageability and auditing, still requires a token refresh to take effect for an individual user.

### Q: Should I assign roles to the application object or the service principal?

To the service principal. An app registration creates two related directory objects: the application object, which is the global definition of the app, and the service principal, which is the local representation of that app in your tenant and the thing that actually authenticates and is authorized. Role assignments must target the service principal's object id, because the service principal is the principal Azure evaluates at request time. Assigning a role to the application object id by mistake records a grant that never applies to the running identity, producing AuthorizationFailed even though the portal appears to show access. Resolve the service principal's object id with `az ad sp show --id <application-client-id> --query id`, and use that value as the assignee so the grant lands on the identity that runs the workload.

### Q: How do I confirm a deny assignment is what is blocking me?

List deny assignments at the failing scope, which the Azure CLI does not surface as readily as role assignments, so use PowerShell: `Get-AzDenyAssignment -Scope <scope>`. Examine each returned deny assignment for whether its actions include the action from your error and whether its principals include your identity, accounting for groups your identity belongs to. If a deny covers both your action and your principal, it is the cause, and no role assignment will override it because deny takes precedence over allow. The resolution is to address whatever placed the deny, commonly a blueprint assignment that locks resources or a managed application protecting its own deployment, rather than trying to grant around it. A correct, propagated, plane-appropriate role for the right principal that still fails is the strongest signal that a deny assignment is in play.

### Q: What is the difference between AuthorizationFailed and a token acquisition failure?

They sit at different layers. AuthorizationFailed means the platform knows who you are, has identified your principal, and has decided that principal may not perform the action, so it is an authorization decision. A token acquisition failure means the platform could not establish who you are in the first place, so authentication failed and authorization never ran. These produce different errors: authorization failures come from Azure Resource Manager as AuthorizationFailed with an action and scope, while token failures typically surface as identity-platform errors, often with an AADSTS code, before any resource request is evaluated. The practical consequence is order: first confirm the identity obtained a valid token, then confirm that token's principal holds the role. Chasing role assignments when the real problem is a managed identity that cannot get a token wastes effort one layer below where the fix lives.

### Q: How do I diagnose AuthorizationFailed for a managed identity on a virtual machine?

Start by identifying which managed identity the code uses, because a virtual machine can carry both a system-assigned identity and one or more user-assigned identities, and the role may be on one while the code authenticates as another. Fetch the system-assigned principal id with `az vm identity show --name <vm> --resource-group <rg> --query principalId`, and for user-assigned identities resolve each identity's principal id separately. Match the principal id against the object id in the error to confirm which identity actually made the failing call. Then list that principal's assignments and apply the standard checks: is there a role covering the action, at the right scope, is the action control-plane or data-plane, and has any recent assignment propagated. The most frequent managed-identity mistake is granting the role to the wrong one of several identities the machine holds.

### Q: Can a NotActions entry in a role cause AuthorizationFailed even with a broad role?

Yes. A role definition can include wildcard Actions that grant a wide range of operations and then explicitly subtract specific operations through NotActions. The effective grant is the Actions set minus the NotActions set, so an operation listed under NotActions is denied even though a wildcard in Actions would otherwise include it. This is how some built-in roles grant broad management while withholding sensitive operations such as granting access to others. If a broad role is assigned and one specific operation fails with AuthorizationFailed while related ones succeed, inspect the role's NotActions for the failing action. The fix is not to widen the role blindly but to use or build a role whose effective grant, after NotActions are subtracted, includes the action the operation needs.

### Q: How do I avoid over-permissioning while fixing AuthorizationFailed under time pressure?

Resist the instinct to grant Owner or Contributor at the subscription to make the error disappear, because that trades a small access gap for a large standing risk that nobody walks back later. Even under pressure, the action-and-scope rule is fast: the error already names the action and the scope, so query the role definitions for the smallest role containing that action and assign it at the failing scope or its nearest covering ancestor. That is usually no slower than a broad grant and it leaves the security posture intact. If you must grant broadly to unblock an incident, record it as a temporary measure with an owner and a date to narrow it, and follow through, because the over-permissions that linger are almost always the ones added during an incident and forgotten once the pressure passed.
