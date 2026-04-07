---
layout: post
title: "DRM Web Client HTTP 503 Error"
date: 2016-09-17
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "One of the DRM servers was idle for a long time and one day I decided to start using it. After ensuring the usual things of the application services..."
image: "/assets/images/blog/blog-15.webp"
reading_time: 1
author: "ian-fletcher"
last_updated: 2026-04-01
lang: en
---
One of the DRM servers was idle for a long time and one day I decided to start using it. After ensuring the usual things of the application services running, the application itself started and the database responding fine, it was time to login to the DRM web client. But unfortunately I was shown the below error message, which did not appear to something often encountered:

     "HTTP 503 Error"

There cannot be a more dreadful error than the Web Client not responding when all the different parts of the application seem to be working fine. Also it was a not a firewall or Weblogic issue since those were tested to be working fine.

![DRM Web Client HTTP 503 Error](/assets/images/blog/blog-15.webp)
DRM Web Client HTTP 503 Error

On further investigation it was found in the Internet Information Services (IIS) for Windows Server the connection drm_pool was in Stopped state. On starting it back the Web Client started responding fine.