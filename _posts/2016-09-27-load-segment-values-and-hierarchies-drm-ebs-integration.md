---
layout: post
title: "Load Segment Values and Hierarchies - DRM EBS Integration"
date: 2016-09-27
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "The Oracle Data Relationship Management is one of the best in-class master data management tool by Oracle. It is often used along with Oracle E-Business..."
image: "/assets/images/blog/blog-36.webp"
reading_time: 4
author: "ian-fletcher"
last_updated: 2026-04-01
lang: en
---
The Oracle Data Relationship Management is one of the best in-class master data management tool by Oracle. It is often used along with Oracle E-Business Suite to maintain its master data due to the benefits and flexibility it offers.

To start with the integration, there is a list of values that needs to be configured in Oracle EBS, these will help DRM and EBS interact with each other as required:

- GL: DRM Username

- GL: DRM Property for Value Set Name

- GL: DRM Property to Allow Version Export

- GL: DRM Property to Allow Hierarchy Export

- GL: DRM API Adapter URL

- GL: DRM WSDL URL

- GL: DRM Template for Hierarchy Export

- GL: DRM Template for Version Export

Out of these, the API Adapter URL and the WSDL URL are the first pre-requisites to be checked that they are working fine. If these are not returning any data then it is time to bring them up first. The Value Set name refers to the names of the different segments that is present in my system. Since I have multiple segment hierarchies to integrate, I have multiple Value Set Names configured in EBS.

![a group of people looking at a laptop](/assets/images/blog/blog-36.webp)
Load Segment Values and Hierarchies - DRM EBS Integration

The program 'Load Segment Values and Hierarchies' when triggered with a specific Value Set name, calls the DRM Exports EBSValueSetExport and EBSHierarchyExport using the Data Relationship Management Web Service (which is why this needs to be up and running as the first sanity check) - the username used to login being the value used in the parameter "DRM Username". On successful completion of the program, the data is loaded into the staging interface tables GL.GL_DRM_SEGVALUES_INTERFACE and GL.GL_DRM_HIERARCHY_INTERFACE and subsequently into the EBS tables. **Download** the sample DRM EBS integration White Paper at the end of this article. This document will give you an idea of how the process works.

For smooth integration, I would like to summarize the **pre-requisites in EBS** for the process to work:

1. Apply the DRM integration patches 10632813 and 11659733  
2. Setup the values for all the GL profile parameters specified above in the list  
3. Store password for DRM user in FND_VAULT using below syntax:  
sqlplus apps/apps_pwd @$FND_TOP/sql/afvltput.sql ModuleName DRMUserName DRMUserPassword

Also here are the **pre-requisites in DRM** for the process to work:

1. Verify the WSDL and API Adapter URLs  
2. Verify the version to be exported has "Allow Export" property set to "True"  
3. Verify the version to be exported has the "Value Set Name" populated correctly  
4. Verify the DRM property name used for "Value Set Name" is the same as the value configured in EBS for the parameter "GL DRM Property for Value Set Name"  
5. Make sure the 3 users exist [as per this document](https://insightcrunch.com/2016/09/18/3-essential-sanity-checks-for-drm-ebs-integration/)  
6. Set up the external DB connection with the correct credentials having read-write access to the tables GL.GL_DRM_SEGVALUES_INTERFACE and GL.GL_DRM_HIERARCHY_INTERFACE  
7. Check if the DRM Exports EBSValueSetExport and EBSHierarchyExport exist fine  
8. Make sure the exports used in point 6 above are the same as tagged with the EBS parameters "GL DRM Template for Hierarchy Export" and "GL DRM Template for Version Export"

Now when I run the program "Load Segment Values and Hierarchies" for a specific value set name, it is important to note that I can only upsert (update insert) segment values and hierarchy data accessible using my General Ledger data access setting. Without the right access, I will not be able to provide the correct parameter to the program at all. The profile option which controls this access and makes sure the parameters appear correctly is called GL Data Access Set. Additionally, as a pre-requisite, the value sets must be already configured correctly in the table APPS.FND_FLEX_VALUE_SETS in the field FLEX_VALUE_SET_NAME.

Finally, once the program "Load Segment Values and Hierarchies" completes, here's the lines in the log file that indicates a successful run.

2016.10.07 16:35:55:-- Running DRM version export...  
2016.10.07 16:36:03:-- DRM Version Export finished successfully.  
2016.10.07 16:36:19:-- DRM Hierarchy Export finished successfully.  
2016.10.07 16:36:19:-- Calling PL/SQL API to import values from interface tables to FND ...  
2016.10.07 16:36:19:-- Logs from GL_DRM_IMPORT_PKG.gl_drm_import_process in FND_FILE section  
2016.10.07 16:36:23:-- Import process completed successfully

**Download** the DRM EBS Integration White Paper below. Subscribe to get access.

[s2If current_user_can(access_s2member_level1)]

This [document](https://insightcrunch.com/wp-content/uploads/2022/09/EBS-Integration-Oracle-DRM-White-Paper.pdf) will provide you with the details of how to achieve your integration.

Once the program completes, the data will flow to Oracle GL - the [data flow is explained in details here](https://insightcrunch.com/2016/09/23/drm-ebs-integration-fnd-flex-loader-value-updates/). That's all to this awesome integration process. Do you do your integration differently anyhow? Is there an easier or more flexible approach?