---
layout: post
title: "TCS Digital Quants: Advanced-Level Strategies"
page_title: "TCS Digital Advanced Quantitative and Reasoning Ability - High-Difficulty Preparation with Speed Techniques"
date: 2024-02-03
categories: ["Industry"]
tags: ["TCS Digital aptitude", "TCS Digital quants", "TCS Digital reasoning", "TCS advanced aptitude"]
excerpt: "Crack the hardest sections of TCS Digital. Advanced-level quant and reasoning strategies with speed techniques for 25-minute crunch."
image: "/assets/images/blog/blog-27.webp"
reading_time: 60
author: "Insight Crunch Team"
last_updated: 2026-03-30
---
The TCS Digital Advanced Quantitative and Reasoning sections are where Digital candidates separate themselves from Ninja candidates - and where most Digital aspirants leave marks on the table. The time pressure alone is brutal: 14 to 16 questions in 25 minutes means roughly 90 to 100 seconds per question, and these are not Foundation-level questions. They are multi-step, concept-layered problems that would take a prepared candidate four to five minutes to solve carefully. The only way to score well here is to combine genuine mathematical depth with aggressive time management, shortcut recognition, and the discipline to move on when a question is taking too long. This guide covers every advanced topic with the specific strategies and shortcut techniques that make the difference between a 60% score and a 90% score in this section.

![TCS Guide](/assets/images/blog/blog-27.webp)

## Understanding the Difficulty Jump from Foundation to Advanced

The Foundation numerical section tests whether you know the concepts. The Advanced section tests whether you can apply them under time pressure, in multi-step combinations, and with deliberate trap options designed to penalise the candidate who applies concepts mechanically without thinking.

### What Makes Advanced Quants Harder

**Multi-concept problems.** Foundation questions are typically single-concept: "A sells an item at 20% profit, find the CP." Advanced questions chain concepts: "A sells to B at 20% profit, B sells to C at 15% loss, C sells to D at 25% profit. What is D's cost relative to A's selling price?" This requires three profit/loss calculations in sequence, each using the previous result as the new base.

**Deliberate trap options.** Options are engineered to match intermediate wrong answers. If you stop one step early, you will find your answer in the options - and select it confidently. TCS designs Advanced options this way specifically. The discipline to complete every calculation step before scanning options is non-negotiable.

**Abstract problem framing.** Foundation problems name the concept in the problem text ("find the compound interest"). Advanced problems describe a scenario and you must identify which concept applies: "A sum of money triples itself in 12 years under simple interest. In how many years will it become 7 times itself?" This requires recognising it as a SI relationship problem, extracting the rate, and applying it to a new target.

**Combined topics.** "A pipe fills a tank in 6 hours. Another pipe drains it in 9 hours. If both are open, a third pipe fills the tank in T hours. What is T if the tank fills in 4 hours when all three are open?" - this requires simultaneous equation setup in a time-and-work framework.

### The Time Math

25 minutes for 14-16 questions. Call it 25 minutes for 15 questions = 100 seconds per question average. But in practice:

- About 5 questions will take 45-60 seconds each (straightforward applications once you know the shortcut)
- About 7 questions will take 90-120 seconds each (multi-step but doable with practice)
- About 3 questions will take 180+ seconds even if you know the approach perfectly

The 3 hardest questions will eat your time if you let them. Your strategy must include a decision rule: if a question is still unsolved after 2 minutes, mark your best guess and move on. Banking time on the 5 fast questions (finishing them in 50 seconds each) creates a 50-second buffer per question for the harder ones.

---

## Advanced Quantitative: Permutations and Combinations

P&C at Advanced level moves beyond basic selection and arrangement into problems with multiple constraints operating simultaneously.

### Circular Permutations

Arranging n distinct objects in a circle has (n-1)! arrangements (one object is fixed to eliminate rotational equivalences).

For objects with two sides (e.g., a necklace where flipping is considered the same), the count is (n-1)!/2.

**Problem:** 6 people sit around a circular table. How many arrangements have person A and person B never adjacent?

**Method:** Total circular arrangements = 5! = 120.
Arrangements where A and B ARE adjacent: treat A+B as a single unit. 5 units around a table = 4! = 24. But A and B can swap internally: 24 x 2 = 48.
Arrangements where A and B are NOT adjacent = 120 - 48 = **72**.

**Shortcut:** "Never adjacent" = total - "always adjacent." The always-adjacent calculation uses the "glue" technique - merge constrained items into one unit.

### Arrangements With Restrictions

**Problem:** How many 4-digit numbers can be formed using {1, 2, 3, 4, 5} (repetition allowed) such that the number is divisible by 4?

**Rule for divisibility by 4:** Last two digits form a number divisible by 4.

**Method:** Identify valid last two digits from {1-5, repetition allowed}: 12, 24, 32, 44, 52. That gives 5 valid endings. For each, the first two digits can be any of 5 choices each = 5 x 5 = 25.
Total = 5 x 25 = **125**.

### Distribution Problems

**Problem:** In how many ways can 12 identical chocolates be distributed among 4 children such that each child gets at least 2 chocolates?

**Method:** Give each child 2 first (4 x 2 = 8 used). Remaining 4 chocolates distributed freely among 4 children = stars and bars = C(4+4-1, 4-1) = C(7,3) = **35**.

**Stars and bars formula:** Distributing n identical items among r groups (no restriction) = C(n+r-1, r-1).

---

## Advanced Quantitative: Probability

### Conditional Probability

P(A | B) = P(A ∩ B) / P(B) - the probability of A given B has occurred.

**Problem:** A bag contains 4 red and 6 blue balls. Two balls are drawn without replacement. Given that the first ball drawn is red, what is the probability the second is also red?

P(2nd red | 1st red) = P(both red) / P(1st red) = [C(4,2)/C(10,2)] / [4/10] = [6/45] / [4/10] = [6/45] x [10/4] = 60/180 = **1/3**.

Alternatively, directly: after removing one red, 3 red and 6 blue remain = 9 total. P = 3/9 = 1/3. ✓

### Bayes' Theorem

Bayes' theorem calculates the probability of a cause given an observed effect.

P(Cause | Effect) = P(Effect | Cause) x P(Cause) / P(Effect)

**Problem:** Factory A produces 30% of items, Factory B produces 70%. Factory A has a 5% defect rate; Factory B has a 3% defect rate. An item is found defective. What is the probability it came from Factory A?

P(A | Defective) = P(Defective | A) x P(A) / P(Defective)

P(Defective) = P(D|A)·P(A) + P(D|B)·P(B) = 0.05 x 0.30 + 0.03 x 0.70 = 0.015 + 0.021 = 0.036

P(A | Defective) = (0.05 x 0.30) / 0.036 = 0.015 / 0.036 = **5/12 ≈ 41.7%**

**Shortcut for Bayes':** Use a probability tree. Left branch Factory A (prob 0.3), right branch Factory B (prob 0.7). Under each, branches for defective/non-defective. Multiply along branches to get joint probabilities. Divide the target branch by the sum of all branches with the observed effect (defective).

### Expected Value

Expected value E(X) = sum of (value x probability) for all outcomes.

**Problem:** A game pays Rs. 100 if a die shows 6, Rs. 20 if it shows 4 or 5, and costs Rs. 30 to play. Is this game profitable?

E(payout) = 100 x (1/6) + 20 x (2/6) + 0 x (3/6) = 16.67 + 6.67 + 0 = Rs. 23.33

Since cost = Rs. 30 and E(payout) = Rs. 23.33, expected loss per game = Rs. 6.67. **Not profitable.**

---

## Advanced Quantitative: Geometry and Coordinate Geometry

### Coordinate Geometry Essentials

**Distance between (x1,y1) and (x2,y2):** √[(x2-x1)² + (y2-y1)²]

**Midpoint:** ((x1+x2)/2, (y1+y2)/2)

**Slope:** m = (y2-y1)/(x2-x1)

**Equation of line:** y - y1 = m(x - x1) (point-slope form)

**Area of triangle with vertices (x1,y1), (x2,y2), (x3,y3):**
Area = (1/2)|x1(y2-y3) + x2(y3-y1) + x3(y1-y2)|

**Problem:** Three points are A(1,2), B(4,6), C(7,2). Is triangle ABC a right triangle?

AB = √[(4-1)²+(6-2)²] = √[9+16] = √25 = 5
BC = √[(7-4)²+(2-6)²] = √[9+16] = √25 = 5
AC = √[(7-1)²+(2-2)²] = √36 = 6

Check: AB² + BC² = 25 + 25 = 50 ≠ AC² = 36. Not a right triangle. It is isosceles (AB = BC).

**Shortcut:** Use the distance formula and Pythagorean check. For TCS Advanced, memorise: slope of perpendicular lines have product = -1.

### Circle Problems (Advanced)

**Problem:** A circle has equation x² + y² - 6x + 4y - 12 = 0. Find the centre and radius.

Complete the square: (x-3)² + (y+2)² = 12 + 9 + 4 = 25.
Centre: (3, -2). Radius: 5.

**Standard form:** (x-h)² + (y-k)² = r². Convert from general form (x² + y² + Dx + Ey + F = 0) by completing the square: centre = (-D/2, -E/2), radius = √(D²/4 + E²/4 - F).

### 3D Geometry Basics

**Diagonal of a cuboid** with dimensions l, w, h: d = √(l² + w² + h²)

**Problem:** A box measures 3m x 4m x 5m. What is the length of the longest rod that fits inside?
d = √(9 + 16 + 25) = √50 = 5√2 ≈ 7.07m

**Volume and surface area of a cone:** V = (1/3)πr²h, CSA = πrl where l = slant height = √(r² + h²)

**Problem:** A cone has radius 5 cm and height 12 cm. Find the total surface area.
l = √(25 + 144) = √169 = 13 cm
TSA = πrl + πr² = π(5)(13) + π(25) = 65π + 25π = 90π ≈ 282.7 cm²

---

## Advanced Quantitative: Number Theory

### Euler's Totient Function

φ(n) counts the integers from 1 to n that are coprime to n (share no common factor other than 1).

For prime p: φ(p) = p - 1
For prime power p^k: φ(p^k) = p^k - p^(k-1) = p^(k-1)(p-1)
For general n = p1^a1 x p2^a2 x ...: φ(n) = n x ∏(1 - 1/pi)

**Problem:** Find φ(36).
36 = 2² x 3²
φ(36) = 36 x (1 - 1/2) x (1 - 1/3) = 36 x 1/2 x 2/3 = **12**

Verify: numbers from 1 to 36 coprime to 36 (not divisible by 2 or 3): 1, 5, 7, 11, 13, 17, 19, 23, 25, 29, 31, 35. Count = 12. ✓

**Application:** Euler's theorem states: a^φ(n) ≡ 1 (mod n) when gcd(a,n) = 1. Used in remainder problems with large exponents.

**Problem:** Find the remainder when 7^100 is divided by 36.
φ(36) = 12. Since gcd(7,36) = 1: 7^12 ≡ 1 (mod 36).
100 = 8 x 12 + 4. So 7^100 = (7^12)^8 x 7^4 ≡ 1^8 x 7^4 = 2401 (mod 36).
2401 = 66 x 36 + 25. Remainder = **25**.

### Wilson's Theorem

For prime p: (p-1)! ≡ -1 (mod p).

**Problem:** What is the remainder when 28! is divided by 29?
29 is prime. By Wilson's theorem: 28! ≡ -1 ≡ 28 (mod 29). Remainder = **28**.

### Fermat's Little Theorem

For prime p and integer a not divisible by p: a^(p-1) ≡ 1 (mod p).

**Problem:** Find the remainder when 2^50 is divided by 7.
By FLT: 2^6 ≡ 1 (mod 7) (since 7 is prime and gcd(2,7) = 1, φ(7) = 6).
50 = 8 x 6 + 2. So 2^50 = (2^6)^8 x 2^2 ≡ 1 x 4 = **4** (mod 7).

---

## Advanced Quantitative: Algebra

### Quadratic Equations and Discriminant

For ax² + bx + c = 0:
- Roots: x = (-b ± √(b²-4ac)) / 2a
- Sum of roots = -b/a
- Product of roots = c/a
- Discriminant D = b² - 4ac: D > 0 → two distinct real roots; D = 0 → equal roots; D < 0 → no real roots

**Problem (shortcut approach):** Two roots of x² - 5x + 6 = 0 are p and q. Find p² + q².

Without solving for p and q: p + q = 5, pq = 6.
p² + q² = (p + q)² - 2pq = 25 - 12 = **13**.

**TCS Advanced pattern:** Problems often give algebraic relationships between roots and ask for derived expressions like p³ + q³, p² + q², or (p-q)². Use Vieta's formulas (sum/product of roots) combined with algebraic identities rather than solving for individual roots.

Identity bank:
- p² + q² = (p+q)² - 2pq
- p³ + q³ = (p+q)³ - 3pq(p+q)
- (p-q)² = (p+q)² - 4pq
- p⁴ + q⁴ = (p²+q²)² - 2(pq)²

### Logarithms

**Key rules:**
- log(ab) = log a + log b
- log(a/b) = log a - log b
- log(aⁿ) = n log a
- log_b(a) = log a / log b (change of base)
- log_a(a) = 1
- log_a(1) = 0

**Problem:** If log 2 = 0.301, find log 8000.
log 8000 = log (8 x 1000) = log 8 + log 1000 = 3 log 2 + 3 = 3(0.301) + 3 = 0.903 + 3 = **3.903**

**Problem:** If log_2(x) + log_4(x) = 6, find x.
Convert log_4(x) = log_2(x) / log_2(4) = log_2(x) / 2.
Let log_2(x) = t: t + t/2 = 6 → 3t/2 = 6 → t = 4 → x = 2⁴ = **16**.

### Inequalities

**Problem:** Find all integer values of x such that x² - 5x + 6 < 0.
Factor: (x-2)(x-3) < 0.
Product is negative when one factor is positive and the other is negative: 2 < x < 3.
No integers exist strictly between 2 and 3. **No integer solutions.**

For TCS Advanced, inequality problems typically ask for the range of valid values and may combine with modulus:
|2x - 3| < 5 → -5 < 2x - 3 < 5 → -2 < 2x < 8 → **-1 < x < 4**.

---

## Advanced Quantitative: Complex Data Interpretation

Advanced DI in TCS Digital involves multi-variable datasets, incomplete information that must be inferred, and calculations that require combining data from two or more charts.

### Multi-Graph Analysis Strategy

When a DI set shows two or more charts (e.g., a bar chart of revenue and a line chart of growth percentage, or a table of market share and a pie chart of total market size), the questions typically require:

1. Finding absolute values from percentage data (market share % x total market size)
2. Comparing rates of change across two variables that are measured on different scales
3. Inferring missing values from given constraints ("if total is 100 and three segments are shown, the fourth is 100 minus the sum of the three")

**Three-step approach for complex DI:**
Step 1: Identify what each chart measures (units, scale, what the axes represent)
Step 2: Note which questions require data from one chart vs two charts combined
Step 3: For combined calculations, extract the needed data points first before computing

### Approximation Techniques for DI Speed

Advanced DI under time pressure requires comfort with approximation:

- For percentage calculations: replace exact values with round numbers. Revenue of Rs. 4,87,320 can be approximated as Rs. 490,000 for quick estimation; the exact answer will be close to 4.9 times any quantity expressed in lakhs.
- For ratio comparisons: convert to comparable denominators mentally. Comparing 47/312 with 38/256: 47/312 ≈ 15%; 38/256 ≈ 15%. These are approximately equal, so look for the question that asks which is larger (neither is clearly dominant - need exact values only if the question distinguishes between very close results).
- For CAGR (Compound Annual Growth Rate) estimation: for small rates, CAGR ≈ (Final/Initial)^(1/n) - 1. Use logarithms or the rule of 72 for quick mental calculations.

**Problem (compound DI):** A table shows company revenue for four divisions in two years. A separate pie chart shows the percentage contribution of each division to total company profit in Year 2. If Division A's profit margin (profit/revenue) in Year 2 is 25%, and Division A contributed 40% of total company profit, what is the total company profit?

Method: Division A's revenue (from table) x 25% = Division A's profit. Division A's profit = 40% of total profit. Solve for total profit.

If Division A revenue = Rs. 80 crore:
Division A profit = 80 x 0.25 = Rs. 20 crore.
Total profit = 20 / 0.40 = **Rs. 50 crore**.

### Series Problems at Advanced Level

Advanced series questions use multi-level differences, interleaved series, and operational patterns (each term is derived from previous terms through a non-obvious operation).

**Multi-level difference series:** Find the next term: 2, 5, 10, 17, 26, 37, ?
First differences: 3, 5, 7, 9, 11... (arithmetic with d=2)
Second differences: 2, 2, 2, 2... (constant)
Next first difference = 13. Next term = 37 + 13 = **50**.

**Interleaved series (two alternating patterns):** Find the next term: 1, 4, 3, 8, 9, 16, 27, ?
Odd positions: 1, 3, 9, 27... (multiply by 3 each time)
Even positions: 4, 8, 16... (multiply by 2 each time)
Next term is at odd position (8th): 27 x 3 = **81**.

Wait - let me recount: positions 1,2,3,4,5,6,7 → terms 1,4,3,8,9,16,27. The 8th position would be even: 16 x 2 = **32**.

**Mixed-operation series:** 3, 7, 15, 31, 63, ?
Each term = 2 x previous + 1. Next: 2 x 63 + 1 = **127**.

**Cube and square combinations:** 2, 9, 28, 65, 126, ?
Terms: 1³+1, 2³+1, 3³+1, 4³+1, 5³+1 = 6³+1 = **217**.

---

## Advanced Reasoning: Analytical Puzzles

### Multi-Variable Arrangement Puzzles

These puzzles assign multiple attributes (name, city, profession, colour) to multiple people through a set of conditions. They are the most time-consuming question type in Advanced Reasoning.

**Approach framework:**
1. Create a grid with people as rows and attributes as columns
2. Mark confirmed assignments with a tick and eliminated options with an X
3. Apply each condition to fill as many cells as possible
4. Look for cells where only one option remains (forced assignment)
5. Use the forced assignments to unlock further cells

**Time management rule:** Multi-variable puzzles that require a full grid (5 people x 4 attributes) take 4-6 minutes when solved correctly. If you are at minute 2 and have not placed at least half the assignments, do not continue - guess and move on. These puzzles are designed to punish candidates who start them without the skills to finish quickly.

**A 4-person puzzle condensed example:**

Four friends - Aryan, Bhuvan, Chirag, Dhruv - each have a different profession (Engineer, Doctor, Lawyer, Accountant) and own different cars (Swift, Innova, WagonR, Creta).

Conditions:
(i) Aryan is not an Engineer and does not own a Swift.
(ii) Bhuvan is either a Lawyer or owns an Innova.
(iii) Chirag is an Accountant.
(iv) The Doctor owns a Creta.
(v) Dhruv owns a WagonR.

From (v): Dhruv → WagonR.
From (iv): Doctor owns Creta. Since Dhruv owns WagonR, Dhruv is not the Doctor.
From (iii): Chirag → Accountant. So Chirag is not the Doctor.
From (i): Aryan is not Engineer. So Aryan is either Doctor or Lawyer.
If Aryan is Doctor, Aryan owns Creta.
From (i): Aryan doesn't own Swift. Aryan owns Creta. ✓ Consistent.
From (ii): Bhuvan is Lawyer or owns Innova. If Aryan is Doctor, remaining professions for Bhuvan: Engineer or Lawyer. Dhruv: Engineer or Lawyer. If Bhuvan is Lawyer, (ii) satisfied.
Then Dhruv is Engineer. Remaining cars: Swift and Innova for Bhuvan and Chirag. Bhuvan owns Innova or is Lawyer - if Bhuvan is Lawyer, no car restriction from (ii). So Bhuvan could own Swift, and Chirag owns Innova. Valid.

Final: Aryan - Doctor - Creta; Bhuvan - Lawyer - Swift; Chirag - Accountant - Innova; Dhruv - Engineer - WagonR.

### Complex Syllogisms (3+ Statements)

At Advanced level, syllogism problems add a third premise and sometimes ask whether conclusions follow when combined with the negative of one statement.

**Framework:** Draw Venn diagrams for three-statement syllogisms. With three sets (A, B, C), draw three interlocking circles. Apply each statement as an inclusion (all A are B = entire A circle inside B circle) or partial inclusion (some A are B = circles overlap but neither contains the other).

**Problem:**
Statements:
(1) All politicians are corrupt.
(2) Some corrupt people are criminals.
(3) No criminal is poor.

Conclusions:
(I) Some politicians are criminals.
(II) No politician is poor.
(III) Some corrupt people are not poor.

Analysis:
From (1): All politicians are corrupt. Politicians ⊂ Corrupt.
From (2): Some corrupt people are criminals. Corrupt ∩ Criminal ≠ ∅.
The overlap between corrupt and criminal may or may not include the politician subset.
Conclusion (I): Some politicians are criminals. NOT CERTAIN - the corrupt criminals may be non-politician corrupt people.
From (3): No criminal is poor. Criminal ∩ Poor = ∅.
From (2): Some corrupt people are criminals. Those corrupt people who are criminals are not poor (from 3).
Conclusion (III): Some corrupt people are not poor. TRUE - the corrupt criminals are not poor.
Conclusion (II): No politician is poor. NOT CERTAIN - politicians are corrupt, but not necessarily among the corrupt criminals. A politician could be corrupt without being a criminal, and the "no criminal is poor" statement doesn't apply to non-criminal politicians.

Answer: Only Conclusion (III) definitely follows.

### Advanced Data Sufficiency

Data sufficiency questions at Advanced level use more complex relationships where determining "sufficient" requires actually working through the math rather than recognising obvious patterns.

**Template for answering:**
(A) Statement 1 alone is sufficient
(B) Statement 2 alone is sufficient
(C) Both statements together are sufficient but neither alone is sufficient
(D) Each statement alone is sufficient
(E) Neither alone nor both together are sufficient

**Problem:** Is x > 0?
Statement 1: x² > x
Statement 2: x³ > x²

Analysis:
Statement 1: x² > x → x² - x > 0 → x(x-1) > 0 → x < 0 OR x > 1. So x could be positive (x > 1) or negative (x < 0). NOT sufficient to confirm x > 0.
Statement 2: x³ > x² → x²(x-1) > 0. Since x² ≥ 0 and equals 0 only when x = 0 (but then x³ = x² = 0, contradiction), we need x² > 0 AND x > 1, OR x² < 0 (impossible). So x > 1, which means x > 0. SUFFICIENT.

Answer: **(B) Statement 2 alone is sufficient.**

### Critical Reasoning at Advanced Level

Critical reasoning questions present an argument and ask candidates to: strengthen it, weaken it, identify its assumption, or identify its logical flaw.

**Strengthen a conclusion:** Find an answer choice that makes the argument's conclusion more likely to be true. It should provide additional support for the reasoning or rule out an alternative explanation.

**Weaken a conclusion:** Find an answer choice that makes the argument's conclusion less likely. It should attack the premises, introduce a confounding factor, or show that the evidence supports a different conclusion.

**Identify the assumption:** The conclusion would collapse if this unstated premise were false. The correct answer is something the argument takes for granted but never explicitly states.

**Common logical flaw types tested:**
- Circular reasoning (conclusion restates the premise)
- Correlation-causation error ("Sales increased after we changed the logo, so the logo change caused the increase")
- False dichotomy ("Either we raise prices or cut staff")
- Hasty generalisation (small sample to broad conclusion)
- Ad hominem (attacking the source rather than the argument)

**Problem:** "Our new fertiliser increased crop yield by 30% in trials on 5 test farms. Therefore, all farmers should use this fertiliser to improve their yields."

Identify the flaw:
The conclusion (all farmers) is a generalisation from a small sample (5 farms). The trial conditions (soil type, climate, crop variety) may not represent all farming contexts. This is a **hasty generalisation** - drawing a broad conclusion from insufficient sample size.

A correct weakener: "The 5 test farms were all located in the same geographic region and had identical soil profiles."

---

## Advanced Reasoning: Input-Output Problems

Input-output questions describe a "machine" that transforms an input through a sequence of steps. Candidates must trace the transformation pattern and answer questions about intermediate steps or the final output.

### Identifying the Pattern

Most TCS Advanced input-output patterns involve one or two of: alphabetical shift (each letter moves n positions forward/backward), numeric sorting (numbers rearranged by value), word position swap (words change positions by a rule), or numerical transformation (each number undergoes an arithmetic operation).

**Example:**
Input: cat 48 dog 25 run 17 jump 63
Step 1: 17 cat 48 dog 25 run jump 63
Step 2: 17 cat 25 dog 48 run jump 63
Step 3: 17 cat 25 dog 48 run 63 jump

Pattern: Numbers are being sorted in ascending order from the left, one step at a time, while words maintain relative position between numbers.

Question: What is Step 4?
Step 4: 17 cat 25 dog 48 63 run jump (numbers fully sorted: 17, 25, 48, 63; words maintain relative positions between and after numbers)

### Two-Operation Patterns

Some input-output problems apply two simultaneous operations per step:

Input: 8 red 12 blue 5 green 20 yellow
Step 1: 20 red 12 blue 8 green 5 yellow

Pattern: Numbers are being sorted in descending order. Words are paired with numbers but maintain their relative sequence.

---

## Managing the 25-Minute Time Pressure

This section addresses the central challenge of TCS Digital Advanced sections: the time crunch is more limiting than the content difficulty for most candidates.

### The Time Budget System

Allocate your 25 minutes before starting the section, not as you go:

**Tier 1 questions (target: 60-75 seconds each):** DI questions once the chart is understood, straightforward P&C, simple probability, basic coordinate geometry. Aim for 5-6 such questions. If you finish each in 65 seconds, you spend 6.5 minutes total and earn 5-6 marks efficiently.

**Tier 2 questions (target: 90-120 seconds each):** Multi-step arithmetic chains, quadratic root properties, logarithm problems, conditional probability. Aim for 6-7 such questions. These take 10-14 minutes.

**Tier 3 questions (target: 120-150 seconds, maximum):** Complex analytical puzzles, three-statement syllogisms, input-output with non-obvious patterns. Aim for 3-4 such questions. Budget 90 seconds per question; if a Tier 3 question is not resolving by 90 seconds, guess and move on.

Total: approximately 5 x 70 + 6 x 100 + 4 x 120 = 350 + 600 + 480 = 1430 seconds ≈ 24 minutes. The remaining 60 seconds is your buffer.

### The 2-Minute Rule

If any question has consumed 2 minutes without a confirmed answer, stop immediately. Mark your best guess and move. No single question is worth 3 minutes in a 25-minute section. The candidates who score 85%+ in Advanced sections are not the ones who solve every question perfectly - they are the ones who solve 12 out of 15 correctly in time while guessing on the remaining 3.

### Triage in the First 90 Seconds

Before attempting any question, spend 90 seconds reading all questions and mentally categorising them as Tier 1, 2, or 3. Sequence your attempts: start with all Tier 1 questions (even if they appear later in the set), move to Tier 2, and spend whatever time remains on Tier 3.

This is counterintuitive - most candidates answer questions in the order presented. But the order TCS presents questions is not optimised for your time management. Your sequence should be optimised for your scores.

### Shortcut Techniques That Save 30-60 Seconds Per Question

**Percentage shortcuts:** To find 37.5% of any number, recognise 37.5% = 3/8. Divide by 8 and multiply by 3. Much faster than (37.5/100) x N.

Common percentage-fraction equivalents to memorise:
- 12.5% = 1/8
- 16.67% = 1/6
- 33.33% = 1/3
- 37.5% = 3/8
- 62.5% = 5/8
- 66.67% = 2/3
- 87.5% = 7/8

**Ratio shortcuts:** For mixture problems, use alligation directly. Place the two source concentrations and the required concentration in the alligation cross: the difference between required and each source gives the ratio of the two sources (in reverse). This replaces setting up simultaneous equations.

**P&C shortcuts:** For problems asking "how many 4-letter words from MATHS," first check for repeated letters. No repeats here → 5 x 4 x 3 x 2 = 120. If the question says "distinct letters only" and the word has repeated letters, divide by the factorial of each repeated letter's count.

**Cube and square recognition:** Know perfect cubes up to 20³ = 8000 and perfect squares up to 50² = 2500. Many Advanced quant problems have answers that are perfect squares or cubes, and recognising the form instantly eliminates the need to calculate.

**Unit digit shortcuts:** For large exponents, the unit digit of any base cycles with a period of at most 4. Unit digits of powers: 2 cycles 2,4,8,6; 3 cycles 3,9,7,1; 4 cycles 4,6; 7 cycles 7,9,3,1; 8 cycles 8,4,2,6; 9 cycles 9,1. Find position in cycle using exponent mod 4 (or mod 2 for 4 and 9).

### Mental Arithmetic Techniques

**Squaring numbers near 50:** (50 + n)² = 2500 + 100n + n². So 53² = 2500 + 300 + 9 = 2809. Much faster than long multiplication.

**Multiplication by 11:** For a 2-digit number AB: A, A+B, B (with carries). 47 x 11 = 4, 4+7, 7 = 4, 11, 7 → 517. Carry the 1: 517.

**Vedic multiplication for 2-digit numbers:** (a+b)(c+d) expanded, or use the cross-method: first digit product + middle cross + last digit product.

**Approximation for complex fractions:** 127/9 - instead of dividing, note 9 x 14 = 126, so 127/9 ≈ 14.11. Use this pattern for quickly estimating quotients.

---

## Practice Problem Set: Digital Advanced Level

These 15 problems simulate the Advanced Quants and Reasoning section. Attempt each under the time budget framework: classify Tier, attempt Tier 1 first, and use the 2-minute rule.

**Q1 (P&C, Tier 1):** How many ways can the letters of LEVEL be arranged so that the two L's are never together?
Total arrangements with repeats: 5!/2! = 60 (two L's are repeated).
Arrangements with L's together: treat LL as one unit: 4! = 24.
Never together: 60 - 24 = **36**.

**Q2 (Probability, Tier 2):** A box has 5 red and 7 green balls. Two draws are made without replacement. Given the first draw was green, what is the probability the second is red?
After removing one green: 5 red, 6 green, 11 total. P = 5/11.

**Q3 (Number Theory, Tier 2):** What is φ(48)?
48 = 2⁴ x 3. φ(48) = 48 x (1-1/2) x (1-1/3) = 48 x 1/2 x 2/3 = **16**.

**Q4 (Coordinate Geometry, Tier 1):** Find the distance between (-3, 4) and (2, -8).
d = √[(2-(-3))² + (-8-4)²] = √[25 + 144] = √169 = **13**.

**Q5 (Logarithm, Tier 2):** If log₂ = 0.301, find the number of digits in 2^25.
Number of digits = floor(log(2^25)) + 1 = floor(25 x 0.301) + 1 = floor(7.525) + 1 = 7 + 1 = **8**.

**Q6 (Algebra, Tier 1):** Roots of x² - 7x + 10 = 0 are p and q. Find p² + q² - pq.
p+q = 7, pq = 10. p² + q² = 49 - 20 = 29. p² + q² - pq = 29 - 10 = **19**.

**Q7 (DI inference, Tier 2):** A company's quarterly profits are Rs. 12L, Rs. 15L, Rs. 18L, Rs. 21L for Q1-Q4. What is the year's profit as a percentage increase over the previous year if the previous year's total was Rs. 55L?
Current year: 12+15+18+21 = 66L. Increase = 11L. Percentage = 11/55 x 100 = **20%**.

**Q8 (Series, Tier 1):** Find the missing term: 4, 9, 25, 49, ?, 169.
Sequence: 2², 3², 5², 7², 11², 13². These are squares of prime numbers. Next prime after 7 is 11: 11² = **121**.

**Q9 (Syllogism, Tier 2):**
Statements: All doctors are professionals. Some professionals are rich.
Conclusion I: Some doctors are rich.
Conclusion II: Some professionals are doctors.
Analysis: Conclusion I cannot be confirmed - the "some professionals who are rich" may not overlap with the doctor subset. Conclusion II follows from "All doctors are professionals" (converting: some professionals are doctors). Answer: Only **Conclusion II follows**.

**Q10 (Data Sufficiency, Tier 2):** Is x a perfect square?
Statement 1: x is divisible by 4.
Statement 2: √x is an integer.
Statement 1: 4 is divisible by 4 and is a perfect square; 12 is divisible by 4 and is not. NOT sufficient.
Statement 2: If √x is an integer, x = integer², which IS a perfect square by definition. SUFFICIENT.
Answer: **Statement 2 alone is sufficient (B)**.

**Q11 (Critical Reasoning, Tier 2):**
Argument: "Our city's accident rate dropped 15% after the traffic camera system was installed. Therefore, traffic cameras cause fewer accidents."

Identify the flaw: This assumes correlation implies causation. The 15% drop could be due to other factors: increased police presence, road improvements, seasonal variation, or public awareness campaigns that coincided with camera installation. This is a **correlation-causation fallacy**.

**Q12 (P&C Advanced, Tier 3):** 8 people need to be divided into two teams of 4. How many ways are possible?
Select 4 from 8 for Team 1: C(8,4) = 70. The remaining form Team 2 automatically.
But the two teams are indistinguishable (Team 1 and Team 2 have no difference): divide by 2.
Answer: 70/2 = **35 ways**.

**Q13 (Euler's theorem, Tier 3):** Find the remainder when 3^102 is divided by 10.
Unit digit of powers of 3 cycle: 3,9,7,1 (period 4). 102 mod 4 = 2. So unit digit = 9. Remainder = **9**.

**Q14 (Input-Output, Tier 2):**
Input: 15 apple 32 mango 8 orange 45 grape
Step 1: 8 apple 32 mango 15 orange 45 grape
Step 2: 8 apple 15 mango 32 orange 45 grape

Pattern: Numbers sorted ascending left to right, words maintain relative order.
What is the output after all steps are complete? **8 apple 15 mango 32 orange 45 grape** (numbers fully sorted, words unchanged in relative sequence).

**Q15 (Geometry, Tier 1):** A cylinder has radius 7 cm and height 10 cm. Find the total surface area. (Use π = 22/7)
TSA = 2πr(r + h) = 2 x (22/7) x 7 x (7 + 10) = 2 x 22 x 17 = **748 cm²**.

---

## Topic Priority for Advanced Sections

Not all Advanced topics appear with equal frequency. Prioritise your preparation using this ranking:

**Highest frequency and highest ROI:**
1. Data Interpretation (multi-variable) - appears in virtually every Advanced section
2. Permutations and Combinations with restrictions - appears frequently, high mark value
3. Probability (conditional and expected value) - reliable appearance
4. Analytical Puzzles (multi-variable arrangements) - most time-consuming but high mark yield if mastered
5. Advanced Syllogisms and Data Sufficiency - appear consistently

**Medium frequency:**
6. Coordinate geometry and circle problems
7. Logarithms and algebraic root properties
8. Complex series (multi-level, interleaved)
9. Critical Reasoning

**Lower frequency but high value when present:**
10. Number Theory (Euler's theorem, Fermat's Little Theorem) - appears in harder rounds
11. 3D Geometry
12. Input-Output (advanced patterns)

Candidates with 3-4 weeks to prepare should cover all of 1-6 thoroughly, 7-9 at concept level, and 10-12 as awareness only (recognise the type and attempt with partial knowledge rather than skipping entirely).

---

## Building Speed: The 10-Day Advanced Sprint

If you have limited preparation time and specifically need to improve your Advanced Quants and Reasoning score, this 10-day intensive sprint targets the highest-impact areas.

**Days 1-2:** Advanced DI. Practice two multi-graph DI sets per day (one bar+line combination, one table+pie combination). Focus on speed: extract data without reading every data point, answer questions using approximation where exact answers would take too long.

**Days 3-4:** P&C and Probability (Advanced). Cover circular permutations, restricted arrangements, conditional probability, Bayes' theorem, and expected value. Practice 8 problems per day, timed.

**Days 5-6:** Analytical Puzzles and Syllogisms. Build the grid framework for multi-variable puzzles. Practice complete 5-person, 4-attribute puzzles under 5-minute time limit. Drill Venn diagram syllogisms until pattern recognition is automatic.

**Days 7-8:** Algebra (quadratics, logarithms) and Number Theory. Practice using Vieta's formulas. Practice logarithm change-of-base problems. Cover Euler's theorem and Fermat's Little Theorem for remainder problems.

**Days 9-10:** Full mock sections. Two complete 25-minute Advanced sections per day. After each, analyse: which questions took more than 2 minutes? What category were they? Were your Tier classifications accurate? Use this data to calibrate your triage instinct.

The 10-day sprint will not produce the same results as the full 45-day preparation, but it will meaningfully improve speed and triage accuracy - the two factors most responsible for score gaps in this section.

---

## Frequently Asked Questions: TCS Digital Advanced Aptitude

**Is the Advanced section adaptive (does question difficulty change based on performance)?**
The TCS NQT Foundation section is non-adaptive. The Advanced section at Digital level presents the same question set to all candidates in a given drive - the difficulty is uniformly high, not adjusted per candidate. Your score reflects how many of these fixed questions you answered correctly and completely within the time limit.

**Is it possible to skip the Advanced section and still get a Digital profile?**
No. The Advanced sections (Quants, Reasoning, Coding) are what differentiate Digital candidates from Ninja candidates. Skipping or performing poorly in the Advanced sections while performing well in Foundation sections typically results in Ninja profile, not Digital.

**How much harder is Advanced Reasoning compared to Advanced Quants?**
This is subjective and varies by individual background. Candidates with strong mathematical training often find Advanced Quants more accessible. Candidates with logical and verbal strengths often find Advanced Reasoning more tractable. Most candidates have one stronger section - identify yours through diagnostic mock tests and invest extra time in the weaker one.

**What is the best single investment of preparation time for Digital Advanced?**
Data Interpretation. It appears in every Advanced Quants section, carries the highest question concentration of any topic, and improves the most rapidly with focused practice. A candidate who can handle multi-graph DI at speed has a significant baseline score advantage before touching any other Advanced topic.

**Should I guess on questions I cannot solve?**
For TCS Advanced sections with negative marking: guess only when you can eliminate at least two options, making your expected value positive. For sections without negative marking: always guess. Never leave a question blank.

**How much does Advanced section performance actually affect Digital vs Ninja profile assignment?**
The Advanced sections are the primary differentiator. TCS's internal scoring model weights Advanced performance heavily for profile determination. A candidate who scores at Foundation level only (performing well in Foundation Numerical, Verbal, Reasoning but poorly in all three Advanced sections) will almost certainly receive Ninja. Strong Advanced performance is not sufficient alone (Foundation must clear threshold) but is necessary for Digital.

The investment in Advanced preparation is not just about a higher salary at entry - it is about a faster growth trajectory, more challenging initial projects, and the professional network and reputation that comes from being identified as a high-calibre technical candidate from Day 1 of your TCS career.

---

## Advanced Quantitative: Time, Speed, Distance (Advanced Applications)

### Relative Motion in Complex Scenarios

**Problem:** Two trains start simultaneously from stations A and B towards each other. Train 1 travels at 72 km/h; Train 2 at 54 km/h. The distance between A and B is 315 km. After they meet, Train 1 takes T₁ hours to reach B and Train 2 takes T₂ hours to reach A. Find the ratio T₁ : T₂.

**Key formula:** When two objects moving towards each other meet, the ratio of times they take to cover the remaining distance (after meeting) equals the inverse square of their speed ratio.

T₁ : T₂ = v₂² : v₁² = 54² : 72² = 2916 : 5184 = **9 : 16**

Shortcut derivation: Let them meet after time t. At meeting: Train 1 covered 72t km; Train 2 covered 54t km. Remaining distance for Train 1 = 54t km (at speed 72 km/h → time T₁ = 54t/72 = 3t/4). Remaining for Train 2 = 72t km (at speed 54 km/h → T₂ = 72t/54 = 4t/3). Ratio: (3t/4) : (4t/3) = 9:16. ✓

### Circular Track Problems

**Problem:** A and B run around a circular track of 400m. A's speed is 10 m/s; B's speed is 6 m/s. They start simultaneously from the same point in the same direction. How many times do they meet before A completes 5 full rounds?

Relative speed (same direction) = 10 - 6 = 4 m/s. Time for A to complete 5 rounds = 5 x 400/10 = 200 seconds. In 200 seconds, the relative distance covered = 4 x 200 = 800m = 2 laps. They meet **2 times** (each time relative distance = 400m).

**Critical rule for circular track:** When running in the same direction, they meet when the faster runner gains exactly one full lap. When running in opposite directions, they meet when their combined distance equals one full lap.

### Boats and Streams

**Problem:** A boat's speed in still water is 12 km/h. In 3 hours, it covers 42 km downstream. In how long will it cover 30 km upstream?

Downstream speed = 42/3 = 14 km/h. Stream speed = 14 - 12 = 2 km/h. Upstream speed = 12 - 2 = 10 km/h. Time upstream for 30 km = 30/10 = **3 hours**.

**Shortcut:** Downstream = boat + stream; upstream = boat - stream. Always identify which of the three (boat, downstream, upstream, stream) you know and which you need.

---

## Advanced Quantitative: Mixtures and Alligation (Advanced)

### Alligation for Complex Mixtures

**Problem:** A 40-litre solution contains acid and water in the ratio 3:5. How much pure acid must be added to make the ratio 4:5?

Original acid: 40 x 3/8 = 15 litres. Original water: 25 litres. Let x litres of acid be added.
New ratio: (15 + x) / 25 = 4/5 → 5(15 + x) = 100 → 75 + 5x = 100 → x = **5 litres**.

**Successive dilution formula:** If a container has V litres of liquid A, and n litres are removed and replaced with liquid B, repeated k times:
Remaining A = V x ((V-n)/V)^k

**Problem:** A 50-litre cask contains wine. 10 litres are removed and replaced with water, repeated 3 times. How much wine remains?
Remaining wine = 50 x (40/50)³ = 50 x (4/5)³ = 50 x 64/125 = 3200/125 = **25.6 litres**.

---

## Advanced Quantitative: Interest (Advanced Applications)

### Compound Interest with Half-Yearly Compounding

When interest is compounded half-yearly: rate becomes r/2 per period, number of periods becomes 2n.

**Problem:** Rs. 8,000 is invested at 10% per annum compounded half-yearly for 1.5 years. Find the compound interest.

Rate per half-year = 5%. Number of half-years = 3.
Amount = 8000 x (1.05)³ = 8000 x 1.157625 = Rs. 9261. CI = 9261 - 8000 = **Rs. 1261**.

### Equal Installments for Loan Repayment

**Problem:** A loan of Rs. 10,000 at 10% per annum compound interest is repaid in 2 equal annual installments. Find each installment.

Let installment = x. Present value of installments = Present value of loan:
x/(1.1) + x/(1.1)² = 10000
x x (1/1.1 + 1/1.21) = 10000
x x (0.9091 + 0.8264) = 10000
x x 1.7355 = 10000
x = 10000/1.7355 ≈ **Rs. 5762**

---

## Advanced Quantitative: Geometry (Triangles and Circles - Advanced)

### Similar Triangles and Area Ratios

**Key property:** If two triangles are similar with sides in ratio k:1, their areas are in ratio k²:1.

**Problem:** Two similar triangles have perimeters in ratio 4:3. The area of the larger triangle is 48 cm². Find the area of the smaller.

Sides ratio = 4:3. Area ratio = 16:9. Area of smaller = 48 x (9/16) = **27 cm²**.

### Inscribed and Circumscribed Circles

For an equilateral triangle with side a:
- Inradius (r) = a/(2√3) = a√3/6
- Circumradius (R) = a/√3 = a√3/3
- R = 2r

**Problem:** An equilateral triangle has side 6 cm. Find the radius of its inscribed circle.
r = 6/(2√3) = 3/√3 = √3 ≈ **1.73 cm**.

### Angle in a Semicircle (Thales' Theorem)

Any angle inscribed in a semicircle that subtends the diameter is exactly 90°.

**Problem:** In a circle with diameter AB = 10 cm, C is a point on the circle. If AC = 6 cm, find BC.
Since AB is a diameter, angle ACB = 90° (Thales' theorem). By Pythagoras: BC = √(AB² - AC²) = √(100 - 36) = √64 = **8 cm**.

---

## Advanced Reasoning: Pattern Recognition

### Numerical Pattern Matrices (3x3 Grid)

Pattern matrix questions show a 3x3 grid with 8 numbers and one missing cell. The pattern operates across rows, columns, or both.

**Common patterns:**
- Row sums are constant
- Column products are equal
- Each row follows an arithmetic or geometric progression
- The pattern operates on digit sums or digit products
- The number equals the sum/product/difference of the other two in its row or column

**Example grid:**
```
4   9   16
25  36   ?
64  81  100
```

Looking at each row: 4=2², 9=3², 16=4²; 25=5², 36=6², ?=7²=49; 64=8², 81=9², 100=10².
Pattern: perfect squares in sequence. Missing value = **49**.

**Example (operations-based grid):**
```
6   2   12
8   3   24
5   4    ?
```

Pattern: column 1 x column 2 = column 3. 6x2=12, 8x3=24, 5x4=20. Missing = **20**.

### Letter Series With Positional Logic

Some letter series require tracking both the letter position and its distance to the next letter:

Z A Y B X C W D V E ?

Pattern: Alternating forward (from Z backward: Z,Y,X,W,V) and forward (from A: A,B,C,D,E). Next letter continues the second sequence: F. Answer: **F**.

More complex: AZ, CX, EV, GT, ?
First letter: A, C, E, G (+2 each time → next: I)
Second letter: Z, X, V, T (-2 each time → next: R)
Answer: **IR**.

---

## Advanced Reasoning: Logical Deductions

### Venn Diagram Problems With Three Sets

**Problem:** In a group of 100 students: 70 study Maths, 55 study Physics, 45 study Chemistry. 30 study both Maths and Physics, 20 study both Physics and Chemistry, 25 study both Maths and Chemistry. 10 study all three.

How many study exactly one subject?

Using inclusion-exclusion: M ∪ P ∪ C = 70+55+45 - 30-20-25 + 10 = 105.
This means some students are counted who study none? Since 100 students total and the union is 105 - this implies 5 students study none (they are outside the union). Alternatively, the union total is limited to 100 means students who study at least one subject = 100 - those studying none.

If all 100 study at least one subject: total in exactly one = total - exactly two - exactly three.
Exactly two = (30-10) + (20-10) + (25-10) = 20 + 10 + 15 = 45.
Exactly all three = 10.
Exactly one = 100 - 45 - 10 = **45**.

Verify: exactly one Maths = 70 - 30 - 25 + 10 = 25. Exactly one Physics = 55 - 30 - 20 + 10 = 15. Exactly one Chemistry = 45 - 20 - 25 + 10 = 10. Total = 25 + 15 + 10 = 50. Hmm - that's 50, not 45. Let me recheck the formula.

Actually: exactly one subject = (those in M only) + (P only) + (C only)
M only = 70 - (M∩P) - (M∩C) + (M∩P∩C) = 70 - 30 - 25 + 10 = 25
P only = 55 - 30 - 20 + 10 = 15
C only = 45 - 20 - 25 + 10 = 10
Total exactly one = 25 + 15 + 10 = **50**.

**Key takeaway:** Always derive the formula carefully. "Exactly one" requires subtracting those in two sets and adding back those in all three (since those in all three were double-subtracted).

---

## Additional Practice Problems: Digital Advanced Level

### Advanced Quants Extended Set

**Q16 (Successive dilution, Tier 2):** A 100L cask has pure wine. 20L is removed and replaced with water three times. What percentage of the final mixture is wine?
Wine remaining = 100 x (80/100)³ = 100 x 0.512 = **51.2%**.

**Q17 (Circular permutation, Tier 2):** 5 boys and 3 girls are to be seated around a circular table such that no two girls sit adjacent. Find the number of arrangements.
First arrange 5 boys: (5-1)! = 24 ways. There are 5 gaps between boys. Choose 3 of 5 gaps for girls: C(5,3) = 10. Arrange girls in those gaps: 3! = 6.
Total = 24 x 10 x 6 = **1440**.

**Q18 (Compound interest installments, Tier 3):** A person borrows Rs. 15,000 at 8% compound interest. He repays Rs. 7,800 at the end of the first year. What should he pay at the end of the second year to clear the debt?
After year 1: Principal + Interest = 15000 x 1.08 = 16200. Paid 7800. Remaining = 8400.
After year 2: 8400 x 1.08 = **Rs. 9072**.

**Q19 (Boats advanced, Tier 2):** A boat travels 60 km upstream in 5 hours and 40 km downstream in 2 hours. Find the speed of the stream.
Upstream speed = 12 km/h. Downstream speed = 20 km/h.
Stream speed = (Downstream - Upstream)/2 = (20-12)/2 = **4 km/h**.

**Q20 (Triangle advanced, Tier 2):** The ratio of sides of a triangle is 5:12:13. If the perimeter is 60 cm, find the area.
Sides: 10, 24, 26 cm. Since 10² + 24² = 100 + 576 = 676 = 26², it is a right triangle.
Area = (1/2) x 10 x 24 = **120 cm²**.

### Advanced Reasoning Extended Set

**Q21 (Analytical puzzle, Tier 3):** A, B, C, D, E are five friends. Each lives in a different city (Delhi, Mumbai, Kolkata, Chennai, Hyderabad) and owns a different vehicle (Car, Bike, Scooter, Cycle, Auto).

Conditions:
- A lives in Delhi and owns a Car.
- B lives in Mumbai.
- The person who owns a Bike lives in Chennai.
- C does not own a Cycle.
- D lives in Kolkata and owns a Scooter.
- E does not live in Hyderabad.

From conditions: A-Delhi-Car; B-Mumbai; D-Kolkata-Scooter.
Remaining people: C, E; remaining cities: Chennai, Hyderabad; remaining vehicles: Bike, Cycle, Auto.
Bike owner lives in Chennai. E does not live in Hyderabad → E lives in Chennai. E owns Bike.
C lives in Hyderabad. C does not own Cycle → C owns Auto. B owns Cycle.

Final: A-Delhi-Car; B-Mumbai-Cycle; C-Hyderabad-Auto; D-Kolkata-Scooter; E-Chennai-Bike.

**Q22 (Critical Reasoning, Tier 2):** 
Argument: "Students who study more than 6 hours daily perform better in exams. Therefore, to improve exam performance across all students, we should mandate a minimum 7-hour daily study requirement."

Weakener: Which of the following most weakens this argument?
(A) Some students perform well with less than 6 hours of study.
(B) Forcing students to study more than their optimal duration can cause burnout and reduce performance.
(C) Students who study 6 hours voluntarily may have different characteristics than those who need to be mandated.
(D) Both B and C together.

Best weakener: **(D)**. B attacks the assumption that more study time always improves performance. C attacks the assumption that the correlation in voluntary studiers applies to mandated studiers.

**Q23 (Input-Output advanced, Tier 3):**
Input: 16 alpha 9 beta 4 gamma 25 delta

Step 1: alpha 16 9 beta 4 gamma 25 delta
Step 2: alpha 4 9 beta 16 gamma 25 delta
Step 3: alpha 4 9 beta 16 gamma 25 delta

Pattern: Words move to the immediate left of their preceding number. Then numbers are sorted ascending. Hmm, let me re-examine: In Step 1, "alpha" moved left of 16. In Step 2, numbers 16 and 4 swapped... This type of problem requires more context. The pattern here: words move to positions 1, 3, 5, 7 while numbers sort into positions 2, 4, 6, 8.

Final output: alpha 4 beta 9 gamma 16 delta 25.

**Q24 (Data Sufficiency advanced, Tier 2):** Is the integer n a multiple of 15?
Statement 1: n is a multiple of 5.
Statement 2: n is a multiple of 3.

Statement 1 alone: n could be 5, 10, 15, 20... Not necessarily divisible by 15. NOT sufficient.
Statement 2 alone: n could be 3, 6, 9, 12, 15... Not necessarily divisible by 15. NOT sufficient.
Both together: n is a multiple of both 3 and 5. LCM(3,5) = 15. So n is a multiple of 15. SUFFICIENT together.

Answer: **(C) Both statements together are sufficient**.

**Q25 (Pattern recognition - matrix, Tier 2):**
```
3   5   15
2   7   14
4   ?   20
```

Pattern: Column 1 x Column 2 = Column 3. (3x5=15, 2x7=14... wait: 2x7=14 ✓, 4x?=20 → ?=5)

Wait, column 3 for row 2: 2x7=14 ✓. Row 3: 4 x ? = 20 → ? = **5**.

---

## Speed Building Exercises: 5-Minute Warm-Ups

Before any practice session, do a 5-minute mental math warm-up. This primes your arithmetic processing speed and reduces calculation errors during the actual section.

**Warm-up 1:** Calculate sequentially: 48 x 25, then 75% of the result, then square root if it's a perfect square.
48 x 25 = 1200. 75% of 1200 = 900. √900 = 30. ✓ (Use: 48 x 25 = 48 x 100/4 = 1200. Speed trick: multiply by 100 then divide by 4.)

**Warm-up 2:** Successive percentages: Start with 200. Increase 30%, decrease 20%, increase 10%.
200 x 1.30 = 260. 260 x 0.80 = 208. 208 x 1.10 = 228.8.
**Shortcut:** Net multiplier = 1.30 x 0.80 x 1.10 = 1.144. 200 x 1.144 = 228.8.

**Warm-up 3:** Identify whether 10! + 11! + 12! + 13! is divisible by 100.
= 10!(1 + 11 + 11x12 + 11x12x13) = 10!(1 + 11 + 132 + 1716) = 10! x 1860.
10! = 3628800. Does 3628800 x 1860 contain 100 as a factor? 3628800 has factors of 2 and 5 many times over. Yes, divisible by 100. This type of "factor analysis" builds the number sense needed for Advanced Quants.

---

## Common Error Patterns in Advanced Aptitude and How to Avoid Them

### Confusing "at most" and "at least" in P&C

"At most 2 vowels" means 0, 1, or 2 vowels - not exactly 2. Calculate each case separately and sum. The shortcut: "at most k" = total - "more than k" when the "more than k" case is simpler to calculate.

### Missing Negative Values in Inequalities

When multiplying or dividing an inequality by a negative number, flip the sign. (2x > -4) → x > -2. But (-2x > -4) → x < 2 (sign flips). Missing this flip in multi-step inequality problems is a reliable trap.

### Probability: Forgetting to Account for Order

"Two cards drawn from a deck, what is the probability both are aces?" If drawing without replacement and order does not matter: C(4,2)/C(52,2) = 6/1326 = 1/221. If order matters: (4/52)(3/51) = 12/2652 = 1/221. Same result, but the calculation path differs. For TCS Advanced, most drawing problems specify "without replacement" - always adjust the denominator for each draw.

### Venn Diagrams: Overcounting the Intersection

When computing "exactly two" from a three-set Venn diagram, subtract the "all three" count from each pairwise intersection, then sum. A student who studies Maths AND Physics = 30 includes those who study all three. Those who study Maths AND Physics BUT NOT Chemistry = 30 - 10 = 20. This distinction is the source of most Venn diagram errors.

### DI: Using the Wrong Year as Base for Percentage Change

Percentage change from Year A to Year B = (Year B - Year A) / Year A x 100. The base is always the starting year (Year A), not the target year (Year B). Using Year B as the base is a consistent trap in TCS DI questions where both options are available.

---

## The Advanced Aptitude Mindset

The Advanced sections test not just mathematical knowledge but decision-making under cognitive load. Three mindset principles separate high-scorers from average scorers:

**Accept partial performance.** You are not expected to solve every Advanced question. A realistic target is 10-12 of 15 questions correct within the time limit. Candidates who aim for perfection freeze on hard questions and lose time they could have spent on easier ones.

**Guess intelligently.** On any question where you can eliminate two options, your remaining guess has 50% probability of being correct. On a 1-mark question with -0.33 negative marking, this is a positive expected value. Develop the instinct to eliminate aggressively - in TCS Advanced options, extreme answers (very large or very small numbers that would require unusual circumstances) are usually wrong.

**Practise under test conditions, not study conditions.** The Advanced section's difficulty is compounded by time pressure. A problem that takes 3 minutes in a quiet study session may take 4 minutes under exam conditions. The only way to build test-condition performance is to practise with a running timer and the commitment not to pause it for any reason.

---

## Advanced Reasoning: Seating Arrangements at Digital Level

Digital level seating arrangements are significantly more complex than Foundation level. They may involve two rows facing each other, circular arrangements with direction constraints, or multiple conditions that interact in non-obvious ways.

### Two-Row Facing Arrangement

**Problem:** 8 people A, B, C, D, E, F, G, H are seated in two rows of 4 facing each other. Row 1 faces north; Row 2 faces south.

Conditions:
(i) B is at an end of Row 1.
(ii) H is to the immediate right of B.
(iii) D faces B.
(iv) F is not at any end of either row.
(v) C is to the left of G in Row 2.
(vi) E faces H.

From (i) and (ii): Row 1 positions 1-4 (left to right): if B is at position 1, H is at position 2. If B is at position 4, H is at position 3.
From (iii): D faces B. "Facing" means directly across. If B is at R1-position 1, D is at R2-position 1. If B is at R1-position 4, D is at R2-position 4.
From (vi): E faces H. If H is at R1-position 2, E is at R2-position 2.

Try B at position 1: Row 1: B, H, ?, ? | Row 2: D, E, ?, ? (D faces B at 1, E faces H at 2).
Remaining for Row 1: C, F, G, A minus those placed.
Remaining people: A, C, F, G for Row 1 positions 3,4 and Row 2 positions 3,4.
From (iv): F is not at an end. Row 1 ends are 1,4. Row 2 ends are 1,4. Position 1 is B/D; position 4 in Row 1 is available; position 4 in Row 2 is available. So F cannot be at R1-position 4 or R2-position 4.
From (v): C is to the left of G in Row 2. Row 2 remaining positions 3 and 4. For Row 2 facing south, "left" is position 4 relative to position 3 (since they face south). So C is at position 4 and G is at position 3? Or is "left from their perspective"? For someone facing south, their left is east (position increasing). So G at 4 is to the left of C at 3 from Row 2's perspective. This requires careful interpretation - TCS problems specify orientation clearly. Assuming left = position with lower number: C at 3, G at 4.

Then Row 2: D(1), E(2), C(3), G(4). Row 1 remaining: A, F at positions 3, 4. F cannot be at position 4. F at 3, A at 4.

Final: Row 1: B(1), H(2), F(3), A(4) | Row 2: D(1), E(2), C(3), G(4).

This type of problem takes 5-8 minutes for a well-prepared candidate. Under exam conditions with the 2-minute rule, recognise this as a Tier 3 problem immediately and budget accordingly.

---

## Advanced Quants: Quadratic Inequalities and Functions

### Graphical Interpretation of Quadratic Functions

Knowing the shape of y = ax² + bx + c (parabola opening upward if a > 0, downward if a < 0) helps solve inequality problems rapidly.

**For ax² + bx + c > 0:**
- If a > 0 (opens upward) and discriminant D < 0: always true (parabola entirely above x-axis)
- If a > 0 and D > 0: true for x < smaller root or x > larger root (outside the roots)
- If a < 0 and D > 0: true for smaller root < x < larger root (between the roots)

**Problem:** For which values of x is 2x² - 5x + 2 < 0?
a = 2 > 0. Roots: (5 ± √(25-16))/4 = (5 ± 3)/4. Roots: x = 2 and x = 1/2.
Since a > 0 and the parabola opens upward, 2x² - 5x + 2 < 0 BETWEEN the roots: **1/2 < x < 2**.

### Functions: Domain, Range, and Composition

**Problem:** f(x) = (x² - 4)/(x - 2). Find f(3) and determine whether f(2) is defined.

f(3) = (9 - 4)/(3 - 2) = 5/1 = 5.
f(2) = (4 - 4)/(2 - 2) = 0/0 - undefined directly. However, factoring: (x² - 4)/(x - 2) = (x+2)(x-2)/(x-2) = x + 2 for x ≠ 2. So f(x) = x + 2 everywhere except x = 2 (removable discontinuity). TCS sometimes tests whether candidates recognise this simplification.

**Composition:** If f(x) = 2x + 3 and g(x) = x², find f(g(2)) and g(f(2)).
g(2) = 4. f(g(2)) = f(4) = 2(4) + 3 = **11**.
f(2) = 7. g(f(2)) = g(7) = 7² = **49**.

---

## Advanced Quantitative: Profit, Loss and Partnership (Advanced)

### Dishonest Dealer Problems

**Problem:** A dealer uses weights that are 10% less than the standard weight. He also marks up his goods by 10% above cost. What is his actual profit percentage?

True weight sold = 900g when customer pays for 1000g. Effective SP for 900g = SP of 1000g.
Let CP = 100 per 1000g. Marked price = 110 per 1000g. But only 900g is given. Effective CP for 900g = 90. SP = 110.
Profit % = (110 - 90)/90 x 100 = 20/90 x 100 = **22.22%**.

### Partnership with Changing Capital

**Problem:** A invests Rs. 50,000 for the full year. B invests Rs. 80,000 for 8 months and Rs. 40,000 for the remaining 4 months. C invests Rs. 60,000 for the last 6 months. Find their profit-sharing ratio.

A's weighted investment = 50,000 x 12 = 600,000
B's weighted investment = 80,000 x 8 + 40,000 x 4 = 640,000 + 160,000 = 800,000
C's weighted investment = 60,000 x 6 = 360,000

Ratio = 600,000 : 800,000 : 360,000 = 15 : 20 : 9. Ratio = **15:20:9**.

---

## Building the Advanced Aptitude Test-Taking System

### The Scan-and-Sort Technique

Before attempting any question in the Advanced section, spend the first 90 seconds scanning all questions and mentally sorting them:

Mark each question with a mental tag:
- **Green (Tier 1):** I can solve this in under 90 seconds
- **Yellow (Tier 2):** Solvable in 90-150 seconds with focus
- **Red (Tier 3):** Complex; will take 150+ seconds or I am unsure of the approach

Attempt all Green questions first, even if they appear at the end of the question list. Then Yellow. Then Red with whatever time remains.

This ordering matters enormously because Advanced sections often front-load Tier 2 and Tier 3 problems. Candidates who answer sequentially get stuck on a hard question early, spend 4 minutes on it, and never reach the 3 easy questions at the end.

### The Estimation Confirmation Technique

For calculation-heavy questions, after completing your full calculation, perform a quick order-of-magnitude check:

"I calculated 37.5% of 4,800 = 1,800. Sense check: 40% of 4,800 = 1,920; 35% = 1,680. My answer of 1,800 falls between these - plausible."

If your answer does not fall in the expected range, recalculate before selecting. This 5-second sanity check catches arithmetic errors without re-doing the full calculation.

### Answer Elimination for Difficult Questions

When you cannot fully solve an Advanced question, eliminate options using logic:

**Elimination by units:** If the question asks for a distance in km and one option is "5,000 km" while the numbers in the problem are in the hundreds of metres range, that option is dimensionally implausible.

**Elimination by direction:** For profit/loss questions where the problem describes a profitable scenario, negative-percentage options are wrong. For probability questions, options outside [0,1] are impossible.

**Elimination by magnitude:** If the calculation involves adding 20% to a base of 100, the answer should be around 120. Options of 600 or 12 are implausibly far from this.

**Elimination by parity:** For P&C problems asking for the number of arrangements, the answer must be a positive integer. If the calculation yields a fraction, you have made an error - re-examine the formula applied.

Using elimination to reduce from 4 options to 2 options before guessing doubles your probability of guessing correctly. On questions with negative marking, this converts a negative expected value guess (25% correct = 0.25 - 0.75 x 0.33 = +0.003 marks) into a positive-expected-value guess (50% correct = 0.50 - 0.50 x 0.33 = +0.33 marks).

---

## The Week Before Your TCS Digital Advanced Test

This week-long plan assumes you have been preparing for several weeks and are refining your performance rather than starting from scratch.

**Day 1:** Take a full timed mock Advanced Quants section (25 minutes). Review every wrong answer and categorise errors: Was it a concept gap? A calculation error? A time management failure?

**Day 2:** Deep dive the two topic categories where you made the most errors in Day 1's mock. Concept re-study followed by 6 targeted practice problems in each category.

**Day 3:** Timed drill on your highest-ROI topics: DI complex and P&C advanced. 3 DI sets (5 minutes each) and 8 P&C problems (90 seconds each).

**Day 4:** Advanced Reasoning mock section (25 minutes). Focus on the triage protocol - are you spending too long on Tier 3 problems? Practice cutting off at 2 minutes even when the answer feels close.

**Day 5:** Mixed practice - 5 Advanced Quants questions (90 seconds each, no exceptions) alternating with 5 Advanced Reasoning questions. Build the mental gear-shifting ability to switch between quantitative and logical modes.

**Day 6:** Light review only. No new problems. Re-read your shortcut formulas, percentage-fraction equivalents, and the key theorems (Euler, Fermat, Wilson). Review your Venn diagram templates for three-set problems. Confirm your test environment setup.

**Day 7 (day before test):** Rest. No preparation. Light reading or activity. Early sleep. The preparation is done - trust it.

---

## Summary: What Separates 90th Percentile Performance in Advanced Sections

The candidates who consistently score in the top percentile of TCS Digital Advanced sections share five characteristics:

**1. They have automated the shortcuts.** Percentage-fraction equivalents, alligation, Vieta's formulas, circular permutation reduction - these are reflexes, not recalled procedures. The calculation time saved through automation is used on the analysis.

**2. They triage instantly.** Within 20 seconds of reading a question, they know its tier and whether to attempt it now or later. This is a practised skill, not an instinct - it develops through exposure to enough question types that pattern recognition becomes fast.

**3. They never chase a question past 2 minutes.** The discipline to guess and move is arguably more valuable than any single topic skill. It requires accepting imperfection, which is psychologically difficult but mathematically necessary.

**4. They eliminate before selecting.** They never select an option without first confirming the other options are wrong (for questions they can solve) or eliminating at least two options before guessing (for questions they cannot fully solve).

**5. They have practised under exam conditions, not study conditions.** Their preparation happened with timers running, no pausing, and the same cognitive pressure as the actual exam. The test is not harder than practice - it is the same difficulty, but under conditions they have already experienced many times.

These five characteristics are all learnable. None requires exceptional mathematical talent. They require preparation that is deliberate, consistent, and calibrated to the actual test conditions you will face.

---

## Putting It All Together: The Digital Advanced Preparation Compact

This guide has covered every major topic in the TCS Digital Advanced Quantitative and Reasoning sections. Before concluding, a synthesis of the most important preparation principles:

**On content:** The topics are finite and learnable. P&C, Probability, Coordinate Geometry, Logarithms, Number Theory, Advanced DI, Complex Syllogisms, Data Sufficiency, Critical Reasoning, and Input-Output patterns cover 95% of what appears in these sections. You do not need to master every topic - you need enough depth in the high-frequency topics to score reliably on them, and enough familiarity with the lower-frequency topics to earn partial credit through elimination.

**On shortcuts:** Shortcuts are not cheating - they are the expected approach. A candidate who solves every percentage problem from first principles (divide by 100, multiply) will run out of time. A candidate who has memorised that 37.5% = 3/8 and applies that instantly is using the same mathematics more efficiently. Invest time learning shortcut methods and practising them until they replace the long-form calculation as your natural approach.

**On time management:** The 25-minute constraint is the distinguishing factor in Advanced sections. Mathematical ability determines the ceiling of what you can score; time management determines how close you get to that ceiling. The triage protocol (Tier 1/2/3 classification, Green-Yellow-Red ordering, strict 2-minute cutoff) is a system that converts good mathematical ability into good test scores under time pressure. Practice this system in every mock session, not just the day before.

**On the relationship between Advanced sections and Digital profile:** The Advanced sections are not supplementary - they are the core of what makes Digital different from Ninja. Every hour invested in Advanced Quants and Advanced Reasoning preparation directly increases your probability of a Digital offer. The return on this preparation is not just a higher starting salary; it is a fundamentally different starting point in the TCS career - technically richer projects, faster exposure to client work, and the professional identity of a high-calibre candidate from the first day.

The difficulty of these sections is designed to be selective, not impossible. Every question in them has a solution reachable by a well-prepared candidate. The preparation in this guide gives you the tools. The practice - consistent, timed, and analytically reviewed - gives you the performance. Together, they give you the Digital profile.

Approach every practice session with the same urgency as the actual test. Close the textbook. Start the timer. Attempt the questions. Review the errors. The Advanced sections reward preparation that was itself demanding - not comfortable study, but challenging timed practice that builds the decision speed and mathematical reflexes the test requires.
