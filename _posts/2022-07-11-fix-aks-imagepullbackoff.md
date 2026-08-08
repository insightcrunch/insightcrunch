---
layout: post
title: "Fix AKS ImagePullBackOff and ErrImagePull"
page_title: "Fix AKS ImagePullBackOff and ErrImagePull: Read the Events Line, Find the Real Cause, and Apply the Exact Fix on Azure Kubernetes Service"
date: 2022-07-11
categories: ["Technology"]
tags: ["Azure", "AKS", "ImagePullBackOff", "ErrImagePull", "Troubleshooting", "Kubernetes", "Cloud Computing"]
excerpt: "ImagePullBackOff in AKS means the kubelet could not pull your image. Read the pod events line to find the real cause, then apply the one matching fix."
image: "/assets/images/blog/blog-99.webp"
reading_time: 65
author: "alex-cunningham"
last_updated: 2022-07-11
lang: en
---
A pod sits in `ImagePullBackOff`, the deployment never reaches ready, and the temptation is immediate: rotate the registry credentials, recreate the secret, redeploy, and hope. That guess is wrong far more often than it is right, because `ImagePullBackOff` is not a single fault. It is a status the kubelet shows after it tried to pull a container image, failed, and decided to wait before trying again. The word that matters sits one line lower, under Events, where the kubelet records exactly why the last attempt failed. An unauthorized pull, a tag that does not exist, a registry that is rate limiting, and a host name that will not resolve all surface as the same yellow status in `kubectl get pods`, and all four have different fixes. Reading the events line first is the difference between a five-minute correction and an afternoon of rotating secrets that were never the problem.

This guide treats `ImagePullBackOff` and its companion `ErrImagePull` as a diagnosis you perform on the cluster rather than a verdict you accept. You will learn what the two statuses mean and how they relate, where the real reason is written, how to route each Events message to its cause, and how to confirm and fix every one of the recurring cases engineers hit on Azure Kubernetes Service: an Azure Container Registry that was never attached to the cluster, a Docker Hub anonymous pull that ran into the rate limit, a typo in the tag, a `:latest` that was overwritten or deleted, an `imagePullSecret` created in the wrong namespace, a private registry blocked by a firewall, and registry DNS that fails from the node.

![Fixing AKS ImagePullBackOff and ErrImagePull root causes - Insight Crunch](/assets/images/blog/blog-99.webp)

The shape of the fix is always the same: read the Events line, classify the message into name, tag, authentication, or reachability, confirm the cause with one command, apply the matching remedy, and verify the pod reaches running. Everything below builds that loop and gives you the command for each step. If you want the broader picture of how the scheduler, the node, and the kubelet cooperate to place and start a pod, the [Azure Kubernetes Service deep dive](/2022/01/17/azure-kubernetes-service-aks-explained/) lays out the node-and-pull model that this troubleshooting sits on top of.

## What ImagePullBackOff and ErrImagePull actually mean

When you create a pod, the Kubernetes scheduler places it on a node, and from that point the kubelet on that node owns the pod's lifecycle. Before any container can start, the kubelet must have the container image present in the node's local image store. If the image is not already cached on the node, the kubelet calls the container runtime to retrieve it from the registry named in the pod spec. That retrieval is the pull. When the pull succeeds, the kubelet starts the container. When the pull fails, the kubelet records the failure and enters a wait-and-retry loop, and that loop is what the two statuses describe.

`ErrImagePull` is the status of the most recent failed attempt. The kubelet asked the runtime to fetch the image, the runtime returned an error, and the kubelet surfaced that error as `ErrImagePull` on the container. It is the raw result of one failed try.

`ImagePullBackOff` is what the status becomes once the kubelet has failed enough times to start delaying its retries. Rather than hammer the registry on a tight loop, the kubelet backs off, doubling the wait between attempts up to a ceiling. The container is still not running, the kubelet is still trying, but it is now spacing those tries out. So the two are stages of the same event: the runtime fails the fetch, the container shows `ErrImagePull`, and after repeated failures the same container settles into `ImagePullBackOff` while the kubelet keeps retrying on a growing delay.

### What is the difference between ErrImagePull and ImagePullBackOff?

`ErrImagePull` is the immediate result of one failed pull attempt. `ImagePullBackOff` is the state the kubelet enters after several failures, when it begins spacing out retries with an exponential delay. They report the same underlying problem at different stages, so you diagnose both the same way: read the Events line under the pod.

The practical consequence is that you should not read meaning into which of the two you see. A pod observed early may show `ErrImagePull`, and the same pod observed a minute later shows `ImagePullBackOff`, with nothing about the fault having changed. Neither status names the cause. Both are containers for a cause that is written elsewhere, and the next section is about where.

The backoff itself matters in one situation. Because the kubelet doubles its retry interval, a pod that has been failing for several minutes is not retrying every few seconds anymore. After you apply a fix, the pod may sit in `ImagePullBackOff` for a while before the kubelet's next scheduled attempt, which can make a correct fix look like it did nothing. In that case, deleting the pod so a fresh one is created forces an immediate pull rather than waiting out the backoff window, which is the single legitimate reason to recreate a pod here. Recreating the pod as a fix for the underlying fault, by contrast, accomplishes nothing, because the new pod hits the same registry with the same spec and fails the same way.

To reason about pull failures well, it helps to hold the right model of what a pull actually does. A container image is not one file. It is a manifest that lists an ordered set of compressed layers plus a configuration object, and the digest in the manifest uniquely identifies that exact set of bytes. When the runtime fetches an image, it reads the manifest, downloads each layer the node does not already hold, verifies each layer's digest, and assembles them into the root filesystem the container will run on. Every step in that sequence can fail independently. The registry can refuse to hand over the manifest because authentication failed. The manifest can be absent because the tag does not exist. The download can stall because the network path is blocked. A layer can fail its digest check because the transfer was corrupted. The kubelet collapses all of those distinct failures into the single `Failed to pull image` event, but the descriptive text it appends preserves which step broke, which is exactly why reading that text is the whole game.

The node's local image store is the other half of the model. Each node keeps a cache of the layers it has already downloaded, and the kubelet consults that cache before reaching out to the registry. This is why `imagePullPolicy` matters so much and why two nodes can behave differently for the same image reference. Under the default `IfNotPresent` policy, a node that already holds every layer of the requested image starts the container without contacting the registry at all, so a node with a warm cache can succeed while a freshly scaled node, with an empty cache, performs a real pull and surfaces whatever fault is waiting. The store is also subject to garbage collection: when disk pressure crosses a threshold, the kubelet evicts unused images to reclaim space, which can quietly remove a layer set that had been masking a registry problem. A pull that worked for a month and then failed after a node ran low on disk is often this, the cache that hid the fault was reclaimed, and the underlying registry or reference issue was there all along.

## Where the real diagnosis lives

The whole method rests on one habit: read the cluster's own record of the failure before changing anything. The kubelet writes a human-readable reason for each failed pull into the pod's events, and that reason is the diagnosis. Three commands surface it.

The first is `kubectl describe pod`, which prints the pod's full status including the Events list at the bottom. The Events list is a timeline of what the kubelet did and what went wrong, newest at the end.

```bash
kubectl describe pod <pod-name> -n <namespace>
```

Scroll to the Events section. You are looking for a `Warning` event with reason `Failed` and a message that begins with `Failed to pull image`. That message is the payload. A few representative lines, reproduced as the literal strings the kubelet emits:

```
Failed to pull image "myacr.azurecr.io/api:v3": rpc error: code = Unknown
  desc = failed to pull and unpack image "myacr.azurecr.io/api:v3":
  failed to resolve reference "myacr.azurecr.io/api:v3": failed to authorize:
  ... 401 Unauthorized
```

```
Failed to pull image "docker.io/library/nginx:latest": ... toomanyrequests:
  You have reached your pull rate limit.
```

```
Failed to pull image "myacr.azurecr.io/api:v99": ... not found:
  manifest unknown
```

```
Failed to pull image "myacr.azurecr.io/api:v3": ... dial tcp: lookup
  myacr.azurecr.io: no such host
```

Each of those four messages points at a different fault, and the words that classify them are right there in plain text: `401 Unauthorized`, `toomanyrequests`, `manifest unknown` or `not found`, and `no such host`. The kubelet is telling you the cause. The mistake most engineers make is to skip past the message, see the yellow status, and act on a hunch.

The second command is `kubectl get events`, which shows events across a namespace sorted by time. It is useful when many pods are failing at once and you want to see whether they share one cause.

```bash
kubectl get events -n <namespace> --sort-by=.lastTimestamp
```

The third is the quick status check that started the investigation, `kubectl get pods`, with the wide output so you can see which node each failing pod landed on. That node column matters in two of the cases below, because a pull can succeed on one node and fail on another.

```bash
kubectl get pods -n <namespace> -o wide
```

### Reading the full container status block

The Events list is the headline, but the container status block in `kubectl describe pod` carries detail that confirms what the events say and sometimes adds the precise registry response. Inside the describe output, each container has a `State` and a `Last State`, and during a pull failure the relevant container reports a `State` of `Waiting` with a `Reason` of either `ErrImagePull` or `ImagePullBackOff`, and a `Message` field that frequently holds the same registry text the event carries. Reading both together removes ambiguity: the `Reason` classifies the stage, and the `Message` carries the registry's own words.

```
Containers:
  api:
    State:          Waiting
      Reason:       ImagePullBackOff
    Last State:     Waiting
      Reason:       ErrImagePull
      Message:      failed to authorize: ... 401 Unauthorized
    Ready:          False
    Restart Count:  0
```

Two details in that block are worth internalizing. A `Restart Count` of zero alongside an image-pull reason confirms the container never started, which separates a pull failure from a crash that happens after start. And the transition you can see in the block, `Last State` showing `ErrImagePull` while the current `State` shows `ImagePullBackOff`, is the two-stage progression made visible: the previous attempt errored, and the current state is the backoff. If instead you find a `Last State` of `Terminated` with an exit code, the image is pulling fine and the container is crashing after start, which is a different problem entirely and is covered later under related failures.

You can also pull just the container statuses as structured output when you want the registry message without scrolling, which is handy in scripts and in a busy namespace:

```bash
kubectl get pod <pod-name> -n <namespace> \
  -o jsonpath='{.status.containerStatuses[*].state.waiting.message}'
```

That one line prints the waiting message for every container in the pod, so a single command hands you the registry's own explanation. Whichever route you take, the destination is the same: the registry's text, classified into authentication, name or tag, rate limiting, or reachability.

### Does ImagePullBackOff mean the node itself is broken?

Almost never. `ImagePullBackOff` is about the kubelet failing to fetch a specific image, not about the node being unhealthy. A node that runs other pods fine but fails this one has a problem with the image reference, the registry authentication, or the network path to that registry, not with the node. Confirm node health separately with `kubectl get nodes` before suspecting the node.

That distinction saves real time. If `kubectl get nodes` shows every node `Ready` and other workloads on the same node are running, the node is not your problem, and cordoning, draining, or restarting it is wasted effort. The fault is in the four-line message you just read, and it belongs to one of the causes that follow.

### The InsightCrunch image-pull cause table

This is the artifact to bookmark. Read the Events message, find its signature in the left column, and the table routes you to the cause and the fix. The sections after it expand each row with the confirming command and the tested remedy.

| Events message signature | What it means | Most likely cause | The fix |
|---|---|---|---|
| `401 Unauthorized` / `failed to authorize` | The registry rejected the credentials, or there were none | Private registry not authenticated: ACR not attached to AKS, or a missing or wrong `imagePullSecret` | Attach ACR to the cluster, or create and reference a correct `imagePullSecret` in the pod's namespace |
| `manifest unknown` / `not found` | The registry has no image at that name and tag | A typo in the repository or tag, or a tag that was overwritten or deleted | Correct the tag, push the missing tag, or pin a digest so the reference cannot drift |
| `toomanyrequests` / `pull rate limit` | The registry is throttling anonymous or free-tier pulls | Docker Hub anonymous rate limit hit by nodes sharing one public IP | Pull through ACR (import or cache), or authenticate the pull with a Docker Hub account |
| `no such host` / `server misbehaving` | The node cannot resolve the registry host name | DNS failure from the node, often a private registry with a private endpoint and missing DNS | Fix the DNS chain so the node resolves the registry FQDN |
| `dial tcp ... i/o timeout` / `connection refused` | The host resolves but the node cannot reach it | A firewall, egress restriction, or NSG blocking the node-to-registry path | Allow egress to the registry, or fix the private link path |
| `desc = no match for platform` | The manifest has no image for the node's architecture | An amd64-only image scheduled onto an arm64 node, or the reverse | Build a multi-arch image, or constrain scheduling to matching nodes |

The namable claim is simple and worth stating plainly: the events-line rule for `ImagePullBackOff` says the real cause is the message under Events in `describe pod`, so reading it, unauthorized versus not found versus rate limited versus unreachable, replaces all guessing. Every section below is one row of that table made operational.

## Cause one: a wrong image name or tag

The most common reason a pull fails has nothing to do with credentials or networking. The image simply is not where the pod spec says it is. The repository name has a typo, the tag was never pushed, the tag was overwritten so the old reference no longer resolves, or a `:latest` that something deleted now points at nothing. The Events message for this class reads `manifest unknown` or `not found`, and it is unambiguous: the registry answered, the authentication was accepted, and the registry reported that it holds no image at that coordinate.

### Can a wrong image tag cause ImagePullBackOff?

Yes, and it is one of the most frequent causes. If the tag in the pod spec does not exist in the repository, the registry returns `manifest unknown` and the kubelet reports the failure as `ImagePullBackOff`. A typo, a tag never pushed, or a tag overwritten or deleted all produce it. The fix is to correct the reference, not to touch credentials.

Confirm it by reading the failing reference straight out of the message and checking what the registry actually holds. For an Azure Container Registry, list the tags on the repository and compare:

```bash
az acr repository show-tags \
  --name myacr \
  --repository api \
  --output table
```

If the spec asks for `api:v3` and the listing shows `v1`, `v2`, and `v2.1` but no `v3`, the reference is the fault. The same check against a public registry is a manifest inspection:

```bash
docker manifest inspect docker.io/library/nginx:1.27
```

A missing tag returns a not-found error rather than a manifest, which confirms the reference is bad before you ever touch the cluster.

The fix depends on which flavor of missing you have. If it is a typo, correct the image reference in the deployment and reapply. If the tag was genuinely never built, push it. If something deletes or moves the tag underneath you, the durable correction is to stop referencing mutable tags in production at all and pin a digest, which the registry cannot reassign:

```yaml
containers:
  - name: api
    image: myacr.azurecr.io/api@sha256:9b2a...e41
```

A digest reference is immutable. The same bytes will resolve forever, so a pipeline that overwrites `:latest` or retags `:stable` can never silently change what your pods run, and a pull that worked yesterday cannot start failing today because someone moved a tag. This is the single most effective prevention for the entire tag-drift family of `ImagePullBackOff`, and it costs nothing but a small change in how your build records the image it produced.

One subtlety trips people here. The default `imagePullPolicy` is `IfNotPresent` for any tag other than `:latest`, and `Always` for `:latest`. A node that already cached `api:v2` will keep using its cached copy even after you push a new `api:v2`, because `IfNotPresent` means the kubelet does not re-fetch a tag it already has. That is not an `ImagePullBackOff`, it is the opposite problem of a stale image running, but it is the reason teams reach for `:latest` and then inherit the tag-drift failures above. Pinning a digest solves both: the kubelet always has the right bytes, and there is no mutable tag to drift.

To see the whole loop concretely, here is the failure manufactured and then resolved. Deploy a workload that references a tag the registry does not hold:

```bash
kubectl create deployment api --image=myacr.azurecr.io/api:v99 -n demo
kubectl get pods -n demo
```

The pod appears and within moments reports the failure:

```
NAME                   READY   STATUS             RESTARTS   AGE
api-7d9f6c8b5-h2k4l    0/1     ImagePullBackOff   0          25s
```

Read the events to confirm the class rather than assume it:

```bash
kubectl describe pod -l app=api -n demo | sed -n '/Events:/,$p'
```

```
Warning  Failed  ...  Failed to pull image "myacr.azurecr.io/api:v99":
  ... manifest unknown: manifest tagged by "v99" is not found
```

The `manifest unknown` text settles it: this is a name-or-tag fault, not authentication. Verify against the registry's real inventory:

```bash
az acr repository show-tags --name myacr --repository api --output table
```

If the listing shows `v1` and `v2` but no `v99`, repoint the deployment at a tag that exists and the pull succeeds:

```bash
kubectl set image deployment/api api=myacr.azurecr.io/api:v2 -n demo
kubectl rollout status deployment/api -n demo
```

The rollout completing is the verification step, and it proves the fix without any guesswork about credentials. Notice that nothing in this loop touched a secret, a role, or the network, because the events line told you the fault lived in the reference.

For the durable version, capture the digest your build produced and deploy that, so the deployment manifest records exactly which bytes it runs. A build pipeline that pushes an image already knows the digest the registry returned, and recording it turns the deploy into a reference that cannot drift:

```bash
DIGEST=$(az acr repository show --name myacr \
  --image api:v2 --query "digest" -o tsv)
kubectl set image deployment/api \
  api=myacr.azurecr.io/api@${DIGEST} -n demo
```

From that point the workload is pinned to an immutable artifact, and the entire `manifest unknown` family of pull failures cannot reach it, because there is no longer a mutable label between the deployment and the bytes it depends on.

## Cause two: a private registry the cluster cannot authenticate to

This is the cause that drives the most wasted effort, because the Events message, `401 Unauthorized` or `failed to authorize`, looks like a credentials problem, and the reflex is to rotate credentials. On AKS pulling from Azure Container Registry, the real cause is usually not bad credentials at all. It is that the cluster has no credentials to present, because the registry was never attached to the cluster and no `imagePullSecret` was supplied.

### Why does AKS show ImagePullBackOff pulling from ACR?

The usual reason is that the registry is not attached to the cluster, so the cluster's kubelet identity has no permission to pull from it. The Events line reads `401 Unauthorized`. Attaching the ACR to the AKS cluster grants the cluster's managed identity the pull role on that registry, and most private-registry `ImagePullBackOff` failures clear once the attachment is in place.

Here is what is actually happening. A pull from ACR has to authenticate. AKS can authenticate to ACR using the cluster's own managed identity, but only if that identity has been granted the role that permits pulling from the registry. The clean way to grant it is to attach the registry to the cluster, which performs the role assignment for you. If you created the cluster and the registry separately and never attached them, the kubelet has no identity ACR will accept, every pull comes back `401`, and no amount of secret rotation helps because there is no secret in play.

It is worth being precise about which identity does the pulling, because the precision is what lets you confirm the fix rather than hope for it. An AKS cluster has more than one identity. The control-plane identity manages Azure resources on the cluster's behalf, while a separate kubelet identity is the one the nodes use to pull images. When you attach a registry, Azure assigns the `AcrPull` role to that kubelet identity on the registry's scope, which is what gives the nodes permission to fetch images. So the question behind a `401` from ACR is always the same: does the kubelet identity hold `AcrPull` on this registry? You can answer it directly by reading the role assignments on the registry and checking for the kubelet identity, and the attach operation exists precisely so you do not have to construct that role assignment by hand.

Confirm it directly. Azure provides a purpose-built check that tests whether the cluster can actually authenticate to and reach the registry from inside the cluster:

```bash
az aks check-acr \
  --resource-group myRG \
  --name myAKS \
  --acr myacr.azurecr.io
```

This command validates the authentication path and the network path together and reports which one failed, which makes it the fastest single confirmation for this cause. Verify its current behavior and any version requirements against the official Azure CLI reference at read time, since the tool evolves, but its role in the workflow is stable: it tells you whether the cluster, as configured today, can pull from that registry.

The fix for the unattached case is to attach the registry to the cluster, which assigns the pull permission to the cluster's identity:

```bash
az aks update \
  --resource-group myRG \
  --name myAKS \
  --attach-acr myacr
```

After the attachment completes, delete the failing pod so the kubelet pulls again immediately rather than waiting out its backoff, then confirm the pod reaches running:

```bash
kubectl delete pod <pod-name> -n <namespace>
kubectl get pods -n <namespace> -w
```

A worked version of this case makes the confirmation concrete. You inherit a cluster, deploy a workload from an ACR that someone provisioned separately, and every pod reports `ImagePullBackOff`. The events line reads `401 Unauthorized`, which classifies it as authentication. Before assuming the credentials are wrong, you run `az aks check-acr` and it reports that authentication failed while the network path was fine, which narrows it to the cluster lacking permission rather than a blocked path. You attach the registry with `az aks update --attach-acr`, delete the stuck pods to skip the backoff, and watch them transition to running. The whole sequence is four commands and contains no guessing, because each step confirmed the next: the events line said authentication, the check said the auth leg specifically, and the attach addressed exactly that leg.

If the registry is geo-replicated across regions, attaching still grants pull access globally, and the nodes pull from the replica nearest their region automatically, so geo-replication does not introduce a separate authentication step; it is the same `AcrPull` grant on the registry, and the replica selection is transparent to the pod. That detail matters only because engineers sometimes suspect a replica when a `401` appears in one region, when in fact the authentication model is identical across all replicas and the regional difference, if any, is a network or DNS one rather than an auth one.

There is a second authentication path for cases where attaching the registry is not appropriate, for example a registry that is not ACR, or a registry shared across clusters where you would rather grant a scoped credential than the cluster identity. In that path you create a Kubernetes secret of type `docker-registry` holding the credentials and reference it from the pod as an `imagePullSecret`:

```bash
kubectl create secret docker-registry regcred \
  --docker-server=myregistry.example.com \
  --docker-username=<user> \
  --docker-password=<token> \
  --namespace=<namespace>
```

```yaml
spec:
  imagePullSecrets:
    - name: regcred
  containers:
    - name: api
      image: myregistry.example.com/api:v3
```

The deep treatment of the registry-authentication model itself, the pull role, the difference between the cluster identity and a kubelet identity, the admin account and why it is discouraged for production, lives in the dedicated guide on [fixing an unauthorized pull from Azure Container Registry](/2023/02/06/fix-acr-pull-unauthorized/). If you want to remove long-lived secrets from this picture entirely and pull using a federated identity, the walkthrough on [setting up workload identity in AKS](/2023/05/29/configure-aks-workload-identity/) covers the identity angle. For the `ImagePullBackOff` you are staring at right now, the table's row is enough: a `401` on an ACR pull means the cluster cannot authenticate, and attaching the registry or supplying a correct pull secret fixes it.

## The imagePullSecret namespace trap

When teams do reach for an `imagePullSecret` and it still does not work, the cause is almost always the namespace. A Kubernetes secret is a namespaced object. A secret named `regcred` created in the `default` namespace does not exist as far as a pod in the `production` namespace is concerned, and a pod can only reference a pull secret that lives in its own namespace. So the pull keeps failing with `401`, the secret looks present in `kubectl get secrets`, and the disconnect is that you are looking at the secret in one namespace while the pod runs in another.

### Why is my imagePullSecret not working in AKS?

The most common reason is that the secret lives in the wrong namespace. A pull secret must exist in the same namespace as the pod that references it, because secrets are namespaced objects. A secret in `default` is invisible to a pod in `production`. Recreate the secret in the pod's namespace, confirm the pod spec references it by name, and the pull authenticates.

Confirm it by checking which namespace the secret is in against where the pod runs:

```bash
kubectl get secret regcred -n <pod-namespace>
```

If that returns `NotFound` while the same query against `default` returns the secret, the namespace mismatch is your fault. Two further checks catch the other ways a pull secret silently fails. First, confirm the pod actually references the secret, because a secret that exists but is not named in `imagePullSecrets` is never used:

```bash
kubectl get pod <pod-name> -n <namespace> \
  -o jsonpath='{.spec.imagePullSecrets[*].name}'
```

Second, confirm the secret's contents are valid by decoding the embedded docker config and checking that the server, username, and token match the registry you are pulling from. A pull secret built against the wrong server, or with a token that has expired, authenticates against nothing and produces the same `401`.

The fix is to create the secret in the pod's namespace and reference it there. If many namespaces need the same registry, create the secret in each, or attach the registry to the cluster so the cluster identity handles authentication and individual pull secrets become unnecessary. The cluster-identity path sidesteps the namespace trap entirely, which is one more reason attaching ACR is the cleaner default for an Azure-native setup.

There is a middle option that removes the per-pod boilerplate without abandoning pull secrets. A pull secret can be attached to a service account, and every pod that runs under that service account then inherits the secret without naming it in its own spec. The default service account in a namespace can carry the pull secret, so a single patch covers every workload in that namespace that does not override it:

```bash
kubectl patch serviceaccount default -n <namespace> \
  -p '{"imagePullSecrets": [{"name": "regcred"}]}'
```

After that patch, a new pod in the namespace pulls using `regcred` even though its spec lists no `imagePullSecrets`, because the service account contributes them. This is useful when you control the namespace but not every manifest deployed into it, and it removes the most common omission, a spec that forgot to reference the secret. The one caveat is that it applies to pods created after the patch, not to existing ones, so recreate the affected pods to pick it up. The namespace boundary still holds, though: the service account, the secret, and the pods all live in the same namespace, so the patch does nothing for pods in a different one.

## Cause three: Docker Hub rate limiting

A pull that worked for weeks suddenly fails across several pods with `toomanyrequests: You have reached your pull rate limit`, and nothing in your configuration changed. This is the Docker Hub rate limit, and it surprises AKS users because the way a cluster pulls makes it far easier to hit than a single developer ever would.

### Does the Docker Hub rate limit cause ImagePullBackOff?

Yes. Docker Hub limits anonymous and free-tier pulls over a rolling window, and when a cluster exceeds it the registry returns `toomanyrequests`, which the kubelet reports as `ImagePullBackOff`. AKS nodes often pull anonymously through a shared outbound IP, so a busy cluster hits the limit collectively. Pulling through ACR or authenticating the pull resolves it.

The mechanism is what makes this counterintuitive. Docker Hub meters pulls by the source IP for anonymous requests. An AKS cluster's nodes commonly share one outbound public IP through the load balancer or a NAT gateway, so every anonymous pull from every node on the cluster counts against the same bucket. A node scale-up, a rollout that restarts many pods, or a few CronJobs that all reference public images can drain a shared anonymous quota in minutes, and then every fresh pull from that cluster gets throttled at once. The exact thresholds change, so check Docker's current published limits at read time rather than trusting a number, but the pattern is durable: shared IP plus anonymous pulls plus a busy cluster equals collective throttling.

Confirm it by reading the message, which names the throttle explicitly, and by noticing that the failures cluster around a scaling or rollout event and clear partly as the rolling window resets. You can also see the limit headers on a manual pull from a node or a debug pod, where Docker returns the remaining quota in the response.

There are two durable fixes, and both remove the dependence on anonymous Docker Hub pulls. The stronger one for an Azure setup is to stop pulling public images from Docker Hub at runtime at all and instead import them into your own ACR, then pull from there:

```bash
az acr import \
  --name myacr \
  --source docker.io/library/nginx:1.27 \
  --image nginx:1.27
```

After the import, change the pod spec to reference `myacr.azurecr.io/nginx:1.27` and the cluster pulls from your private registry, which you control, with no shared anonymous quota in the path. This also insulates you from a public image being retagged or removed upstream, which is its own source of the `manifest unknown` failures in cause one.

The lighter fix is to authenticate the Docker Hub pull with an account, which raises the limit above the anonymous tier. You create a `docker-registry` secret with Docker Hub credentials and reference it as an `imagePullSecret`, exactly as in cause two, so the pulls count against an authenticated quota rather than the shared anonymous one. The import-to-ACR approach is the better long-term posture because it brings the image fully inside your control, but the authenticated pull is a fast unblock when you need the cluster healthy now.

For public images you depend on continuously rather than import once, ACR offers a cache that keeps a local copy current against the upstream source, so pods pull from your registry while the cache handles refreshing from Docker Hub behind the scenes. This combines the control of importing with the freshness of pulling upstream, and it means a single configured cache rule can cover an image your fleet pulls constantly without each pull touching the shared anonymous quota. Whether you import on demand or configure a cache, the principle is identical: the runtime path your nodes take should terminate at a registry you own, not at a metered public endpoint shared with every other anonymous puller behind your cluster's IP.

A worked version shows how cleanly the import fix lands. A nightly batch of CronJobs all reference `docker.io/library/python:3.12`, and one morning every job pod is stuck in `ImagePullBackOff`. The events line reads `toomanyrequests: You have reached your pull rate limit`, which is unmistakable. You import the image once into your registry and repoint the jobs:

```bash
az acr import --name myacr \
  --source docker.io/library/python:3.12 --image python:3.12
```

You change the CronJob template to pull `myacr.azurecr.io/python:3.12`, the next run pulls from your registry with no shared bucket in the path, and the failures stop. The fix took one import and one reference change, and it also removed the future risk of the upstream tag being moved or removed, which would have produced a `manifest unknown` down the line. One unblock addressed both the rate limit in front of you and a latent reference risk behind it.

## Cause four: a deleted or overwritten tag

This case overlaps with cause one but deserves its own treatment because of how it appears: a pull that succeeded yesterday starts failing today with `manifest unknown`, and nobody changed the pod spec. The reference did not change. What changed is the registry. A mutable tag like `:latest`, `:stable`, or a version that a pipeline reuses was overwritten or deleted, so the coordinate the pod has always referenced no longer resolves to anything.

The trap is that the failure is intermittent across the fleet. Nodes that already cached the old `:latest` keep running it under `IfNotPresent`, so part of your deployment is fine while new pods, scheduled onto fresh nodes or after a scale-up, fail to pull. You see a deployment that is half healthy, which does not look like an image problem at first glance, and the node column in `kubectl get pods -o wide` is what reveals that the failures track the nodes without the cached copy.

Confirm it by listing the registry's current tags, as in cause one, and by checking the tag's history if your registry records it. For ACR, the repository show and tag listing reveal whether the referenced tag still exists and when it was last updated:

```bash
az acr repository show \
  --name myacr \
  --repository api \
  --output table
```

If the tag is gone or its timestamp is newer than the last successful pull, the registry moved underneath you. The fix in the moment is to push the missing tag back or repoint the deployment at a tag that exists. The fix that ends the recurrence is the digest pin from cause one. A workload that references images by digest is immune to this entire failure mode, because there is no mutable label for a pipeline to overwrite. Teams that adopt digest pinning in their deployment manifests stop seeing the half-healthy-deployment version of `ImagePullBackOff` almost entirely.

## Cause five: the registry is unreachable on the network

When the Events message reads `dial tcp ... i/o timeout`, `connection refused`, or `no route to host`, authentication never even got a chance. The node could not open a connection to the registry. The credentials may be perfect and the tag may exist, but the network path from the node to the registry is blocked. This is common with private registries reached over a private endpoint, with clusters behind a firewall or a NAT gateway that enforces egress rules, and with ACR configured to refuse public network access.

The relevant facts are about reachability, not identity. A registry that lives behind a private endpoint is only reachable from networks that can route to that private endpoint and resolve its private address, which for a node means the cluster's virtual network must be peered or linked correctly and the egress rules must permit the traffic. An ACR with public network access disabled rejects any pull that does not arrive over its private endpoint, so a node that tries to reach it over the public path is refused outright.

Confirm it by testing connectivity from inside the cluster, not from your laptop, because your laptop's network path is irrelevant. Launch a debug pod on the affected node and test the registry endpoint:

```bash
kubectl run netcheck --rm -it --image=nicolaka/netshoot \
  --overrides='{"spec":{"nodeName":"<the-failing-node>"}}' \
  -- /bin/bash
```

From inside, test whether the node can reach the registry's HTTPS endpoint:

```bash
nc -vz myacr.azurecr.io 443
curl -v https://myacr.azurecr.io/v2/
```

A timeout or refusal here confirms a reachability problem rather than an authentication one, and it tells you the fault is in the firewall, the egress configuration, the NSG, or the private link path rather than in any secret. The `az aks check-acr` command from cause two also reports the network leg separately from the authentication leg, so a clean auth result paired with a failed network result points straight here.

The fix is to open the path. For a cluster behind Azure Firewall or a restrictive egress setup, the node's outbound traffic to the registry FQDN must be allowed, which for ACR means permitting the registry endpoint and the data endpoints it redirects to. For a private-endpoint registry, the cluster's virtual network must be able to route to and resolve the private endpoint, which is as much a DNS problem as a routing one and leads directly into cause six. The principle to hold is that a reachability failure is fixed at the network layer, and widening registry permissions or rotating credentials cannot touch it.

The data-endpoint detail is the one that catches careful engineers off guard, so it is worth spelling out. An ACR pull does not happen entirely against the registry's login endpoint. The login endpoint handles authentication and hands back the manifest, but the layer blobs are served from separate data endpoints, and a firewall rule that allows only the login FQDN while blocking the data endpoints produces a pull that authenticates, retrieves the manifest, and then stalls fetching layers with an `i/o timeout`. The symptom looks contradictory, the credentials clearly worked yet the pull still failed, and the resolution is to allow egress to the data endpoints as well. ACR can be configured with dedicated data endpoints whose FQDNs are stable and regional, which makes them straightforward to enumerate in a firewall allow list rather than relying on broad wildcard rules. When you build the egress policy for a locked-down cluster, the rule of thumb is that both the registry's login FQDN and its data FQDNs must be reachable, or the pull breaks partway through in a way that masquerades as an authentication success.

Network security groups add a parallel trap. An NSG on the node subnet that restricts outbound traffic can block the pull just as a firewall does, and because an NSG attaches at both the subnet and the NIC level, the effective rule is the combination of the two, which is easy to misread when only one layer is inspected. If the connectivity test from the node fails while the firewall policy looks permissive, check the effective outbound security rules on the node subnet before concluding the path is open. The confirming test is always the same in-cluster connectivity probe, because it exercises the exact path the kubelet uses, and a tool on your workstation cannot reproduce the node's routing, its NSGs, or its egress device.

A worked version makes the data-endpoint trap memorable. A locked-down cluster pulls from a private-endpoint ACR, authentication is confirmed working by `az aks check-acr`, yet pods still report `ImagePullBackOff` with an `i/o timeout` partway through the pull. The events line shows the manifest was retrieved but a layer fetch timed out, which is the signature of blocked data endpoints. You launch a debug pod on the failing node and test both the login endpoint and a data endpoint:

```bash
kubectl run netcheck --rm -it --image=nicolaka/netshoot \
  --overrides='{"spec":{"nodeName":"aks-pool1-31-3"}}' \
  -- bash -c "nc -vz myacr.azurecr.io 443; nc -vz myacr.<region>.data.azurecr.io 443"
```

The login endpoint connects and the data endpoint times out, which confirms the diagnosis precisely. You add the data endpoint FQDNs to the firewall allow list, rerun the test until both connect, delete the stuck pods, and the pulls complete. The instructive part is that authentication was never the problem despite the credentials being valid; the path to the bytes was. Only the connectivity test on the exact endpoint that was failing made that visible, which is why testing from inside the cluster, on the failing node, against the specific endpoint, beats reasoning about the firewall policy from a diagram.

## Cause six: registry DNS does not resolve from the node

The message `no such host` or `server misbehaving` means the node could not turn the registry's host name into an address. Without a resolved address there is nothing to connect to, so the pull fails before authentication and before any connection attempt. On AKS this most often appears with a private-endpoint registry, where the public DNS name must resolve to the private address from inside the virtual network, and the private DNS zone that makes that happen is missing, unlinked, or not wired into the cluster's resolution path.

The relevant behavior is that a registry behind a private endpoint keeps its normal public FQDN, but that FQDN must resolve to the private IP when queried from the cluster's network. A private DNS zone for the registry, linked to the cluster's virtual network, is what provides that mapping. If the zone is absent, the FQDN either fails to resolve or resolves to the public IP that the private-only registry then refuses, and either way the pull fails.

Confirm it from inside the cluster, again on the affected node, because resolution depends on the node's configured resolver:

```bash
kubectl run dnscheck --rm -it --image=nicolaka/netshoot \
  -- nslookup myacr.azurecr.io
```

If the lookup fails outright with `no such host`, the resolution chain is broken. If it returns a public address for a registry you know is private-only, the private DNS zone is not in the path. Either result confirms DNS as the cause rather than authentication or a firewall.

The fix is to repair the resolution chain so the node resolves the registry FQDN to the address it should reach. For a private-endpoint ACR that means the private DNS zone exists, is linked to the cluster's virtual network, and contains the record for the registry, and that the cluster's DNS settings route queries through a resolver that consults that zone. The detailed mechanics of private resolution, custom DNS servers, forwarders, and zone links are a networking topic in their own right, but for this pull failure the confirmation is the `nslookup` from the node and the fix is making that lookup return the right address.

A few specifics turn that principle into action. The private DNS zone for an ACR private endpoint follows a well-known name for the registry service, and the private endpoint, when created with the integration enabled, registers the registry's record into that zone automatically. The link from the zone to the virtual network is the step most often missing: a zone can exist and hold the right record, but if it is not linked to the cluster's virtual network, queries from the nodes never consult it and resolution falls back to public, which a private-only registry then refuses. So the two things to verify are that the zone contains a record for the registry FQDN and that a virtual network link ties that zone to the cluster's network.

The resolver path inside the cluster adds one more hop to keep in mind. Pods and nodes resolve names through the cluster's DNS, which forwards names it does not own to the upstream resolver configured for the node's network, and that upstream is what must reach the private zone. When a custom DNS server sits in that chain, it needs a conditional forwarder or a rule that sends the registry's zone queries to the Azure-provided resolver that can see the private zone, otherwise the custom server answers with the public address. The clean confirmation remains the node-level `nslookup`: if it returns the private address, the whole chain is intact from the node's perspective, and if it returns the public address or fails, you walk the chain from the node's resolver outward until you find the hop that does not know about the private zone. Because this failure resolves before authentication and before any connection, no credential or firewall change can fix it; only making the name resolve correctly will.

A worked version ties the hops together. A team locks down a registry behind a private endpoint and immediately every pull fails with `no such host`. You run the in-cluster lookup on a failing node:

```bash
kubectl run dnscheck --rm -it --image=nicolaka/netshoot \
  -- nslookup myacr.azurecr.io
```

The lookup returns the public address rather than the private one, which means the node's resolver is not consulting the private zone. You check whether the private DNS zone for the registry exists and whether it is linked to the cluster's virtual network, and you find the zone present with the correct record but no link to the cluster network. Adding the virtual network link is the fix:

```bash
az network private-dns link vnet create \
  --resource-group myRG \
  --zone-name privatelink.azurecr.io \
  --name aks-link \
  --virtual-network myAksVnet \
  --registration-enabled false
```

After the link propagates, the same `nslookup` on the node returns the private address, the pull connects, and you delete the stuck pods to trigger an immediate retry. The diagnosis hinged entirely on running the lookup from the node rather than from a workstation, because a workstation resolves through a completely different path and would have shown a misleading answer. The fix touched DNS and nothing else, which is exactly what a `no such host` message tells you to do.

## What the events line cannot tell you, and where to look then

The events line resolves the overwhelming majority of pull failures, but a few sit at its edge, and knowing them keeps you from misreading a rare message. The first is a registry-side error rather than a client-side one. If the registry itself returns a server error, a `500` or a `503`, the pull fails through no fault of your configuration, and the message reflects the registry's response rather than a credential or path problem. The right move is to confirm the registry's own health and any service advisory before changing anything on the cluster, because the fault is upstream and your manifest, secret, and network are all correct.

The second is registry throttling that is not Docker Hub. ACR meters operations too, and a burst of pulls, especially during a large scale-up that fans out across many nodes at once, can run into the registry's own throttling, which surfaces as a transient failure that clears on retry. The signature is that the failures are transient and correlated with a burst rather than persistent, and the durable mitigation is to smooth the burst, with pre-pulling or staggered rollouts, rather than to change credentials. Confirming current throttling behavior and limits against the official ACR documentation at read time is the right habit, since these values are revised.

The third is a transport-layer failure that looks like reachability but is really a certificate problem. A pull to a self-hosted or proxied registry can fail with a TLS verification error when the registry presents a certificate the node does not trust, and the message names the certificate rather than a host or an authorization. That is neither a credential nor a routing problem; it is trust, and the fix is to make the node trust the registry's certificate chain, not to open a firewall or rotate a secret. The fourth is a corrupted or partial layer, where a transfer was interrupted and a cached layer fails its digest verification on assembly. Clearing the affected image from the node's cache so the kubelet fetches a clean copy resolves it, and it is rare enough that you should suspect the common causes first and reach for it only when the message explicitly references a digest mismatch or a verification failure. None of these contradicts the events-line rule; they extend it, because in each case the message still names the real fault, it simply points at the registry, the transport, or the cache rather than at the four common classes.

## One more case: the image has no build for the node's architecture

A subtler failure shows the message `no match for platform in manifest` or `no matching manifest for linux/arm64`. The registry has the image, authentication succeeded, and the network was fine, but the image was built only for one CPU architecture and the node runs another. This appears when a cluster mixes amd64 and arm64 node pools, or when an arm64-only or amd64-only image is scheduled onto the wrong node. It is genuinely an image-pull failure, because the runtime cannot find a matching layer set in the manifest list, but the remedy is different from every cause above.

Confirm it by inspecting the manifest to see which platforms the image actually provides:

```bash
docker manifest inspect myacr.azurecr.io/api:v3
```

If the manifest lists only `linux/amd64` and the failing pod is on an arm64 node, the mismatch is the cause. The fix is either to build and push a multi-architecture image so the manifest covers both platforms, or to constrain the workload to nodes of the matching architecture using a node selector on the well-known architecture label:

```yaml
spec:
  nodeSelector:
    kubernetes.io/arch: amd64
```

This case is worth knowing precisely because it does not respond to any of the credential, tag, or network fixes, and an engineer who has not seen it can burn an hour rotating secrets for an image that simply was not built for the node it landed on.

## Is the pod failing, or is it still pulling a large image?

Before treating a not-ready pod as a pull failure, confirm it is actually failing rather than simply working through a large download. A genuinely failing pod shows `ErrImagePull` or `ImagePullBackOff`, but a pod that is mid-pull shows `ContainerCreating` with a `Pulling` event and no `Failed` event, and the two look similar at a glance in `kubectl get pods` because neither is ready. The distinction matters because the fixes are opposite: a failing pull needs intervention, while a slow pull needs patience, and deleting a pod that is patiently downloading a multi-gigabyte image only restarts the download from the start.

Read the events to tell them apart. A pull in progress emits a `Pulling` event and, on completion, a `Pulled` event, with no `Failed` in between, so the absence of a `Failed` event is the signal that nothing is wrong yet:

```bash
kubectl describe pod <pod-name> -n <namespace> | grep -E "Pulling|Pulled|Failed"
```

If you see only `Pulling` with no `Failed`, the kubelet is still fetching, and the right action is to wait and let it finish. Large images, images with many layers, and nodes on constrained network paths can take real time to pull, and a pod that sits in `ContainerCreating` for a few minutes during a first pull on a cold node is normal rather than broken. The image size and layer count are worth knowing for your own workloads, because an image that routinely takes minutes to pull is a candidate for slimming, which shortens every cold-start and every scale-up, but a slow pull is a performance characteristic rather than a fault.

The trap is impatience. An engineer who sees a not-ready pod, assumes `ImagePullBackOff`, and starts changing configuration can introduce a real problem into a situation that would have resolved on its own. The discipline is the same as everywhere in this guide: read the events first. A `Failed` event with a registry message is a fault to fix, and a `Pulling` event with no failure is a download to wait out. Confirming which one you have before acting is the difference between solving a problem and creating one.

A pod is rarely one container anymore. Init containers run to completion before the main containers start, and sidecars run alongside the application, and any one of them references its own image that the kubelet must pull. When the pull that fails belongs to an init container, the pod never progresses past initialization, and the status reflects that with an `Init:ImagePullBackOff` rather than a plain `ImagePullBackOff`. The diagnosis is identical, the events line still names the cause, but the detail to catch is which container the failed pull belongs to, because the registry, the tag, and even the pull secret can differ between an init container and the main one.

Read the container-by-container statuses to see exactly which image failed, since `describe pod` lists init containers and regular containers separately:

```bash
kubectl get pod <pod-name> -n <namespace> \
  -o jsonpath='{range .status.initContainerStatuses[*]}{.name}{": "}{.state.waiting.message}{"\n"}{end}'
```

If an init container references a utility image from a public registry while the main container pulls from your ACR, a rate-limit failure can hit only the init image, leaving you puzzled that the application image is fine. The status prefix `Init:` is the tell, and the per-container output above pinpoints the offending image. The fix then applies to that specific reference, whether it is a tag correction, a pull secret, or an import to your own registry, and the pod proceeds once every container's image resolves. The lesson is to resist treating a multi-container pod as a single image; the pull is per container, and so is the fault.

## How imagePullPolicy changes what failures you see

The `imagePullPolicy` field decides when the kubelet attempts a pull at all, and that choice quietly shapes which failures surface and when. With the default behavior, a tag like `:latest` is pulled on every pod start, so a freshly broken tag fails loudly and immediately on the next scheduling. With `IfNotPresent`, the kubelet reuses a copy already on the node and skips the registry entirely when the layers are present, which means a tag that has gone bad in the registry can keep working on a node that pulled it earlier while failing on a node that never had it. That split is the source of the maddening case where the same deployment runs on one node and shows `ImagePullBackOff` on another, and the per-node history of what was cached, not any difference in credentials, is the real explanation.

This caching behavior is worth understanding before you reach for a fix, because it can both mask a problem and create a confusing one. A pinned digest reference pulled under `IfNotPresent` is safe to reuse, since the digest names exact content and the cached copy is by definition the right one. A moving tag reused under the same policy is not safe in the same way, because the cached layers may no longer match what the tag points to in the registry, and the node serves stale content without ever revealing that the tag was updated. When you need a node to fetch the current content of a moving tag, the reliable move is to reference the image by its digest so the identity is unambiguous, rather than trying to force a refresh of a tag whose meaning has shifted underneath you.

The policy also explains a class of errors that look like pull failures but are not. A pod set to `Never` does not contact the registry at all, so if the image is absent from the node it fails with `ErrImageNeverPull` rather than `ImagePullBackOff`, and no amount of fixing credentials or tags will help because the kubelet was never going to pull in the first place. Reading the policy alongside the events line keeps you from treating a deliberate no-pull configuration as a registry problem. The discipline holds: the events name the symptom, and the policy tells you whether a pull was even attempted, and the two together point at the fix without guesswork.

## Diagnosing a fleet-wide pull failure

When a single pod fails, you read its events and move on. When dozens fail at once, the question becomes whether they share one cause, and answering it quickly prevents you from chasing the same fault across many pods. The fastest read is the namespace event stream sorted by time, which surfaces a repeated message if there is one:

```bash
kubectl get events -n <namespace> --field-selector reason=Failed \
  --sort-by=.lastTimestamp
```

If every failing pod shows the same `toomanyrequests` or the same `401`, you have one root cause to fix, not many. A shared `toomanyrequests` across pods that all pull public images points squarely at the Docker Hub rate limit draining a shared quota. A shared `401` across pods pulling from the same registry points at an authentication change, a registry that was detached, a managed identity whose role assignment was removed, or an expired credential common to all of them. A fleet-wide failure that started at a precise moment usually maps to a single event: a registry credential rotated, a firewall rule tightened, a private DNS zone unlinked, or a tag that a pipeline overwrote. Correlating the failure's start time with recent changes narrows the cause faster than reading any single pod.

A different shape tells a different story. If the failures are scattered across pods that pull from many registries with no common message, the cause is more likely the node or the path than any one registry, and you check node-level connectivity and DNS rather than a registry credential. The grouping of the events, one message everywhere versus many messages scattered, is itself a diagnostic, and reading it first keeps a fleet-wide incident from turning into dozens of separate investigations of what is really one fault.

## Registries other than ACR: the same method

Most of this guide centers on Azure Container Registry because that is what most AKS clusters pull from, but the method does not depend on ACR. A pull from Docker Hub, GitHub Container Registry, a self-hosted Harbor, Quay, or any other registry fails through the same kubelet pull cycle and writes the same kind of events line, so the classification into name, tag, authentication, and reachability holds unchanged. What differs is the fix for the authentication row, because only ACR has the attach mechanism that grants the cluster identity a pull role.

For any non-ACR registry, the authentication fix is the `docker-registry` pull secret, created in the pod's namespace and referenced by the pod or its service account, exactly as described in the namespace section. The server value in that secret must match the registry's host, the username and token must be valid for that registry, and the token must not have expired, and those three are the things to verify when a non-ACR pull returns `401`. A private GitHub Container Registry image, for instance, needs a token with the read packages scope, and a pull failure with `401` against it almost always means the token lacks that scope or has expired, not that the cluster is misconfigured. The reachability and DNS rows are registry-agnostic too: a self-hosted Harbor behind a firewall fails with the same `i/o timeout` an ACR private endpoint does, and the same in-cluster connectivity and `nslookup` tests confirm it.

The practical upshot is that you do not need a different mental model per registry. Read the events line, classify the message, and apply the fix for that class, substituting the pull-secret path for the attach path whenever the registry is not ACR. The events line speaks the same language no matter who serves the image, which is why the method generalizes.

## A complete diagnosis from one command to the fix

It helps to see the whole method run once on a single incident, because the value is in the order of operations, not any individual command. A deployment that shipped fine yesterday is failing this morning. The first command is the status check, which tells you the scope:

```bash
kubectl get pods -n payments -o wide
```

```
NAME                       READY   STATUS             NODE
checkout-6c8d9f7b4-2xk9p   0/1     ImagePullBackOff   aks-pool1-31-2
checkout-6c8d9f7b4-7m4qr   1/1     Running            aks-pool1-31-0
checkout-6c8d9f7b4-bw8nt   0/1     ImagePullBackOff   aks-pool1-31-3
```

Two observations come for free. The deployment is half healthy, and the failing pods sit on different nodes from the running one. A half-healthy deployment with the failures tracking specific nodes is the signature of a cached-tag drift, where the running pod's node holds an old cached layer set and the failing nodes do not. That is a hypothesis, not a conclusion, so the second command tests it by reading the events:

```bash
kubectl describe pod checkout-6c8d9f7b4-2xk9p -n payments | sed -n '/Events:/,$p'
```

```
Warning  Failed  ...  Failed to pull image "myacr.azurecr.io/checkout:release":
  ... manifest unknown: manifest tagged by "release" is not found
```

The events line confirms the hypothesis: `manifest unknown` on a mutable `:release` tag, exactly what cached drift looks like. The third command checks the registry to see what happened to the tag:

```bash
az acr repository show --name myacr --image checkout:release --output table
```

If that returns not-found, or returns a timestamp from this morning, a pipeline overwrote or removed the tag, and the node that is still running simply has not been asked to re-pull because its cache satisfies `IfNotPresent`. The fix is to repoint at a tag or digest that exists and let the rollout replace every pod, which also refreshes the lucky node before its cache is evicted and it joins the failures:

```bash
DIGEST=$(az acr repository show --name myacr \
  --image checkout:1.4.2 --query "digest" -o tsv)
kubectl set image deployment/checkout \
  checkout=myacr.azurecr.io/checkout@${DIGEST} -n payments
kubectl rollout status deployment/checkout -n payments
```

The rollout reaching complete is the verification. Four commands carried the incident from symptom to fix, and each one earned the next: the status check scoped it and produced a hypothesis, the events line confirmed the class, the registry check identified the specific drift, and the digest pin both fixed it and prevented the recurrence. At no point did the diagnosis detour through credentials or networking, because the events line ruled those out on the first read. That is the entire discipline: let the cluster tell you what is wrong, confirm it with one targeted command, and apply only the fix the message points to.

## Prevention that stops the recurrence

The fixes above clear the failure in front of you. A few habits stop the whole family from coming back. Pinning images by digest in production manifests removes tag drift and the half-healthy deployments it causes, and it makes every pull deterministic. Attaching ACR to the cluster, or adopting workload identity, removes the namespace-scoped pull-secret traps and the secret-expiry failures that come with long-lived credentials. Importing public images into your own registry rather than pulling them from Docker Hub at runtime removes the shared-anonymous rate limit and the upstream-deletion risk in one move. Validating the registry path in your deployment pipeline, with `az aks check-acr` run against the target cluster as a pre-deploy gate, catches an authentication or reachability regression before it reaches a pod. And keeping node pools architecturally consistent, or always building multi-arch images, removes the platform-mismatch case.

The throughline is that each prevention turns a runtime surprise into a build-time or deploy-time guarantee. A digest cannot drift, an attached registry cannot lose its credentials to an expiry you forgot, an imported image cannot be rate limited by a shared bucket, and a checked path cannot silently break between deploys. None of these is expensive, and together they convert `ImagePullBackOff` from a recurring incident into a rare one.

Two further controls catch the failures before a pod is ever scheduled. An admission policy can reject any manifest that references a disallowed registry, so a workload that accidentally points at Docker Hub instead of your imported copy is refused at deploy time rather than discovered in `ImagePullBackOff` later. The same class of policy can require digest references and reject mutable tags, which enforces the tag-drift prevention across every team rather than leaving it to discipline. Gating at admission moves the cost of a bad reference from a production incident to a failed deploy, which is the cheapest place to pay it.

The other control addresses cold caches on new nodes. When a cluster scales up or upgrades, fresh nodes start with empty image stores, and the first pods scheduled onto them perform real pulls that expose any latent registry or path problem at the worst moment, under load. Pre-pulling the critical images onto new nodes, with a small DaemonSet that references those images so the kubelet caches them as nodes join, removes that exposure by warming the cache before the workload arrives. It does not fix a broken reference or a blocked path, those still need the real fix, but it stops a marginal registry condition from turning a routine scale-up into a wave of pull failures, and it makes the moment a new node joins boring rather than risky.

## Related failures it is often confused with

Once the image pulls, the next thing that can go wrong is the container starting and immediately crashing, which surfaces as `CrashLoopBackOff`. That is a different status with a different diagnostic method, the previous container's logs and the exit code rather than the pull events, and it is covered in full in the guide on [fixing AKS CrashLoopBackOff](/2022/07/18/fix-aks-crashloopbackoff/). If you fix the pull and the pod moves from `ImagePullBackOff` to `CrashLoopBackOff`, that is progress: the image now reaches the node, and the problem has moved from fetching the image to running it.

Two statuses look like `ImagePullBackOff` but are not. `InvalidImageName` means the image reference is malformed, a bad character, a missing tag separator, an illegal registry host, so the kubelet rejects it before even attempting a pull. The fix is to correct the syntax of the reference, and no registry or network change applies. `ErrImageNeverPull` appears when a pod sets `imagePullPolicy: Never` and the image is not already present on the node, so the kubelet refuses to pull by policy and there is nothing cached to use. That is a policy choice failing, not a pull failing, and the fix is to either pre-load the image onto the node or change the policy.

A pod stuck in `Pending` rather than `ImagePullBackOff` has not been scheduled to a node yet, so no pull has been attempted at all. That is a scheduling problem, insufficient resources, a taint, an affinity rule, or an unbound volume, and it is diagnosed from the scheduler's `FailedScheduling` events rather than the kubelet's pull events. The walkthrough on [fixing AKS pods stuck in Pending](/2022/07/25/fix-aks-pods-pending/) covers that path. The quick way to tell them apart is the status column: `Pending` means not yet placed, while `ImagePullBackOff` means placed and failing to pull.

## Where to reproduce and drill this

Reading about the events-line rule is one thing; building the muscle to apply it under incident pressure is another, and that comes from doing it. You can [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.net/tools/azure-labs.html) to stand up an AKS cluster with an ACR, deliberately break a pull each of the ways above, and watch how each fault writes its own distinct Events message, with the tested `az`, `kubectl`, and diagnostic commands kept in the searchable library so you can copy the exact confirmation step for each cause. VaultBook's error and issue reference pairs each symptom, the `401`, the `manifest unknown`, the `toomanyrequests`, the `no such host`, with its root causes and the command that confirms it, which turns the cause table above into something you can practice against rather than just read.

To build the diagnostic reflex itself, you can [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html), which present a failing pod and its Events output and ask you to classify the cause and pick the fix, exactly the loop this guide teaches. The drills reward reading the message before acting, so they train out the rotate-secrets-and-hope reflex and train in the events-line habit, and they cover the full spread of image-pull cases so the rare ones, the platform mismatch, the DNS failure, are familiar by the time you meet them in production. Used together, VaultBook gives you the cluster to break and restore, and ReportMedic gives you the structured practice that makes the classification automatic.

## Confirming the fix took, not just that you changed something

A change is not a fix until the pod proves it. The most common way a troubleshooting session goes wrong after the right diagnosis is stopping at the change rather than confirming the outcome, because the backoff window can hide whether the change worked. After attaching a registry, correcting a tag, importing an image, opening a path, or fixing DNS, force a fresh attempt and watch the pod reach running rather than assuming it will:

```bash
kubectl delete pod <pod-name> -n <namespace>
kubectl get pods -n <namespace> -w
```

The `-w` flag streams status changes, so you see the pod move from `ContainerCreating` to `Running` in real time, or you see it return to `ImagePullBackOff` if the fix was incomplete. If it returns to the failure, read the events again, because the message may now name a second, different cause that the first fault was masking. A registry that was both unattached and behind a blocked path will surface the authentication failure first and the network failure only after you fix the authentication, so a fix that changes the message is still progress even when the pod is not yet running. The events line is the arbiter at every step, not just the first.

For a deployment rather than a bare pod, watch the rollout reach complete, since that confirms every replica pulled successfully rather than just the one you deleted:

```bash
kubectl rollout status deployment/<name> -n <namespace>
```

Reaching ready is the outcome you want, but it helps to confirm it for the right reason rather than by coincidence. A pod can leave the failing state simply because the kubelet has not retried yet during a long back-off interval, so an absence of the failure for a few seconds is not the same as a successful pull. The positive signal is a fresh `Pulled` event for the image, which says the kubelet fetched it this time, paired with a container that reports `Running` and a restart count that is no longer climbing. Reading those two together, the new `Pulled` event and a settled restart count, tells you the fix took because the pull actually succeeded, not because the back-off timer happened to be mid-wait when you looked. That is the difference between verifying the work and catching it in a quiet moment between retries.

The discipline closes the loop the events line opened. You read the message, classified the cause, confirmed it with one command, applied the matching fix, and now you verify the pod or rollout reaches ready. Skipping that last step is how a correct diagnosis still ends in a reopened incident an hour later, and spending the few seconds to watch the status settle is how you know the work is actually done.

## The verdict

`ImagePullBackOff` and `ErrImagePull` are not a diagnosis, they are a prompt to go read one. The kubelet has already done the investigation and written the result into the pod's events, and the entire fix hinges on reading that line before touching anything. A `401` is authentication, and on AKS pulling from ACR it almost always means the registry is not attached or the pull secret is in the wrong namespace. A `manifest unknown` is the wrong name, tag, or a tag that drifted, and the durable answer is a digest pin. A `toomanyrequests` is Docker Hub throttling a shared anonymous quota, fixed by importing into your own registry. A `no such host` is DNS, and a connection timeout is a blocked network path, both fixed at the network layer and never at the credential layer. A platform mismatch is an image built for the wrong architecture. Read the Events line, classify it into one of those, confirm with the one command for that cause, and apply the matching fix. Do that and the status stops being a wall and becomes a signpost, which is the whole point: the cluster is telling you what is wrong, and the skill is listening to it.

The deeper skill underneath the table is a habit of mind that transfers far beyond this one status. Every Kubernetes failure writes its reason somewhere, in events, in logs, in a container's last state, in a scheduler decision, and the engineers who resolve incidents quickly are the ones who go read that record first instead of acting on a guess. `ImagePullBackOff` is a clean place to build the habit because its evidence is unusually legible: the kubelet hands you a plain sentence that names the fault. Treat that sentence as the source of truth, let it veto your first instinct when the two disagree, and you will not only fix pull failures faster, you will carry the same discipline into `CrashLoopBackOff`, into scheduling failures, and into every other status that looks opaque until you read what the cluster already wrote about it. The command set changes from one failure to the next, but the method does not: find the cluster's own record of what happened, classify it, confirm it, and fix exactly that. The reward for learning it on image pulls is that the rest of the platform starts to feel legible too.

## Frequently Asked Questions

### Q: Why does AKS show ImagePullBackOff pulling from ACR?

The usual reason is that the Azure Container Registry was never attached to the AKS cluster, so the cluster's managed identity has no permission to pull from it and the registry returns `401 Unauthorized`. The kubelet reports that as `ImagePullBackOff`. Confirm with `az aks check-acr`, which tests the authentication and network path from inside the cluster and reports which leg failed. Fix it by attaching the registry with `az aks update --attach-acr`, which assigns the pull role to the cluster identity, then delete the failing pod so the kubelet pulls again immediately. If attaching is not appropriate, supply a `docker-registry` secret as an `imagePullSecret` in the pod's namespace instead. Rotating credentials does nothing here, because in the unattached case there were never any credentials to rotate.

### Q: Can a wrong image tag cause ImagePullBackOff?

Yes, and it is among the most frequent causes. When the tag in the pod spec does not exist in the repository, the registry answers `manifest unknown` or `not found`, and the kubelet surfaces that as `ImagePullBackOff`. The trigger can be a typo in the repository or tag, a tag that was never pushed, or a mutable tag like `:latest` that a pipeline overwrote or deleted. Confirm it by listing the actual tags with `az acr repository show-tags` and comparing them to what the spec requests. The immediate fix is to correct the reference or push the missing tag. The durable fix is to pin images by digest, since a digest is immutable and cannot drift, which eliminates the entire tag-related family of pull failures in production.

### Q: Does the Docker Hub rate limit cause ImagePullBackOff?

Yes. Docker Hub throttles anonymous and free-tier pulls over a rolling window, and when the limit is exceeded it returns `toomanyrequests`, which the kubelet reports as `ImagePullBackOff`. AKS hits this more easily than a single developer because the cluster's nodes typically share one outbound IP, so every anonymous pull across the cluster counts against the same bucket. A scale-up or a rollout that restarts many pods can drain a shared quota quickly. Check Docker's current published limits at read time, since they change. The strong fix is to import the public images into your own ACR with `az acr import` and pull from there, removing the shared anonymous quota from the path. A lighter fix is to authenticate the Docker Hub pull with an account credential, which raises the applicable limit above the anonymous tier.

### Q: Why is my imagePullSecret not working in AKS?

The most common reason is that the secret lives in the wrong namespace. Kubernetes secrets are namespaced, so a pull secret in `default` is invisible to a pod in `production`, and the pull keeps failing with `401` even though the secret clearly exists when you list it. Confirm by checking `kubectl get secret <name> -n <pod-namespace>`; if it returns NotFound while it exists elsewhere, that is the fault. Two other checks matter: confirm the pod actually references the secret in its `imagePullSecrets`, and confirm the embedded server, username, and token match the registry and have not expired. The fix is to create the secret in the pod's own namespace, or to attach ACR to the cluster so the cluster identity authenticates and per-namespace pull secrets become unnecessary.

### Q: How do I find the real reason behind ImagePullBackOff?

Run `kubectl describe pod <pod> -n <namespace>` and read the Events section at the bottom. The kubelet writes a `Warning` event with a message beginning `Failed to pull image`, and the words in that message name the cause: `401 Unauthorized` is authentication, `manifest unknown` or `not found` is a bad name or tag, `toomanyrequests` is rate limiting, `no such host` is DNS, and a `dial tcp` timeout is a blocked network path. For a namespace-wide view when many pods fail at once, use `kubectl get events --sort-by=.lastTimestamp`. The discipline is to read that line before changing anything, because the status itself, whether `ErrImagePull` or `ImagePullBackOff`, never tells you the cause, only that a pull failed.

### Q: What is the difference between ErrImagePull and ImagePullBackOff?

They are two stages of the same failure. `ErrImagePull` is the immediate result of one failed pull attempt: the runtime tried to fetch the image and returned an error. `ImagePullBackOff` is what the status becomes after several failures, when the kubelet starts spacing out its retries with an exponential delay rather than retrying continuously. The same pod often shows `ErrImagePull` first and `ImagePullBackOff` a moment later, with nothing about the underlying fault having changed. Because they report the same problem, you diagnose both by reading the pod's Events line. The only practical effect of the backoff is that after you apply a fix, the pod may sit in `ImagePullBackOff` until the next scheduled retry, so deleting the pod forces an immediate fresh pull.

### Q: Does deleting and recreating the pod fix ImagePullBackOff?

Only as a way to skip the backoff wait after you have already fixed the real cause. The kubelet spaces out its retries with a growing delay, so once a fix is in place the pod may sit in `ImagePullBackOff` for a while before the next scheduled attempt. Deleting the pod creates a fresh one that pulls immediately, which makes the fix visible right away. Recreating the pod as the fix itself, before addressing the underlying fault, accomplishes nothing, because the new pod uses the same spec to hit the same registry and fails identically. Always read the Events line, apply the matching remedy, and only then delete the pod to force an immediate pull if you do not want to wait out the backoff window.

### Q: How long does Kubernetes back off between image pull retries?

The kubelet uses an exponential backoff, doubling the wait between failed pull attempts up to a ceiling, rather than retrying on a fixed tight loop. The exact starting interval and cap are kubelet defaults that can change across versions, so treat the specific durations as values to confirm against the current Kubernetes documentation rather than fixed constants. The behavior that matters for troubleshooting is stable: a pod that has been failing for several minutes is no longer retrying every few seconds, so a correct fix can appear to do nothing for a while. If you need the pull to retry immediately after applying a fix, delete the pod so a fresh one is scheduled, which resets the backoff and triggers a new pull at once.

### Q: How do I pull a private image into AKS without attaching ACR?

Create a Kubernetes secret of type `docker-registry` holding the registry server, a username, and a token, in the same namespace as the pod, then reference it from the pod spec under `imagePullSecrets`. Build it with `kubectl create secret docker-registry <name> --docker-server=... --docker-username=... --docker-password=...`, and add the secret name to the pod's `imagePullSecrets` list. This is the right approach for registries that are not ACR, or for sharing a scoped credential rather than granting the cluster identity. The two things that break it are putting the secret in the wrong namespace and forgetting to reference it in the spec, so confirm both. For an ACR on Azure, attaching the registry to the cluster is cleaner because it avoids per-namespace secret management entirely.

### Q: Why does my image pull succeed on one node but fail on another?

This usually means the image is cached on the node where it works and not on the node where it fails, while the registry reference has drifted. Under the default `IfNotPresent` policy, a node that already holds a mutable tag like `:latest` keeps using its cached copy even after the tag was overwritten or deleted upstream, so it runs fine, while a fresh node with no cache tries to pull the now-missing tag and fails with `manifest unknown`. Use `kubectl get pods -o wide` to confirm the failures track the nodes without the cached image. The fix is to push the missing tag or, durably, pin the image by digest so every node pulls the same immutable reference and node-to-node behavior becomes consistent.

### Q: Can a missing architecture build cause an image pull failure?

Yes. If the image manifest contains no layer set for the node's CPU architecture, the runtime cannot select a matching image and the pull fails with a message like `no match for platform` or `no matching manifest for linux/arm64`. This happens on clusters that mix amd64 and arm64 node pools, or when a single-architecture image lands on the wrong node. Confirm by inspecting the manifest with `docker manifest inspect <image>` to see which platforms it provides. Fix it by building and pushing a multi-architecture image so the manifest covers both platforms, or by constraining the workload to matching nodes with a `nodeSelector` on `kubernetes.io/arch`. This case does not respond to credential, tag, or network fixes, so recognizing the platform message saves the wasted effort of treating it like an authentication problem.

### Q: What does the message no such host mean during an image pull?

It means the node could not resolve the registry's host name into an address, so there was nothing to connect to and the pull failed before authentication. On AKS this most often happens with a registry behind a private endpoint, where the public FQDN must resolve to the private address from inside the virtual network, and the private DNS zone that provides that mapping is missing, unlinked, or not in the cluster's resolution path. Confirm it from inside the cluster with an `nslookup` of the registry FQDN run from the affected node; a failed lookup, or one returning a public address for a private-only registry, confirms DNS as the cause. The fix is at the DNS layer: ensure the private DNS zone exists, is linked to the cluster's virtual network, and is consulted by the node's resolver.

### Q: How do I verify an imagePullSecret is actually being used by the pod?

Read the pod spec back from the cluster and confirm the secret is named under `imagePullSecrets`, because a secret that exists but is not referenced is never consulted. Use `kubectl get pod <pod> -n <namespace> -o jsonpath='{.spec.imagePullSecrets[*].name}'` to print the referenced names. An empty result means the pod references no pull secret at all, so creating one without adding it to the spec changes nothing. If the name is present, confirm the secret exists in the same namespace and that its decoded docker config points at the registry you are pulling from with valid, unexpired credentials. A mismatch between the secret's server and the image's registry, or an expired token, produces a `401` even though the reference and namespace look correct.

### Q: Does ImagePullBackOff mean my AKS node is unhealthy?

Almost never. `ImagePullBackOff` is about the kubelet failing to fetch one specific image, not about the node's health. A node that runs other workloads fine but fails this pull has a problem with the image reference, the registry authentication, or the network path to that registry, not with the node itself. Confirm node health separately with `kubectl get nodes`; if every node shows `Ready` and other pods on the same node are running, the node is not the issue. Cordoning, draining, or restarting a healthy node wastes time and does not address a pull failure. The actual cause is in the pod's Events message, so read that line and classify it into authentication, name or tag, rate limiting, or reachability before touching the node.

### Q: How do I confirm whether the failure is authentication or network during an image pull?

Run `az aks check-acr` against the cluster and registry, because it tests the authentication leg and the network leg separately and reports which one failed, making it the fastest single confirmation. To isolate the network path further, launch a debug pod pinned to the failing node with a network toolbox image and test the registry's HTTPS endpoint using `nc -vz <registry> 443` and a `curl` to the registry's `/v2/` path. A timeout or refused connection points to a firewall, egress rule, or private-link problem, while a clean connection paired with a `401` points to authentication. Reading the Events message first usually classifies it, since `401` is authentication and `dial tcp` timeouts or `no such host` are network, but the in-cluster tests confirm it definitively.

### Q: Can imagePullPolicy Never cause a pull error instead of ImagePullBackOff?

Yes, and the status is different so it is worth distinguishing. With `imagePullPolicy: Never`, the kubelet will not attempt a pull at all and relies on the image already being present on the node. If the image is not cached there, the pod shows `ErrImageNeverPull` rather than `ImagePullBackOff`, because no pull was ever tried. This is a policy choice failing, not a registry or network failure, so none of the credential, tag, or connectivity fixes apply. The remedy is either to pre-load the image onto the node by some other mechanism or to change the policy to `IfNotPresent` or `Always` so the kubelet fetches the image normally. Recognizing `ErrImageNeverPull` as distinct from `ImagePullBackOff` prevents chasing a registry problem that does not exist.

### Q: What does InvalidImageName mean and how is it different from ImagePullBackOff?

`InvalidImageName` means the image reference in the pod spec is malformed, so the kubelet rejects it before attempting any pull. A bad character, a missing tag separator, an illegal registry host, or a stray space all produce it. It differs from `ImagePullBackOff` in that no pull was attempted: with `ImagePullBackOff` the kubelet tried to fetch a syntactically valid reference and the registry or network failed it, whereas with `InvalidImageName` the reference never parsed. The fix is purely to correct the syntax of the image string, and no registry, credential, or network change applies. Read the reference carefully against the expected `registry/repository:tag` or digest form, fix the typo, and reapply. Distinguishing the two by status saves you from troubleshooting a registry that the kubelet never even contacted.

### Q: My pod moved from ImagePullBackOff to CrashLoopBackOff, what happened?

That is progress, not a regression. The image now pulls successfully, so the problem has moved from fetching the image to running it. `CrashLoopBackOff` means the container started and then exited, and the kubelet keeps restarting it with a growing delay. The diagnosis is completely different from a pull failure: instead of the pod's pull events, you read the previous container's logs with `kubectl logs <pod> --previous` and check the last state and exit code in `kubectl describe pod`. Common causes are a missing environment variable or secret, an out-of-memory kill shown as exit code 137, or a failing liveness probe restarting an otherwise healthy app. The full method for that status lives in the dedicated CrashLoopBackOff guide, but the key point here is that the image-pull problem is solved.

### Q: Why did image pulls start failing right after a cluster upgrade or node pool scale-up?

Because new nodes start with an empty image cache, so the first pods scheduled onto them perform real pulls that expose any latent registry or path problem that warm-cached nodes were hiding. An upgrade replaces nodes, and a scale-up adds fresh ones, and in both cases the new nodes must fetch every image from scratch. If a credential expired, a firewall rule tightened, a tag drifted, or DNS to a private registry was never quite right, the old nodes kept running on cached layers and masked it, while the new nodes hit the real condition immediately. Read the events line on a failing pod on a new node and treat it as any other pull failure; the upgrade or scale-up did not cause the fault, it merely removed the cache that was concealing it. Pre-pulling critical images onto new nodes prevents the surprise from landing under load.

### Q: Can a corrupted or partial layer download cause ImagePullBackOff, and how do I clear it?

It can, though it is uncommon, and the message is the tell: a digest mismatch or a layer verification failure rather than an authorization, not-found, or network error. A transfer interrupted partway can leave a cached layer that fails its integrity check when the runtime tries to assemble the image, so the pull fails even though the registry, credentials, and network are all fine. Before suspecting this, confirm the message actually references a digest or verification problem, because the common causes are far more likely. When it is genuinely a bad cached layer, the fix is to clear the affected image from the node's local store so the kubelet fetches a clean copy on the next attempt, then delete the pod to trigger that fetch. If the corruption recurs across nodes, look upstream at the registry or the network for a transfer problem rather than treating each node's cache in isolation.
