---
layout: post
title: "Fix AADSTS65001 Consent Required Error"
page_title: "AADSTS65001 Consent Required: How to Grant Admin Consent and Fix the Error in Microsoft Entra ID"
date: 2022-10-03
categories: ["Technology"]
tags: ["Azure", "AADSTS65001", "Microsoft Entra ID", "Identity", "Troubleshooting", "Security"]
excerpt: "AADSTS65001 means no one has yet approved the requested permission. Learn who must grant it, when an administrator is required, and how to fix it fast."
image: "/assets/images/blog/blog-53.webp"
reading_time: 59
author: "david-thornton"
last_updated: 2022-10-03
lang: en
---
When a sign-in or a token request fails with AADSTS65001, Microsoft Entra ID is telling you something precise: nobody has approved this application to use the permission it just asked for. The full text reads that the user or administrator has not consented to use the application with the given ID, and that an interactive authorization request should be sent for this user and resource. That message looks like a wall, and the instinct is to retry the sign-in or to recreate the app registration. Both instincts are usually wrong. The error is not a transient fault and not a broken registration. It is a missing grant, and the fix is to record the right grant, by the right person, in the right tenant.

This guide treats AADSTS65001 as a decision problem rather than a mystery. The first question is what kind of permission the app requested, because the answer decides who is allowed to approve it. The second question is which tenant the grant has to land in, because consent is stored per directory and a grant in your development tenant does nothing for a customer's tenant. Once you can answer those two questions from the error itself, the fix is short and you stop guessing.

![Fixing AADSTS65001 consent required in Microsoft Entra ID - Insight Crunch](/assets/images/blog/blog-53.webp)

## What AADSTS65001 actually means

The code belongs to the Entra ID authorization layer, not the authentication layer, and that distinction matters for the diagnosis. Authentication answers whether the caller is who they claim to be. Authorization answers whether the application is allowed to do what it is trying to do on a protected resource. A user can authenticate perfectly, prove their identity, pass multifactor, and still hit AADSTS65001, because the second gate is about the application's permissions, not the user's credentials.

Every time an application asks Entra for a token that carries a permission to a resource such as Microsoft Graph, the platform checks whether that exact permission has already been approved for that application in that directory. If the approval exists, the token is issued and the call proceeds. If it does not, two things can happen. In an interactive flow with a user present, Entra shows a consent prompt so the user or an administrator can approve it on the spot. In a non-interactive flow, where no human is at the keyboard, there is no prompt to show, so Entra returns AADSTS65001 instead. The error is the platform saying that it reached the approval gate, found no approval on file, and had no way to ask for one in the current flow.

Reading the error this way reframes the whole task. You are not chasing a bug. You are recording an approval that was never recorded, or recording it in a place where the application can actually find it. The rest of this article is about identifying exactly which approval is missing and putting it where it belongs.

## How to read the AADSTS65001 error and gather the signal

Before changing anything, extract the facts the error hands you, because they point straight at the fix. The message contains three load-bearing pieces of information: the application ID, the application name, and frequently the resource or the scope that triggered the failure. The application ID confirms which app registration is involved, which lets you rule out the common case where a copied configuration is pointing at the wrong client ID entirely. The resource tells you which API the app was reaching for, usually Microsoft Graph or a custom API, and that narrows the search for the missing approval.

### What does the AADSTS65001 message tell you?

It names the application that requested access and signals that the approval gate found nothing on file for the requested permission. It does not say the password was wrong, the app was not found, or the network failed. It says the grant is missing, which means the fix is to record that grant rather than to retry the sign-in.

The richer signal usually lives one layer down, in the response from the token endpoint and in the sign-in logs. The OAuth error response carries an `error` of `invalid_grant` or `consent_required` along with an `error_description` that embeds the AADSTS65001 text. Capturing that full description is worth the minute it takes, because it frequently spells out the scope by name, and a named scope removes all ambiguity about what to approve. When the flow is a browser redirect, the description rides in the query string or fragment of the redirect back to your application; when the flow is a direct token call from a daemon or a script, it sits in the JSON body of the failed response.

The Entra sign-in logs give you the same picture from the platform side and add the timestamp, the client app, the resource, and a correlation ID. Open the Entra admin center, go to the sign-in logs, filter to the application, and find the failed entry. The failure reason will reference consent, and the activity details tie the attempt to a specific application and resource. Capturing the correlation ID at this stage pays off if you later need to confirm that a fresh approval actually cleared the original failure, because you can compare a failing entry to a succeeding one for the same application.

One more signal separates two cases that look identical from the outside. If a user sees an interactive consent prompt and the prompt itself is blocked or greyed out with a note that an administrator must approve, the tenant's user consent policy is in play. If there is no prompt at all and the error arrives directly, the flow was non-interactive and could never have shown a prompt. Knowing which of these you are in tells you immediately whether the path forward is an admin grant, a policy change, or a switch to an interactive flow, and you will see all three mapped out below.

## The consent framework behind the error: delegated versus application permissions

Almost every AADSTS65001 diagnosis comes down to one classification: is the app requesting a delegated permission or an application permission? The two are approved by different people under different rules, and confusing them is the single most common reason a fix fails to stick. The model here is the same one covered in depth in the [walkthrough of how Microsoft Entra ID works as an identity platform](/2022/02/21/microsoft-entra-id-explained/), and it is worth holding the two permission types clearly in mind before touching any grant.

A delegated permission lets the application act on behalf of a signed-in user. The app can only do what both the app has been granted and the user is themselves allowed to do, whichever is more restrictive. Because a user is present in these flows, Entra can, in principle, show that user a prompt and let them approve the access for themselves. Whether the user is actually allowed to approve it depends on the tenant's user consent setting, which an administrator controls.

### Do delegated permissions always need consent?

Yes, every delegated permission needs an approval on file before a token carrying it is issued. What varies is who may give that approval. Low-risk delegated permissions can be approved by the user when the tenant allows user consent. Higher-risk ones, or any permission when the tenant disables user consent, require an administrator.

An application permission is different in kind. It lets the application act as itself, with no signed-in user anywhere in the picture. A background service, a scheduled job, a daemon, or any workload using the client credentials flow runs under an application permission. Because there is no user to act on behalf of and no user to show a prompt to, an application permission can only ever be approved by an administrator, in every tenant, without exception. This is the heart of the matter, and it deserves a name.

The application-permission-needs-admin rule states it plainly: any application permission, and many delegated permissions under a restrictive tenant policy, can be approved only by an administrator, so an AADSTS65001 on such a permission is a request for an administrative grant, never a sign-in to retry. Internalize that rule and most of the diagnoses below become quick. If the failing flow is client credentials, you already know a user-level approval is impossible and an admin grant is the only path. If the failing flow has a user but the user cannot get past the prompt, the tenant policy or the permission's risk level has pushed it into admin territory. The fix changes accordingly, but the rule tells you which branch you are on before you run a single command. The mechanics of where these permissions are declared, in the app registration's requested resource access, are covered in the [breakdown of Entra app registrations and how permissions are requested](/2024/03/04/entra-app-registrations-explained/).

## The distinct root causes of AADSTS65001

The error has a small number of genuine causes, and each one has a confirming check and a matching fix. Working through them in order is faster than trying remedies at random, because the first cause you confirm is almost always the real one. The causes are: an application permission that never received an administrative grant, a delegated permission under a tenant that blocks user approval, a newly added scope that invalidated a prior grant, a client credentials workload requesting permissions through the `.default` scope without those permissions being pre-approved, and a grant that was recorded in the wrong directory. Each is treated below with the check that confirms it and the command that fixes it.

### An application permission that was never granted by an admin

This is the most frequent cause for background services and integrations. The app declares an application permission, for example a Microsoft Graph application permission such as `User.Read.All` or `Mail.Read`, the workload runs as a daemon with the client credentials flow, and the token request fails with AADSTS65001 because no administrator ever approved that permission.

To confirm it, open the application's entry under enterprise applications, look at its permissions, and check whether the application permission shows a granted status. If the permission appears in the app registration's requested permissions but does not appear as granted on the enterprise application, the approval is simply missing. You can verify the same fact from the command line by listing what the service principal has actually been assigned, which is shown later in the section on confirming the grant.

The fix is an administrative approval. From the portal, an administrator opens the enterprise application, goes to permissions, and uses the grant admin consent action for the tenant. From the command line, the Azure CLI does the same in one call:

```bash
az ad app permission admin-consent --id <application-client-id>
```

That command requires the caller to be a Global Administrator or to hold a role with the rights to grant tenant-wide consent, and it records the approval for every permission the app currently requests. After it runs, the daemon's next token request finds the approval on file and succeeds.

### A delegated permission blocked by the tenant's user consent policy

Here a user is present and the permission is delegated, yet the user still cannot complete the approval. The cause is the tenant's user consent setting. An administrator may have set user consent to allow only for permissions classified as low risk, to allow only for verified publishers, or to disallow user consent entirely. Under any of the more restrictive settings, a delegated permission the user would normally approve for themselves is escalated to require an administrator, and a non-interactive retry of the same request returns AADSTS65001.

To confirm it, check the user consent configuration under enterprise applications, in the consent and permissions area. If user consent is restricted or disabled, and the failing permission falls outside what users are allowed to approve, the policy is your cause. The sign-in logs reinforce this: the failure reason will reference that an administrator must approve the access.

You have two clean fixes. The first is an administrative grant for that specific application, identical to the command above, which approves the permission once for the whole tenant so individual users never see the gate again. The second, where you want users to keep approving routine access themselves, is to adjust the tenant's user consent policy to permit the class of permission in question. The policy change is broader and should be made deliberately, because it affects every application, not just this one. The flows that surface this prompt in the first place are described in the [explanation of Entra ID authentication and the OAuth consent flow](/2023/12/18/entra-id-authentication-explained/).

### A newly added scope that invalidated the prior consent

An application that worked yesterday can fail today with AADSTS65001 the moment a developer adds a new permission. Consent in Entra is per permission, not per application. Approving an app for three scopes does not pre-approve a fourth one added later. When the app starts requesting the new scope, the platform finds no approval for that specific permission and fails, even though the older scopes remain perfectly approved.

To confirm it, compare the permissions the app now requests against the permissions actually granted on the enterprise application. A scope present in the request but absent from the grant list is your culprit. This case is easy to miss precisely because most of the app keeps working; only the code path that needs the new scope breaks.

The fix depends on the permission type. For a delegated scope that users are allowed to approve, an interactive flow will simply show the consent prompt again for the new permission, and incremental consent handles the rest. For an application permission, or for any permission under a restrictive policy, an administrator must grant the addition, again using the same admin consent action or CLI command. The deeper mechanics of why a new scope re-triggers the prompt are covered in their own section below.

### A client credentials workload using `.default` without pre-approved permissions

Daemons and service-to-service workloads request tokens with the `.default` scope, for example `https://graph.microsoft.com/.default`. That scope does not request a single permission; it asks for a token covering every permission the application has been configured for and that has already been approved in the tenant. If any required application permission has not been approved, the request fails with AADSTS65001, because there is no user and no prompt, and `.default` cannot trigger interactive approval.

To confirm it, look at which application permissions the daemon's registration declares and which have actually been granted. A declared but ungranted application permission, combined with a `.default` request, produces this failure every time.

The fix is the administrative grant, after which `.default` resolves to the full set of approved permissions and the token issues. This case is worth separating from the others because `.default` makes the failure feel mysterious: the error does not always name one scope, since the scope requested was effectively all of them. Granting consent for the application as a whole resolves it cleanly.

### A grant recorded in the wrong tenant

This cause hits multi-tenant applications and anyone who develops in one directory and runs in another. Consent lives on the service principal, the enterprise application object, inside a specific tenant. Approving the app in your own development tenant records the grant there and nowhere else. When the same app runs against a customer's tenant, or against your production tenant, Entra looks for the approval in that directory, finds nothing, and returns AADSTS65001, even though the app is fully approved in the tenant you tested in.

To confirm it, identify which tenant the failing token request authenticated against, by checking the authority used in the request, then look for the enterprise application and its granted permissions in that exact directory. If the app is missing or its permissions are ungranted there, you have located the problem.

The fix is to record the approval in the directory that actually serves the failing request. For a customer tenant, that means an administrator in the customer's directory grants consent, often through the admin consent URL described below. For your own multi-tenant setup, it means granting in each tenant the app must operate in. The tenant-scoping of every Entra object, including the service principal that holds consent, is part of the model in the [Entra ID platform overview](/2022/02/21/microsoft-entra-id-explained/).

## The InsightCrunch consent decision table

The fastest way to resolve AADSTS65001 is to classify the failing permission and the tenant policy, then read off who must approve it and how. The table below is the findable artifact for this article: a single map from permission type and policy to the required grant path. Carry it into any AADSTS65001 incident and the next move is never in doubt.

| Permission type | Tenant user consent policy | Who can approve | How to grant it |
| --- | --- | --- | --- |
| Delegated, low risk | User consent allowed | The signed-in user or an admin | Interactive prompt approves it, or an admin grants once for the tenant |
| Delegated, low risk | User consent restricted or disabled | An administrator only | Admin grant in the enterprise app, or via the admin consent action |
| Delegated, higher risk | Any policy | An administrator only | Admin grant for the tenant |
| Application permission | Any policy | An administrator only | Admin grant, required in every tenant the app runs in |
| Any permission, multi-tenant app | Per consuming tenant | An admin in that tenant | Admin consent in the customer or production directory |
| Newly added scope | Depends on the scope above | Same rule as the scope's type | Re-approve the new scope; interactive for user-approvable, admin grant otherwise |

The table encodes the namable claim from the start of this article. Read down the who-can-approve column and one fact dominates: for application permissions and for delegated permissions under any restrictive condition, the answer is always an administrator. That is the application-permission-needs-admin rule in practice. The moment you classify the failing permission as an application permission, you can stop considering user-level fixes entirely, because no user-level approval can ever satisfy it. The table turns a confusing error into a two-column lookup, and the lookup almost always ends at an administrative grant.

## Granting admin consent the right way

Most AADSTS65001 fixes end in an administrative grant, so it pays to know every reliable way to record one. There are three: the portal, a direct admin consent URL, and the command line. They write the same underlying objects, so pick whichever fits the situation, a one-off fix, a self-service request from a customer admin, or an automated pipeline.

### How do I grant admin consent from the portal?

Open the Entra admin center, go to enterprise applications, select the application, open its permissions, and choose grant admin consent for the tenant. Confirm the requested permissions, approve, and the grant is recorded for the whole directory. The next token request for those permissions then succeeds without any prompt.

The portal path is the one to use when you can sign in as an administrator of the affected tenant and want to review exactly what you are approving before you approve it. The permissions screen lists each requested permission, marks which are delegated and which are application permissions, and shows the current granted status. Reviewing that list before clicking the grant action is good hygiene, because admin consent for a tenant is a powerful action and you want to approve only what the application genuinely needs.

The direct admin consent URL is the cleaner path when the administrator is not you, which is the normal multi-tenant case. You construct a URL that sends the admin straight to the approval page for your application in their own tenant:

```text
https://login.microsoftonline.com/{tenant}/adminconsent?client_id={client-id}
```

Replace `{tenant}` with the customer's tenant ID or verified domain and `{client-id}` with your application's client ID. When the customer's administrator opens that link, signs in, and approves, the grant is recorded in their directory, which is exactly where the failing request needed it. This is the standard way to onboard a multi-tenant app into a new customer tenant, and it sidesteps the wrong-tenant cause entirely because the grant lands in the directory that serves the request.

The command line is the path for automation and for engineers who live in a terminal. The Azure CLI grants consent for everything the app currently requests:

```bash
# Grant admin consent for all permissions the app requests, in the current tenant
az ad app permission admin-consent --id <application-client-id>

# Inspect what the app requests before granting
az ad app permission list --id <application-client-id>
```

Microsoft Graph PowerShell offers finer control when you want to grant a single specific permission rather than everything at once. For a delegated permission you create an OAuth2 permission grant against the resource's service principal; for an application permission you create an app role assignment. The shape of the calls is:

```powershell
Connect-MgGraph -Scopes "Application.ReadWrite.All","DelegatedPermissionGrant.ReadWrite.All","AppRoleAssignment.ReadWrite.All"

# Application permission: assign the app role on the resource service principal
New-MgServicePrincipalAppRoleAssignment -ServicePrincipalId $clientSpId -PrincipalId $clientSpId -ResourceId $resourceSpId -AppRoleId $appRoleId

# Delegated permission: create the OAuth2 permission grant
New-MgOauth2PermissionGrant -ClientId $clientSpId -ConsentType "AllPrincipals" -ResourceId $resourceSpId -Scope "User.Read Mail.Read"
```

The `ConsentType` of `AllPrincipals` records the grant for every user in the tenant, which is the admin-consent equivalent for delegated permissions. Granting per permission this way is the surgical option when you want to approve exactly what is needed and nothing more, which keeps the application's footprint minimal and auditable.

## Why adding a new scope re-triggers AADSTS65001

The incremental nature of consent in the Entra v2 model is a feature, but it surprises engineers who expect a single up-front approval to cover an application forever. Each permission is approved on its own. When an application requests a scope it has not yet had approved, the platform treats that as a new request regardless of how many other scopes the app already holds. In an interactive flow this shows up as a fresh prompt asking the user to approve the additional access. In a non-interactive flow it shows up as AADSTS65001, because there is no opportunity to prompt.

This design protects users and tenants from scope creep. An application cannot quietly broaden its reach by adding permissions to its registration and expecting them to be live immediately; the additions sit dormant until someone approves them. That is the right default for security, and it is the reason a working integration breaks the day a new feature ships that needs one more permission.

The practical consequence is a deployment discipline. When you add a permission to an application that runs non-interactively, the approval must be recorded as part of the same change, not left for a runtime prompt that will never appear. Treat the grant as a deployment step. For pipelines, that means the release that adds the scope also runs the admin consent action against the target tenant, so the permission and its approval go live together. Skipping that step is the textbook way to ship a change that passes in a tenant where you happened to click consent manually and then fails in every tenant where you did not.

There is a subtlety with the `.default` scope worth restating here. A `.default` request does not name the new scope; it asks for all configured permissions at once. So when you add a permission to a `.default` workload and forget to re-approve, the failure is not isolated to one feature. The entire token request can fail until the new permission is approved alongside the rest. That makes the re-consent step non-negotiable for client credentials workloads, and it is the most common reason a previously stable daemon starts returning AADSTS65001 after an otherwise innocent deployment.

## The client credentials and `.default` case in depth

Background workloads deserve their own treatment because they hit AADSTS65001 in a way that interactive apps never do. A client credentials flow has no user. The application authenticates with its own client ID and a secret or certificate, and it requests a token using the `.default` scope of the target resource. Because there is no user, there is no on-behalf-of relationship and no delegated permission in play at runtime; the workload runs purely on application permissions.

This is where the application-permission-needs-admin rule is absolute. A daemon cannot self-approve. A user cannot approve on its behalf, because the daemon does not act for any user. Only an administrator can record the grant, and until that grant exists, every token request the daemon makes for a permission it lacks will fail with AADSTS65001. Engineers new to the client credentials flow sometimes try to fix this by signing in as an admin in a browser and approving the app interactively, which works, but only because the interactive sign-in is itself an administrative grant. The grant, not the sign-in, is what resolved the error.

The confirming check is direct. Identify the application permissions the daemon's registration declares for the target resource, then list the app role assignments actually present on the workload's service principal. If a declared application permission has no matching assignment, the daemon will fail. The Microsoft Graph PowerShell call to inspect this is shown in the section on confirming the grant; the fix is the administrative consent that creates the missing app role assignment.

A second pitfall in this flow is the wrong resource. A `.default` request must target the resource the app actually calls. Requesting `.default` for Microsoft Graph when the app needs a custom API, or the reverse, produces a token that lacks the needed permission and a downstream failure. While that specific mismatch can surface as a different error, it frequently sits next to a genuine consent gap, so when you debug a daemon, confirm both that the resource is right and that its permissions are approved. Getting the application's identity and credentials configured correctly is a prerequisite covered alongside the broader registration model in the [Entra app registrations breakdown](/2024/03/04/entra-app-registrations-explained/).

## Multi-tenant consent: why it works in one tenant and fails in another

The single most disorienting AADSTS65001 is the one that appears in production after everything passed in development. The cause is almost always tenant scoping. Consent is not a property of the application registration that travels with the app. It is a property of the service principal, the local representation of the app inside a particular directory, and each tenant that uses a multi-tenant app gets its own service principal with its own grants.

When you develop a multi-tenant application, your home tenant holds the app registration, the master definition. The first time the app runs in your home tenant and you approve it, a service principal is created there and the grants are recorded on it. Everything works. Then a customer uses the app. Their tenant gets its own service principal for your app, created on first sign-in, but that service principal starts with no grants. Until an administrator in the customer's tenant approves the permissions, every non-interactive request, and every delegated request that exceeds their user consent policy, fails with AADSTS65001 in that tenant while continuing to work flawlessly in yours.

The clean onboarding path is the admin consent URL aimed at the customer's tenant. Sending a customer administrator the `adminconsent` link for your client ID lets them approve your app in their own directory in one step, which provisions the service principal and records the grants together. This is the intended mechanism for multi-tenant onboarding, and building it into your setup flow prevents the wrong-tenant failure before it can occur.

For internal multi-tenant setups, where one organization runs several directories, the same rule applies: approve the app in each tenant it must operate in. A grant in the hub tenant does nothing for the spoke tenants. Treating consent as per-directory state, rather than as a one-time application setting, is the mental shift that makes these failures predictable. The tenant boundary that scopes the service principal is the same boundary explored throughout the [Entra ID platform overview](/2022/02/21/microsoft-entra-id-explained/), and it explains why the same code path can pass and fail depending only on which directory it runs against.

## Confirming consent on the enterprise application

Whether you are diagnosing the failure or verifying that a fix worked, the source of truth is the enterprise application, which is the service principal for your app in the current tenant. Its permissions blade shows exactly what has been approved, split into the permissions an administrator granted for the tenant and the permissions individual users approved for themselves. A permission that the app requests but that appears in neither list is your missing grant.

From the portal, open enterprise applications, select the app, and open permissions. The admin-consented permissions appear together, each with the resource it targets and the approval date. If the permission your error referenced is absent, the diagnosis is confirmed and the fix is the grant. If it is present and the error persists, the problem is likely tenant scoping, meaning you are looking at the grant in the wrong directory, which sends you back to the multi-tenant check above.

From Microsoft Graph PowerShell, you can read both kinds of grant directly off the service principal, which is the precise way to confirm a daemon's application permissions:

```powershell
# Find the service principal for your app
$sp = Get-MgServicePrincipal -Filter "appId eq '<application-client-id>'"

# Delegated grants recorded for the app
Get-MgServicePrincipalOauth2PermissionGrant -ServicePrincipalId $sp.Id

# Application permission assignments (app roles granted to the app)
Get-MgServicePrincipalAppRoleAssignment -ServicePrincipalId $sp.Id
```

The first list shows delegated scopes and whether they were granted for all principals or for individual users. The second shows the application permissions, each as an app role assignment naming the resource and the role. Matching these against what the registration requests tells you, conclusively, which permission lacks an approval. The Azure CLI offers a comparable view through `az ad app permission list-grants`, which is convenient inside a script that needs to assert the grant exists before a workload starts.

This confirmation step is also your regression guard. After granting consent, re-run the original failing request and check the sign-in logs for a success entry with the same application and resource. A clean success there, where AADSTS65001 used to be, is the proof that the grant landed in the right place.

## Reproducing AADSTS65001 from scratch

The fastest way to build a reliable mental model of this failure is to cause it deliberately in a sandbox tenant, then clear it, and watch the sign-in logs flip from failure to success. A reproducible repro is worth more than a dozen forum threads, because you control every variable and you see exactly which action resolves the error. The walkthrough below builds the daemon case, which is the cleanest because it removes the user entirely and isolates the approval question.

Start by registering an application. Give it a name, leave it single-tenant for now, and note the client ID Entra assigns. Create a client secret on it so the workload can authenticate. Then add a Microsoft Graph application permission to the registration, for example `User.Read.All`, which lets the app read user profiles as itself. Crucially, do not approve it yet. The registration now declares a permission it has not been authorized to use, which is precisely the configuration that yields the error.

```bash
# Acquire a token as the application using the client credentials flow
curl -s -X POST "https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token" \
  -d "client_id=<client-id>" \
  -d "client_secret=<client-secret>" \
  -d "scope=https://graph.microsoft.com/.default" \
  -d "grant_type=client_credentials"
```

The response will not be a token. It returns a JSON body with an `error` and an `error_description` carrying the AADSTS65001 text, telling you the application has not been authorized for the permission it implicitly requested through `.default`. This is the failure, reproduced on demand. Look at it closely: there is no user in this exchange, so there was never a prompt to show, and the platform had no choice but to refuse.

Now clear it with a single administrative action and observe the change:

```bash
# An administrator authorizes every permission the app currently requests
az ad app permission admin-consent --id <client-id>
```

Re-run the token request unchanged. This time the response carries an `access_token`, because the approval the daemon needed now exists on the service principal. The only thing that changed between the failing call and the succeeding call was the recorded sign-off, which is the entire lesson of this error compressed into two commands. If you check the sign-in logs for the application across both attempts, the first appears as a failure referencing the missing authorization and the second as a clean success, with the resource and correlation captured for each.

To extend the repro to the interactive case, switch the registration to expose a delegated permission, build an authorize request with `response_type=code` and a delegated scope the tenant requires an admin to approve, and observe that a normal user is sent to a page stating an administrator must approve the access rather than being allowed to proceed. Approving as an administrator, or pre-approving with the same admin consent action, then lets the user through. Running both halves, the daemon and the interactive user, side by side is the single best exercise for internalizing why the same error code can demand a user action in one flow and an administrator in another.

## Microsoft Graph permissions: which ones need an administrator

Microsoft Graph is the resource behind the large majority of AADSTS65001 incidents, simply because most applications call it for users, mail, calendars, groups, or directory data. Graph splits its permissions into delegated permissions, used when a user is signed in, and application permissions, used by daemons, and the split maps directly onto who may authorize each one.

Many Graph delegated permissions are low risk and a tenant that permits user consent will let an ordinary user approve them. Reading the signed-in user's own profile, for example, is the kind of access users routinely approve for themselves. As the access broadens, the risk classification rises. A delegated permission to read all users in the directory, or to read mail across the organization, is treated as sensitive, and tenants commonly require an administrator to authorize it even though it is delegated. So a delegated Graph permission can still produce AADSTS65001 for users when it exceeds the tenant's user-consent threshold, and the remedy is an administrative sign-off for that permission.

Graph application permissions are a different story, and the rule is mechanical: every one of them requires an administrator. There is no user-approvable Graph application permission anywhere, because application permissions by definition run without a user. A background service that reads all mailboxes, writes to all calendars, or manages directory objects under its own identity is operating on application permissions, and an administrator must authorize each before the service can obtain a working token through `.default`. When such a service fails with AADSTS65001 after a deployment, the cause is almost always a Graph application permission that was added to the registration but never authorized for the tenant.

### Why do some Graph permissions still fail after a user approves them?

Because the user approved a different, lower-risk permission than the one the failing call needs. Graph permissions are granted individually, so approving profile access does not authorize directory-wide reads. The sensitive permission still awaits an administrator, and the call that needs it returns AADSTS65001 until that separate sign-off is recorded.

The practical takeaway for any Graph integration is to enumerate the exact permissions the application uses, classify each as delegated or application, and for the delegated ones check whether they sit above the tenant's user-consent line. That enumeration, done once, tells you in advance which permissions will need an administrator and lets you authorize them up front rather than discovering the gap at runtime. The permissions an application declares are part of its registration, the model for which is detailed in the [Entra app registrations breakdown](/2024/03/04/entra-app-registrations-explained/).

## The OAuth flow end to end: where AADSTS65001 surfaces

Understanding precisely where in the OAuth exchange the error appears removes the last of the mystery, because the two main flows fail at different endpoints and for slightly different reasons. The authorization code flow, used by interactive web and native apps, runs through the authorize endpoint first; the client credentials flow, used by daemons, goes straight to the token endpoint.

In an interactive authorization code flow, the browser is redirected to the authorize endpoint with the requested scopes. Entra authenticates the user, then checks whether the requested permissions have an approval on file. If a permission is missing and the user is allowed to approve it, Entra renders the consent screen and lets the user authorize it then and there. If the permission requires an administrator the user is not, Entra shows a page indicating administrative approval is needed and does not let the flow complete. Where the request is built to avoid interaction, or where a silent token renewal is attempted, the same missing-approval condition returns AADSTS65001 instead of a screen, because a silent request explicitly forbids prompting.

The `prompt` parameter shapes this behavior. A request with `prompt=consent` forces the consent screen even when an approval already exists, which is useful for re-confirming or for re-authorizing after adding a scope. A request with `prompt=admin_consent` drives the administrative approval experience directly. These parameters do not bypass the rules about who may authorize what; they only control which experience Entra presents to a user who is in a position to authorize. A daemon cannot benefit from either, since it never reaches an interactive surface.

In the client credentials flow there is no authorize step at all. The application posts directly to the token endpoint with its credentials and the `.default` scope. The platform validates the credentials, then checks that every application permission covered by `.default` has been authorized for the tenant. A single missing authorization fails the request with AADSTS65001 in the JSON response body. There is no fallback and no prompt, which is why daemon failures are so absolute: the token is either issued because everything is approved, or refused because something is not.

Reading the failure at the right endpoint speeds diagnosis. If the error arrives in a browser redirect, you are in an interactive flow and the question is whether the user may authorize the permission or whether an administrator must. If it arrives in the JSON body of a direct token call, you are in a non-interactive flow and an administrative sign-off is almost certainly the only path. The flows themselves, and how a token is requested in each, are walked through in the [Entra ID authentication explainer](/2023/12/18/entra-id-authentication-explained/).

## Exposing your own API: custom scopes and pre-authorized clients

AADSTS65001 is not limited to Microsoft Graph. When you expose your own web API in Entra and a client application requests one of its scopes, the same approval gate applies, and the same error appears when no one has authorized the client to call your API. Diagnosing this case follows the identical logic, with one extra lever that is unique to APIs you own: pre-authorization.

An API you expose declares its own delegated scopes and, optionally, its own application permissions, called app roles, that other applications may request. A client that requests one of those scopes must be authorized to do so, by a user or an administrator depending on the scope and the tenant policy, exactly as with Graph. If the client is a daemon requesting an app role on your API through `.default`, an administrator must authorize it, with no exception, because the rule about application permissions does not care whether the resource is Microsoft's or yours.

Pre-authorization changes the experience for trusted clients. When you mark a client application as pre-authorized for specific scopes of your API, users of that client are not shown a consent prompt for those scopes at all; the trust is established once, by you, at the API. This is how a first-party suite of applications avoids prompting users repeatedly for access among its own components. Pre-authorization applies to delegated scopes and removes the user-facing approval step for the named client, but it does not eliminate the administrative authorization that application permissions on your API still require.

The diagnosis for a custom API therefore has an extra branch. If a client hits AADSTS65001 calling your API, first classify the requested access as a delegated scope or an app role, which routes you to the same who-can-authorize question as before. Then, for delegated scopes on a trusted first-party client, consider whether pre-authorization should have removed the prompt and was simply not configured. Adding the client to the API's pre-authorized list resolves the recurring-prompt variant for that client cleanly, while genuine application permissions on your API still travel through an administrator. Building the API registration correctly, including which scopes and roles it exposes, is part of the registration design covered in the [Entra app registrations breakdown](/2024/03/04/entra-app-registrations-explained/).

## How consent interacts with Conditional Access and app governance

Authorization does not happen in isolation. A tenant can layer Conditional Access policies and application governance controls on top of the consent framework, and these can shape when AADSTS65001 appears and what an administrator should check before authorizing an application broadly. Understanding the interaction prevents you from authorizing an app that a separate policy will still block, which would leave you puzzling over why the grant did not fix everything.

Conditional Access evaluates the conditions of a sign-in, the user, the device, the location, the risk, and can require additional controls or block access entirely. These policies operate on the authentication and access decision, not on the application consent record. So a permission can be fully authorized and a token still withheld because a Conditional Access policy demands compliance the session does not meet. That refusal is not AADSTS65001; it carries its own codes. The lesson is that clearing AADSTS65001 resolves the approval gate, but it does not override an access policy, and an app that still fails after a clean grant may be hitting a policy rather than a missing authorization. Separating the two keeps you from over-authorizing an application in a fruitless attempt to satisfy what is actually a Conditional Access requirement.

Application governance and consent policies sit on the approval side and can make the gate stricter. A tenant can require that only applications from verified publishers be user-approvable, can restrict user consent to a curated set of low-risk permissions, or can route everything through the admin consent request workflow. Each of these is a deliberate narrowing that increases how often a user lands on AADSTS65001 and is steered toward requesting administrative approval. For an administrator, the right posture before authorizing an application tenant-wide is to review the publisher, the exact permissions requested, and whether the app genuinely needs each one, because a tenant-wide sign-off is a meaningful expansion of trust. The platform's emphasis on least privilege and reviewable grants is the same discipline that governs role assignments on resources, which is treated in the [guide to Azure RBAC AuthorizationFailed errors](/2022/10/10/fix-azure-rbac-authorizationfailed/).

## Five real-world AADSTS65001 patterns and how each resolves

The textbook description of this error rarely matches the messy shape it takes at work. The five patterns below are the recurring forms engineers actually report, each described as a problem pattern with the signal that identifies it and the move that resolves it, so you can match your incident to one and act.

The first pattern is the integration that ships an application permission nobody authorized. A team builds a service that reads directory data as itself, adds the Graph application permission to the registration, deploys, and the service immediately fails its first token call. The signal is a `.default` client credentials request returning the error with no user anywhere in the logs. The move is an administrative sign-off in the tenant the service runs in, after which the next call succeeds. This pattern is so common that it is worth adding the grant to the deployment itself so it never ships unauthorized again.

The second pattern is the locked-down tenant that blocks a permission a user would normally approve. A user tries an application, sees a prompt that tells them an administrator must approve, and the non-interactive retry surfaces AADSTS65001. The signal is an interactive flow where the prompt appears but cannot be completed by the user, combined with a restrictive user consent setting in the tenant. The move is either an administrative grant for that application or, where you want users to keep handling routine access, a considered loosening of the user consent policy for the relevant permission class.

The third pattern is the integration that broke the morning after a feature shipped. Everything worked, then a developer added one Graph scope and a code path that uses it began failing while the rest of the app stayed healthy. The signal is a brand-new permission in the registration that does not appear in the granted list, against an otherwise fully authorized application. The move is to authorize the new scope, interactively if a user may approve it or through an administrator otherwise, and to fold that authorization into the deployment so the next added scope does not repeat the surprise.

The fourth pattern is the daemon that runs without any human in the loop. A scheduled job authenticates with a certificate and requests `.default` for Graph, and an unauthorized application permission fails the entire request rather than one feature. The signal is a service identity, no user, and a `.default` scope. The move is an administrative authorization that creates the missing app role assignment on the service principal, after which the daemon's token covers its full approved permission set. Because `.default` is all-or-nothing, this pattern rewards keeping the daemon's permissions minimal and authorized up front.

The fifth pattern is the app that passed everywhere except the customer's tenant. A multi-tenant application is approved and working in the development directory, then fails the moment a customer uses it. The signal is a production-only or customer-only failure with an identical client ID and identical code to the working environment. The move is to record the approval in the customer's directory, normally by sending their administrator the admin consent URL for the application, which provisions the service principal and its grants in the directory that actually serves the failing request. The tenant scoping that makes this happen is the same boundary running through the [Entra ID platform overview](/2022/02/21/microsoft-entra-id-explained/), and recognizing it turns the most disorienting variant of this error into the most predictable.

## Preventing AADSTS65001 from recurring

Fixing the error once is easy; stopping it from returning across deployments and new tenants takes a little structure. The prevention strategy follows from the causes. Because consent is per permission, per tenant, and easy to forget when a scope is added, the durable fixes are about making approval an explicit, repeatable part of how applications ship rather than a manual click someone remembers to perform.

The first prevention is to treat consent as a deployment artifact. When a release adds or changes a permission on a non-interactive application, the same release should record the grant. A pipeline step that runs the admin consent action against the target tenant, gated behind the right administrative credentials, keeps the permission and its approval synchronized. This single habit eliminates the new-scope cause and the silent-failure-after-deploy pattern that produces most repeat incidents.

The second prevention is a deliberate user consent policy. Decide, as a tenant administrator, which classes of delegated permission users may approve for themselves and which require review. A policy that permits low-risk delegated approvals for verified-publisher apps reduces friction for routine access while still routing sensitive permissions through an administrator. Setting this intentionally, rather than leaving it at a default you have not examined, means fewer surprise escalations to admin consent and fewer users stuck at a prompt they cannot complete.

The third prevention is an admin consent request workflow. Entra lets you enable a process where users who hit a permission they cannot approve can submit a request, and designated reviewers approve or deny it. Turning this on converts a dead-end error into a tracked request, which is far better than a user filing a help ticket or, worse, abandoning the task. It also gives administrators a queue and an audit trail, so consent decisions are visible rather than scattered across individual sign-ins.

The fourth prevention is least privilege at the registration. Many AADSTS65001 incidents trace back to an application requesting more than it needs, which makes every grant heavier and every review slower. Requesting only the permissions the app genuinely uses keeps grants small, keeps admin review fast, and reduces the surface that has to be re-approved when anything changes. Reviewing an application's requested permissions periodically and trimming what is unused is quiet work that prevents a surprising amount of future friction.

The fifth prevention, for multi-tenant apps, is to bake the admin consent URL into onboarding. If every new customer tenant is brought online through the `adminconsent` link, the grants are recorded in the right directory from the first day, and the wrong-tenant failure simply never happens. Documenting that step as part of customer setup is cheaper than diagnosing the same production-only failure repeatedly.

## The on-behalf-of flow and AADSTS65001

Middle-tier APIs add a layer that produces a distinctive version of this error, and it trips up engineers building layered services. In the on-behalf-of flow, a client calls your API with a user's token, and your API needs to call a downstream API, such as Microsoft Graph, as that same user. Your API exchanges the incoming user token for a new token to the downstream resource. That exchange runs through the token endpoint and is subject to the same approval gate as any other token request, which means it can fail with AADSTS65001 for a reason that lives two hops away from where the symptom shows up.

There are two separate approvals in play, and confusing them is the usual mistake. The first is the client's authorization to call your middle-tier API, which must be approved like any delegated scope. The second is your middle-tier API's authorization to call the downstream resource on the user's behalf, which is a delegated permission your API holds against that resource. When the on-behalf-of exchange fails with AADSTS65001, it is almost always the second approval that is missing: the user, or an administrator, never authorized your API to access the downstream resource for that user, even though the client was perfectly authorized to call your API.

The confirming check follows the token's journey. Verify that the client is authorized for your API's scope, then verify that your API's service principal holds the delegated permission it needs on the downstream resource and that the permission has been approved in the user's tenant. The fix is to authorize that downstream permission, by the user where the permission is user-approvable and the tenant allows it, or by an administrator where it is sensitive or where the tenant restricts user approval. Because the on-behalf-of flow runs server to server during the exchange, it cannot show a prompt at exchange time, so a downstream permission that requires interaction must be pre-authorized through the normal sign-off mechanisms before the exchange will ever succeed. The token flows this builds on are the same ones described in the [Entra ID authentication explainer](/2023/12/18/entra-id-authentication-explained/).

## Token caching and why a fresh grant seems not to take effect

A grant that you know is correct can appear to do nothing, and the culprit is usually a cached token rather than a failed authorization. Applications and identity libraries cache access tokens and refresh tokens to avoid hitting the token endpoint on every call. When you authorize a new permission, an in-memory token acquired before the sign-off does not retroactively gain the new access; it carries only the permissions it was issued with. The application keeps presenting the old token, the downstream call keeps failing, and it looks as though the grant did not work when in fact the application simply has not requested a new token yet.

The check is to confirm whether the application is reusing a token minted before the authorization. The fix is to force a fresh token acquisition. For a daemon using client credentials, that means clearing any cached token and requesting a new one, which on the next call will reflect the new approval, since `.default` resolves against the now-complete set of authorized permissions. For an interactive app, it can mean signing the user out and back in, or instructing the identity library to acquire a token rather than return a cached one, so the new scope is included in the request and consequently in the issued token.

This is a frequent source of false negatives during a fix. An engineer authorizes the permission, retries immediately, sees the same failure from a cached token, and concludes the grant was ineffective. Building the retry to acquire a genuinely new token, or simply waiting for the cached token to expire and the application to refresh, removes the illusion. When you validate a fix, validate it with a request that you know forces a new token, so a stale cache cannot mask a grant that actually succeeded.

## Grant propagation and timing

Most authorization changes in Entra take effect immediately, and a daemon that retries after an administrative sign-off usually succeeds on the very next call. There are two timing effects worth knowing so you do not misread a brief delay as a failed fix. The first is service principal provisioning. When a multi-tenant application is approved in a new tenant for the first time, the service principal that holds its grants is created as part of that approval. The creation and the recording of the grants are part of the same action, so by the time the administrative sign-off completes, the object and its approvals exist together. The case to watch is an application that has never signed in and never been provisioned in the tenant; until the service principal exists, there is nothing to authorize, and the right first step is to create it through the admin consent URL, which provisions and authorizes in one motion.

The second effect is directory replication. Entra is a globally distributed directory, and while authorization changes propagate quickly, a request that happens to hit a replica a moment before the change has fully propagated can briefly see the old state. This is rare and short-lived, and the correct response is a short, bounded retry rather than re-authorizing, which would only record a grant that already exists. If a freshly authorized permission fails for a few seconds and then succeeds without any further action, replication timing was the cause, and no fix beyond patience was required. Distinguishing this from a genuine missing grant is straightforward: a true authorization gap does not clear on its own, while a propagation lag does. When in doubt, confirm the grant is present on the service principal, then retry; if the object shows the approval, time will resolve the rest.

## Errors AADSTS65001 is confused with

Several Entra errors share the family resemblance of an app that will not get a token, and telling them apart saves time because their fixes differ. AADSTS65001 specifically means consent is missing, so distinguishing it from its neighbors keeps you from applying a consent fix to a problem that is not about consent at all.

The closest neighbor is the case where a user actively declines the consent prompt rather than the prompt being absent. That produces a different code in the AADSTS65004 range and a description noting that the user declined to consent. The fix there is not an administrative grant but a conversation with the user or a reconsideration of what the app is asking for, because the approval mechanism worked, the human just said no.

A more confusing neighbor is the application-not-found error, AADSTS700016, which says the application could not be located in the directory. That is not a consent problem; it is an identity problem, and it usually means the client ID is wrong, the authority points at the wrong tenant, or the service principal was never provisioned in the tenant. The two errors can feel similar in a multi-tenant context because both can appear when an app runs in a tenant it was not set up in, but the remedies diverge: 700016 wants you to verify the application exists in the right tenant, while 65001 wants you to approve a permission for an application that does exist. The full diagnosis of the not-found case is covered in the [guide to fixing AADSTS700016 when the application is not found](/2022/09/26/fix-aadsts700016-app-not-found/).

The redirect URI mismatch, AADSTS50011, is a third sibling that also blocks sign-in but for an unrelated reason: the reply URL the app sent does not match a value registered for it. It surfaces at roughly the same point in an interactive flow, which is why it gets mixed up with consent failures, but its fix lives entirely in the app registration's redirect configuration rather than in any permission grant. The step-by-step remedy is in the [walkthrough of the AADSTS50011 redirect URI mismatch](/2022/09/19/fix-aadsts50011-redirect-uri/).

Finally, AADSTS65001 is sometimes confused with an authorization failure on an Azure resource, the AuthorizationFailed error returned by Azure Resource Manager when an identity lacks a role. Those look related because both are about an identity not being allowed to do something, but they live in different systems. AADSTS65001 is about Entra application permissions and consent; AuthorizationFailed is about Azure role-based access control on resources. An identity can have full consent and still be denied a resource action for want of a role, and the reverse holds too. The distinction, and the least-privilege approach to fixing the resource side, is the subject of the [guide to Azure RBAC AuthorizationFailed errors](/2022/10/10/fix-azure-rbac-authorizationfailed/).

## Auditing who authorized an application

Once you have fixed an AADSTS65001 incident, and especially in a tenant where several administrators can authorize applications, you will want a record of who approved what and when. The Entra audit logs capture authorization events as discrete entries, which turns a fix into something traceable rather than a quiet change nobody can later reconstruct. This matters for security review, because a tenant-wide approval is a meaningful expansion of an application's reach, and it matters for incident response, because a sudden new approval can be the first visible sign of a problem.

Open the audit logs in the Entra admin center and filter to the directory activities that record approvals. An administrative sign-off appears as an event noting that consent was granted to an application, with the actor, the target application, and the permissions involved. A delegated approval recorded for all principals and an application permission recorded as an app role assignment each leave their own entry. Reading these entries against the timeline of your incident confirms not only that the fix landed but that the right person made it, which is exactly the evidence a security review asks for.

From Microsoft Graph, the same events are queryable as directory audit records, which lets you build a recurring check rather than a manual one. A scheduled query that surfaces newly granted application permissions, particularly the high-privilege ones, gives administrators an early warning of broad approvals they did not expect. Treating approval events as security-relevant signals, not just operational noise, is the posture that keeps a tenant's application surface understood over time. The same least-privilege and auditability mindset applies to resource access through roles, which is covered in the [guide to Azure RBAC AuthorizationFailed errors](/2022/10/10/fix-azure-rbac-authorizationfailed/), and the two together give you a complete view of what an identity is allowed to do and who allowed it.

## A triage order for AADSTS65001

When the error lands and the clock is running, a fixed order of checks beats trying remedies at random. Begin by reading the full error, not the short code, and pull the application ID and the resource or scope from the description and the sign-in logs. That first step confirms you are working on the right application and tells you which API was being reached, which narrows everything that follows.

Next, classify the permission. Decide whether the failing access is a delegated permission or an application permission, because that single fact routes the rest of the diagnosis. An application permission means an administrator is the only path, full stop. A delegated permission means you then check the tenant's user consent policy and the permission's risk level to learn whether a user can authorize it or whether it has been escalated to an administrator.

Then locate the tenant. Identify the directory the failing request authenticated against and confirm whether the application and its grants exist there, since a perfectly valid approval in the wrong tenant is the most common production-only cause. Finally, record the missing approval where the request can find it, verify on the enterprise application that the grant is present, and re-run the original flow with a freshly acquired token so a cached one does not mask the result. Worked end to end, that order, read, classify, locate, authorize, verify, turns the error from a guessing game into a short, repeatable procedure.

## The verdict

AADSTS65001 reads like an obstacle and behaves like a checklist. The error is not transient, not a broken registration, and not something a sign-in retry can clear. It is the platform reporting that a permission was requested and never approved, and the fix is to record the approval where the request can find it. The whole diagnosis collapses to two questions: what kind of permission is this, and which tenant must hold the grant. Answer the first with the delegated-versus-application split, lean on the application-permission-needs-admin rule, and you immediately know whether a user can help or whether only an administrator can. Answer the second by confirming which directory the failing request authenticated against, and you avoid the most common production-only failure, a perfectly valid grant sitting in the wrong tenant.

If you want a place to reproduce the failure safely and rehearse the fix, you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to stand up an app registration, trigger the consent gate, and practice both the portal grant and the command-line grant against a sandbox tenant. To sharpen the diagnostic reflex itself, telling 65001 apart from its lookalikes under time pressure, you can [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html), which pose the failing flow and ask you to name the cause and the grant path. The combination of reproducing the gate and drilling the classification is what turns AADSTS65001 from a recurring surprise into a thirty-second fix.

The broader habit worth carrying away is to treat approval as state you manage rather than a box you click once and forget. Permissions are authorized one at a time, in one directory at a time, and they outlive any single deployment, so the engineers who never meet this error twice are the ones who record the sign-off alongside the change that needs it, scope each application to the minimum it actually uses, and onboard every new tenant through the admin consent URL so the grant lands where the request will look for it. Do that, and AADSTS65001 stops being a wall and becomes what it always was underneath: a short, honest message that a permission was requested and simply needs someone with the authority to approve it. Read the error, classify the permission, locate the tenant, record the grant, and verify with a freshly acquired token, and the failure resolves on the first attempt rather than the fifth.

## Frequently Asked Questions

### Q: What does AADSTS65001 consent required mean?

AADSTS65001 means a user or an administrator has not approved the application to use the permission it requested. Entra reached the authorization gate, found no approval on file for that specific permission in the current directory, and could not issue the token. It is not an authentication failure and not a transient platform fault. The identity may be perfectly valid; what is missing is the grant that allows the application to use a scope or an application permission against a resource such as Microsoft Graph. The platform suggests sending an interactive authorization request, which is its way of saying that someone needs to approve the access. The fix is therefore to record the missing approval, by a user or an administrator depending on the permission type, rather than to retry the sign-in or rebuild the application.

### Q: How do I grant admin consent to fix AADSTS65001?

You record an administrative approval for the application in the affected tenant. From the Entra admin center, open enterprise applications, select the app, open its permissions, and choose the grant admin consent action, which approves the requested permissions for the whole tenant. From the command line, run `az ad app permission admin-consent --id <client-id>`, which does the same in one call and requires a role allowed to grant tenant-wide approval. For a customer tenant you do not administer, send the administrator a link of the form `https://login.microsoftonline.com/{tenant}/adminconsent?client_id={client-id}`, which takes them straight to the approval page in their own directory. After the grant is recorded, the next token request for those permissions succeeds. Verify by checking the enterprise application's permissions blade or the sign-in logs for a success entry replacing the prior failure.

### Q: Do delegated permissions need consent for AADSTS65001?

Yes. Every delegated permission requires an approval on file before Entra issues a token carrying it. What changes is who is allowed to give that approval. For low-risk delegated permissions in a tenant that permits user consent, the signed-in user can approve the access for themselves through the interactive prompt. For higher-risk delegated permissions, or for any delegated permission in a tenant that restricts or disables user consent, an administrator must approve it instead. When a delegated permission falls outside what users may approve and the flow is non-interactive, the request returns AADSTS65001 rather than a prompt. So delegated permissions always need approval; the variable is whether a user can supply it or whether the permission has been escalated to require an administrator by its risk level or by tenant policy.

### Q: Why do application permissions require admin consent?

An application permission lets the app act as itself, with no signed-in user anywhere in the flow. A daemon, a scheduled job, or any client credentials workload runs this way. Because there is no user acting on whose behalf the app operates, there is no user who could approve the access, and there is no interactive session in which to show a prompt. Only a directory administrator has the authority to approve an application acting under its own identity against a resource. This is true in every tenant without exception, which is why the application-permission-needs-admin rule holds universally. When a background workload requesting an application permission has not received that administrative approval, it fails with AADSTS65001 on every token request until an admin records the grant. No user-level action can ever substitute for it.

### Q: Why does adding a new API scope trigger AADSTS65001?

Consent in Entra is recorded per permission, not per application. Approving an app for a set of scopes does not pre-approve any scope added later. The moment the application starts requesting a newly added permission, the platform finds no approval for that specific scope and blocks the token, even though every previously approved scope still works. In an interactive flow this surfaces as a fresh consent prompt; in a non-interactive flow it surfaces as AADSTS65001. The behavior is deliberate, since it stops an application from quietly widening its access by editing its registration. The remedy is to record the approval for the new scope as part of the same change that adds it. For client credentials workloads using `.default`, this is especially important, because that scope requests all configured permissions at once and an unapproved addition can break the entire token request, not just one feature.

### Q: How do I confirm consent on the enterprise application?

The enterprise application is the service principal for your app in the current tenant, and its permissions blade is the source of truth. Open enterprise applications in the Entra admin center, select the app, and open permissions to see exactly which scopes and application permissions have been approved, split between admin-granted and user-granted. A permission the app requests that appears in neither list is your missing grant. From Microsoft Graph PowerShell, read the grants directly off the service principal with `Get-MgServicePrincipalOauth2PermissionGrant` for delegated scopes and `Get-MgServicePrincipalAppRoleAssignment` for application permissions. The Azure CLI exposes a similar view through `az ad app permission list-grants`. Matching what is granted against what the registration requests tells you conclusively which permission lacks approval, and re-checking after a grant confirms the fix landed in the right directory.

### Q: Can I fix AADSTS65001 by just signing in again?

Usually not, and understanding why saves time. AADSTS65001 is not a stale session or a transient hiccup that a fresh sign-in clears. It reports that the required permission was never approved. Signing in again only helps in one narrow case: an interactive flow where the signed-in user is allowed to approve the permission and simply has not seen or completed the prompt yet. If the permission is an application permission, no sign-in helps, because no user can approve it. If the tenant restricts user consent and the permission exceeds what users may approve, signing in again still hits the same gate. When signing in as an administrator appears to fix it, what actually resolved the error was the administrative grant recorded during that sign-in, not the sign-in itself. Treat the error as a missing approval, not a session problem.

### Q: What is the difference between user consent and admin consent?

User consent is an individual approving an application to act on their own behalf for a delegated permission, recorded only for that user. Admin consent is an administrator approving an application for the entire tenant, recorded for all users at once. User consent is available only for delegated permissions and only when the tenant policy allows it for the permission's risk class. Admin consent covers both delegated permissions, granted for all principals, and application permissions, which can never be user-approved. The practical difference is reach and authority: a user grant satisfies one person's flows for low-risk scopes, while an admin grant satisfies everyone and is the only mechanism that can approve application permissions or sensitive scopes. When AADSTS65001 appears, classifying which kind of approval is required tells you whether a single user can resolve it or whether an administrator must act.

### Q: Why does a daemon using client credentials get AADSTS65001?

A client credentials workload authenticates as itself with a client ID and a secret or certificate, with no user present, and requests a token using the `.default` scope of the target resource. That request covers every application permission the app is configured for. If any required application permission has not been approved by an administrator in the tenant, the request fails with AADSTS65001, because there is no user to act for and no interactive prompt to display. The confirming check is to compare the application permissions the registration declares for the resource against the app role assignments actually present on the workload's service principal; a declared but unassigned permission is the cause. The fix is an administrative grant, which creates the missing app role assignment, after which the `.default` request resolves to the approved set and the token issues.

### Q: What does the .default scope do for consent?

The `.default` scope, written as `https://graph.microsoft.com/.default` or similarly for any resource, does not request a single named permission. It asks Entra for a token covering all permissions the application has been statically configured for and that have already been approved in the tenant. For client credentials flows it covers the application permissions; in delegated flows it covers the delegated scopes. Because it relies on pre-approval, `.default` never triggers an incremental prompt for a new permission. If any required permission is unapproved, the whole request can fail with AADSTS65001 rather than prompting for the missing piece. This is why workloads built on `.default` must have their permissions approved up front, and why a forgotten grant after adding a permission breaks the entire token request instead of one feature path.

### Q: How do I let users request admin consent instead of hitting a dead end?

Entra includes an admin consent request workflow that turns the error into a tracked request. When you enable it, a user who reaches a permission they cannot approve sees an option to submit a request for an administrator to review, rather than a bare failure. You designate reviewers, who receive the requests in a queue and can approve or deny them, and the decisions are recorded for audit. Configure it in the Entra admin center under enterprise applications, in the user consent and admin consent settings. Enabling this is a meaningful improvement over leaving users stuck, because it replaces an opaque AADSTS65001 with a self-service path that still keeps an administrator in control of what gets approved. It also gives you visibility into which applications users are trying to use, which informs your broader consent policy.

### Q: Where is consent stored in Microsoft Entra ID?

Consent is stored on the service principal, the enterprise application object that represents your app inside a specific tenant. Delegated approvals are recorded as OAuth2 permission grant objects, each naming the client, the resource, the consent type, and the approved scopes, with a consent type of AllPrincipals for admin grants or a specific principal for individual user grants. Application permission approvals are recorded as app role assignments on the service principal, each naming the resource and the granted role. Because these objects live on the service principal and the service principal is scoped to one tenant, consent is inherently per-directory. The same multi-tenant application has a separate service principal, with its own grants, in every tenant that uses it. This is the reason a grant in one directory has no effect in another, and why the wrong-tenant cause of AADSTS65001 exists at all.

### Q: How do I revoke consent I granted by mistake?

Open the enterprise application for the app in the Entra admin center, go to its permissions, and remove the granted permissions you no longer want, which deletes the underlying grant objects. From Microsoft Graph PowerShell you can delete a specific OAuth2 permission grant with `Remove-MgOauth2PermissionGrant` for a delegated approval, or remove an app role assignment with `Remove-MgServicePrincipalAppRoleAssignment` for an application permission. To withdraw an application's access entirely, you can disable or delete its service principal in the tenant, which removes all of its grants at once. Revoking consent is the right move when an app was approved for more than it needs or when an integration is being retired. After revoking, expect the app's next request for the removed permission to fail with AADSTS65001, which in that case is the system correctly reflecting that the approval is gone.

### Q: Does AADSTS65001 mean my app registration is broken?

No. The app registration being broken or missing produces a different error, AADSTS700016, which says the application was not found in the directory. AADSTS65001 presupposes that the application exists and is recognized; it reports only that a permission has not been approved. The two can feel similar in a multi-tenant scenario, where an app running in an unfamiliar tenant might hit either one, but they call for different fixes. A 700016 sends you to verify the client ID, the authority tenant, and whether the service principal was provisioned. A 65001 sends you to approve a permission for an application that the directory already knows about. If you see 65001, the registration is fine; the grant is what is missing.

### Q: Can I grant admin consent with Azure CLI or PowerShell?

Yes, and automation often should. The Azure CLI grants consent for everything an app currently requests with `az ad app permission admin-consent --id <client-id>`, run by an identity allowed to grant tenant-wide approval. Microsoft Graph PowerShell offers finer control: create an OAuth2 permission grant with a consent type of AllPrincipals for a delegated permission, or create an app role assignment for an application permission, granting exactly one permission at a time. Scripting the grant is the right approach for pipelines, where the release that adds a permission should also record its approval against the target tenant. Doing it in code keeps the permission and its consent synchronized across deployments and tenants, which is the durable cure for the new-scope failure that otherwise reappears every time someone forgets to click the portal button.

### Q: Why did consent work in my dev tenant but fail in the customer tenant?

Because consent lives on the service principal inside each tenant, and your grant in the development directory was recorded only there. A multi-tenant application gets a separate service principal in every tenant that uses it, and a new tenant's service principal starts with no approvals. Your code, your client ID, and your requested permissions are identical across tenants, but the grant is not, so the customer tenant returns AADSTS65001 until one of its administrators approves the app. The fix is to record the approval in the customer's directory, typically by sending their administrator the admin consent URL for your client ID so they can approve in one step. Building that link into your onboarding flow provisions the service principal and its grants together, which eliminates this production-only failure for every future customer.

### Q: What is the admin consent URL and how do I use it?

The admin consent URL sends a tenant administrator directly to the approval page for your application in their own directory. Its form is `https://login.microsoftonline.com/{tenant}/adminconsent?client_id={client-id}`, where you replace the tenant placeholder with the target tenant ID or a verified domain and the client ID with your application's ID. When an administrator of that tenant opens the link, signs in, and approves, Entra records admin consent for the requested permissions on the service principal in their directory and provisions that service principal if it did not yet exist. This is the standard mechanism for onboarding a multi-tenant application into a customer tenant, and it is the cleanest fix for the wrong-tenant cause of AADSTS65001, because the grant lands precisely in the directory that serves the failing request rather than in yours.

### Q: How do I tell which permission is missing consent from the error?

Capture the full OAuth error description rather than the short code, because the description frequently names the scope or resource that failed. In a redirect flow it rides in the response sent back to your application; in a direct token call it sits in the JSON body of the failed response. The Entra sign-in logs add the platform's view, naming the application and the resource and giving a correlation ID. With the resource identified, open the enterprise application's permissions and compare what the app requests against what has been granted; the requested-but-ungranted permission is your answer. For a `.default` request the error may not name one scope, since the request covered all configured permissions, so in that case enumerate the declared permissions and find the one without a matching grant on the service principal.

### Q: Why does my middle-tier API hit AADSTS65001 during the on-behalf-of flow?

In the on-behalf-of flow, your API exchanges an incoming user token for a downstream token, and that exchange passes through the same approval gate as any token request. There are two distinct approvals involved: the client's authorization to call your API, and your API's authorization to call the downstream resource on the user's behalf. An on-behalf-of exchange that fails with AADSTS65001 almost always lacks the second one, meaning no user or administrator authorized your API to reach the downstream resource for that user. Because the exchange happens server to server, it cannot present a prompt, so a downstream permission that needs interaction must be pre-authorized before the exchange will succeed. Confirm that your API's service principal holds and has had approved the delegated permission it needs on the downstream resource in the user's tenant, then authorize it by the user or an administrator as the permission's risk and the tenant policy require.

### Q: How is AADSTS65001 different from AADSTS65004?

The two codes sit next to each other but describe opposite situations. AADSTS65001 means no approval is on file and, in a non-interactive flow, there was no way to ask for one. AADSTS65004 means a user was asked and actively declined to approve the access. The consent mechanism worked in the 65004 case; a person saw the prompt and said no. That changes the fix entirely. For 65001 you record the missing approval, by a user or an administrator depending on the permission. For 65004 there is nothing technical to grant on the spot, because the decision was a deliberate refusal. The right response is to understand why the user declined, reconsider whether the application is requesting more access than the task warrants, and either trim the request to what is genuinely needed or, where the access is appropriate and the tenant allows it, route it through an administrator who can authorize it for everyone.
