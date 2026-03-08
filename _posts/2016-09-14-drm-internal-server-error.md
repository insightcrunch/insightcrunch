---
layout: post
title: "DRM Internal Server Error"
date: 2016-09-14
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "Oracle Data Relationship Management is a highly robust tool by Oracle with a 99.99% of uptime month over month and a largely satisfied user base. However, every few months we are expected to ..."
image: "/assets/images/technology-industry-analysis-insightcrunch.webp"
reading_time: 1
author: "Insight Crunch Team"
---

Oracle Data Relationship Management is a highly robust tool by Oracle with a 99.99% of uptime month over month and a largely satisfied user base. However, every few months we are expected to encounter some issues which can be defined as minor hiccups, nothing major. But it's good to have a knowledge base of quickly resolving such issues. Here are the details of one I dread the most and how to fix it.

**Issue:** After logging into DRM and selecting the Application, when I click Login, I get the below error message in Internet Explorer 8:

"The page cannot be displayed because an internal server error has occurred."

Everything looked fine, all services are up, restarting the application from DRM Configuration Console did not help.

**Solution:**

- Follow the below steps as mentioned:

- Go to DRM Configuration Console -> Click on Stop Services

- Go to Oracle EPM System -> epmsystem1 -> Foundation Services -> Click on Stop EPM System

- Go to Oracle EPM System -> epmsystem1 -> Foundation Services -> Click on Start EPM System

- Go to Configuration Console -> Click on Start Services

- Try to login to DRM as usual, it should work fine

If this did not resolve your issue, there's [another possible scenario here](http://www.insightcrunch.com/2016/09/drm-web-client-internal-server-error.html).

![DRM Internal Server Error](https://insightcrunch.com/wp-content/uploads/2016/09/pexels-photo-6592702.jpeg)
DRM Internal Server Error