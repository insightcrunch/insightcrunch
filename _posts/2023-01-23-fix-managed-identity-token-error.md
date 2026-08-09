---
layout: post
title: "Fix Managed Identity Token Failures"
page_title: "Managed Identity Token Error: Fix ManagedIdentityCredential, IMDS, and DefaultAzureCredential Failures in Azure"
date: 2023-01-23
categories: ["Technology"]
tags: ["Azure", "Managed Identity", "Troubleshooting", "Identity", "Security", "Cloud Computing"]
excerpt: "A managed identity token error usually means the identity is unassigned, the wrong type, missing a role, or aimed at the wrong audience. Fix each cause."
image: "/assets/images/blog/blog-01.webp"
reading_time: 60
author: "nathan-cole"
last_updated: 2026-08-09
lang: en
---
A managed identity token error is the moment a workload that was supposed to authenticate without any stored secret suddenly cannot prove who it is. The application code asks the platform for a token, the request comes back empty or with an exception such as `ManagedIdentityCredential authentication failed`, and every downstream call to Key Vault, Storage, or the Azure Resource Manager returns a 401 or a 403. The temptation in that moment is to abandon the credential-free design, paste a client secret back into the configuration, and move on. That reaction trades a five-minute diagnosis for a long-term liability, because a stored secret is a credential someone now has to rotate, guard, and eventually leak. The faster path is to understand that a managed identity does not hold a secret at all. It asks an endpoint on the host for a token, and a token request fails for a small, finite set of reasons. Learn those reasons, learn the one command that confirms each, and the failure becomes routine rather than mysterious.

![Fixing Azure managed identity token errors and ManagedIdentityCredential failures - Insight Crunch](/assets/images/blog/blog-01.webp)

This article diagnoses the managed identity token error down to its real causes and gives the confirming check and the tested fix for each. The thesis the whole piece defends is what I will call the identity-plus-role rule: a token request fails when the principal is either not present on the resource or lacks the role on the thing it is trying to reach, so the correct fix is always to verify both the assignment and the authorization, never to regress to a secret. Hold that rule in mind and the rest of the diagnosis falls into place. Everything that follows is an elaboration of where the assignment can be missing, where the authorization can be missing, and the handful of edge cases (the wrong identity type, the wrong audience, the absence of any identity at all on a developer laptop) that produce the same symptom through a different mechanism.

## What a managed identity token error actually means

Before any diagnosis is useful you have to know what is supposed to happen on the happy path, because the error is always a deviation from that path. A managed identity is an account that the Azure platform creates and maintains for a resource. Unlike a service principal that you create yourself with an associated secret or certificate, the platform owns the credential material for a managed identity and never exposes it to you. Your workload never sees a password. Instead, when the code needs to call another Azure service, it asks a local endpoint on the host for a short-lived bearer token, presents that token to the target service, and the target validates it. The endpoint that issues the token is the part most engineers have never looked at directly, and it is where a surprising number of failures originate.

On a virtual machine or a scale set instance, that endpoint is the Azure Instance Metadata Service, reachable at the link-local address 169.254.169.254. The address is non-routable and only answers from inside the instance, which is part of why it is considered reasonably safe to expose without authentication of its own. A raw token request looks like this:

```bash
# From inside a VM or VMSS instance, request a token for ARM
curl -s -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/"
```

A healthy response is a JSON object containing an `access_token`, an `expires_on` timestamp, the `resource` the token is good for, and a `token_type` of `Bearer`. The `Metadata: true` header is mandatory; omit it and the metadata service refuses the request as a defense against server-side request forgery, where an attacker tricks a vulnerable application into making the call on their behalf. The `api-version` query parameter selects the contract version, and the `resource` parameter is the audience, meaning the specific service the token is minted for. That last parameter matters enormously and is the source of an entire class of failure I will return to.

The detail that trips up the most people is that the 169.254.169.254 address is only the right endpoint on a VM or a scale set. App Service, Azure Functions, and Container Apps do not expose the metadata service to your app the same way. Instead they inject two environment variables, `IDENTITY_ENDPOINT` and `IDENTITY_HEADER`, and your code is expected to call the value of `IDENTITY_ENDPOINT` while passing the value of `IDENTITY_HEADER` in an `X-IDENTITY-HEADER` header. If you hardcode the VM address inside an App Service application you will get a connection failure that looks like the metadata service is down, when in reality you were knocking on a door that was never there. A direct request on App Service looks closer to this:

```bash
# From inside an App Service or Functions host
curl -s -H "X-IDENTITY-HEADER: $IDENTITY_HEADER" \
  "$IDENTITY_ENDPOINT?resource=https://vault.azure.net&api-version=2019-08-01"
```

Almost nobody should be writing these raw calls in production. The reason to know them is diagnostic: when the Azure Identity client library reports a token failure, dropping down to the raw request tells you whether the problem is in the platform plumbing or in your application's use of the library. The library, exposed as `DefaultAzureCredential` and `ManagedIdentityCredential` across the .NET, Python, JavaScript, Java, and Go SDKs, wraps all of this and picks the right endpoint for the host automatically. When it works you never think about IMDS. When it fails, you need the model underneath it.

### What does a managed identity token error look like in practice?

It usually surfaces as an SDK exception rather than a raw HTTP code. The most common string is `ManagedIdentityCredential authentication failed`, often wrapped inside a broader `DefaultAzureCredential failed to retrieve a token` message that lists every credential the chain tried. The downstream symptom is a 401 from the target service when no token was attached, or a 403 when a token was attached but lacked authorization.

The distinction between those two downstream codes is the first fork in the diagnosis, and getting it right saves an enormous amount of wasted effort. A 401 Unauthorized from the target means the request arrived without a valid bearer token at all. That points upstream, at the token acquisition itself: the metadata endpoint was unreachable, no identity was assigned, the wrong identity was selected, or the token was minted for the wrong audience and the target rejected it as not intended for itself. A 403 Forbidden means the request arrived with a perfectly valid token whose subject the target recognizes, but that subject has no permission to perform the operation. That points at authorization, specifically a missing role assignment on the target resource. The same code that fixes a 401 will do nothing for a 403, and the reverse is equally true, so resist the urge to start granting roles before you know which code you are actually seeing.

## How to read the error and gather the diagnostic signal

A token failure is a chain of distinct steps, and effective diagnosis walks that chain from the bottom up: is there an endpoint, does an identity exist on the resource, is the right identity being selected, does that identity hold the role on the target, and is the token aimed at the correct audience. Each step has a confirming command, and the discipline of running them in order is what separates a quick fix from an afternoon of guessing.

Start by capturing the exact error, not a paraphrase of it. The Azure Identity libraries are deliberately verbose when a chained credential fails, and the full message names which credential in the chain failed and frequently why. In Python you turn on logging so the chain narrates its decisions:

```python
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("azure.identity")
logger.setLevel(logging.DEBUG)

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://my-vault.vault.azure.net", credential=credential)
secret = client.get_secret("db-password")
```

With logging at debug level the chain reports each credential it attempts and the reason each one declined. On a developer laptop you will see the managed identity step decline because no metadata endpoint answered, then the chain fall through to the Azure CLI credential. Inside Azure you will see the managed identity step either succeed or fail with a specific reason. That narration is the single most useful artifact in the whole investigation, and most teams never enable it.

Next, confirm whether the host can reach a token endpoint at all. On a VM, the raw curl above either returns JSON or it does not, and the failure mode is informative: a connection refused or a timeout against 169.254.169.254 means the metadata path is blocked or the address is being intercepted by a proxy. A 400 with a `bad request` body usually means you malformed the query, most often by forgetting the `Metadata: true` header. A 400 with an `identity not found` style body means the endpoint is reachable but no identity is assigned to the resource, which is a different problem entirely and lives in the next section.

Finally, when a token does come back but the target still rejects it, decode the token and read its claims. A bearer token is a JSON Web Token, and its middle segment is a Base64Url-encoded JSON payload you can inspect without any secret. Two claims matter most for this diagnosis: `aud`, the audience the token was minted for, and `oid` or `appid`, the object or application id of the principal the token represents. If `aud` does not match the service you are calling, you have an audience problem. If `oid` is not the identity you expected, you selected the wrong identity. Reading the token turns a vague rejection into a precise fact:

```bash
# Decode the payload (middle segment) of a captured token without verifying the signature
TOKEN="eyJ0eXAiOiJKV1Qi..."   # the access_token value
echo "$TOKEN" | cut -d '.' -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

That handful of checks (the verbose chain log, the raw endpoint probe, and the decoded token claims) gathers every signal the diagnosis needs. With those facts in hand you can map the symptom to exactly one of the causes below rather than trying fixes at random. If you want a place to reproduce each of these probes against a live but disposable environment, the hands-on labs are built for exactly this kind of stepwise investigation; you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.net/tools/azure-labs.html) and walk a token failure end to end without risking a production identity.

## The distinct root causes and the InsightCrunch managed-identity token table

Across the incidents engineers actually report, a managed identity token failure reduces to five recurring causes. The first is that no identity is present on the resource, or the metadata endpoint that would issue the token is unreachable. The second is that the wrong identity type is in play, almost always a user-assigned identity that was not selected by client id when more than one is attached. The third is that the identity exists and is selected correctly but holds no role on the target resource, which produces a 403 rather than a 401. The fourth is that the token was minted for the wrong audience, so the target rejects a structurally valid token as not intended for itself. The fifth is the local-development case, where the code runs on a laptop or a build agent on which no managed identity exists at all, so the managed-identity step of the chain is guaranteed to fail and the real question is which other credential should take over.

The findable artifact for this article is the InsightCrunch managed-identity token table. It pairs each cause with the confirming check and the tested fix, and it is meant to be the thing you bookmark and return to mid-incident. Everything in the prose sections that follow expands one row of it.

| Cause | What you see | Confirming check | The fix |
| --- | --- | --- | --- |
| Identity absent or IMDS unreachable | 401 downstream; raw probe times out or returns identity-not-found | `az vm identity show` or probe the metadata endpoint with `Metadata: true` | Enable or attach an identity to the resource; clear the proxy that intercepts the link-local address |
| Wrong identity type or client id not specified | Token belongs to an unexpected `oid`; 403 with a principal you did not grant | Decode the token and compare `oid`/`appid`; list attached identities | Pass the user-assigned client id explicitly to the credential or the IMDS query |
| Missing role on the target | 403 from the target; valid token attached | `az role assignment list --assignee <principalId> --scope <resourceId>` | Grant the specific data-plane or control-plane role at the right scope; wait for propagation |
| Wrong audience | 401 from the target; token decodes with a mismatched `aud` | Decode the token and read the `aud` claim | Request the token for the target's resource id, not a guessed string |
| Local development, no identity exists | Managed-identity step fails on a laptop or build agent | Run with chain logging; observe the managed-identity decline | Sign in with the developer credential the chain expects, or build an explicit chain |

The rest of the article walks each row in turn, with the reproducible command for the confirming check and the fix.

## Cause one: the identity is absent or IMDS is unreachable

The most basic failure is that the workload asks for a token and there is no identity for the platform to mint one against, or the request never reaches the endpoint that would mint it. These are two different problems that present almost identically as a 401 downstream, and the confirming probe tells them apart.

The first variant is simply that no identity is assigned to the resource. A system-assigned identity has to be explicitly enabled on the resource, and a user-assigned identity has to be explicitly attached. It is entirely possible to write correct code, deploy it to a VM that has no identity at all, and watch every token request fail. Confirm the assignment with the resource's identity view:

```bash
# Check whether a VM has any identity
az vm identity show --name my-vm --resource-group my-rg -o json

# Check an App Service
az webapp identity show --name my-app --resource-group my-rg -o json
```

An empty or null result means no identity is present, and the fix is to enable or attach one. Enabling a system-assigned identity on a VM is a single command, and the platform creates the principal and provisions the credential onto the instance automatically:

```bash
# Enable a system-assigned identity on a VM
az vm identity assign --name my-vm --resource-group my-rg

# Attach a user-assigned identity to an App Service
az webapp identity assign --name my-app --resource-group my-rg \
  --identities /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.ManagedIdentity/userAssignedIdentities/<name>
```

Enabling the identity is necessary but not sufficient, because the newly created principal still holds no permissions anywhere. That is the bridge to cause three, and the correct setup sequence for the identity from the start is worth following deliberately rather than discovering by trial; the full procedure lives in the companion piece on how to [set up managed identities the right way](/2023/04/17/configure-managed-identities/), which covers the order of operations so you do not enable an identity and forget to authorize it.

### Why does the metadata endpoint time out even when an identity is assigned?

A timeout against 169.254.169.254 almost always means something on the host is intercepting traffic to the link-local address before it reaches the metadata service. The usual culprit is an HTTP proxy configured through environment variables that captures all outbound requests, including the one to the non-routable address that should never be proxied.

The link-local range is supposed to be reached directly, never through a proxy, because the metadata service lives on the host itself and a proxy has no path to it. When a containerized application or a locked-down VM has `HTTP_PROXY` and `HTTPS_PROXY` set globally, the SDK or the curl call dutifully sends the IMDS request to the proxy, which cannot resolve a link-local address and either refuses or hangs until it times out. The fix is to exclude the metadata address from proxying by adding it to the no-proxy list:

```bash
# Ensure the link-local metadata address bypasses any proxy
export NO_PROXY="169.254.169.254,$NO_PROXY"
export no_proxy="169.254.169.254,$no_proxy"
```

In PowerShell on Windows, the equivalent diagnostic uses the `-NoProxy` switch to prove the address is reachable when the proxy is taken out of the path:

```powershell
Invoke-RestMethod -Headers @{ Metadata = "true" } -Method GET -NoProxy `
  -Uri "http://169.254.169.254/metadata/instance?api-version=2021-02-01" | ConvertTo-Json -Depth 5
```

If the `-NoProxy` request succeeds and the normal request fails, the proxy is your problem and excluding the address resolves it permanently. A second, rarer variant is a host firewall or a network virtual appliance forcing all traffic through an inspection device that drops the link-local range; in that case the exclusion has to happen at the network layer rather than in an environment variable. The defining characteristic of this whole cause is that the failure is in reaching the endpoint, not in anything about the identity or its permissions, which is why the raw probe is the confirming check rather than any role command.

There is a hosting-specific wrinkle worth naming. On App Service and Functions, the absence of `IDENTITY_ENDPOINT` in the environment is itself a confirming signal that the identity is not enabled, because the platform only injects those variables once an identity is turned on. If you exec into the container and `echo $IDENTITY_ENDPOINT` returns nothing, you have not enabled the identity, regardless of what the deployment template claimed to do. That single check resolves a large fraction of App Service token failures before any role investigation begins.

## Cause two: the wrong identity type, or the client id was not specified

The second cause is subtler because the token request succeeds. A token comes back, the metadata endpoint is plainly reachable, and yet the target still rejects the call or the call runs as the wrong principal entirely. This is the signature of an identity-type or identity-selection problem, and it is overwhelmingly a user-assigned identity issue.

A resource can carry exactly one system-assigned identity, but it can carry many user-assigned identities at once. When more than one user-assigned identity is attached, the metadata service has no way to guess which one you mean, and the behavior of an unspecified request is not something to rely on. The rule to internalize is that whenever multiple user-assigned identities are attached, you must specify which one to use by its client id, both in raw IMDS calls and in the SDK credential. The choice between a system-assigned and a user-assigned identity in the first place, and the trade-offs each carries, is a design decision covered in the comparison of [managed identities versus service principals](/2024/01/08/managed-identity-vs-service-principal/); for the purposes of this failure, what matters is that once you have chosen user-assigned and attached more than one, selection becomes mandatory.

The confirming check is to decode the token that came back and read its `oid` claim, then compare it against the object id of the identity you expected. If they differ, the request ran as a different identity than you intended, and that identity may well lack the roles you carefully granted to the one you had in mind. List the attached identities and their ids to make the comparison concrete:

```bash
# List user-assigned identities attached to a VM and their principal/client ids
az vm identity show --name my-vm --resource-group my-rg \
  --query "userAssignedIdentities" -o json

# Resolve a single user-assigned identity's clientId and principalId
az identity show --name my-uami --resource-group my-rg \
  --query "{clientId:clientId, principalId:principalId}" -o json
```

The fix is to pass the client id explicitly. In a raw IMDS call you add a `client_id` query parameter; in the SDK you construct the credential with the client id rather than relying on the default:

```bash
# Raw IMDS call selecting a specific user-assigned identity
curl -s -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://vault.azure.net&client_id=<clientId>"
```

```python
# Python SDK: bind ManagedIdentityCredential to a specific user-assigned identity
from azure.identity import ManagedIdentityCredential
credential = ManagedIdentityCredential(client_id="<clientId>")
```

```csharp
// .NET SDK: select the user-assigned identity by client id
var credential = new DefaultAzureCredential(new DefaultAzureCredentialOptions
{
    ManagedIdentityClientId = "<clientId>"
});
```

### Is the application expecting a system-assigned identity while a user-assigned one is configured?

This mismatch is its own recurring case. Some teams write code that assumes a system-assigned identity and request a token with no client id, then deploy onto a resource configured with only user-assigned identities. The token step either fails or selects unpredictably, and the symptom looks like an intermittent authentication problem that nobody can reproduce on demand.

The deeper issue is a mental model gap: a system-assigned identity is unique to the resource and dies with it, so code can request it without naming it, while a user-assigned identity is a standalone resource that can be attached to many things and therefore must be named when ambiguity exists. When you migrate a workload from a system-assigned to a user-assigned identity to share one principal across several resources, the code that worked perfectly under the old model breaks under the new one unless you add the client id. The fix is to align the code with the configuration: either bind the credential to the user-assigned client id as shown above, or, if the workload genuinely wants its own dedicated principal, switch the resource back to a system-assigned identity and grant that new principal the roles it needs. The wrong fix, and a common one, is to attach more identities hoping one of them works, which only deepens the ambiguity that caused the failure.

## Cause three: the identity lacks the role on the target

This is the cause that most directly embodies the identity-plus-role rule, and it is the one engineers misdiagnose most often because the token acquisition succeeds completely. The metadata endpoint answers, a valid token comes back, the SDK reports no error during authentication, and then the target service returns a 403. Authentication worked. Authorization did not. The principal is who it says it is; it simply has not been granted permission to do what it is attempting.

The confirming check is to list the role assignments the principal actually holds at the scope it is reaching for. You need the principal id of the identity, which you obtained in cause two, and the resource id of the target:

```bash
# List the roles the identity holds at the target scope
az role assignment list \
  --assignee <principalId> \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<account> \
  -o table
```

An empty result is your answer: the identity has no role at that scope, so every authorized operation returns a 403 no matter how clean the token is. The fix is to grant the specific role the operation requires, at the narrowest scope that satisfies it. The word specific is doing real work here, because the role you need is frequently a data-plane role that people overlook. Reading a blob, for instance, requires the Storage Blob Data Reader role, not a control-plane role like Reader or even Contributor, which govern management of the account rather than access to the data inside it. Granting Contributor and watching the 403 persist is one of the most common dead ends in this entire failure family:

```bash
# Grant a data-plane role, not a control-plane one, at the resource scope
az role assignment create \
  --assignee <principalId> \
  --role "Storage Blob Data Reader" \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<account>
```

### Why does the 403 persist for a few minutes after I grant the role?

Role assignments propagate through the authorization system rather than taking effect the instant the command returns, so a freshly granted role can take several minutes to be reflected in the tokens and the authorization decisions the target makes. During that window the 403 continues even though the assignment plainly exists in the portal.

The practical consequence is that you should not conclude a role grant failed just because the next call still returns 403 seconds later. Confirm the assignment exists with the list command, then wait and retry rather than granting a second, broader role in frustration, which is how identities end up massively over-permissioned. Cached tokens compound the delay: a token minted before the grant carries the old authorization context until it expires, so even after propagation completes, a long-lived cached token may need to age out or be refreshed before the new permission appears in practice. If you must verify quickly, acquire a fresh token after the propagation window rather than reusing the one your application already holds. Key Vault is the single most common target for this exact failure, and because its access model has its own data-plane subtleties layered on top of the role question, the dedicated diagnosis of [Key Vault access denied and Forbidden errors](/2023/01/16/fix-key-vault-access-denied/) walks the vault-specific version of this propagation and data-plane-role problem in full.

The scope of the grant deserves a deliberate decision rather than a reflex. Granting at the resource scope authorizes the identity against exactly that one resource, which is the least-privilege choice and the one to prefer. Granting at the resource-group or subscription scope is broader and occasionally justified when an identity genuinely needs access across many resources, but it should be a conscious choice, never the path of least resistance taken to make a single 403 disappear. The identity-plus-role rule is not satisfied by any role; it is satisfied by the right role at the right scope, which is why the fix names both.

## Cause four: the token is minted for the wrong audience

The fourth cause is the one that looks most like a platform bug and is most often a single wrong string. The token acquisition succeeds, the identity is assigned and selected correctly, the role is present, and the target still returns a 401. Decoding the token reveals the culprit: the `aud` claim names a different service than the one being called. A token is minted for a specific audience, and a service validates that the token presented to it was actually intended for it. Present a token whose audience is the Resource Manager to a Key Vault endpoint and the vault rejects it, correctly, as a token meant for somebody else.

This happens because the `resource` parameter on the token request determines the audience, and that parameter is easy to get wrong. Each service has its own resource identifier: the Resource Manager is `https://management.azure.com/`, Key Vault is `https://vault.azure.net`, Azure Storage is `https://storage.azure.com/`, and Microsoft Graph is `https://graph.microsoft.com/`. Request a token with the wrong identifier and you receive a perfectly valid token for the wrong service. The confirming check is to decode the captured token and read its `aud` claim against the service you are actually calling:

```bash
# Decode and inspect the audience claim
echo "$TOKEN" | cut -d '.' -f2 | base64 -d 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin)['aud'])"
```

If the printed audience does not match the target, request the token for the correct resource. In a raw IMDS call you correct the `resource` query parameter; in the SDK you almost never set the audience by hand, because the typed clients set the correct scope for their own service automatically, which is a strong argument for using the client libraries rather than hand-rolling token requests:

```bash
# Correct the audience by requesting the token for the right resource
curl -s -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://vault.azure.net&client_id=<clientId>"
```

The reason this cause is worth its own section, despite reducing to a single corrected string, is that it is invisible without decoding the token. Every other signal looks healthy. The identity is there, the role is there, the endpoint answers, and the only evidence of the problem is buried in the `aud` claim that nobody reads until they know to. Once you have inspected the audience a single time, the fix is trivial and the failure rarely recurs, because you have learned to use the typed client whose audience is correct by construction. The trailing-slash and exact-string sensitivity of these resource identifiers is real, so copy the canonical identifier from the service's own documentation rather than typing it from memory, and prefer the SDK client that handles it for you.

## Cause five: it works in Azure but not locally

The fifth cause is the one that generates the most confused bug reports, because the application is correct and the failure is environmental. The code runs flawlessly when deployed to Azure and fails the instant a developer runs it on a laptop or a continuous-integration agent. The error names the managed identity credential, which makes engineers hunt for a misconfigured identity that was never the problem. The truth is simpler: there is no managed identity on a laptop. A managed identity exists only on Azure resources, so on any machine that is not an Azure resource, the managed-identity step of the credential chain is guaranteed to fail. There is nothing to fix about the identity, because there is no identity to fix.

The behavior makes sense once you understand what `DefaultAzureCredential` is. It is a preconfigured chain of credentials that the SDK tries in order, stopping at the first one that returns a token. The chain is deliberately built so that the same code authenticates correctly both in Azure, where the managed-identity step succeeds, and on a developer machine, where that step fails and the chain falls through to a developer credential such as the signed-in Azure CLI, the Azure Developer CLI, an IDE plugin, or environment-variable credentials. The exact ordering and the exact set of credentials in the chain differ across language SDKs and have changed across versions, so treat the precise order as a thing to verify against the current documentation for your SDK rather than a constant to memorize. What is durable across all of them is the shape: cloud credentials first, developer credentials after, and a managed-identity step that always declines off-Azure.

### Why does ManagedIdentityCredential always fail on my development machine?

Because the managed-identity step in the chain has nothing to talk to off-Azure. There is no metadata endpoint and no platform-provisioned credential on a laptop, so the step reaches for an identity that does not exist and declines, by design, so the chain can move on to a developer credential. The decline is expected behavior, not a defect.

The fix for local development is to make sure the chain can reach a working developer credential, which usually means signing in with the Azure CLI so the CLI credential step succeeds:

```bash
# Sign in locally so the developer credential in the chain can mint tokens
az login
az account set --subscription "<your-subscription>"
```

With a valid CLI sign-in present, `DefaultAzureCredential` falls through the failed managed-identity step and authenticates using the CLI session, and the same binary that fails with a managed-identity error one moment works the next without any code change. If the verbose chain logging from the diagnosis section is enabled, you will watch this happen in the logs: the managed-identity step declines, the next steps decline, and the CLI step succeeds.

There are two refinements worth knowing. The first is performance: trying and failing through several credentials adds startup latency, and on a laptop the failing managed-identity probe in particular can cost noticeable seconds. For local development you can short-circuit this by constructing an explicit chain that tries the CLI credential first, or by excluding the managed-identity step entirely when an environment flag indicates local development. The second is predictability: because the chain inspects environment variables, a stray variable on a shared build agent can silently change which credential wins, producing the kind of works-on-my-machine inconsistency that is maddening to track down. The mature pattern, once an application is past early development, is to stop relying on the all-purpose chain in production and instead use `ManagedIdentityCredential` explicitly in Azure and an explicit developer credential locally, branching on the environment. That makes the authentication path predictable and the failure messages precise, at the cost of a few lines of branching code. The configuration article on setting up identities goes deeper into wiring this branch cleanly, and the practice exam scenarios that drill credential-chain reasoning are a good way to cement it; you can [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) that present a failing chain and ask you to name the declining step.

## Confirming the fix and the verification commands

A fix you cannot verify is a guess that happened to coincide with the problem resolving. Every cause above has a verification step that proves the fix took effect, and running it closes the loop with evidence rather than hope. The verification mirrors the confirming check but is run after the change, and a green result is the signal that the incident is genuinely over rather than temporarily quiet.

For the absent-identity and unreachable-endpoint cause, the verification is a successful raw token request returning JSON with an `access_token`, run from inside the resource after enabling the identity and clearing any proxy interception. For the wrong-identity cause, the verification is decoding the new token and confirming the `oid` claim now matches the principal id you intended. For the missing-role cause, the verification is the role-assignment list returning the role you granted at the expected scope, followed by a fresh token-bearing call to the target that returns 200 rather than 403 once propagation completes. For the wrong-audience cause, the verification is decoding the token and confirming the `aud` claim now names the correct service. For the local-development cause, the verification is the application running locally to completion with the chain logging showing a developer credential succeeding.

A single end-to-end verification that exercises the whole path is worth more than any individual probe. The cleanest one is to use the identity to read something it should be able to read and confirm a 200:

```bash
# End-to-end: use the identity to read a secret it now has rights to
# (run from inside the Azure resource that holds the identity)
TOKEN=$(curl -s -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://vault.azure.net&client_id=<clientId>" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -s -H "Authorization: Bearer $TOKEN" \
  "https://my-vault.vault.azure.net/secrets/db-password?api-version=7.4"
```

If that returns the secret, every link in the chain is sound: the endpoint answered, the right identity was selected, the audience was correct, and the role was present and propagated. If it returns 401 you are back at audience or token acquisition; if it returns 403 you are back at the role. The same logic generalizes to any target by swapping the resource identifier and the call. Reproducing this verified end-to-end path against a sandbox before you touch production is exactly the kind of rehearsal the labs are designed for, and running it once builds the muscle memory that makes the next incident a two-minute fix.

## Prevention: keeping the credential-free path working

The whole point of a managed identity is to remove a stored secret from the system, and the prevention strategy is therefore organized around never reintroducing one. The single most important preventive habit is to treat reverting to a client secret as the wrong answer it almost always is. When a token fails, the identity needs the right assignment or the right role, not a password; pasting a secret back in to make authentication work tonight recreates the exact liability the managed identity was adopted to eliminate, and it tends to become permanent because nothing forces its removal once the immediate pressure passes.

Beyond that discipline, prevention is largely a matter of making the identity configuration explicit and repeatable rather than clicked together in the portal and forgotten. Define the identity, its attachment to the resource, and its role assignments as infrastructure as code so the assignment and the authorization are version-controlled and reviewed together. A Bicep fragment that creates a user-assigned identity, attaches it, and grants a scoped data-plane role keeps the identity-plus-role rule satisfied by construction:

```bicep
resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'app-identity'
  location: location
}

resource roleAssign 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, uami.id, 'blobreader')
  scope: storageAccount
  properties: {
    // Storage Blob Data Reader role definition id
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1')
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}
```

Encoding the role assignment alongside the identity in the same template means an identity is never created without its authorization, which eliminates the most common production version of the missing-role cause: an identity enabled in one change and authorized in a change that never happened. It also makes the scope visible in review, which keeps the least-privilege decision honest rather than defaulting to a broad grant.

Two monitoring habits catch the rest before they become incidents. The first is to alert on authorization failures at your targets. A sudden cluster of 403s from Storage or Key Vault attributed to a managed identity principal is the earliest visible sign that a role was removed, a scope changed, or a propagation problem is underway, and a Log Analytics query over the relevant resource logs surfaces it:

```kql
// Surface recent authorization failures on a Key Vault attributed to identities
AzureDiagnostics
| where ResourceType == "VAULTS"
| where ResultSignature == "Forbidden" or httpStatusCode_d == 403
| project TimeGenerated, identity_claim_oid_g, OperationName, requestUri_s
| order by TimeGenerated desc
```

The second is to review identity role assignments on a schedule, because the failure mode that hurts most in security terms is not the 403 that blocks a workload but the over-broad grant that nobody noticed. An identity that was given Contributor at subscription scope to clear a 403 two years ago is now a standing risk, and a periodic review that lists every role each managed identity holds and questions anything broader than a scoped data-plane role keeps the estate aligned with least privilege. The same identity model underlies the sibling failure on service principals, and the prevention discipline carries over directly to the diagnosis of [service principal authentication errors](/2023/01/30/fix-service-principal-auth-error/), which face the analog of these causes with a credential that, unlike a managed identity, you do have to rotate.

## Related failures it is often confused with

A managed identity token error sits in a family of identity failures that look alike at the symptom level, and confusing one for another sends the diagnosis down the wrong path. Three neighbors account for most of the confusion.

The closest neighbor is the Key Vault access-denied case. When a managed identity calls Key Vault and the vault returns Forbidden, the instinct is to suspect the token, but the cause is usually a missing data-plane role or, on vaults still using the older access-policy model, a missing access policy entry. The token is fine; the vault's own authorization layer is the gate. The tell is that the token decodes cleanly with the correct `aud` for the vault, which rules out the audience and acquisition causes and points squarely at the vault's access model. That investigation has its own dedicated treatment because the vault layers an access-policy-versus-RBAC choice on top of the ordinary role question.

The second neighbor is the service principal authentication error. A service principal and a managed identity are both principals that obtain tokens, but a service principal authenticates with a secret or certificate that you manage, so its failures include expired secrets, wrong tenant ids, and clock skew that simply cannot occur for a managed identity, which holds no secret at all. When a token failure involves a secret, a certificate thumbprint, or a credential expiry, you are looking at a service principal problem wearing similar clothing, and the fix lives in that diagnosis rather than this one.

The third neighbor is the broad authorization failure that the Resource Manager raises during management-plane operations, the one that returns an `AuthorizationFailed` message naming a missing action at a scope. That failure is about control-plane RBAC on management operations, while much of what this article covers is data-plane access to the contents of a resource. The distinction between managing a storage account and reading the blobs inside it is precisely the control-plane-versus-data-plane line, and conflating the two is why granting Contributor so often fails to clear a data-plane 403. Recognizing which plane you are operating on tells you which kind of role to grant and which diagnosis to follow.

The unifying lesson across all three neighbors is to read the evidence before choosing the fix. Decode the token, check its audience and subject, confirm the assignment and the role at the scope, and only then act. The identity-plus-role rule holds across the whole family: the principal must be present, and it must be authorized for exactly what it is attempting, on exactly the resource it is attempting it against.

## How a managed identity obtains a token, step by step

Diagnosing a token failure is far easier once you can picture the exact sequence the platform runs on the happy path, because each failure is a specific step in that sequence breaking. The flow has more moving parts than the single curl call suggests, and the parts map directly onto the causes.

When your workload constructs a credential and asks it for a token aimed at a target service, the credential first determines where it is running. On a virtual machine it reaches for the link-local metadata address; on App Service or Functions it reads the injected endpoint and header environment variables; inside a cluster configured for workload identity federation it follows a different path entirely, exchanging a projected token for an Entra token. Whichever endpoint applies, the credential then issues a request that names two things: the audience, through the resource identifier, and, when ambiguity exists, the specific user-assigned principal, through the client id. The platform validates that an identity is present, mints a short-lived bearer token for that principal scoped to the requested audience, and returns it with an expiry timestamp.

Notice what is absent from that description. There is no password sent, no certificate presented, and no refresh token returned, because the model does not need any of them. A traditional confidential client proves itself with a secret and receives both an access token and a refresh token so it can obtain new access tokens without re-presenting the secret. A managed identity skips all of that: the platform already vouches for the principal because the principal is provisioned onto the host the platform controls, so when an access token expires the credential simply asks the metadata endpoint again and receives a fresh one. The `refresh_token` field in the raw response is empty for exactly this reason, and engineers who expect to find one and build logic around it are designing for a flow that does not exist here.

The token itself is a JSON Web Token whose claims encode everything a target needs to make an authorization decision. The `aud` claim fixes which service the token is valid for, the `oid` claim identifies the principal as an object in the directory, the `iss` claim names the issuing authority and therefore the tenant, and the `exp` claim sets the expiry. A target service that receives the token validates the signature against the issuer's published keys, checks that the audience matches itself, confirms the token has not expired, and then consults its own authorization layer to decide whether the principal identified by `oid` is allowed to perform the requested operation. Every one of the five causes maps onto a step in that validation: an unreachable endpoint or absent principal means no token to present, a wrong client id means the wrong `oid`, a wrong resource means the wrong `aud`, and a missing role means the authorization layer says no even though signature, audience, and expiry all check out.

### How long does a managed identity token last and what refreshes it?

A managed identity access token is short-lived, typically valid for under an hour, with the exact lifetime carried in the `expires_on` field of the response. There is no refresh token; when the access token expires, the credential requests a new one from the metadata endpoint directly, since the platform already vouches for the principal.

The practical importance of this is in how the SDK caches tokens. The Azure Identity libraries cache a token in memory and reuse it until shortly before its expiry, then transparently fetch a replacement. That cache is why a single long-running process does not hammer the metadata endpoint on every call, and it is also why some failures appear only after a delay rather than immediately. A role change made after a token was cached will not affect calls using that cached token until it ages out and a fresh one carries the new authorization context. Understanding the cache turns an otherwise baffling intermittent failure, where the same code works for fifty minutes and then starts returning 403, into an obvious consequence of a token minted before a permission change expiring and being replaced by one minted after it.

## Recurring real-world scenarios and the check for each

The five causes are abstractions; engineers experience them as concrete situations. Walking the most common situations and naming the single check that resolves each builds the pattern-matching that makes the next incident fast, and each scenario below is a real shape that turns up repeatedly in incident reports.

The first is a Function App reading from a Storage account. The function deploys, the identity is enabled, and every blob read returns 403. The check is the role list at the storage scope, and the resolution is almost always granting Storage Blob Data Reader or Storage Blob Data Contributor, the data-plane roles, rather than the control-plane Contributor the team granted out of habit. The function authenticated perfectly; it simply had no data-plane authorization, which is the missing-role cause wearing its most common costume. The same shape recurs with a Function reading from a queue, where the needed role is the storage queue data role rather than the blob one, so the resolution is to grant the data-plane role for the specific sub-resource the workload actually touches.

The second is a virtual machine connecting to Azure SQL using an Entra token rather than a SQL login. The connection string is configured for token authentication, the VM has a system-assigned identity, and the connection fails with an authentication error. The check is whether the identity has been created as a user in the database, because being a principal in the directory is necessary but not sufficient: Azure SQL requires the identity to be provisioned as a database-level user and granted database roles before it can connect. The token acquisition succeeds and the database rejects the authenticated principal because it is unknown inside the database, which is a database-side authorization gap layered on top of the ordinary directory model.

The third is an application that runs as a user-assigned identity shared across several resources and suddenly behaves as if it has no permissions on one of them. The check is decoding the token to read its `oid` and confirming it matches the shared identity, because the most common cause is that the affected resource had a second user-assigned identity attached, introducing the selection ambiguity that lets the request run as the wrong principal. The resolution is to pin the client id explicitly so the intended shared identity is always chosen, which is the wrong-identity-type cause in its sharing-related form.

### Why does my AKS pod fail to get a token even though the node has an identity?

Because a pod runs in its own network and security context, not the node's, so the identity assigned to the node or the cluster is not automatically the identity the pod authenticates as. Modern clusters use workload identity federation, where a Kubernetes service account is federated to an Entra identity and the pod exchanges a projected service-account token for an Azure token.

When that federation is misconfigured, the pod's attempt to authenticate fails in a way that looks like a missing managed identity, because from the pod's perspective there is none of the node's identity available to it. The check is whether the service account the pod uses carries the annotation linking it to the intended client id, and whether a federated credential exists on the target identity that trusts that service account's issuer and subject. Reaching for the raw node metadata address from inside a pod is the wrong instinct; the correct path is the workload identity integration, which projects a token the pod exchanges for an Entra token scoped to the federated principal. The resolution is to fix the federation mapping rather than to grant the pod broader network access to the metadata endpoint, which would be both ineffective and a step backward for security.

The fourth scenario is the cross-tenant attempt. An application running with an identity in one tenant tries to reach a resource governed by a different tenant, and the token is rejected because its issuer, encoded in the `iss` claim, names the home tenant rather than the resource's tenant. A managed identity is scoped to the tenant of the subscription that hosts it and cannot natively present itself as a principal of a foreign tenant, so the check is to decode the token and read `iss`, and the resolution is an architectural one: use a mechanism designed for cross-tenant access rather than expecting a single managed identity to span tenants. This scenario is worth naming because it produces a rejection that looks like an audience or role problem until you read the issuer and realize the boundary being crossed is the tenant itself.

## A diagnostic decision tree you can run in two minutes

The table earlier in the article is the reference; this is the order to consult it under pressure. Run the steps in sequence and stop at the first that explains the symptom, because the steps are ordered from the cheapest and most common cause to the rarest, and stopping early saves the cost of the later checks.

Begin with the downstream status code, because it forks the entire investigation. A 403 with a valid token means you skip straight to the role check; there is no point probing the endpoint or decoding the audience when authentication plainly succeeded. A 401, an SDK exception during authentication, or no token at all means you stay in the acquisition half of the tree. This first fork alone eliminates half the possible causes in a single observation.

If you are in the acquisition half, probe the endpoint next. Run the raw request appropriate to the host, the metadata address on a VM or the injected endpoint on App Service, with the mandatory header. A timeout or refusal means an unreachable endpoint, usually a proxy intercepting the link-local address, and you fix the no-proxy configuration. An identity-not-found response means no principal is assigned, and you enable or attach one. A token coming back means the endpoint and the assignment are both fine, so the acquisition problem is narrower than it first appeared and you move to the next step.

With a token in hand that is still being rejected, decode it and read two claims. Read `aud` first: if it names a service other than the one you are calling, that is the wrong-audience cause and you correct the resource identifier, ideally by switching to the typed SDK client. Read `oid` next: if it is not the principal you intended, that is the wrong-identity cause and you pin the client id. If `aud` and `oid` are both correct and the target still rejects the call, the rejection is not really an acquisition problem at all and you have fallen through to the authorization half despite the misleading code, so you run the role check after all.

The local-development case sits outside this tree because it announces itself: the failure happens on a laptop or a build agent, never in Azure, and the chain log shows the managed-identity step declining followed by a developer credential either succeeding or failing. If the symptom is environmental rather than deployed, you skip the tree entirely and go straight to confirming the developer credential is signed in. Internalizing this ordering is the difference between a diagnosis that takes two minutes and one that takes an afternoon, and rehearsing it against deliberately broken sandboxes is how the sequence becomes reflexive rather than something you reconstruct from scratch each time.

## Token lifetime, caching, and the 401-after-an-hour trap

A specific timing pattern deserves its own treatment because it confuses even experienced engineers: a workload authenticates correctly, runs for the better part of an hour, and then begins returning 401 from a target it had been reaching successfully. The instinct is to suspect a transient platform problem, but the cause is usually a token-handling defect in the application rather than anything in the identity.

The pattern arises when code acquires a token once at startup and holds it as a long-lived value, perhaps stashing it in a static field or a module-level variable, rather than letting the credential manage the token's lifecycle. Because the token expires in under an hour, the stashed value goes stale, and every call after expiry presents a token the target correctly rejects as expired. The application never asked for a fresh one because it treated the token as a configuration constant rather than the short-lived artifact it is. The fix is to stop caching the raw token yourself and instead hold the credential object, calling it for a token at the point of use; the SDK caches the token internally and refreshes it transparently before expiry, which is the entire reason to use the credential abstraction rather than raw requests.

A subtler version of the same trap involves the authorization context baked into a token at mint time. When you grant a new role to an identity, tokens already minted and cached do not retroactively gain the new permission; they carry the authorization context from when they were issued until they expire. An application holding a token minted before a grant will keep being denied until that token ages out and the credential fetches a replacement that reflects the new role. This is why the propagation delay on a role grant can appear longer than it actually is: the grant may have propagated within minutes, but a token cached for the rest of its hour-long life masks the change until it expires. Acquiring a fresh token after the propagation window, rather than reusing the application's cached one, separates a genuine propagation delay from a caching artifact and prevents the over-granting that impatience produces.

The defensive posture against the whole family of timing problems is to let the credential own the token and to retry transient acquisition failures with a short backoff rather than failing hard on the first miss. The metadata endpoint can occasionally be briefly unavailable during host maintenance, and a single failed acquisition is not the same as a misconfiguration; a credential that retries a transient miss rides through the blip, while one that throws on the first failure turns a momentary hiccup into an outage. Reproducing an expired-token scenario deliberately, by forcing a long pause between acquisition and use, is a useful drill because it surfaces exactly this class of defect before it reaches production at three in the morning.

## Control plane versus data plane, the distinction that resolves most 403s

If a single conceptual gap is responsible for more wasted hours on managed identity failures than any other, it is the control-plane-versus-data-plane line, so it earns a dedicated treatment. The Azure authorization system governs two different kinds of operation with two different sets of roles, and a role that authorizes one says nothing about the other.

Control-plane operations manage a resource: creating a storage account, changing its configuration, listing its keys, deleting it. These are operations against the Resource Manager, and roles like Owner, Contributor, and Reader govern them. Data-plane operations act on the contents a resource holds: reading a blob, writing a message to a queue, retrieving a secret from a vault, querying rows in a database. These are operations against the resource's own data endpoint, and an entirely separate family of roles, with names like Storage Blob Data Reader, Key Vault Secrets User, and the various data-specific roles, governs them. The two planes are deliberately separated so that an operator who can manage a storage account does not automatically gain the ability to read every customer record inside it, which is a sound security boundary and the source of endless confusion.

The confusion plays out predictably. An engineer grants Contributor to a managed identity, reasons that Contributor is a broad and powerful role, and is baffled when blob reads still return 403. Contributor is indeed broad on the control plane, but it conveys no data-plane access to blob contents, so the data read is denied exactly as designed. The fix is never to escalate further up the control-plane ladder toward Owner, which also conveys no data access; it is to grant the matching data-plane role at the resource scope. Recognizing which plane an operation lives on is therefore the first thing to settle once you know you are facing a 403, because it tells you which catalog of roles to grant from. A useful rule of thumb is that if the operation reads or writes the stuff inside the resource, it is data-plane and needs a data-plane role, regardless of how powerful a control-plane role the principal already holds.

This distinction also explains why some targets need two grants. A workload that both manages a resource and reads its data legitimately needs one control-plane role and one data-plane role, and granting only one leaves half the operations failing. Naming the planes explicitly in design review, rather than reaching for a single broad role, keeps the grants minimal and the failures rare, and it makes the eventual security review far easier because each role on the identity has an obvious operational justification rather than being a broad grant that nobody can quite account for.

## Reproducing a managed identity token failure on purpose

The fastest way to learn the signal each cause produces is to create each failure deliberately in a disposable environment, because a failure you have manufactured and watched is one you recognize instantly when it appears unannounced in production. Each cause has a clean way to reproduce it.

To reproduce the unreachable-endpoint cause, set a bogus proxy in the environment and watch the metadata request time out, then clear it and watch the request succeed; the contrast teaches the exact shape of a proxy-intercepted failure. To reproduce the absent-identity cause, deploy a workload to a resource with no identity enabled and observe the acquisition failure, then enable the identity and watch acquisition begin to work while data calls still fail for lack of a role, which usefully separates the assignment problem from the authorization problem in two distinct steps. To reproduce the wrong-identity cause, attach two user-assigned identities, omit the client id, and decode the resulting token to see which principal answered; then pin the client id and confirm the `oid` changes to the one you intended.

To reproduce the missing-role cause, grant nothing and confirm the clean 403 with a valid token, then grant a control-plane role and confirm the 403 persists, then grant the data-plane role and watch it clear; running those three steps in order burns the control-plane-versus-data-plane lesson into memory more effectively than any explanation. To reproduce the wrong-audience cause, request a token with the resource identifier of the wrong service, present it to the right one, and decode the rejected token to read the mismatched `aud`. To reproduce the local-development case, run the same code on a laptop with and without a signed-in developer credential and read the chain log narrating the difference.

Manufacturing these failures in a sandbox rather than discovering them in production is the single best preparation for the on-call moment, and a structured environment that lets you toggle each cause and observe its signal turns a theoretical understanding into a reflex. Running these reproductions as a guided exercise, where each scenario is staged and the expected signal is described before you trigger it, is precisely what the hands-on labs and the scenario drills are built to provide, so a team that rehearses there arrives at real incidents already fluent in the signals.

## Making the identity configuration auditable and repeatable

Prevention scales only when the identity, its attachment, and its roles live in version control rather than in someone's memory of which buttons they clicked. The Bicep fragment earlier showed the Azure-native form; the same discipline expresses cleanly in Terraform for teams standardized on it, and seeing both makes the underlying principle, that the assignment and the authorization ship together, concrete regardless of tooling.

```hcl
resource "azurerm_user_assigned_identity" "app" {
  name                = "app-identity"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
}

resource "azurerm_role_assignment" "blob_reader" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}
```

The value of expressing it this way is not the syntax but the guarantee: the role assignment references the identity's principal id directly, so the plan cannot create the identity without also creating its authorization, and a reviewer reading the diff sees the scope and the role in the same change. The most damaging production version of the missing-role cause is an identity enabled in one deployment and authorized in a follow-up deployment that slips and never happens, leaving an identity that can acquire tokens but do nothing with them; binding the two in one declarative unit eliminates that gap entirely.

Auditing closes the loop that prevention opens. A scheduled query over the activity and resource logs surfaces both the workload-blocking failures and the quieter security risk of an over-broad grant. A second Log Analytics query, complementing the Key Vault one shown earlier, watches for the role assignments themselves so a sudden grant of a broad role to an identity becomes visible rather than silent:

```kql
// Surface broad role grants to managed identities for review
AzureActivity
| where OperationNameValue == "Microsoft.Authorization/roleAssignments/write"
| where ActivityStatusValue == "Success"
| project TimeGenerated, Caller, Properties
| order by TimeGenerated desc
```

The cadence that keeps an estate healthy is a periodic review, monthly for a fast-moving environment, that lists every role each managed identity holds and questions anything broader than a scoped data-plane role with a clear operational reason. The review is where the standing risk of a forgotten subscription-scope Contributor grant gets caught and narrowed, long after the incident that prompted it has been forgotten. Treating identity authorization as something to review on a schedule, rather than something to set once and never revisit, is what keeps the least-privilege intent of the identity-plus-role rule true over the life of a system rather than only on the day it was first deployed.

## A note on the Entra ID rename and what it means for these errors

Azure Active Directory was renamed to Microsoft Entra ID, and the rename matters for this diagnosis in a practical way even though it changes nothing about how a managed identity behaves. The directory that holds the principal, issues the tokens, and validates them is now Entra ID, and current documentation, portal labels, and newer error strings use that name. Older error messages, blog posts, and forum threads you will find while searching still say Azure Active Directory or Azure AD, and they describe the same system; the token a managed identity receives is still an Entra-issued JSON Web Token whose `iss` claim names the issuing authority for your tenant.

The reason to keep this straight is that a search for a managed identity error will surface results spanning both names, and treating them as two different systems leads to chasing phantom differences that do not exist. When a result describes acquiring a token from Azure AD and your error mentions Entra ID, they are the same flow. The principal, the audience model, the role assignments, and the control-plane-versus-data-plane distinction are all unchanged by the rename. Read older material for its technical content, mentally substitute the current name, and apply the same identity-plus-role reasoning, because the mechanism the name refers to has not moved even as the label on it has.

## Host-specific quirks that change where the token comes from

The mental model of a single metadata endpoint is a useful simplification, but the endpoint differs by host, and a fix that works on one host fails on another precisely because the plumbing underneath is not identical. Knowing the per-host differences turns a confusing cross-environment failure into an expected one.

On a virtual machine or a scale set, the link-local address is the real endpoint and the raw probe against it is meaningful, so the proxy-exclusion fix and the connectivity diagnosis apply directly. On App Service and Functions, the platform does not expose that address to your application; it injects the endpoint and header environment variables, and the correct probe reads those variables rather than hardcoding the address. A team that copies a working VM diagnostic into an App Service troubleshooting guide spreads a probe that cannot succeed there, which is why the first App Service check is always whether the injected variables are present at all. Their absence is the fastest possible confirmation that the identity is not enabled, short-circuiting a longer investigation.

Container Apps sit closer to the App Service model than the VM one for token acquisition, and the same reliance on the platform-provided endpoint applies, so the instinct to reach for the link-local address from inside a container is again the wrong one. Inside Kubernetes, as covered in the scenarios, workload identity federation replaces the metadata call with a token exchange, so the diagnosis shifts from endpoint reachability to federation mapping. Logic Apps and Data Factory acquire tokens through their own managed identity integration rather than exposing an endpoint your code calls at all; there the failure surfaces in a connector or a linked service configuration, and the check is whether the identity selected in that configuration holds the role on the target, which is the missing-role cause expressed through a designer surface rather than code.

### Why does the same code authenticate on a VM but fail on App Service?

Because the two hosts expose the token endpoint differently. A VM answers token requests at the link-local metadata address, while App Service and Functions do not expose that address at all and instead inject endpoint and header environment variables for the SDK to use. Code that hardcodes the VM address works on the VM and fails on App Service because the address it targets simply is not reachable there.

The lesson the per-host differences teach is to let the SDK credential pick the endpoint rather than choosing it yourself. The whole reason the Azure Identity libraries detect the host and select the right endpoint automatically is that the endpoints genuinely differ, and code that delegates that decision to the library moves between hosts without change while code that hardcodes one host's endpoint breaks the moment it is deployed somewhere else. When a token failure appears only after moving a workload from one host type to another, and the code reaches the metadata service directly rather than through the credential, the endpoint mismatch is the first thing to suspect, and the durable fix is to stop hardcoding the endpoint and let the credential resolve it. This is the same principle that makes the typed clients the right answer for the audience problem: the library encodes the host-specific and service-specific knowledge that is tedious and error-prone to maintain by hand, and leaning on it removes an entire category of avoidable failure.

## The verdict

A managed identity token failure feels like a deep platform problem the first time you hit it and becomes a routine five-minute check once you hold the model. The token comes from an endpoint on the host, not from a secret, and a request for it fails for a small set of reasons that the identity-plus-role rule organizes completely: the identity is absent or the endpoint is unreachable, the wrong identity is selected, the right identity lacks the role on the target, the token is aimed at the wrong audience, or the code is running somewhere no managed identity exists. Each cause has a confirming command, the downstream code tells you whether to look at acquisition or authorization, and decoding the token turns vague rejections into precise facts. The discipline that matters most is refusing the false fix: when a token fails, the answer is to repair the identity's assignment or its role, never to surrender the credential-free design by stuffing a secret back into the configuration. An engineer who internalizes that one rule, and who reaches for the verbose chain log and the decoded token before reaching for a role grant, will diagnose these failures faster than the documentation can describe them and will keep the secretless path that managed identities exist to provide intact.

## Frequently Asked Questions

### Q: Why does my managed identity fail to get a token?

A managed identity fails to get a token for one of a small set of reasons, and the downstream status code points to which. A 401 from the target usually means no valid token was acquired at all, which traces to the metadata endpoint being unreachable, no identity assigned to the resource, the wrong identity selected, or a token minted for the wrong audience. A 403 means a valid token was acquired but the principal lacks the role on the target. Start by enabling verbose chain logging in the Azure Identity SDK to see exactly which step failed, then probe the raw metadata endpoint to confirm reachability, and finally decode the returned token to inspect its audience and subject claims. Working the chain from endpoint to assignment to role isolates the cause in a few minutes rather than leaving you guessing.

### Q: What is the IMDS endpoint and why would it be unreachable?

The Instance Metadata Service is a host-local REST endpoint that issues managed identity tokens, reachable on a virtual machine at the link-local address 169.254.169.254 with a mandatory `Metadata: true` header. It is non-routable and only answers from inside the instance, which is part of its security model. The most common reason it appears unreachable is a proxy: when `HTTP_PROXY` or `HTTPS_PROXY` is set globally, the request to the link-local address gets sent to the proxy, which cannot reach a host-local address and times out. Adding the address to the no-proxy list fixes it. A second reason, specific to App Service and Functions, is that those platforms do not expose 169.254.169.254 at all; they inject `IDENTITY_ENDPOINT` and `IDENTITY_HEADER` environment variables instead, so hardcoding the VM address there fails because that door was never there.

### Q: How do I tell whether a system-assigned or user-assigned identity is being used?

Decode the access token and read its `oid` claim, which is the object id of the principal the token represents, then compare it against the principal ids of the identities attached to the resource. List those with the resource's identity command, such as `az vm identity show`, which reports both the system-assigned principal id and any user-assigned identities by their resource ids. Resolve a user-assigned identity's principal and client ids with `az identity show`. If the token's `oid` matches the system-assigned principal you have one answer; if it matches a user-assigned identity you have another; and if it matches none of what you expected, the request selected an identity you did not intend, which is itself the bug. This comparison is the single most reliable way to settle which identity is actually in play rather than which one you assumed.

### Q: Does my identity lack the role on the target resource?

If the token acquisition succeeds and the target returns 403, the answer is almost certainly yes. Confirm it directly by listing the role assignments the principal holds at the target scope with `az role assignment list --assignee <principalId> --scope <resourceId>`. An empty result means no role at that scope, which produces a 403 on every authorized operation regardless of how valid the token is. The fix is to grant the specific role the operation needs, and the trap is granting a control-plane role like Contributor when the operation needs a data-plane role like Storage Blob Data Reader. Control-plane roles govern managing the resource; data-plane roles govern accessing its contents, and the two are separate. Grant at the narrowest scope that works, and remember that a fresh grant takes a few minutes to propagate before the 403 clears.

### Q: Why does it work in Azure but fail when I run it locally?

Because a managed identity exists only on Azure resources, so on a laptop or a build agent there is no identity for the managed-identity step of the credential chain to use, and that step fails by design. `DefaultAzureCredential` is built to handle exactly this: it tries managed identity first in Azure, and when that step declines off-Azure it falls through to a developer credential such as the signed-in Azure CLI. The error names the managed identity because that is the step that failed, but the identity was never the problem. Sign in locally with `az login` so the CLI credential step in the chain can mint a token, and the same code that failed will work. Enabling chain logging makes the fall-through visible, showing the managed-identity step declining and the CLI step succeeding.

### Q: Why is my token rejected for the wrong audience?

A token is minted for a specific audience determined by the `resource` parameter on the request, and a service validates that any token presented to it was actually intended for it. If you request a token with the wrong resource identifier, you receive a structurally valid token for the wrong service, and the target rejects it with a 401 even though everything else is correct. Decode the token and read its `aud` claim; if it names a different service than the one you are calling, that is the cause. Each service has its own identifier, such as `https://vault.azure.net` for Key Vault and `https://management.azure.com/` for the Resource Manager. The durable fix is to use the typed SDK client for the target service, because those clients set the correct audience automatically and you never type the identifier by hand.

### Q: What does ManagedIdentityCredential authentication failed mean exactly?

It is the Azure Identity SDK reporting that the managed-identity step of authentication could not obtain a token, and it is frequently wrapped inside a broader message listing every credential the chain attempted. The phrase alone does not tell you the cause; it tells you which step failed. The cause underneath is one of the usual set: no identity assigned, the metadata endpoint unreachable, a user-assigned identity not specified by client id, or, on a developer machine, no managed identity existing at all. Enable debug-level logging for the identity logger so the SDK narrates the reason it declined, because the verbose output names the specific failure rather than the generic wrapper. Treat the wrapper message as a pointer to enable logging, not as the diagnosis itself.

### Q: How do I select a specific user-assigned identity by client id?

When more than one user-assigned identity is attached to a resource, you must name which one to use by its client id, because the platform cannot infer your intent. In a raw IMDS request, add a `client_id` query parameter alongside `resource` and `api-version`. In the SDK, construct the credential with the client id rather than relying on the default: in Python, `ManagedIdentityCredential(client_id="...")`; in .NET, set `ManagedIdentityClientId` on `DefaultAzureCredentialOptions`. Find the client id with `az identity show --query clientId`. Selecting by client id is mandatory whenever multiple user-assigned identities exist, and skipping it produces unpredictable behavior where the request may run as an identity that lacks the roles you granted to the one you intended, which surfaces as an inexplicable 403 from the target.

### Q: How do I decode a managed identity token to read its claims?

A bearer token is a JSON Web Token with three dot-separated segments, and the middle segment is a Base64Url-encoded JSON payload you can read without any secret, because you are inspecting it rather than verifying its signature. Split on the dot, take the second field, Base64-decode it, and pretty-print the JSON. The two claims that matter most for token diagnosis are `aud`, the audience the token was minted for, and `oid` or `appid`, identifying the principal. Reading `aud` settles whether you have an audience mismatch; reading `oid` settles whether the right identity was selected. Never trust this decode for security decisions, since it does not verify the signature, but for diagnosis it is invaluable because it converts a vague rejection into a concrete, checkable fact about what the token actually contains.

### Q: Why does the 403 persist for several minutes after I grant a role?

Role assignments do not take effect the instant the grant command returns; they propagate through the authorization system, which can take several minutes to reflect in the authorization decisions a target makes. During that window the 403 continues even though the assignment exists. Cached tokens extend the delay further, because a token minted before the grant carries its old authorization context until it expires, so even after propagation an application reusing a stale token will still be denied. The correct response is to confirm the assignment with the role-list command, then wait and retry, ideally acquiring a fresh token after the propagation window. The wrong response, and a common one, is to grant a second broader role out of impatience, which leaves the identity over-permissioned long after the original grant has quietly started working.

### Q: How do I confirm a managed identity is even enabled on an App Service?

Exec into the App Service container and check whether the `IDENTITY_ENDPOINT` environment variable is present, because the platform only injects it once an identity is enabled. If `echo $IDENTITY_ENDPOINT` returns nothing, the identity is not enabled regardless of what a deployment template appeared to do, and that single fact resolves a large share of App Service token failures before any role investigation. You can also check from the control plane with `az webapp identity show`, which returns the system-assigned principal id and any attached user-assigned identities, or null if none are configured. App Service and Functions use the injected `IDENTITY_ENDPOINT` and `IDENTITY_HEADER` rather than the VM metadata address, so confirming those variables exist is the hosting-correct way to verify the identity is wired up.

### Q: What is the difference between a 401 and a 403 in a managed identity failure?

The two codes point at opposite halves of the problem and demand different fixes. A 401 Unauthorized means the request reached the target without a valid bearer token, which traces upstream to token acquisition: the endpoint was unreachable, no identity was assigned, the wrong identity was selected, or the token was minted for the wrong audience and rejected as not intended for this service. A 403 Forbidden means a valid token did arrive and the target recognizes the principal, but that principal has no permission for the operation, which is a missing role assignment on the target. The fix for a 401 lives in acquisition and audience; the fix for a 403 lives in roles and scope. Identifying the code first prevents the common waste of granting roles to solve what was actually an acquisition problem.

### Q: Should I revert to a client secret to get authentication working again?

No, and treating that as the fix is the most common mistake in this entire failure family. A managed identity fails because it is unassigned, the wrong type, missing a role, or aimed at the wrong audience, and every one of those has a direct fix that keeps the credential-free design intact. Pasting a client secret back in recreates exactly the liability the managed identity was adopted to remove: a credential someone now has to store, rotate, guard, and eventually risks leaking. Worse, the secret tends to become permanent, because once authentication works under deadline pressure nothing forces its removal. Diagnose the real cause instead. The fix is almost always a single role grant at the right scope or a client id passed to the credential, both of which take less time than wiring a secret back in safely.

### Q: How does DefaultAzureCredential decide which credential to use?

`DefaultAzureCredential` is a preconfigured chain that attempts a sequence of credentials in order and stops at the first one that returns a token. The chain is designed so the same code works in Azure, where the managed-identity step succeeds, and on a developer machine, where that step declines and the chain falls through to developer credentials such as the Azure CLI, the Azure Developer CLI, an IDE plugin, or environment variables. The exact ordering and the precise set of credentials differ across language SDKs and have changed across versions, so verify the current order against the SDK documentation rather than memorizing it. Because the chain inspects environment variables, a stray variable on a shared host can change which credential wins, which is why mature production code replaces the chain with an explicit credential once the application's authentication requirements are settled.

### Q: Can a token work from a VM but fail from inside a container on the same host?

Yes, and the usual reason is networking rather than identity. A container may not inherit a route to the link-local metadata address, or its proxy environment variables may intercept the request to 169.254.169.254 even though the host itself can reach it. On orchestrated platforms the recommended path is the platform's own identity mechanism rather than reaching for the raw VM metadata address from inside a pod, because the pod's network namespace is not the host's. Confirm by running the raw probe with the `Metadata: true` header from inside the container and comparing the result with the same probe on the host. If the host succeeds and the container times out, exclude the link-local address from the container's proxy configuration or adopt the platform-native identity integration, which routes token acquisition correctly for workloads running inside the cluster.

### Q: How do I verify end to end that a managed identity fix actually worked?

Run a single call that exercises the whole path: from inside the Azure resource, request a token for the target service with the correct `resource` and `client_id`, then use that token in an authenticated call to the target and confirm a 200. If the call returns the data, every link is sound, since the endpoint answered, the right identity was selected, the audience was correct, and the role was present and propagated. If it returns 401 you are back at acquisition or audience; if it returns 403 you are back at the role. This end-to-end check is more trustworthy than any single probe because it proves the steps work together rather than in isolation. Reproducing it against a disposable sandbox before touching production turns the verification into a rehearsal you can run in minutes.

### Q: Why does adding more user-assigned identities make the problem worse?

Because the original failure was usually ambiguity, and adding identities deepens it. When multiple user-assigned identities are attached and the code does not specify a client id, the selection is not something to rely on, so the request may run as an identity that lacks the roles you granted to the one you intended. Attaching yet another identity in the hope that one of them works adds more candidates to an already ambiguous selection and makes the behavior harder to reason about, not easier. The correct move is the opposite: reduce ambiguity by naming exactly one identity through its client id in the credential or the IMDS request, and grant that single identity the role it needs. Fewer identities, each explicitly selected and precisely authorized, is the configuration that stays diagnosable as the system grows.

### Q: How can I monitor for managed identity authorization failures before they become incidents?

Alert on authorization failures at the targets the identity calls. A cluster of 403s from Storage or Key Vault attributed to a managed identity principal is the earliest visible sign that a role was removed, a scope changed, or propagation is lagging, and a Log Analytics query over the relevant resource logs surfaces it by filtering on the forbidden result and projecting the identity claim, the operation, and the request uri. Pair that with a scheduled review of every role each managed identity holds, which catches the quieter risk: the over-broad grant added long ago to clear a single 403 and never narrowed. Encoding the identity and its scoped role assignment together in infrastructure as code prevents the most common production failure, an identity created in one change and authorized in a change that never happened, so the assignment and the authorization always ship together.
