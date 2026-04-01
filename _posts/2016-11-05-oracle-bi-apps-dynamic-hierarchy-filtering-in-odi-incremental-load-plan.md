---
layout: post
title: "Oracle BI Apps dynamic hierarchy filtering in ODI incremental load plan"
date: 2016-11-05
categories: ["Analytics"]
tags: ["Oracle Data Integrator"]
excerpt: "Filter hierarchies dynamically in BI Apps ODI loads. How to restrict dimension data at runtime using variables and conditional logic in load plans."
image: "/assets/images/blog/blog-89.webp"
reading_time: 5
author: "james-carter"
last_updated: 2026-03-29
---
Oracle Business Intelligence Applications often sources data from various systems, and it is often required to restrict or allow various dimension information during the loading processes. There are a variety of ways this can be done, let's take a walk through of few possible mechanisms of how this can be achieved in the Oracle Data Integrator incremental load plan with the maximum amount of flexibility.

![Oracle BI Apps Dynamic Hierarchy Filtering using ODI Incremental Load Plan](/assets/images/blog/blog-89.webp)
Oracle BI Apps Dynamic Hierarchy Filtering using ODI Incremental Load Plan

Our source system can be a number of applications like Oracle E-business Suite, Oracle Data Relationship Management, custom data warehouses, custom Essbase cubes, etc. To process the transaction data from each of these source systems, we need to first process the dimensional data from them.

While **loading to Oracle BI Apps**, there a few integration points which need to be closely monitored. The first area to focus on is the table **W_GL_SEGMENT_DH** (loaded by the objects in the folder SIL_GLSegmentDimensionHierarchy) which holds all the hierarchy information. This table gets loaded from the table W_GL_SEGMENT_DHS, so we can put a filter based on the top node of the hierarchy tree we want to exclude - so our filter will look like:  
    WHERE W_GL_SEGMENT_DHS.HIERARCHY_ID NOT IN ('<>')  
This will ensure that all the members in the hierarchy under the node <> are excluded while loading to W_GL_SEGMENT_DH.

While **sourcing from Oracle E-business Suite**, if we are using custom interfaces to source the hierarchy information, it becomes essential to make sure that the filtering process is robust to make sure all the intended members are filtered out (or in). This calls for a flexible dynamic filtering process instead of putting in all the individual member names. Here in the below query we will be able to recursively traverse the whole hierarchy tree starting from the top node. Then using these values we can easily implement in our design.

```
SELECT SYS_CONNECT_BY_PATH (PARENT_FLEX_VALUE, '/') PARENT_VAL,
LEVEL ACCOUNT_PARENT_LEVEL, H.FLEX_VALUE CHILD_VAL,
H.SUMMARY_FLAG
FROM APPS.FND_FLEX_VALUE_CHILDREN_V H
START WITH PARENT_FLEX_VALUE IN ('<>')
CONNECT BY NOCYCLE PRIOR FLEX_VALUE = PARENT_FLEX_VALUE
```

While **sourcing hierarchy from Oracle Data Relationship Management**, the first step is to connect our DRM application to a database and then export the DRM hierarchy to a database table (unless you love to work with files more) with the values TOP_NODE, NODE_NAME, PARENT as the mandatory fields. Then, while sourcing from this table, we can similarly use our filter with a CONNECT BY query as above. We can also use DRM Properties as flags and then use the values of those flags (Y or N or some other value) from the table as part of our filtering, but that's usually required for more complex scenarios.


While **sourcing data from an Essbase cube**, first we have to identify the full hierarchy information. Based on that information we can implement our filtering process. We will be using Essbase Report Script to extract the Essbase outline information using IDESCENDANTS - this will return the values of all the members in the hierarchy starting from the top node. Once the output of this Report Script is stored in a database table, it can be easily used to fetch our required information by placing the filter to include or exclude the members of a tree. Again, I always prefer keeping everything as dynamic and flexible as possible to minimize manual effort in the future in case of any changes - so CONNECT BY is my go-to choice. **Download** the IDESCENDANTS and CONNECT_BY Guides at the end of this article to learn more on how to implement these in your code.

While **sourcing hierarchy data from a custom data warehouse**, things cannot get more exciting. We are blessed with all the freedom in the world to optimize our design as much we want. I prefer designing and creating custom mappings for each dimension with different target dimension tables which provides a lot of ease of maintenance and troubleshooting in the long run. Each target table will be containing all the hierarchy information for the specific dimension along with its corresponding keys. Then we can load these keys to the fact table as usual. Now, while sourcing each of the dimensions, we can choose to include or exclude specific trees in the hierarchy. The same logic using CONNECT BY will be used here, but need to be repeated for each specific dimension mapping - since we have separate target tables for each dimension as part of design and future troubleshooting optimization.

In each of the above cases, we can see the **value for <> is critical** for the dynamic filtering to work. It's better to keep the value(s) of the top node(s) as much flexible as possible so that any future change can be absorbed with minimal impact. This can be done by storing the values of the relevant top nodes in a table. And refreshing this table from a file at the first step of our ODI incremental load plan. The file will be containing the values of the top nodes, so our only single point of maintenance becomes the file - using this file we can control whether to include or exclude entire hierarchy trees or specific values while loading into our Oracle BI Apps warehouse. This sort of flexibility no doubt comes at the cost of a lot of effort during the initial development phase, but surely proves to be a very decent and robust solution in the long run.

Subscribe and **Download** the *IDESCENDANTS* and *CONNECT_BY* Guides below to enhance your implementation practice.

[s2If current_user_can(access_s2member_level1)]

Download the [IDESCENDANTS](https://insightcrunch.com/wp-content/uploads/2022/09/Essbase_IDESCENDANTS.pdf) and [CONNECT_BY](https://insightcrunch.com/wp-content/uploads/2022/09/CONNECT-BY.pdf) Guides here. Learn how you can apply them in different scenarios based on your requirement.

How do you prefer to control your hierarchy data?