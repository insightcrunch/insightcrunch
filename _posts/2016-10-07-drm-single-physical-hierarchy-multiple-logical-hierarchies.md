---
layout: post
title: "DRM Single Physical Hierarchy Multiple Logical Hierarchies"
date: 2016-10-07
categories: ["Analytics"]
tags: ["Master Data Management"]
excerpt: "One DRM physical hierarchy, many logical views. How to configure multiple business perspectives from a single master hierarchy in Oracle DRM."
image: "/assets/images/blog/blog-12.webp"
reading_time: 3
author: "james-carter"
last_updated: 2026-03-29
---
The Oracle Data Relationship Management application provides tremendous flexibility in terms of managing the master data for an organization. It has amazing customizing options and integrability with other Oracle products that makes it even more useful.

 Here I will explain how easily we can solve a complex business requirement using DRM. The requirement is to have **3 different hierarchies for 3 different downstream applications** in a txt file for the same segment, say Account. So each downstream application will receive a different Account hierarchy from DRM - i.e. the parent child relationships will be different for the 3 applications.

![DRM Single Physical Hierarchy Multiple Logical Hierarchies](/assets/images/blog/blog-12.webp)
DRM Single Physical Hierarchy Multiple Logical Hierarchies

No, I am not going to create 3 different DRM versions and use exports to generate the text files from each version. I will be using DRM properties and a few custom formulae to achieve my goal **using a single DRM version**. Let's say the version is called V1. I have 3 Defined properties named as FlagHier1, FlagHier2, FlagHier3 - as you can see by the names, these will be used for flagging purposes to identify which DRM nodes will belong to which Hierarchy.

Then I do the usual steps of assigning the 3 properties to a property category and then I open the hierarchy. In the hierarchy, say I have defined the nodes as below:

In Version V1,  
   Nodes H1N1, H1N2, H1N3 are marked Yes in FlagHier1

   Nodes H2N1, H2N2, H2N3 are marked Yes in FlagHier2

   Nodes H3N1, H3N2, H3N3 are marked Yes in FlagHier3

They are arranged in a single physical hierarchy in version V1 in this parent-child relationship below:  
TopNode -> H1N1 -> H2N1 -> H1N2 -> H3N1 -> H1N3 -> H2N2 -> H3N2 -> H2N3 -> H3N3

In the output DRM exports, **each node must belong to it's correct parent** present in the corresponding hierarchy - parent name in the text file cannot be the name of a node belonging to a different hierarchy. This will be achieved by the below Calculated Properties - which uses the 3 Flag properties to calculate the parent names of a node.

Formula for **Hier1ParentName**:  
ParentPropValue(Custom.FindH1ParentName)

Formula for FindH1ParentName:  
AncestorProp(=,Custom.FlagHier1,Yes, 0,Custom.NodeName)

Formula for **Hier2ParentName**:  
ParentPropValue(Custom.FindH2ParentName)

Formula for FindH2ParentName:  
AncestorProp(=,Custom.FlagHier2,Yes, 0,Custom.NodeName)

Formula for **Hier3ParentName**:  
ParentPropValue(Custom.FindH3ParentName)

Formula for FindH3ParentName:  
AncestorProp(=,Custom.FlagHier3,Yes, 0,Custom.NodeName)

What the above formula does is, it will keep traversing the hierarchy starting from the Current Node (denoted by the boolean value 0 false - if you give 1 it will start at the top node which is not required in our case). **When it finds a "Yes"** value for the property specified, it will return the NodeName of that node, thus returning our desired parent name.

Now, I will need to create 3 exports as below using the different properties as mentioned:

For Hierarchy 1, child and parent will be: **NodeName, Hier1ParentName**  
Use Filter: Custom.FlagHier1=Yes

For Hierarchy 2, child and parent will be: **NodeName, Hier2ParentName**  
Use Filter: Custom.FlagHier2=Yes

For Hierarchy 3, child and parent will be: **NodeName, Hier3ParentName**  
Use Filter: Custom.FlagHier3=Yes

After running the first export (let's name the file Hier1.txt), I will see in my file 3 rows:  
H1N1,  
H1N2,H1N1  
H1N3,H1N2

Note how the second row is reflecting correct parent (H1N1) of H1N2 even though in the hierarchy it is H2N1. Similarly verify the other exports.

That's all! Pretty flexible right?