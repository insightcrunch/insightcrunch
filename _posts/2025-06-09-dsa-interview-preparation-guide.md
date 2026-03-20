---
layout: post
title: "Complete DSA Interview Preparation Guide: Topic-Wise Strategy, 150 Must-Solve Problems, Patterns & Revision Plan for Cracking Product-Based Company Interviews"
date: 2025-06-09
categories: ["Industry"]
tags: ["DSA interview questions", "DSA preparation", "LeetCode patterns", "coding interview", "data structures and algorithms", "product based company interview", "FAANG interview prep", "competitive programming", "system design", "coding interview patterns"]
excerpt: "The most complete DSA interview preparation guide for software engineers: topic-wise strategy, 150 curated must-solve problems, pattern recognition techniques, a structured revision plan, and everything you need to crack coding interviews at product-based companies."
image: "/assets/images/blog/blog-15.webp"
reading_time: 55
author: "Insight Crunch Team"
---

## Table of Contents

- [How Product-Based Company Interviews Actually Work](#how-interviews-work)
- [The DSA Preparation Roadmap: What to Study, In What Order](#preparation-roadmap)
- [Arrays and Strings: The Foundation of Every Interview](#arrays-strings)
- [Hashing and Hash Maps: O(1) Thinking](#hashing)
- [Two Pointers and Sliding Window: The Efficiency Patterns](#two-pointers-sliding-window)
- [Recursion and Backtracking: Thinking in Trees](#recursion-backtracking)
- [Stacks and Queues: Ordered Memory Structures](#stacks-queues)
- [Linked Lists: Pointer Mastery](#linked-lists)
- [Binary Search: Beyond Sorted Arrays](#binary-search)
- [Trees and Binary Search Trees: Hierarchical Problem Solving](#trees-bst)
- [Graphs: BFS, DFS, and the Algorithms That Connect Everything](#graphs)
- [Dynamic Programming: The Pattern-First Approach](#dynamic-programming)
- [Heaps and Priority Queues: When Order Matters](#heaps)
- [The 150 Must-Solve Problems: Curated Topic-Wise List](#must-solve-problems)
- [Pattern Recognition: The Meta-Skill That Accelerates Preparation](#pattern-recognition)
- [The 12-Week Structured Revision Plan](#revision-plan)
- [Mock Interviews and the Communication Framework](#mock-interviews)
- [Frequently Asked Questions](#faq)

---

## How Product-Based Company Interviews Actually Work {#how-interviews-work}

Before diving into preparation strategy, it is essential to understand what product-based companies are actually evaluating in a coding interview. The interview is not primarily a test of memorised solutions. It is a test of how you think, how you communicate under pressure, and how systematically you approach an unfamiliar problem.

A typical product-based company interview process consists of several rounds. An online assessment (OA) typically precedes on-site or virtual rounds and involves 2-3 coding problems to be solved within 60-90 minutes on a platform like HackerRank, HackerEarth, or CodeSignal. Performance in the OA determines whether you proceed to further rounds. Phone/video screening rounds involve 1-2 coding problems solved live with a recruiter or engineer, usually 45-60 minutes. On-site or virtual interview loops at top-tier companies (sometimes called FAANG-level or product-based companies) typically involve 4-6 rounds: 2-4 coding rounds, 1 system design round (for experienced engineers), and 1-2 behavioural rounds.

![Complete DSA Interview Preparation Guide: Topic-Wise Strategy, 150 Must-Solve Problems, Patterns & Revision Plan for Cracking Product-Based Company Interviews](/assets/images/blog/blog-15.webp)
Complete DSA Interview Preparation Guide — Topic-Wise Strategy, 150 Must-Solve Problems, Patterns and Revision Plan

### What Interviewers Are Actually Scoring

Most major tech companies use a structured scoring rubric across four dimensions:

**Problem Solving:** Did you understand the problem correctly? Did you ask clarifying questions? Did you identify the right approach? Did you handle edge cases? Did you arrive at an optimal or near-optimal solution?

**Coding:** Is your code clean, readable, and correct? Do you use meaningful variable names? Do you naturally write modular code? Do you catch bugs quickly?

**Communication:** Do you think aloud throughout the problem? Do you explain your reasoning before coding? Do you discuss time and space complexity?

**Culture/Collaboration:** Do you respond well to hints? Can you incorporate feedback mid-problem? Are you pleasant to work with under pressure?

Many candidates fail despite solving the problem correctly because they solved it silently, never explained their reasoning, never discussed alternatives, and left the interviewer with no insight into their thought process. Understanding that the interview is a collaborative performance - not a silent exam - is the most important mindset shift in interview preparation.

### The Difficulty Distribution at Top Companies

Contrary to what many preparation resources suggest, the majority of coding interview problems at top product-based companies are medium difficulty. A realistic difficulty distribution based on historical interview reports is approximately: Easy 15%, Medium 60-65%, Hard 20-25%. This means that solving LeetCode Hard problems at high volume is less important than thoroughly understanding and confidently executing medium-difficulty problems across all major topic areas. Candidates who can solve all common medium-difficulty patterns fluently perform better than candidates who have memorised hard problem solutions but stumble on fundamental medium problems under pressure.

---

## The DSA Preparation Roadmap: What to Study, In What Order {#preparation-roadmap}

The order of study matters significantly. Some topics are foundational prerequisites for others; starting with graphs before mastering arrays is a common error that leads to confusion and wasted time. The following roadmap sequences topics in the order that maximises learning efficiency.

### Phase 1: Core Linear Structures (Weeks 1-3)

Arrays and Strings → Hashing → Two Pointers → Sliding Window → Stacks → Queues → Linked Lists

These topics form the bedrock of all DSA interviews. Most candidates already have familiarity with these from their undergraduate coursework; the interview preparation goal is to deeply understand the patterns (not just individual problems) that appear across this family.

### Phase 2: Non-Linear Structures and Search (Weeks 4-6)

Recursion and Backtracking → Binary Search → Trees → Binary Search Trees → Heaps

Recursion must be mastered before trees, since most tree algorithms are recursive. Binary search must be mastered before heaps, since the heap's conceptual basis requires comfort with ordering and comparison. This phase contains the highest density of interview-critical topics per unit of study time.

### Phase 3: Graphs and Dynamic Programming (Weeks 7-10)

Graphs (BFS, DFS, shortest path, topological sort) → Dynamic Programming (memoisation, tabulation, common DP patterns)

These two topics are the most frequently studied and the most frequently stumbled over in preparation. Both require a significant time investment; rushing through them to move on to practice problems is the most common preparation mistake.

### Phase 4: Advanced Topics and System Design (Weeks 11-12)

Tries, Segment Trees, Union-Find → System Design fundamentals → Mock interviews and contest practice

Advanced data structures appear infrequently in interviews but do appear at senior levels and at the most selective companies. System design, critical for candidates with 3+ years of experience, is prepared separately from DSA but belongs in this final phase.

### Language Choice

For DSA interviews, Python and Java are the most popular choices among Indian candidates. C++ is preferred in competitive programming circles and is fully acceptable. JavaScript is acceptable but less commonly used. The choice of language is less important than depth of knowledge of your chosen language's standard library, since using built-in data structures and sorting algorithms fluently is faster and less error-prone during interviews.

Key standard library features to master in your chosen language: sorting (and comparator functions for custom sort), collections (deque, priority queue / heap, sorted set / TreeMap, hash map), string manipulation methods, and list operations. Spending time knowing your language's standard library deeply will save you significant interview minutes.

---

## Arrays and Strings: The Foundation of Every Interview {#arrays-strings}

Arrays are the most fundamental data structure and appear in some form in virtually every coding interview. The key insight about array problems is that they rarely require unusual data structures or complex algorithms - they require pattern recognition and the willingness to think about traversal strategies systematically.

### Core Array Concepts and Interview Patterns

**Prefix Sum:** A prefix sum array stores the cumulative sum of elements up to each index. It enables O(1) range sum queries (what is the sum of elements from index i to j?) after O(n) preprocessing. Prefix sum is the foundation for subarray sum problems, range query problems, and many 2D matrix problems. The pattern appears constantly: recognise it whenever a problem asks about cumulative properties over a contiguous range.

**Kadane's Algorithm:** The classic algorithm for finding the maximum sum contiguous subarray in O(n) time and O(1) space. The pattern extends naturally to maximum product subarray and many similar problems. Understand the algorithm conceptually (maintain a running sum, reset to current element if the running sum becomes negative) rather than memorising the code.

**Two-Pass and Multiple Pass Patterns:** Many array problems that seem to require nested loops can be solved in two passes (one forward, one backward) or by precomputing from the left and from the right independently and combining. Problems on the "best time to buy and sell stock" family use exactly this pattern.

**In-Place Modification:** Problems that ask you to modify an array in-place (remove duplicates, move zeros, rotate array) test your ability to use swaps, two-pointer manipulation, and reversal techniques. These are mechanical but important.

**Sorting as a Preprocessing Step:** Many array problems become significantly simpler after sorting. If the problem asks about pairs, triplets, or groups with a specific sum or property, sorting typically enables a two-pointer or binary search approach that replaces a brute-force O(n²) or O(n³) solution.

### String-Specific Patterns

Strings in most languages are immutable (Java, Python), which means string concatenation inside a loop is O(n²). Always use a StringBuilder (Java) or list join (Python) when building strings iteratively.

**Sliding window on strings:** Problems asking for the smallest window containing all characters, the longest substring without repeating characters, or similar "window" problems have a canonical sliding window solution. Understand the expand-right / contract-left framework thoroughly.

**Character frequency maps:** Many string problems reduce to frequency counting with a hash map. Anagram detection, grouping anagrams, and character rearrangement problems all use this pattern.

**Pattern matching:** While KMP and Rabin-Karp string matching algorithms appear occasionally, the more interview-relevant skill is recognising when a problem is fundamentally about checking character frequency or order, and distinguishing those from problems that genuinely require subsequence or substring matching logic.

---

## Hashing and Hash Maps: O(1) Thinking {#hashing}

Hash maps (dictionaries in Python, HashMap in Java) are the single most commonly used data structure in coding interview solutions. They enable O(1) average-case lookup, insertion, and deletion, transforming O(n²) brute-force solutions into O(n) solutions in a wide range of problems.

### When to Reach for a Hash Map

The signal to use a hash map is the phrase "find a pair / group / element that satisfies a condition." Any time you need to check "have I seen this before?" or "is there a complementary element in the array?", a hash map is the tool.

**Two Sum pattern:** The archetypal hash map problem. For each element, check if its complement (target - element) exists in the map. This O(n) approach replaces the O(n²) brute force and is the template for dozens of interview problems: subarray sum equals k (using prefix sum + hash map), longest subarray with equal number of 0s and 1s, four sum, and more.

**Frequency counting:** Count the frequency of elements in a hash map, then process the frequency map. This pattern underlies finding the first non-repeating character, finding the majority element, grouping anagrams, and top-k frequent elements.

**Hash Set for O(1) existence checks:** When you only need to know whether an element exists (not its count or value), a hash set is more space-efficient and equally fast. The classic use is in cycle detection in arrays (tortoise and hare uses O(1) space; hash set approach uses O(n) space but is more readable) and in the "contains duplicate" family of problems.

### Hash Map Implementation Awareness

Understanding how hash maps work internally (hash function, collision handling via chaining or open addressing, load factor and rehashing) is occasionally tested directly and always useful for discussing time complexity accurately. The O(1) average-case claim assumes a good hash function and a load factor below the rehashing threshold; in the worst case (many collisions), hash map operations degrade to O(n).

---

## Two Pointers and Sliding Window: The Efficiency Patterns {#two-pointers-sliding-window}

Two pointers and sliding window are algorithm patterns rather than data structures, and they are among the highest-leverage patterns to master for interviews. Both convert O(n²) or O(n³) brute-force solutions into O(n) solutions for a specific class of problems.

### Two Pointers: When and How

The two-pointer pattern applies when:
- The input is sorted (or can be sorted without losing information)
- You are looking for pairs, triplets, or a contiguous segment satisfying a condition
- You are partitioning an array in-place

**Same-direction two pointers (fast and slow):** Used in cycle detection (Floyd's algorithm), finding the middle of a linked list, and removing duplicates from a sorted array. The slow pointer marks the boundary of the "valid" processed region; the fast pointer scans ahead.

**Opposite-direction two pointers:** Used when the array is sorted and you need pairs summing to a target, or when checking if a string is a palindrome. One pointer starts at the left, the other at the right; they move toward each other based on comparison logic.

**Three-pointer extension:** The 3Sum problem is the canonical example: fix one element, then use opposite-direction two pointers on the remainder. This converts O(n³) brute force to O(n²), which is optimal for 3Sum.

### Sliding Window: Fixed vs Variable Size

The sliding window pattern maintains a contiguous window (subarray or substring) and moves it across the input, updating the window's property incrementally rather than recomputing it from scratch.

**Fixed-size window:** Problems asking for the maximum/minimum sum or average of a subarray of size k. Maintain a running sum, subtract the leftmost element and add the new rightmost element as the window slides. O(n) versus O(n*k) brute force.

**Variable-size window:** Problems asking for the smallest window satisfying a condition (e.g., contains all characters, sum equals k, no repeating characters). Expand the right boundary to satisfy the condition, then contract the left boundary to minimise the window size. The key invariant is maintaining the window's validity as a property tracked with a counter or hash map.

The sliding window pattern is the correct first instinct for: longest substring without repeating characters, minimum window substring, maximum consecutive ones, permutation in string, and fruit into baskets - a family of problems that all reduce to the same variable-window framework.

---

## Recursion and Backtracking: Thinking in Trees {#recursion-backtracking}

Recursion is the most important conceptual prerequisite for tree and graph algorithms, and backtracking is the recursive exploration pattern that underlies a significant portion of hard interview problems. Many candidates who struggle with trees and graphs are actually struggling with recursion; investing deeply in this topic pays dividends across multiple later subjects.

### The Three Laws of Recursion

Every recursive function must have:
1. A base case that terminates the recursion
2. A recursive case that makes progress toward the base case
3. Trust - you must trust that the recursive call correctly solves the smaller subproblem

The third point is where most beginners break down. They try to mentally trace through multiple levels of recursion and lose track. The correct mental model is: assume your recursive function works correctly for smaller inputs, then figure out how to express the solution to the current input in terms of the smaller solution.

### Visualising Recursion as a Tree

Every recursive function call creates a tree of subcalls. Visualising this tree explicitly - drawing it on paper during problem-solving - is the most reliable technique for understanding recursive problems and for deriving their time complexity.

For a recursive call that branches into two calls of size n/2 (like merge sort), the tree has log n levels and 2^(log n) = n nodes. The total work is O(n log n). For a recursive call that branches into two calls of size n-1 (a naive Fibonacci), the tree has exponential nodes, which is why memoisation is required.

### Backtracking: Systematic Exploration with Pruning

Backtracking is a recursive algorithm that incrementally builds a candidate solution and abandons it ("backtracks") as soon as it determines the candidate cannot lead to a valid solution. It is the algorithmic foundation of constraint satisfaction problems.

The canonical backtracking template:

```python
def backtrack(candidate, state):
    if is_solution(candidate):
        record_solution(candidate)
        return
    
    for choice in get_choices(state):
        if is_valid(choice, candidate):
            make_choice(choice, candidate, state)
            backtrack(candidate, state)
            undo_choice(choice, candidate, state)  # backtrack
```

This template generates: all subsets, all permutations, all combinations summing to a target, N-Queens solutions, Sudoku solutions, word search in a grid, and more. Recognising that a problem asks you to "find all" or "generate all valid" configurations is the signal to apply backtracking.

**Pruning:** The efficiency of backtracking comes from pruning - cutting off branches of the exploration tree that cannot lead to valid solutions. In the combination sum problem, sorting the candidates and stopping when the current element exceeds the remaining target prunes large portions of the exploration tree.

---

## Stacks and Queues: Ordered Memory Structures {#stacks-queues}

Stacks (LIFO - Last In, First Out) and queues (FIFO - First In, First Out) are essential data structures that appear both directly as interview topics and as implementation tools inside other algorithms.

### Stack Patterns

**Matching and balancing:** Stacks are the natural tool for matching open-close pairs: valid parentheses, valid bracket sequences, decode string. Push opening elements; when a closing element is encountered, check that the top of the stack matches.

**Monotonic stack:** A monotonic stack maintains elements in a specific order (increasing or decreasing) by popping elements that violate the order before pushing a new element. It enables O(n) solutions to problems that would otherwise require O(n²): next greater element, daily temperatures, largest rectangle in histogram, trapping rain water. Recognise the monotonic stack pattern whenever a problem asks "for each element, find the nearest element to the left/right that is greater/smaller."

**Expression evaluation:** Stack-based expression evaluation (infix to postfix conversion, evaluating a postfix expression, calculator problems) is a classic interview topic that tests both stack mechanics and careful handling of operator precedence.

### Queue Patterns

**BFS (Breadth-First Search):** Queues are the implementation structure for BFS. Every level-order tree traversal and every shortest-path computation in an unweighted graph uses a queue. Covered in detail in the graphs and trees sections.

**Sliding window maximum:** The deque (double-ended queue) enables O(n) computation of the maximum (or minimum) in every sliding window of size k. The pattern: maintain a deque of indices in decreasing order of value. For each new element, remove indices from the back that are smaller (since they can never be the maximum going forward) and remove the front index if it is outside the current window.

**Design problems:** Designing a stack with O(1) minimum, a queue using two stacks, or a circular buffer are design-oriented problems that test deep understanding of these structures.

---

## Linked Lists: Pointer Mastery {#linked-lists}

Linked lists appear frequently in interviews not because they are the most important data structure in practice, but because problems on them require clean, careful pointer manipulation under pressure - which tests code quality directly.

### Core Linked List Techniques

**Two-pointer (fast and slow):** The most important linked list technique. Applications:
- Finding the middle of a linked list (fast moves 2 steps, slow moves 1; when fast reaches end, slow is at the middle)
- Detecting a cycle (Floyd's tortoise and hare algorithm)
- Finding the start of a cycle
- Finding the nth node from the end (fast starts n steps ahead; when fast reaches end, slow is at the target)

**Reversal:** Reversing a linked list (or a portion of it) is a fundamental operation that appears directly and as a subroutine in more complex problems (reverse nodes in k-group, palindrome linked list, reorder list). Master the iterative three-pointer reversal approach (prev, curr, next) before the recursive version.

**Merge and sort:** Merging two sorted linked lists (the core operation of merge sort on lists) is a canonical problem. The merge sort on a linked list uses the find-middle technique followed by recursive sorting and merging, all in O(n log n) time without requiring extra space.

**Dummy node technique:** Many linked list problems become cleaner when you introduce a dummy (sentinel) node at the head of the list. This eliminates special cases for operations on the head node. Always consider whether a dummy node simplifies the pointer manipulation before writing code.

### Common Pitfalls

Off-by-one errors are endemic in linked list code. The discipline of drawing the list state on paper (or in comments) before and after each pointer operation, then verifying against the code, prevents the majority of these errors. Never submit linked list code in an interview without mentally tracing through a small example.

Null pointer errors are the other common failure mode. Always check whether a pointer is null before accessing `.next` or `.val`.

---

## Binary Search: Beyond Sorted Arrays {#binary-search}

Binary search is one of the most widely misunderstood interview topics. Most candidates know the basic sorted array binary search; far fewer recognise the breadth of problems that reduce to binary search on a search space that is not literally a sorted array.

### The Binary Search Template

The standard binary search template eliminates off-by-one errors and handles both "find exact match" and "find first/last occurrence" variants:

```python
def binary_search(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = left + (right - left) // 2  # avoids integer overflow
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
```

The `left + (right - left) // 2` formulation for mid is standard - it is numerically equivalent to `(left + right) // 2` but avoids integer overflow in languages with fixed-size integers (Java, C++). Use it habitually.

### Binary Search on the Answer Space

The most powerful application of binary search, and the one that most separates interview-prepared candidates from unprepared ones, is binary search on an abstract search space - typically a range of possible answer values.

The pattern: when a problem asks "find the minimum/maximum value X such that condition C(X) is satisfied," and C(X) is monotonic (if X satisfies C then X+1 also satisfies C, or vice versa), binary search the answer space. Examples:

- Koko eating bananas: binary search on eating speed; for each speed, check if all bananas can be eaten within the time limit.
- Minimum capacity to ship packages within D days: binary search on ship capacity.
- Find the minimum number of days to make M bouquets: binary search on the answer (number of days).
- Split array largest sum: binary search on the maximum subarray sum.

Recognising the "binary search on answer" pattern requires understanding that the problem has a monotonic feasibility function. Practise with 5-10 problems in this category until the pattern click is automatic.

### Binary Search Variants

**First true / last false:** Modified binary search for finding the first position where a condition becomes true in a sorted boolean array. This variant underlies many "find first occurrence" and "left boundary" problems.

**Rotated sorted array search:** A classic problem where the array is sorted but rotated at an unknown pivot. The key insight is that at least one of the two halves [left, mid] or [mid, right] is always sorted; identify which half is sorted and determine whether the target is in that half.

**Search in 2D matrix:** Treating a matrix as a flattened sorted array (if rows are sorted and the first element of each row is greater than the last element of the previous row) enables standard binary search with index-to-coordinate conversion.

---

## Trees and Binary Search Trees: Hierarchical Problem Solving {#trees-bst}

Trees are the most important topic for coding interviews after arrays and strings, both in terms of frequency and in terms of the conceptual depth required. Mastering tree traversals, the recursive tree decomposition pattern, and BST properties is non-negotiable.

### The Four Tree Traversals

**Inorder (Left - Root - Right):** Visits BST nodes in ascending sorted order. Used whenever a problem requires processing BST nodes in sorted sequence.

**Preorder (Root - Left - Right):** Visits the root before its subtrees. Used for tree serialisation and for problems that require the root's value to be processed before its children (e.g., constructing a tree from traversal).

**Postorder (Left - Right - Root):** Visits the root after its subtrees. Used when a node's result depends on the results of its subtrees (bottom-up computation): tree height, tree diameter, balanced tree check.

**Level-order (BFS):** Visits nodes level by level using a queue. Used for level-by-level processing: right side view, maximum width of binary tree, connect next right pointers.

### The Recursive Tree Pattern

Almost every tree problem follows the same recursive skeleton: at each node, compute a value that depends on the values computed for the left and right subtrees. This is the postorder pattern in disguise.

```python
def solve(root):
    if root is None:
        return base_case_value
    
    left_result = solve(root.left)
    right_result = solve(root.right)
    
    return combine(root.val, left_result, right_result)
```

The maximum depth, minimum depth, diameter, path sum, symmetric tree check, and balanced tree check all reduce to this skeleton. Recognising this allows you to derive solutions quickly rather than reasoning from scratch.

### BST Properties and Operations

A Binary Search Tree satisfies the invariant: for every node, all values in the left subtree are less than the node's value, and all values in the right subtree are greater.

Key BST operations:
- **Search:** O(h) where h is the height. O(log n) for balanced BST, O(n) worst case for skewed tree.
- **Insert:** O(h) - find the correct position and insert.
- **Delete:** The most complex operation; three cases (leaf node, one child, two children - the two-children case requires finding the inorder successor).
- **Inorder traversal:** Gives sorted order in O(n).
- **Validate BST:** Use a range-based recursive approach (pass min and max bounds down the recursion), not a simple "left < root < right" check (which fails for grandparent violations).

### LCA (Lowest Common Ancestor)

The Lowest Common Ancestor problem appears frequently and has multiple variants. For a BST, the LCA is found by traversing from the root: if both nodes are in the left subtree, recurse left; if both are in the right subtree, recurse right; otherwise, the current node is the LCA. For a general binary tree (without BST property), the recursive approach uses the postorder pattern to return the node if found.

---

## Graphs: BFS, DFS, and the Algorithms That Connect Everything {#graphs}

Graphs are the most general data structure and underlie a huge range of problems that are not immediately recognisable as graph problems. The ability to model a problem as a graph and then apply the appropriate traversal or algorithm is one of the most valuable skills in competitive DSA preparation.

### Graph Representations

Graphs can be represented as:
- **Adjacency list:** A hash map (or array of lists) from each node to its list of neighbours. Efficient for sparse graphs; O(V + E) space.
- **Adjacency matrix:** A V × V boolean matrix where entry [i][j] is true if there is an edge from i to j. Efficient for dense graphs and for O(1) edge existence queries; O(V²) space.
- **Edge list:** A list of (u, v) or (u, v, weight) tuples. Used in algorithms like Kruskal's MST.

For most interview problems, adjacency list representation is standard.

### BFS: Level-Order Exploration

BFS (Breadth-First Search) explores a graph level by level, visiting all nodes at distance d before any node at distance d+1. It uses a queue and a visited set.

**When to use BFS:**
- Finding the shortest path in an unweighted graph (BFS guarantees the first path found is the shortest)
- Level-order tree traversal
- Finding connected components
- Multi-source BFS (starting BFS from multiple sources simultaneously - used in 0-1 matrix distances, walls and gates, rotting oranges)

```python
from collections import deque

def bfs(graph, start):
    visited = set([start])
    queue = deque([start])
    
    while queue:
        node = queue.popleft()
        process(node)
        
        for neighbour in graph[node]:
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append(neighbour)
```

### DFS: Deep Exploration

DFS (Depth-First Search) explores as deep as possible along each branch before backtracking. It can be implemented recursively (using the call stack) or iteratively (using an explicit stack).

**When to use DFS:**
- Detecting cycles in a directed graph (using colouring: WHITE/GREY/BLACK)
- Topological sort
- Finding strongly connected components
- Path existence problems
- Flood fill and island counting in grid problems

### Topological Sort

Topological sort produces a linear ordering of nodes in a Directed Acyclic Graph (DAG) such that for every directed edge u → v, node u appears before node v. Two standard algorithms:

**Kahn's Algorithm (BFS-based):** Compute the in-degree of each node. Add all nodes with in-degree 0 to a queue. Repeatedly dequeue a node, add it to the result, and decrement the in-degree of its neighbours (adding any that reach in-degree 0 to the queue). If the result contains all nodes, the graph is a DAG; if not, there is a cycle.

**DFS-based topological sort:** Run DFS; add each node to a stack after all its descendants have been processed (postorder DFS). The reverse of this postorder gives the topological order.

### Shortest Path Algorithms

**BFS:** Unweighted graphs. O(V + E).

**Dijkstra's Algorithm:** Weighted graphs with non-negative edge weights. Uses a min-heap (priority queue). O((V + E) log V). The standard algorithm for "shortest path from a source to all nodes" in interview problems involving weighted graphs.

**Bellman-Ford:** Weighted graphs that may have negative edges (but no negative cycles). O(V * E). Less common in interviews but important to know.

**Floyd-Warshall:** All-pairs shortest path. O(V³). Used when you need the shortest path between every pair of nodes and V is small.

### Union-Find (Disjoint Set Union)

Union-Find is a data structure that efficiently tracks which elements belong to the same connected component, supporting Union (merge two components) and Find (identify which component an element belongs to) operations in near-O(1) amortised time with path compression and union by rank.

**When to use Union-Find:**
- Detecting cycles in undirected graphs
- Checking if adding an edge creates a cycle (Kruskal's MST uses this)
- Connecting components (number of provinces, accounts merge, number of islands II)
- Any problem asking "are these two nodes in the same group?"

Union-Find is often a cleaner and more efficient alternative to BFS/DFS for connectivity problems.

---

## Dynamic Programming: The Pattern-First Approach {#dynamic-programming}

Dynamic programming is consistently rated as the most feared DSA topic in interview surveys, and the fear is partly justified - DP problems have a high variance in difficulty and require both the correct framing and the correct implementation. However, DP is also one of the most pattern-rich topics: once you recognise the 6-7 fundamental DP patterns, a large proportion of interview DP problems become significantly more approachable.

### What Makes a Problem a DP Problem

Two conditions are required for DP to be applicable:

**Optimal Substructure:** The optimal solution to the problem can be constructed from optimal solutions to its subproblems. A problem lacks this property if locally optimal choices do not lead to globally optimal solutions.

**Overlapping Subproblems:** The recursive solution to the problem solves the same subproblems repeatedly. Without overlapping subproblems, plain recursion (divide and conquer) is sufficient and DP adds no benefit.

### The Two DP Implementation Approaches

**Top-Down (Memoisation):** Write the recursive solution first, then add a cache (usually a dictionary or array) to store computed results. On the first call with a given input, compute and cache the result. On subsequent calls with the same input, return the cached result immediately.

Memoisation is the recommended starting point for most candidates because it follows the natural recursive problem decomposition and you only compute states that are actually needed.

**Bottom-Up (Tabulation):** Build the DP table iteratively, starting from the base cases and working up to the final answer. This approach uses O(n) space (or sometimes O(1) with space optimisation) and has no recursion overhead.

For interviews, starting with top-down memoisation and then discussing space optimisation via bottom-up tabulation demonstrates both correctness thinking and optimisation awareness.

### The Six Core DP Patterns

**Pattern 1: Linear DP (1D)**
Problems where the state is a single index or value and the transition depends on a few previous states. Examples: climbing stairs, house robber, maximum subarray, coin change, word break. The state definition is dp[i] = "optimal value considering elements 0 to i," and transitions look back a fixed or bounded number of positions.

**Pattern 2: Two-Sequence DP**
Problems involving two strings or sequences where the state is a pair of indices (i, j). Examples: Longest Common Subsequence (LCS), Edit Distance, Interleaving String. State: dp[i][j] = "optimal value for first i characters of string 1 and first j characters of string 2." This family has O(n*m) time and space complexity, optimisable to O(min(n,m)) space.

**Pattern 3: Interval DP**
Problems where you merge or split intervals and the optimal solution depends on all possible split points. Examples: Burst Balloons, Matrix Chain Multiplication, Palindrome Partitioning II. State: dp[i][j] = "optimal value for the interval [i, j]." These are typically O(n³) with O(n²) space.

**Pattern 4: Subset DP / Knapsack**
Problems where you choose a subset of items to satisfy a constraint. Classic 0/1 Knapsack, Partition Equal Subset Sum, Target Sum. State: dp[i][j] = "whether it is possible to form value j using a subset of the first i items." These are pseudo-polynomial in the value dimension.

**Pattern 5: Tree DP**
DP on tree structures where the state is computed for each subtree and combined bottom-up. The recursive tree pattern naturally gives a DP formulation. Examples: Binary Tree Maximum Path Sum, House Robber III.

**Pattern 6: DP with Bitmask**
Used for problems where the state includes a subset of elements (typically up to 15-20 elements). Examples: Travelling Salesman Problem variants, minimum cost to visit all nodes. State: dp[mask][node] where mask represents the set of visited nodes. These are O(2^n * n) and appropriate only for small n.

### The Four Steps to Solving a DP Problem

1. **Define the state:** What information do you need to uniquely characterise a subproblem? Be precise. "dp[i] = something about the first i elements" or "dp[i][j] = something about elements i through j."

2. **Define the transition:** How do you compute dp[i] from previously computed states? What choices are you making at step i?

3. **Identify the base cases:** What are the smallest subproblems with trivially known answers?

4. **Determine the answer:** Which state(s) in the DP table contain the final answer?

Working through these four steps explicitly before writing any code is the discipline that separates candidates who "kind of understand DP" from those who can derive new DP solutions under interview pressure.

---

## Heaps and Priority Queues: When Order Matters {#heaps}

A heap is a complete binary tree that satisfies the heap property: in a max-heap, every parent is greater than or equal to its children; in a min-heap, every parent is less than or equal to its children. A heap enables O(1) access to the maximum (or minimum) element and O(log n) insertion and deletion.

### Heap Use Cases in Interviews

**Top-K problems:** Finding the top K largest elements, the K most frequent elements, or the K closest points to the origin. Use a min-heap of size K: iterate through all elements, push to the heap, and pop when size exceeds K. The heap always retains the K largest elements seen so far. O(n log K) time.

**K-way merge:** Merging K sorted lists or arrays. Maintain a min-heap of size K, initially containing the first element of each list. Repeatedly extract the minimum, add it to the result, and push the next element from the same list into the heap. O(n log K) time.

**Median of a data stream:** Maintain two heaps: a max-heap for the lower half and a min-heap for the upper half. The median is the top of one or both heaps depending on the total count. Balancing the two heaps after each insertion takes O(log n).

**Dijkstra's algorithm:** A min-heap (priority queue) is the implementation structure for Dijkstra's shortest path algorithm.

**Scheduling and task problems:** Problems about scheduling tasks, rearranging characters to avoid adjacent duplicates, or reorganising a string use max-heaps keyed on frequency.

### Python heapq Note

Python's `heapq` module implements a min-heap only. For max-heap behaviour, negate the keys: push `-value` instead of `value`, and negate on retrieval. For heaps of tuples, the first element of the tuple is the comparison key: `heapq.heappush(heap, (priority, value))`.

---

## The 150 Must-Solve Problems: Curated Topic-Wise List {#must-solve-problems}

The following curated list covers the essential problem patterns across all major interview topics. Problems are listed by topic and difficulty level (E = Easy, M = Medium, H = Hard). Solve them in order within each topic; each problem reinforces the pattern introduced by the previous one.

### Arrays and Strings (20 Problems)

1. Two Sum (E) - Hash map complement pattern
2. Best Time to Buy and Sell Stock (E) - One-pass max profit
3. Contains Duplicate (E) - Hash set existence check
4. Product of Array Except Self (M) - Prefix and suffix product
5. Maximum Subarray (M) - Kadane's algorithm
6. Maximum Product Subarray (M) - Kadane's variant with sign handling
7. Find Minimum in Rotated Sorted Array (M) - Modified binary search
8. Search in Rotated Sorted Array (M) - Binary search with sorted half identification
9. 3Sum (M) - Sort + two pointers
10. Container With Most Water (M) - Two pointers greedy
11. Trapping Rain Water (H) - Two pointers or monotonic stack
12. Longest Substring Without Repeating Characters (M) - Sliding window
13. Minimum Window Substring (H) - Variable sliding window
14. Sliding Window Maximum (H) - Monotonic deque
15. Longest Repeating Character Replacement (M) - Sliding window with frequency map
16. Rotate Array (M) - Reversal technique
17. Merge Intervals (M) - Sort + greedy merge
18. Insert Interval (M) - Linear scan with overlap handling
19. Jump Game (M) - Greedy reachability
20. Spiral Matrix (M) - Layer-by-layer simulation

### Hashing (10 Problems)

21. Group Anagrams (M) - Sort key hash map
22. Top K Frequent Elements (M) - Hash map + heap
23. Valid Anagram (E) - Frequency count
24. Encode and Decode Strings (M) - Custom serialisation
25. Subarray Sum Equals K (M) - Prefix sum + hash map
26. Longest Consecutive Sequence (M) - Hash set streak counting
27. Two Sum II - Input Is Sorted (M) - Two pointers on sorted input
28. 4Sum (M) - Two pointers extension
29. First Missing Positive (H) - Index-as-hash map
30. Majority Element (E) - Boyer-Moore voting

### Two Pointers and Sliding Window (10 Problems)

31. Valid Palindrome (E) - Opposite two pointers
32. Remove Duplicates from Sorted Array (E) - Fast-slow two pointers
33. Move Zeros (E) - In-place partition
34. Permutation in String (M) - Fixed window + character frequency
35. Fruits Into Baskets (M) - Variable window with at-most-K constraint
36. Minimum Size Subarray Sum (M) - Shrinkable window
37. Longest Subarray with Sum at Most K (M) - Variable window
38. Find All Anagrams in a String (M) - Fixed sliding window
39. Longest Turbulent Subarray (M) - State machine sliding window
40. Max Consecutive Ones III (M) - Variable window with constraint

### Recursion and Backtracking (10 Problems)

41. Subsets (M) - Backtracking, all subsets
42. Subsets II (M) - Backtracking with duplicates
43. Permutations (M) - Backtracking, all orderings
44. Permutations II (M) - Backtracking with duplicates
45. Combination Sum (M) - Backtracking with reuse
46. Combination Sum II (M) - Backtracking without reuse
47. Letter Combinations of a Phone Number (M) - Backtracking on decision tree
48. N-Queens (H) - Backtracking with constraint propagation
49. Sudoku Solver (H) - Backtracking with row/col/box constraints
50. Word Search (M) - DFS backtracking on grid

### Stacks and Queues (10 Problems)

51. Valid Parentheses (E) - Stack matching
52. Min Stack (M) - Auxiliary stack for minimum
53. Evaluate Reverse Polish Notation (M) - Operator stack
54. Daily Temperatures (M) - Monotonic decreasing stack
55. Next Greater Element I (E) - Monotonic stack
56. Next Greater Element II (M) - Circular array monotonic stack
57. Largest Rectangle in Histogram (H) - Monotonic stack
58. Basic Calculator II (M) - Stack-based arithmetic
59. Decode String (M) - Stack with counter and builder
60. Sliding Window Maximum (H) - Monotonic deque (also in arrays)

### Linked Lists (10 Problems)

61. Reverse Linked List (E) - Iterative three-pointer reversal
62. Merge Two Sorted Lists (E) - Two-pointer merge
63. Linked List Cycle (E) - Fast-slow pointer detection
64. Reorder List (M) - Find middle + reverse + merge
65. Remove Nth Node From End (M) - Fast pointer n ahead
66. Intersection of Two Linked Lists (E) - Length difference or two-pointer trick
67. Sort List (M) - Merge sort on linked list
68. LRU Cache (M) - Doubly linked list + hash map
69. Reverse Nodes in k-Group (H) - Group reversal with recursion
70. Copy List with Random Pointer (M) - Hash map for cloning

### Binary Search (10 Problems)

71. Binary Search (E) - Standard template
72. Find Minimum in Rotated Sorted Array (M) - (Also in arrays)
73. Search a 2D Matrix (M) - Treat as 1D sorted array
74. Koko Eating Bananas (M) - Binary search on answer
75. Find Peak Element (M) - Binary search on local maximum
76. Time Based Key-Value Store (M) - Binary search on sorted values
77. Median of Two Sorted Arrays (H) - Binary search on partition
78. Split Array Largest Sum (H) - Binary search on answer
79. Capacity to Ship Packages Within D Days (M) - Binary search on answer
80. Minimum Number of Days to Make M Bouquets (M) - Binary search on answer

### Trees (20 Problems)

81. Maximum Depth of Binary Tree (E) - Recursive postorder
82. Same Tree (E) - Recursive structural comparison
83. Invert Binary Tree (E) - Recursive swap
84. Symmetric Tree (E) - Recursive mirror check
85. Maximum Path Sum (H) - Recursive postorder with global max
86. Binary Tree Level Order Traversal (M) - BFS with level tracking
87. Right Side View (M) - BFS, last node per level
88. Count Good Nodes in Binary Tree (M) - Preorder with running max
89. Validate Binary Search Tree (M) - Inorder or range-based recursion
90. Kth Smallest Element in a BST (M) - Inorder traversal
91. LCA of a Binary Search Tree (M) - BST property traversal
92. LCA of a Binary Tree (M) - Recursive postorder
93. Binary Tree from Preorder and Inorder (M) - Divide and conquer
94. Diameter of Binary Tree (E) - Recursive height + global max
95. Flatten Binary Tree to Linked List (M) - Preorder with right rewiring
96. Serialize and Deserialize Binary Tree (H) - BFS or preorder encoding
97. Path Sum (E) - DFS with target tracking
98. Path Sum II (M) - DFS backtracking
99. Populating Next Right Pointers (M) - Level-order BFS
100. Recover Binary Search Tree (M) - Inorder traversal swap detection

### Graphs (20 Problems)

101. Number of Islands (M) - DFS/BFS flood fill
102. Clone Graph (M) - DFS/BFS with hash map
103. Pacific Atlantic Water Flow (M) - Multi-source BFS/DFS
104. Number of Connected Components (M) - Union-Find or DFS
105. Graph Valid Tree (M) - Union-Find cycle detection
106. Course Schedule (M) - Topological sort (cycle detection)
107. Course Schedule II (M) - Topological sort (ordering)
108. Redundant Connection (M) - Union-Find
109. Network Delay Time (M) - Dijkstra's algorithm
110. Cheapest Flights Within K Stops (M) - Bellman-Ford or modified Dijkstra
111. Word Ladder (H) - BFS on implicit graph
112. Alien Dictionary (H) - Topological sort on character ordering
113. Accounts Merge (M) - Union-Find
114. Surrounded Regions (M) - DFS from boundary
115. Walls and Gates (M) - Multi-source BFS
116. Rotting Oranges (M) - Multi-source BFS with timer
117. Minimum Spanning Tree (Kruskal's) - Union-Find + edge sort
118. Swim in Rising Water (H) - Dijkstra or binary search + BFS
119. Reconstruct Itinerary (H) - Hierholzer's algorithm (Eulerian path)
120. Find Critical and Pseudo-Critical Edges (H) - Bridge finding (Tarjan's)

### Dynamic Programming (20 Problems)

121. Climbing Stairs (E) - Linear DP base case
122. House Robber (M) - Linear DP with skip constraint
123. House Robber II (M) - Circular array, two linear DPs
124. Longest Palindromic Substring (M) - Expand around centre or 2D DP
125. Palindromic Substrings (M) - Count of palindromic substrings
126. Coin Change (M) - Unbounded knapsack
127. Coin Change II (M) - Unbounded knapsack, count ways
128. Longest Increasing Subsequence (M) - O(n log n) with patience sort
129. Partition Equal Subset Sum (M) - 0/1 knapsack
130. Target Sum (M) - 0/1 knapsack, count ways
131. Word Break (M) - Linear DP with substring check
132. Unique Paths (M) - 2D DP or combinatorics
133. Longest Common Subsequence (M) - Two-sequence DP
134. Edit Distance (H) - Two-sequence DP
135. Distinct Subsequences (H) - Two-sequence DP, count ways
136. Interleaving String (M) - Two-sequence DP
137. Best Time to Buy and Sell Stock with Cooldown (M) - State machine DP
138. Best Time to Buy and Sell Stock IV (H) - K-transaction DP
139. Burst Balloons (H) - Interval DP
140. Regular Expression Matching (H) - Two-sequence DP with wildcards

### Heaps and Advanced (10 Problems)

141. Kth Largest Element in an Array (M) - Quick select or heap
142. Top K Frequent Words (M) - Heap with custom comparator
143. Find Median from Data Stream (H) - Two heaps
144. Merge K Sorted Lists (H) - K-way merge with min-heap
145. Task Scheduler (M) - Max-heap greedy
146. Reorganize String (M) - Max-heap construction
147. K Closest Points to Origin (M) - Max-heap of size K
148. IPO (H) - Two heaps for greedy capital problem
149. Implement Trie (Prefix Tree) (M) - Trie node structure
150. Design In-Memory File System (H) - Trie with file content storage

---

## Time and Space Complexity: The Language of the Interview {#complexity}

Discussing time and space complexity correctly is a non-negotiable interview skill. Every solution you present must be accompanied by an accurate complexity analysis, stated proactively before the interviewer asks. Candidates who cannot state complexity or who state it incorrectly signal a fundamental gap in their understanding of algorithms.

### Big-O Notation: What It Means and What It Does Not

Big-O notation describes the asymptotic upper bound of an algorithm's resource usage (time or space) as a function of the input size n. It captures how the algorithm scales.

The standard complexity classes in order from fastest to slowest: O(1) - constant, O(log n) - logarithmic, O(n) - linear, O(n log n) - linearithmic, O(n²) - quadratic, O(2^n) - exponential, O(n!) - factorial.

Big-O notation drops constants and lower-order terms: O(3n + 100) simplifies to O(n). O(n² + n) simplifies to O(n²). This simplification is justified because for large n, the dominant term overwhelms the others.

**What interviewers actually care about:** When they ask for time complexity, they want to know: does this scale linearly, quadratically, or logarithmically? Can you identify the dominant operation? Can you explain why? Stating "it's O(n) because we iterate through the array once" is correct and clear. Stating "it's O(n)" with no explanation leaves the interviewer uncertain whether you arrived at the answer by reasoning or guessing.

### Deriving Time Complexity: The Rules

**Single loop over n elements:** O(n). Two nested loops each over n: O(n²). Three nested loops: O(n³).

**Divide-and-conquer recurrences:** Use the Master Theorem. T(n) = 2T(n/2) + O(n) gives O(n log n) (merge sort). T(n) = 2T(n/2) + O(1) gives O(n) (binary tree height). T(n) = T(n/2) + O(1) gives O(log n) (binary search).

**Heap operations:** A heap of size k has push and pop operations costing O(log k). Processing n elements with a heap of size k: O(n log k).

**Recursive backtracking:** Often O(2^n) or O(n!) for problems generating all subsets or all permutations respectively. These complexities are sometimes unavoidable (you must enumerate all solutions), but should be stated accurately.

**Hash map operations:** O(1) average case for insert, lookup, delete. O(n) worst case (all elements hash to the same bucket). In interviews, always state O(1) average but acknowledge the worst case if asked.

### Space Complexity

Space complexity counts all memory used by the algorithm, including the input (in some definitions) and any auxiliary structures. For most interview purposes, we analyse the auxiliary space (extra space beyond the input).

**Recursive call stack:** Each recursive call occupies a stack frame. A recursion that goes n levels deep uses O(n) auxiliary space even if no explicit data structures are allocated. Tree DFS on a balanced tree: O(log n) stack depth. Tree DFS on a skewed tree: O(n). Forgetting the call stack in space complexity analysis is a common interview mistake.

**In-place algorithms:** An algorithm is in-place if it uses O(1) auxiliary space (or O(log n) if recursive). Sorting algorithms: merge sort is O(n) space (the merge requires a temporary array), quicksort is O(log n) average space (call stack depth), and heapsort is O(1) auxiliary space.

### The Complexity Trade-off Discussion

Many interview problems have a trade-off between time and space efficiency. When you present a solution, be prepared to discuss this trade-off:

- "My current solution is O(n) time and O(n) space using a hash map. If space is constrained, we could instead sort the array (O(n log n) time, O(1) auxiliary space) and use two pointers."
- "This recursive solution is O(n) time but O(n) space due to the call stack. Iterating bottom-up with an explicit stack would use O(n) space explicitly but avoid stack overflow for very large inputs."

Demonstrating awareness of trade-offs and discussing them without being prompted is a mark of an experienced, thoughtful candidate.

---

## Tries, Segment Trees, and Union-Find: The Advanced Tier {#advanced-structures}

Advanced data structures appear in 15-20% of senior-level product-based company interviews and in the hard problems at companies with the most selective interview processes. They are not required for everyone, but knowing them expands the set of problems you can solve efficiently.

### Tries (Prefix Trees)

A Trie is a tree-based data structure where each path from the root to a node represents a prefix of some stored string. Tries enable O(L) insert, search, and prefix-search operations where L is the string length, regardless of the number of strings stored.

**When to use a Trie:**
- When a problem involves prefix matching ("find all words starting with prefix X")
- When a problem involves searching a large dictionary of strings for exact or prefix matches
- When you need to count distinct prefixes or autocomplete suggestions

**Trie node structure:**

```python
class TrieNode:
    def __init__(self):
        self.children = {}  # or array of 26 for lowercase only
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
    
    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end
```

Interview problems that require a Trie: Implement Trie, Word Search II (Trie + backtracking), Design Search Autocomplete System, Replace Words, Maximum XOR of Two Numbers in an Array (using a binary Trie).

### Segment Trees

A Segment Tree is a binary tree built over an array that enables both range queries (sum, minimum, maximum over a subarray) and point updates in O(log n) time each.

The Segment Tree is the answer to problems that require both range queries AND updates. If only range queries are needed (no updates), a prefix sum array suffices. If only point updates are needed (no range queries), a simple array suffices. Segment trees handle the combined case.

**Interview appearance:** Segment trees appear in hard problems and in competitive programming. For most product-based company interviews below the FAANG senior level, understanding what a segment tree does and its complexity is sufficient. Implementing one from scratch is required only for the most selective interviews.

### Fenwick Tree (Binary Indexed Tree)

A Fenwick Tree (BIT) is a more space-efficient alternative to a Segment Tree for the specific case of prefix sum queries with point updates. It stores partial sums using the binary representation of indices, enabling O(log n) prefix sum queries and O(log n) point updates in O(n) space with a very simple implementation.

Common interview use: Count of Smaller Numbers After Self, Reverse Pairs, Calculate the Sum of Elements Between Queries.

### Union-Find with Path Compression

Union-Find (Disjoint Set Union) was introduced in the graphs section. The optimised implementation deserves explicit coverage:

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # path compression
        return self.parent[x]
    
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False  # already connected
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        return True
```

Path compression (in the find method) and union by rank together give near-O(1) amortised time for both operations. Memorise and understand this implementation - it appears in Kruskal's MST, number of islands II, accounts merge, and many graph connectivity problems.

---

## Online Platforms and Resources: Where to Practice {#platforms}

The quality of your practice platform matters. Not all platforms provide the same quality of problems, explanations, or community resources.

### Primary Practice Platform

**LeetCode:** The standard platform for product-based company interview preparation. LeetCode's problem database is the most directly aligned with actual interview questions, its discuss section contains community solutions with complexity analysis, and its tagged problem lists allow topic-focused practice. The premium subscription (LeetCode Premium) unlocks company-tagged problems (problems frequently asked at specific companies) and the mock interview feature. For serious preparation, the premium is worth the cost in the final 4-6 weeks before interviews.

### Secondary Practice Platforms

**InterviewBit:** Strong structured learning path with topic-wise problem sets and embedded conceptual notes. Particularly well-regarded for its topic introductions and for candidates who need more guided hand-holding through DSA topics compared to LeetCode's problem-only format.

**GeeksForGeeks:** The most comprehensive free reference for DSA concepts, algorithm explanations, and implementation examples. Less useful as a practice platform (problem quality and editorial quality are uneven) but extremely valuable as a reference and concept-learning resource. If you need to understand how an algorithm works before solving problems on it, GeeksforGeeks is the first stop.

**Codeforces:** The leading competitive programming platform. Problems are harder and more mathematically demanding than LeetCode interview problems, but regular Codeforces contest practice builds speed, accuracy under pressure, and familiarity with edge cases that translates to better interview performance. Participating in Div 2 contests (the beginner-to-intermediate level) two to three times per week in the months before interviews is a high-leverage supplement.

**Pramp and Interviewing.io:** Mock interview platforms where you practice with a real partner in a real-time coding environment. Pramp is free and peer-based (you interview others in exchange for being interviewed). Interviewing.io connects you with senior engineers at top companies for anonymous practice interviews and is particularly valuable for realistic FAANG-level interview simulation. Both platforms are highly recommended for the final 4 weeks of preparation.

### Reference Books

**Introduction to Algorithms (CLRS):** The authoritative academic text covering algorithms and data structures with rigorous proofs. Not a cover-to-cover interview prep book, but the relevant chapters (sorting, graph algorithms, dynamic programming, data structures) provide the deepest conceptual foundation available. Useful as a reference when you need to understand why an algorithm works rather than just how.

**Cracking the Coding Interview by Gayle Laakmann McDowell:** The most widely read coding interview preparation book. Its problem-solving framework, 189 programming questions, and insider perspective on what interviewers evaluate make it a strong complement to platform-based practice.

**Elements of Programming Interviews (EPI):** A denser, more rigorous alternative to CTCI with a broader problem set and deeper solution analysis. Particularly strong on problems involving arrays, strings, linked lists, and trees. Many serious candidates work through both CTCI and EPI.

### Staying Current With Interview Trends

Interview formats and question types evolve. Staying informed through community resources is part of ongoing preparation. Leetcode discuss forums, Blind (a professional anonymous networking platform popular with tech employees for sharing interview experiences), and Glassdoor interview reviews for specific companies all provide current, first-hand interview experience reports. Cross-reference reported questions with your preparation list and fill any topic gaps identified.

---

## Pattern Recognition: The Meta-Skill That Accelerates Preparation {#pattern-recognition}

Pattern recognition is the ability to look at a new problem and immediately identify which algorithmic technique or data structure is likely the key to the solution. It is the meta-skill that transforms preparation from memorisation of individual solutions into a transferable problem-solving capability.

### The Pattern Identification Map

Use the following mapping from problem characteristics to likely solutions:

| Problem Characteristic | Likely Pattern |
|---|---|
| "Find if a pair exists with sum K" | Hash map |
| "Subarray / substring satisfying a property" | Sliding window or prefix sum |
| "K largest / K smallest elements" | Min/max heap of size K |
| "All subsets / all permutations / all combinations" | Backtracking |
| "Sorted array, find target" | Binary search |
| "Tree traversal or path problem" | DFS (recursive) or BFS |
| "Shortest path in graph" | BFS (unweighted) or Dijkstra (weighted) |
| "Connected components / cycle detection" | Union-Find or DFS |
| "Ordering with dependencies" | Topological sort |
| "Optimal substructure + overlapping subproblems" | Dynamic programming |
| "Next greater element / monotonic order" | Monotonic stack |
| "Nearest / closest element queries" | Sorted set (TreeMap) or binary search |
| "String prefix matching" | Trie |
| "Minimum / maximum at every window position" | Monotonic deque |

### Building Pattern Recognition Through Deliberate Practice

Pattern recognition is not built by solving many problems randomly. It is built by deliberately grouping problems by pattern, solving 5-10 problems from the same pattern family back-to-back, and then verbalising what they have in common.

After solving the 150 problems in this guide, go back and categorise each problem you solved into its primary pattern. If you cannot immediately identify the pattern for a problem you have already solved, that is a signal to re-examine it. Eventually, the pattern identification should happen within the first 30-60 seconds of reading a new problem statement.

---

## The 12-Week Structured Revision Plan {#revision-plan}

This plan assumes approximately 2 hours of focused daily practice on weekdays and 3-4 hours on weekends, totalling roughly 14-16 hours per week. Adjust the pace based on your existing knowledge baseline.

### Weeks 1-3: Linear Structures and Core Patterns

**Week 1:** Arrays and Strings (Problems 1-20). Focus on implementing each solution from scratch without looking at hints after the first attempt. After each problem, write down the pattern it exemplifies.

**Week 2:** Hashing and Two Pointers (Problems 21-40). Maintain a "pattern journal" - a notebook or document where you write the pattern name, the signal that indicates it, and 2-3 example problems.

**Week 3:** Backtracking and Stacks/Queues (Problems 41-60). Implement the backtracking template and apply it to each problem variation. Practise the monotonic stack pattern on at least 5 problems.

### Weeks 4-6: Non-Linear Structures

**Week 4:** Linked Lists and Binary Search (Problems 61-80). Draw pointer diagrams for every linked list problem before coding. Implement binary search on answer space for at least 3 problems.

**Week 5:** Trees I - Traversals and Recursive Pattern (Problems 81-100, first half). Implement all four traversals without referencing material. Derive the recursive template and apply it to depth, diameter, path sum, and validate BST.

**Week 6:** Trees II and Heaps (Problems 81-100, second half and 141-150 heaps). Focus on BST operations and LCA variants. Implement the two-heap median problem.

### Weeks 7-9: Graphs and Dynamic Programming

**Week 7:** Graphs I - BFS, DFS, and connectivity (Problems 101-115). Implement BFS and DFS from scratch. Solve all connected components, island, and BFS shortest-path problems.

**Week 8:** Graphs II - Advanced (Problems 116-120). Implement Union-Find with path compression and union by rank. Implement Dijkstra from scratch.

**Week 9:** Dynamic Programming (Problems 121-140). Follow the four-step framework (state, transition, base case, answer) for every problem. Spend extra time on the two-sequence DP family (LCS, Edit Distance) and the knapsack family.

### Weeks 10-11: Review and Integration

**Week 10:** Re-solve all problems you previously got wrong or found slow. Without referencing your earlier solutions, solve from scratch in 25 minutes. Track time to solution.

**Week 11:** Mixed-topic timed sessions. Set a 45-minute timer, pick two random problems from the 150 list across different topics, and solve them as if in an interview. Practise thinking aloud.

### Week 12: Mock Interviews and System Design

**Week 12:** Conduct at least 3-4 mock interviews with a partner or on a platform (Pramp, Interviewing.io, LeetCode's mock interview feature). Each mock interview should be 45-60 minutes with a coding problem, communication scoring, and post-interview debrief. If you are a candidate with 3+ years of experience, spend at least 5-6 hours on system design fundamentals: scalability, database design, caching, load balancing, and the design of 2-3 canonical systems (URL shortener, rate limiter, messaging queue).

### Tracking Progress Metrics

Tracking the right metrics throughout preparation provides honest feedback on readiness. The following metrics are more useful than raw problem count:

**Time-to-solution by difficulty:** How long does it take you to solve an easy, medium, and hard problem from scratch? Target benchmarks for interview readiness: Easy in under 10 minutes, Medium in 20-30 minutes, Hard in 45 minutes or with one hint. Track these times weekly to see objective improvement.

**First-attempt solve rate:** What percentage of new medium problems do you solve correctly on the first attempt without hints? A rate above 60% on mediums indicates solid pattern fluency. Below 40% suggests you need more pattern study before increasing problem volume.

**Pattern identification speed:** Before attempting a problem, how quickly (and accurately) can you identify the primary pattern? Time yourself from reading the problem to identifying the likely approach. Reducing this to under 60 seconds for common patterns is a concrete, measurable goal.

**Code quality self-assessment:** After each solution, score your own code on: variable naming, modularity, handling of edge cases, and absence of redundant code. Improving code quality on practice problems directly translates to interview code quality.

### The Final 48 Hours Before the Interview

Do not introduce new material in the final 48 hours. The goal is to arrive at the interview mentally fresh, confident, and warm - not exhausted from a last-minute cramming session.

On the day before the interview, spend no more than 90 minutes on two or three easy warm-up problems in your primary language to activate your coding recall. Review your pattern journal one final time. Confirm logistics (interview link or venue, time zone, equipment check for virtual interviews).

On the interview day itself, do not practice in the morning before the interview. Eat well, arrive (or log on) a few minutes early, and enter the interview in a calm state. The preparation is done; the interview is the performance.

---

## Mock Interviews and the Communication Framework {#mock-interviews}

Technical correctness is necessary but not sufficient for interview success. How you communicate throughout the problem-solving process is evaluated equally. The following communication framework, practised until it is natural, structures a 45-minute coding interview optimally.

### The 5-Phase Interview Framework

**Phase 1 - Understand (3-5 minutes):** Read the problem carefully. Immediately ask clarifying questions:
- What is the expected input range? (Helps determine if overflow handling is needed)
- Are there negative numbers? (Critical for many array problems)
- Can the input be empty? (Defines base cases)
- Are elements unique? (Changes approach for duplicates)
- What should be returned in edge cases?

Never start coding before fully understanding the problem. Interviewers actively reward the habit of clarification.

**Phase 2 - Plan Aloud (5-10 minutes):** Describe your approach in English before writing a single line of code. Start with a brute force solution ("The naive approach would be..."), then reason toward optimisation ("But we can improve this by..."). State the time and space complexity of your proposed solution and confirm with the interviewer before coding. This phase prevents you from writing code in the wrong direction and demonstrates structured thinking.

**Phase 3 - Code (15-20 minutes):** Write code while narrating what you are doing. Not a constant stream of explanation, but enough that the interviewer knows what each major step is doing ("I'm using a hash map here to track frequencies..."). Write clean, readable code with meaningful variable names. Do not rush.

**Phase 4 - Test (5-7 minutes):** After writing the code, immediately test it on the example cases from the problem, then on edge cases you identified earlier (empty input, single element, all same values, negative numbers). Trace through your code by hand rather than declaring "it should work."

**Phase 5 - Optimise and Discuss (remaining time):** Discuss the time and space complexity of your solution. If you have a suboptimal solution, think aloud about how you would improve it. If you know there is a better approach but could not implement it, say so and describe the better approach conceptually. Interviewers credit honest self-assessment.

### The Most Common Communication Failures

**Silent coding:** Writing code for 20 minutes without speaking is the most common failure mode. The interviewer cannot score your reasoning; they can only see code appearing on screen. Develop the habit of thinking aloud even if it feels unnatural initially.

**Premature coding:** Jumping into code within 2 minutes of reading the problem, without discussing approach, leads to wrong solutions that require full rewrites. Always plan before coding.

**Over-apologising for the brute force:** Starting with a brute force solution and then optimising is a perfectly valid and well-regarded interview strategy. Apologising excessively for the brute force ("I know this is bad but...") signals self-doubt. Present the brute force clearly and confidently as Step 1 of your reasoning.

**Giving up:** If you are stuck, say "I'm not immediately seeing the optimal approach - let me think through a simpler version of the problem first" and work through small examples. Interviewers are trained to give hints; there is no penalty for asking for a hint if framed appropriately ("Would it help to focus on a particular aspect?"). Sitting silently for five minutes is worse than asking for direction.

---

## Frequently Asked Questions {#faq}

**Q1: How many LeetCode problems do I need to solve to crack a product-based company interview?**

Quality and pattern coverage matter far more than raw volume. Candidates who have deeply solved 150-200 problems across all major patterns, and can explain their reasoning clearly, consistently outperform candidates who have churned through 600+ problems without internalising the patterns. The goal is pattern fluency, not problem count. The 150 problems in this guide, solved with deliberate attention to patterns and time complexity, are sufficient preparation for most product-based company interviews including mid-tier product companies and the lower half of FAANG/MAANG-tier companies. For the most selective companies, supplement with an additional 50-100 medium-hard problems and focus heavily on mock interviews.

**Q2: Should I start with easy, medium, or hard problems?**

Start with easy problems in each topic area to solidify the fundamental pattern, then move to medium problems, which form the bulk of interview questions. Hard problems should be attempted only after you can consistently solve medium problems in 20-25 minutes. Attempting hard problems too early creates frustration and an inaccurate sense of your readiness. One hard problem per day in the final month of preparation, reviewed with solution analysis, is a reasonable exposure level.

**Q3: Is competitive programming (Codeforces, CodeChef) necessary for product-based company interviews?**

Competitive programming builds excellent problem-solving speed and mathematical intuition but covers a broader and harder problem space than interview preparation. For interview preparation, LeetCode is more targeted and efficient. Competitive programming is a valuable long-term skill that naturally improves interview performance, but it is not a prerequisite and should not replace dedicated interview-focused practice in the weeks before interviews.

**Q4: How should I prepare for system design interviews?**

System design interviews are typically required for candidates with 3+ years of experience. The preparation involves learning the core concepts (horizontal vs vertical scaling, load balancers, caching layers, database sharding and replication, message queues, CDNs, consistent hashing) and practising the design of 10-15 canonical systems (URL shortener, rate limiter, social media feed, distributed cache, messaging system, ride-sharing system). Key resources include the System Design Primer (available free on GitHub), Designing Data-Intensive Applications (the standard text in the field), and Grokking System Design courses. Allocate at least 4-6 weeks to system design preparation in parallel with the final DSA practice weeks.

**Q5: Is it better to prepare in Python or Java for coding interviews?**

Both are excellent choices. Python's concise syntax allows you to write solutions faster, which is valuable in timed interviews, and its standard library (collections.deque, heapq, defaultdict, Counter, sorted with key) is extremely powerful. Java's verbosity requires more typing but the strong typing catches more bugs before submission. The important factors are: use the language you know most fluently, know the standard library for that language deeply, and practise until your chosen language's syntax is completely automatic so you never waste interview time on syntax lookup.

**Q6: How do I maintain motivation during a 12-week preparation period?**

DSA preparation is a long-duration effort, and motivation management is a genuine challenge. Strategies that work: track progress concretely (a problem count, a topics-covered checklist) so you can see measurable advancement; set small daily goals rather than vague large ones; join a preparation group or find a partner to mock interview with; take one full rest day per week; and remind yourself periodically of the specific companies and roles that motivate the preparation. Burnout in month two is the most common reason capable candidates underperform in interviews they are technically ready for.

**Q7: What should I do the week before the interview?**

Do not start new topics. Practise only problems you have previously solved, aiming to solve them faster and more cleanly than before. Conduct one mock interview in as realistic conditions as possible (webcam on, timed, spoken communication). Review your pattern journal. Get sufficient sleep every night of the week before the interview. On the day before the interview, solve at most two easy warm-up problems and stop. Mental freshness on interview day is more valuable than one additional day of grinding.

**Q8: How much weight does communication carry versus solution correctness?**

At most top product-based companies, a candidate who solves a problem partially but communicates their reasoning clearly, handles feedback well, and demonstrates structured thinking will score comparably to a candidate who silently arrives at the correct solution. Communication and collaboration are explicitly weighted in rubrics alongside problem-solving and coding quality. Both matter; neither is sufficient on its own. The practical implication: a clean, well-explained O(n log n) solution is generally scored higher than a silent, correct O(n) solution with no explanation.

**Q9: How do I handle a problem I have never seen and have no idea how to approach?**

This scenario happens to every candidate, including experienced ones. The correct response is a structured exploration rather than panic. Start by working through small examples by hand - draw the input and trace what the output should be for 2-3 examples. Identify what information you need to compute at each step. Ask yourself: "Is this similar to a problem I have seen before?" even partially. If you cannot find the right approach in 5 minutes, state your best guess at an approach, explain why you think it might work, and ask the interviewer if that direction is worth pursuing. Interviewers are significantly more impressed by systematic exploration and honest communication than by silence followed by a lucky correct guess.

**Q10: What is the best way to recover if I write incorrect code mid-interview?**

Discovering a bug in your code mid-interview is normal and not disqualifying. Do not panic or over-apologise. Calmly trace through your code with a small example to identify where the bug is. Say aloud what you are doing ("Let me trace through this with the example to find the issue"). When you find the bug, explain what was wrong before fixing it. This demonstrates debugging ability, which is a genuine engineering skill. Candidates who catch and fix their own bugs in a structured way often score better than candidates who wrote correct code instantly, because the debugging process reveals their thinking process.

---

DSA interview preparation is one of the most systematic challenges in a software engineer's career, and systematic preparation is exactly what it rewards. The candidates who succeed do not have higher raw intelligence than those who do not; they have invested deliberate, structured practice time over a sustained period, built genuine pattern fluency, and learned to perform under the specific conditions of a coding interview. Every hour of honest practice - solving problems from scratch, explaining reasoning aloud, reviewing wrong answers thoroughly - compounds into interview readiness. Start with the foundation, follow the roadmap, use the revision plan, and trust that the process works.
