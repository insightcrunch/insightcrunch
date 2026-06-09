---
layout: post
title: "Set Up Azure DevOps Service Connections"
page_title: "Azure DevOps Service Connection Setup: Workload Identity Federation, Least-Privilege Scope, and Pipeline Approvals for Secretless Azure Deployments"
date: 2023-08-07
categories: ["Technology"]
tags: ["Azure", "Azure DevOps", "DevOps", "Security", "Identity", "Cloud Computing"]
excerpt: "An Azure DevOps service connection is your pipeline's credential to Azure. Federate it, scope it least-privilege, and gate it with approvals to deploy safely."
image: "/assets/images/blog/blog-75.webp"
reading_time: 62
author: "gregory-marsh"
last_updated: 2023-08-07
lang: en
---
When a pipeline deploys to Azure, something has to vouch for it. The Azure DevOps service connection is that something: it is the stored credential and trust relationship a pipeline uses to authenticate to your subscription and act on your resources. Get it right and your deployments run unattended, prove who they are without a password sitting in a variable, and touch only the resources they were meant to touch. Get it wrong and you have a long-lived secret that leaks in a log, expires on a Friday afternoon, or hands a compromised pipeline the keys to an entire subscription. The credential choice is not a checkbox at the end of setup. It is the single most consequential security decision you make when you wire delivery to the cloud, and most teams make it by accident.

![Azure DevOps service connection setup with workload identity federation and least-privilege scope - Insight Crunch](/assets/images/blog/blog-75.webp)

This guide builds the endpoint the durable way and names the rule that should govern every choice along the path. Call it the federate-not-store rule: a service connection should authenticate through workload identity federation so that there is no secret to leak, expire, or rotate, and the credential type is chosen before anything else because everything downstream depends on it. The old pattern, a service principal carrying a client secret that some human has to remember to renew, is still the default many teams reach for because it is what the wizard offered them three years ago. It works until the secret expires mid-release or shows up in a debug dump. Federation removes the secret entirely, and once you have seen a pipeline authenticate to Azure with nothing stored, the secret-bearing connection looks like the liability it always was.

You will leave this article able to create a federated service connection, scope it to exactly the subscription or resource group it needs with a least-privilege role, gate its use behind approvals and checks so a production deploy cannot happen unreviewed, verify that the whole chain actually works with a deploy you can watch, and express the result as code so the next environment is a copy rather than a fresh round of clicking. Along the way you will see the misconfigurations that break real pipelines and how to recognize each one from its symptom, because a connection that fails at three in the morning gives you an error message, not an explanation, and the difference between a frustrating night and a two-minute fix is knowing which of a handful of causes you are actually looking at.

## What a Service Connection Actually Is and Why the Credential Type Decides Everything

A service connection in Azure DevOps is a named, reusable definition of how a pipeline authenticates to an external system. For Azure deployments the external system is your Azure Resource Manager (ARM) endpoint, and the connection type is the Azure Resource Manager service connection. The pipeline references the endpoint by name in a task such as `AzureCLI@2` or `AzureResourceManagerTemplateDeployment@3`, and at run time the agent uses the endpoint's identity to acquire an access token and call ARM. Nothing in your YAML carries a password. The connection holds the trust, and the pipeline borrows it for the duration of a job.

The mental model worth holding is that the connection is an identity wearing a permission set. The identity is some principal in Microsoft Entra ID: an app registration (a service principal) or a user-assigned managed identity. The permission set is whatever Azure role-based access control (RBAC) role you have assigned that identity at some scope. The connection itself is the binding that lets a pipeline assume that identity, plus the rules that say which pipelines and which branches may use it. Three separate questions hide inside one endpoint, then: who is the pipeline (the identity), what may it do (the role and scope), and when may a given pipeline borrow it (the approvals and checks). Confusing these three is the source of most trouble, because an endpoint can be perfectly authenticated and still be dangerously over-permissioned, or correctly scoped and still usable by a pipeline that should never have touched it.

### How does a pipeline turn a service connection into an Azure token?

When a job runs a task that names an Azure service connection, the agent reads the connection's identity and credential type, requests a token from Entra ID for the ARM resource, and uses that bearer token on the management API calls the task makes. With a secret-based connection the agent presents the stored client secret to get the token; with federation the agent presents a short-lived assertion that Entra trusts because of a pre-established federation rule. Either way the deploy task sees a token, not a password.

That token exchange is the whole game, and it is where the credential type matters. A service principal with a client secret means a real password lives in the connection, encrypted at rest but extractable by anyone who can edit the endpoint or read it through the API, and it carries an expiry that someone owns the job of renewing. A service principal or user-assigned managed identity configured for workload identity federation means there is no password at all: Entra ID has been told to trust tokens issued by Azure DevOps for that specific organization and service connection, so the agent obtains a federated token, swaps it for an ARM token, and never holds a long-lived secret. The federation relationship is a description of trust, not a credential you can copy. You cannot leak what does not exist.

This is why the federate-not-store rule leads the article rather than trailing it. Every later decision, the scope you grant, the approvals you add, the way you template the endpoint, is easier and safer when there is no secret in the picture. Teams that start with a secret spend the rest of the connection's life managing that secret: rotating it, storing the new value, updating the connection, explaining the outage when someone forgot. Teams that federate spend that energy on the things that actually protect them, the scope and the approvals. The credential type is the first domino, and the series treats the secretless default as the one to reach for unless a genuine constraint forbids it, the same habit that runs through the way managed identities replace stored credentials elsewhere in Azure.

### Is workload identity federation always the right choice?

Federation is the right default for Azure Resource Manager service connections in a modern Azure DevOps organization, because it removes the stored secret and the rotation it demands. The honest exception is a target that cannot participate in the federation trust, such as some sovereign or disconnected environments, or a connection to a system that only accepts a client secret. In those narrow cases a secret-based endpoint is the fallback, with a short expiry and a documented owner. Everywhere else, federate.

There is a second reason to prefer federation that is easy to miss. A federated endpoint is bound to your Azure DevOps organization and to the specific service connection by an Entra federated credential whose subject identifier encodes both. A token issued for one connection cannot be replayed against another, and a secret copied out of a different system cannot impersonate the connection, because there is no secret to copy and the trust is scoped to an exact issuer and subject. The secretless property is the headline, but the bound-to-this-connection property is what makes a federated credential hard to misuse even if part of your pipeline is compromised. A leaked client secret is a portable credential anyone can use anywhere; a federation trust is a rule that only fires for the exact pipeline identity it names.

## The Prerequisites and the Correct Order of Operations

Before you create anything, line up the pieces in the order that prevents rework. The most common reason a service connection setup turns into an afternoon of frustration is doing the steps in the wrong sequence: granting a role before the identity exists, creating the endpoint before the role is assigned, or pointing approvals at an endpoint nobody has scoped yet. Each of those produces a connection that looks created but fails at deploy time, and you debug it backward instead of building it forward.

The prerequisites are concrete. You need an Azure subscription and the right to assign roles in it, which means an Owner or User Access Administrator role at the scope where the connection will operate, because creating a least-privilege assignment is itself a privileged action. You need an Azure DevOps project and at least the endpoint administrator permission in it, since service connections are project-scoped security objects. You need to know your target: the exact subscription, and within it the exact resource group, that the pipeline will deploy into, because the whole point of least privilege is to scope the role to that target and not to the whole subscription out of laziness. And you need to decide, up front, whether the identity will be an app registration or a user-assigned managed identity, because the federation setup differs slightly between them and you do not want to discover that halfway through.

### What is the correct order of operations for setting up the connection?

Create or choose the identity first, then assign it the least-privilege role at the target scope, then create the service connection that references that identity using federation, then add the approvals and checks that gate it, and only then run a verification deploy. Building in that order means each step has what it depends on, and a failure points at the step you just did rather than three steps back.

Holding that order in mind, the dependency chain reads cleanly. The role assignment needs the identity to exist, so the identity comes first. The endpoint needs both the identity and, for a clean verification, the role already in place, so the endpoint comes third. Approvals and checks attach to the connection, so they come fourth. Verification proves the entire chain, so it comes last. When you instead create the connection first through the portal wizard and let it auto-create an app registration and grant Contributor on the whole subscription, you have collapsed three deliberate decisions into one default, and every one of those defaults is the thing you will later wish you had chosen differently. The wizard optimizes for getting you a working connection in two clicks. It does not optimize for the endpoint you actually want, which is federated, narrowly scoped, and gated.

There is a subtlety in the order worth calling out. Workload identity federation has a small bootstrapping wrinkle: the Entra federated credential's subject identifier includes the service connection's own identifier, which does not exist until the endpoint is created. Azure DevOps handles this for you when you let it create the connection with the automatic federation flow, because it creates the connection and configures the matching federated credential in one operation. If you are wiring the federation manually against an identity you already own, you create the connection in a half-configured state to obtain its identifier, then add the federated credential to the identity with the issuer and subject the endpoint expects, then finish verifying the endpoint. Knowing that the connection identifier feeds the federation subject is what keeps the manual path from feeling like a chicken-and-egg problem.

### Which identity should the connection use: app registration or managed identity?

Use an app registration (service principal) for most pipeline service connections, because it is the path the automatic federation flow creates and the one with the broadest tooling support. Choose a user-assigned managed identity when you want the identity's lifecycle tied to Azure resources you already manage as code and to avoid holding an app registration in Entra. Both support federation; both can be scoped least-privilege. The deciding factor is who owns the identity's lifecycle.

The distinction between an app registration and a managed identity here is less about capability and more about ownership and governance, a choice covered in depth where the series [weighs managed identities against service principals](/2024/01/08/managed-identity-vs-service-principal/) as a general pattern. An app registration is an Entra object you create and manage in the directory; a user-assigned managed identity is an Azure resource you create in a resource group and manage with the same Bicep or Terraform that builds the rest of your platform. If your organization treats Entra app registrations as carefully governed objects with their own approval process, a user-assigned managed identity may be faster to provision and easier to keep in code. If your pipelines already lean on app registrations and your tooling expects them, stay with the app registration. Either way the federation mechanics and the least-privilege scoping are the same, and either way you are not storing a secret.

## The Step-by-Step Setup With Working Commands

The cleanest way to create a federated Azure Resource Manager service connection is the automatic flow in the project settings, because it creates the app registration, configures the federated credential with the correct issuer and subject, and assigns a role in one motion. The catch is that the convenient default grants Contributor at the subscription scope, which is exactly the over-permission this article is built to avoid. So the recommended path is to drive the identity and the role yourself, then let the connection bind to them. This section walks the full sequence with commands you can run.

### How do I create the identity and assign a least-privilege role?

Create the app registration and its service principal, capture the application and object identifiers, then assign a narrow role at the resource group scope rather than the subscription scope. The role grant is the security boundary, so assign the least-privilege role that still lets the pipeline do its job, and assign it at the smallest scope that contains every resource the pipeline touches.

Start by creating the app registration and reading back the identifiers you will need:

```bash
# Create the app registration that will back the service connection
az ad app create --display-name "sc-shop-prod-deploy"

# Capture the appId from the output, then create the service principal
APP_ID=$(az ad app list --display-name "sc-shop-prod-deploy" --query "[0].appId" -o tsv)
az ad sp create --id "$APP_ID"

# The service principal objectId is what role assignments target
SP_OID=$(az ad sp show --id "$APP_ID" --query "id" -o tsv)
echo "appId=$APP_ID  spObjectId=$SP_OID"
```

With the identity in place, assign the role at the resource group scope. This is the line that decides how much damage a compromised pipeline could do, so it deserves a moment of thought rather than a reflexive Contributor on the subscription:

```bash
SUB_ID=$(az account show --query id -o tsv)
RG="rg-shop-prod"

# Least-privilege: Contributor scoped to ONE resource group, not the subscription
az role assignment create \
  --assignee "$APP_ID" \
  --role "Contributor" \
  --scope "/subscriptions/$SUB_ID/resourceGroups/$RG"
```

Contributor at a single resource group lets the pipeline create and manage resources inside that group and nothing outside it. If the pipeline only deploys a web app and a storage account, you can go narrower still with the resource-specific data and management roles, but resource group Contributor is the sensible starting point that most deploy pipelines need and the one that keeps a breach contained to a single group rather than an entire subscription.

### How do I create the federated service connection that uses this identity?

Create an Azure Resource Manager service connection with the workload identity federation authentication scheme, point it at the app registration you created, and let Azure DevOps configure the federated credential. The endpoint holds no secret; it holds the identity reference and the federation trust. After creation, confirm the endpoint verified successfully before you rely on it.

In the project, open the service connections settings, choose a new Azure Resource Manager connection, and select the workload identity federation scheme rather than the secret-based scheme. When you choose to use an existing identity, supply the application identifier and the tenant, select the subscription as the scope level, and complete the flow. Azure DevOps writes a federated credential onto the app registration whose issuer is the Azure DevOps token service and whose subject encodes your organization and this connection, so Entra will trust tokens that the pipeline presents on behalf of exactly this connection and no other.

If you prefer to script the endpoint rather than click it, you can define it with the Azure DevOps CLI from a JSON specification. The shape that matters is the authentication scheme set to the federation type and the absence of any secret field:

```bash
# Service connection defined for workload identity federation (no secret)
cat > sc.json << 'JSON'
{
  "name": "sc-shop-prod-deploy",
  "type": "azurerm",
  "url": "https://management.azure.com/",
  "authorization": {
    "scheme": "WorkloadIdentityFederation",
    "parameters": {
      "tenantid": "<TENANT_ID>",
      "serviceprincipalid": "<APP_ID>"
    }
  },
  "data": {
    "subscriptionId": "<SUB_ID>",
    "subscriptionName": "<SUB_NAME>",
    "scopeLevel": "Subscription",
    "creationMode": "Manual"
  }
}
JSON

az devops service-endpoint create \
  --service-endpoint-configuration sc.json \
  --org "https://dev.azure.com/<your-org>" \
  --project "<your-project>"
```

With `creationMode` set to manual you are telling Azure DevOps that you own the identity, so it will not try to create an app registration or assign a role for you. That is exactly what you want, because you already created the identity and assigned the narrow role yourself. The federated credential on the app registration still needs the issuer and subject that match this endpoint; the automatic portal flow writes those for you, and when you script the connection you add the matching federated credential to the app registration with `az ad app federated-credential create`, using the issuer and subject values the connection's details page displays after creation.

### What does the pipeline YAML look like once the connection exists?

The pipeline references the endpoint by name in any Azure task, and the task acquires a token through the endpoint automatically. No secret variable, no login command with a password, nothing stored in the repository. The connection name is the only coupling between the pipeline and the credential, which is exactly the separation you want.

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main

pool:
  vmImage: ubuntu-latest

stages:
  - stage: Deploy
    jobs:
      - deployment: DeployProd
        environment: production   # environment carries the approval gate
        strategy:
          runOnce:
            deploy:
              steps:
                - task: AzureCLI@2
                  inputs:
                    azureSubscription: 'sc-shop-prod-deploy'  # the connection name
                    scriptType: bash
                    scriptLocation: inlineScript
                    inlineScript: |
                      az group show --name rg-shop-prod
                      az deployment group create \
                        --resource-group rg-shop-prod \
                        --template-file infra/main.bicep
```

The `azureSubscription` input is the service connection name despite the field being called subscription, a naming quirk that confuses newcomers. The task uses the connection's federated identity to authenticate, runs against the resource group the role was scoped to, and would fail with an authorization error if it reached for anything outside that group. The pipeline carries no credential of its own; it borrows the connection's identity for the life of the job and gives it back. This division between the deploy logic in YAML and the credential in the endpoint is the same separation the [deeper treatment of pipeline structure](/2025/01/13/azure-devops-pipelines-deep-dive/) relies on, where the endpoint is the trust boundary and the YAML is just the work.

## The Settings the Defaults Get Wrong

The wizard is fast, and fast is the problem. Three of its defaults are the settings you will most regret, and each one trades a moment of convenience now for a recurring liability later. Naming them plainly makes the better choice obvious.

The first default that misleads is the credential type. The classic Azure Resource Manager connection offered a service principal with an automatically generated client secret, and for years that was the path of least resistance. A secret-based connection works on the day you create it and fails on the day the secret expires, which in many tenants is a year out and therefore a forgotten time bomb. The default still nudges some teams toward a secret because it is the pattern they know. Federation is the setting to choose instead, and choosing it is the difference between a connection you maintain and one you create and forget in the good sense.

The second default that misleads is the scope. When the automatic flow creates the role assignment, it grants Contributor at the subscription level, because that is the broadest scope that guarantees the pipeline can do whatever it is asked. Subscription Contributor means the pipeline can create, modify, and delete any resource in the subscription, including resources owned by other teams that happen to share it. The setting to change is to assign the role at the resource group that actually contains the deployment target, and to choose a role narrower than Contributor when the pipeline's real needs are narrower. The wizard optimizes for never hitting a permission error. You should optimize for the blast radius staying small when something goes wrong.

The third default that misleads is the pipeline authorization. A new endpoint can be configured to grant access permission to all pipelines, which means any pipeline in the project, including one a colleague writes next week or one an attacker injects through a pull request, may use the endpoint without a further approval. The setting to change is to turn off the grant-to-all-pipelines option and authorize the connection per pipeline, so that using the connection from a new pipeline is a deliberate act rather than an inherited default. This single toggle is the difference between a connection that any pipeline can borrow and one that only the pipelines you trust can.

### Why is subscription-scoped Contributor the wrong default for a deploy endpoint?

Subscription Contributor lets the endpoint touch every resource in the subscription, so a compromised or buggy pipeline can damage workloads it was never meant to see. Scoping the role to the resource group the pipeline deploys into limits the blast radius to that group. The pipeline still does its job; it simply cannot reach beyond it. Narrow scope is free insurance.

The blast-radius argument is the one to internalize, because it reframes least privilege from a compliance chore into a practical safeguard. Imagine the pipeline is fine but a dependency in the build is not, and an attacker runs arbitrary Azure CLI in the deploy job. With subscription Contributor, that attacker can enumerate and delete every resource group in the subscription, exfiltrate data from storage accounts other teams own, and create resources that bill to your account. With the role scoped to one resource group, the same attacker is boxed into that group, can damage only what lives there, and trips authorization errors the moment they reach outward, which is also a signal your monitoring can catch. The narrow scope did not slow your deploys at all. It simply ensured that the worst day was contained.

### Should I let all pipelines use the connection or authorize them individually?

Authorize pipelines individually. The grant-to-all-pipelines default means any pipeline in the project, present or future, can borrow the connection's identity, which is convenient and dangerous in equal measure. Turning it off forces an explicit authorization the first time a pipeline uses the connection, so a new or malicious pipeline cannot quietly inherit production deploy rights. The friction is small and the protection is real.

This setting interacts with pull-request safety in a way that is worth spelling out. If the grant-to-all-pipelines option is on and a fork or a pull request can trigger a pipeline that names the endpoint, an outside contributor's code could run with your endpoint's identity. Per-pipeline authorization closes that door for connections, and you pair it with the pipeline-level controls that restrict which triggers and which branches may run privileged stages at all. The connection authorization and the branch controls are two layers of the same defense: decide which pipelines may borrow the identity, and decide under what conditions those pipelines may run the stages that use it.

## Gating the Connection With Approvals and Checks

An endpoint that is federated and narrowly scoped is still usable by an automated run the instant code merges, and for a production target that is rarely what you want. Approvals and checks are the mechanism that gates an endpoint, turning the question who may use this credential into when and under what conditions. Azure DevOps lets you attach these gates in two related places, and understanding the difference keeps you from gating the wrong thing.

The first place is the service connection itself, under its approvals and checks. A check attached to the connection fires whenever any pipeline tries to consume the connection in a stage, regardless of which pipeline or which environment. The available checks include a manual approval that pauses the run until a named approver signs off, a business-hours check that holds the run until a permitted window, a branch control check that allows the connection only from specified branches, and an invoke check that calls out to a function or REST endpoint for a policy decision. Attaching a manual approval and a branch control directly to the production endpoint means the endpoint cannot be consumed from an unexpected branch and cannot be consumed at all without a human signing off, no matter which pipeline asks.

The second place is the environment, the named target a deployment job declares. Environments carry their own approvals and checks, and because a deployment job runs against an environment, the environment's approval gates the deploy regardless of which connection it uses. The two layers compose: the environment approval gates the act of deploying to production, and the connection check gates the use of that specific credential. For a high-stakes production deploy you often want both, so that the deploy is approved as an act and the credential is approved as a resource.

### How do I require a human approval before a production deploy uses the connection?

Attach a manual approval check to the production service connection, or to the production environment the deployment job targets, and name the approvers. When a run reaches the gated stage, it pauses and notifies the approvers; the endpoint is not consumed and no Azure changes happen until someone approves. This turns an automatic production deploy into a reviewed one without adding a credential or a manual step to the pipeline.

In practice you add the manual approval through the endpoint's approvals-and-checks panel, choose the approvers, and optionally set instructions and a timeout. The behavior to understand is that the check evaluates at stage level when the connection is first consumed, so the run does all its build and test work, reaches the deploy stage, and then waits. Approvers see the run, the stage, and the connection, and approve or reject. Because the gate is on the connection rather than buried in a single pipeline, every pipeline that consumes the production endpoint inherits the same approval, which is exactly the consistency you want: there is no path to production that skips the gate because someone wrote a new pipeline that forgot to add it.

### What is the difference between gating the endpoint and gating the environment?

A connection check gates the use of one credential wherever it is consumed; an environment check gates deployments to one named target whatever credential they use. Gating the connection protects the credential as a resource; gating the environment protects the target as a place. For production you often want both, so that neither a new pipeline nor a new connection can reach production unreviewed.

The reason both layers earn their place is that they fail safe in different directions. If someone creates a new endpoint to production but forgets the gate, the environment approval still catches the deploy. If someone deploys to production through an ungated environment by mistake, the endpoint check still catches the credential use. Two independent gates mean a single oversight does not open an unreviewed path to your most important target. This belt-and-suspenders posture is the series habit of designing so that one forgotten setting does not become an incident, and it costs you only the few minutes it takes to configure the second gate.

## The Verification Step That Proves It Worked

A service connection that exists is not a service connection that works. The verify button on the connection details page confirms that Azure DevOps can obtain a token for the identity, which is necessary but not sufficient, because a connection can verify and still fail at deploy time when the identity lacks the role on the target. Real verification means running a deploy you can watch and confirming it touched what it should and was refused what it should not.

The fastest meaningful check is a read against the target resource group through the connection, because a read proves authentication and basic authorization without changing anything. A pipeline step that runs `az group show` against the scoped resource group through the endpoint will succeed only if the identity authenticated and holds at least Reader on that group. Follow it with a what-if deployment, which evaluates the template against the live environment and reports the changes it would make without applying them, so you confirm the identity can plan a deployment before you let it perform one.

```yaml
- task: AzureCLI@2
  displayName: 'Verify connection authenticates and is scoped correctly'
  inputs:
    azureSubscription: 'sc-shop-prod-deploy'
    scriptType: bash
    scriptLocation: inlineScript
    inlineScript: |
      set -e
      # Proves authentication and that the identity can see the target group
      az group show --name rg-shop-prod --query name -o tsv
      # Proves the identity can plan a deployment without applying it
      az deployment group what-if \
        --resource-group rg-shop-prod \
        --template-file infra/main.bicep
      # Proves the scope boundary: this SHOULD fail with an authorization error
      az group show --name rg-some-other-team 2>&1 | grep -i "authoriz" && \
        echo "Correctly denied outside the scoped group" || \
        echo "WARNING: connection can see groups it should not"
```

### How do I confirm the endpoint is scoped correctly and not over-permissioned?

Run a step that deliberately reaches outside the intended scope and confirm it is denied. If the connection can read a resource group it has no business touching, the role was assigned too broadly. The negative test is more informative than the positive one: a deploy that works tells you the identity has enough permission, but only a denied reach tells you it does not have too much.

That negative test is the verification step most teams skip, and it is the one that catches the over-permission this article keeps warning about. A connection scoped to one resource group should be refused when it tries to enumerate another team's group, and seeing that refusal in the run log is the proof that your least-privilege scope actually holds. If instead the reach succeeds, the role was assigned at the subscription rather than the group, and you have found the misconfiguration before it found you. Building the negative check into your first verification deploy means the connection is born with its boundary proven, not assumed.

### How do I confirm there is genuinely no secret stored in the endpoint?

Inspect the endpoint's authorization scheme through the API or the details page and confirm it reads as workload identity federation, not service principal with a secret. A federated connection shows the issuer and subject of its federated credential and no secret field; a secret-based connection shows a client secret with an expiry date. The presence of an expiry date is the tell: federation has none, because there is nothing to expire.

This check matters because connections migrate over time and a team can believe it federated when it did not. Pulling the endpoint definition and confirming the scheme is the federation type, with no secret and no expiry, is a one-minute audit that confirms the headline property holds. If you find an expiry date, the endpoint is still secret-based and is still on a clock, and converting it to federation is the fix. Running this audit across every Azure connection in a project is how you find the secret-bearing stragglers that will otherwise surprise you on the day they expire.

## The Common Misconfigurations and Their Symptoms

Most service connection failures are one of a small set of recurring patterns, and once you can name them you stop debugging in the dark. Each pattern below pairs the way it shows up at run time with the setup step that prevents it, because the symptom is what you see at three in the morning and the setup step is what you wish you had done at noon.

### Why did my pipeline break when the service connection secret expired?

A secret-based connection stops authenticating the moment its client secret expires, and the symptom is a sudden authentication failure on a pipeline that worked yesterday, often phrased as an invalid client secret or a failure to acquire a token. Nothing in your code changed; the credential aged out. The fix in the moment is to rotate the secret, and the fix forever is to convert the connection to workload identity federation so there is no secret to expire.

This is the single most common production incident tied to service connections, and it is entirely self-inflicted by the choice of a secret-based endpoint. The secret has an expiry the day it is created, usually months out, and the person who created it has often moved on or forgotten by the time it lands. The pipeline fails on a release day, the on-call engineer burns an hour discovering that the credential rather than the code is at fault, and someone rotates the secret under pressure. The setup step that prevents the entire episode is the federate-not-store rule applied at creation: a federated endpoint has no secret and therefore no expiry, and this class of incident simply cannot occur. If you are migrating an existing secret-based connection, the move to federation is the durable fix, and it is the same secretless pattern the [GitHub equivalent reaches for when it configures OpenID Connect](/2023/08/14/configure-github-actions-oidc/) instead of storing an Azure secret in the workflow.

### Why does my deploy fail with an authorization error even though the connection verified?

The connection authenticated but the identity lacks the role it needs on the target, so verification passed (it only checks that a token can be obtained) while the deploy fails with a 403 or an authorization-failed message naming the action and the scope. The symptom names the operation it could not perform, such as a write on a resource group. The fix is to assign the missing role at the correct scope, and the prevention is to assign the role before you rely on the endpoint rather than after the first failure.

The trap here is that the verify button gives false confidence. Verification confirms the federation trust and the token exchange; it does not confirm that the identity can actually do anything in Azure, because authentication and authorization are separate. A brand-new app registration with no role assignment will verify happily and then fail every deploy, because it can prove who it is but is permitted to do nothing. Reading the error closely is the diagnosis: Azure tells you the exact action that was denied and the exact scope, so you assign the role that grants that action at that scope and no broader. This separation of authentication from authorization is the same distinction that sits underneath [service principal authentication failures](/2023/01/30/fix-service-principal-auth-error/) generally, where the message that looks like a login problem is often a permissions problem wearing a login problem's clothes.

### Why can my pipeline touch resources it should not?

The role was assigned at the subscription scope rather than the resource group scope, so the endpoint's identity holds Contributor across the whole subscription and the symptom is that a deploy meant for one group can read, write, or delete resources in others. You usually discover this during a security review or, worse, after a pipeline modifies something it should never have reached. The fix is to remove the broad assignment and re-grant the role at the resource group scope, and the prevention is to scope at creation rather than accepting the wizard's subscription default.

The reason this lingers undetected is that an over-scoped connection works perfectly for its intended job; the extra permission is invisible until something exploits it. A deploy pipeline scoped to the whole subscription deploys its one app exactly as well as a correctly scoped one would, so nothing prompts you to fix it until a review surfaces it or an incident weaponizes it. The negative verification test described earlier is what surfaces it early: a connection that can read another team's resource group is over-scoped, full stop. Re-scoping is a matter of deleting the subscription-level role assignment and creating a resource-group-level one, and doing it deliberately at creation is far cheaper than doing it under audit pressure later.

### Why does the same connection behave differently across environments?

One endpoint is being reused across development, staging, and production, so a change to its scope, its approvals, or its identity affects all three at once and the symptom is that tightening production accidentally breaks development, or that development's looseness leaks into production. The fix is to create a separate endpoint per environment, each scoped to that environment's resource group and gated with that environment's approvals. The prevention is to treat one connection as one environment's credential from the start.

Reusing a single connection across environments feels efficient and is a false economy, because the whole value of a connection is that it carries a specific identity, a specific scope, and specific gates. When one endpoint serves three environments it must be scoped broadly enough for all of them, which means it is over-scoped for the least privileged of them, and its approvals must be permissive enough for the most automated of them, which means production inherits development's looseness. Splitting into one endpoint per environment lets production be tightly scoped and heavily gated while development stays fast and open, which is the entire point of having environments. The cost is a few more connections; the benefit is that each one means exactly what its name says.

### Why does my connection fail only from a pull-request build?

The connection's grant-to-all-pipelines option is off (as it should be) but a pull-request trigger is running a pipeline that has not been authorized to use the endpoint, so the symptom is a failure that appears only on pull-request runs while merged-branch runs succeed. Alternatively, if the option is on, the opposite danger appears: a pull request from a fork can consume the endpoint, which is a security problem rather than a failure. The fix depends on which you intend: authorize the specific pipeline if the pull-request build legitimately needs the connection, or confirm the branch control check is blocking pull-request branches if it should not have access at all.

This pattern is where connection authorization and branch controls meet pull-request safety. A privileged connection should generally not be reachable from pull-request builds, because pull requests can carry untrusted code, so the desired behavior is often that the endpoint is refused on pull-request branches and that is working as intended. When a pull-request build genuinely needs a low-privilege endpoint (to run a what-if against a sandbox, say), you authorize that pipeline explicitly and scope the connection to the sandbox only. The symptom of a pull-request-only failure is therefore not always a bug; it is sometimes the branch control doing its job, and reading the check result tells you which.

### Why does the connection break after the identity or its federated credential changes?

The federated credential's subject must match the issuer and subject the connection presents, so if the app registration is recreated, the federated credential is deleted, or the endpoint is recreated with a new identifier, the trust breaks and the symptom is a token-acquisition failure that mentions a missing or mismatched federated credential. The fix is to re-add the federated credential with the issuer and subject the endpoint expects, which the connection details page displays. The prevention is to treat the identity, the federated credential, and the connection as one coupled unit and to recreate them together when you recreate any of them.

The coupling is the thing to remember. A federated connection is not just an identity reference; it is an identity that has been told to trust tokens from a specific issuer and subject, and that subject encodes the endpoint. Delete or recreate one half of the pair and the trust no longer matches. This is the federation analogue of the expired-secret problem, except that it fails on a configuration change rather than a clock, and the diagnosis is to compare the issuer and subject on the app registration's federated credential against the values the endpoint expects. When they match, tokens flow; when they drift, they do not.

## Making the Configuration Repeatable as Code

A connection you click together once is a connection nobody can reproduce, audit, or recreate when it breaks. The configuration that matters here splits into two layers, and both belong in source control. The Azure-side layer is the identity and its role assignment, which Bicep or Terraform owns alongside the rest of your platform. The Azure DevOps-side layer is the connection and its checks, which the Azure DevOps CLI or the REST API can create from a definition you keep in the repository. Treating both as code means a new environment is a parameterized copy rather than a fresh round of manual setup, and an audit is a diff against the repository rather than a tour of the portal.

### How do I express the identity and least-privilege role as code?

Define the user-assigned managed identity and its role assignment in Bicep or Terraform, scoping the role to the target resource group, so the identity and its permission are provisioned and version-controlled together. This makes the least-privilege scope reviewable in a pull request and reproducible across environments, and it means the answer to who can deploy here and what can they do lives in the same repository as the infrastructure itself.

A user-assigned managed identity is the cleaner choice for an as-code identity, because it is an Azure resource rather than an Entra app registration and therefore lives naturally in the same template as everything else. The Bicep below provisions the identity and grants it Contributor on the resource group it sits in, which is the least-privilege pattern when the pipeline deploys only into that group:

```bicep
// identity.bicep - identity plus least-privilege role, scoped to this RG
param location string = resourceGroup().location

resource deployId 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-shop-prod-deploy'
  location: location
}

// Contributor on THIS resource group only
var contributorRoleId = 'b24988ac-6180-42a0-ab88-20f7382dd24c'

resource roleAssign 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, deployId.id, contributorRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', contributorRoleId)
    principalId: deployId.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

output identityClientId string = deployId.properties.clientId
output identityPrincipalId string = deployId.properties.principalId
```

Because the role assignment names the resource group as its implicit scope (the deployment runs at the group level), the grant cannot accidentally widen to the subscription, and a reviewer can see the exact role and the exact scope in the pull request. Deploying this template to a new environment's resource group produces an identically scoped identity there, which is how you get one endpoint per environment without one round of clicking per environment. The infrastructure-as-code discipline that owns the rest of your platform owns the deploy identity too, which is the same reasoning the broader treatment of infrastructure as code applies to every other resource.

### How do I express the service connection and its checks as code?

Define the endpoint with the Azure DevOps CLI or REST API from a JSON specification stored in the repository, with the authentication scheme set to federation and no secret, and add the approval and branch-control checks through the API as well. Keeping the connection definition in source means recreating it is a command rather than a memory, and reviewing its scope and gates is a diff rather than a portal walkthrough.

The connection definition shown earlier is the artifact you keep; you parameterize the identity client identifier, the tenant, and the subscription so the same definition produces a development connection and a production endpoint from different parameter files. The checks are added after creation through the pipeline-permissions and checks endpoints, which let you script the per-pipeline authorization (rather than grant-to-all) and the manual approval. The result is that the entire endpoint, its identity reference, its federation, its per-pipeline authorization, and its approval gate, reconstructs from files in the repository, which is what makes it auditable. When a reviewer asks how production deploys are gated, the answer is a file, not a tour.

There is one honest limit to acknowledge. The federated credential on the identity encodes the connection's identifier, which Azure DevOps assigns at creation, so the federation trust has a small bootstrapping step that the fully automatic portal flow hides and a scripted flow must handle by reading the connection's identifier after creation and writing the matching federated credential. This is a solved problem, not a blocker, and handling it once in a setup script means every subsequent environment inherits the same reliable sequence. The reward for crossing that small bump is a connection that is reproducible end to end, which is worth far more than the two clicks the portal saved you.

## A Worked Migration From a Stored Secret to Federation

The most valuable thing many teams can do is convert an endpoint they already run. The scenario is familiar: a pipeline has deployed reliably for a year through an Azure Resource Manager endpoint that authenticates with a client secret, and the secret is approaching its expiry. The reflex is to generate a new secret and update the connection, which buys another year before the same fire drill repeats. The better move is to spend the same maintenance window converting the connection to federation, after which the fire drill never recurs because there is no secret left to age. This section walks that conversion end to end so you can do it without an outage.

Begin by capturing the current state, because you will want to confirm afterward that the identity and its permissions did not change, only the way the connection authenticates. Read the endpoint's identity and the roles that identity holds, so you have a baseline to compare against:

```bash
# Identify the app registration the existing connection uses, then list its roles
APP_ID="<existing-appId-from-connection-details>"
SP_OID=$(az ad sp show --id "$APP_ID" --query id -o tsv)

# Baseline the role assignments so you can confirm they are unchanged after migration
az role assignment list --assignee "$APP_ID" \
  --query "[].{role:roleDefinitionName, scope:scope}" -o table
```

With the baseline recorded, add a federated credential to the existing identity rather than creating a new one, so that the same principal keeps the same role assignments and only gains a new way to authenticate. The federated credential needs the issuer and subject that the converted endpoint will present, which you read from the connection after switching its scheme, so the practical sequence is to edit the connection to the federation scheme first, read the issuer and subject it now expects, and then write the matching credential:

```bash
# After switching the connection to the federation scheme in the UI or API,
# read the issuer and subject it expects, then add the federated credential.
cat > fic.json << 'JSON'
{
  "name": "azuredevops-shop-prod",
  "issuer": "<issuer-from-connection-details>",
  "subject": "<subject-from-connection-details>",
  "audiences": ["api://AzureADTokenExchange"]
}
JSON

az ad app federated-credential create --id "$APP_ID" --parameters fic.json
```

### How do I migrate without an outage?

Add the federated credential while the existing secret is still valid, switch the connection to the federation scheme, verify it authenticates, run a deploy through it, and only then delete the old secret. Keeping the secret in place until federation is proven means you always have a working credential, so the migration is reversible at every step and the pipeline never loses its ability to deploy.

The no-outage property comes from ordering the steps so a working credential always exists. While the old secret is still live, the identity can authenticate the old way, so nothing breaks while you add the federated credential. After you switch the endpoint to federation and verify it, run a real deploy (or at least a what-if) to prove the new path works against the actual target, not just that a token can be obtained. Once that deploy succeeds, the secret is dead weight, and removing it is the final step that makes the migration complete. If anything goes wrong before that final step, the secret is still there as a fallback, so you can pause and diagnose without a production pipeline stuck unable to authenticate. This reversibility is what turns a nerve-wracking credential change into a routine one.

### How do I confirm the migrated endpoint kept the same permissions?

After the migration, list the identity's role assignments again and compare them to the baseline you captured before starting. They should be identical, because you converted how the connection authenticates without touching what it is allowed to do. If the assignments differ, something in the migration recreated the identity or altered its roles, and you reconcile against the baseline before trusting the connection.

This comparison catches a subtle failure mode. A careless migration that recreates the app registration rather than editing the existing one produces a new principal with no role assignments, which verifies (it can get a token) and then fails every deploy with an authorization error, exactly the false-confidence trap the verification section warned about. By baselining the role assignments before the migration and diffing afterward, you confirm that the same identity carries the same permissions and only its authentication method changed. The migration is complete when three things are true: the connection authenticates through federation, the identity holds the same roles at the same scopes it held before, and the old secret has been removed so there is nothing left to expire. At that point the endpoint has shed its recurring maintenance entirely.

## Choosing the Right Role Below Contributor

Contributor scoped to a resource group is the sensible starting point, but it is not always the right ending point, because Contributor can create and delete nearly anything in its scope and many pipelines need far less. The discipline of least privilege does not stop at scope; it continues into the role itself, and a pipeline that only updates an app or only writes blobs should hold a role that only does that. Narrowing the role beyond Contributor is the last mile of containment, and it is the difference between a pipeline that could delete the database it deploys next to and one that could not.

Azure ships a large catalog of built-in roles, many of them tightly scoped to a single service or a single data plane, and choosing among them is a matter of matching the role's allowed actions to the operations the pipeline actually performs. A pipeline that deploys only an App Service can often hold Website Contributor rather than full Contributor, which lets it manage the web app without granting authority over unrelated resources in the group. A pipeline that only pushes container images needs a registry push role rather than the authority to manage the registry itself. A pipeline that writes data to a storage account needs a data-plane role such as Storage Blob Data Contributor rather than a management role that could reconfigure or delete the account. Each substitution shrinks what a compromised pipeline could reach.

### When should I use a custom role instead of a built-in one?

Use a built-in role whenever one matches the pipeline's actions closely, because built-in roles are maintained by Microsoft and need no upkeep. Reach for a custom role only when no built-in role fits and the gap matters, defining a role with exactly the actions the pipeline performs. A custom role is more work to maintain, so it earns its place only when least privilege genuinely requires actions no built-in role bundles correctly.

The trade-off with a custom role is maintenance against precision. A custom role lets you enumerate the exact management and data actions a pipeline needs and nothing more, which is the tightest possible grant, but you own that role definition forever, updating it whenever the pipeline's needs change or Azure adds an action the pipeline should hold. For most pipelines a built-in role lands close enough that the maintenance cost of a custom role is not worth the marginal tightening, so the practical rule is to start from the narrowest built-in role that covers the pipeline's actions and only define a custom role when the narrowest built-in role still grants meaningfully more than the pipeline uses. When you do define one, scope it to the resource group like any other assignment, and keep its definition in the same code that provisions the identity so its actions are reviewable.

### How do I find the minimum role a pipeline actually needs?

Run the pipeline with a candidate role, observe which operations succeed and which are denied, and adjust the role until every operation the pipeline must perform succeeds and nothing more is granted. The activity log records the actions the identity attempted, so you can read the exact operations the pipeline needs and match them to a role rather than guessing. Start narrow and widen only to the demonstrated need.

This empirical approach beats reasoning about roles in the abstract, because a pipeline's real action set is often smaller than its author assumes. Assign a narrow candidate role, run the pipeline, and let it tell you what it is missing through the authorization errors it raises, which name the exact action and scope denied. Add only the role or permission that covers that specific action, then run again, repeating until the pipeline completes. The end state is a role grant derived from the pipeline's demonstrated behavior rather than from a cautious over-estimate, which is least privilege established by evidence. Recording the final role in code means the next environment inherits the same tight grant, and the activity log remains the place you return to whenever the pipeline's needs change and you must adjust the role.

## How the Federated Token Exchange Actually Works

It is worth understanding the token exchange one level deeper than the setup, because the mechanism explains why federation has the security properties it does and why the issuer and subject must match exactly. The exchange is not magic; it is a specific, inspectable sequence of token requests, and seeing it laid out demystifies both why it is secretless and why a subject mismatch breaks it so cleanly.

When a pipeline job consumes a federated endpoint, the Azure DevOps agent first obtains a token from the Azure DevOps token service that asserts the identity of this organization and this service connection. That assertion is short-lived and is signed by the token service, whose signing keys are published at a well-known issuer endpoint. The agent then presents that assertion to Microsoft Entra ID, asking to authenticate as the connection's identity. Entra checks whether the identity has a federated credential whose issuer matches the token service that signed the assertion and whose subject matches the organization-and-connection value the assertion carries. If both match, Entra issues an access token for the identity scoped to the Azure Resource Manager resource, and the deploy task uses that token to call the management API.

### Why must the federated credential subject match exactly?

The subject in the identity's federated credential is the precise string Entra compares against the subject in the assertion the agent presents, and Entra issues a token only on an exact match. The subject encodes the organization and the specific service connection, so a token meant for one connection cannot authenticate as the identity behind another. An exact-match rule is what makes the trust narrow rather than blanket.

The exact-match requirement is the security property, not a finicky implementation detail. Because Entra issues a token only when the subject matches exactly, the federation trust authorizes precisely one issuer-and-subject pair and nothing else, so the identity cannot be assumed by any pipeline, organization, or endpoint other than the one the credential names. This is why a recreated endpoint (which gets a new identifier and therefore a new subject) breaks the trust until you update the credential, and it is also why federation resists misuse: there is no shared secret that works from anywhere, only a trust rule that fires for one exact caller. The exact-match rule trades a little fragility under reconfiguration for a great deal of safety under attack, which is the right trade for a credential that can deploy to production.

### What makes the federated path secretless end to end?

No durable secret exists anywhere in the federated path. The assertion the agent obtains is short-lived and signed rather than a stored password, the access token Entra issues is short-lived, and the trust on the identity is a description of which issuer and subject to accept rather than a credential you could copy. Because every artifact is either short-lived or a trust description, there is nothing persistent to leak or rotate.

The secretless property follows directly from the mechanism. A stored client secret is a long-lived bearer credential: anyone who reads it can authenticate as the identity from anywhere until it expires, which is why it must be guarded and rotated. The federated path replaces that long-lived bearer credential with a chain of short-lived, signed assertions and a static trust rule, none of which is a portable password. The agent cannot hand an attacker a reusable secret because it never holds one; it holds a freshly issued assertion good for minutes and bound to one exchange. Understanding this is what makes the federate-not-store rule feel less like a policy to follow and more like the obvious conclusion: once the credential is a short-lived assertion against a narrow trust rule rather than a stored password, the whole category of secret-leakage and secret-expiry problems disappears, and the GitHub Actions equivalent reaches the same conclusion through the same OpenID Connect mechanism for the same reasons.

## Designing Connections Across Many Environments and Teams

A single pipeline with one connection is the easy case. Real organizations run many pipelines across many environments and many teams sharing subscriptions, and the connection design that works for one pipeline has to scale to that reality without becoming either a sprawl of unmanaged endpoints or a handful of dangerously broad ones. The design principle that scales is one endpoint per environment per project, each narrowly scoped and individually gated, provisioned from shared code so the sprawl is managed rather than manual.

The instinct to economize by sharing connections is exactly backward at scale, because the cost of a connection is near zero when it is defined as code and the cost of a shared, broad connection is a permanent expansion of blast radius. A platform team that defines a parameterized endpoint template and a parameterized identity template can stamp out a correctly scoped, federated, gated endpoint for each environment of each project in seconds, so the marginal connection costs nothing to create and carries exactly the scope and gates that environment needs. The result is many connections, each meaning precisely one thing, which is far easier to reason about and audit than a few broad connections shared across boundaries nobody can quite remember.

### How should endpoints map to environments and teams?

Map one endpoint to one environment of one project, scoped to that environment's resource group and gated with that environment's approvals, and provision all of them from a shared template so the mapping is consistent. This keeps each connection's meaning unambiguous: its name tells you the project and environment, its scope tells you the resource group, and its gates tell you the review it enforces. Consistency through templating is what keeps many connections manageable.

The clarity this buys pays off most during an incident or an audit. When every connection maps to exactly one project-and-environment and is scoped to that environment's resource group, the question of what a given endpoint could have done has a precise answer you can read off its name and scope, rather than a shrug about which environments share it. When endpoints are stamped from a shared template, an auditor reviews the template once and trusts that every connection conforms, instead of inspecting each connection individually. The discipline that makes this work is treating connections as cattle rather than pets: each is a uniform, code-defined instance of a known pattern, not a hand-tuned artifact, and the platform that governs the rest of your infrastructure as code governs them too.

### How do I keep many endpoints auditable as the organization grows?

Define every endpoint and identity from a small set of shared, parameterized templates, store those definitions in source control, and review the templates rather than the instances. An auditor who trusts the template trusts every connection stamped from it, so the audit surface is the template count, not the connection count. Drift is caught by reconciling live connections against the definitions in source.

Auditability at scale is a property of uniformity, not of effort. If each endpoint were configured by hand, auditing a hundred of them would mean a hundred inspections, and any one could quietly carry a broad scope or a missing gate. If all hundred are stamped from three templates, the audit is three template reviews plus a reconciliation that confirms the live endpoints match their definitions, which is tractable no matter how many connections exist. The reconciliation step, comparing the live state against the source-controlled definitions, is what catches the connection someone edited in the portal in a hurry, because that edit shows up as drift from the template. Keeping the definitions authoritative and the portal read-only in practice is the habit that keeps a growing fleet of connections honest, and it is the same source-of-truth discipline that makes the rest of an Azure estate governable rather than mysterious.

## Monitoring and Auditing the Deploy Identity

A service endpoint that is built well still needs watching, because permissions drift, identities get reused in ways nobody intended, and a deploy that should never have run sometimes does. Operability is the part of setup that the wizard never mentions, yet it is what tells you whether the careful scoping and gating you configured are still holding weeks later. The two signals worth wiring up are the Entra sign-in record for the identity and the Azure activity log for the resource group it deploys into, because together they answer who authenticated and what they changed.

The Entra sign-in logs record every token the federated identity obtains, including the application that requested it and the result, so an unexpected sign-in from an identity that should only ever authenticate from a pipeline is a signal worth an alert. The Azure activity log records every management operation against the target resource group, attributed to the principal that performed it, so you can see exactly which deploys the identity ran, when, and what they touched. Pointing both of these at a Log Analytics workspace through diagnostic settings turns them into queryable history rather than a portal blade you have to remember to check.

### How do I tell whether a deploy identity is being misused?

Alert on sign-ins or operations that fall outside the expected pattern: authentication at an unusual hour, an operation type the pipeline never performs, or activity against a resource the role should not reach. The identity's normal behavior is narrow and predictable, so anything outside that narrow band is worth a look. Predictability is the property that makes anomaly detection easy.

Because a deploy identity does one job on a schedule the pipeline defines, its legitimate behavior forms a tight pattern: it authenticates when the pipeline runs, performs a known set of operations, and acts only within its scoped resource group. That tightness is exactly what makes misuse visible. A query that surfaces any management operation attributed to the identity outside its resource group, or any sign-in that does not correlate with a pipeline run, draws a short list precisely because the legitimate activity is so regular. Wiring that query into an alert means the first sign that an identity has been borrowed for something it should not do reaches you quickly, rather than waiting for a quarterly review. The audit history also gives you the evidence trail an incident response needs, since every change carries the principal that made it.

### What should I review periodically even when nothing looks wrong?

Review the identity's role assignments, the per-pipeline authorizations, and the gates on the endpoint on a regular cadence, comparing them against the definitions in source control. Permissions accumulate, authorizations get granted and forgotten, and gates get loosened during an incident and never restored, so a periodic reconciliation catches the slow drift that no single alert would. Drift is gradual, so the review is what catches it.

The slow erosion of a good setup is the threat that monitoring alone misses, because each individual loosening looks reasonable in the moment. Someone widens a role to unblock a deploy, someone authorizes an extra pipeline during a migration, someone removes an approval gate to ship a hotfix and means to put it back. None of those triggers an anomaly alert, because each is a deliberate human action, yet their accumulation is exactly how a tightly scoped endpoint becomes a broad one over a year. The defense is the periodic reconciliation against the source-controlled definitions described earlier: anything live that does not match the code is drift, and drift is either corrected in the live environment or, if the change was intended, captured back into the code. That loop is what keeps the careful setup from quietly decaying into the over-permissioned default it started as a deliberate alternative to.

## The InsightCrunch Service-Connection Setup Checklist

The whole procedure compresses into a checklist you can run against any new endpoint, with the gotcha called out at each step so the easy mistake is the visible one. This is the findable artifact: a single table that takes an endpoint from nothing to verified, secretless, narrowly scoped, and gated.

| Step | What to do | The gotcha to avoid |
| --- | --- | --- |
| 1. Choose the identity | Create an app registration or user-assigned managed identity to back the connection | Letting the wizard auto-create an identity you do not control or track |
| 2. Choose federation | Select workload identity federation, not a client secret | Accepting a secret-based connection that will expire and demand rotation |
| 3. Scope the role | Assign the least-privilege role at the target resource group, not the subscription | Accepting the default of Contributor on the whole subscription |
| 4. Authorize per pipeline | Turn off grant-to-all-pipelines; authorize each pipeline explicitly | Leaving the connection usable by any pipeline, including future or malicious ones |
| 5. Gate with approvals | Attach a manual approval and a branch control to the endpoint or environment | Shipping a production endpoint that any merge can consume unreviewed |
| 6. Verify positively | Run a read and a what-if through the connection against the target | Trusting the verify button, which proves authentication but not authorization |
| 7. Verify negatively | Reach outside the scoped group and confirm the denial | Skipping the negative test, so over-scoping goes undetected |
| 8. Express as code | Put the identity, role, and connection definition in source control | Clicking it together once with no way to reproduce or audit it |

The checklist is deliberately ordered so each step depends only on the ones before it, and the gotcha column is the part to read twice, because every gotcha listed is a default the fast path would have chosen for you. A connection that clears all eight rows is federated, narrowly scoped, individually authorized, gated, proven in both directions, and reproducible, which is the endpoint this article set out to build. You can run an endpoint you inherited through the same eight rows to find what it is missing, and the gaps you find are almost always the secret, the subscription-wide scope, or the missing gate.

To put the whole procedure into practice against a live Azure target, including creating a federated connection, scoping the role, and running a gated deploy you can watch, [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), where the connection setup, the verification deploy, and the as-code templates are laid out as exercises you can work through against a sandbox subscription. Building the connection once in a lab where mistakes are free is the fastest way to internalize the eight-step sequence before you run it against production.

## Closing Verdict

The service connection is where delivery meets the cloud, and the credential type is the decision that defines everything after it. The federate-not-store rule is the verdict: choose workload identity federation so there is no secret to leak, expire, or rotate, and you have removed the single most common cause of endpoint failure and the single most portable credential an attacker could steal. Federation is not a nice-to-have on a modern endpoint; it is the default a deliberate engineer reaches for, and a secret-based connection is the exception you justify rather than the path you accept.

Scope and gating are the two decisions that ride alongside the credential type. Scope the role to the resource group the pipeline actually deploys into, never the subscription out of convenience, so a compromised pipeline is boxed into one group rather than loose across your account. Authorize pipelines individually and gate the connection with a human approval and a branch control, so reaching production is a reviewed act rather than an automatic consequence of a merge. Verify in both directions, proving the connection can do its job and proving it cannot reach past its boundary, and express the whole thing as code so it is reproducible and auditable. An endpoint built this way is one you create and trust rather than one you create and worry about, and the few extra minutes the deliberate path costs are repaid the first time a Friday-afternoon secret expiry does not happen, because there was never a secret to expire.

## Frequently Asked Questions

### Q: How do I set up an Azure DevOps service connection for Azure deployments?

Create an Azure Resource Manager service connection in your project's settings, choose the workload identity federation authentication scheme rather than a client secret, and point it at an app registration or user-assigned managed identity you control. Before creating the endpoint, assign that identity a least-privilege role, such as Contributor scoped to the single resource group the pipeline deploys into rather than the whole subscription. After the connection is created, turn off the grant-to-all-pipelines option so only authorized pipelines can use it, attach an approval and a branch control to gate production use, and run a verification deploy that includes both a positive check (a read and a what-if against the target) and a negative check (a reach outside the scope that should be denied). Reference the connection by name in your pipeline's Azure tasks, and the task acquires a token through it automatically with no secret in your YAML.

### Q: How do I use workload identity federation for an Azure DevOps service connection?

Choose the workload identity federation scheme when creating the Azure Resource Manager connection instead of the service-principal-with-secret scheme. Federation establishes a trust relationship in Microsoft Entra ID: Entra is told to trust tokens issued by the Azure DevOps token service for your specific organization and this specific service connection, identified by an issuer and a subject value. At deploy time the agent obtains a short-lived federated token and exchanges it for an Azure Resource Manager token, so no client secret is ever stored. When you let the automatic flow create the endpoint it writes the matching federated credential onto the identity for you; when you script the endpoint, you read the issuer and subject the connection expects from its details page and add the federated credential to the identity with the Azure CLI. The result has no secret, nothing to rotate, and no expiry, and the trust is bound to exactly this connection so a token cannot be replayed elsewhere.

### Q: Should the connection use a service principal or a managed identity?

Both an app registration (service principal) and a user-assigned managed identity can back a federated endpoint, scope to least privilege, and authenticate without a secret, so the choice turns on who owns the identity's lifecycle rather than on capability. An app registration is the path the automatic federation flow creates and has the broadest tooling support, which makes it the simpler default for most pipeline endpoints. A user-assigned managed identity is an Azure resource you can provision and version-control in the same Bicep or Terraform that builds the rest of your platform, which makes it cleaner when you want the deploy identity to live in code alongside the infrastructure and to avoid holding an app registration in your directory. If your organization governs Entra app registrations through their own approval process, the managed identity may be faster to provision; if your tooling already expects app registrations, stay with the app registration. The federation mechanics and least-privilege scoping are identical either way.

### Q: What scope and role does the service connection need?

The connection needs a role that grants exactly the actions the pipeline performs, assigned at the smallest scope that contains every resource the pipeline touches. For a pipeline that deploys into one resource group, that is typically Contributor scoped to that resource group, which lets the pipeline create and manage resources inside the group and nothing outside it. Avoid the wizard's default of Contributor at the subscription scope, because that lets the connection's identity touch every resource in the subscription, including other teams' workloads, and turns a compromised pipeline into a subscription-wide risk. When the pipeline's real needs are narrower than full Contributor, prefer a more specific built-in role, such as a data-plane role on a storage account or a Website Contributor on app resources. The rule is to scope the role to the action and the target, then verify the boundary holds by deliberately reaching outside the scope and confirming the denial.

### Q: How do I avoid rotating service connection secrets?

Stop storing a secret at all by converting the connection to workload identity federation. A secret-based service connection carries a client secret with an expiry, so someone owns the recurring job of generating a new secret before the old one lapses and updating the endpoint, and the day that job is forgotten the pipeline fails to authenticate. Federation removes the secret entirely: the endpoint trusts a short-lived token issued at run time through an Entra federation relationship, so there is nothing to rotate and nothing to expire. To migrate an existing secret-based connection, recreate it (or edit it) to use the federation scheme, add the matching federated credential to the identity, verify the connection authenticates, and remove the old client secret from the identity. After the migration, audit the connection's authorization scheme to confirm it reads as federation with no secret and no expiry date, since the absence of an expiry is the proof that rotation is no longer your problem.

### Q: How do I gate a service connection with approvals?

Attach a manual approval check to the endpoint through its approvals-and-checks panel, naming the approvers, optionally with instructions and a timeout. When any pipeline tries to consume the endpoint in a stage, the run pauses and notifies the approvers, and no Azure changes happen until someone approves, so an automatic merge cannot trigger an unreviewed production deploy. Because the gate lives on the connection rather than inside one pipeline, every pipeline that uses the connection inherits the same approval, which removes the risk that a newly written pipeline forgets to add the gate. You can also pair the approval with a branch control check that allows the connection only from specified branches, and with an environment approval on the deployment target, so the deploy is gated both as a credential use and as an act against production. The two layers compose, and using both means a single forgotten setting does not open an unreviewed path.

### Q: Why does my service connection verify successfully but the deploy still fails?

Verification only confirms that Azure DevOps can obtain a token for the identity; it does not confirm that the identity holds any role on the target. An endpoint whose identity has no role assignment will verify happily and then fail every deploy with an authorization error, because authentication (proving who you are) and authorization (being permitted to act) are separate. Read the error closely: Azure names the exact action that was denied and the exact scope, such as a write operation on a resource group. Assign the role that grants that action at that scope, then redeploy. The prevention is to assign the least-privilege role to the identity before you create or rely on the endpoint, so the role is in place by the time the first deploy runs rather than discovered as a failure afterward. The lesson is that a green verify button is necessary but not sufficient, and only a deploy proves the connection can actually do its job.

### Q: Can I reuse one service connection across development, staging, and production?

You can, but you should not, because a single connection forces one identity, one scope, and one set of gates onto environments that need different ones. To serve all three environments, the connection must be scoped broadly enough for the most demanding one, which over-permissions it for the least privileged, and its approvals must be permissive enough for the most automated one, which strips production of the gating it needs. Create a separate endpoint per environment instead, each backed by its own identity, scoped to that environment's resource group, and gated with that environment's approvals. This lets development stay fast and open while production stays tightly scoped and heavily gated, which is the entire reason environments exist. The cost is a few more endpoints, easily managed when you define them as code from a parameterized template, and the benefit is that each connection means exactly what its name says and a change to one cannot accidentally affect another.

### Q: What is the difference between gating the connection and gating the environment?

A check on the service connection gates the use of that one credential wherever it is consumed, regardless of which pipeline or environment; a check on the environment gates deployments to that one named target, regardless of which connection they use. Gating the endpoint protects the credential as a resource, so the credential cannot be borrowed without approval. Gating the environment protects the target as a place, so the target cannot be deployed to without approval. They fail safe in different directions: if someone creates a new endpoint to production but forgets its gate, the environment approval still catches the deploy; if someone deploys to production through an ungated environment, the connection check still catches the credential use. For a high-stakes production target you usually want both, so that a single oversight, whether a new connection or a new environment, does not open an unreviewed path. The two gates cost a few extra minutes and remove a whole class of single-point failures.

### Q: How does the pipeline reference the service connection in YAML?

The pipeline names the connection in the relevant Azure task's input, and the task acquires a token through the endpoint automatically with no secret in the YAML. In tasks such as AzureCLI@2 or AzureResourceManagerTemplateDeployment@3 the input is confusingly named azureSubscription, but its value is the service connection name, not a subscription identifier. The endpoint name is the only coupling between the pipeline and the credential, which keeps the deploy logic in YAML separate from the trust held in the connection. Because the task uses the connection's federated identity, the only place the credential is configured is the connection, and the only thing the YAML carries is the name. If the task reaches for a resource outside the role's scope, it fails with an authorization error, which is the scope boundary working as designed. This separation means you can change the endpoint's identity, scope, or gates without touching the pipeline, and you can reuse a pipeline against a different environment by swapping the endpoint name.

### Q: How do I create the federated credential when scripting the connection myself?

When you script the connection rather than using the automatic portal flow, create it with creationMode set to manual so Azure DevOps does not try to create an identity or assign a role for you, then read the issuer and subject the connection expects from its details page or the API. Add the matching federated credential to your identity with the Azure CLI, for example az ad app federated-credential create for an app registration, supplying the issuer (the Azure DevOps token service URL) and the subject (which encodes your organization and the endpoint's identifier). The small wrinkle is that the endpoint's identifier does not exist until the connection is created, so the sequence is to create the connection, read its identifier, then write the federated credential whose subject matches. Handling this once in a setup script means every subsequent environment inherits a reliable sequence, and the reward is a connection whose trust is reproducible from files rather than configured by hand.

### Q: Why does my service connection fail only on pull-request builds?

With the grant-to-all-pipelines option correctly turned off, a pull-request trigger may run a pipeline that has not been individually authorized to use the endpoint, so the run fails only on pull-request builds while merged-branch runs, which use authorized pipelines, succeed. Often this is the desired behavior, because a privileged production endpoint generally should not be reachable from pull-request builds that can carry untrusted code, and a branch control check refusing pull-request branches is doing its job. If a pull-request build legitimately needs a low-privilege connection, such as running a what-if against a sandbox, authorize that specific pipeline and scope the connection only to the sandbox. The opposite and more dangerous case appears when grant-to-all is left on: then a pull request, even from a fork, can consume the connection's identity, which is a security problem rather than a failure. Reading the check result tells you which situation you are in, and in most cases a pull-request-only failure on a privileged endpoint is protection, not a bug.

### Q: How do I confirm my service connection is not over-permissioned?

Run a negative verification test: have a pipeline step deliberately reach for a resource the endpoint should not be able to touch, such as reading a resource group that belongs to another team, and confirm that Azure denies it with an authorization error. A correctly scoped connection is refused, and seeing that refusal in the run log is the proof your least-privilege scope holds. If the reach succeeds, the role was assigned too broadly, almost always at the subscription scope instead of the target resource group, and the fix is to delete the broad assignment and re-grant the role at the group. The negative test is more informative than the positive one, because a successful deploy only tells you the identity has enough permission while a denied reach tells you it does not have too much. Building this check into your first verification deploy means the connection's boundary is proven at birth rather than assumed, and running it across existing connections is how you find over-scoped stragglers.

### Q: What happens to the endpoint if I recreate the backing app registration?

The federation trust breaks, because a federated endpoint depends on a federated credential whose issuer and subject must match what the connection presents, and recreating the app registration removes that credential. The symptom is a token-acquisition failure that mentions a missing or mismatched federated credential, appearing on a connection that worked before the identity changed. The fix is to re-add the federated credential to the new (or recreated) identity with the exact issuer and subject the connection expects, which the endpoint's details page displays. The prevention is to treat the identity, its federated credential, and the endpoint as one coupled unit, so when you recreate any part you recreate the federation trust along with it. This is the federation analogue of the expired-secret problem, except it fails on a configuration change rather than a clock, and the diagnosis is always to compare the issuer and subject on the identity's federated credential against the values the connection expects until they match.

### Q: Is a service connection scoped to a resource group enough to keep deployments safe?

Scoping the role to a resource group is necessary but not the whole story, because scope controls what the identity may do while approvals and authorization control when and by whom the credential may be used. A resource-group-scoped connection cannot damage resources outside its group, which contains the blast radius, but on its own it does not stop an unreviewed automatic deploy or prevent an unauthorized pipeline from borrowing the identity. Pair the narrow scope with per-pipeline authorization, so only trusted pipelines can use the connection, and with approval and branch-control checks, so reaching the target is a reviewed act from an allowed branch. The three controls address different risks: scope limits the damage, authorization limits who can borrow the credential, and gating limits when it fires. An endpoint that is narrowly scoped, individually authorized, and gated is safe in a way that any one of those controls alone is not, which is why the setup checklist insists on all three.

### Q: How do I make the whole service connection setup reproducible and auditable?

Express both layers as code. The Azure-side layer, the identity and its least-privilege role assignment, belongs in Bicep or Terraform alongside the rest of your platform, with the role scoped to the target resource group so a reviewer can see the exact permission in a pull request. The Azure DevOps-side layer, the endpoint definition and its checks, belongs in a JSON specification in the repository that you apply with the Azure DevOps CLI or REST API, with the authentication scheme set to federation and no secret, the per-pipeline authorization scripted rather than granted to all, and the approval added through the checks endpoint. Parameterize the identity client identifier, tenant, and subscription so the same definitions produce a development connection and a production connection from different parameter files. The payoff is that recreating a connection is a command rather than a memory, reviewing its scope and gates is a diff rather than a portal tour, and a new environment is a parameterized copy rather than a fresh round of clicking, which is what makes the setup both reproducible and auditable.

