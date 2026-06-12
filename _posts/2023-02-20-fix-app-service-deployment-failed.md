---
layout: post
title: "Fix Azure App Service Deployment Failed Errors"
page_title: "Fix Azure App Service Deployment Failed: File Lock, Oryx Build Failure, Runtime Mismatch, and Run From Package Errors Explained for Engineers"
date: 2023-02-20
categories: ["Technology"]
tags: ["Azure", "App Service", "Troubleshooting", "DevOps", "Deployment", "Cloud Computing"]
excerpt: "An App Service deployment failed message usually traces to a file lock, an Oryx build error, a runtime mismatch, or permissions. Here is how to fix each one."
image: "/assets/images/blog/blog-93.webp"
reading_time: 60
author: "kevin-reeves"
last_updated: 2023-02-20
lang: en
---
An App Service deployment failed message is one of the least helpful errors Azure shows you, because the words on the screen almost never name the thing that actually broke. The portal says the operation failed, the pipeline turns red, and the underlying reason sits in a log you have not opened yet. Most engineers respond by clicking deploy again, and most of the time the second attempt fails the same way, because the cause was structural rather than transient. The fix is not to retry harder. The fix is to read the right log, decide which of a small set of distinct causes you are looking at, and change the one thing that caused it. This article walks through that diagnosis end to end, with the command that confirms each cause and the tested fix that clears it, including the path that removes both the failure and the downtime at the same time.

![Fixing Azure App Service deployment failed errors and the file lock and build causes - Insight Crunch](/assets/images/blog/blog-93.webp)

The reason the generic message is so common is that "deploy" on App Service is not one operation. It is a family of operations that share a screen. A zip deploy uploads an archive and unpacks it into the site root. A Run From Package deploy uploads or references an archive and mounts it read-only. A continuous integration push hands a build artifact to the platform and asks the platform to build, or asks it only to copy. A local Git push triggers a server-side build through Oryx. FTP copies files directly. Each of these can produce the same red banner for an entirely different reason, so the first job is never to fix anything. The first job is to find out which deploy method you used and which stage of it failed. Once you know that, the cause is usually obvious, and the rest of this guide exists to make that mapping precise.

## What an App Service deployment failure actually means

The phrase covers two very different moments in the life of a release, and conflating them is the most common reason a deployment investigation goes in circles. The first moment is the deploy itself: the act of getting your bytes onto the platform, unpacked or mounted, and the worker restarted to pick them up. The second moment is what the application does when it starts running those bytes. A deploy can succeed perfectly and the app can still fail to start, and a deploy can fail outright before the app ever gets a chance to run. The error surfaces look similar in the portal, but they live in different logs and have different fixes, so the discipline that saves you the most time is deciding which moment you are in before you touch anything.

A true deployment failure happens during the transfer and activation stage. The package did not upload, the unpack hit a locked file, the server-side build threw an error, the deployment credential was rejected, or the operation timed out. These failures show up in the deployment log, which is a different stream from the application log. They are about the plumbing that moves and activates your code, not about your code's behavior once it runs. When this stage fails, the previously running version usually keeps serving, because in-place deploys do not remove the old files until the new ones are in place, and Run From Package swaps the mount atomically. That detail matters: a failed deploy is often not an outage, which buys you time to diagnose calmly rather than under incident pressure.

The other moment, where the deploy reports success but the site then returns a 503 or a 500.30, is a startup failure rather than a deployment failure, and it belongs to a different diagnosis. We cover the boundary later in this guide because engineers routinely misfile one as the other, and the misfiling sends them reading the wrong log for an hour. For now, hold the distinction: a deployment failure is a transfer-and-activation problem visible in the deployment log, and a startup failure is a runtime problem visible in the application log and the log stream. The whole strategy of this article rests on that line.

### Where does the real error message live?

The real error almost never appears in the banner. It lives in the deployment log, reachable through the Deployment Center in the portal and through the Kudu site at your-app.scm.azurewebsites.net. The banner reports that an operation failed; the deployment log reports the stage and the exact line that failed. Open the log first, every time.

That habit alone resolves a large share of cases, because the deployment log is verbose where the banner is silent. It records the upload, the unpack or mount, the build steps if a build ran, the post-deploy restart, and the exit code of each. When a zip deploy fails on a locked file, the log names the file it could not overwrite. When Oryx fails, the log shows the build command and the compiler or package-manager error. When a credential is rejected, the log or the HTTP response carries a 401 or 403 rather than a vague failure. The banner abstracts all of that away to keep the portal tidy, which is exactly why the banner is useless for diagnosis. Treat it as a notification that something happened, then go straight to the stream that says what.

## The deployment methods, and how each one fails

You cannot map a failure to a cause without knowing which deploy method produced it, because the same red result means different things across methods. There are five methods you will meet in practice, and each has a characteristic failure signature. Knowing the signatures turns a vague failure into a short list of suspects.

Zip deploy, invoked with `az webapp deploy --type zip` or the older `az webapp deployment source config-zip`, uploads a zip archive and unpacks it into the site root at `/home/site/wwwroot`. Its characteristic failures are a file lock during the unpack, because the running worker is holding a DLL or executable open, and an Oryx build failure if build-on-deploy is enabled. Because zip deploy writes into the live site directory, it is the method most exposed to the file-lock problem, and that exposure is the single most important fact in this whole guide.

Run From Package, controlled by the `WEBSITE_RUN_FROM_PACKAGE` application setting, does not unpack into the site root at all. It mounts the package as a read-only file system over `wwwroot`. Because nothing is unpacked over running files, the file-lock failure simply cannot occur with this method, which is why switching to it is one of the cleanest fixes in the entire diagnosis. Its own failure modes shift to the package reference: a bad value, an unreachable storage URL, or an expired shared access signature. We treat the deeper behavior of that setting in its own article on common ways the run from package setting and its read-only mount cause confusing failures, linked later, because the mechanics there deserve their own walkthrough.

Continuous deployment from a pipeline, whether Azure DevOps or GitHub Actions, wraps one of the above transports inside an automated identity. Its extra failure surface is authentication: the pipeline's service connection, publish profile, or federated credential is rejected, or the platform's basic-auth publishing path is switched off so a publish-profile-based step cannot connect. The build may also run in the pipeline or on the server depending on configuration, and a mismatch there produces a build failure that looks like a deploy failure.

Local Git deployment pushes a branch to a remote that the platform exposes, and the push triggers a server-side Oryx build by default. Its failures are almost always build failures: a missing build manifest, an unsupported project layout, a runtime the build did not detect, or a dependency restore that could not reach its feed. FTP and FTPS, finally, copy files directly into `wwwroot` with no build and no atomicity, so its failures are connection and credential problems and the subtle corruption of a half-finished upload that left the site in a mixed state.

### Which deploy method am I actually using?

Check the Deployment Center's source setting and the deploy command or pipeline task. Zip deploy and Run From Package both take a zip, but Run From Package is identified by the `WEBSITE_RUN_FROM_PACKAGE` app setting being present. Local Git shows a Git source; a pipeline shows an external source. The method dictates the failure shortlist, so confirm it first.

This is not a pedantic step. An engineer who believes they are doing a clean package deploy but actually has build-on-deploy enabled will chase a runtime mismatch that is really a server-side build error, and vice versa. The method and its build behavior are the frame for everything that follows, and the two settings that fix the method into place are `WEBSITE_RUN_FROM_PACKAGE` for the mount behavior and `SCM_DO_BUILD_DURING_DEPLOYMENT` for whether Oryx runs on the server. Read both before you read anything else. They tell you, in two lines, what kind of failure you are even allowed to have. If you want the broader hosting and slot model these methods sit inside, the [App Service engineering deep dive](/2022/01/10/azure-app-service-deep-dive/) lays out the worker, the plan, and the deployment surface in one place, and it is worth reading once so the rest of this diagnosis has a frame to hang on.

## How do you read the deployment logs in Kudu and the Deployment Center?

The Deployment Center shows a list of deployments with a status and a timestamp, and clicking one opens its log. Kudu, at your-app.scm.azurewebsites.net, exposes the same data with more detail plus a live log stream and a file browser. Read the failed deployment's log top to bottom; the failing stage and its exact error sit there, not in the portal banner.

The Kudu site, formally the Source Control Manager site or SCM site, is the deployment engine's own administrative surface, and it is the single most useful place to stand when a deploy fails. Reaching it requires that you be authenticated, and on a new app with basic authentication disabled you reach it through your Entra ID sign-in to the portal rather than through publish-profile credentials, a point we return to under the permissions cause because it trips up automated tooling constantly. Once inside, the deployment log directory under `/home/LogFiles` and the deployment records under the deployments endpoint hold the history. The log of the most recent failed attempt is the document you came for.

When you read it, you are looking for the last successful line and the first failing line, because the boundary between them names the stage. If the last successful line is the upload completing and the first failing line is an unpack step naming a specific file, you have a file lock. If the build started and then a compiler, a package restore, or a runtime-detection step failed, you have an Oryx build problem. If the log barely starts before a 401 or 403, you have a credential or permission problem and never reached the real work. If the upload itself never completed and the operation ended on a timeout, you have a size or network problem. Four boundaries, four causes, and the log draws the boundary for you. Everything after this is confirming which boundary you are at and applying the matching fix.

You can pull the log without the portal, which matters for scripting and for incident response when you want the evidence in your terminal. The Azure CLI exposes the deployment log stream and the recent deployments, and a direct call to the Kudu API returns the structured deployment records.

```bash
# Tail the live deployment and application log stream
az webapp log tail \
  --name my-web-app \
  --resource-group my-rg

# List recent deployments through the Kudu deployments API
az rest --method GET \
  --uri "https://my-web-app.scm.azurewebsites.net/api/deployments" \
  --resource "https://management.azure.com"
```

The first command streams logs live, which is most useful when you trigger a deploy and watch it fail in real time. The second returns the deployment history as JSON, where each entry carries an id, a status, and a message, and the id lets you fetch the full log for a single failed attempt. Reading these in a terminal rather than the portal is faster once you are doing this often, and it is exactly the kind of repeatable evidence-gathering you can rehearse safely by breaking and recovering a deploy in a sandbox, which is what the [scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) are built for: a place to reproduce a failed deploy and practice the diagnosis until the log boundaries are obvious at a glance.

## The InsightCrunch deployment-failure table

The diagnosis above reduces to a small map. Each cause has a log signal that confirms it and a fix that clears it, and several of them share a single better path that removes the failure and the downtime together. This is the table to keep open while you work.

| Cause | What the deployment log shows | The fix | Zero-downtime path |
| --- | --- | --- | --- |
| Running app holds a file lock | Unpack fails naming a specific `.dll`, `.exe`, or file in use | Stop the app or switch to Run From Package; do not retry in place | Run From Package, or deploy to a stopped staging slot and swap |
| Oryx build fails on the server | Build command runs, then a restore, compile, or runtime-detection error | Fix the build error, or build in the pipeline and disable server build | Build the artifact in CI, deploy the built package to a slot, swap |
| Package targets the wrong runtime | Deploy succeeds, app then fails to start with a runtime or framework error | Align `linuxFxVersion` or the stack to the package's target runtime | Validate the runtime on a slot before swapping into production |
| Deploy identity lacks permission | A 401 or 403 early in the log, before the real work | Enable SCM basic auth or use an Entra-based deploy identity with rights | Use a managed identity or federated credential on the slot deploy |
| Slot-specific setting breaks the swap | Swap completes, app misbehaves with a configuration that moved | Mark the environment-bound settings as slot settings (sticky) | Validate settings on the slot, then swap; swap back if it regresses |
| Large package times out | Upload stalls or the operation ends on a timeout | Shrink the package, exclude build artifacts, or use Run From Package | Stage the package in storage and reference it by URL for the slot |

Call this the InsightCrunch deployment-failure table. The structure it teaches is the whole method in one view: read the log signal, pick the row, apply the fix, and where a zero-downtime path exists, prefer it, because most of these causes are removed entirely by the same two patterns rather than merely worked around. The right-hand column is the part competitors skip, and it is the part that turns a recurring deploy incident into a non-event.

## Cause one: the running app holds a file lock

This is the cause that defines App Service deployment failures, and it is the one the retry button can never solve. When a zip deploy or an FTP upload writes into `/home/site/wwwroot` while the worker process is running, the operating system refuses to overwrite a file that the running process has open. On Windows hosting this is a hard lock: a managed runtime loads its assemblies into the process and holds the file handles for the lifetime of the process, so the deploy step that tries to replace `MyApp.dll` or a native dependency gets an access-denied result and the whole unpack aborts. The deployment log names the file it could not write, which is the unmistakable signature of this cause. You do not need to guess; the log spells out which file was in use.

The instinct on seeing this is to deploy again, and the instinct is exactly wrong, because the worker is still running and still holding the same handles, so the second attempt locks on the same file at the same step. Engineers can burn an afternoon retrying into a lock that is structurally guaranteed to recur, and the frustration is real because nothing in the banner explains why the same action keeps producing the same result. The lock is not flaky; it is deterministic. The file is held because the app is up, and the app is up because you did not stop it, and you did not stop it because stopping production to deploy is exactly what you are trying to avoid. That tension is the whole problem, and it has a clean resolution that does not involve stopping production at all.

### Why does retrying an in-place deploy keep hitting the same file lock?

Because the lock is held by the running worker process, not by a transient condition. The runtime loads your binaries and keeps their file handles open for as long as the process lives, so any in-place overwrite of those files is refused while the app runs. Retrying changes nothing; the same process holds the same handles.

The blunt fix is to stop the app, deploy, and start it again, which releases the handles and lets the unpack complete. It works, and on a development or staging app it is perfectly reasonable.

```bash
# Stop the app to release file handles, deploy, then start
az webapp stop --name my-web-app --resource-group my-rg

az webapp deploy \
  --name my-web-app \
  --resource-group my-rg \
  --src-path ./app.zip \
  --type zip

az webapp start --name my-web-app --resource-group my-rg
```

The cost of that sequence is downtime: between the stop and the start, the app serves nothing. For a side project that is acceptable. For anything a user touches, it is not, and reaching for it in production is the wrong reflex. The better answer is to make the file lock impossible rather than to schedule around it, and there are two ways to do that, both of which appear in the zero-downtime column of the table and both of which we develop in full later. The short version is that Run From Package mounts the package read-only so there is nothing to overwrite and nothing to lock, and the deploy-to-slot-and-swap pattern deploys into a slot whose worker is not the production worker, so the production handles are never in contention. Either one turns this cause from a recurring incident into a structural impossibility. That is the file-lock half of the rule this article is built around.

On Linux hosting the lock behaves differently but the lesson survives. Linux will often let you replace a file that is open, because the inode stays alive for the holder until it closes, but the running process keeps serving the old inode while the new bytes sit in a new inode, so you can get a deploy that reports success while the app keeps running stale code until it restarts. That is a quieter failure than the Windows lock, and it fools engineers into thinking the deploy did not take when in fact it took but did not activate. The resolution is the same family of patterns: a method that activates the new code atomically and restarts the worker as part of activation, which both Run From Package and a slot swap provide.

## Cause two: the Oryx build fails on the server

When build-on-deploy is enabled, the platform runs Oryx, the build system App Service uses to turn your source into a runnable app. Oryx detects the language, restores dependencies, runs the build, and produces the output the runtime will serve. Any of those stages can fail, and when one does, the deployment log shows the build command and the error from the tool that broke, which is the signature that separates a build failure from a transfer failure. You are not looking at a lock or a credential here; you are looking at a compiler, a package manager, or a runtime-detection step that returned non-zero.

The most common Oryx failure is a detection or restore problem. Oryx decides which platform you are on by looking for marker files: a `package.json` for Node, a `requirements.txt` or `pyproject.toml` for Python, a `.csproj` or solution for .NET, a `pom.xml` for Java. If the marker is missing, in an unexpected place, or ambiguous because the repository holds more than one project, detection picks the wrong stack or fails outright, and the build error reflects a tool you did not expect to run. The fix is to make detection unambiguous, either by deploying only the project you mean to deploy, by setting the project path the build should target, or by telling Oryx the platform explicitly through build configuration. A repository that builds locally can still confuse server-side detection, because your local build has context that the server does not.

### Why does the Oryx build fail when my project builds fine locally?

Because the server build runs in a clean environment without your local tooling, caches, global packages, or environment variables. Oryx detects the stack from marker files and restores from the feeds it can reach, so a missing marker, a private feed it cannot authenticate to, or a tool version it does not provide produces a failure your machine never sees.

The reproducible way to settle a build failure is to read the exact failing command from the log and run the equivalent locally in a clean container, because the gap between your machine and the server is almost always something your machine has and the server does not. Pin the runtime version so the server uses the same one you do. Vendor or restore private dependencies in a way the server can reach, since the server cannot authenticate to a private feed it has no credentials for. And if the build is genuinely heavy or depends on tooling the server does not provide, stop building on the server at all.

```bash
# Disable server-side Oryx build so the platform only copies your artifact
az webapp config appsettings set \
  --name my-web-app \
  --resource-group my-rg \
  --settings SCM_DO_BUILD_DURING_DEPLOYMENT=false
```

Setting `SCM_DO_BUILD_DURING_DEPLOYMENT` to false tells the platform to copy your package as-is and skip Oryx entirely, which means you build the artifact yourself in a pipeline where you control the environment, the tool versions, the private-feed credentials, and the caches. This is the cleaner pattern for any non-trivial app, because a build that runs in your continuous integration system is reproducible, observable, and fast, whereas a server-side build is a black box that you can only watch through a log after it fails. The trade-off is that you now own the build, including producing an artifact that matches the target runtime exactly, which leads directly into the next cause. Build where you can see and control the build, then ship the built thing.

There is a subtler Oryx failure worth naming: a build that succeeds but produces output the runtime cannot start, usually because the startup command or the output structure does not match what the platform expects. On Linux, the platform looks for a way to start your app, and if your framework needs a specific startup command and you did not supply one, the build can complete while the app fails to launch. That straddles the line between a deploy failure and a startup failure, and it is the kind of case that sends engineers to the wrong log. When the build log is clean but the app does not come up, you have crossed from deployment into startup, and the diagnosis moves to the application log and the techniques in the startup-error material linked later.

## Cause three: the package targets the wrong runtime

A package built for one runtime version and deployed to a worker configured for another produces a deploy that reports success and then an app that will not start, which is one of the most disorienting failures in the set because the deploy log is green. The bytes transferred, the unpack or mount completed, and the platform recorded a successful deployment, so by the deployment log's standards nothing failed. The failure is a mismatch between what your package expects and what the worker provides, and it surfaces only when the worker tries to run the code. This is where the deployment failure and the startup failure meet, and recognizing the seam is what keeps you from reading the deployment log for an answer that is not there.

The mismatch takes a few shapes. A .NET app published against one major framework version deployed to a worker pinned to another will fail to load the runtime. A Node app built against one Node major deployed to a worker running a different major can fail on native modules compiled for the wrong ABI. A Python app whose wheels were built for one interpreter version deployed to a worker on another can fail to import compiled extensions. In every case the package and the worker disagree about the runtime, and the worker wins, because the worker is what actually runs the process. The fix is to make them agree, and the durable way to do that is to pin the worker's runtime explicitly rather than relying on a default that can drift.

```bash
# Pin the Linux runtime stack so the worker matches the package target
az webapp config set \
  --name my-web-app \
  --resource-group my-rg \
  --linux-fx-version "DOTNETCORE|8.0"

# Confirm the configured runtime stack
az webapp config show \
  --name my-web-app \
  --resource-group my-rg \
  --query "linuxFxVersion"
```

On Linux the `linuxFxVersion` setting names the runtime and version the worker uses, and pinning it to the version your package targets removes the drift. On Windows the stack settings serve the same purpose for the relevant runtime. The verification command reads the configured stack back so you can confirm it matches your build target before you wonder why the app will not start. The principle is the same one that runs through the whole guide: do not rely on an implicit default that can change under you; state the runtime so the package and the worker cannot disagree.

The reason this cause is worth a confirming step rather than a guess is that its symptom, an app that will not start after a clean deploy, overlaps with several startup failures that have nothing to do with the runtime version. A missing connection string, a configuration error, or a dependency the app cannot reach at startup all produce a similar surface, and you can waste real time aligning a runtime that was never the problem. Confirm the mismatch by comparing the package's target against the configured stack before you change anything, because a runtime fix applied to a configuration problem leaves you exactly where you started with one more variable changed.

## Cause four: the deploy identity lacks permission

This cause has quietly become the most common reason a previously working pipeline starts failing, and it is the one most likely to confuse an engineer who changed nothing in their own code or configuration. App Service can authenticate deployments two ways. The historical way is basic authentication: a username and password from the publish profile, used by FTP, Web Deploy, and many pipeline tasks. The modern way is Entra ID: an OAuth token from a service principal, a managed identity, or a federated credential. The pivotal fact, which you should verify against the current platform behavior because it has shifted and may shift again, is that basic authentication is now disabled by default on newly created apps. A pipeline step that relies on a publish profile will be rejected on a new app even though the same step worked yesterday on an older one.

The signature in the deployment log is an early 401 or 403, before any real deploy work happens. The transport never authenticated, so it never got to upload, unpack, or build. Engineers misread this as a transient platform problem and retry, but a rejected credential is not transient; it is rejected every time for the same reason. The question to answer is not whether to retry but which authentication path your deploy uses and whether that path is enabled and authorized.

### Does my deploy identity need basic auth enabled or an Entra-based role?

It depends on the deploy path. Publish-profile, FTP, and Web Deploy steps use basic authentication, which is off by default on new apps and must be turned on to work. Pipeline steps using a service connection or managed identity authenticate through Entra ID and instead need the right RBAC role on the app, not basic auth.

If your deploy genuinely needs basic authentication, because the tool or step only speaks the publish-profile protocol, you turn the SCM publishing credential back on, accepting that it is the less secure path.

```bash
# Re-enable SCM basic auth publishing for publish-profile based deploys
az resource update \
  --resource-group my-rg \
  --name scm \
  --namespace Microsoft.Web \
  --resource-type basicPublishingCredentialsPolicies \
  --parent sites/my-web-app \
  --set properties.allow=true
```

That command sets the SCM basic publishing policy to allow, which restores the publish-profile path. It is the right fix when a tool requires it, but it is worth pausing on, because the platform turned it off by default on purpose. The more durable direction is to move the deploy onto an Entra-based identity, where a service principal or, better, a managed identity holds an RBAC role on the app rather than a long-lived password. With that arrangement there is no publish profile to leak, no basic-auth toggle to forget, and the deploy authenticates with a short-lived token scoped to exactly the app. The pipeline task changes from a publish-profile step to a step that uses the service connection or the workload identity, and the failure class disappears with it.

When the deploy uses an Entra identity and still gets a 403, the problem moves from authentication to authorization: the identity authenticated but lacks the role that permits a deploy. The deploy identity needs a role with the right to publish, and assigning it at the scope of the app rather than over-assigning a broad role across the subscription is both the correct least-privilege posture and the thing that makes the failure go away. Role assignments also take a short time to propagate, so a freshly assigned role can produce a 403 for a minute or two before it takes effect, which looks like the fix did not work when in fact it had not landed yet. Wait for propagation before you conclude the role was wrong. The discipline here is the same one that runs through identity diagnosis across the series: separate authentication from authorization, confirm which one failed, and grant the specific right at the specific scope rather than widening access until the error stops.

## Cause five: a slot-specific setting breaks the swap

Deployment slots are the feature that makes zero-downtime deploys possible on App Service, and they introduce a failure of their own that has nothing to do with transferring bytes. When you deploy to a staging slot and swap it into production, most of the slot's configuration travels with the code during the swap, but some settings are meant to stay attached to the slot they belong to. A connection string that points at a staging database, a setting that names the environment, or a slot-specific configuration that should never reach production will, if it is not marked correctly, swap into production along with the code and break the live app with a configuration that was only ever meant for staging. The deploy succeeded, the swap completed, and the app is now misconfigured because a setting moved when it should have stayed.

The mechanism is the distinction between a regular application setting and a slot setting, sometimes called a sticky setting. A regular setting moves with the swap, following the code, which is correct for anything that is part of the application's definition. A slot setting is pinned to its slot and does not move, which is correct for anything that names the environment: the database the slot talks to, the storage account it uses, the feature flags that differ between staging and production. The failure happens when an environment-bound setting is left as a regular setting, so it swaps into production and the production app suddenly points at staging resources, or the reverse. The fix is to mark the environment-bound settings as slot settings so they stay put during the swap.

```bash
# Mark environment-bound settings as slot settings so they do not swap
az webapp config appsettings set \
  --name my-web-app \
  --resource-group my-rg \
  --slot staging \
  --slot-settings "ENVIRONMENT_NAME=staging" "DB_CONNECTION=staging-db"
```

Using `--slot-settings` rather than `--settings` pins those keys to the slot, so when you swap, they stay with their slot and the code finds the right environment on each side. The verification is to inspect both slots' settings before a swap and confirm that everything environment-bound is marked sticky and everything application-bound is not, because the swap is the moment the marking is tested and a swap is harder to reason about after it has already gone wrong. This is also why a swap that looks fine in staging can regress in production: the regression is not in the code, it is in a setting that moved when it should not have, and the only way to catch it before users do is to validate the slot's effective configuration before the swap rather than after.

There is a related slot surprise worth naming, which is that some settings beyond app settings and connection strings have their own swap behavior, including certain platform settings that are slot-specific by nature. The general rule survives all of them: anything that should differ between the version running in staging and the version running in production must be pinned to its slot, and anything that is part of the application itself should travel with the code. When you internalize which of your settings name the environment and which define the app, the slot-swap failure stops happening, and the swap becomes the safe, instant cutover it is supposed to be.

## Cause six: a large package times out

A deploy can fail simply because the package is too large to transfer and activate within the platform's operation window, and this cause is easy to miss because the log shows no error in your code, your build, or your credentials. The upload stalls, the operation runs long, and the deploy ends on a timeout. The package grew, usually because the build started including artifacts it should exclude, and the bloated archive pushed the transfer past the limit. The signature is a deploy that used to work and now times out, often after a dependency was added or a build configuration changed, with no error other than the timeout itself.

The first thing to check is what is actually in the package, because a surprising amount of deploy bloat is accidental. Build intermediates, test artifacts, local caches, version control directories, and committed dependency folders all inflate the archive without adding anything the running app needs. Excluding them often shrinks the package by an order of magnitude. A deploy ignore file or an explicit include list keeps the package to the runnable output, and a smaller package transfers faster, activates faster, and stops timing out. This is the cheapest fix in the guide and the one most often overlooked, because engineers assume the platform is slow when in fact they are shipping their entire working directory.

When the package is genuinely large because the app legitimately needs it, the better answer is to stop pushing the bytes through the deploy transport at all and instead stage the package in storage and reference it by URL. Run From Package can point at a package in a storage account through a URL, so the deploy becomes a setting change that points the app at an already-uploaded package rather than a transfer that has to complete within an operation window. The upload to storage is a separate, resumable operation with its own generous limits, and the activation is a mount rather than an unpack, which removes both the timeout and the file lock at once. That convergence, where the fix for a timeout is the same pattern that fixes the file lock, is not a coincidence; it is the reason the next section treats those patterns as the spine of the whole diagnosis rather than as one fix among many.

## The zero-downtime path: Run From Package and deploy-to-slot-and-swap

Three of the six causes above, the file lock, the timeout, and most of the slot-setting surprises, dissolve under two patterns, and a fourth, the runtime mismatch, becomes catchable before it reaches users. This is the heart of the guide, and it is worth stating as a rule you can carry into every deploy you ever run on App Service: an in-place deploy can fail because the running app locks files, so Run From Package or a deploy-to-slot-and-swap removes the lock and the downtime at once. Call it the file-lock-and-package rule. It compresses the whole diagnosis into a habit, because once you deploy this way, the most common failure class in the set simply cannot occur, and the others get a validation gate before production sees them.

Run From Package is the first pattern, and its power comes from what it refuses to do. Instead of unpacking your archive over the live site, it mounts the archive as a read-only file system over `wwwroot`. Nothing is written into the running site's directory, so there is no file to overwrite and therefore no handle to be locked, which is why the file-lock cause is structurally impossible under this method rather than merely less likely. The activation is atomic: the platform mounts the new package and restarts the worker to pick it up, so there is no window where the site is half-old and half-new. And because the package can be referenced from storage by URL, a large package no longer has to squeeze through the deploy transport inside an operation window. One setting change removes three failure modes.

```bash
# Run From Package, referencing a package staged in storage by URL
az webapp config appsettings set \
  --name my-web-app \
  --resource-group my-rg \
  --settings WEBSITE_RUN_FROM_PACKAGE="https://mystorage.blob.core.windows.net/packages/app.zip?<sas>"

# Restart so the new package mounts
az webapp restart --name my-web-app --resource-group my-rg
```

The setting points the app at the package, and the restart mounts it. The package itself is uploaded to storage as a separate step, which is resumable and not bound by the deploy operation window, so even a heavy package activates cleanly. The trade-off, which deserves its own treatment, is that the file system over `wwwroot` is now read-only, so any app that writes next to its own binaries, a cache file, a log, a generated config, will fail because there is nowhere to write. That is not a deployment bug; it is a design mismatch that the run from package read-only model exposes, and the fix is to redirect those writes to a writable path rather than to abandon the pattern. The deeper mechanics of that read-only behavior, the difference between a value-based and a URL-based package, and the mount failures that follow a bad reference are exactly what the [companion article on run from package errors](/2023/02/27/fix-website-run-from-package/) works through, so when an app that deployed cleanly suddenly cannot write a file, that is where to go.

Deploy-to-slot-and-swap is the second pattern, and it is the one to reach for when you want validation before production and a swap you can reverse. You create a staging slot, deploy into it, let it warm up and prove it starts, and then swap it into production. The swap is the moment the new code goes live, and it is a routing change rather than a redeploy, so it is fast and it is reversible: if the swapped-in version misbehaves, you swap back and the previous version returns immediately. Because the deploy lands in the slot's worker rather than the production worker, the production file handles are never in contention, so the file lock cannot occur there either. And because the slot runs the new code before the swap, the runtime mismatch and the slot-setting surprise both get a chance to surface in staging rather than in front of users.

```bash
# Create a staging slot, deploy to it, warm it, then swap
az webapp deployment slot create \
  --name my-web-app \
  --resource-group my-rg \
  --slot staging

az webapp deploy \
  --name my-web-app \
  --resource-group my-rg \
  --slot staging \
  --src-path ./app.zip \
  --type zip

az webapp deployment slot swap \
  --name my-web-app \
  --resource-group my-rg \
  --slot staging \
  --target-slot production
```

The platform warms the staging slot before routing production traffic to it during the swap, so the first request after the swap does not pay a cold start, which is one of the reasons a swap is smoother than a restart-in-place even when both would technically work. The swap step is the cutover, and the same command run again with the slots reversed is the rollback. This pattern is the foundation of the broader release strategies the series covers under [blue-green and canary deployments](/2025/02/17/azure-blue-green-canary-deployments/), where the slot swap becomes the mechanism for shifting traffic between versions deliberately rather than all at once, and that article is the right next read once the basic swap is comfortable.

### Should I deploy to a slot and swap, or just deploy in place?

For anything users touch, deploy to a slot and swap. The swap is near-instant, reversible, and avoids the file lock entirely because the production worker is never overwritten. In-place deploy is acceptable only for non-production apps where a brief restart and the file-lock risk are tolerable.

The two patterns are not mutually exclusive, and the strongest setup combines them: deploy a packaged artifact to a staging slot using Run From Package, validate it there, and swap. That arrangement gives you the read-only atomic activation of Run From Package, the validation and reversible cutover of slots, and immunity to the file lock from both directions. It is more moving parts than a single in-place zip deploy, which is the honest trade-off, but the moving parts are the ones that turn deployment from a thing you hold your breath through into a thing you do several times a day without thinking about it. The reproducible way to get comfortable with the combined flow is to build it once in a sandbox and run the swap a dozen times until the sequence is muscle memory, which is precisely the kind of exercise the [hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) is set up for, with the slot creation, the package deploy, and the swap available to run and rerun until the pattern is second nature.

## Prevention: a deployment pipeline that does not hit a file lock

The causes in this guide are not random; they cluster around a few decisions that, made well once, stop the failures from recurring. Prevention is mostly a matter of choosing a deploy architecture that closes the failure classes structurally rather than handling each failure as it arrives. The architecture that does this has four decisions in it, and each one maps to a cause you have now seen.

The first decision is where the build runs. Build the artifact in your continuous integration system, not on the server, by setting `SCM_DO_BUILD_DURING_DEPLOYMENT` to false and producing a runnable package in a pipeline where you control the runtime, the dependencies, and the caches. This closes the Oryx build failure class, because there is no server-side build to fail, and it gives you a reproducible, observable build with logs you can read before anything ships. A built artifact is also faster to deploy than source the server has to build, so the deploy itself shrinks.

The second decision is how the artifact activates. Use Run From Package or a slot swap so activation is atomic and the file lock cannot occur, rather than an in-place unpack that fights the running worker for file handles. This closes the file-lock class and the half-activated Linux variant, and it gives you a clean restart as part of activation rather than a deploy that lands but does not take. Pair it with a slot when you want a validation gate and a reversible cutover, which most production apps do.

The third decision is how the deploy authenticates. Use an Entra-based identity, a service principal or a managed identity with a scoped RBAC role on the app, rather than a publish profile and basic authentication. This closes the credential-rejection class, removes the long-lived password from your pipeline, and survives the platform default that turns basic auth off on new apps. When the deploy authenticates with a short-lived token scoped to exactly the app, there is no profile to leak and no toggle to forget.

The fourth decision is how configuration is managed across environments. Mark every environment-bound setting as a slot setting and keep application-bound settings regular, and define both as code so the marking is reviewed rather than remembered. This closes the slot-setting-surprise class, because the swap can no longer move a setting that names the environment. Defining the settings as code, in a Bicep or Terraform definition that names which are sticky, also means a new slot inherits the correct stickiness automatically instead of depending on someone setting it by hand. The infrastructure-as-code habit is what makes the prevention durable rather than a thing that decays the next time someone provisions an app in a hurry. When all four decisions are in place, the deployment-failure table mostly stops applying to you, which is the point of prevention: not to get faster at fixing the failure, but to stop having it.

## Related failures it is often confused with

The single most expensive mistake in this whole area is reading the wrong log because you filed the failure under the wrong category, so it is worth drawing the boundaries between a deployment failure and the failures that look like one but are not.

A 503 Service Unavailable after a deploy is usually not a deployment failure. The deploy succeeded; the app is now failing to serve, which is a startup or capacity problem. A 503 has its own distinct set of causes, including a worker that crashed on startup, a platform recycle, memory pressure, exhausted outbound connections, or a swap in progress, and the way to tell which one is yours is the log stream and the metrics, not the deployment log. If your deploy reported success and the site then returns 503, you have crossed out of deployment and into the territory the [guide on App Service 503 errors](/2022/06/13/fix-app-service-503-error/) covers in full, and reading the deployment log for that answer will waste your time because the deployment log will correctly tell you the deploy worked.

A 500.30 startup error is likewise a post-deploy failure rather than a deployment failure. It means the application host failed to start the app in-process, and the real exception is surfaced through standard output logging rather than the deployment log. A runtime mismatch can cause it, which is the seam where this article and that one touch, but so can a missing connection string, a configuration error, or a dependency the app cannot reach at startup, none of which the deployment log knows anything about. When a clean deploy is followed by a 500.30, the diagnosis moves to surfacing the startup exception, and the dedicated treatment of the [500.30 startup error](/2022/06/20/fix-app-service-500-30-startup-error/) is where that diagnosis lives. The rule that keeps you out of the wrong log is simple: if the deployment log shows success and the failure is in how the app behaves once running, you have a startup problem, not a deployment problem, and the two have different logs and different fixes.

The third confusion is between a failed deploy and a deploy that succeeded but did not appear to take. On Linux in-place deploys and on apps with aggressive caching, the new code can be present but not active until a restart, so the site keeps serving the old version and the engineer concludes the deploy failed when it actually succeeded but did not activate. The tell is that the deployment log is green and the file system shows the new bytes, but the running app serves the old behavior. The fix is activation, a restart or a swap, not a redeploy, and this is one more reason the atomic-activation patterns are worth adopting: they make activation part of the deploy so this ambiguity never arises. When you find yourself unsure whether a deploy took, check the deployment log status and the files on disk before redeploying, because redeploying a deploy that already succeeded just hits the same activation gap again.

## A closer look at the deployment lifecycle

Understanding why these failures happen where they do is easier once you can picture the stages a release moves through, because each failure lives at a specific stage and the stages are more separable than the portal suggests. The lifecycle has four stages, and the deployment log is, in effect, a transcript of them. Reading the log is reading which stage the release reached before it stopped.

The first stage is transport. Your bytes leave your machine or your pipeline and arrive at the platform's deployment engine, the SCM site that runs alongside your app. For a zip deploy the transport is an HTTPS upload of the archive. For Run From Package it is either the same upload or a pointer to a package already in storage. For local Git it is a Git push. For FTP it is a file copy. The transport stage is where credential rejections and timeouts live, because a credential is checked before the bytes are accepted and a timeout is the transport failing to finish. If the log shows the transport never completing, you are at stage one, and the suspects are authentication, network, and size.

The second stage is build, but only if a build is configured to run on the server. With `SCM_DO_BUILD_DURING_DEPLOYMENT` true, the engine hands the transported source to Oryx, which detects the platform, restores dependencies, and produces runnable output. With the setting false, this stage is skipped entirely and the engine treats your package as already runnable. The build stage is where detection errors, restore failures, and compile errors live, and the log at this stage reads like a build log because it is one. If the log shows a build starting and failing, you are at stage two, and the suspect is the build itself: a marker, a feed, a tool version, or the project layout.

The third stage is activation. The engine places the runnable output where the worker will find it. For an in-place deploy that means writing into `wwwroot`, which is the stage where the file lock bites, because the worker is holding handles in that directory. For Run From Package it means mounting the package read-only over `wwwroot`, which is why the lock cannot occur. Activation also includes the worker restart that makes the new code live. If the log shows the output produced but the activation failing on a file in use, you are at stage three with a file lock, and the fix is a method that does not write into the live directory.

The fourth stage is post-activation startup, which is technically past the deployment boundary but is where the consequences of a deploy show up. The worker restarts and tries to run the new code. If the code runs, the release is done. If the code fails to start, you get a 503 or a 500.30, and you have crossed into startup diagnosis. The deployment log considers its job finished once activation succeeds, so a startup failure here will not appear in the deployment log at all, which is the structural reason the wrong-log mistake is so easy to make. The deployment log is a transcript of stages one through three; the application log is the transcript of stage four.

### What is the difference between the deployment log and the application log?

The deployment log records transport, server build, and activation, the stages of getting code onto the platform. The application log records what the running app does once started. A deployment failure appears in the deployment log; a startup or runtime failure appears in the application log and the log stream. Reading the wrong one wastes time.

Holding the four stages in mind turns the deployment log from a wall of text into a map. You scan for the stage that failed, and the stage names the cause family before you have read a single error in detail. Transport failures are credentials, network, and size. Build failures are the build. Activation failures are the file lock and the slot setting. And anything past activation is no longer a deployment failure at all. The reason this framing is worth internalizing is that it survives across every deploy method and every language stack: the methods differ in how they implement each stage, but every method moves through transport, optional build, activation, and startup, so the map applies whether you ship a .NET app through a pipeline or push a Node app over local Git.

## Worked scenarios from real incidents

The abstract causes become concrete when you walk through the patterns engineers actually hit, so here are several composite scenarios drawn from the recurring shapes these failures take, each resolved by the method this guide teaches.

The first is the pipeline that worked on Friday and failed on Monday with nothing changed in the code. The deployment log shows a 401 early, before any upload. The team assumes a platform incident and retries for an hour. The actual cause is that the app was recreated over the weekend as part of an environment refresh, and the new app has basic authentication disabled by default, so the publish-profile-based pipeline step can no longer authenticate. The fix is either to re-enable SCM basic auth on the new app or, better, to move the pipeline step onto the service connection's Entra identity. The lesson is that an early 401 is never transient and never a retry candidate; it is a credential the platform rejected, and the question is which credential and why.

The second is the in-place zip deploy that fails on a specific DLL every single time. The log names the file as in use. The engineer redeploys, redeploys again, and stops the app in frustration, which works but takes the site down. The cause is the file lock, and the durable fix is not the stop-and-start but the switch to a slot deploy or Run From Package, after which the same release that failed five times in a row succeeds on the first attempt because the production worker is no longer holding the file. The lesson is the core rule of the article: a lock that recurs identically is structural, and the answer is a method that does not write into the live directory.

The third is the deploy that reports success and is followed by an app that will not start, returning a 500.30. The team reads the deployment log, finds it green, and concludes the platform is lying. The cause is a runtime mismatch: the package targets one framework major and the worker is pinned to another, so the host cannot load the runtime. The deployment log is correct that the deploy succeeded; the failure is in startup, visible only in the application log once standard output logging is on. The fix is to align the configured stack to the package's target. The lesson is the seam between deployment and startup: a green deploy followed by a failed start is a startup problem, and you read the application log, not the deployment log.

The fourth is the deploy that used to finish in a minute and now times out. No code error, no credential error, just a transport that stalls. The cause is package bloat: a committed dependency directory and a build-output folder crept into the archive, and the package is now ten times its old size. Excluding them with a deploy-ignore file restores the original size and the original speed. When the app genuinely needs a large package, staging it in storage and referencing it through Run From Package removes the operation-window constraint entirely. The lesson is that a transport that newly times out is almost always size, and the first move is to look at what is in the package before blaming the network.

The fifth is the slot swap that looked perfect in staging and broke production. The deploy succeeded, the staging slot ran fine, the swap completed, and production immediately started talking to the staging database. The cause is a connection string left as a regular setting rather than a slot setting, so it swapped into production with the code. The fix is to mark the environment-bound settings sticky and validate both slots' effective configuration before swapping. The lesson is that a swap tests your setting marking, and the time to get the marking right is before the swap, not after production has pointed at the wrong database.

The sixth is the Linux deploy that reports success while the site keeps serving the old code. The deployment log is green, the new files are on disk, and the running app behaves exactly as it did before. The cause is activation rather than transport: the new bytes are present but the worker is still serving the old inode and has not restarted to pick up the change. A restart activates the new code, and adopting Run From Package or a slot swap makes activation part of the deploy so the gap never appears. The lesson is that on Linux a successful in-place deploy is not the same as an active one, and activation deserves its own confirmation.

Each scenario resolves to a row in the deployment-failure table and to one of the four lifecycle stages, which is the point: the surface symptoms vary wildly, but the underlying map is small, and an engineer who has internalized the map reaches the cause in minutes rather than an afternoon. Practicing these patterns against a real app, breaking the deploy on purpose and watching the log boundary that confirms each cause, is the fastest way to make the map automatic, and reproducing them safely in a sandbox is exactly what the troubleshooting drills are built to support.

## Verifying that a deploy actually succeeded

A deploy is not finished when the log turns green; it is finished when the new code is serving and healthy, and the gap between those two states is where the quietest failures hide. Building a verification step into every release closes the activation-gap and runtime-mismatch classes by catching them immediately rather than letting them surface as a user-facing incident an hour later. The verification has two parts: confirming the bytes activated, and confirming the running app is the new version and is healthy.

Confirming activation means checking that the worker is serving the code you shipped, not the previous version. The cheapest reliable way to do this is to ship a version marker the running app can report, an endpoint that returns the build identifier or commit hash baked into the artifact, and to read it after the deploy. If the marker matches what you shipped, the new code is active; if it still reports the old value, you have an activation gap and the fix is a restart or a swap rather than a redeploy. This single check eliminates the entire category of being unsure whether a deploy took, which is otherwise resolved by guessing and redeploying.

```bash
# Restart, wait, then confirm the running app reports the shipped version
az webapp restart --name my-web-app --resource-group my-rg

sleep 20

curl -s "https://my-web-app.azurewebsites.net/version"
```

The version endpoint pattern works on any stack and any deploy method, and it turns activation from an article of faith into a fact you can read. When you deploy through a slot, you run the same check against the slot's hostname before the swap, so you confirm the new code is healthy in staging before it ever reaches production, which is the validation gate that makes the slot pattern worth its extra moving parts.

### How do I confirm the deployed app is healthy before sending it traffic?

Hit a health endpoint on the staging slot before the swap and confirm it returns success and the expected version. App Service can also gate the swap on warm-up by calling a path during the swap, so the platform only routes traffic once the new version answers healthily. Validate in the slot, then swap.

Confirming health means more than a version match; it means the app starts cleanly and answers a real request. The platform's swap warm-up can call a path on the slot during the swap and hold the routing until that path returns success, which means a slot that fails to start never receives production traffic. Configuring that warm-up path ties the swap to the app's own readiness, so the runtime mismatch that would have produced a 500.30 in production instead fails the warm-up in staging, where it is a non-event. This is the mechanism that turns the slot swap from a fast cutover into a safe one, and it is the difference between catching a bad release at the gate and catching it in your incident channel.

Automating the diagnosis itself is the final maturity step. The same log signals you read by hand can be read by a script that classifies a failure into its cause family, so a failed pipeline run can report file lock, build failure, credential rejection, or timeout rather than just failed. A small wrapper around the deployments API that inspects the failing stage and the error string maps most failures to a row in the table without a human opening Kudu, which shrinks the time from failure to fix and makes the knowledge in this guide a property of your pipeline rather than of whoever happens to be on call. The diagnosis does not have to live in an engineer's head once the mapping is clear enough to encode, and encoding it is the natural endpoint of understanding it.

## The verdict on App Service deployment failures

The generic deployment failed message is a screen that hides its meaning, and the engineers who fix it fastest are the ones who never trust the banner and always read the log. Almost every failure in this space resolves to a small set of distinct causes: a running app holding a file lock, an Oryx build failing on the server, a package targeting the wrong runtime, a deploy identity lacking permission, a slot setting swapping when it should have stayed, or a large package timing out. Each has a confirming signal in the deployment log and a tested fix, and the deployment-failure table maps them so you can move from symptom to fix in one glance.

The deeper lesson, the one worth carrying past this article, is that most of these causes are not worth fixing one at a time, because the same two patterns remove most of them structurally. The file-lock-and-package rule, that an in-place deploy can fail on a file lock and that Run From Package or a deploy-to-slot-and-swap removes the lock and the downtime together, is the habit that turns deployment from a fragile step into a routine one. Build the artifact where you can see the build, activate it atomically so the lock cannot occur, authenticate with a scoped identity rather than a password, and pin the environment-bound settings to their slots. Make those four choices once, as code, and the table mostly stops applying to you. That is the difference between an engineer who fixes deploys and one who has stopped having them fail, and the second engineer is not working harder; they are working from a model of what a deploy actually is.

## Frequently Asked Questions

### Q: Why does my App Service deployment fail?

An App Service deployment fails for a small set of distinct reasons, and the deployment log names which one rather than the portal banner. The most common is a file lock: an in-place zip deploy tries to overwrite a file the running worker holds open, and the unpack is refused. Others are a server-side Oryx build error, a package built for a runtime the worker does not provide, a deploy identity that the platform rejects because basic authentication is off or the identity lacks an RBAC role, an environment setting that swapped into the wrong slot, and a package too large to transfer within the operation window. The fix depends entirely on which cause you have, so the first step is always to open the deployment log in the Deployment Center or Kudu and find the stage that failed. Retrying without reading the log usually reproduces the same failure, because most of these causes are structural rather than transient.

### Q: Does a file lock on a running app really block the deployment?

Yes, and it is the defining failure of in-place deploys on App Service. When the worker is running, the runtime loads your binaries and holds their file handles open for the life of the process, so a zip deploy or FTP upload that tries to overwrite those files in `wwwroot` is refused with a file-in-use error, and the deployment log names the file. Retrying does nothing because the same process holds the same handles. On Windows hosting the lock is hard and the deploy aborts; on Linux the replacement may be allowed but the worker keeps serving the old code until it restarts, which is a quieter version of the same problem. The clean resolution is a method that does not write into the live directory: Run From Package mounts the archive read-only so there is nothing to overwrite, and a slot deploy lands in a different worker, so the production handles are never in contention. Either removes the lock entirely rather than scheduling around it.

### Q: How does Run From Package change the way a deployment works?

Run From Package changes activation from an unpack into a mount. Instead of writing your archive into `wwwroot` over the running app, the platform mounts the archive as a read-only file system over `wwwroot`, and the worker restarts to pick it up. Because nothing is written into the live directory, the file-lock failure cannot occur, which is why switching to it resolves the most common deployment failure outright. The activation is atomic, so there is no window where the site is half-old and half-new, and because the package can be referenced from storage by URL, a large package no longer has to transfer through the deploy operation window. The trade-off is that `wwwroot` is now read-only, so an app that writes files next to its binaries will fail and must redirect those writes to a writable path. You enable it by setting `WEBSITE_RUN_FROM_PACKAGE` to point at the package, either a locally uploaded one or a storage URL with a shared access signature, then restarting the app.

### Q: Why does the Oryx build fail on deploy when my project builds locally?

Because the server-side Oryx build runs in a clean environment that lacks your local tooling, caches, global packages, and environment variables. Oryx detects your platform from marker files like `package.json`, `requirements.txt`, or a `.csproj`, restores dependencies from the feeds it can reach, and builds with the tool versions it provides. A missing or misplaced marker makes detection pick the wrong stack or fail. A private dependency feed that your machine authenticates to but the server cannot reach makes the restore fail. A tool or runtime version your machine has but the server does not provide makes the build fail. The reproducible way to diagnose it is to read the exact failing command from the deployment log and run it in a clean container locally, where the gap becomes visible. The more durable fix for any non-trivial app is to stop building on the server by setting `SCM_DO_BUILD_DURING_DEPLOYMENT` to false and to build the artifact in your pipeline, where you control the environment end to end.

### Q: Should I deploy to a slot and swap, or deploy straight to production?

For any app that users touch, deploy to a staging slot and swap into production. The swap is a routing change rather than a redeploy, so it is near-instant, and it is reversible: if the swapped-in version misbehaves, swapping back restores the previous version immediately. Because the deploy lands in the slot's worker rather than the production worker, the production file handles are never in contention, so the file lock cannot occur. The platform warms the slot before routing traffic during the swap, so the first request after the swap does not pay a cold start. Deploying straight to production in place is acceptable only for non-production apps where a brief restart and the file-lock risk are tolerable, because an in-place deploy fights the running worker for file handles and offers no validation gate and no easy rollback. The strongest setup combines a slot with Run From Package, giving you atomic activation, a validation gate, and a reversible cutover at once.

### Q: How do I read App Service deployment logs in Kudu?

Open the Kudu site at your-app.scm.azurewebsites.net, the deployment engine's own administrative surface, where the deployment history, the live log stream, and a file browser all live. The Deployment Center in the portal shows the same deployment list with a status and a timestamp, and clicking a failed entry opens its log. Read the failed attempt's log from top to bottom and find the boundary between the last successful line and the first failing one, because that boundary names the stage that broke. You can also pull the data from a terminal: `az webapp log tail` streams logs live while you watch a deploy fail, and a GET against the Kudu deployments API returns the deployment records as JSON. On a new app with basic authentication disabled, you reach Kudu through your Entra ID sign-in to the portal rather than through publish-profile credentials, which is why automated tooling that expected basic auth cannot reach it until the auth path is corrected.

### Q: Why does my deployment succeed but the new code never appears?

This is an activation gap rather than a transport failure, and it shows up most on Linux in-place deploys and on apps with caching. The deployment log is green and the new files are on disk, but the running worker is still serving the old code because it has not restarted to pick up the change, or a layer is caching the old response. The tell is a successful deployment log plus new bytes in the file system plus old behavior at runtime. The fix is activation, not redeployment: restart the app so the worker loads the new code, and confirm the running behavior changes. Redeploying just repeats the same activation gap. Adopting Run From Package or a slot swap removes the ambiguity entirely, because both make a worker restart part of activation, so the new code goes live as part of the deploy rather than waiting for a separate restart you have to remember.

### Q: Why does my CI/CD pipeline deploy fail when a manual deploy works?

The usual reason is authentication. A manual deploy from your workstation often uses your interactive Entra sign-in, which carries your permissions, while the pipeline uses a service connection, a publish profile, or a federated credential that may not be enabled or authorized. If the pipeline step is publish-profile based and the app has basic authentication disabled, the pipeline gets a 401 while your interactive session sails through. If the pipeline uses an Entra service principal that lacks the RBAC role to publish, it gets a 403 while your account, which has broader rights, succeeds. The deployment log shows the early 401 or 403 that pinpoints which. The fix is to align the pipeline's identity with a supported, authorized path: either enable SCM basic auth for a publish-profile step, or move the step to the service connection's Entra identity and assign it a scoped role on the app. The Entra path is the durable one, because it removes the long-lived password and survives the platform turning basic auth off by default.

### Q: What is the difference between zip deploy, Run From Package, and an Oryx build?

These describe different parts of the deploy, and confusing them sends you to the wrong fix. Zip deploy is a transport-and-activation method: it uploads a zip and unpacks it into `wwwroot`, writing over the live site, which is what exposes it to the file lock. Run From Package is an alternative activation: it mounts the zip read-only over `wwwroot` instead of unpacking it, so nothing is overwritten and the lock cannot occur. The Oryx build is a separate stage that may run inside either method when `SCM_DO_BUILD_DURING_DEPLOYMENT` is true: it turns source into runnable output on the server. So you can do a zip deploy with or without a server build, and you can use Run From Package with a pre-built package and no server build. When a deploy fails, identifying which transport, which activation, and whether a server build ran tells you which failure family you are even able to have, which is why the method matters before the symptom.

### Q: Can disabling SCM basic authentication break my deployment?

Yes, and it is a leading cause of pipelines that suddenly stop working. Basic authentication, the username-and-password publishing credential from the publish profile, is now disabled by default on newly created apps, which is a value to confirm against the current platform behavior because defaults shift. Any deploy path that relies on basic auth, FTP, Web Deploy, and many publish-profile-based pipeline tasks, gets rejected with a 401 on such an app even though the same path worked on an older app where basic auth was on. The fix is either to re-enable the SCM basic publishing policy, accepting the less secure path, or to move the deploy onto an Entra-based identity that authenticates with a short-lived token and holds a scoped RBAC role on the app. The Entra path is the better answer for the long term, because it removes the password from the pipeline and is unaffected by the basic-auth default. When a previously working deploy returns a 401 and nothing in your code changed, the auth default is the first thing to check.

### Q: How do I roll back a bad App Service deployment quickly?

The fastest rollback is a slot swap in reverse. If you deployed by swapping a staging slot into production, swapping again with the slots reversed restores the previous version immediately, because the old version is still running in what is now the staging slot. That is the single strongest reason to deploy through slots: the rollback is built in and takes seconds. If you deployed in place without slots, rollback means redeploying the previous artifact, which is slower and reintroduces the file-lock risk, so keep your last known-good package available to redeploy. App Service also retains deployment history, and you can redeploy a previous deployment from the Deployment Center, which is a usable fallback when you did not use slots. The durable lesson is to build rollback into the deploy architecture rather than improvising it under incident pressure: a slot-based deploy makes rollback a single reverse swap, which is what you want when production is broken and the clock is running.

### Q: Why does my Linux App Service deploy behave differently from Windows?

The two hosting platforms handle file replacement and startup differently, which changes both the failure and the fix. On Windows, the runtime holds hard file locks on loaded assemblies, so an in-place deploy that tries to overwrite them is refused outright, and the deploy aborts naming the locked file. On Linux, the file replacement is often permitted because the holder keeps its inode alive, but the running worker continues serving the old code until it restarts, so you get a deploy that reports success while the site serves stale code. Linux also relies more on a startup command to launch the app, so a deploy can succeed and the app still fail to start if the startup command or output structure is wrong, which straddles the deployment and startup boundary. The unifying fix is the same on both: use an activation method that restarts the worker atomically, Run From Package or a slot swap, so the new code goes live cleanly rather than waiting on the worker's file handles or a separate restart.

### Q: Should I build my app in the pipeline or let Oryx build it on the server?

For anything beyond a trivial app, build in the pipeline and disable the server build by setting `SCM_DO_BUILD_DURING_DEPLOYMENT` to false. A pipeline build runs in an environment you control: you pin the runtime, authenticate to private feeds, manage caches, and read the build log before anything ships, so the build is reproducible and observable. A server-side Oryx build is convenient for getting started but is a black box you can only inspect through a log after it fails, and it runs in a clean environment that lacks your tooling, which is why builds that pass locally fail on the server. The cost of moving the build into the pipeline is that you now own producing an artifact that matches the target runtime exactly, which means pinning the worker's stack to the version you build against. That ownership is a feature, not a burden, because it closes the entire server-build failure class and makes the deploy a fast copy of a ready-to-run package rather than a build that might break.

### Q: Why does my deployment fail or break only after I added a slot-specific setting?

Because settings have two swap behaviors and the one you want depends on what the setting names. A regular application setting travels with the code during a swap, which is correct for anything that is part of the application's definition. A slot setting, marked sticky, stays pinned to its slot and does not move, which is correct for anything that names the environment: the database the slot uses, the storage account, environment-specific flags. When you add an environment-bound setting as a regular setting and then swap, it moves into production along with the code, so production suddenly points at the staging environment, or the reverse. The fix is to mark environment-bound settings as slot settings using the slot-settings option so they stay put, and to validate both slots' effective configuration before swapping. Defining which settings are sticky as code, in your infrastructure definition, makes the marking reviewable and means a new slot inherits the correct behavior instead of depending on someone remembering to set it.

### Q: How do I tell a deployment failure apart from a 503 or a 500.30 after deploy?

Use the log boundary. A deployment failure happens during transport, server build, or activation, and it appears in the deployment log with the stage that broke. A 503 or a 500.30 after a successful deploy is a startup or runtime failure, and it appears in the application log and the log stream, not the deployment log, because the deployment engine considers its job done once activation succeeds. So if the deployment log is green and the site then returns 503 or 500.30, you have a startup problem, and reading the deployment log for the cause will only confirm, correctly, that the deploy worked. A 503 has its own causes around the worker crashing, recycling, memory, or connection exhaustion, and a 500.30 means the application host failed to start in-process with the real exception in standard output. The discipline that saves the most time is to check the deployment log status first: green means look at the application log, red means stay in the deployment log.

### Q: Does the deployment package size have a limit, and what do I do about a timeout?

A deploy can fail on a timeout when the package is too large to transport and activate within the platform's operation window, and the practical limit is best treated as a value to confirm against current platform behavior rather than a fixed number, because it can change. The first move is to look at what is actually in the package, since most bloat is accidental: committed dependency directories, build intermediates, test output, and version-control folders inflate the archive without adding anything the running app needs. A deploy-ignore file or an explicit include list trims it to the runnable output and often shrinks it dramatically, which restores the transfer speed and clears the timeout. When the app legitimately needs a large package, stop pushing the bytes through the deploy transport and instead upload the package to a storage account and reference it through Run From Package by URL. The storage upload is a separate, resumable operation outside the deploy operation window, and the activation becomes a mount rather than an unpack, which removes the timeout and the file lock at the same time.

### Q: Why does my deployment return a 409 conflict?

A 409 during a deploy signals that another operation on the same app is in progress, so the platform refuses to start a conflicting one. A scaling operation, a configuration change, a slot swap, or a previous deploy that has not finished can all hold the app in a state where a new deploy conflicts. The fix is to serialize, not to retry into the conflict: wait for the in-flight operation to finish, then deploy, rather than firing a second deploy that races the first. In a pipeline, this often means ensuring two deploy jobs cannot target the same app concurrently, which a concurrency control on the pipeline stage enforces. If the conflict persists with no obvious concurrent operation, check whether a resource lock or a stuck previous deployment is holding the app, and clear that before deploying. The principle matches conflict handling elsewhere on the platform: a 409 is a serialization signal, and the answer is to order the operations rather than to retry them into the same race.

### Q: Can I deploy to App Service entirely from infrastructure as code?

Yes, and making the deploy reproducible as code is the prevention strategy that closes most of the failure classes at once. The app, its runtime stack, its application and slot settings, and its deploy identity can all be defined in Bicep or Terraform, which means the runtime is pinned rather than drifting, the environment-bound settings are marked sticky in the definition rather than by hand, and the deploy identity holds a scoped role granted in the same template. The artifact itself is then shipped by a pipeline step that uses an Entra identity and Run From Package or a slot swap. Defining the configuration as code makes the marking reviewable in a pull request, means a freshly provisioned slot inherits the correct settings automatically, and removes the class of failures that come from someone configuring an app in a hurry and forgetting a sticky setting or a runtime pin. The build runs in the pipeline, the activation is atomic, the identity is scoped, and the configuration is reviewed, which is the four-decision architecture that makes the deployment-failure table stop applying to you.

### Q: What permissions does the deploy identity actually need?

It needs the right to publish to the specific app, granted at the app's scope rather than over a broad subscription scope. For an Entra-based deploy, that means a managed identity or service principal with an RBAC role that includes the publish action on the app, assigned at the resource scope so the identity can deploy to that app and nothing more. Avoid the reflex of assigning a broad role like Owner across the subscription to make a 403 go away, because that grants far more than a deploy needs and turns a deployment credential into a standing risk. If the identity authenticated but still gets a 403, the role is missing or scoped wrong, and freshly assigned roles take a short time to propagate, so a brief 403 right after assignment can mean the role simply has not landed yet rather than that it is incorrect. Separate the two questions cleanly: a 401 is authentication, the identity was not recognized, and a 403 is authorization, the identity was recognized but lacks the right. Fix the one the log actually shows.
