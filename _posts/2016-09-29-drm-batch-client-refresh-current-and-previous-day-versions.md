---
layout: post
title: "DRM Batch Client Refresh Current and Previous Day Versions"
date: 2016-09-29
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "The Oracle DRM Batch Client is one of the best command-line utility tools that makes this Master Data Management application undoubtedly one of the best. It is nothing complex but provides a Windows ..."
image: "/assets/images/technology-industry-analysis-insightcrunch.webp"
reading_time: 2
author: "Insight Crunch Team"
---

The Oracle DRM Batch Client is one of the best command-line utility tools that makes this Master Data Management application undoubtedly one of the best. It is nothing complex but provides a Windows batch scripting interface to do all the DRM activities. There's almost nothing I cannot do using the Data Relationship Management Batch Client.

One of the most common practices in a DRM application is to find out the latest changes that have been done over the day - this includes any new additions, movements, changes etc. For this, I need to do a Compare Export between a historical snapshot of the DRM Version before the change and the snapshot after the change.

![Oracle DRM Batch Client Refresh Current and Previous Day Versions](https://insightcrunch.com/wp-content/uploads/2016/09/pexels-photo-3184652.jpeg)
DRM Batch Client Refresh Current and Previous Day Versions

The following design using DRM Batch Client will provide the most efficient way to automate this process with minimal long-term maintenance effort. Let's say the name of the version where all users will make the changes is known as the "Gold Version". There will be 2 more versions - "Current Day Version" and "Previous Day Version".

Now using DRM Batch Client, just before running the Compare export, I will do the below steps daily:

1. Delete the "Previous Day Version"  
2. Export the "Current Day Version" to a file, say X  
3. Delete the "Current Day Version"  
4. Export the "Gold Version" to a file, say Y  
5. Restore the "Previous Day Version" from X  
6. Restore the "Current Day Version" from Y

Since this sequence of steps run daily at the end of the day, after the steps, I have a snapshot of yesterday's data in the version "Previous Day Version", and today's changes in "Current Day Version". This whole activity can be accomplished using the DRM Batch Client. The sample batch client script is given below for reference. I prefer to stuff parameters wherever possible, gives me lot of peace of mind knowing I have lesser places to focus on, so wherever you see the % symbol it means that's a parameter the value of which needs to be **set**.

**set** DRM_URL = net.tcp://DRM-DEV:5210/Oracle/Drm/ProcessManager  
**set** DRM_BATCH_CLIENT = C:\Oracle\Middleware\EPMSystem11R1\products\DataRelationshipManagement\client\batch-client\drm-batch-client.exe  
**set** DRM_LOG_HOME = C:\PROD\DRM\Batch_Log_Files  
**set** SOURCE_VERSION_FOR_PREVIOUS_DAY_VERSION = Current Day Version  
**set** TARGET_VERSION_FOR_PREVIOUS_DAY_VERSION = Previous Day Version  
**set** SOURCE_VERSION_FOR_CURRENT_DAY_VERSION = Gold Version  
**set** TARGET_VERSION_FOR_CURRENT_DAY_VERSION = Current Day Version

%DRM_BATCH_CLIENT% /op=**DeleteVersion** /url=%DRM_URL% /vabbrev="%TARGET_VERSION_FOR_PREVIOUS_DAY_VERSION%" /log="%DRM_LOG_HOME%\Current_and_Previous_Versions"\Refresh_Current_and_Previous_Day_Versions_Log.txt

%DRM_BATCH_CLIENT% /op=**BackupVersionToFile** /url=%DRM_URL% /conn="BackupVersionToFile" /objectaccess=System /vabbrev="%SOURCE_VERSION_FOR_PREVIOUS_DAY_VERSION%" /filename="%DRM_LOG_HOME%\Current_and_Previous_Versions"\Current_Day_Version_Backup.txt /delim="|" /log="%DRM_LOG_HOME%\Current_and_Previous_Versions"\Refresh_Current_and_Previous_Day_Versions_Log.txt

%DRM_BATCH_CLIENT% /op=**DeleteVersion** /url=%DRM_URL% /vabbrev="%TARGET_VERSION_FOR_CURRENT_DAY_VERSION%" /log="%DRM_LOG_HOME%\Current_and_Previous_Versions"\Refresh_Current_and_Previous_Day_Versions_Log.txt

%DRM_BATCH_CLIENT% /op=**BackupVersionToFile** /url=%DRM_URL% /conn="BackupVersionToFile" /objectaccess=System /vabbrev="%SOURCE_VERSION_FOR_CURRENT_DAY_VERSION%" /filename="%DRM_LOG_HOME%\Current_and_Previous_Versions"\Gold_Backup.txt /delim="|" /log="%DRM_LOG_HOME%\Current_and_Previous_Versions"\Refresh_Current_and_Previous_Day_Versions_Log.txt

%DRM_BATCH_CLIENT% /op=**RestoreVersionFromFile** /url=%DRM_URL% /conn="BackupVersionToFile" /objectaccess=System /sver="%SOURCE_VERSION_FOR_PREVIOUS_DAY_VERSION%" /tver="%TARGET_VERSION_FOR_PREVIOUS_DAY_VERSION%" /save=Y /filename="%DRM_LOG_HOME%\Current_and_Previous_Versions"\Current_Day_Version_Backup.txt /delim="|" /log="%DRM_LOG_HOME%\Current_and_Previous_Versions"\Refresh_Current_and_Previous_Day_Versions_Log.txt

%DRM_BATCH_CLIENT% /op=**RestoreVersionFromFile** /url=%DRM_URL% /conn="BackupVersionToFile" /objectaccess=System /sver="%SOURCE_VERSION_FOR_CURRENT_DAY_VERSION%" /tver="%TARGET_VERSION_FOR_CURRENT_DAY_VERSION%" /save=Y /filename="%DRM_LOG_HOME%\Current_and_Previous_Versions"\Gold_Backup.txt /delim="|" /log="%DRM_LOG_HOME%\Current_and_Previous_Versions"\Refresh_Current_and_Previous_Day_Versions_Log.txt

It's interesting to note the versions take some time to save, so this entire process can take atleast upto 5-10 minutes to complete successfully.