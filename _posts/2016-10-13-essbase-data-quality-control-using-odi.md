---
layout: post
title: "Essbase data quality control using ODI"
date: 2016-10-13
categories: ["Analytics"]
tags: ["Oracle Data Integrator"]
excerpt: "Validate Essbase data quality after ODI loads. Post-load checks, aggregation verification, and how to catch data issues before they reach end users."
image: "/assets/images/blog/blog-06.webp"
reading_time: 2
author: "Insight Crunch Team"
last_updated: 2026-03-23
---
Oracle Essbase is an excellent tool for handling large volumes of data and doing complex calculations very fast. But it is interesting to observe how good the data is after we load it into Essbase. Seldom we validate the error logs or the Essbase server logs generated during the load process. Also, much rarely do we set the process to fail for minor issues. It is under these circumstances that the quality of the data needs to come under scrutiny.

Using the ODI **IKM SQL to Hyperion Essbase (DATA)** we daily load the data to the Essbase cubes. But it might so happen that the transactional data is not getting loaded into the cubes, because the outline build was not successful. Thus, **due to a missing member** (say for Account dimension) in the outline, all transactional data corresponding to that specific Account number will get rejected since there is simply **no placeholder** for the data to get into. This missing member in the outline can happen due to **multiple reasons** - cube outline build process failed, the source tables or files for outline build not having the correct data, DRM not having the missing member in its hierarchy, etc.

![Essbase data quality control using ODI](/assets/images/blog/blog-06.webp)
Essbase data quality control using ODI

The **impact of this Essbase data discrepancy** is profound. The data between Database reports and Essbase reports can drastically differ giving inconsistent results under such scenario causing more confusion. Also, data between different environments (say Dev or Test or Prod) can start varying for the same historic month - obviously due to the outline differences causing the data loads to behave differently - succeeding for some and failing for some.

This scenario **can be avoided** by keeping a separate step during the transactional data loading process. This step will be a quality control check to make sure that all the segment codes for which the data we intend to load to the Essbase cubes already exist in the outline. If yes, then only proceed with the loading phase (to avoid the data falling off during loading) - else even if a single member is missing in the outline, then trigger an alert to take necessary remedial action. In case you are thinking **how to run a compare** check with the outline, it's easy - either use a customized report script to export a dump of all the members for that specific dimension using IDESCENDANTS or use the table (or file) that was used as source to build the outline. Any of these can be used as the outline data reference, and then can be used to compare with the transactional data.

How do you make sure your Essbase data quality is perfect?