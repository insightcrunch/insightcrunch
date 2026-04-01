---
layout: post
title: "3 Essential Sanity Checks for DRM EBS Integration"
date: 2016-09-18
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "Avoid DRM-EBS integration failures. Three essential pre-checks on configuration, connectivity, and data that save hours of troubleshooting."
image: "/assets/images/blog/blog-01.webp"
reading_time: 1
author: "christopher-wells"
last_updated: 2026-03-29
---
The integration between Oracle's amazing master data management tool DRM and Oracle EBS is a pretty stable process given the configurations and pre-requisites have been taken care fine. But sometimes the concurrent program gives authentication error or invalid credentials error which can be an exhausting process to debug.

![3 Essential Sanity Checks for DRM EBS Integration](/assets/images/blog/blog-01.webp)
3 Essential Sanity Checks for DRM EBS Integration

So we'll focus on the 3 most important places to make sure the setup is fine. This sanity check is to make sure the setup is as expected when using SSO with Mixed Mode Authentication Enabled. Let's say the name of the user is *EBSIntegrationUser*.

1. The **user should be present in Weblogic Administration Server Console** (port 7001 usually) in the below path:

        Home -> Summary of Security Realms -> myrealm -> Users and Groups -> EBSIntegrationUser

2. Let's say the name of the pool created in the Authentication side is called XYZ. The **user should be present in Workspace** (port 9000 usually) in the below path:

        Shared Services -> User Directories -> XYZ -> Users

Search by the value EbsIntegrationUser in the field 'User Filter', the user should be present.

3. Finally **in DRM Web Client, the EbsIntegrationUser user should be present** in the below path. The user must be set as **CSS (External)** in the DRM System.

        Administer -> Users

Once the user is present all the three places, the integration should be working perfectly fine without any hiccups.