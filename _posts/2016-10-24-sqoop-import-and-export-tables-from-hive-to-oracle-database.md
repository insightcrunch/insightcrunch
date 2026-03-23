---
layout: post
title: "Sqoop Import and Export tables from Hive to Oracle Database"
date: 2016-10-24
categories: ["Analytics"]
tags: ["Hadoop"]
excerpt: "Sqoop import and export between Hive and Oracle Database: commands, configuration, troubleshooting, and best practices for Hadoop-Oracle data movement."
image: "/assets/images/blog/blog-03.webp"
reading_time: 6
author: "Insight Crunch Team"
last_updated: 2026-03-23
---
## Overview

Exporting and Importing table data from Oracle database to Hive and vice-versa is one of the most common activities in the world of Hadoop. It is essential to get sorted out on a few basics for seamless first time integration to avoid various parsing and loading errors. As a Data Analyst, I frequently need to perform the steps to load data between Hive and Oracle databases. Creating automated scripts to achieve the data load is immensely useful and saves a lot of time for Sqoop exports. You can even schedule such scripts to import and export data between Hive and Oracle database tables.

Sqoop provides a number of useful commands to achieve this. I have created a complete set of scripts using which we can import and export data between Hive and Oracle tables. Following these steps will allow you to follow the best practices of exporting and importing, along with additional scalability in case you want to change the parameters and delimiters in the future. The documentation that I have added with color codings will let you know exactly in which lines to implement the changes. Sqoop is one of the top tools today helping process large volumes of data.

## Hive to Oracle using Sqoop 

We will be doing the below activities sequentially to cover all the integration points between Oracle database, Sqoop, HDFS and Hive. In each of the steps you will see how I define the source and target connections, the directory structures, the delimiters, and other necessary arguments. The color coding convention between each of the steps will help you understand the significance of each of the lines of codes. You can **Copy and Paste all the executable codes** for each of the steps below to try out in your own environment. Now let us understand each of the below steps in details.

**Step 1:** Extract data from a source Oracle database table to Hadoop file system using Sqoop  
**Step 2:** Load the above Sqoop extracted data into a Hive table  
**Step 3:** Use Hive query to generate a file extract in the Hadoop file system  
**Step 4:** Load the generated file in Step 3 to a new target Oracle database table

![Sqoop Import and Export tables from Hive to Oracle Database](/assets/images/blog/blog-03.webp)
Sqoop Import and Export tables from Hive to Oracle Database

## **Step 1: Sqoop import data from Oracle database to Hive table**

Our first task is to identify our source Oracle database table, and then use Sqoop to fetch the data from this table to HDFS using Sqoop.

It is interesting to observe that we need to identify a primary key for the source Oracle database table. Else we will get the error “Error during import: No primary key could be found for table”. If we want to skip assigning a key we can include the highlighted parameter -m 1.

## **Step 2: Load the above Sqoop extracted data to a Hive table**

Assuming we already have a table created in Hive, we will load the file created in Step 1 into the Hive table using the below syntax.

## **Step 3: Export a file using Hive query to be consumed by Sqoop**

Now that we have the data in our Hive table, we will use the below command to create a file using a custom Hive query, in the green highlighted path. The delimiter highlighted in yellow can be changed according to our requirement – but accordingly it must be changed in Step 4 also where it’s highlighted in yellow.

## **Step 4: Sqoop export data from Hive exported file to Oracle database table**

The below command will use the above Hive exported file (from the same green highlighted path) to load our target Oracle database table.

The orange and blue highlighted sections above helps reading the records while exporting to the target database table. Else we might sometimes encounter the error “Can’t parse input data”.

## SQOOP IMPORT and EXPORT Commands

You need to be a Subscriber of my website to **Copy the codes**. The below codes have been tested and will allow you to immediately perform all the functions I explained above. Based on the names of your tables and files you will have to customize this code. We can thus use the Sqoop import and export commands here to fetch data from the Oracle tables, and also insert data into the Oracle tables.

[s2If current_user_can(access_s2member_level1)]

**Step 1: Sqoop import data from Oracle database to Hive table**

Our first task is to identify our source Oracle database table, and then use Sqoop to fetch the data from this table to HDFS using Sqoop.

SQOOP IMPORT –connect "jdbc:oracle:thin:@<>:<>:<>" –password "<>" –username "<>" –table "<>.<>" –columns "<>,<>" -m 1 –target-dir "<<HDFS path>>" –verbose

It is interesting to observe that we need to identify a primary key for the source Oracle database table. Else we will get the error “Error during import: No primary key could be found for table”. If we want to skip assigning a key we can include the highlighted parameter -m 1.

**Step 2: Load the above Sqoop extracted data to a Hive table**

Assuming we already have a table created in Hive, we will load the file created in Step 1 into the Hive table using the below syntax.

LOAD DATA INPATH '<<HDFS path>>' INTO TABLE <<hive table name>>;

**Step 3: Export a file using Hive query to be consumed by Sqoop**

Now that we have the data in our Hive table, we will use the below command to create a file using a custom Hive query, in the highlighted path. The delimiter highlighted in yellow can be changed according to our requirement – but accordingly it must be changed in Step 4 also where it’s highlighted in yellow.

INSERT OVERWRITE DIRECTORY '<>/<>'  
ROW FORMAT DELIMITED  
FIELDS TERMINATED BY ','  
select * from <<hive table name>> where <>;

**Step 4: Load data from Hive table exported file to Oracle database table**

The below command will use the above Hive exported file (from the same highlighted path) to load our target Oracle database table.

SQOOP EXPORT –connect "jdbc:oracle:thin:@<>:<>:<>" –password "<>" –username "<>" –table "<>.<>" –input-fields-terminated-by ','–input-lines-terminated-by '\n' –export-dir "<>/<>" –input-null-string "\\\\N" –input-null-non-string "\\\\N" –verbose 

The orange and green highlighted sections above helps reading the records while exporting to the target database table. Else we might sometimes encounter the error “Can’t parse input data”. 

Thus we have successfully loaded a table from Oracle database to Hive and again back from Hive to Oracle database, using Sqoop. We can query our Oracle and Hive databases to check the data if it is loaded fine. How do you prefer to load your data between these two systems?