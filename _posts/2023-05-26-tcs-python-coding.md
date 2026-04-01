---
layout: post
title: "TCS Python Coding: Leverage Python's Power"
page_title: "TCS Coding Questions Using Python - Pythonic Solutions, Performance Tips, and Compiler-Specific Guidance"
date: 2023-05-26
categories: ["Industry"]
tags: ["TCS Python coding", "TCS Python solutions", "TCS Python programs", "Python for TCS", "TCS NQT Python"]
excerpt: "Solve TCS coding problems the Pythonic way. Leverage Python's strengths while avoiding compiler pitfalls on TCS platform."
image: "/assets/images/blog/blog-24.webp"
reading_time: 60
author: "sneha-reddy"
last_updated: 2026-03-30
---
Python has become the most popular language among TCS NQT candidates who are not competitive programmers by background, and for good reason: its expressive syntax lets you write correct solutions faster, its built-in data structures eliminate boilerplate, and its standard library contains tools that solve entire categories of problems in one function call. But Python on TCS iON has specific considerations - version compatibility matters, time limits can catch out naive implementations, and the input handling pattern is different from what most candidates practise. This guide covers the complete Python picture for TCS: the platform-specific details you must know, and a category-by-category problem collection showing both the Pythonic approach and the naive approach so you understand what Python is saving you.

![TCS Guide](/assets/images/blog/blog-24.webp)

## Python on TCS iON: What You Need to Know

### Version Compatibility

TCS iON supports Python 3 (the current standard). Python 2 is not supported. This distinction matters for a few specific patterns:

- `print` is a function in Python 3: `print(value)` not `print value`
- `input()` returns a string in Python 3 (not automatically converted to int)
- Integer division uses `//` in Python 3; `/` always returns float
- `range()` returns an iterator in Python 3 (not a list), but this is almost never a problem in practice
- `map()` and `filter()` return iterators, so wrap them in `list()` if you need to index

All code in this guide uses Python 3 syntax.

### Speed: When Python Is and Is Not a Good Choice

**Python's execution speed is roughly 5-10x slower than C/C++ and 2-4x slower than Java** for equivalent algorithms. On TCS iON:

**Python works fine for:**
- Foundation (Ninja) level problems with N ≤ 10,000
- Problems whose algorithm is O(N) or O(N log N) with small N
- String manipulation (Python's string methods are implemented in C internally - fast)
- Problems where Python's arbitrary precision integers are an advantage (no overflow)

**Python may TLE (Time Limit Exceeded) for:**
- O(N²) algorithms with N > 1,000
- Advanced coding problems with N up to 100,000 or more
- Graph problems with dense adjacency requiring many inner loop iterations

**The practical rule:** For Foundation Coding (Ninja level), Python is an excellent choice. For Digital Advanced Coding, C++ is safer. If you are targeting Digital and your strongest language is Python, solve the problem in Python but be aware of TLE risk on large inputs.

### Input Handling: Two Methods

**Method 1: Standard input with `input()` and `sys.stdin`**

```python
# Read a single integer
n = int(input())

# Read multiple integers from one line
a, b = map(int, input().split())

# Read N integers on separate lines
arr = [int(input()) for _ in range(n)]

# Read all integers from one space-separated line
nums = list(map(int, input().split()))

# Fast input for competitive programming (large inputs)
import sys
input = sys.stdin.readline  # replace input globally with faster version
```

**Method 2: Command line arguments with `sys.argv`**

```python
import sys

# sys.argv[0] = script name, sys.argv[1] = first argument, etc.
n = int(sys.argv[1])
a = int(sys.argv[1])
b = int(sys.argv[2])

# Read N numbers passed as separate arguments
# Run: python program.py 5 3 7 2 8 5
n = int(sys.argv[1])
arr = [int(sys.argv[i+2]) for i in range(n)]

# Read all numbers when count is not given separately
arr = [int(x) for x in sys.argv[1:]]
```

**How to know which to use:** Read the problem statement. "Command line arguments" → use `sys.argv`. "Standard input" or a sample input block → use `input()`. No explicit instruction → use `sys.argv` (safer default for TCS).

### Output Formatting

Python output must exactly match expected output:

```python
# Print a single value
print(42)           # prints "42\n"

# Print without newline
print(42, end="")   # prints "42" with no newline

# Print space-separated values
print(1, 2, 3)      # prints "1 2 3\n"
print(*arr)         # unpack list: prints "3 7 2 8 5\n"

# Print comma-separated
print(*arr, sep=", ")  # prints "3, 7, 2, 8, 5\n"

# Formatted numbers
print(f"{3.14159:.2f}")  # prints "3.14\n"
print("{:.2f}".format(3.14159))  # same

# Join a list into a string for output
print(" ".join(map(str, arr)))  # equivalent to print(*arr)
```

---

## Part 1: Input/Output Patterns

### Problem IO-1: Read N Numbers and Print Statistics

**Problem statement:** Read N numbers. Print their sum, average, maximum, and minimum.

**Naive approach:**
```python
import sys

n = int(sys.argv[1])
arr = [int(sys.argv[i+2]) for i in range(n)]

total = 0
for x in arr:
    total += x
avg = total / n
maximum = arr[0]
minimum = arr[0]
for x in arr:
    if x > maximum:
        maximum = x
    if x < minimum:
        minimum = x

print(f"Sum: {total}")
print(f"Average: {avg:.2f}")
print(f"Max: {maximum}")
print(f"Min: {minimum}")
```

**Pythonic approach:**
```python
import sys

arr = [int(x) for x in sys.argv[1:]]
print(f"Sum: {sum(arr)}")
print(f"Average: {sum(arr)/len(arr):.2f}")
print(f"Max: {max(arr)}")
print(f"Min: {min(arr)}")
```

**What Python saves:** `sum()`, `max()`, `min()` are built-in functions. The list comprehension replaces the reading loop. The f-string handles formatting. The Pythonic version is 4 lines instead of 14 with identical correctness.

### Problem IO-2: Formatted Table Output

**Problem statement:** Read N student names and marks. Print a table with name, marks, and grade.

```python
import sys

# Input: name1 marks1 name2 marks2 ...
data = sys.argv[1:]
print(f"{'Name':<15} {'Marks':>6} {'Grade':>6}")
print("-" * 30)

for i in range(0, len(data), 2):
    name = data[i]
    marks = int(data[i+1])
    if marks >= 90:   grade = 'A'
    elif marks >= 75: grade = 'B'
    elif marks >= 60: grade = 'C'
    elif marks >= 50: grade = 'D'
    else:             grade = 'F'
    print(f"{name:<15} {marks:>6} {grade:>6}")
```

**Python formatting reference:**
- `{value:<width}`: left-align in width
- `{value:>width}`: right-align in width
- `{value:^width}`: centre in width
- `{value:0width}`: zero-pad
- `{value:.2f}`: 2 decimal places

---

## Part 2: String Operations

Python's string handling capabilities are arguably its strongest competitive programming advantage. Operations that require 20 lines in C take 1 line in Python.

### Problem STR-1: String Reversal and Palindrome Check

**Naive (but still Pythonic):**
```python
import sys
s = sys.argv[1]
rev = s[::-1]  # Python slice reversal - the idiomatic way
print(rev)
print("Palindrome" if s == rev else "Not Palindrome")
```

**The `s[::-1]` explained:** Python slices take the form `s[start:stop:step]`. With `start` and `stop` omitted, it covers the whole string. `step = -1` means traverse in reverse. This single operation reverses any sequence (string, list, tuple).

### Problem STR-2: Anagram Check

**Naive approach:**
```python
import sys
s1, s2 = sys.argv[1], sys.argv[2]
freq = {}
for c in s1:
    freq[c] = freq.get(c, 0) + 1
for c in s2:
    freq[c] = freq.get(c, 0) - 1
print("Anagram" if all(v == 0 for v in freq.values()) else "Not Anagram")
```

**Pythonic approach:**
```python
import sys
from collections import Counter

s1, s2 = sys.argv[1], sys.argv[2]
print("Anagram" if Counter(s1) == Counter(s2) else "Not Anagram")
```

**`Counter` explained:** `Counter` creates a dictionary mapping each element to its count. `Counter("hello")` returns `Counter({'l': 2, 'h': 1, 'e': 1, 'o': 1})`. Comparing two Counters checks if the frequency distributions are identical - the exact definition of anagram.

### Problem STR-3: All Permutations of a String

**Python approach using itertools:**
```python
import sys
from itertools import permutations

s = sys.argv[1]
perms = sorted(set(''.join(p) for p in permutations(s)))
for p in perms:
    print(p)
```

**What this does:** `permutations(s)` generates all ordered arrangements of the characters. The outer `set()` removes duplicates (for strings with repeated characters). `sorted()` gives lexicographic order. The `''.join(p)` converts each tuple of characters back to a string.

**Without itertools (naive recursive):**
```python
def permutations_manual(s, prefix=""):
    if len(s) == 0:
        print(prefix)
        return
    seen = set()
    for i, char in enumerate(s):
        if char not in seen:
            seen.add(char)
            permutations_manual(s[:i] + s[i+1:], prefix + char)
```

The itertools version is faster (implemented in C internally) and shorter. Use it.

### Problem STR-4: Longest Common Substring

**Problem statement:** Find the longest common substring of two strings.

```python
import sys

s1, s2 = sys.argv[1], sys.argv[2]
m, n = len(s1), len(s2)
dp = [[0] * (n + 1) for _ in range(m + 1)]
max_len = 0
end_idx = 0

for i in range(1, m + 1):
    for j in range(1, n + 1):
        if s1[i-1] == s2[j-1]:
            dp[i][j] = dp[i-1][j-1] + 1
            if dp[i][j] > max_len:
                max_len = dp[i][j]
                end_idx = i

print(s1[end_idx - max_len: end_idx])
print(f"Length: {max_len}")
```

**Python advantage:** 2D list initialisation `[[0]*(n+1) for _ in range(m+1)]` is clean. The slice `s1[end_idx - max_len: end_idx]` extracts the result without pointer arithmetic.

### Problem STR-5: Most Frequent Character

**Naive:**
```python
import sys
s = sys.argv[1]
freq = {}
for c in s:
    freq[c] = freq.get(c, 0) + 1
most_freq = max(freq, key=freq.get)
print(f"{most_freq}: {freq[most_freq]}")
```

**Pythonic:**
```python
import sys
from collections import Counter

s = sys.argv[1]
counter = Counter(s)
char, count = counter.most_common(1)[0]
print(f"{char}: {count}")
```

`most_common(1)` returns a list of the 1 most common `(element, count)` tuples.

### Problem STR-6: Caesar Cipher Encode and Decode

**Problem statement:** Encode a string by shifting each letter by K positions (wrapping around).

```python
import sys

def caesar(text, shift, encode=True):
    result = []
    for c in text:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            shift_amount = shift if encode else -shift
            shifted = (ord(c) - base + shift_amount) % 26 + base
            result.append(chr(shifted))
        else:
            result.append(c)
    return ''.join(result)

text = sys.argv[1]
k = int(sys.argv[2])
print(caesar(text, k, encode=True))
print(caesar(text, k, encode=False))
```

**Python string methods used:**
- `c.isalpha()`: True if character is a letter
- `c.isupper()`: True if uppercase
- `ord(c)`: ASCII code of character
- `chr(n)`: Character from ASCII code
- `''.join(result)`: Concatenate list to string (faster than string + in a loop)

---

## Part 3: List Operations

### Problem LST-1: Sorting with Custom Key

**Sort students by marks descending, then name ascending:**
```python
import sys
from functools import cmp_to_key

# Input: name1 marks1 name2 marks2 ...
data = sys.argv[1:]
students = [(data[i], int(data[i+1])) for i in range(0, len(data), 2)]

# Sort: marks descending (-x[1]), then name ascending (x[0])
students.sort(key=lambda x: (-x[1], x[0]))

for name, marks in students:
    print(f"{name}: {marks}")
```

**Python sort key functions:**
- `key=lambda x: x[1]`: sort by second element ascending
- `key=lambda x: -x[1]`: sort by second element descending
- `key=lambda x: (x[1], x[0])`: sort by second then first (tuple comparison)
- `key=str.lower`: case-insensitive string sort
- `key=len`: sort by length

### Problem LST-2: List Comprehension for Data Transformation

**Problem: Given N integers, produce a list of (number, square, cube) for all even numbers.**

**Naive:**
```python
result = []
for x in arr:
    if x % 2 == 0:
        result.append((x, x*x, x*x*x))
```

**Pythonic:**
```python
result = [(x, x**2, x**3) for x in arr if x % 2 == 0]
```

**Nested list comprehension - Flatten a 2D list:**
```python
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [x for row in matrix for x in row]  # [1,2,3,4,5,6,7,8,9]
```

**Conditional transformation:**
```python
# Replace negatives with 0
cleaned = [max(0, x) for x in arr]
# or equivalently:
cleaned = [x if x > 0 else 0 for x in arr]
```

### Problem LST-3: Group by Property (groupby from itertools)

**Problem: Given a list of words, group them by their first letter.**

```python
import sys
from itertools import groupby

words = sys.argv[1:]
words.sort()  # groupby requires sorted input for complete groups

for key, group in groupby(words, key=lambda w: w[0]):
    print(f"{key}: {', '.join(group)}")
```

**Alternative using defaultdict (often cleaner for non-sorted grouping):**
```python
from collections import defaultdict

grouped = defaultdict(list)
for word in words:
    grouped[word[0]].append(word)

for letter in sorted(grouped):
    print(f"{letter}: {', '.join(grouped[letter])}")
```

### Problem LST-4: Stack and Queue Using Lists and Deque

**Stack (LIFO) - use list:**
```python
stack = []
stack.append(5)    # push
stack.append(10)   # push
top = stack.pop()  # pop: returns 10
top = stack[-1]    # peek without removing: returns 5
```

**Queue (FIFO) - use deque (not list):**
```python
from collections import deque

queue = deque()
queue.append(5)       # enqueue
queue.append(10)      # enqueue
front = queue.popleft()  # dequeue: returns 5
# Do NOT use list.pop(0) - it's O(N). deque.popleft() is O(1).
```

**Why deque for queues:** `list.pop(0)` is O(N) because all elements shift left. `collections.deque.popleft()` is O(1) because deque is implemented as a doubly-linked list.

---

## Part 4: Mathematical Problems

Python's mathematical capabilities have two specific advantages over C/C++: arbitrary precision integers and a rich `math` module.

### Python's Arbitrary Precision Integers

In C/C++, integers have fixed sizes (int = 32 bits, long long = 64 bits). Python integers have no size limit - they grow as needed.

```python
# This is correct in Python, would overflow in C
print(2 ** 100)  # 1267650600228229401496703205376

# Factorial of 100 - exact, no overflow
import math
print(math.factorial(100))
# 93326215443944152681699238856266700490715968264381621468592963895217599993229915608941463976156518286253697920827223758251185210916864000000000000000000000000

# Very large GCD computation
from math import gcd
print(gcd(10**15 + 7, 10**15 + 3))  # works perfectly
```

This eliminates an entire class of bugs that plague C solutions.

### Problem MATH-1: Fibonacci with Large Numbers

**In C/C++:** Fibonacci overflows long long at F(92). Need big integer library or modular arithmetic.

**In Python:** No overflow ever.

```python
import sys

def fibonacci(n):
    if n <= 0: return 0
    if n == 1: return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

n = int(sys.argv[1])
print(fibonacci(n))  # correct for any n, no overflow
```

**With memoisation (for repeated calls):**
```python
from functools import lru_cache
import sys

@lru_cache(maxsize=None)
def fib(n):
    if n <= 1: return n
    return fib(n-1) + fib(n-2)

print(fib(int(sys.argv[1])))
```

### Problem MATH-2: Combinatorics - nCr and nPr

**Using math module:**
```python
import sys
from math import comb, perm, factorial

n, r = int(sys.argv[1]), int(sys.argv[2])

print(f"nCr: {comb(n, r)}")      # n! / (r! * (n-r)!)
print(f"nPr: {perm(n, r)}")      # n! / (n-r)!
print(f"n!: {factorial(n)}")
```

`math.comb` and `math.perm` are exact integer computations - no floating point errors, no overflow.

**Manual nCr using Pascal's triangle (for iterative computation):**
```python
def ncr(n, r):
    if r > n - r:  # optimisation: use smaller r
        r = n - r
    result = 1
    for i in range(r):
        result = result * (n - i) // (i + 1)
    return result
```

### Problem MATH-3: Prime Factorisation

**Problem statement:** Find all prime factors of N.

**Naive approach:**
```python
import sys

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

n = int(sys.argv[1])
print(*prime_factors(n))
```

**Pythonic using generator:**
```python
def prime_factors(n):
    d = 2
    while d * d <= n:
        while n % d == 0:
            yield d
            n //= d
        d += 1
    if n > 1:
        yield n

print(*prime_factors(int(sys.argv[1])))
```

**Generator version is memory-efficient** for very large numbers since factors are yielded one at a time rather than all stored in a list.

### Problem MATH-4: Sieve of Eratosthenes

```python
import sys

def sieve(n):
    is_prime = bytearray([1]) * (n + 1)  # bytearray is faster than list of bool
    is_prime[0] = is_prime[1] = 0
    i = 2
    while i * i <= n:
        if is_prime[i]:
            is_prime[i*i::i] = bytearray(len(is_prime[i*i::i]))  # zero out multiples
        i += 1
    return [i for i in range(2, n+1) if is_prime[i]]

n = int(sys.argv[1])
primes = sieve(n)
print(f"Prime count up to {n}: {len(primes)}")
print(f"Sum of primes: {sum(primes)}")
```

**`bytearray` vs list of bool:** `bytearray` uses 1 byte per element (vs 28 bytes per element for Python bool in a list). For a sieve of 10^6, `bytearray` uses 1 MB; a list of booleans uses 28 MB. For large sieves, `bytearray` is the correct choice.

**Slice assignment `is_prime[i*i::i] = bytearray(...)`:** This zeroes out all indices that are multiples of i, starting from i*i. Single line replaces the inner loop.

---

## Part 5: Dictionary and Set Operations

### Problem DICT-1: Word Frequency Counter

**Problem statement:** Count frequency of each word in a text.

**Pythonic:**
```python
import sys
from collections import Counter

words = sys.argv[1:]
freq = Counter(words)

# Print in frequency order (most common first)
for word, count in freq.most_common():
    print(f"{word}: {count}")
```

**Using defaultdict:**
```python
from collections import defaultdict

freq = defaultdict(int)
for word in words:
    freq[word] += 1  # no KeyError - defaultdict initialises missing keys to 0
```

### Problem DICT-2: Group Anagrams

**Problem statement:** Group a list of words by their anagram family.

```python
import sys
from collections import defaultdict

words = sys.argv[1:]
groups = defaultdict(list)

for word in words:
    key = ''.join(sorted(word))  # sorted chars = canonical form
    groups[key].append(word)

for group in groups.values():
    print(' '.join(sorted(group)))
```

**The canonical key approach:** Sorting the letters of a word gives the same string for all anagrams of each other. "eat", "tea", "ate" all sort to "aet". This sorted form is used as the dictionary key.

### Problem DICT-3: Two Sum (Count Pairs)

**Problem statement:** Count pairs of elements in an array that sum to target K.

**O(N²) naive:**
```python
count = sum(1 for i in range(len(arr))
            for j in range(i+1, len(arr))
            if arr[i] + arr[j] == k)
```

**O(N) with Counter:**
```python
import sys
from collections import Counter

k = int(sys.argv[1])
arr = list(map(int, sys.argv[2:]))

freq = Counter(arr)
count = 0
for x in freq:
    complement = k - x
    if complement in freq:
        if x == complement:
            count += freq[x] * (freq[x] - 1) // 2  # pairs within same value
        elif x < complement:
            count += freq[x] * freq[complement]

print(count)
```

### Problem DICT-4: Set Operations - Unique Elements and Intersection

```python
import sys

# Input: n1 elements for set1, n2 elements for set2
n1 = int(sys.argv[1])
set1 = set(map(int, sys.argv[2:2+n1]))
set2 = set(map(int, sys.argv[2+n1:]))

print("Union:", *sorted(set1 | set2))
print("Intersection:", *sorted(set1 & set2))
print("Difference (1-2):", *sorted(set1 - set2))
print("Symmetric Difference:", *sorted(set1 ^ set2))
```

**Set operators:**
- `|` union: all elements in either set
- `&` intersection: elements in both
- `-` difference: in left but not right
- `^` symmetric difference: in exactly one

---

## Part 6: Number Theory with Python

### Problem NT-1: GCD, LCM, Extended Euclidean

```python
import sys
from math import gcd

a, b = int(sys.argv[1]), int(sys.argv[2])

g = gcd(a, b)
l = a * b // g  # LCM = (a*b) / gcd(a,b) - use // to stay integer

print(f"GCD: {g}")
print(f"LCM: {l}")

# GCD of a list
from math import gcd
from functools import reduce

nums = list(map(int, sys.argv[1:]))
overall_gcd = reduce(gcd, nums)
print(f"GCD of list: {overall_gcd}")
```

**`functools.reduce(gcd, nums)`:** Applies `gcd` cumulatively: gcd(gcd(gcd(a, b), c), d)... This computes GCD of any number of integers in a single expression.

### Problem NT-2: Modular Exponentiation

**Problem statement:** Compute (base^exp) mod m.

**Python's built-in:**
```python
import sys

base, exp, m = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
result = pow(base, exp, m)  # Python's built-in three-argument pow
print(result)
```

**`pow(base, exp, m)` is Python's built-in modular exponentiation.** It uses binary exponentiation internally and is optimised in C. It correctly handles very large exponents. This one function replaces the entire implementation that C/C++ requires writing manually.

### Problem NT-3: Digital Root

```python
import sys

n = abs(int(sys.argv[1]))
# O(1) mathematical formula:
if n == 0:
    print(0)
elif n % 9 == 0:
    print(9)
else:
    print(n % 9)
```

### Problem NT-4: All Divisors of N

```python
import sys

def divisors(n):
    divs = []
    i = 1
    while i * i <= n:
        if n % i == 0:
            divs.append(i)
            if i != n // i:
                divs.append(n // i)
        i += 1
    return sorted(divs)

n = int(sys.argv[1])
print(*divisors(n))
print(f"Count: {len(divisors(n))}")
```

---

## Part 7: Sorting and Searching

### Python's Sort: Key Functions and Stability

Python's `sorted()` and `list.sort()` use Timsort - O(N log N) average, O(N) best case (nearly sorted), and stable (preserves relative order of equal elements).

```python
# Basic sort
arr = [5, 3, 1, 4, 2]
arr.sort()                          # in-place ascending
arr.sort(reverse=True)              # in-place descending
sorted_arr = sorted(arr)            # returns new sorted list
sorted_desc = sorted(arr, reverse=True)

# Sort tuples by second element
points = [(1, 3), (2, 1), (3, 2)]
points.sort(key=lambda p: p[1])    # [(2,1), (3,2), (1,3)]

# Sort strings by length then alphabetically
words = ['banana', 'apple', 'cherry', 'fig']
words.sort(key=lambda w: (len(w), w))  # [('fig', 3), ('apple', 5), ('banana', 6), ('cherry', 6)]
# Result: ['fig', 'apple', 'banana', 'cherry']

# Sort objects by multiple attributes
students = [('Alice', 85), ('Bob', 90), ('Charlie', 85)]
students.sort(key=lambda s: (-s[1], s[0]))  # marks desc, name asc
```

### Binary Search with bisect Module

```python
from bisect import bisect_left, bisect_right, insort

arr = [1, 3, 3, 5, 7, 9]

# Find leftmost position where 3 can be inserted (first 3's position)
print(bisect_left(arr, 3))   # 1 (index of first 3)

# Find rightmost position where 3 can be inserted (after last 3)
print(bisect_right(arr, 3))  # 3 (index after last 3)

# Count occurrences of 3
count = bisect_right(arr, 3) - bisect_left(arr, 3)  # 2

# Find if a value exists in sorted array (O(log N))
def binary_search(arr, target):
    idx = bisect_left(arr, target)
    return idx < len(arr) and arr[idx] == target

# Insert while maintaining sorted order
insort(arr, 4)  # arr becomes [1, 3, 3, 4, 5, 7, 9]
```

### Problem SRCH-1: K-th Largest Element

**Sorting approach (simpler):**
```python
import sys

k = int(sys.argv[1])
arr = [int(x) for x in sys.argv[2:]]
arr.sort(reverse=True)
print(arr[k-1])
```

**Heap approach (O(N log k) - better for large N, small k):**
```python
import sys
import heapq

k = int(sys.argv[1])
arr = [int(x) for x in sys.argv[2:]]
print(heapq.nlargest(k, arr)[-1])  # k-th largest
```

**`heapq.nlargest(k, arr)`** returns the k largest elements in O(N log k) time. Significantly faster than full sort for large N with small k.

---

## Part 8: Advanced Problems with Python-Specific Tools

### Dynamic Programming with lru_cache

`functools.lru_cache` adds memoisation to any function with a single decorator. This is Python's most powerful DP tool.

**Problem: Count ways to make change for amount N using coins of given denominations.**

```python
import sys
from functools import lru_cache

coins = list(map(int, sys.argv[2:]))
target = int(sys.argv[1])

@lru_cache(maxsize=None)
def ways(amount):
    if amount == 0: return 1
    if amount < 0: return 0
    return sum(ways(amount - c) for c in coins)

print(ways(target))
```

**Without lru_cache (manual memoisation):**
```python
memo = {}
def ways(amount):
    if amount in memo: return memo[amount]
    if amount == 0: return 1
    if amount < 0: return 0
    result = sum(ways(amount - c) for c in coins)
    memo[amount] = result
    return result
```

`lru_cache` version is cleaner - the cache management is automatic.

**Classic DP problems with lru_cache:**

**Longest Increasing Subsequence:**
```python
import sys
from functools import lru_cache

arr = [int(x) for x in sys.argv[1:]]
n = len(arr)

@lru_cache(maxsize=None)
def lis(i):
    return 1 + max((lis(j) for j in range(i) if arr[j] < arr[i]), default=0)

print(max(lis(i) for i in range(n)))
```

**0/1 Knapsack:**
```python
import sys
from functools import lru_cache

# Input: capacity, then n pairs of (weight, value)
args = list(map(int, sys.argv[1:]))
W = args[0]
items = [(args[i], args[i+1]) for i in range(1, len(args)-1, 2)]
n = len(items)

@lru_cache(maxsize=None)
def knapsack(idx, capacity):
    if idx == n or capacity == 0: return 0
    weight, value = items[idx]
    skip = knapsack(idx + 1, capacity)
    if weight <= capacity:
        take = value + knapsack(idx + 1, capacity - weight)
        return max(skip, take)
    return skip

print(knapsack(0, W))
```

### Problem ADV-1: Itertools for Combinations and Permutations

```python
import sys
from itertools import combinations, permutations, combinations_with_replacement, product

arr = list(map(int, sys.argv[1:]))
r = 2  # choose r elements

# All r-combinations (no repetition, order doesn't matter)
combos = list(combinations(arr, r))
print(f"Combinations C({len(arr)},{r}): {combos}")

# All r-permutations (no repetition, order matters)
perms = list(permutations(arr, r))
print(f"Permutations P({len(arr)},{r}): {perms}")

# Combinations with repetition
combos_rep = list(combinations_with_replacement(arr, r))
print(f"With repetition: {combos_rep}")

# Cartesian product of array with itself
pairs = list(product(arr, repeat=2))
print(f"Cartesian product: {pairs}")
```

### Problem ADV-2: Graph BFS with deque

```python
import sys
from collections import deque, defaultdict

# Input: n_nodes, n_edges, then edge pairs
args = list(map(int, sys.argv[1:]))
n = args[0]
m = args[1]
adj = defaultdict(list)

for i in range(m):
    u, v = args[2 + 2*i], args[3 + 2*i]
    adj[u].append(v)
    adj[v].append(u)

# BFS from node 1
visited = set()
queue = deque([1])
visited.add(1)
order = []

while queue:
    node = queue.popleft()
    order.append(node)
    for neighbour in sorted(adj[node]):  # sorted for deterministic output
        if neighbour not in visited:
            visited.add(neighbour)
            queue.append(neighbour)

print("BFS order:", *order)
print("Connected nodes:", len(visited))
```

### Problem ADV-3: Heap for Priority Queue Operations

```python
import sys
import heapq

# Min-heap operations
heap = []
heapq.heappush(heap, 5)
heapq.heappush(heap, 2)
heapq.heappush(heap, 8)
heapq.heappush(heap, 1)

print(heapq.heappop(heap))  # 1 (minimum)
print(heap[0])              # 2 (peek minimum without removing)

# Max-heap: negate values (Python only has min-heap natively)
max_heap = []
for x in [5, 2, 8, 1]:
    heapq.heappush(max_heap, -x)
print(-heapq.heappop(max_heap))  # 8 (maximum, negated back)

# Heapify: convert list to heap in O(N)
arr = [5, 2, 8, 1, 9, 3]
heapq.heapify(arr)  # arr is now a valid min-heap
```

**Problem: Merge K sorted arrays into one sorted array.**
```python
import sys
import heapq

# Input: k (number of arrays), then k arrays of varying sizes
# For simplicity: 2 sorted arrays
n1 = int(sys.argv[1])
arr1 = list(map(int, sys.argv[2:2+n1]))
arr2 = list(map(int, sys.argv[2+n1:]))

# Use heapq.merge for sorted iterables
from heapq import merge
merged = list(merge(arr1, arr2))
print(*merged)
```

`heapq.merge` merges sorted iterables in O(N log K) time where K is the number of iterables.

---

## Python-Specific Time-Saving Tricks for TCS

### Trick 1: Walrus Operator (:=) for Combined Assignment and Test

```python
# Read until end of input
import sys

data = []
while line := sys.stdin.readline():
    data.append(int(line.strip()))
```

### Trick 2: zip() for Parallel Iteration

```python
names = ['Alice', 'Bob', 'Charlie']
scores = [85, 90, 78]

# Instead of: for i in range(len(names)): print(names[i], scores[i])
for name, score in zip(names, scores):
    print(f"{name}: {score}")

# Matrix transpose using zip
matrix = [[1,2,3],[4,5,6],[7,8,9]]
transposed = list(zip(*matrix))  # [(1,4,7),(2,5,8),(3,6,9)]
```

### Trick 3: enumerate() for Index + Value

```python
arr = ['a', 'b', 'c', 'd']

# Instead of: for i in range(len(arr)): print(i, arr[i])
for i, val in enumerate(arr):
    print(i, val)

# Start from 1
for i, val in enumerate(arr, start=1):
    print(i, val)
```

### Trick 4: any() and all() for Boolean Aggregation

```python
arr = [2, 4, 6, 8]

# Is any element odd?
print(any(x % 2 != 0 for x in arr))  # False

# Are all elements positive?
print(all(x > 0 for x in arr))  # True

# Generator expression inside any/all is lazy-evaluated (stops at first True/False)
```

### Trick 5: unpacking and * operator

```python
# Swap without temp variable
a, b = b, a  # pythonic swap

# Multiple assignment
first, *rest = [1, 2, 3, 4, 5]  # first=1, rest=[2,3,4,5]
first, *middle, last = [1,2,3,4,5]  # first=1, middle=[2,3,4], last=5

# Spread list into function arguments
arr = [1, 2, 3]
print(*arr)       # print(1, 2, 3)
print(max(*arr))  # max(1, 2, 3)
```

### Trick 6: String Methods for Clean Processing

```python
# Split and strip in one step
line = "  hello world  \n"
words = line.split()  # ['hello', 'world'] - splits on any whitespace, strips too

# Check multiple conditions
s = "hello123"
s.isalpha()   # False (has digits)
s.isdigit()   # False (has letters)
s.isalnum()   # True (all alphanumeric)
s.startswith('hell')  # True
s.endswith('23')      # True

# Replace and count
print("banana".count('a'))          # 3
print("banana".replace('a', 'o'))   # "bonono"
print("hello".center(11, '-'))      # "---hello---"
print("hello".ljust(10, '.'))       # "hello....."
```

### Trick 7: Complex Number for 2D Grid Coordinates

For problems involving grid movement, Python's complex numbers provide elegant coordinate handling:

```python
# Grid coordinates as complex numbers
pos = 0 + 0j  # (0, 0)

# Directions as complex numbers
RIGHT = 1 + 0j
UP = 0 + 1j
LEFT = -1 + 0j
DOWN = 0 - 1j

# Rotate 90 degrees left: multiply by i (imaginary unit)
direction = RIGHT
direction *= 1j  # direction is now UP

# Move
pos += direction

# Get coordinates
row, col = int(pos.real), int(pos.imag)
```

This technique reduces coordinate arithmetic errors in maze and grid problems.

---

## Common Python Mistakes on TCS Platform

**Mistake 1: Incorrect input reading method**
The most common Python error on TCS: writing `n = int(input())` when the input comes from command line arguments. The program runs but reads nothing - producing wrong output or errors.

**Fix:** Check the problem statement. If unsure, write both and use `sys.argv` as default.

**Mistake 2: Integer division confusion**
In Python 3, `/` always returns float. `5 / 2 = 2.5`, not `2`. Use `//` for integer division: `5 // 2 = 2`.

**Fix:** Use `//` everywhere you need integer division results. `n // 2`, `mid = (lo + hi) // 2`, `rem = n // d`.

**Mistake 3: Modifying a list while iterating over it**
```python
# Wrong - may skip elements or cause IndexError
for x in arr:
    if x < 0:
        arr.remove(x)

# Right - iterate over a copy
for x in arr[:]:
    if x < 0:
        arr.remove(x)

# Better - list comprehension
arr = [x for x in arr if x >= 0]
```

**Mistake 4: Using `in` to check membership in a list (O(N)) when set (O(1)) should be used**
```python
# Slow for large lists
if x in large_list:  # O(N) - scans entire list

# Fast
large_set = set(large_list)  # O(N) to create, then...
if x in large_set:  # O(1) - hash lookup
```

**Mistake 5: Forgetting that `sort()` returns None**
```python
# Wrong
result = arr.sort()  # result is None!

# Right - either
arr.sort()           # in-place, returns None
result = sorted(arr) # returns new sorted list
```

**Mistake 6: Mutable default argument**
```python
# Wrong - the default list is shared across calls
def append_to(elem, to=[]):
    to.append(elem)
    return to

# Right
def append_to(elem, to=None):
    if to is None:
        to = []
    to.append(elem)
    return to
```

**Mistake 7: Slow string concatenation in loops**
```python
# Wrong - O(N²) because each + creates a new string
result = ""
for c in arr:
    result += str(c)

# Right - O(N) using join
result = "".join(str(c) for c in arr)
```

---

## Quick Reference: Python Built-ins for Competitive Programming

| Function | Purpose | Example |
|---|---|---|
| `sum(iterable)` | Sum elements | `sum([1,2,3])` = 6 |
| `max(iterable)` | Maximum value | `max([1,5,3])` = 5 |
| `min(iterable)` | Minimum value | `min([1,5,3])` = 1 |
| `sorted(iterable)` | New sorted list | `sorted([3,1,2])` = [1,2,3] |
| `reversed(iterable)` | Reverse iterator | `list(reversed([1,2,3]))` = [3,2,1] |
| `enumerate(iterable)` | Index + value pairs | `for i,v in enumerate(['a','b'])` |
| `zip(*iterables)` | Parallel iteration | `zip([1,2],[3,4])` = (1,3),(2,4) |
| `map(func, iterable)` | Apply function | `list(map(int, ['1','2']))` = [1,2] |
| `filter(func, iterable)` | Filter elements | `list(filter(lambda x:x>0, [-1,2,-3,4]))` |
| `any(iterable)` | True if any True | `any([False, True, False])` = True |
| `all(iterable)` | True if all True | `all([True, True, False])` = False |
| `abs(x)` | Absolute value | `abs(-5)` = 5 |
| `pow(a,b,m)` | Modular exponentiation | `pow(2,10,1000)` = 24 |
| `divmod(a,b)` | Quotient and remainder | `divmod(17,5)` = (3,2) |
| `bin(n)` | Binary string | `bin(10)` = '0b1010' |
| `int(s, base)` | String to int in base | `int('1010',2)` = 10 |
| `chr(n)`, `ord(c)` | ASCII conversion | `ord('A')` = 65, `chr(65)` = 'A' |

| Collection | When to use | Key method |
|---|---|---|
| `list` | Ordered, mutable, indexed | `.append()`, `.sort()`, slicing |
| `tuple` | Ordered, immutable, hashable | Used as dict keys or set elements |
| `set` | Unique elements, O(1) lookup | `.add()`, `|`, `&`, `-` |
| `dict` | Key-value mapping, O(1) lookup | `.get()`, `.items()`, `.keys()` |
| `collections.Counter` | Frequency counting | `.most_common()`, arithmetic |
| `collections.defaultdict` | Dict with default values | `defaultdict(list)`, `defaultdict(int)` |
| `collections.deque` | O(1) both-end operations | `.append()`, `.appendleft()`, `.popleft()` |
| `heapq` (module) | Priority queue | `heappush`, `heappop`, `nlargest` |

---

## Putting It Together: Python for Foundation vs Advanced Coding

**For Foundation (Ninja) coding:**
Python is the best choice for candidates who are not fluent in C/C++. The Foundation level problems - prime check, palindrome, Fibonacci, array operations, string manipulation - are all cleanly solvable in Python with the built-in functions covered in this guide. Time limits at Foundation level are generous enough that Python's speed disadvantage does not cause TLE.

**For Advanced (Digital) coding:**
Use Python when:
- The problem is mathematically oriented (Python's arbitrary precision integers and `math` module are genuine advantages)
- The problem involves string manipulation (Python string methods are faster than C-style loops)
- You are more fluent in Python than C++ (a correct Python solution beats a buggy C++ solution)

Be cautious with Python when:
- The problem has N > 100,000 and an O(N log N) or better algorithm is needed
- The problem involves heavy graph computation with dense edges
- The problem explicitly tests bit manipulation efficiency

The foundation for Python success on TCS is not memorising a list of functions - it is developing the instinct for which Python tool fits each problem. The problems in this guide, practised until their Pythonic solutions are second nature, build that instinct. A candidate who can immediately reach for `Counter` when asked for frequency analysis, `bisect` when asked for binary search in sorted data, `lru_cache` when asked for DP memoisation, and `heapq` when asked for priority operations has genuinely leveraged Python's power for competitive programming.

---

## Extended Problem Collection: Foundation Level

### Problem F-1: Number Pattern Programs

Pattern problems test nested loop control. Python's `range()` and string multiplication make these clean.

**Problem: Print a number pyramid of N rows.**
```
1
1 2
1 2 3
```

**Naive approach:**
```python
import sys
n = int(sys.argv[1])
for i in range(1, n+1):
    row = []
    for j in range(1, i+1):
        row.append(str(j))
    print(' '.join(row))
```

**Pythonic approach:**
```python
import sys
n = int(sys.argv[1])
for i in range(1, n+1):
    print(*range(1, i+1))
```

`*range(1, i+1)` unpacks the range into `print`'s arguments with space separation. Three lines instead of six.

**Star pyramid:**
```python
import sys
n = int(sys.argv[1])
for i in range(1, n+1):
    print(' ' * (n - i) + '*' * (2*i - 1))
```

String multiplication (`'*' * k`) creates a string of k asterisks. This eliminates the inner loops entirely.

**Inverted number triangle:**
```python
import sys
n = int(sys.argv[1])
for i in range(n, 0, -1):
    print(*range(1, i+1))
```

`range(n, 0, -1)` counts down from n to 1.

### Problem F-2: Armstrong Numbers in Range

**Problem statement:** Print all Armstrong numbers between A and B.

**Naive approach:**
```python
import sys

def is_armstrong(n):
    digits = str(n)
    power = len(digits)
    return sum(int(d)**power for d in digits) == n

a, b = int(sys.argv[1]), int(sys.argv[2])
for n in range(a, b+1):
    if is_armstrong(n):
        print(n)
```

**Pythonic - one expression per number:**
```python
import sys
a, b = int(sys.argv[1]), int(sys.argv[2])
print(*[n for n in range(a, b+1)
        if sum(int(d)**len(str(n)) for d in str(n)) == n], sep='\n')
```

Both are correct. The naive version is more readable - prefer readability for Foundation level unless code length is a constraint.

### Problem F-3: Remove Duplicates Preserving Order

**Problem statement:** Remove duplicate elements from an array while preserving insertion order.

**Naive (O(N²)):**
```python
seen = []
for x in arr:
    if x not in seen:
        seen.append(x)
```

**Pythonic (O(N)) using dict.fromkeys:**
```python
import sys
arr = list(map(int, sys.argv[1:]))
unique = list(dict.fromkeys(arr))
print(*unique)
```

`dict.fromkeys(arr)` creates a dictionary with arr elements as keys (removing duplicates) while preserving insertion order (Python dicts maintain insertion order). Converting back to list gives the deduplicated array.

**Alternatively with linked set approach:**
```python
seen = set()
unique = [x for x in arr if not (x in seen or seen.add(x))]
```

The `or seen.add(x)` is a side-effect trick: `seen.add(x)` returns `None` (falsy), so `x in seen or seen.add(x)` evaluates to `False` only after adding x to seen if x wasn't there. This is clever but less readable.

### Problem F-4: Matrix Operations in Python

**Matrix creation and transposition:**
```python
import sys

# Read 3x3 matrix
n = 3
args = list(map(int, sys.argv[1:]))
matrix = [args[i*n:(i+1)*n] for i in range(n)]

# Print original
for row in matrix:
    print(*row)

# Transpose using zip
transposed = [list(row) for row in zip(*matrix)]
print("Transposed:")
for row in transposed:
    print(*row)

# Matrix multiplication (2D x 2D)
def mat_mul(A, B):
    n = len(A)
    C = [[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                C[i][j] += A[i][k] * B[k][j]
    return C
```

**Pythonic transpose:** `zip(*matrix)` transposes the matrix. The `*` unpacks the matrix rows as arguments to `zip`, which zips corresponding columns together. Each zip result is a column of the original = row of the transposed.

### Problem F-5: Find Subarray with Given Sum

**Problem statement:** Find if there exists a contiguous subarray with sum equal to target K.

**O(N) sliding window (for non-negative arrays):**
```python
import sys

target = int(sys.argv[1])
arr = list(map(int, sys.argv[2:]))

left = 0
curr_sum = 0
for right in range(len(arr)):
    curr_sum += arr[right]
    while curr_sum > target and left <= right:
        curr_sum -= arr[left]
        left += 1
    if curr_sum == target:
        print(f"Found: {arr[left:right+1]}")
        break
else:
    print("Not found")
```

**O(N) with prefix sums (handles negative elements):**
```python
from collections import defaultdict
import sys

target = int(sys.argv[1])
arr = list(map(int, sys.argv[2:]))

prefix_sum = 0
seen_sums = defaultdict(list)
seen_sums[0].append(-1)

for i, x in enumerate(arr):
    prefix_sum += x
    complement = prefix_sum - target
    if complement in seen_sums:
        start = seen_sums[complement][0] + 1
        print(f"Found: {arr[start:i+1]}")
        break
    seen_sums[prefix_sum].append(i)
else:
    print("Not found")
```

---

## Extended Problem Collection: Intermediate Level

### Problem I-1: Spiral Matrix Traversal

```python
import sys

# Read NxN matrix
n = int(sys.argv[1])
args = list(map(int, sys.argv[2:]))
matrix = [args[i*n:(i+1)*n] for i in range(n)]

result = []
top, bottom, left, right = 0, n-1, 0, n-1

while top <= bottom and left <= right:
    # Traverse right
    result.extend(matrix[top][left:right+1])
    top += 1
    # Traverse down
    for i in range(top, bottom+1):
        result.append(matrix[i][right])
    right -= 1
    # Traverse left
    if top <= bottom:
        result.extend(reversed(matrix[bottom][left:right+1]))
        bottom -= 1
    # Traverse up
    if left <= right:
        for i in range(bottom, top-1, -1):
            result.append(matrix[i][left])
        left += 1

print(*result)
```

### Problem I-2: Balanced Parentheses Checker

```python
import sys

def is_balanced(s):
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

s = sys.argv[1]
print("Balanced" if is_balanced(s) else "Not Balanced")
```

**Python advantage:** Dictionary lookup `pairs = {')': '(', ...}` makes the matching clean. The `stack[-1]` peek and `stack.pop()` operations are O(1).

### Problem I-3: Longest Common Subsequence

```python
import sys

s1, s2 = sys.argv[1], sys.argv[2]
m, n = len(s1), len(s2)

# Build DP table
dp = [[0] * (n + 1) for _ in range(m + 1)]
for i in range(1, m + 1):
    for j in range(1, n + 1):
        if s1[i-1] == s2[j-1]:
            dp[i][j] = dp[i-1][j-1] + 1
        else:
            dp[i][j] = max(dp[i-1][j], dp[i][j-1])

print(f"LCS length: {dp[m][n]}")

# Trace back to find the actual LCS
lcs = []
i, j = m, n
while i > 0 and j > 0:
    if s1[i-1] == s2[j-1]:
        lcs.append(s1[i-1])
        i -= 1; j -= 1
    elif dp[i-1][j] > dp[i][j-1]:
        i -= 1
    else:
        j -= 1
print(f"LCS: {''.join(reversed(lcs))}")
```

### Problem I-4: Detect Cycle in Undirected Graph

```python
import sys
from collections import defaultdict

args = list(map(int, sys.argv[1:]))
n, m = args[0], args[1]
adj = defaultdict(list)
for i in range(m):
    u, v = args[2 + 2*i], args[3 + 2*i]
    adj[u].append(v)
    adj[v].append(u)

def has_cycle_dfs(node, parent, visited):
    visited.add(node)
    for neighbour in adj[node]:
        if neighbour not in visited:
            if has_cycle_dfs(neighbour, node, visited):
                return True
        elif neighbour != parent:
            return True  # found back edge
    return False

visited = set()
cycle_found = False
for node in range(1, n+1):
    if node not in visited:
        if has_cycle_dfs(node, -1, visited):
            cycle_found = True
            break

print("Cycle detected" if cycle_found else "No cycle")
```

---

## Python vs Other Languages: The Honest Comparison for TCS

### When Python Wins

**Problem: Count frequency of each character in a string.**
- Python: `Counter(s)` - 1 line
- C: 20+ lines with array and loop
- Java: 15+ lines with HashMap

**Problem: Find all prime factors.**
- Python: 6 lines with generator
- C: 12 lines
- Java: 15 lines

**Problem: Sort list of tuples by second element.**
- Python: `sorted(lst, key=lambda x: x[1])` - 1 line
- C: `qsort` with custom comparator - 10+ lines
- Java: `Collections.sort` with Comparator - 5+ lines

**Problem: Compute 100! (factorial of 100).**
- Python: `math.factorial(100)` - exact, 1 line
- C/Java: overflow without big integer library

### When Python Loses

**Problem: Sort 10^6 elements in under 1 second.**
- Python `sorted()` takes ~1.5-2 seconds for 10^6 elements
- C++ `std::sort` takes ~0.1-0.2 seconds
- If the time limit is 1 second, Python fails

**Problem: BFS/DFS on a graph with 10^5 nodes and 5×10^5 edges.**
- Python: ~2-3 seconds
- C++: ~0.2-0.3 seconds
- Digital-level graph problems with tight limits may require C++

**Problem: Count set bits for 10^9 numbers.**
- Python loop: slow
- C++ `__builtin_popcount`: hardware instruction, extremely fast

**The honest recommendation:** Python is the right choice for most TCS Foundation (Ninja) problems. For Digital Advanced problems, benchmark your Python solution against the time limit. If it passes on the sample test cases in under 1 second locally, it will likely pass. If it takes 2-3 seconds, switch to C++ for that problem.

---

## Recursive Thinking with Python

Python's recursion limit is 1,000 by default. For problems requiring deep recursion (N > 1,000), either:
1. Use an iterative approach
2. Increase the recursion limit: `sys.setrecursionlimit(10000)`

```python
import sys
sys.setrecursionlimit(100000)  # increase if needed

# Tower of Hanoi
def hanoi(n, from_peg, to_peg, aux_peg):
    if n == 1:
        print(f"Move disk 1 from {from_peg} to {to_peg}")
        return
    hanoi(n-1, from_peg, aux_peg, to_peg)
    print(f"Move disk {n} from {from_peg} to {to_peg}")
    hanoi(n-1, aux_peg, to_peg, from_peg)

n = int(sys.argv[1])
hanoi(n, 'A', 'C', 'B')
```

### Memoised Recursion vs Bottom-Up DP

For TCS problems requiring DP, both approaches work. The memoised recursive approach with `lru_cache` is often faster to write and easier to reason about:

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def dp(state1, state2):  # state must be hashable (tuples, not lists)
    # base case
    if state1 == 0:
        return 0
    # recursive case
    return 1 + dp(state1 - 1, state2)
```

**Key requirement:** All arguments to a `lru_cache`-decorated function must be hashable. Use tuples instead of lists when passing sequences.

---

## Python Input/Output: Extended Patterns

### Reading Until End of File

```python
import sys

# Method 1: read all at once
data = sys.stdin.read().split()
nums = list(map(int, data))

# Method 2: read line by line
for line in sys.stdin:
    n = int(line.strip())
    print(n * n)
```

### Multiple Test Cases

```python
import sys

# Input: first line T (number of test cases), then T lines each with one number
lines = sys.stdin.read().split('\n')
t = int(lines[0])
for i in range(1, t+1):
    n = int(lines[i])
    print(n * n)
```

Or using command line:
```python
import sys

t = int(sys.argv[1])
for i in range(t):
    n = int(sys.argv[i + 2])
    print(n * n)
```

### Fast Output: sys.stdout.write

For programs that output many lines, `sys.stdout.write` is faster than `print`:

```python
import sys

output = []
for i in range(1000):
    output.append(str(i * i))

sys.stdout.write('\n'.join(output) + '\n')
```

Building a list and joining at the end is much faster than calling `print` in a loop for large outputs.

---

## The Python Competitive Programming Mindset

The difference between a Python user and a Python competitive programmer is not vocabulary size - it is reflex. A competitive programmer sees a problem and immediately connects it to the right tool without conscious deliberation.

**Build these reflexes through deliberate practice:**

| Problem type | Reflex |
|---|---|
| "Count frequency" | `Counter()` |
| "Find unique elements" | `set()` |
| "Need default value for missing key" | `defaultdict()` |
| "Process both ends efficiently" | `deque()` |
| "Find k largest/smallest" | `heapq.nlargest(k)` / `heapq.nsmallest(k)` |
| "Sorted insertion" | `bisect.insort()` |
| "Generate all subsets" | Power set with bitmasking or `combinations()` |
| "All permutations" | `itertools.permutations()` |
| "DP with recursion" | `@lru_cache` |
| "Parallel iteration" | `zip()` |
| "Index + value" | `enumerate()` |
| "Flatten nested list" | `[x for row in matrix for x in row]` |
| "Check any/all condition" | `any()` / `all()` |
| "Reverse anything" | `[::-1]` for sequence, `reversed()` for iterator |

Practising the problems in this guide - and specifically practicing identifying which Python tool fits each problem before looking at the solution - builds these reflexes. The goal is to reach a state where writing Pythonic TCS solutions feels natural rather than effortful.

Python's power for TCS coding is not just about shorter code. It is about reduced cognitive load - fewer lines to write means fewer opportunities for bugs, and cleaner code means clearer thinking during the exam. The candidate who reaches for `Counter` instead of manually building a frequency dictionary has more mental bandwidth left for the algorithm design that actually solves the problem.

That clarity under time pressure is what makes Python preparation worth doing properly, and what makes the techniques in this guide worth practicing until they are fluent.

---

## Extended Mathematical Programs

### Problem EM-1: Check If N Is a Perfect Square Without sqrt()

```python
import sys

def is_perfect_square(n):
    if n < 0: return False
    if n == 0: return True
    # Binary search for the integer square root
    lo, hi = 1, n
    while lo <= hi:
        mid = (lo + hi) // 2
        sq = mid * mid
        if sq == n: return True
        elif sq < n: lo = mid + 1
        else: hi = mid - 1
    return False

n = int(sys.argv[1])
if is_perfect_square(n):
    # Find the square root using the same binary search
    lo, hi = 1, n
    while lo <= hi:
        mid = (lo + hi) // 2
        if mid * mid == n:
            print(f"{n} is a perfect square. Square root: {mid}")
            break
        elif mid * mid < n: lo = mid + 1
        else: hi = mid - 1
else:
    print(f"{n} is not a perfect square")
```

**Python alternative using integer square root (Python 3.8+):**
```python
import math
import sys

n = int(sys.argv[1])
root = math.isqrt(n)  # integer square root - largest integer <= sqrt(n)
if root * root == n:
    print(f"Perfect square. Root: {root}")
else:
    print("Not a perfect square")
```

`math.isqrt()` is the cleanest approach - exact integer square root without floating point errors.

### Problem EM-2: Collatz Sequence

**Problem statement:** Given N, print the Collatz sequence (if N is even: N/2; if odd: 3N+1; stop at 1).

```python
import sys

n = int(sys.argv[1])
sequence = [n]
while n != 1:
    if n % 2 == 0:
        n = n // 2
    else:
        n = 3 * n + 1
    sequence.append(n)

print(*sequence)
print(f"Steps: {len(sequence) - 1}")
```

**Pythonic with list:**
```python
import sys

def collatz(n):
    seq = [n]
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        seq.append(n)
    return seq

seq = collatz(int(sys.argv[1]))
print(*seq)
print(len(seq) - 1)
```

**Ternary expression `n // 2 if n % 2 == 0 else 3 * n + 1`** replaces the if-else block in one line.

### Problem EM-3: Base Conversion

**Convert from decimal to any base (2-16):**
```python
import sys

def to_base(n, base):
    if n == 0: return "0"
    digits = "0123456789ABCDEF"
    result = ""
    while n > 0:
        result = digits[n % base] + result
        n //= base
    return result

n = int(sys.argv[1])
base = int(sys.argv[2])
print(f"Decimal {n} in base {base}: {to_base(n, base)}")

# Python built-ins for common bases:
print(f"Binary: {bin(n)[2:]}")    # bin() returns '0b101010', [2:] removes prefix
print(f"Octal: {oct(n)[2:]}")     # oct() returns '0o52', [2:] removes prefix
print(f"Hex: {hex(n)[2:].upper()}")  # hex() returns '0x2a', [2:] removes prefix
```

**Convert from any base to decimal:**
```python
n_str = "1010"  # binary
base = 2
decimal = int(n_str, base)  # Python's int() accepts a base parameter
print(decimal)  # 10
```

`int(string, base)` - the second argument to `int()` specifies the base. `int("FF", 16)` = 255. `int("777", 8)` = 511.

### Problem EM-4: Catalan Numbers

**Catalan numbers** count the number of valid bracket sequences, binary tree structures, and many other combinatorial objects. C(n) = (2n choose n) / (n+1).

```python
import sys
from math import comb

n = int(sys.argv[1])
# Direct formula
catalan = comb(2*n, n) // (n+1)
print(f"Catalan({n}) = {catalan}")

# DP approach
def catalan_dp(n):
    if n <= 1: return 1
    cat = [0] * (n + 1)
    cat[0] = cat[1] = 1
    for i in range(2, n+1):
        for j in range(i):
            cat[i] += cat[j] * cat[i-1-j]
    return cat[n]

print(f"Catalan({n}) via DP = {catalan_dp(n)}")
```

---

## Advanced Data Structures with Python

### Implementing a Trie in Python

```python
import sys
from collections import defaultdict

class TrieNode:
    def __init__(self):
        self.children = defaultdict(TrieNode)
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word:
            node = node.children[char]
        node.is_end = True

    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end

    def starts_with(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True

    def count_words_with_prefix(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return 0
            node = node.children[char]
        # Count all words below this node
        return self._count_below(node)

    def _count_below(self, node):
        count = 1 if node.is_end else 0
        for child in node.children.values():
            count += self._count_below(child)
        return count

# Usage
trie = Trie()
words = sys.argv[1:]
for word in words:
    trie.insert(word)

# Test
print(trie.search(words[0]))  # True
print(trie.starts_with(words[0][:2]))  # True
print(trie.count_words_with_prefix(words[0][:1]))
```

### Union-Find (Disjoint Set Union) in Python

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n + 1))
        self.rank = [0] * (n + 1)
        self.components = n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # path compression
        return self.parent[x]

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False  # already in same component
        # Union by rank
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        self.components -= 1
        return True

    def same_component(self, x, y):
        return self.find(x) == self.find(y)

# Usage: solve connected components with queries
import sys
args = list(map(int, sys.argv[1:]))
n, m = args[0], args[1]
uf = UnionFind(n)

for i in range(m):
    u, v = args[2 + 2*i], args[3 + 2*i]
    uf.union(u, v)

print(f"Connected components: {uf.components}")
```

---

## Python Debugging Techniques for TCS Coding

### Print Debugging

```python
import sys

def solve(arr, k):
    # Debugging: print intermediate state
    print(f"DEBUG: arr={arr}, k={k}", file=sys.stderr)  # stderr doesn't affect output evaluation

    total = sum(arr)
    return total >= k

arr = [int(x) for x in sys.argv[2:]]
k = int(sys.argv[1])
print("Yes" if solve(arr, k) else "No")
```

`file=sys.stderr` sends debug output to the error stream, which does not affect the stdout comparison that TCS iON uses for evaluation.

### Assert Statements for Testing

```python
def is_prime(n):
    if n <= 1: return False
    if n == 2: return True
    if n % 2 == 0: return False
    return all(n % i != 0 for i in range(3, int(n**0.5) + 1, 2))

# Test cases
assert is_prime(2) == True
assert is_prime(17) == True
assert is_prime(1) == False
assert is_prime(4) == False
assert is_prime(97) == True
print("All tests passed")
```

Running locally with assertions before submission catches logic errors early.

---

## Comprehensive Practice Problem Set

### 10 Python-Specific Problems

**P1:** Read a sentence (multiple words as separate args). Print each word reversed, maintaining word order. ("hello world" → "olleh dlrow")

```python
import sys
words = sys.argv[1:]
print(*[w[::-1] for w in words])
```

**P2:** Given N integers, find the two numbers whose product is maximum.

```python
import sys
arr = sorted(map(int, sys.argv[1:]))
# Maximum product: either two largest positive or two most negative
n = len(arr)
print(max(arr[0]*arr[1], arr[-1]*arr[-2]))
```

**P3:** Find the most common element in a list.

```python
import sys
from collections import Counter
arr = list(map(int, sys.argv[1:]))
print(Counter(arr).most_common(1)[0][0])
```

**P4:** Check if a number is a happy number (repeatedly sum squares of digits; reaches 1 = happy, loops at non-1 = unhappy).

```python
import sys

def is_happy(n):
    seen = set()
    while n != 1:
        if n in seen: return False
        seen.add(n)
        n = sum(int(d)**2 for d in str(n))
    return True

print("Happy" if is_happy(int(sys.argv[1])) else "Not Happy")
```

**P5:** Given a list of integers, find the subarray with the maximum product.

```python
import sys
arr = list(map(int, sys.argv[1:]))
max_p = min_p = result = arr[0]
for x in arr[1:]:
    candidates = (x, max_p * x, min_p * x)
    max_p = max(candidates)
    min_p = min(candidates)
    result = max(result, max_p)
print(result)
```

**P6:** Find the longest run of consecutive integers in an unsorted list.

```python
import sys
from collections import Counter
arr = list(map(int, sys.argv[1:]))
num_set = set(arr)
best = 0
for n in num_set:
    if n - 1 not in num_set:  # start of a sequence
        length = 1
        while n + length in num_set:
            length += 1
        best = max(best, length)
print(best)
```

**P7:** Rotate a string K positions to the right.

```python
import sys
s = sys.argv[1]
k = int(sys.argv[2]) % len(s)
print(s[-k:] + s[:-k])
```

**P8:** Check if one string is a rotation of another.

```python
import sys
s1, s2 = sys.argv[1], sys.argv[2]
print("Rotation" if len(s1) == len(s2) and s2 in s1 + s1 else "Not Rotation")
```

Concatenating `s1` with itself creates a string containing all rotations of `s1` as substrings. If `s2` is a rotation, it appears as a substring of `s1+s1`.

**P9:** Given a list of words, find words that are prefixes of other words in the list.

```python
import sys
words = sys.argv[1:]
word_set = set(words)
prefixes = [w for w in words
            if any(other.startswith(w) and other != w for other in word_set)]
print(*sorted(set(prefixes)))
```

**P10:** Find the minimum number of coins to make change for amount N (greedy works for standard coin denominations).

```python
import sys
amount = int(sys.argv[1])
coins = sorted(map(int, sys.argv[2:]), reverse=True)
count = 0
for coin in coins:
    while amount >= coin:
        amount -= coin
        count += 1
print(count if amount == 0 else -1)
```

**Note:** Greedy only works for specific coin systems (e.g., Indian/US coins). For arbitrary denominations, use DP (coin change problem with `lru_cache` as shown earlier).

---

## Python for the TCS Traits Section

Some TCS NQT platforms include a Traits/Behavioural assessment section. While not a coding section, Python skills indirectly relate to Traits in a specific way: Python's readability emphasis aligns with communication clarity, which is a valued trait. Candidates who approach problems clearly (state what you are solving, how you are solving it, what the output means) demonstrate the same structured communication that Python code itself models.

The connection is philosophical: Python's design philosophy ("There should be one obvious way to do it", "Readability counts") reflects the same values TCS interviewers look for - clear thinking, direct communication, and elegant solutions over clever ones. Practising Python trains more than coding skill; it trains a problem-solving approach that serves well in technical communication too.

---

## Final Reference: Python on TCS in One Page

**Platform:** TCS iON, Python 3, GCC-equivalent environment.

**Input:** `sys.argv[1], sys.argv[2]...` for command line; `input()` or `sys.stdin` for standard input.

**Output:** `print()` with exact format matching. `*list` unpacks to space-separated. `'\n'.join()` for newline-separated.

**Speed:** Fast enough for N ≤ 50,000 with O(N log N) algorithms. Use built-in functions (implemented in C) over Python loops for maximum speed.

**Strengths:** Arbitrary precision integers, expressive built-ins (`Counter`, `defaultdict`, `deque`, `heapq`, `itertools`), clean DP with `lru_cache`, concise string operations.

**The five built-ins to know cold:**
1. `Counter(iterable)` - instant frequency counting
2. `sorted(iterable, key=...)` - versatile sorting
3. `defaultdict(type)` - dict with default values
4. `heapq.nlargest/nsmallest(k, iterable)` - k-th element
5. `@lru_cache(maxsize=None)` - instant memoisation

**The five one-liners to know cold:**
1. `s[::-1]` - reverse any sequence
2. `' '.join(map(str, arr))` - list to space-separated string
3. `list(map(int, sys.argv[1:]))` - all args as integer list
4. `[x for x in arr if condition(x)]` - filtered list
5. `pow(base, exp, mod)` - modular exponentiation

These are the tools. The problems in this guide are the practice. Together, they prepare you for Python-based TCS coding at Foundation level and beyond.

---

## String Problem Deep Dive: Python vs Other Languages

The string section deserves additional depth because Python's string advantages are the most dramatic versus C/C++ and Java.

### What Python Gives You for Free

**Slicing:** `s[start:stop:step]` - any substring, any stride, reversed.
```python
s = "Hello, World!"
print(s[7:12])      # "World"
print(s[::2])       # "Hlo ol!"  (every other character)
print(s[::-1])      # "!dlroW ,olleH"  (reversed)
print(s[-5:])       # "orld!"  (last 5 characters)
```

In C, extracting a substring requires: declare a new char array, copy characters in a loop, add null terminator. In Python: one slice.

**String methods:**
```python
s = "  Hello, World!  "
print(s.strip())              # "Hello, World!" (remove whitespace)
print(s.lower())              # "  hello, world!  "
print(s.upper())              # "  HELLO, WORLD!  "
print(s.replace(',', ';'))    # replace all occurrences
print(s.count('l'))           # count occurrences: 3
print(s.find('World'))        # first occurrence index: 9
print(s.split(', '))          # ['  Hello', 'World!  ']
print('hello'.center(11, '-'))# '---hello---'
print('hello'.startswith('h'))# True
print('hello'.endswith('lo')) # True
print(','.join(['a','b','c'])) # 'a,b,c'
```

Each of these is a clean one-liner. Equivalent C code for any of them ranges from 5-20 lines.

### Problem STR-DEEP-1: Find All Substrings That Are Palindromes

```python
import sys

def all_palindrome_substrings(s):
    palindromes = set()
    n = len(s)
    for i in range(n):
        # Odd length
        lo, hi = i, i
        while lo >= 0 and hi < n and s[lo] == s[hi]:
            palindromes.add(s[lo:hi+1])
            lo -= 1; hi += 1
        # Even length
        lo, hi = i, i+1
        while lo >= 0 and hi < n and s[lo] == s[hi]:
            palindromes.add(s[lo:hi+1])
            lo -= 1; hi += 1
    return sorted(palindromes)

s = sys.argv[1]
result = all_palindrome_substrings(s)
print(f"Count: {len(result)}")
for p in result:
    print(p)
```

### Problem STR-DEEP-2: String Compression (Run Length Encoding)

**Problem statement:** Compress a string using run-length encoding. "aaabbbccddddee" → "a3b3c2d4e2".

**Naive:**
```python
import sys

def rle(s):
    if not s: return ""
    result = []
    count = 1
    for i in range(1, len(s)):
        if s[i] == s[i-1]:
            count += 1
        else:
            result.append(s[i-1] + str(count))
            count = 1
    result.append(s[-1] + str(count))
    return ''.join(result)

print(rle(sys.argv[1]))
```

**Pythonic using itertools.groupby:**
```python
import sys
from itertools import groupby

def rle(s):
    return ''.join(f"{char}{sum(1 for _ in group)}" 
                   for char, group in groupby(s))

print(rle(sys.argv[1]))
```

`groupby(s)` groups consecutive identical characters. For "aaabbb", it yields ('a', iterator of 'aaa') and ('b', iterator of 'bbb'). The inner `sum(1 for _ in group)` counts the group size.

---

## Advanced List Operations

### Problem LST-DEEP-1: Sliding Window Maximum

**Problem statement:** For an array and window size K, find the maximum in each sliding window.

```python
import sys
from collections import deque

def sliding_max(arr, k):
    dq = deque()  # stores indices of useful elements
    result = []

    for i, x in enumerate(arr):
        # Remove elements outside window
        while dq and dq[0] < i - k + 1:
            dq.popleft()
        # Remove smaller elements from back
        while dq and arr[dq[-1]] < x:
            dq.pop()
        dq.append(i)
        # Window is complete
        if i >= k - 1:
            result.append(arr[dq[0]])
    return result

k = int(sys.argv[1])
arr = list(map(int, sys.argv[2:]))
print(*sliding_max(arr, k))
```

**Time complexity:** O(N) - each element is added and removed at most once from the deque.

### Problem LST-DEEP-2: Majority Element

**Problem statement:** Find the element that appears more than N/2 times (guaranteed to exist). Boyer-Moore voting algorithm.

```python
import sys

def majority(arr):
    candidate, count = arr[0], 1
    for x in arr[1:]:
        if count == 0:
            candidate, count = x, 1
        elif x == candidate:
            count += 1
        else:
            count -= 1
    return candidate

arr = list(map(int, sys.argv[1:]))
print(majority(arr))
```

**Why this works:** The majority element's "votes" cannot be cancelled out by the minority elements because it has more than half. The counter tracks the "net lead" of the current candidate.

**Verification (if majority not guaranteed):**
```python
result = majority(arr)
if arr.count(result) > len(arr) // 2:
    print(result)
else:
    print("No majority element")
```

### Problem LST-DEEP-3: Next Greater Element

**Problem statement:** For each element in an array, find the next element to its right that is greater. If none, print -1.

```python
import sys

def next_greater(arr):
    n = len(arr)
    result = [-1] * n
    stack = []  # monotonic stack: stores indices

    for i in range(n):
        # Pop all elements smaller than current - current is their next greater
        while stack and arr[stack[-1]] < arr[i]:
            result[stack.pop()] = arr[i]
        stack.append(i)

    return result

arr = list(map(int, sys.argv[1:]))
print(*next_greater(arr))
```

**Monotonic stack pattern:** Maintain a stack where elements (or their indices) are in decreasing order. When a larger element arrives, it is the "next greater" for all smaller elements on the stack.

---

## Frequently Asked Questions: Python on TCS

**"Is Python 2 or Python 3 supported on TCS iON?"**
Python 3 only. All code in this guide is Python 3. The most practical differences: `print()` is a function (not a statement), `input()` returns a string, and `/` always returns float.

**"Can I use numpy for mathematical operations?"**
numpy is generally not available on TCS iON. Stick to the Python standard library (math, cmath, decimal, fractions) and the built-in functions demonstrated in this guide. The `math` module functions (`factorial`, `comb`, `gcd`, `isqrt`, `log`, `sqrt`) cover all TCS mathematical requirements.

**"My Python solution gives correct output for the sample test case but wrong answer on hidden test cases. Why?"**
Common causes:
- Edge cases not handled (n=0, n=1, empty array, negative numbers)
- Integer overflow - but Python doesn't overflow! Check if the expected output is actually a very large number that you are representing incorrectly (float instead of int, for example)
- Off-by-one in array index or range
- Output format mismatch (extra space, missing newline, wrong separator)

**"Should I use recursion or iteration for DP problems?"**
For Python, the `@lru_cache` recursive approach is often cleaner and equally efficient. The recursion limit (default 1000) is only a concern for problems with state space depth > 1000. For those, use iterative bottom-up DP or increase the recursion limit with `sys.setrecursionlimit(10000)`.

**"How do I read multiple numbers from one line?"**
`a, b, c = map(int, input().split())` reads three space-separated integers from one line.
`nums = list(map(int, input().split()))` reads an unknown number of integers from one line.

**"My code uses `input()` but the TCS problem uses command line. Should I rewrite everything?"**
The change is minimal. Replace `n = int(input())` with `n = int(sys.argv[1])`. Replace `a, b = map(int, input().split())` with `a, b = int(sys.argv[1]), int(sys.argv[2])`. The logic itself is unchanged.

**"Is there a recursion depth limit in Python on TCS iON?"**
The default is 1000. You can increase it at the start of your program:
```python
import sys
sys.setrecursionlimit(100000)
```
Set this high enough for your problem's recursion depth but not unnecessarily high (very high limits consume stack memory).

**"Can I use type hints and f-strings?"**
Type hints (Python 3.5+) and f-strings (Python 3.6+) are available if TCS iON uses Python 3.6 or later, which is standard. Both features work normally and f-strings are strongly recommended for formatted output.

---

## One Final Program: Bringing It All Together

This final program demonstrates multiple Python strengths in a single solution.

**Problem:** Given a list of student records (name and marks pairs), compute and display:
1. Class average
2. Highest and lowest scoring students
3. Grade distribution (A/B/C/D/F counts)
4. Students above average, sorted by marks descending

```python
import sys
from collections import Counter

# Read: name1 marks1 name2 marks2 ...
args = sys.argv[1:]
students = [(args[i], int(args[i+1])) for i in range(0, len(args), 2)]

# Class statistics
marks = [m for _, m in students]
average = sum(marks) / len(marks)
top = max(students, key=lambda s: s[1])
bottom = min(students, key=lambda s: s[1])

# Grade assignment function
def grade(m):
    if m >= 90: return 'A'
    if m >= 75: return 'B'
    if m >= 60: return 'C'
    if m >= 50: return 'D'
    return 'F'

grade_counts = Counter(grade(m) for m in marks)

# Students above average
above_avg = sorted(
    [(n, m) for n, m in students if m > average],
    key=lambda s: -s[1]  # descending by marks
)

# Output
print(f"Class Average: {average:.1f}")
print(f"Top Student: {top[0]} ({top[1]})")
print(f"Lowest Student: {bottom[0]} ({bottom[1]})")
print(f"Grade Distribution: {dict(sorted(grade_counts.items()))}")
print(f"\nAbove Average:")
for name, score in above_avg:
    print(f"  {name}: {score} ({grade(score)})")
```

This program uses: list comprehension, `max/min` with key, `Counter`, generator expression, `sorted` with lambda key, f-strings with format spec, and dictionary operations. Every technique in this guide appears in a realistic problem context.

Python, practised to the level this guide describes, is a genuine competitive advantage in TCS coding. Not because it is faster than C++, but because it is faster to write correctly - which is the real bottleneck for most TCS candidates.

---

## Python Template: Ready-to-Use for TCS

### Standard Template (Command Line Input)

```python
import sys
from collections import Counter, defaultdict, deque
from itertools import combinations, permutations
from functools import lru_cache
from math import gcd, sqrt, isqrt, factorial, comb
import heapq

def solve():
    # Read command line arguments
    args = sys.argv[1:]

    # For single integer input
    # n = int(args[0])

    # For multiple integer inputs
    # a, b = int(args[0]), int(args[1])

    # For array input: n followed by n numbers
    # n = int(args[0])
    # arr = [int(args[i+1]) for i in range(n)]

    # Your solution here

    # Output
    # print(result)
    # print(*arr)  # space-separated array

if __name__ == "__main__":
    solve()
```

### Standard Template (Standard Input)

```python
import sys
from collections import Counter, defaultdict, deque
from functools import lru_cache
from math import gcd, isqrt, factorial, comb
import heapq

# Faster input
input = sys.stdin.readline

def solve():
    # Single integer
    # n = int(input())

    # Multiple integers on one line
    # a, b = map(int, input().split())

    # Array of N integers
    # n = int(input())
    # arr = list(map(int, input().split()))

    # Or all on one line
    # arr = list(map(int, input().split()))

    pass

t = 1
# t = int(input())  # uncomment for multiple test cases
for _ in range(t):
    solve()
```

### Mini-Template for Short Programs

```python
import sys
from collections import Counter
from math import gcd, isqrt

n = int(sys.argv[1])
arr = [int(x) for x in sys.argv[2:]]

# solution
print(sum(arr))
```

---

## Performance Benchmarks: What Python Can Handle on TCS

Understanding the approximate performance boundaries helps you decide when Python is safe and when to switch to C++.

| Algorithm complexity | Max N for Python in ~1 second |
|---|---|
| O(1) | Unlimited |
| O(log N) | Unlimited |
| O(N) | ~10,000,000 (10^7) |
| O(N log N) | ~1,000,000 (10^6) with tight constant |
| O(N√N) | ~100,000 (10^5) |
| O(N²) | ~5,000 - 10,000 |
| O(N³) | ~200 - 300 |
| O(2^N) | N ≤ 20 |
| O(N!) | N ≤ 10-12 |

**For TCS Foundation Coding:** Problems typically have N ≤ 10,000. O(N²) solutions in Python are safe.

**For TCS Digital Advanced Coding:** Problems may have N up to 10^5 or 10^6. O(N log N) Python solutions are at the limit. Use C++ for safety on large-N problems.

**The practical test:** Run your Python solution locally with the sample input. If it completes in under 0.2 seconds, it will comfortably pass TCS's time limits. If it takes 0.5-1 second, it might fail on larger hidden test cases.

---

## The Learning Path: From Python Beginner to TCS-Ready

**Stage 1 (Days 1-5): Input/Output and Basic Operations**
- Command line argument reading with sys.argv
- Standard input with input() and map()
- Output formatting with print() and f-strings
- Basic arithmetic, conditionals, loops

**Stage 2 (Days 6-12): Built-in Mastery**
- List comprehensions and generator expressions
- sorted(), min(), max(), sum() with key functions
- String methods: split, join, strip, replace, find
- Counter, defaultdict, deque from collections

**Stage 3 (Days 13-20): Problem-Solving Patterns**
- Two-pointer technique
- Sliding window
- Hash map for O(N) lookups
- Stack for bracket matching and monotonic problems
- Recursive thinking with lru_cache

**Stage 4 (Days 21-28): Advanced Techniques**
- DP with lru_cache
- Heap for priority queue problems
- bisect for binary search in sorted arrays
- itertools for combinations and permutations
- Graph BFS/DFS with defaultdict and deque

By the end of Stage 4, a Python-focused TCS candidate is prepared for all Foundation coding problems and most Digital coding problems that don't require C++ speed. The journey is approximately four weeks of daily 1-2 hour practice - achievable alongside regular college academics or work.

Python's learning curve for TCS coding is genuinely shorter than C++ because the language handles so much plumbing automatically. A candidate who spends those four weeks fully engaged with the techniques in this guide arrives at TCS iON with real Python fluency, not just familiarity with syntax. That fluency translates directly to correct solutions under time pressure.
