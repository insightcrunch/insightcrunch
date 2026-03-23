---
layout: post
title: "DRM Essbase Integration to refresh outline"
date: 2016-10-03
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "Oracle DRM to Essbase integration: refresh cube outlines from DRM hierarchy data. Configuration, export process, and troubleshooting outline updates."
image: "/assets/images/blog/blog-01.webp"
reading_time: 2
author: "Insight Crunch Team"
last_updated: 2026-03-23
---
The Oracle Data Relationship Management application has been consistently the leading master data management utility for businesses over the years. The flexibility of this application to easily integrate with other systems has been one of the best features. DRM integration with Hyperion Essbase to refresh the Essbase cubes outline can be accomplished in a variety of ways to update the metadata.

## Approach using ODI

Let's say I have an Account hierarchy in DRM. I have a Hyperion Planning application that has the Account dimension and relies on DRM to get the latest metadata. To start with, there is a **list of properties** that needs to be present already in DRM and values set accordingly - these are the properties that Essbase will require in the next steps:

Sample list of properties: Account, Parent, Alias: Default, Valid For Consolidations, Data Storage, Two Pass Calculation, Description, Formula, UDA, Smart List, Data Type, Account Type, Time Balance, Skip Value, Exchange Rate Type, Variance Reporting, Source Plan Type, Plan Type, Aggregation

![Oracle DRM Essbase Integration to refresh outline](/assets/images/blog/blog-01.webp)
Oracle DRM Essbase Integration to refresh outline

The name Account represents a Dimension. It can be replaced as required by different dimension names like Department, Location etc. Using an **external connection** from DRM, we can save all the values from the DRM in a **Oracle database table**. Then after creating a rule file and associating it with the Essbase cube outline, the metadata in the outline can be updated using the new rule file and using the ODI Knowledge Module **IKM SQL to Hyperion Essbase (METADATA)**. The name of the rule file will need to be used as a IKM parameter value.

## Approach using Flat Files

If I do not have ODI in my environment, then let's start with saving the DRM export with all the dimension property values in a **csv or txt file**. The file has to be in the format that Essbase can read, usually delimited by comma. The same properties mentioned above will be present in this file. Once the fresh file with the latest metadata is ready, it can be used to update my Essbase cube outline by loading it using a **rule file**. The fields in the flat file must map correctly with the rule file for the refresh process to work fine.

There are some Essbase property requirements that might be specific to my cube, maybe related to length or special characters. The DRM properties in that case can be adjusted and updated accordingly or for long term solutions can be validated in real-time using custom **DRM validations**.

Thus once the metadata is refreshed fine using any of the above approaches the Essbase outline will reflect the latest master data exported from DRM.