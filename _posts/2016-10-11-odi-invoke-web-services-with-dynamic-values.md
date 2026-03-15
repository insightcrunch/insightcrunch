---
layout: post
title: "ODI Invoke Web Services with dynamic values"
date: 2016-10-11
categories: ["Analytics"]
tags: ["Oracle Data Integrator"]
excerpt: "The ODI Invoke Web Service utility is extremely handy and lots of users are already using it in their systems. The tool allows invoking an operation on a web service by the specified port number. ..."
image: "/assets/images/technology-industry-analysis-insightcrunch.webp"
reading_time: 3
author: "Insight Crunch Team"
last_updated: 2026-03-15
---
The ODI Invoke Web Service utility is extremely handy and lots of users are already using it in their systems. The tool allows invoking an operation on a web service by the specified port number. Once we provide with all the required parameters, we can use the ODI tool OdiInvokeWebService to meet our required web services operation. **Download** the ODI Invoke Web Service document at the end of this article.

![ODI Invoke Web Services with dynamic values](/assets/images/technology-industry-analysis-insightcrunch.webp)
ODI Invoke Web Services with dynamic values

There are credentials to be provided when we use the command OdiInvokeWebService, and the parameters we use as per Oracle's guidelines are as below:

-HTTP_USER=  
-HTTP_PASS=

The tricky part is what we do to encrypt or hide our credentials from all users who has access to the environment. Using OdiInvokeWebService as a tool in a Package will not help us hide it. Instead we will use an ODI Procedure to achieve this.

First we will create an ODI procedure, and select the technology **ODI Tools** in the Source tab. Next, in the Topology, create a new Data Server (say X, under File Technology), and save the username and password in this Topology Connection that you want to use when you call your Web Service. In the field "Host (Data Server)", provide the <>:<> details. It is interesting to note that the credentials even if entered incorrectly here will work here if you do "Test Connection". So we shouldn't get misleaded by it, instead we should make sure we can login to the Web Service or Analytics or BI Publisher URL using these credentials to make sure they are correct, and then use them in this Data Server X. In X, create a new Physical Schema with some path (you may or may not use it later) in the server. Then let's tag this Physical Schema to a Logical Schema Y in the default context Global.

Now in the ODI procedure, in the Target tab, select the Technology you used for creating the Data Server X (say **File**), and then select the corresponding Logical Schema Y. Then in the Source tab we can use the below in place of the credentials. It will automatically retrieve the values we have saved in the Data Server X.

- This will dynamically fetch the username  
- This will dynamically fetch the password  
- This will dynamically retrieve the instance URL

Thus, we can see, for Dev or Test or Prod, we do not need to change the code with the above 3 information every time. Instead, the same code will dynamically retrieve these details if we simply keep the Topology information updated with the instance specific details. The Topology thus provides incredible flexibility to Developer and Administrators and saves a lot of effort if used wisely. Do you have any ideas to use the Topology in more interesting ways?

The below document will give you details of how to invoke web services using ODI. Subscribe to **Download** the document.

[s2If current_user_can(access_s2member_level1)]

[Download](https://insightcrunch.com/wp-content/uploads/2022/09/OdiInvokeWebService.pdf) the guide here to learn more on how to use ODI to trigger web services.