---
layout: post
title: "Troubleshooting Hive in Hortonworks Virtualbox Sandbox"
date: 2016-10-13
categories: ["Analytics"]
tags: ["Hadoop"]
excerpt: "While getting started with Hadoop, the [sandbox](https://www.cloudera.com/downloads/hortonworks-sandbox.html) provided by Hortonworks is an easy to use starting point. Once we download the ..."
image: "/assets/images/technology-industry-analysis-insightcrunch.webp"
reading_time: 1
author: "Insight Crunch Team"
---

While getting started with Hadoop, the [sandbox](https://www.cloudera.com/downloads/hortonworks-sandbox.html) provided by Hortonworks is an easy to use starting point. Once we download the Virtualbox, we can easily import it into our existing VirtualBox Manager. This is assuming we already have a [VM VirtualBox Manager](http://www.oracle.com/technetwork/server-storage/virtualbox/downloads/index.html) installed in our machine and the machine meets the minimum system requirements.

The VirtualBox will create a Virtual Disk Image in the path specified during the import process, I prefer to keep it in my external storage systems to save space since I have more than one such Virtual Boxes deployed.

![](https://insightcrunch.com/wp-content/uploads/2022/08/326B7FF8-F610-40CB-8FBF-A55F682EA8AF.png)

So now that we have imported successfully and logged in using the default credentials **root** and **hadoop**, I get the below error when I try to use hive inside the sandbox.

![](https://insightcrunch.com/wp-content/uploads/2022/08/93C83EE5-6BD4-44EE-9CF2-2BE18C80A379.png)

There's a browser portal that can be used to access: http://127.0.0.1:4200/  
Here again I get stuck at the below screen for an indefinite amount of time. The screen freezes at the initialization step for a long time. It shows initializing but does not, and the CPU and memory consumption stays the same for a long period of time.

![](https://insightcrunch.com/wp-content/uploads/2022/08/98EC209C-1BE1-42B2-A535-92E87DDB849E.png)

After shutting down the virtual box and re-logging in and again repeating the steps, finally the login worked fine. And I am able to enter the Hive prompt and execute few simple statements.

![](https://insightcrunch.com/wp-content/uploads/2022/08/29B611D1-1A90-491D-B084-182888714EEE-1024x345.png)

The create database for a sample database and create schema worked fine as expected.

![](https://insightcrunch.com/wp-content/uploads/2022/08/895A9D25-2FED-46F7-A502-163AA312F781.png)

![](https://insightcrunch.com/wp-content/uploads/2022/08/F8D58C71-6DD0-4117-AB3A-C79A823626E0.png)

![](https://insightcrunch.com/wp-content/uploads/2022/08/5C3D5503-4FC4-4215-9302-8F5AF1303FE7.png)

Then creating a dummy sample table also worked fine inside the sandbox. Thus we are ready with Hive in a virtual box to try out our next steps.

![Troubleshooting Hive in Hortonworks Virtualbox Sandbox](https://insightcrunch.com/wp-content/uploads/2016/10/pexels-photo-3808819.jpeg)
Troubleshooting Hive in Hortonworks Virtualbox Sandbox