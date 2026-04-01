---
layout: post
title: "DRM EBS Integration Find Orphans in EBS"
date: 2016-09-26
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "Orphan values in EBS after DRM sync? How to identify disconnected segment records created during integration and clean them up properly."
image: "/assets/images/blog/blog-85.webp"
reading_time: 1
author: "park-jimin"
last_updated: 2026-03-29
---
The Oracle Data Relationship Management application is integrated with Oracle E-Business Suite via the Oracle integration kit. However, it is often observed during integration with different EBS environments that orphans are sometimes created in EBS. It gives rise to issues during reporting for the transactions for that specific orphan and so becomes necessary to track the orphans and keep them identified for troubleshooting purposes.

![Oracle DRM Hierarchy in EBS](/assets/images/blog/blog-85.webp)
Oracle DRM Hierarchy in EBS

**Related Post:** [DRM EBS Integration Load Segment Values and Hierarchies »](http://rahul-bhattacharya.blogspot.com/2016/09/load-segment-values-and-hierarchies-drm.html)

The below query when executed in the APPS schema will help identify the orphans for the different segments. The query essentially checks the segment values that exist in EBS excluding the segment values that are tagged with a parent segment value belonging to a hierarchy - thus finding out the orphan segment values.

```
SELECT FLEX_VALUE_SET_ID, FLEX_VALUE FROM APPS.FND_FLEX_VALUES_VL
WHERE FLEX_VALUE_SET_ID IN ('1014867')
MINUS
SELECT FLEX_VALUE_SET_ID, CHILD_FLEX_VALUE_LOW FROM APPS.FND_FLEX_VALUE_NORM_HIERARCHY
WHERE FLEX_VALUE_SET_ID IN ('1014867')
```

Here the value 1014867 represents one of the segment hierarchies, and multiple values can be used in the IN clause to check all the hierarchies; thus identifying all the orphans in EBS. Once the orphans are identified, they need to be re-configured in DRM and the DRM EBS integration need to be executed one more time to bring back the segment value within a hierarchy in EBS.
