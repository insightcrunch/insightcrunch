---
layout: post
title: "EBS DRM Integration for Account Type and Summary Flag attributes"
date: 2016-09-18
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "The DRM to EBS integration using the patches 10632813 and 11659733 are not one of the as flexible integration concurrent program as it may appear, apparently. It is though true that the set-up ..."
image: "/assets/images/technology-industry-analysis-insightcrunch.webp"
reading_time: 2
author: "Insight Crunch Team"
---

The DRM to EBS integration using the patches 10632813 and 11659733 are not one of the as flexible integration concurrent program as it may appear, apparently. It is though true that the set-up appears straightforward, configure the patches for the program 'Load Segment Values and Hierarchies', and then configure DRM for the corresponding segment value names. With the 'Allow Export' version property set to True, all the hierarchies within that version for that segment is expected to flow to EBS.

All the different properties like Segment Value Code, Description, Account Type, Allow Posting, Allow Budgeting, Summary Flag etc are going to flow to EBS from DRM. However, there is a special consideration in place for **Account Type and Summary Flag**.

![Oracle EBS DRM Integration for Account Type and Summary Flag attributes](/assets/images/technology-industry-analysis-insightcrunch.webp)
Oracle EBS DRM Integration for Account Type and Summary Flag attributes

The attributes Account Type and Summary Flag **can only be set one-time** for each Segment Value. **Account Type cannot be null** in DRM. Once it is set up, this value cannot be updated from DRM anymore. If absolutely required to be changed, it needs to be manually updated in EBS and DRM and only after that the integration program will succeed. Else the program will fail with the error that it needs the Account Type and Summary Flag value needs to be updated for that node. This scenario is faced usually in fast-paced development projects and usually happens rarely.

**Errors** faced in such cases are as below:

*The value for Summary Flag cannot be updated. Please reset it to its original value.*

*The value for Account Type cannot be updated. Please reset it to its original value.*

> 

In each of the above cases, the exact flex value for which the error has appeared will be mentioned in the logs.