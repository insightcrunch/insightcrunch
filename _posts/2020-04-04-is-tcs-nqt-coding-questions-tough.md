---
layout: post
title: "Is TCS NQT Coding Questions tough?"
date: 2020-04-04
categories: ["Industry"]
tags: ["TCS"]
excerpt: "Is TCS NQT coding tough? Honest difficulty analysis of programming questions, language-wise comparison, and what level of preparation actually clears it."
image: "/assets/images/blog/blog-07.webp"
reading_time: 100
author: "Insight Crunch Team"
last_updated: 2026-03-15
render_with_liquid: false
---
{% raw %}
## Overview

Tata Consultancy Services conducts the National Qualifier Test (NQT) that is taken by hundreds of thousands of candidates every year. The TCS NQT exam is the gateway to get recruited in one of the many distinguished profiles in TCS. Based on your background and skill set you then get allocated to a project. As you keep learning, you can also switch between different profiles based on how you perform and the existing demand. However succeeding in the TCS NQT exam requires rigorous practice.

If you meet the TCS NQT eligibility criteria, you will be provided with an exam date. Int he TCS NQT exam you will be asked questions based on various topics like numerical ability, logical reasoning, verbal skills, and coding knowledge. The TCS NQT exam is a mixture of basic and advanced questions. Thus you need to make sure you have strong foundation of each of the concepts. Extensive practice will help you prepare for the TCS NQT exam comprehensively. I have created a dynamic set of practice exams below that you can attempt unlimited times and filter by topic, difficulty, and your expertise.

![TCS NQT Coding Questions Aptitude Syllabus Eligibility Practice](/assets/images/blog/blog-07.webp)
TCS NQT Coding Questions

## TCS NQT Coding Questions

The TCS NQT exam consists of a coding section where candidates are evaluated based on their coding skills. You will be presented with a couple of coding questions during the TCS NQT exam that you have to solve in about an hour. If you have a good grasp over C, C++, Python, Java, or Perl it will be easy for you to build up your skills further. Having robust clarity and clear concepts on at least one programming language is essential to score well in the TCS NQT exam. Before you finalize your code during the exam, I suggest evaluate your code for boundary value analysis. I would also want your code to be tested for all different types of values as parameters. In addition, I want to see a strong exception handling logic in your code.

The TCS NQT Coding questions need months of preparation. I recommend you practice a variety of resources and try to keep your codes scalable and flexible. I do not want you to rewrite multiple lines of a code if I want you to add a new logic. The better you get at handling different functions in the different languages, the more powerful codes you can formulate in lesser time. I would also suggest you practice writing the same program in different programming languages that you are comfortable in. This will help fine tune your skills even further. I will share some of the most popular TCS NQT coding questions below, you must be a Subscriber to access them.

TCS NQT Coding Question 1
[s2If current_user_can(access_s2member_level1)]

**Question**: An automobile company manufactures both a two wheeler (TW) and a four wheeler (FW). A company manager wants to make the production of both types of vehicle according to the given data below:

- 1st data, Total number of vehicle (two-wheeler + four-wheeler)=v

- 2nd data, Total number of wheels = W

The task is to find how many two-wheelers as well as four-wheelers need to manufacture as per the given data.

**Example :**

**Input :  
**200  -> Value of V  
540   -> Value of W

**Output :  
**TW =130 FW=70

**Explanation:  
**130+70 = 200 vehicles  
(70*4)+(130*2)= 540 wheels

**Constraints :**

- 2<=W

- W%2=0

- V<W

Print “INVALID INPUT” , if inputs did not meet the constraints.

**The input format for testing   
**The candidate has to write the code to accept two positive numbers separated by a new line.

- First Input line – Accept value of V.

- Second Input line- Accept value for W.

**The output format for testing **

- Written program code should generate two outputs, each separated by a single space character(see the example)

- Additional messages in the output will result in the failure of test case

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;
int main ()
{
    int v, w;
    cin >> v >> w;
    float x = ((4 * v) - w) / 2;
    if ((w & 1) || w < 2 || w <= v)
    {
        cout << "INVALID INPUT";
        return 0;
    }
    cout << "TW=" << x << " " << "FW=" << v - x;

}
```

**Java Code**:

```
import java.util.*;
public class Main
{
    public static void main(String[] args)
    {
             Scanner sc=new Scanner(System.in);
             int v=sc.nextInt();
             int w=sc.nextInt();
             float res=((4*v)-w)/2;
             if(w>=2 && (w%2==0) && v<w)              
             System.out.println("TW= "+(int)(res)+" FW= "+(int)(v-res));
             else                
             System.out.println("INVALID INPUT");
    }
}
```

**Python Code**:

```
v=5
w=6
if (w&1)==1 or w<2 or w<=v:
    print("INVALID INPUT")
else:
    x=((4*v) -w)//2
    print("TW={0} FW={1}".format(x,v-x))
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 2
[s2If current_user_can(access_s2member_level1)]

**Question**: Given a string S (input consisting) of ‘*’ and ‘#’. The length of the string is variable. The task is to find the minimum number of ‘*’ or ‘#’ to make it a valid string. The string is considered valid if the number of ‘*’ and ‘#’ are equal. The ‘*’ and ‘#’ can be at any position in the string.  
**Note :** The output will be a positive or negative integer based on number of ‘*’ and ‘#’ in the input string.

- (*>#): positive integer

- (#>*): negative integer

- (#=*): 0

**Example 1:  
****Input 1:**

- ###***   -> Value of S

**Output :**

- 0   → number of * and # are equal

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;
int main()
{
    string s="Hello";
    int a=0,b=0;
    getline(cin,s);
    for(auto i:s)
        if(i=='#') 
            a++;
        else if(i=='*')
            b++;
    cout<<b-a;
}
```

**Java Code**:

```
import java.util.*;
public class Main
{
 	public static void main(String[] args)
 	{
        		
        String str="Hello";
        int count1=0,count2=0;
        for(int i=0;i< str.length();i++)
    	{
            if(str.charAt(i)=='*')
        		count1++;##
            else if(str.charAt(i)=='#')
         		count2++;
    		}
        System.out.println(count1-count2);
	}
}
```

**Python Code**:

```
s="Hello"
a=0
b=0
for i in s:
    if i=='*':
        a+=1
    elif i=='#':
        b+=1
print(a-b)
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 3
[s2If current_user_can(access_s2member_level1)]

**Question**: Given an integer array Arr of size N the task is to find the count of elements whose value is greater than all of its prior elements.

**Note :** 1st element of the array should be considered in the count of the result.

**For example,  
**Arr[]={7,4,8,2,9}  
As 7 is the first element, it will consider in the result.  
8 and 9 are also the elements that are greater than all of its previous elements.  
Since total of  3 elements is present in the array that meets the condition.  
Hence the output = 3.  
**Example 1:**

**Input   
**5 -> Value of N, represents size of Arr  
7-> Value of Arr[0]  
4 -> Value of Arr[1]  
8-> Value of Arr[2]  
2-> Value of Arr[3]  
9-> Value of Arr[4]

**Output :  
**3

**Example 2:  
**5   -> Value of N, represents size of Arr  
3  -> Value of Arr[0]  
4 -> Value of Arr[1]  
5 -> Value of Arr[2]  
8 -> Value of Arr[3]  
9 -> Value of Arr[4]

**Output :   
**5

**Constraints**

- 1<=N<=20

- 1<=Arr[i]<=10000

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;
int main()
{
    int n,c=0,a,m=INT_MIN;
    cin>>n;
    while(n--)
    {
        cin>>a;
        if(a>m)
        {
            m=a;
            c++;
        }
    }
    cout<< c;
}
```

**Java Code**:

```
import java.util.*;
class Main
{
     public static void main(String[] args)
     {
        Scanner sc=new Scanner(System.in);
        int n=sc.nextInt();
        int arr[]=new int[n];
        for(int i=0;imax)
                {
                    max=arr[i];
                    count++;
                }
            }
            System.out.println(count);
     }
}
```

**Python Code**:

```
import sys
n=int(input())
c=0
m=-sys.maxsize-1
while n:
    n-=1
    a=int(input())
    if a>m:
        m=a
        c+=1
print(c)
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 4
[s2If current_user_can(access_s2member_level1)]

**Question**: A parking lot in a mall has RxC number of parking spaces. Each parking space will either be  empty(0) or full(1). The status (0/1) of a parking space is represented as the element of the matrix. The task is to find index of the prpeinzta row(R) in the parking lot that has the most of the parking spaces full(1).

**Note :  
**RxC- Size of the matrix  
Elements of the matrix M should be only 0 or 1.

**Example 1:**

**Input :  
**3   -> Value of R(row)  
3    -> value of C(column)  
[0 1 0 1 1 0 1 1 1] -> Elements of the array M[R][C] where each element is separated by new line.  
**Output :  
**3  -> Row 3 has maximum number of 1’s

**Example 2:**

**Input :  
**4 -> Value of R(row)  
3 -> Value of C(column)  
[0 1 0 1 1 0 1 0 1 1 1 1] -> Elements of the array M[R][C]  
**Output :  
**4  -> Row 4 has maximum number of 1’s

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;
int main()
{
    int r,c,a,sum=0,m=INT_MIN,in=0;
    cin>>r>>c;
    for(int i=0;i>a;
            sum+=a;
        }
        if(sum>m)
        {
            m=sum;
            in=i+1;
        }
        sum=0;
    }
    cout<< in;
}
```

**Java Code**:

```
import java.util.*;
class Main
{
     public static void main(String[] args)
     {
        Scanner sc=new Scanner(System.in);
        int row=sc.nextInt();
        int col=sc.nextInt();
        int arr[][]=new int[row][col];
        for(int i=0;i< row;i++)
            for(int j=0;j< col;j++)
                arr[i][j]=sc.nextInt();
        
              int max=0,count=0,index=0;
              for(int i=0;i< row;i++)
                { 
                    count=0;
                    for(int j=0;j< col;j++)
                    {
                        if(arr[i][j]==1)
                        count++;
                    }
                        if(count>max)
                    {
                        max=count;
                        index=i+1;
                    }
                 }
        System.out.println(index);
    }
}
```

**Python Code**:

```
r=int(input())
c=int(input())
sum=0
m=0
id=0
for i in range(r):
    for j in range(c):
        sum+=int(input())
    if sum>m:
        m=sum
        id=i+1
    sum=0
print(id)
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 5
[s2If current_user_can(access_s2member_level1)]

**Question**: A party has been organised on cruise. The party is organised for a limited time(T). The number of guests entering (E[i]) and leaving (L[i]) the party at every hour is represented as elements of the array. The task is to find the maximum number of guests present on the cruise at any given instance within T hours.

**Example 1:  
****Input :**

- 5    -> Value of T

- [7,0,5,1,3]  -> E[], Element of E[0] to E[N-1], where input each element is separated by new line 

- [1,2,1,3,4]   -> L[], Element of L[0] to L[N-1], while input each element is separate by new line.

**Output :  
**8     -> Maximum number of guests on cruise at an instance.

**Explanation:**

**1st hour:**  
Entry : 7 Exit: 1  
No. of guests on ship : 6

**2nd hour :**  
Entry : 0 Exit : 2  
No. of guests on ship : 6-2=4

**Hour 3:  
**Entry: 5 Exit: 1  
No. of guests on ship : 4+5-1=8

**Hour 4:  
**Entry : 1 Exit : 3  
No. of guests on ship : 8+1-3=6

**Hour 5:  
**Entry : 3 Exit: 4  
No. of guests on ship: 6+3-4=5  
Hence, the maximum number of guests within 5 hours is 8.

**Example 2:  
****Input:  
**4  -> Value of T  
[3,5,2,0]   -> E[], Element of E[0] to E[N-1], where input each element is separated by new line.  
[0,2,4,4]    -> L[], Element of L[0] to L[N-1], while input each element in separated by new line

**Output:  
**6  
Cruise at an instance

**Explanation:  
**Hour 1:  
Entry: 3 Exit: 0  
No. of guests on ship: 3

Hour 2:  
Entry : 5 Exit : 2  
No. of guest on ship: 3+5-2=6

Hour 3:  
Entry : 2 Exit: 4  
No. of guests on ship: 6+2-4= 4

Hour 4:  
Entry: 0  Exit : 4  
No. of guests on ship : 4+0-4=0

Hence, the maximum number of guests within 5 hours is 6.  
The input format for testing  
The candidate has to write the code to accept 3 input.  
First input- Accept  value for number of T(Positive integer number)  
Second input- Accept T number of values, where each value is separated by a new line.  
Third input- Accept T number of values, where each value is separated by a new line.  
The output format for testing  
The output should be a positive integer number or a message as given in the problem statement(Check the output in Example 1 and Example 2)

**Constraints:**

- 1<=T<=25

- 0<= E[i] <=500

- 0<= L[i] <=500

**Java Code**:

```
import java.util.*;
class Main
{
    public static void main (String[]args)
    {
        Scanner sc = new Scanner (System.in);
        int t = sc.nextInt ();
        int e[] = new int[t];
        int l[] = new int[t];
        for (int i = 0; i < t; i++)
            e[i] = sc.nextInt ();
            
            for (int i = 0; i < t; i++)
                l[i] = sc.nextInt ();
                
                int max = 0, sum = 0;
            for (int i = 0; i < t; i++)
            {
                sum += e[i] - l[i];
                max = Math.max (sum, max);
            }
        System.out.println (max);
}
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 6
[s2If current_user_can(access_s2member_level1)]

**Question**: At a fun fair, a street vendor is selling different colours of balloons. He sells N number of different colours of balloons (B[]). The task is to find the colour (odd) of the balloon which is present odd number of times in the bunch of balloons.

**Note: **If there is more than one colour which is odd in number, then the first colour in the array which is present odd number of times is displayed. The colours of the balloons can all be either upper case or lower case in the array. If all the inputs are even in number, display the message “All are even”.

**Example 1:**

- 7  -> Value of N

- [r,g,b,b,g,y,y]  -> B[] Elements B[0] to B[N-1], where each input element is sepārated by ṉew line.

**Output :**

- r -> [r,g,b,b,g,y,y]  -> “r” colour balloon is present odd number of times in the bunch.

**Explanation:  
**From the input array above:

- r: 1 balloon 

- g: 2 balloons

- b:  2 balloons

- y : 2 balloons  
Hence , r is only the balloon which is odd in number.

**Example 2:  
****Input:**

- 10 -> Value of N

- [a,b,b,b,c,c,c,a,f,c] -> B[], elements B[0] to B[N-1] where input each element is separated by new line.

**Output :  
**b-> ‘b’ colour balloon is present odd number of times in the bunch.

**Explanation:  
**From the input array above:

- a: 2 balloons

- b: 3 balloons 

- c: 4 balloons 

- f: 1 balloons 

Here, both ‘b’ and ‘f’ have odd number of balloons. But ‘b’ colour balloon occurs first.  
Hence , b is the output.

**Input Format for testing  
**The candidate has to write the code to accept: 2 input 

- First input: Accept value for number of N(Positive integer number).

- Second Input : Accept N number of character values (B[]), where each value is separated by a new line.

**Output format for testing  
**The output should be a single literal (Check the output in example 1 and example 2)

**Constraints:**

- 3<=N<=50

- B[i]={{a-z} or {A-Z}}

**Java Code**:

```
import java.util.*;
class Main
{
    public static void main (String[]args)
    {
        Scanner sc = new Scanner (System.in);
        int n = sc.nextInt ();
        char arr[] = new char[n];
        for (int i = 0; i < n; i++)
            arr[i] = sc.next ().charAt (0);
        int lower[] = new int[26];
        int upper[] = new int[26];
        for (int i = 0; i < n; i++)
        {
            if ((arr[i] >= 'A') && (arr[i] <= 'Z'))
            upper[arr[i] - 'A']++;
            else if ((arr[i] >= 'a') && (arr[i] <= 'z'))
            lower[arr[i] - 'a']++;
        }
        boolean flag = false;
        char ch = '\0';
        for (int i = 0; i < n; i++)
        {
            if ((arr[i] >= 'A') && (arr[i] <= 'Z'))
            {
                if (upper[arr[i] - 'A'] % 2 == 1)
                    {
                        ch = (char) (arr[i]);
                        flag = true;
                        break;
                    }
            }
            else if ((arr[i] >= 'a') && (arr[i] <= 'z'))
            {
                if (lower[arr[i] - 'a'] % 2 == 1)
                {
                    ch = (char) (arr[i]);
                    flag = true;
                    break;
                }
        
            }
        
        }
        if (flag == true)
            System.out.println (ch);
        else
            System.out.println ("All are even");
    }
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 7
[s2If current_user_can(access_s2member_level1)]

**Question**: There is a JAR full of candies for sale at a mall counter. JAR has the capacity N, that is JAR can contain maximum N candies when JAR is full. At any point of time. JAR can have M number of Candies where M<=N. Candies are served to the customers. JAR is never remain empty as when last k candies are left. JAR if refilled with new candies in such a way that JAR get full.  
Write a code to implement above scenario. Display JAR at counter with available number of candies. Input should be the number of candies one customer can order at point of time. Update the JAR after each purchase and display JAR at Counter.

Output should give number of Candies sold and updated number of Candies in JAR.

If Input is more than candies in JAR, return: “INVALID INPUT”  
**Given,   
**N=10, where N is NUMBER OF CANDIES AVAILABLE  
K =< 5, where k is number of minimum candies that must be inside JAR ever.  
**Example 1:(N = 10, k =< 5)**

**Input Value   
**3  
**Output Value  
**NUMBER OF CANDIES SOLD : 3  
NUMBER OF CANDIES AVAILABLE : 7

**Example : (N=10, k<=5)**

**Input Value  
**0  
**Output Value  
**INVALID INPUT NUMBER OF  
CANDIES LEFT : 10

**C Code**:

```
#include <stdio.h>   
int main()  
{
	int n=10, k=5;
	int num;
	scanf("%d",&num);
	if(num>=1 && num<=5)
	{
    		printf("NUMBER OF CANDIES SOLD : %d\n",num);
    		printf("NUMBER OF CANDIES LEFT : %d",n-num);
	}
	else
	{
    		printf("INVALID INPUT\n");
    		printf("NUMBER OF CANDIES LEFT : %d",n);
	}
	return 0;
} 
```

**C++ Code**:

```
#include <iostream>
using namespace std;
int main()
{
	int n=10, k=5;
	int num;
	cin>>num;
	if(num>=1 && num<=5)
	{
    	cout<< "NUMBER OF CANDIES SOLD : "<<num<<"\n";
    	cout<<"NUMBER OF CANDIES LEFT : "<<n-num;
	}
	else
	{
    	cout<<"INVALID INPUT\n";
    	cout<<"NUMBER OF CANDIES LEFT : "<<n;
	}
	return 0;
}
```

**Java Code**:

```
import java.util.Scanner;
class Main{
    public static void main(String[] args) {
   	 int n = 10, k = 5;
   	 int num;
   	 Scanner sc = new Scanner(System.in);
   	 num = sc.nextInt();
   	 if(num >= 1 && num <= 5) {
   		 System.out.println("NUMBER OF CANDIES SOLD : " + num);
   		 System.out.print("NUMBER OF CANDIES LEFT : " + (n - num));
   	 } else {
   		 System.out.println("INVALID INPUT");
   		 System.out.print("NUMBER OF CANDIES LEFT : " + n);
   	 }
    }
}
```

**Python Code**:

```
total_candies = 10
no_of_candies = int(input())
if no_of_candies in range(1, 6):
	print('No. of Candies Sold:',no_of_candies)
	print('No. of Candies Left:',total_candies-no_of_candies)
else:
	print("Invalid Input")
	print('No. of Candies Left:',total_candies)
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 8
[s2If current_user_can(access_s2member_level1)]

**Question**: Selection of MPCS exams include a fitness test which is conducted on ground. There will be a batch of 3 trainees, appearing for running test in track for 3 rounds. You need to record their oxygen level after every round. After trainee are finished with all rounds, calculate for each trainee his average oxygen level over the 3 rounds and select one with highest oxygen level as the most fit trainee. If more than one trainee attains the same highest average level, they all need to be selected.

**Display the most fit trainee (or trainees) and the highest average oxygen level.**

**Note:**

- **The oxygen value entered should not be accepted if it is not in the range between 1 and 100.**

- If the calculated maximum average oxygen value of trainees is below 70 then declare the trainees as unfit with meaningful message as “All trainees are unfit.

- Average Oxygen Values should be rounded.

**Example 1:  
****INPUT VALUES  
**95  
92  
95  
92  
90  
92  
90  
92  
90

**OUTPUT VALUES  
**Trainee Number : 1  
Trainee Number : 3

**Note:  
**Input should be 9 integer values representing oxygen levels entered in order as

**Round 1**

- Oxygen value of trainee 1

- Oxygen value of trainee 2

- Oxygen value of trainee 3

**Round 2**

- Oxygen value of trainee 1

- Oxygen value of trainee 2

- Oxygen value of trainee 3

**Round 3**

- Oxygen value of trainee 1

- Oxygen value of trainee 2

- Oxygen value of trainee 3

**Output must be in given format as in above example. For any wrong input final output should display “INVALID INPUT”**

**C Code**:

```
#include <stdio.h>    
int main()  
{
	int trainee[3][3];
	int average[3] = {0};
	int i, j, max=0;
	for(i=0; i<3; i++)
	{
    		for(j=0; j<3; j++)
    		{
        		scanf("%d",&trainee[i][j]);
        		if(trainee[i][j]<1 || trainee[i][j]>100)
        		{
            		trainee[i][j] = 0;
        		}
    		}
	}
	for(i=0; i<3; i++)
	{
    		for(j=0; j<3; j++)
    		{
        			average[i] = average[i] + trainee[j][i];
    		}
    		average[i] = average[i] / 3;
	}
	for(i=0; i<3; i++) { if(average[i]>max)
    		{
        			max = average[i];
    		}
	}
	for(i=0; i<3; i++)
	{
    		if(average[i]==max)
    		{
        			printf("Trainee Number : %d\n",i+1);
    		}
    		if(average[i]<70)
    		{
        			printf("Trainee is Unfit");
    		}
	}
	return 0;
}
```

**C++ Code**:

```
#include <iostream>
using namespace std;
int main()  
{
	int trainee[3][3];
	int average[3] = {0};
	int i, j, max=0;
	for(i=0; i<3; i++)
	{
        	for(j=0; j<3; j++) { cin>>trainee[i][j];
                	if(trainee[i][j]<1 || trainee[i][j]>100)
                	{
                    	trainee[i][j] = 0;
            	}
        	}
	}
	for(i=0; i<3; i++)
	{
        	for(j=0; j<3; j++)
        	{
                	average[i] = average[i] + trainee[j][i];
        	}
        	average[i] = average[i] / 3;
	}
	for(i=0; i<3; i++) { if(average[i]>max)
        	{
                	max = average[i];
        	}
	}
	for(i=0; i<3; i++)
	{
        	if(average[i]==max)
        	{
                	cout<<"Trainee Number : "<<i+1<<"\n";
        	}
        	if(average[i]<70)
        	{
                	cout<<"Trainee is Unfit";
        	}
	}
	return 0;
} 
```

**Java Code**:

```
import java.util.Scanner;
class Main {
    public static void main(String[] args) {
   	 int[][] trainee = new int[3][3];
   	 int[] average = new int[3];
   	 int max = 0;
   	 Scanner sc = new Scanner(System.in);
   	 for(int i = 0; i < 3; i++) {
   		 for(int j = 0; j < 3; j++) {
   			 trainee[i][j] = sc.nextInt();
   			 if(trainee[i][j] < 1 || trainee[i][j] > 100) {
   				 trainee[i][j] = 0;
   			 }
   		 }
   	 }
   	 for(int i = 0; i < 3; i++) {
   		 for(int j = 0; j < 3; j++) {
   			 average[i] = average[i] + trainee[j][i];
   		 }
   		 average[i] = average[i] / 3;
   	 }
   	 for(int i = 0; i < 3; i++) { if(average[i] > max) {
   			 max = average[i];
   		 }
   	 }
   	 for(int i = 0; i < 3; i++) {
   		 if(average[i] == max) {
   			 System.out.println("Trainee Number : " + (i + 1));
   		 }
   		 if(average[i] <70) {
   			 System.out.print("Trainee is Unfit");
   		 }
   	 }
    }

}
```

**Python Code**:

```
trainee = [[],[],[],[]]
for i in range(3):
	for j in range(3):
    		trainee[i].append(int(input()))
    		if (trainee[i][-1]) not in range(1,101):
        			print("invalid input")
for i in range(3):
	trainee[3].append((trainee[2][i]+trainee[1][i]+trainee[0][i])//3)
maximum = max(trainee[3])
for i in range(3):
	if trainee[3][i] < 70 :
    		print("Trainee {0} is unfit".format(i+1))
	elif trainee[3][i] == maximum:
    		print("Trainee Number: ",i+1)
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 9
[s2If current_user_can(access_s2member_level1)]

**Question**: A washing machine works on the principle of Fuzzy System, the weight of clothes put inside it for washing is uncertain But based on weight measured by sensors, it decides time and water level which can be changed by menus given on the machine control area.   

For low level water, the time estimate is 25 minutes, where approximately weight is between 2000 grams or any nonzero positive number below that. 

For medium level water, the time estimate is 35 minutes, where approximately weight is between 2001 grams and 4000 grams.

For high level water, the time estimate is 45 minutes, where approximately weight is above 4000 grams.

Assume the capacity of machine is maximum 7000 grams

Where approximately weight is zero, time estimate is 0 minutes.

Write a function which takes a numeric weight in the range [0,7000] as input and produces estimated time as output is: “OVERLOADED”, and for all other inputs, the output statement is

“INVALID INPUT”.

Input should be in the form of integer value –

Output must have the following format –

Time Estimated: Minutes

**Example:  
Input value**  
2000  
**Output value  
**Time Estimated: 25 minutes

**C Code**:

```
#include <stdio.h>
void calculateTime(int n)
{
    if(n==0)
        printf("Time Estimated : 0 Minutes");
    else if(n>0 && n<=2000) 
        printf("Time Estimated : 25 Minutes"); 
    else if(n>2000 && n<=4000) 
        printf("Time Estimated : 35 Minutes"); 
    else if(n>4000 && n<=7000)
        printf("Time Estimated : 45 Minutes");
    else
        printf("INVALID INPUT");
}
int main()
{
    int machineWeight;
    scanf("%d",&machineWeight);
    calculateTime(machineWeight);
    return 0;
}
```

**C++ Code**:

```
#include<bits/stdc++.h>
using namespace std;
void calculateTime (int n)
{
if (n == 0)
cout << "Time Estimated : 0 Minutes";

else if (n > 0 && n <= 2000)
cout << "Time Estimated : 25 Minutes";

else if (n > 2000 && n <= 4000)
cout << "Time Estimated : 35 Minutes";

else if (n > 4000 && n <= 7000)
cout << "Time Estimated : 45 Minutes";

else
cout << "INVALID INPUT";
}

int main ()
{
int Weight;
cin >> Weight;

calculateTime (Weight);
return 0;

}
```

**Python Code**:

```
n = int(input())
if n==0:
    print("Time Estimated : 0 Minutes")
elif n in range(1,2001):
    print("Time Estimated : 25 Minutes")
elif n in range(2001,4001):
    print("Time Estimated : 35 Minutes")
elif n in range(4001,7001):
    print("Time Estimated : 45 Minutes")
else:
    print("INVALID INPUT")
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 10
[s2If current_user_can(access_s2member_level1)]

**Question**: The Caesar cipher is a type of substitution cipher in which each alphabet in the plaintext or messages is shifted by a number of places down the alphabet.  
For example,with a shift of 1, P would be replaced by Q, Q would become R, and so on.  
To pass an encrypted message from one person to another, it is first necessary that both parties have the ‘Key’ for the cipher, so that the sender may encrypt and the receiver may decrypt it.  
Key is the number of OFFSET to shift the cipher alphabet. Key can have basic shifts from 1 to 25 positions as there are 26 total alphabets.  
As we are designing custom Caesar Cipher, in addition to alphabets, we are considering numeric digits from 0 to 9. Digits can also be shifted by key places.  
For Example, if a given plain text contains any digit with values 5 and keyy =2, then 5 will be replaced by 7, “-”(minus sign) will remain as it is. Key value less than 0 should result into “INVALID INPUT”

**Example 1:   
**Enter your PlainText: All the best  
Enter the Key: 1

The encrypted Text is: Bmm uif Cftu

Write a function CustomCaesarCipher(int key, String message) which will accept plaintext and key as input parameters and returns its cipher text as output.

**C Code**:

```
#include <stdio.h>
int main()
{
    char str[100];
    int key, i=0, left;
    printf("Enter your plain text : ");
    scanf("%[^\n]s",str);
    printf("Enter the key : ");
    scanf("%d",&key);
    if(key==0)
    {
        printf("INVALID INPUT");
    }
    else
    {
        while(str[i]!='\0')
        {
            //printf("%d\n", str[i]);
            if(str[i]>=48 && str[i]<=57)
            {
                if(str[i]+key<=57)
                {
                    str[i] = str[i] + key;
                }
                else
                {
                    left = (str[i] + key) - 57;
                    str[i] = 47 + left;
                }   
            }
            else if(str[i]>=65 && str[i]<=90)
            {
                if(str[i]+key<=90)
                {
                    str[i] = str[i] + key;
                }
                else
                {
                    left = (str[i] + key) - 90;
                    str[i] = 64 + left;
                }  
            }
            else if(str[i]>=97 && str[i]<=122)
            {
                if(str[i]+key<=122)
                {
                    str[i] = str[i] + key;
                }
                else
                {
                    left = (str[i] + key) - 122;
                    str[i] = 96 + left;
                } 
            }
            i++;
        }
        printf("The encrypted text is : %s",str);
   }
   return 0;
}
```

**C++ Code**:

```
#include<bits/stdc++.h>
using namespace std;
void ceaser(string s, int key)
{
    if(key==0)
    {
        printf("INVALID INPUT");
    }
    else
    {
        for(int i=0; i< s.size(); i++)
        {
        
            if(isdigit(s[i]))
            {
                if(s[i]+key<=57)
                {
                    s[i] = s[i] + key;
                }
                else
                {
                    int left = (s[i] + key) - 57;
                    s[i] = 47 + left;
                }
            }
            else if(s[i] >=65 && s[i]<=90)
            {
                if(s[i]+key<=90)
                {
                    s[i] = s[i] + key;
                }
                else
                {
                    int left = (s[i] + key) - 90;
                    s[i] = 64 + left;
                }
            }
            else if(s[i] >=97 && s[i]<=122)
            {
                if(s[i]+key <=122)
                {
                    s[i] = s[i] + key;
                }
                else
                {
                    int left = (s[i] + key) - 122;
                    s[i] = 96 + left;
                }
            }
        
        }
    }
    cout <<"The Encrypted Text is:"<< s;
}

int main ()
{
    string s;
    int key;
    
    cout<<"Enter the plain text :";
    getline(cin, s);
    
    cout<<"\nEnter the key :";
    cin>>key;
    
    ceaser(s, key);
    return 0;

}
```

**Python Code**:

```
def ceaser(text,key):
    result = ""
   # transverse the plain text
    for i in range(len(text)):
        char = text[i]
      # Encrypt uppercase characters in plain text
        if (char.isupper()):
            result += chr((ord(char) + key-65) % 26 + 65)
      # Encrypt lowercase characters in plain text
        elif (char.islower()):
            result += chr((ord(char) + key - 97) % 26 + 97)
        elif(char.isdigit()):
            result += str(int(char) + key)
        elif(char == '-'):
            result += '-'
        elif (char.isspace()):
            result += " "
    return result
#check the above function
text = input("Enter your plain text:")
key = int(input("Enter the key:"))
print(ceaser(text,key))
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 11
[s2If current_user_can(access_s2member_level1)]

**Question**: We want to estimate the cost of painting a property. Interior wall painting cost is Rs.18 per sq.ft. and exterior wall painting cost is Rs.12 per sq.ft.

**Take input as**  
1. Number of Interior walls  
2. Number of Exterior walls  
3. Surface Area of each Interior 4. Wall in units of square feet  
Surface Area of each Exterior Wall in units of square feet

**If a user enters zero  as the number of walls then skip Surface area values as User may don’t  want to paint that wall.**

**Calculate and display the total cost of painting the property  
Example 1:  
**6  
3  
12.3  
15.2  
12.3  
15.2  
12.3  
15.2  
10.10  
10.10  
10.00  
Total estimated Cost : 1847.4 INR  
**Note:** Follow in input and output format as given in above example

**C Code**:

```
#include <stdio.h>
int main()
{
    int ni,ne,i=0;
    float int_p=18,ext_p=12,cost=0,temp;
    scanf("%d %d",&ni,&ne);
    if(ni<0 || ne<0 )
    {
        printf("INVALID INPUT");
    }
    else if(ni==0 && ne==0)
    {
        printf("Total estimated Cost : 0.0");
    }
    else
    {
        for(i=0;i<ni;i++)
        {
            scanf("%f",&temp);
            cost+= int_p*temp;
        }
        for(i=0;i<ne;i++)
        {
            scanf("%f",&temp);
            cost+= ext_p*temp;
        }
        printf("Total estimated Cost : %.1f",cost);
    }
    return 0;
}
```

**C++ Code**:

```
#include <iostream>
using namespace std;
int main()
{
    int ni,ne,i=0;
    float int_p=18,ext_p=12,cost=0,temp;
    scanf("%d %d",&ni,&ne);
    if(ni<0 || ne<0 )
    {
        cout<<"INVALID INPUT";
    }
    else if(ni==0 && ne==0)
    {
        cout<<"Total estimated Cost : 0.0";
    }
    else
    {
        for(i=0;i<ni;i++)
        {
            cin>>temp;
            cost+= int_p*temp;
        }
        for(i=0;i<ne;i++)
        {
            cin>>temp;
            cost+= ext_p*temp;
        }
        cout<<"Total estimated Cost : "<<cost;      
    }
    return 0;
}
```

**Python Code**:

```
interior_walls = int(input())
exterior_walls = int(input())
if interior_walls:
    int_walls = []
    for i in range(interior_walls):
        int_walls.append(float(input()))
if exterior_walls:
ext_walls = []
for i in range(exterior_walls):
ext_walls.append(float(input()))
if exterior_walls < 0 or interior_walls < 0:
print(“Invalid Input”)
exit()
if exterior_walls and interior_walls:
print("Total estimated Cost : ",(sum(int_walls)*18+sum(ext_walls)*12),"INR")
else:
if exterior_walls:
print("Total estimated Cost : ",sum(ext_walls)*12,"INR")
elif interior_walls:
print("Total estimated Cost : ",sum(int_walls)*18,"INR")
else:
print("Total estimated Cost : 0.0 INR")
```

**Java Code**:

```
import java.util.Scanner;
class Main {
    public static void main(String[] args) {
       int ni, ne, i = 0;
       float intP = 18, extP = 12, cost = 0, temp;
       Scanner sc = new Scanner(System.in);
       ni = sc.nextInt();
       ne = sc.nextInt();
       if(ni < 0 || ne < 0) {
           System.out.print("INVALID INPUT");
       } else if(ni == 0 && ne == 0) {
           System.out.print("Total estimated Cost : 0.0");
       } else {
           for(i = 0; i < ni; i++) {
               temp = sc.nextFloat();
               cost += intP * temp;
           }
           for(i = 0; i < ne; i++) {
               temp = sc.nextFloat();
               cost += extP * temp;
           }
           System.out.printf("Total estimated Cost : %.1f", cost);
       }
    }
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 12
[s2If current_user_can(access_s2member_level1)]

**Question**: A City Bus is a Ring Route Bus which runs in circular fashion.That is, Bus once starts at the Source Bus Stop, halts at each Bus Stop in its Route and at the end it reaches the Source Bus Stop again.  
If there are n  number of Stops and if the bus starts at Bus Stop 1, then after nth Bus Stop, the next stop in the Route will be Bus Stop number 1 always.  
If there are n stops, there will be n paths.One path connects two stops. Distances (in meters) for all paths in Ring Route is given in array Path[] as given below:  
Path = [800, 600, 750, 900, 1400, 1200, 1100, 1500]  
Fare is determined based on the distance covered from source to destination stop as  Distance between Input Source and Destination Stops can be measured by looking at values in array Path[] and fare can be calculated as per following criteria:

- If d =1000 metres, then fare=5 INR

- (When calculating fare for others, the calculated fare containing any fraction value should be ceiled. For example, for distance 900n when fare initially calculated is 4.5 which must be ceiled to 5)

Path is circular in function. Value at each index indicates distance till current stop from the previous one. And each index position can be mapped with values at same index in BusStops [] array, which is a string array holding abbreviation of names for all stops as-  
**“THANERAILWAYSTN” = ”TH”, “GAONDEVI” = “GA”, “ICEFACTROY” = “IC”, “HARINIWASCIRCLE” = “HA”, “TEENHATHNAKA” = “TE”, “LUISWADI” = “LU”, “NITINCOMPANYJUNCTION” = “NI”, “CADBURRYJUNCTION” = “CA”**

Given, n=8, where n is number of total BusStops.  
**BusStops = [ “TH”, ”GA”, ”IC”, ”HA”, ”TE”, ”LU”, ”NI”,”CA” ]**

Write a code with function getFare(String Source, String Destination) which take Input as source and destination stops(in the format containing first two characters of the Name of the Bus Stop) and calculate and return travel fare.

Example 1:  
**Input Values  
**ca  
Ca  
**Output Values**  
INVALID OUTPUT

Example 2:  
**Input Values  
**NI  
HA  
**Output Values  
**23.0 INR  
**Note:** Input and Output should be in format given in example.  
Input should not be case sensitive and output should be in the format INR.

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;
int main() 
{
    string s , d;
    cin>>s>>d;
    transform(s.begin(),s.end() , s.begin(),::toupper);
    transform(d.begin(),d.end() , d.begin(),::toupper);
    string arrs[8] = {"TH" , "GA", "IC" , "HA" , "TE", "LU" ,"NI","CA"};
    float arr[8]={800,600,750,900,1400,1200,1100,1500};
    float res=0;
    int st ,ed;
    for(int i=0;i<8;i++)
    {
        if(s==arrs[i])
        st=i;
        if(d==arrs[i])
        ed=i;
    }
    if(st==ed)
    {
        cout<< " INVALID INPUT";
        return 0;
    }
    else
    {
        int i=st+1;
        cout<< i;
        while(i!=ed+1)
        {
            res+=(arr[i]);
            i=(i+1)%8;
        }
        cout<<(ceil)(res*0.005);
        return 0;
    }
}
```

**Python Code**:

```
import math
def getFare(source,destination):
    route=[ [ "TH", "GA", "IC", "HA", "TE", "LU", "NI", "CA"],
    [800,600,750,900,1400,1200,1100,1500]
        ]
    fare = 0.0
    if not (source in route[0] and destination in route[0]):
        print("Invalid Input")
        exit()
    if route[0].index(source) < route[0].index(destination):
        for i in range(route[0].index(source),route[0].index(destination)+1):
            fare+=route[1][i]
    elif route[0].index(destination) < route[0].index(source):
        for i in range(route[0].index(source)+1,len(route[0])):
            fare+=route[1][i]
        for i in range(0,route[0].index(destination)+1):
            fare+=route[1][i]
    return float(math.ceil(fare*0.005))
source = input()
destination = input()
fare = getFare(source,destination)
if fare == 0:
print("Invalid Input")
else:
print(fare)
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 13
[s2If current_user_can(access_s2member_level1)]

**Question**: There are total n number of Monkeys sitting on the branches of a huge Tree. As travelers offer Bananas and Peanuts, the Monkeys jump down the Tree. If every Monkey can eat k Bananas and j Peanuts. If total m number of Bananas and p number of Peanuts are offered by travelers, calculate how many Monkeys remain on the Tree after some of them jumped down to eat.  
At a time one Monkeys gets down and finishes eating and go to the other side of the road. The Monkey who climbed down does not climb up again after eating until the other Monkeys finish eating.  
Monkey can either eat k Bananas or j Peanuts. If for last Monkey there are less than k Bananas left on the ground or less than j Peanuts left on the ground, only that Monkey can eat Bananas(<k) along with the Peanuts(<j).  
Write code to take inputs as n, m, p, k, j and return  the number of Monkeys left on the Tree.  
    Where, n= Total no of Monkeys  
        k= Number of eatable Bananas by Single Monkey (Monkey that jumped down last may get less than k Bananas)  
        j = Number of eatable Peanuts by single Monkey(Monkey that jumped down last may get less than j Peanuts)  
        m = Total number of Bananas  
        p  = Total number of Peanuts  
Remember that the Monkeys always eat Bananas and Peanuts, so there is no possibility of k and j having a value zero

**Example 1:**  
Input Values      
20  
2  
3  
12  
12

**Output Values**  
Number of  Monkeys left on the tree:10  
**Note:** Kindly follow  the order of inputs as n,k,j,m,p as given in the above example. And output must include  the same format  as in above example(Number of Monkeys left on the Tree:)  
For any wrong input display INVALID INPUT

**C Code**:

```
#include <stdio.h>
int main ()
{
    int n, k, j, m, p;
    float atebanana = 0.0, atepeanut = 0.0;
    scanf ("%d %d %d %d %d", &n, &k, &j, &m, &p);
    if (n < 0 || k < 0 || j < 0 || m < 0 || p < 0)
    {
        printf ("INVALID INPUT");
    }
    else
    {
        if (k > 0)
        {
            atebanana = (float) (m / k);
	        m = m % k;
	}
        if (j > 0)
	{
            atepeanut = (float) (p / j);
	        p = p % j;
	}
        n = n - atebanana - atepeanut;
        if ((m != 0) || (p != 0))
	    n = n - 1;
        printf ("Number of Monkeys left on the Tree:%d", n);
    }
    return 0;
}
```

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;
int main()
{
    int n,k,j,m,p;
    float atebanana=0.0, atepeanut=0.0;
    cin>>n>>k>>j>>m>>p;
    if(n<0 or k<0 or j<0 or m<0 or p<0)
    {
        cout<<"INVALID INPUT";
    }
    else
    {
        if(k>0)
        {
            atebanana =(float)(m/k);
            m=m%k;
        }
        if(j>0)
        {
            atepeanut =(float) (p/j);
            p=p%j;
        }
        n=n-atebanana-atepeanut;
        if((m!=0) || (p!=0))
            n=n-1;
        cout<<"Number of Monkeys left on the Tree: "<<n;
    }
    return 0;
}
```

**Java Code**:

```
import java.util.*;
 class Monkeys 
{
    public static void main(String []args)
    {
        Scanner sc = new Scanner (System.in);
        int n = sc.nextInt();
        int k = sc.nextInt();
        int j = sc.nextInt();
        int m = sc.nextInt();
        int p = sc.nextInt();
        int atebanana=0 ,atepeanut=0;
        if( n<0 && k<0 || j<0 || m<0 || p<0)
        {
            System.out.println("Invalid Input");
        }
        else
        {
            if(k>0)
            {
                 atebanana =m/k;
                 m=m%k;
            }
            if(j>0)
            {
                atepeanut = p/j; 
                p=p%j; 
            }
            n=n-atebanana-atepeanut;
            if((m!=0) || (p!=0))
                n=n-1;
            System.out.println("Number of Monkeys left on the Tree: "+n);
        }
    }
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 14
[s2If current_user_can(access_s2member_level1)]

**Question**: Chain Marketing Organization has has a scheme for income generation, through which its members generate income for themselves. The scheme is such that suppose A joins the scheme and makes R and V to join this scheme  then A is Parent Member of R and V who are child Members. When any member joins the scheme then the parent gets total commission of 10% from each of its child members.  
Child members receive commission of 5% respectively. If a Parent member does not have any member joined under him, then he gets commission of 5%.  
Take name of the members joining the scheme as input.  
Display how many members joined the scheme including parent member.Calculate the Total commission gained by each members in the scheme. The fixed amount for joining the scheme is Rs.5000 on which commission will be generated  
**SchemeAmount = 5000**

**Example 1:**** When there are more than one child members   
****Input : (Do not give input prompts.Accept values as follows. )  
**Amit                     //Enter parent Member as this  
Y                           //Enter Y if  Parent member has child members otherwise enter N  
Rajesh,Virat        //Enter names of child members of Amit in comma separated  
**Output:(Final Output must be in format given below.**)  
TOTAL MEMBERS:3  
COMISSION DETAILS  
Amit: 1000 INR  
Rajesh :250 INR  
Virat: 250 INR

**Example 2: When there is only one child member in the hierarchy  
Input :  
**Amit  
Y  
Rajesh  
**Output:  
**Total Members: 2   
Comission Details  
Amit: 500 INR  
Rajesh: 250 INR

**C++ Code**:

```
using namespace std;
int main()
{
    string par;
    cin >> par;
    string x;
    cin >> x;
    if (x == "N") {
        cout << "TOTAL MEMBERS:1\n";
        cout << "COMISSION DETAILS\n";
        cout << par << ":250 INR\n";
    } else {
        string child;
        cin >> child;
        vectorv;
        string temp = "";
        for (int i = 0; i < child.length(); i++) {
            if (child[i] == ',') {
                v.push_back(temp);
                temp = "";
            }
            else  if (child[i] != ' ')
                temp += child[i];
        }
        v.push_back(temp);
        cout << "TOTAL MEMBERS:" << v.size() + 1 << "\n";
        cout << "COMISSION DETAILS\n";
        cout << par << ":" << v.size() * 500 << " INR\n";
        for (auto a : v) {
            cout << a << ":" << "250 INR\n";
      }
   }
}
```

**Python Code**:

```
parent = input()
Yes_No = input()
if Yes_No == "N":
    print("TOTAL MEMBERS:1\nCOMMISSION DETAILS\n{0}: 250 INR".format(parent))
elif Yes_No == "Y":
    child=list(map(str,input().split(",")))
    print("TOTAL MEMBERS:{}".format(len(child)+1))
    print("COMMISSION DETAILS \n{0}:{1} INR".format(parent,len(child)*500))
    for i in child:
        print("{0}:250 INR".format(i))
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 15
[s2If current_user_can(access_s2member_level1)]

**Question**: **FULLY AUTOMATIC VENDING MACHINE – **dispenses your cuppa on just press of button. A vending machine can serve range of products as follows:

Coffee

- Espresso Coffee

- Cappuccino Coffee

- Latte Coffee

Tea

- Plain Tea

- Assam Tea

- Ginger Tea

- Cardamom Tea

- Masala Tea

- Lemon Tea

- Green Tea

- Organic Darjeeling Tea

Soups 

- Hot and Sour Soup

- Veg Corn Soup

- Tomato Soup

- Spicy Tomato Soup

Beverages

- Hot Chocolate Drink

- Badam Drink

- Badam-Pista Drink

**Write a program to take input for main menu & sub menu and display the name of sub menu selected in the following format (enter the first letter to select main menu):**

**Welcome to CCD   
****Enjoy your   
****Example 1:**

**Input:  
**c  
1  
**Output  
**Welcome to CCD!  
Enjoy your Espresso Coffee!

**Example 2:  
Input:  
**t  
9  
**Output  
**INVALID OUTPUT!

**C Code**:

```
#include <stdio.h> 
int main()
{
    char c[3][20]={"Espresso Coffee","Cappuccino Coffee","Latte Coffee"};

    char t[8][30]={"Plain Tea","Assam Tea","Ginger Tea","Cardamom Tea","Masala Tea","Lemon Tea","Green Tea","Organic Darjeeling Tea"};

    char s[4][20]={"Hot and Sour Soup","Veg Corn Soup","Tomato Soup","Spicy Tomato Soup"};

    char b[3][20]={"Hot Chocolate Drink","Badam Drink","Badam-Pista Drink"};

    char str[]="Welcome to CCD!\nEnjoy your ";

    char ch;

    int  item, i;

    scanf("%c",&ch);

    scanf("%d",&item);

    if(ch=='c')

    {

        for(i=0; i<3; i++)

        {

            if(item==i+1)

            {

                printf("Welcome to CCD!\nEnjoy your %s!",c[i]);

                break;

            }

        }

        if(i==3)

        {

            printf("INVALID OPTION!");

        }

    }

    else if(ch=='t')

    {

        for(i=0; i<8; i++)

        {

            if(item==i+1)

            {

                printf("Welcome to CCD!\nEnjoy your %s!",t[i]);

                break;

            }

        }

        if(i==8)

        {

            printf("INVALID OPTION!");

        }

    }

    else if(ch=='s')

    {

        for(i=0; i<4; i++)

        {

            if(item==i+1)

            {

                printf("Welcome to CCD!\nEnjoy your %s!",s[i]);

                break;

            }

        }

        if(i==4)

        {

            printf("INVALID OPTION!");

        }

    }

    else if(ch=='b')

    {

        for(i=0; i<3; i++)

        {

            if(item==i+1)

            {

                printf("Welcome to CCD!\nEnjoy your %s!",b[i]);

                break;

            }

        }

        if(i==3)

        {

            printf("INVALID OPTION!");

        }

    }

    else

    {

        printf("INVALID INPUT!");

    }

    return 0;

}
```

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;

int main()
{
string c[3]={"Espresso Coffee","Cappuccino Coffee","Latte Coffee"};

string t[8]={"Plain Tea","Assam Tea","Ginger Tea","Cardamom Tea","Masala Tea","Lemon Tea","Green Tea","Organic Darjeeling Tea"};

string s[4]={"Hot and Sour Soup","Veg Corn Soup","Tomato Soup","Spicy Tomato Soup"};

string b[3]={"Hot Chocolate Drink","Badam Drink","Badam-Pista Drink"};

char ch;
int n;

string res = "";

cin>>ch>>n;

if(ch=='c' and n <= 3)
res = c[n-1];

else if(ch=='t' and n <= 8)
res = t[n-1];

else if(ch=='s' and n <= 4)
res = s[n-1];

else if(ch=='b' and n <= 3)
res = b[n-1];

else res = "Invalid Input";

if(res != "Invalid Input" )
cout<<"Welcome to CCD!\nEnjoy your "<<res;

else cout<<res;

return 0;
}
```

**Python Code**:

```
menu = [['Espresso Coffee','Cappuucino Coffee','Latte Coffee'], ['Plain Tea',
'Assam Tea','Ginger Tea','Cardamom Tea','Masala Tea','Lemon Tea','Green Tea',

'Organic Darjeeling Tea'], ['Hot and Sour Soup','Veg Corn Soup','Tomato Soup',

'Spicy Tomato Soup'], ['Hot Chocolate Drink', 'Badam Drink',

'Badam-Pista Drink']]

m = input()

if m=='c' or m=='t' or m=='s' or m=='b':

    if m=='c':

        submenu = int(input())

        if submenu in range(3):

            print('Welcome to CCD!\nEnjoy your {}!'.format(menu[0][submenu-1]))

        else:

            print("INVALID INPUT")

    if m=='t':

        submenu = int(input())

        if submenu in range(8):

            print('Welcome to CCD!\nEnjoy your {}!'.format(menu[1][submenu-1]))

        else:

            print("INVALID INPUT")

    if m=='s':

        submenu = int(input())

        if submenu in range(4):

            print('Welcome to CCD!\nEnjoy your {}!'.format(menu[2][submenu-1]))

        else:

            print("INVALID INPUT")

    if m=='b':

        submenu = int(input())

        if submenu in range(3):

            print('Welcome to CCD!\nEnjoy your {}!'.format(menu[3][submenu-1]))

        else:

            print("INVALID INPUT")

else:

    print("INVALID INPUT!")
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 16
[s2If current_user_can(access_s2member_level1)]

**Question**: A doctor has a clinic where he serves his patients. The doctor’s consultation fees are different for different groups of patients depending on their age. If the patient’s age is below 17, fees is 200 INR. If the patient’s age is between 17 and 40, fees is 400 INR. If patient’s age is above 40, fees is 300 INR. Write a code to calculate earnings in a day for which one array/List of values representing age of patients visited on that day is passed as input.  
**Note**:

- Age should not be zero or less than zero or above 120

- Doctor consults a maximum of 20 patients a day

- Enter age value (press Enter without a value to stop):

**Example 1:  
Input**  
20  
30  
40  
50  
2  
3  
14  
**Output**  
Total Income 2000 INR  
**Note**: Input and Output Format should be same as given in the above example.  
For any wrong input display INVALID INPUT  
**Output Format  
**Total Income 2100 INR

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;

int main()
{
int x, count =0, flag = 0, fee_sum=0;

while(cin>>x){

if(x<=0 and x>120)
{
flag=1;
break;
}

count++;

if(x<17) fee_sum +=200;

else if(x>=17 and x<=40) fee_sum += 400;

else fee_sum += 300;
}

if(count >20 and flag != 1)
cout<<"INVALID INPUT";

else cout<<"Total income : "<<fee_sum<<" INR";
return 0;
}
```

**Python Code**:

```
age = []

for i in range(20):
    m = input()
    if m == "":
        break
    elif int(m) in range(0,120):
        age.append(int(m))
    else:
        print("INVALID INPUT")
        exit()
fees = 0
for i in age:
    if i < 17:
        fees+=200
    elif i <40:
        fees+=400
    else:
        fees+=300
print("Total Income {} INR".format(fees))
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 17
[s2If current_user_can(access_s2member_level1)]

**Questions**: To check whether a year is leap or not  
**Step 1: **

- We first divide the year by 4.

- If it is not divisible by 4 then it is not a leap year.

- If it is divisible by 4 leaving remainder 0 

**Step 2: **

- We divide the year by 100

- **If it is not divisible by 100 then it is a leap year.**

- If it is divisible by 100 leaving remainder 0

**Step 3: **

- We divide the year by 400

- If it is not divisible by 400 then it is a leap year.

- If it is divisible by 400 leaving remainder 0 

**Then it is a leap year**.

**C Code**:

```
#include <stdio.h>
int leapprog(int year)
{
//checking divisibility by 4
    if(year%4 == 0)
    {
//checking divisibility by 100
        if( year%100 == 0)
        {
//checking divisibility by 400
            if ( year%400 == 0)
                printf("%d, the year entered happens to be a leap year", year);
            else
                printf("%d is surely not a leap year", year);
        }
        else
            printf("%d, the year entered happens to be a leap year", year );
    }
    else
        printf("%d is surely not a leap year", year);
        return 0;
}
int main()
{
    int input_year, val;
    printf("Enter the year that you want to check"); //enter the year to check
    scanf("%d",&input_year);
    val = leapprog(input_year);    
return 0;
}
```

**C++ Code**:

```
#include <iostream>
using namespace std;
//main program
int main()
{
	//initialising variables
	int year;
	cout<<"Enter year to check: ";
	//user input
	cin>>year;
	//checking for leap year
	if( ((year % 4 == 0)&&(year % 100 != 0)) || (year % 400==0) )
	{
		//input is a leap year
		cout<<year<<" is a leap year";
	}
	else
	{
		//input is not a leap year
		cout<<year<< " is not a leap year";
	}
	return 0;
}
```

**Java Code**:

```
import java.util.Scanner;
public class Main
{
    public static void main(String[] args)
    {
        //scanner class declaration
        Scanner sc=new Scanner(System.in);
        //input year from user
        System.out.println("Enter a Year");
        int year = sc.nextInt();
        //condition for checking year entered by user is a leap year or not
        if((year % 4 == 0 && year % 100 != 0) || year % 400 == 0)
        System.out.println(year + " is a leap year.");
        else
        System.out.println(year + " is not a leap year.");
    }
}
```

**Python Code**:

```
#python program to check if a year number taken from the user is a leap year or not, using nested if-else.
num = int(input("Enter the year you want to check if is leap year or not: "))

#take input year from the user to check if it is a leap year

if(num%4 == 0):

 #check if the number is divisible by 4 and if true move to next loop

if(num%100 == 0):

     #check if the input year is divisible by 100 and if true move to next loop

if(num%400 == 0):

print("The year {} is a leap year".format(num))

           #the input year is divisible by 4, 100 and 400, hence leap year.

else:

print("The year {} is Not a leap year".format(num))

else:

print("The year {} is a leap year".format(num))

       #if the number is divisible by both 4 and 100 it is a leap year

else:

print("The year {} is Not a leap year".format(num))

 #if the input num is not divisible by 4 then it can not be a leap year altogether.
```

**Perl Code**:

```
# perl Script
# leap year
print "Enter Year: ";
$year=;
# condition to check for leap year
  if( (0 == $year % 4) && (0 != $year % 100) || (0 == $year % 400) )
    {
        print "Leap year";
    }
    else
    {
        print "Not a leap year";
    }
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 18
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a code to check whether a number is prime or not. Condition use function check() to find whether entered no is positive or negative ,if negative then enter the no, And if yes pas no as a parameter to prime() and check whether no is prime or not?

- **Whether the number is positive or not, if it is negative then print the message “please enter the positive number”**

- **It is positive then call the function prime and check whether the take positive number is prime or not. **

****C Code**:**

```
#include <stdio.h>
void prime(int n)
{
int c=0;
    for(int i=2;i<n;i++)     {         if(n%i==0)         c = c+1;     }     if(c>=1)
        printf("%d is not a prime number",n);
    else
        printf("%d is a prime number",n);
}
void main()
{
int n;
printf("Enter no : "); //enter the number
scanf("%d",&n);
if(n<0)
    {
    printf("Please enter a positive integer");
    }
else
    prime(n);
}
```

**C++ Code**:

```
//Prime Number
#include <iostream>
using namespace std;
//function declaration
void enter();
void check(int);
void prime(int);
//main program
int main()
{
    enter();
    return 0;
}
//function to enter value
void enter()
{
    int num;
    cout<<"Enter number:"; cin>>num;
    check(num);
}
//function to check whether the input is positive or negative
void check(int num)
{
    if(num<0)
    {
        cout<<"invalid input enter value again"<< endl;
        enter();
    }
    else
    {
        prime(num);
    }
}
//function to check for prime number
void prime(int num)
{
    int i,div =0;
    for(i=1;i<=num;i++)
    {
        if(num%i==0)
        {
            div++;
        }
    }
    //prime number only have two divisors
    if(div==2)
    {
        cout<< num<<" is a prime number";
    }
    //not a prime number
    else
    {
        cout<< "not a prime number" ;
    }
}
```

**Java Code**:

```
//Prime number is a number which is divisible by 1 and another by itself only.

import java.util.Scanner;
class Main
{
public static void main(String[] args)
{
Scanner sc = new Scanner(System.in);
//input a number from user
System.out.println("Enter the number to be checked : ");
int n = sc.nextInt();
//create object of class CheckPrime
Main ob=new Main();
//calling function with value n, as parameter
ob.check(n);
}
//function for checking number is positive or negative
void check(int n)
{
if(n<0)
System.out.println("Please enter a positive integer");
else
prime(n);
}
//function for checking number is prime or not
void prime(int n)
{
int c=0;
for(int i=2;i<n;i++)
{
if(n%i==0)
++c;
}
if(c>=1)
System.out.println("Entered number is not a prime number");
else
System.out.println("Entered number is a prime number");
}
}
```

**Python Code**:

```
def prime(n):
if n > 1:

for i in range(2, n):

if (n % i) == 0:

print(n, "is not a prime number")

break

else:

print(n, "is a prime number")

num = int(input("enter a number: "))

if (num > 0):

prime(num)

else:

print("please enter a positive number")
```

**Perl Code**:

```
#Perl Script
#Prime Number or Not
print "Enter a number";
$n=<STDIN>;
$d=0;
if($n<0)
{
	print "Ivalid Input!!! Enter Value Again";
}
else
{
	#Loop  to find number of divisors
	for($c=1;$c<=$n;$c++)
	{
		if($n%$c==0)
		{
			$d=$d+1;
		}
	}
	#checking for prime numbers
	if($d==2)
	{
		print "Prime Number";
	}
	else
	{
		print "Not a Prime number";
	}
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 19
[s2If current_user_can(access_s2member_level1)]

**Question**: Find the 15th term of the series?  
0,0,7,6,14,12,21,18, 28

**Explanation :   
**In this series the odd term is increment of 7 {0, 7, 14, 21, 28, 35 – – – – – – }  
And even term is a increment of 6 {0, 6, 12, 18, 24, 30 – – – – – – }** **

**C Code**:

```
#include <stdio.h>
int main()
{
   int i, n, a=0, b=0;
   printf("enter number : ");
   scanf("%d",&n);
   for(i=1;i<=n;i++)
   {
      if(i%2!=0)
      {
           a = a + 7;
      }
       else
      {    
           b = b + 6;
      }
   }
      if(n%2!=0)
      {
           printf("%d term of series is %d\t",n,a-7);
      }
      else
      {    
           printf("%d term of series is %d\t",n,b-6);
      }
return 0;
 }
```

**C++ Code**:

```
//C++ Program
#include <iostream>
using namespace std;
int main()
{
	//initialising variables
	int n,d;
	cout<<"Enter the position: ";
	//user input
	cin>>n;
	//logic to find nth element of the series
	if(n==1||n==2)
	{
			cout<<0;
			return 0;
	}
	else if(n%2==0)
	{
		n=n/2;
		d=6;		
	}
	else
	{
		n=n/2+1;
		d=7;
	}
	//logic ends here
	//printing output
	cout<<(n-1)*d;
	return 0;
}
```

**Java Code**:

```
//Java program to find 15th element of the series
class Main
{
	public static void main(String[] args)
	{
		int a = 7, b = 0,c;
		System.out.println("Series :");
		for(int i = 1 ; i < 8 ; i++)
		{
			c = a * b;
			System.out.print(c+"	"+(c-b)+"	");
			b++;
		}
			c = a * b;
			System.out.println(c);
			System.out.print("15th element of the series is = "+c);
	}
}
```

**Python Code**:

```
num = int(input('enter the number: '))
a=0

b=0

for i in range(1,num+1):

if(i%2!=0):

a= a+7

else:

b = b+6

if(num%2!=0):

print(' {} term of series is {}'.format(num,a-7))

else:

print('{} term of series is {}'.format(num,b-6))
```

**Perl Code**:

```
#perl Script
print"Enter position: ";
$n=;
$term=0;
$d=0;
if($n==0||$n==1)
{	
    $term=0;
}
else
{
    if(0==$n%2)
    {
    	$n=($n/2);
    	$d=6;		
    }
    else
    {
    	$n=($n/2) + 0.5;
    	$d=7;
    }
    $term= ($n-1) * $d;
}
print"$term.";
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 20
[s2If current_user_can(access_s2member_level1)]

**Question**: Consider the following series: 1, 1, 2, 3, 4, 9, 8, 27, 16, 81, 32, 243, 64, 729, 128, 2187 …

This series is a mixture of 2 series – all the odd terms in this series form a geometric series and all the even terms form yet another geometric series. Write a program to find the Nth term in the series.

The value N in a positive integer that should be read from STDIN. The Nth term that is calculated by the program should be written to STDOUT. Other than value of n th term,no other character / string or message should be written to STDOUT. For example , if N=16, the 16th term in the series is 2187, so only value 2187 should be printed to STDOUT.

You can assume that N will not exceed 30.** **

**C Code**:

```
#include <stdio.h>
int main()
{
   int i, n, a=1, b=1;
   printf("enter number : ");
   scanf("%d",&n);
   for(i=1;i<=n;i++)
   {
       if(i%2!=0)
       {
           a = a * 2;
       }
       else
       {    
            b = b * 3;
       }
   }
    if(n%2!=0)
       {
           printf("\n%d term of series is %d\t",n,a/2);
       }
       else
       {    
           printf("\n%d term of series is %d\t",n,b/3);
       }
return 0;
}
```

**C++ Code**:

```
//C++ Program
#include <iostream>
#include <math.h>
using namespace std;
int main()
{
  //initialising variables
  int n,r,term;
  cout<<"Enter the position: ";
  //user input
  cin>>n;
  //logic to find nth element of the series
  if(n==1||n==2)
  {
    cout<<1;
    return 0; 
  }
  else if(n%2==0)
  {
    n=n/2-1;
    r=3; 
  }
  else
  {
    n=n/2;
    r=2;
  }
  //logic ends here
  //printing output
  cout<<(int)(pow(r,n));
  return 0;
}
```

**Java Code**:

```
//Java program to find nth element of the series
import java.util.Scanner;
class Main
{
	public static void main(String[] args)
	{
		Scanner sc = new Scanner(System.in);
		//input value of n
		System.out.print("Enter the value of n : ");				
		int n = sc.nextInt();
		int a = 1, b = 1;
		//statement for even value of n
		if(n % 2 == 0)
		{
			for(int i = 1 ; i <= (n-2) ; i = i+2)
			{
				a = a * 2;
				b = b * 3;
			}
			System.out.print(n+" element of the series is = "+b);
		}
		//statement for odd value of n
		else
		{
			for(int i = 1 ; i < (n-2) ; i = i+2)
			{
				a = a * 2;
				b = b * 3;
			}
			a = a * 2;
			System.out.print(n+" element of the series is = "+a);
		}
	}
}
```

**Python Code**:

```
n = int(input('enter the number: '))
a= 1

b= 1

for i in range(1, n+1):

if(i%2!=0):

a = a*2

else:

b = b*3

if(n%2!=0):

print('\n{} term of series is {}\t'.format(n,a/2))

else:

print('\n{} term of series is {}\t'.format(n,a/2))
```

**Perl Code**:

```
#Perl Script
$a=1;
$b=1;
print("enter number : ");
$n=<STDIN>;
for($i=1;$i<=$n;$i++)
{
    if($i%2!=0)
    {
        $a = $a * 2;
    }
    else
    {    
        $b = $b * 3;
    }
}
if($n%2!=0)
{    
    print("$n term of series is ",$a/2);
}
else
{    
    print("$n term of series is ",$b/3);
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 21
[s2If current_user_can(access_s2member_level1)]

**Question**: Consider the below series :

0, 0, 2, 1, 4, 2, 6, 3, 8, 4, 10, 5, 12, 6, 14, 7, 16, 8

This series is a mixture of 2 series all the odd terms in this series form even numbers in ascending order and every even terms is derived from the previous  term using the formula (x/2)  
**Write a program to find the nth term in this series.  
**The value n in a positive integer that should be read from STDIN the nth term that is calculated by the program should be written to STDOUT. Other than the value of the nth term no other characters /strings or message should be written to STDOUT.

For example if n=10,the 10 th term in the series is to be derived from the 9th term in the series. The 9th term is 8 so the 10th term is (8/2)=4. Only the value 4 should be printed to STDOUT.

You can assume that the n will not exceed 20,000.** **

**C Code**:

```
#include <stdio.h>

int main()
{
    int i, n, a=0, b=0;
    printf("enter number : ");
    scanf("%d",&n);
    
    
    for(i=1;i<=n;i++)
    {
        if(i%2!=0)
        {
            if(i>1)
                a = a + 2;
        }
        else
        {
            b = a/2;
        }
    }

    if(n%2!=0)
    {
        printf("%d",a);
    }
    else
    { 
        printf("%d",b);
    }
    
    return 0;
}
```

**C++ Code**:

```
#include

using namespace std;
int main()
{
    int i, n, a=0, b=0;
    cout << "enter number : ";
    cin >> n;
    
    
    for(i=1;i<=n;i++)
    {
        if(i%2!=0)
        {
            if(i>1)
                a = a + 2;
        }
        else
        {
            b = a/2;
        }
    }

    if(n%2!=0)
    {
        cout << a;
    }
    else
    { 
        cout << b;
    }
    
    return 0;
}
```

**Java Code**:

```
//Java program to find nth element of the series
import java.util.Scanner;
class Main
{
  public static void main(String[] args)
  {
    Scanner sc = new Scanner(System.in);
    int n = sc.nextInt();
    int a = 0, b = 0;
    if(n % 2 == 0)
    {
      for(int i = 1 ; i <= (n-2) ; i = i+2)
      {
        a = a + 2;
        b = a / 2;
      }
      System.out.print(b);
     }
     else
     {
       for(int i = 1 ; i < (n-2) ; i = i+2)
       {
         a = a + 2;
         b = a / 2;
       }
       a = a + 2;
       System.out.print(a);
     }
   }
}
```

**Python Code**:

```
n = int(input('enter the number:'))
a=0
b=0

for i in range(1,n+1):
if(i%2!=0):
a= a+2
else:
b= b+1

if(n%2!=0):
print('{}'.format(a-2))
else:
print('{}'.format(b-1))
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 22
[s2If current_user_can(access_s2member_level1)]

**Question**: The program will recieve 3 English words inputs from STDIN

- These three words will be read one at a time, in three separate line

- The first word should be changed like all vowels should be replaced by %

- The second word should be changed like all consonants should be replaced by #

- The third word should be changed like all char should be converted to upper case

- Then concatenate the three words and print them

Other than these concatenated word, no other characters/string should or message should be written to STDOUT

For example if you print how are you then output should be h%wa#eYOU.

You can assume that input of each word will not exceed more than 5 chars.

**C Code**:

```
#include <stdio.h>
#include 
int main()
{
  char a[10], b[10], c[10];
  int i,j;
  int x, y, z;

  scanf("%s",a);
  scanf("%s",b);
  scanf("%s",c);

  x = strlen(a);
  y = strlen(b);
  for(i=0;i<x;i++)
  {
      if(a[i]=='a'||a[i]=='e'||a[i]=='i'||a[i]=='o'||a[i]=='u')
      {
          a[i] = '%';
      }
  }
  for(j=0;j<y;j++)
  {
      if(b[j]=='b'||b[j]=='c'||b[j]=='d'||b[j]=='f'||b[j]=='g'||b[j]=='h'||b[j]=='j'||b[j]=='k'||b[j]=='l'||
         b[j]=='m'||b[j]=='n'||b[j]=='p'||b[j]=='q'||b[j]=='r'||b[j]=='s'||b[j]=='t'||b[j]=='v'||b[j]=='w'||
         b[j]=='x'||b[j]=='y'||b[j]=='z')
      {
          b[j] = '#';
      }
      
      if(b[j]=='B'||b[j]=='C'||b[j]=='D'||b[j]=='F'||b[j]=='G'||b[j]=='H'||b[j]=='J'||b[j]=='K'||b[j]=='L'||
         b[j]=='M'||b[j]=='N'||b[j]=='P'||b[j]=='Q'||b[j]=='R'||b[j]=='S'||b[j]=='T'||b[j]=='V'||b[j]=='W'||
         b[j]=='X'||b[j]=='Y'||b[j]=='Z')
      {
          b[j] = '#';
      }
  }
  z=0;
   while (c[z] != '\0') {
      if (c[z] >= 'a' && c[z] <= 'z')
       {
         c[z] = c[z] - 32;
      }
      z++;
   }
   printf("%s%s%s",a,b,c);
}
```

**C++ Code**:

```
#include < isotream>
#include <math.h>
using namespace std;
int main() { 
char a[10], b[10], c[10];
 int i,j; 
int x, y, z; 
cin >> a;
 cin >> b;
 cin >> c;
x = strlen(a); 
y = strlen(b); 
for(i=0;i<x;i++) { 
if(a[i]=='a'||a[i]=='e'||a[i]=='i'||a[i]=='o'||a[i]=='u') { 
a[i] = '%';
 } 
} for(j=0;j<y;j++) { 
if(b[j]=='b'||b[j]=='c'||b[j]=='d'||b[j]=='f'||b[j]=='g'||b[j]=='h'||b[j]=='j'||b[j]=='k'||b[j]=='l'|| b[j]=='m'||b[j]=='n'||b[j]=='p'||b[j]=='q'||b[j]=='r'||b[j]=='s'||b[j]=='t'||b[j]=='v'||b[j]=='w'|| b[j]=='x'||b[j]=='y'||b[j]=='z') { 
b[j] = '#'; 
} 
if(b[j]=='B'||b[j]=='C'||b[j]=='D'||b[j]=='F'||b[j]=='G'||b[j]=='H'||b[j]=='J'||b[j]=='K'||b[j]=='L'|| b[j]=='M'||b[j]=='N'||b[j]=='P'||b[j]=='Q'||b[j]=='R'||b[j]=='S'||b[j]=='T'||b[j]=='V'||b[j]=='W'|| b[j]=='X'||b[j]=='Y'||b[j]=='Z') { 

b[j] = '#'; 

}
 }
 z=0; 
while (c[z] != '\0') {
 if (c[z] >= 'a' && c[z] <= 'z') { 
c[z] = c[z] - 32; 
} 
z++; 
} 
cout << a << b << c;

return 0; }
```

**Java Code**:

```
import java.util.*;
public class Main
{
	public static void main(String[] args)
	{
		Scanner sc = new Scanner(System.in);
		System.out.println("Enter three words : ");
				
		String s1 = sc.next();
		String s2 = sc.next();
		String s3 = sc.next();

		int l1 = s1.length();
		int l2 = s2.length();

		String str1 = "";
		String str2 = "";
		String str3 = "";
		char c;
		for(int i = 0 ; i < l1 ; i++)
		{
			c = s1.charAt(i);
			if(c == 'A' || c == 'a' || c == 'E' || 
                           c == 'e' || c == 'I' || c == 'i' || c == 'O' || c == 'o' || c == 'U' || c == 'u')
			str1 = str1 + "%";
			else
			str1 = str1 + c;
		}
		for(int i = 0 ; i < l2 ; i++)
		{
			c = s2.charAt(i);
			if((c >= 'A' && c <= 'Z')||(c >= 'a' && c <= 'z'))
			{
				if(c == 'A' || c == 'a' || c == 'E' || c == 'e' || 
                            c == 'I' || c == 'i' || c == 'O' || c == 'o' || c == 'U' || c == 'u')
					str2 = str2 + c;
				else
					str2 = str2 + "#";
			}
			else
				str2 = str2 + c;
		}
		str3 = s3.toUpperCase();
		System.out.println(str1+str2+str3);
	}
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 23
[s2If current_user_can(access_s2member_level1)]

**Question**: Using a method, pass two variables and find the sum of two numbers.  
**Test case:  
**Number 1 – 20  
Number 2 – 20.38  
Sum = 40.38

There were a total of 4 test cases. Once you compile 3 of them will be shown to you and 1 will be a hidden one. You have to display error message if numbers are not numeric.

**C Code**:

```
#include <stdio.h>
addition(int x, float y)
{
    float ans;
    ans = (float)x + y;
    printf("Answer : %.2f",ans);
}
int main()
{
   int a;
   float b;
   printf("enter first number : ");
   scanf("%d",&a);
   printf("enter second number : ");
   scanf("%f",&b);
   addition(a, b);
}
```

**C++ Code**:

```
//C++ Program
//Sum of two numbers using function
#include
using namespace std;
//function to add two numbers
float sum(int a, float b)
{
	return (float)(a+b);
}
//main program
int main()
{
	//initialising variables
	int a;
	float b;
	cout<<"Enter two numbers";
	//user input
	cin>>a;
	cin>>b;
	//call function to find sum
	cout<<"Sum of "<<a<<" and "<<b<<" is "<<sum(a,b);
	return 0;
}
```

**Java Code**:

```
import java.util.Scanner;
class Main
{
	public static void main(String[] args)
	{
		Scanner sc = new Scanner(System.in);
		System.out.print("Number 1 : ");				
		int num1 = sc.nextInt();
		System.out.print("Number 2 : ");				
		float num2 = sc.nextFloat();
		float sum = num1 + num2;
		System.out.println("Sum = "+sum);
	}
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 24
[s2If current_user_can(access_s2member_level1)]

**Question**: **Consider the below series :**

0, 0, 2, 1, 4, 2, 6, 3, 8, 4, 10, 5, 12, 6, 14, 7, 16, 8

This series is a mixture of 2 series all the odd terms in this series form even numbers in ascending order and every even terms is derived from the previous  term using the formula (x/2)  
**Write a program to find the nth term in this series.  
**The value n in a positive integer that should be read from STDIN the nth term that is calculated by the program should be written to STDOUT. Other than the value of the nth term no other characters /strings or message should be written to STDOUT.  
For example if n=10,the 10 th term in the series is to be derived from the 9th term in the series. The 9th term is 8 so the 10th term is (8/2)=4. Only the value 4 should be printed to STDOUT.

You can assume that the n will not exceed 20,000.

**C Code**:

```
#include <stdio.h>

int main() {
//code
int n;
scanf(“%d”, &n);
if(n % 2 == 1)
{
int a = 1;
int r = 2;
int term_in_series = (n+1)/2;
int res = 2 * (term_in_series – 1);
printf(“%d “, res);
}
else
{
int a = 1;
int r = 3;
int term_in_series = n/2;

int res = term_in_series – 1;
printf(“%d “, res);
}

return 0;
}
```

**C++ Code**:

```
#include <iostream>
using namespace std;
int main ()
{

int n;
cin >> n;

if (n % 2 == 1)
{
int a = 1;
int r = 2;

int term_in_series = (n + 1) / 2;

int res = 2 * (term_in_series-1);
cout << res;
}

else
{
int a = 1;
int r = 3;
int term_in_series = n / 2;

int res = term_in_series-1;
cout << res;
}

return 0;

}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 25
[s2If current_user_can(access_s2member_level1)]

**Question**: A chocolate factory is packing chocolates into the packets. The chocolate packets here represent an array  of N number of integer values. The task is to find the empty packets(0) of chocolate and push it to the end of the conveyor belt(array).

**Example 1 :**

N=7 and arr = [4,5,0,1.9,0,5,0].

There are 3 empty packets in the given set. These 3 empty packets represented as O should be pushed towards the end of the array

**Input :**

7  – Value of N

[4,5,0,1,0,0,5] – Element of arr[O] to arr[N-1],While input each element is separated by newline

**Output:**

4 5 1 9 5 0 0

**Example 2:**

**Input:**

6 — Value of N.

[6,0,1,8,0,2] – Element of arr[0] to arr[N-1], While input each element is separated by newline

**Output:**

6 1 8 2 0 0

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;

int
main () 
{
  
int n, j = 0;
  cin >> n;
  
int a[n] = { 0 };
  
for (int i = 0; i < n; i++)
    
    {
      
cin >> a[j];
      
if (a[j] != 0)
	j++;
    
}
  
for (int i = 0; i < n; i++)
    
cout << a[i] << " ";

}
```

**Java Code**:

```
import java.util.*;
class Main
{
    public static void main(String[] args)
    {
            Scanner sc=new Scanner(System.in);
            int n=sc.nextInt();
            int arr[]=new int[n];
            for(int i=0;i< n;i++)
                  arr[i]=sc.nextInt();
            int count=0;
            for(int i=0;i< n;i++)
                if(arr[i]!=0)
                    arr[count++]=arr[i];
             for(int i=count;i < n;i++)
                 arr[i]=0;
             for(int i=0;i< n;i++)
                    System.out.print(arr[i]+" ");
    }
}
```

**Python Code**:

```
n=int(input())
j=0
L=[0 for i in range(n)]
for i in range(n):
    a=int(input())
    if a!=0:
        L[j]=a
        j+=1
for i in L:
    print(i,end=" ")
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 26
[s2If current_user_can(access_s2member_level1)]

**Question**: Joseph is learning digital logic subject which will be for his next semester. He usually tries to solve unit assignment problems before the lecture. Today he got one tricky question. The problem statement is “A positive integer has been given as an input. Convert decimal value to binary representation. Toggle all bits of it after the most significant bit including the most significant bit. Print the positive integer value after toggling all bits”.

**Constrains-**

1<=N<=100

**Example 1:**

**Input :**

10  -> Integer

**Output :**

5    -> result- Integer

**Explanation:**

Binary representation of 10 is 1010. After toggling the bits(1010), will get 0101 which represents “5”. Hence output will print “5”.

**C++ Code**:

```
#include<bits/stdc++.h>
using namespace std;
int main()
{
    int n; cin>>n;
    int k=(1<<(int)floor(log2(n))+1)-1;
    cout<<(n^k); }
```

**Java Code**:

```
import java.util.*;
class Main
{
  public static void main(String[] args)
  {
         Scanner sc=new Scanner(System.in);
         int no=sc.nextInt();
          String bin="";
         
          while(no!=0)
           {
                  bin=(no&1)+bin;
                  no=no>>1;
           }
            bin=bin.replaceAll("1","2");
            bin=bin.replaceAll("0","1");
            bin=bin.replaceAll("2","0");
            int res=Integer.parseInt(bin,2);
           System.out.println(res);
   }
}
```

**Python Code**:

```
import math
n=int(input())
k=(1<<int(math.log2(n))+1)-1
print(n^k)
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 27
[s2If current_user_can(access_s2member_level1)]

**Question**: Jack is always excited about sunday. It is favourite day, when he gets to play all day. And goes to cycling with his friends. 

So every time when the months starts he counts the number of sundays he will get to enjoy. Considering the month can start with any day, be it Sunday, Monday…. Or so on.

Count the number of Sunday jack will get within n number of days.

** Example 1:**

**Input **

mon-> input String denoting the start of the month.

13  -> input integer denoting the number of days from the start of the month.

**Output :**

2    -> number of days within 13 days.

**Explanation**:

The month start with mon(Monday). So the upcoming sunday will arrive in next 6 days. And then next Sunday in next 7 days and so on.

Now total number of days are 13. It means 6 days to first sunday and then remaining 7 days will end up in another sunday. Total 2 sundays may fall within 13 days.

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;
int main()
{
    string s; cin>>s;
    int a,ans=0;
    cin>>a;
    unordered_map< string,int > m;
    m["mon"]=6;m["tue"]=5;m["wed"]=4;
    m["thu"]=3;m["fri"]=2;m["sat"]=1;
    m["sun"]=0;
    if(a-m[s.substr(0,3)] >=1) ans=1+(a-m[s.substr(0,3)])/7;
    cout<< ans;
}
```

**Java Code**:

```
import java.util.*;
class Main
{
public static void main(String[] args)
{
        Scanner sc=new Scanner(System.in);
        String str=sc.next();
        int n=sc.nextInt();
        String arr[]={"mon","tue,","wed","thu","fri","sat","sun"};
        int i=0;
        for(i=0;i< arr.length;i++)
             if(arr[i].equals(str))
                 break;
        int res=1;
        int rem=6-i;
        n=n-rem;    
        if(n >0)
           res+=n/7;
        System.out.println(res);
      
}
}
```

**Python Code**:

```
from collections import defautdict
m=defaultdict(int)
m["mon"]=6
m["tue"]=5
m["wed"]=4
m["thu"]=3
m["fri"]=2
m["sat"]=1
m["sun"]=0
s=input()
a=int(input())
ans=0
if a-m[s[0:3]]>=1:
  ans=1+(a-m[s[0:3]])//7
print(ans)
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 28
[s2If current_user_can(access_s2member_level1)]

**Question**: Airport security officials have confiscated several item of the passengers at the security check point. All the items have been dumped into a huge box (array). Each item possesses a certain amount of risk[0,1,2]. Here, the risk severity of the items represent an array[] of N number of integer values. The task here is to sort the items based on their levels of risk in the array. The risk values range from 0 to 2.

**Example** :

**Input :**

7  -> Value of N

[1,0,2,0,1,0,2]-> Element of arr[0] to arr[N-1], while input each element is separated by new line.

**Output :**

0 0 0 1 1 2 2  -> Element after sorting based on risk severity 

**Example 2:**

input : 10  -> Value of N 

[2,1,0,2,1,0,0,1,2,0] -> Element of arr[0] to arr[N-1], while input each element is separated by a new line.

**Output : **

0 0 0 0 1 1 1 2 2 2  ->Elements after sorting based on risk severity.

**Explanation:**

In the above example, the input is an array of size N consisting of only 0’s, 1’s and 2s. The output is a sorted array from 0 to 2 based on risk severity.

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;
int main()
{
    int n; cin>>n;
    int a[n];
    for(int i=0;i< n;i++) cin>>a[i];
    int l=0,m=0,h=n-1;
    while(m<=h)
    {
        if(a[m]==0) swap(a[l++],a[m++]);
        else if(a[m]==1) m++;
        else swap(a[m],a[h--]);
    }
    for(int i=0;i< n;i++) cout<< a[i]<<" ";
}
```

**Java Code**:

```
import java.util.*;
class Main
{
    public static void main(String[] args)
    {
         Scanner sc=new Scanner(System.in);
          int n=sc.nextInt();
          int arr[]=new int[n];
          for(int i=0;i< n;i++)
                 arr[i]=sc.nextInt();
           int countZero=0,countOne=0,countTwo=0;
           for(int i=0;i< n;i++)
           {
                 if(arr[i]==0)
                        countZero++;
                 else if(arr[i]==1)
                        countOne++;
                 else if(arr[i]==2)
                        countTwo++;
            }
            int j =0;
            while(countZero >0)
             {
                        arr[j++]=0;
                        countZero--;
             }
             while(countOne >0)
             {
                       arr[j++]=1;
                      countOne--;
              }

              while(countTwo >0)
              {
                      arr[j++]=2;
                      countTwo--;
               }

              for(int i=0;i < n;i++)
                    System.out.print(arr[i]+" ");        
    }
}
```

**Python Code**:

```
n = int(input())
arr = []
for i in range(n):
    arr.append(int(input()))
for i in sorted(arr):
    print(i, end=" ")
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 29
[s2If current_user_can(access_s2member_level1)]

**Question**: Given an integer array Arr of size N the task is to find the count of elements whose value is greater than all of its prior elements.

Note : 1st element of the array should be considered in the count of the result.

For example,

Arr[]={7,4,8,2,9}

As 7 is the first element, it will consider in the result.

8 and 9 are also the elements that are greater than all of its previous elements.

Since total of  3 elements is present in the array that meets the condition.

Hence the output = 3.

** Example 1:**

**Input **

5 -> Value of N, represents size of Arr

7-> Value of Arr[0]

4 -> Value of Arr[1]

8-> Value of Arr[2]

2-> Value of Arr[3]

9-> Value of Arr[4]

**Output :**

3

**Example 2:**

5   -> Value of N, represents size of Arr

3  -> Value of Arr[0]

4 -> Value of Arr[1]

5 -> Value of Arr[2]

8 -> Value of Arr[3]

9 -> Value of Arr[4]

**Output : **

5

**Constraints**

1<=N<=20

1<=Arr[i]<=10000

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;
int main()
{
    int n,c=0,a,m=INT_MIN;
    cin>>n;
    while(n--)
    {
        cin>>a;
        if(a>m)
        {
            m=a;
            c++;
        }
    }
    cout << c;
}
```

**Java Code**:

```
import java.util.*;
class Main
{
  public static void main(String[] args)
  {
         Scanner sc=new Scanner(System.in);
         int n=sc.nextInt();
         int arr[]=new int[n];
         for(int i=0;i< n;i++)
                 arr[i]=sc.nextInt();
         int max=Integer.MIN_VALUE;

         int count=0;
         for(int i=0;i< n;i++)
         {
              if(arr[i]>max)

              {
                       max=arr[i];
                       count++;
               }
         }      
         System.out.println(count);
}
}
```

**Python Code**:

```
import sys
n=int(input())
c=0
m=-sys.maxsize-1
while n:
    n-=1
    a=int(input())
    if a>m:
        m=a
        c+=1
print(c)
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 30
[s2If current_user_can(access_s2member_level1)]

**Question**: A supermarket maintains a pricing format for all its products. A value N is printed on each product. When the scanner reads the value N on the item, the product of all the digits in the value N is the price of the item. The task here is to design the software such that given the code of any item N the product (multiplication) of all the digits of value should be computed(price).

**Example 1:**

**Input :**

5244 -> Value of N

**Output :  
**160 -> Price 

**Explanation:**

From the input above 

Product of the digits 5,2,4,4

5*2*4*4= 160

Hence, output is 160.

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;
int main()
{
    string s; 
    cin>>s;
    int p=1;
    for(auto i:s) 
        p*=(i-'0');
    cout<< p;
}
```

**Java Code**:

```
import java.util.*;
class Main
{
    public static void main(String[] args)
    {
          Scanner sc=new Scanner(System.in);
          int n=sc.nextInt();
          int res=1;
          while(n>0)
          {
                res=res*(n%10);
                n=n/10;
           }
            System.out.println(res);
    }
}
```

**Python Code**:

```
n=input()
p=1
for i in n:
    p*=int(i)
print(p)
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 31
[s2If current_user_can(access_s2member_level1)]

**Question**: A furnishing company is manufacturing a new collection of curtains. The curtains are of two colors aqua(a) and black (b). The curtains color is represented as a string(str) consisting of a’s and b’s of length N. Then, they are packed (substring) into L number of curtains in each box. The box with the maximum number of ‘aqua’ (a) color curtains is labeled. The task here is to find the number of ‘aqua’ color curtains in the labeled box.

**Note :**

If ‘L’ is not a multiple of N, the remaining number of curtains should be considered as a substring too. In simple words, after dividing the curtains in sets of ‘L’, any curtains left will be another set(refer example 1)

**Example 1:**

**Input :**

bbbaaababa -> Value of str

3    -> Value of L

**Output:**

3   -> Maximum number of a’s

**Explanation:**

From the input given above.

Dividing the string into sets of 3 characters each 

Set 1: {b,b,b}

Set 2: {a,a,a}

Set 3: {b,a,b}

Set 4: {a} -> leftover characters also as taken as another set

Among all the sets, Set 2 has more number of a’s. The number of a’s in set 2 is 3.

Hence, the output is 3.

**Example 2:**

**Input :**

abbbaabbb -> Value of str

5   -> Value of L

**Output**:

2   -> Maximum number of a’s

**Explanation**:

From the input given above,

Dividing the string into sets of 5 characters each.

Set 1: {a,b,b,b,b}

Set 2: {a,a,b,b,b}

Among both the sets, set 2 has more number of a’s. The number of a’s in set 2 is 2.

Hence, the output is 2.

**Constraints:**

1<=L<=10

1<=N<=50

The input format for testing 

The candidate has to write the code to accept two inputs separated by a new line.

First input- Accept string that contains character a and b only

Second input- Accept value for N(Positive integer number)

The output  format for testing

The output should be a positive integer number of print the message(if any) given in the problem statement.(Check the output in Example 1, Example 2).

**Java Code**:

```
import java.util.*;
class Main
{
       public static void main(String[] args)
       {
               Scanner sc=new Scanner(System.in);
               String str=sc.next();
               int n=sc.nextInt();
               int max=0,count=0;
               for(int i=0;i< str.length();i++)
               {
                       if(i%n==0)
                       {
                          max=Math.max(count,max); 
                          count=0;
                       }
                       if(str.charAt(i)=='a')
                             count++;
                }
                max=Math.max(count,max);
                System.out.println(max);     
       }
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 32
[s2If current_user_can(access_s2member_level1)]

**Question**: An international round table conference will be held in india. Presidents from all over the world representing their respective countries will be attending the conference. The task is to find the possible number of ways(P) to make the N members sit around the circular table such that.

The president and prime minister of India will always sit next to each other.

**Example 1:**

**Input :**

4   -> Value of N(No. of members)

**Output : **

12  -> Possible ways of seating the members

**Explanation:**

2  members should always be next to each other. 

So, 2 members can be in 2!ways

Rest of the members can be arranged in (4-1)! ways.(1 is subtracted because the previously selected two members will be considered as single members now).

So total possible ways 4 members can be seated around the circular table 2*6= 12.

Hence, output is 12.

**Example 2:**

**Input:**

10  -> Value of N(No. of members)

**Output :**

725760 -> Possible ways of seating the members 

**Explanation:**

2 members should always be next to each other.

So, 2 members can be in 2! ways 

Rest of the members can be arranged in (10-1)! Ways. (1 is subtracted because the previously selected two members will be considered as a single member now).

So, total possible ways 10 members can be seated around a round table is 

2*362880 = 725760 ways.

Hence, output is 725760.

The input format for testing

The candidate has to write the code to accept one input 

First input – Accept value of number of N(Positive integer number)

The output format for testing 

The output should be a positive integer number or print the message(if any) given in the problem statement(Check the output in example 1, example2)

**Constraints :**

2<=N<=50

**Java Code**:

```
import java.math.BigInteger;
import java.util.*;
class Main
{
       public static BigInteger fact(int number)
      {
           BigInteger res= BigInteger.ONE;
           for (int i = number; i > 0; i--)
                 res = res.multiply(BigInteger.valueOf(i));
           return res;
      }
      public static void main(String[] args)
     {
           Scanner sc=new Scanner(System.in);
           int n=sc.nextInt();
           BigInteger res=fact(n-1);
           System.out.println(res.multiply(BigInteger.valueOf(2)));    
     }
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 33
[s2If current_user_can(access_s2member_level1)]

**Question**: An intelligence agency has received reports about some threats. The reports consist of numbers in a mysterious method. There is a number “N” and another number “R”. Those numbers are studied thoroughly and it is concluded that all digits of the number ‘N’ are summed up and this action is performed ‘R’ number of times. The resultant is also a single digit that is yet to be deciphered. The task here is to find the single-digit sum of the given number ‘N’ by repeating the action ‘R’ number of times.

If the value of ‘R’ is 0, print the output as ‘0’.

**Example 1:**

**Input :**

99 -> Value of N

3  -> Value of R

**Output :**

9  -> Possible ways to fill the cistern.

**Explanation:**

Here, the number N=99

- Sum of the digits N: 9+9 = 18

- Repeat step 2 ‘R’ times i.e. 3 tims  (9+9)+(9+9)+(9+9) = 18+18+18 =54

- Add digits of 54 as we need a single digit 5+4

Hence , the output is 9.

**Example 2:**

**Input :**

1234   -> Value of N

2      -> Value of R

**Output :**

2  -> Possible ways to fill the cistern

**Explanation:**

Here, the number N=1234

- Sum of the digits of N: 1+2+3+4 =10

- Repeat step 2 ‘R’ times i.e. 2 times  (1+2+3+4)+(1+2+3+4)= 10+10=20

- Add digits of 20 as we need a single digit. 2+0=2

Hence, the output is 2.

**Constraints:**

0<N<=1000

0<=R<=50

The Input format for testing 

The candidate has to write the code to accept 2 input(s)

First input- Accept value for N (positive integer number)

Second input: Accept value for R(Positive integer number)

The output format for testing 

The output should be a positive integer number or print the message (if any) given in the problem statement. (Check the output in Example 1, Example 2).

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;
int main()
{
    string s; cin>>s;
    int n,sum=0; cin>>n;
    for(auto i:s) sum+=(i-'0');
    sum*=n;
    s=to_string(sum);
    while(s.length()>1)
    {
        sum=0;
        for(auto i:s) sum+=(i-'0');
        s=to_string(sum);
    }
    cout<< s;
}
```

**Python Code**:

```
s=input()
n=int(input())
sum=0
for i in s:
    sum+=int(i)
sum*=n
s=str(sum)
while len(s)>1:
    sum=0
    for i in s:
        sum+=int(i)
    s=str(sum)

print(s)
```

**Java Code**:

```
import java.util.*;
class Main
{
       public static int sumOfDigits(int n)
       {
             int sum=0;
             while(n>0)
             {
                  sum+=n%10;
                  n=n/10;
             }
           return sum;
        }
        public static void main(String []args)
        {
              Scanner sc=new Scanner(System.in);
              int n=sc.nextInt();
              int r=sc.nextInt();
              if(r==0)
                    System.out.println("0");
              else
              {
                       int res=sumOfDigits(n)*r;
                       int sum=0;
                       while(true)
                       {
                               while(res>0)
                             {
                                    sum=sum+res%10;
                                    res=res/10;
                              }
                              if((sum/10)==0)
                                 break;
                              else
                                 res=sum;
                      }
                      System.out.println(sum);
                }  
        } }
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 34
[s2If current_user_can(access_s2member_level1)]

**Question**: Particulate matters are the biggest contributors to Delhi pollution. The main reason behind the increase in the concentration of PMs include vehicle emission by applying Odd Even concept for all types of vehicles. The vehicles with the odd last digit in the registration number will be allowed on roads on odd dates and those with even last digit will on even dates.

Given an integer array a[], contains the last digit of the registration number of N vehicles traveling on date D(a positive integer). The task is to calculate the total fine collected by the traffic police department from the vehicles violating the rules.

**Note :** For violating the rule, vehicles would be fined as X Rs.

**Example 1:**

**Input :**

4 -> Value of N

{5,2,3,7} -> a[], Elements a[0] to a[N-1], during input each element is separated by a new line

12 -> Value of D, i.e. date 

200 -> Value of x i.e. fine

**Output :**

600  -> total fine collected 

**Explanation:**

Date D=12 means , only an even number of vehicles are allowed. 

Find will be collected from 5,3 and 7 with an amount of 200 each.

Hence, the output = 600.

**Example 2:**

**Input :**

5   -> Value of N 

{2,5,1,6,8}  -> a[], elements a[0] to a[N-1], during input each element is separated by new line

3 -> Value of D i.e. date 

300 -> Value of X i.e. fine 

Output :

900  -> total fine collected 

**Explanation:**

Date D=3 means only odd number vehicles with are allowed.

Find will be collected from 2,6 and 8 with an amount of 300 each.

Hence, the output = 900 

**Constraints:**

- 0<N<=100

- 1<=a[i]<=9

- 1<=D <=30

- 100<=x<=5000 

The input format for testing 

The candidate has to write the code to accept 4 input(s).

First input – Accept for N(Positive integer) values (a[]), where each value is separated by a new line.

Third input – Accept value for D(Positive integer)

Fourth input – Accept value for X(Positive integer )

The output format for testing 

The output should be a positive integer number (Check the output in Example 1, Example e) if no fine is collected then print ”0”.

**Java Code**:

```
import java.util.*;
class Main
{
   public static void main (String[]args)
   {
       Scanner sc = new Scanner (System.in);
       int n = sc.nextInt ();
       int arr[] = new int[n];
       for (int i = 0; i < n; i++)
           arr[i] = sc.nextInt ();
       int d = sc.nextInt ();
       int x = sc.nextInt ();
       int countEven = 0, countOdd = 0;
       for (int i = 0; i < n; i++)
       {
       if (arr[i] % 2 == 0)
           countEven++;
       else
           countOdd++;
       }
       if (d % 2 != 0)
       {
       if (countEven == 0)
           System.out.println ("0");
       else
           System.out.println (countEven * x);
       }
       else
       {
       if (countOdd == 0)
           System.out.println ("0");
       else
           System.out.println (countOdd * x);
       }
   }
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 35
[s2If current_user_can(access_s2member_level1)]

**Question**: At the security checkpoint, airport security personnel have seized a number of travellers’ belongings. Everything has been thrown into a big box (array). Each product carries a specific level of risk[0,1,2]. The risk severity of the items in this case is represented by an array[] of N integer values. Sorting the elements in the array according to the degrees of danger is the task at hand. Between 0 and 2 are the risk values. 

**Example** :

**Input :**

7  -> Value of N

[1,0,2,0,1,0,2]-> Element of arr[0] to arr[N-1], while input each element is separated by new line.

**Output :**

0 0 0 1 1 2 2  -> Element after sorting based on risk severity

**Example 2:**

input : 10  -> Value of N

[2,1,0,2,1,0,0,1,2,0] -> Element of arr[0] to arr[N-1], while input each element is separated by a new line.

**Output : **

0 0 0 0 1 1 1 2 2 2  ->Elements after sorting based on risk severity.

**Explanation:**

In the above example, the input is an array of size N consisting of only 0’s, 1’s and 2s. The output is a sorted array from 0 to 2 based on risk severity.

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;
int main()
{
    int n; cin>>n;
    int a[n];
    for(int i=0;i< n;i++) cin>>a[i];
    int l=0,m=0,h=n-1;
    while(m<=h)
    {
        if(a[m]==0) swap(a[l++],a[m++]);
        else if(a[m]==1) m++;
        else swap(a[m],a[h--]);
    }
    for(int i=0;i< n;i++) cout<< a[i]<<" ";
}
```

**Java Code**:

```
import java.util.*;
class Main
{
    public static void main(String[] args)
    {
         Scanner sc=new Scanner(System.in);
          int n=sc.nextInt();
          int arr[]=new int[n];
          for(int i=0;i< n;i++)
                 arr[i]=sc.nextInt();
           int countZero=0,countOne=0,countTwo=0;
           for(int i=0;i< n;i++) { 
             if(arr[i]==0) 
                countZero++; 
             
             else if(arr[i]==1) 
                countOne++; 
    
             else if(arr[i]==2)
                countTwo++; 
           }
           int j =0;
             while(countZero >0)
             {
                        arr[j++]=0;
                        countZero--;
             }
             while(countOne >0)
             {
                       arr[j++]=1;
                      countOne--;
              }

              while(countTwo >0)
              {
                      arr[j++]=2;
                      countTwo--;
               }

              for(int i=0;i < n;i++)
                    System.out.print(arr[i]+" ");        
    }
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 36
[s2If current_user_can(access_s2member_level1)]

**Question**: For all of its products, a supermarket maintains a pricing structure. Each product has a value N printed on it. The price of the item is determined by multiplying the value N, which is read by the scanner, by the sum of all its digits. The goal here is to create software that, given the code of any item N, will compute the product (multiplication) of all the value digits (price). 

**Example 1:**

**Input :**

5244 -> Value of N

**Output :  
**160 -> Price 

**Explanation:**

From the input above   
Product of the digits 5,2,4,4  
5*2*4*4= 160  
Hence, output is 160.

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;
int main()
{
    string s; 
    cin>>s;
    int p=1;
    for(auto i:s) 
        p*=(i-'0');
    cout<< p;
}
```

**Java Code**:

```
import java.util.*;
class Main
{
    public static void main(String[] args)
    {
          Scanner sc=new Scanner(System.in);
          int n=sc.nextInt();
          int res=1;
          while(n>0)
          {
                res=res*(n%10);
                n=n/10;
           }
            System.out.println(res);
    }
}
```

**Python Code**:

```
n=input()
p=1
for i in n:
    p*=int(i)
print(p)
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 37
[s2If current_user_can(access_s2member_level1)]

**Question**: There are two banks – Bank A and Bank B. Their interest rates vary. You have received offers from both banks in terms of the annual rate of interest, tenure, and variations of the rate of interest over the entire tenure.You have to choose the offer which costs you least interest and reject the other. Do the computation and make a wise choice.

The loan repayment happens at a monthly frequency and Equated Monthly Installment (EMI) is calculated using the formula given below :

EMI = loanAmount * monthlyInterestRate / ( 1 – 1 / (1 + monthlyInterestRate)^(numberOfYears * 12))

**Constraints:**

- 1 <= P <= [1000000](tel:1000000)

- 1 <=T <= 50

- 1<= N1 <= 30

- 1<= N2 <= 30

**Input Format:**

- First line: P principal (Loan Amount)

- Second line: T Total Tenure (in years).

- Third Line: N1 is the number of slabs of interest rates for a given period by Bank A. First slab starts from the first year and the second slab starts from the end of the first slab and so on.

- Next N1 line will contain the interest rate and their period.

- After N1 lines we will receive N2 viz. the number of slabs offered by the second bank.

- Next N2 lines are the number of slabs of interest rates for a given period by Bank B. The first slab starts from the first year and the second slab starts from the end of the first slab and so on.

- The period and rate will be delimited by a single white space.

**Output Format: **Your decision either Bank A or Bank B.

**Example 1**

Input

10000  
20  
3  
5 9.5  
10 9.6  
5 8.5  
3  
10 6.9  
5 8.5  
5 7.9

**Output**: Bank B

**Example 2**

Input

500000  
26  
3  
13 9.5  
3 6.9  
10 5.6  
3  
14 8.5  
6 7.4  
6 9.6

**Output**: Bank A

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;
 
int main()
{
   int year,principal,installments;
   float bank[2],roi,square,emi,sum;
   cin>>principal;
   cin>>year;
   for(int i=0;i<2;i++) { cin>>installments;
       sum = 0;
       for(int j=0;j<installments;j++) { cin>>year>>roi;
           square = pow((1+roi),year*12);
           emi = (principal*(roi)/(1-1/square));
           sum += emi;
       }
       bank[i]=sum;
   }
   if( bank[0] < bank[1]) cout<<"Bank A";
   else cout<<"Bank B";
}
```

**Java Code**:

```
import java.util.Scanner;
public class Main{
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        double p,s,mi,sum,emi,sq;
        int y,n,k,yrs,l=0;
        double[] bank = new double[5];
        System.out.println("Enter the principal amount");
         p = sc.nextDouble();
         System.out.println("Enter tenature year");
         y = sc.nextInt();
         for (k = 0; k < 2; k++) {
            System.out.println("Enter the no of slabs");
            n = sc.nextInt();
         sum=0;
         for (int i = 0; i < n; i++) {
            System.out.println("Enter the period :");
            yrs = sc.nextInt();
            System.out.println("Enter the intrest :");
            s = sc.nextDouble();
            mi=0;
            sq=Math.pow((1+s), yrs*12);
            emi=(p*(s))/(1-1/sq);
            sum=sum+emi;
         }
         bank[l++]=sum;
      }
         if(bank[0]<bank[1])
             System.out.println("Bank A");
         else
             System.out.println("Bank B");
        
    }

}
```

**Python Code**:

```
bank = []
principal = int(input())
year = int(input())
for i in range(2):
    installments = int(input())
    sum = 0
    for i in range(0, installments):
        year, roi = map(float,input().split())
        year = int(year)
        square = pow((1+roi),year*12)
        emi = (principal*(roi)/(1-1/square))
        sum = sum + emi
    bank.append(sum)
 
if bank[0] < bank[1]:
    print("Bank A")
else:
    print("Bank B")
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 38
[s2If current_user_can(access_s2member_level1)]

**Question**: Some prime numbers can be expressed as a sum of other consecutive prime numbers. For example 5 = 2 + 3, 17 = 2 + 3 + 5 + 7, 41 = 2 + 3 + 5 + 7 + 11 + 13. Your task is to find out how many prime numbers which satisfy this property are present in the range 3 to N subject to a constraint that summation should always start with number 2.

Write code to find out the number of prime numbers that satisfy the above-mentioned property in a given range.

**Input Format :** First line contains a number N

**Output Format :** Print the total number of all such prime numbers which are less than or equal to N.

**Constraints :**  2<N<=12,000,000,000

**Example  :**                                 

**Input :**

20                       

**Output :**

2                                                                    

**Explanation :**

Below 20, there are 2 such numbers,   
5=2+3  
17=2+3+5+7

**C++ Code**:

```
#include<bits/stdc++.h>
using namespace std;
map<int,int> prime;
vector<int> pr;
int ans=0,n;
 
int main()
{
    cin>>n;
    prime[0]=1;
    for(int p = 2; p <= n; p++)
    {
        if (prime[p] == 0)
        {
            pr.push_back(p);
            for (int i = p*p; i <= n; i += p)
                prime[i] =1;
        }
    }
    int sum=2;
    for(int i=1;i<pr.size();i++)
    {
        sum+=pr[i];
        if(sum>n) break;
        if(prime[sum]==0) {ans++;}
    }
    cout<<ans;
}
```

**Java Code**:

```
public class Main{
    public static void main(String[] args)
    {
        int n = 45;
        boolean prime[] = new boolean[n + 1];
        vector <Integer>primevector = new vector<>();
        
        for (int i = 0; i <= n; i++)
            prime[i] = true;
 
        for (int p = 2; p <= n; p++)
        {
            if (prime[p] == true)
            {
                primevector.add(p);
                for(int i = (p * p); i <= n; i += p)
                    prime[i] = false;
            }
        }
        int count = 0;
        int sum = primevector.elementAt(0);
        for (int i = 1; i < primevector.size(); i++) { sum += primevector.elementAt(i); if(sum > n)
                break;
            if(prime[sum] == true)
            {
                count++;
            }
        }
        System.out.println(count);
    }
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 39
[s2If current_user_can(access_s2member_level1)]

**Question**: Juan Marquinho is a geologist and he needs to count rock samples in order to send it to a chemical laboratory. He has a problem: The laboratory only accepts rock samples by a range of its size in ppm (parts per million).

Juan Marquinho receives the rock samples one by one and he classifies the rock samples according to the range of the laboratory. This process is very hard because the number of rock samples may be in millions.

Juan Marquinho needs your help, your task is to develop a program to get the number of rocks in each of the ranges accepted by the laboratory.

**Input Format**

An positive integer S (the number of rock samples) separated by a blank space, and a positive integer R (the number of ranges of the laboratory); A list of the sizes of S samples (in ppm), as positive integers separated by space R lines where the ith line containing two positive integers, space separated, indicating the minimum size and maximum size respectively of the ith range.

**Output Format**

R lines where the ith line contains a single non-negative integer indicating the number of the samples which lie in the ith range.

**Constraints**

- 10 < S < 10000 

- 1 < R < 1000000

- 1 size of each sample (in ppm) <  1000

**Example 1**

Input: 10 2  
345 604 321 433 704 470 808 718 517 811  
300 350  
400 700

**Output**: 2 4

**Explanation:**

There are 10 samples (S) and 2 ranges ( R ). The samples are 345 604 321 433 704 470 808 718 517 811. The ranges are 300-350 and 400-700. There are 2 samples in the first range (345 and 321) and 4 samples in the second range (604, 433, 470, 517). Hence the two lines of the output are 2 and 4

**Example 2**

**Input:** 20 3  
921 107 270 631 926 543 589 520 595 93873 424 759 537 458 614 725 842 575 195  
1 100  
50 600  
1 1000

**Output**: 1 12 20

**Explanation:**

There are 20 samples and 3 ranges. The samples are 921, 107 195. The ranges are 1-100, 50-600 and 1-1000. Note that the ranges are overlapping. The number of samples in each of the three ranges are 1, 12 and 20 respectively. Hence the three lines of the output are 1, 12 and 20.

**C++ Code**:

```
#include <bits/stdc++.h>
using namespace std;
int main()
{
    int s,r,a,b,ans;
     cin>>s>>r;
    vector<int> ansv;
    unordered_map<int,int> m;
    for(int i=0;i<s;i++)
    {
        cin>>a;
        m[a]++;
    }
    for(int i=0;i<r;i++)
    {
        cin>>a>>b;
        ans=0;
        for(int j=a;j<=b;j++)
        if(m[j]) ans++;
        ansv.push_back(ans);
    }
    for(auto i:ansv) cout<<i<<" ";
}
```

**Java Code**:

```
import java.util.*;

class Main {

   public static void main(String[] args) {
       {

           int n, range, count = 0;
           Scanner sc = new Scanner(System.in);
           n = sc.nextInt();
           int arr[] = new int[n];
           range = sc.nextInt();

           for (int i = 0; i < n; i++)
               arr[i] = sc.nextInt();
               range = range * 2;

           for (int i = 0; i < range; i = i + 2) {
               int arrrange[] = new int[range];
               arrrange[i] = sc.nextInt();
               arrrange[i + 1] = sc.nextInt();
               for (int j = 0; j < n; j++) {
                   if ((arr[j] >= arrrange[i]) && (arr[j] <= arrrange[i + 1]))
                       count++;
               }
               System.out.println(count);
               count = 0;
           }
       }
   }
}
```

**Python Code**:

```
from collections import defaultdict
D=defaultdict(int)
AnsString=""
s,r=map(int,input().split())
L=list(map(int,input().split()))
for i in L:
    D[i]=1
for i in range(r):
    a,b=map(int,input().split())
    ans=0
    for j in range(a,b+1):
        if D[j]:
            ans+=1
    AnsString+=str(ans)+" "
print(AnsString)
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 40
[s2If current_user_can(access_s2member_level1)]

**Question**: K-th largest factor of N. We have a positive integer d which is said to be a factor of another positive integer N if when N is divided by d, the remainder obtained is zero. For example, for number 12, there are 6 factors 1, 2, 3, 4, 6, 12. Every positive integer k has at least two factors, 1 and the number k itself.Given two positive integers N and k, write a program to print the kth largest factor of N.

**Input Format: **The input is a comma-separated list of positive integer pairs (N, k)

**Output Format: **The kth highest factor of N. If N does not have k factors, the output should be 1.

**Constraints: **1<N<10000000000. 1<k<600.You can assume that N will have no prime factors which are larger than 13.

**Example 1**

- **Input**: 12,3

- **Output**: 4

**Explanation: **N is 12, k is 3. The factors of 12 are (1,2,3,4,6,12). The highest factor is 12 and the third largest factor is 4. The output must be 4

**Example 2**

- **Input**: 30,9

- **Output**: 1

**Explanation: **N is 30, k is 9. The factors of 30 are (1,2,3,5,6,10,15,30). There are only 8 factors. As k is more than the number of factors, the output is 1.

**C++ Code**:

```
#include<bits/stdc++.h>
using namespace std;
vector<int> a,ans;
 
void Find_Factor(int f,int i)
{
    if(f>sqrt(a[0])) return;
    if(a[0]%f)
    {
        Find_Factor(f+i,i);return;
    }
    ans.push_back(f);
    Find_Factor(f+i,i);
    if(f*f!=a[0])
    ans.push_back(a[0]/f);
}
 
int main()
{
    string s;getline(cin,s);
    int n,k;
    istringstream ss(s);
    for(int i;ss>>i;)
    {
        a.push_back(i);
        if(ss.peek()==',') ss.ignore();
    }
    ans.push_back(1);
    if((a[0]&1)==0) Find_Factor(2,1);
    else Find_Factor(3,2);
    ans.push_back(a[0]);
    //for(auto i:ans) cout<<i<<" ";
    if(ans.size()<a[1]) cout<<1;
    else cout<<ans[ans.size()-a[1]];
}
```

**Java Code**:

```
import java.util.*;

class Main {

   public static void main(String[] args) {
       {
           int n, k, i, c = 0;
           Scanner sc = new Scanner(System.in);

         
           n = sc.nextInt();
        
           k = sc.nextInt();
           for (i = n; i >= 1; i--) {
               if ((n % i) == 0)
                   c++;
               if (c == k) {
                   System.out.println(i);
                   break;
               }
           }
           if (c != k)
               System.out.println("1");
           return ;

       }

   }
}
```

**Python Code**:

```
def Find_Factor(f,i,n,ans):
    if f*f>n:
        return
    if (n%f):
        Find_Factor(f+i,i,n,ans)
        return
    ans.append(f)
    Find_Factor(f+i,i,n,ans)
    if (f*f)!=n:
        ans.append(n//f)
 
n,k=map(int,input().split(","))
ans=[]
ans.append(1)
if n&1:
    Find_Factor(3,2,n,ans)
else:
    Find_Factor(2,1,n,ans)
ans.append(n)
 
if(len(ans)<k):
    print(1)
else:
    print(ans[len(ans)-k])
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 41
[s2If current_user_can(access_s2member_level1)]

**Question**: Krishna loves candies a lot, so whenever he gets them, he stores them so that he can eat them later whenever he wants to.

He has recently received N boxes of candies each containing Ci candies where Ci represents the total number of candies in the ith box. Krishna wants to store them in a single box. The only constraint is that he can choose any two boxes and store their joint contents in an empty box only. Assume that there are an infinite number of empty boxes available.

At a time he can pick up any two boxes for transferring and if both the boxes contain X and Y number of candies respectively, then it takes him exactly X+Y seconds of time. As he is too eager to collect all of them he has approached you to tell him the minimum time in which all the candies can be collected.

**Input Format:**

- The first line of input is the number of test case T

- Each test case is comprised of two inputs

- The first input of a test case is the number of boxes N

- The second input is N integers delimited by whitespace denoting the number of candies in each box

**Output Format: **Print minimum time required, in seconds, for each of the test cases. Print each output on a new line.

**Constraints:**

- 1 <T<10

- 1 <N<10000

- 1 < [Candies in each box] < 100009

**Input :**

1

4

1 2 3 4

**Output :**

19

**Explanation :**

4 boxes, each containing 1, 2, 3 and 4 candies respectively.Adding 1 + 2 in a new box takes 3 seconds.Adding 3 + 3 in a new box takes 6 seconds.Adding 4 + 6 in a new box takes 10 seconds.Hence total time taken is 19 seconds. There could be other combinations also, but overall time does not go below 19 seconds.

**C++ Code**:

```
#include<bits/stdc++.h>
using namespace std;
 
int main()
{
    int t;cin>>t;
    vector<int> ans;
    while(t--)
    {
        int n,a;cin>>n;
        priority_queue<int,vector<int>,greater<int>> pq;
        for(int i=0;i<n;i++)
        {cin>>a;pq.push(a);}
        a=0;
        while(pq.size()>1)
        {
            int k1=pq.top();pq.pop();
            k1+=pq.top();pq.pop();
            a+=k1;pq.push(k1);
        }
        ans.push_back(a);
    }
    for(auto i:ans) cout<<i<<endl;
}
```

**Python Code**:

```
import heapq as hq
t=int(input())
for _ in range(t):
    n=int(input())
    a=list(map(int,input().split()))
    hq.heapify(a)
    s=0
    for j in range(n-1):
        b=hq.heappop(a)
        c=hq.heappop(a)
        s+=(b+c)
        hq.heappush(a,b+c)
    print(s)
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 42
[s2If current_user_can(access_s2member_level1)]

**Question**: In the theory of numbers, square free numbers have a special place.  A square free number is one that is not divisible by a perfect square (other than 1).  Thus 72 is divisible by 36 (a perfect square), and is not a square free number, but 70 has factors 1, 2, 5, 7, 10, 14, 35 and 70.  As none of these are perfect squares (other than 1), 70 is a square free number.

For some algorithms, it is important to find out the square free numbers that divide a number.  Note that 1 is not considered a square free number. 

In this problem, you are asked to write a program to find the number of square free numbers that divide a given number.

**Input**

- The only line of the input is a single integer N which is divisible by no prime number larger than 19

**Output**

- One line containing an integer that gives the number of square free numbers (not including 1)

**Constraints**

- N   < 10^9

**Complexity**

Simple

**Time Limit**

1

**Example 1**

**Input**

20

**Output**

3

**Explanation**

N=20

If we list the numbers that divide 20, they are

1, 2, 4, 5, 10, 20

1 is not a square free number, 4 is a perfect square, and 20 is divisible by 4, a perfect square.  2 and 5, being prime, are square free, and 10 is divisible by 1,2,5 and 10, none of which are perfect squares.  Hence the square free numbers that divide 20 are 2, 5, 10.  Hence the result is 3.

**Example 2**

**Input**

72

**Output**

3

**Explanation**

N=72.  The numbers that divide 72 are

1, 2, 3, 4, 6, 8, 9, 12, 18, 24, 36, 72

1 is not considered square free. 4, 9 and 36 are perfect squares, and 8,12,18,24 and 72 are divisible by one of the.  Hence only 2, 3 and 6 are square free.  (It is easily seen that none of them are divisible by a perfect square).  The result is 3.

**C++ Code**:

```
#include
using namespace std;
 
int main()
{
    int N,c=0; //c is Count of Prime Factors
    cin>>N;
    vector <int> Prime={2,3,5,7,11,13,17,19};
    for(auto i:Prime)
    if(N%i==0) c++;
    cout<<((1<<c)) - 1;  //2^n - 1
}
```

**Java Code**:

```
import java.io.*;
import java.util.*;
import java.lang.Math; 
public class Main
{
    public static void main(String[] args) {
        
        long n;
        double square;
        long j = 0,  check;
        long[] temp = new long[10_000];
        int total_count = 0;
        System.out.println("Enter the number:");
        Scanner sc= new Scanner(System.in); 
        n = sc.nextLong();
        
        
//        Checking for dividends of the given number and primality
        for(int i = 2; i <= n / 2; i++) {
            if(n % i == 0) {
                total_count++;
                square = Math.sqrt(i);
                check = (long)square;
                
//                Checking for perfect square
                if(check == square) {
                    total_count--;
                    temp[(int)j] = i;
                    j++;
                } else {
                    for(int rem = 0; rem < j; rem++) {
                        if(i > temp[rem] && j != 0) {
                            if(i % temp[rem] == 0) {
                                total_count--;
                                rem = (int)(j + 1);
                            }
                        } else {
                            break;
                        }
                    }
                }
            }
        }

        System.out.print(total_count);
        sc.close();
    }
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 43
[s2If current_user_can(access_s2member_level1)]

```
Scanner sc = new Scanner(System.in);

long sum = 0;

int N = sc.nextInt();

for (int i = 0; i < N; i++) {

final long x = sc.nextLong(); // read input

String str = Long.toString((long) Math.pow(1 << 1, x)); str = str.length() > 2 ? str.substring(str.length() - 2) : str;

sum += Integer.parseInt(str);

}

System.out.println(sum%100);
```

**Question**: Given N number of x’s, perform logic equivalent of the above Java code and print the output

**Input**

- First line contains an integer N

- Second line will contain N numbers delimited by space

**Output**

- Number that is the output of the given code by taking inputs as specified above

**Constraints**

- 1<=N<=10^7

- 0<=x<=10^18

**Example 1**

**Input**

4

8 6 7 4

**Output**

64

**Example 2**

**Input**

3

1 2 3

**Output**

14

**C++ Code**:

```
#include<bits/stdc++.h>
using namespace std;
int main()
{
    long long int n,ans=0,x;
    cin >>n;
    for(int i=0;i<n;i++)
    {
        cin >> x;
        x=pow(2,x);
        if(x>99) ans+=x%100;
        else ans+=x;
    }
    cout<<ans%100;
    return 0;
}
```

**Java Code**:

```
import java.util.Scanner;
import java.lang.Math;
class Main {

    public static void main(String[] args) {
        long  ans = 0;
        Scanner scn = new Scanner(System.in);
        long n = scn.nextInt();

        for (int i = 0; i < n; i++) { long x = scn.nextInt(); Math.pow(2, x); if (x > 99)
            ans += x % 100;
            else ans += x;
        }
        System.out.println(ans % 100);
    }
}
```

**Python Code**:

```
n=int(input())
arr=list(map(int,input().split()))
ans=0
for i in arr:
    x=2**i
    if(x>99):
        ans+=x%100 
    else:
        ans+=x 
print(ans%100)
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 44
[s2If current_user_can(access_s2member_level1)]

**Question**: There are n houses built in a line, each of which contains some value in it.

A thief is going to steal the maximal value of these houses, but he can’t steal in two adjacent houses because the owner of the stolen houses will tell his two neighbours left and right side.

What is the maximum stolen value?

**Input Format**

- First an integer n, denoting how many houses are there.

- Then n space separated integers denoting the values for the n houses.

**Output Format**

An integer denoting the maximum value possible to steal.

**Input    **                                      

7                                               

6 7 1 3 8 2 5

**Output**

20

**Explanation**

6+1+8+5 = 20.

It is the max possible value.

**C++ Code**:

```
#include<bits/stdc++.h>
using namespace std;
int n;
 
int main()
{
    cin>>n;
    vector<int> arr(n);
    for(int i=0;i<n;i++) cin>>arr[i];
    int incl=0,excl=0,mx;
    for(int i=0;i<n;i++)
    {
        mx=max(incl,excl);
        incl=excl+arr[i];
        excl=mx;
    }
    cout<<max(incl,excl);
}
```

**Python Code**:

```
n=int(input())
arr=list(map(int,input().split()))
incl=0
excl=0
mx=0
for i in range(n):
    mx=max(incl,excl)
    incl=excl+arr[i]
    excl=mx
 
print(max(incl,excl))
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 45
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a c program, to find the GCD of the given 2 numbers, using command line arguments. The input is 2 integer and the output GCD also should be an integer value.

**C Code**:

```
#include<stdio.h>
int main(int x, char *y[])
{
int a,b,small,i;
a=atoi(y[1]);
b=atoi(y[2]);
small=a>b?b:a;
for(i=small;i>=1;i–)
{
if((a%i==0)&&(b%i==0))
{
printf(“%d”,i);
break;
} }
return 0;
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 46
[s2If current_user_can(access_s2member_level1)]

**Question**: Create a C Program to check whether a given number is a prime number or not. The given number N, a positive integer, will be passed to the program using the first command line parameter. If it is a prime number the output should be the square root of the number up to 2 decimal point precision, If it is not a prime number then print 0.00 to stdout

**C Code**:

```
#include<stdio.h>
#include<math.h>
 int main(int a, char *b[])
{
int number,i,flag = 1;
number = atoi(b[1]);
for(i=2; i<number; i++)
{
if(number%i == 0)
{
flag = 0;
break;
}
}
if(flag == 1)
printf(“%.2f”,sqrt(number));
else
printf(“0.00”);
return 0;
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 47
[s2If current_user_can(access_s2member_level1)]

**Question**: Create a C Program to check whether a given number is a strong number or not. The given number N, a positive integer, will be passed to the program using the first command line parameter. If it is a strong number, the output should be “YES”, If it is not a prime number then output should be “NO” to stdout. Other than YES or NO, no other extra information should be printed to stdout.

**C Code**:

```
#include<stdio.h>
#include<math.h>
int main(int a, char *b[])
{
int number, i, temp, sum = 0, factorial = 1;
number = atoi(b[1]);
temp = number;
while(number != 0)
{
int rem = number%10;
for(i=2; i<=rem; i++)
{
factorial = factorial * i;
}
sum = sum + factorial;
number = number/10;
factorial = 1;
}
if(temp == sum)
printf(“YES”);
else
printf(“NO”);
return 0;
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 48
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a C program which will convert a given decimal integer number N to its binary equivalent. The given number N, a positive integer, will be passed to the program using the first command line parameter. Print the equivalent binary number to stdout. Other than the binary number, no other extra information should be printed to stdout Example: Given input “19”, here N=19, expected output 10011.

```
#include<stdio.h>
#include<math.h>
int main(int a, char *argv[])
{
int number, count, i;
int b[32];
number = atoi(argv[1]);
count = 0;
while(number != 0)
{
b[count]=number%2;
number = number/2;
count++;
}
for(i=(count-1); i>=0; i–)
printf(“%d”, b[i]);
return 0;
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 49
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a C program that will find the sum of all prime numbers in a given range. The range will be specified as command line parameters. The first command line parameter, N1 which is a positive integer, will contain the lower bound of the range. The second command line parameter N2, which is also a positive integer will contain the upper bound of the range. The program should consider all the prime numbers within the range, excluding the upper bound and lower bound. Print the output in integer format to stdout. Other than the integer number, no other extra information should be printed to stdout. Example Given inputs “7” and “24” here N1= 7 and N2=24, expected output as 83. 

**C Code**:

```
#include<stdio.h>
int main(int argc, char *argv[])
{
int N1, N2, j, i, count, sum = 0;
N1 =atoi(argv[1]);
N2 =atoi(argv[2]);
for(i=N1+1; i<N2; ++i)
{
count = 0;
for(j=2; j<=(i/2); j++)
{
if(i%j==0)
{
count++;
break;
}
}
if(count==0)
sum = sum + i;
}
printf(“%d”,sum);
return 0;
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 50
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a C program to check whether the given number is a perfect square or not using command line arguments.

**C Code**:

```
#include<stdio.h>
#include<math.h>
int main(int a, char *b[])
{
int n, i;
n= atoi(b[1]);
for(i = 0; i <= n; i++)
{
if(n == i * i)
{
printf(“YES”);
return 0;
}
}
printf(“NO”);
return 0;
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 51
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a C program to check whether the given number is Palindrome or not using command line arguments.

**C Code**:

```
#include<stdio.h>
#include<math.h>
int main(int a,int *b[])
{
int number, rem, sum = 0;
number = atoi(b[1]);
int copy = number;
while(number != 0)
{
rem =number%10;
sum = sum * 10 + rem;
number = number/10;
}
if(copy == sum)
printf(“Palindrome”);
else
printf(“Not Palindrome”);
return 0;
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 52
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a C program to convert the vowels to an uppercase in a given string using command line arguments.  
Example: if the input is tata, then the expected output is tAtA.

**C Code**:

```
#include<stdio.h>
int main(int argc, char *argv[])
{
char *str = argv[1];
int i;
for(i =0; str[i] !=’\0′; i++)
{
if(str[i] == ‘a’ || str[i] == ‘e’ || str[i] == ‘i’ || str[i] == ‘o’ || str[i] == ‘u’)
{
str[i] = str[i] – 32;
}
}
printf(“%s”, str);
return 0;
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 53
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a C program to find the hypotenuse of a triangle using command line arguments.

**C Code**:

```
#include<stdio.h> 
int main(int a, char*b[])
{
float hyp;
int opp=atoi(b[1]);
int adj=atoi(b[2]);
hyp=sqrt((opp*opp)+(adj*adj));
printf(“%0.2f”,hyp);
return 0;
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 54
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a C program to find whether the given number is an Armstrong number or not using command line arguments.  
An Armstrong number of three digits is an integer such that the sum of the cubes of its digits is equal to the number itself. For example, 371 is an Armstrong number  
since 3**3 + 7**3 + 1**3 = 371.

**C Code**:

```
#include<stdio.h>
#include<math.h> 
int main(int a, char*b[])
{
int n;
n= atoi(b[1]);
int sum=0;
int temp=n;
int cnt=0;
while(n!=0)
{
n=n/10;
cnt++;
}
n=temp;
while(n!=0)
{
int rem=n%10;
sum=sum+pow(rem,cnt);
n=n/10;
}
if(temp==sum)
{
printf(“yes”);
}
else
{
printf(“no”);
}
return 0;
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 55
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a C program to generate Fibonacci Series.

**C Code**:

```
#include<stdio.h>
#include<math.h>
int main(int a, char *b[])
{
int i, n, t1 = 0, t2 = 1, nextTerm;
n=atoi(b[1]);
for (i = 1; i <= n; ++i)
{
printf(“%d “, t1);
nextTerm = t1 + t2;
t1 = t2;
t2 = nextTerm;
}
return 0;
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 56
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a C program to calculate length of hypotenuse of right-angled triangle.

**C Code**:

```
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
int main(int argc, char *argv[])
{
if(argc<2)
{
printf(“please use \”prg_name value1 value2 … \”\n”);
return -1;
}
int a,b,side1,side2,side3;
a=atoi(argv[1]);
b=atoi(argv[2]);
side1=pow(a,2);
side2=pow(b,2);
side3=sqrt((side1+side2));
printf(“the hypotenuse is %d“,side3);
return 0;
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 57
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a C program to print odd numbers from 7 to 99.

**C Code**:


[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 58
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a c program to count the number of words and characters in a file. File name should be a user input. You have to use at least one macro in this code.

**C Code**:


[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 59
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a C++ program. Using Dynamic Array, read a data file containing some names into a dynamically declared array. Note that the total number of names is not known so your program should determine it. Create a second array that contains the names in alphabetical order. Produce an output file containing the alphabetized list.

According to the question, we have to write a C++ program using Dynamic Array. And Read a data file containing some names into a dynamically declared array. The total number of names is not known so program should determine it. Create a second array that contains the names in alphabetical order. Produce an output file containing the alphabetized list.In step 2 , we will write a C++ program using Dynamic Array

**C++ program Using Dynamic Array :**

```
#include <iostream>
#include <fstream>
using namespace std;

// Read the stream and return its contents
string *getFile(string filename, const int maxUsers, int *size)
{
    string *result = new string[maxUsers];
    ifstream is(filename.c_str());
    *size = 0;
    while (*size < maxUsers && getline(is, result[*size])) {
 ++ *size;
    }
    return result;
}

int main()
{
    int size;
    string *lines = getFile("foo.cpp", 20, &size);
    for (int i=0; i<size; ++i) {
 cout << lines[i] << endl;
    }
    delete[] lines;
    return 0;
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 60
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a C++ program that perform following tasks:

- Create a function Student() that prompt user to a student record. Student contains following details.

- ID, Full Name, Email, Department and Phone Number.

- Store the input in file student.txt

- In main program call function Student()

- Program should prompt user that you want to enter a new record. If ‘Y’ ask user for new details. If ‘N’, program should terminate. (Use event controlled loop)


[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 61
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a C++ program that accepts upper, lower limits of a sequence and increment. The entered number should be within 1 and 100 (both limits included). Use for loop and while loop to show their differences.

```
#include <iostream>
using namespace std;
 
int main()
{
    int arr[100];
    int size, i, j, temp;
 
    // Reading the size of the array
    cout<<"Enter size of array: ";
    cin>>size;
 
    //Reading elements of array
    cout<<"Enter elements in array: ";
    for(i=0; i<size; i++)
    {
        cin>>arr[i];
    }
    //Sorting an array in ascending order
    for(i=0; i<size; i++)
    {
        for(j=i+1; j<size; j++)
        {
            //If there is a smaller element found on the right of the array then swap it.
            if(arr[j] < arr[i])
            {
                temp = arr[i];
                arr[i] = arr[j];
                arr[j] = temp;
            }
        }
    }
    //Printing the sorted array in ascending order
    cout<<"Elements of array in sorted ascending order:"<<endl;
    for(i=0; i<size; i++)
    {
        cout<<arr[i]<<endl;
    }
 
    return 0;
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 62
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a C++ program that displays factorial of an input integer number entered by the user.

```
#include <iostream>
using namespace std;

int main()
{
    int n;
    unsigned long long factorial = 1;

    cout << "Enter a positive integer: ";
    cin >> n;

    if (n < 0)
        cout << "Error! Factorial of a negative number doesn't exist.";
    else {
        for(int i = 1; i <=n; ++i) {
            factorial *= i;
        }
        cout << "Factorial of " << n << " = " << factorial;    
    }

    return 0;
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 63
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a C++ program that displays all CAPITAL English alphabets and small English Alphabets.

```
#include <iostream> 
using namespace std; 
  
// Function to print the alphabet 
// in lower case 
void lowercaseAlphabets() 
{ 
    // lowercase 
  
    for (int c = 97; c <= 122; ++c) 
        cout << c << " "; 
  
    cout << endl; 
} 
// Function to print the 

// C++ program to print alphabets 
#include <iostream> 
using namespace std; 
  
// Function to print the alphabet 
// in lower case 
void lowercaseAlphabets() 
{ 
    // lowercase 
  
    for (int c = 97; c <= 122; ++c) 
        cout << c << " "; 
  
    cout << endl; 
} 
// Function to print the alphabet 
// in upper case 
void uppercaseAlphabets() 
{ 
  
    // uppercase 
    for (int c = 65; c <= 90; ++c) 
        cout << c << " "; 
  
    cout << endl; 
} 
  
// Driver code 
int main() 
{ 
  
    cout << "Uppercase Alphabets" << endl; 
    uppercaseAlphabets(ch); 
  
    cout << "Lowercase Alphabets " << endl; 
    lowercaseAlphabets(ch); 
  
    return 0; 
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]

TCS NQT Coding Question 64
[s2If current_user_can(access_s2member_level1)]

**Question**: Write a C++ program to sort a numeric array and a string array.

```
#include <iostream>
#include <string>
#include <algorithm>
#include <vector>
using namespace std;
int main()
{
    //Declaring the vector
    vector<int>num_arr = {100,20,30,-50,0,56,445,-98,108};
    int i;
    cout<<"Original Numeric Array :\n";
    
    for (i = 0; i < num_arr.size(); ++i)
    {
        cout<<num_arr.at(i)<<" "; 
    }
    
    // Sorting the data
    sort(num_arr.begin(), num_arr.end());
    
    cout<<"\nNumeric Array after sorting :\n";
    for (i = 0 ; i < num_arr.size() ; ++i)
    {
        cout<<num_arr.at(i)<<" "; 
    }
    
    //Declaring the vector
    vector<string> Data = {"abc", "def","xyz"};
    cout<<"\nOriginal String Array : \n";
    
    for(i = 0 ; i<Data.size() ; i++)
    {
        cout <<Data.at(i)<<" ";
    }
    
    // Sorting the data
    sort(Data.begin(),Data.end());
    cout<<"\nString Array after sorting :\n";
    for(i = 0 ; i < Data.size() ; i++)
    {
        cout <<Data.at(i)<<" ";
    }
    return 0;
}
```

[/s2If]

[s2If !current_user_can(access_s2member_level1)]

[/s2If]
{% endraw %}
