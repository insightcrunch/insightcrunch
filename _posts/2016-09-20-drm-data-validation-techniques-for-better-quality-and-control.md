---
layout: post
title: "DRM Data Validation Techniques for Better Quality and Control"
date: 2016-09-20
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "The data in DRM is of extreme importance for any organization. Hence, automatically the need comes to have a robust control over the data and making sure..."
image: "/assets/images/blog/blog-66.webp"
reading_time: 3
author: "marcus-hall"
last_updated: 2026-04-01
---
The data in DRM is of extreme importance for any organization. Hence, automatically the need comes to have a robust control over the data and making sure there's no invalid content in there. There are quite a few ways to achieve this based on what sort of validations and control I want to put in place.

## Validations Required

Let's assume I have a few types of validations as per my requirement to put in place for a specific hierarchy:

- Prefix of a node must be a specific sequence of letters

- Leaf node must be 6 characters in length

- Limb nodes must not have descriptions with hyphen

- Leaf nodes cannot have null description

## Method 1

The **DRM repository tables** provide a range of options to find and format the relevant data easily. The main tables required for having all the required validation information above are below. By joining the below tables using SQL we can retrieve the required data.

- RM_VERSION

- RM_HIERARCHY

- RM_NODE

- RM_RELATIONSHIP

- RM_NODE_PROP_LOCAL

- RM_NODE_PROP_GLOBAL

- RM_TRANSACTION_HISTORY

We have lot of options after identifying the nodes which do not meet the 4 validation criterion above. We can use Windows Batch scripting to extract the required data using SQL and dump it in a txt file and send it via mail using Windows Mail. This activity can be scheduled to run always after a specific interval (say 30 mins) to make it near real-time data monitoring. Note how we are completely bypassing the inbuilt DRM Exports functionalities here. It's totally driven by the repository tables, SQL and Windows scripting.

![Oracle DRM Data Validation Techniques for Better Quality and Control](/assets/images/blog/blog-66.webp)
Oracle DRM Data Validation Techniques for Better Quality and Control

## Method 2

**DRM Exports** can be done to a **database table** after setting up a connection string to the database. The highly preferred method is to immediately create a batch script to call this export via DRM Batch Client, so that we can leverage the immense power of Windows scripting in our design. The required columns (mostly from the System Property Category) need to be added to this Export and then saved in a database table (say X).

Once in the Oracle database table, we can leverage the full flexibility of **SQL** to capture our required information. If I am using any Data Extraction tools in my instance like **ODI, Informatica PowerCenter, etc** it becomes all the more useful. I can use the tools to create sample reports, format data extracts, and even send out notification mails to relevant people with this information and request any corrective action. Such ETL jobs can be scheduled to run in tandem with the batch script that refreshes the table X. This way always the data will be latest in the DB table.

## Method 3

If I do not want to touch the DRM repository tables, and also do not want to create any new database table, there's still another way to generate notifications if data meeting the criterion is found. Create a **DRM export** which will generate a delimited flat file with the required data that is meeting the 4 validation rules. Directly read this file via an ETL tool like **ODI**, and send it via mail.

This approach assumes that the DRM export will be able to handle all the validation rules, which it is usually capable of doing. And sending mail using ODI is pretty straightforward, but it is essential that I have access to the path where the DRM export file is being generated, and also ODI must read the correct file from that path.

What techniques do you use to validate your Master Data?