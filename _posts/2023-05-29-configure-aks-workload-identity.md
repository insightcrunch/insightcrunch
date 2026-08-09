---
layout: post
title: "Set Up Workload Identity in AKS"
page_title: "AKS Workload Identity: Configure the OIDC Issuer, Federated Credentials, and Service Account Binding to Get Entra Tokens Without Secrets"
date: 2023-05-29
categories: ["Technology"]
tags: ["Azure", "AKS", "Workload Identity", "Entra ID", "Kubernetes", "Managed Identity", "Security"]
excerpt: "AKS workload identity lets pods get Entra tokens without secrets. Set up the OIDC issuer, federated credential, and service account binding correctly."
image: "/assets/images/blog/blog-44.webp"
reading_time: 62
author: "ryan-walsh"
last_updated: 2026-08-09
lang: en
---
A pod running in Azure Kubernetes Service needs to read a secret from Key Vault, write a blob to Storage, or call a database, and it needs to prove who it is to do any of that. For years the answer involved a connection string stuffed into an environment variable, a client secret baked into a Kubernetes Secret object, or the brittle and now deprecated AAD Pod Identity that intercepted the instance metadata endpoint. AKS workload identity replaces all of that with a federation model: a Kubernetes service account is federated to a Microsoft Entra identity through the cluster OIDC issuer, and a pod that uses that service account receives short-lived Entra tokens with no stored credential anywhere. Configure it correctly and your workloads authenticate to Azure resources the same way a managed identity on a virtual machine does, except the trust flows through Kubernetes rather than through the host. Configure it wrong and the symptom is almost always the same: the pod starts, the SDK tries to acquire a token, and the call fails with an authorization or federation error that sends engineers chasing code bugs that do not exist.

![Set Up Workload Identity in AKS](/assets/images/blog/blog-44.webp)

The correct configuration buys you three concrete things. First, no secret lives in the cluster, in source control, or in a pipeline variable, which removes an entire category of leak and rotation work. Second, the token a pod receives is short-lived and scoped, so a compromised pod yields a credential that expires in minutes rather than a static key that an attacker keeps. Third, the access the workload holds is governed by Azure role-based access control on the target resource, so you reason about permissions in exactly the same vocabulary you use for every other Azure principal. What breaks when the configuration is wrong is rarely subtle once you know where to look, but it is maddening when you do not: a federated credential whose subject does not match the service account, an OIDC issuer that was never enabled on the cluster, a pod that is missing the label that injects the token, or an identity that exists and federates correctly but was never granted a role on the thing it is trying to reach. Each of those produces a token failure, and each has a precise setup step that fixes it.

This guide walks the full chain end to end, in the order the pieces must exist, with a working command for every step and the gotcha that bites at each one. It covers the prerequisites and the order of operations, the step-by-step setup, the defaults that mislead, the verification that proves the token actually flows, the misconfigurations and their symptoms, and how to express the whole thing as repeatable infrastructure rather than a sequence of portal clicks you will never reproduce. By the end you will be able to stand up workload identity on a fresh cluster, migrate a workload off the deprecated pod identity, and diagnose a token failure by reasoning about the federation rather than guessing at the application.

## What Workload Identity Actually Is and the Mental Model to Hold

Workload identity is a way for code running inside Kubernetes to authenticate to Microsoft Entra without holding a secret. The mechanism is OpenID Connect federation. Every AKS cluster can expose an OIDC issuer, which is a public endpoint that publishes a discovery document and a set of signing keys. Kubernetes issues service account tokens that are signed by the cluster, and those tokens are standard OIDC tokens with an issuer, a subject, an audience, and an expiry. Microsoft Entra can be told to trust tokens from a specific issuer that carry a specific subject and audience, and when it does, it will exchange one of those Kubernetes-issued tokens for an Entra access token scoped to whatever the federated identity is allowed to reach.

The mental model that keeps you out of trouble is a chain of four trust relationships, each of which must line up exactly. The cluster OIDC issuer is the authority that signs the Kubernetes token. The federated credential on an Entra identity declares which issuer, which subject, and which audience it will accept. The Kubernetes service account is the subject named in that federated credential, and it carries an annotation pointing at the Entra client ID. The pod references the service account and carries a label that switches on the token-injection webhook. When a request for a token arrives, Entra checks that the incoming Kubernetes token came from the trusted issuer, that its subject matches the federated credential, and that its audience is the one configured, and only then does it mint an Entra token. Break any link and the exchange fails.

The subject is the part most people get wrong, so it deserves a plain statement. The subject of the Kubernetes service account token is the string `system:serviceaccount:<namespace>:<serviceaccountname>`. The federated credential you create on the Entra identity must name that exact subject. If your service account is named `workload-sa` in the namespace `payments`, the subject is `system:serviceaccount:payments:workload-sa`, and the federated credential must say precisely that. A trailing typo, the wrong namespace, or a different service account name produces a subject mismatch, and a subject mismatch is the single most common reason a correctly written application cannot get a token.

The audience matters too, though it is easier because it has a conventional default. The audience that AKS workload identity uses is `api://AzureADTokenExchange`. The federated credential names that audience, and the projected service account token the webhook injects is requested with that same audience. As long as you do not override it inconsistently, the audience lines up on its own, but if you start customizing it on one side and not the other, the exchange will refuse the token even though the subject and issuer are correct.


## The Federation-Binds-the-Token Rule

Here is the claim this guide is built around, stated so you can quote it back to yourself at three in the morning when a pod cannot authenticate. Call it the federation-binds-the-token rule: workload identity works only when the federated credential matches the service account subject and the OIDC issuer is enabled, so a token failure is almost always a federation mismatch, not a code bug. The corollary is the diagnostic shortcut that follows from it. When a pod fails to acquire an Entra token, do not start by reading the application logs for a logic error. Start by checking the three things the federation depends on, in order: is the OIDC issuer enabled and does the cluster publish a discovery document; does a federated credential exist whose subject is `system:serviceaccount:<namespace>:<serviceaccount>` for the exact service account the pod uses; and has the pod actually been mutated by the webhook so that it carries the projected token and the environment the SDK reads. In the overwhelming majority of cases, the failure lives in one of those three and the application code is fine.

The reason this rule holds is structural. The application code that requests a token is almost always a one-line call into the Azure SDK that asks `DefaultAzureCredential` or `WorkloadIdentityCredential` to fetch a token. That code path is identical across every workload that has ever used workload identity, and it is exercised by millions of pods. The variable that changes from one deployment to the next is the federation configuration, and the federation configuration is where the errors are introduced, because it is hand-entered, namespace-specific, and easy to get subtly wrong. Internalize the rule and you stop wasting time in the wrong layer.

## The InsightCrunch Workload-Identity Setup Checklist

The findable artifact for this guide is a checklist that names every step in the order it must happen, the command that performs it, and the gotcha that bites if you skip or fumble it. Keep this next to you while you build the chain the first time, and use it as the triage map when something later goes wrong.

| Step | What you do | Command or action | The gotcha |
|------|-------------|-------------------|------------|
| 1 | Enable the OIDC issuer on the cluster | `az aks update --enable-oidc-issuer` | A cluster created without it must be updated; the issuer URL is not the API server URL |
| 2 | Enable the workload identity add-on | `az aks update --enable-workload-identity` | Without the add-on the mutating webhook never runs and the token is never injected |
| 3 | Read the issuer URL | `az aks show --query oidcIssuerProfile.issuerUrl` | Copy it exactly; a trailing slash difference will break the federated credential match |
| 4 | Create the user-assigned managed identity | `az identity create` | A user-assigned identity is portable across pods; a system-assigned one is not the right fit here |
| 5 | Create the Kubernetes service account | `kubectl apply` with the client-ID annotation | The annotation `azure.workload.identity/client-id` must carry the identity's client ID, not its object ID |
| 6 | Create the federated credential | `az identity federated-credential create` | Subject must be `system:serviceaccount:<ns>:<sa>` exactly; audience is `api://AzureADTokenExchange` |
| 7 | Grant the identity a role on the target | `az role assignment create` | Federation proves identity; it grants no access until a role is assigned on the resource |
| 8 | Label the pod | `azure.workload.identity/use: "true"` on the pod template | The label, not just the service account, switches on token projection for the pod |
| 9 | Verify a token | Exec into the pod and check the projected token file and a real call | A green deployment is not proof; the token must actually be exchanged for an Entra token |

Every later section in this guide expands one or more of these rows. The table is the spine; the prose is the marrow.

## Prerequisites and the Correct Order of Operations

Before you create a single resource, confirm three prerequisites, because two of them cannot be added retroactively without a cluster update and the third determines whether your version of AKS supports the model at all. First, you need an AKS cluster on a version that supports workload identity, which means a reasonably current Kubernetes version on a current AKS release; this is a fast-moving floor and you should verify the minimum supported version against the current official documentation rather than trusting a number written in any guide, including this one. Second, you need the ability to run `az aks update` against the cluster, because the OIDC issuer and the workload identity add-on are cluster-level features that are most reliably enabled through the Azure CLI. Third, you need permission in the Entra tenant to create a managed identity and to add a federated credential to it, and permission on the target resource to create a role assignment, because the chain spans two control planes and you need rights in both.

The order of operations is not arbitrary, and getting it out of order is a common source of confusion even when every individual step is correct. The dependency graph runs like this. The OIDC issuer must be enabled before the federated credential can reference its URL, because the credential's issuer field is that URL. The managed identity must exist before you can add a federated credential to it, because the credential is a child object of the identity. The service account must exist, or at least its name and namespace must be decided, before you create the federated credential, because the credential's subject names that service account. The role assignment can happen at any point after the identity exists, but the workload will not function until it is in place. The pod label and the service account annotation tie the runtime to the configuration, so they come last, at deploy time.

A practical way to hold the order is to think of it as building from the cluster inward and from the identity inward, then joining them at the federated credential. On the cluster side you enable the issuer and the add-on and read the issuer URL. On the identity side you create the managed identity, note its client ID, and grant it the role it needs on the target. The federated credential is the joint: it takes the issuer URL from the cluster side, the subject from the service account you are about to deploy, and attaches them to the identity from the identity side. Once the joint is made, you deploy the service account with its annotation and the pod with its label, and the runtime closes the loop.

If you are working on an existing cluster that predates your decision to use workload identity, the order has one wrinkle. Enabling the OIDC issuer on a running cluster triggers a control-plane update and rotates the issuer, which means any federated credential you might have created against a previous issuer URL must be updated. On a brand-new cluster you can enable both the issuer and the add-on at creation time, which avoids the update cycle entirely. The InsightCrunch labs in VaultBook let you stand up a cluster with the issuer and add-on enabled from the first command and then federate a credential against it, so you can rehearse the order on a disposable cluster before you touch the one that matters.


## The Step-by-Step Setup With Working Commands

This section walks the nine rows of the checklist as a continuous build. Run the commands in order against a non-production cluster the first time, read the output of each before moving on, and resist the temptation to paste the whole block at once, because the values you read in early steps feed the later ones.

### How do I enable the OIDC issuer and the add-on?

On an existing cluster, enable both features with a single update. The OIDC issuer publishes the discovery document that Entra will trust, and the workload identity add-on installs the mutating webhook that injects the token into labeled pods. Run the update, wait for it to complete, and then read back the issuer URL.

```bash
# Enable the OIDC issuer and the workload identity add-on on an existing cluster
az aks update \
  --resource-group rg-aks-prod \
  --name aks-prod \
  --enable-oidc-issuer \
  --enable-workload-identity

# Read the issuer URL that the cluster now publishes
export AKS_OIDC_ISSUER="$(az aks show \
  --resource-group rg-aks-prod \
  --name aks-prod \
  --query oidcIssuerProfile.issuerUrl \
  --output tsv)"

echo "$AKS_OIDC_ISSUER"
```

The issuer URL looks like a regional Azure host followed by a tenant and cluster path, and it ends in a way that varies by region and cluster. The important discipline is to capture it into a variable and never retype it, because a single character difference between the URL the cluster publishes and the URL the federated credential names will break the trust silently. On a new cluster you can fold these flags into `az aks create` so the issuer and the add-on exist from the start, which avoids the control-plane update that enabling the issuer later requires.

### How do I create the managed identity and the service account?

Create a user-assigned managed identity for the workload. A user-assigned identity is the right choice because it is a standalone Entra object that survives pod restarts and can be referenced by name, and because the federated credential is a child of it. Capture the client ID, because the service account annotation needs it.

```bash
# Create a user-assigned managed identity for the workload
az identity create \
  --resource-group rg-aks-prod \
  --name id-payments-workload \
  --location eastus

# Capture the client ID of the identity
export USER_ASSIGNED_CLIENT_ID="$(az identity show \
  --resource-group rg-aks-prod \
  --name id-payments-workload \
  --query clientId \
  --output tsv)"
```

Now create the Kubernetes service account in the namespace where the workload runs, and annotate it with the client ID you just captured. The annotation `azure.workload.identity/client-id` is what tells the injected SDK which Entra application to request a token for. Note carefully that the annotation carries the client ID, which is the application identifier, and not the object ID or the principal ID; mixing those three identifiers up is a frequent and confusing error because all three are GUIDs and all three are easy to copy from the wrong field.

```yaml
# service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: workload-sa
  namespace: payments
  annotations:
    azure.workload.identity/client-id: "REPLACE_WITH_USER_ASSIGNED_CLIENT_ID"
```

```bash
# Substitute the captured client ID and apply the service account
sed "s/REPLACE_WITH_USER_ASSIGNED_CLIENT_ID/${USER_ASSIGNED_CLIENT_ID}/" service-account.yaml | kubectl apply -f -
```

The namespace and the service account name you choose here are not cosmetic. They become part of the subject that the federated credential must match, so decide them deliberately and write them down. If you later rename the service account or move the workload to a different namespace, you must update the federated credential to match the new subject, and forgetting that step is one of the classic ways a working setup breaks after a refactor.

### How do I create the federated credential that ties it together?

The federated credential is the joint of the whole chain. It lives on the managed identity, it names the issuer URL the cluster publishes, it names the subject of the service account, and it names the audience. Create it with the issuer variable you captured and the subject built from your namespace and service account name.

```bash
# Create the federated credential that trusts the service account
az identity federated-credential create \
  --name fic-payments-workload \
  --identity-name id-payments-workload \
  --resource-group rg-aks-prod \
  --issuer "${AKS_OIDC_ISSUER}" \
  --subject "system:serviceaccount:payments:workload-sa" \
  --audience "api://AzureADTokenExchange"
```

Read the subject in that command slowly, because it is the line that fails most often. The format is the literal prefix `system:serviceaccount:` followed by the namespace, a colon, and the service account name. For a service account named `workload-sa` in the namespace `payments`, the subject is exactly `system:serviceaccount:payments:workload-sa`. The audience `api://AzureADTokenExchange` is the standard value that AKS workload identity uses, and the projected token the webhook injects requests that same audience, so as long as you do not override it on only one side, it lines up. After this command succeeds, the trust is declared but not yet exercised, because the workload still has no permission on any resource and is not yet labeled to receive the token.

### How do I grant the identity a role on the target?

Federation proves who the workload is; it grants no access on its own. To let the workload read a Key Vault secret, write a blob, or query a database, assign the identity a least-privilege role on the specific target resource. The principal you assign the role to is the identity's principal ID, which you read from the identity. Scope the assignment to the narrowest resource that works, never to the subscription when a single resource will do.

```bash
# Read the principal ID of the managed identity
export PRINCIPAL_ID="$(az identity show \
  --resource-group rg-aks-prod \
  --name id-payments-workload \
  --query principalId \
  --output tsv)"

# Grant a least-privilege data-plane role on a specific Key Vault
az role assignment create \
  --assignee-object-id "${PRINCIPAL_ID}" \
  --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/<sub-id>/resourceGroups/rg-aks-prod/providers/Microsoft.KeyVault/vaults/kv-payments"
```

The role you choose is the access the workload will have, so pick the data-plane role that matches the operation rather than a broad management role. A workload that reads secrets needs Key Vault Secrets User, not Key Vault Administrator. A workload that reads blobs needs Storage Blob Data Reader, not Owner. The principle of least privilege applied here is not a formality; the whole value of workload identity is that a compromised pod yields a short-lived token scoped to exactly what you granted, and that value evaporates if you grant the identity broad rights out of haste. Our guide on setting up managed identities the right way at [/2023/04/17/configure-managed-identities/](/2023/04/17/configure-managed-identities/) walks the role-scoping decision in more depth, and the same discipline applies whether the identity is consumed by a virtual machine or by a federated pod.

### How do I label the pod so it receives the token?

The final runtime step is the label. The service account annotation tells the system which identity to use, but the pod template must carry the label `azure.workload.identity/use: "true"` for the mutating webhook to inject the projected token volume and the environment variables the SDK reads. Set the service account on the pod and add the label to the pod template, not only to the deployment metadata.

```yaml
# deployment.yaml (excerpt)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payments-api
  namespace: payments
spec:
  template:
    metadata:
      labels:
        app: payments-api
        azure.workload.identity/use: "true"
    spec:
      serviceAccountName: workload-sa
      containers:
        - name: payments-api
          image: myregistry.azurecr.io/payments-api:1.0.0
```

The label belongs on the pod template's metadata, under `spec.template.metadata.labels`, because that is the metadata the pods themselves carry. A frequent mistake is to put the label only on the deployment's top-level metadata, where it does nothing for the pods, and then to wonder why the token is never injected. The service account name under the pod spec must match the service account you annotated and federated. When both the label and the service account are correct, the webhook mutates the pod at admission time, projects a service account token into a known path, and sets environment variables that the Azure SDK reads automatically.


## How the SDK Consumes the Injected Token

Once the pod is labeled and the webhook has mutated it, the application code that fetches a token is short and identical across languages, which is precisely why token failures are almost never in the application. The webhook injects a projected service account token at a known file path and sets a handful of environment variables: the path to that token file, the Entra client ID from the service account annotation, the tenant ID, and the authority host. The Azure SDK reads those variables and exchanges the projected token for an Entra access token without any code on your part beyond constructing the credential.

```python
# Python: the workload-identity credential reads the injected environment automatically
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://kv-payments.vault.azure.net",
    credential=credential,
)
secret = client.get_secret("db-connection-string")
print(secret.value)
```

`DefaultAzureCredential` tries a chain of credential sources and picks up the workload identity environment when it is present, which makes the same code work locally with a developer login and in the cluster with the federated identity. If you want to be explicit and avoid the chain probing other sources, construct `WorkloadIdentityCredential` directly, which reads the same injected environment but skips the fallbacks. The choice between the two is a matter of how much you value the local-development convenience of the chain versus the predictability of the explicit credential; both consume the same injected token.

The important point for diagnosis is that this code does not change between a working pod and a broken one. If the credential cannot get a token, the SDK raises an authentication error, and the instinct is to debug the SDK call. The federation-binds-the-token rule says to look elsewhere: the token file the credential reads is injected by the webhook, the client ID it uses comes from the annotation, and the exchange it performs is governed by the federated credential. The code is the same in both cases, so the difference is in the configuration the code depends on. Our deep dive on managed identity token failures at [/2023/01/23/fix-managed-identity-token-error/](/2023/01/23/fix-managed-identity-token-error/) catalogs the specific error strings the SDK emits and maps each one back to the configuration layer that produced it, which is the fastest way to turn an opaque exception into a one-line fix.

## The Settings the Defaults Get Wrong

The defaults around workload identity are mostly sensible, but a few of them mislead in ways that cost hours, and naming them up front saves you the discovery.

The first misleading default is that a cluster created before you decided to use workload identity has neither the OIDC issuer nor the add-on enabled, and nothing in the cluster's status screams that fact at you. The cluster runs fine, pods schedule, everything looks healthy, and the absence of the issuer is invisible until a pod tries to get a token and cannot. Treat the issuer and the add-on as features you must explicitly confirm are on, not as things that come for free, and check them first when you inherit a cluster you did not build.

The second misleading default concerns the identifiers. A managed identity exposes a client ID, a principal ID, and an object ID, and the three serve different purposes. The service account annotation wants the client ID, which is the application identifier used during the token exchange. The role assignment wants the principal ID, which is the service principal object that holds permissions. Because all three are GUIDs and the Azure CLI and portal present them in adjacent fields, copying the wrong one into the wrong place is easy and the resulting error is unhelpful. When the annotation carries a principal ID instead of a client ID, the exchange fails with an error that does not name the mistake, and you can stare at a correct-looking configuration for a long time before noticing the field was wrong. Capture each identifier into a clearly named variable and use the variable, never a copy-pasted GUID.

The third misleading default is the audience. The conventional audience is `api://AzureADTokenExchange`, and most tooling defaults to it on both the federated credential and the projected token, so it usually lines up without thought. The trap appears when someone customizes the projected token audience on the service account or the pod, perhaps copied from an unrelated example, while the federated credential still names the default. The two sides then disagree, and Entra refuses a token whose audience does not match the credential. Unless you have a specific reason to change it, leave the audience at the conventional value on both sides and you will avoid the mismatch entirely.

The fourth misleading default is around token lifetime and refresh. The projected service account token has a finite lifetime and is rotated by the kubelet, and the Azure SDK refreshes the Entra token it derives. For ordinary request-response workloads this is invisible and correct. For a long-running process that acquires a token once at startup and caches it forever, you can see a failure after the token would have expired, which looks like an intermittent authentication error hours into a pod's life. The fix is to let the SDK manage the token rather than caching a raw token string yourself, because the SDK knows to refresh.


## The Verification Step That Proves It Worked

A deployment that rolls out cleanly is not proof that workload identity works. The pod can be running, the service account can be attached, and the token can still fail to exchange, because the federation is checked at token-acquisition time, not at scheduling time. Verification means proving that a token is actually minted and that a real call against the target resource succeeds. Do this in three layers, from the cheapest check to the most conclusive.

The first layer confirms that the webhook mutated the pod. Exec into a running pod and inspect the environment and the projected token file. If the mutation happened, you will see the workload identity environment variables set and a token file present at the projected path.

```bash
# Confirm the pod received the injected environment and token file
kubectl exec -n payments deploy/payments-api -- env | grep AZURE
kubectl exec -n payments deploy/payments-api -- \
  cat /var/run/secrets/azure/tokens/azure-identity-token | head -c 40
```

If the environment variables are absent, the webhook did not mutate the pod, which means the label is missing or wrong, or the add-on is not enabled. That single check separates a token problem from a labeling problem, and it is the first thing to run when a pod cannot authenticate.

The second layer confirms that the projected token is a valid OIDC token with the subject and issuer you expect. You can decode the token's payload inside the pod and read its claims, which lets you confirm the subject matches the federated credential and the issuer matches the cluster. This is the check that catches a subject mismatch, because it shows you the actual subject the cluster put in the token, which you can compare character by character against the federated credential.

```bash
# Decode the projected token payload to read its claims (sub, iss, aud)
kubectl exec -n payments deploy/payments-api -- sh -c '
  TOKEN=$(cat /var/run/secrets/azure/tokens/azure-identity-token)
  echo "$TOKEN" | cut -d "." -f2 | base64 -d 2>/dev/null
'
```

Read the `sub`, `iss`, and `aud` fields from that payload. The `sub` must equal the subject in your federated credential, the `iss` must equal the cluster issuer URL, and the `aud` must equal the audience. If any of the three disagrees with the federated credential, you have found the mismatch without ever touching the application.

The third layer is the conclusive one: make a real call. The cheapest real call is to acquire a management token from inside the pod using the injected environment, which exercises the full exchange end to end. If that succeeds, the federation is sound and any remaining failure is a missing role assignment rather than a federation problem.

```bash
# Acquire a token from inside the pod to prove the exchange works end to end
kubectl exec -n payments deploy/payments-api -- sh -c '
  curl -s -X POST "https://login.microsoftonline.com/${AZURE_TENANT_ID}/oauth2/v2.0/token" \
    -d "client_id=${AZURE_CLIENT_ID}" \
    -d "scope=https://management.azure.com/.default" \
    -d "client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer" \
    -d "client_assertion=$(cat ${AZURE_FEDERATED_TOKEN_FILE})" \
    -d "grant_type=client_credentials" | head -c 200
'
```

A successful response returns an access token, which proves the issuer is trusted, the subject matches, and the audience lines up. A failure here returns an Entra error code that names the problem more precisely than the SDK exception does, and that error code is the fastest path to the specific layer at fault. Once you can acquire a management token, attempt the actual data-plane operation the workload performs, and if that fails while the token acquisition succeeds, the gap is the role assignment on the target resource, not the federation.

### What proves workload identity is configured correctly?

Workload identity is proven correct when three things hold together: the pod carries the injected environment and projected token file, the token's subject, issuer, and audience match the federated credential, and a real call against the target resource succeeds. A clean deployment proves none of these; only an exercised token exchange and a successful data-plane call do.

The VaultBook labs build this verification into the workflow rather than leaving it as an afterthought. The hands-on track has you enable the issuer, federate a credential, deploy a labeled pod, and then pull a token from inside that pod and watch the claims, so you see the exchange happen and learn to read the token payload before you ever need to debug a real failure. Rehearsing the verification on a disposable cluster is the difference between recognizing a subject mismatch in thirty seconds and losing an afternoon to it in production.


## The Common Misconfigurations and Their Symptoms

Six failure patterns account for nearly every workload identity problem engineers report. Each one maps to a specific setup step, and each has a symptom you can recognize and a confirmation you can run. Learn the six and you will diagnose by pattern recognition rather than by trial and error.

### Why does the federated credential subject not match the service account?

A subject mismatch happens when the federated credential names a subject that differs from the actual service account the pod uses, even by a single character. The cluster issues a token with subject `system:serviceaccount:<namespace>:<serviceaccount>`, and Entra rejects the exchange when that does not equal the credential's subject exactly.

This is the most common failure of all, and it has several flavors. The namespace in the subject is wrong because the workload was deployed to a different namespace than the one written into the credential. The service account name has a typo or a stray plural. The service account was renamed during a refactor and the credential was never updated. Or two environments share a credential that names only one of their subjects. The confirmation is the token-decode check from the verification section: read the `sub` claim from the projected token and compare it against the subject on the federated credential, character by character. The fix is to update the federated credential's subject to match the actual service account, or to deploy the workload into the namespace the credential expects. There is no partial match and no wildcard in the common case, so the strings must be identical.

### Why is the OIDC issuer not enabled on the cluster?

When the OIDC issuer was never enabled, the cluster does not publish a discovery document, so Entra has no issuer to trust and the token exchange has no foundation. The symptom is that no pod in the cluster can ever acquire a token, regardless of how carefully the rest of the chain is built.

This pattern is the signature of an inherited cluster. Someone built the cluster before workload identity was a goal, the issuer flag was never set, and the cluster has run happily for months because nothing needed the issuer until now. The confirmation is direct: query the cluster for its issuer profile and check whether an issuer URL is present. If the query returns empty, the issuer is off. The fix is to run `az aks update --enable-oidc-issuer`, which enables it and publishes the discovery document, after which you read the issuer URL and use it in every federated credential. Remember that enabling the issuer on a running cluster triggers a control-plane update, so plan for it rather than running it blind against production at peak hours.

```bash
# Confirm whether the OIDC issuer is enabled and read its URL
az aks show --resource-group rg-aks-prod --name aks-prod \
  --query oidcIssuerProfile.enabled --output tsv
az aks show --resource-group rg-aks-prod --name aks-prod \
  --query oidcIssuerProfile.issuerUrl --output tsv
```

### Why is the pod missing the workload-identity label?

The label `azure.workload.identity/use: "true"` is what switches on the mutating webhook for a given pod. When it is missing, the webhook does not project the token volume or set the environment variables, so the SDK has nothing to read and the credential cannot find a workload identity to use.

The telltale sign is that the verification check for the injected environment comes back empty: exec into the pod, grep for the Azure environment variables, and find nothing. The most common cause is putting the label on the deployment's top-level metadata instead of on the pod template under `spec.template.metadata.labels`, where it actually governs the pods. A subtler cause is a templating tool that strips or relocates the label during rendering. The confirmation is to read the labels on a running pod, not on the deployment, and verify the workload identity label is present on the pod object itself. The fix is to move the label to the pod template, redeploy, and confirm the new pods carry it.

```bash
# Read the labels on a running pod (not the deployment) to confirm the label
kubectl get pod -n payments -l app=payments-api \
  -o jsonpath='{.items[0].metadata.labels}'
```

### Why does the identity lack a role on the target?

Federation establishes who the workload is, but it grants no access. When the identity has no role assignment on the target resource, the token exchange succeeds and the data-plane call then fails with an authorization error, which is a different and more specific failure than a federation problem.

The distinguishing symptom is exactly that split: a token acquires successfully, proven by the management-token check, but the actual operation against Key Vault, Storage, or the database returns a forbidden or access-denied response. Engineers often misread this as a federation failure and go back to checking the subject, when the federation is fine and the gap is purely permissions. The confirmation is to list the role assignments on the target resource scoped to the identity's principal ID and see whether the needed role is present. The fix is to create the role assignment with the least-privilege data-plane role for the operation, scoped to the specific resource. Our guide on managed identities at [/2023/04/17/configure-managed-identities/](/2023/04/17/configure-managed-identities/) details how to choose the right role for each Azure service, because the correct role name is service-specific and not always obvious.

```bash
# List role assignments for the identity's principal on the target scope
az role assignment list \
  --assignee "${PRINCIPAL_ID}" \
  --scope "/subscriptions/<sub-id>/resourceGroups/rg-aks-prod/providers/Microsoft.KeyVault/vaults/kv-payments" \
  --output table
```

### Why is the migration from pod identity left half done?

A migration from the deprecated AAD Pod Identity that stops halfway leaves two systems contending for the same workload, and the result is unpredictable token behavior that depends on which mechanism wins. The symptom is intermittent or environment-specific authentication, where a workload authenticates in one namespace or cluster and not in another that should be identical.

The half-done migration usually looks like this: the workload identity pieces are in place, but the old pod identity components, such as the AzureIdentity and AzureIdentityBinding custom resources and the node-level pod identity components, are still installed and still trying to handle the workload. The two models inject tokens differently and can conflict, especially if the application code still targets the instance metadata endpoint that pod identity intercepted. The confirmation is to look for residual pod identity custom resources and node components in the cluster. The fix is to complete the migration: confirm the workload identity chain works end to end with the verification checks, update the application to use the SDK credential rather than the metadata endpoint, then remove the pod identity custom resources and uninstall its components so nothing competes.

### Why does a multi-namespace or multi-tenant mismatch occur?

A multi-namespace or multi-tenant mismatch happens when one federated credential is expected to serve workloads whose subjects or tenants differ, so the single subject on the credential matches some pods and not others. The symptom is that the same image and the same code authenticate in one place and fail in another.

The subject of a federated credential names exactly one namespace and one service account. If you deploy the same workload into `payments` and into `payments-staging` using the same identity, you need a federated credential for each subject, because `system:serviceaccount:payments:workload-sa` and `system:serviceaccount:payments-staging:workload-sa` are different subjects. A managed identity supports multiple federated credentials, so the fix is to add one credential per subject rather than trying to make one credential cover several. For genuinely separate tenants, the identity and its federation live in their own tenant, and you federate per tenant rather than expecting a single credential to span tenants. The confirmation is to list the federated credentials on the identity and check that every namespace and service account combination that runs the workload has a matching subject.

```bash
# List all federated credentials on the identity to audit the subjects
az identity federated-credential list \
  --identity-name id-payments-workload \
  --resource-group rg-aks-prod \
  --query "[].{name:name, subject:subject, issuer:issuer}" \
  --output table
```


## Migrating Off the Deprecated Pod Identity

AAD Pod Identity was the previous answer to the same problem, and it is now deprecated in favor of workload identity. If you have workloads still on pod identity, the migration is a defined path, and doing it deliberately avoids the half-done state that produces the intermittent failures described above. The two models solve the same problem with fundamentally different mechanics, and understanding the difference makes the migration legible rather than mysterious.

Pod identity worked by running a set of components on the cluster nodes that intercepted calls to the instance metadata endpoint, the same endpoint a virtual machine uses to fetch a managed identity token. An AzureIdentity custom resource named the managed identity, an AzureIdentityBinding tied it to pods matching a selector, and the node-level components answered metadata requests from matching pods with that identity's token. The model was clever but operationally fragile: it depended on node components keeping up with pod scheduling, it had race conditions at pod startup, and it intercepted a node-level endpoint in a way that did not scale cleanly. Workload identity replaces all of that with the federation model, where the trust flows through the OIDC issuer and Entra rather than through a node component intercepting metadata.

The migration path runs in clear phases, and you should complete each phase for a workload before moving to the next, rather than starting many workloads and finishing none. First, enable the OIDC issuer and the workload identity add-on on the cluster, which can coexist with pod identity during the transition. Second, for each workload, create the user-assigned identity, or reuse the one pod identity already used, since the same managed identity can be federated. Third, add a federated credential to that identity for the workload's service account subject. Fourth, annotate the service account with the client ID and label the pod. Fifth, update the application code: pod identity relied on the metadata endpoint, so code that explicitly targeted the metadata endpoint or used an older credential flow should move to the current Azure SDK credential that reads the injected workload identity environment. Sixth, verify the workload acquires a token through the new path using the verification checks. Only after the new path is proven do you remove the pod identity AzureIdentity and AzureIdentityBinding resources for that workload, and once every workload is migrated, uninstall the pod identity node components entirely.

The single most important discipline in the migration is to verify the new path before removing the old one, and to remove the old one once the new one is proven. Leaving both installed is the trap. While both are present, a pod can sometimes get a token through pod identity even though its workload identity configuration is incomplete, which masks a misconfiguration that then surfaces later when pod identity is finally removed, often in an unrelated change window, making the cause hard to trace. Migrate one workload completely, prove it, remove its old binding, and repeat, so that at no point is a workload depending on a mechanism you intend to delete.

A subtle code consideration during migration is the difference between how the two models present the identity to the SDK. Under pod identity, the SDK fetched a token from the metadata endpoint as though it were a virtual machine managed identity. Under workload identity, the SDK reads the projected token file and exchanges it. The current `DefaultAzureCredential` handles workload identity natively when the injected environment is present, so for most applications the migration requires no code change beyond ensuring the SDK is current. Applications that hand-rolled token acquisition against the metadata endpoint, rather than using the SDK credential, are the ones that need code changes, and they are worth refactoring to the SDK credential during the migration so that the next model change is again transparent.

## A Worked End-to-End Diagnosis

Bring the pieces together with a single worked example that starts from a symptom and ends at a fix, the way a real incident unfolds. A team deploys a payments service to AKS. The deployment rolls out, the pods are running and ready, and the service starts. Within seconds the logs fill with authentication errors: the SDK cannot acquire a token to read the database connection string from Key Vault. Nothing in the application changed; the same image ran in staging. The instinct is to suspect the Key Vault, the network, or a transient Entra issue, and the team spends twenty minutes there before stepping back and applying the federation-binds-the-token rule.

They start at the cheapest check. They exec into a pod and grep the environment for the Azure variables. The variables are present and the projected token file exists, so the webhook mutated the pod and the label is correct. That rules out the labeling and add-on layer in one command, which is exactly why it is the first check. Next they decode the projected token and read its claims. The issuer matches the cluster, the audience is the conventional value, and the subject reads `system:serviceaccount:payments:payments-sa`. They open the federated credential and read its subject: `system:serviceaccount:payments:workload-sa`. There is the mismatch. The service account was renamed from `workload-sa` to `payments-sa` in a recent cleanup, the deployment was updated to use the new name, but the federated credential still names the old one.

The fix is one command: update the federated credential's subject to the new service account name, or add a second federated credential for the new subject if the old workload still runs somewhere. They update the subject, the next token request succeeds, and the service authenticates. The whole diagnosis, once they applied the rule, took three commands and under five minutes, against the twenty minutes lost in the wrong layer beforehand. That contrast is the entire argument for internalizing the rule: the failure was a federation mismatch, the application was never the problem, and the diagnostic path went straight to the subject because that is where the rule says to look.

The lesson generalizes. Every workload identity failure resolves to one of the six patterns, and the verification checks discriminate among them quickly. Is the injected environment present? If not, it is the label or the add-on. Does the token decode with the right subject, issuer, and audience? If not, it is the federation mismatch, the disabled issuer, or the audience. Does the token exchange succeed but the data-plane call fail? Then it is the role assignment. Walking those checks in order turns a vague authentication failure into a named cause every time.


## How to Make the Configuration Repeatable as Code

A workload identity chain assembled by hand at the command line works once and is impossible to reproduce reliably, because the steps span two control planes, depend on values read from one resource and fed into another, and are easy to fumble under time pressure. The configuration earns its durability only when it lives as code, so the cluster, the identity, the federated credential, and the role assignment are declared together and applied as a unit. Express the Azure side in Bicep or Terraform and the Kubernetes side in your manifests, and the whole chain becomes reviewable, versioned, and reproducible across environments.

The Azure side has four resources: the managed identity, the federated credential as a child of it, the role assignment on the target, and, if you manage the cluster as code, the cluster with the issuer and add-on enabled. Here is the identity and federated credential expressed in Bicep, parameterized by the issuer URL and the service account subject so the same module serves every workload.

```bicep
// workload-identity.bicep
param location string = resourceGroup().location
param identityName string
param oidcIssuerUrl string
param namespace string
param serviceAccountName string

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
}

resource federatedCredential 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  name: 'fic-${namespace}-${serviceAccountName}'
  parent: identity
  properties: {
    issuer: oidcIssuerUrl
    subject: 'system:serviceaccount:${namespace}:${serviceAccountName}'
    audiences: [
      'api://AzureADTokenExchange'
    ]
  }
}

output clientId string = identity.properties.clientId
output principalId string = identity.properties.principalId
```

The subject is built from the namespace and service account parameters in exactly the format the cluster emits, so the template cannot produce a typo that hand entry would. The outputs expose the client ID for the service account annotation and the principal ID for the role assignment, which you wire into the next module or pass to your deployment pipeline. Notice that the audience is the conventional value, declared once, which removes the audience-mismatch risk because the template is the single source of the value.

The role assignment is a separate resource scoped to the target, and keeping it as code means the access the workload holds is reviewed alongside the federation rather than granted ad hoc. The same shape works in Terraform, where the `azurerm_user_assigned_identity`, `azurerm_federated_identity_credential`, and `azurerm_role_assignment` resources mirror the Bicep, and the issuer URL is read from the cluster data source. Whichever tool you use, the principle is the same: the federation subject is computed from the namespace and service account, never typed, and the role is declared at a specific scope, never broadened for convenience.

On the Kubernetes side, the service account and its annotation and the pod label belong in your manifests, ideally templated so the client ID flows from the infrastructure output into the annotation without a human copying a GUID. If you template with Helm or Kustomize, parameterize the client ID and the service account name so a single values file configures both the annotation and the deployment's service account reference, which keeps the two in sync. The result is that standing up workload identity for a new workload is a matter of supplying a namespace, a service account name, and a target, and the tooling produces a chain that is correct by construction. Our infrastructure-as-code patterns carry over directly here; the discipline of computing the subject rather than typing it is the same discipline that prevents drift in any declarative system.

Repeatability also pays off in disaster recovery and environment parity. Because the federation subject is deterministic from the namespace and service account, recreating the chain in a new region or a rebuilt cluster is a matter of re-running the templates against the new issuer URL. The only value that changes is the issuer, and because the templates take it as a parameter read from the cluster, even that is automatic. A chain built by hand has none of this property; a chain built as code reproduces itself.

## Production Hardening Beyond the Happy Path

Getting a token to flow is the start, not the finish. A production workload identity setup needs a few additional disciplines that the basic chain does not enforce on its own, and they are the difference between a setup that works and a setup that is safe and operable.

The first discipline is least privilege taken seriously. The federation gives the workload an identity; the role assignment gives it power. Scope every role assignment to the narrowest resource and the most specific data-plane role that the operation requires, and resist the convenience of a broad role at a resource group or subscription scope. A workload that needs to read three secrets does not need read access to every secret in the vault if you can scope it, and it certainly does not need management-plane rights. The whole security argument for workload identity is that a compromised pod yields a token scoped to exactly what you granted; an over-broad grant throws that argument away. Our complete guide to securing AKS clusters at [/2024/02/12/securing-aks-clusters-guide/](/2024/02/12/securing-aks-clusters-guide/) places workload identity in the broader hardening picture, alongside network policy, pod security, and image provenance, because a credential-free workload is one layer of a defense in depth rather than the whole defense.

The second discipline is auditability. Because the identity is an Entra principal and the access is an Azure role assignment, every action the workload takes against a target resource appears in the resource's diagnostic logs attributed to that principal, and the role assignment itself is visible in the activity log. Configure diagnostic settings on the target resources so that data-plane access is logged, and you gain a clear record of what each workload did, which a stored connection string never gave you because every caller looked identical. The auditability is a direct benefit of using a per-workload identity rather than a shared secret, and it is worth designing for deliberately by giving each meaningful workload its own identity rather than sharing one across many.

The third discipline is one identity per workload, or at least per trust boundary. It is tempting to create a single identity and federate many service accounts to it, and the mechanism allows it, but doing so collapses the audit trail and the blast radius into one principal. When a workload has its own identity, its access is independently scoped, its actions are independently attributed, and revoking or rotating it affects nothing else. The cost is a few more resources, which infrastructure as code makes cheap, and the benefit is that the principle of least privilege and the audit trail both hold at the workload level.

The fourth discipline is treating the federation as configuration that drifts. A federated credential's subject is tied to a namespace and service account name, and those can change as the platform evolves. When a team renames a namespace, splits a service, or reorganizes service accounts, the federation must move with it, and if the federation lives as code next to the workload, the change is caught in review. If it lives as a one-time CLI command nobody remembers, the change silently breaks authentication weeks later. Keeping the federation in the same repository as the workload that depends on it is the structural fix for this class of drift.


## The Counter-Reading: Why Tokens Do Not Arrive on Their Own

Two beliefs cause most of the early frustration with workload identity, and both deserve to be confronted directly because they feel reasonable and are wrong. The first belief is that a pod should get a token simply because it runs in AKS, the way a virtual machine gets a managed identity token from the metadata endpoint. The second belief, held by teams coming from the older model, is that pod identity is good enough and the migration can wait.

The first belief misreads where the trust lives. A virtual machine gets a managed identity token because the Azure fabric knows which identity is assigned to that virtual machine and answers the metadata endpoint accordingly; the trust is anchored in the fabric's knowledge of the machine. A pod is not a machine the fabric tracks individually, so there is no fabric-level mapping from a pod to an identity. Workload identity supplies the missing mapping through federation: the cluster signs a token that names the service account, and Entra trusts that token because a federated credential told it to. Without the federated credential and the enabled issuer, there is nothing for the fabric to consult and no trust to exercise, so no token arrives. Expecting a token without federation is expecting a trust relationship that was never declared. Once you see that the federation is the trust, the requirement to configure it stops feeling like bureaucracy and starts feeling like the obvious place the trust must be expressed.

The second belief, that pod identity can wait, underestimates the cost of running a deprecated mechanism. Deprecated does not mean broken today, but it means no new investment, eventual removal, and growing distance from the supported path. The operational fragilities of pod identity, the startup races and the node-component coupling, do not improve, and every month on the old model is a month of accruing migration debt against a deadline you do not control. The migration is not large for a single workload, and doing it now, while you have the context and the cluster is calm, is far cheaper than doing it under pressure when the old model is finally withdrawn. The counter-reading that the migration can wait is the counter-reading that turns a planned afternoon into an unplanned incident.

There is a narrower and more legitimate counter-reading worth acknowledging: not every workload needs its own federated identity. A pod that talks only to other pods inside the cluster, never reaching an Azure resource, needs no Azure credential at all, and bolting workload identity onto it adds configuration for no benefit. Workload identity earns its place exactly when a pod must authenticate to an Azure resource outside the cluster, such as Key Vault, Storage, a database, or a service bus. For purely in-cluster communication, Kubernetes-native mechanisms are the right tool, and reaching for workload identity there is over-engineering. The skill is matching the mechanism to the boundary the call crosses.

## How Workload Identity Fits the AKS Cluster Model

Workload identity does not exist in isolation; it is one capability of the cluster, and it interacts with the way AKS schedules pods, manages nodes, and exposes its control plane. Holding the cluster model in mind makes several behaviors legible that otherwise look arbitrary. The OIDC issuer is a property of the cluster control plane, which is why enabling it triggers a control-plane update and why the issuer URL is regional and cluster-specific. The mutating webhook that injects the token runs as part of the add-on, which is why the add-on must be enabled for any token to be projected, and why the webhook acts at pod admission time rather than at scheduling time. The projected token is a Kubernetes service account token feature, which is why the subject takes the `system:serviceaccount` form and why the namespace is part of the identity.

Because the webhook acts at admission, a pod that was already running before the add-on was enabled will not retroactively gain the injection; it must be recreated so that admission runs again. This explains a confusing observation: enable the add-on, and existing pods still cannot get tokens until they are restarted, while new pods work immediately. The fix is simply to roll the workloads after enabling the add-on, which forces fresh admission. If you have never built or operated an AKS cluster at the level these behaviors assume, our service deep dive on Azure Kubernetes Service at [/2022/01/17/azure-kubernetes-service-aks-explained/](/2022/01/17/azure-kubernetes-service-aks-explained/) lays out the node, pod, and control-plane model that workload identity sits on top of, and reading it first makes the federation chain far easier to reason about.

The cluster model also shapes how you think about scale. A single managed identity can hold many federated credentials, and a single cluster can host workloads in many namespaces, each with its own service account and its own federation. This composes cleanly: the issuer is shared across the whole cluster, while the federation is per service account, so you scale the model by adding federated credentials and identities rather than by touching the cluster-level issuer again. That separation, a shared issuer and per-workload federation, is the property that lets workload identity serve a large multi-tenant cluster without the configuration becoming unmanageable, provided you keep the federation in code so the growing set of credentials stays reviewable.

A final cluster-level consideration is upgrade and rotation. The signing keys behind the issuer rotate, and the SDK and the projected token machinery handle that rotation transparently, which is why you do not manage keys by hand. The thing you do manage is the issuer URL stability across cluster lifecycle events: recreating a cluster produces a new issuer, so a disaster-recovery rebuild requires re-pointing the federated credentials at the new issuer URL, which is exactly the parameter your infrastructure-as-code templates already take. The cluster model and the repeatability discipline reinforce each other here, because the one value that changes across a rebuild is the one value the templates were already designed to receive.

## Operating Workload Identity at Scale With GitOps

A single workload's federation is easy to reason about; a cluster running dozens of workloads, each with its own identity and federated credential, is where operational discipline starts to matter. The property that makes scale tractable is the separation between the shared cluster issuer and the per-workload federation. The issuer is enabled once and never touched again under normal operation, while each new workload adds an identity, a federated credential, and a role assignment. Because those per-workload resources are small and independent, the set grows linearly with the number of workloads rather than entangling, provided you never share an identity across trust boundaries and never broaden a role to cover several workloads at once.

GitOps fits this model naturally, and adopting it removes most of the drift that bites hand-managed federation. In a GitOps flow, the Kubernetes manifests, including the service account with its client-ID annotation and the deployment with its workload identity label, live in a repository and are reconciled into the cluster by a controller. The Azure-side resources, the identity and federated credential and role assignment, live as infrastructure code and are applied by a pipeline. The two repositories together describe the complete chain for every workload, and a review of a change to either side shows reviewers the federation a workload depends on. When a team renames a service account, the manifest change and the federated credential change appear in the same review, which is the structural defense against the renamed-subject failure that otherwise surfaces weeks later. The deploy model that GitOps assumes also makes the admission-time behavior of the webhook a non-issue, because reconciliation recreates pods through normal rollout, so newly labeled workloads pass through admission with the add-on active.

At scale you also want a convention for naming and a way to audit the whole set. A naming convention that ties the identity name, the federated credential name, the namespace, and the service account together makes the relationships legible at a glance, so that reading the identity list tells you which workload each one serves. An audit script that lists every identity, enumerates its federated credentials, and reads each subject lets you confirm that every running service account has a matching credential and that no credential names a service account that no longer exists. Stale federated credentials, ones whose subject points at a deleted service account, are not a security hole on their own, because they cannot mint a token for a service account that does not exist, but they are clutter that obscures the audit, and removing them as part of decommissioning a workload keeps the set honest. The same infrastructure code that creates the chain should delete it when the workload retires, so the federation set always reflects the workloads that actually run.

The payoff of this discipline is that a large cluster's authentication posture stays comprehensible. Anyone can read the code, see which workload holds which identity, see what role that identity has on which target, and see the exact service account subject the federation trusts. That comprehensibility is worth as much as the security of the model itself, because a security mechanism nobody can audit is a mechanism nobody can trust, and the per-workload federation kept in code is auditable by construction.

## Why Federation Beats Stored Secrets

It is worth stating plainly what workload identity replaces and why the replacement is better, because the contrast sharpens every configuration decision. The thing it replaces is a stored secret: a connection string, a client secret, an account key, or a certificate, placed into a Kubernetes Secret, an environment variable, or a configuration file, and read by the application to authenticate. That model has three structural problems that no amount of careful handling fully solves, and workload identity removes all three rather than mitigating them.

The first problem is that a stored secret is a static credential that does not expire on its own, so a leak is durable. If a connection string ends up in a log, a crash dump, a backup, or a screenshot, it remains valid until someone notices and rotates it, and rotation is manual work that teams defer. A federated token is short-lived and minted on demand, so a token that leaks expires in minutes and a compromised pod yields nothing reusable. The difference is not incremental; it is the difference between a credential an attacker keeps and a credential that evaporates.

The second problem is rotation. A stored secret must be rotated periodically to limit exposure, and rotation across a fleet of workloads is error-prone, often skipped, and a frequent cause of outages when a rotation breaks a workload that still holds the old value. Workload identity has no secret to rotate, because the trust is the federation and the token is ephemeral. The signing keys behind the issuer rotate automatically and transparently, so the rotation burden that consumes operational time under the secret model simply does not exist. Eliminating an entire category of recurring work is a larger benefit than it first appears, because it removes both the labor and the outages that labor occasionally causes.

The third problem is attribution. When many workloads share a connection string or an account key, every call against the target looks identical in the logs, so you cannot tell which workload did what. A per-workload identity attributes every action to a distinct Entra principal, so the target resource's diagnostic logs name the workload behind each call. That attribution turns an opaque access log into an accountable one, which matters for both security investigation and ordinary operational debugging. The secret model cannot offer this because the secret carries no identity beyond itself, while the federation model carries the workload's identity into every call by design.

Set against these benefits, the cost of workload identity is the configuration effort this guide describes, which is small per workload and one-time, and the discipline to keep the federation in code. That trade is heavily favorable for any workload that authenticates to an Azure resource, which is why federation is the right default and a stored secret is the exception that needs a specific justification. The configuration steps stop feeling like overhead once you see them as the price of removing leak durability, rotation labor, and attribution blindness all at once.

## Timing, Propagation, and What to Expect After Each Change

A practical frustration that catches newcomers is propagation delay. Several of the changes you make do not take effect the instant a command returns, and mistaking a propagation lag for a misconfiguration sends people editing things that were already correct. Knowing roughly what to expect after each action keeps you from chasing phantom problems.

Enabling the cluster issuer triggers a control-plane operation that takes time to complete, and the command returns only when that operation finishes, so the published URL is ready once the call succeeds. A role assignment on a target resource is usually effective quickly, but Azure role propagation is eventual rather than instantaneous, so a data-plane call attempted in the first moments after assignment can return a denial that resolves on its own a short while later. If a freshly granted permission seems absent, wait briefly and retry before concluding the assignment was wrong; a denial that clears after a minute or two was propagation, not error.

Changes on the Kubernetes side behave differently because they hinge on admission. Editing a service account annotation does not retroactively alter pods that are already scheduled; the new annotation governs pods created afterward. Adding the use label to a deployment rolls out new pods that pass through the webhook, and those new pods carry the projection while the old ones, if any survive, do not. The reliable habit after any change to the annotation, the label, or the federation is to roll the affected workload so fresh pods pick up the current state through a clean admission, rather than expecting running pods to absorb the change in place.

The federation record itself, created on the side of the managed identity, is effective as soon as the create command succeeds, and a token request that follows will be evaluated against the current record. There is no long propagation for the federation declaration the way there can be for a role assignment, so a token failure immediately after creating the federation record points at the content of the record, the subject or audience or issuer, rather than at a delay. Distinguishing the two timing profiles, near-immediate for the federation declaration and eventual for the access grant, tells you whether a fresh failure deserves a retry or a closer look at the values you entered.

A final timing note concerns deletion and cleanup. Removing a federation record or a role assignment takes effect promptly, so revoking access is fast when you need it, which is part of why per-resource grants are safer than broad ones. Tearing down a workload should remove its federation record, its role assignment, and its Kubernetes objects together, and because each of those revocations is quick, a clean teardown leaves no lingering grant behind. Treating create and delete as symmetric operations, both expressed in code, keeps the whole arrangement honest as workloads come and go.

## Closing Verdict

Workload identity is the correct way to give an AKS pod access to Azure resources, and it is not hard once you hold the right model. The model is a chain of four trust relationships that must line up: the cluster OIDC issuer signs a token, the federated credential declares which issuer, subject, and audience it trusts, the service account is the subject and carries the client-ID annotation, and the labeled pod receives the injected token. The federation-binds-the-token rule follows from that chain and gives you the diagnostic shortcut that saves the most time: a token failure is almost always a federation mismatch, so check the issuer, the subject, and the injection before you ever suspect the application.

Build the chain in the order the dependencies demand, enable the issuer and the add-on first, create the identity and grant it a least-privilege role, federate the exact service account subject, then label the pod, and verify with a real token exchange rather than trusting a clean rollout. Express the whole thing as code so the subject is computed rather than typed and the chain reproduces across environments. Migrate off pod identity deliberately, proving the new path before removing the old, so you never leave the half-done state that produces intermittent failures. Do those things and your workloads authenticate to Azure with short-lived, scoped, auditable tokens and no secret anywhere in the cluster, which is the outcome the whole exercise exists to deliver.


## Frequently Asked Questions

### Q: How do I set up workload identity in AKS from scratch?

Setting up workload identity is a chain of steps that must happen in dependency order. Enable the OIDC issuer and the workload identity add-on on the cluster, then read the issuer URL the cluster publishes. Create a user-assigned managed identity and capture its client ID and principal ID. Create a Kubernetes service account annotated with the client ID. Add a federated credential to the identity whose subject is `system:serviceaccount:<namespace>:<serviceaccount>` and whose audience is the conventional token-exchange value, using the issuer URL you read. Grant the identity a least-privilege role on the target resource using its principal ID. Finally, label the pod template with the workload identity use label and set the service account on the pod. After deployment, verify by exec-ing into a pod, confirming the injected environment and token file, decoding the token claims, and acquiring a real token. Each step has a precise gotcha, and skipping the verification is how a setup that looks complete fails in production.

### Q: How do federated credentials link a pod to Microsoft Entra?

A federated credential is the trust declaration that lets Entra accept a Kubernetes-issued token in exchange for an Entra access token. It is a child object of a managed identity, and it names three things: the issuer, which is the cluster OIDC issuer URL; the subject, which is the service account in the form `system:serviceaccount:<namespace>:<serviceaccount>`; and the audience, which is the conventional token-exchange value. When a pod using the matching service account requests a token, the cluster issues an OIDC token signed by its issuer with that subject and audience. The Azure SDK sends that token to Entra, and Entra checks it against the federated credential: same issuer, same subject, same audience. If all three match, Entra mints an access token for the identity the credential belongs to. The federated credential is therefore the single point where the Kubernetes world and the Entra world agree on who a workload is, which is why a mismatch in any of the three fields breaks authentication.

### Q: How do I bind a Kubernetes service account to an Entra identity?

Binding a service account to an identity takes two coordinated pieces. First, annotate the service account with `azure.workload.identity/client-id` set to the managed identity's client ID, which tells the injected SDK which Entra application to request a token for. Second, create a federated credential on that same identity whose subject names the service account exactly, in the form `system:serviceaccount:<namespace>:<serviceaccount>`. The annotation points the runtime at the identity, and the federated credential lets Entra trust tokens issued for that service account. Both pieces must agree on the identity: the client ID in the annotation and the identity that owns the federated credential must be the same identity. A common error is annotating with the wrong identifier; the annotation wants the client ID, which is the application identifier, not the principal ID or object ID. Once both the annotation and the federated credential are in place and the pod uses the service account and carries the workload identity label, the binding is complete and tokens flow.

### Q: What is the OIDC issuer requirement and why does it matter?

The OIDC issuer is a public endpoint the cluster exposes that publishes an OpenID Connect discovery document and the signing keys for the tokens the cluster issues. It is the foundation of the entire model, because federation works by Entra trusting tokens from a specific issuer. Without an enabled issuer, the cluster does not publish a discovery document, Entra has no issuer to trust, and no federated credential can reference a URL that does not exist. The issuer is a cluster-level feature that must be explicitly enabled; a cluster created without it has no issuer until you run an update, and that update triggers a control-plane change. The issuer URL is regional and cluster-specific, and it is the value every federated credential names in its issuer field. Because it is the root of the trust chain, the issuer is the first thing to check when no pod in a cluster can authenticate: if the issuer is off, nothing downstream can work regardless of how carefully it is configured.

### Q: How do I migrate from AAD pod identity to workload identity?

Migrate one workload at a time, completing each before starting the next. Enable the OIDC issuer and workload identity add-on, which coexist with pod identity during the transition. For the workload, reuse or create a managed identity, add a federated credential for its service account subject, annotate the service account with the client ID, and label the pod. Update the application to use the current Azure SDK credential, which reads the injected workload identity environment, rather than targeting the instance metadata endpoint the old model intercepted. Verify the new path acquires a token end to end. Only then remove the pod identity AzureIdentity and AzureIdentityBinding resources for that workload. Once every workload is migrated and verified, uninstall the pod identity node components. The cardinal rule is to prove the new path before removing the old, and to remove the old once proven, because leaving both installed lets pod identity mask an incomplete workload identity configuration that surfaces later as a confusing intermittent failure.

### Q: How do I grant the workload a role on a target resource?

Federation establishes who the workload is but grants no access; you grant access with an Azure role assignment on the target resource, scoped to the identity's principal ID. Read the principal ID from the managed identity, choose the least-privilege data-plane role that matches the operation, and assign it at the narrowest scope that works. A workload that reads Key Vault secrets gets Key Vault Secrets User scoped to that vault, not a broad administrator role and not a subscription-wide scope. A workload that reads blobs gets Storage Blob Data Reader on the specific account or container. The role determines exactly what a compromised pod's short-lived token could do, so over-granting throws away the security benefit of the model. After assigning the role, verify by acquiring a token and performing the actual operation; if the token exchange succeeds but the operation returns forbidden, the gap is the role assignment rather than the federation, which is a distinct and faster diagnosis.

### Q: Why does my pod get an authentication error even though the deployment succeeded?

A successful deployment proves only that the pod scheduled and started; it proves nothing about token acquisition, because federation is checked when a token is requested, not when the pod is scheduled. The authentication error means one link in the federation chain is broken. Apply the federation-binds-the-token rule and check in order. Exec into the pod and confirm the injected Azure environment variables and projected token file are present; if not, the label or the add-on is the problem. Decode the projected token and compare its subject, issuer, and audience against the federated credential; a difference there is your mismatch. Acquire a token from inside the pod to test the exchange end to end; if that succeeds but the data-plane call fails, the gap is the role assignment. In nearly every case the application code is fine and the failure is in the configuration the code depends on, which is why debugging the SDK call directly wastes time.

### Q: What is the difference between the client ID, principal ID, and object ID?

A managed identity exposes three GUIDs that serve different roles, and confusing them is a frequent source of silent failures. The client ID, sometimes called the application ID, is the application identifier used during the token exchange; it is the value that goes in the service account's `azure.workload.identity/client-id` annotation. The principal ID is the service principal object that holds permissions; it is the value you assign roles to in a role assignment. The object ID can refer to either the application object or the service principal object depending on context, which is part of why the three are confusing. The practical rule is simple: the annotation wants the client ID, and the role assignment wants the principal ID. Because all three are GUIDs presented in adjacent fields by the CLI and portal, capture each into a clearly named variable when you read it and use the variable rather than copying a raw GUID, which is how the wrong identifier ends up in the wrong field.

### Q: Do I need a separate federated credential for each namespace?

Yes, in the common case, because a federated credential's subject names exactly one namespace and one service account, and there is no wildcard in the typical setup. If you run the same workload in `payments` and `payments-staging`, those are two different subjects, `system:serviceaccount:payments:workload-sa` and `system:serviceaccount:payments-staging:workload-sa`, and each needs its own federated credential. A single managed identity supports multiple federated credentials, so the pattern is to add one credential per subject on the same identity rather than trying to make one credential span subjects. This composes cleanly: the issuer is shared across the cluster, and you add federation per service account as you add workloads. When the same image authenticates in one namespace and fails in another, an absent federated credential for the second namespace's subject is the usual cause, and listing the credentials on the identity to audit their subjects confirms it quickly.

### Q: Can I use a system-assigned identity instead of a user-assigned one?

For workload identity the practical choice is a user-assigned managed identity, because it is a standalone Entra object that exists independently of any single resource, can be referenced by name, and can hold the federated credential the model requires. A user-assigned identity survives pod and cluster lifecycle events, can be federated to multiple service accounts when appropriate, and can be granted roles ahead of deployment. A system-assigned identity is tied to the lifecycle of the resource it is created on and does not fit the federated, portable model that workload identity expects. The federated credential is created as a child of the user-assigned identity, and the service account annotation references that identity's client ID. So while the broader managed identity feature supports both kinds, workload identity in AKS is built around the user-assigned identity, and choosing it avoids fighting the model. Our managed identities guide explains the system-assigned versus user-assigned decision in the general case, where the trade-offs differ from the workload identity context.

### Q: How do I verify that the token is actually being injected into my pod?

Verify in three layers from cheapest to most conclusive. First, exec into a running pod and grep its environment for the Azure variables, and confirm the projected token file exists at the expected path; their presence proves the mutating webhook ran, which means the label and add-on are correct. Second, decode the projected token's payload and read its subject, issuer, and audience claims, then compare them against the federated credential to catch a mismatch. Third, acquire a real token from inside the pod by posting the projected token to the Entra token endpoint as a client assertion; a successful response proves the issuer is trusted, the subject matches, and the audience lines up. After that, attempt the actual data-plane operation the workload performs. A clean deployment proves none of this, so always verify with an exercised token exchange rather than trusting that a running pod is an authenticated one.

### Q: What audience value should the federated credential use?

The conventional audience for AKS workload identity is the token-exchange value `api://AzureADTokenExchange`, and it should appear identically on both the federated credential and the projected service account token. Most tooling defaults to this value on both sides, so it usually lines up without intervention, and you should leave it at the default unless you have a specific reason to change it. The audience matters because Entra checks it during the exchange: a token whose audience does not match the federated credential is refused even when the subject and issuer are correct. The trap is customizing the projected token audience on one side, often copied from an unrelated example, while the federated credential keeps the default. The two then disagree and the exchange fails in a way that is hard to spot because the subject and issuer look fine. The safe practice is to declare the audience once in your infrastructure code and let both sides take it from there.

### Q: Why does authentication work in one cluster but fail in another?

Identical workloads behaving differently across clusters almost always trace to a per-cluster value that differs, and the OIDC issuer URL is the prime suspect because it is unique to each cluster. A federated credential created against one cluster's issuer URL will not match tokens from a different cluster, so the same identity and service account fail in the second cluster until a federated credential is added for its issuer. The second suspect is the issuer being enabled on one cluster and not the other, which makes one cluster unable to issue trusted tokens at all. A third is the add-on being enabled in one place and not the other, so the webhook injects the token in one cluster and not the other. The diagnosis is to compare the issuer URL each cluster publishes, confirm the add-on is enabled in both, and confirm a federated credential exists for each cluster's issuer. Because the issuer is the value that legitimately differs, it is where the investigation starts.

### Q: Does workload identity cost anything to use?

Workload identity itself is a configuration capability of AKS and Entra rather than a separately metered service, so the federation, the OIDC issuer, the managed identity, and the federated credential do not carry a usage charge in the way a running compute resource does. You should still verify current pricing and any related charges against the official Azure pricing pages, because pricing and packaging change and any figure in a guide can age. The real cost of workload identity is operational rather than monetary: the time to configure the chain, the discipline to keep it as code, and the care to scope roles and audit access. Against that modest cost sits a substantial saving, because eliminating stored secrets removes rotation work, leak risk, and the incident response that a leaked static credential triggers. For most teams the calculus is straightforward: the configuration effort is small and one-time per workload, and the security and operational benefits are ongoing, so the model pays for itself quickly.

### Q: What happens to the token when it expires, and do I need to refresh it?

The projected service account token has a finite lifetime and is rotated by the kubelet automatically, and the Azure SDK refreshes the Entra access token it derives from that projected token. For ordinary request-response workloads this is entirely transparent: the SDK acquires and refreshes tokens as needed, and you write no refresh logic. The failure mode appears only when an application acquires a token once at startup, caches the raw token string, and reuses it indefinitely; that cached token eventually expires and the call fails hours into the pod's life, which looks like an intermittent and mysterious authentication error. The fix is to let the SDK credential manage the token rather than caching a raw string yourself, because the credential knows the expiry and refreshes ahead of it. As a rule, hold the credential object and request a token through it per operation or let the client library do so, and never hand-cache the token value, and the refresh problem disappears.

### Q: How is workload identity tested in Azure certification exams?

Identity and access topics appear across the Azure administrator and solutions architect certifications, and workload identity sits within the broader managed identity and Entra material those exams assess. Expect conceptual questions about when to use a managed identity rather than a stored secret, scenario questions that ask you to choose the right way for a containerized workload to authenticate to an Azure resource without secrets, and questions that test whether you understand that access requires a role assignment separately from establishing the identity. The exam rewards the same mental model this guide builds: identity is established through federation, access is granted through role-based access control, and the two are distinct steps. For hands-on readiness, being able to enable the issuer, create the federation, and grant a scoped role is the practical skill the scenario questions are checking. Verify the current exam objectives against the official certification pages, because the skills measured are updated over time and the specific weighting shifts between exam versions.

### Q: Can one managed identity be federated to multiple workloads safely?

Technically one identity can hold many federated credentials and serve many service accounts, but doing so trades away two of the model's benefits, so reserve it for cases where the workloads genuinely share a trust boundary. When several workloads share one identity, they share its access and its audit identity, which means a role granted for one workload is held by all of them and the activity log cannot distinguish which workload performed an action. The least-privilege and auditability arguments both favor one identity per workload, where each workload's access is independently scoped and its actions are independently attributed. The cost of more identities is a few more resources, which infrastructure as code makes cheap, and the benefit is a tighter blast radius and a cleaner audit trail. Share an identity only when the workloads are genuinely the same trust domain and the simplification is worth the lost granularity; otherwise give each meaningful workload its own identity and federate per service account.

### Q: Why do my existing pods still fail after I enable the add-on?

The mutating webhook that injects the token acts at pod admission time, which happens when a pod is created, not continuously while it runs. A pod that was already running before you enabled the workload identity add-on never passed through the webhook with the add-on active, so it carries no injected environment or token file and cannot authenticate, while pods created after the add-on is enabled work immediately. This produces the confusing observation that new pods succeed and old pods fail right after you enable the feature. The fix is simply to roll the affected workloads so their pods are recreated and pass through admission again, for example by restarting the deployment. After the roll, the fresh pods carry the injection and authenticate. This admission-time behavior is also why the workload identity label must be on the pod template rather than only on the deployment metadata, because admission evaluates the pod that the template produces.

