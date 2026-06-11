---
layout: post
title: "Azure Storage Security and Encryption"
page_title: "Azure Storage Security and Encryption: Customer-Managed Keys, Data-Plane RBAC, Network Lockdown, and Secure SAS"
date: 2024-02-19
categories: ["Technology"]
tags: ["Azure", "Azure Storage", "Security", "Identity", "Encryption", "Cloud Computing"]
excerpt: "Azure Storage security rests on identity over keys: encrypt with customer-managed keys, scope data-plane RBAC, lock the network, and issue short-lived SAS."
image: "/assets/images/blog/blog-21.webp"
reading_time: 63
author: "james-carter"
last_updated: 2024-02-19
lang: en
---
A storage account holds the data that matters: the customer uploads, the backups, the diagnostic logs, the firmware images, the export drops that three teams pull from on a schedule. Azure Storage security is the discipline of protecting that data, and the first surprise is that an account is also one of the most quietly over-exposed resources in a typical Azure subscription, where the reason is almost never a missing encryption setting. The reason is that the account ships with two long-lived keys that grant total control over every byte, those keys end up pasted into connection strings and shared in chat threads, and the network is left open to the whole internet because nobody got around to changing the default. Closing that gap on purpose is the whole job, and the work has a clear shape once you see the pieces: encryption at rest that you actually control, data access that flows through identity instead of keys, a network path that is private rather than public, and delegated access that is short-lived and scoped rather than a key handed out under a different name.

The encryption part tends to get the attention because it sounds like the hard problem, and it is the part Azure already solved for you. Every storage account encrypts data at rest by default with 256-bit AES, and that encryption cannot be turned off. The part that is left to you, and the part that decides whether an account is genuinely hardened or merely encrypted, is everything around the key: who can read the data once it is decrypted on the wire, where requests are allowed to come from, and whether the credentials that grant access are an account key with godlike reach or an Entra identity scoped to exactly one container with read-only rights. This article works through the whole posture in the order that matters, builds the InsightCrunch storage security checklist as a reference you can apply to any account, and names the single rule that organizes all of it.

![Azure Storage Security and Encryption](/assets/images/blog/blog-21.webp)

## The identity-over-keys rule

If you remember one thing from this article, make it this: the strongest Azure Storage security uses Microsoft Entra ID and data-plane role assignments instead of the account access keys, so disabling shared-key access and issuing user-delegation SAS removes the most common storage exposure there is. That is the identity-over-keys rule, and almost every hardening step below is an application of it. Encryption protects data at rest from someone who steals a physical disk or a database file; it does nothing about a leaked account key, because a leaked key authorizes a perfectly normal, fully decrypted read over the API. The threat that actually causes storage incidents is credential reach, not broken ciphers, and credentials are where identity-based access changes the game.

The account access key is the problem in miniature. Every storage account is created with two 512-bit keys, key1 and key2, and either one authorizes any operation on any resource in the account: read any blob, delete any container, rewrite any file share, drain any queue. There is no scoping. A key cannot be limited to one container or to read-only. It does not expire. It is not tied to a person or a workload you can audit. When that key lands in a connection string in app configuration, a CI variable, a notebook, and a runbook, it has effectively been published to everyone who can read any of those places, and rotating it means coordinating a simultaneous update across all of them or taking an outage. Identity-based access inverts every one of those properties. An Entra principal can be granted read-only access to a single container, the grant is visible in the role-assignment list, it can be revoked in one place, and it never travels as a secret because the token is minted per request and expires in an hour.

### Why is encryption not enough on its own?

Encryption at rest defends against offline theft of the storage medium, not against an authorized API request. A leaked account key produces a request that Azure considers legitimate, so the service decrypts and returns the data exactly as designed. Closing the exposure requires controlling who holds credentials, not strengthening the cipher.

That distinction is the spine of the whole posture. Spend your effort where the risk is. The cipher is handled; the credential and the network are not, unless you handle them. For the broader picture of how an account is structured, the access tiers, redundancy, and resource hierarchy that sit underneath all of this, the [complete guide to Azure storage accounts](/2022/01/31/azure-storage-accounts-complete-guide/) lays out the model this article secures.

## Anatomy of a storage exposure

It helps to walk through how a storage account actually ends up leaking, because the failure is rarely a single dramatic mistake and almost always a chain of small, reasonable decisions that compound. Picture an account that begins life correctly enough. A team creates it to hold report exports, wires up the original application with a connection string, and ships. The connection string carries the account key, because that is what the quickstart used and it worked on the first try, so nobody revisited it.

Six months later the account has accumulated history. A second service was added that needed the same data, and rather than set up a new identity, an engineer copied the existing connection string into the new service's configuration, because it was faster and the deadline was real. A data analyst needed to investigate a discrepancy and was handed the key to query the account from a notebook, which then sat in a shared repository. An operations runbook was written to clean up old exports on a schedule, and it stored the key so it could run unattended. A partner integration needed to pull a nightly file, so someone generated a service SAS, set the expiry two years out so it would not need renewing, and emailed the URL. By now the single key that was minted at creation has been copied into four places, and a long-lived key-signed token is circulating outside the organization entirely.

Then the ordinary thing happens. The shared repository with the notebook is made public by accident, or a laptop with the runbook is lost, or the partner's mailbox is compromised. Whichever it is, an attacker now holds either the account key or a token signed by it, and because neither expires and neither is scoped, the attacker has read, write, and delete access to every byte in the account from anywhere on the internet, since the network was never locked down either. Encryption at rest does nothing, because the request the attacker makes is indistinguishable from a legitimate one. The exposure is total, and the organization has no audit trail of how it was used, because key-based access does not record which principal made which call.

Now replay the same six months with the identity-over-keys rule applied from the start. The original application authenticates with a managed identity holding Storage Blob Data Contributor scoped to the exports container. The second service gets its own managed identity with its own scoped role, so a compromise of one cannot reach through the other. The analyst is granted Storage Blob Data Reader on the one container for the duration of the investigation and the grant is removed afterward, leaving a record in the assignment history. The runbook runs under its own identity. The partner receives a user-delegation SAS scoped to the single nightly file, valid for a few hours, regenerated by an automated job each night, signed by Entra and revocable. Shared-key access is disallowed on the account, so even if any of these credentials leaked, the leaked thing is scoped, short-lived, and traceable, and the account key path that would have made the leak catastrophic is closed entirely. The network denies public traffic, so the leaked credential is useless without a foothold inside the network anyway. The same business needs were met, and not one of them required handing out an unscoped, non-expiring key. That contrast is the whole argument of this article rendered as a story, and the sections that follow are the mechanics of living the second version rather than the first.

## The two planes: management and data

Before the individual controls make sense, you need the mental model that separates them, because mixing the two planes is the single most common source of confusion when an engineer cannot work out why an account is reachable or why a permission is not taking effect. Azure Storage has a management plane and a data plane, and they are governed by entirely different mechanisms.

The management plane is the Azure Resource Manager surface. It is where you create the account, change its SKU, set the firewall rules, toggle whether shared-key access is allowed, configure customer-managed keys, and read the account's properties. Operations here go through `management.azure.com`, and they are authorized by Azure RBAC roles assigned at the subscription, resource group, or account scope. The role that matters most here is Owner or Contributor on the account, plus the specialized Storage Account Contributor. A principal with management-plane rights can change how the account behaves, but management-plane rights alone do not let that principal read a blob. This trips people up constantly: a user with Contributor on the storage account cannot open a container in the portal and see its contents unless they also hold a data role or the portal falls back to the account key on their behalf.

The data plane is the storage service endpoint itself, `blob.core.windows.net`, `file.core.windows.net`, `queue.core.windows.net`, and `table.core.windows.net`. It is where the actual bytes live and where reads, writes, lists, and deletes happen. Data-plane requests are authorized one of three ways: with the account key (shared key), with a shared access signature, or with an Entra token carrying a data-plane RBAC role. The whole identity-over-keys argument lives in the data plane, because that is where credential reach turns into data exposure. When you assign Storage Blob Data Reader to a managed identity, you are operating in the data plane. When you set the firewall to deny public traffic, you are operating in the management plane to constrain the data plane. Keeping these straight tells you immediately where to look when something is wrong: a 403 on a blob read is a data-plane authorization problem, while an account that will not accept your firewall change is a management-plane permission problem.

A useful way to internalize the split is to ask, for any storage security task, whether it changes what the account is or what the account will serve. Changing what the account is, its keys, its network rules, its encryption configuration, is management-plane work. Changing what gets served and to whom, in the moment of a request, is data-plane work. The controls in the rest of this article are deliberately grouped this way: encryption configuration and network rules are management-plane settings you establish once, while the access decisions, the RBAC roles and the SAS tokens, are data-plane mechanisms that govern every individual request.

## Encryption at rest: the default you keep and the key you control

Azure Storage encrypts all data at rest automatically, and this is not a setting you enable. It is on for every account, it uses 256-bit AES in Galois/Counter Mode, it is FIPS 140-2 compliant, and it cannot be disabled. The encryption applies regardless of access tier (hot, cool, cold, or archive), regardless of redundancy option, and regardless of whether the account is Resource Manager or classic. Both the primary region and, for geo-redundant accounts, the secondary region are encrypted. Block blobs, append blobs, page blobs, file shares, queues, and tables are all covered. There is no performance penalty and no additional charge for the baseline encryption, so the question is never whether your data is encrypted at rest. It always is. The only real decision is who holds and controls the key.

By default the key is a Microsoft-managed key. Microsoft generates it, stores it, and rotates it on a schedule aligned to compliance requirements, and you never see it or touch it. For a large fraction of workloads this is the correct choice, because it removes an entire category of operational burden and the encryption guarantee is identical. The reason to move off the default is not stronger encryption, since the algorithm and key length do not change. The reason is control: a requirement to manage rotation yourself, to revoke access to the key on your own authority, to keep the key in a vault under your governance, or to satisfy a regulatory standard that demands customer control of the key material. When any of those apply, you reach for customer-managed keys.

### When should I use customer-managed keys for storage?

Use customer-managed keys when a compliance requirement or internal policy demands that you own key rotation, revocation, and audit, rather than because they encrypt more strongly. The cipher is identical to the Microsoft-managed default. CMK adds governance: you hold the key in Azure Key Vault or Managed HSM, control its lifecycle, and can cut access by disabling the key.

Customer-managed keys for Azure Storage live in Azure Key Vault or in Azure Key Vault Managed HSM, and the storage account is configured to reference that key. The mechanism is envelope encryption. The data is still encrypted with a data encryption key, and that data encryption key is wrapped with your key encryption key in the vault. When you rotate or disable the key in the vault, the storage service loses the ability to unwrap, which is precisely the control point you wanted: revoking the key revokes the account's ability to decrypt, even though Microsoft operates the storage hardware. The wiring has a few hard requirements that engineers miss and then spend an afternoon debugging.

First, the storage account needs an identity that can reach the vault, and a managed identity is the right tool here rather than a secret. You assign the account a system-assigned or user-assigned managed identity, then grant that identity access to the key. Second, the access grant should use Key Vault RBAC with the Key Vault Crypto Service Encryption User role rather than the legacy access-policy model, for the same identity-over-keys reasons that apply everywhere in this article. Third, the vault must have soft delete and purge protection enabled, because if the key can be permanently deleted while the account depends on it, the account's data becomes unrecoverable, and Azure enforces this prerequisite. Fourth, decide between manual and automatic key-version rotation: pointing the account at a key without a version pins it to whatever version is current and follows rotations automatically, while pinning a specific version freezes it until you update the reference.

```bash
# Assign the storage account a system-assigned managed identity
az storage account update \
  --name stcontoso \
  --resource-group rg-data \
  --identity-type SystemAssigned

# Grant that identity the crypto encryption role on the vault (Key Vault RBAC model)
PRINCIPAL_ID=$(az storage account show -n stcontoso -g rg-data \
  --query identity.principalId -o tsv)

az role assignment create \
  --assignee "$PRINCIPAL_ID" \
  --role "Key Vault Crypto Service Encryption User" \
  --scope "/subscriptions/<sub>/resourceGroups/rg-keys/providers/Microsoft.KeyVault/vaults/kv-contoso"

# Point the account at the customer-managed key (no version pinned, so rotation is automatic)
az storage account update \
  --name stcontoso \
  --resource-group rg-data \
  --encryption-key-source Microsoft.Keyvault \
  --encryption-key-vault "https://kv-contoso.vault.azure.net/" \
  --encryption-key-name storage-cmk
```

The most useful framing for a team deciding whether to take on CMK is to treat it as a governance feature with an operational cost, not a security upgrade. If nobody can articulate why the organization needs to control the key, the Microsoft-managed default is the responsible answer, because every CMK deployment adds a dependency: the account now relies on the vault being reachable, the key being enabled, and the identity retaining its role, and a mistake in any of those takes the account offline. Where CMK is genuinely required, store the key in a well-governed vault, and the [Key Vault security best practices](/2024/01/15/key-vault-security-best-practices/) for that vault become part of your storage security posture, because the vault is now in the critical path for your data.

### Infrastructure encryption: the second layer for compliance

For workloads that must meet a standard explicitly requiring two independent layers of encryption, Azure Storage offers infrastructure encryption on top of the standard service-level encryption. When you enable it, data is encrypted twice, once at the service level with the Microsoft-managed or customer-managed key you configured, and once again at the infrastructure level with a separate Microsoft-managed key, using two different algorithms and two different keys. The point is defense against the compromise of a single algorithm or key: if one layer is somehow broken, the other still protects the data.

Two constraints shape how you use it. Infrastructure encryption must be enabled at account creation or on an encryption scope; you cannot toggle it on an existing account after the fact. And the infrastructure layer always uses Microsoft-managed keys, even when your service layer uses a customer-managed key, so this is not a way to get two customer-controlled keys. For most accounts there is no benefit to enabling it, because the single AES-256 layer already meets the requirements of the overwhelming majority of security standards. Reserve it for the regulated cases (some government and financial regimes mandate double encryption) where a control framework names the requirement explicitly, and enable it deliberately at creation time.

```bash
# Infrastructure (double) encryption must be set at account creation time
az storage account create \
  --name stcontosogov \
  --resource-group rg-data \
  --location eastus2 \
  --sku Standard_GRS \
  --kind StorageV2 \
  --require-infrastructure-encryption true \
  --allow-blob-public-access false \
  --allow-shared-key-access false \
  --min-tls-version TLS1_2
```

Notice the other flags on that creation command. They are the secure defaults this article argues for, set at the moment the account is born rather than retrofitted: public blob access denied, shared-key access disallowed, and a minimum TLS version of 1.2. Establishing the posture at creation is the cheapest possible time to do it, because there is no live workload depending on the insecure settings yet.

## Encryption scopes: per-container key control

The account-level encryption settings discussed so far apply to everything in the account, which is fine when one account holds data of a single sensitivity class but limiting when one account holds data belonging to several tenants or several classifications. Encryption scopes solve this by letting you apply distinct encryption configurations to different containers or even individual blobs within the same account. A scope defines which key protects the data assigned to it, and you can create one scope that uses a Microsoft-managed key and another that uses a specific customer-managed key, then assign each container the scope that matches its requirement.

The most common reason to reach for encryption scopes is multi-tenancy. When a single account stores data for several customers and each customer needs their data protected under a key you can rotate or revoke independently, an encryption scope per customer gives you that isolation without the operational overhead of a separate account per customer. Revoking one customer's key through their scope cuts access to their data alone, leaving every other tenant unaffected. The same pattern serves a single organization that mixes data classifications in one account: a scope with infrastructure encryption for the regulated data and a standard scope for the rest, side by side.

```bash
# Create an encryption scope that uses a customer-managed key, then a container bound to it
az storage account encryption-scope create \
  --account-name stcontoso \
  --resource-group rg-data \
  --name tenant-acme-scope \
  --key-source Microsoft.KeyVault \
  --key-uri "https://kv-contoso.vault.azure.net/keys/acme-cmk"

az storage container create \
  --account-name stcontoso \
  --name acme-reports \
  --default-encryption-scope tenant-acme-scope \
  --prevent-encryption-scope-override true \
  --auth-mode login
```

The `--prevent-encryption-scope-override true` flag matters more than it looks. It locks the container so that blobs uploaded into it must use the container's default scope and cannot specify a different one, which stops a client from sidestepping the intended key. Without it, the default scope is merely a default that an upload can override, and the isolation guarantee weakens. For a multi-tenant design where the whole point is that one tenant's data is protected under one tenant's key, the override prevention is what turns the intent into an enforced boundary.

Encryption scopes also interact with infrastructure encryption: a scope can require infrastructure encryption independently of the account, so you can enable double encryption for exactly the containers that need it rather than for the whole account, which is the granular alternative to the account-wide flag set at creation. The trade-off to weigh is operational complexity, since every scope backed by a customer-managed key is another key in the critical path with its own vault dependency, so reserve per-tenant or per-classification scopes for the cases where the isolation is genuinely required rather than applying them by reflex.

## Data-plane access through Entra and RBAC, not keys

This is where the identity-over-keys rule earns its keep. The default way an application reaches a storage account, the one in every quickstart and most legacy code, is the connection string, which embeds an account key. It works immediately, which is exactly why it spreads, and it carries the full set of problems described earlier: unscoped reach, no expiry, no audit trail tied to a principal, and painful rotation. The alternative is to authorize data-plane requests with an Entra identity that holds a data-plane RBAC role, and the difference in posture is large.

Azure Storage exposes a set of built-in data roles that map to the operations a workload actually needs. For blobs, the meaningful ones are Storage Blob Data Reader for read and list, Storage Blob Data Contributor for read, write, and delete, and Storage Blob Data Owner for full control including managing POSIX ACLs on accounts with hierarchical namespace. There are parallel roles for queues (Storage Queue Data Reader, Storage Queue Data Contributor, and more granular message-level roles), for tables (Storage Table Data Reader and Contributor), and for files over the SMB protocol. The point of this catalog is that you grant a workload the narrowest role that lets it do its job, scoped to the narrowest resource it needs, and nothing more. A function that reads images from one container gets Storage Blob Data Reader on that container, not Contributor on the account.

These roles authorize a request when the caller presents an Entra token, and the cleanest way for a workload to present one is a managed identity. A managed identity gives an Azure resource, a function app, a container, a virtual machine, an Entra identity with no secret to store or rotate, and the platform mints and refreshes the token automatically. The application code asks the Azure Identity library for a credential and uses it against the storage SDK; there is no key anywhere.

```python
# Read a blob using a managed identity, no account key in sight
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

credential = DefaultAzureCredential()
client = BlobServiceClient(
    account_url="https://stcontoso.blob.core.windows.net",
    credential=credential,
)

container = client.get_container_client("reports")
blob = container.get_blob_client("2024-q1-summary.csv")
data = blob.download_blob().readall()
```

The role assignment that makes this work is a single command, and the scope on it is the whole control surface. Assign at the container scope when one container is all the workload touches, at the account scope only when it genuinely needs every container, and never broader than the account.

```bash
# Grant a managed identity read-only access to ONE container, not the whole account
az role assignment create \
  --assignee "<managed-identity-principal-id>" \
  --role "Storage Blob Data Reader" \
  --scope "/subscriptions/<sub>/resourceGroups/rg-data/providers/Microsoft.Storage/storageAccounts/stcontoso/blobServices/default/containers/reports"
```

### How do I secure data-plane access to storage?

Authorize requests with Microsoft Entra identities that hold the narrowest data role at the narrowest scope, prefer managed identities so no secret is stored, and disallow shared-key access on the account so account-key and account-SAS requests are rejected. The result is access you can scope, audit, and revoke in one place.

One subtlety catches teams moving from keys to roles: data-plane role assignments can take a few minutes to propagate, so a freshly granted role that returns a 403 for a short window is normal rather than broken. The other common stumble is granting a management-plane role and expecting data access, the plane confusion from earlier. Owner on the account does not by itself read a blob through the Entra path; the principal needs a data role too. When a read fails with a 403 even though the role looks correct, the cause is almost always one of scope, propagation delay, or plane confusion, and the [fix for Azure Storage 403 AuthorizationFailure errors](/2022/08/01/fix-storage-403-authorization-error/) walks through the full diagnosis tree for exactly this failure.

## The full data-role catalog and custom roles

The blob roles get most of the attention because blob storage is the most used service, but each storage service has its own family of data-plane roles, and choosing the right one is the practical core of least privilege. For blobs, the progression runs from Storage Blob Data Reader, which grants read and list, through Storage Blob Data Contributor, which adds write and delete, to Storage Blob Data Owner, which adds management of POSIX-style ACLs on accounts with a hierarchical namespace. There is also Storage Blob Delegator, a role that does not grant data access at all but allows a principal to request the user-delegation key needed to mint a user-delegation SAS, which is how you separate the right to issue delegated access from the right to read the data directly.

Queues carry a parallel set. Storage Queue Data Reader grants peek and read on messages, Storage Queue Data Contributor adds the ability to add and process messages, and finer roles like Storage Queue Data Message Processor and Storage Queue Data Message Sender split the send and receive halves so a producer that only enqueues work cannot also drain the queue. Tables follow the same shape with Storage Table Data Reader and Storage Table Data Contributor. File shares accessed over SMB have their own roles, Storage File Data SMB Share Reader, Contributor, and Elevated Contributor, where the elevated variant adds the ability to modify NTFS permissions on the share. The point of cataloging these is that the right role almost always exists, so reaching for a broad role like Contributor on the account because it was the first thing that worked is leaving precision on the table that the platform already gave you.

When the built-in roles do not fit, custom roles let you define exactly the data actions a workload needs. A custom role is a JSON definition listing the permitted data actions, and it is the tool for a workload that, say, needs to read and write blobs but must never delete them, a separation no built-in blob role expresses. The data action for blob delete can simply be omitted from the role's action list, producing a read-write-no-delete capability that contains the damage a compromised writer can do.

```json
{
  "Name": "Storage Blob Read Write No Delete",
  "IsCustom": true,
  "Description": "Read and write blobs but never delete them.",
  "Actions": [],
  "NotActions": [],
  "DataActions": [
    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read",
    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write",
    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/add/action"
  ],
  "NotDataActions": [],
  "AssignableScopes": [
    "/subscriptions/<sub>/resourceGroups/rg-data/providers/Microsoft.Storage/storageAccounts/stcontoso"
  ]
}
```

Attribute-based access control, ABAC, sharpens this one step further by adding conditions to a role assignment that are evaluated against attributes of the request and the resource. Rather than granting read on a whole container, you can grant read on the container only for blobs that carry a particular index tag or whose path begins with a particular prefix, so a single role assignment can express a rule like "read access, but only to blobs tagged for this project." This collapses what would otherwise be many narrow container-scoped assignments into one assignment with a condition, and it expresses intent that scope alone cannot, since two workloads can share a container while each sees only its own tagged subset. ABAC conditions are written against a defined set of attributes, currently richest for blob storage, and they evaluate at request time alongside the role, so a request that satisfies the role but fails the condition is denied. For a data estate where many principals touch overlapping containers, ABAC is the mechanism that keeps least privilege expressible without an unmanageable sprawl of assignments.

The discipline that ties the catalog together is to start from what the workload does and pick the narrowest expression of exactly that: a built-in reader role where read is all it needs, a built-in contributor where it writes, a custom role where the built-ins grant something it should not have, and an ABAC condition where even a container scope is broader than the workload's true need. Each step down in breadth is a step down in blast radius, and the cost of the narrower grant is almost always smaller than the cost of explaining a breach that a broader grant enabled.

## Shared access signatures done right

Sometimes you must grant access to a client that cannot hold an Entra identity: an external partner downloading a report, a mobile app uploading a photo, a browser fetching a file directly. The mechanism for that is the shared access signature, a signed token appended to a URL that grants limited, time-bound access to a resource. SAS is necessary and useful, and it is also where a great deal of storage exposure originates, because the easy way to make one is the dangerous way. Getting SAS right means understanding that there are three kinds and choosing the one signed by identity.

An account SAS and a service SAS are both signed with the account key. That single fact carries the consequences: a token signed by the account key inherits the key's reach in whatever scope the token defines, it cannot be individually revoked without rotating the key (which invalidates every other token signed by that key), and because it is signed by a static key, it can be issued with an arbitrarily long expiry, which is how long-lived backdoor SAS tokens come to exist. A SAS token does not appear in any audit log at the moment of its creation; anyone with the account key, or with permission to generate one, can mint a token that lives for years, and you would have no record of it.

A user-delegation SAS is the identity-signed alternative, and it is the one Microsoft recommends and the one this article argues for. Instead of the account key, it is signed with a user-delegation key that the storage service issues against an Entra credential. The practical consequences flip every problem with key-signed SAS. The token's permissions are bounded by the Entra principal's own RBAC permissions, so a principal with Storage Blob Data Reader cannot mint a write SAS. The token has a maximum lifetime of seven days, which caps the blast radius of a leak. And the underlying user-delegation key can be revoked, which invalidates the tokens derived from it without touching the account key or disrupting anything else. You get the delegated-URL capability you needed for the external client, without handing out a slice of an account key.

```bash
# Mint a short, read-only user-delegation SAS for ONE blob, signed by Entra (no account key)
END=$(date -u -d "1 hour" '+%Y-%m-%dT%H:%MZ')

az storage blob generate-sas \
  --account-name stcontoso \
  --container-name reports \
  --name 2024-q1-summary.csv \
  --permissions r \
  --expiry "$END" \
  --auth-mode login \
  --as-user \
  --https-only \
  --full-uri
```

The `--auth-mode login --as-user` pair is what makes this a user-delegation SAS rather than a key-signed one; it tells the CLI to authenticate you with Entra and request a user-delegation key rather than reaching for the account key. The discipline that turns the capability into good security is in the parameters: the narrowest permission (`r`, not `rwdl`), the shortest expiry that does the job (an hour, not a month), HTTPS only, scoped to a single blob rather than a container or the account, and where the client's address is known, a source-IP restriction. A SAS that grants read on one blob for one hour from one address is a precision tool. A SAS that grants full permissions on a container for a year is a liability with a URL.

### Disable shared-key access to make the rule enforced rather than aspirational

Everything above is advice until you remove the unsafe option, and Azure gives you the switch to do exactly that. Setting the account property `allowSharedKeyAccess` to false stops the service from honoring any request authorized with the account key, which includes both account-key SAS and service SAS. The behavior is precise and worth stating exactly: with shared-key access disallowed, a service SAS or account SAS (signed by the key) is rejected, while a user-delegation SAS (signed by Entra) continues to work, and direct Entra-token requests continue to work. In other words, flipping this switch does not break identity-based access at all; it only closes the key-based path. That is the whole point.

```bash
# Turn off the unsafe path entirely: reject all shared-key (account-key) authorization
az storage account update \
  --name stcontoso \
  --resource-group rg-data \
  --allow-shared-key-access false
```

One detail surprises people: when `allowSharedKeyAccess` has never been set, its value is null, and null is treated as allowed, so an account is open to shared-key authorization until you explicitly set the property to false. Checking it across an estate is a one-line Azure Resource Graph query, and on a large tenant that query is the fastest way to find the accounts still exposed.

```kusto
// Find every storage account that still permits shared-key (account-key) authorization
resources
| where type =~ 'microsoft.storage/storageaccounts'
| extend sharedKey = tostring(parse_json(properties).allowSharedKeyAccess)
| where isempty(sharedKey) or sharedKey == "true"
| project subscriptionId, resourceGroup, name, sharedKey
```

The migration to disabling shared key is the one piece of this that needs sequencing rather than a flip of the switch, because some clients and some Azure services still authenticate to storage with the account key and will break the moment you disallow it. The order that works is to first turn on logging and identify which callers are using shared-key authorization, then move each of them to an Entra identity or a user-delegation SAS, then disallow shared key once the logs show no shared-key traffic remains. Doing it in that order turns a risky cutover into a measured one.

## Newer delegation controls: user-bound and cross-tenant SAS

The user-delegation SAS has gained finer controls worth knowing about, because they tighten delegated access beyond what the basic token offered and they answer real questions that come up when partners sit outside your tenant. The first is user binding. With a recent signed-version of the token, you can bind a delegated token to a specific end user by supplying that user's Entra object identifier when you create it, so the token is usable only by that one person and only after they prove their identity with an Entra sign-in. A token bound this way stops being a bearer credential that anyone holding the URL can replay, and becomes a credential tied to a verified principal, which removes the largest weakness of a plain delegated token: that whoever obtains the link can use it.

The second is cross-tenant delegation. A delegated token can be bound to an end user who lives in a different Entra tenant, by supplying that user's tenant identifier alongside their object identifier at creation time, which lets you grant a partner in their own directory a token that only their verified user can exercise. This feature is gated: cross-tenant user-bound delegation is not permitted by default and must be enabled on the resource explicitly, because opening cross-tenant delegation widens the set of principals that can be bound to a token and you should turn it on deliberately rather than find it already available. Treating it as off until a specific partner scenario justifies it is the conservative default.

These additions matter because they push delegated access closer to the identity model the rest of this article argues for. A plain user-delegation token is already a large improvement over a token signed by the static credential, since it is Entra-signed, time-capped, and revocable, but it is still a bearer token within its window. Binding it to a verified user closes the bearer gap, so even a leaked URL is inert in anyone else's hands. For the high-value cases, a partner pulling sensitive exports, a one-off grant to a named individual, the binding is the control that turns "anyone with this link, for the next few hours" into "this one verified person, for the next few hours," which is a materially smaller exposure.

The operational cost is modest. Binding requires you to know the recipient's Entra object identifier, and cross-tenant binding requires their tenant identifier and the resource-level enablement, so the friction is gathering those values and flipping the setting once. For routine internal delegation where the consumer is a trusted automated job inside your own boundary, the plain delegated token is fine and the binding is unnecessary ceremony. For delegation that crosses a trust boundary to a human you do not fully control, the binding is the difference between a token that is merely scoped and short and one that is also pinned to the identity you meant to grant. Reach for it where the recipient is a person and the data is sensitive, and keep the simpler token for the machine-to-machine cases inside your own walls.

## Choosing the right access method

With three ways to authorize a data-plane request, the account key, a SAS, and an Entra identity, teams need a rule for which to use when, because the wrong default is how the account-key path spreads. The rule is short: prefer an Entra identity whenever the caller can hold one, fall back to a user-delegation SAS when it cannot, and use the account key essentially never. Everything else is the reasoning behind that ordering.

A caller that runs inside Azure, a function app, a container, a virtual machine, an App Service, can hold a managed identity, and for those callers an Entra identity is always the answer. There is no secret to store, the access is scoped and auditable, and the token is short-lived by construction. A caller that runs outside Azure but belongs to your organization, a build agent or an on-premises service, can hold a service principal or a workload identity, which is still an Entra identity and still the answer. A caller that cannot hold an Entra identity at all, an external partner, an anonymous browser fetching a file, a mobile client you do not control, is the case the SAS exists for, and there the user-delegation SAS is the right tool because it is Entra-signed, time-capped, scoped, and revocable. The account key remains only for the narrow legacy cases where a tool genuinely cannot do anything else, and the goal is to eliminate even those over time.

| Access method | Authorized by | Scope possible | Expiry | Revocable | Use when |
| --- | --- | --- | --- | --- | --- |
| Entra identity (managed identity preferred) | Microsoft Entra token plus data role | Per container, queue, table, or finer with ABAC | Token lasts about an hour, auto-refreshed | Remove the role assignment | The caller can hold an Entra identity, which is the default for in-Azure workloads |
| User-delegation SAS | User-delegation key issued against an Entra credential | Per blob, container, or service, with permission verbs | Up to a 7-day maximum | Revoke the user-delegation key | A client cannot hold an identity but you still want short, scoped, revocable access |
| Account or service SAS | The account key (shared key) | Per resource, but signed by the all-reaching key | Unbounded, can be set arbitrarily long | Only by rotating the account key | Avoid; use only where no other method is possible, and disable once migrated |
| Account key directly | The account key (shared key) | None, total access to the whole account | None | Only by rotating the key | Avoid entirely; disable shared-key access once callers are migrated |

Reading the table top to bottom is reading the posture from best to worst. The methods get less scoped, less time-bounded, and harder to revoke as you descend, and the bottom two share the single property that makes them dangerous: they depend on the account key, which is why disabling shared-key access removes both at once and leaves only the top two methods working. A team that internalizes this ordering stops reaching for the key reflexively and starts asking, for each new caller, the only question that matters: can this caller hold an identity, and if not, can a short user-delegation SAS serve it. The account key stops being the default and becomes the exception you are actively working to remove.

## Locking down the network: firewall and private endpoints

Identity controls who can authorize a request. Network controls where a request is allowed to originate. They are independent layers, and a hardened account uses both, because identity alone still leaves the account's public endpoint reachable from anywhere on the internet, presenting its API surface to every scanner and brute-force attempt that crawls the address space. By default a new storage account accepts traffic from all networks, and the first network decision is to stop doing that.

The storage firewall lets you switch the default action from allow to deny, then add back exactly the sources you trust: specific virtual networks via service endpoints, specific public IP ranges (a corporate egress address, for example), and the trusted-Azure-services exception for platform integrations that need it. With the firewall set to deny by default, an unlisted source is refused at the network layer before authorization is even considered, which means a leaked SAS or even a leaked account key is useless to an attacker who cannot reach the endpoint from an allowed network. That is defense in depth working as intended: the network control compensates for a credential failure, and the credential control compensates for a network gap.

```bash
# Deny by default, then allow only a known corporate egress range and trusted Azure services
az storage account update \
  --name stcontoso \
  --resource-group rg-data \
  --default-action Deny \
  --bypass AzureServices

az storage account network-rule add \
  --account-name stcontoso \
  --resource-group rg-data \
  --ip-address 203.0.113.0/24
```

The stronger network posture, and the one to reach for when the account serves workloads inside Azure, is the private endpoint. A private endpoint projects the storage service into your virtual network as a private IP address, so traffic from your network reaches the account over the Azure backbone and never traverses the public internet. Combined with the firewall denying public access entirely, this removes the public attack surface rather than merely filtering it. The account becomes reachable only from inside your network, which for a backend data store is usually exactly what you want.

### Is a private endpoint enough on its own?

No. A private endpoint removes public network exposure, but it does not authorize anything. A caller that reaches the account over the private endpoint still presents an account key, a SAS, or an Entra token, and the data role or shared-key setting still decides whether the request succeeds. Network and identity are separate layers, and you need both.

Private endpoints introduce one operational requirement that catches teams off guard: DNS. For a client to resolve the account's hostname to the private IP rather than the public one, the virtual network must use the storage private DNS zone (`privatelink.blob.core.windows.net` and its siblings) so the standard `blob.core.windows.net` name resolves privately. Skip the DNS integration and clients keep resolving the public IP, which the firewall then refuses, producing a confusing failure that looks like a permissions problem but is in fact a name-resolution problem. The full sequence of setting up the endpoint, the network interface, and the private DNS zone is involved enough that the dedicated walkthrough of [setting up private endpoints end to end](/2023/05/01/configure-private-endpoints/) is the right reference when you implement this, because the DNS step is where most first attempts go wrong.

A reasonable default for a production data account, then, is private endpoints for the in-Azure consumers, the firewall denying all public access, and any rare external access handled through a narrowly scoped short user-delegation SAS rather than by reopening the public endpoint. That combination gives you a private network path for the workloads that should reach the account and no path at all for everyone else.

## Least privilege applied concretely

Least privilege is easy to nod along to and hard to implement, because the path of least resistance always grants more than is needed: Contributor instead of a specific data role, account scope instead of container scope, full SAS permissions instead of the one verb required. The way to make least privilege real is to translate it into concrete defaults you apply without deliberating each time, and to scope down rather than up by habit.

For data-plane roles, the defaults are straightforward. A workload that reads gets a Reader data role; a workload that writes gets a Contributor data role; almost nothing gets an Owner data role, which exists mainly for managing ACLs on hierarchical-namespace accounts. Scope each assignment to the container or queue or table the workload uses, not the account, unless the workload genuinely spans the whole account. Two applications sharing one account should hold two separate, container-scoped assignments, not one shared account-scoped grant, because the shared grant means a compromise of either application reaches the other's data. The friction of creating per-container assignments is small and the containment it buys is large.

For SAS, least privilege is expressed in the token parameters every time you mint one. The permission string carries only the verbs the client needs, so a download link is `r` and never `rwdl`. The expiry is the shortest window that lets the operation complete, measured in minutes or hours for an interactive operation and capped at the seven-day ceiling that user-delegation SAS enforces. The scope is the single resource where possible, a specific blob rather than a container. And the protocol is HTTPS only, with a source-IP restriction wherever the client's address is predictable. A SAS minting routine that hard-codes these defaults, narrow permission, short expiry, single resource, HTTPS, makes the secure token the easy token, which is the only way least privilege survives contact with a busy team.

The same principle governs who can hand out access at all. The ability to generate a SAS or to assign a data role is itself a privilege, and it should be held by a small set of principals, because a user who can mint SAS tokens can effectively grant access without leaving an audit trail of the grant. Restrict the management-plane roles that allow SAS generation and role assignment, and you shrink the set of people who can quietly widen access.

## The InsightCrunch storage security checklist

Everything above collapses into a checklist you can run against any storage account, in priority order, with the rationale for each step so you know why it matters and not merely that it is on a list. This is the findable artifact for this article: a single reference that turns the identity-over-keys rule into a sequence of concrete controls.

| Priority | Control | Setting or action | Why it matters |
| --- | --- | --- | --- |
| 1 | Disallow shared-key access | `allowSharedKeyAccess = false` | Removes the unscoped, non-expiring account-key path that causes most storage exposure; user-delegation SAS and Entra tokens keep working |
| 2 | Block public blob access | `allowBlobPublicAccess = false` | Stops anonymous container or blob access from being enabled, even by accident, at the account level |
| 3 | Authorize with Entra identities | Assign data roles (Blob Data Reader/Contributor) to managed identities | Gives scoped, auditable, revocable access with no stored secret, instead of a shared key |
| 4 | Scope every assignment narrowly | Container or queue scope, narrowest role | Contains a compromise to one resource rather than the whole account |
| 5 | Deny network by default | Firewall `defaultAction = Deny`, allow only known sources | Refuses unlisted sources at the network layer before authorization, compensating for a credential leak |
| 6 | Use private endpoints for in-Azure access | Private endpoint plus private DNS zone | Removes the public attack surface entirely for backend consumers |
| 7 | Prefer user-delegation SAS | `--auth-mode login --as-user`, short expiry, narrow permission | Entra-signed, time-capped at 7 days, revocable, bounded by the principal's own rights |
| 8 | Enforce modern transport | `minimumTlsVersion = TLS1_2`, HTTPS-only | Rejects weak transport and plaintext, closing downgrade and interception paths |
| 9 | Control the key when required | Customer-managed key in Key Vault with soft delete and purge protection | Gives you rotation, revocation, and audit of the encryption key where compliance demands it |
| 10 | Add infrastructure encryption for regulated data | `requireInfrastructureEncryption = true` at creation | Second independent encryption layer where a standard mandates double encryption |
| 11 | Log and monitor data-plane access | Diagnostic settings to a Log Analytics workspace | Produces the audit trail that authorization decisions need and that key-based access never had |
| 12 | Review access regularly | Audit role assignments and outstanding SAS practices | Catches drift, stale grants, and the shared-key accounts a query reveals |

The order is deliberate. Disabling shared-key access sits at the top because it is the single change that closes the largest exposure, and the controls beneath it either support that move (Entra identities, scoped roles) or add the independent layers (network, encryption, logging) that turn a single hardened account into one with defense in depth. Run the list top to bottom on a new account and you establish the posture at creation; run it against an existing account and you find, in priority order, exactly what is missing.

## The common misconfigurations and the breaches they enable

Security advice lands better when it is attached to the failure it prevents, so here are the recurring patterns engineers report, each described as a problem with its hardening step. None of these is exotic. They are the ordinary ways storage accounts end up exposed, and recognizing the pattern is most of the fix.

The first and most damaging pattern is the widely distributed account key. The account key starts in one place, a connection string for the original app, and then it spreads: a second service copies it, a developer pastes it into a notebook to debug a data issue, an operations runbook stores it to do a cleanup, and a contractor receives it to load a one-time dataset. None of those copies expires, none is scoped, and the key now grants total access to everyone who can read any of those locations. The breach this enables is comprehensive, because the leaked key reads, writes, and deletes everything in the account. The hardening step is to replace each consumer with an Entra identity holding a scoped data role and then disallow shared-key access, which converts the distributed-key problem into a set of scoped, auditable, revocable grants. Where the key was needed because the consumer could not hold an identity, a user-delegation SAS replaces it.

The second pattern is the long-lived SAS that should have been short and identity-signed. A team needs to give a partner access to a file, generates a service SAS because that is the example they found, and sets the expiry a year out so they do not have to deal with it again. That token is signed by the account key, cannot be revoked without rotating the key, and is now a standing credential that nobody is tracking. The breach is the same reach the SAS granted, available to anyone who obtains the URL, for a year, invisibly. The hardening step is the user-delegation SAS: Entra-signed, scoped to the single resource, with a short expiry, revocable through the user-delegation key, and bounded by the issuing principal's own permissions. The partner gets the same working URL; the organization keeps the ability to revoke it and an upper bound on its life.

The third pattern is the open network. The account is left at its default of accepting traffic from all networks because changing it required understanding the firewall and nobody prioritized it. The data is encrypted and perhaps even uses Entra identities, but the public endpoint is reachable from the entire internet, which means every credential leak becomes immediately exploitable from anywhere and the API surface is exposed to continuous scanning. The hardening step is to set the firewall to deny by default and, for in-Azure consumers, to add a private endpoint with its private DNS zone so the account is reachable only from inside the network. The breach this prevents is the conversion of any future credential mistake into an internet-wide exposure.

The fourth pattern is shared-key access left enabled when nothing needs it. Even an account that has moved all its real workloads to Entra identities often still has `allowSharedKeyAccess` at its null default, which means the account-key path remains open as a latent backdoor. The breach is that the key, still present and still all-reaching, can be retrieved by anyone with the management-plane rights to read it and then used for unscoped data access. The hardening step is to verify with logs that no shared-key traffic remains and then set the property to false, which closes the path the workloads no longer use.

The fifth pattern is the assumption that a customer-managed key was needed when it was not, or the reverse, that the Microsoft-managed default was acceptable when a compliance requirement demanded customer control. The breach here is not a data leak but a compliance failure or an operational outage: a CMK deployed without soft delete and purge protection on the vault risks unrecoverable data, while a regulated workload left on the Microsoft-managed default fails an audit. The hardening step is to make the key decision from the actual requirement: Microsoft-managed by default, customer-managed only where governance demands it and only with the vault prerequisites in place.

The sixth pattern is the request for double encryption arriving after the account already exists. A compliance review lands and asks for infrastructure encryption, and the team discovers it cannot be enabled on the running account, only at creation or on a new encryption scope. The hardening step is to plan for it: where double encryption is a known requirement, create the account with `requireInfrastructureEncryption = true` from the start, and where a requirement arrives late, create a new account or encryption scope and migrate the data, because there is no in-place toggle.

## Anonymous public access: the setting to keep off

One exposure deserves its own treatment because it is both common and avoidable: anonymous public read access to containers and blobs. Azure Storage can be configured to serve blobs to unauthenticated callers, which is the mechanism behind public static websites and openly shared assets, and it is genuinely useful for content that is meant to be public. The danger is that the same mechanism, left enabled by default and applied carelessly, turns a container of private data into an openly readable URL that any crawler eventually finds. Public blob exposures are a recurring source of data leaks precisely because nothing about an anonymously readable blob looks wrong from the inside; the data is encrypted at rest, the network may even be partly restricted, and yet the content is one guessed or indexed URL away from anyone.

The control is layered. At the top sits an account-level switch that governs whether public access can be enabled at all. Setting it to disallow public access means no container in the account can be made anonymously readable, regardless of any container-level setting, which is the secure-by-default posture for any account that does not deliberately serve public content. Beneath it, each container has its own public-access level, which can be set to private (no anonymous access), blob (anonymous read of blobs but not container listing), or container (anonymous read and listing). When the account-level switch disallows public access, the container settings are overridden and nothing is served anonymously, which is why the account switch is the stronger and more reliable control.

```bash
# Disallow public access at the account level so no container can be made anonymous
az storage account update \
  --name stcontoso \
  --resource-group rg-data \
  --allow-blob-public-access false
```

The decision is straightforward. If the account never serves content that is meant to be public, disallow public access at the account level and the entire category of accidental anonymous exposure disappears, because no container can opt back in. If the account does serve public content, isolate that content in a dedicated account or at minimum a dedicated container whose public-access level is set deliberately, and keep the private data in an account where public access is disallowed entirely. Mixing public-serving and private data in one account where public access is permitted is the configuration that produces the accidental leak, because it leaves the door open and relies on every future container being configured correctly, which is exactly the kind of standing assumption that eventually fails.

Verifying this across an estate is the same Resource Graph pattern used for shared-key access: query the accounts and flag any where public access is permitted, then confirm each is one that genuinely serves public content rather than one where the default was never changed. Pairing the query with an Azure Policy assignment that denies or audits accounts allowing public blob access makes the posture enforced rather than aspirational, so a newly created account cannot quietly reintroduce the exposure. The combination of the account-level disallow, the dedicated-account pattern for genuinely public content, and the policy that catches drift closes the public-access gap as durably as the identity controls close the credential gap.

## How to verify your storage security posture

Configuring controls is half the job; confirming they are actually in effect is the other half, because a setting that was supposed to be applied and was not is worse than no setting, since it produces false confidence. Verification for storage security is concrete and scriptable, and you should treat it as a routine you run rather than a one-time check.

Start by reading the account's own properties, because most of the posture is visible there. A single `show` command returns whether shared-key access is allowed, whether public blob access is allowed, the minimum TLS version, the network default action, and the encryption key source. Reading these and comparing them to the checklist tells you, in seconds, where a single account stands.

```bash
# Pull the security-relevant properties of an account in one shot
az storage account show \
  --name stcontoso \
  --resource-group rg-data \
  --query "{sharedKey:allowSharedKeyAccess, publicBlob:allowBlobPublicAccess, tls:minimumTlsVersion, network:networkRuleSet.defaultAction, keySource:encryption.keySource}" \
  -o table
```

For an estate rather than a single account, Azure Resource Graph is the tool, because it queries every account across every subscription in one pass. The shared-key query shown earlier finds the accounts still permitting account-key authorization; the same approach finds accounts with public network access, weak TLS, or public blob access enabled. Running these queries on a schedule turns posture verification into a report you can act on rather than a manual sweep nobody has time for.

```kusto
// Estate-wide posture check: accounts that are open to the public network
resources
| where type =~ 'microsoft.storage/storageaccounts'
| extend net = tostring(parse_json(properties).networkAcls.defaultAction)
| extend pub = tostring(parse_json(properties).allowBlobPublicAccess)
| extend tls = tostring(parse_json(properties).minimumTlsVersion)
| where net =~ 'Allow' or pub =~ 'true' or tls != 'TLS1_2'
| project subscriptionId, resourceGroup, name, net, pub, tls
```

To verify the data-plane access itself, list the role assignments on the account and its containers and confirm they match what you expect: the right principals, the narrowest roles, the narrowest scopes, and nothing left over from a project that ended. An assignment to a principal nobody recognizes, or a Contributor where a Reader would do, or an account-scoped grant where a container scope was intended, is exactly the drift this review exists to catch.

```bash
# List the data-plane role assignments on the account and look for over-grants and stale principals
az role assignment list \
  --scope "/subscriptions/<sub>/resourceGroups/rg-data/providers/Microsoft.Storage/storageAccounts/stcontoso" \
  --query "[].{principal:principalName, role:roleDefinitionName, scope:scope}" \
  -o table
```

Finally, verify that logging is on, because the audit trail is part of the posture and not an optional extra. Diagnostic settings should route the account's read, write, and delete events to a Log Analytics workspace, which gives you the record of who accessed what that identity-based access makes meaningful and that key-based access never could. The verification here is simply that the diagnostic setting exists and points at a workspace you retain.

## Monitoring and detecting how clients authorize

Disabling shared-key access is the goal, but you cannot disable it safely until you know who still depends on it, and that knowledge comes from logging. Azure Storage diagnostic logs record, for every data-plane request, the authentication type used, which lets you see at a glance whether traffic is arriving as shared-key, SAS, or Entra-token requests. Routing those logs to a Log Analytics workspace turns the question "is anyone still using the account key" from a guess into a query, and that query is the gate you pass through before flipping the switch.

```bash
# Send blob read/write/delete logs to a Log Analytics workspace
az monitor diagnostic-settings create \
  --name storage-audit \
  --resource "/subscriptions/<sub>/resourceGroups/rg-data/providers/Microsoft.Storage/storageAccounts/stcontoso/blobServices/default" \
  --workspace "/subscriptions/<sub>/resourceGroups/rg-logs/providers/Microsoft.OperationalInsights/workspaces/law-central" \
  --logs '[{"category":"StorageRead","enabled":true},{"category":"StorageWrite","enabled":true},{"category":"StorageDelete","enabled":true}]'
```

Once the logs are flowing, a query over the storage request records grouped by authentication type tells you the composition of traffic. If every request is arriving as an Entra-token or user-delegation request and the shared-key count is zero across a representative window, the account is ready to have shared-key access disallowed. If the shared-key count is nonzero, the same records identify the callers behind it by their IP, user agent, and the operations they perform, which gives you the list of consumers to migrate before you close the path.

```kusto
// Composition of storage traffic by how each request was authorized, last 7 days
StorageBlobLogs
| where TimeGenerated > ago(7d)
| summarize requests = count() by AuthenticationType
| order by requests desc
```

Beyond the migration use, logs are the audit trail that identity-based access makes meaningful in the first place. When access flows through Entra identities, each request carries the identity that made it, so the log answers who read which blob and when, a question the account key could never answer because every key-based request looked identical regardless of who made it. This is one of the underrated payoffs of moving off keys: not only is the access scoped and revocable, it is also attributable, and attribution is what turns a log from noise into evidence. For a regulated workload that must demonstrate who touched sensitive data, the combination of Entra-based access and diagnostic logging produces exactly the record an auditor asks for.

The detection layer extends naturally into alerting. A query that finds shared-key requests after you believed the account was fully migrated, or that finds access from an unexpected network or principal, can drive an alert so a regression or an anomaly surfaces rather than sitting silently in the logs. The point is to make the posture observable: an account whose authorization mix you can see is an account whose drift you can catch, and an account you cannot see is one where the next exposure builds up exactly the way the earlier walkthrough described, one quiet decision at a time, with nothing watching.

## Making the posture auditable and repeatable

A storage account hardened by hand in the portal is hardened until the next account, which someone creates with the defaults because the manual steps live in nobody's memory. The posture survives only if it is encoded: defined as infrastructure so every account is born hardened, and enforced as policy so an account that drifts is flagged or corrected automatically. This is where storage security stops being a checklist someone runs and becomes a property of the environment.

The infrastructure-as-code approach defines the secure account in a template, with the hardened settings baked in, so deploying the template produces a correct account every time. The Bicep below creates an account with shared-key access disallowed, public blob access disallowed, TLS 1.2 enforced, and the network defaulting to deny, the top of the checklist expressed as code.

```bicep
resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'stcontoso'
  location: resourceGroup().location
  sku: {
    name: 'Standard_GRS'
  }
  kind: 'StorageV2'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    allowSharedKeyAccess: false
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
    encryption: {
      requireInfrastructureEncryption: false
      services: {
        blob: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}
```

Codifying the account is the proactive half. The enforcement half is Azure Policy, which evaluates accounts against rules and either reports the non-compliant ones or actively remediates them. The built-in policy definitions cover most of the checklist directly: there are policies that audit or deny storage accounts allowing shared-key access, accounts allowing public blob access, accounts permitting public network access, and accounts not requiring a minimum TLS version. Assigning these at a management group or subscription scope means a new account that violates the posture is flagged the moment it appears, and policies with a deny effect prevent the non-compliant account from being created at all.

```bash
# Assign a built-in policy that denies storage accounts with shared-key access allowed
az policy assignment create \
  --name "deny-storage-shared-key" \
  --display-name "Storage accounts should prevent shared key access" \
  --scope "/subscriptions/<sub>" \
  --policy "8c6a50c6-9ffd-4ae7-986f-5fa6111f9a54" \
  --params '{"effect":{"value":"Deny"}}'
```

The combination is what makes the posture durable. Infrastructure as code ensures the accounts you create are correct; policy ensures the accounts that appear by other means are caught; and the Resource Graph queries from the verification section give you the running report of where the estate actually stands. Together they turn storage security from a thing a person remembers to do into a property the environment maintains, which is the only version of security that holds up as the number of accounts grows past what any individual can track.

When you want to practice the whole sequence on accounts you can break without consequence, [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), where you can stand up an account, enable a customer-managed key, lock the network down to a private endpoint, and issue a user-delegation SAS in a sandbox, working through the exact commands above against live resources until the moves are second nature. The lab environment is where the difference between reading the checklist and owning it gets made, because the DNS step on a private endpoint and the propagation delay on a role assignment are things you learn by doing them rather than by reading about them.

## The verdict: identity first, keys last

Azure Storage security has a center of gravity, and it is not encryption. Encryption at rest is solved for you, on by default, unconfigurable away, and the same strength whether Microsoft holds the key or you do. The decisions that determine whether an account is genuinely secure all sit around access: whether requests are authorized by an Entra identity scoped to one container or by an account key that opens everything, whether delegated access is a short Entra-signed SAS or a year-long key-signed one, whether the account is reachable from the whole internet or only from your network, and whether the unsafe key-based path is left open as a latent backdoor or closed with a single property.

The identity-over-keys rule organizes all of it. Lead with Entra identities and data-plane roles for your workloads, prefer managed identities so there is no secret to leak, use user-delegation SAS for the clients that cannot hold an identity, lock the network down with the firewall and private endpoints, and then disallow shared-key access to make the rule enforced rather than aspirational. Take on customer-managed keys where governance genuinely requires controlling the key, and infrastructure encryption only where a standard names double encryption as a requirement, and otherwise keep the secure defaults. Encode the whole posture as infrastructure and policy so it holds as the estate grows.

The single most consequential action on the list is the one at the top of the checklist: turn off shared-key access. Everything else is layering and refinement; that one switch closes the exposure that causes most real storage incidents, and the fact that user-delegation SAS and Entra tokens keep working through it means the cost of flipping it, once you have moved your callers to identity, is nearly zero. Secure the account the way it should have shipped, with identity first and keys last.

The harder part is keeping the posture once it is set, and that is a matter of habit rather than configuration. Make identity the default question for every new workload, treat a request to distribute a long-lived credential as a signal to redesign rather than a routine grant, review the role assignments and the authorization mix on a schedule so drift surfaces while it is still small, and encode every control so the next engineer inherits the secure version without having to know the history. A team that builds those habits stops fighting the same exposure repeatedly and starts treating a hardened storage account as the ordinary baseline, which is where the real durability of this whole approach lives.

## Frequently Asked Questions

### Q: Is data in Azure Storage encrypted by default?

Yes, and there is nothing to enable. Every storage account encrypts all data at rest automatically with 256-bit AES in Galois/Counter Mode, the encryption is FIPS 140-2 compliant, and it cannot be turned off. It applies across every access tier including archive, every redundancy option, and both the primary and secondary regions for geo-redundant accounts, and it covers block blobs, append blobs, page blobs, file shares, queues, and tables. There is no performance cost and no separate charge for this baseline encryption. Because it is always on, the encryption question for a storage account is never whether data is encrypted at rest but who controls the key that protects it. The default key is Microsoft-managed, which suits most workloads, and you move to a customer-managed key only when you need to own rotation, revocation, and audit of the key material yourself.

### Q: What is the difference between Microsoft-managed and customer-managed keys?

Both encrypt your data with the same 256-bit AES algorithm, so the cryptographic strength is identical. The difference is governance. Microsoft-managed keys are generated, stored, and rotated by Microsoft on a compliance-aligned schedule, and you never interact with them, which removes operational burden. Customer-managed keys live in your Azure Key Vault or Managed HSM, and the storage account references them through envelope encryption, so you control rotation, you can audit key usage, and you can revoke the account's ability to decrypt by disabling the key. The trade-off is dependency: with a customer-managed key the account now relies on the vault being reachable, the key being enabled, and the storage identity retaining its access, and a failure in any of those takes the account offline. Choose customer-managed keys when a compliance requirement or internal policy demands that control, and keep the Microsoft-managed default otherwise.

### Q: What is infrastructure encryption and when do I need it?

Infrastructure encryption adds a second, independent layer of encryption beneath the standard service-level encryption. With it enabled, data is encrypted twice, once at the service level with your Microsoft-managed or customer-managed key and once at the infrastructure level with a separate Microsoft-managed key, using two different algorithms and two different keys, so that if one layer is somehow compromised the other still protects the data. It must be enabled at account creation or on an encryption scope, because there is no way to toggle it on an existing account, and the infrastructure layer always uses Microsoft-managed keys even when your service layer uses a customer-managed key. Most workloads do not need it, because the single AES-256 layer already satisfies the requirements of nearly every security standard. Reserve it for regulated scenarios, some government and financial regimes among them, where a control framework explicitly mandates double encryption.

### Q: Why is using the account access key a security risk?

The account key is unscoped, non-expiring, and untraceable, which is a dangerous combination. Either of the account's two keys authorizes any operation on any resource in the account, with no way to limit it to one container or to read-only. It does not expire on its own, and it is not tied to a person or workload you can audit, so once it spreads into connection strings, CI variables, notebooks, and runbooks, it has effectively been published to everyone who can read those places. A leaked key authorizes a perfectly normal, fully decrypted request that Azure considers legitimate, so encryption does nothing to stop it. Rotating the key means updating every place it lives simultaneously or taking an outage. Identity-based access reverses all of this: an Entra principal can be scoped to one container, the grant is visible and revocable in one place, and the token is minted per request and expires in about an hour.

### Q: How do I secure data-plane access without the account key?

Authorize requests with Microsoft Entra identities that hold a data-plane RBAC role, scoped as narrowly as the workload allows. For blobs the roles are Storage Blob Data Reader for read and list, Storage Blob Data Contributor for read, write, and delete, and Storage Blob Data Owner for full control including ACLs, with parallel roles for queues, tables, and files. Assign the narrowest role at the narrowest scope, a single container rather than the whole account where the workload permits. The cleanest credential is a managed identity, which gives an Azure resource an Entra identity with no secret to store or rotate, and the platform mints and refreshes the token automatically. The application asks the Azure Identity library for a credential and uses it against the storage SDK with no key anywhere. Once your callers are on identities, disallow shared-key access so the account-key path is closed entirely.

### Q: What happens when I set allowSharedKeyAccess to false?

The storage service stops honoring any request authorized with the account key, which includes both account SAS and service SAS tokens, because those are signed by the key. Crucially, identity-based access is unaffected: a user-delegation SAS, which is signed with Microsoft Entra credentials rather than the account key, continues to work, and direct Entra-token requests continue to work. So disabling shared key closes the key-based path without breaking the identity-based one, which is exactly the intent. One detail to watch is that the property is null by default, and null is treated as allowed, so an account permits shared-key authorization until you explicitly set the property to false. Before flipping it, turn on logging to identify which callers still use shared-key authorization, migrate each to an Entra identity or a user-delegation SAS, and then disallow shared key once no shared-key traffic remains in the logs.

### Q: What are the three types of SAS and which should I use?

There are account SAS, service SAS, and user-delegation SAS. An account SAS and a service SAS are both signed with the account key, which means they inherit the key's reach within their defined scope, cannot be individually revoked without rotating the key, and can be issued with an arbitrarily long expiry, which is how long-lived backdoor tokens come to exist. A user-delegation SAS is signed with a user-delegation key that the storage service issues against an Entra credential, and it is the one to use. Its permissions are bounded by the issuing principal's own RBAC rights, it has a maximum lifetime of seven days, and the underlying user-delegation key can be revoked to invalidate derived tokens without touching the account key. Prefer the user-delegation SAS in every case where you need a delegated URL, and pair it with the narrowest permission and the shortest expiry the task allows.

### Q: How do I create a user-delegation SAS?

You authenticate with Microsoft Entra rather than the account key, which tells the storage service to issue a user-delegation key and sign the token with it. In the Azure CLI, the `az storage blob generate-sas` command with `--auth-mode login --as-user` produces a user-delegation SAS, and you add the permission string, the expiry, and the scope. The discipline that turns the capability into good security lives in those parameters: use the narrowest permission such as `r` for a download rather than full `rwdl`, set the shortest expiry that completes the operation rather than reaching for the seven-day maximum, restrict to HTTPS only, scope to a single blob rather than a whole container, and add a source-IP restriction wherever the client's address is predictable. A token granting read on one blob for one hour from one address is a precision tool, while one granting full permissions on a container for a year is a standing liability.

### Q: Is a private endpoint enough to secure a storage account?

No, because a private endpoint controls where requests can originate, not whether they are authorized. It projects the storage service into your virtual network as a private IP so traffic reaches the account over the Azure backbone and never touches the public internet, and combined with the firewall denying public access it removes the public attack surface entirely. But a caller that reaches the account over the private endpoint still presents an account key, a SAS, or an Entra token, and the data role or the shared-key setting still decides whether the request succeeds. Network and identity are independent layers, and a hardened account uses both. The private endpoint also depends on DNS: the virtual network must use the storage private DNS zone so the standard hostname resolves to the private IP, and skipping that integration leaves clients resolving the public IP, which the firewall then refuses, producing a failure that looks like permissions but is in fact name resolution.

### Q: How do I lock down storage network access?

Set the storage firewall's default action to Deny, which refuses all traffic except the sources you explicitly allow back: specific virtual networks through service endpoints, specific public IP ranges such as a corporate egress address, and the trusted-Azure-services bypass for platform integrations that need it. With deny as the default, an unlisted source is refused at the network layer before authorization is even evaluated, so a leaked credential is useless to an attacker who cannot reach the endpoint from an allowed network. For workloads running inside Azure, go further and add a private endpoint with its private DNS zone, which makes the account reachable only from inside your network and removes the public surface rather than merely filtering it. A reasonable production default is private endpoints for in-Azure consumers, the firewall denying all public access, and any rare external access handled through a short, narrowly scoped user-delegation SAS rather than by reopening the public endpoint.

### Q: Why does a blob read return 403 even though I assigned a role?

A 403 on a data-plane read after a role assignment usually comes down to one of three causes. The first is scope: the role may be assigned at a different scope than the request targets, for example at one container when the blob is in another, or at the subscription when you expected the account. The second is propagation: data-plane role assignments can take a few minutes to take effect, so a freshly granted role that returns 403 for a short window is normal rather than broken. The third is plane confusion: a management-plane role such as Owner or Contributor on the account does not by itself authorize a data-plane read, so the principal also needs a data role like Storage Blob Data Reader. Check those three in order, confirm the principal is the one actually making the request, and the cause is almost always among them.

### Q: Should I use customer-managed keys for every storage account?

No. Customer-managed keys add governance, not encryption strength, and they add an operational dependency that most accounts do not need. With a customer-managed key the account depends on the vault being reachable, the key being enabled, and the storage identity retaining its role, and a mistake in any of those takes the account offline, so a CMK deployed carelessly is a reliability risk rather than a security gain. Use customer-managed keys only where a compliance requirement or internal policy specifically demands that you own key rotation, revocation, and audit, and when you do, store the key in a vault with soft delete and purge protection enabled, because without those an accidental key deletion can render the account's data unrecoverable. For everything else, the Microsoft-managed default gives you the identical encryption with none of the operational burden.

### Q: How do I find storage accounts that still allow shared-key access?

Use Azure Resource Graph, which queries every account across every subscription in a single pass. Query the `microsoft.storage/storageaccounts` resource type and inspect the `allowSharedKeyAccess` property, treating both an empty value and `true` as still permitting shared-key authorization, because the property is null by default and null is treated as allowed. The result is the list of accounts where the account-key path remains open, which is the fastest way to find the latent backdoors across a large tenant. The same technique finds accounts with public network access, public blob access, or a weak minimum TLS version by inspecting the corresponding properties. Running these queries on a schedule turns posture verification into a report you act on rather than a manual sweep, and pairing them with Azure Policy assignments lets you both detect and prevent the non-compliant configurations.

### Q: What is the difference between the management plane and the data plane for storage?

The management plane is the Azure Resource Manager surface where you create the account and change its configuration, the SKU, the firewall rules, the encryption settings, and the shared-key toggle, authorized by Azure RBAC roles like Owner, Contributor, or Storage Account Contributor at the subscription, resource group, or account scope. The data plane is the storage service endpoint itself, where reads, writes, lists, and deletes of actual bytes happen, authorized by the account key, a SAS, or an Entra token carrying a data-plane role. The two are governed separately, which is why a user with Contributor on the account cannot necessarily read a blob: management rights change what the account is, while data rights change what it will serve. Keeping the split clear tells you where to look when something fails, since a 403 on a blob is a data-plane problem and a rejected firewall change is a management-plane permission problem.

### Q: How do I make storage security settings repeatable across many accounts?

Encode the posture as infrastructure and enforce it as policy. Define the secure account in a Bicep or ARM template with the hardened settings baked in, shared-key access disallowed, public blob access disallowed, TLS 1.2 enforced, and the network defaulting to deny, so that deploying the template produces a correct account every time. Then assign Azure Policy definitions at a management group or subscription scope to catch accounts created by other means: there are built-in policies that audit or deny storage accounts allowing shared-key access, public blob access, public network access, or weak TLS, and policies with a deny effect stop the non-compliant account from being created at all. Combine that with scheduled Azure Resource Graph queries for a running report of where the estate stands. Together, infrastructure as code, policy enforcement, and estate queries turn storage security into a property the environment maintains rather than a checklist a person remembers.

### Q: Does disabling shared-key access break my existing applications?

It can, which is why you sequence the change rather than flipping the switch. Some clients and some Azure services still authenticate to storage with the account key and will fail the moment shared-key authorization is disallowed, so a blind cutover risks an outage. The safe order is to first enable diagnostic logging and use it to identify exactly which callers are using shared-key authorization, then migrate each of those callers to an Entra identity with a data role or to a user-delegation SAS, and only then set `allowSharedKeyAccess` to false once the logs show no shared-key traffic remains. Done in that order, the change is measured and safe, because you have already moved every dependent caller off the key-based path before you close it. The Resource Graph query for shared-key accounts helps you find the accounts to work through, and the logs tell you when each one is ready.

### Q: How does a user-delegation SAS get revoked?

A user-delegation SAS is signed with a user-delegation key that the storage service issues against an Entra credential, and revoking that underlying key invalidates every token derived from it. This is a meaningful advantage over key-signed SAS, where the only way to invalidate an issued token is to rotate the account key, which simultaneously invalidates every other token signed by that key and forces an update everywhere the key is used. With a user-delegation SAS you can cut off the derived tokens without that collateral damage. The token also carries a hard seven-day maximum lifetime, so even without an explicit revocation it expires on its own within a week, which caps the exposure of a leaked token in a way that an arbitrarily long key-signed SAS never does. Between the revocable key and the bounded lifetime, the user-delegation SAS gives you control over delegated access that the key-signed variants cannot.

### Q: What transport-level settings should I enforce on a storage account?

Require a minimum TLS version of 1.2 and allow only HTTPS traffic. Setting `minimumTlsVersion` to TLS1_2 rejects connections that try to negotiate an older, weaker protocol, closing the downgrade paths that legacy TLS versions leave open, and enabling HTTPS-only traffic with `supportsHttpsTrafficOnly` rejects plaintext HTTP so data in transit is always encrypted on the wire. These are management-plane settings you establish once on the account, ideally at creation, and they cost nothing operationally because any reasonably current client already speaks TLS 1.2. When you issue a SAS, restrict it to HTTPS as well, so the delegated access cannot be exercised over an unencrypted connection. Together these settings ensure that the data which is encrypted at rest and authorized by identity is also protected in transit, completing the picture across the three states of data at rest, in transit, and in use to the extent storage controls reach.

### Q: What are encryption scopes and when would I use them?

Encryption scopes let you apply different encryption configurations to different containers, or even individual blobs, within a single storage account, rather than encrypting everything under one account-level key. Each scope defines which key protects the data assigned to it, so you can have one scope on a Microsoft-managed key and another on a specific customer-managed key in the same account. The common reason to use them is multi-tenancy: when one account stores data for several customers and each needs their data under a key you can rotate or revoke independently, a scope per customer gives that isolation without a separate account per customer, and revoking one scope's key cuts access to that tenant's data alone. Use the prevent-override option on the container so uploads must use the intended scope rather than choosing another, which turns the default into an enforced boundary. Reserve scopes for cases where the per-tenant or per-classification isolation is genuinely needed, since each customer-managed scope adds a vault dependency.

### Q: Can I use a custom role or ABAC to restrict storage access further?

Yes. When the built-in data roles grant something a workload should not have, a custom role lets you list exactly the data actions it needs, for example read and write blobs while omitting the delete action entirely, producing a read-write-no-delete capability no built-in blob role expresses. You define the custom role as JSON with its data actions and assignable scopes, then assign it like any built-in role. Attribute-based access control, ABAC, goes further by adding conditions to an assignment that evaluate against request and resource attributes, so you can grant read on a container only for blobs carrying a particular index tag or path prefix. That collapses many narrow assignments into one with a condition and expresses intent that scope alone cannot, letting two workloads share a container while each sees only its own subset. Together, custom roles and ABAC conditions extend least privilege below the level the built-in roles and container scopes reach, which matters most in dense estates where many principals touch overlapping data.
