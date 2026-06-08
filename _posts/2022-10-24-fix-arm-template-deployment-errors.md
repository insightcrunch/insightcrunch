---
layout: post
title: "Fix ARM Template Deployment Failures"
page_title: "Fix ARM Template Deployment Errors: Read InvalidTemplate and DeploymentFailed Down to the Nested Provider Cause and Resolve It"
date: 2022-10-24
categories: ["Technology"]
tags: ["Azure", "ARM Templates", "Troubleshooting", "DevOps", "InvalidTemplate", "Cloud Computing"]
excerpt: "ARM template deployment errors hide the real cause inside a nested message. Read InvalidTemplate and DeploymentFailed to the provider error, then fix it."
image: "/assets/images/blog/blog-26.webp"
reading_time: 61
author: "alex-cunningham"
last_updated: 2022-10-24
lang: en
---
An ARM template deployment that fails almost never tells you the truth in its first line. The top of the error reads `InvalidTemplate` or `DeploymentFailed`, and both are generic envelopes that say something went wrong without saying what. ARM template deployment errors are layered: a broad outer status that the portal and the CLI surface first, and a nested resource-provider message buried one or two levels down that actually names the failing resource and the reason. The engineer who fixes the deployment fast is the one who stops reading the outer line, drills to the nested operation, and reads the provider's own words. The engineer who burns an afternoon is the one who sees `DeploymentFailed`, assumes a syntax problem, and starts rewriting template JSON when the real cause was a missing role assignment or an exhausted quota that the template never touched.

![Fixing ARM template deployment failures by reading the nested provider error - Insight Crunch](/assets/images/blog/blog-26.webp)

This article teaches the diagnosis as a method rather than a list of one-off fixes. You will learn how Azure Resource Manager structures a deployment error, where the actionable message hides, how to pull the nested provider error from the deployment operations rather than guessing from the outer envelope, and how to map each common top-level error to its true cause and the command that confirms it. The distinct root causes behind a failed ARM deployment are few: a schema or expression error in the template itself, a circular dependency in the `dependsOn` graph, a resource-provider validation failure that rejects an otherwise well-formed resource, an `AuthorizationFailed` because the deploying identity lacks a role, a quota or capacity limit surfaced through the deployment, a parameter type or value that the template rejects, and an API version or resource type that does not exist. Each one produces a recognizable nested signal, and once you can read that signal you fix the cause instead of editing syntax at random.

The reason this matters is that ARM is the control plane every Azure deployment passes through, whether you author raw JSON templates, write Bicep that compiles to those templates, or run Terraform against the same resource providers underneath. A deployment failure is the most common way an engineer meets ARM head-on, usually mid-incident, usually with a pipeline red and a release blocked. Treating the failure as a template typo when the nested error says `AuthorizationFailed` is the single most expensive misdiagnosis in infrastructure as code, because it sends you editing the one thing that was never broken. The whole craft is learning to find the confirming detail under the generic banner, which is the habit this series returns to again and again: root cause over symptom, the nested message over the outer envelope.

## How an ARM Deployment Error Is Actually Structured

A deployment in Azure Resource Manager is not a single atomic operation. It is a graph of resource operations that ARM orders, submits to the relevant resource providers, and tracks individually. When something fails, ARM rolls the outcome up into a top-level deployment status, and that roll-up is where the generic message comes from. The outer status answers "did the deployment succeed" with a flat no. The detail you need answers "which resource failed and why," and that detail lives in the per-resource deployment operations, not in the summary.

### Why is the top-level error so generic?

The top-level `DeploymentFailed` or `InvalidTemplate` is a category, not a diagnosis. ARM validates and submits many resources in one deployment, so the outer status only reports that at least one operation did not succeed. The specific reason sits in the nested provider error for the resource that actually failed, which you read from the deployment operations.

This layering is deliberate, and once you see why it exists it stops being frustrating. ARM cannot collapse a multi-resource failure into one sentence without losing information, so it preserves the structure: the deployment has a status, each resource operation within it has a status and a message, and the resource provider that owns the resource type contributes the message that names the real problem. A storage account that fails because the name is already taken globally produces a provider message about name availability; the deployment-level status above it just says the deployment failed. If you only read the top, you see "failed." If you read the operation, you see "the storage account name is already in use," which is a different afternoon entirely.

There are broadly two outer errors you will meet, and they sit at different stages. `InvalidTemplate` is a validation-stage failure: ARM rejected the template before it tried to create anything, because the JSON is malformed, an expression does not evaluate, a referenced parameter or variable is missing, or a dependency cannot be resolved. `DeploymentFailed` is a runtime-stage failure: the template validated, ARM began submitting resources, and one or more of them failed at the provider. The distinction tells you where to look first. An `InvalidTemplate` means the problem is in the template document or its parameter wiring, and nothing was deployed. A `DeploymentFailed` means the template was structurally fine and the problem is in what happened when a real resource provider tried to act on a real subscription with real permissions, quota, and state.

A third string you will see is plain `Conflict` or a 409, and that one usually is not a template problem at all. It means the deployment collided with another operation in progress, a resource lock, or a transitioning resource. That failure family has its own diagnosis, and treating it as a template error wastes time. The companion article on [resolving Azure deployment conflict errors](/2022/10/17/fix-azure-deployment-conflict/) walks the 409 case end to end, because a conflict is a concurrency and state problem rather than an authoring problem, and the fix is to serialize or unblock rather than to edit the template.

### Reading the deployment, the operations, and the provider message

The single most useful habit when an ARM deployment fails is to stop looking at the outer error and pull the deployment operations. Every deployment, named or default, records an operation per resource, and each operation carries the provider status message. With the Azure CLI you list those operations against the resource group and the deployment name:

```bash
az deployment operation group list \
  --resource-group myResourceGroup \
  --name myDeploymentName \
  --query "[?properties.provisioningState=='Failed'].{resource:properties.targetResource.resourceName, type:properties.targetResource.resourceType, code:properties.statusMessage.error.code, message:properties.statusMessage.error.message}" \
  --output table
```

That query filters to only the failed operations and projects the four fields that matter: the resource name, the resource type, the provider error code, and the provider error message. The `statusMessage.error.message` field is where the actionable text lives. For a subscription-scoped deployment you use `az deployment operation sub list`, and for management-group or tenant scope the matching `mg` and `tenant` variants. The shape is the same: a list of operations, each with a nested error you can read.

If you prefer PowerShell, the equivalent walks the same structure:

```powershell
Get-AzResourceGroupDeploymentOperation `
  -ResourceGroupName myResourceGroup `
  -DeploymentName myDeploymentName |
  Where-Object { $_.ProvisioningState -eq 'Failed' } |
  Select-Object @{n='Resource';e={$_.TargetResource}},
                @{n='Code';e={$_.StatusMessage.Error.Code}},
                @{n='Message';e={$_.StatusMessage.Error.Message}}
```

The provider message often nests further. A `DeploymentFailed` at the top may contain a resource operation whose error is `ResourceDeploymentFailure`, which in turn wraps the provider's own code, such as `SkuNotAvailable`, `QuotaExceeded`, or `AuthorizationFailed`. You keep reading inward until you reach the leaf error that names a concrete cause. The leaf is the truth. Everything above it is the envelope. When you train yourself to read to the leaf, the entire class of "I have no idea why this failed" problems collapses, because the leaf almost always tells you exactly what to fix.

The Azure portal exposes the same structure under the resource group's Deployments blade. Each deployment shows its operations, and selecting a failed operation reveals the error code and message and, importantly, the raw error JSON, which you can copy. The portal also surfaces a correlation ID for the deployment. That correlation ID is the thread that ties the deployment to the activity log, where ARM records the control-plane events for the operation, including the identity that ran it and the precise action that was denied when authorization is the cause. When the nested message alone is not enough, the activity log filtered by that correlation ID is the next place to look.

## The Diagnostic Signal: Where the Real Cause Hides

Before walking the individual causes, it helps to fix in your mind the map of where each kind of failure announces itself, because that map is what turns a red deployment into a fast diagnosis. The outer error tells you the stage. The nested provider error tells you the cause. The activity log, reached through the correlation ID, tells you the control-plane detail that the provider message sometimes summarizes. And the what-if and validate operations, run before deploy, tell you which of these failures you could have caught without touching the live subscription at all.

The stage matters because it narrows the search before you read a single provider message. An `InvalidTemplate` returned in milliseconds, before any resource appeared in the resource group, is a pre-flight rejection: the template document or its parameter binding is wrong, and the fix is in the file. A `DeploymentFailed` returned after some resources were created and others were not is a runtime rejection: the template was acceptable and a provider refused to act, and the fix is in permissions, quota, naming, state, or a property the provider validates only at creation time. Knowing the stage stops you from rewriting JSON for a runtime problem and from checking RBAC for a syntax problem.

The provider error code is the second coordinate. Codes such as `InvalidTemplate`, `InvalidTemplateDeployment`, and `PreflightValidationCheckFailed` point at the template and its pre-flight validation. Codes such as `AuthorizationFailed` point at RBAC. Codes such as `QuotaExceeded` and `SkuNotAvailable` point at capacity and limits. Codes such as `ResourceNotFound` and `BadRequest` from a specific provider point at a reference or a property that resource type rejects. The code is a strong hint, and the message under it usually completes the diagnosis by naming the resource, the property, and sometimes the exact value that was wrong.

The trap that catches experienced engineers is over-reading the outer line and under-reading the leaf. A pipeline log that prints the deployment error frequently shows only the top-level `DeploymentFailed` with a generic "At least one resource deployment operation failed" string, and a tired engineer reads that, concludes the template is broken, and starts editing. The fix is mechanical discipline: never act on the outer error. Always pull the operations, read to the leaf, and only then decide what to change. This is the read-the-nested-error rule, and it is the namable claim this article is built around. The top-level `DeploymentFailed` is generic by design, so the fix lives in the nested provider error that names the failing resource and the reason it failed.

## Cause One: An InvalidTemplate From a Schema or Expression Error

The first family of failures is the one most people expect: the template itself is wrong, and ARM rejects it at validation before deploying anything. This surfaces as `InvalidTemplate`, and the nested message usually names the line, the expression, or the property that broke. Because nothing was deployed, the resource group is untouched, and the entire problem is in the file you wrote.

### How do I confirm an InvalidTemplate is a syntax error?

Read the nested message under the `InvalidTemplate` code. If it names a JSON parse position, an unrecognized function, an unresolved parameter or variable, or a property that failed schema validation, the cause is in the template document. Run a local validate to reproduce it without deploying.

The most common form is a malformed template expression. ARM template expressions live inside square brackets and call functions such as `resourceId`, `concat`, `reference`, `parameters`, and `variables`. A single mistake there fails the whole template. A frequent example is a `resourceId` call with the wrong number of arguments. The function needs the resource type and the resource name segments, and a child resource needs both the parent and child name segments. Passing one segment where the type requires two produces an expression evaluation error that the nested message describes in terms of the function and the segment count. The fix is to count the name segments the resource type requires and supply exactly that many.

Another frequent form is referencing a parameter or variable that does not exist, or that is spelled differently from its declaration. ARM treats `parameters('storageAccountName')` and `parameters('storageAccountname')` as two different references, and the second fails because no parameter by that exact name was declared. The nested message names the missing parameter, and the fix is to align the reference with the declaration. The same applies to variables and to the outputs that reference them.

A subtler form is a function used in a context where it cannot evaluate. The `reference` function reads a resource's runtime properties and therefore cannot be used in a place that ARM evaluates before deployment, such as a variable definition that ARM resolves at template-expansion time. Using `reference` where only a compile-time value is allowed produces a validation error. The fix is to move the `reference` call into a resource property or an output where runtime evaluation is legal, or to use `resourceId` where you only need the identifier rather than the live properties.

To reproduce and confirm this class without touching the subscription, run the validate operation, which performs the same template validation ARM does at the start of a deployment but stops before creating anything:

```bash
az deployment group validate \
  --resource-group myResourceGroup \
  --template-file azuredeploy.json \
  --parameters @azuredeploy.parameters.json
```

If the template has a schema or expression error, `validate` returns the same `InvalidTemplate` with the same nested message you would have seen on a real deployment, and it does so in seconds and for free. Wiring `validate` into the pull-request stage of a pipeline turns this entire cause into a pre-merge check rather than a deploy-time surprise. The deeper treatment of the template anatomy, the functions, and how ARM expands a template lives in the [complete guide to Azure Resource Manager](/2022/05/16/azure-resource-manager-arm-explained/), which is the pillar to read when the expression model itself is the thing you need to understand rather than a single broken call.

A related schema failure is a property that does not belong on a resource, or a required property that is missing. Resource providers publish a schema per API version, and ARM validates the resource body against it. Sending a property the schema does not define, or omitting one it requires, fails validation with a message that names the property. The fix is to align the body with the schema for the API version you declared, which leads directly into the API version cause covered below, because the schema that applies is the schema of the API version in the resource's `apiVersion` field, not the latest one.

## Cause Two: A Circular Dependency in the dependsOn Graph

ARM deploys resources in an order it computes from their dependencies. You declare dependencies explicitly with `dependsOn` and implicitly through the `reference` and `resourceId` functions, and ARM builds a directed graph from them and deploys in topological order. If that graph contains a cycle, there is no valid order, and ARM rejects the template with a circular dependency error before deploying anything.

A cycle is usually an accident of over-declaring dependencies. Two resources that each list the other in `dependsOn` form the simplest cycle. More often the cycle is indirect: resource A depends on B, B depends on C, and C depends on A, which no one wrote intentionally but which emerged as `dependsOn` entries accumulated. The nested message names the resources in the cycle, which is the thread to pull. You read the named resources, map their `dependsOn` entries, and find the loop.

The fix is rarely to reorder and usually to remove. Most explicit `dependsOn` entries are unnecessary because ARM already infers the dependency from a `reference` or a `resourceId` call in the resource body. If resource A references B's properties, A already depends on B implicitly, and adding an explicit `dependsOn` from B back to A to "make the order clear" creates the cycle. Removing the redundant explicit dependency breaks the loop without changing the real deployment order, because the implicit dependencies still hold. The discipline is to declare an explicit `dependsOn` only when there is a genuine ordering requirement that ARM cannot infer, and to let implicit dependencies carry the rest.

When a cycle is genuine rather than redundant, the resolution is to restructure so the dependency runs one way. A classic case is two resources that each need a value from the other, such as a pair of resources that reference each other's identifiers. The fix is to break the mutual reference by introducing the value as a parameter or by splitting the deployment into stages, so that the second stage consumes the output of the first rather than the two trying to resolve simultaneously. Nested or linked deployments are the common tool for this, because a child deployment can consume the parent's outputs cleanly.

You confirm the cycle the same way you confirm any template-stage error, with `validate`, because a circular dependency is caught at validation before any resource is created. The `validate` output names the resources in the cycle exactly as a real deployment would, so you debug the graph locally and fix the `dependsOn` entries before you ever submit the deployment.

## Cause Three: A Resource Provider Validation Failure

The third family is the one the outer error hides most thoroughly. The template is well-formed, it passes schema validation, ARM accepts it and begins deploying, and then a resource provider rejects a specific resource at creation time. The outer status is `DeploymentFailed`, the resource operation shows `ResourceDeploymentFailure`, and the leaf carries the provider's own code and message. This is where reading to the leaf pays off most, because the leaf can be almost anything the provider enforces that the schema does not.

A provider validation failure happens because schema validation and provider validation are different checks at different times. The schema check confirms the resource body is shaped correctly for the API version. The provider check, which runs when ARM actually creates the resource, enforces the rules only the provider knows: that a storage account name is globally unique and within the allowed character set, that a chosen SKU is offered in the target region, that a referenced subnet exists and has room, that a name does not collide with an existing resource, that a value falls inside a range the provider enforces at runtime. None of these can be caught by schema validation, because they depend on the live state of Azure rather than on the shape of the JSON.

The most common leaf messages in this family are recognizable once you have seen them. A storage account or other globally named resource fails because the name is already taken, and the message names the name and the conflict. A SKU fails because it is not available in the region, which surfaces as `SkuNotAvailable` and is a capacity and availability issue rather than a quota one, discussed further in the related-failures section. A networking resource fails because a referenced subnet or address range is wrong, and the message names the network resource. A child resource fails because its parent does not exist or was not deployed first, which is an ordering problem that the dependency graph should have prevented.

You confirm a provider validation failure by reading the leaf and then verifying the specific condition it names. If the leaf says a name is taken, check the name's availability:

```bash
az storage account check-name --name mystorageacct123
```

If the leaf names a SKU and region, list what is offered there to confirm the SKU is genuinely unavailable rather than misspelled. If the leaf names a subnet, confirm the subnet exists and has free addresses. The pattern is always the same: the leaf names the resource and the condition, and you run the targeted command that proves or disproves that condition before changing anything. The fix follows from what you find: rename the globally unique resource, choose an available SKU or region, correct the network reference, or fix the ordering so the parent exists first.

The reason this cause is so often misdiagnosed is that the outer `DeploymentFailed` looks identical whether the leaf is a provider validation failure, an authorization failure, or a quota failure. An engineer who reads only the outer line cannot tell them apart and defaults to assuming a template problem. The leaf is the only thing that distinguishes them, which is why the entire method comes back to reading the deployment operations rather than the deployment status.

## Cause Four: An AuthorizationFailed During Deployment

A deployment runs under an identity, and that identity needs the role assignments to perform every action the deployment requires. When it lacks one, the resource that needed that permission fails with `AuthorizationFailed`, and the leaf message names the action that was denied, the scope it was attempted at, and often the principal that lacked the permission. This is a runtime failure, so the outer status is `DeploymentFailed`, and the cause is entirely outside the template. No amount of editing JSON fixes a missing role assignment.

### Why does an ARM deployment fail with AuthorizationFailed when the template is correct?

Because the deploying identity, a user, a service principal, or a managed identity, lacks a role that grants the specific action on the target scope. ARM evaluates the deployment under that identity's RBAC, so a missing assignment fails the resource even though the template is valid.

The `AuthorizationFailed` leaf message is precise, and reading it precisely is the whole diagnosis. It names the action, such as a write on a specific resource type, the scope, such as a particular resource group or subscription, and frequently the object ID of the principal. The action plus the scope is the diagnosis: the identity needs a role that includes that action at or above that scope. The most common mistake is assigning a role at the wrong scope, so the identity has Contributor on one resource group but the deployment targets another, or has a role on a child scope when the action is evaluated at the parent. Reading the action and scope from the leaf and comparing them to the identity's actual assignments closes the gap.

You confirm the cause by checking the identity's effective assignments at the scope the leaf named:

```bash
az role assignment list \
  --assignee <principalObjectId> \
  --scope /subscriptions/<subId>/resourceGroups/<rgName> \
  --output table
```

If the assignment that grants the denied action is absent at or above that scope, you have confirmed the cause. The fix is to assign the least-privilege role that includes the action, at the scope the action is evaluated. Reaching for Owner because it is broad is the wrong instinct, because it grants far more than the deployment needs and leaves a standing over-permission; the right move is the specific role that covers the denied actions. The dedicated article on [diagnosing Azure RBAC AuthorizationFailed errors](/2022/10/10/fix-azure-rbac-authorizationfailed/) covers the action-and-scope reading, the control-plane versus data-plane distinction, and the role-assignment propagation delay that makes a freshly granted role appear not to work for a short window, all of which apply directly when authorization is the leaf behind a `DeploymentFailed`.

A particular variant worth naming is the deployment that assigns roles itself. A template that creates a role assignment requires the deploying identity to have permission to write role assignments, which is a higher privilege than deploying ordinary resources. A deployment that creates resources fine but fails on the role-assignment resource is hitting this: the identity can create the workload but not grant access. The leaf names the role-assignment write action, and the fix is to grant the deploying identity the permission to manage role assignments at the scope, typically through a role designed for that, rather than assuming Contributor is enough, because Contributor deliberately excludes the ability to grant access.

## Cause Five: A Quota or Capacity Limit Surfaced Through the Template

A deployment can be perfectly authored and fully authorized and still fail because the subscription has no room for what it asks. Compute quota is scoped per subscription, per region, and per VM family, and a deployment that pushes a region or family over its approved vCPU limit fails with `QuotaExceeded`. The outer status is `DeploymentFailed`, and the leaf names the quota that was exceeded and usually the region and the family. Like authorization, this cause lives entirely outside the template, and editing JSON does nothing.

The signal that distinguishes quota from capacity is the leaf code. `QuotaExceeded` means a soft limit that you can raise through a quota increase request; the resource type exists and the region offers it, but your subscription's approved allocation is full. `SkuNotAvailable` or `AllocationFailed` means a capacity or availability problem; the region or zone cannot place the SKU right now, or the SKU is not offered there at all, which a quota increase will not fix. Confusing the two leads to the wrong action: requesting a quota increase for a capacity problem, or switching regions blindly for a quota problem that a simple increase would have solved.

You confirm a quota cause by reading current usage against the limit for the region and family the leaf named:

```bash
az vm list-usage --location eastus --output table
```

That output lists each VM family's current usage and its limit in the region, and the family the leaf named will be at or near its limit. The fix is to request a quota increase for that specific region and family through the Usage and quotas experience, or to deploy a family or region with headroom if the workload allows. The full treatment of telling a quota error from a capacity error, finding the limiting regional and family quota, and requesting the right increase is the subject of the article on [fixing Azure quota exceeded and vCPU limit errors](/2022/11/07/fix-azure-quota-exceeded/), which matters here because a quota error that surfaces through a template deployment is exactly the kind of cause that the generic `DeploymentFailed` hides until you read the leaf.

This cause is the cleanest illustration of why the read-the-nested-error rule exists. A `DeploymentFailed` whose leaf is `QuotaExceeded` is indistinguishable from a `DeploymentFailed` whose leaf is a template typo until you read the operation. An engineer who assumes the template is wrong will rewrite resource definitions, redeploy, and hit the same quota wall, because the resources were always correct and the subscription was always full. Reading the leaf once turns a repeated failed-redeploy loop into a single quota request.

## Cause Six: A Parameter Type Mismatch or a Missing Required Parameter

Templates take parameters, and the binding between the parameter values you supply and the parameter declarations in the template is a frequent failure point. A parameter declared as an integer that receives a string, a parameter declared with an `allowedValues` constraint that receives a value outside the set, a required parameter with no default that receives no value, or a parameter object whose property names do not match the template all fail at validation with an `InvalidTemplate` or a parameter-specific message. Because this is a validation-stage failure, nothing is deployed, and the fix is in the parameter wiring rather than the resource bodies.

The most common form is a type mismatch from a parameters file. ARM parameters files supply values as JSON, and a value supplied as `"3"` is a string while a parameter declared as `int` expects `3`. The nested message names the parameter and the expected type, and the fix is to supply the value in the declared type. Pipelines that build parameter values dynamically are especially prone to this, because a value interpolated into a parameters file as text becomes a string even when the parameter wants a number or a boolean.

A second form is the `allowedValues` violation. A parameter that constrains its input to a fixed set rejects anything outside the set, and the message names the parameter and lists the allowed values. The fix is to supply a permitted value or, if the constraint is too narrow, to widen the declared set. A third form is the missing required parameter: a parameter with no `defaultValue` must be supplied at deploy time, and omitting it fails validation with a message naming the parameter. The fix is to supply it or to give it a sensible default in the template if one exists.

You confirm all of these with `validate` against the same parameters file you intend to deploy with, because the validation that catches the binding error is exactly the validation `validate` runs:

```bash
az deployment group validate \
  --resource-group myResourceGroup \
  --template-file azuredeploy.json \
  --parameters @azuredeploy.parameters.json \
  --parameters environment=prod instanceCount=3
```

Passing the parameters file and any inline overrides exactly as the real deployment would reproduces the binding error locally. Wiring this into the pipeline means a parameter type mismatch fails the validation step rather than the deployment step, which is faster and does not leave a half-finished deployment behind.

## Cause Seven: An Invalid API Version or Resource Type

Every resource in a template declares an `apiVersion` and a `type`, and both must exist. An `apiVersion` that the resource provider does not offer, or a `type` that is misspelled or belongs to a provider that is not registered in the subscription, fails the deployment. Depending on the exact problem this surfaces as a validation-stage `InvalidTemplate` or as a runtime provider error naming the type or version, so it can appear at either stage, and the leaf names the offending type or version.

An unregistered resource provider is a frequent and easily missed cause. Azure resource providers must be registered in a subscription before resources of their types can be created, and a subscription that has never used a particular service may not have its provider registered. A template that creates a resource from an unregistered provider fails with a message naming the provider namespace and a `MissingSubscriptionRegistration` or similar code. The fix is to register the provider:

```bash
az provider register --namespace Microsoft.ContainerService
```

After registration completes, which can take a short time, the deployment proceeds. Confirming registration state before deploying avoids this entirely:

```bash
az provider show --namespace Microsoft.ContainerService --query registrationState --output tsv
```

An invalid `apiVersion` is the other form. Each resource type supports a set of API versions, and declaring one that does not exist for the type fails. This often happens when a template is copied from an example using a version the provider has since retired, or when a hand-edited version string has a typo. The message names the type and the version, and the fix is to declare a version the provider currently supports for that type. The same care applies to the resource body, because the properties a type accepts can differ between API versions, so a body valid for one version may be invalid for another. The schema that ARM validates against is the schema of the declared `apiVersion`, which ties this cause back to the schema-validation failures in Cause One.

## Pre-Deploy Validation: What-If and Validate

The cheapest deployment failure is the one you catch before deploying. ARM offers two pre-flight operations that run against the template and the live subscription without committing changes, and using them turns most of the causes above into pre-merge checks rather than deploy-time incidents. The two operations answer different questions, and using both covers more ground than either alone.

### Does what-if catch every deployment error before deploying?

No. What-if predicts the changes a deployment would make and runs validation, so it catches template, schema, and many reference errors, but it cannot reliably predict every runtime provider failure such as a quota or capacity limit that depends on live allocation at the moment of deployment. Treat it as a strong filter, not a guarantee.

The `validate` operation runs the same template validation ARM performs at the start of a deployment. It expands the template, evaluates expressions, checks the schema, resolves the dependency graph, and binds parameters, then stops before creating anything. Everything in the validation stage, the entire `InvalidTemplate` family, circular dependencies, expression errors, missing parameters, and type mismatches, is catchable by `validate`. It is fast and free and belongs in the pull-request stage of any pipeline that deploys templates, because it converts an entire class of failures from a deploy-time red into a pre-merge red:

```bash
az deployment group validate \
  --resource-group myResourceGroup \
  --template-file azuredeploy.json \
  --parameters @azuredeploy.parameters.json
```

The what-if operation goes further. It performs validation and then computes the set of changes the deployment would make against the current state of the resource group: which resources would be created, which modified, which deleted, and which left unchanged. It returns a colored diff of the predicted changes, which is valuable on its own for catching an unintended deletion before it happens, and it surfaces validation errors in the process:

```bash
az deployment group what-if \
  --resource-group myResourceGroup \
  --template-file azuredeploy.json \
  --parameters @azuredeploy.parameters.json
```

What-if is especially worth running before a complete-mode deployment, because complete mode deletes any resource in the resource group that the template does not declare, and the what-if diff shows those deletions before they execute. A deployment that would quietly delete a resource someone added out of band is exactly the surprise what-if exists to prevent, and reading the diff before approving the deployment is the discipline that prevents it.

The honest limit of both operations is that they cannot predict every runtime failure. Validation and what-if evaluate the template and the predicted change set, but they do not reserve quota, do not place capacity, and do not always exercise the same provider runtime checks that fire only at actual creation. A deployment that passes what-if can still fail at runtime with `QuotaExceeded` if the subscription crosses its limit between the prediction and the deployment, or with `SkuNotAvailable` if regional capacity changes. What-if narrows the failure surface dramatically, catching the template and many reference and authorization problems early, but it is a filter rather than a guarantee, and the runtime causes still require reading the leaf when they occur. The right mental model is that what-if and validate eliminate the authoring-stage failures so that any failure that survives to deployment is far more likely to be a genuine runtime cause worth the leaf read.

## The InsightCrunch ARM Error Layer Table

The method this article teaches reduces to a single mapping: each top-level error points to a stage, and the real cause hides in a nested location that a specific check confirms. The table below is the findable artifact, the ARM error layer table, mapping each common top-level error to where the real cause hides and the action that resolves it. It is built to be the page you keep open beside a failed deployment.

| Top-level error | Stage | Where the real cause hides | Confirming check | Fix direction |
|---|---|---|---|---|
| `InvalidTemplate` | Validation, pre-deploy | Nested message names the expression, property, or parameter | `az deployment group validate` reproduces it | Correct the expression, schema, or parameter binding in the template |
| `InvalidTemplate` (circular dependency) | Validation, pre-deploy | Nested message names the resources in the cycle | `validate` lists the cycle members | Remove the redundant explicit `dependsOn`; let implicit dependencies order it |
| `DeploymentFailed` with `ResourceDeploymentFailure` leaf | Runtime | Leaf provider code on the failed resource operation | `az deployment operation group list` filtered to Failed | Act on the leaf: rename, change SKU, fix reference, fix ordering |
| `DeploymentFailed` with `AuthorizationFailed` leaf | Runtime | Leaf names the denied action, scope, and principal | `az role assignment list` at the named scope | Assign the least-privilege role that includes the action at the scope |
| `DeploymentFailed` with `QuotaExceeded` leaf | Runtime | Leaf names the region and VM family over limit | `az vm list-usage` for the region | Request a quota increase for that family and region |
| `DeploymentFailed` with `SkuNotAvailable` leaf | Runtime | Leaf names the SKU and region with no capacity | List SKUs offered in the region | Choose an available SKU, region, or zone; this is capacity, not quota |
| `DeploymentFailed` with `MissingSubscriptionRegistration` leaf | Runtime | Leaf names the unregistered provider namespace | `az provider show --query registrationState` | Register the provider, then redeploy |
| `Conflict` / 409 | Runtime, control plane | Activity log names the competing operation or lock | Activity log by correlation ID | Serialize the deployment or remove the lock; see the conflict article |
| Parameter binding error | Validation, pre-deploy | Nested message names the parameter and expected type | `validate` with the real parameters file | Supply the value in the declared type or allowed set |

The table encodes the whole diagnosis. The first column is what you see. The second tells you the stage, which narrows where to look. The third tells you the nested location that holds the truth. The fourth gives the command that confirms it without guessing. The fifth gives the direction of the fix. Reading left to right turns a generic red into a confirmed cause and a concrete action, which is the difference between a five-minute fix and a lost afternoon.

## Prevention: Stop the Failure Before the Deploy

The causes above each have a fix, but the better outcome is a deployment pipeline where most of them cannot reach production. Prevention is mostly about moving the catchable failures left, into validation and review, and about authoring templates so the runtime failures are rare and legible when they do occur.

Run `validate` and `what-if` in the pipeline before every deployment. Validation catches the entire authoring-stage family, the expression errors, the circular dependencies, the schema mismatches, and the parameter binding problems, and it does so in seconds without touching the subscription. What-if adds the change preview, which catches unintended deletions under complete mode and surfaces many reference and authorization problems early. Making both gates required on the pull request means a template that would have failed at deploy time fails at review time instead, where it costs a comment rather than a blocked release.

Pin and align API versions deliberately. A template with `apiVersion` values copied from scattered examples accumulates versions of different ages, some of which the provider may retire. Choosing a current supported version for each resource type and keeping them aligned reduces the surface for version-specific schema failures and makes the template's behavior reproducible. When a version is retired, the failure is predictable and the fix is a version bump, which is far better than a mysterious schema rejection on a resource that worked last quarter.

Declare dependencies sparingly. Most `dependsOn` entries are redundant because ARM infers the dependency from a `reference` or `resourceId` call, and every redundant entry is a chance to introduce a cycle. The discipline of adding an explicit `dependsOn` only for a genuine ordering requirement that ARM cannot infer keeps the dependency graph minimal and acyclic, which removes the circular dependency cause almost entirely.

Confirm the deploying identity's permissions and the subscription's provider registrations as part of environment setup rather than discovering them at deploy time. An identity that runs deployments should hold the roles its deployments require at the scopes they target, granted once during environment provisioning, so that an `AuthorizationFailed` becomes a rare signal of a genuinely new permission requirement rather than a recurring setup gap. Registering the providers a subscription will use, as part of its baseline, removes the `MissingSubscriptionRegistration` cause from first-deployment failures. The choice of authoring tool also affects how many of these failures you meet, and the trade-offs between raw ARM JSON, Bicep, and Terraform are weighed in the comparison of [Bicep, ARM, and Terraform on Azure](/2024/12/30/bicep-vs-arm-vs-terraform/), which matters because Bicep's compile-time type checking catches several of the authoring-stage failures before a template is ever produced.

Test the template, not just validate it. Validation confirms the template is well-formed and deployable, but a separate test pass checks the template against authoring conventions that prevent whole classes of failure before they reach validation: that every parameter is referenced, that no `apiVersion` is hardcoded as an outdated literal where a maintained value belongs, that secure parameters are not given plain-text defaults, that location values flow from a parameter rather than being pinned per resource, and that outputs do not leak secrets. A template that passes a convention test is far less likely to carry the subtle authoring problems that surface later as expression or schema failures, and running such a test in the pull-request stage alongside `validate` catches the issues a pure validity check does not. The point is that validity and quality are different bars, and a template can be valid while still carrying the habits that produce a failure two resources or one API-version retirement from now.

Track quota headroom for the regions and families a workload uses, so a `QuotaExceeded` is anticipated rather than discovered. A subscription approaching its vCPU limit in a region is a known condition, and requesting the increase before the deployment that would cross the limit turns a deploy-time failure into a planned capacity request. The runtime causes that pre-flight validation cannot predict, quota and capacity, are exactly the ones worth monitoring ahead of the deployment that depends on them.

## Related Failures Often Confused With ARM Template Errors

Several failures look like ARM template errors because they surface through a deployment, but their root cause and fix live elsewhere. Telling them apart is part of the diagnosis, because treating them as template problems sends you editing the wrong thing.

The deployment conflict, the 409, is the most common confusion. A `Conflict` returned during a deployment is not a template problem; it means the deployment collided with another operation in progress on the same resource, a resource lock, or a resource in a transitioning state. The fix is to serialize deployments, respect or remove the lock, or wait for the transition to complete, none of which involve the template. The full diagnosis of why a deployment returns a conflict and how to unblock it without retrying into the same race is the subject of the [Azure deployment conflict article](/2022/10/17/fix-azure-deployment-conflict/), and the tell is the 409 code in the leaf, which points at concurrency and state rather than authoring.

Bicep deployment errors share the runtime half of this article entirely, because Bicep compiles to ARM and the deployment that runs is an ARM deployment under the hood. A Bicep deployment that fails at runtime fails with the same provider leaf errors, the same `AuthorizationFailed`, `QuotaExceeded`, and provider validation messages, because the resource providers do not know or care that the template originated as Bicep. What differs is the compile stage: Bicep adds linter and type errors that occur before any ARM template exists, which are a separate family. Separating the Bicep compile-time errors from the shared ARM deploy-time errors is the subject of the [Bicep deployment errors article](/2022/10/31/fix-bicep-deployment-errors/), and the rule is that a Bicep failure is either a compile-time problem in the Bicep, or a deploy-time problem in the ARM it produced, which is one of the causes covered here.

Capacity failures masquerade as quota failures and vice versa, as covered in Cause Five, and the distinction is the leaf code: `QuotaExceeded` is a soft limit to raise, while `SkuNotAvailable` and `AllocationFailed` are capacity conditions that a quota increase does not fix. Reading the leaf code rather than assuming "the deployment failed because of limits" is what separates the right action from the wrong one.

A linked or nested template failure can look like a problem in the parent when the real failure is in the child. ARM treats a linked deployment as its own deployment with its own operations, so a parent that fails because a linked template failed shows a generic failure at the parent level and the real leaf inside the child deployment's operations. The fix is to list the child deployment's operations, not the parent's, which is the same read-to-the-leaf discipline applied across a deployment boundary. The correlation ID ties the parent and child together in the activity log, which is the thread to follow when the failure crosses that boundary.
## The Anatomy of an ARM Error Payload

Reading to the leaf is easier once you know the shape of the JSON you are reading. An ARM error is a nested object, and the nesting is the layering this article keeps returning to, made literal. The outer object carries a `code` and a `message`, and the `message` of a deployment failure frequently contains, or points to, a `details` array holding the next layer inward. Each element of `details` is itself an error object with its own `code` and `message`, and that inner object may again carry `details`. You descend through the `details` arrays until you reach an object with no further nesting, and that terminal object is the leaf.

A typical `DeploymentFailed` payload looks structurally like this, with the specifics varying by cause:

```json
{
  "error": {
    "code": "DeploymentFailed",
    "message": "At least one resource deployment operation failed. Please list deployment operations for details.",
    "details": [
      {
        "code": "ResourceDeploymentFailure",
        "message": "The resource operation completed with terminal provisioning state 'Failed'.",
        "details": [
          {
            "code": "QuotaExceeded",
            "message": "Operation could not be completed as it results in exceeding approved Total Regional Cores quota."
          }
        ]
      }
    ]
  }
}
```

The outermost `code` is `DeploymentFailed`, which tells you nothing actionable and explicitly directs you to list the deployment operations. The middle layer, `ResourceDeploymentFailure`, tells you a specific resource reached a failed terminal state but still does not name the cause. The leaf, `QuotaExceeded`, is the truth, and its message names the quota dimension. An engineer who reads only the outer message follows its own advice poorly by editing the template; an engineer who descends to the leaf reads `QuotaExceeded` and requests a quota increase. The structure is the same for authorization, provider validation, and the rest: the cause is always at the bottom, and the layers above are envelopes that preserve the structure of a multi-resource deployment.

When you pull operations with the CLI, the `properties.statusMessage.error` field on a failed operation is this same nested object, which is why the earlier query projects `statusMessage.error.code` and `statusMessage.error.message`. If the leaf you want sits one layer deeper than the projection reaches, drop the `--query` projection and read the full `statusMessage` object, then descend its `details` manually. The portal's raw error JSON view shows the whole nested object directly, which is often the fastest way to read a deeply nested leaf without crafting a query.

## Walking a Real Failure End to End

The method is clearest applied to a single failure from red to fixed. Consider a pipeline that deploys a template creating a virtual machine, a network interface, and a role assignment, and the deployment comes back `DeploymentFailed` with the generic "At least one resource deployment operation failed" message. The pipeline log shows only that outer line, and the instinct of an engineer under release pressure is to assume the VM template is wrong and start checking the VM resource body. That instinct is the trap. The first move is not to read the template; it is to pull the operations.

Listing the failed operations returns two failed resources rather than one, which is the first useful signal: the failure is not isolated to a single resource, so a single typo is unlikely. The first failed operation is the role assignment, with a leaf code of `AuthorizationFailed` and a message naming a write action on role assignments at the resource group scope and the object ID of the deploying service principal. The second failed operation is the virtual machine, with a leaf code of `QuotaExceeded` naming the regional cores quota. Two different causes, neither of them a template problem, both hidden under the same generic outer error.

The role-assignment leaf is diagnosed by checking what the service principal can do at the scope it named. Listing its role assignments shows it has Contributor on the resource group, which deliberately excludes the permission to write role assignments. That is the cause: Contributor can create the VM and the network interface but cannot grant access, so the role-assignment resource fails. The fix is to grant the service principal a role that includes role-assignment write at the scope, such as one designed for managing access, rather than widening it to Owner, which would grant far more than the deployment needs.

The VM leaf is diagnosed by reading current usage in the region. Listing VM usage shows the family the VM uses is at its approved limit in the region, which is the cause of the `QuotaExceeded`. The fix is a quota increase request for that family and region, or, if the workload tolerates it, a different family with headroom. Neither fix touches the template, and an engineer who had started editing the VM body would have found nothing wrong with it and lost the time to discover that.

The whole diagnosis took two list commands and two confirming checks, and it produced two precise actions: grant one specific permission and request one specific quota increase. The deployment that failed generically was, on inspection, two well-understood runtime conditions wearing the same outer error. This is the read-the-nested-error rule in operation, and it is why the discipline of pulling operations before reading the template is worth building into reflex. Reproducing exactly this kind of layered failure and practicing the leaf read is what the hands-on environment is for; you can [run the deployment and read its nested operations in the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), and [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) to drill the diagnosis until reading to the leaf is automatic.

## Copy Loops, Nested Templates, and the Errors They Add

Two ARM features generate their own error patterns because they multiply or nest the resources a deployment creates, and recognizing those patterns shortens the diagnosis. The first is the copy loop, the `copy` property that creates multiple instances of a resource or a property from a count and an index. The second is the linked or nested template, a deployment that calls another deployment.

A copy loop fails in ways a single resource does not. The count must resolve to a valid integer at template-expansion time, so a `copy` count that depends on a `reference` to a not-yet-deployed resource cannot evaluate, because `reference` is a runtime function and the count is needed at expansion. The fix is to drive the count from a parameter or a value known at expansion rather than from a runtime reference. A copy loop also fails when the generated resources collide, for example when the name expression does not incorporate the `copyIndex` and every iteration produces the same name, which the provider rejects as a duplicate. The fix is to include `copyIndex` in the name so each iteration is unique. The leaf for these names the resource and the collision or the unresolved count, and reading it points straight at the loop.

A nested or linked template adds a deployment boundary, and errors cross that boundary in a way that confuses the diagnosis if you do not expect it. A parent deployment that invokes a child template shows the child as a deployment resource in the parent's operations, and if the child fails, the parent's operation for that child shows a failure that points inward. The real leaf is in the child deployment's own operations, not the parent's. The fix is to list the child deployment's operations directly, using the child deployment's name, which surfaces the same kind of leaf you would read for any deployment. A linked template adds one more failure mode of its own: the link itself. A linked template referenced by a URI that is unreachable, or that requires a SAS token that is missing or expired, fails because ARM cannot fetch the template to deploy it, and the leaf names the retrieval failure rather than a resource. The fix is to make the linked template reachable with valid access at deploy time, which is a packaging and access problem rather than a template-content problem.

The general rule across both features is that the error still lives at a leaf, but the path to the leaf is longer: through a copy iteration, or across a deployment boundary into a child's operations. The correlation ID holds the whole tree together in the activity log, so when a nested failure is hard to trace through the operations, filtering the activity log by the correlation ID shows every control-plane event for the parent and its children in one timeline.

## Complete Mode, Incremental Mode, and the Failures Each Produces

ARM deploys in one of two modes, and the mode changes both what the deployment does and how it can fail. Incremental mode, the default, adds and updates the resources the template declares and leaves everything else in the resource group alone. Complete mode deploys the template as the desired full state of the resource group and deletes any resource in the group that the template does not declare. The mode is a property of the deployment, not the template, and choosing it is a decision with real consequences.

The failure complete mode introduces is deletion, not a thrown error. A complete-mode deployment that omits a resource someone added out of band succeeds, and in succeeding deletes that resource. The "failure" is silent and after the fact: a resource that should still exist is gone because the template that defined the resource group's complete state did not include it. This is why running what-if before a complete-mode deployment is not optional discipline but a safeguard, because the what-if diff lists every deletion the deployment would perform, and reading that diff is the only chance to catch an unintended deletion before it executes. An engineer who treats complete mode as a safe default, the way incremental mode is safe, is one out-of-band resource away from deleting something important.

Incremental mode has its own subtlety. Because it only adds and updates, it does not delete resources the template no longer declares, so a resource group can accumulate resources from past deployments that the current template does not mention, which is harmless for correctness but can confuse a later complete-mode deployment that would then delete them. The interaction between the two modes over the life of a resource group is a source of surprises, and the prevention is consistency: decide the mode deliberately per resource group and per pipeline, and run what-if whenever complete mode is in play. The deeper treatment of the deployment modes, the dependency graph, and how ARM evaluates a deployment lives in the [Azure Resource Manager guide](/2022/05/16/azure-resource-manager-arm-explained/), which is the place to build the full model of why complete mode deletes and how the ordering graph is computed.

## The Verdict: Read the Nested Error

Every cause in this article reduces to one discipline. The top-level ARM error, `InvalidTemplate` or `DeploymentFailed`, is a generic envelope that names a stage and nothing more. The actionable cause lives in the nested provider error on the failed operation, and reading to that leaf is the difference between fixing the deployment and guessing at it. This is the read-the-nested-error rule, and it holds across every cause: a schema or expression error names itself in the leaf, a circular dependency names its members, a provider validation failure names the resource and the condition, an `AuthorizationFailed` names the action and scope, a `QuotaExceeded` names the region and family, and a parameter mismatch names the parameter and the type. The outer line never names any of these. The leaf always does.

The practical workflow that follows is short and repeatable. When a deployment fails, do not read the template first. Pull the deployment operations, filter to the failed ones, and read each leaf. Match the leaf code to its stage and cause using the error layer table, run the one confirming command that proves the condition, and only then change the thing the leaf named. For the authoring-stage causes, move the catch left by running `validate` and `what-if` in the pipeline so the failure never reaches deployment. For the runtime causes that pre-flight cannot predict, anticipate them by holding the right roles and quota headroom before the deployment that needs them. The engineer who builds this into reflex stops experiencing ARM deployment errors as mysteries and starts reading them as instructions, because that is what the nested error is: an instruction the outer envelope was hiding.

## When the Leaf Is Not Enough: The Activity Log and Correlation ID

Most failures resolve at the leaf, but a few need one more layer of detail than the provider message carries, and that detail lives in the activity log. Every deployment emits a correlation ID, a single identifier that threads together all the control-plane events ARM generated for that operation. When the leaf names a problem but not enough of it, filtering the activity log by the correlation ID assembles the full control-plane story: which identity acted, which exact action was attempted, what the provider returned, and the precise timestamp of each step.

The correlation ID is most useful for authorization and conflict diagnoses. An `AuthorizationFailed` leaf names the action and scope, but the activity log entry for that correlation ID confirms the principal that attempted it, which matters when several identities could have run the deployment or when a managed identity rather than the expected service principal turns out to be the actor. A conflict diagnosis benefits even more, because the leaf for a 409 often just says another operation is in progress, while the activity log filtered by correlation ID and the surrounding time window shows the competing operation by name, which is the thing you need to serialize against.

You retrieve the activity log for a correlation ID with the CLI, scoping it to the time window around the deployment:

```bash
az monitor activity-log list \
  --correlation-id <correlationId> \
  --start-time 2022-10-24T00:00:00Z \
  --query "[].{op:operationName.value, status:status.value, caller:caller, resource:resourceId}" \
  --output table
```

The correlation ID appears in the deployment's properties and in the portal's deployment detail view, so you copy it from the failed deployment and feed it to the query. The result is the ordered list of control-plane events, and reading it alongside the leaf usually closes any gap the provider message left. For most failures you will not need this step, because the leaf is enough, but knowing the activity log is there and how to reach it through the correlation ID means the rare failure that the leaf underspecifies does not become a dead end.

## Diagnosing a Failure From a Pipeline

A large share of ARM deployments run from a pipeline rather than a developer's terminal, and pipeline logs are where the outer-error trap catches the most people, because the pipeline task usually prints the top-level `DeploymentFailed` and stops. The log shows the generic line, the build is red, and the engineer reading the log has only the envelope, not the leaf. The fix is to make the pipeline surface the leaf, because the operations are available to the pipeline exactly as they are to a terminal.

The reliable approach is to add a step that runs after a failed deployment and lists the failed operations, so the leaf lands in the same log the engineer is already reading. In a pipeline that uses the CLI, a step conditioned to run on failure pulls the operations for the named deployment and prints the projected leaf fields, turning the red build's log from "the deployment failed" into "the storage account name is taken" or "the principal lacks role-assignment write at this scope." A deployment given an explicit name rather than an auto-generated one makes this trivial, because the failure step references the same name the deploy step used:

```bash
az deployment group create \
  --resource-group myResourceGroup \
  --name release-$(Build.BuildId) \
  --template-file azuredeploy.json \
  --parameters @azuredeploy.parameters.json
# on failure, the next step runs:
az deployment operation group list \
  --resource-group myResourceGroup \
  --name release-$(Build.BuildId) \
  --query "[?properties.provisioningState=='Failed'].properties.statusMessage.error" \
  --output json
```

Naming the deployment deterministically also helps because it makes the deployment findable later in the portal and the activity log, which matters when a failure needs the correlation-ID step. A deployment with an auto-generated name is harder to locate after the fact, especially when many deployments run in a short window.

The other pipeline-specific discipline is to fail fast at validation. A pipeline that runs `validate` on the pull request and `what-if` before the deploy converts the authoring-stage causes into pre-merge and pre-deploy gates, so the only failures that reach the deploy step are the runtime ones, which the failure step then surfaces by leaf. The result is a pipeline where a red build comes with the actionable cause in the log rather than the generic envelope, which is the entire point of the read-the-nested-error rule applied to automation: the pipeline should read the leaf for you and print it where you are already looking.

## Re-Running a Failed Deployment Safely

After diagnosing and fixing the cause, you redeploy, and a fair question is whether re-running a deployment that partially succeeded is safe. ARM resource creation is largely idempotent: deploying a template whose resources already exist in the declared state is a no-op for those resources, so a redeploy after fixing one failed resource does not duplicate or damage the resources that succeeded the first time. The resources that already exist are evaluated, found to match, and left unchanged, while the previously failed resource is attempted again with the fix in place.

The idempotency holds because ARM deployments describe desired state rather than imperative steps. A storage account that the first deployment created is described by the template as a desired resource, and the second deployment, seeing it already exists in that state, makes no change. This is why redeploying after a fix is the normal recovery, not a risk, in incremental mode. The caution is complete mode, where a redeploy is still the full desired state and will still delete anything the template does not declare, so the same what-if discipline applies to a recovery redeploy as to the original.

The exception to clean idempotency is a resource that does not update in place. Some resource properties are immutable after creation, so a deployment that changes such a property does not update the existing resource but fails or requires a replacement, depending on the provider. When a fix involves changing an immutable property on an already-created resource, the redeploy may surface a new leaf about the immutable property, and the resolution is to delete and recreate the resource or to use the provider's supported path for that change rather than expecting an in-place update. Reading the leaf on the recovery redeploy catches this, which is the same discipline once more: the leaf tells you whether the redeploy did what you expected or hit a new condition.

A partially completed deployment also leaves the resource group in an intermediate state, with some resources created and others not, and that intermediate state is worth confirming before the recovery redeploy. Listing the resource group's resources shows what the failed deployment actually created, which is occasionally surprising, because a resource can be created and then a later resource in the same deployment fails, leaving the first in place. The recovery redeploy reconciles the group to the template's desired state, but knowing what exists going in makes the what-if diff easier to read and confirms that the recovery will not leave orphaned resources behind.

## The Verification Step for Each Cause

A fix is not finished until a confirming check proves it worked, and each cause has a natural verification that closes the loop. For a template or expression error, the verification is a clean `validate` run: after correcting the expression or the schema, `validate` returns success rather than the `InvalidTemplate`, which proves the authoring problem is resolved before you spend a deployment on it. For a circular dependency, the same `validate` returns without naming a cycle, confirming the graph is now acyclic.

For an `AuthorizationFailed`, the verification is twofold: the role assignment now appears in the identity's effective assignments at the scope, and the redeploy proceeds past the resource that failed. Listing the assignment confirms the grant; the successful redeploy confirms it was the right grant at the right scope. Role-assignment changes can take a short time to propagate, so a redeploy that still fails immediately after granting the role is worth retrying after the propagation window rather than concluding the grant was wrong, a nuance the RBAC article treats in depth. For a `QuotaExceeded`, the verification is that current usage now sits below the raised limit for the region and family, which `az vm list-usage` shows, and that the redeploy places the resource that previously could not fit.

For a provider validation failure, the verification is specific to the condition the leaf named: a renamed globally unique resource passes the name-availability check, a changed SKU appears in the region's offered SKUs, a corrected network reference resolves to an existing subnet with room. For a missing provider registration, the verification is that the provider's registration state reads as registered before the redeploy. The common thread is that verification is not optional confidence but a concrete command whose output proves the condition the leaf named is no longer true, which is the same evidence-based discipline that diagnosed the failure in the first place. A fix you cannot verify with a command is a fix you are guessing at, and the whole method is built to replace guessing with reading and confirming.

## Frequently Asked Questions

### Q: What does InvalidTemplate mean in an Azure ARM deployment?

`InvalidTemplate` means Azure Resource Manager rejected the template during validation, before it created any resource, because the template document or its parameter binding is wrong. The cause is in the file: a malformed expression, a function called with the wrong arguments, a reference to a parameter or variable that does not exist, a property that fails schema validation for the declared API version, or a parameter supplied in the wrong type. Because validation runs before deployment, the resource group is untouched and nothing was created, which means you can reproduce the exact error locally by running the validate operation against the same template and parameters. Read the nested message under the `InvalidTemplate` code, because it names the specific expression, property, or parameter that broke, and that name is the fix. The error is always an authoring problem, never a permissions, quota, or capacity problem, so the search stays in the template document.

### Q: How do I read the nested error behind a DeploymentFailed message?

A `DeploymentFailed` is a generic envelope that explicitly tells you to list the deployment operations for the real cause. Run `az deployment operation group list` against the resource group and the deployment name, filter to operations whose provisioning state is Failed, and project the `statusMessage.error` fields, which carry the provider's own code and message. The error object nests: the outer code is `DeploymentFailed`, a middle layer is often `ResourceDeploymentFailure`, and the leaf at the bottom carries the actionable code such as `AuthorizationFailed`, `QuotaExceeded`, or a provider validation message. Descend through the `details` arrays until you reach the object with no further nesting, because that leaf names the failing resource and the reason. The portal shows the same structure under the resource group's Deployments blade, with a raw error JSON view that displays the whole nested object directly, which is often the fastest way to read a deeply nested leaf.

### Q: What causes a circular dependency error in an ARM template?

A circular dependency error means the dependency graph ARM builds from your `dependsOn` entries and your `reference` and `resourceId` calls contains a cycle, so there is no valid order to deploy the resources, and ARM rejects the template at validation. The cycle is usually accidental and indirect: resource A depends on B, B on C, and C back on A, formed as explicit `dependsOn` entries accumulated over time. Most of those explicit entries are redundant, because ARM already infers a dependency wherever one resource references another, so the fix is almost always to remove the redundant explicit `dependsOn` rather than to reorder anything. The nested message names the resources in the cycle, which is the thread to pull: map their `dependsOn` entries, find the loop, and delete the one that ARM would have inferred anyway. For a genuine mutual dependency, break it by splitting the deployment into stages or introducing a value as a parameter.

### Q: How do I validate an ARM template before deploying it?

Run the validate operation, which performs the same template validation ARM does at the start of a real deployment but stops before creating anything. With the CLI, `az deployment group validate` takes the same template file and parameters as a deployment and returns the same `InvalidTemplate` and nested message you would have hit at deploy time, in seconds and without touching the subscription. It catches the whole authoring-stage family: expression errors, circular dependencies, schema mismatches, and parameter binding problems. For a broader pre-flight, run `az deployment group what-if`, which validates and then computes the change set the deployment would make, showing which resources would be created, modified, or deleted. What-if is especially worth running before a complete-mode deployment, because it lists the deletions complete mode would perform. Wiring validate into the pull-request stage and what-if before the deploy converts authoring-stage failures into pre-merge and pre-deploy gates rather than deploy-time surprises.

### Q: Why does an ARM deployment fail with AuthorizationFailed when the template is valid?

Because a deployment runs under an identity, and that identity lacks a role assignment granting the specific action the deployment needs at the scope where the action is evaluated. ARM evaluates the deployment against the identity's RBAC, so a missing assignment fails the affected resource even though the template is structurally perfect. The leaf message names the action that was denied, the scope it was attempted at, and often the principal's object ID, and that action-plus-scope is the diagnosis. The most common version is a role assigned at the wrong scope, so the identity has Contributor on one resource group while the deployment targets another, or has a role on a child scope when the action evaluates at the parent. Confirm by listing the identity's role assignments at the named scope, then assign the least-privilege role that includes the denied action. A frequent variant is a deployment that creates role assignments, which needs the higher permission to write role assignments that Contributor deliberately excludes.

### Q: Why does a template expression or function fail to evaluate?

A template expression fails when a function is called incorrectly or used in a context where it cannot evaluate. The most common case is `resourceId` called with the wrong number of name segments, because a child resource type needs both the parent and child name segments while a top-level type needs one; supplying the wrong count fails evaluation. Another is referencing a parameter or variable whose name does not exactly match its declaration, since ARM treats names case-sensitively and a single character difference is a different, undeclared reference. A subtler case is using the `reference` function, which reads a resource's runtime properties, in a place ARM evaluates before deployment, such as a variable definition; `reference` only works in a resource property or an output where runtime evaluation is legal. The nested message names the function and the problem. Reproduce it with the validate operation, which evaluates expressions exactly as a real deployment does, and fix the call rather than guessing.

### Q: What does MissingSubscriptionRegistration mean during a deployment?

It means the template tried to create a resource from a resource provider that is not registered in the subscription. Azure resource providers must be registered before resources of their types can be created, and a subscription that has never used a particular service may not have its provider registered, so the first deployment that needs it fails with this code and the provider namespace named in the message. The fix is to register the provider with `az provider register --namespace <Namespace>`, wait for the registration state to read as registered, then redeploy. You can avoid the failure entirely by confirming registration ahead of the deployment with `az provider show --namespace <Namespace> --query registrationState`, and by registering the providers a subscription will use as part of its baseline provisioning. This is a setup gap rather than a template problem, so editing the resource definition does nothing; the resource body is correct, the provider behind it simply was not enabled in the subscription yet.

### Q: How is an invalid apiVersion different from an invalid resource type?

Both fail a resource, but they fail for different reasons and the messages differ. An invalid `apiVersion` means the resource type exists but does not offer the version you declared, usually because the version was copied from an old example and has since been retired, or because the version string has a typo; the fix is to declare a version the provider currently supports for that type. An invalid resource `type` means the type itself does not exist as written, from a misspelling or from a provider that is not registered, and the fix is to correct the type or register the provider. The two interact through the schema, because the properties a resource accepts can change between API versions, so a body valid under one version may be rejected under another. ARM validates the body against the schema of the declared `apiVersion`, not the latest one, so pinning a current supported version and aligning the body to its schema resolves both the version error and the schema mismatches that follow from it.

### Q: Why does my deployment delete resources I did not expect?

Because the deployment ran in complete mode, which treats the template as the full desired state of the resource group and deletes any resource the template does not declare. Unlike incremental mode, which only adds and updates and leaves everything else alone, complete mode reconciles the group to exactly what the template describes, so a resource added out of band, or one a previous template defined but the current one omits, is deleted when complete mode runs. The deletion is not an error; the deployment succeeds and removes the resource as part of reaching the declared state. The safeguard is to run what-if before any complete-mode deployment, because the what-if diff lists every deletion the deployment would perform, giving you the chance to catch an unintended one before it executes. Treat complete mode as a deliberate choice with deletion semantics, never as a drop-in safe default the way incremental mode is, and reserve it for resource groups whose full state the template genuinely owns.

### Q: Can what-if predict every reason a deployment will fail?

No, and treating it as a guarantee leads to surprises. What-if runs template validation and computes the change set the deployment would make, so it reliably catches the authoring-stage failures, the template and expression errors, the schema mismatches, many reference problems, and it surfaces unintended deletions under complete mode. What it cannot reliably predict are the runtime conditions that depend on the live state of Azure at the exact moment of deployment: a `QuotaExceeded` that occurs because the subscription crossed its limit between the prediction and the deployment, a `SkuNotAvailable` from regional capacity that changed, or some provider runtime checks that fire only at actual creation. The right model is that what-if is a strong filter that eliminates the authoring-stage failures, so that any failure surviving to the real deployment is far more likely to be a genuine runtime cause. Run what-if to shrink the failure surface, and still read the leaf when a runtime failure occurs, because the runtime causes were never what-if's to predict.

### Q: How do I find the real cause when a linked or nested template fails?

A linked or nested template is its own deployment with its own operations, so when a child fails, the parent's operations show a generic failure pointing inward while the real leaf lives in the child deployment's operations. List the child deployment's operations directly, using the child deployment's name rather than the parent's, and read the leaf there exactly as you would for any deployment. A linked template adds one failure mode of its own: the link itself can fail if the template URI is unreachable or a required SAS token is missing or expired, in which case the leaf names a retrieval failure rather than a resource, and the fix is to make the linked template reachable with valid access at deploy time. The correlation ID ties the parent and all its children together in the activity log, so when tracing through nested operations is awkward, filtering the activity log by the correlation ID shows every control-plane event across the whole deployment tree in one timeline.

### Q: Is it safe to re-run a failed ARM deployment after fixing the cause?

In incremental mode, yes, because ARM deployments describe desired state and resource creation is largely idempotent. Resources the first deployment created already exist in the declared state, so the redeploy evaluates them, finds them matching, and leaves them unchanged, while the previously failed resource is attempted again with your fix in place. There is no duplication and no damage to the resources that succeeded. The caution is complete mode, where a recovery redeploy is still the full desired state and will still delete anything the template does not declare, so run what-if on the recovery redeploy too. The other exception is a resource with an immutable property: if your fix changes a property that cannot update in place, the redeploy surfaces a new leaf about the immutable property and you resolve it by recreating the resource or using the provider's supported change path. Confirm what the failed deployment actually created by listing the resource group before redeploying, so the what-if diff is easy to read.

### Q: How do I surface the ARM error in a CI/CD pipeline log instead of the generic message?

Add a step that runs after a failed deployment and lists the failed operations, so the leaf lands in the same log you are already reading. Give the deployment an explicit, deterministic name in the deploy step, then in a step conditioned to run on failure, call `az deployment operation group list` against that same name, filter to Failed operations, and print the `statusMessage.error` object. This turns the red build's log from "at least one resource deployment operation failed" into the actual leaf, such as a taken storage account name or a denied role-assignment write at a named scope. Naming the deployment deterministically also makes it findable later in the portal and the activity log, which matters when a failure needs the correlation-ID step. Pair this with running validate on the pull request and what-if before the deploy, so the only failures reaching the deploy step are runtime ones, which the failure step then surfaces by leaf rather than envelope.

### Q: What is the difference between QuotaExceeded and SkuNotAvailable in a deployment?

They look similar at the outer level but require opposite actions, and the leaf code is what tells them apart. `QuotaExceeded` is a soft limit: the resource type exists and the region offers the SKU, but your subscription's approved allocation for that region and VM family is full, and the fix is a quota increase request, which raises the limit and lets the deployment proceed. `SkuNotAvailable`, and the related `AllocationFailed`, is a capacity or availability condition: the region or zone cannot place that SKU right now, or the SKU is not offered there at all, and a quota increase does nothing because the limit was never the problem. Confusing them leads to the wrong action, requesting an increase for a capacity problem or switching regions for a quota problem a simple increase would solve. Confirm a quota cause by reading current usage against the limit with `az vm list-usage` for the region; confirm a capacity cause by checking which SKUs the region actually offers, and choose an available SKU, region, or zone.

### Q: Why does a parameter type mismatch fail my deployment?

Because ARM binds the values you supply to the parameter declarations in the template, and a value whose type does not match the declared type fails at validation. The frequent version comes from a parameters file, where a value written as `"3"` is a JSON string while a parameter declared as `int` expects `3`; pipelines that build parameter values as interpolated text are especially prone to this, because the interpolation produces a string even when the parameter wants a number or boolean. Other versions are a value outside an `allowedValues` set, which the parameter rejects with the allowed values listed, and a required parameter with no default that received no value. The nested message names the parameter and the expected type or allowed set. Reproduce it by running validate with the exact parameters file and inline overrides the real deployment uses, and fix the value's type, choose a permitted value, or supply the missing parameter, all of which are changes to the parameter wiring rather than the resource bodies.

### Q: How do I use the correlation ID to diagnose a deployment failure?

The correlation ID is a single identifier ARM stamps on every control-plane event for a deployment, and filtering the activity log by it assembles the full story when the leaf alone is not enough. Copy the correlation ID from the failed deployment's properties or the portal's deployment detail, then run `az monitor activity-log list --correlation-id <id>` scoped to the time window around the deployment, projecting the operation, status, caller, and resource. The result is the ordered list of control-plane events, which is most useful for authorization and conflict diagnoses: it confirms which principal actually attempted a denied action when several identities could have run the deployment, and for a 409 it names the competing operation you need to serialize against. Most failures resolve at the leaf without this step, but knowing the activity log is reachable through the correlation ID means the occasional failure the provider message underspecifies does not become a dead end.

### Q: Should I assign Owner to fix an AuthorizationFailed in a deployment?

No, reaching for Owner is the wrong instinct even though it makes the immediate error disappear, because it grants far more than the deployment needs and leaves a standing over-permission that widens your blast radius. The right move is to read the action and scope from the leaf and assign the least-privilege role that includes exactly those actions at the scope where they are evaluated. If the deployment creates ordinary resources, a role scoped to those resource types and that resource group is enough. If the deployment creates role assignments, the identity needs the specific permission to write role assignments, which Contributor deliberately excludes and which a role designed for managing access grants without handing over everything Owner does. Granting the minimum that covers the denied actions keeps the identity capable of its deployments and nothing more, which is both the secure choice and the one that makes a future `AuthorizationFailed` a meaningful signal of a genuinely new requirement rather than noise from an over-broad grant.

### Q: How do I prevent ARM deployment failures from reaching production?

Move the catchable failures left and anticipate the ones you cannot catch early. Run validate on the pull request and what-if before the deploy, which converts the entire authoring-stage family, expression errors, circular dependencies, schema mismatches, and parameter binding problems, into pre-merge and pre-deploy gates. Pin and align API versions deliberately so retired versions fail predictably as a version bump rather than mysteriously. Declare `dependsOn` only for genuine ordering ARM cannot infer, which removes the circular dependency cause almost entirely. Grant the deploying identity the roles its deployments need at the right scopes during environment setup, and register the providers a subscription will use as part of its baseline, so authorization and registration failures stop appearing on first deployments. For the runtime causes pre-flight cannot predict, quota and capacity, track headroom for the regions and families a workload uses and request increases ahead of the deployment that would cross a limit. The result is a pipeline where most failures are caught at review and the rest arrive with a readable leaf.

### Q: Why does my copy loop fail in an ARM template?

A copy loop, the `copy` property that creates multiple instances from a count and an index, fails in ways a single resource does not. The count must resolve to an integer at template-expansion time, so a count derived from a `reference` to a not-yet-deployed resource cannot evaluate, because `reference` is a runtime function while the count is needed earlier; drive the count from a parameter or an expansion-time value instead. The loop also fails when its iterations collide, most commonly when the name expression does not incorporate `copyIndex`, so every iteration produces the same name and the provider rejects the duplicates; include `copyIndex` in the name so each instance is unique. The leaf names either the unresolved count or the duplicate resource, pointing straight at the loop. Read it, fix the count source or the name expression, and validate to confirm the loop now expands cleanly before deploying, since a copy-loop error is an authoring-stage failure that validate reproduces without touching the subscription.

### Q: My deployment succeeded partially and left some resources created. How do I recover?

A partially completed incremental deployment leaves the resource group in an intermediate state, with the resources that succeeded created and the ones after the failure not, and the recovery is to fix the cause and redeploy, because the redeploy reconciles the group to the template's desired state without disturbing the resources that already match it. Before redeploying, list the resource group's resources to confirm what the failed deployment actually created, which is occasionally surprising because a resource can be created just before a later one fails, and knowing the starting state makes the what-if diff easy to read. Run what-if on the recovery redeploy to confirm it will create only the missing resources and not delete anything, especially if the deployment uses complete mode. If your fix changed an immutable property on an already-created resource, the redeploy will surface a new leaf about it, and you resolve that by recreating the resource through the provider's supported path. Idempotency makes the redeploy safe in incremental mode, so recovery is normal rather than risky.
