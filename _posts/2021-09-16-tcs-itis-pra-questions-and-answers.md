---
layout: post
title: "TCS ITIS PRA Questions and Answers"
date: 2021-09-16
categories: ["Industry"]
tags: ["TCS"]
excerpt: "Preparing for TCS ITIS PRA? Real questions, topic coverage for infrastructure services, answer strategies, and the pass criteria for this assessment."
image: "/assets/images/blog/blog-03.webp"
reading_time: 35
author: "Insight Crunch Team"
last_updated: 2026-03-23
---
## Overview

The TCS Information Technology Infrastructure Services module is one of the most popular service industry modules today. The demand and criticality of maintaining IT infrastructures to effectively support IT services is increasing with every passing year, and the professionals who understand these foundations deeply are among the most consistently employed in the technology industry.

As someone who has been through the TCS ITIS pathway and worked extensively with infrastructure technologies, the goal of this article is to make sure you are aware of the key technologies, assessment patterns, and preparation strategies before you get onboard into a project. The TCS ITIS PRA full form is TCS ITIS Project Readiness Assessment Test. This is one of the most important internal assessments in the TCS fresher journey, and understanding it well before you sit it makes a significant difference to the outcome.

There is sufficient learning material available for you to upskill yourself before the PRA, and this article organises that material systematically. The passing criteria is typically kept around 80 percent, which means the exam is designed to ensure you have genuinely studied the domain before being deployed on a live client project. This is not a threshold to approach casually. You get 3 attempts to clear the TCS ITIS PRA exam, and while that might sound like enough cushion, using all three attempts adds stress and delay to your project deployment timeline that is entirely avoidable with proper preparation.

For those still working through the TCS recruitment process, the [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html) covers the entrance assessment comprehensively. For those who have joined TCS and are preparing for the ILP, the [TCS ILP Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-ilp-preparation-guide.html) provides structured guidance for that phase. And for the ITIS PRA specifically, this article is the most detailed preparation resource available here.

Read more: [TCS ITIS Detailed Analysis »](https://insightcrunch.com/2011/07/28/tcs-itis-detailed-analysis/)

![TCS ITIS PRA Questions and Answers](/assets/images/blog/blog-03.webp)
TCS ITIS PRA Questions and Answers

---

## Understanding the TCS ITIS PRA: What It Is and Why It Matters

Before diving into preparation content, it is worth establishing a clear picture of what the PRA actually is and where it sits in the broader TCS ITIS journey.

You take the TCS ITIS PRA after completing the TCS ILP (Initial Learning Programme). The ILP gives you the general technical and professional foundation. The PRA tests whether you are ready for the specific demands of an ITIS project. It is a project readiness gate, not just another routine assessment, and the name is precise: Project Readiness Assessment.

The reason TCS places an 80 percent passing threshold on the PRA, rather than the more forgiving 60 or 65 percent thresholds used in some other internal assessments, is that ITIS project work involves real client environments. A junior associate who does not understand basic networking, server management, security principles, or service management concepts creates risk for the client engagement. The PRA threshold is calibrated to ensure that only genuinely prepared associates are deployed.

**The three-attempt rule:** You have three attempts to clear the PRA. After three failures, the matter escalates to a formal performance review. This is not something anyone wants to experience. The sensible approach is to treat the first attempt as the one that matters and prepare accordingly, while understanding that one or two attempts are available as genuine safety nets rather than as a comfortable fallback plan.

**What happens if you clear the PRA:** You are cleared for project deployment in your allocated ITIS service line. The specific project you are deployed to depends on available openings, your stream, and your base branch location.

**What the PRA tests:** The exam tests domain-specific technical knowledge across the technologies relevant to your ITIS service line. The broad technology areas covered, which are discussed in depth throughout this article, include networking fundamentals, operating systems (Windows and Linux), database concepts, cloud basics, security principles, IT service management frameworks (particularly ITIL), monitoring and management tools, virtualisation, and scripting basics.

---

## TCS ITIS PRA Exam Pattern: Structure and Format

The TCS ITIS PRA questions come in a multiple-choice format for the primary objective sections. There are also hands-on or practical evaluation components in some versions of the PRA where you are assessed on your ability to write or interpret code, execute commands, or demonstrate platform-specific knowledge.

If you are preparing for the TCS ITIS PRA, you have already gone through the TCS ILP programme. You are familiar with the general exam simulation environment and how TCS conducts their assessments through the internal platforms. The PRA uses a similar interface, and the procedural aspects (timer management, question navigation, marking for review) should feel familiar.

**Multiple-choice sections:** The objective sections test conceptual knowledge and applied understanding across the technology domains covered in your ITIS track. Questions may ask you to identify the correct definition of a term, select the right command for a described task, choose the appropriate protocol for a described scenario, or identify the error in a described configuration. The questions are scenario-based in many cases: "Given this situation, what is the most appropriate action?" rather than purely definitional.

**Practical or hands-on sections:** These test your ability to actually work with the technologies rather than just describe them. In a networking context, this might mean selecting the correct sequence of commands to configure a described network scenario. In a scripting context, it might mean reading a Python or Bash script and predicting its output or identifying its error.

**Domain coverage:** The specific domains tested depend on your allocated ITIS service line. However, certain technology areas are foundational across all ITIS service lines and should be studied regardless of your specific assignment: networking, operating systems, database fundamentals, ITIL service management, and basic scripting. More specialised domains (cloud platforms, virtualisation tools, security frameworks, specific monitoring platforms) are weighted more heavily based on service line.

**Time allocation:** The PRA is timed, and the time per question is comparable to TCS's other internal assessments. Questions that take more than two to three minutes to resolve should be flagged for review and returned to after completing the rest of the section, rather than blocking progress through the test.

---

## Core Technology Domain 1: Networking Fundamentals

Networking is the single most universally relevant technology domain across all TCS ITIS service lines. Whether you are in Data Center Management, Converged Network Services, Managed Security, End-User Computing, or IT Service Management, you will encounter networking concepts daily. The PRA reflects this by including networking questions regardless of your specific service line.

### The OSI Model

The Open Systems Interconnection (OSI) model is the conceptual framework that describes how data communication works across a network in seven distinct layers. Every networking question you will ever encounter in any professional context can be mapped back to this model, and understanding it deeply rather than just memorising layer names is the foundation of real networking competence.

**Layer 1 - Physical:** The actual physical transmission medium. Cables (copper, fibre optic), radio waves (Wi-Fi), the electrical or optical signals carrying the data. Physical layer standards define things like connector types, cable specifications, and signal characteristics.

**Layer 2 - Data Link:** The layer responsible for reliable communication between directly connected nodes. Ethernet operates at Layer 2. MAC (Media Access Control) addresses identify devices at this layer. Switches operate at Layer 2, forwarding frames based on MAC address tables.

**Layer 3 - Network:** The layer responsible for routing data across multiple networks from source to destination. IP (Internet Protocol) operates at Layer 3. IP addresses identify devices and networks at this layer. Routers operate at Layer 3, forwarding packets based on routing tables and IP addresses.

**Layer 4 - Transport:** The layer responsible for end-to-end communication between applications, including segmentation, flow control, and error recovery. TCP (Transmission Control Protocol) and UDP (User Datagram Protocol) operate at Layer 4. TCP provides reliable, ordered delivery; UDP provides faster but unreliable delivery.

**Layer 5 - Session:** Manages the establishment, maintenance, and termination of sessions between applications. Less commonly tested in granular detail, but understanding that sessions are established, maintained, and torn down is important context for security and troubleshooting questions.

**Layer 6 - Presentation:** Handles data formatting, encryption, and compression. SSL/TLS encryption operates at this layer. Data conversion between different formats (ASCII to Unicode, for example) is a Layer 6 function.

**Layer 7 - Application:** The layer at which network services interact directly with end-user applications. HTTP, HTTPS, FTP, SMTP, DNS, DHCP all operate at Layer 7. When a user opens a web browser and loads a page, they are interacting with Layer 7 protocols.

**PRA-relevant OSI questions typically test:** Matching a described protocol to its correct OSI layer, identifying which layer a described problem is occurring at, understanding how a troubleshooting approach maps to layers (start at Layer 1 and work up, or top-down from Layer 7), and the difference between the OSI model and the simpler TCP/IP model (four layers: Network Access, Internet, Transport, Application).

### TCP/IP Protocols and Addressing

IP addressing is tested heavily in the PRA because it is practically applicable across every ITIS service line.

**IPv4 addressing:** A 32-bit address typically written in dotted decimal notation (e.g., 192.168.1.100). The address is divided into a network portion and a host portion by the subnet mask.

**Subnet masks and CIDR notation:** A subnet mask (e.g., 255.255.255.0) or CIDR notation (e.g., /24) defines how many bits of the IP address identify the network and how many identify individual hosts within that network. Being able to calculate the number of hosts in a subnet (/24 gives 254 usable host addresses, /25 gives 126, /26 gives 62, etc.) is a practical skill tested in the PRA.

**Private IP address ranges:** Memorise these:
- 10.0.0.0 to 10.255.255.255 (Class A private range)
- 172.16.0.0 to 172.31.255.255 (Class B private range)
- 192.168.0.0 to 192.168.255.255 (Class C private range)

**Key protocols to know in depth:**
- **DNS (Domain Name System, port 53):** Translates domain names to IP addresses. Understand the difference between authoritative and recursive DNS servers, and what a DNS cache does.
- **DHCP (Dynamic Host Configuration Protocol, port 67/68):** Automatically assigns IP addresses to devices on a network. Understand the DORA process (Discover, Offer, Request, Acknowledge).
- **HTTP (port 80) and HTTPS (port 443):** Web protocol and its encrypted version. Know the difference between HTTP and HTTPS and why HTTPS is the standard.
- **FTP (ports 20 and 21):** File Transfer Protocol. Know the difference between active and passive FTP modes.
- **SMTP (port 25), POP3 (port 110), IMAP (port 143):** Email protocols. SMTP sends mail; POP3 and IMAP retrieve it.
- **SSH (port 22):** Secure Shell, used for encrypted remote command-line access to Linux/Unix systems.
- **RDP (port 3389):** Remote Desktop Protocol, used for graphical remote access to Windows systems.
- **SNMP (port 161/162):** Simple Network Management Protocol, used by monitoring tools to collect performance data from network devices.
- **ICMP:** Internet Control Message Protocol, used by ping and traceroute for network diagnostics.

### Routing and Switching

**Routing protocols:** Dynamic routing protocols allow routers to automatically discover network paths and adapt to changes.
- **OSPF (Open Shortest Path First):** A link-state protocol used within a single organisation's network (interior gateway protocol). Finds the shortest path using Dijkstra's algorithm.
- **BGP (Border Gateway Protocol):** The protocol that makes the internet work. Routes traffic between different autonomous systems (large networks operated by ISPs, large companies, etc.).
- **EIGRP (Enhanced Interior Gateway Routing Protocol):** A Cisco-proprietary hybrid routing protocol used within enterprise networks.

**Switching concepts:**
- **VLANs (Virtual Local Area Networks):** Allow a single physical switch infrastructure to be logically segmented into multiple separate networks. Traffic between VLANs requires a Layer 3 device (router or Layer 3 switch). VLAN configuration and troubleshooting is a frequent PRA topic.
- **Spanning Tree Protocol (STP):** Prevents network loops in environments with redundant switch connections by blocking certain ports and creating a loop-free logical topology.
- **Trunk ports vs access ports:** Access ports carry traffic for a single VLAN; trunk ports carry traffic for multiple VLANs between switches, tagged using IEEE 802.1Q.

---

## Core Technology Domain 2: Operating Systems

Both Windows Server and Linux/Unix operating system environments are central to ITIS work, and the PRA tests practical knowledge of both.

### Linux Command Line

Linux is the dominant operating system for servers in enterprise environments globally. Most cloud workloads run on Linux. Most web servers run Linux. Most database servers in large enterprises run Linux. A working knowledge of the Linux command line is not optional for an ITIS professional.

**Essential commands to know fluently:**

**File system navigation:**
- `pwd` - print working directory (where am I?)
- `ls -la` - list all files including hidden, with long format details
- `cd /path/to/directory` - change directory
- `find /path -name "filename"` - search for files by name
- `locate filename` - faster file search using a prebuilt index

**File and directory operations:**
- `cp source destination` - copy file
- `mv source destination` - move or rename file
- `rm -rf directoryname` - remove directory and contents recursively (use with care)
- `mkdir -p path/to/new/directory` - create directory and any necessary parent directories
- `chmod 755 filename` - change file permissions (read/write/execute for owner, read/execute for group and others)
- `chown user:group filename` - change file ownership

**Viewing and editing files:**
- `cat filename` - display entire file contents
- `less filename` - view file contents page by page (press q to quit)
- `head -n 20 filename` - show first 20 lines
- `tail -n 20 filename` - show last 20 lines
- `tail -f filename` - follow a log file in real time as it grows (very useful for monitoring)
- `grep "search term" filename` - search for a pattern within a file
- `grep -r "search term" /path/` - recursive search across a directory

**System information and processes:**
- `top` or `htop` - real-time process monitoring (CPU, memory usage)
- `ps aux` - list all running processes
- `kill -9 PID` - forcefully terminate a process by its Process ID
- `df -h` - disk space usage in human-readable format
- `du -sh /path/` - size of a specific directory
- `free -m` - memory usage in megabytes
- `uname -a` - system information including kernel version
- `uptime` - how long the system has been running
- `who` or `w` - who is logged in

**Networking from Linux:**
- `ip addr` or `ifconfig` - show network interface configuration
- `ping hostname_or_ip` - test basic connectivity
- `traceroute hostname` (or `tracepath`) - trace the network path to a destination
- `netstat -tuln` or `ss -tuln` - show active network connections and listening ports
- `curl -I https://website.com` - retrieve HTTP headers from a URL
- `wget URL` - download a file from a URL
- `nslookup domain` or `dig domain` - DNS lookup

**Permissions model:** Linux file permissions use a three-tier model: owner, group, and others. Each tier can have read (r=4), write (w=2), and execute (x=1) permissions. The `chmod` command changes these, either in symbolic notation (`chmod u+x file`) or octal notation (`chmod 755 file`). The PRA frequently tests permission calculation: what does `chmod 644` mean? (Owner: read+write, Group: read only, Others: read only.)

**User and group management:**
- `useradd username` - create a new user
- `passwd username` - set password for a user
- `usermod -aG groupname username` - add user to a group
- `su - username` - switch to another user
- `sudo command` - execute command with superuser privileges

### Windows Server

Windows Server is the dominant OS in enterprise end-user computing environments and remains significant in data center environments, particularly for organisations running Microsoft application stacks.

**Key Windows Server concepts for the PRA:**

**Active Directory (AD):** The Microsoft directory service that manages users, computers, and resources within a Windows network. Understanding the hierarchy (Forest, Domain, Organizational Unit) and the role of Domain Controllers is essential. Key concepts: user accounts, group policies (GPOs), security groups (distribution vs security, local vs global vs universal).

**Windows Server Roles:** Windows Server roles are specific functions the server is configured to perform. Key roles to know: Active Directory Domain Services (AD DS), DNS Server, DHCP Server, File and Storage Services, Web Server (IIS), Remote Desktop Services.

**PowerShell:** Microsoft's command-line shell and scripting language. Basic PowerShell commands that appear in PRA context include:
- `Get-Process` - list running processes (equivalent to `ps` on Linux)
- `Stop-Process -Name "processname"` - stop a process
- `Get-Service` - list services and their status
- `Start-Service ServiceName` / `Stop-Service ServiceName` - manage services
- `Get-EventLog -LogName System -Newest 50` - view recent System event log entries
- `Test-Connection -ComputerName hostname` - equivalent to ping
- `Get-ChildItem` (alias `ls` or `dir`) - list directory contents
- `Set-ExecutionPolicy RemoteSigned` - allow PowerShell scripts to run

**Windows Event Viewer:** The primary tool for reviewing system logs, application logs, and security logs on Windows. Understanding the three primary log categories (Application, System, Security) and what types of events each records is standard PRA territory.

**Task Scheduler:** The Windows service for scheduling automated tasks. Understanding how to create, modify, and troubleshoot scheduled tasks is relevant to ITIS operations.

---

## Core Technology Domain 3: Database Fundamentals

SQL proficiency is relevant to a broader range of ITIS roles than most associates initially expect, and the PRA tests it accordingly.

### SQL Essentials

**Core SQL operations:**

```sql
-- Select all columns from a table
SELECT * FROM employees;

-- Select specific columns with a condition
SELECT employee_id, first_name, last_name, department
FROM employees
WHERE department = 'IT Infrastructure'
ORDER BY last_name ASC;

-- Count records
SELECT COUNT(*) FROM incidents WHERE status = 'Open';

-- Aggregate functions
SELECT department, AVG(salary) as avg_salary, MAX(salary) as max_salary
FROM employees
GROUP BY department
HAVING AVG(salary) > 50000;

-- INNER JOIN: returns only rows where there is a match in both tables
SELECT e.first_name, e.last_name, d.department_name
FROM employees e
INNER JOIN departments d ON e.department_id = d.department_id;

-- LEFT JOIN: returns all rows from the left table, 
-- with NULLs where there is no match in the right table
SELECT e.first_name, d.department_name
FROM employees e
LEFT JOIN departments d ON e.department_id = d.department_id;

-- Subquery
SELECT first_name, last_name
FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);

-- INSERT
INSERT INTO incidents (incident_id, description, priority, status)
VALUES (1001, 'Server unreachable', 'High', 'Open');

-- UPDATE
UPDATE incidents
SET status = 'Resolved', resolved_date = CURRENT_DATE
WHERE incident_id = 1001;

-- DELETE
DELETE FROM incidents
WHERE status = 'Closed' AND resolved_date < '2023-01-01';
```

**Key SQL concepts beyond basic syntax:**

**Indexes:** Database structures that speed up query execution by allowing the database engine to find rows without scanning the entire table. A primary key is automatically indexed. Creating indexes on frequently queried columns (particularly those used in WHERE clauses and JOIN conditions) is a standard DBA performance optimisation. The trade-off: indexes speed up reads but slow down writes (INSERT, UPDATE, DELETE) because the index must also be updated.

**Transactions:** A transaction is a group of SQL operations that are treated as a single unit. Either all operations succeed (COMMIT) or all are rolled back (ROLLBACK) if any operation fails. The ACID properties govern transaction behaviour: Atomicity (all or nothing), Consistency (the database remains in a valid state), Isolation (concurrent transactions do not interfere with each other), Durability (committed changes persist).

**Views:** A virtual table defined by a SQL query. Views simplify complex queries, provide an abstraction layer over the underlying tables, and can be used to restrict which data a user can see.

**Stored Procedures (PL/SQL):** Compiled SQL programs stored within the database and executed by name. PL/SQL (Oracle's procedural extension to SQL) adds programming constructs to SQL: variables, loops, conditional logic, exception handling. The PRA may include questions on reading simple PL/SQL blocks and predicting their output.

### Database Administration Basics

**Backup and recovery:** Understanding the difference between full backups (entire database), incremental backups (only changes since the last backup), and differential backups (all changes since the last full backup) is standard PRA content. Recovery Point Objective (RPO, how much data you can afford to lose) and Recovery Time Objective (RTO, how long recovery can take) are the business metrics that drive backup strategy decisions.

**Database performance monitoring:** Key metrics to track include query execution time, CPU and memory usage by the database process, disk I/O rates, lock wait times (indicating contention between concurrent transactions), and tablespace usage (ensuring you do not run out of storage).

---

## Core Technology Domain 4: Cloud Computing Fundamentals

Cloud is no longer a future consideration for ITIS professionals; it is the present reality of enterprise infrastructure. The PRA increasingly includes cloud-related questions even for service lines that are primarily focused on on-premises infrastructure.

### Service Models

**IaaS (Infrastructure as a Service):** The cloud provider supplies raw compute (virtual machines), storage, and networking. The customer is responsible for the operating system, middleware, applications, and data. AWS EC2, Azure Virtual Machines, and Google Compute Engine are IaaS examples.

**PaaS (Platform as a Service):** The cloud provider supplies the infrastructure and the platform (runtime, database engine, web server), leaving the customer responsible only for the application and data. AWS Elastic Beanstalk, Azure App Service, and Google App Engine are PaaS examples.

**SaaS (Software as a Service):** The cloud provider supplies the entire stack including the application. The customer simply uses the software. Microsoft 365, Salesforce, and Google Workspace are SaaS examples. Most end-users interact with SaaS without realising it.

### Deployment Models

**Public cloud:** Infrastructure owned and operated by a third-party provider (AWS, Azure, GCP), shared among multiple customers but logically separated. Most cost-efficient for variable workloads.

**Private cloud:** Cloud infrastructure dedicated to a single organisation, either hosted on-premises or by a third-party provider in a dedicated facility. More expensive than public cloud but allows more control and meets certain regulatory requirements.

**Hybrid cloud:** A combination of public and private cloud, connected and orchestrated together. Allows organisations to keep sensitive workloads on private infrastructure while using public cloud for variable or less sensitive workloads.

**Multi-cloud:** Using services from more than one public cloud provider simultaneously. Avoids vendor lock-in and allows workload placement based on each provider's specific strengths.

### Key Cloud Services to Know by Name

For AWS specifically (the most commonly referenced in PRA contexts):
- **EC2 (Elastic Compute Cloud):** Virtual machines.
- **S3 (Simple Storage Service):** Object storage. Bucket-based, accessible via URL.
- **VPC (Virtual Private Cloud):** Isolated network environment within AWS.
- **IAM (Identity and Access Management):** User and permission management within AWS.
- **CloudWatch:** AWS monitoring and logging service.
- **RDS (Relational Database Service):** Managed database service.
- **Lambda:** Serverless compute (code that runs without managing a server).

For Azure:
- **Azure VMs:** Virtual machines.
- **Azure Blob Storage:** Object storage equivalent to S3.
- **Azure Active Directory (Azure AD / Entra ID):** Cloud identity service that integrates with on-premises Active Directory.
- **Azure Monitor:** Monitoring and logging.
- **Azure SQL Database:** Managed SQL Server service.

---

## Core Technology Domain 4b: Monitoring and Management Tools

Monitoring is the nervous system of ITIS operations. Before anything else, monitoring tells you that a problem exists and, when configured well, tells you roughly what kind of problem it is before any human has investigated it. The PRA tests awareness of monitoring concepts and tools because ITIS associates interact with monitoring platforms from their very first week on a project.

### What ITIS Monitoring Covers

Enterprise infrastructure monitoring covers several distinct layers that map closely to the OSI model and the infrastructure stack:

**Network monitoring:** Tracks the availability and performance of network devices (routers, switches, firewalls, load balancers) and the connectivity between them. Metrics include interface utilisation (bandwidth consumption as a percentage of capacity), packet loss, latency, and device CPU and memory usage. SNMP (Simple Network Management Protocol) is the primary protocol used to collect data from network devices. SNMP traps are alerts sent from devices to monitoring systems when a threshold is crossed or an event occurs.

**Server monitoring:** Tracks the health and performance of physical and virtual servers. Key metrics: CPU utilisation (the percentage of available processing capacity in use), memory utilisation (RAM used vs total RAM), disk I/O (how fast data is being read from and written to storage), disk space (how full the file system is), and network throughput. On Linux, these metrics map directly to the command-line tools covered earlier: `top` for CPU and memory, `df` for disk space, `iostat` for disk I/O, `netstat` for network connections.

**Application monitoring:** Tracks the performance and availability of the applications running on the infrastructure. Response time (how long the application takes to process a request), error rates (what percentage of requests result in an error), throughput (how many requests per second the application handles), and transaction success rates are the key application performance metrics.

**Log monitoring:** Aggregates log data from servers, applications, and network devices and applies pattern detection to identify anomalies. A spike in failed login attempts in the authentication log, an application suddenly generating a high rate of ERROR entries, or a database experiencing an unusual number of timeouts are examples of issues that log monitoring is designed to catch before they become visible to users.

**End-to-end availability monitoring:** Simulates user transactions or network connections from external points to verify that the service is accessible and performing within specification from a user perspective, not just from within the infrastructure.

### Common Monitoring Platforms

**Nagios / Nagios XI:** One of the oldest and most widely deployed open-source monitoring platforms. Nagios uses a plugin-based architecture where each check (can I ping this server? is the CPU above 80%? is the disk above 90% full?) is a separate plugin that can be configured with thresholds. When a threshold is crossed, Nagios generates an alert and changes the state of the monitored object from OK to WARNING or CRITICAL.

**Zabbix:** An open-source monitoring platform with more built-in functionality than Nagios, including native support for SNMP, IPMI, JMX monitoring, and a built-in graphing interface. Widely used in enterprise ITIS environments.

**SolarWinds NPM (Network Performance Monitor):** A commercial network monitoring platform with strong SNMP integration, topology mapping, and deep drill-down into network device performance. Very common in large enterprise data centers and managed services environments.

**Dynatrace and AppDynamics:** Application Performance Monitoring (APM) platforms that provide deep visibility into application behaviour, transaction traces, and code-level performance analysis. More relevant to application support service lines but increasingly present in ITIS environments as infrastructure and application monitoring converge.

**Splunk:** A platform for aggregating, searching, and analysing machine-generated log data from across an infrastructure. Splunk's query language (SPL, Splunk Processing Language) allows analysts to search across billions of log events, create dashboards, set alerts, and identify patterns that would be invisible to manual log review. Splunk is used heavily in both operations and security monitoring contexts.

**ServiceNow (ITSM):** While primarily an IT Service Management platform (ticketing, change management, CMDB), ServiceNow increasingly integrates with monitoring platforms to automatically generate incident tickets when alerts fire. Understanding the relationship between monitoring alerts and ITSM tickets is practical daily-operations knowledge.

### Alert Fatigue and Threshold Management

A monitoring system that generates too many alerts trains operators to ignore alerts, which defeats the entire purpose of monitoring. **Alert fatigue** is a well-documented problem in ITIS operations where the volume of non-critical alerts degrades the team's ability to respond effectively to genuinely critical ones.

Good threshold management involves setting meaningful thresholds based on baseline behaviour (what is normal for this specific server or service?) rather than generic defaults, suppressing alerts during scheduled maintenance windows, and building alert suppression rules that prevent a single root cause (one router failure) from generating hundreds of downstream alerts for all the services that depend on that router.

The PRA may include scenario questions where you are asked to identify the appropriate response to an alert condition, or to identify which monitoring data point would most clearly indicate a specific type of problem.

---

## Core Technology Domain 5: IT Service Management (ITIL)

ITIL (Information Technology Infrastructure Library) is the global framework for IT service management, and it is directly embedded in how TCS ITIS service lines are structured and measured. The PRA tests ITIL concepts because ITIS associates are expected to understand the professional framework within which their operational work sits.

### ITIL Core Processes

**Incident Management:** The process for restoring normal service operation as quickly as possible after an unplanned interruption. Key distinctions: an incident is any unplanned disruption to a service or degradation of service quality. Resolution does not require identifying the root cause; it only requires restoring service. The difference between incident management (restore service) and problem management (find root cause) is one of the most frequently tested ITIL distinctions.

**Problem Management:** The process for identifying and addressing the root causes of recurring incidents. A problem is the underlying cause of one or more incidents. Problem management aims to eliminate the root cause permanently rather than applying workarounds repeatedly. A Known Error is a problem for which a root cause has been identified and a workaround or fix is available.

**Change Management:** The process for controlling changes to the IT environment to minimise the risk of service disruption. All changes should be categorised (Standard change: low-risk, pre-approved; Normal change: requires full change management review; Emergency change: expedited process for urgent changes), documented, reviewed, approved, and implemented with a rollback plan. The Change Advisory Board (CAB) reviews and approves normal changes.

**Service Request Management:** Handles routine requests from users for standard services or information that are pre-approved and low-risk. Ordering a new laptop, requesting access to a shared folder, resetting a password. These are not incidents (nothing is broken) and not changes in the traditional sense.

**Configuration Management:** Maintains a Configuration Management Database (CMDB) that records all Configuration Items (CIs) within the IT environment: servers, network devices, software licences, relationships between components, and ownership. Accurate configuration management is foundational to effective incident, problem, and change management.

**Release Management:** Controls the planning, scheduling, and execution of software releases and infrastructure updates into the production environment. Works closely with change management.

**SLAs, OLAs, and UCs:** Service Level Agreements (SLAs) are contracts between the service provider and the customer defining expected service levels. Operational Level Agreements (OLAs) define expected service levels between internal teams supporting each other. Underpinning Contracts (UCs) are agreements with external vendors. Understanding the hierarchy (SLA is met by the combination of OLAs and UCs) is standard PRA content.

**ITIL Service Lifecycle:** The five stages of the ITIL service lifecycle are Service Strategy, Service Design, Service Transition, Service Operation, and Continual Service Improvement. The PRA may ask which processes belong to which lifecycle stage.

---

## Core Technology Domain 6: Cybersecurity Fundamentals

Managed Security Services is one of the TCS ITIS service lines, but security concepts are relevant across all service lines. Every ITIS associate is expected to understand and apply basic security principles.

### CIA Triad

The fundamental framework of information security is the CIA triad: **Confidentiality** (only authorised users can access information), **Integrity** (information is accurate and has not been improperly modified), and **Availability** (information and systems are accessible when needed). Every security control, policy, and tool can be evaluated in terms of which aspects of the CIA triad it protects.

### Common Attack Types

**Phishing:** Social engineering attacks that trick users into revealing credentials or installing malware through deceptive emails, websites, or messages. Spear phishing targets specific individuals with personalised content. Whaling targets senior executives.

**DoS and DDoS (Denial of Service / Distributed DoS):** Attacks that overwhelm a system or network with traffic to make it unavailable. DDoS uses multiple compromised systems simultaneously. Protection involves traffic filtering, rate limiting, and DDoS mitigation services.

**Man-in-the-Middle (MitM):** An attacker intercepts communications between two parties, potentially reading or modifying the traffic without either party being aware. HTTPS/TLS encryption defends against MitM for web communications.

**SQL Injection:** An attack where malicious SQL code is inserted into an application's input fields, causing the database to execute unintended commands. Parameterised queries and input validation are the primary defences.

**Ransomware:** Malware that encrypts the victim's data and demands payment for the decryption key. Defence relies on regular, tested backups kept offline (air-gapped), endpoint protection, network segmentation, and user education.

**Privilege Escalation:** An attacker who gains limited initial access attempts to obtain higher-level privileges (administrator or root access) to extend their reach within the system. Principle of least privilege (giving accounts only the minimum permissions required) is the primary defence.

### Security Controls and Frameworks

**Principle of Least Privilege:** Every user, service, and application should have only the minimum permissions required to perform its function. No more.

**Defence in Depth:** Security is layered so that if one control fails, others remain in place. Physical security, network security, endpoint security, application security, and data security are all separate layers.

**Patch Management:** Keeping software and operating systems updated with security patches is one of the most effective security controls available. Most major breaches exploit known vulnerabilities for which patches have been available.

**Firewalls:** Network security devices that monitor and filter traffic based on rules. Stateful firewalls track the state of connections and make decisions based on connection context. Next-Generation Firewalls (NGFW) add application awareness and intrusion prevention.

**IDS/IPS:** Intrusion Detection Systems (IDS) monitor network traffic for suspicious patterns and generate alerts. Intrusion Prevention Systems (IPS) can automatically block detected attacks. The distinction between detection (passive) and prevention (active) is frequently tested.

**Encryption types:** Symmetric encryption uses the same key for encryption and decryption (AES is the standard symmetric algorithm). Asymmetric encryption uses a public/private key pair (RSA is the standard asymmetric algorithm). TLS/SSL certificates for HTTPS use asymmetric encryption to exchange a symmetric key, which is then used for the actual data transfer.

---

## Core Technology Domain 6b: Storage Fundamentals

Storage is a foundational topic for ITIS data center and cloud service lines. The PRA includes storage-related questions, and operational work in those service lines requires confident working knowledge of storage concepts.

### Storage Types

**DAS (Direct Attached Storage):** Storage physically connected to a single server, typically via SATA, SAS, or NVMe interfaces. Fast and low-latency but not shareable between multiple servers. Local hard drives and SSDs in servers are DAS.

**NAS (Network Attached Storage):** A dedicated storage device connected to the network and accessible by multiple servers and clients over file-sharing protocols (NFS for Linux/Unix, SMB/CIFS for Windows). NAS is used for shared file storage, backups, and archive purposes. Suitable for unstructured data (files, documents, media).

**SAN (Storage Area Network):** A dedicated high-speed network providing block-level storage access from shared storage arrays to servers. Unlike NAS, which presents file systems, a SAN presents raw block devices that the server formats and manages as if they were locally attached disks. SANs use Fibre Channel (FC) or iSCSI protocols. SANs are used for high-performance databases and enterprise applications that require fast, consistent storage access.

**Object Storage:** A storage architecture that stores data as objects (each object contains the data, metadata, and a unique identifier) rather than files in a hierarchy or blocks on a device. Amazon S3 is the most widely known object storage service. Object storage scales to enormous capacities and is ideal for unstructured data at scale (backups, archives, media files, log data), but is not suitable for applications that require low-latency random access.

### RAID Levels

RAID (Redundant Array of Independent Disks) is a technology that combines multiple physical disks into a logical unit to improve performance, redundancy, or both. RAID levels are frequently tested in the PRA.

**RAID 0 (Striping):** Data is split across multiple disks simultaneously, improving read and write performance. No redundancy: if any disk fails, all data is lost. Used only when performance matters more than data safety.

**RAID 1 (Mirroring):** Data is written identically to two or more disks simultaneously. If one disk fails, the other contains a complete copy. Usable capacity is 50 percent of total disk capacity. Read performance is improved; write performance is similar to a single disk.

**RAID 5 (Striping with distributed parity):** Data is striped across three or more disks, with parity information distributed across all disks. Can survive the failure of any single disk: the lost data can be reconstructed from the parity information on the remaining disks. Provides a balance of performance, redundancy, and usable capacity.

**RAID 6 (Striping with double distributed parity):** Similar to RAID 5 but with two sets of parity, allowing it to survive the simultaneous failure of any two disks. Requires a minimum of four disks.

**RAID 10 (1+0, Mirroring and Striping):** A combination of RAID 1 and RAID 0. Data is mirrored in pairs, and the mirrored pairs are striped. Requires a minimum of four disks. Provides both the redundancy of RAID 1 and the performance of RAID 0. Used for high-performance databases. Expensive in terms of usable capacity (50 percent of total).

The PRA will test your ability to identify which RAID level is appropriate for a described scenario and to identify the consequences of a disk failure in each configuration.

---

## Core Technology Domain 7: Scripting and Automation

The PRA tests basic scripting ability because ITIS operations increasingly depend on automation, and associates who can read, write, and debug basic scripts are significantly more effective than those who cannot.

### Python Basics for ITIS

Python is the most relevant scripting language for ITIS work given its readability, extensive library support, and cross-platform applicability. The PRA may include Python-related questions in the practical sections.

```python
# Variables and basic data types
server_name = "web-server-01"
port_number = 443
is_active = True

# Lists (ordered, mutable)
active_servers = ["web-01", "web-02", "db-01", "db-02"]
print(len(active_servers))        # 4
print(active_servers[0])          # web-01
active_servers.append("cache-01") # adds to end

# Dictionaries (key-value pairs)
server_config = {
    "hostname": "web-server-01",
    "ip": "192.168.1.10",
    "os": "Ubuntu 22.04",
    "cpu_cores": 8,
    "ram_gb": 32
}
print(server_config["ip"])        # 192.168.1.10

# Conditional statements
cpu_usage = 87
if cpu_usage > 90:
    print("CRITICAL: CPU threshold exceeded")
elif cpu_usage > 75:
    print("WARNING: CPU usage is high")
else:
    print("OK: CPU usage is normal")

# For loop
for server in active_servers:
    print(f"Checking connectivity to {server}...")

# While loop
retry_count = 0
max_retries = 3
while retry_count < max_retries:
    print(f"Attempt {retry_count + 1} of {max_retries}")
    retry_count += 1

# Functions
def check_port_open(host, port):
    """Check if a TCP port is open on a given host."""
    import socket
    try:
        sock = socket.create_connection((host, port), timeout=3)
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError):
        return False

# Reading a file (log file analysis example)
with open("/var/log/syslog", "r") as log_file:
    for line in log_file:
        if "ERROR" in line:
            print(line.strip())

# Exception handling
try:
    result = 100 / 0
except ZeroDivisionError as e:
    print(f"Error: {e}")
finally:
    print("This always executes")
```

### Bash Scripting Basics for ITIS

Bash is the default scripting environment on Linux servers and is used heavily in ITIS operations for automating routine tasks, monitoring checks, and batch operations.

```bash
#!/bin/bash
# Basic Bash script structure

# Variables
SERVER="192.168.1.100"
LOG_FILE="/var/log/health_check.log"

# Check if a service is running
SERVICE="nginx"
if systemctl is-active --quiet $SERVICE; then
    echo "$SERVICE is running" >> $LOG_FILE
else
    echo "WARNING: $SERVICE is not running. Attempting restart..." >> $LOG_FILE
    systemctl restart $SERVICE
fi

# Loop through a list of servers
SERVERS=("web-01" "web-02" "db-01")
for SERVER in "${SERVERS[@]}"; do
    if ping -c 1 -W 2 $SERVER > /dev/null 2>&1; then
        echo "$SERVER: REACHABLE"
    else
        echo "$SERVER: UNREACHABLE - Alert sent"
    fi
done

# Disk usage check
THRESHOLD=80
USAGE=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
if [ $USAGE -gt $THRESHOLD ]; then
    echo "ALERT: Root filesystem at ${USAGE}% capacity"
fi

# Reading and processing log files
grep "FAILED" /var/log/auth.log | tail -20
```

---

## Core Technology Domain 8: Virtualisation

Virtualisation is fundamental to modern enterprise infrastructure, and ITIS associates working in data center management, cloud, or end-user computing will encounter it constantly.

### Hypervisors

A hypervisor is software that creates and manages virtual machines on a physical host. The host's physical CPU, memory, and storage are shared among the virtual machines running on it.

**Type 1 Hypervisors (Bare-metal):** Run directly on the hardware without a host operating system. More efficient and used in production enterprise and data center environments. Examples: VMware vSphere/ESXi, Microsoft Hyper-V (when installed directly on hardware), KVM (Kernel-based Virtual Machine, built into Linux).

**Type 2 Hypervisors (Hosted):** Run on top of an existing operating system. Less efficient but convenient for development and testing. Examples: VMware Workstation, Oracle VirtualBox.

### VMware vSphere: The Industry Standard

VMware vSphere is the dominant virtualisation platform in enterprise data centers globally. ITIS PRA questions on virtualisation are heavily weighted toward VMware.

**ESXi:** The VMware Type 1 hypervisor that runs directly on the physical server. Multiple virtual machines run on each ESXi host.

**vCenter Server:** The centralised management platform for multiple ESXi hosts and their virtual machines. vCenter provides a single console from which you can manage an entire virtualised data center.

**vSphere Client:** The web-based interface for connecting to and managing vCenter Server.

**Key VMware concepts:**

**VM Snapshots:** A snapshot captures the state of a virtual machine at a specific point in time. You can revert to a snapshot if a change causes problems. Snapshots are not backups; they are intended for short-term use and degrade VM performance if retained for extended periods.

**vMotion:** Allows a running virtual machine to be migrated from one ESXi host to another with no downtime. Storage vMotion migrates the VM's storage between datastores while it is running.

**High Availability (HA):** A vSphere feature that automatically restarts virtual machines on other hosts in the cluster if the host they are running on fails.

**Distributed Resource Scheduler (DRS):** Automatically balances workloads across hosts in a cluster by migrating VMs using vMotion based on current resource utilisation.

**Datastores:** The storage repositories where virtual machine files are kept. Can be backed by local storage, SAN (Storage Area Network), or NAS (Network-Attached Storage).

### Containers and Docker

Containers are increasingly relevant to ITIS work, particularly as organisations modernise their infrastructure. The PRA may include basic container questions.

**The difference between VMs and containers:** Virtual machines virtualise the entire hardware stack and run a complete operating system. Containers virtualise at the operating system level, sharing the host OS kernel and isolating only the application and its dependencies. Containers are smaller, start faster, and use fewer resources than VMs, but offer less isolation.

**Docker basics:**
- A Docker **image** is a read-only template for creating containers.
- A Docker **container** is a running instance of an image.
- A **Dockerfile** defines how to build an image.
- `docker pull imagename` - download an image
- `docker run -d -p 80:80 nginx` - run a container in detached mode, mapping host port 80 to container port 80
- `docker ps` - list running containers
- `docker stop containername` - stop a container
- `docker logs containername` - view container logs

---

## Preparing for the PRA: A Structured Study Plan

If you are preparing for the TCS ITIS PRA, you have already gone through the TCS ILP programme. You understand how TCS conducts their tests. Now the goal is to prepare specifically on your allocated technologies, and the following plan provides a structured approach.

### Week 1: Foundation Assessment and Networking

**Day 1-2:** Take a diagnostic self-assessment. Go through the domain list above and honestly rate your confidence level in each area. This identifies where to focus preparation time.

**Day 3-5:** Networking foundations. Study the OSI model, IP addressing, subnetting, and the key protocol list. Practice subnetting calculations until they are automatic. Write out the port numbers for all major protocols from memory until you have them.

**Day 6-7:** Routing and switching. VLANs, STP, OSPF vs BGP distinctions, basic Cisco IOS command syntax.

### Week 2: Operating Systems

**Day 1-3:** Linux command line. Go through the command reference above and actually run each command in a Linux terminal (use a free Ubuntu VM on VirtualBox or a free cloud tier instance if you do not have a Linux machine). Reading about commands is categorically less effective than using them.

**Day 4-5:** Linux permissions, user management, and process management. The `chmod` permission system deserves specific drilling.

**Day 6-7:** Windows Server concepts. Active Directory hierarchy, Group Policy basics, PowerShell fundamental commands, Event Viewer logs.

### Week 3: Database, Cloud, and ITIL

**Day 1-2:** SQL. Practice writing SELECT, JOIN, aggregate, and subquery statements. Focus on JOIN types (INNER, LEFT, RIGHT, FULL OUTER) and when each is appropriate.

**Day 3:** Cloud service models (IaaS, PaaS, SaaS) and deployment models. Key AWS and Azure service names.

**Day 4-5:** ITIL. This is one of the most reliably tested domains in the PRA. Go through every process named in this article and understand the purpose, the key roles, and the distinguishing characteristics of each.

**Day 6-7:** Security fundamentals. CIA triad, common attack types, key controls (firewalls, IDS/IPS, encryption types, patch management, principle of least privilege).

### Week 4: Scripting, Virtualisation, and Mock Practice

**Day 1-2:** Python basics. Write the scripts above yourself (do not just read them), run them, modify them. Understanding comes from doing.

**Day 3:** Bash scripting fundamentals for Linux operations.

**Day 4-5:** Virtualisation. VMware concepts, hypervisor types, Docker basics.

**Day 6-7:** Full mock practice across all domains. Review every incorrect answer in detail. In the final two days, do light review of your weakest areas and confirm exam logistics.

---

## On the Day of the PRA: Exam Strategy

**Read questions carefully before selecting answers.** Many PRA questions contain specific qualifier words (always, never, first, best, most appropriate) that change the correct answer. A question asking for the "first" step in a process has a different correct answer from one asking for any step in the process.

**For scenario-based questions:** Identify what the core problem is before evaluating the options. Eliminate clearly wrong options first, then choose between the remaining ones based on the specific context of the scenario. ITIL-based scenarios often test whether you choose the right process (incident management vs problem management vs change management) for the described situation.

**For networking calculations:** Subnetting questions have definitive right answers that you either get or miss. If you have practiced subnetting calculation to fluency, these are reliable scoring opportunities. If you have not, they become time-consuming guesses. Invest the practice time to make subnetting automatic.

**Time management:** Flag any question that takes more than two minutes without resolution and move on. Return to flagged questions with remaining time rather than spending five minutes on a single difficult question while leaving several easy ones unattempted.

**The 80 percent threshold:** This means you can get up to 20 percent of questions wrong and still pass. Understanding which domains you are strongest in helps you ensure you capture full marks in your strong areas rather than spending excessive time in areas of genuine weakness.

---

## After the PRA: What Project Deployment Looks Like

Clearing the PRA is the gate to project deployment. Once cleared, the transition into live project work begins.

**The ramp-up period:** Every project has a client environment with its own specific configuration, history, tooling, and processes. The first month on a project is primarily about learning this specific environment rather than demonstrating all your technical knowledge immediately. Ask questions freely, read the documentation and run-books available on the project, shadow experienced team members, and take notes. The associates who ramp up fastest are those who ask the most targeted questions rather than those who try to figure everything out independently.

**ITSM tools in practice:** Your first interaction with ITIL concepts will likely be through the ServiceNow or equivalent ticketing platform used on the project. The incident management, change management, and service request processes you studied for the PRA will be immediately visible in how work is organised and tracked. This transition from abstract concepts to live operational tools is one of the satisfying moments of early ITIS career development.

**Certification planning:** Once deployed, begin planning your first professional certification. For ITIS associates, ITIL Foundation is the most universally recommended starting point. CompTIA Network+ or Cisco CCNA are appropriate next certifications depending on your service line. AWS Cloud Practitioner or Azure Fundamentals are relevant for any service line given the direction of infrastructure investment. Having a certification plan and making regular progress on it from early in your career creates a compounding career development effect that is much harder to build from a standing start later.

---
