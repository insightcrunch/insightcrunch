---
layout: post
title: "DRM Error - File Does not Exist"
date: 2016-09-15
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "Hitting 'File Does not Exist' in Oracle DRM? This error during export/import operations has a specific cause and a straightforward resolution."
image: "/assets/images/blog/blog-46.webp"
reading_time: 1
author: "marcus-hall"
last_updated: 2026-03-29
---
One of the most interesting issues faced till today is the below message while during any Export Import or Query activities in the DRM Web Client:

"File Does not Exist"

[](http://imageshack.com/a/img922/8788/QUL2Ky.jpg)So how does it exactly appear. Say I am logged into the DRM Web Client. I need to run a DRM Export which will generate a txt file or write to a database table. When I run the Export it gives this error, but it runs fine in other DRM environments. Note that I do not have any existing file in the destination export directory which might cause this issue. Same thing happens for a DRM Import, when I try to import a version export for example, it gives this error. When I got this import error, it clearly indicates something wrong at the server directory level. Even when creating new Queries this error message appears.

![DRM Error - File Does not Exist](/assets/images/blog/blog-46.webp)
DRM Error - File Does not Exist

On further investigation, it was found that every activity in the DRM Web Client creates *.tmp files in the directory C:\Windows\Temp. This has a very specific naming convention and over a very long period of time, the application struggles to create tmp files when the directory C:\Windows\Temp is almost filled up. On moving all the *.tmp files from C:\Windows\Temp to a folder in the Desktop, this issue got resolved.