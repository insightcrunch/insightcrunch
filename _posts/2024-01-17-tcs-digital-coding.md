---
layout: post
title: "TCS Digital Coding: Competitive Level Prep"
page_title: "TCS Digital Advanced Coding Guide - Competitive Programming Topics, Solutions, and 45-Day Preparation Roadmap"
date: 2024-01-17
categories: ["Industry"]
tags: ["TCS Digital coding", "TCS advanced coding", "TCS CodeVita", "competitive programming", "TCS Digital DSA"]
excerpt: "Competitive programming preparation for TCS Digital. Advanced DSA topics, original problems with solutions, and a 45-day roadmap."
image: "/assets/images/blog/blog-14.webp"
reading_time: 60
author: "Insight Crunch Team"
---

The TCS Digital Advanced Coding section is the single highest-leverage preparation target for candidates who want the Digital profile. Everything else - Foundation aptitude, verbal, reasoning - gets you into the pool. Coding performance determines which pool you end up in. A candidate who solves both Advanced Coding problems fully and correctly will almost certainly receive a Digital offer. A candidate who solves neither will likely receive Ninja or nothing. The gap between these outcomes is not talent - it is preparation. This guide maps the exact topics, patterns, and problem types that TCS Digital coding tests, provides original problems with complete solutions in both Java and C++, and gives you a 45-day roadmap to get there from wherever you are starting.

![TCS Guide](/assets/images/blog/blog-14.webp)

## The TCS Digital Advanced Coding Environment

Before diving into topics, you must understand the environment you are coding in. Knowing the compiler, the scoring model, and the constraints in advance eliminates test-day surprises that cost you marks.

### The Compiler and Platform

TCS Digital Advanced Coding runs on the TCS iON platform using what TCS refers to as a "CodeVita-style" compiler environment. This means:

**Language options:** C, C++, Java, Python. For competitive coding at Digital level, C++ is the strongest choice for most candidates because it runs fastest, has the STL (Standard Template Library) which provides ready implementations of all major data structures, and is the language of the competitive programming community. Java is the second choice - slightly slower than C++ but with robust standard libraries. Python is too slow for time-constrained problems at this difficulty level; avoid it for Digital coding.

**Memory and time limits:** Problems specify time limits (typically 1-2 seconds per test case) and memory limits (typically 256 MB). A solution that is logically correct but algorithmically inefficient (O(n^2) where O(n log n) is required) will time out on large test cases. Understanding complexity and choosing the right algorithm is not optional at Digital level.

**IDE features:** The TCS iON coding editor provides syntax highlighting and basic compilation. There is no autocomplete. You cannot run your code against custom test inputs before submitting - you can only compile and submit. This means mental testing and paper tracing of edge cases is essential before submission.

### Scoring Mechanism

TCS Digital Advanced Coding scores problems by test cases passed:

- Each problem has a set of test cases (typically 10-15)
- Each test case passed earns a proportional share of the problem's total marks
- Partial credit is awarded - a solution passing 7 of 10 test cases earns 70% of the problem's marks
- No penalty for incorrect submissions (you can resubmit as many times as time permits)
- The final score is the best submission across all attempts

**Strategic implications:**

Because of partial credit, always submit something. A brute-force O(n^2) solution that passes the smaller test cases is better than an unsubmitted optimal solution. Write the brute-force first, submit it, then optimise if time permits. The partial credit from the brute-force submission is secure while you work on the improvement.

Because there is no submission penalty, submit early and often. Every time you make a meaningful improvement, submit. Do not wait until the solution is "perfect" - in competitive coding, perfect is the enemy of submitted.

### The Relationship With TCS CodeVita

TCS CodeVita is TCS's annual global competitive coding competition. The Digital Advanced Coding section uses the same compiler infrastructure and a similar difficulty profile to CodeVita problems. Specifically:

- Digital Problem 1 is approximately CodeVita Round 1 difficulty (accessible competitive programming, LeetCode Medium range)
- Digital Problem 2 is approximately CodeVita Round 2 difficulty (genuine competitive programming, LeetCode Hard to CodeChef Division 2 range)
- Digital Problem 3 (when present) is approximately CodeVita Finals difficulty (requires advanced algorithmic knowledge)

Strong CodeVita performance feeds directly into TCS Digital and Prime profile selection. Candidates who participate in and perform well in CodeVita are sometimes shortlisted for Digital profiles without going through the standard NQT/ITP process. The two programs are genuinely connected - not just structurally similar, but organically linked in how TCS identifies technical talent.

### Difficulty Calibration Compared to Other Platforms

| Level | Comparable Difficulty |
|---|---|
| TCS Digital Problem 1 | LeetCode Medium, CodeChef Div 3 |
| TCS Digital Problem 2 | LeetCode Hard, CodeChef Div 2 |
| TCS Digital Problem 3 | LeetCode Hard (top 20%), CodeChef Div 1 |
| TCS Ninja Coding | LeetCode Easy-Medium, HackerRank Medium |

This calibration matters for preparation: practising only on LeetCode Easy or HackerRank Medium is insufficient for Digital. Your preparation must include LeetCode Medium (to solidify Problem 1 capability) and LeetCode Hard attempts (to build Problem 2 capability).

---

## Topic 1: Advanced Array Techniques

Arrays underlie most competitive programming problems. The techniques in this section transform naive O(n^2) solutions into O(n) or O(n log n) solutions that pass time limits.

### Prefix Sums

Prefix sums precompute cumulative totals so that range sum queries become O(1) instead of O(n).

**Construction:** `prefix[i] = prefix[i-1] + arr[i]` for 0-indexed arrays (with `prefix[0] = 0` as a sentinel).

**Range query:** Sum of arr[l..r] = `prefix[r+1] - prefix[l]`

**Problem: Subarray Sum Equals K**

Given an array of integers and a target K, count the number of subarrays whose sum equals K.

*Approach:* Prefix sum + HashMap. For each index r, we need prefix[r] - K to have appeared before. Count occurrences.

**Java solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(), k = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();

        Map<Integer, Integer> countMap = new HashMap<>();
        countMap.put(0, 1); // empty prefix
        int prefixSum = 0, result = 0;

        for (int num : arr) {
            prefixSum += num;
            result += countMap.getOrDefault(prefixSum - k, 0);
            countMap.put(prefixSum, countMap.getOrDefault(prefixSum, 0) + 1);
        }
        System.out.println(result);
    }
}
```

**C++ solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, k; cin >> n >> k;
    vector<int> arr(n);
    for (int& x : arr) cin >> x;

    unordered_map<int,int> cnt;
    cnt[0] = 1;
    int prefix = 0, ans = 0;
    for (int x : arr) {
        prefix += x;
        ans += cnt[prefix - k];
        cnt[prefix]++;
    }
    cout << ans << endl;
}
```

**Time:** O(n). **Space:** O(n). The `#include <bits/stdc++.h>` header in C++ includes everything - standard competitive programming shorthand.

### Two-Pointer and Sliding Window (Advanced)

**Problem: Minimum Length Subarray With Sum >= Target (Positive Integers)**

Given an array of positive integers and a target S, find the minimum length contiguous subarray with sum >= S. Return 0 if none exists.

**Java solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(), s = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();

        int left = 0, sum = 0, minLen = Integer.MAX_VALUE;
        for (int right = 0; right < n; right++) {
            sum += arr[right];
            while (sum >= s) {
                minLen = Math.min(minLen, right - left + 1);
                sum -= arr[left++];
            }
        }
        System.out.println(minLen == Integer.MAX_VALUE ? 0 : minLen);
    }
}
```

**C++:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, s; cin >> n >> s;
    vector<int> a(n); for (int& x : a) cin >> x;
    int l = 0, sum = 0, ans = INT_MAX;
    for (int r = 0; r < n; r++) {
        sum += a[r];
        while (sum >= s) { ans = min(ans, r-l+1); sum -= a[l++]; }
    }
    cout << (ans == INT_MAX ? 0 : ans) << endl;
}
```

**Time:** O(n). **Space:** O(1).

### Kadane's Algorithm (Extended: Maximum Subarray With Indices)

The basic Kadane's finds the maximum sum. The extended version also returns the start and end indices of the optimal subarray.

**C++:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n; cin >> n;
    vector<int> a(n); for (int& x : a) cin >> x;

    int maxSum = a[0], curSum = a[0];
    int start = 0, end = 0, tempStart = 0;

    for (int i = 1; i < n; i++) {
        if (curSum + a[i] < a[i]) {
            curSum = a[i];
            tempStart = i;
        } else {
            curSum += a[i];
        }
        if (curSum > maxSum) {
            maxSum = curSum;
            start = tempStart;
            end = i;
        }
    }
    cout << "Max sum: " << maxSum << " [" << start << ", " << end << "]" << endl;
}
```

---

## Topic 2: String Algorithms

String problems at Digital level require knowledge of efficient pattern matching algorithms beyond the brute-force O(n*m) approach.

### KMP (Knuth-Morris-Pratt) Algorithm

KMP finds all occurrences of a pattern P in a text T in O(n + m) time, where n = |T| and m = |P|. The key is the failure function (also called the LPS array - Longest Proper Prefix which is also Suffix).

**Why TCS tests it:** String pattern matching problems are common in Digital coding. A candidate who implements brute-force O(n*m) will time out on large inputs. KMP is the expected solution.

**Problem: Count occurrences of pattern P in text T (overlapping allowed)**

**Java:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String text = sc.nextLine();
        String pattern = sc.nextLine();

        int n = text.length(), m = pattern.length();
        int[] lps = computeLPS(pattern);

        int count = 0, j = 0;
        for (int i = 0; i < n; ) {
            if (text.charAt(i) == pattern.charAt(j)) { i++; j++; }
            if (j == m) {
                count++;
                j = lps[j - 1]; // allow overlap
            } else if (i < n && text.charAt(i) != pattern.charAt(j)) {
                if (j != 0) j = lps[j - 1];
                else i++;
            }
        }
        System.out.println(count);
    }

    static int[] computeLPS(String p) {
        int m = p.length();
        int[] lps = new int[m];
        int len = 0, i = 1;
        while (i < m) {
            if (p.charAt(i) == p.charAt(len)) { lps[i++] = ++len; }
            else if (len != 0) { len = lps[len - 1]; }
            else { lps[i++] = 0; }
        }
        return lps;
    }
}
```

**Time:** O(n + m). **Space:** O(m) for the LPS array.

### String Hashing (Rolling Hash)

String hashing enables O(1) comparison of substrings after O(n) preprocessing. It is the basis of the Rabin-Karp algorithm and is used for problems involving finding duplicate substrings, palindrome checks on substrings, and string matching.

**Concept:** Assign each string a numeric hash value using polynomial hashing: `hash(s) = s[0]*p^(n-1) + s[1]*p^(n-2) + ... + s[n-1]*p^0 (mod M)`. Precompute prefix hashes so that the hash of any substring can be computed in O(1).

**C++ (Rabin-Karp pattern matching):**
```cpp
#include <bits/stdc++.h>
using namespace std;
const long long MOD = 1e9+7, BASE = 31;

int main() {
    string text, pattern;
    cin >> text >> pattern;
    int n = text.size(), m = pattern.size();

    // Compute hash of pattern
    long long pHash = 0, power = 1;
    for (int i = 0; i < m; i++) {
        pHash = (pHash + (pattern[i] - 'a' + 1) * power) % MOD;
        if (i < m-1) power = power * BASE % MOD;
    }

    // Rolling hash on text
    long long tHash = 0; power = 1;
    for (int i = 0; i < m; i++) {
        tHash = (tHash + (text[i] - 'a' + 1) * power) % MOD;
        if (i < m-1) power = power * BASE % MOD;
    }

    int count = 0;
    long long inv = 1; // modular inverse of BASE (for rolling)
    // For simplicity, recompute for each window (O(nm) but hash comparison is fast in practice)
    for (int i = 0; i <= n - m; i++) {
        if (tHash == pHash) {
            if (text.substr(i, m) == pattern) count++; // verify to handle collisions
        }
        if (i < n - m) {
            tHash = (tHash - (text[i] - 'a' + 1) + MOD) % MOD;
            tHash = tHash * 1 % MOD; // shift - simplified; full rolling hash uses modular inverse
            tHash = (tHash + (text[i+m] - 'a' + 1) * power) % MOD;
        }
    }
    cout << count << endl;
}
```

---

## Topic 3: Dynamic Programming

DP is the highest-frequency advanced topic in TCS Digital coding. Problems require recognising when DP applies, defining the right state, and implementing the recurrence efficiently.

### 1D DP: Longest Increasing Subsequence (LIS)

**Problem:** Given an array of N integers, find the length of the longest strictly increasing subsequence.

**Example:** [3, 1, 4, 1, 5, 9, 2, 6] → LIS length = 4 ([1, 4, 5, 9] or [1, 2, 5, 9] or [1, 2, 6])

**O(n^2) DP approach:**

```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = sc.nextInt();

        int[] dp = new int[n];
        Arrays.fill(dp, 1); // each element is a subsequence of length 1
        int maxLen = 1;

        for (int i = 1; i < n; i++) {
            for (int j = 0; j < i; j++) {
                if (arr[j] < arr[i]) {
                    dp[i] = Math.max(dp[i], dp[j] + 1);
                }
            }
            maxLen = Math.max(maxLen, dp[i]);
        }
        System.out.println(maxLen);
    }
}
```

**O(n log n) approach using patience sorting (C++):**

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n; cin >> n;
    vector<int> a(n); for (int& x : a) cin >> x;

    vector<int> tails; // tails[i] = smallest tail of all IS of length i+1
    for (int x : a) {
        auto it = lower_bound(tails.begin(), tails.end(), x);
        if (it == tails.end()) tails.push_back(x);
        else *it = x;
    }
    cout << tails.size() << endl;
}
```

**Time:** O(n log n) with binary search. This is the expected approach for large n.

### 2D DP: Edit Distance

**Problem:** Given two strings S1 and S2, find the minimum number of operations (insert, delete, replace) required to transform S1 into S2.

**C++:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    string s1, s2; cin >> s1 >> s2;
    int m = s1.size(), n = s2.size();
    vector<vector<int>> dp(m+1, vector<int>(n+1));

    for (int i = 0; i <= m; i++) dp[i][0] = i; // delete all of s1
    for (int j = 0; j <= n; j++) dp[0][j] = j; // insert all of s2

    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (s1[i-1] == s2[j-1]) dp[i][j] = dp[i-1][j-1];
            else dp[i][j] = 1 + min({dp[i-1][j],   // delete from s1
                                     dp[i][j-1],   // insert into s1
                                     dp[i-1][j-1]  // replace
                                    });
        }
    }
    cout << dp[m][n] << endl;
}
```

**Time:** O(m x n). **Space:** O(m x n), reducible to O(min(m,n)) with space optimisation.

### Knapsack Variants

**Unbounded Knapsack (each item can be used unlimited times):**

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, W; cin >> n >> W;
    vector<int> w(n), v(n);
    for (int i = 0; i < n; i++) cin >> w[i] >> v[i];

    vector<int> dp(W+1, 0);
    for (int j = 1; j <= W; j++)
        for (int i = 0; i < n; i++)
            if (w[i] <= j)
                dp[j] = max(dp[j], dp[j - w[i]] + v[i]);

    cout << dp[W] << endl;
}
```

The key difference from 0/1 knapsack: iterate capacity from 1 to W (forward), not W to 1 (backward), allowing the same item to be used multiple times.

**Coin Change (minimum coins for exact amount):**

```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(), amount = sc.nextInt();
        int[] coins = new int[n];
        for (int i = 0; i < n; i++) coins[i] = sc.nextInt();

        int[] dp = new int[amount + 1];
        Arrays.fill(dp, amount + 1); // "infinity"
        dp[0] = 0;

        for (int i = 1; i <= amount; i++)
            for (int coin : coins)
                if (coin <= i)
                    dp[i] = Math.min(dp[i], dp[i - coin] + 1);

        System.out.println(dp[amount] > amount ? -1 : dp[amount]);
    }
}
```

### Matrix Chain Multiplication (Interval DP)

**Problem:** Given N matrices, find the minimum number of scalar multiplications to compute their product. Matrix i has dimensions p[i-1] x p[i].

**C++:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n; cin >> n;
    vector<int> p(n+1); for (int& x : p) cin >> x;

    // dp[i][j] = min cost to multiply matrices i through j
    vector<vector<int>> dp(n, vector<int>(n, 0));

    for (int len = 2; len <= n; len++) { // chain length
        for (int i = 0; i <= n - len; i++) {
            int j = i + len - 1;
            dp[i][j] = INT_MAX;
            for (int k = i; k < j; k++) {
                int cost = dp[i][k] + dp[k+1][j] + p[i]*p[k+1]*p[j+1];
                dp[i][j] = min(dp[i][j], cost);
            }
        }
    }
    cout << dp[0][n-1] << endl;
}
```

**Time:** O(n^3). **Space:** O(n^2). Interval DP solves problems where the optimal substructure comes from splitting an interval at different points.

---

## Topic 4: Graph Algorithms

Graph problems appear consistently in Digital Advanced Coding. The core algorithms below cover the most common patterns.

### Dijkstra's Shortest Path (Weighted Graph)

**Problem:** Given a weighted undirected graph with N nodes and E edges, find the shortest distance from source S to all other nodes.

**Java (Priority Queue implementation):**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(), e = sc.nextInt(), src = sc.nextInt();

        List<int[]>[] adj = new List[n+1];
        for (int i = 1; i <= n; i++) adj[i] = new ArrayList<>();
        for (int i = 0; i < e; i++) {
            int u = sc.nextInt(), v = sc.nextInt(), w = sc.nextInt();
            adj[u].add(new int[]{v, w});
            adj[v].add(new int[]{u, w});
        }

        int[] dist = new int[n+1];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[src] = 0;

        PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> a[0] - b[0]);
        pq.offer(new int[]{0, src});

        while (!pq.isEmpty()) {
            int[] curr = pq.poll();
            int d = curr[0], u = curr[1];
            if (d > dist[u]) continue; // stale entry
            for (int[] edge : adj[u]) {
                int v = edge[0], w = edge[1];
                if (dist[u] + w < dist[v]) {
                    dist[v] = dist[u] + w;
                    pq.offer(new int[]{dist[v], v});
                }
            }
        }

        for (int i = 1; i <= n; i++)
            System.out.println("Node " + i + ": " + (dist[i] == Integer.MAX_VALUE ? -1 : dist[i]));
    }
}
```

**Time:** O((V + E) log V). **Space:** O(V + E). The key optimisation: skip stale priority queue entries with `if (d > dist[u]) continue`.

### Topological Sort (Kahn's Algorithm - BFS-based)

**Problem:** Given a directed acyclic graph (DAG), output a topological ordering of the nodes.

**C++:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, e; cin >> n >> e;
    vector<vector<int>> adj(n+1);
    vector<int> indegree(n+1, 0);

    for (int i = 0; i < e; i++) {
        int u, v; cin >> u >> v;
        adj[u].push_back(v);
        indegree[v]++;
    }

    queue<int> q;
    for (int i = 1; i <= n; i++)
        if (indegree[i] == 0) q.push(i);

    vector<int> order;
    while (!q.empty()) {
        int u = q.front(); q.pop();
        order.push_back(u);
        for (int v : adj[u])
            if (--indegree[v] == 0) q.push(v);
    }

    if ((int)order.size() != n) cout << "CYCLE DETECTED" << endl;
    else for (int x : order) cout << x << " ";
    cout << endl;
}
```

**Time:** O(V + E). **Space:** O(V + E). If the output order size is less than n, a cycle exists.

### Cycle Detection in Directed Graph (DFS-based)

**C++:**
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<vector<int>> adj;
vector<int> color; // 0=white, 1=gray, 2=black

bool dfs(int u) {
    color[u] = 1; // visiting
    for (int v : adj[u]) {
        if (color[v] == 1) return true; // back edge = cycle
        if (color[v] == 0 && dfs(v)) return true;
    }
    color[u] = 2; // fully processed
    return false;
}

int main() {
    int n, e; cin >> n >> e;
    adj.resize(n+1); color.assign(n+1, 0);
    for (int i = 0; i < e; i++) {
        int u, v; cin >> u >> v;
        adj[u].push_back(v);
    }
    bool hasCycle = false;
    for (int i = 1; i <= n; i++)
        if (color[i] == 0 && dfs(i)) { hasCycle = true; break; }

    cout << (hasCycle ? "Cycle detected" : "No cycle") << endl;
}
```

### Union-Find (Disjoint Set Union) for Connected Components

**C++:**
```cpp
#include <bits/stdc++.h>
using namespace std;

struct DSU {
    vector<int> parent, rank;
    DSU(int n) : parent(n+1), rank(n+1, 0) {
        iota(parent.begin(), parent.end(), 0);
    }
    int find(int x) {
        if (parent[x] != x) parent[x] = find(parent[x]); // path compression
        return parent[x];
    }
    bool unite(int x, int y) {
        int px = find(x), py = find(y);
        if (px == py) return false;
        if (rank[px] < rank[py]) swap(px, py);
        parent[py] = px;
        if (rank[px] == rank[py]) rank[px]++;
        return true;
    }
};

int main() {
    int n, e; cin >> n >> e;
    DSU dsu(n);
    for (int i = 0; i < e; i++) {
        int u, v; cin >> u >> v;
        dsu.unite(u, v);
    }
    // Count distinct components
    set<int> components;
    for (int i = 1; i <= n; i++) components.insert(dsu.find(i));
    cout << "Connected components: " << components.size() << endl;
}
```

**Time:** O(α(n)) per operation (nearly O(1) with path compression and union by rank). DSU is essential for problems involving network connectivity, Kruskal's MST, and grouping elements.

---

## Topic 5: Greedy Algorithms

Greedy algorithms make locally optimal choices at each step, hoping to reach a globally optimal solution. When greedy applies, it produces O(n log n) solutions where DP would require O(n^2) or worse.

### Activity Selection (Interval Scheduling)

Already covered in Article 16. The pattern: sort by finish time, greedily take the earliest-finishing non-conflicting activity. This maximises the count of non-overlapping activities.

### Fractional Knapsack

Unlike 0/1 knapsack, fractional knapsack allows taking fractions of items. The greedy solution: sort items by value-to-weight ratio (descending), take greedily.

**C++:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, W; cin >> n >> W;
    vector<pair<double,pair<int,int>>> items(n);
    for (int i = 0; i < n; i++) {
        int w, v; cin >> w >> v;
        items[i] = {(double)v/w, {w, v}};
    }
    sort(items.rbegin(), items.rend()); // descending by ratio

    double totalValue = 0;
    int remaining = W;
    for (auto& [ratio, wv] : items) {
        if (remaining <= 0) break;
        int w = wv.first, v = wv.second;
        int taken = min(w, remaining);
        totalValue += (double)taken * ratio;
        remaining -= taken;
    }
    cout << fixed << setprecision(2) << totalValue << endl;
}
```

**Time:** O(n log n) for sort. **Space:** O(n). Fractional knapsack has a greedy proof; 0/1 knapsack does not (requires DP).

### Jump Game II (Minimum Jumps)

**Problem:** Given an array where arr[i] is the maximum jump length from position i, find the minimum number of jumps to reach the last index. Assume you can always reach the last index.

**C++:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n; cin >> n;
    vector<int> a(n); for (int& x : a) cin >> x;

    int jumps = 0, curEnd = 0, farthest = 0;
    for (int i = 0; i < n-1; i++) {
        farthest = max(farthest, i + a[i]);
        if (i == curEnd) { // must jump
            jumps++;
            curEnd = farthest;
        }
    }
    cout << jumps << endl;
}
```

**Time:** O(n). **Space:** O(1). The greedy choice: at each step, extend the reachable range as far as possible, counting jumps only when the current range boundary is reached.

---

## Topic 6: Divide and Conquer

### Binary Search on Answer

This technique applies binary search not to find a value in an array, but to find the optimal answer in a monotonic solution space.

**Problem: Minimum Maximum Distance (Placing K Stations on a Line)**

Given N positions on a line and K stations to add, minimise the maximum distance between consecutive stations.

**C++ (Binary search on the answer):**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, k; cin >> n >> k;
    vector<double> pos(n);
    for (double& x : pos) cin >> x;
    sort(pos.begin(), pos.end());

    auto canPlace = [&](double maxDist) -> bool {
        int stationsNeeded = 0;
        for (int i = 1; i < n; i++)
            stationsNeeded += (int)ceil((pos[i] - pos[i-1]) / maxDist) - 1;
        return stationsNeeded <= k;
    };

    double lo = 0, hi = pos.back() - pos.front();
    for (int iter = 0; iter < 100; iter++) { // 100 iterations gives sufficient precision
        double mid = (lo + hi) / 2;
        if (canPlace(mid)) hi = mid;
        else lo = mid;
    }
    cout << fixed << setprecision(6) << hi << endl;
}
```

The pattern: define a `check(x)` function that returns true if x is a feasible answer, binary search over x. Works when "if x is feasible, so is anything larger (or smaller)" - monotonicity.

### Merge Sort Applications (Count Inversions)

**Problem:** Count inversions in an array - pairs (i,j) where i < j but arr[i] > arr[j].

**C++:**
```cpp
#include <bits/stdc++.h>
using namespace std;
long long mergeCount(vector<int>& arr, int l, int r) {
    if (l >= r) return 0;
    int mid = (l + r) / 2;
    long long cnt = mergeCount(arr, l, mid) + mergeCount(arr, mid+1, r);

    vector<int> merged;
    int i = l, j = mid+1;
    while (i <= mid && j <= r) {
        if (arr[i] <= arr[j]) { merged.push_back(arr[i++]); }
        else {
            cnt += mid - i + 1; // all remaining elements in left half form inversions with arr[j]
            merged.push_back(arr[j++]);
        }
    }
    while (i <= mid) merged.push_back(arr[i++]);
    while (j <= r) merged.push_back(arr[j++]);
    for (int k = l; k <= r; k++) arr[k] = merged[k-l];
    return cnt;
}

int main() {
    int n; cin >> n;
    vector<int> a(n); for (int& x : a) cin >> x;
    cout << mergeCount(a, 0, n-1) << endl;
}
```

**Time:** O(n log n). **Space:** O(n). The count inversions problem is a classic divide-and-conquer application that rewards candidates who see through the "counting" surface to the underlying merge sort structure.

---

## Topic 7: Bit Manipulation

Bit manipulation produces O(1) solutions to problems that would otherwise require loops or complex data structures.

### Essential Bit Operations

```cpp
x & (x-1)   // clears the lowest set bit of x; equals 0 iff x is a power of 2
x & (-x)    // isolates the lowest set bit of x
x ^ x       // equals 0 (XOR of a number with itself)
x ^ 0       // equals x (XOR with 0 is identity)
x >> k      // right shift by k (divide by 2^k)
x << k      // left shift by k (multiply by 2^k)
__builtin_popcount(x)  // C++ GCC: count set bits
Integer.bitCount(x)    // Java: count set bits
```

### Problem: Find the Single Non-Duplicate in an Array Where Every Other Appears Twice

**C++:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n; cin >> n;
    int xorSum = 0;
    for (int i = 0; i < n; i++) { int x; cin >> x; xorSum ^= x; }
    cout << xorSum << endl;
}
```

**Time:** O(n). **Space:** O(1). XOR is commutative and associative; a ^ a = 0; so all pairs cancel and the result is the single element.

### Problem: Count Set Bits in All Numbers From 1 to N

**Java:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int total = 0;
        for (int i = 1; i <= n; i++) total += Integer.bitCount(i);
        System.out.println(total);
    }
}
```

For competitive programming, a O(log n) mathematical solution exists but the O(n) loop is acceptable for moderate n.

### Subset Generation Using Bitmask

**Problem: Print all subsets of a set**

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n; cin >> n;
    vector<int> a(n); for (int& x : a) cin >> x;

    for (int mask = 0; mask < (1 << n); mask++) {
        cout << "{ ";
        for (int i = 0; i < n; i++)
            if (mask & (1 << i)) cout << a[i] << " ";
        cout << "}" << endl;
    }
}
```

Bitmask DP (DP over subsets) is a powerful technique for problems involving small sets (n <= 20). The state `dp[mask]` represents the optimal solution for the subset of elements indicated by `mask`.

---

## Topic 8: Number Theory

### Modular Arithmetic

When problems say "answer modulo 10^9+7," modular arithmetic is required to prevent overflow on large computations.

**Key rules:**
- `(a + b) % M = ((a % M) + (b % M)) % M`
- `(a * b) % M = ((a % M) * (b % M)) % M`
- `(a - b) % M = ((a % M) - (b % M) + M) % M` (add M to keep positive)
- Division: `(a / b) % M = (a * modInverse(b, M)) % M`

**Modular inverse (Fermat's little theorem, when M is prime):**
```cpp
long long power(long long base, long long exp, long long mod) {
    long long result = 1;
    base %= mod;
    while (exp > 0) {
        if (exp & 1) result = result * base % mod;
        base = base * base % mod;
        exp >>= 1;
    }
    return result;
}
long long modInverse(long long a, long long mod) {
    return power(a, mod - 2, mod); // Fermat: a^(p-1) = 1 (mod p)
}
```

### Combinatorics With Modular Arithmetic

**Precompute factorials and inverse factorials for nCr queries:**

```cpp
#include <bits/stdc++.h>
using namespace std;
const int MOD = 1e9+7, MAXN = 1e6+5;
long long fact[MAXN], inv_fact[MAXN];

long long power(long long b, long long e, long long m) {
    long long r = 1; b %= m;
    for (; e > 0; e >>= 1) { if (e&1) r = r*b%m; b = b*b%m; }
    return r;
}

void precompute() {
    fact[0] = 1;
    for (int i = 1; i < MAXN; i++) fact[i] = fact[i-1] * i % MOD;
    inv_fact[MAXN-1] = power(fact[MAXN-1], MOD-2, MOD);
    for (int i = MAXN-2; i >= 0; i--) inv_fact[i] = inv_fact[i+1] * (i+1) % MOD;
}

long long nCr(int n, int r) {
    if (r < 0 || r > n) return 0;
    return fact[n] % MOD * inv_fact[r] % MOD * inv_fact[n-r] % MOD;
}

int main() {
    precompute();
    int n, r; cin >> n >> r;
    cout << nCr(n, r) << endl;
}
```

**Why this matters for Digital:** Many combinatorics problems ask for answers modulo 10^9+7. Without precomputed factorials and modular inverses, each nCr query takes O(r) time; with precomputation, each query is O(1).

---

## Topic 9: Advanced Data Structures

### Segment Tree (Range Query and Point Update)

**Problem:** Given an array of N integers, support two operations: update a single element, and query the sum over a range [l, r]. Both in O(log n).

**C++:**
```cpp
#include <bits/stdc++.h>
using namespace std;
const int MAXN = 1e5+5;
long long tree[4*MAXN];

void build(vector<int>& arr, int node, int start, int end) {
    if (start == end) tree[node] = arr[start];
    else {
        int mid = (start+end)/2;
        build(arr, 2*node, start, mid);
        build(arr, 2*node+1, mid+1, end);
        tree[node] = tree[2*node] + tree[2*node+1];
    }
}

void update(int node, int start, int end, int idx, int val) {
    if (start == end) tree[node] = val;
    else {
        int mid = (start+end)/2;
        if (idx <= mid) update(2*node, start, mid, idx, val);
        else update(2*node+1, mid+1, end, idx, val);
        tree[node] = tree[2*node] + tree[2*node+1];
    }
}

long long query(int node, int start, int end, int l, int r) {
    if (r < start || end < l) return 0;
    if (l <= start && end <= r) return tree[node];
    int mid = (start+end)/2;
    return query(2*node, start, mid, l, r) + query(2*node+1, mid+1, end, l, r);
}

int main() {
    int n; cin >> n;
    vector<int> arr(n+1); for (int i = 1; i <= n; i++) cin >> arr[i];
    build(arr, 1, 1, n);

    int q; cin >> q;
    while (q--) {
        int type, a, b; cin >> type >> a >> b;
        if (type == 1) update(1, 1, n, a, b);
        else cout << query(1, 1, n, a, b) << "\n";
    }
}
```

**Time:** O(log n) per query and update. O(n) build. Segment trees are used for problems requiring both range queries and point updates - sorting-based alternatives cannot handle updates efficiently.

---

## Difficulty Comparison and Preparation Calibration

### How Digital Coding Maps to Competitive Programming Platforms

Understanding the difficulty mapping helps you select appropriate practice material:

**LeetCode:** Digital Problem 1 = LeetCode Medium (difficulty score 1400-1800). Digital Problem 2 = LeetCode Hard (difficulty score 1800-2200). Practice target: solve 50+ Medium problems fluently before starting Hard problems. Aim for 15-20 Hard problems solved by test day.

**CodeChef:** Digital Problem 1 = Division 3 or upper Division 2 range. Digital Problem 2 = Division 2 to lower Division 1 range. Competitive programmers rated 1200-1500 on CodeChef are in the right range for Digital Problem 1; 1500-1800 rating is the target for Problem 2.

**Codeforces:** Digital Problem 1 corresponds to Codeforces problems rated 1200-1600. Digital Problem 2 corresponds to rated 1600-2000.

**HackerRank:** Digital Problem 1 corresponds to HackerRank Hard. HackerRank Expert corresponds to Digital Problem 2.

### What Distinguishes Digital-Ready Candidates

Beyond topic knowledge, Digital-ready candidates share three characteristics:

**Pattern recognition speed.** They identify the algorithm category within 2-3 minutes of reading a problem. "This is a graph connectivity problem" or "this needs DP with state = (position, count)" comes quickly from pattern exposure rather than on-the-spot invention.

**Clean implementation under pressure.** They can implement merge sort, BFS, Kadane's, and Dijkstra's from memory without reference material, in under 10 minutes each, with correct edge case handling.

**Partial solution strategy.** When the optimal solution is not immediately apparent, they write a correct brute-force solution first, submit it for partial credit, and then optimise. They do not spend 45 minutes trying to develop the optimal solution from scratch with nothing submitted.

---

## 45-Day Preparation Roadmap: Zero to Digital-Ready

This roadmap assumes 2-3 hours of focused daily practice. Adjust the pace based on your starting point but do not skip topics - each builds on the previous.

### Days 1-5: Foundation Review

Before touching competitive programming, verify that you can write the following from memory in under 10 minutes each: sorting (merge sort and quick sort), binary search (standard and first-occurrence variant), BFS and DFS on a graph, HashMap-based frequency count, and basic DP (Fibonacci with memoisation).

If any of these takes more than 10 minutes, spend the first five days exclusively on them. They are prerequisites for everything that follows.

### Days 6-10: Arrays and Two-Pointer Mastery

Topics: Prefix sums, sliding window (fixed and variable), two-pointer for sorted arrays and pairs, Dutch National Flag.

Daily target: 3 LeetCode Medium problems from the "Array" and "Two Pointers" categories. Track your time per problem. Target: under 25 minutes for Medium by Day 10.

### Days 11-15: String Algorithms

Topics: KMP algorithm implementation, string hashing basics, palindrome problems (expand around center, Manacher's algorithm concepts), anagram and permutation problems.

Daily target: 2 LeetCode Medium string problems + KMP and hashing implementation from scratch (no reference).

### Days 16-22: Dynamic Programming (The Heaviest Week)

Topics: 1D DP (LIS, coin change, house robber), 2D DP (LCS, edit distance, grid paths), knapsack (0/1 and unbounded), interval DP (matrix chain), DP with bitmask (travelling salesman on small n).

Daily target: 2 DP problems per day. Start with LeetCode Medium DP (70% of your time) and attempt 1 Hard DP problem per day (30%). Write each solution from scratch after understanding the approach - do not look at solutions while coding.

### Days 23-27: Graph Algorithms

Topics: BFS/DFS (connected components, bipartite check, cycle detection), Dijkstra (weighted shortest path), Bellman-Ford (negative weights), topological sort (Kahn's and DFS), Union-Find (connected components, Kruskal's MST concept).

Daily target: 3 LeetCode Medium graph problems. Implement Dijkstra and topological sort from memory by the end of this block.

### Days 28-32: Greedy and Divide & Conquer

Topics: Interval scheduling, fractional knapsack, greedy approaches to minimum spanning trees (Prim's concept), binary search on answer, merge sort applications (count inversions), quick select.

Daily target: 2 problems per day. Focus on recognising when greedy applies vs when DP is required - this distinction is frequently tested.

### Days 33-36: Bit Manipulation and Number Theory

Topics: Bit tricks (power of 2 check, lowest set bit, XOR properties), subset generation with bitmask, modular arithmetic (operations, fast exponentiation, modular inverse), Sieve of Eratosthenes, Euler's totient function basics, combinatorics with precomputed factorials.

Daily target: 1 bit manipulation problem + 1 number theory problem per day. Focus on implementation accuracy for modular arithmetic chains.

### Days 37-40: Advanced Data Structures

Topics: Segment tree (range sum/min/max queries + point updates), Binary Indexed Tree / Fenwick Tree (simpler implementation for range sum queries), Trie (prefix problems), basic concepts of sparse tables (range minimum query).

Daily target: Implement a segment tree and a BIT from scratch. Solve 2 problems requiring each structure.

### Days 41-43: Mock Tests and Pattern Recognition

Take three full timed mock tests of 90 minutes each, simulating the Digital coding environment:
- Two problems, 90 minutes
- No reference material
- Implement your solution, test mentally, submit

After each mock, analyse: which topic did the problems test? How long did pattern recognition take? Where did implementation bugs occur? What edge cases did you miss?

This analysis is more valuable than the score itself. Fix the specific gaps revealed by each mock before the next one.

### Days 44-45: Final Review and Mental Preparation

Day 44: Review your weakest implementations from the roadmap. Re-write KMP, Dijkstra, and your DP base cases one more time from memory. These are most commonly needed.

Day 45: No heavy new coding. Verify your test environment setup (for remote tests). Review input-output patterns for your primary language. Sleep well. Trust the preparation.

---

## Common Mistakes in TCS Digital Coding Rounds

**Integer overflow in C++.** Using `int` for computations that require `long long`. Classic trap: `int a = 1e9; int b = 1e9; cout << a * b;` overflows silently. Use `long long` for any product that might exceed 2 billion.

**Off-by-one errors in segment trees.** Indexing mismatches between 0-indexed arrays and 1-indexed segment trees cause subtly wrong outputs. Decide on one indexing convention and apply it consistently.

**Not handling disconnected graphs.** BFS/DFS from a single source misses nodes not reachable from that source. For problems asking about all connected components, loop over all unvisited nodes.

**Greedy vs DP confusion.** A common mistake is applying greedy to a problem that requires DP (because the greedy choice at each step does not lead to a globally optimal solution). Before committing to greedy, verify that the exchange argument holds: swapping any locally suboptimal choice for the greedy choice never makes the solution worse.

**Not submitting a partial solution.** Spending the full 90 minutes attempting to develop an optimal solution and submitting nothing is worse than submitting a correct brute-force that passes half the test cases. Always submit something before working on optimisation.

**Forgetting to read output format.** Problems specify exact output format. Missing newlines, extra spaces, or wrong precision on decimal outputs fail test cases that the logic handles correctly.

---

## Topic 10: Additional DP Patterns

### Digit DP (Count Numbers With a Property in a Range)

Digit DP solves problems like "count integers from L to R satisfying property P" efficiently by building numbers digit by digit.

**Problem: Count numbers from 1 to N that do not contain the digit 4.**

**C++:**
```cpp
#include <bits/stdc++.h>
using namespace std;

string num;
int dp[12][2]; // dp[pos][tight]

int solve(int pos, bool tight, bool started) {
    if (pos == (int)num.size()) return started ? 1 : 0;

    if (dp[pos][tight] != -1) return dp[pos][tight];

    int limit = tight ? (num[pos] - '0') : 9;
    int ans = 0;

    for (int d = 0; d <= limit; d++) {
        if (d == 4) continue; // skip digit 4
        ans += solve(pos + 1, tight && (d == limit), started || d > 0);
    }

    return dp[pos][tight] = ans;
}

int countWithout4(int n) {
    num = to_string(n);
    memset(dp, -1, sizeof(dp));
    return solve(0, true, false);
}

int main() {
    int n; cin >> n;
    cout << countWithout4(n) << endl;
}
```

**Why TCS tests it:** Digit DP generalises to many constraint-based counting problems. Understanding the `tight` flag - which tracks whether we are still constrained to the upper bound at the current digit position - is the key insight.

### DP on Trees

**Problem: Diameter of a Binary Tree (longest path between any two nodes)**

The diameter may or may not pass through the root. At each node, compute the diameter as the sum of the heights of its two longest subtrees.

**Java:**
```java
import java.util.*;
public class Main {
    static int maxDia = 0;

    public static void main(String[] args) {
        // For this example, tree represented as adjacency list (general tree)
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        List<List<Integer>> adj = new ArrayList<>();
        for (int i = 0; i <= n; i++) adj.add(new ArrayList<>());
        for (int i = 0; i < n-1; i++) {
            int u = sc.nextInt(), v = sc.nextInt();
            adj.get(u).add(v); adj.get(v).add(u);
        }
        dfs(1, -1, adj);
        System.out.println(maxDia);
    }

    static int dfs(int u, int parent, List<List<Integer>> adj) {
        int first = 0, second = 0; // two longest child subtree heights
        for (int v : adj.get(u)) {
            if (v == parent) continue;
            int h = dfs(v, u, adj);
            if (h > first) { second = first; first = h; }
            else if (h > second) second = h;
        }
        maxDia = Math.max(maxDia, first + second);
        return first + 1;
    }
}
```

**Time:** O(n). **Space:** O(n) recursion stack. DP on trees passes information both upward (return value) and updates global state (maxDia) during the traversal.

---

## Topic 11: Advanced Graph Problems

### Shortest Path in a Graph With Constraints (Modified Dijkstra)

**Problem: Shortest path from S to T with at most K stops (airline routing style)**

Standard Dijkstra does not handle "at most K intermediate nodes" directly. Modified Bellman-Ford or modified Dijkstra with state (node, stops_used) works.

**Java (BFS/Bellman-Ford variant):**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(), e = sc.nextInt(), src = sc.nextInt(), dst = sc.nextInt(), k = sc.nextInt();

        int[][] edges = new int[e][3];
        for (int i = 0; i < e; i++) {
            edges[i][0] = sc.nextInt();
            edges[i][1] = sc.nextInt();
            edges[i][2] = sc.nextInt();
        }

        int[] dist = new int[n+1];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[src] = 0;

        for (int i = 0; i <= k; i++) { // k+1 relaxations = at most k stops
            int[] temp = dist.clone();
            for (int[] edge : edges) {
                int u = edge[0], v = edge[1], w = edge[2];
                if (dist[u] != Integer.MAX_VALUE && dist[u] + w < temp[v]) {
                    temp[v] = dist[u] + w;
                }
            }
            dist = temp;
        }
        System.out.println(dist[dst] == Integer.MAX_VALUE ? -1 : dist[dst]);
    }
}
```

### Bipartite Graph Check

**Problem: Determine if a graph is bipartite (2-colorable)**

**C++:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, e; cin >> n >> e;
    vector<vector<int>> adj(n+1);
    for (int i = 0; i < e; i++) {
        int u, v; cin >> u >> v;
        adj[u].push_back(v); adj[v].push_back(u);
    }

    vector<int> color(n+1, -1);
    bool bipartite = true;

    for (int start = 1; start <= n && bipartite; start++) {
        if (color[start] != -1) continue;
        queue<int> q;
        q.push(start); color[start] = 0;
        while (!q.empty() && bipartite) {
            int u = q.front(); q.pop();
            for (int v : adj[u]) {
                if (color[v] == -1) { color[v] = 1 - color[u]; q.push(v); }
                else if (color[v] == color[u]) bipartite = false;
            }
        }
    }
    cout << (bipartite ? "BIPARTITE" : "NOT BIPARTITE") << endl;
}
```

---

## Topic 12: Trie and Advanced String Structures

### Trie Implementation for Prefix Problems

**Problem: Given a list of words and a list of queries, for each query check how many words in the list start with the given prefix.**

**C++:**
```cpp
#include <bits/stdc++.h>
using namespace std;

struct TrieNode {
    map<char, TrieNode*> children;
    int count = 0; // number of words passing through this node
};

struct Trie {
    TrieNode* root = new TrieNode();

    void insert(const string& word) {
        TrieNode* cur = root;
        for (char c : word) {
            if (!cur->children.count(c)) cur->children[c] = new TrieNode();
            cur = cur->children[c];
            cur->count++;
        }
    }

    int prefixCount(const string& prefix) {
        TrieNode* cur = root;
        for (char c : prefix) {
            if (!cur->children.count(c)) return 0;
            cur = cur->children[c];
        }
        return cur->count;
    }
};

int main() {
    int n; cin >> n;
    Trie trie;
    for (int i = 0; i < n; i++) { string w; cin >> w; trie.insert(w); }

    int q; cin >> q;
    while (q--) { string prefix; cin >> prefix; cout << trie.prefixCount(prefix) << "\n"; }
}
```

**Time:** O(L) per insert and query where L = word length. **Space:** O(total characters). Tries are used when prefix matching queries need to be answered efficiently over a large dictionary.

---

## Full Problem Set: Digital-Level Practice Problems

The following problems are at Digital coding difficulty. Attempt each with a 25-minute time limit before reading the solution approach.

### Problem D1: Minimum Cost to Reach Destination

**Statement:** A robot starts at cell (0,0) in a grid of N x M cells. Each cell has a cost. The robot can move right or down. Find the minimum total cost path to reach (N-1, M-1).

**Approach:** 2D DP. `dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])`

**Java:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(), m = sc.nextInt();
        int[][] grid = new int[n][m];
        for (int i = 0; i < n; i++) for (int j = 0; j < m; j++) grid[i][j] = sc.nextInt();

        int[][] dp = new int[n][m];
        dp[0][0] = grid[0][0];
        for (int i = 1; i < n; i++) dp[i][0] = dp[i-1][0] + grid[i][0];
        for (int j = 1; j < m; j++) dp[0][j] = dp[0][j-1] + grid[0][j];

        for (int i = 1; i < n; i++)
            for (int j = 1; j < m; j++)
                dp[i][j] = grid[i][j] + Math.min(dp[i-1][j], dp[i][j-1]);

        System.out.println(dp[n-1][m-1]);
    }
}
```

**Time:** O(n x m). **Space:** O(n x m), reducible to O(m) with rolling array.

### Problem D2: Longest Palindromic Substring

**Statement:** Given a string, find the length of its longest palindromic substring.

**Approach:** Expand around center. For each index i (and each pair i, i+1 for even-length palindromes), expand outward while characters match.

**C++:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int expandAroundCenter(const string& s, int l, int r) {
    while (l >= 0 && r < (int)s.size() && s[l] == s[r]) { l--; r++; }
    return r - l - 1; // length of palindrome
}

int main() {
    string s; cin >> s;
    int maxLen = 1;
    for (int i = 0; i < (int)s.size(); i++) {
        maxLen = max(maxLen, expandAroundCenter(s, i, i));   // odd
        maxLen = max(maxLen, expandAroundCenter(s, i, i+1)); // even
    }
    cout << maxLen << endl;
}
```

**Time:** O(n^2). **Space:** O(1). For O(n) time, Manacher's algorithm is the advanced solution.

### Problem D3: Number of Islands (Grid DFS/BFS)

**Statement:** Given a 2D grid of '1's (land) and '0's (water), count the number of islands. An island is surrounded by water and formed by connecting adjacent land cells horizontally or vertically.

**Java:**
```java
import java.util.*;
public class Main {
    static char[][] grid;
    static int n, m;

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        n = sc.nextInt(); m = sc.nextInt();
        grid = new char[n][m];
        for (int i = 0; i < n; i++) {
            String row = sc.next();
            for (int j = 0; j < m; j++) grid[i][j] = row.charAt(j);
        }

        int count = 0;
        for (int i = 0; i < n; i++)
            for (int j = 0; j < m; j++)
                if (grid[i][j] == '1') { dfs(i, j); count++; }

        System.out.println(count);
    }

    static void dfs(int r, int c) {
        if (r < 0 || r >= n || c < 0 || c >= m || grid[r][c] != '1') return;
        grid[r][c] = '0'; // mark visited
        dfs(r+1, c); dfs(r-1, c); dfs(r, c+1); dfs(r, c-1);
    }
}
```

**Time:** O(n x m). **Space:** O(n x m) recursion stack in worst case.

### Problem D4: Maximum Points on a Line

**Statement:** Given N points in a 2D plane, find the maximum number of points that lie on the same straight line.

**Approach:** For each pair of points, compute the slope. Use a HashMap to count how many points share the same slope from a reference point.

**Java:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] x = new int[n], y = new int[n];
        for (int i = 0; i < n; i++) { x[i] = sc.nextInt(); y[i] = sc.nextInt(); }

        if (n <= 2) { System.out.println(n); return; }

        int maxPoints = 2;
        for (int i = 0; i < n; i++) {
            Map<String, Integer> slopeCount = new HashMap<>();
            int duplicates = 0, localMax = 0;

            for (int j = i+1; j < n; j++) {
                int dx = x[j] - x[i], dy = y[j] - y[i];
                if (dx == 0 && dy == 0) { duplicates++; continue; }
                int g = gcd(Math.abs(dx), Math.abs(dy));
                dx /= g; dy /= g;
                // Normalise sign
                if (dx < 0 || (dx == 0 && dy < 0)) { dx = -dx; dy = -dy; }
                String key = dx + "," + dy;
                slopeCount.put(key, slopeCount.getOrDefault(key, 0) + 1);
                localMax = Math.max(localMax, slopeCount.get(key));
            }
            maxPoints = Math.max(maxPoints, localMax + duplicates + 1);
        }
        System.out.println(maxPoints);
    }

    static int gcd(int a, int b) { return b == 0 ? a : gcd(b, a % b); }
}
```

**Time:** O(n^2). **Space:** O(n). Representing slope as a normalised (dx, dy) fraction rather than a floating-point ratio avoids precision errors that would make the HashMap comparisons unreliable.

---

## Frequently Asked Questions: TCS Digital Advanced Coding

**How many problems appear in the Digital Advanced Coding section?**
Typically 2 problems in the standard Digital coding round, with some administrations including a third problem for Prime profile differentiation. Budget approximately 30-35 minutes for Problem 1 and 45-50 minutes for Problem 2, with remaining time for review and optimisation.

**Should I use C++ or Java for Digital coding?**
C++ is the competitive programming standard and has a slight speed advantage due to its faster I/O and compiled performance. If you are equally comfortable in both, choose C++. If you are significantly more fluent in Java, stay with Java - a fluent Java solution is better than a buggy C++ solution. Python is not recommended for Digital level due to time limit constraints.

**What if I cannot solve a problem completely? Should I still submit?**
Always submit your best attempt, even if it is a brute-force solution or handles only simple cases. Partial test case credit is real marks. A brute-force that passes 4 of 10 test cases is better than an unsubmitted optimal solution. Submit early, then improve.

**Is Digital profile guaranteed if I solve both problems fully?**
Full correct solutions to both problems strongly correlate with Digital profile assignment, but TCS considers the full test performance including Foundation sections. A candidate with strong coding and weak Foundation aptitude may receive Ninja rather than Digital. The strongest Digital candidates perform well across all sections.

**How does TCS Prime differ from Digital in the coding section?**
Prime candidates are expected to demonstrate performance on the hardest problems in the coding section and exceptional performance in Advanced Quantitative and Reasoning. In test administrations that include a third coding problem, strong performance on that problem signals Prime-level candidacy. Prime is a small percentage of total offers.

**What is the relationship between preparing for Digital coding and preparing for competitive programming more broadly?**
They are substantially the same activity. Digital coding preparation using LeetCode Medium/Hard and CodeChef Division 2 problems is identical to building competitive programming skill. The difference: competitive programming is an ongoing pursuit that continues after placement. Many TCS Digital hires continue competitive programming and participate in CodeVita, Codeforces rounds, and ICPC. The preparation for placement coding is the foundation for a competitive programming hobby or career skill.

**Can I use STL in C++ on TCS iON?**
Yes. The C++ environment on TCS iON supports the full STL. `#include <bits/stdc++.h>` (the competitive programming shorthand that includes everything) may or may not be supported - if in doubt, include the specific headers you need: `<vector>`, `<map>`, `<queue>`, `<algorithm>`, `<set>`, `<unordered_map>`, `<stack>`.

**Is there a penalty for submitting wrong solutions?**
No. TCS iON does not apply a time penalty or score deduction for incorrect submissions. You are scored on your best submission across all attempts. Submit frequently - every time you improve your solution.

**How much time should I spend on Digital coding preparation relative to other NQT/ITP sections?**
If your target is Digital profile, Advanced Coding deserves the majority of your technical preparation time - approximately 60-70% of it. Foundation aptitude requires solid preparation but responds quickly to focused review (1-2 weeks). Coding improvement at Digital level requires sustained practice over 4-6 weeks minimum. Start coding preparation early.

**What should I do the week before my TCS Digital test?**
Take at least two 90-minute full-length coding mock tests under exam conditions. Review your solutions from the 45-day roadmap one final time - particularly the implementations you find hardest to reproduce from memory. Verify your environment setup (for remote tests). Do not attempt heavy new algorithm learning in the final week - consolidate what you have built rather than adding topics you cannot yet implement correctly under pressure.

---

## The Competitive Programming Mindset

Technical knowledge accounts for about 60% of competitive coding performance. The other 40% is mindset and process. These principles, borrowed from the competitive programming community, apply directly to TCS Digital coding.

**Read the problem three times.** Once for the narrative, once for the constraints (n = 10^5 tells you you need O(n log n) or better), once for the exact output format. Most wrong answers stem from misreading a constraint or output requirement.

**Solve on paper before coding.** Before writing a single line of code, verify your approach with a small example. If the example does not produce the expected output, your approach is wrong. Discovering this on paper takes two minutes; discovering it after 20 minutes of coding is demoralising.

**Test all edge cases before submitting.** Empty input, single element, all identical elements, minimum and maximum values, and the examples given in the problem. A solution that fails on n=1 when n can be 1 loses marks that should have been easy.

**Time yourself honestly.** Competitive coding speed improves with explicit time tracking. Knowing that you solved a particular LeetCode Medium in 22 minutes and aiming to bring it to 18 minutes over the next week creates a concrete improvement target. Speed is a skill, not a fixed attribute.

**Celebrate partial solutions.** In competitive programming culture, getting 7 of 10 test cases on a hard problem is a good result. Internalise this. A candidate who submits something that passes 7 of 10 cases is ahead of one who submits nothing. Progress in competitive coding is measured in test cases passed, not in perfect solutions.

---

## TCS CodeVita and Its Relationship to Digital Profile

TCS CodeVita is one of the largest coding competitions in the world by participant count. Understanding how it connects to Digital profile selection is valuable both for strategy and for motivation.

### What CodeVita Tests

CodeVita problems are problem-solving challenges that require competitive programming knowledge. The competition runs in multiple rounds:

**Zone Round:** Entry-level round. Problems range from LeetCode Easy to LeetCode Hard. Candidates are judged on the number of problems solved and execution time. Thousands of candidates participate.

**Grand Finale:** Top performers from zone rounds compete globally. Problems here are genuinely difficult - Codeforces Div 1 difficulty and above. This round identifies world-class programming talent.

The zone round difficulty profile is almost identical to TCS Digital Advanced Coding. This is not coincidental - TCS uses CodeVita to identify the same technical profile that the Digital coding section targets through the NQT/ITP process.

### How CodeVita Performance Feeds Into Hiring

Strong CodeVita performers are shortlisted for TCS Digital and Prime profiles independently of the NQT/ITP process in some hiring cycles. Candidates who rank in the top percentiles of their zone are sometimes contacted directly for Digital profile offers. This makes CodeVita participation a genuine strategic opportunity for candidates who perform better in competition settings than in timed aptitude tests.

Even without direct shortlisting, CodeVita participation is a signal in the TCS Technical Interview. "I participated in CodeVita and reached [round/rank]" is a concrete technical achievement that interviewers view positively. It demonstrates that your competitive coding experience extends beyond placement preparation to genuine engagement with the field.

### Preparing for CodeVita vs Preparing for Digital Coding

The preparation is essentially the same, with one difference in emphasis:

CodeVita zone rounds tend to feature more mathematically oriented problems (combinatorics, number theory, geometry) than the standard Digital coding section. If you are specifically targeting CodeVita alongside Digital, ensure your number theory preparation includes: Euler's totient function, Chinese Remainder Theorem basics, and extended Euclidean algorithm. These appear in CodeVita problems more frequently than in the standard Digital coding round.

---

## C++ STL Reference for Competitive Programming

Having these STL structures and their operations memorised eliminates the need to think about implementation details during the exam.

### Containers

```cpp
vector<int> v;           // dynamic array
v.push_back(x);          // O(1) amortised
v.pop_back();            // O(1)
v.size();                // O(1)
sort(v.begin(), v.end()); // O(n log n)
reverse(v.begin(), v.end()); // O(n)

set<int> s;              // sorted unique elements, O(log n) operations
s.insert(x);
s.count(x);              // 1 if present, 0 if not
s.erase(x);
s.lower_bound(x);        // iterator to first element >= x

map<int,int> m;          // sorted key-value pairs, O(log n) operations
m[key] = val;
m.count(key);
m.find(key);             // returns end() if not found

unordered_map<int,int> um; // O(1) average, O(n) worst case
unordered_set<int> us;

priority_queue<int> maxPQ;    // max-heap by default
priority_queue<int, vector<int>, greater<int>> minPQ; // min-heap

deque<int> dq;           // double-ended queue
dq.push_front(x); dq.push_back(x);
dq.pop_front(); dq.pop_back();

stack<int> stk;
stk.push(x); stk.top(); stk.pop();

queue<int> q;
q.push(x); q.front(); q.pop();
```

### Algorithm Functions

```cpp
sort(a, a+n);                    // sort array
sort(v.begin(), v.end());        // sort vector
sort(v.begin(), v.end(), greater<int>()); // descending
lower_bound(a, a+n, x);         // first element >= x (requires sorted)
upper_bound(a, a+n, x);         // first element > x (requires sorted)
max_element(v.begin(), v.end());
min_element(v.begin(), v.end());
accumulate(v.begin(), v.end(), 0LL); // sum (use 0LL for long long)
unique(v.begin(), v.end());      // remove consecutive duplicates (sort first)
next_permutation(v.begin(), v.end()); // generate next permutation
__gcd(a, b);                     // GCD (C++14+)
__builtin_popcount(x);           // count set bits in int
__builtin_popcountll(x);        // count set bits in long long
```

### Fast I/O for C++

For problems with large input, standard `cin/cout` can be slow. Add these two lines at the start of main:

```cpp
ios_base::sync_with_stdio(false);
cin.tie(NULL);
```

This decouples C++ streams from C streams (removing synchronisation overhead) and unties cin from cout (removing the automatic flush before each cin call). Combined, these make `cin/cout` nearly as fast as `scanf/printf`.

---

## Java Competitive Programming Reference

### Fast I/O in Java

```java
BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
PrintWriter pw = new PrintWriter(new BufferedWriter(new OutputStreamWriter(System.out)));

int n = Integer.parseInt(br.readLine().trim());
StringTokenizer st = new StringTokenizer(br.readLine());
int a = Integer.parseInt(st.nextToken());
int b = Integer.parseInt(st.nextToken());

pw.println(answer);
pw.flush(); // critical
```

### Java Equivalents of Common C++ Competitive Programming Operations

| C++ | Java |
|---|---|
| `__builtin_popcount(x)` | `Integer.bitCount(x)` |
| `__gcd(a, b)` | No built-in; implement with `while (b != 0) { int t = b; b = a%b; a = t; }` |
| `lower_bound` | `Collections.binarySearch()` or `Arrays.binarySearch()` with custom logic |
| `priority_queue` (min-heap) | `new PriorityQueue<>()` (Java's default is min-heap) |
| `priority_queue` (max-heap) | `new PriorityQueue<>(Collections.reverseOrder())` |
| `map` (sorted) | `TreeMap<>()` |
| `unordered_map` | `HashMap<>()` |
| `set` (sorted) | `TreeSet<>()` |
| `unordered_set` | `HashSet<>()` |
| `vector<pair<int,int>>` | `int[][] arr` or `List<int[]>` |
| `pair<int,int>` | `int[]` of size 2, or `Map.Entry<Integer,Integer>` |

---

## Building Your Competitive Programming Environment

Setting up an efficient local coding environment before the test period helps you practice in realistic conditions.

### Local Setup for C++

Install a C++ compiler (GCC via MinGW on Windows, or g++ on Linux/Mac) and a code editor (VS Code with C++ extensions). For competitive programming, most practitioners use a single template file that includes all standard headers and common shortcuts. A minimal template:

```cpp
#include <bits/stdc++.h>
using namespace std;
typedef long long ll;
typedef pair<int,int> pii;
typedef vector<int> vi;
#define all(x) x.begin(), x.end()
#define pb push_back

int main(){
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    // your solution here
}
```

Practise with this template until using it is automatic. The type aliases (`ll` for `long long`, `pii` for `pair<int,int>`) and the `all()` macro reduce repetitive typing without making code less readable.

### Local Setup for Java

Use IntelliJ IDEA (or VSCode with Java extension) with a template class:

```java
import java.util.*;
import java.io.*;

public class Solution {
    static BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
    static PrintWriter pw = new PrintWriter(new BufferedWriter(new OutputStreamWriter(System.out)));

    public static void main(String[] args) throws IOException {
        // your solution here
        pw.flush();
    }
}
```

### Building Your Problem Log

Competitive programmers who improve fastest maintain a problem log: a document or spreadsheet tracking every problem attempted, the category, the approach used, the time taken, and whether it was solved correctly on first attempt. After each practice session, add the problems worked. Review your log weekly to identify recurring blind spots.

Patterns you are looking for in your log:
- Are there categories where you consistently time out (approach knowledge gap)?
- Are there categories where your approach is right but implementation has bugs (implementation practice needed)?
- Are you improving on time-per-problem in the categories you have been practising?

The log transforms practice from an undirected activity into a measured improvement process.

---

## Final Checklist Before Your TCS Digital Coding Round

**One week before:**
- Implement from memory: BFS, DFS, Dijkstra, merge sort, binary search (first occurrence), Kadane's algorithm, KMP LPS array, 0/1 knapsack (both DP formulations), segment tree query and update
- Take one full 90-minute mock test under exam conditions
- Verify your primary language's fast I/O setup

**Day before:**
- Light review of your most recent mock test errors
- No heavy new algorithm learning
- Confirm your test environment setup (remote test: webcam, internet, system check)
- Sleep well

**During the test:**
- Read both problems in the first 3 minutes before starting to code
- Start with the problem you are more confident about (often Problem 1)
- Write a brute-force for Problem 1 and submit within 20 minutes
- Optimise if needed while Problem 1 partial credit is secured
- Spend remaining time on Problem 2 with the same strategy: brute-force first, optimise second
- Submit before the time limit - never have an unsubmitted solution when time expires

The TCS Digital profile is within reach for any candidate who commits to the 45-day roadmap and maintains the practice discipline it requires. The algorithms are learnable. The implementation skill is buildable. The competitive mindset is trainable. What separates Digital hires from Ninja hires is not innate talent - it is the decision to prepare for a harder standard, and the consistency to follow through on it.

---

## Worked Walkthrough: Approaching a Digital-Level Problem From Scratch

The following walkthrough demonstrates the complete problem-solving process a Digital-ready candidate uses, from reading the problem to a submitted solution.

### Problem: Maximum Profit With at Most K Transactions (Stock Trading DP)

**Statement:** You are given an array of stock prices where prices[i] is the price on day i. You may complete at most K transactions (buy then sell). Find the maximum profit. You cannot hold more than one stock at a time (must sell before buying again).

**Step 1: Understand the problem (2 minutes)**

Read carefully. Key constraints: at most K transactions, one stock at a time. This is an optimisation problem over a sequence where decisions interact (buying today affects what you can do tomorrow). That combination - optimisation + sequence + interacting decisions - screams DP.

**Step 2: Define the state (2 minutes)**

What varies? The day we are on, and how many transactions we have completed so far. Do we currently hold a stock?

State: `dp[k][0]` = max profit using at most k transactions, not currently holding stock
       `dp[k][1]` = max profit using at most k transactions, currently holding stock

**Step 3: Define the recurrence (3 minutes)**

On day i, if we are not holding stock:
- We could have done nothing: `dp[k][0]` stays same
- We could sell today: `dp[k][1] + prices[i]`

If we are holding stock:
- We could have done nothing: `dp[k][1]` stays same
- We could buy today (starts a new transaction): `dp[k-1][0] - prices[i]`

Base case: `dp[0][0] = 0` (no transactions, no stock, no profit), `dp[k][1] initially = -infinity` (have not bought yet).

**Step 4: Code it (15 minutes)**

**Java:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(), k = sc.nextInt();
        int[] prices = new int[n];
        for (int i = 0; i < n; i++) prices[i] = sc.nextInt();

        // Edge case: if k >= n/2, we can make as many transactions as we want
        if (k >= n / 2) {
            int profit = 0;
            for (int i = 1; i < n; i++)
                if (prices[i] > prices[i-1]) profit += prices[i] - prices[i-1];
            System.out.println(profit);
            return;
        }

        // dp[j][0] = max profit with at most j transactions, not holding
        // dp[j][1] = max profit with at most j transactions, holding
        int[][] dp = new int[k+1][2];
        for (int j = 0; j <= k; j++) dp[j][1] = Integer.MIN_VALUE / 2; // -infinity

        for (int i = 0; i < n; i++) {
            for (int j = k; j >= 1; j--) {
                dp[j][0] = Math.max(dp[j][0], dp[j][1] + prices[i]); // sell
                dp[j][1] = Math.max(dp[j][1], dp[j-1][0] - prices[i]); // buy
            }
        }

        System.out.println(dp[k][0]);
    }
}
```

**Step 5: Test against the example (3 minutes)**

prices = [3, 2, 6, 5, 0, 3], k = 2.
Expected output: 7 (buy at 2, sell at 6, profit 4; buy at 0, sell at 3, profit 3; total 7).

Trace the DP for day 1 (price=2): dp[1][1] = max(-inf, dp[0][0] - 2) = -2. Day 2 (price=6): dp[1][0] = max(0, -2+6) = 4. Continue tracing... final answer should be 7. Verify.

**Step 6: Check edge cases (2 minutes)**
- k=0: no transactions allowed, profit = 0. The loop does nothing with j starting at 0.
- Single day: no transactions possible, profit = 0.
- Decreasing prices: never profitable to trade, profit = 0.

**Step 7: Submit (1 minute)**

Total time: approximately 28 minutes for a complete solution to a LeetCode Hard-level DP problem. This is the process and pace to internalise for Digital coding.

**C++ version:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, k; cin >> n >> k;
    vector<int> p(n); for (int& x : p) cin >> x;

    if (k >= n/2) {
        int profit = 0;
        for (int i = 1; i < n; i++) if (p[i] > p[i-1]) profit += p[i]-p[i-1];
        cout << profit; return 0;
    }

    vector<array<int,2>> dp(k+1, {0, INT_MIN/2});
    for (int price : p)
        for (int j = k; j >= 1; j--) {
            dp[j][0] = max(dp[j][0], dp[j][1] + price);
            dp[j][1] = max(dp[j][1], dp[j-1][0] - price);
        }
    cout << dp[k][0];
}
```

**Time:** O(n x k). **Space:** O(k). The space-optimised 1D DP avoids the full 2D array. For k >= n/2, the greedy solution is faster and simpler - the edge case check is essential.

---

## Topic Coverage vs Frequency Analysis

Understanding which topics appear most frequently helps you allocate preparation time efficiently when the 45-day roadmap cannot be followed in full.

### High-Frequency Topics (Appear in Most Digital Coding Rounds)

**Dynamic Programming (all variants):** DP is the single highest-frequency advanced topic. If you invest in only one area beyond basic algorithms, invest in DP. Specifically: 1D DP (coin change, house robber, LIS), 2D DP (LCS, edit distance, grid paths), and knapsack variants (0/1, unbounded, bounded).

**Graph Traversal (BFS and DFS applications):** Connected components, shortest path in unweighted graphs (BFS), cycle detection (DFS), number of islands and similar grid problems. These are clean and well-defined in their problem pattern.

**Two-Pointer and Sliding Window:** These techniques appear in array and string problems that look complex but have elegant linear solutions. The pattern is consistent enough that learning the technique converts a category of "hard" problems into "straightforward."

### Medium-Frequency Topics (Appear in Many Digital Rounds)

**Binary Search on Answer:** Appears when the problem asks for a minimum or maximum value satisfying a condition. Once recognised, the implementation is mechanical.

**Greedy with Sorting:** Interval problems, scheduling problems, assignment problems. The "sort by some criterion, then greedily select" framework covers a wide range.

**Prefix Sums with HashMap:** Subarray sum problems that would be O(n^2) with brute force become O(n) with this technique.

### Lower-Frequency Topics (Appear in Harder Rounds and Prime-Level Problems)

**Segment Tree and BIT:** Required when a problem combines range queries with updates. The implementation is complex but the structure is always the same - building the template once and memorising it covers the pattern.

**Digit DP:** Specific to counting problems over number ranges. Recognising that a problem requires digit DP is the key skill.

**Advanced Graph (Dijkstra, Bellman-Ford, Topological Sort):** These appear in problems explicitly mentioning weighted graphs, directed graphs with precedence, or shortest path in constraint-modified graphs.

### The 80/20 Rule for Digital Preparation

80% of Digital coding problems can be solved with thorough preparation in: DP (1D and 2D), BFS/DFS on graphs and grids, two-pointer/sliding window, binary search, greedy with sorting, and prefix sums. These six technique families cover the vast majority of what appears in Problem 1 and most of what appears in Problem 2.

The remaining 20% - segment trees, digit DP, advanced graph algorithms, number theory - covers the problems that separate Digital from Prime and the hardest Problem 2 instances. If your 45 days are shorter in practice than planned, prioritise the 80% topics and treat the 20% topics as bonus preparation.

Regardless of preparation depth, the test-day strategy remains the same: read carefully, identify the technique family, write the brute-force first, submit it, then optimise. This process applies whether you have 45 days of preparation or 10.

---

Competitive coding at Digital level is a skill built through deliberate daily practice - not through passive reading or watching solution explanations. Every hour you spend writing code, debugging, and submitting builds the reflexes that the test rewards. Start with the 45-day roadmap, follow it consistently, and you will arrive at your TCS Digital coding round with the tools to compete.
