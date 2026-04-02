---
layout: post
title: "Infosys Coding Questions: Complete Programming Test Guide"
page_title: "Infosys Coding Questions and Answers: 80+ Solved Problems with Full Solutions Across All Categories"
date: 2021-08-30
categories: ["Industry"]
tags: ["Infosys Coding Questions", "Infosys Programming Test", "Infosys Coding Round", "Infosys Coding Questions with Solutions", "Infosys Pseudocode Questions", "Infosys Programming Questions", "Infosys Coding Test Pattern", "Infosys Coding Round Preparation"]
excerpt: "80+ solved Infosys coding questions with complete Python and Java solutions across arrays, strings, patterns, algorithms, recursion, DP, and pseudocode. Includes test format, strategy, and 4-week preparation plan."
image: "/assets/images/blog/blog-33.webp"
reading_time: 60
author: "ritika-singh"
last_updated: 2026-04-02
---
The Infosys coding assessment is where most candidates lose marks even after solid aptitude performance. Aptitude questions are objective and formula-driven. Coding questions require algorithmic thinking and the ability to write correct, working code under time pressure. Many students prepare extensively for the aptitude section and treat the coding round as an afterthought, arriving underprepared for the specific patterns Infosys uses.

![Infosys Coding Questions Complete Guide](/assets/images/blog/blog-33.webp)

This guide is different from the shallow "top 10 Infosys coding questions" lists that dominate search results. Every problem here comes with a complete working solution in Python and Java, a detailed explanation of the approach, time and space complexity analysis, the edge cases most candidates miss, and the specific pattern each question belongs to. The pseudocode section is treated separately because it tests a different skill from implementation coding.

The problems are organized by category and difficulty, matching the actual Infosys assessment pattern. A full mock coding test at the end mirrors the real format.

---

## Table of Contents

1. [Infosys Coding Assessment: Format and Strategy](#infosys-coding-assessment-format-and-strategy)
2. [Category 1: Array and Number Manipulation](#category-1-array-and-number-manipulation)
3. [Category 2: String Processing](#category-2-string-processing)
4. [Category 3: Pattern Printing](#category-3-pattern-printing)
5. [Category 4: Mathematical and Number Theory](#category-4-mathematical-and-number-theory)
6. [Category 5: Searching and Sorting](#category-5-searching-and-sorting)
7. [Category 6: Recursion and Dynamic Programming](#category-6-recursion-and-dynamic-programming)
8. [Category 7: Pseudocode Tracing Questions](#category-7-pseudocode-tracing-questions)
9. [Full Mock Coding Test](#full-mock-coding-test)
10. [Language Tips: Python vs Java vs C++](#language-tips-python-vs-java-vs-c)
11. [The 4-Week Preparation Plan](#the-4-week-preparation-plan)
12. [Frequently Asked Questions](#frequently-asked-questions)

---

## Infosys Coding Assessment: Format and Strategy

**The Coding Section Structure:**

The Infosys online assessment includes a dedicated programming section separate from the aptitude sections.

Standard SE track: 2 coding problems, 30 minutes total. The problems are typically at Easy and Easy-Medium difficulty. Both require writing complete, correct code that passes all hidden test cases on the online judge.

DSE track: Higher difficulty, 2-3 problems with a mix of Medium and Hard. More emphasis on algorithmic efficiency.

**The Online Judge:**

Infosys uses an online code judge that compiles and runs your code against hidden test cases. Each test case returns Accepted (correct output) or Wrong Answer. Some judges also return Time Limit Exceeded (TLE) for solutions that are too slow.

Your code must be: syntactically correct, logically correct for all test cases including edge cases, and efficient enough to run within the time limit. A partial solution that handles some test cases scores better than a blank submission in partial-credit configurations.

**Language Selection:**

Infosys typically supports C, C++, Java, and Python. The specific languages are shown at the start of the coding section. Java is the recommended choice for Infosys-specific reasons: Mysore foundation training uses Java, so demonstrating Java fluency signals direct readiness. Python is the best choice for candidates who can write faster and more accurately in it. Never use a language you are not fluent in during a timed assessment.

**The 30-Minute Time Strategy:**

Minutes 0-2: Read both problems completely. Identify which is easier.
Minutes 2-20: Solve the easier problem: code, test against sample cases, handle edge cases, submit.
Minutes 20-30: Attempt the harder problem. A partial solution that handles the sample cases is better than a blank submission.

Never spend the full 30 minutes on one problem. A correct easy solution plus a partial medium solution outscores a single partially solved medium every time.

**The Edge Case Mindset:**

The hidden test cases almost always include: empty input, single element, all identical elements, maximum size input, negative numbers (where applicable), and the boundary conditions specified in the constraints. Test your code against all of these before submitting, not just the sample cases.

---

## Category 1: Array and Number Manipulation

Arrays are the most consistently appearing category in Infosys coding assessments. The patterns range from simple traversal to two-pointer techniques.

---

### Problem 1.1 (Easy): Find the Second Largest Element

Given an array of integers, find the second largest distinct element without sorting.

**Sample Input:** [3, 8, 1, 8, 5, 7]
**Sample Output:** 7

**Approach:** Single pass maintaining two variables. When a new element exceeds the current largest, update both. When it exceeds only the second largest, update only that.

```python
def second_largest(arr):
    if len(arr) < 2:
        return -1
    first = second = float('-inf')
    for num in arr:
        if num > first:
            second = first
            first = num
        elif num > second and num != first:
            second = num
    return second if second != float('-inf') else -1

print(second_largest([3, 8, 1, 8, 5, 7]))  # 7
print(second_largest([5, 5, 5]))            # -1 (no distinct second)
print(second_largest([1]))                  # -1 (too short)
```

```java
public static int secondLargest(int[] arr) {
    if (arr.length < 2) return -1;
    int first = Integer.MIN_VALUE, second = Integer.MIN_VALUE;
    for (int num : arr) {
        if (num > first) {
            second = first;
            first = num;
        } else if (num > second && num != first) {
            second = num;
        }
    }
    return second == Integer.MIN_VALUE ? -1 : second;
}
```

**Time:** O(n), **Space:** O(1)

**The Trap:** Sorting first is O(n log n) and also fails when the requirement is "distinct from the largest." The single-pass approach is both faster and correct.

---

### Problem 1.2 (Easy): Count Even and Odd Numbers

Given an array, count how many elements are even and how many are odd.

```python
def count_even_odd(arr):
    even = sum(1 for x in arr if x % 2 == 0)
    odd = len(arr) - even
    return even, odd

e, o = count_even_odd([1, 2, 3, 4, 5, 6])
print(f"Even: {e}, Odd: {o}")  # Even: 3, Odd: 3
```

**Java note:** In Java and C++, `-3 % 2 = -1` (not 1). Use `Math.abs(x % 2) == 0` to safely handle negative numbers.

---

### Problem 1.3 (Easy): Rotate Array by K Positions

Rotate an array K positions to the right.

**Sample Input:** [1, 2, 3, 4, 5], K=2
**Sample Output:** [4, 5, 1, 2, 3]

```python
def rotate_right(arr, k):
    n = len(arr)
    k = k % n          # Handle k > n
    return arr[-k:] + arr[:-k]

print(rotate_right([1, 2, 3, 4, 5], 2))  # [4, 5, 1, 2, 3]
print(rotate_right([1, 2, 3], 6))        # [1, 2, 3] (6%3=0)
```

**In-place O(1) space using reversal:**
```python
def rotate_inplace(arr, k):
    n = len(arr)
    k = k % n
    arr.reverse()
    arr[:k] = arr[:k][::-1]
    arr[k:] = arr[k:][::-1]
    return arr
```

---

### Problem 1.4 (Medium): Find All Pairs with Given Sum

Given an array and a target, find all unique pairs whose sum equals the target.

**Sample Input:** [1, 5, 3, 7, 2, 8], target=9
**Sample Output:** [(1, 8), (2, 7)]

```python
def find_pairs(arr, target):
    seen = set()
    pairs = set()
    for num in arr:
        complement = target - num
        if complement in seen:
            pair = (min(num, complement), max(num, complement))
            pairs.add(pair)
        seen.add(num)
    return sorted(pairs)

print(find_pairs([1, 5, 3, 7, 2, 8], 9))  # [(1, 8), (2, 7)]
print(find_pairs([1, 1, 1, 1], 2))         # [(1, 1)]
```

**Time:** O(n), **Space:** O(n). Using a set for pairs prevents duplicates when the same pair can be formed multiple ways.

---

### Problem 1.5 (Medium): Maximum Subarray Sum (Kadane's Algorithm)

Find the contiguous subarray with the maximum sum.

**Sample Input:** [-2, 1, -3, 4, -1, 2, 1, -5, 4]
**Sample Output:** 6 (subarray [4, -1, 2, 1])

```python
def max_subarray(arr):
    max_sum = current = arr[0]
    for num in arr[1:]:
        current = max(num, current + num)
        max_sum = max(max_sum, current)
    return max_sum

print(max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]))  # 6
print(max_subarray([-1, -2, -3]))                       # -1
```

**The Key Insight:** At each element, decide whether to extend the current subarray or start fresh from here. Starting fresh is better when the current running sum is negative because a negative prefix only reduces any new element added to it.

**Edge Case:** All negative array - Kadane's correctly returns the largest (least negative) single element, not 0.

---

### Problem 1.6 (Medium): Move All Zeroes to End

Move all zeros to the end while maintaining relative order of non-zero elements.

**Sample Input:** [0, 1, 0, 3, 12]
**Sample Output:** [1, 3, 12, 0, 0]

```python
def move_zeroes(arr):
    pos = 0
    for i in range(len(arr)):
        if arr[i] != 0:
            arr[pos] = arr[i]
            pos += 1
    for i in range(pos, len(arr)):
        arr[i] = 0
    return arr

print(move_zeroes([0, 1, 0, 3, 12]))  # [1, 3, 12, 0, 0]
print(move_zeroes([0, 0, 0, 1]))       # [1, 0, 0, 0]
```

---

### Problem 1.7 (Hard): Trapping Rainwater

Given heights of walls, calculate how much water can be trapped between them.

**Sample Input:** [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]
**Sample Output:** 6

```python
def trap_water(height):
    n = len(height)
    if n < 3:
        return 0
    left_max = [0] * n
    right_max = [0] * n
    left_max[0] = height[0]
    for i in range(1, n):
        left_max[i] = max(left_max[i-1], height[i])
    right_max[n-1] = height[n-1]
    for i in range(n-2, -1, -1):
        right_max[i] = max(right_max[i+1], height[i])
    water = 0
    for i in range(n):
        water += min(left_max[i], right_max[i]) - height[i]
    return water

print(trap_water([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]))  # 6
print(trap_water([4, 2, 0, 3, 2, 5]))                      # 9
```

**Logic:** Water at each position = min(max height to its left, max height to its right) minus its own height.

---

## Category 2: String Processing

---

### Problem 2.1 (Easy): Count Vowels and Consonants

```python
def count_vowels_consonants(s):
    s = s.lower()
    vowels = sum(1 for c in s if c in 'aeiou')
    consonants = sum(1 for c in s if c.isalpha() and c not in 'aeiou')
    return vowels, consonants

v, c = count_vowels_consonants("Hello World")
print(f"Vowels: {v}, Consonants: {c}")  # Vowels: 3, Consonants: 7
```

---

### Problem 2.2 (Easy): Reverse Words in a Sentence

```python
def reverse_words(sentence):
    return ' '.join(sentence.split()[::-1])

print(reverse_words("Hello World from Python"))
# "Python from World Hello"
print(reverse_words("  spaces   around  "))
# "around spaces" (split handles extra spaces)
```

---

### Problem 2.3 (Easy): Check Palindrome

```python
def is_palindrome(s):
    cleaned = ''.join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]

print(is_palindrome("racecar"))                    # True
print(is_palindrome("A man a plan a canal Panama")) # True
print(is_palindrome("hello"))                      # False
```

```java
public static boolean isPalindrome(String s) {
    int left = 0, right = s.length() - 1;
    while (left < right) {
        while (left < right && !Character.isLetterOrDigit(s.charAt(left))) left++;
        while (left < right && !Character.isLetterOrDigit(s.charAt(right))) right--;
        if (Character.toLowerCase(s.charAt(left)) !=
            Character.toLowerCase(s.charAt(right))) return false;
        left++; right--;
    }
    return true;
}
```

---

### Problem 2.4 (Medium): Check if Two Strings Are Anagrams

```python
def are_anagrams(s1, s2):
    s1 = s1.lower().replace(' ', '')
    s2 = s2.lower().replace(' ', '')
    if len(s1) != len(s2):
        return False
    from collections import Counter
    return Counter(s1) == Counter(s2)

print(are_anagrams("listen", "silent"))      # True
print(are_anagrams("triangle", "integral"))  # True
print(are_anagrams("hello", "world"))        # False
```

**Alternative using sorted:**
```python
def are_anagrams_v2(s1, s2):
    return sorted(s1.lower()) == sorted(s2.lower())
```

---

### Problem 2.5 (Medium): First Non-Repeating Character

```python
def first_non_repeating(s):
    count = {}
    for c in s:
        count[c] = count.get(c, 0) + 1
    for c in s:        # Preserve order by re-scanning original
        if count[c] == 1:
            return c
    return None

print(first_non_repeating("aabbcdeeff"))  # 'c'
print(first_non_repeating("aabb"))        # None
print(first_non_repeating("abcdef"))      # 'a'
```

---

### Problem 2.6 (Medium): Longest Substring Without Repeating Characters

```python
def longest_unique_substring(s):
    char_index = {}
    max_len = start = 0
    for i, c in enumerate(s):
        if c in char_index and char_index[c] >= start:
            start = char_index[c] + 1
        char_index[c] = i
        max_len = max(max_len, i - start + 1)
    return max_len

print(longest_unique_substring("abcabcbb"))  # 3 ("abc")
print(longest_unique_substring("bbbbb"))     # 1 ("b")
print(longest_unique_substring("pwwkew"))    # 3 ("wke")
print(longest_unique_substring(""))          # 0
```

**Sliding window:** The window [start, i] always contains unique characters. When a repeat is hit, slide start past the previous occurrence of that character.

---

### Problem 2.7 (Medium): Count and Say Sequence

The count-and-say sequence: 1, 11, 21, 1211, 111221... Each term describes the previous.

```python
def count_and_say(n):
    result = "1"
    for _ in range(n - 1):
        new_result = ""
        i = 0
        while i < len(result):
            count = 1
            while i + count < len(result) and result[i+count] == result[i]:
                count += 1
            new_result += str(count) + result[i]
            i += count
        result = new_result
    return result

for i in range(1, 7):
    print(f"n={i}: {count_and_say(i)}")
# n=1: 1   n=2: 11   n=3: 21   n=4: 1211   n=5: 111221   n=6: 312211
```

---

### Problem 2.8 (Medium): String Compression (Run-Length Encoding)

Compress "aaabbbccddddee" to "a3b3c2d4e2".

```python
def compress_string(s):
    if not s:
        return ""
    result = []
    count = 1
    for i in range(1, len(s)):
        if s[i] == s[i-1]:
            count += 1
        else:
            result.append(s[i-1] + (str(count) if count > 1 else ''))
            count = 1
    result.append(s[-1] + (str(count) if count > 1 else ''))
    compressed = ''.join(result)
    return compressed if len(compressed) < len(s) else s

print(compress_string("aaabbbccddddee"))  # a3b3c2d4e2
print(compress_string("abcd"))            # abcd (no benefit)
print(compress_string("aaa"))             # a3
```

---

## Category 3: Pattern Printing

Pattern printing is nearly guaranteed to appear in the Infosys assessment, typically as the easier of the two coding problems. Mastering these patterns is one of the highest-value preparation investments given the certainty of their appearance.

---

### Problem 3.1: Right-Angled Triangle

```
*
**
***
****
*****
```

```python
def right_triangle(n):
    for i in range(1, n+1):
        print('*' * i)

right_triangle(5)
```

---

### Problem 3.2: Inverted Triangle

```
*****
****
***
**
*
```

```python
def inverted_triangle(n):
    for i in range(n, 0, -1):
        print('*' * i)
```

---

### Problem 3.3: Centered Pyramid

```
    *
   ***
  *****
 *******
*********
```

```python
def pyramid(n):
    for i in range(1, n+1):
        print(' ' * (n-i) + '*' * (2*i-1))

pyramid(5)
```

---

### Problem 3.4: Diamond Pattern

```
    *
   ***
  *****
 *******
*********
 *******
  *****
   ***
    *
```

```python
def diamond(n):
    for i in range(1, n+1):
        print(' ' * (n-i) + '*' * (2*i-1))
    for i in range(n-1, 0, -1):
        print(' ' * (n-i) + '*' * (2*i-1))

diamond(5)
```

---

### Problem 3.5: Number Triangle

```
1
12
123
1234
12345
```

```python
def number_triangle(n):
    for i in range(1, n+1):
        print(''.join(str(j) for j in range(1, i+1)))
```

---

### Problem 3.6: Floyd's Triangle

```
1
2 3
4 5 6
7 8 9 10
```

```python
def floyds_triangle(n):
    num = 1
    for i in range(1, n+1):
        row = []
        for j in range(i):
            row.append(str(num))
            num += 1
        print(' '.join(row))

floyds_triangle(4)
```

---

### Problem 3.7: Hollow Square

```
*****
*   *
*   *
*   *
*****
```

```python
def hollow_square(n):
    for i in range(n):
        if i == 0 or i == n-1:
            print('*' * n)
        else:
            print('*' + ' ' * (n-2) + '*')

hollow_square(5)
```

---

### Problem 3.8: Pascal's Triangle

```
1
1 1
1 2 1
1 3 3 1
1 4 6 4 1
```

```python
def pascals_triangle(n):
    row = [1]
    for i in range(n):
        print(' '.join(map(str, row)))
        row = [1] + [row[j]+row[j+1] for j in range(len(row)-1)] + [1]

pascals_triangle(5)
```

---

### Problem 3.9: Spiral Matrix

Print an N×N matrix filled in spiral order.

```python
def spiral_matrix(n):
    matrix = [[0]*n for _ in range(n)]
    top, bottom, left, right = 0, n-1, 0, n-1
    num = 1
    while top <= bottom and left <= right:
        for i in range(left, right+1):
            matrix[top][i] = num; num += 1
        top += 1
        for i in range(top, bottom+1):
            matrix[i][right] = num; num += 1
        right -= 1
        if top <= bottom:
            for i in range(right, left-1, -1):
                matrix[bottom][i] = num; num += 1
            bottom -= 1
        if left <= right:
            for i in range(bottom, top-1, -1):
                matrix[i][left] = num; num += 1
            left += 1
    for row in matrix:
        print(' '.join(f'{x:3}' for x in row))

spiral_matrix(4)
```

**Output for n=4:**
```
  1  2  3  4
 12 13 14  5
 11 16 15  6
 10  9  8  7
```

---

## Category 4: Mathematical and Number Theory

---

### Problem 4.1 (Easy): Check Prime Number

```python
def is_prime(n):
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    for i in range(3, int(n**0.5)+1, 2):
        if n % i == 0:
            return False
    return True

primes = [x for x in range(2, 50) if is_prime(x)]
print(primes)
# [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
```

**Why sqrt(n):** If n has a factor greater than √n, its paired factor is smaller than √n and would already have been found. Checking only up to √n is sufficient.

---

### Problem 4.2 (Easy): Fibonacci Sequence

```python
# Iterative - preferred for performance
def fibonacci(n):
    if n <= 0: return []
    if n == 1: return [0]
    seq = [0, 1]
    for _ in range(2, n):
        seq.append(seq[-1] + seq[-2])
    return seq[:n]

print(fibonacci(10))  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

# Nth term only, O(1) space
def nth_fibonacci(n):
    if n <= 0: return 0
    a, b = 0, 1
    for _ in range(n-1):
        a, b = b, a+b
    return a

print(nth_fibonacci(10))  # 34
```

---

### Problem 4.3 (Easy): Digit Sum and Digital Root

```python
def digit_sum(n):
    return sum(int(d) for d in str(abs(n)))

def digital_root(n):
    n = abs(n)
    while n >= 10:
        n = digit_sum(n)
    return n

print(digit_sum(12345))    # 15
print(digital_root(9875))  # 2  (9+8+7+5=29, 2+9=11, 1+1=2)
print(digital_root(0))     # 0
```

---

### Problem 4.4 (Medium): GCD and LCM

```python
def gcd(a, b):
    while b:
        a, b = b, a % b
    return abs(a)

def lcm(a, b):
    return abs(a * b) // gcd(a, b)

def gcd_array(arr):
    from functools import reduce
    return reduce(gcd, arr)

print(gcd(48, 18))              # 6
print(lcm(12, 18))              # 36
print(gcd_array([12, 24, 36]))  # 12
```

---

### Problem 4.5 (Medium): Armstrong Number

A number is Armstrong if the sum of its digits each raised to the power of the number of digits equals the number. 153 = 1³+5³+3³ = 153.

```python
def is_armstrong(n):
    digits = str(abs(n))
    power = len(digits)
    return sum(int(d)**power for d in digits) == abs(n)

armstrong_list = [n for n in range(1, 10000) if is_armstrong(n)]
print(armstrong_list)
# [1, 2, 3, 4, 5, 6, 7, 8, 9, 153, 370, 371, 407, 1634, 8208, 9474]
```

---

### Problem 4.6 (Medium): Prime Factorization

```python
def prime_factors(n):
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors

print(prime_factors(360))  # [2, 2, 2, 3, 3, 5]
print(prime_factors(97))   # [97]
print(prime_factors(1))    # []
```

---

### Problem 4.7 (Medium): Perfect Number

A perfect number equals the sum of its proper divisors. 28 = 1+2+4+7+14.

```python
def is_perfect(n):
    if n < 2: return False
    div_sum = 1
    i = 2
    while i * i <= n:
        if n % i == 0:
            div_sum += i
            if i != n // i:
                div_sum += n // i
        i += 1
    return div_sum == n

perfects = [n for n in range(1, 10000) if is_perfect(n)]
print(perfects)  # [6, 28, 496, 8128]
```

---

## Category 5: Searching and Sorting

---

### Problem 5.1 (Easy): Binary Search

```python
def binary_search(arr, target):
    left, right = 0, len(arr)-1
    while left <= right:
        mid = left + (right - left) // 2   # Overflow-safe
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

arr = [1, 3, 5, 7, 9, 11, 13, 15]
print(binary_search(arr, 7))   # 3
print(binary_search(arr, 6))   # -1
print(binary_search(arr, 15))  # 7
```

**Common mistake:** Using `(left+right)//2`. In Python integers don't overflow, but in Java/C++ `left+right` can overflow int. Always use `left + (right-left)//2`.

---

### Problem 5.2 (Medium): Bubble Sort with Optimization

```python
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
                swapped = True
        if not swapped:   # Already sorted - early exit
            break
    return arr

print(bubble_sort([64, 34, 25, 12, 22, 11, 90]))
# [11, 12, 22, 25, 34, 64, 90]
```

---

### Problem 5.3 (Medium): Merge Sort

```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    return result + left[i:] + right[j:]

print(merge_sort([38, 27, 43, 3, 9, 82, 10]))
# [3, 9, 10, 27, 38, 43, 82]
```

**Time:** O(n log n) guaranteed. **Space:** O(n). Merge sort is stable.

---

### Problem 5.4 (Medium): Kth Largest Element

```python
def kth_largest(arr, k):
    # Simple approach: sort descending, return index k-1
    return sorted(arr, reverse=True)[k-1]

# Efficient approach using heap
def kth_largest_heap(arr, k):
    import heapq
    return heapq.nlargest(k, arr)[-1]

print(kth_largest([3, 2, 1, 5, 6, 4], 2))          # 5
print(kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4)) # 4
```

---

## Category 6: Recursion and Dynamic Programming

---

### Problem 6.1 (Easy): Factorial

```python
def factorial(n):
    if n < 0:
        raise ValueError("Negative input")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n-1)

# Iterative (avoids stack overflow for large n)
def factorial_iter(n):
    result = 1
    for i in range(2, n+1):
        result *= i
    return result

print(factorial(10))       # 3628800
print(factorial_iter(15))  # 1307674368000
```

---

### Problem 6.2 (Medium): Fast Power (Exponentiation by Squaring)

Compute x^n efficiently without the built-in power function.

```python
def power(x, n):
    if n == 0: return 1
    if n < 0: return 1 / power(x, -n)
    if n % 2 == 0:
        half = power(x, n//2)
        return half * half
    return x * power(x, n-1)

print(power(2, 10))   # 1024
print(power(2, -3))   # 0.125
print(power(3, 5))    # 243
```

**Why squaring is efficient:** Each recursive call halves n, giving O(log n) time instead of O(n) for naive repeated multiplication.

---

### Problem 6.3 (Medium): Coin Change (Minimum Coins)

Given coin denominations and a target amount, find the minimum number of coins needed.

```python
def min_coins(coins, amount):
    dp = [float('inf')] * (amount+1)
    dp[0] = 0
    for coin in coins:
        for amt in range(coin, amount+1):
            dp[amt] = min(dp[amt], dp[amt-coin] + 1)
    return dp[amount] if dp[amount] != float('inf') else -1

print(min_coins([1, 5, 6, 9], 11))  # 2 (5+6)
print(min_coins([2], 3))            # -1 (impossible)
print(min_coins([1, 2, 5], 11))     # 3 (5+5+1)
```

---

### Problem 6.4 (Medium): Longest Common Subsequence

Find the length of the longest subsequence present in both strings.

```python
def lcs(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]

print(lcs("ABCBDAB", "BDCAB"))   # 4 (BCAB or BDAB)
print(lcs("AGGTAB", "GXTXAYB")) # 4 (GTAB)
print(lcs("", "ABC"))            # 0
```

---

### Problem 6.5 (Medium): 0/1 Knapsack

Given items with weights and values and a capacity W, find the maximum value achievable without exceeding capacity.

```python
def knapsack(weights, values, W):
    n = len(weights)
    dp = [[0]*(W+1) for _ in range(n+1)]
    for i in range(1, n+1):
        for w in range(W+1):
            dp[i][w] = dp[i-1][w]
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w],
                               dp[i-1][w-weights[i-1]] + values[i-1])
    return dp[n][W]

weights = [1, 3, 4, 5]
values  = [1, 4, 5, 7]
W = 7
print(knapsack(weights, values, W))  # 9 (items w=3,v=4 + w=4,v=5)
```

---

### Problem 6.6 (Hard): Longest Increasing Subsequence

Find the length of the longest strictly increasing subsequence.

```python
def lis(arr):
    if not arr: return 0
    n = len(arr)
    dp = [1] * n
    for i in range(1, n):
        for j in range(i):
            if arr[j] < arr[i]:
                dp[i] = max(dp[i], dp[j]+1)
    return max(dp)

print(lis([10, 9, 2, 5, 3, 7, 101, 18]))  # 4 ([2,3,7,101])
print(lis([0, 1, 0, 3, 2, 3]))             # 4 ([0,1,2,3])
print(lis([7, 7, 7, 7]))                   # 1
```

---

## Category 7: Pseudocode Tracing Questions

Pseudocode questions require no coding: you read language-agnostic pseudocode and determine the output mentally. The skill is code comprehension, not implementation.

**Strategy:** Work through the trace line by line, writing down variable values as they change. Do not try to hold the entire state in memory.

---

### Pseudocode Q1: Simple While Loop

```
x = 5
y = 10
WHILE x < y:
    x = x + 2
    y = y - 1
PRINT x, y
```

**Trace:**
- Start: x=5, y=10
- Iteration 1 (5<10 ✓): x=7, y=9
- Iteration 2 (7<9 ✓): x=9, y=8
- Iteration 3 (9<8 ✗): EXIT
- **Output: 9 8**

---

### Pseudocode Q2: Recursive Function

```
FUNCTION mystery(n):
    IF n <= 0: RETURN 0
    RETURN n + mystery(n - 2)

PRINT mystery(6)
```

**Trace:**
- mystery(6) = 6 + mystery(4)
- mystery(4) = 4 + mystery(2)
- mystery(2) = 2 + mystery(0)
- mystery(0) = 0
- Unwinding: mystery(2)=2, mystery(4)=6, mystery(6)=12
- **Output: 12**

---

### Pseudocode Q3: Array Index Maximum

```
arr = [3, 1, 4, 1, 5, 9, 2, 6]
result = 0
FOR i FROM 0 TO length(arr)-1:
    IF arr[i] > arr[result]:
        result = i
PRINT result
```

**Trace:** Tracks the index of the current maximum.
- i=0: arr[0]=3, result=0 (initial)
- i=1: 1>3? No
- i=2: 4>3? Yes → result=2
- i=3: 1>4? No
- i=4: 5>4? Yes → result=4
- i=5: 9>5? Yes → result=5
- i=6: 2>9? No
- i=7: 6>9? No
- **Output: 5** (index of element 9)

---

### Pseudocode Q4: Euclid's Algorithm

```
FUNCTION compute(a, b):
    IF b == 0: RETURN a
    RETURN compute(b, a MOD b)

PRINT compute(48, 18)
```

**Trace:**
- compute(48, 18) → compute(18, 48%18=12)
- compute(18, 12) → compute(12, 18%12=6)
- compute(12, 6)  → compute(6, 12%6=0)
- compute(6, 0)   → RETURN 6
- **Output: 6** (This is GCD)

---

### Pseudocode Q5: Array Swap Trace

```
arr = [1, 2, 3, 4, 5]
FOR i FROM 0 TO 2:
    SWAP arr[i] AND arr[4-i]
PRINT arr
```

**Trace:**
- i=0: swap arr[0] and arr[4]: [5,2,3,4,1]
- i=1: swap arr[1] and arr[3]: [5,4,3,2,1]
- i=2: swap arr[2] and arr[2]: [5,4,3,2,1] (self-swap, no change)
- **Output: [5, 4, 3, 2, 1]**

---

### Pseudocode Q6: Mixed Conditional Loop

```
x = 1
WHILE x <= 5:
    IF x MOD 2 == 0:
        PRINT x * x
    ELSE:
        PRINT x + 1
    x = x + 1
```

**Trace:**
- x=1: odd → print 1+1=**2**
- x=2: even → print 2*2=**4**
- x=3: odd → print 3+1=**4**
- x=4: even → print 4*4=**16**
- x=5: odd → print 5+1=**6**
- x=6: 6>5, exit
- **Output: 2 4 4 16 6**

---

### Pseudocode Q7: Case Toggle

```
FUNCTION transform(s):
    result = ""
    FOR i FROM 0 TO length(s)-1:
        IF s[i] IS UPPERCASE:
            result = result + LOWERCASE(s[i])
        ELSE:
            result = result + UPPERCASE(s[i])
    RETURN result

PRINT transform("HeLLo WoRLD")
```

**Trace:** Toggle each character's case.
- H→h, e→E, L→l, L→l, o→O, ' '→' ', W→w, o→O, R→r, L→l, D→d
- **Output: "hEllO wOrld"**

---

## Full Mock Coding Test

This mock test matches the Infosys assessment format exactly: 2 problems, attempt under a strict 30-minute timer before reading solutions.

---

### Mock Problem 1 (Easy-Medium): Number to Words

Convert a number from 0 to 999 to its English word representation.

**Sample:**
- Input: 256
- Output: "Two Hundred Fifty Six"
- Input: 45 → "Forty Five"
- Input: 100 → "One Hundred"
- Input: 0 → "Zero"

```python
def number_to_words(n):
    if n == 0:
        return "Zero"

    ones = ["", "One", "Two", "Three", "Four", "Five", "Six",
            "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve",
            "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    tens_words = ["", "", "Twenty", "Thirty", "Forty", "Fifty",
                  "Sixty", "Seventy", "Eighty", "Ninety"]

    parts = []
    if n >= 100:
        parts.append(ones[n // 100] + " Hundred")
        n %= 100
    if n >= 20:
        t = tens_words[n // 10]
        o = ones[n % 10]
        parts.append((t + " " + o).strip() if o else t)
    elif n > 0:
        parts.append(ones[n])

    return " ".join(parts)

test_cases = [0, 5, 11, 19, 20, 45, 100, 115, 256, 999]
for num in test_cases:
    print(f"{num:4}: {number_to_words(num)}")
```

**Critical edge cases:**
- Teen numbers (11-19): these have unique words, not "Ten One" or "One Teen".
- Multiples of 100 with no remainder: "One Hundred", not "One Hundred Zero".
- 0: "Zero", not "".

---

### Mock Problem 2 (Medium): Valid Parentheses

Given a string of brackets, determine if they are correctly balanced.

**Sample:**
- Input: "()[]{}" → True
- Input: "([)]" → False
- Input: "{[]}" → True
- Input: "" → True

```python
def is_valid(s):
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for c in s:
        if c in '([{':
            stack.append(c)
        elif c in ')]}':
            if not stack or stack[-1] != pairs[c]:
                return False
            stack.pop()
    return len(stack) == 0

test_cases = ["()[]{}", "([)]", "{[]}", "", "(]", "((()))"]
for tc in test_cases:
    print(f'"{tc}" → {is_valid(tc)}')
```

**Why a stack:** The most recently opened bracket must be closed first. A stack's LIFO property models this exactly.

**Edge cases:**
- Empty string: returns True (vacuously valid).
- String with only opening brackets "(((" : stack is non-empty → False.
- String starting with closing bracket "]abc": stack is empty when ']' is encountered → False.

---

### Mock Problem 3 (Alternative): Matrix Rotation 90 Degrees Clockwise

Rotate a square matrix 90 degrees clockwise in-place.

```
Input:        Output:
1 2 3         7 4 1
4 5 6    →    8 5 2
7 8 9         9 6 3
```

```python
def rotate_matrix(matrix):
    n = len(matrix)
    # Step 1: Transpose (rows become columns)
    for i in range(n):
        for j in range(i+1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    # Step 2: Reverse each row
    for i in range(n):
        matrix[i].reverse()
    return matrix

mat = [[1,2,3],[4,5,6],[7,8,9]]
result = rotate_matrix(mat)
for row in result:
    print(row)
# [7, 4, 1]
# [8, 5, 2]
# [9, 6, 3]
```

**The transpose-then-reverse trick:** Transposing swaps rows and columns. Reversing each row after that achieves the clockwise rotation. Two simple operations achieve what seems complex.

---

## Language Tips: Python vs Java vs C++

**Python Strengths for Coding Rounds:**

```python
a, b = b, a                      # Swap without temp
arr[::-1]                        # Reverse a list
sorted(arr, key=lambda x: -x)    # Sort descending
Counter(arr)                     # Frequency count in one call
all(x > 0 for x in arr)          # Check all elements
any(x < 0 for x in arr)          # Check any element
arr[-k:] + arr[:-k]              # Rotate right by k
```

**Python Pitfalls:**
- Slower execution than Java/C++ for large inputs (may TLE on very large n).
- Default recursion limit is 1000. Use `sys.setrecursionlimit(10000)` for deep recursion.
- Mutable default arguments in functions create bugs: use `def f(memo=None): if memo is None: memo = {}`.

**Java Strengths for Infosys:**
```java
Arrays.sort(arr);                                    // Sort array
Collections.sort(list, Collections.reverseOrder());  // Sort descending
StringBuilder sb = new StringBuilder();              // Efficient string building
sb.append("text"); String r = sb.toString();
int mid = left + (right - left) / 2;               // Overflow-safe midpoint
Map<Character, Integer> freq = new HashMap<>();     // Frequency map
freq.put(c, freq.getOrDefault(c, 0) + 1);
```

**Java Pitfalls:**
- String concatenation in a loop is O(n²). Always use StringBuilder.
- Integer overflow is real: use `long` for large computations.
- `int[]` is zero-initialized; `boolean[]` is false-initialized. This is useful and can replace explicit initialization.

**C++ When to Use:**
Use C++ when you are already fluent in it and the problem involves tight time limits or requires STL data structures (priority_queue for Dijkstra, map/set for ordered structures, unordered_map for O(1) lookup).

---

## The 4-Week Preparation Plan

**Week 1: Foundation Problems**

Target: solve any Easy problem in under 15 minutes.

Daily: 3 Easy problems from the categories in this guide. Focus first on arrays and strings because they appear most frequently.

Pattern mastery goals for week 1:
- Second largest, rotate array, count even/odd, pairs with sum
- Reverse words, palindrome check, vowel count
- All pattern printing variations (right triangle through diamond)

Session structure: 20 minutes solving independently, then review the solution in this guide, then re-solve without looking.

**Week 2: Core Algorithm Patterns**

Target: solve Easy-Medium problems within 20 minutes.

Daily: 2 Easy + 1 Medium. Focus on the three patterns that solve 80% of Easy-Medium problems: frequency counting with a dictionary, the two-pointer technique, and the sliding window.

Pseudocode practice: 30 minutes per day. Trace 5 pseudocode questions without running any code. The discipline of tracing on paper trains the skill being tested.

Algorithm understanding goals:
- Understand Kadane's algorithm intuitively (not just code-memory)
- Understand binary search and be able to implement from scratch
- Understand merge sort's divide-and-conquer logic

**Week 3: Medium Problems and DP**

Target: solve Medium problems in 25-30 minutes.

Daily: 2 Medium problems. Focus on dynamic programming patterns: coin change, LCS, LIS, knapsack. These are the DP problems that appear at Infosys.

DP approach discipline: for every DP problem, define the state first ("dp[i] represents..."), the transition ("dp[i] = ..."), the base case, and the answer ("return dp[n]"). Coding before defining the state produces wrong solutions consistently.

**Week 4: Mock Tests and Time Management**

Target: complete the full 30-minute mock test format reliably.

Daily: one complete mock test under strict timed conditions. Two problems, 30-minute timer, no pausing.

Review discipline: after each mock, categorize every error: wrong algorithm, wrong edge case handling, syntax error, time management failure. Different errors need different remediations.

Final week goals:
- Complete all pattern printing problems without reference in under 5 minutes each
- Trace any pseudocode trace in this guide accurately before looking at the answer
- Have internalized the "read both problems first, solve easier first, partial before empty" strategy

---

## Frequently Asked Questions

**1. How many coding questions appear in the Infosys assessment?**

Standard SE track: 2 coding problems in 30 minutes. DSE track: 2-3 problems in 45 minutes. The pseudocode section (when included) is separate: typically 5 questions in 10 minutes.

**2. What languages are supported?**

Typically C, C++, Java, and Python. The available languages are shown at the start of the coding section. Verify before starting.

**3. Is there a compiler available during the assessment?**

Yes. The platform provides an online editor where you can write, compile, and run code against the provided sample test cases before final submission. Hidden test cases are not visible.

**4. What happens if my solution only passes some test cases?**

Some assessments award partial credit per test case; others are all-or-nothing. Always aim for a complete correct solution, but submit a partial solution rather than leaving it blank if you run out of time.

**5. Are pattern printing questions always included?**

Pattern printing appears in the vast majority of Infosys coding assessments as one of the two problems. It is almost always the easier of the two. Not mastering patterns is a preventable reason to lose guaranteed marks.

**6. What difficulty level are the problems?**

SE track: Easy and Easy-Medium by LeetCode standards. One problem is typically straightforward (pattern printing or simple array operation) and one requires a specific algorithm or technique. DSE track: Medium and Hard.

**7. How important is time complexity?**

For Easy problems with small inputs (n≤1000), O(n²) typically passes. For Medium problems, O(n log n) or O(n) is usually needed. Read the constraints in the problem statement before deciding on an approach.

**8. What is the most common reason solutions fail on hidden test cases?**

Unhandled edge cases: empty array/string, single element, all identical elements, negative numbers (where applicable), k=0 in rotation problems, target not achievable in sum problems. Test against these before submitting.

**9. Should I memorize solutions or understand patterns?**

Understand patterns. Infosys does not reuse questions verbatim; they vary the parameters and constraints. A candidate who understands Kadane's algorithm can solve any maximum subarray variant; one who memorized a specific solution cannot.

**10. What is the pseudocode section like?**

Five questions, each presenting 5-15 lines of pseudocode with a specific output to determine. No coding required. The questions test: loop tracing, recursive call unwinding, array index tracking, and conditional logic following. Practice specifically by tracing on paper without running code.

**11. How do I handle a problem where I know the brute force but not the optimal solution?**

Implement the brute force first. A correct brute force that passes all test cases scores full marks. An incomplete or buggy "optimal" solution scores zero. Optimize only if time permits after the brute force is submitted and working.

**12. Can I use built-in sorting in the coding section?**

Yes. You are not required to implement sorting from scratch unless the question specifically asks for a sort implementation. Using `sorted()` in Python or `Arrays.sort()` in Java is completely acceptable.

**13. What about the difficulty of pattern printing problems specifically?**

The pattern printing problems in Infosys assessments range from simple triangles (5 minutes) to hollow diamonds and number patterns (10-15 minutes). The formula for every pattern is: determine the number of spaces, the number of stars/numbers, and whether the character should be printed or a space should be printed based on position. Every pattern follows from this three-part analysis.

**14. How do I prepare for pseudocode questions specifically?**

Practice tracing code in your head (or on paper) without running it. Work through the pseudocode questions in this guide without checking the answer, then verify. The discipline of tracing one line at a time and writing down each variable's value is the skill. It cannot be developed by reading; it requires active practice.

**15. Is the coding section score released along with the aptitude score?**

Candidates typically receive an overall score rather than section-level scores. Infosys uses the overall online assessment score as the primary filter for the interview stage. Strong performance in coding compensates for moderate aptitude performance and vice versa, but excellence in both is needed for highly competitive positions.

---

## Advanced Array Problems: Building on the Fundamentals

The seven array problems above cover the core patterns. The following problems extend into territory that appears in DSE-track assessments and in the harder of the two SE problems.

---

### Problem A1: Dutch National Flag (Sort 0s, 1s, 2s)

Sort an array containing only 0, 1, and 2 without using a sorting function.

**Sample Input:** [2, 0, 2, 1, 1, 0]
**Sample Output:** [0, 0, 1, 1, 2, 2]

```python
def sort_colors(arr):
    low, mid, high = 0, 0, len(arr)-1
    while mid <= high:
        if arr[mid] == 0:
            arr[low], arr[mid] = arr[mid], arr[low]
            low += 1; mid += 1
        elif arr[mid] == 1:
            mid += 1
        else:
            arr[mid], arr[high] = arr[high], arr[mid]
            high -= 1
    return arr

print(sort_colors([2, 0, 2, 1, 1, 0]))  # [0, 0, 1, 1, 2, 2]
print(sort_colors([0]))                  # [0]
print(sort_colors([2, 2, 0, 0]))         # [0, 0, 2, 2]
```

**Time:** O(n), **Space:** O(1). The three-pointer approach partitions the array into three regions in a single pass.

---

### Problem A2: Maximum Product Subarray

Find the contiguous subarray with the maximum product.

**Sample Input:** [2, 3, -2, 4]
**Sample Output:** 6 (subarray [2, 3])

```python
def max_product(arr):
    max_prod = min_prod = result = arr[0]
    for num in arr[1:]:
        candidates = (num, max_prod * num, min_prod * num)
        max_prod = max(candidates)
        min_prod = min(candidates)
        result = max(result, max_prod)
    return result

print(max_product([2, 3, -2, 4]))    # 6
print(max_product([-2, 0, -1]))      # 0
print(max_product([-2, 3, -4]))      # 24
```

**Why track minimum:** A negative minimum times a negative number becomes the new maximum. Both must be tracked.

---

### Problem A3: Merge Intervals

Given a list of intervals, merge all overlapping ones.

**Sample Input:** [[1,3],[2,6],[8,10],[15,18]]
**Sample Output:** [[1,6],[8,10],[15,18]]

```python
def merge_intervals(intervals):
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged

print(merge_intervals([[1,3],[2,6],[8,10],[15,18]]))
# [[1, 6], [8, 10], [15, 18]]
print(merge_intervals([[1,4],[4,5]]))
# [[1, 5]] (touching counts as overlapping)
```

---

### Problem A4: Find Majority Element

Find the element that appears more than n/2 times. Guaranteed to exist.

```python
def majority_element(arr):
    # Boyer-Moore Voting Algorithm
    candidate, count = arr[0], 1
    for num in arr[1:]:
        if count == 0:
            candidate = num
            count = 1
        elif num == candidate:
            count += 1
        else:
            count -= 1
    return candidate

print(majority_element([3, 2, 3]))        # 3
print(majority_element([2,2,1,1,1,2,2]))  # 2
```

**Why this works:** The majority element cannot be fully cancelled out because it appears more than n/2 times. The final candidate is always the majority.

---

### Problem A5: Two Sum with Sorted Array (Two Pointers)

Given a sorted array and target, find indices of two numbers that sum to target.

```python
def two_sum_sorted(arr, target):
    left, right = 0, len(arr)-1
    while left < right:
        current_sum = arr[left] + arr[right]
        if current_sum == target:
            return [left+1, right+1]  # 1-indexed
        elif current_sum < target:
            left += 1
        else:
            right -= 1
    return []

print(two_sum_sorted([2, 7, 11, 15], 9))   # [1, 2]
print(two_sum_sorted([2, 3, 4], 6))         # [1, 3]
print(two_sum_sorted([-1, 0], -1))          # [1, 2]
```

---

## Advanced String Problems

---

### Problem S1: Longest Palindromic Substring

Find the longest substring that is a palindrome.

```python
def longest_palindrome(s):
    if not s:
        return ""
    start = end = 0

    def expand(left, right):
        while left >= 0 and right < len(s) and s[left] == s[right]:
            left -= 1
            right += 1
        return left+1, right-1

    for i in range(len(s)):
        # Odd length palindromes
        l, r = expand(i, i)
        if r - l > end - start:
            start, end = l, r
        # Even length palindromes
        l, r = expand(i, i+1)
        if r - l > end - start:
            start, end = l, r

    return s[start:end+1]

print(longest_palindrome("babad"))    # "bab" or "aba"
print(longest_palindrome("cbbd"))     # "bb"
print(longest_palindrome("racecar"))  # "racecar"
```

---

### Problem S2: Group Anagrams

Group strings that are anagrams of each other.

```python
def group_anagrams(strs):
    from collections import defaultdict
    groups = defaultdict(list)
    for s in strs:
        key = tuple(sorted(s))
        groups[key].append(s)
    return list(groups.values())

words = ["eat","tea","tan","ate","nat","bat"]
print(group_anagrams(words))
# [['eat','tea','ate'], ['tan','nat'], ['bat']]
```

---

### Problem S3: Minimum Window Substring

Find the minimum length substring of s that contains all characters of t.

```python
def min_window(s, t):
    from collections import Counter
    need = Counter(t)
    missing = len(t)
    start = best_start = 0
    best_len = float('inf')
    j = 0
    for i, c in enumerate(s):
        if need[c] > 0:
            missing -= 1
        need[c] -= 1
        if missing == 0:
            while need[s[j]] < 0:
                need[s[j]] += 1
                j += 1
            window_len = i - j + 1
            if window_len < best_len:
                best_len = window_len
                best_start = j
            need[s[j]] += 1
            missing += 1
            j += 1
    return "" if best_len == float('inf') else s[best_start:best_start+best_len]

print(min_window("ADOBECODEBANC", "ABC"))  # "BANC"
print(min_window("a", "a"))                # "a"
print(min_window("a", "b"))                # ""
```

---

## Practical Coding Tips for the Infosys Assessment

**Reading the Problem Statement Thoroughly:**

Every word in the problem statement matters. "Return -1 if not found" versus "return 0 if not found" is a one-character difference that changes the output for the edge case. "1-indexed output" versus "0-indexed" is a difference that makes every answer wrong. Read the entire problem, including constraints and output format, before writing a single line of code.

**Using Comments to Think:**

In a coding interview or assessment, writing pseudocode comments before implementation is a discipline that reduces bugs. For a binary search implementation:
```python
def binary_search(arr, target):
    # Two pointers, converge toward middle
    left, right = 0, len(arr)-1
    while left <= right:
        # Use overflow-safe midpoint
        mid = left + (right - left) // 2
        # Check mid first
        if arr[mid] == target:
            return mid
        # Move left pointer if target is in right half
        elif arr[mid] < target:
            left = mid + 1
        # Move right pointer if target is in left half
        else:
            right = mid - 1
    # Not found
    return -1
```

Writing the intent in comments before the code forces clarity on what each line does and catches logical errors before they are coded.

**Testing Against Sample Cases First:**

Before testing edge cases, always verify your solution against the provided sample input and output. If the sample fails, the logic is fundamentally wrong and needs to be fixed before worrying about edge cases.

**The Partial Solution Strategy:**

If you cannot solve the problem completely in the available time, submit a solution that handles the sample cases correctly. In many assessment configurations this scores partial marks. An empty submission always scores zero.

---

## Common Infosys Coding Patterns: Recognition Guide

Understanding which pattern applies to which problem type is what separates candidates who solve problems quickly from those who restart from scratch each time.

**Pattern: Frequency Map**
Trigger words: count occurrences, find duplicates, first unique, most frequent, anagram check.
Implementation: `count = {}; count[x] = count.get(x, 0) + 1`

**Pattern: Two Pointers**
Trigger words: sorted array, pairs with sum, remove duplicates, move elements to end.
Implementation: `left, right = 0, len-1; while left < right: ...`

**Pattern: Sliding Window**
Trigger words: longest/shortest substring with property, subarray of size k, maximum in window.
Implementation: `start = 0; for end in range(len): ...; if window invalid: start += 1`

**Pattern: Prefix Sum**
Trigger words: range sum queries, subarray sum equals k, cumulative counts.
Implementation: `prefix = [0]; for x in arr: prefix.append(prefix[-1] + x)`

**Pattern: Stack**
Trigger words: matching brackets, next greater element, evaluate expression, valid sequence.
Implementation: `stack = []; push on open, pop and check on close`

**Pattern: Recursion/Divide and Conquer**
Trigger words: split into two halves, sort recursively, find in sorted, tree traversal.
Implementation: `if base_case: return; left = solve(left_half); right = solve(right_half); return combine(left, right)`

**Pattern: Dynamic Programming**
Trigger words: minimum/maximum number of operations, count distinct ways, optimal subsequence, whether achievable.
State definition: what does dp[i] or dp[i][j] represent?
Transition: how does dp[i] relate to dp[i-1] or earlier states?

Recognizing the pattern from the trigger words is the first step. Once the pattern is identified, the implementation follows from the template.

---

## The 30-Minute Coding Session: A Minute-by-Minute Walkthrough

Understanding how the 30 minutes should be spent prevents the most common time management failure (spending too long on one problem and running out of time for the other).

**Minutes 0-2: Problem Reading**
Read both problems completely. Do not start coding. During this reading, identify: which problem is easier, what the input format is, what constraints exist (array size, value range), what edge cases the problem hints at.

**Minutes 2-3: Algorithm Selection**
For the easier problem, identify the pattern (see Pattern Recognition Guide above). For the harder problem, note the approach you would take if you had time. If you cannot identify the approach for the harder problem immediately, that is fine - your primary focus is the easier problem.

**Minutes 3-18: Solve the Easy Problem**
Write the solution. Test against sample input. Check edge cases (empty, single element, all same, boundary values). If it passes all checks, submit.

**Minutes 18-20: Start the Hard Problem**
Read the harder problem again carefully with the time remaining in mind. If you have 10 minutes, can you write a correct brute force?

**Minutes 20-28: Attempt the Hard Problem**
Write whatever correct solution you can. Even if it is O(n²) when O(n) is possible, a correct solution beats a blank submission. Submit.

**Minutes 28-30: Review Both Submissions**
If both are submitted and you have time remaining, review the edge cases on the easier submission one more time. Running out of time with both submitted is the ideal scenario; running out of time with only one submitted is a time management failure.

---

## InsightCrunch Infosys Series: Related Articles

This guide is Article 24 of the InsightCrunch Infosys Series. Related articles that complement this coding guide:

The [Infosys Aptitude Questions](https://insightcrunch.com/2021/09/07/infosys-aptitude-questions-answers/) guide (Article 11) covers the quantitative and logical reasoning sections of the same online assessment in the same format: complete questions with solutions and strategy.

The [Infosys Technical Interview](https://insightcrunch.com/2021/08/22/infosys-technical-interview-questions/) Questions guide (Article 12) covers the questions asked in the technical interview that follows the online assessment: OOP, Java, DBMS, OS, and networking.

The [HackWithInfy Preparation](https://insightcrunch.com/2021/10/01/hackwithinfy-preparation/) guide (Article 9) covers competitive programming preparation for the DSE/SP/PP tracks at significantly higher difficulty than the standard coding section.

The Infosys Online Assessment guide (within the Hiring Process article, Article 1) covers the overall assessment structure including how the coding section fits relative to the aptitude sections.

Together, these four articles cover the complete technical preparation journey for the [Infosys selection process](https://insightcrunch.com/2021/12/28/infosys-hiring-process/) from aptitude through coding through technical interview.

---

## More Pseudocode Tracing Practice

The seven pseudocode questions earlier build the foundation. The following set goes deeper into the patterns that Infosys assessments use.

---

### Pseudocode Q8: Nested Loop with Accumulator

```
result = 0
FOR i FROM 1 TO 4:
    FOR j FROM 1 TO i:
        result = result + j
PRINT result
```

**Trace:**
- i=1: j=1 → result=1
- i=2: j=1 → result=2; j=2 → result=4
- i=3: j=1 → result=5; j=2 → result=7; j=3 → result=10
- i=4: j=1 → result=11; j=2 → result=13; j=3 → result=16; j=4 → result=20
- **Output: 20**

---

### Pseudocode Q9: String Reversal in Pseudocode

```
FUNCTION reverse(s):
    result = ""
    FOR i FROM length(s)-1 DOWN TO 0:
        result = result + s[i]
    RETURN result

PRINT reverse("coding")
```

**Trace:**
- Build from last to first: g, n, i, d, o, c
- **Output: "gnidoc"**

---

### Pseudocode Q10: Binary Conversion

```
n = 13
result = ""
WHILE n > 0:
    result = STRING(n MOD 2) + result
    n = n DIV 2
PRINT result
```

**Trace:**
- n=13: 13%2=1, result="1", n=6
- n=6: 6%2=0, result="01", n=3
- n=3: 3%2=1, result="101", n=1
- n=1: 1%2=1, result="1101", n=0
- n=0: exit loop
- **Output: "1101"** (which is 13 in binary: 8+4+0+1)

---

### Pseudocode Q11: Fibonacci Without Recursion

```
a = 0
b = 1
COUNT = 0
WHILE COUNT < 8:
    PRINT a
    temp = a + b
    a = b
    b = temp
    COUNT = COUNT + 1
```

**Trace:**
- COUNT=0: print 0, temp=1, a=1, b=1
- COUNT=1: print 1, temp=2, a=1, b=2
- COUNT=2: print 1, temp=3, a=2, b=3
- COUNT=3: print 2, temp=5, a=3, b=5
- COUNT=4: print 3, temp=8, a=5, b=8
- COUNT=5: print 5, temp=13, a=8, b=13
- COUNT=6: print 8, temp=21, a=13, b=21
- COUNT=7: print 13, COUNT=8, exit
- **Output: 0 1 1 2 3 5 8 13**

---

### Pseudocode Q12: Stack Simulation

```
stack = []
PUSH 5 onto stack
PUSH 3 onto stack
PUSH 7 onto stack
POP from stack and PRINT
PUSH 2 onto stack
POP from stack and PRINT
POP from stack and PRINT
PRINT top of stack
```

**Trace:**
- Push 5: stack=[5]
- Push 3: stack=[5,3]
- Push 7: stack=[5,3,7]
- Pop and print: print 7, stack=[5,3]
- Push 2: stack=[5,3,2]
- Pop and print: print 2, stack=[5,3]
- Pop and print: print 3, stack=[5]
- Print top: print 5
- **Output: 7 2 3 5**

---

### Pseudocode Q13: Matrix Diagonal Sum

```
matrix = [[1,2,3],[4,5,6],[7,8,9]]
sum = 0
FOR i FROM 0 TO 2:
    sum = sum + matrix[i][i]
PRINT sum
```

**Trace:**
- i=0: sum += matrix[0][0] = 1, sum=1
- i=1: sum += matrix[1][1] = 5, sum=6
- i=2: sum += matrix[2][2] = 9, sum=15
- **Output: 15** (main diagonal sum)

---

### Pseudocode Q14: Palindrome Check via Loop

```
FUNCTION check(s):
    n = LENGTH(s)
    FOR i FROM 0 TO n DIV 2 - 1:
        IF s[i] != s[n-1-i]:
            RETURN False
    RETURN True

PRINT check("racecar")
PRINT check("hello")
```

**Trace for "racecar" (n=7):**
- i=0: s[0]='r', s[6]='r' → equal
- i=1: s[1]='a', s[5]='a' → equal
- i=2: s[2]='c', s[4]='c' → equal
- Loop ends (3 = 7//2, 3 iterations done)
- Return True

**Trace for "hello" (n=5):**
- i=0: s[0]='h', s[4]='o' → not equal → Return False

- **Output: True then False**

---

## Handling Common Code Submission Problems

Beyond the algorithm, practical submission issues cause failures that have nothing to do with understanding the problem. These are preventable.

**Problem: Input Parsing Errors**

Most online judges provide input through stdin. In Python:
```python
# Read a single integer
n = int(input())

# Read a line of space-separated integers
arr = list(map(int, input().split()))

# Read n lines each containing an integer
arr = [int(input()) for _ in range(n)]

# Read first line as n, then second line as array
n = int(input())
arr = list(map(int, input().split()))
```

In Java:
```java
Scanner sc = new Scanner(System.in);
int n = sc.nextInt();
int[] arr = new int[n];
for (int i = 0; i < n; i++) {
    arr[i] = sc.nextInt();
}
```

**Problem: Off-by-One in Loops**

The most common coding error. Always verify: should the loop go to `n` (exclusive) or `n-1` (inclusive)? For an array of length n, valid indices are 0 to n-1. A loop `for i in range(n)` uses 0 to n-1 correctly. A loop `for i in range(1, n+1)` uses 1 to n.

**Problem: Output Format Mismatch**

Some judges require exact output including trailing newlines or spaces. Match the expected output format exactly as shown in the sample. If the sample shows `[1, 2, 3]` and you print `1 2 3`, the judge returns Wrong Answer even if the values are correct.

**Problem: Integer Overflow**

In Java and C++, `int` holds values up to approximately 2.1 billion. If the problem involves products or sums of large numbers, use `long`. Python integers are unbounded and never overflow.

---

## Topic-Specific Cheat Sheet

A concise reference for the most important concepts, usable for last-minute review before the assessment.

**Arrays:**
- Second largest: one pass, two variables
- Maximum subarray: Kadane's (current = max(num, current+num))
- Two sum (sorted): two pointers converging
- Rotate by k: Python slice `arr[-k:] + arr[:-k]`
- Move zeroes: maintain "next non-zero position" pointer

**Strings:**
- Palindrome: compare cleaned string with its reverse
- Anagram: sorted(s1) == sorted(s2), or Counter comparison
- First non-repeating: build freq dict, re-scan for freq==1
- Longest unique substring: sliding window with last-seen index

**Patterns:**
- Right triangle: `print('*' * i)` for i in 1..n
- Pyramid: `print(' '*(n-i) + '*'*(2*i-1))` for i in 1..n
- Hollow square: first/last row all stars, middle rows star-space-star

**Math:**
- Prime: check divisibility up to sqrt(n), step by 2
- GCD: Euclidean algorithm `while b: a,b = b,a%b`
- Armstrong: sum(d**len(str(n)) for d in digits) == n
- Perfect: sum proper divisors up to sqrt(n)

**Sorting:**
- Bubble: n rounds, each placing max of unsorted portion at end
- Merge: split, sort halves, merge back O(n log n)
- Binary search: O(log n), requires sorted input

**DP:**
- Coin change: dp[amt] = min(dp[amt], dp[amt-coin]+1)
- LCS: if match: dp[i][j]=dp[i-1][j-1]+1, else max(left,up)
- Knapsack: for each item, choose to include or exclude
- LIS: dp[i] = max(dp[j]+1 for j<i if arr[j]<arr[i])

---

## Final Note: Coding Is a Practice Skill

Every algorithm in this guide was once unfamiliar to someone who now solves these problems in 10 minutes. The difference is entirely in the hours of deliberate practice between that first confusion and the current fluency.

The students who perform best in Infosys coding assessments are not those who have the highest intelligence or the best academic background. They are those who have solved the most problems under the most realistic conditions. Intelligence determines the ceiling; practice determines how close to the ceiling the performance actually reaches.

Four weeks of daily coding practice following the plan in this guide is sufficient to reach a level where any Easy-Medium Infosys coding problem can be solved correctly and confidently within the 30-minute window. The work is straightforward. The results are reliable. The preparation is available to anyone who commits to it.

This guide provides every problem, every solution, every pattern, and every strategy needed. The practice is yours to do.

---

## Additional Solved Problems: Building the Complete Practice Set

The following problems round out the practice set with additional patterns that appear in Infosys assessments.

---

### Problem B1: Check if Array is Sorted

```python
def is_sorted(arr):
    return all(arr[i] <= arr[i+1] for i in range(len(arr)-1))

print(is_sorted([1, 2, 3, 4, 5]))  # True
print(is_sorted([1, 2, 3, 2, 5]))  # False
print(is_sorted([5]))               # True (single element)
print(is_sorted([]))                # True (empty is sorted)
```

---

### Problem B2: Find Missing Number in 1 to N

Given an array of N-1 distinct integers from 1 to N, find the missing one.

```python
def find_missing(arr, n):
    expected_sum = n * (n + 1) // 2
    return expected_sum - sum(arr)

print(find_missing([1, 2, 4, 5, 6], 6))  # 3
print(find_missing([2, 3, 4, 5], 5))      # 1
print(find_missing([1, 2, 3, 4], 5))      # 5
```

**XOR approach (avoids potential overflow with large n):**
```python
def find_missing_xor(arr, n):
    xor = 0
    for i in range(1, n+1):
        xor ^= i
    for x in arr:
        xor ^= x
    return xor
```

---

### Problem B3: Find Duplicate in Array of N+1 Numbers

Array contains N+1 integers all in range [1, N]. Exactly one is duplicated. Find it without modifying the array.

```python
def find_duplicate(arr):
    slow = fast = arr[0]
    # Phase 1: Find intersection point
    while True:
        slow = arr[slow]
        fast = arr[arr[fast]]
        if slow == fast:
            break
    # Phase 2: Find entrance to cycle
    slow = arr[0]
    while slow != fast:
        slow = arr[slow]
        fast = arr[fast]
    return slow

print(find_duplicate([1, 3, 4, 2, 2]))  # 2
print(find_duplicate([3, 1, 3, 4, 2]))  # 3
```

**Simple approach (uses O(n) space):**
```python
def find_duplicate_simple(arr):
    seen = set()
    for x in arr:
        if x in seen:
            return x
        seen.add(x)
```

---

### Problem B4: Flatten a Nested List

Flatten a list that may contain nested lists to arbitrary depth.

```python
def flatten(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result

print(flatten([1, [2, 3], [4, [5, 6]], 7]))
# [1, 2, 3, 4, 5, 6, 7]
print(flatten([[1, [2]], [3, [4, [5]]]]))
# [1, 2, 3, 4, 5]
```

---

### Problem B5: Check for Balanced Parentheses (Only Round Brackets)

Simpler version appearing frequently in Infosys Easy problems.

```python
def is_balanced(s):
    count = 0
    for c in s:
        if c == '(':
            count += 1
        elif c == ')':
            count -= 1
            if count < 0:
                return False
    return count == 0

print(is_balanced("((()))"))  # True
print(is_balanced("(()"))     # False
print(is_balanced(")("))      # False
print(is_balanced(""))        # True
```

---

### Problem B6: Print All Subsets of an Array

```python
def print_subsets(arr):
    n = len(arr)
    for i in range(1 << n):   # 2^n subsets
        subset = [arr[j] for j in range(n) if (i >> j) & 1]
        print(subset)

print_subsets([1, 2, 3])
# [] [1] [2] [1,2] [3] [1,3] [2,3] [1,2,3]
```

---

### Problem B7: String Rotation Check

Check if string B is a rotation of string A.

```python
def is_rotation(A, B):
    if len(A) != len(B):
        return False
    doubled = A + A
    return B in doubled

print(is_rotation("abcde", "cdeab"))  # True
print(is_rotation("abcde", "abced"))  # False
print(is_rotation("aaa", "aaa"))      # True
```

**Why this works:** If B is a rotation of A, then B appears as a substring in A+A.

---

### Problem B8: Number of Islands (Grid Problem)

Count the number of connected regions of '1's in a binary grid.

```python
def num_islands(grid):
    if not grid:
        return 0
    rows, cols = len(grid), len(grid[0])
    count = 0

    def dfs(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] == '0':
            return
        grid[r][c] = '0'   # Mark as visited
        dfs(r+1, c); dfs(r-1, c)
        dfs(r, c+1); dfs(r, c-1)

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                dfs(r, c)
                count += 1
    return count

grid = [
    ["1","1","0","0","0"],
    ["1","1","0","0","0"],
    ["0","0","1","0","0"],
    ["0","0","0","1","1"]
]
print(num_islands(grid))  # 3
```

---

### Problem B9: Palindrome Number (Without String Conversion)

Check if an integer is a palindrome without converting it to a string.

```python
def is_palindrome_number(x):
    if x < 0 or (x % 10 == 0 and x != 0):
        return False
    reversed_half = 0
    while x > reversed_half:
        reversed_half = reversed_half * 10 + x % 10
        x //= 10
    return x == reversed_half or x == reversed_half // 10

print(is_palindrome_number(121))   # True
print(is_palindrome_number(-121))  # False
print(is_palindrome_number(10))    # False
print(is_palindrome_number(0))     # True
```

**Why reverse only half:** Reversing the full number risks overflow for large integers. Comparing halves avoids this and works for both even and odd digit counts.

---

### Problem B10: Implement Queue Using Two Stacks

```python
class QueueUsingStacks:
    def __init__(self):
        self.stack1 = []  # For enqueue
        self.stack2 = []  # For dequeue

    def enqueue(self, x):
        self.stack1.append(x)

    def dequeue(self):
        if not self.stack2:
            while self.stack1:
                self.stack2.append(self.stack1.pop())
        if not self.stack2:
            return None
        return self.stack2.pop()

q = QueueUsingStacks()
q.enqueue(1); q.enqueue(2); q.enqueue(3)
print(q.dequeue())  # 1 (FIFO order)
print(q.dequeue())  # 2
q.enqueue(4)
print(q.dequeue())  # 3
print(q.dequeue())  # 4
```

---

## The Full Problem Index

A quick reference of all problems covered in this guide, organized by category and difficulty:

**Arrays (Easy-Hard):**
1.1 Second Largest, 1.2 Count Even/Odd, 1.3 Rotate Array, 1.4 Pairs with Sum, 1.5 Maximum Subarray (Kadane's), 1.6 Move Zeroes, 1.7 Trapping Rainwater, A1 Dutch National Flag, A2 Maximum Product Subarray, A3 Merge Intervals, A4 Majority Element, A5 Two Sum Sorted, B1 Is Sorted, B2 Find Missing Number, B3 Find Duplicate, B4 Flatten List, B6 All Subsets, B8 Number of Islands

**Strings (Easy-Medium):**
2.1 Count Vowels/Consonants, 2.2 Reverse Words, 2.3 Palindrome Check, 2.4 Anagram Check, 2.5 First Non-Repeating, 2.6 Longest Unique Substring, 2.7 Count and Say, 2.8 String Compression, S1 Longest Palindromic Substring, S2 Group Anagrams, S3 Minimum Window Substring, B5 Balanced Parentheses, B7 Rotation Check, B9 Palindrome Number

**Pattern Printing (Easy-Medium):**
3.1 Right Triangle, 3.2 Inverted Triangle, 3.3 Centered Pyramid, 3.4 Diamond, 3.5 Number Triangle, 3.6 Floyd's Triangle, 3.7 Hollow Square, 3.8 Pascal's Triangle, 3.9 Spiral Matrix

**Mathematics (Easy-Medium):**
4.1 Prime Check, 4.2 Fibonacci, 4.3 Digit Sum/Digital Root, 4.4 GCD/LCM, 4.5 Armstrong Number, 4.6 Prime Factorization, 4.7 Perfect Number, B10 Queue Using Stacks

**Searching and Sorting (Easy-Medium):**
5.1 Binary Search, 5.2 Bubble Sort, 5.3 Merge Sort, 5.4 Kth Largest

**Recursion and DP (Easy-Hard):**
6.1 Factorial, 6.2 Fast Power, 6.3 Coin Change, 6.4 LCS, 6.5 Knapsack, 6.6 LIS

**Pseudocode (All levels):**
Q1-Q14: covering while loops, recursion, array tracing, GCD, swap patterns, conditional loops, case toggle, nested loops, binary conversion, Fibonacci trace, stack simulation, matrix diagonal, palindrome loop

**Mock Test:**
M1 Number to Words, M2 Valid Parentheses, M3 Matrix Rotation

**Total: 80+ problems with complete solutions.**

---

## How Infosys Selects Coding Problems: The Pattern Behind the Questions

Understanding why certain problem types appear in Infosys assessments helps candidates prepare more efficiently. Infosys's coding section is designed with specific goals.

**Goal 1: Filter for Basic Programming Literacy**

The easier of the two coding problems is almost always solvable by anyone who has written code in any language for more than a month. Pattern printing, simple array traversal, and basic string manipulation at this level. The goal is not to find geniuses; it is to confirm that the candidate can actually write and run code, has used loops and conditionals correctly, and can produce correct output for a defined problem.

The implication: if you cannot reliably solve the easy problem in under 15 minutes, that is the gap to fix first. Advanced algorithm study is irrelevant if you cannot handle the guaranteed-easy problem.

**Goal 2: Test Algorithmic Thinking at an Entry Level**

The harder of the two problems requires knowing a specific algorithm or technique: Kadane's for subarray sum, binary search for sorted arrays, the frequency-counting pattern for string problems, or basic DP for optimization problems. These are all learnable patterns, not innate abilities.

The implication: learning the 8-10 core patterns (listed in the Pattern Recognition Guide section) covers the vast majority of what appears in the harder SE-track problem.

**Goal 3: Differentiate for DSE and Premium Tracks**

The DSE assessment uses the same platform but harder problems. The differentiation is in the algorithmic complexity required: DSE problems typically require: understanding sliding window at depth, non-trivial DP (LCS, knapsack at minimum), graph traversal basics, or sorting-based solutions with O(n log n) requirements.

**Goal 4: Assess Code Quality Indirectly**

The judge tests correctness, not code quality. But the ability to write code that handles edge cases correctly is indirectly a code quality signal: engineers who handle edge cases write more defensive, production-quality code. The hidden test cases that include edge scenarios serve both the selection goal (does the candidate handle edges?) and the indirect quality signal.

---

## Dealing with Unfamiliar Problems During the Assessment

Even with extensive preparation, the actual assessment may present a problem in a form that feels unfamiliar. The following approach handles this reliably.

**Step 1: Rephrase the Problem**
If you are confused by the problem statement, rephrase it in your own words. "The problem asks me to find... given... and output..." Writing this out forces comprehension.

**Step 2: Work Through the Sample**
Manually trace through the sample input to understand what transformation the problem requires. Watch what changes between the input and the output.

**Step 3: Identify the Pattern**
Ask: "What category does this feel like?" Arrays? Strings? Math? Sorting? Once the category is identified, ask "Which pattern within this category fits?" The Pattern Recognition Guide section provides the trigger words.

**Step 4: Write the Brute Force**
Even if the optimal approach is unclear, the brute force is usually clear: try all possibilities, pick the best. Implement it. Test it. If it is correct and fast enough for the given constraints, submit it.

**Step 5: Optimize if Time Permits**
Only after submitting a working brute force, consider optimization. What is slow about the brute force? Can a smarter data structure eliminate repeated work? Can sorting enable binary search? Can a DP table eliminate repeated subproblems?

This sequence prioritizes correctness over optimality, which is the right priority in a 30-minute timed assessment.

---

## Infosys Coding Question: Java Template

For candidates using Java, the following template handles the standard input-output pattern for Infosys coding problems and can be adapted to most problem types.

```java
import java.util.*;
import java.io.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        
        // Read input (adapt to problem format)
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) {
            arr[i] = sc.nextInt();
        }
        
        // Call solution function
        System.out.println(solve(arr, n));
    }
    
    static int solve(int[] arr, int n) {
        // Implementation here
        int result = 0;
        // ... your logic
        return result;
    }
}
```

**Adapting for string input:**
```java
String s = sc.nextLine();
// or
String s = sc.next();  // For single word input
```

**Adapting for 2D matrix input:**
```java
int rows = sc.nextInt();
int cols = sc.nextInt();
int[][] matrix = new int[rows][cols];
for (int i = 0; i < rows; i++)
    for (int j = 0; j < cols; j++)
        matrix[i][j] = sc.nextInt();
```

---

## Summary: The Infosys Coding Assessment in 10 Points

1. **Format:** 2 problems, 30 minutes for SE track. One easy, one medium.

2. **Languages:** C, C++, Java, Python. Java recommended for Infosys-specific alignment.

3. **Judge:** Online judge with hidden test cases. Must handle all valid inputs.

4. **Strategy:** Read both first, solve easier first, submit partial rather than blank.

5. **Most guaranteed category:** Pattern printing appears in nearly every assessment as the easy problem.

6. **Most important algorithm:** Kadane's maximum subarray is the single algorithm worth memorizing perfectly.

7. **Most common failure:** Unhandled edge cases. Always test empty input, single element, all identical, max size before submitting.

8. **Pseudocode section:** Separate from coding. Tests reading comprehension of code logic. Practice tracing on paper.

9. **DSE track:** Same platform, harder problems. Requires sliding window mastery, DP proficiency, and O(n log n) thinking.

10. **Preparation principle:** Understand patterns, not solutions. Infosys varies parameters; pattern recognition generalizes to all variations.

Every algorithm and every problem type covered in this guide has been solved correctly by students from non-CS backgrounds with two to three weeks of focused daily practice. The patterns are learnable. The assessment is passable. The guide is complete.

---

## Quick-Reference Solutions for the Most Common Infosys Patterns

This section provides the condensed implementation for the 15 patterns most likely to appear, written for speed of recall and use during last-minute review.

```python
# 1. Second Largest (one pass)
def second_largest(arr):
    a = b = float('-inf')
    for x in arr:
        if x > a: b, a = a, x
        elif x > b and x != a: b = x
    return b

# 2. Kadane's Maximum Subarray
def max_sub(arr):
    best = cur = arr[0]
    for x in arr[1:]:
        cur = max(x, cur+x); best = max(best, cur)
    return best

# 3. Sliding Window: Longest Unique Substring
def longest_uniq(s):
    idx = {}; best = start = 0
    for i, c in enumerate(s):
        if c in idx and idx[c] >= start: start = idx[c]+1
        idx[c] = i; best = max(best, i-start+1)
    return best

# 4. Two Pointers: Pairs with Sum
def pairs_sum(arr, t):
    seen = set(); res = set()
    for x in arr:
        if t-x in seen: res.add((min(x,t-x), max(x,t-x)))
        seen.add(x)
    return sorted(res)

# 5. Binary Search
def bsearch(arr, t):
    l, r = 0, len(arr)-1
    while l <= r:
        m = l+(r-l)//2
        if arr[m]==t: return m
        elif arr[m]<t: l=m+1
        else: r=m-1
    return -1

# 6. GCD (Euclidean)
def gcd(a,b):
    while b: a,b=b,a%b
    return a

# 7. Prime Check
def is_prime(n):
    if n<2: return False
    for i in range(2, int(n**0.5)+1):
        if n%i==0: return False
    return True

# 8. Armstrong
def is_armstrong(n):
    d=str(n); p=len(d)
    return sum(int(x)**p for x in d)==n

# 9. Reverse Words
def rev_words(s): return ' '.join(s.split()[::-1])

# 10. Anagram
def anagram(a,b): return sorted(a.lower())==sorted(b.lower())

# 11. Palindrome
def palindrome(s):
    c=''.join(x.lower() for x in s if x.isalnum())
    return c==c[::-1]

# 12. Coin Change (DP)
def coins(c, amt):
    dp=[float('inf')]*(amt+1); dp[0]=0
    for coin in c:
        for a in range(coin,amt+1):
            dp[a]=min(dp[a],dp[a-coin]+1)
    return dp[amt] if dp[amt]!=float('inf') else -1

# 13. Valid Brackets
def valid_brk(s):
    st=[]; m={')':'(',']':'[','}':'{'}
    for c in s:
        if c in '([{': st.append(c)
        elif not st or st[-1]!=m.get(c,''): return False
        else: st.pop()
    return not st

# 14. Move Zeroes
def move_z(arr):
    p=0
    for x in arr:
        if x: arr[p]=x; p+=1
    for i in range(p,len(arr)): arr[i]=0
    return arr

# 15. Rotate Right by k
def rotate(arr,k):
    n=len(arr); k%=n
    return arr[-k:]+arr[:-k]
```

These 15 implementations cover the problems that together account for the majority of Infosys Easy and Easy-Medium coding questions. Read through them, understand each one, then practice writing each from memory until the code flows without reference.

The coding assessment rewards fluency and pattern recognition. This guide provides both the patterns and the fluency through repeated exposure. The assessment is the opportunity to demonstrate what the practice has built.

---

## The Infosys Coding Round Versus Other IT Company Coding Rounds

Placing the Infosys coding assessment in context relative to peer IT services companies helps candidates who are applying to multiple companies simultaneously calibrate their preparation.

**[Infosys vs TCS](https://insightcrunch.com/2021/12/04/infosys-vs-tcs-vs-wipro-comparison/):**
TCS's CodeVita and NQT coding sections are comparable in difficulty to Infosys's standard SE track. Both test similar categories: arrays, strings, math, and basic algorithms. TCS's competitive programming rounds (CodeVita specifically) are significantly harder and directly comparable to HackWithInfy for premium track selection. The core preparation - mastering Easy to Easy-Medium patterns - applies to both.

**Infosys vs Wipro:**
Wipro's coding section is broadly similar in difficulty profile to Infosys. The AMCAT-based assessments that Wipro uses for some hiring channels share many question patterns with Infosys's assessment. Array manipulation and string processing questions with the same difficulty profile appear consistently.

**[Infosys vs Cognizant](https://insightcrunch.com/2021/11/26/infosys-vs-wipro-vs-cognizant/):**
Cognizant's GenC and GenC Pro tracks both include coding sections. GenC coding is at SE-equivalent difficulty; GenC Pro is slightly harder. The same preparation set covers both effectively.

**The Key Differentiator:**
The Infosys assessment's emphasis on pseudocode questions is more pronounced than at some peer companies. Candidates applying only to Infosys should specifically invest in pseudocode tracing practice. Candidates applying to multiple companies can largely share preparation but should note this Infosys-specific component.

---

## After the Coding Assessment: What the Score Means for Your Application

Understanding how the online assessment score is used helps candidates calibrate their effort allocation between the coding and aptitude sections.

**The Composite Score:**
Infosys does not typically publish the weighting between aptitude sections (Quantitative, Logical, Verbal) and the coding section. Based on candidate reports, the coding section carries weight that is comparable to or greater than any individual aptitude section. Doing well in coding materially improves the overall composite score.

**The Cutoff:**
The assessment cutoff (the minimum composite score for interview shortlisting) varies by hiring cycle and by the batch size relative to available positions. In cycles with high application volume relative to positions, the effective cutoff rises. In cycles with more positions than typical, it may be more accessible.

**What "Partially Correct" Means:**
A coding solution that handles 3 out of 5 hidden test cases typically scores less than a perfect aptitude section. The incentive is clear: a correct, complete coding solution that passes all test cases is worth more than partial credit across multiple test cases. Always aim for complete correctness.

**The Interview Threshold:**
Candidates who clear the online assessment composite cutoff are shortlisted for the technical and HR interviews. The coding assessment score does not directly appear in the interview; the interviewer evaluates technical skills independently. However, candidates who performed well in the coding section typically arrive at the interview with more confidence in their programming ability, which shows.

The Infosys coding assessment is a learnable, passable component of the overall selection process for any candidate who invests in the preparation described in this guide. The 80+ solved problems, 14 pseudocode traces, 3 mock test problems, 15 pattern cheat sheet implementations, and the 4-week preparation plan together constitute everything needed to approach the assessment prepared and confident.


---

*Article 24 of the InsightCrunch Infosys Series. The series covers every stage of the Infosys career journey across 30 articles - from first preparation through experienced professional lateral hiring. Read the complete series at insightcrunch.com.*

---

## Additional Edge Case Reference: Problems That Fail Without Proper Handling

This final section documents the specific edge cases that cause the most submissions to fail on hidden test cases, organized by problem type.

**Array Problems - Common Failures:**
- Second largest with all identical elements: must return -1, not the element itself
- Rotate by k where k > n: must apply `k = k % n` before rotation
- Maximum subarray with all negative: must return the largest (least negative) element, not 0
- Two pairs with duplicate elements: must track unique pairs, not all pair instances

**String Problems - Common Failures:**
- Palindrome check with spaces and punctuation: clean first (alphanumeric only), then check
- Anagram with different cases: convert both to lowercase before comparing
- First non-repeating with all repeating: must return None or -1, not crash
- Longest unique substring with empty string: must return 0, not raise an error

**Math Problems - Common Failures:**
- Prime check for n=0, n=1: both are not prime, must return False
- Prime check for n=2: is prime, special case needed (n=2 is the only even prime)
- Armstrong for single-digit numbers: 1-9 are all Armstrong (digit^1 = digit)
- GCD with 0: gcd(0, n) = n by mathematical definition; the Euclidean algorithm handles this

**Pattern Printing - Common Failures:**
- n=1 edge case: all patterns should output a single star (or number)
- Space versus newline: the judge may require exactly one newline at the end, not two
- Leading space sensitivity: some judges are strict about trailing spaces on each line

**DP Problems - Common Failures:**
- Coin change with target=0: should return 0 (zero coins needed)
- Coin change impossible: must return -1, not infinity
- LCS with one empty string: should return 0
- Knapsack with capacity=0: should return 0

**Pseudocode Tracing - Common Failures:**
- Off-by-one in loop bounds: always verify whether the loop condition uses < or <=
- Integer division vs float division: MOD and DIV in pseudocode are always integer operations
- Recursive base case: always identify and trace the base case first before unwinding

Testing against these edge cases before submission prevents the majority of Wrong Answer results on hidden test cases. Build the habit of running through this list mentally for every submission.

---

## The Complete 30-Day Daily Practice Schedule

For candidates with exactly 30 days before the Infosys assessment, the following daily schedule provides structured coverage of every problem type in this guide.

**Days 1-5: Arrays Foundation**
Day 1: Problems 1.1, 1.2, 1.3 (Second Largest, Even/Odd, Rotate)
Day 2: Problems 1.4, 1.5 (Pairs with Sum, Kadane's)
Day 3: Problems 1.6, 1.7 (Move Zeroes, Trapping Rainwater)
Day 4: Problems A1, A2 (Dutch Flag, Max Product)
Day 5: Problems A3, A4, A5, B1 (Merge Intervals, Majority, Two Sum, Is Sorted)

**Days 6-10: Strings**
Day 6: Problems 2.1, 2.2, 2.3 (Vowels, Reverse Words, Palindrome)
Day 7: Problems 2.4, 2.5 (Anagram, First Non-Repeating)
Day 8: Problems 2.6, 2.7 (Longest Unique, Count and Say)
Day 9: Problems 2.8, S1 (Compression, Longest Palindromic)
Day 10: Problems S2, S3, B7 (Group Anagrams, Min Window, Rotation)

**Days 11-15: Pattern Printing**
Day 11: Problems 3.1, 3.2, 3.3, 3.4 (All triangle/pyramid patterns)
Day 12: Problems 3.5, 3.6 (Number Triangle, Floyd's)
Day 13: Problems 3.7, 3.8 (Hollow Square, Pascal's)
Day 14: Problem 3.9 (Spiral Matrix - spend full session on this)
Day 15: Reproduce all 9 patterns from memory under 45-minute timer

**Days 16-18: Math and Number Theory**
Day 16: Problems 4.1, 4.2, 4.3 (Prime, Fibonacci, Digit Sum)
Day 17: Problems 4.4, 4.5 (GCD/LCM, Armstrong)
Day 18: Problems 4.6, 4.7, B2, B3 (Factorization, Perfect, Missing, Duplicate)

**Days 19-21: Searching and Sorting**
Day 19: Problems 5.1, 5.2 (Binary Search, Bubble Sort)
Day 20: Problems 5.3, 5.4 (Merge Sort, Kth Largest)
Day 21: Additional problems B6, B8, B9, B10 (Subsets, Islands, Palindrome Number, Queue)

**Days 22-25: Recursion and DP**
Day 22: Problems 6.1, 6.2 (Factorial, Fast Power)
Day 23: Problem 6.3 (Coin Change - understand the DP state definition deeply)
Day 24: Problems 6.4, 6.5 (LCS, Knapsack)
Day 25: Problem 6.6 + review all DP problems (LIS + full DP review)

**Days 26-27: Pseudocode Tracing**
Day 26: Trace Q1-Q7 on paper without running code, then verify
Day 27: Trace Q8-Q14 on paper without running code, then verify

**Days 28-30: Mock Tests**
Day 28: Full mock test (M1 + M2), strict 30-minute timer
Day 29: Full mock test with 2 random problems from this guide
Day 30: Review the 15-pattern cheat sheet from memory, light review only

This 30-day schedule ensures complete coverage of every problem type in this guide with deliberate review built in. The final three days of mock testing train the time management skill that is as important as algorithmic knowledge on the actual assessment day.
