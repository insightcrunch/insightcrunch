---
layout: post
title: "ODI Trigger Essbase MaxL Dynamically with no hard-coding"
date: 2016-10-15
categories: ["Analytics"]
tags: ["Oracle Data Integrator"]
excerpt: "Trigger Essbase MaxL scripts dynamically from ODI without hard-coding. Variable-driven cube operations that adapt to different environments automatically."
image: "/assets/images/blog/blog-08.webp"
reading_time: 2
author: "Insight Crunch Team"
last_updated: 2026-03-23
---
The Oracle Data Integrator tool provides a flexible option, though customized, to call and execute MaxL scripts to perform various operations on our Essbase cubes. And more importantly, this approach using ODI is completely independent of the environment we are going to run our ODI codes in. A simple control table will contain the server information that will be referred by the ODI code to run the MaxL scripts in that specific Essbase instance.

![ODI Trigger Essbase MaxL Dynamically with no hard-coding](/assets/images/blog/blog-08.webp)
ODI Trigger Essbase MaxL Dynamically with no hard-coding

So the first step is to create my **control table** with all the different values that will be used by my ODI code. This control table will be present in all the instances like Development Test Production, each with it's own unique values as applicable for that environment. Usually the server admins will be having all these information and the table might only have read access in Development instance. In higher instance the developers might not be allowed to have read access on this table since it will contain sensitive information like the user credentials. The below are the parameters that will be stored in the control table:

    1. Server Directory (where I will find my startMAXL.sh script)  
    2. MaxL Directory (where I have saved my custom MaxL scripts)  
    3. The name of my Essbase Application  
    4. The name of my Essbase Database (maybe same as Essbase Application name)  
    5. Essbase Server Name  
    6. Essbase Login User Name with full privilege  
    7. Essbase Login Password for the above user

Now, once I have all the required values, it is time to start creating my **ODI package**. I will need 7 variables to fetch the values of the above 7 parameters. Then I will use an ODI command with the below syntax to run my MaxL script.

. #SERVER_DIR/startMAXL.sh #MAXL_DIR/Aggregate.mxl #APP #DB #SERVER_NAME #USER #PW

The MaxL script now will need to start with the below lines to accept the above values:

    /* Initialize variables */  
    SET app =$1;  
    SET db =$2;  
    SET esbs =$3;  
    SET user =$4;  
    SET pwd =$5;

    /* Login to the server */  
    login "$user" "$pwd" on "$esbs";  
    iferror 'loginFailed';

Then the MaxL script can proceed to do it's own activities (like executing calculations) on the cube as usual. That's all to this short flexible process! How do you prefer to execute your MaxL scripts?