---
layout: post
title: "OdiSqlUnload and the Possibilities"
date: 2016-10-01
categories: ["Analytics"]
tags: ["Oracle Data Integrator"]
excerpt: "OdiSqlUnload in Oracle Data Integrator: extracting data from databases into flat files. Syntax, parameters, use cases, and performance considerations."
image: "/assets/images/blog/blog-08.webp"
reading_time: 1
author: "Insight Crunch Team"
last_updated: 2026-03-23
---
The Oracle Data Integrator is one of the best futuristic data transformation and loading tools with a variety of features for the end-user. ODI as an ELT tool provides a lot of inbuilt features for data processing using different technologies.

One of the most useful I find is the ODI tool OdiSqlUnload, which can be used in multiple ways in different scenarios for different purposes. To use this feature, create a new ODI procedure and in the Source tab select technology as "ODI Tools". Then using the below syntax we can create files with the listed customization options:

- Dynamic output file path

- Dynamically fetched schema username

- Dynamically fetched schema password

- File content is decided by the SQL query (the logical schema for the SQL to be executed in needs to be set in the Target tab of the ODI procedure)

**OdiSqlUnload** "-FILE=/Output.txt" "-DRIVER=" "-URL=" "-USER=" "-PASS=" "-FILE_FORMAT=VARIABLE" "-FIELD_SEP=" "-ROW_SEP=" "-DATE_FORMAT=yyyy/MM/dd HH:mm:ss" "-CHARSET_ENCODING=ISO8859_1" "-XML_CHARSET_ENCODING=ISO-8859-1"  
select <>, <>, <> from <>.<>

![OdiSqlUnload and the Possibilities](/assets/images/blog/blog-08.webp)
OdiSqlUnload and the Possibilities

Now that I am able to successfully generate the ODI generated files, let's look at the different ways this can be leveraged to cater to various scenarios:

- Create and attach files to emails via the OdiSendMail tool

- Generate error logs for ODI Load Plans and notify administrators

- Create multiple files with different delimiter formats and data content in a single procedure by adding multiple steps

- Create files in a single path using data from different physical sources using different logical schemas in different steps in a single procedure

How do you utilize this feature in your environment? Do you need help implement a new design? Comment or message me to get started.

[s2If !current_user_can(access_s2member_level1)]

[/s2If]