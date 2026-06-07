---
layout: post
title: "Set Up Azure Policy for Governance"
page_title: "Azure Policy Setup for Governance: Effects, Initiatives, Scopes, Exemptions, and Remediation Explained for Engineers"
date: 2023-07-24
categories: ["Technology"]
tags: ["Azure", "Azure Policy", "Governance", "Security", "DevOps", "Cloud Computing"]
excerpt: "Set up Azure Policy for governance by choosing the right effect, grouping rules into initiatives, assigning at the correct scope, and remediating drift."
image: "/assets/images/blog/blog-21.webp"
reading_time: 62
author: "abigail-cooper"
last_updated: 2023-07-24
lang: en
---
Most teams that say they have governance in place have a folder of policy assignments that audit and a compliance dashboard full of red. Nothing is prevented, nothing is fixed, and the dashboard is a record of drift rather than a control on it. The reason is almost never the rule that was written. It is the effect that rule carries. Azure Policy enforces standards only as strongly as the effect each definition declares, and choosing that effect is the real governance decision, not the resource type or the condition you match on.

![Setting up Azure Policy for governance with effects, initiatives, scopes, and remediation - Insight Crunch](/assets/images/blog/blog-21.webp)

This is the gap this guide closes. You can stand up an assignment in five minutes from the portal, and the documentation will happily walk you through it. What the documentation rarely connects is the chain that turns a written rule into an enforced one: an effect that prevents or remediates rather than merely observes, an initiative that groups related controls so they assign and report as a unit, a scope that lands the control where it belongs and inherits no further than intended, an exemption that records the one justified exception without weakening everything else, and a remediation task that drags existing noncompliant assets into line instead of waiting for someone to recreate them. Miss any link and you get the folder of red dashboards. Get the chain right and standards are enforced rather than documented, which is the whole point.

The claim this article defends is narrow and useful. An Azure Policy enforces exactly as strongly as its effect. An audit effect documents drift and stops nothing. A deny effect blocks the noncompliant create or update at the control plane before the item ever exists. A deployIfNotExists effect provisions or corrects a related object after the fact, and a modify effect rewrites properties during the request. Append adds what was missing. Once you internalize that the effect is the lever, every other decision in setting up governance falls into place around it, and the dashboard starts to mean something.

## What correct policy configuration buys, and what breaks when it is wrong

The promise of governance as code is that a standard lives in one place, applies everywhere it should, and corrects itself when reality drifts. Azure Policy is the engine that delivers on that promise inside Azure, evaluating workloads against rules at the control plane and at scheduled intervals, and acting on the result according to the effect you chose. When the configuration is right, a developer who tries to create a public storage account in a regulated subscription is stopped at deployment time with a clear message, an environment that was provisioned before the rule existed gets a remediation task that adds the missing diagnostic setting, and the compliance view tells leadership the truth about where the estate stands.

When the configuration is wrong, the failure is quiet, which is what makes it dangerous. An audit-only assignment generates compliance data and nothing else, so a subscription can sit at thirty percent compliant for a year while everyone assumes the red squares are someone else's problem. A deny policy assigned at too broad a scope blocks a legitimate deployment that a single team needed, and because the block surfaces as a generic authorization-style failure deep in a pipeline log, the team burns an afternoon before anyone traces it to a policy. A deployIfNotExists rule assigned without the managed identity it needs reports compliant on paper and remediates nothing in practice, because it never had the permission to deploy the correction. Each of these is a configuration mistake, not a product limitation, and each maps to a specific step in the setup that was skipped or done in the wrong order.

The cost of getting it wrong compounds. Governance is the layer auditors, security teams, and platform owners lean on, so a policy that looks enforced but is not creates a false sense of safety that is worse than no policy at all. A real deny on asset location, an enforced requirement for encryption, or an automatic deployment of a logging configuration each removes an entire class of manual review. The difference between that outcome and a wall of red is the handful of configuration choices this guide walks through in order: the effect, the grouping, the scope, the exemption model, the remediation identity, and the verification that proves the control actually does what you believe it does.

### What does Azure Policy actually enforce, and how is that different from RBAC?

Azure Policy governs the shape and configuration of items, while role-based access control governs who may act on them. RBAC decides whether you are allowed to create a virtual machine; policy decides whether the virtual machine you create may use a public IP, must carry a cost-center tag, or has to sit in an approved region. They run at the same control plane but answer different questions.

The two work as a pair, and conflating them is a common source of confusion when standards do not behave as expected. A user with Contributor rights can create objects, yet a deny policy will still block a create that violates a rule, because authorization and compliance are separate gates a request passes through. Understanding where each gate sits is the difference between debugging a permission problem and debugging a governance problem. If you are untangling the authorization side of that pair, the model in our walkthrough of [how Azure RBAC and ABAC decide access](/2024/01/01/azure-rbac-vs-abac-explained/) covers the role-assignment plane that policy sits alongside, and the two articles are meant to be read together.

The practical takeaway is that policy is your tool for the configuration of workloads and RBAC is your tool for the actions of identities. Governance that relies only on RBAC ends up writing custom roles to prevent configurations, which is brittle and incomplete. Governance that relies only on policy without RBAC leaves the door open for anyone with rights to create whatever passes the rules. A real estate uses both, with policy carrying the configuration standards and RBAC carrying the least-privilege boundary around who can touch what.

## The prerequisites and the correct order of operations

The order in which you build a governance control matters, because each step depends on the one before it and skipping ahead produces the silent failures described above. The sequence that works is: confirm the management-group and subscription layout you will scope to, decide the effect each rule needs, author or select the policy definitions, group related definitions into an initiative, assign the initiative at the right scope, declare the exemptions you already know you need, provision the remediation identity if any effect requires one, run remediation against existing assets, and finally read compliance to confirm the control behaves as intended. Build in that order and every step has what it needs. Build out of order and you assign before you have decided the effect, or remediate before the identity exists, and the control limps.

The first prerequisite is structural. Azure Policy assigns to a management group, a subscription, or a resource group, and the assignment inherits downward to everything beneath it. If your management-group hierarchy is not yet in place, a policy assigned at a subscription will not reach a sibling subscription, and a policy meant for the whole organization has nowhere clean to live. Sorting the hierarchy first means an assignment at the top genuinely covers the estate, and a narrower assignment can override or supplement it lower down. This is why platform teams stand up the management-group tree before they write a single rule.

The second prerequisite is permission. To create and assign policy you need rights on the scope, typically the Resource Policy Contributor role or higher at the management group or subscription. To remediate with deployIfNotExists or modify, the assignment needs a managed identity that itself holds the roles required to make the change it deploys. That identity does not exist until the assignment is created with one, and it does not have its roles until you grant them, so remediation is the step most often half-configured. Planning the identity and its role grants before you assign saves the round trip of discovering, days later, that nothing has been corrected.

### Which scope should I assign a policy at?

Assign at the highest scope where the rule should apply without exception, then narrow only when a subset genuinely differs. A region-restriction or required-tag standard usually belongs at the management group so it covers every subscription. A rule that applies only to one workload belongs at that workload's resource group. Inheritance does the rest.

The reasoning behind that default is that inheritance flows down but not up, so a control placed too low leaves siblings ungoverned, while a control placed at the right height covers them automatically and stays consistent as new subscriptions appear under the same management group. Placing a rule too high is the opposite mistake and the one that generates support tickets: a deny meant for production lands on a sandbox subscription where developers legitimately need the blocked configuration, and now you are writing exemptions to undo an over-broad assignment instead of having scoped it correctly. The judgment is to find the smallest scope that contains everything the rule must cover and nothing it must not, and to lean toward the higher scope only when the rule is a genuine organization-wide standard.

A practical habit is to keep broad, durable standards (allowed locations, required tags, encryption baselines) at the management group, and to keep workload-specific or environment-specific rules at the subscription or resource group. That split keeps the organization-wide controls stable and the local controls flexible, and it makes the compliance view readable, because the scope of a noncompliant result tells you immediately which layer of the hierarchy the rule came from.

## The findable artifact: the InsightCrunch Policy setup checklist

Every governance control you build should clear the same six gates, in order, with the same gotcha checked at each. This is the InsightCrunch Policy setup checklist, and it is the spine of the rest of this article. Treat it as the thing you run down before you call a control done.

| Step | What you do | The gotcha to check |
| --- | --- | --- |
| 1. Pick the effect | Choose audit, deny, deployIfNotExists, modify, or append based on whether you need to observe, prevent, or correct | An audit effect enforces nothing; if you need prevention, only deny blocks the request, and only deployIfNotExists or modify corrects |
| 2. Group into an initiative | Bundle related definitions into a policy set so they assign and report as one unit | A single sprawling assignment of unrelated rules is hard to exempt and read; group by intent |
| 3. Assign at the right scope | Place the assignment at the management group, subscription, or resource group that the rule should cover | Inheritance flows down only; too high blocks legitimate work, too low leaves siblings ungoverned |
| 4. Add exemptions | Record any justified exception as an exemption on the specific scope and item | A broad scope plus many exemptions usually means the assignment was scoped wrong; exempt the exception, not the rule |
| 5. Remediate existing objects | Run a remediation task so deployIfNotExists and modify correct workloads that predate the assignment | These effects do not touch existing assets until a remediation task runs, and the task needs the managed identity and its roles |
| 6. Read compliance | Confirm the compliance view reflects what the effect actually did, not just that the assignment exists | An assignment showing compliant can still be doing nothing if the effect was audit or remediation never ran |

The checklist is also a diagnostic tool. When a control is not behaving, walk the six steps and the failure almost always sits at one of them: the effect was audit when you needed deny, the scope was wrong, the identity was missing, or remediation never ran. Naming the step that failed is faster than re-reading the whole assignment, and it is the habit this series returns to again and again, that a governance outcome traces back to one decisive setting rather than a vague misconfiguration.

## The settings the defaults get wrong: choosing the effect

The effect is the first and most consequential choice, and it is the one teams most often get wrong by reaching for audit when they need enforcement. An effect is a declared behavior in the policy definition that tells the engine what to do when a item matches the rule. The five effects you will use for governance are audit, deny, deployIfNotExists, modify, and append, and they fall into three jobs: observe, prevent, and correct. Picking the wrong job is how you end up with a compliant-looking dashboard and an ungoverned estate.

Audit is the observe effect. When a resource matches the rule, audit marks it noncompliant in the compliance view and does nothing else. The resource is created, updated, or left alone exactly as it would have been without the policy. Audit is the right choice when you are measuring drift before you decide to enforce, when you want a compliance signal without changing behavior, or when prevention is not technically possible for that property. Audit is the wrong choice, and the central mistake of this whole topic, when you believe assigning it has governed the environment. It has not. It has measured it. There is a sibling audit effect, auditIfNotExists, which checks for the absence of a related resource (a diagnostic setting that should exist, an extension that should be installed) and flags noncompliance when it is missing, but it still only observes.

Deny is the prevent effect, and it is the one that actually stops noncompliance. When a create or update request would produce a resource that matches the rule, deny rejects the request at the control plane before the resource exists. A developer trying to create a storage account with public network access enabled, in a scope where a deny policy forbids it, gets the request refused with a message naming the policy. Nothing was created and nothing has to be cleaned up. The critical fact to keep exact is that deny acts at create or update time only. It does not reach back and delete or alter a resource that already exists and violates the rule. Existing violations show as noncompliant under a deny policy but are not removed; deny is a gate on new and changed resources, not a cleanup crew.

DeployIfNotExists is the first correct effect, usually shortened to DINE. When a resource matches the rule and a specified related resource does not exist, the effect deploys that related resource through an embedded ARM template. The classic use is ensuring every resource of a type has a diagnostic setting routing its logs somewhere, or that every subnet has a network security group. The defining requirement, and the one that catches everyone, is that deployIfNotExists needs a managed identity on the assignment, and that identity must hold the roles required to perform the deployment it describes. Without the identity and its roles, the policy evaluates, reports noncompliance, and corrects nothing. DINE also does not run on existing resources automatically; it triggers on create and update, and you must run a remediation task to bring the back catalog into line.

Modify is the second correct effect, and it changes properties on the resource during the request or during remediation rather than deploying a separate resource. The common use is adding or replacing a tag, or toggling a property to a required value. Like deployIfNotExists, modify needs a managed identity with the right roles, because it is making a change on your behalf, and like DINE it requires a remediation task to alter resources that predate the assignment. Append is the lightest correct effect: it adds a field or value to a resource during the create or update request, for example adding a default tag if one is absent. Append acts at request time and does not retroactively change existing resources, and it does not need a managed identity, which makes it simpler but also narrower than modify.

### What is the difference between the deny and audit effects?

Deny blocks a noncompliant create or update at the control plane so the resource never exists, while audit allows the operation and only records the resource as noncompliant. Deny prevents; audit observes. If your goal is to stop a configuration from happening, audit will never do it no matter how the rule is written.

The reason this distinction matters so much is that the two effects look identical in the authoring experience and differ only in the single effect field, so it is trivial to assign audit while believing you have prevention. Teams discover the gap when a configuration they thought was forbidden keeps appearing, and the compliance view dutifully marks each new instance noncompliant while letting it through. The fix is to change the effect to deny once you have confirmed, usually through a period of audit, that the rule does not block legitimate work. Audit first to measure, then deny to enforce, is the safe sequence, and it is why many built-in definitions ship with the effect as a parameter you set at assignment time rather than a value baked into the rule.

There is one more wrinkle worth holding. Deny evaluates the request payload, so it can only block based on what is in the create or update call. If a property is set after creation by a separate operation, a deny on that property at creation will not catch the later change unless that change is itself an update that re-evaluates. For properties that are mutated post-creation, the durable enforcement is often a deployIfNotExists or modify that corrects the drift, paired with a deny that handles the create path, which is the kind of layered design governance matures into.

## The step-by-step setup with working commands

With the effect chosen, the rest of the setup is mechanical, and it is worth running it once from the command line so you understand what the portal is doing on your behalf. The flow is: author or pick a definition, optionally group definitions into an initiative, assign at a scope, and then remediate. The examples below use the Azure CLI because it reads cleanly and reproduces exactly, and the same operations exist in PowerShell, Bicep, and ARM for when you move the control into source control.

A policy definition is a JSON document with two halves: a `policyRule` that pairs an `if` condition with a `then` effect, and a `parameters` block that lets the rule be reused. Here is a compact definition that denies storage accounts which allow public blob access, written so the effect is a parameter you can set to audit while testing and deny once you trust it.

```json
{
  "properties": {
    "displayName": "Deny storage accounts that allow public blob access",
    "policyType": "Custom",
    "mode": "All",
    "parameters": {
      "effect": {
        "type": "String",
        "allowedValues": ["Audit", "Deny", "Disabled"],
        "defaultValue": "Audit",
        "metadata": { "displayName": "Effect" }
      }
    },
    "policyRule": {
      "if": {
        "allOf": [
          { "field": "type", "equals": "Microsoft.Storage/storageAccounts" },
          { "field": "Microsoft.Storage/storageAccounts/allowBlobPublicAccess", "equals": true }
        ]
      },
      "then": { "effect": "[parameters('effect')]" }
    }
  }
}
```

Create that definition at a scope, then assign it. Creating at a management group rather than a single subscription lets every child subscription use the same definition without duplicating it.

```bash
# Create the custom definition at a management group
az policy definition create \
  --name "deny-storage-public-blob" \
  --display-name "Deny storage accounts that allow public blob access" \
  --rules @policy-rule.json \
  --params @policy-params.json \
  --mode All \
  --management-group "mg-org-root"

# Assign it to a subscription, setting the effect to audit first
az policy assignment create \
  --name "deny-storage-public-blob" \
  --display-name "Deny public blob access (audit)" \
  --policy "deny-storage-public-blob" \
  --scope "/subscriptions/00000000-0000-0000-0000-000000000000" \
  --params '{ "effect": { "value": "Audit" } }'
```

Run an evaluation and read the result rather than waiting for the next scheduled scan, so you see immediately what the rule catches.

```bash
# Trigger an on-demand compliance scan for the subscription
az policy state trigger-scan \
  --subscription "00000000-0000-0000-0000-000000000000"

# List noncompliant resources for the assignment
az policy state list \
  --filter "PolicyAssignmentName eq 'deny-storage-public-blob' and ComplianceState eq 'NonCompliant'" \
  --query "[].{resource:resourceId, state:complianceState}" \
  --output table
```

Once the audit run confirms the rule flags what you expect and nothing you did not, flip the effect to deny and the same definition now prevents the configuration at create and update time.

```bash
# Promote the assignment from audit to deny
az policy assignment update \
  --name "deny-storage-public-blob" \
  --scope "/subscriptions/00000000-0000-0000-0000-000000000000" \
  --params '{ "effect": { "value": "Deny" } }'
```

This audit-then-deny promotion is the safest way to roll out a preventive control, because it surfaces every legitimate workload that the rule would have blocked before the block goes live. A rule that looks obviously correct on paper routinely turns up a handful of real exceptions in the audit pass, and finding them while the effect is still audit means you can write the exemptions or adjust the condition before anyone is blocked mid-deployment.

### How do I test a policy before enforcing it?

Assign the definition with the effect set to audit, trigger an on-demand compliance scan, and read the noncompliant results. Audit changes nothing about how resources are created, so you see exactly what a deny would have blocked without blocking anything, then promote the effect to deny once the results are clean.

The value of this pattern is that it separates the question of whether the rule is correct from the question of whether enforcing it is safe. A rule can be perfectly written and still be unsafe to enforce because a legitimate workload depends on the configuration it forbids, and only an audit pass against real resources reveals that. Skipping the audit step is how a deny policy ends up blocking a production deployment on its first day, which is the fastest way to make a platform team distrust governance entirely. Spend a few days in audit, read the results, resolve the surprises, and the promotion to deny is a non-event.

For effects that correct rather than prevent, the same caution applies in a different form. A deployIfNotExists or modify assignment should be created, its identity and roles confirmed, and a remediation task run against a small scope first, so you watch the correction land on a handful of resources before you turn it loose on the estate. Reproducing this whole loop end to end, from a custom definition through an audit pass to a deny promotion and a remediation, is exactly the kind of exercise the [hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) are built for, since policy behavior is far easier to trust once you have watched it act on resources you created yourself rather than read about it.

## Grouping definitions into an initiative

A single rule rarely constitutes a standard. A real governance requirement is usually a set: an encryption baseline might be a dozen rules across storage, SQL, and disks; a regulatory benchmark might be hundreds. Assigning each of those individually means hundreds of assignments to manage, exempt, and report on separately, which does not scale. An initiative, also called a policy set, groups related policy definitions into a single object you assign and report on as one unit. This is step two of the checklist and the thing that turns a pile of rules into a manageable control.

An initiative definition references its member policy definitions by ID and maps each member's parameters up to initiative-level parameters, so you set a value once and it flows to every member that needs it. When you assign the initiative, the compliance view rolls up: the initiative has an overall compliance percentage, and you can drill into each member policy to see which one a resource failed. That rollup is the reporting benefit, and it is significant. Leadership wants one number for the encryption baseline, not a dozen, and an auditor wants to see the benchmark as a named set rather than reconstructing it from scattered assignments.

Initiatives also make exemptions and overrides coherent. Because the initiative is one assignment, you exempt a resource from the whole set or, with more recent capabilities, from specific members within it, at one place. Azure ships large built-in initiatives that map to common regulatory and security baselines, and the usual pattern is to assign a built-in initiative for the broad benchmark and add a smaller custom initiative for organization-specific rules. Grouping by intent is the rule of thumb: an initiative should answer one governance question (are we encrypted, are we logging, are we tagged) so its compliance number means something, rather than being a grab bag of unrelated rules whose aggregate percentage tells you nothing actionable.

Here is the shape of assigning a built-in or custom initiative from the CLI. The mechanics mirror a single assignment, with the policy set definition standing in for the definition.

```bash
# Assign an initiative (policy set) to a management group
az policy assignment create \
  --name "encryption-baseline" \
  --display-name "Encryption baseline" \
  --policy-set-definition "/providers/Microsoft.Management/managementGroups/mg-org-root/providers/Microsoft.Authorization/policySetDefinitions/encryption-baseline" \
  --scope "/providers/Microsoft.Management/managementGroups/mg-org-root" \
  --location "eastus" \
  --mi-system-assigned
```

Note the last two arguments. When an initiative contains any deployIfNotExists or modify member, the assignment needs a managed identity and a location for it, which is why the example requests a system-assigned identity. An initiative of pure audit and deny rules needs neither, and adding them does no harm but signals that you expect to remediate. Getting this right at assignment time avoids the most common initiative failure, which is assigning a baseline full of DINE rules with no identity and watching it correct nothing.

### Should I use a built-in initiative or build my own?

Start with the built-in initiative that matches your benchmark, because Microsoft maintains its members as the underlying services change, then layer a small custom initiative for rules specific to your organization. Building a large benchmark from scratch means owning maintenance you could inherit for free.

The judgment shifts when your requirements diverge from any published benchmark, which is common for organization-specific tagging, naming, and region rules that no external standard covers. Those belong in a custom initiative you own, kept small and focused so it stays readable. The pattern that works at scale is therefore two-layered: built-in initiatives carry the recognized benchmarks and stay current without your effort, and a lean custom initiative carries the rules that are yours alone. Trying to fork a giant built-in initiative to add three custom rules is the mistake, because you take on maintenance of the whole thing; keeping the custom rules in their own initiative keeps both layers clean.

## Scopes, inheritance, and the exemptions that handle exceptions

Step three placed the assignment at a scope; this section is about what that scope decision actually controls and how to handle the cases it does not fit. Scope in Azure Policy is the node in the resource hierarchy where an assignment lives, and the hierarchy runs management group, subscription, resource group, resource. An assignment applies to its scope and everything beneath it, and that downward flow is the single most important behavior to keep exact: inheritance goes down, never up. A rule at a subscription covers every resource group and resource in that subscription, but not a sibling subscription, and not the management group above it. A rule at a management group covers every subscription beneath it, which is why broad standards live high.

This inheritance is what makes governance scale, and it is also what makes over-broad scoping painful. Assign a deny at the organization root and it reaches every subscription, including the sandbox where developers are supposed to break things, the data-science environment that legitimately needs the configuration you forbade elsewhere, and the legacy subscription mid-migration that cannot yet comply. None of those teams did anything wrong; the assignment simply reached further than the standard actually applies. The instinct at that point is to lower the scope, but if the rule genuinely applies almost everywhere, lowering it means re-assigning at many child scopes and losing the single-assignment simplicity. The better tool for the genuine exception is an exemption.

An exemption is a record, attached to a specific scope and optionally a specific resource, that excuses it from an assignment or from specific definitions within an initiative, with a stated category and an optional expiry. The two categories are waiver, meaning the resource is excused without a plan to comply, and mitigated, meaning the requirement is met by some other control so the policy need not apply. The exemption is not a way to weaken the rule; it is a way to document, in the platform itself, the one place the rule does not apply and why. That distinction is what keeps the compliance view honest, because an exempted resource is reported as exempt rather than silently passing, so an auditor can see exactly which exceptions exist and on what grounds.

The configuration discipline around exemptions is what separates a governed estate from a gamed one. A handful of well-documented exemptions with expiry dates is healthy; it shows the standard is real and the exceptions are tracked. A long list of permanent waivers is a smell, and it usually means the assignment was scoped too broadly in the first place and the exemptions are quietly undoing it. When you find yourself writing the fifth exemption for the same kind of environment, the signal is to narrow the assignment scope or split the rule, not to keep waiving. Exempt the exception, not the rule, is the discipline, and it keeps the number of exemptions small enough that each one means something.

Here is an exemption created from the CLI, excusing a single resource group from an assignment with a category and an expiry so it does not become permanent by neglect.

```bash
# Exempt a resource group from an assignment, with a reason and an expiry
az policy exemption create \
  --name "sandbox-public-blob-waiver" \
  --display-name "Sandbox waiver for public blob access" \
  --policy-assignment "/subscriptions/00000000-0000-0000-0000-000000000000/providers/Microsoft.Authorization/policyAssignments/deny-storage-public-blob" \
  --scope "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-sandbox" \
  --exemption-category "Waiver" \
  --expires-on "2024-01-31T23:59:59Z" \
  --description "Sandbox environment for controlled testing; reviewed quarterly"
```

The expiry is the detail that keeps exemptions from rotting. An exemption with no expiry outlives the reason it was created, the person who created it, and the team that needed it, and a year later nobody remembers why a resource group is excused from a security baseline. An expiry forces a review: when it lapses, the resource becomes subject to the rule again, and someone has to decide consciously to renew the exemption or let the rule apply. That forced review is cheap to set up and expensive to live without.

### How do scopes and exemptions work together?

A scope sets where an assignment applies and inherits downward to everything beneath it; an exemption then excuses a specific resource or resource group from that assignment. Use scope to cover the estate broadly and exemptions to record the rare, justified exceptions, each with a category and ideally an expiry so it is reviewed rather than forgotten.

The interaction becomes important when an initiative is involved, because you can exempt a resource from the whole initiative or from specific member definitions within it. Exempting the whole initiative when only one of its rules is the problem is too blunt, since it excuses the resource from every other control in the set as well. The precise move is to exempt only the member definition that does not apply, leaving the rest of the baseline enforced. That precision is what keeps an exemption from quietly opening a hole far wider than the exception required, and it is the difference between an exemption that documents one exception and one that disables a whole baseline for a resource.

One more interaction is worth naming. An exemption lives at a scope, so an exemption at a resource group covers everything in it, while an exemption at a single resource covers only that resource. Put the exemption at the narrowest scope the exception actually needs, for the same reason you scope assignments tightly: a resource-group-wide exemption written to excuse one resource quietly excuses every other resource in that group from the rule too, which is rarely what anyone intended.

## Remediation: bringing existing resources into line

Steps one through four govern what happens to new and changed resources. Step five, remediation, is about the resources that already exist, and it is the step that most often gets skipped because the dashboard can look fine without it. Deny prevents new violations but never touches existing ones. DeployIfNotExists and modify correct resources, but only as part of a create or update by default, which means a resource that has sat untouched since before the assignment is noncompliant and stays noncompliant until something forces a correction. That forcing function is a remediation task.

A remediation task takes a deployIfNotExists or modify assignment and applies its correction to the existing resources that are currently noncompliant. It is the mechanism that closes the gap between the rule and the back catalog. The critical configuration fact, the one that defines this whole effect family, is that remediation runs as the assignment's managed identity, and that identity must hold the roles required to perform the change. If the assignment was created without an identity, or with an identity that lacks the necessary role, the remediation task either cannot be created or runs and fails, and the resources stay noncompliant while the assignment reports as though enforcement is in place.

The setup therefore has three parts that must all be present. First, the assignment is created with a managed identity, either system-assigned or a user-assigned identity you manage yourself. Second, that identity is granted the roles it needs at a scope that covers the resources it will correct; a DINE that deploys a diagnostic setting needs rights to write that setting and to read the target resource, for instance. Third, you create the remediation task, which enumerates the noncompliant resources and applies the correction to each. The identity that does this work is the same kind of identity covered in our guide to [setting up managed identities the right way](/2023/04/17/configure-managed-identities/), and the role grants follow the same least-privilege thinking, giving the identity exactly the roles the correction requires and no more.

Here is the sequence from the CLI: create the assignment with an identity, grant the identity a role, then start a remediation task against the assignment.

```bash
# Create a DINE assignment with a system-assigned identity and a location for it
az policy assignment create \
  --name "deploy-diag-settings" \
  --display-name "Deploy diagnostic settings to log analytics" \
  --policy "/providers/.../policyDefinitions/deploy-diagnostic-settings" \
  --scope "/subscriptions/00000000-0000-0000-0000-000000000000" \
  --location "eastus" \
  --mi-system-assigned

# Read back the identity's principal ID, then grant it the role it needs
PID=$(az policy assignment show \
  --name "deploy-diag-settings" \
  --scope "/subscriptions/00000000-0000-0000-0000-000000000000" \
  --query identity.principalId -o tsv)

az role assignment create \
  --assignee "$PID" \
  --role "Monitoring Contributor" \
  --scope "/subscriptions/00000000-0000-0000-0000-000000000000"

# Start a remediation task to correct existing noncompliant resources
az policy remediation create \
  --name "remediate-diag-settings" \
  --policy-assignment "deploy-diag-settings" \
  --resource-group "" \
  --scope "/subscriptions/00000000-0000-0000-0000-000000000000"
```

After the remediation task runs, re-read compliance and the corrected resources should move from noncompliant to compliant. If they do not, the failure is almost always the identity: the wrong role, the role granted at too narrow a scope, or no identity at all. Reading the remediation task's deployment results tells you which, because a failed remediation deployment carries the same authorization or template error any deployment would, and that message names the missing permission or the failing resource directly.

### How do I remediate existing noncompliant resources?

Create the deployIfNotExists or modify assignment with a managed identity, grant that identity the roles its correction requires, then start a remediation task against the assignment. The task applies the effect to resources that predate the assignment, which neither effect touches on its own until a remediation task runs.

The reason remediation is a separate, explicit step rather than automatic is safety. A correct effect changes resources, and changing every existing noncompliant resource the instant an assignment is created could be a large, unreviewed deployment across production. Making remediation a deliberate task you start, ideally against a narrow scope first, lets you watch the correction land on a few resources before you apply it broadly. Remediation tasks also report their own results, so you see how many resources were corrected, how many failed, and why, which turns a bulk change into something you can verify rather than hope about.

There is a useful nuance for ongoing governance. New resources created after the assignment trigger the effect at create time and are corrected automatically, so remediation tasks are mostly a one-time catch-up for the back catalog plus an occasional rerun if the identity's roles were fixed after the fact. Once the back catalog is corrected and the effect handles new resources, the estate converges, and the compliance view stabilizes near fully compliant rather than drifting, which is the outcome that distinguishes a correct effect from an audit that only ever reports the same red.

## Reading compliance: the verification that proves it worked

Step six is verification, and it is where most teams stop too early. The compliance view shows, per assignment and per resource, whether each resource matches the rules, and it rolls up to a percentage per assignment and per initiative. It is the obvious place to confirm a control is working, and it is also the place that most readily lies, because an assignment showing up in the view does not mean the effect is doing anything. An audit assignment at one hundred percent compliant means every resource happens to match; an audit assignment at thirty percent means seventy percent of resources violate the rule and nothing is stopping them. The percentage is a measurement, not a guarantee of enforcement, and reading it as the latter is how a wall of green hides an ungoverned estate.

Verification therefore has to ask a sharper question than is the assignment compliant. It has to ask did the effect do what I intended. For a deny, the verification is to attempt the forbidden create and confirm it is blocked with a message naming the policy; a deny you have never seen reject anything is a deny you have not verified. For a deployIfNotExists or modify, the verification is to confirm the remediation task ran, that previously noncompliant resources are now compliant, and that a newly created resource gets the correction automatically. For an audit, verification is simply that the noncompliant count matches what you expect, since audit makes no other change. The compliance view supports all of this, but you have to drive it with intent rather than glancing at the headline number.

Compliance evaluation is not instantaneous, which trips people who expect a change to show immediately. Azure Policy evaluates on resource create and update in near real time for the request itself, but the broader compliance scan that reconciles existing resources runs on a schedule, roughly every day, and on demand when you trigger it. So after assigning a policy or remediating, the compliance view can lag until the next scan, and reading it too soon shows stale results. Triggering an on-demand scan with the command shown earlier, then reading the state, gives you the current picture without waiting for the scheduled cycle. Mistaking scan latency for a broken policy is a common and avoidable confusion; the policy is working, the view simply has not refreshed.

### How do I check whether a policy is actually being enforced?

Read the per-resource compliance state for the assignment, then prove the effect directly: try the forbidden operation under a deny and confirm it is blocked, or confirm a remediation task corrected the noncompliant resources under a deployIfNotExists. The compliance percentage alone tells you matching, not enforcement.

The deeper habit this builds is treating the compliance view as a hypothesis to test rather than a verdict to trust. A governance control makes a claim, that a configuration is prevented or corrected, and that claim is verifiable by trying to violate it and watching what happens. Teams that build governance they actually rely on run that verification once per control when it is set up and again whenever the rule or scope changes, because a control that worked last quarter can be quietly undone by a scope edit, an exemption, or a change in the effect parameter. Querying compliance programmatically, as in the state-list command earlier, also lets you fold it into a pipeline or a scheduled report, so drift surfaces in a place someone looks rather than in a portal blade nobody opens. The practice layer of working through these verification drills, where you assign a control and then try to break it, is exactly what the [scenario-based troubleshooting and practice resources on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) are built around, since governance you have personally tried to defeat is governance you understand.

## The common misconfigurations and their symptoms

Most policy problems are not exotic. They are the same handful of configuration mistakes, each with a recognizable symptom, and each mapping back to a step in the checklist that was skipped or done wrong. Recognizing the pattern from the symptom is what turns a frustrating afternoon into a five-minute fix, which is the thesis this series keeps returning to. Here are the recurring cases engineers report, described as patterns with the setup step that resolves each.

The first and most common is audit-only governance. The symptom is a compliance dashboard full of noncompliant resources that never decreases, and a configuration the team believed was forbidden continuing to appear. The cause is that the assignment's effect is audit when the intent was prevention, so the rule observes and reports but never blocks or corrects. The fix is step one: change the effect to deny for prevention, or to deployIfNotExists or modify for correction, after an audit pass confirms the rule does not catch legitimate work. The tell is that the same noncompliant resources persist and new ones keep arriving, because nothing in the pipeline is acting on them.

The second is a deny policy blocking a legitimate deployment. The symptom is a deployment or pipeline failing with a policy-violation error, often surfacing deep in a log where it is mistaken for a permissions or template problem. The cause is a correctly working deny whose scope reaches a workload that genuinely needs the blocked configuration. The fix is step four: add an exemption for the specific resource or resource group that legitimately differs, with a category and an expiry, or narrow the assignment scope if the exception is really the rule. The tell is that the failure names a policy in its error, which distinguishes it from an authorization failure, and traces to a recent assignment or scope change.

The third is a deployIfNotExists remediation that corrects nothing. The symptom is a DINE assignment that reports noncompliant resources and never fixes them, even after a remediation task is started, or a remediation task that fails outright. The cause is the managed identity: the assignment was created without one, or its identity lacks the role needed at the scope of the correction. The fix is step five: create the assignment with a managed identity, grant that identity the required role at a scope covering the targets, and rerun the remediation task. The tell is that the remediation task's deployment carries an authorization error naming the missing permission, which points straight at the role grant.

The fourth is an initiative that has grown into a grab bag. The symptom is an initiative whose compliance percentage is meaningless because it bundles unrelated rules, so a single number mixes encryption, tagging, and region controls and tells nobody what to act on. The cause is grouping by convenience rather than intent. The fix is step two: split the initiative so each one answers a single governance question, so its percentage means something specific and its exemptions are coherent. The tell is that stakeholders cannot say what the initiative's compliance number represents, which means it is not serving its reporting purpose.

The fifth is scope inheritance applying a policy too broadly. The symptom is a rule affecting environments it was never meant for, sandbox subscriptions blocked by a production control, or a wave of new noncompliance after an assignment moved up the hierarchy. The cause is an assignment placed too high, so inheritance carries it to children that should have been excluded. The fix is step three combined with step four: lower the assignment to the scope that actually needs it, or keep it high and exempt the genuine exceptions, choosing based on whether the rule applies almost everywhere or only in specific places. The tell is that the newly affected resources cluster in a particular subscription or environment that differs in purpose from the rest.

The sixth is forgetting to remediate after assignment. The symptom is a correct effect that handles new resources perfectly while the existing estate stays noncompliant indefinitely, so the dashboard improves for anything created after the assignment and never for anything before it. The cause is that no remediation task was ever run, so the back catalog was never corrected. The fix is step five: start a remediation task against the assignment, confirm the identity has its roles, and watch the existing resources converge. The tell is a compliance view where the noncompliance is entirely older resources, with everything created after a certain date already compliant.

### Why does my deny policy block a deployment that should be allowed?

The deny is working correctly and its scope reaches a workload that legitimately needs the configuration the rule forbids. Add an exemption for that specific resource or resource group with a documented category and an expiry, or narrow the assignment to a scope that excludes the legitimate case, rather than disabling the rule for everyone.

The diagnostic move when this happens is to read the error, which under a policy block names the policy and the assignment, distinguishing it cleanly from an RBAC authorization failure that names a missing role or action. Once you have the policy name, you know exactly which assignment to look at, and the decision is whether the blocked case is a genuine exception, which calls for a scoped exemption, or evidence that the rule is wrong or scoped too broadly, which calls for fixing the rule or its scope. Reaching for a broad waiver or, worse, deleting the assignment, undoes the governance for every resource that was being correctly protected, so the precise exemption is almost always the right tool. Tracing a confusing block back to a specific assignment is the same reasoning we apply to the broader family of [authorization and access failures](/2024/01/01/azure-rbac-vs-abac-explained/), where the discipline is to read the error for the gate that actually rejected the request before changing anything.

## Making the configuration repeatable as code

A governance control clicked together in the portal is a control nobody can review, reproduce, or roll back cleanly. The setup so far has used the CLI precisely so you can see each operation, but the durable home for definitions, initiatives, and assignments is source control, expressed as Bicep or ARM and applied through a pipeline. Treating policy as code is what makes governance itself governed: changes go through review, the state of every control is readable in a repository, and standing up the same controls in a new tenant is a deployment rather than an afternoon of clicking.

Bicep expresses policy resources directly. A definition, an initiative, and an assignment are all resource types under the authorization provider, so the same module that deploys an environment can carry its governance. Here is a Bicep fragment that defines a custom policy and assigns it at the deploying scope, which keeps the rule and its assignment together and versioned.

```bicep
targetScope = 'subscription'

resource denyPublicBlob 'Microsoft.Authorization/policyDefinitions@2021-06-01' = {
  name: 'deny-storage-public-blob'
  properties: {
    displayName: 'Deny storage accounts that allow public blob access'
    policyType: 'Custom'
    mode: 'All'
    parameters: {
      effect: {
        type: 'String'
        allowedValues: [ 'Audit', 'Deny', 'Disabled' ]
        defaultValue: 'Audit'
      }
    }
    policyRule: {
      'if': {
        allOf: [
          { field: 'type', equals: 'Microsoft.Storage/storageAccounts' }
          { field: 'Microsoft.Storage/storageAccounts/allowBlobPublicAccess', equals: true }
        ]
      }
      then: { effect: '[parameters(\'effect\')]' }
    }
  }
}

resource assignDenyPublicBlob 'Microsoft.Authorization/policyAssignments@2022-06-01' = {
  name: 'deny-storage-public-blob'
  properties: {
    displayName: 'Deny public blob access'
    policyDefinitionId: denyPublicBlob.id
    parameters: {
      effect: { value: 'Deny' }
    }
  }
}
```

Deploying that through a pipeline puts the whole lifecycle of the control under the same review and history as the rest of your infrastructure. A change to the effect, the condition, or the scope becomes a pull request someone approves, and the deployment record shows exactly when a control changed and who changed it. This matters for governance specifically, because the controls themselves are the thing auditors trust, and a control that can be silently edited in a portal is a control whose history is unknowable. Expressing it as code closes that gap.

The connection to drift is direct and worth making explicit. Policy as code is a declaration of the desired state of your governance, and like any infrastructure declaration it can drift if someone edits an assignment out of band in the portal. The same reasoning that applies to [managing Azure infrastructure state and drift](/2025/02/24/azure-iac-state-drift/) applies to the policy layer: the repository is the source of truth, out-of-band changes are drift to detect and reconcile, and a pipeline that redeploys the declared state on a schedule keeps the controls matching what was reviewed. Governance that lives only in the portal drifts the same way any unmanaged infrastructure drifts, and folding it into the same code-and-pipeline discipline as the rest of the estate is what keeps it trustworthy over time.

There is a companion control worth assigning alongside policy when you take governance to code, which is diagnostic settings applied at scale so the policy actions and the resources they govern are observable. Routing those logs consistently is itself a governance task, and the [configuration of diagnostic settings across Azure](/2023/07/17/configure-diagnostic-settings/) is the natural at-scale companion to policy, often delivered through a deployIfNotExists policy that ensures every resource emits logs to a central workspace. Pairing the two means you not only enforce a standard but can see, in the logs, when and where it acted.

## How effects interact when more than one policy matches

A resource is rarely governed by a single assignment. In a mature estate it is covered by a management-group standard, a subscription baseline, and perhaps a resource-group rule, and several of those may match the same resource at once. Knowing how the effects combine is what keeps you from being surprised when a resource is blocked by a rule you did not expect or modified in a way you did not intend. The combination logic is mostly intuitive once stated, but it is rarely stated, so it surprises people.

Deny is decisive. If any matching policy evaluates to deny, the request is blocked, regardless of how many other policies would have allowed it. There is no voting; a single deny is sufficient to reject the create or update. This is why a deployment can fail against a deny assigned three levels up the hierarchy even though every rule at the resource group allows it, and why tracing a block means reading which assignment, at which scope, carried the deny. The decisiveness is deliberate: a prevention control would be worthless if a permissive rule lower down could override it.

The correct effects compose rather than conflict. Multiple append, modify, and deployIfNotExists effects can all apply to the same resource, each making its change, so a resource might get a tag added by one modify, a diagnostic setting deployed by one DINE, and a network rule appended by an append, all from different assignments. The engine applies them, and the ordering among modify and append operations is handled so the results are consistent. Audit effects simply each record their own compliance result, so a resource can be compliant under one assignment and noncompliant under another at the same time, which is correct and expected; each assignment answers its own question.

The interaction that confuses people most is the disabled effect. Setting an assignment's effect parameter to disabled turns that assignment off without deleting it, which is useful for temporarily suspending a control. But disabling one assignment does nothing to another assignment of the same definition at a different scope, so a rule you think you disabled can still be enforced by a separate assignment higher up. When a control you believed was off keeps acting, the cause is usually a second assignment of the same rule at a scope you did not check, and the fix is to find every assignment of that definition across the hierarchy rather than assuming one disable covered them all.

### What happens when two policies conflict on the same resource?

If any matching policy has a deny effect, the request is blocked; deny always wins over allow. Correct effects like modify, append, and deployIfNotExists each apply their change and compose rather than conflict, and audit effects each record their own result independently. There is no precedence by scope for deny; one deny anywhere in the inheritance chain is enough.

The practical consequence is that you debug a surprising block by enumerating every assignment that reaches the resource, across the resource group, subscription, and every management group above it, and finding the one with the deny. The portal's compliance and the effective-policy tooling will show which assignments apply to a resource, which is faster than guessing. For the correct effects, the consequence is that you should expect a resource to accumulate changes from several assignments and design for that, rather than assuming a single assignment owns a resource's configuration. Governance at scale is layered by design, and the layering only works if you understand that deny is decisive while correction composes.

## Policy mode, aliases, and the conditions you can actually write

Two technical details shape what a policy can express, and getting them wrong produces rules that silently match nothing. The first is mode. A policy definition's mode is usually All or Indexed. Indexed means the policy evaluates only resource types that support tags and location, which is the right mode for rules about tags or regions because it skips resource types where those concepts do not apply and would otherwise generate noise. All means the policy evaluates every resource type including resource groups and subscriptions. Choosing Indexed for a tag rule keeps the compliance view clean; choosing All when you need to govern resource groups themselves is necessary because Indexed would skip them. A rule that matches nothing is sometimes simply a mode mismatch.

The second detail is aliases. A policy condition matches on fields, and for resource-specific properties those fields are exposed through aliases, which are stable names that map to a property in a resource type's API. The condition in the storage example matched on an alias for the public-access property. You cannot invent an alias; the property has to be exposed as one, and not every property is. When a rule you expect to work matches nothing, a frequent cause is an alias that does not exist or a different alias than the one you used, and the resolution is to list the available aliases for the resource type and confirm the exact name and the values it returns. Listing aliases from the CLI before writing a condition saves the frustration of a rule that evaluates against a field that is not there.

Conditions themselves combine through `allOf` and `anyOf` for boolean logic, with `field` comparisons like equals, notEquals, in, exists, and like for pattern matching. A well-built condition is specific: it names the resource type, then the property and the value that makes a resource noncompliant, so the rule matches exactly the configurations you mean and no others. An over-broad condition that omits the resource type can match far more than intended and produce a flood of false noncompliance, while an over-narrow condition misses cases. The discipline is the same as the rest of governance, which is to be exact about what you match, because the effect will act on everything the condition catches.

### Why does my policy match no resources at all?

The two usual causes are a mode mismatch and a bad alias. If the rule targets tags or location but the mode is All on resource types that do not support them, or if it should evaluate resource groups but uses Indexed, the rule skips what you meant to catch. If the condition references an alias that does not exist or returns different values than you assumed, it matches nothing.

Resolving it is methodical. Confirm the mode matches the intent: Indexed for tag and location rules, All when you need to govern resource groups and subscriptions or resource types that Indexed excludes. Then confirm the alias by listing the aliases for the target resource type and checking both the name and the values the property actually takes, because a boolean you assumed was true or false might be a string, or the property might live under a different path than the portal label suggests. Testing the condition with the effect set to audit and reading what it flags is the fast confirmation, since an audit pass that catches the resources you expect proves the condition is correct before you promote it to an enforcing effect.

## A worked example: governing a regulated subscription end to end

The pieces are clearer when assembled into one realistic task, so here is a worked example that runs the full checklist against a single requirement. The scenario is common: a subscription holding regulated workloads must meet three standards. Every resource has to sit in an approved region, every storage account has to forbid public blob access, and every resource has to emit diagnostic logs to a central workspace. Those three standards map to three different effects, which is exactly why the example is instructive.

Start with the structure. The subscription lives under a management group, and the region and storage rules are organization-wide standards, so they belong at the management group where they cover this subscription and its siblings. The diagnostic-logging rule is also organization-wide but uses a correct effect, so its assignment needs an identity. You confirm the management-group hierarchy is in place and that you hold Resource Policy Contributor at that scope, satisfying the structural and permission prerequisites before writing anything.

Now choose the effects, the decisive step. The approved-region rule is a prevention requirement, because a resource created in the wrong region cannot simply be moved, so it gets a deny: a built-in allowed-locations policy with the effect set to deny. The public-blob rule is also prevention, so it gets the deny definition from earlier in this guide. The diagnostic-logging rule is correction, because you want every resource, including ones that already exist, to emit logs whether or not whoever created them remembered, so it gets a deployIfNotExists that deploys a diagnostic setting routing logs to the central workspace. Three standards, three effects, each chosen by asking whether you need to prevent or to correct.

Group them sensibly. The region and storage denies are both prevention controls but answer different governance questions, so rather than one grab-bag initiative you keep the regulatory baseline coherent: a custom initiative named for the regulated workload that carries the region, storage, and logging rules together, because in this case they share a single governance question, namely is this subscription meeting its regulatory baseline. That single initiative assigns once, reports one compliance number for the baseline, and lets you exempt at the baseline level when a justified exception arises.

Assign the initiative at the management group with a system-assigned identity and a location, because it contains the deployIfNotExists logging rule. The assignment inherits down to the regulated subscription and any sibling under the same management group. Before promoting the denies, you assign with the deny rules set to audit, trigger a scan, and read the noncompliant results. The audit pass reveals two surprises: a legitimate disaster-recovery resource in a secondary region the approved list omitted, and a storage account a data pipeline needs with public access for a specific integration. Finding these now, while the effect is audit, is the entire reason for the audit-first sequence.

Handle the exceptions precisely. The secondary region is a real omission, so you fix the rule by adding that region to the approved list rather than exempting, because the requirement was simply incomplete. The public-access storage account is a genuine, narrow exception, so you write an exemption on that specific resource, category mitigated because a separate network control compensates, with an expiry six months out so it is reviewed. You exempt only the storage member of the initiative for that resource, leaving the region and logging rules enforced on it. The exception is recorded, scoped to one resource, time-bound, and limited to the one rule that does not apply.

Now promote and remediate. With the surprises resolved, you flip the region and storage rules from audit to deny, and they begin blocking new violations at the control plane. For the logging rule, you grant the assignment's identity the role it needs to write diagnostic settings at the subscription scope, then start a remediation task so every existing resource that lacks a diagnostic setting gets one. You watch the remediation task report its results, confirm the previously noncompliant resources move to compliant, and create a test resource without a diagnostic setting to confirm the effect adds one automatically at creation. That last test is the verification that proves the correction works going forward, not just for the back catalog.

Finally, read compliance with intent. The initiative shows a baseline number, and you drill into each member to confirm each is doing its job: the region deny has blocked a test create in a disallowed region, the storage deny has blocked a public-access create, the logging DINE shows the remediated resources compliant and the test resource auto-corrected, and the one exemption shows the data-pipeline storage account as exempt rather than silently passing. The whole control now lives in a Bicep module in your repository, applied through a pipeline, so its history is reviewable and a new regulated subscription inherits the baseline by being placed under the management group. That is governance enforced rather than documented, built by running the six steps in order, and the decisive choice at the center of it was the effect for each rule.

## From a first assignment to a governed estate

A single correct control is a milestone, but governance is a posture you grow into, and the configuration habits that make the first control trustworthy are the ones that scale. The progression most teams follow starts with audit-everything to measure, moves to enforcing the highest-value preventions with deny, adds correction with deployIfNotExists and modify for the standards that can be auto-fixed, and ends with the whole set expressed as code and assigned through the management-group hierarchy so new subscriptions inherit the baseline automatically. Each stage is the same checklist applied to more controls, and the discipline that held for one assignment holds for a hundred.

The trap at scale is the one this guide opened on, dressed up larger: a sprawling set of audit assignments that produce an impressive-looking compliance program and enforce almost nothing. The antidote is to keep asking, control by control, whether the effect matches the intent. A standard you only ever want to measure stays audit, honestly. A standard you want to guarantee gets deny or a correcting effect, and you verify it acts. Resisting the temptation to call audit-everywhere a governance program is the single most valuable habit, because it keeps the compliance view meaningful and the enforcement real.

The other habit that scales is treating exemptions as data about your scoping rather than as escape hatches. A growing list of waivers is a signal to revisit where assignments are scoped, not a normal cost of governance. When exemptions cluster around a particular environment, that environment probably wants its own scope with a different baseline, which is cleaner than excusing it from a too-broad standard one resource at a time. Watching the exemption list and acting on its patterns keeps the governance model honest as the estate grows, and it is the kind of operational feedback loop that separates a governance program that ages well from one that calcifies into a pile of permanent exceptions nobody understands.

Building these instincts is faster with a place to practice the full loop against resources you can break without consequence, which is what the [hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) provide for authoring, assigning, and remediating policies, and the practice and research drills on ReportMedic complement them for working through governance scenarios and the reasoning behind each control. Governance you have set up, broken, and fixed yourself is governance you can reason about under pressure, which is the difference between copying an assignment and understanding why it enforces what it does.

## The verdict

Azure Policy is the engine that turns a written standard into an enforced one, and the decisive configuration choice is the effect. Audit observes and changes nothing, deny prevents a noncompliant create or update at the control plane, and deployIfNotExists and modify correct resources with the help of a managed identity that must hold the right roles. Everything else in the setup arranges itself around that choice: an initiative groups related rules so they assign and report as a unit, a scope lands the control where it belongs and inherits downward only, an exemption records the rare justified exception with a category and an expiry, a remediation task drags the existing estate into compliance, and the compliance view verifies the effect did what you intended rather than merely that the assignment exists.

The mistake to design against is the comfortable one: assigning audit policies and believing the environment is governed. It is not; it is measured. If you want a configuration prevented, only deny does it, and if you want existing resources corrected, only a remediation task driven by a properly permissioned identity does it. Run the six-step checklist in order, choose the effect by asking whether you need to observe, prevent, or correct, verify by trying to violate the rule, and express the whole thing as code so the controls themselves are reviewable. Do that and your compliance view stops being a wall of red you have learned to ignore and becomes a true statement about an estate that enforces its own standards.

## Frequently Asked Questions

### Q: How do I set up Azure Policy for governance from scratch?

Start by confirming your management-group hierarchy is in place, because assignments inherit downward and broad standards belong at the top. Then run the six-step sequence for each control: pick the effect based on whether you need to observe, prevent, or correct; group related definitions into an initiative; assign at the scope that the rule should cover; declare any known exemptions; provision a managed identity and run a remediation task if the effect corrects; and read compliance to verify the effect acted. The single most important decision is the effect, since an audit-only assignment measures drift without stopping it. Assign preventive rules as audit first to find legitimate exceptions, then promote to deny once the audit pass is clean, which is the safe way to roll out enforcement without blocking real work on day one.

### Q: What is the difference between the deny, audit, and deployIfNotExists effects?

These three effects do three different jobs. Audit observes: when a resource matches the rule, it is marked noncompliant in the compliance view and nothing else changes, so the resource is created or left exactly as it would have been. Deny prevents: it rejects a noncompliant create or update at the control plane before the resource exists, so nothing has to be cleaned up afterward, but it never touches resources that already exist. DeployIfNotExists corrects: when a matching resource lacks a specified related resource, it deploys that related resource through an embedded template, which requires a managed identity holding the right roles and a remediation task to fix resources that predate the assignment. The rule of thumb is to use audit to measure, deny to prevent new violations, and deployIfNotExists to correct missing related resources like diagnostic settings or network security groups.

### Q: How do I group multiple policies into an initiative?

An initiative, also called a policy set, references its member policy definitions by ID and maps their parameters up to initiative-level parameters, so you set a value once and it flows to every member. You create the policy set definition at a scope, usually a management group so all children can use it, then assign the initiative exactly as you would a single policy. The compliance view rolls up to one percentage for the initiative with a drill-down to each member, which is the reporting benefit. If any member uses a deployIfNotExists or modify effect, the assignment needs a managed identity and a location. Group by intent so each initiative answers a single governance question, like whether an estate is encrypted or logging, rather than bundling unrelated rules whose combined compliance number tells nobody what to act on.

### Q: How do scopes and inheritance work in Azure Policy?

Scope is the node in the resource hierarchy where an assignment lives, and the hierarchy runs management group, then subscription, then resource group, then resource. An assignment applies to its scope and everything beneath it, and the inheritance flows downward only, never upward. A rule at a subscription covers every resource group and resource in it but not a sibling subscription; a rule at a management group covers every subscription under it. This is why durable organization-wide standards belong at the management group, where they cover the estate and automatically reach new subscriptions added under the same group. Placing a rule too low leaves siblings ungoverned, while placing it too high reaches environments the standard was never meant for, so the judgment is to find the smallest scope that contains everything the rule must cover and nothing it must not.

### Q: How do I remediate existing noncompliant resources?

Deny prevents new violations but never touches existing resources, and deployIfNotExists and modify correct resources only during create or update by default, so existing noncompliant resources stay noncompliant until you run a remediation task. Create the assignment with a managed identity, grant that identity the roles its correction requires at a scope covering the targets, then start a remediation task against the assignment. The task enumerates the currently noncompliant resources and applies the correction to each, running as the assignment's identity. If remediation fixes nothing or fails, the cause is almost always the identity: missing entirely, or lacking the role at the right scope. Read the remediation task's deployment results, which carry the same authorization or template error any deployment would, and that message names the missing permission directly so you can grant exactly what is needed.

### Q: How do I check whether a policy is actually being enforced?

The compliance view shows whether each resource matches the rules and rolls up to a percentage, but a high percentage proves matching, not enforcement. To verify enforcement, prove the effect directly. For a deny, attempt the forbidden create and confirm it is rejected with a message naming the policy; a deny you have never seen block anything is unverified. For a deployIfNotExists or modify, confirm the remediation task ran, that previously noncompliant resources are now compliant, and that a newly created resource gets the correction automatically. Remember that the broad compliance scan runs on a schedule, roughly daily, plus on demand, so after assigning or remediating you may need to trigger an on-demand scan rather than waiting, and reading the view too soon shows stale results that look like a broken policy when the policy is fine.

### Q: Why does my Azure Policy show compliant but nothing is being enforced?

The most common reason is that the effect is audit when you intended prevention. An audit assignment that shows compliant simply means every evaluated resource happens to match the rule, and an audit assignment showing noncompliant is still doing nothing about it; audit only ever observes. Change the effect to deny for prevention or to deployIfNotExists or modify for correction, after an audit pass confirms the rule does not catch legitimate work. A second possibility is that a deployIfNotExists assignment looks fine but its managed identity is missing or under-permissioned, so it reports compliance based on evaluation while correcting nothing. Verify by trying to violate the rule and watching what happens, because a control that has never rejected or corrected anything has not been shown to enforce, regardless of what the percentage says.

### Q: What happens when two policies conflict on the same resource?

If any matching assignment evaluates to a deny, the request is blocked, regardless of how many other policies would allow it; deny always wins and there is no precedence by scope, so a single deny anywhere in the inheritance chain is decisive. The correct effects compose rather than conflict: multiple modify, append, and deployIfNotExists assignments can each apply their change to the same resource, so it might receive a tag from one, a diagnostic setting from another, and a network rule from a third. Audit effects each record their own result independently, so a resource can be compliant under one assignment and noncompliant under another simultaneously. To debug a surprising block, enumerate every assignment that reaches the resource across its resource group, subscription, and all management groups above it, and find the one carrying the deny, which the effective-policy tooling will surface faster than guessing.

### Q: Do I need a managed identity for every Azure Policy assignment?

No, only for assignments that contain a deployIfNotExists or modify effect, because those effects make changes on your behalf and need an identity with permission to make them. Audit, deny, and append effects need no managed identity: audit and deny only evaluate, and append adds a value during the request without a separate deployment. When an assignment or an initiative includes any deployIfNotExists or modify member, you create it with a managed identity, either system-assigned or a user-assigned identity you manage, and supply a location for that identity. You then grant the identity the specific roles its corrections require, scoped to cover the resources it will change. Forgetting the identity, or granting it the wrong role or the right role at too narrow a scope, is the single most common reason remediation reports success on paper while correcting nothing in practice.

### Q: What is the difference between an exemption and disabling a policy?

An exemption excuses a specific resource or resource group from an assignment, or from specific members of an initiative, while leaving the assignment fully active for everything else; it is the precise tool for a justified exception, carries a category of waiver or mitigated, and can have an expiry that forces a review. Disabling, by setting an assignment's effect to disabled, turns off the entire assignment without deleting it, which is a blunt, estate-wide suspension rather than a targeted exception. Use an exemption when one resource legitimately differs and the rule should keep applying everywhere else. Use disabled only to temporarily suspend a whole control, and remember that disabling one assignment does nothing to a separate assignment of the same definition at another scope, so a rule you think you turned off can still be enforced by another assignment higher in the hierarchy.

### Q: Why does my policy condition match no resources?

The two usual causes are a mode mismatch and a bad alias. If the rule targets tags or location, it should use Indexed mode, which evaluates only resource types that support those concepts; using All on a tag rule, or Indexed when you actually need to govern resource groups and subscriptions, makes the rule skip what you meant to catch. The second cause is an alias that does not exist or returns different values than you assumed, since conditions match resource properties through aliases that map to the resource type's API, and you cannot invent one. List the available aliases for the target resource type, confirm both the exact name and the values the property takes, and test the condition with the effect set to audit so you can read what it flags before promoting it. A boolean you assumed might actually be a string, or the property might sit under a different path than the portal label suggests.

### Q: Should I assign policies at the management group or the subscription?

Assign at the highest scope where the rule applies without exception, then narrow only when a subset genuinely differs. Broad, durable standards like allowed locations, required tags, and encryption baselines belong at the management group, where they cover every subscription beneath and automatically reach new ones added under the same group, keeping the organization-wide controls consistent. Workload-specific or environment-specific rules belong at the subscription or resource group, where they stay flexible without affecting the rest of the estate. The mistake to avoid is assigning a production-grade deny at the organization root where it reaches sandbox and data-science environments that legitimately need the blocked configuration, which forces you to write exemptions to undo an over-broad assignment. Find the smallest scope that contains everything the rule must cover and nothing it must not, leaning higher only for genuine organization-wide standards.

### Q: How long does it take for an Azure Policy assignment to take effect?

For new and changed resources, a policy assignment takes effect almost immediately: deny, append, modify, and deployIfNotExists evaluate during the create or update request itself, so a deny blocks the very next noncompliant deployment after assignment. For the evaluation of resources that already exist, there is a delay, because the broad compliance scan that reconciles existing resources runs on a schedule, roughly every twenty-four hours, plus whenever you trigger an on-demand scan. So after assigning a policy you may see the compliance view lag until the next scan completes, which is often mistaken for a broken policy when the assignment is working fine and the view simply has not refreshed. Trigger an on-demand compliance scan to see current results without waiting, then read the per-resource state for an accurate picture rather than the possibly stale headline percentage.

### Q: Can Azure Policy automatically fix resources, not just flag them?

Yes, through the deployIfNotExists and modify effects, which correct rather than merely observe. Modify changes properties on the resource, such as adding or replacing a tag or toggling a required setting, while deployIfNotExists provisions a related resource that should exist, such as a diagnostic setting or a network security group association. Both require a managed identity on the assignment holding the roles needed to make the change, and both correct existing resources only when you run a remediation task; on their own they act during create and update. Append is a lighter correction that adds a field or value during the request without an identity, but it does not retroactively change existing resources. Audit and deny cannot fix anything: audit only flags, and deny only blocks. So automatic correction means choosing deployIfNotExists or modify, wiring up the identity and its roles, and running remediation for the back catalog.

### Q: How do I roll out a deny policy without breaking existing deployments?

Roll it out in audit mode first. Assign the definition with the effect parameter set to audit, trigger an on-demand compliance scan, and read the noncompliant resources, which shows you exactly what a deny would block without blocking anything. Real workloads that legitimately depend on the forbidden configuration surface here, and you resolve each before enforcing: fix the rule if it was simply incomplete, or write a scoped exemption with a category and an expiry for a genuine exception. Once the audit results are clean and the surprises are handled, promote the effect to deny, which now prevents new violations while the documented exceptions remain excused. This audit-then-deny sequence is the safest enforcement rollout because it finds legitimate exceptions while nothing is yet blocked, avoiding the classic failure of a deny that breaks a production pipeline on its first day and makes a team distrust governance entirely.

### Q: Where should Azure Policy definitions and assignments live, in the portal or in code?

In code. A control clicked together in the portal cannot be reviewed, reproduced, or rolled back cleanly, and its history is unknowable, which is a serious problem for governance specifically because the controls are the thing auditors trust. Express definitions, initiatives, and assignments as Bicep or ARM under the authorization provider, keep them in source control, and apply them through a pipeline so every change is a reviewed pull request with a deployment record showing who changed what and when. This also makes governance reproducible: standing up the same baseline in a new tenant becomes a deployment rather than an afternoon of clicking. The portal remains useful for exploring, reading compliance, and triggering scans, but the source of truth for the controls themselves should be the repository, and a pipeline that redeploys the declared state catches out-of-band edits as drift to reconcile.

### Q: What roles do I need to create and assign Azure Policy?

To create and assign policy definitions and initiatives, you need rights at the scope, typically the Resource Policy Contributor role or a higher role like Owner at the management group or subscription where you are working. That covers authoring definitions, creating initiatives, and creating assignments and exemptions. Remediation adds a separate requirement: the assignment's managed identity, not your user account, needs the roles required to perform the correction it deploys, granted at a scope covering the resources it will change. So a deployIfNotExists that writes diagnostic settings needs its identity to hold a role permitting that write. Plan both layers before assigning, because discovering days later that remediation corrected nothing because the identity lacked a role means a round trip you could have avoided. Keep both your authoring rights and the identity's grants least-privilege, matching the role exactly to what each needs to do.

### Q: How is Azure Policy different from Azure Blueprints or RBAC?

RBAC governs who may act on resources, deciding whether an identity can create or modify something, while Azure Policy governs the shape and configuration of resources, deciding whether what is created meets a standard. They run at the same control plane as separate gates a request passes, and a real estate uses both: policy for configuration standards, RBAC for the least-privilege boundary on actions. Azure Blueprints was a packaging concept that bundled policies, role assignments, and resource templates into a repeatable deployment artifact, but the durable, recommended direction is to express that same packaging as infrastructure as code, with policy assignments, role assignments, and resource definitions in Bicep or Terraform under source control. So think of policy as your configuration-standards tool, RBAC as your access-control tool, and code-based deployment as the way to package and version both together repeatably.

### Q: Can I use Azure Policy to enforce tagging across all resources?

Yes, and tagging is one of the clearest places to use the correcting effects rather than only auditing. A deny effect can block the creation of a resource that lacks a required tag, which enforces tagging on new resources at the control plane. An append effect can add a default tag value during the create request when one is absent, and a modify effect can add or replace a tag on existing resources when you run a remediation task, which is how you bring an already-deployed estate into tag compliance. Use Indexed mode for tag policies so they evaluate only resource types that support tags and skip those that do not. The common mature pattern combines a deny that requires the tag on new resources with a modify that remediates existing ones, so both the back catalog and everything created afterward carry the tag, and your cost-attribution and ownership reporting can finally rely on it.

### Q: Why is my deployIfNotExists policy not creating the resource it should?

Almost always the managed identity. DeployIfNotExists deploys a related resource through an embedded template, and that deployment runs as the assignment's managed identity, so if the assignment was created without an identity, or the identity lacks the role needed to perform the deployment at the right scope, the effect evaluates and reports but creates nothing. Confirm the assignment has a managed identity, that the identity holds the specific roles the deployment requires, and that those roles are granted at a scope covering the target resources. The second cause is that deployIfNotExists does not touch existing resources until a remediation task runs, so if you are waiting for it to fix the back catalog, start a remediation task. Read the remediation deployment results, which carry the underlying authorization or template error, and that message names the missing permission or the failing step directly so you know precisely what to grant or fix.

## Operating governance after setup: watching for drift in the controls themselves

Setting up a control is the start, not the end. Governance ages the moment the estate changes around it, so the operational habit that keeps a program trustworthy is treating the controls as living things you monitor rather than artifacts you file. Three signals are worth watching after every control goes live, and each one tells you something the headline compliance number hides.

The first signal is the trend of noncompliance, not its snapshot. A compliance figure that holds steady at ninety-two percent for months can hide a control that has quietly stopped acting, because new violations arriving at the same rate as old ones get fixed produce a flat line that looks healthy. Watching whether the count of noncompliant items is falling, holding, or climbing tells you whether enforcement is winning, treading water, or losing, and a climbing count under a deny is a strong hint that a recent exemption or scope edit opened a path the rule used to close.

The second signal is the exemption list and its growth rate. Each exemption is a small, deliberate hole, and a list that grows steadily is the clearest evidence that an assignment was scoped too broadly for the reality it governs. When several waivers cluster in one environment, the cleaner move is almost always to give that environment its own scope with a baseline that fits it, rather than excusing it one item at a time. Reviewing exemptions on their expiry, and asking why each renewal is needed, keeps the list honest and surfaces scoping problems before they calcify.

The third signal is out-of-band change to the controls. An assignment edited in the portal, an effect quietly flipped from deny back to audit, or a definition altered outside the pipeline are all drift in the governance layer itself, and they are invisible unless the repository is the source of truth and a pipeline reconciles against it. A scheduled redeploy of the declared state catches these edits and either restores the reviewed configuration or flags the divergence for a human to judge. Governance that nobody can edit without leaving a trace is governance you can still trust a year later, which is the only kind worth building.

### How do I know if my governance is getting weaker over time?

Watch three things rather than the headline percentage: whether the noncompliant count is trending down or up, whether the exemption list is growing, and whether any assignment has been edited outside your pipeline. A flat compliance figure can hide a control that stopped acting, and a growing waiver list usually means an assignment was scoped too broadly for what it governs.
