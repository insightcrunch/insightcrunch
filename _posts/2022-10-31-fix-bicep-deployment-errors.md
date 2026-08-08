---
layout: post
title: "Fix Bicep Deployment Errors"
page_title: "Fix Bicep Deployment Errors: Compile-Time vs Deploy-Time Failures, BCP Codes, Module Resolution, and targetScope Explained"
date: 2022-10-31
categories: ["Technology"]
tags: ["Azure", "Bicep", "Troubleshooting", "DevOps", "ARM", "Cloud Computing"]
excerpt: "Bicep deployment errors split into compile-time and deploy-time stages. Learn to read each, confirm the cause, and apply the tested fix at the right stage."
image: "/assets/images/blog/blog-06.webp"
reading_time: 60
author: "marcus-hall"
last_updated: 2022-10-31
lang: en
---
When a Bicep deployment fails, the single most useful thing you can do before touching a line of code is decide which of two worlds the failure lives in. Bicep deployment errors fall into exactly two stages, and they look deceptively similar in a terminal scrollback. A compile-time error is the Bicep toolchain refusing to turn your `.bicep` file into a valid ARM template: a linter complaint, a type mismatch, a required property you left out, a module path that does not resolve, or a `targetScope` that does not match the command you ran. A deploy-time error is something else entirely. By that point the compile has already succeeded, an ARM template exists, and Azure Resource Manager is rejecting the request the same way it would reject any ARM deployment: an `AuthorizationFailed` because the deploying identity lacks a role, a `QuotaExceeded` because the region is out of vCPUs, a `Conflict` because another operation holds the resource. Mistaking one stage for the other is the most common reason engineers spend an afternoon rewriting syntax that was never wrong.

![Fixing Bicep deployment errors across compile-time and deploy-time stages - Insight Crunch](/assets/images/blog/blog-06.webp)

This article is built on one organizing idea that you can carry into every red deployment you ever read. Bicep is a transpiler. It compiles your authored file down to an ARM template in JSON, and then it hands that JSON to the same Resource Manager control plane that a hand-written ARM template would hit. Once you internalize that, the entire error surface separates cleanly. Anything the Bicep CLI emits with a `BCP` code, anything the linter flags, anything about modules and types and scope, happens before a single byte reaches Azure. Anything ARM emits, the provider validation, the role checks, the quota math, the in-progress conflicts, happens after the compile finished and is identical to the errors a JSON author would see. Knowing which side of that line you are on tells you which tool to reach for, which command confirms the cause, and whether the fix belongs in your editor or in your subscription.

## How to read a Bicep failure and find the stage

The first diagnostic move is never to read the error text for meaning. It is to read the error text for origin. A `BCP` prefix, a file-and-line-number reference into your `.bicep` source, or a message from the Bicep linter all mean the failure happened during transpilation and your code never left the machine. An ARM error code (anything that looks like `AuthorizationFailed`, `QuotaExceeded`, `Conflict`, `InvalidTemplate`, `SkuNotAvailable`, or a resource-provider message naming a specific resource type) means the compile succeeded and Resource Manager is the one objecting. The two stages even surface through different commands, which is the cleanest way to force the distinction.

To isolate the compile stage with certainty, run the build without deploying:

```bash
# Compile main.bicep to ARM JSON without touching Azure.
# If this fails, the problem is 100% compile-time.
az bicep build --file main.bicep --outfile main.json

# Or with the standalone CLI:
bicep build main.bicep
```

If `az bicep build` returns errors, you have a compile-time problem and there is no point looking at your subscription, your roles, or your quota. The template that ARM would have rejected does not even exist yet. If `az bicep build` succeeds and produces a JSON file, but `az deployment group create` still fails, the problem is deploy-time, and the actionable detail is in the ARM response, not in your Bicep.

### Why does my Bicep deployment fail even though the syntax looks correct?

Because syntax correctness is only the compile stage. A file can transpile to flawless ARM and still be rejected by Resource Manager for a missing role, an exhausted quota, a name collision, or a provider validation rule. A clean `az bicep build` proves the compile passed and points you to the deploy stage.

When you deploy through the Azure CLI, the command itself fuses both stages into one invocation, which is exactly what hides the boundary:

```bash
az deployment group create \
  --resource-group rg-app-prod \
  --template-file main.bicep \
  --parameters main.bicepparam
```

That single command compiles `main.bicep` in memory, then submits the resulting template to ARM. When it fails, the CLI does not always make it obvious which half failed. The discipline of running `az bicep build` first, as its own step, removes the ambiguity for free. If the build is clean, every remaining error is an ARM error, and you read it the way you would read any deployment failure: by drilling into the deployment operations to find the resource and the provider message that actually failed.

```bash
# After a deploy-time failure, list the per-resource operations
# to find which resource failed and why.
az deployment operation group list \
  --resource-group rg-app-prod \
  --name main \
  --query "[?properties.provisioningState=='Failed'].{resource:properties.targetResource.id, code:properties.statusMessage.error.code, message:properties.statusMessage.error.message}" \
  -o jsonc
```

The `statusMessage.error.code` field in those operations is the single most valuable string in a deploy-time failure. It is the provider's own verdict, and it names the real cause: `RoleAssignmentUpdateNotPermitted`, `QuotaExceeded`, `SkuNotAvailable`, `InvalidResourceReference`, and so on. Everything downstream of reading that code is mechanical.

## The compile-time errors: what the Bicep toolchain rejects

Compile-time errors all share one trait. They are deterministic and reproducible offline. The same file produces the same `BCP` error on every machine, with no network, no credentials, and no subscription state involved. That property is your friend, because it means you can fix and re-verify in a tight loop using `az bicep build` alone, never spending a deployment attempt to learn whether a change worked. The compile stage breaks down into a handful of recurring families: linter findings, type and required-property errors, module resolution failures, `targetScope` mismatches, and the awkward output of decompiling an existing ARM template into Bicep.

### What do Bicep compile and linter errors actually mean?

A compile error is the transpiler refusing to emit ARM because your source is invalid: a misspelled property, a wrong type, an unresolved symbol. A linter finding is a warning or error about a valid but risky pattern, governed by `bicepconfig.json`. Both surface before deployment, and both are fixed entirely in your editor.

The Bicep CLI ships with a built-in linter that runs automatically during a build, and its behavior is configured by a `bicepconfig.json` file placed in your project. The linter is the cheapest defense you have against deploy-time surprises, because several of its rules exist precisely to catch patterns that compile cleanly but fail or misbehave once ARM evaluates them. A typical configuration tightens the default rule set and promotes the most dangerous warnings to hard errors so a continuous integration build fails fast:

```json
{
  "analyzers": {
    "core": {
      "enabled": true,
      "rules": {
        "no-hardcoded-env-urls": { "level": "error" },
        "no-unused-params": { "level": "warning" },
        "no-unused-vars": { "level": "warning" },
        "secure-parameter-default": { "level": "error" },
        "prefer-interpolation": { "level": "warning" },
        "explicit-values-for-loc-params": { "level": "warning" }
      }
    }
  }
}
```

When the linter reports something, the message names the rule and the line. The fix is to satisfy the rule, not to suppress it, unless you have a deliberate reason. A rule like `secure-parameter-default` set to `error` will stop a build cold if you give a parameter marked `@secure()` a hardcoded default, which is exactly the kind of mistake you want caught in the editor rather than discovered in a committed template. Treating linter output as advisory noise is one of the named misdiagnoses this article exists to correct, because a warning you ignore at compile time frequently becomes a failure at deploy time once the underlying provider enforces the same constraint.

To run the linter explicitly and see every finding without producing output, point the build at the file and read what comes back:

```bash
# The build runs the linter; warnings and errors print to stderr.
az bicep build --file main.bicep --stdout > /dev/null
```

### How do I fix a Bicep type or required-property error?

Read the `BCP` message: it names the property and the expected type. A missing required property means the resource type demands a value you did not supply; a type error means you passed a string where an int or object was expected. Both are fixed by aligning your source with the resource type's schema, which the Bicep extension surfaces through IntelliSense.

Type and required-property errors are the most common compile failures, and they are also the ones the Bicep language server prevents in real time if you have the editor extension installed. A required-property error reads, in essence, that a resource declaration is missing a property the type defines as mandatory. Consider a storage account that omits the SKU:

```bicep
// This will NOT compile: 'sku' and 'kind' are required.
resource sa 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'stappdata${uniqueString(resourceGroup().id)}'
  location: resourceGroup().location
  // missing: sku, kind
}
```

The Bicep CLI rejects this with a message that the type requires `sku` and `kind`. The fix is to supply them with the correct shape, which the schema for that API version dictates:

```bicep
resource sa 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'stappdata${uniqueString(resourceGroup().id)}'
  location: resourceGroup().location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}
```

A type error is its sibling: you supplied a value of the wrong shape, such as a string literal where the schema expects one of a fixed set of allowed values, or a flat value where an object is required. The transpiler names the offending property and the expected type. Because Bicep carries full type information for each resource and API version, the editor will often flag these before you ever save, and `az bicep build` will reproduce them deterministically in a pipeline. The one subtlety worth naming is the API version itself. The required properties and allowed values for `Microsoft.Storage/storageAccounts` differ between API versions, so a property that was optional in an older version can become required in a newer one. When a type error appears after you bump an API version, the schema change is the cause, and the fix is to read the schema for the version you now target rather than the one you remembered.

### Why can Bicep not resolve a module?

A module reference fails when the path or registry coordinate does not point to something Bicep can load: a local file at the wrong relative path, a registry artifact (`br:`) that was never published or that you lack pull rights to, or a template spec (`ts:`) at a version that does not exist. The compiler reports the unresolved reference; the fix is to correct the coordinate or publish the missing artifact.

Module resolution is where compile-time errors get the most interesting, because Bicep supports three distinct ways to reference a module and each fails differently. A local module is a relative file path. A registry module uses the `br:` scheme and lives in an Azure Container Registry. A template spec uses the `ts:` scheme and lives as a resource in a subscription. A local-path failure is the simplest: the relative path is wrong, or the file was moved or renamed, and the compiler cannot find it on disk.

```bicep
// Local module by relative path. If ./modules/storage.bicep
// does not exist at this path, compilation fails immediately.
module storage './modules/storage.bicep' = {
  name: 'storageDeploy'
  params: {
    storageAccountName: storageName
    location: location
  }
}
```

A registry reference is more involved because resolution requires both that the artifact exists and that your identity can pull it. The coordinate names a registry, a repository path, and a tag:

```bicep
// Registry module. Resolution requires the artifact to be
// published AND your identity to have AcrPull on the registry.
module network 'br:contosoregistry.azurecr.io/bicep/modules/network:v1.2.0' = {
  name: 'networkDeploy'
  params: {
    vnetName: 'vnet-app'
    location: location
  }
}
```

If `contosoregistry.azurecr.io/bicep/modules/network:v1.2.0` was never published, or the tag is wrong, Bicep cannot restore it and the build fails at restore time. If the artifact exists but your identity lacks `AcrPull` on the registry, you get an authorization failure during restore that masquerades as a compile problem because it surfaces from the Bicep CLI. The distinction matters: the first is fixed by publishing or correcting the tag, the second by granting the role. To publish a module to a registry so the reference resolves, you build and push it:

```bash
# Publish a module to an ACR-backed Bicep registry.
az bicep publish \
  --file ./modules/network.bicep \
  --target 'br:contosoregistry.azurecr.io/bicep/modules/network:v1.2.0'
```

A template spec reference behaves like the registry case but the artifact is an Azure resource rather than an OCI artifact. The coordinate embeds a subscription, resource group, spec name, and version:

```bicep
// Template spec module. Resolution requires the spec and the
// exact version to exist, and Reader access to the spec resource.
module shared 'ts:00000000-0000-0000-0000-000000000000/rg-shared/landingZone:1.0.0' = {
  name: 'landingZoneDeploy'
  params: {
    environment: 'prod'
  }
}
```

When a template spec reference fails, the usual cause is a version that was never created, because template spec versions are immutable and a typo in the version string points at nothing. Confirm the spec and its versions exist before assuming the Bicep is wrong:

```bash
# Confirm the template spec and its versions exist.
az ts show --name landingZone --resource-group rg-shared --query "id"
az ts list --resource-group rg-shared -o table
```

The single rule that covers all three module forms is that a module reference is a coordinate, and a coordinate either resolves to a real, reachable artifact or it does not. The compiler is not guessing at your intent; it is trying to load a specific thing from a specific place, and the fix is always either to make that thing exist, correct the coordinate that points at it, or grant the access needed to read it.

### Why does a Bicep targetScope cause an error?

`targetScope` declares the level a file deploys at: `resourceGroup` (the default), `subscription`, `managementGroup`, or `tenant`. The error appears when the scope in the file disagrees with the deployment command. A file with `targetScope = 'subscription'` must be deployed with `az deployment sub create`, not `az deployment group create`, and a resource-group-scoped file cannot declare subscription-level resources.

The `targetScope` mismatch is a compile-and-command coordination error, and it produces some of the most confusing messages because the file looks internally consistent while being wrong for how you invoked it. Every Bicep file has an implicit or explicit scope. Without a `targetScope` declaration, the file is resource-group scoped, which is why most tutorials never mention it. The moment you need to create something that lives above a resource group, a subscription-level policy assignment, a resource group itself, a role assignment at subscription scope, you must declare the scope and deploy with the matching command.

```bicep
// Subscription-scoped file: creates a resource group and
// deploys a module into it.
targetScope = 'subscription'

param location string = 'eastus'

resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: 'rg-app-prod'
  location: location
}

module app './app.bicep' = {
  name: 'appDeploy'
  scope: rg
  params: {
    location: location
  }
}
```

This file is valid, but it will fail if you deploy it with the resource-group command, because that command expects a resource-group-scoped template. The matching invocation is the subscription-level command:

```bash
# Correct command for a subscription-scoped file.
az deployment sub create \
  --location eastus \
  --template-file main.bicep

# WRONG for the file above; produces a scope mismatch error.
# az deployment group create --resource-group rg-x --template-file main.bicep
```

The inverse mistake is declaring a subscription-level resource type inside a resource-group-scoped file, which the compiler rejects because the resource cannot exist at that scope. The mental model that prevents both is that the scope is a property of the deployment, the file declares the scope it expects, and the command must agree with the file. When they disagree, the error is telling you to change one of the two so they match, not to rewrite the resources.

### Does decompiling ARM to Bicep cause errors?

Often, yes. `az bicep decompile` is a best-effort translation, not a guaranteed-clean conversion. It can emit Bicep with warnings, awkward names, lost type information, or constructs that compile to ARM that differs subtly from the original. Treat decompiled output as a draft to review and clean up, never as finished code.

Decompilation is a genuine source of compile-time errors and warnings that catch people off guard, because the expectation is that a tool which produced ARM from Bicep can reverse the process cleanly. It cannot, and Microsoft documents this explicitly: decompilation is a starting point. The reason is structural. ARM JSON loses information that Bicep expresses more richly, and some ARM patterns have no idiomatic Bicep equivalent, so the decompiler approximates. The result frequently includes generated symbolic names that are not human-friendly, warnings about constructs it could not fully translate, and occasionally outright errors where the source JSON used a pattern the decompiler mishandled.

```bash
# Decompile an existing ARM template to Bicep.
# Expect warnings; review every one before trusting the output.
az bicep decompile --file azuredeploy.json
```

After decompiling, the disciplined workflow is to immediately run `az bicep build` on the output and read every warning, then deploy the resulting JSON through `what-if` against a non-production scope to confirm the decompiled Bicep produces the same resources as the original ARM. The named misdiagnosis here is treating decompiled Bicep as authoritative and then debugging a deployment that diverges from the original template, when the divergence was introduced by the decompiler and could have been caught by comparing the rebuilt JSON against the source.

## The deploy-time errors: what Resource Manager rejects

Everything past a clean `az bicep build` is the deploy stage, and here Bicep stops being relevant. The template has compiled, ARM has received it, and the failures are the same ones a hand-authored JSON template would hit. This is the half engineers most often misattribute, because the failure surfaces through the same `az deployment group create` command they used to compile, so it feels like a Bicep problem when it is an Azure problem. The cure is the deployment-operations read shown earlier: pull the per-resource operations, find the failed one, and read its provider error code. Four families account for the overwhelming majority of deploy-time failures: authorization, quota, conflict, and provider validation.

### Why does a Bicep deployment fail with AuthorizationFailed?

Because the identity running the deployment lacks an Azure RBAC role with the action the deployment needs, at the scope it targets. ARM evaluates every operation against the deploying principal's effective permissions. A compile-clean template that creates a role assignment, for instance, fails unless the principal holds `Microsoft.Authorization/roleAssignments/write`, typically via Owner or User Access Administrator.

Authorization is the deploy-time failure most often misread as a code problem, and the misreading wastes the most time. The deployment runs under an identity: your user account, a service principal in a pipeline, or a managed identity. ARM checks that identity's effective role assignments for the specific action each resource operation requires, at the specific scope. When the identity is short a role, the operation returns `AuthorizationFailed`, and the message names the action and the scope it was denied. The fix is never in the Bicep. It is a role assignment.

```bash
# Read the failed operation to see the denied action and scope.
az deployment operation group list \
  --resource-group rg-app-prod \
  --name main \
  --query "[?properties.statusMessage.error.code=='AuthorizationFailed'].properties.statusMessage.error.message" \
  -o tsv
```

A classic example is a template that, beyond creating infrastructure, also assigns a role to a managed identity. Creating a role assignment requires elevated rights, so a deployment principal that can happily create storage accounts and virtual networks will still fail the moment it tries to write a role assignment:

```bicep
// This resource needs Microsoft.Authorization/roleAssignments/write.
// A principal with Contributor can deploy the storage account but
// will get AuthorizationFailed on this assignment.
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(sa.id, principalId, 'Storage Blob Data Reader')
  scope: sa
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1')
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}
```

To confirm the cause rather than guess at it, check the deploying identity's effective role assignments at the target scope:

```bash
# What roles does the deploying service principal actually have?
az role assignment list \
  --assignee <appId-or-objectId> \
  --scope /subscriptions/<subId>/resourceGroups/rg-app-prod \
  --include-inherited \
  -o table
```

Two subtleties trip people up even after they accept that authorization is the cause. The first is propagation delay: a freshly created role assignment is not always effective instantly, so a deployment that runs seconds after the grant can still see the old permission set and fail. The cure is to wait and retry, not to re-grant. The second is the control-plane versus data-plane distinction, which the related RBAC troubleshooting covers in depth: a control-plane role like Contributor lets you manage a resource but does not necessarily grant data-plane access to its contents, so a deployment step that touches data, not just the resource, can fail authorization even when the resource itself was created successfully.

### Can a quota error surface through a Bicep deployment?

Yes, and it looks like a deployment failure while being a subscription-limits problem. Compute quota is scoped per subscription, per region, and per VM family. A template that requests more vCPUs than the regional family quota allows fails with `QuotaExceeded`, regardless of how clean the Bicep is. The fix is a quota increase or a smaller request, never a syntax change.

Quota is the deploy-time failure that most cleanly proves the compile-then-deploy rule, because nothing about your template is wrong and yet it cannot deploy. Azure caps how many vCPUs a subscription can allocate, and the cap is granular: it applies per region and per VM family, so a subscription with plenty of headroom in one region or family can be exhausted in another. A Bicep file that declares a virtual machine scale set with twenty instances of a large SKU compiles perfectly and then fails at deploy because the regional family quota for that SKU is lower than the request.

```bash
# Read the failed operation: a quota error names the limit.
az deployment operation group list \
  --resource-group rg-app-prod \
  --name main \
  --query "[?contains(properties.statusMessage.error.code, 'Quota')].properties.statusMessage.error.message" \
  -o tsv

# Check current vCPU usage and limits for a region.
az vm list-usage --location eastus -o table
```

The important diagnostic discipline is distinguishing a quota error, which is a soft limit you can raise, from a capacity error such as `SkuNotAvailable` or `AllocationFailed`, which means the region physically lacks capacity for that SKU right now and no quota increase will help. The dedicated quota troubleshooting walks through that distinction and the request process; for the purpose of a Bicep failure, the point is simply that the template is innocent and the resolution lives in the subscription, through a quota increase request or by targeting a region or SKU with available headroom.

### What causes a Conflict error on a Bicep deployment?

A `Conflict` (HTTP 409) means the operation collides with the current state or another in-progress operation: two deployments touching the same resource, a resource still in a transitioning provisioning state, a read-only or delete resource lock, or a name collision. Retrying into the same race repeats the failure. The fix is to serialize the operations or remove the blocking lock.

Conflicts are state-collision errors, and they are the family where a retry is most tempting and least effective. When two deployments try to modify the same resource at once, or a single resource is still mid-provisioning when a second operation arrives, ARM returns a 409 rather than corrupting the resource. A resource lock produces the same family of failure: a `ReadOnly` lock blocks writes and a `CanNotDelete` lock blocks deletes, so a deployment that would update or remove a locked resource is rejected. The message often reads that another operation is in progress, which points directly at serialization as the fix.

```bash
# Is there a lock blocking the operation?
az lock list --resource-group rg-app-prod -o table

# Read the activity log to find the competing operation.
az monitor activity-log list \
  --resource-group rg-app-prod \
  --offset 1h \
  --query "[?status.value=='Failed'].{op:operationName.value, status:status.value, time:eventTimestamp}" \
  -o table
```

The conflict troubleshooting sibling covers the full set of causes, but the Bicep-specific lesson is that a deployment failing with a conflict is rarely a template defect. It is a timing or locking issue, and the remedy is to stop running deployments that race each other against shared resources, respect the locks that are protecting production, and let an in-progress operation finish before launching the next one. Serializing through a pipeline that deploys one change at a time eliminates the most common version of this entirely.

### Why does a deploy-time provider validation error look like a template problem?

Because the resource provider, not Bicep, validates business rules that the type system cannot express: a name that violates a uniqueness or naming constraint, a property combination the provider forbids, a referenced resource that does not exist, or a region that does not offer the requested feature. The template compiles because it is type-valid; it fails at deploy because it is provider-invalid.

Provider validation is the deploy-time family that most resembles a compile error and is most often confused with one. The Bicep type system knows the shape of a resource, the properties it has and their types, but it does not know the runtime business rules each resource provider enforces. A storage account name must be globally unique and lowercase alphanumeric; the type system accepts any string, so an invalid name compiles and then fails at deploy when the Storage provider rejects it. A reference to a resource that does not exist, an `InvalidResourceReference`, compiles because the expression is type-valid, and fails at deploy because the target is not there. A feature requested in a region that does not offer it fails the same way.

```bicep
// Type-valid but provider-invalid: storage names must be
// 3 to 24 chars, lowercase letters and digits only, globally unique.
resource badName 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'My_App_Storage_2022'  // illegal characters; compiles, fails at deploy
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
}
```

The way to catch provider validation before spending a real deployment is the `what-if` and `validate` operations, which submit the template to ARM for a preview and a validation pass without provisioning anything. They run far enough into the provider path to surface many validation errors that a pure compile cannot:

```bash
# Preview the changes and surface many provider errors pre-deploy.
az deployment group what-if \
  --resource-group rg-app-prod \
  --template-file main.bicep \
  --parameters main.bicepparam

# Validate without deploying.
az deployment group validate \
  --resource-group rg-app-prod \
  --template-file main.bicep \
  --parameters main.bicepparam
```

The discipline that prevents an entire class of provider-validation failures is to run `what-if` before every deployment to a scope that matters. It costs nothing, it changes nothing, and it converts a category of deploy-time failures into pre-deploy findings you fix in the editor.

## The Insight Crunch Bicep error stage table

The whole diagnosis collapses into one lookup once you have the table that maps every common failure to its stage and its fix. This is the findable artifact for this article: print it, pin it next to your editor, and use it to route any red deployment in seconds. Each row names the symptom, the stage it belongs to, the command that confirms it, and where the fix lives.

| Symptom or error | Stage | Confirm with | Where the fix lives |
| --- | --- | --- | --- |
| `BCP` code, file and line reference | Compile-time | `az bicep build --file main.bicep` | Your editor: correct the source |
| Linter warning or error | Compile-time | build output, `bicepconfig.json` | Your editor: satisfy the rule |
| Missing required property | Compile-time | `az bicep build` | Add the property per the type schema |
| Type mismatch on a property | Compile-time | `az bicep build` | Align value to the expected type |
| Local module path not found | Compile-time | `az bicep build` | Correct the relative path |
| `br:` registry module not found | Compile-time (restore) | `az bicep build`, `az acr repository show` | Publish the artifact or fix the tag |
| `br:` registry pull denied | Compile-time (restore) | `az role assignment list` on the registry | Grant `AcrPull` to the identity |
| `ts:` template spec version missing | Compile-time (restore) | `az ts list`, `az ts show` | Create the version or fix the coordinate |
| `targetScope` mismatch | Compile-time | the deploy command you ran | Match command to scope, or change scope |
| Decompiled Bicep warnings or errors | Compile-time | `az bicep build` on decompiled output | Review and clean the decompiled draft |
| `AuthorizationFailed` | Deploy-time | `az deployment operation group list` | A role assignment, not the template |
| `QuotaExceeded` | Deploy-time | `az vm list-usage` | A quota increase or smaller request |
| `SkuNotAvailable`, `AllocationFailed` | Deploy-time | the operation error message | A different region or SKU |
| `Conflict` (409) | Deploy-time | `az lock list`, activity log | Serialize, or remove the lock |
| Provider validation (name, reference) | Deploy-time | `az deployment group what-if` | Fix the value the provider rejects |

The namable rule that the table encodes is the compile-then-deploy rule for Bicep: every Bicep failure is either a compile-time error, which the toolchain throws before anything reaches Azure and which you reproduce offline with `az bicep build`, or a deploy-time error, which Resource Manager throws against the ARM your file compiled to and which you read from the deployment operations. Knowing which stage failed is the whole diagnosis, because it tells you whether the fix belongs in your editor or in your subscription, and it stops you from rewriting correct syntax to chase an authorization or quota problem that no edit will ever solve.

## A worked example: one failure, read end to end

Walking a single failure from red to resolved shows the rule in motion. Suppose a pipeline deploys a `main.bicep` that creates a storage account, assigns a managed identity the Storage Blob Data Reader role on it, and pulls a shared networking module from a registry. The deployment fails, and the pipeline log shows a wall of text. The temptation is to open `main.bicep` and start reading. The discipline is to ask which stage failed first.

The first move is to compile in isolation:

```bash
az bicep build --file main.bicep --outfile /tmp/main.json && echo "COMPILE OK"
```

If this prints an error instead of `COMPILE OK`, the failure is compile-time and you read the `BCP` code. Suppose it fails on the registry module with a restore error naming `contosoregistry.azurecr.io/bicep/modules/network:v1.2.0`. That is the module-resolution family: either the artifact was never published at that tag, or the pipeline's identity lacks `AcrPull`. You confirm which:

```bash
# Does the artifact exist?
az acr repository show-tags \
  --name contosoregistry \
  --repository bicep/modules/network -o tsv

# Does the pipeline identity have pull rights?
az role assignment list \
  --assignee <pipeline-sp-appId> \
  --scope $(az acr show --name contosoregistry --query id -o tsv) \
  -o table
```

If the tag is absent, you publish it. If the tag exists but no `AcrPull` shows for the identity, you grant the role. Either way the fix is at the compile stage and you re-run the build to verify before spending another deployment.

Now suppose instead the build prints `COMPILE OK`. The registry module resolved, the types are valid, the scope matches. Every remaining failure is deploy-time, so you read the operations:

```bash
az deployment operation group list \
  --resource-group rg-app-prod \
  --name main \
  --query "[?properties.provisioningState=='Failed'].{resource:properties.targetResource.resourceType, code:properties.statusMessage.error.code}" \
  -o table
```

If the failed operation is the role assignment with code `AuthorizationFailed`, the pipeline identity can create the storage account, it has Contributor, but it cannot write a role assignment because that needs Owner or User Access Administrator. The fix is to grant the pipeline identity the rights to manage role assignments at the target scope, or to move the role assignment into a separate, more privileged deployment. No edit to `main.bicep` changes the outcome, because the Bicep was correct the entire time. This is the compile-then-deploy rule paying off: ten minutes of reading the right signal replaces an afternoon of editing syntax that was never the problem. The deeper authorization mechanics, propagation timing, scope reading, and the control-plane versus data-plane split, are exactly what the [Resource Manager control plane](/2022/05/16/azure-resource-manager-arm-explained/) and the [ARM deployment error walkthrough](/2022/10/24/fix-arm-template-deployment-errors/) cover, since a Bicep deploy-time error is an ARM error wearing a Bicep wrapper.

## Prevention: stop the recurrence before it ships

Diagnosis is the cure for a failure you already have. Prevention is how you stop the same failure from reaching a pipeline again, and the levers are concrete. The first is to make the compile stage a gate. Run `az bicep build` in continuous integration on every change, with the linter configured strictly in `bicepconfig.json`, so a type error, an unresolved module, or a scope mismatch fails the build before review rather than after a deployment attempt. The compile stage is fast, offline, and deterministic, which makes it the ideal place to catch the entire compile-time family for free.

The second lever is to make `what-if` mandatory before any deployment to a scope that matters. The preview submits the template far enough into the provider path to surface many provider-validation errors, and it shows exactly what the deployment would change, which catches both validation failures and the more dangerous case of a template that compiles, validates, and then changes something you did not intend.

```bash
# Gate pattern: build, then preview, then deploy.
az bicep build --file main.bicep || exit 1
az deployment group what-if \
  --resource-group rg-app-prod \
  --template-file main.bicep \
  --parameters main.bicepparam
# human approval here, then:
az deployment group create \
  --resource-group rg-app-prod \
  --template-file main.bicep \
  --parameters main.bicepparam
```

The third lever is to design out the deploy-time families you can. Authorization failures shrink when the deploying identity has a stable, least-privilege role set defined as code and granted ahead of time rather than scrambled together after a failure. Conflicts shrink when a single pipeline serializes deployments to shared resources rather than letting parallel jobs race. Quota failures shrink when capacity planning checks `az vm list-usage` before a large rollout rather than discovering the ceiling mid-deploy. None of these live in the Bicep, which is the recurring lesson: prevention for deploy-time errors is an operational practice, while prevention for compile-time errors is a build gate.

The fourth lever is modular, reviewed authoring, which is the practice the [complete Bicep authoring guide](/2025/01/27/azure-bicep-complete-guide/) develops in full. A monolithic file is harder to reason about, harder to lint cleanly, and more likely to mix scopes in ways that produce `targetScope` confusion. Composing a deployment from small, single-purpose modules, each one buildable and testable on its own, turns a large opaque failure into a small localized one and makes the compile-then-deploy split easier to apply because each module's stage is obvious.

## Parameter and .bicepparam errors that masquerade as template bugs

Parameters are a frequent source of failures that present as deployment errors while really being input errors, and they split across both stages in a way worth naming explicitly. A parameter with the wrong type, a missing required parameter with no default, or an allowed-value violation is a compile-or-validate failure that the toolchain catches early. A parameter that is type-valid but semantically wrong, a region string that the provider does not recognize, a SKU name that does not exist, passes compile and fails at deploy through provider validation.

The modern `.bicepparam` format is itself compiled, so a mistake in a parameter file can fail at the compile stage rather than at deploy. A `.bicepparam` file references its template with a `using` statement and assigns each parameter, and the Bicep CLI type-checks the assignments against the template's parameter declarations:

```bicep
// main.bicepparam
using './main.bicep'

param environment = 'prod'
param location = 'eastus'
param instanceCount = 3
```

If `instanceCount` is declared `int` in `main.bicep` and you assign a string here, the parameter file fails to compile, which is a compile-time error even though it lives in the parameter file rather than the template. If you omit a parameter that has no default, the deployment fails at submission because a required input is missing. The diagnostic move is the same as always: run the build, and if the build is clean, the parameter problem is semantic and surfaces at deploy through the provider that rejects the value.

A subtle parameter failure is the `@allowed()` decorator, which constrains a parameter to a fixed set of values. A value outside the allowed set is rejected before deployment, which is the intended behavior, but it can confuse someone who expected the value to be accepted:

```bicep
@allowed([ 'dev', 'staging', 'prod' ])
param environment string

// Passing environment='production' fails validation: not in the allowed set.
```

When a parameter-related error appears, the question to ask is whether the value is the wrong type or shape, which the compile or the parameter-file build catches, or the wrong value for a real provider constraint, which deploy-time validation catches. The stage tells you whether to fix the type in the editor or the value against the provider's rules.

## Loops, conditions, and existing references: compile errors with a runtime echo

Bicep's expressive constructs, loops with `for`, conditional resources with `if`, and references to pre-existing resources with the `existing` keyword, introduce their own compile-time error patterns, and a few of them have a deploy-time echo that is easy to misread. A loop that produces duplicate resource names compiles but fails at deploy because two resources cannot share a name within a deployment. A conditional resource referenced unconditionally elsewhere can produce a compile error because Bicep cannot guarantee the resource exists. An `existing` reference to a resource that is not actually there compiles, because the reference is type-valid, and fails at deploy with a resource-not-found provider error.

```bicep
// A loop over an array. If two array entries yield the same name,
// the template compiles but the deployment fails on a name collision.
param storageNames array = [ 'stappa', 'stappb', 'stappa' ]  // duplicate

resource stores 'Microsoft.Storage/storageAccounts@2023-01-01' = [for n in storageNames: {
  name: '${n}${uniqueString(resourceGroup().id)}'
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
}]
```

The `existing` keyword is the construct most likely to produce a deploy-time surprise, because it tells Bicep to reference a resource it should not create, and the compiler trusts you that the resource exists. If it does not, the reference resolves at compile time but the deployment fails when ARM cannot find the target:

```bicep
// References a key vault that must already exist. Compiles regardless;
// fails at deploy with a not-found error if the vault is absent.
resource kv 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: 'kv-app-prod'
}
```

The lesson these constructs reinforce is that the compiler validates shape and type, not the existence of external state. A loop, a condition, or an `existing` reference can be perfectly type-valid and still fail at deploy because the runtime reality, a duplicate name, an absent resource, a condition that did not hold, does not match what the type system could check. When one of these fails at deploy, the fix is to reconcile the template with the actual state of the world, not to rewrite the construct.

## Reading the failure in the portal when the CLI is not enough

The Azure CLI is the fastest path to the failed operation, but the portal sometimes shows the chain of nested deployments more clearly, especially when modules nest several levels deep and the failing resource is buried in a child deployment. Every Bicep module becomes a nested deployment in ARM, and a failure three modules deep can be hard to trace from a flat CLI query. In the portal, the deployment blade on the resource group lists each deployment and its nested children, and drilling into the failed leaf shows the same provider error code the CLI returns, often with a clearer parent-child path.

```bash
# List nested deployments to trace a failure through modules.
az deployment group list \
  --resource-group rg-app-prod \
  --query "[].{name:name, state:properties.provisioningState, timestamp:properties.timestamp}" \
  -o table
```

The portal and the CLI agree on the underlying fact: the failing leaf operation carries a provider error code, and that code is the diagnosis. The value of the portal is purely navigational, helping you find the leaf when modules have nested the failure deep. Once you have the leaf and its code, you are back on the compile-then-deploy rule, routing the fix to the editor or the subscription by the stage and family of the error.

## Companion tools: where to break and fix Bicep on purpose

The fastest way to internalize the compile-then-deploy split is to cause each failure deliberately and watch where it surfaces, which is exactly what a controlled lab environment is for. You can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.net/tools/azure-labs.html) to author a Bicep file, break it at the compile stage with a bad module reference or a type error, fix it, then break it at the deploy stage with an under-privileged identity or a quota-busting request, and read each failure through the commands in this article. Pairing that with scenario practice cements the diagnostic reflex, so engineers who want to drill the read-the-stage habit under realistic conditions can [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html), each one presenting a failed deployment and asking which stage failed and where the fix lives before revealing the answer.

## The closing verdict

The reason Bicep deployment failures feel harder than they are is that two genuinely different problem classes hide behind one command and one scroll of red text. The fix is not more Bicep knowledge in the abstract; it is one habit applied first, every time. Run `az bicep build` before you read anything for meaning. If it fails, you have a compile-time error, the fix is in your editor, and you can iterate offline at the speed of a local build. If it succeeds, every remaining failure is an ARM error against the JSON your file produced, the fix lives in your subscription's roles, quotas, locks, or the provider's own rules, and the actionable detail is in the deployment operations, not the template. That single split, the compile-then-deploy rule, turns a Bicep failure from a guessing game into a lookup. It is the same discipline the rest of this series applies to every error: localize precisely before you change anything, because the cost of a misattributed fix, an afternoon spent rewriting correct syntax to chase an authorization problem, is far higher than the thirty seconds it takes to ask which stage failed.

## CLI and compiler version drift as a hidden cause

A failure that appears the moment a colleague runs the same file you ran successfully, with no change to the file, is often a version-drift problem rather than a code problem. The Bicep compiler ships independently and updates frequently, and the Azure CLI bundles its own copy. A file that uses a language feature or a resource type schema introduced in a newer compiler can fail to build on an older one, producing a `BCP` error that has nothing to do with the source being wrong and everything to do with the toolchain being behind.

```bash
# Check the compiler version both standalone and through the CLI.
bicep --version
az bicep version

# Upgrade the CLI-bundled Bicep to the latest.
az bicep upgrade
```

The diagnostic tell is that the same file builds on one machine and fails on another, or builds in one pipeline agent image and fails in another. When that happens, compare versions before you compare anything else, because the most common resolution is to pin or upgrade the compiler so every environment agrees. Pinning the Bicep version in your pipeline, rather than letting each agent pull whatever it happens to have, removes an entire category of intermittent compile failures that look like flaky code and are really inconsistent tooling. The deploy stage has its own version dimension: the resource type API version you declare in each resource determines the schema the provider validates against, so bumping an API version can introduce a required property or a new validation rule that was not there before. A deploy-time validation error that appears right after an API version change is almost always the schema difference, and the fix is to read the schema for the new version rather than reverting blindly.

## Extension resources, scope functions, and cross-module references

Bicep's scope handling extends beyond `targetScope` into per-resource and per-module scoping, and these are a rich source of compile errors that feel obscure until the model clicks. A resource or module can carry a `scope` property that deploys it somewhere other than the file's default scope, and an extension resource (a lock, a role assignment, a diagnostic setting) attaches to a parent resource through scope functions. Getting the scope expression wrong produces a compile error when Bicep can prove the scope is invalid, and a deploy error when the scope is type-valid but points somewhere the provider rejects.

```bicep
// A lock as an extension resource, scoped to a storage account.
resource sa 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'stappdata${uniqueString(resourceGroup().id)}'
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
}

resource lock 'Microsoft.Authorization/locks@2020-05-01' = {
  name: 'no-delete'
  scope: sa
  properties: {
    level: 'CanNotDelete'
  }
}
```

Cross-module references are the other scope-adjacent failure. A module produces outputs, and a later module or resource consumes them through the module's symbolic name. A typo in the output name, a reference to an output a module does not declare, or a dependency that Bicep cannot infer produces a compile error. Bicep usually infers `dependsOn` automatically from references, which is a feature, but it means that if you reference a module's output, the consuming resource correctly waits for the producing module, while if you do not reference it and the order still matters, you must declare the dependency explicitly or the deployment can attempt the consumer before the producer has finished.

```bicep
module network './modules/network.bicep' = {
  name: 'networkDeploy'
  params: { location: location }
}

// Consumes an output; Bicep infers the dependency automatically.
module app './modules/app.bicep' = {
  name: 'appDeploy'
  params: {
    subnetId: network.outputs.subnetId  // referencing this creates the dependency
    location: location
  }
}
```

When a cross-module reference fails at compile time, the message names the missing or mistyped output, and the fix is to align the consumer with what the producer actually declares. When the failure is at deploy time and reads like a not-found or invalid-reference error, the usual cause is an ordering problem that Bicep could not infer, and the fix is an explicit dependency or a reference that establishes the order implicitly.

## Reading what-if output without chasing phantoms

The `what-if` operation is the single best pre-deploy safeguard, but its output has a learning curve that, misread, sends people chasing changes that are not real. What-if reports a predicted set of changes, marking each resource as to-create, to-modify, to-delete, or unchanged, and it occasionally reports a property as changing when the change is a no-op artifact of how the provider normalizes values rather than a real difference. Reading what-if well means distinguishing a meaningful predicted change, a resource that will be deleted, a property that will actually flip, from this kind of noise.

```bash
# Verbose what-if shows the full predicted delta per resource.
az deployment group what-if \
  --resource-group rg-app-prod \
  --template-file main.bicep \
  --parameters main.bicepparam \
  --result-format FullResourcePayloads
```

The change type that deserves the most attention is a deletion, because it signals that the template, deployed in complete mode or in a way that removes a resource, would destroy something that exists. The relationship between Bicep and ARM deployment modes matters here: ARM's incremental mode only adds and updates, while complete mode deletes resources absent from the template, and a what-if run against complete mode that shows unexpected deletions is warning you before the fact. The full model of incremental versus complete mode, and why complete mode is the most dangerous ARM surprise, belongs to the control-plane treatment the series links to, but the Bicep-facing takeaway is that what-if is where you catch a destructive deployment before it runs, and a deletion in the preview is never noise to dismiss.

## Verbose and debug output for the failures that hide their cause

When the standard error text is too terse to act on, raising the CLI's verbosity exposes the underlying request and response, which sometimes reveals a cause the summarized message obscured. The `--debug` flag prints the full HTTP exchange with ARM, including the request body and the raw provider response, and `--verbose` sits between the default and full debug.

```bash
# Full HTTP exchange with ARM for a stubborn deploy-time failure.
az deployment group create \
  --resource-group rg-app-prod \
  --template-file main.bicep \
  --parameters main.bicepparam \
  --debug
```

Debug output is verbose enough to be overwhelming, so the discipline is to search it for the provider error code rather than read it linearly. The same `statusMessage.error.code` that the deployment-operations query surfaces will appear in the debug stream, often with additional context such as the exact resource ID and the property the provider objected to. For compile-time failures, the equivalent depth comes from building with output to a file and inspecting the generated ARM, because seeing the JSON your Bicep produced sometimes reveals that an expression evaluated to something other than what you intended, which then explains a downstream provider rejection.

```bash
# Inspect the generated ARM to see what your Bicep actually produced.
az bicep build --file main.bicep --outfile main.json
cat main.json | python3 -m json.tool | less
```

## The related failures Bicep errors are confused with

Several failures live adjacent to Bicep deployment errors and get blamed on Bicep when they belong elsewhere, and naming them sharpens the diagnosis. The first is a pure ARM template error in a project that uses both Bicep and hand-authored JSON, where the failing template is the JSON one and Bicep is innocent; the [ARM deployment error guide](/2022/10/24/fix-arm-template-deployment-errors/) owns that family, and the tell is that the failing file is `.json`, not `.bicep`. The second is a pipeline or tooling error, an expired service connection, a wrong subscription context, a missing CLI extension, that fails before either compile or deploy and produces a tooling message rather than a `BCP` code or an ARM error code. The third is a Terraform or other IaC tool error in a polyglot estate, which has nothing to do with Bicep at all but gets swept into the same mental bucket of infrastructure-as-code failures.

The way to keep these distinct is to anchor on the two signals this article is built around. A `BCP` code or a build failure from `az bicep build` is a Bicep compile error and nothing else. An ARM error code from the deployment operations is a deploy-time error shared with hand-authored ARM, which means the diagnosis transfers directly to the JSON world and the fix is identical regardless of which authoring language produced the template. Anything that is neither, no `BCP` code, no ARM error code, just a tooling or auth-context failure, is upstream of both stages and belongs to your pipeline configuration. Routing each failure to its true owner is the same localization habit that makes the compile-then-deploy rule work, applied one level higher.

## Secure parameters and secret references that fail

Secrets introduce a failure mode that spans both stages and trips up engineers who expect a secret value to behave like any other parameter. A parameter decorated with `@secure()` is hidden from logs and outputs, and a linter rule will reject a hardcoded default on it, which is a compile-time guardrail. The more interesting failures come from referencing a secret stored in Key Vault, where the reference must resolve at deploy time and the deploying identity must be allowed to read the secret.

```bicep
@secure()
param adminPassword string

// Reference a Key Vault secret in a parameter file via getSecret.
// Requires the deploying identity to read the secret, and the vault
// to permit template deployment access.
```

The recurring secret failure is an authorization problem dressed as a deployment error: the Key Vault reference resolves only if the vault is configured to allow access during template deployment and the identity has the data-plane permission to read the secret. A control-plane role on the vault is not the same as the data-plane secret-read permission, which is the same control-plane versus data-plane distinction that the authorization discussion raised. When a secret reference fails, confirm the vault's deployment access setting and the identity's secret-read permission before suspecting the Bicep, because the template is almost always correct and the gap is in the vault's access configuration.

The other secret-related compile failure is attempting to output a secure value, which Bicep refuses because outputs are stored in deployment history in plain text. A template that tries to emit a password or key as an output fails the linter or produces a warning you should never suppress, because the fix is to not output the secret at all, not to silence the rule.

## Re-running a failed Bicep deployment safely

After a failure, the instinct is to fix and re-run, and Bicep deployments are generally safe to re-run because ARM resource operations are designed to be idempotent: deploying the same template again converges resources to the declared state rather than duplicating them. The exception is a partially completed deployment where some resources were created before the failure, which is normal and not a problem, because the re-run reconciles the already-created resources and proceeds with the rest. Incremental mode, the default, never deletes a resource just because it already exists, so a re-run does not undo earlier successful resources.

```bash
# A re-run in incremental mode (the default) converges to the
# declared state without duplicating already-created resources.
az deployment group create \
  --resource-group rg-app-prod \
  --template-file main.bicep \
  --parameters main.bicepparam \
  --mode Incremental
```

The genuine risk on a re-run is mode, not the act of re-running. If a deployment uses complete mode, a re-run will delete any resource in the resource group that is not in the template, which can remove resources an earlier deployment or a teammate created out of band. This is why a what-if before a re-run, especially against an environment where other things live, is worth the few seconds it takes. For a failed deployment whose cause you have fixed, a confident re-run in incremental mode after a clean build and a clean what-if is the normal, safe path, and the convergence behavior means you rarely need to tear down and start over.

## Catching both stages in continuous integration before a human ever sees the failure

The cheapest deployment failure is the one a pipeline catches before review, and a well-built continuous integration stage for Bicep catches the entire compile-time family and a large share of the deploy-time one. The structure that works is a layered gate that runs from cheapest and most deterministic to most expensive and most realistic. The first layer is the offline compile, `az bicep build`, which needs no credentials and no Azure connectivity and fails fast on type errors, unresolved modules, and scope mismatches. Running it on every pull request means a type error never reaches a reviewer, let alone a deployment.

```bash
# Layer 1: offline compile gate. No Azure needed.
az bicep build --file main.bicep || { echo "compile failed"; exit 1; }
```

The second layer is the linter promoted to errors for the rules that predict deploy failures, configured in `bicepconfig.json` and enforced by the same build. A secure-default violation or a hardcoded environment URL becomes a build failure rather than a latent risk. The third layer, which does require Azure access, is `what-if` against a representative environment, which surfaces provider-validation errors and, critically, shows any unintended changes or deletions before they happen. Wiring these three layers in sequence means a change has to pass an offline compile, a strict lint, and a provider preview before anyone approves a deployment, and each layer catches a different slice of the error surface this article has mapped.

The discipline that makes the gate trustworthy is consistency of the toolchain across agents, which ties back to the version-drift problem: pin the Bicep compiler version in the pipeline so the build behaves identically on every run, rather than letting an agent image upgrade silently change what compiles. A gate that behaves differently from run to run trains engineers to ignore it, which defeats the purpose. The full modular authoring and pipeline practice that this gate sits inside is the subject of the [complete Bicep authoring guide](/2025/01/27/azure-bicep-complete-guide/), and the deploy-stage errors the gate's what-if layer catches are the same ARM failures the [Resource Manager control plane](/2022/05/16/azure-resource-manager-arm-explained/) explains at the platform level.

## Mapping the most common BCP-class failures to their one-line fix

A handful of compile diagnostics account for most of the time engineers lose at the build stage, and knowing the one-line cause for each turns a `BCP` message from a puzzle into a reflex. A diagnostic about an undeclared or unknown symbol means you referenced a parameter, variable, or resource symbolic name that does not exist in scope, usually a typo or a name you renamed elsewhere, and the fix is to align the reference with the declaration. A diagnostic about a property not existing on a type means you used a property the resource schema for that API version does not define, and the fix is to check the schema for the version you target, since the property may belong to a different version or be misspelled. A diagnostic about an expected value of a different type is the type-mismatch family, fixed by supplying the shape the schema expects.

A diagnostic about a module that cannot be restored is the module-resolution family, fixed by publishing the artifact, correcting the coordinate, or granting pull access depending on whether the artifact is missing or merely inaccessible. A diagnostic about a resource not being valid at the current scope is the `targetScope` family, fixed by matching the file's declared scope to the command and ensuring each resource is declared at a scope where it can exist. A diagnostic about a value not being assignable because it is outside an allowed set is the `@allowed()` family, fixed by passing a permitted value or deliberately widening the set. Across all of them, the constant is that a `BCP` diagnostic is a precise, offline, reproducible statement about your source, never about your subscription, so the fix is always an edit you can verify with another build before you ever attempt a deployment. That precision is the gift of the compile stage, and it is exactly why building first, as its own step, pays for itself many times over.

## Three failure patterns engineers report, each read by stage

The patterns that fill community question threads cluster into a few shapes, and reading each one by stage shows how the same rule resolves very different-looking failures. The first pattern is the deployment that worked yesterday and fails today with no code change. The reflex is to suspect a recent edit, but if the file is genuinely unchanged, the cause is almost always external: a toolchain upgrade on the agent that shifted the compiler version, an expired credential or rotated secret in the pipeline, a role removed from the deploying identity during a permissions cleanup, or a region that ran short on capacity for a SKU the template requests. Reading by stage cuts through it. A clean `az bicep build` rules out the compiler shift and points at the subscription, where a role audit and a capacity check usually find the change. A failed build points back at the toolchain, and a version comparison confirms it. The pattern teaches that an unchanged file failing is a signal to look outside the file first, not inside it.

The second pattern is the module that one teammate can deploy and another cannot, from the same repository. This is almost never a code problem, because the code is shared, and almost always an access or context problem that differs between the two people. One teammate holds `AcrPull` on the module registry and the other does not, so the registry restore fails for one at the compile-restore stage. Or one is logged into the correct subscription context and the other is pointed at a different subscription where the target resources or roles do not exist, so the deploy stage fails for one with not-found or authorization errors. The diagnostic is to compare the two identities' role assignments and the active subscription context, not to compare the code, which is identical. The pattern teaches that a per-person difference in outcome on shared code is a per-person difference in access or context.

The third pattern is the deployment that succeeds but produces a resource that behaves wrong, which is the most insidious because there is no error at all. The template compiled, ARM accepted it, every operation reported success, and yet the deployed resource does not work as intended: a network rule that does not allow the traffic it should, a setting that defaults differently than expected, a reference that resolved to the wrong target. This is not a deployment error in the strict sense, but it is the failure mode that what-if and a careful read of the generated ARM are designed to prevent, because both let you see what the deployment will actually produce before and after it runs. The pattern teaches that a successful deployment is not the same as a correct one, and that the same habit of inspecting the generated template and previewing changes guards against silent misconfiguration as much as against loud failures. Across all three patterns, the constant is the discipline of localizing before changing: the unchanged file points outside itself, the per-person failure points at access, and the silent misbehavior points at what the template truly produced rather than at whether it produced anything. None of these is solved by guessing at syntax, and all of them are solved faster by asking which stage and which signal first.

## Frequently Asked Questions

### Q: Is there a single command that tells me whether my Bicep problem is compile-time or deploy-time?

Yes, and it is the most useful habit you can build. Run `az bicep build --file main.bicep` as a standalone step before deploying. This compiles your Bicep to ARM JSON without contacting Azure. If it fails, your problem is entirely compile-time: a type error, a missing property, an unresolved module, or a scope mismatch, and the fix is in your editor. If it succeeds and produces a JSON file, the compile passed and every remaining failure during deployment is an ARM error against that JSON, meaning the cause lives in your subscription's roles, quotas, locks, or the provider's validation rules. Making this build step its own gate, rather than letting `az deployment group create` fuse compile and deploy into one opaque invocation, removes the ambiguity for free and stops you from editing correct syntax to chase a deploy-stage problem no edit can solve.

### Q: What does a BCP error code mean and where do I find what it refers to?

A `BCP` code is a Bicep compiler diagnostic, emitted during transpilation, identifying a specific problem in your source by a stable code and a file-and-line reference. Each code maps to one class of issue: an unresolved symbol, a type mismatch, a missing required property, an invalid expression, a module that cannot be restored. Because the codes are deterministic, the same file produces the same code on any machine with the same compiler version, so you can reproduce and fix offline using `az bicep build` without spending a deployment. The message text accompanying the code names the property, expression, or reference at fault, which is usually enough to act on directly. When it is not, the code is searchable in the Bicep documentation, and the Bicep editor extension surfaces the same diagnostics inline as you type, often catching the issue before you save. Treat a `BCP` code as a pure compile-stage signal: it means nothing reached Azure and the fix belongs in your editor.

### Q: How do I publish a Bicep module to a registry so the reference resolves?

A registry module reference using the `br:` scheme resolves only if the artifact has been published to that Azure Container Registry at the exact repository path and tag in the coordinate. Publish it with `az bicep publish`, pointing at the source module file and the full target coordinate, including the registry login server, the repository path, and the version tag. After publishing, the reference in your consuming file resolves at build time, provided your identity also holds the `AcrPull` role on the registry. Two failures bracket this: if you never published the artifact or got the tag wrong, the restore fails with a not-found, and the fix is to publish or correct the coordinate; if the artifact exists but you lack pull rights, the restore fails with an authorization error that surfaces from the Bicep CLI, and the fix is the role grant. Confirm the artifact with `az acr repository show-tags` and your access with `az role assignment list` before assuming the Bicep is wrong.

### Q: Why does my Bicep file build locally but fail to build in the pipeline?

This is almost always version drift in the Bicep compiler, not a problem with the file. The compiler ships independently and updates often, and the Azure CLI bundles its own copy, so your local machine and the pipeline agent can run different versions. A file using a language feature or a resource schema introduced in a newer compiler builds on your up-to-date machine and fails on an older agent with a `BCP` error that has nothing to do with the source being wrong. Confirm by comparing `az bicep version` locally and in the pipeline. The durable fix is to pin the Bicep version in the pipeline so every agent agrees, rather than letting each pull whatever it happens to have, which removes a whole class of intermittent failures that masquerade as flaky code. Upgrading the local or agent compiler with `az bicep upgrade` aligns them, but pinning is what keeps them aligned across future runs and prevents the same surprise from recurring on a new agent image.

### Q: How do I give a pipeline identity permission to create role assignments from Bicep?

Creating a role assignment requires the `Microsoft.Authorization/roleAssignments/write` action, which a standard Contributor role does not include. A pipeline service principal that can create storage, networking, and compute will still fail with `AuthorizationFailed` the moment a template tries to assign a role, because that action belongs to Owner or to the more targeted User Access Administrator role. The fix is to grant the pipeline identity one of those roles at the scope where the assignment is created, or to separate the privileged role-assignment step into its own deployment run by a more privileged identity, keeping the bulk of your infrastructure deployment on a least-privilege principal. Granting Owner broadly to a pipeline is the over-broad anti-pattern; User Access Administrator scoped to the specific resource group is the tighter grant that still permits the assignment. Confirm the current rights with `az role assignment list --assignee` against the target scope, and remember that a freshly granted role can take time to propagate before a re-run succeeds.

### Q: What is the difference between az bicep build and az deployment group validate?

They check different things at different depths. `az bicep build` is a pure compile: it transpiles your Bicep to ARM JSON and runs the linter, entirely offline, catching type errors, missing properties, unresolved modules, and scope mismatches without contacting Azure. `az deployment group validate` goes further: it submits the compiled template to Resource Manager, which runs provider-level validation against your subscription, surfacing many deploy-time errors such as authorization gaps, certain provider rules, and reference problems, without actually provisioning anything. Build proves the compile stage; validate begins probing the deploy stage. Neither is a substitute for the other, and the most thorough pre-deploy posture runs build first to clear compile errors fast and offline, then `what-if` or validate to surface provider issues before a real deployment. Using validate alone hides nothing about the compile stage, but it does require Azure connectivity and credentials, whereas build needs neither, which is why build belongs first in any gate.

### Q: How do I preview exactly what a Bicep deployment will change before I run it?

Use the `what-if` operation: `az deployment group what-if` compiles your template, submits it to Resource Manager, and returns a predicted set of changes marking each resource as to-create, to-modify, to-delete, or unchanged, without provisioning anything. It is the single best safeguard against an unintended change, and it doubles as a pre-deploy validator because it runs far enough into the provider path to surface many validation errors. Read deletions with the most care, since a resource marked for deletion signals that the deployment, in complete mode or by removing a resource from the template, would destroy something that exists. What-if occasionally reports a property as changing when the difference is a normalization no-op rather than a real change, so distinguish a meaningful predicted delta from that noise. Adding `--result-format FullResourcePayloads` shows the full predicted state per resource for a closer look. Making what-if mandatory before any deployment to an environment that matters converts a category of deploy-time failures into pre-deploy findings.

### Q: Why does my .bicepparam parameter file fail to compile?

A `.bicepparam` file is itself compiled and type-checked against the template it references through its `using` statement, so a parameter file can fail at the compile stage just like the template. The common causes are a type mismatch, assigning a string to a parameter the template declares as `int`, an assignment to a parameter the template does not declare, or a `using` path that does not point at the right template. Because the parameter file is type-checked against the template's parameter declarations, the compiler catches these before deployment and names the offending assignment. A separate failure is omitting a parameter that has no default, which is not a compile error in the parameter file but a submission error at deploy because a required input is missing. The diagnostic is the usual one: build the template and parameter file together, and if the build is clean, any remaining parameter problem is a semantic one, a value that is type-valid but wrong for a real provider constraint, which surfaces at deploy through the provider that rejects it.

### Q: How do I reference an existing resource in Bicep without trying to create it?

Use the `existing` keyword on the resource declaration, which tells Bicep to reference a resource that already exists rather than create or manage it. You supply the resource type, API version, and the name (and a `scope` if it lives elsewhere), and Bicep gives you a typed reference to read its properties or use its ID. The critical caveat is that `existing` is trusted at compile time: the reference is type-valid and the build succeeds whether or not the resource actually exists, because the compiler cannot check external state. If the resource is absent at deploy time, the deployment fails with a not-found provider error. So an `existing` reference that compiles cleanly but fails at deploy almost always means the target resource is not there, or is in a different scope than you specified, and the fix is to reconcile the reference with reality rather than to change the syntax. This makes `existing` a frequent source of deploy-time surprises that read like template bugs but are really state mismatches.

### Q: Why does a Bicep loop cause a name collision when I deploy?

A `for` loop generates one resource per element of an array, and if two elements produce the same resource name, the template compiles, because the names are computed from expressions the type system accepts, but the deployment fails because two resources cannot share a name within one deployment. The collision is a runtime fact the compiler cannot foresee, since it does not evaluate the array contents for uniqueness. The fix is to ensure the naming expression yields a distinct value per iteration, often by incorporating the loop index or a unique element property rather than a value that can repeat across elements. A subtler version arises when the array itself contains duplicate entries, so even a per-element naming scheme produces the same name twice. The diagnostic is to look at the failed operation, see the duplicate name, and trace it back to the loop's input array and naming expression. This is a clean illustration of why a compile-clean template can still fail: the compiler validates shape, not the uniqueness of computed runtime values.

### Q: How do I find which module failed when my Bicep uses deeply nested modules?

Every Bicep module becomes a nested ARM deployment, so a failure several modules deep can be hard to trace from a single flat query. List the nested deployments with `az deployment group list` to see each deployment and its provisioning state, then drill into the failed one. The Azure portal's deployment blade on the resource group often shows the parent-child chain more clearly than the CLI, letting you navigate to the failed leaf deployment, which is where the actual provider error lives. Once you reach the leaf, `az deployment operation group list` for that specific deployment name returns the failed resource operation and its `statusMessage.error.code`, which is the real diagnosis. The structural insight is that the failure is always in a leaf operation carrying a provider error code; the nesting only makes it harder to locate, not harder to understand. Composing deployments from smaller, single-purpose modules makes this easier, because each module's failure is localized and you spend less time tracing through layers to find the leaf that actually failed.

### Q: Can an outdated Bicep CLI cause a build to fail on a file that is actually valid?

Yes. The Bicep compiler evolves quickly, adding language features and updating the resource type schemas it validates against. A file that uses a newer feature or a newer resource schema builds on an up-to-date compiler and fails on an older one with a `BCP` error, even though the source is correct for the current language. This is why a file can build on one machine and fail on another with no change to the code. Confirm by comparing the compiler version across environments with `az bicep version`, and resolve it by upgrading with `az bicep upgrade` or, better for consistency, pinning a known version across all machines and pipeline agents so they agree. The lesson is to suspect the toolchain before the code when a previously working or locally working file fails to build elsewhere, because version drift in the compiler is a far more common cause of that specific symptom than a genuine error that somehow appears only in one place.

### Q: How do I read the actual provider error behind a failed Bicep deployment?

After a deploy-time failure, query the deployment operations rather than reading the summarized CLI message, which is often generic. Run `az deployment operation group list` for the deployment name, filtering for operations whose provisioning state is failed, and project `statusMessage.error.code` and `statusMessage.error.message`. That error code is the provider's own verdict and names the real cause: `AuthorizationFailed`, `QuotaExceeded`, `SkuNotAvailable`, `InvalidResourceReference`, a name-constraint violation, and so on. The code routes the fix: authorization to a role grant, quota to a limit increase or smaller request, capacity to a different region or SKU, validation to the value the provider rejected. For a stubborn failure where even the operation message is terse, adding `--debug` to the deploy command prints the full HTTP exchange with ARM, including the raw provider response, which you search for the error code rather than reading linearly. The discipline is to get to the provider code first, because everything downstream of reading it is mechanical, and the summarized message rarely contains the actionable detail the operations do.

### Q: Why does bumping a resource API version break my Bicep deployment?

Each resource declaration pins an API version, and that version determines the schema the resource provider validates against. A newer API version can add a required property, change an allowed value, tighten a constraint, or rename a property, so a resource that deployed cleanly under an older version can fail to compile or fail at deploy after the bump. A compile-stage break appears as a `BCP` type or required-property error, because the Bicep type system carries the schema for the version you declared. A deploy-stage break appears as a provider validation error if the change is a business rule the type system cannot express. The fix is never to revert the version blindly; it is to read the schema for the version you now target and align your resource declaration to it, since the new version usually exists for a reason and reverting forgoes whatever it added. When a validation error appears immediately after an API version change, the schema difference is the prime suspect, and comparing the old and new schemas for that resource type points straight at the property to adjust.

### Q: How do I fix an AcrPull denied error when restoring a Bicep registry module?

This error appears during the build or restore phase, from the Bicep CLI, when your `br:` module reference points at a real artifact but your identity lacks permission to pull it from the Azure Container Registry. Although it surfaces from the compile-stage tooling, it is an authorization problem, which is why it confuses people who expect compile errors to be pure code issues. The fix is to grant the identity, your user account or the pipeline's service principal, the `AcrPull` role on the registry. Confirm the current grants with `az role assignment list --assignee` scoped to the registry's resource ID, and add the role if it is missing. Distinguish this from a not-found restore failure, where the artifact or tag does not exist and the fix is publishing or correcting the coordinate rather than granting access. The two failures both block the restore but have opposite remedies, so reading whether the message says the artifact is missing or that access was denied tells you which path to take.

### Q: What does the @allowed decorator do and why does it reject my parameter value?

The `@allowed()` decorator constrains a parameter to a fixed set of permitted values, declared as an array on the parameter. Passing a value outside that set is rejected before deployment, which is the intended behavior: it prevents an invalid input from ever reaching the provider. The rejection can surprise someone who expected a near-miss value to be accepted, for example passing `production` when the allowed set is `dev`, `staging`, `prod`. The fix is to pass one of the exact allowed values, or, if the set is genuinely too narrow, to widen the decorator's array deliberately. A caution from the Bicep guidance is not to over-use `@allowed()` on values like SKUs or locations that change over time, because a hardcoded allowed set becomes stale and rejects newly valid values, turning a guardrail into a maintenance burden. Used on truly fixed sets like an environment name, it is a clean way to validate input at the earliest possible stage, before the deployment even starts.

### Q: How do I deploy a Bicep file that is scoped to the subscription rather than a resource group?

A subscription-scoped file declares `targetScope = 'subscription'` at the top and is deployed with `az deployment sub create`, supplying a `--location` for the deployment metadata since there is no resource group to inherit one from. This scope is what you use to create resource groups themselves, assign policies or roles at subscription scope, or deploy modules into resource groups the same file creates. Deploying such a file with the resource-group command, `az deployment group create`, fails with a scope mismatch, because that command expects a resource-group-scoped template. The inverse also fails: declaring a subscription-level resource inside a resource-group-scoped file is a compile error, because the resource cannot exist at that scope. The model to hold is that the scope is a property of the deployment, the file declares the scope it expects through `targetScope`, and the command you run must match that declaration. When they disagree, change one so they agree rather than rewriting the resources, because the resources are usually fine and only the scope-and-command pairing is wrong.

### Q: Does Bicep set resource dependencies automatically, or do I need dependsOn?

Bicep infers dependencies automatically from references. When one resource or module refers to another, by using its symbolic name, its ID, or one of its outputs, Bicep adds the implicit `dependsOn` so the referenced resource deploys first. This is why idiomatic Bicep rarely needs an explicit `dependsOn`: the references that naturally exist in a template establish the ordering. You only need an explicit `dependsOn` when a real ordering requirement exists that is not expressed through any reference, which is uncommon and often a sign the template could be restructured to reference the dependency instead. A deploy-time failure that reads like an ordering or not-found problem, where a consumer ran before its producer finished, usually means a dependency Bicep could not infer because no reference connected the two. The fix is to introduce a reference that establishes the order implicitly, or to add the explicit `dependsOn` as a last resort. Over-declaring `dependsOn` on resources that already reference each other is redundant and clutters the template without changing behavior.

### Q: How do I debug a Bicep deployment that fails with a message too vague to act on?

Raise the verbosity to expose the underlying exchange. Adding `--debug` to `az deployment group create` prints the full HTTP request and response with Resource Manager, including the request body and the raw provider response, which often contains the specific error code and the property at fault that the summarized message omitted. Because debug output is voluminous, search it for the error code rather than reading top to bottom. For compile-stage vagueness, build to a file with `az bicep build --outfile main.json` and inspect the generated ARM, since seeing the JSON your Bicep produced sometimes reveals an expression that evaluated to something unintended, which explains a downstream rejection. Between the two, you can localize almost any opaque failure: debug for the deploy stage exposes the provider's full response, and the generated JSON for the compile stage exposes what your source actually became. The goal in both cases is to convert a vague summary into a concrete signal, an error code or a wrong generated value, that tells you which stage failed and where the fix lives.

### Q: Is it safe to re-run a Bicep deployment that partially failed partway through?

Generally yes, in incremental mode, which is the default. ARM resource operations are idempotent, so re-running the same template converges resources to the declared state rather than duplicating them, and resources created before the failure are reconciled rather than recreated. Incremental mode never deletes a resource merely because it already exists, so a re-run does not undo earlier successful work; it picks up the resources that had not yet been created. The real risk on a re-run is the deployment mode, not the act of re-running. In complete mode, a re-run deletes any resource in the resource group that is absent from the template, which can remove resources a teammate or an earlier process created out of band. That is why running `what-if` before a re-run, particularly against a shared environment, is worth the few seconds: it shows any deletions before they happen. For a failure whose cause you have fixed, a clean build, a clean what-if, and a re-run in incremental mode is the normal, safe path, and tearing down to start over is rarely necessary.
