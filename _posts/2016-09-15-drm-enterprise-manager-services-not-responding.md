---
layout: post
title: "DRM Enterprise Manager services not responding"
date: 2016-09-15
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "Weblogic services down for Oracle DRM? How to check, restart, and fix the Enterprise Manager services that enable DRM-to-EBS integration."
image: "/assets/images/blog/blog-01.webp"
reading_time: 1
author: "gregory-marsh"
last_updated: 2026-03-29
---
The Weblogic services essential for the Oracle DRM integration to work with Oracle GL is pretty stable and does not require any intervention for months once setup successfully.

However, in case we start getting the error message that the EM page cannot be displayed, then we need to make sure the below services are up.

Follow the below steps:

- Go to Oracle Weblogic --> User Projects --> EPMSystem

- Click on 'Start Admin Server for Weblogic'

![Start Weblogic Server](/assets/images/blog/blog-01.webp)
Start Weblogic Server
