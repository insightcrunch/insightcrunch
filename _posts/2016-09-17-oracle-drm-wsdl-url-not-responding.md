---
layout: post
title: "Oracle DRM WSDL URL not responding"
date: 2016-09-17
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "Oracle DRM WSDL URL not responding: APIAdapter and DrmService endpoints failing. Required for GL integration. Diagnosis and resolution steps."
image: "/assets/images/blog/blog-15.webp"
reading_time: 1
author: "Insight Crunch Team"
last_updated: 2026-03-23
---
The WSDL response pretty much goes often unnoticed in DRM until we try to use it in some way like the GL integration. The APIAdapter?wsdl and the oracle-epm-drm-webservices/DrmService?wsdl services usually load fine when the services are up. But I started getting the page cannot be displayed errors one day.

![Oracle DRM WSDL URL not responding](/assets/images/blog/blog-15.webp)
Oracle DRM WSDL URL not responding

We need to follow a set of steps to make sure the services are up again, including taking a backup of and then deleting a lok file, as shared below:

1. Go to Services  
Stop Oracle Hyperion EPM Server - Java Web Application (epmsystem1)

2. Go to:  
C:\Oracle\Middleware\user_projects\domains\EPMSystem\servers\EPMServer0\tmp  
Delete:  
EPMServer0.lok

3. Go to Services  
Stop Oracle DRM Server Processes

4. Go to Services  
Start Oracle Hyperion EPM Server - Java Web Application (epmsystem1)

5. Go to Services  
Start Oracle DRM Server Processes

6. Start EPM System (under Foundation Services)

7. Start Admin Server for Weblogic Server (under Oracle Weblogic -> User Projects -> EPMSystem)

Once this is done, try visiting the WSDL URL again, and it should be running fine.