---
layout: post
title: "Configure Conditional Access Policies the Safe Way"
page_title: "Configure Conditional Access Policies: Require MFA, Report-Only Mode, Break-Glass Exclusions, and Blocking Legacy Auth in Microsoft Entra ID"
date: 2023-07-31
categories: ["Technology"]
tags: ["Azure", "Conditional Access", "Microsoft Entra ID", "Security", "Identity"]
excerpt: "Configure Conditional Access policies in Entra ID with report-only mode testing, a break-glass exclusion, required MFA, and blocked legacy auth, safely."
image: "/assets/images/blog/blog-90.webp"
reading_time: 61
author: "benjamin-scott"
last_updated: 2023-07-31
lang: en
---
A Conditional Access policy in Microsoft Entra ID is the gate that decides whether a sign-in proceeds, proceeds with an extra requirement, or stops. Configure that gate correctly and you raise the security floor for an entire tenant in an afternoon: you require multifactor authentication where it matters, you shut the door on the legacy authentication protocols that quietly skip every modern control, and you do all of it without surprising a single legitimate user. Configure the same gate carelessly, and you can lock every administrator out of the tenant in the time it takes to click Enable.

![Configure Conditional Access Policies the Safe Way - Insight Crunch](/assets/images/blog/blog-90.webp)

That asymmetry is the whole reason this topic deserves a careful procedure rather than a quick walkthrough. A policy that requires MFA from an untrusted location protects the organization. The identical policy, enforced before anyone tested it, with no account left outside its scope, will block the people who would otherwise fix it. The Entra ID sign-in logs fill with failures, the help desk phone rings, and the only accounts that could reverse the policy are themselves caught behind it. Recovery from that state is possible but slow, and it is entirely avoidable.

This guide treats Conditional Access configuration as a sequenced operation with a safety rail at every step. The work itself is not difficult. The discipline is in the order: define the assignments and conditions, set the grant controls, exclude a break-glass account, watch the policy run in report-only mode against real traffic, and only then turn on enforcement and close out legacy authentication. Skip the report-only step or the break-glass exclusion and the procedure becomes a gamble. Follow them and a tenant-wide security change carries almost no operational risk.

## The InsightCrunch Conditional Access Setup Checklist

The findable artifact for this article is a checklist you can run end to end, with the trap that lurks at each step called out explicitly. Every later section expands one of these rows into working configuration, the verification that proves it took effect, and the symptom you will see if you got it wrong.

| Step | Action | The gotcha to avoid |
| --- | --- | --- |
| 1 | Define assignments: which users and groups, which cloud apps, under which conditions | Targeting "All users" without excluding anyone leaves no account outside the blast radius |
| 2 | Set grant controls: require MFA, require a compliant or hybrid-joined device, or block | Choosing Block without understanding scope is how an organization-wide lockout starts |
| 3 | Exclude a break-glass account before anything is enabled | A break-glass account added after enforcement is added too late to help during a lockout |
| 4 | Create the policy in report-only state, not enforced | Enabling On as the first action means the first test of the policy is against production sign-ins |
| 5 | Read the report-only results in the sign-in logs for several days | Reading one day of logs misses the weekly batch job or the monthly finance login |
| 6 | Switch the tested policy to On and enforce it | Flipping every policy On at once makes a failure impossible to attribute to one policy |
| 7 | Add a separate policy that blocks legacy authentication | Blocking legacy auth in the same policy as everything else hides which rule broke a client |

The two non-negotiable rows are step three and step four. Everything else is a refinement. The break-glass exclusion is what guarantees you can always get back in, and report-only mode is what guarantees you learn the rule's real impact before a user ever feels it. Hold those two fixed and the rest of the configuration becomes a matter of taste and requirement.

## What Correct Conditional Access Configuration Buys You

Before the mechanics, it is worth being precise about what this control actually does and does not do, because the configuration decisions flow directly from that model. A Conditional Access policy evaluates after the first authentication factor succeeds and before the session is issued. The user has proven they know the password (or presented a passwordless credential), and Entra ID now asks a second question: given everything I know about this sign-in, what else do I require, and should I allow it at all?

The InsightCrunch model of [Microsoft Entra ID](/2022/02/21/microsoft-entra-id-explained/) treats the directory as the system of record for identities, applications, and the role assignments that connect them, and a Conditional Access policy sits one layer above that, governing how those identities are allowed to authenticate into those applications. If the identity model itself is unfamiliar, the [sign-in flow that Conditional Access decorates](/2023/12/18/entra-id-authentication-explained/) is worth understanding first, because a policy condition like "device state" or "sign-in risk" only means something once you know where in the token-issuance flow it is evaluated.

A correctly configured set of policies gives you four concrete wins. First, MFA is required exactly where the risk justifies the friction, rather than everywhere (which trains users to approve prompts reflexively) or nowhere (which leaves passwords as the only barrier). Second, legacy authentication, the older protocols that cannot present an MFA challenge, is blocked, so an attacker cannot simply ask for the one door that has no second lock. Third, access decisions can incorporate device compliance, location, and risk signals, so a sign-in from a managed laptop on the corporate network is treated differently from the same account on an unrecognized device in an unexpected country. Fourth, every one of these decisions is logged, testable, and reversible, which is what makes the control safe to operate at all.

### What signals and conditions can a Conditional Access policy use?

A policy assigns to users or groups, to cloud apps or user actions, and then narrows with conditions: sign-in risk, user risk, device platform, location, client app type, and device state. The grant controls then require MFA, a compliant device, a hybrid-joined device, terms of use, or simply block. Each condition is an AND that tightens the rule's scope.

The signals split into two roles, and keeping them straight prevents most configuration mistakes. The assignments decide who and what the policy applies to. The conditions narrow that down to particular circumstances. The grant controls decide what happens when all of that matches. A policy that says "all users, all apps, when signing in from outside trusted locations, require MFA" reads cleanly in that structure: the assignment is all users and all apps, the condition is the location, and the grant control is the MFA requirement.

Location is one of the most useful conditions and one of the most misconfigured. A named location is a range of IP addresses or a set of countries you have defined as meaningful, typically your office egress IPs marked as trusted. A policy can then require MFA from anywhere except those trusted locations, which removes the prompt for users sitting in the office while still protecting remote sign-ins. The trap is that home and mobile users are, by definition, never in a trusted location, so a policy keyed too aggressively on location can prompt your entire remote workforce on every sign-in. The fix is usually to combine location with device state, so a compliant managed device is trusted regardless of network.

Device state as a condition lets a policy distinguish a sign-in from an Intune-compliant or hybrid Entra-joined device from one on an unmanaged machine. This is the condition that makes a "require a compliant device" grant control enforceable, and it is the cleaner long-term answer than location for deciding what counts as trusted, because a device travels with the user while a network does not.

Risk-based conditions (sign-in risk and user risk) require the higher Entra ID licensing tier that includes Identity Protection, and they let a policy react to Microsoft's real-time and offline risk scoring: require MFA on a medium-risk sign-in, force a secure password change on a high user risk, block on the highest tier. These are the most far-reaching conditions available, but they are not the place to start, because a misjudged risk policy produces intermittent, hard-to-reproduce prompts that erode trust in the whole system. Start with the deterministic conditions (location, device, client app) and add risk once the foundation is stable.

## The Report-Only-and-Break-Glass Rule

The namable claim of this article is a rule you can state in one sentence and apply to every policy you ever build: a Conditional Access policy is tested in report-only mode and always excludes a break-glass account, because enforcing a policy that has not been tested, or one with no account left outside its reach, is the classic way an organization locks itself out of its own tenant. Those two conditions are not optional refinements layered on top of a good policy. They are the definition of a safe policy. A technically perfect policy that is enforced cold, with no exclusion, is an unsafe policy regardless of how correct its logic is.

The rule has teeth because the failure it prevents is so severe and so common. Search any administrator forum and the same story recurs: someone built a sensible MFA policy, scoped it to all users, enabled it, and discovered that the administrator account they were signed in with did not yet have an MFA method registered, or that the rule's own grant control could not be satisfied from where they were sitting. The account that could disable the policy was the account the policy had just locked out. The recovery path exists, but it involves a separate emergency credential, support escalation, or in the worst cases a wait, and all of it is unnecessary if the rule was followed.

Report-only mode is the half of the rule that addresses the unknown. You can reason carefully about a policy and still be wrong about its real-world impact, because you do not have a complete picture of every service account, every scheduled job, every mobile client, and every odd sign-in pattern in the tenant. Report-only mode resolves that uncertainty empirically: the policy evaluates every matching sign-in and records what it would have done, while doing nothing. After several days of real traffic you have data, not a guess, about who it would have affected.

The break-glass exclusion is the half that addresses the catastrophic case even when report-only has done its job. No amount of testing is a guarantee, and the cost of being wrong with no way back is total. A break-glass account, excluded from every Conditional Access policy and protected by other means, is the account that is always able to sign in and undo a mistake. It is the difference between a bad afternoon and a tenant-wide outage.

### Why do I need a break-glass account excluded from every policy?

A break-glass account is a highly privileged emergency account, excluded from all Conditional Access policies, so that a misconfigured or overly broad policy can never lock every administrator out. When enforcement blocks the accounts that would normally fix it, the excluded break-glass account remains able to sign in and disable the offending rule.

The reason the exclusion must cover every policy, not just the one you are currently editing, is that lockouts are usually caused by the interaction of policies rather than by one in isolation. You might exclude the break-glass account from your new MFA policy and forget that a separate device-compliance policy, written months earlier, still applies to it. During an incident the break-glass account hits that older policy, fails its grant control, and is locked out exactly when it is needed. The discipline is to maintain a dedicated security group for break-glass accounts and add that group to the exclusion list of every Conditional Access policy as a standing practice, so a new policy is never created without the exclusion already in place.

Protecting the break-glass account itself is the obvious follow-up question, because an account excluded from all your access policies is a tempting target. The account should use a long, randomly generated password stored in a sealed, audited location, be a cloud-only account so an on-premises directory outage cannot affect it, and be monitored with an alert that fires on any sign-in, since a legitimate break-glass sign-in is a rare and noteworthy event. Many organizations maintain two such accounts so a single compromised or lost credential does not eliminate the recovery path. The point is that the account is excluded from Conditional Access but is not therefore unprotected; the protection simply lives outside the access-policy system.

## Prerequisites and the Correct Order of Operations

Three things need to be true before you create your first policy, and getting them in place first is what makes the rest of the procedure smooth. You need the right role, you need a break-glass account ready, and you need at least a rough inventory of how people and services actually authenticate today.

The role you need is Conditional Access Administrator or Security Administrator, or the broader Global Administrator. The narrower roles are the better choice under least privilege, because creating and managing access policies does not require the keys to the entire tenant. Whichever role you use, you will be signing in with it while you build policies that could affect it, which is precisely why the break-glass account has to exist before you start rather than after.

The break-glass account has to be created, granted the Global Administrator role, given a registered authentication method or deliberately left without grant controls it cannot meet, and placed in a security group that you will exclude from every policy. Do this first, verify you can sign into it in a private browser session, and keep that session or a recorded recovery path available while you work. This is the seatbelt, and you fasten it before you start the engine.

The authentication inventory does not need to be exhaustive, but you need a sense of the shape of your sign-in traffic before you scope anything to all users. The Entra ID sign-in logs, filtered by client app, will show you whether legacy authentication is still in use and by whom, which service accounts sign in on schedules, and which applications carry the bulk of traffic. Thirty minutes reading those logs before you write a policy will save you from the surprises that report-only mode would otherwise have to catch later. The correct privileged-access design that governs which roles can even make these changes is worth aligning with here, so that the people configuring access policies are themselves governed by sound role assignment.

The order of operations, then, is fixed and worth committing to memory. Create and verify the break-glass account and its exclusion group. Inventory the sign-in traffic. Define the rule's assignments and conditions. Set its grant controls. Confirm the break-glass exclusion is present. Create the policy in report-only state. Let it run against real traffic for several days and read the results. Promote the tested policy to enforced. Finally, in a separate policy, block legacy authentication. Every step in the next sections maps to one of these, in this order, for a reason.

## Step-by-Step Setup With Working Configuration

The portal is the right place to learn Conditional Access, because its policy blade lays out assignments, conditions, and grant controls in the same structure described above, and report-only is a first-class state on every policy. But the durable, reviewable, and repeatable way to manage policies is through the Microsoft Graph API, either directly or through the Microsoft Graph PowerShell module, and the configuration that follows uses Graph so the same policy can later be committed to source control.

### How do I create a Conditional Access policy that requires MFA?

Create a policy that assigns to your target users and apps, adds the condition you want, and sets the grant control to require multifactor authentication with a state of enabledForReportingButNotEnforced. That last value is report-only mode. The policy evaluates and logs every matching sign-in without enforcing the MFA requirement until you change the state to enabled.

Start by connecting with the Graph PowerShell module and the scope that lets you manage policies. The first sign-in will prompt for consent on these permissions.

```powershell
# Install once if needed: Install-Module Microsoft.Graph -Scope CurrentUser
Connect-MgGraph -Scopes "Policy.ReadWrite.ConditionalAccess", "Policy.Read.All", "Group.Read.All"

# Confirm the connected context and the scopes granted
$context = Get-MgContext
$context | Format-List Account, Scopes
```

Next, resolve the object IDs you will reference: the break-glass exclusion group, and any group the policy targets. Referencing groups by display name in a script is fragile, so look up the immutable IDs once and use those.

```powershell
# The standing exclusion group that holds every break-glass account
$breakGlassGroup = Get-MgGroup -Filter "displayName eq 'SG-BreakGlass-Exclusions'"
$breakGlassGroupId = $breakGlassGroup.Id

# A pilot group you will target first instead of all users
$pilotGroup = Get-MgGroup -Filter "displayName eq 'SG-CA-Pilot'"
$pilotGroupId = $pilotGroup.Id

Write-Host "Break-glass exclusion group: $breakGlassGroupId"
Write-Host "Pilot target group:          $pilotGroupId"
```

Now define the policy itself. The shape of this object mirrors the portal exactly: a conditions block holding the assignments and conditions, a grantControls block holding the requirement, and a top-level state. Note the state value: the policy is born in report-only mode.

```powershell
$params = @{
    displayName = "CA001 - Require MFA for All Apps (Pilot)"
    state       = "enabledForReportingButNotEnforced"   # report-only
    conditions  = @{
        users = @{
            includeGroups = @($pilotGroupId)
            excludeGroups = @($breakGlassGroupId)        # the safety rail
        }
        applications = @{
            includeApplications = @("All")
        }
        clientAppTypes = @("all")
    }
    grantControls = @{
        operator        = "OR"
        builtInControls = @("mfa")
    }
}

$policy = New-MgIdentityConditionalAccessPolicy -BodyParameter $params
Write-Host "Created policy $($policy.DisplayName) in state $($policy.State)"
```

Three things in that object carry the safety of the whole procedure. The excludeGroups entry is the break-glass exclusion, present at creation rather than added later. The includeGroups entry targets a pilot group rather than All, so even in report-only the data you gather is from a representative subset before you widen the scope. And the state is the report-only value, so nothing about this rule enforces anything yet. You have created a policy that watches and records, scoped to a pilot, with the recovery account already outside its reach.

### What signals do I add to narrow the policy?

To require MFA only from outside trusted locations, first define a named location for your trusted egress IPs, then add a locations condition that includes all locations and excludes the trusted one. The rule then evaluates its MFA requirement everywhere except the addresses you have marked as trusted, removing the prompt for in-office sign-ins.

A named location is its own object, created once and referenced by many policies. The example below defines a trusted IP range and marks it trusted, which is what lets a policy treat it specially.

```powershell
$locationParams = @{
    "@odata.type" = "#microsoft.graph.ipNamedLocation"
    displayName   = "Corporate Egress IPs"
    isTrusted     = $true
    ipRanges      = @(
        @{
            "@odata.type" = "#microsoft.graph.iPv4CidrRange"
            cidrAddress   = "203.0.113.0/24"
        }
    )
}

$trustedLocation = New-MgIdentityConditionalAccessNamedLocation -BodyParameter $locationParams
$trustedLocationId = $trustedLocation.Id
```

With the location defined, the rule's conditions block gains a locations entry. Including "All" and excluding the trusted location ID is the idiom that means "everywhere except the office."

```powershell
$conditionsWithLocation = @{
    users = @{
        includeGroups = @($pilotGroupId)
        excludeGroups = @($breakGlassGroupId)
    }
    applications = @{
        includeApplications = @("All")
    }
    clientAppTypes = @("all")
    locations = @{
        includeLocations = @("All")
        excludeLocations = @($trustedLocationId)
    }
}

Update-MgIdentityConditionalAccessPolicy -ConditionalAccessPolicyId $policy.Id `
    -Conditions $conditionsWithLocation
```

The same pattern extends to device state, client app type, and the rest. Each condition you add tightens the set of sign-ins the policy matches, and because every condition is combined with AND, a policy with several conditions matches only the sign-ins that satisfy all of them. Build conditions one at a time and confirm the matched population in report-only before adding the next, rather than writing a policy with five conditions at once and trying to reason about the intersection in your head.

## Report-Only Mode: Testing Before You Enforce

Report-only mode is the single most valuable feature in the Conditional Access system for anyone who wants to make changes without causing incidents, and it deserves to be understood precisely rather than treated as a checkbox. A policy in the enabledForReportingButNotEnforced state is fully live in the sense that it evaluates every sign-in that matches its assignments and conditions, runs its grant controls, and records the result. It is inert in the sense that the result changes nothing: a sign-in that it would have challenged for MFA still proceeds without the challenge, and a sign-in it would have blocked still succeeds.

### What does report-only mode actually evaluate?

Report-only mode evaluates the policy against live sign-ins and records, per sign-in, whether it would have granted access, required a control such as MFA, or blocked, without enforcing any of it. The result appears in the sign-in log under the report-only tab, so you see the rule's real impact on real traffic before a user ever experiences it.

The data lands in two places, and both are worth knowing. Each individual sign-in in the Entra ID sign-in logs gains a report-only tab showing every report-only policy that evaluated it and what each would have done: not applied, would have granted, would have required MFA, or would have failed the control. Aggregated across all sign-ins, the Conditional Access Insights workbook in the portal summarizes the same data, so you can see at a glance how many sign-ins a report-only policy would have affected, how many would have been blocked, and which users and applications are involved. The workbook is the faster way to spot a problem; the per-sign-in tab is where you confirm exactly why a particular sign-in would have failed.

What you are looking for in that data is the gap between what you intended and what the policy actually matches. You intended to require MFA for interactive user sign-ins from outside the office. The report-only data might reveal that a scheduled reporting job authenticates as a user account from a datacenter IP and would now be challenged for an MFA prompt it can never answer, or that a conference-room device signs in from an IP you did not include in the trusted range. Each of those is a problem you would rather discover in a log than in a help desk queue. The fix is to refine the policy (exclude the service account, widen the trusted range, add a device condition) and let report-only run again until the only sign-ins the policy would affect are the ones you meant to affect.

How long to leave a policy in report-only is a judgment call, but the principle is to cover the full cycle of your organization's sign-in patterns. A few days catches the daily rhythm. A full week catches the weekly batch jobs and the people who only come in on certain days. If a monthly process matters (month-end finance, a monthly report run), it is worth either waiting for that cycle or specifically confirming how those accounts would be treated. The cost of waiting is low; the cost of enforcing into an unobserved pattern is exactly the incident report-only exists to prevent.

## The Settings the Defaults Get Wrong

A new policy created through the portal starts with defaults that are reasonable for learning and wrong for production, and knowing which ones to change is most of the difference between a policy that helps and one that surprises you.

The first default to scrutinize is the client app types condition. Left at its default, a policy applies to all client app types, which includes both modern authentication clients and the legacy authentication clients. That sounds comprehensive, but it has a subtle consequence: a legacy client cannot perform an interactive MFA challenge, so a rule that requires MFA and applies to legacy clients does not actually secure those legacy sign-ins the way you expect. The cleaner design, covered below, is to handle modern and legacy clients in separate policies, so an MFA-requiring policy targets only the modern clients that can satisfy it, and a separate policy blocks legacy clients outright.

The second is the scope of the users assignment. The portal makes it trivial to select All users, and for a mature policy that is often correct, but as a default for a policy you are about to enable it is the most dangerous setting available, because it maximizes the blast radius. The discipline is to start every policy against a pilot group, confirm its behavior in report-only, widen to all users still in report-only, confirm again, and only then enforce. The exclude side of the users assignment is equally important and equally easy to leave empty: an empty exclusion list means no account is outside the policy, which is the precondition for a lockout. The break-glass exclusion group belongs there from the start.

The third is the grant controls operator. When a policy has multiple grant controls, the operator decides whether the user must satisfy all of them (AND) or any one of them (OR). A policy that requires MFA OR a compliant device lets a user on a managed device skip the prompt, which is usually what you want; the same controls combined with AND would require both, which is stricter and occasionally intended but rarely the default you want without thinking about it. The operator is easy to skim past and changes the meaning of the policy entirely.

The fourth is session controls, which default to none and are worth a deliberate decision rather than an oversight. Sign-in frequency and persistent browser session controls govern how often a user must reauthenticate and whether their session survives a browser close. Leaving them unset means the tenant defaults apply, which may be longer-lived sessions than a sensitive application warrants. These are a refinement rather than a step-one concern, but they are part of the policy and deserve a conscious choice.

## Verifying the Policy Took Effect

A policy you have enforced is not done until you have confirmed two things: that it does what you intended for the users it should affect, and that it does nothing to the break-glass account that must always get through. Verification is not optional polish; it is how you close the loop that report-only opened.

### How do I verify a Conditional Access policy is working?

Sign in as a test user who matches the policy and confirm the expected control fires, such as an MFA prompt. Then open that sign-in in the Entra ID sign-in logs and read the Conditional Access tab, which lists every policy that evaluated the sign-in and shows each as success, failure, or not applied. The applied policy should show success after the control is satisfied.

The sign-in log is the authoritative record, and learning to read its Conditional Access tab is the core verification skill. For any sign-in, the tab enumerates every policy that was in scope, and for each one shows the result. A policy that required MFA and got it shows as a success with the control satisfied. A policy that did not apply to this sign-in shows as not applied, with the condition that excluded it. A policy that failed shows as a failure, and the detail tells you which grant control was not met. When you enforce a policy, you verify it by signing in as an affected test account, satisfying the control, and confirming the log shows the policy applied and succeeded, then signing in as an account that should be out of scope and confirming the policy shows as not applied.

The break-glass verification is the one people skip and the one that matters most. After enforcing any policy, sign in with the break-glass account in a clean browser session and confirm it gets through without being subject to the policy. In the sign-in log for that session, every Conditional Access policy should show as not applied for the break-glass account, because it sits in the exclusion group on every policy. If even one policy shows as applied to the break-glass account, the exclusion has a gap, and you have found it during a controlled test rather than during the incident where it would have mattered. This single check, run after every enforcement, is what keeps the safety rail honest over time as policies accumulate.

## Blocking Legacy Authentication

Of all the baselines a tenant can adopt, blocking legacy authentication delivers the most security for the least effort, and it is the policy most worth getting right early. Legacy authentication refers to the older protocols and clients that authenticate with a username and password in a single step and have no mechanism to present a second factor: older mail protocols, older Office clients, and various scripts and devices that speak only basic authentication. Because these protocols cannot perform an MFA challenge, an attacker who has a valid password can use a legacy endpoint to sidestep every MFA policy you have built. The MFA requirement on the front door means nothing if there is a side door with no lock.

### How do I block legacy authentication with Conditional Access?

Create a dedicated policy whose client app types condition is set to the legacy clients (Exchange ActiveSync and other clients) and whose grant control is Block. Run it in report-only first to find which accounts still use legacy protocols, remediate or exclude them, then enforce. The rule then refuses any sign-in arriving over a legacy protocol.

The reason this belongs in its own policy rather than bundled into your MFA policy is attribution. When legacy auth is blocked by a dedicated, clearly named policy, a broken client immediately points you at the right rule, and you can read its report-only data in isolation to know exactly which accounts and applications still depend on legacy protocols. Bundling the block into a larger policy hides that signal and makes a future failure harder to trace to its cause.

```powershell
$legacyBlockParams = @{
    displayName = "CA010 - Block Legacy Authentication"
    state       = "enabledForReportingButNotEnforced"   # report-only first
    conditions  = @{
        users = @{
            includeUsers  = @("All")
            excludeGroups = @($breakGlassGroupId)
        }
        applications = @{
            includeApplications = @("All")
        }
        clientAppTypes = @("exchangeActiveSync", "other")   # the legacy clients
    }
    grantControls = @{
        operator        = "OR"
        builtInControls = @("block")
    }
}

$legacyPolicy = New-MgIdentityConditionalAccessPolicy -BodyParameter $legacyBlockParams
Write-Host "Legacy block policy created in state $($legacyPolicy.State)"
```

The clientAppTypes value is what makes this a legacy-only policy: by naming exchangeActiveSync and other (the bucket that holds basic-authentication clients) rather than all, the policy matches only legacy sign-ins and leaves modern authentication untouched. The grant control is block, with no exception, because a legacy sign-in is one you have decided not to permit at all.

Running this in report-only first is not a formality. The report-only data will show you every account still authenticating over a legacy protocol, and there is almost always at least one: a multifunction printer scanning to email, an old line-of-business application, a service account configured years ago against a legacy endpoint. For each, you decide whether to remediate the client to modern authentication (the right answer) or to carve out a narrow, time-limited exclusion while you do (the pragmatic answer). What you do not do is enforce the block cold and discover the printers stopped working from the help desk. Once report-only shows the remaining legacy sign-ins are only the ones you have accounted for, you promote the policy to enabled and the side door closes.

## Common Misconfigurations and Their Symptoms

Every misconfiguration in this section produces a recognizable symptom, and learning the mapping from symptom to cause is what lets you diagnose a Conditional Access problem in minutes rather than guessing. Each pattern below ties back to a step in the checklist that, done differently, would have prevented it.

### A policy enforced without report-only that blocks legitimate sign-ins

The symptom is a sudden wave of sign-in failures immediately after a policy was enabled, affecting users who should have been fine. The sign-in logs show the new rule applying and its grant control failing for accounts you did not intend to disrupt. The cause is enforcement before observation: the policy matched a population you did not fully understand, and because it was enforced rather than report-only, the mismatch became failed sign-ins instead of log entries. The fix is to disable the policy, return it to report-only, read the data it should have generated in the first place, refine the scope, and only re-enforce once the affected population matches the intended one. The prevention is step four of the checklist, every time.

### No break-glass account, so administrators are locked out

The symptom is the worst one: no administrator can sign in to fix a policy, because the policy that needs fixing applies to all of them. The cause is an empty exclusion list combined with a grant control that the locked-out administrators cannot currently satisfy, often an MFA requirement against accounts with no registered method. If a break-glass account exists, the fix is immediate: sign in with it, disable or scope down the offending rule, and restore access. If no break-glass account exists, recovery is slower and may require a support path, which is precisely the situation steps one and three of the checklist exist to make impossible. The lesson reinforces itself: the exclusion has to be in place before enforcement, not created in response to the lockout it would have prevented.

### Legacy authentication still bypassing MFA after an MFA policy is live

The symptom is subtle and dangerous: MFA appears to be required, the policy shows as enabled, and yet sign-in logs show successful password-only authentications for some accounts. The cause is that the MFA rule applies only to modern clients, or applies to all clients but cannot enforce MFA on legacy ones, while no separate policy blocks the legacy protocols. The attacker, or the unmonitored old client, simply uses the legacy endpoint. The fix is the dedicated legacy-block policy described above. The diagnostic that confirms it is filtering the sign-in logs by client app and looking for legacy entries that succeeded with no MFA; their presence is the proof that the side door is still open.

### A location or device condition scoped too broadly

The symptom is users being prompted far more often than intended, or being blocked from a network or device that should have been fine. The cause is usually a trusted location that is too narrow (so legitimate office traffic falls outside it) or a device condition that excludes a managed device platform you forgot to account for. The report-only data exposes this clearly, which is why the condition should have been narrowed one step at a time under observation. The fix is to widen the trusted location to include the missing egress IPs, or to adjust the device condition to match the real device fleet, then re-confirm in report-only before re-enforcing.

### An application that needs to be excluded from a policy

The symptom is one specific application breaking while everything else works, typically a service or integration that authenticates in a way the rule's grant control cannot satisfy. The cause is a policy scoped to all applications that catches an app with a legitimate reason to be outside it, such as a service principal that signs in non-interactively and cannot perform MFA. The fix is to add that application to the rule's application exclusions, or better, to move such service identities to workload identity Conditional Access policies designed for non-interactive sign-ins, rather than weakening the interactive policy. The narrower the exclusion, the better; excluding one application is a scalpel, excluding a whole category is a hole.

### Report-only revealing unexpected impact you would otherwise have enforced

This one is not a failure but a success, and it belongs here because it is what the procedure is for. The symptom is the report-only data showing it would have affected accounts or applications you did not anticipate: a batch job, a monthly process, a class of devices. There is no incident, because nothing was enforced. The cause is simply that real traffic is more varied than any mental model of it. The action is to refine the policy until its projected impact matches your intent, then enforce. Every time report-only surfaces a surprise, it has paid for itself, because that surprise would otherwise have been an outage.

## Making the Configuration Repeatable as Code

A Conditional Access policy created by clicking through the portal is correct but fragile: it exists only in the tenant, its history is whatever the audit log happens to retain, and reproducing it in a second tenant means clicking through the same screens and hoping you matched every setting. Treating policies as code solves all three problems at once. The policy lives in a repository where its definition is reviewable, its changes are diffed and approved like any other change, and its deployment is a script rather than a memory of which checkboxes to tick.

Because the entire policy is a JSON object accessible through the Graph API, exporting and reimporting policies is straightforward, and a small amount of tooling turns the export into a managed baseline. The pattern is to export the current policies as the source of truth, store them in version control, make changes by editing the stored definitions and applying them through a pipeline, and periodically compare the live tenant against the stored definitions to detect drift.

```powershell
# Export every Conditional Access policy to individual JSON files
$exportRoot = "./conditional-access-policies"
New-Item -ItemType Directory -Path $exportRoot -Force | Out-Null

$allPolicies = Get-MgIdentityConditionalAccessPolicy -All
foreach ($p in $allPolicies) {
    $safeName = $p.DisplayName -replace '[^\w\-]', '_'
    $p | ConvertTo-Json -Depth 10 |
        Out-File -FilePath (Join-Path $exportRoot "$safeName.json") -Encoding utf8
}

Write-Host "Exported $($allPolicies.Count) policies to $exportRoot"
```

Each exported file is a complete, reviewable definition of one policy, and committing the directory to a repository gives you the history that the portal does not. From there, a change to a policy is a change to a file, reviewed in a pull request where a second engineer can see exactly which condition or grant control moved before it reaches the tenant. The same export, run on a schedule and compared against the committed definitions, becomes a drift detector: if someone edits a policy in the portal out of band, the comparison surfaces the difference and you can decide whether to fold it into the baseline or revert it.

Applying a stored definition back into a tenant is the inverse operation, and the report-only discipline applies here exactly as it does in the portal. A pipeline that deploys a new or changed policy should create or update it in the report-only state, leave time for the report-only data to be reviewed, and only then run a second step that promotes it to enabled. This keeps the safety rail intact even when the change is automated; automation should never be the thing that removes the testing step, because an enforced policy deployed straight from a pipeline with no report-only window is the same cold enforcement the manual procedure forbids, only faster.

The same approach extends to declarative tooling. Whether you express policies through a Terraform provider, a Bicep deployment that calls the Graph API, or a purpose-built community module, the principle is unchanged: the policy definition is text, it is reviewed before it is applied, it is applied in report-only first, and the break-glass exclusion group is referenced by every policy so the safety rail is part of the code rather than a manual afterthought. The choice of tool matters less than the discipline the tool enforces.

You can practice this entire export-review-apply loop, including the report-only promotion gate, in a sandbox tenant without risking a production environment. The hands-on Azure labs and command library on VaultBook include an interactive Entra environment where you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), build a Conditional Access policy in report-only, generate sign-in traffic against it, read the report-only results, and verify the break-glass path, all against a tenant you cannot break for anyone else. Working the procedure end to end in a sandbox is the fastest way to internalize the order of operations before you apply it to a tenant that matters, and the tested command and template library there means the Graph and PowerShell snippets you need are available to adapt rather than write from scratch.

## A Worked End-to-End Configuration

To tie the pieces together, walk through the configuration of a baseline MFA policy for a real tenant from nothing to enforced, following the checklist in order and noting the decision at each step.

The starting state is a tenant with MFA registered for most users but no Conditional Access policy requiring it, legacy authentication still enabled, and a single Global Administrator account that the engineer is currently signed in as. The goal is a baseline that requires MFA for all users on all apps from outside the office, blocks legacy authentication, and never risks locking out administration.

The first action is the break-glass account, because nothing else is safe until it exists. The engineer creates a cloud-only account, assigns it the Global Administrator role, sets a long random password recorded in the organization's sealed credential store, registers an authentication method for it, and places it in a new security group named for break-glass exclusions. They open a private browser session, sign in as the break-glass account to confirm it works, and leave that path documented. The seatbelt is fastened.

The second action is the inventory. The engineer opens the sign-in logs, filters by client app, and finds that legacy authentication is still used by two accounts: a scanner that emails documents and an old reporting script. They note both for remediation. They also see that the bulk of sign-ins come from a known office IP range and from remote users on managed laptops. This shapes the conditions to come.

The third action is the MFA rule itself, created in report-only against a pilot group of willing testers, with the break-glass group excluded and a trusted named location defined for the office IPs. The condition is all locations excluding the trusted one, so office sign-ins are not prompted. The grant control is require MFA, with the operator set so a compliant device also satisfies it, sparing managed laptops the prompt. The engineer leaves it in report-only and watches for three days.

The report-only data over those days shows the policy behaving as intended for the pilot users, with one surprise: a pilot user's mobile mail client appears as a legacy sign-in that the MFA rule cannot challenge. This is exactly the kind of finding report-only exists to surface, and it confirms the need for the separate legacy-block policy rather than being a problem with the MFA rule. The engineer widens the MFA rule's scope from the pilot group to all users, still in report-only, and watches for another several days across a full week to catch the weekly batch jobs. The data stays clean for interactive sign-ins, so the engineer promotes the MFA rule to enabled and verifies: a test user from outside the office is challenged and succeeds, the same user from the office is not challenged, and the break-glass account shows every policy as not applied.

The fourth action is the legacy-authentication block, created in report-only with the break-glass group excluded, scoped to legacy client types with a grant control of block. The report-only data confirms only the two known accounts (the scanner and the reporting script) plus the one mobile client would be affected. The engineer remediates the scanner to modern authentication, updates the reporting script to a modern flow, and works with the pilot user to reconfigure their mobile client. With the known legacy sign-ins remediated, the report-only data shows the policy would now block essentially nothing legitimate, so the engineer promotes it to enabled. A final verification confirms a legacy sign-in attempt is now refused while modern authentication continues to work, and the break-glass account still passes through everything.

The end state is a tenant with MFA enforced where it matters, legacy authentication closed, every change tested in report-only before it touched a real user, and a break-glass account that proved at every step it could always get back in. No incident occurred, because the order of operations made one nearly impossible. The whole sequence took a couple of weeks of mostly waiting, and the waiting was the point.

## Operating Conditional Access Over Time

A tenant's Conditional Access posture is not a project that finishes; it is a system that is maintained, and a few operating habits keep it healthy as policies accumulate and the organization changes. The first habit is the standing break-glass exclusion group referenced by every policy, so a new policy created six months from now inherits the safety rail automatically rather than depending on someone remembering to add it. The second is the alert on break-glass sign-ins, so the rare legitimate use of an emergency account is noticed and the rarer illegitimate use is caught immediately.

The third habit is periodic review of the report-only and enabled policies together, because a policy left in report-only indefinitely is a policy you decided to test and then forgot to finish, and a stale report-only policy provides no protection while giving the false comfort that the rule exists. Reviewing the policy list and asking, for each report-only policy, whether it should be promoted or removed keeps the set honest. The fourth is reading the Conditional Access Insights workbook periodically even when nothing has changed, because the traffic changes even when the policies do not: a new application, a new office, a new class of device can shift what a stable policy actually matches, and the workbook surfaces that drift before it becomes a complaint.

For an organization investing in this control deeply, the deeper design patterns become worth studying as a body of practice rather than one policy at a time. The way policies compose, the standard set of baseline policies most organizations converge on, the handling of guest and external identities, and the integration with risk-based signals all reward a more systematic treatment. The [design library of Conditional Access patterns](/2024/04/08/entra-conditional-access-patterns/) and the [deeper dive into how Conditional Access evaluates and combines policies](/2024/01/22/conditional-access-deep-dive/) are the natural next reading once the configuration mechanics in this article are second nature, because they move the question from how to configure one policy safely to how to design a coherent set of them.

The relationship to the sign-in flow is also worth revisiting once the policies are in place, because understanding the authentication sequence Conditional Access decorates makes the logs far easier to read. Knowing where in the token-issuance flow each condition is evaluated, and what the sign-in log is actually recording at each stage, turns log reading from pattern matching into genuine diagnosis. The identity model underneath all of it, the tenants and identities and app registrations that the policies govern, remains the foundation; a policy is only ever as clear as your understanding of the identities it applies to.

## Understanding the Policy Model in Depth

The reason Conditional Access feels simple in the portal and confusing in practice is that the visible form (a few dropdowns) hides an evaluation model that has real structure. Understanding that structure is what lets you predict what a policy will do before you create it, and predicting behavior is the whole game when a mistake can lock people out.

Every policy is a three-part statement: assignments, conditions, and access controls. The assignments answer who and what: which users and groups, which client applications or user actions. The conditions answer when and where and how: under what circumstances of risk, location, device, and client does this rule come into play. The access controls answer what happens: grant with requirements, or block, plus any session controls that shape the resulting session. A sign-in is evaluated against every policy in the tenant, and a policy applies to that sign-in only if the assignments match and all the conditions are satisfied. When a policy applies, its grant controls run.

The combination logic across policies is where the surprises live. Within a single policy, conditions combine with AND, so every condition must be true for the policy to apply, and multiple grant controls combine with the operator you chose, AND or OR. Across policies, the model is more demanding: when several policies apply to one sign-in, the user must satisfy the grant controls of all of them. This is the rule that produces unexpected lockouts. You can write two perfectly reasonable policies that each make sense in isolation, and discover that for some user who matches both, the combined requirement is impossible to satisfy. A policy requiring a compliant device and another requiring MFA might each be fine, but for a user on a non-compliant device who cannot reach an MFA method, the intersection is a wall. The defense against this is the same as the defense against every Conditional Access mistake: report-only mode shows you the combined effect across policies, not just the one you are editing, so the impossible intersection appears as a projected failure in the log rather than as a real one.

### How do multiple Conditional Access policies combine for one sign-in?

When several policies apply to a single sign-in, the user must satisfy the grant controls of every applying policy, because policies combine restrictively rather than permissively. Two individually reasonable policies can together create a requirement no one can meet, which is why report-only mode shows the combined projected result across all policies, not one in isolation.

The practical consequence is that you cannot reason about a policy purely on its own. Before enforcing any new policy, the question is not only "does this rule do the right thing" but "what is the combined effect of this rule and every other policy on each population of users." Report-only answers that question empirically, which is why it is indispensable precisely as the number of policies grows. A single policy in a tenant is easy to reason about; the tenth policy interacts with nine others, and the only reliable way to know the combined behavior is to observe it.

## Session Controls and What They Govern

Grant controls decide whether a sign-in is allowed and under what requirement. Session controls decide what the resulting session looks like, and while they are a refinement rather than a first-day concern, they are part of a complete policy and worth understanding so you can make a deliberate choice rather than accepting a default.

Sign-in frequency controls how often a user must reauthenticate within a session. By default, once a user has signed in and satisfied any required controls, the resulting tokens are valid for an extended period and the user is not prompted again for some time. For a sensitive application, that default may be longer than you want, and a sign-in frequency control can require reauthentication on a shorter cadence, so a stolen session token has a smaller window of usefulness. The trade-off is friction: a short sign-in frequency on a frequently used application prompts users often, which both annoys them and trains them toward reflexive approval, so the control is best reserved for genuinely sensitive applications rather than applied broadly.

Persistent browser session controls whether a user's session survives closing and reopening the browser. Allowing a persistent session is convenient on a personal managed device and inappropriate on a shared or public one, so this control is often paired with a device or location condition: persistent sessions allowed on compliant devices, never on unmanaged ones. Application-enforced restrictions and the use of the cloud app security session control extend this further for specific applications that support it, allowing limited-access experiences (view but not download, for example) for sessions that meet a condition but not a stricter one.

The principle uniting the session controls is that they let a policy say not just yes or no but yes, with these constraints on the resulting session. Most baseline configurations leave them at tenant defaults at first and introduce them deliberately for the handful of applications whose sensitivity justifies the added friction. The mistake to avoid is applying a tight session control broadly out of an abundance of caution, because the resulting prompt fatigue undermines the very security the control was meant to add.

## Security Defaults, Per-User MFA, and Where Conditional Access Fits

Conditional Access is one of three ways a tenant can require MFA, and knowing how the three relate prevents the confusion of having more than one of them active at once. Security defaults are a tenant-wide on-off switch that enforces a fixed, Microsoft-managed baseline including MFA for administrators and a push toward MFA for all users; they are free, they are sensible for a small organization with no appetite for custom policy, and they are deliberately not configurable. Per-user MFA is the older, account-by-account enforcement that predates Conditional Access and is now considered legacy practice. Conditional Access is the flexible, condition-aware system this article describes, available with the licensing tier that includes it.

These do not stack cleanly, which is the source of much confusion. Security defaults and Conditional Access are mutually exclusive: you cannot have security defaults enabled and also use Conditional Access policies, because the former is an all-or-nothing baseline and the latter is the customizable replacement for it. The migration path for a growing organization is therefore to disable security defaults at the moment you adopt Conditional Access, having first built Conditional Access policies that at least match the protection security defaults provided, so you do not open a gap during the switch. Doing this in the wrong order, disabling security defaults before the Conditional Access policies are enforced, leaves a window where neither is fully protecting the tenant.

Per-user MFA settings, where they linger from an older configuration, can interact confusingly with Conditional Access, because a user enabled for per-user MFA is prompted regardless of what Conditional Access decides. The clean end state is Conditional Access as the single system that decides MFA, with per-user MFA settings reset to disabled so they do not produce prompts that no Conditional Access policy explains. Untangling an inherited tenant that has per-user MFA, possibly security defaults history, and new Conditional Access policies all in play is a common real-world task, and the sign-in log is again the tool: when a prompt appears that no enabled Conditional Access policy accounts for, a lingering per-user MFA setting is the usual explanation.

### Do I use security defaults or Conditional Access?

Use security defaults for a small organization wanting a free, fixed MFA baseline with no customization. Use Conditional Access when you need conditions such as location, device state, or risk, or per-application policies, which security defaults cannot express. The two are mutually exclusive, so adopting Conditional Access means disabling security defaults after equivalent policies are enforced.

The decision usually resolves itself with growth. A new or small tenant turns on security defaults and is well served by them. As requirements appear (an executive group that needs stricter controls, an application that needs an exception, a desire to stop prompting in-office users), security defaults run out of expressiveness, and that is the signal to move to Conditional Access. The move is not urgent for its own sake; it is driven by a concrete requirement security defaults cannot meet. Adopting Conditional Access before you have such a requirement is taking on the operational responsibility of custom policy with none of the benefit, so the honest answer for many small tenants is that security defaults remain the right choice until a specific need says otherwise.

## Closing Verdict

Conditional Access is the most consequential security control most administrators will configure, in both directions: configured well it raises the floor for an entire tenant, and configured carelessly it can lock that tenant out of itself. The difference between those outcomes is not technical sophistication. It is procedure. The report-only-and-break-glass rule captures the whole of it: test every policy in report-only against real traffic before enforcing it, and exclude a break-glass account from every policy so a mistake is always reversible. A policy that honors both is safe to enforce regardless of how ambitious its logic; a policy that honors neither is unsafe regardless of how careful its logic.

The checklist that opens this article is the operational form of that rule. Define assignments and conditions, set grant controls, exclude break-glass, run report-only, read the results across a full cycle of traffic, enforce, and block legacy authentication in a separate policy. Followed in order, it turns a tenant-wide security change from a gamble into a routine. The two steps people skip, report-only and the break-glass exclusion, are exactly the two that prevent the catastrophic failure, which is why they are not optional and why this article keeps returning to them. Build the habit of the standing exclusion group and the report-only window, and Conditional Access becomes a control you can wield confidently rather than one you approach with dread.

The deeper you go, the more the design questions matter relative to the mechanics, but the mechanics here are the foundation everything else stands on. A correctly scoped, report-only-tested, break-glass-protected policy is the unit from which a coherent security posture is built. Get that unit right, repeatedly and as code, and the larger architecture has somewhere solid to stand.

## Frequently Asked Questions

**How do I configure a Conditional Access policy from scratch?**

Begin by creating and verifying a break-glass account in an exclusion group. Then define the rule's assignments (the users, groups, and applications it covers) and its conditions (location, device, client app, or risk). Set the grant control, such as require MFA or block. Add the break-glass exclusion group to the rule's user exclusions. Create the policy in report-only state, let it evaluate real sign-ins for several days, read the results in the sign-in logs, and only then switch it to enabled. That sequence, break-glass first and report-only before enforcement, is the entire safety procedure.

**What is the difference between assignments and conditions in a policy?**

Assignments define the population the policy targets: which users and groups are included or excluded, and which cloud applications or user actions are in scope. Conditions narrow that population to particular circumstances: a specific location, device state, client application type, or risk level. The assignment decides who could be affected; the condition decides when they actually are. A policy applies to a sign-in only when the assignment matches and every condition is satisfied, since conditions combine with AND.

**How do I require MFA only for sign-ins from outside the office?**

Define a named location containing your office egress IP ranges and mark it as trusted. Then build a policy whose location condition includes all locations and excludes that trusted one, with a grant control of require MFA. The policy evaluates the MFA requirement everywhere except the trusted addresses, so office sign-ins proceed without a prompt while remote sign-ins are challenged. Combining the location condition with a compliant-device condition is often better long term, because a managed device travels with the user while an office network does not.

**What exactly does report-only mode do?**

Report-only mode makes a policy evaluate every matching sign-in and record what it would have done, without enforcing anything. A sign-in it would have challenged for MFA still proceeds unchallenged; a sign-in it would have blocked still succeeds. The projected result appears in the sign-in log's report-only tab and in the Conditional Access Insights workbook. This lets you see the rule's real impact on real traffic and refine its scope before any user is affected by enforcement.

**How long should a policy stay in report-only before I enforce it?**

Leave it in report-only long enough to cover a full cycle of your organization's sign-in patterns. A few days captures the daily rhythm, and a full week captures weekly batch jobs and people who work only certain days. If a monthly process matters, such as month-end finance activity, either wait for that cycle or specifically confirm how those accounts would be treated. The cost of waiting is low compared with the cost of enforcing into a pattern you never observed.

**Why must a break-glass account be excluded from every policy, not just one?**

Lockouts usually come from the combined effect of multiple policies rather than one in isolation. If you exclude the break-glass account from your new policy but an older device-compliance policy still applies to it, the account fails that older policy's control during an incident and is locked out when it is needed most. Maintaining one exclusion group and adding it to every policy's user exclusions, as a standing practice, guarantees no policy can ever catch the recovery account.

**How do I protect the break-glass account if it bypasses all my policies?**

Use a long, randomly generated password stored in a sealed, audited location, make it a cloud-only account so an on-premises outage cannot affect it, and configure an alert that fires on any sign-in, since a legitimate use is rare and noteworthy. Many organizations keep two such accounts so losing one credential does not eliminate the recovery path. The account is excluded from Conditional Access but protected by these other means, so the exclusion does not leave it unguarded.

**How do I block legacy authentication?**

Create a dedicated policy whose client app types condition selects the legacy clients, Exchange ActiveSync and the basic-authentication bucket, with a grant control of block. Run it in report-only first to discover which accounts still authenticate over legacy protocols, remediate or temporarily exclude them, then switch the policy to enabled. Keeping this in its own clearly named policy means a broken client points straight at the right rule, which a bundled policy would hide.

**Why does MFA still get bypassed even though my MFA policy is enabled?**

The usual cause is legacy authentication. Older protocols cannot present an MFA challenge, so a sign-in over a legacy endpoint with a valid password succeeds without a second factor, regardless of the MFA rule on modern clients. Filter the sign-in logs by client app and look for successful legacy sign-ins with no MFA; their presence confirms the gap. The fix is a separate policy that blocks legacy authentication outright, which closes the side door the MFA rule never covered.

**What signals can a Conditional Access policy use as conditions?**

The available conditions are user or sign-in risk (with the Identity Protection licensing tier), device platform, location, client app type, and device state such as compliant or hybrid-joined. Each condition narrows the set of sign-ins the policy matches, and because they combine with AND, a policy with several conditions applies only to sign-ins satisfying all of them. The deterministic conditions, location, device, and client app, are the place to start; risk-based conditions are valuable but best added once the foundation is stable.

**How do I verify that a policy is actually working after I enforce it?**

Sign in as a test account that matches the policy and confirm the expected control fires, such as an MFA prompt, then open that sign-in in the Entra ID sign-in logs and read its Conditional Access tab, which shows every policy that evaluated the sign-in and whether each succeeded, failed, or did not apply. Then sign in as the break-glass account and confirm every policy shows as not applied for it. Run that break-glass check after every enforcement to keep the exclusion honest.

**Can two reasonable policies together lock a user out?**

Yes. When several policies apply to one sign-in, the user must satisfy the grant controls of all of them, because policies combine restrictively. Two policies that each make sense alone, such as one requiring a compliant device and another requiring MFA, can together create a requirement a particular user cannot meet. Report-only mode shows the combined projected result across all policies for each population, which is the reliable way to catch an impossible intersection before it becomes a real lockout.

**Should I use security defaults or Conditional Access?**

Security defaults suit a small organization that wants a free, fixed MFA baseline with no customization. Conditional Access suits any tenant that needs conditions such as location, device state, or risk, or that needs per-application policies, none of which security defaults can express. The two are mutually exclusive, so adopting Conditional Access means disabling security defaults, which should happen only after equivalent Conditional Access policies are enforced so no protection gap opens during the switch.

**What grant control operator should I use when I have more than one control?**

The operator decides whether a user must satisfy all the grant controls (AND) or any one of them (OR). Require MFA OR a compliant device, with the OR operator, lets a user on a managed device skip the prompt, which is usually the intent. The same two controls with AND would require both, which is stricter and occasionally wanted but rarely the right default without a specific reason. The operator changes the rule's meaning entirely, so it deserves a conscious choice rather than a skim.

**How do I exclude a service account or application that cannot do MFA?**

For a non-interactive service identity that cannot perform an interactive MFA challenge, the cleaner answer is a workload identity Conditional Access policy designed for service principals, rather than weakening an interactive policy. Where a narrow carve-out is needed, exclude the specific application from the rule's application assignment rather than excluding a whole category. The narrower the exclusion, the smaller the hole; excluding one application is precise, while excluding a broad class of apps undermines the policy.

**How do I manage Conditional Access policies as code?**

Export every policy through the Graph API to individual JSON files, commit them to version control, and make changes by editing the stored definitions and applying them through a reviewed pipeline. Run the export on a schedule and compare it against the committed baseline to detect drift from out-of-band portal edits. Crucially, a pipeline should create or update policies in report-only state and promote them to enabled in a separate step, so automation never removes the testing window the manual procedure depends on.

**What is the right order of operations for a brand-new tenant baseline?**

Create and verify the break-glass account and its exclusion group first. Inventory the sign-in traffic to understand current patterns and any legacy authentication in use. Build the MFA rule in report-only against a pilot group, widen it to all users still in report-only, then enforce it after the data is clean across a full traffic cycle. Finally, add the legacy-authentication block in its own policy, report-only first, remediate the accounts it surfaces, and enforce. Break-glass first, report-only before every enforcement, legacy block last and separate.

**What happens to existing sessions when I enforce a new policy?**

Conditional Access evaluates at sign-in and at token refresh, so a newly enforced rule does not instantly terminate sessions that were already established; it takes effect as those sessions reauthenticate or refresh their tokens. A sign-in frequency session control shortens that window by forcing reauthentication on a cadence. This is why verification uses a fresh sign-in rather than an existing session: an old session may still reflect the pre-enforcement state until it refreshes, which can otherwise look like the policy not working.

## Device-Based Access as the Durable Foundation

Location conditions are the easiest place to start because office IP ranges are concrete and familiar, but they age poorly as a security boundary, and the more durable foundation is device state. A network address tells you where a request appears to originate, which an attacker can spoof through a VPN or a compromised machine inside the perimeter, and which a legitimate remote worker never satisfies at all. A device condition asks a harder question: is this sign-in coming from a device the organization manages and trusts. That question travels with the user, holds up when the user works from home or a hotel, and resists the spoofing that undermines location.

A device becomes trusted in one of two ways relevant to Conditional Access. A hybrid Entra-joined device is a Windows machine joined to both an on-premises directory and Entra ID, common in organizations with existing Active Directory infrastructure. A compliant device is one that an enrollment and compliance system, typically Microsoft Intune, has evaluated against a compliance policy and marked as meeting it: encrypted, patched, not jailbroken, screen-locked, and whatever else the policy requires. A Conditional Access grant control of require a compliant device or a hybrid-joined device then admits only sign-ins from devices in one of those trusted states.

The configuration shift this enables is significant. Instead of requiring MFA from outside a trusted network, you can require either a compliant device or MFA, with the OR operator, so a user on a managed laptop is admitted without interruption while a user on any other device is challenged for a second factor. This removes prompts for the population most likely to be legitimate, the managed-device users, without removing protection from the population most likely to carry risk, the unmanaged-device users. It is the configuration that reconciles strong security with low friction, and it is why device state is worth investing in even though it requires the enrollment infrastructure that location does not.

### Is requiring a compliant device better than requiring MFA?

They serve different purposes and work best together. A compliant-device requirement verifies the endpoint's health and management state, while MFA verifies the user's identity with a second factor. A policy of require a compliant device OR MFA admits managed devices without a prompt and challenges everything else, combining low friction for trusted endpoints with strong verification for the rest, which neither control achieves alone.

The trade-off device-based access carries is the dependency on the enrollment and compliance pipeline working correctly. A device that should be compliant but is reporting a stale or failed compliance state will be challenged or blocked exactly as an untrusted device would be, and the user experiences that as a sudden inability to work from a machine that was fine yesterday. Diagnosing these means reading the device's compliance status alongside the sign-in log, because the Conditional Access tab will show the policy failing on the device control while the device's own compliance record explains why. Building device conditions therefore means building the operational habit of monitoring compliance health, since a compliance pipeline problem becomes an access problem the moment a policy depends on it.

There is also a bootstrapping concern worth planning for. A brand-new device that has not yet enrolled or reported compliance cannot satisfy a compliant-device control, which can create a chicken-and-egg situation where a user cannot complete enrollment because a policy blocks the sign-in enrollment needs. The standard resolution is to scope the device-requiring rule to exclude the enrollment flow and the specific applications involved in onboarding, or to admit MFA as the alternative control so a new device can get through with a second factor while it becomes compliant. Planning the onboarding path is part of designing a device-based policy, not an afterthought, because the policy that secures steady-state access can otherwise block the very process that produces trusted devices.

## Conditional Access for Guests and External Identities

Most discussions of Conditional Access assume the users are the organization's own employees, but a growing share of access in many tenants comes from guests and external identities: partners invited into the directory, contractors, and users from other organizations collaborating through external identity features. These identities live in your tenant as guest objects, and Conditional Access policies apply to them, which is both an opportunity and a trap.

The opportunity is that you can hold external users to standards appropriate to their access without managing their devices or credentials. A common pattern is a rule that requires MFA for all guest users on all applications, unconditionally, because you have no visibility into the security posture of an external user's own environment and a second factor is the minimum reasonable assurance. Because guests authenticate against their home tenant or an external method, the MFA challenge is satisfied through their own credentials, and you gain assurance without taking on management responsibility you could not fulfill anyway.

The trap is twofold. First, a policy written with the organization's own users in mind, scoped to all users, silently includes guests, and a condition that makes sense for employees may be nonsensical or blocking for a guest. A device-compliance requirement, for instance, cannot be satisfied by a guest whose device you do not manage, so a policy requiring a compliant device and scoped to all users will block every guest unless guests are deliberately excluded or handled by a separate policy. Second, the way external users satisfy MFA depends on trust settings between your tenant and theirs, and a misconfiguration there can mean a guest's MFA from their home tenant is not accepted, forcing them to register a method in your tenant or failing the sign-in entirely.

### How do I apply Conditional Access to guest users?

Scope a policy to the guest and external user types in its user assignment, then set a grant control appropriate to external access, most commonly require MFA. Keep employee-oriented conditions like device compliance out of guest policies, since you do not manage guests' devices. Configure cross-tenant access settings so MFA satisfied in a guest's home tenant is accepted, sparing guests a second registration in your tenant.

The cleaner design treats guests as a distinct population with their own policies rather than folding them into the employee policies. A guest-specific rule requiring MFA, with no device condition, applied to the external user types, handles the realistic case directly. The employee policies, meanwhile, can then exclude the guest types or simply not match them, so an employee-oriented device requirement never accidentally blocks a partner. Keeping the two populations in separate policies makes each one easier to reason about and prevents the most common guest-access surprises, which nearly always come from an employee policy reaching a guest it was never designed for.

## Reading the Sign-In Logs Like a Diagnostician

The sign-in log is the instrument panel for Conditional Access, and the difference between guessing at a policy problem and diagnosing it is fluency with what the log actually records. Every interactive sign-in produces an entry, and that entry carries the full Conditional Access evaluation as a structured record you can read deterministically rather than interpret.

The first field to read on any problematic sign-in is the status: success or failure, and on failure, the failure reason. A Conditional Access failure has a characteristic reason indicating the sign-in was blocked or that a required control was not satisfied, which distinguishes it immediately from a password failure or a disabled-account failure. Once you know the failure is Conditional Access, the Conditional Access tab on that sign-in is where the answer lives. It enumerates every policy that was in scope for the sign-in and gives each a result: success means the policy applied and its controls were satisfied, failure means the policy applied and a control was not met, and not applied means the sign-in did not match the rule's assignments or conditions, with the reason it was excluded.

That not-applied reason is more useful than it first appears, because it is how you confirm a policy is correctly scoped. If you intended a policy to apply to a sign-in and the log shows it as not applied, the reason field tells you which assignment or condition excluded it, and that is usually the bug: a user not in the targeted group, a location that matched a trusted exclusion, a client app type outside the condition. Conversely, if a policy shows as applied to a sign-in you intended to exclude, the assignment is broader than you thought. Reading the not-applied reasons across a few sign-ins calibrates your mental model of what each policy actually matches against what you intended.

### Why does the sign-in log show a policy as not applied?

A policy shows not applied when the sign-in did not match its assignments or conditions: the user was not in the included group or was in an excluded one, the application was out of scope, the location matched a trusted exclusion, or the client app type or device state did not meet a condition. The log gives the specific reason, which tells you exactly why the policy did not fire for that sign-in.

The other field that rewards attention is the client app used for the sign-in, because it is how you confirm whether legacy authentication is in play. A sign-in over a legacy protocol records a legacy client app type, and filtering the sign-in logs to show only legacy client app types is the single most useful query for understanding your legacy authentication exposure: it shows you exactly which accounts and applications still use the protocols you want to block, which is the inventory you need before enforcing a legacy block. Running that filter periodically even after you have enforced a block confirms the block is holding and surfaces any new legacy client that appears, such as a newly provisioned device misconfigured against an old endpoint.

For sign-ins that involve risk-based conditions, the log also records the risk state that was evaluated, which is how you understand why a risk-based rule did or did not fire. A sign-in the policy challenged for MFA on medium risk will show the risk level that triggered it, and a sign-in that was not challenged will show why the risk did not reach the rule's threshold. This is the field that makes risk-based rules debuggable, turning an otherwise mysterious intermittent prompt into an explainable event tied to a recorded risk evaluation.

## Risk-Based Conditional Access as the Next Layer

Once the deterministic rules are stable, risk-based Conditional Access is the layer that adds adaptive response, and it is worth understanding even if you adopt it later. Risk-based conditions depend on the Identity Protection capability in the higher Entra ID licensing tier, which continuously evaluates two kinds of risk: sign-in risk, the likelihood that a particular authentication request is illegitimate, and user risk, the accumulated likelihood that an account is compromised. Microsoft computes these from signals like impossible-travel patterns, sign-ins from anonymized networks, leaked-credential matches, and unfamiliar sign-in properties, and exposes them as conditions a policy can act on.

A risk-based rule reads as a graduated response. A common configuration requires MFA on a medium-or-higher sign-in risk, so a suspicious authentication must clear a second factor before proceeding, and requires a secure password change on a high user risk, so an account that appears compromised is forced to re-establish its credential. These responses are proportionate: a low-risk sign-in proceeds untouched, a medium-risk one is challenged, and a high-risk one is challenged harder or blocked. The result is a system that applies friction in proportion to suspicion rather than uniformly, which is both more secure where it matters and less annoying where it does not.

### When should I add risk-based Conditional Access policies?

Add risk-based rules after the deterministic rules, location, device, client app, and a baseline MFA requirement, are stable and enforced, and once you have the Identity Protection licensing tier. Risk-based policies produce intermittent, context-dependent prompts that are harder to reason about, so they are best layered onto a solid foundation rather than used as a starting point, where their variability would erode trust in the whole system.

The reason risk-based rules come later is precisely their variability. A deterministic policy behaves the same way every time the same conditions hold, which makes it easy to test, explain, and trust. A risk-based rule behaves differently as Microsoft's risk scoring shifts, which means a user may be challenged today and not tomorrow for reasons that are correct but not obvious to them. Introduced onto a stable foundation, this adaptivity is a feature: the unusual sign-in gets the extra scrutiny it deserves. Introduced too early, before users trust the system, the same unpredictability reads as flakiness and undermines confidence in every prompt. The sequencing is therefore not a licensing accident but a deliberate ordering: earn trust with deterministic rules, then add the adaptive layer that the trust can absorb.

Tuning risk-based rules is its own discipline, because the cost of a false positive (challenging a legitimate user) and a false negative (missing a real threat) are both real and pull in opposite directions. The report-only discipline applies with extra force here: run a risk-based rule in report-only long enough to see how often it would fire and against whom, because the projected challenge rate tells you whether the threshold is calibrated for your population before any user feels it. A risk policy that would challenge a large fraction of normal sign-ins is mis-tuned and would train users toward prompt fatigue, while one that almost never fires may have its threshold set too high to catch anything. Report-only turns that calibration into a measured decision rather than a guess, exactly as it does for the deterministic rules, and it remains the single habit that makes every kind of Conditional Access change safe.

## Organizing and Naming Policies for a Maintainable Set

A tenant rarely has one Conditional Access policy; it has a set that grows over time, and a set without a naming and organizing convention becomes unmaintainable surprisingly fast. When a policy is named simply New Policy or MFA, a future engineer reading the list cannot tell at a glance what each one targets or why it exists, and the combined behavior of a dozen vaguely named policies is nearly impossible to reason about during an incident. A naming convention is therefore not cosmetic; it is part of making the set diagnosable.

A convention that holds up assigns each policy a stable identifier and encodes the persona, the target, and the control in the name, so a name like CA001 - All users - All apps - Require MFA tells you everything you need without opening the policy. Grouping the identifiers into ranges by persona keeps the list scannable: one range for policies targeting all users, another for administrators, another for guests, another for workload identities, another for the legacy and baseline blocks. When the names follow a pattern, the policy list reads like a table of contents for the tenant's access posture, and an unfamiliar engineer can orient in seconds rather than reverse-engineering intent from scattered settings.

The organizing principle that pairs with naming is one concern per policy. It is tempting to build a single comprehensive policy that requires MFA, blocks legacy auth, and enforces device compliance all at once, because it feels efficient, but that efficiency is a debugging liability. When a sign-in fails against a policy that does five things, you cannot tell which of the five caused the failure without picking the policy apart. When each policy does one thing and is named for it, a failure points directly at the responsible rule. The legacy-authentication block lives in its own policy for exactly this reason, and the same logic extends across the set: a rule that requires MFA is separate from a policy that requires a compliant device, which is separate from a policy that handles guests, so each can be tested, enforced, diagnosed, and disabled independently.

This separation also makes report-only more precise. A single-concern rule in report-only generates data about exactly that concern, so you read its projected impact without untangling it from four other things the same policy would do. A multi-concern rule in report-only mixes the projections together and obscures the very signal report-only exists to provide. The discipline of one concern per policy is therefore not only about diagnosis after enforcement but about clarity during the testing that precedes it.

## The Emergency Recovery Procedure

Even with the break-glass discipline, knowing the recovery procedure cold is worth the few minutes it takes, because the moment you need it is the moment you least want to be improvising. The procedure assumes the break-glass account exists and is excluded from every policy, which is the entire reason the procedure is fast rather than fraught.

When a policy has locked out the normal administrators, the first move is to sign in with the break-glass account in a clean browser session, ideally a private window so no cached session interferes. Because the break-glass account is excluded from every policy, it authenticates without being subject to the rule that locked everyone else out, and you are now in the tenant with the privileges needed to fix the problem. The second move is to identify the offending rule, which the sign-in logs make straightforward: the locked-out users' failed sign-ins show which policy applied and which control failed, naming the culprit directly. The third move is to neutralize that policy, either by disabling it entirely if the situation is urgent or by returning it to report-only, which immediately stops it enforcing while preserving its definition for repair.

With enforcement stopped, the affected users can sign in again, and you have moved from incident to repair. The repair is to understand why the policy locked people out, which is nearly always one of the patterns from the misconfigurations section: an empty exclusion, a grant control the population could not satisfy, an overly broad condition. You fix the underlying issue, return the policy to report-only, confirm from the report-only data that the projected impact now matches your intent, and only then re-enforce. The temptation during an incident is to re-enable the policy quickly once it seems fixed, but skipping the report-only confirmation is how a second lockout follows the first. The same rule that should have prevented the incident also governs the recovery: test before you enforce, even, and especially, when you are in a hurry.

The procedure's speed depends entirely on preparation done in calm conditions. The break-glass account has to exist before the incident, its credentials have to be retrievable, and the people who might need it have to know where they are and how to use them. A break-glass account documented in a place no one can reach during the incident, or whose credentials no one can locate, provides no recovery at all. The few minutes spent verifying the recovery path while nothing is wrong is what makes the recovery a routine rather than a crisis when something is. That preparation, more than any single policy setting, is what separates a tenant that treats Conditional Access as a controlled, reversible system from one that treats it as a gamble taken one enable button at a time.
