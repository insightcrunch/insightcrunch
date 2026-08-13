---
layout: post
title: "Microsoft Entra App Registrations Explained"
page_title: "Microsoft Entra App Registrations Explained: Application Object vs Service Principal, Credentials, API Permissions, Scopes, and Consent"
date: 2024-03-04
categories: ["Technology"]
tags: ["Azure", "Microsoft Entra ID", "App Registrations", "Identity", "Security", "Cloud Computing"]
excerpt: "Microsoft Entra app registrations explained: the application object versus the enterprise application, credentials, API permissions, scopes, and consent."
image: "/assets/images/blog/blog-65.webp"
reading_time: 61
author: "alex-cunningham"
last_updated: 2026-08-13
lang: en
---
A team registers an application in Microsoft Entra ID, grants it a permission, edits a value in the manifest, and watches the change have no effect on the thing they expected to control. Another team rotates a client secret in one place and the sign-in keeps failing somewhere else. A third team grants an application permission and the app still returns an authorization error until an administrator clicks a button nobody told them about. These are not separate problems. They are the same problem wearing different clothes, and the problem is that Microsoft Entra app registrations are two objects pretending to be one, and almost every piece of registration confusion comes from treating the two as a single thing.

This article fixes that. The goal is not a click-by-click portal walkthrough that goes stale the moment Microsoft moves a blade. The goal is a model an engineer can hold: what the registration actually is, what the enterprise application actually is, how they relate, where credentials live, how API permissions and consent work, how to expose your own API with scopes and roles, and how single-tenant and multitenant audience choices change the whole picture. Hold that model and the portal stops surprising you, because you can predict what each screen does before you open it.

![Microsoft Entra app registrations explained](/assets/images/blog/blog-65.webp)

The single rule that organizes everything here is what this series calls the definition-versus-instance rule. An app registration is the global definition of an application. The enterprise application is the per-tenant instance of that definition, and that instance is a service principal. The registration describes what the app is and what it can request. The service principal is the local identity that actually signs in, holds role assignments, and receives consent inside a specific directory. When you understand which object a setting belongs to, you stop editing the wrong screen and expecting the right result.

## What Microsoft Entra App Registrations Actually Are

Start with the threat the registration model is meant to contain, because that is what the design serves. Every application that talks to a protected resource needs an identity. It needs to prove it is the thing it claims to be, it needs to be granted exactly the access it requires and no more, and the directory needs a record of who allowed that access and when. An app registration is how Microsoft Entra ID gives an application that identity and that record. Get the model wrong and you get one of two failures: an application that cannot authenticate because its identity is misconfigured, or an application that holds far more access than its job requires because someone granted a broad permission to make an error go away. Both are common, and both trace back to the same confusion about which object does what.

The model has two objects. The first is the application object, also called the app registration. It is created once, it lives in the tenant where the application was registered (the home tenant), and it is the global definition of the application. It holds the application ID (the client ID), the display name, the credentials the app uses to prove itself, the API permissions the app declares it wants, the APIs and scopes the app exposes to others, the redirect URIs, and the sign-in audience that decides who can use the app. If you have read the broader [identity model in this series](/2022/02/21/microsoft-entra-id-explained/), the application object is the template that everything else derives from.

The second object is the service principal, which the portal surfaces under Enterprise applications. The service principal is the local representation of the application inside a specific tenant. It is the identity that actually authenticates, the object that holds role assignments and group memberships, the place where consent is recorded for that directory, and the target of conditional access policies and sign-in logs. In the application's home tenant, registering an app creates both the application object and a service principal for it. In any other tenant that uses a multitenant app, there is no application object, only a service principal, provisioned when that tenant first consents to the app.

### What is the difference between an app registration and an enterprise application?

The app registration is the application object, the global definition that lives in the app's home tenant and describes what the app is and can request. The enterprise application is the service principal, the local instance in a given tenant that signs in, holds role assignments, and records consent. One definition, one instance per tenant.

That distinction sounds academic until it changes what you do. Suppose you edit the app registration and add an app role, then check the enterprise application and the role is there too, because in the home tenant they sit on top of the same underlying pair. Now suppose you edit a property that belongs to the service principal, such as a tag used for assignment, or you assign a user to the enterprise application. That assignment lives on the service principal and does not appear on the application object, because the application object is the definition and assignment is an instance concern. The most common waste of an afternoon in this area is editing one object while watching the other for a change that will never show up there.

### Why does editing the registration not change the service principal?

Because the registration is the definition and the service principal is the instance. Definition properties (credentials, declared permissions, exposed scopes) live on the application object. Instance properties (user and group assignments, local role grants, recorded consent) live on the service principal. Changing one does not retroactively rewrite the other unless the change is to a shared, propagated property.

There is a precise way to see the two objects with the Microsoft Graph PowerShell module, and seeing them side by side cements the model better than any diagram.

```powershell
# Connect with permission to read applications and service principals
Connect-MgGraph -Scopes "Application.Read.All"

# The application object: the global definition
Get-MgApplication -Filter "displayName eq 'InsightCrunch Reporting API'" |
    Select-Object DisplayName, AppId, Id, SignInAudience

# The service principal: the local instance in this tenant
Get-MgServicePrincipal -Filter "displayName eq 'InsightCrunch Reporting API'" |
    Select-Object DisplayName, AppId, Id, ServicePrincipalType
```

Notice that both objects share the same AppId (the client ID) but each has its own Id (object ID). The shared AppId is the thread that ties the definition to its instances: it is the value an app presents when it requests a token, and the directory uses it to find the right service principal in the tenant that is being signed in to. The separate object IDs are how the directory keeps the global definition distinct from the local identity. When a command or a script asks for an object ID, the first question to ask is which object it wants, the application or the service principal, because passing the wrong one is a frequent and quiet source of failure.

The home tenant relationship is worth stating plainly. When you register a single-tenant application, Entra ID writes an application object and a service principal in your tenant, and your application uses both without you thinking about the split. When you register a multitenant application and another organization signs in to it for the first time, that organization gets a service principal for your app in their tenant, while the application object stays only in yours. This is why a multitenant app provisions a service principal per consuming tenant: the definition is published once, and each tenant materializes its own local instance to hold its own consent and its own assignments. The same idea applies to the Microsoft-published applications you see in your Enterprise applications list that you never registered. Those are service principals for first-party and gallery applications whose application objects live elsewhere, and your tenant holds only the instance.

## The InsightCrunch Registration Model Map

Before going deeper into credentials and permissions, fix the whole structure in one reference. The table below is the InsightCrunch registration model map, the findable artifact for this article. It names every part of an app registration, says which of the two objects owns it, and states what that part is for. When a setting confuses you later, return here first and ask which object you are actually touching.

| Part | Owning object | What it is and what it controls |
|------|---------------|----------------------------------|
| Application (client) ID | Application object (shared with service principal) | The stable identifier the app presents when requesting a token. Same value on the definition and every instance. |
| Object ID (application) | Application object | The directory key for the global definition. Used in Graph calls that read or modify the registration. |
| Object ID (service principal) | Service principal | The directory key for the local instance. Used for role assignments, consent, and sign-in records. |
| Display name | Both | The human label. Editing it on the registration in the home tenant updates the paired service principal. |
| Sign-in audience | Application object | Who may sign in: this tenant only, any organization, or any organization plus personal accounts. Drives multitenancy. |
| Redirect URIs | Application object | The vetted return addresses for authorization responses. A mismatch produces a redirect-URI error at sign-in. |
| Client secrets | Application object (credentials) | Shared-string credentials the confidential client uses to prove itself. Portal lifetime capped at 24 months. |
| Certificates | Application object (credentials) | Asymmetric key credentials, stronger than secrets, recommended for production confidential clients. |
| Federated credentials | Application object (credentials) | Trust to an external issuer (such as a CI provider or another cloud) so the app authenticates with no stored secret. |
| API permissions (delegated) | Application object declares; service principal holds the grant | What the app may do on behalf of a signed-in user, bounded by that user's own rights. |
| API permissions (application) | Application object declares; service principal holds the grant | What the app may do as itself with no user present. Requires administrator consent. |
| Exposed API and scopes | Application object | The permissions your own API publishes for other apps to request (the api node and oauth2PermissionScopes). |
| App roles | Application object | Roles your app defines, assignable to users, groups, or other applications, surfaced as a roles claim in the token. |
| User and group assignments | Service principal | Who is assigned to the app, and whether assignment is required to sign in. An instance concern, not a definition concern. |
| Consent records | Service principal | The record, per tenant, of which permissions were granted and by whom (user consent or admin consent). |
| Manifest | Application object | The JSON view of the definition. Now the Microsoft Graph app manifest format after the older Azure AD Graph format was retired. |

Two columns in that table do the heavy lifting. The owning-object column tells you where to go to make a change. The description column tells you what breaks if the change is wrong. Keep both in view and the rest of this article is detail hung on a frame you already hold.

### The manifest, and why it looks different than older guides

The manifest is the application object expressed as JSON. Anything you can set through a tile in the portal is also a property in the manifest, and a few properties can only be set by editing the manifest directly. If you follow older walkthroughs, be careful here, because Microsoft retired the Azure AD Graph manifest format and the portal now shows the Microsoft Graph app manifest. Several attributes were renamed or relocated in that change. The clearest example engineers hit is the access token version. The attribute that older guides call `accessTokenAcceptedVersion` at the root of the manifest is now `requestedAccessTokenVersion` and it sits inside the `api` node. Set it to 2 when you want v2.0 tokens.

```jsonc
// Microsoft Graph app manifest (excerpt), current format
{
  "appId": "11111111-2222-3333-4444-555555555555",
  "signInAudience": "AzureADMyOrg",
  "api": {
    "requestedAccessTokenVersion": 2,
    "oauth2PermissionScopes": [ /* the scopes your API exposes */ ]
  },
  "web": {
    "redirectUris": [ "https://app.insightcrunch.example/auth/callback" ]
  },
  "appRoles": [ /* the roles your app defines */ ]
}
```

The takeaway is not the specific attribute name. It is that the manifest is a moving schema, the property locations change over time, and a value copied from a years-old blog can fail to load or land in the wrong place. When a manifest edit does not take, verify the current attribute name and node against current Microsoft documentation before assuming the value is wrong, because the schema may simply have moved underneath the guide you are following. Flag this for re-verification before publishing anything that depends on a specific manifest attribute, since the format continues to evolve.

## Credentials: How an Application Proves It Is Itself

A confidential client (a web app, a daemon, an API calling another API) authenticates to Entra ID with a credential that proves it is the holder of the registration. There are three kinds, and the choice among them is one of the most consequential security decisions you make on a registration. The credential is the thing an attacker wants, because whoever holds it can become the application, and the application may hold permissions far beyond any single user.

The first kind is the client secret, a generated string the app sends to the token endpoint. It is the easiest to set up and the weakest to operate. A secret is a shared symmetric value, which means a copy exists wherever the app runs and wherever it was configured, and any copy can be exfiltrated. Through the portal the maximum lifetime you can set is 24 months, and the option to create a non-expiring secret was removed for security reasons. You can create a longer-lived secret with the Microsoft Graph API or PowerShell, but doing so trades a future incident for present convenience and is the opposite of the direction the platform pushes you. Microsoft's own guidance is to keep secret lifetimes short, often under six months, and to rotate.

```bash
# Create a client secret with a defined lifetime (Azure CLI)
az ad app credential reset \
  --id 11111111-2222-3333-4444-555555555555 \
  --display-name "reporting-api-2024-q1" \
  --years 1

# The output includes the secret value exactly once.
# It is never retrievable again. Capture it now or rotate again.
```

The second kind is the certificate, an asymmetric key credential. The app holds the private key and registers the public key on the application object. When it authenticates, it signs a token request with the private key rather than sending a shared string, so the secret material never leaves the app and never travels to the token endpoint. This is stronger than a client secret and is the recommended choice for production confidential clients. The operational cost is that you must manage the certificate lifecycle: issuance, secure storage of the private key, rotation before expiry, and revocation if compromised. Storing the private key in Azure Key Vault and letting the application read it through a managed identity removes the last copy of a long-lived secret from your app configuration.

The third kind is the federated credential, and it is the one that ends the credential-rotation treadmill entirely. Instead of storing any secret, you configure the registration to trust tokens issued by an external identity provider, such as a GitHub Actions workflow, a Kubernetes service account, or another cloud's identity service. The external system presents its own token, Entra ID validates it against the configured trust, and issues an access token without the app ever holding a secret of its own. For the pipeline case specifically, this is the foundation of workload identity federation and the reason a modern CI workflow can deploy to Azure with no secret in the repository or the runner.

### Which credential type should a registration use?

Prefer a federated credential when the workload runs somewhere that can present its own trusted token, because there is no secret to leak or rotate. Use a certificate for confidential clients that need a stored credential, since the private key never leaves the app. Use a client secret only for low-risk or short-lived cases, and rotate it.

The reason credential failures feel mysterious is that the symptom appears far from the cause. A secret expires at 2 a.m., the app keeps running on a cached token for an hour, and then every downstream call starts failing with an authentication error that points at the resource, not at the credential. The fix is not to chase the resource. It is to check the credential's expiry on the application object, and the prevention is to alert on upcoming expiry and to move off shared secrets where you can. This same pattern (a credential problem surfacing as a downstream authorization failure) is exactly what the [managed identity token failure guide](/2023/01/23/fix-managed-identity-token-error/) walks through for the identity-based case, and the diagnostic instinct transfers directly: trace the failure back to the credential, not the resource that reported the error.

There is a deeper point here about why secrets accumulate. When an application permission returns an error, a tired engineer often adds a new secret or a broader credential to rule out the credential as the cause, then forgets to remove it. Over months, a registration grows a drawer of secrets nobody can account for, each one a live key. The single best habit is to treat every credential on a registration as something that must have a named owner and a rotation date, and to delete anything that fails that test.

## Certificates and Key Vault: Removing the Last Stored Secret

Choosing a certificate over a client secret is the right call for a production confidential client, but the choice only pays off if the private key is handled well, because a certificate whose private key sits in a config file or a build artifact is no safer than the secret it replaced. The operational goal is to ensure no long-lived private key lives anywhere a person or a pipeline could copy it, and Azure Key Vault paired with a managed identity is the pattern that gets there.

The shape is straightforward to describe. The certificate's public key is registered on the application object as a key credential, so the directory can validate the app's signed token requests. The private key lives in Key Vault, never exported, and the application reads it at runtime through a managed identity assigned to the host. The application therefore holds no stored credential of its own; it borrows the certificate from the vault using an identity that itself has no secret, which collapses the chain of copyable keys down to nothing the app persists. When the certificate nears expiry, you rotate it in the vault and register the new public key on the registration, and the rotation touches the vault and the application object rather than every place the app runs.

### How do I avoid storing a private key in my application?

Keep the certificate's private key in Azure Key Vault and let the application read it at runtime through a managed identity assigned to its host. Register only the public key on the app registration. The app then holds no stored credential, because it borrows the key through an identity that has no secret of its own, which removes the copyable key from your configuration.

The lifecycle discipline matters as much as the storage choice. Set a rotation cadence shorter than the certificate's validity so a rotation always happens before an expiry forces one, automate the rotation through the vault where the platform supports it, and alert on the registration's key-credential expiry the same way you would on a secret. Revocation has to be part of the plan too: if a key is suspected compromised, you remove its public key from the registration to stop the directory from accepting tokens signed with it, then rotate. The difference between a certificate that improves your posture and one that merely looks better than a secret is entirely in this handling, so treat the storage, rotation, and revocation steps as the actual work and the choice of credential type as only the first decision.

There is a clean way to see the registered key credential and its expiry, which is the check that catches a certificate drifting toward an unplanned expiry. Reading the key credentials on the application object shows each registered public key, its type, and its end date, so an automated job can flag any credential approaching its limit well before it lapses and takes the application's authentication down with it. Pairing this check with the secret-expiry check from the verification routine gives one combined view of every credential the registration depends on, which is the view an on-call engineer wants at the moment an authentication failure starts and the question is whether a credential just expired.

## API Permissions: Delegated, Application, and the Consent That Activates Them

Declaring a permission on a registration does nothing by itself. A permission is a request the registration makes, a statement of what the application would like to be able to do. It becomes real only when someone consents to it, and the consent is recorded on the service principal in the tenant where it was granted. This is the second place the two-object model decides outcomes: the registration declares, the instance is granted. An engineer who adds a permission in the portal and expects the app to work immediately has done half the job, because the declaration is in place but the grant is not.

There are two categories of permission, and confusing them is one of the most expensive mistakes in this entire area. A delegated permission is exercised on behalf of a signed-in user. The app acts as the user, and the effective access is the intersection of what the permission allows and what the user is themselves allowed to do. If a delegated permission lets the app read files, the app can read the files that the signed-in user can read, not every file in the organization. An application permission, by contrast, is exercised by the app as itself, with no user in the picture. The effective access is exactly what the permission grants across the whole tenant, bounded only by the permission's own scope. An application permission that reads files reads every file the permission covers, for everyone.

That difference is the entire security story. A delegated permission inherits the user's blast radius. An application permission has the app's blast radius, which is usually the whole directory. This is why application permissions require administrator consent and cannot be granted by an ordinary user: the platform refuses to let a single user authorize tenant-wide app access. It is also why so many over-privilege incidents start with an engineer switching a permission from delegated to application to make a daemon scenario work, without registering that they just changed the blast radius from one user to the entire organization.

### What is the difference between delegated and application permissions?

A delegated permission lets the app act for a signed-in user, limited to what that user can do. An application permission lets the app act as itself with no user, limited only by the permission's tenant-wide scope. Delegated inherits the user's reach. Application has the app's reach, which is why it needs admin consent.

Consent comes in two forms that mirror the two permission types. User consent is when a signed-in user agrees to let the app act on their behalf, possible for delegated permissions that the tenant allows users to consent to. Admin consent is when an administrator grants a permission for the whole tenant at once, required for application permissions and for any delegated permission the tenant has marked as needing admin approval. The practical signal is the Grant admin consent button in the API permissions screen. Until someone with the right role clicks it, an application permission is declared but inert, and the app keeps failing with an authorization error that has nothing to do with its credential and everything to do with the missing grant.

### Why does my app still get an authorization error after I added the permission?

Most often because the permission is declared on the registration but not yet consented on the service principal. Application permissions and admin-restricted delegated permissions need an administrator to grant consent before they take effect. Adding the permission and saving is not the same as granting it.

The relationship to the broader authentication flow matters here. A permission shows up in a token as a claim, either as scopes for delegated access or as roles for application access, and the app and the API both read those claims to decide what is allowed. The mechanics of how the token is requested, issued, and validated are covered in depth in the [Entra authentication walkthrough](/2023/12/18/entra-id-authentication-explained/); for the purpose of the registration, what matters is that the permission you declare and consent to is what ends up in the token, and an API that does not see the expected claim will reject the call no matter how the registration looks in the portal.

Applying least privilege to permissions is concrete, not aspirational. Start from the narrowest permission that accomplishes the task and widen only when a specific operation fails for a specific, understood reason. Prefer delegated over application whenever a user is present, because the user's own rights cap the damage. When an application permission is unavoidable, choose the most scoped variant the API offers; many APIs publish both a broad read-everything permission and a narrower variant limited to specific resources, and the narrow one closes most of the exposure. The following command grants and consents an application permission deliberately, which is the moment to ask whether the scope is the smallest that works.

```bash
# Grant an application (app-only) permission and admin-consent it (Azure CLI)
# Microsoft Graph appId is 00000003-0000-0000-c000-000000000000
az ad app permission add \
  --id 11111111-2222-3333-4444-555555555555 \
  --api 00000003-0000-0000-c000-000000000000 \
  --api-permissions df021288-bdef-4463-88db-98f22de89214=Role

# 'Role' marks it as an application permission; 'Scope' would mark delegated.
az ad app permission admin-consent \
  --id 11111111-2222-3333-4444-555555555555
```

The misconfiguration to watch for is the broad grant that nobody revisits. An app is built, an application permission like full directory read is granted to get past a deadline, the app ships, and the permission stays for years. If that app's credential leaks, the attacker inherits tenant-wide read access, not because the breach was sophisticated but because the registration was over-permissioned and never trimmed. The defense is a periodic review that asks, for every application permission on every registration, whether the app still uses it and whether a narrower permission would do. The secretless alternative, where an app uses a [managed identity instead of a registration with stored credentials](/2023/04/17/configure-managed-identities/), removes the credential-leak path entirely for workloads that run inside Azure, which is why it is the preferred pattern when the app does not need to be multitenant or run outside Azure.

## Exposing an API: Defining Your Own Scopes and App Roles

So far the registration has been a client, requesting access to other APIs. A registration can also be the resource, an API that other applications call and that needs to control what those callers may do. This is the expose-an-API side of the model, and it is where two distinct mechanisms live: scopes for delegated access and app roles for both delegated and application access. Engineers often reach for one when they need the other, so the distinction is worth drawing carefully.

When you expose an API, you first set an Application ID URI, a unique identifier for your API such as `api://11111111-2222-3333-4444-555555555555` or a verified custom domain form. This URI is the audience that tokens for your API will carry, and it is how a caller names your API when it requests a scope. Then you define what the API offers. A delegated scope (published in the manifest under `oauth2PermissionScopes` and shown in the portal under Expose an API) represents an action a calling app may perform on behalf of a signed-in user, such as `Reports.Read` or `Reports.Write`. A calling application requests these scopes, the user or an admin consents, and the issued token carries them in the `scp` claim. Your API reads `scp` and decides what the call may do.

An app role is different. App roles are defined on your API's application object under the `appRoles` collection, and they can be assigned to users and groups (surfacing as a `roles` claim in a user's token) or to other applications (surfacing as a `roles` claim in an app-only token). The application-assignable app role is how you grant another service application-level access to your API with no user present, the mirror image of the application permission discussed earlier, now seen from the resource side. When another app needs to call your API as itself, you define an app role on your API, the other app requests it as an application permission, an admin consents, and your API validates the `roles` claim.

### When do I use a scope versus an app role?

Use a delegated scope when a calling app acts on behalf of a signed-in user and you want to gate user-context actions. Use an app role when you need to assign access to a user, a group, or another application directly, especially for app-only (no user) access to your API. Scopes ride the user's session; app roles are assigned identities.

The validation step on the API side is where exposing an API is won or lost, and it is the part the portal cannot do for you. A correctly issued token is worthless if your API does not check it. Your API must validate the token's signature and issuer, confirm the audience matches your Application ID URI, and then enforce the specific `scp` or `roles` claim required for the operation. Skipping the claim check is a common and serious gap: an API that accepts any valid token from the tenant without checking which scope or role it carries has effectively published every operation to every caller who can get a token at all. The point of defining scopes and roles is to enforce them, and enforcement is code you write, not a setting you toggle.

```jsonc
// Validating the claim in your API (conceptual, framework-agnostic)
// 1. Verify signature, issuer, and that 'aud' == your Application ID URI.
// 2. For delegated calls, require the scope:
//      token.scp contains "Reports.Read"   -> allow the read operation
// 3. For app-only calls, require the role:
//      token.roles contains "Reports.Read.All" -> allow the read operation
// 4. If the required claim is absent, reject with 403, not 401.
```

A subtle design choice sits inside the audience version. Tokens come in v1.0 and v2.0 shapes, and the `requestedAccessTokenVersion` attribute in the `api` node of your manifest controls which version your API receives. Mixing expectations here, where the API library expects v2.0 claims but the registration still issues v1.0 tokens, produces validation failures that look like the caller's fault when the cause is the resource registration's token version. Set the version deliberately and make sure your validation library agrees with it.

The least-privilege principle applies on the resource side too. Publish scopes and roles that match real operations rather than one all-encompassing scope that gates everything, because a coarse scope forces callers to request more than they need and removes your ability to grant a partner read without also granting write. A well-designed API publishes a small set of named, operation-aligned scopes and roles, which lets every caller request the minimum and lets you reason about who can do what by reading the assignments.

## Single-Tenant Versus Multitenant: The Audience Decision

The sign-in audience on the application object decides who, across the whole identity ecosystem, is allowed to use the app. It is a single setting with large consequences, and it is the property that turns the two-object model from an abstraction into a daily operational reality, because the audience is what determines how many service principals your one application object will spawn.

There are a few audience values, and they correspond to widening circles of who may sign in. The narrowest is single tenant (`AzureADMyOrg`), meaning only identities in the app's home tenant can use it. The next is multitenant (`AzureADMultipleOrgs`), meaning any Microsoft Entra organization can use it. Wider still is the value that also admits personal Microsoft accounts (`AzureADandPersonalMicrosoftAccount`), and there is a personal-accounts-only value for consumer scenarios. The choice is not cosmetic. It changes the authority your app signs in against, the consent experience other organizations see, and, most importantly for operations, where service principals get created.

For a single-tenant app, the picture is simple: one application object and one service principal, both in your tenant, and nothing is provisioned anywhere else. For a multitenant app, the application object stays in your home tenant alone, but a service principal is created in every other tenant that consents to your app. This is the fact engineers find surprising the first time they see it: your one registration produces a service principal in each consuming organization's directory, and each of those instances holds that organization's own consent and assignments independently. Your application object is the single published definition; the consuming tenants each materialize their own local instance.

### Why does a multitenant app create a service principal in every tenant?

Because each tenant needs a local identity to hold its own consent, assignments, and policy for your app, and that local identity is the service principal. Your application object is published once in your home tenant. When another tenant first consents, Entra ID provisions a service principal there so that tenant can govern the app independently. One definition, many instances.

The operational consequences follow directly from that fact. Consent is per tenant, so granting admin consent in your home tenant does nothing for a customer's tenant; their administrator must consent for their organization, on their own service principal. Conditional access and assignment are per tenant, so each organization controls how its users reach your app. And revocation is per tenant, because a customer can delete their service principal for your app to cut it off entirely without touching your registration or any other customer's instance. If you build a multitenant app, you are not deploying one identity, you are publishing a definition that becomes an independent identity in every customer directory, and your support model has to account for that.

Choosing the audience is a security decision before it is a distribution decision. Multitenant is necessary when you genuinely sell or share the app across organizations, but it widens who can request your app and provision an instance of it, so it should be chosen on purpose, not inherited from a sample that happened to set it. If the app only ever serves your own organization, single tenant is the smaller exposure and the right default. Widening the audience later is a deliberate change with a clear reason, not a setting to leave open in case it is needed someday.

There is a redirect-URI angle to the audience too. The redirect URIs on the registration are the only return addresses the authorization endpoint will honor, and they must match exactly, including scheme and path. A multitenant app still has one set of redirect URIs on its single application object, so the return addresses are shared across all consuming tenants. A mismatch here produces the redirect-URI error that stops sign-in cold, and it is a registration-side problem (the URI is not in the allowed list) rather than a consent or permission problem, which is why it resists the usual permission-focused troubleshooting.

## The Common Misconfigurations and the Breaches They Enable

Every misconfiguration in this area maps back to the two-object model, the permission model, or the credential model, and naming them as patterns makes them easier to catch before they become incidents. Treat the following as the recurring cases engineers report, each one a predictable result of the model being misread.

The first is conflating the application object with the service principal. The symptom is editing one and expecting the other to change: assigning users to the enterprise application and wondering why the registration's manifest does not show them, or adding an app role to the registration and looking for it under the wrong object. The fix is always to ask which object owns the setting and go there, using the model map above. The cost is usually wasted time rather than a breach, but it also produces wrong conclusions, such as deciding a permission is broken when it was simply declared on the definition and never consented on the instance.

The second is the secret that expires unnoticed. A registration carries a client secret with a 24-month maximum, the team forgets it, and one day the app stops authenticating with an error that points downstream. The breach risk is indirect but real: the scramble to fix it often produces a hastily created long-lived secret that then becomes the unmanaged credential nobody rotates. The fix is to alert on credential expiry well ahead of the date and, where possible, to move to certificates or federated credentials so there is no shared secret to expire in the first place.

The third is the application permission granted to silence an error. An app fails with an authorization error, an engineer grants a broad application permission and admin-consents it, the error goes away, and the broad grant stays forever. The breach this enables is severe: if the app's credential leaks, the attacker inherits the app's tenant-wide access, and a full directory read or write permission turns a single leaked secret into an organization-wide compromise. The fix is to grant the narrowest permission that works, prefer delegated where a user is present, and review application permissions on a schedule, removing any the app no longer exercises.

### How do over-permissioned registrations turn into breaches?

A registration with a broad application permission holds tenant-wide access that does not depend on any user. If its credential leaks, the attacker becomes the app and inherits that access directly. The breach scales with the permission, so a full read-write grant turns one leaked secret into directory-wide compromise. Narrow permissions and short credentials limit the blast radius.

The fourth is the exposed API that does not validate claims. An API publishes scopes and roles but accepts any valid tenant token without checking which scope or role it carries. The result is that every operation is open to every caller who can authenticate at all, which defeats the entire point of defining scopes. The fix is to enforce the specific `scp` or `roles` claim on every protected operation and to reject calls that lack it. The fifth is choosing a client secret where a certificate or federated credential belongs, accepting a weaker, copyable credential for a production confidential client out of convenience; the fix is to match the credential strength to the exposure, which almost always means a certificate or federated credential for anything that runs in production.

## How to Verify the Posture of a Registration

A registration that looks correct in the portal can still be wrong in ways the portal does not surface at a glance. Verifying the posture means checking the three models directly: which credentials exist and when they expire, which permissions are declared and which are actually consented, and which audience and assignments are in force. Each check answers a question an attacker would also ask, so doing them yourself first closes the gap before someone else finds it.

Begin with credentials, because they are the most direct path to becoming the app. List every secret and certificate on the registration and confirm each has a known owner and a near-term expiry, and treat any credential nobody can account for as a finding to remove. The following enumerates credentials and their end dates so you can spot the long-lived or orphaned ones.

```powershell
# Audit credentials on a registration: secrets and certificates with expiry
$app = Get-MgApplication -Filter "appId eq '11111111-2222-3333-4444-555555555555'"

$app.PasswordCredentials | Select-Object KeyId, DisplayName, StartDateTime, EndDateTime
$app.KeyCredentials      | Select-Object KeyId, DisplayName, Type, EndDateTime
```

Next, verify permissions against consent, which is the check that catches both the inert permission and the over-broad grant. The permissions declared on the application object are only requests; the grants recorded on the service principal are what is real. Comparing the two tells you whether a permission is missing its consent (the app will fail) or whether a broad application permission is consented and live (the exposure to review). Reading the service principal's app-role assignments shows the application permissions that are actually granted in the tenant.

```powershell
# What application permissions are actually granted (consented) on the instance
$sp = Get-MgServicePrincipal -Filter "appId eq '11111111-2222-3333-4444-555555555555'"

Get-MgServicePrincipalAppRoleAssignment -ServicePrincipalId $sp.Id |
    Select-Object ResourceDisplayName, AppRoleId, PrincipalDisplayName
```

### How can I tell whether a permission is actually granted?

Check the service principal, not the registration. The registration's API permissions list shows what the app declared; the service principal's consented grants (delegated grants and app-role assignments) show what is real in the tenant. A permission that appears on the registration but not in the service principal's grants is declared but not consented, and the app will fail when it tries to use it.

Then verify the audience and assignment posture. Confirm the sign-in audience matches the intended reach (single tenant unless multitenancy is a deliberate requirement), confirm whether assignment is required so that only assigned users and groups can sign in, and for a multitenant app, understand that each consuming tenant governs its own instance and that your checks in the home tenant say nothing about theirs. Finally, confirm the redirect URIs are exactly the addresses you expect and contain no stale or wildcard-like entries that widen where authorization responses can be sent.

The discipline that ties these checks together is to verify the instance, not just the definition. The registration is the story the app tells about itself; the service principal is what the tenant actually granted and enforces. Posture lives on the instance, so when in doubt, read the service principal. This is the same instinct that the model map encodes, applied as a security routine rather than a troubleshooting one.

## Making Registrations Auditable and Repeatable

A registration created by hand in the portal is a snapshot with no history. Six months later, nobody remembers who added which permission or why a particular secret exists, and the only record is the current state. The way out is to define registrations as code and to govern them with policy, so that the configuration is reviewable, reproducible, and constrained by rules the platform enforces rather than habits people remember.

Defining the registration as code means expressing the application object and its service principal in a template or module, so the permissions, exposed scopes, app roles, and redirect URIs live in version control where changes are reviewed and history is preserved. The exact tool matters less than the property: a registration in code is a registration you can diff, review, and recreate identically, and a permission added in a pull request is a permission someone approved on the record. The infrastructure-as-code approach turns the registration from a mutable portal artifact into a managed resource, which is the same shift this series argues for across every configurable Azure object.

The governance layer is application management policy, which lets you enforce credential standards across the tenant rather than hoping each team follows them. A tenant-wide policy can cap the maximum lifetime of client secrets, disallow password credentials entirely in favor of certificates and federated credentials, or require that new applications meet a standard from a chosen date forward. Because the policy is enforced by the platform, it closes the gap between the rule you wrote in a wiki and the configuration that actually exists, which is exactly where long-lived secrets and over-broad grants tend to hide.

### How do I keep registrations from drifting out of compliance?

Define them as code so every change is reviewed and reproducible, and apply application management policies so the platform enforces credential standards (such as a maximum secret lifetime or a ban on password credentials) tenant-wide. Code gives you history and review; policy gives you enforcement that does not depend on anyone remembering the rule.

Auditability also means watching the right signals over time. The sign-in logs and audit logs on the service principal record who signed in, what consent was granted and by whom, and what changed on the instance, and reviewing those signals on a schedule catches the secret added out of process or the consent granted to an app nobody recognizes. Pair the code definition with the policy enforcement and the periodic review, and a registration stops being a thing that quietly accretes risk and becomes a managed identity surface you can reason about.

To run, reproduce, and inspect any of this against a live tenant, [work through the hands-on Azure labs and command library on VaultBook](https://vaultbook.net/tools/azure-labs.html), where you can register an app, expose an API with custom scopes, grant and consent permissions, and inspect the resulting service principal end to end, which turns the model in this article into muscle memory faster than reading alone.

## How the Registration Feeds Each Authentication Flow

The pieces on a registration are not decoration. Each authentication flow consumes a specific subset of them, and knowing which flow your app uses tells you which registration settings have to be right. When an app fails to get a token, the fastest diagnosis is to name the flow and then check the exact registration parts that flow depends on, rather than scanning the whole registration for anything that looks off.

The authorization code flow is what interactive web apps and single-page apps use. A user signs in, the authorization endpoint returns a short-lived code to a redirect URI, and the app exchanges that code for tokens at the token endpoint. This flow leans on the redirect URIs (the code goes to one of them, and a mismatch stops the flow), the requested delegated scopes (which decide what the resulting token can do), and, for a confidential web app, the credential used at the code-for-token exchange. Single-page apps run this flow with PKCE and register their redirect URIs under the single-page application platform rather than the web platform, a distinction that matters because the platform type changes how the redirect and the token request are treated.

The client credentials flow is the no-user flow, used by daemons, background services, and one API calling another as itself. There is no user and no redirect; the app authenticates with its credential and receives a token whose access comes entirely from application permissions and app-role assignments. This flow depends on the credential being valid and on the application permissions being not just declared but consented by an administrator. The recurring failure here is the daemon that authenticates fine (the credential works) but is refused by the resource (the application permission was never admin-consented), which again separates the credential question from the grant question.

### Which flow does my application use?

An interactive app where a user signs in uses the authorization code flow and depends on redirect URIs and delegated scopes. A background service with no user uses the client credentials flow and depends on its credential and admin-consented application permissions. An API calling another API on behalf of the original user uses the on-behalf-of flow. Name the flow first; it tells you which registration parts must be correct.

The on-behalf-of flow handles the chain where a user calls API A, and API A must call API B as that same user. API A takes the user's token, exchanges it at the token endpoint using its own credential, and receives a new token for API B that still represents the user. This flow needs API A to hold a delegated permission to API B, needs that permission consented, and needs API A's own credential for the exchange. It is the flow behind most multi-tier applications, and its failures usually trace to a missing delegated permission or consent between the middle tier and the downstream API rather than to anything visible at the front door.

The device code flow serves input-constrained devices and command-line tools that cannot host a browser redirect. The app shows a code and a URL, the user authenticates on a separate device, and the app polls for the token. It relies on the registration being marked to allow public client flows, a setting that lives on the registration and that, when missing, produces a failure that looks like a protocol error but is in fact a single unset toggle. Across all of these, the pattern holds: the flow names the registration parts that matter, so identify the flow and check exactly those parts.

A worked example makes the dependency concrete. Consider a background job that reads mailboxes across the tenant. It uses the client credentials flow, so it needs a valid credential and an admin-consented application permission to read mail. Suppose the job authenticates and then fails when it tries to read a mailbox. The credential is fine, because authentication succeeded. The flow tells you to check the application permission and its consent next, and there you find the permission declared on the registration but never granted by an administrator on the service principal. The flow turned a vague failure into a single, specific check.

```bash
# Confirm the client-credentials path: token acquisition is one question,
# resource authorization is another. This requests a token (auth side only).
curl -s -X POST \
  "https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token" \
  -d "client_id=11111111-2222-3333-4444-555555555555" \
  -d "scope=https://graph.microsoft.com/.default" \
  -d "client_secret=<secret>" \
  -d "grant_type=client_credentials"
# A token here proves the credential is valid. A 403 from the resource
# afterward points at the missing application-permission grant, not the token.
```

## Redirect URIs and Platform Configuration

Redirect URIs decide where the authorization endpoint is allowed to send a response, and they are both a functional requirement and a security boundary. Functionally, the URI the app uses at sign-in has to be on the registration's allowed list or the request is refused before the user ever authenticates. As a boundary, the list is what stops an attacker from redirecting authorization responses to a destination they control, which is why the matching is strict and why a wildcard or an overly broad entry is a real exposure rather than a convenience.

The matching is exact. The scheme, host, port, and path all have to match what the app sends, with only narrow exceptions the platform documents for specific cases. A registration configured with an `https` redirect that the app sends as `http`, or a path that differs by a trailing segment, produces the redirect-URI error that halts sign-in. This is a registration-side failure (the address is simply not on the list) and not a permission or consent problem, which is why it resists permission-focused troubleshooting and why the first check on a redirect-URI error is always the literal string comparison between what the app sends and what the registration allows.

Redirect URIs are grouped by platform, and the platform type changes the rules. The web platform is for confidential clients that exchange the code using a credential. The single-page application platform is for browser apps that use the authorization code flow with PKCE and cannot hold a secret. The public client and mobile and desktop platform is for native apps and tools that also cannot keep a secret and that often use loopback or custom-scheme redirects. Registering a URI under the wrong platform is a quiet cause of failure: the same string under the web platform and under the single-page application platform behaves differently, because the platform decides whether a secret is expected and how the token request is validated.

### Why do I get a redirect URI mismatch error?

Because the redirect address the app sends does not exactly match an address on the registration's allowed list. Matching is strict on scheme, host, port, and path. The fix is a literal string comparison between what the app requests and what the registration permits, and confirming the URI is registered under the correct platform (web, single-page application, or public client).

The least-privilege idea applies to redirect URIs as much as to permissions. Keep the list to the exact addresses the app actually uses, remove stale entries from old environments, and never widen an entry to cover a range of destinations to save configuration effort, because each allowed address is a place an authorization response can legitimately be sent. A registration with a tidy, exact redirect list is one fewer thing an attacker can abuse and one fewer source of the sign-in failures that look mysterious until you compare the strings.

## Consent in Depth: the Framework and the Attack It Invites

Consent is the mechanism that turns a declared permission into a real grant, and it is also, when misgoverned, one of the more dangerous surfaces in the identity model, because a consent decision can hand an application standing access to data with a single click. Understanding the consent framework is therefore both an operational necessity and a security control, not a detail to skip past on the way to making an app work.

User consent is when a signed-in user agrees to let an application act on their behalf for delegated permissions. Whether a user can consent at all, and to which permissions, is governed by tenant settings that range from allowing user consent for permissions classified as low risk, to allowing it only for verified publishers, to disabling user consent entirely so that every grant goes through an administrator. Tightening user consent is one of the highest-value identity hardening steps a tenant can take, because it closes the path by which an individual user can grant a third-party application access to their data without anyone reviewing the request.

Admin consent is when an administrator grants a permission for the whole tenant, required for all application permissions and for any delegated permission the tenant has classified as needing approval. Because admin consent applies tenant-wide, it carries weight and deserves a process. The admin consent workflow lets users request access to an application and routes the request to designated reviewers, which replaces the pattern where a user hits a consent wall, gives up, and files a ticket that an administrator approves without much scrutiny. A reviewed request is a chance to ask whether the application is trustworthy and whether the permissions it wants are the minimum it needs.

### What is admin consent and when is it required?

Admin consent is an administrator granting a permission for the entire tenant at once. It is required for all application permissions and for any delegated permission the tenant has marked as admin-restricted. Until an administrator grants it, the permission is declared on the registration but inert, and the application fails with an authorization error unrelated to its credential.

The attack this framework invites is the illicit consent grant, sometimes called consent phishing. An attacker registers an application, often with a name that imitates something familiar, and sends users a link that asks them to consent to delegated permissions such as reading their mail or files. If the user consents and the tenant allows user consent, the attacker's application now holds a standing OAuth grant to that user's data, and the grant survives password changes because it is not a password; it is a token-issuing relationship recorded on a service principal. This attack bypasses many traditional defenses precisely because the user authorized it through a legitimate mechanism. The defenses are to restrict user consent so risky grants require admin review, to use the admin consent workflow so requests are scrutinized, and to review the applications that hold consent in the tenant on a schedule, looking for unfamiliar applications or permissions that do not match a known need.

Reviewing existing consent is a posture check worth running periodically. The service principals in the tenant that hold delegated grants and application-permission assignments are the full list of applications that can act in the directory, and an unfamiliar entry there, especially one with broad permissions and a recent creation date, is exactly what a consent-phishing investigation looks for. Treat the consented-application inventory as a security asset, not a byproduct, and the consent framework becomes a control you operate rather than a mechanism that operates on you.

## The Authorities: Where Sign-In Actually Happens

Every token request goes to an authority, the endpoint that authenticates the caller and issues the token, and the authority your app uses interacts with the sign-in audience on the registration. Getting these two to agree is a common stumbling point, because an audience that allows broad sign-in paired with an authority that scopes it narrowly, or the reverse, produces failures that read like permission problems but are in fact authority-and-audience mismatches.

The common authority accepts sign-ins from any organization and, depending on the exact endpoint, personal accounts, and it pairs with a multitenant audience. The organizations authority accepts any Microsoft Entra organization but not personal accounts. The consumers authority is for personal accounts only. A tenant-specific authority, which names a particular tenant by its identifier or domain, scopes sign-in to that one tenant and pairs naturally with a single-tenant audience. The rule that prevents a class of failures is that the authority and the audience must be compatible: a single-tenant registration signed in against the common authority, or a multitenant app that hard-codes one tenant's authority when it needs to serve many, will fail in ways that look puzzling until you line the two up.

For a multitenant app specifically, the authority choice has an operational meaning. Signing in against the common authority lets users from any organization reach the app and triggers the per-tenant service principal provisioning described earlier, while signing in against a specific tenant's authority restricts that particular sign-in to that tenant. Multitenant applications usually sign in against the common or organizations authority to admit users broadly, then rely on per-tenant consent and assignment to govern what each organization's instance can do. The authority is the front door, the audience on the registration decides who the door admits, and the per-tenant service principal is what each admitted organization governs once inside.

## Reading the Recurring Scenarios Through the Model

The value of the definition-versus-instance rule is that it explains the cases engineers actually hit, turning each from a surprise into a predictable result. Walking the recurring scenarios through the model is the fastest way to internalize it, because each one is the model applied to a situation rather than a separate fact to memorize.

The first scenario is editing the registration and expecting the change on the enterprise application. An engineer assigns users to the enterprise application, then opens the registration's manifest to confirm and finds nothing. The model explains it immediately: assignment is an instance property held on the service principal, and the registration is the definition, so the assignment was never going to appear there. The resolution is not to keep looking but to go to the object that owns the property.

The second scenario is the expiring client secret. An app that has run for months suddenly fails with a downstream authorization error. The model says the credential lives on the application object and that a credential failure surfaces as a downstream symptom, so the check is the secret's expiry on the registration, not the resource that reported the error. The prevention, alerting on expiry and moving to a certificate or federated credential, follows from the same understanding of where the credential lives and why a shared secret is the weakest option.

### Why does my daemon authenticate but still get denied?

Because authentication and authorization are separate questions in the client credentials flow. A valid credential gets the app a token, which is the authentication side. The resource then checks for an admin-consented application permission, which is the authorization side. A daemon that authenticates but is denied has a valid credential and a missing or unconsented application permission, so the fix is on the grant, not the credential.

The third scenario is the application permission that needs admin consent. A daemon gets a token but the resource refuses it. The model separates authentication from authorization: the credential worked, so the problem is the grant, and an application permission is inert until an administrator consents to it on the service principal. The fourth is exposing an API with custom scopes and finding callers can do more than intended, which the model explains as a missing claim check on the API side, since publishing a scope does nothing unless the API enforces it. The fifth is the multitenant app provisioning a service principal in each tenant, which the model predicts exactly: one application object in the home tenant, one independent service principal per consuming tenant. The sixth is choosing a certificate over a secret for a production confidential client, which the model frames as matching credential strength to exposure. Each scenario is the same small rule applied to a new situation, which is why holding the rule is worth more than memorizing the cases.

## Service Principal Types and the Objects You Did Not Create

Open the Enterprise applications list in any established tenant and you will see entries you never registered, often dozens of them. These are service principals whose application objects live elsewhere, and understanding the categories explains why your tenant holds identities for software you never installed. The service principal carries a type that names its origin, and reading that type tells you what kind of object you are looking at and how it got there.

An application-type service principal is the instance of an application object, whether that object is yours (a registration you created) or someone else's (a multitenant or first-party application your tenant consented to). A managed-identity-type service principal is the identity behind an Azure managed identity, created when you enable a managed identity on a resource; it has a service principal in the directory but no app registration you manage, which is precisely the property that makes managed identities secretless. Legacy and other types cover older or special-purpose principals. The point of the type field is orientation: when a principal surprises you, its type usually explains its provenance before you investigate further.

First-party applications are Microsoft's own, and their service principals appear in your tenant so that Microsoft's services can operate against your directory under identities you can see and, within limits, govern. Gallery applications are the pre-integrated third-party applications you add from the application gallery for single sign-on, each of which creates a service principal in your tenant from a publisher's application object. Your own registrations are the third category. Knowing which of the three a given enterprise application is tells you who owns its definition, whether you can edit its registration at all (you cannot edit the application object of a first-party or another publisher's app), and what your governance options are, which are mostly assignment, consent, and conditional access on the instance.

### Why are there enterprise applications I never registered?

Because they are service principals whose application objects live in another tenant. First-party Microsoft applications, gallery applications you added for single sign-on, managed identities, and multitenant apps you consented to all create a service principal in your directory while their definition stays elsewhere. Your tenant holds the instance to govern it, not the definition to edit it.

This is the two-object model at tenant scale. Your directory is full of instances whose definitions you do not own, and your control over each is the control the instance offers: who is assigned, what was consented, and what conditional access applies. The application object, where it even exists for you to see, is yours to edit only for your own registrations. Reading the enterprise applications list as a list of instances, each tied to a definition somewhere, turns a confusing inventory into a map you can reason about.

## What the Registration Puts Into a Token

A token is where the registration's choices become consequences, because the token is what the app presents and what the resource reads. Several token claims come straight from registration settings, and knowing the mapping lets you debug from the token backward to the registration rather than guessing.

The audience claim, `aud`, names who the token is for. For a token to your exposed API, it carries your Application ID URI or client ID, and your API must confirm the audience matches before trusting anything else in the token. A token whose audience is some other resource is not for you, and accepting it would be a serious validation gap. The audience traces directly to which resource the caller requested and to the Application ID URI you set when you exposed the API.

The scope claim, `scp`, lists the delegated permissions present in a user-context token, and the roles claim, `roles`, lists the app roles or application permissions in the token. These are the claims your code enforces: a delegated operation checks `scp`, an app-only operation checks `roles`, and the absence of the required claim is grounds to reject the call with a forbidden response rather than an unauthorized one, because the caller authenticated but lacks the specific grant. Both claims trace to what was declared on the registration and consented on the service principal, which closes the loop from registration to token to enforcement.

### Why does my API reject a token that signed in successfully?

Because authentication and authorization differ. A successful sign-in produces a valid token, but the token may lack the specific scope or role your API requires for the operation. The API should reject with a forbidden response when the required `scp` or `roles` claim is absent, even though the token itself is valid. Trace the missing claim to a declared-but-unconsented permission.

The version claim, `ver`, tells you whether the token is v1.0 or v2.0, and it ties back to the `requestedAccessTokenVersion` attribute in your registration's `api` node. A validation library configured for v2.0 claims that receives a v1.0 token, or the reverse, fails in ways that look like a malformed token when the cause is a version mismatch between the registration and the library. Optional claims, configured on the registration, let you enrich the token with additional information when an app genuinely needs it, but each added claim is more token to handle and should be added for a reason rather than by default. Reading a token, comparing its `aud`, `scp`, `roles`, and `ver` against what the registration declares, is the most direct debugging path in this entire subject, because the token is the registration's choices made visible.

## A Worked End-to-End Example

Concepts settle when they are assembled, so here is the whole model in one scenario: a client application that needs to call a custom API as a signed-in user, built from two registrations. The example names each step and the object it touches, so the two-object model is visible throughout rather than implied.

First, the API side. You register the API, which creates its application object and a service principal in your tenant. You set an Application ID URI to name the API, then expose a delegated scope, say `Reports.Read`, under the API's exposed permissions. This scope is published on the API's application object and is what callers will request. You also decide the token version in the `api` node so your validation library and the issued tokens agree. Nothing here is consented yet, because exposing a scope only publishes it; the grant happens on the calling side.

Second, the client side. You register the client application, which creates its own application object and service principal. On the client's API permissions, you add a delegated permission to the API's `Reports.Read` scope, which declares that the client wants to call the API on a user's behalf. Because this is a delegated permission, it may be grantable by user consent or may require admin consent depending on the tenant's settings. You configure the client's redirect URI under the correct platform for its type, and you give the client a credential if it is a confidential web app or none beyond PKCE if it is a single-page app.

Third, consent and the grant. When a user signs in to the client and the client requests the `Reports.Read` scope, the user or an administrator consents, and that consent is recorded on the client's service principal in the tenant. Now the declaration on the client's application object has a matching grant on its service principal, which is the condition that makes the permission real. If the tenant requires admin consent, the user hits a consent wall until an administrator grants it, the exact pattern that produces the authorization error so many engineers misread as a credential problem.

Fourth, the call and the enforcement. The client obtains a token for the API carrying the `Reports.Read` scope in its `scp` claim, with the `aud` claim set to the API's identifier. The client calls the API, and the API validates the token's signature, issuer, and audience, then checks that `scp` contains `Reports.Read` before serving the read. If the API skipped that claim check, any valid tenant token would pass, which is why enforcement on the resource side is the step that gives the published scope meaning. Every object touched in this walk maps to the model: two application objects (the definitions), two service principals (the instances), a scope published on one definition, a permission declared on the other and consented on its instance, and a token that carries the result to an API that enforces it.

This single example contains the whole subject. The definitions and instances are distinct. The credential proves the client is itself. The permission is declared on one side and granted on the other. The audience and scope land in the token. The API enforces the claim. Hold this walk in mind and the portal screens stop being a maze, because each one is a place to set one of these named parts, and you already know what each part is for.

## The Verdict on Microsoft Entra App Registrations

The whole subject collapses to one rule, and holding it is the difference between fighting the portal and predicting it. An app registration is the global definition of an application, the application object. The enterprise application is the per-tenant instance of that definition, the service principal. The registration declares what the app is, what credentials it holds, what permissions it requests, and what API it exposes. The service principal is what actually signs in, what holds the consent and the assignments, and what the tenant governs. When a setting confuses you, name the object it belongs to, go to that object, and the confusion resolves.

From that rule, the security posture follows. Prefer certificates or federated credentials over client secrets so there is no copyable, long-lived key to leak. Prefer delegated permissions over application permissions wherever a user is present so access is capped by the user's own rights, and when an application permission is unavoidable, grant the narrowest variant and consent it deliberately. Choose single tenant unless multitenancy is a real requirement, because the audience decides how widely your app can be provisioned. Validate the `scp` and `roles` claims on every API you expose, because publishing a scope you do not enforce is the same as publishing nothing. And make the whole thing auditable by defining it as code and governing it with application management policy, so the registration is reviewed, reproducible, and constrained rather than quietly accumulating risk. Get the definition-versus-instance rule right and everything else is detail; get it wrong and every other setting will mislead you.

## Frequently Asked Questions

**What is a Microsoft Entra app registration?**

An app registration is the global definition of an application in Microsoft Entra ID, stored as an application object in the app's home tenant. It holds the application (client) ID, the credentials the app uses to authenticate, the API permissions the app requests, the APIs and scopes the app exposes, the redirect URIs, and the sign-in audience that decides who may use it. The registration is the template from which the app's behavior derives, but it is not the identity that signs in. That identity is the service principal, a separate object. Registering an app in its home tenant creates both the application object and a paired service principal, which is why the two are easy to confuse. The clearest way to think about it is that the registration is the definition and the service principal is the instance, and almost every registration question becomes simpler once you know which of the two you are actually working with.

**What is the difference between an app registration and an enterprise application?**

They are two views of the same application but two different objects. The app registration is the application object, the global definition that lives once in the app's home tenant. The enterprise application is the service principal, the local instance of that definition inside a given tenant. The registration describes what the app is and can request; the enterprise application is what actually authenticates, holds role assignments and group memberships, records consent, and is targeted by conditional access and sign-in logs. In the app's home tenant, both exist and sit on top of each other, so changes can appear in both places. In any other tenant that uses a multitenant app, only the service principal exists, because the application object stays in the home tenant. Editing the registration when you meant to change the enterprise application, or the reverse, is the single most common source of confusion in this area, and naming which object you need fixes it.

**Why does editing the app registration not change the enterprise application?**

Because they own different properties. Definition properties, such as credentials, declared permissions, exposed scopes, and app roles, live on the application object (the registration). Instance properties, such as user and group assignments, consented permission grants, and recorded consent, live on the service principal (the enterprise application). Changing a definition property does not retroactively rewrite the instance unless the property is a shared one that propagates, like the display name in the home tenant. When you assign users to the enterprise application, that assignment is an instance concern and never appears on the registration's manifest. When you add an app role to the registration, that is a definition concern. If you make a change in one place and watch the other for an effect that never arrives, the cause is almost always that you are looking at the wrong object for the property you changed.

**What credential types can a registration use, and which is best?**

A registration can authenticate with a client secret, a certificate, or a federated credential. A client secret is a generated string, the easiest to set up and the weakest to operate, because it is a shared value that exists wherever the app runs and can be copied; through the portal its lifetime is capped at 24 months. A certificate is an asymmetric key, stronger because the private key never leaves the app and is never sent to the token endpoint, and it is the recommended choice for production confidential clients. A federated credential stores no secret at all; the registration trusts tokens from an external issuer such as a CI provider or another cloud, so there is nothing to leak or rotate. Prefer a federated credential when the workload can present its own trusted token, a certificate when a stored credential is needed, and a client secret only for low-risk or short-lived cases.

**What is the difference between delegated and application permissions?**

A delegated permission lets the app act on behalf of a signed-in user, and the effective access is the intersection of the permission and what that user is themselves allowed to do. An application permission lets the app act as itself with no user present, and the effective access is exactly what the permission grants across the tenant. The practical difference is blast radius: a delegated permission inherits the user's reach, while an application permission has the app's reach, which is usually the whole directory. That is why application permissions always require administrator consent and cannot be granted by an ordinary user. When you switch a permission from delegated to application to make a no-user scenario work, you are also changing the blast radius from a single user to the entire organization, so the switch should be deliberate and the permission should be the narrowest variant the API offers.

**Why does my app still get an authorization error after I added a permission?**

Most often because the permission is declared on the registration but not yet consented on the service principal. Declaring a permission states what the app would like; consenting grants it in a specific tenant, and the grant is recorded on the service principal, not the application object. Application permissions and admin-restricted delegated permissions require an administrator to click Grant admin consent before they take effect. Until that happens, the permission shows in the registration's API permissions list but is inert, and the app fails with an authorization error that has nothing to do with its credential. The fix is to confirm an administrator has consented to the permission for the tenant, then verify the consent is present on the service principal. If the token the app receives still lacks the expected scope or role claim, the permission has not been granted the way the app needs it.

**How do I expose my own API with custom scopes?**

Set an Application ID URI on the registration to name your API, such as an `api://` form or a verified domain form, then define the access your API offers. For delegated access, publish scopes under Expose an API (the `oauth2PermissionScopes` collection in the manifest); calling apps request these, a user or admin consents, and the issued token carries them in the `scp` claim. For access that other applications hold directly, including app-only access with no user, define app roles in the `appRoles` collection and let other apps request them as application permissions, which surface in the `roles` claim. The step that makes exposing an API actually secure is validation: your API must verify the token's signature, issuer, and audience, then enforce the specific `scp` or `roles` claim for each operation. Publishing a scope you do not check is the same as not protecting the operation at all.

**When should I use a scope versus an app role?**

Use a delegated scope when a calling application acts on behalf of a signed-in user and you want to gate user-context actions; the scope rides the user's session and appears in the `scp` claim. Use an app role when you need to assign access to a user, a group, or another application directly, especially for app-only access where no user is present; app roles are assignable identities and appear in the `roles` claim. The clearest rule is that scopes are about what an app may do for a user, while app roles are about what an assigned principal may do. If another service needs to call your API as itself, define an app role on your API and have the other service request it as an application permission. If a user-facing app needs to call your API on a user's behalf, publish a delegated scope.

**What does single-tenant versus multitenant mean for a registration?**

The sign-in audience on the application object decides who can use the app. Single tenant (`AzureADMyOrg`) restricts use to the app's home tenant. Multitenant (`AzureADMultipleOrgs`) allows any Microsoft Entra organization to use it, and a wider value additionally allows personal Microsoft accounts. The operational consequence is where service principals are created. A single-tenant app has one application object and one service principal, both in your tenant. A multitenant app keeps its application object only in the home tenant but provisions a service principal in every other tenant that consents to it, and each of those instances holds that tenant's own consent and assignments. Choose the audience deliberately, because widening it increases how broadly your app can be provisioned. Single tenant is the smaller exposure and the right default unless cross-organization use is a genuine requirement.

**Why does a multitenant app create a service principal in every tenant?**

Because each tenant needs a local identity to hold its own consent, role assignments, conditional access, and policy for your app, and that local identity is the service principal. The application object, your single published definition, stays only in your home tenant. When another organization first uses your app and an administrator or user consents, Entra ID provisions a service principal for your app in that organization's directory so the organization can govern the app on its own terms. Consequences follow directly: consent is per tenant, so granting it in your tenant does nothing for a customer's; assignment and conditional access are per tenant; and a customer can revoke your app by deleting its service principal in their directory without affecting your registration or any other customer. One definition, an independent instance in each consuming tenant.

**How can I tell whether a permission is actually granted?**

Check the service principal, not the registration. The registration's API permissions list shows what the application declared it wants, which is only a request. The service principal records what was actually consented in the tenant: delegated grants and application-permission role assignments. A permission that appears on the registration but has no matching grant on the service principal is declared but not consented, and the app will fail when it tries to use it. With the Microsoft Graph PowerShell module you can read the service principal's app-role assignments to see the application permissions that are live in the tenant, and its delegated grants to see the delegated permissions. Confirming a permission therefore means comparing the declaration on the definition with the grant on the instance, and the grant on the instance is the one that determines what the app can actually do.

**What is the maximum lifetime of a client secret?**

Through the Microsoft Entra admin center, the maximum lifetime you can set for a client secret is 24 months, and the option to create a non-expiring secret was removed for security reasons. You can create a secret with a longer lifetime using the Microsoft Graph API or PowerShell, but doing so works against the platform's direction and against good practice, because a long-lived shared secret is a long-lived risk. Microsoft recommends keeping secret lifetimes short, often under six months, and rotating regularly. Better still, a tenant can enforce a maximum secret lifetime, or ban password credentials entirely, with an application management policy, so the rule is enforced by the platform rather than left to each team. The strongest position is to avoid client secrets for production confidential clients altogether and use certificates or federated credentials, which removes the expiring shared secret from the picture.

**What is the app manifest and why does it look different than older guides?**

The manifest is the application object expressed as JSON, and every property you can set through a portal tile is also a manifest attribute, with a few attributes only settable by editing the manifest directly. It looks different from older guides because Microsoft retired the Azure AD Graph manifest format, and the portal now shows the Microsoft Graph app manifest, in which several attributes were renamed or relocated. A frequently hit example is the access token version: the attribute older guides call `accessTokenAcceptedVersion` at the root is now `requestedAccessTokenVersion` inside the `api` node. The lesson is that the manifest is a moving schema, so a value copied from an old post can fail to load or land in the wrong place. When a manifest edit does not take effect, confirm the current attribute name and location against current documentation before assuming your value is wrong.

**How do over-permissioned registrations turn into breaches?**

A registration that holds a broad application permission has tenant-wide access that does not depend on any signed-in user. If that registration's credential leaks, the attacker can authenticate as the application and inherit the permission directly, with no user account to compromise and no additional step. The breach scales with the permission: a narrow, resource-scoped permission limits the damage, while a full directory read or read-write permission turns one leaked secret into organization-wide exposure. This is why application permissions deserve more scrutiny than any other setting on a registration. The defenses are to grant the narrowest permission that accomplishes the task, prefer delegated permissions where a user is present so the user's rights cap the reach, keep credentials short-lived and ideally secretless, and review application permissions on a schedule, removing any the app no longer uses.

**Should I use an app registration or a managed identity?**

Use a managed identity when the workload runs inside Azure and does not need to be multitenant, because a managed identity has no stored credential to leak or rotate, which removes the most common attack path entirely. Use an app registration when the application must run outside Azure, must be multitenant, or must expose its own API for other applications to call, scenarios a managed identity does not cover. The two are not competitors so much as different tools: the managed identity is the secretless choice for Azure-hosted workloads calling Azure resources, while the registration is the general-purpose identity for applications that need credentials, a published API, or cross-organization reach. When you find yourself managing a registration's secret for an app that only runs in Azure and only serves your own tenant, that is the signal to consider a managed identity instead.

**How do I keep registrations auditable and from drifting?**

Define registrations as code so their permissions, exposed scopes, app roles, credentials, and redirect URIs live in version control where every change is reviewed and the configuration can be recreated identically. Then govern them with application management policies that the platform enforces, such as capping client-secret lifetime or banning password credentials tenant-wide, so the standard does not depend on anyone remembering it. Finally, review the service principal's sign-in and audit logs on a schedule to catch out-of-process changes, like a secret added by hand or consent granted to an unfamiliar app. Code gives you history and review, policy gives you enforcement, and periodic review gives you detection. Together they turn a registration from a mutable portal artifact that quietly accretes risk into a managed identity surface you can reason about and trust.
