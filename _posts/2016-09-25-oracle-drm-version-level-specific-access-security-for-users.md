---
layout: post
title: "Oracle DRM Version Level Specific Access Security for Users"
date: 2016-09-25
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "Security in Oracle Data Relationship Management is of immense significance in situations where I do not want to give all the application users the full..."
image: "/assets/images/blog/blog-87.webp"
reading_time: 1
author: "david-thornton"
last_updated: 2026-04-01
lang: en
---
Security in Oracle Data Relationship Management is of immense significance in situations where I do not want to give all the application users the full visibility of all the data present. DRM provides the feature to restrict visibility of the existing DRM data at user-level which is amazing and provides the admin a lot of flexibility to work with.

[](http://imageshack.com/a/img924/2394/tAYMfL.jpg)The feature that enables this called DRM Node Access Groups. Say I want to give access to User U1 access to the DRM Version V1, but not to Version V2 and V3. My first step is to create a new Node Access Group, say AG1. I will add U1 to AG1, save and close.

![Oracle DRM Version Level Specific Access Security for Users](/assets/images/blog/blog-87.webp)
Oracle DRM Version Level Specific Access Security for Users

Then after opening version V1, as I navigate to Nodes -> Assign -> Node Access, I can see the name AG1 under the categories 'Limb Access' which I need to set to the level of access I want to give (example Read, Edit, Insert, etc). Similarly for 'Leaf Access'. Then after Saving the changes, it is time to test how it's working for the User U1.

Now if I log in with the credentials for User U1, despite the presence of 3 different versions, I can only see the Version V1. This thus achieves my goal of implementing user level version level leaf/limb level security for users with tremendous amount of flexibility.