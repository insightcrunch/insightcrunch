---
layout: post
title: "TCS Ninja Coding: Beginner to Job-Ready"
page_title: "TCS Ninja Coding Questions - Complete Beginner-Friendly Guide with Solutions in C, C++, Java, and Python"
date: 2023-09-22
categories: ["Industry"]
tags: ["TCS Ninja coding", "TCS coding beginners", "TCS Foundation coding", "TCS command line", "TCS coding solutions"]
excerpt: "From zero coding knowledge to cracking TCS Ninja coding round. Step-by-step guide with solutions in four languages for beginners."
image: "/assets/images/blog/blog-07.webp"
reading_time: 60
author: "Insight Crunch Team"
---

The TCS Ninja Foundation Coding section is the section that ends the most careers before they begin. Candidates who score well in aptitude and reasoning often discover that their coding section produced zero output - and in TCS's evaluation, zero output means zero marks, regardless of how close the logic was. This is not a section where partial credit saves you. Either your program compiles, runs, and produces correct output, or it does not. This guide makes that outcome achievable for every candidate, including non-CS students and those who have not written code in years. The explanations start from scratch and the solutions are given in all four TCS-supported languages with line-by-line comments explaining every single step.

![TCS Guide](/assets/images/blog/blog-07.webp)

## The TCS Ninja Foundation Coding Environment

### What You Are Facing

The Foundation Coding section gives you one programming problem and thirty minutes to solve it. One problem. Thirty minutes. This is a generous time allocation for a single problem at Foundation difficulty - enough time to think through the problem, write the code, test it mentally, and fix any bugs. The pressure is not the time - it is the unfamiliarity with the environment and the input-handling approach that trips most candidates.

### Languages Available

TCS iON supports four languages for Foundation Coding:
- **C** (most restrictive, no object-oriented features, manual memory management)
- **C++** (C with classes and STL, the most powerful option)
- **Java** (object-oriented, robust standard library, slightly verbose)
- **Python** (most concise, most readable, slowest at runtime but fast enough for Foundation problems)

**Recommendation:** Use the language you know best from your college coursework. The problems are at a difficulty level where the language choice matters less than your fluency in it. If you are equally comfortable in multiple languages, Python gives you the most concise solutions and Java gives you the most structured solutions with good library support.

### The Critical Input Handling Decision

This is the most important technical detail in this entire guide. TCS iON Foundation Coding problems can provide input in two ways, and using the wrong method means your program reads nothing and produces wrong output.

**Method 1: Command Line Arguments (most common in TCS Ninja)**

Input values are passed as arguments when the program is run. Your program must read them from the `args` array in Java/Python or from `argc`/`argv` in C/C++. This is NOT the same as `scanf()` or `input()`.

**Method 2: Standard Input (stdin)**

Input is typed or piped into the program as it runs. Your program reads it with `scanf()` in C/C++, `Scanner` in Java, or `input()` in Python.

**How to know which method the problem uses:** The problem statement will show an example of how the program is called. If it shows something like `./program 5 10` or `java Main 5 10`, that is command line arguments. If it shows input being provided on separate lines below the program execution, that is standard input.

**The safest approach:** Read the problem statement carefully and note the input format shown in the example. Then use the appropriate method. This guide covers both methods for every problem.

---

## Understanding Command Line Arguments

### In C and C++

```c
#include <stdio.h>
#include <stdlib.h>  /* for atoi() */

int main(int argc, char *argv[]) {
    /* argc = number of arguments (including the program name itself) */
    /* argv[0] = program name */
    /* argv[1] = first actual argument, argv[2] = second, etc. */

    /* To read an integer from the first argument: */
    int n = atoi(argv[1]);  /* atoi converts string "42" to integer 42 */

    printf("You entered: %d\n", n);
    return 0;
}
```

**If called as:** `./program 42`
**Output:** `You entered: 42`

The `atoi()` function (in `stdlib.h`) converts a string to an integer. It is essential for command line argument handling in C/C++. For doubles, use `atof()`. For longs, use `atol()`.

### In Java

```java
public class Main {
    public static void main(String[] args) {
        /* args[0] = first argument, args[1] = second, etc. */
        /* Unlike C, there is no program name in args[0] */

        int n = Integer.parseInt(args[0]);  /* parse first argument as integer */

        System.out.println("You entered: " + n);
    }
}
```

**If called as:** `java Main 42`
**Output:** `You entered: 42`

### In Python

```python
import sys  # sys.argv contains command line arguments

# sys.argv[0] = script name
# sys.argv[1] = first actual argument

n = int(sys.argv[1])  # convert first argument from string to integer

print("You entered:", n)
```

**If called as:** `python program.py 42`
**Output:** `You entered: 42`

### Understanding atoi() in C - The Most Important Function

`atoi` stands for "ASCII to Integer." It converts a character string like `"123"` to the integer `123`. This function is critical because command line arguments always arrive as strings, even when they represent numbers.

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    /* Reading two integers from command line */
    int a = atoi(argv[1]);  /* First argument */
    int b = atoi(argv[2]);  /* Second argument */

    printf("Sum: %d\n", a + b);
    printf("Product: %d\n", a * b);
    return 0;
}
```

**If called as:** `./program 6 7`
**Output:**
```
Sum: 13
Product: 42
```

---

## Standard Input: The scanf/input Approach

For problems where input is provided via standard input (not command line):

### In C

```c
#include <stdio.h>

int main() {
    int n;
    scanf("%d", &n);  /* Read one integer */
    printf("You entered: %d\n", n);
    return 0;
}
```

### In C++

```cpp
#include <iostream>
using namespace std;

int main() {
    int n;
    cin >> n;  /* Read one integer */
    cout << "You entered: " << n << endl;
    return 0;
}
```

### In Java (Scanner)

```java
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        System.out.println("You entered: " + n);
    }
}
```

### In Python

```python
n = int(input())  # Read one integer from standard input
print("You entered:", n)
```

---

## Core Concept: The Basic Program Structure

Every TCS Ninja coding solution follows this structure. Understand it before any problem.

### Minimum Working C Program

```c
#include <stdio.h>   /* Required for printf and scanf */
#include <stdlib.h>  /* Required for atoi */
#include <string.h>  /* Required for strlen, strcmp, strcpy */
#include <math.h>    /* Required for sqrt, pow */

int main(int argc, char *argv[]) {
    /* Read input from command line */
    int n = atoi(argv[1]);

    /* Your logic here */

    /* Print output */
    printf("%d\n", n);

    return 0;  /* 0 means success */
}
```

### Minimum Working Java Program

```java
public class Main {  /* Class name MUST be Main */
    public static void main(String[] args) {
        /* Read input from command line */
        int n = Integer.parseInt(args[0]);

        /* Your logic here */

        /* Print output */
        System.out.println(n);
    }
}
```

### Minimum Working Python Program

```python
import sys

# Read input from command line
n = int(sys.argv[1])

# Your logic here

# Print output
print(n)
```

---

## Foundation Problem 1: Sum and Difference of Two Numbers

**Problem:** A program receives two integers A and B. Print their sum, difference (A-B), product, and quotient (A/B, use integer division).

**Example:** Input: 15 4
Output:
```
Sum: 19
Difference: 11
Product: 60
Quotient: 3
```

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int a = atoi(argv[1]);  /* First number from command line */
    int b = atoi(argv[2]);  /* Second number from command line */

    printf("Sum: %d\n", a + b);        /* Addition */
    printf("Difference: %d\n", a - b); /* Subtraction */
    printf("Product: %d\n", a * b);    /* Multiplication */
    printf("Quotient: %d\n", a / b);   /* Integer division (3.75 becomes 3) */

    return 0;
}
```

### Solution in Java

```java
public class Main {
    public static void main(String[] args) {
        int a = Integer.parseInt(args[0]);  /* Convert first arg to int */
        int b = Integer.parseInt(args[1]);  /* Convert second arg to int */

        System.out.println("Sum: " + (a + b));        /* Note: brackets around a+b */
        System.out.println("Difference: " + (a - b)); /* prevent string concatenation */
        System.out.println("Product: " + (a * b));
        System.out.println("Quotient: " + (a / b));   /* Java integer division */
    }
}
```

**Important Java note:** `"Sum: " + a + b` would give `"Sum: 154"` not `"Sum: 19"` because `+` with a string does concatenation left-to-right. Use `(a + b)` with brackets to force arithmetic first.

### Solution in Python

```python
import sys

a = int(sys.argv[1])  # Convert first argument to integer
b = int(sys.argv[2])  # Convert second argument to integer

print("Sum:", a + b)
print("Difference:", a - b)
print("Product:", a * b)
print("Quotient:", a // b)  # // is integer division in Python (/ gives float)
```

### Solution in C++

```cpp
#include <iostream>
#include <cstdlib>  /* for atoi */
using namespace std;

int main(int argc, char *argv[]) {
    int a = atoi(argv[1]);
    int b = atoi(argv[2]);

    cout << "Sum: " << (a + b) << endl;
    cout << "Difference: " << (a - b) << endl;
    cout << "Product: " << (a * b) << endl;
    cout << "Quotient: " << (a / b) << endl;

    return 0;
}
```

---

## Foundation Problem 2: Even or Odd with Conditional Logic

**Problem:** Given an integer N, print "Even" if it is divisible by 2, otherwise print "Odd".

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);

    if (n % 2 == 0) {         /* % is modulo - gives remainder after division */
        printf("Even\n");     /* remainder 0 means divisible by 2 */
    } else {
        printf("Odd\n");      /* any other remainder means odd */
    }

    return 0;
}
```

### Solution in Python

```python
import sys

n = int(sys.argv[1])

if n % 2 == 0:      # % is modulo operator
    print("Even")
else:
    print("Odd")
```

### Solution in Java

```java
public class Main {
    public static void main(String[] args) {
        int n = Integer.parseInt(args[0]);

        if (n % 2 == 0) {
            System.out.println("Even");
        } else {
            System.out.println("Odd");
        }
    }
}
```

---

## Foundation Problem 3: Loops - Print a Series

**Problem:** Given N, print all numbers from 1 to N, one per line.

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    int i;  /* loop variable - declare before use in C89 */

    for (i = 1; i <= n; i++) {  /* start at 1, go up to n inclusive */
        printf("%d\n", i);       /* print each number on new line */
    }

    return 0;
}
```

### Solution in Python

```python
import sys

n = int(sys.argv[1])

for i in range(1, n + 1):  # range(1, n+1) gives 1, 2, 3, ..., n
    print(i)
```

**Why n+1 in range?** Python's `range(start, stop)` generates numbers from `start` up to but NOT including `stop`. So `range(1, 6)` gives `1, 2, 3, 4, 5`. To include n, write `range(1, n+1)`.

### Solution in Java

```java
public class Main {
    public static void main(String[] args) {
        int n = Integer.parseInt(args[0]);

        for (int i = 1; i <= n; i++) {  /* i starts at 1, increments by 1, stops at n */
            System.out.println(i);
        }
    }
}
```

---

## Foundation Problem 4: Factorial

**Problem:** Given a non-negative integer N, compute N! (N factorial). N! = N x (N-1) x ... x 2 x 1. Special case: 0! = 1.

**Example:** Input: 5 → Output: 120 (because 5 x 4 x 3 x 2 x 1 = 120)

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    long long factorial = 1;  /* long long for large factorials (up to 20!) */
    int i;

    if (n == 0) {             /* 0! = 1 by definition */
        printf("1\n");
        return 0;
    }

    for (i = 1; i <= n; i++) {
        factorial = factorial * i;  /* multiply current result by next number */
    }

    printf("%lld\n", factorial);  /* %lld for long long */
    return 0;
}
```

### Solution in Python

```python
import sys

n = int(sys.argv[1])
factorial = 1  # start with 1 (multiplicative identity)

for i in range(1, n + 1):  # multiply 1, 2, 3, ..., n
    factorial = factorial * i

print(factorial)
```

**Python advantage:** Python integers handle arbitrarily large numbers automatically. No overflow risk even for 100!.

### Solution in Java

```java
public class Main {
    public static void main(String[] args) {
        int n = Integer.parseInt(args[0]);
        long factorial = 1;  /* long handles up to 20! */

        for (int i = 1; i <= n; i++) {
            factorial *= i;  /* *= is shorthand for factorial = factorial * i */
        }

        System.out.println(factorial);
    }
}
```

### Solution in C++

```cpp
#include <iostream>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    long long factorial = 1;

    for (int i = 1; i <= n; i++) {
        factorial *= i;
    }

    cout << factorial << endl;
    return 0;
}
```

---

## Foundation Problem 5: Fibonacci Series

**Problem:** Given N, print the first N Fibonacci numbers separated by spaces. The Fibonacci sequence is: 0, 1, 1, 2, 3, 5, 8, 13, 21, ...
Each number is the sum of the two preceding numbers.

**Example:** Input: 7 → Output: 0 1 1 2 3 5 8

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    long long a = 0, b = 1;  /* first two Fibonacci numbers */
    int i;

    if (n == 1) {
        printf("0\n");
        return 0;
    }

    printf("0 ");  /* print first */
    printf("1");   /* print second (no trailing space after last) */

    for (i = 3; i <= n; i++) {       /* generate from 3rd term onward */
        long long next = a + b;      /* next = sum of previous two */
        printf(" %lld", next);       /* space before each number after first */
        a = b;                       /* shift: a becomes old b */
        b = next;                    /* shift: b becomes the new number */
    }

    printf("\n");
    return 0;
}
```

### Solution in Python

```python
import sys

n = int(sys.argv[1])

if n == 1:
    print(0)
elif n == 2:
    print("0 1")
else:
    fibs = [0, 1]             # start with first two
    for i in range(2, n):     # generate n-2 more terms
        fibs.append(fibs[-1] + fibs[-2])  # append sum of last two
    print(" ".join(map(str, fibs)))  # join all numbers with spaces
```

**Python note:** `map(str, fibs)` converts each number to a string. `" ".join(...)` joins them with a space between each.

### Solution in Java

```java
public class Main {
    public static void main(String[] args) {
        int n = Integer.parseInt(args[0]);
        long a = 0, b = 1;

        StringBuilder sb = new StringBuilder();

        for (int i = 0; i < n; i++) {
            if (i > 0) sb.append(" ");  /* space between numbers, not after last */
            sb.append(a);               /* add current Fibonacci number */
            long next = a + b;          /* compute next */
            a = b;                      /* shift */
            b = next;
        }

        System.out.println(sb.toString());
    }
}
```

---

## Foundation Problem 6: Prime Number Check

**Problem:** Given N, determine if it is a prime number. Print "Prime" or "Not Prime".

A prime number has exactly two factors: 1 and itself. 1 is not prime.

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>
#include <math.h>    /* for sqrt() */

int isPrime(int n) {  /* separate function for clean code */
    int i;

    if (n < 2) return 0;   /* 0 and 1 are not prime */
    if (n == 2) return 1;  /* 2 is the only even prime */
    if (n % 2 == 0) return 0;  /* all other even numbers are not prime */

    /* Check odd divisors from 3 up to square root of n */
    for (i = 3; i * i <= n; i += 2) {
        if (n % i == 0) return 0;  /* found a divisor, not prime */
    }

    return 1;  /* no divisor found, it is prime */
}

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);

    if (isPrime(n)) {
        printf("Prime\n");
    } else {
        printf("Not Prime\n");
    }

    return 0;
}
```

**Why check only up to sqrt(n)?** If n has a factor larger than its square root, it must also have a corresponding factor smaller than its square root. So checking up to sqrt(n) is sufficient and much faster.

### Solution in Python

```python
import sys
import math

def is_prime(n):
    if n < 2:
        return False         # 0 and 1 are not prime
    if n == 2:
        return True          # 2 is prime
    if n % 2 == 0:
        return False         # even numbers > 2 are not prime
    for i in range(3, int(math.sqrt(n)) + 1, 2):  # check odd numbers to sqrt
        if n % i == 0:
            return False     # found a divisor
    return True

n = int(sys.argv[1])
print("Prime" if is_prime(n) else "Not Prime")
```

### Solution in Java

```java
public class Main {
    static boolean isPrime(int n) {
        if (n < 2) return false;
        if (n == 2) return true;
        if (n % 2 == 0) return false;
        for (int i = 3; (long) i * i <= n; i += 2) {  /* cast to long to avoid overflow */
            if (n % i == 0) return false;
        }
        return true;
    }

    public static void main(String[] args) {
        int n = Integer.parseInt(args[0]);
        System.out.println(isPrime(n) ? "Prime" : "Not Prime");
    }
}
```

---

## Foundation Problem 7: Armstrong Number

**Problem:** An Armstrong number (also called narcissistic number) of k digits satisfies: sum of each digit raised to power k equals the number. Determine if N is an Armstrong number.

**Examples:** 153 = 1³ + 5³ + 3³ = 153 ✓ (3 digits). 1634 = 1⁴ + 6⁴ + 3⁴ + 4⁴ = 1634 ✓ (4 digits).

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    int original = n;     /* save original to compare at end */
    int k = strlen(argv[1]);  /* number of digits = length of string argument */
    int sum = 0;
    int temp = n;

    /* Sum each digit raised to power k */
    while (temp > 0) {
        int digit = temp % 10;          /* extract last digit */
        sum += (int)pow(digit, k);      /* add digit^k to sum */
        temp /= 10;                     /* remove last digit */
    }

    if (sum == original) {
        printf("Armstrong\n");
    } else {
        printf("Not Armstrong\n");
    }

    return 0;
}
```

### Solution in Python

```python
import sys

n = int(sys.argv[1])
digits = str(n)        # convert to string to count digits easily
k = len(digits)        # number of digits

total = sum(int(d) ** k for d in digits)  # sum of each digit^k

if total == n:
    print("Armstrong")
else:
    print("Not Armstrong")
```

**Python advantage:** The one-liner `sum(int(d) ** k for d in digits)` is compact and clean - iterate through each character in the string, convert to int, raise to power k, and sum all results.

### Solution in Java

```java
public class Main {
    public static void main(String[] args) {
        int n = Integer.parseInt(args[0]);
        int original = n;
        int k = args[0].length();  /* number of digits from the string argument */
        int sum = 0;
        int temp = n;

        while (temp > 0) {
            int digit = temp % 10;
            sum += (int) Math.pow(digit, k);  /* Math.pow returns double, cast to int */
            temp /= 10;
        }

        System.out.println(sum == original ? "Armstrong" : "Not Armstrong");
    }
}
```

---

## Foundation Problem 8: Palindrome Number

**Problem:** A palindrome number reads the same forwards and backwards. Determine if N is a palindrome.

**Examples:** 121 ✓, 1331 ✓, 12321 ✓, 123 ✗

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    int original = n;
    int reversed = 0;

    while (n > 0) {
        int digit = n % 10;          /* extract last digit */
        reversed = reversed * 10 + digit;  /* build reversed number */
        n /= 10;                     /* remove last digit */
    }

    if (reversed == original) {
        printf("Palindrome\n");
    } else {
        printf("Not Palindrome\n");
    }

    return 0;
}
```

### Solution in Python

```python
import sys

n_str = sys.argv[1]   # keep as string for easy comparison
n_str_reversed = n_str[::-1]  # Python slice trick: [::-1] reverses a string

if n_str == n_str_reversed:
    print("Palindrome")
else:
    print("Not Palindrome")
```

**Python string reversal:** `s[::-1]` is Python's slice notation meaning "start from end, go backwards, step -1" - effectively reverses the string. This is cleaner than building a reversed number mathematically.

### Solution in Java

```java
public class Main {
    public static void main(String[] args) {
        int n = Integer.parseInt(args[0]);
        int original = n;
        int reversed = 0;

        while (n > 0) {
            int digit = n % 10;
            reversed = reversed * 10 + digit;
            n /= 10;
        }

        System.out.println(reversed == original ? "Palindrome" : "Not Palindrome");
    }
}
```

---

## Foundation Problem 9: Digit Sum

**Problem:** Find the sum of all digits of a given number N.

**Example:** Input: 4567 → Output: 22 (4 + 5 + 6 + 7)

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    int sum = 0;

    while (n > 0) {
        sum += n % 10;  /* add last digit to sum */
        n /= 10;        /* remove last digit */
    }

    printf("%d\n", sum);
    return 0;
}
```

### Solution in Python

```python
import sys

n_str = sys.argv[1]
total = sum(int(d) for d in n_str)  # sum each character (digit) converted to int
print(total)
```

### Solution in Java

```java
public class Main {
    public static void main(String[] args) {
        int n = Integer.parseInt(args[0]);
        int sum = 0;

        while (n > 0) {
            sum += n % 10;
            n /= 10;
        }

        System.out.println(sum);
    }
}
```

---

## Foundation Problem 10: Reverse a Number

**Problem:** Given an integer N, print the digits in reverse order.

**Example:** Input: 12345 → Output: 54321. Input: 1200 → Output: 21 (leading zeros dropped as an integer)

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    long n = atol(argv[1]);  /* use long to handle larger numbers */
    long reversed = 0;

    while (n > 0) {
        reversed = reversed * 10 + (n % 10);  /* append each digit to reversed */
        n /= 10;
    }

    printf("%ld\n", reversed);
    return 0;
}
```

### Solution in Python

```python
import sys

n_str = sys.argv[1]
print(int(n_str[::-1]))  # reverse string, convert to int (drops leading zeros)
```

---

## Foundation Problem 11: Array Operations - Maximum, Minimum, Sum

**Problem:** Given N numbers as command line arguments, find the maximum, minimum, and sum.

**Example:** Input: 5 3 8 1 9 2 → Output:
```
Max: 9
Min: 1
Sum: 28
```

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = argc - 1;  /* number of actual arguments (minus program name) */
    int arr[1000];     /* array to store the numbers */
    int i;

    /* Read all arguments into array */
    for (i = 0; i < n; i++) {
        arr[i] = atoi(argv[i + 1]);  /* argv[1] is first number, etc. */
    }

    /* Find max, min, sum */
    int max = arr[0];   /* assume first element is max */
    int min = arr[0];   /* assume first element is min */
    long sum = 0;

    for (i = 0; i < n; i++) {
        if (arr[i] > max) max = arr[i];
        if (arr[i] < min) min = arr[i];
        sum += arr[i];
    }

    printf("Max: %d\n", max);
    printf("Min: %d\n", min);
    printf("Sum: %ld\n", sum);

    return 0;
}
```

### Solution in Python

```python
import sys

# sys.argv[1:] is all arguments after the script name, as a list
numbers = [int(x) for x in sys.argv[1:]]  # convert each to int

print("Max:", max(numbers))   # Python built-in max()
print("Min:", min(numbers))   # Python built-in min()
print("Sum:", sum(numbers))   # Python built-in sum()
```

**Python advantage:** Built-in `max()`, `min()`, and `sum()` functions work directly on a list, eliminating the need for manual loop logic.

### Solution in Java

```java
public class Main {
    public static void main(String[] args) {
        int n = args.length;  /* number of arguments */
        int[] arr = new int[n];

        for (int i = 0; i < n; i++) {
            arr[i] = Integer.parseInt(args[i]);
        }

        int max = arr[0];
        int min = arr[0];
        long sum = 0;

        for (int x : arr) {  /* enhanced for-loop: x takes each value in arr */
            if (x > max) max = x;
            if (x < min) min = x;
            sum += x;
        }

        System.out.println("Max: " + max);
        System.out.println("Min: " + min);
        System.out.println("Sum: " + sum);
    }
}
```

---

## Foundation Problem 12: Sorting an Array (Bubble Sort)

**Problem:** Given N numbers, sort them in ascending order and print the sorted sequence.

**Example:** Input: 5 3 1 4 2 → Output: 1 2 3 4 5

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = argc - 1;
    int arr[1000];
    int i, j;

    for (i = 0; i < n; i++) {
        arr[i] = atoi(argv[i + 1]);
    }

    /* Bubble sort: repeatedly swap adjacent elements if out of order */
    for (i = 0; i < n - 1; i++) {
        for (j = 0; j < n - 1 - i; j++) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];      /* swap arr[j] and arr[j+1] */
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }

    /* Print sorted array */
    for (i = 0; i < n; i++) {
        if (i > 0) printf(" ");
        printf("%d", arr[i]);
    }
    printf("\n");

    return 0;
}
```

### Solution in Python

```python
import sys

numbers = [int(x) for x in sys.argv[1:]]
numbers.sort()  # Python built-in sort, in-place
print(" ".join(map(str, numbers)))
```

### Solution in Java

```java
import java.util.Arrays;

public class Main {
    public static void main(String[] args) {
        int n = args.length;
        int[] arr = new int[n];

        for (int i = 0; i < n; i++) {
            arr[i] = Integer.parseInt(args[i]);
        }

        Arrays.sort(arr);  /* Java built-in sort */

        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) {
            if (i > 0) sb.append(" ");
            sb.append(arr[i]);
        }
        System.out.println(sb.toString());
    }
}
```

---

## Foundation Problem 13: Pattern Printing

**Problem:** Given N, print a right-angled triangle pattern of stars with N rows.

**Example:** Input: 4
```
*
* *
* * *
* * * *
```

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    int i, j;

    for (i = 1; i <= n; i++) {     /* outer loop: row number */
        for (j = 1; j <= i; j++) { /* inner loop: stars in row i */
            if (j > 1) printf(" ");
            printf("*");
        }
        printf("\n");               /* newline after each row */
    }

    return 0;
}
```

### Solution in Python

```python
import sys

n = int(sys.argv[1])

for i in range(1, n + 1):
    print(" ".join(["*"] * i))  # create list of i stars, join with spaces
```

**Python note:** `["*"] * i` creates a list with i copies of `"*"`. `" ".join(...)` joins them with spaces.

### Solution in Java

```java
public class Main {
    public static void main(String[] args) {
        int n = Integer.parseInt(args[0]);

        for (int i = 1; i <= n; i++) {
            StringBuilder sb = new StringBuilder();
            for (int j = 1; j <= i; j++) {
                if (j > 1) sb.append(" ");
                sb.append("*");
            }
            System.out.println(sb.toString());
        }
    }
}
```

---

## Foundation Problem 14: String Reversal

**Problem:** Given a string, print it in reverse.

**Example:** Input: "hello" → Output: "olleh"

### Solution in C

```c
#include <stdio.h>
#include <string.h>

int main(int argc, char *argv[]) {
    char *str = argv[1];          /* the string argument */
    int len = strlen(str);        /* length of the string */
    int i;

    /* Print from last character to first */
    for (i = len - 1; i >= 0; i--) {
        printf("%c", str[i]);    /* %c for single character */
    }
    printf("\n");

    return 0;
}
```

### Solution in Python

```python
import sys

s = sys.argv[1]
print(s[::-1])  # reverse the string using slice notation
```

### Solution in Java

```java
public class Main {
    public static void main(String[] args) {
        String s = args[0];
        String reversed = new StringBuilder(s).reverse().toString();
        System.out.println(reversed);
    }
}
```

---

## Foundation Problem 15: The TCS Narrative-Style Problem

TCS Ninja coding problems are often presented as real-world scenarios to make them seem complex. Recognising the underlying logic is the key skill.

**Problem:** "Rohit is planning a road trip. The distance from his home to the destination is D kilometres. His car gives M kilometres per litre of fuel. Fuel costs Rs. P per litre. If Rohit wants to make the trip and return, what is the total fuel cost? Print the result rounded to two decimal places."

**What this actually is:** (2 x D / M) x P - simple arithmetic with three variables.

### Solution in Python (most concise for narrative problems)

```python
import sys

D = float(sys.argv[1])  # distance to destination
M = float(sys.argv[2])  # mileage (km per litre)
P = float(sys.argv[3])  # fuel price per litre

total_distance = 2 * D          # round trip
litres_needed = total_distance / M  # fuel required
total_cost = litres_needed * P   # total cost

print(f"{total_cost:.2f}")  # :.2f formats to 2 decimal places
```

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    double D = atof(argv[1]);  /* atof converts string to double */
    double M = atof(argv[2]);
    double P = atof(argv[3]);

    double total_cost = (2 * D / M) * P;

    printf("%.2f\n", total_cost);  /* %.2f = 2 decimal places */
    return 0;
}
```

### Solution in Java

```java
public class Main {
    public static void main(String[] args) {
        double D = Double.parseDouble(args[0]);  /* parse as decimal number */
        double M = Double.parseDouble(args[1]);
        double P = Double.parseDouble(args[2]);

        double totalCost = (2 * D / M) * P;

        System.out.printf("%.2f%n", totalCost);  /* printf for formatted output */
    }
}
```

---

## The Five Most Common TCS Ninja Coding Mistakes

### Mistake 1: Not Printing Any Output

The most catastrophic mistake. Some candidates write code that computes the correct answer internally but stores it in a variable without printing it. If no output is printed, the judge receives a blank answer and scores zero.

**Always verify:** Does your code have at least one `printf`/`print`/`println`/`cout` that will execute for the given input?

### Mistake 2: Wrong Input Method

Using `scanf()` when the problem expects command line arguments, or using `argv` when the problem provides standard input. Re-read the input format description and the example in the problem statement before writing a single line of code.

### Mistake 3: Missing Headers/Imports

Calling `atoi()` in C without `#include <stdlib.h>`, or using `Math.pow()` in Java without `import java.lang.Math` (not needed, it is auto-imported), or using `sqrt()` in C without `#include <math.h>`.

The safest approach: start every C program with these includes:
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
```

And every Java program with:
```java
import java.util.*;
import java.io.*;
```

These cover all standard functions you will need.

### Mistake 4: Off-by-One in Loops

The difference between `i < n` and `i <= n` in a loop determines whether the loop runs n or n+1 times. Printing 1 to N requires `i <= n` (or equivalent). Accessing an array of N elements requires `i < n` (indices 0 to N-1). Getting these backwards causes either missing output or an array index out-of-bounds runtime error.

**Mental check:** After writing every loop, ask: "What is the first value? What is the last value? Is the last value correct?"

### Mistake 5: Integer Overflow

Multiplying two large `int` values and storing the result in an `int` variable silently overflows in C and Java. Factorials, sums of large arrays, and power calculations are common overflow traps.

**Rule:** If a calculation might produce a result greater than 2 billion (2,147,483,647), use `long` in Java/C, `long long` in C/C++, or trust Python's automatic big-integer handling.

---

## The 2-Week Zero-to-Ready Plan for Non-CS Students

This plan is designed for candidates from non-CS streams (ECE, Mechanical, Civil, Chemical) or CS candidates who have not coded in a while.

### Week 1: Foundations

**Day 1:** Set up your coding environment. Download and install a C compiler (gcc) or use an online compiler (onlinegdb.com). Write and run the "Sum and Difference" problem from this guide. Verify you can compile and see output. This setup step alone is what many candidates skip - do it first.

**Day 2:** Learn variables, data types (int, float, double, char), and basic arithmetic operators. Write 5 programs that read two numbers and perform arithmetic operations. Focus on getting output on screen.

**Day 3:** Learn conditional logic (if, else if, else). Write programs for: even/odd check, largest of three numbers, grade assignment (A/B/C/D/F based on marks), positive/negative/zero classification.

**Day 4:** Learn loops (for, while). Write programs for: print 1 to N, print N to 1, print even numbers from 1 to N, print multiplication table of N.

**Day 5:** Loops continued. Write programs for: sum of first N numbers, count of digits in a number, print all factors of N.

**Day 6:** Practice day. Write the factorial, Fibonacci, and digit sum programs from this guide without looking at the solutions. Then compare with the guide solutions and note differences.

**Day 7:** Rest and review. Read through all Week 1 programs you wrote. Fix any that had errors.

### Week 2: Problem Types

**Day 8:** Mathematical checks. Write programs for: prime number check, Armstrong number, palindrome number check. These are the most commonly tested individual programs in TCS Ninja.

**Day 9:** Strings. Write programs for: string reversal (using loop or built-in), counting vowels in a string, checking if a string is a palindrome.

**Day 10:** Arrays. Write programs for: find max/min of an array, sum and average of an array, count occurrences of a value in an array.

**Day 11:** Sorting and searching. Write a bubble sort program. Write a program that checks if a value exists in an array.

**Day 12:** Pattern printing. Write programs for: right-angled star triangle, inverted triangle, number pyramid. These test nested loop understanding.

**Day 13:** Narrative-style problems. Take three problems from the internet framed as "real-world scenarios" and strip them down to their underlying arithmetic. Write solutions.

**Day 14:** Full mock test. Set a 30-minute timer. Pick one problem you have not yet seen (from a practice website). Solve it completely - read, design logic, write code, test with sample input, verify output.

---

## Quick Reference: Input/Output Syntax Across Languages

| Task | C | Java | Python |
|---|---|---|---|
| Read int from argv | `atoi(argv[1])` | `Integer.parseInt(args[0])` | `int(sys.argv[1])` |
| Read double from argv | `atof(argv[1])` | `Double.parseDouble(args[0])` | `float(sys.argv[1])` |
| Read string from argv | `argv[1]` (already string) | `args[0]` (already string) | `sys.argv[1]` |
| Read int from stdin | `scanf("%d", &n)` | `sc.nextInt()` | `int(input())` |
| Print integer | `printf("%d\n", n)` | `System.out.println(n)` | `print(n)` |
| Print string | `printf("%s\n", s)` | `System.out.println(s)` | `print(s)` |
| Print 2 decimal places | `printf("%.2f\n", x)` | `System.out.printf("%.2f%n", x)` | `print(f"{x:.2f}")` |
| String length | `strlen(s)` | `s.length()` | `len(s)` |
| Number of args | `argc - 1` | `args.length` | `len(sys.argv) - 1` |

---

## After the Coding Section: What TCS Evaluates

The Foundation Coding section evaluates your submission against a set of test cases. Each test case provides a specific input and expects a specific output. Your program must produce the exact expected output - including correct spacing, newlines, capitalisation, and number format.

This means:

**Capitalisation matters.** If the expected output is "Prime" and you print "prime", you score zero for that test case. Check your problem statement for the exact expected strings.

**Spacing matters.** If the expected output has a newline after each number and you print them space-separated, test cases fail. Follow the output format in the example exactly.

**Trailing newlines.** Most judges expect a newline at the end of output. In C, always include `\n` at the end of your last `printf`. In Python, `print()` adds a newline automatically.

**No extra output.** Do not print debug messages like "The answer is:" unless the problem specifies that prefix. Print only exactly what is required.

The simplest way to verify your output format is to run your program with the provided sample input and compare your output character-by-character with the expected output shown in the problem. If they match visually, you are on the right track.

---

## Final Words: The Only Barrier Is Starting

The TCS Ninja coding section is not as intimidating as it appears to candidates who have not written code in a while. The problems test basic programming concepts that are taught in the first two months of any programming course. The time pressure is generous. The input format, once understood, is consistent across problems.

The candidates who fail this section are almost never the ones who lack programming ability. They are the ones who walked in without having practised the input-handling setup, without knowing which method the test uses, or without having verified that a "hello world" program runs correctly on their test environment.

Spend two hours on the setup. Write five programs that read inputs and print outputs. That preparation alone separates you from a significant percentage of candidates who underestimate this section. Add the two-week plan and you will walk in with genuine confidence and genuine competence.

The code is manageable. The concepts are learnable. The only barrier is starting.

---

## Foundation Problem 16: Count Vowels and Consonants in a String

**Problem:** Given a string, count the number of vowels (a, e, i, o, u - both uppercase and lowercase) and consonants. Print both counts.

**Example:** Input: "HelloWorld" → Output: Vowels: 3, Consonants: 7

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>   /* for tolower(), isalpha() */

int main(int argc, char *argv[]) {
    char *str = argv[1];
    int vowels = 0, consonants = 0;
    int i;

    for (i = 0; i < strlen(str); i++) {
        char c = tolower(str[i]);  /* convert to lowercase for uniform check */

        if (isalpha(c)) {          /* only count letters, not digits or spaces */
            if (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u') {
                vowels++;
            } else {
                consonants++;
            }
        }
    }

    printf("Vowels: %d\n", vowels);
    printf("Consonants: %d\n", consonants);
    return 0;
}
```

### Solution in Python

```python
import sys

s = sys.argv[1].lower()   # convert to lowercase
vowels_set = set("aeiou") # a set of vowel characters for fast lookup

vowels = sum(1 for c in s if c in vowels_set and c.isalpha())
consonants = sum(1 for c in s if c.isalpha() and c not in vowels_set)

print(f"Vowels: {vowels}")
print(f"Consonants: {consonants}")
```

### Solution in Java

```java
public class Main {
    public static void main(String[] args) {
        String str = args[0].toLowerCase();
        String vowelChars = "aeiou";
        int vowels = 0, consonants = 0;

        for (int i = 0; i < str.length(); i++) {
            char c = str.charAt(i);
            if (Character.isLetter(c)) {
                if (vowelChars.indexOf(c) != -1) {
                    vowels++;       /* indexOf returns -1 if not found */
                } else {
                    consonants++;
                }
            }
        }

        System.out.println("Vowels: " + vowels);
        System.out.println("Consonants: " + consonants);
    }
}
```

---

## Foundation Problem 17: Check if String is a Palindrome

**Problem:** Given a word, determine if it reads the same forwards and backwards. Ignore case.

**Example:** "Racecar" → "Palindrome". "Hello" → "Not Palindrome"

### Solution in Python

```python
import sys

s = sys.argv[1].lower()       # convert to lowercase
if s == s[::-1]:              # compare string with its reverse
    print("Palindrome")
else:
    print("Not Palindrome")
```

### Solution in Java

```java
public class Main {
    public static void main(String[] args) {
        String s = args[0].toLowerCase();
        String reversed = new StringBuilder(s).reverse().toString();

        if (s.equals(reversed)) {   /* use .equals() to compare strings in Java, not == */
            System.out.println("Palindrome");
        } else {
            System.out.println("Not Palindrome");
        }
    }
}
```

**Critical Java note:** In Java, `s1 == s2` compares object references (memory addresses), not content. To compare string content, always use `s1.equals(s2)`. This is one of the most common beginner Java mistakes.

---

## Foundation Problem 18: Second Largest Element in an Array

**Problem:** Given a list of N integers, find the second largest distinct value.

**Example:** Input: 3 5 1 8 2 8 → Output: 5

### Solution in Python

```python
import sys

numbers = [int(x) for x in sys.argv[1:]]
unique = list(set(numbers))    # remove duplicates
unique.sort(reverse=True)      # sort in descending order
print(unique[1])               # index 1 is the second largest
```

### Solution in Java

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        int n = args.length;
        int max = Integer.MIN_VALUE;      /* smallest possible int */
        int secondMax = Integer.MIN_VALUE;

        for (int i = 0; i < n; i++) {
            int x = Integer.parseInt(args[i]);
            if (x > max) {
                secondMax = max;   /* old max becomes second max */
                max = x;           /* new max found */
            } else if (x > secondMax && x != max) {
                secondMax = x;     /* update second max (must be distinct) */
            }
        }

        System.out.println(secondMax);
    }
}
```

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>
#include <limits.h>  /* for INT_MIN */

int main(int argc, char *argv[]) {
    int n = argc - 1;
    int max = INT_MIN;
    int secondMax = INT_MIN;
    int i;

    for (i = 1; i <= n; i++) {
        int x = atoi(argv[i]);
        if (x > max) {
            secondMax = max;
            max = x;
        } else if (x > secondMax && x != max) {
            secondMax = x;
        }
    }

    printf("%d\n", secondMax);
    return 0;
}
```

---

## Foundation Problem 19: Count Occurrences of a Digit in a Number

**Problem:** Given a number N and a digit D, count how many times D appears in N.

**Example:** Input: 12321 3 → Output: 1. Input: 11211 1 → Output: 4

### Solution in Python

```python
import sys

n_str = sys.argv[1]  # number as string (no need to convert to int)
d = sys.argv[2]      # digit as string (single character)

count = n_str.count(d)  # Python string count method counts occurrences
print(count)
```

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    char *n_str = argv[1];  /* number as string */
    int digit = atoi(argv[2]);  /* digit to search for (as int) */
    int count = 0;
    int i;

    for (i = 0; n_str[i] != '\0'; i++) {  /* '\0' is the null terminator at string end */
        if (n_str[i] - '0' == digit) {    /* convert char to int by subtracting '0' */
            count++;
        }
    }

    printf("%d\n", count);
    return 0;
}
```

**Key concept - char to int conversion in C:** Characters are stored as their ASCII codes. The character '0' has ASCII value 48, '1' has value 49, etc. So `'5' - '0' = 53 - 48 = 5`, converting the character digit to its integer value.

---

## Foundation Problem 20: Number Pyramid Pattern

**Problem:** Given N, print a number pyramid where row i contains numbers 1 through i.

**Example:** Input: 4
```
1
1 2
1 2 3
1 2 3 4
```

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    int i, j;

    for (i = 1; i <= n; i++) {
        for (j = 1; j <= i; j++) {
            if (j > 1) printf(" ");
            printf("%d", j);
        }
        printf("\n");
    }

    return 0;
}
```

### Solution in Python

```python
import sys

n = int(sys.argv[1])

for i in range(1, n + 1):
    row = [str(j) for j in range(1, i + 1)]  # list of numbers 1 to i as strings
    print(" ".join(row))                       # join with spaces
```

### Solution in Java

```java
public class Main {
    public static void main(String[] args) {
        int n = Integer.parseInt(args[0]);

        for (int i = 1; i <= n; i++) {
            StringBuilder sb = new StringBuilder();
            for (int j = 1; j <= i; j++) {
                if (j > 1) sb.append(" ");
                sb.append(j);
            }
            System.out.println(sb.toString());
        }
    }
}
```

---

## Foundation Problem 21: Greatest Common Divisor (GCD)

**Problem:** Find the GCD (Highest Common Factor) of two numbers A and B using the Euclidean algorithm.

**Example:** Input: 48 18 → Output: 6

The Euclidean algorithm: GCD(a, b) = GCD(b, a mod b) until b becomes 0.

### Solution in C (recursive)

```c
#include <stdio.h>
#include <stdlib.h>

int gcd(int a, int b) {
    if (b == 0) return a;  /* base case: GCD(a, 0) = a */
    return gcd(b, a % b);  /* recursive case */
}

int main(int argc, char *argv[]) {
    int a = atoi(argv[1]);
    int b = atoi(argv[2]);

    printf("%d\n", gcd(a, b));
    return 0;
}
```

### Solution in Python

```python
import sys
import math

a = int(sys.argv[1])
b = int(sys.argv[2])

print(math.gcd(a, b))  # Python has built-in gcd in math module
```

### Solution in Java

```java
public class Main {
    static int gcd(int a, int b) {
        while (b != 0) {    /* iterative version (avoids recursion stack overflow) */
            int temp = b;
            b = a % b;
            a = temp;
        }
        return a;
    }

    public static void main(String[] args) {
        int a = Integer.parseInt(args[0]);
        int b = Integer.parseInt(args[1]);
        System.out.println(gcd(a, b));
    }
}
```

---

## Foundation Problem 22: Power Calculation Without Built-in

**Problem:** Compute A raised to power B (A^B) without using `pow()` or equivalent built-ins. Use a loop.

**Example:** Input: 3 4 → Output: 81

### Solution in C

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    long long base = atol(argv[1]);
    int exp = atoi(argv[2]);
    long long result = 1;
    int i;

    for (i = 0; i < exp; i++) {
        result *= base;   /* multiply result by base, exp times */
    }

    printf("%lld\n", result);
    return 0;
}
```

### Solution in Python

```python
import sys

base = int(sys.argv[1])
exp = int(sys.argv[2])

result = 1
for _ in range(exp):    # _ is a conventional name for an unused loop variable
    result *= base

print(result)
```

---

## Handling Multiple Test Cases

Some TCS problems ask you to process multiple test cases. The input typically comes from standard input in this format:

```
T        <- number of test cases
input1   <- first test case input
input2   <- second test case input
...
```

### Multi-Test-Case Template in Java (Scanner)

```java
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int t = sc.nextInt();   /* number of test cases */

        while (t-- > 0) {       /* process each test case */
            int n = sc.nextInt();
            /* solve for n and print result */
            System.out.println(n * n);  /* example: print square of n */
        }
    }
}
```

### Multi-Test-Case Template in Python

```python
t = int(input())   # number of test cases

for _ in range(t):
    n = int(input())
    print(n * n)   # example: print square of n
```

### Multi-Test-Case Template in C

```c
#include <stdio.h>

int main() {
    int t;
    scanf("%d", &t);

    while (t--) {     /* t-- uses t then decrements it; loop runs t times */
        int n;
        scanf("%d", &n);
        printf("%d\n", n * n);
    }

    return 0;
}
```

---

## Debugging Your Code When It Produces Wrong Output

When your code runs but gives wrong answers, use this systematic debugging approach:

### Step 1: Trace With a Simple Example

Pick the smallest possible input and trace your code manually. If the problem asks for sum of digits of a number, trace with n=15: extract 5 (15%10=5, sum=5, n=1), extract 1 (1%10=1, sum=6, n=0), print 6. Expected output: 6. If your code gives 0, check whether sum was initialized correctly.

### Step 2: Check Boundary Cases

- What if the input is 0?
- What if N is 1?
- What if N is negative?
- What if the string is empty?

TCS test cases often include these boundary inputs specifically to test whether your code handles edge cases.

### Step 3: Check Variable Types

If your result is consistently 0, you may have an integer division issue. `int / int` in C and Java gives integer result: `5 / 2 = 2`, not `2.5`. To get decimal division, one operand must be a `double` or `float`: `(double)5 / 2 = 2.5`.

If your result is a very large negative number, you likely have integer overflow. Switch `int` to `long long` in C or `long` in Java.

### Step 4: Check Print Format

Is your print statement using the right format specifier? `%d` for int, `%f` for float, `%lld` for long long, `%s` for string. Using `%d` to print a `long long` in C produces garbage output.

### Step 5: Check the Termination Condition

Off-by-one errors in loops are extremely common. A loop that runs n-1 times instead of n times gives a result that is one step short. Check whether your loop condition uses `<` or `<=`, and verify with a small example whether the last iteration is executed.

---

## Understanding the TCS iON Coding Interface

### What You See During the Test

The TCS iON coding editor shows:
- A problem description panel on the left
- A code editor in the centre
- A language selector (usually a dropdown)
- Compile button and Run button
- A test case panel showing sample input/output

### The Compile-Run Process

1. Write your code in the editor
2. Click "Compile" - this checks for syntax errors and reports them
3. If compilation succeeds, click "Run" with the sample input
4. Compare your output with the expected output
5. If correct, submit

**Critical:** Compilation success does NOT mean your output is correct. A program can compile and run but produce the wrong output. Always verify by comparing your output with the expected output in the problem.

### Common Compilation Errors and Their Fixes

**"undefined reference to sqrt":** Add `-lm` flag when compiling C with math functions. In TCS iON, this is handled automatically - but if you are practising locally, compile with `gcc program.c -o program -lm`.

**"Main class not found":** In Java, your class must be named exactly `Main` (capital M) and the file must be saved as `Main.java`. The TCS iON editor handles the file naming - but ensure your class declaration says `public class Main`.

**"SyntaxError: invalid syntax" (Python):** Check for: missing colons after `if`/`for`/`def`, inconsistent indentation (mixing tabs and spaces), unclosed brackets or quotes.

**"ArrayIndexOutOfBoundsException" (Java):** Accessing `args[1]` when only `args[0]` was provided, or accessing `arr[n]` in a 0-indexed array of size n (valid indices are 0 to n-1).

---

## Preparing Without a Computer: Paper-Based Practice

If you do not have consistent access to a computer for practice, you can still prepare meaningfully through paper-based exercises.

**Trace programs on paper.** Take a printed program from this guide and trace its execution step by step, writing down the value of every variable at each step. This builds the mental model of code execution that you need during the test.

**Write programs on paper first.** Before typing any code, write the full solution on paper including every variable declaration, every loop, every print statement. This forces deliberate thinking about the structure before worrying about syntax.

**Memorise the templates.** The input-reading templates, the loop structures, and the print formats for each language are the same in almost every Foundation Coding problem. Memorising these templates means the coding section becomes filling in the problem-specific logic rather than reconstructing the entire program structure from scratch.

---

## Language-Specific Tips for Foundation Coding

### C Tips

**Use `int main(int argc, char *argv[])` by default.** Even if the problem uses standard input, this signature also works because you can ignore argc/argv and use scanf/printf.

**Declare variables at the top of each block** (before any executable statements) for compatibility with older C standards that TCS iON may enforce.

**Use `long long` instead of `int` whenever multiplication or large sums are involved.** The format specifier for long long in printf is `%lld`.

**String functions require `#include <string.h>`.** Functions: `strlen(s)`, `strcpy(dest, src)`, `strcmp(s1, s2)`, `strcat(dest, src)`.

### C++ Tips

**`#include <bits/stdc++.h>` includes everything.** While not standard, this header is commonly available in TCS iON and includes all necessary headers.

**Use `cin >> n` and `cout << n` for cleaner I/O than C's scanf/printf.**

**STL is available.** `vector`, `map`, `set`, `sort()`, `max()`, `min()` - use them freely. They make Foundation problems much cleaner to solve.

### Java Tips

**Class must be named `Main`.** This is not optional - TCS iON compiles your file expecting a class named Main.

**`Integer.parseInt()` is your most-used method** for converting command line args to integers.

**Use `System.out.println()` for most output.** For formatted decimal output, use `System.out.printf("%.2f%n", value)`.

**For string comparison, always use `.equals()`,** never `==`. The `==` operator checks reference equality (are they the same object?), not content equality.

**`StringBuilder` is faster than string concatenation in loops.** For building a string character by character or number by number, use `StringBuilder sb = new StringBuilder(); sb.append(x); String result = sb.toString();`.

### Python Tips

**`sys.argv[1]` gives the first argument as a string.** Always convert to `int()` or `float()` before arithmetic.

**Python's `//` is integer division; `/` is float division.** `7 // 2 = 3`; `7 / 2 = 3.5`.

**List comprehensions are powerful for Foundation problems.** `[int(x) for x in sys.argv[1:]]` converts all command line args to integers in one line.

**`f-strings` for formatted output:** `print(f"{value:.2f}")` prints value with 2 decimal places. Cleaner than `print("%.2f" % value)`.

**Python has no `do-while` loop.** Simulate with `while True: ... if condition: break`.

---

## A Sample TCS Narrative Problem: Complete Walkthrough

**Problem text:** "Meera runs a small grocery store. A customer buys N different items. The price of the i-th item is given as command line arguments. The customer is eligible for a 10% discount if the total bill exceeds Rs. 500. Calculate the amount the customer has to pay. Print the result rounded to 2 decimal places."

**Step 1: Extract the core task.** Read N prices, sum them, if sum > 500 apply 10% discount (multiply by 0.9), print result with 2 decimal places.

**Step 2: Identify input format.** The prices are command line arguments (the problem says "as command line arguments"). The total number of arguments is argc-1 in C or args.length in Java.

**Step 3: Code the solution.**

### Python Solution

```python
import sys

prices = [float(x) for x in sys.argv[1:]]  # all args as floats
total = sum(prices)

if total > 500:
    total = total * 0.9    # apply 10% discount

print(f"{total:.2f}")
```

### Java Solution

```java
public class Main {
    public static void main(String[] args) {
        double total = 0;

        for (String arg : args) {   /* iterate through all arguments */
            total += Double.parseDouble(arg);
        }

        if (total > 500) {
            total *= 0.9;   /* multiply by 0.9 = reduce by 10% */
        }

        System.out.printf("%.2f%n", total);
    }
}
```

### C Solution

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = argc - 1;    /* number of prices */
    double total = 0;
    int i;

    for (i = 1; i <= n; i++) {
        total += atof(argv[i]);    /* atof for double, not atoi */
    }

    if (total > 500) {
        total *= 0.9;
    }

    printf("%.2f\n", total);
    return 0;
}
```

**Key insight from this problem:** TCS narrative problems always reduce to simple computation. Strip the story, identify the variables, write the arithmetic. The difficulty is in stripping the story - not in the programming.

---

## Frequently Asked Questions: TCS Ninja Coding

**Do I have to use command line arguments or can I always use stdin?**
Read the problem statement carefully. If it shows example execution with values after the program name (e.g., `./program 15 7`), use command line arguments. If it shows values being typed below the program execution, use standard input. When in doubt and both formats seem possible, check the sample input format described in the problem.

**What if I cannot solve the problem completely - should I still submit?**
Yes. TCS iON scores by test cases. A partial solution that handles some cases correctly earns partial marks. A program that reads the input correctly and prints a placeholder answer (like 0) may pass some test cases. Something is always better than nothing.

**Can I use recursive functions in TCS Ninja coding?**
Yes. Recursion is fully supported in all four languages. However, for very large inputs, deep recursion can cause stack overflow. For Foundation-level problems, recursion depth is typically small enough that this is not an issue.

**Is there a limit on how many times I can submit?**
There is no stated submission penalty in TCS Ninja coding. You can submit multiple times and your score reflects your best submission.

**What language should I practice in if I know only one?**
Stick with the language you know. Foundation-level problems can be solved in any of the four languages. The biggest risk is switching to a language you are not comfortable in for the exam.

**How do I handle floating point precision issues?**
For TCS Ninja Foundation problems, using `double` (not `float`) in C/Java and the standard Python `float` is sufficient. When the problem asks for a result rounded to 2 decimal places, use `printf("%.2f")` in C, `System.out.printf("%.2f")` in Java, or `f"{x:.2f}"` in Python.

**What if the problem requires reading a string with spaces?**
Command line arguments cannot contain spaces (the space is the argument separator). If a string with spaces is needed, it must come from standard input: `scanf("%[^\n]", str)` in C reads until newline; `sc.nextLine()` in Java reads the full line; `input()` in Python reads the full line.

**I am from a non-CS branch (Mechanical, Civil, ECE). Is the Foundation Coding section fair for me?**
The Foundation Coding section tests basic programming fundamentals - loops, conditionals, simple arithmetic, basic string operations. These are concepts typically covered in the first-year programming courses that are part of all engineering curricula in India. The difficulty is calibrated for this level. If your first-year programming course covered at least the topics in this guide, you have the background needed. The preparation plan in this guide is specifically designed for candidates who need to refresh or build these foundations.

---

## What Happens If You Get Zero in Coding

This is the scenario that most candidates fear and that drives the recommendation to prepare specifically for the coding section.

TCS evaluates Foundation Coding performance as a meaningful filter in the selection process. A zero in coding - even with strong aptitude and reasoning scores - can result in being placed in a lower tier or not proceeding in the process. This is the "coding section is mandatory" reality that distinguishes TCS from companies where coding is optional for non-CS branches.

The good news: getting a non-zero score in Foundation Coding is achievable with relatively modest preparation. If your program reads the input correctly and produces any reasonable output for the simplest test case, you have already moved off zero. If it produces correct output for half the test cases, you have a meaningful coding score.

The preparation in this guide - specifically the input-handling setup and the fifteen core problem types - covers the range of what Foundation Coding tests. Two weeks of daily practice with the problems here is sufficient to walk in with the confidence that you can read the input, apply the logic, and print the output. That is all the Foundation Coding section requires.

---

## Standard Input Deep Dive: Reading Multiple Values

When TCS Foundation problems use standard input rather than command line arguments, the input format varies. Here are the most common patterns with solutions across all four languages.

### Pattern A: Single integer on one line

```
Input:
5
```

**C:** `scanf("%d", &n);`
**C++:** `cin >> n;`
**Java:** `int n = sc.nextInt();`
**Python:** `n = int(input())`

### Pattern B: Multiple integers on one line, separated by spaces

```
Input:
10 20 30
```

**C:**
```c
int a, b, c;
scanf("%d %d %d", &a, &b, &c);
```

**Java:**
```java
Scanner sc = new Scanner(System.in);
int a = sc.nextInt(), b = sc.nextInt(), c = sc.nextInt();
```

**Python:**
```python
a, b, c = map(int, input().split())
# input().split() splits "10 20 30" into ["10", "20", "30"]
# map(int, ...) converts each to int
# a, b, c = ... unpacks into three variables
```

### Pattern C: First line is count N, second line is N numbers

```
Input:
5
3 1 4 1 5
```

**Java:**
```java
Scanner sc = new Scanner(System.in);
int n = sc.nextInt();
int[] arr = new int[n];
for (int i = 0; i < n; i++) {
    arr[i] = sc.nextInt();
}
```

**Python:**
```python
n = int(input())
arr = list(map(int, input().split()))
# input().split() splits the second line
# map(int, ...) converts each to int
# list(...) makes it a list
```

**C:**
```c
#include <stdio.h>

int main() {
    int n;
    scanf("%d", &n);

    int arr[1000];
    for (int i = 0; i < n; i++) {
        scanf("%d", &arr[i]);
    }

    /* process arr here */
    return 0;
}
```

### Pattern D: Read until end of input (unknown number of values)

**Python:**
```python
import sys

numbers = []
for line in sys.stdin:
    numbers.extend(map(int, line.split()))
# processes all input lines
```

**Java:**
```java
Scanner sc = new Scanner(System.in);
while (sc.hasNextInt()) {
    int x = sc.nextInt();
    // process x
}
```

---

## Foundation Problem 23: Sum of All Prime Numbers Up to N

**Problem:** Given N, find the sum of all prime numbers from 2 to N.

**Example:** Input: 10 → Output: 17 (2 + 3 + 5 + 7 = 17)

### Solution in Python

```python
import sys
import math

def is_prime(n):
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0: return False
    return True

n = int(sys.argv[1])
total = sum(i for i in range(2, n + 1) if is_prime(i))
print(total)
```

### Solution in Java

```java
public class Main {
    static boolean isPrime(int n) {
        if (n < 2) return false;
        for (int i = 2; (long) i * i <= n; i++) {
            if (n % i == 0) return false;
        }
        return true;
    }

    public static void main(String[] args) {
        int n = Integer.parseInt(args[0]);
        long sum = 0;
        for (int i = 2; i <= n; i++) {
            if (isPrime(i)) sum += i;
        }
        System.out.println(sum);
    }
}
```

---

## Foundation Problem 24: Check if All Elements in Array are Unique

**Problem:** Given N numbers, print "All Unique" if no two numbers are the same, otherwise print "Duplicates Found".

**Example:** Input: 3 1 4 1 5 → Output: Duplicates Found

### Solution in Python

```python
import sys

numbers = [int(x) for x in sys.argv[1:]]

if len(numbers) == len(set(numbers)):  # set removes duplicates; if lengths match, all unique
    print("All Unique")
else:
    print("Duplicates Found")
```

### Solution in Java

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Set<Integer> seen = new HashSet<>();  /* HashSet stores unique values */

        for (String arg : args) {
            int x = Integer.parseInt(arg);
            if (!seen.add(x)) {  /* add() returns false if element already exists */
                System.out.println("Duplicates Found");
                return;
            }
        }

        System.out.println("All Unique");
    }
}
```

---

## Foundation Problem 25: Frequency Count of Each Element

**Problem:** Given N numbers, print each distinct number and how many times it appears, in the order numbers first appear.

**Example:** Input: 3 1 3 2 1 3 → Output:
```
3: 3
1: 2
2: 1
```

### Solution in Python

```python
import sys
from collections import OrderedDict

numbers = [int(x) for x in sys.argv[1:]]
freq = OrderedDict()         # preserves insertion order

for n in numbers:
    freq[n] = freq.get(n, 0) + 1  # increment count (default 0)

for num, count in freq.items():
    print(f"{num}: {count}")
```

### Solution in Java

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Map<Integer, Integer> freq = new LinkedHashMap<>();  /* preserves insertion order */

        for (String arg : args) {
            int x = Integer.parseInt(arg);
            freq.put(x, freq.getOrDefault(x, 0) + 1);
        }

        for (Map.Entry<Integer, Integer> entry : freq.entrySet()) {
            System.out.println(entry.getKey() + ": " + entry.getValue());
        }
    }
}
```

---

## The Standard Template You Should Memorise for Each Language

Before your test, memorise one "minimum working template" for each language you might use. This template should be something you can type from memory in under 60 seconds.

### C Minimum Template

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

int main(int argc, char *argv[]) {
    /* Read input */
    int n = atoi(argv[1]);

    /* Process */

    /* Output */
    printf("%d\n", n);

    return 0;
}
```

### Java Minimum Template

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        // Read input
        int n = Integer.parseInt(args[0]);

        // Process

        // Output
        System.out.println(n);
    }
}
```

### Python Minimum Template

```python
import sys

# Read input
n = int(sys.argv[1])

# Process

# Print output
print(n)
```

### C++ Minimum Template

```cpp
#include <bits/stdc++.h>
using namespace std;

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);

    // Process

    cout << n << endl;
    return 0;
}
```

Once you have memorised your template, the only thing you need to change for each problem is the input-reading section (more variables, different types) and the processing logic. The output format rarely changes. This mechanical stability under exam pressure is worth more than any single algorithm.

---

## Building Exam Confidence Through Deliberate Practice

The difference between walking into the TCS Ninja coding section confidently and walking in anxiously is almost entirely a function of how many times you have successfully written a program from scratch, compiled it, and seen the correct output.

**The 10-program rule:** Write and successfully run at least 10 complete programs before your exam. Not "study" 10 programs - actually type them, compile them, and verify the output. This mechanical repetition builds the automatic memory for syntax, I/O patterns, and loop structures that reading alone cannot build.

**Practice on the same type of machine you will test on:** If your exam is remote (online) and you practice only on a powerful desktop, the constraint of a potentially slower or unfamiliar TCS iON interface may catch you off guard. Practice on an online compiler (onlinegdb.com, replit.com, or similar) to simulate the browser-based editor environment.

**Time yourself:** Set a 30-minute timer and write a complete solution to one Foundation problem from this guide. If you finish in under 20 minutes, you have comfortable margin. If you are still writing at 28 minutes, you need more practice on the mechanical aspects of coding (reading input, writing loops, printing output) before the actual test.

**Read your code before submitting:** Before clicking submit in any practice session, read your code top to bottom one time. Does every variable have a declared type (in C/Java)? Is every `if` statement followed by `else` where needed? Does the output section print exactly what the problem requires? This 60-second habit catches most bugs that automated testing would catch.

The TCS Ninja Foundation Coding section rewards candidates who have done the mechanical work of actually writing code. No amount of conceptual understanding substitutes for having typed, debugged, and run programs until the process feels natural. That is the preparation that makes the difference.

---

Every candidate who has ever cracked TCS Ninja coding started exactly where you are - staring at a problem, unsure how to begin. The difference between those who got the output and those who did not was not intelligence or talent. It was whether they had practised the specific mechanics: reading input, writing the logic, printing the output. This guide has given you the problems, the solutions, the explanations, and the plan. The remaining variable is the practice hours you invest between now and your test. Invest them, and the coding section will be your advantage rather than your fear.
