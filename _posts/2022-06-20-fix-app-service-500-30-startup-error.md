---
layout: post
title: "Fix App Service 500.30 Startup Error"
page_title: "Fix App Service HTTP 500.30 ASP.NET Core Startup Error: Diagnose 500.30, 500.31, and 500.32 with stdout Logging"
date: 2022-06-20
categories: ["Technology"]
tags: ["Azure", "App Service", "500.30", "ASP.NET Core", "Troubleshooting", "Cloud Computing"]
excerpt: "App Service 500.30 is an in-process startup failure that hides its real exception. Enable stdout logging, read the cause, and fix it without redeploying."
image: "/assets/images/blog/blog-01.webp"
reading_time: 43
author: "Insight Crunch Team"
last_updated: 2022-06-20
---

An HTTP 500.30 on Azure App Service is one of the most misread responses in the whole platform, because the page it produces tells you almost nothing and the instinct it triggers is almost always wrong. The status reads "HTTP Error 500.30 - ASP.NET Core app failed to start," and that single line is the entire message most engineers ever see. It looks like a server fault, so the reflex is to restart the site, or worse, to redeploy and wait. Neither helps, because a 500.30 is not a request that went sideways. It is the application host reporting that your process never finished starting, and until you make the real startup exception visible, every restart simply reproduces the same crash a few seconds later.

![Diagnosing an Azure App Service 500.30 ASP.NET Core startup failure with stdout logging - Insight Crunch](/assets/images/blog/blog-01.webp)

This guide treats the 500.30 the way a senior engineer mid-incident would: as a signal that points at a deterministic failure during process initialization, not as a flaky symptom to ride out. By the end you will hold a clear model of what the 500.3x family of codes actually reports, a reliable method for surfacing the hidden exception behind the generic page, a mapped set of distinct root causes with the confirming check and the tested fix for each, and the prevention that keeps the failure from recurring after the next deploy. The thesis running through all of it is simple and worth stating plainly: the generic page never names the cause, so the first action is always to read the startup exception, never to redeploy.

## What HTTP 500.30 Actually Means on App Service

The 500.30 belongs to the ASP.NET Core Module, the native component that sits in the web server and launches your managed process. The module is usually shortened to ANCM, and the 500.30 is its way of saying that it tried to start your application and the process exited or failed before it signaled readiness. The crucial distinction, the one that reframes the entire investigation, is that this is a startup-phase failure and not a request-handling failure. No controller ran. No middleware executed. The host builder threw, or the runtime could not load, and the worker never reached the point where it could accept a single request.

That distinction governs everything that follows. A request-time error, a 500 with no sub-code, means your code ran and threw while serving traffic, so the answer lives in your application logs and your telemetry. A 500.30 means the answer lives earlier, in whatever happened between the platform handing control to your process and your process announcing that it was alive. Because the host never came up, the framework had no chance to write a friendly error page, so the web server falls back to the bare module text. The emptiness of that page is not a bug. It is a direct consequence of failing before the part of your stack that knows how to describe failures.

### Why does a 500.30 show no useful detail?

A 500.30 shows no detail because the failure happens before your application's logging and error-handling middleware are wired up, so nothing in your code is positioned to capture or render the exception. The ASP.NET Core Module reports only that the process did not start. The real message exists, but it went to the process's standard output stream, which is discarded by default until you explicitly redirect it.

That single fact is the hinge of the whole diagnosis. The exception that crashed your startup is real, it is specific, and it is almost always sitting in the standard output stream of the failed process, unread. The platform does not throw that stream away to spite you; it simply does not persist transient process output unless you ask it to. The moment you ask, the generic 500.30 turns into a precise stack trace that names the missing setting, the wrong framework version, or the dependency that would not load. The skill that resolves a 500.30 quickly is not guessing at causes. It is knowing how to turn that hidden stream back on.

### Is a 500.30 the same as a 502 or a 503?

No. A 502 means the worker accepted the connection and then returned a malformed or no response, while a 503 means no healthy worker was available to take the request at all. A 500.30 is narrower and more specific: a worker exists, the module tried to launch your process inside it, and your process failed during initialization. The three look similar from a browser, but they point at different layers and demand different first steps.

Keeping these apart saves real time. If you chase a 500.30 as though it were a 503, you start scaling out, checking instance health, and looking at SNAT ports, none of which touch the actual problem. The App Service 503 has its own distinct set of causes around worker availability and capacity, and the diagnosis for it runs through the log stream and the metrics blade rather than through startup output. Treat the sub-code as a routing label: the .30 suffix sends you to process startup, full stop.

## The InsightCrunch 500.3x Decoder

Before walking the causes, it helps to fix the whole family in one place, because the suffix after 500 tells you which stage of startup broke and therefore where to look first. This decoder is the findable artifact of this guide; commit it to memory and most of the diagnosis collapses into reading one digit.

| Sub-code | What the module reports | What actually failed | First diagnostic step |
| --- | --- | --- | --- |
| 500.30 | In-process start failure | Your process launched but threw or exited during host startup | Enable stdout logging and read the startup exception |
| 500.31 | Failed to load the runtime | The requested .NET runtime version is not present on the instance | Confirm the target framework against the runtime available on the plan |
| 500.32 | Failed to load coreclr or the framework | The bitness, framework, or a self-contained binary set does not match the host | Check the publish bitness, the framework reference, and the deployment type |
| 500.33 | Failed to read the configuration file | The web.config or the module configuration could not be parsed | Inspect the generated web.config and the handler path |
| 500.34 | Mixed hosting models | A process attempted both in-process and out-of-process hosting | Pick one hosting model and align web.config and the project setting |
| 500.35 | Multiple in-process apps in one pool | More than one in-process app shares a single worker | Isolate each app to its own application pool or plan |
| 500.36 | Out-of-process handler missing | The out-of-process request handler is absent | Confirm the module and handler are installed and referenced |
| 500.37 | Startup time limit exceeded | The process did not signal readiness within the allowed window | Speed up startup or raise the startup time limit |
| 500.38 | Could not find the application | The module could not locate the app to launch | Verify the process path and the published output |

The pattern is consistent across the suffixes. The .30 is your own initialization code failing. The .31 and .32 are the runtime or framework not matching what you shipped. The .33 through .38 are configuration and hosting-model mismatches that the build or the deploy introduced. Reading the suffix first tells you which of these neighborhoods to search, and that alone removes most of the guesswork that makes a 500.30 feel intractable.

## Inside the ASP.NET Core Module

To diagnose a 500.30 with confidence rather than recipe-following, it pays to understand the component reporting it. The ASP.NET Core Module is a native web-server module that bridges the managed world of your application and the unmanaged world of the host that fronts it. On a Windows plan that host is IIS; on a Linux plan an equivalent reverse proxy sits in front of the same managed runtime inside the container. The module's job is to receive an incoming request, ensure your application process is running, and forward the request to it, and the 500.3x codes are the module's vocabulary for the ways that handoff can break.

The module operates in one of two modes, and which one you use changes what a startup failure looks like. In the in-process mode the module loads the .NET runtime directly into the web-server worker and runs your application inside that same process, so there is no second process and no network hop between the server and your code. This is the faster arrangement and the modern default, but it means a startup crash brings down the worker itself, which is why an in-process 500.30 gives you no separate process to attach to or inspect. In the out-of-process mode the module launches a child dotnet process, your application listens on a local port, and the module proxies requests to it over loopback. A startup crash there kills the child process while the worker survives, which can make the failure slightly easier to isolate at the cost of the proxy overhead on every request.

### What does the module do during startup?

During startup the module reads its configuration, locates the runtime and your application binary, launches or loads the process, and waits for the application to signal that it is listening and ready. Each of those steps maps to a sub-code: configuration that will not parse is a 500.33, a runtime it cannot find is a 500.31, a framework it cannot load is a 500.32, an application it cannot locate is a 500.38, and a process that launches but throws before signaling readiness is the 500.30. Reading the sub-code is, in effect, reading which step of the module's own sequence failed.

This sequence is why the surfacing technique works the way it does. The module hands control to your process and then watches for a readiness signal. Anything your process writes to standard output during that window, including the exception that crashes it, flows to the stream the module can capture but does not persist by default. Enabling stdout redirection, or relying on the container's automatic capture on Linux, simply tells the system to keep that window's output instead of discarding it. You are not adding new information; you are preserving information the module already had and threw away. Understanding the handoff this way removes the temptation to treat the 500.30 as random, because you can see that the failure sits at a specific, repeatable point in a deterministic sequence, and that the cause is always recoverable from the output of that exact step.

## How to Surface the Hidden Exception

Everything in this section serves one goal: make the standard output of the failed process visible so the real exception stops hiding behind the generic page. There are several routes to it, and the right one depends on whether the app runs on a Windows plan or a Linux plan, since the two host ASP.NET Core through different mechanisms.

### How do I see the real exception behind a 500.30?

Enable stdout logging by setting the module to redirect standard output to a file, then read that file. On a Windows plan this means flipping the stdout redirect in the generated web.config and reading the log under the LogFiles path through Kudu. On a Linux plan the container already writes startup output to the log stream, so you tail the stream directly. Either way you are reading the same thing: the exception thrown during host startup.

On a Windows App Service, the published web.config contains an `aspNetCore` element whose `stdoutLogEnabled` attribute defaults to false. The cleanest way to flip it without redeploying is through the Kudu console, which gives you a shell on the instance. Open the advanced tools, drop into the site's `wwwroot`, and edit the file in place:

```bash
# In the Kudu (Advanced Tools) Debug console, on a Windows App Service
cd /home/site/wwwroot
# View the current module configuration
type web.config
```

You are looking for a line shaped like this, and you want to change two attributes:

```xml
<aspNetCore processPath="dotnet"
            arguments=".\YourApp.dll"
            stdoutLogEnabled="true"
            stdoutLogFile=".\..\..\LogFiles\stdout"
            hostingModel="inprocess" />
```

Set `stdoutLogEnabled` to `true` and point `stdoutLogFile` at a path under `LogFiles`, because that directory persists and is reachable from Kudu. Save the file, restart the app once so the module re-reads the configuration, and then trigger the failure by loading the site. The module writes a timestamped file under `/home/LogFiles/stdout`, and that file holds the stack trace you have been missing:

```bash
# Back in the Kudu console after reproducing the failure
cd /home/LogFiles
# List the stdout capture files, newest last
dir stdout*
# Read the most recent one
type stdout_<timestamp>.log
```

The result is the difference between "ASP.NET Core app failed to start" and a precise message such as `System.InvalidOperationException: Unable to resolve service for type 'IMyRepository' while attempting to activate 'StartupFilter'`, or `System.IO.FileNotFoundException: Could not load file or assembly`. That is the cause, named. Turn the redirect off again once you have read it, because a permanently enabled stdout log on a Windows plan grows without bound and was only ever meant for short diagnostic windows.

### Reading the exception on a Linux plan

On a Linux App Service the model is different and, in practice, friendlier. Your app runs inside a container, and the container's standard output is captured by the platform automatically, so you do not edit web.config. Instead you read the log stream, which carries the same startup exception in near real time:

```bash
# Stream the container's startup output live with the Azure CLI
az webapp log tail \
  --name <app-name> \
  --resource-group <resource-group>
```

Reproduce the failure with the stream open and the exception scrolls past as the container tries and fails to start. If you prefer a file you can scroll, the same output is written under `/home/LogFiles` and is reachable through the SSH session that Linux plans expose:

```bash
# Open an SSH session into the running Linux container, then
cd /home/LogFiles
ls -lt
# Inspect the most recent container log
cat <newest-log-file>
```

A frequent Linux-specific signature is a managed exception wrapped around a native loader message, where the framework started but a native dependency the app relies on is absent from the slim base image. Recognizing that the trace names a `.so` library, rather than a managed type, immediately tells you the fix lives in the image and not in your configuration.

### Using the Application Event Log and diagnostics

There is a third source worth knowing, because it sometimes captures detail the stdout file misses, particularly when the process dies so early that it never opens its own output. On Windows plans the ANCM writes startup failures to the Application Event Log, which you can read through the diagnostic tooling in the portal or through Kudu's process explorer. The relevant `ASPNETCORE` environment diagnostics, especially `ASPNETCORE_DETAILEDERRORS` set to `true` and `ASPNETCORE_ENVIRONMENT` set to `Development` for a controlled diagnostic window, can also coax a richer page out of the framework once it gets far enough to render one. Use the development setting only briefly and only when you control who can reach the site, since detailed errors expose internals you would not want public.

## The Distinct Root Causes of a 500.30

With the exception visible, the investigation turns from guessing to matching. Almost every 500.30 reduces to one of a handful of root causes, and the stack trace you surfaced points directly at which one is yours. The next sections take them one at a time, each with the way to confirm it and the fix that resolves it.

### Cause one: an unhandled exception in startup

The most common 500.30 is an exception thrown inside the host builder or the startup configuration, before the request pipeline is ever ready. A service registration that cannot be satisfied, a configuration binding that fails because a required value is absent, a database context whose connection is evaluated eagerly at build time, or an `IStartupFilter` that throws, all surface here. The application code is not wrong in the sense of a logic bug; it is throwing during the one window where nothing is positioned to catch it.

You confirm this cause by reading the surfaced exception and seeing a managed type from your own code or from a framework service in the trace. A line such as `Unable to resolve service for type` or `Value cannot be null. (Parameter 'connectionString')` names it outright. The fix is to make startup defensive: register the missing dependency, supply the missing configuration, and defer any work that does not need to run at build time. A connection that is opened lazily, on first use, rather than eagerly during `ConfigureServices`, keeps a transient backend hiccup from becoming a hard startup crash:

```csharp
// Eager resolution during startup turns a missing value into a 500.30.
// Bind options and defer the actual work to first use instead.
builder.Services.AddOptions<DatabaseOptions>()
    .Bind(builder.Configuration.GetSection("Database"))
    .Validate(o => !string.IsNullOrEmpty(o.ConnectionString),
              "Database:ConnectionString is required")
    .ValidateOnStart();
```

The `ValidateOnStart` call is deliberately included even though it can cause a controlled startup failure, because a failure with a clear validation message in the stdout log is far better than a `NullReferenceException` thrown deep in a constructor three layers down. You are trading an opaque crash for a labeled one.

### Cause two: a missing configuration value or connection string

A close relative of the first cause, and common enough to treat on its own, is a configuration value that exists in your local development environment but was never set in App Service. The classic version is a connection string or an API key that lives in `appsettings.Development.json` or in user secrets on your machine, neither of which travels to the cloud. The app binds the value during startup, finds nothing, and throws.

#### Does a missing connection string cause a 500.30 startup error?

Yes, very often. If your startup code reads a connection string or a required setting and then uses it immediately, for example by configuring a database context or a cache client during service registration, an absent value throws before the host is built and produces a 500.30. The fix is to set the value in the App Service application settings or, better, to source it from Key Vault, and to validate its presence at startup so the failure names itself.

App Service surfaces application settings and connection strings to your process as environment variables, so the fix is to place the value where the platform will inject it. The portal has a Configuration blade for this, and the same change is one CLI command:

```bash
# Set an application setting that becomes an environment variable in the process
az webapp config appsettings set \
  --name <app-name> \
  --resource-group <resource-group> \
  --settings "Database__ConnectionString=<your-connection-string>"
```

Note the double underscore in `Database__ConnectionString`. App Service translates that into the hierarchical key `Database:ConnectionString` that the configuration system expects, which is the bridge between flat environment variables and nested settings. For connection strings specifically, the dedicated connection-strings collection is available and carries a type, but for most modern apps an application setting with the double-underscore convention is the simpler and more predictable choice. The durable improvement, rather than pasting secrets into settings, is to reference a Key Vault secret so the value is centralized and rotatable, a pattern worth wiring in once and reusing across every app you run.

### Cause three: a runtime or framework version mismatch

This is the cause that masquerades as the others and wastes the most time, because the app runs perfectly on your machine and dies only in the cloud. You built and published against one version of the .NET runtime, and the App Service plan offers a different one. When the gap is in the major runtime, the module cannot load the framework your app references and you get a 500.31 or 500.32; when the framework loads but a version-specific behavior trips initialization, you can land on a 500.30. A runtime-version mismatch is one of the most frequent root causes behind this whole family, which is exactly why the decoder above puts version checking near the top.

#### Can a runtime version mismatch cause a 500.30?

Yes. If you publish a framework-dependent app that targets a runtime the plan does not have, the host cannot load the framework and the start fails. Depending on which stage breaks, the surface code is a 500.30, a 500.31, or a 500.32. The confirming check is to compare your project's target framework against the runtime configured on the App Service, and the fix is to align them, either by setting the stack version on the plan or by publishing self-contained so the app carries its own runtime.

Confirm it by reading two things. First, the target framework in your project file. Second, the runtime stack the App Service is set to serve:

```bash
# Show the configured runtime stack for the app
az webapp config show \
  --name <app-name> \
  --resource-group <resource-group> \
  --query "{windowsFxVersion:windowsFxVersion, linuxFxVersion:linuxFxVersion, netFrameworkVersion:netFrameworkVersion}"
```

If your project targets a framework newer than the stack the plan reports, the host is being asked to run a binary it cannot load. The straightforward fix on a Linux plan is to set the stack to match:

```bash
# Align the Linux runtime stack with the framework the app targets
az webapp config set \
  --name <app-name> \
  --resource-group <resource-group> \
  --linux-fx-version "DOTNETCORE|8.0"
```

The alternative, when you cannot or do not want to depend on the plan's installed runtime, is to publish a self-contained deployment that bundles the runtime with the app. That removes the dependency on what the plan offers, at the cost of a larger artifact, and it is the more robust choice when you need to pin an exact patch version regardless of what the platform rolls out underneath you.

### Cause four: a missing native dependency on Linux

A 500.30 that appears only on a Linux plan, with a trace that mentions a shared object or a `DllNotFoundException`, usually means your app calls into a native library that the base container image does not include. Image processing libraries, certain cryptography or compression bindings, and globalization data are the recurring culprits. The managed code is fine; the native layer it sits on is missing.

You confirm it by spotting the native signature in the surfaced exception: a reference to a `.so` file, an `Unable to load shared library` message, or a globalization failure complaining that ICU is absent. The fix is to add the dependency to the image. When you control a custom container you install the package in the Dockerfile; when you run on the built-in Linux stack you either switch to a managed alternative that needs no native dependency or, for the specific and common case of globalization, opt into invariant mode so the app does not require the missing ICU data:

```json
// In the .csproj or runtimeconfig, opt into globalization-invariant mode
// only when your app does not need culture-specific formatting.
{
  "configProperties": {
    "System.Globalization.Invariant": true
  }
}
```

Invariant mode is a deliberate trade, not a default to reach for blindly. It removes culture-specific formatting and comparison, which is fine for many APIs and wrong for anything that formats currency or dates for humans. Reach for it only when you have confirmed the app does not depend on culture data; otherwise install the dependency the proper way.

### Cause five: an in-process versus out-of-process hosting mismatch

The Windows hosting model decides whether your app runs inside the web server worker process, called in-process, or in a separate dotnet process that the worker proxies to, called out-of-process. The model is recorded in the project and reflected in the generated web.config, and when the two disagree, or when the deployed web.config names a model the platform cannot honor, you get a startup failure that often surfaces as a 500.30 with a hosting-model flavor, or as one of the dedicated codes 500.34 through 500.36.

#### How does the in-process hosting model relate to 500.30?

In-process hosting runs your app directly inside the IIS worker, which is faster but means a startup exception takes the worker down and reports as a 500.30 with no separate process to inspect. Out-of-process runs a child dotnet process that the worker forwards to. A 500.30 tied to the model usually means the web.config's `hostingModel` attribute and the project's `AspNetCoreHostingModel` setting disagree, or that two in-process apps are sharing one pool. Align the setting and the config, and give each in-process app its own worker.

The confirming check is to read the `hostingModel` attribute in the deployed web.config and compare it against the `AspNetCoreHostingModel` property in your project. The fix is to make them agree and to redeploy so the generated config is regenerated cleanly rather than hand-edited:

```xml
<!-- Pick one model and let publish generate the matching web.config -->
<PropertyGroup>
  <AspNetCoreHostingModel>InProcess</AspNetCoreHostingModel>
</PropertyGroup>
```

In-process is the default and the faster path for most web workloads, since it removes the proxy hop. Out-of-process is the right choice when you need the app to run in its own process for isolation or when something about your stack does not cooperate with the in-process model. The error to avoid is editing the deployed web.config by hand to flip the model, which drifts the running site away from what your project produces and guarantees the mismatch returns on the next deploy.

## Resolving the Less Common Sub-codes

The 500.30 is the headline, but the same investigation method resolves its quieter siblings, and recognizing them saves you from misdiagnosing a configuration or hosting problem as an application crash. Each sub-code names a different broken step in the module's startup sequence, and each has a confirming check and a fix that follows from where it sits.

A 500.31 means the module could not load the requested runtime, which almost always means the .NET version your app targets is not installed on the instance. Confirm it by comparing your target framework against the runtime the plan reports, the same check used for the version-mismatch root cause, and fix it by aligning the plan's stack or publishing self-contained. A 500.32 means the framework or coreclr would not load, which usually traces to a bitness mismatch, where a binary built for one architecture meets a host expecting another, or to a self-contained publish whose runtime identifier does not match the instance. Confirm the publish architecture and the runtime identifier, and republish for the correct target.

A 500.33 is the module failing to read its configuration file, meaning the generated `web.config` is malformed or unparseable. The fix is never to hand-repair it but to let `dotnet publish` regenerate it from your project, because a hand-edited config drifts from the binaries and reintroduces the problem on the next deploy. A 500.34 reports a mixed hosting model, where a process attempted both in-process and out-of-process hosting at once, which is resolved by choosing one model in the project and republishing. A 500.35 reports multiple in-process applications sharing a single worker, which the in-process model forbids because only one application can own a worker; the fix is to isolate each in-process app in its own application pool or its own plan.

### Which sub-code means the app could not be found?

A 500.38 means the module could not locate the application to launch, typically because the process path in the generated `web.config` points at a binary that is not where the config expects it, or because the published output is incomplete. Confirm it by listing the deployed `wwwroot` and checking that the application DLL named in the `arguments` attribute is actually present, then republish a complete output so the path and the binary agree.

A 500.36 reports a missing out-of-process request handler, which appears when an app configured for out-of-process hosting lands on a host where the handler component is absent or unreferenced; aligning the hosting model and ensuring the handler is part of the deployment resolves it. A 500.37, covered earlier, is the startup time limit exceeded, where the process launched correctly but did not signal readiness in time. The thread through all of them is the same as for the 500.30: the sub-code tells you which step broke, the surfaced output or the deployed configuration confirms it, and the fix follows from the step rather than from guesswork. None of these is mysterious once you read the code as a map of the module's own sequence.

## A Worked Reproduction: Breaking and Fixing a 500.30

Reading about the causes is one thing; watching the failure appear and disappear under your own hands is what makes the method stick. The following walkthrough reproduces the most common 500.30, a missing required setting, end to end, so the loop of surface, match, and fix becomes concrete. Start from a minimal API that reads a required value during startup:

```csharp
var builder = WebApplication.CreateBuilder(args);

// This throws during startup if the value is absent, producing a 500.30.
var apiKey = builder.Configuration["Downstream:ApiKey"]
    ?? throw new InvalidOperationException(
        "Downstream:ApiKey is required and was not configured.");

builder.Services.AddSingleton(new DownstreamClient(apiKey));
var app = builder.Build();
app.MapGet("/", () => "alive");
app.Run();
```

On your machine the value sits in user secrets, so the app starts and serves. Publish it to a fresh App Service without setting `Downstream__ApiKey`, browse to the site, and the response is the bare 500.30 page. Nothing in the portal's overview blade explains why. Now run the surfacing step. On a Linux plan, tail the stream while you reload:

```bash
az webapp log tail --name <app-name> --resource-group <resource-group>
```

The output names the cause directly, something close to `Unhandled exception. System.InvalidOperationException: Downstream:ApiKey is required and was not configured.` followed by a stack trace through the host builder. That message is the entire diagnosis. Apply the fix by setting the value where the platform injects it into the process environment:

```bash
az webapp config appsettings set \
  --name <app-name> \
  --resource-group <resource-group> \
  --settings "Downstream__ApiKey=<the-real-key>"
```

Setting an application setting restarts the app automatically, so the corrected process starts cleanly and the site returns `alive`. You changed one setting, never touched the code, and never redeployed. That is the shape of every 500.30 resolution: the surfaced exception turned an opaque page into a one-line instruction, and the fix followed from reading it rather than from guessing. The same loop applies whether the surfaced message names a missing setting, a service that would not resolve, a runtime that would not load, or a library that was not present. Surface, read, match, fix.

## Linux Container Startup in Depth

Linux App Service deserves its own treatment, because when you bring a custom container the surface area for a startup failure widens, and a 500.30-shaped failure can come from the container never reaching the port the platform expects rather than from a managed exception at all. The platform starts your container, waits for it to respond on the port it believes the app listens on, and if the container does not answer within the container start window, the platform reports a startup failure that reads much like an in-process crash from the browser.

### Why does my custom container fail to start with a 500.30-style error?

A custom Linux container usually fails to start for one of three reasons: it listens on a port the platform is not probing, it takes longer to become ready than the container start time limit allows, or its entrypoint exits because of a missing dependency or a bad command. The platform expects your app to listen on the port named by the `WEBSITES_PORT` setting, defaulting to 80 when unset, so a container that binds a different port never answers the readiness probe. Confirm the listening port from the container logs, set `WEBSITES_PORT` to match, and verify the entrypoint runs cleanly by reading the same log stream.

The fix usually starts with making the port explicit and observable. App Service probes the port your container declares, and a mismatch between that and where your application actually binds is the most frequent custom-container start failure:

```bash
# Tell the platform exactly which port the container listens on
az webapp config appsettings set \
  --name <app-name> \
  --resource-group <resource-group> \
  --settings "WEBSITES_PORT=8080"
```

For an ASP.NET Core app in a container, bind to that port explicitly in the entrypoint so there is no ambiguity, using the `ASPNETCORE_URLS` value the framework reads:

```dockerfile
# In the Dockerfile, make the listening port unambiguous
ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080
ENTRYPOINT ["dotnet", "YourApp.dll"]
```

The second container-specific failure is a slow start that exceeds the platform's patience. A container that pulls a large image, runs migrations, or warms a cache before listening can blow past the start window. The setting `WEBSITES_CONTAINER_START_TIME_LIMIT` raises that window when the work genuinely cannot be shortened, though the better engineering answer is to start listening quickly and do the heavy work in the background once the readiness probe is satisfied. The third failure is the simplest: the entrypoint command exits, often because a dependency the image was supposed to include is absent, and the log stream shows the exit directly. In every case the diagnostic move is identical to the in-process one, reading the captured container output, which is why the surfacing skill transfers cleanly from Windows to Linux.

## Sourcing Secrets from Key Vault Without Embedding Them

Because a missing setting is such a common 500.30 trigger, and because pasting secrets into application settings is a habit worth retiring, the durable improvement is to source sensitive configuration from Key Vault through a reference the platform resolves at startup. The app never holds the secret; it holds a pointer, and the platform's managed identity reads the actual value when the process starts.

Wire it once and the pattern repeats across every app. Give the App Service a managed identity, grant that identity read access to the vault's secrets, and then set the application setting to a Key Vault reference rather than a literal value:

```bash
# Grant the app's managed identity the right to read secrets, then
# set the application setting to a Key Vault reference expression.
az webapp config appsettings set \
  --name <app-name> \
  --resource-group <resource-group> \
  --settings 'Downstream__ApiKey=@Microsoft.KeyVault(SecretUri=https://<vault>.vault.azure.net/secrets/downstream-api-key/)'
```

When the process starts, App Service resolves the reference and injects the resolved value as the environment variable your code reads, exactly as a literal setting would. The advantage for startup reliability is twofold: the secret is centralized and rotatable without redeploying, and a resolution failure surfaces in the platform's own diagnostics with a clear message about the reference rather than as a silent null deep in your code. The one new failure mode this introduces, a reference that cannot resolve because the identity lacks access or the secret name is wrong, also names itself plainly, so it fits the same surface-and-read method as every other cause in this guide.

## Deploying Through a Staging Slot So a 500.30 Never Reaches Users

The single most effective prevention for a production 500.30 is to never let a fresh build start in production at all. App Service deployment slots give you a separate, fully running copy of the app that shares the plan, and the workflow built around them turns a startup failure into a contained, observable event on the slot rather than an outage on the live site.

The mechanics are straightforward. Deploy the new build to a staging slot, watch it start, confirm it serves traffic, and only then swap it into production. If the build carries a 500.30, the failure appears on the staging slot while production keeps serving the previous, healthy build untouched:

```bash
# Create a staging slot, deploy to it, then swap once it is verified healthy
az webapp deployment slot create \
  --name <app-name> \
  --resource-group <resource-group> \
  --slot staging

# After deploying the new build to the staging slot and confirming it starts,
# swap it into production
az webapp deployment slot swap \
  --name <app-name> \
  --resource-group <resource-group> \
  --slot staging \
  --target-slot production
```

The swap carries a second benefit beyond catching the failure. During a swap App Service warms the staging instance by sending it startup requests before routing live traffic to it, so the instance that becomes production has already passed the startup window where a 500.30 lives. A site that swaps in a warmed, verified slot effectively cannot present a startup failure to a real user, because any such failure was caught on the slot before the swap completed. Combined with attached telemetry that captures the exception automatically, slot-based deployment is the difference between learning about a 500.30 from an angry alert and never having it reach production traffic in the first place. This is the same disciplined delivery posture that underpins reliable App Service operations generally, and it costs only the minutes it takes to verify a slot before swapping.

## The Counter-Reading: Why Redeploying Does Not Work

There is a tempting and almost universal wrong move worth naming directly, because it feels like progress and is the single biggest reason a 500.30 drags on. The instinct, when a deploy comes up with a 500.30, is to redeploy, then restart, then redeploy again, on the theory that something transient went wrong and another push will shake it loose. It will not, and understanding why is part of holding the right model.

A 500.30 from a startup exception is deterministic. The same code, the same configuration, and the same runtime produce the same crash every single time the process launches, because nothing about the failure depends on timing or load or which instance you land on. Redeploying the identical artifact into the identical configuration reproduces the identical exception. The only thing that changes is the timestamp on a new failed start. This is the difference between a 500.30 and a genuinely transient availability blip, which a restart can sometimes clear: the startup failure is a property of what you shipped, not of the platform's mood. Surface the exception, fix the cause it names, and then deploy the corrected artifact once. That is the whole loop, and it is far shorter than the redeploy-and-pray cycle it replaces.

## Prevention: Stop the 500.30 Before It Ships

Resolving a 500.30 in production is satisfying, but the better outcome is never seeing it from a deploy at all. A handful of habits move the failure from a production incident to a build-time or staging catch.

The first is validating configuration at startup with clear messages, the `ValidateOnStart` pattern shown earlier, so that a missing setting fails with a labeled message in a place you check rather than a raw exception in production. The second is pinning the runtime explicitly, either by aligning the plan's stack to your target framework as a deliberate, version-controlled setting or by publishing self-contained so the artifact is independent of the plan. The third, and the one that catches the most, is deploying to a staging slot first. App Service slots let you push the new build to a slot, watch it start, confirm it serves traffic, and only then swap it into production, so a startup failure surfaces on the slot and never touches live users. The slot swap also warms the worker, so the swapped-in instance is already past the startup window that a 500.30 lives in.

The fourth habit is wiring in observability that captures startup, not just requests. Application Insights, attached to the app, records the failed start and the exception even when the stdout file is not enabled, giving you a second always-on source for the cause. The combination of slot-based deploys and attached telemetry means that when a 500.30 does appear, you learn about it on a slot with the exception already captured, which turns the entire diagnosis from an outage into a non-event. These prevention habits are exactly the kind of repeatable safety that the broader App Service deployment story is built around, and they compound: each one shrinks the window in which a startup failure can reach a real user.

## Related Failures the 500.30 Is Confused With

Part of diagnosing a 500.30 well is knowing what it is not, because several other failures look identical from the browser and send you down the wrong path if you misread them. The 503 Service Unavailable is the most common confusion: it means no healthy worker took the request, which is a capacity or worker-availability problem rather than a startup problem, and it has its own distinct family of causes around recycling, memory pressure, and connection exhaustion. A plain 500 with no sub-code means your code ran and threw while handling a request, so the answer is in your application logs and telemetry, not in startup output. A deploy that never completes, as opposed to one that completes and then fails to start, is a deployment failure with its own diagnostic path through the build and package logs rather than the startup stream.

The discipline that keeps these straight is reading the precise code and the layer it points at before acting. The .30 suffix is startup. The bare 500 is request handling. The 503 is availability. A failed deploy is the delivery stage. Each has a different first move, and the few seconds it takes to read the code correctly saves the long detour of fixing the wrong layer. When the symptom is a 500.30 specifically, the path is fixed: surface the exception, match it to one of the root causes above, apply the fix, and deploy the corrected build once.

## The Verdict

An HTTP 500.30 is not a mystery and not a flaky server fault. It is a precise statement that your process failed during startup, and the precision is hidden only because the failure happens before your application can describe itself. The entire resolution turns on one move that most engineers skip: enable stdout logging, or read the Linux log stream, and let the real exception name its own cause. From there the work is mechanical, matching the surfaced trace to an unhandled startup exception, a missing setting, a runtime mismatch, a native dependency, or a hosting-model conflict, and applying the corresponding fix. Redeploying without reading the exception is the one move guaranteed to fail, because a startup crash is deterministic and will recur until the underlying cause is corrected. Read first, fix once, and the 500.30 stops being a recurring afternoon and becomes a two-minute diagnosis.

To put the method into practice, the next step is to reproduce a 500.30 in a controlled environment and drill the exact sequence of surfacing the exception and matching it to its cause. You can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) to spin up an App Service, break its startup on purpose, and practice reading the stdout stream until the move is automatic, and you can [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) to rehearse the full 500.3x decision path against realistic failures. For the surrounding context, the [engineering deep dive on how App Service hosts your application](/2022/01/10/azure-app-service-deep-dive/) explains the worker and plan model that the hosting decision sits inside, the companion guide to [diagnosing an App Service 503 across its distinct causes](/2022/06/13/fix-app-service-503-error/) covers the availability failure that a 500.30 is most often mistaken for, and the walkthrough of [why an App Service deployment fails before the app ever starts](/2023/02/20/fix-app-service-deployment-failed/) handles the delivery-stage problems that precede startup.

## Frequently Asked Questions

### Q: What does HTTP 500.30 mean on App Service?

HTTP 500.30 is the ASP.NET Core Module reporting that it tried to launch your application process and the process failed to start. It is a startup-phase failure, not a request-handling failure, which is the distinction that governs the entire diagnosis. No controller ran and no middleware executed; the host builder threw, or the runtime could not load, before the worker ever announced it was ready to accept traffic. Because the failure happens before your application's own error handling is wired up, the framework cannot render a descriptive page, so the web server falls back to the bare module text. The real exception still exists, written to the process's standard output stream, and the resolution is to make that stream visible rather than to restart or redeploy the unchanged build.

### Q: How do I enable stdout logging to read a 500.30 on a Windows plan?

On a Windows App Service, open the Advanced Tools (Kudu) console, navigate to `/home/site/wwwroot`, and edit the generated `web.config`. Inside the `aspNetCore` element, set `stdoutLogEnabled` to `true` and point `stdoutLogFile` at a path under `LogFiles`, such as `.\..\..\LogFiles\stdout`, because that directory persists and is reachable from Kudu. Save the file, restart the app once so the module re-reads its configuration, and reproduce the failure by loading the site. The module then writes a timestamped capture file under `/home/LogFiles/stdout`, and that file contains the stack trace behind the generic page. Read it, identify the cause, then turn the redirect off again, because a permanently enabled stdout log grows without bound and is meant only for short diagnostic windows.

### Q: How do I read a 500.30 exception on a Linux App Service?

On a Linux plan your app runs inside a container whose standard output the platform captures automatically, so you do not edit `web.config`. Stream the output live with `az webapp log tail --name <app> --resource-group <rg>` and reproduce the failure with the stream open; the startup exception scrolls past as the container tries and fails to launch. The same output is also written under `/home/LogFiles` and reachable through the SSH session that Linux plans expose, so you can open a shell, list the newest log file, and read it at leisure. A common Linux signature is a managed exception wrapping a native loader message, where the framework started but a shared library the app needs is missing from the slim base image, which points the fix at the container rather than the configuration.

### Q: Can a runtime version mismatch cause a 500.30?

Yes, and it is one of the most frequent root causes. If you publish a framework-dependent application that targets a .NET runtime the plan does not have installed, the host cannot load the framework your binaries reference. Depending on which stage of loading breaks, the surfaced code is a 500.30, a 500.31, or a 500.32. Confirm it by comparing the target framework in your project file against the runtime stack the App Service is configured to serve, which `az webapp config show` reports. The fix is to align the two, either by setting the stack version on the plan to match your framework or by publishing a self-contained deployment that bundles the runtime with the app. Self-contained publishing is the more robust choice when you need to pin an exact patch version regardless of what the platform installs underneath you.

### Q: Does a missing connection string cause a 500.30 startup error?

It does, whenever your startup code reads the value and uses it immediately. If you configure a database context, a cache client, or any service during registration using a connection string that exists only in your local development settings or user secrets, the cloud process finds nothing and throws before the host is built. The result is a 500.30 whose surfaced exception names a null or empty configuration value. The fix is to set the value in the App Service application settings, using the double-underscore convention so `Database__ConnectionString` maps to the hierarchical key the configuration system expects, or better, to reference the secret from Key Vault. Validating required settings at startup with a clear message turns the next occurrence into a labeled failure rather than an opaque crash.

### Q: How does the in-process hosting model relate to 500.30?

In-process hosting runs your application directly inside the IIS worker process on a Windows plan, which removes the proxy hop and is the faster default. Because the app shares the worker, a startup exception takes the worker down and surfaces as a 500.30 with no separate child process to inspect. Out-of-process hosting runs a child dotnet process that the worker forwards requests to. A 500.30 tied to the model usually means the deployed `web.config`'s `hostingModel` attribute disagrees with the project's `AspNetCoreHostingModel` setting, or that two in-process applications are sharing a single worker, which the dedicated codes 500.34 through 500.36 describe more precisely. The fix is to pick one model, set it in the project, and let publish regenerate the matching `web.config` rather than editing the deployed file by hand.

### Q: What is the difference between 500.30, 500.31, and 500.32?

The three codes mark different stages of the same startup sequence. A 500.30 is an in-process start failure: your process launched but threw or exited during host initialization, so the cause is usually your own startup code, a missing setting, or a dependency that would not resolve. A 500.31 means the module failed to load the requested .NET runtime, which points at a runtime version that is not present on the instance. A 500.32 means it failed to load coreclr or the framework, which usually traces to a bitness or framework mismatch, or a self-contained binary set that does not match the host. Reading the suffix tells you where to look first: .30 is your initialization, while .31 and .32 are the runtime or framework not matching what you shipped.

### Q: What does a 500.37 startup time limit exceeded mean and how do I fix it?

A 500.37 means your process did not signal readiness within the window the module allows for startup, so the host treated the slow start as a failure. It commonly appears when an app does heavy work during initialization, such as running migrations, warming a large cache, or making synchronous network calls before the server is ready to listen. Confirm it by reading the surfaced output for evidence of long-running startup work, then fix it by moving that work out of the critical startup path, making it asynchronous, or doing it lazily on first use. When the work genuinely must happen at startup, you can raise the allowed window by setting the module's `startupTimeLimit` and `requestTimeout`, but a faster start is the better outcome because it also shortens recovery after every restart and slot swap.

### Q: Why does my app work locally but throw a 500.30 in Azure?

The gap is almost always something present on your machine that does not travel to the cloud. The three recurring causes are configuration that lives in user secrets or a Development settings file and was never set as an App Service application setting, a runtime version that your machine has but the plan does not, and a native dependency installed on your operating system but absent from the App Service base image. Each produces a clean local run and a cloud startup failure. The diagnosis is identical regardless of which it is: surface the startup exception through stdout logging or the Linux log stream, read which of the three it names, and close the gap by setting the configuration in App Service, aligning the runtime, or adding the dependency to the image.

### Q: How do I capture a 500.30 with Application Insights instead of stdout logging?

Attach Application Insights to the App Service and the SDK records the failed start and its exception even when stdout redirection is not enabled, giving you an always-on second source. Enable it through the portal's Application Insights blade on the app, or by setting the connection string as an application setting and adding the SDK to the project so it initializes early in the host builder. Once attached, a startup crash appears as a failed dependency or an exception telemetry item with the stack trace intact, searchable in the failures view. The advantage over stdout logging is that you do not have to reproduce the failure with a redirect enabled after the fact; the capture is already there from the moment the bad build started. Pairing always-on telemetry with staging-slot deploys means a 500.30 is usually diagnosed before it reaches a live user.

### Q: Why does a 500.30 appear only on certain instances after scaling out?

When an app runs across several instances and only some return a 500.30, the usual cause is that the instances are not all running the same artifact or the same configuration. A deploy that did not fully propagate, an application setting changed on the plan but not yet picked up by every worker, or a slot swap caught mid-flight can leave one instance starting an older or differently configured build that crashes while the others serve fine. Confirm it by checking that every instance reports the same runtime stack and the same settings, and by forcing a clean restart so all workers reload the current artifact together. The deterministic nature of a startup crash still holds per instance; the inconsistency comes from instances disagreeing about what to start, not from the failure being intermittent.

### Q: Should I set ASPNETCORE_ENVIRONMENT to Development to debug a 500.30?

Temporarily and carefully, yes. Setting `ASPNETCORE_ENVIRONMENT` to `Development`, often alongside `ASPNETCORE_DETAILEDERRORS` set to `true`, lets the framework render a richer error page once startup gets far enough to produce one, which can expose detail the bare module page hides. The strong caveat is that detailed errors reveal internals, including stack traces and sometimes configuration, that you would never want exposed publicly. Use the development setting only for a controlled diagnostic window, only when you can restrict who reaches the site, and revert it immediately afterward. For a failure that crashes before the framework can render anything at all, this approach gives you nothing extra, and the stdout stream or Application Insights remains the reliable source.

### Q: Can a bad web.config cause a 500.30 rather than a 500.33?

It can, depending on what is wrong with it. A `web.config` that is malformed or unparseable typically surfaces as a 500.33, which is specifically the module failing to read its configuration. A `web.config` that parses correctly but names a wrong process path, an incorrect arguments value, or a hosting model the platform cannot honor lets the module proceed far enough to attempt a launch that then fails, which surfaces as a 500.30 or one of the hosting-model codes. The safest practice is never to hand-edit the deployed `web.config` except for a temporary stdout redirect; let `dotnet publish` generate it from your project settings so the process path, arguments, and hosting model stay consistent with the binaries you actually shipped.

### Q: Does publishing self-contained avoid 500.30 startup failures?

It removes one specific cause, the runtime version mismatch, by bundling the .NET runtime inside the deployment so the app no longer depends on what the plan has installed. That eliminates the class of 500.30, 500.31, and 500.32 failures that come from the platform offering a different runtime than you targeted. It does not address the other causes: a missing setting, an unhandled startup exception, a native dependency, or a hosting-model conflict will still crash a self-contained app exactly as they would a framework-dependent one. Self-contained publishing trades a larger artifact and a manual responsibility for runtime patching in exchange for full control over the runtime version, which is the right deal when you must pin an exact version, and overkill when aligning the plan's stack would do.

### Q: How do I confirm which root cause is behind my specific 500.30?

Surface the exception first, then read it against the decoder. Enable stdout logging on Windows or tail the log stream on Linux, reproduce the failure, and read the stack trace. A managed type from your own code or a service-resolution message points at an unhandled startup exception. A null or missing-value message points at absent configuration. A framework-load or runtime message, or a 500.31 or 500.32 suffix, points at a version mismatch. A shared-library or `DllNotFoundException` message on Linux points at a missing native dependency. A hosting-model message, or a 500.34 through 500.36 suffix, points at an in-process versus out-of-process conflict. Matching the surfaced message to one of these signatures is the whole diagnosis, and it is reliable precisely because the failure is deterministic and names itself once the stream is visible.

### Q: Why does my App Service keep returning 500.30 after every restart?

Because a restart does not change the cause. A 500.30 from a startup exception is deterministic, meaning the same code, configuration, and runtime reproduce the same crash on every launch regardless of timing or which instance handles the request. Restarting simply relaunches the identical process into the identical failure and writes a fresh failed-start timestamp. This is the defining difference between a startup failure and a genuinely transient availability blip, which a restart can sometimes clear. The persistence is the diagnostic clue: a problem that survives every restart is a property of what you shipped, not of the platform. Stop restarting, surface the exception, fix the cause it names, and deploy the corrected artifact once. The restart loop only feels like progress because it changes the timestamp without touching the problem.

### Q: Can a failed Key Vault reference cause a 500.30?

It can, in two ways. If your startup code reads a setting that was supposed to be a resolved Key Vault reference and the resolution failed, the value arrives empty and your code throws during startup, producing a 500.30 just as a plain missing setting would. The resolution itself fails when the App Service managed identity lacks read access to the vault, when the secret name or URI is wrong, or when a network restriction blocks the app from reaching the vault. Confirm it by reading the platform's configuration diagnostics, which report a Key Vault reference that could not resolve with a specific reason, and by checking that the identity holds a get-secret permission on the vault. The fix is to grant the access, correct the reference, or open the network path, after which the resolved value injects normally and the startup proceeds.

### Q: How do I raise the startup time limit for an App Service app?

On a Windows in-process app the limit lives in the module configuration, where `startupTimeLimit` and `requestTimeout` in the `aspNetCore` element of `web.config` govern how long the module waits for readiness, though the cleaner approach is to set these through your project so publish regenerates the config rather than hand-editing the deployed file. On a Linux custom container the equivalent is the `WEBSITES_CONTAINER_START_TIME_LIMIT` application setting, which extends how long the platform waits for the container to answer its readiness probe. Raising either is appropriate when startup work genuinely cannot be shortened, but treat it as a last resort. A faster start is almost always the better fix, because it shortens recovery after every restart and slot swap, not just the first launch, and a long startup window masks a problem rather than solving it.

### Q: Does a 500.30 affect all instances or just one?

By default a 500.30 from a deterministic startup exception affects every instance that runs the failing build, because each instance launches the same artifact into the same configuration and reproduces the same crash. The exception is the apparent randomness: when only some instances fail, the instances disagree about what to start, usually because a deploy did not fully propagate, a setting changed without all workers reloading, or a swap was caught mid-flight. A truly intermittent 500.30 across identical instances is rare and points at something nondeterministic in startup, such as a race in dependency initialization. The diagnostic move is to confirm every instance reports the same runtime stack and the same settings, force a clean restart so all workers reload together, and then read the surfaced exception, which is consistent once the instances agree on what they are starting.

### Q: How is a 500.30 different from a deployment that fails before the app starts?

A 500.30 means the deploy completed, the artifact landed, and the process then failed during startup, so the diagnostic path runs through the startup output stream. A deployment that fails before the app starts never gets that far: the build or the package step errored, the file copy was blocked by a lock on the running site, or the package could not be mounted, and the diagnostic path runs through the deployment and build logs in Kudu rather than through the startup stream. The two feel similar because both leave the site not working after a push, but they live at different stages. Read where the failure sits: a completed deploy with a crashing process is a 500.30, while an incomplete or errored deploy is a delivery-stage failure with its own separate diagnosis.
