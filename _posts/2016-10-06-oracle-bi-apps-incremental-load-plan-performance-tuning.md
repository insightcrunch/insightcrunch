---
layout: post
title: "Oracle BI Apps Incremental Load Plan Performance Tuning"
date: 2016-10-06
categories: ["Analytics"]
tags: ["Oracle Data Integrator"]
excerpt: "Slow BI Apps incremental loads? ODI performance tuning techniques using indexes, partitioning, and parallel execution that dramatically speed things up."
image: "/assets/images/blog/blog-09.webp"
reading_time: 2
author: "alex-cunningham"
last_updated: 2026-03-29
---
The Oracle Business Intelligence Applications integration with Oracle General Ledger comes with an out-of-the-box load plan that Oracle provides for extracting and loading into the BI data warehouse. However, this load plan comes with a lot of scope of improvement. I got the opportunity to analyze this in details and some findings are really helpful.

The first thing that comes to mind is whether all the steps are essential, and yes, they are. In fact, some relevant practices (like gather stats, updating the W_ETL_LOAD_DATES for every scenario, etc) followed in the load plan are critical for successful loadings and long term ease of maintenance.

![Oracle BI Apps Incremental Load Plan Performance Tuning](/assets/images/blog/blog-09.webp)
Oracle BI Apps Incremental Load Plan Performance Tuning

Before the load plan was tuned, it was observed around 90 minutes was the average execution time, whereas after the changes, the average time has come down to 70 minutes. It is important to mention here that there were some custom loads also that ran as part of the load plan, so the tuning also involved tweaking them. The execution times are dependent on data volume, so keep that in mind while dealing with the stats.

The first change that was done was to move the SDE Dimension and SDE Fact loading phases in parallel. This Source Data Extract (SDE) step can easily help in reducing the time with no impact to the overall process. The dimension data and fact data will continue to be extracted from the source system independent of each other. The dimension loading will complete very soon (usually does unless you are having a massive hierarchy of segment values). The fact loading on the other hand will finish in close to 40-45 minutes (might vary based on your data volume).

The second recommended change is for custom loads in case I have them stitched with the incremental load plan. Many organizations and systems often have custom loads appended at the end of the load - since these loads are *dependent *on the DW loading and need to wait until the loading process completes. The Post Load Process (PLP) runs after the Source Independent Load Objects (SILOS) loading has completed. Any custom load that uses the DW fact tables can start in parallel with the PLP loading process. There's no need to wait (with no negative impact) for PLP loading to complete, since the fact data is already loaded. Thus we can save some more time with the parallelism kicking in.

What are your ideas of performance tuning?