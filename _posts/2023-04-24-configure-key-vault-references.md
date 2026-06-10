---
layout: post
title: "Configure Key Vault References in App Service"
page_title: "Configure Key Vault References in App Service and Functions: Syntax, Managed Identity Access, Version Pinning, and Secret Rotation Explained"
date: 2023-04-24
categories: ["Technology"]
tags: ["Azure", "Key Vault", "Managed Identity", "App Service", "Security", "Identity"]
excerpt: "Key Vault references let App Service and Functions read secrets at runtime, but a reference only resolves when the app identity has data-plane access."
image: "/assets/images/blog/blog-59.webp"
reading_time: 63
author: "william-knight"
last_updated: 2023-04-24
lang: en
---
A Key Vault reference is the feature that lets an App Service or Functions app read a secret from Azure Key Vault at runtime without that secret ever appearing in the application's configuration, in source control, or in a deployment pipeline. You put a small reference string in an app setting, and at runtime the platform swaps that string for the live secret value before your code reads it. Done correctly, your connection strings and API keys live in one audited store, your application sees plain environment variables exactly as it always did, and a secret rotation never requires a redeploy. Done incorrectly, the pointer shows as unresolved, your application reads the literal reference string instead of the secret, and you spend an afternoon convinced you have a syntax typo when the real problem is that the application's principal was never granted access to the store.

![Configure Key Vault references in App Service and Functions with managed identity access - Insight Crunch](/assets/images/blog/blog-59.webp)

That last sentence is the whole article in miniature. The single most common failure when wiring up a Key Vault reference is treating it as a string-formatting problem when it is an access-control problem. The reference syntax is the easy part, and the portal will even validate the shape of it for you. What the portal cannot do for you is grant the application's managed identity permission to read the secret on the data plane of the store. If that grant is missing, every pointer you write will fail in exactly the same way regardless of how carefully you typed it, and the error surface gives you very little to go on unless you know where to look. This guide walks the complete setup end to end, in the order that actually works, with the verification step that proves the pointer resolved and the misconfigurations that produce each symptom.

## The identity-resolves-the-reference rule

The claim this article is built on is short enough to memorize and precise enough to debug with. A Key Vault reference resolves only when the application's managed identity has data-plane access to the secret, so a pointer that shows unresolved is an access problem until proven otherwise, not a syntax problem. Call it the identity-resolves-the-reference rule. The reference string tells the platform which store and which secret to fetch. The managed identity is what actually does the fetching, authenticating to the store as the application rather than as you. If that principal has not been granted the right to read secrets in that store, the fetch returns a 403, the platform cannot substitute the value, and the pointer stays in its raw unresolved form. No amount of correcting the string changes that outcome, because the string was never the problem.

Internalizing this rule changes the order in which you debug. The instinct when a pointer fails is to stare at the syntax, retype the secret name, double-check the store URL, and add or remove a trailing slash. That is the wrong first move, because the syntax is the part the portal can validate and the part you can copy from a known-good example. The right first move is to confirm three things in sequence: that the application has a principal at all, that the principal has a data-plane role or access policy on the store, and that the network path from the application to the store is open. Only after those three pass do you return to the string. In practice the syntax is wrong less than one time in ten; the access grant is missing or pointed at the wrong principal far more often, and the network path bites teams who locked down the store firewall before they wired the pointers.

The rule also explains a class of confusing partial failures. References that work in your development environment but fail in production are almost never a syntax difference, because you usually copy the same setting across environments. They are a principal difference: the development application's principal was granted access to the development store, but nobody granted the production application's principal access to the production store, or the two environments share a store and only one principal got the role. References that work on the production slot but fail on a staging slot are the same story at a smaller scale, because each slot can carry its own system-assigned identity that needs its own grant. When you see a pointer resolve in one place and not another, ask which principal is doing the reading in each place and whether each of those identities has access, and the difference usually falls out immediately.

## Prerequisites and the correct order of operations

Setting up Key Vault references in the wrong order is the reason so many first attempts fail, because the steps have a real dependency chain and the portal lets you do them in any sequence you like. You can create a pointer before the application has a principal, before the principal has access, and before the secret exists, and the portal will accept all of it without complaint. The reference simply will not resolve until every prerequisite is in place, and because the failure is silent at configuration time you do not find out until the application reads the value at runtime. The fix is to do the steps in dependency order so that each one is true before the step that depends on it.

The first prerequisite is the store and the secret. You need a Key Vault that the application can reach, and you need the secret to actually exist in it with the name and, if you are pinning, the version you intend to reference. This sounds obvious, but a pointer to a secret that does not yet exist fails identically to a pointer whose principal lacks access, so creating the secret first removes one variable from every later diagnosis. Note the store name and the secret name exactly, including case sensitivity in the secret name, because Key Vault secret names are case-insensitive on lookup but the URI you build should match what you created to avoid confusion.

The second prerequisite is the application's managed identity. The application needs a principal before it can be granted access, so this comes before the access grant. You choose between a system-assigned identity, which is created with the application and tied to its lifecycle, and a user-assigned identity, which is a standalone resource you create once and attach to one or more applications. For a single application reading its own secrets, a system-assigned identity is the simpler choice and the one most setups use. For a fleet of applications that should share the same access, or for a case where you want the principal to outlive any single application, a user-assigned identity is worth the extra step. The choice matters here because it determines which principal you grant access to and, for user-assigned identities, requires one extra configuration setting that we will come back to. If you want the full treatment of when to pick each kind and how to assign it, the deep dive on that exact decision is in [Set Up Managed Identities the Right Way](/2023/04/17/configure-managed-identities/), and this article assumes the principal is in place.

The third prerequisite is the data-plane access grant. With the principal in place, you grant it permission to read secrets in the store. Under the role-based access model this is the Key Vault Secrets User role assigned at the store or secret scope. Under the legacy access-policy model this is an access policy granting the Get secret permission to the principal. This is the step that the identity-resolves-the-reference rule is about, and it is the step most likely to be skipped, because the pointer works the instant you finish the syntax and nobody thinks to check whether the read will actually be authorized. The access model your store uses is a per-store setting, and getting the model wrong is itself a common failure, which is why the broader access picture lives in [Azure Key Vault: The Complete Guide](/2022/03/07/azure-key-vault-complete-guide/).

The fourth prerequisite, and the one teams discover last, is the network path. If the store is open to all networks, the application can reach it and you can skip ahead. If the store has its firewall enabled, restricting access to selected networks or to a private endpoint, then the application must have a network route that the store accepts, and a missing route fails the pointer in a way that looks exactly like an access denial from the outside. Lock the network down only after the pointers resolve over an open path, or at least be aware that you have introduced a second possible failure mode when you do. The order that consistently works is therefore store and secret, then principal, then access grant, then references, then network hardening, verifying resolution at each stage so you always know which step broke it.

## What is the Key Vault reference syntax?

The reference is a specially formatted string you place as the value of an app setting, and the platform recognizes it by its `@Microsoft.KeyVault(...)` wrapper. There are two ways to write what goes inside the parentheses, and they are equivalent in effect but different in what they pin. The first form uses a full secret identifier URI. The second form names the store and secret as separate fields. Both produce the same runtime substitution; the difference is in how you express the target and whether you fix a version.

The URI form looks like this, placed as the value of an ordinary app setting:

```
@Microsoft.KeyVault(SecretUri=https://my-vault.vault.azure.net/secrets/Sql-ConnectionString/abc123def456...)
```

The trailing segment after the secret name is the secret version. If you include it, the pointer is pinned to that exact version forever, and it will keep returning that version's value even after the secret is rotated. If you omit the version and end the URI at the secret name, the pointer tracks the current version, which is the behavior most people actually want:

```
@Microsoft.KeyVault(SecretUri=https://my-vault.vault.azure.net/secrets/Sql-ConnectionString/)
```

The named-fields form expresses the same target without building a URI by hand, which many teams find less error-prone:

```
@Microsoft.KeyVault(VaultName=my-vault;SecretName=Sql-ConnectionString)
```

You can add a version to the named-fields form with a third field when you want to pin:

```
@Microsoft.KeyVault(VaultName=my-vault;SecretName=Sql-ConnectionString;SecretVersion=abc123def456...)
```

A few mechanical details about the string matter more than they look. The wrapper text `@Microsoft.KeyVault` is fixed and case-sensitive in the prefix, so a lowercased `@microsoft.keyvault` will not be recognized as a pointer and will be passed to your application as a literal string. The fields inside the parentheses are separated by semicolons in the named form, with no spaces around them. The store name is the short name, not the full hostname, so it is `my-vault` and not `my-vault.vault.azure.net` in the `VaultName` field, while the URI form does use the full hostname because it is a real URI. Whitespace inside the parentheses is a frequent and invisible cause of a malformed reference, especially when the value was pasted from a document that introduced a stray space or a non-breaking space, so when a pointer that looks perfect refuses to resolve, copying it into a plain text editor that reveals whitespace is a worthwhile check.

The choice between the URI form and the named form is mostly a matter of taste, with one practical lean. The named form is easier to read, easier to template, and easier to generate from infrastructure code because the store and secret are discrete fields you can interpolate. The URI form is what the portal generates when you pick a secret from the picker, and it is the form you will most often see in examples. Whichever you choose, be consistent across a project so that a reviewer scanning app settings is not switching mental models between settings. Neither form is more capable than the other; both can pin a version or track the latest, and both resolve through the same principal and access path.

## How do I configure Key Vault references in app settings?

The fastest correct path is to assign the principal, grant it access, then set the app setting to the reference string. Here is the full sequence using the Azure CLI for an App Service web app, which you can adapt for a Functions app by changing the resource type where noted. Assume a resource group named `rg-app`, a web app named `my-web-app`, and a store named `my-vault` that already holds a secret named `Sql-ConnectionString`.

First, enable the system-assigned managed identity on the application and capture its principal ID, which you will need for the role assignment:

```
az webapp identity assign \
  --name my-web-app \
  --resource-group rg-app \
  --query principalId \
  --output tsv
```

For a Functions app the equivalent command is `az functionapp identity assign` with the same parameters. The command prints the principal ID, a GUID that identifies the application's principal in Entra ID. Save it; the next command needs it.

Next, grant that principal the right to read secrets. Under the role-based access model, assign the Key Vault Secrets User role scoped to the store. You need the store's resource ID, which you can fetch inline:

```
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee <principal-id-from-previous-step> \
  --scope $(az keyvault show --name my-vault --query id --output tsv)
```

If your store still uses the legacy access-policy model instead of role-based access control, the grant is an access policy rather than a role assignment:

```
az keyvault set-policy \
  --name my-vault \
  --object-id <principal-id-from-previous-step> \
  --secret-permissions get
```

You use one of those two commands, not both, depending on which access model the store is configured for. Mixing them is harmless but pointless; only the model the store actually uses will take effect. The Get secret permission is the minimum the pointer needs. References read secrets, so they do not need List, Set, Delete, or any other permission, and granting more than Get violates least privilege for no benefit.

Finally, set the app setting to the reference string:

```
az webapp config appsettings set \
  --name my-web-app \
  --resource-group rg-app \
  --settings "SqlConnectionString=@Microsoft.KeyVault(VaultName=my-vault;SecretName=Sql-ConnectionString)"
```

The setting name on the left, `SqlConnectionString`, is the environment variable your application code reads. The value on the right is the pointer. At runtime your code reads the environment variable `SqlConnectionString` and receives the resolved secret value, with no awareness that a store was involved. That transparency is the point: the pointer is a deployment and security concern, not an application code concern, and your code does not change when you move a value from a plain app setting into a store behind a pointer.

Setting a pointer as a connection string rather than an app setting works the same way, with the pointer placed as the connection string value. For connection strings the platform still substitutes the resolved secret, and the same principal and access rules apply. The only practical difference is where the value surfaces to your application, following the normal App Service distinction between app settings and connection strings, so use whichever slot your application already reads the value from.

## What access does the application principal need for references?

The access the principal needs is narrow and specific: the ability to read the secret value on the data plane of the store, and nothing more. On the role-based access model this is the Key Vault Secrets User role, which grants read access to secret values. On the access-policy model it is the Get secret permission. These two are the same capability expressed in the two access models, and the store uses one model or the other, never both at once for the same operation. A frequent and costly confusion is to grant a management-plane role like Contributor on the store and expect references to work. Management-plane roles let you manage the store resource, change its configuration, and read its properties, but they do not by themselves grant the data-plane right to read a secret's value when the store uses the role-based model. The reference reads a value, which is a data-plane operation, so it needs a data-plane grant. This is one of the most common reasons a pointer fails for someone who is certain they gave the principal access, because they gave it the wrong kind of access.

Scope is the next decision. You can assign the Key Vault Secrets User role at the store scope, which lets the principal read every secret in the store, or at the individual secret scope, which lets it read only that one secret. Vault scope is operationally simpler and is the common choice when an application legitimately needs several secrets from the same store. Secret scope is tighter and is worth the extra granularity when an application should see exactly one secret and you want the access grant to say so. Either works for references; the pointer does not care how broadly the role was scoped, only that the read it performs is covered. Choose the scope that matches the least privilege you actually need, and prefer per-secret scope when one application should not be able to read another application's secrets in a shared store.

The principal selection is where user-assigned identities introduce their one extra step. By default, a Key Vault reference resolves using the application's system-assigned managed identity. If you want references to resolve using a user-assigned identity instead, setting up that principal and granting it access is not enough on its own, because the platform still defaults to the system-assigned identity for the pointer fetch. You must also tell the application which principal to use for references by setting the application's `keyVaultReferenceIdentity` property to the resource ID of the user-assigned identity. Without that property set, your carefully granted user-assigned identity is ignored for reference resolution and the platform tries the system-assigned identity, which may not exist or may not have access, and the pointer fails. With the CLI this is set as a top-level application property rather than an app setting:

```
az webapp update \
  --name my-web-app \
  --resource-group rg-app \
  --set keyVaultReferenceIdentity=<user-assigned-identity-resource-id>
```

The value is the full resource ID of the user-assigned identity, the long path that starts with `/subscriptions/`. This single property is responsible for a large share of user-assigned-identity reference failures, because everything else looks correct: the principal exists, it has the role, the syntax is fine, and yet the reference will not resolve because the application is still trying to read as the system-assigned identity. When you use a user-assigned identity for references, set this property as part of the same change that grants the access, so the two never drift apart. The full picture of which principal does the authenticating, and the difference between the principal types, is covered in [Set Up Managed Identities the Right Way](/2023/04/17/configure-managed-identities/), and when a reference fails with an access denial the diagnostic path is in [Fix Key Vault Access Denied (Forbidden)](/2023/01/16/fix-key-vault-access-denied/).

## Should I pin a secret version in the reference?

Whether to pin a version is the decision that most directly controls how rotation behaves, and getting it backwards is the source of the second most common reference complaint after access denials. A reference that includes a version is pinned to that exact version of the secret. It will return that version's value for as long as the reference exists, and it will keep returning it even after you create a new version of the secret through rotation. A reference that omits the version tracks the secret's current version, so when you rotate the secret and a new current version appears, the reference begins resolving to the new value once the platform refreshes it.

The practical rule that follows is direct. If you want rotation to be picked up automatically, do not pin a version. Reference the secret without a version so the reference always points at whatever the current version is. If you pin a version and then rotate the secret, you will rotate it in the store, see the new version sitting there, and watch your application keep using the old value, and you will reasonably but wrongly conclude that rotation is broken. Rotation is working perfectly; the reference is simply pinned to a version that rotation did not touch. This is a configuration choice masquerading as a bug, and the identity-resolves-the-reference rule has a sibling here: a pinned reference does not pick up rotation, so a value that will not update after rotation is a pinning problem, not a rotation problem.

There are legitimate reasons to pin. If a specific version of a secret is known to work and you want to freeze it while you validate a newer version, pinning gives you that control. If you are coordinating a change across systems and need every component to use the same exact version during a migration window, pinning prevents one component from racing ahead to a new value. If an audit requires that you can prove exactly which secret version a deployment used, a pinned reference records that in the configuration itself. Outside those deliberate cases, pinning is usually a mistake made by copying a URI from the portal picker, which includes the version by default, and then forgetting that the trailing version segment freezes the value. When you copy a URI from the picker and you want rotation to flow, delete the version segment so the URI ends at the secret name.

## How do references pick up a rotated secret?

When a reference is unpinned and tracking the current version, the rotated value reaches your application through the platform's refresh of resolved reference values rather than instantly. App Service and Functions resolve references and cache the resolved values, and they refresh those cached values periodically and when the application restarts or its configuration changes. This means a rotation is not necessarily visible to the application the instant you create the new secret version. The new value becomes visible after the next refresh, or immediately if you restart the application or change a setting, which forces a re-resolution. The exact refresh interval is a platform behavior you should verify against the current official Azure documentation rather than treat as a fixed constant, because the platform's caching and refresh cadence is the kind of detail Microsoft adjusts over time and it has been documented as a periodic refresh measured in hours rather than seconds.

The operational consequence is that rotation has a propagation delay you must design around. If your rotation process needs the new value to be live immediately, do not rely on the background refresh alone; trigger a re-resolution by restarting the application or by touching a setting as the final step of rotation. If a brief window of the old value being served is acceptable, the background refresh is fine and requires no action, and the rotation simply propagates on its own schedule. Either way, the reference must be unpinned for any of this to happen, because a pinned reference never refreshes to a new version regardless of how many times the application restarts.

A subtlety worth holding is the difference between rotating the secret and rotating to a new secret name. Creating a new version of an existing secret is rotation in the sense references understand, and an unpinned reference follows it. Replacing a secret with a differently named secret is not rotation from the reference's point of view; it is a new target, and the reference, which names the old secret, will keep reading the old secret until you change the reference to name the new one. When you plan a rotation strategy, rotate in place by adding versions to the same secret name so your references can follow, rather than minting new names that require a configuration change on every consumer. The security depth on how to rotate well, including the schedule and the operational hygiene around it, is in [Azure Key Vault Security Best Practices](/2024/01/15/key-vault-security-best-practices/).

## The InsightCrunch Key Vault reference checklist

The findable artifact for this article is a single checklist that captures the five things that must be true for a reference to resolve, the gotcha that breaks each one, and the command or place to confirm it. Run down it in order whenever a reference fails, and you will isolate the cause faster than by guessing. The order is deliberate: it follows the dependency chain, so the first failing row is almost always the real cause and the rows below it are noise until the first one passes.

| Step | What must be true | The gotcha that breaks it | How to confirm |
| --- | --- | --- | --- |
| Identity | The app has a managed identity | No identity assigned, or a user-assigned identity attached but not selected for references | `az webapp identity show`; check for a non-empty principal ID, or a user-assigned identity in the list |
| Access | The identity has data-plane read on the vault | A management-plane role like Contributor granted instead of Key Vault Secrets User or the Get secret permission | `az role assignment list --assignee <principal-id>` or `az keyvault show` access policies |
| Identity selection | The right identity is used for references | User-assigned identity granted access but `keyVaultReferenceIdentity` not set, so the system-assigned identity is used | `az webapp show --query keyVaultReferenceIdentity` |
| Syntax | The reference string is well formed | Stray whitespace, lowercased wrapper, vault hostname in the `VaultName` field, or a pinned version when rotation is expected | Compare against a known-good string; reveal whitespace in a plain editor |
| Network | The app can reach the vault | Vault firewall enabled with no route from the app, which fails like an access denial | Open the vault firewall temporarily, or confirm VNet integration and the vault network rules |

The namable claim sits on top of this table. The identity-resolves-the-reference rule says the access rows come before the syntax row, so resist the urge to start at the syntax row just because it is the one you can see in the app setting. The table reads top to bottom for a reason: an application with no principal cannot have access, a principal with no access cannot read a secret no matter how the reference is selected, and a reference that is selected to the right principal with the right access will fail on the network row if the firewall has no route. Working the rows in order means you never chase a syntax ghost while the real cause is two rows up.

The resolution-check column deserves its own emphasis, because the platform gives you a direct signal that most people never look at. App Service and Functions expose the status of each Key Vault reference in the application's configuration view, showing for each setting whether the reference resolved or failed. When a reference resolves, the status is a clean indicator that the value was fetched. When it fails, the status flags the failure and often hints at the category. This status is the fastest single confirmation in the whole checklist, and it is the thing to look at before you touch anything, because it tells you whether you are debugging a resolution failure at all or chasing a different problem entirely.

## The settings the defaults get wrong

Several defaults around Key Vault references quietly point you toward a failure, and knowing them in advance saves the diagnosis. The first is the principal default. A fresh application has no managed identity until you assign one, so the default state of a new application cannot resolve references at all. The portal will let you save a reference on an application with no principal, and the reference will simply never resolve, because there is no principal to read with. The default is no principal, and the reference feature silently depends on you changing that default first.

The second default that bites is the reference identity selection. As covered above, the platform defaults to the system-assigned identity for reference resolution. If you have deliberately set up a user-assigned identity and granted it access, the default works against you, because the platform ignores your user-assigned identity until you explicitly set the `keyVaultReferenceIdentity` property. The default here is correct for the common system-assigned case and wrong for the user-assigned case, so the user-assigned path requires you to override the default.

The third is the version segment in a copied URI. When you pick a secret from the portal's secret picker, the URI it generates includes the specific version. The default behavior of the picker is therefore to pin, which is the opposite of what most teams want because it blocks rotation. If you take the picker's output as-is, you have silently opted into a pinned reference, and you will discover this only when a rotation fails to propagate. The default is pinned; the behavior most people want is unpinned; the gap between those two is a deleted version segment that nobody told you to delete.

The fourth is the store access model default for newer stores. Azure has moved toward role-based access control as the recommended access model for Key Vault, and the model a store uses determines whether you grant a role or an access policy. If you assume your store uses one model and it actually uses the other, your grant lands in the wrong system and the reference fails despite your having granted access. Confirm which model the store uses before you grant, because the grant command differs and the wrong one is a no-op for resolution. The current default model for a newly created store is a value to verify against the official documentation, since Microsoft has shifted this default over time, and the safe move is to check the store's configuration rather than assume.

The fifth is the network default. A store can be created open to all networks or with its firewall enabled, and the references work trivially over an open store. If your security baseline enables the store firewall by default, then your references will fail the moment the firewall is on unless the application has an accepted network route, and the failure will look like an access problem rather than a network problem. The default network posture interacts with the reference feature in a way that is invisible until you harden the store, so treat firewall enablement as a step that requires its own verification of the reference path.

## How do I confirm a Key Vault reference resolved?

The verification step is the part of the setup people skip and then regret, because a reference that fails to resolve does so silently at configuration time and only surfaces when the application reads the value. Verifying resolution directly, before your application ever runs, turns a runtime surprise into a setup-time check. There are three layers of confirmation, from fastest to most thorough, and you should use the fast one always and the thorough ones when the fast one is ambiguous.

The fastest confirmation is the reference status the platform exposes for each app setting. In the application's configuration view, each setting that holds a Key Vault reference shows whether the reference resolved. A resolved status means the platform successfully fetched the value with the application's principal. A failed status means it did not, and the failure category often points at the cause, whether the secret was not found, access was denied, or the store could not be reached. Reading this status takes seconds and answers the binary question of whether resolution succeeded, which is the first thing you need to know. If the status says resolved, the reference is working and any problem your application has with the value lies elsewhere, such as the application reading the wrong setting name.

The second confirmation is to read the value as the application would and check that it is the secret rather than the literal reference string. If a reference fails to resolve, the platform passes the raw `@Microsoft.KeyVault(...)` string through to the application as the value, so an application that logs its configuration, or a diagnostic endpoint that echoes a setting, will show the literal reference text when resolution failed and the real secret value when it succeeded. Be careful here: do not log secret values in production, and use this technique only in a controlled environment or with a setting whose value is not sensitive. The principle is that the unresolved reference is visibly the reference string, so seeing the literal string anywhere your application reads the value is an unambiguous sign that resolution failed for that setting.

The third confirmation is to test the read independently of the reference machinery, which isolates the access and network rows of the checklist from the reference syntax. From a context that uses the app's principal, attempt to read the secret directly. If a direct read with the principal succeeds but the reference still fails, the problem is in the reference layer, most often the principal selection property or the syntax. If the direct read also fails, the problem is access or network, and you have eliminated the reference syntax entirely. This separation is powerful because it cleaves the failure space in half: a working direct read points you at the string and the principal selection, while a failing direct read points you at the role assignment and the firewall. The independent test is the step that ends the guessing, and pairing it with the reference status gives you a near-complete diagnosis without ever running your application.

A practical verification habit ties these together. After setting a reference, look at the status first. If it says resolved, you are done. If it says failed, do an independent read of the secret with the app's principal. If that read works, the issue is reference selection or syntax; if it fails, the issue is access or network. Two checks, in that order, resolve nearly every reference failure, and they are both faster than the redeploy-and-pray loop that teams fall into when they treat resolution as something they can only observe through application behavior.

## The common misconfigurations and their symptoms

Reference failures cluster into a small number of recurring patterns, and once you can name the pattern you can apply the fix without rediscovering it. Each of the following is a real shape that engineers report, with the symptom that identifies it and the configuration step that resolves it.

The first pattern is the reference that will not resolve because the app principal lacks the read role. The symptom is a failed reference status with an access-denied or forbidden category, an app that reads the literal reference string, and a setup where the syntax is provably correct because it matches a known-good example. The cause is that the principal was never granted Key Vault Secrets User on the role-based model, or the Get secret permission on the access-policy model, or it was granted a management-plane role like Contributor that does not cover data-plane reads. The fix is to grant the correct data-plane role at the store or secret scope. This is the single most common reference failure, and the identity-resolves-the-reference rule exists to push you toward checking it first. When the access denial is stubborn even after a grant, the dedicated diagnosis lives in [Fix Key Vault Access Denied (Forbidden)](/2023/01/16/fix-key-vault-access-denied/), which covers the cases where the grant looks present but is not effective.

The second pattern is the version-pinned reference that does not reflect a rotated secret. The symptom is a reference that resolves cleanly, an app that reads a real value, and a rotation that you can see in the store but that the app never picks up. The cause is a version segment in the reference, often inherited from a portal-generated URI, that pins the reference to the version that existed before rotation. The fix is to remove the version so the reference tracks the current version, and then either wait for the platform refresh or restart the app to force re-resolution. This pattern is insidious because nothing looks broken; the reference is green and the value is correct, just stale, and the rotation appears to have failed when it is the pinning that is at fault.

The third pattern is a store firewall blocking the app. The symptom is a reference that resolved fine until the store was locked down and then began failing across every reference at once, with an access or network category, and no change to the principal or the syntax. The cause is that enabling the store firewall removed the open network path the references were using, and the app now has no accepted route to the store. The fix is to give the app an accepted route, which on App Service typically means VNet integration combined with a private endpoint on the store or the store's network rules permitting the integrated subnet, and confirming that the app routes its outbound traffic accordingly. The tell for this pattern is timing: references that all broke at the moment of a firewall change are a network problem, not an access problem, even though the error category can look the same.

The fourth pattern is a reference syntax error in the setting. The symptom is a single reference failing while others in the same app resolve, a failed status, and an app reading the literal string for just that one setting. The cause is a malformed string: a stray space, a lowercased wrapper prefix, a store hostname placed in the `VaultName` field where the short name belongs, a missing semicolon between fields, or a secret name that does not match what exists in the store. The fix is to correct the string against a known-good template, paying special attention to invisible whitespace. The reason this pattern is identifiable is that it is localized to one setting; when only one reference fails and the rest work, the shared prerequisites like principal and network are proven good, so the difference must be in the string for that one setting or in that one secret's existence.

The fifth pattern is a slot that does not inherit the access. The symptom is a reference that resolves on the production slot and fails on a staging or deployment slot, with the same syntax in both because the setting was cloned. The cause is that each slot can carry its own system-assigned identity, and granting the production slot's principal access to the store does not grant the staging slot's principal anything. The fix is to grant each slot's principal its own data-plane access, or to use a user-assigned identity shared across slots with the `keyVaultReferenceIdentity` property set on each. This pattern is a direct corollary of the identity-resolves-the-reference rule applied to slots: different slots can be different identities, and a reference resolves per the principal doing the reading in that slot.

The sixth pattern is references working in one environment but not another. The symptom is identical configuration across environments, the same reference strings, and resolution succeeding in development while failing in production or the reverse. The cause is almost always a principal-to-store access difference: the development app's identity has access to the development store, but the production app's identity was never granted access to the production store, or the environments share a store and only one identity got the role. The fix is to grant each environment's app identity access to that environment's store, and to make the grant part of the environment provisioning so it cannot be forgotten. The reason this pattern is so common is that the reference string is the thing teams copy between environments, while the access grant is the thing they have to redo per environment, so the copied part works and the per-environment part is the one that gets skipped.

## A worked end-to-end setup with verification

To make the order and the verification concrete, here is a complete walk from an app with nothing wired to a reference that provably resolves, with a deliberate failure injected and diagnosed so you can see the checklist in action. The scenario is a web app `my-web-app` in resource group `rg-app` that needs a database connection string held as the secret `Sql-ConnectionString` in the store `my-vault`, which uses the role-based access model.

Start by confirming the secret exists, because a reference to a missing secret fails identically to an access denial and you want that variable removed first:

```
az keyvault secret show \
  --vault-name my-vault \
  --name Sql-ConnectionString \
  --query "attributes.enabled" \
  --output tsv
```

A return of `true` confirms the secret exists and is enabled. If the command errors with a not-found, the secret does not exist under that name, and no reference will resolve until you create it. Next, assign the system-assigned identity and capture the principal ID:

```
PRINCIPAL_ID=$(az webapp identity assign \
  --name my-web-app \
  --resource-group rg-app \
  --query principalId \
  --output tsv)
echo "Principal: $PRINCIPAL_ID"
```

Grant that principal the data-plane read role at the store scope:

```
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee "$PRINCIPAL_ID" \
  --scope $(az keyvault show --name my-vault --query id --output tsv)
```

Now set the reference, unpinned so rotation will flow later:

```
az webapp config appsettings set \
  --name my-web-app \
  --resource-group rg-app \
  --settings "SqlConnectionString=@Microsoft.KeyVault(VaultName=my-vault;SecretName=Sql-ConnectionString)"
```

Verify resolution. The fastest check is the reference status, which you can view in the app's configuration in the portal, where the setting should show as a resolved Key Vault reference. To confirm from the command line that the platform sees the setting as a reference and to inspect its state, list the settings and look at the value:

```
az webapp config appsettings list \
  --name my-web-app \
  --resource-group rg-app \
  --query "[?name=='SqlConnectionString']"
```

The stored value is the reference string, as expected; the resolution status itself is surfaced in the portal configuration view and through the app's runtime behavior. To prove the value resolves at runtime, deploy a controlled diagnostic in a non-production context that echoes the resolved length of the setting without printing the secret, or simply observe that the application functions, since a failed resolution would leave the literal reference string in the environment variable and the database connection would fail with a malformed connection string rather than an authentication error.

Now inject the classic failure to see the diagnosis. Remove the role assignment and watch the reference break:

```
az role assignment delete \
  --role "Key Vault Secrets User" \
  --assignee "$PRINCIPAL_ID" \
  --scope $(az keyvault show --name my-vault --query id --output tsv)
```

Restart the app to force re-resolution, then look at the reference status in the portal. It now shows a failed reference with an access-denied category, and the app reads the literal `@Microsoft.KeyVault(...)` string. Walk the checklist: identity row passes because the app has a principal ID, syntax row passes because the string is unchanged and was working a moment ago, so the access row is the suspect. Confirm by listing role assignments for the principal, find the role gone, and re-add it. After the role returns and the app re-resolves, the status flips back to resolved. That round trip, from working to broken to diagnosed to fixed, is the muscle memory the checklist is meant to build, and it shows why the access rows come before the syntax row in the diagnosis order.

## How do I make a Key Vault reference resolve when the store has a firewall?

When the store is open to all networks the reference path is trivial, but production stores are usually locked down, and the network row of the checklist becomes the one that breaks setups. A store with its firewall enabled accepts traffic only from the networks or private endpoints you permit, and an App Service app does not have a fixed, easily allowlisted set of outbound addresses by default, so simply enabling the firewall cuts the references off. The reliable answer is to integrate the app with a virtual network and route the reference traffic through a path the store accepts.

The common production shape is VNet integration on the app combined with a private endpoint on the store, so that the app's outbound traffic to the store travels over the private network and the store's public exposure can be removed entirely. With this design the app reaches the store by its private endpoint, the store firewall can deny all public traffic, and the references resolve over the private path using the same identity and access grant as before. The identity and access requirements do not change when you add the private path; the network row is independent of the access row, which is why a reference can pass access and fail network or pass network and fail access, and why the checklist keeps them separate. An alternative is to permit the integrated subnet on the store's network rules using a service endpoint, which keeps the store's public endpoint but restricts it to your subnet. Both approaches give the app an accepted route; the private endpoint approach is the stronger posture because it removes public exposure rather than narrowing it.

There are two non-obvious settings in this design. The first is that the app must actually route its outbound traffic for the store through the VNet integration, which depends on the app's outbound routing configuration; if the app sends the store traffic out its default internet path instead of through the integrated subnet, the store firewall sees public traffic and denies it. The second is that name resolution must point the store hostname at the private endpoint when you use one, which means the app's DNS must resolve the store's name to its private IP, typically through a private DNS zone linked to the VNet. A reference that fails only after you enable the private endpoint, with everything else unchanged, is almost always one of these two: the routing sending traffic the wrong way, or the DNS resolving the store name to its public address so the connection never reaches the private endpoint. The networking specifics of private endpoints and their DNS are their own topic, but for references the rule is simple: the app needs an accepted route to the store and correct name resolution to reach it, and the access grant alone is not enough once the firewall is on.

## How do I make Key Vault references repeatable as code?

Doing the setup once by hand teaches you the pieces, but the configuration only stays correct if it is expressed as code that recreates it identically in every environment. The whole point of references is to remove secrets from configuration, and that benefit collapses if the identity, the role, and the reference are wired by hand in one environment and forgotten in the next. Expressing the three together in an infrastructure template makes them inseparable, so an environment cannot exist with the reference set but the access missing.

In Bicep the pattern is to declare the app with a system-assigned identity, assign the Key Vault Secrets User role to that identity at the store scope, and set the app setting to the reference, all in one template so the dependencies are explicit. A representative shape, with the connection string secret already in the store, looks like this:

```bicep
param appName string
param vaultName string
param secretName string = 'Sql-ConnectionString'

resource vault 'Microsoft.KeyVault/vaults@2023-02-01' existing = {
  name: vaultName
}

resource site 'Microsoft.Web/sites@2023-01-01' = {
  name: appName
  location: resourceGroup().location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    siteConfig: {
      appSettings: [
        {
          name: 'SqlConnectionString'
          value: '@Microsoft.KeyVault(VaultName=${vaultName};SecretName=${secretName})'
        }
      ]
    }
  }
}

resource secretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, site.id, 'Key Vault Secrets User')
  scope: vault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: site.identity.principalId
    principalType: 'ServicePrincipal'
  }
}
```

The role definition GUID in that template is the well-known identifier for Key Vault Secrets User; treat the exact GUID as a value to verify against the current role definition list, because while built-in role IDs are stable they are the kind of literal worth confirming rather than trusting from memory. The structure is the lesson regardless of the GUID: the role assignment depends on the site's identity, which exists only because the site declares a system-assigned identity, and the app setting carries the reference, so deploying the template produces an app that has an identity, has the read role, and has the reference, with no way to get one without the others. That coupling is what keeps environments consistent, because you cannot deploy the reference without also deploying the access.

For a user-assigned identity the template adds the identity resource, attaches it to the app, sets the `keyVaultReferenceIdentity` property to the identity's resource ID, and assigns the role to the user-assigned identity's principal rather than the site's. The extra moving part is the `keyVaultReferenceIdentity` property, which is the same property you would set by hand and the same one whose absence breaks user-assigned reference resolution, so encoding it in the template removes the most common user-assigned mistake. The ARM template equivalent expresses the same three resources with the same dependencies in JSON, and the deeper treatment of writing these templates well, including how to structure role assignments and identities across a real deployment, belongs to the infrastructure-as-code articles in this series. The takeaway for references specifically is that the identity, the role, and the reference are one unit of configuration, and templating them as one unit is what makes the setup durable rather than a thing that works until someone builds the next environment.

When you want a place to actually run these commands and templates against a live store and watch a reference resolve and fail under controlled conditions, [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), where you can wire a reference end to end, confirm it resolves through the app identity, then revoke the access and watch the status flip, which is the fastest way to build the diagnostic instinct this article describes.

## When does resolution happen, and what breaks at startup?

The timing of resolution explains a category of failures that look like the app itself is broken rather than the secret wiring. App Service and Functions resolve the values at app start and re-resolve them on a restart or a configuration change, then serve the cached resolved values to the running process. Your code reads ordinary environment variables, so by the time the application logic runs the substitution has already happened, and the value is either the secret or, on failure, the literal pointer string. The consequence is that a resolution failure does not throw an exception your code can catch at the moment of reading; it manifests as a wrong value, usually the raw pointer text, which then fails downstream when the application tries to use it as a connection string or an API key.

This produces a specific and confusing symptom: an app that starts but behaves as though its configuration is garbage. A database client receives the literal `@Microsoft.KeyVault(...)` text where it expected a connection string and fails to parse it, throwing a connection-string format error rather than an authentication error. An HTTP client sends the pointer text as an API key and gets a 401 from the downstream service. In both cases the surface error points at the consumer, not at the store, and a team can spend real time debugging the database client or the downstream API before realizing the value was never the secret. The tell is to look at the actual value the consumer received: if it is the pointer string, resolution failed and the problem is upstream in the setup, not in the client.

There is a sharper edge case for settings the platform itself needs at startup. Certain platform-level settings are consumed by the hosting runtime before your application code runs, and some of those cannot use a store pointer because the platform needs them too early in the startup sequence to perform the resolution, or because the resolution itself depends on infrastructure that is not yet available at that point. Functions apps in particular have storage-related settings that the runtime reads to bootstrap itself, and using a pointer for a setting the runtime needs before resolution can occur leads to a startup failure rather than a clean resolution error. The safe rule is to use pointers for application configuration that your code reads, and to treat platform bootstrap settings as a separate question to verify against the current documentation, because which settings can and cannot be a store pointer is a platform behavior that has changed and should be confirmed rather than assumed.

Because resolution is cached and refreshed rather than live on every read, a value that resolved correctly at startup remains correct for the running process even if the store becomes temporarily unreachable afterward, since the process is serving the cached value rather than re-fetching on each read. This is generally helpful for resilience, because a brief store blip does not take down a running app that already resolved its values. It also means a fix you make in the store or in the access grant may not take effect until the next refresh or restart, which is why forcing a restart is the reliable way to make a setup change visible immediately rather than waiting for the background refresh.

## Organizing references across many secrets and multiple stores

A real app rarely has one secret, and the way you organize the pointers across secrets and stores affects both clarity and the blast radius of an access grant. The simplest organization keeps all of an app's secrets in one store and grants the app's identity read access at the store scope, so one role assignment covers every pointer the app uses. This is clean and operationally light, and it is the right default when the secrets in the store all belong to the same trust boundary as the app. The cost is that store-scope access lets the identity read every secret in the vault, so if the vault holds secrets that belong to other apps, vault-scope access over-grants.

When a vault is shared across apps, per-secret scope tightens the grant so each app's identity can read only the secrets it should. This costs more role assignments, one per secret per identity, but it makes the access grant express the real need and prevents one app from reading another's secrets through a shared vault. The pointers do not change between vault-scope and secret-scope access; only the role assignment scope changes, so you can tighten an existing setup from vault scope to secret scope without touching any app setting. Choose per-secret scope when the vault is a shared resource and vault scope when the vault is dedicated to one app or one trust boundary.

Referencing secrets across multiple vaults is fully supported, since each pointer names its own vault, and an app can hold pointers to several vaults at once. The requirement is that the app's identity has read access in every vault it references, because each vault enforces its own access independently. This is the right structure when secrets have genuinely different ownership or lifecycle, such as a platform vault owned by a central team and an application vault owned by the app team, and the app legitimately needs values from both. The thing to watch is that a multi-vault setup multiplies the access grants and the network paths you must keep correct, so a pointer to a second vault that nobody granted access to fails exactly like any other access failure, isolated to the settings that name that vault. When several settings that share one vault all fail together while settings naming a different vault resolve, the shared-vault grouping of the failure points straight at that vault's access or network, which is the multi-vault version of reading the failure pattern.

Naming discipline helps more than it seems. Giving secrets names that map predictably to the settings that consume them, and keeping the setting name and the secret name related, makes a configuration view readable and makes a missing grant obvious. A configuration where the setting `SqlConnectionString` points at a secret named `Sql-ConnectionString` is self-documenting; a configuration where it points at a secret named `secret3` is a future debugging tax. The pointer mechanism does not require any particular naming, so the discipline is yours to impose, and imposing it pays back every time someone has to reason about which value comes from where.

## Secrets with special characters, multiline values, and certificates

Most secrets are simple strings, but the values teams store in vaults sometimes carry characteristics that interact with the pointer in ways worth knowing. A secret value with special characters, including semicolons, equals signs, or quotation marks, is stored and returned by the vault verbatim, and the pointer substitution places that exact value into the environment variable. The pointer syntax itself uses semicolons to separate fields in the named form, but that separation is parsed inside the parentheses of the pointer string, not in the secret value, so a connection string full of semicolons stored as a secret value is returned intact because the semicolons live in the value, not in the pointer fields. The place to be careful is when you build the pointer string in a shell or a template, where the surrounding tooling might interpret characters in the pointer text; quoting the whole setting value when you set it, as the CLI examples here do, prevents the shell from mangling the pointer before it reaches the platform.

Multiline secret values, such as a private key or a PEM-encoded block stored as a secret, are returned by the vault as the full multiline string and substituted into the environment variable as that full value. The pointer does not truncate or transform the value; it fetches what the vault holds. The practical caution is that some consumers expect a single-line environment variable, so storing a multiline value works for the pointer but may surprise the consumer, and the fix there is on the consumer or the encoding rather than on the pointer. Encoding a multiline value as base64 in the vault and decoding it in the app is a common way to sidestep multiline environment-variable awkwardness, and the pointer carries the base64 string transparently.

Certificates stored in Key Vault are a related but distinct case. A certificate in Key Vault is backed by a secret that holds the certificate material, and the pointer mechanism reads secret values, so referencing the secret behind a certificate is possible but is not the typical way apps consume certificates. App Service has its own mechanism for importing certificates from a vault for TLS and for making them available to the app, which is a better fit than a raw pointer when the app needs the certificate as a certificate rather than as a string. Use pointers for the secrets your code reads as configuration values, and use the platform's certificate import path for certificates the platform or the app consumes as certificates, because the two mechanisms exist for different consumption models and mixing them produces a value in the wrong shape.

## Auditing which references resolved and monitoring them over time

A setup that resolves today can break tomorrow when someone changes a role, rotates to a new secret name, or hardens the vault network, so treating resolution as something to monitor rather than something to set and forget is what keeps a production app from silently degrading. The platform's per-setting reference status is the first-line monitor: it reflects the current resolution state, so a setting that flips from resolved to failed shows it there. For a small app, glancing at that status after any change to the vault or the identity catches regressions early.

For ongoing monitoring at scale, the vault's own access logging is the authoritative record of whether the read happened and whether it was authorized. Key Vault can log data-plane operations, including the secret reads that pointer resolution performs, and those logs show the identity that read, the secret it read, and whether the read succeeded or was denied. Sending those logs to a workspace and watching for denied reads from your app identities turns a silent resolution failure into an alertable event, because a denied read in the vault log is the upstream cause of a failed reference downstream. This is the difference between learning about a broken pointer from a customer-facing outage and learning about it from an alert the moment the access was revoked. The logging configuration itself is part of vault hardening and is covered in the security depth article, but the relevance to pointers is direct: the vault log is where you see the read attempt that the pointer makes, so it is the canonical place to confirm whether the read is happening and succeeding.

Correlating the two signals gives a complete picture. The reference status tells you the platform's view of resolution, and the vault access log tells you the vault's view of the read. When both agree that resolution succeeded, the value is live. When the status says failed and the vault log shows a denied read, you have the access problem confirmed from both ends, with the vault log naming the exact identity and secret so you know precisely which grant to fix. When the status says failed but the vault log shows no read attempt at all, the read never reached the vault, which points at the network path rather than the access grant, because an access denial requires the request to have arrived. That last distinction, a denied read versus no read, is one of the most useful diagnostics available, and it comes for free once the vault is logging, because it separates the access row of the checklist from the network row without any further investigation.

## Should I read secrets through a reference or through code?

A pointer in an app setting is not the only way to get a vault secret into an app, and choosing it deliberately rather than by default helps you know when a different approach fits better. The main alternative is to read the secret in your application code using a vault client library and the same managed identity, fetching the value at the moment your code needs it. Both approaches use the app's identity and the same data-plane access grant, so the access setup is identical; the difference is where the fetch happens and how the value is delivered to your code.

The pointer approach delivers the secret as an ordinary environment variable, which means your application code is completely unaware of Key Vault and reads configuration exactly as it would for any plain setting. This is the strength of the approach: no library dependency, no vault-specific code, and a clean separation where the deployment owns the secret sourcing and the code owns the logic. It fits the common case where a value is read once at startup and used throughout, such as a connection string or an API key, and it keeps the application portable because the same code runs against a plain setting in one environment and a pointer-backed setting in another. The limitation is that the value is resolved on the platform's schedule, not on demand, so a freshly rotated value is not visible until the next refresh or restart, and the substitution happens for the whole process rather than per request.

Reading in code with the vault client gives you control over when the fetch happens and lets you re-fetch on demand, which matters when you need a rotated value immediately without a restart, or when you want to fetch a secret only in the rare code path that uses it rather than at every startup. The cost is a library dependency, vault-aware code, and the responsibility for caching and error handling that the platform otherwise provides for free. It fits cases where the timing of the fetch is part of the requirement, such as short-lived secrets you want to fetch fresh, or where the secret is needed conditionally rather than always.

The decision rule is therefore about timing and coupling rather than about access, since access is the same either way. Use a pointer when the value is read at startup and used as plain configuration, which is the majority of cases and the lowest-friction path. Read in code when you need on-demand freshness, conditional fetching, or per-request secret selection that the platform's startup-time substitution cannot provide. A third option, layering App Configuration in front of Key Vault, exists for teams that already centralize configuration there and want vault-backed values flowing through the same channel, and it carries its own pointer mechanism that resolves to the vault; that is a configuration-platform decision beyond the scope of wiring a direct pointer, and the direct pointer remains the simplest path for an app that just needs its own secrets at startup.

## Choosing system-assigned or user-assigned identity for references

The identity-type choice deserves a focused treatment because it changes the reference setup in concrete ways beyond the general identity decision. With a system-assigned identity the setup is minimal: the identity is created with the app, it is the default identity for resolution so you set nothing extra, and you grant that identity access. The trade-off is that the identity is tied to the app's lifecycle, so it is recreated if the app is recreated, and it is unique per app and per slot, which means a fleet of apps that should share access each needs its own grant. For a single app reading its own secrets, this is the path of least resistance and the one to choose unless a specific need pushes you to the alternative.

With a user-assigned identity the setup adds two things: you create and attach the identity, and you set the `keyVaultReferenceIdentity` property so the platform uses it for resolution rather than defaulting to the system-assigned identity. The payoff is a stable identity that outlives any single app, can be shared across many apps and slots with a single grant, and survives app recreation. This is the right choice for a fleet of apps that should all read the same secrets, because you grant the user-assigned identity access once and attach it everywhere, rather than granting each app's system-assigned identity separately. It is also the cleaner choice when you want the access grant to name a long-lived identity in audits rather than an identity that comes and goes with an app.

The decision rule names the deciding factor as sharing and lifecycle. If one app reads its own secrets and you want the simplest setup, use the system-assigned identity and skip the reference-identity property entirely. If multiple apps or slots should share the same access, or you want an identity that outlives the app, use a user-assigned identity, attach it everywhere it is needed, set the reference-identity property on each app, and grant access once. The single most common failure on the user-assigned path is forgetting the reference-identity property, which silently sends resolution back to the system-assigned identity, so if you adopt user-assigned identities, make the property part of the same change that creates the attachment so the two cannot drift. The broader reasoning behind the identity types, including the security and operational trade-offs that apply beyond references, is in [Set Up Managed Identities the Right Way](/2023/04/17/configure-managed-identities/), which is the canonical treatment for the choice.

## Closing verdict

A Key Vault reference is a small string with a large dependency behind it, and the whole craft of configuring it correctly is respecting that dependency. The string is the visible part and the part the portal will validate, which is exactly why it draws attention it does not deserve when something fails. The invisible part, the app's managed identity authenticating to the vault and being authorized to read the secret, is what actually makes the substitution happen, and it is where setups break far more often than the syntax. The identity-resolves-the-reference rule compresses this into one debugging instinct: when resolution fails, check the identity and its access before you check the string, because the string is almost never the problem and the access almost always is.

Configure it in dependency order: vault and secret, then identity, then the data-plane read grant, then the pointer, then network hardening, verifying resolution at each stage so you always know which step broke it. Leave references unpinned when you want rotation to flow, and pin only when you have a deliberate reason to freeze a version. Set the reference-identity property whenever you use a user-assigned identity, because its absence is the quiet killer of the user-assigned path. Express the identity, the role, and the pointer together as code so an environment cannot have one without the others. And use the two signals the platform and the vault give you, the per-setting resolution status and the vault access log, to verify the setup at configuration time and to monitor it afterward, so a broken pointer becomes an alert rather than an outage. Do those things and references deliver exactly what they promise: secrets that live in one audited vault, an app that reads plain environment variables, and rotations that require no redeploy.

## Frequently Asked Questions

### Q: Why is my app reading the literal @Microsoft.KeyVault string instead of the secret value?

When resolution fails, the platform passes the raw pointer text through to your app as the setting value, so seeing the literal `@Microsoft.KeyVault(...)` text where you expected a secret is the unambiguous sign that the lookup did not succeed. The value was never substituted, and your app received the pointer instead. The cause is one of the checklist rows: no managed identity on the app, an identity without the data-plane read grant, a user-assigned identity that was not selected with the reference-identity property, a malformed string, or a blocked network path to the vault. Start with the reference status the platform exposes for the setting, then confirm the identity has the Key Vault Secrets User role or the Get secret permission, since the missing grant is the most frequent cause. If the access denial persists even after a grant, the deeper diagnosis is in the dedicated access-denied troubleshooting article, which covers the cases where the grant looks present but is not effective.

### Q: Can I use a Key Vault reference for a connection string as well as an app setting?

Yes. The substitution works for both app settings and connection strings, and the same identity and access rules apply to each. You place the pointer string as the connection string value exactly as you would for an app setting, and at runtime the platform fetches the secret and delivers the resolved value to your app through the connection string channel. The only practical difference is where the value surfaces to your code, following the normal distinction your app already observes between app settings and connection strings. Choose whichever channel your application reads the value from today, and move the value into the vault behind a pointer in that same channel so your code does not change. The access grant, the identity selection, and the pinning behavior are identical regardless of which channel holds the pointer, so everything you know about wiring an app setting applies unchanged to a connection string.

### Q: Do Key Vault references work the same way in Azure Functions as in App Service?

The core mechanism is the same, because Functions runs on the same hosting platform and uses the same managed identity and the same pointer syntax to resolve secrets at runtime. You enable the identity, grant it the data-plane read on the vault, and set the app setting to the pointer, using the `az functionapp` commands in place of the `az webapp` ones. The one area to treat with extra care is platform bootstrap settings that the Functions runtime reads very early in startup, before application code runs. Some of those settings are needed before resolution can occur, so using a pointer for them can cause a startup failure rather than a clean resolution. Application configuration that your function code reads works fine behind a pointer; settings the runtime itself needs to bootstrap are the exception to verify against the current documentation. For ordinary secrets your code consumes, treat Functions and App Service as equivalent.

### Q: How do I use a user-assigned managed identity for Key Vault references?

Three things must all be true. First, the user-assigned identity must be attached to the app. Second, that identity must have the data-plane read grant on the vault, the Key Vault Secrets User role or the Get secret permission. Third, and this is the step teams miss, the app's `keyVaultReferenceIdentity` property must be set to the resource ID of the user-assigned identity. Without that property, the platform defaults to the system-assigned identity for resolution and ignores your user-assigned one entirely, so the lookup fails even though the identity exists and has access. Set the property with `az webapp update --set keyVaultReferenceIdentity=<resource-id>` using the full identity resource ID that starts with `/subscriptions/`. Make this property part of the same change that attaches the identity and grants the role, so the three never drift apart, because a user-assigned setup that is correct in every way except this property is the single most common user-assigned failure.

### Q: Why does my Key Vault reference work in production but fail on a deployment slot?

Because each slot can carry its own system-assigned managed identity, and granting access to the production slot's identity grants the staging slot's identity nothing. The pointer string is identical in both, which is why teams assume the slots are equivalent, but the identity doing the reading differs between them. The production slot's principal has the role; the staging slot's principal does not, so its lookups are denied. The fix is to grant each slot's identity its own data-plane read on the vault, or to use a single user-assigned identity shared across the slots with the reference-identity property set on each, so one grant covers them all. This is the slot-level expression of the identity-resolves-the-reference rule: a pointer resolves according to whichever identity authenticates in that slot, and different slots can be different principals, so a reference that works in one slot and fails in another is almost always a missing grant on the second slot's identity.

### Q: Do I need to restart my app after changing a Key Vault reference?

Changing the app setting that holds the pointer triggers a re-resolution on its own, so setting or correcting a pointer does not generally require a manual restart for that change to take effect. Where a restart helps is when you change something outside the app setting, such as granting a role, fixing the network path, or rotating a secret that an unpinned pointer should pick up. Those changes are visible after the platform's next background refresh, which is periodic, or immediately if you force a re-resolution by restarting the app or touching a setting. So if you grant access and the reference does not flip to resolved within the refresh window, restart the app to force the lookup to retry right away rather than waiting. The reliable rule is that an app setting change re-resolves itself, while a vault-side or access-side change becomes visible on the next refresh or on a restart, and a restart is the fast path when you want a fix to take effect immediately.

### Q: Can one app reference secrets from more than one Key Vault?

Yes. Each pointer names its own vault, so a single app can hold pointers to several vaults at once, with different settings reading from different vaults. The requirement is that the app's identity has the data-plane read grant in every vault it points at, because each vault enforces its access independently, and a grant in one vault does nothing for another. This is the right structure when secrets have genuinely different ownership or lifecycle, such as a central platform vault and an application-team vault that the app legitimately needs values from. The thing to watch is that a multi-vault setup multiplies the grants and the network paths you must keep correct. A pointer to a second vault that nobody granted access to fails exactly like any other access failure, isolated to the settings naming that vault, so when several settings sharing one vault all fail together while settings for another vault resolve, the shared-vault grouping points straight at that vault's access or network.

### Q: What is the keyVaultReferenceIdentity property and when do I set it?

It is the app property that tells the platform which managed identity to use when resolving Key Vault references. By default the platform uses the system-assigned identity, so for a system-assigned setup you set nothing and the property can stay at its default. You set it only when you want references to resolve through a user-assigned identity instead, in which case you set the property to that identity's full resource ID. The reason it exists is that an app can have multiple identities attached, and the platform needs to know which one to authenticate as for reference resolution; without the property it falls back to the system-assigned identity. The practical importance is outsized relative to its obscurity, because a user-assigned identity that is attached and granted access but not selected through this property is silently ignored, and resolution fails as though the identity had no access at all. If you use user-assigned identities for references, this property is mandatory, not optional.

### Q: Should I scope the read role to the whole vault or to a single secret?

It depends on whether the vault is dedicated to the app or shared, and the deciding factor is least privilege against operational overhead. Scope the Key Vault Secrets User role at the vault when the vault holds only this app's secrets or secrets within the same trust boundary, because one assignment then covers every pointer the app uses and the operational cost is minimal. Scope it at the individual secret when the vault is shared across apps and one app should not be able to read another app's secrets, because per-secret scope makes the grant express exactly what the app needs and prevents lateral reads through a shared vault. The pointer strings do not change between the two scopes; only the role assignment scope differs, so you can tighten an existing vault-scope setup to per-secret scope later without editing any app setting. Prefer per-secret scope in shared vaults and vault scope in dedicated vaults, matching the grant to the real need.

### Q: How do I assign the read role and the reference together in one Bicep deployment?

Declare the app with a system-assigned identity, set the app setting to the pointer string, and add a role assignment resource that grants Key Vault Secrets User to the app's identity at the vault scope, all in the same template. The role assignment references the app's `identity.principalId`, which exists only because the app declares an identity, and the app setting carries the pointer, so deploying the template produces an app that has an identity, has the role, and has the pointer, with no way to get one without the others. That coupling is the point, because it makes it impossible to provision an environment where the reference is set but the access is missing, which is the most common cross-environment failure. Use the well-known role definition ID for Key Vault Secrets User, and treat that GUID as a value to confirm against the current built-in role list. For a user-assigned identity, add the identity resource, attach it, set the reference-identity property, and assign the role to the user-assigned identity's principal.

### Q: Does using Key Vault references change my application code?

No, and that is the main reason to use them. The pointer is resolved by the platform before your code runs, so your application reads the value as an ordinary environment variable or connection string exactly as it would for any plain setting. There is no vault client library to add, no vault-specific code to write, and no awareness in the application that a vault is involved at all. This keeps the application portable: the same code runs against a plain setting in one environment and a pointer-backed setting in another, because the difference lives entirely in the deployment configuration rather than in the code. The separation is clean, with the deployment owning where the secret comes from and the code owning what to do with it. If you instead read the secret in code with a vault client, that does require a library and vault-aware code, which is a deliberate choice for cases that need on-demand freshness; for the common startup-time read, the pointer keeps your code untouched.

### Q: Why did all my references break right after I enabled the Key Vault firewall?

Because enabling the firewall removed the open network path the lookups were using, and the app no longer has an accepted route to the vault. The tell is the timing and the breadth: every reference failed at once, at the moment of the firewall change, with no change to the identities or the strings. That pattern is a network problem, not an access problem, even though the error category can look similar from the outside. An App Service app does not have a fixed, easily allowlisted set of outbound addresses by default, so simply turning on the firewall cuts it off. The fix is to give the app an accepted route, typically VNet integration combined with a private endpoint on the vault, plus correct name resolution so the vault hostname resolves to the private endpoint. Confirm the app routes its vault traffic through the integrated subnet rather than out its default internet path, because misrouted traffic reaches the vault as public traffic and is denied.

### Q: If I copied the secret URI from the portal, why does my app not get the new value after rotation?

Because the portal's secret picker includes the specific version in the URI it generates, which pins the pointer to that version. A pinned pointer keeps returning the version it names even after you rotate the secret and a new current version appears, so rotation looks broken when it is actually working and the pointer is simply frozen. The fix is to remove the trailing version segment so the URI ends at the secret name, which makes the pointer track the current version and pick up rotated values on the next refresh or restart. This is a configuration choice that masquerades as a bug, and it is extremely common precisely because the picker pins by default and nobody tells you to delete the version. Whenever you take a URI from the picker and you want rotation to flow, delete the version segment; keep it only when you have a deliberate reason to freeze a specific version, such as validating a new value before switching to it.

### Q: How do I store a multi-line secret like a private key behind a reference?

The vault stores and returns the value verbatim, including newlines, so a multi-line secret such as a PEM-encoded key is fetched in full and substituted into the environment variable as the complete multi-line string. The pointer does not truncate or transform it. The caution is on the consuming side, because some libraries and runtimes expect a single-line environment variable and behave oddly with embedded newlines. The common workaround is to base64-encode the multi-line value before storing it in the vault, store the single-line encoded string as the secret, and decode it in the app at the point of use. The pointer carries the base64 string transparently, and the app decodes it back to the original multi-line value, which sidesteps any newline awkwardness in environment-variable handling. So the pointer mechanism itself imposes no limit on multi-line values; the practical pattern is to encode for transport and decode in code when the consumer is sensitive to newlines.

### Q: How can I tell which managed identity a Key Vault reference uses to authenticate?

Check the app's `keyVaultReferenceIdentity` property. If it is unset or set to the system-assigned value, references resolve using the app's system-assigned identity. If it holds the resource ID of a user-assigned identity, references resolve using that identity. You can read it with `az webapp show --query keyVaultReferenceIdentity`. To confirm the identity actually has access, the authoritative source is the vault's data-plane access log, which records each secret read with the identity that performed it and whether it was authorized, so a denied entry there names the exact identity that failed and tells you which grant to fix. Pairing the property with the vault log gives a complete answer: the property tells you which identity the platform intends to use, and the log tells you whether that identity's read actually succeeded. A frequent surprise is finding the property unset when the team believed a user-assigned identity was in use, which explains a failure where the user-assigned identity has access but the system-assigned one, which the platform is actually using, does not.

### Q: Will scaling out to many instances cause Key Vault throttling on referenced secrets?

Key Vault enforces request limits on data-plane operations, and reference resolution performs reads against those limits, so a very large number of instances all resolving references can in principle contribute to throttling, especially during simultaneous startups or restarts when many instances resolve at once. In practice the platform caches resolved values per instance and refreshes them periodically rather than reading on every request, which keeps steady-state read volume low, so throttling from references is uncommon for ordinary workloads. The scenarios to watch are large scale-out events and coordinated restarts, where many instances resolve in a narrow window. Treat the exact request limits and the refresh cadence as values to verify against the current official documentation, since both are platform behaviors Microsoft tunes over time. If you operate at a scale where this is a concern, spreading restarts, keeping the number of distinct secrets reasonable, and monitoring the vault's throttling metrics are the levers, and the vault's own metrics will tell you whether resolution reads are approaching the limit.

### Q: Can I use a Key Vault reference in a slot setting that should not swap with the slot?

Yes. The pointer is just the value of an app setting or connection string, so it follows the same slot-stickiness rules as any other setting. If you mark the setting as a deployment-slot setting, it stays with the slot and does not swap, and its pointer resolves using that slot's identity. If you leave it as a normal setting, it swaps with the slot like any other value. The interaction to keep in mind is the identity: a sticky setting that stays on a slot still resolves through whatever identity authenticates in that slot, so a slot-specific pointer needs the slot's identity to have access. This is most relevant when production and staging point at different vaults or different secrets, where you want the pointer to be slot-specific so a swap does not move production onto the staging value. Mark such settings as slot settings, grant each slot's identity access to its own vault or secret, and the pointers stay correctly paired to their slots through swaps.

### Q: How do I migrate an existing plaintext app setting to a Key Vault reference safely?

Do it in the dependency order with a verification between each step, so the app never loses the value. First, create the secret in the vault holding the current plaintext value, so the source exists. Second, ensure the app's identity has the data-plane read grant on the vault, so the lookup will be authorized. Third, change the app setting from the plaintext value to the pointer string, which triggers a re-resolution. Fourth, verify the reference status shows resolved and that the app reads the secret value rather than the literal pointer text, ideally in a non-production environment first. Only after resolution is confirmed should you consider the plaintext value retired, and you should then remove the plaintext from any source control or pipeline where it lingered, since the point of the migration is to get the secret out of those places. If resolution fails at the verification step, the plaintext is still recoverable because you have it in the vault, and you walk the checklist to find the missing grant or the malformed string before retrying.
