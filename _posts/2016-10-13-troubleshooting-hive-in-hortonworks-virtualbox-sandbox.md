---
layout: post
title: "Troubleshooting Hive in Hortonworks Virtualbox Sandbox"
date: 2016-10-13
categories: ["Analytics"]
tags: ["Hadoop"]
excerpt: "Hive not working in Hortonworks sandbox? Common VirtualBox issues, service startup failures, and the fixes that get your Hadoop environment running."
image: "/assets/images/blog/blog-08.webp"
reading_time: 1
author: "Insight Crunch Team"
last_updated: 2026-03-29
---
While getting started with Hadoop, the [sandbox](https://www.cloudera.com/downloads/hortonworks-sandbox.html) provided by Hortonworks is an easy to use starting point. Once we download the Virtualbox, we can easily import it into our existing VirtualBox Manager. This is assuming we already have a [VM VirtualBox Manager](http://www.oracle.com/technetwork/server-storage/virtualbox/downloads/index.html) installed in our machine and the machine meets the minimum system requirements.

The VirtualBox will create a Virtual Disk Image in the path specified during the import process, I prefer to keep it in my external storage systems to save space since I have more than one such Virtual Boxes deployed.

![](/assets/images/blog/blog-08.webp)

So now that we have imported successfully and logged in using the default credentials **root** and **hadoop**, I get the below error when I try to use hive inside the sandbox.


There's a browser portal that can be used to access: http://127.0.0.1:4200/  
Here again I get stuck at the below screen for an indefinite amount of time. The screen freezes at the initialization step for a long time. It shows initializing but does not, and the CPU and memory consumption stays the same for a long period of time.


After shutting down the virtual box and re-logging in and again repeating the steps, finally the login worked fine. And I am able to enter the Hive prompt and execute few simple statements.


The create database for a sample database and create schema worked fine as expected.


Then creating a dummy sample table also worked fine inside the sandbox. Thus we are ready with Hive in a virtual box to try out our next steps.
