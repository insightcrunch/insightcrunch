---
layout: post
title: "SNP_SESSION - The Data Analyst’s Dream Table of Oracle Data Integrator"
date: 2018-07-11
categories: ["Analytics"]
tags: ["Oracle Data Integrator"]
excerpt: "The SNP_SESSION table in ODI is an analyst's dream. Execution metadata, error tracking, and the SQL queries that reveal everything about your ETL runs."
image: "/assets/images/blog/blog-21.webp"
reading_time: 4
author: "james-carter"
last_updated: 2026-03-29
---
The Oracle Business Intelligence Applications stack provides an array of tools during the implementation, and each of them comes with its rich set of features. The awesomeness comes when we get to experience several business use-cases and scenarios, analyze the metrics and data, interpret them along the lines of the business process, and ultimately when also we encounter product limitations - and **discover amazing ideas to make our lives easier**. Happiness...as deep the word sounds, becomes almost synonymous in such cases, as we make breakthroughs through innovative complex ideas. For any help in ODI please feel free to comment or contact me.

[Ask Rahul](https://insightcrunch.com/contact/)

All of us are aware of this repository table **SNP_SESSION** in ODI, the unattractive component that shows lots of rows and numbers and dates, often just helps only to find specific information, and then we are done with it. In an environment where overnight several incremental loads consume around 6 hours daily, it generates lots of logs and data and writes to all the repository tables, including session level details in SNP_SESSION. All information of every session like rows processed, rows inserted, rows updated, period and filter variables used, duration taken, start time, end time - are logged in SNP_SESSION.

![](/assets/images/blog/blog-21.webp)

To understand the prowess of SNP_SESSION, we need to get to a **few questions first**, and then the train of thoughts and discoveries can follow. For a session am interested in, what is the behavior of this session over the last 4 months? Does it have any pattern during specific periods? Does it have any relation with other sessions’ attributes? Does a data volume of another session or duration of a different session influence this? Since rows processed do not always proportionately impact session durations, does a % variance of a different session impact the session am interested in to an extent? Say in my today’s load, can I find which scenarios from the past repeated today, say with similar data volume or % variance in duration? Can I foresee untold information or what is going to happen as the loads progress by real-time analysis of the data?

It’s been very exciting to know over the last few weeks that all of the above questions can be answered, tremendously **by using SNP_SESSION**, and with some help from SNP_LP_INST and SNP_LPI_STEP. We have implemented a solution which is now in its final testing phase with live data, and will heavily complement manual human monitoring activities - by providing root causes before the impact happens, and providing additional insights into the application which otherwise often gets overlooked due to the vastness of the system.

We have **calculated** the weighted average of each session duration, load plan wise, over a period of last several months, with an **algorithm **that took a long time to develop after a lot of brainstorming. Then came the perilous task of calculating the standard deviation of the weight samples so as to help calculate the accuracy of our analysis, but it finally happened! Next came analyzing the data volume - with NB_ROW, NB_INS, NB_UPD already available in SNP_SESSION and waiting for us. Comparing today’s volume with the weighted average for the corresponding session itself started giving insights, but we **wanted more**. We asked what next, what if, why now, what then, and each metric opened up new paths before us to explore.

Each field of SNP_SESSION gave rise to almost 3-4 metrics of it’s own, giving rise to real-time daily calculation and analysis of the datasets during executions, and the impact it causes to the parent load plan. During the execution of each load, we are able to get **insightful emails** consisting of detailed analysis of the load - and a similar day in history if today’s scenario matched, and what happened then, and how the day went with the consequent activities.

But again, we need a single indicating factor, giving rising to the **calculation of probability** - as a single point of figure to indicate the possibility of actual realization of our real-time predictions, for each prediction. Hence, more brainstorming followed, and finally now every email gets tagged by a probability that makes it so much more meaningful. Thus, it becomes so true in today’s world, data is only useful when we know how to process it to our benefit - and it will truly continue to become more and more the case in future!