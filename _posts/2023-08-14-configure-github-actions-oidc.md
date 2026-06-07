---
layout: post
title: "Configure GitHub Actions OIDC for Azure"
page_title: "GitHub Actions OIDC for Azure: Configure Federated Credentials, the Subject Claim, and azure/login for Secretless Deployment"
date: 2023-08-14
categories: ["Technology"]
tags: ["Azure", "GitHub Actions", "OIDC", "DevOps", "Identity", "Security"]
excerpt: "GitHub Actions OIDC for Azure removes stored secrets entirely. Configure the federated credential, match the subject claim, and deploy without a client secret."
image: "/assets/images/blog/blog-10.webp"
reading_time: 62
author: "Insight Crunch Team"
last_updated: 2023-08-14
---

Most teams wire a GitHub workflow to Azure the way they always have: they create a service principal, generate a client secret, paste that secret into a repository secret named `AZURE_CREDENTIALS`, and move on. The pipeline deploys, the dashboard turns green, and a long-lived credential now sits in a repository setting where it will quietly expire eighteen months later in the middle of a release, or leak through a fork, a log, or a compromised action. GitHub Actions OIDC for Azure exists to delete that credential entirely. Instead of storing a secret, the workflow asks GitHub for a short-lived token at run time, presents it to Microsoft Entra ID, and receives an Azure access token in exchange. Nothing is stored, nothing expires on a calendar you forgot about, and nothing can leak from a place a secret never lived.

Correct configuration of GitHub Actions OIDC buys you a deployment identity that cannot be stolen from your repository, because the only thing the repository holds is three non-secret identifiers: a client ID, a tenant ID, and a subscription ID. When the configuration is wrong, the symptom is almost always the same: the `azure/login` step fails with an Entra error complaining that no matching federated identity record was found, and the deploy never starts. The gap between a working setup and a failing one is rarely the action, the permissions, or the role. It is one string. The federated credential you create in Entra carries a subject, and the token GitHub mints carries a subject, and those two strings must be identical down to the branch name, the environment name, or the pull-request marker. This article walks the full path: the prerequisites and the order they must happen in, the step-by-step setup with working commands, the settings the portal defaults get wrong, the verification that proves the chain works end to end, the misconfigurations that produce each error you will actually see, and how to make the whole thing repeatable as code so the next repository takes two minutes instead of an afternoon.

![Configuring GitHub Actions OIDC for Azure federated credentials and the subject claim - Insight Crunch](/assets/images/blog/blog-10.webp)

The framework that holds the rest of the article together is a single rule worth naming up front, because it explains the overwhelming majority of failures engineers hit. Call it the subject-must-match rule: a federated credential authorizes exactly one workflow context, the one whose token subject matches the credential's configured subject, so a login failure under OIDC is almost never a permissions problem and almost always a subject that does not match the branch, environment, repository, or trigger the workflow actually ran under. Hold that rule in mind. Everything below is either a way to satisfy it or a way to confirm you have.

## What GitHub Actions OIDC actually exchanges, and why the order matters

Before touching a single command, it helps to hold an accurate picture of what happens during a secretless login, because the setup steps are just the standing infrastructure that this run-time exchange needs in order to succeed. When a workflow runs and reaches the `azure/login` step, the GitHub runner requests an OIDC token from a GitHub endpoint that only the runner can reach. That token is a signed JSON Web Token. Its issuer is GitHub's OIDC provider, its audience is whatever the login step requested (the Azure exchange audience by default), and buried in its claims is a `sub` field that GitHub fills in automatically based on the repository, the trigger, and the ref. The runner then hands that token to Microsoft Entra ID and asks, in effect, to trade it for an Azure token. Entra looks at the application or managed identity named by the client ID, scans its federated identity credentials, and tries to find one whose configured issuer, audience, and subject all match the presented token. If it finds a match, it issues an Azure access token scoped to whatever roles that identity holds. If it does not, it refuses, and the step fails.

That sequence tells you why the order of setup operations is not arbitrary. You are building a chain, and a chain proves itself only at its weakest link. The identity must exist before you can attach a federated credential to it. The federated credential must exist before the token exchange can match anything. The role assignment must exist before a matched token can do anything useful, because authentication and authorization are separate concerns: a federated credential proves who the workflow is, and a role assignment decides what that identity may touch. The workflow file must request the OIDC token permission before the runner will even mint a token to present. Skip or reorder any of these and the failure surfaces at a different point than the cause, which is exactly why OIDC setups feel mysterious to debug the first time.

### What is the difference between authentication and authorization in this setup?

Authentication is the federated credential proving the workflow is the identity it claims to be, by matching the token's claim. Authorization is the Azure role assignment deciding what that identity may read or change. A workflow can authenticate perfectly and still fail every deploy because the identity holds no role on the target resource group.

The prerequisites are modest, but each one is load-bearing. You need an Entra tenant where you can create an application registration or a user-assigned managed identity, which means you need at least the Application Developer role for an app registration or Contributor on a resource group for a user-assigned identity. You need permission to assign Azure roles at the scope you intend to deploy to, which means Owner or User Access Administrator on that subscription or resource group, because granting a role is itself a privileged operation that a plain Contributor cannot perform. You need a GitHub repository where you can edit workflow files and, if you plan to scope credentials to deployment environments, permission to create those environments. None of these prerequisites involves a secret, a certificate, or a password, which is the entire point. The credential you are about to build has no secret material at all.

The correct order of operations, then, is fixed. First, decide whether the deployment identity will be an Entra application with a service principal or a user-assigned managed identity, because that choice changes which commands you run and where the federated credential lives. Second, create that identity. Third, attach one federated credential per workflow context you intend to support, getting the subject string exactly right for each. Fourth, grant the identity a least-privilege role on the deployment target. Fifth, add the three non-secret identifiers to the repository and write the workflow with the OIDC permission and the `azure/login` step configured for federation. Sixth, verify the chain with a trivial read-only command before you trust it with a real deploy. The rest of this article expands each step, but the order above is the skeleton, and reordering it is the first mistake to avoid.

## The InsightCrunch GitHub OIDC setup checklist

The findable artifact for this article is a checklist that maps each setup step to the thing that goes wrong when you skip it and the command that confirms the step succeeded. Treat it as the spine of the configuration; every later section is a deeper reading of one of these rows.

| Step | What you create | The gotcha if you skip or fumble it | Confirm it with |
|------|-----------------|-------------------------------------|-----------------|
| 1. Choose the identity | App registration plus service principal, or user-assigned managed identity | App registration suits cross-tenant and Entra app scenarios; user-assigned identity suits single-tenant Azure-native setups. Picking blind makes step 3 awkward. | `az ad app list` or `az identity list` |
| 2. Create the identity | The Entra object that will hold the federated credential | The federated credential has nothing to attach to until this exists. | `az ad app show` or `az identity show` |
| 3. Add the federated credential | A federated identity credential with issuer, audience, and the exact subject | A subject that does not match the workflow context causes every login to fail with no matching record. | `az ad app federated-credential list` |
| 4. Grant the role | An Azure RBAC role assignment at the deployment scope | A matched token with no role authenticates but cannot create or change anything. | `az role assignment list --assignee` |
| 5. Wire the workflow | `permissions: id-token: write` and `azure/login` with client, tenant, and subscription IDs | Without the id-token permission the runner never mints a token to present. | A read-only `az account show` in the job |
| 6. Verify and remove the secret | A successful read-only command, then deletion of any old stored credential | Leaving the old `AZURE_CREDENTIALS` secret defeats the security gain entirely. | `gh secret list` showing the secret gone |

Every failure described in the misconfiguration section later maps to one of these six rows. When a login fails, the fastest triage is to walk the checklist top to bottom and ask which row is not yet true, rather than rereading the workflow YAML for a typo that is usually not there.

## Choosing the deployment identity: app registration or user-assigned identity

The first real decision is which kind of Entra object will carry the federated credential, and the choice shapes every command that follows. Two options work, and both are legitimate. An application registration with its associated service principal is the classic choice: it is an Entra application object that can live in one tenant and be granted access in another, it carries application roles and API permissions if you ever need them, and it is the form most documentation and most older pipelines assume. A user-assigned managed identity is the newer, leaner choice for purely Azure-native work: it is an Azure resource that lives in a resource group, it can hold federated credentials just as an app registration can, and it tends to feel more natural to teams who already manage identities as infrastructure alongside their virtual machines and storage accounts.

The deciding factor is tenancy and ownership. If the workflow deploys within a single tenant and you want the deployment identity to be a managed Azure resource that shows up in your resource graph, lives in a resource group, and is governed by the same role assignments and locks as everything else, the user-assigned managed identity is the cleaner fit. The choice between system-assigned and user-assigned does not arise here, because a system-assigned identity is bound to a specific Azure resource and cannot receive a federated credential for an external workflow; only a user-assigned identity or an app registration can. If you need the identity to be granted access across tenants, to hold Microsoft Graph permissions, or to integrate with an Entra application model your security team already governs, the app registration is the form that supports those cases. For the deeper trade-off between these identity forms and where each belongs, the companion piece on how to [set up managed identities the right way](/2023/04/17/configure-managed-identities/) walks the system-assigned versus user-assigned decision in full, and the same reasoning about avoiding stored credentials carries straight into this OIDC setup.

### Should I use an app registration or a user-assigned managed identity for OIDC?

Use a user-assigned managed identity for single-tenant, Azure-native deployments where you want the identity governed as a normal Azure resource. Use an app registration when you need cross-tenant access, Microsoft Graph permissions, or integration with an existing Entra application model. Both hold federated credentials, so neither path requires a stored secret.

Whichever you pick, the mechanics of the federated credential are nearly identical, because both object types expose the same federated identity credential concept. The difference is the command surface and where the object lives. With an app registration you work against the application object and its service principal. With a user-assigned identity you work against the identity resource in a resource group. The rest of this article shows the app registration commands as the primary path, since it is the more common starting point, and notes the user-assigned identity equivalent where the command differs, so you can follow either without translating in your head.

## Creating the identity and attaching the federated credential

With the choice made, the setup begins by creating the identity. For an app registration, you create the application and then its service principal, because the application object is the definition and the service principal is the instance in your tenant that role assignments attach to. A common point of confusion is that the federated credential attaches to the application, while the role assignment attaches to the service principal, and the client ID you put in the workflow is the application's client ID. Keeping those three facts straight prevents a class of errors where everything looks configured but the pieces are bolted to the wrong object.

```bash
# Create the Entra application that will be the deployment identity
az ad app create --display-name "insightcrunch-deploy-oidc"

# Capture the application (client) ID it returns
APP_ID=$(az ad app list --display-name "insightcrunch-deploy-oidc" --query "[0].appId" -o tsv)

# Create the service principal for that application in this tenant
az ad sp create --id "$APP_ID"
```

For a user-assigned managed identity the equivalent is a single resource creation, and the identity's client ID and principal ID both come back from the same object:

```bash
# Create a user-assigned managed identity instead of an app registration
az identity create \
  --name "insightcrunch-deploy-oidc" \
  --resource-group "rg-cicd-identities" \
  --location "eastus"
```

The federated credential is the heart of the configuration, and it is where the subject-must-match rule earns its name. A federated identity credential has three fields that matter for matching: the issuer, the audience, and the subject. The issuer is GitHub's OIDC provider, written as `https://token.actions.githubusercontent.com`, and it is the same for every GitHub-hosted workflow on the planet, so you will copy it verbatim and never change it. The audience is the value the token's `aud` claim must carry, and for Azure it is `api://AzureADTokenExchange`, which is what the `azure/login` action requests by default. The subject is the field you must get exactly right, because it identifies the precise workflow context allowed to use this identity.

The subject format follows a fixed grammar that GitHub defines, and the credential's subject must reproduce the value GitHub will place in the token's `sub` claim for the run you intend to authorize. For a branch, the subject is `repo:OWNER/REPO:ref:refs/heads/BRANCH`. For a tag, it is `repo:OWNER/REPO:ref:refs/tags/TAG`. For a deployment environment, it is `repo:OWNER/REPO:environment:ENVIRONMENT_NAME`. For any pull request, it is `repo:OWNER/REPO:pull_request`, with no branch component, because GitHub uses a single fixed subject for all pull-request triggered runs. The owner and repository are case-sensitive and must match the repository's actual path. The following command creates a federated credential that authorizes the `main` branch of a repository to use the app registration:

```bash
# Attach a federated credential scoped to the main branch
az ad app federated-credential create \
  --id "$APP_ID" \
  --parameters '{
    "name": "github-main-branch",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:insightcrunch-org/azure-deploy:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

For a user-assigned managed identity, the same federated credential attaches with a different command but the identical issuer, audience, and subject semantics:

```bash
# The user-assigned identity equivalent of the same federated credential
az identity federated-credential create \
  --name "github-main-branch" \
  --identity-name "insightcrunch-deploy-oidc" \
  --resource-group "rg-cicd-identities" \
  --issuer "https://token.actions.githubusercontent.com" \
  --subject "repo:insightcrunch-org/azure-deploy:ref:refs/heads/main" \
  --audiences "api://AzureADTokenExchange"
```

The single most common error at this step is a subject that almost matches. The repository owner is spelled differently from the real organization slug, the branch is `master` in the credential but `main` in the workflow, or someone copied a branch claim when the workflow actually runs on a tag. Entra does no fuzzy matching. The presented subject and the configured claim are compared as exact strings, and a single character of difference produces a complete refusal. When you write the subject, copy the owner and repository directly from the repository URL rather than typing them, and confirm which ref or environment the workflow will actually run under before you decide the subject's tail.

## Why one federated credential is rarely enough

A federated credential authorizes exactly one subject, and a real repository runs under several. A deploy that triggers on a push to `main` runs with the branch claim. A validation job that runs on a pull request runs with the pull-request claim, which has no branch in it at all. A release that triggers on a version tag runs with the tag claim. A job that uses a GitHub deployment environment to gate production runs with the environment claim. Each of these is a different string, and Entra will match a presented token against only the credentials you have actually created. Configure one credential for `main` and then wonder why the pull-request validation job cannot log in, and the answer is that the pull-request claim was never added, so there is nothing for the token to match.

This is the practical meaning of the subject-must-match rule, and it is why the realistic setup attaches several federated credentials to the same identity rather than one. You add a branch credential for the branch that deploys, a pull-request credential if validation jobs need to authenticate, a tag credential if releases trigger on tags, and an environment credential for each protected environment the workflow targets. They all attach to the same application or managed identity, they all share the same issuer and audience, and they differ only in the subject. The identity is one, the contexts are many, and each context needs its own credential.

### How many federated credentials can one identity hold?

A single application or managed identity can hold multiple federated credentials, which is exactly how you support a branch, a pull request, a tag, and several environments on one deployment identity. There is a documented per-identity ceiling on the number of federated credentials, so for very large fan-out you confirm the current limit against the official source before designing around it.

Environments deserve special attention because they are the cleanest way to scope production access, and they interact with the subject in a way that surprises people. When a job declares `environment: production`, GitHub sets the token subject to the environment form, `repo:OWNER/REPO:environment:production`, regardless of which branch the job ran from. That is a feature, not a quirk: it lets you grant a production-scoped credential that only jobs explicitly running in the production environment can use, and it lets you layer GitHub's environment protection rules, required reviewers, and wait timers on top of the Azure role. The environment claim does not include the branch, so a job that targets the production environment authenticates through the environment credential even if it ran from a feature branch, which means the GitHub-side environment protection becomes the gate rather than the branch name. For teams that came to OIDC from the world of Azure DevOps, this maps closely to how a service connection plus an environment check gates a pipeline, and the comparison piece on how to [set up Azure DevOps service connections](/2023/08/07/configure-azure-devops-connections/) shows the same federate-not-store reasoning applied to the DevOps equivalent, where workload identity federation replaces the stored service principal secret in exactly the spirit this article applies to GitHub.

The pull-request claim carries its own subtlety. Because GitHub uses a single fixed subject for all pull-request runs, `repo:OWNER/REPO:pull_request`, a credential scoped to it authorizes any pull request in the repository, including one opened from a fork if your repository settings allow fork workflows to run with that token. That is usually acceptable for read-only validation against a non-production subscription, and it is usually wrong for anything that can change a production resource. The safe pattern is to scope the pull-request credential to an identity that holds only a reader role on a non-production scope, and to reserve write-capable identities for branch and environment claims that a fork cannot impersonate. Treating all four subject forms as interchangeable is the misconfiguration that quietly widens your blast radius, and naming which subject a credential carries is how you keep the scope honest.

## Granting the role: authentication is not authorization

A federated credential that matches gets the workflow an Azure token, and that token can do precisely nothing until the identity holds a role. This is the second half of the chain and the one teams skip most often, because the login step succeeds and the failure moves downstream to the first command that actually touches a resource. The error then reads like an authorization failure rather than a login failure, which it is, and the fix is a role assignment rather than anything to do with the federated credential.

Grant the least-privilege role the workflow actually needs, scoped as narrowly as the work allows. A workflow that deploys an application to a single resource group needs Contributor on that resource group, not Owner on the subscription. A workflow that only reads configuration to run a validation check needs Reader. A workflow that assigns roles as part of its deployment needs a role that can perform role assignments, which is a deliberately privileged grant you make only when the work genuinely requires it. The assignment attaches to the service principal for an app registration, or to the managed identity's principal for a user-assigned identity, and it names the scope explicitly:

```bash
# Find the service principal's object ID for the app registration
SP_ID=$(az ad sp show --id "$APP_ID" --query "id" -o tsv)

# Grant Contributor on a single resource group, not the whole subscription
az role assignment create \
  --assignee-object-id "$SP_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Contributor" \
  --scope "/subscriptions/SUBSCRIPTION_ID/resourceGroups/rg-app-prod"
```

The principle of least privilege is concrete here, not aspirational. The deployment identity is a credential that lives outside your tenant's interactive controls; it cannot be protected by a human's multifactor prompt, because no human is in the loop at run time. Its only protection is the narrowness of its role and the precision of its subject. Scope it to the resource group it deploys to, give it the lowest role that completes the work, and resist the temptation to grant subscription-wide Contributor because it is convenient. If a single workflow deploys to several resource groups, prefer several scoped assignments over one broad one, because the broad grant is exactly what an attacker who somehow forged a matching token would inherit. The role grant is where the security posture of the whole setup is decided, and it deserves the same care you would give a production firewall rule.

### What role does the federated identity need on the target?

The identity needs whatever Azure RBAC role lets the workflow perform its deployment, scoped to the narrowest resource group or resource that the work touches. Contributor on the target resource group suits most deployments. Reader suits validation-only jobs. Avoid subscription-wide grants, because a deployment identity has no interactive protection beyond its role and subject.

## Wiring the workflow: the permissions block and the login action

With the identity, the credential, and the role in place, the workflow file is the last piece, and it is shorter than the secret-based version it replaces. Two things must be true in the YAML. First, the job must request permission to mint an OIDC token, which is the `id-token: write` permission. Without it, the runner will not produce a token at all, and the `azure/login` step fails before it ever reaches Entra, with a message about a missing token rather than a missing match. Second, the login step must be configured with the three non-secret identifiers and no `creds` block, because the presence of a `creds` value is what tells the action to use a stored secret instead of federation.

```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]

permissions:
  id-token: write        # required so the runner can mint the OIDC token
  contents: read         # required to check out the repository

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Azure login via OIDC
        uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}

      - name: Confirm the login worked
        run: az account show
```

Notice that the three identifiers come from `vars`, not `secrets`. The client ID, tenant ID, and subscription ID are not secrets. They identify which application, which tenant, and which subscription to use, but knowing them grants no access whatsoever, because access depends entirely on holding a token that matches a federated credential. Storing them as repository or organization variables rather than secrets makes the configuration readable and signals correctly that nothing sensitive lives in the repository. You may store them as secrets if your governance prefers it, but doing so out of habit obscures the fact that the secretless model has removed the only thing that ever needed protecting.

The `permissions` block sets the token permissions for the job. A subtle trap is that declaring `permissions` at all resets every permission to none except the ones you list, so a job that needed `contents: read` to check out the repository and that you then gave only `id-token: write` will fail to check out. List both, as the example does. Another trap is placing the `permissions` block at the wrong scope; setting it at the workflow level applies it to every job, while setting it inside a job applies it to that job only. For a multi-job workflow where only the deploy job logs in to Azure, scoping `id-token: write` to that job follows least privilege and avoids handing the token permission to jobs that have no business minting one.

### Why does the azure/login step fail with no error about the subject?

If the login fails complaining that no token could be obtained rather than no match could be found, the cause is the missing `id-token: write` permission, not the federated credential. The runner never minted a token to present. Add the permission to the job and the error moves on to subject matching if anything there is still wrong.

The `azure/login` action requests a GitHub OIDC token whose audience is the Azure exchange value, presents it to Entra, and on success leaves the Azure CLI and the Azure PowerShell session authenticated for the rest of the job. Subsequent steps run `az` or `Connect-AzAccount`-based commands without any further credential handling, because the session is already established. If your workflow uses other actions that deploy to Azure, many of them detect the existing login automatically, and the ones that do not accept the same client, tenant, and subscription identifiers and reuse the federated token. The model that this workflow follows, the full structure of an OIDC-based deployment with environments and reusable jobs, is covered in depth in the companion article on [GitHub Actions for Azure deployments](/2025/01/20/github-actions-azure-deployments/), which builds on the credential you are configuring here and shows it inside a complete delivery pipeline rather than the minimal login this setup article uses to prove the chain.

## The settings the defaults get wrong

Several defaults look harmless and quietly cause failures, and walking them is the difference between a setup that works the first time and one that takes an afternoon of confused debugging. The first is the audience. The federated credential's audience defaults to `api://AzureADTokenExchange` in the portal and in the CLI, and the `azure/login` action requests that same audience by default, so in the common case they agree and you never think about it. The moment you override the audience on one side, for instance by setting a custom audience on the action because a blog post suggested it, you must set the identical audience on the credential, or the match fails on the audience claim even though the subject is perfect. The safe default is to leave both at the standard exchange audience and never touch it.

The second default that bites is the issuer. It must be exactly `https://token.actions.githubusercontent.com`, with the scheme, the host, and no trailing path or slash. Variations creep in when someone retypes it, adds a path segment they saw in an enterprise context, or uses a GitHub Enterprise Server issuer for a workflow that actually runs on github.com. An issuer mismatch produces a refusal that names the issuer rather than the subject, which is a useful tell: if the error mentions the issuer, fix the issuer string; if it mentions the subject, fix the subject. GitHub Enterprise Server and certain enterprise configurations use a different issuer that includes your enterprise slug, so for those deployments you confirm the issuer from your own GitHub settings rather than assuming the public value.

The third default is the subject itself, and the trap is assuming the subject for an environment includes the branch. It does not. When a job targets an environment, the subject is the environment form with no ref component, so a credential written as `repo:OWNER/REPO:environment:production` is correct and a credential written as `repo:OWNER/REPO:ref:refs/heads/main:environment:production` is not a real subject and will never match. The inverse error is equally common: writing a branch credential for a job that actually runs in an environment, so the branch claim never matches because GitHub minted an environment claim instead. The rule to internalize is that the trigger and the `environment` declaration together decide the subject, and you read the subject off the workflow's actual behavior rather than off what you expected it to be.

The fourth default concerns customizing the subject claim. GitHub allows a repository or organization to customize the format of the OIDC subject claim, for example to include the job's `runner_environment` or to drop the ref. If someone has customized the subject template for the repository, the default subject grammar described above no longer applies, and your federated credential must match the customized format instead. This is rare, and it is also the most baffling failure to debug, because every standard subject string looks correct and still does not match. If you have exhausted the ordinary subject forms and the match still fails, check whether the repository or organization has a custom OIDC subject claim configuration overriding the defaults, because that is the silent setting that invalidates every textbook subject at once.

## Verifying the chain before you trust it

A setup is not finished when the commands return success; it is finished when a run proves the whole chain works end to end. The verification step is deliberately trivial so that any failure points cleanly at a single link rather than tangling with deployment logic. Add a job that does nothing but log in and run a read-only command, push it to the branch whose subject you configured, and read the result. If `az account show` returns the subscription, the federated credential matched, the role at least permits reading the account context, and the workflow permission minted a token. That single green step confirms five of the six checklist rows at once.

```yaml
# A minimal verification job; deploy nothing until this passes
name: Verify OIDC

on:
  workflow_dispatch:

permissions:
  id-token: write
  contents: read

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - run: az account show --output table
      - run: az group list --output table
```

Read the verification failures by their wording, because the error text tells you which link broke. A message that no token could be obtained, or that the request lacked an OIDC token, points at the missing `id-token: write` permission in the job. A message from Entra that no matching federated identity record was found for the presented assertion claim points at a subject mismatch: the credential's subject and the token's claim are not the same string, and you compare them character by character. A message that no matching record was found for the presented issuer points at an issuer string that is wrong or that belongs to a different GitHub host. A login that succeeds followed by an authorization failure on `az group list` points at a missing or too-narrow role assignment, because the identity authenticated but holds no role that lets it list groups at that scope. Each symptom maps to exactly one checklist row, which is why the trivial verification job is worth more than it looks: it isolates the break.

To compare the subjects directly when a match fails, you can have the workflow print the claims of the token it would present, which removes all guesswork about what GitHub actually put in the `sub` field for that run. A short step that decodes the OIDC token's payload shows you the literal subject string, and you set the federated credential's subject to match it exactly. This is the fastest way to resolve the maddening case where the subject looks right but is not, because the run that uses a feature branch, a tag, or an environment will print a subject you might not have predicted from reading the workflow alone.

### How do I confirm which subject GitHub actually sent?

Have the workflow request its OIDC token and decode the payload, then read the `sub` claim from the decoded JSON. That literal value is what Entra compares against your federated credential's subject. Set the credential's subject to that exact string, and the match succeeds. Predicting the subject from the workflow file alone is where mistakes hide.

Once the verification job is green, you have earned the right to point the same login at a real deployment. Promote the login step into your actual deploy job, keep the `permissions` block, and remove the verification workflow or leave it as a documented sanity check. The discipline of verifying before deploying pays off most when you add the second and third repositories, because by then you know the exact shape of each failure and can fix it from the error text alone.

## Removing the stored secret, the step that completes the migration

If you are migrating an existing pipeline rather than building a fresh one, the configuration is not finished until the old secret is gone. This is the step that converts the work from a security improvement on paper into a security improvement in fact. A repository that holds both a working OIDC setup and a leftover `AZURE_CREDENTIALS` secret has not removed its attack surface; it has added a second path to Azure and kept the first one. An attacker who reads the secret still owns a credential, and the OIDC work bought nothing but a second way in.

Delete the stored credential from the repository, and delete the client secret from the Entra application if one existed, because the secret lives in two places and removing it from only one leaves the other exploitable. On the GitHub side, the secret comes out with a single command, and confirming its absence is part of the checklist's final row:

```bash
# Remove the leftover stored credential from the repository
gh secret delete AZURE_CREDENTIALS --repo insightcrunch-org/azure-deploy

# Confirm it is gone
gh secret list --repo insightcrunch-org/azure-deploy
```

On the Entra side, if the application held a client secret for the old service-principal login, remove that secret from the application's credentials so there is nothing left to rotate or leak. The federated credential you created has no secret material, so after this cleanup the application authenticates only through federation, and there is genuinely no stored credential anywhere in the path. This is the outcome the whole setup exists to produce, and verifying it is what separates a configuration that looks secretless from one that is.

The same principle, that the migration is complete only when the old credential is destroyed rather than merely supplemented, applies to every secretless migration across the series. The broader treatment of how secrets move out of pipelines, including the cases this article does not cover, lives in the deeper companion material, but the discipline is identical: the win is not adding OIDC, it is removing the secret that OIDC made unnecessary, and a setup that stops at the first half has done the harder work and skipped the point of it.

## The common misconfigurations and the symptom each one produces

The value of holding the subject-must-match rule and the six-row checklist together is that almost every failure you will meet maps cleanly to one named cause, and the symptom tells you which. Walking the recurring cases as patterns, each with the setup step that fixes it, turns OIDC debugging from guesswork into a short lookup.

The first and most common pattern is a login that fails because the subject does not match the branch or environment. The symptom is an Entra refusal naming the presented assertion claim and reporting that no matching federated identity record was found. The cause is that the credential's subject and the token's claim differ, and the difference is usually a branch name, an owner slug, or the gap between a branch claim and an environment claim. The fix is to decode the token, read the literal subject GitHub sent, and set the credential's subject to that exact string. The temptation at this moment, and the wrong fix to resist, is to fall back to a stored service-principal secret because OIDC "isn't working." It is working; the subject simply does not match. Aligning the subject takes a minute, and reverting to a secret reintroduces the exact exposure the setup removed.

The second pattern is needing separate credentials for the branch, the environment, and the pull request, and having configured only one. The symptom is that the deploy on `main` works perfectly while the pull-request validation job, or the production environment job, fails to log in. The cause is that each of those contexts mints a different claim value, and only the configured one matches. The fix is to add a federated credential for each context the workflow actually uses, all on the same identity, differing only in the subject. This is the pattern that most surprises engineers coming from secret-based pipelines, where one secret covered every trigger, because under OIDC the trigger and the environment together decide the subject.

The third pattern is the identity lacking the target role. The symptom is a login that succeeds cleanly followed by an authorization failure on the first command that touches a resource, often reading that the client does not have permission to perform an action over a scope. The cause is a missing or too-narrow role assignment. The fix is to grant the identity the least-privilege role at the deployment scope, attaching it to the service principal or managed identity principal as shown earlier. The tell that distinguishes this from a subject problem is that the login step itself is green; the failure is downstream, which means authentication worked and authorization did not.

The fourth pattern is the `azure/login` action misconfigured for OIDC, usually by leaving a `creds` input in place from a copied secret-based workflow. The symptom is that the action tries to parse a stored credential and either fails or, worse, silently uses the old secret path instead of federation. The cause is the lingering `creds` value, which switches the action out of OIDC mode. The fix is to remove `creds` entirely and supply only the client, tenant, and subscription identifiers, which is what tells the action to use federation. A workflow that still references `secrets.AZURE_CREDENTIALS` anywhere has not actually moved to OIDC, regardless of whether a federated credential exists.

The fifth pattern is the missing token permission. The symptom is a failure before any contact with Entra, complaining that the OIDC token could not be obtained or that the request lacked the necessary permission. The cause is the absent `id-token: write` permission on the job, or a `permissions` block that listed other permissions and silently dropped it. The fix is to add `id-token: write` at the job or workflow level, alongside `contents: read` if the job checks out code. This failure never reaches the subject-matching stage, because there is no token to present, so the error wording is the giveaway.

The sixth pattern is a reusable workflow changing the claim. The symptom is that a workflow which logged in correctly begins failing after it is refactored into a reusable workflow called from another workflow. The cause is that the token subject for a job running inside a reusable workflow can differ from the subject of a job running directly, depending on how GitHub composes the claim for called workflows. The fix is to decode the token from inside the reusable workflow context, read the actual subject, and add a federated credential matching it, rather than assuming the subject is unchanged. This is a real trap for teams who centralize their deployment logic into a shared reusable workflow and find that the federated credential they built against the original direct workflow no longer matches.

### Which is more likely, a subject problem or a role problem?

Read the login step. If the login itself fails, it is almost always a subject, issuer, or token-permission problem, because those are checked during authentication. If the login succeeds and a later command fails with a permission error, it is a role problem, because the identity authenticated but holds no role at that scope. The login step's color is the fastest single signal.

The recurring misdiagnoses are worth naming so you can catch yourself making them. The first is reverting to a stored secret the moment a subject does not match, which trades a one-minute fix for the exposure the setup removed. The second is treating a subject mismatch as a role problem and granting ever-broader roles in the hope it helps, which it never does because the login is failing before authorization is ever consulted. The third is assuming a missing role is a subject problem and rewriting credentials when the login was already succeeding. Each misdiagnosis comes from not reading where the failure actually occurred, which is why the discipline of looking at the login step's outcome first resolves most confusion before it starts. To practice these failure modes against a real subscription, where you can watch each symptom appear and clear as you fix the matching checklist row, [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), which is built to let you federate a credential, break it deliberately, and watch the exact error each break produces so the symptom-to-cause mapping becomes second nature.

## Making the configuration repeatable as code

A setup you clicked through once is a setup you will fumble the second time, and the third repository should not cost what the first one did. The federated credential, the role assignment, and the identity are all expressible as infrastructure as code, which turns the whole configuration into a reviewable, version-controlled, repeatable artifact. Expressing it as code also documents the subject strings explicitly, which is the field most prone to silent error, so the code review itself becomes a check on the configuration's correctness.

In Bicep, the user-assigned managed identity, its federated credential, and the role assignment compose into a small template that any new repository can reuse by changing the repository owner, name, and the branch or environment in the subject. The federated credential is a child resource of the identity, and the subject is a plain string property that a reviewer can read and confirm against the workflow.

```bicep
param location string = resourceGroup().location
param identityName string = 'insightcrunch-deploy-oidc'
param repoOwner string = 'insightcrunch-org'
param repoName string = 'azure-deploy'
param branch string = 'main'

resource deployIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
}

resource branchCredential 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  parent: deployIdentity
  name: 'github-${branch}'
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    subject: 'repo:${repoOwner}/${repoName}:ref:refs/heads/${branch}'
    audiences: ['api://AzureADTokenExchange']
  }
}

resource contributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, deployIdentity.id, 'Contributor')
  properties: {
    // Contributor role definition ID
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c')
    principalId: deployIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}
```

The Terraform equivalent reads similarly and suits teams who already manage Azure with it. The federated credential becomes its own resource that references the identity, and a single variable for the subject keeps the value reviewable. Expressing the configuration in whichever tool your team already uses means the OIDC setup joins the rest of your infrastructure rather than living as a manual exception nobody can reproduce.

```hcl
resource "azurerm_user_assigned_identity" "deploy" {
  name                = "insightcrunch-deploy-oidc"
  resource_group_name = var.resource_group
  location            = var.location
}

resource "azurerm_federated_identity_credential" "branch" {
  name                = "github-main"
  resource_group_name = var.resource_group
  parent_id           = azurerm_user_assigned_identity.deploy.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = "https://token.actions.githubusercontent.com"
  subject             = "repo:${var.repo_owner}/${var.repo_name}:ref:refs/heads/main"
}

resource "azurerm_role_assignment" "deploy" {
  scope                = var.target_resource_group_id
  role_definition_name = "Contributor"
  principal_id         = azurerm_user_assigned_identity.deploy.principal_id
}
```

The deeper reason to template this is that the subject string, the field most prone to a silent typo, becomes a parameter a reviewer reads and approves rather than a value someone types into a portal field at the end of a long day. Adding a second environment becomes another federated-credential resource with a different claim value, and adding a second repository becomes a new instantiation of the same module with different parameters. The protocol that underpins this entire exchange, the OAuth and OIDC mechanics that make a federated token trade for an Azure token in the first place, is worth understanding when you design these templates at scale, and the explainer on [OAuth 2.0 and OIDC in Azure](/2023/12/25/azure-oauth-oidc-explained/) lays out the token types, the issuer and audience claims, and the flow that the federated credential is matching against, so the subject and audience fields stop being magic strings and become claims you can reason about.

### How do I add a second repository without redoing everything?

Reuse the same identity-and-credential template, change the repository owner and name parameters, and add one federated credential per workflow context the new repository uses. The role assignment and identity logic stay identical. Templating the subject as a parameter means the only per-repository change is the string, which a reviewer can confirm against the new repository's workflow before it merges.

## What the OIDC token actually carries

Debugging federation at the level where the maddening cases live means knowing what is inside the token GitHub mints, because every matching decision Entra makes is a comparison against the claims in that payload. The token is a signed JSON Web Token with a header, a payload, and a signature. Entra validates the signature against GitHub's published keys, which is why the issuer must be exactly right: the issuer tells Entra which key set to trust. Inside the payload sit the three claims that decide the match, the issuer, the audience, and the assertion's subject, plus a set of contextual claims that GitHub fills in automatically and that you can use to understand or customize matching.

The contextual claims are worth reading once so they stop being mysterious. GitHub includes the repository path, the repository owner, the ref that triggered the run, the commit SHA, the workflow file reference, the actor who triggered the run, the run identifier, and an indicator of whether the runner was GitHub-hosted or self-hosted. The assertion's subject is assembled from a subset of these, which is why a branch run and an environment run produce different values: the run on a branch composes the ref into the claim, while the run in an environment composes the environment name instead. When you decode a token during a failing run and read its claims, you are reading the raw material from which GitHub built the value Entra is trying to match, and seeing it directly removes every guess about what the workflow presented.

### Why does decoding the token resolve so many failures at once?

Because the decoded payload shows the literal value GitHub sent rather than the value you expected, and the gap between those two is where almost every match failure hides. Reading the claims turns an opaque refusal into a one-line comparison, so you fix the configured record to match what the run actually presented rather than what the workflow file implies.

The reason this matters beyond curiosity is that GitHub allows the format of the assertion to be customized at the repository or organization level. The default composition follows the grammar described earlier, but an administrator can change it, for example to drop the ref and include only the repository and the runner type, or to add the job workflow reference for tighter scoping of reusable workflows. If such a customization is in force, every textbook value you construct from the default grammar will be correct against the documentation and wrong against the token, which is the single most baffling failure in this entire space. The diagnostic for it is the same decode step: read the claims, see the shape the assertion actually takes for this repository, and build the matching record against that shape rather than the default. Customization is rare, so you reach for it only after the ordinary forms have all failed, but knowing it exists saves an afternoon when the ordinary forms are demonstrably right and still do not match.

Understanding the claims also clarifies why the audience is fixed and dull. The audience is the intended recipient of the token, and Azure declares that recipient as its token-exchange endpoint, so the token says in effect that it is meant for Azure and Entra confirms it was. Leaving the audience at the standard value across both the action and the matching record means the audience comparison is always trivially satisfied, which removes one of the three matchable claims from your worry list and lets you focus on the issuer and the assertion, which are the two that actually vary in practice. The protocol-level reasoning behind these claims, the token types and the exchange flow that turns a presented assertion into an Azure access token, is laid out in the explainer on [OAuth 2.0 and OIDC in Azure](/2023/12/25/azure-oauth-oidc-explained/), and reading it alongside this section turns the matchable claims from strings you copy into mechanics you can predict.

## Organizing federation across many repositories

A single repository is the easy case. The real test of the configuration is the tenth repository, when ad-hoc clicking has produced a sprawl of identities, inconsistent naming, and credentials nobody can audit. Deciding the organizational pattern before the sprawl arrives is what keeps a fleet of repositories governable, and the decision turns on whether identities are shared or dedicated and on how the matching records are named.

The first organizational choice is whether each repository gets its own deployment identity or whether several repositories share one. A dedicated identity per repository gives the cleanest blast-radius story, because a compromise of one repository's deployment path reaches only that identity's roles, and the matching records on it name only that repository. A shared identity reduces the number of objects to manage but widens the blast radius, because every repository that can present a matching assertion inherits the same roles. The defensible default for production is a dedicated identity per repository or per environment, accepting more objects in exchange for tighter isolation, and reserving shared identities for low-risk, read-only validation work where the convenience outweighs the wider reach. The deciding factor is the sensitivity of what the role can touch: the more a role can change, the more the identity behind it should be dedicated and narrowly named.

The second choice is naming, and it pays for itself the first time someone audits the tenant. A naming convention that encodes the repository, the environment, and the purpose into both the identity name and the matching record name turns an audit from archaeology into a scan. An identity named for its repository and a federated record named for the context it authorizes, such as a record whose name marks it as the production environment entry for a specific repository, lets a reviewer read the intent off the name without decoding the assertion inside. The matching value itself is not human-friendly, so the record name is where you put the human-readable intent, and a consistent convention there is the difference between a tenant you can reason about and one you cannot.

### How should I name federated records so audits stay sane?

Encode the repository, the context, and the purpose into the record name, because the matchable value inside it is not readable at a glance. A name that marks an entry as, for example, the production-environment authorization for a named repository lets a reviewer confirm intent without decoding the assertion. Consistency across the tenant turns an access review into a quick scan rather than a forensic exercise.

This organizational thinking is exactly the territory the Azure DevOps world already mapped, and the parallels are instructive. A DevOps service connection using workload identity federation faces the same shared-versus-dedicated decision and the same need to scope a role narrowly, which is why the companion piece on how to [set up Azure DevOps service connections](/2023/08/07/configure-azure-devops-connections/) reads as a sibling rather than a competitor: the platform differs, the federate-not-store discipline is identical. Teams running both GitHub Actions and Azure DevOps benefit from a single governance model that treats every deployment identity, whatever presents the assertion, as a credential to be dedicated, named, scoped, and audited the same way. When the full delivery pipeline is built on top of this identity, with environments, approvals, and the deploy steps themselves, the structure that surrounds the login is detailed in the companion article on [GitHub Actions for Azure deployments](/2025/01/20/github-actions-azure-deployments/), which assumes the federation you are configuring here and shows where it sits inside a production workflow.

## A diagnostic reference for OIDC login failures

The misconfiguration section described the recurring failures as patterns. A second findable artifact compresses them into a lookup keyed by the literal error you see, so that mid-incident you map symptom to cause to confirming command without rereading prose. Treat this as the bedside chart for a login that will not work.

| Symptom or error wording | Most likely cause | Confirming command or check |
|--------------------------|-------------------|------------------------------|
| No matching federated identity record for the presented assertion claim | The configured match value differs from what the run presented | Decode the token, compare its subject claim to the configured value |
| No matching record for the presented issuer | Issuer string wrong or belongs to a different GitHub host | Check the configured issuer against the run's issuer claim |
| Could not obtain an OIDC token / missing token permission | The job lacks `id-token: write` | Inspect the job's `permissions` block |
| Login succeeds, then a later command reports a permission failure | Missing or too-narrow role assignment | `az role assignment list --assignee <id> --all` |
| Login behaves as if using a secret, or parsing a credential fails | A leftover `creds` input on `azure/login` | Search the workflow for `creds:` and `AZURE_CREDENTIALS` |
| Worked directly, fails after refactor into a reusable workflow | The assertion the called workflow presents changed | Decode the token from inside the reusable workflow |
| Every standard match value is correct yet nothing matches | A custom assertion format is configured for the repository or org | Decode the token and read the actual claim shape |

The discipline the table encodes is to read the failure's location and wording before changing anything. A failure during the login step is an authentication failure, and authentication is decided by the issuer, the audience, and the assertion, so the fix lives among those three. A failure after a successful login is an authorization failure, and authorization is decided by the role assignment, so the fix lives there. A failure before any contact with Entra is a token-permission failure, and the fix lives in the workflow's permissions. Mapping the moment of failure to the layer that owns it is the whole skill, and the table is just that mapping written down.

The confirming commands matter because they replace belief with evidence. Listing the role assignments for the identity tells you definitively whether a role exists and at what scope, rather than assuming it does. Decoding the token tells you definitively what the run presented, rather than inferring it from the workflow file. Inspecting the permissions block tells you whether the token could be minted at all. Each command turns a hypothesis into a fact, and a setup debugged on facts converges in minutes while a setup debugged on guesses can churn for hours. To rehearse this lookup against live failures, where you can trigger each row of the table deliberately and watch the exact wording appear, [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), which lets you break and repair a federated deploy until the symptom-to-layer mapping is reflexive.

## The security posture a secretless deploy actually buys

It is worth being precise about what the secretless model improves and what it does not, because a security control oversold is a security control misused. The concrete gain is the removal of a long-lived bearer credential from your repository and from your tenant. A stored client secret is a value that grants access to anyone who reads it, for as long as it remains valid, from anywhere. Removing it removes an entire class of incident: the secret leaked through a log, a fork, a screenshot, a compromised action, or a backup. The token that replaces it is minted fresh for each run, lives only for the duration of that run, and is scoped to the exact context that requested it, so even an intercepted token is worthless minutes later and useless outside its run.

The blast radius of the remaining risk is set by two things you control: the narrowness of the role and the precision of the matching record. An attacker who could somehow cause a workflow to run under a context whose assertion matches a federated record would inherit exactly the roles that record's identity holds, and nothing more. This is why the role grant is the security decision of the whole setup. A deployment identity scoped to Contributor on one resource group is a contained risk; the same identity granted Owner on the subscription is a tenant-wide one. The precision of the matching record matters for the same reason: a record scoped to a single protected branch or a gated environment is far harder to satisfy than one scoped to any pull request from any fork, so the scope of the match is itself a control, not a detail.

### What would an attacker actually need to abuse a federated deploy?

They would need to cause a workflow run whose presented assertion matches a configured record, then they would inherit only that identity's roles for the life of one run. They cannot extract a reusable credential, because none exists. This is why a narrow role and a precise, hard-to-satisfy match value are the two controls that bound the risk, and why broad roles undo the model's main benefit.

Two further controls layer on top for teams that want them. The first is the GitHub side: protected branches, required reviewers on environments, and restrictions on which workflows may run with the token all reduce the chance that an attacker can cause a matching run in the first place. A production environment gated by required reviewers means that even a matching assertion cannot be presented without a human approving the run, which puts a person back in a loop that automation otherwise removes. The second is the Azure side: Conditional Access policies that apply to workload identities can add location or risk conditions to the token exchange, and monitoring the sign-in logs for the deployment identity surfaces any exchange that should not have happened. These are additive hardening rather than prerequisites, and most setups are well served by the core model alone, but they exist when the sensitivity of the target warrants more than a narrow role.

What the model does not buy is freedom from thinking about the runner, especially for self-hosted runners, where the host can reach the token during the job and therefore sits inside the trust boundary. Nor does it remove the need to audit role assignments over time, because a role granted for one purpose and never revoked accumulates into exactly the broad standing access the model was meant to avoid. The secretless deploy is a strong default, not a finished posture, and the difference between the two is the ongoing discipline of keeping roles narrow, match values precise, and old grants pruned. Done with that discipline, it is the most defensible deployment identity available, because the credential that cannot leak is the one that never persists.

## Maintaining federation as repositories and branches change

A configuration that works on the day you build it still has to survive the ordinary churn of a codebase: branches get renamed, environments get added, repositories get archived, and people leave with knowledge of why a given entry exists. Federation has one large advantage over the secret model here, which is that there is nothing to rotate, because no credential material expires. There is no annual scramble to regenerate a value before it lapses and breaks a release at the worst moment. What does need ongoing attention is the set of matching records and the role assignments, both of which drift if nobody tends them.

The most common churn event is a branch rename or deletion. Because a branch-scoped record matches the literal ref, renaming the branch from one name to another silently breaks the match, and the next deploy fails with the no-matching-record refusal even though nothing about the workflow or the role changed. The fix is to update the record's match value to the new ref, or to add a new entry and remove the old one. This is a good argument for scoping deploys to a small, stable set of long-lived branches and to environments rather than to many short-lived feature branches, because every ref you authorize is a record you must maintain when that ref changes. Environments are more durable than branches in this respect, since an environment name tends to outlive any particular branch, which is one more reason to prefer environment-scoped authorization for anything that reaches production.

Listing what exists is the maintenance habit that prevents drift from accumulating into mystery. The records attached to an identity are enumerable, and reviewing them periodically catches the entry that was added for a branch deleted six months ago, the record for a repository that has since been archived, and the duplicate someone created while debugging and never cleaned up. Each stale entry is a small piece of standing authorization that no longer serves a purpose, and the principle that quiet, unused access is risk applies as much to a forgotten federated record as to a forgotten role.

```bash
# Enumerate the federated records on an app registration
az ad app federated-credential list --id "$APP_ID" --output table

# Enumerate them on a user-assigned managed identity
az identity federated-credential list \
  --identity-name "insightcrunch-deploy-oidc" \
  --resource-group "rg-cicd-identities" --output table

# Review the role assignments the identity holds, at every scope
az role assignment list --assignee "$SP_ID" --all --output table
```

### How do I clean up a federated record after a branch is gone?

List the records on the identity, find the entry whose match value names the deleted ref, and remove it. Removing it costs nothing operationally, because a record for a ref that no longer exists can never match anyway, and deleting it keeps the identity's authorized contexts honest. The same review catches role assignments that outlived their purpose, which are the quieter risk.

There is a practical ceiling on how many records a single identity can hold, which shapes the design of large fan-out setups. When a single identity would need more authorized contexts than the limit allows, the design answer is to split across more identities rather than to fight the ceiling, which also improves the blast-radius story by isolating contexts onto separate identities. Because limits of this kind change over time, you confirm the current number against the official source before designing a fleet that approaches it, and you treat the limit as a signal to reconsider whether one identity should carry that many contexts in the first place. An identity that authorizes dozens of contexts is usually a sign that several identities have been collapsed into one for convenience, and splitting them back out is both the fix for the ceiling and the better security design.

Removing an entire setup is as clean as building it, which is a property worth valuing. To decommission a repository's deployment access, you remove its role assignments first so the identity can no longer change anything, then delete its matching records so no run can authenticate, then delete the identity itself if nothing else uses it. Because there was never a secret, there is no credential to invalidate elsewhere, no value that might still be cached in a forgotten system, and no rotation to confirm completed. The access simply stops existing the moment the records and roles are gone, which is the kind of clean teardown the secret model never offered, because a leaked secret remained dangerous until it expired regardless of how thoroughly you thought you had removed it.

The maintenance discipline reduces to three recurring reviews. Confirm that every authorized context still corresponds to a branch, environment, or repository that still exists and still needs to deploy. Confirm that every role assignment is still scoped as narrowly as the work requires and still serves a current purpose. Confirm that no leftover secret has crept back in through a copied workflow or a hurried fix. None of these reviews is heavy, and running them on a schedule keeps the federation fleet in the state the initial setup left it in, rather than letting entropy widen the access surface a record and a role at a time. The work of configuring federation correctly is front-loaded; the work of keeping it correct is light but not zero, and naming the three reviews is how you make the light work actually happen.

## A worked setup from empty tenant to first deploy

Pulling the pieces into one narrative helps the order of operations stick, so consider a team starting from nothing: a fresh repository and a subscription with a single application resource group. Their goal is a workflow that deploys to that resource group on every push to the main branch, with no stored credential anywhere. The walk-through below is the same six checklist rows, told as one continuous procedure rather than as isolated steps, because seeing them flow into each other is how the chain becomes intuitive.

They begin by choosing a user-assigned managed identity, because the work is single-tenant and Azure-native and they want the identity governed as a normal resource. They create it in a dedicated resource group reserved for delivery identities, which keeps deployment plumbing separate from application resources and makes later audits cleaner. With the identity created, they read back its client identifier, which they will hand to the workflow, and its principal identifier, which they will hand to the role assignment. Neither of these is sensitive, so they record them as repository variables without a second thought.

Next they attach the matching record that authorizes the main branch. They take the repository owner and name straight from the repository URL to avoid a typo, compose the branch form of the claim, and create the record with GitHub as the issuer and the standard Azure exchange audience. They resist the urge to also create a pull-request entry at this stage, because their first workflow only runs on push, and adding contexts the workflow does not use yet would be authorizing access nobody needs. They will add the pull-request entry the day a validation job actually needs it, and not before.

With authentication in place, they turn to authorization and grant the identity Contributor scoped to the single application resource group, not the subscription. This is the decision they treat with the most care, because it sets the blast radius for the life of the setup. A reviewer on the pull request that adds the infrastructure code can read the scope in one line and confirm it is the resource group and nothing wider, which is exactly why they expressed the grant as code rather than clicking it into the portal.

Then they write the workflow. They add the token permission and the checkout permission to the deploy job, call the login action with the three recorded identifiers and no stored credential input, and add a single read-only command as the first step after login so a failure surfaces cleanly. They push to a throwaway branch first, watch it fail to authenticate exactly because the throwaway branch is not the authorized one, and take that failure as confirmation that the authorization is genuinely scoped rather than open to anything. Then they merge to main, watch the login succeed and the read-only command return the subscription, and only then add the real deploy steps beneath the proven login.

The whole procedure took one short infrastructure template and one workflow file, produced no secret, and left an audit trail in version control showing exactly which repository, which branch, and which scope were authorized and by whom. That is the shape every subsequent repository will take, which is why expressing it as a reusable template pays off immediately: the second repository is the same template with three parameters changed and one matching record reviewed, and the team has turned a fiddly afternoon into a two-minute, reviewable change.

## Closing verdict

GitHub Actions OIDC for Azure is the deployment identity done correctly: no stored secret, no expiry to forget, nothing in the repository worth stealing. The configuration is genuinely small, an identity, one federated credential per workflow context, a least-privilege role, and a workflow that requests the token permission and calls `azure/login` with three non-secret identifiers. What makes it feel hard the first time is that the chain proves itself only at the end, so a break anywhere surfaces as a login failure that looks the same regardless of cause. The fix for that confusion is the subject-must-match rule and the six-row checklist read together: when the login fails, the wording tells you whether the subject, the issuer, or the token permission broke, and when the login succeeds but a command fails, the cause is the role. Configure one credential per context rather than expecting one to cover all triggers, scope the role to the resource group rather than the subscription, and finish the migration by deleting the old secret rather than leaving it beside the new path. Do those things and the workflow deploys to Azure with a credential that cannot leak from your repository, because the only credential involved is minted fresh for each run and lives no longer than the job that used it.

The longer payoff is organizational rather than technical. Once the first repository is federated correctly and expressed as a reusable template, every later repository inherits the same reviewable shape, and the security model your team reasons about stops being a patchwork of secrets with different expiry dates and becomes a single, uniform pattern: a narrowly scoped identity, a precise match value per context, and an audit trail in version control. That uniformity is what makes a fleet of deployment pipelines governable at scale, because a reviewer can read any one of them and know exactly what it can reach and why, without hunting for a secret that might be stored somewhere they cannot see. The first setup is the one that teaches the chain; every setup after it is the same chain with the parameters changed, and the discipline that keeps the whole fleet safe is the light, recurring review that prunes stale records and over-broad roles before they harden into the standing access the model was built to avoid.

## Frequently Asked Questions

### Q: How do I configure GitHub Actions OIDC for Azure end to end?

Create a deployment identity, either an Entra app registration with a service principal or a user-assigned managed identity. Attach a federated identity credential to it whose issuer is `https://token.actions.githubusercontent.com`, whose audience is `api://AzureADTokenExchange`, and whose subject matches the workflow context, such as `repo:OWNER/REPO:ref:refs/heads/main`. Grant the identity a least-privilege Azure role at your deployment scope. In the workflow, add `permissions: id-token: write`, then call `azure/login@v2` with the client ID, tenant ID, and subscription ID and no `creds` input. Verify with a read-only command before deploying anything real, then delete any old stored secret so the only credential is the short-lived token minted per run. Each piece is small; the order is what matters, because the chain proves itself only when all of authentication, authorization, and the token permission are in place at once.

### Q: What exactly goes in the federated identity credential's subject for a branch?

For a branch trigger, the subject is `repo:OWNER/REPO:ref:refs/heads/BRANCH`, with the owner and repository copied exactly from the repository path and the branch spelled exactly as it appears in GitHub. The string is compared as an exact match, so `master` will not match `main`, and a capitalization difference in the owner slug breaks it. The owner and repository together form the first segment, the literal `ref` keyword forms the second, and `refs/heads/` plus the branch name forms the third. Do not add an environment segment to a branch claim; if the job runs in an environment, GitHub mints an environment claim instead and the branch claim will never match. The safest way to get this right is to run the workflow once, decode the token it presents, and copy the literal subject from the `sub` claim into the credential, rather than constructing the string from memory.

### Q: What subject does a pull request use, and is it safe for production?

A pull-request triggered run uses the fixed subject `repo:OWNER/REPO:pull_request`, with no branch component, because GitHub assigns one subject to all pull-request runs in the repository. A federated credential scoped to that subject therefore authorizes any pull request, which can include pull requests opened from forks if your repository allows fork workflows to obtain the token. For that reason, a pull-request credential is appropriate for read-only validation against a non-production scope, and inappropriate for anything that can change production. Scope the pull-request credential to an identity holding only a reader role on a non-production subscription, and reserve write-capable identities for branch and environment claims that a fork cannot present. Treating the pull-request claim as equivalent to a branch claim is how teams accidentally let untrusted pull requests reach a scope they should never touch.

### Q: Why does my environment job fail to authenticate when the branch job works?

Because the two jobs present different claim values. A job that declares `environment: production` causes GitHub to set the token subject to `repo:OWNER/REPO:environment:production`, regardless of which branch it ran from, while a plain branch job presents the branch claim. If you configured only a branch credential, the environment job has nothing to match, so its login fails even though the branch job's login succeeds. The fix is to add a second federated credential on the same identity with the environment claim. This is the most common surprise for teams adopting OIDC, because a single stored secret used to cover every trigger, while under federation each distinct context needs its own credential. The environment claim deliberately omits the branch, which is what lets GitHub environment protection rules, rather than the branch name, gate access to that credential.

### Q: Do I need to store the client ID and tenant ID as GitHub secrets?

No. The client ID, tenant ID, and subscription ID are identifiers, not secrets. Knowing them grants no access at all, because access depends entirely on presenting a token that matches a federated credential. Store them as repository or organization variables and reference them with `${{ vars.AZURE_CLIENT_ID }}` and the equivalents. Doing so keeps the configuration readable and signals correctly that nothing sensitive lives in the repository, which is the whole point of the secretless model. You may store them as secrets if your organization's governance insists on it, but treating them as secrets out of habit obscures the fact that OIDC removed the only value that ever needed protecting. The genuine secret in the old model was the client secret, and that is exactly the thing the federated credential replaced.

### Q: What is the audience value for the federated credential, and when do I change it?

The audience is `api://AzureADTokenExchange`, and it is the value the token's `aud` claim must carry for Entra to accept it. Both the federated credential and the `azure/login` action default to this value, so in the normal case they agree and you never adjust it. You only change it when you have a deliberate reason to use a custom audience, and if you do, you must set the identical custom value on both the credential and the action, or the match fails on the audience claim even when the subject is correct. For almost every GitHub Actions to Azure setup, the right move is to leave the audience at the standard exchange value and never touch it, because a mismatched audience is an avoidable failure that adds nothing.

### Q: What error does Entra return when the subject does not match?

Entra refuses the token exchange and reports that no matching federated identity record was found for the presented assertion claim. The message names the subject, which is the useful part, because it tells you the issuer and audience matched and only the subject did not. When you see that wording, compare the credential's configured subject against the literal subject GitHub minted for the run, character by character. The difference is usually a branch name, an owner slug, the gap between a branch claim and an environment claim, or a tag claim where a branch claim was configured. A separate message naming the issuer rather than the subject means the issuer string is wrong, which is a different fix. Reading which claim the error names is the fastest way to know which field to correct, so read the message rather than guessing.

### Q: Can one federated credential cover both pushes and pull requests?

No, because a push to a branch and a pull-request run present different claim values, and a credential matches exactly one subject. A push to `main` presents the branch claim, while a pull request presents the fixed `pull_request` subject with no branch. You configure one credential for each, both attached to the same identity, differing only in the subject string. This is the practical consequence of the subject-must-match rule, and it is why a realistic setup holds several federated credentials on one identity rather than one. If you also release on tags and gate production through an environment, you add a tag credential and an environment credential as well. The identity is single; the contexts are many; each context requires its own credential.

### Q: How do I migrate an existing secret-based workflow to OIDC without downtime?

Add the OIDC path alongside the existing secret path first, then cut over, then remove the secret. Create the federated credential and role on the existing identity or a new one, add the `id-token: write` permission and the `azure/login` configuration to a non-production branch or a verification workflow, and confirm a read-only command succeeds. Once the OIDC login is proven, switch the production deploy job to the federation configuration and run a real deploy through it. Only after that deploy succeeds do you delete the stored credential from the repository and remove any client secret from the app registration. Removing the secret is the step that completes the migration; a repository holding both a working OIDC setup and a leftover secret has added a path rather than closed one, so the security gain is not real until the secret is gone.

### Q: Do I still need a client secret on the app registration after setting up OIDC?

No, and you should remove it. The federated credential authenticates the workflow without any secret material, so once OIDC is working, a client secret on the application is dead weight that can still be stolen or that will expire and confuse a future engineer. Delete it from the application's credentials. The presence of a leftover client secret is one of the two ways a migration looks complete while leaving the original exposure intact; the other is a leftover repository secret. Removing both is what turns the configuration from secretless on paper into secretless in fact. After the cleanup, the application's only credential is the federated one, which has nothing to rotate and nothing to leak, which is the outcome the whole setup exists to reach.

### Q: How do I configure OIDC for a tag-triggered release workflow?

Use a federated credential whose subject is `repo:OWNER/REPO:ref:refs/tags/TAG`, matching the tag the release runs on. If your releases use a tag pattern rather than a single fixed tag, you confirm the literal subject GitHub mints for a real tag run by decoding the token, because the subject carries the specific tag ref. A workflow that triggers on a tag presents a tag claim, not a branch claim, so a branch credential will not match a release run even though it matched the branch that created the tag. Attach the tag credential to the same identity that holds your branch and environment credentials, and grant it whatever role the release work needs, which for a production release is often scoped more tightly than ordinary deploys because a release touches production directly.

### Q: Why did OIDC stop working after I moved my deploy into a reusable workflow?

Because the token subject for a job running inside a called reusable workflow can differ from the subject of the same job running directly, depending on how GitHub composes the claim for reusable workflows. Your federated credential was built against the original direct workflow's subject, so after the refactor the presented claim no longer matches. The fix is to decode the token from inside the reusable workflow context, read the actual subject GitHub now sends, and add a federated credential matching it. This trips up teams who centralize deployment logic into a shared reusable workflow for consistency and then find the credential they carefully configured no longer authenticates. Treat the reusable-workflow subject as a new context to verify rather than assuming it is unchanged, and the fix is the same one-credential-per-context discipline that applies everywhere else.

### Q: Can a federated credential use a wildcard for the branch name?

A standard federated credential matches a single exact subject, so a literal wildcard in the branch position is not the general mechanism for matching many branches. For matching across many refs, the supported approach is to use a flexible matching configuration where it is available, or to scope to an environment claim so that the GitHub environment, rather than the branch, becomes the gate. Because matching behavior and any flexible-matching support evolve, confirm the current capability against the official source before designing a setup that depends on matching many branches with one credential. The simpler and more dependable pattern for most teams is to deploy from a small, fixed set of branches and environments, each with its own credential, so that the set of authorized contexts is explicit and auditable rather than implied by a pattern.

### Q: What is the issuer value, and does it differ for GitHub Enterprise Server?

For workflows on github.com, the issuer is exactly `https://token.actions.githubusercontent.com`, with no trailing path or slash, and it is identical for every public GitHub-hosted workflow. GitHub Enterprise Server and certain enterprise configurations use a different issuer that includes your enterprise identifier, so for those you read the correct issuer from your own GitHub settings rather than assuming the public value. An issuer mismatch produces an Entra refusal that names the issuer rather than the subject, which is a helpful tell: if the error mentions the issuer, fix the issuer string; if it mentions the subject, fix the subject. The issuer is one of the three fields Entra matches, alongside audience and subject, and getting it wrong fails the exchange before the subject is ever considered.

### Q: How do I scope the deployment role to least privilege for an OIDC identity?

Grant the lowest Azure role that lets the workflow complete its work, at the narrowest scope the work touches. A workflow deploying to one resource group needs Contributor on that resource group, not Owner on the subscription. A validation-only job needs Reader. A workflow that assigns roles as part of its deployment needs a role capable of role assignments, which you grant deliberately and rarely. Attach the assignment to the service principal for an app registration or to the managed identity's principal for a user-assigned identity, and name the scope explicitly in the assignment. Least privilege matters more here than for an interactive user, because the deployment identity has no multifactor prompt or human in the loop to catch misuse; its only protection is the narrowness of its role and the precision of its subject. Prefer several scoped assignments over one broad grant when a workflow spans multiple resource groups.

### Q: Can I use OIDC with a system-assigned managed identity?

No. A system-assigned managed identity is bound to a specific Azure resource and cannot hold a federated identity credential for an external workflow, so it cannot be the target of GitHub Actions OIDC. The two identity forms that can hold a federated credential are a user-assigned managed identity and an Entra app registration with its service principal. Choose the user-assigned identity for single-tenant, Azure-native deployments where you want the identity governed as a normal Azure resource in a resource group, and choose the app registration when you need cross-tenant access or integration with an existing Entra application model. Both expose the same federated identity credential concept with the same issuer, audience, and subject fields, so the configuration steps are nearly identical once you have created the object.

### Q: How do I test the OIDC login in isolation before adding deployment steps?

Create a minimal workflow that does nothing but log in and run read-only commands such as `az account show` and `az group list`, with `permissions: id-token: write` and the `azure/login` step configured for federation. Trigger it on the same branch or environment whose subject you configured, and read the result. A green login confirms the federated credential matched and the token permission is present, while the read-only commands confirm the identity holds at least a reading role at that scope. Keep deployment logic out of this job entirely, because the point is to isolate the authentication chain so that any failure points cleanly at one link rather than tangling with deployment errors. Once this trivial job passes, promote the same login step into your real deploy job with confidence that the credential, role, and permission are all correct.

### Q: Does GitHub Actions OIDC work with self-hosted runners?

Yes, because the OIDC token is minted by GitHub's token service and requested through the workflow's `id-token: write` permission, not by the runner's own infrastructure, so a self-hosted runner obtains and presents the token the same way a GitHub-hosted runner does. The federated credential's subject, issuer, and audience are determined by the repository, the trigger, and the workflow rather than by where the job executes, so the same credential matches regardless of runner type. What does change with self-hosted runners is the surrounding security model, since the runner host itself can reach the token during the job, so you treat the runner host as part of the trust boundary and keep it as locked down as the Azure scope the credential can reach. The configuration of the credential and the workflow, though, is identical.
