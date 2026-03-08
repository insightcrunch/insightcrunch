---
layout: post
title: "ODI Automation of Smart View Manual Activities"
date: 2016-10-19
categories: ["Analytics"]
tags: ["Oracle Data Integrator"]
excerpt: "Oracle Data Integrator provides multiple features to automate almost all manual data extraction and transformation related activities. One such scenario is using Smart View to manually fetch data ..."
image: "/assets/images/technology-industry-analysis-insightcrunch.webp"
reading_time: 3
author: "Insight Crunch Team"
---

Oracle Data Integrator provides multiple features to automate almost all manual data extraction and transformation related activities. One such scenario is using Smart View to manually fetch data from the Essbase cubes, maybe weekly or monthly. Often such cases require changing the values of time dimension over the entire scope of the template (maybe to different values for current year and last year, or current month and last month, in adjacent columns, etc) and then retrieve the data to meet our needs. So it might become time-consuming and prone to manual errors.

![ODI Automation of Smart View Manual Activities](https://insightcrunch.com/wp-content/uploads/2016/10/pexels-photo-6914017.jpeg)
ODI Automation of Smart View Manual Activities

This is where ODI comes really handy with the KM called **LKM Hyperion Essbase DATA to SQL**. First we need to create our report script (say X.rep) within Essbase to fetch the data we require. This report script is the first layer of data extraction and must include all the relevant information and records. It might not necessarily be formatted exactly as per requirement but should extract all the data for the next processes to act on this retrieved data.

Since the **report script** is containing all the filters for time dimension and other parameters - it is essential to keep it **dynamic** to avoid manual intervention. Lets save my report script content in a table T1 and instead of hard-coding the time value, I name it "DummyPeriod". Then using an ODI interface, my first step is to create the report script with the actual value of "DummyPeriod". Using the KM **IKM SQL to File Append**, I use the table T1 as my source and the file X.rep as my target. In the target, I use the [REPLACE](https://docs.oracle.com/en/database/oracle/oracle-database/21/sqlrf/REPLACE.html#GUID-1A79BDDF-2D3B-4AD4-98E7-985B2E59DA6B) function to replace "DummyPeriod" with my actual period value (this value can get refreshed by a ODI variable). In the Flow properties for this IKM, the value for TRUNCATE must be set to *True* - else the Report Script will get appended with its old content every time I create the report script using the ODI interface. Thus, the report script gets created dynamically every time with dynamically generated values.

Now, in a new ODI interface, a datastore which matches the report script's number of output columns and data-types will act as the **Source**, and a database staging table will act as our **Target**. The **LKM Hyperion Essbase DATA to SQL** will be used here. It has the flow control parameters EXTRACTION_QUERY_TYPE and  EXTRACTION_QUERY_FILE. Our values in this case will be *ReportScript* and *X* respectively. Within this interface, we can map the fields from the source to the target and use any filter or join or transformation as required.

Once the data is loaded in the target database staging table, we can implement standard ETL transformations to modify the data as per our required formatting. Then we can unload this data in a delimited file as required. Once the file is ready, it can be zipped and sent over as an email attachment to the intended recipients. It can also be sent via SFTP to any other server and path if required, thus completely eliminating any human intervention.

Learn more about the control parameters and LKM Hyperion Essbase DATA to SQL in the guide below. Subscribe to **Download** the document, then see page 9.

[s2If current_user_can(access_s2member_level1)]

[Download](https://insightcrunch.com/wp-content/uploads/2022/09/ODI_Essbase_Integration.pdf) the ODI Essbase integration guide here.

So now we can save our valuable time to catch some Pokemons! How do you automate your Smart View activities?