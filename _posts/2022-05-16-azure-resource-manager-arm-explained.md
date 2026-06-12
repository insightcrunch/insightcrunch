---
layout: post
title: "Azure Resource Manager (ARM) Explained"
page_title: "Azure Resource Manager (ARM) Explained: How Templates, Deployment Modes, Scopes, Dependencies, and the Control Plane Work, and Why Deployments Fail"
date: 2022-05-16
categories: ["Technology"]
tags: ["Azure", "ARM", "DevOps", "Architecture", "Cloud Computing"]
excerpt: "Azure Resource Manager is the control plane behind every deployment. Learn how ARM templates, modes, scopes, and dependencies work and why deploys fail."
image: "/assets/images/blog/blog-37.webp"
reading_time: 63
author: "nathan-cole"
last_updated: 2022-05-16
lang: en
---
Every action you take in Azure, whether you click a button in the portal, run an `az` command, push a Terraform plan, or trigger a pipeline, passes through Azure Resource Manager before a single byte of infrastructure changes. Azure Resource Manager, almost always shortened to ARM, is the control plane that receives the request, authenticates it, authorizes it against role assignments, hands the work to the right resource provider, orders the operations into a graph, and reports back what happened. Engineers who treat ARM as an invisible plumbing layer keep getting surprised by it, because the surprises live exactly where the plumbing is: a deployment that deletes a database nobody meant to touch, a 409 conflict on a pipeline that ran fine yesterday, an `AuthorizationFailed` on an identity that "has Owner," a template that validates locally and then fails in the cloud with a provider error three layers deep. None of those are random. Each is the predictable output of a specific ARM behavior, and once you hold the model of how the control plane works, you can reason about why a deployment failed instead of staring at a red blade and guessing.

![Azure Resource Manager control plane and deployment flow explained - Insight Crunch](/assets/images/blog/blog-37.webp)

This guide treats ARM the way the rest of this series treats every service: as a system with a definite model, real limits, and a finite set of failure modes you can name and design against. We will build the mental model of ARM as the deployment and management API in front of every resource provider, walk the anatomy of a template part by part, settle the incremental-versus-complete question that causes the most damage in production, follow how ARM turns `dependsOn` and references into an ordered graph, map the four deployment scopes and what each can and cannot create, show what the what-if operation tells you before you commit, and explain how role-based access control is evaluated during a deployment rather than before it. Then we put the failure modes in one place: a deployment-error table that maps each common error code to its root cause and the check or fix that resolves it, so a red deployment becomes a diagnosis rather than a mystery. The single claim to carry out of this article is the complete-mode-deletes rule, because it reframes the most dangerous ARM surprise as a mode choice, not a syntax error.

## What Azure Resource Manager actually is

Azure Resource Manager is the management layer that sits between you and every Azure resource. It is not a service you deploy and it is not a region you pick; it is the always-on API surface that every other tool talks to. When you run `az group create`, the CLI translates that into an HTTPS request to the Resource Manager endpoint. When the portal shows you a list of storage accounts, it got that list by asking Resource Manager. When a GitHub Actions workflow applies a Bicep file, the Bicep is compiled to an ARM template and submitted to the same endpoint. Terraform, Pulumi, the Azure PowerShell module, the REST API, and the SDKs all converge on this one control plane. That convergence is the first thing to internalize: there is no back door around ARM. Whatever interface you prefer, the request becomes an ARM operation, and ARM's rules govern the outcome.

The control plane and the data plane are different layers, and confusing them is the source of a recurring class of mistakes. The control plane is the management surface: creating a storage account, assigning a role, changing a firewall rule, listing virtual machines. The data plane is what you do with a resource once it exists: writing a blob into that storage account, reading a secret from a Key Vault, querying a Cosmos DB container. ARM governs the control plane. It does not put a blob in a container and it does not run your query. This distinction explains one of the most common authorization confusions in all of Azure: an identity with the Owner role at the subscription level can create a storage account, configure it, and delete it, yet still receive a 403 when it tries to read a blob, because reading a blob is a data-plane action governed by a different set of roles. ARM authorized the management action and had nothing to say about the data action. Hold that line between planes clearly and a whole category of "but I have permission" tickets dissolves.

### Do all Azure tools go through Azure Resource Manager?

Yes. The portal, the Azure CLI, Azure PowerShell, the REST API, the SDKs, Bicep, and Terraform all converge on the Resource Manager endpoint, because there is no back door around the control plane. Whatever interface you prefer, your request becomes an ARM operation, so ARM's authentication, authorization, ordering, and dispatch rules govern the outcome regardless of the tool.

The model that pays off is to picture ARM as a dispatcher standing in front of a set of specialists. ARM itself does not know how to create a virtual machine, a SQL database, or a virtual network. What it knows is how to take a well-formed request, verify who is asking and whether they are allowed, figure out the order in which things must happen, and route each piece of work to the specialist that handles that resource type. Those specialists are the resource providers, and understanding them is the next layer of the model.

## How ARM works internally: resource providers, types, and the request path

A resource provider is the component that actually understands a category of resources. `Microsoft.Compute` knows about virtual machines, disks, and scale sets. `Microsoft.Storage` knows about storage accounts. `Microsoft.Network` knows about virtual networks, network security groups, public IP addresses, and load balancers. `Microsoft.KeyVault`, `Microsoft.Sql`, `Microsoft.Web`, `Microsoft.ContainerService` for AKS, and dozens more each own their slice. When you submit a deployment that creates a virtual machine attached to a network interface in a subnet of a virtual network, ARM is not doing the work; it is coordinating three providers, `Microsoft.Compute` and `Microsoft.Network` chiefly, and making sure each receives its instruction in a valid order with valid inputs.

Every resource you can create has a fully qualified type written as `provider/resourceType`, sometimes with a nested child type. A storage account is `Microsoft.Storage/storageAccounts`. A subnet is a child type, `Microsoft.Network/virtualNetworks/subnets`. A role assignment is `Microsoft.Authorization/roleAssignments`. This naming is not decoration; it is how ARM routes the operation and how the template engine knows which provider to validate against. When a template fails with an error that names a type you did not expect, the type string tells you which provider rejected the request, and that narrows the diagnosis immediately.

Resource providers must be registered in a subscription before they will accept work. Most of the common ones are registered automatically the first time you use them, but a fresh subscription or a tightly governed one can surprise you with a provider that is not registered, and the deployment fails with a message that the resource type is not available or the provider is not registered for the subscription. The check is direct:

```bash
# List provider registration state for the current subscription
az provider list --query "[].{Provider:namespace, State:registrationState}" -o table

# Register a specific provider explicitly
az provider register --namespace Microsoft.ContainerService

# Confirm it has finished registering
az provider show --namespace Microsoft.ContainerService --query registrationState -o tsv
```

Registration is asynchronous; `register` returns quickly but the state moves through `Registering` to `Registered` over a short interval, and a deployment that races ahead of registration can still fail. In automated pipelines that stand up new subscriptions, registering the providers you depend on as an explicit early step, then polling until they report `Registered`, removes a whole class of intermittent first-run failures.

### How does an ARM request travel from your keyboard to a created resource?

Your tool builds an HTTPS request to the Resource Manager endpoint carrying a bearer token. ARM authenticates the token, authorizes the action against your role assignments, validates the request shape, resolves dependencies into an order, dispatches each operation to its resource provider, polls each provider to completion, and returns a single deployment result you can inspect.

The request path is worth walking slowly because each station in it is a place a deployment can stop. First, authentication: the caller presents a token issued by Microsoft Entra ID, and ARM verifies it is valid and unexpired. A stale token or a misconfigured service principal fails here, before any resource logic runs. Second, authorization: ARM evaluates the requested actions against the role assignments that apply to the target scope, and if the identity lacks a role that grants the specific action, the request stops with `AuthorizationFailed`. Third, request validation: ARM checks that the payload is well formed, that required properties are present, that values are within allowed ranges, and that referenced resources make sense. A malformed template stops here with `InvalidTemplate`. Fourth, dependency resolution: ARM builds the order of operations from the dependencies it can see. Fifth, dispatch and polling: ARM sends each operation to the owning provider and tracks each as it runs, because most real resource creation is asynchronous and takes seconds to many minutes. Sixth, result: ARM aggregates the provider outcomes into one deployment record with a status and, on failure, a nested error that points at the operation that broke. Knowing these six stations turns "the deployment failed" into "the deployment failed at authorization" or "at provider dispatch," which is most of the diagnosis.

## The anatomy of an ARM template

An ARM template is a JSON document that declares the desired state of a set of resources. It is declarative: you describe what you want to exist, not the imperative steps to create it, and ARM works out the operations. A template has a small number of top-level sections, and knowing what each one is for makes any template readable, including the dense ones generated by export tools.

The skeleton looks like this:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {},
  "variables": {},
  "functions": [],
  "resources": [],
  "outputs": {}
}
```

The `$schema` line tells the validation engine which template language version to apply and which scope the template targets; a resource-group template, a subscription template, and a management-group template each use a different schema URL, and pointing at the wrong one is a common early error. The `contentVersion` is a free-form version string you control for your own change tracking; ARM does not interpret it. The interesting work happens in the other sections.

### What goes in parameters, variables, resources, and outputs?

Parameters are the inputs a caller supplies at deploy time, such as a region or a SKU. Variables are values computed once inside the template to avoid repetition. Resources are the declared resource objects ARM will create or update. Outputs are values the template returns after deployment, such as a connection string or a resource ID, for a caller or a later stage to consume.

Parameters are how a template stays reusable across environments. Instead of hard-coding `eastus` and a virtual machine size, you declare them as parameters with types, allowed values, and defaults, then pass different values for dev, test, and production. A parameter block with constraints catches bad input before any provider is touched:

```json
"parameters": {
  "location": {
    "type": "string",
    "defaultValue": "[resourceGroup().location]",
    "metadata": { "description": "Region for all resources in this deployment." }
  },
  "storageSku": {
    "type": "string",
    "defaultValue": "Standard_LRS",
    "allowedValues": [ "Standard_LRS", "Standard_GRS", "Standard_ZRS" ],
    "metadata": { "description": "Replication SKU for the storage account." }
  }
}
```

The `allowedValues` array is a cheap, powerful guardrail: a caller who passes a SKU that is not in the list fails validation immediately with a clear message rather than failing deep inside the storage provider with a vaguer one. The `defaultValue` of `location` uses a template function, `resourceGroup().location`, which resolves to the region of the target resource group, a pattern that keeps a template portable without forcing the caller to repeat the region everywhere.

Variables exist to compute a value once and reuse it. If a storage account name must be globally unique and derived from a base name plus a unique suffix, you compute it in `variables` and reference it from the resource, so the logic lives in one place:

```json
"variables": {
  "storageAccountName": "[concat('stinsight', uniqueString(resourceGroup().id))]"
}
```

The `uniqueString` function produces a deterministic hash from its inputs, so the same resource group always yields the same name, which keeps redeployments idempotent rather than generating a new account each run. Functions like `concat`, `uniqueString`, `resourceId`, `reference`, `parameters`, and `variables` are the small expression language ARM evaluates while it builds the deployment, and they are the reason a template is more than static JSON.

The `resources` array is the heart of the template. Each entry declares one resource with at least a `type`, an `apiVersion`, a `name`, and a `location` where the type requires one, plus a `properties` object whose shape is defined by the provider. A minimal storage account looks like this:

```json
"resources": [
  {
    "type": "Microsoft.Storage/storageAccounts",
    "apiVersion": "2022-09-01",
    "name": "[variables('storageAccountName')]",
    "location": "[parameters('location')]",
    "sku": { "name": "[parameters('storageSku')]" },
    "kind": "StorageV2",
    "properties": {
      "minimumTlsVersion": "TLS1_2",
      "allowBlobPublicAccess": false
    }
  }
]
```

The `apiVersion` is more important than it looks. It pins the template to a specific version of the provider's contract, which means the property shape and the available features are fixed even as the provider evolves. A template written against an older API version will not see a property that a newer version introduced, and a template that copies an `apiVersion` from a years-old sample may be missing a setting you want or may behave differently from the portal default. When a property you expect is rejected as unrecognized, the API version is the first thing to check; you may be writing a newer property against an older contract, and the verification step is to confirm the current API version for that type against the official provider documentation at the time you deploy.

Outputs return values from a finished deployment so that a person or a downstream stage does not have to go hunting for them. A common pattern is to output a resource ID or an endpoint that a later deployment consumes:

```json
"outputs": {
  "storageAccountId": {
    "type": "string",
    "value": "[resourceId('Microsoft.Storage/storageAccounts', variables('storageAccountName'))]"
  }
}
```

Outputs are also where secrets can leak if you are careless: a value you output is recorded in the deployment history, so outputting a key or a connection string writes that secret into a record many identities can read. Treat outputs as public within the subscription and keep secrets out of them, fetching them at runtime through a managed identity instead.

## Incremental versus complete: the deployment mode that deletes things

Here is the single most consequential decision in all of ARM, and the one most engineers never make on purpose because they never learn it exists. Every ARM deployment runs in one of two modes: incremental or complete. The mode is not a property of the template; it is a property of the deployment operation, set by the caller. Incremental is the default, and most people use it for years without ever knowing the other mode is there. Complete mode is where the danger lives, and the rule to carry forever is simple: an incremental deployment only adds and updates, while a complete deployment removes anything in the target resource group that is absent from the template. The most dangerous ARM surprise is therefore a mode choice, not a syntax error.

### Which deployment mode can delete live resources?

Complete mode can. It reconciles the target resource group to match the template exactly, so any resource present in the group but absent from the template is deleted. Incremental mode, the default, never deletes on this basis; it only creates and updates the resources the template names and leaves everything else untouched.

Walk through what each mode does with a concrete case. Suppose a resource group already holds a storage account, a virtual network, and a SQL database, all created by hand or by an earlier deployment. Now you submit a template that declares only the storage account, with a property change. In incremental mode, ARM updates the storage account to match the template and leaves the virtual network and the SQL database completely alone, because incremental mode only reasons about the resources the template names. In complete mode, ARM reads the template as the full and authoritative description of what the resource group should contain, sees that the virtual network and the SQL database are not in it, and deletes them. The storage account change applies either way; the difference is the silent destruction of everything the template did not mention. This is why a team that adopts complete mode for the right reason, enforcing that a resource group contains exactly what the template says and nothing drifted in by hand, must also adopt the discipline that the template is genuinely complete, because a missing resource is now a delete instruction.

The command makes the mode explicit, and the safe habit is to always state it rather than rely on the default:

```bash
# Incremental: additive, the default; existing unlisted resources are preserved
az deployment group create \
  --resource-group rg-insight-prod \
  --template-file ./main.json \
  --parameters @main.parameters.json \
  --mode Incremental

# Complete: the group is reconciled to the template; unlisted resources are deleted
az deployment group create \
  --resource-group rg-insight-prod \
  --template-file ./main.json \
  --parameters @main.parameters.json \
  --mode Complete
```

There is one critical protection to use before ever running complete mode against anything you care about, and it is the what-if operation covered later in this article: running what-if in complete mode shows you the delete list before you commit, turning an invisible hazard into a reviewable plan. The misdiagnosis to retire here is the belief that complete mode is a tidy, safe default for keeping environments clean. It is a powerful reconciliation tool, and it is the correct choice for an environment that must match its template exactly, but it is never a casual default, and it should never run against a shared or production resource group without a what-if preview and a human reading the delete list. When a deployment that "only changed one setting" wipes out a database, the cause is almost always a complete-mode deployment against a template that did not declare the database, and the lesson is that the mode, not the template body, decided the outcome. For the conflict and failure cases that show up around repeated and concurrent deployments, the dedicated walkthrough of [Azure deployment conflict errors](/2022/10/17/fix-azure-deployment-conflict/) covers the 409 family in depth, and the [ARM template deployment failure guide](/2022/10/24/fix-arm-template-deployment-errors/) handles the validation and provider errors that stop a deployment before mode ever matters.

## Dependencies and the ordered graph

A resource group full of resources is not a flat list to be created all at once; it is a graph with edges, because some resources cannot exist until others do. A network interface needs a subnet to attach to. A virtual machine needs a network interface and a disk. A private endpoint needs the resource it connects to. ARM's job is to discover that order and execute the operations in it, and it does this by building a directed graph from the dependencies it can see and then creating resources in an order that respects every edge, parallelizing wherever the graph allows.

ARM learns about dependencies two ways. The explicit way is the `dependsOn` property, an array of resource identifiers that tells ARM "do not start this resource until those are done." The implicit way is the `reference` and `resourceId` functions: when resource B's definition refers to resource A through one of these functions, ARM infers that B depends on A and orders them accordingly, without you writing `dependsOn` at all. The implicit mechanism is the cleaner one, because the dependency lives where the relationship actually is, inside the property that uses the other resource. Over-using explicit `dependsOn` leads to brittle, over-constrained templates and is a frequent cause of unnecessary serialization, where resources that could have been created in parallel are forced into a slow chain.

### Does the order of resources in a template matter?

No. ARM ignores the textual position of resources in the template's JSON array and obeys only the dependency graph it builds from `dependsOn` and from implicit `reference` and `resourceId` links. A subnet declared after the virtual machine that uses it is still created first, because the graph, not the order on the page, decides execution order.

That last point catches people: the order of resources in the `resources` array is irrelevant to execution order. ARM ignores textual position entirely and obeys only the graph. Two engineers reading the same template can disagree about the creation order if one is reading top to bottom and the other is reading the dependencies, and the dependency reader is right. A subnet declared after the virtual machine that uses it still gets created first, because the graph says so. This is also why a circular dependency is a hard error rather than a slow loop: if A depends on B and B depends on A, no valid order exists, and ARM rejects the template rather than trying to break the cycle. Circular-dependency errors usually come from over-specified `dependsOn` entries that encode a relationship the implicit references already handle, and the fix is to remove the explicit dependency and let the reference functions express the real edge. A worked example of expressing a network-interface-to-subnet relationship through a reference rather than a hand-written dependency:

```json
"resources": [
  {
    "type": "Microsoft.Network/networkInterfaces",
    "apiVersion": "2022-07-01",
    "name": "nic-app",
    "location": "[parameters('location')]",
    "properties": {
      "ipConfigurations": [
        {
          "name": "ipconfig1",
          "properties": {
            "subnet": {
              "id": "[resourceId('Microsoft.Network/virtualNetworks/subnets', 'vnet-app', 'subnet-app')]"
            }
          }
        }
      ]
    }
  }
]
```

Because the network interface references the subnet through `resourceId`, ARM knows the subnet, and therefore its parent virtual network, must exist first, and it orders the operations without a single `dependsOn`. If you later add an explicit `dependsOn` pointing the other direction by mistake, you create a cycle and the template stops validating. Reading dependency errors well means reading them as graph problems: a missing dependency produces a race where a resource tries to attach to something not yet there, and a circular dependency produces a rejection where no order exists.

## Deployment scopes: where a template is allowed to act

A template does not float in a vacuum; it is deployed at a scope, and the scope determines what kinds of resources the template may create and which command submits it. There are four scopes, nested from narrowest to broadest: resource group, subscription, management group, and tenant. Most templates target a resource group, which is why the resource-group scope feels like the only one until you need to create something that lives above it.

### Why can't I create a resource group at resource-group scope?

Because a resource-group deployment targets a group that already exists, so the group cannot be the thing it creates. Creating a resource group is a subscription-scope action, alongside policy and role assignments that apply across the subscription. You deploy each resource at the lowest scope that contains it, which is why group creation lives one level up at subscription scope.

The reason scope matters in practice is that the resource you want to create dictates the scope you must deploy at, and a mismatch produces a confusing error. A resource group itself cannot be created by a resource-group deployment, because the group is the thing being targeted; you create resource groups with a subscription-scope deployment. A policy assignment that should apply across an entire subscription is a subscription-scope deployment. A role assignment at the management-group level is a management-group deployment. The command differs by scope, and the schema in the template's `$schema` line must match:

```bash
# Resource-group scope: the common case, create resources inside an existing group
az deployment group create --resource-group rg-insight-prod --template-file ./rg-level.json

# Subscription scope: create resource groups, assign policy or roles across the subscription
az deployment sub create --location eastus --template-file ./sub-level.json

# Management-group scope: govern many subscriptions at once
az deployment mg create --management-group-id mg-insight --location eastus --template-file ./mg-level.json

# Tenant scope: act across the whole directory
az deployment tenant create --location eastus --template-file ./tenant-level.json
```

A subscription-scope and higher deployment requires a `--location` because the deployment record itself needs a region to live in even though the resources it creates may not be regional, which trips people who are used to the resource-group command that infers the region from the group. The practical guidance is to deploy at the lowest scope that contains everything the template creates, and to split a deployment when it spans scopes: a subscription-scope template that creates a resource group can hand off to a nested resource-group deployment for the resources inside that group, which keeps each piece at its natural level and makes the failure boundaries cleaner.

## The what-if operation: see the change before you make it

The single most underused safety feature in ARM is the what-if operation. What-if takes your template and parameters, asks ARM to compute the difference between the current state and the desired state, and returns a preview of what would be created, modified, deleted, or left unchanged, without actually doing any of it. In a world where complete mode can delete a database and an incremental deployment can quietly change a property you did not intend, a preview that lists every create, modify, and delete before you commit is the difference between a controlled change and a hopeful one.

### How do I preview an ARM deployment without applying it?

Run the what-if operation, the same command as your deployment with `what-if` in place of `create`. ARM computes the difference between live state and your template and returns a per-resource preview of creates, modifies, deletes, and unchanged resources, without altering anything, so you confirm the deployment does what you expect before committing.

The command mirrors the deployment command, with `what-if` in place of `create`:

```bash
# Preview an incremental deployment: see creates and modifies before committing
az deployment group what-if \
  --resource-group rg-insight-prod \
  --template-file ./main.json \
  --parameters @main.parameters.json

# Preview a complete deployment: this is where the delete list appears
az deployment group what-if \
  --resource-group rg-insight-prod \
  --template-file ./main.json \
  --parameters @main.parameters.json \
  --mode Complete
```

The complete-mode what-if is the one to make a habit, because it is the only routine way to see the delete list that complete mode will execute. A reviewer reading a what-if output that shows three modifies and zero deletes can approve with confidence; a what-if that unexpectedly shows a delete is a stop sign that just prevented an outage. What-if is not perfect: some resource providers report property changes that are cosmetic or that the provider will normalize, so a what-if can show a "modify" that turns out to be a no-op, a behavior that improves over time as providers refine their change reporting. The right posture is to read what-if as a high-quality preview that catches the dangerous changes reliably and occasionally over-reports a harmless one, which is exactly the asymmetry you want from a safety check. Wiring what-if into a pipeline as a required, human-reviewed gate before any production deployment, and especially before any complete-mode deployment, converts ARM's most dangerous behaviors into reviewable plans.

## How RBAC is evaluated during a deployment

A misconception worth correcting early is that authorization happens once, when the deployment starts, against the identity that submitted it. The reality is more specific and explains a frequent failure: a deployment runs under the identity that submitted it, and every operation in that deployment is authorized against that identity's role assignments at the relevant scope, so a deployment can pass the first few operations and then fail partway through with `AuthorizationFailed` on the one action the identity lacks. The deployment does not pre-check every permission up front; it dispatches operations and each operation must clear authorization when it runs.

This has practical consequences. A service principal that can create storage and networking but lacks `Microsoft.Authorization/roleAssignments/write` will deploy most of a template successfully and then fail exactly on the resource that assigns a role, such as granting a managed identity access to a Key Vault. The error names the action that was denied and the scope it was attempted at, and reading those two facts tells you precisely which role the identity is missing and where. The fix is to grant the deploying identity the role that includes the missing action at the scope the action targets, which for role assignments usually means a role such as User Access Administrator or Owner at the relevant scope, scoped as narrowly as the deployment needs. The sibling article on [Azure RBAC AuthorizationFailed errors](/2022/10/10/fix-azure-rbac-authorizationfailed/) walks the full diagnosis of these permission failures, including how to read the action string in the error and map it back to the role that grants it.

A second consequence concerns managed identities and deployment scripts. When a template includes a deployment script resource that runs under a user-assigned managed identity, that identity, not the original caller, authorizes the actions the script performs, so the script's identity needs its own role assignments. Mixing up which identity authorizes which part of a deployment is a recurring source of permission failures that look mysterious until you separate the caller's permissions from the script identity's permissions. The discipline is to enumerate, for each action a deployment performs, which identity performs it and whether that identity holds a role granting the action at the target scope. Doing that enumeration before the deployment turns a partway-through `AuthorizationFailed` into a permission you granted in advance.

## ARM's limits, quotas, and throttling

ARM is not infinite, and a few of its limits shape how you structure large deployments. These are values that Azure adjusts over time, so the specific numbers are ones to verify against the current official documentation at the time you deploy rather than memorize; what matters is knowing the limit exists and designing so you do not collide with it. There is a cap on the number of resources a single deployment can declare, which is why very large environments are decomposed into nested or linked deployments rather than one enormous template. There is a cap on template size, both for the inline template and for the parameter file, which is another reason large templates are split or moved to linked templates pulled from a storage account at deploy time. There is a limit on how many deployments are retained in a resource group's deployment history, after which the oldest are pruned, which matters for pipelines that deploy frequently and can hit the retention limit and start failing until old deployments are cleared.

Then there is throttling. ARM enforces request rate limits per subscription and per tenant to protect the control plane, and a tool that hammers the API, a pipeline running many deployments in parallel, or an over-eager retry loop can hit a 429 response that says the request was throttled. The correct response to a 429 is not to retry immediately and harder; it is to back off, ideally with the retry interval the response suggests, because retrying into a throttle extends it. Well-behaved tools honor the throttling headers automatically, and custom automation that talks to the ARM REST API directly should implement exponential backoff that respects those headers. When a pipeline that worked at small scale starts failing intermittently as it grows, throttling is a prime suspect, and the fix is to serialize or rate-limit the deployments rather than fan them all out at once.

### Why does a large deployment fail with a resource or size limit?

A single ARM deployment caps the number of resources it can declare and the byte size of the template and parameter files. A monolithic template that grows past those caps fails validation. The fix is decomposition: split the work into nested or linked deployments so each piece stays under the limit, which also improves parallelism and failure isolation.

The quota dimension is separate from ARM's own limits and is owned by the resource providers. When a deployment fails with `QuotaExceeded`, ARM is not the constraint; a provider is reporting that the subscription has hit a quota such as the number of vCPUs of a given VM family in a region, the number of public IP addresses, or the number of storage accounts. The error names the quota and the region, and the resolution is either to request a quota increase through the portal or to fit within the existing quota by choosing a different region, a smaller size, or a different family. Reading a `QuotaExceeded` as an ARM problem sends you debugging the template when the template is fine; the constraint is the subscription's allocation for that resource type in that region, and the dedicated guide on [Azure quota exceeded and vCPU limits](/2022/11/07/fix-azure-quota-exceeded/) covers how to find the current usage, request an increase, and design around the common quota walls.

## The ARM deployment-error table

The fastest way to turn a red deployment into a diagnosis is a map from the error you see to the cause behind it and the check or fix that resolves it. The errors below are the ones engineers actually hit, and each one points at a specific station in the request path. This is the InsightCrunch ARM deployment-error table, and it is the artifact to bookmark and return to mid-incident.

| Error code or symptom | What it actually means | Root cause | Check or fix |
| --- | --- | --- | --- |
| `InvalidTemplate` | The template failed validation before any provider ran | Malformed JSON, an undefined parameter or variable reference, a bad function expression, or a schema mismatch for the scope | Validate locally, confirm the `$schema` matches the scope, and resolve the named expression; the error usually points at the exact line or property |
| `DeploymentFailed` with a nested provider error | ARM dispatched the operation and a provider rejected it | A provider-specific problem: an invalid property value, an unsupported region for the SKU, a name that violates the provider's rules | Open the nested error; it carries the provider's real message and the resource that failed, which is the actual diagnosis |
| `409 Conflict` | The requested change conflicts with the current state | A concurrent deployment touching the same resource, a repeated operation on a resource mid-change, or a name already in use | Serialize the conflicting deployments, wait for the in-flight operation to finish, or change the conflicting name |
| `AuthorizationFailed` | The identity lacks permission for a specific action | The deploying identity has no role granting the denied action at the target scope | Read the action and scope in the error, grant the role that includes that action at that scope, and redeploy |
| `QuotaExceeded` | A provider quota for the subscription and region is full | vCPU, public IP, storage account, or similar quota reached for that region and family | Request a quota increase or fit within quota by changing region, size, or family |
| `ResourceNotFound` | A referenced resource does not exist when needed | A dependency that was assumed to exist, a wrong resource ID, or a race where the referent was not created first | Confirm the referenced resource ID and ensure the dependency is expressed so ARM creates it first |
| Circular dependency error | No valid creation order exists | Two or more resources depend on each other, usually through over-specified `dependsOn` | Remove the redundant explicit dependency and let `reference` and `resourceId` express the real edge |
| Provider not registered | The resource type is unavailable in the subscription | The owning resource provider is not registered | Register the provider and poll until it reports `Registered` before deploying |
| `429 Too Many Requests` | The control plane throttled the request | Too many ARM requests per subscription or tenant in a short window | Back off with the suggested interval, serialize or rate-limit the deployments, and honor throttling headers |

The discipline that table encodes is to read the error code as a pointer to a station in the request path rather than as a generic failure. `InvalidTemplate` is validation, so the problem is in the template before any provider; `DeploymentFailed` with a nested error is dispatch, so the problem is in the provider and the nested message is the real diagnosis; `AuthorizationFailed` is authorization, so the problem is a role; `QuotaExceeded` is a provider constraint, so the problem is allocation, not the template; `409` is state, so the problem is concurrency or a name; `429` is the control plane protecting itself, so the problem is request rate. Naming the station is most of the fix.

## Idempotency: why redeploying the same template is safe

A property of ARM that makes infrastructure as code practical is idempotency: deploying the same template twice produces the same result as deploying it once, because ARM reconciles to the declared desired state rather than blindly creating. If a storage account in the template already exists with the declared properties, a redeployment is effectively a no-op for that resource; if a property drifted, the redeployment brings it back to the declared value. This is what lets a pipeline run the same deployment on every commit without piling up duplicate resources, and it is why deterministic naming through `uniqueString` matters: a name that changes every run would create a new resource each time and break idempotency, while a name derived deterministically from stable inputs keeps the deployment repeatable.

Idempotency interacts with the deployment mode. In incremental mode, a redeployment converges the named resources to the template and leaves everything else alone, which is the safe, repeatable behavior most pipelines want. In complete mode, a redeployment reconciles the whole group to the template, which is also idempotent but with the destructive edge that anything not in the template stays deleted. The mental model is that ARM is computing a desired state and reconciling toward it, and idempotency falls out of that reconciliation naturally. When a redeployment surprises you by changing something, it is almost always because the live state had drifted from the template and the deployment did its job by correcting the drift, which is a good argument for treating the template as the source of truth and avoiding out-of-band portal changes that the next deployment will silently revert.

## Nested and linked templates: composing large deployments

A single template that declares everything for a large environment runs into the size and resource-count limits and becomes hard to read and reuse. ARM offers two ways to compose deployments out of smaller pieces. A nested template embeds a child template inside a parent using a `Microsoft.Resources/deployments` resource, so the parent can deploy a self-contained unit with its own scope and parameters. A linked template lives in a separate file, typically hosted at a URI such as a storage account with a SAS token or a template spec, and the parent references it by location, so the same module can be reused across many parent templates.

The composition unlocks reuse and isolation. A networking module, a storage module, and an identity module can each be a linked template, and different environments assemble them with different parameters, which keeps each module focused and testable. Composition also changes the failure boundaries in a useful way: a nested deployment is its own deployment in the history with its own result, so a failure inside it is reported against that nested deployment, which makes a large rollout's failures easier to locate than a single flat deployment where everything is one record. The trade-off is that linked templates must be reachable by ARM at deploy time, which means the hosting location and any access token must be valid for the duration of the deployment, and an expired SAS token on a linked template produces a deployment failure that has nothing to do with the template's contents. Template specs, which store a versioned template as a first-class Azure resource, remove the hosting-and-token problem by letting ARM pull the linked template from a governed, access-controlled resource rather than a URL you manage by hand.

For teams that have outgrown raw JSON, the modern authoring path compiles to exactly these ARM constructs while being far easier to write, and the relationship is worth understanding before you decide where to invest. Bicep is a domain-specific language that transpiles to ARM JSON, so everything in this article about modes, scopes, dependencies, and the request path applies unchanged to a Bicep deployment; the [complete Bicep engineering guide](/2025/01/27/azure-bicep-complete-guide/) covers that authoring layer in depth, and the decision between authoring tools is the subject of the [Bicep versus ARM versus Terraform comparison](/2024/12/30/bicep-vs-arm-vs-terraform/).

## ARM is the management layer too, not only the deployment engine

It is easy to think of ARM as the thing that creates resources and stop there, but the same control plane governs how you organize, secure, and control resources for their whole life. The management features all flow through ARM, and understanding them rounds out the model.

Tags are key-value pairs ARM attaches to resources and resource groups, and they are the backbone of cost attribution, ownership, and automation. A tag such as `environment=production` or `costCenter=platform` lets you filter the activity log, build cost reports, and target automation at exactly the resources that carry the tag. Tags are an ARM concept applied uniformly across resource types, which is why they work the same way whether you are tagging a virtual machine or a storage account.

Resource locks are an ARM mechanism to prevent accidental change or deletion. A `CanNotDelete` lock allows reads and modifications but blocks deletion, and a `ReadOnly` lock blocks both modification and deletion. Locks are evaluated by ARM during the authorization stage, so a delete attempt against a locked resource fails regardless of the caller's role, which makes locks a useful backstop against a fat-fingered delete or, importantly, against a complete-mode deployment trying to remove a resource the template omitted. A lock that blocks a complete-mode delete turns a dangerous mode mistake into a clean failure rather than a data loss, which is one more reason to lock the resources you cannot afford to lose.

Azure Policy is the governance layer ARM enforces. A policy is a rule evaluated against resource properties, and ARM enforces it at deployment time for policies with a deny effect: a policy that denies storage accounts without secure transfer enabled causes a deployment of a non-compliant storage account to fail with a policy violation, before the storage provider ever runs. This is why a template that worked in one subscription fails in another with a policy error: the second subscription carries a deny policy the first did not, and the deployment is rejected at the control plane. Reading a policy denial well means recognizing it as a governance rule rather than a template defect, then either bringing the resource into compliance or, with the right authority, adjusting the policy.

The deployment history is ARM's record of every deployment against a resource group or higher scope, and it is an underused diagnostic resource. Each deployment record carries the template, the parameters, the mode, the outputs, and the per-operation result, so when a deployment failed days ago you can open its record and read exactly which operation broke and why. The history is also where the retention limit mentioned earlier applies, and a frequently deploying pipeline that starts failing on deployment creation may have filled the history, which is cleared by deleting old deployment records. The activity log, a sibling feature, records every control-plane operation with the caller, the time, and the result, which is how you answer "who deleted this resource and when," because the answer is a control-plane operation ARM recorded.

### How do I find out who changed or deleted a resource?

Open the activity log for the resource, resource group, or subscription and filter by operation and time. Because every control-plane action passes through ARM, the activity log records the caller identity, the operation, the timestamp, and the result, so a deletion or a configuration change is traceable to the identity and the moment it happened, which is the starting point for any incident review.

## Naming and tagging: the ARM discipline that scales

The behaviors that cause incidents are dramatic, but the discipline that quietly determines whether a large Azure estate stays manageable is naming and tagging, both of which are ARM constructs you control from the template. A naming convention that encodes the workload, the environment, the region, and an instance marker turns a flat list of resources into something a human can read at a glance, and it makes the deterministic-naming pattern with `uniqueString` work in your favor rather than producing opaque hashes nobody can map back to a purpose. The convention does not need to be elaborate; it needs to be consistent and enforced, ideally through a policy that denies non-conforming names so a misnamed resource fails at the control plane rather than slipping into production. A storage account named with a workload prefix, an environment marker, and a short unique suffix tells an on-call engineer at 2 a.m. exactly what they are looking at, which is worth more than any clever automation.

Tags carry the metadata names cannot. A resource that carries `environment`, `owner`, `costCenter`, and `workload` tags can be found, billed, and acted on as a group, and the cost reports that finance asks for become a tag query rather than a manual reconstruction. Because tags are an ARM concept applied uniformly across resource types, a tag strategy declared in templates and enforced by policy applies the same way to every resource, and an inherited-tag policy can push a resource group's tags down to the resources inside it so the metadata stays consistent even when a deployment forgets to set it. The failure mode to avoid is the half-tagged estate, where some resources carry the tags and others do not, which makes every tag-based report and automation unreliable; the prevention is to enforce required tags through policy so a resource without them fails to deploy, the same control-plane enforcement that makes a deny policy reject a non-compliant resource.

### Why should I enforce naming and tags through policy rather than convention?

Because a convention nobody enforces drifts, and a drifted naming or tagging scheme makes cost reports, automation, and incident triage unreliable. A policy with a deny effect rejects a non-conforming resource at the ARM control plane before it is created, so the standard holds automatically rather than depending on every engineer remembering it, which is the only way consistency survives across a large team and a long-lived estate.

The connection back to the rest of ARM is that naming, tagging, locks, and policy are all the same control plane expressing your intent about how resources are organized and protected, and they are most effective when declared as code in the same templates that create the resources rather than bolted on afterward in the portal. A resource that arrives already named to convention, already tagged, already locked where it matters, and already compliant with policy is a resource the rest of your tooling can reason about; a resource created by hand and tagged later is a gap in every report until someone notices. Treating these as deployment-time concerns, governed by the same templates and policies, is what keeps an estate legible as it grows from a handful of resources to thousands.

## Real-world deployment scenarios and the patterns that handle them

The textbook template that creates one storage account teaches the syntax, but the deployments that cause incidents are the messier ones engineers actually run, and a few recurring patterns are worth naming because each maps to a behavior covered above.

The first is the environment that drifted. A resource group was created by a deployment months ago, then someone changed a setting in the portal to fix an incident, and now the live state no longer matches the template. The next incremental deployment quietly reverts the portal change, because ARM reconciles the named resources to the template, and the engineer who made the portal fix is surprised when their change vanishes. The pattern to adopt is to treat the template as the source of truth and to fold any necessary change into the template rather than the portal, using what-if before each deployment to see exactly what will revert. Drift is not an ARM bug; it is ARM doing its reconciliation job against a state that diverged out of band.

The second is the partial failure. A deployment of ten resources gets through seven and fails on the eighth with a provider error, leaving the resource group in a half-built state. Because ARM dispatches operations and tracks each, the deployment record shows precisely which operations succeeded and which failed, so recovery is targeted: fix the cause of the eighth failure and redeploy, and idempotency ensures the seven that succeeded are reconciled rather than duplicated. The misstep is to tear down the whole group and start over, which throws away seven correct resources; the right move is to read the deployment record, fix the specific failure, and let the idempotent redeployment converge.

The third is the concurrent-deployment conflict. Two pipelines, or a pipeline and a human, deploy into the same resource group at the same time and touch the same resource, producing a 409 conflict because ARM will not let two operations change the same resource simultaneously. The pattern is to serialize deployments that share a target, either by a pipeline concurrency control or by deploying shared infrastructure separately from the per-team resources that change often, so two fast-moving pipelines are not racing on the same network or the same shared account.

The fourth is the cross-environment surprise, where a template that deployed cleanly in development fails in production. The usual causes are a deny policy in production that development lacked, a quota that production has not been granted, a provider not registered in the production subscription, or an identity in the production pipeline missing a role the development identity had. Each maps to a station in the request path, and the diagnosis is to read which station the error names rather than assuming the template changed.

For teams that want the reconciliation discipline of complete mode with safety rails and a managed lifecycle, deployment stacks group a set of resources as a single managed unit with defined behavior for what happens to managed resources when they leave the stack, which addresses the exact danger complete mode carries; the dedicated walkthrough of [Azure deployment stacks](/2025/03/10/azure-deployment-stacks/) covers that lifecycle model and when it earns its place over a plain complete-mode deployment.

## The resource group as ARM's unit of lifecycle and management

The resource group is not just a folder for resources; it is an ARM construct with real semantics that shape how you design deployments. A resource group is a management and lifecycle boundary: the resources inside it share a region for the group's metadata, share a deployment history, can be deleted together as a unit, and are the default scope for role assignments, locks, tags, and policy. Deleting a resource group deletes every resource in it, which is both a convenience for tearing down an environment and a hazard if the group holds more than you think, and it is one more reason the contents of a group should be deliberate rather than accumulated by habit.

Where a resource lives matters because the group is the unit you reason about together. A common and effective pattern groups resources by lifecycle: resources created, updated, and destroyed together belong in one group, while long-lived shared infrastructure such as a hub network or a central Key Vault belongs in its own group with its own deployment cadence and tighter locks. Mixing a fast-churning application's resources with shared infrastructure in one group invites the concurrent-deployment conflicts discussed earlier, because two pipelines with different rhythms end up deploying into the same group, and it makes a complete-mode deployment on the application far more dangerous because the shared resources are now in the blast radius. Separating by lifecycle keeps each group's deployments independent, narrows the blast radius of a complete-mode mistake, and lets locks and policy match the value of what each group holds.

### How should I decide which resource group a resource belongs in?

Group resources by shared lifecycle: things created, changed, and deleted together belong in the same group, while long-lived shared infrastructure belongs in its own group with its own cadence and stronger locks. This keeps deployments independent, narrows the blast radius of a complete-mode deployment, and aligns locks, tags, and policy with the value of each group's contents.

The region you assign to a resource group is a subtle point worth getting right. The group's region stores the group's metadata and its deployment records, not the resources themselves, which can live in other regions. That said, the metadata region still matters for resilience: if the group's metadata region has an outage, control-plane operations against that group can be affected even when the resources are elsewhere, which is an argument for placing a group's metadata in the same region as the bulk of its resources for locality and for spreading critical groups across regions rather than concentrating every group's metadata in one place. This is a low-frequency concern compared to modes and permissions, but it is part of designing groups on purpose.

## Deployment scripts: running imperative steps inside a declarative deployment

ARM is declarative, but real deployments occasionally need an imperative step that no resource type expresses: generating a certificate, seeding a database, calling an external API to register a resource, or computing a value that must come from a script rather than a template function. The deployment script resource, `Microsoft.Resources/deploymentScripts`, runs an Azure CLI or PowerShell script as part of the deployment, executing it in a container that ARM provisions, and returns the script's output back into the deployment so later resources or outputs can use it.

The behavior to understand is that a deployment script runs under a user-assigned managed identity you supply, and that identity, not the original deploying caller, authorizes whatever the script does. This is the same per-identity authorization principle covered earlier, applied to scripts: a script that creates or modifies resources needs its managed identity to hold the roles for those actions, and a script failing with a permission error usually means the script's identity, not the pipeline's identity, is under-privileged. The script also needs somewhere to store its execution state, which the resource handles by provisioning a storage account and a container instance for the duration of the run, both of which ARM cleans up according to the retention you set.

Deployment scripts are powerful and should be used sparingly, because each one is an imperative escape hatch in an otherwise declarative deployment, and the more logic that lives in scripts the less ARM can reason about, preview with what-if, and reconcile idempotently. The guidance is to reach for a deployment script only when no declarative construct does the job, to keep the script idempotent so a redeployment behaves predictably, and to grant its identity the narrow set of roles the script genuinely needs. When you find yourself writing substantial procedural logic in deployment scripts, that is often a signal the work belongs in a separate pipeline stage with proper tooling rather than wedged into the deployment, where it is harder to test and to observe.

### When should I use a deployment script instead of a resource declaration?

Use a deployment script only when an imperative action has no declarative equivalent, such as seeding data, generating a certificate, or calling an external API mid-deployment. Prefer declarative resources for everything ARM can express, because they preview with what-if and reconcile idempotently. Keep any script idempotent and grant its managed identity the minimum roles its actions require.

The thread connecting deployment scripts, the resource group lifecycle, secure parameters, and the rest of this article is that ARM gives you a small number of powerful primitives, and using them well is mostly about restraint and intent: declare what you can, script only what you must, group by lifecycle, state the mode explicitly, preview before you destroy, and let the deploying identity carry exactly the permissions the deployment needs. The engineers who get burned by ARM are almost always the ones who used a powerful default without choosing it; the engineers who find ARM predictable are the ones who chose each behavior on purpose.

## When to use ARM directly and when to reach for something else

ARM JSON is the substrate, but it is not always the layer you should be writing by hand, and being honest about that is part of using ARM well. Hand-authored ARM JSON is verbose, the expression language is awkward for anything beyond simple logic, and the noise-to-signal ratio of a large template is poor. The substrate is always ARM, but the authoring layer is a choice.

### Should I write ARM JSON by hand or use Bicep?

For new work, author in Bicep and let it compile to ARM JSON. Bicep produces the same deployments with the same modes, scopes, and behaviors covered here, but the syntax is concise, the tooling catches errors earlier, and modules are cleaner than linked templates. Write raw ARM JSON only when you must read or patch an existing template or integrate with a tool that emits JSON directly.

The honest guidance breaks down by situation. For brand-new infrastructure as code on Azure, Bicep is the better authoring experience and compiles to exactly the ARM constructs this article describes, so you lose nothing of the model and gain readability, modules, and earlier error detection; the [Bicep complete guide](/2025/01/27/azure-bicep-complete-guide/) is the place to go deep on that layer. For teams already standardized on Terraform across multiple clouds, Terraform talks to the same ARM control plane through its Azure provider and brings its own state model and multi-cloud consistency, and the trade-offs against the Azure-native tools are laid out in the [Bicep versus ARM versus Terraform comparison](/2024/12/30/bicep-vs-arm-vs-terraform/). Raw ARM JSON earns its place in a narrower set of cases: when you must read, debug, or patch an existing JSON template; when a tool exports or consumes ARM JSON directly; when a portal export gives you JSON as a starting point; and when you are learning the platform and want to see the underlying contract without a compiler in the way, which is part of why understanding the JSON pays off even if you author in Bicep. The broader concept of infrastructure as code on Azure, and where ARM sits within it, is covered in the [infrastructure as code overview](/2025/01/06/azure-iac-explained/).

The portal still has a role. For exploration, for a one-off resource you will never need to reproduce, and for inspecting state, the portal is faster than writing a template. The trap is using the portal for anything you need to be repeatable or reviewable, because a portal change leaves no template, no diff, and no history beyond the activity log, and it is exactly the kind of change a later deployment will revert as drift. The rule that scales is portal for exploration and inspection, code for anything that must be repeatable, reviewed, or recovered.

When you want to run these deployments safely rather than read about them, you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), where the sandbox lets you deploy a template, run what-if against it, switch between incremental and complete mode to watch the delete list appear, and trigger and read a real deployment error end to end. Reproducing a complete-mode what-if and a partway-through `AuthorizationFailed` in a throwaway environment is the fastest way to make the behaviors in this article concrete, and the VaultBook command and template library keeps tested examples for the CLI, PowerShell, and Bicep so you start from something that works rather than from a blank file.

## A worked walkthrough: debugging a failed deployment end to end

Theory settles once you trace a real failure from the red banner to the fixed deployment, so here is the diagnostic path on a deployment that fails the way real ones do. Picture a pipeline that deploys a virtual machine, a network interface, a storage account for boot diagnostics, and a role assignment that grants the VM's managed identity read access to a Key Vault. The pipeline reports `DeploymentFailed`, and the instinct is to re-run it, which is the wrong first move because a re-run repeats whatever caused the failure.

The first step is to read the deployment record rather than the pipeline log, because the pipeline log shows the command and the top-level status while the deployment record carries the per-operation result. Pull the failed deployment and its operations:

```bash
# Show the most recent deployment for the group and its overall state
az deployment group show \
  --resource-group rg-insight-prod \
  --name vm-rollout \
  --query "properties.{state:provisioningState, error:error}" -o json

# List each operation in the deployment with its status and the resource it targeted
az deployment operation group list \
  --resource-group rg-insight-prod \
  --name vm-rollout \
  --query "[].{resource:properties.targetResource.resourceName, status:properties.provisioningState, code:properties.statusMessage.error.code}" \
  -o table
```

The operation list is the diagnosis. Suppose it shows the storage account, the network interface, and the virtual machine all `Succeeded`, and the role assignment `Failed` with code `AuthorizationFailed`. That single line collapses the search: three of four operations completed, the deployment got most of the way, and it failed precisely on the role assignment. This is the per-operation authorization behavior in action, where ARM dispatched and authorized each operation as it ran and stopped on the one the deploying identity lacked permission for.

The second step is to read the failed operation's full error, which names the action and the scope:

```bash
az deployment operation group list \
  --resource-group rg-insight-prod \
  --name vm-rollout \
  --query "[?properties.provisioningState=='Failed'].properties.statusMessage" -o json
```

The message names the action that was denied, in this case the write of a role assignment, and the scope it was attempted at, the Key Vault. Now the fix is unambiguous: the pipeline's service principal can create compute, network, and storage resources but lacks the authority to create role assignments, which requires an action the storage and compute roles do not include. The remedy is to grant the service principal a role that includes role-assignment write at the scope the assignment targets, scoped to the specific Key Vault rather than the whole subscription so the grant stays least-privilege. After the grant, the idempotent redeployment converges: the three succeeded resources are reconciled as no-ops and the role assignment, now authorized, completes. The full mechanics of reading and resolving these permission errors live in the dedicated guide on [Azure RBAC AuthorizationFailed errors](/2022/10/10/fix-azure-rbac-authorizationfailed/), and the broader family of template-stage failures is covered in the [ARM template deployment failure guide](/2022/10/24/fix-arm-template-deployment-errors/).

The third step is prevention, which is where the model pays off. Before this deployment ever ran, an enumeration of which identity performs which action would have flagged that creating a role assignment needs a permission the pipeline identity did not hold, and a what-if run would have shown the role assignment as a planned create against a scope the identity could not write to. The general lesson the walkthrough teaches is to start every deployment diagnosis at the operation list, read the failing operation's code as a pointer to a station in the request path, fix the specific cause, and let idempotency converge the rest, rather than tearing down and rebuilding from scratch.

## Template expressions and secure parameter handling

The small expression language inside a template is what turns static JSON into something reusable, and a handful of functions carry most of the weight. The `parameters` and `variables` functions pull values you defined; `concat` joins strings; `resourceId` builds the fully qualified identifier of a resource so other resources and outputs can reference it; `reference` retrieves runtime properties of a resource such as an endpoint that only exists after creation; `uniqueString` produces a deterministic hash for globally unique names; and `resourceGroup` and `subscription` expose context such as the region and the subscription ID. These functions evaluate while ARM builds the deployment, which is why a `reference` to a resource creates an implicit dependency: ARM cannot resolve the reference until the referenced resource exists, so it orders that resource first.

A frequent error is using `reference` where a value is needed at template-build time rather than at resource-runtime, or using it without the dependency the reference implies being satisfiable, which produces a resolution failure. The mental rule is that `resourceId` builds an identifier from names you already know and is safe to use anywhere, while `reference` reads a property that only exists after the resource is created and therefore both implies a dependency and can only be used where a runtime value is acceptable.

Secure parameter handling deserves its own discipline because templates routinely need secrets such as an administrator password or a connection string, and the wrong handling writes those secrets into records that many identities can read. Parameters of type `securestring` and `secureobject` are not recorded in the deployment history, which is the correct type for any sensitive input. The stronger pattern is to keep secrets out of the template and parameter files entirely and to reference them from Key Vault at deploy time, so the secret never appears in source control, in a parameter file, or in the deployment record:

```json
"parameters": {
  "adminPassword": {
    "reference": {
      "keyVault": {
        "id": "[resourceId('Microsoft.KeyVault/vaults', 'kv-insight-secrets')]"
      },
      "secretName": "vmAdminPassword"
    }
  }
}
```

With this pattern, ARM retrieves the secret from Key Vault during the deployment using the deploying identity's access to the vault, and the secret value never lands in the parameter file or the history. This is also why outputs must never carry secrets: an output is recorded in the deployment history, so outputting a key or a connection string defeats the secure-parameter discipline by writing the secret into a readable record. The rule that scales is to accept secrets only as `securestring`, prefer Key Vault references over literal values, and keep secrets out of outputs entirely, fetching them at runtime through a managed identity instead of passing them through the deployment.

### How do I pass a secret to a template without exposing it?

Use a Key Vault reference in the parameter file so ARM fetches the secret from the vault at deploy time, or declare the parameter as `securestring` so its value is not recorded in the deployment history. Never put a secret in a plain string parameter, a committed parameter file, or a template output, since all of those persist the value where other identities can read it.

## The single best way to think about ARM

If you keep one model, keep this one: ARM is a desired-state control plane that authorizes who you are, resolves what you want into an ordered graph, dispatches each piece to the provider that owns it, and reconciles the result against the live state, and almost every behavior that surprises an engineer is a direct consequence of one of those four jobs. A deployment that fails on permissions is the authorization job. A circular-dependency rejection or a parallel creation is the graph job. A provider error buried in a nested `DeploymentFailed` is the dispatch job. A reverted portal change, an idempotent redeployment, and the complete-mode delete are all the reconciliation job. When something unexpected happens, ask which of the four jobs produced it, and the answer points straight at the diagnosis.

That model also tells you where the danger concentrates. The reconciliation job is the powerful and the perilous one, because reconciling to a desired state means removing what is not in the state when you ask it to, which is the complete-mode-deletes rule. Every other behavior is additive or diagnostic; reconciliation is the one that can destroy. So the safety habits cluster there: state the mode explicitly on every deployment, run what-if in complete mode to see the delete list, lock the resources you cannot lose, and treat the template as the single source of truth so drift is corrected on purpose rather than discovered by accident.

## Closing verdict

Azure Resource Manager rewards the engineer who treats it as a system rather than as magic. The investment is small and the payoff is large: learn the four jobs of the control plane, the two deployment modes and which one deletes, the way the dependency graph is built from references rather than from textual order, the four scopes and the resource that forces each, the what-if preview that makes every change reviewable, and the way authorization is evaluated per operation during the deployment rather than all at once before it. With that model, the error codes stop being noise and start being pointers: `InvalidTemplate` is validation, `DeploymentFailed` is a provider, `AuthorizationFailed` is a role, `QuotaExceeded` is allocation, `409` is concurrency, `429` is rate, and a circular-dependency rejection is a graph with no valid order. The deployment that deletes a database is not bad luck; it is complete mode against an incomplete template, and a what-if would have shown it. The deployment that fails partway on permissions is not mysterious; it is the one action the identity lacked, named in the error with the scope it needed. Hold the model, run what-if before anything destructive, keep the template as the source of truth, and ARM becomes the most predictable layer in your stack rather than the one that surprises you. That predictability is the whole point, because the difference between an engineer who pastes a template and one who can reason about why a deployment behaved the way it did is exactly the difference this control plane makes visible.

## Frequently Asked Questions

### Q: What is Azure Resource Manager and what does it do?

Azure Resource Manager is the control plane for every Azure resource, the management API that every tool talks to whether you use the portal, the CLI, PowerShell, Bicep, Terraform, or the REST API directly. It receives each management request, authenticates the caller through Microsoft Entra ID, authorizes the action against role assignments, validates the request, resolves the work into an ordered dependency graph, dispatches each operation to the resource provider that owns that resource type, polls each provider to completion, and returns one consistent result. It governs the control plane, meaning create, read, update, and delete of resources, not the data plane, meaning what you do with a resource once it exists. There is no way to manage Azure resources that bypasses ARM, which is why understanding its rules explains so many otherwise confusing behaviors.

### Q: How is an ARM template structured?

An ARM template is a JSON document with a small set of top-level sections. The `$schema` line declares the template language version and the deployment scope. `contentVersion` is a version string you control for change tracking. `parameters` are the inputs a caller supplies at deploy time, such as a region or a SKU, with optional types, allowed values, and defaults. `variables` are values computed once inside the template to avoid repetition. `functions` hold any user-defined functions. `resources` is the array of resource objects ARM will create or update, each with a `type`, an `apiVersion`, a `name`, usually a `location`, and a `properties` object whose shape the provider defines. `outputs` return values such as a resource ID or an endpoint after the deployment finishes. The resources array is the heart of the template, and the order of resources in it does not affect creation order, which ARM derives from dependencies.

### Q: What is the difference between incremental and complete deployment modes?

Incremental mode, the default, is additive: it creates or updates the resources the template declares and leaves any existing resource not named in the template completely untouched. Complete mode is a full reconciliation: it makes the target resource group match the template exactly, which means any resource that exists in the group but is absent from the template is deleted. The mode is a property of the deployment operation, not of the template, set by the caller through the mode flag. The practical rule is that incremental is safe by default while complete can remove live infrastructure, so complete mode should never run against a shared or production group without a what-if preview that shows the delete list and a human reading it. Most accidental deletions in ARM trace to a complete-mode deployment against a template that did not declare the deleted resource.

### Q: How does ARM order and resolve resource dependencies?

ARM builds a directed dependency graph and creates resources in an order that satisfies every edge, running independent resources in parallel. It learns dependencies two ways. Explicitly, through the `dependsOn` property, an array naming resources that must finish first. Implicitly, through the `reference` and `resourceId` functions, so when one resource refers to another through those functions ARM infers the dependency automatically without any `dependsOn`. The implicit way is cleaner because the dependency lives in the property that uses the other resource. The order of resources in the template's JSON array has no effect on creation order; ARM ignores textual position and obeys only the graph. A circular dependency, where two resources depend on each other, is a hard error because no valid order exists, and it usually comes from over-specified explicit dependencies that the implicit references already cover.

### Q: What does the what-if operation show before a deployment?

The what-if operation computes the difference between the current live state and the desired state your template describes, then returns a per-resource preview without making any change. It shows which resources will be created, which will be modified and exactly which properties change, which will be deleted, and which are unchanged. The complete-mode what-if is the one to make a habit, because it is the only routine way to see the delete list that complete mode will execute before you commit to it. What-if occasionally over-reports a cosmetic property change as a modify because some providers report changes the deployment will normalize, but it reliably catches the dangerous changes such as deletions, which is exactly the asymmetry you want from a safety check. Wiring what-if into a pipeline as a required, human-reviewed gate before production deployments converts ARM's most dangerous behaviors into reviewable plans.

### Q: What deployment scopes does ARM support?

ARM supports four nested scopes. Resource-group scope, the common case, creates resources inside one resource group and is submitted with the group-level deployment command. Subscription scope creates resource groups, policy assignments, and role assignments across a subscription and requires a location for the deployment record. Management-group scope governs policy and access across many subscriptions at once. Tenant scope acts across the whole directory. The scope you must use is dictated by the lowest level the resource lives at: a resource group itself cannot be created by a resource-group deployment because the group is the target, so you create groups with a subscription-scope deployment. The template's `$schema` line must match the scope, and a higher-scope deployment requires a `--location` even when its resources are not regional, which surprises engineers used to the resource-group command that infers the region from the group.

### Q: Why does my ARM deployment fail with InvalidTemplate?

`InvalidTemplate` means the template failed validation before any resource provider ran, so the problem is in the template itself rather than in Azure or your permissions. The common causes are malformed JSON such as a missing comma or brace, a reference to a parameter or variable that is not defined, a bad expression in a function such as a mistyped `resourceId` call, or a schema that does not match the deployment scope you are targeting. The error usually points at the exact line, property, or expression that failed, which is the fastest path to the fix. Confirm the `$schema` matches the scope, validate the JSON locally, and resolve the named expression. Because this error fires at the validation station before dispatch, it is purely a template problem and never a provider, quota, or permission issue, which narrows the search immediately.

### Q: What does a 409 Conflict mean during an ARM deployment?

A 409 Conflict means the change you requested conflicts with the current state of a resource. The most common cause is concurrency: two deployments, or a deployment and a manual change, are touching the same resource at the same time, and ARM will not allow two operations to change one resource simultaneously. Other causes are a repeated operation on a resource that is still mid-change from a previous request, or a resource name that is already in use where the name must be unique. The fix follows the cause: serialize the deployments that share a target so they do not race, wait for an in-flight operation to finish before retrying, or change a name that collides. When a pipeline that ran cleanly yesterday hits a 409 today, the usual culprit is another pipeline or a human deploying into the same resource group concurrently.

### Q: Why does a deployment fail with AuthorizationFailed partway through?

ARM authorizes each operation against the deploying identity's roles when that operation runs, not all at once before the deployment starts, so a deployment can complete several operations and then fail on the one action the identity lacks. A service principal that can create storage and networking but cannot write role assignments will deploy most of a template and then fail exactly on the resource that grants a role. The error names the denied action and the scope it was attempted at, which tells you precisely which role is missing and where. The fix is to grant the deploying identity a role that includes the denied action at the scope the action targets, scoped as narrowly as the deployment needs. If the deployment includes a script running under a managed identity, remember that the script's identity, not the original caller, authorizes the script's actions and needs its own roles.

### Q: How do I register a resource provider before deploying?

A resource provider must be registered in a subscription before it will accept work, and a deployment against an unregistered provider fails saying the resource type is not available. List the registration state with `az provider list` and register a specific one with `az provider register --namespace Microsoft.ContainerService`, substituting the provider you need. Registration is asynchronous, so the command returns quickly while the state moves from `Registering` to `Registered` over a short interval, and a deployment that races ahead of registration can still fail. In pipelines that stand up new subscriptions, register the providers you depend on as an explicit early step and poll with `az provider show --query registrationState` until each reports `Registered`. Most common providers register automatically on first use, so this mainly bites fresh or tightly governed subscriptions where automatic registration was not triggered or was restricted by policy.

### Q: Is complete mode safe to use as a default?

No. Complete mode is a powerful reconciliation tool and the correct choice when a resource group must match its template exactly with no hand-added drift, but it is never a casual default because it deletes any resource in the group that the template does not declare. Using it without care is the most common cause of accidental resource deletion in Azure. If you adopt complete mode, you must also adopt the discipline that the template is genuinely complete, because every resource you forgot to include becomes a delete instruction. Always run what-if in complete mode first to see the delete list, have a human review it, and consider resource locks on anything you cannot afford to lose, since a `CanNotDelete` lock turns a complete-mode delete attempt into a clean failure rather than data loss. For a managed alternative with safety rails around the reconciliation lifecycle, deployment stacks are designed for exactly this need.

### Q: What causes a QuotaExceeded error and how do I fix it?

`QuotaExceeded` is not an ARM template problem; it is a resource provider reporting that your subscription has hit an allocation limit for a resource type in a region. Common quotas include the number of vCPUs of a given virtual machine family in a region, the number of public IP addresses, and the number of storage accounts. The error names the quota and the region, which tells you exactly what is full. The resolution is either to request a quota increase through the portal, which routes to a support process, or to fit within the existing quota by choosing a different region, a smaller VM size, or a different family that has headroom. Reading a `QuotaExceeded` as a template defect sends you debugging JSON that is fine, when the real constraint is the subscription's allocation for that resource in that region, so check current usage against the quota before assuming the template is wrong.

### Q: How do I handle ARM throttling and 429 responses?

A 429 Too Many Requests means the control plane throttled your request because too many ARM operations arrived per subscription or tenant in a short window. The wrong response is an immediate, harder retry, which extends the throttle. The right response is to back off, ideally using the retry interval the response suggests, because the headers carry guidance on when to try again. Well-behaved tools such as the CLI and PowerShell honor those headers automatically; custom automation that calls the ARM REST API directly should implement exponential backoff that respects them. At the design level, a pipeline that fans out many parallel deployments is a common cause, so serializing or rate-limiting deployments removes the throttling rather than fighting it. When automation that worked at small scale starts failing intermittently as it grows, throttling is a leading suspect, and the fix is in how fast you call ARM, not in the templates themselves.

### Q: What is the difference between the control plane and the data plane in ARM?

The control plane is the management surface ARM governs: creating, reading, configuring, and deleting resources, such as making a storage account or assigning a role. The data plane is what you do with a resource after it exists: writing a blob into the account, reading a secret from a Key Vault, or querying a database. ARM authorizes control-plane actions against management roles, and it has nothing to say about data-plane actions, which are governed by their own data roles. This separation explains a frequent confusion where an identity with the Owner role can create and delete a storage account but still receives a 403 trying to read a blob, because reading a blob is a data-plane action that Owner does not grant. Whenever a permission works for managing a resource but fails for using it, the boundary between these two planes is almost always the reason.

### Q: How does ARM make deployments idempotent?

ARM is a desired-state engine, so deploying the same template twice produces the same result as deploying it once: it reconciles the live state to the declared state rather than blindly creating new resources each run. If a resource in the template already exists with the declared properties, a redeployment is effectively a no-op for it; if a property drifted, the redeployment corrects it back to the template value. This is what lets a pipeline run the same deployment on every commit without accumulating duplicates. Idempotency depends on stable naming, which is why deterministic functions such as `uniqueString` derived from a resource group ID matter: a name that changes each run would create a new resource every time and break repeatability. In incremental mode this reconciliation is additive and safe; in complete mode it is also idempotent but carries the destructive edge of keeping absent resources deleted.

### Q: Why did my portal change disappear after the next deployment?

Because ARM reconciles named resources to the template, and your portal change made the live state diverge from the template, so the next deployment corrected the drift by reverting your change. This is not a bug; it is ARM doing its reconciliation job against a state that someone modified out of band. The lesson is to treat the template as the single source of truth and fold any necessary change into the template rather than into the portal, because a portal change leaves no diff, no review, and no record beyond the activity log, and it is exactly the kind of divergence a later deployment will undo. If you must make an emergency portal change during an incident, the follow-up is to capture that change in the template before the next deployment runs, and to use what-if before that deployment so you can see precisely what it intends to revert.

### Q: What is the difference between nested and linked templates?

Both compose a large deployment out of smaller pieces, but they differ in where the child template lives. A nested template is embedded inside the parent template as a `Microsoft.Resources/deployments` resource, so the child JSON is right there in the parent file. A linked template lives in a separate file referenced by location, typically a URI such as a storage account with a SAS token or a template spec, so the same module can be reused across many parents. Nested templates keep everything in one file, which is simple for a self-contained unit; linked templates enable real reuse and cleaner modules at the cost of needing the linked file reachable by ARM at deploy time, where an expired access token produces a failure unrelated to the template's contents. Template specs solve the hosting-and-token problem by storing a versioned template as a governed Azure resource, and Bicep modules compile to these same constructs with a far cleaner authoring experience.

### Q: Why does a template that worked in dev fail in production?

The template is usually fine; the environment differs at a station in the request path. The four common causes are a deny policy in production that development lacked, which rejects a non-compliant resource at the control plane; a quota that production has not been granted, producing `QuotaExceeded`; a resource provider registered in development but not in production, producing a resource-type-unavailable error; and a production pipeline identity missing a role the development identity had, producing `AuthorizationFailed`. Each maps to a specific station, so the diagnosis is to read which station the production error names rather than assuming the template changed between environments. The discipline that prevents these surprises is to keep policy, quota, provider registration, and role assignments as consistent as the environments allow, and to run what-if in production before the real deployment so the environment-specific rejections surface in the preview instead of mid-rollout.

### Q: Can a resource lock stop a deployment from deleting a resource?

Yes, and this is one of the most useful safety backstops in ARM. A `CanNotDelete` lock allows reads and modifications but blocks deletion, and a `ReadOnly` lock blocks both modification and deletion. ARM evaluates locks during the authorization stage, so a delete attempt against a locked resource fails regardless of the caller's role, including a delete that a complete-mode deployment would otherwise perform on a resource the template omitted. That means a lock on a critical database or storage account turns a dangerous complete-mode mistake into a clean failure rather than data loss, because the deployment cannot delete what is locked. The trade-off is that a lock also blocks intentional deletes and some operations a `ReadOnly` lock treats as modifications, so apply locks deliberately to the resources you genuinely cannot afford to lose, and remember to account for them when a legitimate change is unexpectedly blocked.

### Q: What is the deployment history and how long is it kept?

The deployment history is ARM's record of every deployment against a resource group or higher scope, and each record carries the template, the parameters, the mode, the outputs, and the per-operation result. It is an underused diagnostic resource: when a deployment failed days ago, opening its record shows exactly which operation broke and why, and it shows which mode was used, which is how you confirm a complete-mode deployment caused a deletion. ARM retains a limited number of deployments per resource group, after which the oldest records are pruned automatically. A pipeline that deploys very frequently can reach the retention limit and start failing on deployment creation until old records are cleared, which is a failure that looks mysterious until you recognize the history is full. The exact retention count is a value to verify against the current Azure documentation, since these limits are adjusted over time.
