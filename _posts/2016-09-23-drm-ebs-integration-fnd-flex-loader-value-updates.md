---
layout: post
title: "DRM EBS Integration Fnd Flex Loader Value Updates"
date: 2016-09-23
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "DRM to EBS segment value sync via Fnd Flex Loader: how the refresh works, what can go wrong, and how to fix value update failures."
image: "/assets/images/blog/blog-32.webp"
reading_time: 2
author: "Insight Crunch Team"
last_updated: 2026-03-29
---
The Oracle DRM to EBS integration is one of the most widely used programs to maintain and refresh master data easily. The EBS concurrent program pulls the data from DRM and **refreshes the existing values and hierarchies** with the new information. There's a specific list of attributes which demands constant special attention for every integration, they are as below:

- FLEX_VALUE_SET_NAME

- PARENT_FLEX_VALUE

- CHILD_FLEX_VALUE_LOW

- CHILD_FLEX_VALUE_HIGH

![Oracle DRM EBS Integration Fnd Flex Loader Value Updates](/assets/images/blog/blog-32.webp)
Oracle DRM EBS Integration Fnd Flex Loader Value Updates

**Once the integration is completed**, the values are expected to be showing up fine in EBS, more specifically in FND_FLEX_VALUES and FND_FLEX_VALUE_NORM_HIERARCHY. Any new values, hierarchy changes, description changes can be verified using these and few other FND tables under APPS or APPLSYS schemas.

Keep reading: [Load Segment Values and Hierarchies »](http://rahul-bhattacharya.blogspot.com/2016/09/load-segment-values-and-hierarchies-drm.html)

Understanding how the **data flows** from DRM to EBS is useful and helps troubleshooting various scenarios quickly. Once the concurrent program Load Segment Values and Hierarchies completes fine, the values are updated and inserted in FND_FLEX_VALUES, i.e. loading is done in upsert mode. The table FND_FLEX_VALUE_NORM_HIERARCHY is truncated and loaded for that specific segment, rest data stays as-is.

The below **diagram** will explain schematically how the data flows, focussed mainly on the hierarchy tables in EBS. The interface tables which are truncated and loaded are GL_DRM_SEGVALUES_INTERFACE and GL_DRM_HIERARCHY_INTERFACE in the GL schema. The FND tables in APPS or APPLSYS schemas are refreshed after that.


## DRM Integration User Guide

For all the details regarding the integration, please **Download** the Oracle Data Relationship Management Guide detailed documentation below. Subscribe to get access.

[s2If current_user_can(access_s2member_level1)]

[Download the Oracle Data Relationship Guide here](https://insightcrunch.com/wp-content/uploads/2022/09/Oracle-Data-Relationship-Management-User-Guide.pdf). You will get a complete understanding of how to proceed with the set-up and configurations of your environment. If you encounter any issues along the way, please feel free to leave a comment or message me.