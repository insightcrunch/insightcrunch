---
layout: post
title: "Fix AKS Pods Stuck in Pending State"
page_title: "Fix AKS Pods Stuck in Pending State: Diagnose FailedScheduling, Insufficient CPU, Taints, Affinity, and Unbound PVC Causes in Azure Kubernetes Service"
date: 2022-07-25
categories: ["Technology"]
tags: ["Azure", "AKS", "Kubernetes", "Troubleshooting", "Performance", "Cloud Computing"]
excerpt: "An AKS pod stuck in Pending means the scheduler found no node to place it on. Read the FailedScheduling events and fix every root cause with confidence."
image: "/assets/images/blog/blog-36.webp"
reading_time: 59
author: "kevin-reeves"
last_updated: 2022-07-25
lang: en
---
A pod that reports `Pending` in Azure Kubernetes Service has not crashed, has not failed to pull an image, and has not been rejected by your application code. It is waiting. The Kubernetes scheduler looked at every worker in the cluster, weighed what the workload asked for against what each machine could offer, and concluded that no eligible host exists right now. When an AKS pod is stuck in Pending, the cluster is telling you, with more precision than most engineers stop to read, exactly why placement failed. The single most common mistake during this incident is to treat Pending as a generic stall and start restarting deployments, scaling replicas, or recreating the namespace, none of which addresses the constraint the scheduler already named for you.

This guide rebuilds the diagnosis from the scheduling decision outward. You will learn to read the `FailedScheduling` events on a Pending workload, sort the symptom into one of the distinct families that produce it, confirm which family is yours with a command rather than a guess, and apply the matching remedy. The families are resource starvation, autoscaler limits, placement constraints such as taints and affinity, storage that will not bind, and address or quota exhaustion at the platform layer. Each leaves a different fingerprint in the events, and once you can read that fingerprint the fix stops being a gamble.

![Diagnosing AKS pods stuck in Pending state and FailedScheduling root causes - Insight Crunch](/assets/images/blog/blog-36.webp)

The reason this matters beyond a single incident is that Pending sits at the boundary between your declared intent and the physical capacity of the cluster. Every other Kubernetes failure mode assumes the workload was placed and then something went wrong; a Pending workload never got that far. Understanding it forces you to understand how the scheduler reasons, which in turn makes you better at sizing requests, designing node pools, and writing affinity rules that do not paint the cluster into a corner. By the end you should be able to look at the events on any unscheduled workload and route directly to the layer that needs your attention.

## What a Pending Pod Actually Means in Kubernetes

A pod enters the `Pending` phase the moment it is admitted to the API server and persists in that phase until every one of its containers has been bound to a node and started. Pending is therefore not an error state in the way `CrashLoopBackOff` is an error state. It is the normal first phase of any workload's life, and it becomes a problem only when the workload never leaves it. The distinction matters because it tells you where to look: a workload that lingers in Pending has a scheduling problem, not a runtime problem, and scheduling problems are decided before a single container image is ever fetched.

### Why does the scheduler leave a pod unscheduled?

The Kubernetes scheduler runs a two-phase algorithm on each unscheduled workload. First it filters: it walks the list of worker machines and discards any that cannot host the workload at all, because they lack the requested CPU or memory, carry a taint the workload does not tolerate, or fail a node selector or affinity predicate. Then it scores the survivors and picks the best fit. If the filter phase eliminates every machine, no candidate remains to score, and the workload stays Pending with a `FailedScheduling` event explaining which predicate did the eliminating.

That two-phase model is the mental picture to hold for the rest of this guide. Almost every Pending incident is a filter-phase failure: the predicates threw out every worker. The job of diagnosis is to read which predicate fired. The scheduler is not coy about this. It records the reason in the workload's events, often with a per-machine tally such as "3 Insufficient cpu, 2 node(s) had untolerated taint," and that tally is the most valuable single line in the entire investigation. Engineers who skip it and start mutating the cluster are discarding the answer the platform already wrote down.

### Is Pending the same as ContainerCreating or Unschedulable?

No, and conflating them sends you down the wrong path. `Pending` with a `FailedScheduling` event means the scheduler could not assign the workload to any worker. `ContainerCreating` means the scheduler already succeeded, a machine was chosen, and the kubelet on that machine is now pulling images or mounting volumes. A workload that shows `Unschedulable` in its conditions is a Pending workload whose scheduler gave up for now. The phase you see in `kubectl get pods` plus the events together tell you whether you have a placement problem or a startup problem, and that branch determines everything that follows.

The practical consequence is that you should never debug a Pending workload by looking at container logs. There are no container logs yet, because no container has started. The logs you want live in the workload's events and in the state of the cluster's workers, not in the application. This is the first habit to build: when a workload is Pending, your eyes go to `kubectl describe`, never to `kubectl logs`.

## How to Read the Diagnostic Signal Before You Touch Anything

Every minute spent reading the scheduler's own explanation saves ten minutes of speculative changes. The diagnostic sequence below gathers the four signals that, taken together, identify the responsible family without ambiguity. Run them in order before you alter a single manifest, because each later step interprets the output of the earlier ones.

The first command surfaces the scheduler's verdict directly:

```bash
kubectl describe pod <pod-name> -n <namespace>
```

Scroll to the `Events` section at the bottom. A genuinely stuck workload shows a repeating `Warning  FailedScheduling` line from the `default-scheduler` source. The message after it is the diagnosis. Read it literally. "0/5 nodes are available: 5 Insufficient memory" tells you the request exceeds free memory on every worker. "2 node(s) had untolerated taint {workload: gpu}, 3 Insufficient cpu" tells you a mix of two constraints across the pool. The aggregate counts always sum to the total worker count, so when the numbers do not add up to the machines you expect, you have already learned something about a missing or NotReady worker.

The second command shows what the cluster can actually offer:

```bash
kubectl get nodes -o wide
kubectl describe node <node-name>
```

On the worker description, the `Allocatable` block reports the CPU and memory the scheduler is allowed to hand out, which is always less than the machine's raw capacity because the kubelet, the operating system, and reserved daemons claim a slice first. The `Allocated resources` block reports how much of that allocatable pool is already committed by existing workloads. The gap between allocatable and allocated is the room a new workload can claim. If that gap is smaller than your workload's request on every worker, you have found a resource-starvation case before touching anything.

### How do I compare a pod's requests against node capacity?

Pull the workload's resource requests and set them beside the allocatable headroom on your largest worker. The request, not the limit, is what the scheduler reads during the filter phase. If the largest worker's free allocatable CPU is 1.4 cores and the workload requests 2 cores, no machine can host it, and the fix is to lower the request, choose a larger worker SKU, or add capacity. This single comparison resolves the most frequent Pending incident outright.

```bash
kubectl get pod <pod-name> -n <namespace> \
  -o jsonpath='{.spec.containers[*].resources.requests}'
```

The third signal is the state of automatic scaling. If the cluster runs the autoscaler, its decisions appear as events and in its status configmap:

```bash
kubectl get configmap cluster-autoscaler-status -n kube-system -o yaml
kubectl get events -A --field-selector source=cluster-autoscaler
```

The autoscaler annotates a Pending workload with its own reasoning, including phrases that indicate it tried to add a worker and could not, or that the relevant pool is already at its maximum size. That annotation distinguishes a cluster that simply needs to grow from one that has hit a ceiling you configured or a subscription quota you did not know was there.

The fourth signal covers storage. A workload that mounts a `PersistentVolumeClaim` cannot be scheduled until that claim binds to a volume:

```bash
kubectl get pvc -n <namespace>
kubectl describe pvc <claim-name> -n <namespace>
```

A claim shown as `Pending` rather than `Bound` is itself the reason the workload will not schedule, and its events name the storage problem: a missing or mistyped storage class, a zone the volume cannot reach, or a provisioner that errored. With these four readings in hand, the responsible family is rarely in doubt, and the cause table below turns the reading into a remedy.

## The InsightCrunch Pending-Pod Cause Table

This table is the routing artifact for the rest of the guide. Match the message you read in the `FailedScheduling` event to its row, confirm with the named check, and jump to the section that walks the fix in depth. The governing principle, which this series calls the requests-not-limits rule, is that the scheduler places work by its resource requests and its placement predicates, so a workload that will not schedule is almost always asking for more than any worker offers or violating a constraint the events spell out by name.

| FailedScheduling message you see | Family | Confirming check | Section |
| --- | --- | --- | --- |
| `Insufficient cpu` or `Insufficient memory` | Resource starvation | Compare request to allocatable headroom on the largest worker | Cause One |
| `Too many pods` | Per-node pod ceiling reached | `kubectl describe node` pod count versus max pods | Cause One |
| Autoscaler note: pool at max, or no scale-up | Autoscaler ceiling | `cluster-autoscaler-status` configmap | Cause Two |
| `had untolerated taint` | Placement constraint, taint | `kubectl describe node` taints versus pod tolerations | Cause Three |
| `didn't match Pod's node affinity/selector` | Placement constraint, selector or affinity | Compare `nodeSelector` and affinity to node labels | Cause Four |
| `had volume node affinity conflict`, or PVC `Pending` | Storage will not bind | `kubectl describe pvc` events | Cause Five |
| `FailedCreatePodSandBox` IP allocation, or no free IPs | Address exhaustion under Azure CNI | Subnet free address count | Cause Six |
| Autoscaler note: quota exceeded, vCPU limit | Subscription quota | Azure usage versus quota for the SKU family | Cause Seven |

The table is deliberately ordered by frequency in real AKS clusters rather than by alphabet. Resource starvation and autoscaler ceilings account for the large majority of Pending incidents; taints, affinity, and storage account for most of the remainder; address and quota exhaustion are rarer but produce some of the most confusing symptoms because the message points at the platform rather than at the workload. Work the table top to bottom and you will resolve the common cases before reaching the exotic ones.

## Cause One: The Request Exceeds Every Worker's Free Capacity

The most frequent reason an AKS workload will not schedule is the simplest to state and the easiest to misdiagnose: the workload asks for more CPU or memory than any worker in the pool has available to give. The event reads `Insufficient cpu` or `Insufficient memory`, sometimes both, with a count against every machine. Engineers who do not pause to read the count often conclude the cluster is "out of resources" and reach for the wrong lever, scaling the replica count higher, which only creates more unschedulable copies of the same oversized workload.

Two numbers decide this case. The first is the workload's resource request, which is what the scheduler reads during filtering. The second is the allocatable headroom on the roomiest worker, meaning the allocatable total minus what is already committed there. When the request is larger than that headroom on every machine, filtering eliminates all of them and the workload waits. The fix follows from whichever number is wrong.

### Why does requests, not limits, drive scheduling?

The scheduler filters and scores workers using the `requests` field only. The `limits` field caps runtime consumption and triggers throttling or eviction, but it plays no part in placement. A workload with a 4 core limit and a 250 millicore request schedules onto any worker with 250 millicores free, while a workload with a 4 core request will not fit a worker that has only 3 cores free no matter how generous its limit is. Confusing the two is the single most common sizing error behind a stuck workload.

To confirm the case, read the request and the headroom side by side:

```bash
# What the workload asks for at schedule time
kubectl get pod <pod-name> -n <namespace> \
  -o jsonpath='{range .spec.containers[*]}{.name}{": "}{.resources.requests}{"\n"}{end}'

# What the busiest pool can still hand out
kubectl describe node <node-name> | sed -n '/Allocatable/,/Allocated resources/p'
```

If the largest free block on any worker is smaller than the request, you have confirmed resource starvation. Three remedies exist, and choosing among them is a design decision rather than a reflex.

The first remedy is to lower the request to match reality. Many workloads carry inflated requests copied from a template or guessed during early development, and a workload requesting 2 cores that historically uses 200 millicores should request something close to its real working set plus headroom, not a round number someone typed once. Measure actual consumption with the metrics server before you trust an old request:

```bash
kubectl top pod <pod-name> -n <namespace>
```

The second remedy is to grow the cluster, either by letting the autoscaler add a worker, which only helps if the autoscaler is healthy and below its ceiling, or by manually scaling the node pool:

```bash
az aks nodepool scale \
  --resource-group <rg> \
  --cluster-name <cluster> \
  --name <nodepool> \
  --node-count <n>
```

The third remedy applies when a single workload genuinely needs more than any current worker can offer, for example a memory-hungry analytics job on a pool of small machines. In that situation no count of small workers helps, because a workload runs on one machine and cannot be spread across several. You need a larger worker SKU, which means a new node pool sized for the workload:

```bash
az aks nodepool add \
  --resource-group <rg> \
  --cluster-name <cluster> \
  --name memorypool \
  --node-vm-size Standard_E8s_v5 \
  --node-count 2
```

A related variant of this family hides behind the message `Too many pods`. Every AKS worker has a maximum pod count, set per node pool, and once a worker hosts that many workloads the scheduler treats it as full for placement purposes even when CPU and memory remain free. The default ceiling differs between the kubenet and Azure CNI networking models, and a cluster packed with tiny workloads can exhaust the pod count long before it exhausts compute. Confirm by reading the worker's capacity:

```bash
kubectl get node <node-name> -o jsonpath='{.status.capacity.pods}'
```

If the committed pod count equals that ceiling on every worker, the remedy is to add workers, raise the max-pods setting on a new pool, or consolidate workloads, not to add CPU. This variant is worth knowing because the symptom feels identical to compute starvation from the outside, yet the lever is entirely different.

## Cause Two: The Cluster Autoscaler Cannot or Will Not Add a Worker

When a cluster runs the autoscaler, a Pending workload should normally trigger a scale-up: the autoscaler notices the unschedulable workload, decides a new worker would let it fit, and provisions one. When that does not happen and the workload sits Pending while the autoscaler stays quiet or logs a refusal, you are in the autoscaler family, and the question becomes why the automatic remedy declined to act.

The autoscaler's reasoning is recorded in its status configmap and its events, and reading them is the whole of the diagnosis:

```bash
kubectl get configmap cluster-autoscaler-status -n kube-system -o yaml
```

Several distinct refusals show up here, and each points at a different fix. The most common is that the relevant node pool is already at its configured maximum. The autoscaler will not exceed the upper bound you set, so a pool capped at five workers that already runs five will leave the workload Pending no matter how much it would like to help. Raising the bound resolves it:

```bash
az aks nodepool update \
  --resource-group <rg> \
  --cluster-name <cluster> \
  --name <nodepool> \
  --update-cluster-autoscaler \
  --min-count 1 \
  --max-count 10
```

### Why does the autoscaler ignore a Pending pod entirely?

The autoscaler only adds a worker when doing so would let the Pending workload schedule. If the workload cannot fit even on a brand-new, empty worker of the pool's SKU, because its request exceeds that SKU's allocatable capacity, the autoscaler concludes that scaling up would not help and declines. The status configmap says as much. The fix is not to coax the autoscaler but to size a pool whose workers are large enough, which loops back to the SKU decision in Cause One.

A second refusal appears when the workload carries a placement constraint, such as a node selector for a pool that is itself at maximum, or a toleration for a taint that only a capped pool offers. The autoscaler scales the pool that would satisfy the constraint, and if that specific pool is maxed the workload waits even though other pools have room. Reading which pool the autoscaler considered, named in its events, tells you which ceiling to lift.

A third refusal is a genuine inability to provision, where the autoscaler tries to add a worker and Azure refuses because a subscription quota is exhausted or the requested SKU is unavailable in the region or zone. That refusal is the bridge to Cause Seven, and the autoscaler status will say the scale-up failed rather than that it was declined. The difference between "I chose not to" and "I tried and could not" is the difference between a configuration fix and a quota request, so read the wording precisely.

There is also a quieter failure where the autoscaler is not actually enabled on the pool you expect, perhaps because it was provisioned without the flag or disabled during maintenance. Confirm the pool's scaling configuration directly rather than assuming:

```bash
az aks nodepool show \
  --resource-group <rg> \
  --cluster-name <cluster> \
  --name <nodepool> \
  --query "{autoscaling:enableAutoScaling,min:minCount,max:maxCount,count:count}" -o table
```

If autoscaling shows as disabled on a pool you believed elastic, the workload was never going to get a new worker automatically, and the remedy is either to enable scaling or to scale the pool by hand while you investigate why it was off.

## Cause Three: A Taint With No Matching Toleration

Taints are how a worker repels workloads that do not explicitly opt in. AKS applies them in several situations, on GPU and spot pools, on system pools reserved for platform components, and wherever an operator has marked workers for a dedicated purpose. A workload without a matching toleration is filtered off every tainted worker, and if every eligible worker is tainted the workload stays Pending with the unmistakable message `had untolerated taint`.

The event names the taint, which is the fast path to the fix. Read the taints on your workers and the tolerations on the workload, and the mismatch is usually obvious:

```bash
# Taints across the cluster's workers
kubectl get nodes -o json | jq '.items[] | {name:.metadata.name, taints:.spec.taints}'

# Tolerations the workload declares
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.tolerations}'
```

The remedy depends on intent. If the workload genuinely belongs on the tainted workers, for example a GPU job that should land on the GPU pool, add the matching toleration to the workload's spec:

```yaml
spec:
  tolerations:
    - key: "sku"
      operator: "Equal"
      value: "gpu"
      effect: "NoSchedule"
```

### Does a taint always keep a pod Pending?

Only when no untainted worker can host the workload. A taint with the `NoSchedule` effect removes a worker from consideration for any workload lacking the matching toleration, but if the cluster also runs an untainted pool with room, the workload schedules there and never goes Pending. Pending from a taint therefore tells you that every worker with capacity is tainted, which is common on small clusters where the only pool is a system pool or where spot workers carry a taint the workload does not tolerate.

A frequent and avoidable version of this case involves spot node pools. Spot workers carry a taint precisely so that only workloads explicitly willing to run on interruptible capacity land there. A team that converts its only pool to spot to save money, then forgets to add the spot toleration to its workloads, watches every workload go Pending and concludes spot is broken. It is not broken; it is doing exactly what the taint instructs. The fix is to tolerate the spot taint on workloads that can survive eviction, and to keep a small on-demand pool for workloads that cannot.

The opposite remedy is sometimes correct. If a taint was applied by mistake or no longer serves a purpose, removing it returns the workers to the general scheduling pool:

```bash
kubectl taint nodes <node-name> sku=gpu:NoSchedule-
```

The trailing minus removes the taint. Be deliberate here, because removing a taint on a system pool can let arbitrary workloads displace platform components, which trades a Pending workload for a less obvious instability. Prefer adding a precise toleration over stripping a taint whose purpose you have not confirmed.

## Cause Four: Node Selector or Affinity Matches No Worker

A node selector or a node affinity rule narrows where a workload may run by requiring labels on the host. When those requirements match no worker, the scheduler filters out every machine and the workload waits with `didn't match Pod's node affinity/selector`. This family is insidious because the manifest looks correct in isolation; the problem is a mismatch between the labels the workload demands and the labels the cluster actually carries.

The investigation is a comparison of two lists. Read the workload's selector and affinity, then read the labels present on the workers:

```bash
# What the workload requires
kubectl get pod <pod-name> -n <namespace> \
  -o jsonpath='{.spec.nodeSelector}{"\n"}{.spec.affinity.nodeAffinity}'

# What labels the workers carry
kubectl get nodes --show-labels
```

The mismatches are usually one of a small set. A typo in a label key or value, where the workload asks for `disktype=ssd` but the workers are labeled `disk-type=ssd`, eliminates every machine over a single character. A label that was expected to exist but was never applied, because a node pool was created without the custom label or the label was set on a pool that has since been deleted, leaves nothing to match. A zone affinity that pins the workload to an availability zone where the pool has no workers asks for a machine that does not exist in that zone.

### Why does a correct-looking affinity rule leave a pod Pending?

Because affinity is evaluated against the labels actually present on workers at schedule time, not against what the manifest author assumed would be there. A `requiredDuringSchedulingIgnoredDuringExecution` rule is a hard filter; if no worker satisfies it, the workload cannot schedule, full stop. The rule may be syntactically perfect and still match nothing, which is why the fix is always to reconcile the rule with the real label set rather than to re-read the rule for syntax errors.

Two remedies apply. If the workload's requirement is right and the cluster simply lacks the label, apply the label to the appropriate pool, ideally at the pool level so new workers inherit it:

```bash
az aks nodepool update \
  --resource-group <rg> \
  --cluster-name <cluster> \
  --name <nodepool> \
  --labels disktype=ssd
```

If the requirement itself is wrong, correct the manifest so it matches the labels the cluster carries, and consider whether a hard `required` rule should be a soft `preferred` one. A preferred affinity expresses a wish without making it a filter, so the scheduler honors it when possible and places the workload anyway when not, which prevents a label gap from turning into an outage. Reserve hard requirements for cases where running on the wrong worker would be genuinely incorrect, such as a workload that must use local NVMe storage, and use preferences everywhere a wrong placement would merely be suboptimal.

## Cause Five: A PersistentVolumeClaim That Will Not Bind

A workload that mounts storage cannot schedule until its `PersistentVolumeClaim` binds to a volume. When the claim stays `Pending`, the workload stays Pending with it, and the event may read `had volume node affinity conflict` or simply point at the unbound claim. The diagnosis moves from the workload to the claim, and from the claim to the storage class and the provisioner behind it.

Start at the claim and read its events, which name the storage problem directly:

```bash
kubectl get pvc -n <namespace>
kubectl describe pvc <claim-name> -n <namespace>
```

A claim shown as `Pending` rather than `Bound` falls into a few recognizable patterns. The storage class named in the claim may not exist, because of a typo or because the cluster was provisioned without it, and the claim then has no provisioner to satisfy it. Confirm the available classes:

```bash
kubectl get storageclass
```

A second pattern is a zone conflict. Azure managed disks are zonal resources, and a disk provisioned in one availability zone can only attach to a worker in that same zone. With the `WaitForFirstConsumer` binding mode the provisioner waits to learn which zone the workload lands in before creating the disk, which avoids the conflict, but with the older `Immediate` mode the disk is created first and the scheduler must then find a worker in the disk's zone. If no worker exists in that zone, the workload reports a volume node affinity conflict and waits. The fix is to use `WaitForFirstConsumer` so disk and workload are placed together:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: managed-csi-zone-aware
provisioner: disk.csi.azure.com
volumeBindingMode: WaitForFirstConsumer
parameters:
  skuName: Premium_LRS
```

### Why is my pod Pending with a perfectly valid PVC?

Because validity is not the same as bindability. A claim can be well-formed and still wait if its storage class has no provisioner, if the requested access mode is unsupported by the disk type, or if a zonal disk has been pinned away from where the workload can run. The claim's own events name which of these applies, so the rule is to debug the claim first and the workload second, since the workload is merely a hostage to the claim.

A third pattern concerns access modes. Azure managed disks support `ReadWriteOnce`, meaning a single worker may mount the disk at a time, while a workload spread across workers that all demand `ReadWriteMany` on a disk-backed claim cannot be satisfied by managed disks at all. The remedy is to switch the workload to a file-backed share through Azure Files, which supports shared read-write access, when multiple replicas must write the same volume. Choosing the wrong storage primitive for the access pattern produces a claim that can never bind, and recognizing that early saves a long hunt through provisioner logs.

When the cause is a missing class, create the class your claim expects, or repoint the claim at an existing class. When the cause is a provisioner error, the claim events carry the provisioner's message, and that message, not the workload, is where the next step lives. Treating storage-driven Pending as a workload problem rather than a claim problem is the recurring misdiagnosis here, and the discipline of describing the claim first prevents it.

## Cause Six: Address Exhaustion Under Azure CNI

This family is the one that most often sends engineers in the wrong direction, because the message blames the platform rather than the workload and the workload itself looks beyond reproach. Under the Azure CNI networking model, every workload receives a real IP address from the subnet the cluster's workers live in. When that subnet runs out of addresses, new workloads cannot be assigned an IP, and they sit Pending or fail at sandbox creation with a message about IP allocation, even though CPU, memory, taints, affinity, and storage are all perfectly fine.

The arithmetic behind this is the part worth internalizing. With Azure CNI in its traditional mode, each worker reserves a block of IP addresses up front, one for the worker plus a configured number for the workloads it can host, often around thirty. A pool of ten workers can therefore consume more than three hundred subnet addresses before a single workload is even running, and a subnet sized for a handful of virtual machines is exhausted almost immediately. The cluster appears to have ample compute while the network silently caps how many workloads can ever be placed.

### How do I confirm the subnet has run out of addresses?

Read the subnet's available address count against its size. A subnet with a small prefix offers few usable addresses after Azure reserves several at each end, and Azure CNI's per-worker reservation can outpace it quickly. The platform reports the available count, and when it sits at or near zero while workloads report IP allocation failures, address exhaustion is confirmed and the fix lives in the network, not the cluster.

```bash
az network vnet subnet show \
  --resource-group <rg> \
  --vnet-name <vnet> \
  --name <subnet> \
  --query "{prefix:addressPrefix,available:availableIpAddressCount}" -o table
```

Several remedies exist, and they differ in disruption. The least invasive is to reduce the per-worker IP reservation by lowering the maximum pod count on future pools, which shrinks the block each new worker claims and stretches the remaining addresses further. This helps only for pools you create or replace, since the reservation is fixed when a worker joins.

A more thorough remedy is to move to the overlay networking model, where workloads draw addresses from a private overlay range rather than from the subnet, so the subnet only needs enough addresses for the workers themselves. Overlay decouples workload density from subnet size and removes the exhaustion ceiling for most clusters. Migrating a running cluster's networking model is a significant change and is planned, not performed mid-incident, but for a cluster repeatedly hitting this wall it is the durable answer.

The immediate, in-incident remedy when a subnet is full and a migration is not on the table is to expand the address space available to the cluster, by widening the subnet's prefix where the surrounding virtual network has room, or by attaching additional address space. This is bounded by how the virtual network was originally laid out, which is why network sizing for AKS deserves attention at provisioning time rather than at the moment of exhaustion. The lesson this family teaches is that an AKS cluster is a network consumer first and a compute consumer second, and a subnet that was sized as an afterthought will cap the cluster long before the workers fill up.

## Cause Seven: A Subscription Quota or Regional Capacity Limit

The last family lives entirely outside Kubernetes. The scheduler is willing, the autoscaler is willing, every predicate would pass on a new worker, and yet no worker appears, because Azure itself declines to create the virtual machine. The autoscaler status reports a failed scale-up rather than a declined one, and the underlying message names a quota that has been reached or a SKU that the region cannot currently provide.

The most common form is a regional vCPU quota. Every subscription carries a per-region, per-SKU-family limit on the total virtual CPUs it may run, and a cluster that tries to grow past that ceiling cannot add workers regardless of how reasonable the request is. Read your usage against the quota for the family your workers use:

```bash
az vm list-usage --location <region> -o table | grep -i "Standard Dv5"
```

The output pairs the current usage with the limit for each family. When current equals limit, you have found the ceiling, and the remedy is a quota increase request through the Azure portal's usage and quotas blade or the support channel, which is an administrative action with its own lead time rather than a command you run in the cluster. Planning capacity ahead of a known growth event, rather than discovering the quota during an incident, is the only way to keep this family from becoming an outage.

### Why does a scale-up fail even though I have budget and nodes?

Budget and quota are unrelated. Quota is a count of resources you are permitted to allocate, set independently of how much you are willing to spend, and a brand-new or recently scaled subscription often carries conservative defaults that are far below what a production cluster needs. A scale-up can also fail because the specific SKU has no capacity in the region or availability zone at that moment, which is a transient platform condition rather than a quota you can raise. The autoscaler status distinguishes a quota refusal from a capacity refusal, and the distinction changes whether you file a quota request or choose a different SKU or zone.

A subtler version of this family is zonal capacity. A cluster pinned to a single availability zone depends on that zone having the requested SKU available, and a zone under pressure can refuse new allocations of a popular machine size even when the regional quota has room. Spreading a pool across zones, or choosing a SKU family with broader availability, reduces exposure to a single zone's momentary scarcity. For a deeper treatment of vCPU limits and the request process, the dedicated walkthrough of [Azure quota exceeded and vCPU limit errors](/2022/11/07/fix-azure-quota-exceeded/) covers the administrative path end to end, and pairs naturally with this section whenever the autoscaler reports a failed rather than declined scale-up.

## The Requests-Not-Limits Rule, Stated Plainly

Across all seven families, one principle does the most diagnostic work, and naming it makes it portable to the next incident. The requests-not-limits rule holds that the Kubernetes scheduler places a workload using only its resource requests and its placement predicates, never its limits, so a workload that refuses to schedule is, with very few exceptions, asking for more than any worker can offer or violating a constraint the `FailedScheduling` events name explicitly. Everything in this guide is an application of that rule to a different layer of the platform.

The rule explains why the same instinct fails repeatedly. Raising a workload's limits to "give it more room" does nothing for a scheduling failure, because limits are a runtime cap the scheduler ignores. Scaling the replica count higher when one replica will not fit only multiplies the unschedulable copies. Restarting the deployment re-submits the same request against the same constraints and produces the same verdict. Each of these is an attempt to fix a placement problem with a runtime tool, and the rule predicts in advance that each will fail.

### What is the single most reliable first move on any Pending pod?

Read the `FailedScheduling` event and treat its message as the diagnosis, not as noise. The scheduler has already done the analysis and recorded which predicate eliminated which workers; the per-worker tally tells you whether you face resource starvation, a taint, an affinity miss, or a platform refusal. Acting before reading is the error the rule is designed to prevent, because the answer is almost always sitting in the events you skipped.

The rule also reframes prevention. If placement is governed by requests and predicates, then a cluster that rarely produces Pending workloads is one whose requests reflect real consumption, whose taints and affinity rules match the workers that actually exist, whose storage classes bind in the zones where workloads run, and whose subnet and quota were sized for the cluster's true scale. Pending is, in this light, a feedback signal about the honesty of your declarations, and treating each incident as a chance to correct an inflated request or a stale label compounds into a cluster that schedules cleanly.

## Preventing Pending Pods Before They Page You

Diagnosis fixes the incident in front of you; prevention keeps the next one from forming. The practices below address the families at their source, and each follows directly from a cause section above.

Size requests from measurement rather than habit. The metrics server and the requests-not-limits rule together let you set requests that reflect a workload's real working set, which keeps workers densely and honestly packed and stops inflated requests from manufacturing artificial starvation. Periodically compare requested against actual consumption across the cluster and trim the workloads that ask for far more than they use, because every overstated request shrinks the headroom available to legitimate work.

Give the autoscaler real headroom and honest bounds. A pool whose maximum is set just above its steady-state size has no room to absorb a burst, and the autoscaler ceiling becomes the first thing a spike hits. Set maximums with a margin for the largest expected surge, and confirm the autoscaler is actually enabled on the pools you believe elastic, since a pool that was provisioned static will never grow on its own. The behavior of the horizontal, vertical, and cluster autoscalers together is worth understanding in depth, and the dedicated treatment of [AKS autoscaling across HPA, VPA, and the cluster autoscaler](/2024/08/12/aks-autoscaling-explained/) explains how they interact so a scale-up that should happen actually does.

Keep taints, labels, and affinity in sync with the pools that exist. Most taint and affinity Pending incidents come from drift, where a manifest expects a label or tolerates a taint that no current pool carries. Manage labels and taints at the pool level so new workers inherit them, review affinity rules when you add or retire a pool, and prefer soft `preferred` affinity to hard `required` affinity wherever a wrong placement would be merely suboptimal rather than incorrect.

Size the network and the quota for the cluster you are growing into, not the one you have today. Subnet exhaustion and quota ceilings are provisioning decisions disguised as incidents, and both have lead times that make them painful to fix under pressure. Lay out the virtual network with address space for the cluster's projected density, prefer the overlay networking model when density is high, and file quota increases ahead of known growth so the autoscaler never meets a wall you could have moved in advance. A foundational understanding of how AKS structures node pools, networking, and the control plane underpins all of this, and the [Azure Kubernetes Service architecture and node-pool model explained](/2022/01/17/azure-kubernetes-service-aks-explained/) lays that groundwork for anyone designing a cluster meant to scale cleanly.

Finally, build the diagnostic habit into your team's runbook. A Pending workload should trigger a fixed sequence, describe the workload and read the events, compare requests to allocatable headroom, check the autoscaler status, inspect taints and affinity, and describe any claim, before anyone mutates the cluster. Codifying that order turns a stressful incident into a short checklist and prevents the speculative changes that the requests-not-limits rule predicts will fail.

## Failures Often Mistaken for a Pending Pod

Several other states look like Pending from a distance and are routinely confused with it, sending engineers to apply a placement fix to a runtime problem or the reverse. Telling them apart at a glance saves the whole misdirected investigation, and each lives in a different phase of a workload's life.

`ContainerCreating` is the closest neighbor and the most often confused. A workload in this state has already been scheduled successfully, a worker was chosen, and the kubelet there is now pulling images, mounting volumes, or wiring up networking. The placement problem this guide addresses is already solved by the time a workload reaches ContainerCreating, so reading scheduler events is pointless; the relevant signals are image pull progress and volume mount status on the chosen worker. If a workload sticks in ContainerCreating because of a volume that mounts slowly or an image that pulls forever, the diagnosis lives on the worker, not in the scheduler.

`ImagePullBackOff` and `ErrImagePull` belong to the same post-scheduling phase. The workload was placed and the kubelet then failed to fetch the container image, because of a wrong image name, a missing registry credential, or an unreachable registry. This is a runtime fetch problem with nothing to do with capacity or constraints, and the dedicated guide to [fixing AKS ImagePullBackOff and ErrImagePull](/2022/07/11/fix-aks-imagepullbackoff/) walks the registry, tag, and credential causes that produce it. The tell is that the workload reached a worker at all, which a Pending workload never does.

`CrashLoopBackOff` sits one phase further along still. The workload scheduled, the image pulled, the container started, and then the process inside it exited and kept exiting, so the kubelet keeps restarting it with growing backoff. This is squarely an application or configuration failure, and treating it as a scheduling problem wastes the investigation. The full triage for it lives in the guide to [diagnosing AKS CrashLoopBackOff by root cause](/2022/07/18/fix-aks-crashloopbackoff/), which is the natural next stop once a previously Pending workload finally schedules and then begins crashing, since fixing the placement problem can simply expose the next failure in line.

### How do I tell a scheduling problem from a startup problem in one command?

Run `kubectl get pods` and read the status column, then read the events with `kubectl describe`. A `Pending` status with `FailedScheduling` events is a placement problem the scheduler owns. A `ContainerCreating`, `ImagePullBackOff`, or `CrashLoopBackOff` status means placement already succeeded and the problem moved to the kubelet or the application. The status word plus the event source together make the branch unambiguous, and choosing the right guide depends entirely on that branch.

One more state deserves mention because it masquerades as Pending without being a scheduling failure at all. A workload that depends on an init container which never completes, or that is blocked by an admission webhook holding it before scheduling, can appear stalled in ways that resemble Pending. Reading the events distinguishes these too, since an admission rejection or a stuck init container produces messages that name the webhook or the init container rather than a `FailedScheduling` line from the scheduler. The discipline of reading the event source, not just the status word, keeps these edge cases from derailing the diagnosis.

## A Worked Diagnosis From Symptom to Fix

To tie the families together, walk a representative incident the way a calm responder would. A deployment is updated to a larger memory footprint and one of its replicas will not come up. `kubectl get pods` shows the replica as `Pending`, which immediately rules out the runtime states above and points at the scheduler.

The responder describes the workload and reads the events:

```bash
kubectl describe pod web-7c9f-abcde -n production
```

The events end with a repeating line: `0/4 nodes are available: 4 Insufficient memory`. That message is decisive. Four workers, all four eliminated for memory, which is the Cause One signature. The responder does not scale replicas, restart the deployment, or raise limits, because the requests-not-limits rule predicts those moves will fail. Instead the responder reads the request and the headroom:

```bash
kubectl get pod web-7c9f-abcde -n production \
  -o jsonpath='{.spec.containers[*].resources.requests.memory}'
# 6Gi

kubectl describe node aks-pool-21 | grep -A4 "Allocatable"
# memory: 6800Mi allocatable, ~5100Mi already committed
```

The request is 6 gibibytes; the roomiest worker has roughly 1.6 gibibytes free. No worker can host the replica, which confirms resource starvation rather than any other family. Now the decision is which remedy fits. The responder checks whether the request is honest:

```bash
kubectl top pod -n production -l app=web
# steady-state usage near 2Gi
```

The workload uses about 2 gibibytes but requests 6, an inflated request copied during the update. The correct fix is to lower the request to match reality with margin, not to grow the cluster, which would spend money to accommodate a number that was wrong. The responder edits the request down to something like 3 gibibytes, applies the change, and the replica schedules onto an existing worker within seconds. Had the workload genuinely needed 6 gibibytes, the responder would have checked the autoscaler status next, and if the pool were maxed or the SKU too small, moved to a larger worker pool. The branch at each step is driven by what the events and the headroom say, never by a reflex.

This is the shape of every clean Pending diagnosis: read the verdict, identify the family from its signature, confirm with one targeted check, and choose the remedy the confirmation points to. The speed comes not from knowing the fix in advance but from refusing to act before reading, and that refusal is the entire discipline.

## Reading the Signature at a Glance

With every family walked, the diagnosis collapses into a single skill: matching the `FailedScheduling` message to its signature and acting on what the message already states. A clause mentioning insufficient CPU or memory points at resource starvation, resolved by comparing the request to allocatable headroom and then trimming the request, adding capacity, or moving to a larger worker size. A clause about a maxed pool or a declined scale-up points at the autoscaler, resolved by reading its status configmap and either raising a ceiling or sizing a pool whose workers can actually host the workload. A clause naming an untolerated taint points at a placement guard, resolved by adding a precise toleration or, more rarely, removing a taint whose purpose you have confirmed.

A clause about an affinity or selector that matched nothing points at a label mismatch, resolved by reconciling the rule with the labels the cluster carries and softening hard requirements into preferences where a wrong placement would merely be suboptimal. An unbound claim points at storage, resolved at the claim and its storage class rather than at the workload, usually by adopting the zone-aware binding mode. A platform message about IP allocation points at subnet exhaustion under Azure CNI, resolved in the network rather than the cluster. A failed scale-up naming a quota or capacity limit points outside Kubernetes entirely, resolved by a quota request or a SKU and zone choice. Each signature names one family, each family has one confirming check, and each check chooses among a small set of deliberate remedies. The speed of a seasoned responder comes entirely from trusting that mapping and reading before reaching for the keyboard.

## The Verdict on Pending Pods in AKS

A Pending workload in Azure Kubernetes Service is the most legible failure the platform produces, because the scheduler writes its reasoning into the events before you ever start investigating. The whole craft of resolving it is reading that reasoning and routing it to the correct layer: requests against capacity for starvation, the autoscaler status for scaling ceilings, taints and affinity for placement constraints, the claim's events for storage, and the subnet and quota for platform exhaustion. Every one of the seven families announces itself in the `FailedScheduling` message, and the requests-not-limits rule explains why the common reflexes, scaling replicas, raising limits, restarting deployments, fail against all of them.

The engineers who resolve Pending quickly are not the ones who memorized fixes; they are the ones who built the habit of reading the scheduler's verdict first and acting second. That habit generalizes. It makes you size requests honestly, design node pools and affinity rules that match the workers you actually run, and provision networks and quotas for the scale you are growing into. Pending, treated this way, stops being an incident to dread and becomes a precise, well-documented signal about the gap between what your workloads declare and what your cluster can provide, which is exactly the gap a well-run platform keeps small.

To put this into practice on a cluster you control, you can [reproduce a Pending pod and work through every FailedScheduling signature in the hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html), and then [drill the diagnosis under realistic incident conditions with the scenario-based troubleshooting exercises on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html), so that reading the scheduler's verdict becomes reflex before the next page arrives rather than during it.

## Understanding the Scheduler's Filter and Score Phases in Depth

The two-phase model sketched earlier rewards a closer look, because the more precisely you understand how the scheduler reasons, the faster you read its verdict. Each unscheduled workload passes through filtering, where workers that cannot host it are discarded, and then scoring, where the survivors are ranked and the best is chosen. Pending incidents are almost always filter-phase failures, and knowing which predicates run during filtering tells you exactly what the `FailedScheduling` message is reporting on.

The filter predicates check a fixed set of conditions, and each maps to a family in the cause table. A fit predicate confirms the worker has enough allocatable CPU, memory, and ephemeral storage for the request, which is Cause One. A pod-count predicate confirms the worker is below its maximum pod ceiling, which is the `Too many pods` variant. A taint-toleration predicate confirms the workload tolerates every taint on the worker, which is Cause Three. A node-affinity predicate confirms the workload's selector and required affinity match the worker's labels, which is Cause Four. A volume predicate confirms any required volume can attach to the worker, often a zonal check, which is Cause Five. When you read a `FailedScheduling` message, you are reading which of these predicates rejected each worker, expressed as a tally.

### What happens during the scoring phase, and can it cause Pending?

Scoring runs only on workers that survived filtering, and it ranks them by spread, by how well the request packs, by image locality, and by other soft preferences such as a `preferred` affinity. Scoring never produces Pending on its own, because it operates on candidates that already passed filtering; if even one worker survives the filter, scoring picks among the survivors and the workload schedules. Pending therefore always means the filter eliminated everything, which is why every remedy in this guide targets a filter predicate rather than a scoring weight. A soft `preferred` affinity that goes unsatisfied lowers a worker's score but never removes it from contention, which is precisely why preferring over requiring prevents so many Pending incidents.

The distinction between hard and soft constraints runs through the entire scheduling model and is worth holding firmly. A hard constraint, expressed by `requiredDuringSchedulingIgnoredDuringExecution` for affinity or by a `NoSchedule` taint without a toleration, participates in filtering and can leave a workload Pending. A soft constraint, expressed by `preferredDuringSchedulingIgnoredDuringExecution` or by the weaker `PreferNoSchedule` taint effect, participates only in scoring and bends rather than blocks. Every time you write a placement rule you are choosing which phase it lives in, and choosing a hard constraint where a soft one would do is the most common way teams manufacture future Pending incidents for themselves.

There is also a topology dimension that the score phase governs through spread constraints. A `topologySpreadConstraints` rule with a `whenUnsatisfiable` value of `DoNotSchedule` is a hard constraint that participates in filtering, so a workload that cannot satisfy its spread requirement, for example one that demands even distribution across three zones when only two have capacity, can go Pending on the spread predicate alone. Setting `whenUnsatisfiable` to `ScheduleAnyway` moves the rule into scoring, where it shapes placement without blocking it. Reading a `FailedScheduling` message that names a spread constraint points you straight at this setting, and the remedy is usually to soften the constraint or to add capacity in the underrepresented topology domain.

Understanding the predicates also clarifies why two workloads with seemingly identical specs can behave differently, where one schedules and its neighbor goes Pending. The difference is almost always a field that participates in filtering, a slightly larger request, an extra toleration the scheduling one carries, a selector the Pending one adds, or a volume the Pending one mounts. Diffing the two specs field by field, with attention to requests, tolerations, selectors, affinity, and volumes, surfaces the deciding field quickly, and it is invariably one the filter phase reads. This diffing habit turns a confusing "why this one and not that one" into a mechanical comparison with a definite answer.

## When System Pods and DaemonSets Will Not Schedule

Most Pending discussions assume an ordinary application workload, but system components and DaemonSets follow slightly different rules, and a Pending system workload can destabilize the cluster in ways an application workload does not. Recognizing when the stuck workload is a platform component changes both the urgency and the fix.

A DaemonSet is meant to run one copy on every eligible worker, and its scheduling is governed by the same predicates as any workload, with one important wrinkle: DaemonSet workloads commonly carry tolerations for the taints that ordinary workloads do not, precisely so they can run on system and specialized pools. When a DaemonSet workload goes Pending, the usual cause is that a new worker carries a taint the DaemonSet does not tolerate, or that the DaemonSet's own resource request cannot fit alongside everything already packed onto a worker. The fix mirrors the application cases, add the missing toleration or make room, but the consequence of leaving it unfixed is broader, because a DaemonSet often provides logging, networking, or monitoring that the rest of the cluster depends on.

### Why would a kube-system pod be stuck Pending?

A platform workload in the `kube-system` namespace usually goes Pending for the same reasons application workloads do, most often because the system pool has no room or because a worker it targets carries an incompatible taint. The difference is impact: a Pending core component can degrade DNS, networking, or metrics for the whole cluster, so it deserves immediate attention. Read its events the same way, but treat the system pool's capacity and taints as the first suspects, since system pools are often small and tightly constrained by design.

System pools in AKS are deliberately kept lean and are often tainted to keep application workloads off them, which means a system component that grows or a system pool that shrinks can produce Pending where there was headroom before. The remedy is rarely to loosen the system pool's protections, since those exist to keep platform components isolated from noisy application work. It is usually to ensure the system pool is sized for its actual occupants and to keep application workloads, with their own tolerations, from creeping onto it. A system pool that has been allowed to host application workloads is both a stability risk and a frequent source of Pending for the components that pool was meant to guarantee.

A related case is the workload that must run before the cluster is fully ready, such as a CNI or storage driver component during a node's join. If that component cannot schedule, the worker may never become fully `Ready`, which then shrinks the capacity available to everything else, producing application Pending as a downstream effect. Tracing an application Pending incident back to a stuck platform component is a less obvious path, but reading the state of `kube-system` workloads whenever capacity seems mysteriously short is a habit that catches these layered failures early.

## Gathering Cluster-Wide Signal When One Pod Is Not Enough

Describing a single workload answers most Pending incidents, but some require a wider view, particularly when many workloads go Pending at once or when the cause sits in the cluster's overall state rather than in one spec. A handful of cluster-scoped reads turn a confusing multi-workload incident into a clear picture.

When several workloads go Pending together, read the events across the whole cluster rather than one workload at a time, sorted so the newest sit last:

```bash
kubectl get events -A --sort-by='.lastTimestamp' | tail -40
```

A burst of `FailedScheduling` events with the same message points at a cluster-wide cause, a pool that filled, an autoscaler that stopped scaling, a subnet that exhausted, or a quota that was reached, rather than at a problem unique to one manifest. The shared message is the fast route to the family, and it saves describing each affected workload separately.

To see the capacity picture across every worker at once, read allocation cluster-wide:

```bash
kubectl describe nodes | grep -E "Name:|Allocated resources" -A6
```

This reveals whether the whole cluster is near saturation or whether one pool is full while another sits idle, which distinguishes a genuine capacity shortage from a placement constraint steering everything toward the wrong pool. A cluster with idle workers and Pending workloads almost always has a constraint problem, a taint, an affinity, or a selector, rather than a capacity problem, because real capacity exists but the workloads are forbidden from using it.

### How do I check whether a node is even available to the scheduler?

Run `kubectl get nodes` and confirm each worker shows `Ready` without `SchedulingDisabled`. A worker in `NotReady`, one that is cordoned, or one mid-drain does not count toward the scheduler's available candidates, so capacity you believe exists may be invisible to placement. Reconcile the worker count the scheduler reports in its `FailedScheduling` tally against the count of genuinely `Ready` workers, and any gap is a worker that needs attention before the capacity math will hold.

The cluster-wide view also catches a class of incident where the trigger is an infrastructure change rather than a workload change. A node pool upgrade that cordons and drains workers one at a time temporarily reduces capacity, and workloads with tight headroom can go Pending during the rollout and recover after it. A spot pool reclamation can evict workers en masse, leaving their workloads Pending until replacements arrive. A maintenance operation that cordons a pool removes it from scheduling entirely. None of these is a manifest problem, and describing a single workload would not reveal them; the cluster-wide event stream and the worker readiness list make them obvious. Whenever a Pending incident coincides with a known infrastructure operation, check the timing before assuming the workloads themselves changed, because the cluster's own activity is often the cause.

Finally, when the signal still seems incomplete, the scheduler's own logs and the autoscaler's events fill the remaining gaps. The autoscaler records every scale decision and refusal, and reading its event stream alongside the cluster-wide workload events reconstructs the sequence: a burst of Pending workloads, the autoscaler's attempt or refusal to add capacity, and the platform's response if it tried. That reconstructed timeline is what turns a noisy incident into a single sentence, such as "the pool hit its maximum, the autoscaler declined, and twelve workloads waited," which is exactly the kind of precise statement that points at one fix rather than many guesses.

## Namespace Quotas and LimitRanges That Shape Whether a Pod Schedules

Two namespace-scoped objects influence scheduling in ways that are easy to overlook because they live one layer above the workload spec, and both can leave engineers staring at a Pending or rejected workload whose own manifest looks blameless. A `ResourceQuota` caps the total requests and limits a namespace may consume, and a `LimitRange` sets default and bounded values for any workload that does not specify its own. Neither is part of the scheduler's filter phase, yet both change the request the scheduler ultimately reads, so they belong in any complete account of why a workload will not run.

A `ResourceQuota` does its work at admission rather than at scheduling. When a namespace has a quota and a new workload would push the namespace's total requested CPU, memory, or object count past the cap, the API server rejects the workload before it is ever admitted, which can look like a Pending problem from a dashboard that only shows workload counts. The tell is that the workload does not appear in `kubectl get pods` at all, or that the controller that owns it, a Deployment or a Job, reports a quota failure in its own events. Read the quota and its current usage to confirm:

```bash
kubectl get resourcequota -n <namespace>
kubectl describe resourcequota <quota-name> -n <namespace>
```

The description shows used against hard for each tracked resource. When used has reached hard for requested CPU or memory, no further workloads can be admitted to the namespace until existing ones are removed or the quota is raised. The fix is a deliberate choice between trimming overstated requests on existing workloads, which frees quota without raising the cap, and raising the quota itself, which is appropriate when the namespace genuinely needs to grow. Raising a quota that exists to protect a shared cluster from one team's overconsumption should be a conversation rather than a reflex, since the quota is doing exactly what it was created to do.

### Why does my deployment create no pods at all instead of Pending ones?

Because a `ResourceQuota` rejection happens before scheduling, so the workload is never admitted and therefore never reaches the Pending phase. Look at the owning controller's events with `kubectl describe deployment` or `kubectl describe replicaset`, where a message about exceeded quota appears. This is distinct from true Pending, where the workload exists and waits on the scheduler. The two feel similar from a monitoring view that counts running replicas, but they live in different phases, and the quota case is resolved by freeing or raising quota rather than by anything in the scheduler.

A `LimitRange` interacts with Pending from the opposite direction, by changing requests rather than capping them. When a namespace has a `LimitRange` with default requests, any workload that omits its own requests inherits those defaults, and a generous default can quietly inflate a workload's request to a size that no worker can host, producing a resource-starvation Pending whose request the author never wrote. The workload's effective request, the one the scheduler reads, then differs from the empty `requests` block in the original manifest, which is why a workload that "asks for nothing" can still fail to schedule. Read the namespace's limit range to see what defaults are being applied:

```bash
kubectl get limitrange -n <namespace>
kubectl describe limitrange <range-name> -n <namespace>
```

If the default request is larger than you expected, the remedy is either to set explicit, measured requests on the workload so it no longer inherits the inflated default, or to adjust the limit range's defaults to reflect realistic sizing. A `LimitRange` can also enforce minimum and maximum requests, rejecting a workload whose explicit request falls outside the allowed band, which is another admission-time rejection that masquerades as a scheduling problem. Reading the range tells you whether your workload is being reshaped or rejected by policy before the scheduler ever sees it.

The broader lesson is that the request the scheduler reads is the product of three inputs, the workload's own spec, any `LimitRange` defaults the namespace applies, and the admission gate that a `ResourceQuota` imposes, and a complete diagnosis accounts for all three. A workload that will not schedule because of an inflated request may have inherited that request from a limit range rather than declared it, and a workload that never appears at all may have been turned away by a quota rather than the scheduler. Checking the namespace's quota and limit range whenever a workload's scheduling behavior does not match its manifest closes the gap between what the author wrote and what the platform actually evaluated, and it resolves a category of incident that examining the workload alone can never explain.

This namespace layer also explains a confusing pattern in shared clusters where the same manifest schedules cleanly in one namespace and fails in another. The manifest is identical; the namespaces differ in their quotas and limit ranges, so the effective request and the admission outcome differ too. When a workload behaves differently across namespaces, compare the `ResourceQuota` and `LimitRange` objects in each before suspecting the workload, because the namespace policy is almost certainly the variable that changed. Treating the namespace as part of the workload's effective specification, rather than as a neutral container, is what makes these cross-namespace puzzles tractable.

## Spot Node Pools and the Pending Pods They Produce

Spot node pools deserve their own treatment because they generate Pending incidents through a mechanism that the cost savings tempt teams into without fully appreciating. Spot workers run on Azure's surplus capacity at a steep discount, and that capacity can be reclaimed at any time with little warning, so spot pools carry a taint that keeps workloads off them unless those workloads explicitly tolerate interruption. Two distinct Pending patterns follow from this design, and both are predictable once the trade is understood.

The first pattern is the toleration gap covered earlier from the taint angle: a team moves workloads onto spot to save money but omits the spot toleration, so every workload is filtered off the tainted spot workers and waits. The second pattern is subtler and specific to spot economics. When Azure reclaims spot capacity, the affected workers disappear, their workloads are evicted, and those workloads go Pending until replacement spot capacity becomes available, which may take seconds, minutes, or in a constrained region considerably longer. A cluster that runs critical workloads exclusively on spot will see them go Pending precisely when spot capacity is scarce, which is often exactly when demand is highest.

### How should I design around spot pool evictions to avoid Pending outages?

Keep workloads that must stay up off spot, or give them a fallback. The durable pattern is a mixed-pool design where a small on-demand pool guarantees a floor of capacity for critical workloads and a larger spot pool absorbs interruptible or batch work at a discount. Critical workloads tolerate only the on-demand pool or treat spot as a preference rather than a requirement, so a reclamation degrades capacity without taking the workload down. Batch and stateless work can live happily on spot, accepting occasional Pending stretches in exchange for the cost saving, because a delayed batch job is a tolerable outcome where a downed service is not.

The reclamation pattern also interacts with the autoscaler in a way worth anticipating. When spot workers vanish, the autoscaler tries to replace them, and if the regional spot capacity is exhausted the replacement fails, leaving the evicted workloads Pending with an autoscaler note about unavailable capacity rather than a configuration ceiling. This is a capacity refusal, not a quota one, and it is not something a quota increase fixes; the remedy is design, spreading across zones or SKU families to reduce exposure to any single pool's scarcity, or keeping critical work on on-demand capacity that does not get reclaimed. Recognizing a spot reclamation in the autoscaler events, rather than chasing it as a quota or configuration problem, points you at the architectural answer instead of an administrative dead end.

## A Second Worked Diagnosis: The Constraint That Hid in Plain Sight

The first worked example resolved a resource-starvation case. A constraint case unfolds differently and is worth walking, because the trap there is that capacity exists and the workload still will not schedule, which tempts every wrong instinct at once.

A team adds a workload that must run on workers with local NVMe storage, expressed as a hard node affinity for the label `storagetier=nvme`. The workload goes Pending. The dashboard shows the cluster has plenty of free CPU and memory, so the team's first instinct is that the cluster is fine and the workload is somehow broken, and someone proposes deleting and recreating it. The responder instead reads the events:

```bash
kubectl describe pod analytics-engine-0 -n data
# FailedScheduling: 0/6 nodes are available: 6 node(s) didn't match Pod's node affinity/selector
```

Six workers, all six eliminated on affinity, which is the Cause Four signature and immediately rules out capacity despite the free compute the dashboard shows. The responder compares the required label against what the workers carry:

```bash
kubectl get pod analytics-engine-0 -n data \
  -o jsonpath='{.spec.affinity.nodeAffinity}'
# requires storagetier in (nvme)

kubectl get nodes --show-labels | grep -o 'storagetier=[^,]*' | sort -u
# storagetier=ssd
```

The cluster's workers are labeled `storagetier=ssd`; not one carries `nvme`. The NVMe pool the affinity assumes was either never created or was deleted in an earlier cleanup, so the hard requirement matches nothing and the workload can never schedule as written. The responder now faces the same kind of branch as the first example, driven by intent. If the workload genuinely needs NVMe, the fix is to add an NVMe-backed pool with the expected label, and the affinity is correct. If the workload merely prefers fast storage but can tolerate SSD, the fix is to relax the hard `required` affinity to a soft `preferred` one, after which the scheduler honors the preference when an NVMe worker exists and places the workload on SSD when none does, eliminating the Pending entirely.

The team confirms with the storage owner that SSD is acceptable for now, softens the affinity to a preference, and the workload schedules within seconds onto an SSD worker, with the preference recorded so it will migrate to NVMe capacity once such a pool exists. The lesson repeats the first example's shape from a different family: read the verdict, recognize the signature, confirm with one targeted comparison, and let the confirmation choose between adding capacity and correcting the constraint. The free compute that tempted the team toward "the workload is broken" was a distraction the events cut through in a single line, which is why reading them first is the whole discipline.

## Frequently Asked Questions

### Q: Why is my AKS pod stuck in Pending?

A Pending workload means the Kubernetes scheduler could not place it on any worker. Read the `FailedScheduling` event with `kubectl describe pod` and the message names the constraint: `Insufficient cpu` or `Insufficient memory` for resource starvation, `had untolerated taint` for a taint mismatch, `didn't match Pod's node affinity/selector` for a label problem, or an unbound `PersistentVolumeClaim` for storage. The event includes a per-worker tally that tells you how many machines each constraint eliminated. That message is the diagnosis, so read it before changing anything, because the most common error is to scale replicas or restart the deployment without first reading why placement failed in the first place.

### Q: Can the cluster autoscaler being maxed out cause Pending pods?

Yes. The autoscaler will not grow a node pool past the maximum count you configured, so a pool already at its ceiling leaves new workloads Pending even though the autoscaler would otherwise add a worker. Read the `cluster-autoscaler-status` configmap in the `kube-system` namespace to see its reasoning. If the pool is at maximum, raise the bound with `az aks nodepool update` and the `--max-count` flag. The autoscaler also declines to scale when a brand-new worker still could not host the workload because the request exceeds the SKU's capacity, and in that case the answer is a larger worker size rather than a higher ceiling.

### Q: Does a taint without a matching toleration cause a Pending pod?

It does when every worker with capacity is tainted. A taint with the `NoSchedule` effect removes a worker from consideration for any workload that lacks the matching toleration, and if the only pool with room is tainted, the workload stays Pending with the message `had untolerated taint`. The event names the taint, so read it and either add the matching toleration to the workload spec when it belongs on those workers, or remove the taint when it was applied by mistake. Spot node pools are a frequent source of this, since spot workers carry a taint that only workloads explicitly willing to run on interruptible capacity should tolerate.

### Q: Why does a node selector or affinity rule leave my pod Pending?

Because the rule is evaluated against the labels workers actually carry, not against what the manifest author assumed. A `requiredDuringSchedulingIgnoredDuringExecution` affinity or a `nodeSelector` is a hard filter, so if no worker matches the required labels, every machine is eliminated and the workload waits with `didn't match Pod's node affinity/selector`. Compare the workload's selector to the output of `kubectl get nodes --show-labels`. The mismatch is usually a typo in a label, a label that was never applied to the pool, or a zone requirement the pool cannot satisfy. Fix the labels on the pool, correct the rule, or soften a hard requirement to a preference where a wrong placement would only be suboptimal.

### Q: Why is my pod Pending because of an unbound PVC?

A workload that mounts a `PersistentVolumeClaim` cannot schedule until that claim binds, so a claim shown as `Pending` rather than `Bound` keeps the workload Pending too. Describe the claim with `kubectl describe pvc` and its events name the problem: a storage class that does not exist, a zone conflict where a zonal disk cannot reach any worker, an unsupported access mode, or a provisioner error. The most common durable fix is to use the `WaitForFirstConsumer` binding mode so the disk is created in the same zone the workload lands in, which avoids the zonal conflict that the older `Immediate` mode can produce.

### Q: How do I read FailedScheduling events for a Pending pod?

Run `kubectl describe pod <name> -n <namespace>` and scroll to the `Events` section at the bottom. A stuck workload shows a repeating `Warning  FailedScheduling` line from the `default-scheduler`. The message after it carries a per-worker tally such as `0/5 nodes are available: 3 Insufficient cpu, 2 node(s) had untolerated taint`. Read each clause: the counts sum to your total worker count, and each clause names one constraint and how many machines it eliminated. When the counts do not add up to the workers you expect, a machine is likely NotReady or missing, which is itself a finding. This single block routes you to the responsible family faster than any other signal.

### Q: What is the difference between Pending and ContainerCreating?

`Pending` means the scheduler has not yet placed the workload on any worker, so the problem is placement and the signals live in the scheduler's events. `ContainerCreating` means placement already succeeded, a worker was chosen, and the kubelet there is now pulling images or mounting volumes, so the problem is startup and the signals live on the worker. Reading scheduler events for a ContainerCreating workload is wasted effort, and reading image or volume status for a Pending workload is equally pointless. The status word in `kubectl get pods` tells you which phase you are in and therefore where to look.

### Q: Will adding more replicas fix a Pending pod?

No, and it usually makes the situation harder to read. If one replica will not schedule because its request exceeds every worker's headroom or it violates a placement constraint, adding replicas simply creates more copies that fail the same filter, multiplying the Pending count without resolving the cause. The requests-not-limits rule predicts this: replicas do not change the request or the constraint that eliminated every worker. Fix the underlying constraint, by lowering an inflated request, adding capacity, or correcting a taint or affinity, and then scale the replica count once a single replica can actually be placed.

### Q: Does raising a pod's CPU or memory limit help it schedule?

It does not. The scheduler reads only the `requests` field during placement; the `limits` field caps runtime consumption and has no role in scheduling. A workload with a small request and a large limit schedules onto any worker that can satisfy the small request, while a workload with a large request will not fit a worker lacking that much free capacity regardless of its limit. If a Pending workload will not schedule, examine and adjust its request, not its limit, and measure actual usage with `kubectl top pod` so the request reflects the real working set rather than a guess.

### Q: Why does the autoscaler refuse to scale up for my Pending pod?

The autoscaler adds a worker only when doing so would let the Pending workload schedule. If the workload could not fit even on a fresh, empty worker of the pool's SKU, because its request exceeds that SKU's allocatable capacity, the autoscaler concludes scaling would not help and declines, recording that reasoning in its status configmap. It also declines when the pool that satisfies the workload's constraint is already at its maximum, and it fails outright when Azure cannot provision the worker due to a quota or capacity limit. Read the status to tell a deliberate refusal from a failed attempt, since they lead to different fixes.

### Q: How do I know if a subnet IP shortage is causing Pending pods?

Under Azure CNI, every workload consumes a real subnet address, and each worker reserves a block of addresses up front, so a modest cluster can exhaust a small subnet before the workers fill up. Check the available address count with `az network vnet subnet show` and read the `availableIpAddressCount`. When it sits at or near zero while workloads report IP allocation failures or stick at sandbox creation, address exhaustion is the cause. The remedies are to lower the per-worker pod maximum on new pools, expand the subnet where the virtual network has room, or migrate to the overlay networking model, which draws workload addresses from a private range and removes the subnet ceiling.

### Q: Can a subscription quota cause AKS pods to stay Pending?

Yes, indirectly. When the autoscaler tries to add a worker and Azure refuses because the subscription's regional vCPU quota for that SKU family is exhausted, the new worker never appears and the workload stays Pending. The autoscaler status reports a failed scale-up rather than a declined one. Check usage against the limit with `az vm list-usage` for your region and SKU family, and when current equals limit, request a quota increase through the portal's usage and quotas blade. A new or recently scaled subscription often carries conservative defaults well below production needs, so plan increases ahead of known growth rather than discovering them during an incident.

### Q: Why is a pod Pending when nodes show free CPU and memory?

Free compute does not guarantee a worker can host the workload. The worker may have reached its maximum pod count, which caps placements independent of CPU and memory and produces a `Too many pods` message. The workload may carry a node selector or affinity that matches no worker, or require a toleration for a taint the free workers carry. Storage may be the blocker, with an unbound claim holding the workload back regardless of compute. Under Azure CNI the subnet may be out of addresses even while compute is plentiful. Read the `FailedScheduling` event, which names the actual constraint rather than the one you assumed.

### Q: How do I compare a pod's request to a node's allocatable capacity?

Read both numbers and set them side by side. Get the workload's request with `kubectl get pod <name> -o jsonpath='{.spec.containers[*].resources.requests}'`, then read the worker's `Allocatable` block and `Allocated resources` block from `kubectl describe node <node>`. Allocatable is the total the scheduler may hand out, always less than raw capacity because the system reserves a slice, and the gap between allocatable and already-allocated is the room a new workload can claim. If the request is larger than that gap on every worker, you have confirmed resource starvation, and the fix is to lower the request, add capacity, or move to a larger worker SKU.

### Q: What does the WaitForFirstConsumer binding mode do for Pending pods?

It prevents the zonal conflict that leaves storage-bound workloads Pending. With the `Immediate` binding mode, the provisioner creates a zonal managed disk before knowing where the workload will run, and the scheduler must then find a worker in that disk's zone; if none exists, the workload waits with a volume node affinity conflict. `WaitForFirstConsumer` delays disk creation until the scheduler picks a worker, so the disk is provisioned in the same zone the workload lands in and the conflict cannot arise. Setting `volumeBindingMode: WaitForFirstConsumer` on the storage class is the standard remedy for zone-driven storage Pending in a multi-zone cluster.

### Q: My pod was Pending and now it is CrashLoopBackOff, what changed?

Fixing the placement problem let the workload schedule, and scheduling exposed the next failure in line. Pending is a pre-placement state, so while the workload was Pending no container had started and no application error could surface. Once you resolved the scheduling constraint, the workload landed on a worker, the image pulled, the container started, and the process inside it began exiting, which is `CrashLoopBackOff`. This is a different problem in a later phase, an application or configuration failure rather than a capacity or constraint one, and it is diagnosed by reading container logs and exit codes rather than scheduler events. The two failures are unrelated except that one was hidden behind the other.

### Q: Should I remove a taint or add a toleration to fix a Pending pod?

Prefer adding a precise toleration unless you are certain the taint serves no purpose. Taints on system pools protect platform components, and taints on spot or GPU pools steer the right workloads onto the right workers, so removing one can trade a Pending workload for a subtler instability where arbitrary workloads displace components that needed isolation. Add the matching toleration to the workloads that genuinely belong on the tainted workers, and remove a taint only when you have confirmed it was applied in error or no longer reflects how the pool is used. The narrow fix beats the broad one whenever the taint's intent is not fully clear.

### Q: How do I prevent Pending pods from recurring after I fix one?

Address the family at its source. Size requests from measured consumption rather than copied defaults so workers pack honestly and inflated requests stop manufacturing starvation. Give the autoscaler real headroom and confirm it is enabled on the pools you treat as elastic. Manage taints, labels, and affinity at the pool level so new workers inherit them and drift does not strand workloads. Size the subnet and the subscription quota for the scale you are growing into, since both have lead times that make them painful to fix mid-incident. Finally, codify the read-first diagnostic sequence into a runbook so the next incident becomes a short checklist rather than a round of speculative changes.

### Q: Why do the node counts in the FailedScheduling message not add up to my cluster size?

When the per-worker tally in a `FailedScheduling` message sums to fewer machines than you expect, the missing workers are usually not eligible for scheduling at all. A worker in the `NotReady` state, one cordoned for maintenance, or one that has left the cluster does not appear in the scheduler's count of available candidates. Run `kubectl get nodes` and look for any worker that is not `Ready` or that shows `SchedulingDisabled`. A NotReady or cordoned worker silently shrinks the capacity the scheduler can use, which can be the real reason a workload that used to fit no longer does, so reconcile the message's count against the healthy worker count before assuming the constraint is the whole story.

### Q: Can pod priority and preemption resolve a Pending pod?

They can, within limits. Kubernetes priority classes let a higher-priority workload preempt and evict lower-priority ones to make room when the cluster is full, so assigning a critical workload a higher priority can let it schedule by displacing less important work rather than waiting for new capacity. This helps only when lower-priority, evictable workloads occupy the space the Pending workload needs; it does nothing when every worker is full of equally or higher-priority work, or when the blocker is a taint, an affinity miss, an unbound claim, or address exhaustion rather than raw capacity. Use priority to protect critical workloads, not as a general substitute for sizing requests and capacity correctly.
