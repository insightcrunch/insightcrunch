---
layout: post
title: "Unix find Lines and restructure file content"
page_title: "Unix find Lines containing specific string, then Cut and Insert these Lines after specific Lines containing another specific string"
date: 2018-12-19
categories: ["Analytics"]
tags: ["Unix"]
excerpt: "Unix text manipulation: find lines with a specific string, cut them, and insert after lines containing another string. Sed and awk solutions for ETL work."
image: "/assets/images/blog/blog-05.webp"
reading_time: 3
author: "Insight Crunch Team"
last_updated: 2026-03-23
---
The world of data integration and transformation gets more and more exciting every day. Where we have data fuelling intelligent applications, and transformations paving the way to create cleaner and leaner data. Let's dive in to some sorting and ordering transformations using shell scripting which will subsequently be triggered via ODI. We now have an interesting scenario where we have to identify all the records having the string "Parmesan Cheese", and after identifying the unique identifier, we have to cut this record and paste it under the immediate next record having the string "Filet Mignon" with the same unique identifier. Let's see a quick example below:

**Base Dataset:**  
**"X1","Y1","Z1****","****Parmesan Cheese****","****Yummy****","****Delicious"**  
**"X1","Y1","Z1","Grilled Salmon","Amazing","Tender"**  
**"X1","Y1","Z1","Filet Mignon","Juicy","Exquisite"**  
**"X2","Y2","Z2****","****Parmesan Cheese****","****Yummy****","****Delicious"**  
**"X2","Y2","Z2","Grilled Salmon","Amazing","Tender"**  
**"X2","Y2","Z2","Filet Mignon","Juicy","Exquisite"**

**Required Dataset:**  
**"X1","Y1","Z1","Grilled Salmon","Amazing","Tender"**  
**"X1","Y1","Z1","Filet Mignon","Juicy","Exquisite"**  
**"X1","Y1","Z1****","****Parmesan Cheese****","****Yummy****","****Delicious"**  
**"X2","Y2","Z2","Grilled Salmon","Amazing","Tender"**  
**"X2","Y2","Z2","Filet Mignon","Juicy","Exquisite"**

**"X2","Y2","Z2****","****Parmesan Cheese****","****Yummy****","****Delicious"**

The below Unix script will process the data as per our required logic. First it will create a lookup file *lookup.txt* containing all the records having "Parmesan Cheese".

**lookup.txt**  
**"X1","Y1","Z1****","****Parmesan Cheese****","****Yummy****","****Delicious"**  
**"X2","Y2","Z2****","****Parmesan Cheese****","****Yummy****","****Delicious"**

**In summary,** for each record being read in getEntireRecord from this lookup file, it will take the getUniqueRecIdentifier (**"X1","Y1","Z1****"**) and find the line number lineNumOfFiletMignon (3) of the "Filet Mignon" record having same identifier (**"X1","Y1","Z1"**). Now we know where to insert the "Parmesan Cheese" record getEntireRecord - the line number will be lineNumToInsertParmesanCheese which is the next line, so add one (3+1=4).

![](/assets/images/blog/blog-05.webp)

**Full logic:**

filename="file.txt"  
grep 'Parmesan Cheese' $filename > lookup.txt  
lkpfilename="lookup.txt"

while read -r line  
do  
readLine=$line  
getUniqueRecIdentifier="$(cut -c1-8 <<<"$readLine")"  
getEntireRecord="$(cut -c1-100 <<<"$readLine")"  
generateSameIdFiletMignon=$getUniqueRecIdentifier""',"Filet Mignon"'""  
lineNumOfFiletMignon="$(grep -n "$generateSameIdFiletMignon" $filename | head -n 1 | cut -d: -f1)"  
lineNumToInsertParmesanCheese=$((lineNumOfFiletMignon + 1))  
sed -i ''"$lineNumToInsertParmesanCheese"'i '"$getEntireRecord"'' file.txt  
lineNumToBeDeleted="$(grep -n "$getEntireRecord" $filename | head -n 1 | cut -d: -f1)"  
sed -i ''"$lineNumToBeDeleted"'d' file.txt  
done < "$lkpfilename"

rm $lkpfilename

**Detailed Explanation:** To identify lineNumOfFiletMignon we are using grep -n as seen below, with head -n 1 to get the first record for the specific combination, even though we know it will give only one record in our case. Then we have cut -d: -f1 to get the first column as the Unix line number.

lineNumOfFiletMignon="$(grep -n "$generateSameIdFiletMignon" $filename | head -n 1 | cut -d: -f1)"

Now we are adding one to lineNumOfFiletMignon to get lineNumToInsertParmesanCheese.

lineNumToInsertParmesanCheese=$((lineNumOfFiletMignon + 1))

Once we have identified lineNumToInsertParmesanCheese we can use sed -i then the line number where we want to insert our record followed by the record string and file name. Since we are iteratively storing the entire records iteratively in getEntireRecord from *lookup.txt*, we are using the same in the sed -i command.

sed -i ''"$lineNumToInsertParmesanCheese"'i '"$getEntireRecord"'' file.txt

After we do the above, we are going to have a duplicate original record of "Parmesan Cheese" that has to be deleted, this is calculated in lineNumToBeDeleted by using the entire record string getEntireRecord which was retrieved from *lookup.txt*.

lineNumToBeDeleted="$(grep -n "$getEntireRecord" $filename | head -n 1 | cut -d: -f1)"

The duplicate original line will be removed by the below sed -i command where we are providing the line number lineNumToBeDeleted to be deleted with d at the end for deletion, followed by the file name.

sed -i ''"$lineNumToBeDeleted"'d' file.txt

Then at the end we can safely delete our lookup file, which was happily storing all the "Parmesan Cheese" for us until now!

The above activity can also be done in Excel macro, but considering the amount of maintenance and scalability factors, we are clear which option to choose now.
