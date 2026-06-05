---
layout: post
title: "Fix AADSTS700016 Application Not Found"
page_title: "Fix AADSTS700016 Application Not Found in the Directory: Diagnose a Wrong Client ID, Wrong Tenant, or Missing Service Principal in Microsoft Entra ID"
date: 2022-09-26
categories: ["Technology"]
tags: ["Azure", "Microsoft Entra ID", "AADSTS700016", "Troubleshooting", "Identity", "Security", "Cloud Computing"]
excerpt: "AADSTS700016 means Entra cannot find your app by its client ID. Diagnose a wrong ID, wrong tenant, or a missing service principal and fix the real cause."
image: "/assets/images/blog/blog-88.webp"
reading_time: 60
author: "ryan-walsh"
last_updated: 2022-09-26
lang: en
---
AADSTS700016 is the error Microsoft Entra ID returns when the application identified by the client ID in your sign-in or token request was not found in the directory the request was sent to. The full message usually reads something close to "Application with identifier 'GUID' was not found in the directory 'tenant'," and it stops authentication before any password, secret, or consent ever comes into play. The error is not about a wrong password, a missing permission, or an expired certificate. It is about identity resolution: Entra looked for an application registered under that client ID in the tenant your request named, and the lookup came back empty.

![Fix AADSTS700016 application not found in the directory root causes - Insight Crunch](/assets/images/blog/blog-88.webp)

That single fact is what makes AADSTS700016 both easy to misread and easy to fix once you read it correctly. The reflex when an app stops authenticating is to assume the registration is broken and to recreate it, generate a fresh client secret, or rebuild the whole app from scratch. That reflex is almost always wrong here, and it costs hours. The application is usually fine. What is wrong is that the client ID and the tenant the request is aimed at no longer agree, or a multitenant application was never provisioned into the tenant that is trying to use it, or the request is hitting an authority that points at the wrong directory entirely. This article walks through every distinct cause, the exact lookup that confirms which one is yours, and the fix for each, so you stop guessing and start resolving the identity the way Entra does.

## What AADSTS700016 actually means

When a client application authenticates against Microsoft Entra ID, the very first thing the identity platform does, before it evaluates credentials, scopes, or conditional access, is resolve the application. It takes the `client_id` (a GUID) from the request, looks at the authority the request was sent to (which names a tenant, directly or indirectly), and asks a simple question: is there an application object or a service principal with this identifier in this directory? AADSTS700016 is the answer "no." The platform could not find the application, so it has nothing to authenticate and it returns the error immediately.

The wording carries two pieces of information that together name the problem. The identifier inside the quotes is the client ID the request presented. The directory name or tenant ID, also in the message, is where Entra looked. If the client ID is right but the directory is wrong, you have a tenant or authority problem. If the directory is right but the client ID is unknown there, you have either a wrong ID or a missing service principal. Reading those two values is the entire first move of the diagnosis, and most engineers skip it and start editing the registration.

A small vocabulary distinction sits under every cause of this error, and it is the distinction the documentation buries. In Entra, a registered application is two related but separate objects. The application object (what you see under App registrations) is the global definition of the app: its client ID, its reply URLs, its requested permissions, its credentials, and whether it is single-tenant or multitenant. The service principal (what you see under Enterprise applications) is the local representation of that app inside a specific tenant: the thing that holds consent grants, role assignments, and the local identity the tenant actually uses. In the tenant that owns the app, both objects exist and share a client ID. In any other tenant that uses a multitenant app, only a service principal exists, created the first time someone in that tenant signs in or consents. AADSTS700016 fires when the request lands in a directory where neither object answers to the client ID it presented.

### Why does Entra return AADSTS700016 instead of a credential error?

Because application resolution happens before credential validation. Entra must first find the app the request claims to be, then check what that app is allowed to do, then validate the secret or assertion. A 700016 means the platform never got past step one, so it cannot reach the point where a wrong secret would matter. The credential is irrelevant until the app is found.

## How to read the error and gather the diagnostic signal

The first thing to do with AADSTS700016 is capture the full error string, not the truncated version a front-end framework shows the user. The complete message, which appears in the redirect response, the token endpoint response body, or the Entra sign-in logs, contains the client ID Entra received and the directory it searched. Both are the diagnostic signal, and you cannot localize the cause without them.

If the failure happens during an interactive sign-in, look at the URL the browser was sent back to or open the browser developer tools network tab and find the request to `login.microsoftonline.com`. The response will carry the `error` and `error_description` parameters, and the description holds the GUID and tenant. If the failure happens on a back-channel token request (a daemon, a service-to-service call, a confidential client), the token endpoint returns a JSON body with `error` set to `unauthorized_client` or `invalid_request` and `error_description` containing AADSTS700016 and the full text. Capture that body from your application logs.

The single most useful place to confirm the values is the Entra sign-in logs. Open the Microsoft Entra admin center, go to the tenant you believe the request is targeting, and look under sign-in logs. A 700016 failure shows up with the application ID the request used and the failure reason. If the sign-in does not appear in that tenant's logs at all, that is itself a strong signal: the request is being evaluated by a different tenant than the one you are looking at, which points straight at an authority or tenant cause.

### Which two values in the message do I need to read first?

Read the client ID (the GUID inside the quotes) and the directory the message names (a tenant ID or a domain). The client ID is what Entra looked for; the directory is where it looked. If the ID is correct but the directory is unexpected, the cause is the authority. If the directory is correct but the ID is unknown there, the cause is the ID or a missing service principal.

Once you have those two values, the rest of the diagnosis is a set of lookups. You will look up the application object by client ID in the tenant you expect to own it, look up the service principal by client ID in the tenant the request actually targeted, and inspect the authority your application code is configured with. Each lookup either confirms or eliminates a cause. The Azure CLI and Microsoft Graph both expose these lookups, and the commands below are the ones to run.

To check whether an application object exists for a given client ID, with the CLI:

```bash
az ad app show --id "11111111-1111-1111-1111-111111111111"
```

If that returns the application, the registration exists in the tenant your CLI session is signed in to. If it returns a "Resource not found" or "does not exist" error, either the ID is wrong or the registration lives in a different tenant. To check the service principal, which is the object that actually authenticates inside a tenant:

```bash
az ad sp show --id "11111111-1111-1111-1111-111111111111"
```

The service principal lookup is the more important of the two for 700016, because authentication resolves against the service principal in the target tenant. An application object can exist in the home tenant while the service principal is missing in the tenant that is trying to use the app, and that gap is one of the most common causes of this error in multitenant scenarios.

Note which tenant your CLI session is pointed at before you trust either result. Run `az account show` to see the active tenant, and use `az login --tenant <tenant-id-or-domain>` to switch to the tenant the error message named. Running `az ad sp show` while signed in to the wrong tenant will report the principal as missing even when it exists in the right one, which sends you chasing the wrong cause.

## The distinct root causes that produce AADSTS700016

AADSTS700016 has a small, finite set of causes, and every real instance reduces to one of them. The client ID is wrong or mistyped. The request is authenticating against the wrong tenant. A multitenant application has no service principal in the resource tenant. The authority is wrong, often the common endpoint where a tenant-specific authority was needed. Or the application registration was deleted while a credential or configuration still references it. Each cause has a distinct confirming lookup and a distinct fix, and the table below is the map.

| Cause | What the message shows | Confirming lookup | Fix |
| --- | --- | --- | --- |
| Wrong or mistyped client ID | A GUID that does not match any app you own | `az ad app show --id <id>` returns not found in the home tenant | Correct the client ID in configuration to the value from the app registration overview |
| Wrong tenant in the authority | Correct client ID, unexpected directory named | Sign-in appears in a different tenant's logs, or none | Point the authority at the tenant that actually owns or has consented to the app |
| Missing service principal (multitenant) | Correct ID, correct resource tenant, app never consented there | `az ad sp show --id <id>` fails in the resource tenant but `az ad app show` succeeds in the home tenant | Provision the service principal through the admin-consent flow or an explicit creation |
| Wrong authority or common vs tenant-specific endpoint | ID correct, request routed to the wrong directory by the endpoint | Inspect the authority URL the client uses; the common endpoint resolved to an unexpected tenant | Use the tenant-specific authority for a single-tenant app, or provision the app in the resolved tenant |
| Deleted app registration | Correct ID that no longer resolves anywhere | `az ad app show --id <id>` fails in every tenant; the app appears in Deleted applications | Restore the registration within the recovery window or recreate and re-provision it |

This table is the findable artifact for this article: the InsightCrunch 700016 cause table, mapping each cause to the lookup that confirms it and the fix that resolves it. Keep it next to your terminal while you work the problem, because the discipline it enforces, running the confirming lookup before applying a fix, is exactly what separates a five-minute resolution from an afternoon of recreating an application that was never broken.

### Cause one: a wrong or mistyped client ID

The simplest cause is also the one engineers dismiss too quickly because they are sure the ID is right. The client ID in your application configuration does not correspond to any application in the directory because it was mistyped, copied from the wrong registration, carried over from a different environment, or pulled from documentation that used a placeholder GUID. Entra looks for that exact GUID, finds nothing, and returns 700016.

To confirm this cause, take the client ID from the error message and look it up in the tenant that should own the app:

```bash
az login --tenant contoso.onmicrosoft.com
az ad app show --id "<client-id-from-error>" --query "{name:displayName, appId:appId}" -o table
```

If the command returns "Resource '<id>' does not exist or one of its queried reference-property objects are not found," the ID does not match an application in this tenant. Now compare the GUID in the error against the Application (client) ID shown on the app registration's Overview blade in the Entra admin center. Read the two values character by character, because the failure is often a single transposed digit or a confusion between the client ID and another GUID on the same blade. The Overview page shows several GUIDs that look alike at a glance: the Application (client) ID, the Directory (tenant) ID, and the Object ID. Configuring the Object ID or the tenant ID where the client ID belongs produces exactly this error.

The fix is to set the client ID in your configuration to the Application (client) ID from the registration overview. Update the value wherever your code reads it: an `appsettings.json`, an environment variable, an MSAL configuration object, a Key Vault secret, or a pipeline variable. After updating, confirm the change took effect by checking what the running application actually loaded, not just what the source file contains, because a stale environment variable or a cached configuration can keep serving the old GUID after the file is corrected.

A subtle variant of this cause is environment drift. The client ID is correct for one environment but the configuration for development, staging, and production share a value through a misconfigured pipeline or a copied template. The app authenticates fine in the environment whose ID is configured and throws 700016 everywhere else. When you see 700016 in one environment but not another, suspect a shared or copied client ID before anything else, and verify that each environment's configuration points at the registration intended for it.

### Cause two: authenticating against the wrong tenant

This cause is the one most often misdiagnosed as a broken registration. The client ID is correct, the application exists, but the request is sent to a tenant where that application has no presence. Entra searches the directory the authority named, finds no application or service principal with that client ID, and returns 700016. The registration is healthy. The request is simply knocking on the wrong door.

The authority in your authentication configuration encodes the tenant. An authority of `https://login.microsoftonline.com/contoso.onmicrosoft.com` or `https://login.microsoftonline.com/<tenant-guid>` targets that specific tenant. If your application was registered in tenant A but the authority points at tenant B, and the app has no service principal in tenant B, the lookup fails. This happens when a configuration is copied from another project, when a tenant ID is hardcoded and the app is later moved, or when a multi-environment setup mixes tenant identifiers.

To confirm this cause, first read the directory the error message names, then check whether your sign-in actually reached the tenant you intended. Open the sign-in logs in the tenant you believe owns the app:

```bash
az login --tenant <expected-tenant>
az ad sp show --id "<client-id>" --query "{name:displayName, appOwnerTenantId:appOwnerOrganizationId}" -o table
```

If the service principal resolves in the tenant you expected, the app is present there, which means the request that failed was not aimed at this tenant. Compare the tenant ID in the error against the tenant ID in your authority configuration. A mismatch confirms the cause: your code is authenticating against a different directory than the one the application lives in.

The fix is to align the authority with the tenant that owns the application, or that has a provisioned service principal for it. For a single-tenant application, set the authority to the home tenant's ID or verified domain. For a multitenant application that genuinely needs to serve multiple tenants, the fix is different and is covered under the next cause, because the issue there is not a wrong authority but a missing local representation in the resource tenant.

### Why does the same app work in one tenant but throw 700016 in another?

Because an application object lives in its home tenant, but every other tenant needs its own service principal for that app, created through consent. The home tenant has both objects and authenticates fine. A second tenant that never consented has no service principal, so the client ID resolves to nothing there and Entra returns 700016 even though the registration is healthy in its home tenant.

### Cause three: a missing service principal in a multitenant scenario

This is the cause that the app object versus service principal distinction exists to explain, and it is the one that most rewards understanding the model. A multitenant application is registered once, in its home tenant, where it has an application object and a home-tenant service principal. When a user or admin from a different tenant signs in to that app for the first time, Entra creates a service principal for the app in their tenant, recording the local consent and identity. Until that service principal exists, the resource tenant has no representation of the app, and any token request that resolves to that tenant returns 700016.

The error appears in several recognizable shapes. A daemon or service that uses the client credentials flow against a customer tenant fails on first run because no one ever consented the app into that tenant, so the service principal was never created. A web app that signs users in from many organizations works for the organizations that have consented and fails for a new organization whose first user has not yet triggered consent. A line-of-business app shared across two tenants in the same company authenticates in the tenant where it was registered and throws 700016 in the sibling tenant that never provisioned it.

To confirm this cause, look up the application object in the home tenant and the service principal in the resource tenant, and watch one succeed while the other fails:

```bash
# In the home tenant: the application object exists
az login --tenant <home-tenant>
az ad app show --id "<client-id>" --query "displayName" -o tsv

# In the resource tenant: the service principal is missing
az login --tenant <resource-tenant>
az ad sp show --id "<client-id>"
```

When the first command returns the app name and the second returns a not-found error, you have confirmed a missing service principal in the resource tenant. The application is registered correctly; it simply has no foothold in the tenant that is trying to authenticate it.

The fix is to provision the service principal in the resource tenant, which you do through consent rather than by editing the registration. For a multitenant app that uses delegated permissions, an administrator in the resource tenant can grant tenant-wide admin consent by visiting the admin-consent URL, which both consents the permissions and creates the service principal in one step:

```
https://login.microsoftonline.com/<resource-tenant>/adminconsent?client_id=<client-id>
```

For an application that uses application permissions through the client credentials flow, the service principal must exist before the app can get a token, and admin consent is required because application permissions always need it. The admin-consent flow above creates the principal and grants the permissions together. If you need to create the service principal explicitly without going through interactive consent, you can create it with the CLI while signed in to the resource tenant:

```bash
az login --tenant <resource-tenant>
az ad sp create --id "<client-id>"
```

This creates the service principal for the multitenant app in the resource tenant, after which the app can authenticate there. Note that creating the principal does not grant any permissions; for application permissions you still need an administrator to consent. The distinction matters: AADSTS700016 is solved by the existence of the service principal, while a permissions error such as AADSTS65001 is solved by consent. The two are different stages of the same provisioning, and confusing them sends you to the wrong fix. The dedicated treatment of that consent failure lives in the companion article on [granting admin consent to clear AADSTS65001](/2022/10/03/fix-aadsts65001-consent-required/), which picks up exactly where the service principal exists but the permissions have not been granted.

### Cause four: a wrong authority or the common endpoint where a tenant-specific one was needed

Microsoft Entra exposes several authority endpoints, and choosing the wrong one routes your request to a directory that cannot resolve your application. The common endpoint, `https://login.microsoftonline.com/common`, is meant for multitenant apps and tells Entra to figure out the user's tenant from the sign-in. The organizations endpoint behaves similarly for work and school accounts. The consumers endpoint targets personal Microsoft accounts. A tenant-specific authority names exactly one directory by ID or domain. The mistake that produces 700016 is using the common endpoint for an application that is registered as single-tenant, or letting the common endpoint resolve to a tenant where the app has no service principal.

When a single-tenant application uses the common endpoint, Entra resolves the user's home tenant and looks for the application there. If the user belongs to a tenant other than the one the app is registered in, the lookup fails with 700016 because the single-tenant app exists only in its home directory. The app works for users in its home tenant, who resolve to the right directory, and fails for everyone else, which can look like an intermittent or user-specific problem when it is really an authority and registration-type mismatch.

To confirm this cause, inspect the authority your client is configured with and the sign-in account's home tenant. In an MSAL configuration this is the `authority` or `Instance` plus `TenantId` setting. If the authority is `common` or `organizations` and the application's registration is single-tenant (its supported account types are set to "Accounts in this organizational directory only"), and the failing user belongs to a different tenant, the cause is confirmed. The sign-in logs in the user's home tenant will show the failed application resolution, while the app's home tenant logs show nothing for that sign-in.

The fix depends on intent. If the app is meant to serve only one organization, use the tenant-specific authority so every request is evaluated against the directory that owns the app:

```csharp
var app = ConfidentialClientApplicationBuilder
    .Create(clientId)
    .WithClientSecret(clientSecret)
    .WithAuthority("https://login.microsoftonline.com/<your-tenant-id>")
    .Build();
```

If the app is genuinely meant to serve multiple organizations, change the registration's supported account types to a multitenant option and ensure each consuming tenant provisions a service principal through consent, which is the cause-three fix. The deciding factor is whether the app should authenticate users from one directory or many; pick the authority and the registration type to match, and do not mix a single-tenant registration with the common endpoint. The mechanics of authorities, endpoints, and the v1 versus v2 sign-in flow are covered in depth in the treatment of [how Entra authentication and its endpoints work](/2023/12/18/entra-id-authentication-explained/), which is the article to read when you need the full model rather than the fix.

### Cause five: a deleted or recreated app registration

The last cause is the most permanent-looking and the easiest to confirm once you suspect it. The application registration was deleted, but a credential, a configuration file, or another service still references its client ID. Entra has no application or service principal under that ID, so every request returns 700016 regardless of tenant. A variant is an app that was deleted and recreated: the new registration has a new client ID, and any configuration still pointing at the old ID fails.

This happens during cleanup that removes an app still in use, during a migration that recreates registrations with new IDs, or when one team deletes an app another team depends on. The signature is that the client ID resolves nowhere, in any tenant, and the app cannot be found in App registrations.

To confirm, attempt the lookup in the home tenant and then check the deleted applications list, which holds recently deleted registrations during a recovery window:

```bash
az login --tenant <home-tenant>
az ad app show --id "<client-id>"   # fails: not found

# List recently deleted applications
az rest --method GET \
  --uri "https://graph.microsoft.com/v1.0/directory/deletedItems/microsoft.graph.application?\$filter=appId eq '<client-id>'"
```

If the app appears in the deleted items list, it was deleted within the recovery window and can be restored. If it does not appear, either the recovery window has passed or the app was never in this tenant. Restoring the app preserves its client ID and credentials, which means every dependent configuration starts working again without changes:

```bash
az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/directory/deletedItems/<object-id>/restore"
```

If restoration is not possible because the window has passed, the fix is to create a new registration, then update every dependent configuration to the new client ID and re-provision service principals and consent in each tenant that used the old app. There is no way to recreate an app with a specific prior client ID, so a deletion past the recovery window forces a configuration update everywhere the old ID was used. This is why deleting an in-use registration is costly, and why the prevention section below treats registration ownership and lifecycle as a first-class concern.

## The right-tenant rule for AADSTS700016

Every cause above reduces to one principle, and naming it gives you a single test to run before you touch anything. The client ID must resolve to an application or service principal in the tenant named by the authority. Call it the right-tenant rule: 700016 is always a statement that the identifier and the directory do not agree, so the fix is to make them agree, by correcting the ID, redirecting the authority, or provisioning the service principal, and almost never by recreating the application.

The rule turns a confusing error into a two-step check. First, is the client ID correct and does it point at a real application? Second, does the tenant the request targets contain an application object or service principal for that ID? If the answer to the first is no, you have a wrong or mistyped ID, or a deleted app. If the answer to the first is yes but the second is no, you have a wrong authority or a missing service principal. That branch covers every instance of the error, and it replaces the folk model "the registration is broken, recreate it" with the real model "the identity did not resolve in the directory the request named."

The reason engineers reach for recreation is that the error feels like the app is gone, and recreating it sometimes appears to work, because the new app happens to be created in the tenant the request targets and consent provisions a service principal as a side effect. But that accidental fix leaves the original problem, a wrong authority or a stale ID, in place, and it orphans the old registration and any consent and role assignments attached to it. Worse, it changes the client ID, so any other consumer of the old registration now fails. Applying the right-tenant rule instead of recreating keeps the existing registration, its credentials, its consent grants, and its role assignments intact, and fixes only the thing that was actually wrong.

## How each cause maps to where you see the error

The same error code surfaces in different flows, and where it appears narrows the cause before you run a single lookup. In an interactive authorization-code flow, the user is redirected to sign in and the error returns in the redirect, which means the authority and the registration type are the first suspects, because interactive sign-in is where the common endpoint and single-tenant mismatch bite. In a client credentials flow used by a daemon or service, the error returns from the token endpoint on a back-channel call, and the first suspect is a missing service principal in the resource tenant, because client credentials require the principal to exist and there is no interactive consent to create it on the fly.

In a device code or username-password flow, the same authority and tenant logic applies as in interactive sign-in. In an on-behalf-of flow, where a middle-tier service exchanges a user token for a downstream token, a 700016 on the exchange usually means the middle-tier app's client ID is wrong or its service principal is missing in the tenant the token is scoped to. Reading which flow failed tells you which causes are even possible, and that alone cuts the diagnosis in half.

The Entra sign-in logs distinguish interactive and non-interactive sign-ins and record the application ID and the failure reason for each, which is why they are the authoritative place to confirm what the request actually presented. A back-channel failure that your application logs as a generic authentication error will appear in the non-interactive sign-in logs with the precise application ID and the 700016 reason, and matching that logged ID against your configuration is often the fastest confirmation of a wrong or stale client ID.

## Confirming the fix worked

After applying a fix, confirm it the way Entra resolves identity rather than by watching the application succeed once, because a single success can hide a partial fix. The confirming check is that the service principal now resolves in the target tenant and that a token request succeeds end to end.

For a confidential client using client credentials, request a token directly against the token endpoint to isolate the identity resolution from the rest of your application:

```bash
curl -X POST "https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token" \
  -d "client_id=<client-id>" \
  -d "scope=https://graph.microsoft.com/.default" \
  -d "client_secret=<client-secret>" \
  -d "grant_type=client_credentials"
```

A successful response returns an access token and no error. If 700016 still appears, the identity has not resolved in this tenant: re-check that the service principal exists with `az ad sp show --id <client-id>` while signed in to the tenant in the URL, and re-check that the client ID in the request matches the registration. If a different error appears, such as a consent or permission error, the 700016 is solved and you have moved to the next stage, which is permissions rather than identity resolution.

For an interactive flow, sign in with a user from the target tenant and confirm the authorization request reaches the sign-in page rather than returning the error in the redirect. Then check the tenant's sign-in logs and confirm the application now appears with a successful or expected-next-step result. Seeing the application resolve in the logs of the tenant the request targets is the durable confirmation that the right-tenant rule is now satisfied.

## Diagnosing AADSTS700016 with Microsoft Graph and PowerShell

The Azure CLI lookups are the fastest path for most engineers, but the same diagnosis runs through Microsoft Graph directly and through the Microsoft Graph PowerShell module, and knowing the Graph queries pays off when you are scripting onboarding or auditing many tenants at once. Graph is also the authoritative surface, because the CLI and the portal are both clients of it, so a Graph query removes any doubt about what the directory actually holds.

To find the application object by client ID through Graph, query the applications collection filtered on the appId, which is the client ID:

```bash
az rest --method GET \
  --uri "https://graph.microsoft.com/v1.0/applications?\$filter=appId eq '<client-id>'" \
  --query "value[].{name:displayName, appId:appId, signInAudience:signInAudience}" -o table
```

The `signInAudience` field in that response is worth reading, because it tells you whether the registration is single-tenant (`AzureADMyOrg`) or multitenant (`AzureADMultipleOrgs` or one of the personal-account variants). A single-tenant audience combined with a common-endpoint authority is the cause-four signature, and seeing it in the Graph response confirms the mismatch without opening the portal. An empty `value` array means no application object exists in the tenant your token is scoped to, which is the wrong-ID or wrong-tenant signature.

To find the service principal, query the servicePrincipals collection on the same appId, because that collection is where the per-tenant identity lives:

```bash
az rest --method GET \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals?\$filter=appId eq '<client-id>'" \
  --query "value[].{name:displayName, appId:appId, accountEnabled:accountEnabled}" -o table
```

An empty result here, in the tenant the failing request targeted, is the decisive confirmation of a missing service principal, and the `accountEnabled` field catches the rarer case where a principal exists but has been disabled, which produces a related sign-in failure rather than 700016 but is worth ruling out in the same pass.

The Microsoft Graph PowerShell module expresses the same two lookups for engineers who live in PowerShell. After connecting with `Connect-MgGraph` against the target tenant, the application and service principal queries read naturally:

```powershell
Connect-MgGraph -TenantId "<tenant-id>" -Scopes "Application.Read.All"
Get-MgApplication -Filter "appId eq '<client-id>'" |
  Select-Object DisplayName, AppId, SignInAudience
Get-MgServicePrincipal -Filter "appId eq '<client-id>'" |
  Select-Object DisplayName, AppId, AccountEnabled
```

The same interpretation applies: the application query answers whether the registration exists in the connected tenant, and the service principal query answers whether the local identity exists there. When you are checking many tenants, wrap the service principal query in a loop over your tenant list and flag any tenant where it returns nothing, because that flag is a 700016 waiting to happen the next time a request resolves to that tenant. This is the audit that turns the missing-service-principal cause from a production surprise into a pre-checked onboarding step.

When you provision through Graph rather than the CLI, creating a service principal for a multitenant app is a POST to the servicePrincipals collection with the appId in the body:

```bash
az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals" \
  --body '{"appId": "<client-id>"}'
```

This is the Graph equivalent of `az ad sp create --id`, and it is the call that admin consent performs under the hood before it records the consent grant. Running it explicitly during onboarding is exactly the prevention the cause-three discussion recommends, and doing it through Graph lets you script it into the same automation that grants consent and assigns roles.

## Where the client ID and authority live in your application code

Because two of the five causes are configuration disagreements between the client ID and the authority, knowing exactly where each value lives in your stack is half the fix. The values surface in different places depending on the authentication library, and the most common version of this error is a stale or copied value in one of those places that no longer matches the registration. The MSAL family of libraries is the canonical client for Entra, and the configuration point is the same idea in every language: a client ID, a tenant or authority, and a credential are assembled into a client object.

In .NET, a confidential client is built with the client ID, the authority, and a secret or certificate, and the authority is where the tenant is named:

```csharp
var app = ConfidentialClientApplicationBuilder
    .Create("<client-id>")
    .WithClientSecret("<client-secret>")
    .WithAuthority("https://login.microsoftonline.com/<tenant-id>")
    .Build();
```

If the `Create` argument and the `WithAuthority` tenant come from different configuration sources, they can drift, and a 700016 is the result when the client ID belongs to one tenant and the authority names another. The fix is to source both from one configuration object per environment, and the diagnosis is to log the exact values the built client used, not the values the source file declares.

In Python, the MSAL `ConfidentialClientApplication` takes the client ID, the authority, and the credential as constructor arguments, and the same drift applies:

```python
import msal

app = msal.ConfidentialClientApplication(
    client_id="<client-id>",
    authority="https://login.microsoftonline.com/<tenant-id>",
    client_credential="<client-secret>",
)
result = app.acquire_token_for_client(
    scopes=["https://graph.microsoft.com/.default"]
)
```

When `acquire_token_for_client` returns a result containing an `error` of `unauthorized_client` and an `error_description` carrying AADSTS700016, the client ID did not resolve in the tenant the authority named. Print the `authority` value and the `client_id` the application object was constructed with, and compare them against the registration; a mismatch is the confirmation.

In Node.js, the `@azure/msal-node` `ConfidentialClientApplication` reads the same trio from a configuration object, with the authority under `auth.authority`:

```javascript
const { ConfidentialClientApplication } = require("@azure/msal-node");

const cca = new ConfidentialClientApplication({
  auth: {
    clientId: "<client-id>",
    authority: "https://login.microsoftonline.com/<tenant-id>",
    clientSecret: "<client-secret>",
  },
});
```

The Java MSAL library and the JavaScript browser library MSAL.js follow the identical pattern, a client ID and an authority assembled together, which means the diagnosis transfers across every stack: find where the client ID is set, find where the authority or tenant is set, and confirm they name the same directory. The recurring production failure is that one of those two values is templated, hardcoded, or copied from another service while the other is environment-specific, so they agree in the environment they were authored for and disagree everywhere else. Logging the resolved pair at startup, behind a debug flag, turns this from a guessing game into a one-line confirmation.

The values also live outside code, in places that are easy to forget. A managed identity or a workload identity federation setup names a client ID in its configuration. A Terraform or Bicep deployment that creates the registration emits the client ID as an output that downstream resources consume, and a recreated registration changes that output. A Kubernetes secret, an App Service application setting, a GitHub Actions or Azure Pipelines variable, and a Key Vault secret are all common homes for the client ID, and any of them can hold a stale value after a registration is recreated. The discipline that prevents the error is to have exactly one source of truth for each environment's client ID and authority and to reference it everywhere rather than copying it.

## Workload identity federation and AADSTS700016

Federated credentials let an external workload, such as a GitHub Actions job or a Kubernetes pod, exchange its own issuer-signed token for an Entra token without a stored secret. The federation binds an issuer and a subject to the registration, and the exchange still begins with application resolution by the registered identifier. If that identifier is mistyped in the workflow, points at a recreated registration with a new value, or names an object that does not exist in the directory the exchange targets, the federated exchange fails with AADSTS700016 before the issuer-signed assertion is ever evaluated. The federation setup is healthy; the identity simply did not resolve.

This produces a recognizable pattern. A pipeline that ran for months stops working after someone recreated the registration during a cleanup, because the recreated object carries a fresh identifier while the workflow still references the old one. The federated trust, the issuer, and the subject all look correct, which sends engineers to inspect the federation configuration when the real problem is upstream at resolution. Confirm by reading the identifier the workflow presents against the current registration overview, and by looking up the object in the directory the exchange targets. A not-found result means the recreation left a stale reference behind.

The fix mirrors the deleted-registration remedy: restore the original object within its recovery window so the identifier is preserved and the pipeline works unchanged, or update the workflow to the new identifier and re-establish the federated credential against the recreated object. The prevention is to treat the registration backing a federated workload as a protected, owned resource, exclude it from automated cleanup, and source its identifier from the registration itself rather than pasting it into a workflow file where it silently goes stale when the object is rebuilt. Because federation removes the stored secret, the registration object becomes the single point whose continuity the whole pipeline depends on, which makes its lifecycle protection more important, not less.

## The v1.0 and v2.0 endpoints and how they affect resolution

Entra exposes two generations of sign-in and token endpoints, the v1.0 endpoints under `login.microsoftonline.com/<tenant>/oauth2/` and the v2.0 endpoints under `login.microsoftonline.com/<tenant>/oauth2/v2.0/`, and while application resolution works the same way on both, a few differences interact with 700016 in ways worth knowing. Both endpoints resolve the application by client ID against the tenant in the path, so a wrong tenant or a missing service principal fails identically on either. The difference that matters is in how scopes and audiences are expressed, which can change which tenant a request effectively targets and therefore where the resolution happens.

On the v2.0 endpoint, scopes are fully qualified resource URLs or the `.default` scope, and the client credentials flow uses `scope=<resource>/.default`. On the v1.0 endpoint, the equivalent is the `resource` parameter naming the target API. A request that mixes the two, sending a v1.0-style `resource` to a v2.0 endpoint or the reverse, can fail in confusing ways, though the failure is usually a malformed-request error rather than 700016. The cleaner mental model is that the endpoint generation does not change application resolution, so when you see 700016, the endpoint version is rarely the cause and you should keep your attention on the tenant in the path and the client ID in the request.

Where the endpoint generation does intersect with 700016 is in libraries that default to one generation and configurations that assume the other. MSAL uses the v2.0 endpoints by default. Older ADAL-based code uses v1.0. If a configuration was carried over from an ADAL application to an MSAL one without updating the authority format, the authority may be malformed in a way that resolves to an unexpected tenant or the common endpoint, indirectly producing 700016 for single-tenant apps. The fix is to use the MSAL authority format with an explicit tenant for single-tenant apps, and to let MSAL manage the endpoint generation rather than hand-constructing v1.0 URLs.

The token endpoint you call directly for a confirmation, shown earlier as the v2.0 client-credentials request, is the right one to use for diagnosis because it is the modern default and because its error responses carry the full AADSTS700016 text in the `error_description`. Calling it with an explicit tenant in the path removes any ambiguity about which directory is resolving the application, which is exactly the property you want when you are confirming that the right-tenant rule is now satisfied.

## National clouds and sovereign authority hosts

The commercial Azure cloud is not the only Entra environment, and an application registered in one cloud does not exist in another. Microsoft operates sovereign and national clouds with their own authority hosts: the commercial cloud uses `login.microsoftonline.com`, while government and regional clouds use different hosts entirely. An application registered in the commercial cloud has no presence in a government cloud directory, so a request that reaches a government authority host for a commercial-cloud app resolves against a directory where the app does not exist and returns 700016.

This cause appears when configuration is copied between cloud environments, when a library defaults to the commercial host while the app lives in a sovereign cloud, or when an infrastructure layer rewrites the authority host as described in the indirect-causes section. The signature is that the client ID is correct for the cloud the app was registered in, but the authority host points at a different cloud. Confirm by reading the full authority host, not just the tenant, and checking it against the cloud where the registration actually lives.

The fix is to set the authority host to the cloud the application is registered in. MSAL exposes cloud instance settings, often called the Azure cloud instance or the national cloud, that select the correct host, and the libraries provide named constants for the known clouds so you do not hand-type the host. For a confidential client, set the instance to the cloud where the app lives and the tenant within it, and the request will resolve against the right directory. If an application genuinely needs to operate across clouds, it must be registered separately in each cloud's directory, because registrations do not span clouds, and each cloud's registration has its own client ID. This makes cross-cloud scenarios a multi-registration problem rather than a multitenant one, and conflating the two is a common path into 700016.

## A second worked example: a single-page app failing for external users

The daemon example showed a back-channel failure; the interactive case has a different shape worth walking through. A single-page application uses MSAL.js to sign users in, and it works for everyone in the company's tenant. A partner organization's users, invited as guests or signing in to a multitenant app, hit AADSTS700016 on sign-in, redirected back with the error instead of reaching the app.

Reading the error first: the client ID in the message is the SPA's correct ID, and the directory named is the partner's tenant. The SPA's authority is configured as `common`, which is typical for a multitenant SPA. The client ID being correct and the directory being the partner's tenant points away from a wrong ID and toward either a single-tenant registration or a missing service principal in the partner tenant.

Confirming the cause: query the application's `signInAudience` through Graph, which returns `AzureADMyOrg`, meaning the registration is single-tenant. A single-tenant app on the common endpoint resolves each user's home tenant and looks for the app there; the partner's users resolve to the partner tenant, where this single-tenant app does not exist, so the lookup fails. That is the cause-four signature exactly: a single-tenant registration paired with a multitenant authority.

The decision the fix turns on is whether the SPA should serve only the company or also partners. If only the company, the fix is to set the authority to the company's tenant-specific host so external users are never routed to a directory without the app, and to handle partner users as guests in the company tenant instead. If the SPA should serve partners as their own organizations, change the registration's supported account types to multitenant and ensure each partner tenant provisions a service principal through consent, after which the common endpoint resolves correctly for partner users. The deciding factor is the intended audience, and the same registration-type-and-authority pairing that prevents cause four is the durable fix. Confirming it means watching a partner user reach the sign-in page rather than the error, and seeing the SPA's application resolve in the partner tenant's sign-in logs.

## The prevention that stops a recurrence

AADSTS700016 recurs for structural reasons, and a few habits remove most of them. The first is treating the client ID and the authority as a matched pair that travel together through configuration. Storing them separately, or letting one be hardcoded while the other is environment-specific, is what allows them to drift apart. Keep the client ID, the tenant ID, and the authority for each environment in one configuration source, ideally a secret store such as Key Vault referenced per environment, so that a deployment cannot mix a development client ID with a production tenant. The credential-free pattern of referencing identity configuration from a managed store rather than copying it between projects is the same discipline that prevents the wrong-tenant and stale-ID causes.

The second habit is provisioning service principals deliberately for multitenant apps rather than relying on the first interactive sign-in to create them. For any tenant that will use a multitenant app through a back-channel flow, run the admin-consent flow or create the service principal explicitly as part of onboarding that tenant, before the first daemon run. This removes the cause-three failure that otherwise surfaces on first execution in production, which is the worst time to discover that no one ever consented the app into the customer's directory.

The third habit is protecting registration lifecycle. App registrations in active use should be owned, tagged, and excluded from automated cleanup, and deletion should be gated behind a check for active consumers. Because a deletion past the recovery window forces a client ID change everywhere, the cost of an accidental delete is far higher than the cost of a registration that lingers unused. Where registrations are recreated as part of infrastructure as code, capture the client ID as an output and feed it into every dependent configuration automatically, so a recreated app never leaves a stale ID behind. The broader model of what a registration contains and how application objects and service principals relate is laid out in the deep dive on [Entra app registrations and reply-URL configuration](/2024/03/04/entra-app-registrations-explained/), which is the reference to keep for the structure these habits protect.

The fourth habit is choosing the registration type and the authority to match intent at registration time. Decide whether an app serves one organization or many before you register it, set the supported account types accordingly, and configure the authority to match: a tenant-specific authority for single-tenant apps, and the common or organizations endpoint plus per-tenant provisioning for multitenant apps. Getting this pairing right at the start prevents the cause-four mismatch that otherwise appears only when a user from an unexpected tenant tries to sign in.

### How do I make this error impossible in a new environment?

Store the client ID, tenant ID, and authority together in one per-environment configuration source so they cannot drift apart, provision the service principal in each target tenant during onboarding rather than on first use, and protect the registration from automated deletion. These three habits remove the wrong-ID, missing-principal, and deleted-app causes before they can occur.

## Why the error sometimes appears as unauthorized_client

The AADSTS700016 text is the precise signal, but the OAuth-level error name that wraps it varies by flow, and that variation trips up engineers who match on the wrapper rather than the AADSTS code. On the token endpoint, a 700016 commonly arrives with the OAuth error `unauthorized_client`, which reads as a permissions failure and pulls attention toward consent and roles. It is not an authorization failure; it is an identity-resolution failure wearing an authorization-shaped label, because from the protocol's view an unresolvable client cannot be an authorized one. The fix is to read past the OAuth wrapper to the AADSTS code in the `error_description`, which names the real stage, and to treat `unauthorized_client` plus AADSTS700016 as the not-found case rather than a consent case.

On the authorization endpoint during interactive sign-in, the same condition can surface with `invalid_request` or a generic error, again with AADSTS700016 in the description. The lesson is consistent: the AADSTS code is authoritative and the OAuth error name is a coarse category that can mislead. Build any automated handling on the AADSTS code, not the wrapper, and when reading a log line, find the AADSTS number before reacting to the word next to it. This single habit prevents the most common misdirection, which is treating a not-found app as a consent problem because the wrapper said `unauthorized_client` and then adding permissions that the app, not yet resolvable, can never use.

## The on-behalf-of flow and chained application resolution

The on-behalf-of flow, where a middle-tier API exchanges an incoming user token for a token to call a downstream API, resolves two applications rather than one, and a 700016 on the exchange names which link in the chain failed. The middle-tier service authenticates as itself using its own client ID and credential, and Entra must resolve that middle-tier application in the tenant the token is scoped to. If the middle-tier app's client ID is wrong, or its service principal is missing in that tenant, the exchange fails with 700016 even though the incoming user token was valid and the downstream API is registered correctly.

Reading the error in this flow means identifying which application the message names. If the client ID in the error is the middle-tier app's ID, the failure is in resolving the middle-tier service, and the diagnosis is the standard one: confirm the ID and the service principal in the scoped tenant. A common variant is a multitenant API that works in its home tenant and fails the on-behalf-of exchange for users from other tenants, because the middle-tier app has no service principal in those tenants, exactly the cause-three pattern applied to an API rather than to a daemon. The fix is the same, provision the middle-tier app's service principal in each consuming tenant through consent.

The downstream resolution is the second link. After the middle-tier app is resolved and its token request accepted, Entra resolves the downstream API the token targets. A 700016 naming the downstream resource's identifier points at a wrong resource client ID or audience in the middle-tier's request, or a downstream API not provisioned in the tenant. Distinguishing the two links comes down to reading which identifier the error names, and the chained nature is why on-behalf-of failures reward the message-first discipline more than any other flow: the message tells you which application, of the two in play, did not resolve, and that alone localizes the fix to the right registration.

## The related failures AADSTS700016 is often confused with

AADSTS700016 sits in a family of Entra sign-in errors that look similar in a log line but mean different things, and confusing them sends you to the wrong fix. The most important distinction is between application resolution, which is 700016, and the errors that occur after the app is found.

AADSTS50011 is the redirect URI mismatch. It fires after the application is found, when the reply URL in the request does not match a URL registered on the app. If you see 50011, the app resolved correctly, which means none of the 700016 causes apply; the problem is purely the reply URL. The full diagnosis of that mismatch, including the exact-match rule and the platform-type trap, is in the article on [fixing the AADSTS50011 redirect mismatch](/2022/09/19/fix-aadsts50011-redirect-uri/), and the clean separation is worth remembering: 700016 is "we could not find your app," 50011 is "we found your app but its reply URL does not match."

AADSTS65001 is consent required. It also fires after the app is found and even after the service principal exists, when the user or administrator has not consented to the permissions the app requests. This is the error you may hit immediately after fixing a cause-three missing service principal, because creating the principal does not grant permissions. If 700016 turns into 65001, you have made progress: the identity now resolves and the remaining work is consent.

AADSTS7000215 and related credential errors indicate an invalid client secret or assertion, which again can only appear after the app is found, because the credential is validated only once the application is resolved. If you were getting 700016 and now get a credential error, the identity resolution is fixed and the secret is the new and separate problem.

The pattern across all of these is sequence. Entra resolves the application, then checks the redirect URI, then evaluates consent, then validates the credential. AADSTS700016 is the failure at the first stage, and every other error in the family is a failure at a later stage, which means seeing any of them is proof that the 700016 cause is behind you. Reading the error code as a position in that sequence tells you immediately whether you are still fighting identity resolution or have moved on to a downstream concern.

## A worked example: a daemon failing in a customer tenant

To make the diagnosis concrete, consider a common production scenario. A background service uses the client credentials flow to read data from a customer's tenant using a multitenant application registered in your own tenant. The service has worked for three existing customers. You onboard a fourth, deploy the same code with the new customer's tenant ID in the authority, and the first run fails with AADSTS700016 naming the new customer's directory.

Reading the error first: the client ID in the message is your app's correct ID, and the directory named is the new customer's tenant. The client ID resolving correctly and the directory being the expected target points away from a wrong ID and a wrong authority. The flow is client credentials, back-channel, which makes a missing service principal the leading suspect, because there was no interactive sign-in to create one.

Confirming the cause: sign in to your home tenant and confirm the application object exists with `az ad app show --id <client-id>`, which it does. Then sign in to the customer's tenant and run `az ad sp show --id <client-id>`, which fails with not found. The application is registered correctly in your tenant and has no service principal in the customer's tenant, which is exactly the cause-three signature.

Applying the fix: an administrator in the customer's tenant grants admin consent by visiting `https://login.microsoftonline.com/<customer-tenant>/adminconsent?client_id=<client-id>`, which creates the service principal and consents the application permissions in one step. Confirming the fix: re-run `az ad sp show --id <client-id>` in the customer's tenant, which now returns the principal, then request a token against the customer's token endpoint, which now succeeds. The 700016 is gone, and if a consent or permission error had appeared instead, that would have confirmed the identity resolution was fixed and moved the problem to the permissions stage. The lesson the example teaches is the prevention: provision the service principal during onboarding, not on the first production run, so the failure never reaches a customer-facing deployment.

## When the fix is not what it appears

A few situations produce AADSTS700016 through an indirect path, and recognizing them saves a long detour. A reverse proxy or a load balancer that rewrites the authority host can route a request to a different cloud instance, such as a national or government cloud, where the application is not registered, producing the error even though the configuration looks correct in your code. Confirm by reading the exact authority host the request reached, not the one your configuration intends, because an infrastructure layer can change it.

A token cache holding a token for a stale or deleted app can mask and then unmask the error: the app works while the cached token is valid and fails with 700016 when the cache expires and a fresh resolution is attempted against an app that no longer resolves. When an app fails only after running fine for a while, suspect a cached token over a configuration that was already broken. A configuration management system that templates the client ID across many services can propagate a wrong or stale ID to every consumer at once, turning a single registration mistake into a fleet-wide 700016; the fix is to correct the template source and redeploy, and the prevention is to source the ID from the registration itself rather than from a hand-maintained template.

Each of these is a variant of the same underlying causes, surfaced through an extra layer. The right-tenant rule still applies: in every case, the client ID and the directory the request actually reached do not agree, and the fix is to make them agree at the layer that broke the agreement, whether that is your code, your infrastructure, your cache, or your configuration pipeline. The model of how Entra represents applications and identities across tenants, which underpins all of these variants, is covered in the foundational treatment of [Microsoft Entra ID and the app-versus-service-principal model](/2022/02/21/microsoft-entra-id-explained/), the article to read when you want the why behind the rule rather than the fix.

## Reading the Entra sign-in logs and correlation IDs for AADSTS700016

The sign-in logs are the authoritative record of what each request presented, and for AADSTS700016 they answer the two questions the diagnosis turns on: which application ID the request used and which tenant evaluated it. Because the error happens during application resolution, the failed sign-in is recorded in the directory the request reached, which is the most reliable way to discover whether your request landed in the tenant you intended. A failure that does not appear in the tenant you expected, but does appear in another, is direct proof that the authority routed the request to the wrong directory.

Open the sign-in logs in the Microsoft Entra admin center for the tenant under investigation, and filter by the application or by the failure. Each failed entry carries the application ID, the timestamp, the client app and flow, and a correlation ID. The application ID is the value to match against your configuration; a mismatch between the logged ID and the registration's Application (client) ID is an immediate confirmation of a wrong or stale client ID. The flow field distinguishes interactive from non-interactive sign-ins, which tells you whether to suspect the authority and registration type (interactive) or the missing service principal (non-interactive client credentials).

The correlation ID is the value to keep when a failure resists diagnosis. It ties together the request across Entra's internal logging, and it is the identifier to provide if you open a support case, because it lets the platform trace the exact request that failed. Capturing the correlation ID from the error response or the sign-in log entry, alongside the timestamp and the tenant, is the difference between a support interaction that resolves quickly and one that stalls for lack of a way to find the request.

For scripted analysis, the sign-in logs are queryable through Microsoft Graph and through Log Analytics when sign-in logs are exported to a workspace. A Kusto query over the SigninLogs table that filters on the result code surfaces every 700016 across the tenant, grouped by application, which turns a scattered set of complaints into a single view of which apps are failing resolution and in which tenants:

```kusto
SigninLogs
| where ResultType == "700016"
| summarize Failures = count() by AppId, AppDisplayName, bin(TimeGenerated, 1h)
| order by Failures desc
```

That query is the fleet-level version of the single lookup, and it is how you catch a templated wrong client ID that has propagated to many services at once, because they all show up under the same failing AppId. It is also how you confirm a fix at scale: after correcting the configuration, the failure count for that AppId drops to zero, which is the durable signal that the resolution is now succeeding across every consumer rather than just the one you tested by hand.

## Automating tenant onboarding to prevent the missing-principal cause

The missing service principal is the cause that hurts most in production because it surfaces on the first run in a new tenant, which is usually a customer-facing moment. The prevention is to make service principal creation and consent an explicit, scripted step in onboarding a tenant, run before any workload executes against that tenant, rather than relying on an interactive sign-in to create the principal as a side effect. Scripting it also makes onboarding auditable: you can prove a tenant was provisioned rather than discover it was not when a daemon fails.

A minimal onboarding script for a multitenant application that uses application permissions does three things in order: it creates the service principal in the customer tenant, it triggers admin consent for the application's permissions, and it confirms the principal resolves. The first two steps are what the admin-consent URL performs interactively, and scripting them removes the dependency on a human clicking through consent at the right moment. The confirmation step is the same `az ad sp show` lookup the diagnosis uses, run here proactively:

```bash
#!/usr/bin/env bash
set -euo pipefail
CLIENT_ID="<multitenant-app-client-id>"
TENANT="<customer-tenant-id>"

az login --tenant "$TENANT" >/dev/null

# Create the service principal for the multitenant app in the customer tenant
az ad sp create --id "$CLIENT_ID" 2>/dev/null || echo "Service principal may already exist; continuing."

# Confirm the principal now resolves in this tenant
if az ad sp show --id "$CLIENT_ID" >/dev/null 2>&1; then
  echo "Service principal present in $TENANT. Resolution will succeed."
else
  echo "Service principal still missing in $TENANT. Investigate before deploying." >&2
  exit 1
fi
```

Creating the principal clears AADSTS700016, but application permissions still require an administrator to grant consent, so the script's existence does not replace the consent step; it guarantees the identity exists so that the next failure, if any, is a consent error rather than a not-found error. That ordering is deliberate, because moving the failure from identity resolution to consent moves it from a confusing 700016 to a clear consent prompt that an administrator can act on directly. For tenants where you cannot run the script with sufficient privileges, the fallback is to send the administrator the admin-consent URL, which performs the principal creation and consent together in one approval.

The same automation belongs in any infrastructure-as-code pipeline that stands up a new environment. When a deployment creates an application registration, capture its client ID as an output and feed that exact value into every dependent resource and into the onboarding script for each tenant, so the principal is created against the real, current client ID rather than a hand-copied one. This closes the loop on three causes at once: the client ID is sourced from the registration so it cannot be stale, the service principal is provisioned so it cannot be missing, and the authority is set from the same source so it cannot drift from the ID.

## A diagnosis you can run from memory

The fastest engineers do not consult the cause table for every instance; they internalize the decision tree and run it from memory in under a minute. The tree has exactly two branches off the right-tenant rule, and walking it in order names the cause before you touch any configuration. Start by reading the client ID and the directory from the error message, then ask the first question.

Is the client ID correct, matching the Application (client) ID on the registration overview? If you cannot answer yes with certainty, that is the first thing to confirm, because a wrong or stale ID is the most common cause and the cheapest to check. Look it up with `az ad app show --id` in the home tenant; if it does not resolve anywhere, you have a wrong ID or a deleted app, and the deleted-items query distinguishes them. If the ID is correct and resolves to a real application, move to the second question.

Does the tenant the request targeted contain a service principal for that ID? Sign in to that tenant and run `az ad sp show --id`. If the principal is present, the app exists in the tenant and the request that failed must have been aimed at a different tenant, which sends you back to the authority configuration to find where it points. If the principal is absent, you have a missing service principal, which for a multitenant app is the cause-three provisioning fix and for a single-tenant app on the common endpoint is the cause-four authority-and-registration-type fix. Reading the registration's sign-in audience tells you which.

That is the whole tree: confirm the ID resolves, then confirm the principal exists in the targeted tenant, and the cause is named. Everything else, the deleted app, the wrong authority, the national cloud, the proxy rewrite, is a variant of one of those two answers, distinguished by where the disagreement between the ID and the directory was introduced. Running this from memory is what makes 700016 a five-minute fix, and it is the habit the worked examples and the cause table are designed to build.

## Closing verdict

AADSTS700016 is an identity-resolution failure, not a broken application, and treating it as the former is what makes it a quick fix instead of a long one. The error says exactly one thing: the client ID in the request did not resolve to an application or service principal in the directory the request named. Read the two values in the message, apply the right-tenant rule, and the cause falls into one of five buckets, each with a confirming lookup and a targeted fix. A wrong or mistyped ID is corrected in configuration. A wrong tenant is fixed by aligning the authority. A missing service principal in a multitenant scenario is provisioned through admin consent or explicit creation. A wrong authority or common-endpoint mismatch is fixed by matching the authority to the registration type. A deleted registration is restored within the recovery window or recreated with a configuration update everywhere.

The single most valuable habit is to resist recreating the application, because the registration is almost never the problem and recreation orphans the consent, the role assignments, and the client ID that the rest of your estate depends on. Run the confirming lookup, find the disagreement between the ID and the directory, and fix that disagreement. To reproduce a not-found application end to end and drill the tenant lookup until the diagnosis is automatic, [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) and [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html), where you can register a multitenant app, watch a daemon fail in a tenant with no service principal, and confirm the fix the way Entra resolves identity.

## Frequently Asked Questions

### Q: What does AADSTS700016 application not found in the directory mean?

It means Microsoft Entra ID could not find an application or service principal matching the client ID in your request inside the tenant the request was sent to. The error happens during application resolution, the very first step of authentication, before any credential, scope, or consent is evaluated. The full message names two values: the client ID Entra looked for and the directory it searched. If the ID is unknown in that directory, Entra has nothing to authenticate and returns the error immediately. It is an identity-resolution failure, not a credential or permission problem, which is why fixing the secret or adding a permission does nothing for it. The fix is to make the client ID and the targeted directory agree, by correcting the ID, redirecting the authority, or provisioning the service principal.

### Q: Does a wrong or mistyped client ID cause AADSTS700016?

Yes, and it is the simplest cause to confirm. If the GUID in your configuration does not match any application in the directory, Entra finds nothing and returns the error. The mistake is often a single transposed character, or configuring the Object ID or the Directory (tenant) ID where the Application (client) ID belongs, because all three appear together on the registration's Overview blade and look alike. Confirm by running `az ad app show --id <id>` in the home tenant and comparing the returned value against the Application (client) ID on the Overview page, reading character by character. The fix is to set the configured client ID to the exact Application (client) ID and verify the running application loaded the corrected value, since a cached environment variable can keep serving the old GUID after the file is fixed.

### Q: Can the wrong tenant or authority cause AADSTS700016?

Yes. If the client ID is correct but the authority points at a tenant where the application has no application object or service principal, Entra searches that directory, finds nothing, and returns the error. The registration is healthy; the request is simply aimed at the wrong directory. This happens when an authority is copied from another project, a tenant ID is hardcoded and the app is later moved, or a multi-environment setup mixes tenant identifiers. Confirm by comparing the tenant in the error message against the tenant in your authority configuration, and by checking that the service principal resolves in the tenant you expected with `az ad sp show --id <id>`. The fix is to set the authority to the tenant that owns the app or has a provisioned service principal for it.

### Q: Is a missing service principal the cause of AADSTS700016 in multitenant apps?

Often, yes. A multitenant application is registered once in its home tenant, where it has both an application object and a service principal. Every other tenant needs its own service principal, created the first time someone consents to the app. Until that service principal exists, the resource tenant has no representation of the app, and any request resolving to that tenant returns the error. This is the classic failure for daemons using client credentials against a customer tenant on first run, because there was no interactive sign-in to create the principal. Confirm by checking that `az ad app show` succeeds in the home tenant while `az ad sp show` fails in the resource tenant. The fix is to provision the service principal through the admin-consent flow or by running `az ad sp create --id <id>` in the resource tenant.

### Q: Does the common versus tenant-specific endpoint matter for AADSTS700016?

It matters a great deal. The common endpoint tells Entra to resolve the user's home tenant and look for the app there. If the application is registered as single-tenant, it exists only in its home directory, so a user from any other tenant resolves to a directory where the app is not found, producing the error. The app then works for home-tenant users and fails for everyone else, which can look like a user-specific glitch. Confirm by checking whether the authority is `common` or `organizations` while the registration's supported account types are single-tenant. The fix is to use a tenant-specific authority for a single-tenant app, or to change the registration to multitenant and provision a service principal in each consuming tenant. Match the authority to the registration type.

### Q: How do I confirm the app is registered in the tenant I am targeting?

Sign in to that specific tenant and look up both objects by client ID. Run `az login --tenant <tenant>` to point your session at the right directory, then `az ad app show --id <client-id>` to check for the application object and `az ad sp show --id <client-id>` to check for the service principal. Authentication resolves against the service principal, so its presence in the target tenant is the decisive check. Verify your active tenant with `az account show` before trusting the result, because running the lookup against the wrong tenant reports the principal as missing even when it exists elsewhere. You can also open the Entra sign-in logs in that tenant; a 700016 failure appears there with the application ID and reason, and its absence means the request reached a different tenant.

### Q: Should I recreate the app registration to fix AADSTS700016?

Almost never. The registration is rarely the problem, and recreating it causes new ones. A new registration has a new client ID, which breaks every other consumer of the old ID, and it orphans the consent grants and role assignments attached to the original app. Recreation sometimes appears to work because the new app is created in the tenant the request targets and consent provisions a service principal as a side effect, but that masks the real cause, a wrong authority or a stale ID, and leaves it in place. Apply the right-tenant rule instead: confirm whether the client ID is correct and whether the target tenant contains the app, then fix the specific disagreement. This preserves the credentials, consent, and role assignments your estate depends on.

### Q: Why does my daemon get AADSTS700016 on its first run in a new tenant?

Because the client credentials flow it uses is a back-channel call with no interactive sign-in, and a multitenant app needs a service principal in each tenant before it can get a token there. The first three customers worked because someone consented the app into their tenants, creating the principal. The new customer's tenant never had that step, so no service principal exists and the identity does not resolve. Confirm with `az ad sp show --id <client-id>` in the new tenant, which fails, while `az ad app show` succeeds in your home tenant. Fix it by having an admin in the new tenant grant admin consent at the adminconsent URL, which creates the principal and consents the permissions together. Prevent it by provisioning the principal during onboarding rather than on the first production run.

### Q: What is the difference between an app registration and a service principal in AADSTS700016?

The application object, under App registrations, is the global definition of the app: its client ID, reply URLs, requested permissions, and credentials, plus whether it is single-tenant or multitenant. The service principal, under Enterprise applications, is the local representation of that app inside one specific tenant, holding that tenant's consent grants, role assignments, and the identity it actually uses to authenticate. The home tenant has both objects sharing a client ID; any other tenant using a multitenant app has only a service principal, created through consent. AADSTS700016 fires when the targeted directory has neither object for the presented client ID. Authentication resolves against the service principal, which is why a missing principal in a resource tenant produces the error even when the application object is healthy in the home tenant.

### Q: How do I provision a service principal for a multitenant app without interactive consent?

Sign in to the resource tenant and create the principal explicitly with `az ad sp create --id <client-id>`, which registers the multitenant app's service principal in that directory. After this, the app can resolve and authenticate in the tenant. Creating the principal does not grant any permissions, so for application permissions an administrator must still consent, either through the adminconsent URL or by granting consent on the enterprise application. The distinction matters: the existence of the service principal clears AADSTS700016, while the grant of permissions clears a consent error such as AADSTS65001. They are separate stages of the same provisioning. For onboarding automation, create the principal and grant consent as scripted steps so a new tenant is fully provisioned before the first token request rather than failing on first use.

### Q: Why does AADSTS700016 appear only after the app worked fine for a while?

Suspect a cached token over a configuration that was already broken, or a deleted registration. While a previously issued token remains valid, your app uses it and never re-resolves the application, so the underlying problem stays hidden. When the cache expires and a fresh resolution runs against an app that no longer resolves, the error surfaces. A deleted registration produces the same timing: the app runs on a valid token, then fails on the next resolution after deletion. Confirm by checking whether the registration still exists with `az ad app show --id <client-id>` and whether it appears in the deleted applications list. If it was deleted within the recovery window, restore it to preserve the client ID; if not, recreate it and update every dependent configuration to the new ID.

### Q: Can a reverse proxy or load balancer cause AADSTS700016?

Yes, when it rewrites the authority host and routes the request to a directory or cloud instance where the app is not registered. A proxy that changes the host can send a request intended for the commercial cloud to a national or government cloud endpoint, where your application has no registration, producing the error even though your code's configuration looks correct. Confirm by reading the exact authority host the request actually reached rather than the one your configuration intends, since an infrastructure layer can alter it in transit. The fix is to correct the host rewriting at the proxy so the request reaches the cloud instance and tenant where the app is registered. The right-tenant rule still applies: the ID and the directory the request actually hit must agree.

### Q: How do I restore a deleted app registration to fix AADSTS700016?

If the registration was deleted within the recovery window, it sits in the directory's deleted items and can be restored with its original client ID and credentials intact, which makes every dependent configuration work again without changes. Find it by querying the deleted applications through Microsoft Graph with a filter on the appId, then restore it by posting to the restore endpoint for its object ID. In the CLI this is an `az rest` call to `directory/deletedItems/microsoft.graph.application` to find it and a POST to the restore path to recover it. If the recovery window has passed, restoration is not possible and you must create a new registration, which gets a new client ID, then update every configuration and re-provision service principals and consent in each tenant that used the old app.

### Q: Does AADSTS700016 mean my client secret is wrong?

No. The credential is validated only after the application is resolved, so a 700016 means Entra never reached the point where the secret would be checked. If the app cannot be found, its secret is irrelevant. This is why regenerating the client secret does nothing for this error and why you should not start there. If you fix the identity resolution and then see a credential error such as AADSTS7000215, that is progress: the app now resolves and the secret is a separate, later-stage problem. Reading the error as a position in Entra's sequence, resolve the app, check the redirect URI, evaluate consent, validate the credential, tells you that 700016 is the first stage and a secret error is a much later one.

### Q: How can I tell AADSTS700016 apart from AADSTS50011 and AADSTS65001?

By where each sits in Entra's authentication sequence. AADSTS700016 is application resolution: Entra could not find the app, so nothing downstream runs. AADSTS50011 is a redirect URI mismatch that fires after the app is found, when the request's reply URL does not match a registered one; seeing it proves the app resolved correctly. AADSTS65001 is consent required, firing after the app is found and even after the service principal exists, when permissions have not been granted. The practical signal is that if you were getting 700016 and now get 50011 or 65001, the identity resolution is fixed and you have moved to a later stage. Each code is a different point of failure, so treating them as interchangeable sends you to the wrong fix.

### Q: Why do I get AADSTS700016 in one environment but not another?

Almost always because of a shared or copied client ID across environments. When development, staging, and production share a configuration value through a misconfigured pipeline or a copied template, the app authenticates fine in the environment whose registration the ID actually matches and throws 700016 everywhere else. The same happens when a tenant ID is environment-specific but the client ID is hardcoded, so the pair drifts apart. Confirm by checking that each environment's running configuration loads the client ID and tenant intended for that environment, not just what the source file declares. The fix is to give each environment its own correct client ID and authority, and the prevention is to store the ID, tenant, and authority together per environment in one source so they cannot diverge.

### Q: How do I verify the AADSTS700016 fix actually worked?

Confirm it the way Entra resolves identity, not by watching the app succeed once. First, check that the service principal now resolves in the target tenant with `az ad sp show --id <client-id>` while signed in to that tenant. Then request a token end to end. For a confidential client, post a client-credentials request directly to the token endpoint for the target tenant; a response containing an access token and no error confirms resolution. If 700016 still appears, the principal is still missing or the ID is still wrong. If a different error appears, such as consent required, the resolution is fixed and you have advanced to the permissions stage. For interactive flows, sign in with a user from the target tenant and confirm the request reaches the sign-in page and the app appears in that tenant's sign-in logs.

### Q: Can creating the service principal alone resolve AADSTS700016 without granting consent?

Yes for the resolution error itself, but not for everything the app needs. AADSTS700016 is about whether the identity exists in the tenant, and creating the service principal makes it exist, so the not-found error clears. However, creating the principal grants no permissions. If the app uses application permissions, you will immediately hit a consent error because those always require an administrator to grant consent. So creating the principal is the correct and complete fix for 700016 specifically, and it often reveals the next stage, a consent requirement, which is a separate problem with its own fix. Treat the two as distinct: the principal's existence answers "can Entra find the app here," and consent answers "is the app allowed to do what it is asking."

### Q: Why does the common endpoint resolve to an unexpected tenant for AADSTS700016?

The common endpoint resolves the signing-in user's home tenant and looks for the app there. If your app is single-tenant, it exists only in its own directory, so a user whose home tenant differs from the app's registration tenant resolves to a directory without the app and triggers the error. Even for a multitenant app, the common endpoint will resolve to whatever tenant the user belongs to, and if that tenant has never provisioned a service principal, the lookup still fails. Confirm by noting the failing user's home tenant and comparing it to where the app is registered and provisioned. The fix is to use a tenant-specific authority for single-tenant apps, and for multitenant apps to ensure each consuming tenant has a service principal before users from it sign in.

### Q: What is the fastest way to diagnose AADSTS700016 in production?

Read the two values in the error message first, the client ID and the directory, then run one lookup in the named tenant. If the client ID is correct and the directory is the one you intended, sign in to that tenant and run `az ad sp show --id <client-id>`. A missing principal points to the multitenant provisioning cause; a present principal points to a wrong ID or a request that reached a different tenant than the logs suggest. If the directory in the message is not the one you intended, the cause is the authority, and you check the configured authority against the tenant you meant to target. This message-then-one-lookup sequence resolves the cause in under a minute and tells you exactly which fix to apply, without recreating anything.
