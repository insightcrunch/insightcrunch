---
layout: post
title: "Azure VM Performance Tuning Guide"
page_title: "Azure VM Performance Tuning: Find the Real Bottleneck in Disk, Network, CPU, and Memory Before You Resize"
date: 2024-07-29
categories: ["Technology"]
tags: ["Azure", "Virtual Machines", "Performance", "Networking", "Cloud Computing", "Cost Management"]
excerpt: "Azure VM performance tuning begins by finding the real bottleneck across disk, network, CPU, and memory, so you fix the limit instead of resizing blind."
image: "/assets/images/blog/blog-109.webp"
reading_time: 62
author: "gregory-marsh"
last_updated: 2026-08-13
lang: en
---
A virtual machine that feels slow is almost never slow for the reason the first guess assumes. Azure VM performance tuning fails most often because the engineer reaches for the resize button, moves from a Standard_D4s_v5 to a Standard_D8s_v5, watches the bill double, and finds the workload no faster than before. The capacity went up. The thing that was actually gating the work did not move at all. That gap, between the size of the machine and the limit that constrains it, is where most wasted spend and most wasted afternoons live.

![Azure VM performance tuning across disk, network, CPU, and memory bottlenecks - Insight Crunch](/assets/images/blog/blog-109.webp)

Every guest on Azure runs against four hard ceilings at once: how fast its attached storage can read and write, how fast packets move across its network interface, how much processor it can apply to a unit of work, and how much memory it can hold before paging begins. A workload runs at the speed of whichever ceiling it hits first. Everything else is headroom that does nothing until the binding ceiling rises. Tuning is the discipline of identifying which of the four is binding right now, raising only that one, confirming the gain with a measurement, and then asking whether a new ceiling has become the limit. The skill that separates a careful operator from a guesser is the refusal to spend money on a dimension that was never the constraint.

This guide builds that discipline into a repeatable method. It names the four dimensions and the metric that exposes each, lays out the lever that raises each ceiling with the measured effect and the cost it carries, and gives the commands to measure before and after so the gain is a number rather than a feeling. It treats the most common misdiagnosis as the central enemy: paying for a larger machine when the storage tier, not the machine, was holding the line. By the end the resize button becomes the last resort instead of the first reflex, reached for only after the evidence points to processor or memory as the true ceiling.

## Where the limit actually sits before you touch a single setting

The instinct to resize is understandable. The portal makes the size dropdown the most visible control, and the mental model that a bigger machine is a faster machine is intuitive. It is also wrong often enough to be expensive. A machine is a bundle of separately governed resources, and Azure caps several of them independently of the size you pick. The clearest example is storage. The managed disk you attach has its own provisioned ceiling for input and output operations per second and for megabytes per second of throughput, and that ceiling holds no matter how many virtual processors the host gives you. A Standard SSD that tops out near 6,000 IOPS will deliver near 6,000 IOPS whether it hangs off a two-core machine or a sixty-four-core one. Doubling the cores buys nothing for a job that spends its day waiting on that storage to acknowledge writes.

### Why does a bigger VM sometimes make no difference?

A bigger machine raises the processor and memory ceilings and the per-machine storage and network caps, but it cannot raise a per-disk limit that the storage tier itself sets. If the workload was waiting on a Standard SSD's IOPS or on a network path without Accelerated Networking, the extra cores sit idle and the elapsed time barely moves while the hourly rate climbs.

That single fact reorganizes the whole approach. Performance work is not a search for a faster machine. It is a search for the binding constraint, followed by a targeted change to that constraint alone. The four candidate constraints are storage, network, processor, and memory, and each announces itself with a distinct signal in the metrics. Read those signals first and the rest of the work becomes mechanical. Skip them and every change is a gamble dressed up as engineering.

### The find-the-bottleneck-first rule

The organizing principle of this guide is the find-the-bottleneck-first rule: a virtual machine runs at the speed of whichever of storage, network, processor, or memory saturates first, so the only change worth making is the one that raises the saturated dimension, and the only honest way to know which dimension is saturated is to measure it before spending. The rule sounds obvious stated plainly. In practice almost every wasted resize violates it, because measuring takes ten minutes of attention and clicking the size dropdown takes ten seconds of hope. The rule converts a habit of hope into a habit of evidence.

Stated as a sequence, the rule has four moves. Establish a baseline under real load so there is a number to beat. Read the four metric families and identify which dimension is pinned at its ceiling. Raise that dimension with the matching lever, changing one thing at a time. Re-measure against the baseline and confirm the gain, then ask whether the constraint has migrated to a different dimension. The loop ends when the workload meets its target or when the cost of the next lever exceeds the value of the next increment of speed.

### The InsightCrunch VM bottleneck table

The findable artifact that anchors this guide pairs each dimension with the metric that reveals it and the lever that fixes it. Keep this table beside the metrics blade and the diagnosis stops being guesswork.

| Dimension | Symptom the user reports | Metric that reveals it | What the metric shows when this is the limit | The lever that raises the ceiling | The cost the lever carries |
|-----------|--------------------------|------------------------|---------------------------------------------|-----------------------------------|----------------------------|
| Storage (disk) | Saves, queries, and batch jobs hang; the app feels laggy under write load | OS Disk and Data Disk IOPS Consumed Percentage; Disk Queue Depth; storage latency counters | Consumed percentage sits at or near 100 while CPU stays low; queue depth climbs | Move to a higher disk tier, raise provisioned IOPS and throughput on Premium SSD v2, stripe disks, or enable host caching | Higher storage bill; striping adds operational complexity; caching changes durability semantics for writes |
| Network | High latency between tiers; capped transfer rate; packet loss under load | VM bandwidth counters; packets-per-second; round-trip latency from a probe | Throughput plateaus below the machine's rated bandwidth; latency is dominated by per-packet host processing | Enable Accelerated Networking; pick a size with higher rated bandwidth; co-locate with a proximity placement group | A brief reboot or redeploy to enable the feature; proximity groups reduce allocation flexibility and capacity options |
| Processor (CPU) | Sustained high utilization; requests queue; throughput flatlines as load rises | Percentage CPU; run-queue length inside the guest; per-core saturation | CPU pinned near 100 while disk and network sit idle; work waits on compute | Resize to more vCPUs or a compute-optimized series; offload or parallelize the work | Higher hourly rate; some workloads do not scale linearly with cores |
| Memory | Paging and swap activity; sudden latency cliffs; the working set exceeds RAM | Guest memory metrics (Available Bytes, committed memory); page-fault and swap counters | Available memory near zero with active paging; latency spikes correlate with swap | Resize to a memory-optimized series; reduce the working set; add caching upstream | Memory-optimized series cost more per core; redesign effort if the working set is structural |

The table is deliberately built around symptoms first, because the engineer arrives with a complaint, not a metric. The complaint points at a row, the metric column confirms or refutes the row, and only then does the lever column come into play. Reading the table in that order keeps the discipline intact. Reading it lever-first invites the same blind spending the rule exists to prevent.

## The storage ceiling, the one that fools the most engineers

Storage is the dimension most likely to masquerade as a CPU problem, because a job waiting on a slow write looks, from a distance, like a job that is working hard. The processor sits at a polite thirty percent, the application logs grow slowly, and the natural conclusion is that the machine needs more muscle. The metric that breaks the illusion is the consumed-percentage counter on the data disk and on the operating-system disk. When that counter rides at or near one hundred while the processor idles, the storage subsystem is the wall, and no amount of compute will move it.

Azure governs managed disk performance on two axes that engineers routinely conflate. The first is IOPS, the count of read or write operations the disk completes per second, which dominates workloads built from many small random accesses such as a transactional database. The second is throughput, the megabytes per second the disk can stream, which dominates workloads built from large sequential transfers such as a log writer or a backup job. A disk can be starved on one axis while the other sits idle. A database doing thousands of tiny commits can hit its IOPS ceiling at a throughput far below the disk's megabytes-per-second rating, and a misread of the situation leads to provisioning the wrong axis. Diagnose which axis is pinned before changing anything.

### How do disk tiers cap IOPS and throughput?

Each managed disk tier sets a maximum for IOPS and for throughput that holds regardless of the machine it attaches to. Standard HDD, Standard SSD, Premium SSD, Premium SSD v2, and Ultra Disk climb in both ceilings and in price. A larger machine never lifts a per-disk ceiling; it only raises the aggregate the machine can sustain across all its disks combined, which is a separate cap.

The tier hierarchy is worth holding in concrete terms, with every figure flagged for verification against the current official disk documentation, since Azure revises these numbers as hardware generations turn over. Standard HDD sits at the bottom, suited to cold archives and infrequently touched data, with a ceiling commonly cited near 2,000 IOPS and a few hundred megabytes per second. Standard SSD raises the floor for light enterprise and development work, commonly cited near 6,000 IOPS. Premium SSD, the long-standing production default, prices by fixed size tiers labeled P1 through P80 and reaches roughly 20,000 IOPS and 900 megabytes per second at the top tiers. Premium SSD v2 is the more flexible successor: it lets you provision capacity, IOPS, and throughput as three independent dials, includes a baseline of 3,000 IOPS and 125 megabytes per second free of charge on any size, and scales to roughly 80,000 IOPS and 1,200 megabytes per second. Ultra Disk sits at the apex for the most demanding databases, with per-disk ceilings into the hundreds of thousands of IOPS and thousands of megabytes per second, and sub-millisecond latency. Treat each of those numbers as a starting point to confirm, not as a fixed constant, because the exact caps shift by region, by disk size, and by generation.

The independence of the dials on Premium SSD v2 is the single most useful change for tuning work, and it deserves emphasis. With the older Premium SSD model, raising IOPS meant buying a larger disk even when the extra capacity was useless, because performance was bundled into the size tier. A transaction-heavy database needing high IOPS at a small footprint had to overpay for gigabytes it would never fill. Premium SSD v2 breaks that bundle. A 64 gibibyte volume can carry 20,000 provisioned IOPS if the workload demands it, and the bill reflects the IOPS rather than phantom capacity. For most general-purpose production workloads this makes Premium SSD v2 both faster and cheaper than the equivalent Premium SSD, which is why it has become the sensible default for new deployments. The catch is that the baseline above 6 gibibytes raises maximum throughput by a fixed increment per provisioned IOPS, so the two dials interact and the provisioning needs a moment of arithmetic rather than a blind maximum.

### The aggregate cap the machine itself imposes

There is a second ceiling that catches engineers who have correctly chosen a fast disk. The machine size carries its own aggregate limits for uncached and cached storage operations, expressed as a combined IOPS and throughput budget across every disk attached to it. A small machine paired with an Ultra Disk capable of 100,000 IOPS may still see only a fraction of that, because the machine's own storage budget is the narrower of the two ceilings. Performance is gated by the minimum of the disk's cap and the machine's cap, never the maximum. The fix for this case is not a bigger disk, which would be wasted, but a larger or more storage-capable machine, or a different series whose storage budget matches the disk. Confirming which of the two caps binds requires comparing the disk's provisioned ceiling against the machine size's documented storage limits, both flagged for verification against current figures.

### Host caching, the free lever people forget

Azure offers a read and read-write caching layer on the host for data disks and the operating-system disk, and it is frequently left at a default that does not match the workload. ReadOnly caching serves repeated reads from a cache local to the host, which sharply helps read-heavy patterns such as a database serving the same hot pages repeatedly, at no extra charge. ReadWrite caching also buffers writes, which helps some patterns but changes the durability picture, because a write acknowledged to the application may still be in cache rather than committed to the underlying disk. For a database that manages its own write ordering and recovery, ReadWrite host caching can corrupt that contract and is usually set to None on the data disk holding the database files, while ReadOnly is reserved for read-mostly volumes. The operating-system disk commonly uses ReadWrite. Matching the caching mode to the access pattern is a lever that costs nothing and is too often skipped.

### Striping disks for a ceiling no single disk reaches

When a workload needs more IOPS or throughput than any one disk tier delivers within the machine's budget, the answer is to combine several disks into a single logical volume and spread the load across them. On Linux this is done with a logical volume manager or a software array; on Windows it is a Storage Spaces pool. Eight Premium SSD v2 disks striped together present a combined ceiling that is the sum of their provisioned performance, up to the machine's aggregate cap. The lever is effective for high-throughput analytic and database workloads, and it is also the one that adds the most operational weight. A striped volume has more moving parts to provision, to monitor, and to resize, and a failure model that the operator must understand. Reach for striping when a single disk genuinely cannot reach the target and the machine has budget to spare, not as a first move.

### Reading the storage signal in practice

The confirming evidence for a storage bottleneck lives in a small set of counters. The OS Disk IOPS Consumed Percentage and Data Disk IOPS Consumed Percentage metrics, exposed in the platform metrics for the machine, show how close the disk runs to its provisioned ceiling; sustained values near one hundred are the signature of a saturated disk. Disk queue depth, visible inside the guest, shows requests stacking up faster than the disk drains them. Storage latency counters show the time each operation takes to complete, and a latency that climbs under load while throughput plateaus confirms the disk, not the application, is the wait. The diagnostic discipline is to watch these alongside the processor counter: high disk consumption with low processor use is storage; high processor use with low disk consumption is compute. The pairing is what separates the two most-confused cases.

## The network ceiling and the single feature that moves it most

A network-bound workload presents differently from a storage-bound one. The complaint is usually about latency between tiers, a web layer waiting on a database layer, a cache reply that arrives later than it should, or a transfer rate that refuses to climb above some plateau well under the machine's rated bandwidth. The processor and the disk both sit comfortably while the work stalls, and the stall correlates with traffic rather than with computation. When the symptoms point at the wire, the first lever to reach for is almost always Accelerated Networking, because it is free, broadly available, and frequently the largest single improvement a network-bound machine will ever see.

### What does Accelerated Networking actually do?

Accelerated Networking enables single root I/O virtualization on supported machine sizes, giving the guest a direct hardware path to the physical network adapter. Traffic bypasses the host virtual switch instead of being processed in software on the host CPU, which cuts latency and jitter, lowers processor overhead, and raises the packets-per-second the machine can handle. The feature is free and generally available worldwide.

To see why the effect is large, picture the default path. Without the feature, every packet entering or leaving the guest traverses a virtual switch running in software on the host, where network security group rules, access control lists, isolation policy, and other virtualized services are applied. That software processing adds time to every packet and consumes host processor cycles, and under heavy packet rates it becomes the limit. Accelerated Networking moves that policy enforcement onto programmable hardware, an FPGA-based smart adapter, and hands the guest a virtual function that talks to the physical card almost directly. The packets no longer wait in a software queue on the host. Real measurements illustrate the scale of the change: independent tests on a pair of general-purpose machines have shown round-trip latency falling from roughly 300 microseconds to the range of 55 to 60 microseconds once the feature is enabled, a reduction of more than fourfold on the wire. The exact figures depend on machine size, region, the traffic path, and the workload, and should be treated as illustrative rather than guaranteed, but the direction and the magnitude are consistent.

The benefit concentrates in workloads that are sensitive to latency or that push high packet rates: chatty multi-tier applications, in-memory caches, streaming pipelines, network appliances, and anything that moves data at high speed with many small packets. A workload that moves a few large files an hour will barely notice. A service handling tens of thousands of small requests per second will often see the single biggest win of any tuning lever from this one toggle.

### How do I know whether my machine supports it and uses it?

Support depends on the size and series. Most modern general-purpose and compute-optimized series with two or more virtual processors support the feature, and many current marketplace images ship with the required drivers already installed. The historical guidance named series such as the D and Ds families, the E and Es families, the F and Fs families, and the memory-heavy M family, with a minimum core count; the supported list has broadened over successive generations, so confirm against the current size documentation for the exact series and minimum size rather than relying on an older list. The newer Microsoft network adapter, sometimes referenced under its preview name, is the next step in the same direction and is worth checking for on recent hardware.

Two failure modes around the feature trip people up. The first is that it is enabled on the network interface but not actually used by the traffic, which happens when the guest operating system lacks the driver for the virtual function or fails to bind the synthetic interface to it. The confirming check on Linux is to inspect the interface statistics and verify that traffic is flowing over the virtual function rather than the synthetic path; the command below reads the per-interface counters so you can see which path carries the load. The second failure mode is a machine that will not start after the feature is enabled, which almost always means the chosen size does not support it, and the resolution is to pick a size that does or to disable the feature on that size.

### Enabling the feature without guessing

On an existing machine the interface must usually be deallocated before the property is changed, then started again, which is a brief interruption rather than a rebuild. The commands below enable the feature on a network interface and confirm the property afterward. Reproduce the exact flag names against the current command reference, since the tooling evolves.

```bash
# Stop and deallocate the VM so the NIC property can change
az vm deallocate --resource-group rg-perf --name vm-app01

# Enable Accelerated Networking on the existing NIC
az network nic update \
  --resource-group rg-perf \
  --name vm-app01-nic \
  --accelerated-networking true

# Start the VM again
az vm start --resource-group rg-perf --name vm-app01

# Confirm the property is now set on the NIC
az network nic show \
  --resource-group rg-perf \
  --name vm-app01-nic \
  --query "enableAcceleratedNetworking"
```

Inside a Linux guest, confirm that the virtual function is carrying traffic rather than sitting idle while the synthetic path does the work:

```bash
# List interfaces; with the feature working you will see a VF interface
ip link show

# Read per-interface statistics to confirm the VF carries the load
ethtool -S eth0 | grep -i 'vf\|rx_packets\|tx_packets'

# Measure round-trip latency to a peer to compare before and after
sudo apt-get install -y sockperf
sockperf ping-pong -i 10.0.1.5 -t 30
```

The measurement step is the part most people skip and the part that matters most. Run the latency probe before enabling the feature, record the number, enable it, run the probe again, and keep both figures. A claim that the network got faster is worth nothing without the two numbers that prove it. The before-and-after pair also tells you whether the network was the bottleneck at all; if the latency was already low and the workload was still slow, the wire was never the constraint and the attention belongs elsewhere.

### The rated bandwidth ceiling that sizing sets

Accelerated Networking lowers latency and raises packet rate, but it does not lift the machine's rated bandwidth, which is a function of the size. Each size carries an expected network bandwidth, and a workload that genuinely needs more aggregate throughput than the size provides needs a larger or more network-capable size, not just the feature. The two levers address different ceilings: the feature attacks the per-packet host overhead and the packet rate, while the size attacks the raw bandwidth allotment. A transfer plateauing exactly at the size's rated bandwidth is a sizing problem; a transfer plateauing below it with high host processor use on the network path is an Accelerated Networking problem. Reading which of the two is binding, again, comes down to comparing the measured plateau against the documented rating, with the rating flagged for verification.

## Matching the size and series to the workload, not to a hunch

When measurement points at the processor or the memory as the binding ceiling, the lever genuinely is the machine itself, but the choice is rarely as simple as picking a bigger number. Azure organizes machines into series tuned for different ratios of processor to memory to storage, and choosing the right series matters more than choosing the right size within a series. A workload that is starved for memory gains little from a general-purpose series with more cores; it needs a memory-optimized series that carries more gigabytes per core. A workload pinned on compute gains little from a memory-heavy series; it needs a compute-optimized series that packs more processor per gigabyte. Picking the family first and the size second is the order that avoids paying for the wrong resource.

### How does the VM series shape performance?

Each series fixes a ratio of processor to memory and a storage and network budget. General-purpose series balance the three for typical web and application tiers. Compute-optimized series raise the processor-to-memory ratio for batch and front-end work. Memory-optimized series raise memory per core for databases and in-memory caches. Storage and specialized series tune for high disk throughput or for accelerators. The right series matches the workload's scarcest resource.

The general-purpose families, the D and Dsv-generation series and their relatives, suit the broad middle: web servers, application tiers, small to medium databases, and development environments where no single resource dominates. They are the right default when measurement has not yet revealed a lopsided demand. The compute-optimized families, the F and Fsv-generation series, carry a higher processor-to-memory ratio and a faster per-core clock profile, which fits batch processing, application servers under heavy request load, gaming back ends, and analytics front ends where the work is processor-bound and the memory footprint is modest. Spending on a compute-optimized series for a memory-bound job wastes the very thing it sells.

The memory-optimized families, the E and Esv-generation series and the larger M family, carry more gigabytes per core and suit relational databases, in-memory caches, and analytics that hold a large working set. The M family in particular targets the largest in-memory databases, where the entire dataset must sit in RAM to perform, and where paging to disk would collapse the latency profile. A database that spends its time paging because the working set exceeds available memory will transform on a memory-optimized series in a way that no amount of extra processor would achieve. Beyond these, storage-optimized series carry high local disk throughput for big-data and warehouse work, and accelerated series carry processors or other accelerators for specialized numerical and rendering tasks.

### Resizing the right way

Once the series is right, resizing within it raises the processor, memory, network, and aggregate storage ceilings together in proportion. The mechanics are straightforward, but two cautions apply. First, resizing across some size boundaries requires the machine to stop and deallocate, which interrupts the workload, while resizing within a compatible family can sometimes happen in place; plan the change against the maintenance window the workload allows. Second, resizing into a different series can move the machine to different underlying hardware, which can change network and storage behavior in ways that need re-measurement rather than assumption. The command below resizes a machine and lists the sizes available in its current region and cluster, which is the set of valid targets.

```bash
# List the sizes the VM can resize to in its current placement
az vm list-vm-resize-options \
  --resource-group rg-perf \
  --name vm-app01 \
  --output table

# Resize the VM (a stop/deallocate may occur depending on the target)
az vm resize \
  --resource-group rg-perf \
  --name vm-app01 \
  --size Standard_E8s_v5
```

### The discipline of changing one dimension at a time

The most common way a resize misleads is by changing several ceilings at once and then crediting the wrong one for the gain. Moving from a four-core general-purpose machine to an eight-core memory-optimized machine raises cores, raises memory per core, and changes the storage and network budgets, all together. If the workload speeds up, the operator cannot say which change mattered, and the next tuning decision rests on a guess. The cleaner method, when the budget and the maintenance window allow, is to change the series for the memory ratio first, measure, then change the size within that series, measure again. The slower path produces knowledge that compounds across the fleet; the faster path produces a result that does not transfer to the next machine.

## Co-locating machines with a proximity placement group

Some latency is not about the machine at all but about the physical distance between machines that talk to each other constantly. Two machines in the same region can still sit in different datacenters within that region, and the speed of light across that distance, plus the switching in between, sets a floor on the round-trip time between them. For a tier that is sensitive to inter-machine latency, an application server hammering a database, a set of nodes in a tightly coupled cluster, that floor can dominate the latency budget even after Accelerated Networking has done its work.

### How does a proximity placement group reduce latency?

A proximity placement group is a placement constraint that asks Azure to allocate the machines in the group physically close to one another, in the same datacenter and ideally the same network segment. Co-locating the machines cuts the network distance their traffic crosses, which lowers the round-trip latency between them. The benefit shows up only for latency-sensitive inter-machine traffic, not for a single isolated machine.

The lever stacks with Accelerated Networking rather than replacing it. The feature removes the host-processing overhead on each packet; the placement group removes the physical distance the packet travels. A latency-sensitive cluster benefits from both, and the combination is the standard pattern for tightly coupled tiers such as the application and database layers of a packaged enterprise workload, where vendors explicitly recommend pairing the two. The measured effect is real but modest in absolute terms, often a further reduction of tens of microseconds on top of what Accelerated Networking already delivered, which matters enormously for a chatty synchronous protocol making thousands of round trips per request and not at all for a workload that makes one large call.

### The cost the placement group carries

The constraint that delivers the latency benefit is also its cost. Asking Azure to place every machine in the group in the same physical location reduces the platform's freedom to allocate, which can make capacity harder to obtain, especially for larger sizes or specialized series, and especially when the group spans several sizes that must all fit the same cluster. A placement group that mixes many sizes, or that is created after some members already exist elsewhere, can fail to allocate or can pin the group to a location that limits later growth. The practical guidance is to create the group, then deploy the most constrained size first so the placement settles around it, and to keep the group as narrow as the latency requirement demands rather than sweeping every machine into it. Co-location is a precision tool for the few tiers that need it, not a default to apply broadly.

## Finding a processor or memory bottleneck and acting on it

The two dimensions that genuinely call for a bigger machine are processor and memory, and they are the two that a careful diagnosis reaches last rather than first, precisely because they are the ones the size button addresses. When the storage and network ceilings have been ruled out by their metrics, the remaining candidates are compute and RAM, and each has a clean signature.

### How do I find a CPU bottleneck?

A processor bottleneck shows the Percentage CPU metric pinned near one hundred for sustained periods while disk consumption and network throughput sit well below their ceilings. Inside the guest, the run-queue length climbs, meaning work is waiting for a core to become free. Throughput stops rising as load increases. The fix is more virtual processors, a faster series, or parallelizing the work.

The subtlety with processor diagnosis is distinguishing a genuinely compute-bound workload from one that merely looks busy because it is spinning while it waits on something else. A thread blocked on a slow disk write can register as busy in some accounting, and a single-threaded application can pin one core to one hundred percent while seven other cores idle, which the machine-level average hides. The honest diagnosis looks at per-core utilization, not just the aggregate, and at what the busy threads are actually doing. A workload pinning one core while the machine-level average reads twelve percent on an eight-core machine does not need a bigger machine; it needs to use the cores it has, through parallelism or a redesign, because adding cores it cannot use changes nothing. A workload pinning every core is the real compute bottleneck, and there the lever is more processors or a faster compute-optimized series.

### How do I find a memory bottleneck?

A memory bottleneck appears as available memory falling toward zero with active paging or swapping, and latency that spikes in correlation with that swap activity. The working set has outgrown the RAM, so the operating system pushes pages to disk and pays a heavy latency penalty to fetch them back. The fix is a memory-optimized series, a smaller working set, or caching that reduces what must be held.

Memory pressure is the most punishing of the four bottlenecks when it crosses its threshold, because the failure is not gradual. A machine with enough memory runs at memory speed; a machine a few percent short of enough memory runs at disk speed for the overflow, and the latency cliff is sharp rather than sloped. This is why a database whose working set creeps just past available RAM can degrade catastrophically overnight as data grows, with no change in code or query volume. The metric to watch is the guest's available-memory counter together with page-fault and swap counters; a steady decline in available memory as the dataset grows is the early warning that the cliff is approaching. Acting before the cliff, by moving to a memory-optimized series or by trimming the working set, is far cheaper than reacting after the latency has already collapsed.

Reading processor and memory through the guest gives more detail than the platform metrics alone, because the platform sees the machine from the outside while the guest sees what the operating system is actually doing. Enabling guest-level diagnostics, which forwards in-guest performance counters to the platform, closes that gap and is worth doing on any machine being tuned seriously. The platform Percentage CPU metric is a true reading of host-charged processor time and is reliable for the compute ceiling, but the platform cannot see guest memory usage without the guest diagnostics extension, because memory accounting lives inside the operating system. Without that extension a memory bottleneck is invisible in the portal metrics, which is one reason memory problems are so often misdiagnosed as something else.

## Measuring before and after, the step that makes tuning honest

Every lever in this guide is paired with a measurement, and the measurement is not optional decoration. The find-the-bottleneck-first rule rests on a baseline, and a baseline is a number captured under real load before any change. Without it, the question of whether a change helped has no answer, only an impression, and impressions are exactly what blind resizing trades on. The measurement discipline has three parts: capture a baseline, read the right metric for the dimension under test, and compare the after against the before for that same metric under the same load.

### Reading the platform metrics

The platform exposes a metrics blade for every machine, and the counters that matter for tuning are a small set. Percentage CPU reads the processor ceiling. OS Disk and Data Disk IOPS Consumed Percentage and the corresponding bandwidth-consumed counters read the storage ceiling against the provisioned cap. The network in and out total counters and the packet counters read the network dimension. These can be pulled through the command line so the baseline is a stored number rather than a glance at a chart, which is what makes a real before-and-after possible.

```bash
# Pull average CPU over the last hour as a baseline number
az monitor metrics list \
  --resource "/subscriptions/<sub-id>/resourceGroups/rg-perf/providers/Microsoft.Compute/virtualMachines/vm-app01" \
  --metric "Percentage CPU" \
  --interval PT1M \
  --aggregation Average \
  --output table

# Pull data-disk IOPS consumed percentage to test the storage ceiling
az monitor metrics list \
  --resource "/subscriptions/<sub-id>/resourceGroups/rg-perf/providers/Microsoft.Compute/virtualMachines/vm-app01" \
  --metric "Data Disk IOPS Consumed Percentage" \
  --interval PT1M \
  --aggregation Average Maximum \
  --output table
```

### Reading the storage signal inside the guest

Platform metrics show whether a disk is near its provisioned ceiling, but the guest shows the latency and the queue depth that the workload actually feels. On Linux the standard tool reports utilization, queue size, and per-operation latency per device, and a controlled load test against the disk produces a reproducible throughput and IOPS figure to compare before and after a tier change.

```bash
# Watch per-device utilization, queue depth, and latency live
iostat -dx 2

# Generate a reproducible random-read IOPS baseline with fio
fio --name=randread --filename=/datadisk/testfile --size=4G \
    --rw=randread --bs=4k --iodepth=32 --numjobs=4 \
    --runtime=60 --time_based --group_reporting

# Generate a reproducible sequential-throughput baseline
fio --name=seqread --filename=/datadisk/testfile --size=4G \
    --rw=read --bs=1M --iodepth=16 --numjobs=2 \
    --runtime=60 --time_based --group_reporting
```

The two load tests matter because they exercise the two storage axes separately. The small-block random test stresses IOPS, the metric that gates a transactional database; the large-block sequential test stresses throughput, the metric that gates a log writer or a backup. Running both before a change tells you which axis was pinned, and running both after tells you whether the lever raised the axis that was actually binding. A tier change that lifts throughput while the workload was IOPS-bound produces a measurement that proves the change missed, which is far more useful than a vague sense that nothing improved.

### Keeping the baseline honest

A baseline is only as good as the load it was captured under. A measurement taken at three in the morning when the workload is idle tells you nothing about the peak that the users complain about. Capture the baseline during representative load, or generate representative load deliberately with a test harness, and capture the after-figure under the same conditions. Comparing a busy-hour baseline against a quiet-hour after-reading is the classic way to convince yourself a change worked when it did nothing. The discipline is dull and it is the entire difference between tuning and guessing.

## The four metric families and how to wire up the signal

Reading the binding ceiling well depends on having the right counters collected and on knowing what each one means when it moves. The four dimensions map to four families of metric, and a machine being tuned seriously should expose all four so the diagnosis never stalls for want of data.

The storage family centers on the consumed-percentage counters for the operating-system disk and each data disk, which compare current operations against the provisioned ceiling, and on the parallel bandwidth-consumed counters that do the same for throughput. These platform metrics answer the question of how close the volume runs to its cap, but they do not by themselves show the latency the workload feels, which is why the guest-level counters for queue depth and per-operation service time complete the picture. A disk at ninety-five percent consumed with a deep queue and rising service time is saturated; a disk at thirty percent consumed is not the constraint no matter how slow the application feels, and attention belongs elsewhere.

The network family centers on the inbound and outbound byte counters and the packet counters, read against the size's rated bandwidth. A throughput that plateaus exactly at the rated figure is a sizing limit; a plateau well below it, paired with high host processor time spent on the network path, points at the absence of Accelerated Networking. Latency itself is not a standing platform metric in the same way, which is why a probe such as a ping-pong latency tester is the right instrument when the complaint is about round-trip time rather than volume.

The processor family is the simplest to read, because the platform's percentage-CPU counter is a faithful reading of host-charged compute time. Its trap is the aggregate average, which hides a single pinned core behind seven idle ones, so the guest view of per-core utilization and the run-queue length is what turns a vague reading into a diagnosis. The memory family is the one the platform cannot see unaided, since memory accounting lives inside the operating system; the guest diagnostics extension forwards available-memory, committed-memory, and paging counters that are otherwise invisible, and without it a memory bottleneck simply does not appear in the portal.

### How do I set up alerts so a bottleneck announces itself?

Wire metric alerts to the binding counters so a saturated dimension pages you rather than waiting for a user complaint. A sustained data-disk consumed percentage above a threshold, a percentage-CPU average above a level for a window, or available memory below a floor each makes a good alert rule. The alert turns a reactive diagnosis into a proactive one.

The configuration below creates a metric alert on sustained high data-disk IOPS consumption, which is the early warning that a storage ceiling is being approached before the latency collapses. Reproduce the exact parameter names against the current command reference, since the alerting commands evolve across tool versions.

```bash
# Create an action group to receive the alert
az monitor action-group create \
  --resource-group rg-perf \
  --name ag-perf-oncall \
  --short-name perfcall

# Alert when data-disk IOPS consumed percentage stays high
az monitor metrics alert create \
  --resource-group rg-perf \
  --name "vm-app01-disk-saturation" \
  --scopes "/subscriptions/<sub-id>/resourceGroups/rg-perf/providers/Microsoft.Compute/virtualMachines/vm-app01" \
  --condition "avg Data Disk IOPS Consumed Percentage > 90" \
  --window-size 15m \
  --evaluation-frequency 5m \
  --action ag-perf-oncall \
  --description "Data disk approaching its provisioned IOPS ceiling"
```

An alert tuned to the dimension that actually binds the workload is worth more than a dozen generic alerts on processor alone, because the generic alert fires on the wrong dimension and trains the on-call engineer to reach for the resize button out of habit. A storage-saturation alert on a storage-bound workload, by contrast, points straight at the lever that will help.

## A worked diagnosis from complaint to confirmed fix

The method reads abstractly until it is walked once end to end. Take a concrete and common complaint: a reporting database on a Standard_D8s_v5 machine has become slow during the nightly batch window, queries that finished in minutes now run for the better part of an hour, and the team's first instinct is to resize to a Standard_D16s_v5 to throw cores at the problem. The find-the-bottleneck-first rule says to measure before spending, so the diagnosis begins at the metrics rather than the size dropdown.

The first reading is the processor counter across the batch window. It averages twenty-two percent, with no sustained pinning and a run queue that rarely exceeds the core count. That single reading rules out a compute bottleneck and, with it, the proposed resize: doubling cores that sit four-fifths idle cannot help. The instinct was wrong, and ten minutes of measurement has already saved the cost of the larger machine.

The second reading is the storage family. The data-disk IOPS consumed percentage rides at ninety-eight to one hundred for the entire batch window, the guest queue depth climbs into the dozens, and the per-operation service time has tripled compared with the daytime baseline. This is the signature of a saturated disk. The batch job does many small random reads and writes against the reporting tables, which is an IOPS-bound pattern, and the disk's provisioned IOPS ceiling is the wall the job hits every night. The processor idles because it spends the window waiting on storage it cannot hurry.

The confirming step is a controlled load test that reproduces the pattern in isolation. A random-read test at a small block size against the data disk returns an IOPS figure that matches the disk's provisioned ceiling almost exactly, which proves the disk is delivering everything it was provisioned to deliver and the ceiling itself is the limit. A sequential-throughput test, by contrast, returns a figure far below the throughput cap, confirming that throughput was never the binding axis and that provisioning more megabytes per second would waste money on the wrong dial.

With the binding dimension and the binding axis both identified, the lever is precise: raise the provisioned IOPS on the Premium SSD v2 data disk, or move it to a tier whose IOPS ceiling clears the batch demand, leaving the throughput dial and the machine size untouched. After the change, the same load test returns an IOPS figure at the new, higher ceiling, the batch-window consumed percentage drops from one hundred to the sixties, the queue depth falls, and the query times return to minutes. The before-and-after IOPS numbers prove the fix addressed the axis that bound the work. The machine size never changed, the cores were never the problem, and the bill rose only by the cost of the additional provisioned IOPS rather than by the cost of a machine twice the size.

The walk illustrates every move of the rule in sequence: a baseline under real load, a reading of all four families that ruled out the assumed cause, a confirming load test that identified the binding axis, a targeted lever on that axis alone, and a re-measurement that proved the gain. It also illustrates the saving the rule produces, because the obvious resize would have doubled the compute bill and changed nothing, while the measured fix cost a fraction of that and solved the problem outright.

## Tuning configuration as code and autoscale for scale sets

A tuning change made by hand in the portal is a change that drifts, that no one can reproduce, and that disappears when the machine is rebuilt. The durable form of every lever in this guide is a declarative definition, so the disk tier, the provisioned IOPS, the Accelerated Networking flag, the size, and the caching mode all live in source control and deploy identically every time. The Bicep fragment below pins a data disk to Premium SSD v2 with explicit provisioned IOPS and throughput, attaches it with the caching mode chosen for the workload, and enables Accelerated Networking on the interface, capturing the tuning decisions as code rather than as portal clicks.

```bicep
resource dataDisk 'Microsoft.Compute/disks@2023-04-02' = {
  name: 'vm-app01-data01'
  location: location
  sku: {
    name: 'PremiumV2_LRS'
  }
  properties: {
    creationData: { createOption: 'Empty' }
    diskSizeGB: 256
    diskIOPSReadWrite: 20000
    diskMBpsReadWrite: 600
  }
}

resource nic 'Microsoft.Network/networkInterfaces@2023-09-01' = {
  name: 'vm-app01-nic'
  location: location
  properties: {
    enableAcceleratedNetworking: true
    ipConfigurations: [
      {
        name: 'ipconfig1'
        properties: {
          subnet: { id: subnetId }
          privateIPAllocationMethod: 'Dynamic'
        }
      }
    ]
  }
}
```

Capturing the tuning as code does more than prevent drift. It makes the tuning reviewable, so a change to the provisioned IOPS appears in a pull request where its cost and rationale can be weighed before it ships, and it makes the tuning transferable, so a second machine serving the same workload inherits the same proven configuration rather than being tuned from scratch. The declarative form is also where the measurement discipline and the change discipline meet, because the commit message records why the IOPS were raised and the metric that justified it, turning a one-time fix into institutional knowledge.

### How do I tune a scale set rather than a single VM?

A virtual machine scale set applies the same per-machine levers, the disk tier, Accelerated Networking, the size, and the caching mode, to every instance in the set, and adds autoscale rules that change the instance count in response to a metric or a schedule. Tune the individual instance first so each one is efficient, then set autoscale so the set grows only when the per-instance ceiling is genuinely reached.

The order matters because autoscale that fires on the wrong metric scales the wrong thing. A scale set whose instances are storage-bound will not improve by adding instances if every new instance hits the same disk ceiling, and autoscaling on processor utilization for a storage-bound workload adds machines that sit at twenty percent processor while the disks saturate, multiplying the bill without multiplying the throughput. The discipline carries over from the single machine: identify the per-instance binding dimension first, tune it, and only then let autoscale add instances against the metric that actually reflects load. The autoscale rule below scales out on sustained per-instance processor pressure, which is the correct trigger only once the instance has been confirmed compute-bound rather than storage-bound or network-bound.

```bash
# Define an autoscale profile on a scale set
az monitor autoscale create \
  --resource-group rg-perf \
  --resource vmss-web01 \
  --resource-type Microsoft.Compute/virtualMachineScaleSets \
  --name autoscale-web01 \
  --min-count 2 --max-count 10 --count 2

# Scale out when average CPU stays above 70 percent
az monitor autoscale rule create \
  --resource-group rg-perf \
  --autoscale-name autoscale-web01 \
  --condition "Percentage CPU > 70 avg 10m" \
  --scale out 2

# Scale in when average CPU falls below 30 percent
az monitor autoscale rule create \
  --resource-group rg-perf \
  --autoscale-name autoscale-web01 \
  --condition "Percentage CPU < 30 avg 10m" \
  --scale in 1
```

The asymmetry between the scale-out and scale-in thresholds is deliberate and worth keeping. Scaling out aggressively and scaling in gently prevents the thrash that comes from a metric hovering near a single threshold, where the set would otherwise add and remove instances repeatedly as the metric crosses back and forth. A wide gap between the two thresholds gives the set hysteresis, so it commits to a count and holds it until the load has genuinely changed rather than oscillating on noise.

## Temporary disk, burst credits, and the smaller levers

Beyond the four headline ceilings sit a handful of smaller levers that are easy to forget and occasionally decisive. The first is the temporary disk that many sizes include, a local volume physically attached to the host that offers fast, low-latency storage at the cost of being ephemeral: its contents do not survive a deallocation or a host migration. For workloads that need scratch space, a buffer pool extension, or a temporary directory under heavy churn, routing that activity to the temporary disk relieves the managed data disk of operations it never needed to carry, which can clear a storage bottleneck without changing any disk tier at all. The caution is the impermanence; nothing that must persist belongs on the temporary disk, and the size of the temporary disk varies by machine size and must be confirmed against the current size documentation.

The second smaller lever is disk bursting, which lets eligible disk sizes temporarily exceed their baseline IOPS and throughput by drawing on accumulated credits. Credit-based bursting accrues credits during idle periods and spends them during spikes, and it is available on smaller Premium SSD disks and smaller Standard SSD disks within documented size limits, which means a workload with brief, periodic spikes such as a boot sequence or a short batch job can ride through the spike on burst credits without paying for a permanently higher tier. The trap is treating burst as steady-state capacity: a workload that saturates the disk continuously exhausts its credits and falls back to the baseline, so bursting solves a spiky pattern and does nothing for a sustained one. Reading whether the demand is spiky or sustained is, once again, the diagnosis that picks the right lever.

The third is the choice between paying for provisioned performance and accepting throttling. A disk pushed past its ceiling does not fail; it throttles, queuing operations until they fit within the cap, which shows up as rising latency and queue depth rather than an error. An engineer who does not recognize throttling as the symptom will blame the application or the network for the latency, when the cause is a disk politely enforcing the ceiling it was provisioned for. Recognizing throttling for what it is, a self-imposed limit rather than a fault, is the difference between raising the right ceiling and chasing a phantom problem in code that was never slow.

Together these smaller levers reinforce the same theme the headline levers teach. Each one raises or relieves a specific ceiling, each carries a specific cost or caveat, and each is chosen by reading the workload rather than by reflex. The temporary disk trades durability for speed, bursting trades steady cost for spike coverage, and recognizing throttling trades a misdirected investigation for a precise one. None of them replaces the four-dimension diagnosis; they extend it, giving the careful operator more ways to raise exactly the ceiling that binds without overspending on the three that do not.

## Six patterns engineers actually report, and the lever for each

Tuning work tends to recur as a handful of recognizable patterns. Naming them turns a fresh diagnosis into a match against cases already understood, which shortens the path from symptom to lever.

The first and most expensive pattern is the resize that did nothing because the storage tier was the real ceiling. The team moves the database machine up two sizes, the bill climbs, and the query latency does not budge. The metric that was ignored is the data-disk consumed percentage, which sat at one hundred before the resize and sat at one hundred after, because the disk tier capped the IOPS the whole time and the extra cores had nothing to do. The lever was never the machine; it was a higher disk tier or more provisioned IOPS on Premium SSD v2. This pattern is the reason the find-the-bottleneck-first rule exists, and recognizing it is worth more than any single configuration change.

The second pattern is the network-bound workload that transforms the moment Accelerated Networking is enabled. A multi-tier application makes thousands of small calls between its web and data layers, the latency between them dominates each request, and the machine was provisioned without the feature. Enabling it cuts the per-packet host overhead, latency falls by a multiple, and the request time drops with it. The before-and-after latency probe is what proves the diagnosis, and the fix costs nothing beyond a brief reboot.

The third pattern is the memory-bound application that needs a memory-optimized series rather than more cores. The working set has grown past available RAM, the machine pages to disk, and the latency develops a cliff that correlates with swap activity. Adding cores does nothing because the cores are not the scarce resource. Moving to an E-series or M-series machine that carries more memory per core lets the working set sit in RAM, and the cliff disappears. The guest memory counter, visible only with guest diagnostics enabled, is what reveals this case.

The fourth pattern is the latency-sensitive cluster that benefits from proximity placement after the easier levers are exhausted. The tiers already run Accelerated Networking, the disks are fast, and yet a synchronous protocol making many round trips per request still pays a latency tax from the physical distance between machines in the same region. A proximity placement group co-locates them and shaves the remaining tens of microseconds per round trip, which compounds across thousands of round trips. This is the pattern where co-location earns its operational cost.

The fifth pattern is the genuine processor bottleneck found honestly in the metrics. Every core sits near one hundred percent, disk and network idle, and throughput flatlines as load rises. Here the size button is finally the right answer, or a compute-optimized series, or a redesign that parallelizes the work across more cores. The discipline that makes this pattern trustworthy is that it was reached by ruling out the other three dimensions first, so the spend on more compute is evidence-backed rather than hopeful.

The sixth pattern is the overlooked operating-system disk that throttles the whole machine. The data disk is fast and correctly sized, but the operating-system disk was left on a small default tier, and it quietly caps operations that route through it, including paging, logging, and temporary files. The machine feels sluggish in a way that the data-disk metrics do not explain, because the constraint lives on the other disk. Reading the OS Disk IOPS Consumed Percentage alongside the data-disk counter exposes it, and raising the operating-system disk tier or moving the offending activity to a faster volume clears it. This case is common precisely because attention naturally goes to the data disk and the operating-system disk gets forgotten.

## The misdiagnoses that cost the most, and the counter that corrects each

Every dimension has a way of impersonating another, and the recurring cost of tuning work is the change made against the impersonation rather than the truth. Cataloguing the common confusions, each with the single counter that settles it, turns a fresh puzzle into a quick lookup.

The most expensive confusion treats a saturated volume as a tired processor. The job spends its time waiting on small random reads and writes, the application logs crawl, and the natural reading is that the machine needs more compute. The counter that corrects it is the pairing of percentage-CPU against the data-disk consumed percentage: low compute use beside a volume pinned near its provisioned ceiling is storage every time, and the resize that the confusion suggests would change nothing. This is the confusion the find-the-bottleneck-first rule was written to defeat, and it remains the one that drains the most budget across a fleet.

A subtler confusion treats a network path that lacks Accelerated Networking as a bandwidth shortage. The transfer rate plateaus, the obvious conclusion is that the size does not carry enough bandwidth, and the proposed fix is a larger size. The counter that corrects it is the comparison of the measured plateau against the size's rated bandwidth alongside the host processor time spent on the network path: a plateau well below the rating with high host overhead on packets is the absence of the feature, not a bandwidth shortfall, and the free toggle solves it where the larger size would have overpaid for headroom the workload could not use without the feature anyway.

A third confusion mistakes burst-credit exhaustion for a performance regression. A workload that ran briskly for weeks suddenly slows, nothing in the code changed, and the team hunts for a regression that does not exist. The counter that corrects it is the disk's consumed percentage read over a longer window: a workload that has grown from spiky to sustained exhausts its accumulated credits and settles back to the baseline ceiling, which feels like a regression but is the disk behaving exactly as provisioned. The fix is a permanently higher provisioned floor rather than a code investigation, and recognizing the pattern saves days of chasing a phantom.

A fourth confusion reads a single pinned core as a busy machine. The aggregate processor average sits low, yet the workload is plainly compute-limited, and the machine-level metric seems to contradict the symptom. The counter that corrects it is per-core utilization inside the guest: one core at one hundred percent while the others idle is a single-threaded limit that a bigger machine cannot relieve, because the extra cores will idle exactly as the current spare cores do. The lever is parallelism in the workload or a series with a faster per-core profile, not more cores, and the per-core view is what makes that distinction visible where the average conceals it.

A fifth confusion blames the data volume while the operating-system volume quietly throttles. The data volume's counters look healthy, yet the machine feels sluggish, and the diagnosis stalls because the obvious counter shows nothing wrong. The counter that corrects it is the operating-system disk consumed percentage read alongside the data-disk counter: paging, logging, and temporary activity route through the operating-system volume, and a small default tier there caps the whole machine in a way the data-volume metrics never reveal. Raising the operating-system disk tier or relocating the busy activity clears it, and reading both volume counters as a routine pair is what prevents the stall.

The thread through all five is identical. The symptom points at a plausible cause, the plausible cause suggests an expensive lever, and a single well-chosen counter either confirms the cause or exposes the impersonation for what it is. The counter costs a minute to read and the wrong lever costs a month of budget, which is the entire economic case for measuring first. An operator who keeps this catalogue beside the metrics blade stops being fooled by the impersonations, because each one has a tell, and the tell is always a counter that the careful reading checks before the spending begins.

## The trade-offs every lever carries

No lever is free of cost, and pretending otherwise leads to over-correction. A higher disk tier raises the storage bill, sometimes substantially for Ultra Disk, and the right move is to provision to the measured need plus a margin, not to the maximum. Premium SSD v2's independent dials make this easier, because the IOPS and throughput can be raised exactly as far as the measurement demands without buying capacity, and lowered again if the load proves smaller than feared. Striping disks adds the most operational weight of any storage lever, introducing more components to provision, monitor, and reason about during failures, so it belongs only where a single disk genuinely cannot reach the target.

Accelerated Networking carries almost no cost beyond the brief interruption to enable it, which is why it is usually the first lever to try; its only real constraint is the supported-size requirement. A larger size or a different series raises the hourly rate in proportion to the resources gained, and the trap is paying for a resource the workload does not consume, the over-provisioned cores or memory that sit idle while a different ceiling binds. The proximity placement group trades allocation flexibility for latency, and an aggressive group spanning many sizes can fail to place or can pin the workload to a location that limits later growth, so the group should stay as narrow as the latency requirement allows.

The consistent theme is that every lever raises one ceiling at a price, and the discipline is to raise only the binding ceiling and only by as much as the measurement justifies. This is the series habit of measured trade-offs applied to a single machine: the spend is matched to evidence, the change is confirmed by a number, and the next lever is reached for only when the current ceiling has provably moved.

## The ceiling of tuning and when to redesign instead

There is a point past which tuning a single machine stops being the right answer. Every dimension has a top tier, and when a workload pushes a single machine against the largest disk, the fastest network path, the biggest compute or memory series, and still cannot meet its target, the constraint has moved from the machine to the architecture. Continuing to spend on a bigger single machine past that point buys diminishing returns at increasing cost, and the honest engineering move is to change the shape of the solution rather than its size.

The redesign options depend on which ceiling the single machine cannot clear. A workload that has exhausted a single machine's compute often belongs on more than one machine behind a load balancer, scaling out rather than up, which is the natural path once vertical scaling reaches its limit. A workload pinned on a single database machine's IOPS may belong on a managed database service whose performance scales independently of any one machine, or on a sharded design that spreads the load. A workload chasing the lowest possible latency for a tightly coupled tier may have reached the floor that physics and the platform impose, and the next gain comes from reducing the number of round trips in the protocol rather than from any infrastructure lever.

Knowing when to stop tuning is itself a tuning skill. The signal is a lever whose measured gain no longer justifies its cost, or a dimension already at its top tier with the target still unmet. At that point the question changes from which ceiling to raise to which architecture to adopt, and the answer often lives in the broader series rather than in this single machine. A workload that has outgrown vertical scaling is the moment to read the cost angle of sizing carefully, to weigh scaling out against scaling up, and to bring the performance pillar of a formal architecture review to bear on the design rather than the instance.

For readers who want to run these levers against a real machine rather than only read about them, the hands-on path is to [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.net/tools/azure-labs.html), where the disk-tier changes, the Accelerated Networking toggle, the resize commands, and the measurement harness can be reproduced in a sandbox and the before-and-after numbers captured without risk to a production workload. Reproducing a bottleneck and clearing it in a lab is the fastest way to internalize the find-the-bottleneck-first rule, because the measurement becomes muscle memory rather than a step to remember.

## Why the order you try the levers in matters

Once the binding dimension is known, more than one lever can usually raise it, and the order you try them in decides how much you spend to reach the same result. The principle is to exhaust the free and the cheap levers before the paid ones, because a free lever that solves the problem makes the paid lever unnecessary, while a paid lever applied first hides whether the free one would have sufficed.

On the storage dimension, the free levers come first: matching the host caching mode to the read pattern, moving churning temporary activity onto the included temporary volume, and confirming the operating-system volume is not the hidden throttle. Only when those are exhausted does the cheap lever follow, raising provisioned IOPS on a flexible tier to the measured need, and only when that ceiling is genuinely reached does the expensive lever follow, striping several volumes or moving to the top tier. On the network dimension the order is even starker, because Accelerated Networking is free and frequently decisive, so it is always tried before the paid lever of a larger size. On the compute and memory dimensions the levers are mostly paid, but even there the free move of confirming the work uses the cores it already has, through per-core reading, precedes buying cores that would idle.

Trying the levers in cost order has a second benefit beyond saving money: it isolates the cause. A free lever that resolves the symptom proves the diagnosis cheaply, and a free lever that does not move the number narrows the search before any spend. Reaching for the expensive lever first muddies both the budget and the evidence, because a paid change that helps cannot tell you whether a free change would have helped as much. The disciplined order, free before cheap before expensive, is the find-the-bottleneck-first rule extended from which dimension to raise into how to raise it without overpaying.

## The verdict on Azure VM performance tuning: measure the ceiling, then raise only that one

The closing position of this guide is the same as its opening claim, now earned rather than asserted. Azure VM performance tuning is not the art of buying a faster machine; it is the discipline of finding which of storage, network, processor, and memory binds the workload, raising that one ceiling with the matching lever, and confirming the gain with a measurement before asking whether the constraint has moved. The resize button is the last lever, not the first, because three of the four ceilings it raises were probably never the limit, and the one it does address, compute, deserves the same evidence as the rest.

This sits inside a larger model of how Azure compute works, which the foundational treatment of the platform's compute service lays out in the [complete engineering guide to Azure Virtual Machines](/2022/01/03/azure-virtual-machines-complete-guide/); tuning is the performance layer on top of that model, and the model is worth holding clearly before tuning against it. The cost dimension of the same decision, when to spend on a larger machine and when a smaller one paired with the right disk would serve, belongs to the discipline of [right-sizing Azure VMs to cut cost](/2024/11/04/azure-vm-right-sizing/), which is the mirror image of this work: performance tuning raises a ceiling that binds, right-sizing lowers a ceiling that wastes, and the two together keep the machine matched to the workload in both directions. When a tuning change goes wrong and the machine will not come back, for instance after a size change that the chosen image cannot boot on, the recovery path runs through the diagnosis in [fixing an Azure VM boot failure and no-boot issues](/2022/05/23/fix-azure-vm-boot-failure/), since a resize across hardware boundaries is one of the events that can surface a boot problem. And the principle behind the whole method, spending matched to measured need rather than to hope, is the performance pillar of the [Azure Well-Architected Framework](/2024/06/10/azure-well-architected-framework/), which formalizes the habit this guide builds into a single machine across an entire estate.

The engineer who internalizes the find-the-bottleneck-first rule stops fearing slow machines and starts reading them. A slow machine is no longer a mystery to be solved by spending; it is a question with an answer in the metrics, a binding ceiling that names its own lever, and a measurement that will confirm the fix or expose the misdiagnosis. That shift, from hope to evidence, is the entire return on learning to tune. It saves the budget, it saves the afternoon, and it produces knowledge that transfers to the next machine instead of evaporating with the last guess.

## Frequently Asked Questions

### Q: How do I tune Azure VM performance the right way?

Start by refusing to resize until you know which dimension is slow. A machine runs at the speed of whichever of storage, network, processor, or memory saturates first, so the first move is to read the metrics and find the saturated one. Watch the data-disk and OS-disk consumed-percentage counters for storage, the bandwidth and packet counters for network, the percentage-CPU counter for processor, and the guest memory counters for memory. Whichever sits pinned at its ceiling while the others idle is the binding constraint. Raise only that dimension with its matching lever, a higher disk tier for storage, Accelerated Networking or a bigger size for network, more cores for processor, a memory-optimized series for memory, and confirm the gain with a before-and-after measurement under the same load. Then ask whether the constraint has moved to a new dimension and repeat. Tuning is this loop, not a single purchase, and the measurement at each step is what separates it from guessing.

### Q: How do disk tiers affect IOPS and throughput on an Azure VM?

Each managed disk tier sets a maximum for IOPS and for throughput that holds no matter how large the machine attached to it is. Standard HDD and Standard SSD sit at the low end, Premium SSD prices performance into fixed size tiers, Premium SSD v2 lets you provision capacity, IOPS, and throughput as three independent dials, and Ultra Disk reaches the highest ceilings with sub-millisecond latency. A larger machine never raises a per-disk ceiling; it only raises the aggregate budget the machine can sustain across all its disks, which is a separate cap, and performance is gated by the lower of the two. IOPS governs many small random operations such as a transactional database, while throughput governs large sequential transfers such as a backup, and a disk can be starved on one axis while the other idles. Diagnose which axis is pinned before changing tiers. Treat the specific numbers as values to verify against the current disk documentation, since they shift by region, size, and hardware generation.

### Q: What does Accelerated Networking actually do for a VM?

Accelerated Networking enables single root I/O virtualization on supported machine sizes, giving the guest a direct hardware path to the physical network adapter so traffic bypasses the host virtual switch. Without it, every packet is processed in software on the host, where network policy is enforced, which adds latency and consumes host processor cycles. With it, that policy enforcement moves onto programmable hardware and the guest talks to the card almost directly, which lowers latency and jitter, reduces processor overhead, and raises the packets-per-second the machine can handle. The feature is free and generally available. Independent tests have shown round-trip latency on a pair of general-purpose machines falling from roughly 300 microseconds to around 55 to 60 microseconds once enabled, though the exact figures depend on size, region, and workload. The benefit concentrates in latency-sensitive and high-packet-rate workloads such as multi-tier applications and in-memory caches, and barely registers for a workload that moves a few large files an hour.

### Q: Why did resizing my VM to a larger size not improve performance?

The most likely answer is that the machine was never the bottleneck. A larger size raises the processor and memory ceilings and the aggregate storage and network budgets, but it cannot raise a per-disk performance cap that the storage tier itself sets, and it does not retroactively enable Accelerated Networking on a network-bound workload. If the job was waiting on a Standard SSD's IOPS, the extra cores have nothing to do and the elapsed time barely moves while the hourly bill climbs. Confirm the real constraint by reading the metrics: a data-disk consumed percentage near one hundred with low processor use means storage was the wall, and the fix is a higher disk tier or more provisioned IOPS, not a bigger machine. The lesson is the find-the-bottleneck-first rule: measure the saturated dimension before spending, because three of the four ceilings a resize raises were probably not the limit.

### Q: How do I find whether my VM is CPU-bound or memory-bound?

The two have distinct signatures. A processor bottleneck shows the percentage-CPU metric pinned near one hundred for sustained periods while disk and network sit idle, with the run-queue length climbing inside the guest as work waits for a free core. A memory bottleneck shows available memory falling toward zero with active paging or swapping, and latency that spikes in correlation with that swap activity as the working set overflows RAM. The important caveat is that the platform metrics show processor usage directly but cannot see guest memory without the guest diagnostics extension installed, because memory accounting lives inside the operating system. Without that extension a memory problem is invisible in the portal and is easily misread as something else. Also check per-core utilization rather than the aggregate, since a single-threaded job can pin one core while the machine-level average stays low, which calls for parallelism rather than a bigger machine.

### Q: How does a proximity placement group reduce latency between VMs?

A proximity placement group is a placement constraint that asks Azure to allocate the machines in the group physically close to one another, ideally in the same datacenter and network segment. Two machines in the same region can otherwise sit in different datacenters, and the physical distance between them sets a floor on round-trip latency that no machine-level lever can lower. Co-locating them cuts that distance and shaves the round-trip time, which matters for a latency-sensitive synchronous protocol making many round trips per request and not at all for a workload that makes one large call. The lever stacks with Accelerated Networking rather than replacing it: the feature removes the per-packet host overhead, the placement group removes the physical distance. The cost is reduced allocation flexibility, since constraining placement can make capacity harder to obtain, especially for large sizes, so keep the group as narrow as the latency requirement demands and deploy the most constrained size first.

### Q: What is the difference between Premium SSD and Premium SSD v2?

Premium SSD prices performance into fixed size tiers labeled P1 through P80, so raising IOPS means buying a larger disk even when the extra capacity is useless, because performance is bundled with size. Premium SSD v2 breaks that bundle by letting you provision capacity, IOPS, and throughput as three independent dials, with a baseline of IOPS and throughput included free on any size and the ability to raise each dial exactly as far as the workload needs. A small Premium SSD v2 volume can carry high provisioned IOPS without paying for gigabytes it will never fill, which is why it is both faster and cheaper than the equivalent Premium SSD for most production workloads and has become the sensible default for new deployments. The one nuance is that above a small threshold the maximum throughput rises by a fixed increment per provisioned IOPS, so the two dials interact and provisioning benefits from a moment of arithmetic. Verify the exact baseline and ceiling figures against the current disk documentation.

### Q: Does host caching improve Azure VM disk performance?

Host caching can sharply improve read-heavy patterns at no extra charge, but the right mode depends on the workload and the wrong mode can corrupt data. ReadOnly caching serves repeated reads from a cache local to the host, which helps a read-mostly volume or a database serving the same hot pages repeatedly. ReadWrite caching also buffers writes, which means a write acknowledged to the application may still be in cache rather than committed to the disk, and for a database that manages its own write ordering and recovery this can break the durability contract. The common configuration sets the data disk holding database files to None or ReadOnly, reserves ReadWrite for volumes whose write semantics tolerate it, and leaves the operating-system disk on its default. Matching the caching mode to the access pattern is a free lever that is too often skipped, so check it early when diagnosing a read-heavy storage bottleneck before reaching for a more expensive disk tier.

### Q: How do I measure VM performance before and after a change?

Capture a baseline number under real load before touching anything, because a change without a baseline can only be judged by impression. Pull the platform metrics through the command line so the baseline is stored rather than glanced at: percentage CPU for the processor ceiling, the data-disk and OS-disk consumed-percentage counters for storage, and the bandwidth and packet counters for network. Inside the guest, use a tool that reports per-device utilization, queue depth, and latency for storage, and run a controlled load test that exercises the random-IOPS axis and the sequential-throughput axis separately so you know which one was pinned. After the change, re-run the same measurement under the same load and compare. The discipline that ruins most before-and-after comparisons is capturing the baseline at a quiet hour and the after-reading at a busy one, or the reverse; the load must match for the comparison to mean anything.

### Q: Why is my VM slow even though CPU usage is low?

Low processor usage rules out a compute bottleneck and points at one of the other three dimensions, most often storage. A job waiting on a slow disk write looks idle on the processor while it stalls, and the data-disk or OS-disk consumed-percentage counter riding near one hundred confirms it. A network-bound workload also shows low processor use while latency between tiers dominates each request, which Accelerated Networking usually addresses. A memory-bound workload can show low processor use while it pages to disk, visible only through the guest memory counters with diagnostics enabled. The diagnostic move is to read all four dimensions at once rather than fixating on the processor: low CPU with high disk consumption is storage, low CPU with a throughput plateau and high host network overhead is network, low CPU with falling available memory and active swap is memory. The constraint announces itself once you look at the right counter.

### Q: Can I enable Accelerated Networking on an existing VM without rebuilding it?

Yes, in most cases you can enable it on an existing machine without rebuilding, though the change requires a brief interruption. The machine usually must be stopped and deallocated so the network interface property can change, after which you set the accelerated-networking flag on the interface and start the machine again. The constraint is that the machine size must support the feature; if it does not, either pick a supported size or leave the feature off. Two failure modes are worth watching. The feature can be enabled on the interface but not actually carry traffic if the guest operating system lacks the driver for the virtual function, which you confirm by inspecting the interface statistics inside the guest to see whether the virtual function path carries the load. And a machine can fail to start after enabling the feature on an unsupported size, which is resolved by choosing a size that supports it. Reproduce the exact command flags against the current command reference.

### Q: Which Azure VM series should I choose for a database?

The answer depends on whether the database is memory-bound or IOPS-bound, which is itself a tuning question. A database whose working set should sit in memory benefits most from a memory-optimized series such as the E family, or the M family for the largest in-memory datasets, because more gigabytes per core keep the data in RAM and avoid the latency cliff of paging to disk. A database that is IOPS-bound rather than memory-bound benefits more from a fast disk tier, Premium SSD v2 with provisioned IOPS or Ultra Disk, paired with a series that has enough aggregate storage budget to use that disk fully. The mistake is choosing the series before measuring which resource is scarce, because a memory-heavy series wastes money on a database that was actually disk-bound and a general-purpose series starves a database that needed memory. Measure the working set against available RAM and the IOPS demand against the disk ceiling first, then pick the family that matches the scarce resource.

### Q: What happens if the OS disk is the bottleneck instead of the data disk?

The operating-system disk can throttle the whole machine quietly, because attention naturally goes to the data disk and the operating-system disk is often left on a small default tier. Activity that routes through it, including paging, logging, and temporary files, hits that smaller ceiling, and the machine feels sluggish in a way the data-disk metrics do not explain because the constraint lives on the other disk. The signal is the OS Disk IOPS Consumed Percentage counter riding high while the data-disk counter looks healthy. The fix is to raise the operating-system disk tier so it can sustain the traffic, or to move the offending activity, such as a busy temporary directory or a log path, onto a faster data volume provisioned for the load. Reading both disk counters together rather than only the data-disk counter is what exposes this case, and it is common enough that any storage diagnosis should check the operating-system disk as a matter of routine.

### Q: How much faster is Accelerated Networking in real numbers?

Real numbers vary with size, region, traffic path, and workload, so treat any single figure as illustrative rather than guaranteed. Independent latency tests on a pair of general-purpose machines have measured round-trip latency dropping from roughly 300 microseconds without the feature to around 55 to 60 microseconds with it, which is a reduction of more than fourfold on the wire, and the feature also raises the packets-per-second the machine can sustain and lowers processor overhead on the network path. The magnitude matters most for workloads that make many small round trips, where each microsecond saved is multiplied by thousands of round trips per request, and matters little for workloads dominated by a few large transfers. The honest way to know the effect on a specific workload is to run a latency probe before and after enabling the feature and keep both numbers, because the platform and the workload together determine the real gain rather than any published figure.

### Q: When should I scale out to more VMs instead of tuning one VM?

Scale out when a single machine has been pushed against the top tier of the binding dimension and still cannot meet its target, because past that point spending on a larger single machine buys diminishing returns at rising cost. The signal is a lever whose measured gain no longer justifies its price, or a dimension already at its maximum with the goal unmet. A compute-bound workload that has exhausted the largest practical size often belongs behind a load balancer across several machines, scaling horizontally rather than vertically. A database pinned on one machine's IOPS may belong on a managed service whose performance scales independently of any one machine, or on a sharded design. A latency-sensitive tier may have reached the floor that physics imposes, where the next gain comes from cutting round trips in the protocol rather than from infrastructure. Knowing when to stop tuning a single machine and change the architecture is itself part of the discipline, and the trigger is always a measured ceiling rather than a feeling.

### Q: Do I need guest diagnostics enabled to tune a VM?

For a complete picture, yes, because the platform metrics see the machine from the outside and cannot read everything the operating system knows. The platform percentage-CPU metric is a reliable reading of host-charged processor time, and the disk consumed-percentage and network counters are exposed at the platform level, so a storage or network or compute diagnosis can proceed without the extension. Memory is the gap. The platform cannot see guest memory usage without the guest diagnostics extension, because memory accounting lives inside the operating system, so a memory bottleneck is invisible in the portal metrics until the extension forwards the in-guest counters. This is a major reason memory problems are so often misdiagnosed as something else: the metric that would reveal them is not being collected. Enabling guest diagnostics on any machine you intend to tune seriously closes that gap and also gives finer detail on the run queue and per-core processor behavior than the platform view alone provides.

### Q: How is reading time or load capacity affected by striping multiple disks?

Striping combines several disks into one logical volume and spreads the load across them, presenting a combined ceiling that is the sum of the individual disks' provisioned performance, up to the machine's aggregate storage budget. Eight Premium SSD v2 disks striped together can reach a throughput and IOPS that no single disk tier delivers within the machine's limits, which is the lever for a high-throughput analytic or database workload that has exhausted a single disk. The cost is operational weight: a striped volume has more components to provision, monitor, and resize, and a failure model the operator must understand, since the volume's behavior depends on every member disk. Striping also cannot exceed the machine's own aggregate cap, so a small machine gains little from many striped disks because its combined budget binds first. Reach for striping only when a single disk genuinely cannot reach the target and the machine has aggregate budget to spare, not as a routine first move, and confirm the combined ceiling against both the disk and machine limits.

### Q: Is Ultra Disk worth the cost for performance tuning?

Ultra Disk is worth its premium only for workloads that genuinely need its ceilings, mission-critical, latency-sensitive databases requiring very high IOPS or sub-millisecond latency that Premium SSD v2 cannot meet. For most workloads Premium SSD v2 delivers sufficient performance at lower cost, because its independent dials let you provision exactly the IOPS and throughput needed without overpaying, and it covers the large middle of production demand. The way to decide is to measure the actual IOPS, throughput, and latency requirement against what Premium SSD v2 can provision, and reach for Ultra Disk only when the measured need exceeds that tier's ceiling or when the latency requirement is genuinely sub-millisecond. Choosing Ultra Disk by reputation rather than by measurement is the same blind spending the find-the-bottleneck-first rule warns against, applied to storage instead of to machine size. Confirm the current ceilings and pricing of both tiers against the official documentation, since the figures and the relative value shift as the platform evolves.
