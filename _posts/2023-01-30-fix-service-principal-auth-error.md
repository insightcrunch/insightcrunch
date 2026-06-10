---
layout: post
title: "Fix Service Principal Authentication Errors"
page_title: "Fix Service Principal Authentication Errors in Azure: Diagnose AADSTS7000215 Invalid Client Secret, AADSTS7000222 Expired Credentials, Wrong Tenant or Client ID, and Missing Role Failures"
date: 2023-01-30
categories: ["Technology"]
tags: ["Azure", "Service Principal", "AADSTS7000215", "Troubleshooting", "Identity", "Security"]
excerpt: "Service principal authentication errors in Azure split into credential and role failures. Read the error class to fix the secret, certificate, tenant, or role."
image: "/assets/images/blog/blog-06.webp"
reading_time: 59
author: "thomas-reid"
last_updated: 2023-01-30
lang: en
---
A pipeline that deployed cleanly on Friday returns `invalid_client` on Monday, and the message buried in the response reads AADSTS7000215 or AADSTS7000222. A nightly job that has run for a year suddenly cannot reach a storage account. A new automation account works in development and gets rejected in production with a tenant it does not recognize. Every one of these is a service principal authentication error, and almost every one of them is one of a small set of distinct causes wearing slightly different clothes. The reason these incidents feel mysterious is that two completely different kinds of failure print into the same logs and get treated as the same problem. One kind means the identity could not prove who it is. The other means it proved who it is and then was told it is not allowed to do the thing it asked for. Knowing which of those two you are looking at, before you touch anything, is the difference between a thirty second fix and an afternoon of regenerating credentials that were never the problem.

![Diagnosing Azure service principal authentication errors and AADSTS codes - Insight Crunch](/assets/images/blog/blog-06.webp)

This piece treats the service principal authentication error as a diagnosis rather than a symptom. A service principal is the identity an application, a script, or a pipeline uses to sign in to Microsoft Entra ID and act against Azure resources without a human at the keyboard. It carries an application (client) ID, it lives in a specific tenant, and it proves itself with one of two credential types: a client secret or a certificate. When any one of those pieces is wrong, expired, or missing, the sign-in fails before a token is ever issued. When all of them are right but the principal has not been granted a role on the resource it is trying to reach, the sign-in succeeds and the call still fails. Those are two separate failure classes, and the whole method here rests on telling them apart from the first error line.

## What a Service Principal Authentication Error Actually Means

The phrase "service principal authentication error" gets stretched to cover everything from an expired secret to a missing role to a network block, which is exactly why it is hard to fix. Precision starts with the OAuth 2.0 client credentials flow, because that flow is what a service principal actually performs. The application sends a token request to the Entra ID token endpoint for its tenant, presenting its client ID and a credential, and asks for a token scoped to a resource. Entra ID validates the credential against the application registration, confirms the application exists in that tenant, and if everything checks out, issues an access token. The application then presents that token to the target resource, and the resource decides whether the identity behind the token is permitted to perform the operation.

Two distinct gates sit in that sequence. The first gate is authentication: can this caller prove it is the application it claims to be, in the tenant it claims to belong to, using a valid credential. A failure here happens at the token endpoint and comes back as an AADSTS error code, and no token is issued. The second gate is authorization: now that a valid token exists, is the identity behind it allowed to read this blob, deploy to this resource group, or read this Key Vault secret. A failure here happens at the target resource, comes back as an HTTP 403 with an `AuthorizationFailed` body from Azure Resource Manager or a comparable data-plane denial, and crucially, it means a token was already issued successfully.

The single most useful rule in this entire diagnosis is what we will call the authn-versus-authz rule for service principals: an invalid-client style error is an authentication failure that names a credential or identity problem, while an authorization failure is a missing role, so the error text itself tells you whether to fix the credential or fix the role. The practical payoff is that you never regenerate a secret to solve a 403, and you never grant a role to solve an AADSTS7000222. Reading the error class first stops the most common wasted hour in this whole category of incident.

### Is a service principal failure authentication or authorization?

It is authentication if no token was issued and the message carries an AADSTS code from the sign-in service, meaning the credential, the client ID, the tenant, or the application registration is wrong. It is authorization if a token was issued and the target returned a 403 with `AuthorizationFailed`, meaning the identity is valid but lacks the role.

That distinction sounds academic until you watch it save time in practice. An engineer sees a deployment fail, sees the word "authorization" somewhere in the logs, and immediately resets the client secret because that is the ritual they remember. The reset succeeds, the secret is now valid, and the deployment fails again with the identical 403, because the secret was never the issue. The principal authenticated perfectly both times. What it lacked was the Contributor role on the target resource group. The same trap runs in reverse: an engineer sees an authentication error, opens the role assignments blade, and starts handing out roles to an identity that cannot even get a token, which changes nothing because authorization is never reached. The error class is the fork in the road, and it is printed in the first line you already have.

## Inside the Client Credentials Flow That a Service Principal Uses

Understanding the failures is easier once the flow that produces them is concrete. A service principal authenticates with the OAuth 2.0 client credentials grant, which is the flow designed for a non-interactive identity acting as itself rather than on behalf of a person. The application posts to the token endpoint for its tenant with a grant type of `client_credentials`, presenting its client ID and proving possession of a credential, and asks for a token good for a resource. There is no user, no consent prompt at request time, and no refresh token; the application simply requests a fresh access token whenever the current one nears the end of its life.

Two details in that request account for a surprising share of the confusion. The first is the difference between the older and newer token endpoints. The older endpoint takes a resource parameter that names the target by its identifier URI, while the newer endpoint takes a scope parameter that appends `/.default` to the resource identifier to mean all of the application permissions configured for that resource. Mixing the two, sending a resource value to the endpoint that expects a scope, or dropping the `/.default` suffix on the newer endpoint, produces a request the service cannot satisfy even when every credential is correct. The second detail is how the credential is presented. A client secret travels as a `client_secret` form field, while a certificate is never transmitted at all; instead the application builds a signed JWT client assertion and sends it as a `client_assertion` field with a type that declares it a JWT bearer assertion. The private key signs that assertion on the application's side, which is precisely why the private key must be present in the PEM and why a thumbprint mismatch breaks signing before anything reaches the service.

Holding this model makes the error codes legible rather than arbitrary. AADSTS7000215 and AADSTS7000222 are the service reporting that the `client_secret` field was wrong or out of date. A certificate assertion failure is the service reporting that the signed JWT did not validate against any public key on the registration. AADSTS700016 is the service reporting that it looked up the client ID inside the tenant named by the authority and found nothing. AADSTS500011 is the service reporting that the scope named a resource it cannot resolve. Each code maps to one field in the request, and knowing which field a code names is what lets you go straight to its cause instead of cycling through every credential you hold.

## How to Read the Error and Gather the Diagnostic Signal

Before changing a single setting, reproduce the failure in isolation so you are debugging the credential exchange and not the surrounding pipeline. The cleanest reproduction is a direct sign-in with the Azure CLI using the same three values the failing job uses, which strips away every layer of YAML, environment variables, and task wrappers that can hide where the real fault sits.

```bash
# Reproduce the exact sign-in the failing job performs.
az login --service-principal \
  --username "$APP_ID" \
  --password "$CLIENT_SECRET" \
  --tenant "$TENANT_ID"
```

If that command fails with an AADSTS code, the problem lives in the credential exchange and you are looking at an authentication failure. If it succeeds and only the later resource call fails, the credential exchange is healthy and you are looking at an authorization failure. That one command splits the entire problem space in half. For a certificate-based principal, the same login takes the path to a PEM file that contains both the certificate and its private key, and the same logic applies to the result.

```bash
# Certificate-based sign-in: the PEM must hold the private key plus the cert.
az login --service-principal \
  --username "$APP_ID" \
  --password "$PATH_TO_CERT_PEM" \
  --tenant "$TENANT_ID"
```

When you want to see the raw exchange rather than the CLI's interpretation of it, request the token directly. A direct request shows you the literal error code and description, which is the most precise signal available, and it removes any doubt about whether a token came back at all.

```bash
# Request a token directly to see the raw AADSTS response.
curl -s -X POST \
  "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token" \
  -d "client_id=$APP_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "scope=https://management.azure.com/.default" \
  -d "grant_type=client_credentials"
```

A success returns a JSON body with an `access_token` field. A failure returns a JSON body with `error` set to something like `invalid_client` or `unauthorized_client` and an `error_description` that begins with the AADSTS code. That code is the most valuable string in the whole investigation. AADSTS7000215 points at the secret value being wrong or mistyped. AADSTS7000222 points at the secret being expired. AADSTS700016 points at the application not being found in the tenant, which is either a wrong client ID or a wrong tenant. AADSTS90002 points at the tenant itself not being found. AADSTS500011 points at the requested resource or scope not existing in the tenant. Reading the code first narrows eight possible causes down to one or two before you have changed anything.

### Which signal tells you the failure is authentication?

A token endpoint response with no `access_token` and an `error_description` beginning with an AADSTS code is authentication. The sign-in service rejected the caller, so the credential, client ID, tenant, or registration is at fault. If a token came back and the resource later returned 403, the signal is authorization, not authentication.

When a token does come back, decode it to confirm that the identity inside it matches what you expect, because a surprising number of "wrong" failures are actually the right credential pointed at the wrong application or the wrong tenant. A JSON Web Token carries claims you can read without any special tooling, and the three that matter most here are `appid` (the application that authenticated), `tid` (the tenant that issued the token), and `aud` (the resource the token is good for). A quick decode of the payload segment reveals all three.

```bash
# Capture the token, then decode its payload to inspect appid, tid, and aud.
TOKEN=$(curl -s -X POST \
  "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token" \
  -d "client_id=$APP_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "scope=https://management.azure.com/.default" \
  -d "grant_type=client_credentials" | jq -r .access_token)

# Pad and base64url-decode the middle segment of the JWT.
echo "$TOKEN" | cut -d. -f2 | tr '_-' '/+' \
  | awk '{ p=length($0)%4; if(p>0) for(i=p;i<4;i++) $0=$0"="; print }' \
  | base64 -d 2>/dev/null | jq '{appid, tid, aud}'
```

If `appid` is not the application you meant to use, you have copied a client ID from another registration. If `tid` is a tenant you did not expect, your authority points at the wrong directory. If `aud` is not the resource your downstream call targets, you requested a token for the wrong audience and the resource will reject it even though the token is otherwise valid. Reading the token rather than guessing turns three separate root causes into a single confirming step.

### Which token claims help diagnose a service principal problem?

The three headline claims catch most mismatches, and a few more sharpen the rest. The `oid` is the object ID of the service principal, which role assignments are made against, so comparing it to a role's assignee confirms the authenticated identity is the one holding the role. The `iss` encodes the issuing tenant and endpoint version, and `exp` is the token's expiry, useful when a cache holds a token past its life.

The claim that resolves a subtle authorization confusion is `roles`. When an application is granted application permissions to a resource, those permissions appear in the token as a `roles` claim, and their absence when you expected them tells you the permission was never granted or never admin-consented, which is a different problem from a missing Azure role on a resource. A token can be valid, name the right application, tenant, and audience, and still be rejected by a downstream API because its `roles` claim lacks the application permission the API requires. Decoding the full payload rather than only the three headline claims surfaces this distinction.

```bash
# Decode the full token payload to inspect every diagnostic claim.
echo "$TOKEN" | cut -d. -f2 | tr '_-' '/+' \
  | awk '{ p=length($0)%4; if(p>0) for(i=p;i<4;i++) $0=$0"="; print }' \
  | base64 -d 2>/dev/null | jq '{appid, oid, tid, aud, iss, exp, roles}'
```

The habit worth building is to read the token whenever a call is rejected after a token issued, because the claims convert a vague permissions failure into a specific one: a missing `roles` entry points at an ungranted application permission, an unexpected `aud` points at a wrong scope, and an `oid` that does not match the role assignee points at a role granted to the wrong object. Each of those is a different fix, and the token names which one without a guess.

The hands-on Azure command library and the searchable error reference that pairs each symptom with its causes are collected in [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), which is the place to rerun each of these reproductions against a sandbox principal until the signal is unmistakable.

## How to Read the Entra ID Sign-In Logs for a Service Principal

The token endpoint response is the fastest signal, but it is not the only one, and when the failing caller sits inside a pipeline or an SDK you cannot easily instrument, the Entra ID sign-in logs hand you the same information after the fact. Service principal sign-ins are recorded under their own category, separate from user sign-ins, and each entry carries the application ID, the resource the token was requested for, the result, the failure reason, and a correlation ID that ties the event to a specific attempt. Reading the failure reason there often names the AADSTS code directly, which is invaluable when the application swallowed the error or logged only a generic message that hides the real cause.

When the sign-in logs are exported to a Log Analytics workspace, the same data becomes queryable, and a focused query against the service principal sign-in table surfaces every recent failure for one application along with its code and count. This turns an intermittent failure that is hard to catch live into a list you can read at leisure.

```kusto
AADServicePrincipalSignInLogs
| where TimeGenerated > ago(24h)
| where AppId == "REPLACE_WITH_APP_ID"
| where ResultType != 0
| summarize attempts = count() by ResultType, ResultDescription, ResourceDisplayName
| order by attempts desc
```

A `ResultType` of zero is a success, and any non-zero result is a failure whose `ResultType` is the numeric AADSTS code and whose `ResultDescription` is the human-readable reason. Grouping by the resource is diagnostic in itself: failures clustered on a single resource point at a scope or audience problem rather than a credential problem, because a bad credential fails for every resource the principal touches while a bad scope fails only for the one target it names. The correlation ID on an individual failed entry is also the value to hand to support if you escalate, because it identifies the exact request in the service's own telemetry. Capturing a deliberately broken principal in a workspace and watching these codes appear is one of the rehearsals worth running before an outage forces you to learn the query under pressure.

## A Triage Script That Splits the Authentication Gate From the Role Gate

Because the first decision is mechanical, it is worth scripting, so that a single command reports which gate failed and which cause is most likely before any human judgment is applied. The logic mirrors the manual method exactly: attempt the sign-in, branch on whether a token issued, and when one did not, read the AADSTS code out of the error to name the probable cause. The script below is a starting point you adapt to your environment, and it is deliberately read-only, changing nothing while it diagnoses.

```bash
#!/usr/bin/env bash
# Usage: ./sp-triage.sh <app-id> <tenant-id> <secret> [resource-scope]
APP_ID="$1"; TENANT_ID="$2"; SECRET="$3"
SCOPE="${4:-https://management.azure.com/.default}"

resp=$(curl -s -X POST \
  "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token" \
  -d "client_id=$APP_ID" -d "client_secret=$SECRET" \
  -d "scope=$SCOPE" -d "grant_type=client_credentials")

if echo "$resp" | jq -e .access_token >/dev/null 2>&1; then
  echo "GATE: authentication OK, a token issued."
  echo "If the resource call still returns 403 AuthorizationFailed, the gate is AUTHORIZATION (missing role)."
  echo "$resp" | jq -r .access_token | cut -d. -f2 | tr '_-' '/+' \
    | awk '{ p=length($0)%4; if(p>0) for(i=p;i<4;i++) $0=$0"="; print }' \
    | base64 -d 2>/dev/null | jq '{appid, tid, aud}'
else
  code=$(echo "$resp" | jq -r .error_description | grep -oE 'AADSTS[0-9]+' | head -1)
  echo "GATE: authentication FAILED with $code"
  case "$code" in
    AADSTS7000222) echo "CAUSE: secret expired, rotate the secret";;
    AADSTS7000215) echo "CAUSE: wrong secret value or encoding, send the value not the ID";;
    AADSTS700016)  echo "CAUSE: app not found, wrong client ID or wrong tenant";;
    AADSTS90002)   echo "CAUSE: tenant not found, fix the authority tenant";;
    AADSTS500011)  echo "CAUSE: resource not found, fix the scope or resource";;
    *)             echo "CAUSE: consult the sign-in error reference for $code";;
  esac
fi
```

Run against a healthy principal, it prints the authentication-OK branch and the decoded identity claims, which doubles as a confidence check that the principal is who you think it is. Run against a broken one, it names the gate and the likely cause from the code. The value of automating the split is consistency: the script never reaches for a credential reset to solve a 403, because it reads the gate first, every time, which is exactly the discipline the manual method exists to build. Wire this into a pipeline as a preflight step and a credential problem announces itself with its cause named rather than as a downstream task failing for reasons nobody can see.

## Is the Failure Transient or Persistent?

Before you spend time on a root cause, settle a prior question: does the failure repeat. A service principal authentication error that clears on its own after a minute or two is a different animal from one that fails identically on every attempt, and the two demand opposite responses. The transient case is almost always replication lag. When you create a new principal, rotate a secret, or assign a role, the change is written in one place and then propagated across the directory, and for a short window a token request can hit a replica that has not yet received the update. The symptom is an AADSTS700016 that reports the application as not found even though you just created it, or a 403 on a resource immediately after you granted the role. Wait, retry, and it succeeds.

The persistent case never clears. The same error code comes back on attempt one, attempt ten, and attempt one hundred, because the cause is structural: a real expiry, a genuinely wrong client ID, a role that was never assigned. No amount of retrying fixes a structural failure, and retry logic that masks it only delays the diagnosis while burning your token endpoint quota. The discipline, then, is to retry with intent. A bounded retry with backoff distinguishes the two cleanly: if the error resolves within a handful of attempts, it was propagation and you can move on; if it survives the full retry budget, it is persistent and you escalate to the failure table below.

```bash
#!/usr/bin/env bash
# Distinguish transient propagation lag from a persistent structural failure.
attempts=0
max=6
delay=5
while (( attempts < max )); do
  if az login --service-principal -u "$APP_ID" -p "$SECRET" --tenant "$TENANT" >/dev/null 2>&1; then
    echo "authenticated on attempt $((attempts+1)): treat earlier failures as propagation lag"
    exit 0
  fi
  attempts=$((attempts+1))
  echo "attempt $attempts failed, waiting ${delay}s"
  sleep "$delay"
  delay=$((delay*2))
done
echo "failed all $max attempts: this is persistent, consult the failure table"
exit 1
```

The reason this matters for triage is that a transient failure and a persistent one can present with the exact same error text. The code does not tell you which you have; only the behavior over time does. Engineers who skip this step routinely rotate a perfectly good secret to fix a 700016 that was nothing more than a freshly created principal that had not finished propagating, and then they are confused when the same error appears the next time they provision. Establish persistence first, and you never waste a credential reset on a problem that the next thirty seconds would have solved for free.

## The Distinct Root Causes of a Service Principal Authentication Failure

Across the incidents engineers actually report, the failures collapse into a short list of causes, and each one belongs cleanly to either the authentication gate or the authorization gate. The value of organizing them this way is that the gate tells you which tool to reach for, the error code tells you which cause within that gate is yours, and the confirming command proves it before you spend effort on a fix. The artifact below is the InsightCrunch service-principal failure table, and it is the spine of the rest of this article: each row names a cause, places it in its gate, gives the signal that confirms it, and points at the fix.

| Cause | Gate | Typical signal | Confirming check | The fix |
| --- | --- | --- | --- | --- |
| Client secret expired | Authentication | AADSTS7000222, secret keys are expired | `az ad app credential list --id $APP_ID` shows past `endDateTime` | Create a new secret, update the consumer |
| Wrong secret value (secret ID confusion) | Authentication | AADSTS7000215, invalid client secret | Compare what you pass against the secret value, not the secret ID | Pass the secret value; URL-encode special characters |
| Certificate problem | Authentication | invalid client, assertion or thumbprint errors | `az ad app credential list --id $APP_ID --cert` and check the PEM has the private key | Upload the right cert, rotate, fix the PEM |
| Wrong tenant in the authority | Authentication | AADSTS90002 tenant not found, or AADSTS700016 | Decode the token `tid`, compare to the intended directory | Point the authority at the correct tenant ID |
| Wrong or copied client ID | Authentication | AADSTS700016, application not found | Decode the token `appid`, compare to `az ad sp show` | Use the correct application ID for this tenant |
| Wrong audience or scope | Authentication | AADSTS500011, resource principal not found | Decode the token `aud`, compare to the target | Request the correct resource `/.default` scope |
| Application or principal disabled or deleted | Authentication | unauthorized client, application disabled | `az ad sp show --id $APP_ID` enabled flag | Re-enable or recreate, then reassign roles |
| Missing role on the target | Authorization | HTTP 403 `AuthorizationFailed` after a token issues | `az role assignment list --assignee $APP_ID --all` | Assign the least-privilege role at the right scope |

Every row that sits in the authentication gate is fixed by correcting a credential, an identifier, or the registration. The single row in the authorization gate is fixed by granting a role, and it is the row people reach for first and need least. Working down the table in the order the error code suggests, rather than in the order of habit, is the whole method.

### Why do two failures that look the same need different fixes?

Because they happen at different gates. An expired secret and a missing role can both surface in a pipeline as a red "failed to authorize" line, but one was rejected at the token endpoint with no token issued, and the other was rejected at the resource after a token was issued. The same words describe opposite problems, so the gate, not the wording, decides the fix.

## A Worked Diagnosis From Error to Fix

It helps to watch the method run start to finish on one real failure, because the discipline only proves its worth when you see how few steps it actually takes. Picture a deployment pipeline that has run nightly for fourteen months and this morning failed on its first task with a single line in the log: the Azure CLI reported a login failure and the run aborted. There is no stack trace, no resource name, nothing but a failed authentication step. An engineer working from instinct would start poking at the resource the pipeline deploys to, checking whether it still exists, whether the subscription is active, whether a recent platform change broke something. All of that is wasted motion, because the method tells you to read the gate first.

The first move is to reproduce the failure outside the pipeline so you can see the real error rather than the pipeline's sanitized summary. You pull the principal's client ID, tenant, and secret from the same variables the pipeline uses and request a token directly against the token endpoint with curl. The endpoint answers immediately, and the answer is decisive: an HTTP 401 carrying `invalid_client` and the code AADSTS7000222, with a description that the application's secret keys are expired. That single response collapses the entire investigation. The gate is authentication, because the token endpoint rejected the request and issued no token at all, which means the resource, the role assignments, and the subscription are all irrelevant to this incident. They were never reached.

With the gate named, the cause within it is already on screen: 7000222 is the expiry code, not the wrong-value code and not the wrong-tenant code. You confirm it rather than assume it, because confirmation is cheap and a wrong fix is not. A quick credential listing on the application object shows one password credential with an end date that fell yesterday, which matches the fourteen-month-old setup exactly. Now the fix is mechanical and safe. You create a new secret on the same application without touching the old one, capture the new value, update the pipeline's secret store, run a token request to prove the new credential authenticates, and only then remove the lapsed credential. Append, prove, retire, in that order, so there is never a window where the principal has no working credential.

Now run the same scenario with one detail changed, to see how the gate decision steers the whole path. Suppose the curl request had instead returned an HTTP 200 with a perfectly good token, and the failure had appeared one step later as an AuthorizationFailed with a 403 when the pipeline tried to write to a storage account. The error text in the pipeline summary might read almost identically to the expired-secret case, a generic line about a failed operation, but the reproduction tells a completely different story. A token was issued, so authentication passed, so the credential is fine and rotating it would change nothing. The gate is authorization, and the fix lives entirely in role assignments: you list the principal's roles at the storage account's scope, find that the Storage Blob Data Contributor role was never granted at that scope, assign it, allow for propagation, and retry. Two incidents, two error lines that looked the same to the person reading the pipeline log, and two fixes that share not a single step. The only thing that separated them was reading the gate before reaching for a tool, which is the whole method in one sentence.

It is worth counting what the method actually cost in each case, because the economy is the argument for it. The expired-secret diagnosis took one reproduction command to see the real error, one glance at the code to name the gate and the cause together, and one credential listing to confirm before acting. Three reads, no guesses, and the fix was the only safe one available. The authorization variant took the same single reproduction command, and the moment a token came back the entire authentication half of the problem space was eliminated without a second thought. Compare that against the instinct-driven path, where an engineer who never establishes the gate cycles through resource checks, subscription checks, and a speculative secret rotation, any one of which can take longer than the whole disciplined diagnosis and none of which addresses an authorization failure. The method is not slower because it is careful; it is faster because it never investigates the half of the system the error already ruled out. That is why the gate question comes first every time, even when the cause feels obvious, because the cases where it feels obvious and is wrong are exactly the ones that cost a wasted rotation and a repeat incident.

## Cause One: The Client Secret Expired

Client secrets carry an expiry date set when they are created, and when that date passes, the credential stops working with no warning to the application that relies on it. The signal is unambiguous: the token endpoint returns `invalid_client` with AADSTS7000222 and a description stating that the secret keys for the application are expired. This is the single most common service principal incident in production, because secrets are created once during setup, the expiry is months or years out, and nobody is watching the calendar when the deadline finally arrives. The job that ran flawlessly for a year stops on the exact day the secret lapses.

Confirming it takes one command that lists the credentials on the registration and their validity windows. Reading the end date against the current date tells you immediately whether expiry is the cause, and it also reveals whether a newer secret already exists that the consumer simply is not using.

```bash
# List the secret credentials and their expiry windows.
az ad app credential list --id "$APP_ID" \
  --query "[].{keyId:keyId, start:startDateTime, end:endDateTime}" -o table
```

If the only `endDateTime` is in the past, expiry is confirmed. The fix is to create a fresh secret and propagate it to wherever the consumer reads it, which may be a pipeline variable group, a Key Vault entry, an app setting, or a configuration file. Creating the new secret is one command, and appending rather than replacing lets you keep the old credential in place momentarily so a rollback is possible if the new value does not reach the consumer cleanly.

```bash
# Create a new secret without removing the existing one yet.
az ad app credential reset --id "$APP_ID" --append \
  --display-name "rotation-$(date +%Y%m)" \
  --query "{appId:appId, password:password, end:endDateTime}"
```

The output contains the new secret value exactly once, so capture it the moment it appears. Update the consumer, rerun the reproduction from the diagnostic section, confirm a token now issues, and only then remove the expired credential. A subtle trap reported repeatedly is updating the secret in one place while a stale copy lingers in another, so that production keeps reading the old expired value while development reads the new one and works fine. When a rotation appears to fail, search every location that could hold the secret before concluding the new value is wrong, because the new value is usually correct and the old one is usually still being read somewhere.

## Cause Two: The Wrong Secret Value and the Secret ID Trap

AADSTS7000215, invalid client secret provided, is the error that catches people who copied the wrong field. When you create a secret in the portal, the blade shows two values that sit next to each other: a secret ID, which is a GUID that identifies the credential, and a secret value, which is the actual opaque string the application must present. The value is shown only once at creation and is masked afterward, while the ID remains visible. Under time pressure, it is easy to copy the ID, paste it as the secret, and get AADSTS7000215 on every request, because the ID is not a credential and never authenticates anything. The error description itself spells this out, reminding you to send the secret value and not the secret ID.

There is a second flavor of this error that has nothing to do with the secret ID. If the secret value contains special characters and it travels through a URL-encoded form body or a shell command without proper encoding, characters such as plus signs, ampersands, or trailing equals signs get mangled in transit, and Entra ID receives a different string than the one you stored. The symptom is identical, AADSTS7000215, but the cause is encoding rather than the wrong field. Confirming which flavor you have is a matter of inspecting exactly what the application sends. If you can print the value just before it goes on the wire and it matches the stored secret character for character, the cause is encoding somewhere in the transport. If it does not match, you copied the wrong thing.

```bash
# Verify you are sending the value, not the ID, and that it is intact.
echo -n "$CLIENT_SECRET" | wc -c   # length should match the stored secret
echo -n "$CLIENT_SECRET" | head -c 4; echo "..."   # first chars, sanity only
```

The durable fix for the encoding flavor is to generate secrets that avoid problematic characters, or to ensure the transport encodes the body correctly rather than relying on a hand-built string. The fix for the wrong-field flavor is to regenerate the secret, capture the value at the instant it is shown, and store it where the consumer reads it. Because both flavors print the same code, the confirming inspection matters more here than almost anywhere else in the table; without it you can rotate a perfectly good secret three times and still send a broken string each time.

### How do I tell an expired secret from a wrong secret value?

The error code separates them. AADSTS7000222 means the secret is expired, so the value was once correct and time ran out. AADSTS7000215 means the secret value is invalid, so it is the wrong field, a typo, or a transport encoding problem. Expiry is fixed by rotating; an invalid value is fixed by sending the correct, intact string.

The two get confused because both arrive as `invalid_client` at the HTTP level, and an engineer who reads only "invalid client" treats them as one problem. Reading the AADSTS suffix is what splits them. It is worth building the habit of grepping the error description for the numeric code rather than the human-readable phrase, because the phrase generalizes and the code does not.

## Cause Three: The Certificate Is the Problem

Certificate-based service principals replace the shared secret with an asymmetric key pair, where Entra ID holds the public certificate and the application signs a client assertion with the private key. This is more secure because the private key never travels to Entra ID, but it introduces a different set of failures, all of which present as the sign-in being rejected. The certificate can be expired, just as a secret can. The certificate uploaded to the registration can be a different one than the application signs with, so the public key on file does not match the signature. The PEM file the application loads can contain only the certificate and not the private key, so the application cannot sign at all. The thumbprint the application advertises can fail to match any credential on the registration. Each of these stops authentication before a token issues.

Confirming a certificate cause starts with listing the key credentials on the registration and their validity, which is the certificate analog of listing secrets.

```bash
# List certificate (key) credentials and their validity windows.
az ad app credential list --id "$APP_ID" --cert \
  --query "[].{keyId:keyId, start:startDateTime, end:endDateTime, type:type}" -o table
```

If the certificate on file is expired, the fix is the same shape as a secret rotation: create or upload a new certificate, point the application at it, and remove the old one once the new path is proven. If the certificate on file is valid but authentication still fails, the next check is whether the application is actually signing with the matching private key. A PEM intended for service principal sign-in must contain the private key block alongside the certificate block, and a common mistake is exporting only the public certificate, which authenticates nothing.

```bash
# Confirm the PEM contains a private key, not just the certificate.
grep -E "BEGIN (RSA )?PRIVATE KEY" "$PATH_TO_CERT_PEM" && echo "private key present" \
  || echo "NO PRIVATE KEY in PEM"

# Read the certificate thumbprint to compare against the registration.
openssl x509 -in "$PATH_TO_CERT_PEM" -noout -fingerprint -sha1
```

If the PEM has no private key, that is the cause, and re-exporting the certificate with its key resolves it. If the thumbprint from the PEM does not appear among the registration's key credentials, the application is signing with a certificate Entra ID does not know about, and uploading the correct public certificate aligns them. For a quick clean credential during diagnosis, the CLI can generate and attach a self-signed certificate to the registration and hand back the local PEM, which proves the certificate path works end to end before you wire in your real certificate.

```bash
# Generate a self-signed cert, attach it, and write the PEM locally.
az ad app credential reset --id "$APP_ID" --create-cert \
  --query "{appId:appId, fileWithCertAndPrivateKey:fileWithCertAndPrivateKey}"
```

Certificates fail less often than secrets in steady state because a well-run certificate has a longer life and a rotation process, but when they fail the message is less self-explanatory than the secret codes, so the confirming checks on the private key and the thumbprint carry more of the diagnosis. Reproducing each certificate failure mode against a throwaway principal, watching the exact rejection each one produces, is the fastest way to recognize them in production, and the scenario-based drills in [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) are built around exactly this kind of credential-failure rehearsal.

## Cause Four: The Tenant in the Authority Is Wrong

A service principal exists in one tenant, and the token request must be sent to that tenant's authority. The authority is the part of the token endpoint URL that names the directory, and if it names the wrong directory, Entra ID either cannot find the tenant at all or cannot find the application within the tenant you pointed at. A tenant that does not exist or cannot be resolved returns AADSTS90002, tenant not found. A tenant that exists but does not contain the application you named returns AADSTS700016, application not found in that directory. Both are authority problems even though they print different codes, and both happen most often when a configuration was copied from another environment that lived in a different tenant.

The confusion intensifies in multi-tenant setups and in organizations that maintain separate directories for production and non-production. A pipeline promoted from a staging subscription in one tenant to a production subscription in another keeps the staging authority, and the production application, which is a different registration in a different directory, is suddenly unreachable. The decode you ran earlier is the cleanest confirmation, because the token's `tid` claim is the tenant that actually issued it, and comparing that against the tenant you intended exposes the mismatch directly. When no token issues at all, the AADSTS code tells you whether the tenant was unresolvable (90002) or merely the wrong home for the application (700016).

```bash
# Confirm which tenant your current context and your intended values point at.
az account show --query "{tenantId:tenantId, name:name}" -o table
echo "Intended tenant: $TENANT_ID"
```

The fix is to set the authority to the correct tenant ID for the application you are using, and to prefer the tenant's GUID over a domain name in automation, because the GUID is stable while domains can be added, renamed, or moved. Where a single pipeline genuinely spans tenants, the right structure is a distinct service principal per tenant with its own authority, not one principal stretched across directories it does not belong to. Pinning the tenant by GUID and keeping per-environment configuration separate removes this whole class of cross-environment surprise.

## Cause Five: The Client ID Is Wrong or Copied From Another Application

AADSTS700016 names an application that the directory cannot find, and when the tenant is correct, the remaining explanation is that the client ID itself is wrong. The most frequent way this happens is copying an application ID from a different registration, often because a teammate shared the wrong value, or because a configuration was duplicated from a neighboring service and the ID was never updated. The error reads as though the application does not exist, and from the directory's point of view that is exactly true, because the GUID you supplied does not match any registration there. It is easy to misread this as a credential problem and start resetting secrets, but no secret will help an application ID the tenant has never seen.

There is a related identifier trap that produces confusion without producing this exact code: the application has both an application (client) ID and an object ID, and they are different GUIDs serving different purposes. The client ID is what you present during sign-in. The object ID identifies the registration or the service principal object for management operations. Pasting an object ID where a client ID belongs sends a GUID the sign-in flow cannot match to an application. Confirming the right value is a lookup against the directory that returns the canonical application ID for the registration you mean to use.

```bash
# Resolve the registration by display name and read its true client ID.
az ad app list --display-name "$APP_DISPLAY_NAME" \
  --query "[].{displayName:displayName, appId:appId, objectId:id}" -o table

# Confirm the service principal exists for that app and is enabled.
az ad sp show --id "$APP_ID" \
  --query "{appId:appId, displayName:displayName, enabled:accountEnabled}" -o table
```

If the lookup returns an `appId` different from the one you were using, you had the wrong value, and substituting the correct one resolves the failure. If `az ad sp show` cannot find a service principal for the application ID, the registration may exist without a corresponding service principal in this tenant, which is its own cause covered below. The decode of the token's `appid` claim, when a token does issue, is again the fastest confirmation that the identity acting is the one you intended.

### Can a wrong client ID and a wrong tenant produce the same error?

Yes, both can return AADSTS700016, because the directory reports that it cannot find the application either way. The disambiguator is the tenant: confirm the authority points at the right directory first, and if it does, the client ID is the remaining suspect. Decoding the token's `tid` and `appid` claims, when a token issues, separates them cleanly.

## Cause Six: The Principal Authenticated but Lacks a Role

This is the authorization gate, and it is the cause that masquerades as an authentication failure more than any other. The sequence is straightforward: the credential is valid, the client ID and tenant are correct, a token issues without complaint, and then the call to the target resource returns HTTP 403 with an `AuthorizationFailed` body explaining that the client does not have authorization to perform the requested action over the requested scope. The token proves identity. What is missing is a role binding the identity to permission on the resource. Resetting the secret here is the canonical wasted fix, because the secret was never involved in the rejection.

Confirming it has two parts. First, prove that a token issues, which you already did during reproduction; if `az login --service-principal` succeeds, authentication is healthy. Second, inspect the role assignments the principal actually holds and compare them against the scope and action the failing call needs.

```bash
# List every role the principal holds, across scopes.
az role assignment list --assignee "$APP_ID" --all \
  --query "[].{role:roleDefinitionName, scope:scope}" -o table
```

If the list is empty, or holds roles only at scopes unrelated to the target, the missing role is confirmed. The fix is to grant the least-privilege role that covers the action, at the narrowest scope that covers the resource, rather than reaching for Owner or Contributor at the subscription as a reflex. A job that writes blobs needs a data role on the storage account, not Contributor on the subscription. A deployment into one resource group needs a role at that resource group, not across everything.

```bash
# Grant a least-privilege role at the narrowest scope that works.
az role assignment create --assignee "$APP_ID" \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/$SUB_ID/resourceGroups/$RG/providers/Microsoft.Storage/storageAccounts/$ACCOUNT"
```

A new role assignment can take a short time to propagate before the principal can use it, so a failure in the first moments after granting is not necessarily a wrong assignment; rerun the call after propagation before concluding the scope was wrong. There is also a control-plane versus data-plane distinction that trips people: management operations on a resource and operations on the data inside it are governed by different roles, so a principal with Contributor on a storage account can still be denied reading a blob because blob data access needs a data role. The authorization side of this is treated end to end in the diagnosis of [why an AuthorizationFailed error appears and how to grant the right role at the right scope](/2022/10/10/fix-azure-rbac-authorizationfailed/), which is the companion to this article whenever the gate turns out to be authorization rather than authentication.

## Cause Seven: The Application or Service Principal Is Disabled or Deleted

An application registration and its service principal can be disabled, and a disabled principal cannot sign in even with a perfectly valid credential, the correct client ID, and the right tenant. The sign-in is rejected as unauthorized for the client because the directory will not issue tokens to a principal whose account is disabled. This happens through governance actions, lifecycle automation that disables stale identities, or an administrator response to a suspected exposure. A subtler version is a registration that exists without a corresponding service principal in the tenant you are signing into, which arises in multi-tenant patterns where the application is defined in a home tenant but never provisioned as a service principal in the tenant where it is being used.

Confirming the enabled state is a direct read of the service principal object, which carries an account-enabled flag.

```bash
# Read the enabled flag on the service principal.
az ad sp show --id "$APP_ID" \
  --query "{displayName:displayName, enabled:accountEnabled}" -o table
```

If the enabled flag is false, re-enabling the principal restores sign-in, assuming the disablement was not a deliberate security response that should stay in place. If `az ad sp show` reports that the principal does not exist while the application registration does, the fix is to create the service principal in the consuming tenant, after which role assignments can be made against it. Deletion is the harder version: a deleted registration or principal cannot authenticate, and while recently deleted registrations can sometimes be restored within a retention window, a fully removed identity must be recreated and have all of its credentials and roles reestablished, which is why deletion of an identity in active use is an incident rather than a quick fix. Distinguishing disabled from deleted matters because one is a single command to reverse and the other is a rebuild.

## Cause Eight: The Wrong Audience or Scope

A token is issued for a specific resource, named in the request as a scope ending in `/.default`, and the resource the token is good for is recorded in the token's audience claim. If you request a token for the wrong resource, Entra ID may reject the request with AADSTS500011, stating that the named resource principal was not found in the tenant, or it may issue a token whose audience does not match the resource you then call, in which case the call is rejected even though sign-in succeeded. Both are scope problems rather than credential problems, and both get misfiled as authentication failures because the symptom surfaces near sign-in.

The most common version is using a resource identifier that does not exist in the tenant, often a typo in the resource URI or a stale identifier for a service that has been renamed or whose endpoint has changed. Another version is requesting the management plane scope when the downstream call targets a data plane endpoint, so the token is valid but for the wrong audience. The confirmation is again the decoded token: the `aud` claim names the resource the token addresses, and comparing it against the endpoint you call exposes the mismatch.

```bash
# Request a token for an explicit resource and read the audience back.
TOKEN=$(curl -s -X POST \
  "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token" \
  -d "client_id=$APP_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "scope=https://storage.azure.com/.default" \
  -d "grant_type=client_credentials" | jq -r .access_token)

echo "$TOKEN" | cut -d. -f2 | tr '_-' '/+' \
  | awk '{ p=length($0)%4; if(p>0) for(i=p;i<4;i++) $0=$0"="; print }' \
  | base64 -d 2>/dev/null | jq '{aud}'
```

The fix is to request the token for the exact resource the downstream call expects, using the canonical resource identifier with the `/.default` suffix for the client credentials flow. When AADSTS500011 appears, verify that the resource identifier exists in your tenant and is spelled correctly, because the sign-in service is telling you it cannot find a principal for the resource you named, which is a different problem from any credential being wrong.

## When the Secret Lives in Key Vault: Layered Failures

A common and sensible pattern stores the service principal secret in Key Vault rather than in a pipeline variable or a configuration file, so the credential is centralized and access to it is itself governed. This is good hygiene, but it adds a layer where a failure can hide, because now there are two identities and two access checks in play: the consumer must first read the secret from Key Vault, and only then can it use that secret to sign in as the service principal. A failure at the first layer presents as an authentication failure at the second, even though the service principal credential is perfectly valid.

The confusing version runs like this. The secret in Key Vault was rotated, but the consumer reads a specific pinned version that is now the old expired value, so the sign-in fails with AADSTS7000222 while the current version in the vault is healthy. Or the consumer's own identity lost its access to the vault, so it cannot read the secret at all and falls back to an empty or stale string, producing AADSTS7000215 because what reaches the token endpoint is not the secret. Telling these apart from a genuine service principal credential problem means checking the Key Vault layer first: confirm the consumer can read the secret, and confirm which version it reads.

```bash
# Confirm the current secret value and version in Key Vault.
az keyvault secret show --vault-name "$VAULT" --name "$SECRET_NAME" \
  --query "{id:id, enabled:attributes.enabled, expires:attributes.expires}" -o table

# Confirm the consumer identity can actually read it.
az keyvault secret show --vault-name "$VAULT" --name "$SECRET_NAME" --query value -o tsv >/dev/null \
  && echo "read OK" || echo "READ DENIED or not found"
```

The fix depends on which layer broke. If the consumer reads a pinned old version, point it at the current version or stop pinning the version entirely. If the consumer cannot read the vault, restore its access rather than touching the service principal credential. The principle is the one that runs through the whole diagnosis: confirm which layer actually failed before changing the layer you assume failed, because the Key Vault indirection lets a storage-access problem wear the costume of a credential problem and send you rotating a secret that was never at fault.

## How Do You Prevent Service Principal Authentication Failures?

The single most effective prevention is to stop relying on long-lived shared secrets where the platform offers an identity that needs no secret at all. Inside Azure, a workload that runs on a virtual machine, a function, a container, or an App Service can use a managed identity, which the platform provisions and rotates without any secret for you to store, expire, or leak. A managed identity cannot expire the way a secret does, because there is no secret to expire, and it removes the entire AADSTS7000222 failure mode for in-Azure workloads. The choice between a managed identity and a service principal, and the cases where each fits, is laid out in the comparison of [when to use a managed identity versus a service principal and the trade-offs of each](/2024/01/08/managed-identity-vs-service-principal/), which is the decision to make before you ever create another secret.

For workloads that run outside Azure, such as a continuous integration pipeline on an external runner, the secretless path is workload identity federation, where the external system presents an OpenID Connect token that Entra ID trusts through a federated credential on the registration, and no secret is stored anywhere. This eliminates the expired-secret incident for the most common place it happens, which is a deployment pipeline. Setting this up so a pipeline obtains a short-lived token without holding any secret is covered step by step in the guide to [configuring GitHub Actions to authenticate to Azure with OIDC federated credentials](/2023/08/14/configure-github-actions-oidc/), and the same federation pattern applies to other external systems that can present an OIDC token.

```bash
# Add a federated credential so an external workflow signs in without a secret.
az ad app federated-credential create --id "$APP_ID" --parameters '{
  "name": "ci-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:my-org/my-repo:ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

Where a secret or certificate is genuinely unavoidable, the prevention is monitoring expiry before it bites. Microsoft Graph exposes the credential end dates for every registration, and a scheduled query that lists credentials expiring within a chosen window turns the silent Monday-morning outage into a ticket raised weeks ahead. Prefer certificates over secrets when you must hold a credential, because a certificate's longer practical life and clearer rotation story reduce the frequency of the incident, and prefer the narrowest role at the narrowest scope so that an authorization failure, when it does occur, is informative rather than the result of over-broad grants masking the real need.

```bash
# Find credentials expiring soon across registrations (adjust the window).
az ad app list --query "[].{name:displayName, id:appId, secrets:passwordCredentials[].endDateTime}" -o json \
  | jq '.[] | select(.secrets != null) | {name, id, secrets}'
```

Rotation discipline closes the loop: rotate on a schedule rather than at expiry, append the new credential before removing the old, prove the new path with the reproduction commands, and only then retire the previous credential. Building this rehearsal into a habit, rather than improvising it during an outage, is what the cutover and certification-style practice in the ReportMedic drills is for, and reproducing each prevention path against a sandbox principal in the VaultBook labs confirms the configuration before it reaches production. Treating expiry as a monitored event and treating the secret as the credential of last resort removes most of this article's failure modes before they can happen.

### How long should a service principal credential live?

The shortest lifetime you can sustain operationally, and shorter than most defaults make it. The convenience of a two-year secret is that you set it once and forget it, but that convenience is exactly what produces the fourteen-month-old expiry that nobody was watching, and a long lifetime also widens the window in which a leaked secret stays useful to whoever found it. A credential that lives ninety days forces a rotation cadence that keeps the process exercised, so the rotation is routine rather than a panicked first-time attempt during an outage. The shorter the secret lives, the smaller the blast radius if it leaks and the fresher your team's muscle memory for rotating it.

The catch is that a short lifetime is only safe if rotation is automated and monitored, because manual rotation on a ninety-day cycle becomes its own reliability problem. Rotate before expiry, never at it, leaving enough margin that a missed run does not become an outage. Track every credential's end date as a monitored metric and alert with days to spare rather than discovering the lapse from a failed deployment. The real answer to the lifetime question, though, is to remove it entirely where you can. A federated credential through workload identity has no expiry to manage because there is no stored secret at all, and a managed identity removes the question for in-Azure workloads the same way. Where you cannot go secretless, keep the lifetime short, automate the rotation, and monitor the expiry, in that order of preference.

### Should I use a managed identity instead of a service principal?

If the workload runs on an Azure resource that supports managed identity, yes, because a managed identity removes the secret you would otherwise have to store, rotate, and watch for expiry, which eliminates the most common service principal incident. A service principal remains the right tool for workloads outside Azure, though federated credentials make even those secretless.

## Defining the Service Principal and Its Roles as Code

The failures in this article are far less frequent when the identity, its credentials, and its role assignments are defined as code rather than clicked together in the portal, because code makes the configuration reviewable, repeatable across environments, and detectable when it drifts. An infrastructure-as-code definition records exactly which roles the principal holds at which scopes, so an authorization failure becomes a visible diff rather than a mystery, and it records the federated credential or certificate configuration so the secretless path is what ships by default rather than an afterthought bolted on later.

A role assignment expressed in Bicep ties the principal to a specific role at a specific scope, and because it lives in source control, the grant that someone made by hand and forgot is no longer how access is managed.

```bicep
// Assign a least-privilege role to the service principal at this scope.
param principalId string          // the service principal object ID
param roleDefinitionId string     // the built-in role's GUID

resource ra 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, principalId, roleDefinitionId)
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
    principalType: 'ServicePrincipal'
  }
}
```

Two details here prevent the most common mistakes. Setting `principalType` to `ServicePrincipal` avoids a replication race where a freshly created principal is not yet visible when the assignment is attempted, which otherwise produces a spurious failure that looks like a bad object ID. The deterministic name built from the scope, the principal, and the role keeps the assignment idempotent, so reapplying the template neither creates duplicate assignments nor fails on a name collision. Expressing the federated credential in code likewise makes the OIDC trust explicit and reviewable, so the issuer and subject the external workflow must match are not a setting buried in a blade that nobody can audit.

Drift is the remaining risk: someone grants Owner by hand to unblock an incident and never removes it, and the declared configuration no longer matches reality. A periodic comparison of the live role assignments against the declared ones catches this, and `az role assignment list --assignee $APP_ID --all` is the read that feeds that comparison. Defining the identity and its access as code does not erase the failure modes in the table, but it turns most of them from a live incident into a reviewable change, which is the larger aim throughout this work: reason about the system and version its configuration rather than click at it and hope the next environment matches.

## The Failures This Is Often Confused With

The closest sibling is the managed identity token failure, which looks similar because it is also an identity that cannot get or use a token, but its causes are different: an unreachable instance metadata endpoint, the wrong identity type assigned to the resource, or a missing role for the managed identity rather than an expired secret, since there is no secret. When a workload inside Azure cannot authenticate and there is no client secret in play, the diagnosis belongs to the analysis of [why a managed identity fails to obtain or use a token and how to confirm each cause](/2023/01/23/fix-managed-identity-token-error/), not to this article, and pointing the investigation at the right sibling early saves the time of checking credentials that do not exist.

The authorization failure is the other frequent confusion, and the whole point of the authn-versus-authz rule is to route it correctly: a 403 with `AuthorizationFailed` after a token issues is a role problem, and it is handled by granting the right role at the right scope rather than by anything in the credential path. A third confusion is the interactive sign-in error AADSTS50011, redirect URI mismatch, which belongs to user-facing application sign-in and has nothing to do with the client credentials flow a service principal uses; if you see a redirect URI error, you are debugging an interactive application, not a headless service principal, and the fix lives in the application's reply URLs rather than in any secret or role. Recognizing these neighbors by their distinct signals, the absence of a secret for managed identities, the post-token 403 for authorization, the redirect URI for interactive sign-in, keeps each failure on its own track instead of dragging a service principal credential reset into a problem it cannot solve.

## The Verdict

A service principal authentication error is almost never the single inscrutable failure it appears to be in the logs. It is one of a handful of distinct causes, and the first decision, made from the error class alone, cuts the problem in half: an AADSTS code at the token endpoint with no token issued is authentication, and a 403 with `AuthorizationFailed` after a token issues is authorization. Inside authentication, the specific AADSTS code points at the cause: 7000222 is an expired secret, 7000215 is a wrong secret value or encoding, 700016 is a wrong client ID or tenant, 90002 is an unresolvable tenant, 500011 is a wrong resource, and certificate failures show in the assertion and thumbprint. Inside authorization, the fix is a least-privilege role at the narrowest scope. Confirm before you change anything, using the direct sign-in to split the gates and the token decode to read the identity, and you will spend your effort on the actual cause rather than on the credential reset that habit suggests. The deeper durable move is to stop holding secrets where the platform will hold an identity for you, with managed identities inside Azure and federated credentials outside it, which removes the most common incident in this whole category before it can recur.

## Frequently Asked Questions

### Q: Why does my service principal authentication fail with no obvious change?

A service principal that worked for months and then fails without any code or configuration change almost always hit a credential expiry. Client secrets and certificates carry an expiry date set at creation, and when that date passes the sign-in is rejected with AADSTS7000222 for a secret or a comparable rejection for a certificate, even though nothing in your application changed. Confirm by listing the credentials on the registration and reading their end dates against the current date with `az ad app credential list --id $APP_ID`. If the only credential has expired, create a new one, propagate it to every place the consumer reads it, and prove the fix with a direct sign-in before retiring the old credential. The silent nature of this failure is exactly why monitoring credential expiry ahead of time turns an outage into a scheduled rotation.

### Q: Does an expired client secret break service principal authentication?

Yes, completely. When a client secret reaches its expiry date, Entra ID stops accepting it and returns AADSTS7000222 stating that the secret keys for the application are expired, and no token is issued. This is an authentication failure at the token endpoint, not an authorization problem, so granting roles will not help. The fix is to create a new secret with `az ad app credential reset --id $APP_ID --append`, capture the value at the moment it is shown because it is displayed only once, update every consumer that reads the secret, and verify a token issues before removing the expired credential. A frequent complication is a stale copy of the old secret lingering in a second location, so production keeps reading the expired value while another environment reads the new one and works, which makes the rotation look like it failed when the new value is actually correct.

### Q: How do I fix certificate-based service principal authentication?

Start by confirming the certificate on the registration is valid and matches what the application signs with. List the key credentials and their validity using `az ad app credential list --id $APP_ID --cert`, and if the certificate is expired, rotate it the same way you would a secret. If the certificate is valid but sign-in still fails, check that the PEM the application loads actually contains the private key, since exporting only the public certificate leaves nothing to sign the client assertion with, and compare the certificate thumbprint against the credentials on the registration so you know Entra ID recognizes the certificate the application uses. A quick way to prove the certificate path works end to end is to generate a self-signed certificate with `az ad app credential reset --id $APP_ID --create-cert`, which attaches the public certificate and writes a local PEM containing the private key, then sign in with that before wiring in your production certificate.

### Q: What does AADSTS7000215 mean for a service principal?

AADSTS7000215, invalid client secret provided, means Entra ID received a secret string it does not accept. The most common cause is copying the secret ID, which is a GUID that identifies the credential, instead of the secret value, which is the opaque string the application must present, because the portal shows both side by side and the value is masked after creation. The error description itself reminds you to send the value and not the ID. A second cause is a secret value with special characters that gets mangled by improper URL encoding in transit, so Entra ID receives a different string than you stored. Confirm by inspecting exactly what the application sends just before the request: if it matches the stored secret character for character, the problem is transport encoding, and if it does not match, you sent the wrong field. Fix the wrong field by regenerating and capturing the value, and fix the encoding by encoding the body correctly or generating secrets without problematic characters.

### Q: Can a wrong tenant or client ID cause a service principal failure?

Yes, and both can surface as AADSTS700016, application not found in the directory. A service principal lives in one tenant, and the token request must go to that tenant's authority; if the authority names the wrong tenant, the application is not found there even though the client ID is correct. If the tenant is right but the client ID is wrong, often copied from another registration or confused with the object ID, the directory again cannot find the application. Disambiguate by confirming the authority points at the intended tenant first, then verifying the client ID against the directory with `az ad app list --display-name` or `az ad sp show --id`. When a token does issue, decode it and read the `tid` and `appid` claims, which name the tenant that issued the token and the application that authenticated, exposing either mismatch directly. Prefer the tenant GUID over a domain name in automation so the value stays stable.

### Q: Is my service principal failure authentication or authorization?

Read whether a token was issued. If the token endpoint returned no token and the message carries an AADSTS code, the failure is authentication, meaning the credential, client ID, tenant, or registration is wrong, and you fix it by correcting the credential or identifier. If a token was issued and the target resource returned HTTP 403 with an `AuthorizationFailed` body, the failure is authorization, meaning the identity is valid but lacks a role, and you fix it by assigning the right role at the right scope. The fastest way to split the two is a direct sign-in with `az login --service-principal`: if it succeeds, authentication is healthy and your problem is a role, and if it fails with an AADSTS code, authentication is the problem and no role change will help. This single decision prevents the most common wasted effort in the whole category, which is resetting a credential to solve a missing-role 403.

### Q: How do I confirm which service principal credential is in use?

Decode the access token the sign-in produces, because the token carries claims that name the identity acting. Capture the token from a direct request, then decode the middle segment of the JWT and read the `appid`, `tid`, and `aud` claims, which name the application that authenticated, the tenant that issued the token, and the resource the token is good for. If `appid` is not the application you meant to use, you have the wrong client ID. If `tid` is an unexpected tenant, your authority is wrong. If `aud` is not your target resource, you requested the wrong scope. Decoding takes a `cut` to extract the segment, a `tr` to convert from base64url, padding to a multiple of four, a `base64 -d`, and a `jq` to read the claims. Reading the identity rather than guessing turns several separate causes into one confirming step you can run in seconds.

### Q: What is AADSTS7000222 and how is it different from AADSTS7000215?

AADSTS7000222 means the client secret has expired, so the value was once valid and its lifetime ran out, and the fix is to rotate the secret and update the consumer. AADSTS7000215 means the secret value is invalid, which is a different problem: the wrong field was sent, usually the secret ID instead of the value, or a correct value was corrupted by improper encoding in transit. Both arrive as `invalid_client` at the HTTP level, which is why engineers conflate them, but the numeric AADSTS suffix separates them cleanly. Always grep the error description for the numeric code rather than reading only the phrase invalid client, because the phrase generalizes across both and the code does not. Rotating a secret will fix 7000222 and do nothing for 7000215, and sending the correct value will fix 7000215 and do nothing if the credential is actually expired, so reading the code first decides which action to take.

### Q: Why does my service principal get a token but still get denied?

Because the failure is at the authorization gate, not the authentication gate. A successful token proves the identity authenticated correctly: the credential, client ID, and tenant were all right. The denial that follows, an HTTP 403 with `AuthorizationFailed`, means the identity holds no role permitting the action it attempted at the scope of the target resource. The fix is to assign the least-privilege role that covers the action, at the narrowest scope that covers the resource, using `az role assignment create`. Resetting the secret here is the canonical wasted fix, because the secret was never involved in the rejection. Watch also for the control-plane versus data-plane split: a role that manages a resource does not automatically grant access to the data inside it, so a principal with Contributor on a storage account can still be denied reading a blob, which needs a data role. New role assignments take a short time to propagate, so retry after a moment before concluding the scope was wrong.

### Q: How do I rotate a service principal secret without downtime?

Append the new secret before removing the old one so both are valid during the changeover. Run `az ad app credential reset --id $APP_ID --append` to create a fresh secret while the existing credential stays in place, and capture the new value immediately because it is shown only once. Update every consumer that reads the secret, which may include a pipeline variable group, a Key Vault entry, an application setting, or a configuration file, and then prove the new value works with a direct sign-in. Only after the new path is confirmed should you remove the expired or old credential from the registration. The downtime that people accidentally cause comes from replacing the only credential before the new value has reached every consumer, so a stale reader is left with nothing valid. Keeping both credentials live during propagation, and retiring the old one as the final step, makes the rotation a non-event rather than an outage.

### Q: Should I use a certificate or a secret for a service principal?

Prefer a certificate when you must hold a credential at all, and prefer no credential when the platform offers a managed identity or federated credentials. A certificate uses an asymmetric key pair where the private key never travels to Entra ID, which is a stronger posture than a shared secret that must be transmitted, and certificates tend to have a longer practical life and a clearer rotation story, which reduces the frequency of the expiry incident. The trade-off is that certificate failures are less self-explanatory than the secret error codes, so when one fails you check the private key in the PEM and the thumbprint against the registration rather than reading a single clear message. For workloads inside Azure, a managed identity removes the credential entirely, and for external workloads, workload identity federation lets the system present an OIDC token so no secret is stored anywhere, which is the strongest option of all.

### Q: How do I monitor service principal credential expiry before it fails?

Query the credential end dates and alert on credentials approaching expiry, rather than waiting for the silent failure. The registration exposes the end dates for both secrets and certificates, and a scheduled query that lists credentials expiring within a chosen window turns a Monday-morning outage into a ticket raised weeks ahead. With the CLI you can list registrations and project their secret end dates with `az ad app list` and filter the results, and the same data is available through Microsoft Graph for a more structured automation. Set the alert window wide enough to allow a calm rotation, well before the deadline, and route the alert to the team that owns the workload so the rotation is owned rather than orphaned. The deeper fix is to remove the credential entirely where possible, but where a credential must exist, treating its expiry as a monitored event is what prevents the most common service principal incident from ever reaching production.

### Q: Why does my service principal work in development but not in production?

The most frequent reason is that production and non-production live in different tenants or use different registrations, and a value carried over from development points at the wrong directory or the wrong application in production. A staging authority promoted unchanged into a production subscription that sits in another tenant leaves the production application unreachable, often with AADSTS700016 or AADSTS90002. A second common reason is a stale credential: production reads an old secret from a location that was never updated during a rotation, so it fails while development reads the new value and works. Confirm by comparing the tenant and client ID each environment uses, decoding the token from each to read the `tid` and `appid` claims, and verifying that the secret production reads matches the current credential on the registration. Keeping per-environment configuration genuinely separate, pinning the tenant by GUID, and using a distinct principal per tenant removes this whole class of cross-environment surprise.

### Q: What does AADSTS500011 mean for a service principal token request?

AADSTS500011 states that the named resource principal was not found in the tenant, which means the resource or scope you requested a token for does not exist there as you named it. This is a scope problem, not a credential problem, even though it surfaces near sign-in and gets misfiled as authentication. The usual cause is a typo in the resource identifier or a stale identifier for a service that has been renamed or whose endpoint changed, and the fix is to request the token for the correct resource using its canonical identifier with the `/.default` suffix for the client credentials flow. A related version issues a token whose audience does not match the endpoint you then call, so the token is valid but for the wrong resource and the call is rejected; decode the token and read the `aud` claim to compare it against the endpoint you are calling. Resetting the credential will not help, because the credential was accepted; the resource you asked for is what could not be resolved.

### Q: Can a disabled service principal cause an authentication failure?

Yes. A service principal whose account is disabled cannot sign in even with a valid credential, the correct client ID, and the right tenant, because the directory will not issue tokens to a disabled principal, and the sign-in is rejected as unauthorized for the client. This happens through governance actions, lifecycle automation that disables stale identities, or an administrator response to a suspected exposure. Confirm by reading the enabled flag on the service principal with `az ad sp show --id $APP_ID`, and if the flag is false, re-enabling restores sign-in, provided the disablement was not a deliberate security measure that should remain in force. A related case is a registration that exists without a corresponding service principal in the consuming tenant, where the fix is to create the service principal in that tenant before assigning roles. Distinguish disabled from deleted, because a disabled principal is one command to reverse while a deleted one must be recreated with all its credentials and roles reestablished.

### Q: How do I reproduce a service principal authentication error in isolation?

Run a direct sign-in with the same three values the failing job uses, stripping away the surrounding pipeline so you debug only the credential exchange. Use `az login --service-principal --username $APP_ID --password $CLIENT_SECRET --tenant $TENANT_ID`, and read the result: a failure with an AADSTS code means the problem is in authentication, while a success means authentication is healthy and your problem is a role. For a certificate principal, pass the path to a PEM containing the private key in place of the secret. To see the raw exchange, request a token directly against the token endpoint with a curl POST using `grant_type=client_credentials`, which returns either an `access_token` field on success or an `error_description` beginning with the precise AADSTS code on failure. That code is the most valuable string in the investigation, because it narrows the cause before you change anything, and the isolated reproduction guarantees you are not chasing a fault that actually lives in the pipeline's wiring rather than the identity.

### Q: What is the difference between a service principal authentication error and a managed identity token error?

A service principal authenticates with a credential you manage, a client secret or a certificate, so its failures include expired secrets, wrong secret values, certificate problems, wrong client IDs, and wrong tenants. A managed identity has no secret you hold, because the platform provisions and rotates it, so its failures are different: an unreachable instance metadata endpoint, the wrong identity type assigned to the resource, or a missing role rather than an expired credential. When a workload inside Azure cannot authenticate and there is no client secret involved, you are almost certainly looking at a managed identity token problem, not a service principal credential problem, and checking for an expired secret is wasted effort because none exists. The shared symptom is an identity that cannot get or use a token, but the absence of a secret is the tell that routes you to the managed identity diagnosis. Pointing the investigation at the right one early avoids checking credentials that the identity does not even have.

### Q: How do I read service principal sign-in failures in the logs?

Entra ID records service principal sign-ins separately from user sign-ins, and each failed entry carries the application ID, the resource requested, a failure reason that usually names the AADSTS code, and a correlation ID. When the logs are exported to a Log Analytics workspace, query the service principal sign-in table for the application over a recent window, filter to non-zero results, and group by the failure code and the resource. A `ResultType` of zero is a success, and any non-zero value is the numeric AADSTS code with a description alongside it. Grouping by resource is diagnostic: failures clustered on one resource point at a scope or audience problem, while failures across every resource point at a credential problem, because a bad credential fails everywhere and a bad scope fails for one target. The correlation ID on a specific failure is the value to give support if you escalate, since it identifies the exact request in the service's telemetry.

### Q: Why does my service principal fail only when the secret is stored in Key Vault?

Storing the secret in Key Vault adds a layer where a failure can hide, because the consumer must first read the secret from the vault and only then use it to sign in. A failure at the read layer surfaces as an authentication failure at the sign-in layer even though the service principal credential is valid. Two versions are common. The consumer reads a pinned old secret version that has expired while the current version in the vault is fine, producing AADSTS7000222. Or the consumer lost its access to the vault and falls back to an empty or stale value, producing AADSTS7000215 because what reaches the token endpoint is not the real secret. Check the Key Vault layer first by confirming the current version and that the consumer can read it, and fix the layer that actually failed rather than rotating a service principal credential that was never the problem.

### Q: What is the difference between the v1 and v2 token endpoints for a service principal?

The older v1 token endpoint takes a resource parameter that names the target by its identifier URI, while the newer v2 endpoint takes a scope parameter that appends `/.default` to the resource identifier to request all of the application permissions configured for that resource. Sending a v1-style resource value to the v2 endpoint, or omitting the `/.default` suffix on v2, produces a request the service cannot satisfy even when the credential, client ID, and tenant are all correct, and it often surfaces as a resource-not-found or invalid-scope rejection rather than a credential error. For the client credentials flow a service principal uses, the v2 pattern is a scope set to the resource identifier followed by `/.default`. Matching the parameter to the endpoint removes a class of failure that looks like a permissions problem but is really a malformed request, so confirm which endpoint you are calling before you suspect the credential.
