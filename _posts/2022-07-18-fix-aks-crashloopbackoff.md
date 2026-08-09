---
layout: post
title: "Fix AKS CrashLoopBackOff: Root Cause Guide"
page_title: "Fix AKS CrashLoopBackOff: Read the Previous Logs and Exit Code to Find the Root Cause and Apply the Right Fix"
date: 2022-07-18
categories: ["Technology"]
tags: ["Azure", "AKS", "Troubleshooting", "Kubernetes", "Cloud Computing", "DevOps"]
excerpt: "Fix AKS CrashLoopBackOff by reading the previous container logs and the last-state exit code, so you treat the real root cause instead of restarting blindly."
image: "/assets/images/blog/blog-93.webp"
reading_time: 59
author: "abigail-cooper"
last_updated: 2026-08-09
lang: en
---
A pod on your Azure Kubernetes Service cluster shows the status CrashLoopBackOff, and every time you look it has restarted again, with the restart count climbing into the dozens. The status is alarming because it sounds like a single fault, but it is not. CrashLoopBackOff is AKS telling you that a container inside the pod started, ran for a moment, exited, and that Kubernetes has restarted it, found it exit again, and is now waiting a little longer before each retry. The status is a symptom shared by at least six unrelated faults, and the instinct that wastes the most engineer-hours is to react to the symptom by deleting the pod, scaling the deployment, or rolling the workload, none of which touches the reason the container keeps dying. This guide gives you the one habit that replaces all of that guesswork: read the crashed container's own output and the pod's last recorded state, let the exit code name the fault, and apply the fix that matches it.

![Diagram of an AKS pod cycling through CrashLoopBackOff with growing restart backoff](/assets/images/blog/blog-93.webp)

The promise here is specific. By the end you will be able to look at a crashing pod, run two commands, and say with confidence whether you are dealing with an application that threw an unhandled exception on startup, a process the kernel killed for exceeding its memory limit, a health check that is restarting a perfectly healthy program, a missing secret or environment variable, a wrong entrypoint, or a port mismatch that the readiness gate never clears. Each of those has a distinct signature in the diagnostic output, and each has a different remedy. Restarting the workload fixes none of them and, in the memory case, actively makes the incident worse by spreading the same failure across more replicas.

## What CrashLoopBackOff Actually Means on AKS

Before you can diagnose anything, you need a precise mental model of what the status reports, because the name misleads people into chasing the wrong layer. CrashLoopBackOff is not an error thrown by your application. It is a state the kubelet on the AKS node assigns to a container that has died and is being restarted under an increasing delay. The word "loop" describes the cycle of start, exit, restart. The word "backoff" describes the delay that grows between each attempt so the node is not pinned restarting a hopeless process thousands of times a second.

The cycle works like this. The kubelet pulls the image, creates the container, and starts the process named by the image entrypoint or the pod spec command. If that process exits, whether cleanly or by signal, the kubelet consults the pod restart policy. The default policy, Always, tells the kubelet to start the process again. If the process keeps dying quickly, the kubelet inserts a delay before each restart: ten seconds, then twenty, then forty, doubling up to a ceiling of five minutes. While the kubelet is sitting inside one of those waits, the pod reports CrashLoopBackOff. The instant the process is alive again the status flips to Running, and if it dies again the status returns to the backoff wait. That flicker between Running and CrashLoopBackOff is why the restart count keeps climbing while the status never seems to settle.

This model has three immediate consequences for how you debug. First, the problem lives inside the container, not in the AKS control plane, so the place to look is the container's output and exit code, not the cluster's health. Second, because the container has already exited by the time you investigate, its logs are gone from the live container and live only in the record of the previous, now-dead instance, which is why a plain log read returns nothing useful and you have to ask for the previous one explicitly. Third, the exit code the process returned when it died is recorded in the pod's last-state field, and that single number frequently names the fault outright before you read a single line of output.

### Why does Kubernetes keep restarting a container that cannot start?

Because the default restart policy is Always, and Kubernetes treats a container that exits, for any reason, as something it should bring back. It has no way to know your container is hopeless rather than briefly unlucky, so it keeps trying under a growing delay. The backoff exists precisely to make the futile retries cheap rather than to stop them.

The restart policy is set per pod, and on a Deployment, StatefulSet, or DaemonSet it is effectively always Always, because those controllers exist to keep a desired number of running copies and a policy that gave up would defeat them. You will see OnFailure and Never on bare pods and on Jobs, where a finite task that completes should not be relaunched. For the workloads that produce most CrashLoopBackOff incidents, the policy is fixed and is not the lever you should reach for. Changing the restart policy to stop the loop is a way to silence the alarm while leaving the fire burning, and it is one of the counterproductive reactions this guide is written to talk you out of.

## How to Read the Crash: The Two Commands That Replace Guessing

The central claim of this guide, the one worth bookmarking, is the previous-logs rule for CrashLoopBackOff: the crashed container's output lives in the logs of the previous instance, and the last-state reason and exit code name the cause, so reading both together replaces a session of trial restarts. Everything downstream is the application of that rule to specific faults. Internalize the two commands and the interpretation of their output and you have most of the diagnostic skill that separates an engineer who fixes the pod in five minutes from one who restarts it for an hour.

The first command reads the output of the container that already died:

```bash
kubectl logs <pod-name> --previous
```

The `--previous` flag is the whole point. A crashing container that is currently sitting in the backoff wait has no running process, so a plain `kubectl logs <pod-name>` either errors or returns the output of a fresh, equally short-lived attempt that has not yet reached the interesting failure. The `--previous` flag asks the kubelet for the captured standard output and standard error of the prior, terminated instance, which is the run that actually contains the stack trace, the panic, the "configuration value not found" line, or the silence that itself is a clue. If the pod has more than one container, name it with `-c <container-name>`, because logs are per container and asking for the wrong one returns the wrong story.

The second command reads the pod's structured record of how the container died:

```bash
kubectl describe pod <pod-name>
```

Scroll to the container's State and Last State fields. State shows what the container is doing now, typically Waiting with the reason CrashLoopBackOff. Last State is the gold. It shows Terminated, a Reason, an Exit Code, and the start and finish timestamps of the run that just ended. The Reason is sometimes a plain word like Error and sometimes the decisive word OOMKilled. The Exit Code is an integer that, read correctly, frequently identifies the fault category before you have looked at any application output at all. Below those fields, the Events section at the bottom of the describe output lists what the kubelet has been doing: pulling the image, creating the container, starting it, and the recurring line that it is backing off restarting the failed container.

### What does the exit code in Last State tell me?

The exit code is the number the process returned to the operating system when it died, and it sorts crashes into families. A code of 1 is a generic application error, usually an unhandled exception. A code of 137 means the process was killed by signal 9, almost always the out-of-memory killer. A code of 0 with a restart loop means the program is exiting successfully when it should stay running.

Reading the exit code well is a skill worth slowing down for, because it routes the entire rest of the investigation. The Linux convention encodes signal-based terminations as 128 plus the signal number. That arithmetic turns several common codes into a precise statement of how the process died. Exit code 137 is 128 plus 9, signal SIGKILL, which on a container with a memory limit overwhelmingly means the cgroup out-of-memory killer reaped the process for exceeding its limit. Exit code 143 is 128 plus 15, signal SIGTERM, the graceful-shutdown signal, which usually means something asked the container to stop, often a liveness probe failure or a node draining. Exit code 139 is 128 plus 11, signal SIGSEGV, a segmentation fault inside the process, pointing at a native crash or a corrupt binary. Codes that are small positive integers, most often 1 and 2, are the application's own choice and mean the program ran its own code far enough to decide to quit, which sends you straight to the previous logs to read why.

Hold those four readings in your head and you can triage most crashing pods in the time it takes the describe output to scroll. The crash triage table below, the findable artifact of this guide, lays the mapping out so you can route any last-state signal to its cause and its remedy without rederiving the arithmetic each time.

## Reading the Full Diagnostic Surface, Not Just Two Fields

The two commands are the core of the habit, but a crashing pod exposes a wider surface of signal, and learning to read all of it turns a probable diagnosis into a certain one. Start with the list view, because the restart count and the age tell you a story on their own:

```bash
kubectl get pod <pod-name> -o wide
```

The output carries the status, the restart count, the age, the node the pod landed on, and its address. A restart count of two with an age of one minute is a workload still in its first attempts; a restart count of one hundred and forty with an age of nine hours is a loop that has been burning quietly for most of a shift and that nobody noticed because the deployment reports the desired replica count as met. The node column matters when the crash is node-specific, because a workload that dies only on one node and runs elsewhere points away from the application and toward that node's condition, a distinction that saves you from rewriting healthy code to chase a bad host.

The events stream is the kubelet's running narration, and reading it in time order is often more revealing than the per-pod describe block, because it interleaves the pull, the create, the start, the probe results, and the kills into the sequence in which they happened:

```bash
kubectl get events --sort-by=.lastTimestamp -n <namespace>
```

Sorted by timestamp, the events show whether a probe failure preceded each kill, whether the kills cluster at a regular interval that matches the backoff doubling, and whether anything cluster-side, a node going NotReady, a volume failing to attach, coincided with the restarts. When the application output is ambiguous, the order of events frequently disambiguates it: a kill that always follows a probe-failed line is a probe problem regardless of what the application logged, and a kill with no preceding probe line and an OOMKilled reason is a memory problem regardless of how healthy the startup looked.

For the structured last-state data without scrolling through the full describe block, a targeted query pulls exactly the fields that decide the case:

```bash
kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[0].lastState.terminated}'
```

That returns the reason, the exit code, the signal, and the timestamps as a compact object, which is the fastest way to read the decisive numbers and the form best suited to scripting an alert that fires on a specific reason.

### How do I know which container in the pod is crashing?

A pod can hold several containers, and the status reflects whichever is unhealthy, so when a multi-container pod loops you must identify the offending one. Run `kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[*].name}{"\n"}{.status.containerStatuses[*].restartCount}'` to list each container beside its restart count, and the one whose count is climbing is the one to investigate.

Once you know the name, every command takes the `-c <container-name>` selector, and both the previous-logs read and the last-state inspection narrow to that one process. This matters most with the sidecar pattern, where an application runs beside a service mesh proxy, a log shipper, or a secrets agent. A sidecar that fails to start can loop the whole pod while the application container is blameless, and chasing the application code in that situation is wasted effort. The restart-count-per-container view points you at the real culprit before you read a single log line.

## Init Containers: A Crash Loop Before the App Ever Runs

A class of crash loop that confuses engineers badly is the one that happens in an init container, because the status reads differently and the application logs are empty for a reason that has nothing to do with the application. Init containers run to completion, in order, before any of the pod's main containers start. They exist to do setup work: wait for a dependency, run a migration, fetch a configuration file, set a permission. If an init container exits non-zero, Kubernetes restarts it under the same backoff discipline, and the pod status reads `Init:CrashLoopBackOff` rather than the plain form. The main application never starts at all, so reading the application container's logs returns nothing, which sends the unwary engineer hunting for a fault in code that has not executed.

### Why does my pod show Init:CrashLoopBackOff?

It means an init container, not the main application, is the one crashing. Init containers run and must succeed before the app starts, so a failing init container loops the pod in the init phase. Read its logs specifically with `kubectl logs <pod-name> -c <init-container-name> --previous`, and the cause is usually a dependency check that never passes or a setup script that errors.

The fix follows the same six-cause logic as a main-container crash, applied to the init container's job. The most common init-container loop is a wait-for-dependency script that polls a database or an upstream service and exits non-zero when it cannot reach it, which turns an unavailable dependency into an init crash loop. That is often the intended design, a deliberate gate that holds the application back until its dependency is ready, so the right response may be to fix the dependency rather than the init container. Other init loops are migration scripts that fail on a permissions gap, file fetches that fail on a missing source, and permission-setting steps that fail on a read-only mount. The discipline is identical: name the init container, read its previous logs, let the exit reason name the fault, and fix that.

## What the Restart Count and Backoff Timing Tell You

The backoff delay is not arbitrary, and reading its shape gives you a second, independent confirmation of how severe and how fast the failure is. The kubelet starts the delay at ten seconds and doubles it after each failure, ten, twenty, forty, eighty, and so on, capping at five minutes, and it resets the delay only after a container has run successfully for long enough to be considered stable. Two patterns in that timing carry information.

A container that dies instantly on every attempt climbs the restart count quickly at first and then slows as the delay lengthens, so a pod that has been looping for an hour shows a restart count in the low tens rather than the hundreds, because most of that hour was spent in the five-minute waits. A high restart count accumulated over a short age, by contrast, means the container survived for a while between deaths, which points at a fault that triggers after startup, a memory leak that takes minutes to exhaust the limit, or a probe that only begins failing once real traffic arrives, rather than a fault that kills the process at the first instruction. The shape of the count over time is, in effect, a crude profile of when in the container's life the fault strikes, and that timing narrows the candidate causes before you read anything else.

## The InsightCrunch Crash Triage Table

This table is the reference to keep open while you work. Read the Last State reason and exit code from the describe output, find the matching row, and the cause and the confirming move follow. Each cause has its own section below with the full diagnosis and the tested remedy.

| Signal in Last State | Most likely cause | How to confirm it is yours | Where to fix it |
|---|---|---|---|
| Exit code 137, Reason OOMKilled | Container exceeded its memory limit and the kernel killed it | Reason field literally reads OOMKilled; memory limit is low relative to real usage | Raise the memory limit, or cut the program's footprint |
| Exit code 137, Reason Error, no OOMKilled | A liveness probe killed the container, or the node sent SIGKILL after a failed graceful stop | Events show liveness probe failed; the kill follows a probe failure line | Loosen the probe timing or fix the probe target |
| Exit code 143 | Container received SIGTERM and stopped; often a probe-driven restart of a healthy app | Events show a liveness probe failure immediately before termination | Correct the probe path, port, or initial delay |
| Exit code 1 | Application threw an unhandled error on startup | Previous logs show a stack trace, panic, or fatal error line | Read the trace; fix the code path, config, or dependency it names |
| Exit code 1 or 2, log names a missing value | A required environment variable, secret, or config map key is absent | Previous logs reference a missing variable or a nil configuration | Add the env var, mount the secret, or create the config map |
| Exit code 0, still looping | The entrypoint runs to completion instead of staying resident | Logs show normal output then a clean exit; no error at all | Fix the command or entrypoint so the long-running process is what runs |
| Exit code 127 | Command not found; wrong entrypoint or missing binary | Logs or events show "no such file or directory" or "executable not found" | Correct the command, args, or image so the binary exists on PATH |
| Exit code 139 | Segmentation fault in the process | Last State reason indicates SIGSEGV; native crash | Investigate the binary, native dependency, or architecture mismatch |

The discipline the table enforces is the series habit applied to this specific failure: read the cluster's own record of the crash before changing anything. The pod has already written down how it died. Your job is to read that record, not to overwrite it with another restart.

## Cause One: OOMKilled, Exit Code 137

The most common and most misdiagnosed cause of CrashLoopBackOff on AKS is the out-of-memory kill. The container asks for more memory than its limit allows, the Linux kernel's cgroup out-of-memory killer terminates the process with SIGKILL, the kubelet records exit code 137 with the reason OOMKilled, and the restart loop begins. This is the case where the reflexive reactions are not merely useless but harmful. Scaling the deployment to more replicas hands the same too-small memory limit to more copies of the same hungry process, so you get more OOMKills, not fewer. Restarting the pod gives the process a fresh start toward the identical wall it just hit.

### How do I confirm a pod is being OOMKilled?

Run `kubectl describe pod <pod-name>` and read the Last State block. If the Reason field says OOMKilled and the Exit Code is 137, the kernel killed the process for exceeding its memory limit. That is conclusive on its own. You do not need the application logs to confirm it, because the kill came from outside the application.

The describe output makes this case unambiguous, which is a mercy, because the application logs for an OOMKill are often unhelpful: the process is killed instantly by SIGKILL with no chance to flush a final message, so the previous logs may simply stop mid-sentence with no error at all. That abrupt silence, combined with the OOMKilled reason, is itself the signature. The relevant section of the describe output looks like this:

```
    Last State:     Terminated
      Reason:       OOMKilled
      Exit Code:    137
      Started:      Mon, 18 Jul 2022 09:14:02 +0000
      Finished:     Mon, 18 Jul 2022 09:14:39 +0000
```

You can corroborate the pattern by watching memory climb before the kill. If you have the Metrics Server installed, which AKS offers as a managed add-on, `kubectl top pod <pod-name>` shows current usage, and watching it approach the limit just before a restart confirms the growth. For a clearer picture over time, the container insights feature of Azure Monitor records per-container working-set memory, and a sawtooth that rises to the limit and resets at each restart is the fingerprint of a memory leak being repeatedly reaped.

### The fix: right-size the limit or shrink the footprint

There are two honest remedies and one trap. The trap is to remove the memory limit entirely so the kill stops. That does end the OOMKill, but it lets a leaking or genuinely hungry process consume node memory until the node itself comes under pressure and the kubelet starts evicting other innocent pods to reclaim it. You have converted a contained, single-pod failure into a node-wide one. Resist it.

The first honest remedy is to raise the limit to match real demand when the program legitimately needs more memory than you allotted. Look at the working-set figure just before the kills and set the limit comfortably above the observed peak, with headroom for spikes. In the pod template:

```yaml
resources:
  requests:
    memory: "512Mi"
  limits:
    memory: "768Mi"
```

Set the request to the steady-state need so the scheduler places the pod on a node that can actually hold it, and set the limit above the observed peak. A request far below the limit invites the scheduler to overcommit the node, which produces node-level memory pressure and eviction even when no single pod is over its own limit, so keep the gap deliberate rather than accidental.

The second honest remedy applies when the program does not legitimately need that much memory and is leaking or buffering carelessly. Raising the limit on a leak only delays the kill; the sawtooth in the metrics will simply take longer to climb. Here the work is in the application: cap an unbounded cache, stream a large file instead of reading it whole into memory, fix the leak, or set the runtime's own heap ceiling so it gives back rather than grows without bound. For a Java workload in particular, a process that ignores the container limit and sizes its heap to the node's total memory is a classic source of OOMKills; setting the heap relative to the container limit, or using a runtime new enough to be container-aware, aligns the two budgets so the process stays inside the cgroup.

### Runtime defaults that ignore the container limit

The reason a managed runtime tends to overshoot is that older versions read the host's total memory rather than the cgroup ceiling when they decide how large to grow. A Java Virtual Machine from before the container-aware releases sizes its heap as a fraction of the node's physical memory, so a process given a 512 mebibyte limit on a node with 16 gibibytes will happily try to claim a multi-gibibyte heap and be reaped the moment it grows into it. The remedy is either a JVM new enough to honor the cgroup limit automatically or an explicit ceiling expressed as a percentage of the limit, set through the runtime's own flags so the heap and the cgroup agree on the budget.

The same trap appears in other ecosystems with different symptoms. A Node.js process has an old-space heap ceiling that is independent of the cgroup, so a workload that buffers large payloads can be killed by the kernel well before the runtime's own garbage collector feels any pressure, and raising the runtime's heap flag without raising the cgroup limit just moves the kill from the runtime to the kernel. A Go binary holds memory the garbage collector has freed but not yet returned, so its resident footprint can sit above its live heap and brush a tight limit even when the program is not leaking, which is a case for a slightly more generous limit rather than a code change. Knowing which runtime you are operating tells you whether the lever is a runtime flag, a cgroup limit, or genuine application work.

### OOMKill versus eviction: two different memory deaths

A subtlety that misleads engineers is that a pod can die from memory pressure in two distinct ways, and the two have different reasons, different fixes, and different blast radii. The OOMKill described here is per container: one process crossed its own limit and the kernel killed that process inside its cgroup, leaving the rest of the node untouched. Eviction is different. When the node as a whole runs short of memory, the kubelet reclaims it by evicting whole pods chosen by their quality-of-service class, and an evicted pod shows the reason Evicted rather than OOMKilled, often with a message about the node being under memory pressure.

The quality-of-service class is what decides who gets evicted first, and it follows directly from how you set requests and limits. A pod whose every container sets a request equal to its limit is Guaranteed and is evicted last. A pod that sets requests and limits but not equally is Burstable. A pod that sets neither is BestEffort and is the first to be sacrificed when the node is squeezed. A workload that keeps getting evicted rather than OOMKilled is telling you the node is overcommitted, not that this one pod's limit is too low, and the fix lives at the node and scheduling layer, larger nodes, tighter requests so the scheduler stops overpacking, or the cluster autoscaler adding capacity, rather than in this single pod's memory ceiling. Reading the reason field correctly, OOMKilled versus Evicted, keeps you from raising one pod's limit when the real problem is that the whole node is oversubscribed.

## Cause Two: The Liveness Probe Restarting a Healthy Application

The second cause is the cruelest, because the application is fine and the platform is killing it anyway. A liveness probe is a health check the kubelet runs against the container on a schedule; if the check fails enough times in a row, the kubelet concludes the container is wedged and restarts it to recover. When the probe is misconfigured, it fails against a container that is perfectly healthy, the kubelet dutifully restarts it, the fresh container has not yet finished starting when the next probe arrives, that probe fails too, and you have manufactured a CrashLoopBackOff out of a working program.

### Can a liveness probe cause CrashLoopBackOff?

Yes, and it is one of the most common non-obvious causes. If the probe's timing is too aggressive, it kills the container before the application has finished starting, and the restarted container is killed again the same way. The application never gets the chance to prove it is healthy, so the loop is entirely the probe's doing rather than a real fault in the code.

The tell is in the Events section of the describe output rather than the application logs, because the application did nothing wrong. You will see a line reporting that the liveness probe failed, often with the HTTP status or the connection error, followed shortly by the container being killed and restarted. The exit code is frequently 137 or 143, because the kubelet terminates the container by signal rather than the application exiting of its own accord. Crucially, the previous logs usually look healthy: the application logs its normal startup sequence and then is cut off, not by a crash, but by an external kill that arrived before startup finished.

The most frequent specific misconfiguration is an `initialDelaySeconds` that is shorter than the application's real startup time. A program that needs forty seconds to warm a cache, run migrations, and open its listener will fail every probe sent during those forty seconds, and a probe configured to start checking after ten seconds with a low failure threshold will kill it long before it is ready. Other variants are a probe pointed at the wrong path, a probe pointed at the wrong port, a `timeoutSeconds` so short that a momentarily busy app misses the deadline, and a `failureThreshold` of one that gives no tolerance for a single slow response.

### The fix: align the probe with the application's real behavior

The remedy is to make the probe describe the application as it actually behaves rather than as you wish it behaved. If the program needs forty seconds to become ready, the probe must not start judging it until then. The cleanest tool for a slow start is a startup probe, which gates the liveness probe entirely until the application has come up once, after which the liveness probe takes over with tighter timing for steady-state monitoring:

```yaml
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 3
```

The startup probe above tolerates up to three hundred seconds of startup, after which the liveness probe runs every ten seconds and restarts the container only after three consecutive failures. The split lets you be patient about the cold start without being permanently lax about runtime health. If your AKS cluster runs a Kubernetes version that predates startup probes, the older workaround is to set `initialDelaySeconds` on the liveness probe to a value comfortably above the real startup time, which is blunter but effective.

Two adjustments matter alongside the timing. First, point the probe at an endpoint that reports the application's own liveness rather than a dependency's, because a liveness probe that returns failure when a downstream database is briefly unreachable will restart a healthy application during a database blip and turn a transient dependency issue into a self-inflicted crash loop. Second, confirm the port in the probe matches the port the application actually listens on; a probe aimed at the wrong port can never succeed and will restart the container forever regardless of how healthy it is, which is really the port-mismatch cause described later wearing a probe's clothing.

### The three probes do different jobs, and only one restarts the container

Kubernetes offers three health checks, and conflating them is a frequent source of self-inflicted crash loops, so it is worth being precise about what each one does. The liveness probe answers "is this process wedged and beyond recovery," and a sustained failure causes the kubelet to restart the container, which is the only one of the three that can produce CrashLoopBackOff. The readiness probe answers "can this container accept traffic right now," and a failure removes the pod from its Service endpoints but never restarts it, so a failing readiness probe causes a pod to receive no traffic rather than to crash. The startup probe answers "has this container finished its initial boot," and while it runs it suspends the liveness and readiness checks, which is exactly what protects a slow starter from being killed mid-boot.

The practical upshot is that if your pod is looping, the readiness probe is not the culprit, because readiness cannot trigger a restart. Reach straight for the liveness configuration and the startup configuration. A common mistake is to harden a readiness probe in response to a crash loop, which does nothing because readiness was never the lever, while the over-aggressive liveness probe keeps killing the container untouched. Naming the three probes correctly in your own head routes you to the right one immediately.

### Match the probe mechanism to what it is checking

A probe checks the container by one of four mechanisms, and choosing the wrong mechanism is its own source of false failures. An `httpGet` probe expects a success status from a path and port and is right for an HTTP service, but it fails if the endpoint returns a redirect or requires authentication the probe does not supply, so the health endpoint must be a plain, unauthenticated, fast path that returns success without touching slow dependencies. A `tcpSocket` probe only checks that the port accepts a connection, which suits a service that speaks a non-HTTP protocol but cannot tell whether the application behind the port is actually functioning, so it can pass against a half-broken process. An `exec` probe runs a command inside the container and treats a zero exit as success, which is flexible but heavier, and a slow command under a tight `timeoutSeconds` can itself cause the failure it was meant to detect. A gRPC probe, available on recent clusters, checks a gRPC health service directly and is the correct choice for a gRPC server rather than wrapping it in a TCP check.

The most resilient liveness endpoint is deliberately shallow: it confirms the process is running and its event loop is responsive, and it does not check the database, the cache, or any downstream service. A liveness endpoint that returns failure when a dependency is briefly unreachable converts every dependency blip into a restart, which is the opposite of resilience. Deep checks belong on the readiness probe, where a failure correctly pulls the pod out of rotation until the dependency recovers, without killing a process that is itself perfectly alive. Splitting the shallow liveness check from the deep readiness check is the single configuration habit that prevents the largest share of probe-driven crash loops.

## Cause Three: A Missing Environment Variable, Secret, or Config Map

The third cause is a startup crash driven by absent configuration. The application boots, looks for a value it needs, a database connection string, an API key, a feature flag, a path, finds it missing or empty, and exits rather than run in a broken state. This produces a clean exit code 1 or 2 and, mercifully, an explicit message in the previous logs naming what it could not find.

### Does a missing secret or environment variable cause CrashLoopBackOff?

Yes. When an application requires a configuration value at startup and that value is not present, a well-written program logs the missing key and exits, which the kubelet sees as a crash and restarts into the same missing value. The previous logs are the fastest confirmation, because a careful application names exactly which variable, secret, or config map key it could not resolve.

This is where the previous-logs rule earns its keep most directly. Run `kubectl logs <pod-name> --previous` and you will frequently find a line stating that a required environment variable is unset, that a configuration property has no value, or that the application could not connect because the connection string was empty. The exit code is the application's own choice, usually 1. The fault is not in the code or the image; it is in the wiring between the pod and the configuration source.

The wiring fails in several concrete ways worth recognizing. The secret or config map may not exist in the pod's namespace, which is a frequent trap because a secret created in `default` is invisible to a pod running in `production`. The key name referenced in the pod spec may not match the key name inside the secret or config map, a single typo that yields an empty value. A secret referenced through `secretKeyRef` may exist while the specific key requested does not. An environment variable may be set to reference a field that resolves to nothing. Or the value may be present but malformed, an empty string where the application expects a URL, which crashes the parser rather than the lookup.

### The fix: create and bind the configuration correctly

Start by confirming the configuration objects exist where the pod expects them, in the pod's own namespace:

```bash
kubectl get configmap -n <namespace>
kubectl get secret -n <namespace>
```

If the object is missing, create it. If it exists, confirm the exact keys it holds match the keys the pod spec references, since a mismatched key name produces an empty value rather than an error at bind time. For a secret consumed as environment variables, the pod spec references each key explicitly:

```yaml
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: app-secrets
        key: database-url
```

The `name` under `secretKeyRef` must match the secret's name and the `key` must match a key inside it. A surprising amount of CrashLoopBackOff comes down to a hyphen-versus-underscore discrepancy between these two layers. After correcting the binding, the pod must be recreated to pick up the change for variables injected at start, because environment variables are read once at container start and are not refreshed on an existing pod; a rollout restart of the deployment applies the corrected spec.

Two prevention habits cut this cause off at the source. Validate required configuration explicitly at startup and fail with a clear, specific message naming the missing key, so the previous logs hand the next engineer the answer instantly rather than a vague stack trace. And keep configuration objects in the same namespace as the workloads that consume them, or use a controlled mechanism to project shared secrets across namespaces, so the "exists but not here" trap never arises.

### Mounted files behave differently from environment variables

How the application consumes configuration changes both the failure mode and the fix, so it is worth distinguishing the two delivery paths. A value injected as an environment variable is read once when the container starts and is frozen for the life of that container, so updating the secret has no effect until the pod is recreated, which is why a rollout restart is part of the fix for the env-var case. A value mounted as a file from a secret or config map volume is different: the kubelet refreshes the file in place after the source changes, so a long-running container can pick up a new value without a restart if the application re-reads the file. That refresh is not instant and does not apply to env vars, and an application that reads a mounted file only once at startup gains nothing from it, so know which behavior your application relies on before you reason about whether a restart is required.

The mounted path has its own crash signatures. A secret mounted as a volume that does not exist leaves the mount point empty or blocks the pod from starting, depending on whether the reference is marked optional, and an application that reads an expected file and finds it absent crashes exactly as it would on a missing env var. Marking a reference optional changes a hard failure into a soft one where the application must tolerate the absence, which is the right choice only when the value genuinely is optional. A subtle variant is a key projected to a specific file path that does not match where the application looks, so the secret is mounted correctly but the application reads the wrong filename and behaves as though it were missing.

### Immutable config and the rollout that never happened

Two operational traps round out this cause. The first is the deployment that was never rolled. Changing a config map or secret does not automatically restart the pods that consume it through environment variables, so the corrected value sits in the object while the running pods keep crashing on the old, stale copy they read at their own start. The fix is incomplete until you trigger a rollout, with `kubectl rollout restart deployment <name>`, so the new pods read the corrected configuration. The second trap is the immutable config map or secret, a flag that forbids changes to protect against accidental edits; an immutable object must be deleted and recreated rather than patched, and an attempt to edit it in place silently does nothing, leaving the workload crashing on a value you believe you already fixed. Checking whether the object is immutable before you try to correct it saves a confusing round of edits that appear to take but change nothing.

## Cause Four: A Wrong Command, Entrypoint, or Missing Binary

The fourth cause is a container that cannot run the program it was told to run, either because the command points at a binary that does not exist on the image or because the entrypoint is wrong. The signature is often exit code 127, the shell's code for "command not found," or a log and event line reading that there is no such file or directory or that the executable was not found in the container's PATH.

This cause appears most often after a change. Someone overrides the image's default command in the pod spec, mistypes the binary name or its path, and the container dies instantly because the kubelet cannot start anything. It also appears when a multi-stage image build produces a final image that is missing the binary the entrypoint expects, or when a script lacks the executable bit, or when the image is built for one CPU architecture and scheduled onto a node of another, so the binary exists but cannot execute, which on AKS happens when an arm64 image lands on an amd64 node pool or the reverse.

The confirmation is quick. The previous logs may be empty, because nothing ran long enough to write output, so the describe output and its Events section carry the signal. Look for a message that the executable was not found, that there is no such file or directory, or an exec format error, which specifically indicates an architecture mismatch rather than a missing file. The fix is to correct the `command` and `args` in the pod spec so they name a binary that exists on the image at a path on the container's PATH, to rebuild the image so the expected binary is present and executable, or, for the architecture case, to build a matching image or schedule the pod onto a node pool whose CPU architecture matches the image.

### How the pod spec overrides the image, and why that breaks things

The confusion at the root of most wrong-command crashes is that the pod spec's `command` and `args` override the image's built-in entrypoint and default arguments, and the override rules are not what people assume. The image's `ENTRYPOINT` is replaced by the pod spec's `command`, and the image's `CMD` is replaced by the pod spec's `args`. When you set only `command` in the pod spec, you replace the entrypoint but also discard the image's default `CMD`, so a container that worked from its image alone can crash once you add a `command` that omits the arguments the image expected to receive. Setting `command` without the corresponding `args` is therefore a frequent way to break a previously healthy image, and the fix is to supply both halves rather than half-overriding the launch.

A related trap is the difference between the shell form and the exec form of an entrypoint. An entrypoint written in shell form runs through a shell, which means a missing binary surfaces as a shell error and the process running as the container's main process is the shell rather than your program, so signals like SIGTERM may not reach the application during shutdown and the exit codes may be the shell's rather than the program's. An entrypoint in exec form runs the binary directly as the main process, which is what you want for clean signal handling and accurate exit codes. When a container crashes with a confusing exit code or fails to stop gracefully, an entrypoint stuck in shell form is worth checking, because it changes both how the process dies and what code it reports when it does.

## Cause Five: A Port Mismatch the Readiness or Liveness Gate Never Clears

The fifth cause overlaps with the probe case but deserves its own treatment because the root is a mismatch between the port the application listens on and the port the rest of the system expects. If the container listens on port 8080 but the liveness probe checks port 80, the probe can never succeed, and the kubelet restarts the container forever exactly as in the probe-timing case, except no amount of timing adjustment will help because the target is simply wrong.

The same mismatch bites through Services and readiness gates. A readiness probe on the wrong port keeps the pod out of the Service endpoints so traffic never arrives, which is a different symptom, but a liveness probe on the wrong port produces the crash loop directly. The confirmation is to read the application's previous logs to learn the port it actually bound, which a well-behaved server announces on startup, and compare that against the `containerPort`, the probe `port`, and any Service `targetPort` in the manifests. When they disagree, the application is healthy and the platform is testing the wrong door.

The fix is alignment. Decide the one port the application listens on, set the application or its configuration to bind that port, set `containerPort` to it, point both probes at it, and set the Service `targetPort` to it. The single most common version of this fault is an application whose listen port is itself configurable through an environment variable that was changed without updating the manifests, so the application now listens somewhere the probes do not look. Treating the port as one value defined in one place and referenced everywhere else removes the whole class of mismatch.

### Why does my app run but the probe still fails on the right code?

If the application starts cleanly yet the liveness probe keeps failing, the probe is almost certainly reaching the wrong place rather than the application being unhealthy. Confirm the exact port and path the process binds from its own startup output, then compare that against the probe definition. A probe on a port nothing listens on, or a path that returns a non-success status, fails forever against a healthy process.

The most insidious version of this hides behind a configurable listen port. Many frameworks let an environment variable set the port the server binds, with a built-in default the application falls back to when the variable is unset. A workload that worked because both the application default and the probe happened to agree on one number breaks the moment someone sets the port variable in the deployment without updating the `containerPort` and the probe `port` to match, because the application now listens somewhere the probe never checks. The application logs look perfect, the probe fails relentlessly, and the loop has nothing to do with the code. The same disagreement propagates through the Service: a `targetPort` that points at the old number sends traffic to a closed door even when the pod survives, layering a routing failure on top of the crash. The cure is to derive every reference from a single declared value rather than letting the application default and the manifest drift apart, so changing the port in one place updates the binding, the probe target, and the Service route together instead of leaving two of the three pointing at a port the process abandoned.

## Cause Six: An Unhandled Exception or Failed Dependency at Startup

The sixth cause is the plain application crash: the program runs its own startup code, hits an exception it does not handle, and exits with code 1. This is distinct from the missing-configuration case even though both produce exit code 1, because here the failure is in logic or in a dependency rather than in a missing value. The application tried to connect to a database that refused the connection, ran a migration that failed, dereferenced something null, or threw during initialization, and the previous logs carry the stack trace that names the line.

This is the cause for which the previous logs are the entire diagnosis. There is no shortcut through the exit code, because exit code 1 is generic; the program's own output is the only thing that distinguishes a failed database connection from a null pointer from a failed schema migration. Read the trace top to bottom. A connection refused to a database host points at a dependency that is unreachable, which on AKS often means a Service name that does not resolve, a network policy blocking the egress, or a firewall on the managed database rejecting the cluster's address. A migration failure points at schema drift or a permissions gap on the database user. An initialization exception points into your own code.

The remedy depends entirely on what the trace names, which is why no single command fixes this cause. What is universal is the discipline: do not guess at the cause of a generic exit code 1, read the previous logs and let the stack trace tell you, then fix the specific thing it names. For a failed dependency, that may mean correcting a connection string, opening a network path, or adding retry-with-backoff so a transient dependency outage during a deployment does not crash the application outright. A startup that tolerates a briefly unavailable dependency by retrying rather than exiting turns a momentary blip into a short delay instead of a crash loop, which is the more resilient pattern for any service that depends on another at boot.

### When the dependency is unreachable for a cluster-specific reason

A failed dependency connection inside the cluster has causes that never appear when you run the program on a laptop, and recognizing them saves you from rewriting code that is actually correct. The most common is name resolution. A workload that connects to another service by its Kubernetes Service name relies on cluster DNS, and if the Service does not exist, sits in a different namespace than the short name assumes, or the cluster DNS itself is degraded, the lookup fails and the connection never forms. The previous logs show a resolution error or an unknown host rather than a refused connection, which is the tell that the problem is DNS and not the dependency being down. Testing the name from a temporary shell in the cluster, as described earlier, confirms it quickly.

The second cluster-specific cause is a network policy that silently drops the egress. If the namespace has a default-deny policy and no rule permits the workload to reach its dependency, the connection attempts simply time out, and the logs show a timeout rather than a refusal, because nothing on the other end ever rejected anything; the packets were dropped in flight. The third is a managed dependency's own firewall, an Azure SQL or Cosmos DB instance that rejects connections from addresses not on its allow list, so the cluster's outbound address must be permitted on the database side. Each of these presents as a startup crash with a connection error in the previous logs, and each is a network or naming fix rather than a code fix, which is why reading the exact wording of the error, resolution failure versus timeout versus refusal, points at the right layer.

### The wait-and-retry pattern that ends the loop

When the dependency is genuinely just slow to come up, often during a coordinated deployment where the application and its database start together, the durable fix is to make the application patient rather than brittle. Two patterns achieve this. The application can retry the connection on startup with a bounded, backing-off loop, so a dependency that is unreachable for the first few seconds causes a short wait instead of an exit. Or the pod can use an init container whose only job is to poll the dependency until it answers and then exit successfully, which holds the main application back until the dependency is genuinely ready and keeps the retry logic out of the application code entirely. The init-container approach has the advantage that a still-unavailable dependency shows as a clear `Init:CrashLoopBackOff` pointed at the wait container, which names the problem precisely, rather than burying it in application startup output. Either pattern converts the most common deployment-ordering crash into a brief, self-resolving delay.

## Getting a Shell When the Container Will Not Stay Up

Some crashes resist the previous-logs read because the container dies before it writes anything useful, or because the fault is something you need to inspect from inside the filesystem, a missing file, a wrong permission, an environment that does not look the way you expect. The problem is that you cannot `kubectl exec` into a container that is not running, and a CrashLoopBackOff container spends most of its time dead. Two techniques get you inside anyway.

The first is to override the entrypoint so the container starts a shell and stays alive instead of running the failing program. Apply a temporary variant of the pod that sets the command to a long sleep:

```yaml
command: ["/bin/sh", "-c", "sleep 3600"]
```

With the real program replaced by a sleep, the container starts and stays up, and you can `kubectl exec -it <pod-name> -- /bin/sh` into it to look around: check that the expected files exist, that environment variables resolved, that the binary is present and executable, and then run the real command by hand and watch it fail in front of you with full output. This converts an instant crash into an interactive session where the failure is observable rather than inferred. Remember to remove the override afterward, because a container sleeping forever is not running your workload.

The second technique, available on recent clusters, is the ephemeral debug container, which attaches a throwaway container to the running pod without changing its spec:

```bash
kubectl debug -it <pod-name> --image=busybox --target=<container-name>
```

The debug container shares the target's process and, depending on configuration, its filesystem view, so you can inspect the environment of the real container without restarting it or editing its definition. This is the cleaner option when it is available, because it leaves the workload's spec untouched and does not require a temporary redeploy. For an image so minimal that it has no shell of its own, a distroless image being the common case, the debug container supplies the tools the target lacks, which is the only practical way to inspect a container that ships without a shell.

### A worked reproduction of the memory kill

Concrete practice cements the habit, so here is the full loop for the OOMKill case, the kind of exercise the companion labs are built around. Deploy a workload with a memory limit set deliberately below what the process needs, for example a program that allocates three hundred mebibytes against a limit of one hundred and twenty-eight. The pod starts, the process allocates past the ceiling, the kernel kills it, and within a minute the status shows CrashLoopBackOff with a restart count climbing. Run `kubectl describe pod` and read the Last State: the reason is OOMKilled and the exit code is 137, exactly as the table predicts. The application logs, read with the previous flag, stop abruptly with no error, because SIGKILL gave the process no chance to complain. Now apply the fix, raise the limit above the real footprint, roll the deployment, and watch the status settle to Running and stay there with the restart count frozen. Having seen the signature once in a controlled setting, you recognize it instantly in production.

### A worked reproduction of the probe kill

The probe case is just as instructive and more surprising, because the application is healthy throughout. Deploy a program that takes thirty seconds to become ready, and give it a liveness probe with an initial delay of five seconds and a low failure threshold, with no startup probe. The container starts, the probe begins checking at five seconds, fails because the application is still warming up, fails twice more, and the kubelet kills a container that was about to become healthy. The fresh container repeats the pattern, and the pod loops. The describe events show the liveness-probe-failed line before each kill, and the previous logs show a clean, error-free startup cut short, the unmistakable signature of a probe killing a healthy process. Add a startup probe that tolerates the thirty-second boot, roll the deployment, and the loop ends without touching a line of application code, because the application was never the problem.

## CrashLoopBackOff in Jobs, CronJobs, and DaemonSets

The restart behavior differs across workload types, and knowing the difference keeps you from misreading a crash in a non-Deployment workload. A Job runs a finite task and typically sets its restart policy to OnFailure or Never, so a failing Job container may be restarted a bounded number of times and then marked failed rather than looping forever, and the signal to read is the Job's backoff limit and its failed-pod count rather than an endless restart count. A CronJob spawns Jobs on a schedule, so a crash there can show as repeated failed Jobs at each scheduled run, and chasing a single pod misses the pattern that every scheduled invocation is failing the same way for the same reason.

A DaemonSet runs one pod per node, so a crash in a DaemonSet pod has a node dimension the others lack: if the pod crashes on every node, the fault is in the workload, but if it crashes only on certain nodes, the fault is something those nodes share and the others do not, a kernel version, a missing host path, a label, a taint. The per-node view is the diagnostic that a Deployment does not need, because a DaemonSet's whole purpose is to run everywhere and its failures often correlate with where rather than with what. Reading the crash through the lens of the workload type, finite task, scheduled task, or per-node task, frames the same six causes correctly for each.

## Preventing CrashLoopBackOff Before It Starts

Diagnosis is reactive. The more valuable position is to make the common causes impossible or self-explaining, so the next crash either does not happen or names itself in one line of the previous logs. The prevention measures map directly onto the six causes.

Against the memory kill, set requests and limits deliberately from measured usage rather than copied from a template, and watch container memory in Azure Monitor so a slow leak shows as a rising trend before it becomes a restart loop. A pod with a request that reflects steady-state need and a limit set above the observed peak, on a node sized to hold the request, does not get OOMKilled under normal operation, and a leak announces itself in the metrics long before it pages anyone.

Against the probe self-kill, use a startup probe for anything with a non-trivial cold start, point liveness probes at an endpoint that reports the application's own health rather than a dependency's, and keep the liveness threshold tolerant enough to ride out a single slow response. The probe should answer the question "is this process wedged and in need of a restart," not "is every downstream system healthy right now," because conflating the two makes the application restart itself whenever anything it talks to has a bad second.

Against the missing-configuration crash, validate required values at startup and exit with a message that names the exact missing key, and keep configuration objects in the consuming workload's namespace. Against the wrong-command and architecture faults, pin the image by digest rather than a mutable tag so a rebuild cannot silently change the entrypoint or the architecture under you, and run the image locally or in a pipeline stage before it reaches the cluster. Against the dependency crash, make startup tolerant of a briefly unavailable dependency through bounded retries rather than an immediate exit.

The common thread is observability and explicitness. A cluster wired to Azure Monitor container insights gives you the memory trend, the restart counts, and the events in one place, so a crash loop is visible as a pattern rather than discovered when a user complains. To reproduce each of these causes safely and drill the diagnosis until the two-command habit is automatic, [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) alongside the hands-on [Azure labs and command library on VaultBook](https://vaultbook.net/tools/azure-labs.html), where you can stand up a deliberately broken deployment for each row of the triage table and practice reading the previous logs and the last-state exit code until it is reflex.

## Graceful Shutdown, SIGTERM, and the Exit Code 143 Trap

A category of confusing termination comes not from the container failing but from the platform asking it to stop and the container handling that request badly. When Kubernetes needs to end a container, during a rolling update, a scale-down, a node drain, or a probe-driven restart, it sends SIGTERM first, waits for a grace period, and only then sends the unstoppable SIGKILL. A program that catches SIGTERM and shuts down cleanly exits with a code that reflects an orderly stop, often 143, which is 128 plus signal 15. Seeing exit code 143 in the Last State is therefore not always a fault: it can simply mean the container was asked to stop and complied. The question is whether the stop was warranted.

The trap is a program that ignores SIGTERM. If the application does not handle the signal, it keeps running until the grace period expires and the kubelet sends SIGKILL, which produces exit code 137 with no OOMKilled reason, a combination that misleads engineers into hunting a memory problem that does not exist. The signature that distinguishes this from a real OOMKill is the absence of the OOMKilled reason and the presence of a preceding stop request in the events, often a probe failure or a drain. The fix is to make the application handle SIGTERM, draining in-flight work and closing connections within the grace period, and to set `terminationGracePeriodSeconds` long enough for that drain to finish. A `preStop` hook can hold the container briefly so load balancers stop sending it traffic before it begins shutting down, which removes the errors that otherwise appear during the stop. Reading exit code 143 and exit-code-137-without-OOMKilled as shutdown-handling problems rather than crashes keeps you from chasing phantom faults in healthy code.

## Node and Platform Factors That Look Like Crashes

Not every restart loop originates inside the workload. The node beneath it can produce symptoms that mimic a crash, and distinguishing the two saves you from rewriting an application to fix a host. A node under disk pressure triggers eviction of pods to reclaim space, and ephemeral storage that a workload fills, through unbounded logs written to the container filesystem or large temporary files, can get the pod evicted with a message about exceeding its ephemeral-storage limit rather than crashing on its own logic. The fix there is to bound the workload's disk use or raise its ephemeral-storage request, not to touch the application's startup path.

A node that goes NotReady, because the kubelet stopped reporting, the node ran out of resources, or the underlying virtual machine had a problem, causes its pods to be marked for eviction and rescheduled, which can look like a crash loop if the same workload keeps landing on unhealthy nodes. The discriminator is whether the failures correlate with specific nodes, visible in the `-o wide` node column, in which case the node is the suspect rather than the code. Networking faults at the node level, a failing container network interface, exhausted pod IP addresses under the cluster's networking model, or degraded cluster DNS, present as dependency-connection failures inside the application even though the application itself is correct. When the previous logs show connection timeouts to multiple unrelated destinations rather than one specific dependency, suspect the node's network rather than any single downstream service. The habit that keeps these straight is to ask, before editing the workload, whether the failure follows the workload everywhere or stays attached to particular hosts; the answer routes you to the right layer.

## Detecting the Loop Before a User Does

The worst CrashLoopBackOff is the one that runs for hours unseen because the deployment still reports its desired replica count and no human is watching the restart column. Closing that gap is a prevention measure in its own right. With the workload's metrics flowing to Azure Monitor through container insights, you can alert on the restart count and on the OOMKilled reason directly, so a climbing restart count pages someone within minutes rather than surfacing as a customer complaint hours later. A log query against the container records can count restarts per workload over a short window and fire when the count crosses a threshold, and a separate alert on the OOMKilled termination reason catches the memory case specifically, which is valuable because the memory case is both common and silent in the application logs.

Teams running their own metrics stack alongside the cluster watch the standard restart-count gauge that the cluster's metrics expose per container, alerting when it increases faster than a small rate over a few minutes, which catches a fresh loop quickly without firing on the single restart that a healthy rolling update produces. Whichever stack you use, the principle is the same: a restart count that climbs is a signal worth a page, because a Deployment that reports healthy while its pods loop is the exact situation where a crash hides longest. Wiring that signal once means the next crash announces itself, and the diagnosis you have practiced here begins within minutes of the first restart rather than after a shift of silent failure.

## Related Failures CrashLoopBackOff Is Often Confused With

CrashLoopBackOff is one station on a pod's path from scheduled to serving, and it is easy to confuse with the failures on either side of it. Knowing the neighbors keeps you from applying the crash-loop playbook to a problem that is really about scheduling or image pulls.

The stage before the container ever starts is the image pull. If the kubelet cannot fetch the image, the pod shows ImagePullBackOff or ErrImagePull rather than CrashLoopBackOff, and the cause lives in registry authentication, a wrong tag, or a rate limit rather than in the application. The backoff word in both statuses makes them look like relatives, but the remedy is entirely different, and the full diagnosis lives in the companion guide on how to [fix AKS ImagePullBackOff and ErrImagePull](/2022/07/11/fix-aks-imagepullbackoff/). If your pod never reaches a running container at all and the status is about pulling, you are on the wrong page and that one is the right one.

The stage even earlier is scheduling. A pod that cannot be placed on any node sits in Pending, not CrashLoopBackOff, and the cause is insufficient CPU or memory on the nodes, a taint with no matching toleration, a node selector that matches nothing, or unbound storage. That is a placement problem rather than a runtime crash, and it is covered in the guide on how to [fix AKS pods stuck in Pending state](/2022/07/25/fix-aks-pods-pending/). The quick discriminator is the status itself: Pending means the pod has not started, CrashLoopBackOff means it started and keeps dying.

For the secrets-and-configuration angle that drives the missing-value cause, the hardening side, where secrets should come from workload identity and Key Vault rather than plain Kubernetes secrets, is treated in the guide on [securing AKS clusters](/2024/02/12/securing-aks-clusters-guide/). And for the mental model that underlies all of this, what a pod is, how the kubelet runs containers, and where the managed boundary sits between you and AKS, the foundational reference is the deep dive on [Azure Kubernetes Service](/2022/01/17/azure-kubernetes-service-aks-explained/), which is the right place to start if any of the terms in this guide felt unfamiliar.

## When the Previous Logs Are Empty

The previous-logs rule depends on the crashed instance having written something, and occasionally it has not, which throws engineers who have come to rely on the trace being there. An empty previous-log read has a small set of explanations, and each points somewhere specific. The first, already covered, is the instant SIGKILL of an OOMKill, which gives the process no window to flush a final line, so emptiness combined with the OOMKilled reason is itself conclusive and you do not need the missing output. The second is a process killed before it produced any output at all, a wrong command that never started, which the events rather than the logs reveal.

The third and most fixable explanation is a logging misconfiguration, where the application is writing its output to a file inside the writable layer rather than to standard output and standard error. Kubernetes captures only what a process writes to those two streams, so an application that logs to a path on its own filesystem produces a perfectly detailed log that the cluster never sees and that vanishes when the dead container's layer is cleaned up. The signature is a mature application that crashes with completely empty captured output, which is implausible for a program that surely logs something on the way down. The fix is to configure the application to log to standard output, the convention every container platform expects, after which the previous-logs read starts returning the detail it was missing. Until then, the temporary-shell technique lets you run the program by hand and read whatever file it was writing to.

A complementary mechanism is the termination message. Kubernetes reads a small file, by default at a known path, when a container terminates, and surfaces its contents in the Last State message field, which gives you a place to record a final cause even when standard streams are noisy or empty. An application that writes its fatal reason to that file, or a configuration that captures the last lines of standard error into it, makes the describe output carry the cause directly. For a container that dies too fast or too silently for the ordinary log path, the termination message is the channel that still works, and wiring it is a cheap way to ensure that even the quietest crash leaves a one-line explanation in the place you already look.

## Stopping and Rolling Back a Bad Deployment Safely

While you diagnose, the bad version may still be rolling out to more replicas, and knowing how to halt and reverse that protects the running service. A rolling update that is replacing healthy old pods with new ones that immediately crash is a slow-motion outage, but Kubernetes gives you the controls to freeze it. Pausing the rollout with `kubectl rollout pause deployment <name>` stops new pods from being created while you investigate, holding the blast radius at whatever has already shipped rather than letting the bad version march across every replica. If the surviving old pods are still serving, pausing buys you time without losing capacity.

If the new version is clearly the regression, rolling back is faster than diagnosing under pressure. `kubectl rollout undo deployment <name>` returns the workload to its previous revision, restoring the version that was running before the crash began, which stops the incident immediately and lets you diagnose the broken image at leisure rather than live. The rollout history, visible with `kubectl rollout history deployment <name>`, shows the revisions available to return to. The discipline here mirrors the rest of the guide: stabilize first by returning to the known-good state, then diagnose the failed version using the previous logs and exit code on a crashing pod you keep around for the purpose, rather than leaving the service degraded while you read traces.

A configuration habit makes these recoveries safer still. Setting a conservative `maxUnavailable` and a readiness probe that genuinely gates traffic means a rolling update will not retire old pods faster than new ones prove healthy, so a batch of crashing new pods stalls the rollout automatically rather than taking the service down, because the update cannot proceed past replicas that never become ready. A rollout that protects itself this way turns a bad image from an outage into a stalled deployment that pages you while the old version keeps serving, which is exactly the failure mode you want: visible, contained, and reversible.

## The Reflex to Resist and the Procedure to Follow Instead

The instinct that costs the most time is the one that feels most like action: when a pod loops, delete it, add replicas, or roll the whole deployment and hope the churn shakes the fault loose. Every one of those moves treats the visible loop as the problem rather than the cause underneath it, and in the memory case the most popular reflex is the most damaging. Adding replicas to a workload that is OOMKilled hands the same too-small limit to more copies, so a single contained failure becomes a fleet of them, each burning a node's memory and each crashing on schedule. Deleting the pod gives a fresh start toward the identical wall. Rolling the deployment recreates the same broken spec. The churn produces motion that looks like progress and changes nothing, because none of it touches the reason the process exits.

The reason these reflexes persist is that they occasionally appear to work, which teaches the wrong lesson. A pod that crashed on a genuinely transient condition, a dependency that happened to be down for ten seconds during a deployment, will indeed recover when you delete and recreate it, because the transient passed in the meantime rather than because the deletion fixed anything. That coincidental success trains the habit, and the habit then fails silently on every non-transient cause, which is the majority. The discipline of reading before acting costs a minute the first time and saves an hour every time after, because it tells you immediately whether you are in the rare transient case or one of the six structural ones that churning cannot cure.

The procedure that replaces the reflex is short enough to run from memory and is the same every time. First, read the status and restart count to see how long the loop has run and whether it follows the workload or stays on particular nodes. Second, read the Last State exit code, which sorts the crash into a family in seconds: 137 with OOMKilled is memory, 137 without it or 143 is a signal stop usually from a probe or a shutdown the process mishandled, 127 is a missing command, 139 is a native fault, and 1 is the application's own error. Third, for the application-error family, read the previous logs and let the stack trace name the specific fault, and for a multi-container or init-container pod, name the right container first so you read the failing one. Fourth, match the named cause to the triage table and apply the remedy that fits it rather than a generic restart. Fifth, where the version itself is the regression, stabilize by rolling back to the known-good revision before diagnosing, so the service recovers immediately and you read the failed image at leisure.

Run that sequence and the loop ends because its cause is gone, which is the only way a crash loop ever truly ends. The status that looked like one alarming fault resolves into a specific, named problem with a specific, tested fix, and the minute you spent reading the cluster's own record of the crash is the minute that made every step after it correct. That habit, read first and let the evidence name the cause, is what the rest of this series applies to every failure it covers, and it is what turns a frightening status into a routine five-minute repair.

## Closing Verdict

CrashLoopBackOff is not a single fault and it is not a control-plane problem. It is a restart loop wrapped around any one of six unrelated causes, and the engineer who treats it as a mystery to be cleared with another restart will spend an hour where five minutes would do. The discipline that collapses the whole problem is the previous-logs rule: the crashed container already recorded how it died, so read `kubectl logs --previous` and the Last State exit code from `kubectl describe pod` before you change anything. The exit code sorts the crash into a family, 137 for the memory kill, 143 for a signal-driven stop, 1 for the application's own error, 127 for a missing command, and the previous logs name the specific cause inside that family. Match the cause to the triage table, apply the remedy that fits, and the loop ends because the reason for it is gone, not because the alarm was silenced. Scaling and restarting fix nothing here and, in the memory case, multiply the damage. Read first, then act.

## Frequently Asked Questions

### How do I find why a pod is in CrashLoopBackOff?

Run two commands. `kubectl logs <pod-name> --previous` shows the output of the container instance that just died, which holds the stack trace or fatal message. `kubectl describe pod <pod-name>` shows the Last State block with the termination reason and exit code, plus the Events list. Together they name the cause before you change anything.

### What does exit code 137 OOMKilled mean and how do I fix it?

Exit code 137 is signal 9, SIGKILL, and the reason OOMKilled means the kernel killed the process for exceeding its container memory limit. Confirm it in the Last State block of the describe output. Fix it by raising the memory limit above the observed peak usage if the demand is legitimate, or by reducing the application's memory footprint if it is leaking.

### Can a liveness probe cause CrashLoopBackOff?

Yes. A probe with timing tighter than the application's real startup, or pointed at the wrong path or port, fails against a healthy container, and the kubelet restarts it into the same failing check. The Events section shows the probe failure just before each kill, while the previous logs look healthy. Use a startup probe and align the timing and target.

### How do I read a crashing container's logs if it has already restarted?

Add the `--previous` flag: `kubectl logs <pod-name> --previous`. A plain log read targets the current instance, which in a backoff wait has no running process or has not yet reached the failure. The previous flag asks for the captured output of the prior, terminated instance, which is the run that contains the real error.

### Does a missing secret or config map cause CrashLoopBackOff?

It does when the application requires the value at startup and exits if it is absent. The previous logs usually name the missing variable or key explicitly. Confirm the secret or config map exists in the pod's namespace and that the key names referenced in the pod spec match the keys inside the object exactly, then restart the workload to apply the corrected binding.

### Why does my pod show exit code 1 with no obvious cause?

Exit code 1 is a generic application error, so the exit code alone cannot tell you the cause. The answer is always in the previous logs. Read the stack trace or fatal line there: it distinguishes an unhandled exception from a failed database connection from a configuration parse error, each of which needs a different fix.

### What does exit code 127 mean for a crashing pod?

Exit code 127 means command not found. The container could not start the program it was told to run, usually because the `command` or `args` in the pod spec name a binary that does not exist on the image or is not on the PATH. An exec format error instead points at a CPU architecture mismatch between the image and the node.

### Should I scale my deployment to stop the crash loop?

No. Adding replicas hands the same broken configuration to more copies of the workload, so a memory limit that is too low simply produces more OOMKills. Scaling treats a symptom and never the cause. Diagnose the single failing pod first with the previous logs and the exit code, fix the cause, and the loop ends for every replica.

### How do I tell CrashLoopBackOff apart from ImagePullBackOff?

The status name is the discriminator. CrashLoopBackOff means a container started and keeps dying, so the fault is in the running program or its configuration. ImagePullBackOff and ErrImagePull mean the kubelet could not fetch the image at all, so the container never started and the fault is in registry access, the image tag, or a pull rate limit.

### Why does my container keep restarting even though the logs show no error?

Two common cases. An OOMKill terminates the process by SIGKILL before it can log anything, so the logs stop abruptly with the reason OOMKilled in the describe output. Or a liveness probe is killing a healthy container, in which case the logs show a normal startup cut short by an external kill rather than an application error.

### What is the difference between exit code 137 and exit code 143?

Both are signal-based terminations. Exit code 137 is 128 plus signal 9, SIGKILL, a forced kill that the process cannot catch, typically the out-of-memory killer. Exit code 143 is 128 plus signal 15, SIGTERM, the graceful stop signal, which usually means a probe failure or a node drain asked the container to shut down.

### Can a wrong container port cause a crash loop?

Yes, indirectly. If the liveness probe targets a port the application does not listen on, the probe can never succeed and the kubelet restarts the container indefinitely, no matter how healthy the application is. Read the port the application binds in its previous logs and align the `containerPort`, the probe `port`, and any Service `targetPort` to it.

### How can I watch a pod's memory to confirm an OOMKill?

With the Metrics Server add-on enabled, `kubectl top pod <pod-name>` shows live usage you can watch climb toward the limit before a restart. For history, Azure Monitor container insights records per-container working-set memory, and a sawtooth that rises to the limit and resets at each restart is the clear fingerprint of memory exhaustion.

### Does changing the restart policy fix CrashLoopBackOff?

No. The restart policy on a Deployment is effectively Always by design, and changing it only stops the visible loop while the underlying fault remains. You would be silencing the alarm rather than putting out the fire. The correct move is to find why the container exits, using the previous logs and the exit code, and remove that cause.

### Why does my application crash on startup only inside the cluster and not locally?

Almost always a configuration or dependency difference. In the cluster the application reads values from secrets and config maps that may be missing, misnamed, or in the wrong namespace, or it cannot reach a dependency a network policy or firewall blocks. The previous logs name the missing value or the refused connection, which local runs never hit because the environment differs.

### How do I make startup tolerant of a dependency that is briefly unavailable?

Replace an immediate exit on a failed dependency connection with a bounded retry that uses a short backoff, so a database or service that is unreachable for a few seconds during a deployment causes a brief delay rather than a crash. Pair this with a startup probe so the kubelet waits for the application to finish connecting before it begins liveness checks.

### What is the fastest first step when I see CrashLoopBackOff?

Read the Last State exit code from `kubectl describe pod <pod-name>`. The number alone sorts the crash into a family in seconds: 137 with OOMKilled is memory, 143 is a signal stop often from a probe, 127 is a missing command, and 1 sends you to `kubectl logs --previous` for the application's own error message. Let that single number direct everything that follows.
