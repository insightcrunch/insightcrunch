---
layout: post
title: "TCS NQT Coding Questions - Prep Guide"
page_title: "TCS NQT Coding Questions - Programming Patterns, Languages Allowed, Common Algorithms, and Preparation Strategy"
date: 2019-07-24
categories: ["Industry"]
tags: ["TCS", "NQT", "Coding Questions", "Programming"]
excerpt: "What coding questions does TCS NQT ask? Problem types, language options, difficulty level, and how to prepare for the programming assessment section."
image: "/assets/images/blog/blog-44.webp"
reading_time: 45
author: "Insight Crunch Team"
last_updated: 2026-03-23
---
The TCS NQT coding section is the most consequential part of the exam for candidates who want to be considered for the Digital track. It is the section where preparation depth matters most, where the gap between prepared and unprepared candidates is widest, and where the investment in genuine algorithmic skill produces the clearest return.

![Technology Industry Analysis - InsightCrunch](/assets/images/blog/blog-44.webp)
*The complete TCS NQT coding preparation guide - what the coding section tests, the five permitted programming languages and how to choose between them, the specific algorithm categories that appear most frequently, worked solutions for Easy and Medium problems, code quality expectations, edge case handling, the scoring system, and a systematic preparation strategy that builds genuine coding competency*

The coding section of the NQT Advanced section presents two programming problems: one at Easy difficulty and one at Medium difficulty, within approximately 45-60 minutes total. Five programming languages are permitted - C, C++, Java, Python, and Perl. Performance in this section, combined with overall NQT score, determines whether a candidate qualifies for the Ninja track, the Digital track, or neither.

This guide covers every dimension of the NQT coding section preparation - not as a list of memorized solutions but as a genuine preparation framework that builds the algorithmic thinking and coding fluency that the section actually tests.

---

## What the Coding Section Actually Evaluates

### The Multi-Dimensional Assessment

Unlike aptitude questions where each question is answered correctly or incorrectly, the NQT coding section uses test case-based scoring. A solution's score is proportional to the percentage of automated test cases it passes. This creates a nuanced evaluation landscape:

**Correctness:** Does the solution produce the correct output for the given inputs? A solution that is logically correct but syntactically broken (a syntax error prevents execution) scores zero. A logically correct solution that handles edge cases incorrectly scores partial marks.

**Efficiency (time complexity):** Test cases sometimes include inputs large enough that O(n^2) or slower solutions time out while O(n log n) or O(n) solutions pass. Writing efficient solutions matters not just conceptually but practically for test case passage rates.

**Code quality:** Many NQT evaluations assess code quality beyond pure test case passage - meaningful variable names, clear logical structure, appropriate use of functions, and readable code style all contribute. A solution that passes all test cases but is written as a single unreadable function with variable names like `a`, `b`, `x` may score lower than an equivalent solution written clearly.

**Edge case handling:** Test cases typically include edge cases - empty arrays, single elements, negative numbers, maximum input sizes. A solution that handles the average case correctly but crashes or produces wrong output on edge cases loses significant test case marks.

**Partial credit:** A solution that passes 7 of 10 test cases scores 70% of that problem's marks. This makes partial solutions genuinely valuable - submitting a partial solution rather than no solution always produces better expected marks.

### What Scores Are Needed for Each Track

Based on documented candidate community reports across multiple NQT windows:

**Ninja track consideration:** Completing the Easy problem with full or near-full test case passage is the minimum coding section performance associated with Ninja qualification. Combined with adequate aptitude and reasoning scores, this qualifies candidates for Ninja track interviews.

**Digital track consideration:** Completing the Easy problem fully AND demonstrating meaningful progress on the Medium problem (passing at least 60-70% of Medium test cases) combined with strong overall NQT scores is the pattern associated with Digital track consideration. Simply completing Easy alone is typically not enough for Digital qualification.

**The implication for preparation:** Easy problem competency is the floor. Digital aspiration requires Medium problem competency. Preparation investment should reflect which outcome you are targeting.

---

## The Five Programming Languages: Which to Choose

### C

C is the foundational language that most engineering students encounter first. It is close to the metal - manual memory management, pointer operations, and a minimal standard library mean that C solutions require more code than equivalent Python or Java solutions.

**When C is a good choice:** If you have deep C fluency from systems programming coursework and can write C code quickly and accurately. The performance advantage of C (fastest execution among the five languages) can matter for problems with tight time limits.

**The risk:** Memory management bugs (buffer overflows, null pointer dereferences, memory leaks) in C do not always produce obvious errors - they sometimes cause silent wrong answers or runtime crashes that are harder to diagnose than Python or Java exceptions. Under exam pressure, these bugs cost more time to find.

**Recommended for:** Candidates from electronics/systems engineering backgrounds who code in C regularly and have strong C pointer and memory management skills.

### C++

C++ combines C's performance with object-oriented features and the Standard Template Library (STL), which provides ready-to-use data structures (vectors, maps, sets, queues, stacks) and algorithms (sort, binary search, lower_bound).

**The STL advantage:** For NQT problems, the STL dramatically reduces the code needed. A problem requiring a sorted collection uses `std::set` in two characters rather than a manually implemented BST. A problem requiring a FIFO queue uses `std::queue` rather than a linked list implementation.

**Key STL knowledge for NQT:**
- `vector<int>`: dynamic array with push_back, size, access by index
- `map<int,int>`: sorted key-value store with O(log n) operations
- `unordered_map<int,int>`: hash map with O(1) average operations
- `set<int>`: sorted unique elements with O(log n) insert/find
- `unordered_set<int>`: hash set with O(1) average operations
- `queue<int>`: FIFO queue with push, pop, front
- `stack<int>`: LIFO stack with push, pop, top
- `priority_queue<int>`: max-heap by default, min-heap with comparison
- `sort(arr.begin(), arr.end())`: O(n log n) sort
- `lower_bound(arr.begin(), arr.end(), target)`: binary search for first element >= target

**Recommended for:** Candidates who know C and have learned STL, or who have competitive programming experience in C++. C++ is the language of choice in competitive programming for good reason - it offers Python-like expressiveness for data structures with C-like performance.

### Java

Java is the most commonly taught language in Indian engineering curricula and the language many freshers are most comfortable with after four years of coursework.

**Java's NQT-relevant advantages:**
- Well-known syntax for most engineering graduates
- Strong standard library (Collections framework: ArrayList, HashMap, HashSet, Stack, Queue implementations via LinkedList and ArrayDeque)
- Explicit exception handling model that prevents silent failures

**Key Java library knowledge for NQT:**
- `ArrayList<Integer>`: dynamic array
- `HashMap<Integer, Integer>`: hash map with put, get, containsKey
- `HashSet<Integer>`: hash set with add, contains, remove
- `LinkedList<Integer>` used as `Queue<Integer>`: FIFO queue
- `ArrayDeque<Integer>` used as `Stack<Integer>`: preferred stack implementation
- `PriorityQueue<Integer>`: min-heap by default
- `Arrays.sort(arr)`: O(n log n) sort
- `Collections.sort(list)`: sort ArrayList

**The verbosity issue:** Java requires more boilerplate than Python - class declarations, main method, type declarations. Under time pressure, this boilerplate adds up. Practice writing Java code quickly without this overhead slowing you down.

**Recommended for:** Candidates whose strongest programming language is Java and who can write Java quickly and correctly. The additional verbosity is worth the comfort advantage if Java is your primary language.

### Python

Python is increasingly the most popular NQT coding language choice for several reasons that are directly relevant to exam performance:

**Why Python wins for NQT:**
- Most concise syntax - fewer characters to write, fewer typing errors, faster code production
- Clean built-in data structures (list, dict, set, deque from collections) that require no import or configuration beyond a one-line import
- No type declaration overhead
- Readable code by default
- Exception handling that produces clear, interpretable error messages

**Key Python knowledge for NQT:**
```python
# Lists
arr = [1, 2, 3]          # creation
arr.append(4)             # add to end
arr.sort()                # in-place sort
sorted(arr)               # returns sorted copy
arr.reverse()             # in-place reverse

# Dictionary
d = {}                    # empty dict
d[key] = value            # add/update
d.get(key, default)       # safe access with default
key in d                  # check membership

# Set
s = set()                 # empty set
s.add(x)                  # add element
x in s                    # O(1) membership check

# Deque (from collections)
from collections import deque
q = deque()
q.append(x)               # add to right
q.appendleft(x)           # add to left
q.popleft()               # remove from left (FIFO)
q.pop()                   # remove from right (LIFO)

# Counter (character/element frequency)
from collections import Counter
freq = Counter(arr)       # {element: count} dict
most_common = freq.most_common(k)  # k most frequent elements

# DefaultDict
from collections import defaultdict
d = defaultdict(int)      # default value is 0 for int
d = defaultdict(list)     # default value is [] for list
```

**The Python efficiency consideration:** Python is slower than C/C++/Java in execution speed. For most NQT problems, this does not matter - the test cases are not sized to specifically time out Python solutions. For problems with very large inputs and tight time limits, Python's speed can be a factor. If you encounter a time limit exceeded error in Python, consider optimization strategies (using built-in functions rather than loops, choosing more efficient algorithms) before switching languages.

**Recommended for:** Candidates comfortable with Python and able to write Python code quickly and accurately. For most freshers starting preparation today, Python is the recommended language to learn for NQT coding if they do not have strong competency in another language.

### Perl

Perl is an option but is rarely chosen in practice. Perl's syntax is arcane compared to modern languages, it is not part of most engineering curricula, and it offers no significant advantage over Python for NQT problem types.

**Recommendation:** Unless you have significant Perl experience from personal or professional work, do not use Perl for NQT.

---

## Algorithm Categories: What Appears and Why

### Category 1: Array Problems (Most Frequent)

Arrays are the most fundamental data structure and the most consistently tested category in NQT coding. Problems involving arrays appear in both Easy and Medium difficulty.

**Easy array patterns:**

*Linear search and counting:*
Find all elements meeting a condition, count occurrences, find maximum or minimum. O(n) single pass.

*Two-pointer technique:*
Two indices starting at opposite ends of a sorted array and moving toward each other. Used for: pair sum problems, removing duplicates, container with most water.

*Frequency/hash map counting:*
Count occurrences of each element in O(n). Used for: finding duplicates, finding the element that appears once, finding elements that appear exactly k times.

*Prefix sum:*
Precompute cumulative sums to answer range sum queries in O(1). Used for: subarray sum equals target, number of subarrays with given sum.

**Medium array patterns:**

*Sliding window:*
Maintain a window of elements that satisfies a condition, slide it across the array. Used for: maximum sum subarray of size k, longest substring with k distinct characters, minimum window substring.

*Sorting + greedy:*
Sort the array and apply a greedy strategy. Used for: activity selection, interval merging, minimum number of platforms.

*Binary search on answer:*
When the answer has a monotonic property (more resources → easier constraint satisfaction), binary search on the answer space. Used for: allocate minimum pages, aggressive cows, painters partition.

**Sample Medium Array Problem: Rearrange Array Alternately**
Given a sorted array, rearrange it such that the maximum and minimum alternate.

Input: [1, 2, 3, 4, 5, 6, 7]
Output: [7, 1, 6, 2, 5, 3, 4]

```python
def rearrange(arr):
    n = len(arr)
    result = []
    left, right = 0, n - 1
    toggle = True
    while left <= right:
        if toggle:
            result.append(arr[right])
            right -= 1
        else:
            result.append(arr[left])
            left += 1
        toggle = not toggle
    return result
```

### Category 2: String Problems (Second Most Frequent)

String manipulation problems are consistently present in NQT coding. They test both the ability to work with string operations efficiently and the ability to recognize string patterns.

**Easy string patterns:**

*Palindrome checking:*
Two-pointer approach from both ends. O(n).

*Anagram detection:*
Sort both strings and compare, or use frequency counting with hash map. O(n log n) or O(n).

*Character frequency analysis:*
Count occurrences of each character. Use for: most frequent character, first non-repeating character, character frequency comparison.

*String reversal:*
Reverse entire string, or reverse word by word.

**Medium string patterns:**

*Sliding window for substring problems:*
Find longest/shortest substring satisfying a condition. Template:
```python
left = 0
window_state = {}  # track window contents
result = 0
for right in range(len(s)):
    # expand window: add s[right] to state
    while window_violates_condition(window_state):
        # shrink window from left
        left += 1
    result = max(result, right - left + 1)
return result
```

*Pattern matching:*
Check if string matches a pattern (like "aab" matching "ccd"). Use two hash maps for bijective mapping.

*String compression:*
Run-length encoding (aabcccdddd → a2b1c3d4). Simple single-pass.

**Sample Easy String Problem: Longest Common Prefix**
Given an array of strings, find the longest common prefix.

Input: ["flower", "flow", "flight"]
Output: "fl"

```python
def longest_common_prefix(strs):
    if not strs:
        return ""
    prefix = strs[0]
    for s in strs[1:]:
        while not s.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    return prefix
```

**Sample Medium String Problem: Group Anagrams**
Given a list of strings, group anagrams together.

Input: ["eat", "tea", "tan", "ate", "nat", "bat"]
Output: [["eat","tea","ate"], ["tan","nat"], ["bat"]]

```python
from collections import defaultdict

def group_anagrams(strs):
    groups = defaultdict(list)
    for s in strs:
        key = tuple(sorted(s))
        groups[key].append(s)
    return list(groups.values())
```

### Category 3: Linked List Problems

Linked list problems test the ability to work with pointer-based data structures and require careful management of node references.

**Easy linked list patterns:**

*Traversal and search:*
Walk through the list to find elements, count nodes, find the kth node.

*Reversal:*
Three-pointer reversal (prev, current, next). Fundamental operation.

```python
def reverse_linked_list(head):
    prev = None
    current = head
    while current:
        next_node = current.next
        current.next = prev
        prev = current
        current = next_node
    return prev  # new head
```

*Middle element:*
Slow and fast pointer - fast moves twice as fast as slow. When fast reaches end, slow is at middle.

```python
def find_middle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow
```

**Medium linked list patterns:**

*Cycle detection (Floyd's Algorithm):*
Slow moves 1 step, fast moves 2 steps. If they meet, there is a cycle.

*Merge two sorted lists:*
Compare heads recursively or iteratively, link the smaller node.

```python
def merge_sorted_lists(l1, l2):
    dummy = Node(0)
    current = dummy
    while l1 and l2:
        if l1.val <= l2.val:
            current.next = l1
            l1 = l1.next
        else:
            current.next = l2
            l2 = l2.next
        current = current.next
    current.next = l1 or l2
    return dummy.next
```

*Remove nth node from end:*
Two-pointer approach - advance fast pointer n steps, then move both until fast reaches end.

### Category 4: Tree Problems

Tree problems test hierarchical data structure understanding and recursive thinking.

**Easy tree patterns:**

*Inorder, preorder, postorder traversal (recursive):*
```python
def inorder(root, result=[]):
    if root:
        inorder(root.left, result)
        result.append(root.val)
        inorder(root.right, result)
    return result
```

*Maximum depth:*
```python
def max_depth(root):
    if not root:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))
```

*Check if balanced:*
A tree is balanced if the depth difference between left and right subtrees is at most 1 for every node.

**Medium tree patterns:**

*Level-order traversal (BFS):*
Uses a queue. All nodes at each level are processed before moving to the next.

```python
from collections import deque

def level_order(root):
    if not root:
        return []
    result = []
    queue = deque([root])
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

*Lowest Common Ancestor (LCA):*
```python
def lca(root, p, q):
    if not root or root == p or root == q:
        return root
    left = lca(root.left, p, q)
    right = lca(root.right, p, q)
    if left and right:
        return root
    return left or right
```

*Validate Binary Search Tree:*
```python
def is_valid_bst(root, min_val=float('-inf'), max_val=float('inf')):
    if not root:
        return True
    if root.val <= min_val or root.val >= max_val:
        return False
    return (is_valid_bst(root.left, min_val, root.val) and
            is_valid_bst(root.right, root.val, max_val))
```

### Category 5: Dynamic Programming

DP problems require recognizing that the problem has optimal substructure (optimal solutions built from optimal subsolutions) and overlapping subproblems (same subproblems solved repeatedly).

**Pattern recognition - DP indicators in problem statement:**
- "Maximum/minimum" outcome
- "Number of ways" to achieve something
- "Can you achieve" some target
- Optimization over a sequence

**Easy DP patterns:**

*Fibonacci sequence variants:*
Classic DP - each value depends on the two preceding values. Space-optimized with two variables.

*Climbing stairs:*
To reach step n, you came from step n-1 or n-2. ways(n) = ways(n-1) + ways(n-2).

**Medium DP patterns:**

*0/1 Knapsack:*
Given items with weights and values, and a weight capacity, maximize total value.

```python
def knapsack(weights, values, capacity):
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i-1][w], 
                              dp[i-1][w - weights[i-1]] + values[i-1])
            else:
                dp[i][w] = dp[i-1][w]
    return dp[n][capacity]
```

*Longest Common Subsequence:*
```python
def lcs(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]
```

*Coin Change:*
Given denominations and a target amount, find the minimum number of coins to make the amount.

```python
def coin_change(coins, amount):
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for coin in coins:
        for i in range(coin, amount + 1):
            dp[i] = min(dp[i], dp[i - coin] + 1)
    return dp[amount] if dp[amount] != float('inf') else -1
```

### Category 6: Mathematical Problems

Mathematical problems test number theory, combinatorics, and pattern recognition in numerical contexts.

**Prime checking:**
```python
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
```

**Sieve of Eratosthenes (all primes up to n):**
```python
def sieve(n):
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, n+1, i):
                is_prime[j] = False
    return [i for i in range(2, n+1) if is_prime[i]]
```

**GCD (Euclidean algorithm):**
```python
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a
```

**Factorial and modular arithmetic:**
For large factorial problems, compute modulo a prime to prevent overflow.

---

## The Complete NQT Coding Preparation Strategy

### Phase 1: Language Fluency (Weeks 1-2)

Before tackling algorithm problems, ensure your chosen language is fluent enough to write correct code quickly under pressure.

**Python fluency checklist:**
- Write a function that sorts a list (use sorted() and sort())
- Write a function that counts character frequency in a string
- Use a defaultdict to group items
- Use enumerate() and zip() in loops
- Write a list comprehension that filters and transforms
- Use collections.deque for BFS queue
- Handle edge cases with if not arr or if n == 0 checks

**Java fluency checklist:**
- Declare and use ArrayList, HashMap, HashSet
- Use enhanced for loop and iterator
- Use Arrays.sort() and Collections.sort()
- Implement a Queue using ArrayDeque
- Use Integer.parseInt() and String.valueOf()
- Write proper input reading (Scanner or BufferedReader)
- Handle NullPointerException risk with null checks

If you can execute all items on the checklist without looking up syntax, you have adequate language fluency. If any item requires reference, practice it until it is automatic.

### Phase 2: Easy Problem Fluency (Weeks 3-5)

Target: solve Easy-level problems in 15-18 minutes consistently.

**The Easy problem list to master:**
1. Two Sum (find pair summing to target using hash map)
2. Palindrome check (two-pointer)
3. Reverse a string/array (in-place)
4. Find the missing number in 1 to n (sum formula or XOR)
5. First non-repeating character (frequency map + linear scan)
6. Count words in a string
7. Check if two strings are anagrams (sorted comparison or frequency count)
8. Maximum of array using single pass
9. Remove duplicates from sorted array (two-pointer)
10. Fibonacci (iterative with space optimization)
11. Reverse a linked list (three-pointer)
12. Find middle of linked list (slow-fast pointer)
13. Maximum depth of binary tree (recursive)
14. Check if number is prime
15. Factorial (iterative and recursive)

For each problem: understand the approach, code it without reference, trace through with a sample input, check for edge cases, and verify it runs correctly.

**LeetCode Easy practice:** After mastering the above 15, practice 20 additional LeetCode Easy problems sorting by acceptance rate (highest first). High acceptance rate = commonly solvable = appropriate warmup difficulty.

### Phase 3: Medium Problem Competency (Weeks 6-8)

Target: solve Medium-level problems - reach meaningful progress (passing 60%+ of test cases) within 30-35 minutes.

**The Medium problem list to master:**
1. Longest substring without repeating characters (sliding window)
2. Search in a rotated sorted array (binary search variant)
3. Product of array except self (prefix and suffix products)
4. Find all anagrams in a string (sliding window with frequency map)
5. Minimum number of platforms/meeting rooms (sorting + sweep)
6. Detect cycle in linked list (Floyd's algorithm)
7. Level-order traversal of binary tree (BFS)
8. Number of islands (DFS/BFS on grid)
9. Coin change (DP)
10. Longest common subsequence (DP)
11. Group anagrams (hash map with sorted key)
12. 3Sum (sorting + two-pointer)
13. Merge intervals (sorting + greedy)
14. Jump game (greedy or DP)
15. Binary tree right side view (BFS, take last of each level)

For each problem: spend maximum 5 minutes understanding the approach (do not look at solutions), spend 25-30 minutes implementing and debugging, then review a clean solution and identify what your approach missed or could have been cleaner.

### Phase 4: Timed Mock Coding Tests (Week 9-12)

**The weekly timed mock format:**
Set a 45-minute timer. Take one Easy problem and one Medium problem. Attempt both under real exam pressure.

After the 45 minutes:
- Score yourself: did you complete Easy? How many Medium test cases would you pass?
- Review where time was lost
- Identify any bug patterns that appear repeatedly
- Note edge cases you missed

**Target progression:**
- Week 9: Complete Easy in 20 min, pass 40% Medium test cases
- Week 10: Complete Easy in 18 min, pass 55% Medium test cases
- Week 11: Complete Easy in 16 min, pass 65% Medium test cases
- Week 12: Complete Easy in 15 min, pass 70%+ Medium test cases

Reaching this progression means arriving at the NQT with genuine Digital-track coding competency.

The [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html) includes coding practice problems calibrated to NQT difficulty, providing the structured practice that builds this progression systematically.

---

## Code Quality: What TCS Evaluates Beyond Correctness

### Naming Conventions

Variable names should describe what they contain, not where they are in the code or what type they are.

**Poor naming:**
```python
def f(a, b):
    x = 0
    for i in range(len(a)):
        if a[i] == b:
            x += 1
    return x
```

**Good naming:**
```python
def count_target_occurrences(arr, target):
    count = 0
    for element in arr:
        if element == target:
            count += 1
    return count
```

The second function communicates its purpose, the role of each variable, and the logic without any comments. This readability is what TCS's code quality assessment values.

### Function Structure

Break complex solutions into helper functions rather than writing everything in one block.

```python
def is_palindrome(s):
    """Check if string is a palindrome ignoring case and non-alphanumeric."""
    cleaned = clean_string(s)
    return cleaned == cleaned[::-1]

def clean_string(s):
    """Return only alphanumeric characters in lowercase."""
    return ''.join(c.lower() for c in s if c.isalnum())
```

This structure is more readable, more testable, and more maintainable than a single function doing everything.

### Input Validation and Edge Cases

Every NQT solution should handle these edge cases explicitly:

**Empty input:**
```python
def solve(arr):
    if not arr:          # handles None and empty list
        return 0         # or appropriate default
    # main logic
```

**Single element:**
Many algorithms that work for multiple elements break on single elements. Verify your solution handles `arr = [5]` correctly.

**All same elements:**
`arr = [3, 3, 3, 3]` reveals bugs in algorithms that assume all elements are distinct.

**Negative numbers:**
`arr = [-5, -3, -1, 0, 2]` reveals bugs in algorithms written with the assumption of positive values.

**Maximum input size:**
Think about whether your algorithm would complete within the time limit for the maximum possible input. An O(n^2) solution for n=10^5 requires 10^10 operations - way too slow.

### Comments

Brief comments on non-obvious logic choices are valued:

```python
# Use two pointers from both ends - O(n) time, O(1) space
left, right = 0, len(s) - 1
while left < right:
    if s[left] != s[right]:
        return False
    left += 1
    right -= 1
return True
```

Comments should explain WHY, not WHAT. "increment left pointer" is a comment that says what the code does, which is already visible. "Move toward center to compare next character pair" says why.

---

## Handling the Two-Problem Structure Strategically

### The Time Allocation Decision Tree

When the exam begins and you read both problems:

**If Easy seems straightforward (solvable in 15-20 minutes):**
Complete Easy fully. Then spend remaining time on Medium. This is the standard approach.

**If Easy seems hard (expected to take 25+ minutes):**
Skim Medium to assess its difficulty. If Medium looks easier than Easy (which occasionally happens when the "Easy" label is relative), start with Medium. This is rare but worth knowing.

**If both seem hard:**
Complete as much of Easy as possible in 20 minutes, submit partial solution, then attempt Medium. Partial solutions score partial marks - both partial attempts together may outscore one complete solution.

**Never scenario:** Do not spend 40 minutes trying to perfect Easy and leave no time for Medium. The expected value calculation strongly favors submitting a complete Easy and a partial Medium over a perfect Easy and no Medium attempt.

### When to Submit Intermediate Solutions

The NQT coding interface allows multiple submissions. Use this feature strategically:

Submit after completing the Easy problem (before starting Medium). This ensures those marks are locked in even if the exam interface crashes or you run out of time.

Submit a partial Medium solution whenever you have implemented the core logic but are missing edge cases. If your partial solution passes 5 test cases before you add edge case handling, those 5 are secured. Improving to 8 test cases after edge case handling adds 3 more.

Do not wait for a perfect solution before submitting. Progressive submission is always better than waiting.

### Debugging Under Pressure

When a solution is not passing test cases and you have limited time:

**Step 1:** Trace through the algorithm manually with a simple example. Does the logic produce the expected output?

**Step 2:** Check the most common error types:
- Off-by-one (should the loop go to n or n-1? Should the range start at 0 or 1?)
- Null/None check missing (what if the input is empty or None?)
- Wrong comparison operator (< vs <=, != vs ==)
- Integer division instead of float division (in Python 3, / gives float and // gives integer)
- Missing return statement

**Step 3:** If manual tracing does not reveal the bug, try the provided examples step by step through your code. Identify the exact step where the output diverges from expected.

**Step 4:** If you cannot find the bug within 5 minutes of debugging, submit what you have and move on. A partially correct solution earns partial marks; continuing to debug while time runs out earns zero marks for the other problem.

---

## Language-Specific Pitfalls to Avoid

### Python Pitfalls

**Mutable default argument:**
```python
# WRONG - the default list is shared across calls
def append_to(element, to=[]):
    to.append(element)
    return to

# CORRECT
def append_to(element, to=None):
    if to is None:
        to = []
    to.append(element)
    return to
```

**Integer division vs. float division:**
```python
5 / 2   # 2.5 (float division in Python 3)
5 // 2  # 2 (integer/floor division)
```

**List as function output vs. generator:**
When you need a list, use `list(range(n))` not `range(n)` - `range` returns a lazy generator that is list-like but not a list.

**Deepcopy vs. shallow copy:**
```python
import copy
deep = copy.deepcopy(nested_list)    # fully independent copy
shallow = nested_list.copy()          # top-level copy; nested objects shared
shallow = nested_list[:]              # same as shallow copy
```

### Java Pitfalls

**Integer comparison using == vs .equals():**
```java
Integer a = 127, b = 127;  // a == b is True (cached)
Integer x = 200, y = 200;  // x == y is False (not cached!)
// Always use x.equals(y) for Integer comparison
```

**NullPointerException:**
Always check for null before calling methods on objects that might be null.
```java
if (node != null && node.val == target) { ... }
// NOT: if (node.val == target)  // throws NPE if node is null
```

**Array index out of bounds:**
Check array length before accessing by index.

### C++ Pitfalls

**Accessing vector elements out of bounds:**
`vec[i]` does not check bounds. Use `vec.at(i)` for bounds-checked access, or verify manually.

**Integer overflow:**
Operations on `int` that exceed 2^31-1 overflow silently. Use `long long` for large values.

**Not returning from non-void functions:**
Forgetting a return statement in a function that should return a value produces undefined behavior.

---

## Frequently Asked Questions About TCS NQT Coding

**Q1: What is the difficulty level of TCS NQT coding questions?**

The Easy problem is comparable to LeetCode Easy - solvable in 15-20 minutes with basic programming knowledge and data structure understanding. The Medium problem is comparable to LeetCode Medium - requiring algorithmic thinking and 25-35 minutes for a complete solution. The Easy problem is similar in difficulty across NQT windows; the Medium problem varies more.

**Q2: Which programming language is best for TCS NQT coding?**

Python is generally recommended for candidates who do not have a strongly preferred language, due to its concise syntax and built-in data structures. Java is the best choice if you are most comfortable in Java and can code it quickly. C++ is excellent if you know the STL well. Do not use a language you are not fluent in just because it seems "better" - fluency matters more than language choice.

**Q3: How many coding problems are in TCS NQT?**

Typically two - one Easy and one Medium, within approximately 45-60 minutes total. The specific time and exact question count may vary by NQT window.

**Q4: Does TCS NQT coding use online judging (automated test cases)?**

Yes. Solutions are evaluated against automated test cases. The percentage of test cases passed determines the score for each problem. This means partial solutions score partial marks.

**Q5: What topics appear most in TCS NQT coding?**

Arrays (most frequent), strings (second most frequent), linked lists, trees, basic DP, and mathematical problems. The [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html) covers all these categories with NQT-calibrated practice problems.

**Q6: Do I need to know all five languages or just one?**

One language to fluency is sufficient. Knowing multiple languages at shallow levels is less useful than knowing one language deeply. Practice all solutions in your chosen language until you can write them quickly and correctly.

**Q7: Is there negative marking in the coding section?**

No. The coding section scores based on test case passage rates. Submitting a partial or incorrect solution does not create negative marks - it simply scores lower than a complete solution. Always submit something rather than leaving the problem unattempted.

**Q8: What should I do if I cannot figure out the algorithm for the Medium problem?**

Implement a brute-force solution (even O(n^2) or O(n^3)) and submit it. Many NQT test cases pass with brute-force solutions - the test data may not be large enough to expose TLE (Time Limit Exceeded) for brute force. A working brute-force solution that passes 5-6 test cases scores 50-60% of the problem's marks, which is significantly better than a zero.

**Q9: How do I practice specifically for TCS NQT coding level?**

LeetCode Easy (first 30-40 problems sorted by acceptance rate) builds the Easy problem fluency. LeetCode Medium (focusing on arrays, strings, linked lists, trees, and DP categories) builds the Medium problem competency. The [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html) provides NQT-specific practice. Two or three timed mock coding sessions per week (one Easy + one Medium in 45 minutes) builds exam-condition performance.

**Q10: What is the difference between NQT Ninja and Digital in terms of coding?**

Ninja track qualification does not require strong coding performance - adequate aptitude, reasoning, and verbal scores with even partial Easy problem completion can qualify for Ninja. Digital track requires strong overall scores with specifically strong coding - completing Easy fully and making substantial progress on Medium is the typical Digital coding threshold.

**Q11: How important is it to write clean code vs. just getting the right answer?**

Both matter. A clean solution that passes all test cases scores higher than an equivalent messy solution in evaluations that include code quality. In practice, clean code also reduces the probability of bugs, making it both ethically and practically the right approach.

**Q12: Can I use recursion in TCS NQT coding?**

Yes. Recursive solutions are fully acceptable and often the clearest way to express tree-based algorithms. Be aware of Python's default recursion limit (typically 1000) for deep recursion - add `sys.setrecursionlimit(10000)` at the start of your solution if needed.

**Q13: What should I do if I encounter a question type I have never seen?**

Read the problem carefully twice. Identify the core transformation: what is the input and what is the desired output? Think about which data structure would make the required operations efficient. Try to write a brute-force solution that is definitely correct, even if not efficient. Submit the brute-force, then optimize if time permits.

**Q14: Is it helpful to practice competitive programming for TCS NQT?**

Competitive programming practice (Codeforces, AtCoder, LeetCode contests) builds the algorithmic thinking and coding speed that NQT rewards. However, the difficulty level of competitive programming can significantly exceed NQT difficulty. Focus on problems at Codeforces Div. 2 A and B difficulty, or LeetCode Easy and Medium - these calibrate better to NQT difficulty than harder competitive programming problems.

**Q15: How long before the NQT should I start coding preparation?**

Ideally 3-4 months before the target NQT window. Coding skill builds slowly - consistent daily practice over months produces far better results than intense preparation in the final weeks. Begin with Easy problems and build up to Medium problems over the 3-4 month period, using the [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html) alongside LeetCode for structured and timed practice.

---

## The Coding Mindset: Thinking Like an Engineer

### Decompose Before You Code

The most consistent error in NQT coding (and in programming generally) is starting to type before having a clear algorithm in mind. The candidates who perform best spend more of their available time in the thinking phase and less in the typing phase.

**The five-minute plan:**
After reading the problem, spend five minutes:
1. Restating the problem in your own words
2. Identifying the input format and constraints
3. Working through a small example manually
4. Identifying the algorithm approach (brute force first, then optimal)
5. Identifying potential edge cases

Five minutes of clear thinking saves ten minutes of debugging confused code.

### Test Cases as Design Tools

Before writing code, generate your own test cases:

**Normal case:** `arr = [3, 1, 4, 1, 5, 9, 2]` - typical input
**Edge case 1:** `arr = []` - empty input
**Edge case 2:** `arr = [7]` - single element
**Edge case 3:** `arr = [1, 1, 1, 1]` - all same elements
**Edge case 4:** negative numbers if applicable

If you cannot trace through your algorithm with these test cases and produce the expected outputs, your algorithm is not complete. Fixing issues at the mental simulation stage is faster than fixing them after coding.

### The Correct-Then-Optimize Sequence

Always implement a correct solution first, even if it is not optimal. A correct O(n^2) solution that you can optimize to O(n log n) is better than an attempted O(n) solution that has a bug you cannot find.

Submit the correct brute-force. Then optimize if time permits.

This sequence is both practically better (guaranteed partial marks) and intellectually better (you understand the problem fully before optimizing).

---

## Building Toward the NQT: The Complete Coding Path

The path from "I cannot solve Easy problems in 20 minutes" to "I can solve Easy in 15 minutes and pass 70% of Medium test cases" is a genuine progression that requires approximately 3-4 months of consistent practice.

It is not a mysterious progression. The skills are:
- Array manipulation fluency (built through LeetCode Easy arrays)
- String operation fluency (built through LeetCode Easy strings)
- Hash map usage fluency (built through frequency counting problems)
- Two-pointer technique (built through sorted array problems)
- Sliding window technique (built through substring problems)
- Linked list pointer manipulation (built through basic linked list problems)
- Tree recursion (built through tree traversal and property problems)
- Basic DP pattern recognition (built through the canonical DP problems)

Each of these skills has a definable current level and a definable target level. The gap between your current level and the NQT target level is entirely bridgeable through deliberate, consistent practice.

The [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html) provides the structured practice that builds these skills systematically, with problems organized by category and difficulty that map directly to NQT coding question types.

Start with the Easy problems. Master the fundamentals. Build up to Medium competency. Show up at the NQT with genuine coding skill - not memorized solutions, but the algorithmic thinking and language fluency that handles whatever problems appear.

That is what the NQT coding section rewards. That is what this guide is designed to help you build.

---

## Comprehensive Algorithm Patterns: Deep Reference Guide

### Two-Pointer Technique: Complete Coverage

The two-pointer technique is one of the most versatile patterns in NQT coding, applicable to sorted arrays, strings, and linked list problems.

**Pattern 1: Opposite-direction pointers**
Start one pointer at the beginning, one at the end. Move them toward each other based on a condition.

Valid palindrome check:
```python
def is_palindrome(s):
    s = ''.join(c.lower() for c in s if c.isalnum())
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True
```

Two sum in sorted array:
```python
def two_sum_sorted(arr, target):
    left, right = 0, len(arr) - 1
    while left < right:
        current_sum = arr[left] + arr[right]
        if current_sum == target:
            return [left, right]
        elif current_sum < target:
            left += 1
        else:
            right -= 1
    return []
```

3Sum - all triplets summing to zero:
```python
def three_sum(nums):
    nums.sort()
    result = []
    for i in range(len(nums) - 2):
        if i > 0 and nums[i] == nums[i-1]:
            continue
        left, right = i + 1, len(nums) - 1
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            if total == 0:
                result.append([nums[i], nums[left], nums[right]])
                while left < right and nums[left] == nums[left+1]:
                    left += 1
                while left < right and nums[right] == nums[right-1]:
                    right -= 1
                left += 1
                right -= 1
            elif total < 0:
                left += 1
            else:
                right -= 1
    return result
```

**Pattern 2: Same-direction pointers (slow-fast)**

Remove duplicates from sorted array:
```python
def remove_duplicates(nums):
    if not nums:
        return 0
    slow = 0
    for fast in range(1, len(nums)):
        if nums[fast] != nums[slow]:
            slow += 1
            nums[slow] = nums[fast]
    return slow + 1
```

### Sliding Window: Complete Coverage

**Fixed-size window:**
```python
def max_sum_subarray_k(arr, k):
    if len(arr) < k:
        return 0
    window_sum = sum(arr[:k])
    max_sum = window_sum
    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]
        max_sum = max(max_sum, window_sum)
    return max_sum
```

**Variable-size window:**
```python
def min_size_subarray_sum(target, nums):
    left = 0
    current_sum = 0
    min_length = float('inf')
    for right in range(len(nums)):
        current_sum += nums[right]
        while current_sum >= target:
            min_length = min(min_length, right - left + 1)
            current_sum -= nums[left]
            left += 1
    return min_length if min_length != float('inf') else 0
```

### Hash Map Patterns: Complete Coverage

**Frequency counting:**
```python
from collections import Counter

def find_majority_element(nums):
    counts = Counter(nums)
    n = len(nums)
    for element, count in counts.items():
        if count > n // 2:
            return element
    return -1
```

**Complement lookup:**
```python
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
```

**Prefix sum with hash map:**
```python
def subarray_sum_equals_k(nums, k):
    count = 0
    prefix_sum = 0
    prefix_counts = {0: 1}
    for num in nums:
        prefix_sum += num
        count += prefix_counts.get(prefix_sum - k, 0)
        prefix_counts[prefix_sum] = prefix_counts.get(prefix_sum, 0) + 1
    return count
```

### Graph Problems (BFS and DFS on Grids)

**Number of Islands (DFS):**
```python
def num_islands(grid):
    if not grid:
        return 0
    count = 0
    rows, cols = len(grid), len(grid[0])
    def dfs(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != '1':
            return
        grid[r][c] = '0'
        dfs(r+1,c); dfs(r-1,c); dfs(r,c+1); dfs(r,c-1)
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                dfs(r, c)
                count += 1
    return count
```

---

## The Mental Models Behind Algorithm Selection

### "What Data Structure Makes This Efficient?"

When you read an NQT coding problem, ask: what operations does this problem require, and what data structure makes those operations efficient?

**O(1) lookup by value:** Use a hash set or hash map.
**O(log n) lookup in sorted data:** Use binary search.
**O(1) access by index:** Use an array/list.
**O(1) FIFO access:** Use a deque.
**O(log n) access to min/max dynamically:** Use a priority queue (heap).
**Graph traversal:** BFS for shortest path; DFS for connectivity.

### "What is the Brute Force? How Can I Optimize It?"

For array/string problems:
- Brute force: O(n^2) with nested loops
- One optimization: O(n log n) with sorting + one pass
- Optimal: O(n) with hash map or sliding window

For tree/graph problems:
- Brute force: recompute at every node
- Optimization: bottom-up DP or memoization

For DP problems:
- Brute force: recursive with overlapping subproblems
- Optimization: add memoization (top-down DP)
- Further: convert to iterative table (bottom-up DP)

---

## The Complete NQT Coding Readiness Checklist

Before any NQT window, verify your coding readiness:

**Language fluency:**
- Two-sum with hash map in under 5 minutes
- Linked list reversal in under 5 minutes
- Binary tree inorder traversal in under 5 minutes

**Easy problem competency (15-18 minutes each):**
- Palindrome check (two-pointer)
- First non-repeating character (frequency map)
- Two sum (hash map)
- Reverse linked list (three-pointer)
- Maximum depth of binary tree (recursive)

**Medium problem competency (65%+ test cases in 30-35 minutes):**
- Longest substring without repeating (sliding window)
- Detect cycle in linked list (Floyd's)
- Number of islands (DFS)
- Level-order tree traversal (BFS)
- Coin change (DP)

**Edge case awareness:**
- Always checks for empty input
- Considers single-element case
- Considers negative numbers where applicable
- Considers duplicate values where applicable

**Code quality:**
- Meaningful variable names
- Helper functions for complex logic
- Brief comments for non-obvious steps
- Explicit return statements

The coding section rewards consistent practice above all else. The [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html) provides the structured problem sets that build this readiness systematically. Practice genuinely. Build the skill. Show up ready to code well.

---

## Advanced Topics: When Easy Becomes Medium

### Sorting Algorithms: Understanding Beyond Bubble Sort

Most NQT coding problems use the language's built-in sort (which is O(n log n) and correct). However, understanding how sorting algorithms work enables better algorithmic thinking overall.

**Merge Sort - the divide and conquer model:**
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
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
```

Merge sort is O(n log n) time and O(n) space. The merge operation is itself a useful pattern for problems involving two sorted arrays (merge sorted lists, find intersection of sorted arrays).

**Quick Sort - the partition model:**
Understanding quicksort's partition is essential for problems like "find the kth largest element" using QuickSelect.

```python
def quickselect(arr, k):
    """Find kth largest element (1-indexed) in O(n) average time."""
    def partition(left, right, pivot_idx):
        pivot = arr[pivot_idx]
        arr[pivot_idx], arr[right] = arr[right], arr[pivot_idx]
        store_idx = left
        for i in range(left, right):
            if arr[i] > pivot:  # descending order for kth largest
                arr[i], arr[store_idx] = arr[store_idx], arr[i]
                store_idx += 1
        arr[store_idx], arr[right] = arr[right], arr[store_idx]
        return store_idx
    
    left, right = 0, len(arr) - 1
    k -= 1  # convert to 0-indexed
    while left <= right:
        pivot_idx = partition(left, right, (left + right) // 2)
        if pivot_idx == k:
            return arr[k]
        elif pivot_idx < k:
            left = pivot_idx + 1
        else:
            right = pivot_idx - 1
```

### Heap Operations

Priority queues (heaps) solve "find the k largest/smallest" class of problems efficiently.

**Kth Largest Element using a min-heap of size k:**
```python
import heapq

def find_kth_largest(nums, k):
    """O(n log k) solution using min-heap."""
    heap = []
    for num in nums:
        heapq.heappush(heap, num)
        if len(heap) > k:
            heapq.heappop(heap)  # remove smallest
    return heap[0]  # kth largest is smallest in heap of size k
```

**Median from data stream:**
Use two heaps - max-heap for lower half, min-heap for upper half.

```python
import heapq

class MedianFinder:
    def __init__(self):
        self.lower = []  # max-heap (negate values for Python's min-heap)
        self.upper = []  # min-heap
    
    def add_num(self, num):
        heapq.heappush(self.lower, -num)
        # Balance: move largest of lower to upper
        heapq.heappush(self.upper, -heapq.heappop(self.lower))
        # Ensure lower has equal or one more element
        if len(self.upper) > len(self.lower):
            heapq.heappush(self.lower, -heapq.heappop(self.upper))
    
    def find_median(self):
        if len(self.lower) > len(self.upper):
            return -self.lower[0]
        return (-self.lower[0] + self.upper[0]) / 2
```

### String Problems: Advanced Patterns

**Minimum Window Substring:**
Given strings s and t, find the minimum window in s containing all characters of t.

```python
from collections import Counter

def min_window(s, t):
    if not s or not t:
        return ""
    
    t_count = Counter(t)
    required = len(t_count)
    formed = 0
    window_counts = {}
    
    left = right = 0
    min_len = float('inf')
    min_left = 0
    
    while right < len(s):
        char = s[right]
        window_counts[char] = window_counts.get(char, 0) + 1
        
        if char in t_count and window_counts[char] == t_count[char]:
            formed += 1
        
        while left <= right and formed == required:
            if right - left + 1 < min_len:
                min_len = right - left + 1
                min_left = left
            
            left_char = s[left]
            window_counts[left_char] -= 1
            if left_char in t_count and window_counts[left_char] < t_count[left_char]:
                formed -= 1
            left += 1
        
        right += 1
    
    return "" if min_len == float('inf') else s[min_left:min_left + min_len]
```

### Advanced DP: Interval DP and Path Problems

**Maximum profit with stock prices:**
```python
def max_profit(prices):
    """Single transaction: buy once, sell once."""
    if not prices:
        return 0
    min_price = float('inf')
    max_profit = 0
    for price in prices:
        min_price = min(min_price, price)
        max_profit = max(max_profit, price - min_price)
    return max_profit
```

**Unique paths in grid:**
```python
def unique_paths(m, n):
    """Count paths from top-left to bottom-right in m x n grid."""
    dp = [[1] * n for _ in range(m)]
    for i in range(1, m):
        for j in range(1, n):
            dp[i][j] = dp[i-1][j] + dp[i][j-1]
    return dp[m-1][n-1]
```

**Edit Distance (Levenshtein distance):**
```python
def edit_distance(word1, word2):
    m, n = len(word1), len(word2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i  # delete all from word1
    for j in range(n + 1):
        dp[0][j] = j  # insert all of word2
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i-1] == word2[j-1]:
                dp[i][j] = dp[i-1][j-1]  # no operation needed
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],    # delete from word1
                    dp[i][j-1],    # insert into word1
                    dp[i-1][j-1]   # replace
                )
    return dp[m][n]
```

---

## Frequently Asked Questions About TCS NQT Coding (Extended)

**Q16: What is the typical scoring breakdown between Easy and Medium problems?**

TCS does not publish exact point allocations publicly. Based on candidate reports, the Easy and Medium problems contribute roughly equally to the coding section score (each with multiple test cases). This means that fully completing Easy and partially completing Medium produces a higher score than leaving Medium entirely unattempted. Always attempt both.

**Q17: Is object-oriented code required or preferred in TCS NQT?**

TCS NQT coding problems are typically solvable with functional or procedural code - class definitions are not required unless the problem specifically involves object modeling. Write the clearest, most correct solution in your chosen style. A well-written functional Python solution is preferable to a poorly-structured class-based solution.

**Q18: Can I use standard library functions like sorted(), max(), min() in Python?**

Yes. Built-in functions and standard library modules (collections, heapq, math) are available and should be used. Writing manual sort implementations when sorted() works correctly is both unnecessary and error-prone under exam pressure.

**Q19: What should I do if I am not sure whether my approach is O(n) or O(n^2)?**

Count the loops. One loop through n elements = O(n). Two nested loops through n elements each = O(n^2). A loop that divides the problem in half each iteration = O(log n). If you are using a hash map for lookups inside a loop, the total is usually O(n) because hash map operations are O(1) average.

**Q20: How do I know if a problem requires DP vs. greedy vs. something else?**

DP indicators: "maximum/minimum," "number of ways," "can you achieve X," choices that depend on previous choices. Greedy indicators: making the locally optimal choice always produces globally optimal result (sorting + sequential processing). If neither applies clearly, try brute force + memoization and see if DP emerges.

**Q21: What is the best practice for reading input in competitive NQT coding?**

In Python, use `input()` for single values and `input().split()` for multiple values on a line. For arrays: `arr = list(map(int, input().split()))`. For multiple test cases: wrap in a `for _ in range(int(input())):` loop. Practice the input parsing for typical problem formats before the exam.

**Q22: How does TCS handle partial solutions that compile but produce wrong output?**

Partial solutions receive marks proportional to the test cases they pass. A solution that compiles and passes 6 of 10 test cases earns 60% of that problem's marks, regardless of whether the 4 failing tests failed due to logic errors, wrong output, or time limit exceeded.

**Q23: Is it better to use recursion or iteration for tree problems?**

Both work correctly for tree problems. Recursion is often cleaner and more readable for depth-first traversals (inorder, preorder, postorder, maximum depth). Iteration with an explicit stack is necessary for level-order traversal (BFS) and avoids Python's recursion limit for very deep trees. For NQT problems, recursion is fine unless the tree can be extremely deep.

**Q24: What is Python's default recursion limit and how do I change it?**

Python's default recursion limit is 1000. For deep recursion (very deep trees, large recursive DP), add at the top of your solution:
```python
import sys
sys.setrecursionlimit(10000)
```
This prevents RecursionError for input sizes that would exceed 1000 recursive calls.

**Q25: If I have never done competitive programming, can I still prepare well for NQT coding in 2-3 months?**

Yes. The NQT coding section does not require competitive programming experience - it tests fundamental algorithms and data structures at a level that 2-3 months of consistent practice from zero can build. Start with LeetCode Easy, work through the problem categories systematically, and use the [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html) for NQT-specific problem practice. Focus on understanding patterns rather than memorizing solutions.

---

## One Last Word: The Coding Section as Career Signal

TCS NQT's coding section is not just a hiring gate. It is a signal about how you will work in TCS's technology delivery environment - specifically whether you can write code that functions correctly, can be maintained by others, and handles the edge cases that real-world data produces.

TCS evaluates code quality not out of academic perfectionism but because the quality of code written in professional contexts - client-facing delivery, production deployments, code reviews - directly affects the outcome of the work.

The preparation for NQT coding, done well, develops exactly these professional coding qualities: correctness, clarity, efficiency, and edge case awareness. These qualities are not specific to the NQT - they are the qualities that TCS (and every other technology employer) values throughout a career.

Build these qualities deliberately. They compound across every project you contribute to, every code review you participate in, and every technical interview you take for the rest of your career.

The NQT coding section is the first measurement. Make it a strong one.

---

## The 30 Most Important Problems for NQT Coding Preparation

Based on frequency of appearance in NQT and TCS interview coding rounds, these 30 problems provide the most targeted preparation for the NQT coding section. Work through each in your chosen language, time yourself, and review the solution after your attempt.

### Tier 1: Must-Solve Easy Problems (Days 1-15)

**Problem 1: Two Sum**
Given an array and target, return indices of two elements summing to target.
*Pattern:* Hash map complement lookup. O(n) time.

**Problem 2: Reverse a String**
Reverse a string in-place using two-pointer or slicing.
*Pattern:* Two-pointer or `s[::-1]` in Python.

**Problem 3: Valid Palindrome**
Check if string is palindrome ignoring non-alphanumeric characters.
*Pattern:* Two-pointer after cleaning.

**Problem 4: Maximum Subarray**
Find the contiguous subarray with the largest sum.
*Pattern:* Kadane's algorithm. O(n).

**Problem 5: Climbing Stairs**
Count ways to reach the nth step taking 1 or 2 steps at a time.
*Pattern:* Fibonacci DP. O(n) time, O(1) space.

**Problem 6: Single Number**
Find the element that appears once in an array where all others appear twice.
*Pattern:* XOR all elements. O(n) time, O(1) space.

**Problem 7: Contains Duplicate**
Check if any element appears at least twice.
*Pattern:* Hash set. O(n).

**Problem 8: First Non-Repeating Character**
Find the first character in a string that does not repeat.
*Pattern:* Frequency count + linear scan. O(n).

**Problem 9: Reverse Linked List**
Reverse a linked list iteratively.
*Pattern:* Three-pointer (prev, current, next).

**Problem 10: Fibonacci Number**
Return the nth Fibonacci number.
*Pattern:* Iterative with two variables. O(n) time, O(1) space.

**Problem 11: Maximum Depth of Binary Tree**
Find the maximum depth of a binary tree.
*Pattern:* Recursive: 1 + max(left depth, right depth).

**Problem 12: Check if Two Strings are Anagrams**
Determine if two strings contain the same characters in any order.
*Pattern:* Sorted comparison or frequency count.

**Problem 13: Move Zeros**
Move all zeros in array to the end without changing relative order of non-zeros.
*Pattern:* Two-pointer or partition.

**Problem 14: Symmetric Tree**
Check if a binary tree is symmetric around its center.
*Pattern:* Recursive check of mirror subtrees.

**Problem 15: Missing Number**
Find the missing number in array containing n distinct numbers from 0 to n.
*Pattern:* Sum formula: n*(n+1)/2 - sum(arr).

### Tier 2: Must-Solve Medium Problems (Days 16-30)

**Problem 16: Longest Substring Without Repeating Characters**
Find the length of the longest substring with no character repeating.
*Pattern:* Sliding window with hash set. O(n).

**Problem 17: Search in Rotated Sorted Array**
Find a target in a sorted array that was rotated.
*Pattern:* Binary search with rotation detection. O(log n).

**Problem 18: 3Sum**
Find all unique triplets in array summing to zero.
*Pattern:* Sort + two-pointer for each fixed element. O(n^2).

**Problem 19: Container With Most Water**
Find two lines that form a container holding maximum water.
*Pattern:* Two-pointer moving toward center. O(n).

**Problem 20: Merge Intervals**
Merge all overlapping intervals.
*Pattern:* Sort by start, merge overlapping. O(n log n).

**Problem 21: Detect Cycle in Linked List**
Determine if a linked list has a cycle.
*Pattern:* Floyd's slow-fast pointer. O(n).

**Problem 22: Level Order Traversal of Binary Tree**
Return nodes level by level.
*Pattern:* BFS with queue, process one level per queue length. O(n).

**Problem 23: Number of Islands**
Count the number of islands in a 2D grid.
*Pattern:* DFS from each unvisited land cell, mark visited. O(mn).

**Problem 24: Coin Change**
Find minimum coins to make a given amount.
*Pattern:* Bottom-up DP. dp[amount] = min(dp[amount-coin] + 1). O(amount * coins).

**Problem 25: Longest Common Subsequence**
Find the length of the longest common subsequence of two strings.
*Pattern:* 2D DP table. O(mn).

**Problem 26: Product of Array Except Self**
Return array where each element is the product of all other elements.
*Pattern:* Prefix and suffix products. O(n) time, O(1) extra space.

**Problem 27: Find All Anagrams in a String**
Return starting indices of all anagrams of pattern in string.
*Pattern:* Sliding window with frequency counter comparison. O(n).

**Problem 28: Decode Ways**
Count ways to decode a string of digits (1-26 = A-Z).
*Pattern:* DP with one and two digit decoding. O(n).

**Problem 29: Group Anagrams**
Group strings that are anagrams of each other.
*Pattern:* Hash map with sorted string as key. O(nm log m).

**Problem 30: Maximum Product Subarray**
Find the contiguous subarray with the largest product.
*Pattern:* Track both max and min (negative * negative = positive). O(n).

---

## The Progression Framework: From Zero to NQT-Ready

For candidates starting coding preparation from the beginning, here is the progression framework that builds NQT readiness in 12 weeks:

**Weeks 1-3: Language and fundamentals**
Goal: fluent basic coding in chosen language
Practice: Tier 1 problems 1-5, focusing on correctness not speed
Daily: 1 new problem + review of previous day's problem

**Weeks 4-6: Easy problem competency**
Goal: solve Easy problems in under 20 minutes
Practice: Tier 1 problems 6-15, all at under 20-minute target
Daily: 1 timed problem + error review

**Weeks 7-9: Medium problem introduction**
Goal: understand Medium problem patterns, achieve 50%+ test case passage
Practice: Tier 2 problems 16-22 with understanding focus
Daily: 1 Medium problem with solution review, 1 Easy problem timed

**Weeks 10-12: Full exam simulation**
Goal: Easy in 15 min, Medium 65%+ passage in 30 min
Practice: 3× timed mock sessions per week (45 min, Easy + Medium)
Daily: 1 LeetCode problem + mock session on alternating days

At the end of week 12, candidates following this progression consistently achieve the coding performance associated with NQT Ninja qualification, with strong candidates reaching Digital track coding competency.

The [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html) provides the supplementary practice problems, timed mock tests, and structured preparation that supports this 12-week framework.

Code consistently. Improve progressively. Show up ready to write code that works.

---

## Coding Under Exam Pressure: Psychological Preparation

### Managing the Clock Without Panic

The most common performance degradation in the NQT coding section is not lack of knowledge - it is anxiety about the ticking clock causing errors in code the candidate actually knows how to write.

The psychological antidote is accumulated exam experience. Each timed mock coding session builds tolerance for the clock. By the tenth timed session, the timer is a known quantity rather than an anxiety trigger. The brain has processed and normalized the experience of working under time constraint.

Candidates who take their first timed coding session on NQT day are experiencing the time pressure for the first time under high stakes. Candidates who have done twenty timed sessions have normalized the experience. The preparation difference shows directly in code quality.

**The mental reset technique:** If you get stuck on a problem and feel anxiety rising, take 10 seconds to breathe and re-read the problem statement from the beginning. Anxiety causes tunnel vision - re-reading the problem from scratch often reveals a clarification or approach that panic had obscured.

**The partial solution mindset:** Always prefer a submitted partial solution over a perfect solution under construction. If your algorithm is implemented for the main case but missing one edge case, submit it before debugging the edge case. The marks from passing test cases accumulate even as you continue working.

### The Two-Problem Confidence Split

Before starting the exam, calibrate your confidence by category:

"I am confident in Easy problems involving arrays/strings" - these will be straightforward.
"I am less confident in DP Medium problems" - flag these as requiring extra time and careful thinking.

This calibration helps with time allocation decisions. If the Medium problem falls in your confident category, you can invest more time on it knowing the return is likely high. If it falls outside your confident category, consider whether spending 10 minutes on a brute-force partial solution and moving time toward cleaning up the Easy solution produces better expected marks.

---

## Language Comparison Table: Making the Final Choice

For candidates who are still deciding which language to use for NQT:

| Factor | Python | Java | C++ | C |
|--------|--------|------|-----|---|
| Code volume for same logic | Least | Moderate | Moderate | Most |
| Standard library data structures | Excellent (built-in dict, set, list, deque) | Good (Collections framework) | Excellent (STL) | Limited |
| Error messages when debugging | Clear Python exceptions | Clear JVM exceptions | Sometimes cryptic | Often silent/crashes |
| Execution speed | Slowest | Moderate | Fastest (near C) | Fastest |
| Most candidates' familiarity | Growing | Highest in engineering | High in CS/IT | High in ECE |
| Recommended for | Everyone if not strongly preferred elsewhere | Java-fluent candidates | CS candidates with STL knowledge | Only if deeply fluent |

**The final recommendation:** If you have approximately equal fluency in Python and Java, choose Python. The code you write will be shorter, the data structures you need will be available without imports, and debugging will produce clearer error messages. The slight speed disadvantage almost never matters for NQT problem sizes.

If you are significantly more fluent in Java than Python, stay with Java - fluency matters more than language choice.

If you know C++ STL well from competitive programming, C++ is excellent.

---

## The Connection Between Coding Practice and Career Success

The investment in NQT coding preparation does not end at the NQT. The skills built - algorithmic thinking, data structure selection, efficient implementation, edge case awareness - compound across the entire career.

**In TCS ILP:** ILP technical assessments include programming problems. The coding skills built for NQT apply directly to ILP assessment performance.

**In TCS projects:** The ability to write efficient, clean, correct code is the foundation of every technical contribution in TCS delivery. Project code that is well-structured and handles edge cases reduces debugging time, reduces production incidents, and creates positive impressions with team leads and clients.

**In future career moves:** Technical interviews at any technology employer - product companies, startups, other IT services firms - all involve coding assessments at similar or higher difficulty than TCS NQT. The preparation done for NQT is the foundation that makes future technical interviews approachable.

The investment in genuine coding skill development is not a preparation investment - it is a career investment that pays forward for decades. The NQT is simply the first return on that investment.

Prepare well. Build genuinely. Let the skill compound.

The exam is one moment in a career that will use every hour of this preparation. Make the preparation real, make it deep, and make it the foundation that everything else builds on.

---

## Complete Code Templates by Problem Type

Having ready-to-use code templates for the most common NQT coding problem types reduces implementation time during the exam. Practice these templates until they are automatic.

### Template 1: Array Two-Pointer (Sorted)
```python
def two_pointer_sorted(arr, target):
    left, right = 0, len(arr) - 1
    while left < right:
        current = arr[left] + arr[right]
        if current == target:
            # found solution
            return [left, right]
        elif current < target:
            left += 1
        else:
            right -= 1
    return []  # not found
```

### Template 2: Sliding Window (Variable Size)
```python
def sliding_window_variable(s, condition_param):
    left = 0
    window_state = {}  # or counter
    best = 0
    for right in range(len(s)):
        # Add s[right] to window state
        window_state[s[right]] = window_state.get(s[right], 0) + 1
        
        # Shrink window while condition violated
        while len(window_state) > condition_param:  # example condition
            old = s[left]
            window_state[old] -= 1
            if window_state[old] == 0:
                del window_state[old]
            left += 1
        
        best = max(best, right - left + 1)
    return best
```

### Template 3: BFS (Level Order / Shortest Path)
```python
from collections import deque

def bfs(root_or_start):
    queue = deque([root_or_start])
    visited = {root_or_start}
    distance = 0
    
    while queue:
        level_size = len(queue)
        for _ in range(level_size):
            node = queue.popleft()
            # process node
            for neighbor in get_neighbors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        distance += 1
    return distance
```

### Template 4: DFS with Backtracking
```python
def backtrack_template(candidates, target):
    result = []
    
    def backtrack(start, current, remaining):
        if remaining == 0:
            result.append(current[:])
            return
        if remaining < 0:
            return
        for i in range(start, len(candidates)):
            current.append(candidates[i])
            backtrack(i + 1, current, remaining - candidates[i])
            current.pop()
    
    backtrack(0, [], target)
    return result
```

### Template 5: 1D Dynamic Programming
```python
def dp_1d(n):
    dp = [0] * (n + 1)
    dp[0] = base_case_0
    dp[1] = base_case_1  # if applicable
    
    for i in range(2, n + 1):
        dp[i] = some_combination_of(dp[i-1], dp[i-2])  # or other recurrence
    
    return dp[n]
```

### Template 6: 2D Dynamic Programming
```python
def dp_2d(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]
```

### Template 7: Tree DFS (Recursive)
```python
def tree_dfs(root):
    if not root:
        return base_case_value  # 0, None, [], etc.
    
    left_result = tree_dfs(root.left)
    right_result = tree_dfs(root.right)
    
    return combine(root.val, left_result, right_result)
```

### Template 8: Linked List Two-Pointer
```python
def linked_list_slow_fast(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next          # moves 1 step
        fast = fast.next.next     # moves 2 steps
    # slow is now at the middle
    return slow
```

These eight templates cover the most common NQT coding problem patterns. Knowing these by heart means that when a problem maps to one of these patterns, the implementation portion of the problem requires only adapting the template rather than designing from scratch - saving the mental energy for the pattern recognition itself.

Practice each template until you can write it from memory in under two minutes. That fluency is the concrete form of the "coding readiness" that this entire guide has been building toward.

The preparation is in your hands. The exam is coming. The skill is yours to build.

Build it.

---

## The Coding Section in the Broader NQT Context

### How Coding Performance Interacts with Other Sections

The NQT is a holistic assessment where each section contributes to the final outcome. Understanding how coding performance interacts with other section performance helps prioritize the preparation investment.

**For Ninja track (standard entry):**
Strong aptitude and reasoning scores with partial Easy problem completion (passing 5+ test cases) typically suffices for Ninja qualification. Candidates who are strongest in aptitude and reasoning but weaker in coding should ensure their coding baseline is above the partial-pass threshold rather than investing all remaining preparation in perfecting their coding skills.

**For Digital track (premium entry):**
Coding performance has outsized weight. Candidates who complete Easy fully and pass 60%+ of Medium test cases combined with strong aptitude scores have the best Digital qualification probability. For Digital-aspiring candidates, coding is the highest-ROI preparation investment in the final weeks before the exam.

**The cross-section trade-off:** A candidate with 80th percentile aptitude and 60th percentile coding will likely qualify for Ninja. The same candidate investing 20 more hours in coding to reach 75th percentile coding, at the cost of slight aptitude regression to 75th percentile, may produce a better overall Digital qualification outcome. The math depends on the specific section weights TCS applies - but the general principle holds: for Digital consideration, coding strength is weighted heavily enough that it is the correct focus for the final preparation phase.

### When to Finalize Your Language Choice

The language choice for the NQT coding section should be finalized at least four weeks before the exam. At this point:

Your practice has been in one primary language. Continuing in that language through the final four weeks builds the fluency and speed that the timed exam rewards.

Switching languages with four weeks to go requires rebuilding fluency in a new syntax under increasing time pressure. Unless there is a compelling reason to switch (discovering a fundamental limitation in your current language choice), stay with the language you know best.

**The one exception:** If you have been practicing in Java but discover that writing Java under the exam's time pressure is significantly slower than Python would be, and you have more than four weeks remaining, switching to Python may be worthwhile. The syntax learning for Python is fast for Java programmers; the key investment is rebuilding fluency in Python's standard library.

### Post-NQT Coding Preparation: The Interview Coding Component

The TCS technical interview for both Ninja and Digital tracks may include a coding component - writing code on paper, pseudocode on a shared screen, or a brief online coding problem. The preparation done for NQT coding applies directly to this interview coding component.

The additional preparation for interview coding that goes beyond NQT preparation:

Explaining your code out loud. The interview coding component requires narrating your approach while implementing. Practice writing code and explaining simultaneously: "I am using a hash map here to store the complement of each number as I scan, so when I encounter the complement of a previous number, I know we have found the pair."

Handling follow-up questions about complexity. "What is the time complexity of your solution?" is a standard follow-up. Know the answer for every approach you implement: two-pointer is O(n), sliding window is O(n), binary search is O(log n), nested loops are O(n^2).

Discussing alternatives. "Can you make this more space-efficient?" or "What if the input is sorted, does your approach change?" are follow-ups that test understanding beyond the implemented solution. The preparation done for NQT coding provides the algorithm knowledge to answer these questions.

The NQT coding preparation thus serves double duty: it is both the direct preparation for the NQT's coding section and the foundation for the technical interview's coding component. The investment compounds across both selection stages.

Build the coding competency genuinely. Practice consistently. Understand the patterns deeply. The returns are immediate (NQT performance) and long-term (interview performance, career contribution).

That is the complete NQT coding preparation framework. Everything needed to go from current ability to NQT-ready coding competency is in these pages. The path is clear. The practice is yours to do.

Start today. Keep going. Show up ready.

---

## Ten Things Every NQT Coding Candidate Should Know

A concise summary of the most important insights from this guide:

**1. The coding section tests two problems - Easy and Medium.** Always complete Easy before attempting Medium. A complete Easy plus a partial Medium scores higher than a perfect Easy and no Medium attempt.

**2. Five languages are permitted: C, C++, Java, Python, Perl.** Use the language you are most fluent in. For most candidates without a strong existing preference, Python is recommended for its concise syntax and built-in data structures.

**3. Scoring is test-case based.** Partial solutions score partial marks. Always submit something rather than leaving a problem unattempted. A solution passing 6 of 10 test cases earns 60% of that problem's marks.

**4. Edge cases determine test case passage rates.** Solutions that are logically correct for the average case but incorrect for empty inputs, single elements, or boundary values consistently fail multiple test cases. Handle edge cases explicitly.

**5. Code quality is evaluated alongside correctness.** Meaningful variable names, clean function structure, and brief comments for non-obvious logic all contribute to the assessment. Write code as you would for a code review, not just for passing tests.

**6. Arrays and strings are the most frequently tested categories.** Hash maps, two-pointer, and sliding window solve most array and string problems efficiently. These three patterns alone cover a majority of Easy and many Medium problems.

**7. DP problems become manageable with pattern recognition.** Fibonacci variants, climbing stairs, coin change, longest common subsequence, and knapsack are the canonical DP patterns. Recognizing which pattern a new problem maps to is the key skill.

**8. The preparation window before NQT is short after announcement.** Announcements come with 2-4 weeks notice. Begin preparation months before the expected window, not after the announcement.

**9. LeetCode Easy and Medium calibrate directly to NQT difficulty.** Practice with LeetCode Easy for the first month, transition to Medium. The NQT Preparation Guide at ReportMedic provides NQT-specific practice on top of this foundation.

**10. Each hour of coding practice compounds.** The 30 problems in this guide, practiced genuinely with timed attempts and solution review, are worth more than 300 problems practiced casually without timing or review. Quality of practice matters more than quantity.

Apply these ten points. Practice consistently. Show up at the NQT ready to code - confidently, correctly, and efficiently.

The coding section is yours to conquer. Go conquer it.
