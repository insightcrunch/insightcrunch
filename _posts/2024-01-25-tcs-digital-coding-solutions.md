---
layout: post
title: "TCS Digital Coding: Advanced Problem Solving"
page_title: "TCS Digital Coding Questions with Solutions - Advanced Competitive Programming Practice for Digital Profile"
date: 2024-01-25
categories: ["Industry"]
tags: ["TCS Digital coding", "TCS Digital solutions", "TCS competitive coding", "TCS Digital programming"]
excerpt: "Advanced coding problems at TCS Digital difficulty level with complete solutions. Your competitive programming workbook for Digital."
image: "/assets/images/blog/blog-13.webp"
reading_time: 60
author: "Insight Crunch Team"
render_with_liquid: false
last_updated: 2026-03-23
---
The TCS Digital Advanced Coding section tests competitive programming ability - the kind of algorithmic thinking that separates candidates who can read textbook code from those who can write optimal solutions to novel problems under time pressure. This guide is a practice workbook: original problems framed in TCS's narrative style, with complete solutions in both C++ and Java, brute-force-to-optimal approach discussions, complexity analysis, and edge case coverage. Work through these problems the way you would in the actual exam - attempt first, then study the solution approach, then code the solution yourself without reference. The problems are organised by topic category so you can target your preparation systematically.

![TCS Guide](/assets/images/blog/blog-13.webp)

## The TCS Digital Coding Environment: What You Need to Know

### Compiler and Platform

TCS Digital Advanced Coding runs on the TCS iON platform with a CodeVita-style competitive compiler. The environment supports multiple languages:

**Primary competitive languages (recommended):** C++, Java
**Available but less common for competitive use:** C, Python, C#, Kotlin, Go, Haskell, Erlang, Lua, Perl

C++ is the strongest choice because of STL, execution speed, and competitive programming community standardisation. Java is a capable second. Python is too slow for problems with tight time limits at this difficulty level - avoid it for Digital Advanced Coding.

### Test Format

- **90 minutes** for 2-3 problems
- **Scoring by test cases passed** - each problem has 10-15 test cases; partial credit for partial solutions
- **No penalty** for resubmission - submit often
- **Strategy:** submit brute-force early for guaranteed partial credit, then optimise

### C++ Competitive Template

```cpp
#include <bits/stdc++.h>
using namespace std;
typedef long long ll;
typedef pair<int,int> pii;
typedef vector<int> vi;
#define all(x) (x).begin(), (x).end()
#define pb push_back

int main(){
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    // solution here
    return 0;
}
```

### Java Competitive Template

```java
import java.util.*;
import java.io.*;

public class Main {
    static BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
    static PrintWriter pw = new PrintWriter(new BufferedWriter(new OutputStreamWriter(System.out)));

    public static void main(String[] args) throws IOException {
        // solution here
        pw.flush();
    }
}
```

---

## Section 1: Dynamic Programming Problems

### Problem DP-1: The Warehouse Packing Problem

**Problem statement:**
A logistics company needs to pack items into a warehouse. The warehouse has exactly W cubic metres of space. There are N types of items available, each with a volume V[i] and a profit value P[i]. Each item type can be selected at most once. The company wants to maximise the total profit without exceeding the warehouse capacity. Given W, N, and the arrays V and P, find the maximum achievable profit.

**Input format:**
First line: two integers N and W.
Next N lines: two integers V[i] and P[i].

**Constraints:**
1 ≤ N ≤ 100, 1 ≤ W ≤ 10,000, 1 ≤ V[i] ≤ 1,000, 1 ≤ P[i] ≤ 10,000.

**Example:**
Input:
```
4 7
2 3
3 4
4 5
5 6
```
Output: `9` (select items with volumes 2 and 5, profits 3+6=9, or volumes 3 and 4, profits 4+5=9)

**Approach discussion:**

*Brute force (O(2^N)):* Try every subset of items. Check if total volume ≤ W. Track maximum profit. Works for N ≤ 20 but fails for N = 100.

*Optimal - 0/1 Knapsack DP (O(N × W)):* Define dp[i][w] = maximum profit using the first i items with capacity w. Recurrence:
- If we don't take item i: dp[i][w] = dp[i-1][w]
- If we take item i (only if V[i] ≤ w): dp[i][w] = dp[i-1][w-V[i]] + P[i]
- dp[i][w] = max of both options

Space-optimised 1D array: iterate capacity from W down to V[i] to prevent using the same item twice.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n, W; cin >> n >> W;
    vector<int> v(n), p(n);
    for(int i = 0; i < n; i++) cin >> v[i] >> p[i];

    vector<int> dp(W+1, 0);
    for(int i = 0; i < n; i++){
        // iterate backwards to ensure each item used at most once
        for(int w = W; w >= v[i]; w--){
            dp[w] = max(dp[w], dp[w - v[i]] + p[i]);
        }
    }
    cout << dp[W] << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(), W = sc.nextInt();
        int[] v = new int[n], p = new int[n];
        for(int i = 0; i < n; i++) { v[i] = sc.nextInt(); p[i] = sc.nextInt(); }

        int[] dp = new int[W+1];
        for(int i = 0; i < n; i++)
            for(int w = W; w >= v[i]; w--)
                dp[w] = Math.max(dp[w], dp[w - v[i]] + p[i]);

        System.out.println(dp[W]);
    }
}
```

**Time:** O(N × W). **Space:** O(W).
**Edge cases:** W = 0 (answer 0), all items have volume > W (answer 0), single item that fits.

---

### Problem DP-2: The Delivery Route (Minimum Path Sum in Grid)

**Problem statement:**
A delivery robot moves through an N × M grid warehouse. The robot starts at cell (1,1) and must reach cell (N,M). The robot can only move right or down. Each cell has a cost C[i][j] representing the energy cost of passing through it. Find the minimum total energy cost to reach the destination.

**Input format:**
First line: N and M.
Next N lines: M space-separated integers representing costs.

**Constraints:**
1 ≤ N, M ≤ 1,000, 1 ≤ C[i][j] ≤ 100.

**Approach discussion:**

*Brute force (O(2^(N+M))):* Enumerate all paths. Too slow.

*Optimal DP (O(N × M)):* dp[i][j] = minimum cost to reach (i,j).
- dp[1][1] = C[1][1]
- dp[i][1] = dp[i-1][1] + C[i][1] (only from above)
- dp[1][j] = dp[1][j-1] + C[1][j] (only from left)
- dp[i][j] = C[i][j] + min(dp[i-1][j], dp[i][j-1])

Can be done in-place to save memory.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n, m; cin >> n >> m;
    vector<vector<int>> dp(n, vector<int>(m));
    for(int i = 0; i < n; i++)
        for(int j = 0; j < m; j++) cin >> dp[i][j];

    for(int i = 1; i < n; i++) dp[i][0] += dp[i-1][0];
    for(int j = 1; j < m; j++) dp[0][j] += dp[0][j-1];
    for(int i = 1; i < n; i++)
        for(int j = 1; j < m; j++)
            dp[i][j] += min(dp[i-1][j], dp[i][j-1]);

    cout << dp[n-1][m-1] << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(), m = sc.nextInt();
        int[][] dp = new int[n][m];
        for(int i = 0; i < n; i++)
            for(int j = 0; j < m; j++) dp[i][j] = sc.nextInt();
        for(int i = 1; i < n; i++) dp[i][0] += dp[i-1][0];
        for(int j = 1; j < m; j++) dp[0][j] += dp[0][j-1];
        for(int i = 1; i < n; i++)
            for(int j = 1; j < m; j++)
                dp[i][j] += Math.min(dp[i-1][j], dp[i][j-1]);
        System.out.println(dp[n-1][m-1]);
    }
}
```

**Time:** O(N × M). **Space:** O(N × M), reducible to O(M) with rolling array.

---

### Problem DP-3: The Training Schedule (Longest Increasing Subsequence)

**Problem statement:**
A coach is designing a training programme. There are N exercises, each with a difficulty level D[i]. The coach wants to select the longest possible sequence of exercises where the difficulty increases strictly. Exercises must be selected in their original order (indices must be increasing). Find the length of the longest such subsequence.

**Input:**
First line: N.
Second line: N space-separated integers.

**Constraints:** 1 ≤ N ≤ 10,000, 1 ≤ D[i] ≤ 10,000.

**Approach discussion:**

*O(N²) DP:* For each position i, check all previous positions j < i where D[j] < D[i]. dp[i] = max(dp[j]+1) for valid j. Too slow for N = 10,000 at strict Digital time limits.

*O(N log N) patience sort:* Maintain an array `tails` where tails[i] is the smallest tail element of all increasing subsequences of length i+1. For each element, binary search for its position in tails.

**C++ Solution (O(N log N)):**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n; cin >> n;
    vector<int> d(n); for(int& x : d) cin >> x;

    vector<int> tails; // tails[i] = smallest tail of LIS of length i+1
    for(int x : d){
        auto it = lower_bound(all(tails), x); // first element >= x
        if(it == tails.end()) tails.pb(x);    // extend LIS
        else *it = x;                          // update smaller tail
    }
    cout << tails.size() << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] d = new int[n];
        for(int i = 0; i < n; i++) d[i] = sc.nextInt();

        ArrayList<Integer> tails = new ArrayList<>();
        for(int x : d){
            int pos = Collections.binarySearch(tails, x);
            if(pos < 0) pos = -(pos + 1); // insertion point
            if(pos == tails.size()) tails.add(x);
            else tails.set(pos, x);
        }
        System.out.println(tails.size());
    }
}
```

**Time:** O(N log N). **Space:** O(N).
**Edge cases:** All elements equal (LIS = 1), already sorted ascending (LIS = N), reverse sorted (LIS = 1).

---

### Problem DP-4: The Meeting Scheduler (Weighted Job Scheduling)

**Problem statement:**
A consultant has N client meetings available. Each meeting i has a start time S[i], an end time E[i], and a fee F[i]. The consultant cannot attend two overlapping meetings. Find the maximum total fee achievable by selecting a non-overlapping subset of meetings.

**Input:**
First line: N.
Next N lines: three integers S[i] E[i] F[i].

**Constraints:** 1 ≤ N ≤ 50,000. All times fit in int.

**Approach discussion:**

*Brute force (O(2^N)):* Try all subsets. Too slow.

*DP with binary search (O(N log N)):* Sort meetings by end time. Define dp[i] = maximum fee considering meetings 1 through i. For each meeting i:
- Skip it: dp[i] = dp[i-1]
- Take it: find the latest meeting j that ends before meeting i starts (binary search). dp[i] = dp[j] + F[i]
- dp[i] = max(skip, take)

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n; cin >> n;
    vector<tuple<int,int,int>> meetings(n); // (end, start, fee)
    for(auto& [e,s,f] : meetings) cin >> s >> e >> f;
    sort(all(meetings)); // sort by end time

    vector<int> ends(n);
    for(int i = 0; i < n; i++) ends[i] = get<0>(meetings[i]);

    vector<long long> dp(n+1, 0);
    for(int i = 0; i < n; i++){
        auto [e, s, f] = meetings[i];
        // binary search for latest meeting ending before s
        int lo = 0, hi = i;
        while(lo < hi){
            int mid = (lo+hi+1)/2;
            if(ends[mid-1] <= s) lo = mid;
            else hi = mid-1;
        }
        dp[i+1] = max(dp[i], dp[lo] + f);
    }
    cout << dp[n] << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[][] m = new int[n][3];
        for(int i = 0; i < n; i++) { m[i][0]=sc.nextInt(); m[i][1]=sc.nextInt(); m[i][2]=sc.nextInt(); }
        Arrays.sort(m, (a,b) -> a[1]-b[1]); // sort by end time

        long[] dp = new long[n+1];
        int[] ends = new int[n];
        for(int i = 0; i < n; i++) ends[i] = m[i][1];

        for(int i = 0; i < n; i++){
            int start = m[i][0], fee = m[i][2];
            int lo = 0, hi = i;
            while(lo < hi){
                int mid = (lo+hi+1)/2;
                if(ends[mid-1] <= start) lo = mid; else hi = mid-1;
            }
            dp[i+1] = Math.max(dp[i], dp[lo] + fee);
        }
        System.out.println(dp[n]);
    }
}
```

**Time:** O(N log N). **Space:** O(N).

---

## Section 2: Graph Problems

### Problem G-1: The Network Repair (Connected Components with BFS)

**Problem statement:**
A telecommunications company maintains a network of N servers and M direct connections. Due to a power surge, some connections are down. The company needs to know how many isolated groups of servers exist, and the size of the largest group. Given N servers (numbered 1 to N) and M active connections, find the number of connected components and the size of the largest.

**Input:**
First line: N M.
Next M lines: two integers u v (bidirectional connection).

**Constraints:** 1 ≤ N ≤ 100,000, 0 ≤ M ≤ 200,000.

**C++ Solution (BFS):**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n, m; cin >> n >> m;
    vector<vector<int>> adj(n+1);
    for(int i = 0; i < m; i++){
        int u, v; cin >> u >> v;
        adj[u].pb(v); adj[v].pb(u);
    }

    vector<bool> visited(n+1, false);
    int components = 0, maxSize = 0;

    for(int start = 1; start <= n; start++){
        if(visited[start]) continue;
        components++;
        int size = 0;
        queue<int> q;
        q.push(start); visited[start] = true;
        while(!q.empty()){
            int u = q.front(); q.pop(); size++;
            for(int v : adj[u])
                if(!visited[v]){ visited[v] = true; q.push(v); }
        }
        maxSize = max(maxSize, size);
    }
    cout << components << " " << maxSize << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) throws Exception {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(), m = sc.nextInt();
        List<List<Integer>> adj = new ArrayList<>();
        for(int i = 0; i <= n; i++) adj.add(new ArrayList<>());
        for(int i = 0; i < m; i++){
            int u = sc.nextInt(), v = sc.nextInt();
            adj.get(u).add(v); adj.get(v).add(u);
        }
        boolean[] vis = new boolean[n+1];
        int comps = 0, maxSz = 0;
        for(int s = 1; s <= n; s++){
            if(vis[s]) continue;
            comps++; int sz = 0;
            Queue<Integer> q = new LinkedList<>();
            q.add(s); vis[s] = true;
            while(!q.isEmpty()){
                int u = q.poll(); sz++;
                for(int v : adj.get(u))
                    if(!vis[v]){ vis[v]=true; q.add(v); }
            }
            maxSz = Math.max(maxSz, sz);
        }
        System.out.println(comps + " " + maxSz);
    }
}
```

**Time:** O(N + M). **Space:** O(N + M).

---

### Problem G-2: The Shortest Delivery Route (Dijkstra)

**Problem statement:**
A delivery company has a city map with N intersections and M roads. Each road has a travel time (weight). Starting from the depot at intersection 1, the driver must deliver to intersection N. Find the minimum travel time, or output -1 if no path exists.

**Input:**
First line: N M.
Next M lines: u v w (directed road from u to v with time w).

**Constraints:** 1 ≤ N ≤ 10,000, 1 ≤ M ≤ 100,000, 1 ≤ w ≤ 10,000. All weights non-negative.

**C++ Solution (Dijkstra with priority queue):**
```cpp
#include <bits/stdc++.h>
using namespace std;
typedef pair<long long,int> pli;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n, m; cin >> n >> m;
    vector<vector<pair<int,int>>> adj(n+1);
    for(int i = 0; i < m; i++){
        int u, v, w; cin >> u >> v >> w;
        adj[u].pb({v, w});
    }

    vector<long long> dist(n+1, LLONG_MAX);
    dist[1] = 0;
    priority_queue<pli, vector<pli>, greater<pli>> pq;
    pq.push({0, 1});

    while(!pq.empty()){
        auto [d, u] = pq.top(); pq.pop();
        if(d > dist[u]) continue; // stale entry
        for(auto [v, w] : adj[u]){
            if(dist[u] + w < dist[v]){
                dist[v] = dist[u] + w;
                pq.push({dist[v], v});
            }
        }
    }
    cout << (dist[n] == LLONG_MAX ? -1 : dist[n]) << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(), m = sc.nextInt();
        List<int[]>[] adj = new List[n+1];
        for(int i = 1; i <= n; i++) adj[i] = new ArrayList<>();
        for(int i = 0; i < m; i++){
            int u=sc.nextInt(), v=sc.nextInt(), w=sc.nextInt();
            adj[u].add(new int[]{v,w});
        }
        long[] dist = new long[n+1];
        Arrays.fill(dist, Long.MAX_VALUE);
        dist[1] = 0;
        PriorityQueue<long[]> pq = new PriorityQueue<>(Comparator.comparingLong(x -> x[0]));
        pq.offer(new long[]{0, 1});
        while(!pq.isEmpty()){
            long[] cur = pq.poll();
            long d = cur[0]; int u = (int)cur[1];
            if(d > dist[u]) continue;
            for(int[] e : adj[u]){
                if(dist[u]+e[1] < dist[e[0]]){
                    dist[e[0]] = dist[u]+e[1];
                    pq.offer(new long[]{dist[e[0]], e[0]});
                }
            }
        }
        System.out.println(dist[n] == Long.MAX_VALUE ? -1 : dist[n]);
    }
}
```

**Time:** O((N + M) log N). **Space:** O(N + M).
**Edge cases:** N = 1 (answer 0), no path from 1 to N (answer -1), negative edges not present (Dijkstra requires non-negative weights).

---

### Problem G-3: The Project Dependency Chain (Topological Sort)

**Problem statement:**
A software project has N tasks numbered 1 to N. Some tasks must be completed before others (task A must precede task B). Given N tasks and M dependency pairs (A, B), determine a valid order to complete all tasks. If a circular dependency exists, output "CYCLE DETECTED". Otherwise, output any valid ordering.

**Input:**
First line: N M.
Next M lines: A B (A must come before B).

**Constraints:** 1 ≤ N ≤ 100,000, 0 ≤ M ≤ 200,000.

**C++ Solution (Kahn's algorithm):**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n, m; cin >> n >> m;
    vector<vector<int>> adj(n+1);
    vector<int> indegree(n+1, 0);
    for(int i = 0; i < m; i++){
        int a, b; cin >> a >> b;
        adj[a].pb(b); indegree[b]++;
    }
    queue<int> q;
    for(int i = 1; i <= n; i++) if(indegree[i] == 0) q.push(i);

    vector<int> order;
    while(!q.empty()){
        int u = q.front(); q.pop();
        order.pb(u);
        for(int v : adj[u]) if(--indegree[v] == 0) q.push(v);
    }
    if((int)order.size() != n){ cout << "CYCLE DETECTED\n"; return 0; }
    for(int x : order) cout << x << " ";
    cout << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(), m = sc.nextInt();
        List<List<Integer>> adj = new ArrayList<>();
        for(int i = 0; i <= n; i++) adj.add(new ArrayList<>());
        int[] indeg = new int[n+1];
        for(int i = 0; i < m; i++){
            int a=sc.nextInt(), b=sc.nextInt();
            adj.get(a).add(b); indeg[b]++;
        }
        Queue<Integer> q = new LinkedList<>();
        for(int i = 1; i <= n; i++) if(indeg[i] == 0) q.add(i);
        List<Integer> order = new ArrayList<>();
        while(!q.isEmpty()){
            int u = q.poll(); order.add(u);
            for(int v : adj.get(u)) if(--indeg[v] == 0) q.add(v);
        }
        if(order.size() != n){ System.out.println("CYCLE DETECTED"); return; }
        StringBuilder sb = new StringBuilder();
        for(int x : order) sb.append(x).append(" ");
        System.out.println(sb.toString().trim());
    }
}
```

**Time:** O(N + M). **Space:** O(N + M).

---

### Problem G-4: The Bipartite Team Assignment

**Problem statement:**
A company has N employees. Based on personality assessments, some pairs of employees are "incompatible" (they cannot be on the same team). Can all N employees be split into exactly two teams such that every incompatible pair has its members on different teams? Output "YES" if possible and the team assignment, or "NO" if not.

**Approach:** A graph is bipartite if and only if it has no odd-length cycles. Check using 2-colouring via BFS.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n, m; cin >> n >> m;
    vector<vector<int>> adj(n+1);
    for(int i = 0; i < m; i++){
        int u, v; cin >> u >> v;
        adj[u].pb(v); adj[v].pb(u);
    }
    vector<int> color(n+1, -1);
    bool bipartite = true;
    for(int s = 1; s <= n && bipartite; s++){
        if(color[s] != -1) continue;
        queue<int> q; q.push(s); color[s] = 0;
        while(!q.empty() && bipartite){
            int u = q.front(); q.pop();
            for(int v : adj[u]){
                if(color[v] == -1){ color[v] = 1-color[u]; q.push(v); }
                else if(color[v] == color[u]) bipartite = false;
            }
        }
    }
    if(!bipartite){ cout << "NO\n"; return 0; }
    cout << "YES\n";
    for(int i = 1; i <= n; i++) cout << "Employee " << i << ": Team " << (color[i]+1) << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(), m = sc.nextInt();
        List<List<Integer>> adj = new ArrayList<>();
        for(int i = 0; i <= n; i++) adj.add(new ArrayList<>());
        for(int i = 0; i < m; i++){
            int u=sc.nextInt(), v=sc.nextInt();
            adj.get(u).add(v); adj.get(v).add(u);
        }
        int[] color = new int[n+1]; Arrays.fill(color, -1);
        boolean ok = true;
        for(int s = 1; s <= n && ok; s++){
            if(color[s] != -1) continue;
            Queue<Integer> q = new LinkedList<>();
            q.add(s); color[s] = 0;
            while(!q.isEmpty() && ok){
                int u = q.poll();
                for(int v : adj.get(u)){
                    if(color[v] == -1){ color[v] = 1-color[u]; q.add(v); }
                    else if(color[v] == color[u]) ok = false;
                }
            }
        }
        if(!ok){ System.out.println("NO"); return; }
        System.out.println("YES");
        for(int i = 1; i <= n; i++)
            System.out.println("Employee " + i + ": Team " + (color[i]+1));
    }
}
```

**Time:** O(N + M). **Space:** O(N + M).

---

## Section 3: Greedy Problems

### Problem GR-1: The Resource Allocator (Fractional Task Assignment)

**Problem statement:**
A factory has K machines available for T hours each. There are N jobs to complete, each requiring H[i] machine-hours. The factory wants to schedule as many complete jobs as possible. Jobs cannot be split across machines or time slots - each job requires exactly H[i] consecutive machine-hours on a single machine. Find the maximum number of complete jobs that can be scheduled.

**Simplified version (for the purpose of this problem):** You have total capacity = K × T. Schedule as many jobs as possible, each requiring H[i] hours. Maximise count.

**Approach:** Sort jobs by hours required (ascending). Take greedily from smallest. Greedy proof: taking a shorter job over a longer one never reduces the total count since it uses less capacity.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    long long k, t; cin >> k >> t;
    int n; cin >> n;
    vector<int> h(n); for(int& x : h) cin >> x;
    sort(all(h));

    long long capacity = k * t, count = 0;
    for(int hours : h){
        if(capacity >= hours){ capacity -= hours; count++; }
        else break;
    }
    cout << count << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        long k = sc.nextLong(), t = sc.nextLong();
        int n = sc.nextInt();
        int[] h = new int[n];
        for(int i = 0; i < n; i++) h[i] = sc.nextInt();
        Arrays.sort(h);
        long cap = k * t, count = 0;
        for(int hours : h){
            if(cap >= hours){ cap -= hours; count++; }
            else break;
        }
        System.out.println(count);
    }
}
```

**Time:** O(N log N). **Space:** O(N).

---

### Problem GR-2: The Conference Room Booking (Interval Scheduling Maximisation)

**Problem statement:**
A company has one conference room. N meeting requests arrive, each with a start time S[i] and end time E[i]. A meeting occupies the room from S[i] to E[i] (inclusive of start, exclusive of end). No two meetings can overlap. Find the maximum number of non-overlapping meetings that can be accommodated.

**Approach:** Sort by end time. Greedily select the earliest-ending non-conflicting meeting. Classic interval scheduling proof: the meeting that ends earliest leaves the most room for subsequent meetings.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n; cin >> n;
    vector<pair<int,int>> meetings(n);
    for(auto& [s,e] : meetings) cin >> s >> e;
    sort(meetings.begin(), meetings.end(), [](auto& a, auto& b){ return a.second < b.second; });

    int count = 0, lastEnd = INT_MIN;
    for(auto& [s, e] : meetings){
        if(s >= lastEnd){ count++; lastEnd = e; }
    }
    cout << count << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[][] m = new int[n][2];
        for(int i = 0; i < n; i++) { m[i][0]=sc.nextInt(); m[i][1]=sc.nextInt(); }
        Arrays.sort(m, (a,b) -> a[1]-b[1]);
        int count = 0, lastEnd = Integer.MIN_VALUE;
        for(int[] meeting : m)
            if(meeting[0] >= lastEnd){ count++; lastEnd = meeting[1]; }
        System.out.println(count);
    }
}
```

**Time:** O(N log N). **Space:** O(N).

---

## Section 4: Advanced Array and String Problems

### Problem AS-1: The Matrix Rotation (90-Degree Clockwise)

**Problem statement:**
A digital image is represented as an N × N grid of pixels. Rotate the image 90 degrees clockwise in-place (without using extra space proportional to N²). Output the rotated grid.

**Approach:** Two-step in-place rotation:
1. Transpose the matrix: swap grid[i][j] with grid[j][i].
2. Reverse each row: swap grid[i][0] with grid[i][N-1], etc.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n; cin >> n;
    vector<vector<int>> g(n, vector<int>(n));
    for(int i = 0; i < n; i++) for(int j = 0; j < n; j++) cin >> g[i][j];

    // Step 1: Transpose
    for(int i = 0; i < n; i++) for(int j = i+1; j < n; j++) swap(g[i][j], g[j][i]);
    // Step 2: Reverse each row
    for(int i = 0; i < n; i++) reverse(g[i].begin(), g[i].end());

    for(int i = 0; i < n; i++){
        for(int j = 0; j < n; j++) cout << g[i][j] << " \n"[j==n-1];
    }
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[][] g = new int[n][n];
        for(int i = 0; i < n; i++) for(int j = 0; j < n; j++) g[i][j] = sc.nextInt();
        // Transpose
        for(int i = 0; i < n; i++) for(int j = i+1; j < n; j++) { int t=g[i][j]; g[i][j]=g[j][i]; g[j][i]=t; }
        // Reverse rows
        for(int i = 0; i < n; i++){
            int lo = 0, hi = n-1;
            while(lo < hi){ int t=g[i][lo]; g[i][lo]=g[i][hi]; g[i][hi]=t; lo++; hi--; }
        }
        StringBuilder sb = new StringBuilder();
        for(int i = 0; i < n; i++){
            for(int j = 0; j < n; j++) sb.append(g[i][j]).append(j<n-1?" ":"\n");
        }
        System.out.print(sb);
    }
}
```

**Time:** O(N²). **Space:** O(1) extra.

---

### Problem AS-2: The Anagram Groups (String Categorisation)

**Problem statement:**
A lexicographer is sorting a list of N words into groups of anagrams (words that contain the same letters in different orders). Group all N words by their anagram family and output each group on a separate line (words within a group in any order, groups in any order).

**Input:** First line N. Next N lines: one word each (all lowercase).

**Approach:** For each word, create a canonical key (sorted characters). Use a HashMap from key to list of words.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n; cin >> n;
    map<string, vector<string>> groups;
    for(int i = 0; i < n; i++){
        string w; cin >> w;
        string key = w; sort(all(key));
        groups[key].pb(w);
    }
    for(auto& [key, words] : groups){
        for(const string& w : words) cout << w << " ";
        cout << "\n";
    }
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        Map<String, List<String>> groups = new LinkedHashMap<>();
        for(int i = 0; i < n; i++){
            String w = sc.next();
            char[] c = w.toCharArray(); Arrays.sort(c);
            String key = new String(c);
            groups.computeIfAbsent(key, k -> new ArrayList<>()).add(w);
        }
        StringBuilder sb = new StringBuilder();
        for(List<String> group : groups.values()){
            for(String w : group) sb.append(w).append(' ');
            sb.append('\n');
        }
        System.out.print(sb);
    }
}
```

**Time:** O(N × L log L) where L = max word length. **Space:** O(N × L).

---

### Problem AS-3: The Maximum Subarray Sum With Wraparound

**Problem statement:**
Given a circular array of N integers (the array wraps around so index N-1 is adjacent to index 0), find the maximum sum of any non-empty contiguous subarray. The subarray may wrap from the end of the array back to the beginning.

**Approach:**
- Case 1 (no wrap): Standard Kadane's algorithm.
- Case 2 (wrap): Equivalent to total_sum - minimum_subarray_sum (the wrap selects everything except a middle segment, which is the minimum sum subarray).
- Answer = max(case1, case2).
- Special case: if all elements are negative, the answer is the maximum single element (case2 would give 0, which is wrong if all negative).

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n; cin >> n;
    vector<int> a(n); for(int& x : a) cin >> x;

    // Kadane's for max
    int maxSum = a[0], curMax = a[0];
    for(int i = 1; i < n; i++){
        curMax = max(a[i], curMax + a[i]);
        maxSum = max(maxSum, curMax);
    }
    // Kadane's for min (for wraparound case)
    int minSum = a[0], curMin = a[0], total = a[0];
    for(int i = 1; i < n; i++){
        total += a[i];
        curMin = min(a[i], curMin + a[i]);
        minSum = min(minSum, curMin);
    }
    // If all negative, maxSum is the answer (wraparound gives total - minSum = 0, invalid)
    int wrapSum = total - minSum;
    cout << (wrapSum == 0 ? maxSum : max(maxSum, wrapSum)) << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] a = new int[n];
        for(int i = 0; i < n; i++) a[i] = sc.nextInt();
        int maxSum = a[0], curMax = a[0];
        int minSum = a[0], curMin = a[0], total = a[0];
        for(int i = 1; i < n; i++){
            total += a[i];
            curMax = Math.max(a[i], curMax + a[i]); maxSum = Math.max(maxSum, curMax);
            curMin = Math.min(a[i], curMin + a[i]); minSum = Math.min(minSum, curMin);
        }
        int wrapSum = total - minSum;
        System.out.println(wrapSum == 0 ? maxSum : Math.max(maxSum, wrapSum));
    }
}
```

**Time:** O(N). **Space:** O(N) for input, O(1) extra.

---

## Section 5: Number Theory Problems

### Problem NT-1: The Password Generator (Modular Exponentiation)

**Problem statement:**
A security system generates passwords using large powers. Given a base B, an exponent E, and a modulus M, compute (B^E) mod M. E can be extremely large (up to 10^18), requiring fast exponentiation.

**Input:** Three integers B, E, M on one line.

**Constraints:** 1 ≤ B, M ≤ 10^9, 1 ≤ E ≤ 10^18.

**Approach:** Binary exponentiation (repeated squaring). Compute using the bit structure of E.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
typedef long long ll;
typedef unsigned long long ull;

ll power(ll base, ll exp, ll mod){
    ll result = 1;
    base %= mod;
    while(exp > 0){
        if(exp & 1) result = (__int128)result * base % mod;
        base = (__int128)base * base % mod;
        exp >>= 1;
    }
    return result;
}

int main(){
    ll b, e, m; cin >> b >> e >> m;
    cout << power(b, e, m) << "\n";
}
```

Note: `__int128` prevents overflow when multiplying two numbers up to 10^9 before taking mod (product up to 10^18, which overflows long long).

**Java Solution:**
```java
import java.util.*;
import java.math.BigInteger;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        long b = sc.nextLong(), e = sc.nextLong(), m = sc.nextLong();
        // Java BigInteger has built-in modPow
        System.out.println(BigInteger.valueOf(b).modPow(BigInteger.valueOf(e), BigInteger.valueOf(m)));
    }
}
```

Alternatively, implement manually:
```java
static long power(long base, long exp, long mod){
    long result = 1; base %= mod;
    while(exp > 0){
        if((exp & 1) == 1) result = Math.floorMod(result * base, mod); // careful with overflow
        base = Math.floorMod(base * base, mod);
        exp >>= 1;
    }
    return result;
}
```

For Java manual implementation: if base can be up to 10^9, then `base * base` can overflow long (max ~9.2 × 10^18 > 10^18). Use `(long)((double)base * base % mod)` as approximation or use BigInteger for intermediate multiplication.

**Time:** O(log E). **Space:** O(1).

---

### Problem NT-2: The Seating Arrangements Counter (Combinatorics with Modular Arithmetic)

**Problem statement:**
An event organiser wants to seat N guests in N chairs arranged in a circle. However, K specific pairs of guests cannot sit adjacent to each other. Count the total number of valid seating arrangements modulo 10^9+7. For simplicity, two arrangements are the same if one is a rotation of the other.

**Simplified version (ignore K constraints, test modular arithmetic pipeline):**
Count circular permutations of N distinct objects. Answer = (N-1)! mod (10^9+7).

**Full version with constraints:**
For K forbidden adjacency constraints, use inclusion-exclusion or the permanent of a matrix (hard). At Digital level, simplified version is more likely.

**C++ Solution (simplified):**
```cpp
#include <bits/stdc++.h>
using namespace std;
const long long MOD = 1e9+7;
int main(){
    int n; cin >> n;
    if(n == 1){ cout << 1 << "\n"; return 0; }
    long long ans = 1;
    for(int i = 2; i <= n-1; i++) ans = ans * i % MOD; // (n-1)!
    cout << ans << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    static final long MOD = 1_000_000_007L;
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        if(n == 1){ System.out.println(1); return; }
        long ans = 1;
        for(int i = 2; i <= n-1; i++) ans = ans * i % MOD;
        System.out.println(ans);
    }
}
```

**Extended - Computing nCr mod p using precomputed factorials:**
```cpp
const int MAXN = 1e6+5;
const long long MOD = 1e9+7;
long long fact[MAXN], inv_fact[MAXN];

long long power(long long b, long long e, long long m){
    long long r=1; b%=m;
    for(;e>0;e>>=1){if(e&1)r=r*b%m;b=b*b%m;} return r;
}
void precompute(){
    fact[0]=1;
    for(int i=1;i<MAXN;i++) fact[i]=fact[i-1]*i%MOD;
    inv_fact[MAXN-1]=power(fact[MAXN-1],MOD-2,MOD);
    for(int i=MAXN-2;i>=0;i--) inv_fact[i]=inv_fact[i+1]*(i+1)%MOD;
}
long long nCr(int n, int r){
    if(r<0||r>n) return 0;
    return fact[n]%MOD*inv_fact[r]%MOD*inv_fact[n-r]%MOD;
}
```

**Time:** O(N) precompute, O(1) per nCr query.

---

## Section 6: Miscellaneous Competitive Problems

### Problem M-1: The Coin Tower Simulation

**Problem statement:**
Two players play a game with a pile of N coins. Players alternate turns (Player 1 goes first). On each turn, the current player may remove 1, 2, or 3 coins. The player who takes the last coin wins. Determine which player wins with optimal play.

**Approach:** Game theory - Sprague-Grundy / Nim analysis.
- If N mod 4 == 0: Player 2 wins (Player 1 is always left with a multiple of 4 after Player 2 mirrors moves).
- Otherwise: Player 1 wins.

**Proof sketch:** If N = 4k, whatever Player 1 takes (1, 2, or 3), Player 2 takes (3, 2, or 1) to keep a multiple of 4 remaining. Eventually Player 2 takes the last coin(s).

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    int n; cin >> n;
    cout << (n % 4 == 0 ? "Player 2 wins" : "Player 1 wins") << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        System.out.println(n % 4 == 0 ? "Player 2 wins" : "Player 1 wins");
    }
}
```

**Extension (general game with any removal set):** Compute Grundy values for each position using dp[i] = mex({dp[i-k] : k in allowed_moves, k <= i}).

---

### Problem M-2: The Spiral Matrix Generator

**Problem statement:**
Generate an N × N matrix filled with integers 1 to N² in spiral order (starting from the top-left, moving right, then down, then left, then up, and so on inward).

**Example (N=3):**
```
1 2 3
8 9 4
7 6 5
```

**Approach:** Maintain four boundaries (top, bottom, left, right). Fill layer by layer outward-to-inward.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    int n; cin >> n;
    vector<vector<int>> mat(n, vector<int>(n, 0));
    int top=0, bottom=n-1, left=0, right=n-1, num=1;
    while(num <= n*n){
        for(int j=left;j<=right;j++) mat[top][j]=num++;
        top++;
        for(int i=top;i<=bottom;i++) mat[i][right]=num++;
        right--;
        for(int j=right;j>=left;j--) mat[bottom][j]=num++;
        bottom--;
        for(int i=bottom;i>=top;i--) mat[i][left]=num++;
        left++;
    }
    for(int i=0;i<n;i++){
        for(int j=0;j<n;j++) cout<<mat[i][j]<<" \n"[j==n-1];
    }
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[][] mat = new int[n][n];
        int top=0,bot=n-1,left=0,right=n-1,num=1;
        while(num<=n*n){
            for(int j=left;j<=right;j++) mat[top][j]=num++;
            top++;
            for(int i=top;i<=bot;i++) mat[i][right]=num++;
            right--;
            for(int j=right;j>=left;j--) mat[bot][j]=num++;
            bot--;
            for(int i=bot;i>=top;i--) mat[i][left]=num++;
            left++;
        }
        StringBuilder sb=new StringBuilder();
        for(int i=0;i<n;i++){
            for(int j=0;j<n;j++) sb.append(mat[i][j]).append(j<n-1?" ":"\n");
        }
        System.out.print(sb);
    }
}
```

**Time:** O(N²). **Space:** O(N²).

---

### Problem M-3: The Stock Trader (Minimum Buy Maximum Sell with K Transactions)

**Problem statement:**
A trader monitors stock prices over N days. The trader can make at most K buy-sell transactions (buy then sell constitutes one transaction). The trader may not hold more than one stock at a time. Find the maximum profit achievable.

**Approach:** DP with states (number of transactions completed, whether currently holding stock).
- State: dp[k][holding] = max profit with k transactions and holding status
- Transition (per price day):
  - Not holding: don't trade, or sell today
  - Holding: don't trade, or buy today (opens new transaction)

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n, K; cin >> n >> K;
    vector<int> prices(n); for(int& p : prices) cin >> p;

    if(K >= n/2){ // unlimited transactions
        int profit = 0;
        for(int i=1;i<n;i++) if(prices[i]>prices[i-1]) profit+=prices[i]-prices[i-1];
        cout << profit << "\n"; return 0;
    }

    // dp[k][0] = max profit with at most k transactions, not holding
    // dp[k][1] = max profit with at most k transactions, holding
    vector<array<int,2>> dp(K+1, {0, INT_MIN/2});
    for(int price : prices)
        for(int k=K;k>=1;k--){
            dp[k][0] = max(dp[k][0], dp[k][1]+price); // sell
            dp[k][1] = max(dp[k][1], dp[k-1][0]-price); // buy
        }
    cout << dp[K][0] << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(), K = sc.nextInt();
        int[] p = new int[n]; for(int i=0;i<n;i++) p[i]=sc.nextInt();
        if(K >= n/2){
            int profit=0;
            for(int i=1;i<n;i++) if(p[i]>p[i-1]) profit+=p[i]-p[i-1];
            System.out.println(profit); return;
        }
        int[][] dp = new int[K+1][2];
        for(int k=0;k<=K;k++) dp[k][1]=Integer.MIN_VALUE/2;
        for(int price : p)
            for(int k=K;k>=1;k--){
                dp[k][0] = Math.max(dp[k][0], dp[k][1]+price);
                dp[k][1] = Math.max(dp[k][1], dp[k-1][0]-price);
            }
        System.out.println(dp[K][0]);
    }
}
```

**Time:** O(N × K). **Space:** O(K).

---

## Section 7: Union-Find Applications

### Problem UF-1: The Friendship Network (Dynamic Connectivity)

**Problem statement:**
A social network starts with N users, each in their own group. Operations arrive in sequence:
- `CONNECT A B`: merge the groups of users A and B.
- `QUERY A B`: output "YES" if A and B are in the same group, "NO" otherwise.

Handle Q operations efficiently.

**C++ Solution (Union-Find with path compression and union by rank):**
```cpp
#include <bits/stdc++.h>
using namespace std;

struct DSU {
    vector<int> parent, rank;
    DSU(int n): parent(n+1), rank(n+1,0){ iota(parent.begin(),parent.end(),0); }
    int find(int x){ return parent[x]==x?x:parent[x]=find(parent[x]); }
    void unite(int a, int b){
        a=find(a); b=find(b); if(a==b) return;
        if(rank[a]<rank[b]) swap(a,b);
        parent[b]=a;
        if(rank[a]==rank[b]) rank[a]++;
    }
    bool same(int a, int b){ return find(a)==find(b); }
};

int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n, q; cin >> n >> q;
    DSU dsu(n);
    while(q--){
        string op; int a, b; cin >> op >> a >> b;
        if(op == "CONNECT") dsu.unite(a,b);
        else cout << (dsu.same(a,b)?"YES":"NO") << "\n";
    }
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    static int[] parent, rank;
    static int find(int x){ return parent[x]==x?x:(parent[x]=find(parent[x])); }
    static void unite(int a, int b){
        a=find(a); b=find(b); if(a==b)return;
        if(rank[a]<rank[b]){int t=a;a=b;b=t;}
        parent[b]=a; if(rank[a]==rank[b]) rank[a]++;
    }
    public static void main(String[] args) throws Exception {
        Scanner sc = new Scanner(System.in);
        int n=sc.nextInt(), q=sc.nextInt();
        parent=new int[n+1]; rank=new int[n+1];
        for(int i=0;i<=n;i++) parent[i]=i;
        StringBuilder sb=new StringBuilder();
        while(q-->0){
            String op=sc.next(); int a=sc.nextInt(),b=sc.nextInt();
            if(op.equals("CONNECT")) unite(a,b);
            else sb.append(find(a)==find(b)?"YES":"NO").append('\n');
        }
        System.out.print(sb);
    }
}
```

**Time:** O(α(N)) per operation (essentially O(1)). **Space:** O(N).

---

## Exam Strategy for Digital Coding: Worked Example

### The 90-Minute Decision Framework

With 2-3 problems and 90 minutes, the time distribution matters as much as the algorithms.

**Opening 5 minutes:** Read all problems completely. Classify each:
- Problem 1: recognise the algorithmic category immediately? Budget 30-35 minutes.
- Problem 2: recognise category with some thought? Budget 40-45 minutes.
- Problem 3 (if present): unclear or very hard? Budget remaining time.

**The "guaranteed partial credit" strategy:**
For Problem 1 (most accessible): implement the brute-force solution in the first 12-15 minutes. Submit. This secures test case credits before the clock pressure is high. Then spend the remaining allocated time on the optimal solution.

**When stuck on the optimal approach:**
If you cannot identify the optimal algorithm after 10 minutes of genuine thinking, submit whatever you have (brute-force or partial), move to the next problem, and return if time permits. A partial score on Problem 2 combined with a brute-force score on Problem 1 often beats spending the full time on Problem 1's optimal solution.

**The "same technique" recognition:**
Many Digital coding problems share an underlying technique even when the problem narrative differs. Practice mapping problem narratives to algorithm categories:
- "Minimum cost" in a grid or graph → Dijkstra or DP on grid
- "Maximum selection" from a sequence → Greedy or DP (LIS, knapsack)
- "Group membership" queries → Union-Find
- "Count arrangements/paths" → DP with combinatorics
- "Ordering with constraints" → Topological Sort

---

## Frequently Asked Questions: TCS Digital Coding

**Should I use `#include <bits/stdc++.h>` in the TCS iON compiler?**
This GCC-specific header is generally available in competitive programming environments including TCS iON. If it fails to compile, replace with the specific headers needed: `<iostream>`, `<vector>`, `<algorithm>`, `<queue>`, `<map>`, `<set>`, `<string>`, `<climits>`.

**How do I handle overflow in C++?**
For products of numbers up to 10^9, use `long long`. For products of `long long` values (up to 10^18), use `__int128` or take modulo at each multiplication step. A common pattern: `(a % MOD) * (b % MOD) % MOD`.

**What if I don't know the optimal algorithm for a problem?**
Implement the brute-force solution first and submit it. Partial test case credit is real value. Then think about the optimal approach. If the time limit is tight and brute-force is timing out on large inputs, consider approximations or early-exit optimisations.

**Is recursion acceptable or will it cause stack overflow?**
Recursion with depth up to 10,000-20,000 is generally safe. For N up to 100,000, recursive DFS/BFS may cause stack overflow. Use an explicit stack (iterative implementation) for safety on large inputs.

**When should I use `long long` by default?**
Any time a calculation involves: multiplication of two numbers each potentially above 10^5, sums of N numbers where N × max_value > 2 × 10^9, or modular arithmetic products. The safe rule: if in doubt, use `long long`.

**What is the significance of the MOD = 10^9+7 pattern?**
10^9+7 is a prime number. Using a prime modulus enables modular inverse computation via Fermat's little theorem (a^(p-2) mod p). Whenever a problem says "output answer modulo 10^9+7," all arithmetic must be done modulo this value to prevent overflow and maintain correctness.

---

## Section 8: Sliding Window and Two-Pointer Problems

### Problem SW-1: The Quality Control Window (Minimum Window Substring)

**Problem statement:**
A quality inspector has a product catalogue string S and a requirement string T. The inspector needs to find the smallest contiguous substring of S that contains all characters of T (with correct frequencies). Output the starting index and length of the minimum window, or output "-1 0" if no such window exists.

**Approach:** Sliding window with two pointers. Expand right pointer to include all T characters, then contract left pointer to minimise the window.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    string s, t; cin >> s >> t;
    int n = s.size(), m = t.size();

    map<char,int> need, have;
    for(char c : t) need[c]++;
    int formed = 0, required = need.size();
    int bestLen = INT_MAX, bestStart = -1;
    int left = 0;

    for(int right = 0; right < n; right++){
        char c = s[right];
        have[c]++;
        if(need.count(c) && have[c] == need[c]) formed++;

        while(formed == required){
            if(right - left + 1 < bestLen){
                bestLen = right - left + 1;
                bestStart = left;
            }
            char lc = s[left++];
            have[lc]--;
            if(need.count(lc) && have[lc] < need[lc]) formed--;
        }
    }
    if(bestStart == -1) cout << "-1 0\n";
    else cout << bestStart << " " << bestLen << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.next(), t = sc.next();
        Map<Character,Integer> need = new HashMap<>(), have = new HashMap<>();
        for(char c : t.toCharArray()) need.merge(c, 1, Integer::sum);
        int formed = 0, required = need.size();
        int bestLen = Integer.MAX_VALUE, bestStart = -1, left = 0;

        for(int right = 0; right < s.length(); right++){
            char c = s.charAt(right);
            have.merge(c, 1, Integer::sum);
            if(need.containsKey(c) && have.get(c).equals(need.get(c))) formed++;
            while(formed == required){
                if(right - left + 1 < bestLen){ bestLen = right-left+1; bestStart = left; }
                char lc = s.charAt(left++);
                have.merge(lc, -1, Integer::sum);
                if(need.containsKey(lc) && have.get(lc) < need.get(lc)) formed--;
            }
        }
        System.out.println(bestStart == -1 ? "-1 0" : bestStart + " " + bestLen);
    }
}
```

**Time:** O(N + M) where N = |S|, M = |T|. **Space:** O(M) for the character maps.

---

### Problem SW-2: The Budget Planner (Subarray Sum Closest to Target)

**Problem statement:**
A financial planner has N monthly expense amounts. The planner wants to find a contiguous range of months whose total expense is closest to (but not exceeding) a budget limit B. Output the maximum subarray sum that does not exceed B.

**Constraints:** N ≤ 100,000, all amounts positive (for simple sliding window), B up to 10^9.

**Approach (positive values):** Sliding window. Expand right, contract left when sum exceeds B.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n; long long B; cin >> n >> B;
    vector<long long> a(n); for(long long& x : a) cin >> x;

    long long best = 0, cur = 0;
    int left = 0;
    for(int right = 0; right < n; right++){
        cur += a[right];
        while(cur > B) cur -= a[left++];
        best = max(best, cur);
    }
    cout << best << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt(); long B = sc.nextLong();
        long[] a = new long[n]; for(int i=0;i<n;i++) a[i]=sc.nextLong();
        long best=0, cur=0; int left=0;
        for(int r=0;r<n;r++){
            cur+=a[r];
            while(cur>B) cur-=a[left++];
            best=Math.max(best,cur);
        }
        System.out.println(best);
    }
}
```

**Time:** O(N). **Space:** O(N) for input.
**Note:** For arrays with negative values, this problem requires a different approach (prefix sums + sorted structure, O(N log N)).

---

## Section 9: Stack and Queue Applications

### Problem SQ-1: The Expression Evaluator (Valid Parentheses Extension)

**Problem statement:**
Given a string containing brackets, parentheses, and curly braces - `()`, `[]`, `{}` - determine if the string is validly nested. Then, if valid, count the maximum nesting depth.

**Input:** A single string.
**Output:** "VALID depth D" or "INVALID".

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    string s; cin >> s;
    stack<char> st;
    map<char,char> match = {{')', '('}, {']', '['}, {'}', '{'}};
    bool valid = true;
    int depth = 0, maxDepth = 0;

    for(char c : s){
        if(c=='(' || c=='[' || c=='{'){
            st.push(c); depth++;
            maxDepth = max(maxDepth, depth);
        } else if(match.count(c)){
            if(st.empty() || st.top() != match[c]){ valid=false; break; }
            st.pop(); depth--;
        }
    }
    if(!st.empty()) valid = false;
    cout << (valid ? "VALID depth "+to_string(maxDepth) : "INVALID") << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.next();
        Deque<Character> st = new ArrayDeque<>();
        Map<Character,Character> match = Map.of(')',  '(', ']', '[', '}', '{');
        boolean valid = true; int depth=0, maxDepth=0;
        for(char c : s.toCharArray()){
            if("([{".indexOf(c)>=0){ st.push(c); depth++; maxDepth=Math.max(maxDepth,depth); }
            else if(match.containsKey(c)){
                if(st.isEmpty()||st.peek()!=match.get(c)){valid=false;break;}
                st.pop(); depth--;
            }
        }
        if(!st.isEmpty()) valid=false;
        System.out.println(valid ? "VALID depth "+maxDepth : "INVALID");
    }
}
```

**Time:** O(N). **Space:** O(N) stack in worst case.

---

### Problem SQ-2: The Stock Span Problem

**Problem statement:**
A stock's daily prices are given as an array. The "span" of the stock's price on day i is the maximum number of consecutive days (ending on day i) during which the price was less than or equal to the price on day i. Compute the span for each day.

**Example:** Prices = [100, 80, 60, 70, 60, 75, 85]
Spans =       [1,   1,  1,  2,  1,  4,  6]

**Approach:** Monotonic stack. For each day, pop all days with price ≤ current. The span is current index minus the index of the last day with a higher price.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    int n; cin >> n;
    vector<int> price(n); for(int& x : price) cin >> x;

    vector<int> span(n);
    stack<int> st; // stores indices

    for(int i = 0; i < n; i++){
        while(!st.empty() && price[st.top()] <= price[i]) st.pop();
        span[i] = st.empty() ? i+1 : i - st.top();
        st.push(i);
    }
    for(int s : span) cout << s << " ";
    cout << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int[] price = new int[n], span = new int[n];
        for(int i=0;i<n;i++) price[i]=sc.nextInt();
        Deque<Integer> st = new ArrayDeque<>();
        for(int i=0;i<n;i++){
            while(!st.isEmpty() && price[st.peek()]<=price[i]) st.pop();
            span[i] = st.isEmpty() ? i+1 : i-st.peek();
            st.push(i);
        }
        StringBuilder sb=new StringBuilder();
        for(int s:span) sb.append(s).append(' ');
        System.out.println(sb.toString().trim());
    }
}
```

**Time:** O(N) amortised (each index pushed and popped at most once). **Space:** O(N).

---

## Section 10: Binary Search Applications

### Problem BS-1: The Capacity Planning Problem (Binary Search on Answer)

**Problem statement:**
A shipping company needs to ship N packages in D days. Package weights are given in order - each day's shipment must be contiguous packages and cannot exceed the ship's capacity C. Find the minimum capacity C that allows all packages to be shipped in D days or fewer.

**Approach:** Binary search on the answer (capacity C). For a given C, greedily compute the number of days needed. If days ≤ D, C might work (try smaller). If days > D, C is too small (try larger).

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;

bool canShip(vector<int>& w, int cap, int days){
    int d=1, cur=0;
    for(int x : w){
        if(x > cap) return false; // single package exceeds capacity
        if(cur + x > cap){ d++; cur = 0; }
        cur += x;
    }
    return d <= days;
}

int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n, days; cin >> n >> days;
    vector<int> w(n); for(int& x : w) cin >> x;

    int lo = *max_element(all(w));  // must fit the heaviest package
    int hi = accumulate(all(w), 0); // worst case: ship all in one day

    while(lo < hi){
        int mid = (lo+hi)/2;
        if(canShip(w, mid, days)) hi = mid;
        else lo = mid+1;
    }
    cout << lo << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    static boolean canShip(int[] w, int cap, int days){
        int d=1, cur=0;
        for(int x : w){
            if(x>cap) return false;
            if(cur+x>cap){ d++; cur=0; }
            cur+=x;
        }
        return d<=days;
    }
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n=sc.nextInt(), days=sc.nextInt();
        int[] w=new int[n]; int lo=0, hi=0;
        for(int i=0;i<n;i++){ w[i]=sc.nextInt(); lo=Math.max(lo,w[i]); hi+=w[i]; }
        while(lo<hi){ int mid=(lo+hi)/2; if(canShip(w,mid,days)) hi=mid; else lo=mid+1; }
        System.out.println(lo);
    }
}
```

**Time:** O(N log(sum(W))). **Space:** O(N).
**Key insight:** Binary search on the answer works because the "can we do it in D days with capacity C?" function is monotone - if C works, any larger C also works.

---

## Debugging Strategies for Digital Coding

### Common Reasons a Correct Solution Fails Test Cases

**Wrong answer (WA):**
- Off-by-one in array indices (check: does your loop go from 0 to n-1 or 0 to n?)
- Integer overflow (check: are you using `long long` where products might exceed 2 × 10^9?)
- Incorrect handling of equal elements (check: should >= be > or < be <=?)
- Edge case not handled (check: N = 1, all elements equal, empty array)

**Time limit exceeded (TLE):**
- Algorithm is O(N²) when O(N log N) is needed
- Using `cin >> string` in a tight loop without fast I/O
- In Java: using `System.out.println` in a loop instead of `StringBuilder + pw.flush()`
- Unnecessary work in inner loops (precompute instead of recompute)

**Runtime error (RE):**
- Stack overflow from deep recursion (N = 100,000, recursive DFS will overflow)
- Array index out of bounds (accessing arr[n] when valid range is arr[0..n-1])
- Division by zero (check for zero denominators)
- NullPointerException in Java (check that collections are initialised before use)

### The Edge Case Checklist

Before submitting any Digital coding solution, verify these cases:

- **N = 1:** Does your solution handle a single element? (LIS = 1, palindrome = true, prime check needs special case for 1)
- **All same elements:** Does your solution handle uniform arrays? (max subarray = any element, LIS = 1)
- **Maximum constraints:** Would your O(N²) solution TLE at N = 10,000? Use back-of-envelope: 10^8 operations per second, O(N²) at N = 10,000 = 10^8 operations, borderline. At N = 100,000, definitely TLE.
- **Negative numbers:** Does your Kadane's handle all-negative arrays? (yes: return max single element)
- **Empty result:** What if no valid answer exists? (shortest path returns -1, no valid meetings returns 0)

---

## Building Your Problem Recognition Pattern Library

The most important competitive programming skill for TCS Digital is not knowing every algorithm - it is recognising which algorithm a novel problem requires. The following pattern-matching guide maps problem characteristics to algorithm choices.

### "Find the maximum/minimum value satisfying a constraint"

If the answer is monotone (larger answer means easier to satisfy, or smaller means easier), binary search on the answer. The capacity planning problem above is an example.

### "Count ways to do X"

Usually DP. Define the state carefully. Often the answer overflows and requires mod 10^9+7.

### "Group elements that share a property"

Union-Find if the property involves transitivity (if A connects to B and B connects to C, then A connects to C).

### "Shortest path in a graph"

BFS for unweighted graphs (O(N+E)). Dijkstra for non-negative weights (O((N+E) log N)). Bellman-Ford for negative weights (O(NE)).

### "Select a non-overlapping subset with maximum total value"

Sort by end time, then DP (weighted job scheduling). If all weights equal (maximise count), pure greedy (earliest-end-time first).

### "K operations to minimise/maximise"

Often DP with state (current index, operations remaining). The stock trading problems follow this pattern.

### "Sequence with specific growth property"

LIS (strictly increasing) or variant thereof. O(N log N) patience sort.

### "Check if splitting into two groups is possible with a constraint"

Bipartite check (two-colouring via BFS). Graph is bipartite if and only if no odd cycles.

### "String pattern in another string"

KMP for single pattern search (O(N+M)). Rabin-Karp with rolling hash for multiple pattern search or substring matching.

---

## Complete Practice Plan: From Beginner to Digital-Ready in 6 Weeks

This structured plan assumes you have basic programming knowledge (Foundation coding level) and want to reach Digital coding readiness.

### Week 1: Foundation Solidification

Implement from scratch (no reference): prime check, factorial, Fibonacci, palindrome, array sort, binary search, GCD. Each should take under 15 minutes. If any takes longer, repeat that specific one until it is fluent.

End of week target: 6 programs implemented from memory in under 10 minutes each.

### Week 2: Data Structures

Implement from scratch: Stack using array, Queue using array, Singly linked list (insert at head, insert at tail, reverse), Binary search tree (insert, search, in-order traversal).

Practice 5 LeetCode Easy problems per day in your primary language.

### Week 3: Sorting and Searching

Implement: Merge sort, Quick sort, Binary search (first and last occurrence). Understand time complexity of each.

Practice 5 LeetCode Easy/Medium problems per day, focusing on array and string problems.

### Week 4: DP Introduction

Study and implement: Fibonacci with memoisation, coin change (minimum coins), 0/1 knapsack, longest common subsequence. Understand the DP pattern: define state → write recurrence → implement top-down or bottom-up.

Practice 3 LeetCode Medium DP problems per day.

### Week 5: Graphs and Advanced Topics

Implement: BFS, DFS, Dijkstra, topological sort, Union-Find. Solve 1 graph problem per day on LeetCode Medium.

Also this week: study 2-pointer and sliding window techniques. Practice 5 problems total in these categories.

### Week 6: Mock Tests and Problem Variety

Simulate 3 Digital-level coding sessions: 90 minutes, 2 problems, no looking up. After each session, identify which algorithmic category each problem required and ensure you have practiced problems in those categories.

By end of Week 6, you should be able to solve Digital-level Problem 1 reliably (30-35 minutes) and make meaningful progress on Problem 2 (brute-force + partial optimisation).

---

## Final Preparation Reference: Algorithm Complexity Cheat Sheet

| Algorithm | Time | Space | When to Use |
|---|---|---|---|
| BFS / DFS | O(N+E) | O(N) | Traversal, shortest path (unweighted) |
| Dijkstra | O((N+E)logN) | O(N+E) | Shortest path (non-negative weights) |
| Topological Sort | O(N+E) | O(N+E) | Dependency ordering, DAG processing |
| Union-Find | O(α(N)) per op | O(N) | Dynamic connectivity, grouping |
| Knapsack 0/1 | O(N×W) | O(W) | Selection with capacity constraint |
| LIS (O(N logN)) | O(NlogN) | O(N) | Longest increasing subsequence |
| Merge Sort | O(NlogN) | O(N) | Stable sort, count inversions |
| Sliding Window | O(N) | O(1) or O(K) | Contiguous subarray/substring queries |
| Binary Search on Answer | O(NlogAns) | O(N) | Minimise/maximise with monotone check |
| KMP | O(N+M) | O(M) | Pattern search in string |
| Segment Tree | O(logN) per op | O(N) | Range queries with updates |
| Modular Exponentiation | O(logE) | O(1) | Large power computations |

---

## Mindset for the Digital Coding Round

### The Incomplete Solution Mindset

TCS Digital coding is scored by test cases, not by perfect solutions. A candidate who submits a brute-force solution passing 5 of 10 test cases and a partial optimal passing 3 more test cases ends up with 8/10 test cases - a strong partial score.

The candidates who score zero are those who write code that does not compile or produce any output. Getting something on screen is always better than having nothing.

### The Time Allocation Discipline

In 90 minutes with 2-3 problems, the temptation is to spend the full time on one problem trying to make it perfect. This is almost always the wrong strategy. A perfect Problem 1 solution and zero output on Problem 2 typically scores lower than a 70% score on Problem 1 and a 50% score on Problem 2.

Practise the discipline of the "move-on decision": if you have been working on a problem for 45 minutes without a clear path to significant improvement, the remaining 45 minutes are better spent on Problem 2.

### Celebrate Partial Victories

In competitive programming, partial credit is legitimate success. If you have never written a dynamic programming solution before and you get a DP problem correct on 6 of 10 test cases, that is a genuine achievement. The Digital coding section is designed to reward candidates across a skill spectrum - not just the top 1% who solve everything perfectly.

Approach the test not as a binary pass/fail but as a performance on a spectrum where every test case you pass is a point earned. That framing reduces pressure and paradoxically improves performance.

The problems in this workbook are at or above Digital difficulty. Working through them methodically - attempting before reading solutions, implementing both C++ and Java versions, testing edge cases yourself - is the best possible preparation for the real Digital coding round.

---

## Section 11: Segment Tree for Range Queries

### Problem ST-1: The Sales Analytics Dashboard

**Problem statement:**
A sales analytics tool tracks N products with initial revenue values. Two operations are performed:
- `UPDATE i v`: change the revenue of product i to v.
- `QUERY l r`: find the total revenue of products l through r (inclusive, 1-indexed).

Handle Q operations efficiently.

**Constraints:** 1 ≤ N ≤ 100,000, 1 ≤ Q ≤ 100,000.

**Approach:** A naive approach answers queries in O(N) each - too slow for 10^5 queries. A segment tree supports both point updates and range sum queries in O(log N) each.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
typedef long long ll;
const int MAXN = 100005;
ll tree[4*MAXN];

void build(vector<int>& a, int node, int s, int e){
    if(s==e){ tree[node]=a[s]; return; }
    int mid=(s+e)/2;
    build(a, 2*node, s, mid);
    build(a, 2*node+1, mid+1, e);
    tree[node]=tree[2*node]+tree[2*node+1];
}
void update(int node, int s, int e, int idx, int val){
    if(s==e){ tree[node]=val; return; }
    int mid=(s+e)/2;
    if(idx<=mid) update(2*node, s, mid, idx, val);
    else update(2*node+1, mid+1, e, idx, val);
    tree[node]=tree[2*node]+tree[2*node+1];
}
ll query(int node, int s, int e, int l, int r){
    if(r<s||e<l) return 0;
    if(l<=s&&e<=r) return tree[node];
    int mid=(s+e)/2;
    return query(2*node,s,mid,l,r)+query(2*node+1,mid+1,e,l,r);
}

int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    int n, q; cin >> n >> q;
    vector<int> a(n+1);
    for(int i=1;i<=n;i++) cin >> a[i];
    build(a, 1, 1, n);
    while(q--){
        string op; cin >> op;
        if(op=="UPDATE"){
            int i,v; cin>>i>>v;
            update(1,1,n,i,v);
        } else {
            int l,r; cin>>l>>r;
            cout << query(1,1,n,l,r) << "\n";
        }
    }
}
```

**Java Solution:**
```java
import java.util.*;
import java.io.*;
public class Main {
    static long[] tree;
    static int N;
    static void build(int[] a, int node, int s, int e){
        if(s==e){tree[node]=a[s];return;}
        int mid=(s+e)/2;
        build(a,2*node,s,mid); build(a,2*node+1,mid+1,e);
        tree[node]=tree[2*node]+tree[2*node+1];
    }
    static void update(int node,int s,int e,int idx,int val){
        if(s==e){tree[node]=val;return;}
        int mid=(s+e)/2;
        if(idx<=mid) update(2*node,s,mid,idx,val);
        else update(2*node+1,mid+1,e,idx,val);
        tree[node]=tree[2*node]+tree[2*node+1];
    }
    static long query(int node,int s,int e,int l,int r){
        if(r<s||e<l) return 0;
        if(l<=s&&e<=r) return tree[node];
        int mid=(s+e)/2;
        return query(2*node,s,mid,l,r)+query(2*node+1,mid+1,e,l,r);
    }
    public static void main(String[] args) throws Exception {
        BufferedReader br=new BufferedReader(new InputStreamReader(System.in));
        StringTokenizer st=new StringTokenizer(br.readLine());
        N=Integer.parseInt(st.nextToken()); int q=Integer.parseInt(st.nextToken());
        int[] a=new int[N+1];
        st=new StringTokenizer(br.readLine());
        for(int i=1;i<=N;i++) a[i]=Integer.parseInt(st.nextToken());
        tree=new long[4*N+4];
        build(a,1,1,N);
        StringBuilder sb=new StringBuilder();
        while(q-->0){
            st=new StringTokenizer(br.readLine());
            String op=st.nextToken();
            if(op.equals("UPDATE")){
                int i=Integer.parseInt(st.nextToken()),v=Integer.parseInt(st.nextToken());
                update(1,1,N,i,v);
            } else {
                int l=Integer.parseInt(st.nextToken()),r=Integer.parseInt(st.nextToken());
                sb.append(query(1,1,N,l,r)).append('\n');
            }
        }
        System.out.print(sb);
    }
}
```

**Time:** O(N) build, O(log N) per query and update. **Space:** O(N).

---

## Additional Problem: The Palindrome Partitioning (DP on Strings)

### Problem P-1: Minimum Cuts for Palindrome Partitions

**Problem statement:**
A string editor needs to split a string S into the minimum number of substrings such that every substring is a palindrome. Find the minimum number of cuts required.

**Example:** "aab" requires 1 cut: "aa" | "b". "abcba" requires 0 cuts (the whole string is a palindrome).

**Approach:**
Step 1: Precompute isPalin[i][j] = true if S[i..j] is a palindrome.
Step 2: dp[i] = minimum cuts to make S[0..i] all palindromes.
- If S[0..i] is itself a palindrome: dp[i] = 0.
- Otherwise: dp[i] = min(dp[j] + 1) for all j where S[j+1..i] is a palindrome.

**C++ Solution:**
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    ios_base::sync_with_stdio(false); cin.tie(NULL);
    string s; cin >> s;
    int n = s.size();

    // Precompute palindromes using DP
    vector<vector<bool>> isPalin(n, vector<bool>(n, false));
    for(int i=0;i<n;i++) isPalin[i][i]=true;
    for(int i=0;i+1<n;i++) isPalin[i][i+1]=(s[i]==s[i+1]);
    for(int len=3;len<=n;len++)
        for(int i=0;i+len-1<n;i++){
            int j=i+len-1;
            isPalin[i][j]=(s[i]==s[j]&&isPalin[i+1][j-1]);
        }

    vector<int> dp(n, INT_MAX);
    for(int i=0;i<n;i++){
        if(isPalin[0][i]){ dp[i]=0; continue; }
        for(int j=1;j<=i;j++)
            if(isPalin[j][i] && dp[j-1]!=INT_MAX)
                dp[i]=min(dp[i], dp[j-1]+1);
    }
    cout << dp[n-1] << "\n";
}
```

**Java Solution:**
```java
import java.util.*;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.next(); int n = s.length();
        boolean[][] isPalin = new boolean[n][n];
        for(int i=0;i<n;i++) isPalin[i][i]=true;
        for(int i=0;i+1<n;i++) isPalin[i][i+1]=(s.charAt(i)==s.charAt(i+1));
        for(int len=3;len<=n;len++)
            for(int i=0;i+len-1<n;i++){
                int j=i+len-1;
                isPalin[i][j]=(s.charAt(i)==s.charAt(j)&&isPalin[i+1][j-1]);
            }
        int[] dp = new int[n]; Arrays.fill(dp, Integer.MAX_VALUE);
        for(int i=0;i<n;i++){
            if(isPalin[0][i]){ dp[i]=0; continue; }
            for(int j=1;j<=i;j++)
                if(isPalin[j][i]&&dp[j-1]!=Integer.MAX_VALUE)
                    dp[i]=Math.min(dp[i],dp[j-1]+1);
        }
        System.out.println(dp[n-1]);
    }
}
```

**Time:** O(N²) for precomputation and DP. **Space:** O(N²).
**Edge cases:** Empty string (0 cuts), single character (0 cuts), already a palindrome (0 cuts).

---

## Understanding the Test Case Scoring System

### How Partial Credit Actually Works

Each problem in TCS Digital coding is evaluated against a set of test cases. Understanding this scoring model helps you make better submission decisions.

**Typical test case distribution for a Digital problem:**

- Test cases 1-3: Small inputs (N ≤ 10). An O(N³) brute-force will pass these.
- Test cases 4-6: Medium inputs (N ≤ 1,000). An O(N²) solution will pass.
- Test cases 7-9: Large inputs (N ≤ 100,000). O(N log N) or better required.
- Test case 10 (and beyond): Maximum constraints or stress tests. Only optimal solutions pass.

**The submission decision matrix:**

If you have a brute-force (O(N²)) solution and 20 minutes remaining:
- Submit the brute-force immediately (secures test cases 1-6, approximately 60% of marks).
- Spend remaining time attempting the optimal solution.
- If you find the optimal approach, submit the improved version.
- If not, the 60% is secured.

If you have an O(N log N) solution but are not confident it is bug-free:
- Submit it (test cases will reveal bugs without penalty).
- Debug based on which test cases fail.
- Resubmit the corrected version.

**This is why competitive programmers say "submit early and often."** In TCS Digital coding, there is no penalty for wrong submissions. Every submission is risk-free information gathering.

---

## Extended Problem Set: Quick Practice Problems

These shorter problems are at Digital Level 1 difficulty - excellent for warm-up or for testing specific algorithms.

### Quick Problem 1: Find All Prime Factors

Given N (up to 10^12), find and print all prime factors in ascending order.

**Approach:** Trial division up to sqrt(N). For each divisor found, divide out completely.

```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    long long n; cin >> n;
    for(long long i=2; i*i<=n; i++){
        if(n%i==0){
            cout << i << " ";
            while(n%i==0) n/=i;
        }
    }
    if(n>1) cout << n;
    cout << "\n";
}
```

### Quick Problem 2: Count Inversions in an Array

Given an array of N integers, count pairs (i,j) where i < j but arr[i] > arr[j].

**Approach:** Modified merge sort. During merge step, whenever an element from the right half is placed before an element from the left half, it forms inversions with all remaining left-half elements.

```cpp
#include <bits/stdc++.h>
using namespace std;
long long mergeCount(vector<int>& a, int l, int r){
    if(l>=r) return 0;
    int mid=(l+r)/2;
    long long cnt=mergeCount(a,l,mid)+mergeCount(a,mid+1,r);
    vector<int> tmp; int i=l, j=mid+1;
    while(i<=mid&&j<=r){
        if(a[i]<=a[j]) tmp.push_back(a[i++]);
        else{ cnt+=mid-i+1; tmp.push_back(a[j++]); }
    }
    while(i<=mid) tmp.push_back(a[i++]);
    while(j<=r) tmp.push_back(a[j++]);
    for(int k=l;k<=r;k++) a[k]=tmp[k-l];
    return cnt;
}
int main(){
    int n; cin>>n;
    vector<int> a(n); for(int& x:a) cin>>x;
    cout << mergeCount(a,0,n-1) << "\n";
}
```

**Time:** O(N log N). **Space:** O(N).

### Quick Problem 3: Trapping Rain Water

Given N bars of varying heights, compute the total water trapped between them after rain.

**Approach:** Two-pointer from both ends. Maintain max left and max right seen so far.

```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){
    int n; cin>>n;
    vector<int> h(n); for(int& x:h) cin>>x;
    int left=0, right=n-1, maxL=0, maxR=0;
    long long water=0;
    while(left<right){
        if(h[left]<h[right]){
            if(h[left]>=maxL) maxL=h[left];
            else water+=maxL-h[left];
            left++;
        } else {
            if(h[right]>=maxR) maxR=h[right];
            else water+=maxR-h[right];
            right--;
        }
    }
    cout << water << "\n";
}
```

**Time:** O(N). **Space:** O(1).

---

## Your 10-Problem Digital Coding Workout

This is your workout set - one problem from each major category, sequenced from accessible to challenging. Work through one per day over 10 days as a final preparation sprint.

**Day 1:** Warehouse Packing Problem (DP-1: 0/1 Knapsack) - implement without reference.
**Day 2:** Delivery Route Grid (DP-2: Minimum Path Sum) - implement in-place version.
**Day 3:** Network Repair (G-1: BFS Connected Components) - implement with component size tracking.
**Day 4:** Shortest Delivery Route (G-2: Dijkstra) - implement with priority queue, handle disconnected nodes.
**Day 5:** Conference Room Booking (GR-2: Interval Scheduling) - implement and prove the greedy choice.
**Day 6:** Matrix Rotation (AS-1: in-place 90-degree rotation) - implement without extra matrix.
**Day 7:** Maximum Subarray Wraparound (AS-3: Circular Kadane's) - implement and handle all-negative edge case.
**Day 8:** Capacity Planning (BS-1: Binary search on answer) - implement the `canShip` checker and binary search shell.
**Day 9:** Palindrome Partitioning (P-1: String DP) - implement palindrome precomputation first, then the DP.
**Day 10:** Sales Analytics Dashboard (ST-1: Segment Tree) - implement the full build, update, query structure.

For each problem, time yourself. Target: under 35 minutes for Days 1-5, under 45 minutes for Days 6-10. Any problem taking over 50 minutes needs a second attempt the following week.

These 10 problems represent the algorithm families that appear in TCS Digital Advanced Coding. Fluency with all 10 - not just understanding them, but being able to implement them from scratch under time pressure - is what Digital-ready looks like.
