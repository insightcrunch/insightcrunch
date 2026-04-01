---
layout: post
title: "DRM Hierarchy Error - String was not recognized as a valid Boolean"
date: 2016-09-16
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "One of the errors that has been faced while using DRM is that the hierarchy gives an error while opening when some more columns are added in the default..."
image: "/assets/images/blog/blog-32.webp"
reading_time: 1
author: "alex-cunningham"
last_updated: 2026-04-01
---
One of the errors that has been faced while using DRM is that the hierarchy gives an error while opening when some more columns are added in the default hierarchy view. These additional columns are the Description of the nodes (available in the System Property Category) and some other calculated custom properties.

The error message is "String was not recognized as a valid Boolean".

![DRM Hierarchy Error - String was not recognized as a valid Boolean](/assets/images/blog/blog-32.webp)
DRM Hierarchy Error - String was not recognized as a valid Boolean

The error was so new that it took a lot of time to figure out the exact root cause of the issue. Finally it was identified that it is due to some characters used in the properties which is sometimes not compatible with the browser compatibility settings.

So after logging into DRM, open the hierarchy giving the issue, then set the default view to Options --> View By --> Default, the hierarchies will start opening fine.