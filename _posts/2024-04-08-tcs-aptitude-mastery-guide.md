---
layout: post
title: "TCS Aptitude: Topic-Wise Mastery Guide"
page_title: "TCS Aptitude Questions and Answers - Complete Topic-Wise Preparation with Speed-Solving Techniques"
date: 2024-04-08
categories: ["Industry"]
tags: ["TCS aptitude", "TCS quantitative aptitude", "TCS numerical ability", "TCS aptitude questions", "TCS quants"]
excerpt: "Master every TCS aptitude topic with concept refreshers, speed techniques, trap identification, and original practice problems."
image: "/assets/images/technology-industry-analysis-insightcrunch.webp"
reading_time: 60
author: "Insight Crunch Team"
---

The TCS aptitude section does not test mathematical genius - it tests mathematical fluency under time pressure. A candidate who understands the difference between those two things will prepare differently from one who does not. Fluency means pattern recognition is fast, formula recall is automatic, and the decision to skip versus solve is made in under five seconds. Genius is irrelevant when every question has a sixty-second window. This guide builds fluency across every topic that appears in TCS's quantitative sections - Foundation and Advanced - through concept refreshers, speed techniques, trap identification, and original practice problems with full solutions.

![TCS Guide](/assets/images/technology-industry-analysis-insightcrunch.webp)

The guide is organised by topic, from the highest-frequency to the lowest, with a difficulty and ROI rating for each. Read it strategically: master the high-ROI topics first, build speed through the practice problems, and use the Advanced section coverage to target Digital routing if that is your goal. At the end, the [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html) provides a practice platform where you can test your speed across all these topics in a timed, NQT-calibrated environment.

---

## Topic Difficulty and ROI Matrix

Before diving in, use this matrix to prioritise preparation time.

| Topic | Frequency | Difficulty | Prep Effort | ROI | Priority |
|---|---|---|---|---|---|
| Data Interpretation | Very High | Moderate | Medium | Very High | 1 |
| Percentages | Very High | Easy-Moderate | Low | Very High | 1 |
| Time, Speed, Distance | High | Moderate | Low | Very High | 1 |
| Profit and Loss | High | Easy-Moderate | Low | Very High | 1 |
| Averages and Mixtures | Medium | Easy | Very Low | High | 2 |
| Time and Work | Medium | Moderate | Low | High | 2 |
| Ratio and Proportion | Medium | Easy | Very Low | High | 2 |
| Simple and Compound Interest | Medium | Easy | Very Low | High | 2 |
| Permutations and Combinations | Low-Medium | Moderate | Medium | Medium | 3 |
| Probability | Low-Medium | Moderate | Medium | Medium | 3 |
| Number System | Low-Medium | Easy-Moderate | Low | Medium | 3 |
| Sequences and Series | Low | Easy | Low | Medium | 3 |
| Geometry and Mensuration | Low | Moderate | Medium | Low-Medium | 4 |
| Ages and Equations | Low | Easy | Low | Medium | 3 |
| Blood Relations | Low | Easy | Very Low | Medium | 3 |
| Advanced: Logarithms | Very Low | Hard | High | Low | 5 |
| Advanced: Set Theory | Low | Moderate | Medium | Low | 5 |
| Advanced: Functions | Very Low | Hard | High | Low | 5 |

**Priority 1:** Invest maximum time here. Direct multiplier on Foundation score.
**Priority 2:** Cover after Priority 1. Reliable presence in every cycle.
**Priority 3:** Cover in the second week. Occasional presence worth preparing.
**Priority 4:** Cover if time allows. Low frequency, higher effort.
**Priority 5:** Only for Digital/Advanced section targeting.

---

## Topic 1: Number System

**Frequency:** Low-Medium | **Difficulty:** Easy-Moderate | **Priority:** 3

### Concept Refresher

The number system section tests divisibility, HCF/LCM relationships, properties of integers, and remainder calculations. The mathematical depth required is shallow - these questions reward formula memorisation and pattern recognition rather than derivation.

**Divisibility rules (memorise all):**
- By 2: last digit even
- By 3: sum of digits divisible by 3
- By 4: last two digits divisible by 4
- By 6: divisible by both 2 and 3
- By 8: last three digits divisible by 8
- By 9: sum of digits divisible by 9
- By 11: alternating digit sum divisible by 11 (subtract odd-position digits from even-position, result divisible by 11)
- By 12: divisible by both 3 and 4

**HCF and LCM relationship:** HCF(A,B) × LCM(A,B) = A × B (valid for two numbers only)

**Cyclicity of units digits for remainders:**
- Powers of 2: units digits cycle through 2,4,8,6 (period 4)
- Powers of 3: cycle through 3,9,7,1 (period 4)
- Powers of 4: cycle through 4,6 (period 2)
- Powers of 7: cycle through 7,9,3,1 (period 4)
- Powers of 9: cycle through 9,1 (period 2)

### TCS Question Types

**Type 1 - HCF/LCM word problems:** "Find the smallest number divisible by both A and B" requires LCM. "Find the largest number that divides both A and B" requires HCF. "Find the smallest number that when divided by A and B leaves remainder R each time" requires LCM(A,B) + R.

**Type 2 - Units digit of large powers:** Use cyclicity. 7^253 - find position of 253 in the cycle of 4: 253 = 4×63 + 1, so units digit = units digit of 7^1 = 7.

**Type 3 - Divisibility application:** Is 47856 divisible by 11? Alternating sum: 4-7+8-5+6 = 6. Not divisible by 11.

### Speed-Solving Technique: The LCM+R Formula

When a problem says "find the smallest number that when divided by A, B, and C leaves the same remainder R":
Answer = LCM(A, B, C) + R

When the remainders are different: "leaves remainder r1 when divided by A, remainder r2 when divided by B," check whether (A - r1) = (B - r2). If yes: answer = LCM(A,B) - (A - r1).

### Common Traps

**Trap 1:** HCF×LCM = A×B is only valid for two numbers. For three numbers, no such simple relationship exists.

**Trap 2:** "Number of factors of N" requires prime factorisation. If N = 2^a × 3^b × 5^c, the number of factors = (a+1)(b+1)(c+1). Candidates forget the "+1" and undercount.

### Practice Problem

*A production scheduler wants to synchronise three machines that restart every 12, 18, and 30 minutes respectively. They all restart simultaneously at the start of the shift. After how many minutes will they next all restart together?*

Solution: LCM(12, 18, 30). 12 = 2²×3. 18 = 2×3². 30 = 2×3×5. LCM = 2²×3²×5 = 180 minutes.

### Additional Practice: Divisibility and Remainders

*What is the remainder when 17^50 is divided by 18?*

Note that 17 ≡ -1 (mod 18). Therefore 17^50 ≡ (-1)^50 = 1 (mod 18). Remainder = 1.

This "negative representation" trick: when N = (M-1) for some base M, N ≡ -1 (mod M). Powers of N alternate between -1 and +1 depending on whether the exponent is odd or even.

*Find the number of factors of 720.*

720 = 2⁴ × 3² × 5. Number of factors = (4+1)(2+1)(1+1) = 5×3×2 = 30 factors.

---

## Topic 2: Percentages

**Frequency:** Very High | **Difficulty:** Easy-Moderate | **Priority:** 1

### Concept Refresher

Percentages are the most embedded topic in TCS aptitude. They appear directly and as the calculation substrate for profit/loss, interest, DI, and mixtures. The multiplier method is the single most important technique to internalise.

**Multiplier method:** Convert percentage changes to multipliers and chain them.
- 20% increase = multiply by 1.2
- 15% decrease = multiply by 0.85
- Successive changes: multiply the multipliers together

**Reverse percentage formula:** If A is R% more than B, then B is less than A by R/(100+R) × 100.

If A is R% less than B, then B is more than A by R/(100-R) × 100.

### TCS Question Types

**Type 1 - Successive percentage changes:**
A price increases by 30% then decreases by 25%. Net effect?
Multiplier: 1.30 × 0.75 = 0.975. Net: 2.5% decrease.

TCS trap: "a 30% increase followed by a 30% decrease is net zero" - FALSE. It is 1.3 × 0.7 = 0.91, a 9% decrease.

**Type 2 - Population/depreciation:**
A town's population grows at r% per year. Population after T years = P × (1 + r/100)^T.
Machine value depreciates: V × (1 - r/100)^T.

**Type 3 - Percentage of a percentage:**
What is 35% of 40% of 800? = 0.35 × 0.40 × 800 = 112. Sequential multiplication, never add percentages.

### Speed-Solving Technique: The Net Change Formula

For two successive changes of +a% then +b%:
Net change = a + b + ab/100 (where increases are positive, decreases are negative)

Example: +20% then -20%: net = 20 + (-20) + (20×-20)/100 = 0 - 4 = -4%. Net is 4% decrease.

This formula is faster than multiplying (1.20 × 0.80 = 0.96) when the numbers are round.

### Practice Problem

*A retailer marks up a product by 60% above cost. During a sale, the retailer offers a discount of 25% on the marked price. What is the net profit percentage on the cost price?*

Solution: Let CP = 100. MP = 160. Discount 25%: SP = 160 × 0.75 = 120. Profit = 120 - 100 = 20. Net profit = 20%.

Faster using multipliers: 1.6 × 0.75 = 1.2 → 20% profit.

### Additional Practice Problems

*A machine's value depreciates by 15% annually. If the current value is Rs. 40,000, what will it be worth after 3 years?*

Using multiplier: 40,000 × (0.85)³ = 40,000 × 0.614125 = Rs. 24,565.

*The price of a commodity rises by 20% and then falls by 10%. What is the overall percentage change?*

Net change = 20 + (-10) + (20×-10)/100 = 10 - 2 = 8% increase.

*If A earns 25% more than B, by what percentage does B earn less than A?*

Using reverse percentage: 25/(100+25) × 100 = 25/125 × 100 = 20%. B earns 20% less than A.

This asymmetry (A is 25% more than B, but B is only 20% less than A) is a classic TCS trap. The "greater than" and "less than" percentages are never equal when comparing two different bases.

---

## Topic 3: Profit and Loss

**Frequency:** High | **Difficulty:** Easy-Moderate | **Priority:** 1

### Concept Refresher

**Core relationships:**
- SP = CP × (1 + P/100) for profit P%
- SP = CP × (1 - L/100) for loss L%
- CP = SP / (1 + P/100) = SP × 100/(100+P)
- Marked Price (MP) and discount: SP = MP × (1 - D/100)

**When selling price is kept constant across two transactions:**
If one item is sold at a% profit and another at a% loss, net is always a loss of (a²/100)%.

### TCS Question Types

**Type 1 - Chain discount:** MP is discounted by d1%, then by d2%. Effective discount is NOT (d1+d2)%.
Effective SP = MP × (1 - d1/100) × (1 - d2/100).
Effective discount percentage = 1 - (1 - d1/100)(1 - d2/100), expressed as a percentage.

**Type 2 - Profit on marked price vs cost price:**
"A shopkeeper makes a profit of 25% on cost price. What is the profit as a percentage of selling price?"
If CP=100, SP=125. Profit as % of SP = 25/125 × 100 = 20%.

**Type 3 - Dishonest trader:**
A trader uses a weight of 900g instead of 1kg. Gain percentage = (100-90)/90 × 100 = 11.11%.
General formula: Gain% = (Error)/(True value - Error) × 100.

### Speed-Solving Technique: The SP/CP Ratio

Avoid setting up algebraic equations. The ratio SP/CP directly gives the profit or loss:
- SP/CP = 1.25 → 25% profit
- SP/CP = 0.85 → 15% loss
- To find CP from SP: CP = SP × 100/(100+P)

For chain discount problems: always multiply the sequential multipliers, never add discount percentages.

### Practice Problem

*A merchant bought 120 items at Rs. 15 each. He sold 80 items at 20% profit and the remaining 40 items at 10% loss. What is the overall profit or loss percentage?*

Solution:
CP of 120 items = 120 × 15 = 1800
SP of 80 items at 20% profit = 80 × 15 × 1.2 = 1440
SP of 40 items at 10% loss = 40 × 15 × 0.9 = 540
Total SP = 1440 + 540 = 1980
Profit = 1980 - 1800 = 180
Profit% = (180/1800) × 100 = 10%

### Additional Profit/Loss Problems

*Two articles are sold at Rs. 1,200 each. On one, a profit of 20% is made; on the other, a loss of 20% is made. Find the net profit or loss on the entire transaction.*

When SP is the same and profit% = loss%, net is always a loss.
Net loss% = (common %)² / 100 = (20)²/100 = 4%.

CP of profit article = 1200/1.2 = 1000. CP of loss article = 1200/0.8 = 1500.
Total CP = 2500. Total SP = 2400. Loss = 100. Loss% = 100/2500 × 100 = 4%. Confirmed.

*A trader uses weights 25% heavier than standard. What is the gain percentage he makes while appearing to sell at cost price?*

He gives only 0.75 kg while claiming 1 kg. Gain = 0.25/0.75 × 100 = 33.33%.
General formula: if he uses (100-x)% of the actual weight, gain% = x/(100-x) × 100.

---

## Topic 4: Ratio and Proportion / Mixtures / Alligation

**Frequency:** Medium | **Difficulty:** Easy | **Priority:** 2

### Concept Refresher

**Ratios:** A:B = C:D (fourth proportional) → D = BC/A. Mean proportional of A and C = √(AC).

**Alligation rule for mixing two components:**
(Quantity of cheaper) / (Quantity of dearer) = (Price of dearer - Mean price) / (Mean price - Price of cheaper)

Draw the alligation cross: place the two component values on the left and right of the top row, the target mean in the middle row. The cross-differences at the bottom give the mixing ratio.

**Partnership problems:** Profit is divided in the ratio of (investment × time). If A invests P1 for T1 time and B invests P2 for T2 time, profit ratio = P1×T1 : P2×T2.

### TCS Question Types

**Type 1 - Mixture and alligation:** Two types of rice at Rs.30/kg and Rs.50/kg are mixed to make a blend priced at Rs.38/kg. In what ratio should they be mixed?
Alligation: (50-38):(38-30) = 12:8 = 3:2. Mix cheaper:dearer = 3:2.

**Type 2 - Replacement problems:** A container has X litres of liquid A. K litres are removed and replaced with liquid B. After N such operations:
Amount of A remaining = X × (1 - K/X)^N.

**Type 3 - Three-component mixing:** Set up two equations using the given constraints and solve simultaneously.

### Speed-Solving Technique: The Alligation Cross

Draw quickly:
```
Cheaper (C)      Dearer (D)
         Mean (M)
(D-M)            (M-C)
```
Ratio of cheaper to dearer = (D-M) : (M-C).

This visual shortcut bypasses the algebraic setup and answers mixture ratio questions in 20 seconds.

### Practice Problem

*A vessel contains a mixture of milk and water in the ratio 5:3. If 16 litres of the mixture are removed and replaced with 16 litres of water, the ratio becomes 3:5. What is the total volume of the vessel?*

Solution: Let total = V. Milk initially = 5V/8. After removal: milk removed = 16 × (5/8) = 10 litres. Milk remaining = 5V/8 - 10. Total still V. Ratio condition: (5V/8 - 10)/V = 3/8. Solve: 5V/8 - 10 = 3V/8. 2V/8 = 10. V = 40 litres.

---

## Topic 5: Time and Work

**Frequency:** Medium | **Difficulty:** Moderate | **Priority:** 2

### Concept Refresher

**Work rate fraction method:** If a person completes a job in N days, their daily rate is 1/N.
- Combined rate of A and B = 1/a + 1/b
- Time together = ab/(a+b)
- Drain pipe: subtracts from combined rate

**Efficiency ratio:** If A is twice as efficient as B, A's rate is 2 × B's rate. Express both rates in terms of one variable.

**Work done = Rate × Time.** If W total work units, rate of A = W/a per day.

### TCS Question Types

**Type 1 - Mid-work change:** A works alone for T1 days, then A and B together complete the rest. Find total time.
Work done in T1 days = T1 × (1/a). Remaining = 1 - T1/a. Time for rest = (1 - T1/a)/(1/a + 1/b).

**Type 2 - Pipes and cisterns:** Filling pipes add to rate, drain pipes subtract.
Net rate = Σ(filling pipe rates) - Σ(drain pipe rates).

**Type 3 - Work with varying efficiency:** On alternate days with different workers. Set up the pattern for pairs of days, then handle the remainder.

### Speed-Solving Technique: The LCM Method

Instead of fractions, use LCM as total work units.

Example: A takes 12 days, B takes 18 days. LCM(12,18) = 36 units total work.
A's rate = 36/12 = 3 units/day. B's rate = 36/18 = 2 units/day. Together = 5 units/day. Time = 36/5 = 7.2 days.

This eliminates fraction arithmetic entirely - all numbers remain whole.

### Practice Problem

*Two pipes A and B can fill a tank in 20 and 30 minutes respectively. Pipe C can empty the full tank in 40 minutes. All three are opened simultaneously when the tank is empty. In how many minutes will the tank be filled?*

Solution using LCM: LCM(20,30,40) = 120 units.
A fills: 120/20 = 6 units/min. B fills: 120/30 = 4 units/min. C empties: 120/40 = 3 units/min.
Net rate = 6 + 4 - 3 = 7 units/min. Time = 120/7 = 17 1/7 minutes.

### Additional Work Problems

*A can complete a task in 12 days. B is 50% more efficient than A. How long does B take alone?*

B's rate = 1.5 × A's rate = 1.5/12 = 1/8 of the job per day. B takes 8 days.

*A and B together complete a job in 6 days. A alone takes 10 days. C alone takes 15 days. In how many days can B and C together complete the job?*

A's rate = 1/10. A+B rate = 1/6. B's rate = 1/6 - 1/10 = 5/30 - 3/30 = 2/30 = 1/15.
C's rate = 1/15. B+C rate = 1/15 + 1/15 = 2/15. Time = 15/2 = 7.5 days.

*Worker A can build a wall in 30 days. Worker B can destroy the same wall in 20 days. If both start working simultaneously (A building, B destroying), when will the wall be complete?*

Using LCM(30,20) = 60 units. A builds 2 units/day, B destroys 3 units/day. Net: A builds 2 but B destroys 3, so the wall NEVER gets completed - B destroys faster than A builds. Output this insight: the answer is "never" or the wall cannot be completed. TCS uses variants of this where the net rate is positive but small.

---

## Topic 6: Time, Speed, and Distance

**Frequency:** High | **Difficulty:** Moderate | **Priority:** 1

### Concept Refresher

**Fundamental:** Distance = Speed × Time. All three quantities must use consistent units.

**Average speed:** If equal distances are covered at speeds S1 and S2:
Average speed = 2S1S2/(S1+S2) (harmonic mean, NOT arithmetic mean)

If equal times are spent at speeds S1 and S2:
Average speed = (S1+S2)/2 (arithmetic mean)

**Relative speed:**
- Same direction: |S1 - S2|
- Opposite directions: S1 + S2

**Trains:**
- Train crossing a pole or person: Distance = length of train
- Train crossing a platform: Distance = length of train + length of platform
- Two trains crossing each other: Distance = sum of lengths, speed = relative speed

**Boats and streams:**
- Downstream speed = Boat speed + Stream speed
- Upstream speed = Boat speed - Stream speed
- Boat speed = (Downstream + Upstream)/2
- Stream speed = (Downstream - Upstream)/2

### TCS Question Types

**Type 1 - Average speed trap:** This is the single most common TCS trap in this topic. If a journey has two legs of equal DISTANCE at different speeds, the average speed is the harmonic mean. Many candidates apply the arithmetic mean and get the wrong answer.

**Type 2 - Meeting point problems:** Two people/vehicles start from A and B simultaneously and move toward each other. They meet when their combined distance equals the total distance AB.
Time to meet = Total distance / (Sum of speeds)

**Type 3 - Pursuit problems:** A faster vehicle starts from the same point as a slower one but T hours later. Time to catch up = (Slower speed × T) / (Faster speed - Slower speed).

### Speed-Solving Technique: The Closing Speed Method

For two objects moving toward each other, treat them as a single object closing the gap at (S1+S2) per unit time. For same direction, closing at |S1-S2|. This converts two-body problems into single-body problems instantly.

### Practice Problem 1 (Classic Trap)

*A vehicle travels from city A to city B at 60 km/h and returns at 90 km/h. What is the average speed for the round trip?*

Wrong answer (arithmetic mean): (60+90)/2 = 75 km/h.
Correct answer: 2×60×90/(60+90) = 10800/150 = 72 km/h.

### Practice Problem 2 (Trains)

*Train X of length 250m travelling at 72 km/h and Train Y of length 350m travelling at 54 km/h approach each other on parallel tracks. How long does it take for the trains to completely cross each other?*

Relative speed (opposite directions) = 72 + 54 = 126 km/h = 126 × (1000/3600) = 35 m/s.
Total distance = 250 + 350 = 600m.
Time = 600/35 = 120/7 ≈ 17.14 seconds.

### Practice Problem 3 (Boats and Streams)

*A boat travels 30 km downstream and 20 km upstream in the same time. If the stream speed is 5 km/h, what is the boat speed in still water?*

Let boat speed = B. Downstream speed = B+5. Upstream speed = B-5.
Time downstream = 30/(B+5). Time upstream = 20/(B-5). These are equal:
30/(B+5) = 20/(B-5)
30(B-5) = 20(B+5)
30B - 150 = 20B + 100
10B = 250
B = 25 km/h.

### Practice Problem 4 (Pursuit)

*Person A leaves city P for city Q at 6:00 AM at 40 km/h. Person B leaves the same city at 8:00 AM for city Q at 60 km/h. When will B catch up with A?*

By 8:00 AM, A has a 2-hour headstart: distance covered = 40 × 2 = 80 km.
Relative speed of B gaining on A = 60 - 40 = 20 km/h.
Time to close 80 km gap = 80/20 = 4 hours after B starts.
B catches A at 12:00 PM (noon).

---

## Topic 7: Averages and Weighted Averages

**Frequency:** Medium | **Difficulty:** Easy | **Priority:** 2

### Concept Refresher

**Average:** Sum of all values / Count of values.

**Effect of adding/removing an element:**
If a new value X joins a group of N elements with average A:
New average = (N×A + X) / (N+1).
Change in sum = N×A + X. Change in average = (X - A)/(N+1).

**Weighted average:** If group 1 of n1 members has average A1 and group 2 of n2 members has average A2:
Combined average = (n1×A1 + n2×A2) / (n1+n2).

### TCS Question Types

**Type 1 - Average change when a member joins or leaves:**
The average age of a team of 8 people is 30. A new member joins and the average becomes 31. What is the new member's age?
New sum = 9 × 31 = 279. Old sum = 8 × 30 = 240. New member's age = 279 - 240 = 39.

**Type 2 - Incorrect value correction:**
Average of 10 numbers is 40. One number was recorded as 60 instead of 80. Correct average?
Incorrect sum = 400. Correct sum = 400 - 60 + 80 = 420. Correct average = 42.

**Type 3 - Alligation for weighted average ratio:**
Two groups with averages A1 and A2 combine to give average M. Find ratio n1:n2.
n1:n2 = (A2-M):(M-A1). Same as alligation cross.

### Practice Problem

*The average salary of 15 employees in a department is Rs. 45,000. The manager's salary is Rs. 75,000. What is the average salary of the remaining 14 employees?*

Total salary = 15 × 45,000 = 675,000.
Remaining 14 total = 675,000 - 75,000 = 600,000.
Average = 600,000/14 = Rs. 42,857.14.

### Additional Averages Problems

*A cricket player's average score after 20 innings is 38. After the next inning, his average rises to 39. What did he score in the 21st inning?*

Sum after 20 innings = 20 × 38 = 760. Sum after 21 innings = 21 × 39 = 819. 21st inning score = 819 - 760 = 59.

This is the "average change" formula: new score = new average + (new average - old average) × (old count). 39 + (39-38) × 20 = 39 + 20 = 59. Faster than computing total sums.

*The average of 5 numbers is 27. If one number is excluded, the average becomes 25. What is the excluded number?*

Sum of 5 = 5 × 27 = 135. Sum of remaining 4 = 4 × 25 = 100. Excluded = 135 - 100 = 35.

*The average of first N natural numbers is 15. Find N.*

Average of first N natural numbers = (N+1)/2. So (N+1)/2 = 15. N+1 = 30. N = 29.

### Additional Mixture Problems

*A 40-litre solution is 30% salt. How many litres of water should be added to make it 20% salt?*

Salt present = 40 × 0.3 = 12 litres (constant). For 20% salt in final solution: 12 = 0.2 × final volume. Final volume = 60 litres. Water to add = 60 - 40 = 20 litres.

Alligation alternative: Mix 30% solution with 0% water to get 20% solution.
Ratio = (0-(-20)) does not apply cleanly here. Direct algebra is faster for this type.

*Coffee at Rs. 60/kg and Rs. 80/kg are mixed in ratio 3:5. A merchant sells the mixture at Rs. 78/kg. Find his profit percentage.*

Cost price of mixture = (3×60 + 5×80)/(3+5) = (180+400)/8 = 580/8 = Rs. 72.50/kg.
SP = Rs. 78/kg. Profit% = (78-72.50)/72.50 × 100 = 5.50/72.50 × 100 = 7.59%.

---

## Topic 8: Simple and Compound Interest

**Frequency:** Medium | **Difficulty:** Easy | **Priority:** 2

### Concept Refresher

**Simple Interest (SI):** SI = P×R×T/100. Total amount = P + SI = P(1 + RT/100).

**Compound Interest (CI):** Amount = P(1 + R/100)^T. CI = Amount - P.

**Half-yearly compounding:** Use R/2 as rate and 2T as time.
**Quarterly compounding:** Use R/4 as rate and 4T as time.

**Key shortcut - CI minus SI for 2 years:**
CI - SI = P(R/100)² for T=2 years. This is the most commonly tested relationship.

**CI minus SI for 3 years:**
CI - SI = P(R/100)² × (R/100 + 3) for T=3 years.

### TCS Question Types

**Type 1 - Compare SI and CI:** "The SI and CI on a principal for 2 years at R% differ by Rs. X. Find P."
P(R/100)² = X. Solve for P.

**Type 2 - Effective rate with compounding:** "What single annual rate gives the same return as R% compounded half-yearly?"
Effective rate = (1 + R/200)² - 1, expressed as percentage.

**Type 3 - Finding time or rate:** Given SI or CI and other parameters, solve algebraically.

### Practice Problem

*The difference between the compound interest and simple interest on a sum of money at 10% per annum for 2 years is Rs. 180. Find the sum.*

Using CI-SI formula: P × (R/100)² = 180
P × (0.1)² = 180
P × 0.01 = 180
P = Rs. 18,000.

### Additional SI/CI Problems

*What principal will amount to Rs. 2,000 in 5 years at 8% per annum simple interest?*

SI formula: Amount = P(1 + RT/100). 2000 = P(1 + 8×5/100) = P × 1.4. P = 2000/1.4 = Rs. 1,428.57.

*In how many years will a sum double at 12.5% per annum simple interest?*

SI = P (amount doubles, so interest earned = P). P = P × 12.5 × T/100. T = 100/12.5 = 8 years.

*A sum of money at compound interest doubles in 4 years. In how many years will it become 8 times?*

If P doubles in 4 years: 2P = P(1+r)^4. So (1+r)^4 = 2.
For 8 times: 8P = P(1+r)^T. (1+r)^T = 8 = 2³ = ((1+r)^4)³. So T = 12 years.

This "powers of doubling" shortcut avoids computing r. If doubling takes D years, then 2^k times takes k×D years.

---

## Topic 9: Permutations and Combinations

**Frequency:** Low-Medium | **Difficulty:** Moderate | **Priority:** 3

### Concept Refresher

**Fundamental counting principle:** If event A can occur in m ways and event B in n ways (independently), both together can occur in m×n ways.

**Permutations (ordered arrangements):**
nPr = n! / (n-r)!

**Combinations (unordered selections):**
nCr = n! / (r! × (n-r)!)

**Special cases:**
- Circular arrangement of n distinct objects: (n-1)!
- Arrangements with identical objects: n! / (p! × q! × ...) where p, q are counts of identical items
- Objects that must be together: treat as single block. (n-k+1)! × k! for k objects together
- Objects that must not be together: total - (arrangements where they ARE together)

### TCS Question Types

**Type 1 - Simple selection/arrangement:** "In how many ways can 5 people be arranged in a row?" = 5! = 120.

**Type 2 - With constraints:** "In how many ways can 5 people sit in a row if A and B must always sit together?"
Treat A+B as one block: 4! × 2! = 48.

**Type 3 - Circular arrangement with relative constraint:** "In how many ways can 6 people sit around a circular table if two specific people must always sit adjacent?"
Treat the pair as one block: 5 entities in a circle = (5-1)! = 24. Pair can arrange internally in 2! = 2 ways. Total = 48.

**Type 4 - Selection with at-least-one:** Use complement. P(at least one) = 1 - P(none selected).

### Practice Problem

*A committee of 4 members is to be formed from 6 men and 4 women such that there is at least 1 woman in the committee. In how many ways can this be done?*

Total ways without restriction = C(10,4) = 210.
Ways with NO women (all men) = C(6,4) = 15.
Ways with at least 1 woman = 210 - 15 = 195.

---

## Topic 10: Probability

**Frequency:** Low-Medium | **Difficulty:** Moderate | **Priority:** 3

### Concept Refresher

**Basic probability:** P(A) = Favourable outcomes / Total outcomes (equally likely).

**Complement rule:** P(not A) = 1 - P(A).

**Addition rule:** P(A or B) = P(A) + P(B) - P(A and B).
For mutually exclusive events: P(A or B) = P(A) + P(B).

**Multiplication rule:**
Independent events: P(A and B) = P(A) × P(B).
Dependent events: P(A and B) = P(A) × P(B|A).

**Conditional probability:** P(A|B) = P(A and B) / P(B).

**Bayes' theorem (basic):** P(B|A) = P(A|B) × P(B) / P(A).

### TCS Question Types

**Type 1 - Drawing without replacement:**
Two cards drawn from a standard deck. P(both aces)?
P = (4/52) × (3/51) = 12/2652 = 1/221.

**Type 2 - "At least one" problems:** Always use complement.
P(at least one head in 3 tosses) = 1 - P(no heads) = 1 - (1/2)³ = 7/8.

**Type 3 - Conditional probability:**
A box has 3 red and 5 blue balls. Two drawn without replacement. P(2nd is red | 1st was red) = 2/7.

### Speed-Solving Technique for "At Least One"

P(at least one success) = 1 - (probability of complete failure)^n

This formula applies when n independent trials each have the same failure probability. It is consistently faster than computing P(exactly 1) + P(exactly 2) + ... directly.

### Practice Problem

*A bag contains 4 white, 6 red, and 5 blue balls. Three balls are drawn randomly. What is the probability that all three are of different colours?*

Total ways = C(15,3) = 455.
Favourable (one of each colour) = C(4,1) × C(6,1) × C(5,1) = 4×6×5 = 120.
P = 120/455 = 24/91.

### Additional Probability Problems

*Two dice are rolled simultaneously. What is the probability that the sum is at least 10?*

Favourable outcomes: Sum=10: (4,6),(5,5),(6,4) = 3. Sum=11: (5,6),(6,5) = 2. Sum=12: (6,6) = 1.
Total favourable = 6. Total outcomes = 36. P = 1/6.

*Probability of A solving a problem is 1/3. Probability of B solving it is 1/4. If both attempt, what is the probability that the problem is solved?*

P(not solved) = P(A fails) × P(B fails) = (2/3) × (3/4) = 1/2.
P(solved) = 1 - 1/2 = 1/2.

This uses the complement through independence: P(at least one solves) = 1 - P(neither solves).

---

## Topic 11: Geometry and Mensuration

**Frequency:** Low | **Difficulty:** Moderate | **Priority:** 4

### Concept Refresher

**2D Area formulas:**
- Triangle: (1/2) × base × height = (s(s-a)(s-b)(s-c))^(1/2) where s = (a+b+c)/2
- Rectangle: length × width
- Parallelogram: base × height
- Trapezium: (1/2)(sum of parallel sides) × height
- Circle: πr²
- Sector of circle: (θ/360) × πr²

**3D Volume and Surface Area:**
- Cube: V = a³, TSA = 6a²
- Cuboid: V = lbh, TSA = 2(lb+bh+hl)
- Cylinder: V = πr²h, CSA = 2πrh, TSA = 2πr(h+r)
- Cone: V = (1/3)πr²h, CSA = πrl where l = √(r²+h²), TSA = πr(r+l)
- Sphere: V = (4/3)πr³, SA = 4πr²

**Similar triangles:** Linear scale factor k → Area scale factor k².

**Coordinate geometry:**
- Distance = √((x2-x1)²+(y2-y1)²)
- Midpoint = ((x1+x2)/2, (y1+y2)/2)
- Slope = (y2-y1)/(x2-x1)
- Line: y - y1 = m(x - x1)

### Practice Problem

*A cylindrical container has radius 7 cm and height 15 cm. It is melted and recast into small spheres of radius 1.75 cm each. How many complete spheres can be made?*

Volume of cylinder = π×7²×15 = 735π cm³.
Volume of one sphere = (4/3)π×(1.75)³ = (4/3)π×5.359 = 7.146π cm³.
Number of spheres = 735π / 7.146π ≈ 102.86 → 102 complete spheres.

Exact: (4/3)π(7/4)³ = (4/3)π×(343/64) = 343π/48.
Number = 735π / (343π/48) = 735 × 48/343 = 35280/343 = 102.86 → 102.

### Additional Geometry Problems

*Find the area of a rhombus whose diagonals are 24 cm and 10 cm.*

Area of rhombus = (1/2) × d1 × d2 = (1/2) × 24 × 10 = 120 cm².

The diagonals of a rhombus bisect each other at right angles. The side length = √(12² + 5²) = √(144+25) = √169 = 13 cm. (This is a 5-12-13 Pythagorean triple - TCS likes to embed these.)

*A conical tent has a slant height of 13 m and base radius 5 m. What is the curved surface area?*

CSA of cone = πrl = π × 5 × 13 = 65π m².

Height = √(l² - r²) = √(169 - 25) = √144 = 12 m. (Another Pythagorean triple: 5-12-13.)

*In a coordinate plane, three points are A(2,3), B(6,3), and C(4,7). Find the area of triangle ABC.*

Using the coordinate formula: Area = (1/2)|x₁(y₂-y₃) + x₂(y₃-y₁) + x₃(y₁-y₂)|
= (1/2)|2(3-7) + 6(7-3) + 4(3-3)|
= (1/2)|2(-4) + 6(4) + 4(0)|
= (1/2)|-8 + 24 + 0|
= (1/2)(16) = 8 square units.

Note: AB is a horizontal line (both y=3) so the base is |6-2|=4. Height is vertical distance from C to line AB = |7-3|=4. Area = (1/2)×4×4 = 8. Same answer, simpler observation.

### Similar Triangle Applications

*Two triangles are similar with perimeters 30 cm and 45 cm. If the area of the smaller triangle is 72 cm², what is the area of the larger triangle?*

Scale factor = 30:45 = 2:3.
Area ratio = (2:3)² = 4:9.
Area of larger = 72 × (9/4) = 162 cm².

---

## Topic 12: Sequences and Series

**Frequency:** Low | **Difficulty:** Easy-Moderate | **Priority:** 3

### Concept Refresher

**Arithmetic Progression (AP):**
nth term: aₙ = a + (n-1)d
Sum of n terms: Sₙ = n/2 × (2a + (n-1)d) = n/2 × (first + last)

**Geometric Progression (GP):**
nth term: aₙ = a × r^(n-1)
Sum of n terms: Sₙ = a(1-rⁿ)/(1-r) for r≠1

**Special sums:**
Sum of first n natural numbers: n(n+1)/2
Sum of first n perfect squares: n(n+1)(2n+1)/6
Sum of first n perfect cubes: [n(n+1)/2]²

**Harmonic Progression (HP):** reciprocals form an AP. If a, b, c are in HP, then 1/a, 1/b, 1/c are in AP.

**AM-GM-HM inequality:** AM ≥ GM ≥ HM for positive numbers.

### TCS Question Types

**Type 1 - Missing term in series:** Identify the pattern (AP: constant difference; GP: constant ratio; second-order AP: differences form AP).

**Type 2 - Sum to specific value:** Use the Sₙ formula and solve for n.

**Type 3 - Series insertion:** Find the number of AP terms between two values.

### Practice Problem

*The sum of first N terms of an AP is 3N² + 5N. Find the 10th term.*

S_n = 3N² + 5N. S_(n-1) = 3(N-1)² + 5(N-1) = 3N²-6N+3+5N-5 = 3N²-N-2.
aₙ = Sₙ - S_(n-1) = (3N²+5N) - (3N²-N-2) = 6N+2.
a₁₀ = 6(10)+2 = 62.

### Additional Series Problems

*Find the sum of all two-digit numbers divisible by 7.*

Two-digit multiples of 7: 14, 21, 28, ..., 98.
First term a=14, last term l=98, common difference d=7.
n = (98-14)/7 + 1 = 84/7 + 1 = 12 + 1 = 13 terms.
Sum = n/2 × (a+l) = 13/2 × 112 = 728.

*In a GP, the 3rd term is 18 and the 6th term is 486. Find the first term and common ratio.*

a₃ = ar² = 18. a₆ = ar⁵ = 486. Divide: r³ = 486/18 = 27. r = 3.
a = 18/r² = 18/9 = 2. First term = 2, ratio = 3.

*What is the sum of the series 1×2 + 2×3 + 3×4 + ... + n×(n+1)?*

General term = k(k+1) = k² + k. Sum = Σk² + Σk = n(n+1)(2n+1)/6 + n(n+1)/2.
= n(n+1)[(2n+1)/6 + 1/2] = n(n+1)[(2n+1+3)/6] = n(n+1)(2n+4)/6 = n(n+1)(n+2)/3.

This is a standard product series. TCS occasionally tests these at the Advanced level.

---

## Topic 13: Ages and Linear Equations

**Frequency:** Low | **Difficulty:** Easy | **Priority:** 3

### Concept Refresher

Age problems always involve setting up linear equations. The key is translating English sentences into algebraic expressions precisely.

**Translation guide:**
- "Five years ago" → current age - 5
- "After 10 years" → current age + 10
- "Twice as old" → 2 × age
- "Their ages are in ratio 3:5" → ages = 3k and 5k for some k

### TCS Question Types

The standard TCS age problem combines two or more of: current ratio, past/future ratio, and age sum. This creates two equations in two unknowns, solved by substitution or elimination.

### Practice Problem

*The ratio of ages of P and Q is 4:7. After 8 years, the ratio will be 7:10. Find the present ages.*

Let P = 4k, Q = 7k.
After 8 years: (4k+8)/(7k+8) = 7/10.
Cross multiply: 10(4k+8) = 7(7k+8).
40k + 80 = 49k + 56. 9k = 24. k = 8/3.
P = 32/3 ≈ 10.67 years, Q = 56/3 ≈ 18.67 years.

Verify: (32/3 + 8)/(56/3 + 8) = (56/3)/(80/3) = 56/80 = 7/10. ✓

---

## Topic 14: Data Interpretation

**Frequency:** Very High | **Difficulty:** Moderate | **Priority:** 1

### Concept Refresher

DI is the highest-frequency single topic in TCS Numerical Ability. Questions appear in sets of 2-4 based on a single chart or table. The data can be: a table, a bar chart, a line graph, a pie chart, or two related charts presented together.

**DI question types:**
1. Percentage change: (new - old) / old × 100
2. Ratio between categories: simply divide the values
3. Total/average: sum or average of a row/column
4. Absolute difference: direct subtraction
5. Two-chart DI: extract one value from Chart A, another from Chart B, combine

**The critical habit:** Read the entire chart BEFORE looking at any question. Spend 30-40 seconds understanding: what are the axes, what are the units, what is the approximate range of values, are there any notable patterns. This front-loaded investment makes each question faster.

### Line Graph DI Pattern

Line graphs show trends over time for one or more variables. TCS uses them to test:
- Rate of change (slope between two points)
- Identifying the period of maximum or minimum growth
- Comparing trends across multiple lines

**Reading technique:** For rate-of-change questions, do not calculate the exact derivative. Use visual inspection to identify steep vs shallow segments - the question will typically ask which period had the highest or lowest growth rate, which can be determined by comparing the visual steepness of adjacent line segments.

**Trap:** "In which year did the value increase the most?" can mean (a) the highest absolute increase or (b) the highest percentage increase. These can have different answers if the baseline values differ across periods. Always check which is asked.

### Pie Chart DI Pattern

Pie charts show distribution of a total across categories. TCS pie chart questions test:
- One category as a percentage of total (already given by the pie chart angle)
- Absolute value of one category when the total is given separately
- Comparison of two categories' absolute values

**Key trap:** A pie chart gives percentages, not absolute values. Without knowing the total, you cannot compute absolute values. TCS always gives the total somewhere - either in the chart itself, in an accompanying table, or in the question.

**Speed technique for pie charts:** Most pie chart percentage questions are direct reads (30-second answer). Absolute value questions require one multiplication: (category %) × total. Do not over-complicate these.

### Two-Chart DI (Advanced Level)

The hardest DI questions combine information from two sources - typically a bar chart and a pie chart, or a table and a line graph. These require:

1. Extract value X from Chart 1
2. Extract value Y from Chart 2
3. Compute the required expression using X and Y

The challenge is that the connection between the two charts (what X and Y mean in relation to each other) must be understood from the chart titles and axis labels before any computation.

**Worked Two-Chart Example:**

Chart A (bar chart): Company's total revenue (in crores) across five product lines: A(40), B(60), C(30), D(50), E(20). Total = 200 crores.

Chart B (pie chart): Product line C's revenue breakdown by region - North(35%), South(25%), East(20%), West(20%).

Question: What is the revenue from Product Line C's North region?

Step 1: Find C's total revenue from Chart A = 30 crores.
Step 2: North's share from Chart B = 35%.
Step 3: C North revenue = 30 × 0.35 = 10.5 crores.

This question type requires reading from both charts in the right sequence and confirming that the connection (C's total revenue from Chart A feeds into Chart B's percentage breakdown) is understood.

### Common DI Traps

**Unit mismatch:** Chart shows "sales in lakhs" but question asks for value in crores. Always check the unit specified in the question vs the unit in the chart.

**Wrong column/row:** Under time pressure, candidates read the wrong row or column. Re-verify the row/column header before noting any value.

**Percentage vs absolute:** "Which category showed maximum growth?" is ambiguous - maximum absolute growth vs maximum percentage growth can have different answers. The question will specify; re-read carefully.

**Base year ambiguity in percentage change:** "Growth compared to the previous period" requires identifying which period is the base.

### Worked DI Example

A table shows quarterly production (in tonnes) for three factories P, Q, R:

|  | Q1 | Q2 | Q3 | Q4 |
|--|--|--|--|--|
| P | 120 | 135 | 150 | 160 |
| Q | 90 | 110 | 125 | 140 |
| R | 80 | 95 | 105 | 120 |

**Question 1:** What is the percentage increase in Factory P's production from Q1 to Q4?
(160-120)/120 × 100 = 40/120 × 100 = 33.33%.

**Question 2:** In which quarter was the combined production of all three factories highest?
Q1: 120+90+80=290. Q2: 340. Q3: 380. Q4: 420. Highest in Q4.

**Question 3:** What is Factory Q's production in Q3 as a percentage of total production across all factories in Q3?
125/(150+125+105) × 100 = 125/380 × 100 = 32.89%.

**Question 4:** By what percentage is Factory R's total annual production less than Factory P's?
R total: 80+95+105+120=400. P total: 120+135+150+160=565. Difference: 165. % less: 165/565 × 100 = 29.2%.

The speed technique: do not compute totals from scratch for each question. Build a running total as you read the chart initially so these values are ready when needed.

---

## Topic 15: Blood Relations

**Frequency:** Low | **Difficulty:** Easy | **Priority:** 3

### Concept Refresher

Blood relation problems describe family relationships through a chain of statements and ask for the relationship between two specific people.

**Critical conventions:**
- Assign gender only when explicitly stated
- Draw the family tree immediately on rough paper
- Conventional symbols: square for male, circle for female, horizontal double line for marriage, vertical lines for parent-child

**Common relationships to know:**
- Father's brother = Paternal uncle
- Mother's sister = Maternal aunt
- Sister's husband = Brother-in-law
- Husband's mother = Mother-in-law
- Mother's only son = The speaker themselves (if the speaker has no siblings)

### Speed-Solving Technique

Never attempt blood relation problems without drawing a diagram. The diagram converts a complex multi-step relationship into a visual read-off. Setup time is 30 seconds; answer time is 5 seconds. This is faster than reasoning through the chain verbally.

### Practice Problem

*A is the father of C. B is the mother of D. C is the son of B. E is the brother of C. F is the only daughter of E. How is A related to F?*

Build the tree: A married B (since C is son of both, C is their child). E is brother of C, so E is also child of A and B. F is only daughter of E - so F is granddaughter of A and B. A is F's paternal grandfather.

---

## The Numerical Ability 25-Minute Decision Framework

Understanding the mechanics of each topic is necessary but not sufficient for clearing TCS aptitude. The 25-minute window for 25 questions imposes a 60-second average constraint that requires active decision-making throughout the section. This framework is the execution layer on top of the content knowledge.

### The Question Triage System

On receiving the Numerical Ability section, execute this triage in the first 90 seconds before answering any question:

**Scan all 25 questions and classify each into:**
- Green (fast, under 45 seconds): direct formula application, DI reads from a single row or column, simple percentage of a percentage
- Yellow (medium, 45-75 seconds): two-step arithmetic, alligation, HCF/LCM word problem
- Red (slow, over 90 seconds): multi-step DI with percentage change, complex time-work with mid-job changes, compound interest with quarterly compounding

**Attack order:** all Green questions first, then Yellow, then Red. Never start a Red question when you have unanswered Green questions remaining.

### The 90-Second Skip Rule

If a question has consumed 90 seconds and is not within 2-3 steps of the final answer, mark it for review and move on immediately. A question that takes 3 minutes at the cost of three 45-second questions is a net loss of 2 marks even if you get the 3-minute question right.

### Formula Recall vs Derivation Time

Every formula in this guide can be applied in 5-10 seconds once recalled automatically. Deriving a formula from first principles under exam pressure takes 20-40 seconds. The difference over 25 questions accumulates to 3-5 minutes - the difference between attempting 22 questions and attempting all 25.

The preparation habit that builds automatic recall: solve at least 20 questions per topic before moving on. Not 5 "understood" examples - 20 executed problems, including timed ones. Understanding creates theoretical knowledge; execution creates automatic recall.

---

## Cross-Topic Integration: Questions That Blend Multiple Concepts

TCS increasingly presents questions that require applying two or three concepts in sequence. Recognising the integrated nature of these questions is an advanced preparation skill.

### Percentage + Profit and Loss Integration

*A trader buys goods worth Rs. 5,000 at a discount of 20%. He then sells them at a 25% profit on the discounted price, but gives a further 10% discount to the final buyer. What is his net profit or loss as a percentage of the original Rs. 5,000?*

Step 1 (Discount): Buy at 80% of 5000 = Rs. 4,000.
Step 2 (25% profit on discounted price): Intended SP = 4000 × 1.25 = Rs. 5,000.
Step 3 (10% further discount): Actual SP = 5000 × 0.9 = Rs. 4,500.
Net outcome: Paid Rs. 4,000, received Rs. 4,500. Profit = Rs. 500.
As % of original Rs. 5,000: 500/5000 × 100 = 10% profit on original price.

### Ratio + Averages Integration

*Three sections of a class have 40, 35, and 45 students with average scores of 72, 78, and 65 respectively. Find the overall average score of the class.*

Weighted average = (40×72 + 35×78 + 45×65) / (40+35+45)
= (2880 + 2730 + 2925) / 120
= 8535 / 120
= 71.125

### TSD + Work Integration

*A job requires 600 person-hours to complete. Team A has 5 workers each working at 8 hours/day. Team B has 8 workers each working at 6 hours/day. Team A works for the first 3 days, then Team B takes over. How many days does Team B need?*

Person-hours per day: Team A = 5×8 = 40 hrs/day. Team B = 8×6 = 48 hrs/day.
Work done by A in 3 days = 3×40 = 120 person-hours.
Remaining = 600 - 120 = 480 person-hours.
Days for B = 480/48 = 10 days.

### Percentages + DI Integration

This is the most common integrated type in TCS DI sets. The chart provides absolute values; the questions ask for percentage relationships. The key is to recognise that computing the percentage from chart values is a single operation that should take 15-20 seconds, not a complex derivation.

Pattern: "X as % of Y" = (X from chart / Y from chart) × 100. Never more complicated than this.

The only complication arises when units differ between X and Y - for example, if X is in thousands and Y is in crores, you must convert before dividing.

---

## The Error Log Method: Converting Wrong Answers into Preparation Assets

Every wrong answer in a practice session is a preparation asset if correctly analysed. The error log method:

**Step 1:** After each practice session, list every wrong answer with the question topic.

**Step 2:** For each wrong answer, categorise the error:
- **Concept error:** did not know or misapplied the formula
- **Calculation error:** understood the approach but made an arithmetic mistake
- **Reading error:** misread the question, a chart label, or an answer option
- **Time pressure error:** ran out of time and guessed or made a hurried error

**Step 3:** Tally by error type across a week's practice.

If your dominant error type is "concept," you need more content review.
If your dominant error type is "calculation," you need more timed arithmetic drill.
If your dominant error type is "reading," you need slower, more careful question reading in practice sessions.
If your dominant error type is "time pressure," you need more full-section mock tests to build endurance.

Most candidates have a mixed profile, but the dominant error type is usually the same one appearing across many topics. Fixing that root cause improves performance across all topics simultaneously.

---

## Practice Problem Bank: 15 Mixed-Topic Timed Drill Questions

These 15 problems span all major topics at Foundation difficulty. Attempt all 15 in 15 minutes. Time yourself strictly.

**1.** What is the LCM of 36, 48, and 60?

**2.** A price falls by 10% and then rises by 20%. What is the net change?

**3.** If A sells a watch to B at 10% profit and B sells it to C at 20% profit, and C pays Rs. 2,640, how much did A pay originally?

**4.** 20 litres of a 60% acid solution is diluted to 48% acid by adding water. How much water was added?

**5.** Pipe A fills a tank in 8 hours. Pipe B fills it in 12 hours. Both are opened together but Pipe A is closed after 3 hours. In how many more hours does Pipe B fill the remaining tank?

**6.** A train of 250m crosses a 350m platform in 30 seconds. Find the speed of the train in km/h.

**7.** The average of 8 numbers is 45. Two numbers, 60 and 30, are removed. What is the new average?

**8.** Find the CI on Rs. 8,000 at 10% per annum for 2 years compounded annually.

**9.** In how many ways can 5 distinct books be arranged on a shelf if 2 specific books must always be adjacent?

**10.** A box has 4 red balls and 6 blue balls. Two balls are drawn. What is the probability both are red?

**11.** Find the area of a triangle with vertices A(0,0), B(6,0), C(3,4).

**12.** If 7, x, 63 are in GP, find x.

**13.** A sum becomes Rs. 1,200 in 2 years and Rs. 1,440 in 4 years at simple interest. Find the principal.

**14.** A survey of 80 people: 45 read newspaper A, 30 read B, 15 read both. How many read neither?

**15.** A car covers 360 km in 6 hours. A motorcycle covers the same distance at 3/4 the speed. How many hours does the motorcycle take?

**Solutions:**

1. LCM(36,48,60): 36=2²×3², 48=2⁴×3, 60=2²×3×5. LCM=2⁴×3²×5=720.

2. Net change: 20 + (-10) + (20×-10)/100 = 10 - 2 = **8% increase**.

3. C paid 2640. B paid 2640/1.2 = 2200. A paid 2200/1.1 = **Rs. 2,000**.

4. Acid = 20×0.6 = 12 litres. For 48%: 12 = 0.48×(20+w). 20+w = 25. w = **5 litres**.

5. Together for 3 hours: A fills 3/8, B fills 3/12=1/4. Total = 3/8+1/4=5/8. Remaining = 3/8. B's rate = 1/12 per hour. Time = (3/8)/(1/12) = **4.5 hours**.

6. Speed = (250+350)/30 = 600/30 = 20 m/s = **72 km/h**.

7. New sum = 8×45-60-30=360-90=270. New average = 270/6 = **45**.

8. CI = 8000×(1.1)² - 8000 = 8000×1.21 - 8000 = 9680-8000 = **Rs. 1,680**.

9. Treat 2 books as block: 4! arrangements × 2! internal = 24×2 = **48 ways**.

10. P = C(4,2)/C(10,2) = 6/45 = **2/15**.

11. Area = (1/2)|6×4| = **12 sq units**. (Base AB=6, height from C to AB = 4.)

12. 7, x, 63 in GP: x² = 7×63 = 441. x = **21**.

13. SI per 2 years = 1440-1200 = 240. SI per year = 120. Principal × R/100 = 120. P+2×120 = 1200. P = **Rs. 960**. Verify: R = 120/960×100 = 12.5%.

14. |A∪B| = 45+30-15=60. Neither = 80-60 = **20 people**.

15. Car speed = 360/6 = 60 km/h. Motorcycle speed = 60×(3/4) = 45 km/h. Time = 360/45 = **8 hours**.

The following topics appear primarily in the Advanced Quantitative and Reasoning Section, which routes candidates to TCS Digital. They require deeper preparation effort and have a lower frequency-to-effort ROI compared to the Foundation topics above.

---

## Advanced Topic 1: Permutations and Combinations (Hard Variants)

### Additional Complexity Layers

At the Advanced level, P&C questions involve:

**Multi-constraint arrangements:** "Arrange N people in a row such that person A is not at either end AND person B must come before person C."

Approach for compound constraints: use complementary counting iteratively.
Total arrangements - (A at left end OR A at right end) adjusted for overlapping B-before-C constraint.

**Distribution into groups:**
- Distinct objects into distinct groups: multiply the choices per group
- Identical objects into distinct groups with minimum constraint: stars and bars

**Counting paths in a grid:** From (0,0) to (m,n) moving only right or up = C(m+n, m). With blocked cells, subtract paths through each blocked cell.

### Practice Problem

*In how many ways can the letters of the word ARRANGEMENT be arranged such that both R's are not adjacent?*

ARRANGEMENT has 11 letters: A(2), R(2), N(2), G(1), E(2), M(1), T(1).
Total arrangements = 11! / (2!×2!×2!×2!) = 2494800.
Arrangements with both R's adjacent: treat RR as one unit. 10 units with A(2),N(2),E(2),G,M,T: 10!/(2!×2!×2!) = 453600.
Arrangements where R's are NOT adjacent = 2494800 - 453600 = 2041200.

### Additional Advanced P&C Problems

*How many 4-digit numbers greater than 5000 can be formed using digits 3, 4, 5, 6, 7 without repetition?*

For number > 5000, the first digit must be 5, 6, or 7 (3 choices).
Remaining 3 digits from the remaining 4 available digits: 4×3×2 = 24 arrangements.
Total = 3 × 24 = 72.

*In a group of 10 people, in how many ways can a team of 4 be selected such that the team includes at least 2 women if there are 6 men and 4 women?*

Exactly 2 women: C(4,2)×C(6,2) = 6×15 = 90.
Exactly 3 women: C(4,3)×C(6,1) = 4×6 = 24.
Exactly 4 women: C(4,4)×C(6,0) = 1×1 = 1.
Total with at least 2 women = 90+24+1 = 115.

---

## Advanced Topic 2: Logarithms

**Frequency:** Very Low in Advanced | **Difficulty:** Hard | **Priority:** 5

### Concept Refresher

**Laws of logarithms:**
- log(AB) = log A + log B
- log(A/B) = log A - log B
- log(Aⁿ) = n log A
- log_a(b) = log b / log a (change of base)
- log_a(a) = 1; log_a(1) = 0

**Common values:** log₁₀(2) ≈ 0.301, log₁₀(3) ≈ 0.477, log₁₀(7) ≈ 0.845.

**Key relationship:** log_a(b) × log_b(a) = 1.

### Practice Problem

*If log₂(x) + log₄(x) + log₈(x) = 11, find x.*

Convert all to base 2: log₂(x) + log₂(x)/2 + log₂(x)/3 = 11.
Let y = log₂(x): y + y/2 + y/3 = 11. 6y/6 + 3y/6 + 2y/6 = 11. 11y/6 = 11. y = 6.
x = 2⁶ = 64.

---

## Advanced Topic 3: Set Theory

**Frequency:** Low in Advanced | **Difficulty:** Moderate | **Priority:** 5

### Concept Refresher

**Set operations:**
- Union: A∪B (all elements in A or B or both)
- Intersection: A∩B (elements in both A and B)
- Complement: A' (elements not in A)

**Inclusion-Exclusion Principle for two sets:**
|A∪B| = |A| + |B| - |A∩B|

**For three sets:**
|A∪B∪C| = |A| + |B| + |C| - |A∩B| - |A∩C| - |B∩C| + |A∩B∩C|

### Practice Problem

*In a survey of 200 students, 120 like Mathematics, 90 like Science, and 60 like both. How many students like neither?*

|M∪S| = 120 + 90 - 60 = 150.
Neither = 200 - 150 = 50 students.

**Three-set problem:** In a class of 100 students: 70 study Physics, 65 study Chemistry, 55 study Mathematics. 45 study both P and C, 40 study both C and M, 35 study both P and M. If 25 study all three, how many study none?

Using inclusion-exclusion:
|P∪C∪M| = 70+65+55 - 45-40-35 + 25 = 190-120+25 = 95.
Neither = 100-95 = 5.

### Set Theory: Regional Counting

In problems asking "only P," "only P and Q but not R," etc., use the following counting:

- Only A = |A| - |A∩B| - |A∩C| + |A∩B∩C|
- Only A and B (not C) = |A∩B| - |A∩B∩C|
- All three = |A∩B∩C|
- Exactly two = |A∩B| + |A∩C| + |B∩C| - 3|A∩B∩C|

In the Physics-Chemistry-Mathematics example:
Students studying exactly two subjects = (45+40+35) - 3×25 = 120 - 75 = 45.
Students studying exactly one subject = 70+65+55 - 2(45+40+35) + 3×25 = 190 - 240 + 75 = 25.
Verify: 25(one) + 45(two) + 25(three) + 5(none) = 100. ✓

---

## Advanced Topic 4: Functions

**Frequency:** Very Low | **Difficulty:** Hard | **Priority:** 5

### Concept Refresher

**Types of functions:**
- One-to-one (injective): different inputs give different outputs
- Onto (surjective): every element of codomain has at least one preimage
- Bijective: both one-to-one and onto

**Composition:** (f∘g)(x) = f(g(x)). Apply g first, then f.

**Inverse function:** f⁻¹(x) exists only if f is bijective. f(f⁻¹(x)) = x.

**Even and odd functions:** f(-x) = f(x) is even; f(-x) = -f(x) is odd.

### Practice Problem

*If f(x) = 2x+3 and g(x) = x²-1, find (f∘g)(3) and (g∘f)(3).*

(f∘g)(3) = f(g(3)) = f(9-1) = f(8) = 2(8)+3 = 19.
(g∘f)(3) = g(f(3)) = g(2(3)+3) = g(9) = 81-1 = 80.

Note: composition is NOT commutative - order matters.

---

## Advanced Topic 5: Complex Arrangement Problems

At the Advanced Reasoning level, TCS presents compound puzzles that combine multiple constraint types.

**Multi-attribute + conditional arrangements:**
N entities, each with M attributes (person, city, profession, colour preference). 10-14 clues where some are conditional ("if A is in city X, then B cannot be in profession Y").

**Approach:**
1. Build a full grid (entities × attributes)
2. Process absolute/direct clues first (eliminates cells without case analysis)
3. Process clues that link two attributes (cross-elimination)
4. Process conditional clues last (case analysis)
5. Verify the final allocation against every clue

This type of problem takes 7-10 minutes to set up correctly. The time investment is worthwhile only if you have already secured marks from the faster standalone questions.

---

## How Foundation and Advanced Section Questions Differ: A Side-by-Side Analysis

The distinction between Foundation and Advanced quantitative questions is not merely about higher numbers or harder formulas. The structural difference is in how many non-obvious steps are required, and whether the problem requires recognising a mathematical pattern rather than applying a known formula.

### Percentage Questions: Foundation vs Advanced

**Foundation style:** A price increases by 30% and then falls by 20%. What is the net change?
Approach: 1.3 × 0.8 = 1.04. Answer: 4% increase. One direct multiplier chain.

**Advanced style:** A product's price after three successive changes is 80% of its original price. The first change was an increase of 25%. The second change was a decrease of 20%. What was the third percentage change?
Approach: 1.25 × 0.8 × x = 0.8. x = 0.8/(1.25×0.8) = 0.8/1.0 = 0.8. Third change: 20% decrease.
This requires working backwards from a compound result, which is the Advanced distinguishing skill.

### TSD Questions: Foundation vs Advanced

**Foundation style:** Two trains approach each other. Find the crossing time.
**Advanced style:** A, B, and C are three stations. Train X travels A to C via B. Train Y travels C to A via B. They start simultaneously from A and C. X reaches B in 3 hours; Y reaches B in 4 hours. If AB = 180 km, find BC such that X and Y meet exactly at B.
These multi-condition TSD problems require setting up a system of equations from relative motion constraints - the Foundation formula approach does not extend cleanly to these.

### Probability: Foundation vs Advanced

**Foundation style:** Draw 2 from 10. P(both red)?
**Advanced style:** A biased coin shows heads with probability 0.6. In 3 tosses, find P(at least 2 heads given that the first toss was heads).
This requires Bayes-style conditional updating - not just P(A|B) = P(A∩B)/P(B) but recognising that the sample space has been restricted by the given condition.

**Conditional probability setup:**
P(at least 2 heads | first toss is heads) = P(first toss is heads AND at least 2 total heads) / P(first toss is heads).
P(first heads AND at least 2 heads) = P(exactly HHH) + P(exactly HHT) + P(exactly HTH) = 0.6³ + 0.6²×0.4 + 0.6×0.4×0.6 = 0.216 + 0.144 + 0.144 = 0.504.
P(first toss is heads) = 0.6.
P(condition) = 0.504/0.6 = 0.84.

---

## Preparation Resources

For timed topic-wise practice calibrated to the actual NQT difficulty, use the [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html). The platform covers all Foundation and Advanced quantitative topics with question sets you can practice in 25-minute timed blocks - exactly mirroring the actual exam section windows. No sign-up required.

For books: R.S. Aggarwal's Quantitative Aptitude is the most comprehensive reference for all Foundation topics. For Advanced section preparation, CAT-level quant resources (Arun Sharma's Quantitative Aptitude) provide the elevated difficulty calibration needed.

---

## Master Formula Reference

One page of formulas memorised to automatic recall is worth more than ten pages of notes reviewed occasionally. Use this reference as a daily warm-up checklist - read through it each morning of your preparation period until every formula is instantly retrievable.

### Percentages and Ratio
- x% of y = y% of x (useful for mental maths: 35% of 60 = 60% of 35 = 21)
- a is what % of b = (a/b) × 100
- a is r% more than b → b is r/(100+r) × 100 % less than a
- a is r% less than b → b is r/(100-r) × 100 % more than a
- Net effect of successive % changes a and b: a + b + ab/100

### Profit and Loss
- Profit% = (SP-CP)/CP × 100
- SP = CP × (100+P)/100 (for profit P%)
- CP = SP × 100/(100+P)
- Loss when same SP: if both profit and loss are r%, net loss = r²/100 %
- Dishonest trader gain% = (Error)/(True measure - Error) × 100

### Time, Speed, Distance
- Average speed (equal distances): 2S1S2/(S1+S2)
- Time to meet (towards each other): D/(S1+S2)
- Time to overtake (same direction): D/(S1-S2)
- Boat downstream: B+W; upstream: B-W; B=(D+U)/2; W=(D-U)/2

### Time and Work
- Combined rate: 1/A + 1/B + ... Use LCM for whole numbers
- W = R × T, where W is work units (LCM), R is rate, T is time

### Simple and Compound Interest
- SI = PRT/100; A = P(1+RT/100)
- CI: A = P(1+R/100)^T; for half-yearly: A = P(1+R/200)^(2T)
- CI - SI (2 years) = P(R/100)²
- Doubling time for CI: if doubles in D years, 2^k times takes kD years

### Averages
- New average after adding value X to group of N with average A: (NA+X)/(N+1)
- Weighted average of two groups: (n1A1+n2A2)/(n1+n2)

### Sequences
- AP: nth term = a+(n-1)d; Sum = n/2(2a+(n-1)d)
- GP: nth term = ar^(n-1); Sum = a(1-r^n)/(1-r)
- Sum of first n naturals: n(n+1)/2
- Sum of squares: n(n+1)(2n+1)/6
- Sum of cubes: [n(n+1)/2]²

### Permutations and Combinations
- nPr = n!/(n-r)!; nCr = n!/(r!(n-r)!)
- Circular: (n-1)!; with identical: n!/p!q!...
- Together: treat as block × internal arrangements
- Apart: total - together

### Probability
- P(A∪B) = P(A)+P(B)-P(A∩B)
- P(A∩B) = P(A)×P(B) if independent
- P(A|B) = P(A∩B)/P(B)
- P(at least one) = 1 - P(none)

### Mensuration Quick Reference
- Circle area: πr², circumference: 2πr
- Triangle area: ½bh or √(s(s-a)(s-b)(s-c))
- Trapezium: ½(a+b)h
- Cylinder: V=πr²h; TSA=2πr(h+r)
- Cone: V=⅓πr²h; CSA=πrl (l=slant height)
- Sphere: V=⁴⁄₃πr³; SA=4πr²

### Logarithms
- log(AB) = log A + log B
- log(A/B) = log A - log B
- log(Aⁿ) = n log A
- log₁₀(2) ≈ 0.301; log₁₀(3) ≈ 0.477

---

## Summary: The 10 Most Important Preparation Habits

1. **Timed practice from day one.** The 60-second-per-question constraint is the primary difficulty. Practice under time pressure, not at leisure.

2. **DI every day.** Data Interpretation is the highest-frequency topic. Do at least one 4-question DI set under timed conditions daily.

3. **Harmonic mean for TSD.** Internalise 2S1S2/(S1+S2) until reaching for it is automatic when a two-leg equal-distance journey appears.

4. **LCM method for Time and Work.** Eliminates fraction arithmetic entirely.

5. **Multiplier method for Percentages.** Convert all changes to multipliers; chain them; never add percentages.

6. **Alligation cross for mixtures.** The visual cross diagram resolves mixture ratio questions in 20 seconds.

7. **CI-SI formula for 2 years.** P(R/100)² answers the most commonly tested compound vs simple interest comparison.

8. **Complement method for "at least one" probability.** 1 - P(none) is always faster than summing individual cases.

9. **Mock tests with error categorisation.** Taking mocks without analysis is just score measurement; analysis converts mocks into targeted preparation.

10. **High-ROI topics before low-ROI.** DI, Percentages, TSD, and Profit & Loss deliver more marks per preparation hour than Geometry, Logarithms, or Functions.

---

*All practice problems in this guide are original compositions. Solutions are provided for immediate verification. Use the practice bank and drill problems in timed sessions to build the examination speed that content knowledge alone cannot provide.*

---

## Speed Techniques Consolidated Reference

This section consolidates every speed technique from the guide into a single quick-reference list.

**Percentages:** Multiplier method (chain all changes as multipliers). Net change formula: a + b + ab/100.

**TSD:** Average speed for equal distances = harmonic mean 2S1S2/(S1+S2). Closing speed method for meeting problems.

**Time and Work:** LCM method (total work = LCM of all time periods, rates become whole numbers).

**Profit and Loss:** SP/CP ratio gives profit/loss percentage directly.

**Alligation:** Cross diagram for mixing ratios. (Dearer - Mean):(Mean - Cheaper) gives the ratio of cheaper to dearer.

**HCF/LCM:** Product of two numbers = HCF × LCM.

**CI-SI difference for 2 years:** P(R/100)².

**Digital Root:** 1 + (N-1) mod 9 for N > 0.

**Units digit of large powers:** Use cyclicity (period 4 for 2,3,7,8; period 2 for 4,9; period 1 for 5,6).

**Probability:** P(at least one) = 1 - P(none).

**Combinatorics:** Objects together - treat as block. Objects apart - total minus together.

---

## 8-Week Study Calendar for TCS Aptitude Mastery

### Week 1: Priority 1 Topics (Foundational)

Daily: 45 minutes Numerical. 30 minutes Verbal reading for parallel Verbal prep.
Focus: Percentages (multiplier method thoroughly), Profit and Loss (SP/CP ratio approach).
Daily target: 20 timed Percentage/P&L questions under 20 minutes.

### Week 2: Priority 1 Topics Continued

Focus: Time Speed Distance (harmonic mean trap, train problems, boats and streams), and Data Interpretation (chart-first reading habit).
Daily target: 2 complete DI sets (4 questions each) in under 10 minutes total.

### Week 3: Priority 2 Topics

Focus: Time and Work (LCM method), Averages and Mixtures (alligation cross), Ratio and Proportion.
Daily target: 15 mixed priority-2 questions in 15 minutes.

### Week 4: Priority 2 and 3 Topics

Focus: SI/CI (difference formula), Number Systems (cyclicity, LCM+R formula), Sequences and Series.
Daily target: 20 mixed questions across all covered topics.

### Week 5: Priority 3 Topics

Focus: Permutations and Combinations, Probability, Ages and Blood Relations.
Daily target: 15 P&C/Probability questions. Note every trap encountered.

### Week 6: Foundation Integration

Take 2-3 full Foundation section mocks (25 questions, 25 minutes) this week. After each mock:
- Record score per topic
- Categorise every error
- Spend next day revising the two most error-prone topics

### Week 7: Advanced Topics (Digital-targeting candidates only)

Focus: Advanced P&C (multi-constraint, grid paths), Logarithms, Set Theory, Functions.
Daily target: 10 Advanced-level questions. Accept that difficulty is higher and aim for 60% accuracy rather than 90%.

### Week 8: Full Integration and Exam Simulation

Take complete timed Foundation mocks on alternating days. On non-mock days: targeted revision of weakest topics from mock analysis.
Final two days: review speed technique summary only. No new learning.

### How to Adjust the Calendar for Less Time

**With 4 weeks:** Compress Weeks 1-2 into Week 1 (cover P1 topics), compress Weeks 3-4 into Week 2 (cover P2 topics), dedicate Weeks 3-4 to full section mocks and error revision. Skip P4 and P5 topics entirely.

**With 2 weeks:** Foundation only. Weeks 1-2 cover DI, Percentages, TSD, P&L, Averages, and Time/Work exclusively. Take a full Foundation mock every 3 days. Prioritise accuracy on the 6 high-ROI topics over attempting to cover the full syllabus.

The 2-week compressed plan has a lower ceiling (you will likely score well only on the P1 and P2 topics) but is significantly better than unstructured last-minute preparation across all topics at shallow depth. Depth on fewer topics beats breadth at no depth.

---

## Final Words: The Difference Between Knowing and Solving

Every formula and technique in this guide is knowable within a few days of study. The gap between knowing a technique and consistently applying it correctly under a 60-second-per-question time constraint is where most candidates lose marks.

That gap is closed only through timed practice. Reading about the harmonic mean average speed formula is not the same as reflexively reaching for it when you see a two-leg journey problem under exam pressure. Writing it out once is not the same as getting it right on the fifth consecutive problem in a 25-minute mock.

The preparation sequence in this guide is designed to build that reflexive pattern recognition. High-frequency topics first, timed practice from day one, and mock exams with error categorisation - this is the path from understanding the material to scoring well on the actual test.

---

*All practice problems in this guide are original compositions created to illustrate TCS aptitude question styles and approaches. Solve them in your chosen preparation environment and track your accuracy and speed improvement over the preparation period.*
