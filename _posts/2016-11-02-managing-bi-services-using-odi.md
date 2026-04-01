---
layout: post
title: "Managing BI Services using ODI"
date: 2016-11-02
categories: ["Analytics"]
tags: ["Oracle Data Integrator"]
excerpt: "Automate OBIEE maintenance from ODI. Restart services, refresh RPD, and manage BI components programmatically as part of your data pipeline."
image: "/assets/images/blog/blog-78.webp"
reading_time: 3
author: "james-carter"
last_updated: 2026-03-29
---
Oracle Data Integrator is one of the widely used tools for data loading into the Oracle Business Intelligence data warehouse. Often it happens that due to frequent data updates in the source systems, the data needs to be refreshed in the data warehouse during the daytime, while users might still be trying to run reports for their reporting purpose. This no doubt calls for a mechanism to restrict the user data access during the refresh activity to avoid dirty reads.

![Managing BI Services using ODI](/assets/images/blog/blog-78.webp)
Managing BI Services using ODI

We will be using the WebLogic Scripting Tool to achieve our objective. At the start of the load plan that loads the data from source to target, we will add a step that will bring down the services so that BI cannot be accessed by the users. Again at the end of the load plan we will add a step to bring the services up. This will also help us ensure that if the load fails the services will continue to stay down.

**To Stop:**

We will be creating an ODI OS command with the below script that will allow us to stop the BI services:

run.sh stop

This script will call the script wlst.sh with the variable value as **stop**. The content of run.sh will be:

$MW_HOME/oracle_common/common/bin/wlst.sh mydeploy.py stop

The parameters required for wlst.sh can be passed and set via other supporting (usually ".py") files. **Download** the *Weblogic Scripting Tool Guide* at the end of this article.

**To Start:**

We will be creating an ODI OS command with the below script that will allow us to start the BI services:

run.sh start

This script will call the script wlst.sh with the variable value as **start**. The content of run.sh will be:

$MW_HOME/oracle_common/common/bin/wlst.sh mydeploy.py start

The values for start and stop are passed over from run.sh. Using the above variables for stop, start and Middleware home further means we have an increased flexibility and these variables can be refreshed using ODI variables in the package from a **database control table**. Thus this code will run fine in every environment without requiring any change, since the values are already set specific to each instance in our database control table with the appropriate values.

Another advantage of having the start and stop mechanism through ODI is utilizing the daily executing statistics to **predict the completion time** of the job. Usually the execution time tends to vary over a period of time and often shows a pattern, i.e. the job might take longer on specific days of the months, or might be increasing by a few minutes every week. These can be considered in a ETC (estimated time of completion) calculator procedure that can simply calculate the expected end time of the job using our custom algorithm. This information is often extremely handy in crunch situations and puts the static history data to good use for all. There goes some small AI stuff again!

Subscribe and **Download** the *Weblogic Scripting Tool Guide* below to learn more on how to configure and customize the parameters in your script.

[s2If current_user_can(access_s2member_level1)]

[Download](https://insightcrunch.com/wp-content/uploads/2022/09/Using-the-WebLogic-Scripting-Tool.pdf) the Weblogic Scripting Tool Guide here to add more functionalities to your scripts.

How do you automate your BI service related activities and downtime maintenance?