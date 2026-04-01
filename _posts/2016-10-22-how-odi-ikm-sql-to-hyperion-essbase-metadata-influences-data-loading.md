---
layout: post
title: "How ODI IKM SQL to Hyperion Essbase (METADATA) influences data loading"
date: 2016-10-22
categories: ["Analytics"]
tags: ["Oracle Data Integrator"]
excerpt: "The Essbase metadata KM in ODI controls more than outlines. How its settings influence data loading speed, dimension build, and cube integrity."
image: "/assets/images/blog/blog-04.webp"
reading_time: 4
author: "ryan-walsh"
last_updated: 2026-03-29
---
Oracle Data Integrator integrates with Essbase for metadata as well as data loading using different Knowledge Modules. Each of the KMs provides a range of options for us to customize the loading as we want. The IKM SQL to Hyperion Essbase (METADATA) is usually the starting point when we begin our activities, since first we will load the metadata and get the outline ready, then we can load the actual data.

![ODI IKM SQL to Hyperion Essbase (METADATA) Loading](/assets/images/blog/blog-04.webp)
ODI IKM SQL to Hyperion Essbase (METADATA) Loading

The standard practice of the using the **IKM SQL to Hyperion Essbase (METADATA)** is to create an ODI interface for each dimension using this KM, and provide the values of the parameters in each of the interfaces as applicable. As observed below, we need to create a rule file for the different dimensions in Essbase and provide those rule file names as the value for the parameter RULES_FILE. In case we need the data to be loaded in a specific order, we can use the ORDER_BY clause accordingly.


So we can **create an ODI package** with 6 different interfaces, each with it’s own rule file and loading the corresponding dimension hierarchy in the outline. The value for RULE_SEPARATOR need to be set correctly here, else the outline will not reflect any updates and the interface will not work. The value for RESTRUCTURE_DATABASE defines what to do after the metadata loading. If we are clearing out all the data prior to our metadata loading via MaxL, then the default value KEEP_ALL_DATA does not make a difference. Else we can use the values KEEP_INPUT_DATA or KEEP_LEVEL0_DATA or DISCARD_ALL_DATA as per our requirement.

The **Essbase cube outline refresh** plays a very important role in the daily life of the cube. If the loading process or parent child loading sequence is not set correctly, the members can fall off during the loading phase. For example, if we try to load the child before it’s parent, the child will fail to get loaded. And then the parent will stay without it’s child at the end of the load. It becomes even more difficult to track such scenarios if we have LOG_ENABLED as the default false value.

The LOG_FILE_NAME and the ERROR_LOG_FILENAME can prove to be very beneficial in such cases. It is **always recommended to generate a log** during our loading phases, unless we have a strong [data quality control check](https://insightcrunch.com/2016/10/13/essbase-data-quality-control-using-odi/) in place. Incorrect outline build can drastically affect the subsequent data loading process, leading to multiple records rejections due to missing members in the outline. This can lead to confusion and data mismatches across different data sources, thus causing a nightmare for developers, more so if insufficient logging is in place.


While loading the dimension members, we can also use the ODI interfaces to **load the Alias values** of each of the members. If we have more than one Alias, we can accordingly use multiple interfaces and rule files to populate the values accordingly. Only thing is we have to make sure each of the rule files point to the correct Alias in the path below:

    Rule File → Dimension Build Settings → Global Settings → Global Properties → Update Alias Table → <>

So we can use identical ODI interfaces with different values in the Alias field in the Target and different rule files values in the flow properties to load them.

The ODI interfaces during meta data loading sometimes **gives the error ‘Cannot open cube outline’**. This is often caused by a parallel running job which is in incomplete status, thus preventing our interface to have a lock on the outline. Or it can be due to a developer who has locked the outline in edit mode but forgotten to unlock it – thus again preventing our ODI interface to get access to the Essbase outline in Edit mode. In such cases we need to identify the lock and then release it, then restart our ODI process. Subscribe and **Download** the IKM SQL to Hyperion Essbase (METADATA) guide below, then read page 4 for more details on each of the configuration parameters.

[s2If current_user_can(access_s2member_level1)]

[Download](https://insightcrunch.com/wp-content/uploads/2022/09/ODI_Essbase_Integration.pdf) the guide here to learn more on IKM SQL to Hyperion Essbase (METADATA).

This IKM is pretty peaceful otherwise and keeps doing it’s tasks quietly over time. How do you use your IKMs to refresh the Essbase metadata?