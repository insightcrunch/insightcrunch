---
layout: post
title: "DRM Data Loading Automation using ODI"
date: 2017-01-09
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "Automate Oracle DRM data loading using ODI: ETL pipeline setup for importing master data into Data Relationship Management from external sources."
image: "/assets/images/blog/blog-14.webp"
reading_time: 4
author: "Insight Crunch Team"
last_updated: 2026-03-23
---
The Oracle Hyperion Data Relationship Management application is a pretty flexible tool and most of the activities that can be done manually can be automated (using ETL tools like ODI, Informatica PowerCenter, etc). Recently I was presented with a business scenario by one of my readers which is pretty interesting yet tricky. Yes it involves a request to automating a manual process as you might have already guessed.

The requirement goes as below:

*The source systems are DWH and HRMS. Hence, the data/master data which we will get would be through staging tables to DRM. The source system would send the full data every month on month to the staging table and from where DRM has to pick. The comparison process in table (interim changes) first should go to the business user in an email and once the reply is ok, it should be incorporated in DRM and then publish to down stream applications.*

To proceed with this activity, first and foremost we need to be familiar with DRM action scripts - which will involve generating Add, AddInsert and Move scripts. In addition to that, if we have an ETL tool in our environment (like ODI, Informatica PowerCenter, etc) it's beneficial - else we can also use SQL to achieve our purpose as we will see next.

![DRM Data Loading Automation using ODI](/assets/images/blog/blog-14.webp)
DRM Data Loading Automation using ODI

## Method 1

Since the source systems DWH and HRMS are sending the full dataset every month - there needs to be a mechanism to detect the changes arriving at the staging tables in DRM end. This is where the Changed Data Capture (CDC) feature of ODI can come in handy, or else if we are using any other equivalent tool this feature will come in handy. This changed data capture can also be achieved using standard query languages so that the records that have changed/inserted can be flagged (say U/I) accordingly.

This set of records can be sent as an email (with attachment if data volume is too big) to the respective business users for approval. Let's say we have a field called "*APPROVED*" in our table and all these records are defaulted to N. Once the approval comes from the users - these fields need to be set to Y for the approved changes manually by the IT team. Until then these records will sit idly in the staging table without propagating to DRM. This manual flagging step unfortunately cannot be avoided since there is no integration yet between DRM and email server.

Now, once the records (say 8 out of 10 got approved, so we have 8 Y's and 2 N's) are flagged Y - they will be considered for the next steps of processing. The next steps are to create the Action Scripts for DRM to create the Add and Move scripts. Assuming the DRM version and hierarchy are already existing - the scripts formatting once done as per the required format it will be ready to be loaded to DRM. If the target txt/csv Action Script file is not in the same server where DRM can read it from, it has to be further SFTP ed to that location. Or else we can use SQL Loader to fetch the data from the Action Script table to the DRM server and then schedule Windows Batch Scripts to load the action script. There are quite a few ways this can be done and all depends on the environment setup we have in place.

## Method 2

If we want to keep the DRM staging table untouched by the manual update of Y and N flags - we can fine tune our approach to a control-file based design where the member names that are approved, will be kept in a file - that will be used for lookup. So say N1 and N2 are approved, the file will contain the below data:

    X,N1  
    X,N2

Here X denotes the batch id (yes, we need to create a "*BATCH_ID*" field in the DRM staging table which should be updated with a sequence generator type of ID for every record flagged U/I for that specific load run) - which should be unique for every load.

Let's see why we need this BATCH_ID field. If tomorrow our load runs and detects a change for the same member N1, and it finds N1 already in the file, it will get processed without waiting for approval. So since the batch id will change in the DRM staging table for every run - we do not have chances to unapproved changes of the same member to flow through since the next steps will check if both the BATCH_ID and member name are present in the control file. Instead of a file, this can also be made into a small table with only 2 columns which the IT team will have update/delete privilege to manage it daily.

This approach will provide a more safer control to the IT team and avoid the risk of accidentally modifying sensitive application tables or objects. Anyways working with DRM is always extremely a cautious activity day-in and day-out where a simple typo can cause widespread implications to multiple downstream systems - so minimizing risk and avoiding manual errors is preferred to be a part of any design.

How do you prefer to automate your DRM data loading processes?