---
layout: post
title: "Analyzing ODI data load using IKM SQL to Hyperion Essbase (DATA)"
date: 2016-10-21
categories: ["Analytics"]
tags: ["Oracle Data Integrator"]
excerpt: "How ODI loads data into Essbase using IKM SQL to Hyperion Essbase (DATA). KM options, load modes, and tuning strategies for high-volume cubes."
image: "/assets/images/blog/blog-37.webp"
reading_time: 4
author: "ryan-walsh"
last_updated: 2026-03-29
---
Oracle Data Integrator provides a range of Knowledge Modules to integrate with and process data from and load to various applications, and it is no different with Oracle Essbase. The Knowledge Module **IKM SQL to Hyperion Essbase (DATA)** loads the data from a Oracle database to an Essbase cube - and has various parameters to customize it as per our requirement.

![ODI data load using IKM SQL to Hyperion Essbase (DATA)](/assets/images/blog/blog-37.webp)
ODI data load using IKM SQL to Hyperion Essbase (DATA)

Now we need to have the data ready in our **Oracle database table to be used as source**, usually having all the dimensions (like Time, Account, Department, etc) and then the fact value (Actuals) as the base columns (this is the minimum requirement). We can have more than one fact value (say Budget data), these can be loaded to the Essbase cube using the same source table or another different table, whichever is convenient.

Next we select the **Essbase cube as our target** - say Sample.Sample. So now we are ready to create the ODI interface to load our data. We drag the Oracle table datastore in our source and the Cube datastore in our target. We will select the ***IKM SQL to Hyperion Essbase (DATA)*** as KM in our flow properties for the Target as shown below. It is important to observe each of the parameters closely for this ODI interface to behave exactly as expected to.


The **default values usually suffices**, but to optimize our loading, it is advisable to play around a little with the values for *COMMIT_INTERVAL* and the *RULES_FILE*. It can significantly enhance the performance of the loading process. Also note that the value 0 for *MAXIMUM_ERRORS_ALLOWED* does not signify the loading stops even for one error, it's just the opposite, here 0 signifies infinity. So the process will ignore all errors and succeed always, even if it is unable to load any record. The log file configured for the variable *ERROR_LOG_FILENAME* can often come in handy in such cases if the ODI Operator log or the Essbase application log do not provide any fruitful information.

The *CLEAR_DATABASE* option can be set to true if we are doing a full refresh every time. Also, this same activity can be achieved through MaxL (using ODI OS Commnad to call the MaxL script) for some more granular control.

The *CALCULATION_SCRIPT* option is a very handy option and is really useful when we need to run a calculation script immediately after our loading process completes. Thus we can skip a MaxL step by incorporating the calculation script within our ODI interface.

One of the common issues faced during the loading process is **records getting rejected** due to unknown member or missing member. This can be taken care by some [robust data quality control check](https://insightcrunch.com/2016/10/13/essbase-data-quality-control-using-odi/) which is often overlooked and not given due importance - but it definitely saves a lot of time and effort in the long run.

Another commonly faced error which does not get captured in the log explicitly is the **incorrect value of RULE_SEPARATOR**. The default value is comma, but sometimes due to cloning or  migration issues, when we migrate the ODI interfaces with missing references errors, the values set for the IKM gets lost, and returns to the default comma. In such cases, it is best to migrate the interfaces again from higher instances (like Production) after the missing reference errors are fixed. This missing reference error after cloning or migration can happen due to missing KMs, or due to different internal ids for the same ODI objects and KMs between different ODI repositories. If re-migration becomes impossible, we need to re-configure the values for the IKM all over again, and at that time need to make sure we use the correct value for RULE_SEPARATOR.

We can also work on **improving the performance** of the data loading by customizing the *FETCH_SIZE* parameter - this parameter basically determines how many rows are read from the source at a time. Subscribe and **Download** the IKM SQL to Hyperion Essbase (DATA) guide, then read page 5 to learn more about the different control parameters.

[s2If current_user_can(access_s2member_level1)]

[Download](https://insightcrunch.com/wp-content/uploads/2022/09/ODI_Essbase_Integration.pdf) the guide here to learn more on how to use the IKM.

What's your experience with the IKM SQL to Hyperion Essbase (DATA)?