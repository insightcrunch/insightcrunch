---
layout: post
title: "Excel Pivot Table Count Distinct Values Challenge Overcoming"
date: 2018-03-18
categories: ["Uncategorized"]
tags: []
excerpt: "The use of Microsoft Excel automatically becomes a powerful tool to dive deep into the sea of data and form perceptions while generating interesting data..."
image: "/assets/images/blog/blog-57.webp"
reading_time: 2
author: "insight-crunch-team"
last_updated: 2026-04-01
---
The use of Microsoft Excel automatically becomes a powerful tool to dive deep into the sea of data and form perceptions while generating interesting data models. Recently while in the middle of such an exciting activity came a moment where we were stuck with a not-so-latest version of Excel, and thus we are missing the oh-so-lovely built-in Count Distinct formula for a Pivot Table. Yes it's a deal-breaker, when we cannot avoid a pivot, and also desperately don't want to create a different standalone table or formula for a calculation to count the number of distinct values for a combination.

![](/assets/images/blog/blog-57.webp)

Say, we need to find **for each Attrib_1 values (Column B) how many distinct IDs (column A) exist**. Thus we can see AX and BY are repeated in rows 5 and 9, and so we need to tag their duplicate occurrences with a 0.

In the first approach, column E, we check if the row number of each row equals the first occurrence of the unique combination (Column D) we are looking for:

=SUM(IF(ROW([@Combination])MATCH([@Combination],D:D,0),0,1))

In the second approach, column F, we check if the counted value for the unique combination (Column D) we are looking for exceeds 1, in which case it's a duplicate and tagged 0. The range of this formula increases like $D$2:D3 $D$2:D4 $D$2:D5 as it goes down and thus the countif function can calculate from the top down. This needs tad more effort to type and create than the former.

=IF(COUNTIF($D$2:D2,D2)>1,0,1)

Now if we select values from the purple buttons above we can see how vibrantly the pivot chart tells us that the count of distinct combinations for X is 3 (i.e. AX, BX, CX), Y is 2 (i.e. BY, AY), and Z is 1 (i.e. CZ). Once the data is ready, we can use ODI or any integration tool to further process this intelligent dataset.