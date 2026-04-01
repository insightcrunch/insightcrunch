---
layout: post
title: "ODI Performance Tuning using indexes and keys"
date: 2016-10-15
categories: ["Analytics"]
tags: ["Oracle Data Integrator"]
excerpt: "Slow ODI loads? The right indexes and keys can transform performance. When to add them, which types matter, and the impact on your ETL pipeline."
image: "/assets/images/blog/blog-50.webp"
reading_time: 2
author: "rachel-foster"
last_updated: 2026-03-29
---
The Oracle Data Integrator load plans involve extracting and loading large volumes of data and then transforming them as per requirements. Often the volume of data becomes a bottleneck and the execution timings goes beyond the acceptable limits. That is when some of the age-old practices of performance improvement using keys and indexes come in.

![ODI Performance Tuning using indexes and keys](/assets/images/blog/blog-50.webp)
ODI Performance Tuning using indexes and keys

[](http://imageshack.com/a/img921/5388/0B1pqH.jpg)The intermediate C$ work tables and staging tables used in ODI are often ignored as part of the tuning process. It is not always necessary that the Extract and Load phases need to end with the same data set in the Source and the Target Staging areas. Let's say I have a unique key column (X) in my final target table that holds all the data after transformation. This unique key (X) is a sequence number that increases gradually in the source system. So now, during my extract phase, my requirement being fetching only the incremental data to the final target table, I will fetch those records in my source with the filter where the **source key is greater than the max (X) of my target final table**. So, I do not need to fetch all the records, instead only a subset of the data that meets the 'greater than' criterion.

Often, due to millions of records in the source table (example the table XLA_AE_LINE_ACS in XLA schema in EBS), the process takes an absurd amount of time. This is when we implement an **index on the column X in the source system**, and the same ODI load performance improves dramatically. It is relevant to note that my custom ODI code uses the filtering only on column X, and no other join or column is being used here.

How do you prefer to tune your custom ODI codes?