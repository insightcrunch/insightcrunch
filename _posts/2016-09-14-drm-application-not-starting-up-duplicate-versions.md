---
layout: post
title: "DRM Application not starting up - Duplicate Versions"
date: 2016-09-14
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "Oracle DRM won't start? Duplicate version entries in the repository may be the cause. How to diagnose and resolve this rare startup failure."
image: "/assets/images/blog/blog-38.webp"
reading_time: 1
author: "Insight Crunch Team"
last_updated: 2026-03-29
---
It has happened, though very rarely, that the DRM application refuses to start up. On further investigation it has revealed that the number of versions in the repository has been duplicated which had been preventing the application from starting up normally.

![DRM Application not starting up - Duplicate Versions](/assets/images/blog/blog-38.webp)
DRM Application not starting up - Duplicate Versions

The below query will provide the information of the version which is causing the issue:

select UPPER(C_ABBREV), count(*) FROM RM_VERSION GROUP BY UPPER(C_ABBREV) HAVING COUNT(*) > 1

To remove complete reference of a version in the repository, run the below scripts to remove all references to that version. Replace <> with your version name.

Delete from RM_NODE_MERGE where i_version_id in (<>);  
Delete from RM_MERGE_LOG where i_version_id in (<>);  
Delete from RM_NODE_PROP_GLOBAL where i_version_id in (<>);  
Delete from RM_NODE_PROP_LOCAL where i_version_id in (<>);  
Delete from RM_ACCESS_GROUP_PROP_GLOBAL where i_version_id in (<>);  
Delete from RM_ACCESS_GROUP_PROP_LOCAL where i_version_id in (<>);  
Delete from RM_ACCESS_GROUP_CTRL_HIER where i_version_id in (<>);  
Delete from RM_RELATIONSHIP where i_version_id in (<>);  
Delete from RM_VALIDATION_PROP_NODE where i_version_id in (<>);  
Delete from RM_VALIDATION_PROP_HIERARCHY where i_version_id in (<>);  
Delete from RM_VALIDATION_PROP_VERSION where i_version_id in (<>);  
Delete from RM_NODE where i_version_id in (<>);  
Delete from RM_USER_PROP_HIERARCHY where i_version_id in (<>);  
Delete from RM_USER_PROP_VERSION where i_version_id in (<>);  
Delete from RM_HIERARCHY_PROP where i_version_id in (<>);  
Delete from RM_PROPERTY_CTRL_HIER where i_version_id in (<>);  
Delete from RM_VERSION_PROP where i_version_id in (<>);  
Delete from RM_HIERARCHY where i_version_id in (<>);  
Delete from RM_DOMAIN_VERSION where i_version_id in (<>);  
Delete from RM_VERSION where i_version_id in (<>);  
Delete from RM_TRANSACTION_HISTORY where i_version_id in (<>)  and c_action NOT IN ('Add Version','Copy Version','Save Version','Delete Version');

Once this clean up is done, the application should start up normally without any issues. If it still gives error, let me know.