---
layout: post
title: "Oracle BI Apps ODI integration with DRM - Single Child Multiple Parents Issue"
date: 2016-09-19
categories: ["Analytics"]
tags: ["Master Data Management", "Oracle Data Integrator"]
excerpt: "DRM hierarchy has a child with multiple parents and ODI is breaking? How to handle this common BI Apps integration issue with practical solutions."
image: "/assets/images/blog/blog-18.webp"
reading_time: 2
author: "david-thornton"
last_updated: 2026-03-29
---
The Oracle Business Intelligence Applications is a very useful product for many organizations and often Oracle Hyperion DRM is the master data management tool used for managing master data via integration through Oracle EBS.

So the master data flows from DRM --> EBS --> BI. But there is an interesting issue that crops up sometimes. The scenario is in the same hierarchy the same segment value can belong to multiple parents in DRM and EBS (which is logically incorrect, but technically feasible), but when such a scenario is integrated with BI Apps using ODI, the entire tree (say X is the duplicate member, and the two occurrences of X roll up to a common node Y, where Y may or may not be the top node of the hierarchy) will get deleted, and users will not be able to see any segment values appearing under that tree (i.e. under Y) since all those does not exist at all in the Dimension Hierarchy table.

![Oracle BI Apps ODI integration with DRM Single Child Multiple Parents Issue](/assets/images/blog/blog-18.webp)
Oracle BI Apps ODI integration with DRM Single Child Multiple Parents Issue

To handle this scenario as best as possible, I need to understand the flow how the hierarchy is maintained in BI Apps. The flow of the data is as below:

EBS -> DW.W_GL_SEGMENT_HIER_PS -> DW.W_GL_SEGMENT_DHS -> DW.W_GL_SEGMENT_DH

Here DW represents the BI data warehouse schema. The table W_GL_SEGMENT_HIER_PS is not of much use to me since all the required fields to capture the issue is not yet generated there. However, in W_GL_SEGMENT_DHS I am getting all the required fields to find the issue. The below query will help in capturing the error data (i.e. the value of X):

SELECT * FROM W_GL_SEGMENT_DHS DHS  
 WHERE  (INTEGRATION_ID, HIERARCHY_ID, HIERARCHY_VERSION, DATASOURCE_NUM_ID) IN  
 (SELECT DISTINCT INTEGRATION_ID, HIERARCHY_ID, HIERARCHY_VERSION, DATASOURCE_NUM_ID  FROM W_GL_SEGMENT_DHS GROUP BY   
 INTEGRATION_ID, HIERARCHY_ID, HIERARCHY_VERSION,DATASOURCE_NUM_ID HAVING COUNT (1) > 1);

The table W_GL_SEGMENT_DHS is truncated and loaded every time during the loading process. And the deletion of the erroneous tree (i.e. Y) happens at the end. So I need to capture the error record after the loading and before deletion happens in W_GL_SEGMENT_DHS.

I have two options for this:

    1. Modify the ODI load plan to add a new step before the deletion happens - this step will save the duplicated error data in some table or send out an email notification with that information

    2. Create a database trigger which will execute before any deletion happens on W_GL_SEGMENT_DHS - this step will save the duplicated error data in some table

This will help troubleshoot the hierarchy issues faster and subsequently discuss with the DRM team for any necessary action.