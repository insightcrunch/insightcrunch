---
layout: post
title: "Fix WEBSITE_RUN_FROM_PACKAGE Errors"
page_title: "Fix WEBSITE_RUN_FROM_PACKAGE Errors on Azure App Service: Read-Only File System, Package URL, SAS, and Mount Failures Explained"
date: 2023-02-27
categories: ["Technology"]
tags: ["Azure", "App Service", "WEBSITE_RUN_FROM_PACKAGE", "Troubleshooting", "DevOps", "Cloud Computing"]
excerpt: "WEBSITE_RUN_FROM_PACKAGE mounts your App Service app read-only, so a runtime write failure is a design mismatch and not a deploy bug. Here is the fix."
image: "/assets/images/blog/blog-52.webp"
reading_time: 60
author: "ryan-walsh"
last_updated: 2023-02-27
lang: en
---
You ship a deployment to Azure App Service, the pipeline reports success, and then the app falls over with a line you have seen before and never quite trusted: the file system is read-only. Sometimes the message is blunter, a flat refusal when the runtime tries to write a log or a cache file beside its own binaries. Sometimes the symptom is quieter and stranger, a deployment that finished cleanly yet serves the old code, or a remote bundle that simply never appears. In nearly every one of these cases the cause traces back to a single application setting that changed how your code is mounted, and that setting is WEBSITE_RUN_FROM_PACKAGE. When this value is present, App Service stops treating your site directory as an ordinary writable folder and instead mounts your deployed zip as an immutable file system, which is exactly the behavior that breaks any code expecting to write next to its files.

The frustrating part is that almost none of this surfaces as a clear error pointing at the setting. The platform does what it was told, the deployment tooling does what it was told, and the gap sits inside an assumption your application code made about where it lives. Once you see the mechanism, the failures stop looking like a grab bag of unrelated bugs and resolve into a small, predictable family: a value-versus-URL mismatch, a locked file system that rejects runtime writes, a remote bundle that will not mount, or writes that have nowhere to land. This article walks each one to ground, shows the command that confirms it is yours, and gives the tested fix, so that you keep the genuine benefits of running from a package instead of reflexively tearing the setting out.

![Fixing WEBSITE_RUN_FROM_PACKAGE read-only file system errors on Azure App Service - Insight Crunch](/assets/images/blog/blog-52.webp)

## What WEBSITE_RUN_FROM_PACKAGE actually does to your app

The setting changes the deployment model from copy-then-serve to mount-and-run, and that single change explains every downstream failure. In the classic model, your deployment process writes files into the site content folder, the runtime reads them from there, and that folder remains an ordinary read-write directory backed by the shared storage that every instance of your plan sees. Your code can open a file beside its assemblies, write a cache, drop a log, generate a thumbnail next to a controller, and the platform never objects, because the location is a normal mutable folder.

WEBSITE_RUN_FROM_PACKAGE replaces that arrangement. Instead of expanding your files into the writable content folder, the platform takes the zip you produced and mounts it as the site directory in a read-only state. The runtime reads your assemblies and static assets straight out of that mounted bundle. Nothing extracts onto the writable share. The site folder, which your code may have treated for years as a place it can write, is now an immutable view onto a package, and the platform enforces that immutability at the file-system layer. Every instance in the plan mounts the same package, which is the property that makes the model attractive: the deploy is atomic, every worker runs byte-identical content, and a swap or a scale-out cannot land a half-copied file because there is no copy happening at all.

This is the part worth internalizing before you touch anything, because it reframes the whole problem. A great deal of confusion about App Service hosting evaporates once you hold the worker and storage model clearly in mind, which is the same mental model the broader [Azure App Service hosting and worker model deep dive](/2022/01/10/azure-app-service-deep-dive/) lays out in detail. The package is not your old site folder with a flag set on it. It is a different object entirely, a sealed archive that the platform presents as your application root, and the read-only behavior is not a fault to be suppressed but the defining feature you opted into.

### Why does my app run from a read-only file system?

Because the setting tells App Service to mount your deployed zip as the site directory instead of expanding it onto writable storage. The platform serves your code directly from that sealed archive, so the folder your application treats as its root becomes immutable by design, and any attempt to write inside it is refused at the file-system layer.

The benefit you are buying is consistency and atomicity. When a worker recycles, scales out, or comes up after a swap, it mounts the identical sealed bundle rather than syncing a directory that another process might be midway through changing. That removes a whole class of partial-deploy and locked-file problems that plague the copy model, especially the file-in-use errors that surface when a running process holds an assembly open while a deployment tries to overwrite it. The trade is that you give up the ability to mutate the site directory at runtime, and code that quietly depended on that ability has to change where it writes. The setting is a contract: in exchange for an immutable, identical, instantly swappable deployment, your application agrees not to treat its own home as scratch space.

## How to read the failure and gather the diagnostic signal

Before you assign a cause, confirm two facts: that the setting is actually in effect, and what value it holds. Those two facts split the entire problem space, and skipping them is how engineers spend an afternoon fixing the wrong thing. The application settings of the site are the first stop. From the command line you can read every setting without opening the portal:

```bash
az webapp config appsettings list \
  --name <app-name> \
  --resource-group <resource-group> \
  --query "[?name=='WEBSITE_RUN_FROM_PACKAGE']" \
  --output table
```

If that query returns nothing, the setting is not present and your read-only symptoms are coming from somewhere else. If it returns a row, read the value carefully. A value of `1` means the platform runs from the most recent zip you pushed to the site through the deployment endpoint, which the platform stores and mounts locally. A value that is a URL, typically pointing at a blob in a storage account and carrying a long query string, means the platform pulls and mounts that remote archive instead. Those two modes fail in different ways, so the value you read here decides which half of this article applies to you.

The second signal source is the deployment log and the application log. The site's diagnostic log stream shows the runtime's own complaints, and when an application tries to write into the mounted package, the exception text usually names the path it could not write to. Stream the logs live while you reproduce the failure:

```bash
az webapp log tail \
  --name <app-name> \
  --resource-group <resource-group>
```

Watch for the exact failing path in the stack trace. If the path sits under the site root, the application is trying to write into the sealed bundle, and you have the read-only-write cause. If the failure instead mentions an inability to download or open the package, or the site refuses to start with no application exception at all, you are looking at a mount problem rather than a write problem.

The third source is the deployment and source-control management site, often called the advanced tools or Kudu console, reachable at the `scm` host for your app. It exposes a file-system browser and a process explorer that let you see what is actually mounted. When you open the site content folder there and find it presenting a package rather than expanded files, or when an attempt to create a file in it fails, you are seeing the read-only mount with your own eyes. The Kudu environment page also lists the effective application settings the worker received, which is the authoritative answer to whether the setting took effect, because a setting can be defined on the app yet not yet applied if the app has not restarted since the change.

### How do I confirm a Run From Package failure rather than a deploy failure?

Read the setting value first, then the log stream. If WEBSITE_RUN_FROM_PACKAGE is present and the runtime exception names a write to a path under the site root, the failure is the read-only mount, not the deployment. A clean deploy that then throws a write error at runtime is the signature that distinguishes the two.

This distinction matters because the tooling reports a Run From Package deployment as successful the moment the package is in place, since from the platform's point of view nothing failed. The breakage happens later, when your code runs and reaches for a write that the model forbids. That timing is the tell. A genuine deployment failure stops before the app starts and shows up in the deployment log, a topic the [broader guide to App Service deployment failures](/2023/02/20/fix-app-service-deployment-failed/) treats across every cause from build errors to file locks. A Run From Package write error, by contrast, sails through deployment and only appears once a request exercises the offending code path. If your symptom arrives after the green checkmark rather than before it, you are in the territory this article owns.

## Reproducing the failure so you can trust the fix

A fix you cannot reproduce is a fix you do not understand, and the read-only behavior is simple enough to provoke deliberately, which is the fastest way to build confidence before you touch a production app. Stand up a throwaway app, enable the setting with a value of `1`, push a tiny zip, and then add one line of code that writes a file beside its own binaries. The first request that exercises that line throws the read-only exception, and you have the failure in front of you on demand. Provoking it once teaches you to recognize its signature instantly, and it gives you a place to validate that redirecting the write to the temp location actually resolves it.

The minimal reproduction has three parts. First, create the app and turn on the setting:

```bash
az webapp create \
  --name <repro-app> \
  --resource-group <resource-group> \
  --plan <plan> \
  --runtime "DOTNETCORE:8.0"

az webapp config appsettings set \
  --name <repro-app> \
  --resource-group <resource-group> \
  --settings WEBSITE_RUN_FROM_PACKAGE=1
```

Second, deploy a tiny app whose handler tries to write a file under its own base directory, the exact mistake that breaks under the model. Third, hit the endpoint and read the exception in the log stream. The stack trace names the path it could not write, the path sits under the site root, and that single line is the whole diagnosis condensed into evidence you generated yourself. Once you change the handler to resolve the temp location instead and redeploy, the same request succeeds, which proves both the cause and the cure in one cycle.

The remote variant is just as reproducible and just as instructive. Upload a valid archive to a blob, point the setting at its URL with a signature that expires in five minutes, and watch the app run. After the signature lapses, restart the app and observe that it now refuses to start with a fetch failure rather than an application exception, which is the exact signature of the expired-signature cause described later. Doing this once, in a sandbox, removes the mystery from the production incident where an app that ran for a month suddenly will not come up. A controlled space to run these provocations matters more than reading about them, and you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to stand up the repro app, trigger each failure, and confirm the redirect, so the first time you meet the failure in production it is already familiar.

### How do I prove a fix worked rather than hoping it did?

Reproduce the failure, apply the change, and reproduce again. For a read-only write error, force the failing request, redirect the write to the temp location, redeploy, and confirm the same request now succeeds in the log stream. For a remote package, restart the app after updating the URL and watch the worker fetch and mount the new archive cleanly rather than assuming it did.

## The four root causes behind a Run From Package failure

Almost every Run From Package problem reduces to one of four causes, and naming them is the fastest route to a fix. The first is a runtime write into the read-only mount, where the application tries to create or modify a file under the site root. The second is a bad or expired shared access signature in a package URL, where the platform cannot authenticate to the storage holding the remote archive. The third is a mount failure for other reasons, a network block to the storage account or a malformed archive that the platform cannot open. The fourth is confusion between the two modes, where an engineer sets a value of `1` when they meant to supply a URL or supplies a URL when they meant the local mode, and the app then runs the wrong content or no content at all.

That short taxonomy is the namable claim of this article, the read-only-package rule, and it is worth stating plainly so you can carry it into any future incident. Run From Package mounts the application read-only, so any failure where the app tries to write next to its files is a design mismatch and not a deployment bug, and the fix is to redirect the write rather than to disable the model. The corollary covers the remote case: when the package lives behind a URL, any failure to start is most often a failure to fetch or open that package, which means the fix lives in the URL, the signature, or the network path to storage, not in your application code at all.

The findable artifact below is the InsightCrunch Run From Package table. It pairs each failure with the cause that produces it and the fix or alternative path that resolves it, so you can match a symptom to a remedy at a glance and then read the section that explains why.

| Failure you observe | Underlying cause | Fix or alternative path |
| --- | --- | --- |
| Runtime exception writing a file under the site root, often a log, cache, or generated asset | The application writes next to its binaries on a now read-only mount | Redirect the write to the temp path or to mounted external storage; do not disable the model |
| App will not start, log shows it cannot download or open the package | Bad, expired, or malformed shared access signature in the package URL | Regenerate the signature with a longer validity and update the URL value; verify the blob is reachable |
| App will not start, no application exception, package never mounts | Network rule on the storage account blocks the platform from reaching the blob | Allow the platform to reach storage, or move to local package mode, or front the blob with an endpoint the app can reach |
| Deploy reports success but the new code does not appear | Wrong mode set, a value of 1 left while a stale local package is mounted, or a URL pointing at an old blob | Confirm the value, push a fresh package or update the URL to the new blob, then restart |
| Function app worked locally but fails on the platform with the setting | The function host or extension expects to write into the function app root | Point writes at the temp path and confirm the package contains the built output, not the source |
| Malformed or partial archive fails to open | The zip is truncated, wrongly structured, or built from the wrong folder | Rebuild the package from the publish output and validate it opens before pushing |

## Cause one: the app writes next to its binaries on a read-only mount

This is the most common Run From Package failure by a wide margin, and it is almost always a surprise, because the code worked for years in the copy model and worked again on a developer machine where the working directory is fully writable. The moment the setting takes hold, the site root becomes immutable, and the first runtime write into it throws. The classic offenders are a logging library configured to drop a file beside the executable, an image or document library that writes a temporary rendering into the application folder, a caching layer that persists to a file under the content root, a plugin system that unpacks into its own directory, and any code that builds a path relative to the assembly location and then opens it for writing.

### Why can my app not write files with Run From Package?

Because the site root is mounted read-only, so any file the application opens for writing under that root is refused by the platform. The model serves your code from a sealed archive that cannot be modified at runtime. Writes are not blocked everywhere, only inside the mounted package, and the fix is to send the write to a path that remains mutable.

To confirm that this is your cause, stream the logs while you exercise the path that fails and read the exception. The path it names is the evidence. If that path sits under the site root, your code is writing into the package. You can make this concrete in the Kudu console by attempting to create a file in the site content folder yourself and watching it fail with a read-only error, which proves the mount state independently of your application. You can also inspect the code path directly: search the project for any file open or create call that resolves to a location relative to the base directory of the running assembly, because those are the calls that will now hit the immutable mount.

The fix is to redirect the write, and the platform gives you a writable location for exactly this purpose. The temporary directory exposed through the standard temp path environment variable remains writable under Run From Package, and code that needs scratch space should target it. In .NET that means resolving the temp path through the framework rather than building a path off the application base directory:

```csharp
// Wrong under Run From Package: writes into the read-only mounted site root.
var bad = Path.Combine(AppContext.BaseDirectory, "cache", "rendered.png");

// Correct: write scratch output into the writable temp location.
var scratch = Path.Combine(Path.GetTempPath(), "cache");
Directory.CreateDirectory(scratch);
var good = Path.Combine(scratch, "rendered.png");
```

The same principle holds in any runtime. In Node the temp directory comes from the operating system temp accessor, in Python from the standard temporary file module, and in Java from the configured temp directory property. The rule is identical across all of them: never anchor a writable path to the location of your code, because under this model that location is sealed. For data that must survive a restart or be shared across instances, the temp path is the wrong target because it is local to a worker and ephemeral, and the correct destination is external durable storage, which the later section on writable paths covers in full.

A subtle variant of this cause is configuration that points logging or framework state at the content root by default. Many frameworks write their data-protection keys, their session state, or their compiled view cache into a folder under the application root unless told otherwise. Under the copy model that folder was writable and nobody noticed. Under Run From Package the framework's first attempt to persist a key or a compiled artifact fails, and the symptom can be a strange startup error rather than an obvious write exception. The fix is to point those framework facilities at a writable location through their own configuration knobs, the data-protection key ring at external storage, the temp-file location at the temp path, and the response-compilation or view cache at a directory the model permits.

## Cause two: a bad or expired SAS in the package URL

When you run from a remote package, WEBSITE_RUN_FROM_PACKAGE holds a URL rather than the value `1`, and that URL almost always carries a shared access signature, a long query string that grants the platform time-limited, scoped permission to read the blob. The platform uses that signature to download and mount the archive. If the signature is wrong, expired, scoped too narrowly, or attached to a URL that no longer resolves to the blob, the platform cannot fetch the package, and the app will not start. Because the failure is a fetch failure rather than an application exception, the logs show the platform unable to download or open the archive rather than a stack trace from your code.

### How do I point Run From Package at a storage URL?

Set WEBSITE_RUN_FROM_PACKAGE to the full blob URL of your zip, including a shared access signature that grants read access for long enough to cover the deployment lifetime. The platform downloads and mounts that remote archive on start. Use a generous expiry, scope the signature to read only, and restart the app so the new value takes effect.

The most frequent version of this cause is an expired signature. An engineer generates a signature valid for a short window, the deployment works that day, and weeks later a routine restart or a scale event forces the worker to refetch the package, by which time the signature has expired and the fetch fails. The app that ran happily for a month suddenly will not come up, and nothing in the application changed. To confirm, read the signature's expiry out of the URL value and compare it to now. If the expiry is in the past, you have found it. You can also test the URL independently by attempting to read the blob with it from a machine outside Azure, which tells you whether the signature still authorizes the read:

```bash
# Read the current value to inspect the expiry encoded in the SAS query string.
az webapp config appsettings list \
  --name <app-name> \
  --resource-group <resource-group> \
  --query "[?name=='WEBSITE_RUN_FROM_PACKAGE'].value" \
  --output tsv

# Attempt to fetch the blob with the existing URL to test the signature.
curl -sI "<the-url-value-including-sas>"
```

A response that denies access or reports the signature as expired confirms the cause. The fix is to mint a fresh signature with a longer validity, attach it to the correct blob URL, and update the application setting. Generate the signature scoped to read on the specific blob, with an expiry far enough out that routine restarts will not outlive it, and prefer a stored access policy on the container when you want to manage validity and revocation centrally rather than baking a fixed expiry into every URL:

```bash
# Generate a read-only SAS valid well into the future for the package blob.
END=$(date -u -d "2 years" '+%Y-%m-%dT%H:%MZ')
SAS=$(az storage blob generate-sas \
  --account-name <storage-account> \
  --container-name <container> \
  --name <package-blob>.zip \
  --permissions r \
  --expiry "$END" \
  --https-only \
  --output tsv)

URL="https://<storage-account>.blob.core.windows.net/<container>/<package-blob>.zip?${SAS}"

az webapp config appsettings set \
  --name <app-name> \
  --resource-group <resource-group> \
  --settings WEBSITE_RUN_FROM_PACKAGE="$URL"

az webapp restart --name <app-name> --resource-group <resource-group>
```

A cleaner alternative that removes the signature problem entirely is to grant the app's managed identity read access to the blob and let the platform authenticate as that identity rather than carrying a signature in the URL at all. When the app has a managed identity with the storage blob data reader role on the container, you can use the identity-based form of the setting, and there is no signature to expire. That approach trades a one-time identity and role assignment for the elimination of the most common cause of a dead remote package, and it is the configuration to reach for when an app keeps dying weeks after a deployment that everyone has forgotten about.

## Cause three: the remote package will not mount

Beyond an expired signature, a remote package can fail to mount for two structural reasons, and both present as an app that will not start with no application exception in the logs. The first is a network rule on the storage account that blocks the platform from reaching the blob. The second is a malformed or partial archive that the platform downloads but cannot open as a valid package. Distinguishing them is a matter of asking whether the platform could reach the storage at all.

### Why does the remote package fail to mount?

Because the platform either cannot reach the storage that holds the archive or cannot open the archive it fetched. A network rule that denies the platform's access to the storage account blocks the download, and a truncated or wrongly built zip blocks the open. The startup failure carries no application exception because your code never runs.

A storage network block is the more common of the two and the more confusing, because the storage account works fine from your laptop and from the deployment pipeline that uploaded the blob, yet the App Service worker cannot reach it. This happens when the storage account has public network access disabled or restricted to selected networks, and the worker's outbound path to storage is not on the allowed list. To confirm, check the storage account's network configuration and ask whether the platform's egress is permitted. If public access is restricted, the worker fetching the package by its public blob URL will be denied. The resolutions are to permit the platform to reach the storage, to route the worker's outbound traffic through a network that the storage account trusts, or to front the blob through an access path the app can reach. When the app is integrated with a virtual network and the storage is reachable privately, the package fetch can traverse that private path, but that only works when the integration and the private resolution are actually in place, not merely configured on paper.

The second structural cause, a malformed archive, is mechanical and easy to rule in or out. The package must be a valid zip that contains your built application at its root, not a zip of a folder that contains your application, and not the source tree before a build. A common mistake is to zip the project directory rather than the publish output, so the platform mounts a package whose root holds project files rather than runnable binaries, and the runtime finds nothing to execute. Another is a truncated upload, where the blob is shorter than the file that was meant to be uploaded because the transfer was interrupted. To confirm, download the blob and open it locally:

```bash
# Download the package the platform is trying to mount and inspect it.
az storage blob download \
  --account-name <storage-account> \
  --container-name <container> \
  --name <package-blob>.zip \
  --file ./fetched-package.zip \
  --auth-mode login

# Verify it is a valid archive and that the build output sits at the root.
unzip -l ./fetched-package.zip | head -40
```

If the listing fails because the archive is corrupt, or if the contents show a nested folder or raw source instead of the published output at the root, you have found the cause. The fix is to rebuild the package from the publish output, validate that it opens and that the entry point sits where the runtime expects it, and re-upload before updating the URL. Building the package the same way every time, from the same publish step, is the single change that prevents this cause from recurring.

## When the storage block is a virtual network rule

The network-block variant of a mount failure deserves a closer look, because it is the one engineers misdiagnose most often and the one that is hardest to see, since every other actor in the system can reach the storage and only the worker cannot. The setup that produces it is increasingly common: a hardened storage account with public access disabled or limited to selected networks, holding the deployment archive, fronted by a private endpoint, while the app pulls the archive by a public blob address that the storage account now refuses to answer. The deployment pipeline uploaded the blob over an allowed path, so the artifact is genuinely there, and a developer can read it from a trusted network, so the blob looks healthy. The worker, reaching for the same address from an egress path the storage account does not trust, is simply denied, and the app will not start with no clue in the application logs because the runtime never executed.

### Why can the pipeline reach the storage but the app worker cannot?

Because the pipeline and the worker take different network paths to the same blob, and the storage account trusts one path and not the other. A pipeline often uploads over an allowed agent network, while the App Service worker reaches out through its own egress, which a restricted storage account may not permit. The blob is present and valid; only the worker's route is blocked.

To confirm this cause you reason about reachability rather than about the archive. Check whether the storage account restricts network access, then ask whether the App Service worker's outbound path is on the trusted list. If the storage account allows only selected virtual networks and the app is not integrated with one of them, or is integrated but its outbound traffic to storage does not traverse the trusted subnet, the worker cannot reach the blob even though the address is correct and the signature is valid. The diagnostic is not in the package at all; it is in the network configuration of the storage account and the outbound integration of the app.

There are three ways out, and the right one depends on how much network isolation you actually need. The least invasive is to relax the storage account's network rules enough to admit the worker, which trades some isolation for a working mount and is acceptable when the archive is not sensitive. The strongest is to keep the storage locked down and make the worker's outbound traffic legitimate: integrate the app with the virtual network that the storage account trusts, ensure the app routes its outbound calls through that network, and resolve the storage account to its private endpoint so the worker reaches the blob over the private path. That makes the fetch traverse a route the storage account permits, and it is the configuration to reach for when the archive must stay behind a private boundary. The pattern only works when the integration and the private resolution are genuinely in place and not merely declared, which is why confirming the worker can resolve the storage host privately is the step that proves it.

```bash
# From the app, confirm how the storage host resolves. A public address from a
# worker that should be using the private path is the tell that the route is wrong.
az webapp ssh --name <app-name> --resource-group <resource-group>
# inside the SSH session:
#   nslookup <storage-account>.blob.core.windows.net
#   curl -sI "https://<storage-account>.blob.core.windows.net/<container>/<blob>.zip?<sas>"
```

A private address in the lookup, paired with a successful read, confirms the worker reaches the blob over the trusted path and the mount will succeed. A public address, or a denied read, tells you the integration or the private resolution is not actually carrying the package fetch, which is the precise thing to fix. The third route sidesteps the whole question by switching the local push model, value `1`, so the platform stores and mounts the archive itself and there is no remote fetch to block, which is the pragmatic choice when private networking to storage is more isolation than the deployment actually requires.

## How the local package is stored and how value 1 mounts it

The value `1` mode is worth understanding in detail, because the way it stores and mounts the archive explains several of its quirks, including the stale-content symptom and the behavior of a restart. When you push a zip to the deployment endpoint with the setting at `1`, the platform stores that archive in a managed location associated with the app and mounts it as the site directory. The push replaces the stored archive, and a restart causes the worker to mount whatever archive is currently stored. The mount is local to the worker in the sense that each worker mounts the stored archive independently, so a scale-out brings up new workers that mount the same stored bundle, which is why the model gives identical content across instances without any synchronization.

### Why does a restart sometimes serve old code in local package mode?

Because a restart mounts whatever archive is currently stored for the app, and if a release did not actually replace that stored archive, the worker faithfully remounts the previous one. The mount is correct; the stored artifact is stale. Confirm that your release pushed a fresh zip to the deployment endpoint and that the push succeeded, then restart so the worker remounts the new content.

This mounting behavior is the reason a deployment in local mode must do two things to take effect: replace the stored archive and cause the worker to remount it. A pipeline that pushes a new zip but does not trigger a restart can leave workers serving the previously mounted archive until something else recycles them, which presents as a deploy that succeeded but did not change the running app. The cure is to ensure each release both pushes the fresh archive and restarts the app, so the worker mounts the new stored bundle deterministically rather than whenever it happens to recycle. The same mechanism makes a rollback trivial in principle: push the previous archive and restart, and the worker mounts the older content, because the model has no concept of an in-place edit that a rollback would have to undo.

The local mode also interacts with the writable share in a way worth naming. Because the platform mounts the stored archive rather than expanding it onto the content share, the content share is no longer the source of truth for your code, and tools or scripts that inspect the share expecting to find your files there will be confused, since they find a mounted view rather than expanded content. Anything that previously edited files on the share to patch a running app, a practice that was always fragile, stops working entirely under the model, because the share is no longer where the running code lives. That is a feature, since it forces all changes to flow through a proper deployment, but it surprises teams that relied on editing files in place, and recognizing it prevents a fruitless attempt to fix the app by changing files that the worker is not even reading.

The two modes look similar in the application settings and behave completely differently, which is why mixing them is a recurring source of mysterious results. A value of `1` tells the platform to run from the package you most recently pushed to the site through its deployment endpoint, which the platform stores and mounts locally on the worker. A URL value tells the platform to ignore any locally pushed package and instead fetch and mount the archive at that address. Setting the wrong one for your deployment flow produces an app that runs stale content, runs nothing, or appears to ignore your deployments.

### What is the difference between value 1 and a package URL?

A value of 1 runs the app from the latest zip pushed to the site through its deployment endpoint, stored and mounted locally on the worker. A URL runs the app from the remote archive at that address. The first couples to your push-based deploy, the second to a blob you manage yourself, and supplying the wrong one means the app mounts the wrong source.

The signature failure here is a deployment that reports success while the running app does not change. If the value is `1` and your pipeline pushes a fresh zip to the deployment endpoint on each release, a new push should mount the new content after a restart, so an app stuck on old code points either to a push that did not actually replace the stored package or to a worker that has not remounted. If the value is a URL and your pipeline uploads a new blob but the URL still points at the old blob name or an old version, the platform keeps mounting the stale archive because nothing told it to look elsewhere. The two flows fail in opposite directions: with `1` the deployment endpoint owns the package, and with a URL your blob management owns it, and a release pipeline that updates one while the setting expects the other will quietly serve the wrong code.

To resolve, decide which model your delivery flow actually uses and make the setting match it. If your pipeline pushes a zip to the site's deployment endpoint, set the value to `1` and ensure each release pushes the new package and triggers a restart so the worker remounts. If your pipeline publishes a blob and you want the platform to fetch it, set the value to the blob URL and ensure each release either updates the URL to the new blob or overwrites the same blob the URL already names, then restarts. The cleanest pattern for the URL mode is a stable blob name that each release overwrites, paired with an identity-based or stored-policy signature so the address never has to change, which removes the class of failures where the deployment updates the artifact but the setting keeps pointing at the previous one:

```bash
# Confirm which mode is in effect before changing a deployment flow.
az webapp config appsettings list \
  --name <app-name> \
  --resource-group <resource-group> \
  --query "[?name=='WEBSITE_RUN_FROM_PACKAGE'].value" \
  --output tsv
```

A blank or `1` result means local push mode, and a URL means remote fetch mode. Make the pipeline and the setting agree, and the stale-content symptom disappears.

## Where your app can still write when the package is read-only

The read-only mount applies to the site root, not to the entire file system, and knowing precisely which locations remain writable is what lets you keep the model and still run code that needs to persist data. The temporary directory is writable. It is local to each worker, it does not survive a restart or a move to a different instance, and it is not shared across the instances in your plan, but for scratch space, intermediate rendering, transient caches, and any output that can be regenerated, it is the correct target. Resolve it through the standard temp accessor of your runtime rather than hardcoding a path, because the platform owns the actual location and it can differ between environments.

### Where can my app write when Run From Package locks the site root?

Your app can write to the temporary directory, which stays mutable but is local to each worker and cleared on restart, so it suits scratch and regenerable output only. For data that must persist or be shared across instances, write to external durable storage such as a storage account, a database, or a file share mounted into the app.

For anything that must persist beyond a single worker's lifetime or be visible to every instance, external storage is the answer, and App Service makes several forms of it available. A storage account holds blobs your app can read and write through the storage client and a managed identity, which is the right home for uploaded files, generated documents, and any artifact users expect to find again later. A database holds structured state that file storage handles poorly. A file share can be mounted into the app as a path, giving code that genuinely expects a writable directory a real one that is durable and shared, which is the bridge for legacy applications too entangled with the file system to refactor quickly. The decision among them follows the shape of the data: ephemeral and regenerable goes to temp, durable and unstructured goes to blob storage, durable and structured goes to a database, and code that cannot be changed to call a storage client gets a mounted share.

The mistake to avoid is reaching for a mounted share as a reflex to silence a read-only error, because a share carries its own latency and consistency characteristics and turning every local write into a network write can change an app's performance profile. The better instinct is to ask what each write is for. A write that produces a throwaway intermediate belongs in temp and should never have touched durable storage in the first place. A write that produces something a user will retrieve belongs in blob storage and was only ever in the file system because the original developer treated the local disk as permanent. Sorting the writes by purpose usually shrinks the problem to a handful of genuinely durable outputs, which are simple to move, plus a larger set of scratch writes that the temp path absorbs without any architectural change.

## Data-protection keys and state that must outlive a worker

A category of write deserves its own treatment because it fails in a way that looks unrelated to the file system at first: the internal state that frameworks persist to disk and assume will still be there later. The clearest example is the data-protection key ring that many web frameworks use to encrypt cookies, antiforgery tokens, and other protected payloads. By default the framework writes these keys to a folder under the application root, expecting to read them back on the next request and on every other instance. Under the copy model that folder was a writable share visible to every worker, so the keys persisted across restarts and instances and nobody thought about it. Under Run From Package the key folder sits inside the read-only mount, the framework cannot write the key, and the symptom is not an obvious file error but a cascade of decryption failures: users logged out after a restart, antiforgery validation failing across instances, and protected payloads from one worker rejected by another.

### Why do my users get logged out after every restart under the model?

Because the framework wrote its data-protection keys to a folder under the now read-only site root, so it cannot persist them and falls back to keys that do not survive a restart or carry across instances. Each worker generates its own ephemeral keys, so a payload one worker protected another cannot read. Persist the key ring to external storage to fix it.

The fix is to relocate the key ring to a durable, shared location that every instance can read and write, which is external storage rather than the local file system. Pointing the framework's data-protection configuration at a blob container, with the app's managed identity granted access, gives every worker the same key ring, so a restart does not invalidate sessions and a payload protected by one instance is readable by another. The configuration is a one-time change in startup, and it resolves the entire family of symptoms at once because they all trace to the same root: a piece of state the framework assumed was durable and shared that the read-only mount made neither.

The same reasoning applies to any framework facility that writes state to disk and reads it back. A compiled-view or response cache that the framework writes under the content root fails to write and falls back to recompiling on every request, which is slow but not fatal until the recompilation itself tries to write its output and throws. A plugin or extension system that unpacks into its own directory under the root cannot unpack. Session state stored in a local file vanishes on restart and is invisible to other instances. The unifying instinct is to treat the local file system under the model as ephemeral and unshared, which it is, and to move any state that must persist or be shared to external storage, which the framework almost always supports through configuration. Doing this audit deliberately, alongside the write-path audit, catches the framework-state failures before they surface as confusing session and decryption errors in production rather than as the clear write exceptions that application code produces.

There is a performance dimension worth naming so the relocation does not introduce a new problem. Moving the key ring to external storage adds a network read to operations that touch protected payloads, but frameworks cache the key ring in memory after the first read, so the cost is paid once per worker rather than per request, and it is negligible against the correctness it buys. The mistake would be to move high-frequency cache writes to durable storage as a reflex, turning a fast local operation into a network round trip on every request. The discipline is the same one that governs every write under the model: persist what must survive to external storage, keep what is ephemeral and regenerable in the temp location, and never default a high-frequency write to durable storage simply because the read-only mount refused the local path.

## How to confirm which mode and package your app is running

Diagnosis depends on ground truth about what the worker actually mounted, and the platform exposes that truth in a few places that are worth checking in order. The effective application settings, read from the worker's own environment through the Kudu environment page, are authoritative for whether the setting is in force, because a value defined on the app does not take effect until the app restarts, and an engineer who changed the setting but did not restart can chase a phantom. The site content folder, browsed through the Kudu file-system view, shows whether a package is mounted, and an attempt to create a file there confirms the read-only state directly. The process list shows the runtime that is actually running, which catches the case where the wrong package mounted a different entry point than expected.

When you want a scripted confirmation rather than a manual click-through, read the setting and the deployment state from the command line and reason from the two together:

```bash
# Effective setting value, the first fact that splits the problem.
az webapp config appsettings list \
  --name <app-name> \
  --resource-group <resource-group> \
  --query "[?name=='WEBSITE_RUN_FROM_PACKAGE'].value" \
  --output tsv

# Recent deployment records, to see whether a push actually landed.
az webapp deployment list-publishing-profiles \
  --name <app-name> \
  --resource-group <resource-group> \
  --output table
```

The combination tells you the mode and whether a recent release reached the app. If the value is `1` and a deployment landed but the content did not change, suspect a remount that did not happen, and force a restart. If the value is a URL, fetch the blob it names and confirm it is the package you expected, which closes the loop between what your pipeline produced and what the worker mounted. This habit of confirming the mounted artifact rather than trusting the pipeline's green checkmark is what separates a quick diagnosis from an afternoon of guessing, and it is the discipline worth building into every Run From Package incident.

## Prevention: keeping the package without the read-only failures

The durable fix is not to disable the model but to make your application and your pipeline agree with it, and a few deliberate choices prevent the whole failure family from recurring. The first is to audit every file write in your application and route each one to the correct destination before you ever enable the setting, so the read-only mount surprises nobody. Scratch writes go to temp, durable writes go to external storage, and framework facilities that default to the content root get pointed elsewhere through their own configuration. Doing this audit as a deliberate step, rather than discovering each write one production exception at a time, turns a series of incidents into a single planned change.

The second choice is to standardize the package build so the malformed-archive cause cannot occur. Build the package from the publish output of your project, with the runnable application at the archive root, validate that the archive opens and contains the expected entry point before it is pushed or uploaded, and produce it the same way on every release. A pipeline step that builds, packages, and verifies the archive in one reproducible sequence removes the variability that lets a truncated or wrongly structured zip reach the platform.

The third choice addresses the remote mode specifically. When you run from a URL, prefer identity-based access over a signature baked into the URL, because the identity does not expire and the most common remote failure simply cannot happen. Where a signature is genuinely required, use a stored access policy on the container so validity and revocation are managed centrally, and set an expiry generous enough that routine restarts months later will not outlive it. Combine that with a stable blob name that each release overwrites, so the setting value never has to change and a deployment that updates the artifact cannot leave the setting pointing at a stale one.

The fourth choice is operational. Treat a restart as part of every setting change, because a setting that is defined but not applied is a frequent source of false diagnosis. Build a confirmation step into your release that reads the effective setting and, for the remote mode, validates that the URL resolves to the new artifact, so a release proves it mounted the right package rather than merely reporting that it finished. These four habits, an audited write path, a reproducible package build, identity-based remote access, and a confirmed restart, are what let a team run from a package indefinitely without ever filing another read-only ticket. They are the same operational discipline that keeps a delivery flow healthy across the broader set of App Service deployment concerns, and they pay for themselves the first time a routine restart would otherwise have taken an app down.

## Setting the value as code so the configuration is reproducible

A setting that lives only in a portal blade or a one-off command is a setting that drifts, and drift is how an app ends up with a value nobody can explain after a migration or a recreate. Declaring WEBSITE_RUN_FROM_PACKAGE in your infrastructure definition removes that risk: the value is versioned, reviewed, and applied identically every time the app is provisioned, so the read-only behavior is intentional rather than inherited. In a Bicep definition the setting sits in the site configuration alongside the rest of the app settings, and pairing it with an identity-based access grant for the remote mode keeps the whole arrangement in one reviewable place:

```bicep
resource site 'Microsoft.Web/sites@2023-12-01' = {
  name: appName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: planId
    siteConfig: {
      appSettings: [
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
      ]
    }
  }
}
```

For the remote mode the value becomes the blob URL, and the cleaner arrangement grants the site's system-assigned identity the storage blob data reader role on the container so no signature has to be embedded in the template, where it would either expire or sit as a secret in source control. The role assignment lives in the same definition, the identity is created with the site, and the deployment that provisions the app also wires its access to storage, so there is nothing to configure by hand afterward and nothing to expire.

The pipeline that builds and ships the archive deserves the same rigor, because the malformed-archive and stale-content causes both originate in an inconsistent build-and-push step. A delivery flow that builds the publish output, packages it from that output, verifies the archive opens with the entry point at its root, and only then pushes or uploads it removes the variability that lets a bad bundle reach the platform. Expressed as a sequence of pipeline steps, the build produces the publish output, a packaging step zips that output, a verification step lists the archive contents and fails the run if the entry point is missing, and a deploy step pushes the verified bundle and restarts the app. Each step is small, and together they convert the two most operational causes into failures that the pipeline catches before production ever sees them.

### How do I keep the setting from drifting after a redeploy?

Declare it in your infrastructure definition rather than setting it by hand, so every provision applies the same value. For the remote mode, grant the app's managed identity read access to the storage in the same definition instead of embedding a signature, which removes both the drift and the expiry. Review the value in source control like any other configuration.

## Monitoring so a dying remote package never reaches users

The worst version of a remote-package failure is the one you learn about from a customer, weeks after the deployment that planted the time bomb, when a routine restart finally forces a refetch against an expired signature. Monitoring closes that gap by surfacing the failure as soon as a worker cannot mount the archive, rather than waiting for the symptom to reach a user. The platform emits the startup behavior and the request failures to its diagnostics, and a query against the collected logs can distinguish a clean start from a worker that could not fetch its bundle, which is the signal you want an alert on.

A log query that watches for the failure pattern gives you the early warning. Against the App Service logs collected into a workspace, a query that filters for the startup-failure and package-fetch signatures and counts them over a short window turns a silent expiry into a fired alert:

```kusto
AppServiceConsoleLogs
| where TimeGenerated > ago(1h)
| where ResultDescription has_any ("Run From Package", "Failed to download", "read-only", "package")
| where ResultDescription has_any ("download", "denied", "expired", "mount", "Read-only")
| summarize failures = count() by _ResourceId, bin(TimeGenerated, 5m)
| where failures > 0
```

An alert on that query, firing when the failure count crosses zero, tells you a worker is struggling to mount its archive before the failure becomes general, which buys you time to regenerate a signature or switch to identity-based access while most workers are still serving the previously mounted bundle. Pair the log alert with a simple availability check against the app, so a total mount failure that takes every worker down is caught by the availability signal even if the log pattern shifts. The point of the monitoring is not to replace the diagnosis but to move it earlier, so that the engineer reads the failure from a dashboard at the moment it starts rather than from a support ticket after it has spread.

Building the instinct to read these signals quickly is its own skill, separate from knowing the causes, and it is the one that turns a long outage into a short one. You can [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) that hand you a partial signal, a single failing worker, a log line, an app that starts intermittently, and ask you to reason to the cause and the confirming command, which is exactly the reasoning chain a real incident demands under time pressure.

## Function apps and Run From Package

Function apps deserve their own mention because the setting behaves the same way but the failure modes shift, and engineers often hit them after a function that ran perfectly on a local machine fails on the platform. A function host expects to find its built output at the application root, and under Run From Package that root is the sealed mount, so a package that contains source rather than the built function output leaves the host with nothing to run. The fix mirrors the malformed-archive case: package the publish output, with the compiled functions and their host configuration at the root, and validate the archive before pushing it.

The write-path cause also recurs in functions, because a function that writes a temporary file beside its code, or an extension that caches state in the function app root, hits the same read-only wall the moment the setting is in force. The remedy is identical, redirect scratch writes to the temp path and durable writes to external storage, and it sits naturally alongside the broader serverless model that the [Azure Functions serverless internals deep dive](/2022/01/24/azure-functions-serverless-deep-dive/) lays out, including how the host scales and where its state lives. For functions, running from a package is often the default for a consumption-style plan, which means the read-only behavior is in play whether you set it deliberately or not, so the write-path audit is not optional but a prerequisite for any function that touches the file system.

When you want to reproduce these failures safely before they bite you in production, a controlled environment is worth more than a description, and you can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to stand up an app with the setting enabled, watch a write into the site root fail, and then redirect it to a mutable path and confirm the fix. Pairing that with the diagnostic muscle, you can [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) that present a dead remote package and ask you to walk from symptom to signature to network rule, which is exactly the reasoning chain that turns a Run From Package incident from a guessing game into a checklist.

## A decision rule for where each write belongs

The single change that makes the model painless is deciding, for every write your application performs, which destination it belongs in, and that decision follows a short rule with one deciding factor: the required lifetime and visibility of the data. Ask whether the write must survive a worker restart, and whether more than one instance must see it. If the answer to both is no, the write is scratch, and it belongs in the temporary directory, which is fast, local, and cleared when the worker recycles. If the data must survive a restart but only one logical owner ever reads it back, it belongs in durable external storage chosen by its shape, a blob for an unstructured artifact and a database for structured state. If the data must be visible to every instance at once, it belongs in shared external storage by definition, because the temp location is per worker and cannot satisfy a shared read.

The deciding factor is lifetime and visibility, not convenience, and applying it mechanically resolves the ambiguous cases that otherwise invite a wrong choice. A generated thumbnail that the app can recreate on demand is scratch, even though it feels like a real file, so it goes to the temp location and never touches durable storage. An uploaded document a user expects to retrieve next week must survive and be visible everywhere, so it goes to a blob container behind the app's identity. A data-protection key must survive and be shared, so it goes to external storage despite being small and feeling internal. A per-request working file that one handler writes and the same handler reads moments later is scratch even though it briefly matters, so the temp location is correct. Running each write through the lifetime-and-visibility question turns a vague worry about the read-only mount into a short, repeatable classification that anyone on the team can apply the same way.

| What the write produces | Must survive restart | Must be shared across instances | Correct destination |
| --- | --- | --- | --- |
| Regenerable scratch, intermediate, or cache file | No | No | Temporary directory |
| Per-request working file read back immediately | No | No | Temporary directory |
| Uploaded or generated artifact a user retrieves later | Yes | Yes | Blob container via managed identity |
| Structured application state | Yes | Yes | Database |
| Data-protection keys, session state, shared framework state | Yes | Yes | External storage shared across instances |
| Legacy code that needs a real writable directory | Yes | Depends | Mounted file share |

This classification is the durable companion to the read-only-package rule. The rule explains why the failure happens, and the table tells you exactly where to send the write so it cannot happen again, which together let a team adopt the model across an estate of apps with a single shared mental framework rather than rediscovering the same fix one production exception at a time.

## Related failures often confused with a Run From Package error

Several App Service problems look like a Run From Package failure and are not, and telling them apart saves you from fixing the wrong layer. The clearest neighbor is a deployment that genuinely failed before the app ever ran. When a build step errors, when a file lock blocks the copy in the classic model, or when the deployment endpoint rejects the package, the failure appears in the deployment log and the app never starts the new content, which is a different timeline from the Run From Package write error that appears only after a successful deploy. The full taxonomy of those pre-start failures, including the build and file-lock causes, lives in the [guide to App Service deployment failures](/2023/02/20/fix-app-service-deployment-failed/), and reaching for it first when the failure precedes startup keeps you out of the wrong article.

A second neighbor is a startup error that happens to coincide with a Run From Package deployment but has its own root cause. An app can mount its package cleanly and still fail to start because of a runtime version mismatch, a missing configuration value, or an unhandled exception in its own startup path. That presents as a startup failure with an application exception, and the platform's startup-error handling is the right lens for it. The detailed treatment of those startup failures, including how to surface the real exception behind a generic startup error, sits in the [guide to the App Service 500.30 startup error](/2022/06/20/fix-app-service-500-30-startup-error/). The distinguishing question is whether the package mounted at all: if it did and the app then threw its own exception, you are in startup-error territory, and if the package never mounted, you are in the Run From Package territory this article owns.

A third confusion is a slot swap that appears to break the app. Because Run From Package mounts an identical sealed bundle, a swap is usually cleaner than the copy model, but if the two slots carry different values for the setting, or one points at a package the other cannot reach, a swap can move the app onto a configuration that fails. The signature is an app that worked in one slot and failed after the swap with a setting or package difference between the slots. The fix is to align the setting across slots, or to mark it as a slot-specific setting deliberately when the slots are meant to run different packages, so a swap moves the app onto a configuration that is known to work rather than one that was never exercised.

## The verdict: keep the package, move the write path

The reflex when a Run From Package error appears is to delete the setting and return to the copy model, and that reflex is usually wrong, because it throws away the atomic, identical, instantly swappable deployment the model gives you in order to silence a symptom that a one-line code change resolves. The read-only-package rule is the lens that makes this obvious: the mount is read-only by design, a write into the site root is a design mismatch rather than a platform bug, and the fix is to redirect the write to the temp path or to external storage rather than to abandon the model. The remote variant follows the same logic. A dead remote package is almost never an application problem and almost always a fetch problem, which means the cure lives in the URL, the signature, the network path to storage, or the integrity of the archive, none of which is helped by reverting to a local copy.

Hold the four causes and you can diagnose any instance of this failure quickly: a write into the read-only mount, a bad or expired signature in the URL, a mount blocked by a network rule or a malformed archive, and a value-versus-URL mismatch that mounts the wrong source. Confirm the mode and the mounted artifact rather than trusting the pipeline's success report, route every write to a location the model permits, prefer identity-based access for remote packages so signatures cannot expire under you, and build the package reproducibly so a malformed archive never reaches the platform. Do that and you keep every benefit of running from a package while the read-only failures that drove engineers back to the copy model simply stop happening.

## Frequently Asked Questions

### Q: What does WEBSITE_RUN_FROM_PACKAGE do and why does it fail?

It changes the App Service deployment model from copy-then-serve to mount-and-run. Instead of expanding your files into a writable content folder, the platform mounts your deployed zip as the site directory in a read-only state and serves your code directly from that sealed archive. It fails when something assumes the old writable model: application code that writes a file under the site root hits the immutable mount and throws, a remote package URL with an expired signature cannot be fetched, a storage network rule blocks the download, or the wrong mode is set so the worker mounts stale or missing content. None of these are platform bugs. Each is a mismatch between an assumption the application or pipeline made and the read-only, mount-based contract the setting enforces. Naming which of the four is yours, by reading the setting value and the log stream, is the fastest route to the fix.

### Q: Why is the file system read-only with Run From Package?

Because the setting tells the platform to mount your deployed zip as the site directory rather than expanding it onto the writable content share. The runtime reads your assemblies and assets straight out of that sealed archive, and the platform enforces immutability at the file-system layer so the mounted package cannot be modified at runtime. This is the defining feature, not a fault. Every worker in the plan mounts the identical archive, which makes deployments atomic and swaps clean, because there is no per-instance copy that could land half-finished. The read-only state applies to the site root specifically, so writes there are refused while the temporary directory and any external storage you connect remain writable. If your symptom is a write exception naming a path under the site root, this is the mechanism behind it, and the resolution is to redirect that write rather than to suppress the read-only behavior.

### Q: How do I point Run From Package at a storage URL?

Set the WEBSITE_RUN_FROM_PACKAGE application setting to the full blob URL of your package zip, then restart the app so the value takes effect. The URL usually carries a shared access signature granting read access, generated with the storage tooling and scoped to read only on the specific blob, with an expiry generous enough that routine restarts months later will not outlive it. After setting the value, the platform downloads and mounts the remote archive on start instead of using any locally pushed package. A cleaner option is to grant the app's managed identity the storage blob data reader role on the container and use the identity-based form of the setting, which removes the signature entirely so nothing can expire. For either approach, verify the blob is reachable from the worker, confirm the archive contains your built output at its root, and restart so the worker fetches the new package rather than continuing on a previously mounted one.

### Q: Why does the remote package fail to mount?

Because the worker either cannot reach the storage that holds the archive or cannot open the archive it fetched. A network rule on the storage account that disables or restricts public access can block the worker's download even though the storage works fine from your laptop and your pipeline, and the resolution is to permit the platform to reach storage, route its outbound traffic through a trusted network, or front the blob through a path the app can reach privately. A malformed or truncated archive blocks the open: a zip of the source tree rather than the publish output, a nested folder instead of the build at the root, or an interrupted upload all leave the platform with nothing runnable. To tell them apart, ask whether the worker could reach the storage at all. Download the blob, confirm it opens and that the entry point sits at the root, and check the storage network configuration. The startup carries no application exception because your code never ran.

### Q: What is the difference between value 1 and a package URL?

A value of 1 runs the app from the most recent zip you pushed to the site through its deployment endpoint, which the platform stores and mounts locally on each worker. A URL runs the app from the remote archive at that address, ignoring any locally pushed package. The first mode couples to a push-based pipeline that sends a zip to the deployment endpoint on each release, and the second couples to a flow where your pipeline publishes a blob you manage yourself. Setting the wrong one for your flow produces stale or missing content: with value 1, an app stuck on old code points to a push that did not replace the stored package or a worker that did not remount, and with a URL, stale content points to a setting still naming the previous blob. Decide which model your delivery actually uses, make the setting match, and ensure each release either pushes a fresh package or updates the URL, followed by a restart.

### Q: Why can my app not write files with Run From Package?

Because the site root is mounted read-only, so any file your application opens for writing under that root is refused by the platform. The model serves your code from a sealed archive that cannot be modified while it runs, and code that anchored a writable path to the location of its own binaries now hits the immutable mount. The writes are not blocked everywhere, only inside the mounted package. The fix is to send each write to a location the model permits: scratch and regenerable output to the temporary directory, resolved through your runtime's standard temp accessor rather than a hardcoded path, and durable or shared output to external storage such as a blob container, a database, or a mounted file share. Frameworks that default their data-protection keys, session state, or compiled-view cache to the content root also need redirecting through their own configuration. Sorting writes by purpose usually moves most of them to temp and only a few genuinely durable ones to external storage.

### Q: Where can my app write when Run From Package locks the site root?

Your app can write to the temporary directory, which remains mutable under the model, and to any external storage you connect. The temp directory is local to each worker, cleared on restart, and not shared across the instances in your plan, so it suits scratch space, intermediate rendering, and any output you can regenerate, but never data that must survive a restart or be visible to other instances. Resolve it through your runtime's standard temp accessor because the platform owns the actual location. For durable or shared data, write to external storage chosen by the shape of the data: unstructured artifacts a user will retrieve go to a blob container accessed through a managed identity, structured state goes to a database, and code that genuinely needs a writable directory and cannot be refactored gets a file share mounted into the app as a real path. Matching each write to the right destination is what lets you keep the model without read-only errors.

### Q: My deployment succeeded but the new code never appeared, why?

Because the worker is still serving a previously mounted package rather than your new one, and the deployment reported success without forcing a remount of fresh content. In local mode, with value 1, a push to the deployment endpoint must actually replace the stored package and the worker must restart to remount it, so a push that did not replace the package or a worker that never recycled keeps the old code running. In remote mode, with a URL, the platform keeps mounting whatever blob the URL names, so if your pipeline uploaded a new blob under a different name while the setting still points at the old one, the new code never loads. Confirm the mode, ensure each release either pushes a fresh package or updates the URL to the new artifact, and restart the app. The cleanest pattern is a stable blob name each release overwrites so the setting never has to change.

### Q: Does Run From Package work for a function app, and why might it fail there?

Yes, and it is frequently the default for a consumption-style function plan, so the read-only behavior is in play whether you enabled it deliberately or not. The host expects to find the built function output at the application root, so a package that contains source rather than the published build leaves it with nothing to run, which mirrors the malformed-archive cause: package the publish output with the compiled functions and the host configuration at the root, and validate the archive before pushing. The write-path cause also recurs, because a function that writes a temporary file beside its code or an extension that caches state in the app root hits the same read-only wall the moment the setting is active. Redirect those writes to the temp path for scratch data and to external storage for anything durable. Because the model is often the default for functions, the write-path audit is a prerequisite for any function that touches the file system rather than an optional cleanup step.

### Q: How do I confirm whether WEBSITE_RUN_FROM_PACKAGE is actually in effect?

Read the effective setting from the worker's own environment rather than trusting the value defined on the app, because a setting takes effect only after the app restarts, and a change made without a restart can send you chasing a phantom. The advanced tools environment page lists the settings the worker actually received, which is the authoritative answer. From the command line, query the application settings for the value, and remember that a blank result means the setting is absent and your read-only symptoms come from elsewhere, value 1 means local push mode, and a URL means remote fetch mode. Then confirm the mount itself: browse the site content folder in the advanced tools file-system view and try to create a file there, where a read-only error proves the mount state directly. Pairing the effective value with a direct test of the mount removes the guesswork and tells you which half of the diagnosis applies before you change anything.

### Q: My remote package worked for weeks and then the app died, what happened?

Almost certainly the shared access signature in your package URL expired. The signature grants the platform time-limited read access to the blob, and the app runs fine until a routine restart or a scale event forces the worker to refetch the package, by which time the signature has lapsed and the fetch fails. Nothing in your application changed, which is exactly why it is confusing. Read the expiry encoded in the URL value and compare it to the current time, and test the URL by attempting to read the blob with it from outside Azure: a denied or expired response confirms it. The durable fix is to stop depending on a baked-in expiry. Grant the app's managed identity the storage blob data reader role and switch to the identity-based form of the setting so there is no signature to expire, or where a signature is required, use a stored access policy on the container with a generous validity, then restart so the worker picks up the new access.

### Q: Should I disable Run From Package to stop a read-only error?

No, in nearly every case that is fixing the wrong layer. Disabling the setting returns you to the copy-then-serve model, which gives back a writable site folder but throws away the atomic, identical, instantly swappable deployment the package model provides, and it reintroduces the file-lock and partial-deploy failures the model was designed to remove. The read-only error is a signal that a specific write is landing in the wrong place, and the targeted fix is to redirect that write to the temporary directory for scratch data or to external storage for durable data, which is usually a small code or configuration change. Reserve disabling the model for the rare application so entangled with writing to its own directory that no reasonable refactor is available in the time you have, and even then prefer mounting a writable file share into the app over abandoning the model entirely. Keep the package, move the write path.

### Q: How do I generate a long-lived SAS for the package without it expiring too soon?

Generate the signature scoped to read permission on the specific package blob, over HTTPS only, with an expiry set far enough out that routine restarts months later will not outlive it, and attach it to the blob URL in the setting. A signature minted for a short window is the single most common cause of a remote package that dies weeks after deployment, so err generous on the expiry. For central control over validity and revocation, base the signature on a stored access policy on the container rather than baking a fixed expiry into the URL, which lets you adjust or revoke access without regenerating every URL. The strongest option removes the signature entirely: grant the app's managed identity the storage blob data reader role on the container and use the identity-based form of the setting, so the platform authenticates as the identity and there is nothing that can expire. Reach for identity-based access whenever the app has or can be given a managed identity.

### Q: Why does my framework throw a startup error instead of an obvious write error under the model?

Because many frameworks persist internal state to a folder under the application root by default, and that write happens during startup before any request runs. The data-protection key ring, session state, a compiled-view or response cache, or a plugin unpack step can each target the content root unless configured otherwise. Under the copy model that folder was writable and the framework's first write succeeded silently. Under Run From Package the same write hits the read-only mount and fails during initialization, so the symptom is a generic startup failure rather than a clear write exception from your own code. To resolve it, point each framework facility at a writable location through its own configuration: the data-protection key ring at external storage so keys survive restarts and are shared across instances, the temp-file location at the temporary directory, and any compilation or cache directory at a path the model permits. Surface the real exception through the log stream to identify which facility is failing.

### Q: How do I tell a Run From Package failure apart from a plain deployment failure?

Look at the timeline. A deployment failure stops before the app runs the new content and appears in the deployment log, with a build error, a file lock, or a rejected package as the cause. A Run From Package write failure sails through deployment, which reports success, and only surfaces later when a request exercises the code path that writes into the read-only mount. The green checkmark followed by a runtime write exception is the signature of the latter. Read the WEBSITE_RUN_FROM_PACKAGE value first: if it is present and the runtime exception names a write to a path under the site root, the cause is the read-only mount and not the deployment. If the failure precedes startup and shows in the deployment log, it belongs to the broader deployment-failure family instead. This ordering, setting value then log timeline, decides which body of troubleshooting applies before you spend effort in the wrong place.

### Q: Can a slot swap break an app that runs from a package?

It can, even though swaps are usually cleaner under the model because each slot mounts an identical sealed bundle rather than syncing a directory. The risk appears when the two slots carry different values for the setting, or one slot points at a package the other cannot reach, so that a swap moves the live app onto a configuration that was never exercised. The signature is an app that worked in one slot and failed immediately after the swap, with a setting or package difference between the slots as the difference that matters. To resolve it, align the setting across both slots so a swap is a no-op for the package source, or mark the setting as a slot-specific value deliberately when the slots are meant to run different packages, and verify that the target slot mounts a working package before promoting it. Confirming the mounted artifact in the staging slot before the swap turns the swap into a safe, rehearsed step.

### Q: How do I make the package build reproducible so a malformed archive never reaches the platform?

Build the package in a single deterministic pipeline step from the publish output of your project, with the runnable application at the archive root rather than nested in a folder or left as raw source, and validate that the archive opens and contains the expected entry point before any push or upload. The malformed-archive cause is mechanical: a zip of the project directory rather than the build, a nested top-level folder, or a truncated upload from an interrupted transfer. A pipeline that builds, packages, and verifies in one reproducible sequence removes the variability that lets any of those reach the worker. Pair that with a stable blob name each release overwrites in the remote mode, so the setting never has to change and a deployment cannot leave the URL pointing at a previous artifact. Producing the package the same way every time, and proving it opens, converts an intermittent and confusing failure into one that simply cannot occur.

### Q: Is the temp directory durable enough to rely on under Run From Package?

No, and treating it as durable is a mistake that surfaces as data quietly disappearing. The temporary directory is writable under the model, which makes it the correct home for scratch space, intermediate rendering, and any output you can regenerate, but it is local to each worker, it is cleared on restart, and it is not shared across the instances in your plan. Anything written there can vanish when a worker recycles, scales, or moves, and a second instance handling a later request will not see it. Use it only for data whose loss is harmless because you can recreate it. For anything a user will retrieve later, anything that must survive a restart, or anything multiple instances must share, write to external durable storage instead: a blob container for unstructured artifacts, a database for structured state, or a mounted file share for code that needs a real writable directory. Matching the storage to the lifetime of the data is the discipline that keeps the model working.

### Q: Does running from a package change how I should handle application logs?

Yes, because a logging configuration that writes a file beside the application is one of the most frequent triggers of the read-only error. Under the model, the log file target sits inside the immutable mount and the first write fails, sometimes loudly as a write exception and sometimes as a confusing startup failure if logging initializes early. The fix is to stop writing logs to the site root entirely. Send application logs through the platform's diagnostic logging so they flow to the log stream and to a configured destination such as a storage account, which you can read live while reproducing a failure, or write them to external storage directly through your logging library's configuration. If a library insists on a local file during development, point its file target at the temporary directory for the platform environment so it lands in a writable location, accepting that those local files are ephemeral. Treating logs as telemetry to ship rather than files to keep on disk aligns logging with the read-only model.
