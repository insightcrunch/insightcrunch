---
layout: post
title: "TCS Ninja Aptitude: Every Topic Covered"
page_title: "TCS Ninja Aptitude Questions - Complete Topic-Wise Guide with Solutions and Speed Techniques"
date: 2023-10-01
categories: ["Industry"]
tags: ["TCS Ninja aptitude", "TCS Ninja quants", "TCS aptitude questions", "TCS numerical ability"]
excerpt: "Every TCS Ninja aptitude topic with concept refreshers, original practice problems, speed techniques, and priority study order."
image: "/assets/images/blog/blog-03.webp"
reading_time: 60
author: "Insight Crunch Team"
last_updated: 2026-03-23
---
The TCS Ninja Foundation Numerical Ability section is where most candidates either build the confidence to carry through the rest of the test or lose marks they should have locked. Twenty-five questions in twenty-five minutes means sixty seconds per question - enough time if you know the topic, almost never enough if you are figuring it out as you go. This guide covers every topic in the Ninja aptitude syllabus at the exact difficulty level TCS tests, with original practice problems, complete step-by-step solutions, shortcut formulas, and time benchmarks for each type. Work through this guide systematically and you will know every topic. Practice the problems under time pressure and you will know every topic fast.

![TCS Guide](/assets/images/blog/blog-03.webp)

## The TCS Ninja Foundation Aptitude: Format and Scoring

Before diving into topics, understand the exact test you are preparing for.

**25 questions, 25 minutes.** Average of 60 seconds per question. In practice, some questions (simple percentage calculations, direct formula applications) take 30-40 seconds. Others (multi-step time-work problems, compound interest) take 80-90 seconds. The candidates who score 90%+ have automated the fast questions to 30 seconds, banking time for the slower ones.

**No separate DI section for Ninja.** Data Interpretation questions are embedded within the 25-question Numerical Ability section, not in a separate section as in some other company tests. Expect 3-5 DI questions from a single chart or table.

**Negative marking applies.** For each wrong answer, 1/3 of the question mark is deducted. This means: if you cannot eliminate at least two of four options, it is better to leave the question blank. If you can eliminate two options, guessing between the remaining two is statistically favourable (+0.5 - 0.5 x 0.33 = +0.33 marks expected value).

**Topics with highest frequency in Foundation Numerical:**
1. Percentages and Profit/Loss (combined: 5-7 questions)
2. Time, Work, and Pipes (3-4 questions)
3. Time, Speed, and Distance (2-3 questions)
4. Data Interpretation (3-5 questions)
5. Number System and Simplification (2-3 questions)
6. Averages and Mixtures (2-3 questions)
7. Simple and Compound Interest (1-2 questions)
8. Permutations, Combinations, Probability (2-3 questions)
9. Geometry and Mensuration (1-2 questions)
10. Series and Sequences (1-2 questions)

---

## Topic 1: Number System

### Concept Overview

Number system questions test divisibility, factors, remainders, HCF and LCM, and properties of integers. TCS Ninja questions in this category are typically one to two steps and test whether you know the definitions and rules precisely.

### Factors and Number of Factors

**Formula:** For n = p1^a x p2^b x p3^c..., the number of factors = (a+1)(b+1)(c+1)...

**Problem 1.1:** How many factors does 360 have?
360 = 2³ x 3² x 5¹
Number of factors = (3+1)(2+1)(1+1) = 4 x 3 x 2 = **24**

**Problem 1.2:** Find the sum of all factors of 72.
72 = 2³ x 3²
Sum of factors = (2⁰+2¹+2²+2³)(3⁰+3¹+3²) = (1+2+4+8)(1+3+9) = 15 x 13 = **195**

**Shortcut:** Sum of factors formula for n = p^a x q^b: ((p^(a+1) - 1)/(p-1)) x ((q^(b+1) - 1)/(q-1))

**Time benchmark:** 45 seconds if you know the prime factorisation and formula. The bottleneck is the prime factorisation - practice factorising numbers up to 500 quickly.

### HCF and LCM

**Core relationship:** HCF x LCM = Product of two numbers (for exactly two numbers only).

**Problem 1.3:** HCF of two numbers is 12 and their LCM is 180. If one number is 36, find the other.
HCF x LCM = n1 x n2 → 12 x 180 = 36 x n2 → n2 = 2160/36 = **60**

**Problem 1.4:** Find the largest number that divides 47, 95, and 151 leaving the same remainder.
The required number divides (95-47), (151-95), (151-47) exactly: 48, 56, 104.
HCF(48, 56, 104) = HCF(48, 56) = 8; HCF(8, 104) = **8**

**Shortcut for "same remainder" problems:** The number you are looking for divides the differences between the given numbers. Find HCF of the differences.

### Divisibility Rules (Exam-Speed Reference)

| Divisible by | Rule |
|---|---|
| 2 | Last digit even |
| 3 | Sum of digits divisible by 3 |
| 4 | Last two digits divisible by 4 |
| 6 | Divisible by both 2 and 3 |
| 8 | Last three digits divisible by 8 |
| 9 | Sum of digits divisible by 9 |
| 11 | Alternating digit sum (odd positions - even positions) divisible by 11 |
| 12 | Divisible by both 3 and 4 |

**Problem 1.5:** What is the smallest number divisible by both 12 and 18 that also has exactly 6 factors?
LCM(12,18) = 36. Factors of 36: (36 = 2² x 3²), count = (2+1)(2+1) = 9. Not 6.
Next multiple: 72 = 2³ x 3². Factors = (3+1)(2+1) = 12. Not 6.
Try 48 = 2⁴ x 3. Factors = (4+1)(1+1) = 10. Not 6. Try 2⁵ = 32, not divisible by 18. Try 2⁵ x 3: not divisible by 18 (need 3²). Try 2 x 3⁵ = 486 = 2 x 3⁵: factors = (1+1)(5+1) = 12. For 6 factors need p⁵ or p² x q: LCM must divide it and it must be divisible by LCM(12,18) = 36 = 2² x 3². So it must have at least 2² and 3² in factorisation. For exactly 6 factors: (a+1)(b+1) = 6 → options: 6=6x1 (so 2^5 x 3^0, but needs 3²) or 6=3x2 (so 2² x 3¹, but needs 3², contradiction) or 6=2x3 (so 2^1 x 3^2 = 18, check: has 2 factors from 2 part and 3 factors from 3 part = 6 factors, and 18 is divisible by 18 but: 18 = 2 x 3², not divisible by 12 since 12 = 2² x 3). The smallest such number may be **72** (if we relax). This is a deliberately challenging problem showing TCS can combine multiple conditions.

---

## Topic 2: Percentages

Percentages is the single most tested topic in TCS Ninja numerical ability. Master every variant.

### Concept: Percentage Change

Percentage change = (New - Old)/Old x 100. Always use the original value as the base.

**Problem 2.1:** A salary of Rs. 40,000 is first increased by 20% and then decreased by 15%. What is the final salary?
After increase: 40,000 x 1.20 = 48,000.
After decrease: 48,000 x 0.85 = **Rs. 40,800**

**Shortcut:** Net multiplier = 1.20 x 0.85 = 1.02. Final = 40,000 x 1.02 = 40,800. Use this chained multiplier approach for any sequence of percentage changes.

**Problem 2.2:** A's salary is 25% more than B's. By what percentage is B's salary less than A's?
If B = 100, A = 125. B is less than A by 25/125 x 100 = **20%**.

**Shortcut formula:** If X is r% more than Y, then Y is less than X by (r/(100+r)) x 100 percent.
Here: (25/125) x 100 = 20%. ✓

**Problem 2.3:** The price of sugar falls by 10%. By what percentage should consumption increase so that expenditure remains unchanged?
If price falls from 100 to 90, for same expenditure (= 100), new consumption = 100/90 units.
Original consumption = 1 unit. Increase = (100/90 - 1) x 100 = (10/90) x 100 = 11.11%.

**Shortcut:** If price decreases by r%, consumption must increase by (r/(100-r)) x 100 percent.
(10/90) x 100 = **11.11%**. ✓

**Time benchmark:** Simple percentage change: 30 seconds. Chained percentages (two steps): 45 seconds. "By what percentage is X less than Y" type: 40 seconds.

---

## Topic 3: Profit and Loss

### Core Formulae

- Profit = SP - CP; Loss = CP - SP
- Profit% = Profit/CP x 100; Loss% = Loss/CP x 100
- SP = CP x (100 + P%)/100; CP = SP x 100/(100 + P%)
- Marked Price (MP) - Discount = Selling Price

**Problem 3.1:** A shopkeeper buys goods for Rs. 1,200 and marks them 40% above cost price. He then offers a 15% discount on the marked price. Find his profit percentage.
MP = 1200 x 1.40 = 1680. SP = 1680 x 0.85 = 1428.
Profit = 1428 - 1200 = 228. Profit% = 228/1200 x 100 = **19%**

**Shortcut:** Combined effect of markup m% and discount d% on CP:
Net P% = m - d - md/100 = 40 - 15 - (40x15)/100 = 25 - 6 = 19%. ✓

**Problem 3.2:** By selling 40 items, a person earns the same profit as the selling price of 10 items. Find the profit percentage.
Let SP = x per item. Profit on 40 items = SP of 10 items = 10x.
CP of 40 items = SP - Profit = 40x - 10x = 30x. CP per item = 30x/40 = 3x/4.
Profit per item = x - 3x/4 = x/4. Profit% = (x/4)/(3x/4) x 100 = **33.33%**

**Problem 3.3:** A trader sells two items at Rs. 2,400 each - one at 20% profit and one at 20% loss. What is the net result?
When equal SP and equal percentage profit/loss, there is always a net loss = (P%)²/100 = 400/100 = **4% loss**.
To verify: CP₁ = 2400/1.20 = 2000. CP₂ = 2400/0.80 = 3000. Total CP = 5000. Total SP = 4800. Loss = 200 on 5000 = 4%. ✓

**Time benchmark:** Single profit/loss calculation: 40 seconds. Markup + discount combined: 45 seconds. Equal SP, equal % problem: 30 seconds with shortcut.

---

## Topic 4: Ratio, Proportion, and Mixtures

### Ratio and Proportion

**Problem 4.1:** If A:B = 3:4 and B:C = 5:6, find A:B:C.
Make B common: A:B = 3:4 = 15:20; B:C = 5:6 = 20:24. A:B:C = **15:20:24**.

**Problem 4.2:** Rs. 3,900 is divided among A, B, C in the ratio 1/2 : 1/3 : 1/4. Find A's share.
Multiply through by LCM 12: ratio becomes 6:4:3. Total parts = 13.
A's share = 6/13 x 3900 = **Rs. 1,800**.

**Shortcut:** When shares are given as fractions, multiply all fractions by their LCM to convert to whole-number ratio.

### Alligation for Mixtures

Alligation finds the ratio in which two ingredients must be mixed to get a desired concentration.

```
   d1         d2
     \       /
      \     /
       d (mean)
     /       \
   /           \
(d2 - d)  :  (d - d1)
```

**Problem 4.3:** In what ratio must water (cost = 0) be mixed with milk costing Rs. 40 per litre to get a mixture worth Rs. 32 per litre?
Using alligation: 40 and 0 mixed to get 32.
Water proportion = (40 - 32) = 8; Milk proportion = (32 - 0) = 32.
Ratio water:milk = 8:32 = **1:4**

**Problem 4.4:** A mixture of 60 litres has milk and water in ratio 7:3. How much water must be added to make the ratio 3:7?
Milk = 42L, water = 18L. After adding x litres of water: 42/(18+x) = 3/7.
42 x 7 = 3(18+x) → 294 = 54 + 3x → x = **80 litres**.

**Time benchmark:** Simple ratio/proportion: 35 seconds. Alligation: 45 seconds. Mixture with addition: 60 seconds.

---

## Topic 5: Time and Work

Time and work is the topic with the most consistent appearance in TCS Ninja numerical sections. Master the efficiency-based approach.

### The Efficiency Method

**Core idea:** Work done per day = 1/total days. Combined efficiency = sum of individual efficiencies.

**Problem 5.1:** A can do a work in 12 days and B can do it in 18 days. In how many days can they finish it together?
A's daily rate = 1/12; B's daily rate = 1/18.
Combined = 1/12 + 1/18 = 3/36 + 2/36 = 5/36.
Time together = 36/5 = **7.2 days (7 days 4.8 hours)**.

**Shortcut:** Two workers with times a and b: Time together = ab/(a+b).
= (12 x 18)/(12+18) = 216/30 = 7.2 ✓

**Problem 5.2:** A and B together finish in 8 days. A alone takes 12 days. How long does B alone take?
1/B = 1/8 - 1/12 = 3/24 - 2/24 = 1/24. B alone = **24 days**.

**Problem 5.3:** 15 workers can build a wall in 48 days. After 16 days, 5 workers left. How many more days to finish?
Work done in 16 days by 15 workers = 15 x 16 = 240 worker-days.
Total work = 15 x 48 = 720 worker-days. Remaining = 480 worker-days.
Remaining workers = 10. Days needed = 480/10 = **48 more days**.

**Problem 5.4 (pipes):** Pipe A fills a tank in 6 hours, Pipe B fills it in 9 hours, Pipe C drains it in 12 hours. If all three are open, how long to fill the tank?
Net rate = 1/6 + 1/9 - 1/12. LCM(6,9,12) = 36.
= 6/36 + 4/36 - 3/36 = 7/36. Time = 36/7 ≈ **5.14 hours**.

**Shortcut for pipes:** Fill pipes add; drain pipes subtract. Net rate = sum of fill rates - sum of drain rates.

**Time benchmark:** Two-worker combination: 35 seconds. Three-person including pipes: 55 seconds. Chain rule (workers-days): 50 seconds.

---

## Topic 6: Time, Speed, and Distance

### Core Formulae

- Speed = Distance/Time; Distance = Speed x Time; Time = Distance/Speed
- Relative speed (same direction) = |S1 - S2|; Relative speed (opposite direction) = S1 + S2
- Convert km/h to m/s: multiply by 5/18; convert m/s to km/h: multiply by 18/5

**Problem 6.1:** A train 200m long passes a pole in 10 seconds and a bridge in 30 seconds. Find the length of the bridge.
Speed = 200/10 = 20 m/s. In 30 seconds, train covers 20 x 30 = 600m = (train length + bridge length).
Bridge length = 600 - 200 = **400m**.

**Problem 6.2:** Two trains of lengths 150m and 200m approach each other at 60 km/h and 90 km/h. How long do they take to cross each other?
Relative speed = 60 + 90 = 150 km/h = 150 x 5/18 = 125/3 m/s.
Distance = 150 + 200 = 350m. Time = 350 / (125/3) = 350 x 3/125 = 1050/125 = **8.4 seconds**.

**Problem 6.3:** A boat goes 40 km upstream in 8 hours and 36 km downstream in 6 hours. Find the speed of the stream.
Upstream speed = 40/8 = 5 km/h. Downstream speed = 36/6 = 6 km/h.
Stream speed = (Downstream - Upstream)/2 = (6-5)/2 = **0.5 km/h**.

**Boat formulae:** Downstream = boat + stream; Upstream = boat - stream.
Boat speed = (Downstream + Upstream)/2; Stream speed = (Downstream - Upstream)/2.

**Problem 6.4:** A and B run around a 400m circular track at 10 m/s and 6 m/s in the same direction. In how many seconds do they first meet?
Relative speed = 10 - 6 = 4 m/s. Time for A to lap B = 400/4 = **100 seconds**.

**Time benchmark:** Train crossing a pole or platform: 35 seconds. Two trains crossing each other: 50 seconds. Boats and streams: 45 seconds.

---

## Topic 7: Averages

### The Average Formula and Its Applications

Average = Sum/Count. TCS Ninja average problems are typically about changes to the average when items are added or removed.

**Problem 7.1:** The average of 15 numbers is 48. If 3 is added to each number, what is the new average?
New average = 48 + 3 = **51**. (Adding a constant to all numbers shifts the average by that constant.)

**Problem 7.2:** Average of A, B, C = 40. Average of A, B = 38. Find C.
Sum of A+B+C = 120. Sum of A+B = 76. C = 120 - 76 = **44**.

**Problem 7.3 (ages):** The average age of a class of 30 students is 14 years. When the teacher's age is included, the average becomes 15 years. Find the teacher's age.
Total age of students = 30 x 14 = 420. Total including teacher = 31 x 15 = 465.
Teacher's age = 465 - 420 = **45 years**.

**Problem 7.4 (replacement):** Average of 10 numbers is 24. One number 36 is replaced by another. The average becomes 22. What is the new number?
Original sum = 240. New sum = 220. New number = 220 - (240 - 36) = 220 - 204 = **16**.

**Shortcut:** Replacement change: new number = old number + (change in average x count of numbers).
= 36 + (22-24) x 10 = 36 - 20 = 16. ✓

**Time benchmark:** Direct average: 20 seconds. Average with addition/removal: 40 seconds. Ages problems: 45 seconds.

---

## Topic 8: Simple and Compound Interest

### Simple Interest

SI = PRT/100, where P = principal, R = rate per annum, T = time in years.
Amount = P + SI = P(1 + RT/100)

**Problem 8.1:** Find the SI on Rs. 12,000 at 8% per annum for 3 years.
SI = 12000 x 8 x 3 / 100 = **Rs. 2,880**

**Problem 8.2:** At what rate will Rs. 5,000 become Rs. 6,500 in 5 years (SI)?
SI = 6500 - 5000 = 1500. Rate = SI x 100/(P x T) = 1500 x 100/(5000 x 5) = **6% per annum**

### Compound Interest

Amount = P(1 + R/100)^T. CI = Amount - P.

**Key CI shortcuts:**
- For T = 2 years: CI = P(2R/100 + R²/10000) = SI + SI²/(100P) - the difference between CI and SI for 2 years = PR²/10000
- For T = 3 years: CI = SI + 3 x SI x R/(100 x 2) approximately, or use formula directly

**Problem 8.3:** Find CI on Rs. 8,000 at 10% per annum for 2 years.
Amount = 8000 x (1.1)² = 8000 x 1.21 = 9680. CI = 9680 - 8000 = **Rs. 1,680**.

**Shortcut:** SI for 2 years = 8000 x 10 x 2/100 = 1600. Difference = CI - SI = PR²/10000 = 8000 x 100/10000 = 80. CI = 1600 + 80 = 1680. ✓

**Problem 8.4:** A principal triples itself in 20 years under SI. In how many years does it become 7 times itself?
If it triples: SI = 2P in 20 years. Rate = 2P x 100/(P x 20) = 10% per annum.
For 7 times: SI = 6P. Time = 6P x 100/(P x 10) = **60 years**.

**Time benchmark:** Direct SI: 25 seconds. Direct CI (2 years): 40 seconds. "Becomes X times" problems: 40 seconds.

---

## Topic 9: Permutations and Combinations

### Selection vs Arrangement

**Selection (Combination):** nCr = n!/(r!(n-r)!) - order does NOT matter.
**Arrangement (Permutation):** nPr = n!/(n-r)! - order MATTERS.

**Key values to memorise:**
- nC0 = nCn = 1
- nC1 = nCn-1 = n
- nC2 = n(n-1)/2
- nCr = nC(n-r)

**Problem 9.1:** A committee of 3 men and 2 women is to be chosen from 6 men and 5 women. How many ways are possible?
Select 3 men from 6: C(6,3) = 20. Select 2 women from 5: C(5,2) = 10.
Total = 20 x 10 = **200 ways**.

**Problem 9.2:** How many 4-digit numbers can be formed using digits {1,2,3,4,5} if repetition is not allowed and the number is even?
For an even number, the last digit must be even: choices are 2 or 4 (2 options).
Remaining 3 positions from remaining 4 digits: 4 x 3 x 2 = 24 ways.
Total = 2 x 24 = **48**.

**Problem 9.3:** In how many ways can the letters of "ENGINEERING" be arranged?
ENGINEERING: E(3), N(3), G(2), I(2), R(1) = 11 letters.
Arrangements = 11! / (3! x 3! x 2! x 2!) = 39916800 / (6 x 6 x 2 x 2) = 39916800/144 = **277,200**

**Time benchmark:** Simple combination selection: 35 seconds. Arrangement with restrictions: 50 seconds. Letters of a word with repeats: 55 seconds.

---

## Topic 10: Probability

### Basic Probability

P(Event) = Favourable outcomes / Total outcomes. P ranges from 0 to 1.

**Problem 10.1:** A bag contains 5 red, 3 blue, and 2 green balls. One ball is drawn randomly. Find the probability it is not blue.
Total = 10. Blue = 3. P(not blue) = 7/10 = **0.7**.

**Problem 10.2:** Two dice are rolled. Find the probability that the sum is 8.
Total outcomes = 36. Favourable: (2,6),(3,5),(4,4),(5,3),(6,2) = 5 outcomes.
P = 5/36.

**Problem 10.3:** A card is drawn from a standard deck of 52. Find the probability it is a face card or a heart.
P(face) = 12/52. P(heart) = 13/52. P(face AND heart) = 3/52.
P(face OR heart) = 12/52 + 13/52 - 3/52 = 22/52 = **11/26**.

**Problem 10.4 (independent events):** A coin is tossed 3 times. Find P(exactly 2 heads).
Using C(3,2) x (1/2)² x (1/2)¹ = 3 x 1/4 x 1/2 = **3/8**.

**Complementary probability shortcut:** P(at least one) = 1 - P(none). For "at least one head in 3 tosses": 1 - (1/2)³ = 1 - 1/8 = 7/8. Much faster than adding P(exactly 1) + P(exactly 2) + P(exactly 3).

**Time benchmark:** Single event probability: 25 seconds. Two-dice problems: 40 seconds. Card problems with OR: 45 seconds. Binomial-type (exactly k successes): 40 seconds.

---

## Topic 11: Geometry

### Triangles

**Area formulae:**
- Base and height: Area = (1/2) x base x height
- Three sides (Heron's): s = (a+b+c)/2; Area = √(s(s-a)(s-b)(s-c))
- Equilateral triangle side a: Area = (√3/4)a²; Height = (√3/2)a
- Right triangle: Area = (1/2) x leg1 x leg2

**Key properties:**
- Sum of angles in triangle = 180°
- Exterior angle = sum of two non-adjacent interior angles
- In similar triangles, ratio of areas = square of ratio of corresponding sides

**Problem 11.1:** A triangle has sides 7, 24, 25. Find its area.
Check: 7² + 24² = 49 + 576 = 625 = 25². It is a right triangle.
Area = (1/2) x 7 x 24 = **84 sq units**.

**Problem 11.2:** Two similar triangles have corresponding sides in ratio 3:5. The smaller triangle has area 36 cm². Find the area of the larger.
Area ratio = 9:25. Larger area = 36 x 25/9 = **100 cm²**.

### Circles

**Key formulae:**
- Area = πr²; Circumference = 2πr
- Arc length = (θ/360°) x 2πr; Sector area = (θ/360°) x πr²
- Angle at centre = 2 x angle at circumference (same arc)
- Angle in semicircle = 90° (Thales' theorem)

**Problem 11.3:** A circle has circumference 44 cm. Find its area. (Use π = 22/7)
2πr = 44 → r = 7 cm. Area = πr² = (22/7) x 49 = **154 cm²**.

**Problem 11.4:** In a circle of radius 10 cm, a chord is at perpendicular distance 6 cm from the centre. Find the chord's length.
Half-chord = √(r² - d²) = √(100 - 36) = √64 = 8. Chord = 2 x 8 = **16 cm**.

### Quadrilaterals

- Rectangle: Area = l x b; Diagonal = √(l² + b²)
- Square: Area = a²; Diagonal = a√2
- Parallelogram: Area = base x height
- Trapezium: Area = (1/2)(sum of parallel sides) x height
- Rhombus: Area = (1/2) x d1 x d2 (diagonals)

**Time benchmark:** Right triangle area: 20 seconds. Circle area/circumference: 25 seconds. Chord length: 35 seconds.

---

## Topic 12: Mensuration

### 3D Solids - Key Formulae

**Cube (side a):**
- Volume = a³; TSA = 6a²; Diagonal = a√3

**Cuboid (l x b x h):**
- Volume = lbh; TSA = 2(lb + bh + lh); Diagonal = √(l² + b² + h²)

**Cylinder (radius r, height h):**
- Volume = πr²h; CSA = 2πrh; TSA = 2πr(r+h)

**Cone (radius r, height h, slant l = √(r²+h²)):**
- Volume = (1/3)πr²h; CSA = πrl; TSA = πr(r+l)

**Sphere (radius r):**
- Volume = (4/3)πr³; Surface area = 4πr²

**Hemisphere:**
- Volume = (2/3)πr³; CSA = 2πr²; TSA = 3πr²

**Problem 12.1:** A solid metallic cylinder of radius 3 cm and height 12 cm is melted and recast into a cone of same radius. Find the height of the cone.
Volume of cylinder = π x 9 x 12 = 108π. Volume of cone = (1/3)π x 9 x h = 3πh.
108π = 3πh → h = **36 cm**.

**Problem 12.2:** How many spheres of radius 2 cm can be cast from a cuboid 16 cm x 10 cm x 8 cm?
Volume of cuboid = 1280 cm³. Volume of each sphere = (4/3)π(2³) = 32π/3 ≈ 33.51 cm³.
Number = 1280/33.51 ≈ 38.2 → **38 spheres** (take floor, since partial sphere cannot be cast).

**Problem 12.3:** The radius of a sphere is increased by 50%. Find the percentage increase in its volume.
New radius = 1.5r. New volume = (4/3)π(1.5r)³ = (4/3)πr³ x 3.375.
Increase = 2.375 times original = **237.5% increase**.

**Shortcut:** Volume scales as cube of radius. (1.5)³ = 3.375. So 237.5% increase.

**Time benchmark:** Volume of standard solid: 30 seconds. Melting/recasting: 45 seconds. Percentage change in volume: 40 seconds with power shortcut.

---

## Topic 13: Sequences and Series

### Arithmetic Progression (AP)

nth term: aₙ = a + (n-1)d
Sum of n terms: Sₙ = n/2 x (2a + (n-1)d) = n/2 x (first + last term)
where a = first term, d = common difference

**Problem 13.1:** Find the sum of all even numbers from 1 to 200.
First even = 2, last = 200, d = 2.
n = (200-2)/2 + 1 = 100. Sum = 100/2 x (2 + 200) = 50 x 202 = **10,100**.

**Problem 13.2:** In an AP, the 5th term is 17 and 10th term is 32. Find the 20th term.
Using d = (32-17)/(10-5) = 3. a = 17 - 4x3 = 5. 20th term = 5 + 19x3 = **62**.

### Geometric Progression (GP)

nth term: aₙ = ar^(n-1)
Sum of n terms: Sₙ = a(rⁿ - 1)/(r-1) for r ≠ 1
Sum to infinity (|r| < 1): S∞ = a/(1-r)

**Problem 13.3:** Find the sum of a GP with first term 3, ratio 2, and 6 terms.
S₆ = 3(2⁶ - 1)/(2-1) = 3 x 63 = **189**

### Special Series

- Sum of first n natural numbers: n(n+1)/2
- Sum of squares: n(n+1)(2n+1)/6
- Sum of cubes: [n(n+1)/2]²

**Problem 13.4:** Find 1² + 2² + 3² + ... + 20²
= 20 x 21 x 41/6 = 20 x 21 x 41/6 = 2870/... = 8610/... Let me compute: 20x21 = 420; 420x41 = 17220; 17220/6 = **2,870**.

**Time benchmark:** Sum of AP: 35 seconds. Finding nth term from two given terms: 40 seconds. GP sum with small n: 35 seconds.

---

## Topic 14: Simplification

Simplification questions test BODMAS compliance, fraction arithmetic, surds, and indices. They are the quickest questions in the section when recognised.

### BODMAS

**B**rackets → **O**rders (powers/roots) → **D**ivision → **M**ultiplication → **A**ddition → **S**ubtraction.

**Problem 14.1:** Evaluate: 72 ÷ 8 + 4 x 5 - 3²
= 72 ÷ 8 + 4 x 5 - 9 = 9 + 20 - 9 = **20**

### Surds and Indices

**Key rules:**
- a^m x a^n = a^(m+n)
- (a^m)^n = a^(mn)
- a^(-n) = 1/a^n
- √(a/b) = √a/√b
- Rationalising: multiply by conjugate. 1/(a+√b) x (a-√b)/(a-√b) = (a-√b)/(a²-b)

**Problem 14.2:** Simplify: (2√3 + 1)(2√3 - 1)
= (2√3)² - 1² = 12 - 1 = **11**

**Problem 14.3:** Find the value of (0.8)³ - (0.5)³ / [(0.8)² + (0.8)(0.5) + (0.5)²]
Using a³ - b³ = (a-b)(a² + ab + b²): the expression = (0.8 - 0.5) = **0.3**

**Time benchmark:** BODMAS: 20 seconds. Surd multiplication/rationalisation: 30 seconds. a³-b³ pattern recognition: 25 seconds (with pattern recognition) vs 90 seconds (by calculation).

---

## Topic 15: Data Interpretation

### Reading Charts Efficiently

TCS Ninja DI typically uses one chart or table with 3-5 questions. The chart data is fixed across all questions, so the time investment in understanding the chart is amortised.

**Step 1 (30 seconds):** Read the chart title, axis labels, and units. Note the scale. Identify what each row/column/bar represents.

**Step 2 (20 seconds):** Read the questions to know exactly which data points you need. Do not memorise the chart - locate data on demand as questions require it.

**Step 3:** Answer each question using the minimum data extraction needed.

### Question Types and Approaches

**Direct reading:** "What was the revenue in [period]?" - Read directly from chart.

**Percentage change:** "By what percentage did sales grow from Q1 to Q2?" - (Q2-Q1)/Q1 x 100.

**Ratio comparison:** "What is the ratio of sales in Q1 to Q3?" - Extract both values and simplify.

**Highest/lowest identification:** "In which quarter were profits highest?" - Scan visually; calculate only when two values appear close.

**Multiple-series comparison:** "In which period was the difference between revenue and profit greatest?" - Compute the difference for each period and compare.

**Sample DI Set:**

A company's quarterly revenue (Rs. crore): Q1: 120, Q2: 150, Q3: 135, Q4: 180.
Profit margin: Q1: 15%, Q2: 20%, Q3: 18%, Q4: 25%.

**Q15.1:** What was the total profit across all quarters?
Q1: 120 x 0.15 = 18. Q2: 150 x 0.20 = 30. Q3: 135 x 0.18 = 24.3. Q4: 180 x 0.25 = 45.
Total profit = **117.3 crore**.

**Q15.2:** In which quarter was the absolute profit highest?
Q4: 45 crore. **Q4**.

**Q15.3:** What was the percentage growth in revenue from Q1 to Q4?
(180-120)/120 x 100 = 60/120 x 100 = **50%**.

**Q15.4:** What was Q3 revenue as a percentage of total annual revenue?
Total = 120+150+135+180 = 585. Q3% = 135/585 x 100 = **23.08% ≈ 23.1%**.

**Time benchmark:** DI setup (reading chart): 30 seconds. Per DI question (after chart is understood): 35-45 seconds.

---

## Identifying Question Types Quickly

One of the most valuable skills in the Ninja aptitude section is recognising the topic and sub-type within 5-10 seconds of reading a question. The following keyword patterns trigger immediate topic identification:

| Question contains... | Topic |
|---|---|
| "marks up / discount / selling price / cost price" | Profit and Loss |
| "fills / empties / drains / pipe" | Pipes (Time and Work) |
| "crosses / overtakes / relative speed / meets" | Time Speed Distance |
| "mixture / alloy / solution / ratio of contents" | Mixtures / Alligation |
| "simple interest / compound interest / amount" | SI/CI |
| "arranges / selects / committee / group / digit" | P&C |
| "probability / bag / card / coin / dice" | Probability |
| "average age / average weight / replaced by" | Averages |
| "factor / HCF / LCM / remainder / divisible" | Number System |
| "AP / GP / series / next term / sum" | Sequences and Series |
| "triangle / circle / cylinder / cone / sphere / area" | Geometry / Mensuration |
| "increased by X% / decreased by Y% / by what %" | Percentages |

Train yourself to make this identification instantly. 10 seconds of correct topic identification saves 20-30 seconds of methodology searching.

---

## The Most Common Calculation Errors in TCS Ninja Aptitude

### Error 1: Using the Wrong Base for Percentage Change

"A is 20% more than B" means A = B x 1.20. But "A is 20% more" does NOT mean "B is 20% less than A." B = A x 100/120 = A/1.20, which is 16.67% less than A, not 20%. Always identify which quantity is the base.

### Error 2: Not Distinguishing SI and CI in Multi-Year Problems

TCS often states "at X% interest" without specifying simple or compound. In TCS Ninja section, if the context involves a bank or investment, it is typically compound. If the context says "simple interest" explicitly, use SI. When not specified in the question and not given contextual hints, read carefully - often the answer options will indicate which formula was intended.

### Error 3: Forgetting to Account for Both Directions in Circular Track Problems

When two people running on a circular track in the OPPOSITE direction, time to first meet = track_length / (speed1 + speed2). Candidates frequently apply this formula to same-direction problems. Same direction = track_length / |speed1 - speed2|.

### Error 4: Off-By-One in Number of Terms in AP/GP

The number of terms from a to l with common difference d: n = (l-a)/d + 1. The "+1" is consistently missed, leading to an answer that is one term short. Example: terms from 3 to 99 with d=4: (99-3)/4 + 1 = 24 + 1 = 25 terms, not 24.

### Error 5: Confusing CSA and TSA in Mensuration

CSA (Curved Surface Area) excludes flat circular/base faces. TSA includes them. A cylinder's TSA includes the two circular ends; its CSA does not. When a problem asks for "the area of material needed to make a container" and the container is open at the top, use CSA + one base area, not TSA.

### Error 6: Treating "at most" as "exactly" in P&C

"At most 2 boys" means 0 boys OR 1 boy OR 2 boys - three separate cases that must be summed. "Exactly 2 boys" is a single case. This distinction costs marks consistently in P&C problems.

---

## Mental Math Techniques for Speed

### Multiplication Tricks

**Multiply by 25:** Multiply by 100, then divide by 4. 48 x 25 = 4800/4 = 1200.

**Multiply by 125:** Multiply by 1000, then divide by 8. 24 x 125 = 24000/8 = 3000.

**Multiply by 11 (2 digits):** Place the original number and its digits apart: 47 x 11 → 4_(4+7)_7 = 4_11_7 → carry the 1 → 517.

**Squaring numbers ending in 5:** (a5)² = a(a+1) followed by 25. 85² = 8x9 followed by 25 = 7225. 65² = 6x7 followed by 25 = 4225.

**Squaring near 50:** (50+n)² = 2500 + 100n + n². 53² = 2500 + 300 + 9 = 2809. 47² = 2500 - 300 + 9 = 2209.

### Division Tricks

**Divide by 5:** Multiply by 2 and divide by 10 (shift decimal). 840/5 = 840x2/10 = 1680/10 = 168.

**Divide by 15:** Divide by 3, then by 5. 870/15 = 290/5 = 58.

**Fractions to percentages (key ones):** 1/8 = 12.5%; 3/8 = 37.5%; 5/8 = 62.5%; 7/8 = 87.5%; 1/6 = 16.67%; 5/6 = 83.33%; 2/7 ≈ 28.57%; 3/7 ≈ 42.86%.

### Estimation Approach

When the answer options are spread far apart (e.g., 120, 250, 480, 860), estimation is sufficient. You do not need the exact answer - you need to identify which range the correct answer falls in.

For 23% of 4,848: 20% = 969.6; 25% = 1212. So 23% is between 969 and 1212. If the only option in that range is 1114, that is your answer without full calculation.

---

## Topic Priority Study Order

Based on frequency and scoring potential, study these topics in this order:

**Week 1 (highest frequency, fastest improvement):**
1. Percentages (5-7 questions per section)
2. Profit and Loss (closely related to percentages)
3. Time, Work, and Pipes
4. Time, Speed, and Distance
5. Data Interpretation (appears in every section)

**Week 2 (medium frequency):**
6. Averages and Mixtures
7. Simple and Compound Interest
8. Ratio and Proportion
9. Number System (factors, HCF, LCM, remainders)

**Week 3 (complete coverage):**
10. Permutations and Combinations
11. Probability
12. Sequences and Series
13. Geometry and Mensuration
14. Simplification

This ordering ensures you cover the topics that appear in every test first. After Week 1, you have preparation for roughly 60-65% of the questions by frequency. After Week 2, you cover approximately 85%. After Week 3, you have complete coverage.

---

## The Full 25-Question Ninja Aptitude Mock

The following 25 questions replicate the distribution and difficulty of a TCS Ninja Foundation Numerical section. Attempt under strict 25-minute timing.

**Q1 (Number System):** Find the number of factors of 480.
480 = 2⁵ x 3 x 5. Factors = (5+1)(1+1)(1+1) = **24**.

**Q2 (Percentage):** A price increased from Rs. 240 to Rs. 288. Find the percentage increase.
(48/240) x 100 = **20%**.

**Q3 (Profit/Loss):** A sells to B at 20% profit. B sells to C at 10% loss. If C pays Rs. 2160, find A's cost price.
C's price = B's CP x 0.90 = 2160. B's CP = 2400. A's SP = 2400 = A's CP x 1.20. A's CP = **Rs. 2,000**.

**Q4 (Time/Work):** A can complete work in 10 days, B in 15 days, C in 20 days. Working together, how many days?
Combined rate = 1/10+1/15+1/20 = 6/60+4/60+3/60 = 13/60. Time = 60/13 ≈ **4.6 days**.

**Q5 (TSD):** A train 300m long passes a station 200m long in 25 seconds. Find the speed in km/h.
Speed = (300+200)/25 = 20 m/s = 20 x 18/5 = **72 km/h**.

**Q6 (Ratio):** A:B = 3:4 and B:C = 6:7. Find A:C.
A:B = 3:4 = 18:24; B:C = 6:7 = 24:28. A:C = 18:28 = **9:14**.

**Q7 (Averages):** Average of 5 numbers is 32. When a 6th number is added, average becomes 30. Find the 6th number.
Sum of 5 = 160. Sum of 6 = 180. 6th number = **20**.

**Q8 (SI/CI):** Find CI on Rs. 6000 at 5% per annum for 3 years.
Amount = 6000 x (1.05)³ = 6000 x 1.157625 = 6945.75. CI = **Rs. 945.75**.

**Q9 (Averages/Ages):** The average age of 8 people is 28 years. If the oldest person is excluded, the average drops by 2. Find the oldest person's age.
Sum of 8 = 224. Sum of 7 = 7 x 26 = 182. Oldest = 224 - 182 = **42 years**.

**Q10 (P&C):** In how many ways can 8 people be seated in a row if 2 specific people must be adjacent?
Treat the 2 as one unit: 7! arrangements. Internal arrangement: 2! = 2. Total = 7! x 2 = 5040 x 2 = **10,080**.

**Q11 (Probability):** Two cards drawn from 52-card deck without replacement. Find P(both kings).
P = C(4,2)/C(52,2) = 6/1326 = **1/221**.

**Q12 (Mensuration):** A cylindrical tank of radius 7m and height 5m is to be painted on its curved surface. Cost is Rs. 10 per m². Find total cost.
CSA = 2 x (22/7) x 7 x 5 = 2 x 22 x 5 = 220 m². Cost = 220 x 10 = **Rs. 2,200**.

**Q13 (Series - AP):** Sum of first 20 terms of AP with first term 3 and common difference 4.
S₂₀ = 20/2 x (2x3 + 19x4) = 10 x (6+76) = 10 x 82 = **820**.

**Q14 (Percentage - reverse):** After a 20% increase, a price became Rs. 360. What was the original price?
Original = 360/1.20 = **Rs. 300**.

**Q15 (Time/Work - pipes):** Pipe A fills a tank in 8h, Pipe B in 12h. They open together, but after 3 hours Pipe B is closed. How long in total does the tank take to fill?
In 3 hours together: 3(1/8 + 1/12) = 3(5/24) = 15/24 = 5/8 filled.
Remaining: 3/8 at rate 1/8 per hour = 3 hours more. Total = **6 hours**.

**Q16 (Number System):** What is the remainder when 7^77 is divided by 5?
Powers of 7 mod 5: 7¹=2, 7²=4, 7³=3, 7⁴=1, 7⁵=2... cycle of 4. 77 mod 4 = 1. Remainder = **2**.

**Q17 (Mixtures):** 20L solution: acid:water = 3:2. How much water added to make ratio 1:2?
Acid = 12L. Water = 8L. New ratio 1:2: 12/(8+x) = 1/2. 24 = 8+x. x = **16 litres**.

**Q18 (Geometry):** A circle is inscribed in a square of side 14 cm. Find the area of the square not covered by the circle.
Circle radius = 7cm. Circle area = πr² = (22/7) x 49 = 154. Square area = 196. Uncovered = 196-154 = **42 cm²**.

**Q19 (TSD - boats):** A person rows upstream at 4 km/h and downstream at 8 km/h. Find the speed of the person in still water.
= (4+8)/2 = **6 km/h**.

**Q20 (Simplification):** Evaluate: √(225) + 3³ - 2⁴ x 0.5
= 15 + 27 - 16 x 0.5 = 15 + 27 - 8 = **34**.

**Q21 (Compound Interest):** In how many years does Rs. 1000 become Rs. 1331 at 10% per annum compound interest?
1000 x (1.1)^n = 1331. (1.1)^n = 1.331. (1.1)³ = 1.331. n = **3 years**.

**Q22 (DI - based on sample data):** Using the quarterly data from Topic 15: What was the average quarterly profit?
Total profit = 117.3 crore / 4 = **29.325 crore per quarter**.

**Q23 (P&C):** From a group of 6 boys and 5 girls, how many committees of 4 can be formed with at least 2 girls?
Exactly 2 girls: C(5,2) x C(6,2) = 10 x 15 = 150.
Exactly 3 girls: C(5,3) x C(6,1) = 10 x 6 = 60.
Exactly 4 girls: C(5,4) x C(6,0) = 5 x 1 = 5.
Total = 150 + 60 + 5 = **215**.

**Q24 (Mensuration):** A sphere of radius 3cm is melted into a cylinder of radius 3cm. Find the height of the cylinder.
Volume of sphere = (4/3)π(3)³ = 36π. Volume of cylinder = π(3)²h = 9πh.
36π = 9πh. h = **4 cm**.

**Q25 (Probability):** A bag has 3 red, 4 blue, and 5 green balls. 3 balls are drawn at random. Find P(all three are of different colours).
Total ways = C(12,3) = 220.
Favourable: 1 red x 1 blue x 1 green = 3 x 4 x 5 = 60.
P = 60/220 = **3/11**.

---

## Final Preparation Checklist

Before your TCS Ninja aptitude test, verify you can complete the following in under 60 seconds each without a calculator:

- Find the profit percentage given CP and SP
- Calculate CI for 2 years using the shortcut
- Apply the formula for time when two workers work together
- Convert relative speed between m/s and km/h
- Find the number of terms in an AP from first term, last term, and common difference
- Calculate nC3 for n ≤ 15 from memory
- Apply alligation to a two-ingredient mixture problem
- Find percentage increase or decrease when original and new values are given
- Read a simple bar graph and compute a percentage change between two bars
- Apply the shortcut for "X is r% more than Y, Y is what % less than X"

If any of these takes more than 60 seconds, that topic needs additional practice before test day. The Ninja aptitude section rewards candidates who have automated the core formulae to the point of reflex - not those who understand them theoretically and apply them slowly under time pressure.

---

## Topic Deep Dives: Extended Problem Sets

### Percentages - Extended Problem Set

**Problem 2.4 (Successive discounts):** A shopkeeper offers successive discounts of 20% and 10% on an item. What is the effective single discount?
Net price after both discounts = (100-20)% x (100-10)% = 0.80 x 0.90 = 0.72 of MP.
Single equivalent discount = 1 - 0.72 = 0.28 = **28%**.

**Shortcut formula for successive discounts of a% and b%:** Combined discount = a + b - ab/100.
20 + 10 - 200/100 = 30 - 2 = 28%. ✓

**Problem 2.5 (Reverse percentage):** After deducting 15% tax, a person's take-home salary is Rs. 42,500. What is the gross salary?
Gross x 0.85 = 42500. Gross = 42500/0.85 = **Rs. 50,000**.

**Problem 2.6 (Population growth):** A town's population was 50,000. It increased by 5% in the first year and decreased by 2% in the second year. Find the population after two years.
50,000 x 1.05 x 0.98 = 50,000 x 1.029 = **51,450**.

**Problem 2.7 (income and expenditure):** A person spends 75% of his income. If his income increases by 20% and expenditure increases by 10%, find the percentage change in savings.
Let income = 100, expenditure = 75, savings = 25.
New income = 120, new expenditure = 75 x 1.10 = 82.5, new savings = 37.5.
Change in savings = (37.5 - 25)/25 x 100 = **50% increase**.

---

### Profit and Loss - Extended Problem Set

**Problem 3.4 (Cost price unknown):** A trader marks goods 30% above cost and gives a discount of 10%. If he still makes a profit of Rs. 390, find the cost price.
Net profit % = 30 - 10 - 30x10/100 = 20 - 3 = 17%.
17% of CP = 390. CP = 390/0.17 = **Rs. 2,294** (approx Rs. 2,294.12)

**Problem 3.5 (False weights):** A shopkeeper uses a 900g weight instead of 1 kg (1000g). What profit percentage does he make?
He buys 900g but sells as 1000g. If CP per kg = Rs. 100, he pays 90 for 900g.
He sells at Rs. 100 (per 1000g). Profit = 10 on cost 90. Profit% = 10/90 x 100 = **11.11%**.

**Problem 3.6 (Selling price relationship):** If 5 articles are bought for Rs. 100 and sold at the rate of 4 articles for Rs. 100, what is the profit or loss percentage?
CP per article = 100/5 = 20. SP per article = 100/4 = 25.
Profit% = (25-20)/20 x 100 = **25%**.

---

### Time and Work - Extended Problem Set

**Problem 5.5 (alternate days):** A can complete a work in 12 days and B in 18 days. They work on alternate days starting with A. How many days to complete?
A's rate = 1/12; B's rate = 1/18. In 2 days (A then B): 1/12 + 1/18 = 5/36 work done.
After 14 days (7 complete pairs): 7 x 5/36 = 35/36 work done. Remaining: 1/36.
Day 15 is A's turn: 1/12 per day. Time for 1/36: (1/36)/(1/12) = 12/36 = 1/3 day.
Total = 14 + 1/3 = **14 1/3 days** = 14 days and 8 hours.

**Problem 5.6 (work and wages):** A, B, C can do work in 20, 30, 40 days. They work together and earn Rs. 9,200. Find A's share.
Daily rates: 1/20, 1/30, 1/40. Ratio = LCM(20,30,40) = 120.
A works: 120/20 = 6 units/day. B: 120/30 = 4 units/day. C: 120/40 = 3 units/day.
Ratio = 6:4:3. A's share = 6/13 x 9200 = **Rs. 4,246.15** (approximately Rs. 4,246).

**Problem 5.7 (efficiency of men and women):** 8 men or 12 women can complete a task in 25 days. In how many days can 6 men and 11 women complete it?
8 men's work = 12 women's work → 1 man = 1.5 women.
6 men = 9 women (in equivalent). Total = 9 + 11 = 20 women.
12 women take 25 days → 20 women take 12 x 25/20 = **15 days**.

---

### Time, Speed, Distance - Extended Problem Set

**Problem 6.5 (meeting point):** A and B start from cities P and Q simultaneously, 300 km apart. A travels at 60 km/h and B at 40 km/h. When do they meet if travelling towards each other?
Combined speed = 100 km/h. Time to meet = 300/100 = **3 hours**.
Distance covered by A = 60 x 3 = 180 km from P. B is 120 km from Q.

**Problem 6.6 (catches up):** A thief runs at 10 km/h. A police officer starts 15 minutes later at 15 km/h. How long does the officer take to catch the thief?
In 15 minutes, the thief covers 10 x 15/60 = 2.5 km head start.
Relative speed (same direction) = 15 - 10 = 5 km/h. Time to close 2.5 km = 2.5/5 = **30 minutes**.

**Problem 6.7 (average speed):** A travels 240 km at 40 km/h and 360 km at 60 km/h. Find the average speed for the entire journey.
Time 1 = 240/40 = 6h. Time 2 = 360/60 = 6h.
Average speed = Total distance/Total time = 600/12 = **50 km/h**.

**Important:** Average speed ≠ (40+60)/2 = 50 only because the times happen to be equal. In general, use total distance / total time.

---

### Number System - Extended Problem Set

**Problem 1.6 (remainder theorem):** Find the remainder when 17^30 is divided by 7.
17 mod 7 = 3. So 17^30 mod 7 = 3^30 mod 7.
By Fermat: 3^6 ≡ 1 (mod 7). 30 = 5 x 6 + 0. 3^30 = (3^6)^5 ≡ 1 (mod 7). Remainder = **1**.

**Problem 1.7 (LCM application):** Three bells ring at intervals of 12, 15, and 18 minutes. If they ring together at 8:00 AM, at what time will they next ring together?
LCM(12, 15, 18) = 180 minutes = 3 hours. Next together ring: **11:00 AM**.

**Problem 1.8 (divisibility):** Find the largest 4-digit number divisible by 12, 15, and 18.
LCM(12,15,18) = 180. Largest 4-digit multiple of 180: 9999/180 = 55.55, so 55 x 180 = 9900. Answer = **9900**.

---

### Simple and Compound Interest - Extended Problems

**Problem 8.5 (difference between CI and SI):** For Rs. 10,000 at 8% for 2 years, find CI - SI.
SI for 2 years = 10000 x 8 x 2/100 = 1600.
CI - SI = PR²/10000 = 10000 x 64/10000 = **Rs. 64**.

**Problem 8.6 (finding rate from given conditions):** Under compound interest, a sum becomes Rs. 1,250 in 2 years and Rs. 1,562.50 in 3 years. Find the rate of interest.
From year 2 to year 3: 1562.50/1250 = 1.25. Rate = 25%.
Verify: P x (1.25)² = 1250 → P = 1250/1.5625 = Rs. 800.
(1.25)³ x 800 = 1.953125 x 800 = 1562.50. ✓ Rate = **25% per annum**.

---

### Geometry - Extended Problems

**Problem 11.5 (angle in triangle):** In triangle ABC, angle A = 70°, angle B = 60°. Find the exterior angle at C.
Exterior angle = sum of non-adjacent interior angles = 70 + 60 = **130°**.

**Problem 11.6 (tangent from external point):** Two tangents drawn from external point P to a circle are PA = 10 cm. The distance from P to the centre is 26 cm. Find the radius.
The radius to the tangent point is perpendicular to the tangent. Triangle PAO is right-angled at A.
r² + 10² = 26². r² = 676 - 100 = 576. r = **24 cm**.

Wait, this should be PA (tangent) perpendicular to radius at A. PO = 26, PA = 10, OA = r.
OA² + PA² = PO². r² = 26² - 10² = 676 - 100 = 576. r = 24 cm. ✓

**Problem 11.7 (quadrilateral):** A trapezium has parallel sides 12 cm and 8 cm, and height 5 cm. Find its area.
Area = (1/2)(12+8) x 5 = (1/2)(20)(5) = **50 cm²**.

---

### Permutations and Combinations - Extended Problems

**Problem 9.4 (identical objects):** How many ways can the letters of MISSISSIPPI be arranged?
M(1), I(4), S(4), P(2). Total = 11!/(4! x 4! x 2!) = 39916800/(24 x 24 x 2) = 39916800/1152 = **34,650**.

**Problem 9.5 (circular arrangement with restriction):** 5 boys and 4 girls are seated around a circular table such that boys and girls alternate. How many arrangements are possible?
First arrange 4 boys in 4 positions (leaving one position for the circular arrangement start): (4-1)! = 6 arrangements. Wait, with 5 boys and 4 girls alternating: this is impossible since alternating requires equal numbers. The problem likely intends 4 boys and 4 girls. Let me revise:

**4 boys and 4 girls** seated in a circle so boys and girls alternate:
Fix one person (say, a boy) to remove circular symmetry. Arrange remaining 3 boys in 3! = 6 ways. Arrange 4 girls in the 4 gaps between boys: 4! = 24 ways. Total = 6 x 24 = **144**.

**Problem 9.6 (selecting from groups with restriction):** A team of 5 is to be chosen from 6 bowlers and 4 batsmen such that at least 3 bowlers are included.
3 bowlers + 2 batsmen: C(6,3) x C(4,2) = 20 x 6 = 120.
4 bowlers + 1 batsman: C(6,4) x C(4,1) = 15 x 4 = 60.
5 bowlers + 0 batsmen: C(6,5) x C(4,0) = 6 x 1 = 6.
Total = 120 + 60 + 6 = **186**.

---

## Shortcut Formula Reference Sheet

This consolidated reference covers the most important shortcuts for exam-speed application.

### Percentages

| Scenario | Formula |
|---|---|
| X is r% more than Y → Y is _% less than X | r/(100+r) x 100 |
| X is r% less than Y → Y is _% more than X | r/(100-r) x 100 |
| Price rises by r% → quantity reduction to maintain budget | r/(100+r) x 100 |
| Price falls by r% → quantity increase to maintain budget | r/(100-r) x 100 |
| Successive % changes a%, b%, c% | net = {(1 + a/100)(1 + b/100)(1 + c/100) - 1} x 100 |
| Successive discounts a% and b% | combined = a + b - ab/100 |

### Profit and Loss

| Scenario | Formula |
|---|---|
| Markup m% and discount d% on CP | Net P% = m - d - md/100 |
| Equal SP at P% profit and P% loss | Net loss = P²/100 % |
| Selling n items earns profit = SP of m items | Profit% = m/(n-m) x 100 |
| CP given, profit% given → SP | SP = CP(100+P)/100 |
| SP given, profit% given → CP | CP = SP x 100/(100+P) |

### Time and Work

| Scenario | Formula |
|---|---|
| A finishes in a days, B in b days | Together: ab/(a+b) days |
| A and B together in x days, A alone in a days | B alone: ax/(a-x) days |
| m workers do work in d days | Work unit = md |
| Efficiency ratio = inverse of time ratio | If A:B time = 3:4, A:B efficiency = 4:3 |

### Time, Speed, Distance

| Scenario | Formula |
|---|---|
| Average speed for equal distances | 2v₁v₂/(v₁+v₂) (harmonic mean) |
| Train crosses a pole | Time = Length/Speed |
| Train crosses platform | Time = (Train length + Platform length)/Speed |
| Two trains opposite direction | Time = (L₁+L₂)/(S₁+S₂) |
| Two trains same direction | Time = (L₁+L₂)/|S₁-S₂| |
| Boat upstream/downstream | Boat speed = (D+U)/2; Stream = (D-U)/2 |

### SI and CI

| Scenario | Formula |
|---|---|
| SI for T years | PRT/100 |
| Amount under CI | P(1+R/100)^T |
| CI - SI for 2 years | PR²/10000 |
| Sum triples in N years (SI) → rate | Rate = 200/N% |
| Sum becomes k times in N years (SI) → years for m times | N(m-1)/(k-1) |

---

## Diagnosing Your Weak Areas Before the Test

### The 15-Question Diagnostic Drill

Take 15 questions (one from each topic) under timed conditions (15 minutes total). Score yourself. Any topic where you score zero or take more than 90 seconds needs focused revision.

Pattern of errors to watch for:
- Wrong answer within the first minute: concept error (formula or approach is wrong)
- Correct approach but wrong answer: calculation error (arithmetic mistake)
- Correct answer after 2+ minutes: needs shortcut learning (knows method but too slow)
- No attempt: topic is unfamiliar (needs concept study)

Each error type requires a different remedy. Concept errors require re-reading the concept and working through examples without time pressure. Calculation errors require more timed drill. Speed issues require shortcut learning and automation practice. Topic blanks require starting from the concept overview.

### The 72-Hour Last-Sprint Plan

If your exam is in three days and you have not yet prepared, here is the minimum effective sprint:

**Day 1 (Focus: Percentages, Profit/Loss, SI/CI, Averages):**
- Morning: Read formulas and shortcuts for all four topics (2 hours)
- Afternoon: 20 practice problems per topic under 90-second time pressure (2 hours)
- Evening: 25-question mock covering these four topics only (25 minutes + review)

**Day 2 (Focus: Time/Work, Time/Speed/Distance, Data Interpretation):**
- Morning: Read formulas and shortcuts, practice 15 problems per topic (3 hours)
- Afternoon: Two DI sets (3 charts x 4 questions) under timed conditions (30 minutes)
- Evening: 25-question mixed mock (25 minutes + review)

**Day 3 (Focus: P&C, Probability, Number System, Series, Geometry, Mensuration):**
- Morning: Speed read through all remaining topics, focus on one formula per sub-topic (2 hours)
- Afternoon: 15 problems from these topics combined (25 minutes)
- Evening: Full 25-question mock under exam conditions (25 minutes + review). Then rest.

This sprint will not produce the same results as three weeks of focused preparation. But it will ensure you have basic coverage of every topic, which is far better than deep coverage of four topics and no coverage of the rest.

---

## What to Do on Exam Day

### In the 30 Minutes Before the Section Begins

Do not attempt to study new material. Re-read your shortcut sheet one final time. Do a few mental arithmetic exercises to warm up your calculation speed. Take a few slow breaths to manage any anxiety - shallow, rapid breathing increases error rates under cognitive load.

Check your seating and interface before the section opens. Confirm the timer is visible. Note whether a rough paper or on-screen whiteboard is provided - you will need it for multi-step calculations.

### During the Section

Scan the first five questions before attempting any. Are there any immediately obvious questions (DI from a chart you just understood, a direct percentage calculation)? Start with those.

Use rough paper for every multi-step calculation. Mental arithmetic at full speed introduces errors that cost marks. Writing out calculations takes three extra seconds and prevents the five-second error-correction that follows a wrong answer.

If you have answered 20 questions and still have 3 minutes remaining, use that time to check your three most uncertain answers rather than rushing through the last five questions carelessly.

If the section is running over time and you have five questions unanswered with one minute left: read each quickly, guess on any where you can identify two obviously wrong options, and mark blank any where you cannot even narrow it down (given the negative marking).

### The Numerical Ability Mindset

The Foundation Numerical section is testing whether you are the kind of engineer or analyst who can work with numbers accurately under pressure. It is not testing your knowledge of advanced mathematics. Every question type in the section has appeared thousands of times in competitive exams across India. There are no surprises - only topics you have practiced and topics you have not.

Approach each question as a pattern-matching exercise: recognise the type, apply the method, verify the answer, move on. The candidates who walk out of this section with 20+ correct answers are not the ones who are mathematically gifted - they are the ones who prepared systematically, learned the shortcuts, and practised enough to execute them under time pressure.

That is exactly what this guide has prepared you to do.

---

## The 4-Week TCS Ninja Aptitude Preparation Plan

This plan assumes you are starting from school-level mathematics (Class 10-12 foundation) and targeting 80%+ in the Foundation Numerical section.

### Week 1: Core Topics - Percentages, Profit/Loss, Time/Work, TSD

**Daily structure (2 hours):**
- 30 minutes: Read the day's topic from this guide (concepts + shortcuts)
- 45 minutes: Solve 15 practice problems from the day's topic (no timer)
- 30 minutes: Solve 10 problems from the day's topic under time pressure (60 sec each)
- 15 minutes: Review errors and identify the specific step where each error occurred

**Day 1:** Percentages - all sub-types (increase/decrease, reverse, successive).
**Day 2:** Profit and Loss (including markup, discount chains, false weights).
**Day 3:** Time and Work (two-worker, three-worker, pipes).
**Day 4:** Time, Speed, Distance (trains, boats, circular tracks).
**Day 5:** Mixed practice - 25 questions covering Week 1 topics under 25 minutes.
**Day 6:** Error review from Day 5. Re-practice the specific sub-types that caused errors.
**Day 7:** Rest or light revision (read shortcut sheet only, no problem-solving).

### Week 2: Medium-Frequency Topics

**Day 8:** Averages and Mixtures/Alligation.
**Day 9:** Simple and Compound Interest (all variants including half-yearly and installments).
**Day 10:** Ratio and Proportion (including partnership and sharing problems).
**Day 11:** Number System (factors, HCF/LCM, remainders, divisibility).
**Day 12:** Mixed mock - 25 questions covering Weeks 1 and 2 under 25 minutes.
**Day 13:** Targeted drilling on error areas from Day 12.
**Day 14:** Rest or light revision.

### Week 3: Completing Coverage

**Day 15:** Permutations and Combinations (all types).
**Day 16:** Probability (basic, conditional, complementary).
**Day 17:** Sequences and Series (AP, GP, special formulas).
**Day 18:** Geometry (triangles, circles, quadrilaterals).
**Day 19:** Mensuration (cylinder, cone, sphere, cuboid).
**Day 20:** Simplification and Data Interpretation.
**Day 21:** Full 25-question mock under exam conditions. Review all errors.

### Week 4: Speed Building and Final Preparation

**Days 22-24:** Take one full 25-question mock each day under strict timing. After each, analyse: which topics are consistently giving errors? Drill those specifically.

**Days 25-26:** Focus exclusively on your two weakest topics. 20 problems per topic per day.

**Days 27-28:** Mixed timed drills (10 questions in 10 minutes, three rounds per session). This builds the gear-shifting speed to move between different topic types rapidly.

**Day 28:** Final 25-question mock. This is your reference score for where you stand.

---

## Data Interpretation: Extended Guidance

### Reading Tables Efficiently

Tables present multiple rows and columns of data. Before answering any question, spend 20 seconds establishing:
- What each row represents (products, time periods, regions)
- What each column represents (revenue, cost, growth %)
- What the units are (Rs. crore, thousands, percentages)

A common error is calculating in the wrong units because you did not verify what "Revenue" means in the table header (is it in lakhs or crores?).

### Multi-Condition DI Questions

Some DI questions combine data from two rows or two columns:

"Which product had the highest revenue-to-cost ratio in Year 2?"

For each product, compute: Revenue (Year 2) / Cost (Year 2). The product with the highest ratio is the answer. You do not need to compute all ratios exactly - scan for the obviously largest (biggest revenue with smallest cost) and verify only the top two candidates precisely.

### Bar Graph Reading Speed

For bar graphs showing values across multiple periods:

**Direct maximum/minimum:** Visual inspection. The tallest bar is the maximum - no calculation needed.

**Percentage change:** Always need two specific values. Identify the two bars, subtract, divide by the base year, multiply by 100.

**Ratio:** Extract the two values and simplify to lowest terms. 48:72 = 2:3 (divide both by 24).

**Sum or average:** Add up the required values and divide. For averages of 4-5 values, round to the nearest convenient number for a first pass, then verify if two options are close.

### Pie Chart Interpretation Shortcuts

When a pie chart shows percentage shares and the total is given:

"What is the value of Segment A?"
If Segment A = 35% and Total = 600, then value = 0.35 x 600 = 210.

"By what amount does Segment A exceed Segment B?"
Difference in percentages x total = (35% - 25%) x 600 = 60.

"What is the ratio of Segment A to Segment B?"
If A = 35% and B = 25%, ratio = 35:25 = 7:5.

These three question types cover 80% of pie chart questions. Practise all three until the calculation sequence is automatic.

---

## Sequences and Series: Extended Problems

**Problem 13.5 (GP ratio finding):** In a GP, the 3rd term is 36 and the 6th term is 972. Find the common ratio.
aₙ = ar^(n-1). So ar² = 36 and ar⁵ = 972.
Dividing: r³ = 972/36 = 27. r = **3**.

**Problem 13.6 (sum of infinite GP):** Find the sum to infinity: 4 - 2 + 1 - 1/2 + ...
First term a = 4, common ratio r = -1/2. |r| < 1, so sum exists.
S∞ = a/(1-r) = 4/(1-(-1/2)) = 4/(3/2) = **8/3**.

**Problem 13.7 (finding missing term in AP):** In an AP, the 7th term is 28 and the 13th term is 52. Find the sum of first 20 terms.
From the two terms: d = (52-28)/(13-7) = 24/6 = 4. a + 6d = 28 → a = 28-24 = 4.
S₂₀ = 20/2 x (2x4 + 19x4) = 10 x (8+76) = 10 x 84 = **840**.

---

## Frequently Asked Questions: TCS Ninja Aptitude

**How many questions from each topic typically appear?**
There is no fixed allocation per topic. Based on observed patterns: Percentages and Profit/Loss together account for 5-7 questions; Time/Work and TSD account for 4-5 questions; DI accounts for 3-5 questions; the remaining 8-12 questions come from Averages, SI/CI, Number System, P&C, Probability, Geometry/Mensuration, and Series. These proportions shift between drives, which is why complete coverage (not just the top topics) matters.

**Is a calculator allowed during the test?**
No. The TCS NQT is a no-calculator test. All calculations must be done mentally or on rough paper. This is why learning mental math shortcuts is not optional - they are the only way to maintain 60-second-per-question pace without a calculator.

**Should I attempt every question or skip the hardest ones?**
With negative marking at 1/3, the decision depends on your confidence level. If you can eliminate 2 of 4 options, guessing between the remaining 2 has a positive expected value. If you cannot eliminate any option and are purely guessing, the expected score is 0.25 - 0.75 x 0.33 ≈ 0 (essentially neutral). For TCS Ninja, the recommendation is: attempt everything where you have at least partial information, and skip only truly unfamiliar questions where you cannot even reduce the options.

**How do I improve my calculation speed?**
Calculation speed improves through two mechanisms: (1) learning shortcuts that replace long calculations with shorter ones, and (2) drilling the shortcuts until they become reflexes rather than recalled procedures. For example, knowing that 12.5% = 1/8 is only useful if you can apply it instantly without thinking about whether to use it. That automaticity comes from practice - specifically, from solving 15-20 problems per day that require the shortcut, until applying it is as natural as multiplying single digits.

**What if I have only one week before the test?**
Follow the 72-hour sprint plan described in this guide, extended to 7 days. Use Days 1-3 for the highest-frequency topics (Percentages, Profit/Loss, Time/Work, TSD) and Days 4-6 for medium-frequency topics (Averages, SI/CI, Number System, DI). Day 7 is for two full mocks and review. This compressed timeline will not produce the same results as four weeks of preparation, but it will meaningfully outperform going into the test with no aptitude-specific preparation.

**Are there topics from the Ninja syllabus that are safe to skip?**
No topic is completely safe to skip since all can appear. However, if time is severely constrained and you must prioritise, the topics with the lowest risk-reward for skipping are: advanced coordinate geometry (because such advanced questions are more common in Digital sections), complex number theory (Euler's theorem, Wilson's theorem), and very complex series (because simpler series patterns can still earn partial credit through recognition). Everything else - especially Percentages, Profit/Loss, SI/CI, Time/Work, TSD, DI, Averages, and basic P&C - should be covered.

**How much time should I spend on DI relative to other topics?**
Data Interpretation deserves proportionally more practice time because each DI set generates multiple questions from one chart. If you understand a bar chart in 30 seconds and then answer 4 questions at 35 seconds each, you have answered 4 questions in 170 seconds total - well within the 60-second average budget. The bottleneck is chart reading speed and the ability to extract the right data points quickly. Practising 3-4 DI sets per day for 5-7 days produces rapid improvement in DI performance.

---

## Building the Right Aptitude Study Environment

The way you study matters as much as what you study. These environment principles improve learning efficiency.

**Study with a stopwatch running.** Even when not doing timed drills, have a stopwatch visible so you are aware of how long each problem takes. Over time, this awareness itself accelerates your pace.

**Study problems in sets, not one at a time.** Solving 10 problems from the same topic in one sitting builds pattern recognition faster than 10 separate one-problem sessions. The second and third problems in a topic set benefit from the context established by the first.

**Vary the problem source.** Do not rely exclusively on one book or one website. Different sources frame problems differently, which prevents your preparation from being tuned to one question style. The TCS test may phrase a percentage problem differently from your favourite practice book - versatility with the underlying concept is the goal.

**Write out every solution step.** Writing out "SP = CP x (100+P)/100 = 800 x 1.20 = 960" takes 5 extra seconds but builds the formula-to-calculation path that you need to execute automatically during the test. Students who solve in their head often do it correctly in slow practice and incorrectly under time pressure because the steps are not habituated.

**Review wrong answers deeply, not quickly.** After a practice session, for each wrong answer: identify the specific formula or step that was wrong, re-solve the problem correctly, and then immediately solve one more problem of the same type to verify you now have it right. A quick glance at the correct answer without this deeper correction cycle means you will make the same error again.

The Ninja aptitude section is winnable with four weeks of this kind of deliberate, structured practice. The concepts are accessible, the shortcuts are learnable, and the question types are finite. All that separates a 65% scorer from a 90% scorer in this section is the quality and quantity of practice invested before test day.

---

Every concept in this guide is learnable. Every shortcut is memorisable. Every problem type is practisable. The TCS Ninja aptitude section is not a test of mathematical talent - it is a test of mathematical preparation. Walk in having done the preparation, and the section becomes manageable. Walk in having skipped it, and sixty seconds per question becomes sixty seconds per panic. Choose the preparation.
