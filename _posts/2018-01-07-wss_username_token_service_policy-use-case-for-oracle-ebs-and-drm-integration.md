---
layout: post
title: "wss_username_token_service_policy use case for Oracle EBS and DRM Integration"
date: 2018-01-07
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "The year of 2017 was an incredible year with tremendous ups and equal downs both at a professional and personal level. However, it has again helped in garnering some very fruitful insights regarding ..."
image: "/assets/images/technology-industry-analysis-insightcrunch.webp"
reading_time: 2
author: "Insight Crunch Team"
---

The year of 2017 was an incredible year with tremendous ups and equal downs both at a professional and personal level. However, it has again helped in garnering some very fruitful insights regarding everything around me and to plan few things better ahead. This is not to undermine any of the other years like say 2016 or 2015, but it is just that the impact of some incidents and the decisions that I have done and taken in 2017 will be changing my life forever. Let's see what 2018 has in hold! Wishing you a very happy new year ahead!

![wss_username_token_service_policy use case for Oracle EBS and DRM Integration](https://insightcrunch.com/wp-content/uploads/2018/01/pexels-photo-7652136.jpeg)
wss_username_token_service_policy in Oracle EBS and DRM Integration

The web services play an important role in the authentication process for the EBS and DRM metadata integration. Few months back during the DRM repository movement we came across a few challenges with the MDS schema database host info which enlightened a few areas and paved way for some more personal study. After the initial setup, once the oracle-epm-drm-webservices WSDL is up and running fine, we need to attach a security policy to this application. This will ensure that clients like the program "Load Segment Values and Hierarchies" makes the request to the WebLogic Server to get the system generated token for the user (say EbsIntegrationUser) which can be passed to DRM. Then DRM can validate that token with OID to verify authentication instead of requiring a username/password.

Oracle Web Services Manager (OWSM) will need to be deployed first in the same EPM Server and domain where DRM Web Service is deployed. The database repository schema name for OWSM is set to a different value and usually ends with *_MDS which corresponds to Metadata Schema.

Once done, the new policy needs to be created in Weblogic under Farm_EPMSystem → Weblogic Domain → EPM System → Web Services → Policy Sets. Then in Step 3 for "Add Policy References" we need to select and assign wss_username_token_service_policy.

There are other policies also that can be used as per the scenario faced, however for this specific integration an authentication token suffices. [Here](https://docs.oracle.com/cd/E12839_01/web.1111/b32511/configuring.htm#WSSEC1154) are some more details related to authentication and uses of web services. The details of the steps to be followed can be referred in the document below. Subscribe to **Download** the document to understand in details how to configure the policy.

[s2If current_user_can(access_s2member_level1)]

[Download](https://insightcrunch.com/wp-content/uploads/2022/09/Deploying-and-Configuring-Data-Relationship-Management-Web-Service-API.pdf) the Deployment and Configuration Guide to learn more on Data Relationship Management Web Services API.

The ultimate test will be to make sure the token name is visible in the WSDL url. If the attachment of the policy is done fine, it will reflect in the URL. Else there's another approach to manually attach the policy which is kind of a workaround and done only in exception scenarios, which we faced few months back.