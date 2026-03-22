---
layout: post
title: "TCS NQT Coding: Crack the Advanced Round"
page_title: "TCS NQT Advanced Coding Questions - Complete Guide with Solutions in C++, Java, and Python"
date: 2023-08-19
categories: ["Industry"]
tags: ["TCS NQT coding", "TCS coding questions", "TCS programming", "TCS advanced coding", "TCS NQT solutions"]
excerpt: "Comprehensive TCS NQT coding preparation with topic-wise strategies, original practice problems, and solutions in three languages."
image: "/assets/images/blog/blog-08.webp"
reading_time: 61
author: "Insight Crunch Team"
render_with_liquid: false
last_updated: 2026-03-22
---
The TCS NQT Advanced Coding section is where the hiring funnel narrows sharply. Every candidate who sits in the test hall has already cleared the eligibility bar - but the Advanced Coding section separates TCS Ninja from TCS Digital, and TCS Digital from TCS Prime. Two or three programming problems, ninety minutes, a browser-based IDE, and hidden test cases whose results you will not see until after the exam ends. For candidates who have not specifically prepared for this format, it is a brutal surprise. For candidates who understand exactly how the section is structured, what problem types to expect, and how to write code that passes not just visible test cases but all the edge cases running invisibly in the background - it is an opportunity to differentiate themselves completely.

![TCS Guide](/assets/images/blog/blog-08.webp)

This guide covers everything: the TCS iON coding environment mechanics, how test case scoring actually works, language-specific considerations, a complete topic-by-topic preparation roadmap with original problems and full solutions in C++, Java, and Python, and a thirty-day preparation plan. Whether you are starting from scratch or polishing an already solid foundation, the guidance here is calibrated specifically to the TCS NQT Advanced Coding format.

---

## The TCS iON Coding Environment

### Interface and Navigation

The TCS iON coding interface presents the problem statement on the left half of the screen and an integrated code editor on the right. Below the editor are three controls: a language selector dropdown, a "Run" button that executes code against visible sample test cases, and a "Submit" button that evaluates code against all test cases including hidden ones.

The editor is a browser-based code input field with basic syntax highlighting. It does not have the advanced features of a desktop IDE - no auto-complete, no inline error highlighting as you type, and no integrated debugger. This means you cannot rely on IDE-assisted development. You need to write correct code mentally and verify it through manual trace-through before running.

The interface has a problem-level timer displaying the remaining time across all problems. Unlike the Foundation Section where each sub-section has its own locked timer, the ninety minutes in the Coding section is a shared pool across all problems. You can switch between problems at any time.

### The Eclipse-Based Compiler Behaviour

The TCS iON platform uses a compiler infrastructure with roots in Eclipse-based tooling. Key behavioural characteristics that affect how you write code:

**Standard input/output model:** Problems receive input through standard input (stdin) and expect output through standard output (stdout). In Java, this means `Scanner` for input and `System.out.println` for output. In Python, `input()` and `print()`. In C/C++, `scanf`/`cin` and `printf`/`cout`.

**No external libraries:** Only the standard library of the selected language is available. Python's `numpy`, `pandas`, or any third-party package is not available. Java's `java.util.*` and `java.io.*` are available; no external JAR files.

**Class naming in Java:** The class containing your `main` method must be named exactly `Main` (capital M) in most TCS iON configurations. Using any other class name as the entry point causes a compilation failure even if the code is logically correct.

**Single file submission:** All your code must be in a single file. You cannot split across multiple files.

### Why Python Runs Slower on the TCS Compiler

Python is an interpreted language - each line is parsed and executed at runtime rather than compiled to machine code in advance. On the TCS iON platform, this interpretation overhead is compounded by the compilation infrastructure's overhead for launching the Python runtime environment itself.

The practical implication: Python solutions for computationally intensive problems (large sorting operations, deep recursion, graph traversal over thousands of nodes) may receive a Time Limit Exceeded (TLE) verdict on hidden test cases even when the algorithm is correct and would pass on a local machine.

Mitigation strategies for Python candidates:
- Use `sys.stdin.readline()` instead of `input()` for faster input reading when multiple lines of input are expected
- Avoid recursion depth exceeding approximately 1000 (Python's default recursion limit) - convert recursive solutions to iterative where possible
- Prefer built-in functions (sorted(), max(), min(), sum()) over hand-coded equivalents - built-in functions are implemented in C and run significantly faster
- Use `sys.setrecursionlimit(100000)` at the top of the file if deep recursion is unavoidable

### Supported Languages

The TCS iON Advanced Coding section supports C, C++, Java, and Python in all cycles. JavaScript support has been present in select cycles. The four primary languages cover the needs of virtually all candidates:

**C++** is the fastest runtime language available. STL containers (vector, map, set, unordered_map, priority_queue, deque) are all available and should be used freely. `#include <bits/stdc++.h>` with `using namespace std;` is accepted and provides the full STL. Use `long long` instead of `int` for any quantity that might exceed 2 billion.

**Java** offers fast runtime and comprehensive standard library. `java.util.ArrayList`, `HashMap`, `PriorityQueue`, `Arrays`, and `Collections` cover most data structure needs. Read input with `BufferedReader` and `Integer.parseInt` for large inputs (faster than `Scanner`). Output with `System.out.println` or `PrintWriter` flushed at the end.

**Python** offers the most concise code. `collections.deque` for efficient queue/deque operations. `heapq` for priority queue. `collections.Counter` and `collections.defaultdict` for frequency counting. `functools.lru_cache` for automatic memoisation.

**C** is available but generally not recommended unless you are already highly proficient - the lack of STL means implementing data structures manually, which consumes significant time.

---

## How Test Cases and Scoring Work

### Visible vs Hidden Test Cases

Each problem comes with 2-3 visible sample test cases shown in the problem statement. These are the inputs and expected outputs you can see. When you click "Run," your code executes against these visible cases and shows you whether your output matches the expected output.

The problem is also evaluated against a set of hidden test cases - typically 8-15 cases that are not shown to you. These hidden cases specifically probe:

- Boundary conditions (empty input, single element, maximum input size)
- Edge cases (all elements equal, already sorted input, negative numbers if applicable)
- Large inputs that expose time complexity weaknesses
- Non-obvious scenarios the problem setter chose to include

You cannot see the results of hidden test cases during the exam. Your score for each problem is determined by how many of the total test cases (visible + hidden) your code passes.

### Partial Credit Scoring

This is one of the most strategically important features of the TCS NQT Coding section. If your code passes 7 of 10 total test cases, you receive 70% of that problem's marks. This has several implications:

**A brute force solution that passes simple cases has positive value.** If you cannot implement the optimal O(n log n) solution but can implement a correct O(n²) brute force, submit it. It will pass the smaller test cases and likely fail the large-input cases due to TLE. But 5 out of 10 test cases passed is meaningfully better than 0 out of 10.

**Always submit something.** A blank IDE submission scores zero. A solution that handles the base case and simple inputs scores partial credit. Always submit the best solution you have, even if incomplete.

**Fix visible test case failures before submitting.** If your code fails a visible test case, it is almost certainly failing several hidden cases too due to the same bug. Fix the visible failure before submitting.

### The Scoring Mechanism

TCS does not publish the exact mark distribution between Problem 1 and Problem 2 (or 3 if present). Based on candidate experiences across multiple cycles, the approximate weighting is:

- Problem 1 (Easy): approximately 30-35% of the coding section marks
- Problem 2 (Medium-Hard): approximately 50-55% of the coding section marks
- Problem 3 if present (Hard): approximately 15-20% of the coding section marks

This distribution means that a candidate who fully solves Problem 1 and partially solves Problem 2 (passing 6 of 10 cases) scores approximately 60-65% of the coding section marks - which is often sufficient for Digital routing combined with a strong Foundation Section performance.

---

## Command Line Arguments: The MCQ Coding Question

Some TCS NQT formats include multiple-choice questions about programming concepts in addition to the two IDE problems. A frequently tested concept is command line argument handling.

### C/C++: argc and argv

```cpp
#include <iostream>
using namespace std;

int main(int argc, char* argv[]) {
    // argc = argument count (includes program name as argv[0])
    // argv = array of argument strings
    cout << "Number of arguments: " << argc << endl;
    for (int i = 0; i < argc; i++) {
        cout << "argv[" << i << "] = " << argv[i] << endl;
    }
    return 0;
}
```

If run as `./program hello world`, argc is 3, argv[0] is "program", argv[1] is "hello", argv[2] is "world".

MCQ trap: argc counts the program name as the first argument. If the question asks "How many arguments are passed to main when the program is invoked as `./prog a b c`?" the answer is 4 (the program name plus three user arguments), not 3.

### Java: String[] args

```java
public class Main {
    public static void main(String[] args) {
        // args does NOT include the program name
        System.out.println("Argument count: " + args.length);
        for (int i = 0; i < args.length; i++) {
            System.out.println("args[" + i + "] = " + args[i]);
        }
    }
}
```

Key difference from C: Java's `args` array does NOT include the program name. If the program is run as `java Main hello world`, args.length is 2, args[0] is "hello", args[1] is "world".

MCQ trap: Comparing C and Java argument counting. In C, argc for `./prog a b` is 3. In Java, args.length for `java Main a b` is 2. They count differently because Java excludes the class name.

### Python: sys.argv

```python
import sys
# sys.argv[0] is the script name, like C's argv[0]
print("Argument count:", len(sys.argv))
for i, arg in enumerate(sys.argv):
    print(f"sys.argv[{i}] = {arg}")
```

Python's `sys.argv` behaves like C's `argv` - index 0 is the script name.

---

## Topic 1: Arrays and Strings

**TCS framing pattern:** Problems are presented as inventory management (find the most common item in a warehouse), seating arrangements (find the seat number that satisfies a condition), or quality control (find the defective item based on a numerical property).

### Key Operations and Their Complexity

Traversal: O(n). Searching unsorted: O(n). Binary search on sorted: O(log n). Sorting: O(n log n). Prefix sum construction: O(n), then O(1) per range query.

### Original Problem: Chocolate Factory Quality Check

**Problem:** A chocolate factory produces chocolates in batches. The quality score of each chocolate is given as an integer array. Find the length of the longest subarray where all quality scores are strictly increasing. If the input array is empty, return 0.

**Input:** First line is n (number of chocolates). Second line is n space-separated integers.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;

int longestIncreasing(vector<int>& arr) {
    if (arr.empty()) return 0;
    int maxLen = 1, curLen = 1;
    for (int i = 1; i < arr.size(); i++) {
        if (arr[i] > arr[i-1]) {
            curLen++;
            maxLen = max(maxLen, curLen);
        } else {
            curLen = 1;
        }
    }
    return maxLen;
}

int main() {
    int n;
    cin >> n;
    vector<int> arr(n);
    for (int i = 0; i < n; i++) cin >> arr[i];
    cout << longestIncreasing(arr) << endl;
    return 0;
}
```

**Java Solution:**
```java
import java.util.*;

public class Main {
    public static int longestIncreasing(int[] arr) {
        if (arr.length == 0) return 0;
        int maxLen = 1, curLen = 1;
        for (int i = 1; i < arr.length; i++) {
            if (arr[i] > arr[i-1]) {
                curLen++;
                maxLen = Math.max(maxLen, curLen);
            } else {
                curLen = 1;
            }
        }
        return maxLen;
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();
        System.out.println(longestIncreasing(arr));
    }
}
```

**Python Solution:**
```python
def longest_increasing(arr):
    if not arr:
        return 0
    max_len = cur_len = 1
    for i in range(1, len(arr)):
        if arr[i] > arr[i-1]:
            cur_len += 1
            max_len = max(max_len, cur_len)
        else:
            cur_len = 1
    return max_len

n = int(input())
arr = list(map(int, input().split()))
print(longest_increasing(arr))
```

**Thought process:** A single pass keeps a running count of the current streak. When the streak breaks, reset to 1 (the current element starts a new potential streak). Update the maximum at each extension. Time complexity O(n), space O(1).

**Common pitfalls:** Forgetting the edge case of an empty array. Resetting curLen to 0 instead of 1 (the current element itself is always a streak of length 1). Using `>=` instead of `>` when the problem says "strictly increasing."

### String Manipulation: Anagram Detection

TCS frequently presents string problems as "word scramble" or "rearranged product label" scenarios.

**Problem:** Given two strings, determine whether they are anagrams of each other (contain the same characters in any order). Return "YES" or "NO".

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    string a, b;
    cin >> a >> b;
    if (a.length() != b.length()) {
        cout << "NO" << endl;
        return 0;
    }
    sort(a.begin(), a.end());
    sort(b.begin(), b.end());
    cout << (a == b ? "YES" : "NO") << endl;
    return 0;
}
```

**Java Solution:**
```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        char[] a = sc.next().toCharArray();
        char[] b = sc.next().toCharArray();
        if (a.length != b.length) {
            System.out.println("NO");
            return;
        }
        Arrays.sort(a);
        Arrays.sort(b);
        System.out.println(Arrays.equals(a, b) ? "YES" : "NO");
    }
}
```

**Python Solution:**
```python
a = input().strip()
b = input().strip()
print("YES" if sorted(a) == sorted(b) else "NO")
```

**Alternative O(n) approach using frequency array:** Create a count array of 26 integers. Increment count for each character in string A, decrement for each character in string B. If all counts are zero at the end, strings are anagrams. This avoids sorting and runs in O(n) time.

### Prefix Sum for Range Queries

A critical optimisation pattern: if multiple range sum queries are needed, build a prefix sum array once in O(n), then answer each query in O(1).

```python
def build_prefix(arr):
    prefix = [0] * (len(arr) + 1)
    for i, v in enumerate(arr):
        prefix[i+1] = prefix[i] + v
    return prefix

def range_sum(prefix, l, r):  # inclusive [l, r], 0-indexed
    return prefix[r+1] - prefix[l]
```

TCS presents prefix sum problems as "find the total production between station L and station R" across multiple queries. Without prefix sums, answering Q queries on an array of size N takes O(Q*N). With prefix sums: O(N) build + O(Q) queries.

**TCS framing pattern:** Presented as scheduling problems (find the interval at which two machines are both idle using GCD), distribution problems (how many ways to distribute items with prime number constraints), or security key generation (modular arithmetic for access codes).

### Sieve of Eratosthenes

For problems requiring all primes up to N, the Sieve runs in O(N log log N) and is far more efficient than checking each number individually.

### Original Problem: Party Seating Access Codes

**Problem:** A party venue assigns access codes. A code is valid if it is divisible by every prime factor of a given master key K. Given N candidate codes and the master key K, count how many codes are valid. A code of 0 is always invalid.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;

vector<int> primeFactors(int k) {
    vector<int> factors;
    for (int i = 2; i * i <= k; i++) {
        if (k % i == 0) {
            factors.push_back(i);
            while (k % i == 0) k /= i;
        }
    }
    if (k > 1) factors.push_back(k);
    return factors;
}

int main() {
    int n, k;
    cin >> n >> k;
    vector<int> primes = primeFactors(k);
    int count = 0;
    for (int i = 0; i < n; i++) {
        int code;
        cin >> code;
        if (code == 0) continue;
        bool valid = true;
        for (int p : primes) {
            if (code % p != 0) { valid = false; break; }
        }
        if (valid) count++;
    }
    cout << count << endl;
    return 0;
}
```

**Python Solution:**
```python
def prime_factors(k):
    factors = []
    i = 2
    while i * i <= k:
        if k % i == 0:
            factors.append(i)
            while k % i == 0:
                k //= i
        i += 1
    if k > 1:
        factors.append(k)
    return factors

n, k = map(int, input().split())
primes = prime_factors(k)
count = 0
for _ in range(n):
    code = int(input())
    if code == 0:
        continue
    if all(code % p == 0 for p in primes):
        count += 1
print(count)
```

**Thought process:** Extract unique prime factors of K once. For each code, verify divisibility by each prime factor. This is O(sqrt(K) + N * number_of_prime_factors_of_K), which is efficient for the constraints TCS typically uses.

### GCD and Modular Arithmetic Templates

GCD using the Euclidean algorithm - required for scheduling, tiling, and divisibility problems:

```cpp
// C++ - recursive GCD
int gcd(int a, int b) {
    return b == 0 ? a : gcd(b, a % b);
}
int lcm(int a, int b) {
    return a / gcd(a, b) * b; // divide first to avoid overflow
}
```

```python
from math import gcd
lcm = lambda a, b: a * b // gcd(a, b)
```

**Modular arithmetic for large number problems:**

When a problem asks for an answer "modulo 10^9 + 7," apply the modulus at every addition and multiplication step to prevent overflow:

```python
MOD = 10**9 + 7

def power_mod(base, exp, mod):
    result = 1
    base %= mod
    while exp > 0:
        if exp % 2 == 1:
            result = result * base % mod
        base = base * base % mod
        exp //= 2
    return result
```

```cpp
long long powerMod(long long base, long long exp, long long mod) {
    long long result = 1;
    base %= mod;
    while (exp > 0) {
        if (exp & 1) result = result * base % mod;
        base = base * base % mod;
        exp >>= 1;
    }
    return result;
}
```

**TCS MCQ trap:** When computing (a * b) % MOD in C++, if a and b can each be up to 10^9, their product overflows a 64-bit integer. Solution: use `(__int128)a * b % MOD` or restructure the computation.

**TCS framing pattern:** DP problems are typically framed as resource allocation (maximum value of items that fit in a container), path counting (how many routes through a grid from start to end), or sequence optimisation (minimum cost to reach a goal).

### Memoisation Pattern

Every memoised recursive solution follows the same structure: define the recursive function with a state parameter, check a cache before computing, compute and store in cache, return the cached value.

### Original Problem: Traffic Management Route Counter

**Problem:** A city has a grid of M rows and N columns. A traffic management vehicle starts at the top-left corner (1,1) and must reach the bottom-right corner (M,N). It can only move right or down. Some cells are blocked (value 1 in the grid). Count the number of valid paths. Return 0 if no path exists.

**C++ Solution (DP):**
```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    int m, n;
    cin >> m >> n;
    vector<vector<int>> grid(m, vector<int>(n));
    for (int i = 0; i < m; i++)
        for (int j = 0; j < n; j++)
            cin >> grid[i][j];

    if (grid[0][0] == 1 || grid[m-1][n-1] == 1) {
        cout << 0 << endl;
        return 0;
    }

    vector<vector<long long>> dp(m, vector<long long>(n, 0));
    dp[0][0] = 1;

    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            if (i == 0 && j == 0) continue;
            if (grid[i][j] == 1) { dp[i][j] = 0; continue; }
            long long fromTop = (i > 0) ? dp[i-1][j] : 0;
            long long fromLeft = (j > 0) ? dp[i][j-1] : 0;
            dp[i][j] = fromTop + fromLeft;
        }
    }
    cout << dp[m-1][n-1] << endl;
    return 0;
}
```

**Python Solution:**
```python
import sys
input = sys.stdin.readline

def solve():
    m, n = map(int, input().split())
    grid = []
    for _ in range(m):
        grid.append(list(map(int, input().split())))

    if grid[0][0] == 1 or grid[m-1][n-1] == 1:
        print(0)
        return

    dp = [[0]*n for _ in range(m)]
    dp[0][0] = 1

    for i in range(m):
        for j in range(n):
            if i == 0 and j == 0:
                continue
            if grid[i][j] == 1:
                dp[i][j] = 0
                continue
            from_top = dp[i-1][j] if i > 0 else 0
            from_left = dp[i][j-1] if j > 0 else 0
            dp[i][j] = from_top + from_left

    print(dp[m-1][n-1])

solve()
```

**Thought process:** The number of paths to cell (i,j) equals paths from top (i-1,j) plus paths from left (i,j-1), unless the cell is blocked. This is a classical bottom-up DP. Use `long long` in C++ because path counts can be large.

**Common pitfall:** Not handling blocked start or end cells explicitly. Not using long long for path counts (they can exceed int range for large grids).

### Classic DP: Coin Change Problem

**TCS framing:** "A vending machine has coins of denominations D1, D2, ... Dk. Find the minimum number of coins to make change for amount A."

```python
def min_coins(coins, amount):
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for a in range(1, amount + 1):
        for coin in coins:
            if coin <= a:
                dp[a] = min(dp[a], dp[a - coin] + 1)
    return dp[amount] if dp[amount] != float('inf') else -1

k, amount = map(int, input().split())
coins = list(map(int, input().split()))
print(min_coins(coins, amount))
```

```cpp
int minCoins(vector<int>& coins, int amount) {
    vector<int> dp(amount + 1, INT_MAX);
    dp[0] = 0;
    for (int a = 1; a <= amount; a++) {
        for (int c : coins) {
            if (c <= a && dp[a-c] != INT_MAX)
                dp[a] = min(dp[a], dp[a-c] + 1);
        }
    }
    return dp[amount] == INT_MAX ? -1 : dp[amount];
}
```

### Classic DP: 0-1 Knapsack

**TCS framing:** "A delivery van has capacity W kg. N packages are available, each with weight wi and value vi. Find the maximum value that can be loaded."

```python
def knapsack(weights, values, W):
    n = len(weights)
    dp = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for w in range(W + 1):
            dp[i][w] = dp[i-1][w]  # don't take item i
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w],
                               dp[i-1][w - weights[i-1]] + values[i-1])
    return dp[n][W]
```

**Space-optimised 1D version (iterate W in reverse):**
```python
def knapsack_1d(weights, values, W):
    dp = [0] * (W + 1)
    for i in range(len(weights)):
        for w in range(W, weights[i] - 1, -1):  # MUST go backwards
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    return dp[W]
```

The backwards iteration is critical in the 1D version - iterating forward would allow an item to be used multiple times (unbounded knapsack), which is incorrect for 0-1 knapsack.

**TCS framing pattern:** Activity selection problems (schedule maximum non-overlapping events at a venue), coin change with standard denominations (minimum coins for a vending machine), or interval covering (minimum number of broadcast towers to cover a highway).

### Original Problem: Event Hall Scheduling

**Problem:** An event hall receives N booking requests, each with a start time and end time. Find the maximum number of non-overlapping events that can be accommodated. Two events overlap if one starts before the other ends.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    cin >> n;
    vector<pair<int,int>> events(n);
    for (int i = 0; i < n; i++)
        cin >> events[i].first >> events[i].second;

    // Sort by end time (greedy: pick the event that finishes earliest)
    sort(events.begin(), events.end(), [](auto& a, auto& b){
        return a.second < b.second;
    });

    int count = 0, lastEnd = -1;
    for (auto& e : events) {
        if (e.first >= lastEnd) {
            count++;
            lastEnd = e.second;
        }
    }
    cout << count << endl;
    return 0;
}
```

**Java Solution:**
```java
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[][] events = new int[n][2];
        for (int i = 0; i < n; i++) {
            events[i][0] = sc.nextInt();
            events[i][1] = sc.nextInt();
        }
        Arrays.sort(events, (a, b) -> a[1] - b[1]);
        int count = 0, lastEnd = -1;
        for (int[] e : events) {
            if (e[0] >= lastEnd) {
                count++;
                lastEnd = e[1];
            }
        }
        System.out.println(count);
    }
}
```

**Thought process:** The greedy insight is: always choose the event that ends earliest among compatible events. This leaves the most time available for subsequent events. Sorting by end time and iterating once gives an O(n log n) solution.

---

## Topic 5: Graph Basics - BFS and DFS

**TCS framing pattern:** Network connectivity problems (find all servers connected to a main server), island counting problems (count regions of connected cells in a grid), or shortest path problems (minimum hops between two nodes in a network).

### BFS Template for Grid Problems

```cpp
// C++ BFS on a grid
#include <bits/stdc++.h>
using namespace std;

int bfs(vector<vector<int>>& grid, int sr, int sc) {
    int m = grid.size(), n = grid[0].size();
    queue<pair<int,int>> q;
    q.push({sr, sc});
    grid[sr][sc] = 0; // mark visited
    int dist = 0;
    vector<pair<int,int>> dirs = {{0,1},{0,-1},{1,0},{-1,0}};

    while (!q.empty()) {
        int sz = q.size();
        while (sz--) {
            auto [r, c] = q.front(); q.pop();
            for (auto [dr, dc] : dirs) {
                int nr = r + dr, nc = c + dc;
                if (nr >= 0 && nr < m && nc >= 0 && nc < n && grid[nr][nc] == 1) {
                    grid[nr][nc] = 0;
                    q.push({nr, nc});
                }
            }
        }
        dist++;
    }
    return dist;
}
```

### Original Problem: Factory Network Islands

**Problem:** A factory floor is represented as a grid of 1s (machines) and 0s (empty space). Two machines are connected if they are adjacent horizontally or vertically. Count the number of isolated machine clusters (connected components of 1s).

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;

void dfs(vector<vector<int>>& grid, int r, int c) {
    int m = grid.size(), n = grid[0].size();
    if (r < 0 || r >= m || c < 0 || c >= n || grid[r][c] == 0) return;
    grid[r][c] = 0; // mark visited
    dfs(grid, r+1, c);
    dfs(grid, r-1, c);
    dfs(grid, r, c+1);
    dfs(grid, r, c-1);
}

int main() {
    int m, n;
    cin >> m >> n;
    vector<vector<int>> grid(m, vector<int>(n));
    for (int i = 0; i < m; i++)
        for (int j = 0; j < n; j++)
            cin >> grid[i][j];

    int count = 0;
    for (int i = 0; i < m; i++)
        for (int j = 0; j < n; j++)
            if (grid[i][j] == 1) {
                dfs(grid, i, j);
                count++;
            }
    cout << count << endl;
    return 0;
}
```

**Python Solution:**
```python
import sys
sys.setrecursionlimit(100000)

def dfs(grid, r, c, m, n):
    if r < 0 or r >= m or c < 0 or c >= n or grid[r][c] == 0:
        return
    grid[r][c] = 0
    dfs(grid, r+1, c, m, n)
    dfs(grid, r-1, c, m, n)
    dfs(grid, r, c+1, m, n)
    dfs(grid, r, c-1, m, n)

m, n = map(int, input().split())
grid = [list(map(int, input().split())) for _ in range(m)]
count = 0
for i in range(m):
    for j in range(n):
        if grid[i][j] == 1:
            dfs(grid, i, j, m, n)
            count += 1
print(count)
```

**Common pitfall in Python:** Deep recursion for large grids exceeds Python's default limit. Always add `sys.setrecursionlimit` for DFS problems. Alternatively, implement DFS iteratively using an explicit stack to avoid recursion limits entirely.

### BFS for Shortest Path

When edges are unweighted (or all have equal weight), BFS finds the shortest path between two nodes in O(V + E) time.

```python
from collections import deque

def bfs_shortest_path(graph, start, end, n):
    dist = [-1] * (n + 1)
    dist[start] = 0
    q = deque([start])
    while q:
        node = q.popleft()
        for neighbor in graph[node]:
            if dist[neighbor] == -1:
                dist[neighbor] = dist[node] + 1
                if neighbor == end:
                    return dist[neighbor]
                q.append(neighbor)
    return -1  # no path exists
```

**TCS framing:** "Find the minimum number of relay stations between two city nodes in a communication network" - classic BFS shortest path on an adjacency list graph.

**TCS framing pattern:** Binary search on the answer (find the minimum maximum or maximum minimum in a constrained setting), searching in rotated arrays, or finding the first/last occurrence of a value.

**Binary search on the answer** is a powerful technique where the search space is not an array but a range of possible answers.

### Original Problem: Warehouse Package Distribution

**Problem:** A warehouse has N packages with given weights. Distribute them into exactly K convoys such that the maximum weight any single convoy carries is minimised. Find this minimum possible maximum weight. Packages must be kept in order and each convoy takes a contiguous segment.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;

bool canDistribute(vector<int>& weights, int k, long long maxLoad) {
    int convoys = 1;
    long long current = 0;
    for (int w : weights) {
        if (w > maxLoad) return false;
        if (current + w > maxLoad) {
            convoys++;
            current = w;
        } else {
            current += w;
        }
    }
    return convoys <= k;
}

int main() {
    int n, k;
    cin >> n >> k;
    vector<int> weights(n);
    long long total = 0, maxW = 0;
    for (int i = 0; i < n; i++) {
        cin >> weights[i];
        total += weights[i];
        maxW = max(maxW, (long long)weights[i]);
    }

    long long lo = maxW, hi = total, ans = total;
    while (lo <= hi) {
        long long mid = lo + (hi - lo) / 2;
        if (canDistribute(weights, k, mid)) {
            ans = mid;
            hi = mid - 1;
        } else {
            lo = mid + 1;
        }
    }
    cout << ans << endl;
    return 0;
}
```

**Python Solution:**
```python
def can_distribute(weights, k, max_load):
    convoys, current = 1, 0
    for w in weights:
        if w > max_load:
            return False
        if current + w > max_load:
            convoys += 1
            current = w
        else:
            current += w
    return convoys <= k

n, k = map(int, input().split())
weights = list(map(int, input().split()))
lo, hi = max(weights), sum(weights)
ans = hi
while lo <= hi:
    mid = (lo + hi) // 2
    if can_distribute(weights, k, mid):
        ans = mid
        hi = mid - 1
    else:
        lo = mid + 1
print(ans)
```

**Thought process:** Binary search on the answer: the minimum possible maximum load is at least the maximum single weight (lo), and at most the total weight (hi, which means one convoy carries everything). For each candidate answer `mid`, check in O(n) whether distributing into K convoys is feasible. Total complexity O(n log(sum of weights)).

---

## Topic 7: Sliding Window Technique

**TCS framing pattern:** Subarray problems with a constraint on sum, average, or count - presented as quality control windows, production monitoring intervals, or network packet analysis.

### Original Problem: Production Line Monitoring

**Problem:** A factory monitors a production line where each station produces a certain number of units per hour. Find the length of the longest contiguous subarray where the average output is at least T units per hour. Return 0 if no such subarray exists.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    double t;
    cin >> n >> t;
    vector<int> a(n);
    for (int i = 0; i < n; i++) cin >> a[i];

    // Binary search on answer: is there a subarray of length L with avg >= t?
    // Transform: subtract t from each element. Then check if any subarray of length >= L has sum >= 0.
    // Use prefix sums.

    int lo = 1, hi = n, ans = 0;
    vector<double> b(n);
    for (int i = 0; i < n; i++) b[i] = a[i] - t;

    auto check = [&](int L) {
        vector<double> prefix(n+1, 0);
        for (int i = 0; i < n; i++) prefix[i+1] = prefix[i] + b[i];
        double minPrefix = 0;
        for (int i = L; i <= n; i++) {
            minPrefix = min(minPrefix, prefix[i-L]);
            if (prefix[i] - minPrefix >= 0) return true;
        }
        return false;
    };

    while (lo <= hi) {
        int mid = (lo + hi) / 2;
        if (check(mid)) { ans = mid; lo = mid + 1; }
        else hi = mid - 1;
    }
    cout << ans << endl;
    return 0;
}
```

**Simpler fixed-window variant (most common in TCS):**

```python
# Maximum sum of a subarray of exactly K elements
def max_window_sum(arr, k):
    if len(arr) < k:
        return 0
    window = sum(arr[:k])
    max_sum = window
    for i in range(k, len(arr)):
        window += arr[i] - arr[i-k]
        max_sum = max(max_sum, window)
    return max_sum

n, k = map(int, input().split())
arr = list(map(int, input().split()))
print(max_window_sum(arr, k))
```

**Thought process for fixed window:** Compute the sum of the first K elements. Slide the window right by adding the new element and removing the oldest. Never recompute the sum from scratch - each slide is O(1). Total O(n).

---

## Topic 8: Two Pointer Technique

**TCS framing pattern:** Pair-finding problems (find two employees whose combined experience equals a target), partition problems (separate items by a threshold), or palindrome checking on arrays/strings.

### Original Problem: Supply Chain Pair Matching

**Problem:** A supply chain database has N suppliers, each with a reliability score. Find all unique pairs of suppliers whose combined reliability score equals a target value T. Output the count of such pairs.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    int n, t;
    cin >> n >> t;
    vector<int> scores(n);
    for (int i = 0; i < n; i++) cin >> scores[i];

    sort(scores.begin(), scores.end());
    int left = 0, right = n - 1, count = 0;

    while (left < right) {
        int sum = scores[left] + scores[right];
        if (sum == t) {
            if (scores[left] == scores[right]) {
                long long diff = right - left;
                count += diff * (diff + 1) / 2;
                break;
            }
            int cntL = 1, cntR = 1;
            while (left + 1 < right && scores[left+1] == scores[left]) { left++; cntL++; }
            while (right - 1 > left && scores[right-1] == scores[right]) { right--; cntR++; }
            count += cntL * cntR;
            left++; right--;
        } else if (sum < t) {
            left++;
        } else {
            right--;
        }
    }
    cout << count << endl;
    return 0;
}
```

**Python Solution:**
```python
n, t = map(int, input().split())
scores = list(map(int, input().split()))
scores.sort()
left, right, count = 0, n - 1, 0

while left < right:
    s = scores[left] + scores[right]
    if s == t:
        if scores[left] == scores[right]:
            diff = right - left
            count += diff * (diff + 1) // 2
            break
        cnt_l, cnt_r = 1, 1
        while left + 1 < right and scores[left+1] == scores[left]:
            left += 1; cnt_l += 1
        while right - 1 > left and scores[right-1] == scores[right]:
            right -= 1; cnt_r += 1
        count += cnt_l * cnt_r
        left += 1; right -= 1
    elif s < t:
        left += 1
    else:
        right -= 1

print(count)
```

**Thought process:** Sort the array. Use two pointers from both ends. If sum equals target, count the pair(s). If less than target, move left pointer right. If greater, move right pointer left. Handle duplicates by counting how many elements at each pointer share the same value. O(n log n) overall.

### Two Pointer: In-Place Partition

TCS frames this as "separate defective items from non-defective items while preserving relative order among each group" or "move all zeros to the end without changing the order of non-zero elements."

```python
def move_zeros_to_end(arr):
    insert_pos = 0
    for i in range(len(arr)):
        if arr[i] != 0:
            arr[insert_pos] = arr[i]
            insert_pos += 1
    while insert_pos < len(arr):
        arr[insert_pos] = 0
        insert_pos += 1
    return arr
```

```cpp
void moveZerosToEnd(vector<int>& arr) {
    int insertPos = 0;
    for (int i = 0; i < arr.size(); i++) {
        if (arr[i] != 0) {
            arr[insertPos++] = arr[i];
        }
    }
    while (insertPos < arr.size()) {
        arr[insertPos++] = 0;
    }
}
```

This is a two-pointer variant where one pointer tracks the "next valid position" and the other scans ahead. O(n) time, O(1) space, stable (preserves relative order of non-zero elements).

**TCS framing pattern:** Bracket matching for code validation, next greater element in a monitoring stream, or level-order processing of a hierarchy.

### Original Problem: Code Review Bracket Validator

**Problem:** A code review tool checks if the bracket sequence in a given string is valid. Brackets are `(`, `)`, `[`, `]`, `{`, `}`. The string may contain non-bracket characters which should be ignored. Return "VALID" if balanced, "INVALID" otherwise.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    string s;
    getline(cin, s);
    stack<char> st;
    map<char,char> match = {{')', '('}, {']', '['}, {'}', '{'}};

    for (char c : s) {
        if (c == '(' || c == '[' || c == '{') {
            st.push(c);
        } else if (match.count(c)) {
            if (st.empty() || st.top() != match[c]) {
                cout << "INVALID" << endl;
                return 0;
            }
            st.pop();
        }
    }
    cout << (st.empty() ? "VALID" : "INVALID") << endl;
    return 0;
}
```

**Python Solution:**
```python
s = input()
stack = []
match = {')': '(', ']': '[', '}': '{'}
valid = True

for c in s:
    if c in '([{':
        stack.append(c)
    elif c in ')]}':
        if not stack or stack[-1] != match[c]:
            valid = False
            break
        stack.pop()

print("VALID" if valid and not stack else "INVALID")
```

### Stack: Next Greater Element

TCS presents this as "find the next warmer day in a temperature monitoring system" or "next higher production quota in a sequence."

**Problem:** For each element in an array, find the next element to its right that is greater. If none exists, output -1.

```python
def next_greater(arr):
    n = len(arr)
    result = [-1] * n
    stack = []  # stores indices
    for i in range(n):
        while stack and arr[i] > arr[stack[-1]]:
            idx = stack.pop()
            result[idx] = arr[i]
        stack.append(i)
    return result
```

```cpp
vector<int> nextGreater(vector<int>& arr) {
    int n = arr.size();
    vector<int> result(n, -1);
    stack<int> st; // stores indices
    for (int i = 0; i < n; i++) {
        while (!st.empty() && arr[i] > arr[st.top()]) {
            result[st.top()] = arr[i];
            st.pop();
        }
        st.push(i);
    }
    return result;
}
```

**Thought process:** Maintain a stack of indices of elements for which we have not yet found the next greater element. When we encounter an element greater than the stack top, that element is the answer for the stack top. Pop and record. This is O(n) because each element is pushed and popped at most once.

**TCS framing pattern:** Permission systems (which access rights are set using bitwise flags), parity checking in data transmission, or finding the unique element in a dataset where all others appear twice.

### Original Problem: Data Transmission Parity Check

**Problem:** In a data transmission system, each packet has a parity bit. Given N integers, find the one integer that appears an odd number of times. All other integers appear an even number of times. Return that integer.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    cin >> n;
    int result = 0;
    for (int i = 0; i < n; i++) {
        int x;
        cin >> x;
        result ^= x; // XOR cancels pairs, leaves the odd-count element
    }
    cout << result << endl;
    return 0;
}
```

**Python Solution:**
```python
from functools import reduce
from operator import xor
n = int(input())
nums = list(map(int, input().split()))
print(reduce(xor, nums))
```

**Python Solution:**
```python
from functools import reduce
from operator import xor
n = int(input())
nums = list(map(int, input().split()))
print(reduce(xor, nums))
```

**Thought process:** XOR of a number with itself is 0. XOR of a number with 0 is the number itself. XOR all elements: pairs cancel out, leaving the single odd-count element. O(n) time, O(1) space.

**Bit counting pattern:** Count set bits in an integer using `__builtin_popcount(n)` in C++ or `bin(n).count('1')` in Python.

### Bit Manipulation: Subset Generation

TCS occasionally presents problems requiring generation of all subsets. Bit manipulation provides an elegant solution for small input sizes (N ≤ 20):

```cpp
// Generate all subsets of array arr of size n
void allSubsets(vector<int>& arr) {
    int n = arr.size();
    for (int mask = 0; mask < (1 << n); mask++) {
        vector<int> subset;
        for (int i = 0; i < n; i++) {
            if (mask & (1 << i)) {
                subset.push_back(arr[i]);
            }
        }
        // process subset
    }
}
```

```python
def all_subsets(arr):
    n = len(arr)
    for mask in range(1 << n):
        subset = [arr[i] for i in range(n) if mask & (1 << i)]
        yield subset
```

**When to use:** TCS problems that ask "find the subset of items whose total weight equals exactly W" can be solved with this approach for small N. For large N, DP is required.

---

## Handling the Two-Problem Structure Strategically

### When Problem 2 Seems Too Hard

A scenario many candidates face: Problem 1 is solved and correct. Problem 2 is not yielding to the first approach tried. With 50 minutes remaining, what is the right strategy?

**Option A - Brute force and submit Problem 2 as-is.** Implement the simplest correct solution for Problem 2 even if it is O(n²) or O(n³). Submit it. Even if it only passes 4 of 10 test cases, those 4 test cases have positive value. Then spend remaining time trying to optimise.

**Option B - Divide the problem into partial cases.** Some TCS problems can be partially solved by handling specific input cases correctly. If the problem constraints say `1 ≤ N ≤ 100,000`, implement a correct O(n²) solution that handles small N (say N ≤ 1000) and submit. Add a comment and optimise if time allows.

**Option C - Reread the problem.** Sometimes the complexity is lower than it appears on first read. Look for: "output only the count, not all pairs" (often a mathematical formula exists), "the array is guaranteed to be sorted" (enables binary search), "constraints guarantee no duplicates" (simplifies certain algorithms).

**Option D - Look for the greedy signal.** Problems that seem to require DP sometimes have a greedy solution that is significantly simpler to implement. If you can argue that making the locally optimal choice at each step never hurts the global answer, try the greedy approach.

### When Problem 1 Takes Longer Than Expected

If you find yourself 30 minutes in and still not passing all visible test cases on Problem 1, make a deliberate decision: do you abandon Problem 1 and start Problem 2, or do you continue?

The right answer depends on the nature of the failure. If you have the correct algorithm but a bug you cannot locate after 5 minutes of checking, it is often better to start Problem 2, make progress there, and return to the Problem 1 bug with fresh eyes later. If you do not yet have the correct algorithm for Problem 1, think hard about whether a different approach is warranted before spending more time debugging the wrong approach.

---

## Advanced Coding: Building to Digital vs Prime Thresholds

### What Digital Routing Requires

Based on candidate-reported patterns, TCS Digital routing from the Advanced Coding section generally requires:
- Problem 1: fully solved with all or nearly all test cases passing
- Problem 2: partially solved with at least 50-60% of test cases passing, or fully solved

This translates to: implementing correct solutions for array/string/pattern problems (Problem 1 category), and demonstrating ability to write correct DP, greedy, or graph traversal solutions for medium-difficulty algorithmic problems (Problem 2 category), even if not fully optimised.

### What Prime Routing Requires

Prime routing requires exceptional performance: both problems fully solved with optimal or near-optimal solutions, and the ability to handle edge cases that eliminate most candidates. In cycles with a Problem 3 (hard), Prime candidates are expected to make meaningful progress on it.

Practically, Prime-bound candidates need to solve medium-hard LeetCode problems cleanly and consistently within 20-30 minutes each. The benchmark: if you can solve 7 out of 10 randomly selected LeetCode Medium problems within 25 minutes each, you are in the range for Prime routing from the coding section.

### The Foundation Section Still Gates Everything

A reminder that matters: no level of coding section performance compensates for failing the Foundation Section. The Foundation Section cutoff must be cleared first. A candidate who scores 100% in the coding section but fails the Foundation Section numerical or verbal cutoff does not proceed to the interview stage regardless of coding performance.

Prepare the Foundation Section and the Advanced Coding section in parallel, not sequentially. The 30-day coding plan assumes that Foundation preparation is running concurrently in the first two weeks (a lighter parallel track) and intensifies in weeks three and four as the candidate nears the exam.

---

## Resources and Practice Platforms

**For NQT-specific calibrated practice:** The [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html) provides a browser-based environment with coding problems at NQT difficulty levels, including the same I/O format and partial-credit structure as the actual exam.

**For algorithmic problem depth:**
- HackerRank: start with the "Problem Solving" section, Easy to Medium difficulty. The interface is similar to TCS iON and builds comfort with browser-based coding.
- LeetCode: Easy problems for Problem 1 type preparation, Medium for Problem 2. The editorial explanations are high quality for understanding the intended approach.
- GeeksForGeeks: strong on concept explanations with implementations in multiple languages. Use it to understand a data structure or algorithm concept before practising problems.

**For language-specific reference:**
- C++ STL documentation: cppreference.com
- Java Collections documentation: docs.oracle.com/javase
- Python standard library: docs.python.org/3/library

The most effective preparation combines concept understanding (GeeksForGeeks), problem practice (HackerRank/LeetCode), and NQT-specific calibration (ReportMedic). Spending 70% of practice time on problems and 30% on reviewing correct solutions and editorial explanations produces faster skill growth than solving problems alone.

**TCS framing pattern:** Custom sorting (sort employees by department then salary), stable sort requirements (maintain relative order among equal elements), or implementing a specific sorting algorithm as a code trace.

### TCS-Specific Sorting Note

TCS MCQ questions frequently ask candidates to trace through a sorting algorithm by hand. Know the step-by-step execution of: Bubble Sort (O(n²), stable), Selection Sort (O(n²), unstable), Insertion Sort (O(n²), stable, excellent for nearly sorted data), Merge Sort (O(n log n), stable, requires O(n) extra space), Quick Sort (O(n log n) average, O(n²) worst case, unstable, in-place).

**Bubble Sort trace for [5, 3, 1, 4, 2]:**
- Pass 1: [3,1,4,2,**5**] - 5 bubbles to end
- Pass 2: [1,3,2,**4**,5] - 4 bubbles to its correct position
- Pass 3: [1,2,**3**,4,5] - 3 bubbles to its correct position
- Array sorted after 3 full passes (optimised bubble sort exits early if no swaps occurred in a pass)

**Selection Sort trace for [5, 3, 1, 4, 2]:**
- Pass 1: find minimum (1 at index 2), swap with index 0: [**1**, 3, 5, 4, 2]
- Pass 2: find minimum in [3,5,4,2] (2 at index 4), swap with index 1: [1, **2**, 5, 4, 3]
- Pass 3: find minimum in [5,4,3] (3 at index 4), swap with index 2: [1, 2, **3**, 4, 5]

**MCQ trap:** Selection Sort is NOT stable - equal elements can change relative order during selection and swap. Bubble Sort and Insertion Sort are stable.

### Custom Sort: Multi-Criteria Employee Ranking

```python
employees = []
n = int(input())
for _ in range(n):
    name, dept, salary = input().split()
    employees.append((name, dept, int(salary)))

# Sort: primary by department ascending, secondary by salary descending
employees.sort(key=lambda x: (x[1], -x[2]))
for e in employees:
    print(e[0], e[1], e[2])
```

```cpp
// C++ equivalent
sort(employees.begin(), employees.end(), [](auto& a, auto& b){
    if (a.dept != b.dept) return a.dept < b.dept;
    return a.salary > b.salary; // descending salary within same dept
});
```

**TCS framing:** "Sort the employee roster by department (alphabetically), and within each department, list employees from highest to lowest salary." This multi-criteria sort is a very common Problem 1 type requiring only a custom comparator and no advanced algorithms.

---

## Topic 12: Basic Tree Problems

**TCS framing pattern:** Organisational hierarchy traversal (find all employees reporting to a manager at a given level), binary tree construction from traversal sequences, or tree property checking (is a given binary tree a BST?).

### Tree Traversal Template

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def inorder(root):
    if root is None:
        return []
    return inorder(root.left) + [root.val] + inorder(root.right)

def level_order(root):
    if not root:
        return []
    from collections import deque
    result, queue = [], deque([root])
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.val)
            if node.left: queue.append(node.left)
            if node.right: queue.append(node.right)
        result.append(level)
    return result
```

TCS tree problems in the Advanced Coding section typically involve building a tree from given parent-child pairs or from inorder+preorder traversal sequences, then computing a property (height, diameter, number of leaf nodes).

### Tree Height Calculation

**TCS framing:** "An organisation has a hierarchical reporting structure. Find the maximum number of levels in the hierarchy (height of the tree)."

```python
def height(root):
    if root is None:
        return 0
    return 1 + max(height(root.left), height(root.right))
```

```cpp
int height(TreeNode* root) {
    if (!root) return 0;
    return 1 + max(height(root->left), height(root->right));
}
```

### BST Validation

A Binary Search Tree has the property that every node in the left subtree is strictly less than the current node, and every node in the right subtree is strictly greater. Validate this with bounds passing rather than just checking immediate parent-child pairs:

```python
def is_bst(root, min_val=float('-inf'), max_val=float('inf')):
    if root is None:
        return True
    if root.val <= min_val or root.val >= max_val:
        return False
    return (is_bst(root.left, min_val, root.val) and
            is_bst(root.right, root.val, max_val))
```

**Common pitfall:** Checking only immediate parent-child relationships is insufficient. A node in the left subtree must be less than all of its ancestor nodes where it branched right, not just its direct parent. The bounds-passing approach propagates these constraints correctly down every path.

### Building a Tree from Parent Array

TCS sometimes presents a tree as a parent array: `parent[i]` is the parent of node `i`, with the root having `parent[root] = -1`. Build and traverse this representation:

```python
from collections import defaultdict, deque

def build_and_bfs(parent_arr):
    n = len(parent_arr)
    children = defaultdict(list)
    root = -1
    for i, p in enumerate(parent_arr):
        if p == -1:
            root = i
        else:
            children[p].append(i)
    # BFS level order
    queue = deque([root])
    levels = []
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node)
            for child in children[node]:
                queue.append(child)
        levels.append(level)
    return levels
```

**Time complexity:** O(n) to build adjacency list, O(n) for BFS. Total O(n).

---

Understanding the surface language TCS uses to present familiar algorithmic problems is itself a preparation skill. The same underlying algorithm appears in multiple problem "stories."

### The Chocolate Factory / Food Production Scenario

Problems framed around chocolates, food production, or quality control typically involve:
- Array manipulation (find the maximum/minimum in a production run)
- Sliding window (find the window with highest average quality)
- Sorting (rank batches by quality)
- Frequency counting (which defect type appears most often)

When you see "factory," "batch," "production line," or "quality score," mentally classify the problem as an array or frequency problem and look for the underlying numerical pattern.

### The Traffic Management / Route Optimisation Scenario

Problems framed around city routes, traffic flow, or network connectivity typically involve:
- Graph BFS/DFS (find connected components, shortest path)
- Binary search on answer (minimum maximum travel time)
- DP (number of unique paths through a network)
- Greedy (minimum number of stops)

When you see "city," "route," "network," or "path," mentally classify it as a graph or path-counting problem.

### The Party / Seating / Event Scenario

Problems framed around events, scheduling, or seating typically involve:
- Greedy interval scheduling (maximum non-overlapping events)
- Sorting with custom comparator (sort guests by arrival time then name)
- Stack-based matching (pair guests with preferences)
- Set operations (guests in common between two lists)

### The Warehouse / Inventory / Supply Chain Scenario

Problems framed around warehouses, packages, or supply chains typically involve:
- Binary search on answer (split inventory into K groups)
- Prefix sum (total weight between positions L and R)
- Priority queue (process items in order of weight/value)
- DP knapsack (maximise value within weight limit)

### Pattern Recognition Practice

During your preparation, explicitly label every problem you solve with both its surface scenario and its underlying algorithm type. Build a mental mapping table. By the time of the exam, the first sentence of the problem statement should already suggest the likely algorithm, before you have even read the constraints.

---

## Writing Bulletproof Code Under Exam Conditions

The difference between a correct algorithm and a correct solution is implementation discipline. Under time pressure, coding errors that would be obvious in a relaxed setting cause test case failures.

### The Five-Step Pre-Submit Checklist

Before clicking Submit on any problem:

**Step 1 - Edge case check:** Trace your code mentally for: n=0 or empty input, n=1 (single element), all elements equal, the minimum possible input value, and the maximum possible input value.

**Step 2 - Output format check:** Does your output match the expected output format exactly? Common format mistakes: extra spaces, missing newlines, printing "True" when the expected output is "YES", printing a decimal when an integer is expected.

**Step 3 - Integer overflow check:** Any computation involving multiplication of two numbers that could each be 10^5 or larger? Switch those variables to `long long` in C++/Java or Python's native arbitrary precision integers.

**Step 4 - Array bounds check:** Any array access using `arr[i-1]` or `arr[i+1]`? Verify that `i-1 >= 0` and `i+1 < n` before those accesses.

**Step 5 - Logic trace on one visible test case:** Pick the largest visible test case and mentally trace your code's execution for the first 3-4 iterations. Does the state evolve as expected?

This checklist takes 90 seconds to run through. It frequently catches errors that would otherwise fail several hidden test cases.

### Input Parsing Patterns

The most common input parsing mistakes in TCS NQT coding:

**Reading a grid:** In Java, many candidates forget to call `sc.nextLine()` after reading the grid dimensions with `sc.nextInt()`, causing the first row of the grid to be read as an empty string.

```java
Scanner sc = new Scanner(System.in);
int m = sc.nextInt();
int n = sc.nextInt();
sc.nextLine(); // consume the trailing newline after the dimension line
int[][] grid = new int[m][n];
for (int i = 0; i < m; i++) {
    String[] parts = sc.nextLine().split(" ");
    for (int j = 0; j < n; j++) {
        grid[i][j] = Integer.parseInt(parts[j]);
    }
}
```

**Reading multiple test cases:** Some TCS problems present T test cases. Always read T first, then loop T times with a complete read-and-solve per iteration.

```python
T = int(input())
for _ in range(T):
    n = int(input())
    arr = list(map(int, input().split()))
    # solve and print for this test case
```

**Trailing spaces and newlines:** Python's `input()` automatically strips the trailing newline. Java's `sc.nextLine()` does not include the newline in the returned string. Neither should cause issues. But `input().split()` in Python correctly handles multiple spaces between numbers - do not worry about extra whitespace in the input.

---

## Language Choice Decision Framework

Use this framework to decide which language to use for each problem type in the TCS NQT:

**Problem 1 (Implementation, Easy):** Use Python if your Python is strong. The code will be shortest and fastest to write. Only switch to C++ if the problem has explicit large I/O (thousands of lines of input) that might cause Python to TLE.

**Problem 2 (Algorithmic, Medium-Hard):** Use C++ if your algorithmic implementation skills are comparable across languages - C++ is fastest and gives the most headroom on hidden test cases. Use Python if your Python is significantly stronger and you can implement the algorithm confidently with iterative rather than recursive code.

**Problem 3 (Hard, if present):** Use C++ or Java. Hard problems almost certainly involve large inputs that will TLE in Python.

**If your best language is Java:** Java is a solid choice for all three problem types. Use BufferedReader for heavy input, StringBuilder for heavy string output, and the `java.util.Collections` and `java.util.Arrays` utility classes aggressively.

---

## The Top 10 TCS NQT Coding Problem Types by Frequency

Based on patterns across multiple cycles:

1. **Array manipulation with a single-pass condition** (longest streak, count elements satisfying a property) - appears in almost every cycle as Problem 1
2. **String palindrome, anagram, or transformation** - very high frequency Problem 1 type
3. **Number pattern or sequence generation** (prime numbers, Fibonacci, custom sequences) - frequent Problem 1
4. **Grid path counting** (DP, blocked cells) - frequent Problem 2 type
5. **Interval scheduling / greedy** (maximum non-overlapping events) - medium frequency Problem 2
6. **Frequency counting and sorting** (find the top-K elements, mode, median) - Problem 1 or early Problem 2
7. **Stack-based problems** (bracket validation, next greater element) - medium frequency
8. **Binary search on the answer** (split array problem, capacity minimisation) - Problem 2 difficulty
9. **Graph connectivity** (number of islands, connected components) - medium frequency Problem 2
10. **Dynamic programming** (coin change, 0-1 knapsack, unique paths) - appears in cycles targeting Digital and Prime routing

This plan is structured for a candidate with basic programming knowledge who wants to build the problem-solving skills needed to clear the TCS NQT Advanced Coding section. It assumes 90-120 minutes of daily dedicated coding practice.

### Week 1: Foundations and Arrays

**Days 1-2: Environment Familiarisation and I/O**
Write 10 programs that read different input formats: single integer, array of integers, grid, multiple test cases. Practice in all three of your candidate languages. Confirm your Java class is named `Main`. Confirm Python reads input with `input()` and `sys.stdin.readline()`.

**Days 3-4: Array Manipulation**
Solve 15 array problems: reverse an array, rotate by K positions, find duplicate elements, second largest element, rearrange positive and negative numbers. Focus on O(n) solutions using a single pass wherever possible.

**Days 5-6: String Operations**
Solve 12 string problems: count vowels and consonants, check anagram, longest common prefix, first non-repeating character, string compression (aabbc -> a2b2c). Pay attention to string immutability in Java and Python - build new strings using StringBuilder or string join rather than concatenation in loops.

**Day 7: Review and Mock**
Write complete solutions with input parsing and output for three array/string problems under a 45-minute total time limit. Simulate exam conditions.

### Week 2: Number Theory, Patterns, and Recursion

**Days 8-9: Number Theory**
Implement: prime checking (trial division), sieve of Eratosthenes up to 10^6, GCD and LCM (Euclidean algorithm), modular exponentiation. Solve 10 problems using these building blocks.

**Days 10-11: Recursion**
Implement recursive solutions for: factorial, Fibonacci, tower of Hanoi, binary search, power function, flatten a nested list. Then convert each recursive solution to an iterative version. Understanding both forms prepares you for TCS questions that test both.

**Days 12-13: Dynamic Programming - 1D**
Solve the canonical 1D DP problems: climb stairs (1 or 2 steps at a time), house robber (maximum non-adjacent sum), coin change (minimum coins), longest increasing subsequence. For each, implement both the top-down (memoised recursion) and bottom-up (tabulation) approaches.

**Day 14: Mock Problem Set**
Two problems, 60 minutes total. One array/string problem and one DP problem. Write a full solution from scratch including I/O handling, edge case checking, and correct output format.

### Week 3: Algorithms and Data Structures

**Days 15-16: Sorting and Binary Search**
Implement merge sort and quick sort from scratch (understanding internals for MCQ questions). Then practice binary search on arrays: first occurrence, last occurrence, search in rotated array. Practice binary search on the answer for 5 optimisation problems.

**Days 17-18: Two Pointers and Sliding Window**
Solve 8 problems using two pointers: pair sum, three sum, remove duplicates, container with most water. Solve 6 sliding window problems: maximum sum subarray of size K, smallest subarray with sum >= S, longest substring with at most K distinct characters.

**Days 19-20: Stacks and Queues**
Implement stack-based problems: valid brackets, next greater element, largest rectangle in histogram. Implement queue-based BFS for tree level order traversal. Practice the deque pattern for sliding window maximum.

**Days 21: Graph BFS and DFS**
Implement BFS for shortest path in an unweighted graph and for level order traversal. Implement DFS for connected components and cycle detection. Apply both to grid problems (flood fill, number of islands).

### Week 4: Integration, Advanced Topics, and Exam Simulation

**Days 22-23: Dynamic Programming - 2D**
Solve: unique paths in a grid (with and without obstacles), minimum path sum, longest common subsequence, edit distance, 0-1 knapsack. Understand state definition and transition for each. For every 2D DP problem, practise expressing the state in words before writing code: "dp[i][j] represents the minimum cost to reach cell (i,j)" clarifies the transition immediately.

**Days 24-25: Greedy Algorithms**
Solve: activity selection (maximum non-overlapping intervals), fractional knapsack, minimum number of platforms, jump game. For each greedy problem, identify and articulate the greedy choice property: what locally optimal choice leads to the globally optimal result? Being able to articulate this is important for TCS MCQ questions that ask "which approach correctly solves problem X: greedy or DP?"

**Days 26-27: Bit Manipulation and Miscellaneous**
Solve: find single element (XOR), count set bits, check power of 2, swap without temp variable, number of bits to convert one integer to another. These are fast-to-solve problems that appear as the easier Problem 1 in some cycles. Ensure you can write a correct XOR-based single-element solution in all three languages in under 5 minutes.

**Day 28: Language-Specific Practice**
Write 5 complete programs that use Java's Collections (TreeMap, PriorityQueue, LinkedList as Deque) or Python's collections module (Counter, defaultdict, deque) or C++ STL (map, set, priority_queue, deque). Familiarity with language-standard containers eliminates manual implementation time during the exam.

**Day 29: Full Exam Simulation**
Simulate the complete TCS NQT Advanced Coding section: set a 90-minute timer, solve two problems without any external resources. Use the [ReportMedic TCS NQT Preparation Guide](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html) which provides NQT-calibrated coding problems in a timed practice environment specifically designed for this format.

After the simulation, conduct a debrief:
- How much time did Problem 1 take? Was it under 25 minutes?
- Did you attempt Problem 2 at all? If not, why not?
- Were there edge cases you missed that caused visible test case failures?
- Did your code match the required output format exactly?

**Day 30: Final Review and Edge Case Checklist**
Review the five-step pre-submit checklist described earlier. Ensure your code templates handle all standard edge cases. Do one final timed drill: two problems, 60 minutes, no external resources. Your goal on Day 30 is not to learn new material but to consolidate confidence and execution speed.

---

### Debugging Strategies for the TCS iON Environment

The TCS iON coding environment does not have an integrated debugger. Your only debugging tool is adding `print` or `cout` statements and running against visible test cases. Here is a practical debugging protocol for when your code fails a visible test case:

**Step 1 - Read the expected output carefully.** Is the difference in values, or in format (extra space, wrong newline, integer vs float)?

**Step 2 - Add a print statement at the start of your main function** that prints the parsed input values. This confirms whether your input parsing is correct before looking at the logic.

**Step 3 - Trace the algorithm state at a key checkpoint.** Add a print statement inside the main loop that outputs the loop variable and one key state variable. This reveals whether the loop body executes the expected number of times and whether the state evolves correctly.

**Step 4 - Check your termination condition.** The most common cause of wrong answers in loops is an incorrect termination condition. Verify that the loop runs exactly as many iterations as intended for the given input.

**Step 5 - Remove all debug print statements before final submission.** Extra output in stdout causes test case failures even if the actual answer is correct. TCS test cases check exact output.

### Time Complexity Quick Reference

Every solution you submit should be evaluated against this complexity guide:

| Input size N | Maximum acceptable complexity |
|---|---|
| N ≤ 20 | O(2^N) exponential acceptable |
| N ≤ 500 | O(N^3) acceptable |
| N ≤ 5,000 | O(N^2) acceptable |
| N ≤ 100,000 | O(N log N) required |
| N ≤ 1,000,000 | O(N) or O(N log N) required |

TCS problems typically specify constraints in the problem statement. If N ≤ 10^5, an O(N^2) solution will TLE on large hidden test cases even if it passes visible test cases. Recognising when your brute force approach is too slow and pivoting to an efficient algorithm is one of the key exam skills this 30-day plan builds.

---

### Building a Personal Problem Pattern Library

The most effective advanced preparation activity - beyond solving problems - is building a documented library of the 15-20 most common patterns you encounter. For each pattern, document:

1. The pattern name and a one-line description of what it solves
2. A minimal correct implementation in your primary language
3. The time and space complexity
4. Three TCS-style surface scenarios that map to this pattern

Examples of library entries:

**Entry: Sliding Window Fixed Size**
Description: Maximum or minimum aggregate over all subarrays of exactly K elements.
Template: Compute first window sum. Slide by adding right element and removing left element.
Complexity: O(N) time, O(1) space.
TCS scenarios: Maximum average production over K consecutive shifts; highest customer satisfaction score over K consecutive days; minimum total defects in any K-unit batch.

**Entry: BFS Grid Shortest Path**
Description: Minimum steps from a source cell to a destination cell on a 2D grid.
Template: Queue-based BFS, mark visited, track distance by level.
Complexity: O(M*N) time and space.
TCS scenarios: Minimum relay hops between two nodes in a communication grid; shortest path for a robot through a warehouse grid; minimum routing steps in a city block diagram.

This documentation habit converts each solved problem from a one-time experience into a reusable tool. By exam day, your library contains the templates for every pattern you will need.

---

## Exam Day Coding Strategy

### The First Five Minutes

Read both problems completely before writing a single line of code. This investment of five minutes prevents the trap of starting Problem 1 only to find that Problem 2 is actually more approachable for you. After reading both:

- Classify Problem 1: what algorithm or data structure does it require?
- Classify Problem 2: same question
- Estimate time: can you fully solve Problem 1 in 20-25 minutes? Can you fully solve Problem 2 in 45-50 minutes?

### The Submission Strategy

Always run your code against visible test cases before submitting. A visible test case failure means a guaranteed category of hidden failures - fix it before submitting.

If you solve Problem 1 fully and have a partial solution for Problem 2, submit Problem 1's complete solution and Problem 2's partial solution. Do not wait until Problem 2 is perfect before submitting Problem 1.

If you cannot identify the optimal algorithm for Problem 2, implement a brute force that handles the base cases and small inputs correctly. Submit it. Partial credit from passing 40-50% of test cases combined with a full Problem 1 solution is a solid Digital-eligible score in most cycles.

### The Edge Case Mindset

The hidden test cases that most commonly trip candidates are:

- **Single element arrays:** Does your loop body execute zero times correctly?
- **Already sorted or reverse-sorted input:** Does your sorting-based solution handle these without infinite loops?
- **All identical elements:** Does your duplicate-finding or pairing logic handle this?
- **Maximum constraint inputs:** Does your O(n²) solution time out at n = 10^5?

Build the habit of mentally tracing your code against these four scenarios before every submission.

---

## Common Pitfalls Across All Topics

**Integer overflow:** In Java, `int` overflows silently at approximately 2.1 billion. In C++, `int` behaves the same. Multiplying two numbers of order 10^5 each gives 10^10, which overflows `int`. Use `long` in Java and `long long` in C++.

**Off-by-one errors in loops:** `for (int i = 0; i < n; i++)` correctly iterates n times. `for (int i = 0; i <= n; i++)` iterates n+1 times. In array problems, one extra or one fewer iteration is the most common source of wrong answers on boundary test cases.

**Output format mismatch:** TCS test cases check exact output. If the expected output is `5` and your output is `5\n\n` (extra blank line), the test case fails. Print only what is required, nothing more.

**Python recursion depth:** Default recursion limit in Python is 1000. Any recursive algorithm with depth exceeding this raises a `RecursionError`. Add `sys.setrecursionlimit(100000)` or convert to iterative using an explicit stack.

**Java Scanner vs BufferedReader performance:** For problems with hundreds of input lines, `Scanner` is significantly slower than `BufferedReader` with `Integer.parseInt`. If your Java solution times out on large inputs, switching to `BufferedReader` often resolves the issue without changing the algorithm.

**Not resetting state between test cases:** In problems with multiple test cases, data structures initialised outside the test case loop retain values from the previous iteration. Always reinitialise arrays, maps, counters, and stacks inside the loop that processes each test case.

**Printing without flushing in Java:** When using `PrintWriter` for output in Java (which is faster than `System.out.println` for large output), forgetting to call `pw.flush()` before the program exits means some output never reaches stdout. Always flush at the end.

```java
PrintWriter pw = new PrintWriter(new BufferedWriter(new OutputStreamWriter(System.out)));
// ... write output with pw.println() ...
pw.flush(); // critical: must flush before exit
```

**Python list multiplication trap:** `[[0]*n]*m` does NOT create an m x n 2D list - it creates m references to the same list. Modifying one row modifies all rows. Always initialise with: `[[0]*n for _ in range(m)]`.

---

## Final Checklist: What to Verify on Exam Day

**Before the exam begins:**
- Select your language of choice from the dropdown on the first problem. Verify it is the language you prepared in.
- Read both problem statements before writing any code.
- Note the input format for each problem: single line, multiple lines, grid format?

**While coding Problem 1:**
- Is your class named `Main` (Java)?
- Are you reading all required input before beginning computation?
- Have you handled the n=0 or empty input case?
- Does your output match the expected format from the sample test case exactly?

**Before submitting Problem 1:**
- Click Run. Do all visible test cases pass?
- If any fail: is the error in your logic or in your output format?
- Remove all debug print statements.
- Click Submit.

**While coding Problem 2:**
- Have you identified the algorithm? State it in words before coding.
- Is your time complexity appropriate for the given constraints?
- Have you handled the boundary cases?
- If fully optimised is not possible, does your brute force at least correctly handle small inputs?

**Final 10 minutes:**
- Both problems should have been submitted at least once. If not, submit whatever you have.
- If time remains, try to fix any known failures in either problem.
- Do not start a completely new approach to Problem 2 with fewer than 15 minutes remaining - the risk of not completing it is too high.

The TCS NQT Advanced Coding section is learnable. The problems follow recognisable patterns, the algorithms are from a known set, and the ninety minutes, while tight, is enough to solve both problems for candidates who have built genuine algorithmic fluency. This guide provides the map. The thirty days of practice that follow provide the capability.

Success in the coding section is not about memorising solutions - it is about building reliable pattern recognition so that when you read "find the minimum maximum load across K convoys," your brain immediately connects it to binary search on the answer, and your fingers already know the template. That connection, built through repetition across thirty days of deliberate practice, is what transforms exam pressure from a liability into a familiar context.

Every line of code you write during preparation is practice for writing code under pressure. Every edge case you catch during practice is an edge case you will catch during the exam. Start the plan, stay consistent, and the Digital or Prime routing you are targeting is entirely within reach.

---

*Problem difficulty assessments and scoring estimates in this guide reflect observed patterns across multiple TCS NQT Advanced Coding cycles. Always verify current platform specifications and supported languages on the TCS iON interface at the start of your exam session.*
