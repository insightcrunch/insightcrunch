---
layout: post
title: "Complete System Design Interview Guide: Patterns & Practice Problems"
page_title: "Complete System Design Interview Guide: Step-by-Step Approach, Real-World Architecture Examples, Scalability Patterns & Practice Problems for SDE-2 and Senior Roles"
date: 2025-05-28
categories: ["Industry"]
tags: ["system design interview", "system design preparation", "scalability", "distributed systems", "SDE-2 interview", "senior engineer interview", "high level design", "low level design", "database design", "microservices"]
excerpt: "How to crack system design interviews. Structured approach with real problems like URL shortener, chat app, and news feed, plus distributed systems..."
image: "/assets/images/blog/blog-54.webp"
reading_time: 55
author: "Insight Crunch Team"
last_updated: 2026-03-23
---
## Table of Contents

- [What System Design Interviews Are Actually Testing](#what-system-design-tests)
- [The 45-Minute Interview Framework: Step by Step](#interview-framework)
- [Requirements Gathering: The Skill Most Candidates Skip](#requirements-gathering)
- [Capacity Estimation: Numbers Every Engineer Should Know](#capacity-estimation)
- [High-Level Design: Components, APIs, and Data Flow](#high-level-design)
- [Database Design: SQL vs NoSQL, Schemas, and Indexing](#database-design)
- [Scalability Patterns: The Building Blocks of Large Systems](#scalability-patterns)
- [Caching: Strategy, Layers, and Invalidation](#caching)
- [Message Queues and Event-Driven Architecture](#message-queues)
- [Consistency, Availability, and the CAP Theorem](#cap-theorem)
- [Real-World System Design Walkthroughs: 12 Complete Examples](#system-walkthroughs)
- [Low-Level Design: Class Diagrams, OOP, and Design Patterns](#low-level-design)
- [Common System Design Mistakes That Cost Candidates the Job](#common-mistakes)
- [Preparation Resources and Study Plan](#preparation-resources)
- [Frequently Asked Questions](#faq)

---

## What System Design Interviews Are Actually Testing {#what-system-design-tests}

System design interviews are not tests of memorised architectures. They are structured evaluations of how an experienced engineer thinks about building large-scale, reliable, maintainable software systems under ambiguous, open-ended conditions. Understanding this distinction is the foundational insight that separates candidates who prepare effectively from those who memorise system diagrams and then struggle when an interviewer asks a question that deviates from the pattern.

A system design interview is required for SDE-2 (Software Development Engineer - Level 2) and above at most product-based companies. The specific threshold varies: some companies introduce system design at 3 years of experience; others wait until 5-6 years. But for any role beyond the junior individual contributor level at a product company, system design is part of the interview loop.

![Complete System Design Interview Guide: Step-by-Step Approach, Real-World Architecture Examples, Scalability Patterns & Practice Problems for SDE-2 and Senior Roles](/assets/images/blog/blog-54.webp)
Complete System Design Interview Guide — Step-by-Step Approach, Real-World Architecture Examples, Scalability Patterns and Practice Problems for SDE-2 and Senior Roles

### The Four Dimensions of System Design Evaluation

Most companies use a rubric that evaluates candidates across four dimensions:

**Problem Scoping:** Did you identify the right problem to solve? Did you clarify ambiguous requirements? Did you make scope decisions that are sensible given the constraints? Many candidates receive a problem statement and immediately start drawing boxes on a whiteboard. The candidates who score highest spend the first 5-7 minutes asking questions and aligning on what they are building and for what scale.

**Technical Depth:** Do you understand the trade-offs between architectural choices? Can you articulate why you are choosing a relational database over a NoSQL store for this specific use case? Do you know the failure modes of the components you are proposing? Generic architectures score poorly; architectures that are deliberately designed for the specific problem's scale and access patterns score well.

**Breadth of Approach:** Can you identify multiple valid approaches to a sub-problem? Do you know when to use a message queue versus direct synchronous service calls? Can you discuss the trade-offs between SQL and NoSQL, between eventual and strong consistency, between a monolith and microservices? Breadth demonstrates that your design choices are deliberate rather than default.

**Communication:** Can you explain complex technical decisions in clear language? Can you take a hint or incorporate feedback without defensiveness? Do you lead the conversation or wait to be led? System design is inherently collaborative - interviewers look for evidence that you would be effective in architecture discussions with a real team.

### Why Senior Engineers Often Do Worse Than Expected

A counterintuitive finding in system design interviews is that some engineers with 8-10 years of experience perform worse than engineers with 4-5 years who have prepared systematically. The reason: experienced engineers who have not specifically prepared for system design interviews tend to jump to the architecture they know best (the one from their current company), skip the requirements and estimation phases, and struggle to discuss trade-offs in areas outside their current specialisation. Systematic preparation is not just for junior engineers - it is essential for experienced engineers who have not recently practised structured design communication.

---

## The 45-Minute Interview Framework: Step by Step {#interview-framework}

A structured framework for the 45-60 minute system design interview prevents the two most common failure modes: spending too long on one area at the expense of others, and failing to cover the phases that interviewers specifically evaluate. The following time allocation is calibrated for a 45-minute interview; adjust proportionally for 60-minute sessions.

### Phase 1: Clarify Requirements (5-7 minutes)

Begin every system design interview with requirements gathering. Ask the interviewer questions that establish:

**Functional requirements:** What does the system do? What are the core user-facing features? For a URL shortener: "Do users need custom aliases? Do we need analytics on link clicks? Should links expire?"

**Non-functional requirements:** What are the scale, performance, and reliability expectations? "What is the expected daily active users? What is the read-to-write ratio? What latency is acceptable for reads? What availability SLA is required - 99.9% or 99.99%?"

**Scope boundaries:** What is explicitly out of scope for this design session? "Should I focus on the core shortening and redirect service, or include the analytics dashboard as well?" Making explicit scope decisions demonstrates engineering judgment.

**User types and personas:** Who are the actors in the system? "Are there both consumers and businesses? Do admins have different capabilities?" Different user types often imply different data access patterns and permission models.

At the end of Phase 1, summarise your understanding: "So we are building a URL shortener that handles roughly 100 million redirects per day, needs sub-100ms read latency, requires 99.99% availability for the redirect service, and stores links indefinitely unless explicitly deleted. I'll deprioritise the analytics dashboard for now. Does that sound right?"

### Phase 2: Capacity Estimation (5-7 minutes)

Back-of-the-envelope calculations establish the scale of the system and drive architectural decisions. A system that handles 1,000 requests per day is designed very differently from one that handles 1 million. Capacity estimation demonstrates that you understand the practical implications of scale. Key calculations:

- Reads per second (RPS) and writes per second (WPS)
- Storage requirements (per unit × units per day × retention period)
- Bandwidth requirements (average payload size × throughput)
- Memory requirements for caching (what percentage of data should be in cache?)

Write your estimates clearly. State your assumptions explicitly: "I'll assume an average URL is 100 bytes stored, an average response is 50 bytes, and we retain links for 5 years."

### Phase 3: High-Level Design (10-12 minutes)

Draw the major components and the data flow between them. A typical high-level design includes: clients (web, mobile, API consumers), load balancers, application servers, databases (primary and replicas), cache layers, and any external systems (CDN, message queues, third-party services). Label the arrows between components with the protocol (HTTP, gRPC, AMQP) and the direction of data flow.

Describe each component as you draw it: what it does, why it is here, and what its primary data store is. Do not just draw boxes - the explanation is scored as heavily as the diagram.

### Phase 4: Deep Dives (15-18 minutes)

After establishing the high-level design, go deep on two or three specific areas. The interviewer may direct you ("Let's talk more about how you would handle the database at scale") or leave the choice to you ("What would you like to explore further?"). If given a choice, prioritise the areas that are most technically interesting and most central to the system's correctness or performance.

Deep dives typically cover: database schema design, caching strategy, handling of a specific failure scenario, the design of a particularly complex component (e.g., a rate limiter, a notification service, a search indexing pipeline), or the handling of edge cases (duplicate requests, partial failures, consistency under partition).

### Phase 5: Wrap-up and Discussion (5-7 minutes)

In the final minutes, address anything you explicitly deferred and discuss potential improvements. Mention what you would do differently with more time, what monitoring and alerting you would add, how you would approach the operational aspects (deployment, migration strategy), and how the design might evolve as the system scales.

This phase demonstrates forward-thinking engineering maturity. Candidates who say "I think the design is complete" and fall silent in the final minutes score lower than candidates who discuss future evolution, known trade-offs they accepted, and what they would investigate further.

---

## Requirements Gathering: The Skill Most Candidates Skip {#requirements-gathering}

Requirements gathering is the most underinvested skill in system design preparation. Candidates who have practised 20 system design problems but have not specifically practised the requirements phase tend to ask a few vague questions and then dive into design. This creates two problems: the design may solve the wrong problem, and the candidate misses the opportunity to demonstrate engineering judgment by making deliberate scope choices.

### Functional vs Non-Functional Requirements

**Functional requirements** define what the system does - the features and behaviours from the user's perspective. For a notification service: "Send push notifications, SMS, and email. Support scheduling notifications for future delivery. Allow users to set preferences for notification type per category."

**Non-functional requirements** define how well the system does it:

- **Scalability:** How many users, how many requests per second?
- **Availability:** What is the acceptable downtime per year? 99.9% availability means about 8.7 hours of downtime per year; 99.99% means about 52 minutes; 99.999% (five nines) means about 5 minutes.
- **Latency:** What is the acceptable response time at p50, p95, and p99? Note that latency requirements are almost always percentile-based in production systems - saying "average latency of 100ms" is less meaningful than "p99 latency under 500ms."
- **Durability:** What is the acceptable data loss tolerance? Zero data loss requires synchronous replication; small data loss tolerance allows asynchronous replication for better performance.
- **Consistency:** Does the system require strong consistency (reads always see the latest write) or can it tolerate eventual consistency (reads may see stale data for a short window)?

### The Questions to Ask for Any System Design Problem

A universal set of questions that apply to almost every system design problem:

1. How many daily active users (DAU) does this system serve?
2. What is the expected read-to-write ratio?
3. What is the acceptable read latency? Write latency?
4. What is the availability requirement?
5. Does the system need to be globally distributed (multiple regions)?
6. What is the data retention requirement?
7. Are there real-time or near-real-time requirements (live feed, notifications)?
8. What is the most critical feature - the core that must work even if everything else degrades?

These questions take 3-4 minutes to ask and answer but fundamentally shape the architecture. A URL shortener with 1 million DAU and a relaxed SLA is architecturally simpler than one with 1 billion DAU and five-nines availability. Knowing the actual requirement before designing prevents overengineering (designing for billion-scale when the actual need is million-scale) and underengineering (failing to plan for the scale that is actually required).

---

## Capacity Estimation: Numbers Every Engineer Should Know {#capacity-estimation}

Capacity estimation is a practiced skill that requires knowing a set of reference numbers by memory and applying simple arithmetic to derive system-level requirements. These are the numbers to internalise:

### Reference Numbers for Back-of-the-Envelope Calculations

**Time units:**
- 1 day ≈ 86,400 seconds (round to 100,000 for easy math)
- 1 month ≈ 2.5 million seconds
- 1 year ≈ 30 million seconds

**Throughput:**
- 1 million DAU each making 10 requests/day = 10 million requests/day ≈ 100 RPS
- 100 million DAU with 10 requests/day = 1 billion requests/day ≈ 10,000 RPS

**Storage:**
- 1 character ≈ 1 byte
- 1 image (compressed) ≈ 300 KB
- 1 video minute (compressed, 720p) ≈ 10 MB
- 1 tweet-length text post ≈ 200-300 bytes
- 1 user profile record ≈ 1-2 KB

**Bandwidth:**
- 10,000 RPS × 1 KB average payload = 10 MB/s bandwidth
- 1 Gbps network link ≈ 100-125 MB/s

**Memory:**
- 1 GB of cache ≈ 1 million records of 1 KB each
- 32 GB RAM on a single server ≈ 32 million 1 KB records in memory

**Latency order of magnitude (Jeff Dean's numbers, approximate):**
- L1 cache: < 1 nanosecond
- RAM access: ~100 nanoseconds
- SSD random read: ~100 microseconds
- Disk seek: ~10 milliseconds
- Cross-datacenter round trip: ~30-150 milliseconds

### Worked Example: URL Shortener Capacity Estimation

Assumptions:
- 100 million redirects per day (reads)
- 1 million new URLs shortened per day (writes)
- 100:1 read-to-write ratio
- URLs stored for 5 years

**Throughput:**
- Read RPS: 100 million / 86,400 ≈ 1,160 RPS (round to 1,200)
- Write RPS: 1 million / 86,400 ≈ 12 WPS

**Storage:**
- Per URL entry: short code (7 bytes) + original URL (100 bytes avg) + metadata (timestamp, creator, expiry) ≈ 500 bytes total
- New URLs per day: 1 million × 500 bytes = 500 MB/day
- Over 5 years: 500 MB × 365 × 5 ≈ 900 GB ≈ 1 TB

**Cache:** If 20% of URLs account for 80% of traffic (Zipf distribution), caching the top 20% of URLs covers most redirects. 20% of 1 million daily URLs = 200,000 URLs × 500 bytes = 100 MB. Very comfortably fits in memory on a single server.

**Bandwidth:**
- Read bandwidth: 1,200 RPS × 50 bytes (redirect response) ≈ 60 KB/s - negligible
- Write bandwidth: 12 WPS × 500 bytes ≈ 6 KB/s - negligible

This estimation tells us: the system is heavily read-dominant, storage is manageable (~1 TB total), and caching can dramatically reduce database load. These insights directly shape the architecture.

---

## High-Level Design: Components, APIs, and Data Flow {#high-level-design}

High-level design establishes the major components of the system, the APIs they expose, and how data flows between them. This is the phase where candidates demonstrate breadth - knowing which building blocks exist and how they connect.

### Standard Building Blocks

Every system design candidate should be fluent in the following components and when to use each:

**DNS (Domain Name System):** Translates domain names to IP addresses. Also used for geographic load distribution (GeoDNS routes users to the nearest data centre).

**CDN (Content Delivery Network):** Caches static and semi-static content (images, CSS, JavaScript, video segments) at edge nodes close to users. Reduces latency and origin server load dramatically for read-heavy content. CloudFront, Akamai, Fastly, and Cloudflare are major CDN providers.

**Load Balancer:** Distributes incoming requests across multiple application server instances. Layer 4 load balancers operate at the TCP/IP level; Layer 7 load balancers operate at the HTTP level and can route based on URL path, headers, and cookies. Load balancers also perform health checks and remove unhealthy instances from the pool.

**Application Servers:** Stateless compute nodes that process requests and generate responses. Being stateless (no session state stored on the server) allows horizontal scaling (adding more instances) to handle increased load without requiring sticky sessions.

**Databases:** The persistent storage layer. Covered in depth in the database design section.

**Cache:** An in-memory data store (Redis, Memcached) that holds frequently accessed data to reduce database load and improve read latency.

**Message Queue:** An asynchronous communication mechanism (Kafka, RabbitMQ, SQS) that decouples producers of work from consumers. Enables non-blocking writes, buffering of load spikes, and fan-out to multiple consumers.

**Object Storage:** Blob storage for large, unstructured data (images, videos, documents). AWS S3, Google Cloud Storage, Azure Blob Storage. Object storage is highly durable, infinitely scalable, and cheap per GB but has higher latency than database reads.

**Search Index:** A full-text search engine (Elasticsearch, Solr, Typesense) that enables fast, relevance-ranked searches across large text corpora. Maintained separately from the primary database and updated asynchronously.

### API Design in System Design Interviews

Defining the core APIs early in the design anchors the discussion and demonstrates product thinking. API definitions should specify: the endpoint (or RPC method name), the HTTP method (GET, POST, PUT, DELETE), the key request parameters and their types, and the response structure.

For a URL shortener:

```
POST /shorten
Request: { "original_url": string, "custom_alias": string?, "expiry_days": int? }
Response: { "short_url": string, "short_code": string, "expires_at": timestamp? }

GET /{short_code}
Response: HTTP 301/302 redirect to original URL

GET /api/stats/{short_code}
Response: { "original_url": string, "click_count": int, "created_at": timestamp }
```

The choice between 301 (Moved Permanently) and 302 (Found / Moved Temporarily) for the redirect matters: 301 causes browsers to cache the redirect, reducing future load on your servers but preventing click tracking for repeat visitors. 302 prevents caching, ensuring every redirect passes through your servers for tracking. This is a design decision worth discussing explicitly.

---

## Database Design: SQL vs NoSQL, Schemas, and Indexing {#database-design}

Database design is the deepest technical area evaluated in most system design interviews. Getting it right requires understanding the access patterns for the data, the consistency requirements, the scalability needs, and the trade-offs between different storage models.

### SQL (Relational Databases)

SQL databases (PostgreSQL, MySQL, Oracle, SQL Server) store data in tables with predefined schemas, enforce relationships via foreign keys, support ACID transactions (Atomicity, Consistency, Isolation, Durability), and are queried with SQL.

**When to choose SQL:**
- Strong consistency is required (financial transactions, inventory management, reservations where double-booking must be prevented)
- Complex queries involving joins across multiple entities
- Well-defined schema with predictable access patterns
- Moderate scale (single-digit or low double-digit billions of rows)

**Scaling SQL:**
- *Vertical scaling:* Upgrading to a more powerful server. Has limits and is expensive at the top end.
- *Read replicas:* Secondary database instances that synchronise from the primary and serve read traffic. Useful for read-heavy workloads; reads scale linearly with replicas but writes remain on the primary.
- *Sharding (horizontal partitioning):* Distributing data across multiple database instances, each responsible for a subset of the data. Sharding enables write scaling but adds complexity: cross-shard queries become expensive, shard rebalancing is operationally difficult, and cross-shard transactions are painful. Shard by a key that distributes data evenly (user ID modulo number of shards is a common approach).

### NoSQL Databases

NoSQL databases sacrifice some SQL capabilities (typically joins and ACID transactions) in exchange for horizontal scalability, flexible schemas, and better performance at extreme scale for specific access patterns. The major NoSQL categories:

**Key-Value Stores (Redis, DynamoDB, Riak):** Store arbitrary values indexed by a single key. O(1) read and write by key. Excellent for caching, session storage, user preferences, and any access pattern that retrieves data by a single identifier. Poor for range queries or complex filtering.

**Document Stores (MongoDB, Couchbase, Firestore):** Store JSON-like documents indexed by a unique ID, with secondary indexes on nested fields. Excellent for flexible-schema data where entities have varying attributes. Less efficient than relational databases for joins.

**Column-Family Stores (Apache Cassandra, HBase, ScyllaDB):** Organise data as rows with dynamic columns grouped into column families. Designed for write-heavy workloads at massive scale, time-series data, and access patterns that read a complete row by primary key. Cassandra in particular is tunable for availability and eventual consistency and is used at scale by Netflix, Apple, and Discord.

**Graph Databases (Neo4j, Amazon Neptune):** Store entities as nodes and relationships as edges. Excellent for relationship-heavy queries (social graphs, recommendation graphs, fraud detection) that would require expensive multi-level joins in SQL.

**Search Engines (Elasticsearch, Opensearch):** Specialised for full-text search, aggregations, and faceted filtering. Not a primary database - typically used as a secondary index updated from the primary store.

### Schema Design Principles

**Normalisation:** Eliminating redundancy by breaking data into related tables connected via foreign keys. Reduces update anomalies and storage overhead but requires joins for queries.

**Denormalisation:** Deliberately storing redundant data to reduce query-time joins. Improves read performance at the cost of write complexity (must update redundant copies) and potential inconsistency.

For most high-scale systems, the architecture involves a normalised SQL database for writes and consistency, with denormalised read models (in a cache, a document store, or a search index) built asynchronously for read performance.

**Indexing strategy:** Indexes speed up queries by maintaining a sorted copy of indexed columns. The primary key index is always present; secondary indexes should be added for any column frequently used in WHERE clauses or JOIN conditions. Indexes have a cost: they slow down writes (every write must update all indexes) and consume storage. Only index columns whose query benefit justifies the write overhead.

---

## Scalability Patterns: The Building Blocks of Large Systems {#scalability-patterns}

Scalability patterns are the recurring architectural solutions to the fundamental challenge of handling growth - more users, more data, more requests - without proportionally increasing cost or degrading performance.

### Horizontal Scaling (Scale Out)

Adding more instances of a component rather than upgrading a single instance. Horizontal scaling is the primary scalability strategy for stateless application tiers. The prerequisite is statelessness: instances must not hold local state that would make one instance different from another, since load balancers distribute requests arbitrarily.

Horizontal scaling requires a load balancer in front of the scaled tier. Session state must be externalised to a shared cache (Redis) or database. Vertical scaling (upgrading the single instance) is simpler but has a hard ceiling and is expensive at the top end.

### Read Replicas

A read replica is a database copy that synchronises from the primary (master) and serves read-only traffic. Read replicas are the primary scalability mechanism for read-heavy SQL workloads. Replication is typically asynchronous, which means replicas may lag behind the primary by milliseconds to seconds under normal conditions, and longer during high write load. Applications that read from replicas must tolerate eventual consistency.

### Database Sharding

Partitioning data across multiple database instances, each responsible for a range of data. Sharding is necessary when a single database cannot handle the write throughput or storage volume, even with the best hardware.

**Sharding strategies:**
- *Hash-based sharding:* Hash(shard_key) % number_of_shards. Distributes data evenly but makes range queries across the shard key expensive.
- *Range-based sharding:* Assign contiguous ranges of the shard key to each shard (e.g., user_id 1-1 million on shard 1, 1 million to 2 million on shard 2). Enables efficient range queries but risks hot spots (all new users, whose IDs are highest, go to the same shard).
- *Directory-based sharding:* Maintain a lookup table that maps shard key values to specific shards. Flexible but introduces the lookup table as a potential bottleneck and single point of failure.

**Consistent hashing** is an advanced sharding technique that minimises data redistribution when shards are added or removed. Used in distributed caches (Memcached clusters, Redis clusters) and distributed storage systems (DynamoDB, Cassandra). In consistent hashing, servers are mapped to positions on a virtual hash ring; each key is assigned to the nearest server clockwise on the ring. Adding a server affects only the keys that now fall between the new server and its predecessor.

### Service Decomposition and Microservices

Decomposing a monolith into independent services that communicate via APIs or message queues. Microservices enable independent scaling of components (the search service can scale independently of the user service), independent deployment, and team autonomy. Trade-offs: network latency for inter-service calls, distributed transaction complexity, operational overhead of managing many services.

In a system design interview, the question of monolith versus microservices is best answered by the system's scale and team size. For a startup or early-stage product, a modular monolith is often the right architecture. For a system serving hundreds of millions of users with independent teams responsible for different capabilities, microservices are appropriate.

### Rate Limiting

Rate limiting constrains the number of requests a client can make within a time window, protecting the system from abuse, preventing resource exhaustion, and ensuring fair use. Key algorithms:

**Token Bucket:** A bucket holds a fixed number of tokens. Each request consumes one token. Tokens are replenished at a fixed rate. Allows bursting up to the bucket size. Widely used (AWS and Stripe use token bucket algorithms).

**Leaky Bucket:** Requests are added to a queue (bucket) and processed at a fixed rate. Smooths out bursts but adds latency.

**Fixed Window Counter:** Count requests per client in fixed time windows (e.g., 100 requests per minute). Simple but has a boundary problem: a client can make 100 requests in the last second of one window and 100 in the first second of the next, effectively 200 in 2 seconds.

**Sliding Window Log:** Maintain a log of request timestamps per client. Count requests in the last N seconds before each new request. More accurate than fixed window but memory-intensive.

**Sliding Window Counter:** A hybrid that approximates the sliding window by combining the current and previous fixed window counts weighted by overlap. Accurate and memory-efficient.

Rate limiting state (counters per client) is typically stored in Redis for its atomic increment operations and TTL support.

---

## Caching: Strategy, Layers, and Invalidation {#caching}

Caching is the most impactful single technique for improving read performance and reducing database load. Understanding when to cache, what to cache, where to cache, and how to handle cache invalidation is essential for system design interviews.

### Cache Placement Strategies

**Cache-Aside (Lazy Loading):** The application checks the cache before querying the database. On a cache miss, the application reads from the database and populates the cache. The cache is populated lazily - only data that is actually read ends up in cache. This is the most common caching pattern.

*Trade-offs:* Cache misses are expensive (two round trips: cache miss + database read). Initial cold start has high cache miss rate. If the cache fails, the application still works (graceful degradation).

**Write-Through:** Every write to the database simultaneously writes to the cache. The cache is always up to date.

*Trade-offs:* Write latency is higher (both cache and database must confirm). Cache may hold data that is never read (write amplification). Good for read-heavy workloads where freshness is important.

**Write-Back (Write-Behind):** Writes go to the cache immediately; the cache asynchronously writes to the database later. Lowest write latency.

*Trade-offs:* Risk of data loss if the cache fails before writing to the database. Complexity of handling cache failures. Used for write-heavy workloads where some data loss is acceptable (gaming leaderboards, analytics counters).

**Read-Through:** The cache itself handles database reads on a miss. The application only ever interacts with the cache; the cache manages the database interaction transparently.

### Cache Eviction Policies

When the cache is full, an eviction policy determines which entries to remove:

- **LRU (Least Recently Used):** Evict the entry that was least recently accessed. Most commonly used; works well for most workloads.
- **LFU (Least Frequently Used):** Evict the entry with the lowest access frequency. Better than LRU for workloads with clear popularity distributions but more complex to implement.
- **FIFO (First In, First Out):** Evict the oldest entry. Simple but often suboptimal.

### Cache Invalidation

Cache invalidation is notoriously the hardest problem in distributed systems. The core challenge: when data in the primary store is updated, how do you ensure cached copies are invalidated or updated?

**TTL (Time to Live):** Every cache entry has an expiry time. Stale data is automatically evicted after TTL expires. Simple but accepts a window of staleness equal to the TTL. Good for data that can tolerate some staleness (user profiles, product descriptions, public content).

**Event-driven invalidation:** When data is updated in the primary store, publish an event to a message queue. Cache invalidation consumers listen to the queue and delete or update affected cache entries. More complex but enables near-real-time cache consistency.

**Cache-busting with version keys:** Instead of invalidating, create a new cache key that includes a version number when data changes. Old cache entries become orphans and expire naturally via TTL.

### Thundering Herd Problem

When a popular cache entry expires, many concurrent requests simultaneously miss the cache and hit the database, causing a load spike. Mitigations:

- **Probabilistic early expiration:** When a cache entry is close to expiry, proactively refresh it with some probability, so the refresh happens before the entry actually expires.
- **Cache locking:** When a cache miss occurs, only one request fetches from the database and populates the cache; other concurrent requests wait briefly and then read from the newly populated cache.
- **Jittered TTL:** Add random variation to TTL values so that multiple related cache entries do not expire simultaneously.

---

## Message Queues and Event-Driven Architecture {#message-queues}

Message queues decouple producers (services that generate work) from consumers (services that process work), enabling asynchronous communication, load buffering, and fan-out to multiple independent consumers.

### When to Use a Message Queue

Message queues are appropriate when:
- Work can be processed asynchronously (the response to the user does not require the work to be completed immediately)
- Work generation rate can spike above the processing rate (queues absorb bursts)
- Multiple independent services need to react to the same event (fan-out)
- Failures in a downstream service should not fail the entire request (decoupling)

Classic use cases: sending email/SMS notifications after a user action, processing uploaded media files (transcoding, thumbnail generation), propagating events to analytics systems, charging payments asynchronously, updating search indexes after content changes.

### Kafka vs RabbitMQ vs SQS

**Apache Kafka:** A distributed, partitioned, replicated commit log. Messages are persisted on disk and retained for a configurable period (days to weeks). Consumer groups maintain independent offsets; multiple consumer groups can consume the same topic independently. Kafka is designed for high-throughput, ordered, replayable event streaming. Ideal for event sourcing, audit logs, analytics pipelines, and any use case requiring message replay.

**RabbitMQ:** A traditional message broker with rich routing capabilities (exchanges, bindings, routing keys). Messages are consumed and acknowledged; acknowledged messages are deleted. Designed for task queues where work must be done exactly once by exactly one consumer. Easier to set up than Kafka for simple task queue use cases.

**AWS SQS (Simple Queue Service):** A fully managed cloud queue with at-least-once delivery, configurable visibility timeout, and dead-letter queues. SQS Standard has unlimited throughput with possible out-of-order delivery; SQS FIFO guarantees ordering with slightly lower throughput.

In a system design interview, the choice between Kafka and RabbitMQ/SQS depends primarily on: whether you need message replay (Kafka wins), whether you need guaranteed ordering within a partition (Kafka), or whether you simply need reliable task queues with flexible routing (RabbitMQ is simpler).

### Exactly-Once vs At-Least-Once Delivery

Message delivery semantics are critical for correctness:

- **At-most-once:** Messages may be lost but are never processed twice. Suitable for non-critical events (analytics, logging) where occasional loss is acceptable.
- **At-least-once:** Messages are never lost but may be processed multiple times. Requires consumers to be idempotent (processing the same message twice produces the same result as processing it once). The standard for most production systems.
- **Exactly-once:** Each message is processed exactly once. Technically achievable (Kafka Transactions, transactional outbox pattern) but expensive in performance and complexity. Reserved for scenarios where duplicate processing would cause visible harm (payment processing, inventory decrement).

---

## Consistency, Availability, and the CAP Theorem {#cap-theorem}

The CAP theorem is a foundational concept in distributed systems that states a distributed system can guarantee at most two of the following three properties simultaneously:

**Consistency (C):** Every read returns the most recent write or an error. All nodes see the same data at the same time.

**Availability (A):** Every request receives a (non-error) response, though it may not be the most recent data.

**Partition Tolerance (P):** The system continues to function even when network messages between nodes are dropped or delayed.

In practice, network partitions are a reality - distributed systems must be partition-tolerant. The real design choice is between consistency and availability during a partition event. Systems that prioritise consistency over availability (CP systems) return an error when they cannot guarantee the latest data during a partition. Systems that prioritise availability over consistency (AP systems) return potentially stale data during a partition rather than returning an error.

### Consistency Models

The binary C-or-A framing of CAP is an oversimplification in practice. Real systems choose a point on a consistency spectrum:

**Strong Consistency:** All reads return the most recent write. Requires synchronous replication and/or consensus protocols (Raft, Paxos). Most expensive in terms of latency and availability. Required for financial systems, inventory counters, and any scenario where stale reads cause business errors.

**Linearisability:** The strongest consistency model - operations appear to take effect instantaneously at a single point in time. Used in distributed locks and coordination systems (ZooKeeper, etcd).

**Eventual Consistency:** Given no new updates, all replicas will eventually converge to the same value. During the convergence window, different nodes may return different values for the same key. The most available and most scalable consistency model. Used by DNS, Amazon DynamoDB (default), Cassandra, and most NoSQL databases.

**Read-Your-Writes Consistency:** A user always reads the results of their own writes. A weaker guarantee than strong consistency but sufficient for many user-facing applications (you always see your own profile updates, even if others may briefly see an older version). Implementable by routing a user's reads to the primary replica immediately after a write, or by storing write timestamps in a client session.

**Causal Consistency:** Operations that are causally related (A happens before B) are seen in that order by all nodes. Weaker than linearisability but stronger than eventual consistency. Relevant for comment threads and collaborative editing.

### PACELC: Beyond CAP

PACELC extends CAP by recognising that even in the absence of a partition (during normal operation), there is a trade-off between Latency and Consistency. A system that avoids network partitions still faces a choice: respond quickly with potentially stale data (lower latency, lower consistency) or wait for synchronous replication before responding (higher latency, higher consistency). Most production databases and distributed systems sit at a configurable point on this trade-off.

---

## Real-World System Design Walkthroughs: 12 Complete Examples {#system-walkthroughs}

The following twelve system design walkthroughs cover the most frequently asked and most architecturally instructive problems in product-based company interviews. Each walkthrough covers the key design decisions; for full depth on each, use these as starting frameworks and extend during practice.

### 1. URL Shortener (Bitly, TinyURL)

**Core challenge:** Generating short, unique codes at high write volume; redirecting at very high read volume with low latency.

**Architecture:** Clients → Load Balancer → Stateless App Servers → Cache (Redis) → SQL DB (PostgreSQL). Short code generation uses Base62 encoding of an auto-incrementing ID from a distributed ID generator (like Twitter Snowflake or a centralised ID service). The redirect path checks Redis first; on a miss, reads from DB and populates cache. DB schema: (short_code, original_url, user_id, created_at, expires_at). Index on short_code. Redirect response is HTTP 302 for analytics tracking.

**Scale considerations:** At 1 billion redirects/day, a single Redis node handles easily (1 GB RAM for 2 million cached URLs covers 80%+ of traffic given Zipf distribution). DB sharded by short_code if write volume grows beyond single-primary capacity.

### 2. Instagram / Photo Sharing

**Core challenge:** Upload pipeline for large media files; news feed generation at scale; follow graph management.

**Architecture:** Upload path: Client → CDN pre-signed URL → Object Storage (S3) → Message Queue (Kafka) → Media Processing Service (transcoding/thumbnails) → Update metadata DB. Feed path: User → App Server → Feed Cache (Redis) → Fan-out service on post creation. Post metadata in PostgreSQL (post_id, user_id, s3_url, caption, created_at). Follow relationships in a graph store or denormalised in a wide-column store. Feed generation uses pull model (aggregate posts from followed users on request) for accounts with many followees, and push model (fan-out to follower feeds on post creation) for regular users.

**Celebrity problem:** High-follower accounts (millions of followers) would cause fan-out storms on post creation. Use a hybrid: push to regular followers, pull from celebrity accounts at read time, merge in the feed service.

### 3. Twitter / Microblogging

**Core challenge:** Timeline generation for millions of users; real-time tweet delivery; search over the tweet corpus.

**Architecture:** Similar to Instagram but optimised for text. Tweet storage: Cassandra (high write throughput, time-series access pattern). Timeline: pre-computed per-user timeline stored in Redis. Fan-out service publishes to follower timelines on tweet creation. Search index: Elasticsearch updated asynchronously via Kafka. Direct messages: separate service with end-to-end encryption.

**Trending topics:** Count hashtag mentions in a sliding window (Redis sorted set with TTL, Kafka Streams for windowed aggregation). Top-K trending computed periodically and cached.

### 4. YouTube / Video Streaming

**Core challenge:** Upload and transcoding pipeline; adaptive bitrate streaming; CDN-based delivery at global scale.

**Architecture:** Upload: Client → App Server → Object Storage (raw video). Transcoding: message queue triggers Transcoding Service, which produces multiple quality variants (360p, 720p, 1080p) and stores to Object Storage. Delivery: Video segments served from CDN edge nodes using HLS or DASH adaptive streaming protocol. Client selects segment quality based on available bandwidth. Metadata (video_id, uploader_id, title, description, thumbnail_url, view_count) in PostgreSQL. View count in Redis with periodic flush to DB to avoid write amplification.

### 5. Uber / Ride-Sharing

**Core challenge:** Real-time location tracking of drivers; matching algorithm; surge pricing; ETA computation.

**Architecture:** Driver location updates (every 3-5 seconds) → Location Service → Geospatial Index (Quadtree or Geohash in Redis). Rider requests trigger Matching Service, which queries location index for nearby available drivers within a radius, ranks by ETA, and dispatches the best match. Trip state machine (requested → accepted → in-progress → completed) managed in a state service with PostgreSQL. Surge pricing: demand/supply ratio per geohash cell computed periodically, published to a pricing service.

**WebSocket connections:** Maintain persistent WebSocket connections between drivers and the server for real-time location streaming and dispatch notifications. Load balance WebSocket connections using consistent hashing so all connections for a given trip are on the same server, or use a publish-subscribe mechanism (Redis Pub/Sub) to relay messages across servers.

### 6. WhatsApp / Messaging

**Core challenge:** Message delivery with guaranteed delivery and ordering; presence (online/offline status); end-to-end encryption.

**Architecture:** Messages sent via WebSocket to a Chat Server. Chat Server stores message in database (Cassandra: partitioned by conversation_id, sorted by timestamp within partition) and delivers to recipient's Chat Server via a Pub/Sub layer. Delivery acknowledgement: three states (sent, delivered, read). If recipient is offline, message is stored; delivered when they reconnect. Presence service maintains a heartbeat from each client; status stored in Redis with TTL (if heartbeat stops, TTL expires → offline). End-to-end encryption handled client-side; servers only see encrypted ciphertext.

### 7. Designing a Rate Limiter

**Core challenge:** Per-user or per-IP request limiting with low latency; distributed enforcement across multiple app servers.

**Architecture:** Rate limiter implemented as middleware in the API Gateway or as a sidecar. State stored in Redis (atomic INCR + EXPIRE for fixed window; sorted set with score=timestamp for sliding window log). Distributed enforcement: all app servers share the same Redis cluster, so counters are global. Token bucket implemented with Redis MULTI/EXEC transactions. Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset) returned in responses. Rate limit exceeded → HTTP 429 Too Many Requests.

### 8. Search Autocomplete / Typeahead

**Core challenge:** Sub-100ms suggestions for partial-word queries; updating suggestions based on query popularity trends.

**Architecture:** Trie data structure in memory for prefix matching, populated from top-k popular queries. For scale, the Trie is partitioned across multiple nodes (sharded by first 1-2 characters of the prefix). Suggestions ranked by popularity score (query frequency weighted by recency). Query logs written to Kafka; analytics pipeline computes top-k queries per prefix daily and pushes updates to the Trie service. For very fresh data, a real-time layer (Redis sorted set per prefix, updated on query) supplements the batch-computed Trie.

### 9. Distributed Key-Value Store

**Core challenge:** Consistent hashing for partitioning; replication for durability; quorum reads/writes for tunable consistency.

**Architecture:** Data distributed across nodes via consistent hashing with virtual nodes. Each key replicated to N successor nodes on the hash ring (typically N=3). Read and write quorums: W + R > N guarantees at least one node with the latest value is included in every read (W = write quorum, R = read quorum; e.g., W=2, R=2, N=3). Coordinator node (the first node responsible for the key) handles quorum coordination. Gossip protocol for node membership and failure detection. Vector clocks for conflict resolution. Anti-entropy via Merkle trees for data synchronisation between replicas.

### 10. Notification System

**Core challenge:** Multi-channel delivery (push, SMS, email); prioritised delivery; template management; delivery tracking.

**Architecture:** Notification Service receives notification requests from upstream services via API or message queue. Notification Service looks up user preferences (preferred channel, opt-outs) and routes to channel-specific workers. Channel workers: Push Notification Worker (APNS for iOS, FCM for Android), Email Worker (SendGrid, SES), SMS Worker (Twilio). Priority queue (Kafka topics with priority partitioning) for high vs low priority notifications. Delivery status tracked in Cassandra (notification_id, user_id, channel, status, sent_at, delivered_at, clicked_at). Retry with exponential backoff for transient delivery failures. Dead-letter queue for persistently failing notifications.

### 11. Web Crawler / Search Indexer

**Core challenge:** Politeness (not overwhelming target servers); deduplication; parallel crawling; freshness management.

**Architecture:** URL Frontier (priority queue with politeness constraints - one queue per domain, rate-limited dequeuing per domain). Fetcher workers pull URLs from frontier, fetch pages, parse HTML for links and content. Deduplication: URL deduplication via a Bloom filter (fast probabilistic check before expensive DB lookup); content deduplication via MD5/SHA hash of page content. Extracted content sent to Indexer (Elasticsearch). New URLs discovered during crawl added back to frontier if not already crawled. Crawl schedule: fresh pages crawled more frequently using recency-weighted priority.

### 12. Hotel / Flight Booking System

**Core challenge:** Inventory management with concurrent booking (overbooking prevention); transaction integrity; search and filtering.

**Architecture:** Inventory stored in relational DB (PostgreSQL) with pessimistic or optimistic locking to prevent concurrent overbooking. Pessimistic locking: SELECT FOR UPDATE on the inventory row during the booking transaction. Optimistic locking: version column on inventory row; transaction fails if version changed since read. Booking flow: search → view availability (read replica) → hold/reserve (short TTL lock on inventory, e.g., 10 minutes) → payment → confirm (release lock, decrement availability). Payment integration via payment gateway with idempotency keys to prevent double charges. Search served from denormalised read models updated asynchronously.

---

## Low-Level Design: Class Diagrams, OOP, and Design Patterns {#low-level-design}

Low-level design (LLD) interviews are distinct from high-level system design interviews and focus on object-oriented design, class modelling, and the application of design patterns to specific components. LLD is typically evaluated at SDE-1 and SDE-2 levels and is sometimes combined with the system design round at senior levels.

### The LLD Interview Approach

LLD interviews present a component to design in detail: a parking lot, a snake-and-ladder game, a vending machine, a library management system, an elevator system, a chess game. The evaluation focuses on:

**Class identification:** Can you identify the entities in the problem and model them as classes with appropriate attributes and methods?

**Relationship modelling:** Are the relationships between classes correct (inheritance vs composition, one-to-one vs one-to-many)?

**SOLID principles application:** Single Responsibility (each class has one reason to change), Open/Closed (open for extension, closed for modification), Liskov Substitution, Interface Segregation, Dependency Inversion.

**Design pattern recognition:** Does the problem call for a known design pattern, and can you apply it correctly?

### Essential Design Patterns for LLD Interviews

**Singleton:** Ensure a class has only one instance and provide a global access point. Used for: configuration managers, connection pools, logging services. Implementation must handle thread safety.

**Factory Method / Abstract Factory:** Define an interface for creating objects, but let subclasses decide which class to instantiate. Used when the exact type to be created is determined at runtime (creating different payment providers based on region, creating different notification channel handlers).

**Strategy:** Define a family of algorithms, encapsulate each one, and make them interchangeable. Used when multiple algorithms are valid for a task and the choice should be made at runtime (different sorting strategies, different pricing algorithms, different authentication methods).

**Observer:** Define a one-to-many dependency between objects so that when one object changes state, its dependents are notified. The foundation of event-driven systems and GUI event handling.

**Decorator:** Attach additional responsibilities to an object dynamically. Provides a flexible alternative to subclassing for extending functionality. Used in Java I/O streams, UI component enhancement.

**Command:** Encapsulate a request as an object, enabling parameterised requests, queueing, logging, and undo operations. Used in text editors (undo/redo), job schedulers, transactional systems.

**Builder:** Separate the construction of a complex object from its representation. Used when an object requires many optional configuration parameters (HTTP request builders, SQL query builders).

---

---

## Networking and Communication Protocols in System Design {#networking-protocols}

Understanding how components communicate is foundational to designing reliable distributed systems. Protocol choices affect latency, throughput, ordering guarantees, and operational complexity.

### HTTP and REST

HTTP/REST is the default communication protocol for service-to-service and client-to-server communication. It is stateless, universally supported, human-readable in debug tools, and well-understood. REST uses standard HTTP verbs (GET, POST, PUT, PATCH, DELETE) and status codes (200, 201, 400, 401, 404, 500) to convey intent.

Limitations: HTTP/1.1 has head-of-line blocking at the request level. HTTP/2 multiplexes multiple requests over a single TCP connection, dramatically reducing latency for parallel requests. HTTP/3 (over QUIC) eliminates TCP-level head-of-line blocking entirely and improves performance on lossy mobile networks.

For internal service-to-service communication at high throughput, pure REST over HTTP/1.1 is often suboptimal due to per-request connection overhead and text-based serialisation. Binary protocols (gRPC over HTTP/2) outperform REST significantly at high call volumes.

### gRPC

gRPC is a high-performance RPC framework developed by Google that uses Protocol Buffers (Protobuf) for serialisation and HTTP/2 for transport. Advantages over REST: binary serialisation is 3-10x smaller and faster to serialise/deserialise than JSON; HTTP/2 transport enables bidirectional streaming; strong typing from Protobuf schemas generates client and server code in any language.

gRPC is widely used for internal microservice communication (Netflix, Uber, Square) where performance and type safety are priorities. It is less suitable for public APIs (browser support requires a proxy layer) and for ad-hoc debugging (binary format is not human-readable).

### WebSockets

WebSockets provide full-duplex, persistent communication channels over a single TCP connection. Unlike HTTP (request-response), WebSockets allow the server to push data to the client without the client polling. Ideal for: real-time messaging (WhatsApp, Slack), live feed updates (Twitter timeline, stock tickers), multiplayer games, collaborative editing tools.

Managing WebSocket connections at scale requires sticky routing (all connections for a given user routed to the same server) or a pub/sub layer (Redis Pub/Sub, Kafka) to relay messages between connection servers, since the client is connected to exactly one server but messages may originate from any server.

### Server-Sent Events (SSE)

SSE is a simpler alternative to WebSockets for unidirectional server-to-client streaming. The client opens an HTTP connection and the server streams events over it. SSE works over standard HTTP, automatically reconnects on disconnect, and is natively supported by browsers. Appropriate for: live dashboards, notification delivery, activity feeds where the client needs to receive updates but does not need to send them.

### Long Polling

Long polling is a technique for simulating server push over standard HTTP: the client sends a request and the server holds it open until a new event is available, then responds. The client immediately sends the next request on receiving a response. Higher latency than WebSockets (a new HTTP request-response cycle per event) but simpler infrastructure (works through all proxies and load balancers without special configuration).

### Service Mesh and API Gateway

In microservice architectures, cross-cutting communication concerns (authentication, rate limiting, load balancing, observability, circuit breaking) can be handled by two infrastructure layers:

**API Gateway:** The entry point for external traffic into the microservice cluster. The API gateway handles authentication, SSL termination, rate limiting, request routing, and response aggregation (combining responses from multiple backend services into a single response for the client). Kong, NGINX, AWS API Gateway, and Apigee are common implementations.

**Service Mesh:** Infrastructure for internal service-to-service communication. A service mesh (Istio, Linkerd) injects a sidecar proxy alongside each service instance, which handles mutual TLS, circuit breaking, retries, timeouts, and observability without requiring application code changes. The service mesh is powerful but adds operational complexity; appropriate for large microservice deployments where cross-cutting concerns are pervasive.

### Circuit Breaker Pattern

The circuit breaker pattern prevents a cascading failure where a slow or unavailable downstream service causes the upstream caller to accumulate blocked threads, eventually exhausting resources. The circuit breaker monitors calls to the downstream service and transitions between three states:

**Closed (normal):** Requests pass through. Failure count is tracked. If failures exceed a threshold within a window, the circuit opens.

**Open:** Requests fail immediately without calling the downstream service (fail fast). After a timeout period, transitions to half-open.

**Half-Open:** A limited number of requests are allowed through to test if the downstream service has recovered. If successful, circuit closes; if failures continue, circuit opens again.

Netflix's Hystrix (and its successor Resilience4j) are the canonical implementations. Circuit breakers are essential in any microservice architecture where service dependencies have realistic failure probabilities.

---

## Observability: Metrics, Logging, and Distributed Tracing {#observability}

A system that cannot be observed cannot be reliably operated. Observability - the ability to understand the internal state of a system from its external outputs - is a production system requirement that is increasingly expected to be discussed in senior system design interviews.

### The Three Pillars of Observability

**Metrics:** Numerical measurements collected over time that quantify system behaviour. Key metric categories:

- *Infrastructure metrics:* CPU utilisation, memory usage, disk I/O, network throughput per host.
- *Application metrics:* Request rate, error rate, latency percentiles (p50, p95, p99), queue depth, cache hit rate.
- *Business metrics:* Orders per minute, active users, conversion rate, payment success rate.

Metrics are collected by an agent on each host (Prometheus Node Exporter, Datadog Agent) and stored in a time-series database (Prometheus TSDB, InfluxDB, Datadog). Dashboards (Grafana, Datadog Dashboards) visualise metric time series. Alerting rules fire when metric thresholds are exceeded.

**Logging:** Structured event records that capture what happened and when. In distributed systems, logs must be centralised (each service writes logs; a log aggregation pipeline ships them to a central store) for effective querying. The ELK Stack (Elasticsearch, Logstash, Kibana) and Datadog Log Management are common implementations.

Structured logging (JSON format with consistent fields: timestamp, severity, service_name, trace_id, request_id, user_id, message) is strongly preferable to unstructured text logs because it enables fast indexed searches and aggregations.

**Distributed Tracing:** A complete record of a request's journey across multiple services, from ingress to response. Each service adds a span (start time, duration, operation name, service name, tags) to a trace. A trace ID propagated in request headers connects spans across services into a complete call graph. Distributed tracing reveals which service in a chain is the bottleneck, and provides per-service latency breakdown for complex multi-hop requests.

Jaeger, Zipkin, and Datadog APM are common distributed tracing implementations. OpenTelemetry is the emerging standard for instrumentation that is vendor-neutral.

### Alerting and On-Call

An alert is a rule that fires when a metric crosses a threshold. Effective alerting requires:

- Alerts fire on symptoms (high error rate, elevated p99 latency) not causes (high CPU, disk usage), because symptoms directly indicate user impact.
- Alerts have a clear owner and a runbook (step-by-step troubleshooting guide).
- Alert thresholds are calibrated to minimise false positives (alert fatigue causes on-call engineers to ignore alerts) and false negatives (missing genuine incidents).
- Severity levels (P1 = page immediately, P2 = page within 30 minutes, P3 = next business day) match response urgency to user impact.

In a system design interview, briefly discussing monitoring and alerting strategy in the wrap-up phase is a differentiator that signals production engineering experience.

---

## Security Fundamentals in System Design {#security-design}

Security is a non-functional requirement that senior system design candidates are expected to address without being asked. A design that does not mention authentication, authorisation, data encryption, or input validation signals inexperience with production systems.

### Authentication and Authorisation

**Authentication:** Verifying who the user is. Common mechanisms:
- Username/password with bcrypt hashing (passwords must never be stored in plain text or reversibly encrypted)
- OAuth 2.0 for delegated authentication (users authenticate with a trusted third party - Google, GitHub - and the third party issues an access token)
- JWT (JSON Web Token): A self-contained token encoding claims (user ID, roles, expiry) signed with a secret or private key. The server can validate the JWT without a database lookup, making it stateless and scalable.

**Authorisation:** Verifying what the authenticated user is allowed to do. Models:
- RBAC (Role-Based Access Control): Permissions are associated with roles, roles are assigned to users. Suitable for most enterprise applications.
- ABAC (Attribute-Based Access Control): Permissions are defined by policies that evaluate attributes of the user, resource, and environment. More flexible than RBAC but more complex to manage.
- ACL (Access Control List): Per-resource lists of which users have which permissions. Suitable for file systems and document sharing.

### HTTPS and Encryption in Transit

All external communication must use HTTPS (TLS 1.2 or higher). TLS encrypts data in transit, preventing eavesdropping and man-in-the-middle attacks. Internal service-to-service communication should use mutual TLS (mTLS) in security-sensitive environments, where both the client and server authenticate each other with certificates.

### Encryption at Rest

Sensitive data stored in databases, object stores, and file systems should be encrypted at rest. Most cloud databases and object stores (AWS RDS, S3, DynamoDB) offer transparent encryption at rest using cloud-managed keys or customer-managed keys (KMS). Application-level encryption (encrypting specific fields before writing to the database) provides an additional layer for highly sensitive data.

### Input Validation and Injection Prevention

All user inputs must be validated and sanitised to prevent injection attacks. SQL injection is prevented by parameterised queries / prepared statements, never by string concatenation. Cross-site scripting (XSS) is prevented by encoding user-controlled content before rendering in HTML. Command injection is prevented by avoiding shell execution of user-controlled strings.

Mentioning parameterised queries, HTTPS, JWT authentication, and data encryption at rest in the appropriate sections of a system design discussion demonstrates security awareness without requiring a deep dive into security engineering.

---

## Practice Problems Organised by Difficulty and Company Relevance {#practice-problems}

The following practice problems are organised by difficulty and the interview context in which they most commonly appear. Each problem is followed by the key design challenge it tests.

### Foundational Problems (Start Here)

**URL Shortener (Bitly / TinyURL):** Core concepts - short code generation, read-heavy caching, database choice. Best for: understanding the full design loop from requirements to deep dive.

**Pastebin:** Similar to URL shortener but with text content. Core concepts - object storage for large text content, expiry policies, search.

**Rate Limiter:** Core concepts - token bucket and sliding window algorithms, Redis for distributed state, API Gateway integration.

**Design a Parking Lot (LLD):** Core concepts - object modelling, state machines, polymorphism (different vehicle types, different spot types). A LLD warm-up problem.

### Intermediate Problems (SDE-2 Core)

**Instagram / Photo Sharing:** Core concepts - media upload pipeline, CDN delivery, news feed generation, celebrity problem.

**Twitter / Microblogging:** Core concepts - fan-out on write vs read, trending topics, search indexing, timeline generation at scale.

**WhatsApp / Messaging:** Core concepts - WebSocket connection management, message persistence, delivery acknowledgement, offline delivery.

**Search Autocomplete:** Core concepts - Trie data structure, top-k computation, partitioning and caching of prefix suggestions.

**Ride Sharing (Uber / Lyft):** Core concepts - geospatial indexing, real-time location updates, matching algorithm, surge pricing.

**Notification System:** Core concepts - multi-channel delivery, user preferences, delivery tracking, retry and dead-letter queue.

### Advanced Problems (Senior and Staff Level)

**YouTube / Video Streaming:** Core concepts - transcoding pipeline, adaptive bitrate streaming, CDN at global scale, view count at scale.

**Distributed Cache (Redis):** Core concepts - consistent hashing, replication, eviction policies, cluster management.

**Distributed Key-Value Store (DynamoDB / Cassandra):** Core concepts - consistent hashing with virtual nodes, quorum reads/writes, vector clocks, anti-entropy.

**Web Crawler:** Core concepts - politeness and rate limiting, URL deduplication, content deduplication, crawl scheduling.

**Real-Time Gaming Leaderboard:** Core concepts - Redis Sorted Set for O(log n) rank queries, update frequency trade-offs, global vs regional leaderboards.

**Stock Exchange / Trading System:** Core concepts - order matching engine, FIFO queue per price level, low-latency requirements, exactly-once trade processing.

**Distributed Task Scheduler (like Airflow):** Core concepts - job dependency graph (DAG), distributed execution, failure recovery and retry, at-least-once vs exactly-once execution semantics.

**Event-Driven Architecture for E-Commerce Order System:** Core concepts - Saga pattern for distributed transactions (payment + inventory + fulfilment), transactional outbox pattern, compensating transactions on failure.

### LLD Problems for Practice

- Design an ATM system
- Design a chess game
- Design a snake-and-ladder game
- Design an elevator system
- Design a library management system
- Design a hotel booking system (LLD level: class model for rooms, bookings, customers)
- Design a food delivery system (LLD level: order, cart, restaurant, delivery agent classes)
- Design a ride-sharing system (LLD level: trip state machine, driver and rider models)

For each LLD problem, draw the complete class diagram before writing any code, identify which design patterns apply (Strategy for pricing, Observer for trip status notifications, State for the trip state machine), and implement the core classes in your language of choice.

---

## Common System Design Mistakes That Cost Candidates the Job {#common-mistakes}

### Mistake 1: Starting with the Solution Instead of the Problem

Jumping to "I'll use microservices with Kafka and a distributed cache" before clarifying requirements is the most common and most penalised mistake. The architecture should follow from the requirements, not precede them. Start every design by asking questions.

### Mistake 2: Designing at One Scale for All Problems

A design appropriate for Twitter (100 million DAU) is massively overengineered for a company with 100,000 users. Conversely, a design that works for a startup will not work for a global platform. Scale your design to the stated requirements, and explicitly justify your architectural choices in terms of the scale.

### Mistake 3: Ignoring Non-Functional Requirements

Designing a system that is functionally correct but ignores availability, latency, and consistency requirements is an incomplete design. After establishing the happy-path architecture, explicitly address: what happens when a database is down? How do you handle a cache miss storm? What happens during a network partition?

### Mistake 4: Treating the Database as an Afterthought

Database design is the foundation of most system designs, yet many candidates sketch a single "DB" box and move on. The database choice, schema design, indexing strategy, and scaling approach deserve deep discussion. What type of database? What are the primary access patterns? How does it scale as data volume grows? What are the consistency guarantees?

### Mistake 5: Not Discussing Trade-offs

Every architectural decision has trade-offs. Choosing a NoSQL database gives you horizontal scalability but sacrifices joins and ACID transactions. Choosing eventual consistency gives you availability but risks stale reads. Candidates who present their choices without acknowledging trade-offs appear either unaware of the limitations or unwilling to think critically about their own design.

### Mistake 6: Silent Design

System design is collaborative communication. Drawing boxes silently for ten minutes and then presenting a completed diagram without narration deprives the interviewer of the reasoning process they are evaluating. Think aloud throughout.

### Mistake 7: Overcomplicating the Initial Design

Start with the simplest design that meets the requirements, then evolve it toward scale and reliability. Beginning with a fully distributed, sharded, multi-region, multi-tier caching architecture before establishing the basics makes it impossible for the interviewer to evaluate whether you understand the fundamentals. Build incrementally and explain why each added component is necessary.

### Mistake 8: Ignoring Failure Scenarios

Production systems fail. Disks fail, networks partition, application servers crash, and third-party dependencies become unavailable. A design that works perfectly in the happy path but has no strategy for component failures is incomplete. After establishing the main architecture, walk through at least one failure scenario: "What happens if the primary database goes down? The load balancer detects unhealthy replicas via health checks, promotes a replica to primary using automated failover (AWS RDS Multi-AZ or a Raft-based HA setup), and traffic is redirected. The expected downtime for automated failover is 20-60 seconds." This kind of failure analysis distinguishes senior-level thinking from junior-level thinking.

### Mistake 9: Not Knowing When to Stop

Some candidates go deep on a single sub-problem and run out of time before covering the full design. Others rush through every section so quickly that nothing gets meaningful depth. Time management is itself evaluated. A good rule: if you have spent more than 15 minutes on any single phase, check in with the interviewer - "I have spent quite a bit of time on the database design. Should I continue here or would you like to move to the caching and API layers?" Interviewers appreciate this awareness and will guide you to the areas they want to evaluate more deeply.

### Mistake 10: Presenting Without Checking Understanding

Talking continuously for 40 minutes without pausing to check whether the interviewer is following is a communication failure. Pause at the end of each major phase: "That covers the high-level components. Does this make sense, or should I clarify anything before we go deeper?" This creates space for the interviewer to redirect, ask a clarifying question, or confirm that you should proceed. Good system design communication is a conversation, not a monologue.

---

## Preparation Resources and Study Plan {#preparation-resources}

### Books

**Designing Data-Intensive Applications by Martin Kleppmann:** The definitive text on distributed systems foundations. Covers data models, storage engines, replication, partitioning, transactions, consistency models, and batch and stream processing with exceptional depth and clarity. Chapters 5-9 are the most interview-relevant. This is the single most important book for system design preparation.

**System Design Interview by Alex Xu (Volumes 1 and 2):** A more interview-focused walkthrough of common system design problems with clear diagrams. Less theoretical depth than Kleppmann but very practically oriented toward interview preparation.

**The Art of Scalability by Abbott and Fisher:** A broader treatment of scalability across people, process, and technology. The "Scale Cube" model (X-axis for horizontal duplication, Y-axis for functional decomposition, Z-axis for data partitioning) is a useful mental model for thinking about scalability dimensions.

### Online Resources

**System Design Primer (GitHub):** Arpit Bhayani's and Alex Xu's widely-referenced GitHub repository covering the core concepts, patterns, and problems in system design. Free, comprehensive, and regularly updated. The starting point for most self-study plans.

**ByteByteGo Newsletter and YouTube (Alex Xu):** Excellent visual explanations of system design concepts and interview problems.

**High Scalability (highscalability.com):** Real-world case studies of how companies (Stack Overflow, Twitter, Netflix, Dropbox) have built their systems. Reading these gives authentic context for the patterns described in interview prep materials.

**Engineering Blogs:** Engineering blogs from Uber (eng.uber.com), Netflix (netflixtechblog.com), Airbnb, Meta, LinkedIn, Discord, and Cloudflare describe real system design decisions at scale. These are among the best system design learning resources available.

### 8-Week Study Plan

**Weeks 1-2: Foundations.** Read Kleppmann Chapters 1-4 (data models, storage, encoding, replication). Study the core components: load balancers, CDNs, caches, databases, message queues. Practice capacity estimation until it is fast and confident. By the end of week 2, you should be able to estimate RPS, storage, and bandwidth requirements for any problem within 5 minutes without referring to notes.

**Weeks 3-4: Scalability Patterns and Database Depth.** Study sharding, consistent hashing, rate limiting, and database design in depth. Read Kleppmann Chapters 5-7. Practice 3-4 system design problems with a focus on the requirements and database design phases. Pick one SQL and one NoSQL problem - design a bank account system to understand transactional requirements, and design a social graph to understand NoSQL and graph data models.

**Weeks 5-6: Consistency and Distributed Systems.** Study the CAP theorem, consistency models, distributed transactions, and consensus protocols at a conceptual level. Understand the design trade-offs in the context of 3-4 more interview problems. This is also the right week to study message queues and event-driven architecture in depth - design a notification system and a ride-sharing platform, both of which require deep understanding of asynchronous processing.

**Weeks 7-8: Full Practice and Mock Interviews.** Practice 2 complete system design problems per week under timed conditions (45 minutes each). Conduct 2-3 mock interviews with a partner or on a platform like Pramp or interviewing.io. Review the 12 walkthroughs in this guide and identify which areas need deeper study. In the final week, focus on any specific company's known interview style - review engineering blog posts from your target company to understand the problems they have actually solved in production.

### How to Use Engineering Blogs for System Design Preparation

Engineering blogs are among the most underutilised system design resources. Reading how companies actually solved real scaling problems gives authentic context that transforms abstract concepts into concrete, memorable design decisions. Recommended reading:

**Discord:** Discord's engineering blog covers how they handled millions of concurrent WebSocket connections, why they migrated from MongoDB to Cassandra for message storage, and how they engineered low-latency voice connections. Each post directly maps to system design interview topics.

**Netflix Tech Blog:** Netflix's posts on chaos engineering (intentionally breaking production to test resilience), their microservice architecture, and their CDN (Open Connect) provide exceptional depth on large-scale reliability engineering.

**Uber Engineering Blog:** Uber's posts on their geospatial systems, their migration from monolith to microservices, and their data infrastructure are directly relevant to ride-sharing and real-time systems design problems.

**Cloudflare Blog:** Cloudflare's explanations of how CDNs work, DDoS mitigation, and DNS infrastructure are technically precise and highly readable. Particularly useful for understanding networking-layer design.

**Instagram Engineering:** Instagram's early posts on scaling PostgreSQL, adopting Cassandra, and building their feed infrastructure are classics of system design literature that directly correspond to common interview problems.

Set aside one hour per week during your preparation to read one engineering blog post. Annotate it with the design pattern it exemplifies and the problem it solved. These real-world examples become powerful talking points in interviews when you can say "this is the approach Instagram used when they faced the same fan-out problem" - it demonstrates that your knowledge comes from genuine study of production systems, not just interview prep materials.

---

## Frequently Asked Questions {#faq}

**Q1: Is system design required for SDE-1 roles?**

Generally no. System design interviews are standard from SDE-2 (3+ years of experience) onwards at most product-based companies. Some companies introduce a lightweight "object-oriented design" or "low-level design" round at the SDE-1 level, which is different from full system design. If you are preparing for your first or second job, DSA preparation is more important than system design.

**Q2: How long does it take to prepare for system design interviews?**

For engineers with 4-6 years of experience who already have some distributed systems exposure, 6-8 weeks of focused preparation (2-3 hours per day) is typically sufficient to perform well in interviews. Engineers who are newer to distributed systems concepts may need 10-12 weeks. The preparation is not front-loaded - you need to study the foundations before practising problems, or the problem practice will be shallow.

**Q3: Should I memorise system designs or understand the principles?**

Understanding principles, not memorising designs. An interviewer who asked you to design YouTube last week will notice if you present the same design for a completely different problem next week. More importantly, interviewers routinely add constraints or ask "what if" questions that derail memorised designs but are easily handled by candidates who understand the underlying principles. Study real systems to build intuition, but always understand why each component is there.

**Q4: What is the difference between HLD (High-Level Design) and LLD (Low-Level Design)?**

High-Level Design covers the overall system architecture: major components, data flow, APIs, scaling strategy, technology choices. It is evaluated at the system level. Low-Level Design covers detailed class and method design for a specific component: object model, class relationships, design patterns, code structure. They are evaluated in separate interview rounds. Senior engineers are expected to perform well in both; at the SDE-2 level, the emphasis on each varies by company.

**Q5: How do I handle a system design topic I am not familiar with?**

Be honest and transparent. If you are asked to design a recommendation system and have no experience with ML-based recommendations, say so: "I have limited direct experience with ML recommendation systems, so I'll focus on a content-based or collaborative filtering approach using the data signals available, and I'll note where an ML team would likely make different choices." Interviewers respect intellectual honesty far more than confident bluffing that falls apart under follow-up questions. The areas where you have genuine experience are where you will perform best; design around your strengths while being transparent about your gaps.

**Q6: What is the most common area where senior engineers fail system design interviews?**

Consistency and distributed transactions. Engineers with deep experience in a single codebase often have not needed to reason carefully about what happens when two services need to update their respective databases atomically, or what consistency guarantees are required for a specific access pattern. Study the Saga pattern, the transactional outbox pattern, and the different consistency models until you can discuss them fluently.

**Q7: How important is knowing specific technologies (Redis, Kafka, Cassandra) vs general concepts?**

Both matter, but in different ways. You need to know the capabilities, limitations, and trade-offs of the major building blocks (Redis, Kafka, PostgreSQL, Elasticsearch, Cassandra) well enough to make informed design choices. You do not need to know their internal implementation details or configuration options. The conceptual understanding (why Cassandra for time-series? why Kafka for event streaming?) is more important than operational knowledge of any specific technology.

**Q8: Can I use diagrams in a virtual interview?**

Yes, and you should. Most virtual system design interviews use a shared whiteboard tool (Excalidraw, Miro, Google Jamboard, or the interviewer's platform of choice). Practice drawing system diagrams in a digital whiteboard tool as part of your preparation. Diagrams that are organised, legibly labelled, and presented incrementally (draw each component as you discuss it, not all at once) are significantly more effective than sparse diagrams or purely verbal descriptions.

**Q9: How do I approach a system design problem I have never seen and have no idea how to start?**

Fall back to the framework. Even for unfamiliar domains, the structure is always the same: clarify requirements and scale, do capacity estimation, draw the high-level components, identify the hardest sub-problems, and go deep on those. If the domain is unfamiliar (designing a GPS navigation system, designing a collaborative code editor), ask questions about the access patterns and scale that clarify the technical challenges. "What does a write look like in this system? What does a read look like? What is the scale?" These questions almost always surface the core design challenge regardless of domain. You may not know the optimal architecture for a GPS routing system, but you can identify that real-time map data delivery to millions of concurrent users is a CDN and caching problem, and routing computation is a graph problem with pre-computed shortest paths.

**Q10: What is the difference between a system design interview at Google vs Amazon vs a mid-tier product company?**

The fundamental framework is the same everywhere, but the depth and focus vary. Google interviews tend to go deeper on fundamental computer science concepts - expect probing questions on consistency models, concurrency, and data structure choices. Amazon interviews evaluate the Leadership Principles behavioural component heavily alongside the technical design. Mid-tier product companies are more interested in whether you can design a system that solves their specific business problem reliably, with less emphasis on theoretical computer science depth. All three expect clear communication, structured thinking, and explicit trade-off discussion. Calibrate the depth of your technical discussion to the company and role level; over-engineering a design for a mid-tier company interview (proposing a distributed Raft consensus cluster for a problem that needs a simple primary-replica setup) can be just as penalised as under-engineering.

---

System design competency is built through a combination of conceptual study, practical pattern internalisation, and deliberate communication practice. The engineers who perform consistently well in system design interviews are not those who have memorised the most architectures - they are those who have developed genuine fluency with the underlying principles, practised the structured communication framework until it is natural, and can reason confidently about trade-offs in real time. The twelve walkthroughs in this guide are starting frameworks; extend each one, identify your gaps, and practise until the reasoning process feels as natural as the technical knowledge.

*All technology recommendations, tools, and platform references in this guide reflect general industry practice in distributed systems engineering. Specific tool capabilities and best practices evolve rapidly; always consult official documentation for the most current information before making architectural decisions.*
