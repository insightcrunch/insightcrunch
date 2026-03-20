---
layout: post
title: "Type 2 Slowly Changing Dimension - How ORA_HASH (mis) fits in"
date: 2016-10-13
categories: ["Analytics"]
tags: ["Oracle Data Integrator"]
excerpt: "The ORA_HASH is one of my favorite functions to generate a hash value and use it for that record in a variety of ways. But there are certain circumstances where even an useful function like ORA_HASH ..."
image: "/assets/images/blog/blog-08.webp"
reading_time: 2
author: "Insight Crunch Team"
last_updated: 2026-03-15
---
The ORA_HASH is one of my favorite functions to generate a hash value and use it for that record in a variety of ways. But there are certain circumstances where even an useful function like ORA_HASH can have it's limitations. Let's take a look at how this function can act while implementing SCD2.

![](/assets/images/blog/blog-08.webp)

The above snapshot is from a table where SCD2 is implemented. The logic calculates the ORA_HASH value of each record using the values in columns Field 1, Field 2 and Field 3. If the value is new, it marks the existing record as "Active Flag" N, and inserts the new record as "Active Flag" Y. Thus we can see, for R2, the record having V6 is marked Y since on Day 5 the hash value has changed for this record id.

But note what happens for record R1. On Day 2, the hash value changed (from 100 to 200) due to a different value (V4) in Field 3 - so the new record got inserted with hash value 200. The new record gets flagged Y and the previous one gets tagged N. But on Day 3, when the Field 3 of R1 changes back to V3 (from V4),  it's hash value is again *back to 100*. Now, since the logic checks that if the new hash value (100) is different from the existing value (200) of the existing R1 record tagged Y, it will flag the record with hash value 200 as N. **Now**, I have to be careful to make sure the old hash value 100 which **already resides** with a flag of N do not interfere with the new record (**also having hash value 100**).


Several scenarios can happen in this case if not handled properly:

    1. We can have **duplicates** of the record (with hash value **100**) both flagged as **N** since the hash value is already existing  
    2. We can have **duplicates** of the record (with hash value **100**) both flagged as **Y** since the hash value is already existing and it's also the latest  
    3. The new record with old hash value 100 **might not get inserted at all** (most popular error) since hash value 100 is already existing - thus the full set of R1 stays tagged as N with no Y  
    4. The new record with old hash value 100 can get inserted but **subsequently can get tagged N** as the hash value is old - thus the full set of R1 stays tagged as N with no Y

All of these can be overcome with some additional logic to handle them. It's not that we cannot use ORA_HASH to implement SCD2, in fact it is very handy, just that little more caution is required to cover all the scenarios. Where do you like to use ORA_HASH in your codes?