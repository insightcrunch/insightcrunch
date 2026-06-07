---
layout: post
title: "Fix Entra ID AADSTS50011 Redirect Error"
page_title: "AADSTS50011 Redirect URI Mismatch in Microsoft Entra ID: Causes, Diagnosis, and How to Fix the Sign-In Error"
date: 2022-09-19
categories: ["Technology"]
tags: ["Azure", "Microsoft Entra ID", "AADSTS50011", "Troubleshooting", "Identity", "Security"]
excerpt: "AADSTS50011 means the redirect URI in the request does not match your Entra app registration. Read the rejected value and fix the exact mismatch fast."
image: "/assets/images/blog/blog-93.webp"
reading_time: 60
author: "james-carter"
last_updated: 2022-09-19
lang: en
---
When a sign-in dies with **AADSTS50011**, the screen tells you almost everything you need, and almost everyone reads past it. The error means one precise thing: the redirect URI your application sent in the authorization request does not match any redirect URI registered on the Microsoft Entra ID app registration. It is not a consent failure. It is not a bad client secret. It is not a token-lifetime problem. Entra received a return address, compared it character by character against the list you configured, found no match, and refused to send the authorization response anywhere it was not told to send it. The whole repair lives in that comparison, and the error names the exact address it rejected.

![Fixing Entra ID AADSTS50011 redirect URI mismatch - Insight Crunch](/assets/images/blog/blog-93.webp)

The reason this error wastes so much engineer time is that the surrounding context invites a wrong theory. The sign-in was working yesterday, or it works for a colleague, or it works on a different machine, so the instinct is to suspect permissions, scopes, admin consent, or a stale token cache. People open the API permissions blade and start granting things. None of that touches the redirect comparison, so the symptom survives every one of those changes, and the wasted hour begins. The discipline that fixes AADSTS50011 quickly is the opposite instinct: read the rejected address out of the error, open the registration, and find the single character that differs. This guide gives you that discipline as a repeatable procedure, names each distinct cause behind the mismatch, and hands you the command to confirm and correct each one.

## How to read the AADSTS50011 error and gather the diagnostic signal

The message itself is the primary diagnostic instrument, and it is structured. A current form reads close to: "AADSTS50011: The redirect URI specified in the request does not match the redirect URIs configured for the application." Newer renderings name the offending value and the application identifier directly, something like the redirect URI value in single quotes followed by the application id it was checked against. Treat the exact wording as something to confirm in your own tenant rather than memorize, because Microsoft revises these strings, but the two facts you must extract never change: the URI Entra received, and the application it compared that URI against.

### What does AADSTS50011 actually mean?

It means Entra ID got an authorization request whose `redirect_uri` parameter is not on the registered list for that application. Entra will only return an authorization code or token to a pre-registered address, a defense against token theft, so an unregistered or slightly different address is rejected outright before any consent or credential step.

The value you need first is the redirect URI Entra received. You can read it three ways, and at least one is always available. The fastest is the error page itself in a recent tenant, which prints the received value inline. When the page is terse, look at the browser address bar at the moment of failure: the sign-in request is a `GET` to the `authorize` endpoint, and the full query string is right there, with the `redirect_uri` parameter URL-encoded. Copy that parameter and decode it, because `%2F` is a slash, `%3A` is a colon, and a difference hiding inside the encoding is the most commonly missed difference of all. The third way, when the failure happens inside a redirect chain you cannot see, is to capture the network trace. In a browser, open developer tools, enable preserve log, reproduce the failure, and find the request to `login.microsoftonline.com` whose path ends in `/oauth2/v2.0/authorize` or `/oauth2/authorize`. Its query string holds the same `redirect_uri` value.

Once you hold the received value, the second half of the signal is the registered list. For an application you administer, the portal shows it under the app registration's Authentication blade, grouped by platform. From the command line, the registration is queryable directly, and reading it this way removes the chance that your eyes round two near-identical strings to equal:

```bash
# Show every redirect URI registered on the app, grouped by platform type
az ad app show --id <application-client-id> \
  --query "{web:web.redirectUris, spa:spa.redirectUris, publicClient:publicClient.redirectUris}"
```

That single command returns the three buckets that matter, and the bucket a value sits in is itself part of the diagnosis, as a later cause will show. With the received URI in one hand and the registered list in the other, the rest of this article is a structured walk through every reason the two fail to match, each with the way to confirm it is your reason and the exact change that resolves it.

## The exact-match rule, and why AADSTS50011 is a comparison, not a permission

Here is the claim this whole article rests on, the one worth remembering long after the specific portal blades move. Call it the exact-match rule for AADSTS50011: the redirect URI in the request must match a registered redirect URI to the character, including the scheme, the host, the port, the path, and any trailing slash, and it must be registered under the platform type that matches the flow the application is using. There is no fuzzy matching, no normalization that forgives a trailing slash, no implicit promotion from `http` to `https`, and no shared pool across platform types. The address is compared as a literal string within the correct bucket, and anything short of an identical string in the right bucket is a mismatch.

### Is AADSTS50011 a permissions or consent problem?

No. AADSTS50011 is evaluated before consent and before any credential check, purely on whether the return address is registered. If you are editing API permissions, granting admin consent, or rotating a client secret to fix it, you are working on the wrong layer entirely, and the error will persist unchanged until the redirect URI itself matches a registered value.

Internalizing the rule reframes every cause below as a variation on a single question: which character, or which bucket, differs between what the app sent and what the registration holds? The causes are distinct because the difference hides in different places, a slash here, a scheme there, a platform type elsewhere, but the fix is always the same shape. Read the received value, find the divergence, and either correct the value the app sends or add that exact value to the right platform bucket in the registration. The series treats this as a habit worth generalizing: a precise error names a precise condition, and the repair follows the named condition rather than a hunch. The same posture underpins the broader model of how an app obtains a token, which the deep dive on [how Microsoft Entra ID issues tokens and governs identity](/2022/02/21/microsoft-entra-id-explained/) lays out in full, and it is worth holding that model in view as we separate the causes.

One more framing matters before the causes. A redirect URI you register must be an absolute URI, and Entra constrains what it will accept: it does not match on query string or fragment, so a registered value never carries a `?query` or `#fragment`, and the comparison is performed on the scheme, host, port, and path. That constraint is why a difference is almost always in one of exactly those four parts, plus the trailing slash that is technically part of the path. Knowing the comparison is scoped to those parts narrows every hunt.

## Cause one: the trailing slash that is present on one side and absent on the other

The single most common AADSTS50011 is a trailing slash. The application sends `https://app.contoso.com/auth/callback/` and the registration holds `https://app.contoso.com/auth/callback`, or the reverse. The two look identical at a glance, identical when pasted into a chat message, identical to a tired reviewer, and they are not identical to Entra. The path `/auth/callback/` and the path `/auth/callback` are different strings, so the comparison fails and the slash costs you an afternoon.

### Does a trailing slash really cause AADSTS50011?

Yes, directly and reliably. Entra compares the path segment as a literal, and a terminal slash is part of that segment. `https://app.contoso.com/` and `https://app.contoso.com` are two distinct registered values, and an application configured to send one when the other is registered produces AADSTS50011 every time, with no other misconfiguration present.

Confirm it by decoding the received `redirect_uri` and laying it directly above the registered value, end aligned. The slash difference shows at the right edge. The trap is that many code editors and chat tools trim trailing whitespace and sometimes trailing slashes on paste, so comparing by eye in the wrong tool can erase the very difference you are hunting. Use the command line query shown earlier, or paste both strings into a tool that preserves them exactly, and compare the final character deliberately. Where the difference comes from is usually one of two places. Either the framework or authentication library building the request appends or omits the slash according to a default you did not set, or whoever registered the URI typed it from memory and added or dropped the slash without noticing.

The fix has two valid directions, and choosing correctly avoids a second round trip. If the application is sending the canonical address your team intends, change the registration to match it exactly. If the application is sending a stray slash because of a misconfigured base URL or a library default, fix the application so it sends the intended address, then make sure that intended address is what is registered. Registering both the with-slash and without-slash variants is a tempting shortcut and is occasionally justified, but it hides the real inconsistency and tends to multiply across environments, so prefer to make the application deterministic about which address it sends. To set the registered value from the command line for a web-platform app:

```bash
# Replace the entire web redirect URI list with the exact intended value
az ad app update --id <application-client-id> \
  --web-redirect-uris "https://app.contoso.com/auth/callback"
```

Note that this command replaces the web redirect list rather than appending to it, so include every web URI the app legitimately uses in the same call. After the change, reproduce the sign-in. A registration edit takes effect quickly, though propagation is not always instantaneous, so if the first retry still fails, wait briefly and confirm the registered value reads back exactly as intended before concluding the slash was not the cause.

## Cause two: a scheme, host, or port mismatch

The scheme, the host, and the port are each part of the literal comparison, and each produces AADSTS50011 when it diverges. The scheme case is usually `http` against `https`: a local or misconfigured deployment serves over `http`, the registration holds the `https` form, and the strings differ at the first token. Entra does not silently upgrade `http` to `https` for matching, and it has tightened what it accepts for non-localhost `http` over time, so an `http` redirect to a real host is both a mismatch and, increasingly, a value Entra will not even let you register.

The host case is subtler because hosts have aliases. `app.contoso.com` and `www.app.contoso.com` are different hosts. `contoso.azurewebsites.net` and a custom domain mapped to the same App Service are different hosts. An apex domain and its `www` variant are different hosts. Each requires its own registered redirect URI if the application can be reached through more than one of them, because the application builds the redirect from whichever host the user actually arrived on, and that host must be on the list.

### Why does my redirect work on one URL but fail on another?

Because the application constructs the redirect URI from the host the request arrived on, and Entra matches that constructed value literally. If users can reach the app through both an apex domain and a `www` subdomain, or through both the default `azurewebsites.net` host and a custom domain, each distinct host produces a distinct redirect URI that must be registered separately.

The port case bites hardest in development and behind non-standard front ends. A local dev server on `https://localhost:5001` is a different value from `https://localhost:3000`, and a registered `https://localhost` with no port is different again, because an absent port is not a wildcard. When a framework changes its default development port between versions, an app that worked last month can fail today purely because the port in the request moved while the registration stayed. Confirm any of these by decoding the received URI and comparing the scheme token, the host token, and the port token against each registered value in turn. The fix is to register the exact scheme, host, and port the application actually sends, or to make the application send the address you have registered. For an app reachable through several legitimate hosts, register each one explicitly rather than hoping one covers the others.

```bash
# Register multiple legitimate web hosts in one update (apex plus www, plus a default host)
az ad app update --id <application-client-id> \
  --web-redirect-uris \
    "https://contoso.com/signin-oidc" \
    "https://www.contoso.com/signin-oidc" \
    "https://contoso.azurewebsites.net/signin-oidc"
```

Keep this list deliberate. Every host you register is a place a token can be returned to, so register the hosts the application genuinely uses and no more. The discipline of treating the redirect list as a small, intentional set rather than a junk drawer is itself part of the prevention this article returns to later.

## Cause three: the platform-type mismatch, a single-page app URI registered under Web

This is the cause that survives the longest because the redirect URI string can be perfectly correct and the sign-in still fails. Entra groups registered redirect URIs by platform: Web, for confidential server-side apps that hold a secret; Single-page application, for browser apps that run the authorization code flow with PKCE and need cross-origin handling; and Mobile and desktop applications, the public-client bucket for native apps and redirects like a custom scheme or a loopback address. A redirect URI is only matched within the bucket that fits the flow the request is using. Register the right string in the wrong bucket and you get AADSTS50011 even though the address is letter for letter what the app sent.

### Does the platform type (SPA versus Web) matter for AADSTS50011?

It does, decisively. A browser app using the authorization code flow with PKCE must have its redirect URI under the Single-page application platform, not under Web. The same string registered under Web will not satisfy a SPA request, and Entra surfaces that as a redirect mismatch. The bucket is part of the match, not just the string.

The classic instance is a React, Angular, or Vue application whose redirect was originally registered under Web, perhaps copied from an older server-rendered app or added before the team understood the distinction. The browser app runs the modern PKCE flow, Entra evaluates the request against the SPA bucket, finds nothing there, and rejects it. The confusing part for the engineer is that the Web bucket clearly shows the correct URI, so the registration looks right. Confirm this cause by checking which bucket holds the value: the command-line query from earlier returns `web`, `spa`, and `publicClient` lists separately, and the diagnosis is immediate when the URI sits in `web` but the app is a single-page application. The reverse also happens, a server-side app whose redirect drifted into the SPA bucket, with the same symptom.

The fix is to move the redirect URI to the correct platform. In the portal, remove it from the wrong platform section and add it under the right one. From Microsoft Graph or the CLI, set the appropriate property: a SPA redirect goes in the `spa.redirectUris` collection, a web redirect in `web.redirectUris`, and a native or loopback redirect in `publicClient.redirectUris`. The Graph patch makes the placement explicit:

```http
PATCH https://graph.microsoft.com/v1.0/applications/{object-id}
Content-Type: application/json

{
  "spa": {
    "redirectUris": ["https://app.contoso.com/", "http://localhost:3000/"]
  }
}
```

Patch the property for the platform the application actually uses, and clear the value out of the bucket it does not belong in so the registration tells the truth about the app's type. The relationship between the registration, its platform configuration, and the way each flow consumes a redirect is laid out in depth in the guide to [how Entra app registrations and reply URLs are configured](/2024/03/04/entra-app-registrations-explained/), which is the reference to keep open when a string is correct but the platform is wrong. If you are unsure which flow your app runs, the guide to [how Entra ID authentication and the OAuth flows work](/2023/12/18/entra-id-authentication-explained/) maps each application type to its flow and therefore to the platform bucket its redirect belongs in.

## Cause four: a localhost redirect that works in development and was never registered for the deployed URL

Local development hides this cause until the moment of deployment. The app runs against `http://localhost:5000` or `https://localhost:5001`, that loopback address is registered, sign-in works on every developer machine, and confidence is high. Then the app deploys to `https://app.contoso.com`, the deployed instance builds its redirect from the production host, that production address was never added to the registration, and the first real sign-in fails with AADSTS50011. The development URL and the production URL are simply two different values, and registering one says nothing about the other.

### Why does AADSTS50011 happen only after deployment?

Because the redirect URI the app sends is derived from the host it runs on, and the production host's redirect URI was never registered. Localhost works because the loopback redirect was added during setup, but no one added the deployed origin, so the first sign-in against the real domain hits a redirect the registration has never seen.

There is a second, quieter version of this cause inside development itself. Loopback redirects sit in the public-client or, for browser apps, the SPA bucket, and a `http://localhost` value is treated specially enough that it works without TLS, which is convenient locally and misleading for production. Engineers sometimes assume the same leniency extends to the deployed host, register an `http` production URL, and meet both a mismatch and Entra's refusal to accept plain `http` for a non-loopback host. Confirm the deployment version of this cause by reading the received redirect after deploying: it carries the production host, and a query of the registration shows only the localhost values present. The fix is to register the deployed origin's redirect URI under the correct platform, alongside the localhost values you keep for development, so both environments resolve.

```bash
# Keep the local loopback for dev and add the deployed origin, both under SPA for a browser app
az ad app update --id <application-client-id> \
  --enable-id-token-issuance false
# Set SPA redirect URIs via Graph or portal; CLI flags for spa vary by version, so verify the current syntax
```

Because the CLI surface for the SPA platform has shifted across versions, treat the exact flag names as something to verify against your installed CLI rather than as fixed, and fall back to the Graph patch shown for cause three when a flag is unavailable. The durable practice is to register every environment's redirect at the time you stand that environment up, which the prevention section turns into a checklist so a deployed URL is never the thing nobody remembered.

## Cause five: a new environment URL that nobody added to the registration

Cause four is the first deployment. Cause five is every environment after it. Teams stand up staging, QA, a preview slot, a per-pull-request ephemeral environment, a new region, or a customer-specific subdomain, and each new origin produces a new redirect URI that the registration has never seen. The application code is correct, the existing environments still work, and the new environment fails with AADSTS50011 because its host is new and unregistered. This is less a bug than an operational gap: the registration is a manually maintained list, and a new environment is a new entry someone has to make.

The pattern is sharpest with deployment slots and ephemeral preview environments, where the host name is generated and may include a slot name or a build identifier, so the redirect URI is not even known until the environment exists. An app deployed to a staging slot at `https://app-staging.azurewebsites.net` sends a redirect with that host, and unless staging's address was registered, the slot's sign-in fails while production's succeeds. Confirm by comparing the failing environment's received redirect against the registered list: the host will be the new environment's host, absent from the registration. The fix is to add the new environment's redirect URI under the correct platform. Where environments are numerous or ephemeral, the registration itself becomes something to manage as code, generating and applying the redirect list from the same pipeline that creates the environment, so a new origin and its registration entry are created together rather than discovered apart. That automation is the same instinct behind treating any environment-specific auth value as configuration the deployment owns, and it pairs naturally with the way the related consent error is prevented, covered in the walkthrough of [fixing the AADSTS65001 consent-required error](/2022/10/03/fix-aadsts65001-consent-required/), since both errors tend to surface in a freshly created environment for the same reason: something environment-specific was not provisioned with the environment.

## Cause six: a reverse proxy or load balancer rewriting the redirect host

The hardest AADSTS50011 to diagnose is the one where the application code is correct, every intended URL is registered, and the sign-in still fails because something between the user and the app rewrote the host the application sees. A reverse proxy, an ingress controller, an Application Gateway, a CDN, or a load balancer terminates the external request at a public host like `https://app.contoso.com` and forwards it internally to the application on a different host, perhaps an internal service name, a pod address, or `localhost` on the app's own port. If the application builds its redirect URI from the host header it receives internally rather than from the original external host, it sends a redirect for the internal address, and that internal address is not, and should not be, registered.

### Can a reverse proxy cause AADSTS50011 even when my code is correct?

Yes. When a proxy forwards traffic to the app on an internal host, the app may build its redirect URI from that internal host instead of the public one users see. The resulting redirect carries an internal address that was never registered, so Entra rejects it, even though the application logic and the registration both look correct in isolation.

This cause announces itself in the received redirect URI. Decode the `redirect_uri` from the failing request and look at the host: if it is an internal name, a private address, a container or pod host, or a port that only exists behind the proxy, the proxy is rewriting the host the app builds from. The fix lives in two places and you want the application side, not the registration side. Registering the internal host would technically silence the error but would also mean issuing tokens for an internal address, which is both fragile and a security smell. Instead, make the application honor the forwarded host. Most frameworks support reading the standard forwarding headers, `X-Forwarded-Host`, `X-Forwarded-Proto`, and related values, and reconstructing the external URL from them, provided the proxy is trusted and the framework's forwarded-headers handling is enabled and configured to trust the proxy. With forwarded headers honored, the application builds its redirect from `https://app.contoso.com` again, the registered value matches, and AADSTS50011 clears without ever registering an internal address. Where the proxy is an Azure layer-seven service, this interacts with how that service preserves or rewrites the host, so confirm the proxy is configured to pass the original host or the headers that convey it.

## How the authorization request builds the return address in the first place

To fix the mismatch reliably you need to know where the requested value comes from, because the value Entra rejects is not pulled from the registration; it is assembled by your application or its identity library and placed into the authorization request as the `redirect_uri` query parameter. In the authorization code flow that nearly every interactive app now uses, the application sends the user's browser to the Entra `authorize` endpoint with a set of parameters: the client id that names the application, the response type, the requested scopes, a state value, a PKCE challenge for public clients, and the return address. Entra authenticates the user, evaluates policy, and then sends the authorization code back to that return address, but only after confirming the address is one it was told to trust. The comparison this article is about happens at that confirmation step, against the value the application chose when it built the request.

That origin matters because it tells you which side to fix. If the application assembles the return address from its own configured base URL and a fixed callback path, the value is predictable and you change it in configuration. If the application derives the base URL from the incoming request's host header, the value depends on how the user reached the app and on anything in between that rewrites the host, which is why a proxy can change it without a code change. And if an identity library builds the value from a default you never set, the value can move when you upgrade the library. Knowing the assembly path turns a blind comparison into a targeted one: you are not guessing why the strings differ, you are tracing how the requested string was produced and intervening at the step that produced the wrong character.

### Where does the redirect_uri parameter come from in my app?

It is set by your application or its authentication library and sent as a query parameter to the Entra `authorize` endpoint. Depending on the stack, it comes from an explicit configuration value, a callback path appended to a base URL, or a host the app derives from the incoming request. Identify that source and you know exactly where to correct a wrong return address.

The practical takeaway is to make the assembled value deterministic. An interactive web framework typically computes the return address as its public origin plus a callback path, so two knobs decide the result: what the framework believes its origin is, and what callback path it appends. Pin both. When the origin is computed from the request rather than fixed, decide explicitly whether you trust forwarding headers and configure that trust, so the computed origin is the public one and not an internal hop. When the callback path is a library default, write it down in configuration so a library upgrade cannot move it underneath you. The registration then holds that one deterministic value per origin, and the comparison succeeds by construction rather than by luck. This is the same mechanism the broader treatment of [how Entra ID authentication and the OAuth and OIDC flows operate](/2023/12/18/entra-id-authentication-explained/) describes from the protocol side; here we are simply naming the one parameter in that flow that AADSTS50011 polices.

## Fixing the mismatch across common application stacks

The cause is universal but the knob you turn differs by framework, so it helps to name the specific configuration each common stack uses to build its return address. Treat the property names below as accurate to the libraries as commonly used, and verify the exact spelling against the version you have installed, since identity libraries rename and relocate settings between major versions.

A server-rendered ASP.NET Core app using the Microsoft identity library computes its return address as its origin plus a callback path that defaults to a well-known value for the OpenID Connect handler, with a separate path for sign-out. If the app sits behind a proxy, the origin the framework sees is the internal one unless the forwarded-headers middleware is enabled and configured to trust the proxy, which is the single most common reason an otherwise correct ASP.NET Core app emits an internal return address. The fix is to enable that middleware early in the pipeline and register the public origin plus the handler's callback path:

```csharp
// Honor the proxy's forwarded host and scheme so the app builds its public return address
var forwardedOptions = new ForwardedHeadersOptions
{
    ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto | ForwardedHeaders.XForwardedHost
};
// In production, restrict to the known proxy rather than trusting all forwarders
app.UseForwardedHeaders(forwardedOptions);
// The registered value is then: https://<public-host>/signin-oidc
```

A browser single-page application built on the MSAL browser library carries its return address as an explicit configuration value rather than a derived one, which removes the proxy problem but makes the platform bucket the thing to get right: that value must be registered under the Single-page application platform, and the configured value must equal it character for character, trailing slash included. The configuration is small and worth reading aloud against the registration:

```javascript
// MSAL.js auth config; redirectUri must match a value registered under the SPA platform
const msalConfig = {
  auth: {
    clientId: "<application-client-id>",
    authority: "https://login.microsoftonline.com/<tenant-id>",
    redirectUri: "https://app.contoso.com/"
  }
};
```

A daemon or service that authenticates with the client credentials flow has no return address at all, because no user and no browser are involved, so AADSTS50011 should never arise there; if it does, the real problem is that the app is using an interactive flow where it meant to use client credentials, and the fix is the flow choice rather than the registration. A native mobile or desktop app uses a return address registered under the public-client platform, which can be a loopback address, a platform-brokered redirect of the form the platform expects, or a custom scheme; each must be registered under that public-client bucket and must equal what the app's library emits. Server-side libraries in Node and Python follow the same shape as ASP.NET Core conceptually: the return address is either an explicit value you pass when you build the authorization request or an origin the framework derives, so the discipline is identical, pin the value, register it under the platform that matches the flow, and confirm the two agree.

### Which configuration setting controls the return address in my framework?

In a server-rendered app it is usually the public origin combined with a fixed callback path, and behind a proxy it depends on forwarded-headers handling. In a single-page app it is an explicit configured value that must live under the SPA platform. In a native app it is an explicit value under the public-client platform. Pin whichever applies and register that exact value.

The lesson across stacks is that the return address is always either explicitly configured or derived, and your job is to know which and to make the explicit case canonical or the derived case trustworthy. When you treat it as explicit, you remove every typographical cause at once because there is a single source of truth you register against. When it must be derived, you remove the proxy and host causes by controlling what the framework derives from. The deeper model of how a registration exposes platforms, credentials, and reply URLs sits in the reference on [how Entra app registrations and reply URLs are structured](/2024/03/04/entra-app-registrations-explained/), which is the companion to keep open while you align a framework setting with a registered platform value.

## Confirming the registered list precisely, not by eye

Eyes round near-identical strings to equal, which is exactly why AADSTS50011 wastes time, so the confirming step should be mechanical. Read the registered values with a query that prints them verbatim, capture the requested value by decoding it from the request, and compare them with a tool rather than a glance. The command-line query returns the three platform collections, and piping it through a formatter makes hidden characters visible:

```bash
# Print each platform's registered values, one per line, exactly as stored
az ad app show --id <application-client-id> \
  --query "web.redirectUris" -o tsv
az ad app show --id <application-client-id> \
  --query "spa.redirectUris" -o tsv
az ad app show --id <application-client-id> \
  --query "publicClient.redirectUris" -o tsv
```

With the requested value decoded into a file and the registered values in another, a literal diff settles the question no human eye can settle quickly:

```bash
# requested.txt holds the decoded redirect_uri from the failing request
# registered.txt holds the platform list from the query above
diff <(printf '%s\n' "$(cat requested.txt)") registered.txt && echo "exact match found" || echo "no exact match; inspect the difference"
```

When you administer many applications or many environments, scripting the read turns a recurring investigation into a single command that lists every registered return address across the platforms, which is also how you audit for stale or unintended entries during the periodic review the prevention section recommends. The Graph API exposes the same data on the application object's `web`, `spa`, and `publicClient` properties, and reading through Graph is the more reliable path when a CLI version lacks a flag for a platform, since the property names on the object are stable even when the command surface around them shifts. Whichever interface you use, the principle holds: the registered list is data to be read precisely and compared literally, never a thing to approve from memory, because the entire failure is a difference small enough to survive a casual look.

### How do I compare the requested and registered values without missing a hidden character?

Decode the requested return address from the failing request, print the registered values verbatim with a command-line query, and run a literal diff between them rather than comparing visually. A diff exposes a trailing slash, a case difference, or an encoded character that the eye merges, and it ends the comparison in one step instead of several wrong guesses.

## Edge cases that present as AADSTS50011 but hide a different detail

A handful of situations produce the same error code while concealing a subtler cause, and recognizing them saves a second round of investigation. The first is double encoding. A misbehaving client or an intermediary occasionally encodes the return address twice, so a slash that should arrive as `%2F` arrives as `%252F`; Entra decodes once and compares a value that still contains an encoded sequence, which matches nothing. You catch this by decoding the requested parameter and noticing it does not fully decode to a clean address, and you fix it by correcting the client that double-encodes rather than by touching the registration.

The second is case. Hosts resolve case-insensitively because DNS does, but the path portion of a return address is safest treated as case-sensitive, so `/Signin-Oidc` and `/signin-oidc` should be assumed distinct and kept identical between the app and the registration; the dependable rule is to make the entire value byte-for-byte identical and never rely on any part being forgiving. The third is the loopback special case interacting with the platform bucket: a `http://localhost` value behaves leniently about TLS but still must live under the platform that matches the flow, so a loopback value placed under Web for a browser app fails even though localhost itself was accepted, which reads as a puzzling partial success.

### Why does my redirect look identical yet still fail?

Because a difference is hiding where the eye does not look: a double-encoded character that never fully decodes, a case difference in the path, a trailing slash trimmed by the tool you compared in, or the correct string sitting under the wrong platform. Decode and diff the value literally and check the platform bucket, and the invisible difference becomes visible.

A fourth edge case is the product boundary. Entra ID and the customer-identity product that shares much of the same surface handle return addresses with closely related but not identical rules, and a configuration copied from one into the other can carry an assumption that does not hold, so when an app spans both, confirm the rules against the specific product you are configuring rather than assuming they are interchangeable. A fifth is the brokered or platform-specific redirect on mobile, where the platform expects a return address of a particular shape registered under the public-client platform, and using a plain web-style address there produces a mismatch because the broker emits the platform-shaped value the registration does not hold. None of these change the exact-match rule; they change where the hidden difference lives, which is why the mechanical decode-and-diff step finds them when a visual check does not.

## A worked example, from failure to confirmed fix

Walk one concrete instance end to end so the procedure is muscle memory. A team ships a browser application to production at `https://portal.contoso.com`. Sign-in fails immediately with AADSTS50011. The on-call engineer resists the urge to open API permissions and instead reads the failing request: in the browser address bar at the moment of failure, the GET to the `authorize` endpoint carries `redirect_uri=https%3A%2F%2Fportal.contoso.com%2F`. Decoded, that is `https://portal.contoso.com/`, with a trailing slash. The engineer then prints the registered values and sees, under the Web platform, `https://portal.contoso.com` with no trailing slash, and nothing at all under the Single-page application platform. Two findings, both fatal: the trailing slash differs, and a browser app's return address is sitting under Web when the app runs the PKCE flow that is matched under the SPA platform.

The fix addresses both findings in one change. The engineer moves the value to the Single-page application platform and registers it with the exact form the app emits, trailing slash included, then clears the now-incorrect Web entry so the registration honestly reflects a browser app. Using Graph to be explicit about placement:

```http
PATCH https://graph.microsoft.com/v1.0/applications/{object-id}
Content-Type: application/json

{
  "spa": { "redirectUris": ["https://portal.contoso.com/"] },
  "web": { "redirectUris": [] }
}
```

The engineer reads the registration back, confirms the SPA list now holds exactly `https://portal.contoso.com/` and the Web list is empty, and retries the sign-in, which succeeds. The whole episode took minutes because the engineer read the rejected value out of the request, compared it literally against the registered list per platform, and found the two failing rows of the checklist rather than guessing. That is the entire method, and the worked example is just the method applied: extract the requested return address, compare it byte-for-byte within the correct platform, correct the one or two differences, and verify the registered value reads back as intended. The pattern generalizes to every cause in this guide, which is why the checklist that follows is enough to resolve nearly any instance you will meet.

## Why the exact-match rule exists, and why loosening it is the wrong instinct

It helps to understand why Entra is this strict, because the rationale tells you which fixes are safe and which quietly weaken your security. The registered return address is the anchor of the authorization code flow's defense against code theft. When Entra hands an authorization code back to the browser, that code is a bearer of the eventual token, so anyone who receives it at a place they control is most of the way to impersonating the user. By accepting a return address only if it was pre-registered, Entra guarantees the code lands at an endpoint the application owner declared in advance, closing the door on an attacker who crafts a sign-in link with a substituted `redirect_uri` pointing at their own server. The exactness of the comparison is not pedantry; a fuzzy match would let an attacker register a look-alike that a loose rule treats as equivalent, so the literal, character-level comparison is what makes the registered set a meaningful allowlist rather than a suggestion.

### Is it safe to just register every URL my app might use?

Register every address the application genuinely serves, and nothing more. Each registered return address is a place Entra will deliver an authorization code, so a speculative or unused entry is attack surface that buys you nothing. The right list is complete enough that real sign-ins succeed and minimal enough that no entry exists without a live path behind it.

This is why the prevention guidance keeps returning to a small, deliberate set. The temptation under deadline pressure is to widen the allowlist: register both slash forms, add the internal host the proxy uses, register a wildcard-like value, or keep every environment that ever existed. Each of those silences the error and erodes the protection at the same time. Registering an internal host means a code can be delivered to an internal endpoint that may be reachable by something you did not intend. Keeping a retired environment's address means a decommissioned host that someone else could later claim remains a valid token destination. The secure fix is always the precise one: make the application send the address you intend, and register that exact address under the correct platform, so the allowlist stays both correct and tight. The reason a public client additionally carries a PKCE challenge is the same defense in depth applied to the code itself, and the relationship between the registered return address, the code, and the proof key is part of why the modern interactive flow is built the way it is. Holding that security model makes the right repair feel natural rather than restrictive, because you are not fighting the rule, you are honoring the thing it protects.

## Diagnosing AADSTS50011 in automated, headless, and test flows

The error behaves differently in non-interactive contexts, and knowing that prevents a category of confusion. A flow that never uses a browser return address cannot produce a redirect mismatch, so the appearance of AADSTS50011 in such a context is itself a clue that the wrong flow is in use. A daemon or background service authenticating with the client credentials grant has no user, no browser, and no return address, so it should never see this error; if it does, the code path has fallen into an interactive flow by mistake, perhaps because a shared helper defaults to interactive sign-in, and the fix is to route the service through the credential-based grant rather than to register anything. Likewise, an input-constrained device using the device code flow obtains its tokens without a browser redirect on the device itself, so a redirect mismatch there indicates the app selected an interactive flow where the device flow was intended.

### Why does AADSTS50011 appear in my integration tests but not locally?

Usually because the test environment presents a different origin than your machine, so the return address the app builds in the test run is a host the registration never received. A continuous-integration runner, a containerized test host, or a headless browser pointed at a deployed preview each produces its own origin, and that origin needs its own registered return address exactly as any other environment does.

Automated browser tests are the common place this surfaces, because a headless browser driving a real interactive sign-in against a deployed test environment builds the return address from that environment's origin, and if the test environment was stood up without registering its address, every test that exercises sign-in fails with AADSTS50011 while local runs pass. Treat the test environment as a first-class environment: register its origin's return address under the correct platform when you provision it, ideally from the same automation that creates the environment, so the test target is registered the moment it exists. When tests run against ephemeral per-build environments, the registration has to be generated and applied per build, which is the strongest argument for managing the return-address list as code rather than by hand. The diagnostic step is unchanged from the interactive case: capture the value the test's browser sent to the `authorize` endpoint, decode it, and confirm whether the test environment's origin is present in the registered list. The novelty in automation is only that the failing origin is a machine's rather than a developer's, and that the fix belongs in the pipeline that builds the environment.

## A decision rule for which side to fix, the application or the registration

Every AADSTS50011 fix is a choice between two valid directions, and choosing the right one the first time avoids a wasteful second edit. The deciding question is which side currently holds the address you actually intend to use in production. If the application is sending the address your team means to standardize on, the long-lived public origin and the canonical callback path, then the application is right and the registration is stale, so you update the registration to hold that exact value. If the application is sending an address it should not, an internal host leaked through a proxy, a stray slash from a library default, a development port in a deployed build, then the application is wrong and editing the registration to accept its mistake would bake the mistake in, so you fix the application to send the intended address and make sure that intended address is registered.

The rule has a useful corollary for the proxy and internal-host cases specifically: never resolve a proxy-rewritten address by registering the internal host, because that direction trades a transient error for a standing security weakness. The address you want delivered to is the public one, so the fix belongs on the application side, teaching it to build from the forwarded public host. Applying the rule consistently keeps the registration as a faithful description of where tokens should legitimately land, rather than a record of every address the application has ever accidentally emitted. When both sides are arguably reasonable, for instance two clients that genuinely send different but valid forms, registering both is acceptable, but treat that as the rare exception that follows from a real requirement rather than the default reflex, and document why both forms exist so a later reviewer does not prune one and break a client. The throughline is that the registration should mean something: it is the set of return addresses you have deliberately chosen to trust, and the decision rule keeps every entry tied to an intention rather than to an accident.

## Sibling reply-address errors and how their codes differ from AADSTS50011

AADSTS50011 has close relatives that share the Authentication blade and the reply-address concept but mean distinct things, and reading the code precisely routes you to the right fix. The clearest sibling is the case where no reply address is registered at all, which carries its own code and language about the application having no reply address configured rather than about a mismatch; the distinction matters because the fix is to add a first return address rather than to reconcile a difference between two existing ones. If you read a message saying the application has no reply address, you do not hunt for a trailing slash, you register the address the application sends, because there is nothing yet to compare against.

### What is the difference between a redirect mismatch and a missing reply address?

A mismatch, AADSTS50011, means at least one return address is registered but none equals the requested one, so you reconcile the difference. A missing-reply-address error means none is registered at all, so you add the first one. The codes and wording differ, and so does the fix: align an existing value versus create the value that is absent.

Other neighbors turn on configuration toggles adjacent to the return address rather than on the address string. An older browser application that depended on implicit token issuance can fail in ways that look like a return-address problem but are really about whether the registration is configured to issue the token type the legacy flow expected, which is a switch on the same blade rather than an entry in the address list; the modern resolution is usually to move the app to the authorization code flow with PKCE and the SPA platform rather than to re-enable a deprecated issuance mode. The application-not-found family fails earlier, naming the application rather than the address, and points at identity rather than return location. The consent family fails on permissions and names consent, not a return address. The reliable habit across all of them is to read the error code and the noun the message centers on: when it is the redirect or reply URL and a mismatch, it is AADSTS50011 and the repair is the literal comparison this guide is built around; when the noun is anything else, the code is telling you to look at a different layer, and following the noun rather than the surrounding panic is what keeps these siblings from blurring into one long, misdirected investigation.

## Sign-out return addresses and the other places the same mismatch appears

The authorization return address is the famous one, but it is not the only pre-registered address Entra checks, and a mismatch on a sibling address produces a similar failure that engineers often misfile. When a user signs out, the application can ask Entra to return the browser to a post-logout location, and that post-logout address is its own registered value, separate from the sign-in return address. If the application sends a post-logout destination that was never registered, the sign-out leg fails or the user is left on a generic page, and the cause is the same exact-match discipline applied to a different field. The fix mirrors the sign-in case: read the post-logout value the application sends, register that exact value in the corresponding field of the registration, and confirm they agree. Treat sign-in and sign-out destinations as two lists that both deserve the canonicalize-and-register treatment, because an app that pins one and improvises the other will pass sign-in and stumble on sign-out in a way that looks mysterious until you realize a second address is in play.

### Does sign-out have its own registered address separate from sign-in?

Yes. The post-logout destination Entra returns the browser to after sign-out is a distinct registered value from the sign-in return address. Pin and register it with the same exactness, because a sign-in that works tells you nothing about whether the sign-out destination matches, and an unregistered post-logout address fails on its own terms.

Front-channel logout, where Entra notifies the application to clear its session, uses yet another configured location, and the same principle holds: it is a registered address subject to a literal comparison, so a difference between what is configured and what the application expects produces a logout that does not propagate cleanly. The broader point is that the registration is a small constellation of trusted addresses, the sign-in return address per platform, the post-logout destination, and any logout notification location, and AADSTS50011 specifically concerns the sign-in return address while its lookalikes concern the others. When a sign-in succeeds but a sign-out or session-clear step misbehaves, resist re-debugging the sign-in path and instead apply the identical decode-and-compare method to the relevant logout field, because the failure is the same shape on a different address and yields to the same fix.

## Confirming the fix held, and catching the next one from the sign-in logs

A registration edit can read back correctly and a sign-in can still fail on the next attempt for reasons that have nothing to do with whether you fixed the right thing, so the confirmation step deserves the same rigor as the diagnosis. After you change the registered value, read it back with the command-line query or through Graph and verify it equals the intended address byte-for-byte under the correct platform, which removes any doubt that the edit saved as typed. Then start a genuinely fresh sign-in rather than retrying a stale one: a client that still holds a pre-built authorization request will keep sending the old address, so clear the client's authentication state, hard-refresh a browser app, or restart the process before the retry. A clean retry that succeeds confirms the fix; a clean retry that still fails sends you back to decoding the request, because the registered value and the requested value still differ somewhere.

### How do I find every place AADSTS50011 is happening in my tenant?

The Entra sign-in logs record failed sign-ins with their error codes, so you can filter the logs for the code and see which applications, users, and timestamps are affected. That turns a single reported failure into a complete picture, revealing whether one environment, one application, or one host accounts for the failures and whether your fix actually drove the count to zero.

The sign-in logs are the instrument that turns a one-off fix into operational confidence. Entra records each sign-in attempt with the application, the user, the result, and the failure code, so filtering for the AADSTS50011 code shows you every occurrence across the tenant rather than only the one a user happened to report. That view answers questions a single failing request cannot: whether the failures cluster on one newly deployed environment, whether a particular application accounts for all of them, whether they began at a deployment boundary that implicates a moved port or a forgotten origin, and, after your change, whether the occurrence count actually falls to zero. Build the habit of confirming a fix not only by a successful manual sign-in but by watching the logged failure count drop, because a manual success proves your path works while the log proves every user's path works. For ongoing health, a periodic glance at the logs for this code surfaces a newly stood-up environment that nobody registered before its users hit it, closing the operational loop that the prevention habits open. Pairing the log filter with the periodic review of the registered address list gives you both directions of the same discipline: the registration tells you what you trust, and the logs tell you what is actually being requested and rejected, and reconciling the two keeps AADSTS50011 from quietly returning as the system grows.

## Registering return addresses as code, so a new environment never fails its first sign-in

The operational causes, an unregistered deployment, a forgotten staging slot, an ephemeral preview that fails its first sign-in, all share a root: the registered address list is maintained by hand while the environments it must cover are created by automation. The two drift because a human step sits between provisioning an origin and registering it, and that step gets skipped under deadline. Closing the gap means moving the registration into the same pipeline that creates the environment, so the origin and its registered return address come into being in one motion with no manual interval where someone could forget.

The shape of this is straightforward. The pipeline that provisions an environment already knows the origin it is creating, because it either assigns the host or reads it back from the platform after creation. Feed that origin, plus the canonical callback path the application uses, into a step that patches the application object's platform collection through the Graph API or the command line, adding the new environment's return address under the correct platform. For an ephemeral per-build environment, the same step adds the build's address on creation and a teardown step removes it on destruction, so the registered list tracks the set of live environments automatically and never accumulates dead entries. The automation authenticates as a principal with just enough permission to update the application's redirect collections, ideally a workload identity rather than a stored secret, which keeps the pipeline itself aligned with the least-privilege posture the registration is meant to embody.

### How do I keep redirect URIs in sync across many environments?

Generate and apply them from the pipeline that creates each environment, adding the origin's return address under the correct platform when the environment is provisioned and removing it on teardown. Managing the list as code means the registered set always reflects the live environments, which eliminates the forgotten-environment and stale-entry causes at the same time.

Two refinements make this durable. First, keep the callback path and the platform a single source of truth that both the application and the pipeline read, so the address the pipeline registers and the address the application sends are derived from the same configuration and cannot disagree; when both come from one declared value, the literal comparison Entra performs succeeds because the two sides were generated from identical inputs. Second, treat the registered list as something to reconcile, not only to append: a periodic job that reads the current registered addresses, compares them against the set of live environments, and flags entries with no corresponding environment turns the security review from a manual audit into an automated check. That reconciliation is where the two operational instruments meet, the address list that declares what you trust and the live inventory that says what actually exists, and keeping them equal by automation is the most complete prevention available. Teams that reach this state stop seeing AADSTS50011 as a recurring incident and start seeing it only when something genuinely novel happens, a new front end, a changed flow, a moved path, which is exactly when a human should be looking anyway. The error becomes a signal of real change rather than a tax on routine deployment, and the registration becomes a faithful, self-maintaining description of every place the application legitimately receives a token. You can practice building this loop end to end, provisioning an environment, registering its address from the same step, and watching a sign-in succeed without a manual edit, in a sandbox before you wire it into a real pipeline, which is the safest way to get the permissions and the patch shape right.

## The InsightCrunch redirect-URI checklist

Pull the causes into one artifact you can run top to bottom the next time AADSTS50011 appears. The checklist below names each part that must match, the platform rule, and the development-versus-production discipline, with the confirming action and the typical fix for each. This is the reference to bookmark; it turns the error from a guessing game into a five-minute pass.

| Check | What must be true | How to confirm | Typical fix |
|---|---|---|---|
| Scheme | Request and registration share `http` or `https` exactly | Decode `redirect_uri`, compare the first token | Send and register the same scheme; use `https` for non-loopback hosts |
| Host | The exact host in the request is registered | Compare host tokens; watch apex versus `www` and default versus custom domains | Register each legitimate host explicitly |
| Port | The port matches, with absent treated as its own value | Compare the port token; common dev-port drift between framework versions | Register the exact port the app sends |
| Path | The path matches character for character | Compare path tokens end to end | Align the app's callback path with the registered path |
| Trailing slash | A terminal slash is present or absent on both sides identically | End-align both strings; compare the final character | Make the app deterministic, register the canonical form |
| Platform bucket | The URI sits under the platform that matches the flow (Web, SPA, public client) | Query `web`, `spa`, `publicClient` lists separately | Move the URI to the correct platform, clear the wrong one |
| Environment coverage | Every environment's origin is registered | Read the received redirect per environment | Register each environment; manage the list as code where ephemeral |
| Forwarded host | The app builds the redirect from the external host, not the internal one | Inspect the received host for internal names or proxy-only ports | Honor `X-Forwarded-Host`/`Proto`; do not register internal hosts |

Run the rows in order and the cause reveals itself, because every AADSTS50011 reduces to one row failing. The first five rows are string comparisons you can settle in seconds with a decoded URI and the registered list side by side. The sixth is a bucket check the platform query answers directly. The last two are operational rather than typographical, and they are the ones that recur as a system grows, which is why prevention focuses there.

## Prevention: make the redirect URI list a small, deliberate, verified set

The fix for a single AADSTS50011 is a one-line registration edit. The prevention that stops it from returning is treating the redirect URI list as a managed asset rather than an accreting pile. Three habits do most of the work. First, canonicalize the redirect URI the application sends, so there is exactly one intended address per environment and the framework does not append or drop a slash or change a port on its own; pin the callback path and the base URL explicitly in configuration rather than relying on a library default that can move between versions. Second, register every environment's redirect at the moment the environment is created, ideally from the same infrastructure-as-code pipeline that provisions the environment, so a new origin and its registration entry come into existence together; this closes causes four and five permanently because there is no manual step left to forget. Third, keep the list minimal and reviewed, because every registered redirect is a place Entra will return a token, so an unused or speculative entry is attack surface with no benefit; periodically read the registered list back and remove what no production or active development path uses.

A short verification gate before any auth-touching deployment catches the rest. Read the redirect the application will send in the target environment, confirm it is registered under the correct platform, and confirm the platform matches the flow the app runs. For browser apps that means the SPA bucket and the PKCE flow agreeing; for server-side apps the Web bucket; for native or loopback redirects the public-client bucket. This is the same verify-the-named-condition posture the whole series uses for diagnosis, applied one step earlier so the condition never fails in production. You can rehearse the entire loop, registering an app, sending a redirect, watching a mismatch, and correcting it, in a sandbox without risking a real tenant; [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to register an app and reproduce the mismatch end to end, and [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) to practice reading the rejected redirect out of a failing request until it is reflexive. Both build the muscle that turns this error into a thirty-second fix.

## The related failures AADSTS50011 is often confused with

AADSTS50011 lives in a family of Entra sign-in errors, and half the wasted time on it comes from misreading it as one of its siblings. The most common confusion is with consent. A reader sees a failed sign-in, assumes the user or admin has not granted permission, and starts working the consent path; but consent errors carry their own codes and their own language about permissions and admin approval, not about a redirect URI. If the message names a redirect or reply URL, it is AADSTS50011 and consent is irrelevant; if it names a permission or consent, it is a different error with a different fix. The neighboring guide to resolving the consent-required failure separates that path cleanly, and reading the error code rather than the vibe of the page is what keeps the two apart.

The second confusion is with the application-not-found family, where Entra cannot resolve the client id to an application in the tenant at all. That failure happens earlier in the request than the redirect comparison, names the application rather than the redirect, and points at a wrong client id, a wrong tenant, or a missing service principal rather than a return address. If the error is about the application not being found, no amount of redirect URI editing helps. The third confusion is with reply-URL configuration errors that are really about the platform or the issuance toggles rather than the URI string, for instance an implicit-flow token issuance setting that an older SPA configuration depended on; these present near AADSTS50011 and are resolved on the same Authentication blade but turn on a different switch. The throughline is the same diagnostic habit: the error code and the noun it names tell you which layer failed, and AADSTS50011 always names the redirect URI, so the repair is always the redirect comparison and never the layers above or below it.

## Closing verdict

AADSTS50011 is the most honest error Entra throws, because it tells you the exact value it rejected and the exact application it checked against, and the entire fix is to make a registered redirect URI match that value, to the character, in the correct platform bucket. The reason it costs teams so much time is not that it is hard but that it looks like a permissions problem and invites the wrong investigation. Hold the exact-match rule, read the received redirect out of the error or the request, lay it beside the registered list, and find the one row of the checklist that fails: scheme, host, port, path, trailing slash, platform bucket, an unregistered environment, or a proxy-rewritten host. Then either correct the address the application sends or register the exact address under the right platform, and verify the value reads back as intended. Make the list deliberate, provision it with each environment, and gate deployments on a quick redirect check, and the error stops returning. Treat the redirect URI not as a string you paste once and forget but as a small, governed set of return addresses, and AADSTS50011 becomes a thirty-second confirmation rather than a lost afternoon.

## Frequently Asked Questions

### Q: What does the AADSTS50011 redirect URI mismatch error mean?

It means Microsoft Entra ID received an authorization request whose `redirect_uri` parameter does not match any redirect URI registered on the application's registration. Entra only returns authorization codes and tokens to pre-registered addresses, a protection against having tokens delivered to an attacker-controlled location, so when the requested return address is not on the registered list, Entra refuses the request before any consent or credential evaluation. The error names the value it received and the application it checked against, which is everything you need to fix it. The repair is to make a registered redirect URI match the requested one exactly, including scheme, host, port, path, and trailing slash, under the platform type that matches the application's sign-in flow. It is never a permissions or secret problem.

### Q: How do I add a redirect URI in the Entra app registration to fix AADSTS50011?

In the portal, open the app registration, go to the Authentication blade, find the platform section that matches your app type (Web, Single-page application, or Mobile and desktop applications), and add the exact redirect URI there. From the command line, use the platform-appropriate property: for a web app, `az ad app update --id <client-id> --web-redirect-uris "https://your.exact/callback"` replaces the web list, so include every web URI in one call. For a single-page app, set `spa.redirectUris`, and for native or loopback redirects, set `publicClient.redirectUris`, both most reliably through a Microsoft Graph PATCH to the application object since CLI flags for these platforms vary by version. After saving, read the value back and confirm it matches the requested URI character for character, then retry the sign-in once propagation completes.

### Q: Does a trailing slash cause AADSTS50011?

Yes, and it is the most frequent single cause. Entra compares the redirect URI as a literal string, and a terminal slash is part of the path, so `https://app.contoso.com/callback/` and `https://app.contoso.com/callback` are two different values that will not match each other. If your application sends one and the registration holds the other, you get AADSTS50011 with no other misconfiguration. The slash difference is easy to miss because many editors and chat tools trim trailing slashes on paste, hiding the very discrepancy you are hunting. Confirm it by decoding the requested `redirect_uri` and end-aligning it against the registered value to compare the final character. Fix it by making the application deterministic about which form it sends and registering that exact canonical form, rather than registering both variants, which masks the underlying inconsistency.

### Q: Why does AADSTS50011 happen on localhost during development?

Localhost redirects have their own rules and their own pitfalls. A `http://localhost` value is treated leniently enough to work without TLS, which is convenient locally, but the port is part of the match, so `https://localhost:5001` and `https://localhost:3000` are distinct, and a registered `https://localhost` with no port matches neither. When a framework changes its default development port between versions, an app that signed in last month can fail today purely because the requested port moved while the registration did not. Loopback redirects also belong in the public-client bucket for native apps or the SPA bucket for browser apps, not the Web bucket, so a localhost URI in the wrong platform fails even with the right string. Confirm by decoding the requested redirect and comparing the full `scheme://host:port/path` against the registered loopback value, then align the port and platform.

### Q: Does the platform type, SPA versus Web, affect AADSTS50011?

Decisively. Entra matches a redirect URI only within the platform bucket that fits the flow the request uses. A single-page application running the authorization code flow with PKCE must have its redirect under the Single-page application platform; the identical string registered under Web will not satisfy the SPA request, and Entra reports it as a redirect mismatch. The reverse happens too, a server-side app whose redirect drifted into the SPA bucket. This is the cause where the string looks perfectly correct in the portal yet sign-in still fails, because the portal shows the URI present under the wrong platform. Confirm by querying the `web`, `spa`, and `publicClient` redirect lists separately and checking which bucket holds the value against which flow your app actually runs. Fix it by moving the URI to the correct platform and clearing it from the wrong one.

### Q: Can a reverse proxy or load balancer cause AADSTS50011?

Yes, and it is the most deceptive version of the error because the application code and the registration both look correct in isolation. When a proxy, ingress controller, Application Gateway, or load balancer terminates the external request at a public host and forwards it to the application on an internal host, the application may build its redirect URI from the internal host it sees rather than the public host the user arrived on. The resulting redirect carries an internal address that was never registered, so Entra rejects it. Confirm by decoding the requested `redirect_uri` and inspecting the host: an internal service name, a private address, a pod host, or a proxy-only port reveals the rewrite. Fix it on the application side by honoring the standard forwarding headers, `X-Forwarded-Host` and `X-Forwarded-Proto`, with the framework configured to trust the proxy, so the app reconstructs the external URL. Do not register the internal host.

### Q: How do I find the exact redirect URI that Entra received?

Three methods, at least one always available. First, a recent error page prints the received value inline, often in single quotes alongside the application id, so read it there. Second, capture it from the request: the sign-in is a GET to the `authorize` endpoint, so the failing request's URL in the browser address bar or a network trace contains the `redirect_uri` query parameter, URL-encoded. Copy that parameter and decode it, because differences frequently hide inside the encoding, where `%2F` is a slash and `%3A` is a colon. Third, in the browser developer tools, enable preserve log, reproduce the failure, and find the request to `login.microsoftonline.com` ending in `/oauth2/v2.0/authorize`; its query string holds the same value. Whichever method you use, the decoded value is the ground truth you compare against the registered list, and it ends the guessing immediately.

### Q: I granted admin consent and AADSTS50011 still appears. Why?

Because AADSTS50011 is not a consent error and is evaluated before consent. Entra checks whether the requested redirect URI is registered as a very early step, independent of whether any user or admin has approved the application's permissions. Granting admin consent, adding API permissions, or rotating a client secret changes the consent and credential layers, none of which touches the redirect comparison, so the error survives every one of those actions unchanged. If the message names a redirect or reply URL, the fix lives entirely in matching that URL against a registered value under the correct platform, and consent is a separate concern with its own error codes. The quickest way to stop chasing the wrong layer is to read the error code and the noun it names: a redirect URI in the message means the redirect comparison failed, full stop.

### Q: What is the difference between AADSTS50011 and AADSTS700016?

They fail at different stages and name different things. AADSTS700016 means Entra could not find the application identified by the client id in the directory at all, which happens before any redirect check; its causes are a wrong or mistyped client id, authenticating against the wrong tenant, a multitenant app missing a service principal in the resource tenant, or the wrong authority endpoint. AADSTS50011 means the application was found but the redirect URI in the request is not registered on it. If the message talks about the application not being found, editing redirect URIs accomplishes nothing, because the request never reached the redirect comparison. If the message talks about the redirect or reply URL, the application resolved fine and the fix is the redirect match. Reading which noun the error names, application versus redirect URI, routes you to the right repair instantly.

### Q: Do I need to register every environment's redirect URI separately?

Yes. The redirect URI is derived from the origin the application runs on, and each environment, development, staging, QA, preview, production, and each region or custom domain, presents a different origin, so each needs its own registered redirect URI under the correct platform. Registering production says nothing about staging, and a deployment slot or ephemeral preview environment generates a host that may not even exist until the environment is created. The durable approach is to manage the redirect list as code, generating and applying each environment's redirect from the same pipeline that provisions the environment, so a new origin and its registration entry are created together. That eliminates the recurring gap where a freshly stood-up environment fails its first sign-in purely because nobody added its address to the registration by hand.

### Q: Can I use a wildcard in an Entra redirect URI?

Treat redirect URIs as exact values, not patterns. Entra's redirect matching is built around registering specific, absolute URIs and comparing literally, and the platform deliberately constrains the use of wildcards because a permissive return address weakens the protection redirect registration exists to provide. Relying on wildcard-style matching is fragile, varies by scenario, and is the wrong instinct for production, where every place a token can be returned should be a deliberate, known address. For environments that multiply, the right answer is not a wildcard but automation: generate the explicit redirect list from your infrastructure pipeline so each real origin is registered as a concrete value. If you find yourself wanting a wildcard to cover ephemeral hosts, that is the signal to manage the registration as code rather than to loosen the match, keeping the registered set both complete and minimal.

### Q: Why does my redirect URI work for one user but fail for another?

If the application reaches users through more than one host, different users can arrive on different origins, and each origin produces a different redirect URI. A user who reaches the app on the apex domain sends a redirect for the apex host, while a user on the `www` subdomain sends one for that host, and only the registered hosts will match. The same happens across a default `azurewebsites.net` host and a mapped custom domain, or across regional endpoints. It is rarely about the user and almost always about which host their path resolved to. Confirm by decoding the requested redirect for each case and comparing the host token; the failing one carries an unregistered host. Fix it by registering every legitimate host the application can be reached through, keeping that set intentional rather than registering hosts the app does not actually serve.

### Q: How long does it take for a redirect URI change to take effect?

A registration edit generally applies quickly, but propagation is not guaranteed to be instantaneous across Entra, so a sign-in retried within seconds of the change can occasionally still hit the old state. If your first retry after editing the registration still fails, read the registered value back to confirm the edit saved exactly as intended, then wait briefly and retry before concluding the redirect URI was not the cause. Most of the time the change is effective almost immediately. When a retry keeps failing after the registered value clearly matches the requested one, the more likely explanation is a cached or pre-built authorization request on the client side that still carries the old redirect, so clear the client's auth state or start a fresh sign-in rather than assuming slow propagation. Confirming the registered value with a direct query removes the ambiguity.

### Q: Should I register both the trailing-slash and non-slash versions of my redirect URI?

You can, and occasionally it is justified, but it usually treats the symptom rather than the cause. Registering both variants masks the real problem, which is that the application is not deterministic about which address it sends, and that nondeterminism tends to spread across environments and recur. The cleaner fix is to make the application send exactly one canonical redirect URI per environment by pinning the base URL and callback path in configuration rather than relying on a framework default that can change, then register that single canonical form. Reserve registering both forms for genuine cases where two distinct clients legitimately send different forms and you cannot change either. As a general habit, keep the redirect list minimal and intentional, since every registered value is a place Entra will return a token, and redundant entries are attack surface without benefit.

### Q: My app uses http and Entra rejects the redirect URI. What is happening?

Two things can be in play. First, scheme is part of the literal match, so an `http` request against an `https` registration is a plain mismatch regardless of anything else. Second, and increasingly, Entra restricts `http` for non-loopback hosts and will not even let you register a plain `http` redirect for a real domain, because returning tokens over an unencrypted channel is a security exposure. Loopback addresses like `http://localhost` are the deliberate exception and are accepted for local development. So if your deployed app serves over `http` and expects to receive a redirect, the answer is not to register the `http` form but to serve the app over `https` and register the `https` redirect. Confirm by decoding the requested redirect and checking the scheme token, then align both the application's served scheme and the registered value on `https` for any host that is not localhost.

### Q: How do I prevent AADSTS50011 from happening again across my environments?

Three habits prevent nearly all recurrences. Canonicalize the redirect the application sends so there is one intended address per environment, pinning the base URL and callback path explicitly rather than trusting a library default that can shift between versions and introduce a stray slash or port. Register every environment's redirect at the moment the environment is provisioned, ideally from the same infrastructure-as-code pipeline, so a new origin and its registration entry are created together and no manual step is left to forget. Keep the registered list minimal and periodically reviewed, removing entries no active path uses, because every redirect is a place a token can be returned. Then gate auth-touching deployments on a quick check that the redirect the app will send is registered under the platform matching its flow. Together these close the typographical causes and the operational ones, turning the error from a recurring surprise into a verified precondition.

### Q: How do I capture the failing redirect URI from a mobile or native app?

A native app does not expose a browser address bar, so capture the value where the request is built or where it travels. Many identity libraries log the full authorization request at a verbose log level, which prints the return address the library assembled; enable that logging in a debug build and read the value directly. Alternatively, run the app through an HTTPS-inspecting debugging proxy on your development machine and find the request to the `authorize` endpoint, whose query string holds the parameter. For a brokered or platform-specific redirect, the value has the shape the platform broker expects rather than a plain web address, and it must be registered under the public-client platform exactly as the broker emits it. Once you hold the assembled value, the comparison against the registered public-client list is identical to the browser case: decode if encoded, diff literally, and align the platform.

### Q: Does the order of redirect URIs in the registration matter?

No. Entra checks whether the requested value matches any entry in the appropriate platform's list, so order has no effect on whether a match is found. What matters is that the exact value exists somewhere in the correct platform collection. Order can matter for human readability when you audit the list, so keeping it tidy helps the periodic review where you remove stale entries, but it never influences the match itself. If you are tempted to reorder entries hoping to change behavior, that instinct points at the wrong cause; the real question is always whether the precise requested value is present under the right platform, not where in the list it sits. Confirm presence with a literal comparison rather than rearranging, and spend the effort on making the requested value deterministic instead.

### Q: Can AADSTS50011 be caused by a stale browser or token cache?

Indirectly, yes. The error itself is always a present mismatch at the moment of the request, but a stale client can keep sending an old return address after you have fixed the registration, so the symptom appears to survive a correct fix. This happens when the client has a cached or pre-built authorization request carrying the previous value, or when a service worker or single-page app holds an older configuration in memory. After you confirm the registered value matches the intended one, clear the client's authentication state, hard-refresh a browser app, or restart the process, then start a fresh sign-in so the client assembles a new request with the current return address. If a clean client still fails, the registration genuinely does not match and you return to decoding and diffing; if a clean client succeeds, the earlier failures were the stale request, not a registration problem.
