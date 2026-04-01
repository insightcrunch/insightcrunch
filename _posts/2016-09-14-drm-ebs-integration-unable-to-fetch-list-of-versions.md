---
layout: post
title: "DRM EBS Integration - Unable to fetch list of Versions"
date: 2016-09-14
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "Oracle DRM and Oracle GL are integrated very closely in environments where both are present. Sometimes it happens that the concurrent program which is..."
image: "/assets/images/blog/blog-10.webp"
reading_time: 2
author: "choi-yuna"
last_updated: 2026-04-01
---
Oracle DRM and Oracle GL are integrated very closely in environments where both are present. Sometimes it happens that the concurrent program which is supposed to pull data from DRM errors out with the message "Unable to fetch list of versions".

[](http://imageshack.com/a/img924/1008/es5Qbd.png)There can be a few possibilities for this. Firstly, the **versions** should exist in DRM and the Allow Export flag should be set to 'True'. Then, if your **Weblogic** server is responding fine, you need to check if the **APIAdapter** URL is using the right port number. Also need to make sure the port is open and accessible. Often it happens due to an intermittent connectivity issue, sometimes the **firewall** check also need to be performed. If this is confirmed fine, then restart the IIS services to make sure we do not have any stale sessions.

The integration should work fine if the above checks and tests pass. In some rare cases, the error might still be present, and it can often become a headache. Check if the policy manager **wsm-pm** exists under Deployments in the Administration Console, it should be created as part of the extending domain during the configuration. If it is present, need to make sure it is in active status and showing status as 'OK'.

![DRM EBS Integration - Unable to fetch list of Versions](/assets/images/blog/blog-10.webp)
DRM EBS Integration - Unable to fetch list of Versions

Now, in Enterprise Manager, we need to verify if the wss_username_token_service_policy is correctly attached to the **EPMPolicySet** (found under Web Services - Policy Sets, refer screenshot below). If you get the below error after clicking Policy Sets, go back to extending the domain to create wsm-pm. Then try again.

Cannot locate policy manager query/update service. Policy manager service look up did not find a valid service, due to: Unable to connect to WS Policy Manager. <- oracle.wsm.policymanager.PolicyManagerException: WSM-02118 : The query service cannot be created. <- javax.naming.NameNotFoundException: While trying to lookup 'QueryService#oracle.wsm.policymanager.ejb.IStringQueryServiceRemote' didn't find subcontext 'QueryService#oracle'. Resolved ''; remaining name 'QueryService#oracle/wsm/policymanager/ejb/IStringQueryServiceRemote'


If there is still an issue in retrieving an already configured policy, in the Administration Console, navigate to **JDBC Data sources** as shown below, and select mds-owsm. In the **Connection Pool** tab, make sure it is having the correct Database URL. In the Enterprise Manager, in Services - Data Sources - Configuration - **Connection Pool**, need to make sure it is showing the correct TNS URL.


[](http://imageshack.com/a/img924/9341/kpVova.jpg)If required, make changes and then **restart the Manager Server**. We may also need to delete the **EPMPolicySet** and re-create the same just to make sure the attaching of the **wss_username_token_service_policy** is done correctly. If the issue is still not resolved, or you see some other message, let me know.