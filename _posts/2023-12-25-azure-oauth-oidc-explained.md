---
layout: post
title: "OAuth 2.0 and OIDC in Azure Explained"
page_title: "OAuth 2.0 and OIDC in Azure Explained: Grant Flows, PKCE, Scopes, Claims, and Tokens for Microsoft Entra ID Apps"
date: 2023-12-25
categories: ["Technology"]
tags: ["Azure", "OAuth 2.0", "OpenID Connect", "Microsoft Entra ID", "Identity", "Security"]
excerpt: "OAuth 2.0 and OIDC in Azure decide how apps prove identity and obtain tokens. Learn the grant flows, PKCE, scopes, claims, and refresh tokens to choose right."
image: "/assets/images/blog/blog-08.webp"
reading_time: 62
author: "ian-fletcher"
last_updated: 2023-12-25
lang: en
---
The single most expensive identity mistake in Azure is copying an OAuth flow from a sample without knowing which flow you copied. OAuth 2.0 and OIDC are not interchangeable libraries you bolt on at the end. They are the contract that decides how every app, script, and service in Microsoft Entra ID proves who it is and what it is allowed to touch. Pick the wrong grant flow and you do not get an error at design time. You get a token that works in the demo, leaks in production, and fails the security review six months later when an auditor asks why a single-page app is holding a long-lived secret it was never supposed to have.

That gap between using these protocols and understanding them is where the damage lives. An engineer who pastes the implicit flow into a browser app ships an access token through a URL fragment that ends up in browser history and server logs. An engineer who reaches for the client credentials flow to act on behalf of a signed-in user builds an app that cannot tell users apart and quietly runs every request with full application privilege. Both apps authenticate. Both return a 200. Neither is correct, and the protocol gave no warning because OAuth 2.0 is deliberately a framework of choices rather than a single prescribed path.

![OAuth 2.0 and OIDC in Azure explained](/assets/images/blog/blog-08.webp)

This article fixes that by treating flow selection as a decision you can reason about rather than a snippet you inherit. By the end you will hold a working model of OAuth 2.0 as the authorization layer and OpenID Connect as the identity layer built on top of it, know the four grant flows that matter in Entra ID and the exact app shape each one serves, understand why authorization code with PKCE is the modern interactive default and why implicit is deprecated, and be able to read an access token, an ID token, and a refresh token well enough to debug a rejection. The throughline is a single rule that the rest of the article defends and applies: the right flow follows from the type of client, so choosing a flow is an act of reasoning about your app, not an act of copying someone else's.

## What OAuth 2.0 and OIDC actually are in Azure

OAuth 2.0 solves one narrow problem: how does an application get permission to call an API on behalf of a user or on its own behalf, without the application ever holding the user's password? That is authorization, and only authorization. OAuth 2.0 was never designed to tell an application who the user is. It was designed to hand an application a token that says "the bearer of this token may perform these actions against this resource until this time." Nothing in that sentence identifies a person. It identifies a permission.

OpenID Connect, almost always written OIDC, is the identity layer that the industry added on top of OAuth 2.0 once it became clear that everyone was abusing OAuth for sign-in and doing it inconsistently. OIDC standardizes the missing piece. It keeps the OAuth authorization machinery intact and adds a second token, the ID token, whose entire job is to describe the authenticated user in a verifiable, signed format. When you sign in to an Azure-backed web app with your work account, you are running an OIDC flow: OAuth 2.0 moves underneath to authorize the app against Microsoft Graph or your own API, and OIDC rides on top to prove to the app that you are the person who signed in.

Microsoft Entra ID, the identity service formerly branded Azure Active Directory, implements both protocols as the authority. Entra ID is the thing that authenticates the user, runs the consent step, issues the tokens, signs them with keys it publishes, and exposes the standard OAuth and OIDC endpoints your app talks to. Every app registration you create in Entra ID is, at bottom, a declaration of how that app participates in these two protocols: which redirect addresses it trusts, which credentials it holds, which permissions it requests, and which flows it is allowed to run. For the registration side of that story, the companion deep dive on [Entra app registrations](/2024/03/04/entra-app-registrations-explained/) walks through the application object in detail, and the broader [Microsoft Entra ID](/2022/02/21/microsoft-entra-id-explained/) overview places the identity model in context.

### Why does OIDC exist if OAuth already issues tokens?

OAuth 2.0 issues access tokens for calling APIs, but an access token is opaque to the client and says nothing reliable about the user. OIDC adds the ID token, a signed JSON Web Token the client can validate and read, so the app learns who signed in. OAuth authorizes; OIDC authenticates. You almost always need both.

The practical consequence of this split is that the two tokens have different audiences and different rules. The access token is meant for a resource API, which validates and consumes it; the client app is not supposed to crack it open and trust its contents. The ID token is meant for the client app itself, which validates the signature and reads the claims to establish a session. Engineers who blur this line write apps that make authorization decisions from the wrong token, and that confusion is one of the most common root causes behind a flow that behaves strangely in production. The deeper treatment of how Entra wires these protocols into its own sign-in machinery lives in the [Entra ID authentication](/2023/12/18/entra-id-authentication-explained/) deep dive, which this article complements by staying at the protocol layer.

## The InsightCrunch flow decision table

The findable artifact this article is built around is a decision table that maps the shape of your client to the grant flow it should run. The table is the whole argument compressed into one place. If you remember nothing else, remember that the left column is a property of your application that you already know before you write a line of auth code, and the right column follows from it deterministically.

| App type | Correct grant flow | Why this flow, in one line |
| --- | --- | --- |
| Interactive web app with a backend (confidential client) | Authorization code with PKCE | The backend can keep a secret, the code goes through the browser, PKCE binds the code to the original client |
| Single-page app running only in the browser (public client) | Authorization code with PKCE | No place to store a secret, so PKCE replaces the secret and stops code interception |
| Native or mobile app on a device (public client) | Authorization code with PKCE | Same as a SPA: a public client that cannot hold a secret relies on PKCE |
| Daemon, background service, or cron job with no user | Client credentials | There is no user to authenticate, so the app authenticates as itself with its own credential |
| CLI or device with no browser or constrained input | Device code | The user authorizes on a second device with a browser, the constrained device polls for the result |
| App calling a downstream API as the signed-in user | On-behalf-of | A middle-tier API exchanges the user's token for a new token to call a further API as that same user |

Every row is justified later in the article with the protocol detail behind it, but the table earns its place as the thing you reach for first. When a colleague asks which flow their new service should use, you do not start by opening the protocol spec. You ask what kind of client they are building, find the row, and only then drop into the mechanics. This is the difference between an engineer who reasons and one who searches for a snippet that happens to compile.

### How do I read this table in practice?

Identify your client first. Ask three questions: is there a human in the loop at sign-in, can your code keep a secret away from the user, and does your client have a browser. The answers place you in exactly one row. A browser-only app cannot keep a secret, so it lands on authorization code with PKCE rather than anything secret-based.

## The flow-matches-the-app rule

Here is the namable claim this article exists to establish. Call it the flow-matches-the-app rule: the correct OAuth flow is a function of the client type, not a matter of preference or convenience, so selecting a flow is reasoning about the properties of your application rather than copying a sample that happened to target a different kind of app.

The rule sounds obvious stated plainly, and yet nearly every serious OAuth defect in Azure traces back to violating it. The implicit flow lingered in countless single-page apps for years because the official samples used it and nobody re-derived whether it still fit. The client credentials flow shows up inside user-facing web apps because a developer needed to call Graph, found a working code snippet, and never noticed that the snippet authenticated as the app rather than as the user. In both cases the engineer skipped the one question that the rule forces: what kind of client am I, and what does that imply.

The rule also explains why the same flow appears in three different rows of the decision table. A confidential web app, a single-page app, and a native mobile app all run authorization code with PKCE, even though they differ in almost every other respect, because they share the one property that determines the flow: the user is present and interactive at sign-in. PKCE adapts to whether a secret is available, but the spine of the flow is fixed by the presence of an interactive user. Once you internalize that the client's properties drive everything, the protocol stops looking like a confusing menu of options and starts looking like a short decision tree with a defensible answer at each leaf.

### Does the flow ever depend on the API I am calling?

Rarely. The flow is fixed by your client, not by the resource. The same web app uses authorization code with PKCE whether it calls Microsoft Graph, your own API, or a partner API. The resource changes which scopes you request and which audience the access token carries, but it does not change the grant flow your client type demands.

## The grant flows, one decision at a time

A grant flow is the choreography by which an app obtains a token. OAuth 2.0 defines several, Entra ID supports the ones that matter, and the differences between them are not stylistic. Each flow exists to serve a client shape that the others cannot serve safely. Working through them in the order that the decision table implies makes the boundaries clear.

### How does the authorization code flow with PKCE work?

The browser sends the user to Entra ID with a hashed code challenge. The user signs in and consents, and Entra ID returns a short-lived authorization code to the app's redirect address. The app then posts that code plus the original code verifier to the token endpoint, and Entra ID returns the tokens only if the verifier matches the challenge.

That paragraph is the snippet-sized answer, but the flow rewards a slower walk because it is the one you will use most. The flow has two legs. In the first leg, the app builds an authorization request and redirects the browser to the Entra ID authorize endpoint. The request carries the client identifier, the redirect address Entra ID will send the response back to, the scopes the app wants, a response type of `code`, and two values that make PKCE work: a `code_challenge` and the method used to produce it. Proof Key for Code Exchange, which PKCE expands to, is the mechanism that lets a client without a secret prove that the entity redeeming the code is the same entity that started the flow.

The app generates a random secret called the code verifier, hashes it with SHA-256, and sends the hash as the code challenge in the first leg. It keeps the verifier in memory. When Entra ID returns the authorization code to the redirect address, an attacker who intercepts that code cannot use it, because redeeming the code in the second leg requires presenting the original verifier, which the attacker never saw. Entra ID hashes the presented verifier and compares it to the challenge it stored. A mismatch means the code is rejected. This is why PKCE is mandatory for public clients and recommended for every interactive flow including confidential ones.

```bash
# Inspect the authorize request your app should be building.
# response_type=code triggers the authorization code flow.
# code_challenge and code_challenge_method=S256 enable PKCE.

https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/authorize?
  client_id={app-client-id}
  &response_type=code
  &redirect_uri=https%3A%2F%2Fapp.example.com%2Fcallback
  &response_mode=query
  &scope=openid%20profile%20https%3A%2F%2Fgraph.microsoft.com%2FUser.Read
  &state={opaque-state}
  &code_challenge={base64url-sha256-of-verifier}
  &code_challenge_method=S256
```

In the second leg, the app exchanges the code at the token endpoint. A confidential client also sends its client secret or certificate here, because it can keep one. A public client sends only the code, the verifier, and its client identifier, because it has no secret to send. Entra ID validates the code, validates the PKCE verifier, validates the client credential if one was sent, and returns an access token, an ID token if `openid` was among the scopes, and usually a refresh token. The presence of the `openid` scope is exactly what turns a bare OAuth authorization into an OIDC sign-in, which is why interactive apps almost always request it.

```bash
# Second leg: redeem the code for tokens.
# A public client (SPA, native) omits client_secret and relies on PKCE.
# A confidential client (web app with backend) also sends a secret or assertion.

POST https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id={app-client-id}
&grant_type=authorization_code
&code={authorization-code-from-first-leg}
&redirect_uri=https%3A%2F%2Fapp.example.com%2Fcallback
&code_verifier={original-plaintext-verifier}
&scope=openid%20profile%20https%3A%2F%2Fgraph.microsoft.com%2FUser.Read
```

The reason this flow dominates the interactive rows of the decision table is that it never exposes a long-lived credential to the browser and never puts the access token in a place the browser will log. The code that travels through the redirect is single use and short lived, and PKCE renders it useless to anyone who steals it in transit. That combination is what the deprecated implicit flow could not offer.

### When do I use the client credentials flow?

Use client credentials when there is no user at all. A nightly job, a webhook receiver, a service that syncs data between systems: these authenticate as themselves using their own secret or certificate, request a token for the resource, and call the API with application permission. No browser, no consent prompt at runtime, no user identity in the token.

The client credentials flow is the simplest of the grant flows because it removes the user entirely. The app presents its own credential to the token endpoint, names the resource it wants a token for, and receives an access token scoped to the app's application permissions. There is no authorization code, no redirect, and no ID token, because there is no user to identify. The token's subject is the app's service principal, not a person.

```bash
# Client credentials: the app authenticates as itself.
# Note grant_type=client_credentials and the .default scope.

POST https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id={app-client-id}
&grant_type=client_credentials
&client_secret={app-secret}
&scope=https%3A%2F%2Fgraph.microsoft.com%2F.default
```

The `.default` scope is the tell that you are in an application-permission flow. Rather than requesting individual delegated scopes, the app asks for whatever application permissions an administrator has already granted it on that resource, expressed as the resource's `.default` scope. This is deliberate. Application permissions are high trust, because they are not bounded by what any single user can do, so they are granted once by an administrator and then consumed wholesale through `.default`. Treating client credentials casually is dangerous precisely because the resulting token often carries broad, tenant-wide reach. A certificate is strongly preferred over a client secret for production daemons because a certificate is harder to exfiltrate and easier to rotate cleanly.

### How does the device code flow handle a CLI or a TV?

The device code flow exists for clients that either lack a browser or cannot accept a redirect, such as a command-line tool, a smart TV, or an IoT device. The device asks Entra ID for a code, shows the user a short code and a URL, and the user opens that URL on a phone or laptop to sign in and approve. Meanwhile the device polls the token endpoint until the user finishes.

The choreography is a clever workaround for the input problem. The device cannot pop a browser, so it offloads the interactive part to a device that can. Entra ID returns a device code, a user code, a verification URL, and a polling interval. The device displays the user code and the URL, then begins polling the token endpoint with the device code. On the second device the user enters the code, signs in, and consents. Once that completes, the next poll from the original device returns the tokens.

```bash
# Step 1: the device requests a device code.
POST https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/devicecode
Content-Type: application/x-www-form-urlencoded

client_id={app-client-id}
&scope=openid%20profile%20https%3A%2F%2Fgraph.microsoft.com%2FUser.Read

# Step 2: the device polls the token endpoint until the user finishes.
POST https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:device_code
&client_id={app-client-id}
&device_code={device-code-from-step-1}
```

The Azure CLI itself can run this flow when you sign in from a machine without a browser, which is the everyday example most engineers have already used without naming it. The flow keeps the user interactive and present, so what it issues is a delegated user token, not an application token. That is the key contrast with client credentials: device code still authenticates a person, it just relocates where the person does the authenticating.

### What is the on-behalf-of flow for?

The on-behalf-of flow lets a middle-tier API call a further downstream API as the original user. A web API receives an access token from a client, then exchanges that token at the token endpoint for a new access token scoped to a downstream resource, preserving the user's identity through the chain so the downstream API sees the real user rather than the middle service.

This flow matters in layered architectures where a front-end calls an API that must call another API. Without on-behalf-of, the middle API would either call downstream as itself, losing the user context, or it would forward the original token, which fails because that token's audience is the middle API and not the downstream one. On-behalf-of solves the audience problem cleanly: the middle tier proves it received a valid token for itself, asks for a token aimed at the downstream resource, and Entra ID issues one that still names the original user as the subject. The result is end-to-end delegation where every hop knows who the human is.

### Why is the implicit flow deprecated?

The implicit flow returned tokens directly in the URL fragment of the redirect, with no second leg and no code exchange. That put access tokens in browser history, server logs, and referrer headers, and it offered no way to deliver a refresh token safely. Authorization code with PKCE replaces it everywhere, giving browser apps a secure path that implicit never could.

The implicit flow was a compromise from an era when browsers could not make cross-origin calls to the token endpoint, so the only way to get a token into a single-page app was to return it directly in the redirect. Cross-origin resource sharing changed that, and once a SPA could call the token endpoint directly, the entire reason for implicit evaporated. What remained were its costs: tokens exposed in the address bar, no refresh tokens, and a larger attack surface. Microsoft and the wider standards community now direct every interactive client, including single-page apps, to authorization code with PKCE. If you find an app still running implicit, treat it as technical debt with a security dimension, not as a working pattern that happens to be old.

## Scopes and claims: what the token is allowed to do and what it says

Once you have chosen a flow, the next two concepts decide what the resulting token actually permits and what it actually asserts. Scopes govern permission. Claims govern assertion. Engineers conflate them constantly, and the confusion produces a specific, recognizable failure: a token that authenticates fine but is rejected by the API because it lacks the scope the API demands.

A scope is a named permission that a client requests and a resource defines. When a web app asks for `User.Read` against Microsoft Graph, it is requesting the scope that lets it read the signed-in user's profile. The resource, Graph in this case, publishes the set of scopes it understands. The client requests the subset it needs. Entra ID, through the consent process, decides whether to grant them. The access token that comes back carries the granted scopes in its `scp` claim for delegated permissions or its `roles` claim for application permissions, and the resource reads that claim to authorize the call. If the scope the API requires is absent from the token, the API returns a 403, and the fix is to request the right scope at the client and ensure consent was granted, not to retry or to widen the flow.

### What is the difference between a scope and a claim?

A scope is a permission the client requests and the resource enforces, like `Mail.Read`. A claim is a statement of fact inside a token, like the user's object identifier, tenant, name, or the scopes that were granted. Scopes shape what the token can do; claims describe the token's subject and context. The resource reads claims, including the scope claim, to make its decision.

Claims are the key-value statements packed into a token. The ID token carries identity claims: the subject identifier, the issuer, the audience, the user's name and preferred username, the tenant identifier, and timing claims that bound the token's validity. The access token carries authorization claims: the audience that names the intended resource, the scope or roles that name the permissions, the app identifier, and again the timing and issuer claims that let the resource validate it. When you debug an OAuth problem in Azure, you are almost always reading claims. A token rejected for the wrong audience, a sign-in that lands the user in the wrong tenant, an API that cannot find the user's object identifier: each of these is a claim you can inspect directly.

The compound terms here matter and should not be flattened. A delegated permission is not the same as an application permission, and the scope claim is not the same as the roles claim. Delegated permissions appear when a user is present and the app acts on the user's behalf, bounded by what that user can do. Application permissions appear in the client credentials flow when the app acts as itself, bounded only by what an administrator granted. Reading which claim carries the permission tells you immediately which kind of flow produced the token, which is often the fastest way to confirm that an app is running the flow you intended rather than the one a snippet gave it.

### How do consent and permissions fit together?

Consent is the step where a user or an administrator agrees to let an app hold the permissions it requested. Delegated permissions can be consented by the user for themselves, or by an administrator for everyone, depending on the permission's sensitivity. Application permissions always require administrator consent, because they are not bounded by any single user.

The consent step is where many real-world flows visibly succeed or fail, so it deserves a concrete model. The first time a user signs in to an app that requests delegated permissions, Entra ID presents a consent prompt listing what the app wants. If the user agrees, Entra ID records the grant and skips the prompt on future sign-ins. Some permissions are sensitive enough that only an administrator may consent, and others require administrator consent for the whole tenant rather than per user. When a sign-in fails with a consent-required error, the flow itself is correct; the missing piece is the grant. The fix is to request consent, often through an administrator, rather than to change the grant flow. The mechanics of declaring and requesting these permissions live in the [Entra app registrations](/2024/03/04/entra-app-registrations-explained/) deep dive, which pairs naturally with this protocol view.

## Access tokens, ID tokens, and refresh tokens

Three token types do three different jobs, and using one where another belongs is among the most common sources of subtle bugs. Hold the distinctions firmly, because almost every confusing OAuth symptom resolves once you know which token you are actually looking at.

### What is the difference between an access token and an ID token?

The access token authorizes a call to a resource API and is meant for that API to validate and consume. The ID token authenticates the user to the client app and is meant for the client to validate and read. The client should never make authorization decisions from an access token's contents, and a resource should never accept an ID token as proof of permission.

The access token is the workhorse of OAuth. It is a string the client attaches to API calls, usually in an HTTP Authorization header as a bearer token. In Entra ID it is a JSON Web Token, signed by the issuer, carrying an audience claim that names the resource it is valid for, a scope or roles claim that names the permitted actions, and an expiry. The resource validates the signature against Entra ID's published keys, checks that the audience names itself, confirms the issuer and the expiry, and only then trusts the scope claim to authorize the action. A resource that skips audience validation will accept tokens minted for a different resource, which is a serious flaw.

The ID token is the OIDC addition and exists only to tell the client who signed in. It too is a signed JWT, but its audience is the client application, and the client validates and reads it to establish a local session. The crucial discipline is that the ID token is for the client and the access token is for the resource. A web app that sends its ID token to an API as if it were an access token will be rejected, because the API is not the ID token's audience. A client that reads an access token to learn the user's name is reaching into a string it was never meant to parse, and Entra ID does not even guarantee that an access token is readable, since for some resources it is an opaque string by design.

### How do refresh tokens work?

A refresh token lets a client obtain a new access token after the current one expires, without making the user sign in again. The client posts the refresh token to the token endpoint and receives a fresh access token and usually a new refresh token. Refresh tokens are long lived but revocable, and they are issued only to flows that can hold them with reasonable safety.

Refresh tokens are what make a signed-in session feel persistent without sacrificing the short lifetime of access tokens. Access tokens are deliberately short lived, often around an hour, so that a stolen one expires quickly. The refresh token, which lives much longer, sits with the client and is exchanged for new access tokens silently as they expire. This is why a user can stay signed in to a web app all day after one sign-in: the access token keeps expiring and the refresh token keeps renewing it behind the scenes.

```bash
# Use a refresh token to get a new access token with no user interaction.
POST https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id={app-client-id}
&grant_type=refresh_token
&refresh_token={refresh-token}
&scope=openid%20profile%20https%3A%2F%2Fgraph.microsoft.com%2FUser.Read
```

Two properties of refresh tokens shape how you handle them. First, they are sensitive, so where the client can store one safely matters. A confidential web app keeps its refresh token on the server, well away from the browser. A single-page app, which has no safe storage, receives refresh tokens with tighter constraints and shorter lifetimes, and modern guidance leans on the authorization code flow with PKCE plus careful storage rather than long-lived refresh tokens in the browser. Second, refresh tokens are revocable. An administrator revoking a user's sessions, a password reset, or a Conditional Access policy change can invalidate refresh tokens, which is exactly the lever that makes long-lived sessions safe to offer. The client credentials flow, notably, does not get a refresh token at all, because a daemon can simply request a new token with its own credential whenever it needs one.

### Why did my access token get rejected even though sign-in worked?

The most common cause is a scope or audience mismatch. Sign-in produces an ID token that proves who you are, but the access token must carry the specific scope the API requires and an audience that names that API. If you requested the wrong scope, or sent a token minted for a different resource, the API returns 403 or 401 despite a clean sign-in.

This question captures the single most frequent OAuth support ticket, and the diagnosis is almost mechanical once you separate the tokens. A successful sign-in means the ID token validated and the client established a session. It says nothing about whether the access token is fit for the call you are making. Decode the access token, read its audience claim, and confirm it names the resource you are calling. Then read its scope or roles claim and confirm the required permission is present. If the audience is wrong, you requested a token for the wrong resource. If the scope is missing, you did not request it or consent was not granted. Neither symptom is fixed by changing the flow, and that is the whole point of keeping the token types straight.

## Real-world scenarios, each mapped to its flow

The decision table is abstract until you see it resolve concrete situations. These are the recurring patterns engineers actually report, each described as a problem and then placed in its row.

A single-page app needs sign-in and an API call. The team starts from an old sample using implicit and ships tokens through the URL fragment. The correct pattern is authorization code with PKCE running entirely in the browser: the SPA generates a verifier, redirects to authorize with the challenge, receives a code at its redirect address, and exchanges the code with the verifier at the token endpoint using cross-origin calls. No secret, no token in the fragment. This is the most common modernization any identity engineer performs.

A nightly synchronization job moves data between two systems with no human involved. A developer copies a user sign-in snippet and cannot work out where the consent prompt should appear, because there is no browser to show it. The pattern is client credentials: the job authenticates with its own certificate, requests the resource's `.default` scope, and runs with the application permissions an administrator granted. The absence of a user is the signal that selects this row.

A command-line tool must sign a user in on a server with no browser. Attempts to pop a browser fail in the headless environment. The pattern is device code: the tool prints a code and a URL, the engineer authorizes on a laptop, and the tool polls until the tokens arrive. The constraint on input, not on identity, selects this flow, and the resulting token is still a delegated user token.

An API call returns 403 even though the user signed in cleanly. The team retries, widens roles, and restarts the app, none of which helps. Decoding the access token shows the required scope is absent. The pattern is a scope and consent gap: request the correct scope at the client and obtain consent. The flow was never the problem.

A delegated app shows a consent prompt the first time each user signs in, and an administrator wants to suppress it across the tenant. The pattern is administrator consent: an administrator grants the requested permissions tenant-wide, after which individual users no longer see the prompt. This is a permissions and consent decision layered on a correct authorization code flow.

A web app keeps a user signed in for a full working day after one sign-in. The mechanism is the refresh token, held server-side by the confidential client and exchanged silently for new access tokens as each one expires. The user sees an uninterrupted session; underneath, short-lived access tokens are being renewed continuously.

### Which scenario is the one engineers get wrong most often?

The single-page app on implicit and the daemon on a user flow are the two most common errors. Both stem from copying a sample that targeted a different client type. The fix in each case is to re-derive the flow from the client's properties using the decision table rather than trusting that the inherited snippet matched the app being built.

## The two wrong turns this article exists to correct

Template E asks for the common misconfiguration and the exposure it creates, and OAuth in Azure has two that recur often enough to name. Engaging them directly is more useful than listing best practices, because each one feels correct from inside the mistake.

### Using the deprecated implicit flow in a browser app

The implicit flow still appears in production single-page apps, usually because the app was scaffolded years ago or because a tutorial the team followed used it. From inside the codebase it looks fine: the user signs in, a token appears, the API calls work. The exposure is invisible at runtime. Because implicit returns the access token in the URL fragment, that token can land in browser history, in the referrer header sent to the next site the user visits, and in any logging that captures URLs. A token in any of those places is a token an attacker can replay until it expires. The flow also cannot deliver a refresh token safely, which pushes teams toward longer-lived access tokens to avoid frequent re-authentication, compounding the exposure.

The correct response is not to harden implicit but to retire it. Authorization code with PKCE running in the browser gives a single-page app everything implicit offered and removes the exposure. The code that travels through the redirect is single use, PKCE binds it to the originating client so an intercepted code is worthless, and the access token is delivered in a token-endpoint response body rather than a URL. Migrating is rarely more than reconfiguring the identity library to request `code` instead of a token and enabling PKCE, which most current libraries do by default. Treat any remaining implicit usage as a finding, not a style choice.

### Using client credentials for a user-facing scenario

The second wrong turn is subtler because the app works and even passes a casual review. A developer needs to call Microsoft Graph from a web app, finds a client credentials snippet that compiles, and ships it. The app now calls Graph as itself with application permissions rather than as the signed-in user with delegated permissions. Two failures follow. First, the app cannot distinguish users: every request runs with the same application identity, so per-user authorization and auditing collapse. Second, and worse, application permissions are typically broad and tenant-wide, so a web app that should only ever read the current user's mailbox may be holding a permission that can read every mailbox in the organization. A bug or a compromise in that app is now an organization-wide exposure rather than a single-user one.

The correct flow when a user is present and the app acts for that user is authorization code with PKCE producing a delegated token, whose permissions are bounded by what the signed-in user can do. Client credentials is reserved for the rows of the decision table with no user. The way to catch this mistake in review is to read the scope and roles claims of the token the app obtains: a `roles` claim with application permissions on a user-facing web app is the signature of this error, and it should stop the review until the flow is corrected.

### Is a service principal the same as an app registration here?

Not quite. The app registration is the application's definition in your tenant, including its redirect addresses, credentials, and requested permissions. The service principal is the local instance of that application in a tenant, the identity that actually holds role assignments and consents. Client credentials authenticates as the service principal. The registration declares the app; the service principal is the app's identity at runtime.

## Verifying the posture: read the tokens

You cannot reason about an OAuth problem you cannot see, so the central verification skill is reading tokens. Entra ID issues JSON Web Tokens for ID tokens and for most access tokens, and a JWT is three base64url segments separated by dots: a header, a payload of claims, and a signature. The header and payload decode to readable JSON, which is exactly what you inspect when a flow misbehaves.

The discipline is to decode the credential your client received and check the claims that the failing call depends on. For an access token rejected by an API, decode it and read the `aud` claim to confirm it names the resource you are calling, the `scp` claim to confirm the delegated scope is present, and the `roles` claim if you expected application permissions. For an ID token that produced the wrong session, read `tid` to confirm the tenant, `oid` for the user's stable object identifier, and `preferred_username` for the account. For anything rejected as expired or not yet valid, read the `exp`, `nbf`, and `iat` timing claims and check the clock on the validating service, because skew between servers produces tokens that look valid in one place and invalid in another.

```bash
# Decode a JWT's payload locally without sending it anywhere.
# Split on dots, take the second segment, base64url-decode it, pretty-print.

token="eyJ0eXAiOiJKV1QiLi4u.eyJhdWQiOiJodHRwczov...payload....sig"
echo "$token" | cut -d '.' -f2 | tr '_-' '/+' | base64 -d 2>/dev/null | python3 -m json.tool
```

For interactive debugging, Entra ID provides a token-inspection page that decodes a signed-in user's tokens and displays the claims in a readable form, which is convenient when you want to confirm what a real sign-in produced rather than decode by hand. The principle is the same either way: it is not a black box but a signed statement you can read, and most OAuth defects in Azure announce themselves plainly in the claims once you look. Hands-on practice running each flow and inspecting the tokens it produces is exactly what the [Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) are built for, since seeing the difference between an `scp` claim and a `roles` claim in a real token teaches the distinction faster than any description.

### How do I confirm which flow my app is actually running?

Read what it obtained and look at three signals. A `roles` claim with no user subject indicates client credentials. An `scp` claim with a user object identifier indicates a delegated flow such as authorization code. The presence of an ID token alongside the access token confirms an OIDC sign-in occurred, which client credentials never produces.

## Making OAuth auditable and repeatable

A correct flow chosen once is not enough; the choice has to survive turnover, refactors, and new services that copy the old ones. Two practices make the posture durable.

The first is to record the flow decision where the next engineer will see it, tied to the client type that drove it. A short note in the app registration's description or in the repository that says, in effect, "this is a confidential web app, so it runs authorization code with PKCE and holds its secret server-side," prevents the most common regression, which is a future change that silently shifts the flow. The decision table is the format for that note: state the client type, state the flow, state the one-line reason. When a new service is added, it inherits the reasoning rather than a snippet.

The second is to make the permission grants explicit and reviewed rather than accreted. Application permissions in particular should be enumerated, justified, and periodically reviewed, because they are the ones with tenant-wide reach and the ones most likely to be over-granted by a developer reaching for `.default` without checking what it pulls in. Treating the set of granted scopes and roles as a reviewable artifact, rather than as an invisible side effect of consent, is what keeps a daemon from quietly holding far more than it needs. For the workflow case where a continuous integration system needs to authenticate to Azure without a stored secret at all, the federated approach in the [GitHub Actions OIDC](/2023/08/14/configure-github-actions-oidc/) configuration guide shows how an external workload uses OIDC to obtain Entra tokens, which is the secretless evolution of the client credentials story.

### How often should I review the scopes an app holds?

Review delegated scopes when the app's behavior changes and review application permissions on a fixed schedule, because they are tenant-wide and high trust. Any app whose `roles` claim grants broad write access to a sensitive resource deserves scrutiny at every release. The goal is least privilege over time, not just at the moment the app was first granted consent.

## Front-channel and back-channel: where the risk lives

One more distinction sharpens everything above: the difference between the front channel and the back channel. The front channel is the browser. Anything that travels through it, the authorize request and the redirect response, passes through software the user controls and that an attacker may observe, so the front channel is treated as untrusted. The back channel is the direct server-to-server call from your app to the token endpoint, which the user's browser never sees. It is where secrets and tokens can move with far less exposure.

Reading the flows through this lens explains their shapes. Authorization code with PKCE sends only a single-use code through the front channel, never a token and never a long-lived secret, and then moves the actual tokens through the back channel in the token-endpoint response. The deprecated implicit flow violated this principle by returning the access token itself through the front channel in a URL fragment, which is the structural reason it is unsafe rather than merely old. The device code flow keeps the constrained device entirely on the back channel by polling the token endpoint directly, while pushing the untrusted interactive part onto a separate browser the user already trusts. Client credentials lives wholly on the back channel, since there is no browser involved at all, which is why it can carry a long-lived secret that an interactive public client never could.

The practical guidance that falls out of this is to keep credentials and tokens off the front channel wherever the flow allows it, and to prefer a certificate over a client secret for any confidential client that authenticates on the back channel. A certificate never travels as a shared string the way a secret does; the client proves possession of a private key by signing an assertion, so there is no secret value to leak in transit or at rest in a configuration store. For the highest-trust back-channel scenario, the secretless federated pattern removes the stored credential entirely, which is the direction modern Azure identity design keeps pushing toward.

### Why is a certificate better than a client secret for a confidential client?

A client secret is a shared string that must be stored, transmitted, and rotated, and anyone who reads it can impersonate the app. A certificate lets the app prove possession of a private key by signing an assertion, so no reusable secret value crosses the wire or sits in config. Certificates are harder to exfiltrate and cleaner to rotate, which is why they are preferred for production confidential clients.

## Closing verdict

OAuth 2.0 and OIDC in Azure are not a library to import and forget. They are a contract, and the single decision that determines whether you honor that contract or violate it is which grant flow you run. The flow is not a preference. It is a function of your client: whether a user is present, whether your code can keep a secret, and whether the client has a browser. Answer those three questions and the decision table hands you the flow, and with it the audience, the scopes, and the token types you should expect.

Hold the layers apart and the rest follows. OAuth authorizes and OIDC authenticates. The access token is for the resource and the ID token is for the client. Scopes grant permission and claims state facts. PKCE replaces the secret a public client cannot keep, which is why authorization code with PKCE is the modern interactive default and implicit is retired. Client credentials is for the no-user rows and nothing else. When something breaks, you decode it and read the claims, because the failure is almost always written there in plain sight. An engineer who works this way stops copying flows and starts choosing them, which is the difference between an app that demos and an app that survives the security review.

## The endpoints and the authority you are actually talking to

Every flow described so far hits the same two Entra ID endpoints, and understanding what those endpoints are removes a whole category of confusion. The authorize endpoint at `/oauth2/v2.0/authorize` handles the interactive, browser-facing leg: it shows the sign-in page, runs the user through any required checks, runs the consent prompt, and returns an authorization code or an error to your redirect address. The token endpoint at `/oauth2/v2.0/token` handles the back-channel leg: it takes a code, a client credential, a refresh token, or a client-credentials request and returns tokens. Interactive flows touch both endpoints; client credentials touches only the token endpoint, because there is no interactive leg.

The path segment before those endpoints is the authority, and it carries more meaning than engineers usually notice. A URL of the form `https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/authorize` names a specific tenant, which means only accounts from that tenant can sign in. Replacing the tenant identifier with `organizations` allows any work or school account from any Entra tenant, `common` allows both work accounts and personal Microsoft accounts, and `consumers` allows only personal accounts. The authority you choose is therefore an access-control decision baked into the URL, and a multitenant app that should accept any organization's users but is pointed at a single tenant identifier will reject every external user with an error that looks like a misconfiguration but is actually a deliberate boundary doing its job.

### What is the difference between the v1.0 and v2.0 endpoints?

Entra ID exposes both a legacy v1.0 endpoint and a current v2.0 endpoint. The v2.0 endpoint is the one to build on: it supports the modern scope model where you request granular permissions like `User.Read` directly, it issues tokens that follow current claim conventions, and it works with both work accounts and personal Microsoft accounts. The v1.0 endpoint used a resource parameter rather than scopes and predates much of the current model.

The practical advice is to standardize on v2.0 for anything new and to be aware of which endpoint an older app uses when you debug it, because the request shape differs. A v1.0 flow names a resource and receives permissions for that whole resource; a v2.0 flow names individual scopes. Mixing mental models between the two is a common source of confusion when an engineer reads a v1.0 tutorial while building against the v2.0 endpoint. The token an app receives also carries a version, and a resource that expects v2.0 access tokens can reject a v1.0-shaped token even when the sign-in itself succeeded, which is one more reason the token-decoding habit pays off.

### How does the discovery document help?

Every Entra authority publishes a discovery document, an OpenID Connect metadata document, at a well-known path under the authority. It lists the authorize and token endpoint URLs, the supported scopes and response types, the issuer value your tokens will carry, and the location of the signing keys. Libraries fetch it automatically so they never hardcode endpoints, and you can fetch it by hand to confirm exactly what a given authority supports.

```bash
# Fetch the OIDC discovery document for a tenant to see its real endpoints and issuer.
curl -s "https://login.microsoftonline.com/{tenant-id}/v2.0/.well-known/openid-configuration" \
  | python3 -m json.tool

# The jwks_uri field in that document points to the signing keys
# a resource uses to validate token signatures.
```

The discovery document is the source of truth that ties the protocol together. Its `issuer` field is the exact string your tokens will carry in their `iss` claim, so a resource validating tokens compares the token's issuer against this value. Its `jwks_uri` points to the JSON Web Key Set, the published public keys that validate token signatures. When a resource suddenly starts rejecting valid tokens after working for months, a stale cached key set is a frequent cause, because Entra ID rotates its signing keys and a resource that caches keys too aggressively will fail to validate tokens signed with a new key until it refreshes from the `jwks_uri`.

## Public clients, confidential clients, and why the distinction drives everything

The decision table's right column hides a single underlying axis that is worth naming on its own: whether your client is public or confidential. A confidential client can keep a secret. It runs somewhere the user cannot reach the credential, such as a web server backend, so it can authenticate to the token endpoint with a client secret or a certificate. A public client cannot keep a secret. It runs entirely on the user's device, as a single-page app in the browser or a native app on a phone, so any secret you embed in it can be extracted by anyone with the app. This single property explains most of the rules that otherwise look arbitrary.

PKCE exists because public clients cannot keep a secret yet still need to prove that the entity redeeming the authorization code is the one that started the flow. The verifier-and-challenge mechanism gives a public client a per-flow secret that lives only in memory for the duration of the flow, which is the only kind of secret a public client can safely hold. Confidential clients use PKCE too in current guidance, but they additionally present their long-lived secret, giving two independent proofs. The reason a single-page app receives refresh tokens under tighter constraints than a web backend is the same property: the SPA is a public client with nowhere safe to store a long-lived token, while the backend is confidential and can lock its refresh token away from the user.

### Why can a single-page app not just use a client secret?

Because everything a single-page app ships runs in the user's browser, where the user and any script can read it. A secret embedded in browser-delivered code is not secret. That is the definition of a public client. PKCE replaces the secret with a per-flow proof that never has to be stored, which is exactly why authorization code with PKCE, not a secret-based flow, is the correct pattern for a SPA.

The corollary engineers miss is that registering a client incorrectly as confidential when it is in fact public, or the reverse, produces failures that look like protocol bugs. A public client registration that tries to send a secret will be told it should not, and a confidential client that omits its required credential will fail to redeem the code. Matching the registration's client type to the real deployment shape is part of choosing the flow, not a separate concern, and the [Entra app registrations](/2024/03/04/entra-app-registrations-explained/) guide covers where that client type is set.

## The parameters that protect the flow: state and nonce

Two small parameters do outsized security work in the interactive flows, and skipping them is a quiet vulnerability rather than a visible failure. The `state` parameter is an opaque value the client generates before redirecting to the authorize endpoint and checks when the response comes back. It binds the response to the request, which defeats cross-site request forgery against the redirect: an attacker who tricks a browser into hitting the redirect address with a forged response cannot produce the matching `state` value the client is expecting, so the client rejects it. The client can also pack its own context into `state`, such as the page the user was trying to reach, so the flow can resume where it left off.

The `nonce` parameter, used in OIDC sign-in, defends the ID token against replay. The client generates a nonce, sends it in the authorize request, and Entra ID embeds it in the resulting ID token as a claim. When the client validates the ID token, it checks that the nonce in the token matches the one it sent. An attacker who captures an old ID token cannot replay it into a new sign-in, because the new sign-in expects a freshly generated nonce that the old token will not carry. These two parameters cost almost nothing to implement, are handled automatically by mature identity libraries, and close real attack paths, which is why their absence in a hand-rolled flow is a finding worth raising in review.

### Do I need to implement state and nonce myself?

If you use a supported identity library it generates, sends, and validates both for you, and you should not reimplement them. The risk appears in hand-rolled flows that construct the authorize request directly and forget one or both. If you ever build the requests yourself, treat `state` and `nonce` as mandatory, not optional, because their absence is invisible until it is exploited.

## How token validation actually works at the resource

The flows get the token to the client, but the security only holds if the resource validates the token correctly, and validation is where subtle resource-side bugs hide. A resource receiving a bearer token must do several checks before trusting it, and skipping any of them weakens the whole chain. It must verify the signature against the issuer's published keys so it knows Entra ID minted the token and it was not tampered with. It must check the `iss` claim against the expected issuer from the discovery document so a token from a different authority is rejected. It must check the `aud` claim names itself so a token minted for a different resource is rejected. It must check the `exp` and `nbf` timing claims so an expired or not-yet-valid token is rejected. Only after all of that does it read the `scp` or `roles` claim to authorize the specific action.

The most dangerous shortcut is skipping audience validation, because a token is a bearer token: whoever holds it can use it. If resource A does not check that the token's audience names resource A, then a token a client legitimately obtained for resource B can be replayed against resource A, and resource A will honor it. This is how a token scoped for one API ends up granting access to another that trusted it blindly. The published key set, fetched from the `jwks_uri` and refreshed as Entra rotates keys, is the anchor for the signature check, and the issuer and audience values from the discovery document anchor the other two. A resource that validates all four properties and then authorizes from the scope claim is doing OAuth correctly; a resource that validates fewer is trusting more than the protocol intends.

### What does a resource need from the discovery document to validate tokens?

It needs the issuer value to check the `iss` claim and the `jwks_uri` to fetch the signing keys for the signature check. It should cache the keys but refresh them when an unknown key identifier appears, because Entra rotates signing keys over time. With the issuer, the keys, its own audience value, and the token's timing claims, a resource can validate any token Entra issues.

## How multitenancy changes the flow

A multitenant app, one that signs in users from organizations other than the one that registered it, runs the same flows but with two differences that trip people up. First, it uses the `organizations` or `common` authority rather than a single tenant identifier, so Entra ID accepts users from any tenant. Second, the consent model becomes a per-tenant concern: each external tenant's administrator or users must consent to the app before it works in that tenant, and the app's permissions are granted independently in each tenant where it is used. A multitenant app that works perfectly in its home tenant can fail on first use in a customer's tenant purely because consent has not been granted there yet, and the error will reference consent rather than the flow.

The token claims also shift in a multitenant context. The `tid` claim names the tenant the user actually belongs to, which differs from the app's home tenant, and an app that assumes every user comes from its own tenant will mishandle external users. The `iss` claim likewise reflects the user's tenant authority. An app built for multitenancy reads `tid` deliberately to know which organization a user belongs to, often using it to scope data or to apply tenant-specific configuration. For the identity-model background that makes multitenancy comprehensible, the [Microsoft Entra ID](/2022/02/21/microsoft-entra-id-explained/) overview lays out how tenants and directories relate.

### Why does my app work in my tenant but fail for external users?

Almost always consent. A multitenant app needs consent in each tenant where it is used, and the home tenant where it was registered already has it. An external tenant does not until its administrator or a user there grants it. The failure references a consent-required condition, and the fix is to obtain consent in the external tenant, not to change the authority or the flow.

## Where Conditional Access intersects the flow

OAuth and OIDC decide which flow runs and what tokens issue, but Conditional Access can interrupt the interactive leg with additional requirements before Entra ID issues a token at all. A policy might require multifactor authentication, a compliant device, or a particular network location for the resource the app is requesting. From the flow's perspective this happens during the authorize leg: the user is asked for the extra factor, and only when the conditions are satisfied does Entra ID return the authorization code. This is why an interactive flow that worked yesterday can suddenly prompt for more today, and it is not a bug in the flow but a policy gating the sign-in.

The interaction matters for flows without an interactive leg. The client credentials flow has no user and no interactive sign-in, so user-targeted Conditional Access policies do not apply to it in the same way; controlling a daemon's access is a matter of the permissions it holds and, increasingly, workload identity policies rather than user sign-in conditions. For interactive flows, a token rejected or a re-authentication prompt that seems to come from nowhere is often Conditional Access asserting a requirement mid-flow, and the place to look is the policy set rather than the OAuth request. The [Entra ID authentication](/2023/12/18/entra-id-authentication-explained/) deep dive covers how these sign-in gates layer onto the authentication step.

### Can Conditional Access break an existing OAuth flow?

It can change the user experience and, for noncompliant conditions, block token issuance, but it does not change which flow is correct. A new policy requiring multifactor authentication adds a step to the interactive leg. A policy requiring a compliant device can block a sign-in entirely until the device complies. The flow itself is unchanged; the sign-in now carries conditions it must satisfy before Entra issues the token.

## Token lifetimes and what you can and cannot change

Access tokens in Entra ID are short lived by default, commonly around an hour, and this is deliberate rather than configurable on a whim. The short lifetime is the reason a stolen access token is a bounded problem: it expires soon, and the refresh token, which is revocable, controls whether a new one is issued. Engineers sometimes want to lengthen access token lifetime to reduce token-endpoint traffic, but doing so widens the window in which a stolen token is usable, which is exactly the tradeoff the short default is protecting against. The better lever for a smooth session is the refresh token, which renews access tokens silently without extending any single token's exposure.

The durable, revocable nature of the refresh token is the real session control. Because a refresh token can be invalidated by an administrator, a password change, or a policy event, a long session built on silent refresh remains under organizational control in a way a long-lived access token never could be. This is the architecture to lean on: short access tokens that expire quickly, a refresh token that renews them quietly, and revocation that can cut a session at any time. Trying to engineer around it by lengthening access tokens trades a property you want, fast revocation, for one you do not need, fewer token-endpoint calls.

### Should I lengthen my access token lifetime to reduce calls to Entra?

No. The short lifetime bounds the damage from a stolen token, and the refresh token already handles renewal silently, so lengthening the access token buys little and weakens revocation. If token-endpoint traffic is a concern, cache and reuse tokens until they near expiry and let the refresh token do its job rather than extending the access token's reach.

## Reading the errors each flow produces

When a flow fails, Entra ID usually tells you why in an error code, and learning to map the common codes to their cause turns a frustrating loop into a quick diagnosis. The codes carry an `AADSTS` prefix and appear in the redirect response for interactive flows or the token-endpoint response for back-channel flows. Treat the code as the first thing to read, because it names the cause more precisely than the human-readable message beside it.

| Symptom | Typical error family | What it usually means | Where to fix it |
| --- | --- | --- | --- |
| Sign-in returns to an error instead of your app | Redirect address mismatch | The redirect address in the request does not exactly match one registered on the app | Register the exact redirect address, scheme and path included |
| User sees a consent screen that cannot be completed | Consent required | The requested permission needs consent that has not been granted, often administrator consent | Grant consent for the user or the tenant |
| Token request rejected for the requested permission | Invalid scope | The scope is misspelled, not exposed by the resource, or not the resource's `.default` | Request a scope the resource actually publishes |
| Confidential client cannot redeem the code | Invalid client credential | The client secret is wrong, expired, or a certificate assertion is invalid | Rotate or correct the credential on the registration |
| Resource rejects an otherwise valid token | Audience or resource mismatch | The token's audience does not name the resource being called | Request a token for the correct resource scope |

The pattern across the table is that the error names a stage, and the stage points at the fix. A redirect mismatch is a registration problem, not a flow problem, and the fix is to register the exact address the app sends, down to the trailing slash and the scheme, because Entra ID matches it exactly as a string. A consent error is a permissions problem, and the fix lives in the grant, not the request. A credential error on a confidential client is almost always an expired secret, which is one more argument for certificates and for tracking secret expiry before it bites. None of these are reasons to change the grant flow, which is the recurring lesson: most OAuth failures in Azure are configuration or consent issues sitting on top of a correctly chosen flow.

### What is the first thing to check when an interactive sign-in fails?

Read the error code in the redirect response and check the redirect address first. A mismatch between the address your app sends and the addresses registered on the app is the single most common interactive failure, and Entra ID matches the value character for character, so a missing trailing slash or an `http` against a registered `https` is enough to break it. The related redirect-mismatch troubleshooting is a frequent first stop.

## Why some access tokens are readable and some are not

A subtlety that confuses engineers is that not every access token is a JSON Web Token you can decode. For Microsoft Graph and for many Microsoft resources, the access token format is an implementation detail the resource owns, and the client is explicitly not supposed to parse it. The token might look like a JWT or might be opaque, and either way the contract is that the client treats it as a string to forward, not a document to read. Only the resource that issued the audience is guaranteed to be able to interpret it. This is by design: decoupling the client from the token's internals lets the resource change the format without breaking clients.

For your own APIs, where you control the resource, the access token is a JWT you define the validation for, and you can and should read its claims at the resource to authorize. The discipline that prevents bugs is to remember which side you are on. As a client, never branch your logic on the contents of an access token, because you may be reading a string you were never meant to parse and whose format can change under you. As a resource, validate and read it because that is your job. The ID token, by contrast, is always meant for the client to read, which is why identity information for the signed-in user belongs in the ID token's claims and not in whatever the access token happens to contain.

### Should I read claims out of the access token in my client code?

No, not for a token aimed at a resource you do not own, such as Microsoft Graph, because its format is not a contract you can rely on and may be opaque. Read user identity from the ID token, which is meant for the client. Read access-token claims only at a resource you own and validate. Crossing this line is a common, quiet source of breakage.

## Putting it together: a flow chosen by reasoning

Walk one realistic decision end to end to see the whole article operate as a single method. A team is building a customer-facing web application with a server-side backend that must call Microsoft Graph to read the signed-in user's profile and later call the team's own internal API. Start with the client questions. Is a user present at sign-in? Yes, customers sign in interactively. Can the code keep a secret? Yes, the backend runs server-side, so it is a confidential client. Does it have a browser? Yes, it is a web app. Those answers place the app squarely in the interactive, confidential row: authorization code with PKCE, with the backend holding a secret or, better, a certificate.

From there the rest follows without further guesswork. Because a user is present, the app requests delegated scopes, including `openid` and `profile` to get an ID token for sign-in and `User.Read` to call Graph as the user. The token endpoint returns an ID token the backend validates to establish the session, an access token aimed at Graph that the backend forwards to Graph, and a refresh token the backend stores server-side to keep the session alive. When the app later needs to call its own internal API as the same user, it requests the internal API's scope and receives an access token whose audience names that API. If the internal API must in turn call a further service as the user, the on-behalf-of flow carries the identity one hop deeper. At no point did the team copy a flow; they derived each step from a property they already knew about their app, which is the entire discipline this article teaches.

### What changes if that same app had no user?

Everything in the interactive leg disappears. If the same backend ran as a scheduled job with no signed-in user, it would move to client credentials, authenticate with its certificate, request Graph's `.default` scope, and receive an application-permission token with no ID token and no refresh token. The single changed fact, the absence of a user, moves the app to a different row and a different flow, which is the decision table doing its work.

## Frequently asked questions

### Q: What is the difference between OAuth 2.0 and OIDC, stated simply?

OAuth 2.0 is an authorization framework: it lets an application obtain a token to call an API on behalf of a user or itself, without ever handling the user's password. It does not tell the application who the user is. OpenID Connect adds that missing identity layer on top of OAuth 2.0 by introducing the ID token, a signed token the client validates and reads to learn who signed in. So OAuth authorizes access to resources, while OIDC authenticates the user to the client. In an Azure web app sign-in you use both at once: OAuth issues an access token for the API you call, and OIDC issues an ID token that proves the user's identity. Treating them as one thing is the root of many design mistakes, because the two tokens have different audiences and different validation rules.

### Q: Which OAuth grant flow should I pick for a new application?

Derive it from your client rather than copying a sample. Ask three questions: is a user present at sign-in, can your code keep a secret away from the user, and does the client have a browser. An interactive app with a user, whether it is a web app with a backend, a single-page app, or a native mobile app, uses authorization code with PKCE. A background service with no user uses client credentials. A device or command-line tool with no browser uses device code. A middle-tier API that must call a further API as the user uses on-behalf-of. The flow is a function of these properties, not a preference, which is why the same flow can serve a confidential web app and a public SPA: both have an interactive user. If you cannot place your app in exactly one of these rows, you do not yet understand your client well enough to choose, and that is the gap to close first.

### Q: What problem does PKCE actually solve?

PKCE, Proof Key for Code Exchange, stops an attacker who intercepts an authorization code from redeeming it. In the interactive flow, the authorization code travels back to your app through the browser, where it can potentially be intercepted. PKCE binds that code to the client that started the flow. The client generates a random verifier, sends a SHA-256 hash of it as the challenge in the first leg, and presents the original verifier when redeeming the code in the second leg. Entra ID hashes the presented verifier and rejects the code if it does not match the challenge it stored. An attacker who steals the code never saw the verifier, so the code is useless to them. This is why PKCE is mandatory for public clients, which cannot hold a secret, and recommended for confidential clients as well, giving a per-flow proof that lives only in memory for the duration of the flow.

### Q: When is the client credentials flow the right choice, and what are its risks?

Use it when there is no user, such as a scheduled job, a webhook receiver, or a service that syncs systems. The application authenticates as itself using its own secret or certificate and receives a token carrying application permissions, expressed through the resource's `.default` scope. The risks are real and stem from that power. Application permissions are not bounded by what any single user can do, so a daemon that should read one mailbox may hold a permission that reads every mailbox in the tenant. A compromise of the daemon's credential becomes a tenant-wide exposure. Mitigate this by granting the narrowest application permissions the job needs, preferring a certificate over a client secret because it is harder to exfiltrate and cleaner to rotate, and reviewing the permissions on a schedule. Never reach for client credentials simply because a snippet compiled; if a user is present, you want a delegated flow instead.

### Q: How do scopes and claims appear inside an issued token?

A scope you requested and were granted shows up in the access token's `scp` claim for delegated permissions, listing the space-separated permissions the resource will honor, or in the `roles` claim for application permissions obtained through client credentials. Claims more broadly are the key-value statements packed into it: the `aud` claim names the intended resource, `iss` names the issuing authority, `tid` names the tenant, `oid` gives the user's stable object identifier, and `exp`, `nbf`, and `iat` bound the token's validity in time. The resource reads these claims to decide whether to honor the call, checking signature, issuer, audience, and expiry before trusting the scope claim to authorize the specific action. When you debug an OAuth problem in Azure, you are almost always decoding a token and reading exactly these claims, because the cause of a rejection is usually written there plainly.

### Q: How long do refresh tokens last and what can invalidate one?

Refresh tokens are long lived relative to access tokens, which typically expire in about an hour, and they let a client obtain new access tokens silently without forcing the user to sign in again. Rather than thinking in fixed numbers, which can change and should be verified against the current official source, think in terms of revocability. A refresh token can be invalidated by an administrator revoking the user's sessions, by a password change, by a Conditional Access policy event, or by the user's account being disabled. That revocability is exactly what makes long sessions safe to offer: the session persists through silent renewal, but the organization retains the ability to cut it at any moment. Confidential clients store refresh tokens server-side where they are well protected; public clients such as single-page apps receive them under tighter constraints because they have no safe long-term storage. The client credentials flow receives no refresh token, because a daemon can request a fresh token with its own credential whenever it needs one.

### Q: Can I use one access token to call several different APIs?

Generally no, because an access token carries an `aud` claim that names a single intended resource, and a correctly built resource rejects a token whose audience does not name it. A token minted for Microsoft Graph is not valid against your own API, and vice versa. To call multiple APIs you request a token per resource, each with the appropriate scope and audience. In a layered design where a middle-tier API must call a further API as the same user, the on-behalf-of flow exchanges the incoming token for a new one aimed at the downstream resource, preserving the user's identity. The temptation to forward one token everywhere leads to either rejections, when the downstream resource validates the audience, or a security hole, when a resource fails to validate the audience and accepts a token meant for somewhere else. Request the right token for each resource rather than reusing one across boundaries.

### Q: What is the .default scope and when do I use it?

The `.default` scope is how a client requests all the permissions that have already been granted to it on a resource, rather than naming individual scopes. It is used primarily in the client credentials flow, where the application asks for the resource's `.default`, such as `https://graph.microsoft.com/.default`, and receives a token carrying whatever application permissions an administrator configured for it. You also see it when performing administrator consent for a set of statically configured permissions. The contrast is with delegated flows, where you typically request granular scopes like `User.Read` directly for the actions you need. Because `.default` pulls in the full set of configured permissions wholesale, it pairs naturally with the high-trust, administrator-granted application permissions of the client credentials flow. Treat it carefully: requesting `.default` means accepting whatever the app was granted, so the discipline of granting only the permissions the app needs becomes the control that keeps the resulting token from being over-privileged.

### Q: Is OAuth 2.0 an authentication protocol?

No, and treating it as one is a classic mistake. OAuth 2.0 is an authorization framework. It produces access tokens that grant permission to call resources, but it makes no standardized statement about who the user is. The industry abused OAuth for sign-in for years, each implementation inventing its own way to learn the user's identity, which produced inconsistent and sometimes insecure results. OpenID Connect was created precisely to fix this by standardizing authentication on top of OAuth through the ID token. So if your goal is to know who signed in, you want OIDC, which uses OAuth underneath but adds the verifiable identity layer. If your goal is only to call an API with permission, OAuth alone suffices. In Azure most interactive apps want both, which is why they request the `openid` scope to turn an OAuth authorization into an OIDC sign-in and receive an ID token alongside the access token.

### Q: What happens to a flow if the user closes the browser before consenting?

The flow simply does not complete, and no tokens are issued. In an interactive flow the authorization code is only returned to your redirect address after the user signs in and grants any required consent. If the user abandons the sign-in or closes the browser at the consent screen, your app never receives a code and therefore never reaches the token-exchange leg. The app should handle this gracefully by treating the absence of a returned code, or an explicit error in the redirect, as a cancelled sign-in rather than an error to retry blindly. For the device code flow, the constrained device keeps polling and will eventually receive a timeout or pending response if the user never finishes on the second device, and the app should stop polling and present the option to start over. In neither case is partial authorization granted; consent is all or nothing for the requested set.

### Q: Do native mobile apps use the same flow as single-page apps?

Yes, both use authorization code with PKCE, because both are public clients with an interactive user. A native or mobile app cannot safely embed a secret, since anything shipped in the app binary can be extracted, so it relies on PKCE exactly as a single-page app does. The mechanics differ in surface detail. A native app commonly uses a system browser or an in-app browser tab for the interactive leg and a custom redirect scheme to receive the code, while a SPA runs the whole flow in the page and uses cross-origin calls to the token endpoint. The protocol spine is identical: generate a verifier, redirect to authorize with the challenge, receive a code, exchange it with the verifier. This shared answer is the decision table making its point that the flow follows from the client's properties, here the combination of an interactive user and the inability to keep a secret, not from the specific platform.

### Q: How do I migrate a legacy implicit-flow single-page app without breaking users?

Reconfigure the app to request an authorization code rather than a token and enable PKCE, which most current identity libraries do by default once you select the authorization code flow. On the registration side, ensure the app is treated as a single-page application so the token endpoint accepts the cross-origin code exchange. The user-facing experience is unchanged because sign-in still happens through the same redirect to Entra ID; what changes is that the response now carries a single-use code instead of a token in the URL fragment, and your app exchanges that code for tokens through a back-channel call. Test the full sign-in, token acquisition, and silent renewal paths in a staging environment before rolling out, watching for any code that assumed a token would arrive in the fragment. The migration removes the exposure of tokens in browser history and referrer headers and gives you a safer renewal path, so it is worth doing even when the old flow appears to work.

### Q: Why does my daemon not receive a refresh token?

Because the client credentials flow does not issue refresh tokens, by design. A refresh token exists to renew a user's session without forcing re-authentication, and a daemon has no user and no session to preserve. When a daemon's access token expires, it simply runs the client credentials flow again, presenting its own secret or certificate to obtain a fresh access token. There is nothing to refresh because the app's own credential is always available to mint a new token directly. This is actually simpler and safer than holding a refresh token: there is one fewer long-lived secret to store and protect. If you find yourself wanting a refresh token in a daemon, it is usually a sign that you have chosen the wrong flow and there is in fact a user involved, in which case a delegated flow such as authorization code is the correct choice and will provide a refresh token appropriately.

### Q: When does a layered API architecture need token exchange?

When a middle-tier API receives a token for itself and must call a further downstream API as the same user, it needs the on-behalf-of flow, which is a form of token exchange. The middle API cannot forward its incoming token to the downstream API, because that token's audience names the middle API and the downstream resource will reject it on audience validation. It also should not call downstream as itself with application permissions, because that loses the user's identity and runs every call with full application privilege. On-behalf-of resolves this: the middle tier presents the incoming token plus its own credential to the token endpoint and receives a new access token aimed at the downstream resource, still naming the original user as the subject. The user's identity flows end to end through every hop, so the downstream API can apply per-user authorization. This is the standard pattern for a front-end calling an API that calls another API.

### Q: Are bearer tokens safe to log for debugging?

No. A bearer token is, by definition, usable by anyone who holds it until it expires, so writing one to a log creates a credential anyone with log access can replay. This is precisely the exposure that made the implicit flow dangerous, since it placed access tokens in URLs that ended up in logs and history. When debugging, decode and inspect a token locally and in the moment rather than persisting it, and if you must capture claims for a record, extract and store the non-sensitive claims you need rather than the whole token. Be especially careful with access tokens and refresh tokens, where a refresh token is the more dangerous of the two because of its longer life. Scrub tokens from any structured logging, and treat any token that does end up in a log or a screenshot as compromised and in need of revocation. The short lifetime of access tokens limits the window but does not eliminate the risk.

### Q: What is the difference between delegated and application permissions in practice?

Delegated permissions apply when a user is present and the app acts on that user's behalf, and they are bounded by what the user is allowed to do: the effective permission is the intersection of what the app requested and what the user can actually perform. Application permissions apply in the client credentials flow when the app acts as itself with no user, and they are bounded only by what an administrator granted, which can be tenant-wide. In the token, delegated permissions show up in the `scp` claim while application permissions show up in the `roles` claim, so reading which claim carries the permission tells you immediately which kind of flow produced the token. The practical guidance is to prefer delegated permissions whenever a user is involved, because they respect that user's own limits, and to reserve application permissions for genuine no-user scenarios while granting the narrowest set the job requires.

### Q: How do I test an OAuth flow locally before deploying?

Register a development application or a separate development app registration with a localhost redirect address, then run the flow against it using your identity library's development configuration. For interactive flows, sign in with a test account and decode the resulting tokens to confirm the audience, scopes, and identity claims are what you expect. For client credentials, use a development secret or certificate and confirm the token carries the application permissions you intended in its `roles` claim. Inspecting tokens is the core of local testing: a flow that returns a token is not necessarily correct, so decode it and verify it matches the row of the decision table you intended. Keep development and production registrations separate so a development secret never reaches production and so you can grant narrower permissions in development. Running each flow hands-on in a sandbox, watching the exact request and the exact token, is the fastest way to build the intuition that makes production debugging quick.

### Q: Does signing out of an app revoke the tokens it already issued?

Not automatically in the way people expect. Signing out of an application typically clears the app's local session and may trigger a sign-out at the identity provider, but an access token that was already issued remains valid until it expires, because it is a bearer token the resource validates on its own without calling back to the issuer for each request. What sign-out and revocation control is the refresh token and the ability to obtain new access tokens: revoking sessions invalidates the refresh token so no new access tokens can be minted, and the existing short-lived access token expires shortly after on its own. This is the reason access tokens are deliberately short lived. If you need immediate revocation of in-flight access, you rely on the short lifetime plus refresh-token revocation together, and for highly sensitive resources you keep access token lifetimes short so the window between revocation and expiry stays small.
