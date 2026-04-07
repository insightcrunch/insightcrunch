---
layout: post
title: "Essbase Shared Member vs Duplicate Member vs New Dimension ODI Roller Coaster"
date: 2017-11-05
categories: ["Analytics"]
tags: ["Oracle Data Integrator"]
excerpt: "The beginning of winter brought with it some exciting rides into the world of Oracle Data Integrator and Essbase. Feels lovely when things start to..."
image: "/assets/images/blog/blog-39.webp"
reading_time: 2
author: "andrew-price"
last_updated: 2026-04-01
lang: en
---
The beginning of winter brought with it some exciting rides into the world of Oracle Data Integrator and Essbase. Feels lovely when things start to unravel their beauty and prowess. After several sessions (more to come!) of brainstorming on Shared and Duplicate members, we came to a few interesting findings that can help us plan better.

![Essbase Shared Member vs Duplicate Member vs New Dimension ODI Roller Coaster](/assets/images/blog/blog-39.webp)
Essbase Shared Member vs Duplicate Member vs New Dimension ODI Roller Coaster

The “Duplicate” members are providing the below benefits:

- Allows same member to be used multiple times across altogether different dimensions. This is different from a “Shared” member where members need to be part of the same dimension.

- Besides the dimensions where we need Duplicate members, we can explicitly mark other dimensions as Unique which need not contain Duplicate members, thus ensuring integrity.

One drawback being once the outline is marked as enabled for Duplicate member we will be unable to rollback this setting! 

However, unlike a “Shared” member, some of the inconveniences that are caused by “Duplicate” members are:

- To get clarity on the dimension used, Smart View users will now have to select either the [fully qualified or ancestor-driven qualified name](http://www.oracle.com/webfolder/technetwork/tutorials/obe/hyp/DisplayDupesSV-1112/DisplayDupesSV-1112.html#s7) to ensure the correct member is selected. This defeats the aesthetics to an extent. Like [Parent].[Member].

- Existing calculations if used referring these members will need to be revisited to ensure they refer the correct required member from the corresponding dimension.

- The KM “[SQL to Hyperion Essbase (METADATA)](https://insightcrunch.com/2016/10/22/how-odi-ikm-sql-to-hyperion-essbase-metadata-influences-data-loading/)” doesn’t seem to like allow loading the duplicate alias for the duplicate member. The second dimension loaded latter suffers, the first dimension gets loaded fine. The first gets all the alias fine, the next run doesn’t get any alias for the members in the second dimension.

Considering all the above, the most effective solution now becomes a “new dimension”:

- We are going to compromise on space and performance as a drawback for this

- But now, we can have our distinct prefixing and naming convention for each member to make them identifiable at-a-glance

- Reference of any members in any calculations can stay intact without any ambiguity 

- The KM “[SQL to Hyperion Essbase (METADATA)](https://insightcrunch.com/2016/10/22/how-odi-ikm-sql-to-hyperion-essbase-metadata-influences-data-loading/)” is at its best again