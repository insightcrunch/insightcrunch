---
layout: post
title: "DRM Batch Client Credentials Configuration"
date: 2016-09-25
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "Set up DRM Batch Client credentials for hands-free automation. Authentication configuration, credential storage, and secure unattended execution."
image: "/assets/images/blog/blog-44.webp"
reading_time: 2
author: "elena-wright"
last_updated: 2026-03-29
---
The Oracle DRM Batch Client is one of the most interesting features of the amazing master data management tool which enables a set of features without requiring manual intervention. Automation of many DRM activities can be setup daily using the DRM Batch Client.

The file that will store the credentials is named as drm-batch-client-credentials.exe - within this file the credentials for that specific Windows account will be stored. Interesting to note, if I log in with a different Windows account and try to run the DRM Batch Client, it will not run because the credentials though already stored is for the other Windows account. So I need to log in using that Windows account for my DRM Batch Client to work successfully, otherwise I need to configure the DRM Batch Client credentials for all the possible Windows accounts that are present so that all the accounts can use the DRM Batch Client fine.

![Oracle DRM Batch Client Credentials Configuration](/assets/images/blog/blog-44.webp)
Oracle DRM Batch Client Credentials Configuration

While setting up the DRM Batch Client, I would be interactively prompted with a few options whether I want to erase the existing credentials, or update the existing credentials etc. On selecting the the correct option and entering the credentials as requested, I am done configuring the DRM Batch Client successfully. On all future DRM Batch Client tasks, these are the credentials that will be used. This username thus can be found in all the audit logs going forward for all the activities performed by the DRM Batch Client. This immensely helps ease up all maintenance activities in the future and provides a rich benefit to scalability.

**Download** the detailed document on how to use the complete set of features of the Oracle DRM Batch Client. Subscribe to get access.

[s2If current_user_can(access_s2member_level1)]

[Download](https://insightcrunch.com/wp-content/uploads/2022/09/Oracle-Hyperion-DRM-Batch-Client-User-Guide.pdf) the Oracle DRM Batch Client User Guide here that will help you unlock the full potential of the features I explained above.