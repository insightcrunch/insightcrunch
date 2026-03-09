---
layout: post
title: "DRM Web Client Internal Server Error"
date: 2016-09-17
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "The DRM Web Client is usually very responsive and seldom it gives a server down error. But the below error was observed recently which was quite baffling. The application was running fine, the ..."
image: "/assets/images/technology-industry-analysis-insightcrunch.webp"
reading_time: 1
author: "Insight Crunch Team"
---

The DRM Web Client is usually very responsive and seldom it gives a server down error. But the below error was observed recently which was quite baffling. The application was running fine, the Weblogic and Shared Services were up, the SSO configuration was in place perfectly.

The error message when trying to access the DRM Web Client page is as below:

    "The page cannot be displayed because an internal server error has occurred."

![Oracle DRM Web Client Internal Server Error](/assets/images/technology-industry-analysis-insightcrunch.webp)
Oracle DRM Web Client Internal Server Error

On further analysis it has been found that there is a setting in the Shared Services Console that enables the DRM application to authenticate with SSO only if that is enabled. If and only if this is enabled then CSS integration via SSO will be able to authenticate an LDAP user. The parameter is named as 'Enable SSO Compatibility' in Shared Services Console which after being enabled the authentication starts working fine.