---
layout: post
title: "TCS Java Coding: Complete Solutions Guide"
page_title: "TCS Coding Questions Using Java - Comprehensive Problem Set with Detailed Solutions and Optimization Tips"
date: 2023-10-10
categories: ["Industry"]
tags: ["TCS Java coding", "TCS Java programs", "TCS coding solutions Java", "Java for TCS", "TCS NQT Java"]
excerpt: "Master TCS coding rounds with Java. Category-wise problems with complete solutions, complexity analysis, and compiler-specific tips."
image: "/assets/images/blog/blog-03.webp"
reading_time: 60
author: "Insight Crunch Team"
---

Java is the most widely used language in TCS coding rounds - not because TCS mandates it, but because the majority of engineering graduates in India learn Java as their primary programming language, and Java's standard library makes common string, array, and data structure operations clean to express. If you have a solid Java foundation and you understand how TCS iON's coding environment works, you can solve the kinds of problems that appear in TCS NQT and ITP Advanced Coding sections efficiently and confidently. This guide covers everything: the environment, the input-output patterns, and a comprehensive category-wise problem set with complete, annotated Java solutions that you can study, run, and adapt.

![TCS Guide](/assets/images/blog/blog-03.webp)

## Why Java Is a Strong Choice for TCS Coding Rounds

Before diving into problems, it is worth understanding why Java specifically rewards the effort of learning it for TCS exams.

### Robust Standard Library

Java's `java.util` and `java.lang` packages provide ready-to-use implementations of the data structures and algorithms most commonly needed in TCS coding problems:

- `ArrayList` and `LinkedList` for dynamic arrays and linked list behaviour
- `HashMap` and `HashSet` for O(1) average lookup and uniqueness checking
- `Stack`, `Queue` (via `LinkedList` or `ArrayDeque`), and `PriorityQueue` for LIFO, FIFO, and priority-based operations
- `Collections.sort()` for efficient sorting of lists with custom comparators
- `Arrays.sort()` for primitive and object arrays
- `StringBuilder` for efficient string construction in loops
- `Math` class for `abs()`, `pow()`, `sqrt()`, `min()`, `max()`, `log()` without external imports

This richness means you spend less time implementing utility functions from scratch and more time solving the actual problem logic.

### Clear, Readable Syntax

Java's explicit type declarations and structured syntax make it easy to write code that is readable to you under pressure. When you have 30-45 minutes to solve a problem and submit, being able to read back your own code quickly to spot errors is an advantage. Languages with more compact syntax (Python, Kotlin) can be faster to write, but Java's verbosity makes logical flow more visible.

### String Handling

Java's `String` class provides powerful built-in methods: `charAt()`, `substring()`, `indexOf()`, `contains()`, `replace()`, `split()`, `toCharArray()`, `toLowerCase()`, `toUpperCase()`, `trim()`. String manipulation problems - which form a large category of TCS coding questions - are well-handled by these methods.

---

## The TCS iON Java Environment

Understanding the compilation and execution environment before the exam prevents avoidable failures.

### JDK Version and Class Naming

TCS iON uses a standard JDK environment. The pre-defined class structure in the editor typically looks like:

```java
import java.util.*;
import java.io.*;

public class Main {
    public static void main(String[] args) {
        // Your solution here
    }
}
```

**Critical rule:** The class must be named exactly `Main` (capital M). Do not rename it to your solution name or your own name. A class name mismatch causes a compilation error and a zero score for that problem.

All standard `java.util.*` and `java.io.*` imports are available. You do not need to import `java.lang.*` - it is imported by default. For problems requiring `Arrays` or `Collections`, include `import java.util.*;` which covers both.

### Input Handling: Scanner vs BufferedReader vs Command Line

**Scanner (recommended for most TCS problems):**

```java
Scanner sc = new Scanner(System.in);
int n = sc.nextInt();           // Read single integer
String s = sc.next();           // Read single word (no spaces)
String line = sc.nextLine();    // Read full line including spaces
double d = sc.nextDouble();     // Read decimal
long l = sc.nextLong();         // Read large integer
```

Scanner is slower than BufferedReader for very large inputs but perfectly adequate for all standard TCS coding problems. The convenience methods (`nextInt`, `nextDouble`, etc.) eliminate parsing code and reduce error risk.

**Common Scanner trap:** After reading an integer with `nextInt()`, if you then call `nextLine()`, it reads the leftover newline character as an empty string. Fix: add an extra `sc.nextLine()` call to consume the newline before reading the actual next line.

```java
int n = sc.nextInt();
sc.nextLine(); // consume the newline
String s = sc.nextLine(); // now reads the actual next line
```

**BufferedReader (for speed-critical problems):**

```java
BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
int n = Integer.parseInt(br.readLine().trim());
String[] parts = br.readLine().split(" ");
int[] arr = new int[parts.length];
for (int i = 0; i < parts.length; i++) arr[i] = Integer.parseInt(parts[i]);
```

BufferedReader is faster but more verbose. Use it when the problem has very large input (100,000+ elements), though TCS problems rarely reach this scale.

**Command Line args (for simple single-value inputs):**

```java
public static void main(String[] args) {
    int n = Integer.parseInt(args[0]);
}
```

Some TCS iON problem templates pass input through `args`. Check the problem template before assuming Scanner input is the right approach.

### Output Requirements

TCS problems typically specify exact output format. Common patterns:

```java
System.out.println(answer);       // Print with newline
System.out.print(answer + " ");   // Print without newline (for space-separated output)
System.out.printf("%.2f%n", d);   // Formatted decimal (2 places)
```

Read the expected output format carefully. "Print each element on a new line" and "Print all elements space-separated on one line" require different output code. Wrong output format fails all test cases even when your logic is correct.

---

## Category 1: Basic I/O and Data Type Problems

These problems verify that you can read input correctly, perform basic operations, and produce correctly formatted output.

### Problem 1.1: Reverse a Number

**Problem statement:** Given a positive integer N, print its digits in reverse order as an integer (leading zeros in the reversed number are dropped).

**Example:** Input: 12300 → Output: 321

**Approach:** Repeatedly extract the last digit using modulo 10 and build the reversed number, or convert to string and reverse.

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        long n = sc.nextLong(); // use long to handle large numbers
        long reversed = 0;

        while (n > 0) {
            int digit = (int)(n % 10);  // extract last digit
            reversed = reversed * 10 + digit; // append to result
            n /= 10; // remove last digit
        }

        System.out.println(reversed);
    }
}
```

**Time:** O(d) where d = number of digits. **Space:** O(1). Leading zeros are automatically dropped because `reversed` is an integer, not a string.

**Edge case:** For input 0, the while loop does not execute and `reversed` remains 0. Output is 0. Correct.

### Problem 1.2: Sum of Digits Until Single Digit

**Problem statement:** Given an integer N, repeatedly sum its digits until the result is a single digit. Print the final single digit.

**Example:** Input: 9875 → 9+8+7+5 = 29 → 2+9 = 11 → 1+1 = 2. Output: 2

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();

        while (n >= 10) {
            int sum = 0;
            while (n > 0) {
                sum += n % 10;
                n /= 10;
            }
            n = sum;
        }

        System.out.println(n);
    }
}
```

**Time:** O(d x iterations). **Space:** O(1). **Optimisation note:** The digital root of a number has a direct formula: if n % 9 == 0, digital root = 9 (for n > 0); else digital root = n % 9. The loop approach is fine for TCS, but knowing the formula is useful if the interviewer asks for optimisation.

---

## Category 2: String Manipulation

String problems are the most frequently appearing category in TCS coding rounds. The problems below cover the full range of string manipulation types tested.

### Problem 2.1: Check if a String is a Palindrome

**Problem statement:** Given a string, determine if it reads the same forward and backward. Ignore case. Print "YES" if it is a palindrome, "NO" otherwise.

**Example:** Input: "RaceCar" → Output: YES

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine().toLowerCase().trim();
        String reversed = new StringBuilder(s).reverse().toString();

        if (s.equals(reversed)) {
            System.out.println("YES");
        } else {
            System.out.println("NO");
        }
    }
}
```

**Time:** O(n). **Space:** O(n) for the reversed string. **Alternative two-pointer approach:**

```java
boolean isPalin = true;
int left = 0, right = s.length() - 1;
while (left < right) {
    if (s.charAt(left) != s.charAt(right)) {
        isPalin = false;
        break;
    }
    left++;
    right--;
}
```

The two-pointer approach uses O(1) space and exits early on the first mismatch - more efficient for very long strings.

### Problem 2.2: Check if Two Strings Are Anagrams

**Problem statement:** Given two strings, determine if one is an anagram of the other (contains the same characters with the same frequencies, regardless of order). Print "ANAGRAM" or "NOT ANAGRAM".

**Example:** Input: "listen", "silent" → Output: ANAGRAM

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s1 = sc.nextLine().toLowerCase().trim();
        String s2 = sc.nextLine().toLowerCase().trim();

        if (s1.length() != s2.length()) {
            System.out.println("NOT ANAGRAM");
            return;
        }

        int[] freq = new int[26]; // frequency array for a-z

        for (char c : s1.toCharArray()) freq[c - 'a']++;
        for (char c : s2.toCharArray()) freq[c - 'a']--;

        for (int count : freq) {
            if (count != 0) {
                System.out.println("NOT ANAGRAM");
                return;
            }
        }

        System.out.println("ANAGRAM");
    }
}
```

**Time:** O(n). **Space:** O(1) - the frequency array is always size 26 regardless of input length. This is faster than sorting both strings (O(n log n)) and more direct than using a HashMap.

### Problem 2.3: Count Vowels, Consonants, Digits, and Spaces

**Problem statement:** Given a string, print the count of vowels, consonants, digits, and spaces on separate lines.

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine().toLowerCase();

        int vowels = 0, consonants = 0, digits = 0, spaces = 0;
        String vowelSet = "aeiou";

        for (char c : s.toCharArray()) {
            if (c == ' ') {
                spaces++;
            } else if (Character.isDigit(c)) {
                digits++;
            } else if (Character.isLetter(c)) {
                if (vowelSet.indexOf(c) != -1) vowels++;
                else consonants++;
            }
        }

        System.out.println("Vowels: " + vowels);
        System.out.println("Consonants: " + consonants);
        System.out.println("Digits: " + digits);
        System.out.println("Spaces: " + spaces);
    }
}
```

**Time:** O(n). **Space:** O(1). Note: `Character.isDigit()` and `Character.isLetter()` handle the classification cleanly without manual ASCII range checks.

### Problem 2.4: Find the Frequency of Each Character

**Problem statement:** Given a string, print each unique character and its frequency in the order the character first appears. Format: "char:frequency" on each line.

**Example:** Input: "programming" → Output: p:1, r:2, o:1, g:2, a:1, m:2, i:1, n:1

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine();

        Map<Character, Integer> freq = new LinkedHashMap<>(); // preserves insertion order

        for (char c : s.toCharArray()) {
            freq.put(c, freq.getOrDefault(c, 0) + 1);
        }

        for (Map.Entry<Character, Integer> entry : freq.entrySet()) {
            System.out.println(entry.getKey() + ":" + entry.getValue());
        }
    }
}
```

**Time:** O(n). **Space:** O(k) where k is the number of unique characters. Key choice: `LinkedHashMap` over `HashMap` because it preserves insertion order, which is "the order characters first appear" as required by the problem.

### Problem 2.5: Reverse Words in a Sentence

**Problem statement:** Given a sentence, reverse the order of words while preserving each word intact. Multiple spaces between words should be reduced to single space in the output.

**Example:** Input: "Hello World how are you" → Output: "you are how World Hello"

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine().trim();
        String[] words = s.split("\\s+"); // split on one or more spaces

        StringBuilder sb = new StringBuilder();
        for (int i = words.length - 1; i >= 0; i--) {
            sb.append(words[i]);
            if (i > 0) sb.append(" ");
        }

        System.out.println(sb.toString());
    }
}
```

**Time:** O(n). **Space:** O(n). The regex `"\\s+"` handles multiple consecutive spaces correctly, unlike `" "` which would produce empty strings in the split result.

### Problem 2.6: Longest Substring Without Repeating Characters

**Problem statement:** Given a string, find the length of the longest substring that contains no repeating characters.

**Example:** Input: "abcabcbb" → Output: 3 (the substring "abc")

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine();

        Set<Character> window = new HashSet<>();
        int left = 0, maxLen = 0;

        for (int right = 0; right < s.length(); right++) {
            char c = s.charAt(right);

            // shrink window from left until duplicate is removed
            while (window.contains(c)) {
                window.remove(s.charAt(left));
                left++;
            }

            window.add(c);
            maxLen = Math.max(maxLen, right - left + 1);
        }

        System.out.println(maxLen);
    }
}
```

**Time:** O(n) - each character enters and leaves the window at most once. **Space:** O(min(n, alphabet_size)). This sliding window approach is the optimal solution and a common TCS Advanced problem pattern.

---

## Category 3: Array Operations

### Problem 3.1: Find the Second Largest Element

**Problem statement:** Given an array of N integers, find the second largest unique element. If no second largest exists, print -1.

**Example:** Input: N=6, array=[3, 1, 4, 1, 5, 9] → Output: 5

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();

        int max = Integer.MIN_VALUE;
        int secondMax = Integer.MIN_VALUE;

        for (int num : arr) {
            if (num > max) {
                secondMax = max;
                max = num;
            } else if (num > secondMax && num != max) {
                secondMax = num;
            }
        }

        if (secondMax == Integer.MIN_VALUE) System.out.println(-1);
        else System.out.println(secondMax);
    }
}
```

**Time:** O(n). **Space:** O(1). The condition `num != max` ensures uniqueness - if all elements are equal, `secondMax` stays at `Integer.MIN_VALUE` and we output -1.

### Problem 3.2: Rotate an Array to the Right by K Positions

**Problem statement:** Given an array of N integers and a value K, rotate the array to the right by K positions. Print the resulting array space-separated.

**Example:** Input: N=5, K=2, array=[1,2,3,4,5] → Output: 4 5 1 2 3

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int k = sc.nextInt() % n; // handle k > n
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();

        // Three-reversal approach: O(n) time, O(1) space
        reverse(arr, 0, n - 1);       // reverse entire array
        reverse(arr, 0, k - 1);       // reverse first k elements
        reverse(arr, k, n - 1);       // reverse remaining n-k elements

        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) {
            sb.append(arr[i]);
            if (i < n - 1) sb.append(" ");
        }
        System.out.println(sb.toString());
    }

    static void reverse(int[] arr, int start, int end) {
        while (start < end) {
            int temp = arr[start];
            arr[start] = arr[end];
            arr[end] = temp;
            start++;
            end--;
        }
    }
}
```

**Time:** O(n). **Space:** O(1). The three-reversal method is the most elegant and efficient in-place rotation approach.

### Problem 3.3: Find All Pairs With a Given Sum

**Problem statement:** Given an array of N integers and a target sum K, print all pairs (a, b) where a + b = K and a <= b. Print each pair on a new line as "a b". If no pairs exist, print "No pairs found".

**Example:** Input: N=6, K=9, array=[1,8,3,6,4,5] → Output: 1 8 / 3 6 / 4 5

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int k = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();

        Set<Integer> seen = new HashSet<>();
        Set<String> printed = new HashSet<>(); // avoid duplicate pairs
        boolean found = false;

        for (int num : arr) {
            int complement = k - num;
            if (seen.contains(complement)) {
                int a = Math.min(num, complement);
                int b = Math.max(num, complement);
                String pair = a + " " + b;
                if (!printed.contains(pair)) {
                    System.out.println(pair);
                    printed.add(pair);
                    found = true;
                }
            }
            seen.add(num);
        }

        if (!found) System.out.println("No pairs found");
    }
}
```

**Time:** O(n). **Space:** O(n). The `printed` set prevents duplicate pair output when the same pair appears multiple times due to repeated elements.

### Problem 3.4: Subarray With Maximum Sum (Kadane's Algorithm)

**Problem statement:** Given an array of N integers (which may include negative numbers), find the maximum sum of any contiguous subarray. Print the maximum sum.

**Example:** Input: N=8, array=[-2,1,-3,4,-1,2,1,-5,4] → Output: 6 (subarray [4,-1,2,1])

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();

        int maxSum = arr[0];
        int currentSum = arr[0];

        for (int i = 1; i < n; i++) {
            // either extend the current subarray or start fresh from arr[i]
            currentSum = Math.max(arr[i], currentSum + arr[i]);
            maxSum = Math.max(maxSum, currentSum);
        }

        System.out.println(maxSum);
    }
}
```

**Time:** O(n). **Space:** O(1). Kadane's Algorithm is one of the most important algorithms to know for TCS Advanced Coding. The core insight: at each position, the optimal subarray ending here either includes the previous subarray (if it adds value) or starts fresh.

---

## Category 4: Number Theory

### Problem 4.1: Check Primality Using Optimised Trial Division

**Problem statement:** Given N integers, for each determine if it is prime. Print "Prime" or "Not Prime" for each.

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();

        while (n-- > 0) {
            int num = sc.nextInt();
            System.out.println(isPrime(num) ? "Prime" : "Not Prime");
        }
    }

    static boolean isPrime(int n) {
        if (n < 2) return false;
        if (n == 2) return true;
        if (n % 2 == 0) return false;
        // check odd divisors up to sqrt(n)
        for (int i = 3; (long)i * i <= n; i += 2) {
            if (n % i == 0) return false;
        }
        return true;
    }
}
```

**Time:** O(sqrt(n)) per query. **Optimisation note:** The `(long)i * i <= n` cast prevents integer overflow when `i` is large. Checking only odd numbers after 2 halves the iterations.

### Problem 4.2: GCD and LCM

**Problem statement:** Given two integers A and B, print their GCD and LCM on separate lines.

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        long a = sc.nextLong();
        long b = sc.nextLong();

        long gcd = gcd(a, b);
        long lcm = a / gcd * b; // divide before multiply to avoid overflow

        System.out.println("GCD: " + gcd);
        System.out.println("LCM: " + lcm);
    }

    static long gcd(long a, long b) {
        return b == 0 ? a : gcd(b, a % b); // Euclidean algorithm
    }
}
```

**Time:** O(log(min(a,b))) for GCD. **Key formula:** LCM(a,b) = a * b / GCD(a,b). Write it as `a / gcd * b` rather than `a * b / gcd` to avoid overflow when a and b are large.

### Problem 4.3: Armstrong Number Check

**Problem statement:** Given a number N, check if it is an Armstrong number. An Armstrong number of k digits satisfies: sum of each digit raised to k equals the number. Print "Armstrong" or "Not Armstrong".

**Example:** 153 = 1^3 + 5^3 + 3^3 = 153. Output: Armstrong

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();

        int original = n;
        int digits = String.valueOf(n).length(); // count digits
        int sum = 0;
        int temp = n;

        while (temp > 0) {
            int digit = temp % 10;
            sum += (int) Math.pow(digit, digits);
            temp /= 10;
        }

        System.out.println(sum == original ? "Armstrong" : "Not Armstrong");
    }
}
```

**Time:** O(d) where d = number of digits. **Note:** `Math.pow()` returns a `double`, so cast to `int` is necessary. For larger numbers, precision issues may arise - if precision is critical, use a manual power function with integer arithmetic.

### Problem 4.4: Fibonacci Series Using Memoisation

**Problem statement:** Given N, print the first N Fibonacci numbers space-separated. Handle N up to 50 (requiring `long` to avoid overflow).

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();

        long[] fib = new long[Math.max(n, 2)];
        fib[0] = 0;
        fib[1] = 1;

        for (int i = 2; i < n; i++) {
            fib[i] = fib[i-1] + fib[i-2];
        }

        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) {
            sb.append(fib[i]);
            if (i < n - 1) sb.append(" ");
        }
        System.out.println(sb.toString());
    }
}
```

**Time:** O(n). **Space:** O(n). Use `long` - Fibonacci(49) is approximately 12.6 billion, which overflows `int`. If only the nth term is needed (not the series), reduce space to O(1) using two variables.

### Problem 4.5: Convert Decimal to Binary, Octal, and Hexadecimal

**Problem statement:** Given a decimal integer N, print its binary, octal, and hexadecimal representations.

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();

        System.out.println("Binary: " + Integer.toBinaryString(n));
        System.out.println("Octal: " + Integer.toOctalString(n));
        System.out.println("Hexadecimal: " + Integer.toHexString(n).toUpperCase());
    }
}
```

Java's `Integer` class provides built-in conversion methods. Use them - they are reliable and less error-prone than manual implementation. `toHexString()` returns lowercase letters by default; `.toUpperCase()` converts if the problem requires uppercase hex.

---

## Category 5: Sorting and Searching

### Problem 5.1: Implement Merge Sort

**Problem statement:** Given an array of N integers, sort it using merge sort and print the sorted array.

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();

        mergeSort(arr, 0, n - 1);

        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) {
            sb.append(arr[i]);
            if (i < n - 1) sb.append(" ");
        }
        System.out.println(sb.toString());
    }

    static void mergeSort(int[] arr, int left, int right) {
        if (left >= right) return;
        int mid = left + (right - left) / 2; // avoids overflow vs (left+right)/2
        mergeSort(arr, left, mid);
        mergeSort(arr, mid + 1, right);
        merge(arr, left, mid, right);
    }

    static void merge(int[] arr, int left, int mid, int right) {
        int n1 = mid - left + 1;
        int n2 = right - mid;
        int[] L = new int[n1];
        int[] R = new int[n2];

        for (int i = 0; i < n1; i++) L[i] = arr[left + i];
        for (int j = 0; j < n2; j++) R[j] = arr[mid + 1 + j];

        int i = 0, j = 0, k = left;
        while (i < n1 && j < n2) {
            if (L[i] <= R[j]) arr[k++] = L[i++];
            else arr[k++] = R[j++];
        }
        while (i < n1) arr[k++] = L[i++];
        while (j < n2) arr[k++] = R[j++];
    }
}
```

**Time:** O(n log n) all cases. **Space:** O(n). Merge sort is stable and guarantees consistent performance. Know this implementation thoroughly - it demonstrates both recursion and merging logic.

### Problem 5.2: Binary Search With Boundary Condition

**Problem statement:** Given a sorted array of N integers and a target T, find the index of T in the array. If T appears multiple times, return the index of the first occurrence. If T is not present, print -1.

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();
        int target = sc.nextInt();

        System.out.println(firstOccurrence(arr, target));
    }

    static int firstOccurrence(int[] arr, int target) {
        int left = 0, right = arr.length - 1, result = -1;

        while (left <= right) {
            int mid = left + (right - left) / 2;
            if (arr[mid] == target) {
                result = mid;       // record this as a candidate
                right = mid - 1;   // continue searching left half
            } else if (arr[mid] < target) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }

        return result;
    }
}
```

**Time:** O(log n). **Space:** O(1). The key extension over standard binary search: when the target is found, record the index but continue searching the left half to find the first occurrence.

### Problem 5.3: Sort an ArrayList of Custom Objects

**Problem statement:** Given N students each with a name and score, sort them by score in descending order. For equal scores, sort alphabetically by name. Print each student as "name:score".

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        sc.nextLine(); // consume newline after int

        List<String[]> students = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            String line = sc.nextLine();
            String[] parts = line.split(":");
            students.add(new String[]{parts[0].trim(), parts[1].trim()});
        }

        // Sort: descending score, then ascending name for ties
        students.sort((a, b) -> {
            int scoreA = Integer.parseInt(a[1]);
            int scoreB = Integer.parseInt(b[1]);
            if (scoreB != scoreA) return scoreB - scoreA; // descending score
            return a[0].compareTo(b[0]);                  // ascending name
        });

        for (String[] s : students) {
            System.out.println(s[0] + ":" + s[1]);
        }
    }
}
```

**Time:** O(n log n). **Space:** O(n). Lambda comparators in Java 8+ make multi-key sorting concise. The pattern `(a, b) -> comparison` is the standard way to customise `Collections.sort()` or `List.sort()`.

---

## Category 6: Data Structures

### Problem 6.1: Valid Parentheses Using Stack

**Problem statement:** Given a string containing only brackets `()`, `[]`, and `{}`, determine if the brackets are balanced and correctly nested. Print "VALID" or "INVALID".

**Example:** Input: "{[()]}" → Output: VALID. Input: "{[}]" → Output: INVALID

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine().trim();

        Deque<Character> stack = new ArrayDeque<>();

        for (char c : s.toCharArray()) {
            if (c == '(' || c == '[' || c == '{') {
                stack.push(c);
            } else {
                if (stack.isEmpty()) {
                    System.out.println("INVALID");
                    return;
                }
                char top = stack.pop();
                if ((c == ')' && top != '(') ||
                    (c == ']' && top != '[') ||
                    (c == '}' && top != '{')) {
                    System.out.println("INVALID");
                    return;
                }
            }
        }

        System.out.println(stack.isEmpty() ? "VALID" : "INVALID");
    }
}
```

**Time:** O(n). **Space:** O(n). Use `ArrayDeque` instead of `Stack` - it is faster and is the recommended Java stack implementation. `Stack` is a legacy class with synchronisation overhead.

### Problem 6.2: First Non-Repeating Character Using HashMap

**Problem statement:** Given a string, find the first character that does not repeat in the string. Print the character. If all characters repeat, print -1.

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine();

        Map<Character, Integer> freq = new LinkedHashMap<>();
        for (char c : s.toCharArray()) {
            freq.put(c, freq.getOrDefault(c, 0) + 1);
        }

        for (Map.Entry<Character, Integer> entry : freq.entrySet()) {
            if (entry.getValue() == 1) {
                System.out.println(entry.getKey());
                return;
            }
        }

        System.out.println(-1);
    }
}
```

**Time:** O(n). **Space:** O(k). `LinkedHashMap` preserves insertion order, so iterating it finds the first occurrence with frequency 1 in the correct order.

### Problem 6.3: Level-Order Traversal of a Binary Tree

**Problem statement:** Given the level-order input of a binary tree (with -1 representing null nodes), print the level-order traversal. This problem tests both tree construction and BFS.

```java
import java.util.*;

public class Main {
    static int[] val;
    static int[] left;
    static int[] right;
    static int n;

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        n = sc.nextInt();
        val = new int[n];
        left = new int[n];
        right = new int[n];
        Arrays.fill(left, -1);
        Arrays.fill(right, -1);

        for (int i = 0; i < n; i++) {
            val[i] = sc.nextInt();
            int l = sc.nextInt();
            int r = sc.nextInt();
            if (l != -1) left[i] = l;
            if (r != -1) right[i] = r;
        }

        // BFS level-order traversal
        Queue<Integer> queue = new LinkedList<>();
        queue.offer(0); // root is node 0
        StringBuilder sb = new StringBuilder();

        while (!queue.isEmpty()) {
            int node = queue.poll();
            sb.append(val[node]).append(" ");
            if (left[node] != -1) queue.offer(left[node]);
            if (right[node] != -1) queue.offer(right[node]);
        }

        System.out.println(sb.toString().trim());
    }
}
```

**Time:** O(n). **Space:** O(n). This array-based tree representation avoids pointer-based node classes and is faster to write in a timed exam. BFS uses a Queue - always use `LinkedList` or `ArrayDeque`, never `Stack` for BFS.

### Problem 6.4: Top K Frequent Elements Using PriorityQueue

**Problem statement:** Given an array of N integers and a value K, print the K elements that appear most frequently. In case of a tie in frequency, print the element with the larger value first.

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int k = sc.nextInt();

        Map<Integer, Integer> freq = new HashMap<>();
        for (int i = 0; i < n; i++) {
            int num = sc.nextInt();
            freq.put(num, freq.getOrDefault(num, 0) + 1);
        }

        // Max-heap: sort by frequency desc, then by value desc for ties
        PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) ->
            a[1] != b[1] ? b[1] - a[1] : b[0] - a[0]
        );

        for (Map.Entry<Integer, Integer> entry : freq.entrySet()) {
            pq.offer(new int[]{entry.getKey(), entry.getValue()});
        }

        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < k && !pq.isEmpty(); i++) {
            int[] top = pq.poll();
            sb.append(top[0]);
            if (i < k - 1) sb.append(" ");
        }

        System.out.println(sb.toString());
    }
}
```

**Time:** O(n + m log m) where m = unique elements. **Space:** O(m). `PriorityQueue` in Java is a min-heap by default. The comparator `(a, b) -> b[1] - a[1]` reverses it to a max-heap by frequency.

---

## Category 7: Dynamic Programming and Advanced Problems

### Problem 7.1: Longest Common Subsequence (LCS)

**Problem statement:** Given two strings, find the length of their longest common subsequence. A subsequence is a sequence that appears in both strings in the same relative order, but not necessarily contiguous.

**Example:** Input: "ABCBDAB", "BDCAB" → Output: 4 (LCS is "BCAB" or "BDAB")

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s1 = sc.nextLine().trim();
        String s2 = sc.nextLine().trim();

        int m = s1.length(), n = s2.length();
        int[][] dp = new int[m + 1][n + 1];

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (s1.charAt(i - 1) == s2.charAt(j - 1)) {
                    dp[i][j] = dp[i-1][j-1] + 1; // characters match
                } else {
                    dp[i][j] = Math.max(dp[i-1][j], dp[i][j-1]); // take best of skipping either
                }
            }
        }

        System.out.println(dp[m][n]);
    }
}
```

**Time:** O(m x n). **Space:** O(m x n). LCS is a foundational DP problem. The state: `dp[i][j]` = length of LCS of `s1[0..i-1]` and `s2[0..j-1]`. The recurrence follows directly from the definition.

### Problem 7.2: 0/1 Knapsack Problem

**Problem statement:** Given N items each with a weight and value, and a knapsack of capacity W, find the maximum value achievable without exceeding the capacity.

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(); // number of items
        int W = sc.nextInt(); // knapsack capacity

        int[] weights = new int[n];
        int[] values = new int[n];
        for (int i = 0; i < n; i++) {
            weights[i] = sc.nextInt();
            values[i] = sc.nextInt();
        }

        // dp[j] = max value achievable with capacity j
        int[] dp = new int[W + 1];

        for (int i = 0; i < n; i++) {
            // iterate capacity from W down to avoid using item i twice
            for (int j = W; j >= weights[i]; j--) {
                dp[j] = Math.max(dp[j], dp[j - weights[i]] + values[i]);
            }
        }

        System.out.println(dp[W]);
    }
}
```

**Time:** O(n x W). **Space:** O(W) - the space-optimised 1D DP version. The key: iterate `j` from `W` down to `weights[i]` to ensure each item is used at most once (0/1 constraint).

### Problem 7.3: Graph BFS - Shortest Path in an Unweighted Graph

**Problem statement:** Given an undirected graph with N nodes and E edges, and a source node S, print the shortest path distance from S to every other node. Unreachable nodes print -1.

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(); // nodes (1-indexed)
        int e = sc.nextInt(); // edges
        int source = sc.nextInt();

        List<List<Integer>> adj = new ArrayList<>();
        for (int i = 0; i <= n; i++) adj.add(new ArrayList<>());

        for (int i = 0; i < e; i++) {
            int u = sc.nextInt();
            int v = sc.nextInt();
            adj.get(u).add(v);
            adj.get(v).add(u); // undirected
        }

        int[] dist = new int[n + 1];
        Arrays.fill(dist, -1);
        dist[source] = 0;

        Queue<Integer> queue = new LinkedList<>();
        queue.offer(source);

        while (!queue.isEmpty()) {
            int node = queue.poll();
            for (int neighbour : adj.get(node)) {
                if (dist[neighbour] == -1) { // unvisited
                    dist[neighbour] = dist[node] + 1;
                    queue.offer(neighbour);
                }
            }
        }

        // print distances for all nodes except source
        for (int i = 1; i <= n; i++) {
            if (i != source) {
                System.out.println("Node " + i + ": " + dist[i]);
            }
        }
    }
}
```

**Time:** O(N + E). **Space:** O(N + E). BFS guarantees shortest path in unweighted graphs. The visited check (`dist[neighbour] == -1`) prevents processing a node multiple times.

### Problem 4.6: Find All Factors of a Number

**Problem statement:** Given a number N, print all its factors in ascending order, space-separated.

**Example:** Input: 36 → Output: 1 2 3 4 6 9 12 18 36

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();

        List<Integer> factors = new ArrayList<>();

        // collect factors up to sqrt(n)
        for (int i = 1; (long)i * i <= n; i++) {
            if (n % i == 0) {
                factors.add(i);
                if (i != n / i) factors.add(n / i); // avoid duplicate for perfect squares
            }
        }

        Collections.sort(factors); // sort ascending

        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < factors.size(); i++) {
            sb.append(factors.get(i));
            if (i < factors.size() - 1) sb.append(" ");
        }
        System.out.println(sb.toString());
    }
}
```

**Time:** O(sqrt(n) + k log k) where k = number of factors. **Space:** O(k). The paired-factor approach finds all factors in O(sqrt(n)) iterations by observing that for every factor i below sqrt(n), n/i is also a factor.

### Problem 4.7: Sieve of Eratosthenes - Print All Primes Up to N

**Problem statement:** Given N, print all prime numbers from 2 to N in ascending order.

**Example:** Input: 30 → Output: 2 3 5 7 11 13 17 19 23 29

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();

        boolean[] isComposite = new boolean[n + 1]; // false = prime by default

        // mark all multiples of each prime as composite
        for (int i = 2; (long)i * i <= n; i++) {
            if (!isComposite[i]) {
                for (int j = i * i; j <= n; j += i) {
                    isComposite[j] = true;
                }
            }
        }

        StringBuilder sb = new StringBuilder();
        boolean first = true;
        for (int i = 2; i <= n; i++) {
            if (!isComposite[i]) {
                if (!first) sb.append(" ");
                sb.append(i);
                first = false;
            }
        }
        System.out.println(sb.toString());
    }
}
```

**Time:** O(n log log n). **Space:** O(n). The Sieve starts marking multiples of i from `i*i` (not `2*i`) because all smaller multiples have already been marked by earlier primes. This is the most efficient algorithm for generating all primes up to N.

### Problem 4.8: Power Modulo (Fast Exponentiation)

**Problem statement:** Given a base B, exponent E, and modulus M, compute (B^E) % M efficiently. This avoids overflow for large B and E.

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        long b = sc.nextLong();
        long e = sc.nextLong();
        long m = sc.nextLong();

        System.out.println(powerMod(b, e, m));
    }

    static long powerMod(long base, long exp, long mod) {
        long result = 1;
        base = base % mod;

        while (exp > 0) {
            if (exp % 2 == 1) { // if current bit is set
                result = (result * base) % mod;
            }
            exp /= 2;           // right shift exponent
            base = (base * base) % mod; // square the base
        }

        return result;
    }
}
```

**Time:** O(log E). **Space:** O(1). Fast exponentiation (binary exponentiation) is essential when E can be very large. Naively computing B^E as a loop overflows and times out.

---

## Category 5 Extended: Mathematical Problems

### Problem 5.4: Pascal's Triangle

**Problem statement:** Given N, print the first N rows of Pascal's Triangle. Each row should be space-separated, with each row on a new line.

**Example:** N=5 Output:
```
1
1 1
1 2 1
1 3 3 1
1 4 6 4 1
```

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();

        int[][] triangle = new int[n][n];

        for (int i = 0; i < n; i++) {
            triangle[i][0] = 1;              // first element is always 1
            triangle[i][i] = 1;              // last element is always 1
            for (int j = 1; j < i; j++) {
                triangle[i][j] = triangle[i-1][j-1] + triangle[i-1][j];
            }
        }

        for (int i = 0; i < n; i++) {
            StringBuilder sb = new StringBuilder();
            for (int j = 0; j <= i; j++) {
                sb.append(triangle[i][j]);
                if (j < i) sb.append(" ");
            }
            System.out.println(sb.toString());
        }
    }
}
```

**Time:** O(n^2). **Space:** O(n^2). Pascal's Triangle problems sometimes ask for specific row values - in that case, compute only the required row iteratively to reduce space to O(n).

### Problem 5.5: Matrix Multiplication

**Problem statement:** Given two matrices A (m x n) and B (n x p), compute their product C = A x B and print it. Each row of C on a separate line, elements space-separated.

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int m = sc.nextInt(), n = sc.nextInt(), p = sc.nextInt();

        int[][] A = new int[m][n];
        int[][] B = new int[n][p];

        for (int i = 0; i < m; i++)
            for (int j = 0; j < n; j++)
                A[i][j] = sc.nextInt();

        for (int i = 0; i < n; i++)
            for (int j = 0; j < p; j++)
                B[i][j] = sc.nextInt();

        int[][] C = new int[m][p];
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < p; j++) {
                for (int k = 0; k < n; k++) {
                    C[i][j] += A[i][k] * B[k][j];
                }
            }
        }

        for (int i = 0; i < m; i++) {
            StringBuilder sb = new StringBuilder();
            for (int j = 0; j < p; j++) {
                sb.append(C[i][j]);
                if (j < p - 1) sb.append(" ");
            }
            System.out.println(sb.toString());
        }
    }
}
```

**Time:** O(m x n x p). **Space:** O(m x p). Matrix multiplication is a direct implementation problem - the key is getting the loop order and index arithmetic correct. Note the dimension compatibility: A is m x n and B is n x p, so C is m x p.

### Problem 5.6: Spiral Order Traversal of a Matrix

**Problem statement:** Given an m x n matrix, print its elements in spiral order (outer ring clockwise, then inner ring, etc.).

**Example:** Input 3x3 matrix [[1,2,3],[4,5,6],[7,8,9]] → Output: 1 2 3 6 9 8 7 4 5

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int m = sc.nextInt(), n = sc.nextInt();
        int[][] matrix = new int[m][n];
        for (int i = 0; i < m; i++)
            for (int j = 0; j < n; j++)
                matrix[i][j] = sc.nextInt();

        int top = 0, bottom = m - 1, left = 0, right = n - 1;
        StringBuilder sb = new StringBuilder();
        boolean first = true;

        while (top <= bottom && left <= right) {
            // traverse right
            for (int j = left; j <= right; j++) {
                if (!first) sb.append(" ");
                sb.append(matrix[top][j]);
                first = false;
            }
            top++;

            // traverse down
            for (int i = top; i <= bottom; i++) {
                sb.append(" ").append(matrix[i][right]);
            }
            right--;

            // traverse left (if rows remain)
            if (top <= bottom) {
                for (int j = right; j >= left; j--) {
                    sb.append(" ").append(matrix[bottom][j]);
                }
                bottom--;
            }

            // traverse up (if columns remain)
            if (left <= right) {
                for (int i = bottom; i >= top; i--) {
                    sb.append(" ").append(matrix[i][left]);
                }
                left++;
            }
        }

        System.out.println(sb.toString());
    }
}
```

**Time:** O(m x n). **Space:** O(1) excluding output. The four-boundary approach is the cleanest way to implement spiral traversal. The critical conditions (`if (top <= bottom)` before traversing left, `if (left <= right)` before traversing up) prevent duplicate traversal of rows/columns when the matrix reduces to a single row or column.

---

## Category 8: Greedy and Pattern Problems

### Problem 8.1: Activity Selection Problem

**Problem statement:** Given N activities each with a start time and finish time, find the maximum number of activities that can be performed by a single person, assuming they can only work on one activity at a time. Print the count.

**Example:** Activities: (1,3),(2,5),(3,9),(0,6),(5,7),(8,9) → Output: 4

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[][] activities = new int[n][2];

        for (int i = 0; i < n; i++) {
            activities[i][0] = sc.nextInt(); // start
            activities[i][1] = sc.nextInt(); // finish
        }

        // sort by finish time (greedy: always take the earliest-finishing activity)
        Arrays.sort(activities, (a, b) -> a[1] - b[1]);

        int count = 1;
        int lastFinish = activities[0][1];

        for (int i = 1; i < n; i++) {
            if (activities[i][0] >= lastFinish) { // starts after last activity finishes
                count++;
                lastFinish = activities[i][1];
            }
        }

        System.out.println(count);
    }
}
```

**Time:** O(n log n) for sorting, O(n) for selection. **Space:** O(1). The greedy choice: always select the activity that finishes earliest and does not overlap with the last selected activity. This maximises the remaining time for future activities.

### Problem 8.2: Number Pattern - Triangle

**Problem statement:** Given N, print the following number pattern for N rows. Row i contains the number i repeated i times.

**Example N=4:**
```
1
2 2
3 3 3
4 4 4 4
```

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();

        for (int i = 1; i <= n; i++) {
            StringBuilder sb = new StringBuilder();
            for (int j = 1; j <= i; j++) {
                sb.append(i);
                if (j < i) sb.append(" ");
            }
            System.out.println(sb.toString());
        }
    }
}
```

### Problem 8.3: Floyd's Cycle Detection - Find Duplicate in Array

**Problem statement:** Given an array of N+1 integers where each integer is between 1 and N inclusive, there is exactly one duplicate number. Find it without modifying the array and using only O(1) extra space.

**Example:** Input: [1,3,4,2,2] → Output: 2

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n + 1];
        for (int i = 0; i <= n; i++) arr[i] = sc.nextInt(); // n+1 elements

        // Floyd's cycle detection: treat array values as pointers
        int slow = arr[0];
        int fast = arr[0];

        // Phase 1: find meeting point inside the cycle
        do {
            slow = arr[slow];
            fast = arr[arr[fast]];
        } while (slow != fast);

        // Phase 2: find the entrance to the cycle (the duplicate)
        slow = arr[0];
        while (slow != fast) {
            slow = arr[slow];
            fast = arr[fast];
        }

        System.out.println(slow);
    }
}
```

**Time:** O(n). **Space:** O(1). This application of Floyd's cycle detection treats the array as a linked list where `arr[i]` is the "next" pointer from node i. The duplicate creates a cycle. This is a Premium-level problem that demonstrates deep algorithmic thinking.

---

## Category 9: Additional String Problems

### Problem 9.1: Check if String is a Rotation of Another

**Problem statement:** Given two strings S1 and S2 of equal length, determine if S2 is a rotation of S1. Print "YES" or "NO".

**Example:** "abcde" and "cdeab" → YES (rotate left by 2)

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s1 = sc.nextLine().trim();
        String s2 = sc.nextLine().trim();

        if (s1.length() != s2.length()) {
            System.out.println("NO");
            return;
        }

        // If S2 is a rotation of S1, then S2 is a substring of S1+S1
        String doubled = s1 + s1;
        System.out.println(doubled.contains(s2) ? "YES" : "NO");
    }
}
```

**Time:** O(n) using Java's `contains()` which uses an optimised substring search. **Space:** O(n) for the doubled string. This is an elegant one-observation solution: every rotation of S1 appears as a substring of S1+S1.

### Problem 9.2: Count Occurrences of a Pattern in a Text

**Problem statement:** Given a text string T and a pattern string P, count how many times P appears in T (overlapping occurrences count separately).

**Example:** T="ababab", P="aba" → Output: 2 (at index 0 and index 2, overlapping)

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String text = sc.nextLine().trim();
        String pattern = sc.nextLine().trim();

        int count = 0;
        int idx = 0;

        while ((idx = text.indexOf(pattern, idx)) != -1) {
            count++;
            idx++; // advance by 1 to allow overlapping matches
        }

        System.out.println(count);
    }
}
```

**Time:** O(n x m) in worst case using Java's built-in indexOf. **Space:** O(1). For overlapping matches, advance `idx` by 1 rather than by `pattern.length()` after each match.

### Problem 9.3: Compress a String (Run-Length Encoding)

**Problem statement:** Given a string, compress it using run-length encoding. If a character appears consecutively k times, write the character followed by k. If a character appears only once, write just the character. If the compressed string is not shorter than the original, return the original.

**Example:** "aaabccdddd" → "a3bc2d4"

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine().trim();

        StringBuilder compressed = new StringBuilder();
        int i = 0;

        while (i < s.length()) {
            char c = s.charAt(i);
            int count = 1;
            while (i + count < s.length() && s.charAt(i + count) == c) {
                count++;
            }
            compressed.append(c);
            if (count > 1) compressed.append(count);
            i += count;
        }

        String result = compressed.toString();
        System.out.println(result.length() < s.length() ? result : s);
    }
}
```

**Time:** O(n). **Space:** O(n). Run-length encoding is a common TCS string problem. The condition "print original if compressed is not shorter" catches the case where alternating characters (like "abababab") produce a compressed string longer than the original.

---

## Category 10: Two-Pointer and Sliding Window

### Problem 10.1: Three Sum - Find All Triplets That Sum to Zero

**Problem statement:** Given an array of N integers, find all unique triplets (a, b, c) such that a + b + c = 0. Print each triplet sorted in ascending order, one per line. No duplicate triplets.

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();

        Arrays.sort(arr); // sorting enables two-pointer + duplicate skipping
        boolean found = false;

        for (int i = 0; i < n - 2; i++) {
            // skip duplicate values for the first element
            if (i > 0 && arr[i] == arr[i-1]) continue;

            int left = i + 1, right = n - 1;

            while (left < right) {
                int sum = arr[i] + arr[left] + arr[right];

                if (sum == 0) {
                    System.out.println(arr[i] + " " + arr[left] + " " + arr[right]);
                    found = true;
                    // skip duplicates
                    while (left < right && arr[left] == arr[left+1]) left++;
                    while (left < right && arr[right] == arr[right-1]) right--;
                    left++;
                    right--;
                } else if (sum < 0) {
                    left++;
                } else {
                    right--;
                }
            }
        }

        if (!found) System.out.println("No triplets found");
    }
}
```

**Time:** O(n^2). **Space:** O(1) excluding output. The two-pointer approach reduces the naive O(n^3) brute force to O(n^2) by exploiting the sorted order.

### Problem 10.2: Minimum Window Substring

**Problem statement:** Given strings S and T, find the minimum length substring of S that contains all characters of T (with the required frequencies). Print the substring, or "NOT FOUND" if no such window exists.

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine().trim();
        String t = sc.nextLine().trim();

        if (s.length() < t.length()) {
            System.out.println("NOT FOUND");
            return;
        }

        Map<Character, Integer> need = new HashMap<>();
        for (char c : t.toCharArray()) need.put(c, need.getOrDefault(c, 0) + 1);

        int required = need.size(); // distinct chars we need to satisfy
        int formed = 0;             // distinct chars currently satisfied
        Map<Character, Integer> window = new HashMap<>();

        int left = 0, minLen = Integer.MAX_VALUE;
        int minLeft = 0;

        for (int right = 0; right < s.length(); right++) {
            char c = s.charAt(right);
            window.put(c, window.getOrDefault(c, 0) + 1);

            if (need.containsKey(c) && window.get(c).equals(need.get(c))) {
                formed++;
            }

            // shrink window from left while all chars are satisfied
            while (formed == required) {
                if (right - left + 1 < minLen) {
                    minLen = right - left + 1;
                    minLeft = left;
                }
                char leftChar = s.charAt(left);
                window.put(leftChar, window.get(leftChar) - 1);
                if (need.containsKey(leftChar) && window.get(leftChar) < need.get(leftChar)) {
                    formed--;
                }
                left++;
            }
        }

        System.out.println(minLen == Integer.MAX_VALUE ? "NOT FOUND" : s.substring(minLeft, minLeft + minLen));
    }
}
```

**Time:** O(|S| + |T|). **Space:** O(|T|). The minimum window substring problem is a classic advanced sliding window problem - it tests both the technique and the bookkeeping required to track satisfaction of requirements.

---

## Handling Large Inputs Efficiently

### Reading Arrays Faster With BufferedReader

For problems where input size is explicitly large (10,000+ elements), switching from Scanner to BufferedReader provides a meaningful speed improvement:

```java
import java.util.*;
import java.io.*;

public class Main {
    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        PrintWriter pw = new PrintWriter(new BufferedWriter(new OutputStreamWriter(System.out)));

        int n = Integer.parseInt(br.readLine().trim());
        StringTokenizer st = new StringTokenizer(br.readLine());
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = Integer.parseInt(st.nextToken());

        // ... process and write output via pw
        pw.println(answer);
        pw.flush(); // critical: must flush to ensure output is written
    }
}
```

`StringTokenizer` is faster than `String.split()` for space-separated integer parsing. `PrintWriter` with `BufferedWriter` batches output, which is faster than multiple `System.out.println()` calls for large output.

**Important:** Always call `pw.flush()` before the program ends. Buffered output that is not flushed is lost, producing no output even when your logic is correct.

### Common Input Patterns in TCS Coding Problems

**Pattern 1: N followed by N integers on one line**
```java
int n = sc.nextInt();
int[] arr = new int[n];
for (int i = 0; i < n; i++) arr[i] = sc.nextInt();
```

**Pattern 2: Multiple test cases**
```java
int t = sc.nextInt(); // number of test cases
while (t-- > 0) {
    int n = sc.nextInt();
    // process test case
}
```

**Pattern 3: Two strings on separate lines**
```java
String s1 = sc.nextLine();
String s2 = sc.nextLine();
```

**Pattern 4: Matrix input (m rows, each with n space-separated values)**
```java
int m = sc.nextInt(), n = sc.nextInt();
int[][] matrix = new int[m][n];
for (int i = 0; i < m; i++)
    for (int j = 0; j < n; j++)
        matrix[i][j] = sc.nextInt();
```

**Pattern 5: Graph input (N nodes, E edges as pairs)**
```java
int nodes = sc.nextInt(), edges = sc.nextInt();
List<List<Integer>> adj = new ArrayList<>();
for (int i = 0; i <= nodes; i++) adj.add(new ArrayList<>());
for (int i = 0; i < edges; i++) {
    int u = sc.nextInt(), v = sc.nextInt();
    adj.get(u).add(v);
    adj.get(v).add(u);
}
```

Recognising these input patterns and having the reading code ready reduces the setup time for each problem, leaving more time for the actual logic.

---

### Avoiding Common Runtime Errors

**ArrayIndexOutOfBoundsException:** The most frequent runtime error. Always verify array index bounds before access. When iterating an array, use `i < arr.length` not `i <= arr.length`. When accessing `arr[i-1]`, ensure `i > 0` first.

**NullPointerException:** Occurs when calling a method on a null object reference. Common causes: calling methods on uninitialised objects, accessing a map value that does not exist (use `getOrDefault` rather than `get`), or returning null from a method and then calling methods on the return value.

**StackOverflowError:** Occurs when recursion is too deep. For large inputs, convert recursive solutions to iterative ones. Tree and graph traversals are the most common culprits. The iterative DFS using an explicit stack avoids this.

**Integer Overflow:** When arithmetic on `int` values exceeds 2,147,483,647. Use `long` for factorials, Fibonacci (beyond term 46), large sums, and products. The cast `(long) a * b` forces the multiplication to occur in long arithmetic even if `a` and `b` are individually int.

### Handling Edge Cases Systematically

Before submitting, mentally run through:

1. **Empty input:** What if N=0? Does your loop handle zero iterations correctly?
2. **Single element:** What if N=1? Does your two-pointer or comparison logic handle a single-element array?
3. **All identical elements:** What if all elements are the same? Does your "find second maximum" or "find unique elements" logic handle this?
4. **Negative numbers:** Does your solution work if the input contains negative integers? `Integer.MIN_VALUE` comparisons may behave unexpectedly.
5. **Large values:** Will your variables overflow with the maximum input values? Use `long` where needed.

### StringBuilder vs String Concatenation in Loops

**Never concatenate strings in a loop using `+`:**

```java
// WRONG - creates a new String object every iteration: O(n^2) total
String result = "";
for (int i = 0; i < n; i++) result += arr[i] + " ";

// CORRECT - StringBuilder modifies in place: O(n) total
StringBuilder sb = new StringBuilder();
for (int i = 0; i < n; i++) {
    sb.append(arr[i]);
    if (i < n - 1) sb.append(" ");
}
System.out.println(sb.toString());
```

For small inputs, the difference is imperceptible. For large inputs (printing 100,000 elements), the difference between O(n) and O(n^2) string building is the difference between passing and timing out.

### Scanner Peculiarities to Know

**`next()` vs `nextLine()`:** `next()` reads the next token (word), stopping at any whitespace. `nextLine()` reads the entire line including spaces. For sentences or strings with spaces, always use `nextLine()`.

**`hasNext()` and `hasNextInt()` for unknown input size:** When the problem gives an unspecified number of inputs terminated by EOF, loop on `sc.hasNext()`:

```java
while (sc.hasNext()) {
    int n = sc.nextInt();
    // process n
}
```

**Multiple inputs on one line:** For "read N integers from one line separated by spaces":

```java
String[] parts = sc.nextLine().split("\\s+");
int[] arr = new int[parts.length];
for (int i = 0; i < parts.length; i++) arr[i] = Integer.parseInt(parts[i].trim());
```

### Collections Utility Methods Worth Knowing

```java
Collections.sort(list);                    // ascending sort
Collections.sort(list, Collections.reverseOrder()); // descending sort
Collections.max(list);                     // maximum element
Collections.min(list);                     // minimum element
Collections.frequency(list, element);      // count occurrences
Collections.reverse(list);                 // reverse in place
Collections.shuffle(list);                 // random shuffle
Collections.nCopies(n, value);            // list of n copies of value
```

---

## Time and Space Complexity Reference

Every solution you submit to TCS Advanced Coding should have the complexity in your head, even if you do not write it in the code:

| Algorithm / Operation | Time | Space |
|---|---|---|
| Linear scan | O(n) | O(1) |
| Binary search | O(log n) | O(1) |
| Bubble/Selection/Insertion sort | O(n^2) | O(1) |
| Merge sort / Heap sort | O(n log n) | O(n) / O(1) |
| Quick sort (avg) | O(n log n) | O(log n) |
| HashMap get/put | O(1) avg | O(n) |
| HashSet contains/add | O(1) avg | O(n) |
| PriorityQueue offer/poll | O(log n) | O(n) |
| BFS / DFS on graph | O(V + E) | O(V) |
| 2D DP (m x n table) | O(m x n) | O(m x n) |
| String reverse (StringBuilder) | O(n) | O(n) |

When choosing between two correct approaches, the one with better time complexity wins. When time complexities are equal, choose the one with better space complexity. When both are equal, choose the one that is cleaner to write correctly under time pressure.

---

## Final Preparation Checklist for TCS Java Coding

One week before your TCS coding test, verify that you can write each of the following from memory in under 10 minutes:

- Read N integers from input into an array
- Sort an array with a custom comparator
- Build and query a frequency map using HashMap
- Check palindrome with two pointers
- Find GCD using Euclidean algorithm
- Check primality using trial division up to sqrt(n)
- BFS on an adjacency list graph
- Kadane's Algorithm for maximum subarray sum
- Valid parentheses check with a stack
- Fibonacci series iteratively with long

These ten implementations cover the core of what TCS Advanced Coding tests. Write each one by hand (not in an IDE with autocomplete) at least twice. The act of writing by hand in a low-feedback environment builds the same muscle memory you will need on test day.

On the day of the coding test: read the problem statement fully before writing a single line. Understand the input format and output format precisely. Write your solution, test it mentally against the provided examples, then submit. If time remains, test against your own edge cases before the submission deadline.

---

## Category 3 Extended: More Array Problems

### Problem 3.5: Dutch National Flag - Sort Array of 0s, 1s, and 2s

**Problem statement:** Given an array containing only 0s, 1s, and 2s, sort it in a single pass without using a sorting function.

**Example:** Input: [2,0,1,1,0,2,1] → Output: 0 0 1 1 1 2 2

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();

        int low = 0, mid = 0, high = n - 1;

        while (mid <= high) {
            if (arr[mid] == 0) {
                int temp = arr[low]; arr[low] = arr[mid]; arr[mid] = temp;
                low++; mid++;
            } else if (arr[mid] == 1) {
                mid++;
            } else {
                int temp = arr[mid]; arr[mid] = arr[high]; arr[high] = temp;
                high--;
                // do NOT increment mid
            }
        }

        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) {
            sb.append(arr[i]);
            if (i < n - 1) sb.append(" ");
        }
        System.out.println(sb.toString());
    }
}
```

**Time:** O(n). **Space:** O(1). The Dutch National Flag algorithm maintains: all 0s before `low`, all 1s between `low` and `mid`, unknown between `mid` and `high`, all 2s after `high`. When `arr[mid]` is 2, swap with `high` and decrement `high` but do not increment `mid` - the swapped element at `mid` has not been examined yet.

### Problem 3.6: Product Array Without Division

**Problem statement:** Given an array of N integers, construct a result array such that result[i] is the product of all elements except arr[i]. No division allowed.

**Example:** Input: [1,2,3,4,5] → Output: 120 60 40 30 24

```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();

        int[] result = new int[n];
        result[0] = 1;
        for (int i = 1; i < n; i++) result[i] = result[i-1] * arr[i-1];

        int rightProduct = 1;
        for (int i = n - 1; i >= 0; i--) {
            result[i] *= rightProduct;
            rightProduct *= arr[i];
        }

        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) {
            sb.append(result[i]);
            if (i < n - 1) sb.append(" ");
        }
        System.out.println(sb.toString());
    }
}
```

**Time:** O(n). **Space:** O(n) for result array, O(1) extra. The left pass fills result[i] with the product of all elements to the left. The right pass multiplies by the product of all elements to the right. Together these give the product of all elements except arr[i].

---

## Recognising TCS Problem Patterns

After working through these problems, you will notice that most TCS Advanced Coding problems map to a small set of recognisable patterns. Training yourself to identify the pattern before writing code is the most important meta-skill.

**Pattern 1: Frequency Count.** When the problem mentions counts, occurrences, uniqueness, or most/least frequent - reach for `HashMap<T, Integer>` or `int[26]` for character frequencies.

**Pattern 2: Sliding Window.** When the problem asks for the minimum or maximum subarray or substring satisfying a condition - use two pointers `left` and `right`. The window expands rightward and shrinks leftward as needed.

**Pattern 3: Sorted Array Plus Two Pointers.** Pair or triplet sum problems on arrays - sort first, then use two pointers converging from both ends. Reduces O(n^2) brute force to O(n).

**Pattern 4: Stack for Matching and Sequential Dependency.** Bracket matching, next greater element, expression evaluation, valid sequences - stack is almost always the right choice.

**Pattern 5: BFS for Shortest Path, DFS for Exploration.** Graph problems asking for minimum steps or minimum distance - BFS with a queue. Problems asking for all paths, connected components, or cycle detection - DFS with recursion or an explicit stack.

**Pattern 6: DP for Optimal Substructure With Overlapping Subproblems.** When brute-force recursion would re-compute the same subproblem many times - memoize with an array. Identify the state, recurrence, base case, and which cell holds the answer.

Recognising the pattern gets you from "blank page" to "approach" in under 30 seconds. Writing the Java code for a known pattern then takes 5-10 minutes. The remaining time is for edge case handling and testing.

---

## Debugging Under Exam Conditions

When your code compiles but fails some test cases:

1. **Trace the provided example manually.** Step through your code with the sample input. If the output does not match, the bug is in your logic.
2. **Test edge cases:** empty input, single element, all identical elements, maximum values, negative numbers.
3. **Check integer overflow.** Multiply by using `long`, especially for Fibonacci, factorials, and products.
4. **Check array bounds.** Off-by-one errors in `< vs <=` and accessing `arr[i-1]` when `i=0` are the most common bugs.
5. **Check output format.** Extra trailing spaces, wrong delimiter, or missing newline all fail test cases even with correct logic.
6. **Re-read the problem.** A misread constraint or output format requirement causes otherwise correct solutions to fail consistently.

---

## Java-Specific Pitfalls in TCS Coding Rounds

These pitfalls are specific to Java and appear frequently enough to be worth memorising before the test.

### The Integer Cache Trap

Java caches `Integer` objects for values between -128 and 127. This creates a subtle bug when comparing Integer objects with `==`:

```java
Integer a = 128;
Integer b = 128;
System.out.println(a == b); // FALSE - different objects
System.out.println(a.equals(b)); // TRUE - same value
```

When using Integer objects (not primitive `int`) in comparisons - for instance, when retrieving values from a `HashMap<Character, Integer>` and comparing them - always use `.equals()` or unbox to primitive first. The line `if (window.get(c) == need.get(c))` uses `==` on Integer objects and will silently fail for values above 127. Write `if (window.get(c).equals(need.get(c)))` or `if ((int)window.get(c) == (int)need.get(c))`.

### Scanner's nextInt After nextLine

After reading an integer with `sc.nextInt()`, calling `sc.nextLine()` reads the leftover newline character, not the next actual line:

```java
// WRONG
int n = sc.nextInt();
String s = sc.nextLine(); // reads "" (empty - the leftover newline)

// CORRECT
int n = sc.nextInt();
sc.nextLine(); // consume the newline
String s = sc.nextLine(); // reads the actual next line
```

This is the most common Scanner bug in TCS coding submissions.

### Static vs Instance Methods

TCS iON's code template uses a single `Main` class with a `main` method. When you write helper methods, declare them as `static` since they are called from the `static main` method:

```java
public class Main {
    public static void main(String[] args) {
        int result = solve(5); // FINE - calling a static method from main
    }

    static int solve(int n) { // must be static
        return n * 2;
    }
}
```

Forgetting `static` on helper methods causes a compilation error: "non-static method cannot be referenced from a static context."

### Printing Long vs Int

When using `System.out.println()` with arithmetic that might produce a `long`, ensure the computation is done in `long` before printing:

```java
int a = 1000000, b = 2000000;
System.out.println(a * b); // OVERFLOW - computes as int
System.out.println((long)a * b); // CORRECT - computes as long
```

The cast `(long)a` before the multiplication forces the entire expression to long arithmetic.

### String Comparison

Never compare Strings with `==` in Java:

```java
String s1 = "hello";
String s2 = new String("hello");
System.out.println(s1 == s2);      // FALSE - different object references
System.out.println(s1.equals(s2)); // TRUE - same content
```

Always use `.equals()` for String comparison. For case-insensitive comparison, use `.equalsIgnoreCase()`.

### Collections.sort on Primitive Arrays

`Collections.sort()` works on `List` objects, not primitive arrays. For primitive `int[]` arrays, use `Arrays.sort()`:

```java
int[] arr = {3, 1, 2};
Arrays.sort(arr);             // CORRECT for int[]

Integer[] boxed = {3, 1, 2};
Arrays.sort(boxed, (a,b) -> b-a); // custom comparator requires boxed Integer
```

To sort a primitive `int[]` in descending order, either convert to `Integer[]`, sort with a comparator, and convert back - or sort ascending and iterate in reverse.

---

## Writing Clean Code Under Time Pressure

The gap between code that is technically correct and code that passes all TCS test cases is often in cleanliness rather than logic. These practices take seconds each but prevent entire categories of test case failures.

### Always Handle the Empty Input Case

Before writing your main logic, add a guard for n=0 or empty input:

```java
if (n == 0) {
    System.out.println(0); // or whatever the correct output for empty input is
    return;
}
```

TCS problems frequently include test cases with minimum input values. Code that crashes or produces wrong output for n=0 fails those test cases.

### Use trim() When Reading String Inputs

```java
String s = sc.nextLine().trim();
```

Trailing whitespace in string input causes subtle failures in length comparisons, character-by-character processing, and pattern matching. Always trim string inputs unless the problem explicitly requires preserving whitespace.

### Initialize Comparison Variables Correctly

When finding a maximum: initialise to `Integer.MIN_VALUE` (not 0, which is wrong if all values are negative).
When finding a minimum: initialise to `Integer.MAX_VALUE` (not 0, which is wrong if all values are positive).
When counting: initialise to 0.
When computing product: initialise to 1 (not 0, which makes the product always 0).

### Print Exactly What Is Asked

If the problem says "print YES or NO", do not print "Yes/No" or "yes/no". Java string literals are case-sensitive, and TCS test cases are matched exactly. Capitalisation matters. Spacing matters. Punctuation matters.

If the problem says "print space-separated values on one line", do not add a newline between values. If it says "each value on a separate line", use `println` for each value.

---

## A 30-Day Coding Improvement Plan for TCS

If you have 30 days before your TCS test and want to meaningfully improve your Advanced Coding score:

**Days 1-5:** Foundation. Write programs for: read and print an array, reverse a string, check palindrome, sum of digits, count vowels. These warm up the fundamental I/O and loop patterns.

**Days 6-10:** Number theory. Write: isPrime, GCD, LCM, factorial, Fibonacci, Armstrong number check, find all factors, Sieve of Eratosthenes, decimal to binary. These are the single-function problems that appear as Problem 1 in many TCS Advanced Coding rounds.

**Days 11-15:** Arrays. Write: second largest, rotate array, find all pairs summing to K, Kadane's maximum subarray, Dutch National Flag, merge two sorted arrays. These cover the array manipulation category thoroughly.

**Days 16-20:** Strings. Write: anagram check, frequency count, first non-repeating character, reverse words, run-length encoding, longest substring without repeating characters, check if rotation. String problems form the largest category in TCS coding rounds.

**Days 21-25:** Data structures. Write: valid parentheses with stack, queue using two stacks, level-order tree traversal with BFS, top-K frequent elements with PriorityQueue. These cover Problem 2-level difficulty.

**Days 26-30:** Advanced patterns. Write: LCS (DP), 0/1 knapsack, graph BFS for shortest path, activity selection (greedy), minimum window substring. Even partial understanding of these problems earns partial credit on Problem 2 and Problem 3.

The rule for each day: write the solution from memory, not by copying. If you cannot write it from memory, you do not know it well enough yet. Re-read, understand, close the reference, write it again. Repeat until you can produce it in under 8 minutes with no assistance.

This 30-day plan, executed consistently at 45-60 minutes per day, produces a measurable improvement in coding speed and accuracy that directly translates to more test cases passed on the day of the exam.

---

## Frequently Asked Questions: TCS Java Coding

**Should I use Java or Python for TCS coding rounds?**
Both are valid. Java is better if you are already fluent in it - the standard library is powerful and the explicit typing reduces logical errors. Python is better for candidates who are more comfortable with it and want faster prototyping. The key rule: use whichever language you can write bug-free code in faster under time pressure. Do not switch languages two weeks before the exam.

**Is Java 8+ syntax (lambdas, streams) supported on TCS iON?**
TCS iON typically uses a standard JDK that supports Java 8+ features including lambda expressions and stream operations. Lambda comparators (`(a, b) -> b - a`) are fully supported and are used in the solutions throughout this guide. Avoid using very recent Java features (records, sealed classes) that may not be available on all TCS iON environments.

**What if my solution gets a partial score - should I keep submitting?**
Yes. TCS iON coding problems award credit per test case passed. Each submission replaces the previous one, and your score is updated to the highest score achieved across all your submissions. If you improve your solution to handle more edge cases, resubmit. There is no penalty for multiple submissions on most TCS coding platforms.

**How many lines of code are typical for TCS Problem 1?**
Most Problem 1 solutions are 15-35 lines of code including import statements and the class structure. If your solution is growing beyond 50 lines for what seems like a straightforward problem, you may be overcomplicating it. Step back and re-read the problem statement.

**What if the problem requires a data structure Java does not have natively?**
Java has all the data structures needed for TCS problems in its standard library. If you think you need something exotic (like a Trie or a Segment Tree), re-read the problem - TCS coding problems at NQT/ITP level do not require these structures. The problem likely has a HashMap or array-based solution.

**Should I comment my code in the TCS coding exam?**
Comments do not affect your score - only the output matters. However, brief comments help you re-read your own code when debugging. A one-line comment per logical block (// frequency count, // two-pointer search, // print result) is worth the 10 seconds it takes during a 45-minute session.

**What is the most common reason for a "Wrong Answer" verdict on TCS iON?**
Based on common patterns: incorrect output format (trailing spaces, wrong delimiter, wrong case), integer overflow when using `int` instead of `long`, and Scanner input handling errors (the `nextLine` after `nextInt` bug). These three causes account for the majority of logically-correct solutions that still fail test cases.

Practice writing complete solutions including input reading and output formatting. A solution that has perfect logic but wrong output format scores zero. Every hour of full-solution practice (reading input, processing, formatting output) is more valuable than an hour of algorithm-only practice without I/O.
